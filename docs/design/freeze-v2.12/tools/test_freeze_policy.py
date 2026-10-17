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
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
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
    # The exact line `freeze_check.py candidate-guard` prints.
    guard = ("CANDIDATE OK candidate=%s head=%s descendant_commits=3 "
             "(reporting-only)" % (candidate_sha, "e" * 40))
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


def write_validity(run_dir, valid=True, reasons=(), state_sha256=None):
    """A run-validity record in the shape freeze_policy.write_validity writes."""
    with open(os.path.join(run_dir, "validity.json"), "w", encoding="utf-8") as fh:
        json.dump({"schema": "freeze-run-validity/1", "valid": valid,
                   "reasons": list(reasons), "transcript_sha256": "1" * 64,
                   "state_sha256": state_sha256 or "2" * 64,
                   "checked_at": "2026-10-17T00:00:00Z"}, fh)


def write_b3_run(root, diff, n, manifest_id, candidate_sha=CAND, stamps=True,
                 dirname=None, valid=True):
    d = os.path.join(root, diff, dirname or "run-%d" % n)
    os.makedirs(d, exist_ok=True)
    lines = ["runtime_fingerprint: " + "9" * 64]
    if stamps:
        lines += ["manifest_id: " + manifest_id, "check_digest: " + DIGEST,
                  "candidate_sha: " + candidate_sha]
    with open(os.path.join(d, "fingerprint.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(d, "state.json"), "w", encoding="utf-8") as fh:
        fh.write('{"passes": [{"findings": []}]}')
    if valid is not None:
        write_validity(d, valid, () if valid else ("permission failure: Bash",),
                       freeze_common.sha256_file(os.path.join(d, "state.json")))
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


def write_holdout_run(root, case_id, n, manifest_id, candidate_sha=CAND, valid=True):
    d = os.path.join(root, case_id, "run-%d" % n)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "identity.json"), "w", encoding="utf-8") as fh:
        json.dump({"case_id": case_id, "run_name": "run-%d" % n,
                   "manifest_id": manifest_id, "check_digest": DIGEST,
                   "candidate_sha": candidate_sha}, fh)
    if valid is not None:
        write_validity(d, valid, () if valid else ("no scorer output",))
    return d


