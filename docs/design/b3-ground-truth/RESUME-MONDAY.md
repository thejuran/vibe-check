# B3 v2.10 baseline — PAUSE STATE (2026-09-07 23:15) and resume procedure

Working note for the owner-run WAIT. Not a run artifact, not covered by the
pre-registration immutability rule. Authoritative evidence is the committed run dirs and
`RUN-METHOD-NOTES-v2.10.md`.

## Where the campaign stopped

**23 of 36 runs captured.** Paused 2026-09-07 at 23:15 local by owner choice at a clean run
boundary (13 runs captured today, all committed).

| diff | repo | captured | note |
|---|---|---|---|
| Part A (6 diffs) | triggarr / seedsyncarr / roonseek | 18/18 | **COMPLETE**; all clones restored |
| triggarr-session-rotation | ~/triggarr | 3/3 | complete, clone restored, re-pinned for diff 8 |
| triggarr-settings-form-split | ~/triggarr | 2/3 | **IN PROGRESS** — run 3 next |
| should-quiet-4, -6, -7 | ~/triggarr | 0/3 | part-B remainder |
| should-quiet-5 | ~/seedsyncarr | 0/3 | part-B remainder |

Part-B gate (checklist 3253-3296) PASSED 2026-09-07 22:01 — new-diff runs are legal.

## Live state left on disk (do not disturb)

- `~/triggarr` is **detached at 542d5dd** with the triggarr-settings-form-split patch applied.
  Live full diff sha256 `40ae123ce9910d937b8afdf51dcd98de048eec6b86bbdb4be1c0661fbc88cd91` ==
  the sealed EXPECTED_TREE_DIFF_SHA256; touched path `triggarr/templates/settings.html`. `uv.lock`
  carries `uchg`. The sentinel `.turingmind/state/.b3-inprogress` names
  triggarr-settings-form-split, start_branch=main, start_sha=f4366a2. No state JSON present.
- `~/seedsyncarr` is on `main@b00081b`, clean, no sentinel, owner's `seedsyncarr-main.json` restored.
- `~/roonseek` is on `main@680cb88`, clean, no sentinel.
- Do not `git checkout`/`switch` in `~/triggarr`, do not clear the `uchg` flag, do not delete the sentinel.

## Harness — frozen, keep it that way

Unchanged from the 2026-09-06 pause: Claude Code 2.1.261 (symlink + `DISABLE_AUTOUPDATER=1`),
codex-cli 0.153.4, vibe-check 2.9.0 cache == tag v2.9, model Fable 5.1 (saved default is
now `claude-fable-5-1[1m]`; still confirm `/model` in every source session). No `claude update`,
`npm update -g`, `brew upgrade`, or vibe-check resync until all 36 runs commit.

## Resume — exact order (run from a guide session in `~/turingmind-code-review`)

The guide-session driver is the assistant: it runs every block with `~/.b3/b3 <first> <last>`
(INNER line ranges; re-derive with `grep -n '^```' docs/design/b3-ground-truth/RUN-CHECKLIST-v2.10.md`
— numbers below are as of checklist commit debe57a, unchanged today) and prompts the owner
only for what it cannot do: launching/clearing the source session and running `/deep-review`.

1. **Part-B gate** — `~/.b3/b3 3253 3296` → expect `part-B pre-registration gate OK …`.
2. **STEP 0** — `~/.b3/b3 110 149` → expect `STEP 0 OK …`.
3. **Owner: source session** in a NEW terminal: `cd ~/triggarr`, `claude --version` == 2.1.261,
   `claude`, `/model` → Fable 5.1, confirm `/vibe-check:` autocompletes, `/clear`.
   **The assistant verifies a live `claude` process whose cwd is `~/triggarr` BEFORE the next
   step (N-09).**
4. **STEP 0.25 fingerprint** — `printf 'Fable 5.1\n' | ~/.b3/b3 164 211` (new calendar day AND
   any relaunch both require it).
5. **RESUME-AT-NEXT-RUN for triggarr-settings-form-split** — `~/.b3/b3 4195 4219`.
6. **Run 3**: owner `/clear`s → assistant `printf 'CLEARED\n' | ~/.b3/b3 4059 4089` → owner runs
   `/vibe-check:deep-review`, declines fixes (Skip fixes this pass → Abandon for now) → assistant
   checks the ONE fresh state JSON (N-06/N-07/N-10 drift rule) → `~/.b3/b3 4108 4155` (or the
   one-line STATE_FILE substitution if the key drifted) → revert-once `~/.b3/b3 4161 4186`.
7. **Diff 9 should-quiet-4** (triggarr, base 14eecb5): fresh `4309 4341`; runs pre/post
   `4349 4379`/`4398 4445`, `4453 4483`/`4502 4549`, `4557 4587`/`4606 4653`; revert `4659 4684`.
8. **Diff 10 should-quiet-5** (seedsyncarr, base 7035477): park `seedsyncarr-main.json` as
   `.b3-n07-parked` first; new source session + fingerprint; fresh `4807 4835`; runs
   `4843 4871`/`4890 4937`, `4945 4973`/`4992 5039`, `5047 5075`/`5094 5141`; revert `5147 5167`;
   restore the parked file.
9. **Diff 11 should-quiet-6** (triggarr, base 9bfd4a6): fresh `5284 5316`; runs
   `5324 5354`/`5373 5420`, `5428 5458`/`5477 5524`, `5532 5562`/`5581 5628`; revert `5634 5659`.
10. **Diff 12 should-quiet-7** (triggarr, base ce567d3): fresh `5782 5814`; runs
    `5822 5852`/`5871 5918`, `5926 5956`/`5975 6022`, `6030 6060`/`6079 6126`; revert `6132 6157`.
11. At 36/36: re-invoke `/julian-orchestrator:milestone` and tell it to continue past the live
    Phase-38 checkpoint so GSD executes 38-05 (scoring) and 38-06 (RESULTS-v2.10).

## Standing rules (runs 1-23)

- Never type "continue" into a stopped run (N-08). Archive via FAILED-RUN RECOVERY, rerun.
- Fix loop: "Skip fixes this pass" (4), then "Abandon for now" (3). Never finalize, never let the
  fix agent commit.
- State-key drift is expected (N-06/N-07/N-10: `<repo>-HEAD.json` or `<repo>-main.json` instead of
  `<repo>-.json`): capture the ONE JSON newer than the run's clear.txt with a single substituted
  STATE_FILE line and log both block sha256s.
- Before each pre-run: `git branch --show-current` in the source clone must be EMPTY, no state
  JSON newer than the previous capture, and a live `claude` process with cwd = the clone (N-09).
- Park any pre-existing `<repo>-main.json` for the duration of a diff; restore at revert.
- The pass-level codex record has FOUR observed shapes (`codex_joined: true`; `codex: {joined,…}`;
  `codex: {status,…}`; absent even when a codex-adversarial finding exists) and two timestamp
  formats — 38-05 must read all of them.
- The ignore-list caveat for the SessionStart hook: its "checkpoint … Phase 33" line is stale
  HANDOFF.json noise; the live checkpoint is Phase 38.
- Credits: each `/deep-review` is one Fable review with 6-8 native agents plus a Codex pass.
  13 runs remain.
