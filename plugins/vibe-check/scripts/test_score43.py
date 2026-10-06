"""Tests for score43.py — the Phase-43 scorer-of-record worksheet helper.

Every lock carries a demonstrated failure: holes and extras refuse, the
verdict follows the corrected cohort and never the sealed literal (both
directions), the exclusion is proven live by monkeypatching it away, the catch
arm is proven to come from the hand map, bands are proven to be read from
state, and the retune gate is proven to fail on each planted violation in both
its full and its pre-run form.
"""

import ast
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import score43  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
SCORE43_PY = os.path.join(HERE, "score43.py")
QUIET = [d for d in score43.DIFFS if score43.ROLE[d] == "quiet"]
CATCH = [d for d in score43.DIFFS if score43.ROLE[d] == "catch"]

# Six counted quiet diffs fire 8 of 18; should-quiet-7 fires 3 of 3.
FIRE_8_OF_18 = {"should-quiet-1": [True, True, True], "should-quiet-2": [True, True, True],
                "should-quiet-3": [True, True, False], "should-quiet-7": [True, True, True]}
# A one-diff MISS: only should-quiet-1 fails among the retune-eligible diffs.
ONE_DIFF_FIRST = {"should-quiet-1": [True, True, False], "should-quiet-7": [True, False, False]}

PINNED_AGGREGATE_FLAGS = {"--runs-root", "--label", "--fp-bar", "--sealed-fp-bar",
                          "--catch-bar", "--catch-verdicts", "--expected-diffs",
                          "--first-root", "--retune-root", "--failed-diffs",
                          "--denoms-blob", "--verdict-out", "--profile"}


def make_state(fired=False, band=None, codex="joined", rows=None):
    band = band or ("warning" if fired else "medium")
    findings = rows if rows is not None else [{
        "agent": "bugs", "file": "x.py", "line": 7, "band": band, "orchestrator_score": 70,
        "stable_hash": "ab" * 32, "attribution": ["bugs"], "title": "secret title text",
        "members": [{"agent": "bugs", "title": "secret title text"}]}]
    return {"passes": [{"findings": findings, "codex": {
        "status": codex, "reason": None if codex == "joined" else "timeout",
        "verdict": "approve" if codex == "joined" else None, "findings": 0}}]}


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)
    return path


def write_runs(root, fired=None, diffs=score43.DIFFS, runs=(1, 2, 3), codex=None):
    fired = fired or {}
    for d in diffs:
        for n in runs:
            flags = fired.get(d, [False, False, False])
            write_json(os.path.join(root, d, "run-%d" % n, "state.json"),
                       make_state(flags[n - 1] if n <= 3 else False,
                                  codex=(codex or {}).get((d, n), "joined")))
    return root


def catch_map(diffs=CATCH, miss=()):
    return {"%s/run-%d" % (d, n): ("MISS" if ("%s/run-%d" % (d, n)) in miss else "CATCH")
            for d in diffs for n in (1, 2, 3)}


def git(repo, *argv):
    proc = subprocess.run(["git", "-C", repo, *argv], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


class _TmpDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test-score43-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def p(self, *parts):
        return os.path.join(self.tmp, *parts)

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = score43.run(list(argv))
        return code, out.getvalue(), err.getvalue()

    def aggregate_first(self, root, cmap, out="VERDICT.json"):
        cv = write_json(self.p("cv-%s.json" % out), cmap)
        code, stdout, err = self.cli(
            "aggregate", "--runs-root", root, "--label", "first", "--fp-bar", "8",
            "--sealed-fp-bar", "9", "--catch-bar", "15", "--catch-verdicts", cv,
            "--verdict-out", self.p(out))
        return code, stdout, err, (json.load(open(self.p(out))) if code == 0 else None)

    def first_root(self, fired):
        root = write_runs(self.p("first"), fired)
        write_json(os.path.join(root, "CATCH-VERDICTS.json"), catch_map())
        return root


# --------------------------------------------------------------------------
# Ledger
# --------------------------------------------------------------------------

class TestLedger(_TmpDirCase):

    def test_complete_36(self):
        root = write_runs(self.p("first"))
        os.makedirs(os.path.join(root, "should-quiet-1", "run-2.failed-1790000000"))
        led = score43.completeness_ledger(root)
        self.assertTrue(led["complete"])
        self.assertEqual(led["diffs"]["should-quiet-1"]["excluded"], ["run-2.failed-1790000000"])
        self.assertEqual(self.cli("ledger", "--runs-root", root)[0], 0)

    def test_hole_names_the_run(self):
        root = write_runs(self.p("first"))
        shutil.rmtree(os.path.join(root, "should-quiet-4", "run-2"))
        led = score43.completeness_ledger(root)
        self.assertEqual(led["holes"], ["should-quiet-4/run-2"])
        code, _o, err = self.cli("ledger", "--runs-root", root)
        self.assertEqual(code, 1)
        self.assertIn("should-quiet-4/run-2", err)

    def test_run4_is_an_extra(self):
        root = write_runs(self.p("first"))
        write_json(os.path.join(root, "should-quiet-1", "run-4", "state.json"), make_state())
        code, _o, err = self.cli("ledger", "--runs-root", root)
        self.assertEqual(code, 1)
        self.assertIn("extras: should-quiet-1/run-4", err)

    def test_empty_expected_set_never_passes(self):
        with self.assertRaises(ValueError):
            score43.completeness_ledger(self.p("first"), [])
        with self.assertRaises(ValueError):
            score43.completeness_ledger(self.p("first"), ["not-a-diff"])

    def test_one_diff_retune_ledger(self):
        retune = write_runs(self.p("retune"), diffs=["should-quiet-1"])
        fd = write_json(self.p("FAILED-DIFFS.json"), ["should-quiet-1"])
        code, out, _e = self.cli("ledger", "--runs-root", retune, "--expected-diffs", fd)
        self.assertEqual(code, 0)
        self.assertIn("ledger complete: 1 diffs", out)
        # The first-pass rule (all 12) applied to the same root: 33 holes.
        led = score43.completeness_ledger(retune)
        self.assertEqual(len(led["holes"]), 33)
        self.assertEqual(self.cli("ledger", "--runs-root", retune)[0], 1)

    def test_retune_planted_extra_and_missing(self):
        fd = write_json(self.p("FAILED-DIFFS.json"), ["should-quiet-1"])
        for case in ("other-diff", "run-4", "missing"):
            with self.subTest(case=case):
                retune = self.p("retune-" + case)
                write_runs(retune, diffs=["should-quiet-1"])
                if case == "other-diff":
                    write_json(os.path.join(retune, "should-quiet-2", "run-1", "state.json"),
                               make_state())
                    want = "should-quiet-2/run-1"
                elif case == "run-4":
                    write_json(os.path.join(retune, "should-quiet-1", "run-4", "state.json"),
                               make_state())
                    want = "should-quiet-1/run-4"
                else:
                    shutil.rmtree(os.path.join(retune, "should-quiet-1", "run-2"))
                    want = "should-quiet-1/run-2"
                code, _o, err = self.cli("ledger", "--runs-root", retune,
                                         "--expected-diffs", fd)
                self.assertEqual(code, 1)
                self.assertIn(want, err)


# --------------------------------------------------------------------------
# Per-run verdicts
# --------------------------------------------------------------------------

class TestPerRun(_TmpDirCase):

    def test_fp_reads_band_from_state(self):
        st = make_state(fired=True)
        self.assertTrue(score43.fp_verdict(st)["fired"])
        st["passes"][-1]["findings"][0]["band"] = "medium"  # warning -> medium
        self.assertFalse(score43.fp_verdict(st)["fired"])

    def test_fp_output_has_no_titles(self):
        path = write_json(self.p("state.json"), make_state(fired=True))
        code, out, _e = self.cli("fp", "--state", path)
        self.assertEqual(code, 0)
        self.assertIn("| bugs | x.py | 7 | warning | 70 |", out)
        self.assertNotIn("secret title text", out)

    def test_catch_candidates_site_floor_and_titles(self):
        entry = {"site": {"file": "x.py", "lines": [[5, 9]]}, "floor": "warning"}
        rows = [
            {"agent": "bugs", "file": "x.py", "line": 7, "band": "warning",
             "orchestrator_score": 70, "stable_hash": "a" * 64, "title": "survivor t",
             "members": [{"agent": "security", "title": "member t"}]},
            {"agent": "bugs", "file": "x.py", "line": 8, "band": "medium",
             "orchestrator_score": 40, "stable_hash": "b" * 64, "title": "below floor"},
            {"agent": "bugs", "file": "y.py", "line": 7, "band": "critical",
             "orchestrator_score": 90, "stable_hash": "c" * 64, "title": "off site"},
        ]
        got = score43.catch_candidates(make_state(rows=rows), entry)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["survivor_title"], "survivor t")
        self.assertEqual(got[0]["member_titles"], [["security", "member t"]])
        self.assertEqual(got[0]["axis"], "")

    def test_catch_candidates_cli_uses_manifest_site(self):
        path = write_json(self.p("state.json"), make_state(rows=[
            {"agent": "security", "file": "triggarr/web/routes.py", "line": 45,
             "band": "warning", "orchestrator_score": 75, "stable_hash": "d" * 64,
             "title": "autoescape off", "members": []}]))
        code, out, _e = self.cli("catch-candidates", "--state", path,
                                 "--diff", "triggarr-autoescape")
        self.assertEqual(code, 0)
        self.assertIn("autoescape off", out)
        self.assertIn("candidates at site with band >= floor: 1", out)
        self.assertEqual(self.cli("catch-candidates", "--state", path,
                                  "--diff", "should-quiet-1")[0], 1)

    def test_codex_status_and_dropout(self):
        st = make_state(codex="skipped")
        st["passes"][-1]["findings"].append({"agent": "codex-adversarial", "band": "medium"})
        c = score43.codex_status(st)
        self.assertEqual((c["status"], c["reason"], c["codex_findings"], c["dropout"]),
                         ("skipped", "timeout", 1, True))
        self.assertFalse(score43.codex_status(make_state())["dropout"])
        path = write_json(self.p("state.json"), make_state(codex="skipped"))
        self.assertIn("codex.status=skipped reason=timeout", self.cli("codex-status",
                                                                        "--state", path)[1])


