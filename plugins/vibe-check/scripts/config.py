"""config.py — the repo-config I/O boundary for the vibe-check plugin.

Phase 30 (CONFIG-01/02/03). This is the ONE module allowed filesystem I/O so
score.py stays pure: it reads the repo-root `.vibe-check.toml` via `tomllib`,
resolves each Phase-30 knob (`thresholds`, `disabled`, `top_model`) through the
precedence chain (flag > toml > default), and returns `(values, warnings)`.

INVERTED fail posture (vs score.py — the load-bearing divergence): where score.py
fails CLOSED on bad stdin (unparseable input propagates a non-zero exit),
config.py NEVER raises to the orchestrator. A missing / unparseable / non-UTF-8 /
oversized / non-regular / partially-invalid config degrades PER-KEY to defaults
with collected warnings (CONFIG-03) — a bad config must never break a review. An
ABSENT file is silent (all defaults, NO warning — CONFIG-01 zero-config
back-compat). Every known failure mode (no parser / absent path / undecodable
bytes / malformed TOML / unreadable file / special file / oversized file) is
caught; a bad VALUE never reaches a raise because the validators coerce-or-default.

Two-layer threshold note (do NOT conflate — D-02 / Finding #4): the `thresholds`
knob tunes `band_for()`'s band FLOORS (critical/warning/medium labels), a SEPARATE
layer from the per-command finalize cutoffs `THRESHOLDS = {"review": 80,
"deep-review": 70}` (score.py:44), which this module does NOT tune. A VALID config
whose band floor sits BELOW a command's finalize cutoff (e.g. critical=72,
warning=71, medium=70) is ACCEPTED, not rejected — its 72-79 floors are observable
only under `/deep-review` (finalize >= 70); under `/review` (finalize >= 80) those
bands are produced then filtered as sub-threshold. That observability difference is
the per-command-cutoff layer (proven in Plan 02's run()-level test), NOT a reason
to reject a below-80 floor here.

I/O: `$REPO_ROOT` env var in -> reads `$REPO_ROOT/.vibe-check.toml` (the ONE
allowed filesystem read) -> emits `{values, warnings}` JSON on stdout -> exit 0
ALWAYS (degrade, never abort). `tomllib` is imported INSIDE load_config (wrapped in
try/except ImportError) per D-01 so a Python < 3.11 runtime degrades rather than
failing at module import.
"""

import json
import os
import sys

# --------------------------------------------------------------------------- #
# Constants — the built-in defaults + validation bounds. Keep the default path
# byte-stable: a None `thresholds` means score.py's band_for uses its own
# 95/80/70 literals, so the no-config output is identical to v2.7 (D-02).
# --------------------------------------------------------------------------- #

# The resolved-value shape load_config always returns (all keys present).
# None => "use the built-in default"; [] => "no agents disabled".
# min_confidence None => "no confidence filter" (byte-stable default, D-04).
# idiom_floor "medium" => the NOISE-01 cap is ACTIVE BY DEFAULT (A1) — the ONLY
# default that is NOT None (its default-direction is inverted, see the constant
# block below and _validate_idiom_floor).
_DEFAULT_VALUES = {"thresholds": None, "disabled": [], "top_model": None,
                   "min_confidence": None, "idiom_floor": "medium",
                   "codex": "auto"}

# The opus/fable allowlist, mirroring the existing $VIBE_CHECK_TOP_MODEL
# validation (deep-review.md:55) so the two precedence sources cannot diverge
# (Pitfall 6). Anything else => None + warning.
_TOP_MODEL_ALLOWLIST = ("opus", "fable")

