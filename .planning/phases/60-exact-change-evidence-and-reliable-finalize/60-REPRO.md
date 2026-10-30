# Phase 60 — Reproduction verdicts

- **Phase:** 60 — Exact change evidence and reliable Finalize
- **Date:** 2026-10-29
- **HEAD when recorded:** `ce9f8b8` (branch `feat/v2.14-phase-60`; the commit that added `REPRO_60` and completed the red fixtures, before any phase-60 production edit). The fixtures were added in `43d1905` (Task 1) and `2121c57` (Task 2); `ce9f8b8` is the RED SHA for the reverse run.
- **Scope of evidence:** no live or paid run; no network; the live `gh pr diff` fetch was not exercised (D-05). Every verdict below is a local pytest run. Range evidence comes from real `git diff` / `git format-patch` text in throwaway repos built with `gitfixture` (null global and system git config), fed through `header_rule_ranges` — an executable twin of the current `30-collect-score.md` "changed-line ranges" bullet — and then through the real `score.run -> append_pass -> carry_state -> finalize_gate` chain (`run_pass`, `pass1`, `e2e_gate`). Finalize evidence runs the real `90-finalize.md` fences in fresh `bash -s` shells with only PATH, VC_ROOT, TMPDIR and STATE_FILE (`fixtures/iplayarr45-six-row-state.json`). The PR series shape is reproduced with `git format-patch --stdout`, the same mbox commit-series shape `gh pr diff --patch` emits; no real PR was fetched.
- **Rule applied:** reproduce first; work is added only for the four qualifying classes (reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, broken required workflow). A shape that reproduced is a failing fixture committed at `ce9f8b8` and mapped to the plan that fixes it; a shape that did not reproduce would be recorded and dropped (none of the three coordinate probes fell into that arm). The `--all` route has no diff and is recorded as an unsupported fixture.

In-suite record: `test_decision_continuity.REPRO_60` (fourteen rows since 60-13 added the two second-round rows HEAD-SHA-INJECTION and STALE-GATEFILE-RERUN; twelve after 60-09 added GSD-SHELL-VAR, CONFIG-ALTERED-DIFF and GATEFILE-RETRY; nine at first recording), locked by `TestRepro60Record` (exact fourteen-id set, exact row keys, each first gap-round row's disposition starting `reproduced; fixed by 60-0` and each second-round row's starting `reproduced; fixed by 60-1`, the three coordinate dispositions limited to `reproduced; fixed by 60-04` / `did not reproduce; dropped`, and every named fixture resolved by a `def` / `class` in `test_decision_continuity.py`, `test_finalize_card.py`, `test_diff_ranges.py` or (since 60-13) `test_carry_state.py`; `TestRouteAll` is the one allowed forward reference, held in `_REPRO_60_PENDING_FIXTURES`, which 60-04 must empty).

Full suite at `ce9f8b8` (from `plugins/vibe-check/scripts`): `pytest -q` -> `15 failed, 3655 passed, 4832 subtests passed in 172.55s (0:02:52)`. The 15 failures are exactly:

```
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_deletion_keeps
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_deletion_reopens
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_insertion_keeps
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_insertion_reopens
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_net_deletion_keeps
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_net_deletion_reopens
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_ordinary_keeps
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_ordinary_reopens
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_relocated_keeps
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_relocated_reopens
FAILED test_decision_continuity.py::TestCoordinateSpaces60::test_cs60_default_staged_concat_probe
FAILED test_decision_continuity.py::TestCoordinateSpaces60::test_cs60_default_staged_finding_probe
FAILED test_decision_continuity.py::TestCoordinateSpaces60::test_cs60_mixed_concat_probe
FAILED test_decision_continuity.py::TestCoordinateSpaces60::test_cs60_pr_series_probe
FAILED test_finalize_card.py::TestFinalizeFreshShellWalk::test_walk_reaches_counts_gate_report
```

The ten `TestRealDiffRanges60` failures are all `ModuleNotFoundError: No module named 'diff_ranges'` (the builder 60-02 creates is imported lazily inside `_builder()`, so nothing else in the module is affected). Their expectations were checked against a throwaway marker-walk prototype kept outside the repo: with it on `PYTHONPATH` all ten pass (`10 passed, 20 subtests passed`). The prototype is not committed and proves only that the fixtures are satisfiable, not that 60-02's builder is correct.

---

## V1 — 999.24-WIDEN: default-context ranges are ~8 lines wide (EVID-01)

**Verdict: REPRODUCED at `ce9f8b8` -> to be fixed by 60-02 + 60-04.**

**Failure as the owner would see it.** A decision 6–8 lines from an unrelated edit is asked again. The owner dismisses a finding at line 40; the next run edits line 48, eight lines away and outside the 5-line window. Finalize re-asks the dismissal ("code next to it changed") because the ranges are read from git's default diff header, which includes three unchanged context lines on each side of the edit (lines 45–51).

**Fixture.** `TestRepro60Evidence.test_edit_eight_beneath_reopens_through_default_context` (green: documents the defect) and `TestRealDiffRanges60` (red until the builder exists: the exact-range boundary pairs). The documenting test commits `base_file(60)` as `src/a.py`, edits line 48, and reads `git diff --no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/ HEAD`: header `@@ -45,7 +45,7 @@` -> `header_rule_ranges` `{src/a.py: [[45, 51]]}` -> `decision_state == "stale"`, `stale_cause == "nearby"`, `nearby_at == 2`, gate does not write. Its subtest reads the same edit under `-U0` (`[[48, 48]]`) and the decision is kept, so the over-ask comes from the context lines alone.

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k TestRepro60Evidence
4 passed, 154 deselected, 1 subtests passed in 0.22s
$ pytest -q test_decision_continuity.py -k TestRealDiffRanges60
E       ModuleNotFoundError: No module named 'diff_ranges'
10 failed, 148 deselected in 1.11s
```

Green at: 53fb637 (60-02 builder; `TestRealDiffRanges60` 10 passed) + `66d63de` (60-04: the `changed-line ranges` bullet now pipes one range source per route through `scripts/diff_ranges.py` and no longer reads hunk headers).

---

## V2 — 999.24-DELETION-RULE: the deletion rule never fires on a real diff (EVID-01)

**Verdict: REPRODUCED at `ce9f8b8` -> to be fixed by 60-02.**

**Failure as the owner would see it.** The documented rule for a deleted line (the two lines on either side of the deletion point count as changed) is never applied, because a default diff never prints the deletion-only header it keys on. A deleted guard is instead read as an ordinary 6-line hunk, which over-asks at distance and is exact only by accident.

**Fixture.** `TestRepro60Evidence.test_default_context_widens_and_deletion_rule_never_fires` (green: documents the defect): deleting line 34 gives `@@ -31,7 +31,6 @@` under the default diff -> `[[31, 36]]`, and `@@ -34 +33,0 @@` only under `-U0` -> `[[33, 34]]`; no `+T,0` header appears in the default diff. Red pair: `test_rd60_deletion_reopens` (delete 34; builder must give `[[33, 34]]`; decided line moves to 39, window 34..44 -> stale) and `test_rd60_deletion_keeps` (delete 33 -> `[[32, 33]]` -> current).

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k "test_rd60_deletion"
E       ModuleNotFoundError: No module named 'diff_ranges'
2 failed, 156 deselected in 0.27s
```

Green at: 53fb637 (60-02 builder; `test_rd60_deletion_reopens` / `test_rd60_deletion_keeps` pass: a pure deletion gives `[max(T,1), T+1]` from the `-` markers at any context width) + 66d63de (60-04: every route reads its range source through the builder).

---

## V3 — IN-04-NET-DELETION: a net-deletion replace is a silent keep at the boundary (EVID-02, D-02)

**Verdict: REPRODUCED at `ce9f8b8` -> to be fixed by 60-02.**

**Failure as the owner would see it.** Three lines just above a dismissed finding are replaced by one. The decision moves to line 38 with the change at the window's edge, yet Finalize does not re-ask: once ranges are exact, a replace hunk that removes more lines than it adds covers only its new lines, so the line just after the replacement (the removed lines' place) is not counted as changed.

**Fixture.** `TestRepro60Evidence.test_net_deletion_keeps_under_header_rule_even_at_u0` (green: documents the keep): lines 32–34 replaced by one line, `-U0` header `@@ -32,3 +32 @@` -> header rule `[[32, 32]]` -> decision at 38 `current`, gate `write`. Red pair: `test_rd60_net_deletion_reopens` (builder must give `[[32, 33]]` under D-02 -> stale) and `test_rd60_net_deletion_keeps` (lines 31–33 -> `[[31, 32]]` -> current).

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k "test_net_deletion_keeps_under_header_rule_even_at_u0"
1 passed, 157 deselected in 0.10s
$ pytest -q test_decision_continuity.py -k "test_rd60_net_deletion"
E       ModuleNotFoundError: No module named 'diff_ranges'
2 failed, 156 deselected in 0.26s
```

Green at: 53fb637 (60-02 builder; `test_rd60_net_deletion_reopens` / `test_rd60_net_deletion_keeps` pass: a net-deletion replace also covers the line after it, D-02) + 66d63de (60-04 route wiring).

---

## V4 — PR-SERIES: PR ranges read from a commit series use each commit's own line numbers (EVID-03)

**Verdict: REPRODUCED at `ce9f8b8` -> to be fixed by 60-04.** Disposition in `REPRO_60`: `reproduced; fixed by 60-04`.

**Failure as the owner would see it.** On a PR review, a finding on a line the PR actually changed is scored as if it were outside the diff (no +20). With a lower-confidence finding the difference is enough to drop it below the threshold — a real finding on changed code is silently lost. Cause: `gh pr diff --patch` is a per-commit series; commit A's edit is numbered in commit A's file (line 10), but the head file has it at line 15 after commit B inserted five lines above.

**Fixture.** `TestCoordinateSpaces60.test_cs60_pr_series_probe`: commit A edits line 10, commit B inserts 5 lines at the top; `git format-patch --stdout -U0 <base>..HEAD` (two `From <sha>` mbox headers) -> `header_rule_ranges` `[[10, 10], [1, 5]]`; a fresh finding at head line 15 (conf 80) scores 70, not 90 (`scored_in_diff` false). Control `test_cs60_pr_cumulative_control`: `git diff -U0 <base> HEAD` -> `[[1, 5], [15, 15]]` -> in the diff (green).

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k test_cs60_pr_series_probe
E       AssertionError: False is not true : the head-file line of commit A's edit (15) is not in the patch-series ranges
1 failed, 157 deselected in 0.16s
```