# --------------------------------------------------------------------------
# Aggregate
# --------------------------------------------------------------------------

class TestAggregate(_TmpDirCase):

    def test_corrected_cohort_decides_pass(self):
        root = write_runs(self.p("first"), FIRE_8_OF_18)
        code, out, err, v = self.aggregate_first(root, catch_map())
        self.assertEqual(code, 0, err)
        self.assertEqual(v["label"], "first")
        self.assertEqual(v["verdict"], "PASS")
        self.assertEqual((v["quiet_fired"], v["quiet_denominator"]), (8, 18))
        self.assertEqual(v["quiet_excluded"], ["should-quiet-7"])
        self.assertEqual(v["sealed_literal"], {"quiet_fired": 11, "quiet_denominator": 21,
                                               "fp_bar": 9, "would_be": "MISS"})
        self.assertEqual(v["excluded_runs"], {"should-quiet-7": [True, True, True]})
        self.assertEqual((v["catch_hit"], v["catch_denominator"]), (15, 15))
        self.assertEqual((v["fp_bar"], v["catch_bar"]), (8, 15))
        for k in ("dropouts", "snapshot_commit_note"):
            self.assertIn(k, v)
        self.assertIn("sealed literal (never deciding): 11/21 vs <= 9/21 -> would be MISS", out)
        self.assertNotIn("secret title text", out)

    def test_one_more_counted_fire_is_miss(self):
        fired = dict(FIRE_8_OF_18, **{"should-quiet-4": [True, False, False]})
        root = write_runs(self.p("first"), fired)
        _c, _o, _e, v = self.aggregate_first(root, catch_map())
        self.assertEqual((v["verdict"], v["quiet_fired"]), ("MISS", 9))

    def test_exclusion_mutation_turns_pass_into_miss(self):
        """With QUIET_EXCLUDED emptied (and the corrected-denominator pin moved
        to match), the same 8/18 PASS fixture is a MISS at 11/21 — the exclusion
        is what the PASS depends on. With only the exclusion emptied, the
        corrected-denominator pin refuses outright."""
        root = write_runs(self.p("first"), FIRE_8_OF_18)
        led = score43.completeness_ledger(root)
        fp = {k: score43.fp_verdict(s) for k, s in score43._load_states(led).items()}
        denoms = {"DENOM_CATCH_RUNS": 15, "DENOM_QUIET_RUNS": 21}
        self.assertEqual(score43.aggregate(led, fp, catch_map(), denoms)["verdict"], "PASS")
        real_ex, real_denom = score43.QUIET_EXCLUDED, score43.CORRECTED_QUIET_DENOM
        try:
            score43.QUIET_EXCLUDED = ()
            with self.assertRaises(score43.ScoreError):
                score43.aggregate(led, fp, catch_map(), denoms)
            score43.CORRECTED_QUIET_DENOM = 21
            v = score43.aggregate(led, fp, catch_map(), denoms)
        finally:
            score43.QUIET_EXCLUDED, score43.CORRECTED_QUIET_DENOM = real_ex, real_denom
        self.assertEqual((v["verdict"], v["quiet_fired"], v["quiet_denominator"]),
                         ("MISS", 11, 21))

    def test_fp_bar_9_with_10_fired_is_miss(self):
        fired = dict(FIRE_8_OF_18, **{"should-quiet-4": [True, True, False]})
        root = write_runs(self.p("first"), fired)
        led = score43.completeness_ledger(root)
        fp = {k: score43.fp_verdict(s) for k, s in score43._load_states(led).items()}
        v = score43.aggregate(led, fp, catch_map(),
                              {"DENOM_CATCH_RUNS": 15, "DENOM_QUIET_RUNS": 21}, fp_bar=9)
        self.assertEqual((v["quiet_fired"], v["verdict"]), (10, "MISS"))

    def test_band_change_in_state_changes_the_count(self):
        root = write_runs(self.p("first"), FIRE_8_OF_18)
        path = os.path.join(root, "should-quiet-1", "run-1", "state.json")
        st = json.load(open(path))
        st["passes"][-1]["findings"][0]["band"] = "medium"
        write_json(path, st)
        _c, _o, _e, v = self.aggregate_first(root, catch_map())
        self.assertEqual(v["quiet_fired"], 7)

    def test_hole_and_extra_refuse(self):
        root = write_runs(self.p("first"), FIRE_8_OF_18)
        shutil.rmtree(os.path.join(root, "triggarr-autoescape", "run-2"))
        code, _o, err, _v = self.aggregate_first(root, catch_map())
        self.assertEqual(code, 1)
        self.assertIn("holes present: triggarr-autoescape/run-2", err)
        self.assertFalse(os.path.exists(self.p("VERDICT.json")))
        root2 = write_runs(self.p("first2"), FIRE_8_OF_18)
        write_json(os.path.join(root2, "should-quiet-5", "run-4", "state.json"), make_state())
        code, _o, err, _v = self.aggregate_first(root2, catch_map())
        self.assertEqual(code, 1)
        self.assertIn("extras present: should-quiet-5/run-4", err)

    def test_catch_verdicts_must_be_exact(self):
        root = write_runs(self.p("first"), FIRE_8_OF_18)
        full = catch_map()
        fourteen = dict(full)
        fourteen.pop("triggarr-autoescape/run-1")
        sixteen = dict(full, **{"should-quiet-1/run-1": "CATCH"})
        unknown = dict(fourteen, **{"triggarr-autoescape/run-9": "CATCH"})
        lower = dict(full, **{"triggarr-autoescape/run-1": "catch"})
        for name, cmap in (("14", fourteen), ("16", sixteen), ("unknown", unknown),
                           ("lower", lower)):
            with self.subTest(case=name):
                code, _o, err, _v = self.aggregate_first(root, cmap, out=name + ".json")
                self.assertEqual(code, 1)
                self.assertTrue(err.startswith("catch-verdicts:"), err)

    def test_catch_axis_comes_from_the_hand_map(self):
        root = write_runs(self.p("first"), FIRE_8_OF_18)
        _c, _o, _e, v = self.aggregate_first(root, catch_map(miss=("triggarr-autoescape/run-3",)))
        self.assertEqual((v["catch_hit"], v["verdict"]), (14, "MISS"))

    def test_bars_are_pinned(self):
        root = write_runs(self.p("first"), FIRE_8_OF_18)
        cv = write_json(self.p("cv.json"), catch_map())
        code, _o, err = self.cli("aggregate", "--runs-root", root, "--label", "first",
                                 "--fp-bar", "9", "--sealed-fp-bar", "9", "--catch-bar", "15",
                                 "--catch-verdicts", cv, "--verdict-out", self.p("v.json"))
        self.assertEqual(code, 1)
        self.assertIn("bars must be", err)

    def test_sealed_denominators_from_blob(self):
        self.assertEqual(score43.load_denoms(),
                         {"DENOM_CATCH_RUNS": 15, "DENOM_QUIET_RUNS": 21})
        bad = "DENOM_CATCH_RUNS: 15\nDENOM_QUIET_RUNS: 24\n"
        with self.assertRaises(score43.ScoreError):
            score43.check_denoms(score43.parse_denoms(bad))
        with self.assertRaises(score43.ScoreError):
            score43.parse_denoms("DENOM_CATCH_RUNS: 15\n")

    def test_aggregate_help_lists_exactly_the_pinned_flags(self):
        code, out, _e = self.cli("aggregate", "--help")
        self.assertEqual(code, 0)
        flags = set(tok.rstrip(",]") for tok in out.replace("[", " ").split()
                    if tok.startswith("--"))
        self.assertEqual(flags - {"--help"}, PINNED_AGGREGATE_FLAGS)


