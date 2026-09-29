"""Tests for replay.py — the offline SCORER-01 replay harness and guardrail.

Every lock here carries a demonstrated failure: the manifest checks are proven
against mutated copies, the guardrail is proven to reject a planted
catch-killing override and to fail closed on a planted unreproducible catch,
and the census fails (never skips) when the archives are missing.
"""

import ast
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import replay  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
REPLAY_PY = os.path.join(HERE, "replay.py")
REPO_ROOT = replay.REPO_ROOT
SEALED_PATHS = tuple(replay.ARCHIVE_ROOTS) + (
    "docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md",)

# Observed on the committed archives with the baseline blob. (band, score)
# multisets agree on 57/66; the pin is on (band, score, stable_hash), where
# runs/should-quiet-3/run-2 additionally differs by one codex row's hash.
EXPECTED_EXACT_BASELINE = 56
EXPECTED_DRIFT_RUNS = (
    "runs-v2.10/should-quiet-1/run-2",
    "runs-v2.10/should-quiet-7/run-1",
    "runs-v2.10/should-quiet-7/run-2",
    "runs-v2.10/should-quiet-7/run-3",
    "runs-v2.10/triggarr-settings-form-split/run-2",
    "runs/should-quiet-1/run-2",
    "runs/should-quiet-1/run-3",
    "runs/should-quiet-3/run-2",
    "runs/triggarr-secret-in-logs/run-1",
    "runs/triggarr-secret-in-logs/run-2",
)
# An owner amendment (SUPERSESSIONS-v2.10.md) must surface as a visible pin change.
EXPECTED_AMENDED = 1
# The owner-amended protected catches and the ledger entry each one cites.
EXPECTED_AMENDMENTS = {"runs/triggarr-secret-in-logs/run-2": "008"}
# Phase-40 runs whose codex object reached the orchestrator only inside a Write
# payload (not a recovery channel): the codex survivor is exact from state.json,
# but no non-surviving codex finding can be recovered.
CODEX_WRITE_ONLY_RUNS = (
    "runs-v2.10-phase40/batch1/triggarr-secret-in-logs/run-1",
    "runs-v2.10-phase40/batch2/triggarr-secret-in-logs/run-1",
)
CODEX_JOINED_RUN = "runs/triggarr-secret-in-logs/run-2"
NATIVE_ONLY_RUN = "runs/should-quiet-2/run-1"
BASELINE_SPEC = "blob:" + replay.BASELINE_SCORE_BLOB
KILL_ALL = 'THRESHOLDS={"review":101,"deep-review":101}'


def _git(*argv):
    return subprocess.run(["git", "-C", REPO_ROOT, *argv], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, timeout=120)


def sealed_unmodified():
    worktree = _git("diff", "--quiet", "HEAD", "--", *SEALED_PATHS)
    staged = _git("diff", "--cached", "--quiet", "--", *SEALED_PATHS)
    return worktree.returncode == 0 and staged.returncode == 0


def tearDownModule():
    if not sealed_unmodified():
        raise AssertionError(
            "SEALED ARCHIVES MODIFIED by the test run: `git diff HEAD -- %s` is "
            "non-empty. Nothing in this suite may write to the sealed evidence."
            % " ".join(SEALED_PATHS))


_CACHE = {}


def _runs():
    if "runs" not in _CACHE:
        _CACHE["runs"] = replay.iter_runs()
    return _CACHE["runs"]


def _baseline():
    if "base" not in _CACHE:
        scorer = replay.load_scorer(BASELINE_SPEC)
        _CACHE["base"] = replay.replay_all(scorer, _runs())
    return _CACHE["base"]


def _base_results():
    return {k: v["result"] for k, v in _baseline().items()}


def _ledger_numbers():
    with open(os.path.join(REPO_ROOT, replay.LEDGER_REL), encoding="utf-8") as fh:
        return re.findall(r"^## ([0-9]{3}) —", fh.read(), re.MULTILINE)


