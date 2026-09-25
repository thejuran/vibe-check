"""test_tracecheck.py — the dynamic lazy-read detector, proven able to FAIL.

The restructure moves phase bodies into sub-files that the orchestrator reads
only when a phase fires. The new failure mode is silent: a spine step whose
Read instruction is ignored, so the phase runs from the model's memory of its
title and the report looks normal. tracecheck.py observes the run instead of
the repo: coverage is counted ONLY from Read tool_use events paired with a
non-error tool_result.

What these tests lock:

* An announcement is never evidence of a read, and a Read that FAILED (or was
  never answered) is not coverage.
* A phase omitted ENTIRELY is a failure, not an invisible absence — every mode
  path carries an expected phase sequence.
* The two negative controls are built by deleting entries from the SAME passing
  transcript, so they are the passing case minus exactly one thing. If either
  ever yields an empty reason list, the checker is not checking anything.
* Expectations are keyed by (batch, mode): batch 1 runs before phases/ exists,
  so a batch-1 trace checked against batch-3 expectations must fail — the batch
  dimension is load-bearing, not decoration.
* Reads of plugin files must resolve under the plugin root in use (the F2
  nested-read proof), and reasons never echo transcript content or foreign
  paths.
"""

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tracecheck  # noqa: E402

TRACECHECK_PY = os.path.join(HERE, "tracecheck.py")
EXPECT_PATH = os.path.join(HERE, "fixtures", "mode-path-expectations.json")
with open(EXPECT_PATH) as _fh:
    EXPECT = json.load(_fh)

MODES = {"review-plain", "review-all", "deep-plain", "deep-all", "finalize", "fix-loop",
         "fix-agent"}
ROOT = "/snap/b3/plugins/vibe-check"
_IDS = [0]


def expectation(batch, mode):
    return EXPECT["batches"][str(batch)][mode]


def _as_list(v):
    return v if isinstance(v, list) else [v]


class Builder:
    """Builds stream-json records: assistant tool_use/text, user tool_result."""

    def __init__(self, root=ROOT):
        self.root = root
        self.records = []

    @staticmethod
    def _id():
        _IDS[0] += 1
        return "toolu_%05d" % _IDS[0]

    def read(self, rel, ok=True, parent=None, content="file body", absolute=None):
        tid = self._id()
        path = absolute or os.path.join(self.root, rel)
        self.records.append({"type": "assistant", "parent_tool_use_id": parent,
                             "message": {"role": "assistant", "content": [
                                 {"type": "tool_use", "id": tid, "name": "Read",
                                  "input": {"file_path": path}}]}})
        res = {"type": "tool_result", "tool_use_id": tid, "content": content}
        if not ok:
            res["is_error"] = True
            res["content"] = "File does not exist."
        self.records.append({"type": "user", "parent_tool_use_id": parent,
                             "message": {"role": "user", "content": [res]}})
        return tid

    def say(self, text, parent=None):
        self.records.append({"type": "assistant", "parent_tool_use_id": parent,
                             "message": {"role": "assistant",
                                         "content": [{"type": "text", "text": text}]}})

    def dispatch(self, agent, children=1, toolless=False):
        tid = self._id()
        self.records.append({"type": "assistant", "parent_tool_use_id": None,
                             "message": {"role": "assistant", "content": [
                                 {"type": "tool_use", "id": tid, "name": "Task",
                                  "input": {"subagent_type": agent, "prompt": "x"}}]}})
        if toolless:
            # A subagent that answers from its prompt alone: stream-json shows exactly
            # one child record, the user-role prompt delivery (observed 2026-09-24).
            self.records.append({"type": "user", "parent_tool_use_id": tid,
                                 "message": {"role": "user", "content": [
                                     {"type": "text", "text": "You are the agent."}]}})
        for _ in range(children):
            self.read("src/app.py", parent=tid, absolute="/fixture/src/app.py")
        self.records.append({"type": "user", "parent_tool_use_id": None,
                             "message": {"role": "user", "content": [
                                 {"type": "tool_result", "tool_use_id": tid,
                                  "content": "done"}]}})
        return tid


