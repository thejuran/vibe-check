"""Verified fixes close: independent evidence closes a carried finding.

A carried finding whose fix an eligible reviewer has confirmed on the code at
HEAD closes on a later run without a dummy code change, a "fixed in <sha>"
dismissal or a repeated owner confirmation. When the originating lane is not
dispatched (always for Codex; deep-only lanes under `/review`), the request is
routed (`route: "independent"`) to a ladder confirmer: the originating agent if
dispatched, else `bugs`, else `security`, else the first dispatched reviewer;
`fix` and `codex-adversarial` never confirm. A carried member, whose origin
lane is dispatched, is asked on a "bound plain" request: a plain request that
also carries the `snapshot_blob` the reviewer judged.

Closure needs the confirmer's `resolved` verdict AND fresh-code proof: the
request's `snapshot_blob` equals the collect-time `head_blobs[file]` (both
non-null). A `persisted` record (pinned line unchanged) also needs a trigger:
its file or one of its associated tests was touched since it was raised
(`touched_paths`), or the change ranges reach the pinned line or the 5 lines
beneath it. Any `still-applies` keeps the record open and records
`recheck_settled`, so it is not re-asked until its code changes. When the
envelope carries `head_blobs` and an eligible lead received no request, the
scorer explains why it did not close.

Fixture provenance: `fixtures/iplayarr45-six-row-state.json` is a trimmed copy
of the owner's real iPlayarr phase-45 review state (archived 2026-10-20,
passes 1-3). It keeps only the six-row lineage (four Codex-origin rows, one
compliance row, one test-sufficiency row), each finding's schema-required keys
plus `current_code` / `canonical_line_content` / `members` / `snapshot` /
`kept_open`, the real `verdict: record not needs-recheck` rejections and the
`codex` blocks. It has no `decisions` root: the owner's "fixed in review-pass
commits" dismissals are exactly what these tests make unnecessary. The fix
commits and the paths they touched are recorded in FIX_COMMITS below, taken
from the iPlayarr git history.
"""

import hashlib
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import score  # noqa: E402
import state_shape  # noqa: E402
from test_score import GOLDEN_DIGEST, _verdict_rejections, make_finding  # noqa: E402
from test_confirmed_fix import _rejections, reviewer_verdict  # noqa: E402

SIX_ROW_FIXTURE = os.path.join(HERE, "fixtures", "iplayarr45-six-row-state.json")
FUTURE = state_shape.load_schema("future")

# The six rows the owner dismissed by hand, by pass-3 stable_hash prefix.
SIX = ("3dd41363", "0249b52c", "a264e9e9", "22d360d9", "2a01829c", "7bc336e7")
CODEX_ROWS = SIX[:4]
# HEAD is unchanged since pass 3: the fixes were already in by pass 2.
HEAD4 = "e3f7624f"

# The commit that fixed each row and every path it touched (iPlayarr git).
FIX_COMMITS = {
    "0249b52c": {"commit": "a5a75387577d1dc23859a0dfe9cb2141d77f8912",
                 "touched": ["src/endpoints/sabnzbd/AddFileEndpoint.ts",
                             "tests/endpoints/sabnzbd/AddFileEndpoint.test.ts"]},
    "3dd41363": {"commit": "8bb338076f87e854ad43fbb202ea92594693dd30",
                 "touched": ["frontend/src/views/BrowseProgrammePage.vue",
                             "frontend/src/views/BrowseProgrammePage.test.js"]},
    # The fix is not in the pinned file (V3ArrService.ts).
    "a264e9e9": {"commit": "a38f8cfde5311ada90b4956289a27d8c5257b6f4",
                 "touched": ["src/service/browse/ArrDiscoveryHandoffService.ts",
                             "src/types/browse.ts",
                             "tests/service/browse/ArrDiscoveryHandoffService.test.ts"]},
    "2a01829c": {"commit": "849fc202e767899ae291668a20271669b6eaa1ad",
                 "touched": ["src/service/browse/ArrDiscoveryHandoffService.ts",
                             "tests/service/browse/ArrDiscoveryHandoffService.test.ts"]},
    "22d360d9": {"commit": "addc547af1f2780f13673140d7ac9ad895feb11d",
                 "touched": ["src/utils/integrationDeadline.ts",
                             "tests/utils/integrationDeadline.test.ts"]},
    # Tests-only fix.
    "7bc336e7": {"commit": "64ac1c6732b6674b5cdf38167a49594a8071641e",
                 "touched": ["tests/facade/arrFacade.test.ts"]},
}