def make_manifest(candidate=CAND, previous=None, **edits):
    """A minimal manifest dict carrying every GATE_FIELDS entry; `previous`
    is the lineage parent manifest. `edits` = {dotted path: value}."""
    m = {
        "schema": "freeze-manifest/1",
        "candidate_sha": candidate,
        "plugin": {"root": "plugins/vibe-check", "tree_sha256": "1" * 64,
                   "runtime_fingerprint": "9" * 64,
                   "files": {"README.md": {"sha256": "4" * 64, "mode": "100644"},
                             "agents/a.md": {"sha256": "7" * 64, "mode": "100644"}}},
        "covered": {"docs/design/fix-harness/tools": {"tree_sha256": "2" * 64}},
        "models": {"top": {"value": "claude-x", "source": "default"}},
        "codex": {"cli_version": "1.2.3", "config": {"model": "gpt-x"}},
        "runners": {
            "b3": {"cli": {"version": "9.9.9"}, "user_level": {"h": "3" * 64},
                   "launch_model": {"value": "claude-fable-5-1[1m]"},
                   "runner_settings": {"template_canonical_sha256": "5" * 64},
                   "gateway": {"plugin_version": "0.51.2", "tree_sha256": "6" * 64,
                               "base_url": "http://127.0.0.1:18764",
                               "version_id": "0.51.2"}},
            "holdout-eval": {"cli": {"version": "9.9.9"}, "user_level": {"h": "3" * 64},
                             "launch_model": {"value": "claude-fable-5-1[1m]"},
                             "runner_settings": {"template_canonical_sha256": "5" * 64}},
            "fix-harness": {"sdk_version": "0.2.165",
                            "env": {"ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5[1m]",
                                    "ANTHROPIC_BASE_URL": None}},
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

    def test_engineering_guard_must_name_the_records_candidate(self):
        """The guard line is the candidate-guard output for THIS record's
        candidate: a copied line naming another commit, or one naming none,
        is not the record's guard."""
        copied = ("CANDIDATE OK candidate=%s head=%s descendant_commits=1 "
                  "(reporting-only)" % (OTHER, "e" * 40))
        cases = {"copied": copied, "no candidate": "CANDIDATE OK",
                 "short sha": "CANDIDATE OK candidate=%s head=x" % CAND[:12],
                 "two candidates": copied.replace(
                     "head=", "candidate=%s head=" % CAND)}
        for label, line in cases.items():
            with self.subTest(label=label):
                ev = engineering_evidence_dir(self.tmp, CAND, overrides={
                    "test-gate.json": {"candidate_guard": line}})
                rec = fp.read_record(os.path.join(ev, "test-gate.json"))
                self.assertFalse(rec["identity_ok"])
                self.assertEqual(rec["identity_reason"],
                                 "engineering record guard names another candidate")

    def test_real_engineering_evidence_records_still_read(self):
        """The committed test/security/deep-review records name their own
        candidate in the guard line."""
        ev = os.path.join(HERE, "..", "evidence")
        for name in ("test-gate.json", "security-gate.json",
                     "deep-review-release.json"):
            path = os.path.join(ev, name)
            if not os.path.isfile(path):
                continue
            with self.subTest(name=name):
                rec = fp.read_record(path)
                self.assertTrue(rec["identity_ok"], rec["identity_reason"])

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

    def test_detection_gates_bind_gateway_and_process_env(self):
        """A gateway update or an allowlisted model-env change between
        manifests blocks inheritance of both detection gates (D-17: the
        model routing they were measured under changed)."""
        old = make_manifest(CAND)
        edits = {
            "gateway": {"runners.b3.gateway": {
                "plugin_version": "0.52.0", "tree_sha256": "8" * 64,
                "base_url": "http://127.0.0.1:18764", "version_id": "0.52.0"}},
            "process env": {"runners.fix-harness.env": {
                "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-6[1m]",
                "ANTHROPIC_BASE_URL": None}},
            "runner settings b3": {"runners.b3.runner_settings": {
                "template_canonical_sha256": "c" * 64}},
        }
        for label, edit in edits.items():
            new = make_manifest(OTHER, previous=old, **edit)
            field = next(iter(edit))
            for gate in ("b3x3", "holdoutx3"):
                with self.subTest(label=label, gate=gate):
                    ok, reason = fp.inherit(old, new, gate, {})
                    if gate == "holdoutx3" and field == "runners.b3.runner_settings":
                        self.assertTrue(ok)
                        continue
                    self.assertEqual((ok, reason),
                                     (False, "gate field differs: %s" % field))
        held = make_manifest(OTHER, previous=old, **{
            "runners.holdout-eval.runner_settings": {
                "template_canonical_sha256": "c" * 64}})
        self.assertEqual(fp.inherit(old, held, "holdoutx3", {}),
                         (False, "gate field differs: "
                                 "runners.holdout-eval.runner_settings"))

    def test_detection_gate_fields_cover_every_identity_class(self):
        """Every identity class the runner's own check binds maps to a
        manifest field, and that field is in the gate's GATE_FIELDS (classes
        bound by the changed-path classification map to None)."""
        import freeze_check
        self.assertEqual(fp.PROCESS_ENV_FIELD,
                         "runners.fix-harness.env")
        for gate, runner in fp.DETECTION_RUNNER.items():
            for cls in freeze_check.PROFILE_CLASSES[runner]:
                with self.subTest(gate=gate, cls=cls):
                    self.assertIn(cls, fp.CLASS_FIELDS)
                    field = fp.class_field(cls, runner)
                    if field is not None:
                        self.assertIn(field, fp.GATE_FIELDS[gate])

    def test_check_reads_the_policy_env_baseline(self):
        import freeze_check
        m = make_manifest(CAND)
        self.assertEqual(freeze_check._process_env_baseline(m),
                         m["runners"]["fix-harness"]["env"])

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


class TestPathMapCoverage(unittest.TestCase):
    """Each plugin helper maps to every workflow a runner actually runs it in
    (README: shared helpers map to every workflow they affect)."""

    REQUIRED = {
        # harness_seed builds every pass-1 state with score.py
        "plugins/vibe-check/scripts/score.py": {"engineering", "detection", "workflow"},
        # gitguard is the review agents' PreToolUse hook; gitsnap's compare
        # halts any review pass
        "plugins/vibe-check/scripts/gitguard.py": {"engineering", "detection", "workflow"},
        "plugins/vibe-check/scripts/gitsnap.py": {"engineering", "detection", "workflow"},
        # Phase 0.5 forward migration runs on every review (05-state.md)
        "plugins/vibe-check/scripts/review_archive.py": {"engineering", "detection",
                                                         "workflow"},
        # every B3 run reaches the fix-loop card and picks Stop here… from it
        "plugins/vibe-check/scripts/batch_card.py": {"engineering", "detection",
                                                     "workflow"},
    }

    def test_helpers_carry_every_workflow_they_run_in(self):
        pm = fp.load_path_map()
        cats = fp.classify(sorted(self.REQUIRED), pm)
        for path, want in self.REQUIRED.items():
            with self.subTest(path=path):
                self.assertTrue(want <= set(cats[path]), (path, cats[path]))

    def test_map_change_only_adds_categories(self):
        """The edit since the 24c0c00 candidate map is additions only: no
        rule's categories shrink or vanish."""
        try:
            blob = freeze_common.git(REPO_ROOT, "show",
                                     "24c0c00:" + fp.MAP_SELF_PATH)
        except Exception:  # noqa: BLE001 - outside the checkout
            self.skipTest("candidate map not reachable")
        old = fp.validate_path_map(json.loads(blob.decode("utf-8")))
        self.assertEqual(fp.proposed_reductions(old, fp.load_path_map()), [])
        cats = fp.classify([fp.MAP_SELF_PATH], fp.load_path_map())
        self.assertEqual(set(cats[fp.MAP_SELF_PATH]),
                         {"engineering", "detection", "workflow"})


def _tool_result(text, is_error=True):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t1", "is_error": is_error,
         "content": text}]}}


def _turn(text):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": text}]}}


