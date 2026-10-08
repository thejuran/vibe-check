"""holdout_validate.py — the `validate` command of the holdout kit.

The owner runs `bin/holdout validate` after the finder session, and `seal`
runs the same checks (never with --skip-proofs) before it seals anything. The
checks turn the validity rules in kit/VALIDITY-RULES.md into mechanical
tests over the files in sealed/:

  * slots          — exactly six case folders, one per slot C1..Q3, each with
                     a matching keys folder
  * opaque ids     — every folder name is "H-" plus 8 hex digits
  * file allowlist — only the schema's file names; case.json matches the
                     layout; no links or special files
  * provenance     — required fields, kind, revisions, timestamps; the
                     25-candidate budget and the search-ledger arithmetic;
                     selected_using_reviewer_output is literally false
  * repos          — repo_in_b3 recomputed from kit/b3-exclusions.json; the
                     tuning repo and its mirror never eligible; source_repo
                     listed in kit/eligible-repos.json; C1 and Q2 outside the
                     earlier benchmark and distinct from each other
  * B3 reuse       — sha256 of base_rev, feature_rev and change.diff never in
                     the exclusion hash lists
  * key shape      — per class, with the fixed causal-failure vocabulary
  * proofs         — every runnable proof re-executed on fresh base and
                     changed exports; exits must equal the recorded results
                     and fit the slot pattern

Output is one plain-language "OK: <check>: ..." or "PROBLEM: <check>: ...
Fix: ..." line per finding. Messages name slots, opaque ids, field names and
repo basenames only; no key text, diff line or path is ever printed.

I/O: stdlib only, imports exactly {difflib, os, time} plus holdout_kit. Every
subprocess goes through holdout_kit.run_argv (argv list, timeout, no shell).
"""

import difflib
import os
import time

import holdout_kit

KitError = holdout_kit.KitError

# ---------------------------------------------------------------- schema

CAUSAL_CATEGORIES = ("missing-input-validation", "missing-authz-check",
                     "injection", "path-traversal", "unsafe-deserialization",
                     "resource-exhaustion", "race-condition",
                     "error-handling", "crypto-misuse", "info-disclosure",
                     "logic-error", "other")
OTHER_CATEGORY = "other"

CATCH_KEY_KEYS = ("slot", "class", "defect", "location", "causal_failure",
                  "causal_failure_category")
QUIET_KEY_KEYS = ("slot", "class", "expected_quiet_rationale",
                  "supported_behavior", "exposure_check")
LOCATION_KEYS = ("file", "line_start", "line_end")

PROVENANCE_KEYS = ("slot", "kind", "source_repo", "repo_name", "repo_in_b3",
                   "search", "selected_using_reviewer_output", "found_at")
ORGANIC_KEYS = ("base_rev", "feature_rev")
CONSTRUCTED_KEYS = ("constructed_by",)
KINDS = ("organic", "constructed")
CONSTRUCTED_BY = ("owner", "isolated-agent")
SEARCH_KEYS = ("budget", "order_rule", "screened", "rejections")
REJECTION_KEYS = ("ordinal", "rev", "reason")
BUDGET = 25

PROOF_RESULT_KEYS = ("runnable", "base", "changed", "nonrunnable_reason",
                     "manual_evidence")
PROOF_RUN_KEYS = ("exit", "output_sha256", "ran_at")

CASE_JSON = {"base": "base.tar", "diff": "change.diff",
             "apply_with": "git apply"}
REQUIRED_KEY_FILES = ("key.json", "provenance.json", "proof-results.json")
SIMILARITY_LIMIT = 0.5
HEX = frozenset("0123456789abcdef")

RULES_FIX = "rewrite it as kit/VALIDITY-RULES.md shows"


class Check:
    """One finding. `message` is plain language and carries no case content.

    `warning` marks an OK finding the owner must still act on (it never
    blocks validate, but the seal or the cross-check may)."""

    __slots__ = ("name", "ok", "message", "warning")

    def __init__(self, name, ok, message, warning=False):
        self.name = name
        self.ok = ok
        self.message = message
        self.warning = warning

    def __repr__(self):
        return "Check(%r, %r, %r, warning=%r)" % (self.name, self.ok,
                                                  self.message, self.warning)


