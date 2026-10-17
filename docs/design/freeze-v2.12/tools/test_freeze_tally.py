"""Tests for freeze_tally: every tally path goes through freeze_policy.eligible
with the active manifest's prerequisites."""

import ast
import contextlib
import io
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

import freeze_policy as fp  # noqa: E402
import freeze_tally as ft  # noqa: E402
import test_freeze_manifest as tfm  # noqa: E402
from test_freeze_policy import (CAND, OTHER, ROSTER, b3_verdicts,  # noqa: E402
                                engineering_evidence_dir, make_manifest,
                                write_b3_run, write_harness_run)


def _snapshot(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            with open(full, "rb") as fh:
                out.append((os.path.relpath(full, root), fh.read()))
    return out


class _TallyBase(unittest.TestCase):
    def setUp(self):
        self._tmpd = tempfile.TemporaryDirectory()
        self.tmp = self._tmpd.name
        self.m = make_manifest(CAND)
        self.mid = self.m["manifest_id"]
        self.manifest_path = os.path.join(self.tmp, "FREEZE-MANIFEST-1.json")
        with open(self.manifest_path, "w") as fh:
            json.dump(self.m, fh)
        self.ev = engineering_evidence_dir(os.path.join(self.tmp, "evidence"), CAND)
        self.runs = os.path.join(self.tmp, "runs")
        os.makedirs(self.runs)
        self.roster_path = self._json("roster.json", ROSTER)

    def tearDown(self):
        self._tmpd.cleanup()

    def _json(self, name, obj):
        path = os.path.join(self.tmp, name)
        with open(path, "w") as fh:
            json.dump(obj, fh)
        return path

    def run_cli(self, *argv, evidence=True):
        base = list(argv[:1])
        if argv and argv[0] != "bogus":
            base += ["--manifest", self.manifest_path, "--repo", tfm.REAL_REPO or self.tmp,
                     "--series-dir", self.tmp]
            if evidence and "--evidence-dir" not in argv:
                base += ["--evidence-dir", self.ev]
        base += list(argv[1:])
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = ft.main(base)
        return rc, out.getvalue(), err.getvalue()

    def planted_runs(self):
        """Two eligible runs, one FAILED, one stale manifest, one superseded."""
        write_harness_run(self.runs, "triggarr-autoescape", "run-1", self.mid,
                          case_id="triggarr-autoescape")
        write_harness_run(self.runs, "triggarr-autoescape", "run-2", self.mid,
                          mode="gsd", case_id="triggarr-autoescape")
        write_harness_run(self.runs, "triggarr-secret-in-logs", "run-1", self.mid,
                          case_id="triggarr-secret-in-logs", verdict="FAILED")
        write_harness_run(self.runs, "triggarr-session-rotation", "run-1", "b" * 64,
                          case_id="triggarr-session-rotation")
        sup = write_harness_run(self.runs, "triggarr-session-rotation", "run-2", self.mid,
                                mode="gsd", case_id="triggarr-session-rotation")
        with open(os.path.join(sup, "SUPERSEDED"), "w") as fh:
            fh.write("triggarr-session-rotation/run-3\n")

    def workflow_set(self, skip=()):
        for slot in sorted(fp.GATE_SLOTS["workflow"](ROSTER)):
            if slot in skip:
                continue
            case, mode, kind = slot
            if kind == "clean":
                write_harness_run(self.runs, "clean-" + mode, "run-1", self.mid,
                                  mode=mode, kind="clean", case_id="triggarr-autoescape")
            else:
                write_harness_run(self.runs, "%s-%s" % (case, mode), "run-1", self.mid,
                                  mode=mode, case_id=case)


class TestList(_TallyBase):
    def test_list_marks_eligibility(self):
        self.planted_runs()
        before = _snapshot(self.runs)
        rc, out, _ = self.run_cli("list", "--runs-root", self.runs)
        self.assertEqual(rc, 0)
        lines = out.splitlines()
        self.assertIn("triggarr-autoescape/run-1 eligible", lines)
        self.assertIn("triggarr-autoescape/run-2 eligible", lines)
        self.assertIn("triggarr-secret-in-logs/run-1 INELIGIBLE: verdict FAILED", lines)
        self.assertTrue(any(l.startswith("triggarr-session-rotation/run-1 INELIGIBLE: "
                                         "manifest mismatch") for l in lines))
        self.assertIn("triggarr-session-rotation/run-2 INELIGIBLE: superseded by "
                      "triggarr-session-rotation/run-3", lines)
        self.assertEqual(_snapshot(self.runs), before)

    def test_select_eligible(self):
        self.planted_runs()
        pre = fp.prerequisites_for(self.m, self.tmp, self.ev, self.tmp)
        keep, refused = ft.select_eligible(self.runs, self.m, pre)
        self.assertEqual(sorted(r["run"] for r in keep),
                         ["triggarr-autoescape/run-1", "triggarr-autoescape/run-2"])
        self.assertEqual(len(refused), 3)


class TestGate(_TallyBase):
    def test_gate_workflow_met(self):
        self.workflow_set()
        rc, out, _ = self.run_cli("gate", "--gate", "workflow", "--runs-root", self.runs,
                                  "--roster", self.roster_path)
        self.assertEqual((rc, out.splitlines()[0]), (0, "GATE workflow: MET"))

    def test_gate_unmet_on_missing_and_duplicate_slot(self):
        missing = ("third-organic-should-catch", "gsd", "preservation")
        self.workflow_set(skip={missing})
        write_harness_run(self.runs, "triggarr-secret-in-logs-default", "run-2", self.mid,
                          case_id="triggarr-secret-in-logs")
        self.planted_runs()
        rc, out, _ = self.run_cli("gate", "--gate", "workflow", "--runs-root", self.runs,
                                  "--roster", self.roster_path)
        self.assertEqual(rc, 1)
        self.assertEqual(out.splitlines()[0], "GATE workflow: UNMET")
        self.assertIn("missing slot: third-organic-should-catch/gsd/preservation", out)
        self.assertIn("duplicate slot: triggarr-secret-in-logs/default/preservation", out)
        self.assertIn("ineligible: triggarr-secret-in-logs/run-1 (verdict FAILED)", out)

    def test_gate_eighteen_repetitions_unmet(self):
        for i in range(1, 19):
            write_harness_run(self.runs, "triggarr-autoescape", "run-%d" % i, self.mid,
                              case_id="triggarr-autoescape")
        rc, out, _ = self.run_cli("gate", "--gate", "workflow", "--runs-root", self.runs,
                                  "--roster", self.roster_path)
        self.assertEqual(rc, 1)
        self.assertEqual(out.count("missing slot: "), 17)
        self.assertEqual(out.count("duplicate slot: "), 1)

    def test_gate_engineering_met_from_real_shapes(self):
        rc, out, _ = self.run_cli("gate", "--gate", "engineering", "--runs-root", self.ev,
                                  evidence=False)
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.splitlines()[0], "GATE engineering: MET")

    def test_gate_unmet_without_candidate_bound_prerequisites(self):
        ev = engineering_evidence_dir(os.path.join(self.tmp, "ev-other"), CAND, overrides={
            "test-gate.json": {"candidate_sha": OTHER}})
        rc, out, _ = self.run_cli("gate", "--gate", "engineering", "--runs-root", ev,
                                  evidence=False)
        self.assertEqual(rc, 1)
        self.assertEqual(out.splitlines()[0], "GATE engineering: UNMET")
        self.assertIn("prerequisite: prerequisite not candidate-bound: tests", out)

    def test_gate_roster_or_verdicts_missing_unmet(self):
        self.workflow_set()
        rc, out, _ = self.run_cli("gate", "--gate", "workflow", "--runs-root", self.runs)
        self.assertEqual(rc, 1)
        self.assertIn("rule: roster missing", out)
        b3 = os.path.join(self.tmp, "b3")
        for d in fp.B3_DIFFS:
            for n in fp.RUN_NUMBERS:
                write_b3_run(b3, d, n, self.mid)
        rc, out, _ = self.run_cli("gate", "--gate", "b3x3", "--runs-root", b3)
        self.assertEqual(rc, 1)
        self.assertIn("rule: verdicts missing", out)
        rc, out, _ = self.run_cli("gate", "--gate", "b3x3", "--runs-root", b3,
                                  "--verdicts", self._json("v.json", b3_verdicts()))
        self.assertEqual((rc, out.splitlines()[0]), (0, "GATE b3x3: MET"))

    def test_no_required_option(self):
        parser = ft.build_parser()
        sub = next(a for a in parser._actions if isinstance(a, ft.argparse._SubParsersAction))
        for name, p in sub.choices.items():
            opts = {o for a in p._actions for o in a.option_strings}
            self.assertNotIn("--required", opts, name)
            self.assertFalse(any("waiver" in o or "override" in o for o in opts), name)


