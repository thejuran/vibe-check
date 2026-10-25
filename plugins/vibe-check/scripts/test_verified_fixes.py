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
R_CF_SETTLED = "verdict: confirmed fix not verified: the routed reviewer said it still applies and the code is unchanged since"
R_NOT_NEEDS_RECHECK = "verdict: record not needs-recheck"
R_MALFORMED = "verdict: malformed"
R_CONTRADICTED = "verdict: contradicted by still-applies"


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
    for m in cf.get("members", []):
        m["canonical_line_content"] = cf["canonical_line_content"]
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

    def test_no_confirmer_reason_not_doubled_under_a_confirmed_fix(self):
        """A lead awaiting the independent half of a confirmed fix already says
        why (`confirmed fix awaiting independent re-check`); the generic
        reason is not added on top."""
        import test_confirmed_fix as tcf
        from test_score import _nv, _nv_cf, _nv_env, _nv_rows
        p1 = _nv_rows(score.run(_nv_env([_nv(agent="codex-adversarial")])))[0]
        env = _nv_env([], carryforward=[_nv_cf(p1, None, None)], pass_number=2,
                      head_sha=tcf.HEAD2, recheck_requests=[],
                      verdicts=[tcf.confirmed_verdict(p1["stable_hash"])],
                      head_blobs={p1["file"]: tcf.BLOB}, touched_paths={})
        r = score.run(json.loads(json.dumps(env)))
        self.assertEqual(_rejections(r), [tcf.R_NO_REVIEWER])
        # Without the fix verdict the same lead does get the generic reason.
        env["verdicts"] = []
        r = score.run(json.loads(json.dumps(env)))
        self.assertEqual(_rejections(r), [R_IR_NO_REVIEWER])

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


# --------------------------------------------------------------------------- #
# Safeguards on the independent route: stale evidence, still-applies, who may
# confirm
# --------------------------------------------------------------------------- #
def _settled(row, blobs, at_pass=1, head_sha="a" * 40):
    """`row` as carried after a reviewer answered still-applies on `blobs`."""
    out = json.loads(json.dumps(row))
    out["recheck_settled"] = {"verdict": "still-applies", "at_pass": at_pass,
                              "head_sha": head_sha, "fingerprint": dict(blobs)}
    return out


