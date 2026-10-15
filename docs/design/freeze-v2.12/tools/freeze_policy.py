"""Path -> rerun-category classification for post-freeze changes.

PATH-MAP.json (schema `freeze-path-map/1`) lists glob rules, each naming the
categories a change to a matching path requires. The invariants:

  * a path's categories are the UNION over every matching rule;
  * an unmapped path requires every rerun category;
  * PATH-MAP.json itself requires every rerun category, whatever its rules
    say, so a map edit can never lower its own checks;
  * `reporting` is never implied by the fallback: it is the "no rerun,
    identity check still passes" category and only an explicit rule gives it.

The second half of the module turns the classification into enforcement:
which run records may count toward a release gate (`eligible`), whether a
gate is met (`gate_status`, slot-based), when a result may be inherited
across manifests (`inherit`), and the retune seal-order proof
(`retune_evidence_ok`).

Stdlib only (import lock: argparse, json, os, re, sys + freeze_common).
"""

import argparse
import json
import os
import re
import sys

import freeze_common
from freeze_common import FreezeError

SCHEMA = "freeze-path-map/1"
CATEGORIES = ("engineering", "detection", "workflow", "reporting")
ALL_CATEGORIES = frozenset(CATEGORIES)
RERUN_CATEGORIES = ("engineering", "detection", "workflow")
MAP_SELF_PATH = "docs/design/freeze-v2.12/PATH-MAP.json"
DEFAULT_MAP = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "PATH-MAP.json")

REQUIRED_CHECKS = {
    "engineering": ("tests", "security-scan", "deep-review"),
    "detection": tuple("b3-run-%d" % i for i in range(1, 4))
                 + tuple("holdout-run-%d" % i for i in range(1, 4)),
    "workflow": tuple("preservation-run-%d" % i for i in range(1, 17))
                + tuple("clean-tree-run-%d" % i for i in range(1, 3)),
}

_TOP_KEYS = {"schema", "categories", "rules", "unmapped"}
_RULE_KEYS = {"glob", "cats"}


def _cats_ok(cats):
    return (isinstance(cats, list) and bool(cats)
            and all(isinstance(c, str) and c in ALL_CATEGORIES for c in cats))