class _TmpDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test-replay-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_manifest(self, manifest, name="manifest.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh)
        return path

    def _read(self, path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()


# --------------------------------------------------------------------------
# Census
# --------------------------------------------------------------------------

class TestCensus(unittest.TestCase):

    def test_scoreable_count_is_pinned(self):
        n = len(_runs())
        self.assertNotEqual(n, 0, "no archived runs found — the census must fail, not skip")
        self.assertEqual(n, replay.EXPECTED_SCOREABLE)

    def test_per_archive_counts(self):
        per = {}
        for r in _runs():
            per[r["archive"]] = per.get(r["archive"], 0) + 1
        self.assertEqual(per, {"runs": 18, "runs-v2.10": 36, "runs-v2.10-phase40": 12})

    def test_failed_dirs_exist_and_are_excluded(self):
        excluded = replay.excluded_run_dirs()
        self.assertEqual(len(excluded), 3)
        self.assertTrue(all(".failed-" in d for d in excluded))
        returned = {r["rel_path"] for r in _runs()}
        self.assertFalse(returned & set(excluded))
        self.assertFalse(any(".failed" in p for p in returned))

    def test_every_run_has_tree_diff_and_only_phase40_has_transcripts(self):
        for r in _runs():
            self.assertIsInstance(r["tree_diff"], str, r["rel_path"])
            self.assertEqual(r["problems"], [], r["rel_path"])
        with_t = [r["rel_path"] for r in _runs() if r["transcript_path"]]
        self.assertEqual(len(with_t), 12)
        self.assertTrue(all(p.startswith("runs-v2.10-phase40/") for p in with_t))


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------

class TestManifest(unittest.TestCase):

    def test_real_manifest_is_clean(self):
        self.assertEqual(replay.check_manifest(replay.load_manifest(), _runs()), [])

    def test_guardrail_rows(self):
        m = replay.load_manifest()
        self.assertEqual(len(replay._protected_runs(m)), replay.EXPECTED_PROTECTED)

    def _first_protected(self, m):
        return replay._protected_runs(m)[0]

    def test_mutated_hash_is_unresolved(self):
        m = copy.deepcopy(replay.load_manifest())
        run = self._first_protected(m)
        m["catch_runs"][run]["survivors_at_site"][0]["stable_hash"] = "0" * 64
        problems = replay.check_manifest(m, _runs())
        unresolved = [p for p in problems if "unresolved" in p]
        self.assertEqual(len(unresolved), 1, problems)
        self.assertTrue(unresolved[0].startswith(run + ":"))

    def test_deleted_survivor_is_missing(self):
        m = copy.deepcopy(replay.load_manifest())
        run = self._first_protected(m)
        del m["catch_runs"][run]["survivors_at_site"][0]
        problems = replay.check_manifest(m, _runs())
        self.assertTrue(any("missing from manifest" in p for p in problems), problems)

    def test_amendment_with_unknown_ledger_entry(self):
        m = copy.deepcopy(replay.load_manifest())
        run = self._first_protected(m)
        m.setdefault("guardrail_amendments", {})[run] = {"ledger_entry": "999",
                                                         "approved": "t", "reason": "t"}
        problems = replay.check_manifest(m, _runs())
        self.assertIn("%s: amendment ledger entry 999 not found" % run, problems)

    def test_amendment_for_non_protected_run(self):
        m = copy.deepcopy(replay.load_manifest())
        quiet = m["quiet_runs"]["headline"][0]
        m.setdefault("guardrail_amendments", {})[quiet] = {
            "ledger_entry": _ledger_numbers()[-1], "approved": "t", "reason": "t"}
        problems = replay.check_manifest(m, _runs())
        self.assertIn("%s: amendment for a non-protected run" % quiet, problems)

    def test_amendment_with_existing_ledger_entry_is_clean(self):
        numbers = _ledger_numbers()
        self.assertTrue(numbers)
        m = copy.deepcopy(replay.load_manifest())
        m.setdefault("guardrail_amendments", {})[self._first_protected(m)] = {
            "ledger_entry": numbers[-1], "approved": "t", "reason": "t"}
        self.assertEqual(replay.check_manifest(m, _runs()), [])


# --------------------------------------------------------------------------
# Reconstruction
# --------------------------------------------------------------------------

SYNTH_DIFF = """diff --git a/gone.py b/gone.py
--- a/gone.py
+++ /dev/null
@@ -1,3 +0,0 @@
-a
-b
-c
diff --git a/pkg/mod.py b/pkg/mod.py
--- a/pkg/mod.py
+++ b/pkg/mod.py
@@ -10,4 +10,6 @@ def f():
 x
+y
+z
 w
@@ -40 +42 @@
-old
+new
diff --git a/only_del.py b/only_del.py
--- a/only_del.py
+++ b/only_del.py
@@ -5,2 +5,0 @@
-p
-q
"""


class TestReconstruction(unittest.TestCase):

    def test_hunk_ranges_synthetic(self):
        self.assertEqual(replay.hunk_ranges(SYNTH_DIFF), {"pkg/mod.py": [[10, 15], [42, 42]]})

    def _envelope(self, rel):
        return replay.reconstruct_envelope(replay._run_index(_runs())[rel])

    def test_envelope_strips_scored_keys(self):
        for r in _runs():
            env, _meta = replay.reconstruct_envelope(r)
            self.assertEqual(env["command"], "deep-review")
            for key in ("thresholds", "min_confidence", "idiom_floor"):
                self.assertNotIn(key, env)
            for f in env["findings"]:
                for k in replay.SCORED_KEYS:
                    self.assertNotIn(k, f, r["rel_path"])

    def test_codex_status_follows_survivor_agents(self):
        env, meta = self._envelope(CODEX_JOINED_RUN)
        self.assertEqual(env["codex"], {"status": "joined"})
        self.assertTrue(meta["codex_joined"])
        env, meta = self._envelope(NATIVE_ONLY_RUN)
        self.assertEqual(env["codex"], {"status": "skipped"})
        self.assertFalse(meta["codex_joined"])

    def test_transcript_recovery_covers_survivor_agents(self):
        checked = 0
        for r in _runs():
            if not r["transcript_path"]:
                continue
            checked += 1
            recovered = {i["agent"] for i in
                         replay.recover_transcript_findings(r["transcript_path"])}
            survivors = {f.get("agent") for f in r["state"]["passes"][-1]["findings"]}
            missing = survivors - recovered
            if r["rel_path"] in CODEX_WRITE_ONLY_RUNS:
                self.assertEqual(missing, {replay.CODEX_AGENT}, r["rel_path"])
            else:
                self.assertEqual(missing, set(), r["rel_path"])
        self.assertEqual(checked, 12)

    def test_recovery_ignores_template_and_write_payloads(self):
        path = os.path.join(tempfile.mkdtemp(prefix="test-replay-"), "t.jsonl")
        try:
            example = {"agent": "security", "findings": [{"file": "x.py", "line": 1}]}
            records = [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "name": "Write", "input": {"content": json.dumps(example)}}]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "content": json.dumps(example)}]}},
                {"type": "attachment", "attachment": {"prompt": "<result>%s</result>"
                                                      % json.dumps(example)}},
                {"type": "user", "message": {"content": "<result>```json\n%s\n```</result>"
                                             % json.dumps({"agent": "bugs", "findings": [
                                                 {"file": "y.py", "line": 2}]})}},
            ]
            with open(path, "w", encoding="utf-8") as fh:
                for rec in records:
                    fh.write(json.dumps(rec) + "\n")
                fh.write("not json\n")
            meta = {}
            got = replay.recover_transcript_findings(path, meta)
            self.assertEqual([i["agent"] for i in got], ["bugs"])
            self.assertEqual(meta["malformed"], 1)
        finally:
            shutil.rmtree(os.path.dirname(path), ignore_errors=True)


