"""test_carry_state.py — the carry-forward state helper as executable decisions.

`carry_state.py` is the one deterministic helper behind every carry-forward
state read and write:

* `finalize-counts` turns the parsed state into the two counts the UNCHANGED
  `finalize_gate.py` consumes. A finding is closed iff it carries an owner
  decision (new `decisions` record OR legacy `medium_acknowledgments` entry), or
  a fix-agent `obsolete` verdict from the latest pass whose `verified_blob` still
  equals HEAD's blob for that file. Nothing else closes a finding: not age, not a
  pass count, not a min_confidence/threshold change.
* `pending` answers "unchanged since pass N, decision pending" from the state
  file alone.
* `record-decisions` / `record-fix-verdicts` are the only write paths for the
  `decisions` and `fix_verdicts` root families, and never touch `passes` or
  `medium_acknowledgments`.

The old prose rule (90-finalize.md) these counts must reproduce on legacy
medium-only states:

  outstanding_cw        = last pass's findings with band in {critical, warning}
                          AND status != fixed-since-last
  unacknowledged_medium = last pass's findings with band == medium AND no entry
                          in medium_acknowledgments
"""

import ast
import copy
import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

# Make `import carry_state` resolve when unittest discovery runs from root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import carry_state  # noqa: E402  (sibling module under test)
import finalize_gate  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CARRY_STATE_PY = os.path.join(HERE, "carry_state.py")
FIXTURE = os.path.join(HERE, "fixtures", "phase45-loop-state.json")

ARCH_HASH = "5e78e90a6bf05e6a409b4aa3271e5e4df072735a074a9947a0a766a3d794af67"
BUGS_HASH = "7479a9b5fd5b36bce327aea4d49db8dcbe4193208c2b2ca3f1d3ac98368e6644"
ARCH_FILE = "plugins/vibe-check/phases/deep-review/01d-coverage.md"

HA = "a" * 64
HB = "b" * 64
F = "src/app.py"