def load_path_map(path=DEFAULT_MAP):
    """Read and validate a path map; return it with compiled rule regexes
    under `_compiled`. Any shape problem raises FreezeError."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        raise FreezeError("path map unreadable or not JSON: %s" % path)
    return validate_path_map(data)


def validate_path_map(data):
    if not isinstance(data, dict) or set(data) != _TOP_KEYS:
        raise FreezeError("path map: top-level keys must be exactly %s"
                          % sorted(_TOP_KEYS))
    if data["schema"] != SCHEMA:
        raise FreezeError("path map: schema must be %s" % SCHEMA)
    cats = data["categories"]
    if not isinstance(cats, dict) or set(cats) != ALL_CATEGORIES:
        raise FreezeError("path map: categories must be exactly %s"
                          % sorted(ALL_CATEGORIES))
    unmapped = data["unmapped"]
    if not _cats_ok(unmapped) or not set(RERUN_CATEGORIES) <= set(unmapped):
        raise FreezeError("path map: unmapped must name every rerun category")
    rules = data["rules"]
    if not isinstance(rules, list) or not rules:
        raise FreezeError("path map: rules must be a non-empty list")
    compiled = []
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict) or set(rule) != _RULE_KEYS:
            raise FreezeError("path map: rule %d must have exactly glob + cats" % i)
        if not isinstance(rule["glob"], str) or not rule["glob"]:
            raise FreezeError("path map: rule %d glob must be a non-empty string" % i)
        if not _cats_ok(rule["cats"]):
            raise FreezeError("path map: rule %d cats must be a non-empty "
                              "subset of the categories" % i)
        compiled.append((freeze_common.glob_to_regex(rule["glob"]),
                         frozenset(rule["cats"])))
    out = dict(data)
    out["_compiled"] = compiled
    return out


def classify(paths, path_map):
    """{path: set(categories)} — union over every matching rule; unmapped
    paths get the map's fallback; the map file always gets every rerun
    category."""
    compiled = path_map.get("_compiled")
    if compiled is None:
        compiled = validate_path_map(path_map)["_compiled"]
    fallback = set(path_map["unmapped"])
    result = {}
    for path in paths:
        cats = set()
        matched = False
        for regex, rule_cats in compiled:
            if regex.match(path):
                matched = True
                cats |= rule_cats
        if not matched:
            cats = set(fallback)
        if path == MAP_SELF_PATH:
            cats |= set(RERUN_CATEGORIES)
        result[path] = cats
    return result


def required(cats):
    """{rerun category: check ids} for the rerun categories in `cats`;
    `reporting` requires no rerun."""
    return {c: REQUIRED_CHECKS[c] for c in RERUN_CATEGORIES if c in set(cats)}


# --------------------------------------------------------------------------- #
# eligibility / inheritance / gate status
# --------------------------------------------------------------------------- #

GATES = ("b3x3", "holdoutx3", "workflow", "engineering")
DETECTION_GATES = ("b3x3", "holdoutx3")
GATE_CATEGORY = {"b3x3": "detection", "holdoutx3": "detection",
                 "workflow": "workflow", "engineering": "engineering"}

# Copied from plugins/vibe-check/scripts/score43.py (DIFFS :104-109,
# CATCH_DIFFS :110-112, QUIET_EXCLUDED :116, RUN_NUMBERS :117). This module
# never imports score43; test_freeze_policy locks the copies equal.
B3_DIFFS = (
    "triggarr-secret-in-logs", "triggarr-autoescape", "third-organic-should-catch",
    "should-quiet-1", "should-quiet-2", "should-quiet-3",
    "triggarr-session-rotation", "triggarr-settings-form-split",
    "should-quiet-4", "should-quiet-5", "should-quiet-6", "should-quiet-7",
)
B3_CATCH_DIFFS = ("triggarr-secret-in-logs", "triggarr-autoescape",
                  "third-organic-should-catch", "triggarr-session-rotation",
                  "triggarr-settings-form-split")
B3_QUIET_EXCLUDED = ("should-quiet-7",)
RUN_NUMBERS = (1, 2, 3)

# MEAS-01 / MEAS-02 bars.
B3_FP_BAR = 3
HOLDOUT_CATCH_MIN = 2
HOLDOUT_QUIET_MAX = 1

WORKFLOW_MODES = ("default", "gsd")
CLEAN_ANY_CASE = "*"

# Opaque holdout case ids; the same pattern the holdout kit uses.
CASE_ID_RE = re.compile(r"^H-[0-9a-f]{8}$")
ROSTER_SCHEMA = "holdout-roster/1"
ROSTER_ROLES = ("catch", "quiet")
ROSTER_SIZE = 6

SEAL_RELPATH = "docs/design/holdout-v2.12/SEAL.json"
SEAL_ORDER_SCHEMA = "freeze-seal-order/1"
SEAL_ORDER_KEYS = frozenset(("schema", "previous_candidate_sha", "retired_case_ids",
                             "replacement_case_ids", "replacement_seal_commit",
                             "first_repair_commit"))

# Evidence written by the release-gate steps BEFORE any manifest exists:
# file name -> engineering slot name.
ENGINEERING_RECORD_FILES = {"test-gate.json": "tests",
                            "security-gate.json": "security",
                            "deep-review-release.json": "deep-review"}

RUN_DIR_RE = re.compile(r"^run-([0-9]+)(?:\.(failed|voided)-.+)?$")
SUPERSEDED_MARKER = "SUPERSEDED"

# Manifest fields a gate's result depends on; inheritance needs every one
# present and equal in both manifests. `covered[<prefix>]` = every covered
# entry under that prefix.
GATE_FIELDS = {
    "b3x3": ("plugin.tree_sha256", "models", "codex", "runners.b3.cli",
             "runners.b3.user_level", "runners.b3.launch_model"),
    "holdoutx3": ("plugin.tree_sha256", "models", "codex",
                  "runners.holdout-eval.cli", "runners.holdout-eval.user_level",
                  "runners.holdout-eval.launch_model"),
    "workflow": ("plugin.tree_sha256", "runners.fix-harness",
                 "covered[docs/design/fix-harness/]"),
    "engineering": ("candidate_sha",),
}


def _s12(value):
    return value[:12] if isinstance(value, str) and value else "none"


def _hex64(value):
    return isinstance(value, str) and bool(freeze_common.HEX64_RE.match(value))


def _hex40(value):
    return isinstance(value, str) and bool(freeze_common.HEX40_RE.match(value))


def _read_json_obj(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _str_or_none(value):
    return value if isinstance(value, str) and value else None


# --------------------------------------------------------------------------- #
# Run records
# --------------------------------------------------------------------------- #

def _blank_record(path, kind, gate, run):
    return {"kind": kind, "gate": gate, "slot": None, "manifest_id": None,
            "check_digest": None, "candidate_sha": None, "identity_ok": False,
            "identity_reason": None, "verdict": None, "outcome": None,
            "superseded_by": None, "path": path, "run": run}


def _parse_fingerprint(path):
    """`key: value` lines of a run's fingerprint.txt (the score43 format)."""
    out = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                key, sep, value = line.partition(":")
                if sep:
                    out.setdefault(key.strip(), value.strip())
    except OSError:
        return {}
    return out