# The codex knob (LEGIBLE-02, D-10/D-14): controls whether the Codex adversarial
# reviewer is attempted at deep-review Phase 2c. Three modes:
#   off  — never attempt Codex (cheapest path; skip even the setup --json probe).
#   auto — DEFAULT; today's Phase-2c dispatch logic UNCHANGED (run iff available).
#   on   — same dispatch DECISION as auto, but any skip renders PROMINENTLY
#          ("auto + louder", never "bypass safety" — correctness skips preserved).
# codex is ORCHESTRATOR-only — it NEVER enters the score.py envelope, so
# GOLDEN_DIGEST stays frozen. Its malformed default-direction is "auto" (a
# NON-None default, like idiom_floor's "medium"), NOT None: a bad value keeps the
# behavior-unchanged auto posture. See _validate_codex.
_CODEX_MODES = ("off", "auto", "on")

# The byte-stable band floors band_for() falls back to when `thresholds` is
# absent/invalid — kept here for the validation coherence checks (strict descent
# reference). Injecting these literals is byte-equivalent to omitting the key.
_DEFAULT_BANDS = {"critical": 95, "warning": 80, "medium": 70}

# The D-02 thresholds sub-key set (exactly these three, no more/no fewer).
_THRESHOLDS_KEYS = ("critical", "warning", "medium")

# Each threshold sub-key is an int in [_BAND_MIN, _BAND_MAX].
_BAND_MIN = 1
_BAND_MAX = 100

# The `medium` band floor must stay >= this: below 70 would band findings BOTH
# commands' finalize cutoffs (review 80 / deep-review 70) filter out — a dead band
# (D-02). A medium below the floor => whole-set fallback to None + warning.
_MEDIUM_FLOOR = 70

# The [noise] min_confidence knob (CONF-02, D-04): an int in [0, 49]. None =>
# "no filter" (byte-stable default). Anything out of range / non-int / bool
# degrades per-key to None + one warning.
#
# WHY the ceiling is 49, not 100 (Fable A3 — the "H-KNOB kill-shot"): the filter
# runs BEFORE scoring, so the trust adders can never rescue a dropped finding.
# A critical-severity finding surfaces at agent_confidence >= 50 with full trust
# (conf + 20 in_diff + 10 cross-confirm + 15 persisted + 0 critical-severity
# = conf+45 >= the 95 critical band floor  =>  conf >= 50). So any
# min_confidence >= 50 SILENTLY annihilates real criticals the same review would
# otherwise surface — the spec's own illustrative `min_confidence = 60` did
# exactly that. Values >= 50 are refused (None + a warning explaining why), the
# same degrade direction as every other invalid value: over-reporting beats
# silently missing criticals.
_MIN_CONFIDENCE_MIN = 0
_MIN_CONFIDENCE_CRITICAL_FLOOR = 50   # conf >= 50 can reach the critical band.
_MIN_CONFIDENCE_MAX = _MIN_CONFIDENCE_CRITICAL_FLOOR - 1

# The [noise] idiom_floor knob (NOISE-01, D-01/D-02): a per-category band cap on
# `idiom`-category findings. Valid values are the band names below (INCLUDING
# "low" — a valid cap, Finding NEW-2) plus a disable sentinel ("off"/"none", both
# spellings). CRITICAL default-direction divergence from min_confidence/thresholds:
# the cap is ACTIVE BY DEFAULT at "medium" (owner-confirmed A1) so idioms never
# block finalize out of the box. So an absent key AND a malformed value both
# resolve to the "medium" DEFAULT (fail-safe: the cap stays ON), NOT to None. The
# explicit-disable path is the ONLY way to turn the cap off, and it returns the
# LITERAL "off" sentinel (NOT None — Finding #2, Option A) so score.py can tell an
# explicit user disable from an absent key on the envelope (absent => medium cap
# ACTIVE; "off" => cap DISABLED; band => cap at that band). "none" normalizes to
# the single canonical "off".
_IDIOM_FLOOR_BANDS = ("critical", "warning", "medium", "low")
_IDIOM_FLOOR_DISABLE = ("off", "none")
_IDIOM_FLOOR_OFF = "off"          # the canonical disable sentinel (self-describing)
_DEFAULT_IDIOM_FLOOR = "medium"   # A1: the cap is active by default