def _result(name, problems, ok_message, warnings=()):
    if problems:
        return [Check(name, False, p) for p in problems]
    return [Check(name, True, ok_message)] + [
        Check(name, True, w, warning=True) for w in warnings]


# ---------------------------------------------------------------- loading


def _load_or_none(path):
    try:
        return holdout_kit.load_json(path)
    except KitError:
        return None


def _entries(path):
    try:
        return sorted(os.listdir(path))
    except OSError:
        return None


def _is_id_dir(parent, name):
    if not holdout_kit.ID_RE.match(name):
        return False
    full = os.path.join(parent, name)
    return os.path.isdir(full) and not os.path.islink(full)


class _Case:
    __slots__ = ("cid", "slot", "key", "prov", "results", "key_dir",
                 "case_dir")

    @property
    def label(self):
        return self.slot or self.cid


class _Ctx:
    """Everything the checks read, loaded once. Missing or unreadable files
    load as None; the check that owns that file reports it."""

    def __init__(self, folder):
        self.folder = folder
        sealed = holdout_kit.sealed_dir(folder)
        self.cases_dir = os.path.join(sealed, "cases")
        self.keys_dir = os.path.join(sealed, "keys")
        names = _entries(self.cases_dir)
        if names is None:
            raise KitError("sealed/cases is missing or unreadable")
        self.case_names = names
        self.key_names = _entries(self.keys_dir) or []
        self.case_ids = [n for n in names if _is_id_dir(self.cases_dir, n)]
        self.key_ids = [n for n in self.key_names
                        if _is_id_dir(self.keys_dir, n)]
        cases = []
        for cid in self.case_ids:
            c = _Case()
            c.cid = cid
            c.case_dir = os.path.join(self.cases_dir, cid)
            c.key_dir = os.path.join(self.keys_dir, cid)
            c.key = _load_or_none(os.path.join(c.key_dir, "key.json"))
            c.prov = _load_or_none(os.path.join(c.key_dir, "provenance.json"))
            c.results = _load_or_none(os.path.join(c.key_dir,
                                                   "proof-results.json"))
            slot = c.key.get("slot") if c.key else None
            c.slot = slot if slot in holdout_kit.SLOTS else None
            cases.append(c)
        order = {s: i for i, s in enumerate(holdout_kit.SLOTS)}
        cases.sort(key=lambda c: (order.get(c.slot, 99), c.cid))
        self.cases = cases

    def by_slot(self, slot):
        found = [c for c in self.cases if c.slot == slot]
        return found[0] if len(found) == 1 else None


def _diff_bytes(case):
    try:
        with open(os.path.join(case.case_dir, "change.diff"), "rb") as fh:
            return fh.read()
    except OSError:
        return None


def _b3_lists(folder):
    """(repos, exclude_all_slots) basenames from <folder>/kit/b3-exclusions.json."""
    data = holdout_kit.load_json(
        os.path.join(folder, "kit", holdout_kit.B3_EXCLUSIONS),
        required={"repos": list, "exclude_all_slots": list},
        what="kit/b3-exclusions.json")
    return set(data["repos"]), set(data["exclude_all_slots"])


def _b3_hashes(folder):
    """(commit_sha256 set, patch_sha256 set) from kit/b3-exclusions.json."""
    data = holdout_kit.load_json(
        os.path.join(folder, "kit", holdout_kit.B3_EXCLUSIONS),
        required={"commit_sha256": list, "patch_sha256": list},
        what="kit/b3-exclusions.json")
    return set(data["commit_sha256"]), set(data["patch_sha256"])


def _eligible_repos(folder):
    data = holdout_kit.load_json(
        os.path.join(folder, "kit", holdout_kit.ELIGIBLE_REPOS),
        required={"repos": list}, what="kit/eligible-repos.json")
    return {os.path.normpath(r) for r in data["repos"] if isinstance(r, str)}


def _nonempty_str(v):
    return isinstance(v, str) and bool(v.strip())


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _is_hex(v, n):
    return isinstance(v, str) and len(v) == n and set(v) <= HEX