# The closure contract's fixed reasons, verbatim. Asserted literally so a
# scorer that renames one is caught.
R_IR_NO_REVIEWER = "verdict: fix not yet confirmed: no eligible reviewer ran this pass"
R_IR_NO_ANSWER = "verdict: fix not yet confirmed: the routed reviewer gave no verdict"
R_IR_STILL = "verdict: fix not confirmed: the routed reviewer says it still applies"
R_IR_SNAPSHOT = "verdict: fix not confirmed: the reviewed code is not the code at HEAD"
R_IR_NO_TRIGGER = "verdict: fix not confirmed: no change near the finding or in its file since it was raised"
R_IR_SETTLED = "verdict: fix not confirmed: a reviewer said it still applies and the code is unchanged since"
R_CF_SETTLED = ("verdict: confirmed fix not verified: the routed reviewer said it "
                "still applies and the code is unchanged since")
R_NOT_NEEDS_RECHECK = "verdict: record not needs-recheck"
R_MALFORMED = "verdict: malformed"


def _fake_blob(path):
    """A deterministic, distinct 40-hex stand-in for a git blob id."""
    return hashlib.sha1(path.encode("utf-8")).hexdigest()


def _six_state():
    with open(SIX_ROW_FIXTURE) as fh:
        return json.load(fh)


def _six_leads():
    """The pass-3 carried leads by 8-char stable_hash prefix (deep copies)."""
    return {f["stable_hash"][:8]: f for f in _six_state()["passes"][2]["findings"]
            if f["stable_hash"][:8] in SIX}


def _pinned_files():
    return sorted({lead["file"] for lead in _six_leads().values()})


BLOBS = {p: _fake_blob(p)
         for p in sorted(set(_pinned_files())
                         | {t for c in FIX_COMMITS.values() for t in c["touched"]})}


def _six_carryforward():
    """05-state.md step 2 + 30-collect-score step 0 for pass 4, HEAD unchanged
    since pass 3: every carried record's HEAD read is its own stored canonical
    (members sit at their lead's line, so they read the same HEAD line)."""
    out = []
    for prefix in SIX:
        e = json.loads(json.dumps(_six_leads()[prefix]))
        e["canonical_window"] = None
        for m in e.get("members", []):
            m["canonical_line_content"] = e["canonical_line_content"]
        out.append(e)
    return out


def _touched(**over):
    """`touched_paths` keyed by the FULL lead stable_hash. `over` replaces one
    lead's list by prefix (an empty list = nothing touched since raised)."""
    leads = _six_leads()
    out = {}
    for prefix in SIX:
        paths = over.get("p" + prefix, FIX_COMMITS[prefix]["touched"])
        out[leads[prefix]["stable_hash"]] = list(paths)
    return out


def _head_blobs(**over):
    blobs = dict(BLOBS)
    blobs.update(over)
    return blobs


def _independent_request(lead, token, agents=("bugs",), snapshot=None,
                         test_paths=None, fix_commit=None, **over):
    req = {"token": token, "agents": list(agents),
           "stable_hash": lead["stable_hash"], "file": lead["file"],
           "line": lead["line"], "agent": lead["agent"], "title": lead["title"],
           "route": "independent",
           "snapshot_blob": BLOBS[lead["file"]] if snapshot is None else snapshot,
           "test_paths": list(test_paths or [])}
    if fix_commit is not None:
        req["fix_commit"] = fix_commit
    req.update(over)
    return req


def _plain_request(record, token, agent, snapshot=None, stable_hash=None, **over):
    """A bound plain request: the origin lane is asked, and the request names
    the snapshot it judged. Members pass stable_hash=None."""
    req = {"token": token, "agents": [agent], "stable_hash": stable_hash,
           "file": record["file"], "line": record["line"],
           "agent": record["agent"], "title": record["title"],
           "snapshot_blob": BLOBS[record["file"]] if snapshot is None else snapshot}
    req.update(over)
    return req


