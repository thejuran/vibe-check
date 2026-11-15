# Phase 63: Finalize extraction and cross-call variable check - Pattern Map

**Mapped:** 2026-11-14
**Files analyzed:** 16 (4 new code/test, 1 new design doc, 3 new phase-evidence records, 8 modified)
**Analogs found:** 16 / 16 (every file has an in-repo analog; two are "same file, earlier section")

All paths below are relative to `/Users/julianamacbook/turingmind-code-review`. Line numbers are from the tree at `ff786c0` (branch `feat/v2.15-phase-63`), where `plugins/vibe-check/phases/` is byte-identical to `dd8e4ab` (v2.14.1).

> **Superseded in one respect by D-18 (owner, 2026-11-14).** Where this map says to reuse the gate fence's `.err` convention for the new helper call ("Helper fence with diagnostics to `.err`", the `<BLOBFILE>.err` sentence, "the fence redirects stderr to `<BLOBFILE>.err`"), do not: the new fence does not redirect the helper's stderr, the helper writes only the 2.14.1 line on a counting-stage or report-stage refusal and nothing otherwise, and the `.err` sentence is not carried over. Plans 63-02 and 63-06 carry the exact contract.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `plugins/vibe-check/scripts/finalize_inputs.py` (NEW) | service + CLI helper | request-response (JSON out) + read-only git subprocess | `finalize_gate.py` (decide/run/CLI shim, fixed REASONS) + `carry_state.py` (hand-rolled argv, `_refuse`, `run()` → (code, out)) + `gitsnap.py` (`_git` runner) + `fixcommit.py` (PATH_RE + guard import) | exact (composite) |
| `plugins/vibe-check/scripts/test_finalize_inputs.py` (NEW) | test | unit + CLI subprocess + gitfixture | `test_gitsnap.py` (GitsnapCase, `cli`, `TestModuleShape`) + `test_finalize_gate.py::TestImportSet` + `test_finalize_card.py::LockCase` | exact |
| `plugins/vibe-check/scripts/test_cross_call_vars.py` (NEW) | test (static lint) | file-I/O, whole-tree scan | `test_mktemp_template.py` (walk + "scan found something" floor) + `step_count.py::_scan` (fence rule) + `test_finalize_card.py::check_printed_paths` / `LockCase` | exact |
| `plugins/vibe-check/phases/shared/90-finalize.md` (MOD) | instruction prose (config) | request-response (fence → helper → branch) | itself: lines 14-21 (mint+print fence), 57-63 (helper fence with `.err`), 67 (rebuild paragraph), 303-310 (decisions-report fence) | exact |
| `docs/design/lean-v2.15/finalize-counts-explained.md` (NEW, D-12) | design doc (not loaded) | static | `docs/design/state-single-writer-verify-v2.10.md` (header shape); body moved word for word from `90-finalize.md:34-39` | role-match |
| `docs/design/lean-v2.15/tools/finalize_capture.py` (MOD: `HelperWalk`, `compare`) | tool / driver | batch (situation walk) | same file: `FenceWalk2141` (709-785), `_Walk.counts_and_gate` (588-628), `DRIVERS` (791), `verify`/`_differences` (907-978), `_parse` (981-993) | exact |
| `docs/design/lean-v2.15/tools/test_finalize_capture.py` (MOD) | test | integration (pinned tree) | same file: `_PinnedTree` (44), `TestFailureRoutes` (475), `TestMutants` (950), `TestImportSet` (966) | exact |
| `plugins/vibe-check/scripts/test_finalize_card.py` (MOD) | test (prose locks + fresh-shell walk) | event (fresh `bash -s` per fence) | same file: `TestFinalizeFreshShellWalk` (1973-), helpers 1808-1970, `check_printed_paths` (531), `no_cross_call_gate_input` (580) | exact |
| `plugins/vibe-check/scripts/test_decision_continuity.py` (MOD: `REPRO_60` fixtures) | test (record) | static | same file: `REPRO_60` (4266-), rows `999.25-BLOBFILE`, `GATE-INPUT-CROSS-CALL`, `GATEFILE-RETRY` | exact |
| `test_carry_state.py`, `test_score.py`, `test_diff_ranges.py`, `test_confirmed_fix.py` (MOD, prose halves only) | test | static prose lookups | `test_finalize_card.py::_fence_holding` (1835) re-pointed at the new fence | role-match |
| `.github/scripts/test_stdlib_only.py` (MOD 33 → 34) | test (CI gate) | static | itself lines 81, 95 | exact |
| `docs/design/lean-v2.15/README.md` (MOD, tool table) | doc | static | itself lines 8-14 (locked by `tools/test_baseline_page.py`) | exact |
| Shared phase files fixed under D-08 (only if a repro is a real failure): `phases/review/00-scope.md`, `05-state.md`, `06-config.md` | instruction prose | request-response | `90-finalize.md:15-20` printed-path fence | exact |
| `.planning/phases/63-.../63-REPRO.md` (XVAR-02 flagged-site record) | phase evidence | static | `.planning/milestones/v2.14-phases/60-.../60-REPRO.md` V8/V9 (184-224) | exact |
| `.planning/phases/63-.../63-REMOVAL-LEDGER.md` (D-11) | phase evidence | static | 60-REPRO "Fixture / Green at" lines + RESEARCH "Removal Ledger Seed" table | role-match |
| `.planning/phases/63-.../63-RESULT.md` (D-14 owner page) | phase evidence | static | `docs/design/lean-v2.15/BASELINE-v2.14.1.md` (plain-terms baseline page) | role-match |

