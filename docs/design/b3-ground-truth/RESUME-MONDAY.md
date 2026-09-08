# B3 v2.10 baseline — COMPLETE (2026-09-08)

Working note for the owner-run WAIT. Not a run artifact, not covered by the
pre-registration immutability rule. Authoritative evidence is the committed run dirs and
`RUN-METHOD-NOTES-v2.10.md`.

## Status

**36 of 36 runs captured and committed.** The WAIT is over.

| diff | repo | captured |
|---|---|---|
| Part A (6 diffs) | triggarr / seedsyncarr / roonseek | 18/18 |
| triggarr-session-rotation, triggarr-settings-form-split, should-quiet-4, -6, -7 | triggarr | 15/15 |
| should-quiet-5 | seedsyncarr | 3/3 |

Every source clone is restored to `main` (triggarr f4366a2, seedsyncarr b00081b, roonseek
680cb88), no sentinels, no `uchg` flags, owner state files restored. The sealed v2.9 `runs/`
tree is byte-identical to tag v2.9.

## Harness — still frozen until 38-05/38-06 land

Claude Code 2.1.261 (symlink + `DISABLE_AUTOUPDATER=1`), codex-cli 0.153.4, vibe-check 2.9.0
cache == tag v2.9. Keep the freeze until scoring has read every state file; scoring reads the
committed archive, not the live harness, so lifting it afterwards is safe.

## Next

1. In the guide session: `/julian-orchestrator:milestone`. It will find the live Phase-38
   checkpoint (STATE.md: executing, plan 5 of 6). Tell it to continue: GSD's executor runs
   38-05 (scoring against BOTH sealed key blobs) and 38-06 (`RESULTS-v2.10.md`).
2. 38-05 parser requirements gathered during the campaign (see RUN-METHOD-NOTES for detail):
   the pass-level codex record has at least SIX shapes including a plain string and outright
   absence; timestamps come in two formats; one finding had an empty title; state keys drifted
   to `<repo>-HEAD.json` on two runs (captured via the recorded one-line substitution).
3. The guide repo has ~110 unpushed commits on feat/v2.9 — push when ready.

## Deviations logged this campaign

N-09 (fingerprint attested before the source session existed, no run affected), N-10
(state-key drift on roonseek), plus the codex-record schema and empty-title observations.
