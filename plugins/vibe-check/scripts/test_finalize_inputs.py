"""Tests for finalize_inputs.py — the Finalize HEAD fingerprints, on real temp repos.

Behaviour tests build a state from the phase-45 loop fixture (the same file
test_carry_state.py drives), point its last-pass row at a file in a temp repo
from gitfixture.make_repo, and call `head_blobs` with the repo (or a directory
inside it) as the cwd. Every git call runs with global and system config
switched off (gitfixture.helper_env).

Validation-before-git tests wrap the real `_git` in a recorder and assert that a
refused file name appears in no git argv at all.

Mutant tests first assert the real behaviour, then remove one guard (by
`mock.patch.object` where a function or constant boundary exists, otherwise by
loading a source-substituted copy of the module, asserting the replaced text was
present) and show the guarded case goes through. Each guard is load-bearing.

`test_gap_*` tests pin inputs on which the helper could be stricter than the
2.14.1 instructions but deliberately is not.
"""

import ast
import copy
import hashlib
import importlib.util
import io
import itertools
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import batch_card  # noqa: E402  (oracle: the 2.14.1 report data)
import carry_state  # noqa: E402  (oracle: the 2.14.1 counts)
import finalize_gate  # noqa: E402  (oracle: the 2.14.1 gate)
import finalize_inputs  # noqa: E402  (module under test)
import gitfixture  # noqa: E402  (shared temp-repo helper)
from gitfixture import git, write  # noqa: E402

MODULE_PATH = os.path.join(SCRIPTS_DIR, "finalize_inputs.py")
FIXTURE = os.path.join(SCRIPTS_DIR, "fixtures", "phase45-loop-state.json")

ARCH_HASH = "5e78e90a6bf05e6a409b4aa3271e5e4df072735a074a9947a0a766a3d794af67"
BUGS_HASH = "7479a9b5fd5b36bce327aea4d49db8dcbe4193208c2b2ca3f1d3ac98368e6644"
MEMBER_HASH = "c" * 64


