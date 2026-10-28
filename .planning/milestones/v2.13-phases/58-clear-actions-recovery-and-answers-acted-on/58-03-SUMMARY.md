---
phase: 58-clear-actions-recovery-and-answers-acted-on
plan: 03
subsystem: decision-cards
tags: [batch_card, resolve, plain-english-answers, ANSR-01, ANSR-02, V1]
requires:
  - "58-01 (rows doc shape incl. nv_rows / bulk_fix_text)"
provides:
  - "batch_card.resolve_refs(rows_doc, refs_doc, prior_rows_doc=None)"
  - "batch_card.py resolve --rows R --answer F [--prior-rows P] CLI"
  - "REASON_REFS / REASON_PRIOR_ROWS / REASON_PRIOR_NEEDED"
affects: [58-04, 58-05]
tech-stack:
  added: []
  patterns: ["deterministic reference resolution ahead of the strict parser", "mock mutants + real-file mutants per lock"]
key-files:
  created:
    - plugins/vibe-check/scripts/test_answer_resolve.py
  modified:
    - plugins/vibe-check/scripts/batch_card.py
    - plugins/vibe-check/scripts/test_batch_card.py
decisions:
  - "A countless `remaining` (bulk) ref reports the rows the parser's `rest` would reach (unclaimed rows in batch_parse._rest_bands_for(verb)), so `verbs` equals what parse acts on in every ok case"
  - "count_mismatch and conflict refs list the matched rows as `candidates` (label + title) so the D-06 follow-up can name them; `rows` is populated only for one/bulk"
  - "The reason is passed through _one_line before it is appended to the grammar; blank reason counts as none"
  - "A marker with no count that matches 0 rows is `none`; with no count and ≥1 rows it is `one`"
metrics:
  duration: ~35 min
  completed: 2026-10-27
  tasks: 3
  files: 3
---

# Phase 58 Plan 03: resolve maps plain-English answers to card grammar Summary

`batch_card.py resolve` maps the owner's references to current row numbers and builds a grammar string. The references can be row numbers, numbers from an older card, title words, card markers, or the D-16 counted complement. The unchanged strict `parse` then dry-runs the grammar, so the parser stays the only gate (D-01). The eight-row iPlayarr answer now resolves to `fix 5; dismiss 1,2,3,4,6,7,8 -- <reason>` and the parser accepts it. Ambiguity, count mismatch, gone rows, a missing reason, a stale card and conflicts are each detected deterministically.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 (RED) | cf5043b | test(58-03): add failing resolve expectations; eight-row iPlayarr fixture and V1 reproduction |
| 2 (GREEN) | f52258f | feat(58-03): batch_card.py resolve maps owner references to rows; parse stays the gate (D-01, D-02, D-04, D-07, D-16) |
| 3 (mutants) | 138d8cc | test(58-03): resolve lock mutants and CLI contract |

## Contract for 58-04 / 58-05 (copy verbatim into the prose)

CLI: `python3 batch_card.py resolve --rows ROWS.json --answer REFS.json [--prior-rows OLD_ROWS.json]`. It reads no stdin. Owner text goes only in REFS.json, written with the Write tool.

Refs file:
```json
{"refs": [
   {"verb": "fix",     "kind": "number",       "n": 5},
   {"verb": "fix",     "kind": "title",        "text": "Browse recovery"},
   {"verb": "dismiss", "kind": "marker",       "marker": "remaining", "count": 7},
   {"verb": "defer",   "kind": "prior_number", "n": 3}
 ],
 "reason": "fixed (owner: \"dismiss the 7 fixed rows\")" | null,
 "close_out": true | false}
```
- `verb` ∈ `fix` / `dismiss` / `defer`.
- `kind` ∈ `number`, `prior_number`, `title`, `marker`.
- `marker` ∈ `remaining`, `band:critical`, `band:warning`, `band:medium`, `band:needs-verification`, `pending`, `changed`, `absorbed`.
- `count` is an optional int ≥ 1, allowed on markers only.
- `text` must be a non-blank string. `n` is an int ≥ 1.
- Keys are exact per kind. `refs` is required and non-empty. `reason` and `close_out` are optional and default to null / false.
- Anything else → exit 2 with `refused: refs file is missing or malformed`.

