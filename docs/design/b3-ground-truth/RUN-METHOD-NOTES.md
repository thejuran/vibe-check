# B3 run-method notes (Wave 2 working log — feeds the Wave 3 report's Method/Limitations)

> Not a run artifact and not covered by the pre-registration immutability rule (that covers
> ANSWER-KEY-b3.md and PREREGISTRATION.md only). Records protocol clarifications and
> gate deviations observed during the owner runs, in the open, before scoring.

- **N-01 (protocol clarification, before run 3):** the checklist isolates the state-file
  carry-forward channel but does not explicitly mandate fresh conversational context per
  run. Practice adopted from run 1 onward: `/clear` (or a fresh session) in the source repo
  before EVERY `/deep-review` run, so no run can remember a prior run's findings.
  All scored runs follow this practice.

- **N-02 (gate false-positive, triggarr-autoescape run 1, 2026-07-04):** the step-8f3
  no-untracked guard tripped on ~170 pre-existing owner-local tool artifacts
  (`.aidesigner/` Apr 2026, `.gsd/` May 2026, `.playwright-mcp/` Jun 2026, `.mcp.json`,
  `.orchestrator.json`, `.planning/HANDOFF.json`) that are gitignored at triggarr `main`
  but NOT at the pinned base `e11187e` (older `.gitignore`). Diagnosis: files pre-date the
  measurement by weeks-to-months (mtime-proven); `git diff` never includes untracked files,
  so the reviewed diff was unaffected — 8f1/8f2 (full-tree diff sha + touched-path set)
  passed. Remedy: paths added to `~/triggarr/.git/info/exclude` (the same local-exclude
  mechanism STEP 0.5 uses for `.turingmind/`), gate re-ran clean, capture re-executed
  against the UNTOUCHED state file (mtime verified older than the remedy). No run was
  discarded; no state was regenerated. Expect the same remedy to be needed for other
  old-base pins if local tool artifacts exist in those repos.
