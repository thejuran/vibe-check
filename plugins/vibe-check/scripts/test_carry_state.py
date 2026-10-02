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
                          "at_pass": 2, "band": "warning"})

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
                          "at_pass": 3, "band": "warning"})
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
                          "band": "warning"})
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


if __name__ == "__main__":
    unittest.main()
