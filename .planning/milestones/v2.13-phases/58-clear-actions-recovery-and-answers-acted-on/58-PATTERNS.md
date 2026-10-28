# Phase 58: Clear actions, recovery and answers acted on - Pattern Map

**Mapped:** 2026-10-27
**Files analyzed:** 15 (4 new, 11 modified)
**Analogs found:** 15 / 15
**Plugin root:** `plugins/vibe-check/` (paths below are relative to it unless they start with `README.md` or `.planning/`)
**Line numbers:** read on HEAD `ce1ad47`. Re-check them before editing; this branch moves fast.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/batch_card.py` (+ `resolve` subcommand, `resolve_refs()`) | utility (pure helper + CLI) | transform (file in → JSON out) | `batch_card.py` `parse` / `select` / `select_questions` + `successor_links` | exact |
| `scripts/batch_card.py` (+ `bulk_fix_text` / `nv_rows` rows-doc fields) | utility | transform | `batch_card.py` `card_texts()` merged by `build_rows()` | exact |
| `scripts/batch_parse.py` (only if a label changes; prefer none) | utility (grammar) | transform | itself: `FIX_LOOP_OPTIONS` / `FINALIZE_Q1` / `_BUTTON_TEXT` / `_rest_bands_for` | exact |
| `scripts/test_answer_resolve.py` (NEW) | test (unit + CLI) | transform | `test_batch_card.py` `TestParse`, `TestCliContract`, `TestSuccessor` | exact |
| `scripts/test_card_scope.py` (NEW, D-12) | test (text == behavior) | transform | `test_card_text.py` `TestProseMatchesHelper` + `test_batch_card.py` `TestSelect` | role-match |
| `scripts/test_recovery_pairs.py` (NEW, D-13) | test (prose ↔ code constants) | transform | `test_confirmed_fix.py` `RENDER_NEEDLES` / `CONTRACT_REASONS` + `test_verified_fixes.py` NV_RENDER_LINE lock | role-match |
| `scripts/test_batch_card.py` (CLI contract tuples) | test | — | itself `TestCliContract.test_sealed_tuples` (`:1320-1327`) | exact |
| `scripts/test_fix_loop_card.py` (prose locks + mutant C) | test (prose lock) | — | itself `subset_no_card_problems` (`:398-415`), `nv_card_problems` (`:623-635`) | exact |
| `scripts/test_finalize_card.py` (prose locks) | test (prose lock) | — | itself `LockCase` + `check_*` functions (`:163-171`, `:299-306`) | exact |
| `scripts/test_confirmed_fix.py`, `scripts/test_verified_fixes.py` (pin updates only) | test | — | their own `RENDER_NEEDLES` (`:1171-1174`) / `NV_RENDER_LINE` (`:1270-1273`) | exact |
| `phases/review/50-fix-loop.md` (Other path, card text, budget, residue) | prose spine (controller) | request-response (card → parse → act) | itself `:92-125` Other path + `:29` subset bullet | exact |
| `phases/shared/90-finalize.md` (Mixed…/Other path, Q1 descriptions, budget, I-5/I-11) | prose spine (controller) | request-response | itself `:110-174`; twin `50-fix-loop.md` Other path | exact |
| `phases/review/40-render.md` (per-reason recovery table) | prose spine (render) | transform | itself `:43-45` (`Fix not yet verified:` / `Fix not yet confirmed:` rules) | exact |
| `templates/output-format.md` (NV needs-recheck suffix, `:66-70`) | config/template | transform | `40-render.md:83` (same suffix text, must stay in sync) | exact |
| `README.md` (repo root, `:337`) | docs | — | none needed; one-line rewrite | n/a |
| `.planning/phases/58-…/58-REPRO.md` (verdicts V1-V5) | docs | — | `58-RESEARCH.md` §"Reproduction verdicts" | role-match |

---

## Pattern Assignments

### `scripts/batch_card.py` — new `resolve` subcommand (utility, transform)

**Analog:** `scripts/batch_card.py` itself. Copy the `parse` subcommand's shape, and use `successor_links` for identity re-mapping.

**CLI tables to extend together** (lines 83-122). All five must change in one edit, and `TestCliContract.test_sealed_tuples` pins two of them:
```python
SUBCOMMANDS = ("rows", "select-questions", "select", "payload", "parse",
               "decisions-report")
