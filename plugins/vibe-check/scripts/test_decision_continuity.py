"""Decision continuity: an owner's defer/dismiss stays bound to its evidence.

The contract these fixtures hold the scorer, the carry-forward state and the
finalize card to, one sentence per locked decision:
D-01: a pure line shift (code added or removed above, the flagged line itself
unchanged) does not reopen a decided finding; the decision follows the code.
D-02: a change to code immediately around the flagged line (the same window
as the independent re-check trigger: the pinned line and the 5 lines beneath
it) reopens it.
D-03: an edit elsewhere in the same file, outside that window, does not
reopen it.
D-04: Needs-verification decisions keep their rule: any change to the
recorded code body re-asks; a line shift does not.
D-05: only a band rise backed by new corroboration (a reviewer lane absent at
decision time now also reports the finding) reopens it, and the card names
that lane; a rise from the persistence bonus or the lone-lane cap lifting
alone keeps the decision.
D-06: a band drop on unchanged code does not reopen it.
D-07: defer and dismiss follow the same severity rule.
D-08: a decided finding merged into a row with other findings stays decided;
when a newcomer concern from an uncovered reviewer lane joins a decided row,
the whole row reopens once with the D-10 note, so a decision never silently
covers a different reviewer's new concern at the same spot.
D-09: when a decided row splits, every finding the decision covered stays
decided; only genuinely new findings are asked.
D-10: a row mixing a decided finding with new ones shows a short note,
"1 finding here already dismissed (your reason: ...)".
D-11: a deferred finding does not resurface on its own (no timer, no expiry).
D-12: a reopened finding's card shows the earlier decision, its reason and
what changed (code next to it / severity rise / code body).
D-13: a deferred finding that is later fixed closes normally; the deferral
does not block closure.

All fixtures are synthetic. The owner's real review state held no lost-decision
case (its only two real defers closed through a re-check on the next pass), and
no owner data is copied here: every path, title and line below is invented.

The probe split: the orchestrator, not score.py, reads HEAD files, so a
decided record that moved is located by orchestrator prose
(30-collect-score.md step 0). `relocate_decided` SIMULATES that prose so the
real scorer can be driven across passes here; the prose itself is locked
separately by its own phrase test next to the Needs-verification relocation
lock. A fixture passing here therefore proves the scorer and state side, given
an orchestrator that follows the prose, never the prose itself.

Every test runs the real chain: score.run -> append_pass -> carry_state /
batch_card / finalize_gate. Nothing is stubbed. Names that a later change
adds to carry_state are read with getattr so this module always imports.
"""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import batch_card  # noqa: E402
import carry_state  # noqa: E402
import score  # noqa: E402
from test_carry_state import append_pass, e2e_gate  # noqa: E402
from test_score import GOLDEN_DIGEST  # noqa: E402


F = "src/a.py"
OPEN = ("new", "persisted", "needs-recheck")
TITLE_A = "Unchecked return at A"
REASON = "false positive, guarded upstream"
_BAND_ORDER = ("low", "medium", "warning", "critical")


# --------------------------------------------------------------------------- #
# Harness: the real scorer driven across passes.
# --------------------------------------------------------------------------- #
def base_file(n=60):
    """`n` distinct HEAD lines: `line_NN = NN`."""
    return ["line_%02d = %d" % (i, i) for i in range(1, n + 1)]


def head_read(lines, line):
    """(canonical_line_content, canonical_window) as 30-collect-score.md step 0
    reads them at `line`: the line trailing-stripped, plus up to its next 2
    non-blank lines. (None, None) when the line is gone."""
    if (not isinstance(line, int) or isinstance(line, bool)
            or line < 1 or line > len(lines)):
        return None, None
    canon = lines[line - 1].rstrip()
    win = [canon]
    for ln in lines[line:]:
        if len(win) == 3:
            break
        if ln.strip():
            win.append(ln.rstrip())
    return canon, "\n".join(win)


def _first_nonblank(text):
    if not isinstance(text, str):
        return None
    for ln in text.split("\n"):
        if ln.strip():
            return ln
    return None


