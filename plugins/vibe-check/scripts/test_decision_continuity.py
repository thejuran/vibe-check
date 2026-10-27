"""Decision continuity: an owner's defer/dismiss stays bound to its evidence.

The contract these fixtures hold the scorer, the carry-forward state and the
finalize card to, one sentence per locked decision:
D-01: a pure line shift (code added or removed above, the flagged line itself
unchanged) does not reopen a decided finding; the decision follows the code.
D-02: a change to code immediately around the flagged line (the pinned line
and the 5 lines above or below it (D-14), shared with the independent re-check
trigger) reopens it.
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
    Moving the matching `$RECHECK_REQUESTS` entry to the relocated line is the
    prose's responsibility, not this simulator's: these fixtures send no
    request for a relocated record, so the request line is locked by the
    prose phrase test alone.
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


def deletion_hunk_ranges(file, t):
    """The changed-line ranges for a hunk that only deletes (header `+T,0`),
    mirroring the 30-collect-score.md rule: the two new-side lines on either
    side of the deletion point, `[max(T, 1), T + 1]`."""
    return {file: [[max(t, 1), t + 1]]}


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
    if state["passes"]:
        # The orchestrator binds `$DEFERRED_HASHES` in Phase 0.5 the way it
        # binds `$DECIDED_HASHES`; the key is sent only when the read exists.
        deferred = _deferred_read(state)
        if isinstance(deferred, list):
            env["deferred_hashes"] = sorted(deferred)
    env.update(over)
    # An override of None removes the key (an envelope written before it).
    for k in [k for k, v in over.items() if v is None]:
        del env[k]
    result = score.run(env)
    return append_pass(state, result, n, "h%d" % n), result


def target_decided(state):
    """The decided-hash list the relocation prose binds (`carry_state.py
    decided`); empty while that read does not exist."""
    read = getattr(carry_state, "decided", lambda s: None)
    return frozenset(read(state) or [])


def _deferred_read(state):
    """`carry_state.py deferred` on `state`, or None while that read does not
    exist."""
    return getattr(carry_state, "deferred", lambda s: None)(state)


def target_deferred(state):
    """The deferred-hash list the orchestrator binds (`carry_state.py
    deferred`); empty while that read does not exist."""
    return frozenset(_deferred_read(state) or [])


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

    def test_without_decided_hashes_the_decision_is_lost_so_binding_must_not_degrade(
            self):
        """Without `$DECIDED_HASHES` (no relocation of decided records) the
        same inputs still lose the decision: the stored-line read re-hashes
        the row onto whatever code now sits at line 10. This is why
        05-state.md halts when the `decided` read fails instead of binding an
        empty list."""
        # Retired as a repro pin in 57-07; kept as the rationale for the fail-closed binding (57-05).
        L1, s1, s2, hA = self._shift(REHASH_CONF, decided=frozenset())
        self._assert_band(s1, hA, "warning")
        self.assertIn(hA, target_decided(s1))
        rec = record_of(s2, hA)
        self.assertTrue(rec is None
                        or carry_state.decision_state(rec, s2) != "current")
        phantom = score.stable_hash(F, L1[9], TITLE_A)
        self.assertNotEqual(phantom, hA)
        self._assert_band(s2, phantom, "medium")


class TestNearbyEdit(_Base):
    """D-02, D-14, DECN-03: an edit to the pinned line's window (the line and
    the 5 lines above or below it, shared with the independent re-check
    trigger) reopens a decided finding whose own line is unchanged."""

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

    def test_r2_edit_within_five_above_reopens(self):
        """D-14: the window is symmetric, so an edit 1, 3 or 5 lines ABOVE
        the pinned line reopens exactly as one beneath it does."""
        for offset in (1, 3, 5):
            with self.subTest(offset=offset):
                _, s1, s2, hA = self._edit(10 - offset)
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

    def test_r2_edit_six_above_keeps(self):
        _, s1, s2, hA = self._edit(4)
        self._assert_band(s1, hA, "warning")
        self._assert_band(s2, hA, "warning")
        rec = self._current(s2, hA)
        self.assertEqual(carry_state.decision_state(rec, s2), "current")
        self.assertNotIn("nearby_at", row_of(s2, hA)["snapshot"])

    def test_r8_guard_deleted_directly_above_reopens(self):
        """WR-02: the guard directly above a "guarded upstream" dismissal is
        deleted and nothing else changes. A deletion-only hunk has no new-side
        lines, so the changed range is the 30-collect-score.md mapping
        (`deletion_hunk_ranges`). Expected GREEN on the current scorer and
        state (the record relocates onto the deletion point, inside even the
        beneath-only window); what is red is the prose lock in
        test_nv_render.py, so this is a lock, not a reproduction. The
        `mapping dropped` subtest proves the fixture depends on the mapping."""
        L0 = base_file()
        s1, hA = pass1(L0, conf=STABLE_CONF)
        self.assertEqual(s1["decisions"][hA]["reason"], REASON)
        rec1 = self._current(s1, hA)
        self.assertEqual(rec1["line"], 10)
        self.assertEqual(carry_state.decision_state(rec1, s1), "current")
        L2 = list(L0)
        del L2[8]  # line 9, the guard directly above, deleted
        self.assertEqual(len(L2), len(L0) - 1)
        self.assertEqual(L2[8], L0[9])

        self._assert_band(s1, hA, "warning")
        s2, _ = run_pass(s1, L2, [], 2, deletion_hunk_ranges(F, 8),
                         decided=target_decided(s1))
        # The range's T + 1 end is the relocated flagged line itself, so the
        # scorer's changed-line scoring lifts the band (warning -> critical);
        # the nearby cause still outranks severity on the card.
        self._assert_band(s2, hA, "critical")
        rec = self._current(s2, hA)
        self.assertEqual(rec["stable_hash"], hA)
        self.assertEqual(rec["line"], 9)
        self.assertEqual(carry_state.decision_state(rec, s2), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s2), "nearby")
        self.assertEqual(row_of(s2, hA)["snapshot"].get("nearby_at"), 2)
        self.assertNotEqual(e2e_gate(s2, {}), "write")
        self.assertIn(" — code next to it changed since your decision on "
                      "pass 1 (was: dismissed — false positive, guarded "
                      "upstream)", card_text_full(s2))

        with self.subTest("mapping dropped"):
            m2, _ = run_pass(s1, L2, [], 2, {F: []},
                             decided=target_decided(s1))
            self._assert_band(m2, hA, "warning")
            mrec = self._current(m2, hA)
            self.assertEqual(mrec["line"], 9)
            self.assertEqual(carry_state.decision_state(mrec, m2), "current")
            self.assertEqual(e2e_gate(m2, {}), "write")

    def test_nearby_at_carries_forward_on_quiet_pass(self):
        L2, s1, s2, hA = self._edit(11)
        self._assert_band(s1, hA, "warning")
        s2 = decide_on(s2, hA)
        s3, _ = run_pass(s2, L2, [], 3, {F: []})
        self._assert_band(s3, hA, "warning")
        rec = self._current(s3, hA)
        self.assertEqual(row_of(s3, hA)["snapshot"].get("nearby_at"), 2)
        self.assertEqual(carry_state.decision_state(rec, s3), "current")


def new_lane_scenario():
    """Pass 1: lone `bugs` finding dismissed (warning). Pass 2: unchanged
    code; `security` now also reports it at confidence 100 / severity
    critical, which scores 100 and lifts the lone-lane ceiling, so the row
    rises warning -> critical. -> (s1, s2, hA)."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=STABLE_CONF)
    sec = fresh("security", 10, L0, TITLE_A, conf=100, severity="critical",
                category="injection")
    s2, _ = run_pass(s1, L0, [sec], 2, {F: []})
    return s1, s2, hA


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

    def test_r3a_rise_with_new_lane_reopens_and_names_it(self):
        s1, s2, hA = new_lane_scenario()
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



# --------------------------------------------------------------------------- #
# Regrouping: merges, splits and member dedup (D-08, D-09; DECN-02/03).
# --------------------------------------------------------------------------- #
TITLE_B = "Different concern B"
# A title whose hash sorts before A's at line 11, so this finding leads the
# R5 group ("Injection at C" sorts after A and does not lead).
TITLE_C = "SQL injection at C"


def joined_scenario():
    """Pass 1: `bugs` A at line 10 dismissed (warning). Pass 2: a new, weaker
    `security` concern B at line 11 joins A's row; the diff (lines 30-31)
    keeps A's own line out so the band holds. -> (s1, s2, hA)."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=STABLE_CONF)
    b = fresh("security", 11, L0, TITLE_B, conf=60, severity="medium",
              category="injection")
    s2, _ = run_pass(s1, L0, [b], 2, {F: [[30, 31]]})
    return s1, s2, hA


def nearby_scenario(offset=1):
    """Pass 1: A dismissed (warning). Pass 2: line 10+offset edited, the
    flagged line unchanged. -> (s1, s2, hA)."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=STABLE_CONF)
    L2 = list(L0)
    L2[9 + offset] = "line_%02d = 'edited'" % (10 + offset)
    s2, _ = run_pass(s1, L2, [], 2, {F: [[10 + offset, 10 + offset]]})
    return s1, s2, hA


def split_scenario(edit_a=False, real_diff=False, rereport=None):
    """Pass 1: `security` B (line 12) leads a row holding `bugs` A (line 10)
    as a member; the owner dismisses the ROW. Pass 2: B's line is rewritten
    and B's lane answers its re-check `resolved` (the `ab_pipeline` pass-3
    request/verdict shape), so A becomes a row of its own. With `edit_a`,
    A's own line is edited too. -> (L1, s1, s2, r2, hB, hA).

    The pass-2 diff: by default it is empty, the D-09 pure-inheritance shape
    (a split whose causing edit lies outside the member's window), kept for
    the r6 inheritance tests. A real incremental diff names B's rewritten
    line 12, which sits inside A's D-14 window (lines 5-15); `real_diff=True`
    passes exactly that diff and is the realistic split-pass counterpart, on
    which the split row must be re-asked once with "code next to it changed"
    (D-17).

    `rereport`: A's own lane reports it again on the split pass; at a score
    that beats the carried copy (+15 persisted bonus: conf 100, or conf 90
    with a higher severity) the fresh copy leads the row (CR-01 / SA-01). A
    `(conf, severity)` tuple; `None` keeps the split pass free of fresh
    findings."""
    L0 = base_file()
    a = fresh("bugs", 10, L0, TITLE_A, conf=STABLE_CONF)
    b = fresh("security", 12, L0, "Injection at B", conf=80,
              category="injection")
    s1, r1 = run_pass(empty_state(), L0, [a, b], 1, {F: [[1, 200]]})
    assert len(r1["findings"]) == 1, r1["findings"]
    lead = r1["findings"][0]
    hB = lead["stable_hash"]
    s1 = decide_on(s1, hB)
    L1 = list(L0)
    L1[11] = "line_12 = 'fixed'"
    if edit_a:
        L1[9] = "line_10 = 'edited'"
    req = {"token": "TB", "agents": [lead["agent"]], "stable_hash": hB,
           "file": lead["file"], "line": lead["line"], "agent": lead["agent"],
           "title": lead["title"]}
    verdict = {"source": "recheck", "token": "TB", "agent": lead["agent"],
               "verdict": "resolved", "reason": "line rewritten"}
    # Default: an empty diff, the D-09 pure-inheritance shape (the causing
    # edit is treated as outside A's window). `real_diff` names B's rewritten
    # line 12, inside A's D-14 window, as a real incremental diff would (D-17).
    # With `edit_a` the diff names A's own line, as a real incremental diff
    # would (out of the diff, the edited A scores below threshold and is
    # filtered instead of asked).
    if edit_a:
        ranges = {F: [[10, 10]]}
    elif real_diff:
        ranges = {F: [[12, 12]]}
    else:
        ranges = {F: []}
    finds2 = ([] if rereport is None else
              [fresh("bugs", 10, L1, TITLE_A, conf=rereport[0],
                     severity=rereport[1])])
    s2, r2 = run_pass(s1, L1, finds2, 2, ranges, recheck_requests=[req],
                      verdicts=[verdict])
    return L1, s1, s2, r2, hB, score.stable_hash(F, L1[9], TITLE_A)


