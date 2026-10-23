"""Confirmed-fix closure for Needs-verification items.

A Needs-verification item whose raising lane is not re-dispatched (the Codex
lane, a gated lane) can close only through an owner decision or verified
evidence. This file pins the evidence-bound route: an owner-named fix whose
`applied` result is backed by
  - a fix commit that exists and touches the finding's file,
  - the fix agent's own re-check and after-check (`check.outcome` passed or
    not-run, never failed/timeout/unavailable),
  - the repaired code at HEAD: the file's blob in that commit equals HEAD's
    blob, and the file was clean (HEAD = index = working tree) before and after
    the batch, so the verified bytes are the committed bytes,
is recorded as a fix verdict `applied` bound to the finding's stable_hash, the
commit and that blob.

That record is evidence, never a closure (owner decision, fix-1 follow-ups,
S9): the fixer's own check cannot close the item. On the next pass the item is
re-checked by a reviewer other than the fixer, batched into the ordinary
rerun: the raising lane when it is dispatched, otherwise a deterministic
eligible native lane that is (a Codex-raised item, a gated or undispatched
lane). The routed `<recheck>` request names the finding's stable_hash and the
code snapshot the reviewer judged (`snapshot_blob`). The item closes
automatically, as "Resolved by verification (confirmed-fix)", only when that
reviewer answers `resolved` on the routed token AND the reviewed snapshot, the
repaired blob and HEAD's blob at collect time are the same. `still-applies`,
no answer, no eligible reviewer, or a snapshot mismatch keeps it open with a
clear `verdict: confirmed fix …` reason. Finalize without a rerun never closes
it; it lists the item as awaiting the re-check. No owner card is added.

Confirmation alone (`fix N` with no applied result), an applied patch without
that evidence, the fixer's check alone, or the lane's absence never closes the
item.
"""

import json
import os
import re
import sys
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import batch_card  # noqa: E402
import carry_state  # noqa: E402
import score  # noqa: E402
import state_shape  # noqa: E402
from test_score import _nv, _nv_cf, _nv_env, _nv_rows  # noqa: E402

PLUGIN_DIR = os.path.normpath(os.path.join(HERE, ".."))
CARRY_STATE_PY = os.path.join(HERE, "carry_state.py")
SCORE_PY = os.path.join(HERE, "score.py")
FUTURE = state_shape.load_schema("future")

F = "src/nv.py"
SHA = "c0ffee" + "0" * 34
BLOB = "1" * 40
NVH = "a" * 64
WH = "b" * 64
CHECK_PASSED = {"kind": "test", "command": "pytest -q", "outcome": "passed",
                "label": "verified by `pytest -q`"}


def _read(rel):
    with open(os.path.join(PLUGIN_DIR, rel), "r", encoding="utf-8") as fh:
        return fh.read()


def nv_row(h=NVH, file=F, status="needs-recheck"):
    return {"id": "x-" + h[:6], "file": file, "line": 12, "title": "nv " + h[:4],
            "agent": "codex-adversarial", "band": carry_state.NV_BAND,
            "status": status, "stable_hash": h,
            "members": [{"file": file, "line": 12, "title": "nv",
                         "agent": "codex-adversarial",
                         "obligation": carry_state.NV_MEMBER_OBLIGATION}]}


def warning_row(h=WH, file=F):
    return {"id": "x-" + h[:6], "file": file, "line": 30, "title": "w",
            "agent": "bugs", "band": "warning", "status": "new",
            "stable_hash": h}


def state_with(*rows, **roots):
    s = {"medium_acknowledgments": {},
         "passes": [{"pass_number": 1, "head_sha": "h1", "diff_range": "a..b",
                     "findings": list(rows)}]}
    s.update(roots)
    return s


def applied_result(h=NVH, **over):
    r = {"id": h, "status": "applied", "commit_sha": SHA, "files_touched": [F],
         "check": dict(CHECK_PASSED), "summary": "validate parse_limit"}
    r.update(over)
    return r


def payload(results=None, sent=(NVH,), commits=None, clean=None, **over):
    p = {"at_pass": 1, "head_sha": "d" * 40, "sent": list(sent),
         "results": results if results is not None else [applied_result()],
         "blobs": {},
         "commits": commits if commits is not None
         else {SHA: {"files": [F], "blobs": {F: BLOB}}},
         "clean_head_blobs": clean if clean is not None else {F: BLOB}}
    p.update(over)
    return p


def record(state, p):
    skipped = []
    out = carry_state.record_fix_verdicts(state, p, skipped)
    return out, skipped


# --------------------------------------------------------------------------- #
# Recording (carry_state.record_fix_verdicts)
# --------------------------------------------------------------------------- #
class TestRecordConfirmedFix(unittest.TestCase):
    def test_full_evidence_records_applied_verdict(self):
        out, skipped = record(state_with(nv_row()), payload())
        self.assertEqual(skipped, [])
        self.assertEqual(out["fix_verdicts"][NVH], {
            "verdict": "applied", "agent": "fix", "head_sha": "d" * 40,
            "at_pass": 1, "verified_blob": BLOB, "commit_sha": SHA,
            "reason": "validate parse_limit"})

    def test_not_run_check_is_the_fix_agents_recheck(self):
        check = {"kind": "none", "command": "", "outcome": "not-run",
                 "label": "problem re-checked; no automated check available"}
        out, _ = record(state_with(nv_row()),
                        payload(results=[applied_result(check=check)]))
        self.assertEqual(out["fix_verdicts"][NVH]["verdict"], "applied")

    def _assert_not_recorded(self, state, p, skipped_expected=True):
        out, skipped = record(state, p)
        self.assertIsNotNone(out)
        self.assertNotIn(NVH, out.get("fix_verdicts", {}))
        if skipped_expected:
            self.assertEqual(skipped, [NVH])

    def test_confirmation_alone_records_nothing(self):
        """`fix N` was typed but the fix agent returned no applied result."""
        for status in ("needs-human", "unverified", "errored",
                       "applied-uncommitted"):
            with self.subTest(status=status):
                out, skipped = record(
                    state_with(nv_row()),
                    payload(results=[applied_result(status=status,
                                                    commit_sha=None)]))
                self.assertEqual(out.get("fix_verdicts", {}), {})
        out, _ = record(state_with(nv_row()), payload(results=[]))
        self.assertEqual(out.get("fix_verdicts", {}), {})

    def test_not_owner_named_records_nothing(self):
        self._assert_not_recorded(state_with(nv_row()), payload(sent=[]),
                                  skipped_expected=False)

    def test_applied_patch_without_evidence_records_nothing(self):
        row = state_with(nv_row())
        cases = {
            "no commit facts": payload(commits={}),
            "commit misses the file": payload(
                commits={SHA: {"files": ["src/other.py"],
                               "blobs": {F: BLOB}}}),
            "file edited after the fix": payload(clean={F: "2" * 40}),
            "file dirty before or after": payload(clean={}),
            "no commit sha": payload(results=[applied_result(commit_sha=None)]),
            "short commit sha": payload(
                results=[applied_result(commit_sha="c0ffee")],
                commits={"c0ffee": {"files": [F], "blobs": {F: BLOB}}}),
            "file not in files_touched": payload(
                results=[applied_result(files_touched=["src/other.py"])]),
            "check failed": payload(results=[applied_result(
                check=dict(CHECK_PASSED, outcome="failed"))]),
            "check unavailable": payload(results=[applied_result(
                check=dict(CHECK_PASSED, outcome="unavailable"))]),
            "no check": payload(results=[applied_result(check=None)]),
        }
        for name, p in cases.items():
            with self.subTest(name):
                self._assert_not_recorded(row, p)

    def test_non_nv_applied_records_nothing(self):
        out, skipped = record(
            state_with(warning_row(h=NVH)), payload())
        self.assertEqual(out.get("fix_verdicts", {}), {})
        self.assertEqual(skipped, [])

    def test_obsolete_path_unchanged(self):
        p = payload(results=[{"id": NVH, "status": "obsolete",
                              "summary": "gone"}], blobs={F: BLOB})
        out, _ = record(state_with(nv_row()), p)
        self.assertEqual(out["fix_verdicts"][NVH]["verdict"], "obsolete")
        self.assertNotIn("commit_sha", out["fix_verdicts"][NVH])

    def test_malformed_evidence_containers_refuse(self):
        for key, bad in (("commits", []), ("commits", "x"),
                         ("clean_head_blobs", []), ("clean_head_blobs", 3)):
            with self.subTest(key=key, value=bad):
                self.assertIsNone(carry_state.record_fix_verdicts(
                    state_with(nv_row()), payload(**{key: bad})))