def load_fixture():
    with open(FIXTURE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def verdict(at_pass=2, kind="obsolete", blob="b1"):
    return {"verdict": kind, "agent": "fix", "head_sha": "50f9932e",
            "at_pass": at_pass, "reason": "line rewritten",
            "verified_blob": blob}


def row(state, h):
    return [r for r in state["passes"][-1]["findings"]
            if r["stable_hash"] == h][0]


def state_for(files, at_pass=2, kind="obsolete"):
    """The fixture with its two last-pass rows pointed at `files` (in order)
    and a fix verdict on each. `files` may hold one or two names."""
    s = load_fixture()
    s["fix_verdicts"] = {}
    for h, f in zip((ARCH_HASH, BUGS_HASH), files):
        row(s, h)["file"] = f
        s["fix_verdicts"][h] = verdict(at_pass=at_pass, kind=kind)
    return s


class Recorder:
    """Wraps the real `_git`, recording every argv; can fail chosen calls."""

    def __init__(self, real, fail=None):
        self.real = real
        self.fail = fail
        self.calls = []

    def __call__(self, args, cwd):
        self.calls.append(list(args))
        if self.fail is not None and self.fail(args):
            return None
        return self.real(args, cwd)

    def argv_text(self):
        return [a for call in self.calls for a in call]

    def mentions(self, name):
        return any(name in a for a in self.argv_text())


class InputsCase(unittest.TestCase):
    """Base: a temp repo on main with src/a.ts, src/b.ts, sub/c.ts committed."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self.repo = gitfixture.make_repo(self.tmp)
        write(self.repo, "src/a.ts", "a1\n")
        write(self.repo, "src/b.ts", "b1\n")
        write(self.repo, "sub/c.ts", "c1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        env = gitfixture.helper_env()
        env["GIT_CEILING_DIRECTORIES"] = self.tmp
        self._env = mock.patch.dict(os.environ, env, clear=True)
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def blob(self, rel, cwd=None):
        return git(cwd or self.repo, "rev-parse", "HEAD:" + rel).stdout.strip()

    def run_helper(self, state, cwd=None, module=None, fail=None):
        mod = module or finalize_inputs
        rec = Recorder(mod._git, fail)
        with mock.patch.object(mod, "_git", rec):
            out = mod.head_blobs(state, cwd=self.repo if cwd is None else cwd)
        return out, rec

    def mutant(self, old, new):
        """A copy of finalize_inputs with `old` replaced by `new` (once)."""
        with open(MODULE_PATH, "r", encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn(old, src, "mutant text must be present in the real source")
        src = src.replace(old, new, 1)
        spec = importlib.util.spec_from_loader("finalize_inputs_mutant",
                                               loader=None)
        mod = importlib.util.module_from_spec(spec)
        mod.__file__ = MODULE_PATH
        exec(compile(src, MODULE_PATH, "exec"), mod.__dict__)
        return mod


class TestFingerprints(InputsCase):

    def test_clean_committed_file_is_fingerprinted(self):
        out, _ = self.run_helper(state_for(["src/a.ts"]))
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})
        self.assertRegex(out["src/a.ts"], r"^[0-9a-f]{40}$")

    def test_uncommitted_edit_is_left_out(self):
        write(self.repo, "src/a.ts", "edited\n")
        out, _ = self.run_helper(state_for(["src/a.ts"]))
        self.assertEqual(out, {})

    def test_staged_only_change_is_left_out(self):
        # Index differs from HEAD; working tree back to HEAD's content.
        write(self.repo, "src/a.ts", "staged\n")
        git(self.repo, "add", "--", "src/a.ts")
        write(self.repo, "src/a.ts", "a1\n")
        self.assertEqual(git(self.repo, "diff", "--quiet", "HEAD", "--",
                             "src/a.ts", check=False).returncode, 0)
        out, _ = self.run_helper(state_for(["src/a.ts"]))
        self.assertEqual(out, {})

    def test_file_absent_at_head_is_left_out(self):
        write(self.repo, "src/new.ts", "untracked\n")
        out, _ = self.run_helper(state_for(["src/new.ts"]))
        self.assertEqual(out, {})
        out, _ = self.run_helper(state_for(["src/missing.ts"]))
        self.assertEqual(out, {})

    def test_two_verdicts_naming_one_file_give_one_entry(self):
        out, rec = self.run_helper(state_for(["src/a.ts", "src/a.ts"]))
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})
        revs = [c for c in rec.calls if c[:1] == ["rev-parse"]
                and c[1:2] == ["HEAD:src/a.ts"]]
        self.assertEqual(len(revs), 1)

    def test_two_files_both_fingerprinted(self):
        out, _ = self.run_helper(state_for(["src/a.ts", "src/b.ts"]))
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts"),
                               "src/b.ts": self.blob("src/b.ts")})

    def test_exact_git_calls(self):
        _, rec = self.run_helper(state_for(["src/a.ts"]))
        self.assertEqual(rec.calls, [
            ["rev-parse", "--show-toplevel"],
            ["rev-parse", "--show-prefix"],
            ["rev-parse", "HEAD:src/a.ts"],
            ["diff", "--quiet", "HEAD", "--", "src/a.ts"],
            ["diff", "--cached", "--quiet", "--", "src/a.ts"],
        ])

    def test_exact_git_calls_from_a_nested_subfolder(self):
        """From `<repo>/src/deep` the two `git diff` checks name the file
        from the top with one `../` per level; `HEAD:<file>` is already
        read from the top."""
        os.makedirs(os.path.join(self.repo, "src", "deep"))
        deep = os.path.join(self.repo, "src", "deep")
        out, rec = self.run_helper(state_for(["src/a.ts"]), cwd=deep)
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})
        self.assertEqual(rec.calls, [
            ["rev-parse", "--show-toplevel"],
            ["rev-parse", "--show-prefix"],
            ["rev-parse", "HEAD:src/a.ts"],
            ["diff", "--quiet", "HEAD", "--", "../../src/a.ts"],
            ["diff", "--cached", "--quiet", "--", "../../src/a.ts"],
        ])

    def test_prefix_query_failing_leaves_every_file_out(self):
        out, rec = self.run_helper(
            state_for(["src/a.ts", "src/b.ts"]),
            fail=lambda a: a[:2] == ["rev-parse", "--show-prefix"])
        self.assertEqual(out, {})
        self.assertEqual(rec.calls, [["rev-parse", "--show-toplevel"],
                                     ["rev-parse", "--show-prefix"]])


class TestVerdictSelection(InputsCase):

    def test_verdict_at_an_earlier_pass_is_skipped(self):
        out, rec = self.run_helper(state_for(["src/a.ts"], at_pass=1))
        self.assertEqual(out, {})
        self.assertEqual(rec.calls, [])

    def test_applied_verdict_at_last_pass_is_fingerprinted(self):
        out, _ = self.run_helper(state_for(["src/a.ts"], kind="applied"))
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})

    def test_any_verdict_kind_at_last_pass_is_fingerprinted(self):
        out, _ = self.run_helper(state_for(["src/a.ts"], kind="something-else"))
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})

    def test_hash_matching_only_an_absorbed_member_is_skipped(self):
        s = state_for(["src/a.ts"])
        s["fix_verdicts"] = {MEMBER_HASH: verdict()}
        row(s, ARCH_HASH)["members"].append(
            {"file": "src/b.ts", "stable_hash": MEMBER_HASH,
             "obligation": {"stable_hash": MEMBER_HASH, "file": "src/b.ts"}})
        out, rec = self.run_helper(s)
        self.assertEqual(out, {})
        self.assertEqual(rec.calls, [])

    def test_recheck_settled_fingerprint_paths_are_not_fingerprinted(self):
        s = load_fixture()
        s["fix_verdicts"] = {}
        row(s, ARCH_HASH)["file"] = "src/a.ts"
        row(s, ARCH_HASH)["recheck_settled"] = {
            "verdict": "still-applies",
            "fingerprint": {"src/b.ts": self.blob("src/b.ts")}}
        out, rec = self.run_helper(s)
        self.assertEqual(out, {})
        self.assertEqual(rec.calls, [])

    def test_non_string_file_is_skipped(self):
        s = state_for(["src/a.ts", "src/b.ts"])
        row(s, ARCH_HASH)["file"] = 7
        out, _ = self.run_helper(s)
        self.assertEqual(out, {"src/b.ts": self.blob("src/b.ts")})

    def test_non_dict_verdict_is_skipped(self):
        s = state_for(["src/a.ts", "src/b.ts"])
        s["fix_verdicts"][ARCH_HASH] = "obsolete"
        out, _ = self.run_helper(s)
        self.assertEqual(out, {"src/b.ts": self.blob("src/b.ts")})


class TestValidationBeforeGit(InputsCase):

    def test_space_in_name_never_reaches_git(self):
        write(self.repo, "a b.ts", "x\n")
        git(self.repo, "add", "--", "a b.ts")
        git(self.repo, "commit", "-q", "-m", "space")
        out, rec = self.run_helper(state_for(["a b.ts", "src/a.ts"]))
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})
        self.assertFalse(rec.mentions("a b.ts"))

    def test_dotdot_never_reaches_git(self):
        write(self.tmp, "x", "outside\n")
        out, rec = self.run_helper(state_for(["../x", "src/a.ts"]))
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})
        self.assertFalse(rec.mentions("../x"))

    def test_absolute_path_outside_repo_never_reaches_git(self):
        outside = write(self.tmp, "outside.ts", "outside\n")
        self.assertTrue(finalize_inputs.PATH_RE.match(outside), outside)
        out, rec = self.run_helper(state_for([outside, "src/a.ts"]))
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})
        self.assertFalse(rec.mentions(outside))

    def test_no_last_pass_verdicts_runs_no_git(self):
        for s in (load_fixture(), state_for(["src/a.ts"], at_pass=1)):
            out, rec = self.run_helper(s)
            self.assertEqual(out, {})
            self.assertEqual(rec.calls, [])

    def test_no_last_pass_verdicts_outside_a_repo_runs_no_git(self):
        plain = os.path.join(self.tmp, "plain")
        os.makedirs(plain)
        for s in (load_fixture(), state_for(["src/a.ts"], at_pass=1)):
            out, rec = self.run_helper(s, cwd=plain)
            self.assertEqual(out, {})
            self.assertEqual(rec.calls, [])

    def test_candidates_outside_a_repo_give_empty_without_raising(self):
        plain = os.path.join(self.tmp, "plain")
        os.makedirs(plain)
        write(plain, "src/a.ts", "a1\n")
        out, rec = self.run_helper(state_for(["src/a.ts"]), cwd=plain)
        self.assertEqual(out, {})
        self.assertEqual(rec.calls, [["rev-parse", "--show-toplevel"]])

    def test_toplevel_git_unavailable_gives_empty(self):
        out, rec = self.run_helper(state_for(["src/a.ts"]),
                                   fail=lambda a: a[:2] == ["rev-parse",
                                                            "--show-toplevel"])
        self.assertEqual(out, {})
        self.assertEqual(rec.calls, [["rev-parse", "--show-toplevel"]])

    def test_git_unavailable_for_any_per_file_call_leaves_file_out(self):
        cases = {
            "rev-parse": lambda a: a[:2] == ["rev-parse", "HEAD:src/a.ts"],
            "worktree": lambda a: a[:2] == ["diff", "--quiet"],
            "index": lambda a: a[:2] == ["diff", "--cached"],
        }
        for name, fail in cases.items():
            with self.subTest(call=name):
                out, _ = self.run_helper(state_for(["src/a.ts"]), fail=fail)
                self.assertEqual(out, {})

    def test_real_git_runner_returns_none_when_git_cannot_run(self):
        with mock.patch.object(finalize_inputs.subprocess, "run",
                               side_effect=OSError("no git")):
            self.assertIsNone(finalize_inputs._git(["rev-parse", "HEAD"],
                                                   self.repo))
        with mock.patch.object(
                finalize_inputs.subprocess, "run",
                side_effect=subprocess.TimeoutExpired(["git"], 60)):
            self.assertIsNone(finalize_inputs._git(["rev-parse", "HEAD"],
                                                   self.repo))

    def test_real_git_runner_returns_code_and_stdout_only(self):
        code, out = finalize_inputs._git(["rev-parse", "HEAD:nope.ts"],
                                         self.repo)
        self.assertNotEqual(code, 0)
        self.assertIsInstance(out, str)
        self.assertNotIn("fatal", out)

    def test_malformed_states_give_empty_and_never_raise(self):
        bad = [None, 7, "s", [], {}, {"passes": []}, {"passes": "x"},
               {"passes": [7]}, {"passes": [{}]},
               {"passes": [{"pass_number": 1}]},
               {"passes": [{"pass_number": 1, "findings": "x"}],
                "fix_verdicts": {}},
               {"passes": [{"pass_number": 1, "findings": []}],
                "fix_verdicts": []},
               {"passes": [{"pass_number": 1, "findings": [7]}],
                "fix_verdicts": {"h": {"at_pass": 1}}}]
        broken = state_for(["src/a.ts"])
        broken["fix_verdicts"] = None
        bad.append(broken)
        for s in bad:
            with self.subTest(state=repr(s)[:60]):
                out, _ = self.run_helper(copy.deepcopy(s))
                self.assertEqual(out, {})


class TestParityGaps(InputsCase):
    """Inputs where the helper could be stricter than 2.14.1 and is not (D-06)."""

    def test_gap_at_pass_true_matches_pass_one(self):
        s = load_fixture()
        s["passes"] = s["passes"][:1]
        h = s["passes"][0]["findings"][0]["stable_hash"]
        s["passes"][0]["findings"][0]["file"] = "src/a.ts"
        s["fix_verdicts"] = {h: verdict(at_pass=True)}
        self.assertEqual(s["passes"][-1]["pass_number"], 1)
        out, _ = self.run_helper(s)
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})


class TestSubdirectoryCwd(InputsCase):
    """D-19: from a subfolder, every check reads the file from the repo root.

    At 2.14.1 the two `git diff` checks ran in the session's folder, where the
    pathspec after `--` is read relative to that folder: from `<repo>/sub`,
    `sub/c.ts` meant `sub/sub/c.ts`, matched nothing and exited 0, so a file
    with an uncommitted edit was fingerprinted. The helper reads from the root.
    """

    def setUp(self):
        super().setUp()
        self.sub = os.path.join(self.repo, "sub")
        self.rel = "sub/c.ts"

    def plain_subfolder_exit_codes(self):
        rel = self.rel
        return [git(self.sub, "rev-parse", "HEAD:" + rel,
                    check=False).returncode,
                git(self.sub, "diff", "--quiet", "HEAD", "--", rel,
                    check=False).returncode,
                git(self.sub, "diff", "--cached", "--quiet", "--", rel,
                    check=False).returncode]

    def test_clean_file_is_fingerprinted_from_a_subfolder(self):
        out, _ = self.run_helper(state_for([self.rel]), cwd=self.sub)
        self.assertEqual(out, {self.rel: self.blob(self.rel)})

    def test_edited_file_is_not_fingerprinted_from_a_subfolder(self):
        write(self.repo, self.rel, "c2\n")
        # The 2.14.1 reproduction: the plain calls from the subfolder all pass.
        self.assertEqual(self.plain_subfolder_exit_codes(), [0, 0, 0])
        out, _ = self.run_helper(state_for([self.rel]), cwd=self.sub)
        self.assertEqual(out, {})

    def test_staged_file_is_not_fingerprinted_from_a_subfolder(self):
        write(self.repo, self.rel, "staged\n")
        git(self.repo, "add", "--", self.rel)
        write(self.repo, self.rel, "c1\n")
        self.assertEqual(self.plain_subfolder_exit_codes(), [0, 0, 0])
        out, _ = self.run_helper(state_for([self.rel]), cwd=self.sub)
        self.assertEqual(out, {})

    def test_edited_file_is_not_fingerprinted_from_a_nested_subfolder(self):
        write(self.repo, "src/deep/d.ts", "d1\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "deep")
        write(self.repo, self.rel, "c2\n")
        deep = os.path.join(self.repo, "src", "deep")
        out, _ = self.run_helper(state_for([self.rel]), cwd=deep)
        self.assertEqual(out, {})


ROOT_AS_CWD = (
    ('        rev = _git(["rev-parse", "HEAD:" + f], cwd)\n',
     '        rev = _git(["rev-parse", "HEAD:" + f], root)\n'),
    ('_git(["diff", "--quiet", "HEAD", "--", up + f], cwd)',
     '_git(["diff", "--quiet", "HEAD", "--", f], root)'),
    ('_git(["diff", "--cached", "--quiet", "--", up + f], cwd)',
     '_git(["diff", "--cached", "--quiet", "--", f], root)'),
)


class TestSessionRepository(InputsCase):
    """The three per-file checks read the session's own repository, as at
    2.14.1, even when the repo root text names another place. With git's
    `core.worktree` pointing elsewhere, `--show-toplevel` names that other
    folder; running the checks there (the merged helper's way) reads a
    different repository or none. `test_finalize_parity_grid.py` holds the
    same rows against the literal 2.14.1 step."""

    def root_as_cwd(self):
        """A copy of finalize_inputs running the three checks in the root
        path with the name as given (the merged helper's form)."""
        with open(MODULE_PATH, "r", encoding="utf-8") as fh:
            text = fh.read()
        for old, new in ROOT_AS_CWD:
            self.assertIn(old, text, "mutant text must be present")
            text = text.replace(old, new, 1)
        spec = importlib.util.spec_from_loader("finalize_inputs_root_cwd",
                                               loader=None)
        mod = importlib.util.module_from_spec(spec)
        mod.__file__ = MODULE_PATH
        exec(compile(text, MODULE_PATH, "exec"), mod.__dict__)
        return mod

    def other_tree(self, as_repo):
        other = os.path.join(self.tmp, "other")
        for rel in ("src/a.ts", "src/b.ts", "sub/c.ts"):
            with open(os.path.join(self.repo, rel), "r", encoding="utf-8") as fh:
                write(other, rel, fh.read())
        if as_repo:
            git(other, "init", "-q", "-b", "main")
            git(other, "add", "-A")
            git(other, "commit", "-q", "-m", "other")
        return other

    def test_core_worktree_at_another_repo_staged_edit_is_not_fingerprinted(self):
        blob = self.blob("src/a.ts")
        other = self.other_tree(as_repo=True)
        write(self.repo, "src/a.ts", "staged\n")
        git(self.repo, "add", "--", "src/a.ts")
        git(self.repo, "config", "core.worktree", other)
        s = state_for(["src/a.ts"])
        out, _ = self.run_helper(s)
        self.assertEqual(out, {})
        out, _ = self.run_helper(s, module=self.root_as_cwd())
        self.assertEqual(out, {"src/a.ts": blob})

    def test_core_worktree_at_a_plain_folder_clean_file_is_fingerprinted(self):
        blob = self.blob("src/a.ts")
        other = self.other_tree(as_repo=False)
        git(self.repo, "config", "core.worktree", other)
        s = state_for(["src/a.ts"])
        out, _ = self.run_helper(s)
        self.assertEqual(out, {"src/a.ts": blob})
        out, _ = self.run_helper(s, module=self.root_as_cwd())
        self.assertEqual(out, {})


class TestMutants(InputsCase):
    """Each guard removed in turn lets its own case through."""

    def test_mutant_no_char_filter_lets_space_reach_git(self):
        write(self.repo, "a b.ts", "x\n")
        git(self.repo, "add", "--", "a b.ts")
        git(self.repo, "commit", "-q", "-m", "space")
        s = state_for(["a b.ts"])
        out, rec = self.run_helper(s)
        self.assertEqual(out, {})
        self.assertFalse(rec.mentions("a b.ts"))
        with mock.patch.object(finalize_inputs, "PATH_RE", re.compile(r"^.+$")):
            out, rec = self.run_helper(s)
        self.assertTrue(rec.mentions("a b.ts"))
        self.assertEqual(out, {"a b.ts": self.blob("a b.ts")})

    def test_mutant_no_containment_lets_dotdot_reach_git(self):
        s = state_for(["../x"])
        out, rec = self.run_helper(s)
        self.assertEqual(out, {})
        self.assertFalse(rec.mentions("../x"))
        with mock.patch.object(finalize_inputs.guard, "contained",
                               return_value=(True, "contained")):
            _, rec = self.run_helper(s)
        self.assertTrue(rec.mentions("../x"))

    def test_mutant_no_worktree_check_includes_dirty_file(self):
        write(self.repo, "src/a.ts", "edited\n")
        s = state_for(["src/a.ts"])
        out, _ = self.run_helper(s)
        self.assertEqual(out, {})
        mod = self.mutant('_git(["diff", "--quiet", "HEAD", "--", up + f], cwd)',
                          "(0, '')")
        out, _ = self.run_helper(s, module=mod)
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})

    def test_mutant_no_index_check_includes_staged_file(self):
        write(self.repo, "src/a.ts", "staged\n")
        git(self.repo, "add", "--", "src/a.ts")
        write(self.repo, "src/a.ts", "a1\n")
        s = state_for(["src/a.ts"])
        out, _ = self.run_helper(s)
        self.assertEqual(out, {})
        mod = self.mutant('_git(["diff", "--cached", "--quiet", "--", up + f], cwd)',
                          "(0, '')")
        out, _ = self.run_helper(s, module=mod)
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})

    def test_mutant_name_read_from_session_folder_fingerprints_edit_from_subfolder(self):
        """Without the `../` lift the check is 2.14.1's: from `sub`, the name
        means `sub/sub/c.ts` and an edited file passes (D-19)."""
        sub = os.path.join(self.repo, "sub")
        write(self.repo, "sub/c.ts", "c2\n")
        s = state_for(["sub/c.ts"])
        out, _ = self.run_helper(s, cwd=sub)
        self.assertEqual(out, {})
        mod = self.mutant(
            '_git(["diff", "--quiet", "HEAD", "--", up + f], cwd)',
            '_git(["diff", "--quiet", "HEAD", "--", f], cwd)')
        out, _ = self.run_helper(s, cwd=sub, module=mod)
        self.assertEqual(out, {"sub/c.ts": self.blob("sub/c.ts")})

    def test_mutant_index_name_read_from_session_folder_fingerprints_staged_file(self):
        sub = os.path.join(self.repo, "sub")
        write(self.repo, "sub/c.ts", "staged\n")
        git(self.repo, "add", "--", "sub/c.ts")
        write(self.repo, "sub/c.ts", "c1\n")
        s = state_for(["sub/c.ts"])
        out, _ = self.run_helper(s, cwd=sub)
        self.assertEqual(out, {})
        mod = self.mutant(
            '_git(["diff", "--cached", "--quiet", "--", up + f], cwd)',
            '_git(["diff", "--cached", "--quiet", "--", f], cwd)')
        out, _ = self.run_helper(s, cwd=sub, module=mod)
        self.assertEqual(out, {"sub/c.ts": self.blob("sub/c.ts")})

    def test_mutant_unconditional_root_query_calls_git_with_no_candidates(self):
        s = state_for(["src/a.ts"], at_pass=1)
        _, rec = self.run_helper(s)
        self.assertEqual(rec.calls, [])
        mod = self.mutant("    if not files:\n        return {}\n",
                          "    _toplevel(cwd)\n"
                          "    if not files:\n        return {}\n")
        _, rec = self.run_helper(s, module=mod)
        self.assertEqual(rec.calls, [["rev-parse", "--show-toplevel"]])



