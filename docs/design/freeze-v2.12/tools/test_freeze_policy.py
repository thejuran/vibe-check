"""Tests for the post-freeze change policy in freeze_policy: run records,
slots and per-gate rules, classification over a commit range, inheritance,
the retune seal-order proof, eligibility and gate status."""

import copy
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import freeze_common  # noqa: E402
import freeze_policy as fp  # noqa: E402
import test_freeze_manifest as tfm  # noqa: E402
from freeze_common import FreezeError  # noqa: E402

SCRIPTS = os.path.join(tfm.REAL_REPO or "", "plugins", "vibe-check", "scripts")

CAND = "c" * 40
OTHER = "d" * 40
DIGEST = "e" * 64
SENTINEL = b"SEALED-CONTENT-SENTINEL-7f3a"

ROSTER = {"schema": "holdout-roster/1",
          "cases": {"H-00000001": "catch", "H-00000002": "catch",
                    "H-00000003": "catch", "H-00000004": "quiet",
                    "H-00000005": "quiet", "H-00000006": "quiet"}}

# The exact top-level keys each release-gate step writes (the engineering
# evidence record contract in docs/design/freeze-v2.12/README.md).
ENGINEERING_SHAPES = {
    "test-gate.json": ("candidate_sha", "head_sha", "candidate_guard", "ran_at",
                       "suites", "outcome"),
    "security-gate.json": ("candidate_sha", "head_sha", "candidate_guard", "range",
                           "versions", "halves", "coverage", "replica", "triage",
                           "outcome", "reasons"),
    "deep-review-release.json": ("candidate_sha", "head_sha", "candidate_guard",
                                 "reviewer_build_fingerprint", "reviewer_cache_path",
                                 "delta_range", "integration_range", "lanes_delta",
                                 "lanes_integration", "state_paths", "findings",
                                 "critical_count", "warning_count", "medium_count",
                                 "outcome"),
}