class TestIndependentRouteSafeguards(unittest.TestCase):
    """Stale evidence never closes; still-applies keeps the finding open; the
    fixer and Codex never confirm."""

    def _open(self, r, row, reasons):
        self.assertNotIn("resolved", r)
        self.assertEqual(len(_ts_rows(r, row)), 1)
        self.assertEqual(_rejections(r), reasons)

    def test_reason_constants_match_contract(self):
        """RED today: the constants do not exist yet."""
        want = {"_INDEPENDENT_ROUTE": "independent",
                "_NEVER_CONFIRMERS": frozenset({"fix", "codex-adversarial"}),
                "_NEARBY_LINES": 5,
                "_R_IR_NO_REVIEWER": R_IR_NO_REVIEWER,
                "_R_IR_NO_ANSWER": R_IR_NO_ANSWER,
                "_R_IR_STILL": R_IR_STILL,
                "_R_IR_SNAPSHOT": R_IR_SNAPSHOT,
                "_R_IR_NO_TRIGGER": R_IR_NO_TRIGGER,
                "_R_IR_SETTLED": R_IR_SETTLED,
                "_R_CF_SETTLED": R_CF_SETTLED}
        for name, value in want.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(score, name, "<missing>"), value)
        self.assertEqual(score._FIXER_AGENTS, frozenset({"fix"}))

    def test_changed_code_is_stale(self):
        """RED today: `verdict: malformed`."""
        row = _ts_row()
        r = score.run(_review_pass2(row, [_ts_request(row, snapshot=B1)],
                                    [reviewer_verdict(agent="bugs")],
                                    head_blobs={TS_FILE: B2, TS_TEST: T1}))
        self._open(r, row, [R_IR_SNAPSHOT])

    def test_null_snapshot_is_inconclusive(self):
        """RED today: `verdict: malformed`."""
        row = _ts_row()
        r = score.run(_review_pass2(row, [_ts_request(row, snapshot=None)],
                                    [reviewer_verdict(agent="bugs")]))
        self._open(r, row, [R_IR_SNAPSHOT])

    def test_null_head_blob_is_inconclusive(self):
        """RED today: `verdict: malformed`."""
        row = _ts_row()
        r = score.run(_review_pass2(row, [_ts_request(row)],
                                    [reviewer_verdict(agent="bugs")],
                                    head_blobs={TS_FILE: None, TS_TEST: T1}))
        self._open(r, row, [R_IR_SNAPSHOT])

    def test_still_applies_keeps_open_and_settles(self):
        """RED today: `verdict: malformed`, and no `recheck_settled` key."""
        row = _ts_row()
        r = score.run(_review_pass2(row, [_ts_request(row)],
                                    [reviewer_verdict(agent="bugs", verdict="still-applies",
                                                      reason="no deadline assertion yet")]))
        self._open(r, row, [R_IR_STILL])
        self.assertEqual(_ts_rows(r, row)[0].get("recheck_settled"),
                         {"verdict": "still-applies", "at_pass": 2, "head_sha": HEAD_TS,
                          "fingerprint": {TS_FILE: B1, TS_TEST: T1}})

    def test_settled_row_not_reasked_on_unchanged_code(self):
        """RED today: `verdict: malformed`. Nothing changed since still-applies,
        so a stray `resolved` cannot close it."""
        row = _ts_row()
        settled = _settled(row, {TS_FILE: B1, TS_TEST: T1})
        r = score.run(_review_pass2(settled, [_ts_request(row)],
                                    [reviewer_verdict(agent="bugs")], touched={}))
        self._open(r, row, [R_IR_SETTLED])

    def test_settled_row_reasked_after_code_change(self):
        """RED today: `verdict: malformed`. New code or a new touching commit is
        a fresh start."""
        row = _ts_row()
        settled = _settled(row, {TS_FILE: B1, TS_TEST: T1})
        # The file's blob changed (the pinned line moved, so no trigger is needed).
        r = score.run(_review_pass2(settled, [_ts_request(row, snapshot=B2)],
                                    [reviewer_verdict(agent="bugs")],
                                    status="needs-recheck", touched={},
                                    head_blobs={TS_FILE: B2, TS_TEST: T1}))
        self.assertEqual(_rejections(r), [])
        self.assertEqual(len(r.get("resolved", [])), 1)
        self.assertNotIn("recheck_settled", r["resolved"][0])
        self.assertEqual(r["resolved"][0]["resolution"].get("verified_blob"), B2)
        # A new touching commit with the pinned file's blob unchanged.
        r = score.run(_review_pass2(settled, [_ts_request(row)],
                                    [reviewer_verdict(agent="bugs")],
                                    touched={row["stable_hash"]: [TS_TEST]}))
        self.assertEqual(_rejections(r), [])
        self.assertEqual(len(r.get("resolved", [])), 1)
        self.assertEqual(_ts_rows(r, row), [])

    def test_silent_reviewer_keeps_open(self):
        """RED today: `verdict: malformed` instead of the no-answer reason."""
        row = _ts_row()
        r = score.run(_review_pass2(row, [_ts_request(row)], []))
        self._open(r, row, [R_IR_NO_ANSWER])

    def test_never_confirmers_rejected(self):
        """RED today: the bound plain request to `codex-adversarial` is accepted
        and closes the needs-recheck row. (The independent subTests are already
        `verdict: malformed` today, because the route is unknown.)"""
        row = _ts_row()
        cases = [("independent", ["fix"]), ("independent", ["codex-adversarial"]),
                 ("independent", ["bugs", "codex-adversarial"]),
                 ("bound plain", ["codex-adversarial"])]
        for shape, agents in cases:
            with self.subTest(shape=shape, agents=agents):
                req = _ts_request(row, agents=agents)
                if shape == "bound plain":
                    del req["route"], req["test_paths"]
                verdicts = [reviewer_verdict(agent=a) for a in agents]
                r = score.run(_review_pass2(row, [req], verdicts,
                                            status="needs-recheck", touched={}))
                self.assertNotIn("resolved", r)
                self.assertEqual(len(_ts_rows(r, row)), 1)
                self.assertIn(R_MALFORMED, _rejections(r))

    def test_independent_route_requires_stable_hash(self):
        """GREEN today (the route is unknown) and after (no stored hash)."""
        row = _ts_row()
        r = score.run(_review_pass2(row, [_ts_request(row, stable_hash=None)],
                                    [reviewer_verdict(agent="bugs")],
                                    status="needs-recheck", touched={}))
        self.assertNotIn("resolved", r)
        self.assertEqual(len(_ts_rows(r, row)), 1)
        self.assertIn(R_MALFORMED, _rejections(r))

    def test_member_closes_only_bound(self):
        """RED today: the bound member request is `record not needs-recheck`.
        The unbound half is green today and after."""
        member = _member("0249b52c", "bugs")
        site = (member["file"], member["line"])

        def bugs_member_rows(r):
            return [x for x in _rows_at_six_sites(r)
                    if (x["file"], x["line"]) == site and x["agent"] == "bugs"]

        unbound = _plain_request(member, "R5", "bugs")
        del unbound["snapshot_blob"]
        r = _run(_pass4_envelope(requests={"R5": unbound}))
        at_site = [x["reason"] for x in _verdict_rejections(r)
                   if (x["file"], x["line"]) == site]
        self.assertEqual(at_site, [R_NOT_NEEDS_RECHECK])
        self.assertEqual(len(bugs_member_rows(r)), 1)

        r = _run(_pass4_envelope(tokens=["R5"]))
        hits = [x for x in r.get("resolved", [])
                if (x["file"], x["line"], x["agent"]) == site + ("bugs",)]
        self.assertEqual(len(hits), 1, "rejections: %r" % _rejections(r))
        self.assertEqual(hits[0]["resolution"].get("verified_blob"), BLOBS[member["file"]])
        self.assertEqual(bugs_member_rows(r), [])

    def test_still_applies_contradicts_resolved_on_independent(self):
        """RED today: `verdict: malformed`."""
        row = _ts_row()
        r = score.run(_review_pass2(
            row, [_ts_request(row, agents=("bugs", "security"))],
            [reviewer_verdict(agent="bugs"),
             reviewer_verdict(agent="security", verdict="still-applies",
                              reason="the deadline is still not asserted")]))
        self.assertNotIn("resolved", r)
        self.assertEqual(len(_ts_rows(r, row)), 1)
        self.assertIn(R_IR_STILL, _rejections(r))

    def test_recheck_settled_scrubbed_from_new_findings(self):
        """GREEN today (the output shaper drops the unknown key) and after (the
        key is scrubbed from NEW findings, like `status` and `snapshot`): an
        agent cannot forge a still-applies memory."""
        f = make_finding(file="src/z.py", line=5, current_code="  y = 2")
        f["recheck_settled"] = {"verdict": "still-applies", "at_pass": 1,
                                "head_sha": None, "fingerprint": {"src/z.py": B1}}
        r = score.run({"command": "review", "all_mode": False, "pass_number": 1,
                       "changed_line_ranges": {"src/z.py": [[1, 9]]},
                       "findings": [f], "head_blobs": {"src/z.py": B1}})
        rows = [x for x in r["findings"] if x["file"] == "src/z.py"]
        self.assertEqual(len(rows), 1)
        self.assertNotIn("recheck_settled", rows[0])