def absorbed_split_scenario(owed_before_split=False, rereport=None):
    """An own-decision finding absorbed as an obligation sidecar, then split
    out by the lead's nearby fix.

    Pass 1: `bugs` A at line 10 dismissed (its own decision). Pass 2: a
    stronger `security` concern B at line 12 leads the group and A rides as a
    member carrying its obligation. The pass-2 diff is unrelated (lines
    30-31) by default; with `owed_before_split` it names line 12, inside A's
    D-14 window, so A's obligation snapshot is stamped while it is absorbed.
    Pass 3: B's line is rewritten and B's lane answers its re-check
    `resolved`, so A splits back into a row of its own. The pass-3 diff names
    line 12 by default (the causing edit, D-17); with `owed_before_split` it
    is empty so the split itself carries no in-window edit and only the stamp
    already owed can reopen A. -> (s1, s2, s3, r3, hA, hB).

    `rereport`: A's own lane reports it again on the split pass; at a score
    that beats the carried copy (+15 persisted bonus: conf 100, or conf 90
    with a higher severity) the fresh copy leads the row (CR-01 / SA-01). A
    `(conf, severity)` tuple; `None` keeps the split pass free of fresh
    findings."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=STABLE_CONF)
    b = fresh("security", 12, L0, "Injection at B", conf=95,
              severity="critical", category="injection")
    ranges2 = {F: [[12, 12]]} if owed_before_split else {F: [[30, 31]]}
    s2, r2 = run_pass(s1, L0, [b], 2, ranges2)
    assert len(r2["findings"]) == 1, r2["findings"]
    row = r2["findings"][0]
    assert row["agent"] == "security", row
    owed = [m for m in row.get("members", [])
            if (m.get("obligation") or {}).get("stable_hash") == hA]
    assert len(owed) == 1, row.get("members")
    hB = row["stable_hash"]
    L2 = list(L0)
    L2[11] = "line_12 = 'fixed'"
    req = {"token": "TB", "agents": [row["agent"]], "stable_hash": hB,
           "file": F, "line": 12, "agent": row["agent"],
           "title": row["title"]}
    verdict = {"source": "recheck", "token": "TB", "agent": row["agent"],
               "verdict": "resolved", "reason": "line rewritten"}
    ranges3 = {F: []} if owed_before_split else {F: [[12, 12]]}
    finds3 = ([] if rereport is None else
              [fresh("bugs", 10, L2, TITLE_A, conf=rereport[0],
                     severity=rereport[1])])
    s3, r3 = run_pass(s2, L2, finds3, 3, ranges3, recheck_requests=[req],
                      verdicts=[verdict])
    return s1, s2, s3, r3, hA, hB


def plain_rereport_scenario(conf, severity):
    """D-02 / D-14 with no exemption for a same-lane re-report (D-17's
    no-exemption rule): pass 1 `bugs` A at line 10 dismissed; pass 2 line 12
    (inside A's D-14 window, lines 5-15) is edited and A's OWN lane reports A
    again at `conf` / `severity`. At conf 100, or conf 90 with a higher
    severity, the fresh copy out-ranks the carried one (+15 persisted bonus)
    and leads the row; the edit next to A must still re-ask it.
    -> (L1, s2, hA)."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=STABLE_CONF)
    L1 = list(L0)
    L1[11] = "line_12 = 'edited'"
    s2, _ = run_pass(s1, L1, [fresh("bugs", 10, L1, TITLE_A, conf=conf,
                                    severity=severity)], 2, {F: [[12, 12]]})
    return L1, s2, hA


def owed_quiet_rereport_scenario(conf, severity):
    """D-02 / D-14: a re-ask already owed survives a quiet pass on which A's
    own lane re-reports it (the TestSameHashLeadKeepsNearbyStamp shape with
    the SAME lane). Pass 1 `bugs` A dismissed; pass 2 line 11 edited (diff
    [[11, 11]], A owes a nearby re-ask, nearby_at 2), no findings; pass 3 a
    quiet diff with `bugs` A reported fresh at `conf` / `severity`.
    -> (L2, s2, s3, hA)."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=STABLE_CONF)
    L2 = list(L0)
    L2[10] = "line_11 = 'edited'"
    s2, _ = run_pass(s1, L2, [], 2, {F: [[11, 11]]})
    s3, _ = run_pass(s2, L2, [fresh("bugs", 10, L2, TITLE_A, conf=conf,
                                    severity=severity)], 3, {F: []})
    return L2, s2, s3, hA


def low_entropy_split_scenario():
    """WR-01 arm 1 (the `needs-recheck` arm of score._CARRIED_STATUSES): the
    widened carry compare flips a low-entropy member to needs-recheck while
    its hash (keyed on the `}` first line) is unchanged, so the covering
    decision still binds and must be re-asked for the nearby fix.

    Pass 1: line 10 is `}`; `bugs` A there quotes a 3-line fragment (so the
    carry compare widens to it) and rides as a member of the row led by a
    critical `security` B at line 12; the owner dismisses the row. Pass 2:
    B's line is rewritten (inside A's carry window and D-14 window) and B's
    lane answers its re-check `resolved`, so A splits into its own row.
    A's conf is 90: at 75 the needs-recheck copy scores below threshold and
    is filtered. -> (s1, s2, hA, hB)."""
    L0 = base_file()
    L0[9] = "}"
    a = fresh("bugs", 10, L0, TITLE_A, conf=90)
    a["current_code"] = "}\n" + L0[10] + "\n" + L0[11]
    b = fresh("security", 12, L0, "Injection at B", conf=95,
              severity="critical", category="injection")
    s1, r1 = run_pass(empty_state(), L0, [a, b], 1, {F: [[1, 200]]})
    assert len(r1["findings"]) == 1, r1["findings"]
    lead = r1["findings"][0]
    assert lead["agent"] == "security", lead
    hB = lead["stable_hash"]
    s1 = decide_on(s1, hB)
    L1 = list(L0)
    L1[11] = "line_12 = 'fixed'"
    req = {"token": "TB", "agents": [lead["agent"]], "stable_hash": hB,
           "file": lead["file"], "line": lead["line"], "agent": lead["agent"],
           "title": lead["title"]}
    verdict = {"source": "recheck", "token": "TB", "agent": lead["agent"],
               "verdict": "resolved", "reason": "line rewritten"}
    s2, _ = run_pass(s1, L1, [], 2, {F: [[12, 12]]}, recheck_requests=[req],
                     verdicts=[verdict])
    return s1, s2, score.stable_hash(F, "}", TITLE_A), hB


def edited_lead_member_scenario():
    """WR-01 arm 2 (hash equality on the prior seed): a record whose line
    changed is a different finding; the seed's hash equality keeps the old
    record's stamp off the new row.

    Pass 1: `bugs` A at line 10 dismissed. Pass 2: a critical `security` B at
    line 12 leads and A rides absorbed; the diff names line 12, so A's
    obligation snapshot owes a re-ask (nearby_at 2). Pass 3: B's line is
    rewritten and B's lane answers `resolved`, A's OWN line is edited too,
    the diff is quiet, and A's lane re-reports the edited code at conf 100
    (at 75 the row is sub-threshold and a kept-open row under the old hash
    appears instead). -> (s2, s3, hA, hA2)."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=STABLE_CONF)
    b = fresh("security", 12, L0, "Injection at B", conf=95,
              severity="critical", category="injection")
    s2, r2 = run_pass(s1, L0, [b], 2, {F: [[12, 12]]})
    assert len(r2["findings"]) == 1, r2["findings"]
    row = r2["findings"][0]
    assert row["agent"] == "security", row
    hB = row["stable_hash"]
    L2 = list(L0)
    L2[11] = "line_12 = 'fixed'"
    L2[9] = "line_10 = 'edited'"
    req = {"token": "TB", "agents": [row["agent"]], "stable_hash": hB,
           "file": F, "line": 12, "agent": row["agent"],
           "title": row["title"]}
    verdict = {"source": "recheck", "token": "TB", "agent": row["agent"],
               "verdict": "resolved", "reason": "line rewritten"}
    s3, _ = run_pass(s2, L2, [fresh("bugs", 10, L2, TITLE_A, conf=100)], 3,
                     {F: []}, recheck_requests=[req], verdicts=[verdict])
    return s2, s3, hA, score.stable_hash(F, L2[9], TITLE_A)


def same_hash_lines():
    """base_file() with lines 10 and 12 both `return None`: stable_hash has no
    line number, so one title hashes identically at either line."""
    L = base_file()
    L[9] = L[11] = "return None"
    return L


def cross_lane_same_hash_scenario(sec_conf):
    """57-REVIEW-GAPS3.md CR-01 (cross-lane): one identity, two lines.

    Pass 1: `bugs` A at line 12 (`return None`), dismissed. Pass 2: `security`
    reports the same title at line 10 (same text, so the same hash) at
    `sec_conf`; the diff names line 17, inside line 12's D-14 window (7-17)
    and outside line 10's (5-15). The decision binds the identity, so the
    change next to the carried copy re-asks it whichever copy leads (D-02 /
    D-14, D-17, D-19 pooling). -> (s2, r2, hA)."""
    L0 = same_hash_lines()
    s1, hA = pass1(L0, conf=STABLE_CONF, line=12)
    s2, r2 = run_pass(s1, L0, [fresh("security", 10, L0, TITLE_A,
                                     conf=sec_conf, category="injection")],
                      2, {F: [[17, 17]]})
    return s2, r2, hA


def arrival_order_scenario(order):
    """57-REVIEW-GAPS3.md CR-01 (same-lane arrival order): the decided `bugs`
    A at line 12 is re-reported by its own lane at conf 100 at lines 10 and
    12 (one hash), in the arrival `order` given; the diff names line 17
    (inside line 12's window only). The two fresh records tie on every
    score, so the lead must be chosen by line, never by arrival order, and
    the re-ask owed at line 12 must hold either way (D-02 / D-14, D-17,
    D-19). -> (s2, r2, hA)."""
    L0 = same_hash_lines()
    s1, hA = pass1(L0, conf=STABLE_CONF, line=12)
    s2, r2 = run_pass(s1, L0, [fresh("bugs", n, L0, TITLE_A, conf=100)
                               for n in order], 2, {F: [[17, 17]]})
    return s2, r2, hA


def min_conf_twin_scenario(min_confidence, rereport):
    """57-REVIEW-GAPS3.md CR-02: a carried twin dropped by `min_confidence`
    before grouping. Pass 1: `bugs` A at line 10, dismissed. Pass 2: line 12
    is edited (inside A's D-14 window); A's own lane re-reports A at conf
    `rereport` (None: no re-report). With `min_confidence` set the carried
    copy scores below it and is dropped before the group sees it, so its
    owed re-ask must still reach the row (D-19: pool before any filter).
    The envelope key is ABSENT, not null, when `min_confidence` is None.
    -> (s2, r2, hA)."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=STABLE_CONF)
    L1 = list(L0)
    L1[11] = "line_12 = 'edited'"
    finds = ([fresh("bugs", 10, L1, TITLE_A, conf=rereport)]
             if rereport is not None else [])
    over = ({"min_confidence": min_confidence}
            if min_confidence is not None else {})
    s2, r2 = run_pass(s1, L1, finds, 2, {F: [[12, 12]]}, **over)
    return s2, r2, hA


def edited_carried_lead_scenario():
    """57-REVIEW-GAPS3.md IN-01: a carried lead whose own line was edited is a
    different finding and must not carry its old stamp onto the new hash
    (every prior source passes the one hash gate).

    Pass 1: `bugs` A at line 10, conf 90, dismissed. Pass 2: line 11 is
    edited (diff [[11, 11]]), no findings, so A owes a re-ask (nearby_at 2).
    Pass 3: A's OWN line is edited, the diff is quiet, no findings; the
    carried lead re-hashes to hA2. Conf 90: at 75 the re-hashed row is
    sub-threshold and a kept-open row under hA appears instead.
    -> (s2, s3, hA, hA2)."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=90)
    L2 = list(L0)
    L2[10] = "line_11 = 'edited'"
    s2, _ = run_pass(s1, L2, [], 2, {F: [[11, 11]]})
    L3 = list(L2)
    L3[9] = "line_10 = 'edited'"
    s3, _ = run_pass(s2, L3, [], 3, {F: []})
    return s2, s3, hA, score.stable_hash(F, L3[9], TITLE_A)


def far_twin_scenario():
    """57-REVIEW-GAPS3.md, the far-twin shape that tells pooling ("the latest
    owed stamp wins") from "the first copy wins" (D-19).

    Lines 10 and 30 are both `return None`. Pass 1: `bugs` A at line 10,
    dismissed. Pass 2: A's lane reports the same title at line 30 at conf
    100 (NOT STABLE_CONF: a lone-lane conf-75 fresh finding out of the diff
    scores under the deep-review cutoff and is filtered sub-threshold, so
    the second row would never exist; lines 10 and 30 are separate sites
    under the +-2 grouping, so the fresh copy must clear the cutoff on its
    own); the diff names line 33, inside line 30's window and outside line
    10's. Pass 3 is quiet with no findings.

    The two copies are one identity; a change next to either copy re-asks
    the decision (D-19), so the record carry_state reads (the first row with
    hash hA) must carry the stamp owed at the other copy.
    -> (s2, r2, s3, hA)."""
    L0 = base_file()
    L0[9] = L0[29] = "return None"
    s1, hA = pass1(L0, conf=STABLE_CONF)
    s2, r2 = run_pass(s1, L0, [fresh("bugs", 30, L0, TITLE_A, conf=100)], 2,
                      {F: [[33, 33]]})
    s3, _ = run_pass(s2, L0, [], 3, {F: []})
    return s2, r2, s3, hA


def deferred_covered_lines():
    """(L0, L1): the deferred_covered_sub_threshold_scenario file before and
    after the pass-2 edit of B's line."""
    L0 = base_file()
    L0[9] = "}"
    L1 = list(L0)
    L1[11] = "line_12 = 'fixed'"
    return L0, L1


def deferred_covered_sub_threshold_scenario(kind, **over):
    """57-REVIEW-GAPS3.md WR-02 under D-20: a deferred finding may never leave
    the open set on a score; a dismissed one below threshold may drop.

    low_entropy_split_scenario's exact inputs with the `}`-line `bugs` A at
    conf 75 (3-line current_code kept) and the owner's `kind` on the row led
    by the critical `security` B. Pass 2 resolves B and edits line 12, so A
    splits out below threshold; `over` is forwarded to pass 2's run_pass.
    -> (s1, s2, r2, hA, hB)."""
    L0, L1 = deferred_covered_lines()
    a = fresh("bugs", 10, L0, TITLE_A, conf=STABLE_CONF)
    a["current_code"] = "}\n" + L0[10] + "\n" + L0[11]
    b = fresh("security", 12, L0, "Injection at B", conf=95,
              severity="critical", category="injection")
    s1, r1 = run_pass(empty_state(), L0, [a, b], 1, {F: [[1, 200]]})
    assert len(r1["findings"]) == 1, r1["findings"]
    lead = r1["findings"][0]
    assert lead["agent"] == "security", lead
    hB = lead["stable_hash"]
    s1 = decide_on(s1, hB, kind=kind)
    req = {"token": "TB", "agents": [lead["agent"]], "stable_hash": hB,
           "file": lead["file"], "line": lead["line"], "agent": lead["agent"],
           "title": lead["title"]}
    verdict = {"source": "recheck", "token": "TB", "agent": lead["agent"],
               "verdict": "resolved", "reason": "line rewritten"}
    s2, r2 = run_pass(s1, L1, [], 2, {F: [[12, 12]]}, recheck_requests=[req],
                      verdicts=[verdict], **over)
    return s1, s2, r2, score.stable_hash(F, "}", TITLE_A), hB


