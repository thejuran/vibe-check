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

- **N-03 (real gate catch → run repeated, should-quiet-1 run 2, 2026-07-04):** the step-8f1
  full-worktree proof FAILED because `uv.lock` was modified during the review run (a
  dependency re-resolution side effect while the review's agents executed — bcrypt et al.
  folded into the lockfile at the old base). Unlike N-02 this was a REAL tree contamination:
  the reviewed tree was not purely the planted diff, so per D-06 the run was marked
  unscoreable, the bad run dir archived (`run-2.failed-<ts>`), `uv.lock` scope-reverted,
  and run 2 REPEATED via the FAILED-RUN RECOVERY block. The gate did exactly its job.
  Watch-for: if this recurs on the retry, investigate which review step invokes uv.

- **N-04 (N-03 recurred on the retry → prevention applied, should-quiet-1 run 2 retry,
  2026-07-04):** the retry's review completed (state written 11:17 local) but `uv.lock` was
  again modified mid-run (mtime 11:13; +83 lines, same bcrypt-era re-resolution) — the
  retry was therefore ALSO unscoreable per D-06 and was discarded before capture; its
  evidence (state.json + contaminated tree.diff) is archived at
  `runs/should-quiet-1/run-2.failed-1783179419/`. **Root cause (investigated per N-03's
  watch-for):** the deep-review orchestrator's coverage step is consume-only by contract
  (`deep-review.md` Phase 1d: "NEVER run a coverage or test command"), so the writer is a
  reviewer AGENT running an exploratory `uv run …` verification command; at this pinned old
  base the committed lock is stale relative to `pyproject.toml`, so any default `uv run`
  re-locks. Agent behavior is non-deterministic per run — run 1 was clean, both run-2
  attempts were hit — so re-rolling is not a fix. **Prevention (protocol addition for
  uv-managed repos at old bases):** set the macOS immutable flag on the lockfile for the
  duration of a diff's runs — `chflags uchg <repo>/uv.lock` after the fresh/resume block,
  `chflags nouchg <repo>/uv.lock` before the step-9 revert. The flag blocks modify AND
  rename-over (uv's atomic write), is invisible to git, and an agent's failed `uv run` is
  itself harmless to the measurement (the review proceeds; equivalent to the command not
  being run). Applied to `~/triggarr/uv.lock` (in effect for should-quiet-1 runs 2–3).
  `~/roonseek` also has a `uv.lock` — apply the same flag when should-quiet-3's fresh block
  runs; `~/seedsyncarr` has none (n/a for should-quiet-2).

- **N-05 (N-02 recurrence as predicted, should-quiet-2 run 1, 2026-07-04):** the step-8f3
  no-untracked guard tripped in `~/seedsyncarr` on 20 pre-existing owner-local tool
  artifacts (`.orchestrator.json` Jun 1, `.playwright-mcp/*.yml` Jun 2–3) — gitignored at
  current main but not at the pinned old base `84aff27`. Same diagnosis and remedy as N-02
  (mtimes pre-date the measurement by a month; `git diff` unaffected — 8f1/8f2 passed;
  paths added to `~/seedsyncarr/.git/info/exclude`, gate re-ran clean, capture executed
  against the untouched state file). No run discarded; no state regenerated.
