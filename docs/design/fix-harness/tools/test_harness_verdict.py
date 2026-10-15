"""Tests for harness_verdict: the FLOW-02 verdict judged on committed HEAD,
executed only inside Seatbelt on a read-only export, with the repair boundary
first and every obligation that ever entered the workflow reconciled.

Each negative control is run against the real verdict and must FAIL; each
mutant patches one lock, re-runs a control, and asserts the outcome flips —
so every lock is shown to be load-bearing.

Run with bare `pytest -q` from this directory.
"""

import contextlib
import copy as copymod
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness_fixture as hf  # noqa: E402
import harness_seed as hs  # noqa: E402
import harness_sentinels as hsn  # noqa: E402
import harness_verdict as hv  # noqa: E402

CASE = "py-clamp-01"
RECIPE = hf.load_recipe(CASE)
with open(hf.KEYS_DIR / ("%s.json" % CASE), "r", encoding="utf-8") as _fh:
    KEY = json.load(_fh)

SANDBOX_OK = (sys.platform == "darwin"
              and os.access("/usr/bin/sandbox-exec", os.X_OK))
STATE_SHAPE = hf.PLUGIN_SCRIPTS_DIR / "state_shape.py"
CARRY = hf.PLUGIN_SCRIPTS_DIR / "carry_state.py"
PY = os.path.realpath(sys.executable)

FIXED = RECIPE["fixed_file"]
UNTOUCHED = RECIPE["untouched_file"]
HUNK_S, HUNK_E = RECIPE["hunk_lines"]
CASE_DIR = hf.FIXTURES_DIR / CASE
BASE_FIXED = (CASE_DIR / "base" / FIXED).read_bytes()
DEFECT_FIXED = (CASE_DIR / "defect" / FIXED).read_bytes()
BASE_UNTOUCHED = (CASE_DIR / "base" / UNTOUCHED).read_bytes()
# The distant helper: a docstring line well away from the hunk.
HELPER_LINE = RECIPE["sentinels"]["unstaged_fixed"]["after_line"] + 3
TEST_FILES = sorted("tests/" + p.name
                    for p in (CASE_DIR / "base" / "tests").glob("test*.py"))
T_FILE = TEST_FILES[0]
GOOD_SUBJECT = "fix(review-pass-1): clamp keeps hi at the upper bound"
REASON = "harness: not the seeded finding"


def H(name):
    return hashlib.sha256(name.encode("utf-8")).hexdigest()


def sha7(h):
    return h[:7]


# --------------------------------------------------------------------------- #
# git + file helpers (all test-side; the verdict never writes the copy)
# --------------------------------------------------------------------------- #
def _git(root, *args, data=None, env=None, check=True):
    proc = subprocess.run(["git", *args], cwd=root, input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=60, env=env)
    if check and proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (args, proc.stderr))
    return proc.stdout.decode("utf-8", "replace")


def _lines(data):
    return data.splitlines(keepends=True)


def with_hunk(data, new_hunk):
    """`data` (the defect file) with lines [HUNK_S, HUNK_E] replaced."""
    ls = _lines(data)
    return b"".join(ls[:HUNK_S - 1] + [x.encode("utf-8") for x in new_hunk]
                    + ls[HUNK_E:])


FIX_HUNK = [x.decode("utf-8") for x in _lines(BASE_FIXED)[HUNK_S - 1:HUNK_E]]
FIXED_BYTES = with_hunk(DEFECT_FIXED, FIX_HUNK)


def helper_changed(data):
    """`data` with the distant helper's docstring line altered."""
    ls = _lines(data)
    line = ls[HELPER_LINE - 1]
    assert b'"""' in line, line
    ls[HELPER_LINE - 1] = line.replace(b"Return a short", b"Return a brief")
    assert ls[HELPER_LINE - 1] != line
    return b"".join(ls)


def commit_files(root, files, subject, worktree=True):
    """Commit `files` ({path: bytes|None}) on top of HEAD without touching any
    other index entry; mirror only those paths into the real index (and the
    worktree when asked). Returns the new commit sha."""
    tmp = tempfile.mkdtemp(prefix="vt-index-")
    try:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(tmp, "index"))
        _git(root, "read-tree", "HEAD", env=env)
        blobs = {}
        for path, data in files.items():
            if data is None:
                _git(root, "update-index", "--force-remove", path, env=env)
                continue
            blob = _git(root, "hash-object", "-w", "--stdin", data=data).strip()
            blobs[path] = blob
            _git(root, "update-index", "--add", "--cacheinfo",
                 "100644,%s,%s" % (blob, path), env=env)
        tree = _git(root, "write-tree", env=env).strip()
        sha = _git(root, "commit-tree", tree, "-p", "HEAD", "-m",
                   subject).strip()
        _git(root, "update-ref", "HEAD", sha)
    finally:
        shutil.rmtree(tmp)
    for path, data in files.items():
        if data is None:
            _git(root, "update-index", "--force-remove", path)
            if worktree and os.path.exists(os.path.join(root, path)):
                os.unlink(os.path.join(root, path))
        else:
            _git(root, "update-index", "--add", "--cacheinfo",
                 "100644,%s,%s" % (blobs[path], path))
            if worktree:
                Path(root, path).write_bytes(data)
    return sha


def plain_run(argv, cwd, env=None):
    """An UNSANDBOXED run — only ever on a throwaway export, to prove a
    payload really escapes or tampers when nothing contains it."""
    argv = list(argv)
    if argv and argv[0] in ("python3", "python"):
        argv[0] = PY
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          timeout=120, env=env if env is not None
                          else dict(os.environ))