def engineering_evidence_dir(tmp_path, candidate_sha, outcome="pass", overrides=None):
    """Write the three engineering evidence files in their real shapes under
    `tmp_path` and return it. `overrides` = {file name: {key: value}} (a value
    of None removes the key). The one place the shapes are built."""
    os.makedirs(tmp_path, exist_ok=True)
    guard = "CANDIDATE OK %s head %s reporting-only" % (candidate_sha[:12],
                                                       candidate_sha[:12])
    review_outcome = "blocked" if outcome == "fail" else outcome
    docs = {
        "test-gate.json": {
            "candidate_sha": candidate_sha, "head_sha": candidate_sha,
            "candidate_guard": guard, "ran_at": "2026-10-15T00:00:00Z",
            "suites": [{"name": "plugin", "workdir": "plugins/vibe-check/scripts",
                        "command": "pytest -q", "passed": 10, "failed": 0,
                        "duration_s": 1.5, "python": "3.14.5", "pytest": "8.4.0"}],
            "outcome": outcome},
        "security-gate.json": {
            "candidate_sha": candidate_sha, "head_sha": candidate_sha,
            "candidate_guard": guard, "range": "a..b", "versions": {"semgrep": "1"},
            "halves": [], "coverage": {}, "replica": {}, "triage": [],
            "outcome": outcome, "reasons": []},
        "deep-review-release.json": {
            "candidate_sha": candidate_sha, "head_sha": candidate_sha,
            "candidate_guard": guard, "reviewer_build_fingerprint": "f" * 64,
            "reviewer_cache_path": "~/.claude/plugins/cache/x",
            "delta_range": "a..b", "integration_range": "c..b", "lanes_delta": [],
            "lanes_integration": [], "state_paths": [], "findings": [],
            "critical_count": 0, "warning_count": 0, "medium_count": 0,
            "outcome": review_outcome},
    }
    for name, doc in docs.items():
        for key, value in ((overrides or {}).get(name) or {}).items():
            if value is None:
                doc.pop(key, None)
            else:
                doc[key] = value
        with open(os.path.join(tmp_path, name), "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
    return tmp_path


def write_b3_run(root, diff, n, manifest_id, candidate_sha=CAND, stamps=True,
                 dirname=None):
    d = os.path.join(root, diff, dirname or "run-%d" % n)
    os.makedirs(d, exist_ok=True)
    lines = ["runtime_fingerprint: " + "9" * 64]
    if stamps:
        lines += ["manifest_id: " + manifest_id, "check_digest: " + DIGEST,
                  "candidate_sha: " + candidate_sha]
    with open(os.path.join(d, "fingerprint.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(d, "state.json"), "w", encoding="utf-8") as fh:
        fh.write("{}")
    return d


def write_harness_run(root, case, run, manifest_id, mode="default",
                      kind="preservation", verdict="COMPLETE", candidate_sha=CAND,
                      case_id=None):
    d = os.path.join(root, case, run)
    os.makedirs(d, exist_ok=True)
    rec = {"case_id": case_id or case, "mode": mode, "kind": kind,
           "verdict": verdict, "manifest_id": manifest_id,
           "check_digest": DIGEST, "candidate_sha": candidate_sha}
    with open(os.path.join(d, "run.json"), "w", encoding="utf-8") as fh:
        json.dump(rec, fh)
    return d


def write_holdout_run(root, case_id, n, manifest_id, candidate_sha=CAND):
    d = os.path.join(root, case_id, "run-%d" % n)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "identity.json"), "w", encoding="utf-8") as fh:
        json.dump({"case_id": case_id, "run_name": "run-%d" % n,
                   "manifest_id": manifest_id, "check_digest": DIGEST,
                   "candidate_sha": candidate_sha}, fh)
    return d


def make_manifest(candidate=CAND, previous=None, **edits):
    """A minimal manifest dict carrying every GATE_FIELDS entry; `previous`
    is the lineage parent manifest. `edits` = {dotted path: value}."""
    m = {
        "schema": "freeze-manifest/1",
        "candidate_sha": candidate,
        "plugin": {"tree_sha256": "1" * 64, "runtime_fingerprint": "9" * 64},
        "covered": {"docs/design/fix-harness/tools": {"tree_sha256": "2" * 64}},
        "models": {"top": {"value": "claude-x", "source": "default"}},
        "codex": {"cli_version": "1.2.3", "config": {"model": "gpt-x"}},
        "runners": {
            "b3": {"cli": {"version": "9.9.9"}, "user_level": {"h": "3" * 64},
                   "launch_model": {"value": "claude-fable-5-1[1m]"}},
            "holdout-eval": {"cli": {"version": "9.9.9"}, "user_level": {"h": "3" * 64},
                             "launch_model": {"value": "claude-fable-5-1[1m]"}},
            "fix-harness": {"sdk_version": "0.2.165"},
        },
        "lineage": {"previous_manifest_id": previous["manifest_id"] if previous else None,
                    "previous_candidate_sha": previous["candidate_sha"] if previous else None},
    }
    for path, value in edits.items():
        node = m
        parts = path.split(".")
        for part in parts[:-1]:
            node = node[part]
        if value is None:
            node.pop(parts[-1], None)
        else:
            node[parts[-1]] = value
    m["manifest_id"] = fp.manifest_content_id(m)
    return m


def _git(repo, *argv):
    tfm._run(repo, "git", *argv)


def _head(repo):
    return freeze_common.git(repo, "rev-parse", "HEAD").decode().strip()


def _commit(repo, msg, writes=(), removes=()):
    for rel, data in writes:
        tfm._write(repo, rel, data)
    for rel in removes:
        _git(repo, "rm", "-q", rel)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _head(repo)


class _Tmp(unittest.TestCase):
    def setUp(self):
        self._tmpd = tempfile.TemporaryDirectory()
        self.tmp = self._tmpd.name

    def tearDown(self):
        self._tmpd.cleanup()


# --------------------------------------------------------------------------- #
# Run records
# --------------------------------------------------------------------------- #

class TestReadRecord(_Tmp):
    M = "a" * 64

    def test_read_record_b3_slot_from_path(self):
        d = write_b3_run(self.tmp, "triggarr-autoescape", 2, self.M)
        rec = fp.read_record(d)
        self.assertEqual(rec["kind"], "b3")
        self.assertEqual(rec["gate"], "b3x3")
        self.assertEqual(rec["slot"], ("triggarr-autoescape", 2))
        self.assertTrue(rec["identity_ok"], rec["identity_reason"])
        self.assertEqual(rec["manifest_id"], self.M)
        self.assertEqual(rec["candidate_sha"], CAND)
        self.assertEqual(fp.read_record(os.path.join(d, "fingerprint.txt"))["slot"],
                         ("triggarr-autoescape", 2))

    def test_read_record_lacks_manifest_id(self):
        d = write_b3_run(self.tmp, "should-quiet-1", 1, self.M, stamps=False)
        rec = fp.read_record(d)
        self.assertFalse(rec["identity_ok"])
        self.assertEqual(rec["identity_reason"], "record lacks manifest_id")

    def test_read_record_harness_and_holdout_slots(self):
        h = write_harness_run(self.tmp, "triggarr-autoescape", "run-1", self.M, mode="gsd")
        rec = fp.read_record(h)
        self.assertEqual((rec["kind"], rec["gate"]), ("fix-harness", "workflow"))
        self.assertEqual(rec["slot"], ("triggarr-autoescape", "gsd", "preservation"))
        self.assertEqual(rec["verdict"], "COMPLETE")
        o = write_holdout_run(self.tmp, "H-00000001", 3, self.M)
        rec = fp.read_record(o)
        self.assertEqual((rec["kind"], rec["gate"], rec["slot"]),
                         ("holdout-eval", "holdoutx3", ("H-00000001", 3)))
        self.assertTrue(rec["identity_ok"])

    def test_read_record_lacks_slot_identity(self):
        d = os.path.join(self.tmp, "x", "run-1")
        os.makedirs(d)
        with open(os.path.join(d, "identity.json"), "w") as fh:
            json.dump({"case_id": "not-an-id", "run_name": "run-1",
                       "manifest_id": self.M, "check_digest": DIGEST,
                       "candidate_sha": CAND}, fh)
        rec = fp.read_record(d)
        self.assertFalse(rec["identity_ok"])
        self.assertEqual(rec["identity_reason"], "record lacks slot identity")

    def test_read_record_failed_and_superseded(self):
        d = write_b3_run(self.tmp, "should-quiet-2", 1, self.M,
                         dirname="run-1.failed-20261015")
        rec = fp.read_record(d)
        self.assertEqual(rec["verdict"], "FAILED")
        self.assertEqual(rec["slot"], ("should-quiet-2", 1))
        self.assertEqual(rec["superseded_by"], "should-quiet-2/run-1")
        d2 = write_b3_run(self.tmp, "should-quiet-2", 2, self.M)
        with open(os.path.join(d2, "SUPERSEDED"), "w") as fh:
            fh.write("should-quiet-2/run-2b\n")
        self.assertEqual(fp.read_record(d2)["superseded_by"], "should-quiet-2/run-2b")


class TestEngineeringRecords(_Tmp):
    def test_engineering_record_identity_from_real_shapes(self):
        ev = engineering_evidence_dir(self.tmp, CAND)
        for name, slot in (("test-gate.json", ("tests",)),
                           ("security-gate.json", ("security",)),
                           ("deep-review-release.json", ("deep-review",))):
            with open(os.path.join(ev, name)) as fh:
                self.assertEqual(set(json.load(fh)), set(ENGINEERING_SHAPES[name]))
            rec = fp.read_record(os.path.join(ev, name))
            self.assertEqual(rec["kind"], "engineering")
            self.assertTrue(rec["identity_ok"], rec["identity_reason"])
            self.assertIsNone(rec["manifest_id"])
            self.assertIsNone(rec["check_digest"])
            self.assertEqual(rec["slot"], slot)
            self.assertEqual(rec["verdict"], "pass")

    def test_engineering_record_lacks_candidate_guard(self):
        ev = engineering_evidence_dir(self.tmp, CAND, overrides={
            "test-gate.json": {"candidate_guard": None},
            "security-gate.json": {"candidate_guard": "CANDIDATE MOVED"}})
        for name in ("test-gate.json", "security-gate.json"):
            rec = fp.read_record(os.path.join(ev, name))
            self.assertFalse(rec["identity_ok"])
            self.assertEqual(rec["identity_reason"],
                             "engineering record lacks candidate_guard")

    def test_engineering_record_bound_wrong_candidate(self):
        ev = engineering_evidence_dir(self.tmp, OTHER)
        rec = fp.read_record(os.path.join(ev, "test-gate.json"))
        ok, reason = fp.engineering_record_bound(rec, make_manifest(CAND))
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("candidate mismatch ("), reason)
        self.assertTrue(fp.engineering_record_bound(rec, make_manifest(OTHER))[0])

    def test_engineering_record_bound_failed_outcome(self):
        ev = engineering_evidence_dir(self.tmp, CAND, outcome="fail")
        m = make_manifest(CAND)
        for name, out in (("test-gate.json", "fail"),
                          ("deep-review-release.json", "blocked")):
            ok, reason = fp.engineering_record_bound(
                fp.read_record(os.path.join(ev, name)), m)
            self.assertFalse(ok)
            self.assertEqual(reason, "engineering record failed: %s" % out)