class TestRegrouping(_Base):
    """D-08 (with the owner's 2026-10-26 refinement: a newcomer concern from
    an uncovered lane reopens the WHOLE decided row once, with the D-10
    note), D-09; DECN-02/03."""

    def test_r4_new_weaker_concern_on_decided_row_is_asked(self):
        s1, s2, hA = joined_scenario()
        self._assert_band(s1, hA, "warning")
        self._assert_band(s2, hA, "warning")
        row = row_of(s2, hA)
        b_members = [m for m in row["members"]
                     if (m["agent"], m["title"]) == ("security", TITLE_B)]
        # The fixture holds what it claims: B was absorbed into A's row as a
        # member with no obligation of its own (not a record today).
        self.assertEqual(len(b_members), 1, row["members"])
        self.assertNotIn("obligation", b_members[0])
        rec = self._current(s2, hA)
        self.assertEqual(carry_state.decision_state(rec, s2), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s2), "joined")
        counts = carry_state.finalize_counts(s2, {})
        self.assertGreater(counts["outstanding_cw"]
                           + counts["unacknowledged_medium"]
                           + counts["undecided_nv"], 0)
        self.assertNotEqual(e2e_gate(s2, {}), "write")
        crow = card_row(s2, hA)
        self.assertIsNotNone(crow, "decided row not on the card")
        self.assertEqual((crow["stale"] or {}).get("cause"), "joined")

    def test_r4_covers_frozen_at_decision_time(self):
        s1, s2, hA = joined_scenario()
        self._assert_band(s1, hA, "warning")
        want = [{"agent": "bugs", "file": F, "title": TITLE_A,
                 "code": base_file()[9], "band": "warning",
                 "lanes": ["bugs"]}]
        self.assertEqual(s1["decisions"][hA].get("covers"), want)
        # Frozen: only a new record-decisions write may extend it.
        self.assertEqual(s2["decisions"][hA].get("covers"), want)

    def test_r5_fresh_duplicate_outranking_decided_record_keeps_its_obligation(
            self):
        L0 = base_file()
        s1, hA = pass1(L0, conf=60)
        self._assert_band(s1, hA, "medium")
        dup = fresh("bugs", 10, L0, TITLE_A, conf=100)
        c = fresh("security", 11, L0, TITLE_C, conf=100,
                  category="injection")
        # The code is unchanged (L0 on both passes), so pass 2's incremental
        # diff is empty: a change inside A's window (line 10 and the 5 beneath)
        # would rightly re-ask A (D-02, TestNearbyEdit) and confound this test.
        s2, r2 = run_pass(s1, L0, [dup, c], 2, {F: []})
        hC = score.stable_hash(F, L0[10], TITLE_C)
        # The fixture holds what it claims: C leads the group, and the fresh
        # duplicate shares the carried A's occurrence identity (so dedup meets
        # the carried record).
        self.assertEqual(r2["findings"][0]["stable_hash"], hC)
        self._assert_band(s2, hC, "warning")
        a_carried = dict(row_of(s1, hA), canonical_line_content=L0[9])
        self.assertEqual(score._finding_identity(dup),
                         score._finding_identity(a_carried))
        rec = self._current(s2, hA)  # today: obligation dropped by dedup
        self.assertEqual(carry_state.decision_state(rec, s2), "current")
        c_rec = self._current(s2, hC)
        self.assertIsNone(carry_state.decision_state(c_rec, s2))
        shown = [r["stable_hash"] for r in card_rows(s2)]
        self.assertIn(hC, shown)
        self.assertNotIn(hA, shown)

    def test_r6_split_member_inherits_decision(self):
        _, s1, s2, r2, hB, hA = split_scenario()
        row1 = s1["passes"][-1]["findings"]
        self.assertEqual(len(row1), 1)
        self.assertEqual(row1[0]["agent"], "security")
        a_members = [m for m in row1[0]["members"] if m["agent"] == "bugs"]
        self.assertEqual(len(a_members), 1)
        self.assertNotIn("obligation", a_members[0])
        self._assert_band(s1, hB, "warning")
        self.assertIn(hB, [x.get("stable_hash") for x in r2.get("resolved", [])])
        self.assertIsNone(record_of(s2, hB))
        self._assert_band(s2, hA, "warning")
        rec = self._current(s2, hA)
        self.assertIsNone(rec.get("absorbed_into"))
        self.assertEqual(carry_state.decision_state(rec, s2), "current")
        self.assertIsNone(carry_state.stale_cause(rec, s2))
        self.assertEqual(e2e_gate(s2, {}), "write")
        self.assertNotIn(hA, [r["stable_hash"] for r in card_rows(s2)])
        covering = getattr(carry_state, "covering_decision",
                           lambda r, s: None)(rec, s2)
        self.assertEqual(covering, (hB, s2["decisions"][hB]))

    def test_r6_split_member_whose_code_changed_is_asked(self):
        """Fail toward asking: a covered member whose own line changed is a
        different finding and is asked (green today; must stay green)."""
        L1, s1, s2, r2, hB, hA2 = split_scenario(edit_a=True)
        self._assert_band(s1, hB, "warning")
        self.assertNotEqual(hA2, score.stable_hash(F, base_file()[9], TITLE_A))
        rec = self._current(s2, hA2)
        self.assertIsNone(carry_state.decision_state(rec, s2))
        self.assertIn(hA2, [r["stable_hash"] for r in card_rows(s2)])

    def test_covers_cannot_be_injected_by_payload(self):
        """T-57-01: the decisions payload key set is exact, so a payload can
        never write `covers` (green today; must stay green)."""
        L0 = base_file()
        s1, hA = pass1(L0, conf=STABLE_CONF)
        self._assert_band(s1, hA, "warning")
        for extra in ({"covers": []}, {"attribution": ["security"]},
                      {"lanes": ["security"]}):
            with self.subTest(extra=sorted(extra)):
                entry = dict({"stable_hash": hA, "decision": "dismiss",
                              "reason": "x"}, **extra)
                self.assertIsNone(carry_state.record_decisions(
                    s1, {"at_pass": 1, "decisions": [entry]}))


class TestSplitPassNearby(_Base):
    """D-17 (57-VERIFICATION.md gap 1, 57-REVIEW-GAPS.md CR-01): when a
    covered or absorbed finding splits into its own row on the pass whose
    in-window edit caused the split, the new row is re-asked once with "code
    next to it changed"; a re-ask already owed before the split survives it.

    Expected on the unfixed scorer: s1, s2 and s3 fail at the split row's
    missing `nearby_at` stamp (score._snapshot_for stamps only a row that
    already holds a dict snapshot, and a split survivor has none). s4 is the
    negative and stays green: a fresh lead over a carried member is never
    stamped."""

    def test_s1_inherited_member_split_by_nearby_fix_is_reasked(self):
        _, s1, s2, r2, hB, hA = split_scenario(real_diff=True)
        rec = self._current(s2, hA)
        self.assertEqual(rec["snapshot"].get("nearby_at"), 2,
                         "split row snapshot has no nearby_at: %r"
                         % rec["snapshot"])
        self.assertEqual(rec["snapshot"]["at_pass"], 2)
        # Fixture self-check: the causing edit is inside A's D-14 window.
        self.assertTrue(score._nearby_changed(rec, {F: [[12, 12]]}))
        self.assertEqual(carry_state.decision_state(rec, s2), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s2), "nearby")
        self.assertEqual(carry_state.covering_decision(rec, s2),
                         (hB, s2["decisions"][hB]))
        self.assertIn(hA, carry_state.finalize_counts(
            s2, {})["outstanding_cw_hashes"])
        self.assertNotEqual(e2e_gate(s2, {}), "write")
        crow = card_row(s2, hA)
        self.assertIsNotNone(crow, "re-asked split row not on the card")
        self.assertEqual((crow["stale"] or {}).get("cause"), "nearby")

    def test_s2_own_decision_absorbed_then_split_by_nearby_fix_is_reasked(
            self):
        s1, s2, s3, r3, hA, hB = absorbed_split_scenario()
        # Pass 2 holds what the fixture claims: A rides absorbed, current.
        absorbed = self._current(s2, hA)
        self.assertEqual(absorbed.get("absorbed_into"), hB)
        self.assertEqual(carry_state.decision_state(absorbed, s2), "current")
        rec = self._current(s3, hA)
        self.assertEqual(rec["snapshot"].get("nearby_at"), 3,
                         "split row snapshot has no nearby_at: %r"
                         % rec["snapshot"])
        self.assertIsNone(rec.get("absorbed_into"))
        self.assertEqual(carry_state.decision_state(rec, s3), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s3), "nearby")
        self.assertIn(hA, carry_state.finalize_counts(
            s3, {})["outstanding_cw_hashes"])
        self.assertNotEqual(e2e_gate(s3, {}), "write")

    def test_s3_owed_stamp_survives_the_split(self):
        s1, s2, s3, r3, hA, hB = absorbed_split_scenario(
            owed_before_split=True)
        absorbed = self._current(s2, hA)
        self.assertEqual(absorbed["snapshot"].get("nearby_at"), 2)
        self.assertEqual(carry_state.decision_state(absorbed, s2), "stale")
        rec = self._current(s3, hA)
        self.assertEqual(rec["snapshot"].get("nearby_at"), 2,
                         "owed nearby_at lost at the split: %r"
                         % rec["snapshot"])
        self.assertIsNone(rec.get("absorbed_into"))
        self.assertEqual(carry_state.decision_state(rec, s3), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s3), "nearby")
        self.assertIn(hA, carry_state.finalize_counts(
            s3, {})["outstanding_cw_hashes"])

    def test_s4_fresh_lead_over_a_carried_member_is_not_stamped(self):
        s1, s2, s3, r3, hA, hB = absorbed_split_scenario(
            owed_before_split=True)
        self.assertNotIn("nearby_at", row_of(s2, hB)["snapshot"])
        self.assertEqual(record_of(s2, hA)["snapshot"]["nearby_at"], 2)


class TestSameLaneRereport(_Base):
    """57-VERIFICATION.md re-verification 2 gap 1; 57-REVIEW-GAPS2.md CR-01
    and SA-01: a decided finding's OWN lane reports it again at a score that
    beats the carried copy (+15 persisted bonus), so the fresh copy leads the
    row. An edit next to the finding (D-02 / D-14), or a re-ask already owed,
    must still re-ask it: a same-lane re-report has no exemption (D-17).

    Root cause: the scorer reads carried-ness and the prior snapshot from the
    row's lead record only, and the carried twin sharing the fresh lead's
    occurrence identity is deduped away before its evidence is read.

    Expected on the unfixed scorer: a, a2, b, c and d fail at the row's
    missing `nearby_at`; the control (the carried copy still leads at conf
    75) is green and must stay green."""

    def _assert_reasked(self, state, hA, nearby_at):
        """The re-ask contract on the real chain, snapshot in every message."""
        rec = self._current(state, hA)
        snap = rec["snapshot"]
        self.assertEqual(snap.get("nearby_at"), nearby_at,
                         "re-reported row snapshot has no nearby_at: %r"
                         % snap)
        self.assertEqual(carry_state.decision_state(rec, state), "stale",
                         "snapshot %r" % snap)
        self.assertEqual(carry_state.stale_cause(rec, state), "nearby",
                         "snapshot %r" % snap)
        self.assertIn(hA, carry_state.finalize_counts(
            state, {})["outstanding_cw_hashes"], "snapshot %r" % snap)
        self.assertNotEqual(e2e_gate(state, {}), "write",
                            "snapshot %r" % snap)
        crow = card_row(state, hA)
        self.assertIsNotNone(crow, "re-asked row not on the card")
        self.assertEqual((crow["stale"] or {}).get("cause"), "nearby",
                         "snapshot %r" % snap)
        return rec

    def _assert_plain_led_by_fresh(self, s2, hA):
        row = row_of(s2, hA)
        self.assertIsNotNone(row, "no row for %s" % hA[:8])
        # Fixture self-check: the fresh same-lane copy leads, and the carried
        # twin was deduped into the lead's own member ref.
        self.assertEqual(row["status"], "new", row["snapshot"])
        self.assertEqual(row["agent"], "bugs")
        self.assertEqual(len(row["members"]), 1, row["members"])
        return row

    def test_a_plain_row_rereported_by_own_lane_at_conf_100(self):
        _, s2, hA = plain_rereport_scenario(100, "warning")
        self._assert_plain_led_by_fresh(s2, hA)
        self._assert_band(s2, hA, "warning")
        rec = self._assert_reasked(s2, hA, 2)
        self.assertEqual(rec["snapshot"]["at_pass"], 2, rec["snapshot"])

    def test_a2_plain_row_rereported_by_own_lane_at_higher_band(self):
        """The re-report also lifts the band to critical. A same-lane rise is
        not lane-backed (D-05) and nearby out-ranks severity in stale_cause,
        so the cause is still "code next to it changed"."""
        _, s2, hA = plain_rereport_scenario(100, "critical")
        self._assert_plain_led_by_fresh(s2, hA)
        self._assert_band(s2, hA, "critical")
        rec = self._assert_reasked(s2, hA, 2)
        self.assertEqual(rec["snapshot"]["at_pass"], 2, rec["snapshot"])

    def test_b_inherited_split_led_by_own_lane_rereport(self):
        _, s1, s2, r2, hB, hA = split_scenario(real_diff=True,
                                               rereport=(100, "warning"))
        row = row_of(s2, hA)
        self.assertIsNotNone(row, "no split row for %s" % hA[:8])
        self.assertEqual(row["status"], "new", row["snapshot"])
        self.assertIsNone(record_of(s2, hB))
        rec = self._assert_reasked(s2, hA, 2)
        self.assertEqual(carry_state.covering_decision(rec, s2),
                         (hB, s2["decisions"][hB]))

    def test_c_own_decision_absorbed_split_led_by_own_lane_rereport(self):
        s1, s2, s3, r3, hA, hB = absorbed_split_scenario(
            rereport=(100, "warning"))
        # Pass 2 holds what the fixture claims: A rides absorbed, current.
        absorbed = self._current(s2, hA)
        self.assertEqual(absorbed.get("absorbed_into"), hB)
        self.assertEqual(carry_state.decision_state(absorbed, s2), "current")
        row = row_of(s3, hA)
        self.assertIsNotNone(row, "no split row for %s" % hA[:8])
        self.assertEqual(row["status"], "new", row["snapshot"])
        rec = self._current(s3, hA)
        self.assertEqual(rec["snapshot"].get("nearby_at"), 3,
                         "re-reported split row snapshot has no nearby_at: %r"
                         % rec["snapshot"])
        self.assertIsNone(rec.get("absorbed_into"))
        self._assert_reasked(s3, hA, 3)

    def test_d_owed_stamp_survives_own_lane_rereport_on_quiet_pass(self):
        _, s2, s3, hA = owed_quiet_rereport_scenario(100, "warning")
        owed = self._current(s2, hA)
        self.assertEqual(owed["snapshot"].get("nearby_at"), 2)
        self.assertEqual(carry_state.stale_cause(owed, s2), "nearby")
        row = row_of(s3, hA)
        self.assertIsNotNone(row, "no row for %s" % hA[:8])
        self.assertEqual(row["status"], "new", row["snapshot"])
        self._assert_band(s3, hA, "warning")
        rec = self._assert_reasked(s3, hA, 2)
        # Band and canonical are unchanged, so the prior is kept, not
        # refreshed.
        self.assertEqual(rec["snapshot"]["at_pass"], 2, rec["snapshot"])

    def test_control_carried_copy_leads_at_conf_75(self):
        _, s2, hA = plain_rereport_scenario(STABLE_CONF, "warning")
        row = row_of(s2, hA)
        self.assertIsNotNone(row, "no row for %s" % hA[:8])
        self.assertEqual(row["status"], "persisted", row["snapshot"])
        self._assert_reasked(s2, hA, 2)