@unittest.skipUnless(tfm.REAL_REPO, "needs score43 from the repo checkout")
class TestScore43Paths(_TallyBase):
    def b3_set(self):
        for d in fp.B3_DIFFS:
            for n in fp.RUN_NUMBERS:
                write_b3_run(self.runs, d, n, self.mid)

    def test_b3_aggregate_complete(self):
        self.b3_set()
        rc, out, _ = self.run_cli("b3-aggregate", "--runs-root", self.runs)
        self.assertEqual((rc, out.strip()), (0, "complete: 36 eligible runs"))

    def test_b3_aggregate_refuses_holes(self):
        self.b3_set()
        os.rename(os.path.join(self.runs, "should-quiet-1", "run-1"),
                  os.path.join(self.runs, "should-quiet-1", "run-1.failed-x"))
        shutil.rmtree(os.path.join(self.runs, "should-quiet-2", "run-2"))
        write_b3_run(self.runs, "should-quiet-2", 2, "b" * 64)
        before = _snapshot(self.runs)
        rc, out, _ = self.run_cli("b3-aggregate", "--runs-root", self.runs)
        self.assertEqual(rc, 1)
        self.assertIn("refused: holes present: should-quiet-1/run-1, should-quiet-2/run-2",
                      out)
        self.assertIn("ineligible: should-quiet-1/run-1.failed-x (verdict FAILED)", out)
        self.assertIn("ineligible: should-quiet-2/run-2 (manifest mismatch", out)
        self.assertEqual(_snapshot(self.runs), before)

    def test_b3_aggregate_refuses_runs_root_override(self):
        self.b3_set()
        rc, _, err = self.run_cli("b3-aggregate", "--runs-root", self.runs, "--",
                                  "--runs-root", self.tmp)
        self.assertEqual(rc, 2)
        self.assertIn("filtered view", err)

    def test_dev_tally_filters(self):
        write_b3_run(self.runs, "case-a", 1, self.mid)
        write_b3_run(self.runs, "case-a", 2, "b" * 64)
        rc, out, _ = self.run_cli("dev-tally", "--runs-root", self.runs)
        self.assertEqual(rc, 1)
        self.assertIn("runs: 1", out)
        self.assertIn("ineligible: case-a/run-2 (manifest mismatch", out)