# --------------------------------------------------------------------------
# Failed diffs, retune and combined
# --------------------------------------------------------------------------

class TestFailedDiffs(_TmpDirCase):

    def test_excluded_diff_is_stripped_and_strip_is_live(self):
        root = write_runs(self.p("first"), FIRE_8_OF_18)
        per_run = {}
        led = score43.completeness_ledger(root)
        for k, s in score43._load_states(led).items():
            per_run[k] = score43.fp_verdict(s)["fired"]
        self.assertEqual(score43.failed_diffs(per_run),
                         ["should-quiet-1", "should-quiet-2", "should-quiet-3"])
        real = score43.QUIET_EXCLUDED
        try:
            score43.QUIET_EXCLUDED = ()
            self.assertIn("should-quiet-7", score43.failed_diffs(per_run))
        finally:
            score43.QUIET_EXCLUDED = real

    def test_cli_writes_once_and_names_the_exclusion(self):
        root = self.first_root(ONE_DIFF_FIRST)
        out = self.p("FAILED-DIFFS.json")
        code, stdout, err = self.cli("failed-diffs", "--runs-root", root, "--out", out)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.load(open(out)), ["should-quiet-1"])
        self.assertIn("excluded from retune eligibility: should-quiet-7", stdout)
        code, _o, err = self.cli("failed-diffs", "--runs-root", root, "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("ALREADY WRITTEN", err)

    def test_catch_miss_is_a_failed_diff(self):
        root = write_runs(self.p("first"))
        write_json(os.path.join(root, "CATCH-VERDICTS.json"),
                   catch_map(miss=("triggarr-autoescape/run-2",)))
        code, _o, _e = self.cli("failed-diffs", "--runs-root", root, "--out", self.p("F.json"))
        self.assertEqual(code, 0)
        self.assertEqual(json.load(open(self.p("F.json"))), ["triggarr-autoescape"])


class _RepoCase(_TmpDirCase):
    """A temp git repo: S, then the first-pass verdict + FAILED-DIFFS commit F,
    then the retune commit S2."""

    FROZEN_TEXT = "frozen\n"
    BETWEEN_S_AND_F = {}

    def write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    def commit(self, msg):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", msg)
        return git(self.repo, "rev-parse", "HEAD")

    def setUp(self):
        super(_RepoCase, self).setUp()
        self.repo = self.p("repo")
        os.makedirs(self.repo)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "t@example.invalid")
        git(self.repo, "config", "user.name", "t")
        for f in score43.FROZEN_FILES:
            self.write(f, self.FROZEN_TEXT)
        self.write("plugins/vibe-check/agents/bugs.md", "# bugs\n")
        self.S = self.commit("S")
        if self.BETWEEN_S_AND_F:
            for rel, text in self.BETWEEN_S_AND_F.items():
                self.write(rel, text)
            self.commit("first-pass kit fix")
        self.write("docs/first/FAILED-DIFFS.json", json.dumps(["should-quiet-1"]))
        self.F = self.commit("first-pass verdict")
        self.fd = os.path.join(self.repo, "docs/first/FAILED-DIFFS.json")
        self.first = self.first_root(ONE_DIFF_FIRST)

    def retune(self, extra=None):
        self.write("plugins/vibe-check/agents/bugs.md", "# bugs\nretuned rule\n")
        if extra:
            extra()
        return self.commit("retune")

    def gate(self, s2, retune_root=None, pre_run=False):
        argv = ["retune-gate", "--repo", self.repo, "--s", self.S, "--s2", s2,
                "--failed-diffs", self.fd, "--last-first-commit", self.F]
        if not pre_run:
            argv += ["--first-root", self.first, "--retune-root",
                     retune_root or self.p("retune")]
        return self.cli(*argv)