# --------------------------------------------------------------------------- #
# Test association and the trigger (pure helpers)
# --------------------------------------------------------------------------- #
class TestAssociatedTest(unittest.TestCase):
    def test_associated_pairs(self):
        cases = [
            ("tests/facade/arrFacade.test.ts", "src/facade/arrFacade.ts", True),
            ("frontend/src/views/BrowseProgrammePage.test.js",
             "frontend/src/views/BrowseProgrammePage.vue", True),
            ("test_score.py", "score.py", True),
            ("spec/arrFacade_spec.rb", "lib/arrFacade.rb", True),
            ("pkg/score_test.go", "pkg/score.go", True),
            ("src/__tests__/arrFacade.ts", "src/arrFacade.ts", True),
            ("src/arrFacade-spec.js", "src/arrFacade.js", True),
            ("tests/utils/integrationDeadline.test.ts", "src/utils/other.ts", False),
            ("src/facade/arrFacade.ts", "src/facade/arrFacade.ts", False),
            # Same stem, but nothing marks it as a test.
            ("lib/arrFacade.ts", "src/facade/arrFacade.ts", False),
            ("tests/facade/arrFacade.test.ts", None, False),
            (None, "src/facade/arrFacade.ts", False),
            ("tests/test_.py", "src/.py", False),
        ]
        for path, src, want in cases:
            with self.subTest(path=path, src=src):
                self.assertIs(score._is_associated_test(path, src), want)

    def test_trigger(self):
        f = "src/facade/arrFacade.ts"
        rec = {"file": f, "line": 80}
        self.assertTrue(score._independent_trigger(rec, [f], {}))
        self.assertTrue(score._independent_trigger(rec, ["tests/facade/arrFacade.test.ts"], {}))
        self.assertTrue(score._independent_trigger(rec, [], {f: [[80, 85]]}))
        self.assertTrue(score._independent_trigger(rec, [], {f: [[85, 85]]}))
        self.assertFalse(score._independent_trigger(rec, [], {f: [[86, 90]]}))
        self.assertFalse(score._independent_trigger(rec, [], {f: [[70, 79]]}))
        self.assertFalse(score._independent_trigger(rec, ["src/other.ts"], {"src/other.ts": [[80, 80]]}))
        # A record without a line has only the touched checks.
        self.assertFalse(score._independent_trigger({"file": f, "line": None}, [],
                                                    {f: [[1, 999]]}))
        self.assertTrue(score._independent_trigger({"file": f, "line": None}, [f], {}))
        self.assertFalse(score._independent_trigger({"file": None, "line": 80}, [], {}))


# --------------------------------------------------------------------------- #
# Envelope ingress for the new facts and request shapes
# --------------------------------------------------------------------------- #
class TestEnvelopeIngress56(unittest.TestCase):
    def test_malformed_containers_fail_closed(self):
        row = _ts_row()
        for key, bad in (("head_blobs", [TS_FILE]), ("head_blobs", "x"),
                         ("touched_paths", "x"), ("touched_paths", [TS_TEST])):
            with self.subTest(key=key, bad=bad):
                env = _review_pass2(row, [], [])
                env[key] = bad
                with self.assertRaises(TypeError):
                    score.run(env)

    def test_absent_or_null_containers_are_empty(self):
        row = _ts_row()
        for key in ("head_blobs", "touched_paths"):
            for value in (None, "<absent>"):
                with self.subTest(key=key, value=value):
                    env = _review_pass2(row, [], [])
                    if value == "<absent>":
                        del env[key]
                    else:
                        env[key] = value
                    r = score.run(env)
                    self.assertEqual(len(_ts_rows(r, row)), 1)

    def test_garbage_values_do_not_crash(self):
        row = _ts_row()
        env = _review_pass2(row, [_ts_request(row)], [reviewer_verdict(agent="bugs")],
                            head_blobs={TS_FILE: 5, TS_TEST: ["x"], 3: None},
                            touched={row["stable_hash"]: "x", "other": [1, None, TS_TEST]})
        r = score.run(env)
        self.assertNotIn("resolved", r)
        self.assertEqual(len(_ts_rows(r, row)), 1)

    def test_non_str_head_blob_reads_as_unknown(self):
        row = _ts_row()
        r = score.run(_review_pass2(row, [_ts_request(row, snapshot=B1)],
                                    [reviewer_verdict(agent="bugs")],
                                    head_blobs={TS_FILE: 5, TS_TEST: T1}))
        self.assertNotIn("resolved", r)
        self.assertEqual(_rejections(r), [R_IR_SNAPSHOT])

    def test_non_list_touched_reads_as_nothing_touched(self):
        row = _ts_row()
        for bad in ("x", None, {TS_TEST: 1}, [5, None]):
            with self.subTest(bad=bad):
                r = score.run(_review_pass2(row, [_ts_request(row)],
                                            [reviewer_verdict(agent="bugs")],
                                            touched={row["stable_hash"]: bad}))
                self.assertNotIn("resolved", r)
                self.assertEqual(_rejections(r), [R_IR_NO_TRIGGER])
        # Control: the same list with the associated test closes it.
        r = score.run(_review_pass2(row, [_ts_request(row)],
                                    [reviewer_verdict(agent="bugs")],
                                    touched={row["stable_hash"]: [5, TS_TEST]}))
        self.assertEqual(len(r.get("resolved", [])), 1, _rejections(r))

    def test_request_shapes(self):
        row = _ts_row()
        good = _ts_request(row)
        bound_plain = {k: v for k, v in good.items() if k not in ("route", "test_paths")}
        bads = {
            "independent, no stable_hash": dict(good, stable_hash=None),
            "independent, fixer asked": dict(good, agents=["fix"]),
            "independent, codex asked": dict(good, agents=["bugs", "codex-adversarial"]),
            "independent, nobody asked": dict(good, agents=[]),
            "independent, no snapshot key": {k: v for k, v in good.items()
                                             if k != "snapshot_blob"},
            "independent, empty snapshot": dict(good, snapshot_blob=""),
            "independent, bad fix_commit": dict(good, fix_commit="zz"),
            "independent, short fix_commit": dict(good, fix_commit="abc12"),
            "independent, fix_commit newline": dict(good, fix_commit="abc1234\n"),
            "independent, test_paths not a list": dict(good, test_paths="tests/x"),
            "bound plain, codex asked": dict(bound_plain, agents=["codex-adversarial"]),
            "bound plain, fixer asked": dict(bound_plain, agents=["fix"]),
            "bound plain, empty snapshot": dict(bound_plain, snapshot_blob=""),
            "plain, null route": dict(bound_plain, route=None),
        }
        for name, bad in bads.items():
            with self.subTest(name):
                r = score.run(_review_pass2(row, [bad], [], status="needs-recheck",
                                            touched={}))
                self.assertIn(R_MALFORMED, _rejections(r))
        oks = {
            "independent": good,
            "independent, null snapshot": dict(good, snapshot_blob=None),
            "independent, no test_paths": {k: v for k, v in good.items()
                                           if k != "test_paths"},
            "independent, fix_commit": dict(good, fix_commit="a5a7538"),
            "independent, null fix_commit": dict(good, fix_commit=None),
            "bound plain": bound_plain,
            "bound plain, null snapshot": dict(bound_plain, snapshot_blob=None),
        }
        for name, ok in oks.items():
            with self.subTest(name):
                r = score.run(_review_pass2(row, [ok], [], status="needs-recheck",
                                            touched={}))
                self.assertNotIn(R_MALFORMED, _rejections(r))