class TestRunValidity(_Tmp):
    """The invalid-run rule: a permission failure, an incomplete review or
    missing scorer output makes a run INVALID — never quiet, never a miss."""

    def files(self, events=None, state=None):
        t = os.path.join(self.tmp, "transcript.jsonl")
        with open(t, "w", encoding="utf-8") as fh:
            for ev in (events if events is not None else
                       [{"type": "user", "message": {"role": "user", "content":
                                                     "/vibe-check:deep-review"}},
                        _turn("Pass 1 done")]):
                fh.write(json.dumps(ev) + "\n")
        st = os.path.join(self.tmp, "state.json")
        if state is not False:
            with open(st, "w", encoding="utf-8") as fh:
                json.dump(state if state is not None else
                          {"passes": [{"pass_number": 1, "agents_run": ["bugs"],
                                       "findings": []}]}, fh)
        return t, st

    def test_clean_run_is_valid(self):
        self.assertEqual(fp.run_validity(*self.files()), [])

    def test_permission_failures_are_invalid(self):
        base = [{"type": "user", "message": {"role": "user",
                                            "content": "/vibe-check:deep-review"}}]
        for text in ("Permission to use Bash has been denied because Claude Code "
                     "is running in don't ask mode.",
                     "<tool_use_error>File is in a directory that is denied by your "
                     "permission settings.</tool_use_error>",
                     "<tool_use_error>File is covered by a Read deny rule in your "
                     "settings</tool_use_error>"):
            with self.subTest(text=text):
                reasons = fp.run_validity(*self.files(base + [_tool_result(text)]))
                self.assertTrue(any(r.startswith("permission failure") for r in reasons),
                                reasons)
        viol = _tool_result("ok\n<sandbox_violations>\ndeny file-write-create /x\n"
                            "</sandbox_violations>", is_error=False)
        reasons = fp.run_validity(*self.files(base + [viol]))
        self.assertIn("permission failure: sandbox violation", reasons)

    def test_benign_errors_and_quoted_text_stay_valid(self):
        base = [{"type": "user", "message": {"role": "user",
                                            "content": "/vibe-check:deep-review"}}]
        events = base + [_tool_result("Exit code 1\ngrep: no match"),
                         _tool_result("docs say: Permission to use Bash has been denied",
                                      is_error=False)]
        self.assertEqual(fp.run_validity(*self.files(events)), [])

    def test_incomplete_or_unscored_reviews_are_invalid(self):
        cases = {
            "no review command": (lambda: self.files([_turn("hello")]),
                                  "incomplete review: no /vibe-check:deep-review"),
            "no state": (lambda: self.files(state=False),
                         "no scorer output: state missing"),
            "no passes": (lambda: self.files(state={"passes": []}),
                          "no scorer output: no pass in the state"),
            "pass without agents": (lambda: self.files(state={"passes": [{"pass_number": 1}]}),
                                    "incomplete review: the last pass ran no agents"),
        }
        for label, (make, want) in cases.items():
            with self.subTest(label=label):
                st = os.path.join(self.tmp, "state.json")
                if os.path.exists(st):
                    os.unlink(st)
                self.assertIn(want, fp.run_validity(*make()))
        self.assertIn("incomplete review: transcript empty or unreadable",
                      fp.run_validity(os.path.join(self.tmp, "absent.jsonl"),
                                      self.files()[1]))

    def test_write_validity_binds_hashes_and_never_overwrites(self):
        t, st = self.files()
        run = os.path.join(self.tmp, "case", "run-1")
        os.makedirs(run)
        rec = fp.write_validity(run, t, st)
        self.assertTrue(rec["valid"])
        self.assertEqual(rec["state_sha256"], freeze_common.sha256_file(st))
        self.assertEqual(rec["transcript_sha256"], freeze_common.sha256_file(t))
        with self.assertRaises(fp.FreezeError):
            fp.write_validity(run, t, st)

    def test_cli_exit_codes(self):
        t, st = self.files()
        run = os.path.join(self.tmp, "case", "run-1")
        os.makedirs(run)
        self.assertEqual(fp.main(["run-validity", "--run-dir", run,
                                  "--transcript", t, "--state", st]), 0)
        bad = os.path.join(self.tmp, "case", "run-2")
        os.makedirs(bad)
        os.unlink(st)
        self.assertEqual(fp.main(["run-validity", "--run-dir", bad,
                                  "--transcript", t, "--state", st]), 1)
        with open(os.path.join(bad, "validity.json"), encoding="utf-8") as fh:
            self.assertFalse(json.load(fh)["valid"])


class TestInvalidRunsNeverCount(_Tmp):
    M = "a" * 64

    def pre(self):
        return fp.Prerequisites(engineering={}, lineage={
            "resolved": True, "previous_manifest_id": None,
            "previous_candidate_sha": None, "inheritance": {},
            "required_reruns": []}, seal_order={"required": False, "ok": True,
                                                "proof_path": None}, problems=[])

    def manifest(self):
        return {"manifest_id": self.M, "candidate_sha": CAND}

    def test_b3_run_without_or_with_failed_validity_is_ineligible(self):
        ok_dir = write_b3_run(self.tmp, "should-quiet-1", 1, self.M)
        self.assertEqual(fp.eligible(fp.read_record(ok_dir), self.manifest(), self.pre()),
                         (True, "manifest match"))
        none_dir = write_b3_run(self.tmp, "should-quiet-1", 2, self.M, valid=None)
        self.assertEqual(fp.eligible(fp.read_record(none_dir), self.manifest(), self.pre()),
                         (False, "invalid run: no validity record"))
        bad_dir = write_b3_run(self.tmp, "should-quiet-1", 3, self.M, valid=False)
        self.assertEqual(fp.eligible(fp.read_record(bad_dir), self.manifest(), self.pre()),
                         (False, "invalid run: permission failure: Bash"))

    def test_b3_validity_must_match_the_archived_state(self):
        d = write_b3_run(self.tmp, "should-quiet-1", 1, self.M)
        with open(os.path.join(d, "state.json"), "w", encoding="utf-8") as fh:
            fh.write('{"passes": []}')
        self.assertEqual(fp.eligible(fp.read_record(d), self.manifest(), self.pre()),
                         (False, "invalid run: validity record does not match state.json"))

    def test_holdout_invalid_run_is_ineligible(self):
        d = write_holdout_run(self.tmp, "H-00000004", 1, self.M, valid=False)
        self.assertEqual(fp.eligible(fp.read_record(d), self.manifest(), self.pre()),
                         (False, "invalid run: no scorer output"))
        d = write_holdout_run(self.tmp, "H-00000004", 2, self.M, valid=None)
        self.assertEqual(fp.eligible(fp.read_record(d), self.manifest(), self.pre()),
                         (False, "invalid run: no validity record"))

    def test_invalid_quiet_run_leaves_its_slot_missing(self):
        """An invalid quiet-case run is never a QUIET verdict: the slot is
        missing and the gate is UNMET."""
        root = os.path.join(self.tmp, "runs")
        for d in fp.B3_DIFFS:
            for n in fp.RUN_NUMBERS:
                write_b3_run(root, d, n, self.M,
                             valid=not (d == "should-quiet-1" and n == 1))
        res = fp.gate_status("b3x3", fp_walk(root), self.manifest(), self.pre(),
                             verdicts=b3_verdicts())
        self.assertEqual(res["status"], "UNMET")
        self.assertIn(("should-quiet-1", 1), res["missing"])
        self.assertTrue(any("invalid run" in i["reason"] for i in res["ineligible"]))


def fp_walk(root):
    out = []
    for case in sorted(os.listdir(root)):
        for name in sorted(os.listdir(os.path.join(root, case))):
            out.append(fp.read_record(os.path.join(root, case, name)))
    return out


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

    def test_retune_evidence_rejects_empty_retired_list(self):
        """A retune retires the cases that guided the repair; a proof that
        retires none proves nothing about which slots were replaced."""
        ok, reasons = self.check(self.sr.proof(retired_case_ids=[]))
        self.assertFalse(ok)
        self.assertEqual(reasons, ["retired case ids are empty"])

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
# Eligibility and slot-based gate status (first-series manifest, no git)
# --------------------------------------------------------------------------- #