def _run_identity(rec):
    """Identity rule for run kinds: all three stamp lines, well formed, and a
    slot. Returns the first problem or None."""
    for key, check in (("manifest_id", _hex64), ("check_digest", _hex64),
                       ("candidate_sha", _hex40)):
        if not check(rec[key]):
            return "record lacks %s" % key
    if rec["slot"] is None:
        return "record lacks slot identity"
    return None


def _engineering_identity(rec, data):
    """Identity rule for engineering evidence: candidate_sha + candidate_guard
    + outcome. manifest_id / check_digest are absent by design."""
    if not _hex40(rec["candidate_sha"]):
        return "engineering record lacks candidate_sha"
    guard = data.get("candidate_guard")
    if not isinstance(guard, str) or not guard.startswith("CANDIDATE OK"):
        return "engineering record lacks candidate_guard"
    if not _str_or_none(data.get("outcome")):
        return "engineering record lacks outcome"
    return None


def _read_engineering(path):
    name = os.path.basename(path)
    rec = _blank_record(path, "engineering", "engineering", name)
    rec["slot"] = (ENGINEERING_RECORD_FILES[name],)
    data = _read_json_obj(path)
    if data is None:
        rec["identity_reason"] = "engineering record unreadable"
        return rec
    rec["candidate_sha"] = _str_or_none(data.get("candidate_sha"))
    rec["outcome"] = _str_or_none(data.get("outcome"))
    rec["verdict"] = rec["outcome"]
    problem = _engineering_identity(rec, data)
    rec["identity_ok"] = problem is None
    rec["identity_reason"] = problem
    return rec


def _stamps_from(rec, data):
    for key in ("manifest_id", "check_digest", "candidate_sha"):
        rec[key] = _str_or_none(data.get(key))


def read_record(path):
    """One run record with its slot identity.

    `path` is a run directory, a record file inside one (`run.json`,
    `identity.json`, `fingerprint.txt`), or an engineering evidence file
    named in ENGINEERING_RECORD_FILES."""
    path = os.path.abspath(path)
    base = os.path.basename(path)
    # Engineering evidence predates the manifest (D-23): it is identified by
    # candidate_sha + candidate_guard + outcome, never by manifest_id.
    if base in ENGINEERING_RECORD_FILES:
        return _read_engineering(path)
    run_dir = os.path.dirname(path) if os.path.isfile(path) else path
    dname = os.path.basename(run_dir)
    parent = os.path.basename(os.path.dirname(run_dir))
    run = "%s/%s" % (parent, dname)
    m = RUN_DIR_RE.match(dname)
    if os.path.isfile(os.path.join(run_dir, "run.json")):
        rec = _blank_record(run_dir, "fix-harness", "workflow", run)
        data = _read_json_obj(os.path.join(run_dir, "run.json")) or {}
        _stamps_from(rec, data)
        parts = tuple(data.get(k) for k in ("case_id", "mode", "kind"))
        if all(isinstance(p, str) and p for p in parts):
            rec["slot"] = parts
        rec["verdict"] = _str_or_none(data.get("verdict"))
    elif os.path.isfile(os.path.join(run_dir, "identity.json")):
        rec = _blank_record(run_dir, "holdout-eval", "holdoutx3", run)
        data = _read_json_obj(os.path.join(run_dir, "identity.json")) or {}
        _stamps_from(rec, data)
        case_id = data.get("case_id")
        rm = RUN_DIR_RE.match(data.get("run_name") or "") \
            if isinstance(data.get("run_name"), str) else None
        if isinstance(case_id, str) and CASE_ID_RE.match(case_id) and rm:
            rec["slot"] = (case_id, int(rm.group(1)))
        rec["verdict"] = _str_or_none(data.get("verdict"))
    elif os.path.isfile(os.path.join(run_dir, "fingerprint.txt")):
        rec = _blank_record(run_dir, "b3", "b3x3", run)
        _stamps_from(rec, _parse_fingerprint(os.path.join(run_dir, "fingerprint.txt")))
        if m and parent:
            rec["slot"] = (parent, int(m.group(1)))
    else:
        rec = _blank_record(run_dir, "unknown", None, run)
        rec["identity_reason"] = "unrecognized run record"
        return rec
    if m and m.group(2):
        rec["verdict"] = "FAILED" if m.group(2) == "failed" else "voided"
        rec["superseded_by"] = "%s/run-%s" % (parent, m.group(1))
    marker = os.path.join(run_dir, SUPERSEDED_MARKER)
    if os.path.isfile(marker):
        try:
            with open(marker, encoding="utf-8", errors="replace") as fh:
                rec["superseded_by"] = fh.read().strip() or "a later run"
        except OSError:
            rec["superseded_by"] = "a later run"
    problem = _run_identity(rec)
    rec["identity_ok"] = problem is None
    rec["identity_reason"] = problem
    return rec