class TestRetuneGate(_RepoCase):

    def test_clean_one_diff_retune_passes(self):
        s2 = self.retune()
        write_runs(self.p("retune"), diffs=["should-quiet-1"])
        code, out, err = self.gate(s2)
        self.assertEqual(code, 0, err)
        self.assertIn("retune-gate: PASS", out)
        self.assertNotIn("pre-run form", out)

    def test_pre_run_form_passes_before_runs_exist_full_form_does_not(self):
        s2 = self.retune()
        code, out, err = self.gate(s2, pre_run=True)
        self.assertEqual(code, 0, err)
        self.assertIn("retune-gate: pre-run form (ledger skipped)", out)
        code, _o, err = self.gate(s2)  # no retune root on disk
        self.assertEqual(code, 1)
        self.assertIn("ledger hole: should-quiet-1/run-1", err)

    def test_scorer_change_fails_in_both_forms(self):
        s2 = self.retune(extra=lambda: self.write("plugins/vibe-check/scripts/score.py",
                                                  "changed\n"))
        write_runs(self.p("retune"), diffs=["should-quiet-1"])
        for pre in (False, True):
            with self.subTest(pre_run=pre):
                code, _o, err = self.gate(s2, pre_run=pre)
                self.assertEqual(code, 1)
                # Both independent checks name it: the allowlist AND blob-equality.
                self.assertIn("allowlist: plugins/vibe-check/scripts/score.py", err)
                self.assertIn("frozen: plugins/vibe-check/scripts/score.py differs", err)

    def test_planted_extras_and_hole_fail(self):
        s2 = self.retune()
        cases = {
            "other-diff": ("should-quiet-2", "run-1", "ledger extra: should-quiet-2/run-1"),
            "run-4": ("should-quiet-1", "run-4", "ledger extra: should-quiet-1/run-4"),
        }
        for name, (diff, run, want) in cases.items():
            with self.subTest(case=name):
                root = write_runs(self.p("retune-" + name), diffs=["should-quiet-1"])
                write_json(os.path.join(root, diff, run, "state.json"), make_state())
                code, _o, err = self.gate(s2, retune_root=root)
                self.assertEqual(code, 1)
                self.assertIn(want, err)
        root = write_runs(self.p("retune-missing"), diffs=["should-quiet-1"])
        shutil.rmtree(os.path.join(root, "should-quiet-1", "run-2"))
        code, _o, err = self.gate(s2, retune_root=root)
        self.assertEqual(code, 1)
        self.assertIn("ledger hole: should-quiet-1/run-2", err)

    def test_ordering_and_scope_violations(self):
        # S2 == S: nothing retuned, empty allowlist set never passes.
        code, _o, err = self.gate(self.S, pre_run=True)
        self.assertEqual(code, 1)
        self.assertIn("S2 equals S", err)
        # A retune commit that changes nothing under plugins/vibe-check.
        self.write("docs/notes.md", "n\n")
        s_docs = self.commit("docs only")
        code, _o, err = self.gate(s_docs, pre_run=True)
        self.assertEqual(code, 1)
        self.assertIn("changes nothing under plugins/vibe-check", err)
        self.assertNotIn("S2 equals S", err)
        # A non-allowlisted path (phases/) in the retune.
        s2 = self.retune(extra=lambda: self.write("plugins/vibe-check/phases/x.md", "x\n"))
        code, _o, err = self.gate(s2, pre_run=True)
        self.assertEqual(code, 1)
        self.assertIn("plugins/vibe-check/phases/x.md is outside the retune allowlist", err)

    def test_ordering_violations(self):
        s2 = self.retune()
        base = ["retune-gate", "--repo", self.repo, "--s", self.S, "--s2", s2]
        # FAILED-DIFFS first committed AFTER the retune commit.
        self.write("docs/late/FAILED-DIFFS.json", json.dumps(["should-quiet-1"]))
        self.commit("late failed diffs")
        late = os.path.join(self.repo, "docs/late/FAILED-DIFFS.json")
        code, _o, err = self.cli(*(base + ["--failed-diffs", late,
                                           "--last-first-commit", self.F]))
        self.assertEqual(code, 1)
        self.assertIn("FAILED-DIFFS does not strictly precede S2", err)
        # The last first-pass commit is later than FAILED-DIFFS.
        code, _o, err = self.cli(*(base + ["--failed-diffs", self.fd,
                                           "--last-first-commit", s2]))
        self.assertEqual(code, 1)
        self.assertIn("last first-pass commit is not an ancestor of FAILED-DIFFS", err)
        # FAILED-DIFFS rewritten after its first commit.
        self.write("docs/first/FAILED-DIFFS.json", json.dumps(["should-quiet-2"]))
        self.commit("rewrite")
        code, _o, err = self.cli(*(base + ["--failed-diffs", self.fd,
                                           "--last-first-commit", self.F]))
        self.assertEqual(code, 1)
        self.assertIn("rewritten after its first commit", err)

    def test_failed_diffs_must_match_first_pass(self):
        s2 = self.retune()
        write_runs(self.p("retune"), diffs=["should-quiet-1"])
        write_json(os.path.join(self.first, "CATCH-VERDICTS.json"),
                   catch_map(miss=("triggarr-autoescape/run-1",)))
        code, _o, err = self.gate(s2)
        self.assertEqual(code, 1)
        self.assertIn("FAILED-DIFFS differs from the first-pass verdicts", err)

    def test_root_flags_go_together(self):
        s2 = self.retune()
        base = ["retune-gate", "--repo", self.repo, "--s", self.S, "--s2", s2,
                "--failed-diffs", self.fd, "--last-first-commit", self.F]
        self.assertEqual(self.cli(*(base + ["--retune-root", self.p("retune")]))[0], 2)
        self.assertEqual(self.cli(*(base + ["--first-root", self.first]))[0], 2)


class TestRetuneGatePreVerdictTooling(_RepoCase):
    """A runbook-tooling fix committed between S and FAILED-DIFFS is tolerated
    only while the retune leaves it untouched."""

    BETWEEN_S_AND_F = {"plugins/vibe-check/scripts/lanearchive.py": "kit fix\n"}

    def test_untouched_kit_fix_passes_and_is_named(self):
        s2 = self.retune()
        for pre in (True, False):
            with self.subTest(pre_run=pre):
                if not pre:
                    write_runs(self.p("retune"), diffs=["should-quiet-1"])
                code, out, err = self.gate(s2, pre_run=pre)
                self.assertEqual(code, 0, err)
                self.assertIn("pre-verdict tooling change (not part of R): plugins/vibe-check/scripts/lanearchive.py", out)

    def test_kit_file_edited_by_the_retune_fails(self):
        s2 = self.retune(extra=lambda: self.write("plugins/vibe-check/scripts/lanearchive.py", "retune edit\n"))
        code, out, err = self.gate(s2, pre_run=True)
        self.assertEqual(code, 1)
        self.assertIn("allowlist: plugins/vibe-check/scripts/lanearchive.py is outside the retune allowlist", err)
        self.assertNotIn("pre-verdict tooling change", out)

    def test_tolerance_off_without_the_tooling_pattern(self):
        # Mutation: with the tooling pattern removed the same repo fails, so
        # the tolerance (not some other path) is what lets it pass.
        s2 = self.retune()
        saved = score43.PRE_VERDICT_TOOLING
        score43.PRE_VERDICT_TOOLING = ()
        try:
            code, _o, err = self.gate(s2, pre_run=True)
        finally:
            score43.PRE_VERDICT_TOOLING = saved
        self.assertEqual(code, 1)
        self.assertIn("allowlist: plugins/vibe-check/scripts/lanearchive.py is outside the retune allowlist", err)