# --------------------------------------------------------------------------- #
# Finalize counts (no rerun): the same HEAD-blob rule as fix-obsolete
# --------------------------------------------------------------------------- #
def applied_verdict(blob=BLOB, at_pass=1, **over):
    v = {"verdict": "applied", "agent": "fix", "head_sha": "d" * 40,
         "at_pass": at_pass, "verified_blob": blob, "commit_sha": SHA,
         "reason": "validate parse_limit"}
    v.update(over)
    return v


def state_two_passes(row, **roots):
    """A state whose pass 2 carried `row` unchanged from pass 1."""
    s = state_with(json.loads(json.dumps(row)), **roots)
    s["passes"].append({"pass_number": 2, "head_sha": "h2", "diff_range": "b..c",
                        "findings": [json.loads(json.dumps(row))]})
    return s


def settled_row(row, fingerprint, at_pass=2, head_sha="e" * 40):
    """`row` as carried after a routed reviewer answered still-applies on the
    code whose blobs are `fingerprint`."""
    out = json.loads(json.dumps(row))
    out["recheck_settled"] = {"verdict": "still-applies", "at_pass": at_pass,
                              "head_sha": head_sha, "fingerprint": dict(fingerprint)}
    return out


class TestFinalizeCountsConfirmedFix(unittest.TestCase):
    """Without a rerun there is no independent re-check: the fixer's evidence
    alone never closes the item. It is listed as awaiting the re-check."""

    def test_fixer_only_evidence_stays_open(self):
        s = state_with(nv_row(), fix_verdicts={NVH: applied_verdict()})
        c = carry_state.finalize_counts(s, {F: BLOB})
        self.assertEqual(c["undecided_nv"], 1)
        self.assertEqual(c["undecided_nv_hashes"], [NVH])
        self.assertEqual(c["confirmed_fix_awaiting_recheck_hashes"], [NVH])
        self.assertNotIn("verified_confirmed_fix_hashes", c)
        self.assertEqual(c["verified_obsolete_hashes"], [])
        self.assertFalse(carry_state.is_closed(nv_row(), s, {F: BLOB}))

    def test_awaiting_listed_whatever_head_holds(self):
        s = state_with(nv_row(), fix_verdicts={NVH: applied_verdict()})
        for blobs in ({F: BLOB}, {F: "2" * 40}, {}, None):
            with self.subTest(blobs=blobs):
                c = carry_state.finalize_counts(s, blobs)
                self.assertEqual(c["undecided_nv_hashes"], [NVH])
                self.assertEqual(c["confirmed_fix_awaiting_recheck_hashes"], [NVH])

    def test_owner_decision_still_closes_and_is_not_awaiting(self):
        s = state_with(nv_row(), fix_verdicts={NVH: applied_verdict()},
                       decisions={NVH: {"decision": "dismiss", "at_pass": 1,
                                        "reason": "accepted risk"}})
        c = carry_state.finalize_counts(s, {F: BLOB})
        self.assertEqual(c["undecided_nv"], 0)
        self.assertEqual(c["confirmed_fix_awaiting_recheck_hashes"], [])

    def test_stale_pass_never_closes(self):
        """An `applied` verdict older than the last pass still never closes at
        finalize (closure needs score.py's resolved[]), but the item is still
        fixed and awaiting its independent re-check."""
        s = state_with(nv_row(), fix_verdicts={NVH: applied_verdict(at_pass=0)})
        c = carry_state.finalize_counts(s, {F: BLOB})
        self.assertEqual(c["undecided_nv"], 1)
        self.assertFalse(carry_state.is_closed(nv_row(), s, {F: BLOB}))
        self.assertEqual(c["confirmed_fix_awaiting_recheck_hashes"], [NVH])

    def test_awaiting_listed_at_any_later_pass(self):
        """A rerun that could not confirm the fix (no eligible reviewer) leaves
        the verdict at its original pass; the item is still awaiting."""
        s = state_two_passes(nv_row(status="persisted"),
                             fix_verdicts={NVH: applied_verdict(at_pass=1)})
        c = carry_state.finalize_counts(s, {F: BLOB})
        self.assertEqual(c["undecided_nv_hashes"], [NVH])
        self.assertEqual(c["confirmed_fix_awaiting_recheck_hashes"], [NVH])

    def test_settled_row_not_awaiting(self):
        """A reviewer said it still applies on this exact code: nothing is
        awaiting until the code changes."""
        row = settled_row(nv_row(status="persisted"), {F: BLOB})
        s = state_two_passes(row, fix_verdicts={NVH: applied_verdict(at_pass=1)})
        c = carry_state.finalize_counts(s, {F: BLOB})
        self.assertEqual(c["undecided_nv_hashes"], [NVH])
        self.assertEqual(c["confirmed_fix_awaiting_recheck_hashes"], [])
        c = carry_state.finalize_counts(s, {F: "f" * 40})
        self.assertEqual(c["confirmed_fix_awaiting_recheck_hashes"], [NVH])

    def test_applied_without_commit_never_closes(self):
        v = applied_verdict()
        del v["commit_sha"]
        s = state_with(nv_row(), fix_verdicts={NVH: v})
        c = carry_state.finalize_counts(s, {F: BLOB})
        self.assertEqual(c["undecided_nv"], 1)
        self.assertEqual(c["confirmed_fix_awaiting_recheck_hashes"], [])

    def test_applied_on_non_nv_row_never_closes(self):
        s = state_with(warning_row(), fix_verdicts={WH: applied_verdict()})
        c = carry_state.finalize_counts(s, {F: BLOB})
        self.assertEqual(c["outstanding_cw_hashes"], [WH])
        self.assertEqual(c["confirmed_fix_awaiting_recheck_hashes"], [])

    def test_unknown_verdict_never_closes(self):
        s = state_with(nv_row(), fix_verdicts={
            NVH: applied_verdict(verdict="resolved")})
        self.assertEqual(carry_state.finalize_counts(s, {F: BLOB})["undecided_nv"], 1)

    def test_obsolete_list_unchanged(self):
        s = state_with(nv_row(), fix_verdicts={NVH: {
            "verdict": "obsolete", "agent": "fix", "head_sha": "h", "at_pass": 1,
            "verified_blob": BLOB, "reason": "gone"}})
        c = carry_state.finalize_counts(s, {F: BLOB})
        self.assertEqual(c["verified_obsolete_hashes"], [NVH])
        self.assertEqual(c["confirmed_fix_awaiting_recheck_hashes"], [])


# --------------------------------------------------------------------------- #
# Rerun (score.py): the carried NV row moves into resolved[] on the evidence
# --------------------------------------------------------------------------- #
def confirmed_verdict(h, blob=BLOB, head_blob=BLOB, at_pass=1, **over):
    v = {"source": "confirmed-fix", "stable_hash": h, "agent": "fix",
         "verdict": "applied", "at_pass": at_pass, "head_sha": "d" * 40,
         "reason": "validate parse_limit", "verified_blob": blob,
         "head_blob": head_blob, "commit_sha": SHA}
    v.update(over)
    return v


def _rejections(r):
    return [x["reason"] for x in r.get("filtered", [])
            if str(x.get("reason", "")).startswith("verdict:")]


HEAD2 = "e" * 40
R_NO_REVIEWER = ("verdict: confirmed fix awaiting independent re-check: "
                 "no eligible reviewer this pass")
R_NO_ANSWER = ("verdict: confirmed fix awaiting independent re-check: "
               "the routed reviewer gave no verdict")
R_STILL = ("verdict: confirmed fix not verified: the routed reviewer says "
           "it still applies")
R_SNAPSHOT = ("verdict: confirmed fix not verified: the reviewed code is not "
              "the repaired code")
R_ORPHAN_ROUTED = "verdict: routed re-check without a confirmed fix"
R_STALE = "verdict: stale fix verdict"
R_EVIDENCE_CHANGED = "verdict: evidence changed since verification"
R_CF_SETTLED = ("verdict: confirmed fix not verified: the routed reviewer said "
                "it still applies and the code is unchanged since")
HEAD2_BLOB = "2" * 40
BLOB2 = "4" * 40


def routed_request(row, token="R1", agents=("bugs",), snapshot=BLOB, **over):
    """The Phase 2 request for a confirmed-fix re-check routed to a reviewer
    other than the fixer (20-dispatch.md step 3)."""
    req = {"token": token, "agents": list(agents),
           "stable_hash": row["stable_hash"], "file": row["file"],
           "line": row["line"], "agent": row["agent"], "title": row["title"],
           "route": "confirmed-fix", "snapshot_blob": snapshot}
    req.update(over)
    return req


def reviewer_verdict(token="R1", agent="bugs", verdict="resolved",
                     reason="parse_limit is range-checked before use"):
    return {"source": "recheck", "token": token, "agent": agent,
            "verdict": verdict, "reason": reason}


