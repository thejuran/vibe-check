"""score.py — the deterministic-core scoring filter for the vibe-check plugin.

Phase 16 (CORE-01) extracted the orchestrator's by-hand scoring prose
(templates/scoring.md + commands/review.md Phase 3/4.5) into this script, and the
formula stayed FROZEN through v2.9. The freeze lifted for v2.10 Wave 1, scoped to
the replay-guardrailed changes documented in templates/scoring.md § "Wave 1
(v2.10)": the lone-lane band ceiling (B-SEV — a group with no second opinion is
capped below the critical floor) and the lone-lane confidence calibration
(B-REWEIGHT — derived, lower-only per-agent offsets on a group with no second
opinion), and site grouping (H-LANE — every lane at one file within ±2 lines is
one row carrying each lane's own record in `members`; the +10 fires only for a
Codex + Claude pair). No other weight, bonus, band cutoff or threshold is
retuned.

Pure-function boundary (D-05): the script does NO filesystem, git, or shell-out
I/O. Every raw fact (changed_line_ranges, source_window, canonical_line_content,
file_line_totals) arrives PRE-RESOLVED on stdin. Import set is EXACTLY
{json, hashlib, re, sys} — nothing else (the AST import-set test enforces this).

I/O: one JSON envelope on stdin -> one JSON envelope on stdout. The __main__ shim
fails CLOSED — unparseable stdin propagates the error so the process exits non-zero
(the orchestrator's fail-closed gate in 16-02 depends on this).
"""

import hashlib
import json
import re
import sys

# `re` is part of the allowed import set and reserved for future deterministic
# string-matching needs; reference it once so linters and the AST import-set test
# both see a stdlib-only module that is genuinely available.
_RE_AVAILABLE = bool(re)

# --------------------------------------------------------------------------- #
# Constants — transcribed verbatim from templates/scoring.md and review.md:685.
# Do NOT retune outside the v2.10 Wave 1 set (templates/scoring.md § "Wave 1 (v2.10)").
# --------------------------------------------------------------------------- #

# scoring.md:21-26 — severity weight, applied LAST before clamp. Unset/other => -8.
SEVERITY_WEIGHT = {"critical": 0, "high": -3, "medium": -8, "low": -20}
SEVERITY_FALLBACK = -8  # scoring.md:26 (unset / unrecognized => medium-equivalent)

# review.md:685 — the canonical silenced markers (NOT false-positive-rules.md's
# slightly-different list). Fixed-string substring match over a ±2-line window,
# CASE-INSENSITIVE: every needle below is lowercase and silenced_nearby matches
# against line.lower(), so `# NOQA` (valid flake8) is caught. Both spaced and
# unspaced spellings are listed for the two markers real tools emit without a
# space (Fable A13): golangci-lint REQUIRES `//nolint` (no space) and flake8
# accepts `#noqa` — the spaced-only needles missed both, so a finding the author
# legitimately suppressed took no -50 and was reported anyway.
SILENCED_MARKERS = ("eslint-disable", "# noqa", "#noqa", "// nolint", "//nolint",
                    "@suppresswarnings", "#[allow(")

# NOISE-02/03 (D-03) — the `vibe-ignore` marker token. Deliberately NOT a member
# of SILENCED_MARKERS: unlike the 5 bare fixed-string markers, vibe-ignore is
# REASON-AWARE — a `vibe-ignore: <reason>` (non-empty reason) suppresses, but a
# BARE `vibe-ignore` (no/empty reason) must NOT suppress (it surfaces a synthetic
# audit finding instead, run()). If it were a plain SILENCED_MARKERS member a bare
# marker would wrongly suppress. Recognition is folded into silenced_nearby via the
# reason-aware _vibe_ignore_scan below.
_VIBE_IGNORE = "vibe-ignore"

# NOISE-03 (D-04, A2) — the synthetic "suppression without reason" audit finding
# score.py emits for a BARE vibe-ignore. FIXED strings (T-32-04 Information
# Disclosure): the title/category/canonical are NEVER derived from the marker line
# or any repo-controlled text, so no untrusted text feeds the render or the hash.
_SUPPRESSION_CATEGORY = "suppression"   # groups by site like any finding; scores 0 and never fires.
_SUPPRESSION_TITLE = "suppression without reason"
# A FIXED canonical marker-line content string fed to stable_hash (NOT the marker's
# actual line text — no repo text in the hash) so the synthetic finding hashes
# deterministically per (file, marker_line) across runs, even when line is null.
_SUPPRESSION_CANONICAL = "vibe-ignore (no reason)"
# A fixed NON-NULL score strictly below the medium floor (70). It is INERT w.r.t.
# the frozen band math because it NEVER flows through band_for — the band is
# HAND-SET to the literal "low". It exists ONLY to satisfy review.md's Phase 3/4
# "has orchestrator_score" structural gate (Finding #1).
_SUPPRESSION_SCORE = 0
# impact-01 — a DISTINCT status the multi-pass carry-forward path EXCLUDES. The
# synthetic finding is REGENERATED fresh every pass from the live ±2 window scan,
# so it must NOT be carried forward: review.md Phase 0.5 re-ingests only findings
# whose status ∈ {new, persisted, needs-recheck}, and "audit" is deliberately NOT
# in that allowlist — so a synthetic finding is naturally regenerated-not-carried
# (never double-counted, never mis-classified needs-recheck/fixed-since-last from
# its empty current_code). This value is INERT for the STRUCTURAL gates (Phase 3
# step 5 / the Phase-4 render gate key on band/orchestrator_score/stable_hash, NOT
# status) and for the RENDER selector (the Suppression audit section selects by
# category=="suppression", NOT status), so rendering and gate-passing are unchanged
# — ONLY carry-forward inclusion changes, which is the whole point (impact-01).
_SUPPRESSION_STATUS = "audit"

# scoring.md:57-64 — per-command threshold (one parameter selected by `command`).
THRESHOLDS = {"review": 80, "deep-review": 70}

# scoring.md:37-42 — the built-in band-boundary floors band_for() applies when no
# `thresholds` override is present. This is a DIFFERENT layer from THRESHOLDS above:
# THRESHOLDS is the per-command finalize cutoff (which findings surface for /review
# vs /deep-review); _DEFAULT_BANDS is the critical/warning/medium LABEL boundaries.
# The v2.8 `thresholds` config knob (D-02) parameterizes THESE floors, defaulting to
# the whole set so the no-config path stays byte-identical (frozen GOLDEN_DIGEST).
# Do NOT retune these literals (behavior-preserving) and do NOT conflate with THRESHOLDS.
_DEFAULT_BANDS = {"critical": 95, "warning": 80, "medium": 70}

# templates/scoring.md § "Wave 1 (v2.10)" — the Codex lane's agent name
# (codex_translate.py AGENT_NAME). The string ALONE proves nothing: a native agent
# can write it on its own finding. A member counts as Codex's only when the
# envelope's orchestrator-set `codex` block says the Codex pass joined
# (_codex_joined) — see _codex_corroborated.
CODEX_AGENT = "codex-adversarial"

# templates/scoring.md § "Wave 1 (v2.10)" — B-SEV lone-lane ceiling (D-02):
# critical needs a second opinion; a lone lane tops out at warning. A group with
# no second opinion (_second_opinion) has its SCORE capped at the critical floor
# minus one BEFORE band_for runs, so band_for stays the single band writer. The
# shipped value is "warning". `None` disables the ceiling and exists ONLY so
# scripts/replay.py can replay the other Wave-1 candidates ALONE (D-09).
LONE_LANE_BAND_CEILING = "warning"

# B-REWEIGHT (v2.10 Wave 1, D-15). DERIVED, not hand-picked: method + inputs in
# docs/design/b3-ground-truth/CALIBRATION-v2.10.md; re-derive with
# `python3 plugins/vibe-check/scripts/calibrate.py --check` (test_calibrate binds this literal to
# the derivation). Lower-only; lone-lane groups only; absent agent => 0 (identity).
AGENT_CONFIDENCE_OFFSET = {"architecture": -6, "bugs": -2, "impact": -12}

# HARDEN-01 — DOCUMENTATION ONLY (not a reject gate). The three fields a
# well-formed finding normally carries. Per orchestrator correction (this phase),
# a missing / null / non-str value for any of these does NOT make a finding
# malformed: score.py is already null-safe for them (stable_hash and _first_line
# coerce None -> ""), so such a finding flows through and scores. Only a NON-DICT
# container is a crash and gets rejected by `_valid_finding`. This tuple is kept
# as a reference for the expected shape; it intentionally gates nothing.
_REQUIRED_KEYS = ("file", "title", "category")

# The persisted-envelope key set (fixtures/future-schema.json `finding_required` /
# `finding_optional`; test_score locks the equality). The scorer is the single
# normalizer and Phase 4.5 persists its `findings` array unchanged, so what run()
# emits must fit this closed set. Shaping happens at the OUTPUT boundary only:
# bands, scores and stable_hash are computed first and are byte-identical with
# or without it (2026-09-28: a language-python finding arrived with no `id`, no
# `title` and a `suggested_fix` key; W1 kept it, the closed schema rejected it).
FINDING_REQUIRED_KEYS = ("id", "file", "line", "title", "category", "severity", "agent",
                         "agent_confidence", "problem", "source_window", "orchestrator_score",
                         "band", "attribution", "status", "stable_hash")
FINDING_OPTIONAL_KEYS = ("cwe", "why_it_matters", "fix_hint", "current_code", "in_diff",
                         "silenced_marker_nearby", "intent_doc_match", "canonical_line_content",
                         "members", "snapshot", "kept_open")
# H-LANE (v2.10 Wave 1, D-14): a surviving row's `members` is a list of member
# RECORDS — each the finding INPUT key set below, i.e. exactly what a finding
# arrives with (its ORIGINAL multi-line current_code and its own source_window,
# verbatim), so a member can be carried and re-scored on a later pass through the
# identical per-finding path. Excluded: the scorer OUTPUTS (recomputed every pass),
# the hard-rule-#4 booleans (recomputed from raw facts, so an agent's claim carries
# no evidence), the output-boundary `id`, and `canonical_line_content` — a PER-PASS
# orchestrator HEAD read (30-collect-score.md step 0) that a stored copy must never
# stand in for (T-41-37). state_shape validates finding keys only; the member-record
# shape is this module's own contract (test_score TestSiteGroupingHLane).
# `snapshot` (the decision snapshot) is a per-row scorer OUTPUT recomputed every
# pass, never member evidence; `kept_open` (the sub-threshold obligation marker)
# is likewise a per-row scorer output.
_MEMBER_EXCLUDED_KEYS = ("id", "orchestrator_score", "band", "attribution", "status",
                         "stable_hash", "members", "in_diff", "silenced_marker_nearby",
                         "canonical_line_content", "snapshot", "kept_open")