## Pattern Assignments

### `plugins/vibe-check/scripts/finalize_inputs.py` (service + CLI, request-response + git)

**Analogs:** `finalize_gate.py` (whole file, 244 lines), `carry_state.py` (CLI 1450-1575), `gitsnap.py` (105-128), `fixcommit.py` (90-103).

**Module docstring shape** — copy `finalize_gate.py:1-95`: what is transcribed and from where (here: `90-finalize.md:13-22` at `dd8e4ab`), the fail-closed rule, what the module does NOT do ("This module decides; the prose renders" `finalize_gate.py:72-75`), the exact import set, and the CLI usage + exit codes. `gitsnap.py:64-67` gives the git-module wording to reuse:
```python
I/O: stdlib only, imports exactly {argparse, hashlib, json, os, subprocess,
sys}; every `subprocess.run` is an argv list with `timeout=60`, never a shell.
Refusal reasons are fixed strings plus the git subcommand name; they never echo
repo content.
```

**Imports / sibling-import pattern** (`fixcommit.py:90-97`):
```python
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import guard  # noqa: E402  (the ONE containment source; never re-inlined here)
```
New module adds `import json, subprocess` and imports `carry_state`, `finalize_gate`, `batch_card`, `fixcommit` (for `PATH_RE` only — NOT `validate_paths`, which refuses leading `-`, stricter than 2.14.1; RESEARCH Anti-Patterns) the same way. Do not add git to `carry_state.py`/`finalize_gate.py` (their `TestImportSet` pins `{json, sys}` / `{json, os, sys}`).

**Fixed reason constants** (`carry_state.py:195-212`, `finalize_gate.py:111-127`) — one constant per refusal, newline-terminated for stderr, never echoing a path/hash/title:
```python
REASON_HEAD_BLOBS = "refused: head-blobs file is missing or not a JSON object\n"
...
REASONS = (
    REASON_STATE_JSON,
```

**git runner** (`gitsnap.py:109-124`) — list argv, timeout, catch `OSError`/`TimeoutExpired`. For this helper a failure means "omit the file" (fail closed), not raise:
```python
def _git(root, *args):
    try:
        return subprocess.run(
            ["git", "--no-optional-locks", *args], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SnapError("git %s could not run (%s)" % (args[0], type(exc).__name__))
```
Parity calls (exact, from `90-finalize.md:13`): `["git","rev-parse","HEAD:"+f]`, `["git","diff","--quiet","HEAD","--",f]`, `["git","diff","--cached","--quiet","--",f]`; include `f` only when all three exit 0; run `--show-toplevel` only if there is at least one candidate file (RESEARCH Pattern 1, sketch at RESEARCH 339-363). Whether to keep `--no-optional-locks` is assumption A5 — pin with a gitfixture parity test either way.

**Validation-before-git** (`fixcommit.py:117-127`, per-candidate loop):
```python
        if PATH_RE.match(path) is None:
            return False, ("refused: path fails the character pre-filter "
                           "(spaces and shell metacharacters are denied)")
        ok, _ = guard.contained(root, path)
        if not ok:
            return False, "refused: path fails containment under the repo root"
```
Here: on failure `continue` (omit), never refuse the whole call. `guard.contained` takes ONE string (fixcommit F4 note, `fixcommit.py:107-113`); `guard.contained("", f)` already refuses an empty root (`guard.py:54-55`).

