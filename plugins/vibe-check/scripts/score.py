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
    """First line of a (possibly multi-line) snippet, or '' for falsy input.

    Non-string input (a JSON number/object from a malformed-but-parseable
    finding's ``current_code``) coerces to '' rather than raising — a single
    odd finding must not crash run() and trip the orchestrator fail-closed halt
    (completes the W1 null/non-str hardening for the sibling text field).
    """
    if not text or not isinstance(text, str):
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
    # --- compliance ---
    "rule-violation": "compliance",
    # framework-fastapi rows fold into the nearest native domain: its
    # data-exposure/auth-security twins map to "security" (already covered
    # above); its remaining framework-mechanism cues are design/correctness in
    # spirit and carry their native category when emitted, so no extra rows are
    # needed here.
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
    # standalone_adversarials collects those that don't bridge; they are then
    # grouped among themselves by proximity (adversarial<->adversarial).
    standalone_adversarials = []
    for adv in adversarials:
        # Distinct native DOMAINS co-located with this adversarial finding.
        co_domains = {}      # domain -> component index (first seen)
        for idx, comp in enumerate(components):
            if comp["domain"] is None:
                continue
            if any(_line_close(adv, m) for m in comp["members"]):
                co_domains.setdefault(comp["domain"], idx)
        if len(co_domains) == 1:
            # EXACTLY ONE distinct native domain co-located => bridge into it.
            target = next(iter(co_domains.values()))
            comp = components[target]
            comp["members"].append(adv)
            agent = adv.get("agent")
            if agent is not None and agent not in comp["attribution"]:
                comp["attribution"].append(agent)
        else:
            # ZERO or 2+ distinct native domains (ambiguous) => no bridge.
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