Green at: 66d63de (60-04 prose) + 39f6dbd (route tests) + fb8b32b (probe). Prose `66d63de` (PR range source `gh pr diff <ref> --color never`, never `--patch`); route tests `39f6dbd` (`TestRoutePR`: pinned real capture + series refused with `REASON_MBOX`); the probe reads the cumulative diff through the builder and passes in the 60-04 Task 3 commit (the old series reading stays in it as a documenting assertion).

---

## V5 — MIXED-COORD: GSD / incremental concatenation mixes HEAD and working-tree lines (EVID-03)

**Verdict: REPRODUCED at `ce9f8b8` -> to be fixed by 60-04.** Disposition in `REPRO_60`: `reproduced; fixed by 60-04`.

**Failure as the owner would see it.** A committed change 5 lines from a dismissed finding is missed when there are uncommitted edits above it: the decision is kept and Finalize writes without asking (a silent keep). Cause: the GSD and incremental routes concatenate `<base>..HEAD` (HEAD line numbers) with the staged and unstaged diffs (index / working-tree line numbers); the committed edit keeps its HEAD line (35) while the decision is read on the working tree, where it is now line 50 and the edit is at 45.

**Fixture.** `TestCoordinateSpaces60.test_cs60_mixed_concat_probe`: decision at 40; committed edit at 35; uncommitted 10-line insertion at the top; `git diff -U0 <base>..HEAD` + `git diff -U0 --staged` + `git diff -U0` -> `[[35, 35], [1, 10]]` -> decision (line 50) `current`. The probe asserts `stale`. Control `test_cs60_single_diff_control`: `git diff -U0 <base>` (commit vs working tree) -> `[[1, 10], [45, 45]]` -> stale (green).

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k test_cs60_mixed_concat_probe
E   AssertionError: 'current' != 'stale'
1 failed, 157 deselected in 0.18s
```

Green at: 66d63de (60-04 prose) + 39f6dbd (route tests) + fb8b32b (probe). Arm chosen: single-diff range source (reproduced) — GSD pass 1 `git diff $PHASE_START` (`git diff HEAD` when empty), any stateful route pass >= 2 `git diff $LAST_REVIEWED_SHA` (`66d63de`, 30-collect-score.md table, 00-scope.md mode 4, 05-state.md step 3). Route tests `39f6dbd` (`TestRouteGSD`, `TestRouteIncremental`); the probe now reads `git diff <base>` through the builder and passes in the 60-04 Task 3 commit, with the concatenated reading kept as a documenting assertion (silent keep).

---

## V6 — DEFAULT-STAGED: the default route's `--staged` section is numbered in the index (EVID-03)

**Verdict: REPRODUCED at `ce9f8b8` (both probes) -> to be fixed by 60-04.** Disposition in `REPRO_60`: `reproduced; fixed by 60-04`.

**Failure as the owner would see it.** Probe A (wrong reopen): a dismissal is asked again although nothing near it changed. Probe B (mislocated finding): a finding quoted at the line number the staged section shows is not inside the working-tree ranges, so it scores as off-diff. Cause: the default route assembles `git diff HEAD` (working-tree numbering, already includes every staged change) with `git diff --staged` (index numbering); an unstaged insertion above shifts the working tree but not the index.

**Fixture.** Decision at 40; edit at line 48 staged with a real `git add`; 10 lines then inserted at the top without staging. On disk the decided line is 50 and the staged edit is at 58 (outside 45..55, so the correct outcome is keep). `git diff -U0 HEAD` -> `[[1, 10], [58, 58]]`; `git diff -U0 --staged` -> `[[48, 48]]`.
- Probe A `test_cs60_default_staged_concat_probe`: concatenated ranges `[[1, 10], [58, 58], [48, 48]]` -> decision `stale` (asserts `current`). Outcome: reproduced as a wrong reopen.
- Probe B `test_cs60_default_staged_finding_probe`: a fresh finding at line 48 under the `git diff HEAD` ranges is not in the diff (asserts in the diff). Outcome: reproduced as a mislocated finding. Note for 60-04: on disk line 48 is unchanged code (old line 38); the probe shows the two sections disagree on numbering, and the coordinate contract it pins is that on the default route findings and ranges are both in working-tree line numbers (the file as it is on disk).
- Control `test_cs60_default_head_only_control`: `git diff -U0 HEAD` alone -> current (green). Boundary control `test_cs60_default_head_only_boundary_control`: staged edit at 45 (on disk 55) -> `[[1, 10], [55, 55]]` -> stale (green).

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k test_cs60_default_staged_concat_probe
E   AssertionError: 'stale' != 'current'
1 failed, 157 deselected in 0.16s
$ pytest -q test_decision_continuity.py -k test_cs60_default_staged_finding_probe
E       AssertionError: False is not true : line 48 (the staged section's own numbering) is not in the working-tree ranges
1 failed, 157 deselected in 0.17s
```

Green at: 66d63de (60-04 prose) + 39f6dbd (route tests) + fb8b32b (probes). Arm chosen: `git diff HEAD` alone as the range source (reproduced), with the explicit working-tree coordinate contract (`66d63de`); reviewers still receive all three default-route commands unchanged. Route tests `39f6dbd` (`TestRouteDefault`, literal working-tree ranges `[[1, 10], [58, 58]]`, staged with a real `git add`). Probe A now keeps through the builder on `git diff HEAD`; Probe B is recorded as what it is: coordinate disagreement between the two sections, not a lost changed line — the line it flags (48 on disk) is unchanged code, so under the contract it is correctly outside the ranges, and the staged edit's working-tree line 58 is inside them. Both pass in the 60-04 Task 3 commit.

---

## V7 — ALL-ROUTE: `--all` has no diff (EVID-03, D-06)

**Verdict: UNSUPPORTED FIXTURE — recorded, no fix.**

**Failure as the owner would see it.** None. `05-state-all.md` (ii) forces pass 1 with an empty carry-forward on every `--all` run, so there is no diff: `in_diff` never gates (validity comes from the reviewed set), and `nearby_at` is never stamped. There is no range to build and nothing to reproduce.

**Fixture.** `TestRouteAll` — a forward reference 60-04 adds (allowed only through `_REPRO_60_PENDING_FIXTURES`; `TestRepro60Record.test_every_fixture_exists` fails once the class exists and the allowlist still names it).

**Command and output:**

```
$ pytest -q test_decision_continuity.py -k TestRepro60Record
3 passed, 155 deselected, 26 subtests passed in 0.06s
```

Green at: 39f6dbd (60-04; unsupported fixture recorded, nothing fixed) + fb8b32b (allowlist emptied). `TestRouteAll` added in `39f6dbd` (test_diff_ranges.py: asserts 05-state-all.md (ii) still forces `$PASS_NUMBER = 1` and `$CARRYFORWARD = []`, `ranges_from_diff("") == {}`, and `score.run` with `all_mode=True, changed_line_ranges={}` keeps a reviewed-set finding). `_REPRO_60_PENDING_FIXTURES` emptied and the fixture lookup extended to test_diff_ranges.py in the 60-04 Task 3 commit.

---

## V8 — 999.25-BLOBFILE: Finalize stops from a fresh shell (FINL-01, D-09)

**Verdict: REPRODUCED at `ce9f8b8` -> to be fixed by 60-03.**

**Failure as the owner would see it.** Finalize stops with "I'm uncertain about Finalize mode — carry_state.py failed; nothing was written or archived." although the state is fine. The HEAD-fingerprints file is held in a shell variable (`$BLOBFILE`) that no later Bash call sees; no fence ever prints `BLOBFILE=<path>`, so the counts fence passes an empty path and the helper refuses it.

**Fixture.** `TestFinalizeFreshShellWalk.test_walk_reaches_counts_gate_report` (red: asserts a fence prints `BLOBFILE=`, then walks counts -> gate -> rows with literals) and `test_counts_fence_without_literal_exits_two` (green, stays as the D-09 mutant: the counts fence run fresh with `"$BLOBFILE"` unsubstituted -> helper `refused: head-blobs file is missing or not a JSON object`, exit 2; the fence then halts with its uncertain sentence, exit 1). The walk was also checked against an in-memory corrected prose (a `BLOBFILE=` fence and a printed gate-input file) outside the repo: it passes, so it can go green.

**Command and output:**

```
$ pytest -q test_finalize_card.py -k TestFinalizeFreshShellWalk
E       AssertionError: unexpectedly None : no Finalize fence prints BLOBFILE= (D-09): the counts and rows fences read "$BLOBFILE", which no fresh shell holds, so carry_state.py refuses the empty path and Finalize stops
FAILED test_finalize_card.py::TestFinalizeFreshShellWalk::test_walk_reaches_counts_gate_report
1 failed, 2 passed, 70 deselected in 0.14s
```

Green at: b8fb21a (60-03 prose: step 1 mints and prints `BLOBFILE=`, the gate reads a printed `GATEFILE=`; `test_walk_reaches_counts_gate_report` passes) + fd8c1b9 (walk green on both routes, retry and stale-attempt walks). `test_counts_fence_without_literal_exits_two` stays green as the D-09 mutant.

---

## V9 — GATE-INPUT-CROSS-CALL: the gate fence reads a variable set in an earlier call (FINL-01, Pitfall 6)

**Verdict: REPRODUCED at `ce9f8b8` -> to be fixed by 60-03.**

**Failure as the owner would see it.** Even with the blob file fixed, Finalize would stop with "I'm uncertain about Finalize mode — finalize_gate.py failed; nothing was written or archived." The gate fence pipes `"$FINALIZE_GATE_INPUT_JSON"`, set in an earlier Bash call; a fresh shell sends empty stdin and the gate dies with a `JSONDecodeError` traceback (exit 1).

**Fixture.** `TestFinalizeFreshShellWalk.test_gate_fence_reads_cross_call_variable_today` (green today: asserts the fence reads the variable and that a fresh run exits non-zero with the halt sentence). 60-03 inverts its `assertIn(GATE_INPUT_VAR, gate)` line once the input is carried as a printed literal; the walk in V8 already asserts the variable is absent.

**Command and output:**

```
$ pytest -q test_finalize_card.py -k test_gate_fence_reads_cross_call_variable_today
1 passed, 72 deselected in 0.08s
(fresh run of the gate fence: json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
 I'm uncertain about Finalize mode — finalize_gate.py failed; nothing was written or archived.)
```

Green at: fd8c1b9 (60-03: `test_gate_fence_reads_cross_call_variable_today` inverted to assert the gate fence reads the printed `GATEFILE=` literal, not `$FINALIZE_GATE_INPUT_JSON`) on the b8fb21a prose; 53b35ed adds the whole-file `no_cross_call_gate_input` lock.

---

## Controls (green on current code)