**Reused library calls (in-process, never re-derived):**
- `carry_state.finalize_counts(state, head_blobs)` (`carry_state.py:1094-1128`) → dict of 8 keys or None (None → exit 3).
- `finalize_gate.run({"flags": {...}})` (`finalize_gate.py:224-228`) with exactly `finalize_gate.FLAGS` (`:140-142`); build bools as `bool`, counts as `int`.
- `batch_card.decisions_report(state)` (`batch_card.py:1465`) only when `action == "write"` (None → exit 5, no rebuild — RESEARCH Pitfall 3).
- `carry_state.read_json_file` / `load_json_text` (`carry_state.py:1486-1501`) for strict state parsing (NaN rejected).

**Hand-rolled argv parse, unknown flag = error, no defaults** (`carry_state.py:1450-1471`):
```python
def parse_argv(argv):
    """(subcommand, {flag: value}) or None on any usage error. Hand-rolled so an
    unknown flag is an error, never a silent default."""
    ...
        if token not in KNOWN_FLAGS or token not in required + optional:
            return None
        if i + 1 >= len(rest) or token in values:
            return None
    ...
    if any(f not in values for f in required):
        return None
```
All five switches (`--state-file`, `--blob-out`, `--noninteractive`, `--pr-mode`, `--range-mode`) required; booleans accept exactly `true`/`false` (mutant: defaulting `--noninteractive` must trip).

**CLI body returning (code, stdout) + shim** (`carry_state.py:1504-1575`):
```python
def _refuse(reason):
    sys.stderr.write(reason)
    return 2

def run(argv, stdin_text):
    """CLI body. Returns (exit code, stdout text)."""
    parsed = parse_argv(argv)
    if parsed is None:
        return _refuse(USAGE), ""
...
    return 0, json.dumps(result, allow_nan=False)

if __name__ == "__main__":
    ...
    code, out = run(sys.argv[1:], stdin_text)
    if out:
        sys.stdout.write(out)
    sys.exit(code)
```
Exit-code map is RESEARCH Pattern 2 (0 / 2 usage or bad blob-out / 3 state / 4 gate stage / 5 report). Output keys `{action, reason, next, counts, report}`; expose `NEXT_ACTIONS` as a module tuple (like `finalize_gate.ACTIONS`, `:102-109`) so the prose lock can compare against it.

---

### `plugins/vibe-check/scripts/test_finalize_inputs.py` (test)

**Analog:** `test_gitsnap.py` (1-84, 493-520, 594-631); `test_finalize_gate.py::TestImportSet` (516-541); `test_finalize_card.py::LockCase` (909-914).

**Imports + base case with a real repo** (`test_gitsnap.py:11-45`):
```python
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import gitsnap  # noqa: E402  (module under test)
import gitfixture  # noqa: E402  (shared temp-repo helper)
from gitfixture import git, write  # noqa: E402

class GitsnapCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self.repo = gitfixture.make_repo(self.tmp)
        write(self.repo, "f.txt", "one\n")
        git(self.repo, "add", "--", "f.txt")
        git(self.repo, "commit", "-q", "-m", "init")
```

**CLI as subprocess with isolated git config** (`test_gitsnap.py:49-55`):
```python
    def cli(self, *args, root=None):
        proc = subprocess.run(
            [sys.executable, GITSNAP, *args], cwd=self.tmp,
            env=gitfixture.helper_env(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=120)
```
For this helper set `cwd=self.repo` (git runs from the process cwd) and a non-git dir for the "no candidates → no git" case.

**In-process run with env patched** (`test_gitsnap.py:66-71`) — use for mutants that patch a function (e.g. drop the `--cached` check, drop PATH_RE, drop guard) with `mock.patch.object(finalize_inputs, name, ...)`; mutant shape `test_gitsnap.py:493-511` (assert real behaviour first, then patched behaviour differs).

**Module shape locks** (`test_gitsnap.py:594-628`) — exact import set, and every `subprocess.run` has `timeout` and no `shell`:
```python
    def test_every_subprocess_run_has_timeout_and_no_shell(self):
        calls = [n for n in ast.walk(self.tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "run"
                 and getattr(n.func.value, "id", None) == "subprocess"]
        self.assertTrue(calls)
        for call in calls:
            kws = {k.arg for k in call.keywords}
            self.assertIn("timeout", kws)
            self.assertNotIn("shell", kws)
```