class TestWr01Guards(_Base):
    """57-REVIEW-GAPS2.md WR-01: the two guards in the touched region that had
    no real-chain fixture. w1 locks the `needs-recheck` arm of
    score._CARRIED_STATUSES; w2 locks the hash equality on the prior seed."""

    def test_w1_needs_recheck_split_row_keeps_its_hash_and_is_stamped(self):
        s1, s2, hA, hB = low_entropy_split_scenario()
        row = row_of(s2, hA)
        self.assertIsNotNone(row, "no split row for %s" % hA[:8])
        snap = row.get("snapshot")
        # Fixture self-checks: the widened compare flipped the status, the
        # `}`-keyed hash is unchanged.
        self.assertEqual(row["status"], "needs-recheck", snap)
        self.assertEqual(row["stable_hash"], score.stable_hash(F, "}", TITLE_A))
        rec = self._current(s2, hA)
        self.assertEqual(rec["snapshot"].get("nearby_at"), 2,
                         "needs-recheck split row not stamped: %r"
                         % rec["snapshot"])
        self.assertEqual(carry_state.decision_state(rec, s2), "stale",
                         "snapshot %r" % rec["snapshot"])
        self.assertEqual(carry_state.stale_cause(rec, s2), "nearby",
                         "snapshot %r" % rec["snapshot"])
        self.assertIsNotNone(carry_state.covering_decision(rec, s2))
        self.assertIn(hA, carry_state.finalize_counts(
            s2, {})["outstanding_cw_hashes"])
        self.assertNotEqual(e2e_gate(s2, {}), "write")

    def test_w2_edited_lead_member_does_not_inherit_the_old_stamp(self):
        s2, s3, hA, hA2 = edited_lead_member_scenario()
        # Fixture self-check: the old record owed a re-ask before the edit.
        self.assertEqual(record_of(s2, hA)["snapshot"].get("nearby_at"), 2,
                         record_of(s2, hA)["snapshot"])
        self.assertNotEqual(hA, hA2)
        row = row_of(s3, hA2)
        self.assertIsNotNone(row, "no row for the edited finding %s" % hA2[:8])
        snap = row["snapshot"]
        self.assertNotIn("kept_open", row, snap)
        self.assertEqual(snap["at_pass"], 3, snap)
        self.assertNotIn("nearby_at", snap,
                         "edited finding inherited a foreign stamp: %r" % snap)
        self.assertIsNone(carry_state.decision_state(record_of(s3, hA2), s3),
                          snap)


class TestPooledEvidence(_Base):
    """57-REVIEW-GAPS3.md CR-01 / CR-02 and D-19: every carried record of an
    identity is pooled BEFORE any filter; nearby is judged at every copy's
    line; the lead is deterministic by line.

    Expected on the unfixed scorer: p1 (conf 100), p2 (both orders), p3
    (min_confidence 80) and p4 fail; the controls (q1, q3) pass."""

    def _assert_reasked(self, state, hA, nearby_at=2):
        rec = self._current(state, hA)
        snap = rec["snapshot"]
        self.assertEqual(snap.get("nearby_at"), nearby_at,
                         "row snapshot has no owed nearby_at: %r" % snap)
        self.assertEqual(carry_state.decision_state(rec, state), "stale",
                         "snapshot %r" % snap)
        self.assertEqual(carry_state.stale_cause(rec, state), "nearby",
                         "snapshot %r" % snap)
        self.assertIn(hA, carry_state.finalize_counts(
            state, {})["outstanding_cw_hashes"], "snapshot %r" % snap)
        self.assertNotEqual(e2e_gate(state, {}), "write",
                            "snapshot %r" % snap)
        return rec

    def test_p1_cross_lane_same_hash_other_line_nearby_reasks(self):
        s2, _, hA = cross_lane_same_hash_scenario(100)
        row = row_of(s2, hA)
        self.assertIsNotNone(row, "no row for %s" % hA[:8])
        snap = row.get("snapshot")
        # Self-check: the fresh security copy leads at the other line.
        self.assertEqual(row["agent"], "security", snap)
        self.assertEqual(row["line"], 10, snap)
        self._assert_reasked(s2, hA)
        crow = card_row(s2, hA)
        self.assertIsNotNone(crow, "re-asked row not on the card")
        self.assertEqual((crow["stale"] or {}).get("cause"), "nearby",
                         "snapshot %r" % snap)

    def test_q1_control_carried_copy_leads(self):
        s2, _, hA = cross_lane_same_hash_scenario(60)
        row = row_of(s2, hA)
        self.assertIsNotNone(row, "no row for %s" % hA[:8])
        snap = row.get("snapshot")
        self.assertEqual(row["agent"], "bugs", snap)
        self.assertEqual(row["line"], 12, snap)
        self._assert_reasked(s2, hA)

    def test_p2_same_lane_arrival_order_does_not_pick_the_outcome(self):
        for order in ([10, 12], [12, 10]):
            with self.subTest(order=order):
                s2, _, hA = arrival_order_scenario(order)
                row = row_of(s2, hA)
                self.assertIsNotNone(row, "no row for %s" % hA[:8])
                snap = row.get("snapshot")
                # The lead is chosen by line, never by arrival order.
                self.assertEqual(row["line"], 10,
                                 "lead depends on arrival order %r; row %r"
                                 % (order, snap))
                self._assert_reasked(s2, hA)

    def test_p3_min_confidence_dropped_twin_keeps_the_reask(self):
        s2, r2, hA = min_conf_twin_scenario(80, 95)
        # Self-check: the carried twin was dropped before grouping.
        self.assertIn("below-min-confidence",
                      [f.get("reason") for f in r2["filtered"]],
                      r2["filtered"])
        row = row_of(s2, hA)
        self.assertIsNotNone(row, "no row for %s" % hA[:8])
        self.assertEqual(row["status"], "new", row.get("snapshot"))
        self._assert_reasked(s2, hA)

    def test_q3_controls_scored_twin_and_no_rereport(self):
        s2, _, hA = min_conf_twin_scenario(None, 95)
        row = row_of(s2, hA)
        self.assertIsNotNone(row, "no row for %s" % hA[:8])
        self.assertEqual(row["status"], "new", row.get("snapshot"))
        self._assert_reasked(s2, hA)
        s2, _, hA = min_conf_twin_scenario(80, None)
        row = row_of(s2, hA)
        self.assertIsNotNone(row, "no row for %s" % hA[:8])
        self.assertIn("kept_open", row, row.get("snapshot"))
        self._assert_reasked(s2, hA)

    def test_p4_far_twin_latest_stamp_reaches_the_first_copy(self):
        s2, r2, s3, hA = far_twin_scenario()
        rows2 = sorted((f for f in r2["findings"] if f["stable_hash"] == hA),
                       key=lambda f: f["line"])
        # Pass-2 self-checks: two rows of one identity, nothing filtered.
        self.assertEqual([(f["line"], f["status"]) for f in rows2],
                         [(10, "persisted"), (30, "new")],
                         [f.get("snapshot") for f in rows2])
        self.assertEqual(r2["filtered"], [])
        self.assertEqual(rows2[1]["snapshot"].get("nearby_at"), 2,
                         "line-30 copy not stamped: %r" % rows2[1]["snapshot"])
        rows3 = [f for f in s3["passes"][-1]["findings"]
                 if f.get("stable_hash") == hA]
        self.assertEqual(len(rows3), 2, [f.get("snapshot") for f in rows3])
        rec = self._current(s3, hA)
        # carry_state keeps the first row of a hash.
        self.assertEqual(rec["line"], 10, rec["snapshot"])
        self._assert_reasked(s3, hA)


class TestPriorGate(_Base):
    """57-REVIEW-GAPS3.md IN-01: every prior source passes the one hash gate;
    a carried lead whose own line was edited does not carry its old stamp
    onto the new hash. Expected on the unfixed scorer: fails at the foreign
    `nearby_at`."""

    def test_in01_edited_carried_lead_does_not_carry_its_stamp_onto_the_new_hash(
            self):
        s2, s3, hA, hA2 = edited_carried_lead_scenario()
        # Self-check: the old record owed a re-ask before the edit.
        self.assertEqual(record_of(s2, hA)["snapshot"].get("nearby_at"), 2,
                         record_of(s2, hA)["snapshot"])
        self.assertNotEqual(hA, hA2)
        row = row_of(s3, hA2)
        self.assertIsNotNone(row, "no row for the edited finding %s" % hA2[:8])
        snap = row["snapshot"]
        self.assertEqual(row["status"], "needs-recheck", snap)
        self.assertNotIn("kept_open", row, snap)
        self.assertEqual(snap["at_pass"], 3, snap)
        self.assertNotIn("nearby_at", snap,
                         "edited finding inherited a foreign stamp: %r" % snap)
        self.assertIsNone(carry_state.decision_state(record_of(s3, hA2), s3),
                          snap)


class TestDeferredStaysOpen(_Base):
    """D-20 (57-REVIEW-GAPS3.md WR-02, defer variant): a DEFERRED finding
    stays on the owner's open list even when its split-out row scores below
    the reporting threshold; a DISMISSED one below threshold may drop.
    Expected on the unfixed scorer: the defer test fails (record orphaned);
    the dismiss lock passes and must stay green."""

    def test_deferred_covered_member_below_threshold_stays_open(self):
        _, s2, r2, hA, hB = deferred_covered_sub_threshold_scenario("defer")
        rec = self._current(s2, hA)
        snap = rec.get("snapshot")
        row = row_of(s2, hA)
        self.assertIsNotNone(row, "no row for %s; filtered %r"
                             % (hA[:8], r2["filtered"]))
        self.assertTrue(str(row.get("kept_open", "")).startswith(
            "sub-threshold"), "row %r" % row)
        self.assertEqual(carry_state.decision_state(rec, s2), "stale",
                         "snapshot %r" % snap)
        self.assertEqual(carry_state.stale_cause(rec, s2), "nearby",
                         "snapshot %r" % snap)
        self.assertEqual(carry_state.covering_decision(rec, s2)[0], hB,
                         "snapshot %r" % snap)
        self.assertIn(hA, carry_state.finalize_counts(
            s2, {})["outstanding_cw_hashes"], "snapshot %r" % snap)
        self.assertNotEqual(e2e_gate(s2, {}), "write", "snapshot %r" % snap)
        crow = card_row(s2, hA)
        self.assertIsNotNone(crow, "deferred row not on the card")
        self.assertEqual((crow["stale"] or {}).get("cause"), "nearby",
                         "snapshot %r" % snap)

    def test_dismissed_covered_member_below_threshold_may_drop(self):
        _, s2, r2, hA, _ = deferred_covered_sub_threshold_scenario("dismiss")
        self.assertEqual(r2["findings"], [], r2["filtered"])
        self.assertIn({"line": 10, "title": TITLE_A, "reason": "sub-threshold"},
                      [{k: f.get(k) for k in ("line", "title", "reason")}
                       for f in r2["filtered"]], r2["filtered"])
        self.assertIsNone(record_of(s2, hA), r2["filtered"])
        self.assertEqual(carry_state.finalize_counts(s2, {})["outstanding_cw"],
                         0, r2["filtered"])
        self.assertEqual(e2e_gate(s2, {}), "write", r2["filtered"])

    def test_deferred_kept_open_row_shape(self):
        """The kept-open row is the member under its OWN hash, at the band
        the owner deferred it at, naming the covering decision, stamped by
        the split pass's in-window edit (D-17)."""
        _, s2, r2, hA, hB = deferred_covered_sub_threshold_scenario("defer")
        self.assertEqual([f["stable_hash"] for f in r2["findings"]], [hA])
        row = row_of(s2, hA)
        self.assertIsNotNone(row, r2["filtered"])
        self.assertEqual(row["kept_open"], "sub-threshold; deferred-by: " + hB)
        self.assertIn(row["status"], ("persisted", "needs-recheck"))
        self.assertEqual(row["band"], "warning")
        self.assertEqual(row["stable_hash"], hA)
        self.assertEqual(row["snapshot"].get("nearby_at"), 2, row["snapshot"])
        self.assertEqual(row["orchestrator_score"], 65)
        self.assertNotIn("obligation", row)

    def test_deferred_kept_open_row_persists_on_the_next_pass(self):
        """On a quiet pass the kept-open row is carried like any kept-open
        row and stays open; only the owner's own decision closes it."""
        _, s2, _, hA, _ = deferred_covered_sub_threshold_scenario("defer")
        _, L1 = deferred_covered_lines()
        s3, r3 = run_pass(s2, L1, [], 3, {F: []})
        rec = self._current(s3, hA)
        row = row_of(s3, hA)
        self.assertIsNotNone(row, r3["filtered"])
        self.assertIn("kept_open", row, row)
        self.assertEqual(row["snapshot"].get("nearby_at"), 2, row["snapshot"])
        self.assertEqual(carry_state.decision_state(rec, s3), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s3), "nearby")
        self.assertIn(hA, carry_state.finalize_counts(
            s3, {})["outstanding_cw_hashes"])
        s3 = decide_on(s3, hA, "dismiss")
        self.assertEqual(carry_state.decision_state(record_of(s3, hA), s3),
                         "current")
        self.assertNotIn(hA, carry_state.finalize_counts(
            s3, {})["outstanding_cw_hashes"])

    def test_envelope_without_deferred_hashes_scores_as_before(self):
        """An envelope without `deferred_hashes` (every archived replay
        envelope) synthesizes nothing: the member drops as before D-20."""
        _, s2, r2, hA, _ = deferred_covered_sub_threshold_scenario(
            "defer", deferred_hashes=None)
        self.assertEqual(r2["findings"], [], r2["filtered"])
        self.assertIsNone(record_of(s2, hA), r2["filtered"])
        self.assertEqual(e2e_gate(s2, {}), "write", r2["filtered"])


