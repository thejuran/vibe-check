"""999.28 — decisions on uncommitted code were re-asked on every pass.

Phase 61 live smoke C1: on the default route, a finding in uncommitted code
that the owner deferred at pass 1 was re-asked at pass 2 on a byte-identical
working tree, with the false reason "code next to it changed since your
decision on pass 1". Cause: the pass >= 2 range source
(30-collect-score.md, row "default or GSD, pass ≥ 2") is
`git diff <last head_sha>`; before any commit that sha is still HEAD, so the
whole uncommitted block was in `changed_line_ranges` on every pass, and
score.py stamps a decided row's `snapshot.nearby_at` from those ranges.

The fix gives the stamp its own input, `nearby_line_ranges`: the lines changed
since the working tree the last pass reviewed (`worktree_snap.py collect`,
which also records this pass's tree as the pass entry's `reviewed_tree`).
`changed_line_ranges` is unchanged, so the in-diff score term and the
persisted re-check trigger are unchanged.

Every test here drives the real chain: the fences are read from the prose
files (never retyped) and run in fresh `bash -s` shells inside temp git repos,
and the ranges they print go through the real score.py, carry_state.py and
batch_card.py. Run with bare `pytest`.
"""

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

import carry_state  # noqa: E402
import gitfixture  # noqa: E402
import gitsnap  # noqa: E402
import worktree_snap  # noqa: E402
import state_shape  # noqa: E402
import test_decision_continuity as tdc  # noqa: E402
import test_diff_ranges as tdr  # noqa: E402

F = tdc.F
PLUGIN_ROOT = os.path.dirname(SCRIPTS_DIR)
PERSIST_MD = os.path.join(PLUGIN_ROOT, "phases", "review", "45-persist.md")
SCHEMA = os.path.join(SCRIPTS_DIR, "fixtures", "future-schema.json")
COLLECT_CALL = 'worktree_snap.py" collect'
TRIAGE_MD = os.path.join(PLUGIN_ROOT, "phases", "review", "10-triage.md")
TAKE_CALL = 'worktree_snap.py" take'
# Phase 0 (current) take fences, per route.
P0_DEFAULT = 'worktree_snap.py" take --root "$GREPO"\n'
P0_RANGE = 'take --root "$GREPO" --range "<range>"'
P0_PR = 'take --root "$GREPO" --pr-head "$PR_HEAD"'
# e7075ea's Phase 1 take fences and Phase 0 PR bind (kept so the RED run on
# that commit drives its own prose).
OLD_TAKE_RANGE = 'take --root "$GREPO" --out "$GREPO/.turingmind/worktree-snap/before.json" --range'
OLD_TAKE_PR = 'take --root "$GREPO" --out "$GREPO/.turingmind/worktree-snap/before.json" --pr-head'
PR_BIND = "PR_HEAD=$(gh pr view"