def b3_verdicts(fired=(), missed=()):
    out = {}
    for d in fp.B3_DIFFS:
        for n in fp.RUN_NUMBERS:
            key = "%s/run-%d" % (d, n)
            if d in fp.B3_CATCH_DIFFS:
                out[key] = "MISS" if key in missed else "CATCH"
            else:
                out[key] = "FIRED" if key in fired else "QUIET"
    return out


def holdout_verdicts(overrides=None):
    out = {}
    for cid, role in ROSTER["cases"].items():
        for n in fp.RUN_NUMBERS:
            out["%s/run-%d" % (cid, n)] = "CATCH" if role == "catch" else "QUIET"
    out.update(overrides or {})
    return out


class _GateBase(_Tmp):
    def setUp(self):
        super().setUp()
        self.m = make_manifest(CAND)
        self.mid = self.m["manifest_id"]
        self.ev = engineering_evidence_dir(os.path.join(self.tmp, "evidence"), CAND)
        self.runs = os.path.join(self.tmp, "runs")

    def pre(self, manifest=None, ev=None):
        return fp.prerequisites_for(manifest or self.m, "/nonexistent-repo",
                                    ev or self.ev, self.tmp)

    def b3_set(self, skip=()):
        out = []
        for d in fp.B3_DIFFS:
            for n in fp.RUN_NUMBERS:
                if (d, n) not in skip:
                    out.append(write_b3_run(self.runs, d, n, self.mid))
        return out

    def workflow_set(self, skip=(), verdict="COMPLETE"):
        out = []
        for slot in sorted(fp.GATE_SLOTS["workflow"](ROSTER)):
            if slot in skip:
                continue
            case, mode, kind = slot
            if kind == "clean":
                out.append(write_harness_run(self.runs, "clean-" + mode, "run-1",
                                             self.mid, mode=mode, kind="clean",
                                             case_id="triggarr-autoescape",
                                             verdict=verdict))
            else:
                out.append(write_harness_run(self.runs, "%s-%s" % (case, mode), "run-1",
                                             self.mid, mode=mode, case_id=case,
                                             verdict=verdict))
        return out

    def holdout_set(self):
        return [write_holdout_run(self.runs, cid, n, self.mid)
                for cid in ROSTER["cases"] for n in fp.RUN_NUMBERS]

    def status(self, gate, dirs, pre=None, **kw):
        recs = [fp.read_record(d) for d in dirs]
        return fp.gate_status(gate, recs, self.m, pre or self.pre(), **kw)