# --------------------------------------------------------------------------- #
# Code-review fixes (56-REVIEW.md): each test failed on the reviewed scorer
# --------------------------------------------------------------------------- #
def _still_then(row, status, touched=None, **over):
    """Pass 2: `bugs` says the lead still applies. -> the row as carried into
    pass 3 (the pass-2 output row)."""
    r = score.run(_review_pass2(row, [_ts_request(row)],
                                [reviewer_verdict(agent="bugs", verdict="still-applies")],
                                status=status, touched=touched, **over))
    rows = _ts_rows(r, row)
    assert len(rows) == 1, r
    return rows[0]


def _pass3(carried, requests, verdicts, status, touched, **over):
    env = _review_pass2(carried, requests, verdicts, status=status, touched=touched, **over)
    env["pass_number"] = 3
    return env


def _cf_env(agents):
    """Pass 2 of a Codex-raised Needs-verification item with a confirmed fix,
    its routed re-check asked of `agents`, each answering `resolved`."""
    import test_confirmed_fix as tcf
    from test_score import _nv, _nv_cf, _nv_env, _nv_rows
    p1 = _nv_rows(score.run(_nv_env([_nv(agent="codex-adversarial")])))[0]
    return _nv_env([], carryforward=[_nv_cf(p1, None, None)], pass_number=2,
                   head_sha=tcf.HEAD2,
                   recheck_requests=[tcf.routed_request(p1, agents=agents)],
                   verdicts=[tcf.confirmed_verdict(p1["stable_hash"])]
                   + [reviewer_verdict(agent=a) for a in agents])


