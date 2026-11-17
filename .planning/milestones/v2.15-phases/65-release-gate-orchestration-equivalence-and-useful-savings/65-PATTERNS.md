# Phase 65: Release gate — orchestration equivalence and useful savings - Pattern Map

**Mapped:** 2026-11-15
**Files analyzed:** 13 (10 planning records/version files always; 3 conditional code/test touches if D-07 qualifies)
**Analogs found:** 13 / 13

Path shorthand used below:
- `P61/` = `.planning/milestones/v2.14-phases/61-release-gate-decision-reliability/`
- `P63/` = `.planning/phases/63-finalize-extraction-and-cross-call-variable-check/`
- `P65/` = `.planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/`
- `VC/` = `plugins/vibe-check/`

`.planning/` is gitignored: commit records with `bm-sdk query commit`, falling back to `git add -f` if it refuses.

## File Classification

| New/Modified File | Plan | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|---|
| `P65/65-REPRO-WR02.md` | 65-01 | record (repro) | batch (fresh-shell fence walk) | `P63/63-REPRO.md` (Repro standard + "Review fixes" C1 section) | exact |
| `P65/65-LIVE-SMOKE-PROPOSAL.md` | 65-02 | record (approval gate) | request-response (owner ruling) | `P61/61-LIVE-SMOKE-PROPOSAL.md` | exact |
| `VC/.claude-plugin/plugin.json` | 65-03 | config | — | itself, line 4 | exact |
| `README.md` | 65-03 | docs (release block + limits) | — | `README.md` lines 30–33 (v2.14.1 block), 355–362 (Known limitations (2.14.1)) | exact |
| `P65/65-CANDIDATE.md` | 65-03 | record (candidate pin) | — | `P61/61-CANDIDATE.md` lines 1–6 + README fact-check | exact |
| `P65/65-RELEASE-RECORD.md` | 65-04 | record (gate ledger) | batch | `P61/61-RELEASE-RECORD.md` | exact |
| `P65/65-LIVE-SMOKE.md` | 65-05 | record (live evidence) | event-driven (tmux sessions) | `P61/61-LIVE-SMOKE.md` | exact (pass strings differ) |
| `P65/65-RELEASE-NOTES.md` | 65-06 | docs (GH release body) | — | `P61/61-RELEASE-NOTES.md` | exact (add size block) |
| `P65/65-CLOSE-RUNBOOK.md` | 65-06 | runbook | batch (ordered fences) | `P61/61-CLOSE-RUNBOOK.md` | exact (substitute v2.15) |
| `P65/65-SIGNOFF.md` | 65-06 | record (owner go/no-go) | request-response | `P61/61-SIGNOFF.md` | exact |
| *(conditional)* `VC/phases/review/00-scope.md` (print `PHASE_ID=`) | fix round | instruction fence | transform | same file's `printf 'PHASE_START=%s\n'` line ~120; `05-state.md` print lines 12–13 | role-match |
| *(conditional)* `VC/phases/review/05-state.md` (refuse empty `PHASE_ID`) | fix round | instruction fence | transform | `VC/scripts/statepath.py::_resolve_gsd` lines 159–171 + same fence's guard line 11 | exact (rule) |
| *(conditional)* `VC/scripts/test_pasted_name_guard.py` and/or `VC/scripts/test_cross_call_vars.py` | fix round | test (before/after + mutant) | batch | `test_pasted_name_guard.py::TestStateFileGuard` lines 246–339; `test_cross_call_vars.py::TestRepro63` + `REPRO_63`/`TestRepro63Record` | exact |

Also touched at close (no new pattern; follow PLANNING-FORMAT.md): `.planning/STATE.md`, `.planning/ROADMAP.md` (999.38 WR-02 disposition, any new carried items).

## Pattern Assignments

### `65-REPRO-WR02.md` (record, fresh-shell repro) — plan 65-01

**Analog:** `P63/63-REPRO.md` (843 lines; read only the parts below)