MEMBER_KEYS = tuple(k for k in FINDING_REQUIRED_KEYS + FINDING_OPTIONAL_KEYS
                    if k not in _MEMBER_EXCLUDED_KEYS)
_FINDING_KEY_SYNONYMS = {"suggested_fix": "fix_hint"}
_UNTITLED = "(untitled finding)"


def _shape_finding(f):
    """Fit one scored finding to the persisted-envelope key set (shape only)."""
    out = dict(f)
    for src, dst in _FINDING_KEY_SYNONYMS.items():
        if src in out:
            cur = out.get(dst)
            if (not isinstance(cur, str) or not cur.strip()) and isinstance(out[src], str):
                out[dst] = out[src]
    allowed = set(FINDING_REQUIRED_KEYS) | set(FINDING_OPTIONAL_KEYS)
    out = {k: v for k, v in out.items() if k in allowed}
    if not isinstance(out.get("id"), str) or not out["id"].strip():
        out["id"] = "%s-%s" % (out.get("agent") or "agent", str(out.get("stable_hash") or "")[:8])
    if not isinstance(out.get("title"), str) or not out["title"].strip():
        title = ""
        prob = out.get("problem")
        if isinstance(prob, str) and prob.strip():
            first = prob.strip().splitlines()[0].strip()
            m = re.match(r"(.{1,80}?[.!?])(\s|$)", first)
            title = m.group(1) if m else first[:80]
        out["title"] = title or _UNTITLED
    return out


def _snapshot_for(row, pass_number):
    """The decision snapshot for one emitted row: {at_pass, file, line,
    canonical_line_content, band}.

    A row arriving with a well-formed prior snapshot (a carried lead: the carry
    loop copies every carryforward key except `members`) keeps it — older
    `at_pass` included — while its file, line, HEAD canonical text and band all
    equal this pass's values; anything else gets a fresh snapshot at this pass.
    Evidence is the HEAD canonical line, never `current_code` (a quoted fragment
    never equals HEAD, so keying on it would make every such row "changed"); the
    status component is the band, not the carry status (which flips new ->
    persisted between passes with no change at all). Pure; never raises.
    """
    canonical = row.get("canonical_line_content")
    cur = {
        "at_pass": _as_line(pass_number),
        "file": row.get("file"),
        "line": _as_line(row.get("line")),
        "canonical_line_content": canonical if isinstance(canonical, str) else None,
        "band": row.get("band"),
    }
    prior = row.get("snapshot")
    if (isinstance(prior, dict) and _as_line(prior.get("at_pass")) is not None
            and all(k in prior and prior[k] == cur[k]
                    for k in ("file", "line", "canonical_line_content", "band"))):
        return {"at_pass": prior["at_pass"], "file": cur["file"], "line": cur["line"],
                "canonical_line_content": cur["canonical_line_content"],
                "band": cur["band"]}
    return cur


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
def stable_hash(file, canonical_line_content, title):
    """sha256(file + "\\x00" + canonical_line_content + "\\x00" + title).

    Keys medium_acknowledgments (review.md:34,:43) — any separator/encoding/
    field-order drift silently breaks persisted dismissals, so the golden digest
    is frozen in the test suite (now
    7a516d0120c0ff3110198c731f49a775d55dd06071e1831e4a554c7bff793124).

    Separator is NUL ("\\x00"), NOT newline: a newline separator is forgeable
    because newlines can appear inside these text fields, so a crafted finding
    could collide with a prior dismissal's hash and be silently suppressed
    (e.g. title="y\\nz" vs canonical="x\\ny" once collided). NUL cannot appear in
    any of file / canonical_line_content / title, so the encoding is injective.

    None-safe: a present-but-null field (JSON `null` survives `.get`) is coerced
    to "" rather than raising TypeError — a single malformed-but-parseable finding
    must not crash the scorer and trip the orchestrator's fail-closed halt.
    """
    file = file if isinstance(file, str) else ""
    canonical_line_content = (canonical_line_content
                              if isinstance(canonical_line_content, str) else "")
    title = title if isinstance(title, str) else ""
    # "surrogatepass" (Fable A6): a lone surrogate ("\ud800") is LEGAL JSON text
    # that json.load accepts, but a plain .encode() raises UnicodeEncodeError —
    # one crafted finding would halt the whole run at the fail-closed gate.
    # surrogatepass encodes it deterministically (distinct surrogates stay
    # distinct bytes, so injectivity holds) and is byte-identical to strict UTF-8
    # for all valid text — the frozen golden digest is unmoved.
    return hashlib.sha256(
        (file + "\x00" + canonical_line_content + "\x00" + title)
        .encode("utf-8", "surrogatepass")
    ).hexdigest()


def _canonical_for_hash(f):
    """The canonical line text a finding's stable_hash is keyed on.

    The orchestrator-resolved `canonical_line_content` when present (carry-forward
    path, and fresh findings enriched by 30-collect-score.md), else the finding's
    own first `current_code` line (diff-mode findings carry no separate
    canonical). One rule in one place: _score_member and _finding_identity both
    call it. Non-str values pass through; stable_hash coerces them to "".
    """
    canonical = f.get("canonical_line_content")
    if canonical is None:
        canonical = _first_line(f.get("current_code", ""))
    return canonical if canonical is not None else ""


def _finding_identity(f):
    """The lane-aware OCCURRENCE identity of one finding (H-LANE member records).

    (agent, stable_hash(file, canonical, title), line). stable_hash alone cannot
    tell two identical lines carrying one title apart (it has no line number),
    and (stable_hash, line) cannot tell two lanes reporting one title at one line
    apart — so the agent and the line are both part of the identity. Used ONLY to
    de-duplicate a row's `members` and to recognise the representative's own
    record in _expand_members; stable_hash itself (the frozen dismissal / carry
    key) is unchanged. Never raises: non-str agent/file/title coerce to "", a
    non-int line to None.
    """
    agent = f.get("agent")
    file = f.get("file")
    title = f.get("title")
    return (
        agent if isinstance(agent, str) else "",
        stable_hash(file if isinstance(file, str) else "",
                    _canonical_for_hash(f),
                    title if isinstance(title, str) else ""),
        _as_line(f.get("line")),
    )


def _member_ref(m):
    """Project a finding to its member record (MEMBER_KEYS), values verbatim.

    An absent optional key stays absent; `current_code` and `source_window` are
    copied as-is (never projected to one line). Only the identity/location
    fields are coerced: agent/file/title to str-or-"", line via _as_line
    (malformed input never raises and never breaks identity).
    """
    ref = {k: m[k] for k in MEMBER_KEYS if k in m}
    for k in ("agent", "file", "title"):
        v = m.get(k)
        ref[k] = v if isinstance(v, str) else ""
    ref["line"] = _as_line(m.get("line"))
    return ref


def _usable_bands(thresholds):
    """Return a validated {critical,warning,medium} band-floor dict, or _DEFAULT_BANDS.

    CRASH-SAFE (Finding #2 / T-30-06). The `thresholds` value arrives on the stdin
    envelope from the orchestrator (which got it from config.py). config.py validates
    it UPSTREAM (strictly-descending ints in [1,100], medium>=70) and should never send
    a malformed value — but score.py must not TRUST its input: a stale or buggy config.py
    must never crash the scorer. So this accepts the dict ONLY when all three floors are
    present AND each is a USABLE non-bool int; on ANY violation it falls back to the WHOLE
    built-in _DEFAULT_BANDS set (not a per-sub-key mix), matching config.py's whole-set
    posture and keeping the reasoning trivial.

    The bool exclusion is mandatory: `isinstance(True, int)` is True, so a plain int
    check would wrongly accept a bool floor. A WRONG-TYPE sub-key — e.g. {"critical":"80"}
    (string), None, or a float — would otherwise reach `score >= "80"` and raise TypeError;
    this guard prevents that. A non-dict thresholds (incl. None, the zero-config path)
    also falls back to the whole default set. This mirrors score.py's existing null/
    type-safe posture (stable_hash / _safe_window): coerce-or-default, never raise.
    """
    # Return a COPY of the frozen default (dict(...)) — never the module-level object
    # by reference — so a future caller that mutates the returned band-floor dict
    # cannot silently corrupt _DEFAULT_BANDS and the frozen GOLDEN_DIGEST (bugs-003 /
    # lang-py-002). Behavior is unchanged: band_for only READS these values.
    if not isinstance(thresholds, dict):
        return dict(_DEFAULT_BANDS)
    floors = {}
    for key in ("critical", "warning", "medium"):
        v = thresholds.get(key)
        # Present AND a usable non-bool int, else the WHOLE set defaults.
        if not (isinstance(v, int) and not isinstance(v, bool)):
            return dict(_DEFAULT_BANDS)
        floors[key] = v
    return floors


def _codex_joined(envelope):
    """True iff the envelope's orchestrator-set `codex` block says the pass joined.

    The block (`{"status": "joined" | "skipped" | "off"}`, phases/review/
    30-collect-score.md) is written by the orchestrator from the Phase-3 Codex
    outcome — the same source Phase 4.5 persists as the pass-level `codex.status`.
    It is the ONLY provenance source: a finding's own `agent` / `category` are
    agent self-reports, and a native agent reviewing an attacker-authored diff can
    write `agent: "codex-adversarial"` or `category: "adversarial"` to fake
    corroboration (T1). Coerce-or-default: a non-dict block, a non-str status, or
    an absent block => False (no finding is Codex's). Never raises.
    """
    if not isinstance(envelope, dict):
        return False
    block = envelope.get("codex")
    if not isinstance(block, dict):
        return False
    return block.get("status") == "joined"


def _codex_corroborated(members, codex_joined):
    """A Codex member AND a Claude-lane member in one group, Codex verified joined.

    Codex is the independent voter (D-01); Claude<->Claude agreement is one
    correlated voter and does NOT count. `codex_joined` must come from
    _codex_joined(envelope) — without it a member labelled CODEX_AGENT is an
    unverified self-report and earns nothing (T1). Only str `agent` values count
    on either side (a missing / non-str agent is neither Codex nor a Claude lane).
    """
    if not codex_joined:
        return False
    agents = [m.get("agent") for m in members if isinstance(m, dict)]
    agents = [a for a in agents if isinstance(a, str)]
    return (any(a == CODEX_AGENT for a in agents)
            and any(a != CODEX_AGENT for a in agents))


def _second_opinion(members, codex_joined, persisted_ids):
    """D-01 second opinion: Codex-corroborated, OR persisted from a previous pass.

    Persistence is the identity set the carry-forward loop builds (Fable A5) —
    never a member's own `status`, which is an agent-writable field. `in_diff` is
    NOT a corroborator.
    """
    if _codex_corroborated(members, codex_joined):
        return True
    return any(id(m) in persisted_ids for m in members)