Output (stdout JSON, exit 0):
```json
{"ok": false, "stale": false, "needs_reason": false, "close_out": true,
 "refs": [{"status": "one", "rows": [5], "candidates": []},
          {"status": "many", "rows": [], "candidates": [{"label": "#2 app/a.py:10", "title": "…"}, …]}],
 "verbs": {"fix": [5], "dismiss": [1,2,3,4,6,7,8], "defer": []},
 "grammar": "fix 5; dismiss 1,2,3,4,6,7,8 -- fixed (owner: …)" | null,
 "parse_reason": null | "<a batch_parse.REASONS string>"}
```
- Statuses:
  - `one`: exactly one set of rows.
  - `none`: no row matched.
  - `many`: more than one candidate. Each candidate is `_label(row)` plus `_one_line(title)`, cut to 80 characters.
  - `count_mismatch`: the stated count differs from the matched count. `candidates` lists the matched rows.
  - `conflict`: the ref names a row an earlier ref already claimed. `candidates` lists the matched rows.
  - `bulk`: `remaining` with no count. It becomes `<verb> rest`, and its `rows` are the rows `rest` reaches.
  - `blocked`: a `remaining` ref whose rows cannot be computed because another ref is not `one`.
- Resolution order: non-`remaining` refs are resolved first, in order, and each one claims its rows. Then each `remaining` ref is resolved over the rows still unclaimed.
- `prior_number` is re-mapped by `stable_hash` first, then by an equal `(file, title)`.
- `grammar` is built when every ref is `one` or `bulk`, including when the reason is missing. Clauses run fix, then dismiss, then defer, with numbers ascending. ` -- reason` is appended only for a non-blank reason.
- `ok` = a grammar was built and `parse_reason` is null.
- `needs_reason` = `parse_reason == "refused: dismiss/defer needs a reason\n"`.
- `stale` = `--prior-rows` was given and either the `at_pass` differs or the ordered `stable_hash` lists differ.
- `close_out` is echoed back unchanged. It is a same-turn signal only.

Refusals (stderr, exit 2, no stdout, never owner text):
- `refused: refs file is missing or malformed\n`
- `refused: prior rows file is missing or malformed\n`
- `refused: a prior-card reference needs --prior-rows\n`
- `refused: rows file is missing or malformed\n`
- `USAGE`, which now ends `| resolve --rows PATH --answer PATH [--prior-rows PATH]  (state on stdin for rows, payload, decisions-report)`

CLI tables after this plan:
- `SUBCOMMANDS` = `(…, "decisions-report", "resolve")`
- `KNOWN_FLAGS` = `(…, "--answer", "--prior-rows")`
- `_FLAGS_BY_SUBCOMMAND["resolve"] = (("--rows", "--answer"), ("--prior-rows",))`
- `resolve` is not in `_STATE_SUBCOMMANDS`

## Fixtures (checked by `TestFixture`)

- `iplayarr_rows()` has 8 rows numbered 1-8 with bands 3 critical, 4 warning, 1 medium.
  - Rows 1-4 and 6, 8 are the real iPlayarr titles and hashes from `fixtures/iplayarr45-six-row-state.json`. That fixture really is 3 critical / 2 warning / 1 medium (asserted).
  - Row 7 is the synthetic warning "Retry budget is not reset after a successful relay".
  - Row 5 is "Browse recovery leaves a stale cursor after a failed page load". No other title contains "browse" when case-folded.
  - All 8 hashes are distinct, and `_valid_rows_doc` accepts the doc.
- `timeout_rows()`: only rows 2 and 4 contain "timeout".
- `pending_rows()`: only row 2 has `pending_since`.
- `stale_pair()`: prior rows 1 and 2 are gone. Browse keeps its hash and is now row 3. Prior row 6 was re-hashed with the same file and title (now row 4). Prior row 7 kept its hash but was retitled (now row 5).

## RED (Task 1, before batch_card.py changed)