class TestHarnessVerdicts(_TallyBase):
    def test_harness_verdicts_refuses_and_marks_duplicates(self):
        self.planted_runs()
        write_harness_run(self.runs, "triggarr-autoescape-dup", "run-1", self.mid,
                          case_id="triggarr-autoescape")
        rc, out, _ = self.run_cli("harness-verdicts", "--runs-root", self.runs,
                                  "--roster", self.roster_path)
        self.assertEqual(rc, 1)
        self.assertIn("duplicate slot: triggarr-autoescape/default/preservation", out)
        self.assertIn("INELIGIBLE: verdict FAILED", out)
        self.assertIn("refused:", out)

    def test_harness_verdicts_totals_when_clean(self):
        self.workflow_set()
        rc, out, _ = self.run_cli("harness-verdicts", "--runs-root", self.runs,
                                  "--roster", self.roster_path)
        self.assertEqual(rc, 0, out)
        self.assertIn("COMPLETE: 18", out)


    def test_harness_verdicts_requires_a_roster(self):
        """Without the roster no slot set exists to check completeness
        against, so it never totals (usage error, exit 2)."""
        self.workflow_set()
        rc, out, err = self.run_cli("harness-verdicts", "--runs-root", self.runs)
        self.assertEqual(rc, 2)
        self.assertNotIn("COMPLETE:", out)
        self.assertIn("--roster", err)

    def test_harness_verdicts_incomplete_roster_never_totals(self):
        missing = ("triggarr-autoescape", "gsd", "preservation")
        self.workflow_set(skip=(missing,))
        rc, out, _ = self.run_cli("harness-verdicts", "--runs-root", self.runs,
                                  "--roster", self.roster_path)
        self.assertEqual(rc, 1)
        self.assertIn("missing slot: triggarr-autoescape/gsd/preservation", out)
        self.assertNotIn("COMPLETE:", out)

    def test_harness_verdicts_extras_listed_never_counted(self):
        self.workflow_set()
        write_harness_run(self.runs, "unknown-case", "run-1", self.mid,
                          case_id="not-a-roster-case")
        rc, out, _ = self.run_cli("harness-verdicts", "--runs-root", self.runs,
                                  "--roster", self.roster_path)
        self.assertEqual(rc, 0, out)
        self.assertIn("extra: unknown-case/run-1 (not a mandatory slot)", out)
        self.assertIn("COMPLETE: 18", out)