**Fixtures to reuse for parity:** `fixtures/iplayarr45-six-row-state.json` (`SIX_ROW_FIXTURE`, `test_finalize_card.py:1808`), `fixtures/phase45-loop-state.json`, and `from test_carry_state import ARCH_FILE, ARCH_HASH, load_fixture, obsolete_verdict` (as `test_finalize_card.py:40-41`). Parity assertion: helper result's `counts` == `carry_state.finalize_counts(state, blobs)` and `{action, reason}` == `finalize_gate.run(...)` on the same inputs.

**Prose lock with mutant** (`LockCase`, `test_finalize_card.py:909-914`): the prose's `next` branch list == `finalize_inputs.NEXT_ACTIONS`; mutant removes one branch → trips.

---

### `plugins/vibe-check/scripts/test_cross_call_vars.py` (static lint, whole-tree)

**Analogs:** `test_mktemp_template.py` (whole file, 69 lines); `docs/design/lean-v2.15/tools/step_count.py:83-131`; `test_finalize_card.py:528-546, 909-914`.

**Walk + per-file subTest + "found something" floor** (`test_mktemp_template.py:13, 32-52`):
```python
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
...
def plugin_text_files():
    for sub in SCANNED_DIRS:
        base = os.path.join(PLUGIN_ROOT, sub)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
...
            with self.subTest(file=os.path.relpath(path, PLUGIN_ROOT)):
                self.assertEqual(mktemp_problems(text), [])
        # the fences that need temp files exist (guards a scan that finds nothing)
        self.assertGreaterEqual(seen, 10)
```
Scope here is `phases/` only (D-10), `.md` files; assert exactly 27 files (mutant (i)).

**Fence rule — copy, do not re-invent** (`step_count.py:83-85, 104-127`): indented fences, 3 or 4 backticks, closed by the same tick count, other-language fences skipped:
```python
FENCE_OPEN = re.compile(r"^[ \t]*`{3,4}bash$")
_ANY_FENCE_OPEN = re.compile(r"^[ \t]*(`{3,})[^`]*$")
...
        if is_bash or _ANY_FENCE_OPEN.match(line):
            n = _ticks(line)
            close = re.compile(r"^[ \t]*`{%d}$" % n)
```
(Shipped tests can't import `docs/design/...` tools cleanly; transcribe `_scan` and add a lock test that both give the same fence count on `90-finalize.md` — 18 at baseline.) Note `test_finalize_card.bash_fences` (`:75-77`) is a weaker regex (3 ticks only) — don't reuse it for this check.

**Printed-name recognition** (`test_finalize_card.py:1844-1845`, `step_count.py:86`) — extend to any NAME and to multi-name bootstrap formats (`VC_ROOT=%s\nGUARD_PY=%s…`) and `echo "NAME=$NAME"`:
```python
def _print_line(name):
    return "printf '%s=%%s\\n' \"$%s\"" % (name, name)
```

**Check-function + mutant discipline** (`test_finalize_card.py:531-546`, `909-914`): each `check_*` returns a list of problems; `assert_holds(real)` and `assert_trips(mutant)`; mutants (a)-(i) from RESEARCH Pattern 4, each as a subTest. Mutant (c) removes `printf 'BLOBFILE=%s\n' "$BLOBFILE"` from the real `90-finalize.md` text using `remove()` (`test_finalize_card.py:103-105`, asserts the needle was present so the mutant is real).

**Exceptions set:** literal `frozenset({("phases/review/05-state.md", "STATE_FILE"), ...})`, `assertEqual(current_flags, EXCEPTIONS)` (new flag and stale entry both fail). Each entry should carry a repro id that exists in `63-REPRO.md` (XVAR-02 record test).

---

### `plugins/vibe-check/phases/shared/90-finalize.md` (modified prose)

**Analog:** the same file's own fences — keep their exact forms.

**Mint + print fence** (lines 15-20) — keep verbatim at the top of the new single fence (so `step_count`'s `_PRINT_RE` still counts the rows-fence paste and the card reads the literal):
```bash
if BLOBFILE=$(mktemp "${TMPDIR:-/tmp}/vc.XXXXXX"); then
  printf 'BLOBFILE=%s\n' "$BLOBFILE"
else
  echo 'Finalize stopped — nothing was written or archived; run `--finalize` again.' >&2
  exit 1