def _agent_offset(member):
    """The B-REWEIGHT confidence offset for one member (D-15). LOWER-ONLY.

    Scoped to members of a group with NO second opinion — the caller
    (_score_member) passes 0 whenever the group is Codex-corroborated or
    persisted. Returns AGENT_CONFIDENCE_OFFSET[agent] (always <= 0); an unknown
    agent, a non-str `agent`, or a non-int / positive table value is identity (0),
    so the offset can never raise a score and a malformed finding never crashes.
    It feeds ONLY compute_score's starting value — never the emitted
    `agent_confidence`, never the stable_hash inputs, and never the
    min_confidence filter (which reads the raw value).
    """
    agent = member.get("agent")
    if not isinstance(agent, str):
        return 0
    off = AGENT_CONFIDENCE_OFFSET.get(agent, 0)
    if not isinstance(off, int) or isinstance(off, bool) or off > 0:
        return 0
    return off


def _lone_lane_cap(thresholds):
    """The score cap for a group with no second opinion, or None when disabled.

    critical floor - 1 (94 by default; a config-tuned `thresholds.critical` is
    respected via _usable_bands), so a lone lane can band warning but never
    critical. None when LONE_LANE_BAND_CEILING is None (replay-only override).
    """
    if LONE_LANE_BAND_CEILING != "warning":
        return None
    bands = _usable_bands(thresholds)
    return bands["critical"] - 1


def band_for(score, thresholds=None):
    """Score -> band (scoring.md:37-42). <medium floor is below both thresholds => None.

    `thresholds` is an OPTIONAL band-floor override (v2.8 config knob, D-02). When it
    is absent / None OR malformed (non-dict, missing sub-key, or a wrong-type/non-int/
    bool sub-key), band_for uses the built-in _DEFAULT_BANDS literals (95/80/70) — so
    the no-config default path is byte-identical to v2.7 (the frozen GOLDEN_DIGEST and
    the 8 TestBandBoundaries assertions are unchanged). A fully-valid all-int dict is
    honored (tunable). See _usable_bands for the crash-safe validation (Finding #2).
    band_for is the SINGLE writer of `band` (single call site in run()); do not compute
    a band anywhere else.
    """
    bands = _usable_bands(thresholds)
    if score >= bands["critical"]:
        return "critical"
    if score >= bands["warning"]:
        return "warning"
    if score >= bands["medium"]:
        return "medium"
    return None


# --------------------------------------------------------------------------- #
# idiom_floor band cap (NOISE-01, D-01/D-02) — a per-category POST-band
# adjustment on `idiom`-category findings. band_for stays the single band
# WRITER; this is the ONE clearly-scoped adjustment applied immediately after the
# single band-write site, and it only ever LOWERS a band. See run() for the site.
# --------------------------------------------------------------------------- #

# Severity rung ordering for the cap comparison (critical > warning > medium >
# low > None). None is the LOWEST rung so a would-be-None idiom band is never
# "raised" to the cap. The literal band "low" IS a valid cap target (Finding
# NEW-2) — note band_for never RETURNS "low" (its floor is None), but the cap can
# WRITE "low" as the capped label.
_BAND_SEVERITY = {"critical": 4, "warning": 3, "medium": 2, "low": 1, None: 0}

# The valid idiom_floor cap bands (INCLUDING "low", Finding NEW-2) and the disable
# sentinels — mirrored from config.py's allowlist so the scorer re-validates
# independently ("don't trust your input", like _usable_bands).
_IDIOM_FLOOR_BANDS = ("critical", "warning", "medium", "low")
_IDIOM_FLOOR_DISABLE = ("off", "none")
_DEFAULT_IDIOM_FLOOR = "medium"   # A1: absent key => the cap is ACTIVE at medium.


def _usable_idiom_floor(raw):
    """Resolve the RAW `idiom_floor` envelope value to a usable cap band, or None.

    CRASH-SAFE, THREE-STATE (Finding #2, mirroring _usable_bands' "don't trust
    your input" posture — a stale/buggy config.py must never crash the scorer or
    silently disable the cap):

      1. `raw is None` (ABSENT key)                 -> "medium"  (cap ACTIVE, A1).
      2. `raw` is "off"/"none" (case-insensitive)   -> None      (cap DISABLED —
         the EXPLICIT user off; this is WHY config.py returns the literal "off"
         sentinel and not None, so an absent key and an explicit off are
         distinguishable HERE on the envelope).
      3. `raw` is a valid band name (incl. "low")   -> that band (cap at it).
      4. anything else (unknown string, non-str)    -> "medium"  (fail-safe: a bad
         value KEEPS the cap active, matching config.py's malformed->medium; an
         unknown string is NOT the off sentinel, so it never disables).

    The three-state resolution is CENTRALIZED here (not split with a
    `raw if raw is not None else "medium"` in run()) so the off-sentinel semantics
    are unambiguous in exactly one place.
    """
    if raw is None:
        return _DEFAULT_IDIOM_FLOOR
    if isinstance(raw, str):
        low = raw.lower()
        if low in _IDIOM_FLOOR_DISABLE:
            return None
        if low in _IDIOM_FLOOR_BANDS:
            return low
    return _DEFAULT_IDIOM_FLOOR


def _cap_idiom_band(category, band, idiom_floor):
    """Cap an `idiom`-category finding's `band` at idiom_floor. LOWER-ONLY.

    Scoped to category == "idiom" (D-02): a non-idiom finding is returned
    unchanged. The cap resolved by _usable_idiom_floor: None (disabled) => the
    band is returned unchanged; otherwise the band is lowered to the cap ONLY when
    it is strictly HIGHER-severity than the cap (never raised). Touches ONLY the
    band LABEL — never `category`, so a low-capped idiom finding STAYS
    category == "idiom" (Finding NEW-2; the render layer disambiguates by
    category, Plan 03).
    """
    if category != "idiom":
        return band
    cap = _usable_idiom_floor(idiom_floor)
    if cap is None:
        return band  # explicit off/none => cap disabled.
    if _BAND_SEVERITY.get(band, 0) > _BAND_SEVERITY[cap]:
        return cap
    return band


def _effective_band(member, score, thresholds, idiom_floor):
    """One member's band: band_for(score) then the idiom cap by ITS OWN category.

    H-LANE applies the idiom cap per member, before the row's representative is
    chosen, so an idiom finding at a site can never lower the band of a
    co-located non-idiom (e.g. security) member. band_for stays the single band
    writer; this is the one post-band adjustment.
    """
    return _cap_idiom_band(member.get("category"), band_for(score, thresholds),
                           idiom_floor)


# --------------------------------------------------------------------------- #
# vibe-ignore reason-aware scan (NOISE-02/03, D-03) — a PER-TOKEN scan over the
# pre-resolved ±2 source_window. Returns one occurrence record per `vibe-ignore`
# TOKEN found (NOT one per line, NOT first-token-only), each carrying its window
# `index` (0=L-2 … 4=L+2) and its `kind` ("reasoned" | "bare"). A reasoned
# occurrence rides the EXISTING -50 silenced path (folded into silenced_nearby);
# a bare occurrence surfaces a synthetic audit finding in run().
#
# REPORT-ONLY LIMITATION (D-03, OUT OF SCOPE): a `vibe-ignore` token sitting
# INSIDE a string literal triggers this scan exactly as the 5 existing
# SILENCED_MARKERS substring markers already do (`eslint-disable` inside a string
# literal already suppresses identically). This is a PRE-EXISTING,
# comment-syntax-agnostic substring behavior shared by ALL markers; D-03 inherits
# it ("behaviorally consistent with the other markers"). We deliberately add NO
# comment-syntax parsing here that the other markers lack — the per-token
# iteration stays a pure substring/token scan over the pre-resolved window (no
# I/O, no comment-syntax parsing). This note builds no guard.
# --------------------------------------------------------------------------- #

# A colon then a NON-EMPTY (non-whitespace) reason ⇒ reasoned; else bare. The
# text scanned is only the segment AFTER a token up to (not consuming) the NEXT
# vibe-ignore token on the same line, so `// vibe-ignore // vibe-ignore: r`
# classifies the first token as bare (its trailing segment has no reason before
# the next token) and the second as reasoned.
_VIBE_IGNORE_REASON_RE = re.compile(r"\s*:\s*(\S.*)?$", re.DOTALL)


def _has_comment_leadin(line, pos):
    """Is the `_VIBE_IGNORE` token at `pos` preceded by a comment lead-in?

    A genuine marker begins a comment, so its token is preceded — after stripping
    intervening whitespace — by a comment lead-in (`//` or `#`) or by nothing at
    all (the token starts the line). A `vibe-ignore` occurrence preceded by an
    ordinary word character is REASON TEXT of an earlier marker (e.g. the second
    "vibe-ignore" in `// vibe-ignore: see other vibe-ignore usage above`), NOT a
    separate marker (bugs-001).
    """
    prefix = line[:pos].rstrip()
    return prefix == "" or prefix.endswith("//") or prefix.endswith("#")


def _is_marker_shaped_tail(line, pos):
    """Does the token at `pos` look like a real marker by its OWN trailing text?

    The comment-lead-in test alone (`_has_comment_leadin`) is NOT sufficient once
    an EARLIER marker on the same line is REASONED and its reason text quotes a
    sibling comment lead-in right before repeating the token (bugs-002), e.g.:

        // vibe-ignore: like the // vibe-ignore in foo.py
        # vibe-ignore: see the # vibe-ignore above

    Here the SECOND token's immediate prefix is `//`/`#`, so the lead-in test wrongly
    admits it as a fresh (bare) marker and splits it off — producing a spurious
    "suppression without reason" finding for a marker that IS reasoned.

    A GENUINE trailing marker is shaped like a marker in its own right: after its
    token, either nothing but whitespace remains (a real trailing BARE marker, e.g.
    `// vibe-ignore: reason // vibe-ignore`) or a colon-introduced reason follows (a
    real trailing REASONED marker, e.g. `// vibe-ignore // vibe-ignore: r`). Arbitrary
    prose continuing the earlier reason (` in foo.py`) is neither, so it is rejected
    as in-reason text. This distinguishes bugs-002's in-reason quote from the genuine
    trailing-marker contracts, both of which the tests lock.
    """
    tail = line[pos + len(_VIBE_IGNORE):]
    return tail.strip() == "" or bool(_VIBE_IGNORE_REASON_RE.match(tail))