# The codex knob default (D-14): "auto" — behavior UNCHANGED from v2.7. Like
# idiom_floor, this is a NON-None default-direction: an absent key AND a malformed
# value both resolve to "auto" (fail-safe: Codex keeps running per today's logic).
_DEFAULT_CODEX = "auto"

# Pre-parse size cap (Finding #2 round-3, DoS): a real .vibe-check.toml is a few
# hundred bytes; 1 MiB is generous. A regular file over this is degraded to
# defaults + one warning WITHOUT being parsed, so a huge repo-controlled config
# cannot stall or OOM the parser.
_MAX_CONFIG_BYTES = 1_048_576  # 1 MiB


# --------------------------------------------------------------------------- #
# Per-key validators — the coerce-or-default, never-raise idiom (mirrors
# score.py's _category_domain / _safe_window). Each returns
# (value_or_default, warning_or_None). Warnings name the KEY + a FIXED reason
# string ONLY — never the raw (attacker-controlled) config VALUE text (V5).
# --------------------------------------------------------------------------- #
def _validate_thresholds(raw):
    """Validate a raw `thresholds` VALUE against the locked D-02 schema.

    WHOLE-SET fallback (not per-sub-key): the value must be a dict whose keys are
    EXACTLY {critical, warning, medium}, each a non-bool int in [1, 100], strictly
    descending (critical > warning > medium), with medium >= _MEDIUM_FLOOR. ANY
    violation — non-dict, missing/extra sub-key, non-int, out-of-range,
    non-monotonic, medium<70 — returns (None, warning), so band_for falls back to
    its built-in 95/80/70 literals (byte-stable default path). A valid value round
    -trips unchanged with no warning.
    """
    reason = "config: thresholds invalid — using default"
    if not isinstance(raw, dict):
        return None, reason
    # Exact key set: no missing, no extra sub-keys.
    if set(raw.keys()) != set(_THRESHOLDS_KEYS):
        return None, reason
    vals = {}
    for key in _THRESHOLDS_KEYS:
        v = raw[key]
        # A bool is an int subclass but is not a valid band floor.
        if not isinstance(v, int) or isinstance(v, bool):
            return None, reason
        if v < _BAND_MIN or v > _BAND_MAX:
            return None, reason
        vals[key] = v
    # Strict monotonic descent: critical > warning > medium.
    if not (vals["critical"] > vals["warning"] > vals["medium"]):
        return None, reason
    # medium floor coherence with the per-command finalize cutoffs.
    if vals["medium"] < _MEDIUM_FLOOR:
        return None, reason
    return {"critical": vals["critical"],
            "warning": vals["warning"],
            "medium": vals["medium"]}, None


def _validate_disabled(raw):
    """Validate a raw `disabled` VALUE to a list of agent-name strings.

    Container+element double-guard (like score.py's _safe_window): a non-list =>
    ([], warning); a list keeps ONLY its string elements, warning if any non-string
    element was dropped. There is NO allowlist on agent NAMES here — disabling
    `bugs`/`security` IS honored (returned in the list); the orchestrator (Plan 03)
    surfaces a disabled core agent on the config-health line, so config.py's job is
    to report the list faithfully, never to silence it (Pitfall 5).
    """
    if not isinstance(raw, list):
        return [], "config: disabled invalid (not a list) — using default"
    kept = [s for s in raw if isinstance(s, str)]
    if len(kept) != len(raw):
        return kept, "config: disabled had non-string entries (ignored)"
    return kept, None


def _validate_top_model(raw):
    """Validate a raw `top_model` VALUE against the opus/fable allowlist.

    Must be a str in _TOP_MODEL_ALLOWLIST; anything else (wrong type, bogus model
    string) => (None, warning), so the orchestrator falls back to its built-in
    default (opus). Reuses the exact $VIBE_CHECK_TOP_MODEL allowlist so the two
    precedence sources cannot diverge (Pitfall 6).
    """
    if isinstance(raw, str) and raw in _TOP_MODEL_ALLOWLIST:
        return raw, None
    return None, "config: top_model invalid (not opus/fable) — using default"