def _member(prefix, agent):
    ms = [m for m in _six_leads()[prefix]["members"] if m["agent"] == agent]
    assert len(ms) == 1, (prefix, agent, ms)
    return ms[0]


def _default_requests():
    leads = _six_leads()
    reqs = {
        "R1": _independent_request(leads["3dd41363"], "R1"),
        "R2": _independent_request(leads["0249b52c"], "R2"),
        "R3": _independent_request(leads["a264e9e9"], "R3"),
        "R4": _independent_request(leads["22d360d9"], "R4"),
        "R5": _plain_request(_member("0249b52c", "bugs"), "R5", "bugs"),
        "R6": _plain_request(_member("0249b52c", "impact"), "R6", "impact"),
        "R7": _plain_request(leads["2a01829c"], "R7", "compliance",
                             stable_hash=leads["2a01829c"]["stable_hash"]),
        "R8": _plain_request(leads["7bc336e7"], "R8", "test-sufficiency",
                             stable_hash=leads["7bc336e7"]["stable_hash"],
                             test_paths=["tests/facade/arrFacade.test.ts"]),
    }
    return reqs


def _resolved_for(requests):
    return [reviewer_verdict(token=t, agent=req["agents"][0],
                             reason="fixed; the reviewed code handles it")
            for t, req in sorted(requests.items())]


def _ranges(mode="far", only=None):
    """`changed_line_ranges` per pinned file. "far" keeps each site in the
    reviewed set but outside the nearby window (so only `touched_paths` can
    trigger); "near" covers the pinned line. `only` overrides one file."""
    out = {}
    for lead in _six_leads().values():
        line = lead["line"]
        if mode == "far":
            out[lead["file"]] = [[line - 12, line - 8]]
        else:
            out[lead["file"]] = [[line - 2, line + 2]]
    out.update(only or {})
    return out


def _pass4_envelope(ranges="far", tokens=None, requests=None, verdicts=None, **over):
    """The pass-4 envelope: HEAD unchanged since pass 3, every fix committed.
    `tokens` selects a subset of the default requests (and their verdicts)."""
    reqs = _default_requests() if requests is None else requests
    if tokens is not None:
        reqs = {t: reqs[t] for t in tokens}
    env = {"command": "deep-review", "all_mode": False, "pass_number": 4,
           "head_sha": HEAD4,
           "changed_line_ranges": _ranges(ranges) if isinstance(ranges, str) else ranges,
           "carryforward": _six_carryforward(), "findings": [],
           "recheck_requests": [reqs[t] for t in sorted(reqs)],
           "verdicts": _resolved_for(reqs) if verdicts is None else verdicts,
           "head_blobs": _head_blobs(), "touched_paths": _touched()}
    env.update(over)
    return env


def _sites():
    return {(lead["file"], lead["line"]): prefix
            for prefix, lead in _six_leads().items()}


def _rows_at_six_sites(result):
    """Every emitted row at one of the six sites, leads and members[]."""
    sites = _sites()
    out = []
    for f in result.get("findings", []):
        for rec in [f] + list(f.get("members", []) or []):
            if (rec.get("file"), rec.get("line")) in sites:
                out.append(rec)
    return out


def _resolved_prefixes(result):
    return {x["stable_hash"][:8] for x in result.get("resolved", [])
            if isinstance(x.get("stable_hash"), str)}


def _resolved_entry(result, prefix):
    hits = [x for x in result.get("resolved", [])
            if isinstance(x.get("stable_hash"), str) and x["stable_hash"].startswith(prefix)]
    return hits[0] if len(hits) == 1 else None


def _run(env):
    return score.run(json.loads(json.dumps(env)))


