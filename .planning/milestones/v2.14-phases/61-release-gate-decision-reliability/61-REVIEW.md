---
phase: 61-release-gate-decision-reliability
reviewed: 2026-10-30T22:30:35Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - README.md
  - plugins/vibe-check/.claude-plugin/plugin.json
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 61: Code Review Report

**Reviewed:** 2026-10-30T22:30:35Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Scope: release-candidate commit `0d2be77` (diff base `f4bba0a`). It bumps `plugin.json` to 2.14.0 and rewrites the README release section. I checked it against 61-CANDIDATE.md (fact-check table), 61-RELEASE-RECORD.md, 61-LIVE-SMOKE.md, 61-SIGNOFF.md, 61-RELEASE-NOTES.md and ROADMAP backlog 999.23–999.28.

**Version consistency is clean.** `plugins/vibe-check/.claude-plugin/plugin.json` is valid JSON and is the only version pin in the tracked tree. There is no tracked marketplace manifest or CHANGELOG. The only other `"version"` string is a test fixture (`test_batchsnap.py:136`, `2.10.0`), which is unrelated. The external marketplace (`thejuran/marketplace`, `.claude-plugin/marketplace.json`) points vibe-check at `ref: main` and has no plugin version field, so nothing else needs bumping. The test count (3,821) matches gate G1. Every in-page anchor (`#-quick-start`, `#%EF%B8%8F-configuration`, `#-features`, `#-example-output`, `#%EF%B8%8F-limitations`, `#-vibe-check`) resolves to an existing heading, and the commit added no new links.

**The new claims mostly match the records,** each with evidence in 61-CANDIDATE.md. The problems:

- **WR-01:** One README claim was overtaken by the live smoke. Line 33 says nearness is measured only from added/removed lines on the default route. The live smoke (C1, backlog 999.28) showed that on the default route, uncommitted code counts as changed on every pass.
- **WR-02:** The release relabel left a stale "this release" pointer inside the v2.12 block.

Convention rule packs: skipped. There is no JS/TS pack for `.md`/`.json`.

## Warnings

### WR-01: README line 33 says the default route uses the exact five-line window; the live smoke showed it does not for uncommitted code

**File:** `README.md:33` (also `README.md:38`, the v2.13 "Your decisions stick … when you edit unrelated code" bullet)

**Issue:** Line 33 says nearness "is now measured only from lines that were actually added or removed … This applies on the default, GSD, range, PR and incremental review routes." The live smoke on candidate C reproduced C1 (61-LIVE-SMOKE.md S1; RELEASE-RECORD Carried C1; ROADMAP 999.28). On the default review of uncommitted code, the ranges on pass ≥ 2 come from `git diff <last-reviewed-sha>`, and that SHA is still HEAD. So the whole uncommitted block counts as changed on every pass. A deferred or dismissed finding is then re-asked on a byte-identical tree, with a false "code next to it changed" reason. For a README reader on the most common route, this is the opposite of what line 33 (and the v2.13 bullet on line 38) promise.

The owner already ruled on C1 (61-SIGNOFF.md Decision 1 = A: list C1 in the release notes only, leave the README unchanged). That option was framed as "the README stays silent on it." The README is not silent, though: line 33 makes a positive claim that C1 contradicts. This finding records that gap, which the ruling did not weigh. The release notes themselves say "the first limit above is listed only in these notes." Effect: extra questions and a false reason on the card. No findings are lost, so this is a WARNING, not a BLOCKER.

**Fix:** Either accept it explicitly as part of Decision 1, or make a one-clause README edit (this means a new release commit and re-running the gates, as option B on the sign-off page notes):
```markdown
This applies on the default, GSD, range, PR and incremental review routes (`--all` keeps no decisions between runs, so it has no window). Known limit: on the default review of code you have not committed yet, a decided finding is asked again on every pass even when nothing changed (see Limitations).
```
and add the release-notes C1 bullet as the first item under "Known limitations (2.14)".

### WR-02: Stale "Known limitations of this release" pointer now sits in the v2.12 block; the v2.14 block has none