def _validate_min_confidence(raw):
    """Validate a raw `min_confidence` VALUE (CONF-02, D-04, Fable A3): an int in [0, 49].

    A bool is an int subclass but is NOT a valid confidence value (reject it, like
    _validate_thresholds' band floors). Anything else — wrong type, out of range,
    bool — returns (None, warning) so the orchestrator applies NO filter (the
    byte-stable default: score.py drops nothing when min_confidence is None). The
    warning names the KEY + a FIXED reason ONLY — never the raw config VALUE text
    (V5 hardening, module docstring). A valid value round-trips unchanged, no
    warning.

    Values >= 50 get a DISTINCT fixed reason (Fable A3): they are not merely
    out-of-range, they would silently drop findings that score into the critical
    band (see the _MIN_CONFIDENCE_CRITICAL_FLOOR derivation above) — the user
    should learn WHY the knob refused, not just that it did.
    """
    reason = "config: min_confidence invalid — using default"
    if not isinstance(raw, int) or isinstance(raw, bool):
        return None, reason
    if raw >= _MIN_CONFIDENCE_CRITICAL_FLOOR:
        return None, ("config: min_confidence >= 50 can silently drop critical "
                      "findings (the filter runs before scoring) — using default")
    if raw < _MIN_CONFIDENCE_MIN or raw > _MIN_CONFIDENCE_MAX:
        return None, reason
    return raw, None


def _validate_idiom_floor(raw):
    """Validate a raw `idiom_floor` VALUE (NOISE-01, D-01/D-02): a band-cap knob.

    Three accepted shapes, resolving to THREE distinct outcomes so the disable
    stays provably distinct from omission end-to-end (Finding #2, Option A):

    - A valid band name — "critical"/"warning"/"medium"/"low", case-insensitive —
      round-trips as the lowercased band with NO warning. NOTE "low" IS in the
      valid set: it is a valid cap band (caps idioms at the literal "low" band),
      NOT a disable (Finding NEW-2).
    - The disable sentinel — "off" or "none", case-insensitive (both accepted) —
      returns the LITERAL `"off"` sentinel (a single canonical spelling; "none"
      normalizes to "off"), with NO warning. This returns the literal `"off"`
      string and NOT None (Finding #2): the explicit-disable provenance survives
      onto the envelope, so score.py can tell an explicit user disable from an
      absent key. An absent key means the default medium cap is ACTIVE (A1).
    - Anything else (unknown string, empty string, non-str, bool) — returns
      ("medium", warning): the medium DEFAULT + one warning naming the key. This
      is the OPPOSITE default-direction from min_confidence's malformed→None
      (D-02 / ROADMAP criterion 4 mandate malformed→medium): a bad value keeps the
      cap ACTIVE (fail-safe protecting finalize), it does NOT return the "off"
      sentinel and does NOT disable the cap.

    The warning names the KEY + a FIXED reason ONLY — never the raw config VALUE
    text (V7 hardening, module docstring). NEVER raises (never-raise family).
    """
    reason = "config: idiom_floor invalid — using default"
    if isinstance(raw, str):
        low = raw.lower()
        # Disable sentinel FIRST: "off"/"none" -> the literal canonical "off"
        # (NOT None — Finding #2, Option A) so the disable is self-describing.
        if low in _IDIOM_FLOOR_DISABLE:
            return _IDIOM_FLOOR_OFF, None
        # Valid cap band (INCLUDES "low" — Finding NEW-2, a valid cap not a disable).
        if low in _IDIOM_FLOOR_BANDS:
            return low, None
    # Malformed (unknown string, empty, non-str, bool) -> the medium DEFAULT (NOT
    # None, NOT the off sentinel): the cap stays ACTIVE (D-02 / ROADMAP crit 4).
    return _DEFAULT_IDIOM_FLOOR, reason