def passing_builder(batch, mode, root=ROOT):
    """The passing transcript for (batch, mode), derived from the data itself."""
    exp = expectation(batch, mode)
    b = Builder(root)
    # Every real run answers at least one orchestrator tool call before any phase
    # evidence (scope resolution reads the repo); a repo file is never a provenance
    # question, so this changes nothing for the plugin-read checks or the controls.
    b.read("src/app.py", absolute="/fixture/src/app.py")
    for rel in exp["always_read"]:
        b.read(rel)
    for rel in exp["required_reads"]:
        b.read(rel)
    for label in exp["expected_phases"]:
        for rel in _as_list(exp["mandatory_reads"].get(label, [])):
            b.read(rel)
        b.say("✓ Phase %s — step" % label)
        # Review agents are dispatched in Phase 2; the fix agent only in Phase 5.
        for agent in exp["required_dispatches"]:
            if (agent == "fix") == (label == "5"):
                b.dispatch("vibe-check:" + agent)
    return b


def announcement_rule(batch, mode):
    """A copy of (batch, mode) under the DEFAULT announcement rule with no positive
    tool-event requirements — for tests about announcement sequencing alone."""
    exp = dict(expectation(batch, mode))
    exp.pop("sequence_evidence", None)
    exp["required_dispatches"] = []
    return exp


def is_read_of(rec, rel):
    for c in rec["message"]["content"]:
        if c.get("type") == "tool_use" and c["input"].get("file_path", "").endswith("/" + rel):
            return True
    return False


def without_read(records, rel):
    """The passing records minus one read's tool_use AND its tool_result."""
    ids = {c["id"] for r in records for c in r["message"]["content"]
           if c.get("type") == "tool_use" and is_read_of(r, rel)}
    assert ids, "fixture does not contain a read of %s" % rel
    return [r for r in records if not any(
        c.get("id") in ids or c.get("tool_use_id") in ids for c in r["message"]["content"])]


def without_announcement(records, label):
    text = "✓ Phase %s —" % label
    kept = [r for r in records if not any(
        c.get("type") == "text" and c["text"].startswith(text) for c in r["message"]["content"])]
    assert len(kept) == len(records) - 1, "fixture does not announce %s exactly once" % label
    return kept


class TraceCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmp)

    def write(self, records, name="trace.jsonl", raw_lines=()):
        path = os.path.join(self._tmp, name)
        with open(path, "w") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")
            for line in raw_lines:
                fh.write(line + "\n")
        return path

    def check(self, records, batch, mode, root=ROOT, raw_lines=()):
        evts = tracecheck.events(self.write(records, raw_lines=raw_lines))
        return tracecheck.check(evts, expectation(batch, mode), root)

    def cli(self, *argv):
        return subprocess.run([sys.executable, TRACECHECK_PY, *argv], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, timeout=30)


class TestParser(TraceCase):
    def test_failed_read_is_not_coverage(self):
        b = Builder()
        b.read("phases/review/06-config.md", ok=True)
        b.read("phases/review/07-first-run.md", ok=False)
        evts = tracecheck.events(self.write(b.records))
        reads = tracecheck.successful_reads(evts)
        self.assertEqual([p for _, p in reads], [ROOT + "/phases/review/06-config.md"])
        self.assertEqual(len(tracecheck.read_attempts(evts)), 2)

    def test_unpaired_tool_use_is_not_coverage_and_is_reported(self):
        b = passing_builder(3, "review-plain")
        b.records.append({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "toolu_dangling", "name": "Read",
             "input": {"file_path": ROOT + "/phases/review/50-fix-loop.md"}}]}})
        evts = tracecheck.events(self.write(b.records))
        paths = [p for _, p in tracecheck.successful_reads(evts)]
        self.assertNotIn(ROOT + "/phases/review/50-fix-loop.md", paths)
        reasons = tracecheck.check(evts, expectation(3, "review-plain"), ROOT)
        self.assertIn("unpaired tool_use with no tool_result: 1", reasons)

    def test_malformed_lines_are_counted_not_silently_skipped(self):
        b = passing_builder(3, "review-plain")
        reasons = self.check(b.records, 3, "review-plain", raw_lines=["{truncated", "[1, 2]"])
        self.assertEqual(reasons, ["malformed transcript lines: 2"])

    def test_announcement_labels(self):
        b = Builder()
        b.say("✓ Phase 0.6 — Resolve config\n⊘ Phase 1.5 — Intent (skipped: x)")
        b.say("✓ Phase 2 (chunk 1/3) — Dispatching 3 agents\n✓ Phase 2c — Codex")
        b.say("I will now do ✓ Phase 9 — mid-line mentions are not announcements")
        b.say("✓ Phase 3 — child", parent="toolu_x")
        got = [(lbl, mark) for _, lbl, mark in tracecheck.announcements(tracecheck.events(
            self.write(b.records)))]
        self.assertEqual(got, [("0.6", "✓"), ("1.5", "⊘"), ("2", "✓"),
                               ("2c", "✓")])