def load_fixture():
    with open(FIXTURE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def mk_finding(band, status, h, snapshot=None, file=F, line=10, **extra):
    f = {
        "id": "x-" + h[:6],
        "file": file,
        "line": line,
        "title": "t " + h[:6],
        "agent": "bugs",
        "band": band,
        "status": status,
        "stable_hash": h,
    }
    if snapshot is not None:
        f["snapshot"] = snapshot
    f.update(extra)
    return f


def mk_pass(n, findings):
    return {"pass_number": n, "head_sha": "h%d" % n, "diff_range": "a..b",
            "findings": findings}


def mk_state(passes, **roots):
    s = {"medium_acknowledgments": {}, "passes": passes}
    s.update(roots)
    return s


def snap(at_pass, file=F, line=10, band="warning"):
    return {"at_pass": at_pass, "file": file, "line": line,
            "canonical_line_content": "x = 1", "band": band}


def member_ref(file=F, line=10, title="m"):
    return {"file": file, "line": line, "title": title, "agent": "bugs",
            "severity": "warning"}


def ba_state(row_band="warning", a_band="warning", a_snapshot=None):
    """One last-pass row B (hash HB, file F) carrying A's absorbed obligation."""
    a_member = member_ref(line=11, title="A")
    a_member["obligation"] = {
        "stable_hash": HA,
        "orchestrator_score": 85,
        "band": a_band,
        "attribution": {"agents": ["bugs"]},
        "snapshot": a_snapshot if a_snapshot is not None
        else snap(1, line=11, band=a_band),
    }
    row = mk_finding(row_band, "persisted", HB,
                     members=[member_ref(title="B"), a_member])
    return mk_state([mk_pass(1, []), mk_pass(2, [row])])


def obsolete_verdict(at_pass=2, blob="b1"):
    v = {"verdict": "obsolete", "agent": "fix", "head_sha": "50f9932e",
         "at_pass": at_pass, "reason": "line rewritten"}
    if blob is not None:
        v["verified_blob"] = blob
    return v


def gate(counts):
    flags = {"state_file_present": True, "noninteractive": False,
             "pr_mode": False, "range_mode": False,
             "outstanding_cw": counts["outstanding_cw"],
             "unacknowledged_medium": counts["unacknowledged_medium"]}
    return finalize_gate.decide(flags)["action"]


def old_rule(state):
    """The retired 90-finalize.md prose computation, transcribed."""
    last = state["passes"][-1]["findings"]
    acks = state.get("medium_acknowledgments", {})
    old_cw = len([f for f in last if f["band"] in ("critical", "warning")
                  and f["status"] != "fixed-since-last"])
    old_med = len([f for f in last if f["band"] == "medium"
                   and f["stable_hash"] not in acks])
    return old_cw, old_med


class TestFixtureIntegrity(unittest.TestCase):
    """Pitfall 5: assert the fixture holds what the tests below assume."""

    def test_fixture_last_pass_rows(self):
        last = load_fixture()["passes"][-1]
        self.assertEqual(last["pass_number"], 2)
        by_hash = {f["stable_hash"]: f for f in last["findings"]}
        self.assertEqual(by_hash[ARCH_HASH]["band"], "warning")
        self.assertEqual(by_hash[ARCH_HASH]["status"], "needs-recheck")
        self.assertEqual(by_hash[ARCH_HASH]["file"], ARCH_FILE)
        self.assertEqual(by_hash[BUGS_HASH]["band"], "medium")
        audit = [f for f in last["findings"] if f["status"] == "audit"]
        self.assertEqual(len(audit), 1)
        self.assertEqual(audit[0]["band"], "low")

    def test_fixture_members_carry_no_obligation(self):
        for f in load_fixture()["passes"][-1]["findings"]:
            for m in f.get("members", []):
                self.assertNotIn("obligation", m)


class TestFinalizeCounts(unittest.TestCase):
    def test_counts_fixture_as_is(self):
        c = carry_state.finalize_counts(load_fixture())
        self.assertEqual(c["outstanding_cw"], 1)
        self.assertEqual(c["unacknowledged_medium"], 1)
        self.assertEqual(c["outstanding_cw_hashes"], [ARCH_HASH])
        self.assertEqual(c["unacknowledged_medium_hashes"], [BUGS_HASH])
        self.assertEqual(c["verified_obsolete_hashes"], [])

    def test_counts_fix_obsolete_latest_pass_with_matching_blob_closes(self):
        s = load_fixture()
        s["fix_verdicts"] = {ARCH_HASH: obsolete_verdict()}
        c = carry_state.finalize_counts(s, {ARCH_FILE: "b1"})
        self.assertEqual(c["outstanding_cw"], 0)
        self.assertEqual(c["verified_obsolete_hashes"], [ARCH_HASH])

    def test_counts_stale_fix_verdict_never_closes(self):
        s = load_fixture()
        s["fix_verdicts"] = {ARCH_HASH: obsolete_verdict(at_pass=1)}
        c = carry_state.finalize_counts(s, {ARCH_FILE: "b1"})
        self.assertEqual(c["outstanding_cw"], 1)
        self.assertEqual(c["verified_obsolete_hashes"], [])

    def test_counts_evidence_binding(self):
        cases = [
            ("intervening edit", obsolete_verdict(), {ARCH_FILE: "b2"}),
            ("no head blobs", obsolete_verdict(), None),
            ("empty head blobs", obsolete_verdict(), {}),
            ("verified_blob missing", obsolete_verdict(blob=None),
             {ARCH_FILE: "b1"}),
            ("verified_blob non-str", dict(obsolete_verdict(), verified_blob=7),
             {ARCH_FILE: "b1"}),
        ]
        for name, verdict, blobs in cases:
            with self.subTest(name):
                s = load_fixture()
                s["fix_verdicts"] = {ARCH_HASH: verdict}
                c = carry_state.finalize_counts(s, blobs)
                self.assertEqual(c["outstanding_cw"], 1)
                self.assertEqual(c["verified_obsolete_hashes"], [])

    def test_counts_kept_open_is_open(self):
        w = mk_finding("warning", "persisted", HA,
                       kept_open="below-min-confidence", orchestrator_score=10,
                       agent_confidence=5)
        c = carry_state.finalize_counts(mk_state([mk_pass(1, [w])]))
        self.assertEqual(c["outstanding_cw"], 1)
        m = mk_finding("medium", "persisted", HB, kept_open="sub-threshold")
        c = carry_state.finalize_counts(mk_state([mk_pass(1, [m])]))
        self.assertEqual(c["unacknowledged_medium"], 1)

    def test_counts_decision_defer_and_dismiss_close(self):
        for decision in ("defer", "dismiss"):
            with self.subTest(decision):
                s = load_fixture()
                s["decisions"] = {BUGS_HASH: {"decision": decision,
                                              "reason": "r", "at_pass": 2,
                                              "band": "medium"}}
                c = carry_state.finalize_counts(s)
                self.assertEqual(c["unacknowledged_medium"], 0)
                self.assertEqual(c["outstanding_cw"], 1)


class TestAbsorbedObligationCounts(unittest.TestCase):
    """codex rewrite-3 high: an absorbed obligation is its own finding."""

    def test_counts_both_lead_and_absorbed(self):
        c = carry_state.finalize_counts(ba_state())
        self.assertEqual(c["outstanding_cw"], 2)
        self.assertEqual(c["outstanding_cw_hashes"], sorted([HA, HB]))

    def test_counts_lead_decision_never_closes_member(self):
        for decision in ("dismiss", "defer"):
            with self.subTest(decision):
                s = ba_state()
                s["decisions"] = {HB: {"decision": decision, "reason": "r",
                                       "at_pass": 2, "band": "warning"}}
                c = carry_state.finalize_counts(s)
                self.assertEqual(c["outstanding_cw"], 1)
                self.assertEqual(c["outstanding_cw_hashes"], [HA])
                self.assertEqual(gate(c), "outstanding-to-phase-5")

    def test_counts_lead_fix_obsolete_never_closes_member(self):
        s = ba_state()
        s["fix_verdicts"] = {HB: obsolete_verdict()}
        c = carry_state.finalize_counts(s, {F: "b1"})
        self.assertEqual(c["outstanding_cw"], 1)
        self.assertEqual(c["outstanding_cw_hashes"], [HA])
        self.assertEqual(c["verified_obsolete_hashes"], [HB])
        s["decisions"] = {HA: {"decision": "defer", "reason": "r",
                               "at_pass": 2, "band": "warning"}}
        c = carry_state.finalize_counts(s, {F: "b1"})
        self.assertEqual(c["outstanding_cw"], 0)
        self.assertEqual(gate(c), "write")

    def test_counts_member_bands(self):
        s = ba_state(a_band="medium")
        s["decisions"] = {HB: {"decision": "dismiss", "reason": "r",
                               "at_pass": 2, "band": "warning"}}
        c = carry_state.finalize_counts(s)
        self.assertEqual(c["unacknowledged_medium_hashes"], [HA])
        self.assertEqual(c["outstanding_cw"], 0)
        self.assertEqual(gate(c), "medium-ack-loop")
        s = ba_state(a_band="low")
        s["decisions"] = {HB: {"decision": "dismiss", "reason": "r",
                               "at_pass": 2, "band": "warning"}}
        c = carry_state.finalize_counts(s)
        self.assertEqual((c["outstanding_cw"], c["unacknowledged_medium"]),
                         (0, 0))
        self.assertEqual(gate(c), "write")

    def test_counts_dedupe_kept_open_row_own_sidecar(self):
        m = member_ref()
        m["obligation"] = {"stable_hash": HA, "band": "warning",
                           "snapshot": snap(1)}
        row = mk_finding("warning", "persisted", HA, members=[m])
        s = mk_state([mk_pass(2, [row])])
        recs = carry_state.open_findings(s)
        self.assertEqual([r["stable_hash"] for r in recs], [HA])
        self.assertIs(recs[0], s["passes"][-1]["findings"][0])
        self.assertEqual(carry_state.finalize_counts(s)["outstanding_cw"], 1)

    def test_counts_dedupe_two_rows_same_member_hash(self):
        rows = []
        for h in (HB, "c" * 64):
            m = member_ref()
            m["obligation"] = {"stable_hash": HA, "band": "warning"}
            rows.append(mk_finding("warning", "new", h, members=[m]))
        s = mk_state([mk_pass(2, rows)])
        recs = carry_state.open_findings(s)
        hashes = [r["stable_hash"] for r in recs]
        self.assertEqual(hashes, [HB, "c" * 64, HA])
        self.assertEqual(len(set(hashes)), len(hashes))
        self.assertEqual(recs[2]["absorbed_into"], HB)

    def test_counts_member_record_shape(self):
        recs = carry_state.open_findings(ba_state())
        a = [r for r in recs if r["stable_hash"] == HA][0]
        self.assertEqual(a["band"], "warning")
        self.assertEqual(a["file"], F)
        self.assertEqual(a["line"], 11)
        self.assertEqual(a["title"], "A")
        self.assertEqual(a["status"], "persisted")
        self.assertEqual(a["absorbed_into"], HB)
        self.assertEqual(a["snapshot"]["at_pass"], 1)

    def test_counts_member_on_closed_row_is_not_a_record(self):
        for status in ("fixed-since-last", "audit"):
            with self.subTest(status):
                s = ba_state()
                s["passes"][-1]["findings"][0]["status"] = status
                self.assertEqual(carry_state.open_findings(s), [])
                c = carry_state.finalize_counts(s)
                self.assertEqual(c["outstanding_cw"], 0)

    def test_malformed_sidecar_fails_closed(self):
        def mutate(fn):
            s = ba_state()
            fn(s["passes"][-1]["findings"][0])
            return s

        cases = {
            "members not a list": lambda r: r.__setitem__("members", {}),
            "member not a dict": lambda r: r["members"].append("x"),
            "obligation not a dict": lambda r: r["members"][1].__setitem__(
                "obligation", "x"),
            "obligation hash missing": lambda r: r["members"][1][
                "obligation"].pop("stable_hash"),
            "obligation hash non-str": lambda r: r["members"][1][
                "obligation"].__setitem__("stable_hash", 5),
            "obligation band missing": lambda r: r["members"][1][
                "obligation"].pop("band"),
        }
        for name, fn in cases.items():
            with self.subTest(name):
                s = mutate(fn)
                self.assertIsNone(carry_state.open_findings(s))
                self.assertIsNone(carry_state.finalize_counts(s))
                self.assertIsNone(carry_state.pending(s))


class TestLegacyEquality(unittest.TestCase):
    """R3/D-06: old medium-only states give the retired rule's exact counts.

    Caveat: the old c/w rule does not exclude `audit`, the new open allowlist
    does. Audit rows are band `low`, so the two agree. A medium with status
    `fixed-since-last` would diverge, but score.py never emits one into
    findings[] (fixed-since-last rows are dropped at carry-forward), so the
    synthetic fixed-since-last row below is a critical, which both rules skip.
    """

    def _states(self):
        acked = mk_state([mk_pass(1, [mk_finding("medium", "new", HA),
                                      mk_finding("medium", "persisted", HB)])],
                         medium_acknowledgments={HA: {"decision": "dismiss",
                                                      "reason": "r",
                                                      "at_pass": 1}})
        return {
            "fixture": load_fixture(),
            "mediums acked": acked,
            "mediums unacked": mk_state([mk_pass(1, [
                mk_finding("medium", "new", HA),
                mk_finding("medium", "needs-recheck", HB)])]),
            "with critical": mk_state([mk_pass(1, [
                mk_finding("critical", "new", HA),
                mk_finding("medium", "new", HB)])]),
            "with fixed-since-last": mk_state([mk_pass(1, [
                mk_finding("critical", "fixed-since-last", HA),
                mk_finding("warning", "persisted", "c" * 64),
                mk_finding("medium", "new", HB)])]),
            "with audit rows": mk_state([mk_pass(1, [
                mk_finding("low", "audit", HA),
                mk_finding("medium", "new", HB)])]),
            "empty findings": mk_state([mk_pass(1, [])]),
        }

    def test_legacy_equality(self):
        states = self._states()
        self.assertEqual(len(states), 7)
        for name, s in states.items():
            with self.subTest(name):
                c = carry_state.finalize_counts(s)
                self.assertEqual((c["outstanding_cw"],
                                  c["unacknowledged_medium"]), old_rule(s))

    def test_legacy_state_is_not_rewritten(self):
        s = self._states()["mediums acked"]
        before = json.dumps(s, sort_keys=True)
        carry_state.finalize_counts(s)
        carry_state.pending(s)
        self.assertEqual(json.dumps(s, sort_keys=True), before)


class TestGateTable(unittest.TestCase):
    BANDS = ("critical", "warning", "medium", "low")
    CLOSED_BY = ("none", "decision-dismiss", "decision-defer", "legacy-ack",
                 "fix-obsolete-latest", "fix-obsolete-stale")
    CLOSING = {"decision-dismiss", "decision-defer", "legacy-ack",
               "fix-obsolete-latest"}

    def _state(self, band, closed_by):
        s = mk_state([mk_pass(1, []), mk_pass(2, [mk_finding(band, "new", HA)])])
        if closed_by.startswith("decision-"):
            s["decisions"] = {HA: {"decision": closed_by.split("-")[1],
                                   "reason": "r", "at_pass": 2, "band": band}}
        elif closed_by == "legacy-ack":
            s["medium_acknowledgments"] = {HA: {"decision": "dismiss",
                                                "reason": "r", "at_pass": 2}}
        elif closed_by == "fix-obsolete-latest":
            s["fix_verdicts"] = {HA: obsolete_verdict(at_pass=2)}
        elif closed_by == "fix-obsolete-stale":
            s["fix_verdicts"] = {HA: obsolete_verdict(at_pass=1)}
        return s

    def test_gate_table_integrity(self):
        c = carry_state.finalize_counts(self._state("critical", "none"))
        self.assertGreater(c["outstanding_cw"], 0)
        c = carry_state.finalize_counts(self._state("medium", "none"))
        self.assertGreater(c["unacknowledged_medium"], 0)

    def test_gate_table(self):
        n = 0
        for band in self.BANDS:
            for closed_by in self.CLOSED_BY:
                with self.subTest(band=band, closed_by=closed_by):
                    c = carry_state.finalize_counts(self._state(band, closed_by),
                                                    {F: "b1"})
                    action = gate(c)
                    if band == "low" or closed_by in self.CLOSING:
                        self.assertEqual(action, "write")
                    elif band in ("critical", "warning"):
                        self.assertEqual(action, "outstanding-to-phase-5")
                    else:
                        self.assertEqual(action, "medium-ack-loop")
                    n += 1
        self.assertEqual(n, 24)


class TestNoExpiry(unittest.TestCase):
    def test_no_expiry_five_passes(self):
        passes = [mk_pass(i, [mk_finding("warning", "persisted" if i > 1
                                         else "new", HA)])
                  for i in range(1, 6)]
        s = mk_state(passes)
        self.assertEqual(carry_state.finalize_counts(s)["outstanding_cw"], 1)
        self.assertIn(HA, [r["stable_hash"]
                           for r in carry_state.open_findings(s)])

    def test_no_expiry_signature_has_no_age_input(self):
        self.assertEqual(
            list(inspect.signature(carry_state.finalize_counts).parameters),
            ["state", "head_blobs"])
        self.assertEqual(
            list(inspect.signature(carry_state.pending).parameters), ["state"])


class TestMalformed(unittest.TestCase):
    def _cases(self):
        def bad_hash():
            s = load_fixture()
            s["passes"][-1]["findings"][0]["stable_hash"] = 5
            return s

        def no_findings():
            s = load_fixture()
            del s["passes"][-1]["findings"]
            return s

        def with_root(key, value):
            s = load_fixture()
            s[key] = value
            return s

        return {
            "non-dict state": [],
            "passes missing": {"medium_acknowledgments": {}},
            "passes empty": {"passes": []},
            "passes non-list": {"passes": {}},
            "last pass without findings": no_findings(),
            "stable_hash non-str": bad_hash(),
            "decisions non-dict": with_root("decisions", []),
            "fix_verdicts non-dict": with_root("fix_verdicts", "x"),
            "fix_verdicts at_pass bool": with_root(
                "fix_verdicts", {ARCH_HASH: dict(obsolete_verdict(),
                                                 at_pass=True)}),
            "medium_acknowledgments non-dict": with_root(
                "medium_acknowledgments", []),
        }

    def test_malformed_returns_none(self):
        for name, s in self._cases().items():
            with self.subTest(name):
                self.assertIsNone(carry_state.finalize_counts(s))
                self.assertIsNone(carry_state.pending(s))
                self.assertIsNone(carry_state.open_findings(s))


class TestPending(unittest.TestCase):
    def _fixture_with_snapshots(self):
        s = load_fixture()
        for f in s["passes"][-1]["findings"]:
            if f["stable_hash"] == ARCH_HASH:
                f["snapshot"] = snap(1, file=f["file"], line=f["line"])
            elif f["stable_hash"] == BUGS_HASH:
                f["snapshot"] = snap(2, file=f["file"], line=f["line"],
                                     band="medium")
        return s

    def test_pending_fixture(self):
        self.assertEqual(carry_state.pending(self._fixture_with_snapshots()),
                         [{"stable_hash": ARCH_HASH, "since_pass": 1}])

    def test_pending_decision_drops_out(self):
        s = self._fixture_with_snapshots()
        s["decisions"] = {ARCH_HASH: {"decision": "defer", "reason": "r",
                                      "at_pass": 2, "band": "warning"}}
        self.assertEqual(carry_state.pending(s), [])

    def test_pending_fail_soft_on_bad_snapshot(self):
        for name, value in (("missing", None), ("non-dict", "x"),
                            ("at_pass bool", {"at_pass": True}),
                            ("at_pass str", {"at_pass": "1"})):
            with self.subTest(name):
                s = self._fixture_with_snapshots()
                f = [x for x in s["passes"][-1]["findings"]
                     if x["stable_hash"] == ARCH_HASH][0]
                if value is None:
                    del f["snapshot"]
                else:
                    f["snapshot"] = value
                self.assertEqual(carry_state.pending(s), [])

    def test_pending_strictly_older(self):
        s = self._fixture_with_snapshots()
        for f in s["passes"][-1]["findings"]:
            if "snapshot" in f:
                f["snapshot"]["at_pass"] = 2
        self.assertEqual(carry_state.pending(s), [])

    def test_pending_fragment_current_code_is_not_change(self):
        s = self._fixture_with_snapshots()
        f = [x for x in s["passes"][-1]["findings"]
             if x["stable_hash"] == ARCH_HASH][0]
        # Fixture fact (Pitfall 1): the quoted fragment never equals HEAD.
        self.assertNotEqual(f["current_code"].splitlines()[0],
                            f["canonical_line_content"])
        self.assertIn({"stable_hash": ARCH_HASH, "since_pass": 1},
                      carry_state.pending(s))

    def test_pending_member_obligation(self):
        s = ba_state()
        s["passes"][-1]["findings"][0]["snapshot"] = snap(2)
        self.assertEqual(carry_state.pending(s),
                         [{"stable_hash": HA, "since_pass": 1}])
        s["decisions"] = {HA: {"decision": "defer", "reason": "r",
                               "at_pass": 2, "band": "warning"}}
        self.assertEqual(carry_state.pending(s), [])

    def test_pending_member_bad_snapshot_fail_soft(self):
        for value in ("x", {"at_pass": True}, {}):
            with self.subTest(value=value):
                s = ba_state(a_snapshot=value)
                self.assertEqual(carry_state.pending(s), [])
        s = ba_state()
        del s["passes"][-1]["findings"][0]["members"][1]["obligation"][
            "snapshot"]
        self.assertEqual(carry_state.pending(s), [])

    def test_pending_sorted(self):
        rows = [mk_finding("warning", "persisted", h, snapshot=snap(1))
                for h in ("c" * 64, HA, HB)]
        s = mk_state([mk_pass(1, []), mk_pass(3, rows)])
        self.assertEqual([p["stable_hash"] for p in carry_state.pending(s)],
                         [HA, HB, "c" * 64])


def run_cli(args, stdin_bytes):
    return subprocess.run([sys.executable, CARRY_STATE_PY] + args,
                          input=stdin_bytes, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=30)


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path


class TestCLICounts(TempDirCase):
    def test_cli_counts_fixture(self):
        proc = run_cli(["finalize-counts"], json.dumps(load_fixture()).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        out = json.loads(proc.stdout.decode())
        self.assertEqual(out, carry_state.finalize_counts(load_fixture()))

    def test_cli_counts_head_blobs_match(self):
        s = load_fixture()
        s["fix_verdicts"] = {ARCH_HASH: obsolete_verdict()}
        blobs = self.write("blobs.json", json.dumps({ARCH_FILE: "b1"}))
        proc = run_cli(["finalize-counts", "--head-blobs", blobs],
                       json.dumps(s).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        out = json.loads(proc.stdout.decode())
        self.assertEqual(out["outstanding_cw"], 0)
        self.assertEqual(out, carry_state.finalize_counts(s, {ARCH_FILE: "b1"}))

    def test_cli_counts_bad_head_blobs(self):
        cases = {
            "missing": os.path.join(self.tmp, "nope.json"),
            "non-json": self.write("bad.json", "not json"),
            "non-object": self.write("list.json", "[1]"),
            "non-str value": self.write("num.json", json.dumps({ARCH_FILE: 1})),
        }
        for name, path in cases.items():
            with self.subTest(name):
                proc = run_cli(["finalize-counts", "--head-blobs", path],
                               json.dumps(load_fixture()).encode())
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                self.assertIn(proc.stderr.decode().strip(),
                              [r.strip() for r in carry_state.REASONS])

    def test_cli_malformed_invalid_json(self):
        for sub in ("finalize-counts", "pending"):
            with self.subTest(sub):
                proc = run_cli([sub], b"not json")
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")

    def test_cli_malformed_states(self):
        for name, s in TestMalformed()._cases().items():
            for sub in ("finalize-counts", "pending"):
                with self.subTest(name=name, sub=sub):
                    proc = run_cli([sub], json.dumps(s).encode())
                    self.assertEqual(proc.returncode, 2)
                    self.assertEqual(proc.stdout, b"")
                    self.assertIn(proc.stderr.decode().strip(),
                                  [r.strip() for r in carry_state.REASONS])

    def test_cli_malformed_reasons_carry_no_state_values(self):
        s = load_fixture()
        s["passes"][-1]["findings"][0]["stable_hash"] = 5
        proc = run_cli(["finalize-counts"], json.dumps(s).encode())
        err = proc.stderr.decode()
        for leak in (ARCH_HASH, BUGS_HASH, ARCH_FILE, "Two prose files"):
            self.assertNotIn(leak, err)

    def test_cli_pending(self):
        s = TestPending()._fixture_with_snapshots()
        proc = run_cli(["pending"], json.dumps(s).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout.decode()),
                         [{"stable_hash": ARCH_HASH, "since_pass": 1}])

    def test_cli_usage_errors(self):
        state = json.dumps(load_fixture()).encode()
        for argv in ([], ["bogus"], ["finalize-counts", "--title", "x"],
                     ["pending", "--head-blobs", "x"],
                     ["finalize-counts", "--head-blobs"]):
            with self.subTest(argv=argv):
                proc = run_cli(argv, state)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")


class TestReasonsSealed(unittest.TestCase):
    def test_reasons_are_fixed_lines(self):
        self.assertIsInstance(carry_state.REASONS, tuple)
        for r in carry_state.REASONS:
            self.assertTrue(r.endswith("\n"))
            self.assertNotIn("%", r)
            self.assertNotIn("{", r)

    def test_sealed_tuples(self):
        self.assertEqual(carry_state.OPEN_STATUSES,
                         ("new", "persisted", "needs-recheck"))
        self.assertEqual(carry_state.DECISIONS, ("dismiss", "defer"))
        self.assertEqual(carry_state.BLOCKING_BANDS,
                         ("critical", "warning", "medium"))


class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "os", "sys"}

    def _tree(self):
        with open(CARRY_STATE_PY, "r", encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_import_set_is_exactly_allowed(self):
        imported = set()
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertEqual(imported, self.ALLOWED)

    def test_os_used_only_for_isfile(self):
        for node in ast.walk(self._tree()):
            if (isinstance(node, ast.Attribute)
                    and getattr(node.value, "id", None) == "os"):
                self.assertEqual(node.attr, "path")
            if (isinstance(node, ast.Attribute) and isinstance(
                    node.value, ast.Attribute)
                    and getattr(node.value.value, "id", None) == "os"):
                self.assertEqual(node.attr, "isfile")

    def test_no_forbidden_calls(self):
        banned = {"eval", "exec", "compile", "__import__"}
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, banned)


class TestNoWritePath(unittest.TestCase):
    """The helper never writes a file: the prose redirects stdout and `mv`s."""

    def setUp(self):
        with open(CARRY_STATE_PY, "r", encoding="utf-8") as fh:
            self.tree = ast.parse(fh.read())

    def test_no_open_call_in_write_mode(self):
        opens = 0
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id",
                                                      None) == "open":
                opens += 1
                modes = [a.value for a in node.args[1:]
                         if isinstance(a, ast.Constant)]
                modes += [kw.value.value for kw in node.keywords
                          if kw.arg == "mode"
                          and isinstance(kw.value, ast.Constant)]
                self.assertEqual(modes, ["r"],
                                 "every open() must pass an explicit 'r'")
        self.assertGreater(opens, 0, "lock is vacuous: no open() seen")

    def test_no_write_capable_imports(self):
        imported = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    imported.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for banned in ("shutil", "tempfile", "pathlib", "subprocess"):
            self.assertNotIn(banned, imported)

    def test_only_stderr_and_stdout_are_written(self):
        writes = 0
        for node in ast.walk(self.tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("write", "writelines", "truncate",
                                           "dump")):
                target = node.func.value
                if node.func.attr == "dump":
                    # json.dump(obj, fp): the fp must be a std stream.
                    self.assertEqual(getattr(target, "id", None), "json")
                    target = node.args[1] if len(node.args) > 1 else None
                writes += 1
                ok = (isinstance(target, ast.Attribute)
                      and target.attr in ("stdout", "stderr")
                      and getattr(target.value, "id", None) == "sys")
                self.assertTrue(ok, "carry_state.py writes to something "
                                    "that is not sys.stdout/sys.stderr")
        self.assertGreater(writes, 0, "lock is vacuous: no write seen")



