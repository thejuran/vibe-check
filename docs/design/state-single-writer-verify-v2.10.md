# State single-writer verify (v2.10 Phase 40, DIET-03)

**Outcome: dissolved.** On the restructured flow, one sentence writes `state.passes`:
`plugins/vibe-check/phases/review/45-persist.md:45` (W1, Phase 4.5). The second writer (W2, Phase 5)
was removed under D-16. The field it wrote had no reader.

This record follows the evidence → method → outcome shape of the run-method notes. The greps are
printed so anyone can re-run them. They were re-run on the shipped tree for this record (2026-09-28,
commit `f5f514b`; the plugin prose last changed at `d05ecb6`).

## 1. Question

Does the restructured flow keep the Phase 4.5 → Phase 5 state single-writer property? DIET-03 was
re-scoped on 2026-09-05 to verify-only. The deliverable is this record, not new state-machine work.

## 2. Method

List every state-mutating sentence across both command spines and every `phases/**` sub-file. Assert
how many write `state.passes`, and which one. This is the method chosen at plan time (Claude's
Discretion, in the enumerate-and-assert form from RESEARCH Q5). It can be run again, because the
greps are below.

**What the method proves:** the plugin's **prose** has exactly one instruction that writes
`state.passes`. Pair that with the schema check below: `state_shape.py --schema future` passes on
every state produced by real runs on the restructured plugin. Together they show the envelopes those
runs produced carry no removed field.

**What it does not prove:** how the model behaves at runtime in cases no fixture or run exercised.
This is static enumeration plus a schema check on produced states. It is **not** a live measurement
of the property.

## 3. Evidence before (pre-phase revision `7a386ed`)

| Writer | Site at `7a386ed` | Phase | What it wrote |
|---|---|---|---|
| W1 | `commands/review.md:993` | 4.5 | the pass entry, appended to `state.passes` |
| W2 | `commands/review.md:1086-1087` | 5 | applied fix SHAs, to `passes[-1].fixes_applied[]` |
| W2 restated | `commands/review.md:1080` | 5 | inline fallback "MUST append" to the same field |

**The removed field had no reader.** At `7a386ed`, `git grep -n fixes_applied 7a386ed --
plugins/vibe-check` returns only `commands/review.md:1075`, `:1080` and `:1086`: the two write
instructions and the sentence that justifies them. `score.py` never mentioned the field.
Carry-forward is based on content: `score.py:487 carry_forward_status` at `7a386ed` (`:525` today)
returns `fixed-since-last` for a null canonical line and otherwise compares content. Phase 0.5 reads
only the `pass_number`-side fields (`pass_number`, `head_sha`, `findings`). So the justification
("so Phase 0.5 carry-forward sees them") described a dependency that did not exist.

## 4. Change (D-16)

- W2 and the inline-fallback append were deleted in plan 40-11 (commit `3a53948`). The sentences had
  moved to `phases/review/50-fix-loop.md:75` and `:81` during the restructure.
- The pass-entry envelope no longer has the field.
- `plugins/vibe-check/scripts/fixtures/future-schema.json` pins the new shape. It lists
  `fixes_applied` under `pass_forbidden`. `state_shape.py --schema future` enforces it.
- `plugins/vibe-check/scripts/fixtures/archive-compat-schema.json` still lists `fixes_applied` as
  optional. The 37 sealed Phase-38 states therefore validate unchanged. The historical schema was
  not tightened, and the future one was not loosened.

## 5. Evidence after (current tree)

**Grep 1: every state-related sentence**

```bash
grep -rnE 'write.*state|state file|STATE_FILE|state\.passes' \
  plugins/vibe-check/commands/ plugins/vibe-check/phases/
```

It returns 47 lines. After triage, the only lines that mutate state are these four sites:

| Site (under `phases/`) | Phase | Trigger | Kind |
|---|---|---|---|
| `review/45-persist.md:45` | 4.5 | every review, after Phase 4 | **W1, the one `passes` writer** |
| `review/45-persist-all.md:10` | 4.5, nested | `$ALL_MODE` set | adds fields to the W1 entry |
| `shared/90-finalize.md:39` | finalize | Medium "Dismiss" answers | root-field write |
| `shared/90-finalize.md:46` | finalize | finalize completes | archive (`mv`), not a write |

Payloads, in the same order:

- W1 appends the pass entry to `state.passes` and writes the file. The key set is stated once in
  that file.
- The `--all` extension adds `cap_applied`, `chunk_total` and the capped chunks to the SAME W1
  entry. It is not a parallel write.
- Finalize's Dismiss path writes `medium_acknowledgments` at the state ROOT, never under `passes`
  (`:43` repeats the location).
- Finalize archives with `mv "$STATE_FILE" "$STATE_FILE.archived-<date>"`.

The other lines are path binding (`phases/review/05-state.md`, `05-state-all.md`), reads
(`05-state.md:25-27`, `90-finalize.md:12-17,55,61`), routing text in both spines, or statements that
something does NOT write state (`03-estimate-gate.md:55,74,78`, `00-contract.md:12`).
`45-persist.md:8` names W1 as the single writer, and `40-render.md:78` routes to Phase 4.5.
`phases/review/50-fix-loop.md` matches only at `:89`, which routes to finalize. The fix loop writes
nothing to state.

**Grep 2: writes to `passes` specifically**

```bash
grep -rnE 'state\.passes' plugins/vibe-check/commands/ plugins/vibe-check/phases/ \
  | grep -iE 'append|write'
```

It returns 3 lines: `45-persist.md:45` (W1), `45-persist-all.md:10` (the W1 `--all` extension), and
`90-finalize.md:61`. The last one is a **reader**. It names
`state.passes[-1].medium_acknowledgments` as "a per-pass path nothing writes". The same grep
returned 5 lines before 40-11. The difference is exactly the two Phase-5 writes.

**Grep 3: the removed field**

```bash
grep -rn 'fixes_applied' plugins/vibe-check/
```

No hits in `commands/` or `phases/`. The only hits are the enforcement side:
`scripts/fixtures/future-schema.json:11` (forbidden),
`scripts/fixtures/archive-compat-schema.json:8` (optional, archive only), and
`scripts/test_state_shape.py`, which asserts both.

**Schema check on produced states** (re-run for this record):

- All 10 states written by the restructured plugin on owner runs pass `state_shape.py <state.json>
  --schema future` with exit 0. That is batch 2 (2), batch 3 (2) and the final set of 3 runs per
  diff (6), under `docs/design/b3-ground-truth/runs-v2.10-phase40/`. None contains `fixes_applied`.
- All 37 sealed Phase-38 states under `docs/design/b3-ground-truth/runs-v2.10/` pass `--schema
  archive-compat` with exit 0.
- Executable counter-check from 40-11: take a batch-2 W1-written state and apply the old W2 write to
  it. `--schema future` then exits 1 with `forbidden key in pass entry: fixes_applied`.

**Single-writer assertion:** `phases/review/45-persist.md` (Phase 4.5, W1) is the single surviving
writer of `state.passes`.

## 6. Outcome

**Dissolved.** The property holds because the second writer is gone, not because any state-machine
work coordinated two writers. **Nothing returns to backlog 999.8.** D-16 fixed this outcome: the
removed field had no reader, so no coordination problem is left to solve.

**The trade-off:** the state file no longer records which fix commits went with a pass. The fix
commits are still easy to find in git history by their `fix(review-pass-N):` messages. A future "fix
provenance in state" feature would be a **new** backlog item with its own reader. It would not
restore this field.