class TestGateStatus(_GateBase):
    def test_full_sets_met(self):
        self.assertEqual(self.status("b3x3", self.b3_set(),
                                     verdicts=b3_verdicts())["status"], "MET")
        self.assertEqual(self.status("workflow", self.workflow_set(),
                                     roster=ROSTER)["status"], "MET")
        self.assertEqual(self.status("holdoutx3", self.holdout_set(), roster=ROSTER,
                                     verdicts=holdout_verdicts())["status"], "MET")

    def test_missing_slot_not_filled_by_duplicate(self):
        dirs = [write_harness_run(self.runs, "triggarr-autoescape", "run-%d" % i,
                                  self.mid, case_id="triggarr-autoescape")
                for i in range(1, 19)]
        res = self.status("workflow", dirs, roster=ROSTER)
        self.assertEqual(res["status"], "UNMET")
        self.assertEqual(len(res["missing"]), 17)
        self.assertEqual(len(res["duplicates"]), 1)
        self.assertEqual(res["duplicates"][0]["slot"],
                         ("triggarr-autoescape", "default", "preservation"))
        self.assertEqual(len(res["duplicates"][0]["runs"]), 18)

    def test_duplicate_slot_unmet(self):
        dirs = self.workflow_set()
        dirs.append(write_harness_run(self.runs, "triggarr-autoescape-default", "run-2",
                                      self.mid, case_id="triggarr-autoescape"))
        res = self.status("workflow", dirs, roster=ROSTER)
        self.assertEqual(res["status"], "UNMET")
        self.assertEqual([d["slot"] for d in res["duplicates"]],
                         [("triggarr-autoescape", "default", "preservation")])

    def test_extra_record_never_counts(self):
        dirs = self.b3_set()
        extra4 = write_b3_run(self.runs, "should-quiet-1", 4, self.mid)
        unknown = write_b3_run(self.runs, "not-a-diff", 1, self.mid)
        res = self.status("b3x3", dirs + [extra4, unknown], verdicts=b3_verdicts())
        self.assertEqual(res["status"], "MET")
        self.assertEqual(sorted(e["run"] for e in res["extras"]),
                         ["not-a-diff/run-1", "should-quiet-1/run-4"])
        shutil.rmtree(dirs[0])
        res = self.status("b3x3", dirs[1:] + [extra4, unknown], verdicts=b3_verdicts())
        self.assertEqual(res["status"], "UNMET")
        self.assertEqual(res["missing"], [(fp.B3_DIFFS[0], 1)])

    def test_catch_slot_miss_unmet(self):
        res = self.status("b3x3", self.b3_set(),
                          verdicts=b3_verdicts(missed={"triggarr-autoescape/run-2"}))
        self.assertEqual(res["status"], "UNMET")
        self.assertIn("catch slot missed: triggarr-autoescape/run-2",
                      res["rule"]["reasons"])

    def test_quiet_fp_over_bar_unmet(self):
        dirs = self.b3_set()
        three = {"should-quiet-1/run-1", "should-quiet-2/run-2", "should-quiet-3/run-3"}
        self.assertEqual(self.status("b3x3", dirs, verdicts=b3_verdicts(
            fired=three))["status"], "MET")
        self.assertEqual(self.status("b3x3", dirs, verdicts=b3_verdicts(
            fired=three | {"should-quiet-7/run-1", "should-quiet-7/run-2"}))["status"],
            "MET")
        res = self.status("b3x3", dirs, verdicts=b3_verdicts(
            fired=three | {"should-quiet-4/run-1"}))
        self.assertEqual(res["status"], "UNMET")
        self.assertIn("false alarms 4 over the bar of 3", res["rule"]["reasons"])

    def test_holdout_per_case(self):
        dirs = self.holdout_set()
        res = self.status("holdoutx3", dirs, roster=ROSTER, verdicts=holdout_verdicts(
            {"H-00000001/run-1": "MISS", "H-00000001/run-2": "MISS"}))
        self.assertEqual(res["status"], "UNMET")
        self.assertIn("holdout catch case H-00000001 caught 1/3", res["rule"]["reasons"])
        res = self.status("holdoutx3", dirs, roster=ROSTER, verdicts=holdout_verdicts(
            {"H-00000004/run-1": "FIRED", "H-00000004/run-3": "FIRED"}))
        self.assertEqual(res["status"], "UNMET")
        self.assertIn("holdout quiet case H-00000004 fired 2/3", res["rule"]["reasons"])
        # one miss per catch case and one fire per quiet case stays within the bars
        spread = {"H-0000000%d/run-1" % i: "MISS" for i in (1, 2, 3)}
        spread.update({"H-0000000%d/run-2" % i: "FIRED" for i in (4, 5, 6)})
        self.assertEqual(self.status("holdoutx3", dirs, roster=ROSTER,
                                     verdicts=holdout_verdicts(spread))["status"], "MET")

    def test_roster_and_verdicts_missing_unmet(self):
        res = self.status("holdoutx3", self.holdout_set(), verdicts=holdout_verdicts())
        self.assertEqual(res["status"], "UNMET")
        self.assertIn("roster missing", res["rule"]["reasons"])
        res = self.status("b3x3", self.b3_set())
        self.assertEqual(res["status"], "UNMET")
        self.assertIn("verdicts missing", res["rule"]["reasons"])

    def test_waiver_never_met(self):
        slot = ("triggarr-autoescape", "gsd", "preservation")
        dirs = self.workflow_set(skip={slot})
        recs = [dict(fp.read_record(d), waiver={"approved_by": "owner"}) for d in dirs]
        res = fp.gate_status("workflow", recs, self.m, self.pre(), roster=ROSTER)
        self.assertEqual(res["status"], "UNMET")
        self.assertEqual(res["missing"], [slot])
        import inspect
        self.assertNotIn("waiver", inspect.signature(fp.gate_status).parameters)

    def test_failed_never_satisfies(self):
        slot = ("triggarr-autoescape", "gsd", "preservation")
        dirs = self.workflow_set(skip={slot})
        dirs.append(write_harness_run(self.runs, "triggarr-autoescape-gsd", "run-1",
                                      self.mid, mode="gsd", case_id="triggarr-autoescape",
                                      verdict="FAILED"))
        res = self.status("workflow", dirs, roster=ROSTER)
        self.assertEqual(res["status"], "UNMET")
        self.assertEqual(res["missing"], [slot])
        self.assertEqual(res["ineligible"], [{"run": "triggarr-autoescape-gsd/run-1",
                                              "reason": "verdict FAILED"}])
        failed = write_b3_run(self.runs, "should-quiet-1", 1, self.mid,
                              dirname="run-1.failed-x")
        ok, reason = fp.eligible(fp.read_record(failed), self.m, self.pre())
        self.assertEqual((ok, reason), (False, "verdict FAILED"))

    def test_superseded_ineligible(self):
        dirs = self.workflow_set()
        old = write_harness_run(self.runs, "triggarr-autoescape-default", "run-0",
                                self.mid, case_id="triggarr-autoescape")
        with open(os.path.join(old, "SUPERSEDED"), "w") as fh:
            fh.write("triggarr-autoescape-default/run-1\n")
        res = self.status("workflow", dirs + [old], roster=ROSTER)
        self.assertEqual(res["status"], "MET")
        self.assertEqual(res["duplicates"], [])
        self.assertEqual(res["ineligible"], [{
            "run": "triggarr-autoescape-default/run-0",
            "reason": "superseded by triggarr-autoescape-default/run-1"}])

    def test_manifest_mismatch_and_stale_candidate(self):
        d = write_b3_run(self.runs, "should-quiet-1", 1, "b" * 64)
        ok, reason = fp.eligible(fp.read_record(d), self.m, self.pre())
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("manifest mismatch (bbbbbbbbbbbb vs active"))
        d = write_b3_run(self.runs, "should-quiet-1", 2, self.mid, candidate_sha=OTHER)
        ok, reason = fp.eligible(fp.read_record(d), self.m, self.pre())
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("candidate mismatch"), reason)
        d = write_b3_run(self.runs, "should-quiet-1", 3, self.mid, stamps=False)
        ok, reason = fp.eligible(fp.read_record(d), self.m, self.pre())
        self.assertEqual(reason, "identity check not recorded (record lacks manifest_id)")

    def test_reporting_only(self):
        pm = fp.load_path_map()
        out = fp.classify(["README.md", "docs/design/freeze-v2.12/evidence/x.json",
                           "plugins/vibe-check/README.md"], pm)
        union = set().union(*out.values())
        self.assertEqual(union, {"reporting"})
        self.assertEqual(fp.required(union), {})
        # The covered plugin README changes the plugin tree: a new manifest is
        # needed, and every measurement gate inherits across it.
        old = make_manifest(CAND)
        new = make_manifest(OTHER, previous=old, **{
            "plugin.files": dict(old["plugin"]["files"],
                                 **{"README.md": {"sha256": "5" * 64, "mode": "100644"}}),
            "plugin.tree_sha256": "6" * 64})
        readme = {"plugins/vibe-check/README.md": {"reporting"}}
        for gate in ("b3x3", "holdoutx3", "workflow"):
            self.assertEqual(fp.inherit(old, new, gate, readme), (True, "inheritable"))
        # A runtime file differing without a reporting classification refuses.
        agent = make_manifest(OTHER, previous=old, **{
            "plugin.files": dict(old["plugin"]["files"],
                                 **{"agents/a.md": {"sha256": "5" * 64, "mode": "100644"}}),
            "plugin.tree_sha256": "6" * 64})
        self.assertEqual(fp.inherit(old, agent, "b3x3", readme),
                         (False, "gate field differs: plugin.tree_sha256"))


