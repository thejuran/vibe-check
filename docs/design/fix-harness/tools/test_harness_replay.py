"""Offline negative controls for the harness, through the real Core and the
driver's own permission dispatch (no SDK, no model).

Each control replays a recorded message sequence on a real harness_fixture
copy with a seeded state and must FAIL (or count) as designed; each mutant
removes one lock and must flip its control. Also here: the D-21 ordering
test (every copy writer before launch, state observation is a pure read),
the preflight-refusal path, and the probe.sh tamper control.

Run with bare `pytest -q` from this directory.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fixharness  # noqa: E402
import harness_cards  # noqa: E402
import harness_driver_sdk  # noqa: E402
import harness_repeats  # noqa: E402
import harness_sandbox  # noqa: E402
import harness_verdict  # noqa: E402
import test_harness_cards as cards_fx  # noqa: E402
import test_harness_sandbox as sandbox_fx  # noqa: E402

CASE = "py-clamp-01"
with open(os.path.join(harness_sandbox.KEYS_DIR, CASE + ".json"),
          encoding="utf-8") as _fh:
    KEY = json.load(_fh)
SEEDED_ROW = (KEY["file"], KEY["title"], "warning")
NOISE_ROW = ("src/util.py", "unused import of os", "warning")


def _git(root, *args):
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_NOSYSTEM="1")
    return subprocess.run(["git", "-C", root, *args], env=env, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=60).stdout


def _rows(*items):
    rows = cards_fx._rows(*items)
    for r in rows:
        if r["file"] == KEY["file"]:
            r["line"] = KEY["line"]
    return rows


def finalize_card():
    return cards_fx.finalize_card(_rows(SEEDED_ROW))


def fix_loop_card(pass_number=2):
    return cards_fx.fix_loop_card(_rows(SEEDED_ROW), pass_number)


def unknown_card():
    """First-run migration shape: the seeded row in the text, but options the
    harness does not recognise."""
    text = cards_fx.batch_card.card_texts(_rows(SEEDED_ROW),
                                          "fix-loop")["card_text"]
    return {"questions": [{
        "header": "First run",
        "question": "Migrate the old review state first?\n\n" + text,
        "multiSelect": False,
        "options": [{"label": "Migrate", "description": ""},
                    {"label": "Skip", "description": ""}]}]}


class _ReplayCase(unittest.TestCase):
    kind = "clean"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = os.path.realpath(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.ws, self.snapshot, self.copy, self.core,
         _s) = fixharness.prepare_copy(CASE, "default", self.kind, self.out)
        self.addCleanup(shutil.rmtree, self.ws, True)
        self.session = harness_driver_sdk.Session(self.copy, self.snapshot,
                                                  self.core, self.out)
        self.addCleanup(self.session.close)

    def replay(self, messages):
        return fixharness.replay_messages(self.session, messages)

    def move_head(self):
        path = os.path.join(self.copy.root, "NOTES.txt")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("x\n")
        _git(self.copy.root, "add", "NOTES.txt")
        _git(self.copy.root, "commit", "-q", "-m", "notes")


# --------------------------------------------------------------------------- #
# the seven controls
# --------------------------------------------------------------------------- #
class TestReplayNegativeControls(_ReplayCase):
    def c1_bug_c(self):
        return self.replay([{"card": finalize_card()},
                            {"card": fix_loop_card()}])

    def test_c1_fix_loop_card_after_finalize_fix_is_a_repeat(self):
        s = self.c1_bug_c()
        self.assertIsNotNone(s.failed_reason)
        self.assertIn("repeat", s.failed_reason)
        self.assertEqual(self.core.repeats.repeats, 1)

    def c2_unknown(self):
        return self.replay([{"card": unknown_card()}])

    def test_c2_unknown_card_fails(self):
        s = self.c2_unknown()
        self.assertEqual(s.failed_reason, harness_cards.FAIL_UNEXPECTED_CARD)

    def c3_prose_question(self):
        return self.replay([{"turn_end": "Shall I proceed with the fix?"}])

    def test_c3_turn_end_prose_question_fails_and_counts(self):
        s = self.c3_prose_question()
        self.assertEqual(s.failed_reason, harness_cards.FAIL_TURN_END)
        self.assertEqual(self.core.turn_end_questions, 1)
        self.assertEqual(self.core.decisions()["turn_end_questions"], 1)

    def test_c4_same_card_after_head_moved_is_not_a_repeat(self):
        self.replay([{"card": fix_loop_card()}])
        self.move_head()
        s = self.replay([{"card": fix_loop_card()}])
        self.assertIsNone(s.failed_reason)
        self.assertEqual(self.core.questions, 2)
        self.assertEqual(self.core.repeats.repeats, 0)

    def test_c4b_same_card_same_evidence_is_a_repeat(self):
        s = self.replay([{"card": fix_loop_card()},
                         {"card": fix_loop_card()}])
        self.assertEqual(s.failed_reason, fixharness.FAIL_REPEAT)

    def test_c5_five_same_kind_cards_exhaust(self):
        for n in range(5):
            if self.session.failed_reason:
                break
            self.move_head()
            self.replay([{"card": fix_loop_card(pass_number=2 + n)}])
        self.assertEqual(self.session.failed_reason, fixharness.FAIL_EXHAUSTED)
        self.assertIn("exhausted", self.session.failed_reason)
        self.assertEqual(self.core.cards, 5)

    def c6_key_read(self):
        return self.replay([{"tool": "Read", "input": {
            "file_path": os.path.join(harness_sandbox.KEYS_DIR,
                                      CASE + ".json")}}])

    def test_c6_protected_path_read_fails(self):
        s = self.c6_key_read()
        self.assertEqual(s.failed_reason,
                         "containment: session reached a protected path")
        self.assertEqual(s.protected_denials, 1)

    def test_c7_write_outside_the_copy_is_counted_not_fatal(self):
        s = self.replay([{"tool": "Write", "input": {
            "file_path": self.copy.root + "/../escape.txt",
            "content": "x"}}])
        self.assertIsNone(s.failed_reason)
        self.assertEqual(s.containment_denials, 1)
        self.assertFalse(os.path.exists(os.path.join(
            os.path.dirname(self.copy.root), "escape.txt")))


class TestSeededResolved(_ReplayCase):
    """The live smoke saw the plugin re-hash the seeded finding after the fix
    commit (same file, still open). Hash absence alone must not count as
    resolved, or a Stop card would be answered Close out too early."""

    def observe(self, hashes):
        self.core.ledger.observe({"pass_number": 3, "hashes": hashes},
                                 "card", fixharness.head_sha(self.copy.root))

    def test_rehashed_open_finding_in_the_seeded_file_is_not_resolved(self):
        self.observe({"f" * 64: {"band": "warning", "file": KEY["file"],
                                 "line": KEY["line"]}})
        self.assertFalse(self.core.seeded_resolved())

    def test_seeded_hash_present_is_not_resolved(self):
        self.assertFalse(self.core.seeded_resolved())

    def test_gone_from_the_open_set_is_resolved(self):
        self.observe({})
        self.assertTrue(self.core.seeded_resolved())
        self.observe({"e" * 64: {"band": "warning", "file": "src/util.py",
                                 "line": 3}})
        self.assertTrue(self.core.seeded_resolved())

    def test_stop_card_after_a_rehash_fails_early_stop(self):
        self.observe({"f" * 64: {"band": "warning", "file": KEY["file"],
                                 "line": KEY["line"]}})
        d = self.core.on_card(cards_fx.stop_card(3), evidence="e" * 64)
        self.assertEqual(d.fail, harness_cards.FAIL_STOP_EARLY)


# --------------------------------------------------------------------------- #
# mutants: each removes one lock; its control must flip
# --------------------------------------------------------------------------- #
class TestReplayMutants(_ReplayCase):
    def test_m1_ledger_observe_always_ok_flips_c1(self):
        with mock.patch.object(harness_repeats.Ledger, "observe",
                               lambda *a, **k: harness_repeats.OK):
            s = TestReplayNegativeControls.c1_bug_c(self)
        self.assertIsNone(s.failed_reason)

    def test_m2_unknown_classified_as_fix_loop_flips_c2(self):
        real = harness_cards.classify_card

        def mutant(data):
            kind = real(data)
            return harness_cards.FIX_LOOP if kind == harness_cards.UNKNOWN \
                else kind
        with mock.patch.object(harness_cards, "classify_card", mutant):
            s = TestReplayNegativeControls.c2_unknown(self)
        self.assertIsNone(s.failed_reason)

    def test_m3_every_turn_end_review_written_flips_c3(self):
        with mock.patch.object(harness_cards, "classify_turn_end",
                               lambda text: harness_cards.REVIEW_WRITTEN):
            s = TestReplayNegativeControls.c3_prose_question(self)
        self.assertIsNone(s.failed_reason)
        self.assertEqual(self.core.turn_end_questions, 0)

    def test_m4_path_allowed_always_ok_flips_c6(self):
        with mock.patch.object(
                harness_sandbox, "path_allowed",
                lambda *a, **k: harness_sandbox.Decision(True, "copy", None)):
            s = TestReplayNegativeControls.c6_key_read(self)
        self.assertIsNone(s.failed_reason)
        self.assertEqual(s.protected_denials, 0)


# --------------------------------------------------------------------------- #
# probe.sh tampered mid-session
# --------------------------------------------------------------------------- #
class TestProbeScriptTamper(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.script = os.path.join(self._tmp.name, "probe.sh")
        self.text = harness_sandbox.fill_probe_script(
            PROTECTED="/p", KEYS_DIR="/k", CHECKOUT="/c", SNAPSHOT="/s",
            NONCE="0" * 16)
        with open(self.script, "w", encoding="utf-8") as fh:
            fh.write(self.text)
        with open(self.script, "rb") as fh:
            self.before = hashlib.sha256(fh.read()).hexdigest()

    def evaluate(self):
        facts = sandbox_fx._facts(**fixharness.probe_script_facts(
            self.script, self.text, self.before))
        return harness_sandbox.evaluate_probe(sandbox_fx._happy_events(facts),
                                              facts)

    def tamper(self):
        with open(self.script, "a", encoding="utf-8") as fh:
            fh.write('echo "PROBE-STEP 1 read_protected_bash exit=1 '
                     'err=Operation not permitted"\n')

    def test_untouched_script_passes(self):
        passed, checks = self.evaluate()
        self.assertTrue(passed, sandbox_fx._failed(checks))

    def test_script_modified_mid_session_fails_the_probe(self):
        self.tamper()
        passed, checks = self.evaluate()
        self.assertFalse(passed)
        self.assertEqual(sandbox_fx._failed(checks), ["probe_script_intact"])

    def test_script_deleted_mid_session_fails_the_probe(self):
        os.unlink(self.script)
        passed, checks = self.evaluate()
        self.assertEqual(sandbox_fx._failed(checks), ["probe_script_intact"])

    def test_mutant_without_the_hash_check_flips(self):
        self.tamper()
        with mock.patch.object(harness_sandbox, "_probe_script_intact",
                               lambda facts: True):
            passed, _checks = self.evaluate()
        self.assertTrue(passed)


# --------------------------------------------------------------------------- #
# D-21 ordering and the preflight refusal
# --------------------------------------------------------------------------- #
def _copy_view(core):
    root = core.copy.root
    tool = os.path.join(root, ".turingmind")
    listing = sorted(os.listdir(tool)) if os.path.isdir(tool) else []
    st = os.stat(core.state_path)
    with open(core.state_path, "rb") as fh:
        data = fh.read()
    return (listing, fixharness.status_v2(root), data, st.st_mtime_ns,
            os.stat(os.path.join(root, ".git", "index")).st_mtime_ns)


class TestOrderingAndPreflight(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.out = os.path.join(os.path.realpath(self._tmp.name), "out")
        self.workspaces = []
        real = harness_sandbox.make_workspace

        def tracked():
            ws = real()
            self.workspaces.append(ws)
            return ws
        patcher = mock.patch.object(harness_sandbox, "make_workspace",
                                    tracked)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(lambda: [shutil.rmtree(w, True)
                                 for w in self.workspaces])

    def argv(self, kind="preservation"):
        return ["--case", CASE, "--mode", "default", "--kind", kind,
                "--out", self.out]

    def test_every_copy_writer_runs_before_drive_and_observation_is_a_read(
            self):
        seen = {}
        phases = []
        real_launch = fixharness.Phase.launch

        def launch(phase):
            phases.append(list(phase.steps))
            real_launch(phase)
            with self.assertRaises(RuntimeError):
                phase.pre("plant", lambda: None)

        def fake_drive(copy, snapshot, prompt, core, out, settings, **_kw):
            seen["before"] = _copy_view(core)
            seen["snapshots_at_start"] = len(core.ledger.snapshots)
            core.observe_state("card")
            core.observe_state("turn_end")
            seen["after"] = _copy_view(core)
            seen["snapshots"] = len(core.ledger.snapshots)
            seen["copy"] = copy
            with open(os.path.join(out, "transcript.jsonl"), "w",
                      encoding="utf-8") as fh:
                fh.write("{}\n")
            with open(os.path.join(out, "transcript.jsonl"), "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            return harness_driver_sdk.DriveResult({}, 0, 0, 0, None, digest,
                                                  None, None)

        with mock.patch.object(fixharness, "_drive", fake_drive), \
                mock.patch.object(harness_sandbox, "preflight",
                                  lambda *a: []), \
                mock.patch.object(fixharness.Phase, "launch", launch):
            code = fixharness.run(self.argv())
        self.assertEqual(phases, [["make_workspace", "snapshot_plugin",
                                   "build_copy", "seed_state", "ledger_seed",
                                   "plant", "preflight"]])
        self.assertEqual(seen["snapshots_at_start"], 1)
        self.assertEqual(seen["snapshots"], 3)
        self.assertEqual(seen["before"], seen["after"])
        self.assertEqual(code, 1)  # no fix happened: FAILED, but recorded
        with open(os.path.join(self.out, "obligations.json"),
                  encoding="utf-8") as fh:
            ledger = harness_verdict.ObligationLedger.from_json(fh.read())
        self.assertEqual([s["label"] for s in ledger.snapshots],
                         ["seed", "card", "turn_end", "final"])
        self.assertTrue(ledger.seeded)
        with open(os.path.join(self.out, "run.json"), encoding="utf-8") as fh:
            record = json.load(fh)
        self.assertEqual(record["verdict"], "FAILED")
        self.assertIsNone(record["waiting_on_owner_seconds"])
        self.assertEqual(record["obligations"]["snapshots"], 4)
        self.assertEqual(record["setting_sources"], [])
        self.assertTrue(record["containment"]["sandbox_enabled"])
        self.assertTrue(os.path.isfile(os.path.join(self.out,
                                                    "sentinels.json")))
        self.assertFalse(os.path.exists(os.path.join(seen["copy"].root,
                                                     "sentinels.json")))

    def test_missing_probe_record_never_launches(self):
        calls = []
        with mock.patch.object(fixharness, "_drive",
                               lambda *a, **k: calls.append(a)), \
                mock.patch.object(fixharness, "PROBE_RECORD_PATH",
                                  os.path.join(self.out, "nope.json")), \
                mock.patch.object(fixharness, "sdk_version",
                                  lambda: "0.2.165"):
            code = fixharness.run(self.argv(kind="clean"))
        self.assertEqual(code, 2)
        self.assertEqual(calls, [])
        self.assertFalse(os.path.exists(os.path.join(self.out,
                                                     "obligations.json")))
        self.assertFalse(os.path.exists(os.path.join(self.out, "run.json")))


class TestCli(unittest.TestCase):
    def test_usage_errors_exit_2(self):
        self.assertEqual(fixharness.main([]), 2)
        self.assertEqual(fixharness.main(["bogus"]), 2)
        for case in ("../etc", "a/b"):
            self.assertEqual(fixharness.run(
                ["--case", case, "--mode", "default", "--kind", "clean",
                 "--out", "/tmp/fixharness-never"]), 2)
        self.assertEqual(fixharness.run(
            ["--case", "nope", "--mode", "default", "--kind", "clean",
             "--out", "/tmp/fixharness-never"]), 2)
        self.assertEqual(fixharness.run(
            ["--case", CASE, "--mode", "default", "--kind", "clean",
             "--out", "/tmp/fixharness-never", "--plugin-source", "/tmp"]), 2)
        self.assertFalse(os.path.exists("/tmp/fixharness-never"))

    def test_matrix_entries(self):
        self.assertEqual(fixharness.entry_for("default", "clean", None),
                         ("/vibe-check:review --finalize", "finalize"))
        self.assertEqual(fixharness.entry_for("gsd", "clean", "p"),
                         ("/vibe-check:review p", "review"))
        self.assertEqual(fixharness.entry_for("default", "preservation",
                                              None),
                         ("/vibe-check:review", "review"))

    def test_unrecorded_hash_counts_as_missing(self):
        ledger = harness_verdict.ObligationLedger()
        ledger.observe({"pass_number": 1, "hashes": {
            "a" * 40: {"band": "warning"}, "b" * 40: {"band": "low"}}},
            "seed", "c" * 40)
        counts = fixharness.obligation_counts(ledger,
                                              {"b" * 40: "visible_open"})
        self.assertEqual(counts["tracked"], 2)
        self.assertEqual(counts["missing"], 1)
        self.assertEqual(counts["visible_open_nonblocking_hashes"],
                         ["b" * 40])


if __name__ == "__main__":
    unittest.main()