class TestRetuneGatePreVerdictMeasuredSurface(_RepoCase):
    """A pre-verdict change to measured surface is never tolerated."""

    BETWEEN_S_AND_F = {"plugins/vibe-check/phases/x.md": "x\n",
                       "plugins/vibe-check/scripts/score.py": "changed\n"}

    def test_measured_and_frozen_changes_still_fail(self):
        s2 = self.retune()
        code, out, err = self.gate(s2, pre_run=True)
        self.assertEqual(code, 1)
        self.assertIn("allowlist: plugins/vibe-check/phases/x.md is outside", err)
        self.assertIn("allowlist: plugins/vibe-check/scripts/score.py is outside", err)
        self.assertIn("frozen: plugins/vibe-check/scripts/score.py differs", err)
        self.assertNotIn("pre-verdict tooling change", out)


class TestOneDiffRetuneThroughClosure(_RepoCase):
    """End to end: first verdict -> retune subset -> combined -> headline-check."""

    def run_all(self):
        s2 = self.retune()
        retune = write_runs(self.p("retune"), diffs=["should-quiet-1"])  # 0/3 fired now
        self.assertEqual(self.gate(s2)[0], 0)
        code, _o, err, first_v = self.aggregate_first(self.first, catch_map(),
                                                      out="first/VERDICT.json")
        self.assertEqual(code, 0, err)
        cv_retune = write_json(self.p("retune-cv.json"), {})
        code, _o, err = self.cli(
            "aggregate", "--runs-root", retune, "--label", "retune", "--expected-diffs",
            self.fd, "--fp-bar", "8", "--sealed-fp-bar", "9", "--catch-bar", "15",
            "--catch-verdicts", cv_retune, "--verdict-out", self.p("VERDICT-retune.json"))
        self.assertEqual(code, 0, err)
        cv = write_json(self.p("combined-cv.json"), catch_map())
        code, out, err = self.cli(
            "aggregate", "--label", "combined", "--first-root", self.first, "--retune-root",
            retune, "--failed-diffs", self.fd, "--fp-bar", "8", "--sealed-fp-bar", "9",
            "--catch-bar", "15", "--catch-verdicts", cv,
            "--verdict-out", self.p("COMBINED-VERDICT.json"))
        self.assertEqual(code, 0, err)
        return (first_v, json.load(open(self.p("VERDICT-retune.json"))),
                json.load(open(self.p("COMBINED-VERDICT.json"))), out)

    def test_retune_and_combined_artifacts(self):
        first_v, retune_v, comb, out = self.run_all()
        self.assertEqual(retune_v["label"], "retune")
        self.assertNotIn("verdict", retune_v)
        self.assertEqual(retune_v["runs"], 3)
        self.assertEqual(comb["label"], "combined")
        # should-quiet-1 fired 2/3 in the first pass and 0/3 retuned.
        self.assertEqual(first_v["quiet_fired"] - comb["quiet_fired"], 2)
        self.assertEqual(first_v["sealed_literal"]["quiet_fired"]
                         - comb["sealed_literal"]["quiet_fired"], 2)
        self.assertEqual(comb["catch_hit"], first_v["catch_hit"])
        self.assertEqual(comb["untuned"], {"quiet_fired": first_v["quiet_fired"],
                                           "sealed_quiet_fired":
                                               first_v["sealed_literal"]["quiet_fired"],
                                           "catch_hit": first_v["catch_hit"]})
        self.assertIn("combined: PASS", out)
        self.assertIn("untuned first pass: 2/18, 3/21, 15/15", out)

    def results(self, art, retune_used=True, deciding=None, sealed=None):
        x = art["quiet_fired"] if deciding is None else deciding
        sx = art["sealed_literal"]["quiet_fired"] if sealed is None else sealed
        lines = ["# B3 v2.10 — Phase 41 earlier section", "", "## Headline", "",
                 "**MISS** — old", "",
                 "---", "# B3 v2.10 — Phase 43 post-change measurement (PROVE-01/02/03)", "",
                 "## Headline", "",
                 "**%s** — false alarms 16→%d of 18 (corrected cohort, bar ≤ 8; should-quiet-7 "
                 "excluded per SUPERSESSIONS-v2.10.md #001); catches 15→%d of 15 (bar 15) "
                 "(no rounding — exact fractions)" % (art["verdict"], x, art["catch_hit"]),
                 "Sealed literal (never deciding): false alarms 19→%d of 21 vs the sealed "
                 "bar ≤ 9 — would be %s" % (sx, art["sealed_literal"]["would_be"])]
        if retune_used:
            u = art.get("untuned") or {"quiet_fired": 0, "sealed_quiet_fired": 0, "catch_hit": 0}
            lines.append("Retune: used — combined headline above; untuned first pass: "
                         "%d/18, %d/21, %d/15 (see §Retune)" % (
                             u["quiet_fired"], u["sealed_quiet_fired"], u["catch_hit"]))
        else:
            lines.append("Retune: not used")
        lines += ["", "## What was measured", "", "**PASS** — false alarms 16→99 of 18"]
        path = self.p("RESULTS.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return path

    def test_headline_check_end_to_end(self):
        first_v, _r, comb, _o = self.run_all()
        comb_path = self.p("COMBINED-VERDICT.json")
        first_path = self.p("first/VERDICT.json")
        code, out, err = self.cli("headline-check", "--results", self.results(comb),
                                  "--verdict", comb_path)
        self.assertEqual(code, 0, err)
        # Untuned numbers planted in the deciding line.
        code, _o, err = self.cli("headline-check", "--results",
                                 self.results(comb, deciding=comb["untuned"]["quiet_fired"]),
                                 "--verdict", comb_path)
        self.assertEqual(code, 1)
        self.assertIn("quiet_fired", err)
        # The first-pass artifact (label first) while the headline says used.
        code, _o, err = self.cli("headline-check", "--results", self.results(first_v),
                                 "--verdict", first_path)
        self.assertEqual(code, 1)
        self.assertIn("label", err)
        # Sealed literal off by one.
        code, _o, err = self.cli("headline-check", "--results",
                                 self.results(comb, sealed=comb["sealed_literal"]["quiet_fired"] + 1),
                                 "--verdict", comb_path)
        self.assertEqual(code, 1)
        self.assertIn("sealed_literal.quiet_fired", err)
        # The no-retune path matches the first artifact.
        code, _o, err = self.cli("headline-check", "--results",
                                 self.results(first_v, retune_used=False),
                                 "--verdict", first_path)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.cli("headline-check", "--results", self.p("nope.md"),
                                  "--verdict", first_path)[0], 2)

    def test_combined_refuses_when_first_verdict_disagrees(self):
        self.run_all()
        v = json.load(open(self.p("first/VERDICT.json")))
        v["quiet_fired"] += 1
        write_json(os.path.join(self.first, "VERDICT.json"), v)
        cv = write_json(self.p("combined-cv2.json"), catch_map())
        code, _o, err = self.cli(
            "aggregate", "--label", "combined", "--first-root", self.first, "--retune-root",
            self.p("retune"), "--failed-diffs", self.fd, "--fp-bar", "8", "--sealed-fp-bar",
            "9", "--catch-bar", "15", "--catch-verdicts", cv,
            "--verdict-out", self.p("C2.json"))
        self.assertEqual(code, 1)
        self.assertIn("disagrees", err)


# --------------------------------------------------------------------------
# Named profiles (phase43 default, phase49)
# --------------------------------------------------------------------------