class TestPassingAndControls(TraceCase):
    def test_every_passing_transcript_is_clean(self):
        for batch in ("1", "2", "3"):
            for mode in sorted(MODES):
                with self.subTest(batch=batch, mode=mode):
                    self.assertEqual(self.check(passing_builder(batch, mode).records,
                                                batch, mode), [])

    def test_negative_control_missing_read(self):
        """If this test ever passes with an empty reason list, the checker is not checking
        anything: it is the passing transcript minus exactly one mandatory read."""
        records = without_read(passing_builder(3, "review-plain").records,
                               "phases/review/06-config.md")
        reasons = self.check(records, 3, "review-plain")
        self.assertNotEqual(reasons, [])
        self.assertEqual(reasons, ["phase executed without a preceding successful read: 0.6"])

    def test_negative_control_phase_omitted(self):
        """The same passing transcript with one phase removed ENTIRELY — its read and its
        announcement. Without the expected sequence this absence would be invisible."""
        records = without_read(passing_builder(3, "review-plain").records,
                               "phases/review/06-config.md")
        records = without_announcement(records, "0.6")
        self.assertEqual(self.check(records, 3, "review-plain"),
                         ["phase absent from run: 0.6"])

    def test_read_after_announcement_fails(self):
        b = Builder()
        for rel in expectation(3, "review-plain")["always_read"]:
            b.read(rel)
        exp = expectation(3, "review-plain")
        for label in exp["expected_phases"]:
            if label != "0.6":
                b.read(exp["mandatory_reads"][label])
            b.say("✓ Phase %s — step" % label)
            if label == "0.6":
                b.read(exp["mandatory_reads"][label])
        self.assertEqual(self.check(b.records, 3, "review-plain"),
                         ["phase executed without a preceding successful read: 0.6"])

    def test_child_read_does_not_satisfy_orchestrator_read(self):
        records = without_read(passing_builder(3, "review-plain").records,
                               "phases/review/10-triage.md")
        child = Builder()
        child.read("phases/review/10-triage.md", parent="toolu_sub")
        at = next(i for i, r in enumerate(records) if any(
            c.get("text", "").startswith("\u2713 Phase 1 \u2014") for c in r["message"]["content"]))
        records[at:at] = child.records
        self.assertEqual(self.check(records, 3, "review-plain"),
                         ["phase executed without a preceding successful read: 1"])

    def test_batch1_trace_fails_batch3_expectations(self):
        """FL-08: the batch dimension is load-bearing."""
        records = passing_builder(1, "review-plain").records
        self.assertEqual(self.check(records, 1, "review-plain"), [])
        reasons = self.check(records, 3, "review-plain")
        self.assertIn("phase executed without a preceding successful read: 0.6", reasons)
        self.assertIn("always-read file not read before the first phase: 00-contract.md", reasons)