def relocate_decided(lines, entry, decided):
    """The HEAD line a carried record is read at, simulating the orchestrator
    rule for carried decided records in 30-collect-score.md step 0 (the
    paragraph that extends the Needs-verification relocation cases 1-3 to an
    ordinary record whose hash is in `$DECIDED_HASHES`).

    `entry` is a carried lead (its own `stable_hash` and stored
    `canonical_line_content`) or a member carrying an `obligation` (the
    obligation's `stable_hash`; its stored canonical line from the
    obligation's snapshot, else the first non-blank line of `current_code`).
    A record not in `decided` keeps its stored line (undecided ordinary rows
    keep the stored-line read). Lines compare with both sides `.strip()`ped:
      case 1: the stored line still holds the stored canonical -> stored line;
      case 2: exactly one match, or one match nearest-unique to the stored
              line -> that line;
      case 3: two or more matches tie for nearest -> stored line;
      case 4: no match -> stored line (an ordinary record then reads whatever
              is there, or null, as today).
    """
    line = entry.get("line")
    obligation = entry.get("obligation")
    if isinstance(obligation, dict):
        h = obligation.get("stable_hash")
        snap = obligation.get("snapshot")
        stored = snap.get("canonical_line_content") if isinstance(snap, dict) else None
        if not isinstance(stored, str):
            stored = _first_nonblank(entry.get("current_code"))
    else:
        h = entry.get("stable_hash")
        stored = entry.get("canonical_line_content")
    if h not in decided or not isinstance(stored, str) or not isinstance(line, int):
        return line
    want = stored.strip()
    if 1 <= line <= len(lines) and lines[line - 1].strip() == want:
        return line
    matches = [i + 1 for i, ln in enumerate(lines) if ln.strip() == want]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        return line
    best = min(abs(m - line) for m in matches)
    nearest = [m for m in matches if abs(m - line) == best]
    return nearest[0] if len(nearest) == 1 else line


def next_cf(state, lines, decided=frozenset()):
    """05-state.md step 2 + 30-collect-score.md step 0: the next pass's
    carry-forward from the last pass (open statuses only), each lead and each
    member given its own HEAD read at its (possibly relocated) line."""
    out = []
    for f in state["passes"][-1]["findings"]:
        if f.get("status") not in OPEN:
            continue
        e = json.loads(json.dumps(f))
        stored = e.get("line")
        e["line"] = relocate_decided(lines, e, decided)
        e["canonical_line_content"], e["canonical_window"] = head_read(
            lines, e.get("line"))
        for m in e.get("members", []):
            if (e["line"] != stored and "obligation" not in m
                    and (m.get("agent"), m.get("file"), m.get("title"),
                         m.get("line"))
                    == (e.get("agent"), e.get("file"), e.get("title"), stored)):
                # The lead's own member record moves with the lead: left at
                # the stored line it would be read there and come back as a
                # phantom row of whatever code now sits on that line.
                m["line"] = e["line"]
            else:
                m["line"] = relocate_decided(lines, m, decided)
            m["canonical_line_content"], m["canonical_window"] = head_read(
                lines, m.get("line"))
        out.append(e)
    return out


def fresh(agent, line, lines, title, conf=70, severity="warning",
          category="bug"):
    """One agent finding at `line` of `lines` (HEAD canonical resolved)."""
    code = lines[line - 1]
    return {"id": "%s-%d" % (agent, line), "file": F, "line": line,
            "title": title, "category": category, "cwe": None,
            "severity": severity, "agent_confidence": conf, "in_diff": False,
            "intent_doc_match": None, "problem": "problem of " + title,
            "current_code": code, "fix_hint": None, "why_it_matters": "w",
            "silenced_marker_nearby": False, "agent": agent,
            "source_window": ["a", "b", "c", "d", "e"],
            "canonical_line_content": code}


def run_pass(state, lines, findings, n, ranges, decided=frozenset(), **over):
    """(new state, score result) for pass `n` through the real scorer."""
    env = {"command": "deep-review", "all_mode": False, "pass_number": n,
           "changed_line_ranges": ranges,
           "carryforward": (next_cf(state, lines, decided)
                            if state["passes"] else []),
           "findings": findings}
    env.update(over)
    result = score.run(env)
    return append_pass(state, result, n, "h%d" % n), result


def target_decided(state):
    """The decided-hash list the relocation prose binds (`carry_state.py
    decided`); empty while that read does not exist."""
    read = getattr(carry_state, "decided", lambda s: None)
    return frozenset(read(state) or [])


def decide_on(state, h, kind="dismiss", reason=REASON):
    """record_decisions for hash `h` at the last pass; asserts acceptance."""
    at = state["passes"][-1]["pass_number"]
    out = carry_state.record_decisions(state, {"at_pass": at, "decisions": [
        {"stable_hash": h, "decision": kind, "reason": reason}]})
    assert out is not None, "decision refused"
    return out