# The ONLY flags this CLI accepts. No flag ever carries owner text, a title or
# a reason: such text arrives in a file whose path is passed here.
KNOWN_FLAGS = ("--mode", "--head-blobs", "--subset", "--rows", "--answer")
_FLAGS_BY_SUBCOMMAND = {
    ...
    "parse": (("--rows", "--answer"), ()),
    "decisions-report": ((), ()),
}
_STATE_SUBCOMMANDS = ("rows", "payload", "decisions-report")
USAGE = ("usage: batch_card.py rows --mode fix-loop [--subset PATH]" ...)
```
For `resolve`, add `"resolve": (("--rows", "--answer"), ("--prior-rows",))`, add `--prior-rows` to `KNOWN_FLAGS`, extend `USAGE`, and keep `resolve` out of `_STATE_SUBCOMMANDS` because it is pure over the rows docs.

**Fixed refusal reasons** (lines 107-122). A new reason is a module constant added to the `REASONS` tuple and must never contain owner text:
```python
REASON_ROWS = "refused: rows file is missing or malformed\n"
REASON_ANSWER = "refused: answer file is missing or malformed\n"
REASON_ROWS_STATE = "refused: rows file does not match this state\n"

REASONS = (
    USAGE, REASON_STATE_JSON, REASON_HEAD_BLOBS, REASON_SUBSET,
    REASON_SUBSET_EMPTY, REASON_ROWS, REASON_ANSWER, REASON_ROWS_STATE,
)
```

**Answer-shape validator + pure function returning `(result, None) | (None, reason)`** (lines 780-813). Copy this shape for `_valid_resolve_answer` / `resolve_refs`:
```python
def _valid_parse_answer(answer):
    return (isinstance(answer, dict) and "q1" in answer
            and set(answer) <= {"q1", "q2"}
            and isinstance(answer["q1"], str)
            and (answer.get("q2") is None or isinstance(answer["q2"], str)))


def parse(rows_doc, answer):
    """(batch_parse result + payload + fix_targets, None) or (None, reason).
    ...
    """
    if not _valid_parse_answer(answer):
        return None, REASON_ANSWER
```

**CLI dispatch** (lines 1048-1067). Add the `resolve` branch in `_run_answer_side` next to `parse`. Read `--prior-rows` with the same `carry_state.read_json_file` + `_valid_rows_doc` check:
```python
def _run_answer_side(sub, flags, state):
    rows_doc = carry_state.read_json_file(flags["--rows"])
    if not _valid_rows_doc(rows_doc):
        return _refuse(REASON_ROWS), ""
    ...
    answer = carry_state.read_json_file(flags["--answer"])
    if answer is None:
        return _refuse(REASON_ANSWER), ""
    if sub == "select":
        ...
    elif sub == "parse":
        result, reason = parse(rows_doc, answer)
    ...
    if reason is not None:
        return _refuse(reason), ""
    return 0, json.dumps(result, allow_nan=False)
```

**Identity re-map, the D-07 stale-card rule** (lines 374-404, `successor_links`). Match `stable_hash` first. Then match on (file, title), and accept it only when exactly one candidate is found. Several candidates means the reference annotates or resolves nothing:
```python
        candidates = [r for r in rows
                      if (r.get("file"), r.get("title")) == identity
                      and r["stable_hash"] not in decisions
                      and r["stable_hash"] not in acks]
        if len(candidates) == 1:
            claims.setdefault(candidates[0]["stable_hash"], []).append(
                (decision.get("at_pass"), h))
```
Resolve statuses map directly to this rule: 1 candidate → `"one"`, 0 → `"none"`, more than 1 → `"many"`.

**Candidate button labels, D-06** (lines 661-671). Reuse `_label(row)` (`#n file:line`, comma-free) and `_description(row)`. Do not invent a new label format:
```python
def _label(row):
    line = row.get("line")
    has_line = isinstance(line, int) and not isinstance(line, bool)
    return "#%d %s:%s" % (row["n"], _label_file(row.get("file")),
                          str(line) if has_line else "?")
```
For more than 4 candidates, follow the `select_questions` typed-mode precedent (`:688-700`): list the candidates in the question text and take the number through Other.