# Corrected 3 of 18 (should-quiet-6 all three runs) -- a phase49 PASS.
FIRE_3_OF_18 = {"should-quiet-6": [True, True, True]}
# Corrected 5 of 18 -- a phase49 MISS.
FIRE_5_OF_18 = {"should-quiet-6": [True, True, True], "should-quiet-1": [True, True, False]}

P49_BARS = ("--fp-bar", "3", "--sealed-fp-bar", "6", "--catch-bar", "15")
P43_BARS = ("--fp-bar", "8", "--sealed-fp-bar", "9", "--catch-bar", "15")


def v211_results(path, verdict, x, m, k, retune="Retune: not used", bar=3,
                 h1="# B3 v2.11 — Phase 49 release-candidate measurement (REL-01/REL-02)"):
    lines = [h1, "", "## Phase-49 pre-registration", "", "text", "",
             "## Headline", "",
             "**%s** — false alarms 3→%d of 18 (corrected cohort, bar ≤ %d; should-quiet-7 "
             "excluded per SUPERSESSIONS-v2.10.md #001); catches 15→%d of 15 (bar 15) "
             "(no rounding — exact fractions)" % (verdict, x, bar, m),
             "Sealed literal (never deciding): false alarms 6→%d of 21 vs the sealed "
             "bar ≤ 6 — would be PASS" % k,
             retune, "", "## What was measured", ""]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def artifact(label="first", verdict="PASS", x=3, m=15, k=3, fp_bar=3, sealed_bar=6,
             catch_bar=15, untuned=None):
    art = {"label": label, "verdict": verdict, "quiet_fired": x, "catch_hit": m,
           "sealed_literal": {"quiet_fired": k, "fp_bar": sealed_bar},
           "fp_bar": fp_bar, "catch_bar": catch_bar}
    if untuned is not None:
        art["untuned"] = untuned
    return art


class TestProfiles(_TmpDirCase):

    def agg(self, root, profile=None, bars=P49_BARS, label="first", out="V.json"):
        cv = write_json(self.p("cv-" + out), catch_map())
        argv = ["aggregate", "--runs-root", root, "--label", label]
        if profile:
            argv += ["--profile", profile]
        argv += list(bars) + ["--catch-verdicts", cv, "--verdict-out", self.p(out)]
        code, out_s, err = self.cli(*argv)
        return code, out_s, err, (json.load(open(self.p(out))) if code == 0 else None)

    def test_profile_table_values(self):
        want43 = {"fp_bar": 8, "sealed_fp_bar": 9, "catch_bar": 15,
                  "h1": "# B3 v2.10 — Phase 43", "fp_before": 16, "sealed_before": 19,
                  "catch_before": 15}
        want49 = {"fp_bar": 3, "sealed_fp_bar": 6, "catch_bar": 15,
                  "h1": "# B3 v2.11 — Phase 49", "fp_before": 3, "sealed_before": 6,
                  "catch_before": 15}
        for name, want in (("phase43", want43), ("phase49", want49)):
            got = score43.PROFILES[name]
            self.assertEqual({k: got[k] for k in want}, want)
        self.assertEqual(score43.PROFILES["phase43"]["labels"], ("first", "retune", "combined"))
        self.assertEqual(score43.PROFILES["phase43"]["retune_label"], "combined")
        self.assertEqual(score43.PROFILES["phase49"]["labels"], ("first", "retune-full"))
        self.assertEqual(score43.PROFILES["phase49"]["retune_label"], "retune-full")
        # The legacy constants are aliases of the phase43 profile.
        self.assertEqual((score43.FP_BAR, score43.SEALED_FP_BAR, score43.CATCH_BAR), (8, 9, 15))

    def test_default_profile_is_phase43_and_byte_identical(self):
        root = write_runs(self.p("first"), FIRE_8_OF_18)
        _c, out_a, _e, v_a = self.agg(root, None, P43_BARS, out="a.json")
        _c, out_b, _e, v_b = self.agg(root, "phase43", P43_BARS, out="b.json")
        self.assertEqual(v_a, v_b)
        self.assertEqual(out_a, out_b)
        self.assertEqual(open(self.p("a.json")).read(), open(self.p("b.json")).read())

    def test_phase49_bars_accepted(self):
        root = write_runs(self.p("first"), FIRE_3_OF_18)
        code, _o, err, v = self.agg(root, "phase49")
        self.assertEqual(code, 0, err)
        self.assertEqual((v["fp_bar"], v["catch_bar"], v["sealed_literal"]["fp_bar"]),
                         (3, 15, 6))
        self.assertEqual(v["verdict"], "PASS")

    def test_phase49_decides_against_bar_3(self):
        root = write_runs(self.p("first"), FIRE_5_OF_18)
        code, _o, err, v = self.agg(root, "phase49")
        self.assertEqual(code, 0, err)
        self.assertEqual((v["quiet_fired"], v["verdict"]), (5, "MISS"))
        # The same runs under phase43 (bar 8) pass: the profile bar is what decides.
        _c, _o, _e, v43 = self.agg(root, "phase43", P43_BARS, out="v43.json")
        self.assertEqual(v43["verdict"], "PASS")

    def test_phase49_refuses_phase43_bars(self):
        root = write_runs(self.p("first"), FIRE_3_OF_18)
        code, _o, err, _v = self.agg(root, "phase49", P43_BARS)
        self.assertEqual(code, 1)
        self.assertIn("bars must be --fp-bar 3 --sealed-fp-bar 6 --catch-bar 15", err)

    def test_phase43_refuses_phase49_bars(self):
        root = write_runs(self.p("first"), FIRE_3_OF_18)
        code, _o, err, _v = self.agg(root, "phase43", P49_BARS)
        self.assertEqual(code, 1)
        self.assertIn("bars must be --fp-bar 8 --sealed-fp-bar 9 --catch-bar 15", err)

    def test_mutant_profile_fp_bar_is_read_from_table(self):
        root = write_runs(self.p("first"), FIRE_3_OF_18)
        with mock.patch.dict(score43.PROFILES["phase49"], {"fp_bar": 8}):
            self.assertEqual(score43.PROFILES["phase49"]["fp_bar"], 8)
            code, _o, err, _v = self.agg(root, "phase49", out="m.json")
        self.assertEqual(code, 1)
        self.assertIn("bars must be --fp-bar 8", err)
        self.assertEqual(self.agg(root, "phase49", out="r.json")[0], 0)

    def test_unknown_profile_is_usage_error(self):
        root = write_runs(self.p("first"), FIRE_3_OF_18)
        self.assertEqual(self.agg(root, "phase99")[0], 2)

    def hc(self, results, art, profile=None):
        vpath = write_json(self.p("art.json"), art)
        argv = ["headline-check", "--results", results, "--verdict", vpath]
        if profile:
            argv += ["--profile", profile]
        return self.cli(*argv)

    def test_headline_check_phase49_match(self):
        res = v211_results(self.p("R.md"), "PASS", 3, 15, 3)
        code, out, err = self.hc(res, artifact(), "phase49")
        self.assertEqual(code, 0, err)
        self.assertIn("headline-check: match", out)

    def test_headline_check_phase49_from_real_aggregate(self):
        root = write_runs(self.p("first"), FIRE_3_OF_18)
        _c, _o, _e, v = self.agg(root, "phase49")
        res = v211_results(self.p("R.md"), v["verdict"], v["quiet_fired"], v["catch_hit"],
                           v["sealed_literal"]["quiet_fired"])
        code, _o, err = self.cli("headline-check", "--profile", "phase49",
                                 "--results", res, "--verdict", self.p("V.json"))
        self.assertEqual(code, 0, err)

    def test_headline_check_profiles_do_not_cross(self):
        res49 = v211_results(self.p("R49.md"), "PASS", 3, 15, 3)
        # phase43 (default) on v2.11 text: no Phase-43 H1.
        code, _o, err = self.hc(res49, artifact(fp_bar=8, sealed_bar=9))
        self.assertEqual(code, 1)
        self.assertIn("headline-block", err)
        # phase49 on Phase-43 grammar text.
        res43 = v211_results(self.p("R43.md"), "PASS", 3, 15, 3,
                             h1="# B3 v2.10 — Phase 43 post-change measurement")
        code, _o, err = self.hc(res43, artifact(), "phase49")
        self.assertEqual(code, 1)
        self.assertIn("headline-block", err)

    def test_headline_check_phase49_wrong_bar_in_deciding_line(self):
        res = v211_results(self.p("R.md"), "PASS", 3, 15, 3, bar=8)
        code, _o, err = self.hc(res, artifact(), "phase49")
        self.assertEqual(code, 1)
        self.assertIn("deciding-line", err)

    def test_headline_check_artifact_bars_cross_checked(self):
        res = v211_results(self.p("R.md"), "PASS", 3, 15, 3)
        for name, art in (("fp", artifact(fp_bar=8)), ("catch", artifact(catch_bar=14)),
                          ("sealed", artifact(sealed_bar=9))):
            with self.subTest(bar=name):
                code, _o, err = self.hc(res, art, "phase49")
                self.assertEqual(code, 1)
                self.assertIn("bars", err.split(":", 1)[1].strip().replace(" ", "").split(","))
        # Same lock under phase43: a phase49-barred artifact is refused.
        bad = artifact(fp_bar=3, sealed_bar=6)
        self.assertIn("bars", score43.headline_check(
            v211_results(self.p("R43b.md"), "PASS", 3, 15, 3,
                         h1="# B3 v2.10 — Phase 43 x"), write_json(self.p("b.json"), bad)))