@contextlib.contextmanager
def throwaway_export(copy):
    scratch = tempfile.mkdtemp(prefix="vt-export-")
    try:
        os.mkdir(os.path.join(scratch, "runtime"))
        yield os.path.realpath(scratch), hv.export_head(copy, scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def recorder(target_name, module=hv):
    """Patch `module.target_name` with a wrapper that records (args, kwargs,
    result); returns (patcher, calls)."""
    real = getattr(module, target_name)
    calls = []

    def wrapper(*a, **k):
        result = real(*a, **k)
        calls.append((a, k, result))
        return result
    return mock.patch.object(module, target_name, wrapper), calls


# --------------------------------------------------------------------------- #
# state builders (shapes from future-schema.json and test_carry_state.py)
# --------------------------------------------------------------------------- #
def snap(at_pass, band, file, line, content):
    return {"at_pass": at_pass, "band": band, "canonical_line_content": content,
            "file": file, "line": line}


def evidence(f):
    return {k: f["snapshot"][k]
            for k in ("file", "line", "canonical_line_content", "band")}


class States:
    """Builds well-formed envelopes from the real seeded state."""

    def __init__(self, seed_doc):
        self.seed = seed_doc
        self.seed_pass = seed_doc["passes"][0]
        self.seed_finding = self.seed_pass["findings"][0]

    def finding(self, h, band, file, line, status="persisted", at_pass=1,
                members=None):
        f = copymod.deepcopy(self.seed_finding)
        content = "x = %d  # %s" % (line if isinstance(line, int) else 0,
                                    h[:7])
        f.update(stable_hash=h, band=band, file=file, line=line,
                 status=status, title="finding %s" % h[:7],
                 canonical_line_content=content, current_code=content,
                 snapshot=snap(at_pass, band, file, line, content))
        f.pop("members", None)
        if members is not None:
            f["members"] = members
        return f

    def seeded(self, status="persisted"):
        f = copymod.deepcopy(self.seed_finding)
        f["status"] = status
        return f

    def member(self, h, band, file, line):
        m = copymod.deepcopy(self.seed_finding["members"][0])
        content = "y = %d  # %s" % (line, h[:7])
        m.update(file=file, line=line, title="member %s" % h[:7])
        m["obligation"] = {"stable_hash": h, "band": band,
                           "orchestrator_score": 80,
                           "attribution": ["logic"],
                           "snapshot": snap(1, band, file, line, content)}
        return m

    @staticmethod
    def resolved(f, at_pass, head, file=None):
        return {"file": file or f["file"], "line": f["line"],
                "title": f["title"], "band": f["band"],
                "stable_hash": f["stable_hash"], "agent": f["agent"],
                "resolution": {"source": "recheck", "agents": [f["agent"]],
                               "verdict": "resolved", "head_sha": head,
                               "at_pass": at_pass,
                               "reason": "gone on rerun"}}

    def pass_entry(self, n, head, findings, resolved=None):
        p = copymod.deepcopy(self.seed_pass)
        p.update(pass_number=n, head_sha=head, findings=findings)
        p.pop("resolved", None)
        if resolved is not None:
            p["resolved"] = resolved
        return p

    def state(self, passes, decisions=None, fix_verdicts=None):
        s = {"medium_acknowledgments": {},
             "passes": [copymod.deepcopy(self.seed_pass)] + passes}
        if decisions is not None:
            s["decisions"] = decisions
        if fix_verdicts is not None:
            s["fix_verdicts"] = fix_verdicts
        return s


def decision(f, reason=REASON, kind="defer", at_pass=2):
    return {"decision": kind, "reason": reason, "at_pass": at_pass,
            "evidence": evidence(f)}


# --------------------------------------------------------------------------- #
# the shared copy: built, seeded, ready for a run
# --------------------------------------------------------------------------- #
class _Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self.copy = hf.build_copy(RECIPE, "default",
                                  os.path.join(self.tmp, "c"))
        self.seed_path = hs.seed_state(self.copy, KEY, "default")
        self.S = self.seed_path.stable_hash
        self.pre = self.copy.head_sha
        with open(self.seed_path, "r", encoding="utf-8") as fh:
            self.seed_doc = json.load(fh)
        self.st = States(self.seed_doc)
        self.states_dir = os.path.join(self.tmp, "states")
        os.mkdir(self.states_dir)
        self._n = 0

    def tearDown(self):
        self._tmp.cleanup()

    # -- writing and observing states -------------------------------------- #
    def write_state(self, state):
        self._n += 1
        path = os.path.join(self.states_dir, "s%d.json" % self._n)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
        proc = subprocess.run([sys.executable, str(STATE_SHAPE), path,
                               "--schema", "future"], capture_output=True,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 0,
                         "test state is malformed: %s" % proc.stderr)
        return path

    def ledger(self, *later):
        """Snapshot 0 = the real seeded state, marked seeded; then each
        (state, label, head) as a further observation."""
        led = hv.ObligationLedger()
        s0 = hv.snapshot_obligations(self.seed_path)
        led.observe(s0, "seed", self.pre)
        led.mark_seeded(s0["hashes"])
        for state, label, head in later:
            led.observe(hv.snapshot_obligations(self.write_state(state)),
                        label, head)
        return led

    def finalize(self, archived, review=True, root_review=False):
        self.write_state(archived)  # shape-check before use
        if review:
            Path(self.copy.root, ".turingmind", "REVIEW.md").write_text(
                "# Review\n\nfinalized\n", encoding="utf-8")
        if root_review:
            Path(self.copy.root, "REVIEW.md").write_text(
                "# Review\n\nfinalized\n", encoding="utf-8")
        with open(str(self.seed_path) + ".archived-test", "w",
                  encoding="utf-8") as fh:
            json.dump(archived, fh, indent=2, sort_keys=True)
        os.unlink(self.seed_path)

    def counts(self, state, head_blobs=None):
        blobs = os.path.join(self.tmp, "blobs.json")
        with open(blobs, "w", encoding="utf-8") as fh:
            json.dump(head_blobs or {}, fh)
        proc = subprocess.run([sys.executable, str(CARRY), "finalize-counts",
                               "--head-blobs", blobs],
                              input=json.dumps(state), capture_output=True,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    # -- the canonical shapes ----------------------------------------------- #
    def commit_fix(self, hunk=None, extra=None, subject=GOOD_SUBJECT,
                   data=None):
        files = {FIXED: data if data is not None
                 else with_hunk(DEFECT_FIXED, hunk or FIX_HUNK)}
        files.update(extra or {})
        return commit_files(self.copy.root, files, subject)

    def pass2_resolved(self, head, findings=(), resolved_extra=()):
        return self.st.pass_entry(
            2, head, list(findings),
            [States.resolved(self.st.seeded(), 2, head)]
            + list(resolved_extra))

    def happy(self, head=None, extra_open=()):
        """The happy finalize shape: S resolved on pass 2, nothing else open;
        a consistent ledger; REVIEW.md written; state archived."""
        head = head or _git(self.copy.root, "rev-parse", "HEAD").strip()
        state = self.st.state([self.pass2_resolved(head)])
        led = self.ledger((state, "turn_end", head))
        archived = copymod.deepcopy(state)
        archived["passes"][-1]["findings"].extend(extra_open)
        self.finalize(archived)
        return led

    def run_verdict(self, ledger, sentinel=None, transcript=(), denied=(),
                    pre=None):
        return hv.verdict(self.copy, RECIPE, KEY, sentinel, list(transcript),
                          pre or self.pre, denied_roots=denied, ledger=ledger)

    def require_sandbox(self):
        if not SANDBOX_OK:
            self.skipTest("needs /usr/bin/sandbox-exec on darwin")

    def head_stub_if_no_sandbox(self):
        """Conservation controls isolate Condition 3b and run on any host;
        where Seatbelt exists the real HEAD checks run too."""
        if SANDBOX_OK:
            return contextlib.nullcontext()
        return mock.patch.object(hv, "head_check_problems", return_value=[])


# --------------------------------------------------------------------------- #
# Condition 2 — repair boundary, judged on committed content, evaluated first
# --------------------------------------------------------------------------- #
class TestRepairBoundary(_Case):
    def _assert_skipped_no_exec(self, result, calls):
        self.assertEqual(result.status, "FAILED")
        self.assertIn("head checks skipped: repair boundary failed",
                      result.reasons)
        self.assertEqual(calls, [], "committed code ran after the boundary "
                         "failed")

    def test_a_non_fix_subject_fails(self):
        sha = self.commit_fix(subject="tweak clamp")
        led = self.happy()
        p, calls = recorder("run_sandboxed")
        with p:
            r = self.run_verdict(led)
        self.assertIn("unexpected commit %s" % sha[:7], r.reasons)
        self._assert_skipped_no_exec(r, calls)

    def test_m1_subject_check_is_load_bearing(self):
        self.require_sandbox()
        self.commit_fix(subject="tweak clamp")
        led = self.happy()
        with mock.patch.object(hv, "_subject_ok", lambda s: True):
            r = self.run_verdict(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_a2_other_file_in_commit_fails(self):
        sha = self.commit_fix(extra={UNTOUCHED: BASE_UNTOUCHED + b"# x\n"})
        led = self.happy()
        p, calls = recorder("run_sandboxed")
        with p:
            r = self.run_verdict(led)
        self.assertIn("commit %s touches src/util.py outside the accepted "
                      "repair" % sha[:7], r.reasons)
        self._assert_skipped_no_exec(r, calls)

    def test_b_mutated_sentinel_fails(self):
        record = hsn.plant(self.copy, RECIPE)
        commit_files(self.copy.root, {FIXED: FIXED_BYTES}, GOOD_SUBJECT,
                     worktree=False)
        # The worktree keeps S3 and gains the fix inside the hunk, as fixstage
        # leaves it.
        data = Path(self.copy.root, FIXED).read_bytes()
        s, e = record.fixed_hunk
        ls = _lines(data)
        Path(self.copy.root, FIXED).write_bytes(b"".join(
            ls[:s - 1] + [x.encode() for x in FIX_HUNK] + ls[e:]))
        self.assertEqual(hsn.verify(self.copy, record), [])
        # Now damage S2 (the unstaged sentinel in the untouched file).
        u = Path(self.copy.root, UNTOUCHED)
        u.write_bytes(b"".join(x for x in _lines(u.read_bytes())
                               if record.unstaged_line.encode() not in x))
        led = self.happy()
        p, calls = recorder("run_sandboxed")
        with p:
            r = self.run_verdict(led, sentinel=record)
        self.assertIn("unstaged sentinel missing from src/util.py", r.reasons)
        self._assert_skipped_no_exec(r, calls)

    def _distant_helper_commit(self):
        data = with_hunk(helper_changed(DEFECT_FIXED), FIX_HUNK)
        # The helper line is at least 5 lines outside the hunk.
        self.assertGreaterEqual(HELPER_LINE - HUNK_E, 5)
        sha = self.commit_fix(data=data)
        with throwaway_export(self.copy) as (_, tree):
            self.assertEqual(plain_run(RECIPE["test_cmd"], tree).returncode, 0,
                             "tests must pass so the failure is the "
                             "boundary's alone")
        return sha

    def test_f_distant_helper_preservation_fails(self):
        record = hsn.plant(self.copy, RECIPE)
        sha = commit_files(self.copy.root, {FIXED: with_hunk(
            helper_changed(DEFECT_FIXED), FIX_HUNK)}, GOOD_SUBJECT,
            worktree=False)
        data = Path(self.copy.root, FIXED).read_bytes()
        s, e = record.fixed_hunk
        ls = _lines(data)
        Path(self.copy.root, FIXED).write_bytes(b"".join(
            ls[:s - 1] + [x.encode() for x in FIX_HUNK] + ls[e:]))
        self.assertEqual(hsn.verify(self.copy, record), [])
        with throwaway_export(self.copy) as (_, tree):
            self.assertEqual(plain_run(RECIPE["test_cmd"], tree).returncode, 0)
        led = self.happy()
        p, calls = recorder("run_sandboxed")
        with p:
            r = self.run_verdict(led, sentinel=record)
        self.assertEqual(r.reasons, [
            "commit %s changes src/clamp.py outside the accepted repair hunk "
            "(lines %d-%d)" % (sha[:7], HUNK_S, HUNK_E),
            "head checks skipped: repair boundary failed"])
        self._assert_skipped_no_exec(r, calls)

    def test_g_distant_helper_clean_run_fails(self):
        sha = self._distant_helper_commit()
        led = self.happy()
        p, calls = recorder("run_sandboxed")
        with p:
            r = self.run_verdict(led, sentinel=None)
        self.assertEqual(r.reasons, [
            "commit %s changes src/clamp.py outside the accepted repair hunk "
            "(lines %d-%d)" % (sha[:7], HUNK_S, HUNK_E),
            "head checks skipped: repair boundary failed"])
        self._assert_skipped_no_exec(r, calls)

    def test_m3_distant_helper_boundary_is_load_bearing(self):
        self.require_sandbox()
        self._distant_helper_commit()
        led = self.happy()
        with mock.patch.object(hv, "repair_boundary_problems",
                               lambda *a, **k: []):
            r = self.run_verdict(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []),
                         "clean-run shape")

    def test_m3_distant_helper_preservation_flip(self):
        self.require_sandbox()
        record = hsn.plant(self.copy, RECIPE)
        commit_files(self.copy.root, {FIXED: with_hunk(
            helper_changed(DEFECT_FIXED), FIX_HUNK)}, GOOD_SUBJECT,
            worktree=False)
        led = self.happy()
        with mock.patch.object(hv, "repair_boundary_problems",
                               lambda *a, **k: []):
            r = self.run_verdict(led, sentinel=record)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def _touch_and_revert(self):
        first = self.commit_fix(extra={UNTOUCHED: BASE_UNTOUCHED + b"# x\n"})
        commit_files(self.copy.root, {UNTOUCHED: BASE_UNTOUCHED},
                     "fix(review-pass-1): restore util")
        self.assertEqual(_git(self.copy.root, "diff", "--name-only", self.pre,
                              "HEAD").split(), [FIXED])
        return first

    def test_h_touch_and_revert_fails(self):
        first = self._touch_and_revert()
        led = self.happy()
        p, calls = recorder("run_sandboxed")
        with p:
            r = self.run_verdict(led)
        self.assertIn("commit %s touches src/util.py outside the accepted "
                      "repair" % first[:7], r.reasons)
        self.assertFalse([x for x in r.reasons if x.startswith("net ")])
        self._assert_skipped_no_exec(r, calls)

    def test_m4_per_commit_filename_check_is_load_bearing(self):
        self.require_sandbox()
        self._touch_and_revert()
        led = self.happy()
        with mock.patch.object(hv, "_commit_files_problems",
                               lambda *a, **k: []):
            r = self.run_verdict(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_i_intra_hunk_growth_is_accepted(self):
        self.require_sandbox()
        grown = [FIX_HUNK[0],
                 "        # values above the range snap to its top end\n",
                 "        # (the range is closed)\n", FIX_HUNK[1]]
        self.commit_fix(hunk=grown)
        led = self.happy()
        r = self.run_verdict(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_deleted_fixed_file_fails(self):
        sha = commit_files(self.copy.root, {FIXED: None}, GOOD_SUBJECT)
        self.assertIn(
            "commit %s changes src/clamp.py outside the accepted repair hunk "
            "(lines %d-%d)" % (sha[:7], HUNK_S, HUNK_E),
            hv.repair_boundary_problems(self.copy, RECIPE, KEY, self.pre))


# --------------------------------------------------------------------------- #
# Condition 1 — the COMMITTED tree fixes the defect
# --------------------------------------------------------------------------- #
class TestCommittedHead(_Case):
    def _apply_worktree_fix(self):
        Path(self.copy.root, FIXED).write_bytes(FIXED_BYTES)
        for argv in (RECIPE["test_cmd"], RECIPE["defect_check"]):
            self.assertEqual(plain_run(argv, self.copy.root).returncode, 0,
                             "the working tree must look fixed")

    def test_j_applied_uncommitted_fails(self):
        self.require_sandbox()
        self._apply_worktree_fix()
        led = self.happy()
        r = self.run_verdict(led)
        self.assertEqual(r.status, "FAILED")
        self.assertIn("no repair commit", r.reasons)
        self.assertIn("defect check failed on HEAD", r.reasons)

    def _committed_not_fixed(self):
        ls = [x.decode() for x in _lines(DEFECT_FIXED)[HUNK_S - 1:HUNK_E]]
        ls[0] = ls[0].rstrip("\n") + "  # probe\n"
        self.commit_fix(hunk=ls)
        self._apply_worktree_fix()
        with throwaway_export(self.copy) as (_, tree):
            self.assertNotEqual(
                plain_run(RECIPE["defect_check"], tree).returncode, 0,
                "HEAD must still carry the defect")

    def test_j2_committed_not_fixed_fails(self):
        self.require_sandbox()
        self._committed_not_fixed()
        led = self.happy()
        r = self.run_verdict(led)
        self.assertEqual(r.status, "FAILED")
        self.assertIn("defect check failed on HEAD", r.reasons)
        self.assertNotIn("no repair commit", r.reasons)

    @staticmethod
    def _worktree_export(copy, dest):
        """Mutant export: the WORKING TREE's tracked files, not HEAD."""
        tree = os.path.join(dest, "tree")
        out = subprocess.run(["git", "ls-files", "-z"], cwd=copy.root,
                             capture_output=True, timeout=60).stdout
        for rel in filter(None, out.decode().split("\0")):
            src = os.path.join(copy.root, rel)
            dst = os.path.join(tree, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        return tree

    def test_m5_committed_not_fixed_export_is_load_bearing(self):
        self.require_sandbox()
        self._committed_not_fixed()
        led = self.happy()
        with mock.patch.object(hv, "export_head", self._worktree_export):
            r = self.run_verdict(led)
        # The re-hash is an independent lock: a working-tree export is caught
        # before anything runs.
        self.assertIn("export invalid before defect check: src/clamp.py",
                      r.reasons)
        with mock.patch.object(hv, "export_head", self._worktree_export), \
                mock.patch.object(hv, "export_matches_head",
                                  lambda *a, **k: []):
            r = self.run_verdict(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_m6_applied_uncommitted_needs_both_halves(self):
        self.require_sandbox()
        self._apply_worktree_fix()
        led = self.happy()
        with mock.patch.object(hv, "export_head", self._worktree_export), \
                mock.patch.object(hv, "export_matches_head",
                                  lambda *a, **k: []):
            r = self.run_verdict(led)
        self.assertEqual(r.reasons, ["no repair commit"])
        with mock.patch.object(hv, "export_head", self._worktree_export), \
                mock.patch.object(hv, "export_matches_head",
                                  lambda *a, **k: []), \
                mock.patch.object(hv, "_has_repair_commit",
                                  lambda *a, **k: True):
            r = self.run_verdict(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_export_is_committed_content_only(self):
        self.commit_fix()
        Path(self.copy.root, UNTOUCHED).write_bytes(b"# uncommitted\n")
        with throwaway_export(self.copy) as (_, tree):
            self.assertEqual(hv.export_matches_head(self.copy, tree), [])
            self.assertFalse(os.path.exists(os.path.join(tree, ".turingmind")))
            self.assertEqual(Path(tree, UNTOUCHED).read_bytes(),
                             BASE_UNTOUCHED)
            Path(tree, "tests", "__pycache__").mkdir()
            Path(tree, "tests", "__pycache__", "x.pyc").write_bytes(b"x")
            Path(tree, UNTOUCHED).write_bytes(b"changed")
            os.unlink(os.path.join(tree, FIXED))
            self.assertEqual(hv.export_matches_head(self.copy, tree), [
                "export modified: src/clamp.py",
                "export modified: src/util.py",
                "export modified: unexpected file tests/__pycache__",
                "export modified: unexpected file tests/__pycache__/x.pyc"])

    def test_profile_shape(self):
        d = os.path.realpath(tempfile.mkdtemp())
        try:
            os.mkdir(d + "/tree")
            os.mkdir(d + "/runtime")
            p = hv.head_sandbox_profile(d + "/tree", d + "/runtime",
                                        ('/Users/me/a"b',))
            self.assertTrue(p.startswith("(version 1)"))
            self.assertIn("(deny network*)", p)
            self.assertIn('(deny file-write* (subpath "/"))', p)
            self.assertIn('(deny file-read* (subpath "/Users/me/a\\"b"))', p)
            self.assertEqual(p.count("(allow file-write* (subpath"), 1)
            self.assertNotIn(d + "/tree", p)
            with self.assertRaises(ValueError):
                hv.head_sandbox_profile(d + "/tree", d, ())
            with self.assertRaises(ValueError):
                hv.head_sandbox_profile(d, d + "/runtime", ())
        finally:
            shutil.rmtree(d)

    def test_scratch_is_removed_on_every_path(self):
        self.commit_fix()
        made = []
        real = tempfile.mkdtemp

        def spy(*a, **k):
            made.append(real(*a, **k))
            return made[-1]
        with mock.patch.object(hv.tempfile, "mkdtemp", spy), \
                mock.patch.object(hv, "SANDBOX_EXEC", "/nonexistent/sb"):
            r = hv.head_check_problems(self.copy, RECIPE, self.pre)
        self.assertTrue(r and r[0].startswith("head check sandbox "
                                              "unavailable: "))
        self.assertEqual(len(made), 1)
        self.assertFalse(os.path.exists(made[0]))
        self.assertFalse(made[0].startswith(self.copy.root))


# --------------------------------------------------------------------------- #
# Condition 1 — the sandbox fails closed (every host)
# --------------------------------------------------------------------------- #
class TestSandboxUnavailable(_Case):
    def _recipe_ran(self, calls):
        code = RECIPE["defect_check"][2]
        return [c for c in calls
                if code in c or "discover" in c]

    def _subprocess_recorder(self):
        real = subprocess.run
        calls = []

        def wrapper(argv, *a, **k):
            calls.append(list(argv))
            return real(argv, *a, **k)
        return mock.patch("subprocess.run", wrapper), calls

    def test_l2_sandbox_unavailable_fails_closed(self):
        self.commit_fix()
        led = self.happy()
        p, calls = self._subprocess_recorder()
        with p, mock.patch.object(hv, "SANDBOX_EXEC", "/nonexistent/sb"):
            r = self.run_verdict(led)
        self.assertEqual(r.status, "FAILED")
        self.assertEqual(len([x for x in r.reasons if x.startswith(
            "head check sandbox unavailable: ")]), 1)
        self.assertEqual(self._recipe_ran(calls), [], "nothing ran unsandboxed")

    def test_m10_sandbox_unavailable_fallback_mutant(self):
        self.commit_fix()
        led = self.happy()
        real = hv.run_sandboxed

        def fallback(argv, cwd, profile, runtime_dir, timeout):
            try:
                return real(argv, cwd, profile, runtime_dir, timeout)
            except hv.SandboxUnavailable:
                return plain_run(argv, cwd)
        p, calls = self._subprocess_recorder()
        with p, mock.patch.object(hv, "SANDBOX_EXEC", "/nonexistent/sb"), \
                mock.patch.object(hv, "run_sandboxed", fallback):
            self.run_verdict(led)
        self.assertNotEqual(self._recipe_ran(calls), [],
                            "the fallback mutant must run the recipe")

    def test_l2_sandbox_unavailable_rejected_profile(self):
        self.require_sandbox()
        self.commit_fix()
        led = self.happy()
        p, calls = self._subprocess_recorder()
        with p, mock.patch.object(hv, "head_sandbox_profile",
                                  lambda *a, **k: "(version 1)(bogus"):
            r = self.run_verdict(led)
        self.assertEqual(len([x for x in r.reasons if x.startswith(
            "head check sandbox unavailable: ")]), 1)
        ran = self._recipe_ran(calls)
        # The only call carrying the recipe is the rejected sandbox-exec one;
        # the suite was never even offered.
        self.assertEqual(len(ran), 1)
        self.assertEqual(ran[0][:2], [hv.SANDBOX_EXEC, "-p"])
        self.assertFalse([c for c in calls if "discover" in c])

    def test_non_darwin_is_unavailable(self):
        with mock.patch.object(hv.sys, "platform", "linux"):
            with self.assertRaises(hv.SandboxUnavailable):
                hv.run_sandboxed(["python3", "-c", "pass"], self.tmp,
                                 "(version 1)", self.tmp, 10)

    def test_l3_boundary_first(self):
        payload = escape_payload("/nonexistent-canary", "/nonexistent-out",
                                 "0" * 16, indent="    ")
        data = with_hunk(DEFECT_FIXED, FIX_HUNK)
        ls = _lines(data)
        ls[HELPER_LINE:HELPER_LINE] = [x.encode() for x in payload]
        self.commit_fix(data=b"".join(ls))
        led = self.happy()
        p, calls = recorder("run_sandboxed")
        with p:
            r = self.run_verdict(led)
        self.assertEqual(r.status, "FAILED")
        self.assertIn("head checks skipped: repair boundary failed", r.reasons)
        self.assertTrue([x for x in r.reasons
                         if "outside the accepted repair hunk" in x])
        self.assertEqual(calls, [])

    def test_m11_boundary_first_is_load_bearing(self):
        payload = escape_payload("/nonexistent-canary", "/nonexistent-out",
                                 "0" * 16, indent="    ")
        data = with_hunk(DEFECT_FIXED, FIX_HUNK)
        ls = _lines(data)
        ls[HELPER_LINE:HELPER_LINE] = [x.encode() for x in payload]
        self.commit_fix(data=b"".join(ls))
        led = self.happy()
        real = hv.head_check_problems
        p, calls = recorder("run_sandboxed")
        with p, mock.patch.object(
                hv, "head_check_problems",
                lambda *a, **k: real(*a, **dict(k, execute=True))):
            with contextlib.suppress(hv.SandboxUnavailable):
                self.run_verdict(led)
        self.assertNotEqual(calls, [])


# --------------------------------------------------------------------------- #
# Condition 1 — Seatbelt holds against committed code (darwin only)
# --------------------------------------------------------------------------- #
def escape_payload(canary, outside_dir, nonce, indent="    "):
    target = os.path.join(outside_dir, "escaped-%s.txt" % nonce)
    body = [
        "import os as _os",
        "print('PROBE-HEAD-ATTEMPT read', flush=True)",
        "try:",
        "    print('PROBE-HEAD-READ ' + open(%r).read().strip(), flush=True)"
        % canary,
        "except Exception as _e:",
        "    print('PROBE-HEAD-READ', type(_e).__name__, getattr(_e, 'errno',"
        " None), flush=True)",
        "print('PROBE-HEAD-ATTEMPT write', flush=True)",
        "try:",
        "    open(%r, 'w').write('x')" % target,
        "    print('PROBE-HEAD-WRITE ok', flush=True)",
        "except Exception as _e:",
        "    print('PROBE-HEAD-WRITE', type(_e).__name__, getattr(_e, 'errno',"
        " None), flush=True)",
        "print('PROBE-HEAD-ENV ' + repr(_os.environ.get('HARNESS_TEST_SECRET')),"
        " flush=True)",
    ]
    return [indent + x + "\n" for x in body]


INJECTED_TEST = ("import unittest\n\n\nclass Injected(unittest.TestCase):\n"
                 "    def test_ok(self):\n        pass\n")


def tamper_payload(t_file, delete_file, indent="    "):
    body = [
        "import os as _os",
        "print('PROBE-HEAD-ATTEMPT overwrite', flush=True)",
        "try:",
        "    with open(%r, 'w') as _fh:" % t_file,
        "        _fh.write(%r)" % INJECTED_TEST,
        "    print('PROBE-HEAD-OVERWRITE ok', flush=True)",
        "except Exception as _e:",
        "    print('PROBE-HEAD-OVERWRITE', type(_e).__name__, getattr(_e,"
        " 'errno', None), flush=True)",
        "print('PROBE-HEAD-ATTEMPT delete', flush=True)",
        "try:",
        "    _os.remove(%r)" % delete_file,
        "    print('PROBE-HEAD-DELETE ok', flush=True)",
        "except Exception as _e:",
        "    print('PROBE-HEAD-DELETE', type(_e).__name__, getattr(_e,"
        " 'errno', None), flush=True)",
        "print('PROBE-HEAD-ATTEMPT create', flush=True)",
        "try:",
        "    with open('tests/test_zzz_injected.py', 'w') as _fh:",
        "        _fh.write(%r)" % INJECTED_TEST,
        "    print('PROBE-HEAD-CREATE ok', flush=True)",
        "except Exception as _e:",
        "    print('PROBE-HEAD-CREATE', type(_e).__name__, getattr(_e,"
        " 'errno', None), flush=True)",
    ]
    return [indent + x + "\n" for x in body]


def ran_count(text):
    m = re.search(r"Ran (\d+) tests?", text)
    return int(m.group(1)) if m else None


@unittest.skipUnless(SANDBOX_OK, "needs /usr/bin/sandbox-exec on darwin")
class TestHeadSandbox(_Case):
    def setUp(self):
        super().setUp()
        self._outside = tempfile.TemporaryDirectory()
        base = os.path.realpath(self._outside.name)
        self.nonce = uuid.uuid4().hex[:16]
        self.canary_dir = os.path.join(base, "canary")
        self.outside_dir = os.path.join(base, "outside")
        os.mkdir(self.canary_dir)
        os.mkdir(self.outside_dir)
        self.canary = os.path.join(self.canary_dir, "canary.txt")
        Path(self.canary).write_text("HEAD-CANARY-%s\n" % self.nonce)
        self.escaped = os.path.join(self.outside_dir,
                                    "escaped-%s.txt" % self.nonce)
        self._env = mock.patch.dict(os.environ, {
            "HARNESS_TEST_SECRET": "leak-%s" % self.nonce})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._outside.cleanup()
        super().tearDown()

    def _sandboxed(self, argv, export, scratch, extra=()):
        runtime = os.path.join(scratch, "runtime")
        profile = hv.head_sandbox_profile(
            export, runtime, hv.DEFAULT_DENIED_ROOTS + (self.copy.root,)
            + tuple(extra))
        return hv.run_sandboxed(argv, export, profile, runtime, 120)

    # -- (e) the happy path, with execution assertions --------------------- #
    def test_e_happy_path_runs_two_sandboxed_commands(self):
        fix = self.commit_fix()
        led = self.happy()
        rs, rs_calls = recorder("run_sandboxed")
        em, em_calls = recorder("export_matches_head")
        real_run = subprocess.run
        sp_calls = []

        def sp(argv, *a, **k):
            sp_calls.append((list(argv), k))
            return real_run(argv, *a, **k)
        with rs, em, mock.patch("subprocess.run", sp):
            r = self.run_verdict(
                led, transcript=["committed — commit_sha=%s" % fix])
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions, {self.S: "resolved"})
        self.assertEqual([c[0][0] for c in rs_calls],
                         [RECIPE["defect_check"], RECIPE["test_cmd"]])
        for a, _, _ in rs_calls:
            argv, cwd, profile, runtime, _ = a
            self.assertFalse(hv._is_under(runtime, cwd))
            self.assertFalse(hv._is_under(cwd, runtime))
        self.assertEqual(len(em_calls), 3)
        self.assertEqual([c[2] for c in em_calls], [[], [], []])
        sandboxed = [c for c in sp_calls if c[0][0] == hv.SANDBOX_EXEC]
        self.assertEqual(len(sandboxed), 2)
        for argv, k in sandboxed:
            self.assertEqual(argv[3], PY)
            runtime = rs_calls[0][0][3]
            self.assertEqual(k["env"], {
                "PATH": "/usr/bin:/bin", "HOME": runtime, "TMPDIR": runtime,
                "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1",
                "PYTHONPYCACHEPREFIX": runtime + "/pycache"})
        python_direct = [c for c in sp_calls
                         if RECIPE["defect_check"][2] in c[0]
                         and c[0][0] != hv.SANDBOX_EXEC]
        self.assertEqual(python_direct, [])

    def test_d_phantom_commit_claim_fails(self):
        self.commit_fix()
        led = self.happy()
        r = self.run_verdict(led, transcript=["applied: commit_sha=deadbeef"])
        self.assertEqual(r.reasons,
                         ["success claimed for a commit that does not exist"])

    # -- (l) committed-code escape ------------------------------------------ #
    def _escape_commit(self):
        hunk = escape_payload(self.canary, self.outside_dir, self.nonce) \
            + FIX_HUNK
        self.commit_fix(hunk=hunk)
        with throwaway_export(self.copy) as (_, tree):
            out = plain_run(RECIPE["defect_check"], tree).stdout
        self.assertIn("PROBE-HEAD-READ HEAD-CANARY-%s" % self.nonce, out)
        self.assertIn("PROBE-HEAD-WRITE ok", out)
        self.assertIn("PROBE-HEAD-ENV 'leak-%s'" % self.nonce, out)
        self.assertTrue(os.path.exists(self.escaped),
                        "unsandboxed, the payload really escapes")
        os.unlink(self.escaped)

    def test_l_committed_code_escape_is_denied(self):
        self._escape_commit()
        with throwaway_export(self.copy) as (scratch, tree):
            proc = self._sandboxed(RECIPE["defect_check"], tree, scratch,
                                   (self.canary_dir, self.outside_dir))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = proc.stdout
        self.assertIn("PROBE-HEAD-ATTEMPT read", out)
        self.assertIn("PROBE-HEAD-ATTEMPT write", out)
        self.assertIn("PROBE-HEAD-READ PermissionError 1", out)
        self.assertIn("PROBE-HEAD-WRITE PermissionError 1", out)
        self.assertIn("PROBE-HEAD-ENV None", out)
        self.assertNotIn("HEAD-CANARY-", out)
        self.assertFalse(os.path.exists(self.escaped))
        led = self.happy()
        r = self.run_verdict(led, denied=(self.canary_dir, self.outside_dir))
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertFalse(os.path.exists(self.escaped))

    def test_m8_committed_code_escape_without_seatbelt(self):
        self._escape_commit()

        def no_prefix(argv, cwd, profile, runtime_dir, timeout):
            argv = list(argv)
            argv[0] = PY
            return subprocess.run(argv, cwd=cwd, capture_output=True,
                                  text=True, timeout=timeout, env={
                                      "PATH": "/usr/bin:/bin",
                                      "HOME": runtime_dir,
                                      "TMPDIR": runtime_dir})
        with mock.patch.object(hv, "run_sandboxed", no_prefix), \
                throwaway_export(self.copy) as (scratch, tree):
            proc = hv.run_sandboxed(RECIPE["defect_check"], tree, "",
                                    os.path.join(scratch, "runtime"), 120)
        self.assertIn("HEAD-CANARY-%s" % self.nonce, proc.stdout)
        self.assertTrue(os.path.exists(self.escaped))

    def test_m9_committed_code_escape_with_host_env(self):
        self._escape_commit()

        def host_env(argv, cwd, profile, runtime_dir, timeout):
            argv = list(argv)
            argv[0] = PY
            return subprocess.run([hv.SANDBOX_EXEC, "-p", profile, *argv],
                                  cwd=cwd, capture_output=True, text=True,
                                  timeout=timeout, env=os.environ)
        with mock.patch.object(hv, "run_sandboxed", host_env), \
                throwaway_export(self.copy) as (scratch, tree):
            proc = self._sandboxed(RECIPE["defect_check"], tree, scratch,
                                   (self.canary_dir, self.outside_dir))
        self.assertIn("PROBE-HEAD-ENV 'leak-%s'" % self.nonce, proc.stdout)

    # -- (l4) export tamper ------------------------------------------------- #
    def _tamper_commit(self):
        delete = TEST_FILES[1] if len(TEST_FILES) > 1 else T_FILE
        with throwaway_export(self.copy) as (_, tree):
            p = plain_run(RECIPE["test_cmd"], tree)
            k = ran_count(p.stdout + p.stderr)
        self.assertIsNotNone(k)
        self.assertGreaterEqual(k, 2)
        self.commit_fix(hunk=tamper_payload(T_FILE, delete) + FIX_HUNK)
        with throwaway_export(self.copy) as (_, tree):
            p = plain_run(RECIPE["defect_check"], tree)
            self.assertEqual(p.returncode, 0)
            for word in ("OVERWRITE", "DELETE", "CREATE"):
                self.assertIn("PROBE-HEAD-%s ok" % word, p.stdout)
            problems = hv.export_matches_head(self.copy, tree)
            self.assertIn("export modified: %s" % T_FILE, problems)
            self.assertIn("export modified: unexpected file "
                          "tests/test_zzz_injected.py", problems)
            t = plain_run(RECIPE["test_cmd"], tree)
            self.assertEqual(t.returncode, 0)
            self.assertNotEqual(ran_count(t.stdout + t.stderr), k,
                                "unprotected, the committed suite never ran")
        return k

    @staticmethod
    def _writable_export_profile(export_dir, runtime_dir, denied_roots):
        """The vulnerable profile: its one writable subpath is the PARENT
        scratch dir, so the export tree is writable."""
        real = _REAL_PROFILE(export_dir, runtime_dir, denied_roots)
        rt = os.path.realpath(runtime_dir)
        return real.replace('(allow file-write* (subpath "%s"))' % rt,
                            '(allow file-write* (subpath "%s"))'
                            % os.path.dirname(rt))

    def test_l4_export_tamper_is_denied(self):
        k = self._tamper_commit()
        with throwaway_export(self.copy) as (scratch, tree):
            before = set(os.listdir(scratch))
            proc = self._sandboxed(RECIPE["defect_check"], tree, scratch)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            for word in ("overwrite", "delete", "create"):
                self.assertIn("PROBE-HEAD-ATTEMPT %s" % word, proc.stdout)
            for word in ("OVERWRITE", "DELETE", "CREATE"):
                self.assertIn("PROBE-HEAD-%s PermissionError 1" % word,
                              proc.stdout)
            self.assertEqual(hv.export_matches_head(self.copy, tree), [])
            data = Path(tree, T_FILE).read_bytes()
            blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
            self.assertEqual(blob, _git(self.copy.root, "rev-parse",
                                        "HEAD:%s" % T_FILE).strip())
            suite = self._sandboxed(RECIPE["test_cmd"], tree, scratch)
            self.assertEqual(suite.returncode, 0, suite.stderr)
            self.assertEqual(ran_count(suite.stdout + suite.stderr), k)
            self.assertEqual(set(os.listdir(scratch)), before)
            self.assertEqual(hv.export_matches_head(self.copy, tree), [])
        print("\n[l4] defect_check denials: %s" % " | ".join(
            x for x in proc.stdout.splitlines()
            if "PermissionError 1" in x and "PROBE-HEAD-" in x))
        print("[l4] committed suite: %s" % re.search(
            r"Ran \d+ tests?", suite.stdout + suite.stderr).group(0))
        led = self.happy()
        rs, rs_calls = recorder("run_sandboxed")
        em, em_calls = recorder("export_matches_head")
        with rs, em:
            r = self.run_verdict(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual([c[0][0] for c in rs_calls],
                         [RECIPE["defect_check"], RECIPE["test_cmd"]])
        self.assertEqual([c[2] for c in em_calls], [[], [], []])
        self.assertEqual(ran_count(rs_calls[1][2].stdout
                                   + rs_calls[1][2].stderr), k)

    def test_m12_writable_export_profile(self):
        self._tamper_commit()
        with mock.patch.object(hv, "head_sandbox_profile",
                               self._writable_export_profile):
            with throwaway_export(self.copy) as (scratch, tree):
                proc = self._sandboxed(RECIPE["defect_check"], tree, scratch)
            for word in ("OVERWRITE", "DELETE", "CREATE"):
                self.assertIn("PROBE-HEAD-%s ok" % word, proc.stdout)
            led = self.happy()
            rs, rs_calls = recorder("run_sandboxed")
            with rs:
                r = self.run_verdict(led)
        self.assertEqual(r.status, "FAILED")
        self.assertIn("export modified during defect check: %s" % T_FILE,
                      r.reasons)
        self.assertIn("tests skipped: export modified", r.reasons)
        self.assertEqual(len(rs_calls), 1, "the suite ran on a tampered export")

    def test_m13_red_green_export(self):
        k = self._tamper_commit()
        led = self.happy()
        rs, rs_calls = recorder("run_sandboxed")
        with rs, mock.patch.object(hv, "head_sandbox_profile",
                                   self._writable_export_profile), \
                mock.patch.object(hv, "export_matches_head",
                                  lambda *a, **k: []):
            r = self.run_verdict(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        suite = rs_calls[1][2]
        self.assertIn("Ran 1 test", suite.stdout + suite.stderr)
        self.assertNotEqual(ran_count(suite.stdout + suite.stderr), k)

    def test_m14_mid_point_rehash(self):
        self._tamper_commit()
        led = self.happy()
        real = hv.export_matches_head
        n = [0]

        def skip_second(*a, **k):
            n[0] += 1
            return [] if n[0] == 2 else real(*a, **k)
        rs, rs_calls = recorder("run_sandboxed")
        with rs, mock.patch.object(hv, "head_sandbox_profile",
                                   self._writable_export_profile), \
                mock.patch.object(hv, "export_matches_head", skip_second):
            r = self.run_verdict(led)
        self.assertEqual(len(rs_calls), 2)
        suite = rs_calls[1][2]
        self.assertIn("Ran 1 test", suite.stdout + suite.stderr)
        self.assertEqual(r.status, "FAILED")
        self.assertTrue(r.reasons)
        self.assertTrue(all(x.startswith("export modified during tests: ")
                            for x in r.reasons), r.reasons)


_REAL_PROFILE = hv.head_sandbox_profile


# --------------------------------------------------------------------------- #
# Condition 3 — Finalize really happened
# --------------------------------------------------------------------------- #
class TestFinalize(_Case):
    def test_c_outstanding_at_finalize_fails(self):
        self.commit_fix()
        x = self.st.finding(H("X"), "warning", UNTOUCHED, 5, status="new",
                            at_pass=2)
        led = self.happy(extra_open=[x])
        with self.head_stub_if_no_sandbox():
            r = self.run_verdict(led)
        self.assertEqual(r.reasons, ["outstanding findings at finalize: 1"])

    def test_m2_outstanding_check_is_load_bearing(self):
        self.commit_fix()
        x = self.st.finding(H("X"), "warning", UNTOUCHED, 5, status="new",
                            at_pass=2)
        led = self.happy(extra_open=[x])
        with self.head_stub_if_no_sandbox(), \
                mock.patch.object(hv, "_outstanding", lambda counts: 0):
            r = self.run_verdict(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_k_root_review_md_does_not_count(self):
        self.commit_fix()
        head = _git(self.copy.root, "rev-parse", "HEAD").strip()
        state = self.st.state([self.pass2_resolved(head)])
        led = self.ledger((state, "turn_end", head))
        self.finalize(state, review=False, root_review=True)
        with self.head_stub_if_no_sandbox():
            r = self.run_verdict(led)
        self.assertEqual(r.reasons, [".turingmind/REVIEW.md missing"])
        with self.head_stub_if_no_sandbox(), mock.patch.object(
                hv, "_review_md_path",
                lambda copy: os.path.join(copy.root, "REVIEW.md")):
            r = self.run_verdict(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_state_not_archived_and_multiple(self):
        self.commit_fix()
        led = self.happy()
        archived = str(self.seed_path) + ".archived-test"
        shutil.copyfile(archived, archived + "2")
        with self.head_stub_if_no_sandbox():
            r = self.run_verdict(led)
        self.assertIn("multiple archived states", r.reasons)
        os.unlink(archived)
        os.unlink(archived + "2")
        with self.head_stub_if_no_sandbox():
            r = self.run_verdict(led)
        self.assertIn("state not archived", r.reasons)

    def test_pre_run_head_mismatch(self):
        self.commit_fix()
        led = self.happy()
        with mock.patch.object(hv, "head_check_problems", return_value=[]):
            r = self.run_verdict(led, pre=self.copy.base_sha)
        self.assertIn("pre-run head mismatch", r.reasons)

    def test_key_material_in_copy_fails(self):
        self.commit_fix()
        led = self.happy()
        Path(self.copy.root, ".turingmind", "leak.txt").write_text(
            '{"defect_check": 1}')
        with self.head_stub_if_no_sandbox():
            r = self.run_verdict(led)
        self.assertEqual(r.reasons, ["key material found in copy"])


# --------------------------------------------------------------------------- #
# Condition 3b — finding conservation (pure state logic, every host)
# --------------------------------------------------------------------------- #
class _Conservation(_Case):
    def setUp(self):
        super().setUp()
        self.fix = self.commit_fix()
        self.N1, self.N2, self.N3 = H("N1"), H("N2"), H("N3")

    def verdict_of(self, led, **kw):
        with self.head_stub_if_no_sandbox():
            return self.run_verdict(led, **kw)

    def two_passes(self, first, rerun, resolved_extra=()):
        """s1 = seed pass + the first persisted review pass (pass 2, before
        the fix); s2 = s1 + the rerun (pass 3, after the fix commit) on
        which S is resolved."""
        p2 = self.st.pass_entry(2, self.pre, [self.st.seeded()] + list(first))
        p3 = self.st.pass_entry(
            3, self.fix, list(rerun),
            [States.resolved(self.st.seeded(), 3, self.fix)]
            + list(resolved_extra))
        return self.st.state([p2]), self.st.state([p2, p3])

    def n_states(self):
        """s1: S, N1 (warning), N2 (medium), all open; s2: the rerun — S
        resolved, N1 still open, N2 simply gone."""
        n1 = self.st.finding(self.N1, "warning", UNTOUCHED, 5)
        n2 = self.st.finding(self.N2, "medium", UNTOUCHED, 9)
        s1, s2 = self.two_passes([n1, n2], [copymod.deepcopy(n1)])
        return n1, n2, s1, s2

    def fresh(self):
        """A fresh copy for the next shape inside one test."""
        self.tearDown()
        self.setUp()

    def n_ledger(self, s1, s2):
        return self.ledger((s1, "card", self.pre), (s2, "turn_end", self.fix))


class TestConservation(_Conservation):
    def _n1_case(self):
        n1, n2, s1, s2 = self.n_states()
        led = self.n_ledger(s1, s2)
        archived = copymod.deepcopy(s2)
        archived["decisions"] = {self.N1: decision(n1)}
        c = self.counts(archived)
        self.assertEqual((c["outstanding_cw"], c["unacknowledged_medium"]),
                         (0, 0), "the vulnerable verdict would certify this")
        self.finalize(archived)
        return led

    def test_n1_conservation_drop_fails(self):
        led = self._n1_case()
        r = self.verdict_of(led)
        self.assertEqual(r.reasons, ["obligation dropped without decision: %s"
                                     % sha7(self.N2)])
        self.assertEqual(r.dispositions, {self.S: "resolved",
                                          self.N1: "decided",
                                          self.N2: "missing"})

    def test_m18_late_ledger(self):
        led = self._n1_case()

        def replace_observe(self_, snapshot, label, head_sha):
            self_.first_seen = {}
            return _REAL_OBSERVE(self_, snapshot, label, head_sha)
        # The same observations, through a ledger that only remembers the
        # latest snapshot (one started just before Close out).
        with mock.patch.object(hv.ObligationLedger, "observe",
                               replace_observe):
            late = hv.ObligationLedger()
            for snapshot in led.snapshots:
                late.observe(None if snapshot.get("absent") else snapshot,
                             snapshot["label"], snapshot["head_sha"])
        self.assertNotIn(self.N2, late.all_hashes())
        r = self.verdict_of(late)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def _n2_states(self, keep_member):
        r_hash, m_hash = H("R"), H("M")
        member = self.st.member(m_hash, "warning", UNTOUCHED, 12)
        row1 = self.st.finding(r_hash, "warning", UNTOUCHED, 11,
                               members=[copymod.deepcopy(
                                   self.st.seed_finding["members"][0]),
                                   member])
        s1, _ = self.two_passes([row1], [])
        recs = hv._carry_state().open_findings(s1)
        self.assertIn(m_hash, [x["stable_hash"] for x in recs])
        self.assertEqual([x for x in recs if x["stable_hash"] == m_hash][0]
                         ["absorbed_into"], r_hash)
        row2 = copymod.deepcopy(row1)
        if not keep_member:
            row2["members"] = row2["members"][:1]
        _, s2 = self.two_passes([row1], [row2])
        archived = copymod.deepcopy(s2)
        archived["decisions"] = {r_hash: decision(row2)}
        return r_hash, m_hash, s1, s2, archived

    def test_n2_absorbed_member_drop_fails(self):
        r_hash, m_hash, s1, s2, archived = self._n2_states(keep_member=False)
        led = self.ledger((s1, "card", self.pre), (s2, "turn_end", self.fix))
        c = self.counts(archived)
        self.assertEqual((c["outstanding_cw"], c["unacknowledged_medium"]),
                         (0, 0))
        self.finalize(archived)
        r = self.verdict_of(led)
        self.assertEqual(r.reasons, ["obligation dropped without decision: %s"
                                     % sha7(m_hash)])

    def _n2_variant(self):
        r_hash, m_hash, s1, s2, archived = self._n2_states(keep_member=True)
        led = self.ledger((s1, "card", self.pre), (s2, "turn_end", self.fix))
        self.finalize(archived)
        return m_hash, led

    def test_n2_absorbed_member_variant_row_decision_closes_nothing(self):
        m_hash, led = self._n2_variant()
        r = self.verdict_of(led)
        self.assertEqual(r.status, "FAILED")
        self.assertIn("obligation open at archive: %s" % sha7(m_hash),
                      r.reasons)
        self.assertEqual(r.dispositions[m_hash], "visible_open")

    def test_m16_absorbed_member_inherits_closure(self):
        m_hash, led = self._n2_variant()

        def inherit(rec, by_hash):
            return by_hash.get(rec.get("absorbed_into"), rec)
        with mock.patch.object(hv, "_closure_subject", inherit):
            r = self.verdict_of(led)
        # The conservation lock flips: the member reads as decided. The
        # plugin's own finalize-counts still counts it (an independent lock).
        self.assertEqual(r.dispositions[m_hash], "decided")
        self.assertNotIn("obligation open at archive: %s" % sha7(m_hash),
                         r.reasons)
        self.assertEqual(r.reasons, ["outstanding findings at finalize: 1"])

    # -- (n3) ambiguous ----------------------------------------------------- #
    def _n3a(self):
        n1, n2, s1, s2 = self.n_states()
        led = self.n_ledger(s1, s2)
        archived = copymod.deepcopy(s2)
        archived["decisions"] = {self.N1: decision(n1)}
        archived["passes"][-1]["resolved"].append(
            States.resolved(n1, 3, self.fix))
        # N2 is properly resolved so only N1 is in question.
        archived["passes"][-1]["resolved"].append(
            States.resolved(n2, 3, self.fix))
        self.finalize(archived)
        return led

    def test_n3a_ambiguous_resolved_and_open(self):
        r = self.verdict_of(self._n3a())
        self.assertEqual(r.reasons, ["ambiguous obligation match: %s"
                                     % sha7(self.N1)])
        self.assertEqual(r.dispositions[self.N1], "ambiguous")

    def _n3b(self):
        n1, n2, s1, s2 = self.n_states()
        led = self.n_ledger(s1, s2)
        archived = copymod.deepcopy(s2)
        archived["decisions"] = {self.N1: decision(n1)}
        archived["passes"][-1]["resolved"].append(
            States.resolved(n2, 3, self.fix, file="src/other.py"))
        self.finalize(archived)
        return led

    def test_n3b_ambiguous_different_file(self):
        r = self.verdict_of(self._n3b())
        self.assertEqual(r.reasons, ["ambiguous obligation match: %s"
                                     % sha7(self.N2)])

    def _n3c(self):
        n1, n2, s1, s2 = self.n_states()
        led = self.n_ledger(s1, s2)
        archived = copymod.deepcopy(s2)
        archived["passes"][-1]["findings"] = []
        archived["passes"][-1]["resolved"].extend([
            States.resolved(n1, 3, self.fix), States.resolved(n1, 3, self.fix),
            States.resolved(n2, 3, self.fix)])
        self.finalize(archived)
        return led

    def test_n3c_ambiguous_two_resolved_same_pass(self):
        r = self.verdict_of(self._n3c())
        self.assertEqual(r.reasons, ["ambiguous obligation match: %s"
                                     % sha7(self.N1)])

    def test_m17_loose_matcher(self):
        for name, build in (("n3a", self._n3a), ("n3b", self._n3b),
                            ("n3c", self._n3c)):
            with self.subTest(name):
                led = build()
                with mock.patch.object(hv, "_ambiguous",
                                       lambda *a, **k: False):
                    r = self.verdict_of(led)
                self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
                self.fresh()

    # -- (n4)–(n7) -------------------------------------------------------- #
    def _n4(self):
        n1, n2, s1, s2 = self.n_states()
        led = self.n_ledger(s1, s2)
        archived = copymod.deepcopy(s2)
        archived["decisions"] = {self.N1: decision(n1, reason="")}
        archived["passes"][-1]["resolved"].append(
            States.resolved(n2, 3, self.fix))
        self.finalize(archived)
        return led

    def test_n4_decision_without_reason(self):
        r = self.verdict_of(self._n4())
        self.assertEqual(r.reasons, ["obligation decision without reason: %s"
                                     % sha7(self.N1)])
        self.assertEqual(r.dispositions[self.N1], "decided")

    def _n5(self):
        s = self.st.seeded()
        state = self.st.state([self.st.pass_entry(2, self.fix, [s])])
        led = self.ledger((state, "turn_end", self.fix))
        archived = copymod.deepcopy(state)
        archived["decisions"] = {self.S: decision(s)}
        c = self.counts(archived)
        self.assertEqual(c["outstanding_cw"], 0)
        self.finalize(archived)
        return led

    def test_n5_seeded_not_resolved(self):
        r = self.verdict_of(self._n5())
        self.assertEqual(r.reasons, ["seeded finding not verified resolved: %s"
                                     % sha7(self.S)])
        self.assertEqual(r.dispositions[self.S], "decided")

    def test_m15_red_green_conservation(self):
        builds = {"n1": self._n1_case, "n2": None, "n3a": self._n3a,
                  "n3b": self._n3b, "n4": self._n4, "n5": self._n5}
        for name, build in builds.items():
            with self.subTest(name):
                self.fresh()
                if build is None:
                    _, _, s1, s2, archived = self._n2_states(False)
                    led = self.ledger((s1, "card", self.pre),
                                      (s2, "turn_end", self.fix))
                    self.finalize(archived)
                else:
                    led = build()
                real = self.verdict_of(led)
                self.assertEqual(real.status, "FAILED")
                with mock.patch.object(
                        hv, "reconcile_obligations",
                        lambda *a, **k: hv.Reconciliation([], {})):
                    r = self.verdict_of(led)
                self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_n6_ledger_missing(self):
        self.happy()
        r = self.verdict_of(None)
        self.assertEqual(r.reasons, ["obligation ledger missing"])
        r = self.verdict_of(hv.ObligationLedger())
        self.assertEqual(r.reasons, ["obligation ledger empty"])

    def _n7_state(self):
        s = self.st.seeded()
        blob = _git(self.copy.root, "rev-parse", "HEAD:%s" % FIXED).strip()
        state = self.st.state([self.st.pass_entry(2, self.fix, [s])],
                              fix_verdicts={self.S: {
                                  "verdict": "obsolete", "agent": "fix",
                                  "head_sha": self.fix, "at_pass": 2,
                                  "reason": "line rewritten",
                                  "verified_blob": blob}})
        return state

    def test_n7_fix_verified_path(self):
        state = self._n7_state()
        led = self.ledger((state, "turn_end", self.fix))
        self.finalize(copymod.deepcopy(state))
        self.assertEqual(_git(self.copy.root, "status", "--porcelain",
                              "--", FIXED), "")
        r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[self.S], "fix_verified")

    def test_n7_fix_verified_unbound_with_s3_sentinel(self):
        state = self._n7_state()
        led = self.ledger((state, "turn_end", self.fix))
        self.finalize(copymod.deepcopy(state))
        ls = _lines(Path(self.copy.root, FIXED).read_bytes())
        after = RECIPE["sentinels"]["unstaged_fixed"]["after_line"]
        ls.insert(after, b"# sentinel-fixed-file " + b"a" * 32 + b"\n")
        Path(self.copy.root, FIXED).write_bytes(b"".join(ls))
        self.assertEqual(hv.head_blobs_for(self.copy, state), {})
        r = self.verdict_of(led)
        self.assertEqual(r.status, "FAILED")
        self.assertIn("seeded finding not verified resolved: %s"
                      % sha7(self.S), r.reasons)


# --------------------------------------------------------------------------- #
# Condition 3 at the format-53 location: the authoritative state only, no
# legacy fallback, undecided Needs-verification and vanished obligations fail,
# reasoned defer/dismiss decisions are kept
# --------------------------------------------------------------------------- #
def _legacy_archived_states(copy):
    """The pre-format-53 glob: every archive anywhere under .turingmind/state."""
    base = os.path.join(copy.root, ".turingmind", "state")
    return sorted(hv.glob.glob(os.path.join(hv.glob.escape(base), "**",
                                            "*.json.archived-*"),
                               recursive=True))


class TestFormat53State(_Conservation):
    def archive_path(self):
        return str(self.seed_path) + ".archived-test"

    def legacy_copy(self, move):
        """Put the archive at the legacy flat location (copy or move)."""
        src = self.archive_path()
        name = os.path.basename(src)
        dst = os.path.join(self.copy.root, ".turingmind", "state", name)
        (shutil.move if move else shutil.copyfile)(src, dst)
        return ".turingmind/state/%s" % name

    def nv_row(self, h, line=7):
        return self.st.finding(h, "needs-verification", UNTOUCHED, line,
                               status="new", at_pass=2)

    @staticmethod
    def nv_decision(f, reason=REASON, kind="defer"):
        cs = hv._carry_state()
        ev = evidence(f)
        ev["current_code"] = cs._nv_code_key(f.get("current_code"))
        return {"decision": kind, "reason": reason, "at_pass": 2,
                "evidence": ev}

    # -- the seed and archive locations ------------------------------------ #
    def test_format_subdir_matches_the_plugin_rule(self):
        self.assertEqual(hv.FORMAT_SUBDIR, hs.statepath.FORMAT_SUBDIR)

    def test_seed_and_archive_live_under_format_53(self):
        self.assertIn("/.turingmind/state/format-53/", str(self.seed_path))
        self.happy()
        self.assertEqual(hv._archived_states(self.copy), [self.archive_path()])

    def test_legacy_only_archive_fails_with_a_named_reason(self):
        led = self.happy()
        rel = self.legacy_copy(move=True)
        r = self.verdict_of(led)
        self.assertEqual(r.status, "FAILED")
        self.assertIn("state not archived", r.reasons)
        self.assertIn(hv.LEGACY_STATE_PROBLEM_PREFIX + rel
                      + hv.LEGACY_STATE_PROBLEM_SUFFIX, r.reasons)

    def test_legacy_beside_format_53_judges_format_53_only(self):
        led = self.happy()
        self.legacy_copy(move=False)
        r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_mutant_legacy_glob_base_reads_the_stale_archive(self):
        led = self.happy()
        self.legacy_copy(move=False)
        with mock.patch.object(hv, "_archived_states",
                               _legacy_archived_states):
            r = self.verdict_of(led)
        self.assertIn("multiple archived states", r.reasons)

    def test_mutant_legacy_glob_accepts_a_legacy_only_close_out(self):
        led = self.happy()
        self.legacy_copy(move=True)
        with mock.patch.object(hv, "_archived_states",
                               _legacy_archived_states), \
                mock.patch.object(hv, "_legacy_state_files",
                                  lambda copy: []):
            r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    # -- undecided Needs-verification -------------------------------------- #
    NV_REASONS = ["outstanding findings at finalize: 1",
                  "undecided Needs-verification at finalize: 1"]

    def _nv_case(self):
        nv = self.nv_row(H("NV"))
        led = self.happy(extra_open=[nv])
        c = self.counts(self.st.state([self.pass2_resolved(
            self.fix, findings=[nv])]))
        self.assertEqual((c["outstanding_cw"], c["unacknowledged_medium"],
                          c["undecided_nv"]), (0, 0, 1))
        return led

    def test_undecided_nv_at_finalize_fails(self):
        led = self._nv_case()
        r = self.verdict_of(led)
        self.assertEqual(r.reasons, self.NV_REASONS)

    def test_mutant_outstanding_without_nv_flips(self):
        led = self._nv_case()
        with mock.patch.object(
                hv, "_outstanding",
                lambda c: int(c["outstanding_cw"])
                + int(c["unacknowledged_medium"])):
            r = self.verdict_of(led)
        self.assertEqual(r.reasons,
                         ["undecided Needs-verification at finalize: 1"])

    def test_mutant_nv_count_zero_certifies_a_false_close_out(self):
        led = self._nv_case()
        real = hv._finalize_counts

        def no_nv(*a):
            c = real(*a)
            return None if c is None else dict(c, undecided_nv=0)
        with mock.patch.object(hv, "_finalize_counts", no_nv):
            r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_nv_row_is_deferred_through_the_real_finalize_card(self):
        """The plugin renders the finalize card for an archived-shape state
        holding the NV row; harness_cards answers it under the harness policy
        (defer with the harness reason, never a fix); that decision, written
        back, leaves no undecided NV and the verdict COMPLETE."""
        import harness_cards as hc
        nv = self.nv_row(H("NV"))
        head = self.fix
        state = self.st.state([self.pass2_resolved(head, findings=[nv])])
        blobs = os.path.join(self.tmp, "card-blobs.json")
        with open(blobs, "w", encoding="utf-8") as fh:
            json.dump({}, fh)
        proc = subprocess.run(
            [sys.executable, str(hf.PLUGIN_SCRIPTS_DIR / "batch_card.py"),
             "rows", "--mode", "finalize", "--head-blobs", blobs],
            input=json.dumps(state),
            capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        doc = json.loads(proc.stdout)
        self.assertIn("(needs-verification)", doc["card_text"])
        bp = hc.batch_parse
        card = {"questions": [
            {"header": "Decide", "multiSelect": False,
             "question": "Finalize — 1 undecided finding(s) listed below. "
                         "What should happen to them?\n\n"
                         + doc["card_text"],
             "options": [{"label": x, "description": x}
                         for x in bp.FINALIZE_Q1]},
            {"header": "Reason", "multiSelect": False,
             "question": "One reason for everything dismissed or deferred.",
             "options": [{"label": x, "description": x}
                         for x in bp.FINALIZE_Q2]}]}
        self.assertEqual(hc.classify_card(card), hc.FINALIZE)
        d = hc.answer_card(hc.FINALIZE, card, seeded=self.seed_path
                           .seeded_identity, seeded_resolved=True)
        self.assertIsNone(d.fail)
        q1 = card["questions"][0]["question"]
        self.assertEqual(d.answers[q1], "defer 1 -- %s" % hc.DEFER_REASON)
        self.assertEqual(d.deferred_non_seeded, 1)
        led = self.ledger((state, "turn_end", head))
        archived = copymod.deepcopy(state)
        archived["decisions"] = {H("NV"): self.nv_decision(
            nv, reason=hc.DEFER_REASON)}
        self.assertEqual(self.counts(archived)["undecided_nv"], 0)
        self.finalize(archived)
        r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[H("NV")], "decided")

    # -- vanished obligations on a format-53 archive ----------------------- #
    def test_vanished_seeded_obligation_fails(self):
        head = self.fix
        state = self.st.state([self.st.pass_entry(2, head, [])])
        led = self.ledger((state, "turn_end", head))
        self.finalize(state)
        self.assertEqual(hv._archived_states(self.copy), [self.archive_path()])
        r = self.verdict_of(led)
        self.assertIn("obligation dropped without decision: %s"
                      % sha7(self.S), r.reasons)
        self.assertIn("seeded finding not verified resolved: %s"
                      % sha7(self.S), r.reasons)
        self.assertEqual(r.dispositions[self.S], "missing")

    def test_vanished_deferred_obligation_fails(self):
        n1 = self.st.finding(self.N1, "warning", UNTOUCHED, 5)
        s1, s2 = self.two_passes([n1], [])
        s1["decisions"] = {self.N1: decision(n1)}
        led = self.ledger((s1, "card", self.pre), (s2, "turn_end", self.fix))
        archived = copymod.deepcopy(s2)
        archived["decisions"] = {self.N1: decision(n1)}
        self.finalize(archived)
        r = self.verdict_of(led)
        self.assertEqual(r.reasons, ["obligation dropped without decision: %s"
                                     % sha7(self.N1)])
        self.assertEqual(r.dispositions[self.N1], "missing")

    # -- reasoned defer/dismiss decisions are preserved -------------------- #
    def _decided_case(self, kind, reason=REASON):
        n1 = self.st.finding(self.N1, "warning", UNTOUCHED, 5)
        s1, s2 = self.two_passes([n1], [copymod.deepcopy(n1)])
        led = self.n_ledger(s1, s2)
        archived = copymod.deepcopy(s2)
        archived["decisions"] = {self.N1: decision(n1, reason=reason,
                                                   kind=kind)}
        self.finalize(archived)
        return led

    def test_reasoned_defer_is_preserved_as_decided(self):
        r = self.verdict_of(self._decided_case("defer"))
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[self.N1], "decided")

    def test_reasoned_dismiss_is_preserved_as_decided(self):
        r = self.verdict_of(self._decided_case("dismiss"))
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[self.N1], "decided")

    def test_mutant_stripped_reason_is_named(self):
        r = self.verdict_of(self._decided_case("defer", reason=" "))
        self.assertEqual(r.reasons, ["obligation decision without reason: %s"
                                     % sha7(self.N1)])


class TestBandDowngrade(_Conservation):
    def _n8(self, decided=False, first_band="warning"):
        n3a = self.st.finding(self.N3, first_band, UNTOUCHED, 7)
        n3b = self.st.finding(self.N3, "low", UNTOUCHED, 7, at_pass=3)
        s1, s2 = self.two_passes([n3a], [n3b])
        led = self.ledger((s1, "card", self.pre), (s2, "turn_end", self.fix))
        archived = copymod.deepcopy(s2)
        if decided:
            archived["decisions"] = {self.N3: decision(n3b)}
        c = self.counts(archived)
        self.assertEqual((c["outstanding_cw"], c["unacknowledged_medium"]),
                         (0, 0))
        self.finalize(archived)
        return led

    def test_n8_band_downgrade_fails(self):
        led = self._n8()
        self.assertEqual(led.first_seen[self.N3]["bands_seen"],
                         ["low", "warning"])
        r = self.verdict_of(led)
        self.assertEqual(r.reasons, ["obligation downgraded without decision: "
                                     "%s" % sha7(self.N3)])
        self.assertEqual(r.dispositions[self.N3], "downgraded")

    def test_n8b_band_downgrade_decided_is_complete(self):
        r = self.verdict_of(self._n8(decided=True))
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[self.N3], "decided")

    def test_n8c_band_downgrade_never_blocking_is_visible_open(self):
        r = self.verdict_of(self._n8(first_band="low"))
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[self.N3], "visible_open")

    def test_m19_red_green_downgrade(self):
        led = self._n8()
        with mock.patch.object(hv, "_ever_blocking",
                               lambda first, band: band in
                               hv._carry_state().BLOCKING_BANDS):
            r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[self.N3], "visible_open")

    def test_m19b_band_downgrade_accumulation(self):
        def overwrite_bands(self_, snapshot, label, head_sha):
            _REAL_OBSERVE(self_, snapshot, label, head_sha)
            for h, entry in (snapshot or {}).get("hashes", {}).items():
                self_.first_seen[h]["bands_seen"] = [entry["band"]]
        with mock.patch.object(hv.ObligationLedger, "observe",
                               overwrite_bands):
            led = self._n8()
        self.assertEqual(led.first_seen[self.N3]["bands_seen"], ["low"])
        r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[self.N3], "visible_open")


class TestRegression(_Conservation):
    def _n9(self, line=None, first_pre=False, decided=False, resolved=False,
            band="low"):
        span = hv.repair_span_in_head(self.copy, RECIPE, self.pre)
        self.assertIsNotNone(span)
        g_hash = H("G")
        g_line = span.s if line is None else line
        g = self.st.finding(g_hash, band, FIXED, g_line, status="new",
                            at_pass=3)
        s1, s2 = self.two_passes([g] if first_pre else [], [g])
        led = self.ledger((s1, "card", self.pre), (s2, "turn_end", self.fix))
        if not first_pre:
            self.assertNotIn(g_hash, led.snapshots[1]["hashes"])
        archived = copymod.deepcopy(s2)
        if decided:
            archived["decisions"] = {g_hash: decision(g)}
        if resolved:
            archived["passes"].append(self.st.pass_entry(
                4, self.fix, [], [States.resolved(g, 4, self.fix)]))
        c = self.counts(archived)
        self.assertEqual((c["outstanding_cw"], c["unacknowledged_medium"]),
                         (0, 0))
        self.finalize(archived)
        return g_hash, led

    def test_n9_regression_fails(self):
        g, led = self._n9()
        r = self.verdict_of(led)
        self.assertEqual(r.reasons, ["regression finding not resolved: %s"
                                     % sha7(g)])
        self.assertEqual(r.dispositions[g], "regression")

    def test_n9b_regression_decided_still_fails(self):
        g, led = self._n9(decided=True)
        r = self.verdict_of(led)
        self.assertEqual(r.reasons, ["regression finding not resolved: %s"
                                     % sha7(g)])

    def test_n9c_regression_resolved_is_complete(self):
        g, led = self._n9(resolved=True)
        r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[g], "resolved")

    def test_n9d_regression_outside_span_is_preexisting(self):
        g, led = self._n9(line=HELPER_LINE)
        r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[g], "visible_open")

    def test_n9e_regression_first_seen_prefix_is_preexisting(self):
        g, led = self._n9(first_pre=True)
        r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[g], "visible_open")

    def _n9f(self):
        g_hash = H("G")
        gf = self.st.finding(g_hash, "low", FIXED, None, status="new",
                             at_pass=3)
        s1, s2 = self.two_passes([], [gf])
        led = self.ledger((s1, "card", self.pre), (s2, "turn_end", self.fix))
        self.finalize(copymod.deepcopy(s2))
        return g_hash, led

    def test_n9f_regression_unparseable_line_fails_closed(self):
        g, led = self._n9f()
        r = self.verdict_of(led)
        self.assertEqual(r.reasons, ["regression finding not resolved: %s"
                                     % sha7(g)])

    def test_m20_red_green_regression(self):
        for name, build in (("n9", self._n9),
                            ("n9b", lambda: self._n9(decided=True)),
                            ("n9f", self._n9f)):
            with self.subTest(name):
                self.fresh()
                g, led = build()
                self.assertEqual(self.verdict_of(led).status, "FAILED")
                with mock.patch.object(hv, "_is_regression",
                                       lambda *a, **k: False):
                    r = self.verdict_of(led)
                self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_m21_post_fix_is_load_bearing(self):
        g, led = self._n9()
        with mock.patch.object(hv, "_post_fix", lambda *a, **k: False):
            r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))

    def test_m21b_regression_span_is_load_bearing(self):
        g, led = self._n9()
        with mock.patch.object(hv, "repair_span_in_head",
                               lambda *a, **k: None):
            r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))