**Title matching on untrusted text** (lines 426-433). Case-fold and match against `_one_line(row["title"])`, never the raw title:
```python
def _one_line(value):
    """`value` as one printable line: every whitespace or control character
    becomes a space, so a title can never start a fake row of its own."""
```

**Grammar output.** Build the `grammar` string from `"one"` refs as explicit numbers only, never `rest`/`all`. Then validate it by calling `parse(rows_doc, {"q1": grammar, "q2": None})`, which is the existing gate (D-01). Do not write a second validator.

---

### `scripts/batch_card.py` — `bulk_fix_text` / `nv_rows` rows-doc fields (D-10/D-11/D-12)

**Analog:** `card_texts()` (lines 582-610), merged into the doc by `build_rows()` (lines 288-295):
```python
    for i, row in enumerate(rows):
        row["n"] = i + 1
    doc = {"at_pass": last["pass_number"], "mode": mode, "rows": rows}
    if subset is not None:
        doc["subset"] = True
    doc.update(card_texts(rows, mode))
    return doc, None
```
Add a sibling `option_texts(rows, mode, subset)` that is called after numbering and returns `{"nv_rows": [...], "bulk_fix_text": ...}`. On a `subset` doc, `nv_rows` excluded = [], because `select(..., subset=True)` sends every row.

**Behavior the text must equal** (lines 749-753, `select`):
```python
    if "all" in answer:
        numbers = [r["n"] for r in rows
                   if subset or r["band"] != carry_state.NV_BAND]
```
and on Finalize, `batch_parse._BUTTON_TEXT["Fix all"] == "fix rest"` → `_rest_bands_for("fix")` = critical/warning/medium (`batch_parse.py:85-111`). Derive `nv_rows` from the same `carry_state.NV_BAND` literal so text and behavior come from one source.

Note: `_valid_rows_doc` (`:626-650`) ignores unknown top-level keys, so the new fields do not break `parse`/`select` reading an existing rows file.

---

### `scripts/batch_parse.py` (only if a label changes)

**Analog:** itself, lines 47-90. **Recommendation: keep the labels unchanged.** If a label does change, it ripples to `_BUTTON_TEXT` keys plus the tests listed in RESEARCH Pattern 3. Bulk safety lives in one place only:
```python
def _rest_bands_for(verb):
    """Bands a `rest` clause may reach. The bulk-safety rule lives here only."""
    if verb == "fix":
        return _FIX_REST_BANDS
    return ("medium",)
```
D-12 mutant target: make `_rest_bands_for("fix")` include `_NV_BAND`. The `test_card_scope.py` lock must trip on it.

---

### `scripts/test_answer_resolve.py` (NEW; test, unit + CLI)

**Analog:** `scripts/test_batch_card.py`. Import from it directly, as `test_finalize_card.py:25` does (`from test_batch_card import HB, successor_state`).

**Imports / harness** (`test_batch_card.py:30-43`, `:102-118` `TempDirCase`):
```python
HERE = os.path.dirname(os.path.abspath(__file__))
BATCH_CARD_PY = os.path.join(HERE, "batch_card.py")
ALL_REASONS = set(batch_card.REASONS) | set(carry_state.REASONS) | set(
    batch_parse.REASONS)

def run_cli(args, stdin_bytes=b""):
    ...
```

**Row builder** (`:610-616`). Extend it into an eight-row iPlayarr builder with row 5 titled "Browse recovery leaves stale cursor":
```python
def synth_rows(count, at_pass=2):
    bands = ("critical", "warning", "medium")
    return {"at_pass": at_pass, "mode": "fix-loop", "rows": [
        {"n": i + 1, "stable_hash": "%064x" % (i + 1),
         "band": bands[i % 3], "file": "app/f%d.py" % i, "line": i + 1,
         "title": "title %d" % i, "problem": "problem %d " % i + "x" * 100}
        for i in range(count)]}
```
Real-title fixture also available: `scripts/fixtures/iplayarr45-six-row-state.json`.

