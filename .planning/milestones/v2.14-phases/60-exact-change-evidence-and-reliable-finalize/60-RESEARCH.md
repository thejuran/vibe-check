# Phase 60: Exact change evidence and reliable Finalize - Research

**Researched:** 2026-10-29
**Domain:** unified-diff parsing for change ranges (score → carry → card chain); cross-Bash-call temp-path discipline in orchestrator prose (Finalize)
**Confidence:** HIGH (every load-bearing claim below was reproduced in this session against git 2.55.0 / gh 2.86.0 / the repo at `554ee83`)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Carried forward (locked — do not re-litigate)
- Reproduce first on current code: 999.24 (a real `git diff` shows default-context ranges ~8 lines wide and a pure deletion read as an ordinary hunk) and 999.25 (a fresh-shell fence walk sees an empty `$BLOBFILE`). Record each verdict before any fix lands; a non-reproducing path is recorded and dropped, never replaced with invented work.
- Every fix: failing-before/passing-after fixture plus a mutation check that trips it (mutation-test every guard; no decorative locks). `stable_hash` / GOLDEN_DIGEST frozen. Single-writer rule for `decisions` unchanged.
- Nearby window = symmetric 5 lines, one constant shared with the re-check trigger (57 D-14). Deletion-only rule `+T,0` → `[max(T,1), T+1]` stays the documented semantics.
- No-write-on-failure and independent fix verification (`verified_blob == head_blob`, Phase 56) are not weakened.
- Printed-path convention (Phase 58): a temp file prints `NAME=<path>` when created and later fences reuse the literal path, never `"$NAME"`.
- No growth per round: work is added only for a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, or broken required workflow. Live or paid checks need a separately approved, bounded proposal.

#### Range construction
- **D-01:** Ranges are built from the actual `+` / `-` line markers of each hunk, not from git's display-context setting. Reason: `gh pr diff` has no context/`-U0` option, so marker-based construction is the only approach that works the same on every route. Whether this lives in a small deterministic helper (preferred: mechanical work out of prose, consistent with the Lean-orchestration direction) or in score.py is Claude's discretion. It must not add an agent.
- **D-02 (IN-04 folded in, owner 2026-10-29):** A replace hunk that removes more lines than it adds (net deletion, e.g. `-10,3 +10,1`) also covers the new-side line just after the hunk, matching the pure-deletion rule's `T+1`. Reason: once ranges are exact, this edge becomes a reachable silent keep at the 5-line boundary. Same range rule, with its own failing-first fixture and mutant.
- **D-03:** Required end-to-end fixtures run a real `git diff` (in a temp repo) through the actual range builder and assert the resulting ranges for ordinary, deletion-only, insertion, net-deletion replace and relocated-finding hunks, including an at-boundary (reopens) and just-outside (keeps) pair (SC1/SC2). Hand-built range dicts don't count as proof for EVID-02.
- **D-04:** Audit for any other 3-line-context assumption (e.g. silenced-marker windows, re-check trigger, incremental `$LAST_REVIEWED_SHA..HEAD` + staged + unstaged diff in `05-state.md`, `--all` reruns). Fix each one or record why it's unaffected (EVID-03).

#### Route coverage
- **D-05 (owner 2026-10-29):** The PR route is proven with a checked-in real PR-format patch (captured once) run through the same range builder. The phase report states plainly that the live `gh pr diff` fetch was not exercised. No network in the suite; no live PR check required.
- **D-06:** Default, GSD, range and `--all` routes each get a fixture through the same builder, or an explicit "unsupported fixture" record with the reason (e.g. `--all` has no diff on pass 1; its incremental rerun diff, if any, is covered). Silent omission doesn't count.

#### Finalize failure and retry
- **D-07 (owner 2026-10-29):** When `$BLOBFILE`'s path is missing/empty or the counts/gate step fails, Finalize rebuilds the HEAD fingerprints from current code ONCE in the same session (the rebuild is the snapshot-freshness revalidation) and continues only if the rebuild succeeds. A second failure stops with one plain sentence: nothing was written and the owner can run `--finalize` again. No partial REVIEW.md, archive or decision write on any failed attempt.
- **D-08:** A step the owner refused (permission denied) is not auto-retried. It stops the attempt with the same plain no-write message. The automatic rebuild covers only a lost or empty path or a failed step.
- **D-09:** `BLOBFILE=<path>` is printed when created and reused literally by the counts fence, the rows fence and the re-run-counts step (`90-finalize.md` lines ~16, ~85, ~249). A fresh-shell walk test covers every Finalize fence, and a mutant that reverts to `"$BLOBFILE"` must trip it (FINL-01).

#### Cycle bound
- **D-10 (owner 2026-10-29, same as Phase 59 D-08):** One cycle = build → one review (code-review + verify-work) → ONE fix pass limited to reproduced findings in the four qualifying classes → confirmation by each fix's before/after fixture, its mutant and the full offline suite. No second review round. Everything else is carried with rationale. A wrong-keep still open at the end closes the phase "with known limit" (backlog entry with its repro), and Phase 61's release record names it.

### Claude's Discretion
- Where the range builder lives (new helper script vs score.py vs carry_state), its input and output shape, and how prose hands it the raw diff, all within the no-new-agent rule.
- How the fresh-shell walk test is structured (e.g. extracting fences from `90-finalize.md` and running each in a separate `bash -s`).
- Exact wording of the plain stop message.
- Where reproduction verdicts are recorded (e.g. `60-REPRO.md`, as in Phase 59).