fi
```

**Helper fence with diagnostics to `.err`** (lines 57-64):
```bash
if FINALIZE_GATE_JSON=$(python3 "$VC_ROOT/scripts/finalize_gate.py" < "$GATEFILE" 2>"$GATEFILE.err"); then
  printf '%s\n' "$FINALIZE_GATE_JSON"       # {"action": ..., "reason": ...}
else
  echo "I'm uncertain about Finalize mode — finalize_gate.py failed; nothing was written or archived." >&2
  exit 1
fi
```
+ sentence at line 64: "The helper's own diagnostics are kept in `<GATEFILE>.err` and are not shown; the owner reads only the fence's sentence." → reuse as `<BLOBFILE>.err`. Exit-code `case $?` mapping per RESEARCH Code Examples (bash 3.2 only). The three stop sentences must be copied byte for byte from lines 28, 60 and 307.

**Rebuild paragraph** (line 67) — rewrite in the same one-line paragraph form under the same `**One automatic rebuild, then stop (D-07/D-08).**` heading (`RETRY_HEAD`, `test_finalize_card.py:1864`), keep `The stop is exactly one sentence: "…"` (regex in `finalize_capture.py:489`, Pitfall 6), keep `No REVIEW.md is written and no archive move is made before the gate returns \`write\`.` (`WRITE_BOUNDARY`, `:1882`), and add "exit 5 stops at once, no rebuild".

**Step 3 after the answer** (line 272) — keep the shape, re-point "run step 1 again … RE-RUN the counts … NEW `GATEFILE=`" to "run the Finalize-inputs fence again (a NEW `BLOBFILE=`)".

**Kept untouched:** the card (from `### The finalize card`), `record-decisions` fence, the archive fences (85-90, 330-352), owner messages at 68-78 and 94. The decisions-report fence (303-310) goes away only if D-02 folds the report into the helper result; the sentence at 322 "Use the `$COUNTS_JSON` from the gate step" is re-pointed to the result's `counts`.

**Moved out (D-12):** lines 34-39 ("What the helper counts" through "…or an owner decision.") go word for word into the design doc.

---

### `docs/design/lean-v2.15/finalize-counts-explained.md` (new design doc, D-12)

**Analog:** `docs/design/state-single-writer-verify-v2.10.md:1-12` — H1 title with version/phase, a bold one-line outcome, a provenance paragraph naming the commit the text comes from:
```markdown
# State single-writer verify (v2.10 Phase 40, DIET-03)

**Outcome: dissolved.** On the restructured flow, one sentence writes `state.passes`: ...

This record follows the evidence → method → outcome shape ... They were re-run on the shipped tree for this record (2026-09-28,
commit `f5f514b`; the plugin prose last changed at `d05ecb6`).
```
Body = `90-finalize.md:34-39` verbatim (state "moved word for word from `dd8e4ab`"). Add a lock that the passage in the doc equals the `dd8e4ab` bytes (via `git show`, like `test_finalize_capture._git_show_bytes`, `test_finalize_capture.py:39-41`), and re-point the moved needles of `check_phase57_decisions` (`test_finalize_card.py:170`) at this doc. The file is not in `footprint.py` `MODE_PATHS["finalize"]` and must not be referenced by a `Read` instruction in loaded prose.

---

### `docs/design/lean-v2.15/tools/finalize_capture.py` (modified: `HelperWalk` + `compare`)

**Analog:** same file.

**Driver class shape** (`FenceWalk2141`, lines 709-785) — `NAME`, `REBUILDS = 1`, `run(situation_id, vc_root, workdir, leg=None)` returning `walk.outputs()`, `gated()` loop, route aliases:
```python
class FenceWalk2141:
    NAME = "fence-walk-2.14.1"
    REBUILDS = 1
    ...
    def gated(self, walk, inputs):
        faults = inputs.get("attempt_faults", [])
        for attempt in range(self.REBUILDS + 1):
            fault = faults[attempt] if attempt < len(faults) else None
            blob, decision = walk.counts_and_gate(inputs, fault)
            if decision is not None:
                return blob, decision
        walk.stop(stop_sentence(walk.finalize_text))
        return None, None
    ...
    _clean_close = _write_route
    _one_rebuild = _write_route
    _refused_close = _write_route
    _card_first = _card_route
    _fresh_shell_restart = _card_route
```
`HelperWalk(FenceWalk2141)` overrides only the attempt step (a `_Walk` subclass method replacing `counts_and_gate`, lines 588-628) and the fault injections (RESEARCH Pattern 3 table), plus `fresh-shell-restart` git-init prep. Reuse `_Walk.step`/`ok`/`mint`/`fence` (546-583) so the steps/tally are recorded the same way.