# --------------------------------------------------------------------------
# Baseline fidelity
# --------------------------------------------------------------------------

class TestBaselineFidelity(unittest.TestCase):

    def test_exact_count_and_drift_runs_are_pinned(self):
        base = _baseline()
        self.assertEqual(len(base), replay.EXPECTED_SCOREABLE)
        exact = sum(1 for v in base.values() if v["exact"])
        drift = tuple(sorted(k for k, v in base.items() if not v["exact"]))
        self.assertEqual(exact, EXPECTED_EXACT_BASELINE)
        self.assertEqual(drift, EXPECTED_DRIFT_RUNS)
        self.assertEqual(exact + len(drift), replay.EXPECTED_SCOREABLE)


# --------------------------------------------------------------------------
# Guardrail
# --------------------------------------------------------------------------

def _entry(site_lines=((10, 12),), floor="warning", axis=(("security", "leaks key"),),
           non_axis=(("compliance", "convention"),)):
    survivors = [{"agent": a, "title": t, "axis": True} for a, t in axis]
    survivors += [{"agent": a, "title": t, "axis": False} for a, t in non_axis]
    return {"site": {"file": "a.py", "lines": [list(p) for p in site_lines]},
            "floor": floor, "survivors_at_site": survivors}


def _row(agent, title, band="critical", line=11, members=None, file="a.py"):
    row = {"agent": agent, "title": title, "band": band, "line": line, "file": file,
           "orchestrator_score": 99, "stable_hash": "f" * 64}
    if members is not None:
        row["members"] = members
    return row


