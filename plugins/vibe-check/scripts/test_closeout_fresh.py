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

import closeout_fresh  # noqa: E402  (module under test)
import finalize_inputs  # noqa: E402  (the candidate helper, in-process)
import gitfixture  # noqa: E402  (shared temp-repo helper)
import score  # noqa: E402  (oracle for the mirrored window, D-05)
import test_decision_continuity as tdc  # noqa: E402  (pass1, base_file, F)
import test_worktree_snap as tws  # noqa: E402  (_Chain: a reviewed tree in the store)
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

    def test_unverifiable_path_failing_PATH_RE(self):
        for bad in ("src/a b.py", "src/a.py;rm", "src/$(x).py", "", 5):
            with self.subTest(file=bad):
                state, h = self.decided("defer")
                state["passes"][-1]["findings"][0]["file"] = bad
                self.assertEqual(self.stale(state),
                                 self.one(h, "defer", "unverifiable"))


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


if __name__ == "__main__":
    unittest.main()