def _validate_codex(raw):
    """Validate a raw `codex` VALUE (LEGIBLE-02, D-10/D-14): off/auto/on.

    Fixed-enum shape (like _validate_top_model) with the DEFAULT-DIRECTION of
    _validate_idiom_floor (malformed → a NON-None default, NOT None):

    - A valid mode — "off"/"auto"/"on", case-insensitive (mirrors
      _validate_idiom_floor's raw.lower()) — round-trips as the lowercased value
      with NO warning.
    - Anything else (unknown string, empty, non-str, bool) — returns
      ("auto", warning): the "auto" DEFAULT + one warning naming the key. This is
      the OPPOSITE default-direction from top_model's malformed→None: a bad codex
      value keeps the behavior-unchanged auto posture (Codex still runs per
      today's Phase-2c logic), it does NOT disable Codex.

    The warning names the KEY + a FIXED reason ONLY — never the raw config VALUE
    text (V5/V7 hardening, module docstring — the D-14 `(<reason>)` parenthetical
    is NOT interpolated; the sibling-consistent fixed form is used). NEVER raises
    (never-raise family).
    """
    reason = "config: codex invalid — using default"
    if isinstance(raw, str) and raw.lower() in _CODEX_MODES:
        return raw.lower(), None
    return _DEFAULT_CODEX, reason


# --------------------------------------------------------------------------- #
# Precedence overlay — flags run through the SAME per-key validators as toml
# (VALIDATE-THEN-OVERLAY, Finding #3): a flag value is never trusted by fiat.
# --------------------------------------------------------------------------- #
def _apply_flags(values, warnings, flags):
    """Overlay validated flag values onto `values` (flag > toml > default).

    If flags is None, `values` is returned unchanged. Otherwise, for each of the
    four knobs, a non-None `flags[key]` is run through that knob's validator and
    the VALIDATED result overlays the toml value, appending any warning it
    produces. A bad flag degrades to default + warning EXACTLY like a bad toml
    value — a flag can never bypass validation. (This is the precedence slot later
    phases reuse for `--codex`.)
    """
    if not isinstance(flags, dict):
        return values, warnings
    validators = {
        "thresholds": _validate_thresholds,
        "disabled": _validate_disabled,
        "top_model": _validate_top_model,
        "min_confidence": _validate_min_confidence,
        # No flag is parsed for idiom_floor this phase — the precedence slot is
        # harmless (a None flag is skipped below) and future-proof.
        "idiom_floor": _validate_idiom_floor,
        # The reserved --codex slot (D-10): flag > toml > default, validated
        # through the SAME _validate_codex a bad toml value hits.
        "codex": _validate_codex,
    }
    for key, validator in validators.items():
        flag_val = flags.get(key)
        if flag_val is None:
            continue
        resolved, warning = validator(flag_val)
        values[key] = resolved
        if warning:
            warnings.append(warning)
    return values, warnings