class TestSixRowFixtureGuards(unittest.TestCase):
    """The fixture holds what the closure tests assume. Green today and after."""

    def test_fixture_shape(self):
        state = _six_state()
        self.assertEqual(sorted(state), ["medium_acknowledgments", "passes"])
        self.assertEqual(state_shape.check_state(state, FUTURE), [])
        leads = _six_leads()
        self.assertEqual(sorted(leads), sorted(SIX))
        status = {p: leads[p]["status"] for p in SIX}
        self.assertEqual(status, {"3dd41363": "needs-recheck", "0249b52c": "needs-recheck",
                                  "a264e9e9": "needs-recheck", "22d360d9": "persisted",
                                  "2a01829c": "persisted", "7bc336e7": "persisted"})
        for p in CODEX_ROWS:
            self.assertEqual(leads[p]["agent"], "codex-adversarial")
            self.assertIsNone(leads[p].get("current_code"))
        self.assertEqual(leads["22d360d9"]["canonical_line_content"], "")
        self.assertEqual([m["agent"] for m in leads["0249b52c"]["members"]],
                         ["codex-adversarial", "bugs", "impact"])

    def test_without_verdicts_all_six_rows_stay_open(self):
        # Without this, "no row left at the six sites" could pass vacuously.
        r = _run(_pass4_envelope(requests={}, verdicts=[]))
        self.assertNotIn("resolved", r)
        rows = _rows_at_six_sites(r)
        leads = {(x["file"], x["line"], x["agent"], x["title"]) for x in rows}
        for lead in _six_leads().values():
            self.assertIn((lead["file"], lead["line"], lead["agent"], lead["title"]), leads)
        member_agents = {x["agent"] for x in rows
                         if x["file"] == "src/endpoints/sabnzbd/AddFileEndpoint.ts"}
        self.assertEqual(member_agents, {"codex-adversarial", "bugs", "impact"})

    def test_fix_commits_are_full_shas(self):
        self.assertEqual(sorted(FIX_COMMITS), sorted(SIX))
        for prefix, c in FIX_COMMITS.items():
            self.assertRegex(c["commit"], r"^[0-9a-f]{40}$")
            self.assertTrue(c["touched"])