### Deferred Ideas (OUT OF SCOPE)
- Phase 59 residuals WR-01 (own-line spot omitted from the card wording) and WR-02 (deferred-by note lost from pass 3): already parked to 999.23 by the owner, not in this phase.
- 57 IN-01/IN-02/IN-03/IN-05 (presentation or unlikely-shape items): stay carried. Only IN-04 is folded in (D-02).
- Broader Finalize extraction into a script: Lean orchestration milestone.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EVID-01 | Nearby/in-diff ranges come only from added/deleted lines; boundary edit reopens, just-outside keeps | Marker-walk algorithm (Pattern 1); repro table shows default context widens every hunk by 3 lines each side; `_NEARBY_LINES = 5` in `score.py:177` is the single window constant |
| EVID-02 | Real-`git diff` fixtures for ordinary, deletion-only, insertion, relocated (+ net-deletion per D-02) | Repro table below gives the exact `-U0` header for each shape, i.e. the expected ranges; `test_decision_continuity.py` harness (`run_pass`, `decide_on`, `e2e_gate`, `base_file`) and `gitfixture.py` are the reuse points |
| EVID-03 | Every route uses exact ranges or reports an unsupported fixture; no other 3-line assumption | Route table (Pattern 3); **PR `--patch` is a 34-commit series, not a cumulative diff** (new finding); GSD/incremental mixes coordinate spaces; `replay.hunk_ranges` is deliberately context-inclusive and must stay so |
| FINL-01 | Blob-file path printed and literally reused; fresh-shell walk reaches counts → gate → report | `$BLOBFILE` is never `mktemp`'d anywhere today (Write-tool path is invented by the model); `check_printed_paths` only scans the card section; `TestSubsetDispatchWalk` (`test_fix_loop_card.py:2630`) is the walk template; **`$FINALIZE_GATE_INPUT_JSON` is a second cross-call variable on the same path** |
| FINL-02 | Missing path / failed / refused step stops with no write; retry revalidates freshness | `carry_state.py` refuses `--head-blobs ""` and unparsable files (exit 2, verified); `finalize_gate.py` on empty stdin crashes with a traceback (exit 1) — fails closed but not cleanly; retry must mint a NEW blob file (stale-literal pitfall) |
</phase_requirements>

## Summary

Both backlog items reproduce on current code. For 999.24, a real `git diff` of a 30-line file shows every edit shape widened by git's 3 context lines: deleting line 9 yields `@@ -6,7 +6,6 @@` (new-side 6–11) instead of `-U0`'s `@@ -9 +8,0 @@`, so the documented deletion rule in `30-collect-score.md` never fires and the effective nearby window is ~8 lines. Two edits five lines apart (lines 5 and 10) merge into one default-context hunk `@@ -2,12 +2,12 @@`, so a header-only parser cannot even separate them. A marker walk (track the new-side cursor through ` `, `-`, `+` body lines) produces exactly the `-U0` ranges from ANY context width, which is why D-01 chose it — and it is the only option that works for `gh pr diff`, which has no context flag (verified: `gh pr diff --help` lists only `--color`, `--name-only`, `--patch`, `--web`).

Research surfaced one route-level defect the CONTEXT did not name: the PR route runs `gh pr diff <ref> --patch`, and on this repo's PR #5 that emits **34 mbox commit patches (72 `diff --git` sections)** rather than one cumulative diff (34 sections without `--patch`). Hunk line numbers in each commit patch are relative to that commit's parent, so ranges built from it are in mixed coordinate spaces regardless of context width. The plain `gh pr diff <ref> --color never` output is the cumulative base…head diff and is the correct range source. Similarly, the GSD route (`$PHASE_START..HEAD` + staged + unstaged) and the incremental rerun (`$LAST_REVIEWED_SHA..HEAD` + staged + unstaged) concatenate diffs whose new sides are HEAD, index and working-tree coordinates respectively; a single `git diff <base-commit>` (commit vs working tree) gives one consistent coordinate space. These must be reproduced before being fixed (scope rule), but each is a candidate silent keep, not just over-asking.

For 999.25: `$BLOBFILE` is not only unprinted — no fence creates it at all. Step 1 says "serialize … to `$BLOBFILE` with the Write tool" but no `mktemp` exists, so the model must invent a path, and later fences read `"$BLOBFILE"` from a shell that never set it. `carry_state.py` then refuses (`read_json_file("")` → `None` → `REASON_HEAD_BLOBS`, exit 2) and Finalize stops without writing — safe, but a broken required workflow. The fresh-shell walk will also hit `$FINALIZE_GATE_INPUT_JSON`, a second shell variable the gate fence reads across calls; empty stdin makes `finalize_gate.py` crash with a `JSONDecodeError` traceback (exit 1). It fails closed through the fence's `else` arm, but SC4 ("reaches counts → gate → report") cannot pass in a fresh shell until that input is also carried literally.

**Primary recommendation:** Add one pure, stdlib-only helper `plugins/vibe-check/scripts/diff_ranges.py` (stdin unified diff → stdout `{file: [[start,end],…]}`, exit 2 on structural refusal) implementing the marker walk with D-02's net-deletion `+1`; point every range-building route at a single consistent-coordinate diff command run with `--no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/`; leave `replay.hunk_ranges` untouched. In `90-finalize.md`, add a `mktemp` fence that prints `BLOBFILE=`, reuse the literal in all three consumers, carry the gate input as a literal too, mint a fresh blob file on the single automatic retry, and extend `check_printed_paths` + a `TestSubsetDispatchWalk`-style fresh-shell walk over the whole file.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Run git / gh to obtain the diff text | Orchestrator prose (Bash fences) | — | Established split: prose runs git, scripts are pure (`score.py` "no git/file/shell I/O") |
| Parse diff text into exact change ranges | New pure helper `scripts/diff_ranges.py` | — | Deterministic, unit- and fixture-testable; keeps mechanical work out of prose (D-01 preference) |
| `in_diff`, nearby window, `snapshot.nearby_at`, re-check trigger | `score.py` (`_line_in_ranges`, `_nearby_changed`, `_NEARBY_LINES = 5`) | — | Unchanged; envelope key `changed_line_ranges` keeps its `{file: [[s,e]]}` shape |
| HEAD fingerprints (blob file content) | Orchestrator prose (validated git calls + Write tool) | — | Unchanged ownership; only path creation/printing moves into a fence |
| Counts / rows / gate decisions | `carry_state.py`, `batch_card.py`, `finalize_gate.py` | — | Unchanged; already fail closed on absent/invalid blob file |
| Retry-once and stop message | Orchestrator prose (`90-finalize.md`) | — | D-07/D-08 behavior is a prose control-flow rule, locked by prose tests and a fence walk |