def _candidate_matches(record, active_manifest):
    want = active_manifest.get("candidate_sha")
    return _hex40(want) and record.get("candidate_sha") == want


def engineering_record_bound(record, active_manifest):
    """(ok, reason): the ONE rule for engineering evidence — identity ok, the
    record's candidate_sha equals the active manifest's, outcome `pass`.
    manifest_id is never consulted."""
    if record.get("kind") != "engineering":
        return False, "not an engineering record"
    if not record.get("identity_ok"):
        return False, record.get("identity_reason") or "identity check not recorded"
    if not _candidate_matches(record, active_manifest):
        return False, "candidate mismatch (%s vs active %s)" % (
            _s12(record.get("candidate_sha")),
            _s12(active_manifest.get("candidate_sha")))
    if record.get("outcome") != "pass":
        return False, "engineering record failed: %s" % record.get("outcome")
    return True, "candidate-bound"


# --------------------------------------------------------------------------- #
# Slots and per-gate rules
# --------------------------------------------------------------------------- #

def validate_roster(obj):
    """The holdout roster `{schema: holdout-roster/1, cases: {id: role}}`:
    exactly 6 opaque ids, 3 catch + 3 quiet. Returns it; FreezeError else."""
    if not isinstance(obj, dict) or set(obj) != {"schema", "cases"}:
        raise FreezeError("roster: keys must be exactly schema + cases")
    if obj["schema"] != ROSTER_SCHEMA:
        raise FreezeError("roster: schema must be %s" % ROSTER_SCHEMA)
    cases = obj["cases"]
    if not isinstance(cases, dict) or len(cases) != ROSTER_SIZE:
        raise FreezeError("roster: cases must name exactly %d ids" % ROSTER_SIZE)
    for cid, role in cases.items():
        if not isinstance(cid, str) or not CASE_ID_RE.match(cid):
            raise FreezeError("roster: case id outside ^H-[0-9a-f]{8}$")
        if role not in ROSTER_ROLES:
            raise FreezeError("roster: role must be catch or quiet")
    roles = list(cases.values())
    if roles.count("catch") != 3 or roles.count("quiet") != 3:
        raise FreezeError("roster: must be 3 catch + 3 quiet")
    return obj


def _b3_slots(roster=None):
    return frozenset((d, n) for d in B3_DIFFS for n in RUN_NUMBERS)


def _holdout_slots(roster=None):
    cases = validate_roster(roster)["cases"]
    return frozenset((cid, n) for cid in cases for n in RUN_NUMBERS)


def _workflow_slots(roster=None):
    cases = validate_roster(roster)["cases"]
    catch = list(B3_CATCH_DIFFS) + sorted(c for c, r in cases.items() if r == "catch")
    slots = {(c, m, "preservation") for c in catch for m in WORKFLOW_MODES}
    slots |= {(CLEAN_ANY_CASE, m, "clean") for m in WORKFLOW_MODES}
    return frozenset(slots)


def _engineering_slots(roster=None):
    return frozenset((name,) for name in ENGINEERING_RECORD_FILES.values())


GATE_SLOTS = {"b3x3": _b3_slots, "holdoutx3": _holdout_slots,
              "workflow": _workflow_slots, "engineering": _engineering_slots}

ROSTER_GATES = ("holdoutx3", "workflow")
VERDICT_GATES = ("b3x3", "holdoutx3")


def _verdict_key(slot):
    return "%s/run-%d" % (slot[0], slot[1])


def _rule_b3(filled, verdicts, active_manifest, roster=None):
    if not isinstance(verdicts, dict):
        return False, ["verdicts missing"]
    reasons, fired = [], 0
    for slot in sorted(filled):
        diff, key = slot[0], _verdict_key(slot)
        v = verdicts.get(key)
        if diff in B3_CATCH_DIFFS:
            if v not in ("CATCH", "MISS"):
                reasons.append("verdict missing: %s" % key)
            elif v == "MISS":
                reasons.append("catch slot missed: %s" % key)
        else:
            if v not in ("FIRED", "QUIET"):
                reasons.append("verdict missing: %s" % key)
            elif v == "FIRED" and diff not in B3_QUIET_EXCLUDED:
                fired += 1
    if fired > B3_FP_BAR:
        reasons.append("false alarms %d over the bar of %d" % (fired, B3_FP_BAR))
    return not reasons, reasons