class TestCatchStatus(unittest.TestCase):

    def test_survivor_title(self):
        self.assertEqual(replay.catch_status({"findings": [_row("security", "leaks key")]},
                                             _entry()), (True, "survivor-title"))

    def test_member_title(self):
        row = _row("compliance", "convention",
                   members=[{"agent": "compliance", "title": "convention"},
                            {"agent": "security", "title": "leaks key"}])
        self.assertEqual(replay.catch_status({"findings": [row]}, _entry()),
                         (True, "member-title"))

    def test_below_floor(self):
        row = _row("security", "leaks key", band="medium")
        self.assertEqual(replay.catch_status({"findings": [row]}, _entry()),
                         (False, "below-floor"))

    def test_no_row_at_site(self):
        rows = [_row("security", "leaks key", line=40), _row("security", "leaks key",
                                                             file="b.py")]
        self.assertEqual(replay.catch_status({"findings": rows}, _entry()),
                         (False, "no-row-at-site"))

    def test_axis_false(self):
        row = _row("compliance", "convention",
                   members=[{"agent": "compliance", "title": "convention"}])
        self.assertEqual(replay.catch_status({"findings": [row]}, _entry()),
                         (False, "axis-false"))

    def test_axis_needs_matching_agent(self):
        row = _row("bugs", "leaks key")
        self.assertEqual(replay.catch_status({"findings": [row]}, _entry()),
                         (False, "axis-false"))