class TestScoreConfirmedFix(unittest.TestCase):
    def _pass1(self):
        rows = _nv_rows(score.run(_nv_env([_nv()])))
        self.assertEqual(len(rows), 1)
        return rows[0]

    def _pass2(self, cf, verdicts):
        return score.run(_nv_env([], carryforward=[cf], pass_number=2,
                                 head_sha="e" * 40, verdicts=verdicts))

    def test_fixer_only_evidence_stays_open(self):
        """The fix agent's own check is recorded evidence; with no
        independent re-check it closes nothing and says why."""
        p1 = self._pass1()
        cf = _nv_cf(p1, None, None)  # the fix changed the code: not located
        r = self._pass2(cf, [confirmed_verdict(p1["stable_hash"])])
        rows = _nv_rows(r)
        self.assertEqual(len(rows), 1)
        self.assertNotIn("resolved", r)
        self.assertEqual(_rejections(r), [R_NO_REVIEWER])
        rej = [x for x in r["filtered"] if x["reason"] == R_NO_REVIEWER][0]
        self.assertEqual((rej["file"], rej["line"], rej["title"]),
                         (rows[0]["file"], rows[0]["line"], rows[0]["title"]))

    def test_lane_absent_stays_open(self):
        p1 = self._pass1()
        r = self._pass2(_nv_cf(p1, None, None), [])
        rows = _nv_rows(r)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "needs-recheck")
        self.assertNotIn("resolved", r)

    def test_head_moved_since_fix_stays_open(self):
        p1 = self._pass1()
        r = self._pass2(_nv_cf(p1, None, None),
                        [confirmed_verdict(p1["stable_hash"], head_blob="2" * 40)])
        self.assertEqual(len(_nv_rows(r)), 1)
        self.assertEqual(_rejections(r),
                         ["verdict: evidence changed since verification"])

    def test_dirty_file_stays_open(self):
        p1 = self._pass1()
        r = self._pass2(_nv_cf(p1, None, None),
                        [confirmed_verdict(p1["stable_hash"], head_blob=None)])
        self.assertEqual(len(_nv_rows(r)), 1)

    def test_stale_verdict_stays_open(self):
        """Stale means the code changed since the fix was verified, at any
        age: an older verdict on a changed blob never closes."""
        p1 = self._pass1()
        r = self._pass2(_nv_cf(p1, None, None),
                        [confirmed_verdict(p1["stable_hash"], at_pass=0,
                                           head_blob=HEAD2_BLOB)])
        self.assertEqual(len(_nv_rows(r)), 1)
        self.assertNotIn("resolved", r)
        self.assertIn(R_EVIDENCE_CHANGED, _rejections(r))
        self.assertNotIn(R_STALE, _rejections(r))

    def test_malformed_confirmed_verdict_rejected(self):
        p1 = self._pass1()
        good = confirmed_verdict(p1["stable_hash"])
        for bad in ({k: v for k, v in good.items() if k != "commit_sha"},
                    dict(good, commit_sha=5), dict(good, verdict="obsolete"),
                    dict(good, at_pass="1")):
            with self.subTest(bad=sorted(set(good.items()) ^ set(bad.items()),
                                         key=str)[:2]):
                r = self._pass2(_nv_cf(p1, None, None), [bad])
                self.assertEqual(len(_nv_rows(r)), 1)
                self.assertIn("verdict: malformed", _rejections(r))

    def test_confirmed_fix_never_closes_a_non_nv_row(self):
        f = _nv()
        del f["needs_verification"]
        f["agent_confidence"] = 95
        p1 = score.run(_nv_env([f]))["findings"][0]
        self.assertNotEqual(p1["band"], score.NV_BAND)
        cf = json.loads(json.dumps(p1))
        cf["canonical_line_content"] = "something else entirely"
        cf["canonical_window"] = "something else entirely"
        r = self._pass2(cf, [confirmed_verdict(p1["stable_hash"])])
        self.assertNotIn("resolved", r)
        self.assertEqual(_rejections(r),
                         ["verdict: confirmed fix on a non-needs-verification record"])

    def test_obsolete_path_unchanged(self):
        p1 = self._pass1()
        v = {"source": "fix-obsolete", "stable_hash": p1["stable_hash"],
             "agent": "fix", "verdict": "obsolete", "at_pass": 1,
             "head_sha": "d" * 40, "reason": "gone", "verified_blob": BLOB,
             "head_blob": BLOB}
        r = self._pass2(_nv_cf(p1, None, None), [v])
        self.assertEqual(r["resolved"][0]["resolution"]["source"], "fix-obsolete")
        self.assertNotIn("commit_sha", r["resolved"][0]["resolution"])

    def test_routed_lane_resolves_and_binds_finding_and_snapshot(self):
        """A lane other than the fixer answers `resolved` on the routed token
        for the repaired snapshot: closes as confirmed-fix."""
        p1 = self._pass1()
        r = score.run(_nv_env([], carryforward=[_nv_cf(p1, None, None)],
                              pass_number=2, head_sha=HEAD2,
                              recheck_requests=[routed_request(p1, agents=("bugs",))],
                              verdicts=[confirmed_verdict(p1["stable_hash"]),
                                        reviewer_verdict()]))
        self.assertEqual(_nv_rows(r), [])
        self.assertEqual(_rejections(r), [])
        res = r["resolved"][0]
        self.assertEqual(res["stable_hash"], p1["stable_hash"])
        self.assertEqual(res["band"], score.NV_BAND)
        self.assertEqual(res["resolution"], {
            "source": "confirmed-fix", "agents": ["bugs"], "verdict": "resolved",
            "head_sha": HEAD2, "at_pass": 2,
            "reason": "parse_limit is range-checked before use",
            "verified_blob": BLOB, "commit_sha": SHA})
        self.assertEqual(state_shape.check_resolved_record(res, FUTURE), [])

    def test_stable_hash_and_golden_digest_unchanged(self):
        import test_score
        self.assertEqual(score.stable_hash("a.py", "  x=1", "title"),
                         test_score.GOLDEN_DIGEST)