**Skeleton to copy:**
- H1 + one bold count line (63-REPRO line 3: `**6 places flagged. 6 reproduced. 0 did not reproduce.**`) → for 65: one line stating reproduced / not reproduced and the class.
- Metadata bullets (lines 18–21): `**Date:**`, `**HEAD when recorded:**`, `**Scope of evidence:**` ("local runs only. No live review, no paid run, no network").
- `## Repro standard` (lines 23–38): Fresh run / Control run / Outcome class (`stop`, `wrong-file`, `ignored-setting`, `harmless`) / Reproduced = any class but harmless. Reuse verbatim and add the Phase 60 env rule from RESEARCH §D-07 (`env -i` with only `PATH`, `VC_ROOT`, `TMPDIR`, printed `STATE_FILE` substituted only where the file says).
- `## Known limits` (lines 40–44).
- Per-item section modelled on "### C1 — phases/review/05-state-all.md: STATE_FILE" (lines 508–513): **Reproduction** (fixture, RED commit, exact printed output and `next` value), **Fix** (or "none — carried"), **After the fix**, **Defence in depth, not changed**.

**Status markers the gate greps:**
- `grep -q '^Verdict: ' 65-REPRO-WR02.md` (RESEARCH validation map). **Difference:** 63-REPRO writes `**Verdict:** REPRODUCED at \`c7d92c9\` → …` (line 49) — that does NOT match `^Verdict: `. 65 must write a bare line, e.g. `Verdict: NOT QUALIFYING — carried (class: …)` or `Verdict: QUALIFYING — <class> — owner D-08 go required`.

**Phase 65 additions (not in the analog):**
- Two runs, not one: candidate (HEAD) and like-for-like 2.14.1 (`git show v2.14.1:VC/phases/review/05-state.md`), so the "not a regression from 2.14.1" claim in 999.38 is tested, not assumed (RESEARCH A3).
- The two-phase chain: temp repo with `.planning/phases/01-a` and `02-b`; record whether phase B's Finalize-inputs fence (`VC/phases/shared/90-finalize.md` lines 14–29) returns `write-review-md` on A's state (wrong close) or a pass-2 overwrite (data loss).
- Realism caveat section: `test_cross_call_vars.py:1236` types `${PHASE_ID}` → `02-code-review`; the fence-as-written walk is the worst case.
- Four-class classification line + D-08/D-09 routing (qualifying → stop with owner checkpoint; else carried, known limit only if user-visible).
- Repro script lives in the scratchpad (Wave 0), enters the suite only with a fix + mutant.

---

### `65-LIVE-SMOKE-PROPOSAL.md` (owner approval gate) — plan 65-02

**Analog:** `P61/61-LIVE-SMOKE-PROPOSAL.md` (84 lines)

**Headings (copy in order):** `# Proposal: …` (title gets `(APPROVED)`/`(DECLINED)` after ruling) · `Status:` line · `## Why` · `## Scope` · `## Method` · `## Estimated cost` · `## Stop rules` · `## What this does NOT trigger` · `## If declined` · `## Owner ruling`.

**Status line (line 3), the gate's grep target:**
```
Status: APPROVED (owner, 2026-10-30)
```
Gate: `grep -q '^Status: APPROVED (owner, ' 65-LIVE-SMOKE-PROPOSAL.md` before any session. Before ruling write `Status: PROPOSED` (or similar non-matching value).

**Owner ruling block (lines 75–84):** `**Ruling:**`, `**Channel:**` (AskUserQuestion in main session, not relayed), `**Question asked:**`, `**Selection, verbatim:**`, `**Description shown with the selection, verbatim:**`, `**Conditions:**`, closing "authorizes … and nothing else" sentence.

**Stop rules (lines 58–62):** invalid run → one retry; qualifying failure → stop → the one fix round (cite 65 D-08/D-09, not 61 D-05/D-06); anything else → carry (D-10).

**Differences for 65:** candidate placeholder until 65-03 exists (proposal does not need C; say "runs on the candidate recorded in 65-CANDIDATE.md"); sessions = S1 review+defer, S2 `--finalize`, S3 card-first close (RESEARCH §Live smoke); cost $20–30 estimate not cap, basis `54-BUDGET.md`; A1 assumption restated; "does NOT trigger" lists GSD, range, PR, incremental, `--all`, fix loop (D-02).

---

### `VC/.claude-plugin/plugin.json` (config) — plan 65-03

Line 4: `"version": "2.14.1",` → `"version": "2.15.0",`. Only version field. Do **not** touch `2.14.1` mentions in `VC/scripts/finalize_inputs.py` or `fixtures/finalize_step1_2141.sh` (they describe 2.14.1 behaviour).

---

### `README.md` (release block) — plan 65-03

**Analog:** README lines 30–33 (v2.14.1 entry) and 355–362 (`- ⚠️ **Known limitations (2.14.1):**`).