# --------------------------------------------------------------------------- #
# Slots, roster
# --------------------------------------------------------------------------- #

class TestSlots(unittest.TestCase):
    @unittest.skipUnless(tfm.REAL_REPO, "needs the repo checkout")
    def test_b3_slots_match_score43(self):
        sys.path.insert(0, SCRIPTS)
        try:
            import score43
        finally:
            sys.path.remove(SCRIPTS)
        self.assertEqual(fp.B3_DIFFS, score43.DIFFS)
        self.assertEqual(fp.B3_CATCH_DIFFS, score43.CATCH_DIFFS)
        self.assertEqual(fp.B3_QUIET_EXCLUDED, score43.QUIET_EXCLUDED)
        self.assertEqual(fp.RUN_NUMBERS, score43.RUN_NUMBERS)
        self.assertEqual(len(fp.GATE_SLOTS["b3x3"]()), 36)

    def test_slot_sizes(self):
        self.assertEqual(len(fp.GATE_SLOTS["holdoutx3"](ROSTER)), 18)
        wf = fp.GATE_SLOTS["workflow"](ROSTER)
        self.assertEqual(len([s for s in wf if s[2] == "preservation"]), 16)
        self.assertEqual(len([s for s in wf if s[2] == "clean"]), 2)
        self.assertEqual(len(fp.GATE_SLOTS["engineering"]()), 3)

    def test_roster_rejects_wrong_shape(self):
        fp.validate_roster(ROSTER)
        bad = []
        r = copy.deepcopy(ROSTER)
        r["schema"] = "holdout-roster/2"
        bad.append(r)
        r = copy.deepcopy(ROSTER)
        r["cases"]["H-00000007"] = "quiet"
        bad.append(r)
        r = copy.deepcopy(ROSTER)
        r["cases"]["H-00000004"] = "catch"
        bad.append(r)
        r = copy.deepcopy(ROSTER)
        r["cases"]["h-bad"] = r["cases"].pop("H-00000006")
        bad.append(r)
        r = copy.deepcopy(ROSTER)
        r["extra"] = 1
        bad.append(r)
        bad.append(None)
        for obj in bad:
            with self.assertRaises(FreezeError):
                fp.validate_roster(obj)