class TestSixRowClosure(unittest.TestCase):
    """The owner's six already-fixed rows close on independent evidence."""

    def _assert_closed(self, r, prefix, agents=None):
        entry = _resolved_entry(r, prefix)
        self.assertIsNotNone(entry, "%s not resolved; rejections: %r"
                             % (prefix, _rejections(r)))
        res = entry["resolution"]
        self.assertEqual(res["source"], "recheck")
        self.assertEqual(res.get("verified_blob"), BLOBS[entry["file"]])
        if agents is not None:
            self.assertEqual(res["agents"], agents)
        site = (entry["file"], entry["line"])
        self.assertEqual([x for x in _rows_at_six_sites(r)
                          if (x["file"], x["line"]) == site
                          and x["agent"] == entry["agent"]], [])
        return entry

    def _assert_open(self, r, prefix, reason):
        lead = _six_leads()[prefix]
        self.assertIsNone(_resolved_entry(r, prefix))
        self.assertTrue([x for x in _rows_at_six_sites(r)
                         if (x["file"], x["line"], x["agent"])
                         == (lead["file"], lead["line"], lead["agent"])])
        at_site = [x["reason"] for x in _verdict_rejections(r)
                   if (x["file"], x["line"]) == (lead["file"], lead["line"])]
        self.assertIn(reason, at_site, "rejections at the site: %r" % at_site)

    def test_fixture_pins_the_real_rejections(self):
        """GREEN today and forever: the reproduced failure, as recorded."""
        state = _six_state()
        want = {("src/endpoints/sabnzbd/AddFileEndpoint.ts", 204): 2,
                ("src/service/browse/ArrDiscoveryHandoffService.ts", 201): 2,
                ("src/facade/arrFacade.ts", 80): 2}
        for p in state["passes"][1:]:
            got = {}
            for x in p["filtered"]:
                if x["reason"] == R_NOT_NEEDS_RECHECK:
                    key = (x["file"], x["line"])
                    got[key] = got.get(key, 0) + 1
            self.assertEqual(got, want, "pass %d" % p["pass_number"])
        self.assertEqual(state["passes"][0]["filtered"], [])

    def test_persisted_rows_rejected_today_without_binding(self):
        """GREEN today and after: an unbound plain `resolved` never closes a
        persisted record, even with trigger facts present."""
        lead = _six_leads()["2a01829c"]
        req = _plain_request(lead, "R7", "compliance", stable_hash=lead["stable_hash"])
        del req["snapshot_blob"]
        r = _run(_pass4_envelope(requests={"R7": req}))
        self.assertIsNone(_resolved_entry(r, "2a01829c"))
        at_site = [x["reason"] for x in _verdict_rejections(r)
                   if (x["file"], x["line"]) == (lead["file"], lead["line"])]
        self.assertEqual(at_site, [R_NOT_NEEDS_RECHECK])
        self.assertTrue([x for x in _rows_at_six_sites(r) if x["agent"] == "compliance"])

    def test_all_six_close_on_independent_evidence(self):
        """RED today: `verdict: malformed` (routed) and `record not needs-recheck`
        (bound plain)."""
        r = _run(_pass4_envelope())
        self.assertEqual(_rejections(r), [])
        self.assertEqual(_resolved_prefixes(r), set(SIX))
        self.assertEqual(_rows_at_six_sites(r), [])
        files = {lead["file"] for lead in _six_leads().values()}
        for x in r["resolved"]:
            self.assertIn(x["file"], files)
            self.assertEqual(x["resolution"]["source"], "recheck")
            self.assertEqual(x["resolution"].get("verified_blob"), BLOBS[x["file"]])
        for p in CODEX_ROWS:
            self.assertEqual(_resolved_entry(r, p)["resolution"]["agents"], ["bugs"])
        member_agents = sorted(x["agent"] for x in r["resolved"]
                               if x["file"] == "src/endpoints/sabnzbd/AddFileEndpoint.ts"
                               and x["agent"] != "codex-adversarial")
        self.assertEqual(member_agents, ["bugs", "impact"])

    def test_code_beneath_unchanged_line_closes_via_file_touch(self):
        """RED today (P2a): `record not needs-recheck`."""
        r = _run(_pass4_envelope(tokens=["R7"]))
        self._assert_closed(r, "2a01829c", agents=["compliance"])

    def test_tests_only_fix_closes_via_associated_test(self):
        """RED today (P2b): `record not needs-recheck`."""
        r = _run(_pass4_envelope(
            tokens=["R8"],
            touched_paths=_touched(p7bc336e7=["tests/facade/arrFacade.test.ts"])))
        self._assert_closed(r, "7bc336e7", agents=["test-sufficiency"])

    def test_tests_only_fix_needs_the_association(self):
        """RED today: `record not needs-recheck` instead of the no-trigger reason."""
        r = _run(_pass4_envelope(
            tokens=["R8"],
            touched_paths=_touched(p7bc336e7=["tests/utils/integrationDeadline.test.ts"])))
        self._assert_open(r, "7bc336e7", R_IR_NO_TRIGGER)

    def test_codex_rows_close_via_ladder_confirmer(self):
        """RED today (P2c): `verdict: malformed` for every routed request."""
        r = _run(_pass4_envelope(tokens=["R1", "R2", "R3", "R4", "R5", "R6"]))
        for p in CODEX_ROWS:
            entry = self._assert_closed(r, p, agents=["bugs"])
            self.assertEqual(entry["agent"], "codex-adversarial")
        self.assertEqual([x for x in _rows_at_six_sites(r)
                          if x["file"] == "src/endpoints/sabnzbd/AddFileEndpoint.ts"], [])

    def test_persisted_codex_blank_line_needs_trigger(self):
        """RED today: `verdict: malformed`."""
        r = _run(_pass4_envelope(tokens=["R4"], touched_paths=_touched(p22d360d9=[])))
        self._assert_open(r, "22d360d9", R_IR_NO_TRIGGER)
        r = _run(_pass4_envelope(tokens=["R4"]))
        self._assert_closed(r, "22d360d9", agents=["bugs"])

    def test_fix_outside_pinned_file_still_closes_needs_recheck_row(self):
        """RED today: `verdict: malformed`. The fix touched only other files."""
        self.assertNotIn("src/service/arr/V3ArrService.ts", FIX_COMMITS["a264e9e9"]["touched"])
        r = _run(_pass4_envelope(tokens=["R3"]))
        self._assert_closed(r, "a264e9e9", agents=["bugs"])

    def test_nearby_change_triggers_without_a_touching_commit(self):
        """RED today: `record not needs-recheck`."""
        lead = _six_leads()["2a01829c"]
        line = lead["line"]
        r = _run(_pass4_envelope(ranges="near", tokens=["R7"],
                                 touched_paths=_touched(p2a01829c=[])))
        self._assert_closed(r, "2a01829c", agents=["compliance"])
        r = _run(_pass4_envelope(
            ranges=_ranges("far", only={lead["file"]: [[line + 6, line + 9]]}),
            tokens=["R7"], touched_paths=_touched(p2a01829c=[])))
        self._assert_open(r, "2a01829c", R_IR_NO_TRIGGER)

    def test_commit_sha_recorded_when_supplied(self):
        """RED today: `verdict: malformed`."""
        sha = FIX_COMMITS["3dd41363"]["commit"]
        reqs = _default_requests()
        reqs["R1"] = _independent_request(_six_leads()["3dd41363"], "R1", fix_commit=sha)
        r = _run(_pass4_envelope(requests=reqs, tokens=["R1"]))
        entry = self._assert_closed(r, "3dd41363")
        self.assertEqual(entry["resolution"].get("commit_sha"), sha)
        r = _run(_pass4_envelope(tokens=["R1"]))
        entry = self._assert_closed(r, "3dd41363")
        self.assertNotIn("commit_sha", entry["resolution"])

    def test_no_decisions_needed(self):
        """RED today: nothing closes, so the dismissals would still be needed."""
        self.assertNotIn("decisions", _six_state())
        r = _run(_pass4_envelope())
        self.assertEqual(_resolved_prefixes(r), set(SIX),
                         "rejections: %r" % _rejections(r))

    def test_stable_hash_and_golden_digest_unchanged(self):
        """GREEN today and after."""
        self.assertEqual(score.stable_hash("a.py", "  x=1", "title"), GOLDEN_DIGEST)


