# Phase 60: Exact change evidence and reliable Finalize - Pattern Map

**Mapped:** 2026-10-29
**Files analyzed:** 12 (3 new, 9 modified)
**Analogs found:** 12 / 12 (one partial: the PR capture fixture has a format analog only)

All paths are relative to `plugins/vibe-check/` unless prefixed with `.planning/`. Run tests from `plugins/vibe-check/scripts` with bare `pytest`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/diff_ranges.py` (NEW) | utility (pure CLI helper) | transform (stdin diff text → stdout JSON) | `scripts/finalize_gate.py` (shim + docstring contract), `scripts/count_cards.py` (`run(argv)` → exit code), `scripts/replay.py:203-221` `hunk_ranges` (anti-analog) | exact (role + flow) |
| `scripts/test_diff_ranges.py` (NEW) | test | real git in temp repo → helper | `scripts/test_gitsnap.py` (gitfixture + CLI subprocess), `scripts/test_finalize_gate.py:520-540` (import-set lock) | exact |
| `scripts/fixtures/pr-cumulative.diff` (NEW) | fixture (captured data) | file-I/O | `scripts/fixtures/iplayarr45-six-row-state.json` (checked-in real-derived fixture, loaded by path constant) | partial (format differs) |
| `scripts/test_decision_continuity.py` (EXTEND) | test (real chain) | score → carry → card → gate | itself: `TestNearbyEdit` (436-500), `run_pass` (208), `REPRO_59` / `TestRepro59Record` (2608-2680) | exact |
| `scripts/test_finalize_card.py` (EXTEND) | test (prose lock + fence walk) | prose → regex; fresh `bash -s` | itself: `check_printed_paths` (511-528), `ROWS_CALL` (38); `test_fix_loop_card.py:2618-2760` `TestSubsetDispatchWalk` | exact |
| `scripts/test_nv_render.py` (UPDATE) | test (prose phrase lock) | prose → phrase set | itself: `DELETION_RANGE_PHRASES` (199-213, mutants 551-564) | exact |
| `phases/shared/90-finalize.md` (MODIFY) | orchestrator prose (Bash fences) | request-response, cross-call temp files | same file: `SUGGESTFILE` fence (138-146), `ROWSFILE` fence (79-91), "Temp paths are literals" (95) | exact |
| `phases/review/30-collect-score.md` (MODIFY, line 64 bullet) | orchestrator prose | transform hand-off (git → helper → envelope) | `90-finalize.md:15-22` counts fence (fail-closed helper call) | role-match |
| `phases/review/00-scope.md` (MODIFY, modes 1-4, lines 38-55) | orchestrator prose | route diff commands | itself | exact |
| `phases/review/05-state.md` (MODIFY, step 3, line 85) | orchestrator prose | incremental diff | itself + `00-scope.md` | exact |
| `phases/review/05-state-all.md` / `00-scope-all.md` (record only, D-06) | orchestrator prose | none (no diff) | n/a: an "unsupported fixture" record, not code | n/a |
| `.planning/phases/60-…/60-REPRO.md` (NEW) | planning record | n/a | `.planning/phases/59-stale-decisions-and-lost-deferrals/59-REPRO.md` | exact |

## Pattern Assignments

### `scripts/diff_ranges.py` (utility, transform)

**Analog A:** `scripts/finalize_gate.py`. This is the best template for a pure stdin→stdout helper: module docstring states the contract, a stdlib-only import set (locked by a test), and the only process I/O is in a guarded `__main__` shim.

**Docstring contract shape** (lines 86-95):
```python
I/O: stdlib only, imports exactly {json, sys}. CLI:

    echo '{"flags": {...}}' | python3 finalize_gate.py
    python3 finalize_gate.py review-closed < .turingmind/REVIEW.md

Any other argv exits 2 with nothing on stdout.