# --------------------------------------------------------------------------- #
# The result: next action, counts, gate and report bundle.
# --------------------------------------------------------------------------- #
SIX_ROW = os.path.join(SCRIPTS_DIR, "fixtures", "iplayarr45-six-row-state.json")
ARCH_FILE = "plugins/vibe-check/phases/deep-review/01d-coverage.md"

SWITCH_NAMES = ("noninteractive", "pr_mode", "range_mode")
ALL_SWITCHES = [dict(zip(SWITCH_NAMES, combo))
                for combo in itertools.product((False, True), repeat=3)]
INTERACTIVE = {"noninteractive": False, "pr_mode": False, "range_mode": False}
RESULT_KEYS = {"action", "reason", "next", "counts", "report"}
COUNT_KEYS_EXPECTED = (
    "outstanding_cw", "unacknowledged_medium", "undecided_nv",
    "outstanding_cw_hashes", "unacknowledged_medium_hashes",
    "undecided_nv_hashes", "verified_obsolete_hashes",
    "confirmed_fix_awaiting_recheck_hashes")


def load_six_row():
    with open(SIX_ROW, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dismiss(state, hashes):
    out = carry_state.record_decisions(state, {
        "at_pass": state["passes"][-1]["pass_number"],
        "decisions": [{"stable_hash": h, "decision": "dismiss",
                       "reason": "walk"} for h in hashes]})
    assert out is not None
    return out


def dismissed_all_state():
    s = load_fixture()
    c = carry_state.finalize_counts(s)
    return dismiss(s, c["outstanding_cw_hashes"]
                   + c["unacknowledged_medium_hashes"]
                   + c["undecided_nv_hashes"])


def nv_open_state():
    """Only an undecided Needs-verification item open."""
    s = load_fixture()
    row(s, ARCH_HASH)["band"] = "needs-verification"
    return dismiss(s, [BUGS_HASH])


def medium_only_state():
    return dismiss(load_fixture(), [ARCH_HASH])


def fix_obsolete_state(blob):
    """The warning row closed by a last-pass fix-obsolete verdict on `blob`;
    the medium dismissed, so the gate writes when `blob` is HEAD's."""
    s = dismiss(load_fixture(), [BUGS_HASH])
    last = s["passes"][-1]
    s["fix_verdicts"] = {ARCH_HASH: dict(
        verdict(at_pass=last["pass_number"], kind="obsolete", blob=blob),
        head_sha=last["head_sha"])}
    return s


def oracle(state, blobs, switches):
    """What the three 2.14.1 helpers give, called in-process."""
    if state is None:
        counts = None
        flags = {"state_file_present": False, "outstanding_cw": 0,
                 "unacknowledged_medium": 0, "undecided_nv": 0}
    else:
        counts = carry_state.finalize_counts(state, blobs)
        flags = {"state_file_present": True,
                 "outstanding_cw": counts["outstanding_cw"],
                 "unacknowledged_medium": counts["unacknowledged_medium"],
                 "undecided_nv": counts["undecided_nv"]}
    flags.update(switches)
    gate = finalize_gate.run({"flags": flags})
    report = None
    if gate["action"] == "write":
        report = batch_card.decisions_report(state)
    return counts, gate, report


class ResultCase(InputsCase):
    """InputsCase plus ARCH_FILE committed, for the fix-obsolete state."""

    def setUp(self):
        super().setUp()
        write(self.repo, ARCH_FILE, "coverage\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "arch")

    def prepared(self):
        """(label, state, blobs) for each prepared state."""
        fix = fix_obsolete_state(self.blob(ARCH_FILE))
        fix_blobs = finalize_inputs.head_blobs(fix, cwd=self.repo)
        return [
            ("six-row", load_six_row(), {}),
            ("loop", load_fixture(), {}),
            ("dismissed-all", dismissed_all_state(), {}),
            ("nv-open", nv_open_state(), {}),
            ("medium-only", medium_only_state(), {}),
            ("fix-obsolete", fix, fix_blobs),
        ]


class TestNextAction(unittest.TestCase):

    def test_next_actions_are_the_seven_values_in_order(self):
        self.assertEqual(finalize_inputs.NEXT_ACTIONS, (
            "write-review-md", "finalize-card", "stop-fallback-cw",
            "stop-fallback-nv", "stop-fallback-medium", "stop-no-state",
            "stop-refused"))

    def test_exit_codes(self):
        f = finalize_inputs
        self.assertEqual((f.EXIT_OK, f.EXIT_USAGE, f.EXIT_STATE, f.EXIT_GATE,
                          f.EXIT_REPORT), (0, 2, 3, 4, 5))

    def test_count_keys_in_the_instruction_order(self):
        self.assertEqual(finalize_inputs.COUNT_KEYS, COUNT_KEYS_EXPECTED)

    def test_next_mapping(self):
        def counts(cw=0, nv=0, medium=0):
            return {"outstanding_cw": cw, "undecided_nv": nv,
                    "unacknowledged_medium": medium}
        cases = [
            ("write", counts(), "write-review-md"),
            ("outstanding-to-phase-5", counts(cw=1), "finalize-card"),
            ("outstanding-to-phase-5", counts(nv=1), "finalize-card"),
            ("medium-ack-loop", counts(medium=1), "finalize-card"),
            ("fallback", counts(cw=1), "stop-fallback-cw"),
            ("fallback", counts(cw=1, nv=1, medium=1), "stop-fallback-cw"),
            ("fallback", counts(nv=1), "stop-fallback-nv"),
            ("fallback", counts(nv=2, medium=1), "stop-fallback-nv"),
            ("fallback", counts(medium=1), "stop-fallback-medium"),
            ("fallback", counts(), "stop-fallback-medium"),
            ("error", counts(), "stop-no-state"),
            ("refuse", counts(), "stop-refused"),
            ("bogus", counts(), "stop-refused"),
            (None, counts(), "stop-refused"),
        ]
        for action, c, want in cases:
            with self.subTest(action=action, counts=c):
                got = finalize_inputs.next_action(action, c)
                self.assertEqual(got, want)
                self.assertIn(got, finalize_inputs.NEXT_ACTIONS)

    def test_every_gate_action_maps_into_next_actions(self):
        for action in finalize_gate.ACTIONS:
            with self.subTest(action=action):
                self.assertIn(finalize_inputs.next_action(
                    action, {"outstanding_cw": 0, "undecided_nv": 0,
                             "unacknowledged_medium": 0}),
                    finalize_inputs.NEXT_ACTIONS)


class TestBuildResultParity(ResultCase):

    def test_parity_with_the_three_helpers_on_every_prepared_state(self):
        for label, state, blobs in self.prepared():
            for sw in ALL_SWITCHES:
                with self.subTest(state=label, switches=sw):
                    code, result = finalize_inputs.build_result(
                        copy.deepcopy(state), blobs, dict(sw))
                    counts, gate, report = oracle(state, blobs, sw)
                    self.assertEqual(code, 0)
                    self.assertEqual(set(result), RESULT_KEYS)
                    self.assertEqual(result["counts"], counts)
                    self.assertEqual(tuple(result["counts"]),
                                     COUNT_KEYS_EXPECTED)
                    self.assertEqual({"action": result["action"],
                                      "reason": result["reason"]}, gate)
                    self.assertEqual(result["report"], report)
                    self.assertEqual(result["next"], finalize_inputs.next_action(
                        gate["action"], counts))

    def test_parity_actions_cover_the_branches(self):
        seen = set()
        for label, state, blobs in self.prepared():
            for sw in ALL_SWITCHES:
                _, result = finalize_inputs.build_result(
                    copy.deepcopy(state), blobs, dict(sw))
                seen.add((label, result["next"]))
        self.assertIn(("dismissed-all", "write-review-md"), seen)
        self.assertIn(("fix-obsolete", "write-review-md"), seen)
        self.assertIn(("six-row", "finalize-card"), seen)
        self.assertIn(("six-row", "stop-fallback-cw"), seen)
        self.assertIn(("nv-open", "stop-fallback-nv"), seen)
        self.assertIn(("medium-only", "stop-fallback-medium"), seen)
        self.assertIn(("medium-only", "finalize-card"), seen)

    def test_parity_write_carries_the_report_and_obsolete_hashes(self):
        fix = fix_obsolete_state(self.blob(ARCH_FILE))
        blobs = finalize_inputs.head_blobs(fix, cwd=self.repo)
        self.assertEqual(blobs, {ARCH_FILE: self.blob(ARCH_FILE)})
        code, result = finalize_inputs.build_result(fix, blobs, INTERACTIVE)
        self.assertEqual(code, 0)
        self.assertEqual(result["action"], "write")
        self.assertEqual(result["counts"]["verified_obsolete_hashes"],
                         [ARCH_HASH])
        self.assertEqual(result["report"], batch_card.decisions_report(fix))
        self.assertTrue(result["report"]["entries"])

    def test_parity_non_write_has_no_report(self):
        code, result = finalize_inputs.build_result(load_six_row(), {},
                                                    INTERACTIVE)
        self.assertEqual(code, 0)
        self.assertEqual(result["action"], "outstanding-to-phase-5")
        self.assertIsNone(result["report"])

    def test_parity_no_state(self):
        for sw in ALL_SWITCHES:
            with self.subTest(switches=sw):
                code, result = finalize_inputs.build_result(None, {}, dict(sw))
                self.assertEqual(code, 0)
                self.assertEqual(result["action"], "error")
                self.assertEqual(result["reason"],
                                 finalize_gate.REASON_NO_STATE)
                self.assertEqual(result["next"], "stop-no-state")
                self.assertIsNone(result["report"])
                self.assertEqual(tuple(result["counts"]), COUNT_KEYS_EXPECTED)
                for k in COUNT_KEYS_EXPECTED[:3]:
                    self.assertEqual(result["counts"][k], 0)
                for k in COUNT_KEYS_EXPECTED[3:]:
                    self.assertEqual(result["counts"][k], [])

    def test_parity_each_switch_alone_gives_fallback(self):
        for name in SWITCH_NAMES:
            sw = dict(INTERACTIVE, **{name: True})
            for label, state, want in (
                    ("six-row", load_six_row(), "stop-fallback-cw"),
                    ("nv-open", nv_open_state(), "stop-fallback-nv"),
                    ("medium-only", medium_only_state(),
                     "stop-fallback-medium")):
                with self.subTest(switch=name, state=label):
                    code, result = finalize_inputs.build_result(state, {}, sw)
                    self.assertEqual(code, 0)
                    self.assertEqual(result["action"], "fallback")
                    self.assertEqual(result["next"], want)

    def test_flags_passed_to_the_gate_are_exactly_the_seven(self):
        seen = []
        real = finalize_gate.run

        def spy(envelope):
            seen.append(copy.deepcopy(envelope))
            return real(envelope)

        with mock.patch.object(finalize_inputs.finalize_gate, "run", spy):
            finalize_inputs.build_result(load_six_row(), {}, INTERACTIVE)
        self.assertEqual(len(seen), 1)
        self.assertEqual(set(seen[0]), {"flags"})
        flags = seen[0]["flags"]
        self.assertEqual(set(flags), set(finalize_gate.FLAGS))
        for k in ("state_file_present",) + SWITCH_NAMES:
            self.assertIs(type(flags[k]), bool)
        for k in ("outstanding_cw", "unacknowledged_medium", "undecided_nv"):
            self.assertIs(type(flags[k]), int)


class TestBuildResultFailures(ResultCase):

    def test_refuse_malformed_state_gives_exit_state(self):
        for bad in ({}, {"passes": []}, {"passes": "x"}, [], 7):
            with self.subTest(state=repr(bad)):
                self.assertIsNone(carry_state.finalize_counts(bad))
                self.assertEqual(finalize_inputs.build_result(
                    bad, {}, INTERACTIVE), (finalize_inputs.EXIT_STATE, None))

    def test_refuse_report_none_on_write_gives_exit_report(self):
        # A1: no real state has finalize_counts succeed and decisions_report
        # return None (both refuse on carry_state.state_reason), so the
        # report's None is patched in.
        with mock.patch.object(finalize_inputs.batch_card, "decisions_report",
                               return_value=None):
            self.assertEqual(finalize_inputs.build_result(
                dismissed_all_state(), {}, INTERACTIVE),
                (finalize_inputs.EXIT_REPORT, None))

    def test_report_not_computed_on_non_write(self):
        with mock.patch.object(finalize_inputs.batch_card, "decisions_report",
                               side_effect=AssertionError("called")):
            code, result = finalize_inputs.build_result(load_six_row(), {},
                                                        INTERACTIVE)
        self.assertEqual(code, 0)
        self.assertIsNone(result["report"])

    def test_refuse_gate_raising_gives_exit_gate(self):
        with mock.patch.object(finalize_inputs.finalize_gate, "run",
                               side_effect=RuntimeError("boom")):
            self.assertEqual(finalize_inputs.build_result(
                load_six_row(), {}, INTERACTIVE),
                (finalize_inputs.EXIT_GATE, None))

    def test_refuse_gate_unknown_action_gives_exit_gate(self):
        for bad in ({"action": "approve", "reason": "x"}, {"reason": "x"},
                    None, "write", {"action": None}):
            with self.subTest(gate=repr(bad)):
                with mock.patch.object(finalize_inputs.finalize_gate, "run",
                                       return_value=bad):
                    self.assertEqual(finalize_inputs.build_result(
                        load_six_row(), {}, INTERACTIVE),
                        (finalize_inputs.EXIT_GATE, None))

    def test_refuse_gate_refuse_action_is_a_result(self):
        with mock.patch.object(finalize_inputs.finalize_gate, "run",
                               return_value={"action": "refuse",
                                             "reason": "malformed gate input"}):
            code, result = finalize_inputs.build_result(load_six_row(), {},
                                                        INTERACTIVE)
        self.assertEqual(code, 0)
        self.assertEqual(result["next"], "stop-refused")


class TestResultMutants(ResultCase):

    def test_mutant_report_exit_mapped_to_state_exit_trips(self):
        mod = self.mutant("return EXIT_REPORT, None",
                          "return EXIT_STATE, None")
        with mock.patch.object(mod.batch_card, "decisions_report",
                               return_value=None):
            code, _ = mod.build_result(dismissed_all_state(), {}, INTERACTIVE)
        self.assertEqual(code, 3)
        self.assertNotEqual(code, finalize_inputs.EXIT_REPORT)

    def test_mutant_report_on_non_write_trips(self):
        mod = self.mutant('    if action == "write":\n        source = ',
                          '    if True:\n        source = ')
        code, result = mod.build_result(load_six_row(), {}, INTERACTIVE)
        self.assertEqual(code, 0)
        self.assertIsNotNone(result["report"])
        _, real = finalize_inputs.build_result(load_six_row(), {}, INTERACTIVE)
        self.assertIsNone(real["report"])

    def test_mutant_dropping_undecided_nv_flag_trips(self):
        mod = self.mutant('"undecided_nv": int(counts["undecided_nv"]),', "")
        code, result = mod.build_result(dismissed_all_state(), {}, INTERACTIVE)
        self.assertEqual(code, 0)
        self.assertEqual(result["action"], "refuse")
        _, real = finalize_inputs.build_result(dismissed_all_state(), {},
                                               INTERACTIVE)
        self.assertEqual(real["action"], "write")



# --------------------------------------------------------------------------- #
# The command line: required switches, a fresh fingerprint file, exit codes.
# --------------------------------------------------------------------------- #
CARRY_STATE_PY = os.path.join(SCRIPTS_DIR, "carry_state.py")
BATCH_CARD_PY = os.path.join(SCRIPTS_DIR, "batch_card.py")
FINALIZE_GATE_PY = os.path.join(SCRIPTS_DIR, "finalize_gate.py")
GUARD_PY = os.path.join(SCRIPTS_DIR, "guard.py")  # unchanged since dd8e4ab
OWNER_SENTENCES = ("uncertain about Finalize", "Finalize stopped")
NOT_UTF8 = b'{"passes": "\xff\xfe"}'


def argv_for(state_file, blob_out, switches=None, drop=None, extra=()):
    sw = dict(INTERACTIVE, **(switches or {}))
    pairs = [("--state-file", state_file), ("--blob-out", blob_out),
             ("--noninteractive", "true" if sw["noninteractive"] else "false"),
             ("--pr-mode", "true" if sw["pr_mode"] else "false"),
             ("--range-mode", "true" if sw["range_mode"] else "false")]
    argv = []
    for flag, value in pairs:
        if flag != drop:
            argv += [flag, value]
    return argv + list(extra)


def sha256_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def tree_listing(root):
    out = set()
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirnames:
            dirnames.remove(".git")
        for name in filenames:
            out.add(os.path.relpath(os.path.join(dirpath, name), root))
    return out


class CliCase(ResultCase):
    """ResultCase plus a side folder for state and fingerprint files, and
    runners for the helper and the three 2.14.1 commands."""

    def setUp(self):
        super().setUp()
        self.files = os.path.join(self.tmp, "files")
        os.makedirs(self.files)
        self._n = 0

    def new_path(self, content=None, name=None):
        """A fresh path in the side folder; written when `content` is given
        (str, bytes, or a JSON-able object via `json.dumps`)."""
        self._n += 1
        path = os.path.join(self.files, name or "f%d" % self._n)
        if content is not None:
            if isinstance(content, bytes):
                data = content
            elif isinstance(content, str):
                data = content.encode("utf-8")
            else:
                data = json.dumps(content).encode("utf-8")
            with open(path, "wb") as fh:
                fh.write(data)
        return path

    def empty(self):
        return self.new_path(b"")

    def cli(self, argv, cwd=None):
        """Run the helper as a subprocess -> (code, stdout bytes, stderr
        bytes). The state file (if any) and the working tree are unchanged."""
        cwd = cwd or self.repo
        state = argv[argv.index("--state-file") + 1] \
            if "--state-file" in argv else None
        before = sha256_of(state) if state and os.path.isfile(state) else None
        listing = tree_listing(cwd)
        proc = subprocess.run([sys.executable, MODULE_PATH] + argv, cwd=cwd,
                              stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=120)
        if before is not None:
            self.assertEqual(sha256_of(state), before, "state file written")
        self.assertEqual(tree_listing(cwd), listing, "working tree gained a file")
        for text in OWNER_SENTENCES + ("Traceback",):
            self.assertNotIn(text.encode(), proc.stdout + proc.stderr)
        return proc.returncode, proc.stdout, proc.stderr

    def inproc(self, argv, module=None, cwd=None):
        """Run `run(argv)` in-process -> (code, stdout text, stderr text)."""
        mod = module or finalize_inputs
        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            code, out = mod.run(argv, cwd=cwd or self.repo)
        return code, out, err.getvalue()

    def old(self, script, args, stdin_path=None, stdin_bytes=None, env=None):
        """A 2.14.1 command as a subprocess -> (code, stdout, stderr) bytes.

        The 2.14.1 commands read the state from stdin as text, and Python
        picks stdin's error handler from the locale: strict on a UTF-8
        locale such as en_US.UTF-8, `surrogateescape` on C, POSIX and
        C.UTF-8. Only bytes that are not valid UTF-8 tell the two apart.
        The default environment pins strict UTF-8 standard streams
        (`PYTHONIOENCODING=utf-8:strict`, honoured by Python 3.4+ under
        every locale and in UTF-8 mode) so each comparison is against
        2.14.1 on a UTF-8 locale wherever the tests run.
        `test_named_difference_non_utf8_state_under_c_locale` covers the
        C locale. `env` replaces the default environment."""
        if stdin_path is not None:
            with open(stdin_path, "rb") as fh:
                stdin_bytes = fh.read()
        if env is None:
            env = dict(os.environ, PYTHONIOENCODING="utf-8:strict")
        proc = subprocess.run([sys.executable, script] + list(args),
                              cwd=self.repo, input=stdin_bytes or b"",
                              env=env, capture_output=True, timeout=120)
        return proc.returncode, proc.stdout, proc.stderr

    def old_counts(self, state_path, blob_path):
        return self.old(CARRY_STATE_PY, ["finalize-counts", "--head-blobs",
                                         blob_path], stdin_path=state_path)

    def old_report(self, state_path):
        return self.old(BATCH_CARD_PY, ["decisions-report"],
                        stdin_path=state_path)

    def old_gate(self, flags):
        return self.old(FINALIZE_GATE_PY, [],
                        stdin_bytes=json.dumps({"flags": flags}).encode())


class TestCliResult(CliCase):

    def test_parity_cli_result_equals_build_result(self):
        state = load_six_row()
        sp = self.new_path(state)
        bp = self.empty()
        code, out, err = self.cli(argv_for(sp, bp))
        self.assertEqual(code, 0)
        self.assertEqual(err, b"")
        blobs = finalize_inputs.head_blobs(state, cwd=self.repo)
        self.assertEqual(json.loads(out),
                         finalize_inputs.build_result(state, blobs,
                                                      INTERACTIVE)[1])
        with open(bp, "r", encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), blobs)

    def test_parity_cli_against_the_2141_commands(self):
        for label, state, _ in self.prepared():
            for sw in (INTERACTIVE, dict(INTERACTIVE, pr_mode=True)):
                with self.subTest(state=label, switches=sw):
                    sp = self.new_path(state)
                    bp = self.empty()
                    code, out, err = self.cli(argv_for(sp, bp, sw))
                    self.assertEqual((code, err), (0, b""))
                    got = json.loads(out)
                    c_code, c_out, _ = self.old_counts(sp, bp)
                    self.assertEqual(c_code, 0)
                    counts = json.loads(c_out)
                    self.assertEqual(got["counts"], counts)
                    flags = dict({"state_file_present": True,
                                  "outstanding_cw": counts["outstanding_cw"],
                                  "unacknowledged_medium":
                                      counts["unacknowledged_medium"],
                                  "undecided_nv": counts["undecided_nv"]}, **sw)
                    g_code, g_out, _ = self.old_gate(flags)
                    self.assertEqual(g_code, 0)
                    gate = json.loads(g_out)
                    self.assertEqual({"action": got["action"],
                                      "reason": got["reason"]}, gate)
                    if gate["action"] == "write":
                        r_code, r_out, _ = self.old_report(sp)
                        self.assertEqual(r_code, 0)
                        self.assertEqual(got["report"], json.loads(r_out))
                    else:
                        self.assertIsNone(got["report"])

    def test_parity_fix_obsolete_writes_through_the_cli(self):
        state = fix_obsolete_state(self.blob(ARCH_FILE))
        code, out, _ = self.cli(argv_for(self.new_path(state), self.empty()))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["action"], "write")

    def test_parity_rows_accepts_the_written_blob_file(self):
        sp = self.new_path(fix_obsolete_state(self.blob(ARCH_FILE)))
        bp = self.empty()
        self.assertEqual(self.cli(argv_for(sp, bp))[0], 0)
        code, out, err = self.old(BATCH_CARD_PY, ["rows", "--mode", "finalize",
                                                  "--head-blobs", bp],
                                  stdin_path=sp)
        self.assertEqual((code, err), (0, b""))
        self.assertIsInstance(json.loads(out), dict)