# --------------------------------------------------------------------------- #
# /review closes a finding only /deep-review lanes raise
# --------------------------------------------------------------------------- #
TS_FILE = "src/facade/arrFacade.ts"
TS_TEST = "tests/facade/arrFacade.test.ts"
TS_CODE = ("    addSeries(app: App, match: ArrLookupResponse, options: ArrAddOptions) {\n"
           "        return this.client(app).post('/series', match);")
B1 = "b1" * 20
B2 = "b2" * 20
T1 = "71" * 20
HEAD_TS = "f" * 40


def _ts_row():
    """Pass 1 under /deep-review: one test-sufficiency finding, as emitted."""
    f = make_finding(id="ts-001", agent="test-sufficiency", file=TS_FILE, line=80,
                     title="No test checks that addSeries passes the shared deadline",
                     current_code=TS_CODE, severity="medium", agent_confidence=85,
                     category="test-coverage",
                     source_window=["a", "b", "c", "d", "e"])
    f["canonical_line_content"] = TS_CODE.split("\n", 1)[0]
    r = score.run({"command": "deep-review", "all_mode": False, "pass_number": 1,
                   "head_sha": "a" * 40, "changed_line_ranges": {TS_FILE: [[78, 82]]},
                   "carryforward": [], "findings": [f]})
    rows = [x for x in r["findings"] if x["agent"] == "test-sufficiency"]
    assert len(rows) == 1, r
    return rows[0]


def _review_pass2(row, requests, verdicts, status="persisted", head_blobs=None,
                  touched=None):
    """The pass-2 `/review` envelope (test-sufficiency is not dispatched).
    persisted: HEAD's pinned line is the stored first line; needs-recheck: it
    changed. Change ranges are far from the line."""
    cf = json.loads(json.dumps(row))
    first = cf["current_code"].split("\n", 1)[0]
    cf["canonical_line_content"] = first if status == "persisted" else "    // rewritten"
    cf["canonical_window"] = None
    return {"command": "review", "all_mode": False, "pass_number": 2,
            "head_sha": HEAD_TS, "changed_line_ranges": {TS_FILE: [[10, 14]]},
            "carryforward": [cf], "findings": [],
            "recheck_requests": list(requests), "verdicts": list(verdicts),
            "head_blobs": ({TS_FILE: B1, TS_TEST: T1} if head_blobs is None
                           else head_blobs),
            "touched_paths": ({row["stable_hash"]: [TS_TEST]} if touched is None
                              else touched)}