class TestReviewFix56(unittest.TestCase):
    """The still-applies memory holds; only HEAD-bound native confirmers close."""

    def _open(self, r, row, reasons):
        self.assertNotIn("resolved", r)
        self.assertEqual(len(_ts_rows(r, row)), 1)
        self.assertEqual(_rejections(r), reasons)

    def test_cr01_settled_memory_survives_a_kept_open_row(self):
        """CR-01: a sub-threshold needs-recheck row keeps the memory its
        still-applies wrote, so a stray `resolved` on unchanged code next run
        does not close it."""
        row = _ts_row()
        carried = _still_then(row, "needs-recheck", touched={})
        self.assertEqual(carried.get("kept_open"), "sub-threshold")
        self.assertEqual(carried.get("recheck_settled"),
                         {"verdict": "still-applies", "at_pass": 2, "head_sha": HEAD_TS,
                          "fingerprint": {TS_FILE: B1, TS_TEST: T1}})
        r = score.run(_pass3(carried, [_ts_request(carried, token="R9")],
                             [reviewer_verdict(token="R9", agent="bugs")],
                             "needs-recheck", {}))
        self._open(r, row, [R_IR_SETTLED])

    def test_cr01_fresh_start_clear_is_not_resurrected(self):
        """CR-01: a memory the fresh-start rule dropped (the code changed) does
        not come back on the kept-open row."""
        row = _ts_row()
        settled = _settled(row, {TS_FILE: B1, TS_TEST: T1})
        r = score.run(_review_pass2(settled, [], [], status="needs-recheck", touched={},
                                    head_blobs={TS_FILE: B2, TS_TEST: T1}))
        rows = _ts_rows(r, row)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get("kept_open"), "sub-threshold")
        self.assertNotIn("recheck_settled", rows[0])

    def test_cr02_unrelated_touch_keeps_the_memory(self):
        """CR-02: a commit to an unrelated path is no fresh start; the finding
        stays settled until its own file, a fingerprinted path or an
        associated test changes."""
        row = _ts_row()
        settled = _settled(row, {TS_FILE: B1, TS_TEST: T1})
        for status in ("needs-recheck", "persisted"):
            with self.subTest(status=status):
                r = score.run(_review_pass2(settled, [_ts_request(row)],
                                            [reviewer_verdict(agent="bugs")], status=status,
                                            touched={row["stable_hash"]: ["docs/README.md"]}))
                self._open(r, row, [R_IR_SETTLED])
                self.assertIsInstance(_ts_rows(r, row)[0].get("recheck_settled"), dict)

    def test_cr02_relevant_touch_is_a_fresh_start(self):
        """CR-02: the finding's file, a fingerprinted path, or an associated
        test changing since the answer clears the memory."""
        row = _ts_row()
        fp = {TS_FILE: B1, TS_TEST: T1, "src/facade/shared.ts": "5" * 40}
        settled = _settled(row, fp)
        for path in (TS_FILE, TS_TEST, "src/facade/shared.ts",
                     "src/facade/arrFacade.spec.ts"):
            with self.subTest(path=path):
                r = score.run(_review_pass2(settled, [_ts_request(row)],
                                            [reviewer_verdict(agent="bugs")],
                                            status="needs-recheck",
                                            touched={row["stable_hash"]: [path]}))
                self.assertEqual(_rejections(r), [])
                self.assertEqual(len(r.get("resolved", [])), 1)

    def test_wr01_unbound_plain_never_confirmers_rejected(self):
        """WR-01: a plain request without `snapshot_blob` cannot let the fixer
        or Codex close a needs-recheck record either."""
        row = _ts_row()
        for agent in ("fix", "codex-adversarial"):
            with self.subTest(agent=agent):
                req = {"token": "R1", "agents": [agent], "stable_hash": row["stable_hash"],
                       "file": row["file"], "line": row["line"], "agent": row["agent"],
                       "title": row["title"]}
                r = score.run(_review_pass2(row, [req], [reviewer_verdict(agent=agent)],
                                            status="needs-recheck"))
                self.assertNotIn("resolved", r)
                self.assertEqual(len(_ts_rows(r, row)), 1)
                self.assertIn(R_MALFORMED, _rejections(r))
        # The raising lane on the same unbound shape still closes it.
        req = {"token": "R1", "agents": ["test-sufficiency"],
               "stable_hash": row["stable_hash"], "file": row["file"],
               "line": row["line"], "agent": row["agent"], "title": row["title"]}
        r = score.run(_review_pass2(row, [req],
                                    [reviewer_verdict(agent="test-sufficiency")],
                                    status="needs-recheck"))
        self.assertEqual(len(r.get("resolved", [])), 1, _rejections(r))

    def test_wr02_confirmed_fix_refuses_codex_as_confirmer(self):
        """WR-02: the confirmed-fix route refuses `codex-adversarial` as the
        independent reviewer, as 20-dispatch.md says."""
        for agents in (("codex-adversarial",), ("bugs", "codex-adversarial")):
            with self.subTest(agents=agents):
                r = score.run(json.loads(json.dumps(_cf_env(agents))))
                self.assertNotIn("resolved", r)
                self.assertIn(R_MALFORMED, _rejections(r))
        self.assertFalse(score._routed_request_ok(
            {"token": "R1", "agents": ["codex-adversarial"], "stable_hash": "a" * 64,
             "route": "confirmed-fix", "snapshot_blob": "1" * 40}))
        # A native reviewer still confirms.
        r = score.run(json.loads(json.dumps(_cf_env(("bugs",)))))
        self.assertEqual(len(r.get("resolved", [])), 1, _rejections(r))

    def test_wr03_still_applies_on_one_route_blocks_another(self):
        """WR-03: the raising lane's still-applies on a bound plain request
        blocks the independent confirmer's `resolved` for the same lead in the
        same pass (still-applies wins); a persisted lead is not both rejected
        and closed."""
        row = _ts_row()
        plain = {"token": "P1", "agents": ["test-sufficiency"],
                 "stable_hash": row["stable_hash"], "file": row["file"],
                 "line": row["line"], "agent": row["agent"], "title": row["title"],
                 "snapshot_blob": B1}
        verdicts = [reviewer_verdict(token="P1", agent="test-sufficiency",
                                     verdict="still-applies"),
                    reviewer_verdict(token="R1", agent="bugs")]
        for status in ("needs-recheck", "persisted"):
            with self.subTest(status=status):
                r = score.run(_review_pass2(row, [plain, _ts_request(row)], verdicts,
                                            status=status))
                self.assertNotIn("resolved", r)
                self.assertEqual(len(_ts_rows(r, row)), 1)
                self.assertIn(R_CONTRADICTED, _rejections(r))

    def test_wr04_non_str_file_does_not_crash(self):
        """WR-04 (HARDEN-01): a carried record whose `file` is not a string is
        scored, never a crash. With a blob-bound request it has no blob match
        and stays open; on the unbound plain needs-recheck shape it resolves
        exactly as the pre-phase scorer (8df9545) did."""
        row = _ts_row()
        for bad in (["a"], {"x": 1}):
            with self.subTest(file=bad, shape="independent"):
                env = _review_pass2(row, [_ts_request(row)],
                                    [reviewer_verdict(agent="bugs")])
                env["carryforward"][0]["file"] = bad
                env["recheck_requests"][0]["file"] = bad
                r = score.run(json.loads(json.dumps(env)))
                self.assertNotIn("resolved", r)
            with self.subTest(file=bad, shape="unbound plain"):
                env = _review_pass2(row, [], [], status="needs-recheck")
                del env["head_blobs"], env["touched_paths"]
                env["carryforward"][0]["file"] = bad
                env["recheck_requests"] = [
                    {"token": "R1", "agents": ["test-sufficiency"], "stable_hash": None,
                     "file": bad, "line": 80, "agent": "test-sufficiency",
                     "title": row["title"]}]
                env["verdicts"] = [reviewer_verdict(agent="test-sufficiency")]
                r = score.run(json.loads(json.dumps(env)))
                self.assertEqual(len(r.get("resolved", [])), 1)