class TestGuardrail(_TmpDirCase):

    def test_all_protected_catches_reproduced_by_baseline(self):
        """D-05: every recorded catch must be REPRODUCED (or owner-AMENDED).

        A red test here is the intended signal: an unreproducible protected
        catch is a blocking evidence gap, never an exclusion.
        """
        m = replay.load_manifest()
        prot = replay.protected_status(_base_results(), m)
        self.assertEqual(len(prot), replay.EXPECTED_PROTECTED)
        not_ok = {k: v["basis"] for k, v in prot.items() if v["status"] == "UNEVALUABLE"}
        self.assertEqual(not_ok, {}, "UNEVALUABLE protected catches: %r" % not_ok)
        amended = sum(1 for v in prot.values() if v["status"] == "AMENDED")
        self.assertEqual(amended, EXPECTED_AMENDED)
        self.assertEqual(sum(1 for v in prot.values() if v["status"] == "REPRODUCED"),
                         replay.EXPECTED_PROTECTED - EXPECTED_AMENDED)

    def test_amendment_pin_matches_manifest(self):
        m = replay.load_manifest()
        self.assertEqual(len(m.get("guardrail_amendments", {})), EXPECTED_AMENDED)
        self.assertEqual(len(EXPECTED_AMENDMENTS), EXPECTED_AMENDED)
        self.assertEqual({k: v["ledger_entry"] for k, v in m["guardrail_amendments"].items()},
                         EXPECTED_AMENDMENTS)
        for entry_no in EXPECTED_AMENDMENTS.values():
            self.assertIn(entry_no, _ledger_numbers())

    def test_real_amendments_are_amended_with_their_ledger_entry(self):
        prot = replay.protected_status(_base_results(), replay.load_manifest())
        got = {k: v["ledger_entry"] for k, v in prot.items() if v["status"] == "AMENDED"}
        self.assertEqual(got, EXPECTED_AMENDMENTS)

    def test_dropping_a_real_amendment_fails_closed(self):
        """Mutation: without the owner amendment the gap is UNEVALUABLE again (exit 1)."""
        m = copy.deepcopy(replay.load_manifest())
        for run in EXPECTED_AMENDMENTS:
            del m["guardrail_amendments"][run]
        prot = replay.protected_status(_base_results(), m)
        for run in EXPECTED_AMENDMENTS:
            self.assertEqual(prot[run]["status"], "UNEVALUABLE")
        path = self._write_manifest(m)
        out = os.path.join(self.tmp, "unamended.md")
        rc = replay.run(["candidate", "--name", "unamended", "--scorer", BASELINE_SPEC,
                         "--manifest", path, "--out", out])
        self.assertEqual(rc, 1)
        self.assertIn("UNEVALUABLE %d" % len(EXPECTED_AMENDMENTS), self._read(out))

    def test_protected_status_refuses_a_shrunk_denominator(self):
        m = copy.deepcopy(replay.load_manifest())
        m["catch_runs"][replay._protected_runs(m)[0]]["guardrail"] = False
        with self.assertRaises(replay.ReplayError):
            replay.protected_status(_base_results(), m)

    def test_baseline_against_itself_regresses_nothing(self):
        base = _base_results()
        g = replay.guardrail(base, base, replay.load_manifest())
        self.assertEqual(len(g), replay.EXPECTED_PROTECTED)
        self.assertEqual([k for k, v in g.items() if v["status"] == "REGRESSED"], [])

    def test_mutation_planted_override_kills_every_catch(self):
        """Mutation proof 1: a catch-killing override is REJECTED (exit 1)."""
        out = os.path.join(self.tmp, "planted.md")
        rc = replay.run(["candidate", "--name", "planted", "--scorer", BASELINE_SPEC,
                         "--override", KILL_ALL, "--out", out])
        self.assertEqual(rc, 1)
        cand = replay.load_scorer(BASELINE_SPEC, json.loads(
            "{%s}" % KILL_ALL.replace("THRESHOLDS=", '"THRESHOLDS":')))
        cand_results = {k: v["result"] for k, v in replay.replay_all(cand, _runs()).items()}
        g = replay.guardrail(_base_results(), cand_results, replay.load_manifest())
        reproduced = [k for k, v in g.items() if v["status"] not in ("UNEVALUABLE", "AMENDED")]
        self.assertTrue(reproduced)
        self.assertTrue(all(g[k]["status"] == "REGRESSED" for k in reproduced))
        self.assertIn("REGRESSED %d" % len(reproduced), self._read(out))

    def _planted_manifest(self, amend=False):
        m = copy.deepcopy(replay.load_manifest())
        prot = replay.protected_status(_base_results(), m)
        victim = sorted(k for k, v in prot.items() if v["status"] == "REPRODUCED")[0]
        m["catch_runs"][victim]["site"]["file"] = "PLANTED/none.py"
        if amend:
            m.setdefault("guardrail_amendments", {})[victim] = {
                "ledger_entry": _ledger_numbers()[-1], "approved": "test", "reason": "test"}
        return m, victim, prot

    def test_mutation_planted_unreproducible_catch_fails_closed(self):
        """Mutation proof 2: an unreproducible protected catch turns the gate red."""
        m, victim, before = self._planted_manifest()
        before_u = sum(1 for v in before.values() if v["status"] == "UNEVALUABLE")
        path = self._write_manifest(m)
        out = os.path.join(self.tmp, "planted-catch.md")
        rc = replay.run(["candidate", "--name", "planted-catch", "--scorer", BASELINE_SPEC,
                         "--manifest", path, "--out", out])
        self.assertEqual(rc, 1)
        prot = replay.protected_status(_base_results(), m)
        self.assertEqual(prot[victim]["status"], "UNEVALUABLE")
        self.assertEqual(prot[victim]["basis"], "no-row-at-site")
        self.assertIn("UNEVALUABLE %d" % (before_u + 1), self._read(out))

    def test_amendment_turns_the_planted_catch_amended(self):
        m, victim, before = self._planted_manifest(amend=True)
        self.assertEqual(replay.check_manifest(m, _runs()), [])
        path = self._write_manifest(m)
        out = os.path.join(self.tmp, "amended.md")
        rc = replay.run(["candidate", "--name", "amended", "--scorer", BASELINE_SPEC,
                         "--manifest", path, "--out", out])
        before_u = sum(1 for v in before.values() if v["status"] == "UNEVALUABLE")
        before_r = sum(1 for v in before.values() if v["status"] == "REPRODUCED")
        before_a = sum(1 for v in before.values() if v["status"] == "AMENDED")
        self.assertEqual(rc, 1 if before_u else 0)
        text = self._read(out)
        self.assertIn("AMENDED %d" % (before_a + 1), text)
        self.assertIn("REPRODUCED %d / %d" % (before_r - 1, replay.EXPECTED_PROTECTED), text)
        self.assertEqual(replay.protected_status(_base_results(), m)[victim]["status"],
                         "AMENDED")

    def test_malformed_override_is_usage_error(self):
        out = os.path.join(self.tmp, "x.md")
        self.assertEqual(replay.run(["candidate", "--name", "x", "--scorer", BASELINE_SPEC,
                                     "--override", "BROKEN", "--out", out]), 2)
        self.assertEqual(replay.run(["candidate", "--name", "x", "--scorer", BASELINE_SPEC,
                                     "--override", "THRESHOLDS={bad", "--out", out]), 2)

    def test_report_shape(self):
        out = os.path.join(self.tmp, "self.md")
        replay.run(["candidate", "--name", "self", "--scorer", BASELINE_SPEC, "--out", out])
        text = self._read(out)
        for forbidden in ('"title"', "problem", "<result>"):
            self.assertNotIn(forbidden, text)
        self.assertIn("no rounding — exact fractions", text)
        self.assertLess(text.index("## Protected catches"), text.index("## Guardrail"))
        self.assertRegex(text, r"baseline \*\*\d+/18\*\* → candidate \*\*\d+/18\*\*")
        self.assertRegex(text, r"baseline \*\*\d+/6\*\* → candidate \*\*\d+/6\*\*")

    def test_baseline_report(self):
        out = os.path.join(self.tmp, "baseline.md")
        self.assertEqual(replay.run(["baseline", "--out", out]), 0)
        text = self._read(out)
        for forbidden in ('"title"', "problem", "<result>"):
            self.assertNotIn(forbidden, text)
        sections = re.findall(r"^## (.+)$", text, re.MULTILINE)
        self.assertTrue(sections[0].startswith("Protected catches"), sections)
        self.assertIn("REPRODUCED %d / %d · UNEVALUABLE 0 · AMENDED %d"
                      % (replay.EXPECTED_PROTECTED - EXPECTED_AMENDED,
                         replay.EXPECTED_PROTECTED, EXPECTED_AMENDED), text)
        self.assertIn("**%d/%d exact**" % (EXPECTED_EXACT_BASELINE, replay.EXPECTED_SCOREABLE),
                      text)
        cov = text.split("## Transcript coverage (disclosed)", 1)[1].split("\n## ", 1)[0]
        listed = re.findall(r"^- (\S+) — (.+)$", cov, re.MULTILINE)
        self.assertEqual(listed, [(p, replay.CODEX_AGENT) for p in CODEX_WRITE_ONLY_RUNS])
        self.assertIn("12 / %d runs carry a session transcript" % replay.EXPECTED_SCOREABLE, cov)


