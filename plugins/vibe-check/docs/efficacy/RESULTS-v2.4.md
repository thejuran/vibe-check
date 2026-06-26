# Dogfood-Driven Hardening Efficacy Test — RESULTS (v2.4, Phase 18)

**Verdict: CLOSE-01 `PASS` · owner sign-off pending at milestone-end gate** — the v2.4 `--all`
self-dogfood ran end-to-end on vibe-check's own 2.4.0 tree, confirmed every old-class
DOGFIX-01..10 / ROBUST-01..04 defect ABSENT with zero new code-defect regressions, and
`--all --finalize` exited cleanly (the empirical DOGFIX-06 proof — the exact mechanism that
forced v2.3's Phase 12 to SKIP `--finalize`).

Run as a human-in-the-loop main session (the `--all` estimate gate is an interactive
`AskUserQuestion` with no pre-answer flag — same posture as v2.2 Phase 6 / v2.3 Phase 12).
Dogfood target: **this repo itself** (vibe-check), whole tree, on the version-bumped (2.4.0)
tree. Findings scored deterministically by `scripts/score.py` (the new Phase-16 core);
`/deep-review` surfaces at score ≥ 70, with the plain-`--all` Critical/Warning listing bar
narrowing the default render to C+W. Codex correctly fail-closed (a whole-repo set is not a
representable diff range — REVIEW-04), so the run was native-agents-only BY DESIGN.

## Scope reviewed

- **42 of 43 tracked files reviewed** (1 skipped at triage — `LICENSE` boilerplate); 0
  symlinks dropped, 0 selection-time skip-rule exclusions. The tracked tree is the plugin
  source + docs + 8 force-tracked `.planning/*-SUMMARY.md` files (see the hygiene finding
  below).
- **4 risk-ranked chunks** (riskiest first). The new executable core floated correctly to the
  top: chunk 1 seeded on `scripts/score.py` (tier 2 source) + `commands/review.md` (churn 34);
  chunk 2 on `scripts/test_score.py` + `codex-adversarial.md`. README (a high-churn doc) did
  NOT float above source — the tier-first risk sort (ROBUST/CHUNK-01) held.
- **Native agents only.** Codex skipped with slug `whole-repo-non-representable` — expected,
  not a gap.

## CLOSE-01a — old-class defects confirmed ABSENT (the core efficacy proof)

The `--all` lens reviewed every DOGFIX / ROBUST defect-site file. The `architecture` and `bugs`
agents verified, in the reviewed tree:

| Defect class | Site | Verdict |
|---|---|---|
| DOGFIX-01 (resume hint) | review.md / deep-review.md / README | ✅ current `/vibe-check:` namespace, no unbound placeholder |
| DOGFIX-02 (line-number cites) | deep-review.md → review.md | ✅ cites section NAMES, not line numbers |
| DOGFIX-03/05 (phantom "High" band / orphan scoring contract) | false-positive-rules.md | ✅ defers to scoring.md; no phantom band; no second contract |
| DOGFIX-04 (architecture.md contradictions) | docs/architecture.md | ✅ reconciled with specs; no thinking-param claim |
| **DOGFIX-06 (`--all --finalize` wrong state path)** | review.md Finalize | ✅ **PROVEN — see CLOSE-01b** |
| DOGFIX-07 (PRIOR_PHASE→mv guard) | review.md | ✅ allowlist guard present |
| DOGFIX-08/09/10 (Codex title / fix-agent injection / commit-title allowlist) | codex-adversarial.md / fix.md | ✅ sanitize-and-keep + validated multi-path pathspec present |
| ROBUST-01 (single-writer state) | score.py / review.md | ✅ single writer; no by-hand scored-field write (lock test present) |
| ROBUST-02 (cross-confirm matcher) | score.py CATEGORY_DOMAIN | ✅ category-domain overlap; title-substring matcher dead |
| ROBUST-03 (carry-forward hash) | score.py canonical_window | ✅ widens-both-or-neither; low-entropy safe |
| ROBUST-04 (scoring-ran invariant) | review.md render gate | ✅ hard-halt render gate + dispatch detect-and-warn present |

**Zero old-class Critical/Warning reproduced. Zero NEW code-defect regressions.**

## CLOSE-01b — `--all --finalize` exited cleanly (the headline DOGFIX-06 proof)

`--all --finalize` resolved the **mode-aware** state path
`.turingmind/state/by-mode/all/d9f8acbae7c7.json` — NOT an unset `$PHASE_ID` path (the v2.3
bug that made Phase 12 skip finalize). With zero outstanding Critical/Warning it ran the
medium-acknowledgment loop, wrote `.turingmind/REVIEW.md`, and archived its state file. A
pre-run sentinel vs post-run diff confirmed **exactly one fresh archive** produced this run.

FINALIZE_ARCHIVE: .turingmind/state/by-mode/all/d9f8acbae7c7.json.archived-2026-06-26

## What the audit surfaced (the usefulness bar)

68 raw findings → 13 scored survivors (≥70) → all resolved or owner-deferred. **None was an
old-class regression.** Two kinds:

- **Two genuinely-new doc-drift findings (Warning) — FIXED this phase.** The dogfood caught
  `docs/efficacy/ANSWER-KEY.md` and `RESULTS-v2.2.md` still describing the *dead*
  title-substring cross-confirm rule that ROBUST-02 replaced with category-domain overlap —
  which also falsified the 17-01-SUMMARY "tree-wide zero-hit" claim. This is exactly the
  cross-file-drift class vibe-check exists to catch, found in its own tree. Fixed in commit
  `1b747bd`; a targeted re-review confirmed the drift resolved tree-wide.
- **One no-CI Warning + ten Mediums — owner-deferred to v2.5.** Latent untrusted-input edges in
  `score.py` (malformed-container fail-closed crashes), fix-agent prompt-injection hardening,
  test-quality gaps in `test_score.py` (subprocess timeout, loose assertions, duplicated golden
  digest), the `framework-react` categories that never cross-confirm, and the `.planning/`
  SUMMARY force-tracking hygiene issue. All non-old-class; acknowledged as a v2.5
  hardening-candidate backlog, the same disposition v2.3→v2.4 used.

The deterministic core behaved exactly as specified: `score.py` exited 0 with
`scored_by_script:true`, every survivor carried `band`/`orchestrator_score`/`stable_hash`, and
the render gate's fail-closed contract held.

## Provenance (honest history — fixes were applied, not papered over)

- **DOGFOOD_HEAD** below is the clean, version-bumped commit the `--all` dogfood actually
  reviewed (`8ce8ab5`, plugin.json at 2.4.0).
- The dogfood motivated one real fix commit (`1b747bd`, the two doc-drift corrections above),
  which the owner explicitly approved before finalize. So the final tagged tree = the reviewed
  base + that fix + this RESULTS doc. The tag points at the corrected tree; this doc records
  the full chain transparently rather than asserting a single-file-parent provenance that the
  approved fix makes untrue.

DOGFOOD_HEAD: 8ce8ab53e7fc6a7fdb677042a2012690fd8ec348

## Plain-language summary (for the owner)

We pointed the tool at its own code and ran the whole-repo audit end-to-end on the 2.4.0 build.
It estimated the cost and asked before spending, reviewed 42 of 43 files in 4 risk-ordered
batches (the new scoring script and the orchestrator prose correctly ranked riskiest), and
produced a clean report. The important result: **every bug we fixed across this milestone stayed
fixed** — the tool found none of them coming back — and the close mechanism that broke last time
(`--all --finalize`) now works cleanly. The audit did surface a couple of *new* small things,
the most interesting being that two of the tool's own test-record docs still described an old
matching rule we replaced — a real documentation drift, which we fixed on the spot. The rest
were minor hardening ideas we're parking for a future v2.5. In short: the milestone is proven,
the close works, and the tool even caught a fresh drift in itself and we closed it.

<!-- The owner sign-off task is the SOLE author of the OWNER-SIGNOFF marker below this line. -->

OWNER-SIGNOFF: pending