**File:** `README.md:57`

**Issue:** The relabel renamed v2.12 to "(earlier release)" (line 42) and v2.13 to "(previous release)" (line 36). The sentence "Known limitations of this release are listed under [Limitations](#%EF%B8%8F-limitations)." is still at the end of the v2.12 block. Read in place, it now points readers to "this release" from inside the 2.12 entry, and the v2.14 "(this release)" block (lines 30–34) has no pointer to the 2.14 Known limitations at all.

**Fix:** Move the sentence to the end of the v2.14 block (after line 34), or reword it in place to "Known limitations of the current release are listed under [Limitations](#%EF%B8%8F-limitations)."

## Info

### IN-01: v2.11 still labeled "previous release"

**File:** `README.md:59`

**Issue:** `**v2.11 (previous release — last measured).**` now sits below both v2.13 "(previous release)" and v2.12 "(earlier release)". There are two "previous release" labels, and the v2.11 one is wrong. The candidate's relabel row (61-CANDIDATE.md "Relabels") covered v2.13 and v2.12 only. (This label was already stale at 2.13, so it predates this commit.)

**Fix:** `**v2.11 (earlier release — last measured).**`

### IN-02: README understates the PR fetch check and differs from the release notes

**File:** `README.md:357`

**Issue:** The bullet says the other routes "are covered by tests only, and the PR diff fetch is tested on a saved real PR diff." Gate G6 (61-RELEASE-RECORD.md §Live PR fetch) later checked the live `gh pr diff` fetch on PR #6 and PR #4, byte-identical. The release notes say "the PR diff fetch was checked once against real PRs." This is accurate as of commit C, and it errs toward under-claiming, but the README and the release notes now say different things.

**Fix:** Optional, and only if the README is touched again for WR-01: "…and the PR diff fetch was checked once against real PRs."

### IN-03: 2.13→2.12 downgrade note dropped

**File:** `README.md:350-358`

**Issue:** The 2.13 bullet "Downgrading from 2.13 to 2.12 has not been tested…" was replaced by the 2.14→2.13 bullet. Users on 2.13 who want to step back to 2.12 lose that caveat. The 2.12→2.11 note (line 359) is kept, so the chain now skips a step.

**Fix:** Keep both downgrade bullets, or merge them: "Downgrades (2.14→2.13, 2.13→2.12) have not been tested; the older version ignores the newer state fields, so the expected effect is re-asks, not lost data."

## Set aside (needs ruling)

### SA-01: Owner-parked residuals not listed in the README

**Where:** `README.md:350-358`
**Why excluded:** These are owner-parked or owner-deferred backlog items: 999.23 D-02 over-ask (an edit beside a NEW identical copy re-asks), WR-01 (the card names only the other spot), WR-02 (the "still deferred" note drops after one pass), 999.27 (a crafted committed `head_sha` can narrow the pass ≥ 2 range), and live-smoke C4 (the model stopped instead of taking the Rerun after a typed defer). Each one fails toward asking or stopping, or (999.27) needs repo-commit access to exploit.
**Effect if left as is:** The README does not mention them. Users may see an extra question, a card naming a different line than expected, or have to say "continue" once. The 999.27 range narrowing is silent to the owner.
**Needs:** Ruling: accept (current state) or add a short README line for 999.27 in particular, since it is the one silent effect.

### SA-02: Marketplace description diverges from plugin.json

**Where:** `thejuran/marketplace` `.claude-plugin/marketplace.json` (external repo) vs `plugins/vibe-check/.claude-plugin/plugin.json:3`
**Why excluded:** It is in a separate repo, outside this commit's file scope, and predates this commit. Versions are not affected (the marketplace pins `ref: main`, with no version).
**Effect if left as is:** The marketplace listing says "AI-powered parallel code review for your uncommitted changes." This undersells the GSD, range, PR and `--all` routes that plugin.json and the README describe.
**Needs:** Ruling: defer / accept.

---

_Reviewed: 2026-10-30T22:30:35Z_
_Reviewer: Claude (bm-code-reviewer)_
_Depth: standard_