def _is_fresh_marker_start(line, pos):
    """Is the `_VIBE_IGNORE` token at `pos` a GENUINE fresh marker start?

    Combines both signals: a genuine subsequent marker (a) opens a fresh `//`/`#`
    comment (`_has_comment_leadin` — drops in-reason prose whose token is preceded
    by an ordinary word, bugs-001) AND (b) is itself marker-shaped by its own tail
    (`_is_marker_shaped_tail` — drops an in-reason quote of a sibling lead-in that
    continues into prose, bugs-002). Both are required so the same-line contracts
    hold (`// vibe-ignore: r // vibe-ignore` still detects the trailing bare marker;
    `// vibe-ignore // vibe-ignore: r` still detects both) while a REASONED marker
    whose reason quotes another comment lead-in is NOT mis-split.
    """
    return _has_comment_leadin(line, pos) and _is_marker_shaped_tail(line, pos)


def _vibe_ignore_scan(source_window):
    """Per-TOKEN reason-aware scan of the ±2 window for `vibe-ignore` markers.

    Returns a LIST of occurrence dicts — ONE per `_VIBE_IGNORE` TOKEN found in the
    window (Finding #2: iterate every token in each line, not just the first) —
    each `{"index": <0-based window index>, "kind": "reasoned"|"bare"}`.

    For each string window line, the `_VIBE_IGNORE` occurrences that are GENUINE
    markers are walked (bugs-001: the first occurrence, plus any subsequent
    occurrence that is a fresh comment-marker start per _is_fresh_marker_start — an
    in-reason `vibe-ignore` word inside an earlier marker's reason is NOT a
    separate marker and is skipped). For each genuine marker, the text AFTER that
    token up to (but not consuming) the NEXT genuine `_VIBE_IGNORE` marker on the
    line is classified: a colon then a non-empty (`.strip()` non-blank) reason ⇒
    "reasoned"; otherwise (no colon, colon with only-whitespace reason, or the next
    marker immediately follows) ⇒ "bare". Non-str lines are skipped. Pure scan over
    the pre-resolved window (no I/O); never raises on malformed window content
    (mirrors silenced_nearby's crash-safe posture, T-32-05).
    """
    occurrences = []
    if not source_window:
        return occurrences
    tok_len = len(_VIBE_IGNORE)
    for index, line in enumerate(source_window):
        if not isinstance(line, str):
            continue
        # Collect this line's token start offsets first, so each token's trailing
        # segment can end at the NEXT token's start (not the line end).
        raw_starts = []
        pos = line.find(_VIBE_IGNORE)
        while pos != -1:
            raw_starts.append(pos)
            pos = line.find(_VIBE_IGNORE, pos + tok_len)
        # bugs-001: keep the FIRST occurrence unconditionally (preserving the
        # deliberate substring/prose behavior shared with the other markers), but
        # DROP any SUBSEQUENT occurrence that is not a fresh comment-marker start —
        # such an occurrence is `vibe-ignore` text INSIDE an earlier marker's reason
        # (e.g. `// vibe-ignore: see other vibe-ignore usage`), NOT a real second
        # marker. Dropping it means a reasoned token's reason segment correctly
        # extends past the in-reason word to the next GENUINE marker (or line end),
        # so the reasoned marker is no longer mis-split into a false bare finding.
        starts = [s for i, s in enumerate(raw_starts)
                  if i == 0 or _is_fresh_marker_start(line, s)]
        for k, start in enumerate(starts):
            seg_start = start + tok_len
            seg_end = starts[k + 1] if k + 1 < len(starts) else len(line)
            after = line[seg_start:seg_end]
            m = _VIBE_IGNORE_REASON_RE.match(after)
            reasoned = bool(m and m.group(1) and m.group(1).strip())
            occurrences.append({
                "index": index,
                "kind": "reasoned" if reasoned else "bare",
            })
    return occurrences


def silenced_nearby(source_window):
    """Any of the 5 canonical markers, OR any REASONED vibe-ignore, in the ±2 window.

    The orchestrator supplies source_window = [L-2, L-1, L, L+1, L+2] pre-resolved
    (D-05); this is a pure substring scan. D-13 inclusive [L-2 .. L+2].

    NOISE-02 (D-03): a `vibe-ignore: <reason>` marker (a REASONED occurrence from
    _vibe_ignore_scan) OR-s in exactly like the 5 fixed-string markers, so the
    nearby finding takes the existing -50 (compute_score) and drops with reason
    "silenced". A BARE `vibe-ignore` does NOT set silenced (that is run()'s
    synthetic-finding job, NOISE-03).
    """
    if not source_window:
        return False
    # Case-insensitive (Fable A13): needles are all-lowercase, so match against
    # the lowered line (catches `# NOQA` and any other case drift).
    if any(marker in line.lower()
           for line in source_window
           for marker in SILENCED_MARKERS
           if isinstance(line, str)):
        return True
    return any(o["kind"] == "reasoned" for o in _vibe_ignore_scan(source_window))


def _first_line(text):
    """First line of a (possibly multi-line) snippet, or '' for falsy input.

    Non-string input (a JSON number/object from a malformed-but-parseable
    finding's ``current_code``) coerces to '' rather than raising — a single
    odd finding must not crash run() and trip the orchestrator fail-closed halt
    (completes the W1 null/non-str hardening for the sibling text field).
    """
    if not text or not isinstance(text, str):
        return ""
    return text.split("\n", 1)[0]


def _nonblank_lines(text):
    """The stripped NON-BLANK lines of `text`, in order.

    Non-str input (a JSON number/object from a malformed-but-parseable finding's
    ``current_code`` / a resolved window) yields [] rather than raising — the
    same never-crash posture as _first_line (Pattern 1). Blank / whitespace-only
    lines are dropped so cosmetic blank-line drift does not move the carry key.
    """
    if not text or not isinstance(text, str):
        return []
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


def _carry_key(text):
    """The windowed carry-forward key for ONE side (ROBUST-03).

    The first <=3 stripped NON-BLANK lines of `text` joined with "\\n". Used ONLY
    by carry_forward_status's symmetric widen branch — it is SEPARATE from the
    canonical_for_hash path that feeds stable_hash (D-07), so the frozen golden
    digest does not move. Non-str input coerces to "" (never raises, Pattern 1).
    """
    return "\n".join(_nonblank_lines(text)[:3])


def _is_low_entropy(first):
    """Is a (stripped) first line low-entropy — too generic to key on alone?

    Low-entropy iff it is very short (`len < 4`) OR pure punctuation/whitespace/
    bracket characters (`}`, `);`, `})`, `]`). `re` is already in the frozen
    import set; `re.fullmatch(r"[\\s\\W]+", "")` is None, so the empty string is
    NOT low-entropy here (it is handled by the equal/not-equal first-line compare).
    """
    return len(first) < 4 or bool(re.fullmatch(r"[\s\W]+", first))


def carry_forward_status(finding, canonical_line_content, canonical_window=None):
    """Status of a carried-forward finding (review.md:672-678), ROBUST-03 hardened.

    The orchestrator reads HEAD and passes canonical_line_content in (D-05); it
    ALSO resolves a small surrounding HEAD window -> canonical_window (consumed
    ONLY here, never by the stable_hash path — D-07):
      - null/sentinel canonical (file:line gone) => "fixed-since-last"
      - else compare the prior `current_code` against HEAD; "persisted" iff they
        match, "needs-recheck" iff content changed.

    SYMMETRIC-OR-DEGRADE compare (round-2 BLOCKER 1): a low-entropy first line
    (e.g. `}`, `);`) is too generic to key on alone, so it is disambiguated by a
    surrounding window — but ONLY when a real >=2-line window exists on BOTH sides.
    The compare widens BOTH sides or NEITHER; it never compares a multi-line
    window against a single line (which would falsely flip a legal single-line
    snippet to needs-recheck).

      WIDEN-ELIGIBLE iff ALL of:
        - the LHS (current_code) stripped first line is low-entropy, AND
        - the prior current_code has >= 2 non-blank lines, AND
        - canonical_window is present with >= 2 non-blank lines.
      WIDEN  => persisted iff _carry_key(current_code) == _carry_key(canonical_window).
      DEGRADE (anything else: a distinctive first line, OR a single-line/low-entropy
        snippet with no second line on either side) => compare the stripped FIRST
        LINES exactly as before (byte-identical no-churn for distinctive lines AND
        legal single-line low-entropy snippets).

    D-11: strip leading AND trailing whitespace on both sides before comparing, so
    pure whitespace drift is not a false "fixed-since-last" / "needs-recheck".
    Pattern 1: non-str current_code coerces via _first_line / _nonblank_lines and
    never raises.
    """
    if canonical_line_content is None:
        return "fixed-since-last"
    # Pattern 1: a present-but-non-str canonical_line_content (a JSON
    # number/array/object from a malformed-but-parseable carryforward entry)
    # coerces to "" before .strip() rather than raising AttributeError — a
    # single odd finding must not crash run() and trip the orchestrator's
    # fail-closed halt. The None path above is preserved (still
    # "fixed-since-last"); ONLY the non-None-but-non-str case is coerced, so a
    # non-str canonical (first line "" != a real current_code first line)
    # classifies as needs-recheck rather than a false persisted/fixed.
    if not isinstance(canonical_line_content, str):
        canonical_line_content = ""
    current_code = finding.get("current_code", "")
    current_first = _first_line(current_code).strip()
    canonical_first = canonical_line_content.strip()

    # WIDEN-ELIGIBLE: both sides can form a real >=2-line window AND the first
    # line is generic enough to need the surrounding context to disambiguate.
    widen = (
        _is_low_entropy(current_first)
        and len(_nonblank_lines(current_code)) >= 2
        and len(_nonblank_lines(canonical_window)) >= 2
    )
    if widen:
        if _carry_key(current_code) == _carry_key(canonical_window):
            return "persisted"
        return "needs-recheck"

    # DEGRADE: first-line compare (today's behavior — no churn for distinctive
    # first lines AND for legal single-line / window-less low-entropy snippets).
    if current_first == canonical_first:
        return "persisted"
    return "needs-recheck"