class TestSequence(TraceCase):
    def test_unexpected_phase_detected(self):
        b = passing_builder(3, "review-plain")
        b.say("✓ Phase 0.2 — chunk plan")
        self.assertEqual(self.check(b.records, 3, "review-plain"),
                         ["phase ran on a mode path that must skip it: 0.2"])
        b2 = passing_builder(3, "finalize")
        b2.say("✓ Phase 1 — Triage")
        self.assertEqual(self.check(b2.records, 3, "finalize"),
                         ["unexpected phase in run: 1"])

    def test_optional_phase_may_be_skipped_or_absent(self):
        b = passing_builder(3, "review-plain")
        b.say("⊘ Phase 5 — Fix loop (skipped: non-interactive)")
        self.assertEqual(self.check(b.records, 3, "review-plain"), [])

    def test_required_phase_announced_only_as_skipped_fails(self):
        records = without_announcement(passing_builder(3, "review-plain").records, "3")
        b = Builder()
        b.records = records
        b.say("⊘ Phase 3 — Collect (skipped: nothing)")
        self.assertIn("phase announced as skipped on a mode path that must run it: 3",
                      self.check(b.records, 3, "review-plain"))

    def test_phase_order_mismatch_detected(self):
        b = Builder()
        exp = announcement_rule(1, "review-plain")
        seq = list(exp["expected_phases"])
        seq[4], seq[5] = seq[5], seq[4]
        for label in seq:
            b.say("✓ Phase %s — step" % label)
        evts = tracecheck.events(self.write(b.records))
        self.assertEqual(tracecheck.check(evts, exp, ROOT),
                         ["phase order differs from the mode path at: %s" % seq[4]])

    def test_always_read_must_precede_first_announcement(self):
        records = without_read(passing_builder(3, "review-plain").records,
                               "phases/shared/01-bootstrap.md")
        b = Builder()
        b.records = records
        b.read("phases/shared/01-bootstrap.md")
        self.assertEqual(self.check(b.records, 3, "review-plain"),
                         ["always-read file not read before the first phase: 01-bootstrap.md"])

    def test_empty_transcript_fails(self):
        evts = tracecheck.events(self.write([]))
        reasons = tracecheck.check(evts, announcement_rule(1, "review-plain"), ROOT)
        self.assertIn("no phase announcements in transcript", reasons)
        self.assertIn("phase absent from run: 0", reasons)

    def test_empty_transcript_fails_every_batch1_mode(self):
        """Batch 1 opts out of announcement evidence; nothing may still pass."""
        for mode in sorted(MODES):
            with self.subTest(mode=mode):
                reasons = self.check([], 1, mode)
                self.assertNotEqual(reasons, [])
                self.assertIn("no answered orchestrator tool call in transcript", reasons)


class TestReads(TraceCase):
    def test_forbidden_read_detected(self):
        b = passing_builder(3, "review-plain")
        b.read("phases/review/02-chunk-plan.md")
        self.assertEqual(self.check(b.records, 3, "review-plain"),
                         ["file read on a mode path that must not load it: 02-chunk-plan.md"])

    def test_provenance_outside_plugin_root(self):
        foreign = "/somewhere/else/plugins/vibe-check/phases/review/06-config.md"
        b = passing_builder(3, "review-plain")
        b.read("x", absolute=foreign)
        reasons = self.check(b.records, 3, "review-plain")
        self.assertEqual(reasons, ["read from outside the plugin root: 06-config.md"])
        self.assertFalse(any("somewhere" in r for r in reasons))

    def test_mandatory_read_outside_root_is_not_coverage(self):
        foreign = "/somewhere/else/plugins/vibe-check"
        records = passing_builder(3, "review-plain", root=foreign).records
        reasons = self.check(records, 3, "review-plain", root="/other/plugins/vibe-check")
        self.assertIn("phase executed without a preceding successful read: 0.6", reasons)
        self.assertIn("read from outside the plugin root: 06-config.md", reasons)

    def test_installed_cache_read_is_flagged(self):
        b = passing_builder(1, "deep-plain")
        b.read("x", absolute="/Users/u/.claude/plugins/cache/thejuran/vibe-check/2.9.0/"
                             "templates/review-md-schema.md")
        self.assertEqual(self.check(b.records, 1, "deep-plain"),
                         ["read from outside the plugin root: review-md-schema.md"])

    def test_repo_file_read_is_not_a_provenance_question(self):
        b = passing_builder(3, "review-plain")
        b.read("x", absolute="/fixture/plugins/vibe-check/scripts/guard.py")
        b.read("x", absolute="/fixture/src/app.py")
        self.assertEqual(self.check(b.records, 3, "review-plain"), [])

    def test_required_read_missing(self):
        records = without_read(passing_builder(3, "finalize").records,
                               "phases/shared/90-finalize.md")
        self.assertEqual(self.check(records, 3, "finalize"),
                         ["required file never successfully read: 90-finalize.md"])