**Fence lookup by needle** (`COUNTS_CALL` etc., 474-482; `_Walk.fence`, 546-550) — add a `FINALIZE_INPUTS_CALL = 'finalize_inputs.py" --state-file "$STATE_FILE" --blob-out "$BLOBFILE"'` needle; do NOT edit the existing needles (they must keep matching the pinned `dd8e4ab` tree).

**Do not touch:** `SITUATIONS` (134-241), `OUTPUT_KEYS` (104), `NORMALISATION` (88), `DRIVERS = {BASELINE_COMMIT: FenceWalk2141}` (791) — so `verify --record baseline/finalize-situations-v2.14.1.json` still prints `finalize baseline matches (5 situations)`.

**compare** — reuse `_differences(want, got, path)` (907-928) and the `verify` problem-line format (931-978), filtered to the outcome fields `gate, stop_sentence, report, files_written, files_archived, state_closed`; list `steps`/`tally` differences separately as the named intended difference (D-15). CLI: add a subparser beside `capture`/`verify` in `_parse` (981-993) and a `_compare_cmd` in the `_verify_cmd` style (1013-1021); exit codes 0/1/2 as the module docstring states (57-60).

---

### `docs/design/lean-v2.15/tools/test_finalize_capture.py` (modified)

**Analog:** same file — `_PinnedTree` (44-62, materializes `BASELINE_COMMIT` once per class), `TestFailureRoutes` (475-683), `TestMutants` (950), `TestImportSet` (966). Header rule (1-5): "each mutant asserts the mutation really happened". New `TestHelperWalk(_PinnedTree)`-style class materializes the candidate commit instead (HEAD of branch via `fc.materialize(REPO, <sha>, tmp)`), and the supplementary 2.14.1 run of the two new injections stays separate from the pinned record.

---

### `plugins/vibe-check/scripts/test_finalize_card.py` (modified: fresh-shell walk + locks)

**Analog:** same file.

**Fresh-shell runner** (lines 1996-2005) — keep as is; it is the FINX-03 proof harness:
```python
    def _run_fresh(self, script, state_file=SIX_ROW_FIXTURE):
        tmpdir = tempfile.mkdtemp(dir=self.tmp)
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
               "VC_ROOT": PLUGIN_DIR, "TMPDIR": tmpdir,
               "STATE_FILE": state_file}
        proc = subprocess.run(["bash", "-s"], input=textwrap.dedent(script),
                              env=env, cwd=tmpdir, capture_output=True,
                              text=True, timeout=60)
```
Literal substitution `_literal` (2007-2015) and `_mint` (2024-2032) also stay. Replace `_counts` (2044-2052) / `_flags` (2054-) with one `_inputs()` that walks the new fence and parses its JSON stdout.

**Locks to rewrite, keeping mutants:** `RETRY_NEEDLES` (1865-1877), `STEP3_NEEDLES` (1933-1943), `retry_rule_holds` (1898), `step3_rerun_rule_holds` (1953). `no_cross_call_gate_input` (580-588) → "no longer applies" in the ledger, replaced by XVAR mutant (d). `check_printed_paths` (531-546) and `check_file_refs_created` (559-577) stay (card unchanged; the new fence still prints `BLOBFILE=`).

---

### `plugins/vibe-check/scripts/test_decision_continuity.py` (modified: `REPRO_60`)

**Analog:** same file, rows at 4266-4400. Row shape:
```python
    {"id": "999.24-WIDEN", "decision": "EVID-01",
     "scenario": "...",
     "probe_result": "...",
     "disposition": "reproduced; fixed by 60-02 + 60-04",
     "fixture": "TestRepro60Evidence + TestRealDiffRanges60"},
```
For rows `999.25-BLOBFILE`, `GATE-INPUT-CROSS-CALL`, `GATEFILE-RETRY`, `STALE-GATEFILE-RERUN`, `STALE-BLOBFILE-RECOUNT`, `FINALIZE-HEAD-SHA-WEDGE`: keep `id`/`scenario`/`probe_result`, rewrite only `fixture` to the replacement test names (" + "-joined). `TestRepro60Record.test_every_fixture_exists` enforces that every named fixture exists. Each change is a ledger line.

