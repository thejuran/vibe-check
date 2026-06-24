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

# scoring.md:57-64 — per-command threshold (one parameter selected by `command`).
THRESHOLDS = {"review": 80, "deep-review": 70}


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


def band_for(score):
    """Score -> band (scoring.md:37-42). <70 is below both thresholds => None."""
    if score >= 95:
        return "critical"
    if score >= 80:
        return "warning"
    if score >= 70:
        return "medium"
    return None


def silenced_nearby(source_window):
    """Any of the 5 canonical markers in any line of the ±2 window (D-13 inclusive).

    The orchestrator supplies source_window = [L-2, L-1, L, L+1, L+2] pre-resolved
    (D-05); this is a pure substring scan.
    """
    if not source_window:
        return False
    return any(
        marker in line
        for line in source_window
        for marker in SILENCED_MARKERS
    )


def _first_line(text):
    """First line of a (possibly multi-line) snippet, or '' for falsy input."""
    if not text:
        return ""
    return text.split("\n", 1)[0]


def carry_forward_status(finding, canonical_line_content):
    """Status of a carried-forward finding (review.md:672-678).

    The orchestrator reads HEAD and passes canonical_line_content in (D-05):
      - null/sentinel canonical (file:line gone) => "fixed-since-last"
      - first line of current_code == canonical, BOTH sides stripped (D-11) =>
        "persisted"
      - content changed => "needs-recheck"

    D-11: strip leading AND trailing whitespace on both sides before comparing, so
    pure whitespace drift is not a false "fixed-since-last" / "needs-recheck".
    """
    if canonical_line_content is None:
        return "fixed-since-last"
    current_first = _first_line(finding.get("current_code", "")).strip()
    if current_first == canonical_line_content.strip():
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
    # 1. Start from agent_confidence (defensive coercion: garbage => 0).
    # Accept int OR float (JSON from LLM agents routinely carries floats like
    # 85.0), but reject bool (True is an int subclass) — mirrors the numeric
    # guard in _intent_doc_penalty. A float is truncated via int().
    raw_conf = finding.get("agent_confidence", 0)
    s = (int(raw_conf)
         if isinstance(raw_conf, (int, float)) and not isinstance(raw_conf, bool)
         else 0)

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
    """Case-insensitive substring title match (D-15): the shorter title is a
    substring of the longer. This is the CURRENT un-hardened rule — do NOT
    implement Jaccard/category-overlap here (that is Phase 17 / ROBUST-02).
    """
    a = (title_a or "").lower()
    b = (title_b or "").lower()
    if len(a) <= len(b):
        return a in b
    return b in a


def cross_confirm_group(findings):
    """Group cross-confirmed findings (review.md:689, D-13/D-15).

    Two findings group iff: same file AND |line_a - line_b| <= 2 AND a
    case-insensitive substring title match. Returns a list of group dicts:
      {"members": [findings...], "attribution": [unique agent names in seen order]}

    The +10 cross-confirmation bonus is NOT applied here; it is applied ONCE during
    scoring, gated on len(attribution) >= 2 (review.md:689). This function only
    establishes the grouping + attribution so the scorer knows which findings are
    cross-confirmed.
    """
    groups = []
    for f in findings:
        placed = False
        for g in groups:
            for member in g["members"]:
                same_file = member.get("file") == f.get("file")
                # Defensive: a present-but-null line (file-level finding) is not a
                # usable coordinate. If EITHER line is non-int, the ±2 distance
                # check is False (no grouping on line) rather than crashing on
                # abs(None - 0).
                line_a = _as_line(member.get("line"))
                line_b = _as_line(f.get("line"))
                line_close = (line_a is not None and line_b is not None
                              and abs(line_a - line_b) <= 2)
                if same_file and line_close and _titles_match(
                    member.get("title"), f.get("title")
                ):
                    g["members"].append(f)
                    agent = f.get("agent")
                    if agent is not None and agent not in g["attribution"]:
                        g["attribution"].append(agent)
                    placed = True
                    break
            if placed:
                break
        if not placed:
            agent = f.get("agent")
            groups.append({
                "members": [f],
                "attribution": [agent] if agent is not None else [],
            })
    return groups


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
    carryforward = envelope.get("carryforward", []) or []
    findings = list(envelope.get("findings", []) or [])

    threshold = THRESHOLDS.get(command, THRESHOLDS["review"])

    fixed_since_last = []
    filtered = []

    # --- Carry-forward (review.md:672-678) ----------------------------------- #
    # Each carryforward finding carries a pre-resolved canonical_line_content
    # (the orchestrator read HEAD). null => fixed-since-last (excluded).
    persisted_ids = set()
    working = []
    for cf in carryforward:
        status = carry_forward_status(cf, cf.get("canonical_line_content"))
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
        survivor["band"] = band_for(best_score)
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
    file = member.get("file", "")
    line = member.get("line", 0)
    source_window = member.get("source_window", []) or []

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