**CLI parse test shape** (`TestParse`, `:762-790`):
```python
    def parse(self, answer, rows_path=None):
        return run_cli(["parse", "--rows", rows_path or self.rows_path,
                        "--answer", self.write("ans.json", answer)])

    def ok(self, answer, rows_path=None):
        proc = self.parse(answer, rows_path)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        return json.loads(proc.stdout)
```
Refusals must satisfy `self.assertIn(proc.stderr.decode(), ALL_REASONS)` (`:849`), meaning no owner text appears.

**Mutant subtest shape** (`:1009-1043`, `with self.subTest("real") / ("mutant")`, plus `unittest.mock.patch.object`). Use one per check: drop the count check, which should make the mismatch fixture ask; let a `many` match pass as `one`; let the grammar include `rest`. Pitfall 1 applies: assert the fixture has 8 rows and that row 5's title contains "Browse".

**Required fixtures:** the eight-row iPlayarr case (`fix 5; dismiss 1,2,3,4,6,7,8` → parse ok, payload 7 entries, `fix_targets` [row 5]); the D-16 count mismatch (owner says 6 → not acted on); an ambiguous title (`many` + candidates); a prior-card renumber remap; a ref to a row that is gone (`none`); a missing reason (parse `REASON_NO_REASON`).

---

### `scripts/test_card_scope.py` (NEW; D-12 text == behavior)

**Analog:** `scripts/test_card_text.py` `TestProseMatchesHelper` (lines 385-439). This test renders the helper text and asserts it matches, and it has a drift mutant through `mock.patch.object`:
```python
    def test_agreement_trips_on_helper_drift(self):
        state, template, values = self.suffixes()["pending"]
        with mock.patch.object(batch_card, "_suffixes",
                               lambda row, compact: " — pending"):
            rendered = doc_of(state)["card_text"]
        self.assertNotIn(self.fill(template, **values), rendered)
```
Use `doc_of(state, mode, head_blobs, subset)` (`test_card_text.py:34`) to build both card modes. The assertion is that the excluded rows named in `bulk_fix_text` = `nv_rows` = rows missing from `batch_card.select(rows, {"all": True})` (fix-loop) = rows missing from `parse(doc, {"q1": "Fix all", "q2": None})["fix"]` (finalize). Mutants: patch `batch_parse._rest_bands_for` to include NV, and drop a number from the text.

---

### `scripts/test_recovery_pairs.py` (NEW; D-13 prose ↔ `score.py`)

**Analog:** `scripts/test_confirmed_fix.py` (lines 1160-1174), which pins `score.py` reason literals and render needles:
```python
RENDER_NEEDLES = ("Fix not yet confirmed:",
                  "retried on the next run that reviews changes",
                  "run /deep-review", "dismiss",
                  "Closed — fix confirmed by the {{agents}} lane")
```
**Reason source** (`score.py:145-155`, `:176-191`). Collect the constants programmatically rather than retyping them:
```python
_R_IR_NO_REVIEWER = "verdict: fix not yet confirmed: no eligible reviewer ran this pass"
_R_IR_NO_ANSWER = "verdict: fix not yet confirmed: the routed reviewer gave no verdict"
_R_IR_STILL = "verdict: fix not confirmed: the routed reviewer says it still applies"
...
_R_CF_NO_REVIEWER = ("verdict: confirmed fix awaiting independent re-check: "
                     "no eligible reviewer this pass")
```
Use `[v for k, v in vars(score).items() if k.startswith("_R_") and isinstance(v, str) and v.startswith(("verdict: fix not", "verdict: confirmed fix"))]`. Expect 12 constants (7 IR + 5 CF). `_R_ROUTED_ORPHAN` and `_R_CONTRADICTED` drop out because of their prefix. Assert the retrying set is {IR_NO_REVIEWER, IR_NO_ANSWER, IR_SNAPSHOT, CF_NO_REVIEWER, CF_NO_ANSWER, CF_SNAPSHOT}. Mutants: add "retried" to the STILL row, delete a row, and inject a synthetic constant through `mock.patch.dict(vars(score))` or `setattr`. Do not edit `score.py`, because GOLDEN_DIGEST is frozen.