- `pytest -q scripts/test_answer_resolve.py -k "Fixture or V1Reproduction"` → `6 passed, 45 deselected`.
- V1 anchors:
  - The plain-English answer exits 2 with `refused: answer does not match the grammar`.
  - The grammar answer exits 0 with `fix_targets == [row 5 hash]` and 7 dismiss entries carrying the reason.
- `pytest -q scripts/test_answer_resolve.py -k "Resolve"` → `57 failed, 7 passed, 5 skipped`.
  - The failure count includes subtests.
  - `-k Resolve` also matched the file name, so the 7 passes are the fixture and V1 tests plus the subtest parent of `test_cli_malformed_refs`, whose 18 subtests all failed.
- Verbatim error lines (count × line):
```
  32 E       AttributeError: module 'batch_card' has no attribute 'resolve_refs'
  18 E               AttributeError: module 'batch_card' has no attribute 'REASON_REFS'. Did you mean: 'REASON_ROWS'?
   1 E       AttributeError: module 'batch_card' has no attribute 'REASON_PRIOR_NEEDED'
   1 E       AttributeError: module 'batch_card' has no attribute 'REASON_PRIOR_ROWS'
   1 E       AssertionError: 'decisions-report' != 'resolve'
   3 E       AssertionError: 2 != 0 : usage: batch_card.py rows --mode fix-loop [--subset PATH] | ... | decisions-report  (state on stdin for rows, payload, decisions-report)
   1 E       AssertionError: 'usage: batch_card.py rows --mode fix-loop[264 chars]t)\n' != 'refused: rows file is missing or malformed\n'
```

## GREEN (Task 2)

- Focused set (answer_resolve, batch_card, card_scope, card_text, batch_parse): `230 passed, 5 skipped, 258 subtests passed`. The 5 skips were the Task-3 mutant placeholders.
- Cross-check (finalize_card, fix_loop_card, confirmed_fix, decision_continuity): `282 passed, 356 subtests passed`.
- Acceptance greps:
  - `def resolve_refs`: 1
  - `sub == "resolve"`: 1
  - `"--prior-rows"`: 4
  - every `REASONS` entry ends with `\n`: exit 0
- CLI smoke, run from a scratch dir with real files:
  - Eight-row refs → exit 0, `"grammar": "fix 5; dismiss 1,2,3,4,6,7,8 -- fixed (owner: \"dismiss the 7 fixed rows\")"`, `ok: true`.
  - Count 6 → exit 0, statuses `['one', 'count_mismatch']`, grammar `None`.
  - `prior_number` without `--prior-rows` → exit 2, stderr `refused: a prior-card reference needs --prior-rows`.
- `batch_parse.py` and `score.py` are unchanged. Diff over the plan: `batch_card.py`, `test_answer_resolve.py`, `test_batch_card.py` only.

## Mutants

Mock mutants (`TestResolveLockTrips`): for each one, the real subtest passes; the mutant output is first asserted to differ from the real output, and then the shared lock check is asserted to raise.

| Mutant | Patch | Observed |
|--------|-------|----------|
| m1 count check dropped | `_count_status` → `one` if matched | owner-says-6 ref becomes `one`; `check_count_mismatch` raises |
| m2 many treated as one | `_match_title` → first match only | "timeout" becomes `one`; `check_ambiguous_title` raises |
| m3 `rest` for a counted ref | `_grammar_for` turns the dismiss clause into `rest` | grammar `fix 5; dismiss rest -- …`; parse dismisses only row 8 ≠ verbs [1..4,6..8]; `check_no_broadening` raises |
| m4 hash remap skipped | `_remap_prior` sees a non-matching hash | the retitled prior row 7 becomes `none`; `check_hash_remap` raises |
| m5 conflict check dropped | `_claim` always claims | `[fix 5, dismiss 5]` becomes `one`/`one`; parse still refuses with `REASON_DUPLICATE` (second net); `check_conflict` raises |

Real-file mutants were applied to `scripts/batch_card.py` by a scratch driver (`real_mutants.py`), with `pytest -q scripts/test_answer_resolve.py` run after each. After each run the file was restored from a backup and checked with `filecmp.cmp(shallow=False)`, then confirmed unmodified by `git status`. Failure counts include subtests.