Pattern of the entry header (line 30):
```
**v2.14.1 (this release) — unchanged decisions are no longer asked again. Not measured.** … (3,886 passing at release).
```
Edits: new `**v2.15.0 (this release) — … Not measured.**` paragraph above line 30; strip `(this release)` from the v2.14.1 header; bullets = D-11 user-visible differences (items 1, 2, 4, 6, 7 of RESEARCH §Accepted differences); a short "What changed in size" line (bytes and steps, both sides, per-path range +0.41–0.63% / +2 steps — RESEARCH Pitfall 9); a new `- ⚠️ **Known limitations (2.15.0):**` group above line 355 (3–6 bullets, include "only default review + Close out run live" or the waiver wording). Test count = G1a form (`pytest` inside `VC/scripts`), command named.

README-coupled tests to run on the edited tree before committing C: `test_recovery_pairs.py`, `test_gitguard.py` (61 Pitfall 1).

---

### `65-CANDIDATE.md` (candidate pin) — plan 65-03

**Analog:** `P61/61-CANDIDATE.md` lines 1–6:
```
# Phase 61 release candidate
candidate: 47978aad41eccc13c594820a8ab8386904439f31
parent: 072bab8b3e5bc1fd8c76fab1a42c12e0fd1d0c32
version: 2.14.0
suite_on_edited_tree: 3821 passed, 0 failed
supersedes: 0d2be7790577ea6d89e7eb563008e9ba8c5d7c6d
```
Grep target used by every fence: `sed -n 's/^candidate: //p'` + `[[ "$C" =~ ^[0-9a-f]{40}$ ]]` (full 40-hex, no backticks, line-start). Keep `supersedes:` only if a fix round replaces C.

Body sections: `## C (current candidate, <C7>)` with the `git show --stat` proof that only `plugin.json` + `README.md` changed, the README-coupled test run and full suite on the edited tree (61-CANDIDATE lines 10–16 wording), then `## README fact-check` table (61 line 40). **65 addition:** assert `git diff --name-only <branch-point> "$C" -- plugins` lists only `VC/.claude-plugin/plugin.json` (RESEARCH A5) — unless D-07 opened the fix round.

---

### `65-RELEASE-RECORD.md` (gate ledger) — plan 65-04

**Analog:** `P61/61-RELEASE-RECORD.md` (171 lines)

**Headings (61):** `# Phase 61 release record — vibe-check 2.14.0` · intro + `**Code under consideration:**` · `## Gate results — C2 (47978aa), <date>` · `## Raw output` · `## Live PR fetch (D-03)` · `## Dependencies and Dependabot (D-10)` · `## Route and recovery coverage (D-11)` · `## Live smoke (D-01/D-02)` · `## Unsupported fixtures and stated limits` · `## Residuals (linked)` · `## Carried (D-07)` · `## Validation gaps and waivers` · `## Publish status`.

**Gate table shape (61 lines 13–25):**
```
| # | Gate | Requirement | Result on C2 | Verdict |
| G1 | Full offline suite | GATE-01 | `3821 passed, …` | PASS |
```
Precondition paragraph above the table (61 line 11): HEAD = C, `git diff --quiet C HEAD -- . ':(exclude).planning'`, clean porcelain.

**Waiver line form (61 lines 163–168)** — grep-able: `… — waiver: granted (owner, 2026-10-30)`.

**Carried item form (61 lines 150–157):** bold id + title, mechanism, user impact, four-class verdict, `**Reopens if:**`, `**Backlog:**`.

**Differences for 65:**
- Rows G1a, G1b, G2–G12 per RESEARCH §Gate Commands (requirements GATE-04/05/06). Drop 61's "Live PR fetch" section; replace with one line: `diff_ranges.py` unchanged since 2.14.1, 2.14.0 live check stands.
- New sections: `## Counts (direct recount, D-06)` with the six-path table (dd8e4ab vs C, bytes and steps) and the per-file `## D-09 reconciliation` table (RESEARCH lines 282–305); `## Fingerprints and frozen files` (10 of 10, GOLDEN_DIGEST `7a516d01…3124`, G10); `## Accepted differences` (7-item list, RESEARCH §Accepted differences) vs observed `differs` lines from G5b; `## D-07 outcome` linking `65-REPRO-WR02.md`.
- Suite equivalence = 0 failed / 0 errors / 0 skipped; state pass-count change vs 3,886 and why (Pitfall 10).
- Residuals link to `P63/63-RESULT.md`, `63-REVIEW.md`, `63-REVIEW-2.md` and backlog 999.34/999.36/999.38 rather than restating.

