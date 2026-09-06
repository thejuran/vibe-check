# B3 v2.10 baseline — PAUSE STATE (2026-09-06) and Monday resume procedure

Working note for the owner-run WAIT. Not a run artifact, not covered by the
pre-registration immutability rule. Authoritative evidence is the committed run dirs and
`RUN-METHOD-NOTES-v2.10.md`.

## Where the campaign stopped

**10 of 36 runs captured.** Paused 2026-09-06 because the owner ran out of Fable credits.

| diff | repo | captured | note |
|---|---|---|---|
| triggarr-secret-in-logs | ~/triggarr | 3/3 | complete, clone restored |
| triggarr-autoescape | ~/triggarr | 3/3 | complete, clone restored |
| third-organic-should-catch | ~/seedsyncarr | 3/3 | complete, clone restored |
| should-quiet-1 | ~/triggarr | 1/3 | **IN PROGRESS** — run 2 next |
| should-quiet-2, should-quiet-3 | seedsyncarr, roonseek | 0/3 | part A remainder |
| the 6 part-B diffs | — | 0/3 | needs the part-B gate first |

## Live state left on disk (do not disturb)

- `~/triggarr` is **detached at 98eb419** with the should-quiet-1 patch applied. Live full
  diff sha256 `a8137f5d877240428bd3aef44c93ba2b650d19063dd6aa6485c332bd7a17d37a` == the
  sealed EXPECTED_TREE_DIFF_SHA256. `uv.lock` carries the `uchg` flag (N-03/N-04). The
  sentinel `.turingmind/state/.b3-inprogress` names should-quiet-1 and start_branch=main,
  start_sha=f4366a2. No state JSON present (run 2 restarts from empty).
- `~/seedsyncarr` and `~/roonseek` are on `main`, clean, no sentinel.
- `turingmind-code-review` is on `feat/v2.9`, clean, nothing unpushed.
- 5 harness fingerprints committed, all `Fable 5.1 / 2.1.261 / codex-cli 0.153.4`.

Leaving the clone patched across the pause is the checklist's designed resume path (the
RESUME-AT-NEXT-RUN block re-proves it). Do not run `git checkout`/`switch` in `~/triggarr`,
do not clear the `uchg` flag, and do not delete the sentinel.

## Harness — frozen, keep it that way

| component | pinned value | how it is held |
|---|---|---|
| Claude Code | 2.1.261 | `~/.local/bin/claude` symlinked to `versions/2.1.261`; `DISABLE_AUTOUPDATER=1` in `~/.claude/settings.json` env |
| model | Fable 5.1 | typed per session at STEP 0.25; **pin correction is now illegal** |
| codex-cli | 0.153.4 | npm global; do not update |
| vibe-check | 2.9.0 cache == tag v2.9 | STEP 0 verifies both directions |

**Do NOT before the campaign ends:** `claude update` / `claude install`, `npm update -g`,
`brew upgrade`, any vibe-check reinstall or resync.

**⚠ Model default changed on 2026-09-06:** the owner set Opus 5 (1M context) as the saved
default for new sessions. Every source-repo session MUST be switched back to Fable 5.1 with
`/model` before any run — a fingerprint recording `opus 5` fails the STEP 0.25 grammar/pin
gate, and mixing model values across sessions fails the 38-05 cross-session constancy gate.

## Monday resume — exact order

1. **Fix the model default.** `/model` → Fable 5.1 in the guide session, so new sessions
   default correctly.
2. **Guide session** in `~/turingmind-code-review`; the block runner is `~/.b3/b3 <first> <last>`
   (inner line ranges only, never the ``` fences). Re-derive ranges with
   `grep -n '^```' docs/design/b3-ground-truth/RUN-CHECKLIST-v2.10.md` — the numbers below are
   as of this file's commit.
3. **Pre-registration gate** — `~/.b3/b3 59 95` → expect `pre-registration gate OK … (manifest commits: 2)`.
4. **STEP 0** — `~/.b3/b3 110 149` → expect `STEP 0 OK …`.
5. **Source session**: launch Claude Code in `~/triggarr`, confirm `claude --version` is
   2.1.261, run `/model` and set **Fable 5.1**, confirm `/vibe-check:` autocompletes.
6. **STEP 0.25 fingerprint** — `~/.b3/b3 164 211`, type `Fable 5.1` at the prompt (first run of
   any calendar day, and after ANY relaunch).
7. **RESUME-AT-NEXT-RUN for should-quiet-1** — `~/.b3/b3 2131 2162` → re-proves the pin, the
   applied patch, the live diff sha, the touched-path set, and re-asserts the uv flag.
8. **should-quiet-1 run 2**: pre-run `~/.b3/b3 1896 1926` (type `CLEARED` after `/clear` in the
   source session) → owner runs `/vibe-check:deep-review` → post-run `~/.b3/b3 1945 1992`.
9. Then run 3 (pre `~/.b3/b3 2000 2030`, post `~/.b3/b3 2049 2096`), then the revert-once block
   (`~/.b3/b3 2102 2127`), then diff 5 (should-quiet-2, seedsyncarr) and diff 6 (should-quiet-3,
   roonseek). After all 6 part-A diffs: the part-B gate (`~/.b3/b3 3241 3299` — re-derive) before
   any new-diff run.

## Standing rules adopted during runs 1-10

- **Never type "continue" into a stopped run.** A run that halts for credits or any other
  reason is unscoreable (N-08): report it, archive via the FAILED-RUN RECOVERY block, rerun.
- **Fix the loop the same way every time:** "Skip fixes this pass" (option 4), then "Abandon
  for now" (option 3). Never rerun-on-new-diff, never finalize, never let the fix agent commit.
- **State-key drift is expected (N-06/N-07).** After each run, find the ONE state JSON newer
  than that run's `clear.txt`; if its name differs from the checklist's STATE_FILE, capture it
  with a single substituted STATE_FILE line and log the deviation with both block sha256s.
- **Before each pre-run:** `git branch --show-current` in the source clone must be EMPTY, and
  no state JSON may be newer than the previous capture.
- **Park any pre-existing `<repo>-main.json`** for the duration of a diff; restore it at revert.
- **Credits:** each `/deep-review` run is one Fable-model review with 8 native agents plus a
  Codex pass. 26 runs remain. Budget accordingly before starting a session.