# --------------------------------------------------------------------------- #
# Independent re-check (owner decision S9, fix-1 follow-ups)
# --------------------------------------------------------------------------- #
class TestIndependentRecheck(unittest.TestCase):
    def _pass1(self, agent="codex-adversarial"):
        rows = _nv_rows(score.run(_nv_env([_nv(agent=agent)])))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["agent"], agent)
        return rows[0]

    def _run(self, p1, requests, verdicts, cf=None, fix=True, **fix_over):
        vs = ([confirmed_verdict(p1["stable_hash"], **fix_over)] if fix else [])
        env = _nv_env([], carryforward=[cf or _nv_cf(p1, None, None)],
                      pass_number=2, head_sha=HEAD2,
                      recheck_requests=requests, verdicts=vs + verdicts)
        return score.run(json.loads(json.dumps(env)))

    def _open(self, r, reason):
        self.assertEqual(len(_nv_rows(r)), 1)
        self.assertNotIn("resolved", r)
        self.assertIn(reason, _rejections(r))

    def test_codex_origin_routed_and_resolved_closes(self):
        p1 = self._pass1("codex-adversarial")
        r = self._run(p1, [routed_request(p1, agents=("bugs",))],
                      [reviewer_verdict(agent="bugs")])
        self.assertEqual(_nv_rows(r), [])
        res = r["resolved"][0]
        self.assertEqual(res["agent"], "codex-adversarial")
        self.assertEqual(res["resolution"]["source"], "confirmed-fix")
        self.assertEqual(res["resolution"]["agents"], ["bugs"])
        self.assertEqual(res["resolution"]["commit_sha"], SHA)
        self.assertEqual(res["resolution"]["verified_blob"], BLOB)

    def test_gated_lane_origin_routed_to_another_lane_closes(self):
        p1 = self._pass1("architecture")
        r = self._run(p1, [routed_request(p1, agents=("bugs",))],
                      [reviewer_verdict(agent="bugs")])
        self.assertEqual(r["resolved"][0]["resolution"]["agents"], ["bugs"])

    def test_raising_lane_dispatched_is_the_reviewer(self):
        p1 = self._pass1("security")
        r = self._run(p1, [routed_request(p1, agents=("security",))],
                      [reviewer_verdict(agent="security")])
        self.assertEqual(r["resolved"][0]["resolution"]["agents"], ["security"])

    def test_persisted_snippet_still_closes_on_routed_resolved(self):
        """The fix may guard the failure elsewhere in the file; the routed
        reviewer judged the repaired file."""
        p1 = self._pass1()
        cf = _nv_cf(p1, p1["canonical_line_content"], p1["current_code"])
        r = self._run(p1, [routed_request(p1)], [reviewer_verdict()], cf=cf)
        self.assertEqual(_nv_rows(r), [])
        self.assertEqual(r["resolved"][0]["resolution"]["source"], "confirmed-fix")

    def test_routed_still_applies_keeps_open_with_reason(self):
        p1 = self._pass1()
        r = self._run(p1, [routed_request(p1)],
                      [reviewer_verdict(verdict="still-applies",
                                        reason="limit unchecked on reload path")])
        self._open(r, R_STILL)

    def test_no_eligible_reviewer_keeps_open_with_reason(self):
        p1 = self._pass1()
        self._open(self._run(p1, [], []), R_NO_REVIEWER)

    def test_routed_reviewer_silent_keeps_open_with_reason(self):
        p1 = self._pass1()
        self._open(self._run(p1, [routed_request(p1)], []), R_NO_ANSWER)

    def test_snapshot_changed_after_verdict_reopens(self):
        """HEAD's blob read at collect time (after the reviewer answered)
        differs from the repaired blob: the verdict judged code that is no
        longer there."""
        p1 = self._pass1()
        r = self._run(p1, [routed_request(p1)], [reviewer_verdict()],
                      head_blob="2" * 40)
        self._open(r, "verdict: evidence changed since verification")

    def test_reviewed_snapshot_not_the_repaired_code_stays_open(self):
        p1 = self._pass1()
        for snap in ("3" * 40, None):
            with self.subTest(snapshot=snap):
                r = self._run(p1, [routed_request(p1, snapshot=snap)],
                              [reviewer_verdict()])
                self._open(r, R_SNAPSHOT)

    def test_fixer_cannot_be_the_routed_reviewer(self):
        p1 = self._pass1()
        r = self._run(p1, [routed_request(p1, agents=("fix",))],
                      [reviewer_verdict(agent="fix")])
        self._open(r, "verdict: malformed")
        self.assertIn(R_NO_REVIEWER, _rejections(r))

    def test_routed_verdict_counts_only_on_the_routed_token(self):
        p1 = self._pass1()
        other = {"token": "R2", "agents": ["bugs"], "stable_hash": None,
                 "file": "src/other.py", "line": 3, "agent": "bugs",
                 "title": "other"}
        cases = {
            "wrong token": ([routed_request(p1), other],
                            [reviewer_verdict(token="R2")]),
            "agent not asked": ([routed_request(p1, agents=("bugs",))],
                                [reviewer_verdict(agent="security")]),
            "unissued token": ([routed_request(p1)],
                               [reviewer_verdict(token="R9")]),
        }
        for name, (reqs, vs) in cases.items():
            with self.subTest(name):
                r = self._run(p1, reqs, vs)
                self.assertEqual(len(_nv_rows(r)), 1)
                self.assertNotIn("resolved", r)

    def test_routed_resolved_without_confirmed_fix_closes_nothing(self):
        """A routed re-check is only the second half of the evidence."""
        p1 = self._pass1()
        r = self._run(p1, [routed_request(p1)], [reviewer_verdict()], fix=False)
        self._open(r, R_ORPHAN_ROUTED)

    def test_stale_or_changed_fix_verdict_with_routed_resolved_stays_open(self):
        """A routed `resolved` never revives a fix whose code changed since it
        was verified, whatever the verdict's age."""
        p1 = self._pass1()
        r = self._run(p1, [routed_request(p1)], [reviewer_verdict()], at_pass=0,
                      head_blob=HEAD2_BLOB)
        self.assertEqual(len(_nv_rows(r)), 1)
        self.assertNotIn("resolved", r)
        self.assertIn(R_EVIDENCE_CHANGED, _rejections(r))
        self.assertNotIn(R_STALE, _rejections(r))

    def test_malformed_routed_requests_rejected(self):
        p1 = self._pass1()
        good = routed_request(p1)
        bads = {
            "unknown route": dict(good, route="owner"),
            "no stable_hash": dict(good, stable_hash=None),
            "no snapshot key": {k: v for k, v in good.items()
                                if k != "snapshot_blob"},
            "empty snapshot": dict(good, snapshot_blob=""),
            "fixer asked": dict(good, agents=["bugs", "fix"]),
            "nobody asked": dict(good, agents=[]),
        }
        for name, bad in bads.items():
            with self.subTest(name):
                r = self._run(p1, [bad], [reviewer_verdict()])
                self.assertEqual(len(_nv_rows(r)), 1)
                self.assertNotIn("resolved", r)
                self.assertIn("verdict: malformed", _rejections(r))

    def test_plain_recheck_path_unchanged(self):
        """An ordinary hint (no route) on a needs-recheck NV item still closes
        through the raising lane's `resolved`, as before."""
        p1 = self._pass1("bugs")
        plain = {"token": "R1", "agents": ["bugs"],
                 "stable_hash": p1["stable_hash"], "file": p1["file"],
                 "line": p1["line"], "agent": "bugs", "title": p1["title"]}
        r = self._run(p1, [plain], [reviewer_verdict()], fix=False)
        self.assertEqual(r["resolved"][0]["resolution"]["source"], "recheck")

    def test_hash_and_golden_digest_unchanged(self):
        import test_score
        self.assertEqual(score.stable_hash("a.py", "  x=1", "title"),
                         test_score.GOLDEN_DIGEST)
        p1 = self._pass1()
        r = self._run(p1, [routed_request(p1)], [reviewer_verdict()])
        self.assertEqual(r["resolved"][0]["stable_hash"], p1["stable_hash"])


# --------------------------------------------------------------------------- #
# Retry after an inconclusive re-check: a fix that no independent reviewer
# could confirm on one rerun is re-checked on a later rerun, on the same
# evidence, with no new fix and no owner decision
# --------------------------------------------------------------------------- #
HEAD3 = "f" * 40


class TestRetryAfterInconclusive(unittest.TestCase):
    def _pass1(self, agent="codex-adversarial"):
        rows = _nv_rows(score.run(_nv_env([_nv(agent=agent)])))
        self.assertEqual(len(rows), 1)
        return rows[0]

    def _run(self, cf, requests, verdicts, pass_number, head_sha, **env_over):
        env = _nv_env([], carryforward=[cf], pass_number=pass_number,
                      head_sha=head_sha, recheck_requests=requests,
                      verdicts=verdicts, **env_over)
        self.last_env = env
        return score.run(json.loads(json.dumps(env)))

    def _carry(self, r):
        """The pass's surviving NV row, carried into the next pass (the fix
        changed the code, so the stored snippet is not located)."""
        rows = _nv_rows(r)
        self.assertEqual(len(rows), 1)
        return _nv_cf(rows[0], None, None)

    def _open(self, r, reason):
        self.assertEqual(len(_nv_rows(r)), 1)
        self.assertNotIn("resolved", r)
        self.assertIn(reason, _rejections(r))

    def test_inconclusive_then_retry_closes_on_unchanged_code(self):
        p1 = self._pass1()
        fix = confirmed_verdict(p1["stable_hash"], blob=BLOB, head_blob=BLOB,
                                at_pass=1)
        # Pass 2: no eligible reviewer ran, so the fix is not yet confirmed.
        r2 = self._run(_nv_cf(p1, None, None), [], [fix], 2, HEAD2)
        self._open(r2, R_NO_REVIEWER)
        # Pass 3: a later run dispatched a reviewer; the SAME applied verdict
        # (still at_pass 1) and the unchanged blob close the item.
        env_verdicts = [json.loads(json.dumps(fix)), reviewer_verdict()]
        r3 = self._run(self._carry(r2), [routed_request(p1)], env_verdicts, 3, HEAD3)
        self.assertEqual(_rejections(r3), [])
        self.assertEqual(_nv_rows(r3), [])
        res = r3["resolved"][0]["resolution"]
        self.assertEqual(res["source"], "confirmed-fix")
        self.assertEqual(res["commit_sha"], SHA)
        self.assertEqual(res["verified_blob"], BLOB)
        self.assertEqual(res["at_pass"], 3)
        # No new fix pass and no owner decision: the pass-3 envelope holds
        # exactly the one pass-1 fix verdict and no decisions.
        fix_vs = [v for v in self.last_env["verdicts"]
                  if v["source"] in ("confirmed-fix", "fix-obsolete")]
        self.assertEqual(fix_vs, [fix])
        self.assertNotIn("decisions", self.last_env)

    def test_retry_rejects_changed_code_at_any_age(self):
        p1 = self._pass1()
        fix = confirmed_verdict(p1["stable_hash"], blob=BLOB, head_blob=HEAD2_BLOB,
                                at_pass=1)
        r = self._run(_nv_cf(p1, None, None), [routed_request(p1)],
                      [fix, reviewer_verdict()], 3, HEAD3)
        self.assertEqual(len(_nv_rows(r)), 1)
        self.assertNotIn("resolved", r)
        self.assertIn(R_EVIDENCE_CHANGED, _rejections(r))
        self.assertNotIn(R_STALE, _rejections(r))

    def test_retry_after_still_applies_waits_for_code_change(self):
        p1 = self._pass1()
        fix = confirmed_verdict(p1["stable_hash"], at_pass=1)
        # Pass 2: the routed reviewer says it still applies.
        r2 = self._run(_nv_cf(p1, None, None), [routed_request(p1)],
                       [fix, reviewer_verdict(verdict="still-applies",
                                              reason="limit unchecked on reload")],
                       2, HEAD2, head_blobs={F: BLOB}, touched_paths={})
        self._open(r2, R_STILL)
        settled = _nv_rows(r2)[0].get("recheck_settled")
        self.assertIsInstance(settled, dict, "no recheck_settled on the row")
        self.assertEqual(settled.get("fingerprint"), {F: BLOB})
        carried = _nv_cf(settled_row(_nv_rows(r2)[0], {F: BLOB},
                                     head_sha=HEAD2), None, None)
        # Pass 3, code unchanged: a routed `resolved` cannot close it.
        r3 = self._run(carried, [routed_request(p1)], [fix, reviewer_verdict()],
                       3, HEAD3, head_blobs={F: BLOB}, touched_paths={})
        self._open(r3, R_CF_SETTLED)
        # Pass 3, the code changed (a new fix verified on BLOB2): a fresh start.
        fix2 = confirmed_verdict(p1["stable_hash"], blob=BLOB2, head_blob=BLOB2,
                                 at_pass=2)
        r3 = self._run(carried, [routed_request(p1, snapshot=BLOB2)],
                       [fix2, reviewer_verdict()], 3, HEAD3,
                       head_blobs={F: BLOB2}, touched_paths={})
        self.assertEqual(_rejections(r3), [])
        self.assertEqual(_nv_rows(r3), [])
        self.assertEqual(r3["resolved"][0]["resolution"]["source"], "confirmed-fix")
        self.assertEqual(r3["resolved"][0]["resolution"]["verified_blob"], BLOB2)

    def test_obsolete_age_rule_unchanged(self):
        p1 = self._pass1()
        v = {"source": "fix-obsolete", "stable_hash": p1["stable_hash"],
             "agent": "fix", "verdict": "obsolete", "at_pass": 1,
             "head_sha": "d" * 40, "reason": "gone", "verified_blob": BLOB,
             "head_blob": BLOB}
        r = self._run(_nv_cf(p1, None, None), [], [v], 3, HEAD3)
        self._open(r, R_STALE)


