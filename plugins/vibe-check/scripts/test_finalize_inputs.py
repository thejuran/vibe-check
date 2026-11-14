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
import importlib.util
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
            ["rev-parse", "HEAD:src/a.ts"],
            ["diff", "--quiet", "HEAD", "--", "src/a.ts"],
            ["diff", "--cached", "--quiet", "--", "src/a.ts"],
        ])


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

    def test_gap_leading_dash_path_is_fingerprinted(self):
        write(self.repo, "-x.ts", "dash\n")
        git(self.repo, "add", "--", "-x.ts")
        git(self.repo, "commit", "-q", "-m", "dash")
        out, _ = self.run_helper(state_for(["-x.ts"]))
        self.assertEqual(out, {"-x.ts": self.blob("-x.ts")})

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
        mod = self.mutant('_git(["diff", "--quiet", "HEAD", "--", f], root)',
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
        mod = self.mutant('_git(["diff", "--cached", "--quiet", "--", f], root)',
                          "(0, '')")
        out, _ = self.run_helper(s, module=mod)
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})

    def test_mutant_checks_in_session_folder_fingerprint_edit_from_subfolder(self):
        sub = os.path.join(self.repo, "sub")
        write(self.repo, "sub/c.ts", "c2\n")
        s = state_for(["sub/c.ts"])
        out, _ = self.run_helper(s, cwd=sub)
        self.assertEqual(out, {})
        mod = self.mutant(
            '_git(["diff", "--quiet", "HEAD", "--", f], root)',
            '_git(["diff", "--quiet", "HEAD", "--", f], cwd)')
        out, _ = self.run_helper(s, cwd=sub, module=mod)
        self.assertEqual(out, {"sub/c.ts": self.blob("sub/c.ts")})

    def test_mutant_index_check_in_session_folder_fingerprints_staged_file(self):
        sub = os.path.join(self.repo, "sub")
        write(self.repo, "sub/c.ts", "staged\n")
        git(self.repo, "add", "--", "sub/c.ts")
        write(self.repo, "sub/c.ts", "c1\n")
        s = state_for(["sub/c.ts"])
        out, _ = self.run_helper(s, cwd=sub)
        self.assertEqual(out, {})
        mod = self.mutant(
            '_git(["diff", "--cached", "--quiet", "--", f], root)',
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
        mod = self.mutant('if action == "write":', "if True:")
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
        self.assertEqual(names - siblings, {"json", "os", "subprocess", "sys"})
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


if __name__ == "__main__":
    unittest.main()