## Standard Stack

No external packages. This phase is stdlib Python + git + existing test infrastructure.

### Core
| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Python stdlib (`json`, `re`, `sys`) | 3.14.5 (local) [VERIFIED: `python3 --version`] | The range builder | Every helper in `scripts/` is stdlib-only |
| git | 2.55.0 [VERIFIED: `git --version`] | Produces the diffs; used in temp-repo fixtures | Already required |
| gh | 2.86.0 [VERIFIED: `gh --version`] | PR route only; never run in the suite (D-05) | Already required |
| pytest | 9.0.3 [VERIFIED: `pytest --version`] | Test runner (bare `pytest`, per project memory) | Existing suite (~3600 tests, ~165 s full run per 59-REPRO) |

### Supporting (in-repo, reuse)
| Asset | Purpose | When to Use |
|-------|---------|-------------|
| `scripts/gitfixture.py` (`make_repo`, `git`, `helper_env`) | Isolated temp repos (null global/system git config) | Every real-`git diff` fixture |
| `test_decision_continuity.py` (`base_file`, `run_pass`, `decide_on`, `record_of`, `e2e_gate`, `relocate_decided`, `deletion_hunk_ranges`) | Real score → carry → card → gate chain | SC1 boundary pair and relocated-finding fixtures |
| `test_fix_loop_card.py::TestSubsetDispatchWalk` (`_run_fresh`, `_literal`, `_printed`) | Fresh-shell fence walk with literal path substitution | FINL-01 Finalize walk |
| `test_finalize_card.py::check_printed_paths` + `MKTEMP_RE` | Printed-path prose lock | Extend scope to the counts step / whole file |
| `test_mktemp_template.py` | Every `mktemp` uses `"${TMPDIR:-/tmp}/…XXXXXX"` | Applies automatically to the new BLOBFILE fence |

**Installation:** none.

## Package Legitimacy Audit

Not applicable — this phase installs no external packages (stdlib, git and gh only; all already present). slopcheck not run.

## Reproduction Evidence (gathered this session)

Real `git diff` vs `git diff -U0` on a 30-line file `1..30` (isolated config) [VERIFIED: scratch repro, git 2.55.0]:

| Shape | Default `git diff` header | `-U0` header | Exact ranges the builder must emit |
|-------|---------------------------|--------------|------------------------------------|
| delete line 9 | `@@ -6,7 +6,6 @@` | `@@ -9 +8,0 @@` | `[[8, 9]]` (deletion rule, T=8) |
| replace line 10 | `@@ -7,7 +7,7 @@` | `@@ -10 +10 @@` | `[[10, 10]]` |
| insert after 15 | `@@ -13,6 +13,7 @@` | `@@ -15,0 +16 @@` | `[[16, 16]]` |
| delete lines 10–12 | `@@ -7,9 +7,6 @@` | `@@ -10,3 +9,0 @@` | `[[9, 10]]` (deletion rule, T=9) |
| replace 10–12 with 1 line (net deletion) | `@@ -7,9 +7,7 @@` | `@@ -10,3 +10 @@` | `[[10, 11]]` (D-02: `+1` after the hunk) |
| edits at lines 5 and 10 | `@@ -2,12 +2,12 @@` (one merged hunk) | `@@ -5 +5 @@`, `@@ -10 +10 @@` | `[[5, 5], [10, 10]]` |

Diff-text hazards [VERIFIED: same repro]:
- A deleted content line `-- x` prints as `--- x`; an added `++ y` prints as `+++ y` — **inside a hunk body they look like file headers**.
- A path containing a space prints as `+++ b/a b.txt<TAB>` (trailing tab).
- `diff.mnemonicPrefix=true` → `+++ w/f.txt` / `--- i/f.txt`; `diff.noprefix=true` → `+++ f.txt`. `--src-prefix=a/ --dst-prefix=b/` restores `a/`/`b/` under both.
- `color.ui=always` wraps headers in ANSI codes (`\x1b[36m@@ … @@\x1b[m`); `--no-color` removes them.

PR route [VERIFIED: `gh pr diff 5`]: `--patch` → 34 `From <sha>` mbox headers, 72 `diff --git` sections; plain → 0 mbox headers, 34 sections (cumulative).

Finalize [VERIFIED: code read + runs]:
- `carry_state.parse_argv` accepts `--head-blobs ""`; `read_json_file("")` → `None` → `refused: head-blobs file is missing or not a JSON object`, exit 2. An unquoted empty `$BLOBFILE` would drop the argument → usage refusal, also exit 2.
- `printf '' | python3 finalize_gate.py` → uncaught `JSONDecodeError` traceback, exit 1; `echo '{}' |` → `{"action": "refuse", …}` exit 0.
- No `BLOBFILE=$(mktemp …)` exists anywhere in `plugins/vibe-check/` [VERIFIED: grep]. Consumers: counts fence (line 16), rows fence (line 85), step-3 re-run (line 249). Cross-call variables read by Finalize fences without being set in the same fence: `BLOBFILE`, `FINALIZE_GATE_INPUT_JSON`, plus `VC_ROOT`/`STATE_FILE` (the latter two are substituted resolved paths by convention, `01-bootstrap.md`).