class TestRetuneFull(_RepoCase):
    """Under phase49 the retune is the full 12-diff cohort on S2 and its verdict
    is decided from those runs alone."""

    def make_first(self, fired, name="F"):
        root = write_runs(self.p(name), fired)
        write_json(os.path.join(root, "CATCH-VERDICTS.json"), catch_map())
        cv = write_json(self.p("cv-%s.json" % name), catch_map())
        code, _o, err = self.cli("aggregate", "--profile", "phase49", "--runs-root", root,
                                 "--label", "first", *P49_BARS, "--catch-verdicts", cv,
                                 "--verdict-out", os.path.join(root, "VERDICT.json"))
        self.assertEqual(code, 0, err)
        return root

    def make_retune(self, fired, name="R"):
        root = write_runs(self.p(name), fired)
        write_json(os.path.join(root, "CATCH-VERDICTS.json"), catch_map())
        return root

    def full(self, r, f, *extra, profile="phase49", label="retune-full", out="RV.json"):
        argv = ["aggregate", "--profile", profile, "--label", label]
        if r is not None:
            argv += ["--runs-root", r]
        if f is not None:
            argv += ["--first-root", f]
        argv += list(P49_BARS if profile == "phase49" else P43_BARS)
        argv += ["--catch-verdicts", os.path.join(r or self.tmp, "CATCH-VERDICTS.json"),
                 "--verdict-out", self.p(out)] + list(extra)
        code, o, err = self.cli(*argv)
        return code, o, err, (json.load(open(self.p(out))) if code == 0 else None)

    def alone(self, r, out):
        cv = os.path.join(r, "CATCH-VERDICTS.json")
        code, _o, err = self.cli("aggregate", "--profile", "phase49", "--runs-root", r,
                                 "--label", "first", *P49_BARS, "--catch-verdicts", cv,
                                 "--verdict-out", self.p(out))
        self.assertEqual(code, 0, err)
        return json.load(open(self.p(out)))["verdict"]

    def test_verdict_decided_only_from_retune_root(self):
        f_miss = self.make_first(FIRE_5_OF_18, "F1")
        r_pass = self.make_retune(FIRE_3_OF_18, "R1")
        code, out, err, v1 = self.full(r_pass, f_miss, out="v1.json")
        self.assertEqual(code, 0, err)
        self.assertEqual(v1["label"], "retune-full")
        self.assertEqual(v1["untuned"], {"quiet_fired": 5, "sealed_quiet_fired": 5,
                                         "catch_hit": 15})
        self.assertIn("retune-full: PASS", out)
        self.assertIn("untuned first pass: 5/18, 5/21, 15/15", out)
        f_pass = self.make_first(FIRE_3_OF_18, "F2")
        r_miss = self.make_retune(FIRE_5_OF_18, "R2")
        code, _o, err, v2 = self.full(r_miss, f_pass, out="v2.json")
        self.assertEqual(code, 0, err)
        self.assertEqual(v2["untuned"]["quiet_fired"], 3)
        # Not a mix: the two verdicts differ and each is what R alone implies.
        self.assertNotEqual(v1["verdict"], v2["verdict"])
        self.assertEqual(v1["verdict"], self.alone(r_pass, "a1.json"))
        self.assertEqual(v2["verdict"], self.alone(r_miss, "a2.json"))
        self.assertEqual((v1["verdict"], v2["verdict"]), ("PASS", "MISS"))

    def test_retune_root_hole_refuses(self):
        f = self.make_first(FIRE_3_OF_18)
        r = self.make_retune(FIRE_3_OF_18)
        shutil.rmtree(os.path.join(r, "should-quiet-4", "run-3"))
        code, _o, err, _v = self.full(r, f)
        self.assertEqual(code, 1)
        self.assertIn("should-quiet-4/run-3", err)
        self.assertFalse(os.path.exists(self.p("RV.json")))

    def test_first_root_required(self):
        r = self.make_retune(FIRE_3_OF_18)
        code, _o, err, _v = self.full(r, None)
        self.assertEqual(code, 1)
        self.assertIn("--first-root", err)

    def test_runs_root_required(self):
        f = self.make_first(FIRE_3_OF_18)
        argv = ["aggregate", "--profile", "phase49", "--label", "retune-full",
                "--first-root", f, *P49_BARS, "--catch-verdicts",
                os.path.join(f, "CATCH-VERDICTS.json"), "--verdict-out", self.p("x.json")]
        code, _o, err = self.cli(*argv)
        self.assertEqual(code, 1)
        self.assertIn("--runs-root", err)

    def test_first_verdict_disagreement_refuses(self):
        f = self.make_first(FIRE_3_OF_18)
        r = self.make_retune(FIRE_3_OF_18)
        v = json.load(open(os.path.join(f, "VERDICT.json")))
        v["quiet_fired"] += 1
        write_json(os.path.join(f, "VERDICT.json"), v)
        code, _o, err, _v = self.full(r, f)
        self.assertEqual(code, 1)
        self.assertIn("disagrees", err)

    def test_first_verdict_must_exist(self):
        f = self.make_first(FIRE_3_OF_18)
        os.remove(os.path.join(f, "VERDICT.json"))
        r = self.make_retune(FIRE_3_OF_18)
        code, _o, err, _v = self.full(r, f)
        self.assertEqual(code, 1)
        self.assertIn("VERDICT.json", err)

    def test_retune_and_failed_flags_refused(self):
        f = self.make_first(FIRE_3_OF_18)
        r = self.make_retune(FIRE_3_OF_18)
        for flag in (("--retune-root", r), ("--failed-diffs", self.fd)):
            with self.subTest(flag=flag[0]):
                code, _o, err, _v = self.full(r, f, *flag)
                self.assertEqual(code, 1)
                self.assertIn(flag[0], err)

    def test_expected_diffs_must_be_all_12(self):
        f = self.make_first(FIRE_3_OF_18)
        r = self.make_retune(FIRE_3_OF_18)
        short = write_json(self.p("short.json"), list(score43.DIFFS[:11]))
        code, _o, err, _v = self.full(r, f, "--expected-diffs", short)
        self.assertEqual(code, 1)
        self.assertIn("all 12 diffs", err)
        allx = write_json(self.p("all.json"), list(score43.DIFFS))
        self.assertEqual(self.full(r, f, "--expected-diffs", allx, out="ok.json")[0], 0)

    def test_label_profile_refusals(self):
        f = self.make_first(FIRE_3_OF_18)
        r = self.make_retune(FIRE_3_OF_18)
        for label in ("combined", "retune"):
            with self.subTest(label=label):
                code, _o, err, _v = self.full(r, f, label=label)
                self.assertEqual(code, 1)
                self.assertIn("label %s is not allowed under profile phase49" % label, err)
        code, _o, err, _v = self.full(r, f, profile="phase43")
        self.assertEqual(code, 1)
        self.assertIn("label retune-full is not allowed under profile phase43", err)

    def test_mutant_labels_read_from_table(self):
        f = self.make_first(FIRE_3_OF_18)
        r = self.make_retune(FIRE_3_OF_18)
        with mock.patch.dict(score43.PROFILES["phase49"],
                             {"labels": ("first", "retune-full", "combined")}):
            code, _o, err, _v = self.full(r, f, label="combined")
        self.assertNotIn("not allowed under profile", err)
        code, _o, err, _v = self.full(r, f, label="combined")
        self.assertIn("label combined is not allowed under profile phase49", err)

    # retune-gate --cohort

    def gate_cohort(self, s2, root, cohort=None, pre_run=False):
        argv = ["retune-gate", "--repo", self.repo, "--s", self.S, "--s2", s2,
                "--failed-diffs", self.fd, "--last-first-commit", self.F]
        if not pre_run:
            argv += ["--first-root", self.first, "--retune-root", root]
        if cohort:
            argv += ["--cohort", cohort]
        return self.cli(*argv)

    def test_retune_gate_cohort_full(self):
        s2 = self.retune()
        root = write_runs(self.p("rfull"))
        code, out, err = self.gate_cohort(s2, root, "full")
        self.assertEqual(code, 0, err)
        self.assertIn("retune-gate: PASS", out)
        code, _o, err = self.gate_cohort(s2, root)  # default: failed cohort
        self.assertEqual(code, 1)
        self.assertIn("ledger extra: should-quiet-2/run-1", err)
        code, _o, err = self.gate_cohort(s2, root, "failed")
        self.assertIn("ledger extra: should-quiet-2/run-1", err)
        shutil.rmtree(os.path.join(root, "should-quiet-2"))
        code, _o, err = self.gate_cohort(s2, root, "full")
        self.assertEqual(code, 1)
        self.assertIn("ledger hole: should-quiet-2/run-1", err)

    def test_retune_gate_pre_run_ignores_cohort(self):
        s2 = self.retune()
        for cohort in ("full", "failed"):
            with self.subTest(cohort=cohort):
                code, out, err = self.gate_cohort(s2, None, cohort, pre_run=True)
                self.assertEqual(code, 0, err)
                self.assertIn("pre-run form", out)

    # headline retune label per profile

    def test_headline_retune_label_per_profile(self):
        used = ("Retune: used — full-cohort S2 headline above; untuned first pass: "
                "5/18, 5/21, 15/15 (see §Retune)")
        res = v211_results(self.p("R.md"), "PASS", 3, 15, 3, retune=used)
        u = {"quiet_fired": 5, "sealed_quiet_fired": 5, "catch_hit": 15}
        good = write_json(self.p("good.json"), artifact(label="retune-full", untuned=u))
        code, _o, err = self.cli("headline-check", "--profile", "phase49", "--results", res,
                                 "--verdict", good)
        self.assertEqual(code, 0, err)
        comb = write_json(self.p("comb.json"), artifact(label="combined", untuned=u))
        code, _o, err = self.cli("headline-check", "--profile", "phase49", "--results", res,
                                 "--verdict", comb)
        self.assertEqual(code, 1)
        self.assertIn("label", err)
        # phase43 keeps `combined` as its retune label.
        res43 = v211_results(self.p("R43.md"), "PASS", 3, 15, 3, retune=used,
                             h1="# B3 v2.10 — Phase 43 x")
        with open(res43, encoding="utf-8") as fh:
            text = fh.read().replace("false alarms 3→3 of 18 (corrected cohort, bar ≤ 3",
                                     "false alarms 16→3 of 18 (corrected cohort, bar ≤ 8")
            text = text.replace("false alarms 6→3 of 21", "false alarms 19→3 of 21")
        with open(res43, "w", encoding="utf-8") as fh:
            fh.write(text)
        c43 = write_json(self.p("c43.json"), artifact(label="combined", fp_bar=8,
                                                      sealed_bar=9, untuned=u))
        self.assertEqual(score43.headline_check(res43, c43), [])
        r43 = write_json(self.p("r43.json"), artifact(label="retune-full", fp_bar=8,
                                                      sealed_bar=9, untuned=u))
        self.assertEqual(score43.headline_check(res43, r43), ["label"])