# The 2.14.1 guard line, run by a shell exactly as written in step 1:
#   python3 "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "<file>"
# `$0` is this interpreter, `$1` guard.py, `$2` the file. `$(...)` drops the
# trailing line breaks of git's output and nothing else, so a repo folder
# whose name ends in a space or a tab keeps it.
GUARD_LINE_2141 = '"$0" "$1" --root "$(git rev-parse --show-toplevel)" --path "$2"'


def run_in(repo, args):
    return subprocess.run(args, cwd=repo, stdin=subprocess.DEVNULL,
                          capture_output=True, timeout=120)


def fingerprint_2141(repo, name):
    """The blob 2.14.1 step 1 puts in $BLOBFILE for `name`, run in the session
    folder `repo`, or None: the PATH_RE pre-filter, the guard line through
    /bin/sh, then the three git calls, kept only when all exit 0."""
    if not finalize_inputs.PATH_RE.match(name):
        return None
    guard = run_in(repo, ["/bin/sh", "-c", GUARD_LINE_2141, sys.executable,
                          GUARD_PY, name])
    if guard.returncode != 0:
        return None
    rev = run_in(repo, ["git", "rev-parse", "HEAD:" + name])
    if rev.returncode != 0:
        return None
    for check in (["git", "diff", "--quiet", "HEAD", "--", name],
                  ["git", "diff", "--cached", "--quiet", "--", name]):
        if run_in(repo, check).returncode != 0:
            return None
    return rev.stdout.decode().strip()


