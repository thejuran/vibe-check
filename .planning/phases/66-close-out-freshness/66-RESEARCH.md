# Phase 66: Close out freshness - Research

**Researched:** 2026-11-16
**Domain:** vibe-check Finalize (Close out) helper chain, decision-state carry, working-tree snapshot store (Python stdlib + git)
**Confidence:** HIGH for the mechanism and the 999.40 repair design (reproduced and probed in this session); MEDIUM for the 999.44 shape outcomes (design reasoning; shapes 1 and 2 not reproduced here)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Refusal message
- **D-01:** The refusal lists each stale decision on its own line: `file:line`, finding title, decision kind (deferred / dismissed), and the cause ("that line changed" or "code near it changed"; deleted/renamed file says so). Cap at about 10 rows, then "+N more".
- **D-02:** The refusal names the exact next command, mirroring the route the user reviewed with (default, GSD phase, PR, range, `--all`), e.g. "Run /review again (same scope), then Close out." It states that a review starts the (paid) reviewers. Close out itself never starts them.
- **D-03:** Any stale decision refuses the whole Close out: no report is written and state is left untouched, consistent with how Close out already refuses on other failed gates. No partial report that flags stale items.

#### What counts as changed
- **D-04:** Staleness is judged against the code as it is on disk now: committed, staged and unsaved working-tree edits all count (consistent with 999.28, which compares working-tree content, not HEAD).
- **D-05:** "Nearby" uses the same window the review already uses to reopen decisions (no new window definition).
- **D-06:** A decided file that was deleted or renamed after the review makes that decision stale (refuse; a rename is reviewed again, not guessed).
- **D-07:** Any byte change counts, including whitespace-only and comment-only edits. No language-aware "trivial edit" rules.

#### Legacy wrong-keep shapes (999.44)
- **D-08:** When a shape reproduces as a real wrong keep through the documented collection/persistence flow, prefer the smallest safe refusal (Close out asks for a fresh review). Repair only where the fix is equally small and clearly correct. No matching-logic redesign.
- **D-09:** Decisions on untracked files are judged by comparing the file's current bytes against what was reviewed; if they differ, or no reviewed content was saved to compare against, the decision is stale and Close out refuses.
- **D-10:** A shape that does not reproduce through the real flow is dropped with recorded proof: a committed test or counterexample/control showing the real flow cannot produce it, plus a note in the 999.44 backlog entry. No defensive code is added for unreproduced shapes.
- **D-11:** Deleted-original relocation (identical text left elsewhere after the decided line is deleted) must be distinguished from the owner-accepted D-21 behaviour of adding a new identical copy while the original remains.

#### Carried from the milestone (locked, not re-asked)
- Each repair starts with a reproduction that fails on 2.15.0; unchanged-code controls pass on both 2.15.0 and the candidate (GATE-07).
- Fix-verdict freshness, 999.28 unchanged-worktree score parity and real-edit reopening keep passing.
- Replay against 2.15.0 differs only by the intended refusals.
- One branch/PR for this phase: `feat/v2.16-phase-66` (milestone setup and this discussion ride with it).

