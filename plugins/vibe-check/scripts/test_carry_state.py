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


if __name__ == "__main__":
    unittest.main()