def repo_at(path):
    """A fresh repo at exactly `path` (any folder name), on main, with local
    identity; returns `path` unchanged."""
    os.makedirs(path)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.name", "t")
    git(path, "config", "user.email", "t@t")
    git(path, "config", "commit.gpgsign", "false")
    return path


class TestGuardCommandParity(CliCase):
    """The containment check as 2.14.1 ran it: a COMMAND, not a function.

    2.14.1 (dd8e4ab) `phases/shared/90-finalize.md` step 1 "HEAD
    fingerprints" validated each finding's file with

        python3 "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "<file>"

    and required exit 0. argparse reads a `--path` value that looks like an
    option (most names starting with `-`) as an option, exits 2, and the file
    is left out. Which names it refuses depends on the Python version
    (observed: 3.14 accepts `-1.ts`; 3.9, 3.12 and 3.13 refuse it), so each
    side here runs under the same interpreter, `sys.executable`.

    The 2.14.1 side is `fingerprint_2141`: the literal per-file procedure,
    with the guard command run through a shell so `--root` is exactly what
    `$(git rev-parse --show-toplevel)` gives. It never calls the helper."""

    LEADING_DASH = ("-x.ts", "-d/x.ts", "--", "-", "-x", "-hx", "--root",
                    "--path", "-h", "--help", "--ro", "--pa", "--pathx",
                    "-1", "-1.5", "-.5", "-1.ts", "-1e5", "-1_0")
    CONTROLS = ("x.ts", "sub/-x.ts", "d-/x.ts")

    def commit_names(self, names):
        for name in names:
            write(self.repo, name, name + "\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "names")

    def fingerprint_2141(self, name):
        """The blob 2.14.1 step 1 puts in $BLOBFILE for `name`, or None."""
        return fingerprint_2141(self.repo, name)

    def test_parity_leading_dash_names_match_the_2141_guard_command(self):
        names = self.LEADING_DASH + self.CONTROLS
        self.commit_names(names)
        old, new = {}, {}
        for name in names:
            blob = self.fingerprint_2141(name)
            if blob is not None:
                old[name] = blob
            new.update(finalize_inputs.head_blobs(state_for([name]),
                                                  cwd=self.repo))
        # The 2.14.1 side really ran: controls kept, the gap's names refused,
        # and the rule is not "starts with -" (`-` and `-1` are accepted).
        for name in self.CONTROLS + ("-", "-1"):
            self.assertIn(name, old)
        for name in ("-x.ts", "-d/x.ts", "--", "--root", "--path", "-h",
                     "--help"):
            self.assertNotIn(name, old)
        self.assertEqual(new, old)

    def test_parity_names_in_a_repo_folder_ending_in_a_space(self):
        """The same names in a repo whose folder name ends in a space: the
        root 2.14.1 passes keeps the space, so the controls are kept."""
        self.repo = repo_at(os.path.join(self.tmp, "named", "repo "))
        names = ("x.ts", "sub/-x.ts", "-x.ts", "-")
        self.commit_names(names)
        old, new = {}, {}
        for name in names:
            blob = self.fingerprint_2141(name)
            if blob is not None:
                old[name] = blob
            new.update(finalize_inputs.head_blobs(state_for([name]),
                                                  cwd=self.repo))
        for name in ("x.ts", "sub/-x.ts", "-"):
            self.assertIn(name, old)
        self.assertNotIn("-x.ts", old)
        self.assertEqual(new, old)

    def test_parity_leading_dash_path_is_not_fingerprinted(self):
        """End to end for `-x.ts` with a fix-obsolete verdict on unchanged
        code: 2.14.1 leaves the finding open and does not write."""
        self.commit_names(["-x.ts"])
        state = fix_obsolete_state(self.blob("-x.ts"))
        row(state, ARCH_HASH)["file"] = "-x.ts"
        sp = self.new_path(state)
        # 2.14.1: the blob file step 1 writes, then the counts and the gate.
        blob = self.fingerprint_2141("-x.ts")
        old_bp = self.new_path({} if blob is None else {"-x.ts": blob})
        c_code, c_out, _ = self.old_counts(sp, old_bp)
        self.assertEqual(c_code, 0)
        counts = json.loads(c_out)
        flags = dict({"state_file_present": True,
                      "outstanding_cw": counts["outstanding_cw"],
                      "unacknowledged_medium": counts["unacknowledged_medium"],
                      "undecided_nv": counts["undecided_nv"]}, **INTERACTIVE)
        g_code, g_out, _ = self.old_gate(flags)
        self.assertEqual(g_code, 0)
        gate = json.loads(g_out)
        self.assertEqual(
            [counts["outstanding_cw"], counts["unacknowledged_medium"],
             counts["undecided_nv"]], [1, 0, 0])
        self.assertEqual(gate["action"], "outstanding-to-phase-5")
        # The helper on the same state gives the same counts and decision,
        # writes an empty fingerprint map and no report.
        bp = self.empty()
        code, out, err = self.cli(argv_for(sp, bp))
        self.assertEqual((code, err), (0, b""))
        got = json.loads(out)
        self.assertEqual(got["counts"], counts)
        self.assertEqual({"action": got["action"], "reason": got["reason"]},
                         gate)
        self.assertEqual(got["next"], "finalize-card")
        self.assertIsNone(got["report"])
        with open(bp, "r", encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), {})


class TestRepoFolderNameParity(CliCase):
    """The repo root as 2.14.1 passed it, for a repo folder whose name ends
    in whitespace. `$(git rev-parse --show-toplevel)` drops the trailing
    line breaks of git's output and nothing else, so `.../repo ` (ending in
    a space) stays `.../repo `. Each case runs the whole Finalize input
    step both ways, end to end, from the repo folder: the 2.14.1 side is
    `fingerprint_2141` (the guard line through /bin/sh) and the three
    2.14.1 commands; the helper side is the CLI. A clean `x.ts` carries a
    last-pass fix-obsolete verdict on its HEAD blob."""

    def repo_with_x(self, path, content="x1\n"):
        repo = repo_at(path)
        write(repo, "x.ts", content)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "x")
        return repo

    def state_on_x(self, repo):
        state = fix_obsolete_state(self.blob("x.ts", cwd=repo))
        row(state, ARCH_HASH)["file"] = "x.ts"
        return state

    def decide_2141(self, repo, sp):
        """(blob map, [cw, medium, nv], gate) as 2.14.1 gives them with the
        session in `repo`."""
        blob = fingerprint_2141(repo, "x.ts")
        blobs = {} if blob is None else {"x.ts": blob}
        self.repo = repo
        c_code, c_out, _ = self.old_counts(sp, self.new_path(blobs))
        self.assertEqual(c_code, 0)
        counts = json.loads(c_out)
        flags = dict({"state_file_present": True,
                      "outstanding_cw": counts["outstanding_cw"],
                      "unacknowledged_medium": counts["unacknowledged_medium"],
                      "undecided_nv": counts["undecided_nv"]}, **INTERACTIVE)
        g_code, g_out, _ = self.old_gate(flags)
        self.assertEqual(g_code, 0)
        three = [counts["outstanding_cw"], counts["unacknowledged_medium"],
                 counts["undecided_nv"]]
        return blobs, three, json.loads(g_out)

    def decide_helper(self, repo, sp):
        bp = self.empty()
        code, out, err = self.cli(argv_for(sp, bp), cwd=repo)
        self.assertEqual((code, err), (0, b""))
        got = json.loads(out)
        with open(bp, "r", encoding="utf-8") as fh:
            blobs = json.load(fh)
        c = got["counts"]
        three = [c["outstanding_cw"], c["unacknowledged_medium"],
                 c["undecided_nv"]]
        return blobs, three, {"action": got["action"],
                              "reason": got["reason"]}

    def test_parity_folder_ending_in_a_space_or_a_tab(self):
        for label, folder in (("space", "repo "), ("tab", "repo\t")):
            with self.subTest(ending=label):
                repo = self.repo_with_x(os.path.join(self.tmp, label, folder))
                sp = self.new_path(self.state_on_x(repo))
                old = self.decide_2141(repo, sp)
                # 2.14.1 fingerprints the clean file and writes.
                self.assertEqual(old[0], {"x.ts": self.blob("x.ts", cwd=repo)})
                self.assertEqual((old[1], old[2]["action"]),
                                 ([0, 0, 0], "write"))
                self.assertEqual(self.decide_helper(repo, sp), old)

    def test_parity_other_folder_name_endings(self):
        """Further endings: other whitespace (2.14.1 keeps it in the root)
        and line breaks (2.14.1 drops them, so the root names another folder
        and the file is left out). A leading space is kept by both."""
        endings = (("no-break space", "repo\u00a0", "write"),
                   ("carriage return", "repo\r", "write"),
                   ("vertical tab", "repo\x0b", "write"),
                   ("form feed", "repo\x0c", "write"),
                   ("leading space", " repo", "write"),
                   ("line break", "repo\n", "outstanding-to-phase-5"),
                   ("two line breaks", "repo\n\n", "outstanding-to-phase-5"),
                   ("space, line break", "repo \n", "outstanding-to-phase-5"))
        for label, folder, action in endings:
            with self.subTest(ending=label):
                try:
                    repo = self.repo_with_x(os.path.join(self.tmp, label,
                                                         folder))
                except OSError:
                    self.skipTest("the filesystem refuses " + repr(folder))
                sp = self.new_path(self.state_on_x(repo))
                old = self.decide_2141(repo, sp)
                self.assertEqual(old[2]["action"], action)
                self.assertEqual(self.decide_helper(repo, sp), old)

    def test_folder_ending_in_a_space_beside_its_trimmed_name_is_not_approved(self):
        """`repo ` beside a second repo `repo` holding the same `x.ts`; the
        real `x.ts` is edited after the verdict. 2.14.1 leaves the finding
        open; a root trimmed to `repo` would read the neighbour and write."""
        base = os.path.join(self.tmp, "pair")
        repo = self.repo_with_x(os.path.join(base, "repo "))
        self.repo_with_x(os.path.join(base, "repo"))
        sp = self.new_path(self.state_on_x(repo))
        write(repo, "x.ts", "x2 edited after the verdict\n")
        old = self.decide_2141(repo, sp)
        self.assertEqual((old[0], old[1], old[2]["action"]),
                         ({}, [1, 0, 0], "outstanding-to-phase-5"))
        new = self.decide_helper(repo, sp)
        self.assertNotEqual(new[2]["action"], "write")
        self.assertEqual(new, old)