def _rule_holdout(filled, verdicts, active_manifest, roster=None):
    if not isinstance(verdicts, dict):
        return False, ["verdicts missing"]
    try:
        cases = validate_roster(roster)["cases"]
    except FreezeError:
        return False, ["roster missing"]
    per = {cid: [] for cid in cases}
    reasons = []
    for slot in sorted(filled):
        key = _verdict_key(slot)
        v = verdicts.get(key)
        role = cases.get(slot[0])
        want = ("CATCH", "MISS") if role == "catch" else ("FIRED", "QUIET")
        if v not in want:
            reasons.append("verdict missing: %s" % key)
            continue
        per.setdefault(slot[0], []).append(v)
    # Judged per case, never aggregated across cases (MEAS-02).
    for cid in sorted(cases):
        vs = per.get(cid, [])
        if cases[cid] == "catch":
            caught = vs.count("CATCH")
            if caught < HOLDOUT_CATCH_MIN:
                reasons.append("holdout catch case %s caught %d/3" % (cid, caught))
        else:
            fired = vs.count("FIRED")
            if fired > HOLDOUT_QUIET_MAX:
                reasons.append("holdout quiet case %s fired %d/3" % (cid, fired))
    return not reasons, reasons


def _rule_workflow(filled, verdicts, active_manifest, roster=None):
    reasons = ["workflow run not COMPLETE: %s (%s)" % (rec["run"], rec.get("verdict"))
               for _, rec in sorted(filled.items()) if rec.get("verdict") != "COMPLETE"]
    return not reasons, reasons


def _rule_engineering(filled, verdicts, active_manifest, roster=None):
    reasons = []
    for _, rec in sorted(filled.items()):
        ok, reason = engineering_record_bound(rec, active_manifest)
        if not ok:
            reasons.append("%s: %s" % (rec["run"], reason))
    return not reasons, reasons


GATE_RULES = {"b3x3": _rule_b3, "holdoutx3": _rule_holdout,
              "workflow": _rule_workflow, "engineering": _rule_engineering}


# --------------------------------------------------------------------------- #
# Classification over a commit range (map self-protection: old ∪ new)
# --------------------------------------------------------------------------- #

def _map_at(repo, rev, path_map_rel):
    """The validated path map at `rev`, or None when absent or invalid (a
    None map classifies every path under every rerun category)."""
    data = freeze_common.blob_at(repo, rev, path_map_rel)
    if data is None:
        return None
    try:
        return validate_path_map(json.loads(data.decode("utf-8")))
    except (ValueError, UnicodeDecodeError, FreezeError):
        return None


def _maps_for_range(repo, old_rev, new_rev, path_map_rel):
    return [_map_at(repo, old_rev, path_map_rel), _map_at(repo, new_rev, path_map_rel)]


def _classify_union(paths, maps):
    result = {p: set() for p in paths}
    for pm in maps:
        if pm is None:
            for p in paths:
                result[p] |= set(RERUN_CATEGORIES)
            continue
        for p, cats in classify(paths, pm).items():
            result[p] |= cats
    return result


def _nul_list(out):
    return [p for p in out.decode("utf-8").split("\0") if p]


def classify_commit_range(repo, candidate_sha, head, path_map_rel=MAP_SELF_PATH):
    """{path: cats} for every path changed between `candidate_sha` and
    `head`, classified under the union of the map at both ends, so an edit
    to the map can never reduce the checks its own commit range owes."""
    freeze_common.validate_rev(candidate_sha)
    freeze_common.validate_rev(head)
    paths = _nul_list(freeze_common.git(repo, "diff-tree", "-r", "--no-commit-id",
                                        "--name-only", "-z", candidate_sha, head))
    return _classify_union(paths, _maps_for_range(repo, candidate_sha, head,
                                                  path_map_rel))


def _rules_by_glob(pm):
    out = {}
    for rule in pm["rules"]:
        out.setdefault(rule["glob"], set()).update(rule["cats"])
    return out