class TestPrerequisites(_GateBase):
    def test_engineering_record_eligible_by_candidate_sha_without_manifest_id(self):
        pre = self.pre()
        self.assertEqual(pre["problems"], [])
        for name in fp.ENGINEERING_RECORD_FILES:
            rec = fp.read_record(os.path.join(self.ev, name))
            self.assertIsNone(rec["manifest_id"])
            self.assertEqual(fp.eligible(rec, self.m, pre), (True, "candidate-bound"))

    def test_engineering_gate_met_from_real_shapes(self):
        recs = [fp.read_record(os.path.join(self.ev, n)) for n in fp.ENGINEERING_RECORD_FILES]
        res = fp.gate_status("engineering", recs, self.m, self.pre())
        self.assertEqual(res["status"], "MET", res)
        self.assertEqual(sorted(res["slots"]), [("deep-review",), ("security",), ("tests",)])
        self.assertEqual((res["missing"], res["duplicates"]), ([], []))

    def test_engineering_record_wrong_candidate_ineligible(self):
        ev = engineering_evidence_dir(os.path.join(self.tmp, "ev2"), OTHER)
        pre = self.pre(ev=ev)
        rec = fp.read_record(os.path.join(ev, "test-gate.json"))
        ok, reason = fp.eligible(rec, self.m, pre)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("candidate mismatch"))
        self.assertIn("prerequisite not candidate-bound: tests (%s vs %s)"
                      % (OTHER[:12], CAND[:12]), pre["problems"])
        recs = [fp.read_record(os.path.join(ev, n)) for n in fp.ENGINEERING_RECORD_FILES]
        self.assertEqual(fp.gate_status("engineering", recs, self.m, pre)["status"],
                         "UNMET")

    def test_engineering_prerequisite_and_slot_views_agree(self):
        cases = {"bound-pass": (CAND, "pass"), "unbound": (OTHER, "pass"),
                 "fail": (CAND, "fail"), "absent": None}
        for label, spec in cases.items():
            ev = os.path.join(self.tmp, "agree-" + label)
            if spec is None:
                os.makedirs(ev)
            else:
                engineering_evidence_dir(ev, spec[0], outcome=spec[1])
            pre = self.pre(ev=ev)
            for fname, name in fp.ENGINEERING_RECORD_FILES.items():
                v = pre["engineering"][name]
                pre_ok = v["present"] and v["candidate_bound"] and v["passed"]
                path = os.path.join(ev, fname)
                slot_ok = os.path.isfile(path) and fp.eligible(
                    fp.read_record(path), self.m, pre)[0]
                self.assertEqual(pre_ok, slot_ok, (label, name))
                self.assertEqual(pre_ok, label == "bound-pass", (label, name))

    def test_unmet_without_engineering_prerequisite(self):
        dirs = self.workflow_set()
        self.assertEqual(self.status("workflow", dirs, roster=ROSTER)["status"], "MET")
        for fname, name in fp.ENGINEERING_RECORD_FILES.items():
            ev = engineering_evidence_dir(os.path.join(self.tmp, "ev-" + name), CAND)
            os.remove(os.path.join(ev, fname))
            res = self.status("workflow", dirs, pre=self.pre(ev=ev), roster=ROSTER)
            self.assertEqual(res["status"], "UNMET")
            self.assertEqual(res["prerequisites"], ["prerequisite missing: %s" % name])
            self.assertEqual(res["missing"], [])

    def test_unmet_prerequisite_not_candidate_bound(self):
        dirs = self.workflow_set()
        # A well-formed record for another candidate: its own guard line names
        # that candidate, so only the candidate binding refuses it.
        ev = engineering_evidence_dir(os.path.join(self.tmp, "evx"), CAND, overrides={
            "test-gate.json": {"candidate_sha": OTHER, "candidate_guard": (
                "CANDIDATE OK candidate=%s head=%s descendant_commits=1 "
                "(reporting-only)" % (OTHER, "e" * 40))}})
        res = self.status("workflow", dirs, pre=self.pre(ev=ev), roster=ROSTER)
        self.assertEqual(res["status"], "UNMET")
        self.assertEqual(res["prerequisites"], [
            "prerequisite not candidate-bound: tests (%s vs %s)" % (OTHER[:12], CAND[:12])])

    def test_unmet_prerequisite_failed(self):
        dirs = self.workflow_set()
        ev = engineering_evidence_dir(os.path.join(self.tmp, "evf"), CAND, overrides={
            "security-gate.json": {"outcome": "fail"}})
        res = self.status("workflow", dirs, pre=self.pre(ev=ev), roster=ROSTER)
        self.assertEqual(res["status"], "UNMET")
        self.assertEqual(res["prerequisites"], ["prerequisite failed: security"])

    def test_first_series_manifest_owes_only_engineering(self):
        pre = self.pre()
        self.assertFalse(pre["seal_order"]["required"])
        self.assertEqual(pre["lineage"]["required_reruns"], set())
        self.assertTrue(pre["lineage"]["resolved"])
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty)
        self.assertEqual(self.pre(ev=empty)["problems"],
                         ["prerequisite missing: tests", "prerequisite missing: security",
                          "prerequisite missing: deep-review"])

    def test_lineage_unresolved_unmet(self):
        prev = make_manifest(OTHER)
        m2 = make_manifest(CAND, previous=prev)
        pre = self.pre(manifest=m2)
        self.assertIn("lineage unresolved: %s" % prev["manifest_id"][:12], pre["problems"])
        self.assertTrue(pre["seal_order"]["required"])
        self.assertEqual(pre["lineage"]["required_reruns"], set(fp.GATES))
        self.m = m2
        res = self.status("workflow", self.workflow_set(), pre=pre, roster=ROSTER)
        self.assertEqual(res["status"], "UNMET")

    def test_eligible_requires_prerequisites_argument(self):
        d = write_b3_run(self.runs, "should-quiet-1", 1, self.mid)
        with self.assertRaises(TypeError):
            fp.eligible(fp.read_record(d), self.m)  # pylint: disable=no-value-for-parameter
        with self.assertRaises(TypeError):
            fp.gate_status("b3x3", [], self.m)  # pylint: disable=no-value-for-parameter


# --------------------------------------------------------------------------- #
# Seal order enforced end to end on the git fixture
# --------------------------------------------------------------------------- #