# --------------------------------------------------------------------------- #
# Writers.
# --------------------------------------------------------------------------- #
def frozen_families(state, keys=("passes", "medium_acknowledgments")):
    return {k: json.dumps(state.get(k), sort_keys=True) for k in keys}


def defer_payload(h=ARCH_HASH, decision="defer", reason="ships next milestone",
                  at_pass=2):
    return {"at_pass": at_pass,
            "decisions": [{"stable_hash": h, "decision": decision,
                           "reason": reason}]}


ARCH_CANONICAL_PREFIX = ("**REQUIRED OUTPUT \u2014 the Phase 1d status line "
                         "(diff mode only).**")


def arch_row_evidence():
    """The ARCH lead row's own four evidence fields as literals (the fixture
    row has no snapshot, so a decision's evidence is derived from the row).
    file/line/band are written out; the long canonical line is read from the
    raw fixture JSON (never from carry_state) and pinned by its prefix."""
    row = [f for f in load_fixture()["passes"][-1]["findings"]
           if f["stable_hash"] == ARCH_HASH][0]
    canonical = row["canonical_line_content"]
    assert canonical.startswith(ARCH_CANONICAL_PREFIX), canonical[:80]
    assert "snapshot" not in row
    return {"file": ARCH_FILE, "line": 74,
            "canonical_line_content": canonical, "band": "warning"}


def verdict_payload(**over):
    p = {"at_pass": 2, "head_sha": "50f9932e", "sent": [ARCH_HASH],
         "results": [{"id": ARCH_HASH, "status": "obsolete",
                      "summary": "line rewritten"}],
         "blobs": {ARCH_FILE: "b1"}}
    p.update(over)
    return p


class TestRecordDecisions(unittest.TestCase):
    def test_record_decisions_writes_record_with_finding_band(self):
        s = load_fixture()
        out = carry_state.record_decisions(s, defer_payload())
        self.assertEqual(out["decisions"][ARCH_HASH],
                         {"decision": "defer", "reason": "ships next milestone",
                          "at_pass": 2, "band": "warning",
                          "evidence": arch_row_evidence()})

    def test_record_decisions_band_follows_each_record(self):
        # Non-vacuity: the two records differ in band, so a constant cannot pass.
        out = carry_state.record_decisions(
            load_fixture(), defer_payload(h=BUGS_HASH, decision="dismiss"))
        self.assertEqual(out["decisions"][BUGS_HASH]["band"], "medium")
        s = ba_state(row_band="critical", a_band="medium")
        out = carry_state.record_decisions(s, {"at_pass": 2, "decisions": [
            {"stable_hash": HA, "decision": "defer", "reason": "r"},
            {"stable_hash": HB, "decision": "defer", "reason": "r"}]})
        self.assertEqual(out["decisions"][HA]["band"], "medium")
        self.assertEqual(out["decisions"][HB]["band"], "critical")

    def test_record_decisions_band_never_from_payload(self):
        s = load_fixture()
        p = defer_payload()
        p["decisions"][0]["band"] = "low"
        self.assertIsNone(carry_state.record_decisions(s, p))

    def test_record_decisions_leaves_other_families_identical(self):
        s = load_fixture()
        s["medium_acknowledgments"] = {BUGS_HASH: {"decision": "dismiss",
                                                   "reason": "r", "at_pass": 1}}
        s["fix_verdicts"] = {ARCH_HASH: obsolete_verdict()}
        before = json.dumps(s, sort_keys=True)
        out = carry_state.record_decisions(s, defer_payload())
        self.assertEqual(json.dumps(s, sort_keys=True), before, "input mutated")
        self.assertEqual(frozen_families(out),
                         frozen_families(s))
        self.assertEqual(out["passes"], s["passes"])
        self.assertEqual(out["fix_verdicts"], s["fix_verdicts"])
        self.assertIsNot(out, s)

    def test_record_decisions_closes_in_counts(self):
        out = carry_state.record_decisions(load_fixture(), defer_payload())
        self.assertEqual(carry_state.finalize_counts(out)["outstanding_cw"], 0)

    def test_record_decisions_refusals(self):
        dup = defer_payload()
        dup["decisions"].append(dict(dup["decisions"][0]))
        cases = {
            "decision unknown": defer_payload(decision="ignore"),
            "reason empty": defer_payload(reason=""),
            "reason whitespace": defer_payload(reason="  \n\t"),
            "reason non-str": defer_payload(reason=5),
            "hash not open": defer_payload(h="d96ad4eb1ab44609f6005698d3e77a5b"
                                             "43f7851914a4df08b6e1e986a5249856"),
            "hash unknown": defer_payload(h="f" * 64),
            "hash prefix": defer_payload(h=ARCH_HASH[:10]),
            "hash non-str": defer_payload(h=5),
            "at_pass bool": defer_payload(at_pass=True),
            "at_pass str": defer_payload(at_pass="2"),
            "duplicate hash": dup,
            "payload not object": [],
            "decisions not list": {"at_pass": 2, "decisions": {}},
            "entry not object": {"at_pass": 2, "decisions": ["x"]},
            "unknown payload key": dict(defer_payload(), passes=[]),
        }
        for name, payload in cases.items():
            with self.subTest(name):
                self.assertIsNone(
                    carry_state.record_decisions(load_fixture(), payload))

    def test_record_decisions_refuses_malformed_state(self):
        self.assertIsNone(carry_state.record_decisions({"passes": []},
                                                       defer_payload()))

    def test_record_decisions_latest_wins(self):
        s = carry_state.record_decisions(load_fixture(), defer_payload())
        s = carry_state.record_decisions(
            s, defer_payload(decision="dismiss", reason="false positive",
                             at_pass=3))
        self.assertEqual(s["decisions"][ARCH_HASH],
                         {"decision": "dismiss", "reason": "false positive",
                          "at_pass": 3, "band": "warning",
                          "evidence": arch_row_evidence(),
                          "history": [{"decision": "defer",
                                       "reason": "ships next milestone",
                                       "at_pass": 2, "band": "warning",
                                       "evidence": arch_row_evidence()}]})
        self.assertEqual(list(s["decisions"]), [ARCH_HASH])

    def test_record_decisions_member_obligation_own_hash(self):
        s = ba_state(row_band="critical", a_band="warning")
        before = json.dumps(s["passes"], sort_keys=True)
        out = carry_state.record_decisions(
            s, {"at_pass": 2, "decisions": [{"stable_hash": HA,
                                             "decision": "defer",
                                             "reason": "later"}]})
        self.assertEqual(out["decisions"][HA],
                         {"decision": "defer", "reason": "later", "at_pass": 2,
                          "band": "warning",
                          "evidence": {"file": F, "line": 11,
                                       "canonical_line_content": "x = 1",
                                       "band": "warning"}})
        self.assertEqual(json.dumps(out["passes"], sort_keys=True), before)
        self.assertIsNone(carry_state.record_decisions(
            s, {"at_pass": 2, "decisions": [{"stable_hash": "e" * 64,
                                             "decision": "defer",
                                             "reason": "later"}]}))