def proposed_reductions(old_map, new_map):
    """[(glob, old_cats, new_cats)] for every rule whose categories shrank or
    vanished, every new rule that can narrow the unmapped fallback, and a
    shrunk fallback (`<unmapped>`). Non-empty = needs owner approval; the
    reduction is never applied automatically."""
    old_r, new_r = _rules_by_glob(old_map), _rules_by_glob(new_map)
    old_unmapped, new_unmapped = set(old_map["unmapped"]), set(new_map["unmapped"])
    out = []
    for glob in sorted(old_r):
        new_c = new_r.get(glob)
        if new_c is None or not old_r[glob] <= new_c:
            out.append((glob, sorted(old_r[glob]), sorted(new_c or ())))
    for glob in sorted(set(new_r) - set(old_r)):
        if not old_unmapped <= new_r[glob]:
            out.append((glob, sorted(old_unmapped), sorted(new_r[glob])))
    if not old_unmapped <= new_unmapped:
        out.append(("<unmapped>", sorted(old_unmapped), sorted(new_unmapped)))
    return out


# --------------------------------------------------------------------------- #
# Inheritance
# --------------------------------------------------------------------------- #

def _field_value(manifest, field):
    """(present, value) of a GATE_FIELDS entry in `manifest`."""
    if field.startswith("covered[") and field.endswith("]"):
        prefix = field[len("covered["):-1]
        covered = manifest.get("covered")
        if not isinstance(covered, dict):
            return False, None
        picked = {k: v for k, v in covered.items() if k.startswith(prefix)}
        return bool(picked), picked
    node = manifest
    for part in field.split("."):
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return node is not None, node


def _values_differ(a, b):
    return freeze_common.canonical_json(a) != freeze_common.canonical_json(b)


def _field_problem(old_manifest, new_manifest, field):
    old_ok, old_v = _field_value(old_manifest, field)
    new_ok, new_v = _field_value(new_manifest, field)
    if not old_ok or not new_ok:
        return "lineage ambiguous: %s" % field
    if _values_differ(old_v, new_v):
        return "gate field differs: %s" % field
    return None


def inherit(old_manifest, new_manifest, gate, changed_cats_by_path):
    """(ok, reason): may `gate`'s result under `old_manifest` stand under
    `new_manifest`? Only when no changed path carries the gate's category and
    every GATE_FIELDS entry is present and equal in both. Engineering never
    inherits across candidates."""
    if gate not in GATE_FIELDS:
        return False, "unknown gate: %s" % gate
    if not isinstance(old_manifest, dict) or not isinstance(new_manifest, dict):
        return False, "lineage ambiguous: manifest"
    if gate == "engineering" and old_manifest.get("candidate_sha") \
            != new_manifest.get("candidate_sha"):
        return False, "engineering never inherits across candidates"
    cat = GATE_CATEGORY[gate]
    for path in sorted(changed_cats_by_path or {}):
        if cat in changed_cats_by_path[path]:
            return False, "changed path requires %s rerun: %s" % (gate, path)
    for field in GATE_FIELDS[gate]:
        problem = _field_problem(old_manifest, new_manifest, field)
        if problem:
            return False, problem
    return True, "inheritable"


# --------------------------------------------------------------------------- #
# Retune: replacement holdout cases sealed BEFORE the repair
# --------------------------------------------------------------------------- #

def seal_order_required(cats):
    """True iff the change set touches detection."""
    return "detection" in set(cats or ())


def _commit_paths(repo, sha):
    freeze_common.validate_rev(sha)
    return sorted(set(_nul_list(freeze_common.git(
        repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "-m", "-z", sha))))


def first_repair_commit(repo, previous_candidate_sha, active_candidate_sha,
                        path_map_rel=MAP_SELF_PATH):
    """The first commit on the ancestry path previous -> active whose changed
    paths classify (old ∪ new map) to a set containing detection, or None.

    The seal file itself is never a repair: a commit that only removes or
    adds SEAL.json is skipped, so the owner's retirement and replacement
    commits cannot be mistaken for the repair."""
    freeze_common.validate_rev(previous_candidate_sha)
    freeze_common.validate_rev(active_candidate_sha)
    maps = _maps_for_range(repo, previous_candidate_sha, active_candidate_sha,
                           path_map_rel)
    revs = freeze_common.git(repo, "rev-list", "--reverse", "--ancestry-path",
                             "%s..%s" % (previous_candidate_sha,
                                         active_candidate_sha)).decode().split()
    for sha in revs:
        paths = [p for p in _commit_paths(repo, sha) if p != SEAL_RELPATH]
        if not paths:
            continue
        cats = set()
        for c in _classify_union(paths, maps).values():
            cats |= c
        if "detection" in cats:
            return sha
    return None


def _resolves(repo, sha):
    try:
        out = freeze_common.git(repo, "rev-parse", "--verify", sha + "^{commit}")
    except FreezeError:
        return False
    return out.decode().strip() == sha


def _is_ancestor(repo, a, b):
    try:
        freeze_common.git(repo, "merge-base", "--is-ancestor", a, b)
    except FreezeError:
        return False
    return True


