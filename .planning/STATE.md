---
gsd_state_version: 1.0
milestone: v2.10
milestone_name: Opus 5 rebuild + quiet down
current_plan: 6
status: executing
stopped_at: Completed 41-03-PLAN.md
last_updated: "2026-09-29T22:20:00.983Z"
last_activity: 2026-09-29 -- Phase 41 execution started
progress:
  total_phases: 16
  completed_phases: 2
  total_plans: 28
  completed_plans: 25
  percent: 13
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-01)

**Core value:** Catch real defects in a developer's changes before they ship — high coverage, low noise — so a reviewer who can't manually audit code can trust the agent's output as their safety net.
**Current focus:** Phase 41 — Wave 1 — scorer-side noise interventions

## Current Position

Phase: 41 (Wave 1 — scorer-side noise interventions) — EXECUTING
Plan: 6 of 8
Current Plan: 6
Total Plans in Phase: 8
Status: Executing Phase 41
Progress: [█████████░] 89%
Last activity: 2026-09-29 -- Phase 41 execution started

## Performance Metrics

**Velocity:**

- Total plans completed (all milestones): 6
- Average duration: — min
- Total execution time: — hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 09 | 2 | - | - |
| 24 | 1 | - | - |
| 36 | 3 | - | - |
| 37 | 1 | - | - |
| 38 | 6 | - | - |
| 40 | 14 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 05 P01 | 5min | 3 tasks | 1 files |
| Phase 05 P02 | 4min | 2 tasks | 1 files |
| Phase 13 P01 | 5min | 1 tasks | 1 files |
| Phase 19 P01 | 14 | 1 tasks | 1 files |
| Phase 19 P02 | 10min | 3 tasks | 1 files |
| Phase 27 P01 | 3min | 3 tasks | 7 files |
| Phase 28 P01 | 12min | 2 tasks | 7 files |
| Phase 29 P01 | 7min | 2 tasks | 1 files |
| Phase 30 P01 | 3min | 2 tasks | 2 files |
| Phase 30 P02 | 3min | 2 tasks | 2 files |
| Phase 30 P03 | 4min | 3 tasks | 3 files |
| Phase 32 P01 | 6min | 2 tasks | 4 files |
| Phase 32 P02 | 8min | 2 tasks | 2 files |
| Phase 32 P03 | 5min | 2 tasks | 4 files |
| Phase 33 P01 | 4min | 2 tasks | 2 files |
| Phase 35 P01 | 9min | 3 tasks | 2 files |
| Phase 36 P01 | 21min | 5 tasks | 19 files |
| Phase 36 P03 | 15min | 2 tasks | 2 files |
| Phase 37 P01 | 9min | 2 tasks | 2 files |
| Phase 38 P01 | 6min | 2 tasks | 2 files |
| Phase 38 P02 | 23min | 2 tasks | 3 files |
| Phase 38 P03 | 10min | 3 tasks | 14 files |
| Phase 38 P04 | 16min | 2 tasks | 4 files |
| Phase 38 P05 | 41min | 3 tasks | 1 files |
| Phase 38 P06 | 12min | 2 tasks | 1 files |
| Phase 40 P01 | 38min | 2 tasks | 5 files |
| Phase 40 P09 | 45min | 3 tasks | 4 files |
| Phase 40 P13 | 20 min | 2 tasks | 5 files |
| Phase 40 P08 | 16m | 3 tasks | 18 files |
| Phase 40 P11 | 18m | 4 tasks | 27 files |
| Phase 40 P14 | 45m | 4 tasks | 4 files |
| Phase 41 P01 | 25 min | 2 tasks | 2 files |
| Phase 41 P02 | 65min | 3 tasks | 5 files |
| Phase 41 P03 | 12 min | 3 tasks | 3 files |
| Phase 41 P04 | 35 min | 3 tasks | 6 files |
| Phase 41 P05 | 30min | 3 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Decisions affecting current work (v2.9 "Prove it" — from the owner-approved design spec
`docs/superpowers/specs/2026-07-01-prove-it-v2.9-design.md`):

- v2.9 = 3 SEQUENTIAL phases (35 → 36 → 37) continuing numbering from v2.8's Phase 34. Goal: finish
  v2.8's shipped-but-unproven surface (no inert config keys), produce vibe-check's FIRST measured
  catch-rate / false-positive-rate from a committed reusable organic test set, and close. Release
  milestone (plugin 2.8.0 → 2.9.0).

- D-01: branch base is `main`; work on new branch `feat/v2.9`; the old `feat/framework-skill-reviewer`
  branch RETIRES (main is ahead of it after the v2.8 merge + all Fable docs live there).

- D-02: version 2.9.0, not 2.8.1 — `--codex` is a new user-facing capability and the milestone adds a
  new efficacy-artifact class.