class TestDispatch(TraceCase):
    def test_fix_loop_body_reached_needs_no_dispatch(self):
        self.assertEqual(self.check(passing_builder(3, "fix-loop").records, 3, "fix-loop"), [])

    def test_required_dispatch_missing(self):
        records = passing_builder(3, "fix-loop").records
        self.assertEqual(self.check(records, 3, "fix-agent"),
                         ["required agent never dispatched: fix"])

    def test_toolless_subagent_still_counts_as_a_child(self):
        """A subagent that never calls a tool leaves only a user-role prompt record under
        its dispatch id in a -p trace; that record IS the child event (triage, bugs, impact
        and test-sufficiency all ran tool-less against the batch-1 fixtures)."""
        b = passing_builder(3, "fix-agent")
        b.records = [r for r in b.records if r.get("parent_tool_use_id") is None
                     or not any(c.get("type") in ("tool_use", "tool_result")
                                for c in r["message"]["content"])]
        b.dispatch("vibe-check:fix", children=0, toolless=True)
        self.assertNotIn("dispatched agent has no child events: fix",
                         self.check(b.records, 3, "fix-agent"))

    def test_dispatch_without_child_events_fails(self):
        b = Builder()
        b.records = passing_builder(3, "fix-loop").records
        b.dispatch("vibe-check:fix", children=0)
        self.assertEqual(self.check(b.records, 3, "fix-agent"),
                         ["dispatched agent has no child events: fix"])

    def test_session_export_subagent_dir_links_children(self):
        records = passing_builder(3, "fix-loop").records
        records.append({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "toolu_fix", "name": "Agent",
             "input": {"subagent_type": "vibe-check:fix"}}]}})
        records.append({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "toolu_fix", "content": "ok"}]}})
        main = self.write(records)
        sub = os.path.join(self._tmp, "subagents")
        os.makedirs(sub)
        with open(os.path.join(sub, "agent-a1.meta.json"), "w") as fh:
            json.dump({"agentType": "vibe-check:fix", "toolUseId": "toolu_fix"}, fh)
        child = Builder()
        child.read("x", absolute="/fixture/src/app.py")
        with open(os.path.join(sub, "agent-a1.jsonl"), "w") as fh:
            for r in child.records:
                r.pop("parent_tool_use_id")
                fh.write(json.dumps(r) + "\n")
        self.assertIn("dispatched agent has no child events: fix", tracecheck.check(
            tracecheck.events(main), expectation(3, "fix-agent"), ROOT))
        self.assertEqual(tracecheck.check(tracecheck.events(main, sub),
                                          expectation(3, "fix-agent"), ROOT), [])


class TestCli(TraceCase):
    def _clean(self):
        return self.write(passing_builder(3, "review-plain").records)

    def test_clean_exits_zero_with_empty_stderr(self):
        p = self.cli("--trace", self._clean(), "--mode", "review-plain", "--batch", "3",
                     "--plugin-root", ROOT)
        self.assertEqual((p.returncode, p.stderr), (0, ""))

    def test_violation_exits_one(self):
        records = without_read(passing_builder(3, "review-plain").records,
                               "phases/review/06-config.md")
        p = self.cli("--trace", self.write(records), "--mode", "review-plain", "--batch", "3",
                     "--plugin-root", ROOT)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(p.stderr.strip().splitlines(),
                         ["phase executed without a preceding successful read: 0.6"])

    def test_usage_errors_exit_two(self):
        t = self._clean()
        base = ["--plugin-root", ROOT]
        cases = {
            "missing trace": ["--mode", "review-plain", "--batch", "3"] + base,
            "unreadable trace": ["--trace", os.path.join(self._tmp, "nope.jsonl"),
                                 "--mode", "review-plain", "--batch", "3"] + base,
            "unknown mode": ["--trace", t, "--mode", "review-bogus", "--batch", "3"] + base,
            "unknown batch": ["--trace", t, "--mode", "review-plain", "--batch", "9"] + base,
            "missing batch": ["--trace", t, "--mode", "review-plain"] + base,
            "missing plugin root": ["--trace", t, "--mode", "review-plain", "--batch", "3"],
            "bad subagents dir": ["--trace", t, "--mode", "review-plain", "--batch", "3",
                                  "--subagents", os.path.join(self._tmp, "none")] + base,
        }
        for name, argv in cases.items():
            with self.subTest(case=name):
                self.assertEqual(self.cli(*argv).returncode, 2)

    def test_never_echo(self):
        sentinel = "SENTINEL-7f3a9c"
        b = passing_builder(3, "review-plain")
        b.read("phases/review/06-config.md", content="secret " + sentinel)
        b.read("x", absolute="/%s/plugins/vibe-check/phases/review/10-triage.md" % sentinel)
        b.say("✓ Phase 7 — %s" % sentinel)
        p = self.cli("--trace", self.write(b.records), "--mode", "review-plain", "--batch", "3",
                     "--plugin-root", ROOT)
        self.assertEqual(p.returncode, 1)
        self.assertNotIn(sentinel, p.stdout + p.stderr)