---

### Other prose-half tests (`test_carry_state.py`, `test_score.py`, `test_diff_ranges.py`, `test_confirmed_fix.py`)

**Analog:** `test_finalize_card._fence_holding(text, needle)` (1835-1841). Re-point needle constants (e.g. `COUNTS_CALL` in `test_diff_ranges.py`; the `if COUNTS_JSON=$(python3 … finalize-counts` lookup in `test_score.py::test_old_reader_refuses_open_nv_state`) at the new `finalize_inputs.py` call, or replace the prose half with a direct library assertion. `test_carry_state.py::test_fix_obsolete_unbound_when_working_tree_dirty` prose half (asserts `git diff --quiet HEAD --` / `git diff --cached --quiet --` in `90-finalize.md`) moves to a gitfixture parity test in `test_finalize_inputs.py` with a mutant per dropped check. Run the suite against a scratch copy with the section removed first to get the full red list (Pitfall 2).

---

### `.github/scripts/test_stdlib_only.py` (modified)

**Analog:** itself, `TestRealTree` (72-95):
```python
        self.assertEqual(expected, 33)
...
        self.assertEqual(proc.stdout.strip(), "33 shipped .py files; third-party imports: none")
```
Change both literals to 34 (one ledger entry: "count updated; stdlib rule unchanged"); confirm `python3 -I .github/scripts/stdlib_only.py plugins/vibe-check` prints the 34 line. Test files (`test_*`) are not counted, so `test_finalize_inputs.py` / `test_cross_call_vars.py` don't move it.

---

### `docs/design/lean-v2.15/README.md` (modified)

**Analog:** tool table lines 8-14:
```markdown
| `finalize_capture.py` | walks the five Finalize situations offline at the pinned commit and records what they produce (`capture`), or compares a fresh walk with the committed record (`verify --repo <root> --record <json>`) |
```
Extend that row with the new `compare` subcommand / `--driver helper` wording (no new tool file → no new row). `tools/test_baseline_page.py` checks this table — run it after the edit.

---

### Shared phase files (`phases/review/00-scope.md`, `05-state.md`, `06-config.md`) — only on a reproduced failure (D-08/D-09)

**Analog:** the printed-path fence (`90-finalize.md:15-20`) and its prose sentence (`90-finalize.md:32`): "`"$BLOBFILE"` here is the literal path printed after `BLOBFILE=` by this attempt's step 1 — substitute it; a shell variable does not survive into a separate Bash call." Prefer merging fences or substituting an already-printed literal over adding a new `printf` (Pitfall 8: names ending in `FILE` add counted paste steps). Each fix: file, byte delta, repro id recorded for Phase 65.

---

### `.planning/phases/63-.../63-REPRO.md` (XVAR-02 record)

**Analog:** `60-REPRO.md` V8 (184-203). Per flagged pair, one `## Xn — <FILE>:<NAME>` section with:
```markdown
**Verdict: REPRODUCED at `<sha>` -> to be fixed by 63-0N.**   (or: did not reproduce -> pinned in EXCEPTIONS)

**Failure as the owner would see it.** <plain sentence>

**Fixture.** <test name(s)>

**Command and output:**
```
$ <fresh `bash -s` command with only PATH/VC_ROOT/TMPDIR/STATE_FILE>
<output>
```

Green at: <sha> (...)
```
State the repro standard up front (RESEARCH Pitfall 9) before the per-site sections.

### `.planning/phases/63-.../63-REMOVAL-LEDGER.md` (D-11)

**Analog:** RESEARCH "Removal Ledger Seed" table (lines 388-403) — columns: removed passage/test, rule it protected, replacement test, mutant that trips it (or "no longer applies" + reason), commit where the replacement landed (must precede the removal commit).

### `.planning/phases/63-.../63-RESULT.md` (D-14 owner page)

**Analog:** `docs/design/lean-v2.15/BASELINE-v2.14.1.md` (plain-terms page for the same owner). Pass/fail and numbers first; sections in D-14 order: two counts before/after (and, per Open Question 1, extraction-only vs phase-end), maintenance added, five situations with each named difference (fault mappings, `fresh-shell-restart` real-git prep, R15 stderr now in `.err`), ledger summary, flagged files fixed vs pinned, D-06 gaps.

## Shared Patterns