# --------------------------------------------------------------------------- #
# Mutation checks: each new guard trips when removed
# --------------------------------------------------------------------------- #
def _mutant(path, name, old, new):
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    mutated = src.replace(old, new)
    if mutated == src:
        raise AssertionError("mutation target not found: %r" % old)
    mod = types.ModuleType(name)
    mod.__file__ = path
    exec(compile(mutated, path, "exec"), mod.__dict__)
    return mod


class TestMutants(unittest.TestCase):
    def _recorded(self, mod, p, row=None):
        out = mod.record_fix_verdicts(state_with(row or nv_row()), p, [])
        return NVH in (out or {}).get("fix_verdicts", {})

    def test_mutant_commit_file_check_removed(self):
        p = payload(commits={SHA: {"files": ["src/other.py"], "blobs": {F: BLOB}}})
        self.assertFalse(self._recorded(carry_state, p))
        mod = _mutant(CARRY_STATE_PY, "cs_m1",
                      "file not in commit.get(\"files\")", "False")
        self.assertTrue(self._recorded(mod, p))

    def test_mutant_head_blob_binding_removed(self):
        p = payload(clean={F: "2" * 40})
        self.assertFalse(self._recorded(carry_state, p))
        mod = _mutant(CARRY_STATE_PY, "cs_m2",
                      "clean.get(file) != blob", "False")
        self.assertTrue(self._recorded(mod, p))

    def test_mutant_check_outcome_removed(self):
        p = payload(results=[applied_result(check=dict(CHECK_PASSED,
                                                       outcome="failed"))])
        self.assertFalse(self._recorded(carry_state, p))
        mod = _mutant(CARRY_STATE_PY, "cs_m3",
                      "check.get(\"outcome\") not in _CONFIRMED_CHECK_OUTCOMES",
                      "False")
        self.assertTrue(self._recorded(mod, p))

    def test_mutant_nv_band_check_removed(self):
        self.assertFalse(self._recorded(carry_state, payload(),
                                        row=warning_row(h=NVH)))
        mod = _mutant(CARRY_STATE_PY, "cs_m4",
                      "by_hash[h].get(\"band\") == NV_BAND",
                      "True")
        self.assertTrue(self._recorded(mod, payload(), row=warning_row(h=NVH)))

    def test_mutant_awaiting_band_check_removed(self):
        s = state_with(warning_row(), fix_verdicts={WH: applied_verdict()})
        self.assertEqual(carry_state.finalize_counts(
            s, {F: BLOB})["confirmed_fix_awaiting_recheck_hashes"], [])
        mod = _mutant(CARRY_STATE_PY, "cs_m5",
                      "record.get(\"band\") == NV_BAND and _sha40(",
                      "_sha40(")
        self.assertEqual(mod.finalize_counts(
            s, {F: BLOB})["confirmed_fix_awaiting_recheck_hashes"], [WH])

    def test_mutant_fixer_only_closes_at_finalize(self):
        """Restoring the old rule (an `applied` verdict closes like obsolete)
        trips: the fixer's own check would close the item with no re-check."""
        s = state_with(nv_row(), fix_verdicts={NVH: applied_verdict()})
        self.assertEqual(carry_state.finalize_counts(s, {F: BLOB})["undecided_nv"], 1)
        mod = _mutant(CARRY_STATE_PY, "cs_m6",
                      'return kind == "obsolete"',
                      'return kind in ("obsolete", "applied")')
        self.assertEqual(mod.finalize_counts(s, {F: BLOB})["undecided_nv"], 0)

    def test_mutant_score_band_check_removed(self):
        f = _nv()
        del f["needs_verification"]
        f["agent_confidence"] = 95
        p1 = score.run(_nv_env([f]))["findings"][0]
        cf = json.loads(json.dumps(p1))
        cf["canonical_line_content"] = "something else entirely"
        cf["canonical_window"] = "something else entirely"
        env = _nv_env([], carryforward=[cf], pass_number=2, head_sha="e" * 40,
                      recheck_requests=[routed_request(p1)],
                      verdicts=[confirmed_verdict(p1["stable_hash"]),
                                reviewer_verdict()])
        self.assertNotIn("resolved", score.run(json.loads(json.dumps(env))))
        mod = _mutant(SCORE_PY, "score_m1",
                      "record.get(\"band\") != NV_BAND", "False")
        self.assertIn("resolved", mod.run(json.loads(json.dumps(env))))


class TestIndependentRecheckMutants(unittest.TestCase):
    def _env(self, p1, requests, verdicts, fix=True, **fix_over):
        vs = ([confirmed_verdict(p1["stable_hash"], **fix_over)] if fix else [])
        return _nv_env([], carryforward=[_nv_cf(p1, None, None)],
                       pass_number=2, head_sha=HEAD2,
                       recheck_requests=requests, verdicts=vs + verdicts)

    def _p1(self):
        return _nv_rows(score.run(_nv_env([_nv(agent="codex-adversarial")])))[0]

    def _trips(self, name, old, new, env):
        self.assertNotIn("resolved", score.run(json.loads(json.dumps(env))))
        mod = _mutant(SCORE_PY, name, old, new)
        self.assertIn("resolved", mod.run(json.loads(json.dumps(env))))

    def test_mutant_routed_requirement_removed(self):
        p1 = self._p1()
        self._trips("score_m2", "reviewers, why = _confirmed_fix_recheck(",
                    "reviewers, why = [{'agent': 'fix', 'reason': ''}], None; _x = (",
                    self._env(p1, [], []))

    def test_mutant_still_applies_check_removed(self):
        p1 = self._p1()
        env = self._env(p1, [routed_request(p1, agents=("bugs", "security"))],
                        [reviewer_verdict(agent="bugs"),
                         reviewer_verdict(agent="security", verdict="still-applies")])
        self._trips("score_m3",
                    'if any(v["verdict"] == "still-applies" for v in routed):',
                    "if False:", env)

    def test_mutant_snapshot_binding_removed(self):
        p1 = self._p1()
        env = self._env(p1, [routed_request(p1, snapshot="3" * 40)],
                        [reviewer_verdict()])
        self._trips("score_m4",
                    'requests_by_token[v["token"]]["snapshot_blob"] != verified',
                    "False", env)

    def test_mutant_fixer_exclusion_removed(self):
        p1 = self._p1()
        env = self._env(p1, [routed_request(p1, agents=("fix",))],
                        [reviewer_verdict(agent="fix")])
        self._trips("score_m5",
                    'not any(a in _FIXER_AGENTS for a in req["agents"])',
                    "True", env)

    def test_mutant_applied_blob_gate_removed(self):
        """With the age gate relaxed for confirmed fixes, the blob compare is
        the only thing stopping an old verdict on changed code."""
        p1 = self._p1()
        env = self._env(p1, [routed_request(p1)], [reviewer_verdict()],
                        at_pass=0, head_blob=HEAD2_BLOB)
        self._trips("score_m19",
                    'verified == v.get("head_blob")',
                    "True", env)

    def test_mutant_cf_settled_check_removed(self):
        p1 = self._p1()
        cf = _nv_cf(settled_row(p1, {F: BLOB}, head_sha=HEAD2), None, None)
        env = _nv_env([], carryforward=[cf], pass_number=3, head_sha=HEAD3,
                      recheck_requests=[routed_request(p1)],
                      verdicts=[confirmed_verdict(p1["stable_hash"], at_pass=1),
                                reviewer_verdict()],
                      head_blobs={F: BLOB}, touched_paths={})
        self._trips("score_m20",
                    'if isinstance(record.get("recheck_settled"), dict):\n'
                    '                rejected.append((v, _R_CF_SETTLED))',
                    'if False:\n'
                    '                rejected.append((v, _R_CF_SETTLED))',
                    env)

    def test_mutant_routed_counted_as_plain_recheck(self):
        p1 = self._p1()
        env = self._env(p1, [routed_request(p1)], [reviewer_verdict()], fix=False)
        self._trips("score_m6",
                    'if requests_by_token[v["token"]].get("route") is None]',
                    "]", env)