def _ts_request(row, token="R1", agents=("bugs",), snapshot=B1, **over):
    req = {"token": token, "agents": list(agents), "stable_hash": row["stable_hash"],
           "file": row["file"], "line": row["line"], "agent": row["agent"],
           "title": row["title"], "route": "independent", "snapshot_blob": snapshot,
           "test_paths": [TS_TEST]}
    req.update(over)
    return req


def _ts_rows(result, row):
    return [x for x in result.get("findings", [])
            if (x.get("file"), x.get("line"), x.get("agent"), x.get("title"))
            == (row["file"], row["line"], row["agent"], row["title"])]


class TestReviewClosesDeepOnlyFinding(unittest.TestCase):
    """Under /review, `bugs` confirms a fix for a test-sufficiency finding."""

    def test_ts_row_shape(self):
        """GREEN today and after: the builder emits the row the tests assume."""
        row = _ts_row()
        self.assertEqual((row["agent"], row["file"], row["line"]),
                         ("test-sufficiency", TS_FILE, 80))
        r = score.run(_review_pass2(row, [], []))
        self.assertEqual(len(_ts_rows(r, row)), 1)
        self.assertEqual(_ts_rows(r, row)[0]["status"], "persisted")

    def test_bugs_confirms_test_sufficiency_finding_under_review(self):
        """RED today: `verdict: malformed`."""
        row = _ts_row()
        r = score.run(_review_pass2(row, [_ts_request(row)],
                                    [reviewer_verdict(agent="bugs")]))
        self.assertEqual(_rejections(r), [])
        self.assertEqual(len(r.get("resolved", [])), 1, _rejections(r))
        self.assertEqual(r["resolved"][0]["agent"], "test-sufficiency")
        self.assertEqual(r["resolved"][0]["resolution"]["agents"], ["bugs"])
        self.assertEqual(r["resolved"][0]["resolution"].get("verified_blob"), B1)
        self.assertEqual(_ts_rows(r, row), [])

    def test_no_confirmer_shows_bounded_reason(self):
        """RED today: no reason is emitted, the row just stays."""
        row = _ts_row()
        r = score.run(_review_pass2(row, [], []))
        self.assertEqual(len(_ts_rows(r, row)), 1)
        self.assertEqual(_rejections(r), [R_IR_NO_REVIEWER])
        rej = _verdict_rejections(r)[0]
        self.assertEqual((rej["file"], rej["line"], rej["title"]),
                         (row["file"], row["line"], row["title"]))

    def test_no_confirmer_reason_absent_when_not_eligible(self):
        """GREEN before and after: a persisted row with no nearby change and no
        touching commit is not re-checked every run, so no reason is shown."""
        row = _ts_row()
        r = score.run(_review_pass2(row, [], [], touched={}))
        self.assertEqual(len(_ts_rows(r, row)), 1)
        self.assertEqual(_rejections(r), [])

    def test_no_confirmer_reason_absent_without_head_blobs(self):
        """GREEN before and after: envelopes that predate the contract (no
        `head_blobs`) score exactly as before."""
        row = _ts_row()
        env = _review_pass2(row, [], [])
        del env["head_blobs"]
        r = score.run(env)
        self.assertEqual(len(_ts_rows(r, row)), 1)
        self.assertEqual(_rejections(r), [])

    def test_needs_recheck_row_closes_without_trigger(self):
        """RED today: `verdict: malformed`. A changed pinned line needs no trigger."""
        row = _ts_row()
        r = score.run(_review_pass2(row, [_ts_request(row)],
                                    [reviewer_verdict(agent="bugs")],
                                    status="needs-recheck", touched={}))
        self.assertEqual(_rejections(r), [])
        self.assertEqual(len(r.get("resolved", [])), 1)
        self.assertEqual(r["resolved"][0]["resolution"]["agents"], ["bugs"])
        self.assertEqual(_ts_rows(r, row), [])


if __name__ == "__main__":
    unittest.main()