def record_of(state, h):
    """The open record (row or member sidecar) with hash `h`, or None."""
    for rec in carry_state.open_findings(state) or []:
        if rec["stable_hash"] == h:
            return rec
    return None


def card_doc(state):
    """The finalize rows document, or the refusal reason (a str)."""
    doc, reason = batch_card.build_rows(state, "finalize", head_blobs={})
    return doc if doc is not None else reason


def card_rows(state):
    """The finalize card rows, or the refusal reason (a str)."""
    doc = card_doc(state)
    return doc["rows"] if isinstance(doc, dict) else doc


def card_text_full(state):
    doc = card_doc(state)
    return doc["list_text"] if isinstance(doc, dict) else doc


def card_text_compact(state):
    rows = card_rows(state)
    return (batch_card._render(rows, "finalize", compact=True)
            if isinstance(rows, list) else rows)


def row_of(state, h):
    """The last pass's finding row with hash `h`, or None."""
    for f in state["passes"][-1]["findings"]:
        if f.get("stable_hash") == h:
            return f
    return None


def card_row(state, h):
    rows = card_rows(state)
    if not isinstance(rows, list):
        return None
    for r in rows:
        if r["stable_hash"] == h:
            return r
    return None


def shift_band(state, h, step):
    """A copy of `state` with record `h`'s band and snapshot band moved `step`
    ranks (the probe's forced band move on unchanged code)."""
    s = json.loads(json.dumps(state))
    row = row_of(s, h)
    assert row is not None, "no row %s" % h[:8]
    i = _BAND_ORDER.index(row["band"]) + step
    nb = _BAND_ORDER[max(0, min(i, len(_BAND_ORDER) - 1))]
    row["band"] = nb
    row["snapshot"] = dict(row["snapshot"], band=nb)
    return s


def empty_state():
    return {"medium_acknowledgments": {}, "passes": []}


def pass1(lines, title=TITLE_A, conf=70, kind="dismiss", agent="bugs",
          line=10, **kw):
    """Pass 1: one finding at `line`, decided by the owner -> (state, hash)."""
    s1, r1 = run_pass(empty_state(), lines,
                      [fresh(agent, line, lines, title, conf=conf, **kw)], 1,
                      {F: [[1, 200]]})
    assert len(r1["findings"]) == 1, r1["filtered"]
    h = r1["findings"][0]["stable_hash"]
    return decide_on(s1, h, kind=kind), h


class _Base(unittest.TestCase):
    def _assert_band(self, state, h, band):
        rec = record_of(state, h)
        self.assertIsNotNone(
            rec, "record %s is not an open record (decision orphaned)" % h[:8])
        self.assertEqual(rec["band"], band,
                         "fixture band moved: %r != %r" % (rec["band"], band))

    def _current(self, state, h):
        rec = record_of(state, h)
        self.assertIsNotNone(
            rec, "record %s is not an open record (decision orphaned)" % h[:8])
        return rec


class TestGolden(unittest.TestCase):
    def test_stable_hash_and_golden_digest_unchanged(self):
        self.assertEqual(score.stable_hash("a.py", "  x=1", "title"),
                         GOLDEN_DIGEST)


# Band-stable inputs (Pitfall 2). With pass 1 in the diff and pass 2 not
# touching the flagged line, a lone `bugs` finding at severity "warning"
# (scored as the -8 fallback) keeps its band across the two passes at
# confidence 75 (warning -> warning). Confidence 70 is NOT stable here: it
# drops warning -> medium on a quiet pass (82 -> 77), which is R3b noise.
STABLE_CONF = 75
# R1a needs the carried row to stay above threshold after the wrong-line read
# so the scorer re-hashes it: confidence 80 (75 lands kept-open instead).
REHASH_CONF = 80
# R1b needs the row to be a kept-open sub-threshold row on pass 2: confidence
# 60 (55 is dropped already on pass 1).
KEPT_OPEN_CONF = 60
INSERTED = ["inserted_%d = 0" % i for i in range(3)]