**Pins to update in the same plan:** `test_confirmed_fix.py:1171-1174` (`RENDER_NEEDLES` currently pins "retried on the next run that reviews changes" and "run /deep-review") and `test_verified_fixes.py:1270-1273` (`NV_RENDER_LINE`, `NV_OUTPUT_LINE`).

---

### `scripts/test_fix_loop_card.py` (extend; prose lock)

**Analog:** itself. The check-function pattern is to return a list of problems and assert `[]` on the real text and non-empty on a mutant.

**Literal constants** (`:297-303`):
```python
SUBSET_BULLET = "- **Finalize routed a fix set here (D-10)**"
ORDINARY_BULLET = "- **Every other pass**"
SUBSET_NO_CARD = ("Then print Finalize's `echo_text` as message text, write "
                  "`{\"all\": true}` to `$ANSWERFILE` with the Write tool, and "
                  "go straight to **Step B** — ask NO AskUserQuestion: the "
                  "owner already chose these rows at Finalize (D-06).")
BUDGET_NO_CARD = "a Finalize-routed subset costs no card"
```
**Check function to strengthen against mutant C** (`:398-415`, `subset_no_card_problems`). It currently inspects only the bullet slice and the budget line. Add a scan of the whole `card_section(text)` outside the bullet that flags any sentence tying "Finalize routed" / `$SUBSETFILE` to AskUserQuestion or "show the card".

**Mutant test shape** (`:1100-1110`):
```python
    def test_mutant_subset_asks_again(self):
        mutant = self.card.replace(
            SUBSET_NO_CARD, SUBSET_NO_CARD + " Then call AskUserQuestion to "
            "confirm the rows.", 1)
        self.assertNotEqual(mutant, self.card)
        self.assertNotEqual(subset_no_card_problems(mutant), [])
```
Add mutant C: insert "When Finalize routed a fix set, show the card below so the owner can Apply or Skip." before `**Same-turn rule**`.

**Pins that change** (Pitfall 3): `NV_APPLY_ALL_NOTE` / `NV_CARD_NEEDLES` (`:623-635`), which D-11 folds away; the budget sentence "A pass costs one card" (`:774` area); the neutral-menu locks `test_no_recommended_nudge_anywhere` / `test_no_nudge_lock_trips_on_mutant` (`:666-676`), which must stay green after the D-09 "Bottom line suggests:" line is added.

---

### `scripts/test_finalize_card.py` (extend; prose lock)

**Analog:** itself. Use the `LockCase` helpers (`:299-306`):
```python
class LockCase(unittest.TestCase):
    def assert_holds(self, check, *texts):
        self.assertEqual(check(*texts), [])

    def assert_trips(self, check, *mutant_texts):
        self.assertNotEqual(check(*mutant_texts), [])
```
and the needle-tuple check style (`:163-171`):
```python
TURN_AND_BUDGET = ("THIS assistant turn", "Finalize costs one card",
                   "never re-show the card after recording",
                   "there is NO confirm card")

def check_turn_and_budget(text):
    section = card_section(text)
    return [n for n in TURN_AND_BUDGET if n not in section]
```
Mutant helpers: `remove(text, needle)` (`:88-90`, which asserts the needle exists) and `inject_into_card(text, snippet)` (`:82-85`).
**Pins that change:** `test_bare_mixed_buys_one_clarification` (`:413-428`, pins "re-show the same card ONCE" on the `need_text` bullet). That rule is a bare-Mixed clarification, not a refusal, so decide whether it survives D-01..D-08. Keep "never re-show the card after recording". Also `test_no_nudge` (`:316-325`).

---

### `phases/review/50-fix-loop.md` (prose spine, request-response)

**Analog:** itself. The integration points are:

- **Other path, refusal branch** (`:94-103`). This is the bug site:
  ```
  On a refusal the helper has printed one fixed reason on stderr (it never contains owner text); re-show the SAME card once (D-06: an unparseable answer re-asks, never guesses).
  ```
  Replace it with: translate → Write refs file → `batch_card.py" resolve --rows "$ROWSFILE" --answer "$REFSFILE"` → Write the grammar to `$ANSWERFILE` → the same `parse` fence. Copy the existing fence form exactly:
  ```bash
  PARSEFILE=$(mktemp "${TMPDIR:-/tmp}/vc.XXXXXX")
  if python3 "$VC_ROOT/scripts/batch_card.py" parse --rows "$ROWSFILE" --answer "$ANSWERFILE" > "$PARSEFILE"; then
    cat "$PARSEFILE"
  else
    echo "— nothing was recorded; answer the card again." >&2
  fi
  ```
  The owner-text rule to repeat: "Write `{"q1": "<the Other text, verbatim>", "q2": null}` to `$ANSWERFILE` with the Write tool — the owner's text NEVER goes on a command line".