# Which record leads: the carried copy (STABLE_CONF re-report, out-ranked by
# the +15 persisted bonus), a fresh copy out-ranking it at the same band, or a
# fresh copy that also lifts the band.
LEAD_PERMUTATIONS = (("carried-leads", (STABLE_CONF, "warning")),
                     ("fresh-leads-same-band", (100, "warning")),
                     ("fresh-leads-higher-band", (100, "critical")))


def _inv_plain(conf, severity):
    _, s2, hA = plain_rereport_scenario(conf, severity)
    return s2, hA, row_of(s2, hA)["status"]


def _inv_inherited_split(conf, severity):
    _, _, s2, _, _, hA = split_scenario(real_diff=True,
                                        rereport=(conf, severity))
    return s2, hA, row_of(s2, hA)["status"]


def _inv_absorbed_split(conf, severity):
    _, _, s3, _, hA, _ = absorbed_split_scenario(rereport=(conf, severity))
    return s3, hA, row_of(s3, hA)["status"]


def _inv_owed_quiet_same_lane(conf, severity):
    _, _, s3, hA = owed_quiet_rereport_scenario(conf, severity)
    return s3, hA, row_of(s3, hA)["status"]


def _inv_owed_quiet_different_lane(conf, severity):
    """TestSameHashLeadKeepsNearbyStamp with the re-report from `security`;
    the lead marker is the row's agent."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=STABLE_CONF)
    L2 = list(L0)
    L2[10] = "line_11 = 'edited'"
    s2, _ = run_pass(s1, L2, [], 2, {F: [[11, 11]]})
    sec = fresh("security", 10, L2, TITLE_A, conf=conf, severity=severity,
                category="injection")
    s3, _ = run_pass(s2, L2, [sec], 3, {F: []})
    return s3, hA, row_of(s3, hA)["agent"]


def _inv_different_lane_dup_57_04(conf, severity):
    """TestRegrouping r5: `security` C leads the row; a fresh `bugs` A
    duplicate meets the carried decided A (pass-1 conf 60) in the group. The
    lead marker is (C leads, the kept A member's agent_confidence): 60 when
    the carried A was kept, the fresh conf when the duplicate out-ranked it."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=60)
    dup = fresh("bugs", 10, L0, TITLE_A, conf=conf, severity=severity)
    c = fresh("security", 11, L0, TITLE_C, conf=100, category="injection")
    s2, r2 = run_pass(s1, L0, [dup, c], 2, {F: []})
    hC = score.stable_hash(F, L0[10], TITLE_C)
    lead = row_of(s2, hC)
    kept = ([m.get("agent_confidence") for m in lead.get("members", [])
             if m.get("agent") == "bugs"] if lead else [])
    return s2, hA, (lead is not None and lead["agent"] == "security", kept)


def _inv_different_line_same_hash_cross_lane(sec_conf, _sev):
    """CR-01 cross-lane: the lead marker is (row agent, row line)."""
    s2, _, hA = cross_lane_same_hash_scenario(sec_conf)
    row = row_of(s2, hA)
    return s2, hA, (row["agent"], row["line"])


def _inv_same_lane_arrival_order(order, _sev):
    """CR-01 arrival order: the knob is the arrival ORDER of two tied
    conf-100 same-lane reports; the marker is the row line, the self-check
    that the lead is deterministic (not a permutation of the lead)."""
    s2, _, hA = arrival_order_scenario(list(order))
    return s2, hA, row_of(s2, hA)["line"]


def _inv_min_confidence_dropped_twin(rereport, _sev, min_confidence):
    """CR-02: the marker is (row status, whether a record was dropped
    below min_confidence before grouping)."""
    s2, r2, hA = min_conf_twin_scenario(min_confidence, rereport)
    return s2, hA, (row_of(s2, hA)["status"],
                    "below-min-confidence"
                    in [f.get("reason") for f in r2["filtered"]])


# name -> (build(<knobs unpacked>) -> (state, hA, lead marker),
#          ((label, knobs, expected lead marker), ...),
#          expected triple, or None for "whatever carried-leads yields")
_SAME_LANE = {"carried-leads": "persisted", "fresh-leads-same-band": "new",
              "fresh-leads-higher-band": "new"}
_REASK = ("stale", "nearby", True)


def _same_lane_perms():
    return tuple((label, cs, _SAME_LANE[label])
                 for label, cs in LEAD_PERMUTATIONS)


INVARIANCE_SCENARIOS = {
    "plain": (_inv_plain, _same_lane_perms(), _REASK),
    "inherited_split": (_inv_inherited_split, _same_lane_perms(), _REASK),
    "absorbed_split": (_inv_absorbed_split, _same_lane_perms(), _REASK),
    "owed_quiet_same_lane": (_inv_owed_quiet_same_lane, _same_lane_perms(),
                             _REASK),
    # A different lane at a higher band would corroborate into a lane-backed
    # rise: D-05's own test, not this guard's.
    "owed_quiet_different_lane": (
        _inv_owed_quiet_different_lane,
        (("carried-leads", (60, "warning"), "bugs"),
         ("fresh-leads-same-band", (95, "warning"), "security")),
        _REASK),
    # A higher-band duplicate would take the row's lead from C and turn the
    # shape into D-08's joined row (TestRegrouping r4), not this one.
    "different_lane_dup_57_04": (
        _inv_different_lane_dup_57_04,
        ((LEAD_PERMUTATIONS[0][0], LEAD_PERMUTATIONS[0][1], (True, [60])),
         (LEAD_PERMUTATIONS[1][0], LEAD_PERMUTATIONS[1][1], (True, [100]))),
        None),
    # CR-01 cross-lane: a same-hash record at another line out-ranks the
    # carried copy.
    "different_line_same_hash_cross_lane": (
        _inv_different_line_same_hash_cross_lane,
        (("carried-leads", (60, "warning"), ("bugs", 12)),
         ("fresh-leads-same-band", (100, "warning"), ("security", 10))),
        _REASK),
    # CR-01 arrival order. "carried-leads" is the baseline label the coverage
    # lock requires; here both permutations are two fresh same-conf reports.
    "same_lane_arrival_order": (
        _inv_same_lane_arrival_order,
        (("carried-leads", ((10, 12), "warning"), 10),
         ("fresh-leads-reversed-arrival", ((12, 10), "warning"), 10)),
        _REASK),
    # CR-02: the carried twin is dropped by min_confidence before grouping.
    "min_confidence_dropped_twin": (
        _inv_min_confidence_dropped_twin,
        (("carried-leads", (STABLE_CONF, "warning", None),
          ("persisted", False)),
         ("fresh-leads-same-band", (95, "warning", None), ("new", False)),
         ("fresh-leads-twin-dropped", (95, "warning", 80), ("new", True))),
        _REASK),
}


class TestLeadOrderInvariance(_Base):
    """Whether a decided finding re-asks must not depend on which of its
    records leads the row. Three review rounds (57-REVIEW.md,
    57-REVIEW-GAPS.md Critical-1, 57-REVIEW-GAPS2.md CR-01) each found a
    wrong-keep whose only trigger was a fresh record out-ranking the carried
    one. This guard permutes the lead in every row shape the phase cares
    about and asserts the decision outcome is identical.

    Expected on the unfixed scorer: the fresh-leads permutations of plain,
    inherited_split, absorbed_split and owed_quiet_same_lane fail (SUBFAILED);
    every carried-leads baseline passes."""

    def _triple(self, state, hA):
        rec = self._current(state, hA)
        st = carry_state.decision_state(rec, state)
        return (st,
                carry_state.stale_cause(rec, state) if st == "stale" else None,
                hA in carry_state.finalize_counts(
                    state, {})["outstanding_cw_hashes"])

    def test_decision_outcome_does_not_depend_on_which_record_leads(self):
        for name, (build, perms, want) in INVARIANCE_SCENARIOS.items():
            baseline = None
            for label, knobs, marker in perms:
                with self.subTest(scenario=name, lead=label):
                    state, hA, got_marker = build(*knobs)
                    row = row_of(state, hA)
                    snap = (row or {}).get("snapshot")
                    # Self-check: the permutation really moved the lead.
                    self.assertEqual(got_marker, marker,
                                     "%s/%s did not permute the lead; row %r"
                                     % (name, label, snap))
                    triple = self._triple(state, hA)
                    self.assertIsNotNone(
                        triple[0], "%s/%s: decision lost; row %r"
                        % (name, label, snap))
                    if baseline is None:
                        baseline = triple
                    expect = want if want is not None else baseline
                    self.assertEqual(
                        triple, expect,
                        "%s/%s: outcome depends on which record leads; "
                        "row snapshot %r" % (name, label, snap))

    def test_guard_covers_every_scenario_the_phase_cares_about(self):
        self.assertEqual(set(INVARIANCE_SCENARIOS),
                         {"plain", "inherited_split", "absorbed_split",
                          "owed_quiet_same_lane",
                          "owed_quiet_different_lane",
                          "different_lane_dup_57_04",
                          "different_line_same_hash_cross_lane",
                          "same_lane_arrival_order",
                          "min_confidence_dropped_twin"})
        self.assertEqual(len(LEAD_PERMUTATIONS), 3)
        self.assertEqual(LEAD_PERMUTATIONS[0][1][0], STABLE_CONF)
        for name, (_, perms, _) in INVARIANCE_SCENARIOS.items():
            self.assertEqual(perms[0][0], "carried-leads", name)
            self.assertGreaterEqual(len(perms), 2, name)


# --------------------------------------------------------------------------- #
# Card wording (D-05, D-10, D-12): the reopen suffix says what changed.
# --------------------------------------------------------------------------- #
class TestCardWording(_Base):

    def test_r7_rise_card_names_the_new_lane(self):
        s1, s2, hA = new_lane_scenario()
        self._assert_band(s1, hA, "warning")
        self._assert_band(s2, hA, "critical")
        text = card_text_full(s2)
        self.assertIn(
            " — severity rose (%s → %s) since your decision on pass 1: "
            "security now also reports it (was: dismissed — %s)"
            % ("warning", "critical", REASON), text)

    def test_nearby_card_wording(self):
        s1, s2, hA = nearby_scenario(1)
        self._assert_band(s1, hA, "warning")
        self._assert_band(s2, hA, "warning")
        self.assertIn(
            " — code next to it changed since your decision on pass 1 "
            "(was: dismissed — false positive, guarded upstream)",
            card_text_full(s2))

    def test_joined_card_wording_d10(self):
        s1, s2, hA = joined_scenario()
        self._assert_band(s1, hA, "warning")
        self._assert_band(s2, hA, "warning")
        self.assertIn(
            " — 1 finding here already dismissed (your reason: false "
            "positive, guarded upstream); a new concern from security "
            "joined it", card_text_full(s2))

    def test_compact_forms_fit_budget(self):
        cases = (
            ("nearby", nearby_scenario,
             "code next to it changed since your decision on pass 1"),
            ("severity", new_lane_scenario,
             "severity rose since your decision on pass 1"),
            ("joined", joined_scenario,
             "1 finding here already dismissed; a new concern from security "
             "joined it"),
        )
        for name, scenario, phrase in cases:
            with self.subTest(cause=name):
                s1, s2, hA = scenario()
                self._assert_band(s1, hA, "warning")
                text = card_text_compact(s2)
                self.assertIsInstance(text, str)
                self.assertLessEqual(len(text),
                                     batch_card.CARD_TEXT_MAX_CHARS)
                self.assertIn(phrase, text)



# --------------------------------------------------------------------------- #
# Paths that did NOT reproduce on current code (DECN-01): recorded and
# dropped, never replaced with invented work. Each N row is pinned green
# below by a test that executes the scenario, so the claim is evidence, not
# prose, and the fixes for the reproduced paths cannot break it.
# --------------------------------------------------------------------------- #
_DROPPED = "did not reproduce; dropped — no code change"
DID_NOT_REPRODUCE = (
    {"id": "N1", "decision": "D-03",
     "scenario": "same-file edit outside the window (line 40), no shift; "
                 "with and without a same-agent same-title re-report",
     "probe_result": "decision current; the only re-ask came from band "
                     "noise (R3), not the code path",
     "disposition": _DROPPED},
    {"id": "N2", "decision": "D-08",
     "scenario": "a stronger new finding leads a row that holds a decided "
                 "finding",
     "probe_result": "the decided member keeps its obligation and its "
                     "decision; only the new lead is asked (the D-10 note "
                     "is presentation, covered by the card wording)",
     "disposition": _DROPPED},
    {"id": "N3", "decision": "D-12",
     "scenario": "the flagged line itself is edited and re-reported",
     "probe_result": "new hash, undecided, linked to the earlier decision "
                     "by the successor link (code changed, was: dismissed)",
     "disposition": _DROPPED},
    {"id": "N4", "decision": "D-04",
     "scenario": "Needs-verification line shift / body change",
     "probe_result": "relocation by content and the line-free NV evidence "
                     "keys already keep a shift and re-ask a body change",
     "disposition": _DROPPED},
    {"id": "N5", "decision": "D-11",
     "scenario": "deferred finding, no change, many passes",
     "probe_result": "no timer or age input; the deferral stays put",
     "disposition": _DROPPED},
    {"id": "N6", "decision": "D-13",
     "scenario": "deferred finding, flagged line fixed, re-check resolved",
     "probe_result": "listed in resolved[], counts 0, the gate writes",
     "disposition": _DROPPED},
    {"id": "title-drift", "decision": "D-08",
     "scenario": "same agent re-reports A at the same line with a new title",
     "probe_result": "old hash kept as an obligation (current); the "
                     "new-title row is asked with no note",
     "disposition": "excluded by ROADMAP (duplicate presentation)"},
    {"id": "real-data", "decision": "D-11",
     "scenario": "the owner's real review state (two pass-1 defers)",
     "probe_result": "both closed through a re-check on pass 2",
     "disposition": "no real lost-decision case; fixtures synthetic"},
)


class TestDidNotReproduceRecord(unittest.TestCase):

    def test_did_not_reproduce_record_is_complete(self):
        by_id = {r["id"]: r for r in DID_NOT_REPRODUCE}
        tags = {"N1": "D-03", "N2": "D-08", "N3": "D-12", "N4": "D-04",
                "N5": "D-11", "N6": "D-13"}
        for nid, tag in tags.items():
            with self.subTest(nid=nid):
                self.assertIn(nid, by_id)
                self.assertTrue(by_id[nid]["disposition"].startswith(
                    "did not reproduce; dropped"))
                self.assertEqual(by_id[nid]["decision"], tag)
                self.assertTrue(by_id[nid]["scenario"].strip())
                self.assertTrue(by_id[nid]["probe_result"].strip())
        for row in DID_NOT_REPRODUCE:
            self.assertEqual(set(row), {"id", "scenario", "probe_result",
                                        "decision", "disposition"})


class TestDidNotReproducePins(_Base):
    """GREEN on current code and for the whole phase: the behaviour each
    dropped path already has, which the fixes must not break."""

    def test_n1_far_edit_keeps_decision(self):
        for rereport in (False, True):
            with self.subTest(rereport=rereport):
                L0 = base_file()
                s1, hA = pass1(L0, conf=STABLE_CONF)
                self._assert_band(s1, hA, "warning")
                L1 = list(L0)
                L1[39] = "line_40 = 'changed'"
                finds = ([fresh("bugs", 10, L1, TITLE_A, conf=STABLE_CONF)]
                         if rereport else [])
                s2, _ = run_pass(s1, L1, finds, 2, {F: [[40, 40]]})
                self._assert_band(s2, hA, "warning")
                rec = self._current(s2, hA)
                self.assertEqual(carry_state.decision_state(rec, s2),
                                 "current")
                self.assertEqual(e2e_gate(s2, {}), "write")

    def test_n2_stronger_lead_keeps_decided_member(self):
        L0 = base_file()
        s1, hA = pass1(L0, conf=STABLE_CONF)
        self._assert_band(s1, hA, "warning")
        b = fresh("security", 11, L0, TITLE_C, conf=100, severity="critical",
                  category="injection")
        s2, r2 = run_pass(s1, L0, [b], 2, {F: [[30, 31]]})
        hC = score.stable_hash(F, L0[10], TITLE_C)
        self.assertEqual(r2["findings"][0]["stable_hash"], hC)
        a_members = [m for m in r2["findings"][0]["members"]
                     if m["agent"] == "bugs"]
        self.assertEqual(len(a_members), 1)
        self.assertEqual(a_members[0]["obligation"]["stable_hash"], hA)
        self._assert_band(s2, hA, "warning")
        rec = self._current(s2, hA)
        self.assertEqual(rec.get("absorbed_into"), hC)
        self.assertEqual(carry_state.decision_state(rec, s2), "current")
        shown = [r["stable_hash"] for r in card_rows(s2)]
        self.assertEqual(shown, [hC])

    def test_n3_edited_flagged_line_is_linked_not_closed(self):
        L0 = base_file()
        s1, hA = pass1(L0, conf=STABLE_CONF)
        self._assert_band(s1, hA, "warning")
        L1 = list(L0)
        L1[9] = "line_10 = 'edited'"
        s2, _ = run_pass(s1, L1, [fresh("bugs", 10, L1, TITLE_A,
                                        conf=STABLE_CONF)],
                         2, {F: [[10, 10]]})
        h2 = score.stable_hash(F, L1[9], TITLE_A)
        self.assertNotEqual(h2, hA)
        rec = self._current(s2, h2)
        self.assertIsNone(carry_state.decision_state(rec, s2))
        row = card_row(s2, h2)
        self.assertIsNotNone(row)
        self.assertEqual(row["stale"]["via"], "successor")
        self.assertEqual(row["stale"]["prior_hash"], hA)
        self.assertEqual(row["stale"]["cause"], "code")

    def test_n4_nv_rules_unchanged(self):
        """Reference pin: Needs-verification decisions compare file,
        canonical line, band and the code fingerprint, never the line. The
        behaviour is exercised by test_carry_state.py
        TestNeedsVerificationDecisionEvidence (test_nv_changed_body_re_asks_
        decision, test_nv_equal_window_keeps_decision, ...)."""
        self.assertEqual(carry_state._NV_EVIDENCE_KEYS,
                         ("file", "canonical_line_content", "band",
                          "current_code"))

    def test_n5_no_expiry_many_quiet_passes(self):
        """D-11; test_carry_state.py TestNoExpiry pins the absence of any age
        input. Here a deferral survives five quiet passes."""
        L0 = base_file()
        s, hA = pass1(L0, conf=STABLE_CONF, kind="defer")
        self._assert_band(s, hA, "warning")
        for n in range(2, 7):
            s, _ = run_pass(s, L0, [], n, {F: []})
        self.assertEqual(s["passes"][-1]["pass_number"], 6)
        self._assert_band(s, hA, "warning")
        rec = self._current(s, hA)
        self.assertEqual(carry_state.decision_state(rec, s), "current")
        self.assertEqual(e2e_gate(s, {}), "write")

    def test_n6_deferred_then_fixed_closes_normally(self):
        L0 = base_file()
        s1, hA = pass1(L0, conf=STABLE_CONF, kind="defer")
        self._assert_band(s1, hA, "warning")
        L1 = list(L0)
        L1[9] = "line_10 = 'fixed'"
        req = {"token": "TA", "agents": ["bugs"], "stable_hash": hA,
               "file": F, "line": 10, "agent": "bugs", "title": TITLE_A}
        verdict = {"source": "recheck", "token": "TA", "agent": "bugs",
                   "verdict": "resolved", "reason": "line rewritten"}
        s2, r2 = run_pass(s1, L1, [], 2, {F: [[10, 10]]},
                          recheck_requests=[req], verdicts=[verdict])
        self.assertIn(hA, [x.get("stable_hash")
                           for x in r2.get("resolved", [])])
        self.assertIsNone(record_of(s2, hA))
        self.assertEqual(carry_state.open_findings(s2), [])
        counts = carry_state.finalize_counts(s2, {})
        self.assertEqual((counts["outstanding_cw"],
                          counts["unacknowledged_medium"],
                          counts["undecided_nv"]), (0, 0, 0))
        self.assertEqual(e2e_gate(s2, {}), "write")



# --------------------------------------------------------------------------- #
# Cross-module guards: invariants no single module owns.
# --------------------------------------------------------------------------- #
class TestCrossModuleGuards(_Base):

    def test_band_rank_mirrors_score(self):
        self.assertEqual(carry_state._BAND_RANK,
                         {k: v for k, v in score._BAND_SEVERITY.items()
                          if k is not None})

    def test_simulator_matches_locked_prose(self):
        """The relocation simulator and the shipped orchestrator prose say
        the same thing: the simulator documents the three relocation cases
        (and the tie) and leaves the request line to the prose; the prose
        holds every locked decided-relocation phrase."""
        import test_nv_render
        doc = relocate_decided.__doc__
        for phrase in ("case 1", "case 2", "case 3", "tie",
                       "30-collect-score.md"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, doc)
        flat = " ".join(doc.split())
        self.assertIn("`$RECHECK_REQUESTS` entry to the relocated line is "
                      "the prose's responsibility, not this simulator's", flat)
        collect = test_nv_render._read(test_nv_render.COLLECT)
        section = test_nv_render._section(collect,
                                          test_nv_render.DECIDED_START,
                                          test_nv_render.DECIDED_END)
        self.assertTrue(section.strip(), "decided-record paragraph missing")
        for phrase in test_nv_render.DECIDED_RELOCATION_PHRASES:
            with self.subTest(phrase=phrase[:40]):
                self.assertIn(test_nv_render.norm(phrase),
                              test_nv_render.norm(section))
        self.assertTrue(test_nv_render.decided_relocation_holds(collect))

    def _assert_decided_matches(self, state):
        recs = carry_state.open_findings(state)
        self.assertIsNotNone(recs)
        want = {r["stable_hash"] for r in recs
                if carry_state.decision_state(r, state) == "current"}
        self.assertEqual(set(carry_state.decided(state)), want)
        return want

    def test_decided_subcommand_matches_decision_state(self):
        # R1a: a decided row relocated after a line shift.
        L0 = base_file()
        s1, hA = pass1(L0, conf=REHASH_CONF)
        L1 = INSERTED + L0
        s2, _ = run_pass(s1, L1, [], 2, {F: [[1, 3]]},
                         decided=target_decided(s1))
        self._assert_band(s2, hA, "warning")
        self.assertEqual(self._assert_decided_matches(s2), {hA})
        # R6: the covered member split into its own row inherits the
        # decision, so `decided` lists it although it has no decision itself.
        _, _, s6, _, hB, hA6 = split_scenario()
        self._assert_band(s6, hA6, "warning")
        self.assertNotIn(hA6, s6["decisions"])
        self.assertIsNotNone(carry_state.covering_decision(
            record_of(s6, hA6), s6))
        self.assertIn(hA6, self._assert_decided_matches(s6))

    def test_nearby_window_is_phase56_window(self):
        """The decision re-ask window and the re-check trigger window are one
        definition: with nothing touched, the trigger is exactly the nearby
        change."""
        rec = {"file": F, "line": 10}
        pairs = []
        for at in range(7, 18):
            pairs.append((10, {F: [[at, at]]}))
        pairs += [
            (10, {F: []}), (10, {}), (10, {"src/other.py": [[10, 15]]}),
            (10, {F: [[1, 9]]}), (10, {F: [[1, 10]]}), (10, {F: [[16, 40]]}),
            (10, {F: [[15, 40]]}), (1, {F: [[6, 6]]}), (1, {F: [[7, 7]]}),
            # D-14: line-1 clip hit, and 6 above the line misses.
            (3, {F: [[1, 1]]}), (10, {F: [[4, 4]]}),
        ]
        self.assertEqual(len(pairs), 22)
        for line, ranges in pairs:
            with self.subTest(line=line, ranges=ranges):
                r = dict(rec, line=line)
                self.assertEqual(score._nearby_changed(r, ranges),
                                 score._independent_trigger(r, set(), ranges))
        # D-14 symmetric window (line 10 -> 5..15; line 1 -> 1..6; line 3 ->
        # 1..8). The 14 hits: line 10 with an edit at 7..15 (9), [[1, 9]],
        # [[1, 10]], [[15, 40]], line 1 with [[6, 6]], line 3 with [[1, 1]].
        hits = [(line, ranges) for line, ranges in pairs
                if score._nearby_changed(dict(rec, line=line), ranges)]
        self.assertEqual(len(hits), 14, hits)

    def test_split_row_snapshot_is_the_split_pass_shape(self):
        """test_carry_state TestGapClosure57 `_inherited_split_pass2` is a
        legitimate fixture only because score.py writes this exact snapshot
        shape on the split pass: a fresh snapshot at the split pass with
        `nearby_at` at that pass when the causing edit is inside the member's
        D-14 window (D-17). This guard fails if the producer and that
        hand-built consumer fixture drift apart (WR-02)."""
        _, s1, s2, r2, hB, hA = split_scenario(real_diff=True)
        snapshot = self._current(s2, hA)["snapshot"]
        self.assertEqual(set(snapshot),
                         {"at_pass", "file", "line", "canonical_line_content",
                          "band", "nearby_at"})
        self.assertEqual(snapshot["at_pass"], 2)
        self.assertEqual(snapshot["nearby_at"], 2)
        self.assertEqual(snapshot["line"], 10)
        self.assertEqual(snapshot["file"], F)


# --------------------------------------------------------------------------- #
# The owner's journey across eight passes (DECN-02/03; Phase 56 found two
# false-closure blockers that one-path-at-a-time tests missed).
# --------------------------------------------------------------------------- #
TITLE_D = "Missing audit log at D"
# conf 55 compliance (+20 for the lane): weak enough to be absorbed into the
# decided row on pass 6, strong enough to stay a row of its own on pass 7.
COMPLIANCE_CONF = 55


def e2e_pass2(decided_read=None):
    """Passes 1-2 of the journey: `bugs` A at line 10 dismissed, then 3 lines
    inserted above with nothing else changed. `decided_read` stands in for
    `carry_state.decided` (default: the real read). -> (L1, s2, hA)."""
    L0 = base_file()
    s1, hA = pass1(L0, conf=STABLE_CONF)
    read = decided_read or carry_state.decided
    L1 = INSERTED + L0
    s2, _ = run_pass(s1, L1, [], 2, {F: [[1, 3]]},
                     decided=frozenset(read(s1) or []))
    return L1, s1, s2, hA


class TestPhase57EndToEnd(_Base):

    def test_owner_is_asked_exactly_when_evidence_changes(self):
        def shown(state):
            rows = card_rows(state)
            self.assertIsInstance(rows, list, rows)
            return rows

        # Pass 1: reported and dismissed -> the gate writes.
        L1, s1, s, hA = e2e_pass2()
        self._assert_band(s1, hA, "warning")
        self.assertEqual(e2e_gate(s1, {}), "write")
        self.assertEqual(shown(s1), [])

        # Pass 2: 3 lines inserted above; the decision follows the code.
        self._assert_band(s, hA, "warning")
        self.assertEqual(self._current(s, hA)["line"], 13)
        self.assertEqual(carry_state.decision_state(record_of(s, hA), s),
                         "current")
        self.assertEqual(e2e_gate(s, {}), "write")
        self.assertEqual(shown(s), [])

        # Pass 3: the line beneath the flagged one is edited -> asked.
        L2 = list(L1)
        L2[13] = "line_11 = 'edited'"
        s, _ = run_pass(s, L2, [], 3, {F: [[14, 14]]},
                        decided=target_decided(s))
        self._assert_band(s, hA, "warning")
        rec = self._current(s, hA)
        self.assertEqual(carry_state.stale_cause(rec, s), "nearby")
        self.assertNotEqual(e2e_gate(s, {}), "write")
        self.assertEqual([r["stable_hash"] for r in shown(s)], [hA])
        self.assertIn(" — code next to it changed since your decision on "
                      "pass 1 (was: dismissed — %s)" % REASON,
                      card_text_full(s))
        s = decide_on(s, hA)  # the owner re-dismisses on pass 3

        # Pass 4: quiet -> not asked; the stamp is carried.
        s, _ = run_pass(s, L2, [], 4, {F: []}, decided=target_decided(s))
        self._assert_band(s, hA, "warning")
        rec = self._current(s, hA)
        self.assertEqual(row_of(s, hA)["snapshot"].get("nearby_at"), 3)
        self.assertEqual(carry_state.decision_state(rec, s), "current")
        self.assertEqual(e2e_gate(s, {}), "write")
        self.assertEqual(shown(s), [])

        # Pass 5: `security` also reports it and the band rises -> asked,
        # naming the new lane (not the nearby edit already decided).
        sec = fresh("security", 13, L2, TITLE_A, conf=100,
                    severity="critical", category="injection")
        s, _ = run_pass(s, L2, [sec], 5, {F: []}, decided=target_decided(s))
        self._assert_band(s, hA, "critical")
        rec = self._current(s, hA)
        self.assertEqual(row_of(s, hA)["snapshot"].get("nearby_at"), 3)
        self.assertEqual(carry_state.stale_cause(rec, s), "severity")
        self.assertEqual(carry_state.gained_lanes(rec, s), ["security"])
        self.assertNotEqual(e2e_gate(s, {}), "write")
        rows = shown(s)
        self.assertEqual([r["stable_hash"] for r in rows], [hA])
        self.assertEqual(rows[0]["stale"]["gained"], ["security"])
        self.assertIn(" — severity rose (warning → critical) since your "
                      "decision on pass 3: security now also reports it "
                      "(was: dismissed — %s)" % REASON, card_text_full(s))
        s = decide_on(s, hA)  # dismissed again on pass 5

        # Pass 6: a different `compliance` concern is absorbed into the row
        # -> the whole row is asked once, with the D-10 note. The decision
        # covered one concern reported by two lanes (bugs and security),
        # which counts once (D-15).
        comp = fresh("compliance", 14, L2, TITLE_D, conf=COMPLIANCE_CONF,
                     severity="medium", category="compliance")
        s, _ = run_pass(s, L2, [comp], 6, {F: []}, decided=target_decided(s))
        self._assert_band(s, hA, "critical")
        row = row_of(s, hA)
        self.assertIn(("compliance", TITLE_D),
                      [(m["agent"], m["title"]) for m in row["members"]])
        rec = self._current(s, hA)
        self.assertEqual(carry_state.stale_cause(rec, s), "joined")
        self.assertNotEqual(e2e_gate(s, {}), "write")
        rows = shown(s)
        self.assertEqual([r["stable_hash"] for r in rows], [hA])
        self.assertEqual(rows[0]["stale"]["joined"], ["compliance"])
        self.assertIn(" — 1 finding here already dismissed (your reason: "
                      "%s); a new concern from compliance joined it" % REASON,
                      card_text_full(s))
        self.assertEqual(rows[0]["stale"]["covered"], 1)
        s = decide_on(s, hA)  # the owner dismisses the row on pass 6
        # The entry records the row band and the lanes reporting the
        # compliance concern: what an inherited decision is compared to.
        self.assertIn({"agent": "compliance", "file": F, "title": TITLE_D,
                       "code": L2[13], "band": "critical",
                       "lanes": ["compliance"]}, s["decisions"][hA]["covers"])

        # Pass 7: line 13 is rewritten and both lanes that reported it answer
        # their re-check `resolved`; the compliance member becomes a row of
        # its own under the row decision. The rewrite of line 13 is the
        # code next to it (line 14), so it is asked once with "code next to
        # it changed" (D-17: no exemption for the neighbour's own fix).
        L3 = list(L2)
        L3[12] = "line_10 = 'fixed'"
        reqs = [{"token": "TS", "agents": ["security"], "stable_hash": hA,
                 "file": F, "line": 13, "agent": "security",
                 "title": TITLE_A},
                {"token": "TB", "agents": ["bugs"], "stable_hash": None,
                 "file": F, "line": 13, "agent": "bugs", "title": TITLE_A}]
        verdicts = [{"source": "recheck", "token": t, "agent": a,
                     "verdict": "resolved", "reason": "line rewritten"}
                    for t, a in (("TS", "security"), ("TB", "bugs"))]
        s, r7 = run_pass(s, L3, [], 7, {F: [[13, 13]]},
                         decided=target_decided(s), recheck_requests=reqs,
                         verdicts=verdicts)
        self.assertIn(hA, [x.get("stable_hash") for x in r7["resolved"]])
        self.assertIsNone(record_of(s, hA))
        hD = score.stable_hash(F, L2[13], TITLE_D)
        self._assert_band(s, hD, "warning")
        rec = self._current(s, hD)
        self.assertNotIn(hD, s["decisions"])
        self.assertEqual(carry_state.covering_decision(rec, s),
                         (hA, s["decisions"][hA]))
        self.assertEqual(rec["snapshot"].get("nearby_at"), 7)
        self.assertEqual(carry_state.decision_state(rec, s), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s), "nearby")
        self.assertNotEqual(e2e_gate(s, {}), "write")
        self.assertEqual([r["stable_hash"] for r in shown(s)], [hD])
        s = decide_on(s, hD)  # the owner dismisses the split row on pass 7

        # Pass 8: quiet -> not asked; the owner's own decision holds.
        s, _ = run_pass(s, L3, [], 8, {F: []}, decided=target_decided(s))
        self._assert_band(s, hD, "warning")
        rec = self._current(s, hD)
        self.assertIn(hD, s["decisions"])
        self.assertEqual(carry_state.decision_state(rec, s), "current")
        self.assertEqual(e2e_gate(s, {}), "write")
        self.assertEqual(shown(s), [])