def _expand_members(cf):
    """Expand one carried row's `members` into independent working findings.

    H-LANE (v2.10 Wave 1): an absorbed defect must never vanish with its lead —
    not when the lead is fixed, suppressed at its own line or falls below the
    threshold. The orchestrator reads HEAD for every member at the member's OWN
    file:line (30-collect-score.md step 0: `canonical_line_content` AND
    `canonical_window` on each members[] entry). Each member record is carried
    through the identical per-finding call, carry_forward_status(record, head,
    window), and later scored on its own facts.

    The representative's own record (same lane, same occurrence —
    _finding_identity) is skipped: the caller carries the representative itself.
    A member with no HEAD read (absent/null) is `fixed-since-last` and recorded
    as a stub, never carried on faith (T-41-37). Working findings carry no
    `members` and no `id`. Returns (expanded, fixed). Pure; never raises — a
    malformed entry (non-dict, non-str agent or title) is skipped, siblings kept.
    """
    raw_members = cf.get("members")
    if not isinstance(raw_members, list):
        return [], []
    rep = {k: v for k, v in cf.items() if k != "members"}
    rep_id = _finding_identity(rep)
    expanded = []
    fixed = []
    for raw in raw_members:
        if not isinstance(raw, dict):
            continue
        if not isinstance(raw.get("agent"), str) or not isinstance(raw.get("title"), str):
            continue
        e = _member_ref(raw)
        head = raw.get("canonical_line_content")
        window = raw.get("canonical_window")
        if _finding_identity(dict(e, canonical_line_content=head)) == rep_id:
            continue
        st = carry_forward_status(e, head, window)
        if st == "fixed-since-last":
            fixed.append({
                "file": e.get("file"),
                "line": e.get("line"),
                "title": e.get("title"),
                "band": None,
                "first_pass_N": None,
            })
            continue
        expanded.append(dict(e, canonical_line_content=head, status=st))
    return expanded, fixed


def _intent_doc_penalty(finding):
    """Mutually-exclusive intent-doc penalty (D-12, scoring.md:16-17).

    confidence > 0.9 => -100 (REPLACES the -30, does not stack); elif > 0.7 => -30.
    Strictly greater-than. Defensive: a malformed/None intent_doc_match (no usable
    numeric confidence) is treated as no match (T-16-02 / V5).
    """
    m = finding.get("intent_doc_match")
    if not isinstance(m, dict):
        return 0
    conf = m.get("confidence")
    if not isinstance(conf, (int, float)):
        return 0  # malformed => no match
    if conf > 0.9:
        return -100
    elif conf > 0.7:
        return -30
    return 0


def _coerce_confidence(raw):
    """Coerce a raw agent_confidence VALUE to an int; garbage => 0 (single source
    of truth, reused by compute_score AND the min_confidence filter so the two can
    never drift).

    Accept int OR float (JSON from LLM agents routinely carries floats like 85.0),
    but reject bool (True is an int subclass) — mirrors the numeric guard in
    _intent_doc_penalty. A float is truncated via int().
    NON-FINITE guard (HOLE 2): json.load accepts bare NaN/Infinity/-Infinity as
    floats; they pass the isinstance(int,float) check, then int(float('nan')) raises
    ValueError and int(float('inf')) raises OverflowError. The import-free bound
    `-1e308 < raw < 1e308` rejects all three (every comparison with NaN is False;
    inf < 1e308 is False; -1e308 < -inf is False) while any legitimate 0-100
    confidence (incl. floats like 85.0) passes — so a non-finite confidence coerces
    to 0 like other garbage instead of crashing. (`import math` is FORBIDDEN here:
    the AST import-ban test pins the import set to {json,hashlib,re,sys}.)
    """
    return (int(raw)
            if isinstance(raw, (int, float)) and not isinstance(raw, bool)
            and -1e308 < raw < 1e308
            else 0)


def compute_score(finding, *, in_diff, silenced, cross_confirmed, persisted,
                  confidence_offset=0):
    """Apply the score formula (scoring.md:11-29) in the LOCKED operation order.

    Returns the clamped [0,100] orchestrator_score, OR None as the DROP signal when
    the pre-clamp score < 0 (D-14 — the caller removes the finding and records it in
    filtered[]; it is NOT clamped-to-0-and-emitted).

    in_diff / silenced / cross_confirmed / persisted are the orchestrator-verified
    booleans the caller computes (recomputed from raw facts, overriding agent
    self-reports per agent-output-schema hard rule #4); compute_score does not
    re-derive them.

    `confidence_offset` is the B-REWEIGHT lone-lane offset (_agent_offset), <= 0
    by construction; the default 0 is identity.
    """
    # 1. Start from agent_confidence (defensive coercion: garbage => 0). The
    # coercion (int/float accepted, float truncated, bool/non-finite/garbage => 0)
    # lives in _coerce_confidence so it is the SINGLE source of truth shared with
    # the min_confidence pre-scoring filter (they can never drift).
    # scoring.md:86 — plus the lone-lane B-REWEIGHT offset (<= 0 by construction).
    s = _coerce_confidence(finding.get("agent_confidence", 0)) + confidence_offset

    # 2. Additive/subtractive bonuses (intent-doc penalty is mutually exclusive).
    if in_diff:
        s += 20                                   # scoring.md:13
    if silenced:
        s -= 50                                   # scoring.md:14
    if finding.get("agent") == "compliance":
        s += 20                                   # scoring.md:15
    s += _intent_doc_penalty(finding)             # scoring.md:16-17 (elif, D-12)
    if cross_confirmed:
        s += 10                                   # scoring.md:18 (once; Codex + Claude, D-01)
    if persisted:
        s += 15                                   # scoring.md:19

    # 3. Severity weight LAST, before clamp (scoring.md:21-26). Unset/other => -8.
    # Fable A6: a non-str severity (a list/dict from a malformed-but-parseable
    # finding) is UNHASHABLE — a raw dict.get would TypeError, exit non-zero, and
    # halt the WHOLE run at the orchestrator's fail-closed gate. Non-str coerces
    # to None, which takes the same -8 fallback as any unrecognized severity.
    severity = finding.get("severity")
    if not isinstance(severity, str):
        severity = None
    s += SEVERITY_WEIGHT.get(severity, SEVERITY_FALLBACK)

    # 4. pre_clamp.
    pre_clamp = s

    # 5. Drop rule (D-14): pre-clamp < 0 => DROP entirely (signal None to caller).
    if pre_clamp < 0:
        return None

    # 6. Clamp survivors to [0, 100].
    return max(0, min(100, pre_clamp))


def _titles_match(title_a, title_b):
    """DEAD as a cross-confirm signal (ROBUST-02 / D-01) — retained only as an
    inert artifact of the Phase-16 extraction. Title text is NO LONGER a match
    signal: a shared title token alone must NEVER fire a +10 cross-confirmation
    (it was gameable by phrasing — codex-adversarial.md used to coach exactly
    that). `cross_confirm_group` groups by site (file + ±2 lines) only, and the
    +10 is decided from provenance (D-01). This function is intentionally
    UNREFERENCED; do not re-wire it into the matcher.
    """
    a = (title_a or "").lower()
    b = (title_b or "").lower()
    if len(a) <= len(b):
        return a in b
    return b in a


def _line_close(finding_a, finding_b):
    """same file AND |line_a - line_b| <= 2, with the defensive line guard.

    A present-but-null / non-int line (file-level findings legitimately carry
    line=null) is NOT a usable ±2 coordinate: if EITHER line is non-int the
    proximity check is False (no grouping on line) rather than crashing on
    abs(None - 0).
    """
    if finding_a.get("file") != finding_b.get("file"):
        return False
    line_a = _as_line(finding_a.get("line"))
    line_b = _as_line(finding_b.get("line"))
    return (line_a is not None and line_b is not None
            and abs(line_a - line_b) <= 2)


def cross_confirm_group(findings):
    """Group findings by SITE — ORDER-INDEPENDENT (H-LANE, v2.10 Wave 1, D-03/D-14).

    A SITE is the same file within ±2 lines (_line_close). Every lane at a site —
    native Claude agents and Codex alike — is ONE row, whatever each finding's
    category: category no longer affects grouping. Components are the connected
    components of the SYMMETRIC _line_close relation, computed by union-find over
    all pairs, so membership never depends on input order (a greedy "join the
    first match" loop would). A ±2 chain (10, 12, 14) is one site.

    Return shape: a list of group dicts, in first-appearance order of each
    component's lowest input index, members in input order within a group:
      {"members": [findings...], "attribution": [unique str agent names]}
    This function only establishes grouping + attribution. Whether a group earns
    the +10 is decided by the caller from provenance (D-01, _codex_corroborated):
    only a Codex member (envelope-verified) plus a Claude-lane member counts —
    Claude<->Claude agreement at one site earns nothing.

    Pattern 1 (never raise): a non-int line or a non-str file is not co-located
    with anything (the finding stands alone); a non-str agent is left out of
    `attribution`.
    """
    # parent[] indexes into `findings`. Classic union-find with path compression;
    # implemented by hand (no itertools/extra imports — frozen import set).
    parent = list(range(len(findings)))

    def find(i):
        root = i
        while parent[root] != root:
            root = parent[root]
        # path compression
        while parent[i] != root:
            parent[i], i = root, parent[i]
        return root

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(len(findings)):
        for j in range(i + 1, len(findings)):
            if _line_close(findings[i], findings[j]):
                union(i, j)

    # Materialize components in first-appearance order (iterating i ascending
    # meets each component first at its lowest input index).
    comp_index = {}          # root -> position in `components`
    components = []
    for i in range(len(findings)):
        root = find(i)
        if root not in comp_index:
            comp_index[root] = len(components)
            components.append({"members": [], "attribution": []})
        comp = components[comp_index[root]]
        f = findings[i]
        comp["members"].append(f)
        agent = f.get("agent")
        if isinstance(agent, str) and agent not in comp["attribution"]:
            comp["attribution"].append(agent)
    return components


