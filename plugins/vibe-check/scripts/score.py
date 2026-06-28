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
    # NON-FINITE guard (HOLE 2): json.load accepts bare NaN/Infinity/-Infinity as
    # floats; they pass the isinstance(int,float) check, then int(float('nan'))
    # raises ValueError and int(float('inf')) raises OverflowError. The import-free
    # bound `-1e308 < raw_conf < 1e308` rejects all three (every comparison with NaN
    # is False; inf < 1e308 is False; -1e308 < -inf is False) while any legitimate
    # 0-100 confidence (incl. floats like 85.0) passes — so a non-finite confidence
    # coerces to 0 like other garbage instead of crashing. (`import math` is FORBIDDEN
    # here: the AST import-ban test pins the import set to {json,hashlib,re,sys}.)
    raw_conf = finding.get("agent_confidence", 0)
    s = (int(raw_conf)
         if isinstance(raw_conf, (int, float)) and not isinstance(raw_conf, bool)
         and -1e308 < raw_conf < 1e308
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
    file = member.get("file", "")
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