SKIP_RELEVANT = ("no path in its `$TOUCHED_PATHS` list is its `file`, a path in its "
                 "`fingerprint`, or a test of its file")
SKIP_ANY_TOUCH = "AND its `$TOUCHED_PATHS` list is empty"


def dispatch_skip_rule_holds(text):
    """CR-02: the dispatch skip rule mirrors the scorer's fresh-start filter."""
    return SKIP_RELEVANT in text and SKIP_ANY_TOUCH not in text


APPLIED_WHILE_OPEN = ("plus every entry whose `verdict` is `applied` AND whose "
                     "`stable_hash` names a finding of `state.passes[-1].findings`")
APPLIED_KEPT_AS_HISTORY = "the entry itself stays in `fix_verdicts` as history"
APPLIED_FALSE_CLAIM = ("it leaves `fix_verdicts` only when its item closes through "
                       "`resolved[]` or the owner decides it")


def state_forwards_applied_while_open_holds(text):
    """WR-05: an applied verdict is forwarded only while its item is open (no
    stray `verdict: record not carried`), and the prose no longer claims
    something removes it from the root."""
    return (APPLIED_WHILE_OPEN in text and APPLIED_KEPT_AS_HISTORY in text
            and APPLIED_FALSE_CLAIM not in text)


class TestReviewFix56Prose(unittest.TestCase):
    def _read(self, rel):
        from test_confirmed_fix import _read
        return _read(rel)

    def test_cr02_dispatch_skip_rule_matches_scorer(self):
        text = self._read("phases/review/20-dispatch.md")
        self.assertTrue(dispatch_skip_rule_holds(text))
        self.assertFalse(dispatch_skip_rule_holds(text.replace(SKIP_RELEVANT, "")))
        self.assertFalse(dispatch_skip_rule_holds(text + SKIP_ANY_TOUCH))

    def test_wr05_applied_forwarded_only_while_open(self):
        text = self._read("phases/review/05-state.md")
        self.assertTrue(state_forwards_applied_while_open_holds(text))
        for needle in (APPLIED_WHILE_OPEN, APPLIED_KEPT_AS_HISTORY):
            with self.subTest(mutant=needle):
                self.assertFalse(state_forwards_applied_while_open_holds(
                    text.replace(needle, "")))
        self.assertFalse(state_forwards_applied_while_open_holds(
            text + APPLIED_FALSE_CLAIM))

    def test_wr05_orphan_applied_verdict_is_what_the_filter_prevents(self):
        """Why the filter matters: an applied verdict whose item already
        closed, if forwarded, is reported on every pass as not carried."""
        import test_confirmed_fix as tcf
        from test_score import _nv_env
        r = score.run(json.loads(json.dumps(_nv_env(
            [], carryforward=[], pass_number=3, head_sha=tcf.HEAD3,
            verdicts=[tcf.confirmed_verdict("a" * 64)]))))
        self.assertIn("verdict: record not carried", _rejections(r))