class TestRecordFixVerdicts(unittest.TestCase):
    def test_record_fix_verdicts_writes_obsolete(self):
        out = carry_state.record_fix_verdicts(load_fixture(), verdict_payload())
        self.assertEqual(out["fix_verdicts"][ARCH_HASH],
                         {"verdict": "obsolete", "agent": "fix",
                          "head_sha": "50f9932e", "at_pass": 2,
                          "verified_blob": "b1", "reason": "line rewritten"})
        c = carry_state.finalize_counts(out, {ARCH_FILE: "b1"})
        self.assertEqual(c["outstanding_cw"], 0)

    def test_record_fix_verdicts_null_summary_and_head(self):
        p = verdict_payload(head_sha=None)
        p["results"][0]["summary"] = None
        out = carry_state.record_fix_verdicts(load_fixture(), p)
        self.assertEqual(out["fix_verdicts"][ARCH_HASH]["reason"], "")
        self.assertIsNone(out["fix_verdicts"][ARCH_HASH]["head_sha"])

    def test_record_fix_verdicts_missing_fingerprint_writes_nothing(self):
        cases = {
            "blobs missing": {k: v for k, v in verdict_payload().items()
                              if k != "blobs"},
            "blobs not dict": verdict_payload(blobs=["b1"]),
            "file absent": verdict_payload(blobs={"other.py": "b1"}),
            "value non-str": verdict_payload(blobs={ARCH_FILE: 1}),
        }
        for name, payload in cases.items():
            with self.subTest(name):
                s = load_fixture()
                skipped = []
                out = carry_state.record_fix_verdicts(s, payload, skipped)
                self.assertNotIn(ARCH_HASH, out.get("fix_verdicts", {}))
                self.assertEqual(skipped, [ARCH_HASH])
                self.assertEqual(frozen_families(out), frozen_families(s))

    def test_record_fix_verdicts_writes_nothing_for_non_obsolete(self):
        for status in ("applied", "needs-human", "errored", "OBSOLETE"):
            with self.subTest(status):
                p = verdict_payload()
                p["results"][0]["status"] = status
                out = carry_state.record_fix_verdicts(load_fixture(), p)
                self.assertEqual(out.get("fix_verdicts", {}), {})

    def test_record_fix_verdicts_guards(self):
        cases = {
            "id not sent": verdict_payload(sent=[BUGS_HASH]),
            "prefix id": verdict_payload(
                sent=["ddca00413f"],
                results=[{"id": "ddca00413f", "status": "obsolete",
                          "summary": "s"}]),
            "id not in last pass": verdict_payload(
                sent=["f" * 64],
                results=[{"id": "f" * 64, "status": "obsolete",
                          "summary": "s"}]),
            "id non-str": verdict_payload(
                results=[{"id": 5, "status": "obsolete", "summary": "s"}]),
        }
        for name, payload in cases.items():
            with self.subTest(name):
                out = carry_state.record_fix_verdicts(load_fixture(), payload)
                self.assertEqual(out.get("fix_verdicts", {}), {})

    def test_record_fix_verdicts_leaves_other_families_identical(self):
        s = load_fixture()
        s["decisions"] = {BUGS_HASH: {"decision": "defer", "reason": "r",
                                      "at_pass": 2, "band": "medium"}}
        before = json.dumps(s, sort_keys=True)
        out = carry_state.record_fix_verdicts(s, verdict_payload())
        self.assertEqual(json.dumps(s, sort_keys=True), before, "input mutated")
        keys = ("passes", "medium_acknowledgments", "decisions")
        self.assertEqual(frozen_families(out, keys), frozen_families(s, keys))

    def test_record_fix_verdicts_refusals(self):
        cases = {
            "at_pass bool": verdict_payload(at_pass=True),
            "at_pass missing": {k: v for k, v in verdict_payload().items()
                                if k != "at_pass"},
            # Finalize-routed Phase 5: $PASS_NUMBER is last + 1 with no pass
            # persisted, so the verdict could never close (bugs-001).
            "at_pass next pass": verdict_payload(at_pass=3),
            "at_pass older pass": verdict_payload(at_pass=1),
            "head_sha non-str": verdict_payload(head_sha=5),
            "sent not list": verdict_payload(sent=ARCH_HASH),
            "results not list": verdict_payload(results={}),
            "result not object": verdict_payload(results=["x"]),
            "payload not object": [],
            "unknown key": dict(verdict_payload(), passes=[]),
        }
        for name, payload in cases.items():
            with self.subTest(name):
                self.assertIsNone(
                    carry_state.record_fix_verdicts(load_fixture(), payload))