- `TestRepro60Evidence` (4): header twin agrees with `replay.hunk_ranges` except on `+T,0` headers; default context widens and never prints a deletion header; the L+8 over-ask (and its `-U0` keep subtest); the net-deletion keep under the header rule.
- `TestCoordinateSpaces60` controls (4): `test_cs60_pr_cumulative_control`, `test_cs60_single_diff_control`, `test_cs60_default_head_only_control`, `test_cs60_default_head_only_boundary_control`.
- `TestFinalizeFreshShellWalk` (2): `test_counts_fence_without_literal_exits_two`, `test_gate_fence_reads_cross_call_variable_today`.
- `TestRepro60Record` (3): record complete, every fixture exists (with the `TestRouteAll` allowlist), fixture lookup trips on a missing name.
- Unchanged locks still green: `TestNearbyEdit`, `TestRepro59Record`, `TestGolden` (GOLDEN_DIGEST untouched); `test_finalize_card.py` outside the walk (70 passed).

## D-04 audit — other context assumptions

Audit grep, run from the repo root at 60-04 (after the prose fix):

```
grep -rn -i -E "three lines of context|3 lines of context|-U[0-9]|--unified|context lines|hunk header|hunk_ranges|\+start,count" \
  plugins/vibe-check/phases plugins/vibe-check/agents plugins/vibe-check/templates plugins/vibe-check/scripts/*.py | grep -v scripts/test_
```