class TestCliRefusals(CliCase):

    def test_refuse_bad_blob_out_beside_a_good_state(self):
        sp = self.new_path(load_six_row())
        cases = {
            "missing": os.path.join(self.files, "nope"),
            "directory": self.files,
            "empty object": self.new_path("{}"),
            "not json": self.new_path("not json"),
        }
        for label, bp in cases.items():
            with self.subTest(blob_out=label):
                before = (sha256_of(bp) if os.path.isfile(bp) else None)
                code, out, err = self.cli(argv_for(sp, bp))
                self.assertEqual(code, 2)
                self.assertEqual(out, b"")
                self.assertEqual(err, carry_state.REASON_HEAD_BLOBS.encode())
                if before is not None:
                    self.assertEqual(sha256_of(bp), before)
                else:
                    self.assertEqual(os.path.exists(bp), label == "directory")

    def test_refuse_usage_missing_bad_unknown_or_repeated(self):
        sp = self.new_path(load_six_row())
        bp = self.empty()
        cases = [("missing " + f, argv_for(sp, bp, drop=f))
                 for f in finalize_inputs.ARGV_FLAGS]
        good = argv_for(sp, bp)
        for bad in ("<true|false>", "True", "1", "", "yes", "FALSE"):
            for flag in ("--noninteractive", "--pr-mode", "--range-mode"):
                argv = list(good)
                argv[argv.index(flag) + 1] = bad
                cases.append(("%s=%r" % (flag, bad), argv))
        cases += [
            ("unknown flag", good + ["--extra", "x"]),
            ("repeated flag", good + ["--pr-mode", "false"]),
            ("valueless flag", good[:-1]),
            ("positional", good + ["x"]),
            ("empty", []),
        ]
        for label, argv in cases:
            with self.subTest(case=label):
                code, out, err = self.inproc(argv)
                self.assertEqual((code, out, err), (2, "", ""))
        code, out, err = self.cli(argv_for(sp, bp, drop="--noninteractive"))
        self.assertEqual((code, out, err), (2, b"", b""))
        with open(bp, "rb") as fh:
            self.assertEqual(fh.read(), b"")

    def test_refuse_no_state_file_is_the_no_state_result(self):
        cases = {"absent": os.path.join(self.files, "none.json"),
                 "directory": self.files}
        for label, sp in cases.items():
            for bkind in ("empty", "missing", "non-empty"):
                with self.subTest(state=label, blob_out=bkind):
                    bp = {"empty": self.empty,
                          "missing": lambda: os.path.join(self.files, "gone"),
                          "non-empty": lambda: self.new_path("{}")}[bkind]()
                    before = sha256_of(bp) if os.path.isfile(bp) else None
                    rec = Recorder(finalize_inputs._git)
                    with mock.patch.object(finalize_inputs, "_git", rec):
                        code, out, err = self.inproc(argv_for(sp, bp))
                    self.assertEqual((code, err), (0, ""))
                    self.assertEqual(json.loads(out), finalize_inputs.build_result(
                        None, {}, INTERACTIVE)[1])
                    self.assertEqual(json.loads(out)["next"], "stop-no-state")
                    self.assertEqual(rec.calls, [])
                    if before is not None:
                        self.assertEqual(sha256_of(bp), before)
                    else:
                        self.assertFalse(os.path.exists(bp))
        code, out, err = self.cli(argv_for(cases["absent"], self.empty()))
        self.assertEqual((code, err), (0, b""))
        self.assertEqual(json.loads(out)["next"], "stop-no-state")

    def test_gap_empty_state_file_path_is_no_state(self):
        # 2.14.1: `[ -f "" ]` is false, so an empty STATE_FILE reads as no
        # state file ("No prior review passes"), not a usage error.
        bp = self.empty()
        code, out, err = self.cli(argv_for("", bp))
        self.assertEqual((code, err), (0, b""))
        self.assertEqual(json.loads(out)["next"], "stop-no-state")
        with open(bp, "rb") as fh:
            self.assertEqual(fh.read(), b"")

    def test_refuse_state_not_json_or_malformed(self):
        cases = {
            "not json": ("not json", carry_state.REASON_STATE_JSON),
            "nan": ('{"passes": NaN}', carry_state.REASON_STATE_JSON),
            "not utf-8": (NOT_UTF8, carry_state.REASON_STATE_JSON),
            "no passes": ({"x": 1}, carry_state.state_reason({"x": 1})),
            "bad fix_verdicts": (dict(load_fixture(), fix_verdicts=[]),
                                 carry_state.REASON_FIX_VERDICTS),
        }
        for label, (content, line) in cases.items():
            with self.subTest(state=label):
                self.assertIsNotNone(line)
                bp = self.empty()
                code, out, err = self.cli(argv_for(self.new_path(content), bp))
                self.assertEqual((code, out), (3, b""))
                self.assertEqual(err, line.encode())
                with open(bp, "rb") as fh:
                    self.assertEqual(fh.read(), b"")


class TestCliFreshness(CliCase):

    def test_freshness_edit_after_a_write_reopens(self):
        state = fix_obsolete_state(self.blob(ARCH_FILE))
        sp = self.new_path(state)
        first = self.empty()
        code, out, _ = self.cli(argv_for(sp, first))
        self.assertEqual((code, json.loads(out)["action"]), (0, "write"))
        write(self.repo, ARCH_FILE, "edited\n")
        code, out, _ = self.cli(argv_for(sp, self.empty()))
        self.assertEqual(code, 0)
        self.assertNotEqual(json.loads(out)["action"], "write")
        self.assertEqual(json.loads(out)["next"], "finalize-card")
        # The first attempt's file is never reused.
        code, out, err = self.cli(argv_for(sp, first))
        self.assertEqual((code, out), (2, b""))
        self.assertEqual(err, carry_state.REASON_HEAD_BLOBS.encode())


class TestCliStderrParity(CliCase):
    """D-18: the counting and report lines are the 2.14.1 commands' own."""

    def counting_cases(self):
        good = load_six_row()
        return {
            "state not json": (self.new_path("not json"), self.empty()),
            "state not utf-8": (self.new_path(NOT_UTF8), self.empty()),
            "state without passes": (self.new_path({"x": 1}), self.empty()),
            "malformed fix_verdicts": (
                self.new_path(dict(load_fixture(), fix_verdicts=[])),
                self.empty()),
            "fingerprint file missing": (
                self.new_path(good), os.path.join(self.files, "absent")),
            "fingerprint file not json": (
                self.new_path(good), self.new_path("not json")),
            "both bad": (self.new_path("not json"),
                         os.path.join(self.files, "absent2")),
        }

    def test_parity_counting_stage_stderr(self):
        for label, (sp, bp) in self.counting_cases().items():
            with self.subTest(case=label):
                o_code, o_out, o_err = self.old_counts(sp, bp)
                code, out, err = self.cli(argv_for(sp, bp))
                self.assertNotEqual(o_code, 0)
                self.assertTrue(o_err)
                self.assertIn(code, (2, 3))
                self.assertEqual(out, b"")
                self.assertEqual(err, o_err)
        # The state's line wins over the fingerprint file's, as at 2.14.1.
        sp, bp = self.counting_cases()["both bad"]
        self.assertEqual(self.cli(argv_for(sp, bp))[2],
                         carry_state.REASON_STATE_JSON.encode())

    def swap_reader(self, path, second):
        """Patch `_read_text` so the state file's content becomes `second`
        (bytes) after the first read, or raises OSError when `second` is
        OSError."""
        real = finalize_inputs._read_text
        calls = []

        def reader(p):
            calls.append(p)
            if len(calls) == 2:
                if second is OSError:
                    raise OSError("unreadable")
                with open(path, "wb") as fh:
                    fh.write(second)
            return real(p)
        return reader, calls

    def test_parity_report_stage_stderr(self):
        cases = {"not json": b"not json", "not utf-8": NOT_UTF8,
                 "malformed": json.dumps({"passes": []}).encode()}
        for label, swapped in cases.items():
            with self.subTest(case=label):
                sp = self.new_path(dismissed_all_state())
                reader, calls = self.swap_reader(sp, swapped)
                with mock.patch.object(finalize_inputs, "_read_text", reader):
                    code, out, err = self.inproc(argv_for(sp, self.empty()))
                self.assertEqual(len(calls), 2)
                self.assertEqual((code, out), (5, ""))
                o_code, o_out, o_err = self.old_report(sp)
                self.assertNotEqual(o_code, 0)
                self.assertTrue(o_err)
                self.assertEqual(err.encode(), o_err)

    def test_parity_report_reads_the_state_again_unchanged(self):
        state = dismissed_all_state()
        sp = self.new_path(state)
        real = finalize_inputs._read_text
        calls = []

        def reader(p):
            calls.append(p)
            return real(p)

        with mock.patch.object(finalize_inputs, "_read_text", reader):
            code, out, err = self.inproc(argv_for(sp, self.empty()))
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(calls, [sp, sp])
        self.assertEqual(json.loads(out)["report"],
                         batch_card.decisions_report(state))

    def test_report_second_read_unreadable_is_a_silent_report_stop(self):
        sp = self.new_path(dismissed_all_state())
        reader, _ = self.swap_reader(sp, OSError)
        with mock.patch.object(finalize_inputs, "_read_text", reader):
            code, out, err = self.inproc(argv_for(sp, self.empty()))
        self.assertEqual((code, out, err), (5, "", ""))

    def test_report_none_on_an_accepted_state_writes_nothing(self):
        sp = self.new_path(dismissed_all_state())
        with mock.patch.object(finalize_inputs.batch_card, "decisions_report",
                               return_value=None):
            code, out, err = self.inproc(argv_for(sp, self.empty()))
        self.assertEqual((code, out, err), (5, "", ""))

    def test_named_difference_unreadable_state(self):
        # The one screen difference that cannot be removed: at 2.14.1 the
        # shell's own `< "$STATE_FILE"` redirect printed a line naming the
        # path; the helper exits 3 and writes nothing.
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.skipTest("root reads any file")
        sp = self.new_path(load_six_row())
        bp = self.empty()
        os.chmod(sp, 0)
        try:
            proc = subprocess.run(
                [sys.executable, MODULE_PATH] + argv_for(sp, bp),
                cwd=self.repo, capture_output=True, timeout=120)
            self.assertEqual((proc.returncode, proc.stdout, proc.stderr),
                             (3, b"", b""))
            script = ('python3 "$CARRY" finalize-counts --head-blobs "$BLOB" '
                      '< "$STATE_FILE"\n')
            env = dict(os.environ, CARRY=CARRY_STATE_PY, BLOB=bp,
                       STATE_FILE=sp)
            old = subprocess.run(["bash", "-s"], input=script.encode(),
                                 env=env, cwd=self.repo, capture_output=True,
                                 timeout=120)
            lines = old.stderr.decode().splitlines()
            self.assertNotEqual(old.returncode, 0)
            self.assertEqual(len(lines), 1)
            self.assertTrue(lines[0].endswith("Permission denied"))
            self.assertIn(sp, lines[0])
        finally:
            os.chmod(sp, 0o600)

    @staticmethod
    def locale_env(name):
        """The current environment on locale `name`, with every variable
        that would override the locale's choice of stream handling removed."""
        drop = ("LANG", "LANGUAGE", "PYTHONIOENCODING", "PYTHONUTF8",
                "PYTHONCOERCECLOCALE")
        env = {k: v for k, v in os.environ.items()
               if k not in drop and not k.startswith("LC_")}
        env.update(LC_ALL=name, LANG=name)
        return env

    def test_named_difference_non_utf8_state_under_c_locale(self):
        # At 2.14.1 the counting and report commands read the state from
        # stdin as text. On C, POSIX and C.UTF-8 Python reads stdin with
        # `surrogateescape`, so a state that is not valid UTF-8 parses and
        # is refused as malformed; on a UTF-8 locale such as en_US.UTF-8
        # stdin is strict and it is refused as not JSON. The helper reads
        # the file as strict UTF-8 and prints the not-JSON line on every
        # locale.
        not_json = b"refused: state is not valid JSON\n"
        malformed = b"refused: malformed state: passes\n"
        self.assertEqual(carry_state.REASON_STATE_JSON.encode(), not_json)
        probe = ("import locale, sys; "
                 "print(locale.setlocale(locale.LC_CTYPE, ''), "
                 "sys.stdin.errors)")
        for name in ("C", "C.UTF-8"):
            with self.subTest(locale=name):
                env = self.locale_env(name)
                # The locale must really be in force; a missing locale makes
                # `setlocale` raise and this assertion fail (never a skip).
                proc = subprocess.run([sys.executable, "-c", probe], env=env,
                                      stdin=subprocess.DEVNULL,
                                      capture_output=True, timeout=120)
                self.assertEqual((proc.returncode, proc.stdout.split()),
                                 (0, [name.encode(), b"surrogateescape"]),
                                 proc.stderr)
                sp = self.new_path(NOT_UTF8)
                bp = self.empty()
                o_code, _, o_err = self.old(
                    CARRY_STATE_PY, ["finalize-counts", "--head-blobs", bp],
                    stdin_path=sp, env=env)
                self.assertNotEqual(o_code, 0)
                self.assertEqual(o_err, malformed)
                o_code, _, o_err = self.old(BATCH_CARD_PY, ["decisions-report"],
                                            stdin_path=sp, env=env)
                self.assertNotEqual(o_code, 0)
                self.assertEqual(o_err, malformed)
                before = sha256_of(sp)
                proc = subprocess.run(
                    [sys.executable, MODULE_PATH] + argv_for(sp, bp),
                    cwd=self.repo, env=env, stdin=subprocess.DEVNULL,
                    capture_output=True, timeout=120)
                self.assertEqual((proc.returncode, proc.stdout, proc.stderr),
                                 (3, b"", not_json))
                self.assertEqual(sha256_of(sp), before)
                with open(bp, "rb") as fh:
                    self.assertEqual(fh.read(), b"")
        # On a UTF-8 locale with strict stdin 2.14.1 printed the helper's line.
        sp = self.new_path(NOT_UTF8)
        bp = self.empty()
        for o_code, _, o_err in (self.old_counts(sp, bp), self.old_report(sp)):
            self.assertNotEqual(o_code, 0)
            self.assertEqual(o_err, not_json)
        self.assertEqual(self.cli(argv_for(sp, bp))[:3], (3, b"", not_json))
        # Report stage, run as the report-stage parity test runs it.
        sp = self.new_path(dismissed_all_state())
        reader, calls = self.swap_reader(sp, NOT_UTF8)
        with mock.patch.object(finalize_inputs, "_read_text", reader):
            code, out, err = self.inproc(argv_for(sp, self.empty()))
        self.assertEqual(len(calls), 2)
        self.assertEqual((code, out, err), (5, "", not_json.decode()))

    def test_stderr_empty_on_every_other_exit(self):
        sp = self.new_path(load_six_row())
        cases = {
            "success": (None, None),
            "usage": ("--pr-mode", None),
            "gate raises": (None, ("finalize_gate", "run",
                                   RuntimeError("x"))),
            "unexpected exception": (None, ("finalize_inputs", "head_blobs",
                                            RuntimeError("x"))),
        }
        for label, (drop, patch) in cases.items():
            with self.subTest(case=label):
                argv = argv_for(sp, self.empty(), drop=drop)
                if patch is None:
                    code, out, err = self.inproc(argv)
                else:
                    target = (finalize_inputs if patch[0] == "finalize_inputs"
                              else finalize_inputs.finalize_gate)
                    with mock.patch.object(target, patch[1],
                                           side_effect=patch[2]):
                        code, out, err = self.inproc(argv)
                self.assertEqual(err, "")
                self.assertEqual(code, {"success": 0, "usage": 2}.get(label, 4))
                if code:
                    self.assertEqual(out, "")


