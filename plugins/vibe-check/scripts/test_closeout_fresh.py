"""Tests for Close out freshness (FRESH-01, FRESH-02): a deferred or dismissed
finding must not stay closed at Close out once the code it was decided on has
changed on disk since the last review.

BEHAVIOUR UNDER TEST. One finding at src/a.py:10 is reviewed on a committed
tree and the owner defers or dismisses it. The code is then edited WITHOUT a
new review (the working tree counts, D-04) and Finalize's helper
(`finalize_inputs.py`) runs with all three switches false:

  - edit at line 10 (cause `line`) or at 13/15 (cause `nearby`, inside the
    +/- 5 window): the helper must refuse the Close out with
    `next` = "stop-review-again" and one `stale` row naming the hash, the
    decision kind and the cause; no report, state file untouched.
  - no edit, or an edit at 16 or 4 (outside the window): the helper must
    behave exactly as 2.15.0 did.

GATE-07 RULE. Every repair starts from a reproduction that fails on 2.15.0
and from unchanged-code controls that pass on both 2.15.0 and the candidate.
The 2.15.0 side is the LITERAL old procedure: the helper and every sibling it
imports, materialized from commit d5acc19 with `git show` into a temp dir and
run as a subprocess of its own script (its own `sys.path.insert` resolves the
siblings from that temp dir, so nothing in this process is shared). A
byte-identity test proves each materialized file is the d5acc19 blob.

  - `test_repro_999_40_old_helper_*`: the literal d5acc19 helper keeps the
    stale decision (action "write"): the 999.40 wrong keep, reproduced.
  - `test_repro_999_40_candidate_*`: the working-tree helper must refuse.
  - `test_differential_*`: on unchanged code both sides agree.

COMPARISON RULE (the differential). Both sides are subprocesses
(`run_old` on the materialized script, `run_new_cli` on the working-tree
script) with the same argv, cwd, environment, stdin (/dev/null) and timeout;
the result compared is the raw `(returncode, stdout bytes)` with no decoding,
stripping or normalisation on either side. The in-process `run_new` is used
only for parsed-JSON shape assertions and is never byte-compared against the
old side.

MUTANT STRATEGY. Guards in `closeout_fresh.py` are checked by loading a
source-substituted copy of the module (house style: assert the replaced text
is present, replace once, exec under a non-main name) and showing the guarded
fixture goes through; each mutant must make a named test here fail.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import closeout_fresh  # noqa: E402  (contract under test: NEXT_REVIEW_AGAIN)
import finalize_inputs  # noqa: E402  (the candidate helper, in-process)
import gitfixture  # noqa: E402  (shared temp-repo helper)
import test_decision_continuity as tdc  # noqa: E402  (pass1, base_file, F)
from gitfixture import git, write  # noqa: E402
from test_finalize_inputs import argv_for, sha256_of, tree_listing  # noqa: E402

NEW_HELPER = os.path.join(SCRIPTS_DIR, "finalize_inputs.py")

# The 2.15.0 release commit (PR #12 squash). The old side of every
# differential is the helper exactly as committed there.
V215_COMMIT = "d5acc19"
V215_REL = "plugins/vibe-check/scripts/"
# finalize_inputs.py and every sibling it imports at d5acc19, transitively
# (batch_card imports batch_parse; fixcommit imports guard). Any other import
# in these files is stdlib.
V215_MODULES = ("finalize_inputs.py", "carry_state.py", "finalize_gate.py",
                "batch_card.py", "batch_parse.py", "guard.py", "fixcommit.py")
CALL_TIMEOUT = 120

KIND_WORD = {"defer": "deferred", "dismiss": "dismissed"}
REPRO_EDITS = ((10, "line"), (13, "nearby"), (15, "nearby"))
CONTROL_EDITS = (None, 16, 4)
ZERO_COUNTS = {"outstanding_cw": 0, "unacknowledged_medium": 0,
               "undecided_nv": 0, "outstanding_cw_hashes": [],
               "unacknowledged_medium_hashes": [], "undecided_nv_hashes": [],
               "verified_obsolete_hashes": [],
               "confirmed_fix_awaiting_recheck_hashes": []}


def clean_env():
    """os.environ with the developer's git config off and no inherited
    `GIT_*` variable (a hook or a linked worktree may set GIT_DIR)."""
    env = gitfixture.helper_env()
    for key in list(env):
        if key.startswith("GIT_") and key not in ("GIT_CONFIG_GLOBAL",
                                                  "GIT_CONFIG_NOSYSTEM"):
            del env[key]
    return env


def _git_show(spec):
    proc = subprocess.run(
        ["git", "show", spec], cwd=SCRIPTS_DIR, env=clean_env(),
        stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
    if proc.returncode != 0:
        raise AssertionError("cannot read %s at %s (needs full history): %s"
                             % (spec, V215_COMMIT,
                                proc.stderr.decode(errors="replace")))
    return proc.stdout


def materialize_v215(case):
    """Write every V215_MODULES file as committed at d5acc19 into a fresh temp
    dir (removed when `case` ends, on every path) -> the dir."""
    tmp = tempfile.mkdtemp(prefix="v215-")
    case.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
    for name in V215_MODULES:
        data = _git_show(V215_COMMIT + ":" + V215_REL + name)
        with open(os.path.join(tmp, name), "wb") as fh:
            fh.write(data)
    return tmp


def _run_script(script, argv, cwd):
    proc = subprocess.run([sys.executable, script, *argv], cwd=cwd,
                          env=gitfixture.helper_env(),
                          stdin=subprocess.DEVNULL, capture_output=True,
                          timeout=CALL_TIMEOUT)
    return proc.returncode, proc.stdout


def run_old(tmp, argv, cwd):
    """The literal 2.15.0 helper as a subprocess -> (returncode, stdout bytes)."""
    return _run_script(os.path.join(tmp, "finalize_inputs.py"), argv, cwd)


def run_new_cli(argv, cwd):
    """The working-tree helper by the SAME recipe as `run_old` ->
    (returncode, stdout bytes). The only candidate side a byte comparison may
    use."""
    return _run_script(NEW_HELPER, argv, cwd)


def run_new(argv, cwd):
    """The working-tree helper in-process -> (code, stdout text). For parsed
    JSON shape assertions only; never byte-compared with the old side."""
    return finalize_inputs.run(argv, cwd=cwd)


class FreshCase(unittest.TestCase):
    """Base: an isolated temp dir, git config off, the d5acc19 helper
    materialized. Each scenario gets its own repo (`repro_state`)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        env = gitfixture.helper_env()
        env["GIT_CEILING_DIRECTORIES"] = self.tmp
        self._env = mock.patch.dict(os.environ, env, clear=True)
        self._env.start()
        self.v215 = materialize_v215(self)
        self._n = 0

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def repro_state(self, kind, edit=None):
        """The 999.40 scenario in a new repo -> (state_file, hash).

        src/a.py (60 distinct lines) is committed; pass 1 reviews it with one
        finding at line 10 that the owner decides (`kind`); the last pass
        records the real HEAD and `HEAD^{tree}` as the reviewed tree. Then
        `edit` (None, or a line number) rewrites that line on disk WITHOUT a
        commit. The state file lives outside the repo."""
        self._n += 1
        case_dir = os.path.join(self.tmp, "case%d" % self._n)
        os.makedirs(case_dir)
        self.repo = gitfixture.make_repo(case_dir)
        lines = tdc.base_file()
        write(self.repo, tdc.F, "\n".join(lines) + "\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "x")
        state, h = tdc.pass1(lines, conf=95, kind=kind)
        last = state["passes"][-1]
        last["head_sha"] = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        last["reviewed_tree"] = git(self.repo, "rev-parse",
                                    "HEAD^{tree}").stdout.strip()
        state_file = os.path.join(case_dir, "state.json")
        with open(state_file, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        if edit is not None:
            edited = list(lines)
            edited[edit - 1] = "line_%02d = danger()" % edit
            write(self.repo, tdc.F, "\n".join(edited) + "\n")
        self.blob_out = os.path.join(case_dir, "blobs.json")
        return state_file, h

    def argv(self, state_file):
        """The Close out call (three switches false) on a fresh, empty
        fingerprint file at the case's fixed path."""
        with open(self.blob_out, "wb"):
            pass
        return argv_for(state_file, self.blob_out)

    def unchanged(self, state_file, fn):
        """Run `fn()`; assert the state file bytes and the repo's file list
        are unchanged (D-03: state untouched; only the fingerprint file,
        outside the repo, is written)."""
        before, listing = sha256_of(state_file), tree_listing(self.repo)
        out = fn()
        self.assertEqual(sha256_of(state_file), before, "state file written")
        self.assertEqual(tree_listing(self.repo), listing,
                         "repo gained or lost a file")
        return out

    def run_old_case(self, state_file):
        return self.unchanged(state_file, lambda: run_old(
            self.v215, self.argv(state_file), self.repo))

    def run_new_case(self, state_file):
        return self.unchanged(state_file, lambda: run_new(
            self.argv(state_file), self.repo))

    def run_both(self, state_file):
        """(old, new): both `(returncode, stdout bytes)` from subprocesses
        given byte-identical argv, cwd, env, stdin and timeout."""
        old = self.run_old_case(state_file)
        new = self.unchanged(state_file, lambda: run_new_cli(
            self.argv(state_file), self.repo))
        return old, new


class TestRepro999_40(FreshCase):

    def test_repro_999_40_old_helper_writes_on_exact_and_nearby_edit(self):
        for kind in ("defer", "dismiss"):
            for edit, _ in REPRO_EDITS:
                with self.subTest(kind=kind, edit=edit):
                    state_file, _ = self.repro_state(kind, edit)
                    code, out = self.run_old_case(state_file)
                    self.assertEqual(code, 0, out)
                    result = json.loads(out)
                    self.assertEqual(result["action"], "write")
                    self.assertEqual(result["next"], "write-review-md")
                    self.assertEqual(result["counts"], ZERO_COUNTS)
                    self.assertNotIn("stale", result)

    def test_repro_999_40_candidate_refuses_on_exact_and_nearby_edit(self):
        for kind in ("defer", "dismiss"):
            for edit, cause in REPRO_EDITS:
                with self.subTest(kind=kind, edit=edit):
                    state_file, h = self.repro_state(kind, edit)
                    code, out = self.run_new_case(state_file)
                    self.assertEqual(code, 0, out)
                    result = json.loads(out)
                    self.assertEqual(result["action"], "refuse")
                    self.assertEqual(result["next"],
                                     closeout_fresh.NEXT_REVIEW_AGAIN)
                    self.assertEqual(result["stale"][0]["kind"],
                                     KIND_WORD[kind])
                    self.assertEqual(result["stale"], [
                        {"hash": h, "kind": KIND_WORD[kind], "cause": cause}])
                    self.assertIsNone(result["report"])
                    self.assertNotIn("REVIEW.md", tree_listing(self.repo))

    def test_differential_unchanged_controls_identical_both_sides(self):
        for kind in ("defer", "dismiss"):
            for edit in CONTROL_EDITS:
                with self.subTest(kind=kind, edit=edit):
                    state_file, _ = self.repro_state(kind, edit)
                    old, new = self.run_both(state_file)
                    self.assertIsInstance(old[1], bytes)
                    self.assertIsInstance(new[1], bytes)
                    self.assertEqual(new, old)
                    self.assertEqual(old[0], 0, old[1])
                    self.assertEqual(json.loads(old[1])["action"], "write")

    def test_differential_materializer_is_literal_d5acc19(self):
        env = clean_env()
        for name in V215_MODULES:
            with self.subTest(module=name):
                old = subprocess.run(
                    ["git", "rev-parse", V215_COMMIT + ":" + V215_REL + name],
                    cwd=SCRIPTS_DIR, env=env, capture_output=True, text=True,
                    stdin=subprocess.DEVNULL, timeout=60)
                self.assertEqual(old.returncode, 0, old.stderr)
                now = subprocess.run(
                    ["git", "hash-object", "--no-filters",
                     os.path.join(self.v215, name)],
                    cwd=SCRIPTS_DIR, env=env, capture_output=True, text=True,
                    stdin=subprocess.DEVNULL, timeout=60)
                self.assertEqual(now.returncode, 0, now.stderr)
                self.assertEqual(now.stdout.strip(), old.stdout.strip())


if __name__ == "__main__":
    unittest.main()