class TestSealEndToEnd(_SealBase):
    def setUp(self):
        super().setUp()
        self.series = os.path.join(self.tmp, "series")
        os.makedirs(self.series)
        self.m1 = make_manifest(self.sr.P)
        with open(os.path.join(self.series, "FREEZE-MANIFEST-1.json"), "w") as fh:
            json.dump(self.m1, fh)
        self.runs = os.path.join(self.tmp, "runs")

    def setup_active(self, active):
        m2 = make_manifest(active, previous=self.m1)
        ev = engineering_evidence_dir(os.path.join(self.tmp, "ev-" + active[:8]), active)
        return m2, ev

    def pre(self, m2, ev):
        return fp.prerequisites_for(m2, self.sr.repo, ev, self.series)

    def b3_records(self, manifest):
        return [fp.read_record(write_b3_run(self.runs, d, n, manifest["manifest_id"],
                                            candidate_sha=manifest["candidate_sha"]))
                for d in fp.B3_DIFFS for n in fp.RUN_NUMBERS]

    def write_proof(self, path, **edits):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.sr.proof(**edits), fh)

    def test_detection_records_ineligible_without_seal_order(self):
        m2, ev = self.setup_active(self.sr.A)
        recs = self.b3_records(m2)
        pre = self.pre(m2, ev)
        proof_path = fp.seal_order_proof_path(ev, m2)
        self.assertTrue(pre["seal_order"]["required"])
        self.assertEqual(pre["seal_order"]["first_repair_commit"], self.sr.R)
        for rec in recs:
            self.assertEqual(fp.eligible(rec, m2, pre),
                             (False, "seal order not proven: " + proof_path))
        res = fp.gate_status("b3x3", recs, m2, pre, verdicts=b3_verdicts())
        self.assertEqual(res["status"], "UNMET")
        self.assertTrue(any(p.startswith("seal order not proven: ")
                            for p in res["prerequisites"]))
        # the valid sequence: previous -> failed -> removal -> replacement -> repair
        fp.write_seal_order_proof(proof_path, self.sr.repo, self.sr.P, self.sr.A,
                                  fp.MAP_SELF_PATH, self.sr.S1, ["H-00000001"],
                                  ["H-0000000a"])
        pre = self.pre(m2, ev)
        self.assertEqual(pre["problems"], [])
        res = fp.gate_status("b3x3", recs, m2, pre, verdicts=b3_verdicts())
        self.assertEqual(res["status"], "MET", res)
        for seal, reason in ((self.sr.S0, "replacement seal predates the previous candidate"),
                             (self.sr.RM, "replacement seal commit does not add SEAL.json")):
            os.remove(proof_path)
            self.write_proof(proof_path, replacement_seal_commit=seal)
            pre = self.pre(m2, ev)
            self.assertIn("seal order not proven: %s (%s)" % (proof_path, reason),
                          pre["problems"])
            self.assertEqual(fp.gate_status("b3x3", recs, m2, pre,
                                            verdicts=b3_verdicts())["status"], "UNMET")
        # a replacement sealed after the repair
        m3, ev3 = self.setup_active(self.sr.A2)
        late_path = fp.seal_order_proof_path(ev3, m3)
        self.write_proof(late_path, replacement_seal_commit=self.sr.S2)
        pre = self.pre(m3, ev3)
        self.assertIn("seal order not proven: %s (replacement sealed after the repair)"
                      % late_path, pre["problems"])
        self.assertEqual(fp.gate_status("b3x3", self.b3_records(m3), m3, pre,
                                        verdicts=b3_verdicts())["status"], "UNMET")

    def test_workflow_gate_does_not_need_seal_order(self):
        m2, ev = self.setup_active(self.sr.A)
        pre = self.pre(m2, ev)
        self.assertEqual(fp._gate_prerequisite_problems("workflow", pre), [])
        self.assertTrue(fp._gate_prerequisite_problems("holdoutx3", pre))

    def test_rerun_required_refuses_inherited(self):
        m2, ev = self.setup_active(self.sr.A)
        fp.write_seal_order_proof(fp.seal_order_proof_path(ev, m2), self.sr.repo,
                                  self.sr.P, self.sr.A, fp.MAP_SELF_PATH, self.sr.S1,
                                  ["H-00000001"], ["H-0000000a"])
        pre = self.pre(m2, ev)
        self.assertIn("b3x3", pre["lineage"]["required_reruns"])
        pre["lineage"]["inheritance"]["b3x3"] = (True, "inheritable")
        old = fp.read_record(write_b3_run(self.runs, "should-quiet-1", 1,
                                          self.m1["manifest_id"], candidate_sha=self.sr.P))
        self.assertEqual(fp.eligible(old, m2, pre),
                         (False, "rerun required for b3x3: inherited result refused"))

    def test_validated_inheritance_counts(self):
        m2, ev = self.setup_active(self.sr.A)
        pre = self.pre(m2, ev)
        pre["lineage"]["required_reruns"] = set()
        pre["lineage"]["inheritance"]["workflow"] = (True, "inheritable")
        old = fp.read_record(write_harness_run(self.runs, "triggarr-autoescape", "run-1",
                                               self.m1["manifest_id"],
                                               candidate_sha=self.sr.P))
        self.assertEqual(fp.eligible(old, m2, pre),
                         (True, "inherited from %s (validated)"
                          % self.m1["manifest_id"][:12]))
        self.assertFalse(fp.eligible(old, m2, pre, lineage={"workflow": "f" * 64})[0])
        pre["lineage"]["inheritance"]["workflow"] = (False, "gate field differs: models")
        self.assertTrue(fp.eligible(old, m2, pre)[1].startswith("manifest mismatch"))


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

    def test_mutant_a2_detection_fields_without_gateway_or_env(self):
        name = "test_detection_gates_bind_gateway_and_process_env"
        cover = "test_detection_gate_fields_cover_every_identity_class"
        self.assertTrue(self._passes(name, TestInherit))
        self.assertTrue(self._passes(cover, TestInherit))
        for drop in (fp.GATEWAY_FIELD, fp.PROCESS_ENV_FIELD):
            mutant = {g: tuple(f for f in fields if f != drop)
                      for g, fields in fp.GATE_FIELDS.items()}
            with self.subTest(drop=drop), \
                    mock.patch.object(fp, "GATE_FIELDS", mutant):
                self.assertFalse(self._passes(name, TestInherit))
                self.assertFalse(self._passes(cover, TestInherit))

    def test_mutant_b7_guard_prefix_only(self):
        name = "test_engineering_guard_must_name_the_records_candidate"
        self.assertTrue(self._passes(name, TestEngineeringRecords))
        with mock.patch.object(fp, "_guard_names_candidate",
                               lambda guard, sha: True):
            self.assertFalse(self._passes(name, TestEngineeringRecords))

    def test_mutant_bugs010_empty_retired_accepted(self):
        name = "test_retune_evidence_rejects_empty_retired_list"
        self.assertTrue(self._passes(name, TestSealOrder))
        real = fp._proof_problems

        def mutant(proof, *a):
            if isinstance(proof, dict) and proof.get("retired_case_ids") == []:
                proof = dict(proof, retired_case_ids=["H-0000000f"])
            return real(proof, *a)
        with mock.patch.object(fp, "_proof_problems", mutant):
            self.assertFalse(self._passes(name, TestSealOrder))

    def test_mutant_invalid_run_rule_removed(self):
        name = "test_b3_run_without_or_with_failed_validity_is_ineligible"
        self.assertTrue(self._passes(name, TestInvalidRunsNeverCount))
        with mock.patch.object(fp, "_validity_problem", lambda record: None):
            self.assertFalse(self._passes(name, TestInvalidRunsNeverCount))
        name = "test_permission_failures_are_invalid"
        self.assertTrue(self._passes(name, TestRunValidity))
        with mock.patch.object(fp, "PERMISSION_FAILURE_RES", ()):
            self.assertFalse(self._passes(name, TestRunValidity))

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

    def test_mutant_a_verdict_check_removed(self):
        name = "test_failed_never_satisfies"
        self.assertTrue(self._passes(name, TestGateStatus))
        with mock.patch.object(fp, "_verdict_problem", lambda r: None):
            self.assertFalse(self._passes(name, TestGateStatus))

    def test_mutant_c_superseded_check_removed(self):
        name = "test_superseded_ineligible"
        self.assertTrue(self._passes(name, TestGateStatus))
        with mock.patch.object(fp, "_superseded_problem", lambda r: None):
            self.assertFalse(self._passes(name, TestGateStatus))

    def test_mutant_e_count_instead_of_slots(self):
        name = "test_missing_slot_not_filled_by_duplicate"
        self.assertTrue(self._passes(name, TestGateStatus))

        def counted(slots, filled):
            recs = [r for rs in filled.values() for r in rs]
            if len(recs) >= len(slots):
                return [], [], {s: recs[0] for s in slots}
            return list(slots), [], {}
        with mock.patch.object(fp, "_coverage", counted):
            self.assertFalse(self._passes(name, TestGateStatus))

    def test_mutant_f_extras_admitted(self):
        name = "test_extra_record_never_counts"
        self.assertTrue(self._passes(name, TestGateStatus))
        real = fp._bucket

        def admit(gate, records, slots):
            filled, extras = real(gate, records, slots)
            free = [s for s in sorted(slots, key=str) if s not in filled]
            for rec in [r for r in records if fp._slot_key(gate, r["slot"]) not in slots]:
                if free:
                    filled[free.pop(0)] = [rec]
            return filled, []
        with mock.patch.object(fp, "_bucket", admit):
            self.assertFalse(self._passes(name, TestGateStatus))

    def test_mutant_g_holdout_aggregated(self):
        name = "test_holdout_per_case"
        self.assertTrue(self._passes(name, TestGateStatus))

        def aggregated(filled, verdicts, active, roster=None):
            vs = [verdicts.get(fp._verdict_key(s)) for s in filled]
            ok = vs.count("CATCH") >= 6 and vs.count("FIRED") <= 3
            return ok, [] if ok else ["aggregate bar"]
        with mock.patch.dict(fp.GATE_RULES, {"holdoutx3": aggregated}):
            self.assertFalse(self._passes(name, TestGateStatus))

    def test_mutant_h_gate_ignores_prerequisites(self):
        name = "test_unmet_without_engineering_prerequisite"
        self.assertTrue(self._passes(name, TestPrerequisites))
        with mock.patch.object(fp, "_gate_prerequisite_problems", lambda g, p: []):
            self.assertFalse(self._passes(name, TestPrerequisites))

    def test_mutant_i_eligible_ignores_seal_order(self):
        name = "test_detection_records_ineligible_without_seal_order"
        self.assertTrue(self._passes(name, TestSealEndToEnd))
        with mock.patch.object(fp, "_seal_problem", lambda r, p: None):
            self.assertFalse(self._passes(name, TestSealEndToEnd))

    def test_mutant_j_prerequisite_presence_only(self):
        name = "test_unmet_prerequisite_not_candidate_bound"
        self.assertTrue(self._passes(name, TestPrerequisites))

        def presence(path, active):
            present = os.path.isfile(path)
            return {"present": present, "candidate_bound": present, "passed": present,
                    "path": path, "reason": "present" if present else "absent"}
        with mock.patch.object(fp, "_engineering_prerequisite", presence):
            self.assertFalse(self._passes(name, TestPrerequisites))

    def test_mutant_k_eligible_ignores_required_reruns(self):
        name = "test_rerun_required_refuses_inherited"
        self.assertTrue(self._passes(name, TestSealEndToEnd))
        with mock.patch.object(fp, "_rerun_problem", lambda *a: None):
            self.assertFalse(self._passes(name, TestSealEndToEnd))

    def test_mutant_n_manifest_clause_on_engineering(self):
        names = ("test_engineering_record_eligible_by_candidate_sha_without_manifest_id",
                 "test_engineering_gate_met_from_real_shapes")
        for name in names:
            self.assertTrue(self._passes(name, TestPrerequisites))

        def by_manifest(record, active):
            if record.get("manifest_id") != active.get("manifest_id"):
                return False, "manifest mismatch"
            return fp.engineering_record_bound(record, active)
        with mock.patch.object(fp, "_eligible_engineering", by_manifest):
            for name in names:
                self.assertFalse(self._passes(name, TestPrerequisites))


if __name__ == "__main__":
    unittest.main()
