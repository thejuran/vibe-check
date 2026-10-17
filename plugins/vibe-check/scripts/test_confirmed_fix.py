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
commit and that blob. It closes the item only while HEAD's blob for the file
still equals the recorded blob (the fix-obsolete rule), and REVIEW.md lists it
under "Resolved by verification" with source `confirmed-fix`.

Confirmation alone (`fix N` with no applied result), an applied patch without
that evidence, or the lane's absence never closes the item.
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


class TestFinalizeCountsConfirmedFix(unittest.TestCase):
    def test_closes_while_head_blob_matches(self):
        s = state_with(nv_row(), fix_verdicts={NVH: applied_verdict()})
        c = carry_state.finalize_counts(s, {F: BLOB})
        self.assertEqual(c["undecided_nv"], 0)
        self.assertEqual(c["verified_confirmed_fix_hashes"], [NVH])
        self.assertEqual(c["verified_obsolete_hashes"], [])

    def test_reopens_when_head_moved(self):
        s = state_with(nv_row(), fix_verdicts={NVH: applied_verdict()})
        for blobs in ({F: "2" * 40}, {}, None):
            with self.subTest(blobs=blobs):
                c = carry_state.finalize_counts(s, blobs)
                self.assertEqual(c["undecided_nv_hashes"], [NVH])
                self.assertEqual(c["verified_confirmed_fix_hashes"], [])

    def test_stale_pass_never_closes(self):
        s = state_with(nv_row(), fix_verdicts={NVH: applied_verdict(at_pass=0)})
        self.assertEqual(carry_state.finalize_counts(s, {F: BLOB})["undecided_nv"], 1)

    def test_applied_without_commit_never_closes(self):
        v = applied_verdict()
        del v["commit_sha"]
        s = state_with(nv_row(), fix_verdicts={NVH: v})
        self.assertEqual(carry_state.finalize_counts(s, {F: BLOB})["undecided_nv"], 1)

    def test_applied_on_non_nv_row_never_closes(self):
        s = state_with(warning_row(), fix_verdicts={WH: applied_verdict()})
        c = carry_state.finalize_counts(s, {F: BLOB})
        self.assertEqual(c["outstanding_cw_hashes"], [WH])

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
        self.assertEqual(c["verified_confirmed_fix_hashes"], [])


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


class TestScoreConfirmedFix(unittest.TestCase):
    def _pass1(self):
        rows = _nv_rows(score.run(_nv_env([_nv()])))
        self.assertEqual(len(rows), 1)
        return rows[0]

    def _pass2(self, cf, verdicts):
        return score.run(_nv_env([], carryforward=[cf], pass_number=2,
                                 head_sha="e" * 40, verdicts=verdicts))

    def test_changed_code_with_confirmed_fix_resolves(self):
        p1 = self._pass1()
        cf = _nv_cf(p1, None, None)  # the fix changed the code: not located
        r = self._pass2(cf, [confirmed_verdict(p1["stable_hash"])])
        self.assertEqual(_nv_rows(r), [])
        self.assertEqual(len(r["resolved"]), 1)
        res = r["resolved"][0]
        self.assertEqual(res["stable_hash"], p1["stable_hash"])
        self.assertEqual(res["band"], score.NV_BAND)
        self.assertEqual(res["resolution"], {
            "source": "confirmed-fix", "agents": ["fix"], "verdict": "applied",
            "head_sha": "d" * 40, "at_pass": 2, "reason": "validate parse_limit",
            "verified_blob": BLOB, "commit_sha": SHA})
        self.assertEqual(state_shape.check_resolved_record(res, FUTURE), [])

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
        p1 = self._pass1()
        r = self._pass2(_nv_cf(p1, None, None),
                        [confirmed_verdict(p1["stable_hash"], at_pass=0)])
        self.assertEqual(len(_nv_rows(r)), 1)
        self.assertEqual(_rejections(r), ["verdict: stale fix verdict"])

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

    def test_stable_hash_and_golden_digest_unchanged(self):
        import test_score
        self.assertEqual(score.stable_hash("a.py", "  x=1", "title"),
                         test_score.GOLDEN_DIGEST)


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

    def test_mutant_finalize_band_check_removed(self):
        s = state_with(warning_row(), fix_verdicts={WH: applied_verdict()})
        self.assertEqual(carry_state.finalize_counts(s, {F: BLOB})["outstanding_cw"], 1)
        mod = _mutant(CARRY_STATE_PY, "cs_m5",
                      "record.get(\"band\") == NV_BAND and _sha40(",
                      "_sha40(")
        self.assertEqual(mod.finalize_counts(s, {F: BLOB})["outstanding_cw"], 0)

    def test_mutant_score_band_check_removed(self):
        f = _nv()
        del f["needs_verification"]
        f["agent_confidence"] = 95
        p1 = score.run(_nv_env([f]))["findings"][0]
        cf = json.loads(json.dumps(p1))
        cf["canonical_line_content"] = "something else entirely"
        cf["canonical_window"] = "something else entirely"
        env = _nv_env([], carryforward=[cf], pass_number=2, head_sha="e" * 40,
                      verdicts=[confirmed_verdict(p1["stable_hash"])])
        self.assertNotIn("resolved", score.run(json.loads(json.dumps(env))))
        mod = _mutant(SCORE_PY, "score_m1",
                      "record.get(\"band\") != NV_BAND", "False")
        self.assertIn("resolved", mod.run(json.loads(json.dumps(env))))


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
    return ("`verified_confirmed_fix_hashes`" in text
            and "source `confirmed-fix`" in text
            and '"verified_confirmed_fix_hashes"' in text)


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
        self.assertFalse(finalize_renders_confirmed_fix_holds(
            text.replace("source `confirmed-fix`", "")))

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


if __name__ == "__main__":
    unittest.main()