JSON stdin -> JSON stdout. Unparseable stdin propagates so the process exits
NON-ZERO.
```
For `diff_ranges.py`, use: imports exactly `{json, re, sys}`; `git diff … | python3 diff_ranges.py` → `{file: [[s,e],…]}`; structural refusal → exit 2 with a one-line reason on stderr and nothing on stdout; empty input → `{}` exit 0.

**Module-level reason constants** (lines 111-127). Copy this shape so tests can assert exact reasons and none carry attacker text:
```python
REASON_NO_STATE = "no prior review passes"
...
REASONS = (
    REASON_NO_STATE,
    ...
)
```
Suggested constants: `REASON_MBOX` ("commit series, not a single diff"), `REASON_COMBINED` ("combined diff"), `REASON_SHORT_BODY`, `REASON_LONG_BODY`, `REASON_BAD_BODY_LINE`. Never echo a path or content line in a reason (the diff is attacker-authored).

**`__main__` shim** (lines 231-244):
```python
# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY process I/O. Fails CLOSED on bad input.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    if len(sys.argv) == 1:
        json.dump(run(json.load(sys.stdin)), sys.stdout, allow_nan=False)
    ...
    else:
        sys.exit(2)
```
Differences for diff_ranges: read `sys.stdin.buffer.read().decode("utf-8", errors="surrogateescape")` (RESEARCH Pattern 1 step 1), call `ranges_from_diff`, catch ONLY the module's own `RangeError` → write the reason to stderr, exit 2. Do not wrap in a bare except.

**Analog B (exit-code shape):** `scripts/count_cards.py:171-198`:
```python
def run(argv):
    ...
    except IntegrityError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    except (OSError, ValueError) as exc:
        sys.stderr.write("unreadable input: %s\n" % type(exc).__name__)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
```
Use `run(argv, stdin_bytes)` → int so tests can call it in-process and mutants can patch it (same split `test_gitsnap.py` uses).

**Anti-analog (do NOT copy, do NOT edit):** `scripts/replay.py:203-221` `hunk_ranges`. It parses headers only, uses `splitlines()`, and treats any `+++ ` line as a file header. Those are exactly the three anti-patterns in RESEARCH. It stays context-inclusive on purpose for B3 replay fidelity:
```python
def hunk_ranges(diff_text):
    """{file: [[start, end], ...]} from the new-side hunk headers, context included."""
    out = {}
    cur = None
    for ln in (diff_text or "").splitlines():
        if ln.startswith("+++ "):
            p = ln[4:].strip()
            ...
        m = _HUNK_RE.match(ln)
        if m and cur:
            start = int(m.group(1))
            count = int(m.group(2)) if m.group(2) is not None else 1
            if count > 0:
                out.setdefault(cur, []).append([start, start + count - 1])
    return out
```
The `+++ b/` prefix-strip idiom (`p[2:] if p.startswith("b/") else p`) is reusable. Add a test asserting `replay.hunk_ranges` is unchanged (a one-case pin) so nobody "fixes" it by mistake.

**Core algorithm:** RESEARCH.md §"Code Examples / Builder core" (lines 305-359) is the reference shape. There is no in-repo analog for the marker walk itself.

**Consumer contract (unchanged):** `scripts/score.py:177` `_NEARBY_LINES = 5`; `score.py:1554-1566` `_nearby_changed` uses `window = range(max(1, line - _NEARBY_LINES), line + _NEARBY_LINES + 1)`; `score.py:3115` `_line_in_ranges`. Output shape `{file: [[start,end],…]}` must match exactly, with sorted keys and merged ranges.

---

### `scripts/test_diff_ranges.py` (test, real git → helper)

**Analog:** `scripts/test_gitsnap.py` (lines 1-60) plus `scripts/gitfixture.py`.

**Imports + module constant** (test_gitsnap.py 11-28):
```python
import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import gitsnap  # noqa: E402  (module under test)
import gitfixture  # noqa: E402  (shared temp-repo helper)
from gitfixture import git, write  # noqa: E402

GITSNAP = os.path.join(SCRIPTS_DIR, "gitsnap.py")
```

**Temp-repo setUp/tearDown** (test_gitsnap.py 31-44):
```python
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self.repo = gitfixture.make_repo(self.tmp)
        write(self.repo, "f.txt", "one\n")
        git(self.repo, "add", "--", "f.txt")
        git(self.repo, "commit", "-q", "-m", "init")
    def tearDown(self):
        self._tmp.cleanup()