class TestSameHashLeadKeepsNearbyStamp(_Base):
    """Found by the end-to-end journey: a second lane re-reporting a decided
    finding on the same code (same hash) and out-scoring the carried row used
    to take the lead with a fresh snapshot, dropping the row's `nearby_at`
    stamp. A re-ask still owed for a nearby edit then vanished and the gate
    wrote (silent finding loss)."""

    def test_owed_nearby_reask_survives_a_fresh_same_hash_lead(self):
        L0 = base_file()
        s1, hA = pass1(L0, conf=STABLE_CONF)
        L2 = list(L0)
        L2[10] = "line_11 = 'edited'"
        s2, _ = run_pass(s1, L2, [], 2, {F: [[11, 11]]})
        self._assert_band(s2, hA, "warning")
        self.assertEqual(carry_state.stale_cause(record_of(s2, hA), s2),
                         "nearby")
        # The owner has not answered; `security` now reports the same
        # finding at a score that out-ranks the carried row, band unchanged.
        sec = fresh("security", 10, L2, TITLE_A, conf=95,
                    category="injection")
        s3, _ = run_pass(s2, L2, [sec], 3, {F: []})
        self._assert_band(s3, hA, "warning")
        row = row_of(s3, hA)
        self.assertEqual(row["agent"], "security")  # the fresh lane leads
        self.assertEqual(row["snapshot"].get("nearby_at"), 2)
        rec = self._current(s3, hA)
        self.assertEqual(carry_state.decision_state(rec, s3), "stale")
        self.assertEqual(carry_state.stale_cause(rec, s3), "nearby")
        self.assertNotEqual(e2e_gate(s3, {}), "write")


