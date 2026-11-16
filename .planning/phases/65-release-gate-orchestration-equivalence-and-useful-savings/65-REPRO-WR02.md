# Phase 65 — WR-02 reproduction (D-07)

**1 place walked (the GSD state-key fence, `05-state.md`), on 2 revisions. Reproduced on the candidate as `wrong-file`: phase B's Finalize closes on phase A's findings; 2.14.1 under the same standard stops instead.**

- **Date:** 2026-11-15
- **HEAD when recorded:** `a6d29d29aa9092a855f39407e61c8bf1231a6bb9` (branch `feat/v2.15-phase-65`; its `plugins/` tree is the Phase 63 code, the release candidate's base). Compared with tag `v2.14.1` (`dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4`).
- **Scope of evidence:** local runs only. No live review, no paid run, no network. Every fence was taken from the instruction file at that revision (working tree for the candidate, `git show v2.14.1:<path>` for 2.14.1) and run in a scratch folder or a throwaway `gitfixture` repo; nothing ran in the real checkout.

## Repro standard

The Phase 60 / 63 fresh-shell standard (63-REPRO.md "Repro standard"), applied to the one flagged name:

1. **Fresh run.** Each Bash block runs as its own shell, the way each Bash call runs during a review, found in the real file by a piece of its own text. Where the instruction tells the model to type in a printed literal (`STATE_FILE=` in the candidate, the three `"<true|false>"` slots), it is typed in. `PHASE_ID` is not supplied: no fence sets or prints it; `00-scope.md` (~line 125) sets it in prose only.
2. **Control run.** The same blocks with `${PHASE_ID}` typed in as the model would after following `00-scope.md:125` (`01-a`, then `02-b`), phase B's bind and Finalize in one shell.
3. **Outcome class** by `test_cross_call_vars.classify` (stop / wrong-file / ignored-setting / harmless).
4. **Environment.** Walk A: `env -i` with only `PATH=/usr/bin:/bin`, `HOME`, `TMPDIR` (private) and `VC_ROOT` (the plugin folder at that revision), in an empty scratch folder. Walk B: `PATH`, `VC_ROOT`, `TMPDIR` and the null global/system git config only (as `test_cross_call_vars.ShellRun`), in a temp repo. For 2.14.1, `VC_ROOT` is a `git archive v2.14.1 plugins/vibe-check` extract, so its own helpers run.

Phase A's saved progress is the real-shaped fixture `scripts/fixtures/phase45-loop-state.json` (via `test_carry_state.load_fixture`) with decisions recorded through `carry_state.record_decisions` — the same construction as `test_finalize_card.py::_write_route_state`. Two variants: every open finding decided, and one finding decided. The Write tool step (phase A's pass write) is simulated by writing that JSON to the printed path.

## Walk A — mechanism

| Revision | Fence (needle `STATE_FILE=".turingmind/state/format-53/${PHASE_ID}`) | Exit | Printed |
|----------|-------------|------|---------|
| candidate (HEAD) | bind both paths, unsafe-name guard, print both | 0 | `LEGACY_STATE_FILE=.turingmind/state/.json` / `STATE_FILE=.turingmind/state/format-53/.json` |
| v2.14.1 | bind both paths only (no guard, no print lines) | 0 | nothing |

The candidate's guard checks only shell-live characters; an empty id passes it and the fence prints a key named `.json`. `scripts/statepath.py::_resolve_gsd` refuses an empty id (`REASON_MISSING_COMPONENT`), but the fence does not call it. 2.14.1 prints nothing, so a fresh shell has no literal to carry at all.

## Walk B — two-phase chain

Temp repo: `.planning/phases/01-a/`, `.planning/phases/02-b/`, `src/a.txt`, one commit.

**Candidate (HEAD).**