# --------------------------------------------------------------------------- #
# Prose: the orchestrator collects the evidence and renders the closure
# --------------------------------------------------------------------------- #
SHA_RE_LITERAL = "^[0-9a-f]{40}$"


def fix_loop_collects_evidence_holds(text):
    i = text.find("**Record fix verdicts")
    j = text.find("What the helper writes:", i)
    if i < 0 or j < 0:
        return False
    block = text[i:j]
    return all(needle in block for needle in (
        '"commits"', '"clean_head_blobs"', SHA_RE_LITERAL,
        "git cat-file -e", "git merge-base --is-ancestor",
        "git diff-tree --no-commit-id --name-only -r",
    )) and block.index(SHA_RE_LITERAL) < block.index("git cat-file -e")


def finalize_renders_confirmed_fix_holds(text):
    return ("`confirmed_fix_awaiting_recheck_hashes`" in text
            and "source `confirmed-fix`" in text
            and '"confirmed_fix_awaiting_recheck_hashes"' in text
            and "verified_confirmed_fix_hashes" not in text
            and "awaiting an independent re-check" in text
            and "never closes here" in text)


BIND_STEP = "Bind `$RECHECK_REQUESTS`"


def _next_top_level_step(text, i, first=4, last=9):
    """Index of the first top-level numbered step (`\nN. `, N in first..last)
    after `i`, or -1."""
    found = [k for k in (text.find("\n%d. " % n, i) for n in range(first, last + 1))
             if k > i]
    return min(found) if found else -1


def _dispatch_step3(text):
    i = text.find("3. **Confirmed-fix re-check")
    if i < 0:
        return None
    j = _next_top_level_step(text, i)
    return text[i:j] if j > i else None


def _dispatch_bind_step(text):
    i = text.find(BIND_STEP)
    if i < 0:
        return None
    j = text.find("\n\n", i + 1)
    return text[i:j] if j > i else text[i:]


def dispatch_routes_confirmed_fix_holds(text):
    step = _dispatch_step3(text)
    step4 = _dispatch_bind_step(text)
    if step is None or step4 is None:
        return False
    return (all(n in step for n in (
        "`$FIX_VERDICTS_PREV`", "`applied`",
        "the record's own `agent` when it is dispatched",
        "otherwise `bugs` when dispatched",
        "`codex-adversarial` and `fix` are never the reviewer",
        "no eligible reviewer this pass",
        "`snapshot_blob`", "You are the independent re-check",
        "No owner card is added"))
        and '"route": "confirmed-fix"' in step4 and '"snapshot_blob"' in step4)


def collect_rereads_head_blob_holds(text):
    return ("re-read NOW, after the agents returned and the gitsnap compare passed"
            in text and "verdict: confirmed fix not verified: the reviewed code is "
            "not the repaired code" in text)


def render_shows_open_reason_holds(text):
    return ("`verdict: confirmed fix`" in text and "Fix not yet verified:" in text
            and "re-checked independently by the {{agents}} lane" in text)


def collect_forwards_confirmed_fix_holds(text):
    return ('"source": "confirmed-fix"' in text and '"commit_sha"' in text
            and '"verdict": "applied"' in text)


class TestProse(unittest.TestCase):
    def test_fix_loop_collects_evidence(self):
        text = _read("phases/review/50-fix-loop.md")
        self.assertTrue(fix_loop_collects_evidence_holds(text))
        for needle in (SHA_RE_LITERAL, '"clean_head_blobs"', "git cat-file -e"):
            with self.subTest(mutant=needle):
                self.assertFalse(fix_loop_collects_evidence_holds(
                    text.replace(needle, "")))

    def test_finalize_renders_confirmed_fix(self):
        text = _read("phases/shared/90-finalize.md")
        self.assertTrue(finalize_renders_confirmed_fix_holds(text))
        for needle in ("source `confirmed-fix`", "awaiting an independent re-check",
                       "never closes here"):
            with self.subTest(mutant=needle):
                self.assertFalse(finalize_renders_confirmed_fix_holds(
                    text.replace(needle, "")))
        self.assertFalse(finalize_renders_confirmed_fix_holds(
            text + "\nverified_confirmed_fix_hashes"))

    def test_dispatch_routes_confirmed_fix(self):
        text = _read("phases/review/20-dispatch.md")
        self.assertTrue(dispatch_routes_confirmed_fix_holds(text))
        for needle in ("`codex-adversarial` and `fix` are never the reviewer",
                       "otherwise `bugs` when dispatched", "`snapshot_blob`",
                       '"route": "confirmed-fix"', "You are the independent re-check"):
            with self.subTest(mutant=needle):
                self.assertFalse(dispatch_routes_confirmed_fix_holds(
                    text.replace(needle, "")))
        self.assertNotIn("closes by an owner decision or, after an owner-named fix, "
                         "by a confirmed-fix verdict", text)

    def test_dispatch_slicers_survive_renumbering(self):
        """A new step between the confirmed-fix step and the Bind step (Bind
        renumbered) keeps the confirmed-fix lock reading the right slices."""
        text = _read("phases/review/20-dispatch.md")
        old_bind = "\n4. " + BIND_STEP
        self.assertIn(old_bind, text)
        renumbered = text.replace(old_bind, "\n4. **Independent re-check (ordinary "
                                  "carried records)** body.\n5. " + BIND_STEP)
        self.assertTrue(dispatch_routes_confirmed_fix_holds(renumbered))
        self.assertNotIn("Independent re-check", _dispatch_step3(renumbered))
        self.assertTrue(_dispatch_bind_step(renumbered).startswith(BIND_STEP))

    def test_collect_rereads_head_blob(self):
        text = _read("phases/review/30-collect-score.md")
        self.assertTrue(collect_rereads_head_blob_holds(text))
        self.assertFalse(collect_rereads_head_blob_holds(text.replace(
            "re-read NOW, after the agents returned and the gitsnap compare passed",
            "the same HEAD read")))

    def test_render_shows_open_reason(self):
        text = _read("phases/review/40-render.md")
        self.assertTrue(render_shows_open_reason_holds(text))
        self.assertFalse(render_shows_open_reason_holds(
            text.replace("Fix not yet verified:", "")))
        self.assertNotIn("verified by the fix agent against the repaired file, "
                         "which HEAD still holds", text)

    def test_fix_loop_says_applied_never_closes_alone(self):
        text = _read("phases/review/50-fix-loop.md")
        self.assertIn("NEVER closes alone", text)
        self.assertIn("`confirmed_fix_awaiting_recheck_hashes`", text)

    def test_collect_forwards_confirmed_fix(self):
        text = _read("phases/review/30-collect-score.md")
        self.assertTrue(collect_forwards_confirmed_fix_holds(text))
        self.assertFalse(collect_forwards_confirmed_fix_holds(
            text.replace('"source": "confirmed-fix"', "")))

    def test_phase05_forwards_verdict_kind(self):
        text = _read("phases/review/05-state.md")
        self.assertTrue("verdict, commit_sha" in text)

    def test_render_names_confirmed_fix(self):
        text = _read("phases/review/40-render.md")
        self.assertTrue("confirmed-fix" in text)

    def test_schema_enum(self):
        self.assertIn("confirmed-fix", FUTURE["resolution_source_enum"])
        self.assertIn("commit_sha", FUTURE["resolution_optional"])