class TestExpectationsData(unittest.TestCase):
    def test_expectations_complete(self):
        self.assertIn("_comment", EXPECT)
        self.assertEqual(set(EXPECT["batches"]), {"1", "2", "3"})
        for batch, modes in EXPECT["batches"].items():
            self.assertEqual(set(modes), MODES, batch)
            for mode, exp in modes.items():
                with self.subTest(batch=batch, mode=mode):
                    for key in ("expected_phases", "optional_phases", "skip_only_phases",
                                "mandatory_reads",
                                "always_read", "required_reads", "forbidden_reads",
                                "required_dispatches", "noninteractive", "flag_reason"):
                        self.assertIn(key, exp)
                    rels = [r for v in exp["mandatory_reads"].values() for r in _as_list(v)]
                    rels += exp["always_read"] + exp["required_reads"] + exp["forbidden_reads"]
                    for rel in rels:
                        self.assertRegex(rel, r"^(phases/[a-z-]+|commands|templates)/[0-9a-z.-]+"
                                              r"\.md$")
                    if batch != "1" and mode.startswith("review"):
                        for label, v in exp["mandatory_reads"].items():
                            for rel in _as_list(v):
                                self.assertTrue(rel.startswith("phases/"), rel)
                    groups = [set(exp[k]) for k in ("expected_phases", "optional_phases",
                                                    "skip_only_phases")]
                    self.assertFalse(groups[0] & groups[1] or groups[0] & groups[2]
                                     or groups[1] & groups[2])

    def test_gated_modes_are_interactive(self):
        """F3d + FL-09a: --all, deep --all and the fix loop cannot use the flag."""
        for batch in EXPECT["batches"].values():
            for mode in ("review-all", "deep-all", "fix-loop", "fix-agent"):
                self.assertFalse(batch[mode]["noninteractive"], mode)
            self.assertEqual(batch["fix-agent"]["required_dispatches"], ["fix"])
            self.assertEqual(batch["fix-loop"]["required_dispatches"], [])