# --------------------------------------------------------------------------- #
# Orchestrating function over the pure helpers
# --------------------------------------------------------------------------- #
def run(envelope):
    """Process one review pass: findings + context in, scored survivors out.

    Steps (mirroring review.md Phase 3):
      - merge carryforward findings into the working set, computing their status
        (fixed-since-last excluded; persisted flagged for +15; needs-recheck kept);
        each carried row's `members` is expanded into findings of their own
      - group by site (file, ±2 lines) BEFORE final scoring; the +10 needs a
        Codex + Claude pair with the envelope codex block joined (D-01)
      - recompute in_diff (from changed_line_ranges) / in_reviewed_set (from
        reviewed_union + file_line_totals when all_mode) and silenced (from
        source_window), overriding agent self-reports (hard rule #4)
      - score; drop pre-clamp<0; band; per-command threshold filter
      - assemble the stdout envelope with the scored_by_script sentinel
    """
    command = envelope.get("command", "review")
    all_mode = bool(envelope.get("all_mode", False))
    changed_line_ranges = envelope.get("changed_line_ranges", {}) or {}
    reviewed_union = set(envelope.get("reviewed_union", []) or [])
    file_line_totals = envelope.get("file_line_totals", {}) or {}
    # v2.8 config knob (D-02, CONFIG-04): optional band-floor override. No `or {}` —
    # absent AND explicit-None both yield None, so band_for uses the built-in literals
    # and a zero-config run stays byte-identical. band_for() is crash-safe against a
    # malformed value (whole-set fallback), so no re-validation is needed here.
    thresholds = envelope.get("thresholds")
    # v2.8 confidence knob (CONF-02, D-03/D-04): optional pre-scoring drop floor. No
    # `or 0` — absent AND explicit-None both yield None, which the isinstance(int)
    # gate below reads as "no filter" (byte-stable default). score.py's contract is
    # "crash-safe against ANY envelope value" regardless of who fills it, so the
    # filter guards the type itself (mirrors the thresholds crash-safety posture).
    min_confidence = envelope.get("min_confidence")
    # v2.8 idiom band cap (NOISE-01, D-01/D-02, A1): optional per-category cap on
    # `idiom`-category findings. No `or` coercion — the RAW value goes straight to
    # _cap_idiom_band, whose _usable_idiom_floor resolves the THREE distinct states
    # (absent/None -> the "medium" default cap ACTIVE per A1; the literal
    # "off"/"none" sentinel -> disabled; a valid band -> that cap). Centralizing the
    # absent->medium default INSIDE the helper (not `idiom_floor or "medium"` here)
    # is what keeps the explicit "off" sentinel distinguishable from an absent key.
    idiom_floor = envelope.get("idiom_floor")
    # v2.10 Wave 1 (D-01): orchestrator-verified Codex provenance for the B-SEV
    # second-opinion test. Absent block => not joined (no finding is Codex's).
    codex_joined = _codex_joined(envelope)
    # The pass this envelope scores: the decision snapshot's at_pass. A non-int
    # (absent, bool, str) records None rather than raising.
    pass_number = envelope.get("pass_number")

    # --- Envelope fail-closed list-guard (D-02, HARDEN-01) ------------------- #
    # `findings`/`carryforward` MUST be lists. A present-but-non-list value is a
    # broken envelope (an orchestrator contract violation), NOT recoverable agent
    # noise — so fail CLOSED: raise, which propagates through the unchanged
    # __main__ shim to a non-zero exit (preserving the ROBUST-04 "scoring ran"
    # honesty). This check runs BEFORE the `or []` coercion below so a FALSY
    # non-list (`{}`/`""`/`0`, C6) can no longer be SILENTLY masked into a fake
    # "0 findings clean review" — the most important D-02 case, because the mask
    # is otherwise invisible. Absent / None / empty stays a legal empty review
    # (only a present-non-list fails closed). Scope is ONLY findings/carryforward
    # (D-02 literal scope); changed_line_ranges/reviewed_union/file_line_totals are
    # orchestrator-controlled context and intentionally left unguarded.
    raw_findings = envelope.get("findings", [])
    raw_carryforward = envelope.get("carryforward", [])
    if raw_findings is not None and not isinstance(raw_findings, list):
        raise TypeError("malformed envelope: 'findings' must be a list, got "
                        + type(raw_findings).__name__)
    if raw_carryforward is not None and not isinstance(raw_carryforward, list):
        raise TypeError("malformed envelope: 'carryforward' must be a list, got "
                        + type(raw_carryforward).__name__)
    carryforward = raw_carryforward or []
    findings = list(raw_findings or [])

    threshold = THRESHOLDS.get(command, THRESHOLDS["review"])

    fixed_since_last = []
    filtered = []

    # --- Ingress malformed filter (HARDEN-01 / D-01) ------------------------- #
    # Validate the CONTAINER of every finding AND every carryforward entry at
    # ingress — BEFORE the carryforward loop (whose `cf.get(...)` would crash on a
    # non-dict cf, C2 / Pitfall 1) and BEFORE `working.extend(findings)` (whose
    # downstream `cross_confirm_group`/`_score_member` `.get` would crash on a
    # non-dict finding, C1). Malformed entries are skipped-and-reported to the
    # existing `filtered` bucket (no new output key). Pitfall 2: a reject member
    # may be a non-dict, so guard each `.get` accessor with `isinstance(m, dict)`
    # — calling `.get` unguarded here would re-introduce the very AttributeError
    # this filter prevents.
    def _route_malformed(m, reason):
        filtered.append({
            "file": m.get("file") if isinstance(m, dict) else None,
            "line": m.get("line") if isinstance(m, dict) else None,
            "title": m.get("title") if isinstance(m, dict) else None,
            "reason": reason,
        })

    valid_carryforward = []
    for cf in carryforward:
        ok, reason = _valid_finding(cf)
        if ok:
            valid_carryforward.append(cf)
        else:
            _route_malformed(cf, reason)
    carryforward = valid_carryforward

    valid_findings = []
    for f in findings:
        ok, reason = _valid_finding(f)
        if ok:
            valid_findings.append(f)
        else:
            _route_malformed(f, reason)
    findings = valid_findings

    # --- status scrub on NEW findings (Fable A5, security) ------------------- #
    # `status` is a SCORING input (+15 persisted, and the multi-pass carry-forward
    # allowlist) that only the carry-forward loop below may set. On a NEW agent
    # finding it is agent-forgeable: a finding arriving with "status":"persisted"
    # (an agent emitting an extra field — or an attacker-authored diff steering
    # one) would take the +15, enough to flip warning->critical or resurrect a
    # sub-threshold finding, and would render a fresh finding as "PERSISTED".
    # Hard rule #4 already recomputes in_diff/silenced from raw facts; scrub
    # `status` at the same trust boundary. Carryforward entries are untouched —
    # their status is ALWAYS recomputed by carry_forward_status below, never read
    # from the input.
    # `members` (H-LANE, v2.10 Wave 1) is scrubbed at the same boundary: it is
    # provenance the report renders as "flagged by" and Phase-43 scoring credits
    # for the axis (SUPERSESSIONS-v2.10.md 007), so an agent-supplied value is
    # forged provenance (T-41-32). Only orchestrator-supplied carryforward entries
    # (05-state.md forwards the persisted findings[] whole) may carry a prior-pass
    # `members`, and it is consumed ONLY by _expand_members (shape-validated,
    # never raises).
    # `snapshot` is the "unchanged since pass N" input to the decision prompt, so
    # a forged older `at_pass` would suppress a re-ask (T-46-10); `resolution` is
    # evidence only the verdict guard may produce; `kept_open` is an obligation
    # marker only the scorer may set. Carryforward entries keep theirs: a carried
    # snapshot is the prior-pass value the keep/refresh rule reads.
    findings = [{k: v for k, v in f.items()
                 if k not in ("status", "members", "snapshot", "resolution", "kept_open")}
                for f in findings]

    # --- Carry-forward (review.md:672-678) ----------------------------------- #
    # Each carryforward finding carries a pre-resolved canonical_line_content
    # (the orchestrator read HEAD). null => fixed-since-last (excluded).
    # H-LANE (v2.10 Wave 1): every carried row is expanded into its members
    # first; each member was evaluated at its OWN line by the orchestrator
    # (30-collect-score.md step 0) and is scored on its own facts, so an absorbed
    # defect is never dropped because its lead was fixed, suppressed or fell
    # below threshold. The representative itself is carried exactly as before;
    # survivors regroup by site below. A working finding never carries `members`
    # — the group loop rebuilds it from the scored members.
    persisted_ids = set()
    working = []
    for cf in carryforward:
        rep = {k: v for k, v in cf.items() if k != "members"}
        # A prior pass's obligation marker never rides on a row re-scored normally.
        rep.pop("kept_open", None)
        status = carry_forward_status(
            rep, cf.get("canonical_line_content"), cf.get("canonical_window")
        )
        if status == "fixed-since-last":
            fixed_since_last.append({
                "file": cf.get("file"),
                "line": cf.get("line"),
                "title": cf.get("title"),
                "band": cf.get("band"),
                "first_pass_N": cf.get("first_pass_N"),
            })
        else:
            # persisted / needs-recheck both flow through scoring (review.md:678).
            rep["status"] = status
            if status == "persisted":
                persisted_ids.add(id(rep))
            working.append(rep)
        expanded, fixed = _expand_members(cf)
        fixed_since_last.extend(fixed)
        for p in expanded:
            if p["status"] == "persisted":
                persisted_ids.add(id(p))
            working.append(p)
    working.extend(findings)

    # --- min_confidence pre-scoring filter (CONF-02, D-03) — BEFORE cross-confirm #
    # Drop any working finding (new OR carryforward — NO carve-out, D-03) whose
    # coerced agent_confidence < min_confidence, routing it to filtered[] with a
    # DISTINCT reason. Running BEFORE cross_confirm_group is what guarantees a
    # dropped finding neither cross-confirms nor influences any survivor's score
    # (CONF-02's "no influence" clause). The isinstance(int) gate is the crash-safe
    # short-circuit: a malformed/absent/None value leaves `working` UNTOUCHED so the
    # zero-config default path is byte-stable (GOLDEN_DIGEST unmoved). Strict `<` so
    # a finding at exactly N SURVIVES (CONF-02 "below N", D-03).
    if isinstance(min_confidence, int) and not isinstance(min_confidence, bool):
        kept_working = []
        for m in working:
            # reads RAW confidence — the B-REWEIGHT offset never feeds this filter (scoring.md § Wave 1)
            if _coerce_confidence(m.get("agent_confidence", 0)) < min_confidence:
                filtered.append({
                    "file": m.get("file"),
                    "line": m.get("line"),
                    "title": m.get("title"),
                    "reason": "below-min-confidence",
                })
            else:
                kept_working.append(m)
        working = kept_working

    # --- Bare vibe-ignore audit collection (NOISE-03, D-04, A2) -------------- #
    # Collect BARE vibe-ignore occurrences from every working member's window into
    # a de-dup set keyed by (file, marker_line). A bare marker does NOT suppress
    # (Task 1), so a member's fate (kept / silenced / sub-threshold) is irrelevant
    # to the audit — the marker's presence is a fact about the SOURCE, so we scan
    # `working` (all findings that reached scoring) independent of the drop/keep
    # loop below. De-dup by (file, marker_line): the SAME physical marker seen from
    # multiple co-located findings' windows collapses to ONE synthetic finding,
    # while two DISTINCT bare markers (distinct lines) stay two. The synthetic
    # findings are emitted AFTER the threshold filter (A2 exemption) so the
    # sub-threshold drop never sees them.
    bare_marker_keys = []          # ordered unique (file, marker_line) pairs
    _bare_seen = set()
    for member in working:
        window = _safe_window(member.get("source_window"))
        bare = [o for o in _vibe_ignore_scan(window) if o["kind"] == "bare"]
        if not bare:
            continue
        # lang-py-001 (crash guard, mirrors NEW-1 for the OTHER key half): coerce
        # `file` to a safe HASHABLE value BEFORE it enters the `(file, marker_line)`
        # set key. score.py accepts a malformed-but-parseable finding whose `file`
        # is a non-str, potentially UNHASHABLE shape (a list/dict) — a raw
        # `_bare_seen.add((file, marker_line))` / `key not in _bare_seen` on such a
        # value raises `TypeError: unhashable type`, exits non-zero, and halts the
        # WHOLE run at review.md's Phase 3 fail-closed gate (the same halt-class the
        # NEW-1 `line` guard prevents). Coerce to "" for any non-str, mirroring the
        # SYNTHETIC-FINDING block below (`file_str = file if isinstance(file, str)
        # else ""`), and thread this SAME coerced value through `bare_marker_keys`
        # so the emitted synthetic finding's `file` matches what was deduped.
        file_key = member.get("file")
        if not isinstance(file_key, str):
            file_key = ""
        # NEW-1 (crash guard): resolve the member's line through the EXISTING
        # _as_line helper FIRST. score.py DELIBERATELY accepts line:null (file-level
        # findings) and non-int lines (malformed-but-parseable) and MUST NOT raise
        # here — a raw `finding_line - 2 + index` on a null/str/float/bool line
        # would TypeError, exit non-zero, and halt the WHOLE run at review.md's
        # Phase 3 fail-closed check (T-32-10, the same halt-class as Finding #1
        # reached through a different trigger). A usable int => marker_line
        # arithmetic; None => marker_line stays None (line:null synthetic finding,
        # no arithmetic) — which still passes the Phase 3/4 gates (they do not
        # require a non-null line, Finding NEW-1).
        finding_line = _as_line(member.get("line"))
        for o in bare:
            if finding_line is not None:
                marker_line = finding_line - 2 + o["index"]  # 0=L-2 … 4=L+2
            else:
                marker_line = None
            key = (file_key, marker_line)
            if key not in _bare_seen:
                _bare_seen.add(key)
                bare_marker_keys.append(key)

    # --- Site grouping BEFORE scoring (H-LANE; provenance drives the +10) ---- #
    groups = cross_confirm_group(working)

    lone_cap = _lone_lane_cap(thresholds)
    survivors = []
    for g in groups:
        attribution = list(g["attribution"])
        # scoring.md:18 (D-01): the +10 needs a second opinion — a Codex member
        # (envelope-verified) AND a Claude-lane member at the site. Claude<->Claude
        # agreement at one site is one correlated voter and earns nothing.
        cross_confirmed = _codex_corroborated(g["members"], codex_joined)
        # D-01 second opinion, computed BEFORE scoring: it gates both the
        # B-REWEIGHT offset (per member) and the B-SEV ceiling (per group).
        second_opinion = _second_opinion(g["members"], codex_joined, persisted_ids)
        # Score every member first so the representative (the sort below) is
        # well-defined.
        scored_members = []
        for member in g["members"]:
            decision = _score_member(
                member, changed_line_ranges, reviewed_union, file_line_totals,
                all_mode, cross_confirmed, persisted_ids,
                second_opinion=second_opinion,
            )
            if decision["drop"]:
                filtered.append({
                    "file": member.get("file"),
                    "line": member.get("line"),
                    "title": member.get("title"),
                    "reason": decision["reason"],
                })
            else:
                raw = decision["score"]
                # B-SEV (v2.10 Wave 1, D-02): a group with no second opinion
                # (Codex-corroborated or persisted, D-01) tops out at critical
                # floor - 1. The cap is the SCORE, so band_for stays the single
                # band writer; it is identical for every member because
                # second_opinion is a group property.
                capped = raw
                if lone_cap is not None and not second_opinion:
                    capped = min(raw, lone_cap)
                # Per-member effective band: the idiom cap keyed on THIS member's
                # own category, so it never leaks onto a co-located non-idiom
                # member (T-41-33).
                eff = _effective_band(member, capped, thresholds, idiom_floor)
                scored_members.append((capped, member, decision, eff, raw))
        if not scored_members:
            continue
        # Representative: the strongest EFFECTIVE band leads, then the highest
        # (capped, then uncapped) score, then the member's OWN stable_hash
        # (Fable A4: the old stable sort kept whichever tied member arrived
        # FIRST, so the dismissal key depended on agent-return order), then the
        # agent name — the final tie-break for two lanes reporting one title at
        # one line (equal hash), so the pick never depends on arrival order.
        # For a single-category group without the cap this is the old
        # score-then-hash order. The uncapped key keeps the highest raw score
        # first among members the ceiling equalizes.
        scored_members.sort(key=lambda t: (
            -_BAND_SEVERITY.get(t[3], 0),
            -t[0],
            -t[4],
            stable_hash(t[1].get("file", ""), t[2]["canonical_for_hash"],
                        t[1].get("title", "")),
            t[1].get("agent") if isinstance(t[1].get("agent"), str) else "",
        ))
        # The per-command finalize cutoff below judges the UNCAPPED score: the
        # lone-lane ceiling lowers the band label, it never drops a finding (a
        # config-tuned critical floor may sit below the /review cutoff).
        # The row is LED by the first member (in the order above) whose uncapped
        # score clears the cutoff, so the cutoff and the displayed row agree:
        # the per-member idiom cap can sort a lower-scoring non-idiom member
        # ahead of a higher-scoring idiom member, and letting that sub-threshold
        # member lead would either drop the above-threshold site or surface a
        # row whose own score is below the cutoff. When no member clears it the
        # band-first lead is kept and the row drops as sub-threshold.
        passing = [t for t in scored_members if t[4] >= threshold]
        if passing and passing[0] is not scored_members[0]:
            lead = passing[0]
            scored_members = [lead] + [t for t in scored_members if t is not lead]
        best_score, best_member, best_decision, best_band, best_raw = scored_members[0]
        surface_score = best_raw
        # Members that lost the dedup are absorbed into the survivor; each loser
        # is RECORDED in filtered[] below (Fable A2) once the survivor's
        # stable_hash exists to point at.
        survivor = dict(best_member)
        survivor["orchestrator_score"] = best_score
        # band_for stays the single band WRITER and the idiom cap the ONE
        # post-band adjustment (NOISE-01), both applied per member above by that
        # member's OWN category — so the row's band is the strongest applicable
        # member band, and a security warning absorbed with a higher-scoring
        # idiom finding stays warning under any idiom_floor.
        survivor["band"] = best_band
        survivor["attribution"] = attribution
        survivor["stable_hash"] = stable_hash(
            survivor.get("file", ""),
            best_decision["canonical_for_hash"],
            survivor.get("title", ""),
        )
        if "status" not in survivor:
            survivor["status"] = "new"
        # H-LANE (D-14): every lane's own record rides on the row — the survivor
        # first, then the absorbed members in scored order, de-duplicated by
        # each member's lane-aware occurrence identity (never by (agent, title),
        # never by stable_hash alone, never without the agent).
        members = []
        seen = set()
        for _, m, _, _, _ in scored_members:
            ident = _finding_identity(m)
            if ident in seen:
                continue
            seen.add(ident)
            members.append(_member_ref(m))
        survivor["members"] = members
        # Fable A2 (NEW-ABSORB): members that lost the dedup used to vanish —
        # appended to NEITHER findings NOR filtered[] — so when two DISTINCT
        # defects landed within ±2 lines, the real second bug was
        # unrecoverable, violating the "never silently drop" principle. Each
        # loser is still absorbed (one survivor per group) but is now RECORDED
        # in filtered[] with a reason naming its survivor's stable_hash, so the
        # owner can see what was folded into what.
        for _, loser, _, _, _ in scored_members[1:]:
            filtered.append({
                "file": loser.get("file"),
                "line": loser.get("line"),
                "title": loser.get("title"),
                "reason": "absorbed-into: " + survivor["stable_hash"],
            })
        survivors.append((survivor, surface_score))

    # --- Per-command threshold filter (scoring.md:57-64) --------------------- #
    kept = []
    for survivor, sc in survivors:
        if sc < threshold:
            filtered.append({
                "file": survivor.get("file"),
                "line": survivor.get("line"),
                "title": survivor.get("title"),
                "reason": "sub-threshold",
            })
            continue
        survivor["snapshot"] = _snapshot_for(survivor, pass_number)
        kept.append(survivor)

    # --- Synthetic bare-marker "suppression" audit findings (NOISE-03, A2) ---- #
    # The ONE synthetic finding score.py emits and the ONE exemption from the
    # sub-threshold drop: appended to `kept` HERE, AFTER the threshold loop, so the
    # `sc < threshold` filter never sees it (A2 — guaranteed visible as an
    # informational `low` audit finding, NOT dropped). It carries the FULL survivor
    # shape — band literal "low", a fixed NON-NULL orchestrator_score, a stable_hash
    # from the existing stable_hash(file, canonical, title) helper, an attribution
    # of length <=1, and status "audit" (_SUPPRESSION_STATUS) — precisely so
    # review.md's Phase 3 fail-closed check (halts if any survivor lacks
    # band/orchestrator_score/stable_hash) and Phase 4 render gate (halts if any
    # finding lacks band/orchestrator_score) never trip on it (Finding #1), while
    # the "audit" status keeps it OUT of the multi-pass carry-forward allowlist so
    # it is regenerated fresh each pass, never carried-and-double-counted
    # (impact-01). Its `line` may be null for a file-level marker (NEW-1) — neither
    # gate requires a non-null line, so it still passes both.
    # category "suppression" is emitted here, after grouping, so it never joins a
    # site row, never earns the +10 and is never capped by idiom_floor.
    for file, marker_line in bare_marker_keys:
        file_str = file if isinstance(file, str) else ""
        audit_row = {
            "file": file,
            "line": marker_line,   # may be None (NEW-1) — passes the gates.
            "title": _SUPPRESSION_TITLE,
            "category": _SUPPRESSION_CATEGORY,
            "band": "low",                       # hand-set literal (NOT band_for).
            "orchestrator_score": _SUPPRESSION_SCORE,  # fixed non-null < medium(70).
            "attribution": ["vibe-check"],       # length <=1 => never cross-confirmed.
            "stable_hash": stable_hash(
                file_str, _SUPPRESSION_CANONICAL, _SUPPRESSION_TITLE),
            # impact-01: "audit", NOT "new" — the carry-forward allowlist
            # {new, persisted, needs-recheck} excludes it, so the synthetic finding
            # is regenerated fresh each pass rather than carried forward and
            # double-counted / mis-statused. Gate- and render-inert (see the
            # _SUPPRESSION_STATUS definition).
            "status": _SUPPRESSION_STATUS,
        }
        audit_row["snapshot"] = _snapshot_for(audit_row, pass_number)
        kept.append(audit_row)

    # Fable A11: sanitize non-finite floats at the output boundary so the
    # envelope is ALWAYS strict JSON (see _sanitize_nonfinite).
    return _sanitize_nonfinite({
        "scored_by_script": True,
        "findings": [_shape_finding(f) for f in kept],
        "fixed_since_last": fixed_since_last,
        "filtered": filtered,
    })


