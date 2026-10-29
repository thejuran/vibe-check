# Phase 60 — Reproduction verdicts

- **Phase:** 60 — Exact change evidence and reliable Finalize
- **Date:** 2026-10-29
- **HEAD when recorded:** `ce9f8b8` (branch `feat/v2.14-phase-60`; the commit that added `REPRO_60` and completed the red fixtures, before any phase-60 production edit). The fixtures were added in `43d1905` (Task 1) and `2121c57` (Task 2); `ce9f8b8` is the RED SHA for the reverse run.
- **Scope of evidence:** no live or paid run; no network; the live `gh pr diff` fetch was not exercised (D-05). Every verdict below is a local pytest run. Range evidence comes from real `git diff` / `git format-patch` text in throwaway repos built with `gitfixture` (null global and system git config), fed through `header_rule_ranges` — an executable twin of the current `30-collect-score.md` "changed-line ranges" bullet — and then through the real `score.run -> append_pass -> carry_state -> finalize_gate` chain (`run_pass`, `pass1`, `e2e_gate`). Finalize evidence runs the real `90-finalize.md` fences in fresh `bash -s` shells with only PATH, VC_ROOT, TMPDIR and STATE_FILE (`fixtures/iplayarr45-six-row-state.json`). The PR series shape is reproduced with `git format-patch --stdout`, the same mbox commit-series shape `gh pr diff --patch` emits; no real PR was fetched.
- **Rule applied:** reproduce first; work is added only for the four qualifying classes (reproduced mandatory-gate failure, data loss, silent loss of a qualifying finding, broken required workflow). A shape that reproduced is a failing fixture committed at `ce9f8b8` and mapped to the plan that fixes it; a shape that did not reproduce would be recorded and dropped (none of the three coordinate probes fell into that arm). The `--all` route has no diff and is recorded as an unsupported fixture.

In-suite record: `test_decision_continuity.REPRO_60` (nine rows), locked by `TestRepro60Record` (exact id set, exact row keys, the three coordinate dispositions limited to `reproduced; fixed by 60-04` / `did not reproduce; dropped`, and every named fixture resolved by a `def` / `class` in `test_decision_continuity.py` or `test_finalize_card.py`; `TestRouteAll` is the one allowed forward reference, held in `_REPRO_60_PENDING_FIXTURES`, which 60-04 must empty).

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

Green at: <pending — 60-02 (builder) and 60-04 (prose routes ranges through it)>

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

Green at: <pending — 60-02>

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

Green at: <pending — 60-02>

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

Green at: <pending — 60-04>

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

Green at: <pending — 60-04>

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

Green at: <pending — 60-04>

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

Green at: <pending — 60-04 (adds TestRouteAll, empties the pending allowlist)>

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

Green at: <pending — 60-03>

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

Green at: <pending — 60-03 (inverted)>

---

## Controls (green on current code)

- `TestRepro60Evidence` (4): header twin agrees with `replay.hunk_ranges` except on `+T,0` headers; default context widens and never prints a deletion header; the L+8 over-ask (and its `-U0` keep subtest); the net-deletion keep under the header rule.
- `TestCoordinateSpaces60` controls (4): `test_cs60_pr_cumulative_control`, `test_cs60_single_diff_control`, `test_cs60_default_head_only_control`, `test_cs60_default_head_only_boundary_control`.
- `TestFinalizeFreshShellWalk` (2): `test_counts_fence_without_literal_exits_two`, `test_gate_fence_reads_cross_call_variable_today`.
- `TestRepro60Record` (3): record complete, every fixture exists (with the `TestRouteAll` allowlist), fixture lookup trips on a missing name.
- Unchanged locks still green: `TestNearbyEdit`, `TestRepro59Record`, `TestGolden` (GOLDEN_DIGEST untouched); `test_finalize_card.py` outside the walk (70 passed).

## Reverse run

Filled by 60-05.

## Suite at close

Filled by 60-05.

## Residuals

Filled by 60-05.