---

### `65-LIVE-SMOKE.md` (live evidence) — plan 65-05

**Analog:** `P61/61-LIVE-SMOKE.md` (145 lines)

**Headings:** `# Phase 61 live smoke — …` · `Status: DONE` (line 3) · `Approval:` line (line 5, quotes the proposal status) · `## Setup` (C, SNAP, CACHE, CACHE_BAK, SMOKE, Auto-memory slug) · `## Sessions` with `### S1 — … (tmux \`s61-1\`, session <id>)` · `## Evidence` (E1… lines) · `## Carried (D-07)` · `## Verdict` · `## Cache restored`.

**Grep markers the gate relies on:** `^Status: DONE`, `^## Verdict`, `^## Cache restored`, `BLOBFILE=`, `STATE_FILE=`. Verdict body first line is one of `PASS` / `QUALIFYING FAILURE — <class>` / `INVALID — <reason>` (61 line 116: bare `PASS`).

**Evidence line pattern (61 lines 89–96):**
```
E4 — REVIEW.md: `<sha256>  /Users/julianamacbook/.b3/smoke61-…/.turingmind/REVIEW.md`
E5 — Provenance. … every `plugins/vibe-check/` path is under …/rel61-0d2be77/… S1 106 references … 0 references to /Users/julianamacbook/turingmind-code-review/plugins.
```
Hashes only, never `.jsonl` contents.

**Differences for 65:**
- `GATEFILE=` no longer exists (Phase 63 removed it). Evidence prints `STATE_FILE=` (from 05-state) and `BLOBFILE=` (one, or two if the one rebuild fired), the helper JSON line keys `{"action","reason","next","counts","report"}` and `next` value, `review-closed` exit code, `**State format:** 53`, `state archived as …`, absence of "Finalize stopped — nothing was written or archived".
- Session design S1 review+defer / S2 `--finalize` / S3 card-first (RESEARCH §Live smoke). Names: `rel65-<C7>`, `smoke65-<epoch>`, tmux `s65-N`, `CACHE_BAK=$HOME/.b3/vibe-check-2.14.1.bak-pre-phase65`, CACHE `…/cache/thejuran/vibe-check/2.14.1`.
- Carried section uses 65 D-10 wording; 999.32 Rerun stop is carry, not qualifying.

---

### `65-RELEASE-NOTES.md` (GH release body) — plan 65-06

**Analog:** `P61/61-RELEASE-NOTES.md` (19 lines): one-paragraph lead ("…release. Not measured…"), `Contents:` bullets with bold lead sentence, `Known limits:` bullets, `Full list in the README.`, closing test-count sentence.

**Differences for 65 (D-05, D-11):**
- Lead: "Same behaviour as 2.14.1 except:" then plain-words bullets for the user-visible differences (unsafe-name stop; subfolder Finalize closes correctly; 60-second git limit leaves a finding open; one "Permission denied" line gone; C-locale refusal wording). Must not read as "identical to 2.14.1".
- One `What changed in size` block: Finalize 92 → 85 steps, 136,114 → 130,886 bytes; each review path +0.41–0.63% bytes and +2 counted steps (per-path or range). Labelled bytes/steps.
- Known limits: 3–6 bullets (fix loop and `--all` not run live, D-07 outcome if user-visible, carried 999.38 items users can see).
- Gate grep: `grep -nEi '\$[0-9]|token|cheaper|cost sav|billing' 65-RELEASE-NOTES.md` must find nothing in the size block.

---

### `65-CLOSE-RUNBOOK.md` (ordered publish fences) — plan 65-06

**Analog:** `P61/61-CLOSE-RUNBOOK.md` (213 lines), 10 steps:
`## 1. Verify, audit, complete the milestone (skip its tag)` · `## 2. Freshness assert: nothing shipped changed since C` · `## 3. Dependabot note (no action)` · `## 4. Release PR, owner OK, squash merge` · `## 5. Tree-identity assert: origin/main ships C byte-for-byte` · `## 6. Tag origin/main (never the branch tip)` · `## 7. GitHub release (do not skip — it was missed for v2.13)` · `## 8. Remote verification` · `## 9. Update the installed plugin` · `## 10. Clean up and record`.