def _strict_ancestor(repo, a, b):
    return a != b and _is_ancestor(repo, a, b)


def _rule_after_previous(repo, previous, seal):
    if not _strict_ancestor(repo, previous, seal):
        return "replacement seal predates the previous candidate"
    return None


def _seal_statuses(repo, seal):
    tokens = _nul_list(freeze_common.git(repo, "diff-tree", "--no-commit-id",
                                         "--name-status", "-r", "-z", seal))
    out, i = [], 0
    while i < len(tokens):
        status = tokens[i]
        width = 2 if status[:1] in ("R", "C") else 1
        for path in tokens[i + 1:i + 1 + width]:
            out.append((status, path))
        i += 1 + width
    return out


def _rule_adds_seal(repo, seal):
    if ("A", SEAL_RELPATH) not in _seal_statuses(repo, seal):
        return "replacement seal commit does not add SEAL.json"
    return None


def _rule_repair_matches(proof_repair, computed):
    if computed is None:
        return "no detection change after the previous candidate"
    if proof_repair != computed:
        return "first_repair_commit mismatch (proof %s computed %s)" % (
            _s12(proof_repair), _s12(computed))
    return None


def _rule_seal_before_repair(repo, seal, repair):
    if not _strict_ancestor(repo, seal, repair):
        return "replacement sealed after the repair"
    return None


def _rule_repair_in_active(repo, repair, active):
    if not _is_ancestor(repo, repair, active):
        return "first repair commit is not in the active candidate"
    return None


def _proof_problems(proof, repo, previous_candidate_sha, active_candidate_sha,
                    path_map_rel):
    if not isinstance(proof, dict) or proof.get("schema") != SEAL_ORDER_SCHEMA \
            or set(proof) != SEAL_ORDER_KEYS:
        return ["seal-order proof has unknown schema"]
    if not _hex40(previous_candidate_sha) \
            or proof["previous_candidate_sha"] != previous_candidate_sha:
        return ["seal-order proof names another previous candidate"]
    for key in ("replacement_seal_commit", "first_repair_commit"):
        if not _hex40(proof[key]) or not _resolves(repo, proof[key]):
            return ["seal-order proof commit unresolvable: %s" % key]
    retired, repl = proof["retired_case_ids"], proof["replacement_case_ids"]
    for ids in (retired, repl):
        if not isinstance(ids, list) or not all(
                isinstance(i, str) and CASE_ID_RE.match(i) for i in ids):
            return ["seal-order proof has an invalid case id"]
    if not repl or set(repl) & set(retired):
        return ["replacement case ids are empty or overlap the retired ids"]
    seal = proof["replacement_seal_commit"]
    reasons = []
    for problem in (_rule_after_previous(repo, previous_candidate_sha, seal),
                    _rule_adds_seal(repo, seal)):
        if problem:
            reasons.append(problem)
    computed = first_repair_commit(repo, previous_candidate_sha,
                                   active_candidate_sha, path_map_rel)
    problem = _rule_repair_matches(proof["first_repair_commit"], computed)
    if problem:
        reasons.append(problem)
    if computed is not None:
        for problem in (_rule_seal_before_repair(repo, seal, computed),
                        _rule_repair_in_active(repo, computed, active_candidate_sha)):
            if problem:
                reasons.append(problem)
    return reasons


def retune_evidence_ok(proof_path, repo, previous_candidate_sha,
                       active_candidate_sha, path_map_rel=MAP_SELF_PATH):
    """(ok, reasons) for the replacement-seal proof at `proof_path`, checked
    by git topology and file NAMES only; sealed content is never read."""
    proof = None
    if isinstance(proof_path, str) and os.path.isfile(proof_path):
        try:
            with open(proof_path, "r", encoding="utf-8") as fh:
                proof = json.load(fh)
        except (OSError, ValueError):
            proof = None
    if proof is None:
        return False, ["seal-order proof missing or unreadable"]
    try:
        reasons = _proof_problems(proof, repo, previous_candidate_sha,
                                  active_candidate_sha, path_map_rel)
    except FreezeError as exc:
        reasons = ["seal-order proof could not be checked: %s" % exc]
    return not reasons, reasons