# --------------------------------------------------------------------------- #
# load_config — the never-raise reader. Returns (values, warnings) on EVERY
# input; the KNOWN failure modes are all caught, and a bad VALUE never reaches a
# raise because the validators coerce.
# --------------------------------------------------------------------------- #
def load_config(path, *, flags=None):
    """Read `.vibe-check.toml` at `path`; return (values, warnings). NEVER raises.

    values is always `{"thresholds": .., "disabled": .., "top_model": ..,
    "min_confidence": ..}` with defaults substituted for any absent/invalid knob.
    warnings is a list of
    human-readable strings (KEY + fixed reason only — no raw config VALUE text),
    EMPTY when the file is absent OR fully valid. Precedence: flag > toml > default,
    resolved per knob (CONFIG-02). See the module docstring for the inverted
    (degrade-not-abort) contract.
    """
    # Inline-construct a FRESH values dict every call — do NOT `dict(_DEFAULT_VALUES)`.
    # A shallow copy would alias the SAME `disabled` list object as the module-level
    # _DEFAULT_VALUES['disabled'], so any downstream mutation (a `values['disabled']
    # .append(...)`) would permanently poison the default for every subsequent call.
    # The list literal here allocates a new [] on each invocation (lang-py-001).
    # idiom_floor defaults to "medium" here too (A1 — the cap is active by
    # default); keep this an inline literal in lockstep with _DEFAULT_VALUES
    # rather than switching to dict(_DEFAULT_VALUES) (the anti-poisoning literal).
    values = {"thresholds": None, "disabled": [], "top_model": None,
              "min_confidence": None, "idiom_floor": "medium",
              "codex": "auto"}
    warnings = []

    # D-01: no parser (Python < 3.11) => degrade, never raise. Imported here (not
    # at module top) so the module still imports on a runtime without tomllib.
    try:
        import tomllib
    except ImportError:
        warnings.append("config: tomllib unavailable (Python < 3.11) — using defaults")
        return _apply_flags(values, warnings, flags)

    # ABSENT file => all defaults, NO warning (CONFIG-01 zero-config silence).
    if not os.path.exists(path):
        return _apply_flags(values, warnings, flags)

    # GUARD 1 (Finding #2 round-4) — REGULAR-FILE guard, runs FIRST. os.path.isfile
    # follows symlinks but returns False for FIFO/char-device/dir, so a
    # .vibe-check.toml symlinked to a FIFO or /dev/null is degraded WITHOUT being
    # opened. This must precede the size guard: os.path.getsize follows symlinks
    # and reports 0 for special files, so a size-only guard would pass them and
    # tomllib.load would then block on / read an unbounded stream. A
    # symlink->regular-file is honored (isfile True).
    if not os.path.isfile(path):
        warnings.append("config: .vibe-check.toml is not a regular file — using defaults")
        return _apply_flags(values, warnings, flags)

    # GUARD 2 (Finding #2 round-3) — SIZE guard, runs SECOND (regular files only).
    # A stat error is itself caught => degrade (same never-raise family). An
    # oversized regular file is degraded WITHOUT being parsed, so a huge
    # repo-controlled config cannot stall or OOM the parser.
    try:
        size = os.path.getsize(path)
    except OSError:
        warnings.append("config: .vibe-check.toml unreadable — using defaults")
        return _apply_flags(values, warnings, flags)
    if size > _MAX_CONFIG_BYTES:
        warnings.append("config: .vibe-check.toml too large — using defaults")
        return _apply_flags(values, warnings, flags)

    # Parse. BINARY mode is REQUIRED by tomllib (Pitfall 2). The catch tuple MUST
    # include UnicodeDecodeError (Finding #2): tomllib.load decodes UTF-8
    # internally and raises UnicodeDecodeError on non-UTF-8 bytes — it is NOT a
    # subclass of TOMLDecodeError or OSError, so a 0xFF-byte config would otherwise
    # escape and break the never-raise invariant. No blanket `except Exception`
    # (Pitfall 3) — the KNOWN failure modes are named.
    try:
        with open(path, "rb") as fh:
            raw = tomllib.load(fh)
    except (tomllib.TOMLDecodeError, UnicodeDecodeError, OSError):
        warnings.append("config: .vibe-check.toml unparseable — using defaults")
        return _apply_flags(values, warnings, flags)

    # A non-table top level (tomllib always returns a dict for valid TOML, but
    # guard anyway) or a non-table [review]/[agents] section degrades cleanly.
    if not isinstance(raw, dict):
        warnings.append("config: .vibe-check.toml unparseable — using defaults")
        return _apply_flags(values, warnings, flags)
    review = raw.get("review", {})
    agents = raw.get("agents", {})
    noise = raw.get("noise", {})
    review = review if isinstance(review, dict) else {}
    agents = agents if isinstance(agents, dict) else {}
    noise = noise if isinstance(noise, dict) else {}

    # Per-key validation (CONFIG-03): one bad key defaults THAT key + a warning
    # naming it; the other valid keys still apply. Only override the default when
    # the section actually carries the key, so an absent key stays at its default
    # WITHOUT a spurious warning.
    if "thresholds" in review:
        values["thresholds"], w = _validate_thresholds(review["thresholds"])
        if w:
            warnings.append(w)
    if "disabled" in agents:
        values["disabled"], w = _validate_disabled(agents["disabled"])
        if w:
            warnings.append(w)
    if "top_model" in agents:
        values["top_model"], w = _validate_top_model(agents["top_model"])
        if w:
            warnings.append(w)
    if "min_confidence" in noise:
        values["min_confidence"], w = _validate_min_confidence(noise["min_confidence"])
        if w:
            warnings.append(w)
    if "idiom_floor" in noise:
        values["idiom_floor"], w = _validate_idiom_floor(noise["idiom_floor"])
        if w:
            warnings.append(w)
    if "codex" in noise:
        values["codex"], w = _validate_codex(noise["codex"])
        if w:
            warnings.append(w)

    # Precedence: flag wins over toml, but through the SAME validators (Finding #3).
    return _apply_flags(values, warnings, flags)