class TestLineShift(_Base):
    """D-01, DECN-02: a pure line shift above a decided finding keeps the
    decision; the decision follows the code."""

    def _shift(self, conf, rereport=False, decided=None):
        L0 = base_file()
        s1, hA = pass1(L0, conf=conf)
        L1 = INSERTED + L0
        finds = ([fresh("bugs", 13, L1, TITLE_A, conf=conf)]
                 if rereport else [])
        dec = target_decided(s1) if decided is None else decided
        s2, _ = run_pass(s1, L1, finds, 2, {F: [[1, 3]]}, decided=dec)
        return L1, s1, s2, hA

    def test_r1a_shift_above_threshold_keeps_decision_and_hash(self):
        _, s1, s2, hA = self._shift(REHASH_CONF)
        self._assert_band(s1, hA, "warning")
        rec = self._current(s2, hA)  # today: re-hashed, decision orphaned
        self.assertEqual(rec["line"], 13)
        self.assertEqual(rec["stable_hash"], hA)
        self.assertEqual(carry_state.decision_state(rec, s2), "current")
        self.assertEqual(e2e_gate(s2, {}), "write")
        self.assertNotIn(hA, [r["stable_hash"] for r in card_rows(s2)])
        self._assert_band(s2, hA, "warning")

    def test_r1b_shift_sub_threshold_keeps_decision(self):
        _, s1, s2, hA = self._shift(KEPT_OPEN_CONF)
        self._assert_band(s1, hA, "medium")
        rec = self._current(s2, hA)
        self.assertIn("kept_open", row_of(s2, hA))
        self.assertEqual(carry_state.decision_state(rec, s2), "current")
        self.assertIsNone(carry_state.stale_cause(rec, s2))
        self._assert_band(s2, hA, "medium")

    def test_r1c_shift_with_rereport_is_one_decided_row(self):
        _, s1, s2, hA = self._shift(REHASH_CONF, rereport=True)
        self._assert_band(s1, hA, "warning")
        recs = carry_state.open_findings(s2)
        at13 = [r for r in recs if (r.get("file"), r.get("line")) == (F, 13)]
        self.assertEqual(len(at13), 1, at13)
        self.assertEqual(at13[0]["stable_hash"], hA)
        self.assertEqual(carry_state.decision_state(at13[0], s2), "current")
        phantoms = [f["stable_hash"][:8] for f in s2["passes"][-1]["findings"]
                    if f.get("line") == 10]
        self.assertEqual(phantoms, [], "phantom row at the stored line")
        self._assert_band(s2, hA, "warning")

    def test_today_orchestrator_without_relocation_is_the_reproduced_failure(
            self):
        """REPRO PIN: the same inputs with today's orchestrator (no
        relocation of decided records) lose the decision. Proves the R1
        fixture inputs reproduce on current code; retired explicitly once the
        relocation rule ships, never silently."""
        L1, s1, s2, hA = self._shift(REHASH_CONF, decided=frozenset())
        self._assert_band(s1, hA, "warning")
        rec = record_of(s2, hA)
        self.assertTrue(rec is None
                        or carry_state.decision_state(rec, s2) != "current")
        # The stored-line read re-hashed the row onto whatever sits at line 10.
        phantom = score.stable_hash(F, L1[9], TITLE_A)
        self._assert_band(s2, phantom, "medium")


class TestNearbyEdit(_Base):
    """D-02, DECN-03: an edit to the pinned line's window (the line and the 5
    beneath it, shared with the independent re-check trigger) reopens a
    decided finding whose own line is unchanged."""

    def _edit(self, at, n=2, base=None, state=None, h=None):
        L0 = base or base_file()
        if state is None:
            state, h = pass1(L0, conf=STABLE_CONF)
        L2 = list(L0)
        L2[at - 1] = "line_%02d = 'edited'" % at
        s2, _ = run_pass(state, L2, [], n, {F: [[at, at]]})
        return L2, state, s2, h

    def test_r2_edit_within_five_beneath_reopens(self):
        for offset in (1, 3, 5):
            with self.subTest(offset=offset):
                _, s1, s2, hA = self._edit(10 + offset)
                self._assert_band(s1, hA, "warning")
                self._assert_band(s2, hA, "warning")
                rec = self._current(s2, hA)
                self.assertEqual(carry_state.decision_state(rec, s2), "stale")
                self.assertEqual(carry_state.stale_cause(rec, s2), "nearby")
                self.assertEqual(row_of(s2, hA)["snapshot"].get("nearby_at"),
                                 2)
                self.assertNotEqual(e2e_gate(s2, {}), "write")
                row = card_row(s2, hA)
                self.assertIsNotNone(row, "decided row not on the card")
                self.assertEqual((row["stale"] or {}).get("cause"), "nearby")

    def test_r2_edit_six_beneath_keeps(self):
        _, s1, s2, hA = self._edit(16)
        self._assert_band(s1, hA, "warning")
        self._assert_band(s2, hA, "warning")
        rec = self._current(s2, hA)
        self.assertEqual(carry_state.decision_state(rec, s2), "current")
        self.assertNotIn("nearby_at", row_of(s2, hA)["snapshot"])

    def test_r2_edit_two_above_keeps(self):
        """The window is the literal 5 lines BENEATH the pinned line (shared
        with the Phase 56 re-check trigger): an edit 2 lines above keeps."""
        _, s1, s2, hA = self._edit(8)
        self._assert_band(s1, hA, "warning")
        self._assert_band(s2, hA, "warning")
        rec = self._current(s2, hA)
        self.assertEqual(carry_state.decision_state(rec, s2), "current")

    def test_nearby_at_carries_forward_on_quiet_pass(self):
        L2, s1, s2, hA = self._edit(11)
        self._assert_band(s1, hA, "warning")
        s2 = decide_on(s2, hA)
        s3, _ = run_pass(s2, L2, [], 3, {F: []})
        self._assert_band(s3, hA, "warning")
        rec = self._current(s3, hA)
        self.assertEqual(row_of(s3, hA)["snapshot"].get("nearby_at"), 2)
        self.assertEqual(carry_state.decision_state(rec, s3), "current")