class TestSequenceEvidenceNone(TraceCase):
    """Batch 1 is the monolith, and its first live traces (2026-09-24) showed that it does
    not announce phases the way review.md:19 promises: early phases run with no `✓` text
    line, or the line is echoed inside a Bash command. On that layout an announcement is
    not evidence of anything, so batch-1 entries carry `sequence_evidence: "none"`. Under
    that rule the checker still holds reads, provenance, forbidden reads and dispatches;
    it only stops deriving anything from announcement text. A mandatory read that had a
    phase anchor becomes a read that must succeed SOMEWHERE in the transcript."""

    def exp(self, **over):
        base = {"expected_phases": ["0", "2"], "optional_phases": [],
                "skip_only_phases": ["5"], "mandatory_reads": {"0": "commands/review.md"},
                "always_read": [], "required_reads": [],
                "forbidden_reads": ["phases/review/06-config.md"],
                "required_dispatches": [], "sequence_evidence": "none"}
        base.update(over)
        return base

    def run_check(self, records, exp, root=ROOT):
        return tracecheck.check(tracecheck.events(self.write(records)), exp, root)

    def test_silent_run_with_its_reads_is_clean(self):
        b = Builder()
        b.read("commands/review.md")            # no announcement anywhere
        self.assertEqual(self.run_check(b.records, self.exp()), [])

    def test_announcement_text_is_neither_required_nor_trusted(self):
        b = Builder()
        b.read("commands/review.md")
        b.say("✓ Phase 2 — step")
        b.say("✓ Phase 9 — a label no expectation names")
        b.say("✓ Phase 5 — a skip-only phase announced as run")
        self.assertEqual(self.run_check(b.records, self.exp()), [])

    def test_announced_but_never_read_fails_as_a_required_read(self):
        b = Builder()
        b.read("src/app.py", absolute="/fixture/src/app.py")   # unrelated activity
        b.say("✓ Phase 0 — step")               # the announcement proves nothing
        self.assertEqual(self.run_check(b.records, self.exp()),
                         ["required file never successfully read: review.md"])

    def test_failed_mandatory_read_is_not_coverage(self):
        b = Builder()
        b.read("src/app.py", absolute="/fixture/src/app.py")   # unrelated activity
        b.read("commands/review.md", ok=False)
        self.assertEqual(self.run_check(b.records, self.exp()),
                         ["required file never successfully read: review.md"])

    def test_child_read_does_not_satisfy_the_orchestrator(self):
        b = Builder()
        tid = b.dispatch("vibe-check:bugs")
        b.read("commands/review.md", parent=tid)
        self.assertIn("required file never successfully read: review.md",
                      self.run_check(b.records, self.exp()))

    def test_provenance_still_enforced(self):
        b = Builder()
        b.read("src/app.py", absolute="/fixture/src/app.py")   # unrelated activity
        b.read("commands/review.md",
               absolute="/u/.claude/plugins/cache/thejuran/vibe-check/2.9.0/commands/review.md")
        reasons = self.run_check(b.records, self.exp())
        self.assertIn("read from outside the plugin root: review.md", reasons)
        self.assertIn("required file never successfully read: review.md", reasons)

    def test_forbidden_read_still_enforced(self):
        b = Builder()
        b.read("commands/review.md")
        b.read("phases/review/06-config.md")
        self.assertEqual(self.run_check(b.records, self.exp()),
                         ["file read on a mode path that must not load it: 06-config.md"])

    def test_required_dispatch_still_enforced(self):
        b = Builder()
        b.read("commands/review.md")
        self.assertEqual(self.run_check(b.records, self.exp(required_dispatches=["fix"])),
                         ["required agent never dispatched: fix"])

    def test_always_read_must_still_happen(self):
        b = Builder()
        b.read("src/app.py", absolute="/fixture/src/app.py")   # unrelated activity
        self.assertEqual(self.run_check(b.records, self.exp(always_read=["commands/review.md"],
                                                             mandatory_reads={})),
                         ["always-read file not read before the first phase: review.md"])

    def test_negative_control_batch1_deep_plain(self):
        """The real batch-1 shape: the passing deep-plain transcript minus its one mandatory
        read must FAIL. If this ever yields [] the batch-1 rule checks nothing."""
        records = without_read(passing_builder(1, "deep-plain").records, "commands/review.md")
        reasons = self.check(records, 1, "deep-plain")
        self.assertNotEqual(reasons, [])
        self.assertEqual(reasons, ["required file never successfully read: review.md"])

    def test_default_rule_is_unchanged_without_the_key(self):
        base = self.exp()
        del base["sequence_evidence"]
        b = Builder()
        b.read("commands/review.md")            # silent run under the default rule
        reasons = self.run_check(b.records, base)
        self.assertIn("no phase announcements in transcript", reasons)
        self.assertIn("phase absent from run: 0", reasons)

    def test_activity_floor_fires_only_when_nothing_was_answered(self):
        b = Builder()
        b.read("commands/review.md", ok=False)  # attempted, but never answered cleanly
        self.assertIn("no answered orchestrator tool call in transcript",
                      self.run_check(b.records, self.exp()))
        b2 = Builder()
        b2.read("src/app.py", absolute="/fixture/src/app.py")
        self.assertNotIn("no answered orchestrator tool call in transcript",
                         self.run_check(b2.records, self.exp()))

    def test_value_is_validated(self):
        self.assertTrue(tracecheck._valid_entry(self.exp()))
        self.assertTrue(tracecheck._valid_entry(self.exp(sequence_evidence="announcements")))
        base = self.exp()
        del base["sequence_evidence"]
        self.assertTrue(tracecheck._valid_entry(base))
        self.assertFalse(tracecheck._valid_entry(self.exp(sequence_evidence="maybe")))
        self.assertFalse(tracecheck._valid_entry(self.exp(sequence_evidence=None)))

    def test_only_batch1_opts_out_of_sequence_evidence(self):
        for mode, exp in EXPECT["batches"]["1"].items():
            with self.subTest(batch="1", mode=mode):
                self.assertEqual(exp.get("sequence_evidence"), "none")
        for batch in ("2", "3"):
            for mode, exp in EXPECT["batches"][batch].items():
                with self.subTest(batch=batch, mode=mode):
                    self.assertNotEqual(exp.get("sequence_evidence"), "none")


class TestImportSet(unittest.TestCase):
    ALLOWED = {"argparse", "json", "os", "re", "sys"}

    def test_imports_are_exactly_the_allowed_set(self):
        with open(TRACECHECK_PY) as fh:
            tree = ast.parse(fh.read())
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
        self.assertEqual(found, self.ALLOWED)
        self.assertNotIn("subprocess", found)


if __name__ == "__main__":
    unittest.main()