Hits: `30-collect-score.md:64` (the rewritten bullet, which now says never to read hunk headers), `diff_ranges.py:10,18` (the builder's own docstring: display context does not change its answer), `replay.py:203,204,386` (`hunk_ranges`). No agent or template hit. Every hit and every candidate D-04 names:

| Location | What it assumes | Verdict |
|----------|-----------------|---------|
| `phases/review/30-collect-score.md` `changed-line ranges` bullet | Ranges were read from each hunk header `+start,count`, so git's three context lines on each side were counted as changed and a deletion header never appeared | fixed in 60-04 (`66d63de`): ranges come only from `+`/`-` body lines via `scripts/diff_ranges.py`, one range source per route, fail-closed fence; builder from 60-02 (`53fb637`) |
| `phases/review/00-scope.md` mode 1 (default): `git diff HEAD` + `git diff --staged` + `git status --short` | The two diff sections were both range sources; `--staged` numbers lines in the index, not the working tree (DEFAULT-STAGED reproduced) | fixed in 60-04: range source is `git diff HEAD` alone with the working-tree coordinate contract; the three reviewer commands are byte-identical (reviewers keep the staged view) |
| `phases/review/00-scope.md` mode 4 (GSD): `$PHASE_RANGE` + staged + unstaged | Concatenating `<base>..HEAD` (HEAD lines) with staged/unstaged (index/working-tree lines) gives one coordinate space (MIXED-COORD reproduced) | fixed in 60-04: range source `git diff $PHASE_START` (`git diff HEAD` when empty); reviewers' diff assembly unchanged |
| `phases/review/05-state.md` step 3 (incremental): `$LAST_REVIEWED_SHA..HEAD` + staged + unstaged | Same mixed-coordinate concatenation on pass >= 2 (MIXED-COORD reproduced) | fixed in 60-04: range source `git diff $LAST_REVIEWED_SHA`; reviewers' incremental diff unchanged |
| `phases/review/00-scope.md` mode 2 (PR): `gh pr diff <ref> --patch` | The `--patch` commit series numbers each hunk in its own commit's file (PR-SERIES reproduced) | fixed in 60-04: range source `gh pr diff <ref> --color never` (cumulative); the builder refuses a series (`REASON_MBOX`); the agents' `--patch` view is unchanged (agents' view only) |
| `--all` (mode 5, `05-state-all.md` (ii)) | None: no diff on any pass, `changed_line_ranges = {}`, `in_diff` never gates | unaffected — unsupported fixture recorded per D-06 (`TestRouteAll`, `39f6dbd`) |
| `30-collect-score.md` `±2 source window` bullet (`source_window`) | A finding-centred ±2 window read from HEAD for silenced markers; it never reads diff context | unaffected — independent of diff context width |
| `score.py` re-check trigger `_independent_trigger` -> `_nearby_changed` (and `_line_in_ranges` for `in_diff`) | Consumes `changed_line_ranges` as given | unaffected code — fixed by construction, because its input is now exact |
| `replay.py` `replay.hunk_ranges` (lines 203-204, used at 386) | Reads ranges from new-side headers, context included | unaffected — intentionally context-inclusive: it rebuilds envelopes of archived B3 runs whose ranges were read that way, so replay must reproduce them; pinned by `TestReplayPin`; the replay gate in the next phase (GATE-02) depends on it. Do not change. `git diff --stat -- plugins/vibe-check/scripts/replay.py` is empty at 60-04 |
| Stored `snapshot.nearby_at` stamps written from the old, wider ranges | A stamp may have been set by a context line | unaffected — fails toward asking (an extra re-ask, never a silent keep); no migration |
| `diff_ranges.py` docstring (lines 10, 18) | Mentions `-U0` / default context only to state the answer does not depend on them | unaffected — documentation of the builder's contract |

D-05: the live `gh pr diff` fetch was not exercised; the PR route is proven on a checked-in capture. Provenance of `plugins/vibe-check/scripts/fixtures/pr-cumulative.diff`: captured from `gh` (not a fallback) on 2026-10-29 with `gh pr diff 5 --color never` — PR #5 of this repo, base `f2b6a3674d0d0dc62ab6dca3a00816c070943884`, head `98f63aa7834af6a04c5a38d925d8b1ca457111bc` (`gh pr view 5 --json headRefOid,baseRefOid`), squash-merged as the single-parent commit `6dfac6436427cc385fe1937f73ed841fef6c8ffb`. Cut: four whole file sections at `diff --git` boundaries (capture lines 4897-5182: `50-fix-loop.md`, `90-finalize.md`, `batch_card.py`, `carry_state.py`), 286 lines, no mbox line, scanned for `key|token|secret|password` (0 hits). Cross-check at capture time: the same four paths from the local `git diff --no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/ f2b6a36 98f63aa…` (f2b6a36 is the merge base) through the builder gave identical ranges. All three SHAs pass `git rev-parse --verify <sha>^{commit}`.

## Reverse run

The current tests were run against the production code from before any phase-60 fix. Run on 2026-10-29 from HEAD `ec0c9d8`.

- Worktree: `git worktree add --detach <scratchpad>/pre60 ce9f8b8`. `git -C <scratchpad>/pre60 rev-parse --short HEAD` printed `ce9f8b8`, the RED SHA from 60-01-SUMMARY. In that tree `diff_ranges.py` does not exist, `30-collect-score.md` / `00-scope.md` / `05-state.md` still read hunk headers and concatenate diffs, and `90-finalize.md` still holds `$BLOBFILE` and `$FINALIZE_GATE_INPUT_JSON` across calls.
- Copied in from HEAD `ec0c9d8`: `test_decision_continuity.py`, `test_finalize_card.py`, `test_diff_ranges.py`. (`fixtures/pr-cumulative.diff` was not copied; only `test_diff_ranges.py` reads it, and that file cannot collect there anyway.)
- Afterwards: `git worktree remove --force <scratchpad>/pre60`, then `git worktree prune`. `git worktree list | grep -c pre60` printed `0`.

```
$ pytest -q -p no:cacheprovider test_decision_continuity.py -k "TestRealDiffRanges60 or TestCoordinateSpaces60 or TestRepro60"
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_deletion_keeps
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_deletion_reopens
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_insertion_keeps
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_insertion_reopens
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_net_deletion_keeps
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_net_deletion_reopens
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_ordinary_keeps
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_ordinary_reopens
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_relocated_keeps
FAILED test_decision_continuity.py::TestRealDiffRanges60::test_rd60_relocated_reopens
FAILED test_decision_continuity.py::TestCoordinateSpaces60::test_cs60_default_staged_concat_probe
FAILED test_decision_continuity.py::TestCoordinateSpaces60::test_cs60_default_staged_finding_probe
FAILED test_decision_continuity.py::TestCoordinateSpaces60::test_cs60_mixed_concat_probe
FAILED test_decision_continuity.py::TestCoordinateSpaces60::test_cs60_pr_series_probe
14 failed, 11 passed, 133 deselected, 27 subtests passed in 2.18s

$ pytest -q -p no:cacheprovider -rf test_finalize_card.py -k "TestFinalizeFreshShellWalk or printed_paths or file_refs or cross_call or retry_rule or refused_rule"
FAILED test_finalize_card.py::TestFinalizeFreshShellWalk::test_card_route_records_then_writes
FAILED test_finalize_card.py::TestFinalizeFreshShellWalk::test_gate_fence_reads_cross_call_variable_today
FAILED test_finalize_card.py::TestFinalizeFreshShellWalk::test_retry_mints_new_blobfile_after_missing_path
FAILED test_finalize_card.py::TestFinalizeFreshShellWalk::test_stale_earlier_attempt_file_does_not_govern
FAILED test_finalize_card.py::TestFinalizeFreshShellWalk::test_walk_reaches_counts_gate_report
FAILED test_finalize_card.py::TestGapRoundFinalize::test_file_refs_created_holds
FAILED test_finalize_card.py::TestGapRoundFinalize::test_no_cross_call_gate_input_holds
FAILED test_finalize_card.py::TestGapRoundFinalize::test_refused_rule_holds
FAILED test_finalize_card.py::TestGapRoundFinalize::test_retry_rule_holds
SUBFAILED[empty] test_finalize_card.py::TestFinalizeFreshShellWalk::test_malformed_gatefile_shows_only_stop_sentence
SUBFAILED[not json] test_finalize_card.py::TestFinalizeFreshShellWalk::test_malformed_gatefile_shows_only_stop_sentence
SUBFAILED[mutant: the .err redirect removed] test_finalize_card.py::TestFinalizeFreshShellWalk::test_malformed_gatefile_shows_only_stop_sentence
SUBFAILED[mutant: BLOBFILE mktemp fence removed] test_finalize_card.py::TestGapRoundFinalize::test_mutant_file_refs_created
SUBFAILED[mutant: BLOBFILE path not printed] test_finalize_card.py::TestGapRoundFinalize::test_mutant_printed_paths
SUBFAILED[mutant: GATEFILE path not printed] test_finalize_card.py::TestGapRoundFinalize::test_mutant_printed_paths
SUBFAILED[mutant: cross-call gate input restored] test_finalize_card.py::TestGapRoundFinalize::test_mutant_cross_call_gate_input
SUBFAILED[mutant: earlier attempt's BLOBFILE may be reused] test_finalize_card.py::TestGapRoundFinalize::test_mutant_retry_rule
SUBFAILED[mutant: rebuild paragraph gone] test_finalize_card.py::TestGapRoundFinalize::test_mutant_retry_rule
SUBFAILED[mutant: rebuild reuses the old file] test_finalize_card.py::TestGapRoundFinalize::test_mutant_retry_rule
SUBFAILED[mutant: refused step retried] test_finalize_card.py::TestGapRoundFinalize::test_mutant_refused_rule
SUBFAILED[mutant: stop sentence dropped] test_finalize_card.py::TestGapRoundFinalize::test_mutant_refused_rule
21 failed, 8 passed, 70 deselected, 3 subtests passed in 0.51s

$ pytest -q -p no:cacheprovider test_diff_ranges.py
E   ModuleNotFoundError: No module named 'diff_ranges'
ERROR test_diff_ranges.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

The 15 red fixtures from 60-01. Each fails again at `ce9f8b8` and passes at HEAD:

| Fixture (60-01 red set, 15) | Pre-fix result | Verdict | Green at |
|---|---|---|---|
| `TestRealDiffRanges60`: the ten `test_rd60_<shape>_reopens` / `_keeps` pairs (ordinary, insertion, deletion, net_deletion, relocated) | fail (`No module named 'diff_ranges'` from the lazy `_builder()`) | V1, V2, V3 | 53fb637 |
| `TestCoordinateSpaces60::test_cs60_pr_series_probe` | fail | V4 | fb8b32b (prose 66d63de) |
| `TestCoordinateSpaces60::test_cs60_mixed_concat_probe` | fail | V5 | fb8b32b (prose 66d63de) |
| `TestCoordinateSpaces60::test_cs60_default_staged_concat_probe` | fail | V6 | fb8b32b (prose 66d63de) |
| `TestCoordinateSpaces60::test_cs60_default_staged_finding_probe` | fail | V6 | fb8b32b (prose 66d63de) |
| `TestFinalizeFreshShellWalk::test_walk_reaches_counts_gate_report` | fail | V8 | b8fb21a |

All 15 appear in the failure list above. No 60-01 red fixture passed pre-fix. The other red results are the later plans' own guards, which also fail on the pre-fix code:
- `test_gate_fence_reads_cross_call_variable_today` (V9). It was inverted at fd8c1b9, so it now fails pre-fix, as it should.
- The other four 60-03 walks and the four 60-03 prose "holds" locks.
- The malformed-GATEFILE owner-view subtests.
- The 60-03 mutant subtests. Pre-fix their anchor text is absent, so the mutation cannot apply.
- All of `test_diff_ranges.py` fails at collection. That covers 60-02's contract tests and 60-04's route tests, including `TestRouteAll` for V7.

The 11 + 8 tests that pass pre-fix are expected to:
- The `TestRepro60Evidence` documenting tests. They assert the defect through `header_rule_ranges`, which lives in the test file.
- The four `TestCoordinateSpaces60` controls, and `TestRepro60Record`.
- `test_counts_fence_without_literal_exits_two`, the D-09 mutant. The unsubstituted counts fence exits non-zero both before and after the fix.
- `test_printed_paths_holds`. Pre-fix there was no unprinted mktemp path to flag. The BLOBFILE defect was a missing fence, which `test_file_refs_created_holds` catches.
- The parent tests of the mutant groups. Their failures show up as subtests.

## Suite at close

All runs are from `plugins/vibe-check/scripts` in the real checkout at HEAD `ec0c9d8`.

```
$ pytest -q -p no:cacheprovider
3765 passed, 4930 subtests passed in 170.01s (0:02:50)

$ pytest -q -p no:cacheprovider test_replay.py
64 passed, 10 subtests passed in 9.98s
```

- 0 failed. At the RED SHA the same suite gave `15 failed, 3655 passed`, and the 15 are exactly the 60-01 red set above.
- **Replay deltas for Phase 61 GATE-02: none observed.** `git diff --stat ce9f8b8 HEAD -- replay.py test_replay.py score.py finalize_gate.py` is empty, so:
  - `replay.hunk_ranges` is unchanged. It is intentionally context-inclusive and pinned by `TestReplayPin`.
  - No expected value in `test_replay.py` moved.
  - `score.py` was not edited. Its consumers of `changed_line_ranges` are fixed by construction, because their input is now exact.
  - Archived envelopes replay ranges as they were recorded, so the exact-range change cannot move them. If Phase 61 sees replay drift, no Phase-60 change explains it, and it must be treated as a finding.
- GOLDEN_DIGEST is unchanged (`TestGolden` passes in the full run).

## Gap round (60-VERIFICATION, 2026-10-29)

60-VERIFICATION.md (committed at `2f84d2e`, "docs(60): verification gaps_found") found three blocking gaps after the first close. `2f84d2e` is the pre-gap-round production base: every gap below was reproduced there, and the reverse run below uses it. The same rule applies: reproduce first, and add work only for the four qualifying classes. All three qualify. GSD-SHELL-VAR is a silent loss of a qualifying finding (a committed change drops out of the ranges with exit 0). CONFIG-ALTERED-DIFF is a broken required workflow (every pass halts under `diff.suppressBlankEmpty`) plus a fail-open on colored text. GATEFILE-RETRY is a broken required workflow (the documented Finalize retry cannot recover). Each gap was fixed by its own red -> green pair (60-06, 60-07, 60-08). The pytest output below is copied from those plans' SUMMARYs, not retyped.

## V10 — GSD-SHELL-VAR: the GSD / pass-2+ range source reads a shell variable a fresh Bash call does not hold (EVID-03)

**Verdict: REPRODUCED at `2f84d2e` -> fixed by 60-07.**

**Failure as the owner would see it.** No error is shown. On a GSD review, or on any pass 2+, the range-source row was `git diff <flags> $PHASE_START` / `$LAST_REVIEWED_SHA`. Each Bash call is a fresh shell, so the variable is empty there, and the unquoted empty word disappears. git then runs `git diff <flags>` (index vs working tree), which exits 0 with only the uncommitted lines. In the probe (committed edit at line 3, uncommitted edit at line 5) the ranges were `{"f.txt": [[5, 5]]}`. The committed change is missing, so a finding on it loses `in_diff` and a decision on it is never reopened: a silent keep.

**Fixture.** `TestProseRangeFence::test_gsd_route_fresh_shell_includes_committed_change`, `test_incremental_route_fresh_shell_includes_committed_change`, `test_unsubstituted_variable_halts_instead_of_narrowing` (its "old unquoted variable" subtests document the narrowing: rc 0, `[[5, 5]]`), and `TestScopePhaseStartFence` (00-scope.md must print `PHASE_START=` for the literal to be carried). All are in `test_diff_ranges.py`.

**Command and output at the RED SHA `b1bc970`:**

```
$ pytest -q -p no:cacheprovider test_diff_ranges.py -k "ProseRangeFence or ScopePhaseStart or RangeSourceLines"
14 failed, 9 passed, 82 deselected, 5 subtests passed in 1.59s
```

The failing set includes the two fresh-shell route tests (the quoted `"<phase-start-sha>"` / `"<last-reviewed-sha>"` placeholder was not in the row), both "quoted, left unsubstituted" subtests, `test_gsd_empty_phase_start_uses_head`, `test_literal_substitution_sentence_present` and both `TestScopePhaseStartFence` tests.

Green at: 2a63cb5 (60-07). The GSD and pass-2+ rows now end in a quoted literal placeholder that the agent substitutes from the printed `PHASE_START=` line or from `head_sha`. A fresh-shell run gives `{"f.txt": [[3, 3], [5, 5]]}`. A quoted placeholder left empty makes git exit 128 (`fatal: ambiguous argument ''`), and the fence halts through `pipefail` instead of narrowing.

---

## V11 — CONFIG-ALTERED-DIFF: repo or user git config changes the text the range builder reads (EVID-01)

**Verdict: REPRODUCED at `2f84d2e` -> fixed by 60-06 (builder) + 60-07 (fixed flags).**

**Failure as the owner would see it.** There are two faces. (a) With `diff.suppressBlankEmpty=true`, an ordinary edit next to a blank line gives a hunk body line that is empty instead of a single space. `diff_ranges.py` refused it with `unexpected line in hunk body` (exit 2), so every review pass halted. (b) A colored diff (no `--no-color`, `color.ui=always`) parsed to `{}` with exit 0: no ranges, no error, and every finding outside the diff. A textconv driver shifted the ranges (`[[14, 14], [22, 23]]` for the real `[[12, 12], [20, 21]]`), and `diff.relative` run from a subdirectory dropped them (`{}`).

**Fixture.** `TestHazards::test_suppress_blank_empty_context_is_context`, `TestRefusals::test_refuses_colored_diff`, `TestRefusals::test_refuses_non_diff_text` (60-06), and `TestProseRangeFence::test_diff_relative_from_subdirectory_changes_nothing` with `test_hostile_external_diff_config_changes_nothing` (60-07). All are in `test_diff_ranges.py`.

**Command and output at the RED SHAs:**

```
$ pytest -q -p no:cacheprovider test_diff_ranges.py            # at 11d2b76 (60-06 red)
12 failed, 82 passed, 60 subtests passed in 7.67s

$ pytest -q -p no:cacheprovider test_diff_ranges.py -k "ProseRangeFence or ScopePhaseStart or RangeSourceLines"   # at b1bc970 (60-07 red)
14 failed, 9 passed, 82 deselected, 5 subtests passed in 1.59s
```

At `11d2b76` the suppressBlankEmpty subtests failed with `RangeError: unexpected line in hunk body`. The colored and non-diff refusals failed because no `RangeError` was raised, and `test_colored_diff_exits_two_with_reason_only` got rc 0 instead of 2. At `b1bc970`, under textconv, the fence printed `{"f.txt": [[14, 14], [22, 23]]}`, and from `sub/` it printed `{}`.

Green at: b878870 (60-06: an empty hunk body line is read as blank context; any line starting with ESC is refused with `colored or escaped diff`, and non-empty text with no diff line is refused with `not a unified diff`, both exit 2; empty, binary-only and mode-only diffs stay `{}`) + 2a63cb5 (60-07: every range-building git command carries `--no-color --no-ext-diff --no-textconv --no-relative --src-prefix=a/ --dst-prefix=b/`).

---

## V12 — GATEFILE-RETRY: Finalize's one rebuild re-mints BLOBFILE but reuses a broken GATEFILE (FINL-02)

**Verdict: REPRODUCED at `2f84d2e` -> fixed by 60-08.**

**Failure as the owner would see it.** On attempt 1 the `GATEFILE=` write leaves an empty file, and the gate fence stops with "I'm uncertain about Finalize mode — finalize_gate.py failed; nothing was written or archived." (the traceback goes to `<GATEFILE>.err`). The documented one automatic rebuild re-minted only `BLOBFILE`. Re-running the gate on the same `GATEFILE` halts in exactly the same way, so the retry the prose promises cannot recover.

**Fixture.** `TestFinalizeFreshShellWalk::test_retry_mints_new_gatefile_after_gate_input_failure` (a fresh-shell walk: an empty GATEFILE halts, re-running on the same file halts the same way, a re-minted GATEFILE with flags from the rebuilt counts passes, and the rule text must hold) and `test_gatefile_missing_path_is_a_named_trigger`, both in `test_finalize_card.py`. The `TestGapRoundFinalize::test_retry_rule_holds` / `test_mutant_retry_rule` GATEFILE needles lock the prose.

**Command and output at the RED SHA `f100185`:**

```
$ pytest -q -p no:cacheprovider test_finalize_card.py -k "retry or gatefile"
5 failed, 3 passed, 83 deselected, 7 subtests passed
```

The failed tests were `test_retry_rule_holds`, `test_mutant_retry_rule` (both GATEFILE subtests) and `test_gatefile_missing_path_is_a_named_trigger`, plus the walk. The walk failed only at its final `assert_holds(retry_rule_holds)`, with four GATEFILE needles missing. Every walk step before that passed, including "old rule: same GATEFILE reused fails identically".

Green at: c0ece7e (60-08: the rebuild-once rule names a missing or empty `GATEFILE=` as a trigger. It re-runs the existing gate-input fence for a NEW `GATEFILE=`, writes the flags from the rebuilt `$COUNTS_JSON`, and never reuses an earlier attempt's or session's `GATEFILE=`. No second GATEFILE fence was added.)

---

### Gap-round red / green

| Fixture | Pre-fix result (at `2f84d2e`) | Verdict | Green at |
|---|---|---|---|
| `TestProseRangeFence::test_gsd_route_fresh_shell_includes_committed_change` | fail | V10 | 2a63cb5 |
| `TestProseRangeFence::test_incremental_route_fresh_shell_includes_committed_change` | fail | V10 | 2a63cb5 |
| `TestProseRangeFence::test_unsubstituted_variable_halts_instead_of_narrowing` | fail (both "quoted, left unsubstituted" subtests) | V10 | 2a63cb5 |
| `TestProseRangeFence::test_gsd_empty_phase_start_uses_head` | fail | V10 | 2a63cb5 |
| `TestProseRangeFence::test_literal_substitution_sentence_present` | fail | V10 | 2a63cb5 |
| `TestScopePhaseStartFence` (2 tests) | fail | V10 | 2a63cb5 |
| `TestRangeSourceLines::test_every_line_is_fully_flagged` | fail (3 subtests) | V10, V11 | 2a63cb5 |
| `TestProseRangeFence::test_fence_shape` | fail | V11 | 2a63cb5 |
| `TestProseRangeFence::test_hostile_external_diff_config_changes_nothing` | fail | V11 | 2a63cb5 |
| `TestProseRangeFence::test_diff_relative_from_subdirectory_changes_nothing` | fail | V11 | 2a63cb5 |
| `TestHazards::test_suppress_blank_empty_context_is_context` | fail (default and -U10 subtests) | V11 | b878870 |
| `TestRefusals::test_refuses_colored_diff` | fail | V11 | b878870 |
| `TestRefusals::test_refuses_non_diff_text` | fail (error / stat / prose subtests) | V11 | b878870 |
| `TestMutants::test_m20_` / `m21_` / `m22_` | fail (anchors absent) | V11 | b878870 |
| `TestFinalizeFreshShellWalk::test_retry_mints_new_gatefile_after_gate_input_failure` | fail | V12 | c0ece7e |
| `TestFinalizeFreshShellWalk::test_gatefile_missing_path_is_a_named_trigger` | fail | V12 | c0ece7e |
| `TestGapRoundFinalize::test_retry_rule_holds` | fail | V12 | c0ece7e |
| `TestGapRoundFinalize::test_mutant_retry_rule` | fail (both GATEFILE mutant subtests) | V12 | c0ece7e |

`test_hostile_repo_config_does_not_change_ranges` and `test_colored_diff_exits_two_with_reason_only` (60-06) and `test_stale_earlier_attempt_file_does_not_govern` (60-08) also went red at their plans' RED SHAs. They were outside the reverse-run `-k` filter below, and they are counted in the full-file run.

### Reverse run (gap round)

The current tests were run against the production code at `2f84d2e`, from HEAD `2093f88` (the 60-09 record commit).

- Worktree: `git worktree add --detach <scratchpad>/pre60gap 2f84d2e`. `git rev-parse --short HEAD` there printed `2f84d2e`. In that tree, `diff_ranges.py` has no suppressBlankEmpty or escape handling, the 30-collect-score.md GSD/pass-2+ rows end in `$PHASE_START` / `$LAST_REVIEWED_SHA`, and the 90-finalize.md rebuild rule re-mints only `BLOBFILE`.
- Copied in from HEAD: `test_diff_ranges.py`, `test_finalize_card.py`, `test_decision_continuity.py`.
- Afterwards: `git worktree remove --force <scratchpad>/pre60gap`, then `git worktree prune`. `git worktree list | grep -c pre60gap` printed `0`.

```
$ pytest -q -p no:cacheprovider -rf test_diff_ranges.py test_finalize_card.py -k "suppress_blank_empty or refuses_colored or refuses_non_diff or m20 or m21 or m22 or ProseRangeFence or ScopePhaseStart or RangeSourceLines or retry or gatefile"
FAILED test_diff_ranges.py::TestMutants::test_m20_empty_body_line_is_context
FAILED test_diff_ranges.py::TestMutants::test_m21_escape_refusal
FAILED test_diff_ranges.py::TestMutants::test_m22_not_a_diff_refusal
FAILED test_diff_ranges.py::TestProseRangeFence::test_diff_relative_from_subdirectory_changes_nothing
FAILED test_diff_ranges.py::TestProseRangeFence::test_fence_shape
FAILED test_diff_ranges.py::TestProseRangeFence::test_gsd_empty_phase_start_uses_head
FAILED test_diff_ranges.py::TestProseRangeFence::test_gsd_route_fresh_shell_includes_committed_change
FAILED test_diff_ranges.py::TestProseRangeFence::test_hostile_external_diff_config_changes_nothing
FAILED test_diff_ranges.py::TestProseRangeFence::test_incremental_route_fresh_shell_includes_committed_change
FAILED test_diff_ranges.py::TestProseRangeFence::test_literal_substitution_sentence_present
FAILED test_diff_ranges.py::TestRefusals::test_refuses_colored_diff
FAILED test_diff_ranges.py::TestScopePhaseStartFence::test_no_history_prints_empty_value
FAILED test_diff_ranges.py::TestScopePhaseStartFence::test_prints_first_commit_touching_phase_dir
FAILED test_finalize_card.py::TestFinalizeFreshShellWalk::test_gatefile_missing_path_is_a_named_trigger
FAILED test_finalize_card.py::TestFinalizeFreshShellWalk::test_retry_mints_new_gatefile_after_gate_input_failure
FAILED test_finalize_card.py::TestGapRoundFinalize::test_retry_rule_holds
SUBFAILED(context='-U10') test_diff_ranges.py::TestHazards::test_suppress_blank_empty_context_is_context
SUBFAILED(context='default') test_diff_ranges.py::TestHazards::test_suppress_blank_empty_context_is_context
SUBFAILED(file='00-scope.md', line='Range source for 30-collect-score: `git diff $PHASE_START` (one diff, commit vs ') test_diff_ranges.py::TestRangeSourceLines::test_every_line_is_fully_flagged
SUBFAILED(file='00-scope.md', line='Range source for 30-collect-score: `git diff HEAD` only (working-tree line numbe') test_diff_ranges.py::TestRangeSourceLines::test_every_line_is_fully_flagged
SUBFAILED(file='05-state.md', line='Range source for 30-collect-score: `git diff $LAST_REVIEWED_SHA` (one diff, last') test_diff_ranges.py::TestRangeSourceLines::test_every_line_is_fully_flagged
SUBFAILED(input='error') test_diff_ranges.py::TestRefusals::test_refuses_non_diff_text
SUBFAILED(input='prose') test_diff_ranges.py::TestRefusals::test_refuses_non_diff_text
SUBFAILED(input='stat') test_diff_ranges.py::TestRefusals::test_refuses_non_diff_text
SUBFAILED(row='$LAST_REVIEWED_SHA', form='quoted, left unsubstituted') test_diff_ranges.py::TestProseRangeFence::test_unsubstituted_variable_halts_instead_of_narrowing
SUBFAILED(row='$PHASE_START', form='quoted, left unsubstituted') test_diff_ranges.py::TestProseRangeFence::test_unsubstituted_variable_halts_instead_of_narrowing
SUBFAILED[mutant: earlier attempt's GATEFILE may be reused] test_finalize_card.py::TestGapRoundFinalize::test_mutant_retry_rule
SUBFAILED[mutant: rebuild does not re-mint GATEFILE] test_finalize_card.py::TestGapRoundFinalize::test_mutant_retry_rule
28 failed, 14 passed, 159 deselected, 13 subtests passed in 2.33s

$ pytest -p no:cacheprovider -v test_diff_ranges.py test_finalize_card.py -k "<the four controls>"
test_diff_ranges.py::TestRefusals::test_binary_only_and_mode_only_diffs_are_empty PASSED
test_diff_ranges.py::TestProseRangeFence::test_empty_diff_prints_empty_object PASSED
test_finalize_card.py::TestFinalizeFreshShellWalk::test_malformed_gatefile_shows_only_stop_sentence PASSED
test_finalize_card.py::TestFinalizeFreshShellWalk::test_retry_mints_new_blobfile_after_missing_path PASSED
4 passed, 185 deselected, 3 subtests passed in 0.41s

$ pytest -q -p no:cacheprovider test_diff_ranges.py test_finalize_card.py test_decision_continuity.py
32 failed, 327 passed, 367 subtests passed in 12.75s
```

Every gap-round red fixture fails at `2f84d2e` (each V10, V11 and V12 fixture is in the list above), and all four controls pass there. Pre-fix, 60-06 (`test_diff_ranges.py` builder tests and M20-M22), 60-07 (`test_diff_ranges.py` prose and range-source tests) and 60-08 (`test_finalize_card.py` GATEFILE walk and locks) each have failing tests. The three-file run fails 32, against the 28 under the `-k` filter. A second worktree at `2f84d2e` (same recipe, removed and pruned afterwards; `git worktree list | grep -c pre60gap` printed `0`) itemised the 32 with `-rf`. They are the 28 above plus four more: `TestCli::test_colored_diff_exits_two_with_reason_only`, `TestHazards::test_hostile_repo_config_does_not_change_ranges` and `TestRefusals::test_reasons_are_fixed_text` (60-06), and `TestFinalizeFreshShellWalk::test_stale_earlier_attempt_file_does_not_govern` (60-08). Each of the four is listed as red in its plan's SUMMARY. Nothing in `test_decision_continuity.py` fails pre-fix, and no failure comes from outside the gap round's own additions.

### Suite at gap-round close

All runs are from `plugins/vibe-check/scripts` in the real checkout at HEAD `2093f88`.

```
$ pytest -q -p no:cacheprovider
3786 passed, 4965 subtests passed in 174.70s (0:02:54)

$ pytest -q -p no:cacheprovider test_replay.py
64 passed, 10 subtests passed in 10.32s

$ git diff --stat 2f84d2e HEAD -- plugins/vibe-check/scripts/replay.py plugins/vibe-check/scripts/test_replay.py plugins/vibe-check/scripts/score.py plugins/vibe-check/scripts/finalize_gate.py plugins/vibe-check/scripts/carry_state.py
(empty)
```

- 0 failed.
- **Replay deltas: none.** The gap round touched only `diff_ranges.py`, the review prose (`00-scope.md`, `05-state.md`, `30-collect-score.md`), `90-finalize.md` and three test files. `replay.py`, `score.py`, `finalize_gate.py` and `carry_state.py` are byte-identical to `2f84d2e`.

## Second gap round (60-VERIFICATION re-verification, 2026-10-29)

The re-verification (60-VERIFICATION.md, committed at `f2b58d1`, "docs(60): re-verification gaps_found — 3 original gaps closed; CR-01, WR-02 blocking") confirmed that V10-V12 are closed and found two new blocking gaps on the fixed code. Both were first reported by the gap-round code review (60-REVIEW.md CR-01 and WR-02, commit `cfa473a`) and then independently reproduced by the re-verification. `f2b58d1` is the pre-round production base: the planning commits after it (`43ae166`, `65bb39d`) touch no file under `plugins/` (`git diff --stat f2b58d1 65bb39d -- plugins/` is empty), every gap below was reproduced there, and the reverse run below uses it. The same rule applies: reproduce first, and add work only for the four qualifying classes. Both qualify. CR-01 is a working command-execution path in a tool that reads untrusted repository content (a state file committed inside the reviewed repo): the safety of a required workflow is broken. WR-02 is a broken required workflow: "Finalize costs one card" fails, because a card answer that clears every obligation still ends in "Finalize stays blocked". CR-01 was fixed by two red -> green pairs (60-10 helper, 60-11 prose) and WR-02 by one (60-12). The pytest output below is copied from those plans' SUMMARYs, not retyped.

## V13 — HEAD-SHA-INJECTION: a crafted `head_sha` in the state file runs a command on pass 2+ (EVID-03)

**Verdict: REPRODUCED at `f2b58d1` -> fixed by 60-10 (helper) + 60-11 (prose).**

**Failure as the owner would see it.** No error is shown. On pass 2 and later, 05-state.md step 2 read `head_sha` from the last pass of the state file, and 30-collect-score.md told the agent to substitute it into the double-quoted `"<last-reviewed-sha>"` placeholder of the range-source row. The state file can be committed inside the reviewed repo (the GSD key is `<phase-dir-name>.json`), so its content is untrusted. With `head_sha` set to `$(touch "$T/pwned")HEAD`, the row runs the payload: the marker file is created, the fence exits 0 and prints valid-looking ranges. Double quotes stop word-splitting, not `$(...)`. Anyone who can get a state file into a repo the owner reviews could run a command on the owner's machine.

**Fixture.** `TestLastHeadSha` in `test_carry_state.py` (60-10: accept/refuse table incl. the exact payload, empty stdout on refusal, mutation test, sealed reason). In `test_diff_ranges.py` (60-11): `TestStateHeadShaFence` (the 05-state.md step-2 bind fence, run in a fresh shell with on-disk markers), `TestScopePhaseStartFence::test_non_sha_phase_start_halts_before_printing` and `test_mutant_without_the_check_prints_the_payload` (the 00-scope.md `PHASE_START` check), `TestSubstitutedValueProse` (the printed-literal rule and its mutants), `TestProseRangeFence::test_incremental_route_uses_the_printed_last_reviewed_sha`, and `TestProseRangeFence::test_injection_payload_in_the_row_executes_so_the_bind_fence_is_the_control` — the written reproduction: the payload substituted into the row still creates the marker with rc 0, on the old prose and the new, which is why the bind fence is the control.

**Command and output at the RED SHAs:**

```
$ pytest -q -p no:cacheprovider test_carry_state.py -k TestLastHeadSha          # at 558bde3 (60-10 red)
24 failed, 2 passed, 226 deselected

$ pytest -q -p no:cacheprovider --tb=no test_diff_ranges.py -k "StateHeadSha or SubstitutedValue or ScopePhaseStart or printed_last_reviewed or injection_payload"   # at dfca59c (60-11 red)
16 failed, 5 passed, 98 deselected, 1 subtests passed

$ pytest -q -p no:cacheprovider test_diff_ranges.py -k injection_payload_in_the_row   # at dfca59c
1 passed
```

At `558bde3` all eight `TestLastHeadSha` tests are red; the 2 "passed" are the parent entries of the two subtest-table tests, every subtest under which failed. At `dfca59c` the failures are all four `TestStateHeadShaFence` tests, all six `TestSubstitutedValueProse` tests, `test_non_sha_phase_start_halts_before_printing`, `test_mutant_without_the_check_prints_the_payload` and `test_incremental_route_uses_the_printed_last_reviewed_sha`. The last command is the CR-01 reproduction itself: the marker file is created and the row exits 0.

Green at: ae560fe (60-10: `carry_state.py last-head-sha` prints the last pass's `head_sha` as one bare line only when it is exactly 40 or 64 lowercase hex characters; anything else, including the payload, is refused with a fixed reason on stderr, nothing on stdout, exit 2) + 5d81170 (60-11: 05-state.md step 2 binds `$LAST_REVIEWED_SHA` through that subcommand and halts with one sentence on refusal; 00-scope.md refuses a non-empty `PHASE_START` that is not a commit id before printing it; 30-collect-score.md says only the printed literal is ever substituted, and that quotes are not the protection). With the payload, the bind fence exits 1, prints no `LAST_REVIEWED_SHA=` line, and no marker is created.

---

## V14 — STALE-GATEFILE-RERUN: Finalize's post-answer gate re-run decides on the pre-answer flags (FINL-02)

**Verdict: REPRODUCED at `f2b58d1` -> fixed by 60-12.**

**Failure as the owner would see it.** The owner answers the Finalize card and dismisses every open obligation; `record-decisions` lands. Step 3 then said "RE-RUN the counts step and the gate ONCE (the same `BLOBFILE=` literal this attempt printed)". The gate reads only `GATEFILE=`, which still holds the flags written before the answers. On the six-row fixture the counts go from (5, 1, 0) to (0, 0, 0), but the gate on the stale GATEFILE still returns `outstanding-to-phase-5`. The owner sees "Finalize stays blocked" above an empty list and must run `--finalize` again: "Finalize costs one card" is broken.

**Fixture.** `TestFinalizeFreshShellWalk::test_post_decision_rerun_decides_on_a_fresh_gatefile` (a fresh-shell walk over the real fences: the stale GATEFILE returns `outstanding-to-phase-5`; a re-minted GATEFILE written from the recounted counts returns `write`; the step-3 rule must hold), `TestGapRoundFinalize::test_step3_rerun_rule_holds` and `test_mutant_step3_rerun_rule` (one mutant per needle, scoped to the step-3 line), all in `test_finalize_card.py`.

**Command and output at the RED SHA `2648f2d`:**

```
$ pytest -q -p no:cacheprovider test_finalize_card.py -k "step3 or post_decision or card_route or test_retry_rule_holds"
8 failed, 4 passed, 87 deselected, 2 subtests passed
```

The failures are `test_step3_rerun_rule_holds`, all six `test_mutant_step3_rerun_rule` subtests and `test_post_decision_rerun_decides_on_a_fresh_gatefile`. The walk failed only at its final rule check; both of its walk subtests passed, which is the reproduction (stale -> `outstanding-to-phase-5`, fresh -> `write`).

Green at: c112ca6 (60-12: step 3 re-counts on the same `BLOBFILE=` literal, runs the gate-input fence again for a NEW `GATEFILE=`, writes the seven-key `flags` object from the RE-COUNTED `$COUNTS_JSON` to it, and gates on that literal, never on the `GATEFILE=` the attempt's first gate run read. One line changed; the rebuild-once paragraph is byte-identical to `c0ece7e`.)

---

### Second-round red / green

| Fixture | Pre-fix result (at `f2b58d1`) | Verdict | Green at |
|---|---|---|---|
| `TestLastHeadSha` (8 tests, `test_carry_state.py`) | fail (6 tests; every subtest of the 2 table tests) | V13 | ae560fe |
| `TestStateHeadShaFence` (4 tests) | fail | V13 | 5d81170 |
| `TestScopePhaseStartFence::test_non_sha_phase_start_halts_before_printing` | fail | V13 | 5d81170 |
| `TestScopePhaseStartFence::test_mutant_without_the_check_prints_the_payload` | fail | V13 | 5d81170 |
| `TestScopePhaseStartFence::test_sixty_four_hex_is_accepted` | pass (no check existed, so 64-hex was never refused) | V13 | 5d81170 |
| `TestSubstitutedValueProse` (6 tests) | fail (`test_head_sha_mutants_trip` at its four subtests) | V13 | 5d81170 |
| `TestProseRangeFence::test_incremental_route_uses_the_printed_last_reviewed_sha` | fail | V13 | 5d81170 |
| `TestProseRangeFence::test_injection_payload_in_the_row_executes_so_the_bind_fence_is_the_control` | pass (the reproduction: the payload runs) | V13 | control |
| `TestGapRoundFinalize::test_step3_rerun_rule_holds` | fail | V14 | c112ca6 |
| `TestGapRoundFinalize::test_mutant_step3_rerun_rule` | fail (all six subtests) | V14 | c112ca6 |
| `TestFinalizeFreshShellWalk::test_post_decision_rerun_decides_on_a_fresh_gatefile` | fail (at the final rule check) | V14 | c112ca6 |

`test_step3_keeps_answer_files_anchor` (60-12) is a guard that the step-3 rewrite keeps the answer-files anchor; it passes before and after.

### Reverse run (second round)

The current tests were run against the production code at `f2b58d1`, from HEAD `84b5e27` (the 60-13 record commit).

- Worktree: `git worktree add --detach <scratchpad>/pre60round2 f2b58d1`. In that tree, `carry_state.py` has no `last-head-sha` subcommand, 05-state.md step 2 has no bind fence, 00-scope.md has no `PHASE_START` check, and 90-finalize.md step 3 re-runs the gate on this attempt's GATEFILE.
- Copied in from HEAD: `test_carry_state.py`, `test_diff_ranges.py`, `test_finalize_card.py`, `test_decision_continuity.py`.
- Afterwards: `git worktree remove --force <scratchpad>/pre60round2`, then `git worktree prune`. `git worktree list | grep -c pre60round2` printed `0`. (The worktree was made twice with the same recipe, the second time to list the passing tests with `-rA`; both were removed and pruned, and the count was `0` after each.)

```
$ pytest -q -p no:cacheprovider -rf --tb=no test_carry_state.py test_diff_ranges.py test_finalize_card.py -k "LastHeadSha or StateHeadSha or SubstitutedValue or ScopePhaseStart or printed_last_reviewed or injection_payload or step3 or post_decision"
FAILED test_carry_state.py::TestLastHeadSha::test_does_not_mutate_state - Att...
FAILED test_carry_state.py::TestLastHeadSha::test_in_process_returns_none_on_refusal
FAILED test_carry_state.py::TestLastHeadSha::test_malformed_state_refused_before_head_sha
FAILED test_carry_state.py::TestLastHeadSha::test_mutant_validator_lets_the_payload_through
SUBFAILED(value='50f9932e2a6efba17a6db77435bb5bf131039147') test_carry_state.py::TestLastHeadSha::test_prints_bare_sha_for_40_and_64_hex
SUBFAILED(value='0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef') test_carry_state.py::TestLastHeadSha::test_prints_bare_sha_for_40_and_64_hex
FAILED test_carry_state.py::TestLastHeadSha::test_reason_is_sealed - Assertio...
SUBFAILED[cr01-injection] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[backtick] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[symbolic-HEAD] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[option-shaped] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[dash] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[empty] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[null] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[missing] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[hex39] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[hex41] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[hex63] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[hex65] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[uppercase40] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[hex40-trailing-newline] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[int] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
SUBFAILED[list] test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
FAILED test_carry_state.py::TestLastHeadSha::test_usage_and_subcommand_registered
FAILED test_diff_ranges.py::TestProseRangeFence::test_incremental_route_uses_the_printed_last_reviewed_sha
FAILED test_diff_ranges.py::TestScopePhaseStartFence::test_mutant_without_the_check_prints_the_payload
FAILED test_diff_ranges.py::TestScopePhaseStartFence::test_non_sha_phase_start_halts_before_printing
FAILED test_diff_ranges.py::TestStateHeadShaFence::test_injection_payload_halts_without_executing
FAILED test_diff_ranges.py::TestStateHeadShaFence::test_missing_state_file_halts
FAILED test_diff_ranges.py::TestStateHeadShaFence::test_other_non_sha_values_halt
FAILED test_diff_ranges.py::TestStateHeadShaFence::test_prints_the_validated_sha
FAILED test_diff_ranges.py::TestSubstitutedValueProse::test_head_sha_binding_holds
SUBFAILED(removed='ONLY the literal printed after `LAST_REVIEWED_SHA=`') test_diff_ranges.py::TestSubstitutedValueProse::test_head_sha_mutants_trip
SUBFAILED(removed='never a value copied from the state JSON by hand') test_diff_ranges.py::TestSubstitutedValueProse::test_head_sha_mutants_trip
SUBFAILED(removed='refused before it can reach a command') test_diff_ranges.py::TestSubstitutedValueProse::test_head_sha_mutants_trip
SUBFAILED(removed='printf \'LAST_REVIEWED_SHA=%s\\n\' "$LAST_REVIEWED_SHA"') test_diff_ranges.py::TestSubstitutedValueProse::test_head_sha_mutants_trip
FAILED test_diff_ranges.py::TestSubstitutedValueProse::test_phase_start_check_holds
FAILED test_diff_ranges.py::TestSubstitutedValueProse::test_phase_start_check_mutant_trips
FAILED test_diff_ranges.py::TestSubstitutedValueProse::test_substituted_value_mutants_trip
FAILED test_diff_ranges.py::TestSubstitutedValueProse::test_substituted_value_rule_holds
SUBFAILED[mutant: step 3 drops RE-RUN the counts step ONCE (the same `BLOBFILE=` literal this attempt printed)] test_finalize_card.py::TestGapRoundFinalize::test_mutant_step3_rerun_rule
SUBFAILED[mutant: step 3 drops run the gate-input fence again so it prints a NEW `GATEFILE=`] test_finalize_card.py::TestGapRoundFinalize::test_mutant_step3_rerun_rule
SUBFAILED[mutant: step 3 drops write the seven-key `flags` object from the RE-COUNTED `$COUNTS_JSON` to that new path] test_finalize_card.py::TestGapRoundFinalize::test_mutant_step3_rerun_rule
SUBFAILED[mutant: step 3 drops run the gate once on that literal] test_finalize_card.py::TestGapRoundFinalize::test_mutant_step3_rerun_rule
SUBFAILED[mutant: step 3 drops never on the `GATEFILE=` this attempt's first gate run read] test_finalize_card.py::TestGapRoundFinalize::test_mutant_step3_rerun_rule
SUBFAILED[mutant: step 3 re-runs the gate on the old GATEFILE again] test_finalize_card.py::TestGapRoundFinalize::test_mutant_step3_rerun_rule
FAILED test_finalize_card.py::TestGapRoundFinalize::test_step3_rerun_rule_holds
FAILED test_finalize_card.py::TestFinalizeFreshShellWalk::test_post_decision_rerun_decides_on_a_fresh_gatefile
48 failed, 9 passed, 413 deselected, 3 subtests passed in 1.94s

$ pytest -p no:cacheprovider --tb=no -rA <same files and -k>   # the 9 passed
PASSED test_carry_state.py::TestLastHeadSha::test_prints_bare_sha_for_40_and_64_hex
PASSED test_carry_state.py::TestLastHeadSha::test_refuses_every_non_sha_value
PASSED test_diff_ranges.py::TestProseRangeFence::test_injection_payload_in_the_row_executes_so_the_bind_fence_is_the_control
PASSED test_diff_ranges.py::TestScopePhaseStartFence::test_no_history_prints_empty_value
PASSED test_diff_ranges.py::TestScopePhaseStartFence::test_prints_first_commit_touching_phase_dir
PASSED test_diff_ranges.py::TestScopePhaseStartFence::test_sixty_four_hex_is_accepted
PASSED test_diff_ranges.py::TestSubstitutedValueProse::test_head_sha_mutants_trip
PASSED test_finalize_card.py::TestGapRoundFinalize::test_mutant_step3_rerun_rule
PASSED test_finalize_card.py::TestGapRoundFinalize::test_step3_keeps_answer_files_anchor

$ pytest -q -p no:cacheprovider --tb=no test_carry_state.py test_diff_ranges.py test_finalize_card.py -k "<the five controls>"
5 passed, 437 deselected in 0.62s
```

Every second-round red fixture fails at `f2b58d1`: 60-10 (`test_carry_state.py`, `TestLastHeadSha`), 60-11 (`test_diff_ranges.py`, the bind fence, the `PHASE_START` check and the printed-literal prose) and 60-12 (`test_finalize_card.py`, the step-3 lock and the stale-vs-fresh walk) each have failing tests above. Of the 9 "passed", four are parent entries of subtest tables whose subtests failed (`test_prints_bare_sha_for_40_and_64_hex`, `test_refuses_every_non_sha_value`, `test_head_sha_mutants_trip`, `test_mutant_step3_rerun_rule`; each appears as SUBFAILED above), `test_sixty_four_hex_is_accepted` passes because the old 00-scope.md had no check to refuse it, and four are controls. The five controls all pass at `f2b58d1`: `test_injection_payload_in_the_row_executes_so_the_bind_fence_is_the_control` (the written reproduction, green on the old prose too), `test_step3_keeps_answer_files_anchor`, `test_prints_first_commit_touching_phase_dir`, `test_no_history_prints_empty_value` and `test_card_route_records_then_writes` (outside the `-k` filter above; run by name in the third command).

### Suite at second-round close

All runs are from `plugins/vibe-check/scripts` in the real checkout at HEAD `84b5e27`.

```
$ pytest -q -p no:cacheprovider
3813 passed, 5014 subtests passed in 180.43s (0:03:00)

$ pytest -q -p no:cacheprovider test_replay.py
64 passed, 10 subtests passed in 10.38s

$ git diff --stat f2b58d1 HEAD -- plugins/vibe-check/scripts/replay.py plugins/vibe-check/scripts/test_replay.py plugins/vibe-check/scripts/score.py plugins/vibe-check/scripts/finalize_gate.py
(empty)

$ git diff --stat f2b58d1 HEAD -- plugins/vibe-check/scripts/carry_state.py
 plugins/vibe-check/scripts/carry_state.py | 44 +++++++++++++++++++++++++++++--
 1 file changed, 42 insertions(+), 2 deletions(-)
```

- 0 failed.
- **Replay deltas: none.** `replay.py`, `test_replay.py`, `score.py` and `finalize_gate.py` are byte-identical to `f2b58d1`.
- **`carry_state.py` did change, and this is the one helper this round touched.** 60-10 added one read-only subcommand, `last-head-sha` (with `_commit_sha`, `last_head_sha` and `REASON_HEAD_SHA` in the sealed reason set); no existing subcommand changed, and the full `test_carry_state.py` run is green. The replay check does not cover `carry_state.py` and never did, so the empty replay diff-stat says nothing about it; it is listed here rather than left out. The other files this round touched are review prose (`00-scope.md`, `05-state.md`, `30-collect-score.md`), `90-finalize.md` and four test files.

## Residuals

None of these is fixed in Phase 60, except R14, which the second gap round closed (V13). Under D-10 the phase runs one bounded cycle, so no second review round is opened. None of them falls in the four qualifying classes (a reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, a broken required workflow). Each is recorded with its rationale and the check that would reopen it.

- **(R1) `finalize_gate.py` still prints a Python traceback on empty or malformed stdin.** Re-checked at HEAD `ec0c9d8`: `printf '' | python3 finalize_gate.py` exits 1, and stderr starts `Traceback (most recent call last):` and ends `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`. The helper itself is unchanged. 60-03's gate fence sends its stderr to `<GATEFILE>.err`, so the owner sees only the fence's one sentence, and `test_malformed_gatefile_shows_only_stop_sentence` locks that (the subtest that removes the redirect fails). This is helper-side only and never reaches the owner. Carried: if `finalize_gate.py` is ever called outside that fence, give it a fixed one-line refusal like `diff_ranges.py`'s.
- **(R2) Coordinate-space shapes that did not reproduce: none.** All three probes reproduced at `ce9f8b8` and all three were fixed by 60-04, so nothing was dropped. The three are PR-SERIES (`series ranges [[10, 10], [1, 5]]`, the finding at head line 15 is not in the diff), MIXED-COORD (`[[35, 35], [1, 10]]`, the decision at line 50 stays `current`, a silent keep) and DEFAULT-STAGED (Probe A: `[[1, 10], [58, 58], [48, 48]]`, a wrong reopen from index line 48; Probe B: a finding at 48 is outside the `git diff HEAD` ranges). DEFAULT-STAGED sits alongside the other two: the default route now takes ranges from `git diff HEAD` alone, under the working-tree coordinate contract. Probe B is coordinate disagreement, not a lost changed line (V6).
- **(R3) The agents' diff commands are unchanged.** Reviewers still read `gh pr diff <ref> --patch` on the PR route, and the default, GSD and incremental routes still hand reviewers the staged and unstaged views. Only the range source changed. Changing what reviewers read is out of scope for 999.24, whose subject is the ranges. A finding's line number still comes from the agent's reading, and `score.py` checks it against the exact ranges. If an agent numbered a finding from a commit's own lines in the `--patch` series, the finding could lose the `+20 in_diff` term, and near a threshold its band too. That is a question about how reviewers number lines, not about ranges. It was not reproduced in Phase 60: reproduce first, with an agent-produced line number, before any work.
- **(R4) Stored `snapshot.nearby_at` stamps written from the old, wider ranges are not migrated.** A stamp set by a context line fails toward asking, one extra re-ask on the next run and never a silent keep. Per the D-04 audit it is left as it is.
- **(R5) The installed plugin cache runs the OLD prose until it is resynced and the process relaunched.** Agents and phase prose dispatch from `~/.claude/plugins/cache`, not from the repo (project memory: install chronically stale; same-version cache staleness). Phase 61 must confirm the installed vibe-check matches the repo (or run with `--plugin-dir`) before any manual or live check of the new range fence or Finalize fences. Otherwise it will observe the pre-fix behaviour and misread it as a regression.
- **(R6) The live `gh pr diff` fetch was not exercised (D-05).** The PR route is proven on the checked-in real capture `fixtures/pr-cumulative.diff` (PR #5, provenance above) and on a series refused with `REASON_MBOX`. A live fetch, plus gh's behaviour on renames, binary files and very large PRs, is unverified. Phase 61's release record names this gap, and EVID-03 is marked Complete with this known limit.
- **(R7) Untracked files are absent from every `git diff` form.** This behaviour is unchanged: a finding in a new untracked file has no ranges, so `in_diff` is false and no decision there is ever stamped `nearby`. It predates Phase 60 and is the same on every route. Reproduce first before any work (for example an `--intent-to-add` range source).
- **(R8) C-quoted paths contribute no ranges.** `diff_ranges.py` skips `+++ "b/…"` names, which are non-ASCII or contain control characters (research A5, 60-02 mutant M16). Finding paths must match `PATH_RE` `^[A-Za-z0-9._/-]+$`, so such a file can never carry a finding. This is not a silent keep today. Reopen only if `PATH_RE` is widened.
- **(R9) The RESEARCH.md reference range algorithm has a `-U0` pure-deletion off-by-one.** It starts the walk cursor at `T`, not `T+1`, for a `+T,0` header. `diff_ranges.py` fixed it (60-02 decision; mutant M7, `test_delete_one_line` -U0 subtest). The error remains only in the planning document and is recorded so that nobody copies the snippet.
- **(R10) `--all` has no diff (V7).** It is an unsupported fixture, recorded by `TestRouteAll`. `--all` never gates on `in_diff` and never stamps `nearby_at`, because 05-state-all.md (ii) forces pass 1 with an empty carry-forward. Reopen only if `--all` starts to carry state forward.
- **(R11) `replay.hunk_ranges` is intentionally context-inclusive and unchanged.** It reproduces the ranges archived B3 runs were scored with, is pinned by `TestReplayPin`, and Phase 61 GATE-02 depends on it. Do not change it.

R12-R17 were added at the gap round (60-09). They cover the 60-REVIEW.md and 60-VERIFICATION.md items that the first close left out of this list. None is fixed in the gap round. R14 was later reproduced as command execution (gap-round review CR-01) and closed in the second gap round; the others stay out of the four qualifying classes. The parenthetical on each gives its number in the gap-round review.

- **(R12) WR-05 (gap-round review: WR-03): Finalize temp files are never removed.** `BLOBFILE`, `GATEFILE` and `GATEFILE.err` stay under `$TMPDIR` after Finalize, and a retry leaves a second set. This is resource hygiene, not a functional break: each attempt mints fresh paths, and a stale file never governs a later attempt (`test_stale_earlier_attempt_file_does_not_govern`). Reopen if a run is shown to read or fill a stale temp file, or if `$TMPDIR` growth is ever observed to matter.
- **(R13) IN-01 (gap-round review: IN-04): the commit-series (mbox) refusal recognises only SHA-1 `From <40-hex>` separators.** A SHA-256 repository's `--patch` series would not be refused by that check. SHA-256 repositories are not supported anywhere in the plugin, and the PR range source is `gh pr diff` (cumulative), not `--patch`. Reopen if SHA-256 repos come into scope.
- **(R14) IN-02 (first review) / CR-01 (gap-round review): `head_sha` from the state file reached a command unvalidated.** CLOSED at 5d81170: bound through `carry_state.py last-head-sha` (V13). The helper half landed at ae560fe (60-10) and the prose that binds through it at 5d81170 (60-11). The first close recorded this as not reproduced; the gap-round review then reproduced it as command execution (`$(...)` inside the double-quoted placeholder), so it was fixed in the second gap round.
- **(R15) IN-03 (gap-round review: IN-05): the counts fence leaves its stderr uncaptured,** unlike the gate fence, which sends it to `<GATEFILE>.err`. When the counts helper refuses, the owner sees the helper's own fixed one-line refusal text and then the fence's stop sentence. No traceback is involved (`carry_state.py` refuses with fixed text). This is unchanged and not a functional break. Reopen if the counts helper is ever shown to emit a traceback to the owner.
- **(R16) SA-01 (gap-round review: SA-01): the Write tool on a freshly minted, unread `mktemp` path.** It is not known whether the harness Write tool accepts a first write to the `BLOBFILE=` / `GATEFILE=` path that `mktemp` just created and the agent never Read. The same pattern is already used for ROWSFILE, SUGGESTFILE and REFSFILE. It cannot be exercised from pytest. It awaits the owner's live check (60-VERIFICATION human item 1). If the write is refused, both the attempt and its one retry fail at the same step.
- **(R17) SA-02 (gap-round review: SA-02): the PR range source fails closed on PRs above GitHub's diff limits** (about 300+ files or 20k+ lines). `gh pr diff` errors, and the fence halts through `pipefail`. The reviewer judged this intended behaviour, not a defect. It awaits the owner's ruling on accepted limit vs fallback (60-VERIFICATION human item 2).

R18-R21 were added at the second gap round (60-13). They are the gap-round review's (60-REVIEW.md, `cfa473a`) new items other than CR-01 and WR-02, under that review's numbering. None is in the four qualifying classes as reproduced, and none is fixed in the second gap round.

- **(R18) WR-01: `diff.submodule` is not neutralised.** With `diff.submodule=log`, a submodule pointer change prints as `Submodule sub a..b:` with no `diff --` header: a submodule-only change is refused as not-a-diff (the pass halts), and a mixed change silently drops the submodule's range; `diff.submodule=diff` prints the inner diff under superproject-looking keys. Carried: it was not reproduced as the loss of a qualifying finding on a real review, and no submodule is in scope for this plugin's own repos. Reopen with a reproduction on a repo that has a submodule (the review's fix is `--submodule=short` in the fixed flag set plus a hostile-config case with a real submodule change).
- **(R19) IN-01: the "`{}` is printed only for a genuinely empty diff" sentence in 30-collect-score.md is imprecise.** Binary-only, mode-only, deletion-only and C-quoted-path-only diffs also give `{}` with exit 0, by the helper's own contract and test. This is wording, not a functional break: no finding can sit on those lines (R8). Reopen if an agent is seen treating such a `{}` as an anomaly or reporting the diff as empty.
- **(R20) IN-02: the escape-refusal tests cover only fully coloured diffs.** In a fully coloured diff every header starts with ESC, so the not-a-diff rule refuses it anyway, and M21 trips only because the expected reason changes. The case the escape rule exists for, a partly coloured diff with plain headers (for example `color.diff.meta=normal`), has no test. The real module refuses it today (the review reproduced that M21's mutant returns `{}` there while the real module refuses), so the lock is weaker than it looks, not the behaviour. Reopen to add the partly coloured case and point M21 at it if `diff_ranges.py`'s escape rule is touched again.
- **(R21) IN-03: two checks assert less than they claim.** `literal_sha_rule_holds` accepts "substitute" anywhere in the range bullet, and the "old rule: same GATEFILE reused fails identically" subtest in the GATEFILE retry walk reads no prose. These are documentation-strength checks. This round superseded part of the first: `substituted_value_rule_holds` (60-11) checks each row for its printed literal (`printed after `LAST_REVIEWED_SHA=`` / `printed after `PHASE_START=``) with a mutant per needle, and `step3_rerun_rule_holds` (60-12) locks the step-3 GATEFILE rule with per-needle mutants. What remains: `literal_sha_rule_holds` itself still checks "substitute" bullet-wide, and the "old rule" subtest still guards no rule (the retry rule is guarded by the RETRY_NEEDLES lock). Reopen if either check is relied on as the only guard of a rule.

Silent keeps still open at close: none. MIXED-COORD was the one reproduced silent keep of the first cycle, and its probe passes at fb8b32b. The net-deletion boundary keep (V3) passes at 53fb637. The gap round's silent keep, GSD-SHELL-VAR (V10, the committed change dropped from the GSD/pass-2+ ranges in a fresh shell), is closed at 2a63cb5. CONFIG-ALTERED-DIFF (V11) is closed at b878870 + 2a63cb5, and GATEFILE-RETRY (V12) at c0ece7e. The second gap round's CR-01 (HEAD-SHA-INJECTION, V13) is closed at ae560fe + 5d81170, and WR-02 (STALE-GATEFILE-RERUN, V14) at c112ca6. EVID-03 and FINL-02 await re-verification after the second gap round, and this file makes no claim about their status. The known limits named here are R6 (the live PR fetch, which Phase 61 carries into the release record), the carried review items R18-R21, and the two owner rulings R16 and R17. No "reliability" claim beyond these tests is made.