class TestActiveManifestFallback(_TallyBase):
    """--manifest is optional on every subcommand: the active manifest of the
    series dir is used (the README's documented commands run as written)."""

    def run_no_manifest(self, *argv):
        base = [argv[0], "--repo", tfm.REAL_REPO or self.tmp,
                "--series-dir", self.tmp] + list(argv[1:])
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = ft.main(base)
        return rc, out.getvalue(), err.getvalue()

    def test_every_subcommand_accepts_no_manifest(self):
        parser = ft.build_parser()
        sub = next(a for a in parser._actions
                   if isinstance(a, ft.argparse._SubParsersAction))
        for name, p in sub.choices.items():
            with self.subTest(name=name):
                act = next(a for a in p._actions if "--manifest" in a.option_strings)
                self.assertFalse(act.required)

    def test_documented_engineering_gate_runs(self):
        rc, out, err = self.run_no_manifest("gate", "--gate", "engineering",
                                            "--runs-root", self.ev)
        self.assertEqual((rc, out.splitlines()[0]), (0, "GATE engineering: MET"),
                         out + err)

    def test_list_and_harness_verdicts_use_the_active_manifest(self):
        self.workflow_set()
        rc, out, _ = self.run_no_manifest("list", "--runs-root", self.runs,
                                          "--evidence-dir", self.ev)
        self.assertEqual(rc, 0)
        self.assertNotIn("INELIGIBLE", out)
        rc, out, _ = self.run_no_manifest("harness-verdicts", "--runs-root",
                                          self.runs, "--evidence-dir", self.ev,
                                          "--roster", self.roster_path)
        self.assertEqual(rc, 0, out)

    def test_no_manifest_in_series_is_a_usage_error(self):
        os.unlink(self.manifest_path)
        rc, _, err = self.run_no_manifest("gate", "--gate", "engineering",
                                          "--runs-root", self.ev)
        self.assertEqual(rc, 2)
        self.assertIn("no freeze manifest", err)


class TestCli(_TallyBase):
    def test_usage_errors_exit_2(self):
        self.assertEqual(self.run_cli("bogus")[0], 2)
        rc, _, _ = self.run_cli("gate", "--gate", "nope", "--runs-root", self.runs)
        self.assertEqual(rc, 2)
        rc, _, err = self.run_cli("gate", "--gate", "workflow", "--runs-root",
                                  os.path.join(self.tmp, "absent"))
        self.assertEqual(rc, 2)

    def test_tampered_manifest_refused(self):
        self.m["candidate_sha"] = OTHER
        with open(self.manifest_path, "w") as fh:
            json.dump(self.m, fh)
        rc, _, err = self.run_cli("list", "--runs-root", self.runs)
        self.assertEqual(rc, 2)
        self.assertIn("manifest_id does not match", err)


class TestImportSet(unittest.TestCase):
    def test_module_level_imports(self):
        with open(os.path.join(HERE, "freeze_tally.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module)
        allowed = {"argparse", "json", "os", "sys", "tempfile"}
        self.assertTrue(all(n in allowed or n.startswith("freeze_") for n in names), names)


class TestMutants(_TallyBase):
    def _passes(self, cls, name):
        result = unittest.TestResult()
        cls(name).run(result)
        return result.wasSuccessful()

    def test_mutant_select_eligible_bypass(self):
        name = "test_select_eligible"
        self.assertTrue(self._passes(TestList, name))
        with mock.patch.object(fp, "eligible", lambda *a, **k: (True, "bypassed")):
            self.assertFalse(self._passes(TestList, name))

    def test_mutant_gate_empty_prerequisites(self):
        name = "test_gate_unmet_without_candidate_bound_prerequisites"
        self.assertTrue(self._passes(TestGate, name))

        def empty(manifest, repo, evidence_dir, series_dir, path_map_rel=None):
            return fp.Prerequisites(
                engineering={}, problems=[],
                lineage={"previous_manifest_id": None, "previous_candidate_sha": None,
                         "resolved": True, "changed_cats": {}, "required_reruns": set(),
                         "inheritance": {}},
                seal_order={"required": False, "proof_path": "", "ok": True,
                            "reasons": [], "first_repair_commit": None})
        with mock.patch.object(fp, "prerequisites_for", empty):
            self.assertFalse(self._passes(TestGate, name))


if __name__ == "__main__":
    unittest.main()