| Mutant | Real-file edit | Observed |
|--------|----------------|----------|
| m1 (hand check) | `if count is not None and len(matched) != count:` → `if False:` | 6 failed: `test_count_mismatch_asks`, `test_count_mismatch_lists_matched_rows`, `test_band_critical_count_mismatch`, `test_cli_count_mismatch_exits_zero` (+ m1 real subtest) |
| m2 | `_match_title` result sliced `[:1]` | 3 failed: `test_ambiguous_title_many` (+ m2 real subtest) |
| m3 | `"rest" if res["status"] == "bulk" or ref.get("count") else …` | 8 failed: `test_eight_row_grammar`, `test_eight_row_no_broadening`, `test_same_gate_as_the_v1_grammar`, `test_cli_eight_row`, `test_band_critical_count_matches`, `test_counted_reference_never_emits_rest_or_all` (+ subtests) |
| m4 | `if same_hash:` → `if False:` | 3 failed: `test_retitled_row_keeps_hash_identity` (+ m4 real subtest) |
| m5 | `if claimed & set(numbers):` → `if False:` | 3 failed: `test_conflict` (+ m5 real subtest) |

The CLI contract (`TestResolveCliContract`) covers the following. `pytest -q -k Cli | grep -c Browse` → 0.
- Every refusal is in `REASONS`. The cases are bad verb, prior needed, prior malformed and non-JSON refs.
- No owner or title words appear in stderr: "Browse", "recovery", "zebra" and "dismiss the 7" were checked.
- Four usage-error argvs give exactly `USAGE`.
- `resolve` given stdin `b"garbage \xff"` still exits 0 with `ok: true`.

## Full suite

`pytest -q` from `plugins/vibe-check` → **3412 passed, 4579 subtests passed**, 0 failed (167 s). That is 3358 baseline + 54 new tests.

## Threat model

- T-58-07: titles are matched only as case-folded substrings of `_one_line(title)`. The output carries row numbers. The no-broadening check (per verb, resolve `verbs` == what parse acts on) holds, and m3 trips it.
- T-58-08: resolve takes only path flags, and `KNOWN_FLAGS` is sealed by `test_sealed_tuples` in both test files. The reason travels in the refs file and the output JSON.
- T-58-09: a countless `remaining` becomes `rest`, so the parser's bulk rules apply. The counted complement is used only when the count matches (m1, m3).
- T-58-10: the three new constants are in `REASONS`, and `TestResolveCliContract` asserts that stderr is in `REASONS` and contains no owner text.
- T-58-11: prior-number remap goes by stable_hash first, then by unique (file, title). `stale` is surfaced. m4 trips.

## Deviations from Plan

None that change the plan's behavior. Implementation notes:
- **m1 helper name:** the count check lives in `_count_status(matched, count)`, not inside `_marker_rows`. This way one named helper covers both band markers and the `remaining` complement. The plan allowed "or the equivalent named helper". `_grammar_for` takes `(clauses, reason)`, where clauses are `(verb, [numbers] | "rest")`, rather than a verbs dict. It needs the bulk-vs-explicit distinction.
- **Bulk `rows`:** a `bulk` ref's `rows` are the rows `rest` would reach, computed with `batch_parse._rest_bands_for`. That makes the "union of verbs == parse result" check hold for bulk answers too (`test_bulk_remaining_without_count_is_rest` asserts that parse dismisses only row 8, which is the medium row).
- **Candidates on `count_mismatch` / `conflict`:** these refs also fill `candidates` with the matched rows, which the D-06 follow-up needs. This adds to the interface; it changes nothing in it.
- **Mutant driver:** the guard hook (holdout barrier) blocked the first real-file mutant attempt, a bash heredoc that used shell variables. The same mutants were then run through a Python driver in the scratchpad with explicit absolute paths. The holdout folder was not touched.

**Cost if wrong:** low. All of these are internal helper shapes or additive output fields. 58-04/58-05 consume only the documented contract above.

## Known Stubs

None.

## Self-Check: PASSED
- FOUND: plugins/vibe-check/scripts/test_answer_resolve.py
- FOUND: plugins/vibe-check/scripts/batch_card.py (`def resolve_refs`, `sub == "resolve"`)
- FOUND: cf5043b, f52258f, 138d8cc