# --------------------------------------------------------------------------
# Module conventions
# --------------------------------------------------------------------------

class TestModuleConventions(unittest.TestCase):

    ALLOWED = {"argparse", "json", "os", "re", "subprocess", "sys", "replay"}

    def _tree(self):
        with open(SCORE43_PY, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_imports_are_exactly_the_allowed_set(self):
        found = set()
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                for a in node.names:
                    found.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        self.assertEqual(found, self.ALLOWED)

    def test_every_subprocess_run_carries_timeout(self):
        calls = 0
        for node in ast.walk(self._tree()):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if not (isinstance(fn, ast.Attribute) and fn.attr == "run"
                    and isinstance(fn.value, ast.Name) and fn.value.id == "subprocess"):
                continue
            calls += 1
            kw = {k.arg: k.value for k in node.keywords}
            self.assertIn("timeout", kw)
            self.assertEqual(kw["timeout"].value, 120)
        self.assertGreater(calls, 0, "no subprocess.run calls found -- vacuous")

    def test_titles_only_emitted_by_catch_candidates(self):
        tree = self._tree()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for sub in ast.walk(node):
                    if (isinstance(sub, ast.Constant) and sub.value == "title"
                            and node.name != "catch_candidates"):
                        self.fail("title key used in %s" % node.name)

    def test_exclusion_is_not_a_flag(self):
        with open(SCORE43_PY, encoding="utf-8") as fh:
            text = fh.read()
        self.assertEqual(score43.QUIET_EXCLUDED, ("should-quiet-7",))
        self.assertNotIn("--exclude", text)
        self.assertNotIn("--quiet-excluded", text)


if __name__ == "__main__":
    unittest.main()