## Architecture Patterns

### System Architecture Diagram

```
 route (Phase 0 / 0.5)                         range source (ONE diff, new side = working tree / PR head)
 ───────────────────────                       ──────────────────────────────────────────────────────────
 default ─────────────► git diff HEAD ───────────────┐
 GSD (pass 1) ────────► git diff $PHASE_START ───────┤      (all git calls: --no-color --no-ext-diff
 any route, pass ≥2 ──► git diff $LAST_REVIEWED_SHA ─┤       --src-prefix=a/ --dst-prefix=b/)
 range a..b ──────────► git diff a..b ───────────────┤
 PR ──────────────────► gh pr diff <ref> --color never (cumulative, NOT --patch)
 --all ───────────────► (no diff) → changed_line_ranges = {}   [explicit "unsupported fixture" record]
                                                     │
                                                     ▼
                                   diff_ranges.py (pure parse, stdin → stdout)
                                     ├─ structural problem / mbox series / @@@ → exit 2 → review HALTS
                                     └─ {file: [[s,e],…]}  (exact: +lines, deletion points, D-02 +1)
                                                     │
                                                     ▼
                         envelope.changed_line_ranges → score.py
                           ├─ in_diff (+20)                 _line_in_ranges
                           ├─ re-check trigger              _independent_trigger → _nearby_changed (±5)
                           └─ decision re-ask               snapshot.nearby_at (same ±5)
                                                     │
                                                     ▼
                         state → carry_state / batch_card / finalize_gate (unchanged)

 Finalize (90-finalize.md), each Bash call a fresh shell:
   [A] mktemp → print BLOBFILE=<p> ─► Write tool fills <p> with validated {file: blob}
   [B] counts fence reads "<p>" literal ── fail ─► retry once: new [A]+[B] ── fail/refused ─► stop, nothing written
   [C] gate fence reads its input literally (not "$FINALIZE_GATE_INPUT_JSON" from another call)
   [D] write → REVIEW.md + archive    |  card → rows fence reads "<p>" → … → step-3 re-run counts reads "<p>"
```

### Recommended Project Structure
```
plugins/vibe-check/scripts/
├── diff_ranges.py              # NEW: pure marker-walk range builder (CLI + importable function)
├── test_diff_ranges.py         # NEW: unit tests + real-git-diff fixtures per shape and per route
├── fixtures/pr-cumulative.diff # NEW: one real `gh pr diff <ref> --color never` capture (D-05), source noted
├── test_decision_continuity.py # EXTEND: SC1 boundary pair + relocated finding via real git diff → builder → chain
├── test_finalize_card.py       # EXTEND: printed-path lock covers the counts step; Finalize fresh-shell walk
└── test_nv_render.py           # UPDATE: DELETION_RANGE_PHRASES prose lock follows the new 30-collect-score wording
plugins/vibe-check/phases/
├── review/30-collect-score.md  # "changed-line ranges" bullet → run the helper on the route's range diff
├── review/00-scope.md          # range-source command per route (PR: cumulative)
├── review/05-state.md          # step 3: range source for the incremental diff
└── shared/90-finalize.md       # BLOBFILE mktemp/print fence, literal reuse ×3, gate input literal, retry-once rule
.planning/phases/60-…/60-REPRO.md  # reproduction verdicts (Phase 59 format)
```

### Pattern 1: Marker walk (the range builder core)
**What:** Walk each hunk body with a new-side cursor; record `+` lines; record deletion points; apply the deletion and net-deletion rules per contiguous change block. The header supplies only the starting new line and the body line budget.
**When to use:** Every range build, every route.
**Algorithm (prescriptive):**
1. Split input on `"\n"` only — **never `str.splitlines()`** (it also splits on `\f`, `\x1c–\x1e`, `\x85`, `\u2028`, `\u2029`, which appear in real source and would desynchronize the body count). Read stdin as bytes and decode `utf-8` with `errors="surrogateescape"` (or `"replace"`); only header lines are interpreted.
2. File header: `+++ b/<path>` (strip one trailing `\t`; `+++ /dev/null` → deleted file, no new side, skip its hunks). Quoted paths (`"b/…"` C-quoted) → unquote or refuse; recommend refuse-with-reason only if a fixture shows git emits them under `core.quotePath=false` for the paths that can carry findings (findings are already restricted to `^[A-Za-z0-9._/-]+$` elsewhere, so skipping such a file costs nothing).
3. Hunk header `^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@` (missing count = 1). Set `cursor = new_start`, `old_left = old_count`, `new_left = new_count`. **Consume body lines until both budgets reach 0** — this is what keeps `--- x` / `+++ y` content lines from being read as headers. Lines starting `\` ("\ No newline at end of file") consume no budget.
4. Body: ` ` → close any open block, `cursor += 1`, both budgets −1. `+` → record `cursor` as added, `cursor += 1`, `new_left −1`. `-` → mark deletion in the open block (`old_left −1`; cursor unchanged).
5. Closing a change block with `a` added lines starting at `s` and `d` deleted lines:
   - `a ≥ 1` → `[s, s+a−1]`; and if `d > a` (net deletion, D-02) extend to `s+a` → `[s, s+a]`.
   - `a == 0` (pure deletion; `s` = cursor = first new line after the deletion point) → `[max(s−1, 1), s]`. This is exactly the documented `+T,0 → [max(T,1), T+1]` with `T = s−1`, and reproduces `-9 +8,0 → [8,9]`, `-10,3 +9,0 → [9,10]`, `-1 +0,0 → [1,1]`.
6. A budget that goes negative, a body that ends before the budgets reach 0, a `@@@` combined hunk, or an mbox `From <40-hex> ` line → **refuse (exit 2, one-line reason on stderr)**. Output ranges sorted and merged per file; `json.dumps(…, sort_keys=True)`.

**Equivalence check to put in the tests:** for every fixture repo, `ranges(git diff) == ranges(git diff -U0) == ranges(git diff -U10)`. That single assertion is the cleanest proof that ranges are independent of display context (EVID-01), and a mutant that reads header counts instead of markers trips it immediately.

### Pattern 2: Helper invocation from prose (fail closed)
```bash
# Source: established 30-collect-score.md / carry_state.py fail-closed shape
if RANGES_JSON=$(git diff --no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/ HEAD \
                 | python3 "$VC_ROOT/scripts/diff_ranges.py"); then
  printf '%s\n' "$RANGES_JSON"     # copy verbatim into the envelope's changed_line_ranges
