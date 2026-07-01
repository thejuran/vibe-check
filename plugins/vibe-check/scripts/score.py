"""score.py — the deterministic-core scoring filter for the vibe-check plugin.

Phase 16 (CORE-01). This is a BEHAVIOR-PRESERVING extraction of the orchestrator's
by-hand scoring prose (templates/scoring.md + commands/review.md Phase 3/4.5). It
reproduces that prose byte-for-byte in observable behavior. No weight, bonus, band
cutoff, or threshold is re-tuned here; the cross-confirm matcher and carry-forward
compare are the CURRENT (un-hardened) logic. Phase 17 hardens; this only freezes.

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
# Do NOT retune (behavior-preserving extraction).
# --------------------------------------------------------------------------- #

# scoring.md:21-26 — severity weight, applied LAST before clamp. Unset/other => -8.
SEVERITY_WEIGHT = {"critical": 0, "high": -3, "medium": -8, "low": -20}
SEVERITY_FALLBACK = -8  # scoring.md:26 (unset / unrecognized => medium-equivalent)

# review.md:685 — the canonical 5 silenced markers (NOT false-positive-rules.md's
# slightly-different list). Fixed-string substring match over a ±2-line window.
SILENCED_MARKERS = ("eslint-disable", "# noqa", "// nolint", "@SuppressWarnings",
                    "#[allow(")

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
_SUPPRESSION_CATEGORY = "suppression"   # maps to NO domain (never cross-confirms).
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

# HARDEN-01 — DOCUMENTATION ONLY (not a reject gate). The three fields a
# well-formed finding normally carries. Per orchestrator correction (this phase),
# a missing / null / non-str value for any of these does NOT make a finding
# malformed: score.py is already null-safe for them (stable_hash and _first_line
# coerce None -> ""), so such a finding flows through and scores. Only a NON-DICT
# container is a crash and gets rejected by `_valid_finding`. This tuple is kept
# as a reference for the expected shape; it intentionally gates nothing.
_REQUIRED_KEYS = ("file", "title", "category")


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
    return hashlib.sha256(
        (file + "\x00" + canonical_line_content + "\x00" + title).encode()
    ).hexdigest()


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


def _is_fresh_marker_start(line, pos):
    """Is the `_VIBE_IGNORE` token at `pos` a GENUINE fresh marker start (bugs-001)?

    A genuine marker begins a comment, so its token is preceded — after stripping
    intervening whitespace — by a comment lead-in (`//` or `#`) or by nothing at
    all (the token starts the line). A `vibe-ignore` occurrence preceded by an
    ordinary word character is REASON TEXT of an earlier marker (e.g. the second
    "vibe-ignore" in `// vibe-ignore: see other vibe-ignore usage above`), NOT a
    separate marker — treating it as one wrongly split a genuinely REASONED marker
    into a false BARE occurrence and emitted a bogus "suppression without reason"
    synthetic finding (bugs-001). Distinguishing on the comment lead-in preserves
    the existing same-line contracts (`// vibe-ignore: r // vibe-ignore` still
    detects the trailing bare marker; `// vibe-ignore // vibe-ignore: r` still
    detects both) because a genuine second marker always opens a fresh `//`/`#`
    comment, while in-reason prose does not.
    """
    prefix = line[:pos].rstrip()
    return prefix == "" or prefix.endswith("//") or prefix.endswith("#")


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
    if any(marker in line
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


def compute_score(finding, *, in_diff, silenced, cross_confirmed, persisted):
    """Apply the score formula (scoring.md:11-29) in the LOCKED operation order.

    Returns the clamped [0,100] orchestrator_score, OR None as the DROP signal when
    the pre-clamp score < 0 (D-14 — the caller removes the finding and records it in
    filtered[]; it is NOT clamped-to-0-and-emitted).

    in_diff / silenced / cross_confirmed / persisted are the orchestrator-verified
    booleans the caller computes (recomputed from raw facts, overriding agent
    self-reports per agent-output-schema hard rule #4); compute_score does not
    re-derive them.
    """
    # 1. Start from agent_confidence (defensive coercion: garbage => 0). The
    # coercion (int/float accepted, float truncated, bool/non-finite/garbage => 0)
    # lives in _coerce_confidence so it is the SINGLE source of truth shared with
    # the min_confidence pre-scoring filter (they can never drift).
    s = _coerce_confidence(finding.get("agent_confidence", 0))

    # 2. Additive/subtractive bonuses (intent-doc penalty is mutually exclusive).
    if in_diff:
        s += 20                                   # scoring.md:13
    if silenced:
        s -= 50                                   # scoring.md:14
    if finding.get("agent") == "compliance":
        s += 20                                   # scoring.md:15
    s += _intent_doc_penalty(finding)             # scoring.md:16-17 (elif, D-12)
    if cross_confirmed:
        s += 10                                   # scoring.md:18 (once; len(attr)>=2)
    if persisted:
        s += 15                                   # scoring.md:19

    # 3. Severity weight LAST, before clamp (scoring.md:21-26). Unset/other => -8.
    severity = finding.get("severity")
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
    that). `cross_confirm_group` keys on category-DOMAIN overlap instead. This
    function is intentionally UNREFERENCED; do not re-wire it into the matcher.
    """
    a = (title_a or "").lower()
    b = (title_b or "").lower()
    if len(a) <= len(b):
        return a in b
    return b in a


# scoring-domain map (ROBUST-02 / D-01): a finding's `category` collapses to a
# coarse DOMAIN; two NON-adversarial findings cross-confirm iff BOTH map to a
# KNOWN domain AND those domains are EQUAL. `adversarial` is deliberately NOT in
# this map (no wildcard domain) — Codex's category is resolved by the separate,
# ambiguity-safe single-domain bridge in cross_confirm_group STEP B, never here.
# Framework rows fold into the nearest native domain (documented inline).
CATEGORY_DOMAIN = {
    # --- security ---
    "security": "security", "injection": "security", "auth": "security",
    "data-exposure": "security", "auth-security": "security",
    "path-traversal": "security", "ssrf": "security",
    "deserialization": "security", "mass-assignment": "security",
    "xss": "security", "secrets": "security",
    # --- correctness ---
    "null-access": "correctness", "off-by-one": "correctness",
    "race-condition": "correctness", "resource-leak": "correctness",
    "error-handling": "correctness", "infinite-loop": "correctness",
    "state-mutation": "correctness", "concurrency": "correctness",
    "unsafe-usage": "correctness",
    # --- design ---
    "pattern-consistency": "design", "abstraction": "design",
    "duplication": "design", "dependency": "design",
    "separation-of-concerns": "design",
    # --- impact ---
    "breaking-api": "impact", "schema-change": "impact",
    "perf-at-scale": "impact", "blast-radius": "impact", "perf": "impact",
    # --- style ---
    "type-hints": "style", "mutable-default": "style", "bare-except": "style",
    "is-vs-eq": "style", "context-manager": "style", "type-safety": "style",
    "async-discipline": "style", "react-hook": "style", "equality": "style",
    "dep-array": "style", "idiom": "style",
    # framework-react: ONLY "hooks" maps to a native domain — it is the exact
    # TWIN of language-typescript's "react-hook" (already "style" above), so the
    # headline cross-confirm fires: a React hook bug caught by BOTH
    # framework-react (category "hooks") AND language-typescript (category
    # "react-hook") now overlaps at (file, line ±2) and earns the +10 (both
    # resolve to "style"). framework-react's OTHER categories — "rendering",
    # "controlled-uncontrolled", "a11y" — are deliberately NOT mapped (they
    # resolve to None and cross-confirm with NOTHING today; each stands on its
    # own score), MIRRORING the framework-fastapi non-twin policy below: only a
    # genuine cross-agent TWIN is mapped, so we never fold a distinct React
    # finding into the broad "style" bucket where it could spuriously confirm
    # with — and silently absorb — an unrelated co-located TS style finding
    # (e.g. an "a11y" defect vs a "type-safety" cast 2 lines away). Broadening
    # to cover them is a deferred follow-up, not current behavior.
    # (framework-react's "perf" is already mapped to "impact" above, alongside
    # language-typescript's "perf" — unchanged; "perf" IS a cross-agent twin.)
    "hooks": "style",
    # framework-electron (v2.7, D-06): the FIRST real framework-into-"security"
    # twin since react's hooks->style. ONLY "ipc-validation" is mapped — it
    # resolves to "security" because an Electron IPC handler that flows a
    # renderer-supplied arg into a sink (fs / shell.openExternal / a SQL query /
    # child_process) co-locates with security's own "injection" / "path-traversal"
    # findings (both already map to "security" above): it is genuinely the same
    # defect seen by two reviewers, so when framework-electron flags
    # "ipc-validation" AND security flags injection/path-traversal at the same
    # (file, line ±2) they correctly cross-confirm and earn the +10. Because
    # _categories_overlap compares only the COARSE domain, this twin inherits the
    # FULL "security"-domain reach: it cross-confirms with — AND, per
    # cross_confirm_group, can absorb when co-located within ±2 lines — ANY
    # "security"-domain finding (injection, path-traversal, auth, data-exposure,
    # xss, secrets, ssrf, etc.), NOT only injection/path-traversal. This is the
    # SAME broad same-domain behavior every existing security category already
    # has (injection already overlaps auth/secrets/xss — see
    # test_same_domain_co_located_confirms) and it is INTENDED: an IPC->sink flow
    # IS a security defect, so it must behave like one. framework-electron's OTHER
    # FIVE categories — "webpreferences-hardening", "preload-exposure",
    # "navigation-safety", "content-loading", "process-hardening" — are
    # deliberately NOT mapped (they resolve to None and cross-confirm with NOTHING
    # today; each stands on its own score), MIRRORING the framework-react /
    # framework-fastapi non-twin policy: only a genuine cross-agent TWIN is mapped,
    # so a distinct electron misconfiguration is never folded into the broad
    # "security" bucket where it could spuriously confirm with — and silently
    # absorb — an unrelated co-located security finding (e.g. a
    # "webpreferences-hardening" flag-omission note 2 lines from a real injection
    # defect). Broadening to cover them is a deferred follow-up, not current
    # behavior.
    "ipc-validation": "security",
    # framework-react-native (v2.7, D-06): the SECOND real framework twin (after
    # electron's ipc-validation->security) and the earned `perf` twin. ONLY
    # "list-perf" is mapped — it resolves to "impact" because an RN unbounded-list
    # render (a large/fetched collection in a ScrollView instead of a virtualized
    # FlatList/FlashList) is a performance defect that co-locates with "impact"'s
    # own "perf" / "perf-at-scale" / "blast-radius" findings AND framework-react's
    # "perf" (all already map to "impact" above): it is genuinely the same perf
    # defect seen by two reviewers, so when framework-react-native flags "list-perf"
    # AND framework-react/impact flags a perf-domain finding at the same
    # (file, line ±2) they correctly cross-confirm and earn the +10. Because
    # _categories_overlap compares only the COARSE domain, this twin inherits the
    # FULL "impact"-domain reach: it cross-confirms with — AND, per
    # cross_confirm_group, can absorb when co-located within ±2 lines — ANY
    # "impact"-domain finding (perf, perf-at-scale, blast-radius, breaking-api,
    # schema-change), NOT only perf. This is the SAME broad same-domain behavior
    # every existing impact category already has and it is INTENDED: an unbounded
    # list IS a perf defect, so it must behave like one. framework-react-native's
    # OTHER FIVE categories — "platform", "native-cleanup", "reanimated",
    # "expo-config", "native-component" — are deliberately NOT mapped (they resolve
    # to None and cross-confirm with NOTHING today; each stands on its own score),
    # MIRRORING the framework-react / framework-fastapi non-twin policy. In
    # particular "expo-config"'s AsyncStorage-for-secrets finding is DELIBERATELY
    # NOT twinned to "security" this milestone (ROADMAP #4 / D-06) — mapping it
    # would let an RN-mechanism finding spuriously confirm (and silently absorb) an
    # unrelated co-located security finding. Broadening to cover any of the five is
    # a deferred follow-up, not current behavior.
    "list-perf": "impact",
    # --- compliance ---
    "rule-violation": "compliance",
    # framework-fastapi: ONLY its data-exposure/auth-security twins map to
    # "security" (the two rows already listed above), so ONLY those two can
    # cross-confirm with a co-located security finding. Its OTHER declared
    # categories — async-blocking, dependency-injection, pydantic-validation,
    # response-status, lifecycle-background, routing, openapi-honesty,
    # file-upload-safety, settings-app-construction — are deliberately NOT in
    # this map, so they resolve to None (no domain) and cross-confirm with
    # NOTHING today; each stands on its own score. They are NOT folded into a
    # native domain here. (Broadening the map to cover them is a deferred
    # follow-up, not current behavior — keep this comment honest to the map.)
}


def _category_domain(category):
    """Map a finding's `category` to its coarse domain, or None.

    Defensive (D-02 / Pattern 1): a missing / null / non-str / unknown category
    maps to None (NO domain) rather than raising — a single malformed finding
    must not crash run() and trip the orchestrator's fail-closed halt.
    """
    if not isinstance(category, str):
        return None
    return CATEGORY_DOMAIN.get(category)


def _categories_overlap(cat_a, cat_b):
    """True iff BOTH categories map to a KNOWN domain AND the domains are EQUAL.

    NON-overlap (returns False, never raises) whenever EITHER side is
    missing / null / non-str / unknown (D-02 — never a wildcard, never a crash).
    `adversarial` is not in CATEGORY_DOMAIN, so it never overlaps here; it is
    bridged separately in cross_confirm_group STEP B.
    """
    da = _category_domain(cat_a)
    db = _category_domain(cat_b)
    return da is not None and da == db


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


def _is_adversarial(finding):
    """A finding whose category is the literal Codex domain `"adversarial"`."""
    return finding.get("category") == "adversarial"


def cross_confirm_group(findings):
    """Group cross-confirmed findings — ORDER-INDEPENDENT (ROBUST-02, D-01/D-02).

    Replaces the gameable title-substring matcher with category-DOMAIN overlap +
    line proximity, computed as an order-independent relation rather than the old
    greedy "join the first matching group" loop (which made the +10 / absorption
    outcome depend on input order — round-2 BLOCKER 2).

    Return shape is unchanged so run() is untouched: a list of group dicts
      {"members": [findings...], "attribution": [unique agent names]}
    The +10 bonus is applied ONCE during scoring, gated on len(attribution) >= 2;
    this function only establishes grouping + attribution. run() keeps the
    highest-scored member of each group and absorbs the rest, so a group is BOTH
    the absorption/dedup set AND the cross-confirm attribution set.

    STEP A — native same-domain absorption components (order-independent):
      Partition the NON-adversarial findings into connected components under the
      SYMMETRIC relation `same_file AND |line| <= 2 AND _categories_overlap`.
      Membership is computed by union-find (all-pairs), so it does NOT depend on
      iteration order. Each component is one absorption group.

    STEP B — adversarial single-domain bridge (non-grouping, ambiguity-safe):
      For each `adversarial` finding F, look at the FULL set of co-located native
      findings (same file, |line| <= 2) and the set of DISTINCT native DOMAINS
      among them.
        * EXACTLY ONE distinct native domain co-located  -> F joins THAT domain's
          component (adds `codex-adversarial` to its attribution => +10, and
          F is absorbed into the same defect). Because this is computed from the
          full co-located set, security<->adversarial confirms in EVERY ordering.
        * ZERO co-located natives, OR 2+ DISTINCT native domains (ambiguous)
          -> F does NOT bridge: it stands as its OWN group (no +10). Dropping the
          +10 on an ambiguous multi-domain site is deliberate — never guess which
          native it confirms, never +10 / delete an unrelated co-located native.
      Multiple adversarial findings at the same site group together by the same
      proximity rule (their own component); a native joining lifts attribution
      to >= 2.

    Pattern 1 (never raise): non-int line => not co-located; missing/non-str/
    unknown category => NON-overlap; a malformed-line adversarial finds no
    co-located natives and simply stands alone.
    """
    natives = [f for f in findings if not _is_adversarial(f)]
    adversarials = [f for f in findings if _is_adversarial(f)]

    # --- STEP A: union-find over the native findings (order-independent) ----- #
    # parent[] indexes into `natives`. Classic union-find with path compression;
    # implemented by hand (no itertools/extra imports — frozen import set).
    parent = list(range(len(natives)))

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

    for i in range(len(natives)):
        for j in range(i + 1, len(natives)):
            if _line_close(natives[i], natives[j]) and _categories_overlap(
                natives[i].get("category"), natives[j].get("category")
            ):
                union(i, j)

    # Materialize native components, preserving input order within each so the
    # "first member" / attribution ordering is deterministic.
    comp_index = {}          # root -> position in `components`
    components = []          # list of {"members", "attribution", "domain"}
    for i in range(len(natives)):
        root = find(i)
        if root not in comp_index:
            comp_index[root] = len(components)
            components.append({"members": [], "attribution": [], "domain": None})
        comp = components[comp_index[root]]
        f = natives[i]
        comp["members"].append(f)
        agent = f.get("agent")
        if agent is not None and agent not in comp["attribution"]:
            comp["attribution"].append(agent)
        # A component is single-domain by construction (overlap requires equal
        # known domains); record it for the STEP B bridge lookup.
        if comp["domain"] is None:
            comp["domain"] = _category_domain(f.get("category"))

    # --- STEP B: resolve each adversarial finding against the native set ------ #
    # ORDER-INDEPENDENCE (round-2 W1): two holes are closed here.
    #
    # (a) MULTI-ADVERSARIAL RELAY: proximity for bridging is measured ONLY
    #     against NATIVE-origin members, never against an already-bridged
    #     adversarial. We snapshot each component's native members BEFORE the
    #     adversarial bridge loop and test adv proximity against that snapshot —
    #     so a 2nd adversarial cannot transitively relay into a native via a 1st
    #     adversarial that bridged earlier (native@10, adv1@11 bridges, adv2@13
    #     must NOT relay via adv1 since |13-10|=3>2), in any input ordering.
    # (b) SINGLE-DOMAIN-TWO-COMPONENTS: when one native domain spans two
    #     disconnected co-located components (security@10 + security@14, with the
    #     adv@12 between them), WHICH component the +10 lands on would otherwise
    #     depend on iteration/input order. Consistent with D-01/D-02's
    #     ambiguity-safe posture (the multi-DOMAIN case already drops the +10), a
    #     single domain spread across 2+ disconnected co-located components is
    #     ALSO ambiguous — the adv cannot confirm a single defect — so we DROP
    #     the bridge. The bridge fires ONLY when EXACTLY ONE native component is
    #     co-located, which is order-independent by construction.
    native_members = [list(comp["members"]) for comp in components]
    standalone_adversarials = []
    for adv in adversarials:
        # Component indices co-located with this adversarial, by NATIVE members
        # only (the (a) snapshot). A domain may map to MULTIPLE component indices
        # when it is split across disconnected sites — track them all so the
        # (b) ambiguity is visible.
        co_components = []   # list of co-located component indices
        co_domains = set()   # distinct native domains among those components
        for idx, comp in enumerate(components):
            if comp["domain"] is None:
                continue
            if any(_line_close(adv, m) for m in native_members[idx]):
                co_components.append(idx)
                co_domains.add(comp["domain"])
        if len(co_domains) == 1 and len(co_components) == 1:
            # EXACTLY ONE distinct native domain AND exactly one co-located
            # native component => unambiguous bridge into it.
            target = co_components[0]
            comp = components[target]
            comp["members"].append(adv)
            agent = adv.get("agent")
            if agent is not None and agent not in comp["attribution"]:
                comp["attribution"].append(agent)
        else:
            # ZERO co-located natives, 2+ distinct native domains, OR one domain
            # split across 2+ disconnected components (all ambiguous) => no
            # bridge.
            standalone_adversarials.append(adv)

    # Group the non-bridging adversarials among themselves by proximity so two
    # Codex findings at the same site dedup into one group (attribution stays 1
    # unless a native joined — which, by construction here, it did not).
    adv_parent = list(range(len(standalone_adversarials)))

    def adv_find(i):
        root = i
        while adv_parent[root] != root:
            root = adv_parent[root]
        while adv_parent[i] != root:
            adv_parent[i], i = root, adv_parent[i]
        return root

    for i in range(len(standalone_adversarials)):
        for j in range(i + 1, len(standalone_adversarials)):
            if _line_close(standalone_adversarials[i],
                           standalone_adversarials[j]):
                ri, rj = adv_find(i), adv_find(j)
                if ri != rj:
                    adv_parent[ri] = rj

    adv_comp_index = {}
    for i in range(len(standalone_adversarials)):
        root = adv_find(i)
        if root not in adv_comp_index:
            adv_comp_index[root] = len(components)
            components.append({"members": [], "attribution": [], "domain": None})
        comp = components[adv_comp_index[root]]
        f = standalone_adversarials[i]
        comp["members"].append(f)
        agent = f.get("agent")
        if agent is not None and agent not in comp["attribution"]:
            comp["attribution"].append(agent)

    # Return the canonical {"members","attribution"} shape (drop the internal
    # "domain" bookkeeping key) so run() is unchanged.
    return [{"members": c["members"], "attribution": c["attribution"]}
            for c in components]


# --------------------------------------------------------------------------- #
# Orchestrating function over the pure helpers
# --------------------------------------------------------------------------- #
def run(envelope):
    """Process one review pass: findings + context in, scored survivors out.

    Steps (mirroring review.md Phase 3):
      - merge carryforward findings into the working set, computing their status
        (fixed-since-last excluded; persisted flagged for +15; needs-recheck kept)
      - group / dedup to establish attribution BEFORE final scoring (cross-confirm
        +10 needs attribution length)
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

    # --- Carry-forward (review.md:672-678) ----------------------------------- #
    # Each carryforward finding carries a pre-resolved canonical_line_content
    # (the orchestrator read HEAD). null => fixed-since-last (excluded).
    persisted_ids = set()
    working = []
    for cf in carryforward:
        status = carry_forward_status(
            cf, cf.get("canonical_line_content"), cf.get("canonical_window")
        )
        if status == "fixed-since-last":
            fixed_since_last.append({
                "file": cf.get("file"),
                "line": cf.get("line"),
                "title": cf.get("title"),
                "band": cf.get("band"),
                "first_pass_N": cf.get("first_pass_N"),
            })
            continue
        # persisted / needs-recheck both flow through scoring (review.md:678).
        cf = dict(cf)
        cf["status"] = status
        if status == "persisted":
            persisted_ids.add(id(cf))
        working.append(cf)
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

    # --- Cross-confirm grouping BEFORE scoring (attribution drives +10) ------- #
    groups = cross_confirm_group(working)

    survivors = []
    for g in groups:
        attribution = list(g["attribution"])
        cross_confirmed = len(attribution) >= 2
        # Keep the highest-scored member as the surviving representative; score
        # every member first so "highest-scored" is well-defined.
        scored_members = []
        for member in g["members"]:
            decision = _score_member(
                member, changed_line_ranges, reviewed_union, file_line_totals,
                all_mode, cross_confirmed, persisted_ids,
            )
            if decision["drop"]:
                filtered.append({
                    "file": member.get("file"),
                    "line": member.get("line"),
                    "title": member.get("title"),
                    "reason": decision["reason"],
                })
            else:
                scored_members.append((decision["score"], member, decision))
        if not scored_members:
            continue
        # Highest score wins (stable: keep first on ties via max over score only).
        scored_members.sort(key=lambda t: t[0], reverse=True)
        best_score, best_member, best_decision = scored_members[0]
        # Members that lost the dedup are absorbed into the survivor (not emitted).
        survivor = dict(best_member)
        survivor["orchestrator_score"] = best_score
        survivor["band"] = band_for(best_score, thresholds)
        # v2.8 idiom_floor cap (NOISE-01, D-01/D-02): the ONE post-band adjustment.
        # band_for above stays the single band WRITER; this LOWERS the label of an
        # `idiom`-category survivor to idiom_floor (default "medium", A1), scoped to
        # category=="idiom" and never touching `category` or `orchestrator_score`
        # (so GOLDEN_DIGEST / stable_hash / non-idiom bands stay byte-stable). Do
        # NOT add a second band-computation branch elsewhere.
        survivor["band"] = _cap_idiom_band(
            survivor.get("category"), survivor["band"], idiom_floor)
        survivor["attribution"] = attribution
        survivor["stable_hash"] = stable_hash(
            survivor.get("file", ""),
            best_decision["canonical_for_hash"],
            survivor.get("title", ""),
        )
        if "status" not in survivor:
            survivor["status"] = "new"
        survivors.append((survivor, best_score))

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
    # category "suppression" is NOT in CATEGORY_DOMAIN, so it maps to no domain and
    # never cross-confirms (+10) nor is capped by idiom_floor.
    for file, marker_line in bare_marker_keys:
        file_str = file if isinstance(file, str) else ""
        kept.append({
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
        })

    return {
        "scored_by_script": True,
        "findings": kept,
        "fixed_since_last": fixed_since_last,
        "filtered": filtered,
    }


def _as_line(x):
    """Normalize a finding's `line` for arithmetic/comparison.

    A real line number is a non-bool int. Anything else — None (a present-but-null
    `line`, which file-level findings legitimately carry), a float, a string — is
    NOT a usable line and returns None, the "no line" sentinel. Callers treat that
    sentinel as out-of-range / non-grouping rather than crashing with a TypeError.
    """
    return x if isinstance(x, int) and not isinstance(x, bool) else None


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
    """
    line = _as_line(line)
    if line is None:
        return False
    for pair in ranges or []:
        if len(pair) >= 2 and pair[0] <= line <= pair[1]:
            return True
    return False


def _score_member(member, changed_line_ranges, reviewed_union, file_line_totals,
                  all_mode, cross_confirmed, persisted_ids):
    """Recompute the orchestrator-verified booleans for one finding and score it.

    Returns a dict: {"drop": bool, "reason": str|None, "score": int|None,
    "canonical_for_hash": str}. The keep/drop gate differs by mode:
      - diff mode: out-of-diff findings are dropped (reason "out-of-diff")
      - --all mode: in_reviewed_set membership gates (reason "not-in-reviewed-set")
        — a TRANSIENT keep/drop boolean, NOT serialized onto the finding, and the
        +20 in_diff term never fires in --all (review.md:684).
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
    canonical = member.get("canonical_line_content")
    if canonical is None:
        canonical = _first_line(member.get("current_code", ""))
    canonical_for_hash = canonical if canonical is not None else ""

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

    persisted = id(member) in persisted_ids or member.get("status") == "persisted"

    score = compute_score(
        member,
        in_diff=in_diff,
        silenced=silenced,
        cross_confirmed=cross_confirmed,
        persisted=persisted,
    )
    if score is None:
        # pre-clamp < 0 => DROP (D-14). Reason is the dominant drop cause.
        reason = "silenced" if silenced else "sub-threshold"
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
    json.dump(result, sys.stdout)