- D-03: B3 sourcing stays ORGANIC-ONLY (no vibe-check-found bugs — no circular self-testing) and the
  test set is COMMITTED (reusable milestone-over-milestone regression check).

- D-04: WIRING BEFORE PROOFS inside Phase 35 — the frozen 33-02 orchestrator wiring lands first so the
  codex-announce smoke proof tests the REAL wiring, not the inert v2.8 state.

- D-05: scorer design challenges (H-CORE/H-DUP/H-LANE/B-SEV/B-XCONF/B-PROX/B-REWEIGHT) stay OUT of
  scope — they are explicitly gated on B3's numbers; acting before measuring inverts the milestone's
  own logic. The scoring FORMULA is untouched throughout (standing constraint since v2.8).

- Phase 35 rebases the frozen 33-02 plan (archived at
  `.planning/milestones/v2.8-phases/33-codex-legibility-safer-fix-loop-default-orchestrator-only-kn/33-02-PLAN.md`)
  against the post-Fable `commands/review.md` / `commands/deep-review.md` (the Fable remediation edited
  the same regions: Phase 0 gained the `$GUARD_PY` resolution block near the `$SCOPE_ARGS` normalizer
  sites; Phase 0.6's `--min-confidence` parse prose changed). The rebased plan re-passes the codex
  adversarial gate before execution. 33-02 is prose/dispatch only — `score.py`/`test_score.py`
  byte-unchanged.

- Phase 36 resumes `docs/design/b3-ground-truth/B3-STATUS.md`: build the run-kit (3rd should-catch diff
  = triggarr secret-in-logs, fix `d47b4c2` reversed — the subtle high-value case; ≥2 should-quiet
  diffs; per-diff answer key folding in A8 `/health` name-exemption + A16 axis-vs-site ambiguity; owner
  run-checklist). Owner drives `/deep-review` N=3 per diff (~15–18 runs, resumable across days —
  `/deep-review` is user-triggered, the assistant CANNOT invoke it); assistant scores vs key and writes
  the catch/FP report into `plugins/vibe-check/docs/efficacy/`.

- Recurring-risk pre-flight (Phases 35 + 36): the installed-plugin cache must equal repo `plugin.json`
  before any dogfood/smoke run — a stale cache poisoned 4 of the last 5 milestones.

Earlier decisions (v2.8) still on record:

- v2.8 spine: a repo-level `.vibe-check.toml` **config surface** was the milestone's vehicle; the noise controls were its first consumers. Phase 30 built the reader/precedence/fail-safe; Phases 31-33 plugged knobs into it. SHIPPED early-manual-close 2026-07-01 (Phases 30–32 full, 33-01 only, Phase 34 superseded).
- Phases grouped by **enforcement boundary**: script-enforced knobs (`min_confidence`, `idiom_floor`, `thresholds`, `vibe-ignore`) land in `score.py` via envelope keys; orchestrator-enforced knobs (`disabled` agents, `top_model`, `codex`, the fix-loop label) act in dispatch/prose.
- **The scoring FORMULA stays untouched**: `min_confidence` *filters before scoring*, `thresholds` *parameterize* existing cutoffs, `idiom_floor` *caps* an existing category — no re-weighting. Re-deriving `agent_confidence` is explicitly out of scope.
- Load-bearing invariant: a missing/malformed/partial config degrades **per-key** to its built-in default with a warning and **never breaks a review** — zero-config back-compat == v2.7 behavior.
- Precedence is **CLI flag > `.vibe-check.toml` > built-in default**, resolved per knob by the orchestrator before passing into the envelope (script-enforced) or acting directly (orchestrator-enforced).
- Phase 30 P01: config.py is the never-raise .vibe-check.toml I/O boundary (load_config -> (values,warnings)); inverts score.py's fail-closed posture — degrades per-key to defaults, __main__ exits 0 always (CONFIG-03).
- Phase 30 P01: D-02 thresholds schema LOCKED — {critical,warning,medium} non-bool ints in [1,100], strictly descending, medium>=70, whole-set fallback to None; two ordered pre-parse DoS guards (regular-file BEFORE 1-MiB cap).
- Phase 30 P02: band_for parameterized to band_for(score, thresholds=None); default path byte-identical, GOLDEN_DIGEST unchanged.
- Phase 32-01: idiom_floor cap ACTIVE by default at medium (A1); explicit off/none returns the literal 'off' sentinel (NOT None) end-to-end so absent != off is provable at the scorer; malformed fails SAFE to medium.
- Phase 32-02: vibe-ignore reasoned marker (within +/-2) rides the existing -50 silenced path; bare marker does NOT suppress but emits ONE synthetic low 'suppression' finding per bare occurrence.
- [Phase 35]: 35-01: --min-confidence folded into the Phase-0 $SCOPE_ARGS normalizer alongside --codex — Shared parse-timing bug; the normalizer ADDS GSD/PR/range reach + fixes the --all narrow-parse mis-read, never changes byte-correct diff/--all behavior
- [Phase 35]: 35-01: HIGH-B MOVE-SMOKE-INTO-2c — BashOutput smoke gate relocated inside the launch guard — So a non-launching Codex never hard-blocks the native review (SAFE-01/SAFE-02); Phase 2b header repurposed to a pointer, not deleted
- [Phase 35]: 35-01: rebase discipline held (D-06) — Executed diff deviates from frozen 33-02 ONLY by re-anchored line numbers + the one bare-all alias composition sentence; no design change
- [Phase 36]: 36-01: third organic should-catch = seedsyncarr 879266c (unclamped >100% progress); dashboard 052845e excluded per D-12 (DR3m-01 regex hit)
- [Phase 36]: 36-01: should-quiet picks owner-confirmed (confirm-all): triggarr 1a8c9f9, seedsyncarr 3c27e17, roonseek 2a6bbd9; 355c57f rejected by the line-survival gate
- [Phase 36]: 36-01: answer key pre-registered at ANSWER_KEY_COMMIT ef0ab67 with digest in the separate PREREGISTRATION.md manifest (key blob never contains its own hash)
- [Phase 36]: 36-02: owner drove /deep-review N=3 across all 6 diffs — 18/18 SCOREABLE runs committed + verified (len(passes)==1, head_sha==base_sha, tree.diff.sha256==kit EXPECTED value); pre-registration ordering intact (ANSWER_KEY_COMMIT ef0ab67 ancestor of HEAD, committed-blob digest == PREREGISTRATION.md ANSWER_KEY_SHA256, manifest touched once at cca63e2 strictly before first runs/ commit eca98ec)
- [Phase 36]: 36-02: D-06 exercised — should-quiet-1 run-2 captured, marked unscoreable, repeated (2 archived run-2.failed-* dirs; N-01/N-04 uv.lock mid-review rewrites → chflags immutable-flag prevention @ 4eff2aa); every diff has exactly 3 scoreable runs, no holes
- [Phase 36]: 36-02: Codex outcome recorded honestly from state attribution — codex-adversarial finding present in 16/18 runs; should-quiet-2 produced 0 findings all 3 runs (nothing to attribute, NOT skip evidence); should-quiet-3 run-1 had Codex in agents_run but no surviving codex-attributed finding. Runs measured shipped codex=auto (no --codex forcing)
- [Phase 36]: 36-03: FIRST measured numbers — catch-rate 8/9, FP-rate 6/9 (exact fractions D-09, FULL 9+9 pre-registered denominators, 18/18 scoreable, zero holes, no owner waiver). Scored from state.passes[-1].findings[] vs the committed key blob at ef0ab67 (score-from-blob gate: MANIFEST_COMMIT cca63e2 ordering proven, digest match, ancestry, runs/-clean + descent, per-diff FULL-worktree tree.diff consistency); score.py/test_score.py/config.py byte-frozen; pytest 356+221 green
- [Phase 36]: 36-03: autoescape run-1 = the pre-registered right-site-wrong-axis MISS (detected-below-threshold) — SITE ok but fleet named deprecation/breaks-startup, one finding explicitly "NOT an XSS regression"; runs 2-3 named XSS/autoescape → 2/3. should-quiet-2 clean 0/3; should-quiet-1 + -3 = 3/3 FP each. Codex contributed all 8 catches (codex=auto)
- [Phase 36]: 36-03: D-11 verdict = PROCEED on H-CORE/H-LANE/B-SEV/B-REWEIGHT (FP + axis-stability challenges this run implicates; should-quiet FPs are agent-self-sufficient not +10-cross-confirm-rescued → H-CORE/H-LANE not primarily H-DUP/B-XCONF) AND grow the committed set next milestone (N=3 coarse). Input to next-milestone B3-gated-challenge scoping, NOT an in-phase scorer change (formula frozen). Report appended to RESULTS-v2.9.md (no RESULTS-v3.md)
- [Phase 37]: 37-01: v2.9 PUBLISHED — plugin.json 2.8.0→2.9.0 (commit 17950c0), README ## 📊 Measured Efficacy pointer (8/9 · 6/9 + small-N caveat + RESULTS-v2.9.md link). main FF bbecf55→17950c0 (no merge, no checkout), annotated tag v2.9 (object b1c34342, peels to main, 2.9.0 tree), ONE atomic push of main+tag+feat/v2.9, exact-hash verify PUBLISH-VERIFIED for all three refs. Pre-publish anchor bbecf559 (STATE=A fresh capture). No .planning path in the release commit; score.py/test_score.py/config.py byte-frozen. CLOSE-01 criterion 3 (audited) delegated to the wrapper orchestrator (D-06).
- [Phase 38]: 38-01: seal-1 committed — SEAL1=4c67283b46540f997b8a5c6b530996da880b53ed pre-registers the v2.10 pass bar + decision rule with the ordered seal-2 append-only whitelist; RUN-METHOD-NOTES-v2.10.md seeded (N-01 mandatory per-run clear.txt gate, timestamped fingerprint session IDs, exact Claude-5 model grammar, harness-pin tuple equality, pre-run session.txt binding)
- [Phase 38]: 38-02: verifier pinned (a407539/7be8ed39…) + harness pin (claude-code 2.1.261 / codex-cli 0.145.0 / fable 5) committed BEFORE WAIT 1; part-A checklist script-generated (T1-T7) with regeneration byte-equality + sandbox-exercised recovery; WAIT 1 OPEN (carried-6 re-measure, 18 runs); SET-03 stays Pending until the runs land
- [Phase 38]: 38-03: 6 new B3 kits owner-confirmed (confirm-all, live) + committed at ccf887c — catches triggarr-session-rotation (0866332 reversed, base clone-HEAD f4366a2) + triggarr-settings-form-split (542d5dd reversed, base pinned to the fix itself); quiets should-quiet-4..7 (9be610a SSRF validator, f64a874 log-sanitize, 3d042c8 pydantic bounds, 05cfd1b safe_float parse); set total 12 (D-01 target); D-03/D-04 triggers did NOT fire
- [Phase 38]: 38-03: SET-01 deliberately left Pending — the plan delivers its inventory half; the sealed per-diff answer key half lands in 38-04 (a blob cannot contain its own hash)
- [Phase 38]: 38-04: ground truth sealed — ANSWER-KEY-v2.10 at 5f687d9 (6 new rows, 12 kit digest lines from ccf887c blobs, no self-hash) digest-bound by seal-2 633f1dd (pure five-line byte-append, pinned-verifier proven, manifest FINAL at 2 commits; DENOM 15/21/36); checklist part B (debe57a) regen-validated — WAIT 2 OPEN (18 new-diff baseline runs); SET-01 complete
- [2026-09-05 re-scope, owner decision after an external source review + live model-lineup check]: Phase 39 DISSOLVED — COMPAT-02 (measured cost) returned to backlog 999.12 (no mechanism: the orchestrator cannot tokenize; needs a feasibility spike), COMPAT-01 (Claude-5 docs + corrected static cost anchors) → Phase 44. Phase 40 GAINS TRUST-01/02 (helpers resolve from `${CLAUDE_PLUGIN_ROOT}` + owner-set dev override, never repo-first — today a reviewed PR can plant `plugins/vibe-check/scripts/score.py`/`guard.py` and Phase 3 executes it unprompted; fix agent validates paths BEFORE its first edit) and the cost-anchor correction inside DIET-01. DIET-03 verify-only; DIET-04 spot-checks CAPPED (2 diffs ×1 per batch, full ×3 once at phase end). Model defaults UNCHANGED (aliases already resolve to Sonnet 5 / Opus 5 / Haiku 4.5; Fable 5.1 opt-in). New backlog 999.15 (fix-agent hunk isolation + real verification; ambiguous → leave applied-but-uncommitted), 999.16 (deterministic framework routing + bounded chunks replacing the Haiku downgrade), 999.17 (Fable 5.1 top-tier A/B). Reviewer items 3 (confidence vs severity) and 4 (orchestration out of prompts) were already Phase 41 / Phase 40 nearly verbatim — nothing added.
- [Phase 38]: 38-04: settings-form-split band floor = warning (correctness/data-loss — silent loss of saved settings is action-bar, not the v2.9 medium display-nit precedent); session-rotation = warning (security)
- [Phase 38]: 38-05: SET-03 BASELINE MEASURED — full-set catch 15/15, FP 19/21 over the sealed denominators (15/21/36), 36/36 runs scoreable, zero holes, no waiver. Carried-6 re-measure vs v2.9: catch 8/9 -> 9/9, FP 6/9 -> 9/9 (should-quiet-2 moved 0/3 -> 3/3 FP; autoescape's right-site-wrong-axis miss did not recur) — Scored from state.passes[-1].findings[] against both sealed key blobs (carried ef0ab67, new 5f687d9) after a 9-gate fail-closed ladder: pinned byte-exact seal verifier, dual digests, ancestry, sidecar seal gate, sealed v2.9 tree byte-identical, isolation grid, security spot-check, and commit-anchored pin-matched pre-run-ordered fingerprint provenance across all 36 runs under ONE harness tuple (2.1.261 / codex-cli 0.153.4 / fable 5.1). Worksheet: docs/design/b3-ground-truth/SCORING-v2.10.md (1180b15)
- [Phase 38]: 38-05: codex participation is inferred from findings[].agent == codex-adversarial, never the pass-level record — The pass-level codex record is schema-nondeterministic across passes of the same shipped command: >=6 shapes observed (codex_joined bool; codex object with joined/status x verdict x findings x cross_confirmed; a plain string; and outright ABSENCE with a codex-adversarial finding present). Also two pass-timestamp formats and one empty finding title. Phase 40 orchestration-rewrite input; recorded in SCORING-v2.10 §6 and 38-06 limitations
- [Phase 38]: 38-06: RESULTS-v2.10.md PUBLISHED (0ec7208, 284 lines) — the milestone's single append-structured results doc (D-07). Full-set Claude-5 baseline catch 15/15, FP 19/21 over the sealed denominators; the family-conditional "## The Claude 5 re-measure (Fable 5) — v2.9 vs Claude 5, carried 6 only" section pairs v2.9's 8/9 catch / 6/9 FP against 9/9 / 9/9 on the identical carried six and identical unchanged plugin. Every number transcribed from SCORING-v2.10.md §5, never re-derived. Sealed pass bar quoted with implied literal targets and explicitly NOT evaluated (Phase 43's job). Phases 41/43 append to this same file. — SET-03's write-up half / ROADMAP success criterion 4; T-38-19 (report/worksheet divergence) mitigated by transcription-only + spot-check; T-38-21 (premature pass-bar evaluation) mitigated by explicit deferral.
- [Phase 38]: 38-06: CHECKPOINT RESOLVED — Option 1: both Task-2 plan-literal mismatches accepted as RECORDED DEVIATIONS; nothing patched, reverted, or moved to force a literal to pass. (a) The plugin-freeze gate is RE-STATED at its intent — "every plugins/vibe-check/ delta vs v2.9 is status A and confined to non-executable docs/efficacy/, with the executable/prompt surface byte-identical" — because the plan's literal one-A-line assertion is not what was executed: there are TWO A lines, the second being ULTRAREVIEW-SHADOW.md (999.18 status doc, added 9d565f3 / updated 5d2173a, both after SEAL1). T-38-20's threat is unrealized: score.py f3bbaae, test_score.py 7a86600, config.py f9d7ad5, review.md dd71d4f, deep-review.md 4eee361 all byte-identical to v2.9; the diff excluding docs/efficacy/ is empty; all 12 fingerprints record cache-root .../vibe-check/2.9.0 so no repo-side doc reached a run. (b) Check 5 RE-POINTED from the non-existent plugins/vibe-check/README.md to the repo-root README.md — which contains zero RESULTS-v2.10 references and still cites 8/9 - 6/9 linking RESULTS-v2.9.md (D-07 held; the repoint is Phase 44's). — Forcing the literals would have required deleting or rewriting history for a non-executable status doc that cannot affect a review — a worse integrity outcome than an honest deviation record. The composite PHASE-38-EXIT-OK string was NOT emitted; every individual gate it composes passed and is recorded verbatim.
- [Phase 38]: 38-06: PHASE 38 EXIT PROVEN — manifest FINAL at 2 commits (SEAL1 4c67283, SEAL2 633f1dd); pinned canonical verifier (a407539 / 7be8ed39...75daaf) live-digest-matched, single-commit asserted, executed from its introducing-commit blob returning SEAL2-APPEND-WHITELIST-OK; v2.9 sealed docs+runs untouched (exit 0); diffs/ 14 lines all status A, non-A count 0; KIT-BLOB-EQUALITY-OK 15 v2.9 kit paths byte-equal at HEAD; NEW-KIT-SEAL-OK 14 new kit paths single-introducing-commit with all 12 sealed sha256(diffs/...) digests matching HEAD blobs (key blob 5f687d9); working tree clean. Baseline + sealed manifest are committed — Phases 40+ UNBLOCKED (Phase 39 dissolved). ADVISORY: ULTRAREVIEW-SHADOW.md has TWO introducing commits, so it would fail the one-introducing-commit rule if that rule were ever extended from diffs/ to plugins/vibe-check/docs/efficacy/. — T-38-25 (seal rewrite / weakened verifier) and T-38-26 (sealed kits removed, renamed, type-changed, or rewritten post-addition) both mitigated status-letter-complete in both directions.
- [Phase 40]: 40-01: seal verifier hardened + re-pinned (de8633c / 605e61a3…d081a3) — derivation is now git log --full-history --simplify-merges --topo-order --reverse --branches --tags --remotes plus three merge-base --is-ancestor asserts; the old rev-list HEAD form was proven defeatable by a -s ours side-branch edit (scratch scenario 5 counted 2 and passed). New consumer rule: verifier-path full-history all-ref commit count == 2 and the second commit == the ledger pin.
- [Phase 40]: 40-01: SUPERSESSIONS-v2.10.md created as the append-only supersession ledger (entries 001-004 = D-01/D-03a/D-03b/D-04), each quoting its sealed statement verbatim. should-quiet-7 excluded -> FP 16/18 superseded vs sealed 19/21 which stands; Phase 43 runs the 11-diff set against BOTH denominators. No sealed byte rewritten; PREREGISTRATION-v2.10.md byte-unchanged; three sealed docs got one pointer line each.
- [Phase 40]: 40-01: ledger + verifier commits are in NEVER_REVERT and sit outside every batch rollback unit (F18) — reverting would create a third verifier commit and break the count==2 rule entry 004 introduces; a ledger correction is a NEW entry citing the corrected one, never a revert.
- [Phase 40]: 40-01: acceptance-criteria conflict adjudicated — the three sealed-doc pointers are ONE logical pointer each WRAPPED at 100 columns (numstat 4/4/3, not the plan's literal 1 0), because a single-line pointer is 248/192 columns and would violate the 100-column criterion. The plan's own action text says '(one line, may wrap at 100)'. Likewise three ledger lines exceed 100 deliberately: two verbatim sealed-byte quotes and one copy-paste git command.
- [Phase ?]: 40-09: spot-check transcripts stay local (gitignored), bound by a committed sha256 — they carry the owner's private instructions and the repo is public
- [Phase 40]: 40-13: mode-path expectations keyed by (batch, mode); review-all, deep-all and fix-loop run as tmux-driven interactive sessions because no gate pre-answer flag exists at 7a386ed; fix-loop and fix-agent are separate properties
- [Phase 40]: Owner accepted Claude Code 2.1.281 over the 2.1.261 baseline pin before batch 1 (SUPERSESSIONS entry 006; RUN-METHOD-NOTES-phase40 pin corrected while zero session blocks existed). The CLI version is a named confound for every Phase-40 spot-check against the Phase-38 baseline; Phase 43's full re-measure is the proof.
- [Phase 40]: Batch-1 mode-path validation: run 1 failed all 3 captured paths (unseated deep-review.md read review.md from the installed cache and executed a repo-planted helper; the monolith does not announce phases as text; one improvised state key). Owner-approved remediation recorded under 40-13: deep-review.md TRUST-01 seat + absolute review.md read pulled forward from 40-11 (857d019); tracecheck batch-1 rule sequence_evidence:"none" with always-on dispatches as evidence and an activity floor (9e92a9d); procedure-doc fixes (pretrust, finalize seed removes the pass snapshot, finalize deliverable assert). Run 2 on batch1-39e11a7eef89: 6/7 rows pass, negative control live, canary silent everywhere; finalize red on evidence FORM only (Bash cat vs Read tool). Owner handed batch 1 over with that exception; the Read-vs-cat evidence rule is decided in 40-08/40-13.
- [Phase 40]: 40-08: HARD CONTRACT shared at phases/shared/00-contract.md on review.md's stricter wording (F9c); lazy reads are Read-tool instructions in batchsnap's parsed form; the phase-file Read is the evidence, announcements are not
- [Phase 40]: 40-08: pass-entry key set stated once in 45-persist.md = future-schema.json (9 keys incl. filtered+codex; codex {status joined|skipped|off, reason slug|null, verdict, findings int}; /review writes status off; Z-second timestamps)
- [Phase 40]: 40-11: /deep-review is a spine over the shared phase files (own seat + bootstrap Read before any phase, never reads review.md); codex=off short-circuit in the spine; codex_gate.py/codex_translate.py own Family 3; D-11 anchors corrected in both sites; DIET-03 dissolved (Phase-5 fixes_applied write removed, Phase 4.5 sole writer). Batch-3 snapshot batch3-d74452263961 built, not handed over.
- [Phase ?]: 40-14: DIET-01 AFTER leg is proxy-only (footprint.py --measure is a no-op); plain path -41.67% on bytes and the 2.7 proxy vs the 40% soft target
- [Phase ?]: 40-14: DIET-03 recorded as dissolved; W1 phases/review/45-persist.md is the single state.passes writer; nothing returns to 999.8
- [Phase 41]: 41-01: catch-manifest AXIS labels calibrated to the sealed v2.9 autoescape run-1 MISS (revert/convention/divergence framings axis=false; titleless findings axis=false)
- [Phase 41]: 41-02 owner AMENDED runs/triggarr-secret-in-logs/run-2 (ledger 008; v2.9 archive cannot reproduce the catch); replay baseline = REPRODUCED 25 / 26 · UNEVALUABLE 0 · AMENDED 1; ledger 007 not extended to filtered[] — D-05 stop rule; owner decision 2026-09-29
- [Phase 41]: 41-03: B-REWEIGHT offsets derived over committed manifest = impact -12, architecture -6, bugs -2 (pool 96/147, ALPHA=20, MIN_LABELED=5); smaller than research's -18/-11 because 41-01 labels every at-SITE finding; label rule not revisited (D-15)
- [Phase 41]: 41-04 B-SEV: a no-second-opinion group is capped at critical floor - 1 before band_for; second opinion = envelope-verified Codex corroboration or persistence; finalize cutoff judges the uncapped score
- [Phase 41]: 41-05 B-REWEIGHT: embedded offsets == calibrate derive {architecture:-6,bugs:-2,impact:-12}; lone-lane only; min_confidence/agent_confidence/stable_hash read raw; ALONE replay REGRESSED 0, FP 16/18 -> 14/18 (commit 0ee3818)

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work — planning details, not blockers]

- [Phase 35] The 33-02 plan is codex-APPROVED and frozen but NEEDS REBASING before execution — the Fable remediation edited the same review.md/deep-review.md regions (Phase 0 `$GUARD_PY` resolution near the `$SCOPE_ARGS` normalizer sites; Phase 0.6 `--min-confidence` parse prose). Do NOT blind-resume the old Phase-33 orchestrator resume files; the rebased plan must re-pass the codex adversarial gate.
- [Phase 35] WIRING BEFORE PROOFS: execute 33-02 first, THEN run the v2.8 smoke proofs — the codex-announce proof must test the real wiring, not the inert v2.8 state (D-04).
- [Phase 36] B3 needs OWNER RUNTIME (~15–18 `/deep-review` runs; the skill is user-triggered — the assistant cannot run it). The phase delivers a run-checklist with exact commands; runs are resumable and spreadable across days.
- [Phases 35/36] Stale installed-plugin cache poisons dogfood/smoke runs (recurred in 4 of the last 5 milestones) — pre-flight: installed version must equal repo `plugin.json` before any run.
- [Phase 37] The v2.8 evidence debt needs NO separate retroactive audit — it became v2.9 requirements (Phase 35), so the v2.9 milestone audit covers it.
- [Phase 38] BASELINE MODEL IDENTITY (before run 1): the harness pin `fable 5` accepts both Fable 5 and Fable 5.1, but STEP 0.25 / the 38-05 gate require every session's typed `model:` value to be IDENTICAL — fix the session model explicitly for all 36 runs and type the same value every session (the lineup shifted to Fable 5.1 as newest; a mid-baseline label change would hard-stop the gate and force reruns). Do not update Claude Code mid-baseline: the pinned CLI version is what holds the subagent alias→model mapping constant. Zero runs recorded as of 2026-09-05, so the pin is still correctable.
- [Phase 40] TRUST-01 spike before planning: confirm `${CLAUDE_PLUGIN_ROOT}` is expanded/available inside a subagent's Bash (the fix agent resolves guard.py on its own). If it is not, the trusted root must reach the fix agent another way (e.g. the orchestrator passes the resolved absolute path into the prompt) — never via the reviewed repo.
- RESOLVED 2026-09-29: 41-02 blocker (runs/triggarr-secret-in-logs/run-2 UNEVALUABLE) closed by owner amendment, SUPERSESSIONS-v2.10.md entry 008; baseline replay REPRODUCED 25 / 26 · AMENDED 1.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Framework agents | Express, Vue, Angular, Electron, React-Native agents (backlog Phase 999.1) | Shipped v2.7 | v2.1 scoping |
| FastAPI depth | OpenAPI/contract checks; upload streaming/chunking refinements | Deferred | v2.1 scoping |
| Codex async | Background + second-pass folding (ASYNC-01) | Deferred | v2.2 scoping |
| Codex reach | Codex in `/review` via opt-in flag (ASYNC-02); configurable model/effort (ASYNC-03) | Deferred | v2.2 scoping |
| Whole-repo enhancements | Baseline-aware suppression (BASELINE-01), snapshot carry-forward (SNAPSHOT-01), Codex-over-whole-repo (CODEX-ALL-01) | Deferred | v2.3 scoping |
| Configurable & honest | Tunable config (shipped v2.8), measured cost (COST-01 / 999.12), docs pass (DOCS-01 / 999.13) | Partially deferred | v2.6 scoping |
| Dogfood hardening | Remaining v2.4/v2.5 Mediums — fix-agent prompt-injection hardening, `.planning/*-SUMMARY.md` force-tracking hygiene (HARDEN-01) | Deferred | v2.6 scoping |
| CI reach | gitleaks (SECRET-01 / 999.2), SARIF (SARIF-01 / 999.3), PR-posting (PRPOST-01 / 999.5) | Deferred | v2.6 scoping |
| **33-02 orchestrator wiring** | LEGIBLE-01/02/03 — NOW SCHEDULED as v2.9 Phase 35 (rebase + execute against post-Fable review.md/deep-review.md). ⚠ Plan needs REBASING before execution. | **Scheduled (v2.9 Phase 35)** | v2.8 manual close |
| **Phase-34 efficacy proofs** | Planted-fixture smoke proof per v2.8 knob + Phase 33's deep-review gate — NOW SCHEDULED as v2.9 Phase 35 (PROOF-01, PROOF-02). | **Scheduled (v2.9 Phase 35)** | v2.8 manual close |
| **Fable — answer-key fixes (A8/A16)** | A8 (`/health` name-exemption), A16 (axis-vs-site ambiguity) — NOW SCHEDULED into v2.9 Phase 36's per-diff answer key (B3-01). | **Scheduled (v2.9 Phase 36)** | v2.8 manual close |
| **B3 harness execution** | Catch-rate/FP-rate against the FIXED post-Fable system — NOW SCHEDULED as v2.9 Phase 36 (B3-01/02/03). | **Scheduled (v2.9 Phase 36)** | v2.8 manual close |
| **Fable — remaining** | `security.md` critique pass (needs Opus); all design challenges (H-CORE/H-DUP/H-LANE/B-SEV/B-XCONF/B-PROX/B-REWEIGHT) — gated on B3's numbers (v2.9 Phase 36 report states proceed/don't/need-more-data); `CATEGORY_DOMAIN` twin proposals (ts `async-discipline`→correctness, express `input-validation`→security). | Deferred (post-v2.9) | v2.8 manual close |

## Session Continuity

Last session: 2026-09-29T22:19:56.667Z
"Quiet down" merged with the Opus 5 adaptation plan by owner decision — restructure-then-tune) and
re-roadmapped to **Phases 38–44** (7 sequential phases; 20 requirements, 20/20 mapped). The locked
sequence is SET → COMPAT → DIET → SCORER (Wave 1) → AGENT (Wave 2) → PROVE → CLOSE; it may not be
reordered. ROADMAP.md, STATE.md, REQUIREMENTS.md written (the prior 5-phase 38–42 roadmap section was
replaced; milestone history + the 999.x backlog preserved).
Stopped at: Completed 41-03-PLAN.md

Load-bearing sequencing notes for whoever plans next:

- **Phase 38 gates everything.** SET-02's pre-registration must be provably ordered BEFORE any
  COMPAT/DIET/SCORER/AGENT change lands, and SET-03's ×3 baseline runs on the UNCHANGED v2.9.0 plugin.
  Nothing in Phases 40–42 may land until 38's baseline + sealed manifest are committed (Phase 39 dissolved 2026-09-05).

- **The SET-03 baseline is dual-duty**: it is both the pre-change anchor for the noise work AND the
  Opus 5 / Claude 5 re-measure (same unchanged plugin, new model generation).

- **Phase 40 (diet) precedes Phase 41 (scorer) deliberately** — SCORER-01 replays POST-DIET run data so
  the tuning lands on the system that actually ships. Never tune-then-restructure.

- **Measurement is OWNER-RUNTIME.** Phases 38 (36 runs), 40 (CAPPED per-batch spot-checks, 2 runs each, plus ONE
  end-of-phase ×3), 41 (SCORER-05 spot-check, 6 runs), and 43 (~30–36 runs) all need owner-driven `/deep-review` invocations — the assistant CANNOT invoke
  `/deep-review`. Each of those phases must deliver an exact-command run-checklist; runs are resumable
  across days.

- **Recurring pre-flight**: the installed-plugin cache must equal repo `plugin.json` before ANY
  measurement run (a stale cache poisoned 4 of the last 5 milestones).

- Noise-wave design spec: `docs/superpowers/specs/2026-07-08-quiet-down-v2.10-design.md`.
  Prose-diet inventory: `docs/design/prose-to-code-inventory.md` (honor its extract-vs-keep judgments).

## Operator Next Steps

- **Phase 38 is COMPLETE (6/6 plans).** The Claude-5 baseline is measured, published, and its exit
  integrity proven: `plugins/vibe-check/docs/efficacy/RESULTS-v2.10.md` (0ec7208) states full-set
  catch 15/15 · FP 19/21 and the family-conditional "Claude 5 re-measure (Fable 5)" section
  (carried-6: v2.9 8/9 · 6/9 → Claude-5 9/9 · 9/9). Nothing in Phases 40+ was blocked by it any longer.

- Next: plan Phase 40 directly (`/gsd:plan-phase 40`) — Phase 39 was dissolved 2026-09-05. Phase 40
  carries DIET-01..04 + TRUST-01/02; **run the `${CLAUDE_PLUGIN_ROOT}` spike first** (see
  Blockers/Concerns).

- The **sealed pass bar is NOT evaluated** — Phase 43 evaluates it against this baseline per the
  sealed decision rule in PREREGISTRATION-v2.10.md. The **README repoint** (still publishing 8/9 · 6/9
  → RESULTS-v2.9.md) is **Phase 44's**. Phases 41/43 **append** to RESULTS-v2.10.md — do not create a
  RESULTS-v2.11 (D-07).

- The harness freeze (Claude Code 2.1.261 + `DISABLE_AUTOUPDATER=1`, codex-cli 0.153.4, vibe-check
  2.9.0 cache) is no longer load-bearing for correctness — scoring reads the committed archive — but
  38-06 did not lift it.

- Re-scope record: ROADMAP.md v2.10 header note (2026-09-05) + REQUIREMENTS.md (21 active, COMPAT-02
  withdrawn) + PROJECT.md Key Decisions.