# --------------------------------------------------------------------------- #
# Mutation checks: each new guard trips when removed
# --------------------------------------------------------------------------- #
class TestIndependentRouteMutants(unittest.TestCase):
    """Each mutant removes one guard of the independent route; the real scorer
    keeps the record open (or behaves as specified) and the mutant does not."""

    @classmethod
    def setUpClass(cls):
        from test_confirmed_fix import SCORE_PY
        with open(SCORE_PY, "r", encoding="utf-8") as fh:
            cls.src = fh.read()

    def _mod(self, name, old, new):
        from test_confirmed_fix import SCORE_PY, _mutant
        # Each target names exactly one guard.
        self.assertEqual(self.src.count(old), 1, "mutation target not unique: %r" % old)
        return _mutant(SCORE_PY, name, old, new)

    def _trips(self, name, old, new, env):
        self.assertNotIn("resolved", score.run(json.loads(json.dumps(env))))
        mod = self._mod(name, old, new)
        self.assertIn("resolved", mod.run(json.loads(json.dumps(env))))

    def _blocks(self, name, old, new, env):
        """The inverse: the real scorer closes it, the mutant keeps it open."""
        self.assertIn("resolved", score.run(json.loads(json.dumps(env))))
        mod = self._mod(name, old, new)
        self.assertNotIn("resolved", mod.run(json.loads(json.dumps(env))))

    def test_m10_independent_blob_binding_removed(self):
        row = _ts_row()
        env = _review_pass2(row, [_ts_request(row, snapshot=B1)],
                            [reviewer_verdict(agent="bugs")],
                            head_blobs={TS_FILE: B2, TS_TEST: T1})
        self._trips("score_m10",
                    'requests_by_token[v["token"]]["snapshot_blob"] != head_blob'
                    ' for v in independent',
                    "False for v in independent", env)

    def test_m11_independent_never_confirmers_removed(self):
        row = _ts_row()
        env = _review_pass2(row, [_ts_request(row, agents=("codex-adversarial",))],
                            [reviewer_verdict(agent="codex-adversarial")],
                            status="needs-recheck", touched={})
        self._trips("score_m11",
                    'not any(a in _NEVER_CONFIRMERS for a in req["agents"])\n',
                    "True\n", env)

    def test_m12_independent_trigger_removed(self):
        env = _pass4_envelope(tokens=["R4"], touched_paths=_touched(p22d360d9=[]))
        self._trips("score_m12",
                    'status == "persisted" and not _independent_trigger(',
                    "False and not _independent_trigger(", env)

    def test_m13_independent_still_applies_removed(self):
        row = _ts_row()
        env = _review_pass2(
            row, [_ts_request(row, agents=("bugs", "security"))],
            [reviewer_verdict(agent="bugs"),
             reviewer_verdict(agent="security", verdict="still-applies")])
        self._trips("score_m13",
                    'if any(v["verdict"] == "still-applies" for v in independent):',
                    "if False:", env)

    def test_m14_independent_settled_removed(self):
        row = _ts_row()
        settled = _settled(row, {TS_FILE: B1, TS_TEST: T1})
        env = _review_pass2(settled, [_ts_request(row)], [reviewer_verdict(agent="bugs")],
                            status="needs-recheck", touched={})
        self._trips("score_m14",
                    'if isinstance(record.get("recheck_settled"), dict):\n'
                    "        return None, _R_IR_SETTLED",
                    "if False:\n        return None, _R_IR_SETTLED", env)

    def test_m15_bound_plain_blob_binding_removed(self):
        reqs = {"R5": _plain_request(_member("0249b52c", "bugs"), "R5", "bugs",
                                     snapshot="0" * 40)}
        env = _pass4_envelope(requests=reqs)
        self._trips("score_m15",
                    'requests_by_token[v["token"]]["snapshot_blob"] != head_blob for v in plain',
                    "False for v in plain", env)

    def test_m16_bound_plain_trigger_removed(self):
        env = _pass4_envelope(tokens=["R7"], touched_paths=_touched(p2a01829c=[]))
        self._trips("score_m16",
                    'if not _independent_trigger(record, facts["touched"],'
                    ' facts["changed_line_ranges"]):',
                    "if False:", env)

    def test_m17_new_finding_scrub_removed(self):
        f = make_finding(file="src/z.py", line=5, current_code="  y = 2")
        f["recheck_settled"] = {"verdict": "still-applies", "at_pass": 1,
                                "head_sha": None, "fingerprint": {"src/z.py": B1}}
        env = {"command": "review", "all_mode": False, "pass_number": 1,
               "changed_line_ranges": {"src/z.py": [[1, 9]]}, "findings": [f]}

        def survives(mod):
            rows = [x for x in mod.run(json.loads(json.dumps(env)))["findings"]
                    if x["file"] == "src/z.py"]
            return "recheck_settled" in rows[0]

        self.assertFalse(survives(score))
        mod = self._mod("score_m17",
                        '"resolution", "kept_open",\n'
                        '                              "recheck_settled")',
                        '"resolution", "kept_open")')
        self.assertTrue(survives(mod))

    def test_m18_fresh_start_drop_removed(self):
        row = _ts_row()
        settled = _settled(row, {TS_FILE: B1, TS_TEST: T1})
        env = _review_pass2(settled, [_ts_request(row, snapshot=B2)],
                            [reviewer_verdict(agent="bugs")], status="needs-recheck",
                            touched={}, head_blobs={TS_FILE: B2, TS_TEST: T1})
        self._blocks("score_m18", '                del rep["recheck_settled"]',
                     "                pass", env)

    def test_m19_bound_plain_never_confirmers_removed(self):
        row = _ts_row()
        req = _ts_request(row, agents=("codex-adversarial",))
        del req["route"], req["test_paths"]
        env = _review_pass2(row, [req], [reviewer_verdict(agent="codex-adversarial")],
                            status="needs-recheck", touched={})
        self._trips("score_m19",
                    'not any(a in _NEVER_CONFIRMERS for a in req["agents"]))',
                    "True)", env)

    def test_m20_fresh_start_on_touch_removed(self):
        row = _ts_row()
        settled = _settled(row, {TS_FILE: B1, TS_TEST: T1})
        env = _review_pass2(settled, [_ts_request(row)], [reviewer_verdict(agent="bugs")],
                            touched={row["stable_hash"]: [TS_TEST]})
        # CR-02 renamed the term: only a relevant touched path is a fresh start.
        self._blocks("score_m20", "                    or relevant):",
                     "                    or False):", env)

    def test_m21_no_reviewer_reason_gate_removed(self):
        row = _ts_row()
        env = _review_pass2(row, [], [])
        del env["head_blobs"]
        self.assertEqual(_rejections(score.run(json.loads(json.dumps(env)))), [])
        mod = self._mod("score_m21", 'if "head_blobs" in envelope:', "if True:")
        self.assertEqual(_rejections(mod.run(json.loads(json.dumps(env)))),
                         [R_IR_NO_REVIEWER])

    def test_m22_confirmed_fix_settled_removed(self):
        import test_confirmed_fix as tcf
        from test_score import _nv, _nv_cf, _nv_env, _nv_rows
        p1 = _nv_rows(score.run(_nv_env([_nv(agent="codex-adversarial")])))[0]
        carried = _nv_cf(tcf.settled_row(p1, {p1["file"]: tcf.BLOB}), None, None)
        env = _nv_env([], carryforward=[carried], pass_number=3, head_sha=tcf.HEAD3,
                      recheck_requests=[tcf.routed_request(p1)],
                      verdicts=[tcf.confirmed_verdict(p1["stable_hash"], at_pass=2),
                                reviewer_verdict()],
                      head_blobs={p1["file"]: tcf.BLOB}, touched_paths={})
        r = score.run(json.loads(json.dumps(env)))
        self.assertIn(R_CF_SETTLED, _rejections(r))
        self._trips("score_m22",
                    'if isinstance(record.get("recheck_settled"), dict):\n'
                    "                rejected.append((v, _R_CF_SETTLED))",
                    "if False:\n                rejected.append((v, _R_CF_SETTLED))", env)

    def test_m23_settled_memory_not_written(self):
        row = _ts_row()
        env = _review_pass2(row, [_ts_request(row)],
                            [reviewer_verdict(agent="bugs", verdict="still-applies")])

        def settled(mod):
            return _ts_rows(mod.run(json.loads(json.dumps(env))), row)[0].get(
                "recheck_settled")

        self.assertIsInstance(settled(score), dict)
        mod = self._mod("score_m23", 'record["recheck_settled"] = {', "_unused = {")
        self.assertIsNone(settled(mod))

    def test_m24_kept_open_memory_copy_removed(self):
        """CR-01: without the copy, the kept-open row loses the memory and the
        next run's stray `resolved` closes it on unchanged code."""
        row = _ts_row()
        mod = self._mod("score_m24",
                        '        if isinstance(m.get("recheck_settled"), dict):\n'
                        '            row["recheck_settled"] = m["recheck_settled"]\n',
                        "")
        env2 = _review_pass2(row, [_ts_request(row)],
                             [reviewer_verdict(agent="bugs", verdict="still-applies")],
                             status="needs-recheck", touched={})

        def pass3(m):
            carried = _ts_rows(m.run(json.loads(json.dumps(env2))), row)[0]
            return _pass3(carried, [_ts_request(carried, token="R9")],
                          [reviewer_verdict(token="R9", agent="bugs")], "needs-recheck", {})

        self.assertNotIn("resolved", score.run(pass3(score)))
        self.assertIn("resolved", mod.run(pass3(mod)))

    def test_m25_kept_open_memory_pop_removed(self):
        """CR-01: without the pop, a memory the fresh-start rule cleared is
        resurrected from the carried copy."""
        row = _ts_row()
        settled = _settled(row, {TS_FILE: B1, TS_TEST: T1})
        env = _review_pass2(settled, [], [], status="needs-recheck", touched={},
                            head_blobs={TS_FILE: B2, TS_TEST: T1})
        mod = self._mod("score_m25", '        row.pop("recheck_settled", None)\n', "")
        self.assertNotIn("recheck_settled", _ts_rows(score.run(json.loads(json.dumps(env))),
                                                      row)[0])
        self.assertIn("recheck_settled", _ts_rows(mod.run(json.loads(json.dumps(env))),
                                                   row)[0])

    def test_m26_fresh_start_relevance_filter_removed(self):
        """CR-02: without the filter, a commit to an unrelated path clears the
        memory and a stray `resolved` closes the finding on unchanged code."""
        row = _ts_row()
        settled = _settled(row, {TS_FILE: B1, TS_TEST: T1})
        env = _review_pass2(settled, [_ts_request(row)], [reviewer_verdict(agent="bugs")],
                            status="needs-recheck",
                            touched={row["stable_hash"]: ["docs/README.md"]})
        self._trips("score_m26",
                    "relevant = [p for p in touched if _settled_path(",
                    "relevant = [p for p in touched if True or _settled_path(", env)

    def test_m27_unbound_plain_never_confirmers_removed(self):
        """WR-01: without the check, the fixer closes a needs-recheck record on
        an unbound plain request."""
        row = _ts_row()
        req = {"token": "R1", "agents": ["fix"], "stable_hash": row["stable_hash"],
               "file": row["file"], "line": row["line"], "agent": row["agent"],
               "title": row["title"]}
        env = _review_pass2(row, [req], [reviewer_verdict(agent="fix")],
                            status="needs-recheck")
        self._trips("score_m27",
                    'return all(a not in _NEVER_CONFIRMERS for a in req["agents"])',
                    "return True", env)

    def test_m28_confirmed_fix_codex_exclusion_removed(self):
        """WR-02: without the term, Codex confirms a fix on the confirmed-fix
        route."""
        env = _cf_env(("codex-adversarial",))
        self._trips("score_m28",
                    'and all(a not in _NEVER_CONFIRMERS - _FIXER_AGENTS for a in req["agents"]))',
                    "and True)", env)

    def test_m29_cross_route_still_applies_removed(self):
        """WR-03: without the cross-route check, the independent confirmer's
        `resolved` closes a lead the raising lane said still applies."""
        row = _ts_row()
        plain = {"token": "P1", "agents": ["test-sufficiency"],
                 "stable_hash": row["stable_hash"], "file": row["file"],
                 "line": row["line"], "agent": row["agent"], "title": row["title"],
                 "snapshot_blob": B1}
        env = _review_pass2(row, [plain, _ts_request(row)],
                            [reviewer_verdict(token="P1", agent="test-sufficiency",
                                              verdict="still-applies"),
                             reviewer_verdict(token="R1", agent="bugs")],
                            status="needs-recheck")
        self._trips("score_m29",
                    "flag for route, flag in still_on.items() if route != resolved_on):",
                    "False for route, flag in still_on.items()):", env)

    def test_m30_non_str_file_guard_removed(self):
        """WR-04: without the type check, a non-str carried `file` crashes the
        scorer."""
        row = _ts_row()
        env = _review_pass2(row, [_ts_request(row)], [reviewer_verdict(agent="bugs")])
        env["carryforward"][0]["file"] = ["a"]
        env["recheck_requests"][0]["file"] = ["a"]
        self.assertNotIn("resolved", score.run(json.loads(json.dumps(env))))
        mod = self._mod("score_m30",
                        "return head_blobs.get(file) if isinstance(file, str) else None",
                        "return head_blobs.get(file)")
        with self.assertRaises(TypeError):
            mod.run(json.loads(json.dumps(env)))

    def test_stable_hash_and_golden_digest_unchanged(self):
        self.assertEqual(score.stable_hash("a.py", "  x=1", "title"), GOLDEN_DIGEST)
        row = _ts_row()
        r = score.run(_review_pass2(row, [_ts_request(row)],
                                    [reviewer_verdict(agent="bugs")]))
        self.assertEqual(r["resolved"][0]["stable_hash"], row["stable_hash"])


if __name__ == "__main__":
    unittest.main()