else
  echo "Review halted — the changed lines could not be read from the diff; nothing was scored." >&2
  exit 1
fi
```
Note `set -o pipefail` is not on by default; `git` failing upstream leaves the helper with empty stdin → it should emit `{}` for empty input (an empty diff is legitimate). If the planner wants git failures caught, run git into a printed temp file first or add `set -o pipefail` in the fence (fences run under `bash -s`).

### Pattern 3: One consistent-coordinate range source per route
| Route | Agents' diff (unchanged) | Range source (recommended) | Why |
|-------|--------------------------|----------------------------|-----|
| default (pass 1) | `git diff HEAD` + `git diff --staged` | `git diff HEAD` only | Covers staged+unstaged in working-tree coordinates; `--staged` is index coordinates (over-reach only) |
| GSD (pass 1) | `$PHASE_START..HEAD` + staged + unstaged | `git diff $PHASE_START` (no `..HEAD`) | Commit vs working tree = one coordinate space; the concatenation puts committed hunks in HEAD coordinates, which drift from working-tree lines when there are uncommitted edits above them (candidate silent keep — reproduce first) |
| any stateful route, pass ≥ 2 (05-state step 3) | `$LAST_REVIEWED_SHA..HEAD` + staged + unstaged | `git diff $LAST_REVIEWED_SHA` | Same reason |
| range `a..b` | `git diff a..b` | same command | New side = `b`, single space |
| PR | `gh pr diff <ref> --patch` | `gh pr diff <ref> --color never` (no `--patch`) | `--patch` is a per-commit series (verified 34 commits / 72 sections on PR #5); intermediate-commit coordinates are wrong for the head |
| `--all` | none | `{}` — record "unsupported fixture: `--all` forces pass 1 with an empty carry-forward on every run (`05-state-all.md` (ii)); there is no diff, `in_diff` never gates, `nearby_at` is never stamped" | D-06 explicit record |

Keep the agents' diff commands as they are unless a reproduced failure requires otherwise — changing what reviewers see is out of scope (reviewer changes are excluded).

### Pattern 4: Printed, literal BLOBFILE + single fresh retry (Finalize)
```bash
# Step 1a — create and print (new fence, before the Write)
BLOBFILE=$(mktemp "${TMPDIR:-/tmp}/vc.XXXXXX")
printf 'BLOBFILE=%s\n' "$BLOBFILE"
```
Then Write the validated `{file: blob}` JSON (or `{}`) to that printed path with the Write tool (same mktemp-then-Write shape `ANSWERFILE` already uses). Counts fence, rows fence and the step-3 re-run all substitute the literal for `"$BLOBFILE"`. Retry rule (D-07): on a counts/gate failure or a missing/empty path, run step 1 again **creating a new file and printing a new `BLOBFILE=`**, re-run counts and gate once with the new literal; second failure or any refused step (D-08) → one plain sentence, e.g. "Finalize stopped — nothing was written or archived; run `--finalize` again." The gate input should likewise be carried as a literal (inline JSON in the gate fence, or a printed `GATEFILE=` written with the Write tool) rather than `"$FINALIZE_GATE_INPUT_JSON"` set in an earlier call.

### Anti-Patterns to Avoid
- **Parsing hunk headers only** (what the prose and `replay.hunk_ranges` do): includes context, merges nearby edits, and never sees deletion points.
- **`str.splitlines()` on diff text:** splits on form feeds and Unicode separators inside content lines.
- **Treating any line starting `+++ `/`--- ` as a file header:** content lines `++ …`/`-- …` produce exactly that inside hunks.
- **Building ranges from `--patch` / multi-commit output:** each commit's coordinates differ.
- **Concatenating diffs with different new sides** (HEAD vs index vs working tree) into one range set.
- **Reusing a `BLOBFILE=` literal printed by an earlier attempt or session:** its blobs may predate a later edit and close a fix-obsolete verdict on changed code (see Pitfall 5).
- **Editing `replay.hunk_ranges`:** it intentionally reproduces how the archived B3 runs were scored ("context included", `replay.py:20-22,204`); changing it shifts baseline replay fidelity that Phase 61's release gate relies on.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Range parsing in prose | LLM-read hunk headers ("Build the ranges from each hunk's new-side header") | `diff_ranges.py` | Deterministic, testable, mutation-lockable; the LLM reading is what drifted |
| Temp repos in tests | ad-hoc `subprocess` git with the dev's config | `gitfixture.make_repo` / `git` / `helper_env` | Isolates global config (gpgsign, hooks, `diff.noprefix`, color) |
| Fresh-shell fence runner | new harness | Copy `TestSubsetDispatchWalk._run_fresh/_literal/_printed` shape | Proven Phase 58 pattern; minimal env (PATH, VC_ROOT, TMPDIR, STATE_FILE) |
| Printed-path prose lock | new regex | Extend `check_printed_paths` / `MKTEMP_RE` to the counts section (or the whole file) | Its current scope (`card_section`) is exactly why 999.25 slipped through (58 SA-01) |
| Blob-file validation | new checks | `carry_state.read_json_file` + `_is_str_map` (already refuse absent/invalid) | Already fail closed |

**Key insight:** the bug class in both items is "a fact that should be computed mechanically was left to orchestrator prose". The fix is to move the computation (ranges) or the handle (temp path) into something a test can execute in a fresh shell.

## Runtime State Inventory

Not a rename/refactor phase in the data sense, but one stored-state question is relevant:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Existing `.turingmind/state/format-53/*.json` files carry `snapshot.nearby_at` values stamped from the old (wider) ranges | None — a past over-wide stamp only ever re-asked (fail toward asking); new passes stamp from exact ranges. No migration; state format unchanged |
| Live service config | None — verified: no external service consumes ranges | none |
| OS-registered state | None | none |
| Secrets/env vars | None | none |
| Build artifacts | Installed plugin cache (`~/.claude/plugins/...vibe-check`) runs the OLD prose until reinstall + relaunch (project memory: "install chronically stale") | Release-time concern (Phase 61); note in the phase report that any manual check must use `--plugin-dir` or a resynced install |

## Common Pitfalls

### Pitfall 1: Content lines that look like headers
**What goes wrong:** a deleted `-- comment` (SQL/Lua/Haskell) or added `++i` line appears as `--- …`/`+++ …`; a naive parser switches files mid-hunk and drops or misattributes ranges.
**How to avoid:** consume hunk bodies by the header's old/new budgets (Pattern 1 step 3). **Warning sign:** a fixture with `-- x` → `++ y` produces a range under a file literally named `y`.

### Pitfall 2: User git config changes the diff text
**What goes wrong:** `color.ui=always`, `diff.mnemonicPrefix`, `diff.noprefix`, `diff.external` produce ANSI codes, `w/`/`i/` or missing prefixes, or non-unified output → empty or wrong-file ranges → `in_diff` false (−20) → findings can drop below threshold (silent finding loss).
**How to avoid:** every range-building git call passes `--no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/`; the PR call passes `--color never`. One fixture runs the prose command under a hostile repo-local config and asserts the same ranges. **Warning sign:** ranges keyed `w/…` or empty for a non-empty diff.

### Pitfall 3: PR `--patch` is a commit series
**What goes wrong:** per-commit coordinates; lines changed then reverted still count; a line changed in commit 1 and shifted by commit 2 is recorded at the wrong place.
**How to avoid:** range source = cumulative `gh pr diff <ref> --color never`; the builder refuses input containing an mbox `From <40-hex> ` line so a regression back to `--patch` fails closed. The checked-in fixture (D-05) should be a verbatim slice of a real cumulative capture cut at `diff --git` boundaries, with the source PR number, command and capture date recorded beside it. PR route is stateless (no decisions, no Finalize), so its exact ranges affect `in_diff` only.

### Pitfall 4: Mixed coordinate spaces in multi-part diffs
**What goes wrong:** GSD and incremental routes union HEAD-coordinate ranges with working-tree ranges; with an uncommitted insertion above a committed edit, the committed edit's range lands N lines off → a real nearby change can be missed.
**How to avoid:** range source = `git diff <base-commit>` (one diff, commit vs working tree). Reproduce first per the scope rule; if it does not reproduce as a wrong range on the real chain, record and drop. Note that untracked files are absent from every `git diff` form today (unchanged behavior).

### Pitfall 5: Stale literal blob file on retry
**What goes wrong:** the printed-literal convention makes an old `BLOBFILE=` path from an earlier attempt reusable; if code changed since, `head_blobs[file] == verified_blob` can still hold from the stale file and close a fix-obsolete verdict on changed code — weakening independent fix verification (forbidden).
**How to avoid:** prose rule "the blob file used by counts, rows and the re-run is the one printed by THIS attempt's step 1"; the automatic retry always mints a new file. Lock it with a prose phrase test and a walk case where a previous attempt's file holds an outdated blob.

### Pitfall 6: A second cross-call variable on the Finalize path
**What goes wrong:** `$FINALIZE_GATE_INPUT_JSON` is set in one call and read in the gate fence; in a fresh shell the gate gets empty stdin → traceback, exit 1 → "uncertain" stop. SC4 cannot be met by fixing BLOBFILE alone.
**How to avoid:** reproduce it in the same fresh-shell walk (record the verdict in 60-REPRO.md), then carry the gate input as a literal. Optionally make `finalize_gate.py` print `{"action":"refuse"}` on unparsable stdin instead of a traceback (it is already the documented branch for unparsable output) — only if the walk shows the traceback reaching the owner; otherwise carry.

### Pitfall 7: Prose locks pin the old wording
**What goes wrong:** `test_nv_render.DELETION_RANGE_PHRASES` asserts the header-based bullet text in `30-collect-score.md` (`[start, start + count - 1]`, `header \`+T,0\``, `[max(T, 1), T + 1]`, …); `test_finalize_card.ROWS_CALL` pins `--head-blobs "$BLOBFILE"`. Rewriting prose without updating them turns the suite red; updating them carelessly turns them decorative.
**How to avoid:** keep the documented rule text (`[max(T, 1), T + 1]`, net-deletion `+1`) in the bullet as the helper's contract, retarget the locks at the new text, and mutation-check each retargeted lock. `test_decision_continuity.deletion_hunk_ranges` remains a valid hand-built unit helper (CONTEXT), but EVID-02 proof must come from real-diff fixtures.

### Pitfall 8: Pure deletion at a line beyond EOF / start of file
**What goes wrong:** deleting the last lines yields cursor = N+1; deleting line 1 yields T = 0.
**How to avoid:** `[max(s−1,1), s]` handles T=0 → `[1,1]`; a range past EOF is harmless (`_line_in_ranges` is a pure membership test). Include both in unit tests.

## Code Examples

### Builder core (reference shape)
```python
# Source: derived from git's unified-diff format; behavior verified against git 2.55.0 -U0 headers above
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

def ranges_from_diff(text):
    out, path, i, lines = {}, None, 0, text.split("\n")
    while i < len(lines):
        ln = lines[i]; i += 1
        if ln.startswith("From ") and _MBOX.match(ln):
            raise RangeError("commit series, not a single diff")
        if ln.startswith("@@@"):
            raise RangeError("combined diff")
        if ln.startswith("+++ "):
            p = ln[4:].rstrip("\t")
            path = None if p == "/dev/null" else (p[2:] if p.startswith("b/") else p)
            continue
        m = _HUNK.match(ln)
        if not m:
            continue
        old_left = int(m.group(2)) if m.group(2) is not None else 1
        new_left = int(m.group(4)) if m.group(4) is not None else 1
        cursor, blk_s, added, deleted = int(m.group(3)), None, 0, 0
        def close():
            nonlocal blk_s, added, deleted
            if blk_s is not None and path:
                if added:
                    end = blk_s + added - 1 + (1 if deleted > added else 0)   # D-02
                    out.setdefault(path, []).append([blk_s, end])
                elif deleted:
                    out.setdefault(path, []).append([max(blk_s - 1, 1), blk_s])  # +T,0 rule
            blk_s, added, deleted = None, 0, 0
        while old_left > 0 or new_left > 0:
            if i >= len(lines):
                raise RangeError("hunk body shorter than its header")
            b = lines[i]; i += 1
            if b.startswith("\\"):
                continue
            tag = b[:1]
            if tag == " ":
                close(); cursor += 1; old_left -= 1; new_left -= 1
            elif tag == "+":
                if blk_s is None: blk_s = cursor
                added += 1; cursor += 1; new_left -= 1
            elif tag == "-":
                if blk_s is None: blk_s = cursor
                deleted += 1; old_left -= 1
            else:
                raise RangeError("unexpected line in hunk body")
            if old_left < 0 or new_left < 0:
                raise RangeError("hunk body longer than its header")
        close()
    return {f: _merge(r) for f, r in out.items()}
```
(Illustrative only — the executor writes the final version with `_MBOX = re.compile(r"^From [0-9a-f]{40} ")`, `RangeError` and `_merge` defined.) Note the pure-deletion block's `blk_s` is the cursor at the first `-`, i.e. the first new-side line after the deletion point, so `[max(blk_s−1,1), blk_s]` equals `[max(T,1), T+1]`.

### Real-diff fixture shape
```python
# Source: gitfixture.py + test_decision_continuity.py patterns in this repo
repo = gitfixture.make_repo(tmp)                 # isolated config
write(repo, "src/a.py", base_file(60)); commit(repo)
edit(repo, "src/a.py", line=L + 5)               # at boundary → reopens
diff = gitfixture.git(repo, "diff", "--no-color", "--no-ext-diff",
                      "--src-prefix=a/", "--dst-prefix=b/", "HEAD").stdout
ranges = diff_ranges.ranges_from_diff(diff)
assert ranges == ranges_from_diff(git(repo, "diff", "-U0", ...).stdout)  # context-independent
s2, _ = run_pass(s1, lines2, [], 2, ranges)      # real chain
# assert nearby_at stamped / gate blocks; repeat with L + 6 → decision stays current, gate writes
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ranges from hunk headers read by the orchestrator (context included) | Ranges from `+`/`-` markers by a pure helper | This phase | Window = exactly ±5; deletion and net-deletion rules reachable |
| PR ranges from `gh pr diff --patch` | From cumulative `gh pr diff --color never` | This phase (if reproduced) | Correct head coordinates |
| `$BLOBFILE` as a cross-call shell variable | Printed `BLOBFILE=` literal, fresh per attempt | This phase | Finalize completes from fresh shells |

**Deprecated/outdated:** the "Build the ranges from each hunk's new-side header `+start,count`" instruction in `30-collect-score.md:64`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Finding line numbers are working-tree coordinates (the orchestrator's "HEAD read" in `30-collect-score.md` step 0 reads the current file), so `git diff <base>` (vs working tree) is the right range source | Pattern 3 | If they are committed-HEAD coordinates, the default/GSD range source should be `git diff <base> HEAD` instead; reproduce with a dirty-file fixture before choosing |
| A2 | The GitHub non-`--patch` PR diff is base…head (merge-base) cumulative | Pattern 3, Pitfall 3 | Low — verified it is a single 34-file diff for PR #5; merge-base semantics are from training knowledge |
| A3 | The Write tool can write into a `mktemp`-created empty file in this harness | Pattern 4 | Low — `ANSWERFILE` already uses mktemp-then-Write in the shipped prose |
| A4 | In PR mode, agent-reported lines refer to the PR head file | Pattern 3 | If agents report against intermediate commits, exact cumulative ranges still won't match; PR mode is stateless so the only effect is the `in_diff` +20 |
| A5 | Quoted (`"b/…"`) paths only occur for names that can never carry a finding (PATH_RE `^[A-Za-z0-9._/-]+$`) | Pattern 1 step 2 | Low; skipping them reproduces today's effective behavior |

## Open Questions (RESOLVED)

1. **Do the coordinate-space defects (GSD/incremental concatenation, PR `--patch`) reproduce as a wrong keep on the real chain?**
   - What we know: the diff shapes are verified; the effect on decisions depends on A1.
   - Recommendation: one repro fixture each in Wave 0 (record in 60-REPRO.md). If reproduced → fix in this phase under EVID-03; if not → record and drop, keep the existing commands, and still route them through the helper.
   - RESOLVED: 60-01 Task 2 probes (TestCoordinateSpaces60: PR-SERIES, MIXED-COORD, plus the plan-review DEFAULT-STAGED shape) → 60-01 Task 3 REPRO_60 dispositions → 60-04 Task 1 picks each route's arm from the recorded verdict.
2. **Does `$FINALIZE_GATE_INPUT_JSON` actually cross a Bash call in practice?**
   - What we know: the fence reads it without setting it; the walk test will fail on it.
   - Recommendation: treat the walk failure as the reproduction (SC4 is a mandatory success criterion → broken required workflow class) and carry the input literally.
   - RESOLVED: 60-01 Task 2 `test_gate_fence_reads_cross_call_variable_today` (reproduction) → 60-03 Task 1 item 3 (printed `GATEFILE=` fence, `< "$GATEFILE"`) and Task 3 `no_cross_call_gate_input` lock.
3. **Should a failed range build halt the review or degrade?**
   - Recommendation: halt with one plain sentence (fail closed, same as score.py) for structural refusals; an empty diff yields `{}` and is not a failure. Degrading to `{}` silently would turn a parser bug into silent finding loss (`in_diff` false).
   - RESOLVED: 60-04 Task 1 range fence (`set -o pipefail` + halt sentence + exit 1) and Task 2 TestProseRangeFence failure path (no stdout, halt sentence on stderr).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | helper, tests | ✓ | 3.14.5 | — |
| git | fixtures, prose | ✓ | 2.55.0 | — |
| gh | PR route (prose only; not in suite) | ✓ | 2.86.0 | Checked-in capture (D-05) |
| pytest | suite | ✓ | 9.0.3 | — |
| bash | fresh-shell walk (`bash -s`) | ✓ (system bash 3.2 on macOS) | — | — |

**Missing dependencies:** none. Note the holdout PreToolUse hook blocked some compound shell commands in this session (rm -rf / sed -i chains); fixtures should run from pytest (Python `subprocess`), not ad-hoc shell chains.

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | The diff is attacker-authored text: the helper parses only, never executes or evals, refuses structurally inconsistent input, uses paths only as JSON keys; Finalize keeps PATH_RE + `guard.py` validation before any git call on a finding's file (unchanged) |
| V6 Cryptography | no | — |

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Crafted diff that desynchronizes a header parser (fake `+++` lines) to suppress `in_diff` / nearby re-asks | Tampering | Budget-driven body consumption; refusal on mismatch; fixture with `-- x`/`++ y` content |
| Huge diff / pathological lines | DoS | Linear single pass, no regex backtracking beyond the anchored hunk header |
| Stale blob file closing a fix verdict | Tampering (integrity of verification) | Fresh blob file per attempt; `verified_blob == head_blob` check unchanged |
| Owner reason text or paths on a command line | Injection | Unchanged rules: reasons go via files, paths validated before git |

## Validation Architecture

Skipped: `workflow.nyquist_validation` is `false` in `.planning/config.json`. (Test commands for the planner: per-file `pytest -q test_diff_ranges.py`, `pytest -q test_decision_continuity.py`, `pytest -q test_finalize_card.py`; full suite `pytest -q` from `plugins/vibe-check/scripts`.)

## Project Constraints (from CLAUDE.md)

No repo-level `./CLAUDE.md`. Applicable user-global directives:
- Security (absolute): no user input into `subprocess`/shell without structured args (the helper takes stdin only; prose keeps validated paths); no secrets; no stack traces to end users (relevant to Pitfall 6 — the gate traceback must not be what the owner reads).
- Release resources on every path: temp repos in tests via `addCleanup`; prose temp files are consumed/removed as the existing card rules do.
- Don't swallow exceptions silently: the helper refuses with a reason on stderr; no bare except.
- Planning files follow PLANNING-FORMAT.md; STATE.md `last_updated` refreshed when edited (orchestrator's job, not this research).
- Project memory: run fences as `bash -s <<'BASH' … BASH`; bare `pytest`; scope discipline (four qualifying classes); mutation-test every guard.

## Sources

### Primary (HIGH confidence)
- Repo code read at `554ee83`: `phases/review/30-collect-score.md:64`, `00-scope.md` modes 1–5, `05-state.md` step 3, `05-state-all.md` (ii), `phases/shared/90-finalize.md` (lines 13–93, 249), `scripts/score.py` (`_NEARBY_LINES`, `_nearby_changed`, `_line_in_ranges`), `scripts/replay.py` (`hunk_ranges`), `scripts/carry_state.py` (`parse_argv`, `read_json_file`, `REASON_HEAD_BLOBS`), `test_finalize_card.py` (`check_printed_paths`), `test_fix_loop_card.py` (`TestSubsetDispatchWalk`), `test_nv_render.py` (`DELETION_RANGE_PHRASES`), `gitfixture.py`
- Local runs: git 2.55.0 default vs `-U0` headers, hostile-config prefixes/color, content-line header lookalikes; `gh pr diff 5` with/without `--patch`; `carry_state.py` / `finalize_gate.py` empty-input behavior
- `gh pr diff --help` (gh 2.86.0): no context option
- `.planning/milestones/v2.13-phases/58-…/58-REVIEW-GAPS.md` SA-01; `57-…/deferred-items.md` IN-04; `59-REPRO.md` format

### Secondary (MEDIUM confidence)
- git unified-diff format semantics (hunk header counts, `\ No newline` marker, trailing tab on spaced names) — consistent with every observed output above

### Tertiary (LOW confidence)
- none

## Metadata

**Confidence breakdown:**
- Range builder design: HIGH — every expected range was derived from real `-U0` output in this session
- Route table: HIGH for the PR series finding (verified); MEDIUM for whether GSD/incremental mixing reproduces as a wrong keep (depends on A1)
- Finalize repair: HIGH — code paths and failure behavior verified by running the helpers

**Research date:** 2026-10-29
**Valid until:** 2026-11-28 (stable; internal code)