class TestPhase57Mutants(_Base):
    """Guards that span modules: each mutant removes one link and the
    journey's assertion it protects fails."""

    def test_decided_read_returning_empty_loses_the_relocation(self):
        _, _, s2, hA = e2e_pass2()
        rec = self._current(s2, hA)
        self.assertEqual((rec["line"], carry_state.decision_state(rec, s2)),
                         (13, "current"))
        from unittest import mock
        with mock.patch.object(carry_state, "decided", lambda state: []):
            _, _, m2, mh = e2e_pass2()
        self.assertEqual(mh, hA)
        mrec = record_of(m2, hA)
        self.assertFalse(mrec is not None and mrec.get("line") == 13
                         and carry_state.decision_state(mrec, m2) == "current",
                         "the binding did not matter")
        # The stored-line read pins the row to line 10 (re-read code).
        self.assertEqual([f["line"] for f in m2["passes"][-1]["findings"]],
                         [10])

    def test_nearby_window_upper_bound_dropped_misses_offset_five(self):
        from unittest import mock
        from test_confirmed_fix import SCORE_PY, _mutant
        with open(SCORE_PY, "r", encoding="utf-8") as fh:
            src = fh.read()
        old = "range(max(1, line - _NEARBY_LINES), line + _NEARBY_LINES + 1)"
        self.assertEqual(src.count(old), 1, "mutation target not unique")
        mod = _mutant(SCORE_PY, "score_nearby_upper", old,
                      "range(max(1, line - _NEARBY_LINES), line + _NEARBY_LINES)")

        def offset_failures():
            res = unittest.TestResult()
            TestNearbyEdit("test_r2_edit_within_five_beneath_reopens").run(res)
            self.assertEqual(res.errors, [])
            return [str(t) for t, _ in res.failures]

        self.assertEqual(offset_failures(), [])
        with mock.patch.object(score, "_nearby_changed", mod._nearby_changed):
            failed = offset_failures()
        self.assertEqual(len(failed), 1, failed)
        self.assertIn("offset=5", failed[0])

    def test_nearby_window_lower_bound_dropped_misses_edits_above(self):
        """D-14: dropping the lower bound (the window starts at the pinned
        line again) loses every edit above it: offsets 1, 3 and 5 all fail."""
        from unittest import mock
        from test_confirmed_fix import SCORE_PY, _mutant
        with open(SCORE_PY, "r", encoding="utf-8") as fh:
            src = fh.read()
        old = "max(1, line - _NEARBY_LINES)"
        self.assertEqual(src.count(old), 1, "mutation target not unique")
        mod = _mutant(SCORE_PY, "score_nearby_lower", old, "line")

        def offset_failures():
            res = unittest.TestResult()
            TestNearbyEdit("test_r2_edit_within_five_above_reopens").run(res)
            self.assertEqual(res.errors, [])
            return [str(t) for t, _ in res.failures]

        self.assertEqual(offset_failures(), [])
        with mock.patch.object(score, "_nearby_changed", mod._nearby_changed):
            failed = offset_failures()
        self.assertEqual(len(failed), 3, failed)
        for offset in (1, 3, 5):
            self.assertTrue(any("offset=%d" % offset in f for f in failed),
                            (offset, failed))

    _SPLIT_TESTS = ("test_s1_inherited_member_split_by_nearby_fix_is_reasked",
                    "test_s2_own_decision_absorbed_then_split_by_nearby_fix_is_reasked",
                    "test_s3_owed_stamp_survives_the_split",
                    "test_s4_fresh_lead_over_a_carried_member_is_not_stamped")

    def _split_failures(self):
        """The TestSplitPassNearby fixtures that fail, by short prefix."""
        failed = set()
        for name in self._SPLIT_TESTS:
            res = unittest.TestResult()
            TestSplitPassNearby(name).run(res)
            self.assertEqual(res.errors, [])
            if res.failures:
                failed.add(name[:len("test_sN_")])
        return failed

    def test_split_pass_carried_arm_dropped_loses_the_split_edit(self):
        """D-17 guard: `_snapshot_for`'s carried arm stamps a split row whose
        lead record existed before this pass but has no top-level snapshot.
        Without it the inherited split (s1: no obligation to seed a prior
        from) loses the neighbour's fix; the owed stamp (s3, seeded prior) and
        the fresh-lead negative (s4) are unaffected."""
        from unittest import mock
        from test_confirmed_fix import SCORE_PY, _mutant
        with open(SCORE_PY, "r", encoding="utf-8") as fh:
            src = fh.read()
        old = "(isinstance(prior, dict) or carried)"
        self.assertEqual(src.count(old), 1, "mutation target not unique")
        mod = _mutant(SCORE_PY, "score_split_carried", old,
                      "isinstance(prior, dict)")
        self.assertEqual(self._split_failures(), set())
        with mock.patch.object(score, "_snapshot_for", mod._snapshot_for):
            failed = self._split_failures()
        self.assertIn("test_s1_", failed)
        self.assertNotIn("test_s3_", failed)
        self.assertNotIn("test_s4_", failed)

    def test_split_pass_lead_obligation_prior_not_seeded_loses_the_owed_stamp(
            self):
        """D-17 guard: the pooled prior — a row takes, as its prior, the
        pooled snapshot of the carried records under its own hash (here the
        lead member's own obligation), assigned by `survivor["snapshot"] =
        prior`. Without the assignment the re-ask owed before the split (s3),
        the one owed before a same-lane re-report (d) and the far twin's
        stamp (p4) are lost; the carried arm still stamps the split edit (s1)
        and the fresh-lead negative (s4) is unaffected."""
        failed = self._run_mutant(
            "score_split_seed", 'survivor["snapshot"] = prior', "pass")
        self.assertIn("test_s3_", failed)
        self.assertIn("test_d_", failed)
        self.assertIn("test_p4_", failed)
        self.assertNotIn("test_s1_", failed)
        self.assertNotIn("test_s4_", failed)


    _ROW_TESTS = (
        (TestSplitPassNearby,
         "test_s1_inherited_member_split_by_nearby_fix_is_reasked"),
        (TestSplitPassNearby, "test_s3_owed_stamp_survives_the_split"),
        (TestSplitPassNearby,
         "test_s4_fresh_lead_over_a_carried_member_is_not_stamped"),
        (TestSameLaneRereport,
         "test_b_inherited_split_led_by_own_lane_rereport"),
        (TestSameLaneRereport,
         "test_d_owed_stamp_survives_own_lane_rereport_on_quiet_pass"),
        (TestSameLaneRereport, "test_control_carried_copy_leads_at_conf_75"),
        (TestWr01Guards,
         "test_w1_needs_recheck_split_row_keeps_its_hash_and_is_stamped"),
        (TestWr01Guards,
         "test_w2_edited_lead_member_does_not_inherit_the_old_stamp"),
        (TestPooledEvidence,
         "test_p1_cross_lane_same_hash_other_line_nearby_reasks"),
        (TestPooledEvidence, "test_q1_control_carried_copy_leads"),
        (TestPooledEvidence,
         "test_p2_same_lane_arrival_order_does_not_pick_the_outcome"),
        (TestPooledEvidence,
         "test_p3_min_confidence_dropped_twin_keeps_the_reask"),
        (TestPooledEvidence,
         "test_p4_far_twin_latest_stamp_reaches_the_first_copy"),
        (TestPriorGate,
         "test_in01_edited_carried_lead_does_not_carry_its_stamp_onto_the_new_hash"),
        (TestDeferredStaysOpen,
         "test_deferred_covered_member_below_threshold_stays_open"),
        (TestDeferredStaysOpen,
         "test_dismissed_covered_member_below_threshold_may_drop"),
    )

    def _failures(self):
        """The _ROW_TESTS that fail, by short prefix (`test_s1_`, `test_b_`,
        `test_w1_`, `test_control_`); an error (not a failure) fails here."""
        failed = set()
        for cls, name in self._ROW_TESTS:
            res = unittest.TestResult()
            cls(name).run(res)
            self.assertEqual(res.errors, [], name)
            if res.failures:
                failed.add(name[:name.index("_", len("test_")) + 1])
        return failed

    def _run_mutant(self, name, old, new):
        """Failures of _ROW_TESTS with the whole scorer run from `score.py`
        with `old` replaced by `new`; asserts `old` is unique and the row
        tests are green unmutated."""
        from unittest import mock
        from test_confirmed_fix import SCORE_PY, _mutant
        with open(SCORE_PY, "r", encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count(old), 1, "mutation target not unique")
        mod = _mutant(SCORE_PY, name, old, new)
        self.assertEqual(self._failures(), set())
        with mock.patch.object(score, "run", mod.run):
            return self._failures()

    def test_deferral_kind_gate_keeps_a_dismissed_member_open(self):
        """D-20 / WR-02 kind gate: only a member covered by one of the
        owner's DEFERRED hashes is indexed. Without `stored_hash in
        deferred_hashes` a dismissed covered member below threshold is kept
        open too (dismissed lock trips); the deferred case is unaffected."""
        failed = self._run_mutant(
            "score_d20_no_kind_gate",
            "and stored_hash in deferred_hashes", "and True")
        self.assertIn("test_dismissed_", failed)
        self.assertNotIn("test_deferred_", failed)

    def test_no_synthesized_entry_drops_the_deferred_member(self):
        """D-20 / WR-02: without the synthesized carried_obligations entry
        the deferred covered member has no row and leaves the open set (the
        57-20 red returns); the dismiss lock and the split stamp (s1) are
        unaffected."""
        failed = self._run_mutant(
            "score_d20_no_entry",
            "carried_obligations[id(m)] = _covered_entry(",
            "pass  # (")
        self.assertIn("test_deferred_", failed)
        self.assertNotIn("test_dismissed_", failed)
        self.assertNotIn("test_s1_", failed)

    def test_kept_open_covered_row_without_carried_is_not_stamped(self):
        """D-20 with D-17: the kept-open row of a deferred covered member
        has no prior snapshot, so only `carried` lets the split pass's edit
        stamp it. Without it the row reads current, the deferral closes it
        and it is not outstanding; the dismiss lock and a real obligation's
        kept-open row (p3, prior snapshot) are unaffected."""
        failed = self._run_mutant(
            "score_d20_no_carried",
            'carried=bool(entry.get("covered"))', "carried=False")
        self.assertIn("test_deferred_", failed)
        self.assertNotIn("test_dismissed_", failed)
        self.assertNotIn("test_p3_", failed)

    def test_carried_statuses_without_needs_recheck_loses_the_low_entropy_split(
            self):
        """WR-01 arm 1: without `needs-recheck` in _CARRIED_STATUSES the
        hash-preserving needs-recheck split row (w1) is no longer carried, so
        the neighbour's fix is lost; a persisted split (s1) and the seed
        guard (w2) are unaffected."""
        failed = self._run_mutant(
            "score_carried_no_recheck",
            '_CARRIED_STATUSES = ("persisted", "needs-recheck")',
            '_CARRIED_STATUSES = ("persisted",)')
        self.assertIn("test_w1_", failed)
        self.assertNotIn("test_s1_", failed)
        self.assertNotIn("test_w2_", failed)

    def test_seed_without_hash_equality_inherits_a_foreign_stamp(self):
        """WR-01 arm 2 / IN-01: the one hash gate every prior source passes
        (`o.get("stable_hash") == survivor["stable_hash"]`). Without it the
        old record's owed stamp reaches the edited finding's new row, both
        through an edited lead member's obligation (w2) and through an edited
        carried lead's own snapshot (in01); the same-hash priors (s3, d) are
        unaffected."""
        failed = self._run_mutant(
            "score_seed_no_hash",
            'o.get("stable_hash") == survivor["stable_hash"]',
            "True")
        self.assertIn("test_w2_", failed)
        self.assertIn("test_in01_", failed)
        self.assertNotIn("test_s3_", failed)
        self.assertNotIn("test_d_", failed)

    def test_carried_from_lead_only_loses_the_same_lane_rereport(self):
        """Carried-from-any-copy: reading carried-ness off the lead only
        (the pre-fix rule) instead of `row_carried = bool(same_hash)` loses
        the inherited split led by a fresh same-lane re-report (b, nothing to
        seed); the carried-lead control and the seeded owed stamp (d) are
        unaffected."""
        failed = self._run_mutant(
            "score_carried_lead_only",
            "row_carried = bool(same_hash)",
            "row_carried = survivor.get(\"status\") in _CARRIED_STATUSES")
        self.assertIn("test_b_", failed)
        self.assertNotIn("test_control_", failed)
        self.assertNotIn("test_d_", failed)

    def test_index_read_after_filtering_loses_the_dropped_twin(self):
        """Index before every filter (57-REVIEW-GAPS3.md CR-02): when the row
        reads only the carried copies that reached scoring (the pre-fix rule,
        `same_hash` restricted to scored_members), the carried twin the
        min_confidence filter dropped takes its owed re-ask with it (p3); a
        twin that reaches scoring (d) and a split led by the obligation
        member itself (s3) are unaffected."""
        failed = self._run_mutant(
            "score_seed_lead_only",
            'same_hash = carried_by_hash.get(survivor["stable_hash"], ())',
            'same_hash = [e for e in carried_by_hash.get(survivor["stable_hash"], ()) '
            'if any(e[0] is t[1] for t in scored_members)]')
        self.assertIn("test_p3_", failed)
        self.assertNotIn("test_d_", failed)
        self.assertNotIn("test_s3_", failed)

    def test_nearby_judged_at_the_lead_only_loses_the_other_copy(self):
        """CR-01 nearby at every copy: judging nearby at the row's own line
        only loses the edit beside a carried same-hash copy at another line,
        across lanes (p1) and in either same-lane arrival order (p2); the
        control where the carried copy leads (q1) and the inherited split
        (s1) are unaffected."""
        failed = self._run_mutant(
            "score_nearby_lead_only",
            "row_nearby = _any_nearby([survivor] + [r for r, _ in same_hash], "
            "changed_line_ranges)",
            "row_nearby = _nearby_changed(survivor, changed_line_ranges)")
        self.assertIn("test_p1_", failed)
        self.assertIn("test_p2_", failed)
        self.assertNotIn("test_q1_", failed)
        self.assertNotIn("test_s1_", failed)

    def test_line_tie_break_dropped_makes_the_lead_arrival_dependent(self):
        """CR-01 arrival order: without the line as the member sort's final
        tie-break, two fully tied same-lane records of one identity are led by
        whichever arrived first, so the [12, 10] order leads at line 12 (p2's
        lead marker); the cross-lane copy (p1) and the dropped twin (p3) are
        unaffected."""
        failed = self._run_mutant(
            "score_no_line_tie_break",
            '_as_line(t[1].get("line")) or 0,',
            "0,")
        self.assertIn("test_p2_", failed)
        self.assertNotIn("test_p1_", failed)
        self.assertNotIn("test_p3_", failed)

    def test_prior_rank_first_wins_loses_the_latest_stamp(self):
        """D-19 latest stamp: the pooled prior is ranked, never positional.
        In the far-twin fixture's pass 3 the line-10 row's candidates arrive
        as [line-10 obligation (unstamped), line-30 obligation (nearby_at 2),
        the lead's own line-10 snapshot (unstamped)], so taking the first
        candidate hands the line-10 row — the record carry_state reads — no
        stamp (p4); the dropped twin (p3) and the same-lane re-report (d) are
        unaffected."""
        failed = self._run_mutant(
            "score_prior_first_wins",
            "return min(candidates, key=_prior_rank)",
            "return candidates[0]")
        self.assertIn("test_p4_", failed)
        self.assertNotIn("test_p3_", failed)
        self.assertNotIn("test_d_", failed)