class TestCLIWriters(TempDirCase):
    def test_cli_record_decisions_round_trips_shell_metacharacters(self):
        reason = "it's `id` and $(id) \"quoted\"\nnew line; rm -rf /"
        path = self.write("d.json", json.dumps(defer_payload(reason=reason)))
        proc = run_cli(["record-decisions", "--decisions-file", path],
                       json.dumps(load_fixture()).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        out = json.loads(proc.stdout.decode())
        self.assertEqual(out["decisions"][ARCH_HASH]["reason"], reason)
        self.assertEqual(out["passes"], load_fixture()["passes"])

    def test_cli_record_decisions_bad_file(self):
        cases = {
            "missing": os.path.join(self.tmp, "nope.json"),
            "non-json": self.write("bad.json", "{"),
            "non-object": self.write("list.json", "[]"),
            "refused payload": self.write(
                "r.json", json.dumps(defer_payload(reason=""))),
        }
        for name, path in cases.items():
            with self.subTest(name):
                proc = run_cli(["record-decisions", "--decisions-file", path],
                               json.dumps(load_fixture()).encode())
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                self.assertIn(proc.stderr.decode(), carry_state.REASONS)

    def test_cli_record_fix_verdicts(self):
        path = self.write("v.json", json.dumps(verdict_payload()))
        proc = run_cli(["record-fix-verdicts", "--verdicts-file", path],
                       json.dumps(load_fixture()).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(proc.stderr, b"")
        out = json.loads(proc.stdout.decode())
        self.assertEqual(out["fix_verdicts"][ARCH_HASH]["verified_blob"], "b1")

    def test_cli_record_fix_verdicts_missing_fingerprint(self):
        path = self.write("v.json", json.dumps(verdict_payload(blobs={})))
        proc = run_cli(["record-fix-verdicts", "--verdicts-file", path],
                       json.dumps(load_fixture()).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(proc.stderr.decode(), carry_state.REASON_NO_FINGERPRINT)
        out = json.loads(proc.stdout.decode())
        self.assertEqual(out.get("fix_verdicts", {}), {})
        self.assertEqual(out["passes"], load_fixture()["passes"])

    def test_cli_record_fix_verdicts_bad_file(self):
        for name, path in (("missing", os.path.join(self.tmp, "x.json")),
                           ("non-json", self.write("b.json", "nope")),
                           ("refused", self.write("r.json", json.dumps(
                               verdict_payload(at_pass=True))))):
            with self.subTest(name):
                proc = run_cli(["record-fix-verdicts", "--verdicts-file",
                                path], json.dumps(load_fixture()).encode())
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                self.assertIn(proc.stderr.decode(), carry_state.REASONS)

    def test_cli_flags_closed(self):
        self.assertEqual(carry_state.KNOWN_FLAGS,
                         ("--decisions-file", "--verdicts-file", "--head-blobs"))
        d = self.write("d.json", json.dumps(defer_payload()))
        state = json.dumps(load_fixture()).encode()
        for argv in (["record-decisions"],
                     ["record-decisions", "--decisions-file", d,
                      "--head-blobs", d],
                     ["record-decisions", "--verdicts-file", d],
                     ["record-decisions", "--reason", "x"],
                     ["record-fix-verdicts", "--head-blobs", d],
                     ["record-decisions", "--decisions-file", d,
                      "--decisions-file", d]):
            with self.subTest(argv=argv):
                proc = run_cli(argv, state)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")


# --------------------------------------------------------------------------- #
# Writer lock (helper half of the single-writer property).
# --------------------------------------------------------------------------- #
class TestRecordDecisionsInputUnmutated(unittest.TestCase):
    def test_record_decisions_history_path_leaves_input_unmutated(self):
        s = carry_state.record_decisions(load_fixture(), defer_payload())
        before = json.dumps(s, sort_keys=True)
        out = carry_state.record_decisions(
            s, defer_payload(decision="dismiss", reason="fp", at_pass=3))
        self.assertEqual(json.dumps(s, sort_keys=True), before, "input mutated")
        self.assertIn("history", out["decisions"][ARCH_HASH])
        self.assertNotIn("history", s["decisions"][ARCH_HASH])


# --------------------------------------------------------------------------- #
# Evidence-bound decisions (D-13). Builders shared with TestRollbackQuarantine.
# --------------------------------------------------------------------------- #
HC = "c" * 64


def dismiss(state, h, at_pass=2, reason="not a bug"):
    out = carry_state.record_decisions(state, {"at_pass": at_pass, "decisions": [
        {"stable_hash": h, "decision": "dismiss", "reason": reason}]})
    assert out is not None
    return out


def with_passes(decided, fresh):
    """The decided state's roots on top of a fresh state's passes: the same
    hash re-scored on a later pass."""
    out = copy.deepcopy(decided)
    out["passes"] = copy.deepcopy(fresh["passes"])
    return out


def record_of(state, h):
    return [r for r in carry_state.open_findings(state)
            if r["stable_hash"] == h][0]


def fixture_row(state, h):
    return [f for f in state["passes"][-1]["findings"]
            if f["stable_hash"] == h][0]


def band_change_state():
    decided = dismiss(ba_state(a_band="medium"), HA)
    return with_passes(decided, ba_state(a_band="warning"))


def line_move_state():
    decided = dismiss(ba_state(a_snapshot=snap(1, line=11)), HA)
    return with_passes(decided, ba_state(a_snapshot=snap(1, line=14)))


def unchanged_state():
    decided = dismiss(ba_state(), HA)
    return with_passes(decided, ba_state())


def history_state():
    s = dismiss(ba_state(), HA, reason="first")
    return dismiss(s, HA, at_pass=3, reason="second")


def rehash_state():
    s1 = mk_state([mk_pass(1, [mk_finding("warning", "persisted", HA,
                                          canonical_line_content="x = 1",
                                          snapshot=snap(1))])])
    decided = dismiss(s1, HA, at_pass=1)
    fresh = mk_state([mk_pass(1, []), mk_pass(2, [mk_finding(
        "warning", "persisted", HC, canonical_line_content="x = 2",
        snapshot=dict(snap(2), canonical_line_content="x = 2"))])])
    return with_passes(decided, fresh)


def snapshotless_decided_state():
    return dismiss(load_fixture(), ARCH_HASH)


def snapshotless_severity_state():
    s = snapshotless_decided_state()
    fixture_row(s, ARCH_HASH)["band"] = "critical"
    return s


def pre47_record(band="warning"):
    return {"decision": "dismiss", "reason": "r", "at_pass": 2, "band": band}


def pre47_state():
    s = ba_state(a_band="warning")
    s["decisions"] = {HA: pre47_record("medium")}
    return s


def null_evidence_state():
    s = ba_state()
    s["decisions"] = {HA: dict(pre47_record(), evidence=None)}
    return s


def real_decision_state():
    return carry_state.decision_state


class TestDecisionEvidence(unittest.TestCase):
    """D-13: a dismiss/defer closes only while the evidence it judged holds.

    Pitfall-1 rule: stable_hash covers canonical_line_content, so every
    SAME-HASH staleness fixture below varies `band` or `line` ONLY — never the
    canonical text. A canonical-text edit is the re-hash case
    (test_rehash_new_hash_open_orphan_kept), where the new hash simply has no
    decision.
    """

    # Scenario bodies are methods so the contrast subtests can re-run them
    # under a mutant and require them to fail.
    def _band_change_scenario(self):
        s = band_change_state()
        rec = record_of(s, HA)
        self.assertEqual(carry_state.decision_state(rec, s), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s), "severity")
        self.assertIn(HA, carry_state.finalize_counts(s)["outstanding_cw_hashes"])

    def _null_evidence_scenario(self):
        s = null_evidence_state()
        rec = record_of(s, HA)
        self.assertEqual(carry_state.decision_state(rec, s), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s), "code")
        self.assertIn(HA, carry_state.finalize_counts(s)["outstanding_cw_hashes"])

    def _snapshotless_scenario(self):
        s = snapshotless_decided_state()
        ev = s["decisions"][ARCH_HASH]["evidence"]
        self.assertIsInstance(ev, dict)
        self.assertEqual(ev, arch_row_evidence())
        rec = record_of(s, ARCH_HASH)
        self.assertEqual(carry_state.decision_state(rec, s), "current")
        self.assertNotIn(ARCH_HASH,
                         carry_state.finalize_counts(s)["outstanding_cw_hashes"])
        sev = snapshotless_severity_state()
        rec = record_of(sev, ARCH_HASH)
        self.assertNotIn("snapshot", fixture_row(sev, ARCH_HASH))
        self.assertEqual(carry_state.decision_state(rec, sev), "stale")
        self.assertEqual(carry_state.stale_cause(rec, sev), "severity")
        self.assertIn(ARCH_HASH,
                      carry_state.finalize_counts(sev)["outstanding_cw_hashes"])
        moved = snapshotless_decided_state()
        fixture_row(moved, ARCH_HASH)["line"] = 75
        rec = record_of(moved, ARCH_HASH)
        self.assertEqual(carry_state.decision_state(rec, moved), "stale")
        self.assertEqual(carry_state.stale_cause(rec, moved), "code")
        self.assertIn(ARCH_HASH,
                      carry_state.finalize_counts(moved)["outstanding_cw_hashes"])

    def test_band_change_reopens(self):
        self._band_change_scenario()

    def test_line_move_reopens(self):
        s = line_move_state()
        rec = record_of(s, HA)
        self.assertEqual(rec["snapshot"]["canonical_line_content"],
                         s["decisions"][HA]["evidence"]["canonical_line_content"])
        self.assertEqual(carry_state.decision_state(rec, s), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s), "code")
        self.assertIn(HA, carry_state.finalize_counts(s)["outstanding_cw_hashes"])

    def test_unchanged_decided_never_reopens(self):
        s = unchanged_state()
        rec = record_of(s, HA)
        self.assertEqual(carry_state.decision_state(rec, s), "current")
        self.assertIsNone(carry_state.stale_cause(rec, s))
        c = carry_state.finalize_counts(s)
        self.assertNotIn(HA, c["outstanding_cw_hashes"])
        self.assertNotIn(HA, c["unacknowledged_medium_hashes"])
        self.assertNotIn(HA, [p["stable_hash"] for p in carry_state.pending(s)])

    def test_pre47_record_closes_as_before(self):
        s = pre47_state()   # decided as medium; snapshot band is now warning
        rec = record_of(s, HA)
        self.assertNotEqual(rec["snapshot"]["band"],
                            s["decisions"][HA]["band"])
        self.assertEqual(carry_state.decision_state(rec, s), "current")
        self.assertTrue(carry_state.is_closed(rec, s, None))
        self.assertNotIn(HA, carry_state.finalize_counts(s)["outstanding_cw_hashes"])

    def test_non_dict_decision_closes_as_before(self):
        s = ba_state()
        s["decisions"] = {HA: "dismiss"}
        self.assertEqual(carry_state.decision_state(record_of(s, HA), s),
                         "current")

    def test_legacy_ack_closes_as_before(self):
        s = load_fixture()
        self.assertEqual(s["medium_acknowledgments"], {})
        c = carry_state.finalize_counts(s)
        self.assertEqual((c["outstanding_cw"], c["unacknowledged_medium"]), (1, 1))
        s["medium_acknowledgments"] = {BUGS_HASH: {"decision": "dismiss",
                                                   "reason": "r", "at_pass": 1}}
        # A legacy ack is unconditional even after a band/line change.
        fixture_row(s, BUGS_HASH)["line"] = 99
        rec = record_of(s, BUGS_HASH)
        self.assertEqual(carry_state.decision_state(rec, s), "current")
        c = carry_state.finalize_counts(s)
        self.assertEqual((c["outstanding_cw"], c["unacknowledged_medium"]), (1, 0))

    def test_no_decision_is_none(self):
        s = ba_state()
        rec = record_of(s, HA)
        self.assertIsNone(carry_state.decision_state(rec, s))
        self.assertIsNone(carry_state.stale_cause(rec, s))

    def test_history_kept_on_replace(self):
        first = dismiss(ba_state(), HA, reason="first")
        self.assertNotIn("history", first["decisions"][HA])
        s = dismiss(first, HA, at_pass=3, reason="second")
        self.assertEqual(s["decisions"][HA]["history"], [first["decisions"][HA]])
        third = dismiss(s, HA, at_pass=4, reason="third")
        self.assertEqual(third["decisions"][HA]["history"],
                         [{k: v for k, v in s["decisions"][HA].items()
                           if k != "history"}, first["decisions"][HA]])

    def test_snapshotless_resumed_severity_change_reopens(self):
        self._snapshotless_scenario()

    def test_snapshotless_then_snapshot_added_stays_current(self):
        s = snapshotless_decided_state()
        row = fixture_row(s, ARCH_HASH)
        row["snapshot"] = dict(
            {k: row[k] for k in carry_state.EVIDENCE_KEYS}, at_pass=3)
        rec = record_of(s, ARCH_HASH)
        self.assertEqual(carry_state.decision_state(rec, s), "current")
        self.assertNotIn(ARCH_HASH,
                         carry_state.finalize_counts(s)["outstanding_cw_hashes"])

    def test_null_evidence_is_stale_absent_is_legacy(self):
        self._null_evidence_scenario()
        s = null_evidence_state()
        del s["decisions"][HA]["evidence"]
        rec = record_of(s, HA)
        self.assertEqual(carry_state.decision_state(rec, s), "current")
        self.assertNotIn(HA, carry_state.finalize_counts(s)["outstanding_cw_hashes"])
        for name, ev in (("missing keys", {"file": F}),
                         ("list", []), ("string", "x")):
            with self.subTest(name):
                s = null_evidence_state()
                s["decisions"][HA]["evidence"] = ev
                rec = record_of(s, HA)
                self.assertEqual(carry_state.decision_state(rec, s), "stale")
                self.assertEqual(carry_state.stale_cause(rec, s), "code")

    def test_pending_lists_stale_decided(self):
        s = band_change_state()
        self.assertEqual(carry_state.pending(s),
                         [{"stable_hash": HA, "since_pass": 1}])

    def test_rehash_new_hash_open_orphan_kept(self):
        s = rehash_state()
        orphan = json.dumps(s["decisions"][HA], sort_keys=True)
        self.assertEqual(carry_state.finalize_counts(s)["outstanding_cw_hashes"],
                         [HC])
        out = dismiss(s, HC, at_pass=2)
        self.assertEqual(json.dumps(out["decisions"][HA], sort_keys=True), orphan)

    # ---- contrast subtests: each mutant must make its scenario fail ------ #
    def test_contrast_always_current_mutant(self):
        self._band_change_scenario()

        def mutant(record, state):
            h = record["stable_hash"]
            if h in state.get("decisions", {}) or h in state.get(
                    "medium_acknowledgments", {}):
                return "current"
            return None
        with self.subTest("contrast: always-current"):
            with mock.patch.object(carry_state, "decision_state", mutant):
                with self.assertRaises(AssertionError):
                    self._band_change_scenario()

    def test_contrast_band_blind_mutant(self):
        real = real_decision_state()

        def mutant(record, state):
            result = real(record, state)
            if result != "stale":
                return result
            ev = state["decisions"][record["stable_hash"]].get("evidence")
            cur = carry_state._evidence_of(record)
            keys = ("file", "line", "canonical_line_content")
            if isinstance(ev, dict) and all(ev.get(k) == cur[k] for k in keys):
                return "current"
            return "stale"
        s = band_change_state()
        rec = record_of(s, HA)
        with self.subTest("contrast: band-blind"):
            self.assertEqual(real(rec, s), "stale")
            self.assertEqual(mutant(rec, s), "current")
            with mock.patch.object(carry_state, "decision_state", mutant):
                with self.assertRaises(AssertionError):
                    self._band_change_scenario()

    def test_contrast_absent_vs_null_legacy_gate_mutant(self):
        real = real_decision_state()

        def mutant(record, state):
            d = state.get("decisions", {}).get(record["stable_hash"])
            if d is not None and not (isinstance(d, dict) and isinstance(
                    d.get("evidence"), dict)):
                return "current"
            return real(record, state)
        s = null_evidence_state()
        rec = record_of(s, HA)
        with self.subTest("contrast: isinstance legacy gate"):
            self.assertEqual(real(rec, s), "stale")
            self.assertEqual(mutant(rec, s), "current")
            with mock.patch.object(carry_state, "decision_state", mutant):
                with self.assertRaises(AssertionError):
                    self._null_evidence_scenario()

    def test_contrast_null_evidence_derivation_mutant(self):
        real = carry_state._evidence_of

        def mutant(record):
            if not isinstance(record.get("snapshot"), dict):
                return None
            return real(record)
        self._snapshotless_scenario()
        with self.subTest("contrast: evidence None when snapshotless"):
            with mock.patch.object(carry_state, "_evidence_of", mutant):
                with self.assertRaises(AssertionError):
                    self._snapshotless_scenario()