def _as_line(x):
    """Normalize a finding's `line` for arithmetic/comparison.

    A real line number is a non-bool int. Anything else — None (a present-but-null
    `line`, which file-level findings legitimately carry), a float, a string — is
    NOT a usable line and returns None, the "no line" sentinel. Callers treat that
    sentinel as out-of-range / non-grouping rather than crashing with a TypeError.
    """
    return x if isinstance(x, int) and not isinstance(x, bool) else None


def _sanitize_nonfinite(obj):
    """Recursively replace non-finite floats (NaN/Infinity/-Infinity) with None.

    Fable A11: json.dump's default allow_nan=True writes bare `NaN`/`Infinity`
    tokens — NOT valid JSON — for any non-finite float an agent smuggled through
    a passthrough field (e.g. intent_doc_match.confidence rides the survivor
    copy untouched; the _coerce_confidence guard only protects the score MATH,
    not the output). A strict downstream parser (jq, any non-Python consumer)
    rejects the whole envelope. run() sanitizes its return value through this,
    and the __main__ shim passes allow_nan=False as the fail-closed backstop.

    Import-free non-finite test (the AST import-set test bans `math`): the
    `-1e308 < x < 1e308` bound is the same idiom as _coerce_confidence — every
    comparison with NaN is False, inf/-inf fall outside the bound, every
    legitimate JSON-borne float passes. Depth is bounded by what json.load
    already parsed, so recursion mirrors the input's own limits.
    """
    if isinstance(obj, float) and not (-1e308 < obj < 1e308):
        return None
    if isinstance(obj, list):
        return [_sanitize_nonfinite(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _sanitize_nonfinite(v) for k, v in obj.items()}
    return obj


def _valid_finding(member):
    """Is `member` a usable finding CONTAINER (D-01, HARDEN-01)? -> (True, None) | (False, reason).

    The CONTAINER analog of `_as_line` — same coerce-or-skip posture, one level up
    (the finding dict itself, not one of its fields). A non-dict member (a bare
    str / None / list / int from a malformed agent envelope) cannot be `.get`-ed
    and would crash run() with `AttributeError: 'X' object has no attribute 'get'`
    (C1) — or, in the carryforward loop, crash `cf.get(...)` BEFORE the working
    set is even assembled (C2). Such a member is skipped and reported to `filtered`
    (D-01: visible, never silently lost), so one bad agent finding can never
    hard-crash the whole review run.

    Scope is CRASH-SAFETY only (HARDEN-01), not validity policy: a dict with a
    missing / null / non-str `file`/`title`/`category` (see _REQUIRED_KEYS) is NOT
    rejected here. score.py is already null-safe for those fields — stable_hash and
    _first_line coerce None -> "" — so such a finding flows through and scores
    rather than crashing. Rejecting it would be out-of-scope policy tightening that
    breaks deliberate, frozen-test-locked behavior (null-title/null-category
    findings survive). Only a non-dict CONTAINER is a real crash, so only it is
    rejected.
    """
    if not isinstance(member, dict):
        return False, "malformed: non-dict finding"
    return True, None


def _safe_window(x):
    """Normalize a finding's `source_window` to a list of STRING lines (D-01, HARDEN-01).

    A field-coercion sibling of `_as_line` (same coerce-or-skip posture). Guards BOTH
    crash surfaces of `silenced_nearby`'s substring scan:
      - CONTAINER (C3): a truthy non-list (e.g. `99`) currently slips through the old
        `... or []` and crashes `for line in source_window` with
        `TypeError: 'int' object is not iterable`. A non-list coerces to [].
      - ELEMENT (HOLE 1): a GENUINE list with non-string elements (e.g. `[1, 2, 3]`)
        passes a container-only guard but then crashes the `marker in line` scan with
        `TypeError: argument of type 'int' is not iterable`. Filtering to string
        elements keeps `silenced_nearby` a pure substring scan over strings.
    A bad/odd window is NOT grounds to drop the finding — it just means "no silenced
    markers found" (silenced=False). KEPT-and-degraded, never a malformed-reject.
    """
    return [s for s in x if isinstance(s, str)] if isinstance(x, list) else []


def _line_in_ranges(line, ranges):
    """Is `line` within any [start, end] inclusive range?

    A non-int line (None / null / other) is treated as out-of-range (returns
    False) rather than raising — a file-level finding with line=null simply is
    not in any diff range.

    Fable F9: the pair ELEMENTS get the same guard as the pair length — a range
    like [["8","14"]] (string line numbers, a plausible orchestrator-side drift
    in the LLM-assembled hunk JSON) previously raised `TypeError: '<=' not
    supported between 'str' and 'int'` and halted the whole run. A non-int
    endpoint (via _as_line) now reads as "not a usable range" (False), and a
    non-sequence pair / non-list ranges container is skipped the same way.
    """
    line = _as_line(line)
    if line is None:
        return False
    if not isinstance(ranges, (list, tuple)):
        return False
    for pair in ranges:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        start, end = _as_line(pair[0]), _as_line(pair[1])
        if start is not None and end is not None and start <= line <= end:
            return True
    return False


def _score_member(member, changed_line_ranges, reviewed_union, file_line_totals,
                  all_mode, cross_confirmed, persisted_ids, second_opinion=True):
    """Recompute the orchestrator-verified booleans for one finding and score it.

    Returns a dict: {"drop": bool, "reason": str|None, "score": int|None,
    "canonical_for_hash": str}. The keep/drop gate differs by mode:
      - diff mode: in_diff drives ONLY the +20 bonus — an out-of-diff finding is
        NOT dropped here (Fable A12: this docstring used to claim a drop with
        reason "out-of-diff" that never existed in the code; without the +20
        most out-of-diff findings fall sub-threshold, but a high-confidence one
        CAN surface — that is current, deliberate-until-redesigned behavior,
        locked by test_in_diff_recomputed_overrides_agent_claim)
      - --all mode: in_reviewed_set membership gates (reason "not-in-reviewed-set")
        — a TRANSIENT keep/drop boolean, NOT serialized onto the finding, and the
        +20 in_diff term never fires in --all (review.md:684).
    `second_opinion` (D-01) gates the B-REWEIGHT offset: True (the default) =>
    no offset (identity); False => the member's lower-only _agent_offset.
    """
    # lang-py-001 (crash guard): coerce `file` to a safe HASHABLE str BEFORE it is
    # used as a dict key / set membership below (`file_line_totals.get(file)`,
    # `file in reviewed_union`, `changed_line_ranges.get(file, [])`). A
    # malformed-but-parseable finding whose `file` is a non-str, potentially
    # UNHASHABLE shape (list/dict) would otherwise raise `TypeError: unhashable
    # type` on those lookups, exit non-zero, and halt the WHOLE run at review.md's
    # Phase 3 fail-closed gate. A non-str `file` is never a real path (so it can
    # never legitimately be a reviewed_union member or a *_totals/ranges key), so
    # coercing it to "" is behavior-preserving for real input while never raising —
    # mirroring _as_line / _safe_window's coerce-at-read posture.
    file = member.get("file", "")
    if not isinstance(file, str):
        file = ""
    line = member.get("line", 0)
    source_window = _safe_window(member.get("source_window"))

    # silenced recomputed from source_window, overriding agent claim (hard rule #4).
    silenced = silenced_nearby(source_window)

    # canonical content used for the stable hash: prefer the orchestrator-resolved
    # canonical_line_content (carryforward path); else fall back to the finding's
    # own first current_code line (diff-mode findings carry no separate canonical).
    canonical_for_hash = _canonical_for_hash(member)

    if all_mode:
        # in_reviewed_set: file in the dispatched union AND 1 <= line <= N.
        # A non-int line (present-but-null on a file-level finding) is treated as
        # out-of-bounds rather than crashing on `1 <= None <= n`.
        n = file_line_totals.get(file)
        line_norm = _as_line(line)
        in_set = file in reviewed_union and (
            n is None or (line_norm is not None and 1 <= line_norm <= n)
        )
        if not in_set:
            return {"drop": True, "reason": "not-in-reviewed-set",
                    "score": None, "canonical_for_hash": canonical_for_hash}
        in_diff = False  # no diff in --all; +20 never fires (correct).
    else:
        in_diff = _line_in_ranges(line, changed_line_ranges.get(file, []))

    # Fable A5: `persisted` comes ONLY from the identity set the carry-forward
    # loop built — the sole legitimate writer of status=="persisted" (it adds
    # id(cf) of the very dict it appends to `working`, so the identity always
    # hits here). The old `or member.get("status") == "persisted"` fallback was
    # redundant for real carryforward members and was the forgery surface for an
    # agent-supplied status on a new finding (+15 from an unverified input).
    persisted = id(member) in persisted_ids
    confidence_offset = 0 if second_opinion else _agent_offset(member)

    score = compute_score(
        member,
        in_diff=in_diff,
        silenced=silenced,
        cross_confirmed=cross_confirmed,
        persisted=persisted,
        confidence_offset=confidence_offset,
    )
    if score is None:
        # pre-clamp < 0 => DROP (D-14). Reason is the dominant drop cause.
        # Fable F8: an intent-doc-driven drop (the -100 strong-match / -30
        # penalty forcing pre-clamp < 0) was mislabeled "sub-threshold" —
        # conflating "the code matches the plan" with "the score was too low"
        # in the user-facing filtered[] report. silenced keeps precedence when
        # both apply (preserves the existing label in the overlap case).
        if silenced:
            reason = "silenced"
        elif _intent_doc_penalty(member) < 0:
            reason = "intent-doc-match"
        else:
            reason = "sub-threshold"
        return {"drop": True, "reason": reason, "score": None,
                "canonical_for_hash": canonical_for_hash}
    return {"drop": False, "reason": None, "score": score,
            "canonical_for_hash": canonical_for_hash}


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY I/O. Fails CLOSED on bad input (finding #1).
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Do NOT wrap json.load in a swallowing try/except: an unparseable stdin must
    # propagate (json.JSONDecodeError) so the process exits NON-ZERO and the
    # orchestrator's fail-closed gate (16-02) can fail the review closed instead
    # of rendering unscored findings.
    envelope = json.load(sys.stdin)
    result = run(envelope)
    # allow_nan=False (Fable A11): the fail-closed backstop behind run()'s
    # _sanitize_nonfinite — if a non-finite float ever reaches serialization
    # anyway, raise (non-zero exit -> orchestrator halts) rather than emit the
    # bare `NaN` token, which is not valid JSON.
    json.dump(result, sys.stdout, allow_nan=False)