- **Echo-then-act** (`:103`): "print the parse output's `echo_text` field verbatim as message text, then act on it — no confirm card". Prefix it with `Read your answer as: <grammar> — reason: <reason>` (D-01).
- **Close-out intent** (Pattern 2): steps 2 and 3 (`:113-122`) route to the Rerun. Add "then Close out" routing that reuses the Stop here… → **Close out** wording (`:138`: `$ARGUMENTS = "${original_args} --finalize"`).
- **Card question** (`:64`): fold the NV line into the Apply-all description, which comes from the helper `bulk_fix_text` (D-11). Remove the `{{\n\nFrom your finalize answer:\n<echo_text>}}` residue (I-10). Add the D-09 `Bottom line suggests: …` line as a conditional `{{…}}` slot, using the same omit-when-absent convention as the existing NV line.
- **Option 1 description** (`:66`): `(Needs-verification rows are not applied — confirm them by number.)` → the helper text.
- **Stale decision-hold sentence** (`:73`, I-12): rewrite it to Phase 57 behavior. The wording source is the `PHASE57_DECISIONS` needles in `test_finalize_card.py:155-160`.
- **Card budget** (`:144`): add the D-06 follow-up (one per gap) and the D-08 fallback, and remove "an unparseable answer … re-shows".
- **Subset bullet** (`:29`): leave it as is. It is the governing rule for bug C.

### `phases/shared/90-finalize.md` (prose spine, request-response)

**Analog:** itself, plus the `50-fix-loop.md` Other path as its twin. Integration points:
- Q1 header and option descriptions (`:113-118`): I-1..I-4. Fix all uses the helper `bulk_fix_text`; Dismiss/Defer all must also mention NV rows; replace "`all` means every row of the lowest band" with accurate text; add an NV count to `({{C}} critical/warning, {{M}} medium…)`.
- Refusal (`:139`): "Re-show the SAME card (D-06 …)" becomes the same translate → resolve → parse flow as the fix loop.
- Echo residue (`:145`): delete "as that card's closing 'From your finalize answer:' block" (I-11).
- NV stop list (`:53`, I-5): remove "re-checks it once".
- Budget (`:174`): same edit as the fix-loop budget.
- Stop messages (`:168-170`) are checked consistent (I-15). Do not edit them.

### `phases/review/40-render.md` (prose spine, render transform)

**Analog:** itself, `:43-45`. Current form, one rule per sentence, with special cases appended as "render instead …":
```
render under the row `Fix not yet confirmed: {{reason with its leading "verdict: fix not yet confirmed: " or "verdict: fix not confirmed: " removed}} — retried on the next run that reviews changes; or run /deep-review so the raising lane can answer; or dismiss it by number.`
```
Replace the shared tail and the three "render instead" special cases with one markdown table: reason literal → `Next run:` → `You can:`, covering all 12 constants (RESEARCH Pattern 4 draft pairs). Add the pair to the `Fix not yet verified:` rule (`:43`, I-9). Also update the NV needs-recheck suffix at `:83` (I-8). `test_recovery_pairs.py` parses the table, so give it a stable heading or marker the test can slice on (as `card_section` slices on `CARD_HEADING`).

### `templates/output-format.md` (template)

**Analog:** `40-render.md:83`. The suffix at `:66-70` repeats the render text word for word and must change in step with it (`test_verified_fixes.py` `nv_needs_change_prose_holds` reads both).

### `README.md` (repo root, `:337`)