| | All open findings decided | One finding decided |
|---|---|---|
| Phase A printed `STATE_FILE=` | `.turingmind/state/format-53/.json` | same |
| Phase B printed `STATE_FILE=` | `.turingmind/state/format-53/.json` | same |
| Same path for both phases | yes | yes |
| Phase B Finalize-inputs (literal substituted, slots `false`): exit | 0 | 0 |
| Phase B `action` / `next` | `write` / `write-review-md` | `medium-ack-loop` / `finalize-card` |
| Phase B counts (cw / medium / nv) | 0 / 0 / 0 | 0 / 1 / 0 |
| Phase B report entries | 2 (phase A's decisions) | — (card opens on phase A's medium) |
| A pass-2 state write for B would overwrite A's file | yes (B's key is A's file, bytes unchanged until B writes) | yes |
| Control (01-a / 02-b) phase B `next` | `stop-no-state` (B has no passes yet) | `stop-no-state` |
| Files under `.turingmind/` fresh vs control | `format-53/.json` vs `format-53/01-a.json` | same |
| `classify` | `wrong-file` | `wrong-file` |

Phase B's close-out reads phase A's saved progress: with A's findings all decided, B's Finalize decides `write-review-md` and would write an APPROVED REVIEW.md for phase B built from phase A's findings and decisions, then archive A's state as B's. That is a **wrong close**. With A's findings partly decided, B's close-out card asks the owner about A's findings. Any review pass on B writes to the same path, so B's pass replaces or folds into A's saved progress. The overwrite was shown by path identity; Phase 4.5's write itself was not run.

**v2.14.1.** The phase A and phase B fences each exit 0 and print nothing. The later fences read `"$STATE_FILE"` as a shell variable, empty in a fresh shell, and 2.14.1 has no instruction to substitute a printed literal:

- `[ -f "$STATE_FILE" ]` → absent, so `state_file_present` is false; `finalize_gate.py` (2.14.1) on those flags returns `{"action": "error", "reason": "no prior review passes"}` → "No prior review passes." stop.
- The counts fence (`carry_state.py finalize-counts --head-blobs "<printed BLOBFILE>" < "$STATE_FILE"`), with `BLOBFILE` substituted and `{}` written to it, exits 1: `bash: line 1: : No such file or directory`, then "I'm uncertain about Finalize mode — carry_state.py failed; nothing was written or archived."

Under the fresh-shell standard 2.14.1 fails closed (a stop, nothing written); it does not close phase B on phase A's findings. 2.14.1's fence-side state writes (record-decisions, record-fix-verdicts) also read the empty `"$STATE_FILE"` variable and fail; its Phase 4.5 pass write is a Write tool step at whatever path the model holds, which this walk cannot show. So backlog 999.38's "none is a regression from 2.14.1" does not hold for WR-02 under this standard: the candidate's printed `STATE_FILE=` literal (added by the Phase 63 cross-call fixes) is what turns an empty id from a stop into a shared file.

## Realism caveat

- The walk is the worst case: the fence as written, with no `PHASE_ID`. `test_cross_call_vars.py` (~line 1236, `STATE_SETTERS`) types `${PHASE_ID}` as `02-code-review`, because a live model following `00-scope.md:125` ("Set `$PHASE_ID = $(basename "$PHASE_DIR")`") usually substitutes the name before running the fence. WR-02 happens only when the model runs the fence without typing the id in, which no live run has been seen to do.
- 2.14.1's real behaviour depended on the model carrying the path in its own reasoning; the fresh-shell walk shows only what its fences do, not what a model holding the path would have done there.
- The D-02 live smoke does not run the GSD route, so this release gate has no live observation of it either way.

## Script

- `/private/tmp/claude-501/-Users-julianamacbook-turingmind-code-review/1848eafc-2bdb-4e56-aba7-e76f98c7c01e/scratchpad/wr02_repro.py`
- sha256 `78e0d2fd7173c3728ea34b424ef6fdc18a0252fa363bde2f027b565df0fa1732`
- Run: `python3 wr02_repro.py <repo-root> <out.json>`; raw result `wr02_result.json` alongside it.