def old_closed(record, state, last):
    """The pre-47 closure rule, transcribed: closed by hash alone."""
    h = record["stable_hash"]
    if h in state.get("decisions", {}) or h in state.get(
            "medium_acknowledgments", {}):
        return True
    return carry_state._fix_closes(record, state, last, None)


ROLLBACK_FIXTURES = (
    ("band change", band_change_state),
    ("line move", line_move_state),
    ("unchanged", unchanged_state),
    ("history replace", history_state),
    ("re-hash orphan", rehash_state),
    ("snapshotless severity change", snapshotless_severity_state),
    ("null evidence", null_evidence_state),
    ("fixture as shipped", load_fixture),
    ("pre-47 decisions", pre47_state),
)


def disagreements(state):
    last = carry_state._check_state(state)[0]
    return [r["stable_hash"] for r in carry_state.open_findings(state)
            if old_closed(r, state, last)
            != carry_state._closed(r, state, last, None)]


def uncovered(predicate):
    """Fixture names where the old and new rules disagree but `predicate`
    would NOT quarantine the state."""
    return [name for name, build in ROLLBACK_FIXTURES
            if disagreements(build()) and not predicate(build())]


class TestRollbackQuarantine(unittest.TestCase):
    """Reverting carry_state.py is safe only after quarantining every state
    where the pre-47 and post-47 closure rules disagree."""

    def test_quarantine_covers_every_disagreement(self):
        self.assertEqual(uncovered(carry_state.has_evidence_bound_decisions), [])
        # Non-vacuity: the band-change fixture really disagrees.
        self.assertEqual(disagreements(band_change_state()), [HA])

    def test_legacy_states_not_quarantined(self):
        self.assertFalse(carry_state.has_evidence_bound_decisions(load_fixture()))
        self.assertFalse(carry_state.has_evidence_bound_decisions(pre47_state()))
        for bad in (None, [], {"decisions": []}, {"decisions": {HA: "x"}}):
            with self.subTest(repr(bad)):
                self.assertFalse(carry_state.has_evidence_bound_decisions(bad))

    def test_predicate_matches_absent_vs_null_rule(self):
        s = null_evidence_state()
        self.assertTrue(carry_state.has_evidence_bound_decisions(s))
        self.assertEqual(disagreements(s), [HA])

        def dict_only(state):
            return any(isinstance(d, dict) and isinstance(d.get("evidence"), dict)
                       for d in state.get("decisions", {}).values())
        with self.subTest("contrast: dict-evidence predicate"):
            self.assertIn("null evidence", uncovered(dict_only))

    def test_contrast_never_quarantine(self):
        with self.subTest("contrast: lambda s: False"):
            self.assertIn("band change", uncovered(lambda s: False))
        self.assertEqual(uncovered(carry_state.has_evidence_bound_decisions), [])

    def test_history_only_record_is_quarantined(self):
        s = ba_state()
        s["decisions"] = {HA: dict(pre47_record(), history=[pre47_record()])}
        self.assertTrue(carry_state.has_evidence_bound_decisions(s))

    def test_rollback_paragraph_present(self):
        doc = carry_state.__doc__
        for needle in ("ROLLBACK", "quarantine-47",
                       "has_evidence_bound_decisions"):
            self.assertIn(needle, doc)


ALLOWED_KEY_WRITES = {"record_decisions": {"decisions"},
                      "record_fix_verdicts": {"fix_verdicts"}}
FROZEN_KEYS = {"passes", "medium_acknowledgments"}
MUTATORS = {"setdefault", "pop", "popitem", "update", "clear", "append",
            "extend", "insert", "remove", "__setitem__", "__delitem__"}


def _chain_keys(node):
    """String keys along a subscript/attribute chain: x["a"][h]["b"] -> a, b."""
    keys = []
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        if isinstance(node, ast.Subscript):
            sl = node.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                keys.append(sl.value)
        node = node.value
    return keys


def string_key_writes(source):
    """[(enclosing function or '<module>', key)] for every string-keyed write."""
    tree = ast.parse(source)
    found = []

    def visit(node, fn):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn = node.name
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        elif isinstance(node, ast.Delete):
            targets = node.targets
        for t in targets:
            for sub in ast.walk(t):
                if isinstance(sub, ast.Subscript):
                    for k in _chain_keys(sub):
                        found.append((fn, k))
                    break
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in MUTATORS):
            for k in _chain_keys(node.func.value):
                found.append((fn, k))
            if (node.func.attr in ("setdefault", "pop", "__setitem__",
                                   "__delitem__") and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                    and node.args[0].value in FROZEN_KEYS
                    | {"decisions", "fix_verdicts"}):
                found.append((fn, node.args[0].value))
        for child in ast.iter_child_nodes(node):
            visit(child, fn)

    visit(tree, "<module>")
    return found


def writer_lock_violations(source):
    bad = []
    for fn, key in string_key_writes(source):
        if key in FROZEN_KEYS or key not in ALLOWED_KEY_WRITES.get(fn, set()):
            bad.append((fn, key))
    return bad