def _is_iso(v):
    if not isinstance(v, str) or len(v) < 19:
        return False
    try:
        time.strptime(v[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return False
    return True


def _repo_names(prov):
    names = set()
    if isinstance(prov.get("repo_name"), str):
        names.add(prov["repo_name"])
    if isinstance(prov.get("source_repo"), str):
        names.add(os.path.basename(os.path.normpath(prov["source_repo"])))
    return names


def slot_of(folder, case_id):
    """The slot recorded in sealed/keys/<case_id>/key.json; KitError when the
    key is unreadable or names no slot C1..Q3."""
    if not holdout_kit.ID_RE.match(case_id or ""):
        raise KitError("not a case id")
    key = holdout_kit.load_json(
        os.path.join(holdout_kit.sealed_dir(folder), "keys", case_id,
                     "key.json"),
        what="key.json of case %s" % case_id)
    slot = key.get("slot")
    if slot not in holdout_kit.SLOTS:
        raise KitError("key.json of case %s names no slot C1..Q3" % case_id)
    return slot


# ---------------------------------------------------------------- structure


def _check_slots(ctx):
    problems = []
    n = len(ctx.case_ids)
    if n != len(holdout_kit.SLOTS):
        problems.append("found %d case folders under sealed/cases, expected "
                        "6 (one per slot C1..Q3). Fix: add or remove cases "
                        "until each slot has exactly one" % n)
    for cid in ctx.case_ids:
        if cid not in ctx.key_ids:
            problems.append("case %s has no sealed/keys folder. Fix: write "
                            "its key, provenance and proof there, or remove "
                            "the case" % cid)
    for cid in ctx.key_ids:
        if cid not in ctx.case_ids:
            problems.append("sealed/keys/%s has no matching case folder. "
                            "Fix: remove it or restore its case" % cid)
    for c in ctx.cases:
        if c.slot is None and c.cid in ctx.key_ids:
            problems.append("case %s: key.json is missing, unreadable or "
                            "names no slot C1..Q3. Fix: %s"
                            % (c.cid, RULES_FIX))
    for slot in holdout_kit.SLOTS:
        count = sum(1 for c in ctx.cases if c.slot == slot)
        if count == 0:
            problems.append("no case fills slot %s. Fix: find a case for %s "
                            "or set the right slot in its key.json"
                            % (slot, slot))
        elif count > 1:
            problems.append("slot %s is used by %d cases. Fix: keep one case "
                            "per slot" % (slot, count))
    return _result("slots", problems,
                   "six cases, one per slot C1..Q3, each with a keys folder")


def _check_opaque_ids(ctx):
    problems = []
    for where, parent, names in (("sealed/cases", ctx.cases_dir,
                                  ctx.case_names),
                                 ("sealed/keys", ctx.keys_dir,
                                  ctx.key_names)):
        bad = sum(1 for n in names if not _is_id_dir(parent, n))
        if bad:
            problems.append("%s holds %d entr%s that %s not an opaque case "
                            "folder (H- followed by 8 hex digits). Fix: "
                            "rename or remove %s; a case name must never "
                            "describe the case"
                            % (where, bad, "y" if bad == 1 else "ies",
                               "is" if bad == 1 else "are",
                               "it" if bad == 1 else "them"))
    return _result("opaque ids", problems,
                   "every case folder is named H- plus 8 hex digits")


def _walk(path):
    """(files, problem) for a case or keys folder; problem is None or a
    plain description."""
    if not os.path.isdir(path):
        return None, None
    try:
        return holdout_kit.walk_regular(path), None
    except KitError:
        return None, "a link or special file is inside it"


def _check_allowlist(ctx):
    problems = []
    for c in ctx.cases:
        files, err = _walk(c.case_dir)
        if err:
            problems.append("%s: sealed/cases/%s: %s. Fix: remove it"
                            % (c.label, c.cid, err))
        elif files is not None:
            extra = [f for f in files if f not in holdout_kit.CASE_FILES]
            if extra:
                problems.append(
                    "%s: %d file(s) in sealed/cases/%s are not allowed (only "
                    "base.tar, case.json, change.diff). Fix: move them out "
                    "of the holdout" % (c.label, len(extra), c.cid))
            missing = sorted(holdout_kit.CASE_FILES - set(files))
            if missing:
                problems.append("%s: sealed/cases/%s is missing %s. Fix: "
                                "write it" % (c.label, c.cid,
                                              ", ".join(missing)))
            if "case.json" in files:
                meta = _load_or_none(os.path.join(c.case_dir, "case.json"))
                want = dict(CASE_JSON, id=c.cid)
                if meta != want:
                    problems.append(
                        "%s: case.json does not match the layout (id, base, "
                        "diff, apply_with). Fix: %s" % (c.label, RULES_FIX))
        files, err = _walk(c.key_dir)
        if err:
            problems.append("%s: sealed/keys/%s: %s. Fix: remove it"
                            % (c.label, c.cid, err))
        elif files is not None:
            extra = [f for f in files if f not in holdout_kit.KEY_FILES
                     and not f.startswith("proof/")]
            if extra:
                problems.append(
                    "%s: %d file(s) in sealed/keys/%s are not allowed (only "
                    "key.json, provenance.json, proof-results.json and "
                    "proof/). Fix: move them out of the holdout"
                    % (c.label, len(extra), c.cid))
            missing = [f for f in REQUIRED_KEY_FILES if f not in files]
            if missing:
                problems.append("%s: sealed/keys/%s is missing %s. Fix: "
                                "write it" % (c.label, c.cid,
                                              ", ".join(missing)))
    return _result("file allowlist", problems,
                   "only allowed file names, no links, case.json matches "
                   "the layout")


# ---------------------------------------------------------------- provenance


def _provenance_cases(ctx, problems=None):
    """Cases whose provenance.json loaded as an object. When `problems` is
    given, an existing but unreadable provenance.json is reported there."""
    out = []
    for c in ctx.cases:
        if isinstance(c.prov, dict):
            out.append(c)
        elif problems is not None and os.path.exists(
                os.path.join(c.key_dir, "provenance.json")):
            problems.append("%s: provenance.json is unreadable. Fix: %s"
                            % (c.label, RULES_FIX))
    return out


def _search(prov):
    s = prov.get("search")
    return s if isinstance(s, dict) else None


def _check_provenance(ctx):
    problems = []
    for c in _provenance_cases(ctx, problems):
        p = c.prov
        fix = "Fix: %s" % RULES_FIX
        missing = [k for k in PROVENANCE_KEYS if k not in p]
        if missing:
            problems.append("%s: provenance.json lacks %s. %s"
                            % (c.label, ", ".join(missing), fix))
        kind = p.get("kind")
        if kind not in KINDS:
            problems.append("%s: provenance kind must be organic or "
                            "constructed. %s" % (c.label, fix))
            continue
        extra_keys = ORGANIC_KEYS if kind == "organic" else CONSTRUCTED_KEYS
        unknown = set(p) - set(PROVENANCE_KEYS) - set(extra_keys)
        if unknown:
            problems.append("%s: provenance.json has %d field(s) the schema "
                            "does not define for a %s case. %s"
                            % (c.label, len(unknown), kind, fix))
        if kind == "organic":
            for k in ORGANIC_KEYS:
                if not _is_hex(p.get(k), 40):
                    problems.append("%s: %s must be a 40-hex commit id. %s"
                                    % (c.label, k, fix))
        elif p.get("constructed_by") not in CONSTRUCTED_BY:
            problems.append("%s: constructed_by must be owner or "
                            "isolated-agent. %s" % (c.label, fix))
        if p.get("slot") not in holdout_kit.SLOTS:
            problems.append("%s: provenance slot must be one of C1..Q3. %s"
                            % (c.label, fix))
        src = p.get("source_repo")
        if not _nonempty_str(src) or not os.path.isabs(src):
            problems.append("%s: source_repo must be an absolute path. %s"
                            % (c.label, fix))
        if not _nonempty_str(p.get("repo_name")):
            problems.append("%s: repo_name must be the repo folder name. %s"
                            % (c.label, fix))
        if "repo_in_b3" in p and not isinstance(p["repo_in_b3"], bool):
            problems.append("%s: repo_in_b3 must be true or false. %s"
                            % (c.label, fix))
        if "found_at" in p and not _is_iso(p["found_at"]):
            problems.append("%s: found_at must be an ISO-8601 time. %s"
                            % (c.label, fix))
        s = _search(p)
        if "search" in p and s is None:
            problems.append("%s: search must be an object. %s"
                            % (c.label, fix))
        elif s is not None:
            gaps = [k for k in SEARCH_KEYS if k not in s]
            if gaps or set(s) - set(SEARCH_KEYS):
                problems.append("%s: search must hold exactly %s. %s"
                                % (c.label, ", ".join(SEARCH_KEYS), fix))
            if "order_rule" in s and not _nonempty_str(s["order_rule"]):
                problems.append("%s: search.order_rule is empty. Fix: write "
                                "the screening order fixed before the "
                                "search" % c.label)
            if "rejections" in s and not isinstance(s["rejections"], list):
                problems.append("%s: search.rejections must be a list. %s"
                                % (c.label, fix))
    return _result("provenance fields", problems,
                   "every provenance.json has the required fields")


def _check_budget(ctx):
    problems = []
    for c in _provenance_cases(ctx):
        s = _search(c.prov)
        if s is None:
            continue
        if s.get("budget") != BUDGET or not _is_int(s.get("budget")):
            problems.append("%s: search.budget must be 25. Fix: set it to "
                            "25; the budget per type is fixed" % c.label)
        screened = s.get("screened")
        if not _is_int(screened) or not 1 <= screened <= BUDGET:
            shown = screened if _is_int(screened) else "not a number"
            problems.append("%s: search.screened is %s; it must be 1 to 25 "
                            "candidates per type. Fix: stop at the first "
                            "valid candidate within 25, or construct the "
                            "case after 25 rejections" % (c.label, shown))
    return _result("budget", problems,
                   "every search stayed within 25 candidates")


def _check_search_ledger(ctx):
    problems = []
    for c in _provenance_cases(ctx):
        p = c.prov
        s = _search(p)
        if s is None:
            continue
        screened = s.get("screened")
        rejections = s.get("rejections")
        if not _is_int(screened) or not isinstance(rejections, list):
            continue
        fix = ("Fix: record one rejection (ordinal, rev, reason) per "
               "candidate screened before the chosen one")
        shapes_ok = all(isinstance(r, dict) and set(r) == set(REJECTION_KEYS)
                        and _is_int(r["ordinal"]) and _nonempty_str(r["rev"])
                        and _nonempty_str(r["reason"]) for r in rejections)
        if not shapes_ok:
            problems.append("%s: every rejection needs exactly ordinal, rev "
                            "and reason, none empty. %s" % (c.label, fix))
            continue
        ordinals = sorted(r["ordinal"] for r in rejections)
        if ordinals != list(range(1, len(rejections) + 1)):
            problems.append("%s: rejection ordinals must run 1, 2, 3 ... "
                            "without gaps or repeats. %s" % (c.label, fix))
        kind = p.get("kind")
        if kind == "organic":
            if len(rejections) != screened - 1:
                problems.append(
                    "%s: %d candidates screened but %d rejections recorded; "
                    "an organic case needs exactly screened - 1 (the chosen "
                    "change is the last ordinal). %s"
                    % (c.label, screened, len(rejections), fix))
            if p.get("feature_rev") in {r["rev"] for r in rejections}:
                problems.append("%s: the chosen feature_rev is also listed "
                                "as rejected. %s" % (c.label, fix))
        elif kind == "constructed":
            if screened != BUDGET:
                problems.append(
                    "%s: a constructed case is allowed only after all 25 "
                    "candidates were screened and rejected. Fix: keep "
                    "searching, or record the full 25-candidate search"
                    % c.label)
            if len(rejections) != screened:
                problems.append(
                    "%s: %d candidates screened but %d rejections recorded; "
                    "a constructed case needs every candidate rejected. %s"
                    % (c.label, screened, len(rejections), fix))
    return _result("search ledger", problems,
                   "every search ledger adds up")


def _check_reviewer_output(ctx):
    problems = []
    for c in _provenance_cases(ctx):
        if c.prov.get("selected_using_reviewer_output", None) is not False:
            problems.append(
                "%s: selected_using_reviewer_output must be literally false. "
                "Fix: if a reviewer tool helped choose this case, replace "
                "the case; otherwise write false" % c.label)
    return _result("reviewer output", problems,
                   "no case was chosen with reviewer output")


def _check_repo_in_b3(ctx):
    try:
        b3_repos, _ = _b3_lists(ctx.folder)
    except KitError:
        return _result("repo_in_b3", [
            "kit/b3-exclusions.json is missing or unreadable. Fix: run setup "
            "again so the kit copy is complete"], "")
    problems = []
    for c in _provenance_cases(ctx):
        flag = c.prov.get("repo_in_b3")
        if not isinstance(flag, bool):
            continue
        hits = sorted(_repo_names(c.prov) & b3_repos)
        if flag != bool(hits):
            if hits:
                problems.append(
                    "%s: repo_in_b3 says false but %s is in the earlier "
                    "benchmark list (mismatch). Fix: set repo_in_b3 to true; "
                    "for C1 or Q2 choose a repo outside that list"
                    % (c.label, hits[0]))
            else:
                problems.append(
                    "%s: repo_in_b3 says true but the repo is not in the "
                    "earlier benchmark list (mismatch). Fix: set repo_in_b3 "
                    "to false" % c.label)
    return _result("repo_in_b3", problems,
                   "repo_in_b3 matches kit/b3-exclusions.json for every case")


def _check_eligibility(ctx):
    problems = []
    try:
        _, never = _b3_lists(ctx.folder)
    except KitError:
        never = None
        problems.append("kit/b3-exclusions.json is missing or unreadable. "
                        "Fix: run setup again so the kit copy is complete")
    try:
        eligible = _eligible_repos(ctx.folder)
    except KitError:
        eligible = None
        problems.append("kit/eligible-repos.json is missing or unreadable. "
                        "Fix: run setup again with every eligible --repo")
    for c in _provenance_cases(ctx):
        p = c.prov
        if never is not None:
            for name in sorted(_repo_names(p) & never):
                problems.append("%s: %s is the tuning repo or its mirror and "
                                "can never be a holdout source. Fix: replace "
                                "the case" % (c.label, name))
        src = p.get("source_repo")
        if isinstance(src, str) and eligible is not None \
                and os.path.normpath(src) not in eligible:
            problems.append("%s: source_repo is not one of the repos in "
                            "kit/eligible-repos.json. Fix: use a case from "
                            "an eligible repo" % c.label)
        name = p.get("repo_name")
        if isinstance(src, str) and isinstance(name, str) \
                and name != os.path.basename(os.path.normpath(src)):
            problems.append("%s: repo_name is not the folder name of "
                            "source_repo. Fix: set repo_name to that folder "
                            "name" % c.label)
    return _result("eligibility", problems,
                   "every case comes from an eligible repo")


def _check_c1_q2_eligibility(ctx):
    try:
        b3_repos, _ = _b3_lists(ctx.folder)
    except KitError:
        b3_repos = set()
    problems = []
    for slot in ("C1", "Q2"):
        c = ctx.by_slot(slot)
        if c is None or not isinstance(c.prov, dict):
            continue
        hits = sorted(_repo_names(c.prov) & b3_repos)
        if c.prov.get("repo_in_b3") is not False or hits:
            shown = (" (%s)" % hits[0]) if hits else ""
            problems.append("%s: comes from a repo in the earlier "
                            "benchmark%s; C1 and Q2 must come from a repo "
                            "outside it. Fix: choose a %s case from another "
                            "eligible repo" % (slot, shown, slot))
    return _result("C1/Q2 eligibility", problems,
                   "C1 and Q2 come from repos outside the earlier benchmark")


# ---------------------------------------------------------------- C1 / Q2


def _changed_lines(diff):
    """The +/- lines of every hunk in a unified diff, without the marker.

    Hunks are walked by their @@ line counts, so file headers (--- / +++)
    and context never enter the list."""
    out = []
    old = new = 0
    for line in diff.decode("utf-8", "replace").splitlines():
        if old > 0 or new > 0:
            tag = line[:1]
            if tag == "-":
                old -= 1
                out.append(line[1:])
            elif tag == "+":
                new -= 1
                out.append(line[1:])
            elif tag != "\\":
                old -= 1
                new -= 1
            continue
        if line.startswith("@@"):
            parts = line.split()
            if len(parts) >= 3:
                old = _hunk_len(parts[1])
                new = _hunk_len(parts[2])
    return out


def _hunk_len(spec):
    """Line count of a hunk range like '-12,3' or '+7' (default 1)."""
    _, _, count = spec[1:].partition(",")
    try:
        return int(count) if count else 1
    except ValueError:
        return 0


def _similarity(a, b):
    """Share of matching changed lines between two diffs (0.0 .. 1.0)."""
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def _check_c1_q2_distinct(ctx):
    c1, q2 = ctx.by_slot("C1"), ctx.by_slot("Q2")
    if c1 is None or q2 is None:
        return _result("C1/Q2 distinct", [],
                       "skipped until both C1 and Q2 exist")
    problems = []
    fix = "Fix: choose a Q2 change unrelated to C1"
    p1 = c1.prov if isinstance(c1.prov, dict) else {}
    p2 = q2.prov if isinstance(q2.prov, dict) else {}
    if p1.get("kind") == p2.get("kind") == "organic" \
            and p1.get("repo_name") == p2.get("repo_name") \
            and p1.get("feature_rev") == p2.get("feature_rev"):
        problems.append("C1 and Q2 are the same repo and revision. %s" % fix)
    d1, d2 = _diff_bytes(c1), _diff_bytes(q2)
    if d1 is not None and d2 is not None:
        if holdout_kit.sha256_bytes(d1) == holdout_kit.sha256_bytes(d2):
            problems.append("C1 and Q2 have the same diff. %s" % fix)
        else:
            ratio = _similarity(_changed_lines(d1), _changed_lines(d2))
            if ratio >= SIMILARITY_LIMIT:
                problems.append("C1 and Q2 changes are too similar (%d%% of "
                                "changed lines match; must be under 50%%). %s"
                                % (int(ratio * 100), fix))
    return _result("C1/Q2 distinct", problems,
                   "C1 and Q2 are distinct changes")


def _check_b3_reuse(ctx):
    try:
        commits, patches = _b3_hashes(ctx.folder)
    except KitError:
        return _result("B3 reuse", [
            "kit/b3-exclusions.json is missing or unreadable. Fix: run setup "
            "again so the kit copy is complete"], "")
    problems = []
    fix = ("Fix: replace the case; earlier-benchmark material can never be "
           "a holdout case")
    for c in ctx.cases:
        p = c.prov if isinstance(c.prov, dict) else {}
        for field in ORGANIC_KEYS:
            rev = p.get(field)
            if isinstance(rev, str) and \
                    holdout_kit.sha256_bytes(rev.encode("utf-8")) in commits:
                problems.append("%s: %s is a commit from the earlier "
                                "benchmark. %s" % (c.label, field, fix))
        diff = _diff_bytes(c)
        if diff is not None and holdout_kit.sha256_bytes(diff) in patches:
            problems.append("%s: change.diff is a patch from the earlier "
                            "benchmark. %s" % (c.label, fix))
    return _result("B3 reuse", problems,
                   "no earlier-benchmark commit or patch is reused")


# ---------------------------------------------------------------- keys


def _location_ok(loc):
    if not isinstance(loc, dict) or set(loc) != set(LOCATION_KEYS):
        return False
    start, end = loc.get("line_start"), loc.get("line_end")
    return (_nonempty_str(loc.get("file")) and _is_int(start)
            and _is_int(end) and 1 <= start <= end)


def _check_key_shape(ctx):
    problems, warnings = [], []
    for c in ctx.cases:
        k = c.key
        if not isinstance(k, dict) or c.slot is None:
            continue
        fix = "Fix: %s" % RULES_FIX
        catch = c.slot in holdout_kit.CATCH_SLOTS
        cls = "catch" if catch else "quiet"
        fields = CATCH_KEY_KEYS if catch else QUIET_KEY_KEYS
        if k.get("class") != cls:
            problems.append("%s: key class must be %s for this slot. %s"
                            % (c.label, cls, fix))
        missing = [f for f in fields if f not in k]
        if missing:
            problems.append("%s: key.json lacks %s. %s"
                            % (c.label, ", ".join(missing), fix))
        if set(k) - set(fields):
            problems.append("%s: key.json has %d field(s) a %s key does not "
                            "define. %s" % (c.label, len(set(k) - set(fields)),
                                            cls, fix))
        texts = (("defect", "causal_failure") if catch else
                 ("expected_quiet_rationale", "supported_behavior",
                  "exposure_check"))
        empty = [f for f in texts if f in k and not _nonempty_str(k[f])]
        if empty:
            problems.append("%s: %s must not be empty. Fix: write it in "
                            "plain words" % (c.label, ", ".join(empty)))
        if not catch:
            continue
        if "location" in k and not _location_ok(k["location"]):
            problems.append("%s: location needs file, line_start and "
                            "line_end (whole numbers, start <= end). %s"
                            % (c.label, fix))
        if "causal_failure_category" in k:
            cat = k["causal_failure_category"]
            if cat not in CAUSAL_CATEGORIES:
                problems.append("%s: causal_failure_category is not one of "
                                "the allowed categories (%s). Fix: pick the "
                                "closest one" % (c.label,
                                                 ", ".join(CAUSAL_CATEGORIES)))
            elif cat == OTHER_CATEGORY:
                warnings.append('%s: causal_failure_category is "other"; the '
                                'cross-check cannot agree mechanically and '
                                'the seal will block until resolved'
                                % c.label)
    return _result("key shape", problems,
                   "every key has the fields its class requires", warnings)


def _check_slot_agreement(ctx):
    problems = []
    for c in ctx.cases:
        if c.slot and isinstance(c.prov, dict) \
                and c.prov.get("slot") != c.slot:
            problems.append("%s: key.json and provenance.json name different "
                            "slots. Fix: make them agree" % c.label)
    return _result("slot agreement", problems,
                   "key and provenance agree on every slot")


# ---------------------------------------------------------------- proofs


def _check_proofs(ctx, skip_proofs):
    if skip_proofs:
        return [Check("proofs", True, "skipped (--skip-proofs)")]
    return [Check("proofs", False, "proofs were not re-executed. Fix: use "
                                   "a kit copy that can run them")]


# ---------------------------------------------------------------- entry


def validate_folder(folder, skip_proofs=False):
    """Run every check over <folder>/sealed and return the findings.

    A rule failure is a Check with ok False, never an exception; KitError is
    raised only when sealed/cases itself cannot be read."""
    ctx = _Ctx(folder)
    out = []
    for found in (_check_slots(ctx), _check_opaque_ids(ctx),
                  _check_allowlist(ctx), _check_provenance(ctx),
                  _check_budget(ctx), _check_search_ledger(ctx),
                  _check_reviewer_output(ctx), _check_repo_in_b3(ctx),
                  _check_eligibility(ctx), _check_c1_q2_eligibility(ctx),
                  _check_c1_q2_distinct(ctx), _check_b3_reuse(ctx),
                  _check_key_shape(ctx), _check_slot_agreement(ctx),
                  _check_proofs(ctx, skip_proofs)):
        out.extend(found if isinstance(found, list) else [found])
    return out


def nonrunnable_count(folder):
    """How many cases record runnable: false in proof-results.json."""
    return sum(1 for c in _Ctx(folder).cases
               if isinstance(c.results, dict)
               and c.results.get("runnable") is False)


def add_parser(sub, name):
    p = sub.add_parser(name, help="check the six cases against the validity "
                                  "rules and re-run every proof")
    p.add_argument("--skip-proofs", action="store_true",
                   help="do not re-run the proofs (seal never skips them)")


def _names(checks):
    seen = []
    for c in checks:
        if c.name not in seen:
            seen.append(c.name)
    return seen


def cmd(args):
    holdout_kit.refuse_if_claude_spawned(args.folder)
    checks = validate_folder(args.folder, skip_proofs=args.skip_proofs)
    for c in checks:
        line = "%s: %s" % (c.name, c.message)
        if c.ok:
            holdout_kit.print_ok(line)
        else:
            holdout_kit.print_problem(line)
    names = _names(checks)
    failed = _names([c for c in checks if not c.ok])
    if failed:
        holdout_kit.print_problem(
            "%d of %d checks failed (%s). Fix the lines above and run "
            "validate again" % (len(failed), len(names), ", ".join(failed)))
    else:
        holdout_kit.print_ok("all %d checks passed" % len(names))
    print("Warnings: %d" % sum(1 for c in checks if c.warning))
    print("Non-runnable cases: %d" % nonrunnable_count(args.folder))
    return 1 if failed else 0