class _Phases:
    """Runs one pass's snapshot fences in prose order: Phase 0's take (before
    the reviewed diff), `after_diff` (a change after the diff was collected,
    before the old Phase-1 point), the e7075ea Phase-1 take if that prose is
    what is under test, `between` (a change while the reviewers run), then
    Phase 3's collect with the printed snapshot literal substituted."""

    def _lookup_fences(self, route):
        scope, triage = _scope_text(), _triage_text()
        p0 = {"default": P0_DEFAULT, "range": P0_RANGE, "PR": P0_PR}[route]
        self.p0_take = tdr._fence_holding(scope, p0)
        self.p1_take = None
        self.pr_bind = None
        if self.p0_take is None:  # e7075ea prose
            old = {"default": TAKE_CALL, "range": OLD_TAKE_RANGE,
                   "PR": OLD_TAKE_PR}[route]
            self.p1_take = tdr._fence_holding(triage, old)
            if route == "PR":
                self.pr_bind = tdr._fence_holding(scope, PR_BIND)

    def _fill(self, fence):
        return fence

    def _env(self, state_path):
        return {"STATE_FILE": state_path}

    def take_only(self, state_path):
        """Just this pass's take, wherever the prose puts it -> snapshot
        literal ("" for e7075ea's file-based take)."""
        env = self._env(state_path)
        fence = self.p0_take if self.p0_take is not None else self.p1_take
        proc = _bash(self._fill(fence), self.repo.repo, env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        if self.p0_take is not None:
            return _printed(proc.stdout, "REVIEWED_SNAPSHOT")
        return ""

    def collect_only(self, state_path, snap):
        proc = _bash(self._fill(self.collect_fence).replace(
            "<REVIEWED_SNAPSHOT>", snap), self.repo.repo, self._env(state_path))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return (_printed(proc.stdout, "REVIEWED_TREE"),
                _printed(proc.stdout, "NEARBY_LINE_RANGES"))

    def run_pass_fences(self, state_path, after_diff=None, between=None,
                        skip_take=False):
        env = self._env(state_path)
        snap = ""
        if self.p0_take is not None and not skip_take:
            proc = _bash(self._fill(self.p0_take), self.repo.repo, env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            snap = _printed(proc.stdout, "REVIEWED_SNAPSHOT")
        pr_head = ""
        if self.pr_bind is not None:
            proc = _bash(self._fill(self.pr_bind), self.repo.repo, env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            pr_head = _printed(proc.stdout, "PR_HEAD")
        if after_diff is not None:
            after_diff()
        if self.p1_take is not None and not skip_take:
            proc = _bash(self._fill(self.p1_take).replace("<PR_HEAD>", pr_head),
                         self.repo.repo, env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
        if between is not None:
            between()
        proc = _bash(self._fill(self.collect_fence).replace(
            "<REVIEWED_SNAPSHOT>", snap), self.repo.repo, env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return (_printed(proc.stdout, "REVIEWED_TREE"),
                _printed(proc.stdout, "NEARBY_LINE_RANGES"))


def _triage_text():
    with open(TRIAGE_MD, encoding="utf-8") as fh:
        return fh.read()


def _scope_text():
    with open(tdr.SCOPE_MD, encoding="utf-8") as fh:
        return fh.read()
NEARBY_TEXT = "code next to it changed since your decision on pass 1"
BLOCK = range(35, 46)  # the uncommitted block; the finding sits at 40
TITLE = "SQL injection"


def _uncommitted(lines):
    out = list(lines)
    for n in BLOCK:
        out[n - 1] = "uncommitted_%d = query(user_input)" % n
    return out


def _bash(script, cwd, env_extra):
    env = gitfixture.helper_env()
    env["VC_ROOT"] = PLUGIN_ROOT
    for k in ("LAST_REVIEWED_SHA", "PHASE_START", "STATE_FILE"):
        env.pop(k, None)
    env.update(env_extra)
    return subprocess.run(["bash", "-s"], input=script, cwd=cwd, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=120)


def _printed(stdout, key):
    vals = [ln[len(key) + 1:] for ln in stdout.splitlines()
            if ln.startswith(key + "=")]
    assert len(vals) == 1, (key, stdout)
    return vals[0]


class _Chain(_Phases, tdc._RealChain):
    """Pass 1 reviews an uncommitted block and the owner defers the finding;
    pass 2 runs every prose fence again in fresh shells."""

    def setUp(self):
        self.text = tdr._collect_text()
        self.range_fence = tdr.prose_range_fence(self.text)
        self.collect_fence = tdr._fence_holding(self.text, COLLECT_CALL)
        self.assertIsNotNone(self.collect_fence,
                             "30-collect-score.md has no worktree_snap fence")
        with open(tdr.STATE_MD, encoding="utf-8") as fh:
            self.bind_fence = tdr._fence_holding(fh.read(), tdr.HEAD_SHA_CALL)
        self._lookup_fences("default")

    # -- the prose fences ------------------------------------------------- #
    def ranges(self, row, placeholder=None, value=None):
        source = tdr.prose_range_source(self.text, row)
        if placeholder:
            self.assertIn(placeholder, source)
            source = source.replace(placeholder, '"%s"' % value)
        proc = _bash(self.range_fence.replace("<range source>", source),
                     self.repo.repo, {})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def collect(self, state_path, **kw):
        return self.run_pass_fences(state_path, **kw)

    def persist(self, state, head, tree):
        """45-persist.md: head_sha, plus `reviewed_tree` when one was
        printed (omitted when empty)."""
        state = json.loads(json.dumps(state))
        state["passes"][-1]["head_sha"] = head
        if tree:
            state["passes"][-1]["reviewed_tree"] = tree
        path = os.path.join(os.path.dirname(self.repo.repo), "state.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        return state, path

    def last_reviewed_sha(self, state_path):
        proc = _bash(self.bind_fence, self.repo.repo,
                     {"STATE_FILE": state_path, "FINALIZE_MODE": "0"})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return _printed(proc.stdout, "LAST_REVIEWED_SHA")

    # -- the two passes --------------------------------------------------- #
    def pass1(self, route="default", record_tree=True):
        self.L0 = tdc.base_file()
        self.repo = tdc.RealDiffRepo.make(self, self.L0)
        if route == "GSD":
            phase_start = self.repo.base
            self.repo.write(tdc._edited(self.L0, 5))
            self.repo.commit("phase work")
            self.L0 = tdc._edited(self.L0, 5)
        self.L1 = _uncommitted(self.L0)
        self.repo.write(self.L1)
        head = self.repo.git("rev-parse", "HEAD").stdout.strip()
        if route == "GSD":
            r1 = self.ranges("GSD", tdr.GSD_PLACEHOLDER, phase_start)
            self.assertEqual(r1, {F: [[5, 5], [35, 45]]})
        else:
            r1 = self.ranges("default")
            self.assertEqual(r1, {F: [[35, 45]]})
        tree, nearby = self.collect(os.path.join(self.repo.repo, "absent"))
        self.assertRegex(tree, r"^[0-9a-f]{40}$")
        self.assertEqual(nearby, "")  # pass 1: no prior tree
        s1, res = tdc.run_pass(tdc.empty_state(), self.L1,
                               [self.finding(self.L1)], 1, r1)
        self.assertEqual(len(res["findings"]), 1, res["filtered"])
        self.h = res["findings"][0]["stable_hash"]
        s1 = tdc.decide_on(s1, self.h, kind="defer", reason="later")
        self.s1, self.state_path = self.persist(
            s1, head, tree if record_tree else None)
        self.assertEqual(state_shape.check_state(
            self.s1, state_shape.load_schema("future")), [])

    def finding(self, lines):
        return tdc.fresh("security", 40, lines, TITLE, conf=75)

    def pass2(self, L2, rereport=True, use_nearby=True):
        if L2 != self.L1:
            self.repo.write(L2)
        self.assertEqual(self.repo.read(), L2)
        sha = self.last_reviewed_sha(self.state_path)
        changed = self.ranges("default or GSD", tdr.INCR_PLACEHOLDER, sha)
        _, nearby = self.collect(self.state_path)
        over = {}
        if use_nearby and nearby:
            over["nearby_line_ranges"] = json.loads(nearby)
        s2, res = tdc.run_pass(
            self.s1, L2, [self.finding(L2)] if rereport else [], 2, changed,
            decided=tdc.target_decided(self.s1), **over)
        return s2, res, changed, nearby

    def card(self, s2):
        return tdc.card_text_full(s2)


class TestRepro999_28(_Chain):
    """The C1 reproduction, kept as a documenting test: with only the old
    input (`changed_line_ranges`) the identical tree re-asks."""

    def test_identical_tree_old_input_reasks(self):
        self.pass1()
        s2, _, changed, _ = self.pass2(self.L1, use_nearby=False)
        self.assertEqual(changed, {F: [[35, 45]]})
        self.assert_reopens(s2, self.h, 40)
        self.assertIn(NEARBY_TEXT, self.card(s2))


class TestUncommittedDecisionKept(_Chain):

    def test_identical_tree_keeps_the_deferral(self):
        self.pass1()
        s2, _, changed, nearby = self.pass2(self.L1)
        # The in-diff input is unchanged: still the whole uncommitted block.
        self.assertEqual(changed, {F: [[35, 45]]})
        self.assertEqual(json.loads(nearby), {})
        self.assert_keeps(s2, self.h, 40)
        self.assertNotIn("code next to it changed", self.card(s2))

    def test_identical_tree_keeps_without_a_rereport(self):
        self.pass1()
        s2, _, _, _ = self.pass2(self.L1, rereport=False)
        self.assert_keeps(s2, self.h, 40)

    def test_gsd_route_identical_tree_keeps(self):
        self.pass1(route="GSD")
        s2, _, changed, nearby = self.pass2(self.L1)
        self.assertEqual(changed, {F: [[35, 45]]})
        self.assertEqual(json.loads(nearby), {})
        self.assert_keeps(s2, self.h, 40)

    def test_committed_unchanged_between_passes_keeps(self):
        self.pass1()
        self.repo.commit("commit the reviewed block unchanged")
        s2, _, changed, nearby = self.pass2(self.L1)
        self.assertEqual(changed, {F: [[35, 45]]})
        self.assertEqual(json.loads(nearby), {})
        self.assert_keeps(s2, self.h, 40)

    def test_far_edit_keeps(self):
        self.pass1()
        L2 = tdc._edited(self.L1, 52)  # 12 lines below the finding
        s2, _, _, nearby = self.pass2(L2)
        self.assertEqual(json.loads(nearby), {F: [[52, 52]]})
        self.assert_keeps(s2, self.h, 40)

    def test_in_diff_score_unchanged_by_the_new_input(self):
        self.pass1()
        _, with_nearby, _, _ = self.pass2(self.L1)
        _, without, _, _ = self.pass2(self.L1, use_nearby=False)
        self.assertEqual(
            [f["orchestrator_score"] for f in with_nearby["findings"]],
            [f["orchestrator_score"] for f in without["findings"]])


class TestUncommittedNearbyEditReopens(_Chain):
    """Phase 61 S2: a real edit near the decided line still re-asks."""

    def test_edit_three_lines_above_reopens(self):
        self.pass1()
        L2 = list(self.L1)
        L2[36] = "uncommitted_37 = guard_removed"  # line 37
        s2, _, _, nearby = self.pass2(L2)
        self.assertEqual(json.loads(nearby), {F: [[37, 37]]})
        self.assert_reopens(s2, self.h, 40)
        self.assertIn(NEARBY_TEXT, self.card(s2))

    def test_deleted_line_above_reopens(self):
        self.pass1()
        L2 = list(self.L1)
        del L2[37]  # line 38; the finding moves to 39
        s2, _, _, nearby = self.pass2(L2)
        self.assertEqual(json.loads(nearby), {F: [[37, 38]]})
        self.assert_reopens(s2, self.h, 39)

    def test_edit_after_commit_reopens(self):
        self.pass1()
        self.repo.commit("commit the reviewed block")
        L2 = list(self.L1)
        L2[42] = "uncommitted_43 = changed"  # line 43
        s2, _, _, nearby = self.pass2(L2)
        self.assertEqual(json.loads(nearby), {F: [[43, 43]]})
        self.assert_reopens(s2, self.h, 40)


class TestFallsBackTowardAsking(_Chain):
    """Without a recorded tree (a 2.14.0 state, or a pass whose tree could
    not be recorded) the stamp uses `changed_line_ranges`, as before."""

    def test_state_without_reviewed_tree_reasks(self):
        self.pass1(record_tree=False)
        s2, _, _, nearby = self.pass2(self.L1)
        self.assertEqual(nearby, "")
        self.assert_reopens(s2, self.h, 40)

    def test_unknown_tree_id_reasks(self):
        self.pass1()
        bogus = json.loads(json.dumps(self.s1))
        bogus["passes"][-1]["reviewed_tree"] = "0" * 40
        self.s1, self.state_path = self.persist(
            bogus, bogus["passes"][-1]["head_sha"], None)
        s2, _, _, nearby = self.pass2(self.L1)
        self.assertEqual(nearby, "")
        self.assert_reopens(s2, self.h, 40)

    def test_crafted_tree_value_never_reaches_git(self):
        self.pass1()
        marker = os.path.join(os.path.dirname(self.repo.repo), "pwned")
        bad = json.loads(json.dumps(self.s1))
        bad["passes"][-1]["reviewed_tree"] = "$(touch %s)" % marker
        self.s1, self.state_path = self.persist(
            bad, bad["passes"][-1]["head_sha"], None)
        _, nearby = self.collect(self.state_path)
        self.assertEqual(nearby, "")
        self.assertFalse(os.path.exists(marker))


class TestMidPassEditDefault(_Chain):
    """Deep-review WR (cc5c92a): the tree must be the one the reviewers
    read. An edit near the finding after Phase 1's snapshot and before
    Phase 3's collect must not be recorded as reviewed, so pass 2 (with no
    further change) re-asks instead of keeping the decision."""

    def test_edit_during_pass_one_reasks_on_pass_two(self):
        self.L0 = tdc.base_file()
        self.repo = tdc.RealDiffRepo.make(self, self.L0)
        self.L1 = _uncommitted(self.L0)
        self.repo.write(self.L1)
        head = self.repo.git("rev-parse", "HEAD").stdout.strip()
        r1 = self.ranges("default")
        L1b = list(self.L1)
        L1b[36] = "uncommitted_37 = guard_removed_mid_pass"
        tree, _ = self.collect(os.path.join(self.repo.repo, "absent"),
                               between=lambda: self.repo.write(L1b))
        s1, res = tdc.run_pass(tdc.empty_state(), L1b, [self.finding(L1b)], 1, r1)
        self.h = res["findings"][0]["stable_hash"]
        s1 = tdc.decide_on(s1, self.h, kind="defer", reason="later")
        self.s1, self.state_path = self.persist(s1, head, tree)
        self.L1 = L1b
        s2, _, _, nearby = self.pass2(L1b)
        self.assert_reopens(s2, self.h, 40)
        self.assertEqual((tree, nearby), ("", ""))

    def test_no_edit_during_pass_records_the_tree(self):
        self.pass1()
        self.assertIn("reviewed_tree", self.s1["passes"][-1])

    def test_collect_without_take_records_nothing(self):
        self.pass1()
        tree, nearby = self.collect(self.state_path, skip_take=True)
        self.assertEqual((tree, nearby), ("", ""))


class TestReReview999_28(_Chain):
    """Re-review of e7075ea: three remaining fail-open paths."""

    def _decided_pass1(self):
        self.pass1()
        self.assertIn("reviewed_tree", self.s1["passes"][-1])

    def _pass2_with(self, L_reviewed, L_now, **kw):
        """Pass 2: the reviewers read `L_reviewed`; the tree is `L_now` at
        collect (the change happens per `kw`)."""
        changed = self.ranges("default or GSD", tdr.INCR_PLACEHOLDER,
                              self.last_reviewed_sha(self.state_path))
        tree, nearby = self.collect(self.state_path, **kw)
        over = {"nearby_line_ranges": json.loads(nearby)} if nearby else {}
        s2, _ = tdc.run_pass(self.s1, L_now, [self.finding(L_now)], 2, changed,
                             decided=tdc.target_decided(self.s1), **over)
        return s2, tree, nearby

    # 1. A mismatch must blank the nearby ranges too (prior pass decided).
    def test_mid_pass_revert_of_a_nearby_edit_reasks(self):
        """Pass 2's reviewers read line 38 edited (T1); while they run, the
        edit is reverted (T2 == the pass-1 tree). Ranges against T2 say
        "nothing changed", in a numbering the reviewers never saw."""
        self._decided_pass1()
        L1b = list(self.L1)
        L1b[37] = "uncommitted_38 = guard_removed"
        self.repo.write(L1b)
        s2, tree, nearby = self._pass2_with(
            L1b, self.L1, between=lambda: self.repo.write(self.L1))
        self.assert_reopens(s2, self.h, 40)
        self.assertEqual((tree, nearby), ("", ""))

    def test_mid_pass_insert_above_reasks(self):
        """The reviewers read line 38 edited; ten lines are inserted at the
        top while they run."""
        self._decided_pass1()
        L1b = list(self.L1)
        L1b[37] = "uncommitted_38 = guard_removed"
        self.repo.write(L1b)
        L2 = tdc.TOP_TEN + L1b
        s2, tree, nearby = self._pass2_with(
            L1b, L2, between=lambda: self.repo.write(L2))
        self.assert_reopens(s2, self.h, 50)
        self.assertEqual((tree, nearby), ("", ""))

    # 2. The snapshot must precede the reviewed diff.
    def test_edit_after_diff_collection_is_not_recorded(self):
        """An edit near the finding after Phase 0 collected the reviewed diff
        but before the old Phase-1 snapshot point."""
        self.L0 = tdc.base_file()
        self.repo = tdc.RealDiffRepo.make(self, self.L0)
        self.L1 = _uncommitted(self.L0)
        self.repo.write(self.L1)
        head = self.repo.git("rev-parse", "HEAD").stdout.strip()
        L1b = list(self.L1)
        L1b[36] = "uncommitted_37 = changed_after_diff"
        r1 = self.ranges("default")
        tree, _ = self.collect(os.path.join(self.repo.repo, "absent"),
                               after_diff=lambda: self.repo.write(L1b))
        s1, res = tdc.run_pass(tdc.empty_state(), L1b, [self.finding(L1b)], 1, r1)
        self.h = res["findings"][0]["stable_hash"]
        s1 = tdc.decide_on(s1, self.h, kind="defer", reason="later")
        self.s1, self.state_path = self.persist(s1, head, tree)
        self.L1 = L1b
        s2, _, _, nearby = self.pass2(L1b)
        self.assert_reopens(s2, self.h, 40)
        self.assertEqual((tree, nearby), ("", ""))

    # 3. A pass consumes only its own snapshot.
    def test_overlapping_passes_never_consume_each_other(self):
        """Pass A snapshots T1; the tree moves to T2; pass B snapshots T2;
        A collects first. A must record nothing (its reviewers read T1), and
        B must record its own T2."""
        self._decided_pass1()
        snap_a = self.take_only(self.state_path)
        L2 = tdc._edited(self.L1, 37)
        self.repo.write(L2)
        snap_b = self.take_only(self.state_path)
        tree_a, nearby_a = self.collect_only(self.state_path, snap_a)
        self.assertEqual((tree_a, nearby_a), ("", ""))
        tree_b, _ = self.collect_only(self.state_path, snap_b)
        self.assertRegex(tree_b, r"^[0-9a-f]{40}$")

    def test_leftover_snapshot_of_a_halted_pass_is_not_used(self):
        """A pass that halted after its snapshot leaves it unconsumed; the
        next pass, with no snapshot of its own, records nothing."""
        self._decided_pass1()
        self.take_only(self.state_path)  # halted: never collected
        tree, nearby = self.collect_only(self.state_path, "")
        self.assertEqual((tree, nearby), ("", ""))

    def test_snapshot_literal_cannot_name_another_path(self):
        self._decided_pass1()
        victim = os.path.join(os.path.dirname(self.repo.repo), "keep-me")
        os.mkdir(victim)
        for bad in ("../" * 8 + victim.lstrip("/"), victim, "0" * 31,
                    "$(touch %s/pwned)" % victim):
            with self.subTest(bad=bad):
                self.assertEqual(self.collect_only(self.state_path, bad), ("", ""))
        self.assertTrue(os.path.isdir(victim))
        self.assertEqual(os.listdir(victim), [])


class TestCollectInternals(unittest.TestCase):
    """Re-review of 695aeb9, at the helper level (the races are inside one
    `collect` call, so they are driven through hooks, not prose fences)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = gitfixture.make_repo(tmp.name)
        self.L0 = tdc.base_file()
        self.write(self.L0)
        gitfixture.git(self.root, "add", F)
        gitfixture.git(self.root, "commit", "-q", "-m", "base")
        self.L1 = _uncommitted(self.L0)
        self.write(self.L1)
        prior = worktree_snap.take(self.root)
        self.state = os.path.join(tmp.name, "state.json")
        with open(self.state, "w", encoding="utf-8") as fh:
            json.dump({"passes": [{"pass_number": 1, "reviewed_tree": prior}]}, fh)

    def write(self, lines):
        gitfixture.write(self.root, F, "\n".join(lines) + "\n")

    def test_nearby_ranges_are_the_matched_tree_not_the_live_one(self):
        """Pass 2's reviewers read line 38 edited (T1). Right after collect
        matches T1, the edit is reverted on disk. The ranges must still be
        T1's (line 38), not the live tree's (nothing)."""
        L1b = list(self.L1)
        L1b[37] = "uncommitted_38 = guard_removed"
        self.write(L1b)
        nonce, _ = worktree_snap.take_before(self.root)
        orig = worktree_snap._current

        def hooked(*args, **kw):
            out = orig(*args, **kw)
            self.write(self.L1)  # lands between the match and the diff
            return out

        with mock.patch.object(worktree_snap, "_current", hooked):
            tree, nearby, _ = worktree_snap.collect(self.root, self.state,
                                                    nonce=nonce)
        self.assertRegex(tree, r"^[0-9a-f]{40}$")
        self.assertEqual(json.loads(nearby), {F: [[38, 38]]})

    def test_interrupted_object_import_leaves_no_partial_object(self):
        """A kill mid-copy must not leave a truncated object at its final
        name in the shared store (it would never be repaired)."""
        L1b = tdc._edited(self.L1, 50)
        self.write(L1b)
        nonce, _ = worktree_snap.take_before(self.root)
        src = os.path.join(worktree_snap._snap_dir(nonce), "objects")
        names = [os.path.relpath(os.path.join(d, f), src)
                 for d, _, fs in os.walk(src) for f in fs]
        self.assertTrue(names)

        def dying_copy(a, b, *args, **kw):
            with open(a, "rb") as fin, open(b, "wb") as fout:
                fout.write(fin.read()[:3])
            raise OSError("killed mid-copy")

        with mock.patch.object(worktree_snap.shutil, "copyfile", dying_copy):
            worktree_snap.collect(self.root, self.state, nonce=nonce)
        store = os.path.join(self.root, worktree_snap.STORE_REL, "objects")
        for name in names:
            self.assertFalse(os.path.exists(os.path.join(store, name)), name)
        leftovers = [f for d, _, fs in os.walk(store) for f in fs
                     if not re.match(r"^[0-9a-f]{38}$", f)
                     and not d.endswith(("info", "pack"))]
        self.assertEqual(leftovers, [])


class TestPhase0DoesNotCreateTuringmind(_Chain):
    """Phase 0's take runs before Phase 0.7's first-run check, which keys on
    `.turingmind/` existing: it must not create it."""

    def test_take_leaves_no_turingmind_dir(self):
        self.L0 = tdc.base_file()
        self.repo = tdc.RealDiffRepo.make(self, self.L0)
        self.repo.write(_uncommitted(self.L0))
        snap = self.take_only(os.path.join(self.repo.repo, "absent"))
        self.assertRegex(snap, r"^[0-9a-f]{32}$")
        self.assertFalse(os.path.exists(os.path.join(self.repo.repo, ".turingmind")))
        tree, _ = self.collect_only(os.path.join(self.repo.repo, "absent"), snap)
        self.assertRegex(tree, r"^[0-9a-f]{40}$")


class TestRepoUntouched(_Chain):
    """The snapshot writes nothing to `.git`: no object, ref or index."""

    def _objects(self):
        out = []
        root = os.path.join(self.repo.repo, ".git", "objects")
        for d, _, files in os.walk(root):
            out.extend(os.path.join(d, f) for f in files)
        return sorted(out)

    def test_git_dir_and_index_unchanged(self):
        self.L0 = tdc.base_file()
        self.repo = tdc.RealDiffRepo.make(self, self.L0)
        self.repo.write(_uncommitted(self.L0))
        self.repo.git("add", F)
        self.repo.write(tdc._edited(_uncommitted(self.L0), 50))
        index = os.path.join(self.repo.repo, ".git", "index")
        with open(index, "rb") as fh:
            index_before = fh.read()
        objects_before = self._objects()
        snap_before = gitsnap.take_snapshot(self.repo.repo)
        tree, _ = self.collect(os.path.join(self.repo.repo, "absent"))
        self.assertRegex(tree, r"^[0-9a-f]{40}$")
        with open(index, "rb") as fh:
            self.assertEqual(fh.read(), index_before)
        self.assertEqual(self._objects(), objects_before)
        self.assertEqual(gitsnap.take_snapshot(self.repo.repo), snap_before)
        # The tree is readable only through the vibe-check store.
        self.assertNotEqual(
            gitfixture.git(self.repo.repo, "cat-file", "-t", tree,
                           check=False).returncode, 0)


class TestSplitIndexRepo(_Chain):
    """A repo with `core.splitIndex=true`: the temporary index must never
    add or expire a `sharedindex.*` file in the git dir."""

    def test_split_index_repo_git_dir_unchanged(self):
        self.L0 = tdc.base_file()
        self.repo = tdc.RealDiffRepo.make(self, self.L0)
        self.repo.git("config", "core.splitIndex", "true")
        self.repo.git("update-index", "--split-index")
        self.repo.write(_uncommitted(self.L0))
        git_dir = os.path.join(self.repo.repo, ".git")
        before = sorted(os.listdir(git_dir))
        self.assertTrue(any(n.startswith("sharedindex.") for n in before))
        tree, _ = self.collect(os.path.join(self.repo.repo, "absent"))
        self.assertRegex(tree, r"^[0-9a-f]{40}$")
        self.assertEqual(sorted(os.listdir(git_dir)), before)


class TestScorerInput(tdc._RealChain):
    """score.py: `nearby_line_ranges` feeds the decision stamp only; a
    malformed value falls back to `changed_line_ranges` (toward asking)."""

    def _run(self, nearby):
        L0, s1, hA = self._decide40()
        over = {} if nearby is _ABSENT else {"nearby_line_ranges": nearby}
        s2, res = tdc.run_pass(s1, L0, [], 2, {F: [[38, 38]]},
                               decided=tdc.target_decided(s1), **over)
        return s2, res, hA

    def test_absent_uses_changed_ranges(self):
        s2, _, hA = self._run(_ABSENT)
        self.assert_reopens(s2, hA, 40)

    def test_empty_object_keeps(self):
        s2, _, hA = self._run({})
        self.assert_keeps(s2, hA, 40)

    def test_nearby_range_reopens(self):
        s2, _, hA = self._run({F: [[44, 44]]})
        self.assert_reopens(s2, hA, 40)

    def test_malformed_falls_back(self):
        for bad in ([], "x", None, {F: "38"}, {F: [["38", "38"]]},
                    {F: [[38]]}, {F: [[True, 40]]}, {1: [[38, 38]]},
                    {F: [[40, 38]]}):
            with self.subTest(bad=bad):
                s2, _, hA = self._run(bad)
                self.assert_reopens(s2, hA, 40)


_ABSENT = object()


class TestScorerStampSites(tdc._Base):
    """Every stamp site reads `nearby_line_ranges`: a kept-open row (a
    decided record this pass's filters dropped) and a member sidecar that
    carries its own decision, not only the survivor row."""

    def _kept_open(self, over):
        L0 = tdc.base_file()
        s1, hA = tdc.pass1(L0, conf=tdc.KEPT_OPEN_CONF, kind="defer")
        s2, _ = tdc.run_pass(s1, L0, [], 2, {F: [[8, 8]]},
                             decided=tdc.target_decided(s1), **over)
        self.assertIn("kept_open", tdc.row_of(s2, hA))
        rec = self._current(s2, hA)
        return carry_state.decision_state(rec, s2), carry_state.stale_cause(rec, s2)

    def test_kept_open_row_reopens_on_changed_ranges(self):
        self.assertEqual(self._kept_open({}), ("stale", "nearby"))

    def test_kept_open_row_keeps_when_nothing_changed_since(self):
        self.assertEqual(self._kept_open({"nearby_line_ranges": {}}),
                         ("current", None))

    def _sidecar(self, over):
        L0 = tdc.base_file()
        def a(L):
            return tdc.fresh("bugs", 10, L, tdc.TITLE_A, conf=tdc.STABLE_CONF)

        def b(L):
            return tdc.fresh("security", 12, L, "Injection at B", conf=95,
                             severity="critical", category="injection")
        s1, r1 = tdc.run_pass(tdc.empty_state(), L0, [a(L0)], 1, {F: [[1, 200]]})
        hA = r1["findings"][0]["stable_hash"]
        s1 = tdc.decide_on(s1, hA)
        s2, r2 = tdc.run_pass(s1, L0, [a(L0), b(L0)], 2, {F: [[1, 200]]},
                              decided=tdc.target_decided(s1),
                              nearby_line_ranges={})
        hB = [f for f in r2["findings"] if f["agent"] == "security"][0]["stable_hash"]
        s2 = tdc.decide_on(s2, hB)
        s3, _ = tdc.run_pass(s2, L0, [a(L0), b(L0)], 3, {F: [[6, 6]]},
                             decided=tdc.target_decided(s2), **over)
        rec = self._current(s3, hA)
        self.assertNotEqual(tdc.row_of(s3, hA), rec, "A must be a member sidecar")
        return carry_state.decision_state(rec, s3)

    def test_member_sidecar_reopens_on_changed_ranges(self):
        self.assertEqual(self._sidecar({}), "stale")

    def test_member_sidecar_keeps_when_nothing_changed_since(self):
        self.assertEqual(self._sidecar({"nearby_line_ranges": {}}), "current")


RANGE_CALL = '--range "<range>"'
PR_CALL = "--pr-head"
FAKE_GH = """#!/bin/sh
# Stand-in for `gh` (no network): `pr view ... --jq .headRefOid` prints the
# PR head sha, `pr diff ... --color never` prints the cumulative diff.
case "$1 $2" in
  "pr view") [ -s "$FAKE_PR_DIR/head" ] || exit 1; cat "$FAKE_PR_DIR/head" ;;
  "pr diff") cat "$FAKE_PR_DIR/diff" ;;
  *) exit 2 ;;
esac
"""


def _block(lines, tag):
    out = list(lines)
    for n in BLOCK:
        out[n - 1] = "%s_%d = query(user_input)" % (tag, n)
    return out


class _CommittedChain(_Phases, tdc._RealChain):
    """PR and range routes on COMMITTED code: the block 35-45 is committed
    on top of `base`; pass 1 reviews base..<end>, the owner defers the
    finding at 40, and pass 2 reviews again. Every fence is read from
    30-collect-score.md and run in a fresh `bash -s`."""

    ROUTE = None  # "range" or "PR"

    def setUp(self):
        self.text = tdr._collect_text()
        self.range_fence = tdr.prose_range_fence(self.text)
        needle = RANGE_CALL if self.ROUTE == "range" else PR_CALL
        self.collect_fence = tdr._fence_holding(self.text, needle)
        self.assertIsNotNone(self.collect_fence,
                             "30-collect-score.md has no %s collect fence"
                             % self.ROUTE)
        self._lookup_fences(self.ROUTE)
        self.L0 = tdc.base_file()
        self.repo = tdc.RealDiffRepo.make(self, self.L0)
        self.L1 = _block(self.L0, "committed")
        self.repo.write(self.L1)
        self.repo.commit("work under review")
        self.end = self.head()
        tmp = os.path.dirname(self.repo.repo)
        self.fake = os.path.join(tmp, "fakepr")
        os.makedirs(os.path.join(self.fake, "bin"))
        gh = os.path.join(self.fake, "bin", "gh")
        with open(gh, "w", encoding="utf-8") as fh:
            fh.write(FAKE_GH)
        os.chmod(gh, 0o755)

    def head(self):
        return self.repo.git("rev-parse", "HEAD").stdout.strip()

    def env(self, state_path):
        return {"STATE_FILE": state_path, "FAKE_PR_DIR": self.fake,
                "PATH": os.path.join(self.fake, "bin") + os.pathsep
                + os.environ.get("PATH", "")}

    def publish(self, head_sha, gh_head=True):
        """What `gh` reports for the PR: head sha and cumulative diff."""
        diff = self.repo.git("diff", "--no-color", "--src-prefix=a/",
                             "--dst-prefix=b/", self.repo.base,
                             head_sha).stdout
        with open(os.path.join(self.fake, "diff"), "w", encoding="utf-8") as fh:
            fh.write(diff)
        with open(os.path.join(self.fake, "head"), "w", encoding="utf-8") as fh:
            fh.write(head_sha + "\n" if gh_head else "")

    def fill(self, fence):
        if self.ROUTE == "range":
            return fence.replace("<range>", "%s..HEAD" % self.repo.base)
        return fence.replace("<ref>", "7")

    def ranges(self, state_path):
        source = self.fill(tdr.prose_range_source(self.text, self.ROUTE))
        proc = _bash(self.range_fence.replace("<range source>", source),
                     self.repo.repo, self.env(state_path))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def _fill(self, fence):
        return self.fill(fence)

    def _env(self, state_path):
        return self.env(state_path)

    def collect(self, state_path, **kw):
        return self.run_pass_fences(state_path, **kw)

    def finding(self, lines):
        return tdc.fresh("security", 40, lines, TITLE, conf=75)

    def pass1(self, record=True):
        if self.ROUTE == "PR":
            self.publish(self.end)
        absent = os.path.join(self.repo.repo, "absent")
        r1 = self.ranges(absent)
        self.assertEqual(r1, {F: [[35, 45]]})
        tree, nearby = self.collect(absent)
        self.assertEqual(tree, self.end)
        self.assertEqual(nearby, "")
        s1, res = tdc.run_pass(tdc.empty_state(), self.L1,
                               [self.finding(self.L1)], 1, r1)
        self.h = res["findings"][0]["stable_hash"]
        s1 = tdc.decide_on(s1, self.h, kind="defer", reason="later")
        s1["passes"][-1]["head_sha"] = self.end
        if record:
            s1["passes"][-1]["reviewed_tree"] = tree
        self.assertEqual(state_shape.check_state(
            s1, state_shape.load_schema("future")), [])
        self.s1 = s1
        self.state_path = os.path.join(os.path.dirname(self.repo.repo),
                                       "state.json")
        self.save()

    def save(self):
        with open(self.state_path, "w", encoding="utf-8") as fh:
            json.dump(self.s1, fh)

    def move_end(self, L2, msg="new commit on the PR / range end"):
        self.repo.write(L2)
        self.repo.commit(msg)
        self.end = self.head()
        if self.ROUTE == "PR":
            self.publish(self.end)

    def pass2(self, L2, use_nearby=True):
        changed = self.ranges(self.state_path)
        tree, nearby = self.collect(self.state_path)
        over = {}
        if use_nearby and nearby:
            over["nearby_line_ranges"] = json.loads(nearby)
        s2, res = tdc.run_pass(self.s1, L2, [self.finding(L2)], 2, changed,
                               decided=tdc.target_decided(self.s1), **over)
        return s2, res, changed, nearby, tree


class _CommittedCases:
    """Shared cases for the PR and range routes."""

    def test_old_input_reasks_unchanged_code(self):
        """The reproduction, kept as a documenting test."""
        self.pass1()
        s2, _, changed, _, _ = self.pass2(self.L1, use_nearby=False)
        self.assertEqual(changed, {F: [[35, 45]]})
        self.assert_reopens(s2, self.h, 40)
        self.assertIn(NEARBY_TEXT, tdc.card_text_full(s2))

    def test_unchanged_keeps(self):
        self.pass1()
        s2, _, changed, nearby, tree = self.pass2(self.L1)
        self.assertEqual(changed, {F: [[35, 45]]})
        self.assertEqual(json.loads(nearby), {})
        self.assertEqual(tree, self.end)
        self.assert_keeps(s2, self.h, 40)
        self.assertNotIn("code next to it changed", tdc.card_text_full(s2))

    def test_new_commit_near_the_finding_reopens(self):
        self.pass1()
        L2 = list(self.L1)
        L2[36] = "committed_37 = guard_removed"
        self.move_end(L2)
        s2, _, _, nearby, _ = self.pass2(L2)
        self.assertEqual(json.loads(nearby), {F: [[37, 37]]})
        self.assert_reopens(s2, self.h, 40)
        self.assertIn(NEARBY_TEXT, tdc.card_text_full(s2))

    def test_new_commit_far_from_the_finding_keeps(self):
        self.pass1()
        L2 = tdc._edited(self.L1, 55)
        self.move_end(L2)
        s2, _, _, nearby, _ = self.pass2(L2)
        self.assertEqual(json.loads(nearby), {F: [[55, 55]]})
        self.assert_keeps(s2, self.h, 40)

    def test_moved_end_ignores_uncommitted_edits(self):
        """The PR and range routes review commits, so an uncommitted edit
        near the finding in the local checkout is not a change to them."""
        self.pass1()
        L2 = tdc._edited(self.L1, 55)
        self.move_end(L2)
        local = list(L2)
        local[36] = "local_37 = uncommitted"
        self.repo.write(local)
        s2, _, _, nearby, _ = self.pass2(L2)
        self.assertEqual(json.loads(nearby), {F: [[55, 55]]})
        self.assert_keeps(s2, self.h, 40)

    def test_rewritten_history_near_the_finding_reopens(self):
        """A force-push / rebased range end: the end commit is replaced by
        a different one whose line 43 differs."""
        self.pass1()
        self.repo.git("reset", "-q", "--hard", self.repo.base)
        L2 = _block(self.L0, "committed")
        L2[42] = "committed_43 = rewritten"
        self.move_end(L2, "rewritten history")
        s2, _, _, nearby, _ = self.pass2(L2)
        self.assertEqual(json.loads(nearby), {F: [[43, 43]]})
        self.assert_reopens(s2, self.h, 40)

    def test_scores_unchanged_by_the_new_input(self):
        self.pass1()
        _, with_n, c1, _, _ = self.pass2(self.L1)
        _, without, c2, _, _ = self.pass2(self.L1, use_nearby=False)
        self.assertEqual(c1, c2)
        self.assertEqual(
            [(f["orchestrator_score"], f["band"]) for f in with_n["findings"]],
            [(f["orchestrator_score"], f["band"]) for f in without["findings"]])

    def test_state_without_snapshot_reasks(self):
        self.pass1(record=False)
        s2, _, _, nearby, _ = self.pass2(self.L1)
        self.assertEqual(nearby, "")
        self.assert_reopens(s2, self.h, 40)


class _MidPassCases:
    """Deep-review WR (cc5c92a): a commit or push near the finding while
    the reviewers run must not be recorded as reviewed."""

    def test_change_during_pass_one_reasks_on_pass_two(self):
        if self.ROUTE == "PR":
            self.publish(self.end)
        absent = os.path.join(self.repo.repo, "absent")
        r1 = self.ranges(absent)
        L1b = list(self.L1)
        L1b[36] = "committed_37 = guard_removed_mid_pass"
        tree, _ = self.collect(absent, between=lambda: self.move_end(L1b))
        s1, res = tdc.run_pass(tdc.empty_state(), L1b, [self.finding(L1b)], 1, r1)
        self.h = res["findings"][0]["stable_hash"]
        s1 = tdc.decide_on(s1, self.h, kind="defer", reason="later")
        s1["passes"][-1]["head_sha"] = self.end
        if tree:
            s1["passes"][-1]["reviewed_tree"] = tree
        self.s1 = s1
        self.state_path = os.path.join(os.path.dirname(self.repo.repo),
                                       "state.json")
        self.save()
        s2, _, _, nearby, _ = self.pass2(L1b)
        self.assert_reopens(s2, self.h, 40)
        self.assertEqual((tree, nearby), ("", ""))


class TestRangeRoute(_MidPassCases, _CommittedCases, _CommittedChain):
    ROUTE = "range"

    def test_range_end_is_resolved_not_trusted(self):
        self.pass1()
        self.fill = lambda fence: fence.replace("<range>", "a..--output=/tmp/x")
        tree, nearby = self.collect(self.state_path)
        self.assertEqual((tree, nearby), ("", ""))


class TestPRRoute(_MidPassCases, _CommittedCases, _CommittedChain):
    ROUTE = "PR"

    def test_unchanged_head_not_local_keeps(self):
        """An unchanged PR head needs no local objects: same id, `{}`."""
        self.pass1()
        ghost = "ab" * 20
        self.s1["passes"][-1]["reviewed_tree"] = ghost
        self.save()
        self.publish(self.end)
        with open(os.path.join(self.fake, "head"), "w", encoding="utf-8") as fh:
            fh.write(ghost + "\n")
        s2, _, _, nearby, tree = self.pass2(self.L1)
        self.assertEqual(tree, ghost)
        self.assertEqual(json.loads(nearby), {})
        self.assert_keeps(s2, self.h, 40)

    def test_moved_head_with_old_head_not_local_reasks(self):
        """Toward asking: the previous head is not available locally."""
        self.pass1()
        self.s1["passes"][-1]["reviewed_tree"] = "cd" * 20
        self.save()
        s2, _, _, nearby, _ = self.pass2(self.L1)
        self.assertEqual(nearby, "")
        self.assert_reopens(s2, self.h, 40)

    def test_gh_failure_records_nothing_and_reasks(self):
        self.pass1()
        self.publish(self.end, gh_head=False)
        s2, _, _, nearby, tree = self.pass2(self.L1)
        self.assertEqual((tree, nearby), ("", ""))
        self.assert_reopens(s2, self.h, 40)

    def test_crafted_pr_head_never_reaches_git(self):
        self.pass1()
        marker = os.path.join(os.path.dirname(self.repo.repo), "pwned")
        with open(os.path.join(self.fake, "head"), "w", encoding="utf-8") as fh:
            fh.write("$(touch %s)\n" % marker)
        tree, nearby = self.collect(self.state_path)
        self.assertEqual((tree, nearby), ("", ""))
        self.assertFalse(os.path.exists(marker))


class TestRangeAfterDiff(_CommittedChain):
    ROUTE = "range"

    def test_commit_after_diff_collection_is_not_recorded(self):
        absent = os.path.join(self.repo.repo, "absent")
        r1 = self.ranges(absent)
        L1b = list(self.L1)
        L1b[36] = "committed_37 = changed_after_diff"
        tree, _ = self.collect(absent, after_diff=lambda: self.move_end(L1b))
        s1, res = tdc.run_pass(tdc.empty_state(), L1b, [self.finding(L1b)], 1, r1)
        self.h = res["findings"][0]["stable_hash"]
        s1 = tdc.decide_on(s1, self.h, kind="defer", reason="later")
        s1["passes"][-1]["head_sha"] = self.end
        if tree:
            s1["passes"][-1]["reviewed_tree"] = tree
        self.s1 = s1
        self.state_path = os.path.join(os.path.dirname(self.repo.repo), "state.json")
        self.save()
        s2, _, _, nearby, _ = self.pass2(L1b)
        self.assert_reopens(s2, self.h, 40)
        self.assertEqual((tree, nearby), ("", ""))


class TestProse(unittest.TestCase):

    def test_every_snapshot_call_states_the_finalize_and_all_skip(self):
        """`/review <phase> --finalize` must not take a snapshot nobody
        collects: each route's take states the skip (GSD included)."""
        scope = _scope_text()
        for take in (P0_DEFAULT, P0_PR, P0_RANGE,
                     "take the same working-tree snapshot as mode 1"):
            with self.subTest(take=take):
                at = scope.index(take)
                para = scope[at:scope.index("\n\n", at)]
                self.assertIn("--finalize", para)
                self.assertIn("FINALIZE_MODE=1", para)
                self.assertIn("--all", para)

    def test_snapshot_is_taken_before_each_reviewed_diff(self):
        """Phase 0 takes the snapshot before the diff the reviewers get, on
        every route; Phase 1 no longer takes one."""
        scope = _scope_text()
        for take, diff in ((P0_DEFAULT, "   git diff HEAD\n   git diff --staged"),
                           (P0_PR, "gh pr diff <ref> --patch"),
                           (P0_RANGE, "   git diff <range>\n"),
                           ("take the same working-tree snapshot as mode 1",
                            "PHASE_START=$(git log")):
            with self.subTest(take=take):
                self.assertEqual(scope.count(take), 1)
                self.assertLess(scope.index(take), scope.index(diff))
        self.assertNotIn(TAKE_CALL, _triage_text())


    def test_collect_fence_is_one_call_with_state_file(self):
        text = tdr._collect_text()
        fences = [tdr._fence_holding(text, n)
                  for n in (COLLECT_CALL, RANGE_CALL, PR_CALL)]
        self.assertEqual(len({f for f in fences if f}), 3, fences)
        for fence in fences:
            self.assertEqual(fence.count('worktree_snap.py" collect'), 1)
            self.assertIn('--state "$STATE_FILE"', fence)
            self.assertIn('--root "$GREPO"', fence)
        self.assertNotIn("--range", fences[0])
        self.assertNotIn("--pr-head", fences[0])

    def test_persist_names_reviewed_tree(self):
        with open(PERSIST_MD, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn('"reviewed_tree"', text)
        self.assertIn("REVIEWED_TREE=", text)

    def test_schema_allows_reviewed_tree_as_optional_pass_key(self):
        with open(SCHEMA, encoding="utf-8") as fh:
            schema = json.load(fh)
        self.assertIn("reviewed_tree", schema["pass_optional"])
        self.assertNotIn("reviewed_tree", schema["pass_required"])

    def test_envelope_names_nearby_line_ranges(self):
        self.assertIn("`nearby_line_ranges`", tdr._collect_text())


if __name__ == "__main__":
    unittest.main()