class TestVisibleOpenAccounting(_Conservation):
    def test_n10_visible_open_accounting(self):
        n4 = H("N4")
        f = self.st.finding(n4, "low", UNTOUCHED, 3)
        s1, s2 = self.two_passes([f], [copymod.deepcopy(f)])
        led = self.ledger((s1, "card", self.pre), (s2, "turn_end", self.fix))
        self.finalize(copymod.deepcopy(s2))
        r = self.verdict_of(led)
        self.assertEqual((r.status, r.reasons), ("COMPLETE", []))
        self.assertEqual(r.dispositions[n4], "visible_open")
        # The record derivation 52-10 uses.
        visible = sorted(h for h, v in r.dispositions.items()
                         if v == "visible_open")
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible, [n4])


# --------------------------------------------------------------------------- #
# The ledger itself
# --------------------------------------------------------------------------- #
class TestLedger(unittest.TestCase):
    A, B = "a" * 64, "b" * 64

    def test_union_bands_and_round_trip(self):
        led = hv.ObligationLedger()
        led.observe({"pass_number": 1, "hashes": {
            self.A: {"band": "warning", "file": "x", "line": 1,
                     "absorbed_into": None},
            self.B: {"band": "medium", "file": "y", "line": 2,
                     "absorbed_into": self.A}}}, "seed", "0" * 40)
        led.mark_seeded([self.A])
        led.observe({"pass_number": 2, "hashes": {
            self.A: {"band": "low", "file": "x", "line": 1,
                     "absorbed_into": None}}}, "card", "1" * 40)
        led.observe(None, "final", "1" * 40)
        self.assertEqual(set(led.all_hashes()), {self.A, self.B})
        self.assertEqual(led.first_seen[self.A]["bands_seen"],
                         ["low", "warning"])
        self.assertEqual(led.first_seen[self.A]["band"], "warning")
        self.assertEqual(led.first_seen[self.B]["absorbed_into"], self.A)
        self.assertEqual(led.snapshots[2], {"index": 2, "label": "final",
                                            "head_sha": "1" * 40,
                                            "absent": True})
        m = hv.ObligationLedger.from_json(led.to_json())
        self.assertEqual(m.first_seen, led.first_seen)
        self.assertEqual(m.snapshots, led.snapshots)
        self.assertEqual(m.seeded, {self.A})

    def test_bad_head_and_label_raise(self):
        led = hv.ObligationLedger()
        for head in ("", "xyz", "0" * 39, None):
            with self.assertRaises(ValueError):
                led.observe(None, "seed", head)
        with self.assertRaises(ValueError):
            led.observe(None, "whenever", "0" * 40)

    def test_malformed_snapshot_is_reported(self):
        led = hv.ObligationLedger()
        led.observe({"malformed": True}, "card", "0" * 40)
        rec = hv.reconcile_obligations(
            led, {"medium_acknowledgments": {}, "passes": [
                {"pass_number": 1, "findings": []}]}, {}, "0" * 40, None)
        self.assertIn("state malformed at snapshot 0", rec.problems)

    def test_snapshot_is_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "s.json")
            self.assertIsNone(hv.snapshot_obligations(path))
            Path(path).write_text(json.dumps({"medium_acknowledgments": {},
                                              "passes": "x"}))
            before = os.stat(path)
            self.assertEqual(hv.snapshot_obligations(path), {"malformed": True})
            after = os.stat(path)
            self.assertEqual((before.st_mtime_ns, before.st_size),
                             (after.st_mtime_ns, after.st_size))
            self.assertEqual(os.listdir(d), ["s.json"])


_REAL_OBSERVE = hv.ObligationLedger.observe


if __name__ == "__main__":
    unittest.main()