**Preamble to copy (61 lines 7–13), substitute paths:**
```bash
CAND=$( { ls .planning/phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md \
          .planning/milestones/v2.15-phases/65-release-gate-orchestration-equivalence-and-useful-savings/65-CANDIDATE.md 2>/dev/null || true; } | head -1)
test -n "$CAND" || { echo "65-CANDIDATE.md NOT FOUND — STOPPING"; exit 1; }
C=$(sed -n 's/^candidate: //p' "$CAND")
[[ "$C" =~ ^[0-9a-f]{40}$ ]] || { echo "CANDIDATE SHA INVALID — STOPPING"; exit 1; }
```
Every fence wrapped `bash -s <<'BASH' … BASH` with `set -euo pipefail` (zsh does not word-split).

**Tree-identity + tag (61 lines 107–133):** loop `for p in plugins/vibe-check README.md; do test "$(git rev-parse "origin/main:$p")" = "$(git rev-parse "$C:$p")" …`; then `git tag -a v2.14 origin/main -m "vibe-check 2.14.0 — decision reliability"` with local-tag-exists refusal and `v2.14^{commit}` = `origin/main` assert.

**Substitutions for 65:** tag `v2.15`, message/title `vibe-check 2.15.0 — lean orchestration` (A2, confirm at sign-off); `gh release create v2.15 --verify-tag --latest --notes-file 65-RELEASE-NOTES.md`; branch `feat/v2.15-phase-65`; step 9 expects installed version 2.15.0 and sha = origin/main (uninstall + reinstall on lag); step 1 entry gate greps `Status: SIGNED OFF` in 65-SIGNOFF.md.

---

### `65-SIGNOFF.md` (owner page) — plan 65-06

**Analog:** `P61/61-SIGNOFF.md` (73 lines)

**Headings:** `# vibe-check 2.14.0 — release sign-off` · `Candidate:` paragraph · `**What ships:**` paragraph · `## Checks (re-run on <C7>)` (3-column table: Check / What it shows / Result, plain words) · `## Live smoke` · `## Decision 1 — …` · `## What users should know` · `## Dependabot` · `## Not proven live — waivers …` · `## Owner sign-off` with `Status: SIGNED OFF (owner, 2026-10-30)` + verbatim selection paragraph.

**Grep markers:** `^Status: SIGNED OFF (owner, ` (runbook step-1 entry gate). RESEARCH also asks for `grep -q 'waiver: granted (owner, ' 65-SIGNOFF.md` — **difference:** in Phase 61 that string lives in the RELEASE-RECORD (lines 163–168), and the SIGNOFF only lists waivers in prose. For 65, put the `— waiver: granted (owner, <date>)` suffix on each waiver bullet in 65-SIGNOFF.md (and mirror in the record) so both greps hold.

**Additional sections for 65 (D-12):** `## The two counts` (Finalize down; review-path named growth incl. +2 steps — owner signs D-04 knowing the step figure); `## Differences seen` (only the accepted ones); `## WR-02 (D-07) outcome`; tag/title confirmation (A2). Dependabot paragraph can be copied nearly verbatim (61 lines 47–49).

---

### Conditional: WR-02 fix site (only if 65-01 qualifies and the owner gives the D-08 go)

**Rule analog — `VC/scripts/statepath.py` lines 159–162:**
```python
def _resolve_gsd(phase_id):
    """review.md:406 — the FULL resolved phase directory name, never a prefix."""
    if not _is_str(phase_id) or phase_id == "":
        return _refuse(REASON_MISSING_COMPONENT)
```
**Fence analog — `VC/phases/review/05-state.md` lines 9–14** (GSD branch): the empty-id refusal goes beside the existing guard line, same shape (one stderr sentence, `exit 1`, no `NAME=` printed):
```bash
case "$LEGACY_STATE_FILE$STATE_FILE" in *[\$\`\"\\$'\n\r']*) echo "Review halted — …; nothing was scored." >&2; exit 1;; esac
printf 'STATE_FILE=%s\n' "$STATE_FILE"
```
e.g. a `[ -n "$PHASE_ID" ] || { echo "Review halted — …" >&2; exit 1; }` line before the binds (63-REVIEW WR-02 fix shape). Print side: `00-scope.md:125` sets `$PHASE_ID` in prose only; add a printed `PHASE_ID=` literal following the `printf 'PHASE_START=%s\n'` pattern at `00-scope.md` ~line 120 and the D-21 guard. Any bytes added become a new named-growth row (file, bytes, steps, commit, reason) and a new candidate C (full G1–G12 re-run).