class TestCliDisclosure(CliCase):

    def test_markers_never_echoed_on_refusals(self):
        marker = "ZZMARKERTITLE"
        path_marker = "ZZMARKERPATH"
        state = dict(load_fixture(), fix_verdicts=[])
        row(state, ARCH_HASH)["title"] = marker
        row(state, ARCH_HASH)["file"] = marker + ".ts"
        good = load_fixture()
        row(good, ARCH_HASH)["title"] = marker
        bad_blob = self.new_path("x", name=path_marker)
        runs = [argv_for(self.new_path(state), self.empty()),
                argv_for(self.new_path(good), bad_blob),
                argv_for(self.new_path(good),
                         os.path.join(self.files, path_marker + "2")),
                argv_for(self.new_path(good), bad_blob,
                         switches={"pr_mode": True}, extra=["--x", "y"])]
        for argv in runs:
            with self.subTest(argv=argv[1::2][:2]):
                code, out, err = self.cli(argv)
                self.assertNotEqual(code, 0)
                for m in (marker, path_marker):
                    self.assertNotIn(m.encode(), out + err)

    def test_no_owner_sentence_in_the_module(self):
        with open(MODULE_PATH, "r", encoding="utf-8") as fh:
            src = fh.read()
        for text in OWNER_SENTENCES:
            self.assertNotIn(text, src)
        code_lines = [ln for ln in src.splitlines()
                      if not ln.lstrip().startswith("#")]
        self.assertFalse(any("print(" in ln for ln in code_lines))
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                self.assertFalse(node.value.startswith("refused:"),
                                 node.value)

    def test_every_stderr_write_passes_a_carry_state_name(self):
        with open(MODULE_PATH, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        writes = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute)
                  and n.func.attr == "write"
                  and isinstance(n.func.value, ast.Attribute)
                  and n.func.value.attr == "stderr"]
        self.assertEqual(len(writes), 1)
        self.assertFalse(isinstance(writes[0].args[0], ast.Constant))


class TestCliMutants(CliCase):
    """Each CLI guard removed in turn lets its own case through."""

    def multi_mutant(self, *pairs):
        with open(MODULE_PATH, "r", encoding="utf-8") as fh:
            src = fh.read()
        for old, new in pairs:
            self.assertEqual(src.count(old), 1, old)
            src = src.replace(old, new, 1)
        spec = importlib.util.spec_from_loader("finalize_inputs_mutant",
                                               loader=None)
        mod = importlib.util.module_from_spec(spec)
        mod.__file__ = MODULE_PATH
        exec(compile(src, MODULE_PATH, "exec"), mod.__dict__)
        return mod

    def test_mutant_accepting_non_empty_blob_out_trips(self):
        sp = self.new_path(load_six_row())
        argv = argv_for(sp, self.new_path("{}"))
        self.assertEqual(self.inproc(argv)[0], 2)
        mod = self.multi_mutant(("os.path.getsize(path) == 0", "True"))
        self.assertEqual(self.inproc(argv, module=mod)[0], 0)

    def test_mutant_defaulting_noninteractive_to_false_trips(self):
        argv = argv_for(self.new_path(load_six_row()), self.empty(),
                        drop="--noninteractive")
        self.assertEqual(self.inproc(argv)[0], 2)
        mod = self.multi_mutant((
            "    if set(values) != set(ARGV_FLAGS):",
            '    values.setdefault("--noninteractive", "false")\n'
            "    if set(values) != set(ARGV_FLAGS):"))
        code, out, _ = self.inproc(argv, module=mod)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["action"], "outstanding-to-phase-5")

    def test_mutant_reading_an_existing_blob_out_trips_freshness(self):
        state = fix_obsolete_state(self.blob(ARCH_FILE))
        sp = self.new_path(state)
        first = self.empty()
        self.assertEqual(json.loads(self.inproc(argv_for(sp, first))[1])
                         ["action"], "write")
        write(self.repo, ARCH_FILE, "edited\n")
        self.assertEqual(self.inproc(argv_for(sp, first))[0], 2)
        mod = self.multi_mutant(
            ("os.path.getsize(path) == 0", "True"),
            ("blobs = head_blobs(state, cwd)",
             "blobs = carry_state.read_json_file(blob_out) or "
             "head_blobs(state, cwd)"))
        code, out, _ = self.inproc(argv_for(sp, first), module=mod)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["action"], "write")

    def test_mutant_stderr_on_usage_or_gate_exit_trips(self):
        sp = self.new_path(load_six_row())
        usage = self.multi_mutant((
            '        return EXIT_USAGE, ""',
            '        sys.stderr.write("usage\\n")\n'
            '        return EXIT_USAGE, ""'))
        self.assertEqual(self.inproc(argv_for(sp, self.empty(),
                                              drop="--pr-mode"),
                                     module=usage)[2], "usage\n")
        gate = self.multi_mutant((
            "(any gate failure is the gate stop)\n"
            "        return EXIT_GATE, None",
            "(any gate failure is the gate stop)\n"
            '        sys.stderr.write("gate\\n")\n'
            "        return EXIT_GATE, None"))
        with mock.patch.object(gate.finalize_gate, "run",
                               side_effect=RuntimeError("x")):
            self.assertEqual(self.inproc(argv_for(sp, self.empty()),
                                         module=gate)[2], "gate\n")
        catch_all = self.multi_mutant((
            '        return EXIT_GATE, ""',
            '        sys.stderr.write("boom\\n")\n'
            '        return EXIT_GATE, ""'))
        with mock.patch.object(catch_all, "head_blobs",
                               side_effect=RuntimeError("x")):
            self.assertEqual(self.inproc(argv_for(sp, self.empty()),
                                         module=catch_all)[2], "boom\n")

    def test_mutant_counting_line_changed_or_dropped_trips(self):
        sp = self.new_path("not json")
        bp = self.empty()
        o_err = self.old_counts(sp, bp)[2].decode()
        self.assertEqual(self.inproc(argv_for(sp, bp))[2], o_err)
        changed = self.multi_mutant((
            "    except ValueError:\n        return None, "
            "carry_state.REASON_STATE_JSON",
            "    except ValueError:\n        return None, "
            "carry_state.REASON_STATE"))
        self.assertNotEqual(self.inproc(argv_for(sp, bp), module=changed)[2],
                            o_err)
        dropped = self.multi_mutant(("return _refuse(EXIT_STATE, line)",
                                     'return EXIT_STATE, ""'))
        self.assertEqual(self.inproc(argv_for(sp, bp), module=dropped)[2], "")

    def test_mutant_blob_out_checked_before_state_trips(self):
        sp = self.new_path("not json")
        bp = os.path.join(self.files, "absent")
        self.assertEqual(self.inproc(argv_for(sp, bp))[2],
                         carry_state.REASON_STATE_JSON)
        mod = self.multi_mutant((
            "    state, line = _load_state(state_file)\n",
            "    if not _blob_out_ok(blob_out):\n"
            "        return _refuse(EXIT_USAGE, carry_state.REASON_HEAD_BLOBS)\n"
            "    state, line = _load_state(state_file)\n"))
        self.assertEqual(self.inproc(argv_for(sp, bp), module=mod)[2],
                         carry_state.REASON_HEAD_BLOBS)

    def report_swap_run(self, module, swapped):
        sp = self.new_path(dismissed_all_state())
        real = module._read_text
        calls = []

        def reader(p):
            calls.append(p)
            if len(calls) == 2:
                if swapped is OSError:
                    raise OSError("x")
                with open(sp, "wb") as fh:
                    fh.write(swapped)
            return real(p)

        with mock.patch.object(module, "_read_text", reader):
            result = self.inproc(argv_for(sp, self.empty()), module=module)
        return result, sp

    def test_mutant_report_line_changed_or_dropped_trips(self):
        (code, _, err), sp = self.report_swap_run(finalize_inputs, b"not json")
        self.assertEqual(err.encode(), self.old_report(sp)[2])
        changed = self.multi_mutant((
            'return _refuse(code, report_line[0] if report_line else "")',
            "return _refuse(code, carry_state.REASON_STATE)"))
        (_, _, err), sp = self.report_swap_run(changed, b"not json")
        self.assertNotEqual(err.encode(), self.old_report(sp)[2])
        dropped = self.multi_mutant((
            'return _refuse(code, report_line[0] if report_line else "")',
            'return code, ""'))
        (_, _, err), _ = self.report_swap_run(dropped, b"not json")
        self.assertEqual(err, "")

    def test_mutant_report_from_the_first_read_trips(self):
        (code, _, _), _ = self.report_swap_run(finalize_inputs, b"not json")
        self.assertEqual(code, 5)
        mod = self.multi_mutant(("report_source=reread", "report_source=None"))
        (code, out, _), _ = self.report_swap_run(mod, b"not json")
        self.assertEqual(code, 0)
        self.assertIsNotNone(json.loads(out)["report"])

    def test_mutant_decode_error_to_catch_all_trips(self):
        sp = self.new_path(NOT_UTF8)
        bp = self.empty()
        self.assertEqual(self.inproc(argv_for(sp, bp))[:1] + (
            self.inproc(argv_for(sp, bp))[2],),
            (3, carry_state.REASON_STATE_JSON))
        mod = self.multi_mutant((
            "    except UnicodeDecodeError:\n"
            "        return None, carry_state.REASON_STATE_JSON\n", ""))
        code, _, err = self.inproc(argv_for(sp, bp), module=mod)
        self.assertEqual((code, err), (4, ""))
        (code, _, err), _ = self.report_swap_run(mod, NOT_UTF8)
        self.assertEqual((code, err), (4, ""))

    def test_mutant_oserror_to_catch_all_trips(self):
        (code, _, _), _ = self.report_swap_run(finalize_inputs, OSError)
        self.assertEqual(code, 5)
        mod = self.multi_mutant((
            "    except OSError:\n        return None, \"\"\n", ""))
        (code, _, err), _ = self.report_swap_run(mod, OSError)
        self.assertEqual((code, err), (4, ""))


def snapshot(root):
    """{relative path: sha256} for every file under `root`, .git excluded."""
    return {rel: sha256_of(os.path.join(root, rel))
            for rel in tree_listing(root)}


