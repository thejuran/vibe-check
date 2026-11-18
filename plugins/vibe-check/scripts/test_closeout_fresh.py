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

WHOLE DIFFERENTIAL. `TestOnlyIntendedDifferences` runs every fixture state
these tests build (the 999.40 repo, the Finalize result fixtures, the shape 2
and shape 3 fixtures and every main parity-grid scenario) through both
helpers, in each disk variant that applies. Every run is byte-identical
(exit code, stdout and fingerprint file) unless it is named: INTENDED lists
the freshness refusals, REPAIRED the owner-approved covering-order repair.
A named entry that no longer differs fails too.

MUTANT STRATEGY. Guards in `closeout_fresh.py` are checked by loading a
source-substituted copy of the module (house style: assert the replaced text
is present, replace once, exec under a non-main name) and showing the guarded
fixture goes through; each mutant must make a named test here fail.
"""

import concurrent.futures
import importlib.util
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

import carry_state  # noqa: E402  (decision_state of the re-review)
import closeout_fresh  # noqa: E402  (module under test)
import finalize_inputs  # noqa: E402  (the candidate helper, in-process)
import gitfixture  # noqa: E402  (shared temp-repo helper)
import score  # noqa: E402  (oracle for the mirrored window, D-05)
import test_decision_continuity as tdc  # noqa: E402  (pass1, base_file, F)
import test_worktree_snap as tws  # noqa: E402  (_Chain: a reviewed tree in the store)
import test_diff_ranges as tdr  # noqa: E402  (prose range placeholders)
import test_finalize_inputs as tfi  # noqa: E402  (the 66-02 fixture builders)
import test_finalize_parity_grid as tpg  # noqa: E402  (the grid Builder)
import worktree_snap  # noqa: E402  (STORE_REL)
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


# --------------------------------------------------------------------------- #
# The freshness decision itself: `closeout_fresh.stale_decisions`, called
# in-process on a parsed state in a real temp repo (no CLI).
# --------------------------------------------------------------------------- #
KINDS = ("defer", "dismiss")
SHIFT = 20  # lines inserted above the decided line for the pure-shift cases


class Recorder:
    """Wraps the real `closeout_fresh._git` (worktree_snap signature),
    recording every argv; `fail(args)` True makes that call fail the way the
    real runner does (it raises `Unverifiable`)."""

    def __init__(self, real, fail=None):
        self.real = real
        self.fail = fail
        self.calls = []

    def __call__(self, root, args, env=None):
        self.calls.append(list(args))
        if self.fail is not None and self.fail(args):
            raise closeout_fresh.Unverifiable("git %s failed (test)" % args[0])
        return self.real(root, args, env=env)

    def argv_text(self):
        return [a for call in self.calls for a in call]


class DecidedCase(FreshCase):
    """A decided finding at src/a.py:10 on a committed, reviewed tree; each
    `decided()` call builds a new repo, so subtests never share one."""

    def decided(self, kind="defer", lines=None):
        """Commit `lines` (default `tdc.base_file()`) as src/a.py in a new
        repo, review it with one finding at line 10 that the owner decides
        (`kind`), and bind the last pass to HEAD and `HEAD^{tree}` ->
        (state dict, hash)."""
        self.new_repo(lines)
        state, h = tdc.pass1(self.lines, conf=95, kind=kind)
        return self.bind(state), h

    def new_repo(self, lines=None):
        self._n += 1
        case_dir = os.path.join(self.tmp, "case%d" % self._n)
        os.makedirs(case_dir)
        self.repo = gitfixture.make_repo(case_dir)
        self.lines = list(lines or tdc.base_file())
        self.put(self.lines)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "x")

    def bind(self, state):
        last = state["passes"][-1]
        last["head_sha"] = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        last["reviewed_tree"] = git(self.repo, "rev-parse",
                                    "HEAD^{tree}").stdout.strip()
        return state

    def put(self, lines, rel=tdc.F):
        write(self.repo, rel, "\n".join(lines) + "\n")

    def edit(self, n, text=None):
        """Rewrite line `n` of src/a.py on disk (no commit)."""
        edited = list(self.lines)
        edited[n - 1] = ("line_%02d = danger()" % n) if text is None else text
        self.put(edited)

    def stale(self, state):
        blobs = finalize_inputs.head_blobs(state, cwd=self.repo)
        return closeout_fresh.stale_decisions(state, blobs, cwd=self.repo)

    def recorded(self, state, fail=None):
        """`stale(state)` with every closeout_fresh git call recorded ->
        (result, Recorder)."""
        rec = Recorder(closeout_fresh._git, fail)
        with mock.patch.object(closeout_fresh, "_git", rec):
            out = self.stale(state)
        return out, rec

    def one(self, h, kind, cause):
        return [{"hash": h, "kind": KIND_WORD[kind], "cause": cause}]


class TestWindow(DecidedCase):
    """D-04/D-05/D-07: judged against the reviewed tree in its own line
    numbering, with the review's +/- 5 window."""

    def test_window_exact_line_is_stale_cause_line(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state, h = self.decided(kind)
                self.edit(10)
                self.assertEqual(self.stale(state), self.one(h, kind, "line"))

    def test_window_nearby_5_and_15_cause_nearby(self):
        for kind in KINDS:
            for n in (5, 15):
                with self.subTest(kind=kind, edit=n):
                    state, h = self.decided(kind)
                    self.edit(n)
                    self.assertEqual(self.stale(state),
                                     self.one(h, kind, "nearby"))

    def test_window_outside_4_and_16_keep(self):
        for kind in KINDS:
            for n in (4, 16):
                with self.subTest(kind=kind, edit=n):
                    state, _ = self.decided(kind)
                    self.edit(n)
                    self.assertEqual(self.stale(state), [])

    def test_window_unchanged_keeps(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state, _ = self.decided(kind)
                self.assertEqual(self.stale(state), [])

    def test_window_pure_shift_of_20_lines_keeps(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state, _ = self.decided(kind)
                self.put(["shift_%02d = 0" % i for i in range(SHIFT)]
                         + self.lines)
                self.assertEqual(self.stale(state), [])

    def test_window_shift_plus_edit_is_line(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state, h = self.decided(kind)
                edited = list(self.lines)
                edited[9] = "line_10 = danger()"
                self.put(["shift_%02d = 0" % i for i in range(SHIFT)] + edited)
                self.assertEqual(self.stale(state), self.one(h, kind, "line"))

    def test_window_whitespace_only_is_stale(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state, h = self.decided(kind)
                self.edit(10, "line_10 =  10")
                self.assertEqual(self.stale(state), self.one(h, kind, "line"))

    def test_window_comment_only_is_stale(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state, h = self.decided(kind)
                self.edit(10, "line_10 = 10  # checked")
                self.assertEqual(self.stale(state), self.one(h, kind, "line"))


class TestDeleteRename(DecidedCase):
    """D-06: a decided file deleted or renamed since the review is stale."""

    def test_git_rm_is_deleted(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state, h = self.decided(kind)
                git(self.repo, "rm", "-q", tdc.F)
                self.assertEqual(self.stale(state),
                                 self.one(h, kind, "deleted"))

    def test_git_mv_is_deleted(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state, h = self.decided(kind)
                git(self.repo, "mv", tdc.F, "src/b.py")
                self.assertEqual(self.stale(state),
                                 self.one(h, kind, "deleted"))


class TestUntrackedCause(DecidedCase):
    """D-09: no reviewed copy of the decided file -> stale, cause untracked."""

    def test_decided_file_absent_from_reviewed_tree_is_untracked(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state, h = self.decided(kind)
                state = json.loads(json.dumps(state).replace(
                    tdc.F, "notes/x.py"))
                self.put(self.lines, rel="notes/x.py")  # untracked, unedited
                self.assertEqual(self.stale(state),
                                 self.one(h, kind, "untracked"))


class TestUnverifiable(DecidedCase):
    """Fail closed: when the comparison cannot be made, every decided record
    is stale with cause unverifiable (the code is NOT edited in these)."""

    def test_unverifiable_missing_reviewed_tree(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state, h = self.decided(kind)
                del state["passes"][-1]["reviewed_tree"]
                self.assertEqual(self.stale(state),
                                 self.one(h, kind, "unverifiable"))

    def test_unverifiable_malformed_reviewed_tree(self):
        for bad in ("zz", "", None, 7, "0" * 40):
            with self.subTest(reviewed_tree=bad):
                state, h = self.decided("defer")
                state["passes"][-1]["reviewed_tree"] = bad
                self.assertEqual(self.stale(state),
                                 self.one(h, "defer", "unverifiable"))

    def test_unverifiable_git_failure(self):
        for verb in ("rev-parse", "cat-file", "diff", "ls-tree"):
            with self.subTest(failing=verb):
                state, h = self.decided("dismiss")
                out, _ = self.recorded(state, fail=lambda a, v=verb: a[0] == v)
                self.assertEqual(out, self.one(h, "dismiss", "unverifiable"))

    def test_unverifiable_non_int_line(self):
        for bad in ("10", None, 0, -3, True, 10.0):
            with self.subTest(line=bad):
                state, h = self.decided("defer")
                state["passes"][-1]["findings"][0]["line"] = bad
                self.assertEqual(self.stale(state),
                                 self.one(h, "defer", "unverifiable"))

    def test_unverifiable_path_git_would_quote_or_not_a_repo_path(self):
        # Names git still C-quotes in a diff header with core.quotePath=false
        # (`"`, `\\`, control characters) cannot be keyed in the parsed
        # diff, and a name that is not a repo-relative path (absolute, a
        # `..` segment, a decode replacement character, empty, not a
        # string) names nothing the diff can prove unchanged: fail closed.
        for bad in ('src/a"b.py', "src/a\\b.py", "src/a\nb.py",
                    "src/a\tb.py", "src/a\x7fb.py", "src/a\x01b.py",
                    "/etc/a.py", "../a.py", "src/../../a.py",
                    "src/\ufffd.py", "", 5, None):
            with self.subTest(file=bad):
                state, h = self.decided("defer")
                state["passes"][-1]["findings"][0]["file"] = bad
                self.assertEqual(self.stale(state),
                                 self.one(h, "defer", "unverifiable"))

    def test_unverifiable_quoted_name_present_and_unchanged(self):
        # The file really exists in the reviewed tree and on disk, unchanged:
        # still unverifiable, because an edit to it would come out of the
        # diff under a quoted header that no record can match.
        for name in ('src/a"b.py', "src/a\\b.py", "src/a\tb.py",
                     "src/a\nb.py"):
            with self.subTest(file=name):
                state, h = self.decided_at(name, "defer")
                self.assertEqual(self.stale(state),
                                 self.one(h, "defer", "unverifiable"))


# Names common in real projects (SvelteKit routes, Next.js app router,
# spaces, non-ASCII) that git prints raw in a diff header once
# core.quotePath=false. A decision on one must be checked like any other.
SPECIAL_NAMES = ("src/routes/+page.svelte", "app/blog/[slug]/page.tsx",
                 "app/(group)/x.ts", "src/@scope/a.py", "my file.py",
                 "src/caf\u00e9.py", "src/\u6587\u4ef6.py")


def _decided_at(case, name, kind="defer"):
    """`DecidedCase.decided` with the decided file at `name` instead of
    src/a.py -> (state dict, hash)."""
    case._n += 1
    case_dir = os.path.join(case.tmp, "case%d" % case._n)
    os.makedirs(case_dir)
    case.repo = gitfixture.make_repo(case_dir)
    case.lines = list(tdc.base_file())
    case.decided_file = name
    write(case.repo, name, "\n".join(case.lines) + "\n")
    git(case.repo, "add", "-A")
    git(case.repo, "commit", "-qm", "x")
    with mock.patch.object(tdc, "F", name):
        state, h = tdc.pass1(case.lines, conf=95, kind=kind)
    case.assertEqual(state["passes"][-1]["findings"][0]["file"], name)
    return case.bind(state), h


DecidedCase.decided_at = _decided_at


class TestSpecialNames(DecidedCase):
    """CR-01 (D-16): a decision on a file whose name has `+`, `[`, `(`, `@`,
    a space or non-ASCII characters is checked against the code, so an
    unchanged file keeps it and an edit refuses with the real cause. A
    name-based refusal could never clear: a fresh review keeps the name."""

    def edit_at(self, n):
        edited = list(self.lines)
        edited[n - 1] = "line_%02d = danger()" % n
        write(self.repo, self.decided_file, "\n".join(edited) + "\n")

    def test_special_names_unchanged_keep(self):
        for kind in KINDS:
            for name in SPECIAL_NAMES:
                with self.subTest(kind=kind, file=name):
                    state, _ = self.decided_at(name, kind)
                    self.assertEqual(self.stale(state), [])

    def test_special_names_line_edit_is_line(self):
        for kind in KINDS:
            for name in SPECIAL_NAMES:
                with self.subTest(kind=kind, file=name):
                    state, h = self.decided_at(name, kind)
                    self.edit_at(10)
                    self.assertEqual(self.stale(state),
                                     self.one(h, kind, "line"))

    def test_special_names_nearby_edit_is_nearby(self):
        for name in SPECIAL_NAMES:
            with self.subTest(file=name):
                state, h = self.decided_at(name, "dismiss")
                self.edit_at(14)
                self.assertEqual(self.stale(state),
                                 self.one(h, "dismiss", "nearby"))

    def test_space_name_header_tab_is_stripped(self):
        # git ends a `+++` header with a tab when the name has a space; the
        # range must still be keyed under the bare name.
        state, _ = self.decided_at("my file.py", "defer")
        self.edit_at(10)
        top = closeout_fresh._toplevel(self.repo)
        ranges = closeout_fresh.changed_ranges(
            top, state["passes"][-1]["reviewed_tree"])
        self.assertEqual(ranges, {"my file.py": [[10, 10]]})

    def test_non_ascii_name_comes_out_raw(self):
        state, _ = self.decided_at("src/caf\u00e9.py", "defer")
        self.edit_at(10)
        top = closeout_fresh._toplevel(self.repo)
        ranges = closeout_fresh.changed_ranges(
            top, state["passes"][-1]["reviewed_tree"])
        self.assertEqual(ranges, {"src/caf\u00e9.py": [[10, 10]]})

    def test_helper_end_to_end_special_name(self):
        # Through finalize_inputs: unchanged -> write; edited -> refuse.
        for edit, action in ((None, "write"), (10, "refuse")):
            with self.subTest(edit=edit):
                state, h = self.decided_at("src/routes/+page.svelte", "defer")
                state_file = os.path.join(os.path.dirname(self.repo),
                                          "state.json")
                with open(state_file, "w", encoding="utf-8") as fh:
                    json.dump(state, fh)
                if edit is not None:
                    self.edit_at(edit)
                self.blob_out = os.path.join(os.path.dirname(self.repo),
                                             "blobs.json")
                code, out = run_new(self.argv(state_file), self.repo)
                self.assertEqual(code, 0, out)
                result = json.loads(out)
                self.assertEqual(result["action"], action, result)
                if edit is not None:
                    self.assertEqual(result["stale"],
                                     self.one(h, "defer", "line"))


class TestNoDecisionNoGit(DecidedCase):

    def test_no_current_decision_returns_empty_and_runs_no_git(self):
        state, _ = self.decided("defer")
        state.pop("decisions")
        self.edit(10)
        out, rec = self.recorded(state)
        self.assertEqual(out, [])
        self.assertEqual(rec.calls, [])

    def test_stale_decision_is_not_a_candidate_and_runs_no_git(self):
        # A decision the review already re-asks (stale) is not closed, so
        # Close out counts it as outstanding; this check never sees it.
        state, h = self.decided("defer")
        state["decisions"][h]["evidence"]["canonical_line_content"] = "other"
        self.edit(10)
        out, rec = self.recorded(state)
        self.assertEqual(out, [])
        self.assertEqual(rec.calls, [])

    def test_malformed_state_returns_empty_and_runs_no_git(self):
        for bad in (None, {}, {"passes": []}, {"passes": "x"}, []):
            with self.subTest(state=bad):
                self.new_repo()
                rec = Recorder(closeout_fresh._git)
                with mock.patch.object(closeout_fresh, "_git", rec):
                    out = closeout_fresh.stale_decisions(bad, {},
                                                         cwd=self.repo)
                self.assertEqual(out, [])
                self.assertEqual(rec.calls, [])


class TestFixPrecedence(DecidedCase):
    """A fresh fix-obsolete verdict on the current blob is newer evidence
    than the decision (2.15.0 precedence): that record is not a candidate."""

    def fixed(self, with_verdict):
        state, h = self.decided("defer")
        self.edit(10)
        git(self.repo, "commit", "-qam", "fix")
        blob = git(self.repo, "rev-parse", "HEAD:" + tdc.F).stdout.strip()
        if with_verdict:
            state["fix_verdicts"] = {h: {
                "verdict": "obsolete", "agent": "fix",
                "head_sha": state["passes"][-1]["head_sha"],
                "at_pass": state["passes"][-1]["pass_number"],
                "reason": "line rewritten", "verified_blob": blob}}
        return state, h

    def test_fix_obsolete_closed_record_is_not_a_candidate(self):
        state, _ = self.fixed(with_verdict=True)
        self.assertEqual(self.stale(state), [])

    def test_without_the_verdict_the_same_edit_is_stale(self):
        state, h = self.fixed(with_verdict=False)
        self.assertEqual(self.stale(state), self.one(h, "defer", "line"))


class TestMirrorLock(unittest.TestCase):
    """D-05: the window is the review's own (`score._NEARBY_LINES`,
    `score._nearby_changed`); this module mirrors it without importing score."""

    def test_nearby_lines_equals_score(self):
        self.assertEqual(closeout_fresh._NEARBY_LINES, score._NEARBY_LINES)

    def test_window_membership_equals_score_nearby_changed(self):
        rec = {"stable_hash": "h" * 64, "file": tdc.F, "line": 10}
        for n in (3, 4, 5, 9, 10, 11, 15, 16, 17):
            with self.subTest(edit=n):
                ranges = {tdc.F: [[n, n]]}
                out = closeout_fresh.stale_from_ranges(
                    [(rec, {"decision": "defer"}, [])], ranges, {tdc.F},
                    lambda f: True)
                self.assertEqual(bool(out),
                                 score._nearby_changed(rec, ranges))


class TestLineSet(DecidedCase):
    """The Close-out line set equals the review's stamp set
    (`score._nearby_spots`): the record's own line, every open same-hash
    copy's line and every covered member's line."""

    def test_same_hash_copy_line_counts(self):
        L0 = tdc.base_file()
        L0[9] = L0[39] = "return None"
        for edit, expect in ((44, "nearby"), (40, "nearby"), (46, None)):
            with self.subTest(edit=edit):
                self.new_repo(L0)
                s1, h = tdc.pass1(self.lines, conf=95, kind="defer")
                s2, _ = tdc.run_pass(
                    s1, self.lines,
                    [tdc.fresh("bugs", 40, self.lines, tdc.TITLE_A, conf=100)],
                    2, {tdc.F: []}, decided=tdc.target_decided(s1))
                lines = [f["line"] for f in s2["passes"][-1]["findings"]
                         if f["stable_hash"] == h]
                self.assertEqual(sorted(lines), [10, 40])
                state = self.bind(s2)
                self.edit(edit)
                self.assertEqual(self.stale(state),
                                 self.one(h, "defer", expect) if expect else [])

    def test_covered_member_line_counts(self):
        for edit, expect in ((17, "nearby"), (18, None)):
            with self.subTest(edit=edit):
                self.new_repo()
                s1, r1 = tdc.run_pass(
                    tdc.empty_state(), self.lines,
                    [tdc.fresh("bugs", 10, self.lines, tdc.TITLE_A, conf=95),
                     tdc.fresh("security", 12, self.lines, "Other thing",
                               conf=80)],
                    1, {tdc.F: [[1, 200]]})
                self.assertEqual(len(r1["findings"]), 1, r1["filtered"])
                h = r1["findings"][0]["stable_hash"]
                members = r1["findings"][0]["members"]
                self.assertEqual([m["line"] for m in members], [10, 12])
                state = self.bind(tdc.decide_on(s1, h, kind="dismiss"))
                self.edit(edit)
                self.assertEqual(self.stale(state),
                                 self.one(h, "dismiss", expect) if expect else [])


class TestArgvHygiene(DecidedCase):
    """Pitfall 6: a finding path never reaches a git argv."""

    def test_no_finding_path_ever_on_git_argv(self):
        for rel in (tdc.F, "notes/x.py"):
            with self.subTest(file=rel):
                state, h = self.decided("defer")
                state = json.loads(json.dumps(state).replace(tdc.F, rel))
                if rel != tdc.F:
                    self.put(self.lines, rel=rel)
                self.edit(10)
                out, rec = self.recorded(state)
                self.assertTrue(out)
                self.assertTrue(rec.calls)
                for arg in rec.argv_text():
                    self.assertNotIn(rel, arg)
                    self.assertNotIn(os.path.basename(rel), arg)

    def test_diff_argv_is_the_reverse_whole_tree_diff(self):
        state, _ = self.decided("defer")
        self.edit(10)
        _, rec = self.recorded(state)
        tree = state["passes"][-1]["reviewed_tree"]
        diffs = [c for c in rec.calls if c[0] == "diff"]
        self.assertEqual(diffs, [["diff", "-R", "--no-renames", "--text",
                                  *closeout_fresh.REV_FLAGS, tree, "--"]])


class TestOrdering(DecidedCase):

    def test_sorted_by_file_line_hash(self):
        self.new_repo()
        s1, r1 = tdc.run_pass(
            tdc.empty_state(), self.lines,
            [tdc.fresh("bugs", 40, self.lines, "Second title", conf=95),
             tdc.fresh("bugs", 10, self.lines, tdc.TITLE_A, conf=95)],
            1, {tdc.F: [[1, 200]]})
        self.assertEqual(len(r1["findings"]), 2, r1["filtered"])
        by_line = {f["line"]: f["stable_hash"] for f in r1["findings"]}
        s1 = tdc.decide_on(s1, by_line[40], kind="dismiss")
        s1 = tdc.decide_on(s1, by_line[10], kind="defer")
        state = self.bind(s1)
        edited = list(self.lines)
        edited[9] = "line_10 = danger()"
        edited[39] = "line_40 = danger()"
        self.put(edited)
        self.assertEqual(self.stale(state), [
            {"hash": by_line[10], "kind": "deferred", "cause": "line"},
            {"hash": by_line[40], "kind": "dismissed", "cause": "line"}])


class TestStorePath(tws._Chain):
    """The reviewed tree of an uncommitted block lives only in the vibe-check
    store (`_Chain.pass1`: finding at 40 in the uncommitted block 35-45,
    deferred). The comparison must read it there, and must fail closed when
    the store is gone."""

    def setUp(self):
        super().setUp()
        # Not `self._env`: _Chain uses that name for its fence environment.
        patcher = mock.patch.dict(os.environ, gitfixture.helper_env(),
                                  clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def stale(self):
        root = self.repo.repo
        blobs = finalize_inputs.head_blobs(self.s1, cwd=root)
        return closeout_fresh.stale_decisions(self.s1, blobs, cwd=root)

    def test_real_chain_store_tree_unchanged_keeps(self):
        self.pass1()
        self.assertEqual(self.stale(), [])

    def test_real_chain_store_tree_exact_edit_is_line(self):
        self.pass1()
        L2 = list(self.L1)
        L2[39] = "uncommitted_40 = safe_query(user_input)"
        self.repo.write(L2)
        self.assertEqual(self.stale(), [
            {"hash": self.h, "kind": "deferred", "cause": "line"}])

    def test_unverifiable_tree_not_in_store(self):
        self.pass1()
        shutil.rmtree(os.path.join(self.repo.repo, ".turingmind"))
        self.assertEqual(self.stale(), [
            {"hash": self.h, "kind": "deferred", "cause": "unverifiable"}])
        self.assertFalse(os.path.exists(
            os.path.join(self.repo.repo, ".turingmind")),
            "the check must never create the store")


CLOSEOUT_PATH = os.path.join(SCRIPTS_DIR, "closeout_fresh.py")
DIFF_R = '["diff", "-R", "--no-renames", "--text", *REV_FLAGS,'
SWAPPED = '"--src-prefix=b/", "--dst-prefix=a/"'
NORMAL = '"--src-prefix=a/", "--dst-prefix=b/"'


class TestModuleMutants(DecidedCase):
    """Each guard in closeout_fresh.py, removed by a source substitution,
    makes the named behaviour go wrong on the same fixture the real module
    gets right (decorative-guard lesson: no guard that can never trip)."""

    def mutant(self, *pairs):
        """A copy of closeout_fresh with each `(old, new)` replaced once."""
        with open(CLOSEOUT_PATH, "r", encoding="utf-8") as fh:
            src = fh.read()
        for old, new in pairs:
            self.assertIn(old, src,
                          "mutant text must be present in the real source")
            src = src.replace(old, new, 1)
        spec = importlib.util.spec_from_loader("closeout_fresh_mutant",
                                               loader=None)
        mod = importlib.util.module_from_spec(spec)
        mod.__file__ = CLOSEOUT_PATH
        exec(compile(src, CLOSEOUT_PATH, "exec"), mod.__dict__)
        return mod

    def both(self, state, mod):
        """(real result, mutant result) on the same state and repo."""
        blobs = finalize_inputs.head_blobs(state, cwd=self.repo)
        return (closeout_fresh.stale_decisions(state, blobs, cwd=self.repo),
                mod.stale_decisions(state, blobs, cwd=self.repo))

    # M2: forward diff. Dropping `-R` alone leaves the swapped prefixes
    # keying every range under `a/`; dropping it with the usual prefixes is
    # a true forward diff in working-tree numbering.
    def test_mutant_drop_reverse_misses_deleted_file(self):
        mod = self.mutant((DIFF_R, DIFF_R.replace('"-R", ', "")))
        state, h = self.decided("defer")
        git(self.repo, "rm", "-q", tdc.F)
        real, mutated = self.both(state, mod)
        self.assertEqual(real, self.one(h, "defer", "deleted"))
        self.assertEqual(mutated, self.one(h, "defer", "unverifiable"))

    def test_mutant_forward_diff_refuses_pure_shift(self):
        mod = self.mutant((DIFF_R, DIFF_R.replace('"-R", ', "")),
                          (SWAPPED, NORMAL))
        state, h = self.decided("defer")
        self.put(["shift_%02d = 0" % i for i in range(SHIFT)] + self.lines)
        real, mutated = self.both(state, mod)
        self.assertEqual(real, [])
        # Working-tree numbering: the 20 inserted lines are 1-20, line 10's.
        self.assertEqual(mutated, self.one(h, "defer", "line"))

    def test_mutant_forward_diff_loses_git_rm_deleted(self):
        mod = self.mutant((DIFF_R, DIFF_R.replace('"-R", ', "")),
                          (SWAPPED, NORMAL))
        state, h = self.decided("dismiss")
        git(self.repo, "rm", "-q", tdc.F)
        real, mutated = self.both(state, mod)
        self.assertEqual(real, self.one(h, "dismiss", "deleted"))
        self.assertNotEqual(mutated, real)

    # M3: the usual prefixes under -R key ranges as `a/<path>`: silent keep.
    def test_mutant_normal_prefixes_silently_keep_exact_edit(self):
        mod = self.mutant((SWAPPED, NORMAL))
        state, h = self.decided("defer")
        self.edit(10)
        real, mutated = self.both(state, mod)
        self.assertEqual(real, self.one(h, "defer", "line"))
        self.assertEqual(mutated, [])

    # M4: rename detection pairs src/a.py with src/b.py and prints no hunk.
    def test_mutant_renames_on_loses_git_mv_deleted(self):
        mod = self.mutant((DIFF_R, DIFF_R.replace('"--no-renames", ', "")))
        state, h = self.decided("defer")
        git(self.repo, "mv", tdc.F, "src/b.py")
        real, mutated = self.both(state, mod)
        self.assertEqual(real, self.one(h, "defer", "deleted"))
        self.assertNotEqual(mutated, real)

    # M5: the window must be the review's +/- 5.
    def test_mutant_window_4_keeps_edit_at_15(self):
        mod = self.mutant(("_NEARBY_LINES = 5", "_NEARBY_LINES = 4"))
        state, h = self.decided("defer")
        self.edit(15)
        real, mutated = self.both(state, mod)
        self.assertEqual(real, self.one(h, "defer", "nearby"))
        self.assertEqual(mutated, [])

    def test_mutant_window_6_refuses_edit_at_16(self):
        mod = self.mutant(("_NEARBY_LINES = 5", "_NEARBY_LINES = 6"))
        state, h = self.decided("defer")
        self.edit(16)
        real, mutated = self.both(state, mod)
        self.assertEqual(real, [])
        self.assertEqual(mutated, self.one(h, "defer", "nearby"))

    # M6: without the reviewed-tree membership check an untracked decided
    # file has no ranges and is silently kept.
    def test_mutant_no_membership_check_keeps_untracked(self):
        mod = self.mutant(("if file not in reviewed_paths:", "if False:"))
        state, h = self.decided("defer")
        state = json.loads(json.dumps(state).replace(tdc.F, "notes/x.py"))
        self.put(self.lines, rel="notes/x.py")
        real, mutated = self.both(state, mod)
        self.assertEqual(real, self.one(h, "defer", "untracked"))
        self.assertEqual(mutated, [])

    # M7: a comparison that cannot be made must never read as "unchanged".
    def test_mutant_unverifiable_as_unchanged_keeps_missing_tree(self):
        mod = self.mutant((
            "    except Unverifiable:\n        return _all_unverifiable(candidates)",
            "    except Unverifiable:\n        return []"))
        state, h = self.decided("defer")
        del state["passes"][-1]["reviewed_tree"]
        real, mutated = self.both(state, mod)
        self.assertEqual(real, self.one(h, "defer", "unverifiable"))
        self.assertEqual(mutated, [])


# --------------------------------------------------------------------------- #
# The wiring: finalize_inputs._run asks closeout_fresh, and nothing else
# changes. Mutation checks 1, 8 and 9 at the CLI boundary.
# --------------------------------------------------------------------------- #
FINALIZE_INPUTS_PATH = os.path.join(SCRIPTS_DIR, "finalize_inputs.py")
WIRING_CALL = "    stale = closeout_fresh.stale_decisions(state, blobs, cwd)\n"
FIX_CLOSES_SKIP = ("        if carry_state._fix_closes(rec, state, last, blobs):\n"
                   "            continue\n")
NO_CANDIDATES = "    if not candidates:\n        return []\n"
RESULT_DUMP = ("        return code, \"\"\n"
               "    return code, json.dumps(result, allow_nan=False)\n")


def _load_mutant(path, name, pairs):
    """A copy of the module at `path` with each `(old, new)` replaced once;
    every `old` must occur exactly once in the real source."""
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    for old, new in pairs:
        if src.count(old) != 1:
            raise AssertionError("mutant text must occur once: %r" % old)
        src = src.replace(old, new, 1)
    spec = importlib.util.spec_from_loader(name, loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = path
    exec(compile(src, path, "exec"), mod.__dict__)
    return mod


def no_decision_states():
    """(label, state or None) for 66-02's decision-free fixtures plus the
    missing state file (None)."""
    import test_finalize_inputs as tfi
    return (("phase45 fixture", tfi.load_fixture()),
            ("six-row", tfi.load_six_row()),
            ("no state file", None))


class TestWiringMutants(FreshCase):
    """Removing the wiring, ignoring fix precedence, or touching git / the
    result bytes when nothing is decision-closed each makes a named
    behaviour go wrong."""

    def inputs_mutant(self, *pairs):
        return _load_mutant(FINALIZE_INPUTS_PATH, "finalize_inputs_mutant",
                            pairs)

    def fresh_mutant(self, *pairs):
        return _load_mutant(CLOSEOUT_PATH, "closeout_fresh_mutant", pairs)

    def run_in(self, mod, state_file):
        """`mod.run` in-process on the case's Close out argv ->
        (code, stdout text), stderr dropped; state and repo unchanged (a
        missing state file stays missing)."""
        def call():
            with mock.patch("sys.stderr", new=_Sink()):
                return mod.run(self.argv(state_file), cwd=self.repo)
        return self.unchanged_or_absent(state_file, call)

    def unchanged_or_absent(self, state_file, fn):
        if os.path.exists(state_file):
            return self.unchanged(state_file, fn)
        listing = tree_listing(self.repo)
        out = fn()
        self.assertFalse(os.path.exists(state_file), "state file created")
        self.assertEqual(tree_listing(self.repo), listing)
        return out

    def result(self, mod, state_file):
        code, out = self.run_in(mod, state_file)
        self.assertEqual(code, 0, out)
        return json.loads(out)

    def fix_obsolete_after_edit(self, kind):
        """The decided line was rewritten and committed, and a last-pass
        fix-obsolete verdict on the new blob closes the record: 2.15.0
        precedence says the fix, not the decision, closes it."""
        state_file, h = self.repro_state(kind, edit=10)
        git(self.repo, "commit", "-qam", "fix")
        blob = git(self.repo, "rev-parse", "HEAD:" + tdc.F).stdout.strip()
        with open(state_file, "r", encoding="utf-8") as fh:
            state = json.load(fh)
        last = state["passes"][-1]
        state["fix_verdicts"] = {h: {
            "verdict": "obsolete", "agent": "fix",
            "head_sha": last["head_sha"], "at_pass": last["pass_number"],
            "reason": "line rewritten", "verified_blob": blob}}
        with open(state_file, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        return state_file, h

    def decision_free(self, state):
        """A repo from the 999.40 scenario with `state` (None: no state
        file) written beside it -> the state file path."""
        decided_file, _ = self.repro_state("defer")
        path = os.path.join(os.path.dirname(decided_file), "free.json")
        if state is not None:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(state, fh)
            self.assertEqual(closeout_fresh.decided_records(state, {}), [])
        return path

    # M1: the wiring call removed -> the 999.40 wrong keep comes back.
    def test_mutant_no_wiring_call_writes_stale_decision(self):
        mod = self.inputs_mutant((WIRING_CALL, "    stale = []\n"))
        for kind in KINDS:
            with self.subTest(kind=kind):
                state_file, h = self.repro_state(kind, edit=10)
                real = self.result(finalize_inputs, state_file)
                self.assertEqual((real["action"], real["next"]),
                                 ("refuse", closeout_fresh.NEXT_REVIEW_AGAIN))
                self.assertEqual(real["stale"], [
                    {"hash": h, "kind": KIND_WORD[kind], "cause": "line"}])
                wrong = self.result(mod, state_file)
                self.assertEqual((wrong["action"], wrong["next"]),
                                 ("write", "write-review-md"))
                self.assertNotIn("stale", wrong)

    # M8: decided_records ignores fix precedence -> a fixed record refuses.
    def test_mutant_ignoring_fix_precedence_refuses_fixed_record(self):
        mod = self.fresh_mutant((FIX_CLOSES_SKIP, ""))
        for kind in KINDS:
            with self.subTest(kind=kind):
                state_file, h = self.fix_obsolete_after_edit(kind)
                old = json.loads(self.run_old_case(state_file)[1])
                self.assertEqual(old["action"], "write")
                self.assertEqual(old["counts"]["verified_obsolete_hashes"], [h])
                real = self.result(finalize_inputs, state_file)
                self.assertEqual(real["action"], "write")
                self.assertNotIn("stale", real)
                with mock.patch.object(finalize_inputs, "closeout_fresh", mod):
                    wrong = self.result(finalize_inputs, state_file)
                self.assertEqual(wrong["action"], "refuse")
                self.assertEqual(wrong["stale"], [
                    {"hash": h, "kind": KIND_WORD[kind], "cause": "line"}])

    # M9a: git runs with no decision-closed record -> the no-git rule breaks.
    def test_mutant_git_without_candidates_is_seen(self):
        mod = self.fresh_mutant((NO_CANDIDATES,
                                 "    if not candidates:\n"
                                 "        _toplevel(cwd)\n"
                                 "        return []\n"))
        for label, state in no_decision_states()[:2]:
            with self.subTest(state=label):
                path = self.decision_free(state)
                rec = Recorder(closeout_fresh._git)
                with mock.patch.object(closeout_fresh, "_git", rec):
                    self.result(finalize_inputs, path)
                self.assertEqual(rec.calls, [])
                bad = Recorder(mod._git)
                with mock.patch.object(mod, "_git", bad), \
                        mock.patch.object(finalize_inputs, "closeout_fresh",
                                          mod):
                    self.result(finalize_inputs, path)
                self.assertEqual(bad.calls, [["rev-parse", "--show-toplevel"]])

    # M9b: a `stale` key on every result -> 2.15.0 bytes differ.
    def test_mutant_empty_stale_key_breaks_byte_identity(self):
        mod = self.inputs_mutant((RESULT_DUMP,
                                  "        return code, \"\"\n"
                                  "    result[\"stale\"] = stale\n"
                                  "    return code, json.dumps(result, "
                                  "allow_nan=False)\n"))
        for kind in KINDS:
            with self.subTest(kind=kind):
                state_file, _ = self.repro_state(kind)
                old = self.run_old_case(state_file)
                self.assertEqual(old[0], 0, old[1])
                code, out = self.run_in(finalize_inputs, state_file)
                self.assertEqual((code, out.encode("utf-8")), old)
                code, out = self.run_in(mod, state_file)
                self.assertEqual(code, 0)
                self.assertNotEqual(out.encode("utf-8"), old[1])
                self.assertEqual(json.loads(out)["stale"], [])

    def test_differential_no_git_when_no_decision_closed(self):
        for label, state in no_decision_states():
            with self.subTest(state=label):
                path = self.decision_free(state)
                rec = Recorder(closeout_fresh._git)
                with mock.patch.object(closeout_fresh, "_git", rec):
                    code, out = self.run_in(finalize_inputs, path)
                self.assertEqual(code, 0, out)
                self.assertEqual(rec.calls, [])
                self.assertNotIn("stale", json.loads(out))
                old = self.unchanged_or_absent(path, lambda: run_old(
                    self.v215, self.argv(path), self.repo))
                new = self.unchanged_or_absent(path, lambda: run_new_cli(
                    self.argv(path), self.repo))
                self.assertEqual(old[0], 0, old[1])
                self.assertEqual(new, old)
                self.assertEqual(out.encode("utf-8"), old[1])


class _Sink:
    """A stderr stand-in that keeps nothing."""

    def write(self, text):
        return len(text)

    def flush(self):
        pass


# --------------------------------------------------------------------------- #
# Loop freedom (D-16): every refusal clears through the step it names. The
# review the refusal asks for runs through the real prose fences in fresh
# shells (`test_worktree_snap._Chain`), the owner re-decides what the review
# re-asks, Phase 4.5 persists, and Close out writes.
# --------------------------------------------------------------------------- #
README = "README"


class _ClearChain(tws._Chain):
    """`_Chain` (finding at src/a.py:40 in an uncommitted block) with the
    pass-1 decision kind chosen per test, every collected reviewed tree
    kept, and Close out run through the real helper."""

    def setUp(self):
        super().setUp()
        # Not `self._env`: _Chain uses that name for its fence environment.
        patcher = mock.patch.dict(os.environ, gitfixture.helper_env(),
                                  clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.trees = []
        self._calls = 0

    # -- the review, with the kind and the reviewed tree captured -------- #
    def collect(self, state_path, **kw):
        tree, nearby = super().collect(state_path, **kw)
        self.trees.append(tree)
        return tree, nearby

    def decided_pass1(self, kind, route="default"):
        """`_Chain.pass1` with the owner's answer `kind` (defer/dismiss)."""
        real = tdc.decide_on

        def answer(state, h, kind=None, reason=tdc.REASON):
            del kind  # pass1 always answers "defer"; the test chooses
            return real(state, h, kind=chosen, reason=reason)

        chosen = kind
        with mock.patch.object(tdc, "decide_on", answer):
            self.pass1(route=route)
        self.kind = kind
        self.assertEqual(self.s1["decisions"][self.h]["decision"], kind)

    def review_again(self, file_lines, findings, route="default"):
        """Pass 2 by the same fences as `_Chain.pass2`, for working trees
        where src/a.py is gone (`file_lines` is what Phase 1 reads there,
        [] when absent) or the route is `--all` -> (state, result)."""
        if route == "all":
            changed = {}
        else:
            sha = self.last_reviewed_sha(self.state_path)
            changed = self.ranges("default or GSD", tdr.INCR_PLACEHOLDER, sha)
        _, nearby = self.collect(self.state_path)
        over = {}
        if route == "all":
            over = tws._all_mode_over(file_lines, nearby)
        elif nearby:
            over["nearby_line_ranges"] = json.loads(nearby)
        return tdc.run_pass(self.s1, file_lines, findings, 2, changed,
                            decided=tdc.target_decided(self.s1), **over)

    # -- Close out ------------------------------------------------------- #
    def close_out(self, state_path, switches=None):
        """Finalize's helper on a fresh empty fingerprint file -> result."""
        self._calls += 1
        blob_out = os.path.join(os.path.dirname(self.repo.repo),
                                "blobs-%d.json" % self._calls)
        with open(blob_out, "wb"):
            pass
        code, out = finalize_inputs.run(
            argv_for(state_path, blob_out, switches), cwd=self.repo.repo)
        self.assertEqual(code, 0, out)
        return json.loads(out)

    def assert_refused(self, result, cause):
        self.assertEqual((result["action"], result["next"]),
                         ("refuse", closeout_fresh.NEXT_REVIEW_AGAIN))
        self.assertEqual(result["stale"], [
            {"hash": self.h, "kind": KIND_WORD[self.kind], "cause": cause}])
        self.assertIsNone(result["report"])

    def assert_writes(self, result):
        self.assertEqual((result["action"], result["next"]),
                         ("write", "write-review-md"), result)
        self.assertNotIn("stale", result)

    # -- after the fresh review ------------------------------------------ #
    def undecided(self, s2):
        """Hashes of open records the owner has no current decision on."""
        return sorted(rec["stable_hash"]
                      for rec in carry_state.open_findings(s2)
                      if carry_state.decision_state(rec, s2) != "current")

    def reasked_or_gone(self, s2):
        """The pass-1 decision does not stand: its record is re-asked
        (decision stale) or gone; either way something is left to decide
        unless nothing was re-reported."""
        rec = tdc.record_of(s2, self.h)
        if rec is not None:
            self.assertEqual(carry_state.decision_state(rec, s2), "stale",
                             "the fresh review kept a decision on changed code")

    def redecide_persist_close(self, s2, switches=None):
        """The owner answers every re-asked record with the same kind,
        Phase 4.5 persists the new reviewed tree, Close out runs."""
        for h in self.undecided(s2):
            s2 = tdc.decide_on(s2, h, kind=self.kind, reason="re-decided")
        self.assertEqual(self.undecided(s2), [])
        head = self.repo.git("rev-parse", "HEAD").stdout.strip()
        self.assertTrue(self.trees[-1], "the fresh review recorded no tree")
        _, path = self.persist(s2, head, self.trees[-1])
        return self.close_out(path, switches)


class TestClearable(_ClearChain):
    """refuse -> the requested fresh review -> re-decide -> Close out writes,
    for every cause and both decision kinds (D-16, RESEARCH Pitfall 1)."""

    def test_clearable_line(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                self.decided_pass1(kind)
                L2 = list(self.L1)
                L2[39] = "uncommitted_40 = safe_query(user_input)"
                self.repo.write(L2)
                self.assert_refused(self.close_out(self.state_path), "line")
                s2, _, _, _ = self.pass2(L2)
                self.reasked_or_gone(s2)
                self.assertTrue(self.undecided(s2), "nothing re-asked")
                self.assert_writes(self.redecide_persist_close(s2))

    def test_clearable_nearby(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                self.decided_pass1(kind)
                L2 = list(self.L1)
                L2[42] = "uncommitted_43 = other_call()"
                self.repo.write(L2)
                self.assert_refused(self.close_out(self.state_path), "nearby")
                s2, _, _, _ = self.pass2(L2)
                self.assertEqual(self.undecided(s2), [self.h])
                self.assertEqual(carry_state.stale_cause(
                    tdc.record_of(s2, self.h), s2), "nearby")
                self.assert_writes(self.redecide_persist_close(s2))

    def keep_tree_nonempty(self):
        """A second tracked file, so the working tree stays non-empty once
        src/a.py is removed (a real repo has more than one file)."""
        gitfixture.write(self.repo.repo, README, "readme\n")
        self.repo.git("add", README)

    def test_clearable_deleted_rm(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                self.decided_pass1(kind)
                self.keep_tree_nonempty()
                self.repo.git("rm", "-qf", tdc.F)
                self.assert_refused(self.close_out(self.state_path),
                                    "deleted")
                s2, _ = self.review_again([], [])
                self.assertIsNone(tdc.record_of(s2, self.h))
                self.assert_writes(self.redecide_persist_close(s2))

    def test_clearable_deleted_mv(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                self.decided_pass1(kind)
                self.repo.git("mv", "-f", tdc.F, "src/b.py")
                self.assert_refused(self.close_out(self.state_path),
                                    "deleted")
                moved = dict(self.finding(self.L1), file="src/b.py")
                s2, _ = self.review_again([], [moved])
                # Either outcome is a valid review: re-asked at the new
                # path, or the decision followed the record there.
                rec = tdc.record_of(s2, self.h)
                if rec is not None and rec["file"] == "src/b.py":
                    self.assertIn(carry_state.decision_state(rec, s2),
                                  ("current", "stale"))
                self.assert_writes(self.redecide_persist_close(s2))

    def test_clearable_untracked(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                self.untracked_pass1(kind)
                self.assert_refused(self.close_out(self.state_path),
                                    "untracked")
                # The refusal's next step (D-13): add the file, review again.
                self.repo.git("add", "-N", tdc.F)
                s2, _, _, _ = self.pass2(self.L1)
                self.reasked_or_gone(s2)
                self.assertTrue(self.undecided(s2), "nothing re-asked")
                self.assert_writes(self.redecide_persist_close(s2))

    def untracked_pass1(self, kind):
        """Pass 1 on a src/a.py that git does not track (README is the
        committed file): the reviewed tree cannot hold it."""
        self.L0 = tdc.base_file()
        self.repo = tdc.RealDiffRepo.make(self, self.L0)
        gitfixture.write(self.repo.repo, README, "readme\n")
        self.repo.git("add", README)
        self.repo.git("rm", "-q", "--cached", tdc.F)
        self.repo.git("commit", "-qm", "untrack")
        self.L1 = self.L0
        head = self.repo.git("rev-parse", "HEAD").stdout.strip()
        r1 = self.ranges("default")
        self.assertNotIn(tdc.F, r1)
        tree, _ = self.collect(os.path.join(self.repo.repo, "absent"))
        finding = tdc.fresh("security", 40, self.L1, tws.TITLE, conf=95)
        s1, res = tdc.run_pass(tdc.empty_state(), self.L1, [finding], 1, r1)
        self.assertEqual(len(res["findings"]), 1, res["filtered"])
        self.h = res["findings"][0]["stable_hash"]
        s1 = tdc.decide_on(s1, self.h, kind=kind, reason="later")
        self.kind = kind
        self.s1, self.state_path = self.persist(s1, head, tree)

    def test_clearable_unverifiable_store_removed(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                self.decided_pass1(kind)
                shutil.rmtree(os.path.join(self.repo.repo,
                                           worktree_snap.STORE_REL))
                self.assert_refused(self.close_out(self.state_path),
                                    "unverifiable")
                s2, _, _, nearby = self.pass2(self.L1)
                # The code did not change: the fresh review keeps the
                # decision (999.28 parity); a re-ask would be a false reopen.
                self.assertEqual(json.loads(nearby), {})
                self.assert_keeps(s2, self.h, 40)
                self.assertEqual(self.undecided(s2), [])
                self.assert_writes(self.redecide_persist_close(s2))


class TestClearableSpecialName(_ClearChain):
    """CR-01 loop freedom (D-16): a decision on `src/routes/+page.svelte`
    refuses on an edit, and the requested fresh review clears it, through
    the same real fences as TestClearable. Unchanged, it never refuses."""

    NAME = "src/routes/+page.svelte"

    def setUp(self):
        super().setUp()
        for mod in (tdc, tws):
            patcher = mock.patch.object(mod, "F", self.NAME)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_special_name_unchanged_writes(self):
        self.decided_pass1("defer")
        self.assertEqual(
            self.s1["passes"][-1]["findings"][0]["file"], self.NAME)
        self.assert_writes(self.close_out(self.state_path))

    def test_special_name_refuse_review_write(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                self.decided_pass1(kind)
                L2 = list(self.L1)
                L2[39] = "uncommitted_40 = safe_query(user_input)"
                self.repo.write(L2)
                self.assert_refused(self.close_out(self.state_path), "line")
                s2, _, _, _ = self.pass2(L2)
                self.reasked_or_gone(s2)
                self.assert_writes(self.redecide_persist_close(s2))


class TestAllRouteClearable(_ClearChain):
    """`--all` (D-12): a decision and an edit refuse; a fresh `--all` review
    clears. An edit to the decided line is re-asked. An edit only near it is
    NOT re-asked on `--all`: that route never sends `nearby_line_ranges`
    (no scorer effect, 66-05), so the fresh review keeps the decision and
    records the new tree, and Close out then writes. Either way no loop."""

    def finding(self, lines):
        # No in-diff term on --all; a confident finding still survives.
        return tdc.fresh("security", 40, lines, tws.TITLE, conf=95)

    EDITS = ((40, "uncommitted_40 = safe_query(user_input)", "line"),
             (43, "uncommitted_43 = other_call()", "nearby"))

    def test_all_route_refuses_then_clears(self):
        for kind in KINDS:
            for at, text, cause in self.EDITS:
                with self.subTest(kind=kind, cause=cause):
                    self.decided_pass1(kind, route="all")
                    self.assertTrue(
                        self.s1["passes"][-1].get("reviewed_tree"))
                    L2 = list(self.L1)
                    L2[at - 1] = text
                    self.repo.write(L2)
                    self.assert_refused(self.close_out(self.state_path),
                                        cause)
                    s2, _ = self.review_again(L2, [self.finding(L2)],
                                              route="all")
                    if cause == "line":
                        self.reasked_or_gone(s2)
                        self.assertTrue(self.undecided(s2),
                                        "nothing re-asked")
                    else:
                        self.assert_keeps(s2, self.h, 40)
                    self.assert_writes(self.redecide_persist_close(s2))


# --------------------------------------------------------------------------- #
# 999.44 shape 3 (60-REPRO R7): a decision on a file git does not track.
# No reviewed copy exists (the snapshot copies tracked files only, and
# copying untracked files was rejected: they may hold secrets), so the
# decision cannot be checked: refuse until the owner adds the file (D-13).
# --------------------------------------------------------------------------- #
NEW_FILE = "notes/new.py"
UNTRACKED_ROW = "if file not in reviewed_paths:"


class TestShape3Untracked(DecidedCase):

    def shape3_state(self, kind):
        """A finding on notes/new.py, written AFTER the commit and never
        added, that the owner decided; the last pass is bound to HEAD and
        `HEAD^{tree}` -> (state_file, hash)."""
        state, h = self.decided(kind)
        state = json.loads(json.dumps(state).replace(tdc.F, NEW_FILE))
        self.put(self.lines, rel=NEW_FILE)
        listed = git(self.repo, "ls-files", "--", NEW_FILE).stdout
        self.assertEqual(listed, "", "notes/new.py must be untracked")
        state_file = os.path.join(os.path.dirname(self.repo), "state.json")
        with open(state_file, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        self.blob_out = os.path.join(os.path.dirname(self.repo), "blobs.json")
        return state_file, h

    def test_old_helper_writes_on_untracked_decided_file(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state_file, _ = self.shape3_state(kind)
                code, out = self.run_old_case(state_file)
                self.assertEqual(code, 0, out)
                result = json.loads(out)
                # The R7 wrong keep on 2.15.0: nothing checks the decision.
                self.assertEqual((result["action"], result["next"]),
                                 ("write", "write-review-md"))
                self.assertNotIn("stale", result)

    def test_candidate_refuses_untracked(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                state_file, h = self.shape3_state(kind)
                code, out = self.run_new_case(state_file)
                self.assertEqual(code, 0, out)
                result = json.loads(out)
                self.assertEqual((result["action"], result["next"]),
                                 ("refuse", closeout_fresh.NEXT_REVIEW_AGAIN))
                self.assertEqual(result["stale"],
                                 self.one(h, kind, "untracked"))
                self.assertIsNone(result["report"])

    def test_git_add_n_then_review_clears(self):
        # Adding the file alone does not clear: the reviewed tree still
        # lacks it, so the review the refusal names is required.
        for kind in KINDS:
            with self.subTest(kind=kind, step="git add -N only"):
                state_file, h = self.shape3_state(kind)
                git(self.repo, "add", "-N", NEW_FILE)
                result = json.loads(self.run_new_case(state_file)[1])
                self.assertEqual(result["stale"],
                                 self.one(h, kind, "untracked"))
        # Add, then review again through the real fences: clears (D-13).
        outcome = unittest.TestResult()
        TestClearable("test_clearable_untracked").run(outcome)
        self.assertEqual(outcome.testsRun, 1)
        self.assertTrue(outcome.wasSuccessful(),
                        outcome.failures + outcome.errors)

    # Mutation check 6 at the CLI boundary: without the reviewed-tree
    # membership check the untracked decision has no ranges and Close out
    # writes again (the 2.15.0 wrong keep).
    def test_mutant_skip_absent_check_writes(self):
        mod = _load_mutant(CLOSEOUT_PATH, "closeout_fresh_mutant",
                           ((UNTRACKED_ROW, "if False:"),))
        for kind in KINDS:
            with self.subTest(kind=kind):
                state_file, _ = self.shape3_state(kind)
                real = json.loads(self.run_new_case(state_file)[1])
                self.assertEqual(real["action"], "refuse")
                with mock.patch.object(finalize_inputs, "closeout_fresh",
                                       mod):
                    wrong = json.loads(self.run_new_case(state_file)[1])
                self.assertEqual((wrong["action"], wrong["next"]),
                                 ("write", "write-review-md"))
                self.assertNotIn("stale", wrong)


# --------------------------------------------------------------------------- #
# PR and range Close out (D-15, D-04): judged against the files on disk.
# The last pass reviewed a commit (reviewed_tree = the range-end commit id).
# --------------------------------------------------------------------------- #
PR_RANGE = (("range", {"range_mode": True}), ("PR", {"pr_mode": True}))


class TestPrRangeDisk(DecidedCase):

    def range_state(self, kind):
        """Two commits; the review covered base..end and recorded the end
        commit as its reviewed tree (a decided finding at line 10) ->
        (state_file, hash, end commit)."""
        state, h = self.decided(kind)
        self.lines[49] = "line_50 = changed_in_the_range()"
        self.put(self.lines)
        git(self.repo, "commit", "-qam", "range end")
        end = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        last = state["passes"][-1]
        last["head_sha"] = end
        last["reviewed_tree"] = end
        state_file = os.path.join(os.path.dirname(self.repo), "state.json")
        with open(state_file, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        self.blob_out = os.path.join(os.path.dirname(self.repo), "blobs.json")
        return state_file, h, end

    def close_out(self, state_file, switches):
        result = self.unchanged(state_file, lambda: run_new(
            argv_for(state_file, self.fresh_blob_out(), switches),
            self.repo))
        self.assertEqual(result[0], 0, result[1])
        return json.loads(result[1])

    def fresh_blob_out(self):
        with open(self.blob_out, "wb"):
            pass
        return self.blob_out

    def assert_writes(self, result):
        self.assertEqual((result["action"], result["next"]),
                         ("write", "write-review-md"), result)
        self.assertNotIn("stale", result)

    def assert_refuses(self, result, h, kind, cause):
        self.assertEqual((result["action"], result["next"]),
                         ("refuse", closeout_fresh.NEXT_REVIEW_AGAIN))
        self.assertEqual(result["stale"], self.one(h, kind, cause))

    def each(self):
        for kind in KINDS:
            for route, switches in PR_RANGE:
                with self.subTest(kind=kind, route=route):
                    yield kind, switches

    def test_range_closeout_refuses_on_nearby_disk_edit(self):
        for kind, switches in self.each():
            state_file, h, _ = self.range_state(kind)
            self.assert_writes(self.close_out(state_file, switches))
            self.edit(13)  # uncommitted, within the +/- 5 window
            self.assert_refuses(self.close_out(state_file, switches),
                                h, kind, "nearby")

    def test_revert_edit_clears(self):
        for kind, switches in self.each():
            state_file, h, _ = self.range_state(kind)
            self.edit(13)
            self.assert_refuses(self.close_out(state_file, switches),
                                h, kind, "nearby")
            git(self.repo, "checkout", "-q", "--", tdc.F)
            self.assert_writes(self.close_out(state_file, switches))

    def test_checkout_reviewed_commit_clears(self):
        for kind, switches in self.each():
            state_file, h, end = self.range_state(kind)
            self.edit(13)
            git(self.repo, "commit", "-qam", "after the review")
            self.assert_refuses(self.close_out(state_file, switches),
                                h, kind, "nearby")
            git(self.repo, "checkout", "-q", end)
            self.assertEqual(git(self.repo, "status", "--porcelain").stdout,
                             "")
            self.assert_writes(self.close_out(state_file, switches))

    def test_pr_head_absent_locally_is_unverifiable(self):
        for kind, switches in self.each():
            state_file, h, _ = self.range_state(kind)
            with open(state_file, "r", encoding="utf-8") as fh:
                state = json.load(fh)
            absent = "0123456789abcdef" * 2 + "01234567"
            self.assertRegex(absent, worktree_snap.OBJECT_ID_RE)
            state["passes"][-1]["reviewed_tree"] = absent
            with open(state_file, "w", encoding="utf-8") as fh:
                json.dump(state, fh)
            # Fail closed: never fetched, never read as unchanged.
            self.assert_refuses(self.close_out(state_file, switches),
                                h, kind, "unverifiable")


# --------------------------------------------------------------------------- #
# The whole Finalize differential against 2.15.0: every fixture state the
# Close out tests build, in each disk variant, run through the literal
# d5acc19 helper and the working-tree helper. Each run is byte-identical, or
# it is a named difference: a freshness refusal in INTENDED, or the covering
# order repair in REPAIRED. Both lists are exhaustive both ways.
# --------------------------------------------------------------------------- #
VARIANTS = ("unchanged", "exact", "nearby", "outside", "untracked")
NEARBY_STEP = 3  # inside the +/- 5 window
OUTSIDE_STEP = 6  # just outside it
OLD_CLOSES = ("write", "outstanding-to-phase-5", "medium-ack-loop")

# (fixture, variant, kind) -> the stale cause every refused row must carry.
# The 2.15.0 helper wrote REVIEW.md or opened the card; the candidate
# refuses with `next: stop-review-again` because a deferred or dismissed
# decision rests on code it cannot prove unchanged (FRESH-01, D-09).
INTENDED = {
    ("999.40", "exact", "defer"): "line",
    ("999.40", "exact", "dismiss"): "line",
    ("999.40", "nearby", "defer"): "nearby",
    ("999.40", "nearby", "dismiss"): "nearby",
    ("999.40", "untracked", "defer"): "untracked",
    ("999.40", "untracked", "dismiss"): "untracked",
    ("shape3", "unchanged", "defer"): "untracked",
    ("shape3", "unchanged", "dismiss"): "untracked",
}
for _name in ("dismissed-all", "nv-open", "medium-only", "fix-obsolete"):
    INTENDED[("result:" + _name, "exact", "dismiss")] = "line"
    INTENDED[("result:" + _name, "nearby", "dismiss")] = "nearby"
    INTENDED[("result:" + _name, "untracked", "dismiss")] = "untracked"
# The parity grid's named D-09 refusals (66-04): the session's git cannot
# see the reviewed work tree. Reused by name, never re-derived here.
for _sc, _cause in tpg.FRESHNESS_REFUSALS:
    INTENDED[("grid:" + tpg.key_of(_sc), "unchanged", "dismiss")] = _cause

# (fixture, variant, kind) -> (commit, what changed). The 999.44 shape 2
# repair (owner-approved): when two decisions cover one finding, the newest
# decides it. 2.15.0 kept the finding closed by the older cover and wrote;
# the candidate counts it as outstanding and opens the card.
SHAPE2_REPAIR = ("75e4a1da", "newest covering decision wins (999.44 shape 2)")
REPAIRED = {("shape2:older_first:both", "unchanged", kind): SHAPE2_REPAIR
            for kind in KINDS}

# Commits that changed score.py since 2.15.0; empty while it is unchanged.
SCORER_CHANGES = ()


class _ClassCleanup:
    """`materialize_v215` registers its temp dir with `addCleanup`; this
    routes that to the class cleanup."""

    def __init__(self, cls):
        self.addCleanup = cls.addClassCleanup


def _run_pair(v215, argv, cwd, env, blob_out):
    """[old, new], each (returncode, stdout bytes, fingerprint-file bytes),
    the two helpers run by one recipe."""
    out = []
    for script in (os.path.join(v215, "finalize_inputs.py"), NEW_HELPER):
        with open(blob_out, "wb"):
            pass
        proc = subprocess.run([sys.executable, script, *argv], cwd=cwd,
                              env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, timeout=CALL_TIMEOUT)
        with open(blob_out, "rb") as fh:
            out.append((proc.returncode, proc.stdout, fh.read()))
    return out


def _target(state, repo):
    """(file, line) of the first record a current decision closes in the
    candidate's reading, or None when nothing is decision-closed."""
    blobs = finalize_inputs.head_blobs(state, cwd=repo)
    found = closeout_fresh.decided_records(state, blobs)
    return (found[0][0]["file"], found[0][0]["line"]) if found else None


def _rewrite(repo, rel, n):
    path = os.path.join(repo, rel)
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines(True)
    if n > len(lines):
        raise AssertionError("%s has no line %d" % (rel, n))
    lines[n - 1] = "edited after the review %d\n" % n
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("".join(lines))


def _apply_variant(repo, state, target, variant):
    """Change the disk (and for `untracked` the reviewed tree) after the
    review, without telling the state."""
    rel, line = target
    if variant == "exact":
        _rewrite(repo, rel, line)
    elif variant == "nearby":
        _rewrite(repo, rel, line + NEARBY_STEP)
    elif variant == "outside":
        _rewrite(repo, rel, line + OUTSIDE_STEP)
    elif variant == "untracked":
        git(repo, "rm", "-q", "--cached", "--", rel)
        git(repo, "commit", "-q", "-m", "untrack")  # only the removal is staged
        last = state["passes"][-1]
        last["head_sha"] = git(repo, "rev-parse", "HEAD").stdout.strip()
        last["reviewed_tree"] = git(repo, "rev-parse",
                                    "HEAD^{tree}").stdout.strip()


class TestOnlyIntendedDifferences(FreshCase):
    """The 2.15.0 Finalize differential over every fixture, computed once."""

    @classmethod
    def setUpClass(cls):
        cls._ctmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls._ctmp.cleanup)
        cls.top = os.path.realpath(cls._ctmp.name)
        env = gitfixture.helper_env()
        env["GIT_CEILING_DIRECTORIES"] = cls.top
        patch = mock.patch.dict(os.environ, env, clear=True)
        patch.start()
        try:
            cls.old_dir = materialize_v215(_ClassCleanup(cls))
            cls.n = 0
            cls.observed = {}
            cls.not_creatable = []
            cls._local_fixtures()
        finally:
            patch.stop()
        cls._grid()

    # -- recording ---------------------------------------------------------- #
    @classmethod
    def _case_dir(cls):
        cls.n += 1
        path = os.path.join(cls.top, "case%04d" % cls.n)
        os.makedirs(path)
        return path

    @classmethod
    def _observe(cls, key, state, repo, cwd=None, env=None):
        case_dir = os.path.dirname(repo)
        state_file = os.path.join(case_dir, "state.json")
        with open(state_file, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        blob_out = os.path.join(case_dir, "blobs.json")
        before = sha256_of(state_file)
        old, new = _run_pair(cls.old_dir, argv_for(state_file, blob_out),
                             cwd or repo, env or gitfixture.helper_env(),
                             blob_out)
        if sha256_of(state_file) != before:
            raise AssertionError("%r: state file written" % (key,))
        if key in cls.observed:
            raise AssertionError("fixture key %r built twice" % (key,))
        cls.observed[key] = (old, new)

    @classmethod
    def _with_variants(cls, name, kind, build):
        """`build()` -> (state, repo), a fresh repo per call, the state
        bound to an unchanged reviewed tree."""
        for variant in VARIANTS:
            state, repo = build()
            target = _target(state, repo)
            if target is None and variant != "unchanged":
                continue  # nothing decision-closed: no disk variant applies
            if variant != "unchanged":
                _apply_variant(repo, state, target, variant)
            cls._observe((name, variant, kind), state, repo)

    # -- fixture builders --------------------------------------------------- #
    @classmethod
    def _repro(cls, kind):
        """The 66-01 999.40 fixture: src/a.py reviewed on HEAD, a finding
        at line 10 decided."""
        repo = gitfixture.make_repo(cls._case_dir())
        lines = tdc.base_file()
        write(repo, tdc.F, "\n".join(lines) + "\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "x")
        state, _ = tdc.pass1(lines, conf=95, kind=kind)
        return tfi.bind_reviewed_tree(repo, state), repo

    @classmethod
    def _result_repo(cls):
        """The ResultCase repo (66-02): three source files and ARCH_FILE."""
        repo = gitfixture.make_repo(cls._case_dir())
        for rel, text in (("src/a.ts", "a1\n"), ("src/b.ts", "b1\n"),
                          ("sub/c.ts", "c1\n")):
            write(repo, rel, text)
        write(repo, tfi.ARCH_FILE, tfi.synthetic_text(
            tfi.lines_needed(tfi.load_fixture(), tfi.ARCH_FILE)))
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "init")
        return repo

    @classmethod
    def _result(cls, name):
        repo = cls._result_repo()
        if name == "six-row":
            return tfi.load_six_row(), repo
        if name == "loop":
            return tfi.load_fixture(), repo
        if name == "fix-obsolete":
            blob = git(repo, "rev-parse",
                       "HEAD:" + tfi.ARCH_FILE).stdout.strip()
            return tfi.fix_obsolete_state(blob, repo), repo
        builder = {"dismissed-all": tfi.dismissed_all_state,
                   "nv-open": tfi.nv_open_state,
                   "medium-only": tfi.medium_only_state}[name]
        return builder(repo), repo

    @classmethod
    def _shape3(cls, kind):
        """The 66-06 shape 3 fixture: the decided file was written after
        the reviewed commit and never added."""
        state, repo = cls._repro(kind)
        state = json.loads(json.dumps(state).replace(tdc.F, NEW_FILE))
        write(repo, NEW_FILE, "\n".join(tdc.base_file()) + "\n")
        return state, repo

    @classmethod
    def _shape2(cls, kind, order, decide):
        """The 66-08 shape 2 fixture (two covers, or one) on a repo holding
        the reviewed src/a.py."""
        sc = tdc.covering_order_scenario(kind, order, decide)
        lines = tdc.base_file()
        lines[11] = "line_12 = 'fixed'"
        repo = gitfixture.make_repo(cls._case_dir())
        state = tfi.bind_reviewed_tree(
            repo, sc["s"], {tdc.F: "\n".join(lines) + "\n"})
        return state, repo

    @classmethod
    def _local_fixtures(cls):
        for kind in KINDS:
            cls._with_variants("999.40", kind, lambda: cls._repro(kind))
            state, repo = cls._shape3(kind)
            cls._observe(("shape3", "unchanged", kind), state, repo)
            for order in tdc.SHAPE2_OLDER_TITLE:
                for label, decide in (("both", ("older", "newer")),
                                      ("older", ("older",)),
                                      ("newer", ("newer",))):
                    state, repo = cls._shape2(kind, order, decide)
                    cls._observe(("shape2:%s:%s" % (order, label),
                                  "unchanged", kind), state, repo)
        for name in ("six-row", "loop", "dismissed-all", "nv-open",
                     "medium-only", "fix-obsolete"):
            cls._with_variants("result:" + name, "dismiss",
                               lambda: cls._result(name))

    @classmethod
    def _grid(cls):
        """Every main parity-grid scenario (66-02/66-04 Builder), unchanged
        on disk, in the scenario's own session folder and environment."""
        top = os.path.realpath(tempfile.mkdtemp(prefix="vc-v215-grid-"))
        cls.addClassCleanup(shutil.rmtree, top, ignore_errors=True)
        shim = tpg.make_shim(top)

        def one(index, sc):
            base = os.path.join(top, "s%04d" % index)
            files = os.path.join(top, "f%04d" % index)
            os.makedirs(files)
            try:
                session, env, state, _ = tpg.build(sc, base, top, shim)
            except tpg.NotCreatable as exc:
                return sc, None, str(exc)
            state_file = os.path.join(files, "state.json")
            with open(state_file, "w", encoding="utf-8") as fh:
                json.dump(state, fh)
            blob_out = os.path.join(files, "blobs.json")
            return sc, _run_pair(cls.old_dir, argv_for(state_file, blob_out),
                                 session, env, blob_out), None

        workers = min(8, os.cpu_count() or 2)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            done = [f.result() for f in
                    [pool.submit(one, i, sc)
                     for i, sc in enumerate(tpg.all_scenarios())]]
        for sc, pair, why in done:
            key = ("grid:" + tpg.key_of(sc), "unchanged", "dismiss")
            if why is not None:
                cls.not_creatable.append((sc, why))
            else:
                cls.observed[key] = tuple(pair)

    # -- the rules ---------------------------------------------------------- #
    def explain(self, key, old, new):
        return "%r\n  2.15.0    rc=%d stdout=%r blobs=%r\n  candidate rc=%d " \
            "stdout=%r blobs=%r" % ((key,) + old + new)

    def check_refusal(self, key, old, new, cause):
        """2.15.0 closed out (wrote, or opened the card); the candidate
        refuses with the same counts and fingerprints, every stale row
        carrying `cause`."""
        msg = self.explain(key, old, new)
        self.assertEqual((old[0], new[0]), (0, 0), msg)
        self.assertEqual(new[2], old[2], msg)
        before, after = json.loads(old[1]), json.loads(new[1])
        self.assertIn(before["action"], OLD_CLOSES, msg)
        self.assertNotIn("stale", before, msg)
        self.assertEqual((after["action"], after["next"], after["report"]),
                         ("refuse", closeout_fresh.NEXT_REVIEW_AGAIN, None),
                         msg)
        self.assertEqual(after["counts"], before["counts"], msg)
        self.assertTrue(after["stale"], msg)
        self.assertEqual({row["cause"] for row in after["stale"]}, {cause},
                         msg)
        self.assertIn(cause, closeout_fresh.CAUSES)

    def check_repair(self, key, old, new):
        """2.15.0 wrote with the shape 2 finding closed; the candidate
        counts it outstanding and opens the card, with the same
        fingerprints."""
        msg = self.explain(key, old, new)
        self.assertEqual((old[0], new[0]), (0, 0), msg)
        self.assertEqual(new[2], old[2], msg)
        before, after = json.loads(old[1]), json.loads(new[1])
        self.assertEqual(before["action"], "write", msg)
        self.assertEqual(after["action"], "outstanding-to-phase-5", msg)
        self.assertNotIn("stale", after, msg)
        self.assertEqual(after["counts"]["outstanding_cw"],
                         before["counts"]["outstanding_cw"] + 1, msg)

    def test_only_intended_differences(self):
        for key, (old, new) in sorted(self.observed.items()):
            with self.subTest(fixture=key):
                if key in INTENDED:
                    self.check_refusal(key, old, new, INTENDED[key])
                elif key in REPAIRED:
                    self.check_repair(key, old, new)
                else:
                    self.assertEqual(new, old, self.explain(key, old, new))

    def test_only_intended_list_is_exhaustive(self):
        """No stale entry: every named difference was built here and does
        differ (a not-creatable grid scenario is excused only where the
        parity grid excuses it)."""
        skipped = {("grid:" + tpg.key_of(sc), "unchanged", "dismiss")
                   for sc, _ in self.not_creatable}
        for sc, why in self.not_creatable:
            self.assertTrue(("ending", sc.ending) in tpg.MAY_BE_UNCREATABLE
                            or ("name", sc.name) in tpg.MAY_BE_UNCREATABLE,
                            "%s not creatable: %s" % (tpg.key_of(sc), why))
        for key in list(INTENDED) + list(REPAIRED):
            with self.subTest(fixture=key):
                if key in skipped:
                    continue
                self.assertIn(key, self.observed, "named but never built")
                old, new = self.observed[key]
                self.assertNotEqual(new, old, "named but identical")
        for key, cause in INTENDED.items():
            self.assertNotIn(key, REPAIRED)
            self.assertIn(cause, closeout_fresh.CAUSES, key)
        self.assertGreaterEqual(len(self.observed), 250)

    def test_only_intended_scorer_byte_identical_to_d5acc19_or_listed(self):
        env = clean_env()
        old = subprocess.run(
            ["git", "rev-parse", V215_COMMIT + ":" + V215_REL + "score.py"],
            cwd=SCRIPTS_DIR, env=env, capture_output=True, text=True,
            stdin=subprocess.DEVNULL, timeout=60)
        self.assertEqual(old.returncode, 0, old.stderr)
        now = subprocess.run(
            ["git", "hash-object", "--no-filters",
             os.path.join(SCRIPTS_DIR, "score.py")],
            cwd=SCRIPTS_DIR, env=env, capture_output=True, text=True,
            stdin=subprocess.DEVNULL, timeout=60)
        self.assertEqual(now.returncode, 0, now.stderr)
        if now.stdout.strip() != old.stdout.strip():
            self.assertTrue(SCORER_CHANGES,
                            "score.py differs from d5acc19 and no commit "
                            "is listed in SCORER_CHANGES")
            for commit in SCORER_CHANGES:
                found = subprocess.run(
                    ["git", "cat-file", "-e", commit + "^{commit}"],
                    cwd=SCRIPTS_DIR, env=env, stdin=subprocess.DEVNULL,
                    capture_output=True, timeout=60)
                self.assertEqual(found.returncode, 0, commit)
        else:
            self.assertEqual(SCORER_CHANGES, ())


if __name__ == "__main__":
    unittest.main()