**Test analog (before/after + mutant) — `VC/scripts/test_pasted_name_guard.py::TestStateFileGuard` (lines 246–339):**
- Setter by needle: `GSD_NEEDLE = 'STATE_FILE=".turingmind/state/format-53/${PHASE_ID}'`, `fence_holding(STATE_REL, needle)`, `${PHASE_ID}` supplied via `env={"PHASE_ID": …}`.
- Add `("empty", "")` as a bad case → `test_bad_names_are_refused_and_nothing_runs` (after).
- Mutant: `unguarded(body)` strips the line holding `GUARD_NEEDLE` (lines 36–40); add a second needle for the empty-id line and a `test_without_the_empty_guard_…` mirroring `test_without_the_guard_the_cases_fail` (lines 333–339) — must print `STATE_FILE=.turingmind/state/format-53/.json` when the refusal is removed.
- Chain-level case (wrong close across two phases) belongs in `VC/scripts/test_cross_call_vars.py::TestRepro63` (setter table `STATE_SETTERS` lines 1235–1238, `run_pair` lines 1161–1173, outcome via `classify`), with a new `REPRO_63` row (list at line 1028) so `TestRepro63Record` (line 1555) locks it. Unit reference for the rule: `VC/scripts/test_statepath.py::TestGsdMode` (line 129).

## Shared Patterns

### Candidate-bound fence preamble
**Source:** `P61/61-CLOSE-RUNBOOK.md` lines 7–13; RESEARCH Pattern 1
**Apply to:** every gate fence in 65-04, the smoke setup in 65-05, every runbook step. Read C from `65-CANDIDATE.md`, assert 40-hex, `HEAD == C`, clean `plugins README.md docs .github`, `|| true` on the dual-path `ls`.

### Owner ruling recording
**Source:** `P61/61-LIVE-SMOKE-PROPOSAL.md` lines 75–84; `P61/61-SIGNOFF.md` lines 61–65
**Apply to:** proposal, D-08 fix-round go (if any), waivers, sign-off. `Status: <WORD> (owner, <date>)` at line start; channel = AskUserQuestion in the main session; verbatim selection quoted; "approval means proceed, not code review".

### Four-class carry entry
**Source:** `P61/61-RELEASE-RECORD.md` lines 148–157
**Apply to:** 65-REPRO-WR02 verdict, 65-LIVE-SMOKE Carried, 65-RELEASE-RECORD Carried. Each: what, mechanism, user impact, class verdict, `**Reopens if:**`, backlog id.

### Direct recount, never copy a figure
**Source:** RESEARCH §Counts fence / §Fingerprint fence (Phase 63 D-13)
**Apply to:** 65-RELEASE-RECORD counts, 65-SIGNOFF counts, README/notes size block (figures must trace to the G6 output on C).

### Hash-only evidence
**Source:** `P61/61-LIVE-SMOKE.md` E4/E5 (lines 89–96)
**Apply to:** 65-LIVE-SMOKE. sha256 of transcripts and REVIEW.md; paths only for printed lines; `git ls-files '*.jsonl'` empty.

## Conventions

Convention derivation skipped (`no-app-files`) for `plugins/vibe-check/scripts` — the tool found no app files to vote on. Match local style: Python test files are `unittest.TestCase` classes run by bare `pytest -p no:cacheprovider`; instruction fences print `NAME=%s` literals and refuse with one "Review halted — …" stderr line. The CJS<->SDK dual-resolver contested split does not apply to this repo.

## No Analog Found

None. Every output has a Phase 61 or Phase 63 analog. The only new content without precedent is the `What changed in size` block (notes/README) and the D-09 reconciliation table (record); their figures and layout come from RESEARCH §Counts today and are reproduced by the G6 fence.

## Metadata

**Analog search scope:** `P61/` (all release artifacts), `P63/63-REPRO.md`, `README.md`, `VC/.claude-plugin/plugin.json`, `VC/phases/review/{00-scope,05-state}.md`, `VC/scripts/{statepath.py,test_pasted_name_guard.py,test_cross_call_vars.py,test_statepath.py}`
**Files scanned:** 14
**Pattern extraction date:** 2026-11-15