### Fail closed with fixed reasons (no path/hash/title echoed)
**Source:** `carry_state.py:108-112` + `195-212`, `guard.py:39-42`, `finalize_gate.py:82-84`
**Apply to:** `finalize_inputs.py`
Every refusal is a module constant written to stderr; stdout stays empty on refusal; the CLI never prints a traceback to the owner (the fence redirects stderr to `<BLOBFILE>.err`). Untrusted finding `file` values never reach argv before `PATH_RE` + `guard.contained`, and always after `--`.

### "This module decides; the prose renders"
**Source:** `finalize_gate.py:72-75`
**Apply to:** `finalize_inputs.py`, `90-finalize.md`
The helper returns codes and JSON; every owner sentence lives in the fence/prose, byte-identical to 2.14.1 (D-05).

### Printed-path rule across Bash calls
**Source:** `90-finalize.md:15-20, 32`; lock `test_finalize_card.py:531-546`
**Apply to:** new Finalize fence, any D-08 fix, `test_cross_call_vars.py` (the general form)

### Every lock has a mutant
**Source:** `test_finalize_card.py:17-19` docstring + `LockCase` (909-914); `test_gitsnap.py:493-511` (assert real signal first, then patched blindness); `test_finalize_capture.py:1-5`
**Apply to:** all new and rewritten tests

### Import-set pin per module
**Source:** `test_finalize_gate.py:516-541` (`TestImportSet`, subset of `ALLOWED`) and `test_gitsnap.py:600-610` (exact set)
**Apply to:** `test_finalize_inputs.py` (exact set: `{json, os, re?, subprocess, sys}` + sibling modules), `test_cross_call_vars.py` if it holds shared helpers

### Real git in tests
**Source:** `gitfixture.py` (`make_repo`, `git`, `write`, `helper_env`)
**Apply to:** `test_finalize_inputs.py`, `HelperWalk` `fresh-shell-restart` prep. No test-only `--head-blobs` override on the shipped helper (RESEARCH Anti-Patterns).

### Shell inside tests and tooling
Fresh `bash -s` per fence with only PATH/VC_ROOT/TMPDIR/STATE_FILE (`test_finalize_card.py:1996-2005`, `finalize_capture.run_fence` 375-391). Fences must stay bash 3.2-compatible (macOS).

## Conventions

Convention derivation skipped (`no-app-files`: the deterministic module does not classify the Python/Markdown tree under `plugins/vibe-check/scripts`). Observed directly from the analogs instead:

| Axis | Dominant | Status |
|---|---|---|
| File-name casing | `snake_case.py`, tests `test_<module>.py` flat beside the module | named contract |
| Identifier casing | `snake_case` functions, `UPPER_SNAKE` constants (`REASON_*`, `*_CALL` needles), `CamelCase` test classes | named contract |
| Export style | module-level functions + constants; CLI only under `if __name__ == "__main__":` | named contract |
| Import style | stdlib `import x` lines, then `sys.path.insert(0, <scripts dir>)` and sibling imports with `# noqa: E402  (<why>)` | named contract |

**Contested hotspots (author's choice):** the repo's CJS<->SDK dual-resolver split does not apply here (no `bin/lib` / `sdk/src` in this plugin). The local split that does apply: shipped `scripts/*.py` are stdlib-only with pinned import sets, while `docs/design/lean-v2.15/tools/*.py` may use broader stdlib (`argparse`, `getpass`, `tempfile`) and never import the plugin in-process (`finalize_capture.py:23-28`). Match the directory you are editing.

## No Analog Found

None. The closest thing to new ground is the `HelperWalk` fault mapping (RESEARCH Pattern 3), which has a driver analog but no precedent for mapping a 2.14.1 fault onto a different injection point; the planner should take that design from RESEARCH and plan for the supplementary 2.14.1 run.

## Metadata

**Analog search scope:** `plugins/vibe-check/scripts/`, `plugins/vibe-check/phases/shared/`, `docs/design/`, `docs/design/lean-v2.15/tools/`, `.github/scripts/`, `.planning/milestones/v2.14-phases/60-*/`
**Files scanned:** 19 read or partly read (finalize_gate, carry_state, fixcommit, guard, gitsnap, gitfixture, test_mktemp_template, test_finalize_card, test_finalize_gate, test_gitsnap, test_decision_continuity, finalize_capture, test_finalize_capture, step_count, test_stdlib_only, README, 90-finalize.md, 60-REPRO.md, state-single-writer-verify-v2.10.md)
**Pattern extraction date:** 2026-11-14