class TestWriterLock(unittest.TestCase):
    def _source(self):
        with open(CARRY_STATE_PY, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_writer_lock_real_module(self):
        src = self._source()
        self.assertEqual(writer_lock_violations(src), [])
        writes = set(string_key_writes(src))
        # Non-vacuity: both owners are actually seen writing their family.
        self.assertIn(("record_decisions", "decisions"), writes)
        self.assertIn(("record_fix_verdicts", "fix_verdicts"), writes)

    def test_writer_lock_trips_under_mutation(self):
        src = self._source()
        anchor = "def record_fix_verdicts("
        self.assertEqual(src.count(anchor), 1)
        head, tail = src.split(anchor, 1)
        sig, body = tail.split("\n", 1)
        self.assertTrue(sig.rstrip().endswith(":"),
                        "record_fix_verdicts signature must fit one line")
        injections = {
            "passes in a writer": '    state["passes"] = []\n',
            "acks in a writer": '    state["medium_acknowledgments"][h] = 1\n',
            "wrong family": '    state["decisions"] = {}\n',
            "nested passes": '    state["passes"][0]["findings"] = []\n',
            "setdefault passes": '    state.setdefault("passes", [])\n',
            "del passes": '    del state["passes"]\n',
            "aug-assign": '    state["fix_verdicts"]["n"] += 1\n'
                          '    state["passes"] += []\n',
        }
        for name, line in injections.items():
            with self.subTest(name):
                mutated = head + anchor + sig + "\n" + line + body
                self.assertNotEqual(writer_lock_violations(mutated), [])
        with self.subTest("module-level write"):
            mutated = src + '\n_S = {}\n_S["decisions"] = {}\n'
            self.assertNotEqual(writer_lock_violations(mutated), [])
        with self.subTest("passes in a reader"):
            mutated = src.replace("def pending(state):\n",
                                  'def pending(state):\n'
                                  '    state["passes"] = []\n', 1)
            self.assertNotEqual(mutated, src)
            self.assertNotEqual(writer_lock_violations(mutated), [])


# --------------------------------------------------------------------------- #
# Orchestrator compatibility (R6).
# --------------------------------------------------------------------------- #
def count_unfixed_cw(state):
    """Verbatim body of `count_unfixed_cw` from
    ~/.claude/plugins/cache/julian-orchestrator/julian-orchestrator/0.10.0/
    scripts/orchestrator-cmd.sh L1558-1575 (the python3 heredoc), with the file
    read replaced by the parsed state.

    It ignores `decisions` and `fix_verdicts`, so an owner-decided C/W finding
    still counts there. That over-count fails toward blocking; fixing it is an
    orchestrator-repo follow-up, not this module's job.
    """
    try:
        s = state
        p = s["passes"][-1]["findings"]      # raises if passes absent/empty -> blocking
        return len([f for f in p
                    if f.get("band") in ("critical", "warning")
                    and f.get("status") != "fixed-since-last"])
    except Exception:
        return 1                             # cannot confirm clean -> treat as >0


class TestOrchestratorCompat(unittest.TestCase):
    def test_orchestrator_compat_count_unchanged_by_writes(self):
        s = load_fixture()
        before = count_unfixed_cw(s)
        self.assertEqual(before, 1)
        d = carry_state.record_decisions(s, defer_payload())
        v = carry_state.record_fix_verdicts(d, verdict_payload())
        self.assertEqual(count_unfixed_cw(d), before)
        self.assertEqual(count_unfixed_cw(v), before)

    def test_orchestrator_compat_pass1_scope_untouched(self):
        s = load_fixture()
        d = carry_state.record_decisions(s, defer_payload())
        v = carry_state.record_fix_verdicts(d, verdict_payload())
        for key in ("head_sha", "diff_range"):
            self.assertEqual(v["passes"][0][key], s["passes"][0][key])


# --------------------------------------------------------------------------- #
# Phase-45 end-to-end replay through the real modules: score.py ->
# (Phase 4.5 pass append) -> carry_state.py -> finalize_gate.py.
# --------------------------------------------------------------------------- #
import score  # noqa: E402
import state_shape  # noqa: E402
import test_score as ts  # noqa: E402  (shared envelope builders; no classes imported)

FUTURE = state_shape.load_schema("future")
PLUGIN_DIR = os.path.normpath(os.path.join(HERE, ".."))
# An `audit` row (regenerated each pass by score.py) lacks these five scored
# keys under the future schema. This gap predates Phase 46 and is pinned in
# test_state_shape.py (PHASE45_FUTURE_REASONS = 2 rows x 5 keys).
AUDIT_ROW_REASONS = ["missing required key in finding: %s" % k
                     for k in ("severity", "agent", "agent_confidence",
                               "problem", "source_window")]
ROW_STATUSES = {"new", "persisted", "needs-recheck", "audit"}
B_FILE = "src/a.py"


def audit_reasons(state):
    """The only schema reasons a produced state may have: 5 per audit row."""
    n = sum(1 for p in state["passes"] for f in p["findings"]
            if f.get("status") == "audit")
    return sorted(AUDIT_ROW_REASONS * n)


def append_pass(state, scored, pass_number, head_sha):
    """Phase 4.5 (45-persist.md): a NEW state with one pass entry appended —
    the nine required keys, `resolved` only when score.py returned some,
    codex off. Never mutates `state`."""
    new = copy.deepcopy(state)
    prev = new["passes"][-1]["head_sha"] if new["passes"] else "base"
    entry = {
        "pass_number": pass_number,
        "head_sha": head_sha,
        "timestamp": "2026-10-02T00:00:%02dZ" % pass_number,
        "mode": "deep",
        "diff_range": "%s..%s" % (prev, head_sha),
        "agents_run": ["bugs", "architecture", "security"],
        "findings": copy.deepcopy(scored["findings"]),
        "filtered": copy.deepcopy(scored["filtered"]),
        "codex": {"status": "off", "reason": None, "verdict": None,
                  "findings": 0},
    }
    if scored.get("resolved"):
        entry["resolved"] = copy.deepcopy(scored["resolved"])
    new["passes"].append(entry)
    return new


def e2e_gate(state, head_blobs=None):
    counts = carry_state.finalize_counts(state, head_blobs)
    return finalize_gate.decide({
        "state_file_present": True, "noninteractive": False,
        "pr_mode": False, "range_mode": False,
        "outstanding_cw": counts["outstanding_cw"],
        "unacknowledged_medium": counts["unacknowledged_medium"]})["action"]


def carry_set(state):
    """05-state.md step 2: the hashes the next pass carries forward."""
    return {f["stable_hash"] for f in state["passes"][-1]["findings"]
            if f.get("status") in carry_state.OPEN_STATUSES}


def pass2_state():
    """The fixture as the new scorer would have written pass 2: each carried
    lead with a snapshot at pass 2 (the fixture predates `snapshot`)."""
    s = load_fixture()
    for f in s["passes"][-1]["findings"]:
        if f["stable_hash"] in (ARCH_HASH, BUGS_HASH):
            f["snapshot"] = {"at_pass": 2, "file": f["file"], "line": f["line"],
                             "canonical_line_content": f["canonical_line_content"],
                             "band": f["band"]}
    return s


def next_env(state, pass_number, **over):
    """The next pass's score.py envelope from `state` (HEAD unchanged; no
    recheck requests or verdicts unless given)."""
    env = ts._pass3_envelope(recheck_requests=[], verdicts=[],
                             pass_number=pass_number,
                             carryforward=ts._p45_next_cf(state["passes"][-1]))
    env.update(over)
    return env


def fix_verdict(head_blob, verified_blob="blob-a"):
    """05-state.md's $FIX_VERDICTS_PREV entry for arch-001, forwarded."""
    return {"source": "fix-obsolete", "stable_hash": ARCH_HASH, "agent": "fix",
            "verdict": "obsolete", "at_pass": 2, "head_sha": "4a5ee6c0",
            "reason": "already rewritten", "verified_blob": verified_blob,
            "head_blob": head_blob}


def bind_blobs(state, results, pre, post, pre_clean=None, post_clean=None):
    """50-fix-loop.md Step B rule 2: the files whose obsolete verdict may be
    recorded — named by an obsolete result, byte-identical across the batch,
    clean against HEAD at both samples, not touched by an applied fix."""
    files = {f["stable_hash"]: f["file"] for f in state["passes"][-1]["findings"]}
    touched = {p for r in results if r.get("status") == "applied"
               for p in r.get("files_touched", [])}
    out = {}
    for r in results:
        f = files.get(r.get("id"))
        if r.get("status") != "obsolete" or f is None or f not in pre:
            continue
        if post.get(f) != pre[f] or f in touched:
            continue
        if not (pre_clean or {}).get(f, True) or not (post_clean or {}).get(f, True):
            continue
        out[f] = pre[f]
    return out


def passes_json(state):
    return json.dumps(state["passes"], sort_keys=True)


def decide(state, at_pass, *entries):
    """record_decisions with (hash, decision) pairs; asserts acceptance."""
    payload = {"at_pass": at_pass, "decisions": [
        {"stable_hash": h, "decision": d, "reason": "owner: " + d}
        for h, d in entries]}
    out = carry_state.record_decisions(state, payload)
    assert out is not None, payload
    return out


def ab_pipeline(conf_a=60, min_confidence=70):
    """Synthetic three passes at ONE site: A alone (pass 1); A carried + a new
    B absorbs it (pass 2, A's obligation sidecar on B's row); B resolves on
    recheck (pass 3) while A is below this pass's filters.
    -> (states [s1, s2, s3], results [r1, r2, r3], HA, HB)."""
    A = ts._ko_find("A", "security", 10, conf_a, "inj A", "a_line")
    s0 = {"medium_acknowledgments": {}, "passes": []}
    r1 = score.run(ts._hl_env([A], ts._KO_RANGES, pass_number=1, head_sha="h1"))
    s1 = append_pass(s0, r1, 1, "h1")
    HA = r1["findings"][0]["stable_hash"]
    B = ts._ko_find("B", "bugs", 11, 90, "logic B", "b_line",
                    category="logic-error")
    r2 = score.run(ts._hl_env(
        [B], ts._KO_RANGES, pass_number=2, head_sha="h2",
        carryforward=ts._ko_next_cf(s1["passes"][-1], {"security": "a_line"})))
    s2 = append_pass(s1, r2, 2, "h2")
    rowB = r2["findings"][0]
    HB = rowB["stable_hash"]
    heads = {"security": "a_line", "bugs": "b_line_edited"}
    env3 = ts._hl_env([], {}, pass_number=3, head_sha="h3",
                      carryforward=ts._ko_next_cf(s2["passes"][-1], heads),
                      recheck_requests=[ts._ko_req("TB", rowB, HB)],
                      verdicts=[ts._p45_recheck("TB", "bugs")])
    if min_confidence is not None:
        env3["min_confidence"] = min_confidence
    r3 = score.run(env3)
    s3 = append_pass(s2, r3, 3, "h3")
    return [s1, s2, s3], [r1, r2, r3], HA, HB


class TestPhase45EndToEnd(unittest.TestCase):
    def assert_schema(self, state):
        self.assertEqual(sorted(state_shape.check_state(state, FUTURE)),
                         audit_reasons(state))

    def test_fixture_is_blocked_today(self):
        s = load_fixture()
        self.assertEqual(sorted(state_shape.check_state(s, FUTURE)),
                         audit_reasons(s))
        self.assertEqual(len(audit_reasons(s)), 10)
        self.assertEqual(e2e_gate(s), "outstanding-to-phase-5")

    def test_recheck_path_reaches_write(self):
        s = load_fixture()
        r = score.run(ts._pass3_envelope())
        new = append_pass(s, r, 3, "50f9932e")
        self.assert_schema(new)
        self.assertEqual(e2e_gate(new), "write")
        resolved = new["passes"][2]["resolved"]
        self.assertEqual(len(resolved), 2)
        self.assertEqual({x["stable_hash"] for x in resolved},
                         {ARCH_HASH, BUGS_HASH})
        for x in resolved:
            self.assertEqual(x["resolution"]["source"], "recheck")
        self.assertEqual(passes_json(dict(new, passes=new["passes"][:2])),
                         passes_json(s))

    def test_fix_obsolete_without_rerun_reaches_write(self):
        s = load_fixture()
        v = carry_state.record_fix_verdicts(s, {
            "at_pass": 2, "head_sha": "4a5ee6c0", "sent": [ARCH_HASH],
            "results": [{"id": ARCH_HASH, "status": "obsolete",
                         "summary": "already rewritten"}],
            "blobs": {ARCH_FILE: "blob-a"}})
        blobs = {ARCH_FILE: "blob-a"}
        c = carry_state.finalize_counts(v, blobs)
        self.assertEqual((c["outstanding_cw"], c["unacknowledged_medium"]), (0, 1))
        self.assertEqual(c["verified_obsolete_hashes"], [ARCH_HASH])
        self.assertEqual(e2e_gate(v, blobs), "medium-ack-loop")
        d = decide(v, 2, (BUGS_HASH, "defer"))
        self.assertEqual(e2e_gate(d, blobs), "write")
        self.assertEqual(passes_json(d), passes_json(s))

    def test_fix_obsolete_then_intervening_edit_stays_blocked(self):
        s = load_fixture()
        v = carry_state.record_fix_verdicts(s, {
            "at_pass": 2, "head_sha": "4a5ee6c0", "sent": [ARCH_HASH],
            "results": [{"id": ARCH_HASH, "status": "obsolete",
                         "summary": "already rewritten"}],
            "blobs": {ARCH_FILE: "blob-a"}})
        # (a) direct Finalize after an edit to that file (or with no blobs).
        for head_blobs in ({ARCH_FILE: "blob-b"}, None):
            with self.subTest(direct_finalize=head_blobs):
                c = carry_state.finalize_counts(v, head_blobs)
                self.assertEqual(c["outstanding_cw"], 1)
                self.assertEqual(c["verified_obsolete_hashes"], [])
                self.assertEqual(e2e_gate(v, head_blobs), "outstanding-to-phase-5")
        # (b) rerun: Phase 0.5 forwards the verdict with HEAD's current blob.
        with self.subTest("rerun after edit"):
            r = score.run(next_env(v, 3, verdicts=[fix_verdict("blob-b")]))
            self.assertIn(ARCH_HASH, [f["stable_hash"] for f in r["findings"]])
            self.assertEqual([x["reason"] for x in ts._verdict_rejections(r)],
                             ["verdict: evidence changed since verification"])
            self.assertNotIn("resolved", r)
            new = append_pass(v, r, 3, "50f9932e")
            self.assert_schema(new)
            self.assertNotEqual(e2e_gate(new), "write")
            self.assertNotEqual(e2e_gate(new, {ARCH_FILE: "blob-a"}), "write")
        # (c) the same rerun with the blob unchanged resolves arch-001.
        with self.subTest("rerun, blob unchanged"):
            r = score.run(next_env(v, 3, verdicts=[fix_verdict("blob-a")]))
            self.assertNotIn(ARCH_HASH, [f["stable_hash"] for f in r["findings"]])
            arch = [x for x in r["resolved"] if x["stable_hash"] == ARCH_HASH]
            self.assertEqual(len(arch), 1)
            self.assertEqual(arch[0]["resolution"]["source"], "fix-obsolete")
            self.assertEqual(arch[0]["resolution"]["head_sha"], "4a5ee6c0")
            self.assertEqual(arch[0]["resolution"]["verified_blob"], "blob-a")
            new = append_pass(v, r, 3, "50f9932e")
            self.assert_schema(new)
            self.assertNotIn(ARCH_HASH,
                             carry_state.finalize_counts(new)["outstanding_cw_hashes"])

    def test_fix_obsolete_unbound_when_same_batch_rewrote_file(self):
        s = load_fixture()
        results = [{"id": ARCH_HASH, "status": "obsolete",
                    "summary": "already rewritten"},
                   {"id": BUGS_HASH, "status": "applied", "commit_sha": "c1",
                    "files_touched": [ARCH_FILE,
                                      "plugins/vibe-check/phases/review/20-selection.md"]}]
        pre = {ARCH_FILE: "blob-a"}
        post = {ARCH_FILE: "blob-b"}
        blobs = bind_blobs(s, results, pre, post)
        self.assertEqual(blobs, {})
        payload = {"at_pass": 2, "head_sha": "c1", "sent": [ARCH_HASH, BUGS_HASH],
                   "results": results, "blobs": blobs}
        v = carry_state.record_fix_verdicts(s, payload)
        self.assertFalse(v.get("fix_verdicts"))
        self.assertEqual(passes_json(v), passes_json(s))
        self.assertEqual(e2e_gate(v, {ARCH_FILE: "blob-b"}), "outstanding-to-phase-5")
        # Each exclusion leg alone is load-bearing.
        self.assertEqual(bind_blobs(s, results[:1], pre, post), {})
        self.assertEqual(bind_blobs(s, results, pre, pre), {})
        self.assertEqual(bind_blobs(s, results[:1], pre, pre), pre)
        # Contrast: the post-batch blob wrongly bound WOULD close the hash.
        with self.subTest("wrongly bound"):
            bad = carry_state.record_fix_verdicts(
                s, dict(payload, blobs={ARCH_FILE: "blob-b"}))
            self.assertEqual(bad["fix_verdicts"][ARCH_HASH]["verified_blob"], "blob-b")
            c = carry_state.finalize_counts(bad, {ARCH_FILE: "blob-b"})
            self.assertNotIn(ARCH_HASH, c["outstanding_cw_hashes"])
        prose = read_prose("phases/review/50-fix-loop.md")
        for needle in ("PRE_BLOBS", "POST_BLOBS", "files_touched"):
            self.assertIn(needle, prose)

    def test_fix_obsolete_unbound_when_working_tree_dirty(self):
        s = load_fixture()
        pre = post = {ARCH_FILE: "blob-a"}
        obsolete = {"id": ARCH_HASH, "status": "obsolete",
                    "summary": "gone in working tree"}
        cases = {
            "dirty before the batch": ([obsolete], {ARCH_FILE: False}, None),
            "dirty after an errored fix": (
                [obsolete, {"id": BUGS_HASH, "status": "errored",
                            "summary": "edit failed"}],
                None, {ARCH_FILE: False}),
        }
        for name, (results, pre_clean, post_clean) in cases.items():
            with self.subTest(name):
                blobs = bind_blobs(s, results, pre, post, pre_clean, post_clean)
                self.assertEqual(blobs, {})
                v = carry_state.record_fix_verdicts(s, {
                    "at_pass": 2, "head_sha": "50f9932e", "sent": [ARCH_HASH],
                    "results": [obsolete], "blobs": blobs})
                self.assertFalse(v.get("fix_verdicts"))
                self.assertEqual(passes_json(v), passes_json(s))
                # The defect is restored in the working tree; HEAD is still
                # blob-a and clean: nothing closed it.
                self.assertEqual(e2e_gate(v, {ARCH_FILE: "blob-a"}),
                                 "outstanding-to-phase-5")
        with self.subTest("contrast: clean rule skipped"):
            v = carry_state.record_fix_verdicts(s, {
                "at_pass": 2, "head_sha": "50f9932e", "sent": [ARCH_HASH],
                "results": [obsolete], "blobs": {ARCH_FILE: "blob-a"}})
            self.assertEqual(v["fix_verdicts"][ARCH_HASH]["verified_blob"], "blob-a")
            self.assertEqual(carry_state.finalize_counts(
                v, {ARCH_FILE: "blob-a"})["outstanding_cw"], 0)
        with self.subTest("dirty at consumption"):
            v = carry_state.record_fix_verdicts(s, {
                "at_pass": 2, "head_sha": "50f9932e", "sent": [ARCH_HASH],
                "results": [obsolete], "blobs": {ARCH_FILE: "blob-a"}})
            # Finalize omits a dirty file from $BLOBFILE.
            self.assertEqual(e2e_gate(v, {}), "outstanding-to-phase-5")
            # The rerun reports head_blob null for a dirty file.
            r = score.run(next_env(v, 3, verdicts=[fix_verdict(None)]))
            self.assertEqual([x["reason"] for x in ts._verdict_rejections(r)],
                             ["verdict: evidence changed since verification"])
            self.assertIn(ARCH_HASH, [f["stable_hash"] for f in r["findings"]])
        fix_loop = read_prose("phases/review/50-fix-loop.md")
        for needle in ("PRE_CLEAN", "POST_CLEAN", "git diff --quiet HEAD --",
                       "git diff --cached --quiet --"):
            self.assertIn(needle, fix_loop)
        for path in ("phases/review/05-state.md", "phases/shared/90-finalize.md"):
            prose = read_prose(path)
            self.assertIn("git diff --quiet HEAD --", prose, path)
            self.assertIn("git diff --cached --quiet --", prose, path)

    def test_absorbed_member_keeps_blocking_after_lead_resolved(self):
        variants = {
            # A stored warning (conf 60); pass 3 raises min_confidence.
            "below-min-confidence": (60, 70, "warning",
                                     "outstanding_cw_hashes",
                                     "outstanding-to-phase-5"),
            # A stored medium (conf 52); pass 3 drops it sub-threshold.
            "sub-threshold": (52, None, "medium",
                              "unacknowledged_medium_hashes",
                              "medium-ack-loop"),
        }
        for reason, (conf, min_conf, band, key, action) in variants.items():
            with self.subTest(reason):
                (s1, s2, s3), (r1, r2, r3), HA, HB = ab_pipeline(conf, min_conf)
                self.assertNotEqual(HA, HB)
                rowB = r2["findings"][0]
                self.assertEqual(len(r2["findings"]), 1)
                self.assertEqual(rowB["members"][1]["obligation"]["stable_hash"], HA)
                self.assertEqual(count_unfixed_cw(s2), 1)
                self.assertNotEqual(e2e_gate(s2), "write")
                self.assertEqual([x["stable_hash"] for x in r3["resolved"]], [HB])
                rows = [f for f in r3["findings"] if f["stable_hash"] == HA]
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["kept_open"], reason)
                self.assertEqual(rows[0]["band"], band)
                counts = carry_state.finalize_counts(s3)
                self.assertEqual(counts[key], [HA])
                self.assertEqual(e2e_gate(s3), action)
                self.assertIn(HA, [p["stable_hash"] for p in carry_state.pending(s3)])
                for st in (s1, s2, s3):
                    self.assert_schema(st)
                d = decide(s3, 3, (HA, "defer"))
                self.assertEqual(e2e_gate(d), "write")

    def test_absorbed_member_survives_lead_closure(self):
        (_, s2, _), (_, r2, _), HA, HB = ab_pipeline(60, 70)
        rowB = r2["findings"][0]
        sidecar = rowB["members"][1]["obligation"]
        self.assertEqual(sidecar["band"], "warning")
        self.assertNotEqual(rowB["band"], "warning")
        blobs = {B_FILE: "blob-b"}
        closures = {
            "dismiss": (decide(s2, 2, (HB, "dismiss")), None),
            "defer": (decide(s2, 2, (HB, "defer")), None),
            "fix-obsolete": (carry_state.record_fix_verdicts(s2, {
                "at_pass": 2, "head_sha": "h2", "sent": [HB],
                "results": [{"id": HB, "status": "obsolete", "summary": "gone"}],
                "blobs": blobs}), blobs),
        }
        for name, (state, head_blobs) in closures.items():
            with self.subTest(name):
                self.assertEqual(passes_json(state), passes_json(s2))
                c = carry_state.finalize_counts(state, head_blobs)
                self.assertEqual(c["outstanding_cw_hashes"], [HA])
                if name == "fix-obsolete":
                    self.assertEqual(c["verified_obsolete_hashes"], [HB])
                self.assertEqual(e2e_gate(state, head_blobs), "outstanding-to-phase-5")
                self.assertEqual(carry_state.pending(state),
                                 [{"stable_hash": HA,
                                   "since_pass": sidecar["snapshot"]["at_pass"]}])
                d = decide(state, 2, (HA, "defer"))
                self.assertEqual(d["decisions"][HA]["band"], "warning")
                self.assertEqual(e2e_gate(d, head_blobs), "write")
                self.assertEqual(passes_json(d), passes_json(s2))
                self.assertEqual(count_unfixed_cw(d), count_unfixed_cw(s2))

    def test_no_verdict_no_decision_stays_blocked_three_passes(self):
        s = pass2_state()
        for n in (3, 4, 5):
            with self.subTest(pass_number=n):
                s = append_pass(s, score.run(next_env(s, n)), n, "50f9932e")
                self.assert_schema(s)
                self.assertNotEqual(e2e_gate(s), "write")
                self.assertLessEqual({ARCH_HASH, BUGS_HASH}, carry_set(s))
                for f in s["passes"][-1]["findings"]:
                    if f["stable_hash"] in (ARCH_HASH, BUGS_HASH):
                        self.assertEqual(f["snapshot"]["at_pass"], 2)
                self.assertEqual(carry_state.pending(s), [
                    {"stable_hash": h, "since_pass": 2}
                    for h in sorted((ARCH_HASH, BUGS_HASH))])

    def test_config_change_never_closes_obligation(self):
        s3 = append_pass(pass2_state(), score.run(next_env(
            pass2_state(), 3, min_confidence=100)), 3, "50f9932e")
        rows = {f["stable_hash"]: f for f in s3["passes"][-1]["findings"]
                if f["status"] != "audit"}
        self.assertEqual(set(rows), {ARCH_HASH, BUGS_HASH})
        for h, band in ((ARCH_HASH, "warning"), (BUGS_HASH, "medium")):
            self.assertEqual(rows[h]["kept_open"], "below-min-confidence")
            self.assertEqual(rows[h]["band"], band)
        self.assertEqual(e2e_gate(s3), "outstanding-to-phase-5")
        self.assertEqual(carry_state.pending(s3), [
            {"stable_hash": h, "since_pass": 2}
            for h in sorted((ARCH_HASH, BUGS_HASH))])
        self.assertLessEqual({ARCH_HASH, BUGS_HASH}, carry_set(s3))
        s4 = append_pass(s3, score.run(next_env(s3, 4, command="review")),
                         4, "50f9932e")
        rows4 = {f["stable_hash"]: f for f in s4["passes"][-1]["findings"]
                 if f["status"] != "audit"}
        self.assertEqual(rows4[BUGS_HASH]["kept_open"], "sub-threshold")
        self.assertNotIn("kept_open", rows4[ARCH_HASH])
        self.assertNotEqual(e2e_gate(s4), "write")
        for st in (s3, s4):
            self.assertEqual(count_unfixed_cw(st), 1)
            self.assert_schema(st)

    def test_defer_closes_without_blocking_and_is_listed(self):
        s3 = append_pass(pass2_state(), score.run(next_env(pass2_state(), 3)),
                         3, "50f9932e")
        self.assertEqual(e2e_gate(s3), "outstanding-to-phase-5")
        d = decide(s3, 3, (ARCH_HASH, "defer"), (BUGS_HASH, "defer"))
        self.assertEqual(e2e_gate(d), "write")
        self.assertEqual({h: (v["decision"], v["band"])
                          for h, v in d["decisions"].items()},
                         {ARCH_HASH: ("defer", "warning"),
                          BUGS_HASH: ("defer", "medium")})
        self.assertEqual(passes_json(d), passes_json(s3))

    def test_legacy_medium_only_state_unchanged(self):
        row = mk_finding("medium", "new", HA)
        acked = mk_state([mk_pass(1, [row])],
                         medium_acknowledgments={HA: {"decision": "dismiss"}})
        unacked = mk_state([mk_pass(1, [row])])
        for state, action in ((acked, "write"), (unacked, "medium-ack-loop")):
            with self.subTest(action=action):
                before = json.dumps(state, sort_keys=True)
                self.assertEqual(e2e_gate(state), action)
                self.assertEqual(json.dumps(state, sort_keys=True), before)

    def test_still_applies_keeps_blocked(self):
        s = pass2_state()
        env = next_env(s, 3,
                       recheck_requests=[ts._p45_request("R1", "arch-001"),
                                         ts._p45_request("R2", "bugs-001")],
                       verdicts=[ts._p45_recheck("R1", "architecture", "still-applies"),
                                 ts._p45_recheck("R2", "bugs", "still-applies")])
        r = score.run(env)
        self.assertNotIn("resolved", r)
        s3 = append_pass(s, r, 3, "50f9932e")
        self.assertEqual(e2e_gate(s3), "outstanding-to-phase-5")
        before = {f["stable_hash"]: f["snapshot"] for f in s["passes"][-1]["findings"]
                  if f["stable_hash"] in (ARCH_HASH, BUGS_HASH)}
        after = {f["stable_hash"]: f["snapshot"] for f in s3["passes"][-1]["findings"]
                 if f["stable_hash"] in (ARCH_HASH, BUGS_HASH)}
        self.assertEqual(after, before)

    def test_orchestrator_reads_compatible_across_pipeline(self):
        fx = load_fixture()
        recheck = append_pass(fx, score.run(ts._pass3_envelope()), 3, "50f9932e")
        obsolete = carry_state.record_fix_verdicts(fx, {
            "at_pass": 2, "head_sha": "4a5ee6c0", "sent": [ARCH_HASH],
            "results": [{"id": ARCH_HASH, "status": "obsolete", "summary": "x"}],
            "blobs": {ARCH_FILE: "blob-a"}})
        self.assertEqual(count_unfixed_cw(recheck), 0)
        # Documented over-count: the mirror ignores fix_verdicts (D-11 Noted).
        self.assertEqual(count_unfixed_cw(obsolete), 1)
        s = pass2_state()
        produced = [recheck, obsolete]
        for n, over in ((3, {"min_confidence": 100}), (4, {"command": "review"}),
                        (5, {})):
            s = append_pass(s, score.run(next_env(s, n, **over)), n, "50f9932e")
            produced.append(s)
        produced.append(decide(s, 5, (ARCH_HASH, "defer")))
        for i, st in enumerate(produced):
            with self.subTest(state=i):
                for key in ("head_sha", "diff_range"):
                    self.assertEqual(st["passes"][0][key], fx["passes"][0][key])
                for p in st["passes"]:
                    for f in p["findings"]:
                        self.assertIn(f["status"], ROW_STATUSES)


def read_prose(relpath):
    with open(os.path.join(PLUGIN_DIR, relpath), "r", encoding="utf-8") as fh:
        return fh.read()


if __name__ == "__main__":
    unittest.main()
