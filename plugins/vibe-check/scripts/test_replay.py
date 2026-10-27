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

# The 12 Phase-40 session transcripts are gitignored: they carry the owner's private
# instructions, so they exist only in the primary checkout. A linked worktree (a batchsnap
# snapshot is one) never has them, by construction. Tests that read them expect ZERO
# transcripts there and all 12 in the primary checkout, so a transcript missing from the
# primary checkout still fails.
IN_LINKED_WORKTREE = os.path.isfile(os.path.join(REPO_ROOT, ".git"))
EXPECTED_TRANSCRIPTS = 0 if IN_LINKED_WORKTREE else 12


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
        self.assertEqual(len(with_t), EXPECTED_TRANSCRIPTS)
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

    @unittest.skipIf(IN_LINKED_WORKTREE, "Phase-40 transcripts are local-only (gitignored); "
                     "a linked worktree has none to recover from")
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
        want = [] if IN_LINKED_WORKTREE else [(p, replay.CODEX_AGENT)
                                              for p in CODEX_WRITE_ONLY_RUNS]
        self.assertEqual(listed, want)
        self.assertIn("%d / %d runs carry a session transcript"
                      % (EXPECTED_TRANSCRIPTS, replay.EXPECTED_SCOREABLE), cov)


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



class TestMethodRecordOrdering(unittest.TestCase):
    """D-15: the calibration method record was committed BEFORE any Wave-1
    candidate replay report. Each existing candidate report's FIRST commit must
    descend from (and differ from) CALIBRATION-v2.10.md's first commit. At least
    one candidate report must exist: an empty set fails, it never skips."""

    CALIBRATION = "docs/design/b3-ground-truth/CALIBRATION-v2.10.md"
    CANDIDATES = tuple(
        "docs/design/b3-ground-truth/REPLAY-REPORT-phase41-%s.md" % name
        for name in ("b-sev", "b-reweight", "h-lane", "combined"))

    def _first_commit(self, rel):
        res = _git("log", "--format=%H", "--reverse", "--", rel)
        self.assertEqual(res.returncode, 0, res.stderr)
        lines = res.stdout.split()
        return lines[0] if lines else None

    def test_every_candidate_report_follows_the_method_record(self):
        calib = self._first_commit(self.CALIBRATION)
        self.assertIsNotNone(calib, "CALIBRATION-v2.10.md has no commit")
        checked = 0
        for rel in self.CANDIDATES:
            if not os.path.exists(os.path.join(REPO_ROOT, rel)):
                continue
            with self.subTest(report=rel):
                first = self._first_commit(rel)
                self.assertIsNotNone(first, "%s exists but is not committed" % rel)
                self.assertNotEqual(first, calib,
                                    "%s landed in the method-record commit" % rel)
                anc = _git("merge-base", "--is-ancestor", calib, first)
                self.assertEqual(anc.returncode, 0,
                                 "%s predates the method record" % rel)
                checked += 1
        self.assertGreater(checked, 0, "no candidate replay report exists -- vacuous")


# --------------------------------------------------------------------------
# Complete-output diff (byte-identity evidence)
# --------------------------------------------------------------------------

# Each mutant is score.py with ONE anchored substitution; the test asserts the
# substitution changed the text, so a moved anchor fails instead of passing vacuously.
_MUTANTS = {
    "score": ("    return max(0, min(100, pre_clamp))\n",
              "    return max(0, min(100, pre_clamp)) + 1\n"),
    # Moves rows across band floors so whole findings (and their titles) appear
    # and disappear: the title-digest rule then has real title paths to guard.
    "drop": ("    return max(0, min(100, pre_clamp))\n",
             "    return max(0, min(100, pre_clamp - 40))\n"),
    "key": ("    return _sanitize_nonfinite(out)\n",
            "    out[\"probe\"] = 1\n    return _sanitize_nonfinite(out)\n"),
    # Member records carry no orchestrator_score (_MEMBER_EXCLUDED_KEYS), so the
    # member-only mutant shifts each member record's own line in the group loop.
    "member": ("                    changed_line_ranges)\n"
               "            members.append(ref)\n"
               "            kept_by_ident[ident] = ref\n",
               "                    changed_line_ranges)\n"
               "            ref[\"line\"] = (ref[\"line\"] or 0) + 1\n"
               "            members.append(ref)\n"
               "            kept_by_ident[ident] = ref\n"),
    "status": ("            survivor[\"status\"] = \"new\"\n",
               "            survivor[\"status\"] = \"persisted\"\n"),
    "value": ("        \"scored_by_script\": True,\n",
              "        \"scored_by_script\": 1,\n"),
}