# --------------------------------------------------------------------------- #
# Inheritance and reductions
# --------------------------------------------------------------------------- #

class TestInherit(unittest.TestCase):
    def test_inherit_requires_equal_fields(self):
        old = make_manifest(CAND)
        new = make_manifest(OTHER, previous=old)
        self.assertEqual(fp.inherit(old, new, "b3x3", {}), (True, "inheritable"))
        changed = make_manifest(OTHER, previous=old, **{"codex.config": {"model": "gpt-y"}})
        self.assertEqual(fp.inherit(old, changed, "b3x3", {}),
                         (False, "gate field differs: codex"))
        missing = make_manifest(OTHER, previous=old, **{"runners.b3.cli": None})
        self.assertEqual(fp.inherit(old, missing, "b3x3", {}),
                         (False, "lineage ambiguous: runners.b3.cli"))
        no_cov = make_manifest(OTHER, previous=old, covered={})
        self.assertEqual(fp.inherit(old, no_cov, "workflow", {}),
                         (False, "lineage ambiguous: covered[docs/design/fix-harness/]"))
        ok, reason = fp.inherit(old, new, "b3x3",
                                {"plugins/vibe-check/scripts/score.py":
                                 {"engineering", "detection"}})
        self.assertFalse(ok)
        self.assertIn("requires b3x3 rerun", reason)
        # A detection change does not touch the workflow gate.
        self.assertTrue(fp.inherit(old, new, "workflow",
                                   {"plugins/vibe-check/scripts/score.py":
                                    {"engineering", "detection"}})[0])

    def test_engineering_never_inherits(self):
        old = make_manifest(CAND)
        new = make_manifest(OTHER, previous=old)
        self.assertEqual(fp.inherit(old, new, "engineering", {}),
                         (False, "engineering never inherits across candidates"))

    def test_proposed_reductions(self):
        old = fp.load_path_map()
        new = copy.deepcopy({k: v for k, v in old.items() if k != "_compiled"})
        for rule in new["rules"]:
            if rule["glob"] == "plugins/vibe-check/scripts/score.py":
                rule["cats"] = ["reporting"]
        new["rules"].append({"glob": "plugins/**", "cats": ["reporting"]})
        red = fp.proposed_reductions(old, fp.validate_path_map(new))
        globs = [r[0] for r in red]
        self.assertIn("plugins/vibe-check/scripts/score.py", globs)
        self.assertIn("plugins/**", globs)
        self.assertEqual(fp.proposed_reductions(old, old), [])