# --------------------------------------------------------------------------- #
# Prose contract for the independent re-check of ordinary carried records,
# the retry of an unconfirmed fix and the bounded "not yet confirmed" reason
# --------------------------------------------------------------------------- #
INDEPENDENT_STEP = "**Independent re-check (ordinary carried records)**"
STEP2_HEAD = "2. For each record whose `agent` is in THIS pass's dispatched set"
STEP3_HEAD = "3. **Confirmed-fix"
INDEPENDENT_NEEDLES = (
    '"route": "independent"',
    "the record's own `agent` when it is dispatched",
    "otherwise `bugs` when dispatched",
    "`codex-adversarial` and `fix` are never the reviewer",
    "`snapshot_blob`",
    "`test_paths`",
    "`recheck_settled`",
    "no eligible reviewer ran this pass",
    "you are the independent re-check",
    "new tests alone do not resolve",
    "not an instruction to change your review scope",
)
BIND_INDEPENDENT_NEEDLES = ('"route": "independent"', '"test_paths"', '"fix_commit"')
NEVER_REROUTED = "is never rerouted to another agent"
TOUCHED_PATHS_BULLET = "- `$TOUCHED_PATHS`"
TOUCHED_PATHS_NEEDLES = ("`$TOUCHED_PATHS`", "git diff --name-only",
                         "earliest pass whose `findings`", "`recheck_settled`",
                         "`^[A-Za-z0-9._/-]+$`")
FORWARDED_ANY_AGE = "forwarded whatever its `at_pass`"
OLD_IGNORED_SENTENCE = ("Older `fix_verdicts` entries (`at_pass` below the last "
                        "pass) are ignored — never resurrected.")
CONTRACT_REASONS = (
    "verdict: fix not yet confirmed: no eligible reviewer ran this pass",
    "verdict: fix not yet confirmed: the routed reviewer gave no verdict",
    "verdict: fix not confirmed: the routed reviewer says it still applies",
    "verdict: fix not confirmed: the reviewed code is not the code at HEAD",
    "verdict: fix not confirmed: no change near the finding or in its file "
    "since it was raised",
    "verdict: fix not confirmed: a reviewer said it still applies and the code "
    "is unchanged since",
    R_CF_SETTLED,
)
COLLECT_NEEDLES = ("`head_blobs`", "`touched_paths`",
                   "re-read NOW, after the agents returned and the gitsnap "
                   "compare passed") + CONTRACT_REASONS
RENDER_NEEDLES = ("Fix not yet confirmed:",
                  "retried on the next run that reviews changes",
                  "run /deep-review", "dismiss",
                  "Closed — fix confirmed by the {{agents}} lane")
OLD_RENDER_SENTENCE = "The independent re-check runs only on the first rerun after the fix"
OLD_OUTPUT_SUFFIX = "code changed since last pass; awaiting your decision"


def _dispatch_independent_step(text):
    i = text.find(INDEPENDENT_STEP)
    if i < 0:
        return None
    j = text.find(BIND_STEP, i)
    return text[i:j] if j > i else None


def _dispatch_step2(text):
    i = text.find(STEP2_HEAD)
    if i < 0:
        return None
    j = text.find(STEP3_HEAD, i)
    return text[i:j] if j > i else None


def dispatch_routes_independent_holds(text):
    step = _dispatch_independent_step(text)
    bind = _dispatch_bind_step(text)
    step2 = _dispatch_step2(text)
    if step is None or bind is None or step2 is None:
        return False
    return (all(n in step for n in INDEPENDENT_NEEDLES)
            and all(n in bind for n in BIND_INDEPENDENT_NEEDLES)
            and "`snapshot_blob`" in step2
            and NEVER_REROUTED not in text)


def _touched_paths_bullet(text):
    i = text.find(TOUCHED_PATHS_BULLET)
    if i < 0:
        return None
    ends = [k for k in (text.find("\n   - ", i + 1), text.find("\n3. ", i + 1))
            if k > i]
    return text[i:min(ends)] if ends else text[i:]


def state_collects_touched_paths_holds(text):
    bullet = _touched_paths_bullet(text)
    return bullet is not None and all(n in bullet for n in TOUCHED_PATHS_NEEDLES)


def state_forwards_applied_any_age_holds(text):
    return FORWARDED_ANY_AGE in text and OLD_IGNORED_SENTENCE not in text


def collect_forwards_independent_holds(text):
    return all(n in text for n in COLLECT_NEEDLES)


def render_shows_not_yet_confirmed_holds(text):
    return (all(n in text for n in RENDER_NEEDLES)
            and OLD_RENDER_SENTENCE not in text)


def output_format_not_yet_confirmed_holds(text):
    return "Fix not yet confirmed" in text and OLD_OUTPUT_SUFFIX not in text


# A minimal document each predicate accepts, so every needle is proven
# load-bearing today, before the prose exists.
SYNTH_DISPATCH = (
    "On pass >= 2:\n"
    "1. Number every carried RECORD.\n"
    + STEP2_HEAD + " — plain hint, with `snapshot_blob` for every plain entry.\n"
    + STEP3_HEAD + " re-check (independent, batched into this pass).** body\n"
    "4. " + INDEPENDENT_STEP + " " + " ".join(INDEPENDENT_NEEDLES) + "\n"
    "5. " + BIND_STEP + " = [" + ", ".join(BIND_INDEPENDENT_NEEDLES) + "]\n\n"
    "trailing paragraph\n")
SYNTH_STATE = (
    "2. If present: parse it.\n"
    "   " + TOUCHED_PATHS_BULLET + " " + " ".join(TOUCHED_PATHS_NEEDLES) + "\n"
    "   - `$FIX_VERDICTS_PREV` = every applied entry, " + FORWARDED_ANY_AGE
    + " `^[A-Za-z0-9._/-]+$`.\n\n"
    "3. Narrow diff to incremental.\n")
SYNTH_COLLECT = " ".join(COLLECT_NEEDLES)
SYNTH_RENDER = " ".join(RENDER_NEEDLES)
SYNTH_OUTPUT = "| row | — Fix not yet confirmed: ... |"


class TestProse56Predicates(unittest.TestCase):
    """Each Phase 56 prose predicate can go true, and each of its needles is
    load-bearing (the removal mutant goes false)."""

    def _load_bearing(self, holds, text, needles):
        self.assertTrue(holds(text))
        for needle in needles:
            with self.subTest(mutant=needle):
                self.assertIn(needle, text)
                self.assertFalse(holds(text.replace(needle, "")))

    def test_dispatch_independent(self):
        self._load_bearing(dispatch_routes_independent_holds, SYNTH_DISPATCH,
                           INDEPENDENT_NEEDLES + BIND_INDEPENDENT_NEEDLES
                           + (INDEPENDENT_STEP, BIND_STEP))
        # Each bind needle counts inside the Bind step, not only in the step.
        bind = _dispatch_bind_step(SYNTH_DISPATCH)
        self.assertFalse(dispatch_routes_independent_holds(
            SYNTH_DISPATCH.replace(bind, BIND_STEP + " = []")))
        # The plain hint must carry `snapshot_blob`.
        step2 = _dispatch_step2(SYNTH_DISPATCH)
        self.assertFalse(dispatch_routes_independent_holds(SYNTH_DISPATCH.replace(
            step2, step2.replace("`snapshot_blob`", "the blob"))))
        self.assertFalse(dispatch_routes_independent_holds(
            SYNTH_DISPATCH + "\nA record " + NEVER_REROUTED + ".\n"))

    def test_state_touched_paths(self):
        self._load_bearing(state_collects_touched_paths_holds, SYNTH_STATE,
                           TOUCHED_PATHS_NEEDLES)
        # The path-validation literal elsewhere in the file does not count.
        bullet = _touched_paths_bullet(SYNTH_STATE)
        self.assertNotIn("FIX_VERDICTS_PREV", bullet)
        self.assertFalse(state_collects_touched_paths_holds(SYNTH_STATE.replace(
            bullet, bullet.replace("`^[A-Za-z0-9._/-]+$`", ""))))

    def test_state_forwards_applied_any_age(self):
        self._load_bearing(state_forwards_applied_any_age_holds, SYNTH_STATE,
                           (FORWARDED_ANY_AGE,))
        self.assertFalse(state_forwards_applied_any_age_holds(
            SYNTH_STATE + OLD_IGNORED_SENTENCE))

    def test_collect_forwards_independent(self):
        self._load_bearing(collect_forwards_independent_holds, SYNTH_COLLECT,
                           COLLECT_NEEDLES)

    def test_render_not_yet_confirmed(self):
        self._load_bearing(render_shows_not_yet_confirmed_holds, SYNTH_RENDER,
                           RENDER_NEEDLES)
        self.assertFalse(render_shows_not_yet_confirmed_holds(
            SYNTH_RENDER + " " + OLD_RENDER_SENTENCE))

    def test_output_format_bounded_reason(self):
        self._load_bearing(output_format_not_yet_confirmed_holds, SYNTH_OUTPUT,
                           ("Fix not yet confirmed",))
        self.assertFalse(output_format_not_yet_confirmed_holds(
            SYNTH_OUTPUT + OLD_OUTPUT_SUFFIX))

    def test_contract_reasons_match_the_shared_contract(self):
        import test_verified_fixes as tvf
        self.assertEqual(CONTRACT_REASONS, (
            tvf.R_IR_NO_REVIEWER, tvf.R_IR_NO_ANSWER, tvf.R_IR_STILL,
            tvf.R_IR_SNAPSHOT, tvf.R_IR_NO_TRIGGER, tvf.R_IR_SETTLED,
            tvf.R_CF_SETTLED))