def _header_value(text, label):
    m = re.search(r"^- %s: (.*)$" % re.escape(label), text, re.MULTILINE)
    if m is None:
        raise AssertionError("report header has no %r line" % label)
    return m.group(1)


def _section_tables(text):
    """{heading: (before rows, after rows)} for every per-run section of a diff report."""
    out = {}
    for chunk in text.split("\n## ")[1:]:
        lines = chunk.splitlines()
        heading, current, tables = lines[0], None, {"before": [], "after": []}
        for ln in lines[1:]:
            if ln in ("before", "after"):
                current = ln
            elif current and ln.startswith("| ") and not ln.startswith("| agent |"):
                tables[current].append(ln)
        out[heading] = (tables["before"], tables["after"])
    return out


class TestDiffMode(_TmpDirCase):

    def _mutant(self, kind):
        with open(os.path.join(REPO_ROOT, replay.SCORE_REL), encoding="utf-8") as fh:
            original = fh.read()
        old, new = _MUTANTS[kind]
        self.assertEqual(original.count(old), 1, "mutation anchor moved: " + kind)
        text = original.replace(old, new)
        self.assertNotEqual(text, original)
        path = os.path.join(HERE, "_score_mutant_%s_%d.py" % (kind, os.getpid()))
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return "path:" + path

    def _diff(self, cand, roots="manifest", allow=None, name="d.md"):
        out = os.path.join(self.tmp, name)
        rc = replay._cmd_diff("rev:HEAD", cand, out, roots, allow)
        return rc, self._read(out), out

    def _assert_rows_identical(self, text):
        tables = _section_tables(text)
        self.assertGreater(len(tables), 0)
        self.assertGreater(sum(len(b) for b, _a in tables.values()), 0,
                           "no rows in any differing run -- row comparison is vacuous")
        for heading, (before, after) in tables.items():
            self.assertEqual(before, after, "row projection moved in " + heading)

    def _sidecar(self, out):
        with open(out + ".changes.json", encoding="utf-8") as fh:
            return json.load(fh)

    def _write_allow(self, data, name="allow.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        return path

    def test_identical_specs_exit_zero(self):
        rc, text, _out = self._diff("rev:HEAD")
        self.assertEqual(rc, 0)
        self.assertEqual(_header_value(text, "runs differing"), "0")
        self.assertEqual(_header_value(text, "runs with unallowed differences"), "0")
        self.assertEqual(int(_header_value(text, "runs compared")), replay.EXPECTED_SCOREABLE)

    def test_planted_score_mutation_exits_one_with_row_diff(self):
        rc, text, _out = self._diff(self._mutant("score"))
        self.assertEqual(rc, 1)
        self.assertGreater(int(_header_value(text, "runs with unallowed differences")), 0)
        self.assertRegex(text, r"(?m)^- UNALLOWED findings\[[^\]]+\]\.orchestrator_score: ")
        tables = _section_tables(text)
        self.assertTrue(any(b != a for b, a in tables.values()),
                        "a score mutation must move the row projection")

    def test_key_only_mutation_is_reported(self):
        rc, text, _out = self._diff(self._mutant("key"))
        self.assertEqual(rc, 1)
        self.assertIn("UNALLOWED probe: (absent) -> 1", text)
        self.assertEqual(int(_header_value(text, "runs differing")), replay.EXPECTED_SCOREABLE)
        self._assert_rows_identical(text)

    def test_member_only_mutation_exits_one(self):
        rc, text, _out = self._diff(self._mutant("member"), roots="all")
        self.assertEqual(rc, 1)
        # --roots all must really walk every archive root, not the manifest three.
        self.assertEqual(int(_header_value(text, "runs compared")),
                         len(replay.iter_runs(roots=replay.DIFF_ROOTS)))
        self.assertRegex(text, r"(?m)^## runs-v2\.1[01]-phase(41|43|49)/")
        self.assertRegex(text, r"(?m)^## \.\./reachability-dev/runs-phase53-dev/final/")
        self.assertGreater(int(_header_value(text, "runs differing")), 0,
                           "member mutant changed nothing -- test would be vacuous")
        self.assertRegex(text, r"(?m)^- UNALLOWED findings\[[^\]]+\]\.members\[\d+\]\.line: ")
        self.assertNotRegex(text, r"(?m)^- (UNALLOWED )?findings\[[^\]]+\]\.(line|band|"
                                  r"orchestrator_score|file|agent): ")
        self._assert_rows_identical(text)

    def test_status_only_mutation_exits_one(self):
        rc, text, _out = self._diff(self._mutant("status"))
        self.assertEqual(rc, 1)
        self.assertRegex(text, r"(?m)^- UNALLOWED findings\[[^\]]+\]\.status: new -> persisted$")
        self._assert_rows_identical(text)

    def test_existing_key_value_mutation_exits_one(self):
        rc, text, _out = self._diff(self._mutant("value"))
        self.assertEqual(rc, 1)
        self.assertIn("UNALLOWED scored_by_script: True -> 1", text)

    def test_sidecar_allowance_round_trip(self):
        cand = self._mutant("score")
        rc, _text, out = self._diff(cand)
        self.assertEqual(rc, 1)
        rc2, text2, _out2 = self._diff(cand, allow=out + ".changes.json", name="d2.md")
        self.assertEqual(rc2, 0)
        self.assertEqual(_header_value(text2, "runs with unallowed differences"), "0")
        self.assertEqual(_header_value(text2, "allowances unused"), "0")
        self.assertGreater(int(_header_value(text2, "runs differing")), 0)
        self.assertEqual(_header_value(text2, "runs differing (allowed)"),
                         _header_value(text2, "runs differing"))
        self.assertNotIn("UNALLOWED", text2)

    def _int_entry(self, data, field):
        for i, e in enumerate(data["allow"]):
            if e["path"].endswith(".orchestrator_score") and isinstance(e[field], int):
                return i
        raise AssertionError("no int orchestrator_score entry in the sidecar")

    def test_tampered_allowance_fails(self):
        cand = self._mutant("score")
        _rc, _t, out = self._diff(cand)
        data = self._sidecar(out)
        i = self._int_entry(data, "after")
        data["allow"][i]["after"] += 1
        run_path = data["allow"][i]["run"]
        rc, text, _o = self._diff(cand, allow=self._write_allow(data), name="d2.md")
        self.assertEqual(rc, 1)
        self.assertEqual(_header_value(text, "runs with unallowed differences"), "1")
        self.assertEqual(_header_value(text, "allowances unused"), "1")
        section = text.split("\n## " + run_path + "\n", 1)[1].split("\n## ", 1)[0]
        self.assertEqual(section.count("UNALLOWED "), 1)

    def test_partial_allowance_fails(self):
        cand = self._mutant("score")
        _rc, _t, out = self._diff(cand)
        data = self._sidecar(out)
        del data["allow"][0]
        rc, text, _o = self._diff(cand, allow=self._write_allow(data), name="d2.md")
        self.assertEqual(rc, 1)
        self.assertEqual(_header_value(text, "runs with unallowed differences"), "1")
        self.assertEqual(_header_value(text, "allowances unused"), "0")

    def test_allowance_requires_exact_before(self):
        cand = self._mutant("score")
        _rc, _t, out = self._diff(cand)
        data = self._sidecar(out)
        i = self._int_entry(data, "before")
        data["allow"][i]["before"] += 1
        rc, text, _o = self._diff(cand, allow=self._write_allow(data), name="d2.md")
        self.assertEqual(rc, 1)
        self.assertEqual(_header_value(text, "allowances unused"), "1")

    def test_allowance_for_another_run_does_not_apply(self):
        cand = self._mutant("score")
        _rc, _t, out = self._diff(cand)
        data = self._sidecar(out)
        data["allow"][0]["run"] = "runs/not-a-run/run-1"
        rc, text, _o = self._diff(cand, allow=self._write_allow(data), name="d2.md")
        self.assertEqual(rc, 1)
        self.assertEqual(_header_value(text, "allowances unused"), "1")

    def test_unflattenable_difference_is_named_canonical(self):
        # A dotted key and a nested key flatten to the same path with the same
        # value; only the canonical-JSON ground truth can see the difference.
        a = {"scored_by_script": True, "findings": [], "x": {"b.c": 1}}
        b = {"scored_by_script": True, "findings": [], "x": {"b": {"c": 1}}}
        self.assertEqual(replay._flatten_output(a), replay._flatten_output(b))
        changes = replay._changes(a, b)
        self.assertEqual([c["path"] for c in changes], ["__canonical__"])
        self.assertTrue(all(str(c[k]).startswith("sha256:") for c in changes
                            for k in ("before", "after")))
        self.assertEqual(replay._changes(a, json.loads(json.dumps(a))), [])

    def test_malformed_allowance_is_replay_error(self):
        path = self._write_allow({"allow": [{"run": "r", "path": "p", "before": 1}]})
        with self.assertRaises(replay.ReplayError):
            replay._load_allowances(path)
        extra = self._write_allow({"allow": [{"run": "r", "path": "p", "before": 1,
                                              "after": 2, "glob": "*"}]}, "extra.json")
        with self.assertRaises(replay.ReplayError):
            replay._load_allowances(extra)
        rc = replay.run(["diff", "--base", "rev:HEAD", "--scorer", "rev:HEAD",
                         "--out", os.path.join(self.tmp, "x.md"), "--roots", "manifest",
                         "--allow", path])
        self.assertEqual(rc, 2)

    def test_all_roots_scans_more_runs_than_manifest(self):
        all_runs = replay.iter_runs(roots=replay.DIFF_ROOTS)
        self.assertGreater(len(all_runs), replay.EXPECTED_SCOREABLE)
        self.assertEqual(len(replay.iter_runs()), replay.EXPECTED_SCOREABLE)
        prefixes = {r["rel_path"].split("/", 1)[0] for r in all_runs}
        for root in ("runs-v2.10-phase41", "runs-v2.10-phase43", "runs-v2.11-phase49"):
            self.assertIn(root, prefixes)

    def test_dev_rehearsal_root_is_diff_only(self):
        # D-19: the signed-off rehearsal outcomes are compared byte-for-byte by
        # `diff --roots all`, and never enter the census or the guardrail.
        dev = "docs/design/reachability-dev/runs-phase53-dev/final"
        self.assertIn(dev, replay.DIFF_ROOTS)
        self.assertNotIn(dev, replay.ARCHIVE_ROOTS)
        self.assertEqual(replay._DIFF_ROOT_SETS["manifest"], replay.ARCHIVE_ROOTS)
        self.assertEqual(replay.EXPECTED_SCOREABLE, 66)
        self.assertEqual(replay.EXPECTED_PROTECTED, 26)
        self.assertEqual(len(replay.iter_runs()), replay.EXPECTED_SCOREABLE)
        base = os.path.join(REPO_ROOT, dev)
        on_disk = sorted("%s/%s" % (case, run) for case in os.listdir(base)
                         if os.path.isdir(os.path.join(base, case))
                         for run in os.listdir(os.path.join(base, case))
                         if replay.RUN_DIR_RE.match(run)
                         and os.path.isfile(os.path.join(base, case, run, "state.json")))
        self.assertGreater(len(on_disk), 0)
        prefix = "../reachability-dev/runs-phase53-dev/final/"
        walked = sorted(r["rel_path"][len(prefix):] for r in replay.iter_runs(roots=replay.DIFF_ROOTS)
                        if r["rel_path"].startswith(prefix))
        self.assertEqual(walked, on_disk)

    def test_report_and_sidecar_have_no_titles(self):
        rc, text, out = self._diff(self._mutant("drop"), roots="all")
        self.assertEqual(rc, 1)
        sidecar = self._read(out + ".changes.json")
        self.assertIn(".title", sidecar, "no title path changed -- digest rule untested")
        titles = set()
        for run in replay.iter_runs(roots=replay.DIFF_ROOTS):
            for p in run["state"].get("passes") or []:
                for f in p.get("findings") or []:
                    t = f.get("title") if isinstance(f, dict) else None
                    if isinstance(t, str) and t.strip():
                        titles.add(t)
        self.assertGreater(len(titles), 0)
        for blob in (text, sidecar):
            self.assertNotIn('"title"', blob)
            for t in titles:
                self.assertNotIn(t, blob)


# --------------------------------------------------------------------------
# Same-line corroboration: three archived regression cases
# --------------------------------------------------------------------------

# Pre-53 scorer (score.py at 230332e): the row-wide second opinion it gave is
# what lifted each of the three Codex findings below to critical/100.
PRE_SAME_LINE_SPEC = "blob:d4f9fb14aea5f934a12dadf34e357626f7047ba5"
# run -> (file, Codex line, row stable_hash[:12]). Owner-approved outcome under
# the same-line rule: each Codex finding fires at warning/94, not critical.
#   A1: the only Claude member that clears the cutoff alone (bugs L108) reports
#       a different defect; the notes on L107 are too weak to count.
#   A2: KNOWN CONSERVATIVE LIMITATION. Codex (L232) and the qualifying Claude
#       members (L233) report the same defect, anchored on different lines of
#       one multi-line statement, so the pair is not credited.
#   A3: the qualifying Claude member (architecture L232) is at the same code
#       but disputes the harm; the L233 note is below the cutoff alone.
SAME_LINE_CASES = {
    "runs-v2.10-phase43/first/should-quiet-4/run-3":
        ("triggarr/models/config.py", 107, "fedecf9ededf"),
    "runs-v2.10-phase43/first/triggarr-secret-in-logs/run-1":
        ("triggarr/clients/base.py", 232, "13f543dd935e"),
    "runs-v2.10/triggarr-secret-in-logs/run-1":
        ("triggarr/clients/base.py", 233, "12fe298fc07e"),
}
# A scorer that credits a Codex/Claude pair one line apart: the "adjacent
# lines" widening the owner ruled out.
_OFF_LINE_CREDIT = (
    '            if _as_line(b.get("line")) == a_line:\n',
    '            b_line = _as_line(b.get("line"))\n'
    '            if b_line is not None and abs(b_line - a_line) <= 1:\n',
)


class TestPhase53SameLineRegressionCases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        runs = {r["rel_path"]: r for r in replay.iter_runs(roots=replay.DIFF_ROOTS)}
        cls.envelopes = {}
        for rel in SAME_LINE_CASES:
            assert rel in runs, "archived regression run missing: " + rel
            cls.envelopes[rel] = replay.reconstruct_envelope(runs[rel])[0]

    def _scorer(self, mutate=False):
        if not mutate:
            return replay.load_scorer("path:" + os.path.join(REPO_ROOT, replay.SCORE_REL))
        with open(os.path.join(REPO_ROOT, replay.SCORE_REL), encoding="utf-8") as fh:
            original = fh.read()
        old, new = _OFF_LINE_CREDIT
        self.assertEqual(original.count(old), 1, "mutation anchor moved: off-line credit")
        path = os.path.join(HERE, "_score_mutant_offline_%d.py" % os.getpid())
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(original.replace(old, new))
        return replay.load_scorer("path:" + path)

    def _codex_row(self, scorer, rel):
        result = replay.replay_run(scorer, self.envelopes[rel])
        file_, line, hash12 = SAME_LINE_CASES[rel]
        rows = [f for f in result.get("findings", [])
                if f.get("agent") == replay.CODEX_AGENT and f.get("file") == file_
                and f.get("line") == line]
        self.assertEqual(len(rows), 1, rel)
        self.assertEqual(rows[0]["stable_hash"][:12], hash12, rel)
        return result, rows[0]

    def _assert_approved_outcome(self, scorer):
        # No subTest here: the mutation partner needs the first failure to raise.
        for rel in SAME_LINE_CASES:
            result, row = self._codex_row(scorer, rel)
            self.assertTrue(replay.fires(result), rel)
            self.assertEqual((row["band"], row["orchestrator_score"]),
                             ("warning", 94), rel)

    def test_each_case_fires_at_warning_94(self):
        self._assert_approved_outcome(self._scorer())

    def test_pre_same_line_scorer_gave_critical_100(self):
        base = replay.load_scorer(PRE_SAME_LINE_SPEC)
        for rel in SAME_LINE_CASES:
            with self.subTest(run=rel):
                _result, row = self._codex_row(base, rel)
                self.assertEqual((row["band"], row["orchestrator_score"]),
                                 ("critical", 100), rel)

    def test_a2_pair_sits_on_adjacent_lines_of_one_statement(self):
        # The limitation's shape: no Claude member shares Codex's line, and the
        # Claude members that clear the cutoff alone sit on the next line.
        rel = "runs-v2.10-phase43/first/triggarr-secret-in-logs/run-1"
        _result, row = self._codex_row(self._scorer(), rel)
        lanes = [(m.get("agent"), m.get("line")) for m in row["members"]
                 if m.get("agent") != replay.CODEX_AGENT]
        self.assertNotIn(232, [ln for _a, ln in lanes])
        self.assertIn(("architecture", 233), lanes)
        self.assertIn(("compliance", 233), lanes)

    def test_off_line_credit_mutation_trips(self):
        # Mutation partner: crediting pairs one line apart lifts all three
        # Codex findings back to critical, so the pinned outcome fails.
        mutant = self._scorer(mutate=True)
        for rel in SAME_LINE_CASES:
            with self.subTest(run=rel):
                _result, row = self._codex_row(mutant, rel)
                self.assertEqual(row["band"], "critical", rel)
        with self.assertRaises(AssertionError):
            self._assert_approved_outcome(mutant)


if __name__ == "__main__":
    unittest.main()