# --------------------------------------------------------------------------- #
# $REPO_ROOT/stdout shim — the ONLY __main__ I/O. INVERTED from score.py: it
# DEGRADES (exit 0 always) where score.py fails closed (Pitfall 4). An
# empty/unset REPO_ROOT is treated as the absent-config path => defaults + no
# warning (silent zero-config). Do NOT os.path.join("", ".vibe-check.toml"): that
# yields the CWD-relative "./.vibe-check.toml", which would READ a stray config
# from the current directory instead of resolving to "no config" (bugs-001).
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    repo_root = os.environ.get("REPO_ROOT", "")

    # CONF-02 (D-04, option a): thread the --min-confidence flag through the tested
    # _apply_flags validation path via a MIN_CONFIDENCE_FLAG env var. An
    # unset/empty flag => flags=None so today's zero-flag behavior is byte-identical.
    # A non-int MIN_CONFIDENCE_FLAG is caught here and forwarded as None (i.e. no
    # override, matching the "no flag" case) — the shim must never abort (exit 0
    # always). The 0-49 bound (Fable A3) is NOT re-checked here:
    # _validate_min_confidence inside _apply_flags owns it, so a flag like 999
    # (or a critical-annihilating 60) degrades with a warning.
    flag_raw = os.environ.get("MIN_CONFIDENCE_FLAG", "")
    flags = None
    if flag_raw:
        try:
            parsed = int(flag_raw)
        except ValueError:
            parsed = None
        if parsed is not None:
            flags = {"min_confidence": parsed}

    # LEGIBLE-02 (D-10): thread the --codex flag through the SAME tested
    # _apply_flags path via a CODEX_FLAG env var. SIMPLER than min_confidence — no
    # int() parse: a non-empty string flows straight into flags["codex"], and
    # _validate_codex degrades a bogus token to "auto" (never abort). Merged into
    # the SAME flags dict so --codex and --min-confidence coexist on one
    # invocation; an unset/empty CODEX_FLAG adds nothing (byte-identical to today).
    codex_flag_raw = os.environ.get("CODEX_FLAG", "")
    if codex_flag_raw:
        if flags is None:
            flags = {}
        flags["codex"] = codex_flag_raw

    if repo_root:
        config_path = os.path.join(repo_root, ".vibe-check.toml")
        v, w = load_config(config_path, flags=flags)
    else:
        # Empty/unset REPO_ROOT: load_config("") hits `not os.path.exists("")`
        # (True) => absent path => all defaults, no warning. This is byte-identical
        # to the intended zero-config silence and never reads a CWD-relative file.
        # The flag (if any) still overlays through _apply_flags.
        v, w = load_config("", flags=flags)
    json.dump({"values": v, "warnings": w}, sys.stdout)
    sys.exit(0)
