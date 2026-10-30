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
import subprocess
import sys
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import carry_state  # noqa: E402
import gitfixture  # noqa: E402
import gitsnap  # noqa: E402
import score  # noqa: E402
import state_shape  # noqa: E402
import test_decision_continuity as tdc  # noqa: E402
import test_diff_ranges as tdr  # noqa: E402

F = tdc.F
PLUGIN_ROOT = os.path.dirname(SCRIPTS_DIR)
PERSIST_MD = os.path.join(PLUGIN_ROOT, "phases", "review", "45-persist.md")
SCHEMA = os.path.join(SCRIPTS_DIR, "fixtures", "future-schema.json")
COLLECT_CALL = 'worktree_snap.py" collect'
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


class _Chain(tdc._RealChain):
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

    def collect(self, state_path):
        proc = _bash(self.collect_fence, self.repo.repo,
                     {"STATE_FILE": state_path})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return (_printed(proc.stdout, "REVIEWED_TREE"),
                _printed(proc.stdout, "NEARBY_LINE_RANGES"))

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
        a = lambda L: tdc.fresh("bugs", 10, L, tdc.TITLE_A, conf=tdc.STABLE_CONF)
        b = lambda L: tdc.fresh("security", 12, L, "Injection at B", conf=95,
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


class TestProse(unittest.TestCase):

    def test_collect_fence_is_one_call_with_state_file(self):
        fence = tdr._fence_holding(tdr._collect_text(), COLLECT_CALL)
        self.assertIsNotNone(fence)
        self.assertIn('--state "$STATE_FILE"', fence)
        self.assertIn('--root "$GREPO"', fence)

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