def _gained(rec, state):
    return getattr(carry_state, "gained_lanes",
                   lambda r, s: ["<missing>"])(rec, state)


class TestSeverityDirection(_Base):
    """D-05 refinement, D-06, D-07: a drop keeps the decision; a rise reopens
    only when a reviewer lane absent at decision time now reports it."""

    def test_r3b_band_drop_keeps_decision(self):
        for kind in ("dismiss", "defer"):
            with self.subTest(kind=kind):
                L0 = base_file()
                # conf 85 is capped at warning on pass 1 by the lone-lane
                # ceiling (critical needs a second opinion).
                s1, hA = pass1(L0, conf=85, kind=kind)
                self._assert_band(s1, hA, "warning")
                s2, _ = run_pass(s1, L0, [], 2, {F: []})
                self._assert_band(s2, hA, "warning")
                s2 = shift_band(s2, hA, -1)
                self._assert_band(s2, hA, "medium")
                rec = self._current(s2, hA)
                self.assertEqual(carry_state.decision_state(rec, s2),
                                 "current")

    def test_r3a_persistence_rise_without_new_lane_keeps(self):
        L0 = base_file()
        s1, hA = pass1(L0, conf=STABLE_CONF)
        self._assert_band(s1, hA, "warning")
        s2, _ = run_pass(s1, L0, [], 2, {F: []})
        # Observed: on these band-stable inputs the band does NOT rise
        # (warning -> warning), so the rise is forced on the persisted row
        # with its attribution unchanged, exercising the rule itself.
        self._assert_band(s2, hA, "warning")
        s2 = shift_band(s2, hA, +1)
        self._assert_band(s2, hA, "critical")
        rec = self._current(s2, hA)
        self.assertEqual(rec["attribution"], ["bugs"])
        self.assertEqual(carry_state.decision_state(rec, s2), "current")
        self.assertEqual(_gained(rec, s2), [])

    def _new_lane(self):
        L0 = base_file()
        s1, hA = pass1(L0, conf=STABLE_CONF)
        # A second lane at confidence 100 / severity critical scores 100 and
        # lifts the lone-lane ceiling: the row rises warning -> critical.
        sec = fresh("security", 10, L0, TITLE_A, conf=100,
                    severity="critical", category="injection")
        s2, _ = run_pass(s1, L0, [sec], 2, {F: []})
        return s1, s2, hA

    def test_r3a_rise_with_new_lane_reopens_and_names_it(self):
        s1, s2, hA = self._new_lane()
        self._assert_band(s1, hA, "warning")
        self._assert_band(s2, hA, "critical")
        rec = self._current(s2, hA)
        self.assertIn("security", rec["attribution"])
        self.assertEqual(carry_state.decision_state(rec, s2), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s2), "severity")
        self.assertEqual(_gained(rec, s2), ["security"])
        row = card_row(s2, hA)
        self.assertIsNotNone(row)
        self.assertEqual((row["stale"] or {}).get("gained"), ["security"])

    def test_r3_decision_record_saves_attribution(self):
        L0 = base_file()
        s1, hA = pass1(L0, conf=STABLE_CONF)
        self._assert_band(s1, hA, "warning")
        s2, _ = run_pass(s1, L0, [], 2, {F: []})
        self._assert_band(s2, hA, "warning")
        self.assertEqual(s1["decisions"][hA].get("attribution"), ["bugs"])


if __name__ == "__main__":
    unittest.main()