class TestProse56(unittest.TestCase):
    """The shipped prose satisfies each Phase 56 contract."""

    def test_dispatch_routes_independent(self):
        text = _read("phases/review/20-dispatch.md")
        self.assertTrue(dispatch_routes_independent_holds(text))
        for needle in INDEPENDENT_NEEDLES + BIND_INDEPENDENT_NEEDLES:
            with self.subTest(mutant=needle):
                self.assertFalse(dispatch_routes_independent_holds(
                    text.replace(needle, "")))

    def test_dispatch_never_rerouted_sentence_gone(self):
        text = _read("phases/review/20-dispatch.md")
        self.assertFalse(NEVER_REROUTED in text,
                         "20-dispatch.md still says: " + NEVER_REROUTED)

    def test_phase05_touched_paths(self):
        text = _read("phases/review/05-state.md")
        self.assertTrue(state_collects_touched_paths_holds(text))
        for needle in TOUCHED_PATHS_NEEDLES:
            with self.subTest(mutant=needle):
                bullet = _touched_paths_bullet(text)
                self.assertFalse(state_collects_touched_paths_holds(
                    text.replace(bullet, bullet.replace(needle, ""))))

    def test_phase05_forwards_applied_any_age(self):
        text = _read("phases/review/05-state.md")
        self.assertTrue(state_forwards_applied_any_age_holds(text))
        self.assertFalse(state_forwards_applied_any_age_holds(
            text.replace(FORWARDED_ANY_AGE, "")))

    def test_collect_forwards_independent(self):
        text = _read("phases/review/30-collect-score.md")
        self.assertTrue(collect_forwards_independent_holds(text))
        for needle in CONTRACT_REASONS:
            with self.subTest(mutant=needle):
                self.assertFalse(collect_forwards_independent_holds(
                    text.replace(needle, "")))

    def test_render_not_yet_confirmed(self):
        text = _read("phases/review/40-render.md")
        self.assertTrue(render_shows_not_yet_confirmed_holds(text))
        for needle in RENDER_NEEDLES:
            with self.subTest(mutant=needle):
                self.assertFalse(render_shows_not_yet_confirmed_holds(
                    text.replace(needle, "")))

    def test_output_format_bounded_reason(self):
        text = _read("templates/output-format.md")
        self.assertTrue(output_format_not_yet_confirmed_holds(text))

    def test_carry_state_docstring_says_any_age(self):
        self.assertTrue("whatever its `at_pass`" in carry_state.__doc__,
                        "carry_state docstring does not say an applied verdict "
                        "awaits whatever its `at_pass`")


# --------------------------------------------------------------------------- #
# S10: one-row "Apply selected…" sends the picked row, end to end
# --------------------------------------------------------------------------- #
ONE_ROW_BULLET = "  - `none` (one row) →"


def _one_row_bullet(text):
    i = text.find(ONE_ROW_BULLET)
    j = text.find("\n  - `multiselect`", i)
    return text[i:j] if i >= 0 and j > i else None


def one_row_sends_pick_holds(text):
    bullet = _one_row_bullet(text)
    return (bullet is not None and "`answer`" in bullet
            and '{"all": true}' not in bullet)


class TestOneRowApplySelected(unittest.TestCase):
    """card → select → fix payload → recorded verdict → verified close."""

    def _nv_state(self):
        row = _nv_rows(score.run(_nv_env([_nv()])))[0]
        return {"medium_acknowledgments": {}, "passes": [{
            "pass_number": 1, "head_sha": "h1", "diff_range": "a..b",
            "findings": [row]}]}, row

    def test_select_questions_emits_the_pick(self):
        rows = batch_card.build_rows(self._nv_state()[0], "fix-loop")[0]["rows"]
        out = batch_card.select_questions(rows)
        self.assertEqual(out["mode"], "none")
        self.assertEqual(out["answer"], {"labels": ["#1 src/nv.py:12"]})
        self.assertEqual(batch_card.select_questions([])["answer"],
                         {"none": True})

    def test_bulk_all_still_skips_nv(self):
        state, _ = self._nv_state()
        rows_doc = batch_card.build_rows(state, "fix-loop")[0]
        payload_, reason = batch_card.build_payload(state, rows_doc,
                                                    {"all": True})
        self.assertIsNone(reason)
        self.assertEqual(payload_["sent"], [])

    def test_non_nv_one_row_unchanged(self):
        state = state_with(warning_row())
        rows_doc = batch_card.build_rows(state, "fix-loop")[0]
        answer = batch_card.select_questions(rows_doc["rows"])["answer"]
        via_pick, _ = batch_card.build_payload(state, rows_doc, answer)
        via_all, _ = batch_card.build_payload(state, rows_doc, {"all": True})
        self.assertEqual(via_pick["sent"], [WH])
        self.assertEqual(via_pick, via_all)

    def _close_through_the_pipeline(self, select_questions):
        state, row = self._nv_state()
        h = row["stable_hash"]
        rows_doc = batch_card.build_rows(state, "fix-loop")[0]
        answer = select_questions(rows_doc["rows"]).get("answer", {"all": True})
        sent, reason = batch_card.build_payload(state, rows_doc, answer)
        self.assertIsNone(reason)
        if h not in sent["sent"]:
            return False
        self.assertEqual(sent["findings"][0]["id"], h)
        # The fix agent applied and committed it; the orchestrator collected
        # the commit and the clean HEAD blob (50-fix-loop.md step 2b).
        new_state, skipped = record(state, payload(
            results=[applied_result(h=h)], sent=sent["sent"]))
        self.assertEqual(skipped, [])
        self.assertEqual(new_state["fix_verdicts"][h]["verdict"], "applied")
        # Finalize without a rerun: the fixer's evidence alone keeps it open.
        counts = carry_state.finalize_counts(new_state, {F: BLOB})
        self.assertEqual(counts["undecided_nv"], 1)
        self.assertEqual(counts["confirmed_fix_awaiting_recheck_hashes"], [h])
        # Rerun: Phase 0.5 forwards the verdict, Phase 2 routes the re-check
        # to the raising lane (bugs, dispatched), score.py closes the row.
        v = new_state["fix_verdicts"][h]
        forwarded = {"source": "confirmed-fix", "stable_hash": h, "agent": "fix",
                     "verdict": "applied", "commit_sha": v["commit_sha"],
                     "at_pass": v["at_pass"], "head_sha": v["head_sha"],
                     "reason": v["reason"], "verified_blob": v["verified_blob"],
                     "head_blob": BLOB}
        r = score.run(_nv_env([], carryforward=[_nv_cf(row, None, None)],
                              pass_number=2, head_sha="e" * 40,
                              recheck_requests=[routed_request(row)],
                              verdicts=[forwarded, reviewer_verdict()]))
        self.assertEqual(_nv_rows(r), [])
        return r["resolved"][0]["resolution"]["source"] == "confirmed-fix"

    def test_selected_nv_row_closes_end_to_end(self):
        self.assertTrue(self._close_through_the_pipeline(
            batch_card.select_questions))

    def test_mutant_one_row_sends_all(self):
        def old_select_questions(rows):
            out = dict(batch_card.select_questions(rows))
            out.pop("answer", None)  # the caller wrote {"all": true}
            return out
        self.assertFalse(self._close_through_the_pipeline(old_select_questions))

    def test_prose_writes_the_emitted_answer(self):
        text = _read("phases/review/50-fix-loop.md")
        self.assertTrue(one_row_sends_pick_holds(text))
        bullet = _one_row_bullet(text)
        mutant = text.replace(bullet, ONE_ROW_BULLET + ' write `{"all": true}` '
                              "to `$ANSWERFILE` and go to Step B.")
        self.assertFalse(one_row_sends_pick_holds(mutant))


if __name__ == "__main__":
    unittest.main()