def write_seal_order_proof(path, repo, previous_candidate_sha, active_candidate_sha,
                           path_map_rel, replacement_seal_commit, retired_case_ids,
                           replacement_case_ids):
    """The only writer of a seal-order proof. The repair commit is computed,
    the proof is validated before writing, and an existing path is refused."""
    computed = first_repair_commit(repo, previous_candidate_sha,
                                   active_candidate_sha, path_map_rel)
    if computed is None:
        raise FreezeError("no detection change after the previous candidate")
    proof = {"schema": SEAL_ORDER_SCHEMA,
             "previous_candidate_sha": previous_candidate_sha,
             "retired_case_ids": list(retired_case_ids),
             "replacement_case_ids": list(replacement_case_ids),
             "replacement_seal_commit": replacement_seal_commit,
             "first_repair_commit": computed}
    reasons = _proof_problems(proof, repo, previous_candidate_sha,
                              active_candidate_sha, path_map_rel)
    if reasons:
        raise FreezeError("seal-order proof refused: " + "; ".join(reasons))
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o644)
    except FileExistsError:
        raise FreezeError("refused: seal-order proof already exists: %s" % path)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    return proof


# --------------------------------------------------------------------------- #
# Manifests (light loader: content id check only)
# --------------------------------------------------------------------------- #

def manifest_content_id(manifest):
    """sha256 of the canonical JSON of the manifest minus `manifest_id` (the
    freeze_manifest.manifest_id formula)."""
    return freeze_common.canonical_sha256(
        {k: v for k, v in manifest.items() if k != "manifest_id"})


def load_manifest_file(path):
    """A manifest dict whose manifest_id matches its content and whose
    candidate_sha is 40-hex; FreezeError names the file otherwise."""
    m = _read_json_obj(path)
    if m is None:
        raise FreezeError("manifest unreadable or not a JSON object: %s" % path)
    if not _hex64(m.get("manifest_id")) or m["manifest_id"] != manifest_content_id(m):
        raise FreezeError("manifest_id does not match the content of %s" % path)
    if not _hex40(m.get("candidate_sha")):
        raise FreezeError("manifest lacks a 40-hex candidate_sha: %s" % path)
    return m


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

REPO_DEFAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
EVIDENCE_REL = "docs/design/freeze-v2.12/evidence"


def _cmd_classify(args):
    changed = classify_commit_range(args.repo, args.candidate, args.head)
    for path in sorted(changed):
        print("%s: %s" % (path, ", ".join(sorted(changed[path])) or "none"))
    union = set()
    for cats in changed.values():
        union |= cats
    print("required: %s" % (", ".join(c for c in RERUN_CATEGORIES if c in union)
                            or "none (reporting only)"))
    if MAP_SELF_PATH in changed:
        old_map = _map_at(args.repo, args.candidate, MAP_SELF_PATH)
        new_map = _map_at(args.repo, args.head, MAP_SELF_PATH)
        if old_map is None or new_map is None:
            print("needs owner approval: path map absent or invalid at one end")
            return 1
        reductions = proposed_reductions(old_map, new_map)
        for glob, old_c, new_c in reductions:
            print("needs owner approval: %s [%s] -> [%s]"
                  % (glob, ", ".join(old_c), ", ".join(new_c)))
        if reductions:
            return 1
    return 0


def _cmd_seal_order_proof(args):
    active = load_manifest_file(args.manifest)
    previous = load_manifest_file(args.previous_manifest)
    lineage = active.get("lineage") or {}
    if lineage.get("previous_manifest_id") != previous["manifest_id"]:
        raise FreezeError("the manifest's lineage does not name the previous manifest")
    out = args.out or os.path.join(args.repo, EVIDENCE_REL,
                                   "seal-order-%s.json" % active["manifest_id"][:12])
    proof = write_seal_order_proof(out, args.repo, previous["candidate_sha"],
                                   active["candidate_sha"], MAP_SELF_PATH,
                                   args.seal_commit, args.retired or [],
                                   args.replacement)
    print("seal-order proof written: %s (first repair %s)"
          % (out, proof["first_repair_commit"]))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="freeze_policy.py",
                                     description="Post-freeze change policy.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("classify", help="rerun categories for a commit range")
    p.add_argument("--candidate", required=True)
    p.add_argument("--head", default="HEAD")
    p.add_argument("--repo", default=REPO_DEFAULT)
    p = sub.add_parser("seal-order-proof",
                       help="write the replacement-seal proof for a retune")
    p.add_argument("--manifest", required=True)
    p.add_argument("--previous-manifest", required=True)
    p.add_argument("--seal-commit", required=True)
    p.add_argument("--retired", nargs="*", default=[])
    p.add_argument("--replacement", nargs="+", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--repo", default=REPO_DEFAULT)
    return parser


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        if args.cmd == "classify":
            return _cmd_classify(args)
        return _cmd_seal_order_proof(args)
    except FreezeError as exc:
        sys.stderr.write("freeze_policy.py: %s\n" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