class TestSealOrderRequired(unittest.TestCase):
    def test_seal_order_required_for_detection(self):
        self.assertTrue(fp.seal_order_required({"engineering", "detection"}))
        self.assertFalse(fp.seal_order_required({"engineering", "workflow"}))
        self.assertFalse(fp.seal_order_required({"reporting"}))


# --------------------------------------------------------------------------- #
# Retune seal-order proof on a git fixture
# --------------------------------------------------------------------------- #

class _SealRepo:
    """base(map) -> S0 original seal -> P previous candidate -> F failed
    measurement evidence -> RM `git rm` of the seal -> S1 replacement seal
    -> R repair (score.py) -> A active candidate (reporting only).
    Branch `late`: R -> RM2 -> S2 (seal after the repair) -> A2.
    Branch `remap`: R -> M (PATH-MAP remaps score.py to reporting) -> A3."""

    def __init__(self):
        self.fx = tfm._Fixture()
        r = self.repo = self.fx.repo
        with open(fp.DEFAULT_MAP, "rb") as fh:
            real_map = fh.read()
        self.base = _commit(r, "map", [(fp.MAP_SELF_PATH, real_map)])
        self.S0 = _commit(r, "seal", [(fp.SEAL_RELPATH, SENTINEL + b"-0")])
        self.P = _commit(r, "candidate 1", [("plugins/vibe-check/agents/a.md", "v2\n")])
        self.F = _commit(r, "failed measurement",
                         [("docs/design/freeze-v2.12/evidence/failed.json", "{}\n")])
        self.RM = _commit(r, "retire cases", removes=[fp.SEAL_RELPATH])
        self.S1 = _commit(r, "replacement seal", [(fp.SEAL_RELPATH, SENTINEL + b"-1")])
        self.R = _commit(r, "repair",
                         [("plugins/vibe-check/scripts/score.py", "print('fix')\n")])
        self.A = _commit(r, "results", [("README.md", "results\n")])
        _git(r, "checkout", "-q", "-b", "late", self.R)
        self.RM2 = _commit(r, "retire late", removes=[fp.SEAL_RELPATH])
        self.S2 = _commit(r, "late seal", [(fp.SEAL_RELPATH, SENTINEL + b"-2")])
        self.A2 = _commit(r, "results late", [("README.md", "late\n")])
        _git(r, "checkout", "-q", "-b", "remap", self.R)
        data = json.loads(real_map)
        for rule in data["rules"]:
            if rule["glob"] == "plugins/vibe-check/scripts/score.py":
                rule["cats"] = ["reporting"]
        self.M = _commit(r, "remap", [(fp.MAP_SELF_PATH, json.dumps(data, indent=2))])
        self.A3 = _commit(r, "results remap", [("README.md", "remap\n")])
        _git(r, "checkout", "-q", "-")

    def close(self):
        self.fx.close()

    def proof(self, **edits):
        p = {"schema": fp.SEAL_ORDER_SCHEMA, "previous_candidate_sha": self.P,
             "retired_case_ids": ["H-00000001"], "replacement_case_ids": ["H-0000000a"],
             "replacement_seal_commit": self.S1, "first_repair_commit": self.R}
        p.update(edits)
        return p