### Claude's Discretion
- Where in the helper chain the freshness check lives (e.g. `finalize_inputs.py` vs `carry_state.decision_state` / `_closed`), and how the current-content comparison is computed (snapshot store vs `git` blob/tree comparison), provided D-04..D-07 hold.
- Exact refusal wording and exit code, within D-01..D-03 and existing Finalize refusal conventions (`next: stop-refused`).
- Fixture design for the three 999.44 shapes and the exact-line / nearby / unchanged controls for both decision kinds.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. (Phase boundary also excludes: decision-identity redesign (999.31), scorer retuning, new reviewer lanes, any automatic paid review, the other v2.16 items.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FRESH-01 | Stale deferred/dismissed decision (exact line or nearby changed since review) -> Close out refuses, asks for a fresh review, never starts paid reviewers | Reproduced on 2.15.0 code (both kinds, exact-line and nearby). Repair design: reverse `git diff` of the last pass's `reviewed_tree` against the working tree, D-14 window via `score._nearby_changed` semantics, new `next` value. See Architecture Patterns 1-3. |
| FRESH-02 | Unchanged reviewed code still completes for both kinds; fix-verdict freshness, 999.28 parity, real-edit reopening as in 2.15.0 | "No decision-closed record -> no git call, byte-identical result" rule; differential test against the literal v2.15 helper; named regression test classes listed in Validation Architecture. |
| FRESH-03 | Each 999.44 shape gets an evidence-backed outcome; D-21 distinguished; no identity redesign | Loop-freedom finding (Pitfall 1) decides which outcome is safe per shape; shape-by-shape plan in Pattern 5. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

No project `./CLAUDE.md` exists. User-global directives that bind this phase:
- Security (absolute): never pass user input to `subprocess` without structured argv; never log sensitive data; no stack traces to users. Finding `file` values come from the reviewed diff and are attacker-influenced — every git call must be an argv list, paths passed after `--`, never through a shell.
- Every resource released on every path (`try/finally` for temp files/dirs); no swallowed exceptions without at least a recorded fallback.
- Follow existing codebase conventions before introducing patterns: stdlib-only runtime (CI runs `.github/scripts/stdlib_only.py plugins/vibe-check`), helpers "decide", prose "renders", fail closed, fixed reason strings that never echo a title/path/hash on stderr.
- Owner memory rules: mutation-test every new guard (decorative-guard lesson); for "same as 2.15.0" claims build a two-sided differential against the literal old code; add work only for reproduced gate failure / data loss / silent finding loss / broken required workflow; never start a paid reviewer automatically; tests run with bare `pytest`.

## Summary

The 999.40 defect is confirmed on the current branch (2.15.0 code): with a pass-1 state from `test_decision_continuity.pass1(conf=95, kind=defer|dismiss)` and `reviewed_tree = HEAD^{tree}`, editing line 10, 13 (nearby) or even 17 and running the real `finalize_inputs.py` CLI returns `action: write`, `next: write-review-md`, all counts 0, for both kinds [VERIFIED: scratch run of `finalize_inputs.run` in a temp git repo this session]. Cause, confirmed by reading the code: `finalize_inputs._run` -> `carry_state.finalize_counts` -> `_closed` returns True as soon as `decision_state(...) == "current"`, and `decision_state` compares saved decision evidence with saved finding data only; nothing in Finalize reads the code on disk except fix-verdict fingerprints [VERIFIED: carry_state.py:980-1092, finalize_inputs.py:418-447].

Everything needed for the repair already exists: every non-`--all` pass records what it reviewed as `passes[-1].reviewed_tree` (a tree id in the vibe-check object store on default/GSD, the range-end or PR-head commit on range/PR) [VERIFIED: worktree_snap.py, 45-persist.md:21,39]. A reverse diff of that id against the working tree (`git diff -R --no-renames --text <reviewed_tree> --` with the store as an alternate object directory and swapped prefixes) yields changed-line ranges **in the reviewed tree's line numbers**, i.e. the same numbering as the decided record's `line`; `diff_ranges.ranges_from_diff` parses it unchanged, and the existing D-14 window (`score._NEARBY_LINES = 5`, `_nearby_changed`) answers "exact line or nearby" [VERIFIED: probe in this session — edit at 10/15/5 -> stale, 16/4 -> keep, 20 lines inserted above -> keep, whole-file delete or `git mv` -> whole-file range -> stale, whitespace-only edit -> stale].

The most important planning finding is **loop-freedom**: a Close out refusal is only safe if the fresh review it asks for will actually re-ask (or clear) that decision. For 999.40 it does (the next pass's 999.28 nearby ranges come from the same reviewed tree, so the edit stamps `nearby_at` or re-hashes the line). For untracked files, `--all`, and 999.44 shapes 1-2 a Close-out-only refusal would loop forever, which is itself a "broken required workflow". The plan must either pair those refusals with a review-side re-ask or choose a different outcome (see Pitfall 1 and Open Questions).

**Primary recommendation:** Add a new stdlib module (e.g. `scripts/closeout_fresh.py`) that, only when at least one last-pass record is closed by a current owner decision, reverse-diffs the last pass's `reviewed_tree` against the working tree and returns the stale decisions; call it from `finalize_inputs._run` before the gate, return `action: "refuse"` with a new `next: "stop-review-again"` (or similar) plus a `stale` list, and add one prose bullet to `90-finalize.md`. Do **not** modify `carry_state.py` or `finalize_gate.py` for 999.40 (the parity grid pins them byte-identical to dd8e4ab).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Decide which decisions are stale (ranges -> window -> cause) | Helper script (pure Python, new module) | — | "Helper decides, prose renders"; pure part is unit-testable without git |
| Read what was reviewed vs disk now | Helper script git layer (reverse diff against `reviewed_tree` via the store) | `worktree_snap` store/env helpers | Store lives under `.turingmind/worktree-snap/objects`; only `worktree_snap._store_env` knows its alternates |
| Gate outcome (`refuse` + new `next`) | `finalize_inputs.py` | `finalize_gate.py` unchanged | Gate's six ACTIONS are frozen ("never invent a seventh"); `next` is the model's branch key |
| Refusal text, route-mirroring next command, 10-row cap | Prose `phases/shared/90-finalize.md` | `commands/review.md` / `deep-review.md` (no change expected) | Prose renders all owner sentences; titles joined by the existing join rule |
| Review-side re-ask (only if a 999.44 shape needs it) | `score.py` / `carry_state.py` / relocation prose | test simulator `relocate_decided` | Loop-freedom requires the review to re-ask what Close out refuses |

## Standard Stack

No new packages. Python stdlib + the system `git` only (stdlib-only rule enforced in CI).

### Core (existing, reuse)
| Module | Purpose | Why reuse |
|--------|---------|-----------|
| `scripts/worktree_snap.py` | `_store_env(root)` (alternates incl. the vibe-check store), `OBJECT_ID_RE`, `DIFF_FLAGS`, `prior_tree` | The reviewed tree's objects live only in the store; `_store_env` is the one place that wires it |
| `scripts/diff_ranges.py` | `ranges_from_diff(text)` | Exact, `-U`-independent ranges; deleted files give no ranges on the `+++ /dev/null` side, but in the REVERSE diff a deleted file appears as whole-file "added" -> full range (verified) |
| `scripts/score.py` `_NEARBY_LINES`, `_nearby_changed` | D-14 window (line ±5, clipped at 1) | D-05 says reuse the review's window; import the constant or mirror it with a lock test (carry_state documents "this module may not import score"; a new module may, but prefer a mirrored constant + equality test to avoid importing a 3,281-line scorer into Finalize) |
| `scripts/carry_state.py` `open_findings`, `decision_state`, `stale_cause`, `_fix_closes`, `_check_state` | Which records are closed by a current decision | Read-only use; no edits needed for 999.40 |
| `scripts/finalize_inputs.py` | CLI, `_run`, `NEXT_ACTIONS`, `next_action` | The single Finalize-inputs fence; refusal plumbs through it |
| `scripts/gitfixture.py`, `test_decision_continuity.py` (`base_file`, `pass1`, `run_pass`, `_RealChain`), `test_worktree_snap.py` (`_Chain`, `_Phases.run_pass_fences`) | Real-chain fixtures running the actual prose fences | Gives real `reviewed_tree` states without stubbing |

**Version verification:** local Python 3.14.5, git 2.55.0; CI uses Python 3.14 and `pytest==9.0.3` [VERIFIED: `.github/workflows/offline-suite.yml`, local `--version`].

## Package Legitimacy Audit

Not applicable: this phase installs no external packages (stdlib + git only). slopcheck not run.

## Architecture Patterns

### System Architecture Diagram

```
/review --finalize (or fix-loop "Close out")
        |
        v
Phase 0 / 0.5: resolve route + $STATE_FILE (no reviewers dispatched)
        |
        v
90-finalize.md step 1 fence --> finalize_inputs.py _run(state, blob-out, switches)
        |
        +--> load + validate state (unchanged)
        +--> head_blobs (fix-verdict fingerprints, unchanged)
        +--> [NEW] closeout_fresh.decided_records(state)
        |        |  none decision-closed? --> skip (NO git call; result byte-identical to 2.15.0)
        |        v
        |    reviewed id = passes[-1].reviewed_tree
        |        |  missing / not in store / git error --> every decided record stale, cause "unverifiable"
        |        v
        |    git diff -R --no-renames --text <reviewed id> --   (store as alternate; swapped prefixes)
        |        v
        |    diff_ranges.ranges_from_diff  --> {file: [[s,e]]} in REVIEWED line numbers
        |        v
        |    per decided record: file absent from reviewed tree -> "untracked/no saved copy"
        |                        file gone now              -> "file deleted or renamed"
        |                        range hits own line        -> "that line changed"
        |                        range hits line±5 window   -> "code near it changed"
        |        v
        |    stale list (sorted) ----non-empty----> result {action:"refuse", next:"stop-review-again", stale:[...]}
        |        | empty
        v        v
build_result -> carry_state.finalize_counts -> finalize_gate.run   (unchanged)
        |
        v
prose branches on `next`: write-review-md | finalize-card | stop-fallback-* | stop-no-state | stop-refused | [NEW] stop-review-again
                                                                                    |
                                     render <=10 rows via join rule + "+N more", name the same-scope review command,
                                     say a review starts the paid reviewers; STOP (no REVIEW.md, no archive, no state write)
```

### Recommended Project Structure
```
plugins/vibe-check/scripts/
├── closeout_fresh.py            # NEW: pure staleness decision + thin git layer (stdlib only)
├── test_closeout_fresh.py       # NEW: unit + real-chain + mutation tests
├── finalize_inputs.py           # EDIT: call the check in _run; new NEXT_ACTIONS value
├── test_finalize_inputs.py      # EDIT: fixtures that now need a reviewed_tree; new refusal tests
├── test_finalize_parity_grid.py # EDIT: grid states must bind a reviewed_tree for the decided file (see Pitfall 4)
└── (carry_state.py, finalize_gate.py, guard.py, fixcommit.py UNCHANGED for 999.40)
plugins/vibe-check/phases/shared/90-finalize.md   # EDIT: one new `next` bullet + refusal rendering
```

### Pattern 1: Reverse diff in reviewed-tree numbering
**What:** Ranges in the numbering of the tree the reviewers read, so a decided record's stored `line` can be checked directly with no relocation.
**Why reverse:** `git diff <tree>` gives new-side (working-tree) numbers; a forward diff wrongly refuses a pure shift (20 lines inserted above: forward hits the window, reverse does not) and wrongly keeps a deleted or renamed file (forward: no new-side range; reverse: whole-file range). Both verified this session.
```python
# Source: probe in this session against worktree_snap.take() trees
REV_FLAGS = ("--no-color", "--no-ext-diff", "--no-textconv", "--no-relative",
             "--src-prefix=b/", "--dst-prefix=a/")   # swapped: with -R the +++ side shows the src prefix
env = worktree_snap._store_env(root)   # NOTE: creates the store dir if missing; prefer a read-only variant
argv = ["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
        "diff", "-R", "--no-renames", "--text", *REV_FLAGS, reviewed_id, "--"]
proc = subprocess.run(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=GIT_TIMEOUT)
ranges = diff_ranges.ranges_from_diff(proc.stdout.decode("utf-8", "replace"))  # RangeError -> fail closed
```
- `--no-renames` is required (a pure `git mv` otherwise gives no hunk -> wrong keep).
- `--text` so a binary change is not an empty `{}` (D-07 any byte change).
- Run in the repo top (`git rev-parse --show-toplevel`), not the session subfolder; finding paths are repo-relative (`--no-relative`).
- `--no-optional-locks` keeps `git diff` from refreshing the real index (Close out must not write).
- Works for both tree ids (default/GSD) and commit ids (range/PR) as `reviewed_tree`.

### Pattern 2: Which records, which lines
- Records: `carry_state.open_findings(state)` entries for which `decision_state(rec, state) == "current"` **and** `_fix_closes(rec, state, last, blobs)` is False (a fresh fix-obsolete verdict on the current blob is newer evidence; preserve 2.15.0). Decision source: own `decisions[hash]` or the covering decision (`covering_decision`). Exclude legacy `medium_acknowledgments` (90-finalize.md:253 promises "an old medium-only state finalizes exactly as before"; no writer exists) [VERIFIED: grep].
- Lines per record: its own `line`; plus every open same-hash copy's line (mirrors `_merge_nearby`, CR-02) and, for a decided row, its covered members' lines (score `_nearby_spots` "grouped", CR-04). Rationale: the Close-out line set must equal the review's stamp line set — stricter loops, laxer leaks (Pitfall 1). Planner should confirm the exact set against `score._nearby_spots` / `_merge_nearby` with a test per spot kind.
- Non-int line, non-str file, file failing `fixcommit.PATH_RE` -> stale ("unverifiable"), never silently kept.
- Kind for D-01: the decision's `decision` field (`defer` -> "deferred", `dismiss` -> "dismissed").

### Pattern 3: Result shape that keeps 2.15.0 runs byte-identical
- If no record is decision-closed: run no git, add no key; the result JSON is exactly 2.15.0's (`{"action","reason","next","counts","report"}`).
- On refusal only: `{"action": "refuse", "reason": <new fixed reason>, "next": "<new value>", "counts": <finalize_counts as usual>, "report": null, "stale": [{"hash","kind","cause"} ...]}`. Keep `action` inside `finalize_gate.ACTIONS` (tests assert it); add the new `next` to `NEXT_ACTIONS`. Prose renders `file:line — title` via the existing join rule (as the `stop-fallback-*` bullets do), so the helper keeps its "never echoes a path, hash or title on stderr" rule.
- Exit 0 (the prose's "one automatic rebuild" rule retries only non-zero exits; a refusal must not be retried, and `stop-refused` is never retried either).
- Order: run the stale check before the gate (D-03: any stale decision refuses the whole Close out, even when outstanding findings would otherwise open the card).
- An older 90-finalize.md that does not know the new `next` treats it as `stop-refused` ("Any other value ... is treated as `stop-refused`") — fails toward stopping.

### Pattern 4: Missing baseline
- `passes[-1].reviewed_tree` missing (state from 2.14.0, a pass whose code moved mid-pass, `take` failed), not a well-formed id, absent from the store (owner deleted `.turingmind/worktree-snap/`, 999.30), or any git failure/timeout -> treat every decision-closed record as stale with an "unverifiable" cause and refuse. A fresh default/GSD review records a new tree, so this clears in one review (loop-free) — except on `--all`, which never records one (Open Question 1).
- Do not fall back to `head_sha`: if the reviewed content included uncommitted edits, a HEAD->disk diff is in the wrong numbering and misses an edit that was reverted back to HEAD content (wrong keep).

### Pattern 5: 999.44 shapes — outcome plan
| Shape | Fresh evidence | Does the 999.40 check cover it? | Recommended outcome path |
|-------|----------------|-------------------------------|--------------------------|
| 3: untracked files lack change ranges (60-REPRO R7) | `take` uses `git add -u` (copied real index): staged-new and `git add -N` files ARE in `reviewed_tree`; untracked files are not [VERIFIED: probe] | Yes at Close out: decided file absent from `reviewed_tree` -> stale (D-09). Review side still never stamps nearby for it. | Reproduce (decision on untracked file, edit beside it, real chain incl. a fresh review, Close out writes on 2.15.0). Outcome "unsupported decision safely refused". To stay loop-free the refusal must tell the owner to add the file to git (`git add`/`git add -N`) before reviewing again — after that the next review's prior->current diff shows the file as added (whole-file range) and re-asks. Alternative: snapshot untracked non-ignored files in `take` (repairs review side too, but grows the store and changes 999.28 inputs) — see Open Question 2. |
| 1: deleted-original relocation to identical text elsewhere (57 WR-01) | Simulated relocation kept a dismiss current after deleting line 10 with identical text at 49 (999.44 record) | No, once a review ran after the deletion: the last tree already contains the deletion, so Close out sees no change. | Reproduce through the real chain (prose fences + `relocate_decided` simulator + `finalize_inputs` CLI). If it reproduces, a Close-out-only refusal LOOPS (the fresh review relocates again and keeps the decision). The smallest loop-free outcome is review-side: when relocation case 2 moves a decided ordinary record away from its stored line and the prior->current diff deleted/changed that stored line, stamp it (re-ask). D-11 control: original line kept + identical copy added must still keep (D-21; `test_p4_far_twin_*`). Needs owner sign-off if it touches relocation prose (Open Question 3). |
| 2: older covering decision wins (57-REVIEW-GAPS IN-03) | Synthetic legacy-state probe: sorted-first `_covering` gives `current` with older critical + newer medium cover, `stale` with newer alone; real-writer producibility unverified | No (decision_state semantics, not code freshness). | First try to produce two `covers` entries matching one record through `record_decisions` + scorer regrouping (lead change on the same site, re-decide, then split). If not producible: record the counterexample (D-10). If producible: the clearly-correct small repair is in `_covering` (prefer highest `at_pass`, hash tie-break — the GAPS review's own fix), which both the review card and Close out read, so it is loop-free. That edits `carry_state.py` -> must re-plumb the parity grid's 2.14.1 side (Pitfall 4). |

### Anti-Patterns to Avoid
- **Editing `carry_state.decision_state`/`_closed` to read disk:** carry_state is pure (imports exactly json/os/sys, no git) and is pinned byte-identical to dd8e4ab by `test_finalize_parity_grid.py::TestStep1ScriptIsPinned::test_shared_modules_are_byte_identical_to_dd8e4ab`.
- **Adding a seventh gate action:** `finalize_gate.py` says "Never invent a seventh"; tests enumerate `ACTIONS`. Use `refuse` + a new `next`.
- **Taking a new snapshot at Close out (`worktree_snap.take`)** just to diff tree-to-tree: writes objects into the store; diffing the working tree directly is read-only.
- **Forward diff / HEAD baseline:** wrong numbering, misses deletes/renames, over-refuses pure shifts (verified).
- **Refusing for a condition the next review will not re-ask:** produces an endless refuse/review loop (Pitfall 1).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parsing diff hunks into line ranges | A new hunk parser | `diff_ranges.ranges_from_diff` | Handles `\ No newline`, `--- x` content lines, budgets, escape bytes; already mutation-tested |
| Locating reviewed objects | Reading `.turingmind/worktree-snap` paths by hand | `worktree_snap._store_env` (or a read-only twin that does not `makedirs`) | Alternates + env scrubbing (`GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`) already correct |
| The nearby window | A new ±N constant | `score._NEARBY_LINES` / `_nearby_changed` semantics (D-05) | Shared definition with the review's re-ask and re-check trigger (D-14) |
| Which records are decision-closed | Re-deriving decision logic | `carry_state.open_findings` + `decision_state` + `_fix_closes` | Single source of truth; covers own, covering, NV and legacy shapes |
| Path validation before git | A new regex | `fixcommit.PATH_RE` (+ guard containment if a path is passed to git as a pathspec) | Same rule as fix-verdict fingerprints |
| Temp git repos in tests | Ad hoc `git init` | `gitfixture.make_repo/git/write/helper_env` | Isolates global/system git config |
| Real-chain passes with real `reviewed_tree` | Hand-written states | `test_worktree_snap._Chain.run_pass_fences` + `tdc.run_pass` | Runs the actual prose fences in fresh shells |

## Common Pitfalls

### Pitfall 1: Refusal loops (the key planning risk)
**What goes wrong:** Close out refuses, the owner runs the requested review, the review keeps the decision current, Close out refuses again — forever. A broken required workflow introduced by the fix.
**Why it happens:** The review re-asks only via score's nearby stamp (prior `reviewed_tree` -> current tree), hash change, band/lanes, or joined newcomers. Anything Close out flags that none of those flag is unclearable.
**Affected cases found:** untracked decided files (never in any tree), `--all` (never records `reviewed_tree`), 999.44 shape 1 after a review pass, shape 2 if done Close-out-only, PR/range routes when the disk is not at the reviewed commit (e.g. reviewing a range ending at HEAD with uncommitted edits near a decision — the range review never sees them).
**How to avoid:** For every refusal cause, add a "refusal is clearable" test: refuse -> run the real-chain fresh review (`_Chain.run_pass_fences` + `run_pass`) -> assert the decision is now re-asked (stale) or gone -> record a new decision -> Close out writes. Where no review re-asks, either change the instruction (untracked: "add it to git, then review again"), add the review-side re-ask, or record the case as an accepted limit with the owner.

### Pitfall 2: Swapped diff prefixes under `-R`
**What goes wrong:** With `-R` and the usual `--src-prefix=a/ --dst-prefix=b/`, the `+++` header reads `a/src/a.py`; `diff_ranges._file_path` strips only `b/`, so keys become `a/src/a.py`, nothing matches, every decision is silently kept.
**How to avoid:** pass `--src-prefix=b/ --dst-prefix=a/` with `-R` [VERIFIED: probe]. Mutation test: restore the normal prefixes -> the 999.40 fixture must fail.

### Pitfall 3: Breaking "unchanged runs are identical" by running git or adding keys
**What goes wrong:** Running git or adding a `stale` key on every Close out changes 2.15.0 outputs (stderr, result keys, "no state file -> no git" guarantees in tests).
**How to avoid:** Gate the whole check on "at least one decision-closed record"; add `stale` only on the refusal path; keep `build_result` pure and its signature-compatible (TestBuildResultParity compares it to an oracle on every prepared state).

### Pitfall 4: Parity grid and fixture blast radius
**What goes wrong:** (a) The parity grid runs the 2.14.1 side with the CURRENT `carry_state.py`/`finalize_gate.py`/`guard.py`/`fixcommit.py` and asserts they are byte-identical to dd8e4ab; editing them fails `test_shared_modules_are_byte_identical_to_dd8e4ab`. (b) Grid states (`fixtures/phase45-loop-state.json` + a dismiss on BUGS_HASH at `plugins/vibe-check/phases/deep-review/20-selection.md:38`) have no `reviewed_tree` and that file is not in the grid repo, so the new check would refuse every grid scenario. (c) A naive "refuse when decisions are current and no reviewed_tree" mutant fails **48 existing tests** in `test_finalize_inputs.py`, `test_finalize_card.py`, `test_confirmed_fix.py` [VERIFIED: mutant run in a scratch copy this session].
**How to avoid:** Keep the four pinned modules untouched for 999.40. Plan an explicit Wave-0 task to give those fixtures a real temp repo + `reviewed_tree` (the decided file present and unchanged) so they still exercise the write path, rather than loosening assertions. If shape 2 needs a `carry_state.py` change, first change the grid to materialize the dd8e4ab modules via `git show` into a temp dir for its 2.14.1 side.

### Pitfall 5: Index/side-effect writes during Close out
**What goes wrong:** `git diff` against the working tree may opportunistically refresh `.git/index`; `_store_env` creates `.turingmind/worktree-snap/objects` if missing; D-03 says state is left untouched and `TestCliWritesOnlyTheFingerprintFile` asserts only the blob file changes.
**How to avoid:** `--no-optional-locks`, `-c core.fsmonitor=false`, a read-only env builder that adds the store as an alternate only if it exists (missing store -> "unverifiable"), and extend `TestCliWritesOnlyTheFingerprintFile` to the refusal route.

### Pitfall 6: Session subfolder and attacker-shaped paths
**What goes wrong:** Finalize runs in the session cwd (D-19 history); finding `file` values are attacker-influenced.
**How to avoid:** Run the diff at the repo top, never pass a finding path to git (diff the whole tree, then look paths up in the parsed map), and treat paths failing `PATH_RE` as unverifiable/stale. C-quoted paths contribute no ranges (`diff_ranges` skips them) — since `PATH_RE` forbids such names, a decided record can never be on one (R8), but assert it.

### Pitfall 7: Route mismatch on PR/range
**What goes wrong:** `reviewed_tree` is a commit on PR/range; D-04 compares it to disk. If the owner is not checked out at that commit (common for PR reviews), every decision-closed record refuses. A PR head that is not present locally makes git fail -> "unverifiable".
**Mitigating fact:** PR and range modes skip Phase 5 and the Finalize card falls back, so they cannot record decisions themselves; decided records reach a PR/range last pass only through the shared branch state file from a default-route pass. Still needs an explicit outcome (Open Question 4).

## Code Examples

### The 999.40 reproduction (fails on 2.15.0; must refuse after the repair)
```python
# Source: run in this session (scratch), mirrors ROADMAP 999.40 assessment
repo = gitfixture.make_repo(tmp); lines = tdc.base_file()
gitfixture.write(repo, "src/a.py", "\n".join(lines) + "\n")
gitfixture.git(repo, "add", "-A"); gitfixture.git(repo, "commit", "-qm", "x")
state, h = tdc.pass1(lines, conf=95, kind=kind)          # kind in ("defer", "dismiss")
state["passes"][-1]["head_sha"] = git(repo, "rev-parse", "HEAD")
state["passes"][-1]["reviewed_tree"] = git(repo, "rev-parse", "HEAD^{tree}")
# edit: line 10 -> "line_10 = danger()" (exact) | line 13 or 15 (nearby) | none (control) | line 16/4 (outside window control)
code, out = finalize_inputs.run(["--state-file", sf, "--blob-out", empty_file,
    "--noninteractive", "false", "--pr-mode", "false", "--range-mode", "false"], cwd=repo)
# 2.15.0 observed: code 0, action "write", next "write-review-md", outstanding counts 0 for every edit
```
Note: a real default-route pass stores a tree in the vibe-check store; `HEAD^{tree}` is equivalent only for a clean committed tree. Also build one fixture through `test_worktree_snap._Chain` with uncommitted reviewed code so the store path is exercised.

### Window semantics in reviewed numbering (verified results)
```
edit line 10            -> [[10,10]]  stale (cause: that line changed)
edit line 15 / 5        -> stale (code near it changed)      edit 16 / 4 -> keep
20 lines inserted above -> [[1,1]]    keep (pure shift; forward diff would wrongly refuse)
20 above + edit 10      -> [[1,1],[10,10]] stale
whitespace-only line 10 -> stale (D-07)
file deleted / git mv   -> [[1,60]]   stale (D-06; forward diff would wrongly keep)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Decision stamp from `git diff <last head_sha>` | 999.28: prior `reviewed_tree` -> current tree (`NEARBY_LINE_RANGES`) | 2.14.1 (PR #8) | Close out can reuse the same baseline |
| Finalize gate inputs in prose | `finalize_inputs.py` helper | 2.15.0 (Phase 63) | One place to add the freshness check |
| Unbounded/sorted-first decision carry | Still current (`_covering` sorted-hash first; relocation case 2 unbounded) | — | 999.44 shapes 1-2 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The Close-out line set should equal the review's stamp set (own line + same-hash copies + grouped covered members) | Pattern 2 | Too strict -> refusal loops; too lax -> leaks. Verify with per-spot-kind tests |
| A2 | Shape 1 reproduces through the real chain as recorded (simulator mirrors prose) | Pattern 5 | If not, outcome is D-10 non-reproduction instead of a repair |
| A3 | Shape 2 may be producible via lead change + re-decide + split | Pattern 5 | If not producible, record counterexample; no carry_state edit needed |
| A4 | `git add -N` on an untracked decided file makes the next review re-ask it (file appears as added in prior->current diff) | Pattern 5 / Pitfall 1 | If the review does not re-ask, the untracked refusal loops; test it |
| A5 | A refusal action of `refuse` with a new `next` is acceptable to existing tests that enumerate gate reasons | Pattern 3 | Some tests may assert `reason in finalize_gate.REASONS`; then define the reason in finalize_inputs and adjust that test deliberately |

## Open Questions

1. **`--all` route has no `reviewed_tree`.**
   - What we know: `--all` skips `take`/`collect` and 45-persist omits `reviewed_tree`; decisions can still be recorded on `--all` (fix-loop with `--all --fix`, or the Finalize card), and every `--all` run starts fresh. Refusing on missing baseline would make `--all` Close out with any decision impossible (loop). D-02 lists `--all` among the routes, implying coverage is expected.
   - Recommendation: record `reviewed_tree` on `--all` too (run the same `take` in 00-scope-all, `collect` in Phase 3, allow the key in 45-persist-all / `future-schema.json`); no scorer effect because `--all` never stamps. If the owner prefers minimal scope, exempt `--all` explicitly as a named known limit. Product call (scope vs coverage) — bring to the owner.
2. **Untracked decided files (D-09).** Refuse with "add the file to git, then review again" (smallest; loop-free if A4 holds) vs. snapshot untracked non-ignored files in `take` (also repairs review-side R7, but grows the store and may copy untracked secrets into `.turingmind/`). Recommend the first.
3. **Shape 1 outcome if it reproduces.** A Close-out-only refusal loops. The loop-free fix is a bounded review-side re-ask in the decided-record relocation (30-collect-score step 0 + simulator + possibly score stamping). Is that "equally small and clearly correct" under D-08, or should the owner accept it as a known limit? Reproduce first, then ask with the evidence.
4. **PR/range Close out where disk differs from the reviewed commit.** D-04 literally says disk. Recommend keeping D-04 and wording the refusal so the next step is actionable ("commit or revert the edits near these lines, or check out the reviewed commit, then review again"); confirm with the owner because it can block a PR Close out run from another checkout.
5. **Where a decided record's covering decision applies (inherited records):** use the record's own line in last-pass numbering (no `covers` line exists). Low risk; note in tests.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | helpers, tests | ✓ | 3.14.5 | — |
| git | reverse diff, fixtures | ✓ | 2.55.0 | — |
| pytest | suite | ✓ | (CI pins 9.0.3) | — |
| bash | prose-fence tests | ✓ | system | — |
| gh / network | not needed (Close out never fetches; PR head must already be local) | — | — | — |

No missing dependencies. No paid/live run is needed for this phase's offline evidence; any live check needs a separately approved bounded proposal (GATE-08).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (CI), stdlib `unittest` test classes |
| Config file | none (CI command in `.github/workflows/offline-suite.yml`; left-out list `.github/ci-left-out-tests.txt`) |
| Quick run command | `cd plugins/vibe-check/scripts && pytest -q -p no:cacheprovider test_closeout_fresh.py test_finalize_inputs.py test_finalize_card.py` |
| Full suite command | `pytest -q -p no:cacheprovider plugins/vibe-check/scripts .github/scripts docs/design/lean-v2.15/tools` (baseline this session: scripts dir alone 4126 passed, 6207 subtests, ~4m20s) |
| Stdlib check | `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` |

### Phase Requirements -> Test Map
| Req / SC | Behavior | Test Type | Automated Command | File Exists? |
|----------|----------|-----------|-------------------|-------------|
| FRESH-01 / SC1 | 999.40 repro: defer + dismiss x {exact line 10, nearby 13/15/5} -> 2.15.0 writes, candidate refuses with `next` = new value, `stale` lists hash/kind/cause, no REVIEW.md, state file bytes unchanged | integration (temp repo, real CLI) | `pytest -q test_closeout_fresh.py -k repro_999_40` | ❌ Wave 0 |
| FRESH-01 / SC1 | Same through the real prose fences with an uncommitted reviewed block (`_Chain`) so the store path is exercised | integration | `pytest -q test_closeout_fresh.py -k real_chain` | ❌ Wave 0 |
| FRESH-01 / SC1 | Refusal never starts reviewers: prose bullet for the new `next` stops, names the same-scope command, says it starts paid reviewers, has no re-entry/dispatch instruction | prose lock | `pytest -q test_finalize_card.py -k review_again` | ❌ Wave 0 |
| FRESH-01 | D-06 delete and `git mv`; D-07 whitespace-only; window edges 4/5/15/16; 20-lines-above pure shift keeps | unit+integration | `pytest -q test_closeout_fresh.py -k window` | ❌ Wave 0 |
| FRESH-01 | Missing/unknown `reviewed_tree`, store deleted, git failure -> refuse "unverifiable" (fail closed) | integration | `pytest -q test_closeout_fresh.py -k unverifiable` | ❌ Wave 0 |
| FRESH-01 (loop-freedom) | Every refusal cause is clearable: refuse -> fresh real-chain review re-asks -> new decision -> Close out writes | integration | `pytest -q test_closeout_fresh.py -k clearable` | ❌ Wave 0 |
| FRESH-02 / SC2 | Unchanged code, both kinds, default + GSD + committed: candidate == literal v2.15 helper output byte-for-byte; no git call when no decision-closed record | differential (two-sided, v2.15 modules materialized via `git show d5acc19:…`) | `pytest -q test_closeout_fresh.py -k differential` | ❌ Wave 0 |
| FRESH-02 | Fix-verdict freshness | regression | `pytest -q test_finalize_inputs.py -k "Freshness or Fingerprint" test_finalize_card.py -k FreshShell` | ✅ |
| FRESH-02 | 999.28 unchanged-worktree parity + real-edit reopening | regression | `pytest -q test_worktree_snap.py test_decision_continuity.py -k "999_28 or Uncommitted or NearbyEdit or ReReview"` | ✅ |
| FRESH-02 | 2.14.1 parity grid still agrees (after fixture gets a reviewed_tree) | regression | `pytest -q test_finalize_parity_grid.py` | ✅ (needs edit) |
| FRESH-03 / SC3 | Shape 3 (untracked): repro on 2.15.0 (writes) -> candidate refuses; `git add -N` control clears | integration | `pytest -q test_closeout_fresh.py -k untracked` | ❌ Wave 0 |
| FRESH-03 / SC3 | Shape 1: deleted-original relocation repro vs D-21 control (original kept + copy added keeps) | integration (real chain + simulator) | `pytest -q test_decision_continuity.py -k deleted_original` | ❌ Wave 0 |
| FRESH-03 / SC3 | Shape 2: producibility attempt through `record_decisions` + regrouping; repair or committed counterexample | integration | `pytest -q test_decision_continuity.py -k covering_order` | ❌ Wave 0 |
| SC4 | Scorer replay vs 2.15.0 identical (score.py untouched, or byte-identical outcomes if a shape repair touched it) | replay | `python3 plugins/vibe-check/scripts/replay.py diff --base rev:d5acc19 --scorer path:$PWD/plugins/vibe-check/scripts/score.py --out /tmp/…/replay-66.md` | ✅ tool |
| SC4 | Finalize-side differential: across all existing finalize fixtures, the only differences from v2.15 are the intended refusals, each asserted in both directions | differential | `pytest -q test_closeout_fresh.py -k only_intended` | ❌ Wave 0 |

### Mutation checks (decorative-guard lesson — each must make a named test fail)
1. Remove the freshness call in `_run` -> repro test fails.
2. Forward diff (drop `-R`) -> pure-shift-keeps and delete/rename tests fail.
3. Normal prefixes under `-R` -> repro fails (silent keep).
4. Drop `--no-renames` -> `git mv` test fails.
5. Window 5 -> 4 (or 6) -> edge tests at distance 5/6 fail.
6. Skip the "file absent from reviewed tree" check -> untracked test fails.
7. Treat git failure / missing tree as "unchanged" -> unverifiable test fails.
8. Run the check before `_fix_closes` precedence is honoured -> fix-obsolete-after-edit control fails.
9. Always run git / always add `stale` key -> differential "no git, identical bytes" test fails.
Follow the existing mutant style in `test_finalize_inputs.py` (source-text replacement + `inproc(..., module=mod)`).

### Sampling Rate
- Per task commit: quick run command above.
- Per wave merge: full suite + stdlib check.
- Phase gate: full suite green, replay diff clean, differential test green, before `/bm:verify-work`.

### Wave 0 Gaps
- [ ] `scripts/test_closeout_fresh.py` — repro, window, unverifiable, clearable, untracked, differential, mutation tests
- [ ] v2.15 materializer helper for the differential (git show of `finalize_inputs.py`, `carry_state.py`, `finalize_gate.py`, `batch_card.py`, `guard.py`, `fixcommit.py` and their imports at d5acc19 into a temp dir)
- [ ] Re-home the ~48 decision-bearing CLI fixtures (and the parity grid state) onto temp repos with a real `reviewed_tree`
- [ ] Shape 1/2 reproduction fixtures in `test_decision_continuity.py`

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Finding `file`/`line` from state are untrusted: `PATH_RE`, int checks, fail closed; never put a finding path on a git argv |
| V6 Cryptography | no | — |
| V12 Files/Resources | yes | Read-only git (`--no-optional-locks`), no writes outside `--blob-out`; temp dirs cleaned in `finally` |

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Crafted path in state used as git argument (option injection) | Tampering | Diff the whole tree; look paths up in parsed output; argv list, `--` terminator |
| Forged `reviewed_tree` in state pointing at a crafted tree to fake "unchanged" | Spoofing/Tampering | Same trust level as 999.27 `head_sha` (Phase 67); accept `OBJECT_ID_RE` + `cat-file -t` in {tree, commit}; note as residual, not fixed here |
| Hostile titles in refusal text | Tampering/Info | Helper returns hashes only; prose renders via existing join rule; no title on stderr |
| Repo-local git config altering diff output (external diff, textconv, color, relative, noprefix) | Tampering | `--no-ext-diff --no-textconv --no-color --no-relative`, explicit prefixes; `diff_ranges` rejects escape bytes |

## Sources

### Primary (HIGH confidence)
- Codebase read this session: `scripts/finalize_inputs.py`, `finalize_gate.py`, `carry_state.py` (lines 160-1130), `worktree_snap.py`, `diff_ranges.py`, `score.py` (`_snapshot_for`, `_nearby_changed`, `_stamp_ranges`, `_NEARBY_LINES`), `phases/shared/90-finalize.md`, `phases/review/00-scope.md`, `45-persist.md`, `05-state-all.md`, `commands/review.md` Phase 5 skip rules, `50-fix-loop.md` Close out
- Tests read: `test_finalize_parity_grid.py` (pin mechanism), `test_finalize_inputs.py`, `test_decision_continuity.py` helpers, `test_worktree_snap.py` harness
- Probes run this session (scratch, removed): 999.40 reproduction on current code; reverse-diff semantics; untracked / `add -N` / staged-new inclusion in `take`; blast-radius mutant (48 failures); baseline suite 4126 passed
- `.planning/ROADMAP.md` 999.28/999.31/999.40/999.44; `57-REVIEW-GAPS.md` IN-03; `57 deferred-items.md` WR-01; `60-REPRO.md` R7/R10; `57-CONTEXT.md` D-21

### Secondary / Tertiary
- None (no external library research required).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib + existing modules, verified by reading and running
- Architecture: HIGH for 999.40 (probed end to end); MEDIUM for line-set equality with the review (A1)
- Pitfalls: HIGH for pins/prefix/blast radius (verified); MEDIUM for loop cases (reasoned from code, to be proven by the "clearable" tests)

**Research date:** 2026-11-16
**Valid until:** 2026-12-16 (internal codebase; invalidated by any change to worktree_snap/carry_state/finalize_inputs)