```

**CLI as subprocess with isolated config** (test_gitsnap.py 48-54):
```python
    def cli(self, *args, root=None):
        proc = subprocess.run(
            [sys.executable, GITSNAP, *args], cwd=self.tmp,
            env=gitfixture.helper_env(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=120)
        return proc
```
For diff_ranges, pass `input=` with the diff text (bytes) instead of argv.

**gitfixture API** (`scripts/gitfixture.py`): `helper_env()` (null global/system config), `git(repo, *args, check=True)` → CompletedProcess, `make_repo(tmp)` → realpath, `write(repo, rel, data)`. For the hostile-config fixture (RESEARCH Pitfall 2), set `color.ui=always`, `diff.mnemonicPrefix=true`, `diff.noprefix=true` with `git(repo, "config", …)` (repo-local), then run the PROSE command flags `--no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/`.

**Import-set lock** (test_finalize_gate.py 520-540). Copy verbatim, with `ALLOWED = {"json", "re", "sys"}`:
```python
    def _imported(self):
        imported = set()
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        return imported
```

**Required cases (from RESEARCH repro table, lines 114-121):** delete 9 → `[[8,9]]`; replace 10 → `[[10,10]]`; insert after 15 → `[[16,16]]`; delete 10-12 → `[[9,10]]`; net-deletion replace 10-12→1 → `[[10,11]]` (D-02); edits at 5 and 10 → `[[5,5],[10,10]]`. The equivalence assertion `ranges(git diff) == ranges(-U0) == ranges(-U10)` goes on every shape. Edge cases: delete line 1 → `[[1,1]]`; delete last lines (cursor N+1); `-- x`/`++ y` content lines; space-in-path trailing tab; `\ No newline`; mbox `From <40hex> ` → exit 2; `@@@` → exit 2; truncated body → exit 2.

**Mutation pattern:** each guard needs a mutant that trips it, either a module-level patch (as `test_gitsnap.py` mutant tests do with `mock.patch` on one component) or a copied source with one token swapped. Required mutants: header-count reader instead of markers (trips the equivalence test), D-02 `+1` removed (trips the net-deletion case), budget-consumption removed (trips the `-- x` case), mbox refusal removed.

**Route coverage (D-06):** one test class per route (default `git diff HEAD`, GSD `git diff $PHASE_START`, incremental `git diff $LAST_REVIEWED_SHA`, range `git diff a..b`, PR via `fixtures/pr-cumulative.diff`), plus an explicit `--all` "unsupported fixture" record (see REPRO table pattern below).

---

### `scripts/fixtures/pr-cumulative.diff` (fixture)

**Analog:** `scripts/fixtures/iplayarr45-six-row-state.json`, loaded by a path constant (test_fix_loop_card.py 2618-2619):
```python
SIX_ROW_FIXTURE = os.path.join(HERE, "fixtures",
                               "iplayarr45-six-row-state.json")
```
A `.diff` cannot carry a header comment, so record its provenance (PR number, exact command `gh pr diff <n> --color never`, capture date, cut at `diff --git` boundaries) in the test module docstring next to the path constant, and in 60-REPRO.md. The test must also assert the fixture contains no `From <40hex> ` line and at least two `diff --git` sections, so the fixture is shown to hold what the test assumes (memory: decorative guards).

---

### `scripts/test_decision_continuity.py` (EXTEND: SC1/SC2 real-diff boundary pair + relocated finding)

**Analog:** the same file's harness and `TestNearbyEdit`.

**Harness entry points** (lines 77-80, 157-162, 208-226, 248-255, 323-331):
```python
def base_file(n=60):
    return ["line_%02d = %d" % (i, i) for i in range(1, n + 1)]

def deletion_hunk_ranges(file, t):      # hand-built; stays as a unit helper only
    return {file: [[max(t, 1), t + 1]]}

def run_pass(state, lines, findings, n, ranges, decided=frozenset(), **over):
    env = {"command": "deep-review", "all_mode": False, "pass_number": n,
           "changed_line_ranges": ranges, ...}
    result = score.run(env)
    return append_pass(state, result, n, "h%d" % n), result

def pass1(lines, title=TITLE_A, conf=70, kind="dismiss", agent="bugs",
          line=10, **kw):
```

**Boundary-pair test shape** (lines 442-470, 471-477). The new tests replace the hand-built `{F: [[at, at]]}` with ranges from a real `git diff` through `diff_ranges.ranges_from_diff`:
```python
    def _edit(self, at, n=2, base=None, state=None, h=None):
        L0 = base or base_file()
        if state is None:
            state, h = pass1(L0, conf=STABLE_CONF)
        L2 = list(L0)
        L2[at - 1] = "line_%02d = 'edited'" % at
        s2, _ = run_pass(state, L2, [], n, {F: [[at, at]]})
        return L2, state, s2, h

    def test_r2_edit_within_five_beneath_reopens(self):
        ...
                self.assertEqual(carry_state.decision_state(rec, s2), "stale")
                self.assertEqual(carry_state.stale_cause(rec, s2), "nearby")
                self.assertEqual(row_of(s2, hA)["snapshot"].get("nearby_at"), 2)
                self.assertNotEqual(e2e_gate(s2, {}), "write")

    def test_r2_edit_six_beneath_keeps(self):
        _, s1, s2, hA = self._edit(16)
        ...
        self.assertEqual(carry_state.decision_state(rec, s2), "current")
        self.assertNotIn("nearby_at", row_of(s2, hA)["snapshot"])
```
New real-diff variant: write `"\n".join(L0)+"\n"` to `src/a.py` in a `gitfixture.make_repo` repo, commit, write `L2`, run `git diff --no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/ HEAD`, feed `.stdout` to the builder, pass the result as `ranges`. Required pairs: edit at L+5 reopens / L+6 keeps; delete at the boundary (deletion rule) reopens / just outside keeps; net-deletion replace at the boundary reopens (D-02, failing first); a pre-fix sanity case showing the default-context diff fed through the OLD header rule reopens at L+6..L+8 (the 999.24 repro). `F = "src/a.py"` (line 67) is the file key.

**Repro record** (lines 2608-2680). Add `REPRO_60` + `TestRepro60Record` with the same six-key row shape:
```python
REPRO_59 = (
    {"id": "CR-01", "decision": "STALE-01",
     "scenario": "...",
     "probe_result": "...",
     "disposition": "reproduced; fixed by 59-02",
     "fixture": "test_cr01_edit_beside_the_second_copy_reasks"},
    ...
)
class TestRepro59Record(unittest.TestCase):
    def test_repro_59_record_is_complete(self):
        by_id = {r["id"]: r for r in REPRO_59}
        self.assertEqual(set(by_id), {...})
        for row in REPRO_59:
            ...
                self.assertEqual(set(row), {"id", "decision", "scenario",
                                            "probe_result", "disposition",
                                            "fixture"})
```
Candidate rows: 999.24 (context widening), deletion-rule-unreachable, PR `--patch` series, GSD/incremental mixed coordinates (reproduce or "did not reproduce; dropped"), `--all` "unsupported fixture", 999.25 BLOBFILE, FINALIZE_GATE_INPUT_JSON cross-call. If REPRO_60 lives in `test_diff_ranges.py` instead, keep the same shape and lock.

**Gate helper** (test_carry_state.py 3281-3288). Use `e2e_gate(state, head_blobs)` as-is; it is already imported at line 62.

---

### `scripts/test_finalize_card.py` (EXTEND: printed-path lock scope + Finalize fresh-shell walk)

**Analog 1, the prose lock to widen:** `check_printed_paths` (lines 511-528):
```python
MKTEMP_RE = re.compile(r"^\s*(?:if )?([A-Z_]+FILE)=\$\(mktemp", re.M)
PATH_CONVENTION = ("a path printed after `NAME=` is reused in a later fence "
                   "only as that literal, substituted for `\"$NAME\"`")

def check_printed_paths(text):
    section = card_section(text)          # <- scope is why 999.25 slipped (58 SA-01)
    problems = []
    for body in bash_fences(section):
        for name in MKTEMP_RE.findall(body):
            printf = "printf '%s=%%s\\n' \"$%s\"" % (name, name)
            if printf not in body:
                problems.append("%s created but its path is not printed" % name)
    count = section.count(PATH_CONVENTION)
    if count != 1:
        problems.append("path convention sentence appears %d times" % count)
    return problems
```
Extend: scan `bash_fences(text)` over the whole file (or the `## Finalize mode` section plus the card) for mktemp/print pairs. Add a check that every `"$NAME"` with `NAME` ending in `FILE`, read by a fence, is created (mktemp) by some fence in the file, so a bare `"$BLOBFILE"` without a creating fence trips. Keep the convention sentence count rule (it lives in the card section). Mutant style (lines 1218-1224):
```python
    def test_mutant_printed_paths(self):
        with self.subTest("mutant: RESOLVEFILE path not printed"):
            self.assert_trips(check_printed_paths, self._mutant(
                "printf 'RESOLVEFILE=%s\\n' \"$RESOLVEFILE\"\n"))
```
Add a `BLOBFILE` not-printed mutant and a "BLOBFILE mktemp fence removed" mutant.

**`ROWS_CALL` pin** (line 38): `'batch_card.py" rows --mode finalize --head-blobs "$BLOBFILE"'`. It stays valid if the fence keeps `"$BLOBFILE"` as the substitution placeholder (the Phase 58 convention: the fence text says `"$NAME"`, the orchestrator substitutes the printed literal). Do not change it to a literal path.

**Analog 2, the fresh-shell walk:** `test_fix_loop_card.py:2618-2760` `TestSubsetDispatchWalk`.

Fence extraction helpers (test_fix_loop_card.py 2449-2466):
```python
def _fence_after(text, anchor):
    """Body of the first ```bash fence after `anchor` (None if absent)."""
    if anchor not in text:
        return None
    start = text.find("```bash\n", text.index(anchor))
    if start < 0:
        return None
    start += len("```bash\n")
    return text[start:text.index("```", start)]

def _fence_holding(text, needle):
    """Body of the ```bash fence that holds `needle` (None if absent)."""
    if needle not in text:
        return None
    at = text.index(needle)
    start = text.rindex("```bash\n", 0, at) + len("```bash\n")
    return text[start:text.index("```", at)]
```
Note: the Finalize counts fence is indented (inside a list item); `bash_fences` in test_finalize_card.py (line 60-62) already handles indented closers (`\n[ \t]*```), but `_fence_after` returns the indented body. Dedent with `textwrap.dedent` before `bash -s`.

Printed-path capture + fresh shell + literal substitution (test_fix_loop_card.py 2621-2677):
```python
_PRINTED_RE = re.compile(r"^([A-Z_]+FILE)=(.+)$", re.M)
_FILE_REF_RE = re.compile(r'"\$([A-Z_]+FILE)"')

def _printed(stdout):
    return dict(_PRINTED_RE.findall(stdout))

    def _run_fresh(self, script):
        tmpdir = tempfile.mkdtemp(dir=self.tmp)
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
               "VC_ROOT": PLUGIN_DIR, "TMPDIR": tmpdir,
               "STATE_FILE": SIX_ROW_FIXTURE}
        proc = subprocess.run(["bash", "-s"], input=script, env=env,
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return _printed(proc.stdout)

    def _literal(self, fence, subs):
        for name, path in subs.items():
            ref = '"$%s"' % name
            self.assertIn(ref, fence, "fence does not read " + ref)
            fence = fence.replace(ref, '"%s"' % path)
            self.used.add(name)
        return fence
```
Walk for Finalize: [A] run the new BLOBFILE mktemp fence → capture `BLOBFILE`; simulate the Write tool by writing `{}` (or a validated blob map) to that path; [B] counts fence with `_literal(..., {"BLOBFILE": p})` → parse `COUNTS_JSON`; [C] gate fence with its input carried literally (`GATEFILE=` printed path, or inline JSON, whichever the plan picks; `_FILE_REF_RE` only catches `*FILE` names, so a `$FINALIZE_GATE_INPUT_JSON` read must be asserted absent separately); [D] rows fence with the same literal. Closure assertion copied from `test_subset_walk_needs_only_literal_paths` (2743-2760):
```python
        made = set()
        for fence in fences:
            made.update(MKTEMP_RE.findall(fence))
        read = set()
        for fence in fences:
            read.update(_FILE_REF_RE.findall(fence))
        self.assertEqual(read - made - {"STATE_FILE"}, set())
```
Mutants (D-09): (1) remove the BLOBFILE mktemp fence → walk fails / closure set non-empty; (2) run the counts fence WITHOUT literal substitution in a fresh shell → exit 2 from carry_state (`REASON_HEAD_BLOBS`, carry_state.py:200, 1452-1465). That is the 999.25 repro; (3) gate fence reading `"$FINALIZE_GATE_INPUT_JSON"` in a fresh shell → non-zero. Stale-literal pitfall (RESEARCH Pitfall 5): add a prose-phrase lock that the retry mints a new `BLOBFILE=` and a walk case where an earlier attempt's file holds an outdated blob.

State fixture: `SIX_ROW_FIXTURE` works for rows; for counts → gate `write`, use a state with no open findings or build one with `test_decision_continuity` helpers and write it to the temp dir.

---

### `scripts/test_nv_render.py` (UPDATE: retarget `DELETION_RANGE_PHRASES`)

**Analog:** same file, lines 199-213 and mutants 551-564:
```python
DELETION_RANGE_START = "**changed-line ranges**"
DELETION_RANGE_END = "\n   - **"

DELETION_RANGE_PHRASES = (
    "`[start, start + count - 1]`",
    "A hunk that only deletes",
    "header `+T,0`",
    "`[max(T, 1), T + 1]`",
    "either side of the deletion point",
)

def deletion_range_holds(text):
    return _all_in(_section(text, DELETION_RANGE_START, DELETION_RANGE_END),
                   DELETION_RANGE_PHRASES)
```
Mutant loop pattern to keep:
```python
        for phrase in DELETION_RANGE_PHRASES:
            with self.subTest(phrase=phrase):
                mutant = _delete(self.SYNTHETIC, phrase)
                self.assertNotEqual(mutant, self.SYNTHETIC)
                self.assertFalse(deletion_range_holds(mutant))
```
Retarget: drop `[start, start + count - 1]` (the deprecated header rule); add the helper-call phrase (e.g. `scripts/diff_ranges.py`), the net-deletion `+1` phrase (D-02), and the "never read the ranges from hunk headers" phrase. Keep `[max(T, 1), T + 1]` and `either side of the deletion point` as the documented contract (Pitfall 7). Also update `SYNTHETIC` in the test class if it embeds the old sentence. Every phrase stays covered by the delete-one mutant loop.

---

### `phases/shared/90-finalize.md` (MODIFY: BLOBFILE fence, literal reuse ×3, gate input literal, retry-once)

**Analog 1, mktemp + print, then fill with the Write tool:** same file, lines 138-146 (`SUGGESTFILE`):
````markdown
```bash
if SUGGESTFILE=$(mktemp "${TMPDIR:-/tmp}/vc.XXXXXX"); then
  printf 'SUGGESTFILE=%s\n' "$SUGGESTFILE"
else
  echo "no suggestion file — the card shows no Bottom line suggestion" >&2
fi
```

Write `{"q1": "<grammar>", "q2": null}` to `$SUGGESTFILE` with the Write tool, then ...
````
New step-1 fence: `if BLOBFILE=$(mktemp "${TMPDIR:-/tmp}/vc.XXXXXX"); then printf 'BLOBFILE=%s\n' "$BLOBFILE"; else echo "<plain no-write stop sentence>" >&2; exit 1; fi`. Then step 1's existing sentence "Serialize `{"<file>": "<blob>"}` to `$BLOBFILE` with the Write tool" points at the printed path. `test_mktemp_template.py` automatically enforces the `"${TMPDIR:-/tmp}/…XXXXXX"` template.

**Analog 2, fail-closed helper fence with the no-write message** (lines 15-22):
```bash
if COUNTS_JSON=$(python3 "$VC_ROOT/scripts/carry_state.py" finalize-counts --head-blobs "$BLOBFILE" < "$STATE_FILE"); then
  printf '%s\n' "$COUNTS_JSON"
else
  echo "I'm uncertain about Finalize mode — carry_state.py failed; nothing was written or archived." >&2
  exit 1
fi
```
Keep `"$BLOBFILE"` as the substitution placeholder in all three consumers (lines 16, 85, and the step-3 re-run at 249) and add one sentence at step 2 saying the printed literal is substituted (reuse the wording of line 95, "Temp paths are literals"; do not add a second copy of the exact `PATH_CONVENTION` sentence inside the card section, because `check_printed_paths` requires count == 1 there).

**Gate fence** (lines 36-43) currently reads a cross-call variable:
```bash
if FINALIZE_GATE_JSON=$(printf '%s' "$FINALIZE_GATE_INPUT_JSON" | python3 "$VC_ROOT/scripts/finalize_gate.py"); then
```
Follow the same mktemp-print-Write pattern (`GATEFILE=`, then `< "$GATEFILE"`). That keeps it under `MKTEMP_RE`/`_FILE_REF_RE` (both match `[A-Z_]+FILE`), so the existing lock machinery covers it with no new regex. Alternatively use an inline literal JSON. Either way, no `$FINALIZE_GATE_INPUT_JSON`.

**Retry-once / refused-step rule (D-07/D-08):** prose control flow placed after the counts and gate fences. Model the stop message on line 65's archive-stop sentence style (one plain sentence, says what was and wasn't written, says re-running `--finalize` is safe). The rule must say: a missing/empty path or a failed counts/gate step → rerun step 1 ONCE, creating a NEW file and printing a NEW `BLOBFILE=`; a refused (permission-denied) step → no retry, same stop sentence; second failure → stop. No REVIEW.md, archive or `record-decisions` call before the gate returns `write`.

**Do not touch:** the `write` branch (56-70), the archive fence, PATH_RE + `guard.py` validation in step 1, and `verified_blob == head_blob` semantics.

---

### `phases/review/30-collect-score.md` (MODIFY: line 64 "changed-line ranges" bullet)

**Analog:** the fail-closed helper fence shape from `90-finalize.md:15-22` (above) plus RESEARCH Pattern 2:
```bash
if RANGES_JSON=$(git diff --no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/ HEAD \
                 | python3 "$VC_ROOT/scripts/diff_ranges.py"); then
  printf '%s\n' "$RANGES_JSON"
else
  echo "Review halted — the changed lines could not be read from the diff; nothing was scored." >&2
  exit 1
fi
```
Pipe caveat: `set -o pipefail` is off by default. Either add it to the fence (fences run under `bash -s`) or write git output to a printed `DIFFFILE=` first. Replace the sentence "Build the ranges from each hunk's new-side header `+start,count` …" (the deprecated instruction); keep the deletion-rule and `_nearby_changed` / D-14 sentences that `test_nv_render.DELETION_RANGE_PHRASES` pins. The bullet must stay within `DELETION_RANGE_START`…`DELETION_RANGE_END` (`"\n   - **"`), so the fence or route table must not introduce a new `   - **` sub-bullet in between, or the section cut moves. Line 8 ("pure function — no git/file/shell I/O") stays true: prose runs git, the helper parses.

---

### `phases/review/00-scope.md` (MODIFY: per-route range source) and `phases/review/05-state.md` (step 3)

**Analog:** the files themselves. Current commands, 00-scope.md 38-55:
```bash
git diff HEAD
git diff --staged
git status --short
...
gh pr diff <ref> --patch
gh pr view <ref> --json title,body,author,headRefName
...
git diff <range>
```
05-state.md:85: `3. Narrow diff to incremental: \`$LAST_REVIEWED_SHA..HEAD\` + staged + unstaged.`

Pattern (RESEARCH Pattern 3): leave the agents' diff commands unchanged (reviewer changes are out of scope). ADD one named "range source" command per route that 30-collect-score feeds to the helper: default `git diff HEAD`; GSD `git diff $PHASE_START`; incremental `git diff $LAST_REVIEWED_SHA`; range `git diff <range>`; PR `gh pr diff <ref> --color never` (no `--patch`). All git calls carry `--no-color --no-ext-diff --src-prefix=a/ --dst-prefix=b/`. GSD/incremental/PR changes ship only if 60-REPRO.md records them as reproduced. Otherwise record "did not reproduce; dropped" and keep routing the existing diff through the helper. `test_scope_args.py` imports the real Phase 0 fence (see test_fix_loop_card.py:29). Run it after any 00-scope.md edit.

---

### `phases/review/05-state-all.md` / `00-scope-all.md` (record only)

No code change expected. D-06 explicit "unsupported fixture" record: `--all` forces pass 1 with an empty carry-forward on every run (`05-state-all.md` (ii)), so there is no diff, `changed_line_ranges = {}`, `in_diff` never gates and `nearby_at` is never stamped. Record it in REPRO_60 and in the route-coverage test as a named, asserted skip, not a silent omission.

---

### `.planning/phases/60-…/60-REPRO.md` (planning record)

**Analog:** `.planning/phases/59-stale-decisions-and-lost-deferrals/59-REPRO.md`. Header block (Phase, Date, HEAD when recorded, Scope of evidence ("no live or paid run"), Rule applied), the in-suite record pointer (`REPRO_60`, locked by `TestRepro60Record`), the full-suite line at the RED SHA, then one `## Vn — <id>` section per item with **Verdict**, **Failure as the owner would see it**, **Fixture**, **Command and output** (pytest `-k` block), and `Red at <sha>, green at <sha>`. Add the D-05 statement that the live `gh pr diff` fetch was not exercised.

## Shared Patterns

### Fail closed: helper exit code → plain no-write stop
**Source:** `phases/shared/90-finalize.md:15-22`, `scripts/carry_state.py:1463-1465` (`_refuse` writes the reason to stderr, returns 2)
**Apply to:** diff_ranges CLI, 30-collect-score range fence, every Finalize fence.
Exit 2 + fixed reason on stderr; prose branches on the exit code and prints one plain sentence that never includes stderr content or a traceback (user-global rule: no stack traces to end users). Note `finalize_gate.py` crashes with a `JSONDecodeError` traceback on empty stdin (line 238 deliberately does not catch it). Carrying the gate input literally removes that path. Change the gate itself only if the walk shows the traceback reaching the owner.

### Printed-path convention (Phase 58)
**Source:** `90-finalize.md:79-84, 95, 138-142`; locks `test_finalize_card.check_printed_paths` (511-528) and `test_fix_loop_card.MKTEMP_RE` (1910) / `TestSubsetDispatchWalk`.
**Apply to:** `BLOBFILE`, the gate input file, and any `DIFFFILE` the range fence introduces. Name every temp file `*FILE` so `MKTEMP_RE` and `_FILE_REF_RE` see it.

### Mutation-locked guards (no decorative locks)
**Source:** `test_finalize_card.py` header (lines 9-11: "applied to the real text (must return []) AND to a mutant … so no lock is decorative"), `assert_holds` / `assert_trips`, `_mutant(old, new)` (1207-1212) which asserts the needle exists and the mutant differs.
**Apply to:** every new check and every retargeted phrase lock. Mutants must first assert the fixture holds what the test assumes (memory: decorative-guard failure mode).

### Isolated real git
**Source:** `scripts/gitfixture.py` (`helper_env`, `git`, `make_repo`, `write`).
**Apply to:** all real-diff fixtures. Run them from pytest via `subprocess`, never ad-hoc shell chains (RESEARCH: the holdout hook blocks compound shell commands).

### Frozen invariants
`test_score.GOLDEN_DIGEST` (imported at test_decision_continuity.py:63) and `stable_hash` must not move; `_NEARBY_LINES = 5` (score.py:177) stays the one window constant; the envelope key `changed_line_ranges` keeps its shape.

## Conventions

Convention derivation skipped (`no-app-files`): the shared module found no JS/TS app files under `plugins/vibe-check/scripts` (the tree is Python + Markdown). Manual observation from the files read above, for the planner:

| Axis | Observed convention | Status |
|------|---------------------|--------|
| File-name casing | `snake_case.py`; tests `test_<module>.py` beside the module; non-test support modules not named `test_*` (gitfixture.py docstring) | named contract |
| Identifier casing | `snake_case` functions, `UPPER_SNAKE` module constants (`REASON_*`, `*_RE`, `*_PHRASES`), `_leading_underscore` privates | named contract |
| Export style | module-level functions + a `__main__` shim; documented import allowlist, AST-locked in tests | named contract |
| Import style | stdlib only; tests do `sys.path.insert(0, HERE)` then sibling imports with `# noqa: E402  (reason)` | named contract |

Contested hotspots (author's choice): none in this subtree. The repo-wide CJS<->SDK dual-resolver split (`bin/lib/**` CJS vs `sdk/src/**` ESM) is the prototype intentional-contested split, but this plugin is a separate Python tree; match the directory's local style.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (marker-walk core inside `diff_ranges.py`) | utility | transform | No in-repo diff-body parser exists; `replay.hunk_ranges` is header-only and must not be copied. Use RESEARCH.md lines 305-359 as the reference shape. |
| `scripts/fixtures/pr-cumulative.diff` | fixture | file-I/O | No checked-in diff capture exists; only JSON fixtures. Provenance goes in the test docstring + 60-REPRO.md. |

## Metadata

**Analog search scope:** `plugins/vibe-check/scripts/` (helpers, tests, fixtures), `plugins/vibe-check/phases/{shared,review}/`, `.planning/phases/59-*/`
**Files scanned:** ~20 (read targeted ranges of 90-finalize.md, 30-collect-score.md, 00-scope.md, 05-state.md, finalize_gate.py, count_cards.py, gitfixture.py, replay.py, carry_state.py, score.py, test_finalize_card.py, test_fix_loop_card.py, test_decision_continuity.py, test_nv_render.py, test_gitsnap.py, test_finalize_gate.py, test_mktemp_template.py, 59-REPRO.md)
**Pattern extraction date:** 2026-10-29