# --------------------------------------------------------------------------
# Security
# --------------------------------------------------------------------------

class TestSecurity(_TmpDirCase):

    def test_path_outside_scripts_dir_is_refused(self):
        outside = os.path.join(self.tmp, "score.py")
        shutil.copy(os.path.join(HERE, "score.py"), outside)
        with self.assertRaises(replay.ReplayError) as ctx:
            replay.load_scorer("path:" + outside)
        self.assertIn("refused", str(ctx.exception))

    def test_symlink_escaping_scripts_dir_is_refused(self):
        outside = os.path.join(self.tmp, "score.py")
        shutil.copy(os.path.join(HERE, "score.py"), outside)
        link = os.path.join(HERE, "zz_test_replay_link.py")
        try:
            os.symlink(outside, link)
            with self.assertRaises(replay.ReplayError):
                replay.load_scorer("path:" + link)
        finally:
            if os.path.lexists(link):
                os.remove(link)

    def test_path_inside_scripts_dir_loads(self):
        mod = replay.load_scorer("path:" + os.path.join(replay.HERE, "score.py"))
        self.assertTrue(callable(mod.run))

    def test_unknown_override_name_is_refused(self):
        with self.assertRaises(replay.ReplayError):
            replay.load_scorer(BASELINE_SPEC, {"NO_SUCH_CONSTANT": 1})

    def test_report_never_carries_a_planted_title(self):
        out = os.path.join(self.tmp, "r.md")
        finding = {"agent": "security", "file": "a.py", "line": 3, "band": "critical",
                   "orchestrator_score": 97, "stable_hash": "a" * 64,
                   "title": "PLANTED-TITLE-STRING", "problem": "PLANTED-PROBLEM-TEXT"}
        replay.write_report(out, [("#", "t")], [
            {"heading": "rows", "body": ["x"], "tables": [("### r", [finding])]}])
        text = self._read(out)
        self.assertNotIn("PLANTED-TITLE-STRING", text)
        self.assertNotIn("PLANTED-PROBLEM-TEXT", text)
        self.assertIn("| security | a.py | 3 | critical | 97 | aaaaaaaaaaaa |", text)


# --------------------------------------------------------------------------
# Module conventions
# --------------------------------------------------------------------------

class TestImportSet(unittest.TestCase):

    ALLOWED = {"argparse", "hashlib", "importlib", "json", "os", "re", "shutil",
               "subprocess", "sys", "tempfile", "time"}

    def _tree(self):
        with open(REPLAY_PY, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_imports_are_exactly_the_allowed_set(self):
        found = set()
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                for a in node.names:
                    found.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
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
            self.assertIn("timeout", kw, "subprocess.run at line %d has no timeout"
                          % node.lineno)
            self.assertEqual(kw["timeout"].value, 120)
        self.assertGreater(calls, 0, "found no subprocess.run calls -- test is vacuous")

    def test_no_gateable_subset(self):
        with open(REPLAY_PY, encoding="utf-8") as fh:
            self.assertNotIn("gateable", fh.read())


if __name__ == "__main__":
    unittest.main()