Rewrite the single bullet "gets **one** automatic independent re-check, on the next review run" to say the re-check is retried on every later run that reviews changes while the repaired code is unchanged (`05-state.md:55`, `score.py:1765-1772`). There is no other README recovery text (RESEARCH V5).

---

## Shared Patterns

### Owner text only through files (security, absolute)
**Source:** `batch_card.py:84-86` comment and `50-fix-loop.md:94`
**Apply to:** the `resolve` CLI, every new prose fence, and the refs/grammar/suggestion files
```python
# The ONLY flags this CLI accepts. No flag ever carries owner text, a title or
# a reason: such text arrives in a file whose path is passed here.
```
The prose writes JSON with the Write tool, and fences take only file paths. For file-to-file copies of helper output, use the existing idiom:
```bash
if python3 -c 'import json,sys; json.dump(json.load(sys.stdin)["fix_targets"], sys.stdout)' < "$PARSEFILE" > "$SUBSETFILE"; then
```

### Fixed refusal strings
**Source:** `batch_card.py:107-122`, `batch_parse.py:53-71`; tested by `test_batch_card.py:511-515` (REASONS is a tuple, each entry ends with `\n`) and `assertIn(stderr, ALL_REASONS)`
**Apply to:** every new `resolve` refusal

### Helper-rendered text copied verbatim by the prose
**Source:** `build_rows` → `card_texts` → prose "`{{card_text}}` is the `card_text` field, verbatim" (`50-fix-loop.md:64`, `90-finalize.md:113`)
**Apply to:** `bulk_fix_text`, `nv_rows`, and the `resolve` grammar/candidates. The prose never computes row sets itself.

### Lock + mutant pairing (no decorative guards)
**Source:** `test_finalize_card.py` `LockCase.assert_holds/assert_trips`; `test_fix_loop_card.py` `test_mutant_*` (`assertNotEqual(mutant, text)` before asserting a trip)
**Apply to:** every new check in all three new test files and both extended card tests

### Bash fences
**Source:** `50-fix-loop.md:18-27`. Use `mktemp "${TMPDIR:-/tmp}/vc.XXXXXX"` and `if …; then … else echo "…" >&2; fi`. Never add an optional-flag expansion (`OPTIONAL_EXPANSION` lock in `test_git_safety_prose`). Pass literal paths across Bash calls.

### Neutral menu
**Source:** `50-fix-loop.md:12` LEGIBLE-03 comment; locks `test_fix_loop_card.py:666-676`, `test_finalize_card.py:316-325`
**Apply to:** the D-09 suggestion line and the D-10/D-11 descriptions. No "Recommended" and no nudge wording.

## Conventions

Convention derivation skipped (`verify conventions --derive --scope plugins/vibe-check/scripts` → `{"skipped": true, "reason": "no-app-files"}`, because the scope is Python-only). Observed local conventions, by reading the files:

| Axis | Dominant | Status |
|---|---|---|
| File-name casing | `snake_case.py`; tests `test_<module>.py` | named contract |
| Identifier casing | `snake_case` functions, `UPPER_SNAKE` constants, `_leading` private, `REASON_*` refusal constants | named contract |
| Export style | module-level functions + `if __name__ == "__main__"` stdin/stdout shim; stdlib only | named contract |
| Import style | `sys.path.insert(0, dirname(__file__))` then sibling `import x  # noqa: E402  (reason)` | named contract |

Contested hotspots (author's choice): none inside `plugins/vibe-check/scripts`. The CJS↔SDK dual-resolver split (`bin/lib/**` CJS vs `sdk/src/**` ESM) is a GSD-tooling convention and does not apply to this repo. Match the local directory style.

## No Analog Found

None. `58-REPRO.md` has no codebase analog. Copy its structure from `58-RESEARCH.md` §"Reproduction verdicts" (verdict, fixture, commands, mutant table).

## Metadata

**Analog search scope:** `plugins/vibe-check/scripts/` (batch_card, batch_parse, score, test_batch_card, test_fix_loop_card, test_finalize_card, test_card_text, test_confirmed_fix, test_verified_fixes), `plugins/vibe-check/phases/{review,shared}/`, `plugins/vibe-check/templates/output-format.md`, `README.md`
**Files scanned:** 14
**Pattern extraction date:** 2026-10-27