class TestCliWritesOnlyTheFingerprintFile(CliCase):
    """The helper's only write is the fingerprint file it was handed: no
    side file (no `.err`), no state change, nothing in the repo; and a
    missing fingerprint file is refused, never created."""

    def routes(self):
        fix = fix_obsolete_state(self.blob(ARCH_FILE))
        return {
            "write": (fix, True),
            "card": (load_six_row(), True),
            "state refused": ("not json", False),
            "no state file": (None, False),
        }

    def run_route(self, state, module=None):
        """Run one route in-process over a fresh side folder; return
        (before, after, blob_out relative path, exit code)."""
        sp = (os.path.join(self.files, "absent.json") if state is None
              else self.new_path(state))
        bp = self.empty()
        before = snapshot(self.tmp)
        code, _, _ = self.inproc(argv_for(sp, bp), module=module)
        return before, snapshot(self.tmp), os.path.relpath(bp, self.tmp), code

    def changed(self, before, after):
        keys = set(before) | set(after)
        return {k for k in keys if before.get(k) != after.get(k)}

    def test_only_the_fingerprint_file_changes_on_every_route(self):
        for label, (state, writes_blob) in self.routes().items():
            with self.subTest(route=label):
                before, after, bp, _ = self.run_route(state)
                self.assertEqual(self.changed(before, after),
                                 {bp} if writes_blob else set())

    def test_missing_fingerprint_file_is_refused_and_not_created(self):
        sp = self.new_path(load_six_row())
        bp = os.path.join(self.files, "never-made")
        code, out, err = self.cli(argv_for(sp, bp))
        self.assertEqual((code, out), (2, b""))
        self.assertEqual(err, carry_state.REASON_HEAD_BLOBS.encode())
        self.assertFalse(os.path.exists(bp))

    def test_mutant_side_file_or_state_write_trips(self):
        good = self.run_route(fix_obsolete_state(self.blob(ARCH_FILE)))
        self.assertEqual(self.changed(good[0], good[1]), {good[2]})
        side = TestCliMutants.multi_mutant(self, (
            "            fh.write(json.dumps(blobs, sort_keys=True))\n",
            "            fh.write(json.dumps(blobs, sort_keys=True))\n"
            "        open(blob_out + \".err\", \"w\").close()\n"))
        before, after, bp, code = self.run_route(
            fix_obsolete_state(self.blob(ARCH_FILE)), module=side)
        self.assertEqual(code, 0)
        self.assertEqual(self.changed(before, after), {bp, bp + ".err"})
        state_write = TestCliMutants.multi_mutant(self, (
            "    blobs = head_blobs(state, cwd)\n",
            "    blobs = head_blobs(state, cwd)\n"
            "    with open(state_file, \"w\", encoding=\"utf-8\") as sf:\n"
            "        sf.write(json.dumps(state, indent=1))\n"))
        before, after, bp, code = self.run_route(
            fix_obsolete_state(self.blob(ARCH_FILE)), module=state_write)
        self.assertEqual(code, 0)
        self.assertEqual(len(self.changed(before, after)), 2)

    def test_mutant_creating_a_missing_fingerprint_file_trips(self):
        sp = self.new_path(load_six_row())
        bp = os.path.join(self.files, "never-made")
        self.assertEqual(self.inproc(argv_for(sp, bp))[0], 2)
        mod = TestCliMutants.multi_mutant(self, (
            "        return os.path.isfile(path) and os.path.getsize(path) == 0",
            "        return not os.path.exists(path) or "
            "(os.path.isfile(path) and os.path.getsize(path) == 0)"))
        code, out, err = self.inproc(argv_for(sp, bp), module=mod)
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(os.path.isfile(bp))


class TestLedgerReplacements(CliCase):
    """Helper-level locks for rules the Finalize instruction text carried:
    an unsubstituted fingerprint path, a literal `HEAD` head_sha, the card
    route's re-run after recorded answers, and an unknown gate action."""

    multi_mutant = TestCliMutants.multi_mutant

    # -- the fingerprint path left unsubstituted in a fresh shell ------------ #
    def test_unsubstituted_blob_out_is_refused(self):
        # A fresh shell expands an unset "$BLOBFILE" to "".
        code, out, err = self.cli(argv_for(self.new_path(load_six_row()), ""))
        self.assertEqual((code, out), (2, b""))
        self.assertEqual(err, carry_state.REASON_HEAD_BLOBS.encode())

    def test_mutant_unsubstituted_blob_out_reaches_catch_all_trips(self):
        argv = argv_for(self.new_path(load_six_row()), "")
        self.assertEqual(self.inproc(argv), (2, "", carry_state.REASON_HEAD_BLOBS))
        mod = self.multi_mutant(
            ("os.path.isfile(path) and os.path.getsize(path) == 0", "True"),
            ("    except OSError:\n"
             "        return _refuse(EXIT_USAGE, carry_state.REASON_HEAD_BLOBS)",
             "    except ValueError:\n"
             "        return _refuse(EXIT_USAGE, carry_state.REASON_HEAD_BLOBS)"))
        self.assertEqual(self.inproc(argv, module=mod), (4, "", ""))

    # -- FINALIZE-HEAD-SHA-WEDGE ---------------------------------------------- #
    def head_sha_head_state(self):
        state = load_six_row()
        state["passes"][-1]["head_sha"] = "HEAD"
        return state

    def test_head_sha_literal_head_is_not_read(self):
        code, out, err = self.cli(argv_for(self.new_path(
            self.head_sha_head_state()), self.empty()))
        self.assertEqual((code, err), (0, b""))
        got = json.loads(out)
        self.assertEqual((got["counts"]["outstanding_cw"],
                          got["counts"]["unacknowledged_medium"],
                          got["counts"]["undecided_nv"]), (5, 1, 0))
        self.assertEqual(got["next"], "finalize-card")

    def test_mutant_head_sha_check_wedges_finalize_trips(self):
        argv = argv_for(self.new_path(self.head_sha_head_state()), self.empty())
        self.assertEqual(self.inproc(argv)[0], 0)
        mod = self.multi_mutant((
            "    if not _blob_out_ok(blob_out):\n",
            "    if state[\"passes\"][-1].get(\"head_sha\") == \"HEAD\":\n"
            "        return _refuse(EXIT_STATE, carry_state.REASON_STATE)\n"
            "    if not _blob_out_ok(blob_out):\n"))
        code, out, err = self.inproc(argv, module=mod)
        self.assertEqual((code, out), (3, ""))

    # -- the card route: answers recorded, then the block runs again --------- #
    def card_route(self, module=None):
        """Run the helper, record a dismissal of every open obligation through
        the 2.14.1 record-decisions command, run the helper again on a NEW
        fingerprint file. Returns (first result, second exit, second result,
        the recorded state)."""
        sp = self.new_path(load_six_row())
        code, out, err = self.inproc(argv_for(sp, self.empty()), module=module)
        self.assertEqual((code, err), (0, ""))
        first = json.loads(out)
        self.assertEqual(first["next"], "finalize-card")
        counts = first["counts"]
        hashes = (counts["outstanding_cw_hashes"]
                  + counts["unacknowledged_medium_hashes"]
                  + counts["undecided_nv_hashes"])
        self.assertTrue(hashes)
        with open(sp, "r", encoding="utf-8") as fh:
            at_pass = json.load(fh)["passes"][-1]["pass_number"]
        dp = self.new_path({"at_pass": at_pass, "decisions": [
            {"stable_hash": h, "decision": "dismiss", "reason": "walk"}
            for h in hashes]})
        r_code, r_out, r_err = self.old(CARRY_STATE_PY, [
            "record-decisions", "--decisions-file", dp], stdin_path=sp)
        self.assertEqual((r_code, r_err), (0, b""))
        with open(sp, "wb") as fh:
            fh.write(r_out)
        recorded = json.loads(r_out)
        code, out, err = self.inproc(argv_for(sp, self.empty()), module=module)
        return first, code, (json.loads(out) if out else None), recorded

    def test_card_route_record_then_rerun_writes(self):
        _, code, second, recorded = self.card_route()
        self.assertEqual(code, 0)
        self.assertEqual(second["action"], "write")
        self.assertEqual(second["next"], "write-review-md")
        self.assertEqual((second["counts"]["outstanding_cw"],
                          second["counts"]["unacknowledged_medium"],
                          second["counts"]["undecided_nv"]), (0, 0, 0))
        self.assertEqual(second["report"], batch_card.decisions_report(recorded))
        self.assertTrue(second["report"]["entries"])

    def test_mutant_card_route_counts_before_answers_trips(self):
        # The gate deciding on counts that predate the owner's answers (the
        # STALE-GATEFILE-RERUN failure) keeps Finalize blocked.
        mod = self.mutant(
            "        counts = carry_state.finalize_counts(state, blobs)\n",
            "        counts = carry_state.finalize_counts("
            "dict(state, decisions={}), blobs)\n")
        _, code, second, _ = self.card_route(module=mod)
        self.assertEqual(code, 0)
        self.assertNotEqual(second["action"], "write")
        self.assertEqual(second["next"], "finalize-card")

    # -- any other gate action is the gate stop ------------------------------ #
    def test_mutant_unknown_gate_action_passed_through_trips(self):
        bad = {"action": "approve", "reason": "x"}
        with mock.patch.object(finalize_inputs.finalize_gate, "run",
                               return_value=bad):
            self.assertEqual(finalize_inputs.build_result(
                load_six_row(), {}, INTERACTIVE),
                (finalize_inputs.EXIT_GATE, None))
        mod = self.mutant("    if action not in finalize_gate.ACTIONS:\n"
                          "        return EXIT_GATE, None\n", "")
        with mock.patch.object(mod.finalize_gate, "run", return_value=bad):
            code, result = mod.build_result(load_six_row(), {}, INTERACTIVE)
        self.assertEqual(code, 0)
        self.assertEqual(result["action"], "approve")


class TestImportSet(unittest.TestCase):
    """Import set and subprocess discipline stated in the docstring."""

    def setUp(self):
        with open(MODULE_PATH, "r", encoding="utf-8") as fh:
            self.src = fh.read()
        self.tree = ast.parse(self.src)

    def test_stdlib_import_set_is_exact(self):
        names = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module)
        siblings = {"batch_card", "carry_state", "finalize_gate", "fixcommit",
                    "guard"}
        self.assertEqual(names - siblings,
                         {"io", "json", "os", "subprocess", "sys"})
        self.assertEqual(names & siblings, siblings)

    def test_only_path_re_is_taken_from_fixcommit(self):
        froms = [n for n in ast.walk(self.tree)
                 if isinstance(n, ast.ImportFrom) and n.module == "fixcommit"]
        self.assertEqual([[a.name for a in n.names] for n in froms],
                         [["PATH_RE"]])
        self.assertNotIn("validate_paths(", self.src)

    def test_every_subprocess_run_has_timeout_and_no_shell(self):
        calls = [n for n in ast.walk(self.tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "run"
                 and getattr(n.func.value, "id", None) == "subprocess"]
        self.assertTrue(calls)
        for call in calls:
            kws = {k.arg for k in call.keywords}
            self.assertIn("timeout", kws)
            self.assertNotIn("shell", kws)

    def test_git_timeout_constant(self):
        self.assertEqual(finalize_inputs.GIT_TIMEOUT, 60)

    def test_git_runner_mirrors_the_named_calls(self):
        # The 2.14.1 instructions name plain git calls; no extra global flags.
        self.assertNotIn("--no-optional-locks", self.src)


# --------------------------------------------------------------------------- #
# D-01: the instructions branch on the result's `next`, one bullet per value.
# --------------------------------------------------------------------------- #
FINALIZE_MD_PATH = os.path.join(SCRIPTS_DIR, "..", "phases", "shared",
                                "90-finalize.md")
_BRANCH_BULLET_RE = re.compile(r"^- `([a-z][a-z0-9-]*)`", re.M)


def branch_next_values(text):
    """The `next` values heading the top-level branch bullets of the Finalize
    mode section (up to the finalize card), in order."""
    start = text.index("## Finalize mode")
    end = text.index("### The finalize card", start)
    return _BRANCH_BULLET_RE.findall(text[start:end])


def next_vocabulary_problems(text):
    values = branch_next_values(text)
    problems = []
    if len(values) != len(set(values)):
        problems.append("a next value heads two bullets: %r" % values)
    missing = set(finalize_inputs.NEXT_ACTIONS) - set(values)
    unknown = set(values) - set(finalize_inputs.NEXT_ACTIONS)
    if missing:
        problems.append("no bullet for: %r" % sorted(missing))
    if unknown:
        problems.append("bullet for an unknown value: %r" % sorted(unknown))
    return problems


class TestNextVocabularyProse(unittest.TestCase):
    """The instruction file's branch bullets are exactly NEXT_ACTIONS."""

    def setUp(self):
        with open(FINALIZE_MD_PATH, "r", encoding="utf-8") as fh:
            self.text = fh.read()

    def test_branch_bullets_equal_next_actions(self):
        self.assertEqual(next_vocabulary_problems(self.text), [])
        self.assertEqual(len(branch_next_values(self.text)),
                         len(finalize_inputs.NEXT_ACTIONS))

    def test_mutant_bullet_removed_trips(self):
        values = branch_next_values(self.text)
        self.assertIn("stop-no-state", values)
        lines = [ln for ln in self.text.split("\n")
                 if not ln.startswith("- `stop-no-state`")]
        mutant = "\n".join(lines)
        self.assertNotEqual(mutant, self.text)
        self.assertNotEqual(next_vocabulary_problems(mutant), [])

    def test_mutant_unknown_value_trips(self):
        anchor = "- `stop-refused`"
        self.assertIn(anchor, self.text)
        mutant = self.text.replace(
            anchor, "- `stop-unknown` — stop.\n" + anchor, 1)
        self.assertNotEqual(next_vocabulary_problems(mutant), [])


if __name__ == "__main__":
    unittest.main()