class TestPooledPriorUnit(unittest.TestCase):
    """score._pooled_prior / score._prior_rank: the latest owed stamp wins,
    then the oldest at_pass; never positional; never raises."""

    def test_no_candidates_is_none(self):
        self.assertIsNone(score._pooled_prior([]))

    def test_stamped_snapshot_wins_over_an_unstamped_older_one(self):
        old = {"at_pass": 2}
        stamped = {"at_pass": 3, "nearby_at": 3}
        self.assertIs(score._pooled_prior([old, stamped]), stamped)
        self.assertIs(score._pooled_prior([stamped, old]), stamped)

    def test_equal_stamps_take_the_oldest_at_pass(self):
        older = {"at_pass": 1, "nearby_at": 2}
        newer = {"at_pass": 3, "nearby_at": 2}
        self.assertIs(score._pooled_prior([newer, older]), older)
        self.assertIs(score._pooled_prior([older, newer]), older)

    def test_later_stamp_wins_over_an_earlier_one(self):
        early = {"at_pass": 1, "nearby_at": 2}
        late = {"at_pass": 2, "nearby_at": 4}
        self.assertIs(score._pooled_prior([early, late]), late)

    def test_non_int_nearby_at_ranks_after_a_stamped_one(self):
        bad = {"at_pass": 1, "nearby_at": "2"}
        stamped = {"at_pass": 3, "nearby_at": 2}
        self.assertIs(score._pooled_prior([bad, stamped]), stamped)
        self.assertLess(score._prior_rank(stamped), score._prior_rank(bad))

    def test_prior_rank_never_raises(self):
        for snap in ({}, {"nearby_at": None, "at_pass": "x"},
                     {"nearby_at": True, "at_pass": 1.5}, None, []):
            with self.subTest(snap=snap):
                score._prior_rank(snap)


if __name__ == "__main__":
    unittest.main()