class _SealBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sr = _SealRepo()

    @classmethod
    def tearDownClass(cls):
        cls.sr.close()

    def setUp(self):
        self._tmpd = tempfile.TemporaryDirectory()
        self.tmp = self._tmpd.name

    def tearDown(self):
        self._tmpd.cleanup()

    def write_proof(self, proof, name="proof.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            if isinstance(proof, str):
                fh.write(proof)
            else:
                json.dump(proof, fh)
        return path

    def check(self, proof, active=None):
        return fp.retune_evidence_ok(self.write_proof(proof), self.sr.repo,
                                     self.sr.P, active or self.sr.A)


class TestSealOrder(_SealBase):
    def test_first_repair_commit_skips_seal_commits(self):
        self.assertEqual(fp.first_repair_commit(self.sr.repo, self.sr.P, self.sr.A),
                         self.sr.R)

    def test_retune_evidence_accepts_sealed_before_repair(self):
        self.assertEqual(self.check(self.sr.proof()), (True, []))

    def test_retune_evidence_rejects_original_seal(self):
        ok, reasons = self.check(self.sr.proof(replacement_seal_commit=self.sr.S0))
        self.assertFalse(ok)
        self.assertIn("replacement seal predates the previous candidate", reasons)

    def test_retune_evidence_rejects_late_replacement(self):
        ok, reasons = self.check(self.sr.proof(replacement_seal_commit=self.sr.S2),
                                 active=self.sr.A2)
        self.assertFalse(ok)
        self.assertIn("replacement sealed after the repair", reasons)

    def test_retune_evidence_rejects_wrong_repair_commit(self):
        for wrong in (self.sr.A, self.sr.F):
            ok, reasons = self.check(self.sr.proof(first_repair_commit=wrong))
            self.assertFalse(ok)
            self.assertTrue(any(r.startswith("first_repair_commit mismatch")
                                for r in reasons), reasons)

    def test_retune_evidence_rejects_holdout_cli_shape(self):
        ok, reasons = self.check({"schema": "vibe-check-holdout-seal/2",
                                  "cases": ["H-00000001"]})
        self.assertEqual((ok, reasons), (False, ["seal-order proof has unknown schema"]))
        ok, reasons = self.check(dict(self.sr.proof(), extra="x"))
        self.assertEqual(reasons, ["seal-order proof has unknown schema"])
        ok, reasons = self.check("SEAL.json has exactly one commit and it is an "
                                 "ancestor of %s\n" % self.sr.P)
        self.assertEqual((ok, reasons), (False, ["seal-order proof missing or unreadable"]))
        ok, reasons = fp.retune_evidence_ok(os.path.join(self.tmp, "absent.json"),
                                            self.sr.repo, self.sr.P, self.sr.A)
        self.assertEqual(reasons, ["seal-order proof missing or unreadable"])

    def test_retune_evidence_rejects_seal_commit_not_touching_seal(self):
        ok, reasons = self.check(self.sr.proof(replacement_seal_commit=self.sr.F))
        self.assertFalse(ok)
        self.assertIn("replacement seal commit does not add SEAL.json", reasons)

    def test_retune_evidence_rejects_removal_commit(self):
        ok, reasons = self.check(self.sr.proof(replacement_seal_commit=self.sr.RM))
        self.assertFalse(ok)
        self.assertIn("replacement seal commit does not add SEAL.json", reasons)

    def test_retune_evidence_rejects_bad_ids_and_previous(self):
        self.assertFalse(self.check(self.sr.proof(replacement_case_ids=["X-1"]))[0])
        self.assertFalse(self.check(self.sr.proof(replacement_case_ids=[]))[0])
        self.assertFalse(self.check(self.sr.proof(
            replacement_case_ids=["H-00000001"]))[0])
        ok, reasons = self.check(self.sr.proof(previous_candidate_sha=self.sr.base))
        self.assertEqual(reasons, ["seal-order proof names another previous candidate"])

    def test_first_repair_commit_uses_map_union(self):
        self.assertEqual(fp.first_repair_commit(self.sr.repo, self.sr.P, self.sr.A3),
                         self.sr.R)

    def test_map_edit_cannot_reduce(self):
        changed = fp.classify_commit_range(self.sr.repo, self.sr.S1, self.sr.A3)
        self.assertIn("detection", changed["plugins/vibe-check/scripts/score.py"])
        self.assertTrue(set(fp.RERUN_CATEGORIES) <= changed[fp.MAP_SELF_PATH])
        self.assertEqual(changed["README.md"], {"reporting"})

    def test_write_seal_order_proof_refuses_invalid(self):
        out = os.path.join(self.tmp, "seal-order.json")
        with self.assertRaises(FreezeError):
            fp.write_seal_order_proof(out, self.sr.repo, self.sr.P, self.sr.A2,
                                      fp.MAP_SELF_PATH, self.sr.S2, ["H-00000001"],
                                      ["H-0000000a"])
        self.assertFalse(os.path.exists(out))
        proof = fp.write_seal_order_proof(out, self.sr.repo, self.sr.P, self.sr.A,
                                          fp.MAP_SELF_PATH, self.sr.S1, ["H-00000001"],
                                          ["H-0000000a"])
        self.assertEqual(proof["first_repair_commit"], self.sr.R)
        self.assertEqual(fp.retune_evidence_ok(out, self.sr.repo, self.sr.P, self.sr.A),
                         (True, []))
        with self.assertRaises(FreezeError):
            fp.write_seal_order_proof(out, self.sr.repo, self.sr.P, self.sr.A,
                                      fp.MAP_SELF_PATH, self.sr.S1, ["H-00000001"],
                                      ["H-0000000a"])

    def test_seal_order_proof_never_reads_sealed_content(self):
        real = freeze_common.git
        calls = []

        def spy(repo, *argv, **kw):
            out = real(repo, *argv, **kw)
            calls.append((argv, out))
            return out
        with mock.patch.object(freeze_common, "git", spy):
            self.assertTrue(self.check(self.sr.proof())[0])
            self.check(self.sr.proof(replacement_seal_commit=self.sr.S0))
            fp.first_repair_commit(self.sr.repo, self.sr.P, self.sr.A3)
        self.assertTrue(calls)
        for argv, out in calls:
            if argv[0] in ("show", "cat-file", "archive"):
                self.assertFalse(any(fp.SEAL_RELPATH in str(a) for a in argv), argv)
            self.assertNotIn(SENTINEL, out, argv)


# --------------------------------------------------------------------------- #
# Mutants: each guard removed makes its target test fail
# --------------------------------------------------------------------------- #

class TestMutants(_SealBase):
    def _passes(self, test_name, cls):
        """Run one test (no class fixture re-run; a seal-repo class borrows
        this class's repo) and report whether it passed."""
        result = unittest.TestResult()
        seal = issubclass(cls, _SealBase)
        saved = cls.__dict__.get("sr")
        if seal:
            cls.sr = self.sr
        try:
            cls(test_name).run(result)
        finally:
            if seal:
                if saved is None:
                    del cls.sr
                else:
                    cls.sr = saved
        return result.wasSuccessful()

    def test_mutant_b_inherit_without_field_equality(self):
        name = "test_inherit_requires_equal_fields"
        self.assertTrue(self._passes(name, TestInherit))
        with mock.patch.object(fp, "_values_differ", lambda a, b: False):
            self.assertFalse(self._passes(name, TestInherit))

    def test_mutant_d_classify_range_new_map_only(self):
        name = "test_map_edit_cannot_reduce"
        self.assertTrue(self._passes(name, TestSealOrder))
        real = fp._maps_for_range
        with mock.patch.object(fp, "_maps_for_range",
                               lambda *a: real(*a)[1:]):
            self.assertFalse(self._passes(name, TestSealOrder))
            self.assertFalse(self._passes("test_first_repair_commit_uses_map_union",
                                          TestSealOrder))

    def test_mutant_l_engineering_identity_requires_manifest_id(self):
        name = "test_engineering_record_identity_from_real_shapes"
        self.assertTrue(self._passes(name, TestEngineeringRecords))
        with mock.patch.object(fp, "_engineering_identity",
                               lambda rec, data: fp._run_identity(rec)):
            self.assertFalse(self._passes(name, TestEngineeringRecords))

    def test_mutant_m_bound_without_candidate_comparison(self):
        name = "test_engineering_record_bound_wrong_candidate"
        self.assertTrue(self._passes(name, TestEngineeringRecords))
        with mock.patch.object(fp, "_candidate_matches", lambda r, m: True):
            self.assertFalse(self._passes(name, TestEngineeringRecords))

    def test_mutant_o_seal_before_repair_removed(self):
        name = "test_retune_evidence_rejects_late_replacement"
        self.assertTrue(self._passes(name, TestSealOrder))
        with mock.patch.object(fp, "_rule_seal_before_repair", lambda *a: None):
            self.assertFalse(self._passes(name, TestSealOrder))

    def test_mutant_p_repair_commit_from_proof(self):
        name = "test_retune_evidence_rejects_wrong_repair_commit"
        self.assertTrue(self._passes(name, TestSealOrder))
        holder = {}
        real_problems = fp._proof_problems

        def capture(proof, *a):
            holder["repair"] = proof.get("first_repair_commit") \
                if isinstance(proof, dict) else None
            return real_problems(proof, *a)
        with mock.patch.object(fp, "_proof_problems", capture), \
                mock.patch.object(fp, "first_repair_commit",
                                  lambda *a, **k: holder.get("repair")):
            self.assertFalse(self._passes(name, TestSealOrder))

    def test_mutant_q_after_previous_removed(self):
        name = "test_retune_evidence_rejects_original_seal"
        self.assertTrue(self._passes(name, TestSealOrder))
        with mock.patch.object(fp, "_rule_after_previous", lambda *a: None):
            self.assertFalse(self._passes(name, TestSealOrder))


if __name__ == "__main__":
    unittest.main()
