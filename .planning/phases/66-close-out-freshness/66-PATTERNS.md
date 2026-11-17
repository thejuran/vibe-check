# Phase 66: Close out freshness - Pattern Map

**Mapped:** 2026-11-17
**Files analyzed:** 14 (3 new, 11 modified)
**Analogs found:** 14 / 14 (all paths below are relative to `plugins/vibe-check/` unless they start with `docs/` or `.planning/`)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/closeout_fresh.py` (NEW) | utility (pure decide + thin git layer) | transform (reverse diff -> ranges -> stale list), file-I/O read-only | `scripts/worktree_snap.py` (`_git`, `_store_env`, `_treeish`, `since`) + `scripts/finalize_inputs.py` (`_git`, `head_blobs` never-raise wrapper) | exact (same diff->`diff_ranges` pipeline, same store) |
| `scripts/finalize_inputs.py` (EDIT) | controller (CLI gate inputs) | request-response | itself: `_run` 428-458, `NEXT_ACTIONS` 147-149, `next_action` 290-305 | exact |
| `scripts/test_closeout_fresh.py` (NEW) | test (unit + real-chain + mutation + differential) | batch | `scripts/test_finalize_inputs.py` (InputsCase/CliCase/mutant) + `scripts/test_worktree_snap.py` (`_Chain`) + `scripts/test_decision_continuity.py` (`pass1`, `base_file`) | exact |
| v2.15 materializer helper (NEW, inside `test_closeout_fresh.py` or a non-`test_` sibling like `gitfixture.py`) | test utility | file-I/O (`git show <commit>:<path>` -> temp dir -> import) | `scripts/test_finalize_parity_grid.py` `source_text()` 121-132 + `docs/design/lean-v2.15/tools/path_records.py` `git_bytes`/`baseline_mode_paths` 103-128 + `scripts/replay.py` `load_scorer` 412-455 | role-match (precedents load ONE file/module; this loads a sibling set) |
| `scripts/test_finalize_inputs.py` (EDIT) | test | batch | itself: `TestNextAction` 766-815, `TestCliWritesOnlyTheFingerprintFile` 2038+, `ResultCase.prepared` 752-763 | exact |
| `scripts/test_finalize_parity_grid.py` (EDIT, only if grid states need a `reviewed_tree`) | test (two-sided differential) | batch | itself: `TestStep1ScriptIsPinned` 148-207 | exact |
| `scripts/test_finalize_card.py` (EDIT) | test (prose lock) | transform | itself: `nv_fallback_listing_holds` 1859-1866 + `TestNeedsVerificationFinalizeProse` 1912-1940, `LockCase` 963-969 | exact |
| `scripts/test_decision_continuity.py` (EDIT: shape 1 / shape 2 fixtures) | test | batch | itself: `far_twin_scenario` 966-990, `test_p4_far_twin_new_copy_is_not_evidence` 1726-1749, `_RealChain` 3921-3947 | exact |
| `scripts/test_worktree_snap.py` (EDIT: `--all` now takes/collects) | test (prose lock) | transform | itself: `TestProse.test_every_snapshot_call_states_the_finalize_and_all_skip` 1074-1085 | exact |
| `phases/shared/90-finalize.md` (EDIT: new `next` bullet) | config/prose | request-response | itself: `stop-fallback-nv` bullet 45-48, `stop-refused` 66, branch rule 36, retry rule 38 | exact |
| `phases/review/00-scope-all.md` (EDIT: take on `--all`) | config/prose | event-driven (Phase 0 fence) | `phases/review/00-scope.md` mode-1 take fence 37-42 | exact |
| `phases/review/30-collect-score.md` (EDIT: collect on `--all`, still no `nearby_line_ranges` to scorer) | config/prose | event-driven | itself: lines 90-108 (collect fences) and 122 (envelope `nearby_line_ranges`) | exact |
| `phases/review/45-persist.md` + `45-persist-all.md` (EDIT: drop "except --all") | config/prose | CRUD (state write) | `45-persist.md` lines 8, 21, 39 | exact |
| `scripts/fixtures/future-schema.json` (EDIT: `_purpose` note only) | config (schema) | — | itself line 2 (`_purpose` history), 9 (`pass_optional` already holds `reviewed_tree`), 41 (`_rollback.fix999_28_added`) | exact |

Not touched (pinned byte-identical to dd8e4ab by the parity grid): `scripts/carry_state.py`, `scripts/finalize_gate.py`, `scripts/guard.py`, `scripts/fixcommit.py`. If 999.44 shape 2 requires a `carry_state.py` edit, the parity grid must first be changed to materialize those four via `git show dd8e4ab:...` (see the materializer section).

---

## Pattern Assignments

### `scripts/closeout_fresh.py` (NEW — utility, transform)

**Analog A:** `scripts/worktree_snap.py` (the git layer, store env, diff->ranges)
**Analog B:** `scripts/finalize_inputs.py` (module docstring style, never-raise public entry, constants)

**Module docstring convention** — every helper opens with a long contract docstring: purpose, CLI/usage, exit codes, what it never prints, and an explicit "I/O: stdlib imports exactly {...}" line. Copy the shape of `finalize_inputs.py` lines 113-122:
```python
WHAT IT DOES NOT DO. It prints no owner sentence and renders nothing: this
module decides, the prose renders.

I/O: stdlib imports exactly {io, json, os, subprocess, sys}, plus the
siblings `batch_card`, `carry_state` and `finalize_gate` (called in-process),
`guard` (the containment command, `main`) and `fixcommit` (the PATH_RE constant only; never
validate_paths). Every `subprocess.run` is an argv list with
`timeout=GIT_TIMEOUT` and no shell. git's stderr is captured and discarded,
never returned or printed.
```

**Imports pattern** (`finalize_inputs.py` 124-136 — sibling imports after a `sys.path.insert`, each with a `# noqa: E402 (why)` comment):
```python
import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_card  # noqa: E402  (the report data, decisions_report)
import carry_state  # noqa: E402  (the counts, finalize_counts)
import finalize_gate  # noqa: E402  (the gate decision)
import guard  # noqa: E402  (the ONE containment source, as a command)
from fixcommit import PATH_RE  # noqa: E402  (pre-filter constant only)
```
For the new module: `carry_state` (open_findings / decision_state / covering_decision / _fix_closes, read-only), `diff_ranges` (ranges_from_diff, RangeError), `worktree_snap` (OBJECT_ID_RE, STORE_REL, `_git_path`), `fixcommit.PATH_RE`. Do NOT import `score` (3,281 lines) — mirror the window constant (see Shared Patterns "Mirrored constant + lock test").

**Git runner pattern** (`worktree_snap.py` 117-129 — the `--no-optional-locks -c core.fsmonitor=false` prefix is what keeps Close out from refreshing the index; Pitfall 5):
```python
def _git(root, args, env=None, stdin=None):
    try:
        proc = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", *args],
            cwd=root, env=env, input=stdin, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SnapUnavailable("git %s could not run (%s)"
                              % (args[0], type(exc).__name__))
    if proc.returncode != 0:
        raise SnapUnavailable("git %s failed (exit %d)"
                              % (args[0], proc.returncode))
    return proc.stdout.decode("utf-8", "replace")
```
Use a module-local exception (e.g. `Unverifiable`) the same way `SnapUnavailable` is used: every git/parse failure raises it, and the caller maps it to "every decided record stale, cause unverifiable" (fail closed — the opposite direction of worktree_snap, which fails toward asking).

**Store env pattern — needs a READ-ONLY twin** (`worktree_snap.py` 139-156). The existing one `makedirs` the store when `write_to is None`, which Close out must not do:
```python
def _store_env(root, write_to=None):
    store = os.path.join(root, STORE_REL, "objects")
    alternates = [os.path.abspath(_git_path(root, "objects"))]
    if write_to is None:
        os.makedirs(store, exist_ok=True)      # <-- Close out must NOT do this
        write_to = store
    elif os.path.isdir(store):
        alternates.append(store)
    env = dict(os.environ)
    for k in ("GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
              "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(k, None)
    env["GIT_OBJECT_DIRECTORY"] = write_to
    env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = os.pathsep.join(alternates)
    return env
```
Read-only variant: keep the env scrubbing (lines 151-153) verbatim; leave `GIT_OBJECT_DIRECTORY` as the repo's own objects dir; add the store as an alternate only `if os.path.isdir(store)`. A missing store plus a tree id that is not a commit -> `cat-file` fails -> unverifiable.

**Object-id validation before git** (`worktree_snap.py` 98 + 216-220):
```python
OBJECT_ID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")

def _treeish(root, env, oid):
    if not OBJECT_ID_RE.match(oid or ""):
        raise SnapUnavailable("not an object id")
    if _git(root, ["cat-file", "-t", oid], env=env).strip() not in ("tree", "commit"):
        raise SnapUnavailable("not a tree or commit")
```
Reuse `worktree_snap.OBJECT_ID_RE` by import; copy `_treeish` (it is private and takes the env).

**Reading `reviewed_tree` from the state** (`worktree_snap.py` 182-197 `prior_tree`) — same checks, but operate on the already-parsed `state` dict that `finalize_inputs._run` holds (do not re-read the file):
```python
passes = state.get("passes") if isinstance(state, dict) else None
if not isinstance(passes, list) or not passes or not isinstance(passes[-1], dict):
    raise SnapUnavailable("state has no last pass")
value = passes[-1].get("reviewed_tree")
if not isinstance(value, str) or not OBJECT_ID_RE.match(value):
    raise SnapUnavailable("last pass has no reviewed_tree")
```

**Core diff -> ranges pattern** (`worktree_snap.py` 223-241 `since`; the new module is this with `-R`, `--no-renames`, `--text`, swapped prefixes, and no second end = live working tree):
```python
    env = _store_env(root)
    _treeish(root, env, prior)
    ends = [prior]
    ...
    text = _git(root, ["diff", *DIFF_FLAGS, *ends, "--"], env=env)
    try:
        return diff_ranges.ranges_from_diff(text)
    except diff_ranges.RangeError as exc:
        raise SnapUnavailable(str(exc))
```
`DIFF_FLAGS` is at `worktree_snap.py` 101-102 (`--src-prefix=a/ --dst-prefix=b/`). Define a separate `REV_FLAGS` with the prefixes swapped (RESEARCH Pattern 1 / Pitfall 2) — do not edit `DIFF_FLAGS`.

**Repo top** — reuse `finalize_inputs._toplevel(cwd)` (176-184) semantics: `git rev-parse --show-toplevel`, `rstrip("\n")` only; `""` -> unverifiable.

**Never-raise public entry** (`finalize_inputs.py` 278-284):
```python
def head_blobs(state, cwd=None):
    """{file: HEAD blob id} for the last pass's fix verdicts. Never raises;
    {} when there is nothing to fingerprint or the state is wrongly shaped."""
    try:
        return _head_blobs(state, cwd)
    except (KeyError, IndexError, TypeError, AttributeError):
        return {}
```
Mirror it: `stale_decisions(state, blobs, cwd=None)` -> `[]` (no decided records; NO git call) or a sorted list of `{"hash","kind","cause"}`; any shape error on a decided record -> that record stale/unverifiable, never silently dropped.

**Which records** — read-only use of `carry_state` (`carry_state.py` 1088-1091, 464-467, 517-528):
```python
def _closed(record, state, last, head_blobs):
    if decision_state(record, state) == "current":
        return True
    return _fix_closes(record, state, last, head_blobs)
```
The freshness candidate set is `rec for rec in carry_state.open_findings(state) if decision_state(rec, state) == "current" and not carry_state._fix_closes(rec, state, last, blobs)` (keeps fix-verdict precedence, mutation check 8). Same `blobs` that `head_blobs` already computed in `_run`.

**Window** — `score.py` 177 and 1579-1592:
```python
_NEARBY_LINES = 5
...
    window = range(max(1, line - _NEARBY_LINES), line + _NEARBY_LINES + 1)
    return any(_line_in_ranges(n, ranges) for n in window)
```
Cause order per record: own line in ranges -> "line"; else window hit -> "nearby". Same-hash copies and covered members per `score._nearby_spots` (671-688: "copy" before "grouped", skip `own_line`, de-dup by line).

---

### `scripts/finalize_inputs.py` (EDIT — controller, request-response)

**Analog:** itself.

**`NEXT_ACTIONS` tuple** (147-149) — append the new value at the end; `TestNextAction.test_next_actions_are_the_seven_values_in_order` (test_finalize_inputs.py 768-772) pins the tuple and must be updated deliberately (rename to "eight"):
```python
NEXT_ACTIONS = ("write-review-md", "finalize-card", "stop-fallback-cw",
                "stop-fallback-nv", "stop-fallback-medium", "stop-no-state",
                "stop-refused")
```

**Integration point** (`_run` 439-458) — the stale check goes after `blobs` is written to `--blob-out` (so the only-file-written invariant holds) and before `build_result`; `build_result` stays pure and signature-compatible (TestBuildResultParity, 817+):
```python
    blobs = head_blobs(state, cwd)
    try:
        with open(blob_out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(blobs, sort_keys=True))
    except OSError:
        return _refuse(EXIT_USAGE, carry_state.REASON_HEAD_BLOBS)
    # [NEW] stale = closeout_fresh.stale_decisions(state, blobs, cwd)
    # [NEW] if stale: build the refusal dict (exit 0, action "refuse",
    #       next "<new value>", counts from carry_state.finalize_counts,
    #       report None, "stale": stale) and return it; else fall through.
    report_line = []
    ...
    code, result = build_result(state, blobs, switches, report_source=reread)
```
Refusal result shape mirrors `build_result`'s return dict (351-354) plus the one extra key, only on this path:
```python
    return EXIT_OK, {"action": action, "reason": reason,
                     "next": next_action(action, counts),
                     "counts": {k: counts[k] for k in COUNT_KEYS},
                     "report": report}
```
Keep `action` inside `finalize_gate.ACTIONS` (`"refuse"`); `reason` is a new fixed constant defined in `finalize_inputs` (A5: check whether any test asserts `reason in finalize_gate.REASONS`). Exit 0, serialized with `json.dumps(result, allow_nan=False)` like line 458. The top-level `run` (461-471) already maps any uncaught exception to `EXIT_GATE` — the new call inherits that.

**Docstring update** — extend the "stdout (exit 0)" block (13-15) and the "I/O: stdlib imports exactly" line (116-121) to name `closeout_fresh`; mention "With no decision-closed record the freshness check runs no git command" next to the existing "With no last-pass fix verdicts no git command runs at all" (line 66).

---

### `scripts/test_closeout_fresh.py` (NEW — test)

**Analog 1 (fixture base, mutants):** `scripts/test_finalize_inputs.py`

Module docstring describing behaviour/validation/mutant strategy (1-19), then imports (21-47):
```python
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import batch_card  # noqa: E402  (oracle: the 2.14.1 report data)
import carry_state  # noqa: E402  (oracle: the 2.14.1 counts)
import finalize_gate  # noqa: E402  (oracle: the 2.14.1 gate)
import finalize_inputs  # noqa: E402  (module under test)
import gitfixture  # noqa: E402  (shared temp-repo helper)
from gitfixture import git, write  # noqa: E402

MODULE_PATH = os.path.join(SCRIPTS_DIR, "finalize_inputs.py")
```

Temp-repo base with env isolation (102-121) — copy verbatim, including `GIT_CEILING_DIRECTORIES` and the `mock.patch.dict(os.environ, ..., clear=True)`:
```python
class InputsCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self.repo = gitfixture.make_repo(self.tmp)
        ...
        env = gitfixture.helper_env()
        env["GIT_CEILING_DIRECTORIES"] = self.tmp
        self._env = mock.patch.dict(os.environ, env, clear=True)
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()
```

Git-call recorder (81-99) — use it to prove "no decision-closed record -> no git call" (mutation check 9) and "no finding path ever reaches a git argv" (Pitfall 6):
```python
class Recorder:
    """Wraps the real `_git`, recording every argv; can fail chosen calls."""
    def __init__(self, real, fail=None): ...
    def __call__(self, args, cwd):
        self.calls.append(list(args))
        if self.fail is not None and self.fail(args):
            return None
        return self.real(args, cwd)
    def mentions(self, name):
        return any(name in a for a in self.argv_text())
```
Note the new module's `_git` signature is `(root, args, env=None)` (worktree_snap style), so the recorder needs that signature.

Source-substitution mutant (133-144) — the house style for mutation checks 1-7 (drop `-R`, normal prefixes, drop `--no-renames`, window 5->4, skip absent-file check, git-failure->unchanged, remove the call in `_run`):
```python
    def mutant(self, old, new):
        """A copy of finalize_inputs with `old` replaced by `new` (once)."""
        with open(MODULE_PATH, "r", encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn(old, src, "mutant text must be present in the real source")
        src = src.replace(old, new, 1)
        spec = importlib.util.spec_from_loader("finalize_inputs_mutant",
                                               loader=None)
        mod = importlib.util.module_from_spec(spec)
        mod.__file__ = MODULE_PATH
        exec(compile(src, MODULE_PATH, "exec"), mod.__dict__)
        return mod
```
Mutant test shape (556-590): assert the real behaviour first, then the mutant lets the guarded case through:
```python
    def test_mutant_no_worktree_check_includes_dirty_file(self):
        write(self.repo, "src/a.ts", "edited\n")
        s = state_for(["src/a.ts"])
        out, _ = self.run_helper(s)
        self.assertEqual(out, {})
        mod = self.mutant('_git(["diff", "--quiet", "HEAD", "--", spec], cwd)',
                          "(0, '')")
        out, _ = self.run_helper(s, module=mod)
        self.assertEqual(out, {"src/a.ts": self.blob("src/a.ts")})
```
For a mutant of `finalize_inputs._run` that must reach a mutated `closeout_fresh`, patch the module attribute (`mock.patch.object(finalize_inputs, "closeout_fresh", mutant_mod)`) rather than re-exec'ing both.

CLI runner (CliCase 1045-1098) — `cli()` already asserts state-file bytes unchanged, no new working-tree file, no owner sentence/Traceback; `inproc()` runs `run(argv, cwd=...)` with `module=`. Reuse by subclassing `test_finalize_inputs.CliCase` or importing `argv_for`, `sha256_of`, `tree_listing` (1017-1042):
```python
def argv_for(state_file, blob_out, switches=None, drop=None, extra=()):
    sw = dict(INTERACTIVE, **(switches or {}))
    pairs = [("--state-file", state_file), ("--blob-out", blob_out),
             ("--noninteractive", "true" if sw["noninteractive"] else "false"),
             ("--pr-mode", "true" if sw["pr_mode"] else "false"),
             ("--range-mode", "true" if sw["range_mode"] else "false")]
```

**Analog 2 (999.40 repro + window fixtures):** `scripts/test_decision_continuity.py`
```python
def base_file(n=60):                                       # 81-83
    """`n` distinct HEAD lines: `line_NN = NN`."""
    return ["line_%02d = %d" % (i, i) for i in range(1, n + 1)]

def pass1(lines, title=TITLE_A, conf=70, kind="dismiss", agent="bugs",
          line=10, **kw):                                  # 327-335
    """Pass 1: one finding at `line`, decided by the owner -> (state, hash)."""
    s1, r1 = run_pass(empty_state(), lines,
                      [fresh(agent, line, lines, title, conf=conf, **kw)], 1,
                      {F: [[1, 200]]})
    ...
    return decide_on(s1, h, kind=kind), h
```
`F = "src/a.py"` (line 71). Import as `import test_decision_continuity as tdc` (the convention `test_worktree_snap.py` uses). The RESEARCH "Code Examples" block is the exact repro recipe (write file, commit, `pass1`, set `head_sha` + `reviewed_tree = HEAD^{tree}`, edit, run CLI).

**Analog 3 (real prose fences, store path exercised, clearable loop):** `scripts/test_worktree_snap.py` `_Chain` (172-268)
```python
class _Chain(_Phases, tdc._RealChain):
    """Pass 1 reviews an uncommitted block and the owner defers the finding;
    pass 2 runs every prose fence again in fresh shells."""
    ...
    def persist(self, state, head, tree):                  # 196-206
        state = json.loads(json.dumps(state))
        state["passes"][-1]["head_sha"] = head
        if tree:
            state["passes"][-1]["reviewed_tree"] = tree
        path = os.path.join(os.path.dirname(self.repo.repo), "state.json")
        ...
    def pass1(self, route="default", record_tree=True):    # 215-245
    def pass2(self, L2, rereport=True, use_nearby=True):   # 250-264
```
"Clearable" tests (D-13/D-16): `pass1()` -> edit -> Close out refuses -> `pass2(L2)` (real fences, new `reviewed_tree`) -> `tdc.decide_on(s2, h, ...)` -> `persist(...)` -> Close out writes. Assertions reuse `_RealChain.assert_reopens` / `assert_keeps` (test_decision_continuity.py 3936-3947).

---

### v2.15 materializer (two-sided differential, FRESH-02 / SC4)

**Precedent 1** — `scripts/test_finalize_parity_grid.py` 93-132: pin a commit constant and read files with `git show` under `clean_env()`; fail loudly when history is shallow:
```python
SOURCE_COMMIT = "dd8e4ab"
...
def clean_env():
    env = gitfixture.helper_env()
    for key in list(env):
        if key.startswith("GIT_") and key not in ("GIT_CONFIG_GLOBAL",
                                                  "GIT_CONFIG_NOSYSTEM"):
            del env[key]
    return env

def source_text():
    proc = subprocess.run(
        ["git", "show", SOURCE_COMMIT + ":" + SOURCE_DOC], cwd=SCRIPTS_DIR,
        env=clean_env(), stdin=subprocess.DEVNULL, capture_output=True,
        timeout=60)
    if proc.returncode != 0:
        raise AssertionError("cannot read %s at %s (needs full history): %s"
                             % (SOURCE_DOC, SOURCE_COMMIT,
                                proc.stderr.decode(errors="replace")))
    return proc.stdout.decode("utf-8")
```
**Precedent 2** — byte-identity pin (190-207 `test_shared_modules_are_byte_identical_to_dd8e4ab`): `git rev-parse <commit>:<rel>` vs `git hash-object --no-filters <file>`. Use the same check with `d5acc19` to assert which modules the candidate did NOT change (so the differential's "old" side is genuinely 2.15).
**Precedent 3** — loading a module from history into a temp dir and importing it, with `finally: shutil.rmtree`: `scripts/replay.py` `load_scorer` 412-455 (`tempfile.mkdtemp`, write bytes, `importlib.util.spec_from_file_location`, unique module name via a counter). Also `docs/design/lean-v2.15/tools/path_records.py` 111-128 (`exec` of `git show` output under a non-main `__name__`).

Materializer recipe for the planner: for each of `finalize_inputs.py, carry_state.py, finalize_gate.py, batch_card.py, guard.py, fixcommit.py` (plus any sibling those import at d5acc19 — check with `git show d5acc19:plugins/vibe-check/scripts/<m> | grep ^import`), `git show d5acc19:plugins/vibe-check/scripts/<m>` into one `tempfile.mkdtemp()`; run the OLD helper as a subprocess `[sys.executable, <tmp>/finalize_inputs.py, ...]` (its own `sys.path.insert(dirname(__file__))` at line 130 then resolves siblings from the temp dir, so no in-process module collision); `shutil.rmtree` in `finally`/`addCleanup`. Compare stdout bytes + exit code with the candidate on unchanged fixtures (must be equal) and on each intended-refusal fixture (old = write, new = refuse — both outcomes asserted, like the parity grid's KNOWN_DIFFERENCES rule in its docstring lines 22-30).

---

### `scripts/test_finalize_inputs.py` (EDIT)

- `TestNextAction.test_next_actions_are_the_seven_values_in_order` (768-772): add the new value; `test_next_mapping` (782-806) unchanged (the new `next` is not produced by `next_action`, it comes from the freshness path).
- `ResultCase.prepared` (752-763) / `TestCliWritesOnlyTheFingerprintFile.routes` (2043-2050): add a `"stale refusal"` route so "only the fingerprint file changes" covers the refusal (Pitfall 5):
```python
    def routes(self):
        fix = fix_obsolete_state(self.blob(ARCH_FILE))
        return {
            "write": (fix, True),
            "card": (load_six_row(), True),
            "state refused": ("not json", False),
            "no state file": (None, False),
        }
```
- Blast radius (Pitfall 4c): fixtures with current decisions and no `reviewed_tree` (e.g. `dismissed_all_state` 693-698, `dismiss` 684-691) will now refuse "unverifiable". Re-home them by adding a real `reviewed_tree` (`git rev-parse HEAD^{tree}` after committing the decided files into `self.repo`) in a shared helper, not by loosening assertions. Same applies in `test_finalize_card.py` and `test_confirmed_fix.py`.

---

### `scripts/test_finalize_parity_grid.py` (EDIT, conditional)

Grid states (`fixtures/phase45-loop-state.json` + a dismiss on `BUGS_HASH`) have no `reviewed_tree` and the decided file is not in the grid repo. Either (a) give each grid scenario the decided file committed + `reviewed_tree`, or (b) scope the comparison to the fingerprint map/counts/gate the 2.14.1 side computes (the grid compares "fingerprint map, the three counts and the gate action", docstring 7-10). Keep `SHARED_WITH_2141` (103-104) and `test_shared_modules_are_byte_identical_to_dd8e4ab` untouched unless shape 2 forces a `carry_state.py` edit.

---

### `scripts/test_finalize_card.py` (EDIT — prose lock for the new `next` bullet)

**Analog:** the NV fallback bullet lock, 1851-1866 + 1925-1936:
```python
NV_FALLBACK_HEADER = ("Print: \"Cannot finalize — {{N}} Needs-verification "
                      "item(s) undecided:\"")

def nv_fallback_listing_holds(text):
    i = text.find(NV_FALLBACK_HEADER)
    if i < 0:
        return False
    bullet_end = text.find("\n- ", i)
    bullet = text[i:bullet_end if bullet_end >= 0 else len(text)]
    return "`undecided_nv_hashes`" in bullet and "and stop" in bullet
```
```python
    def test_nv_fallback_listing(self):
        self.assertTrue(nv_fallback_listing_holds(self.text))
        with self.subTest("mutant: header removed"):
            self.assertFalse(nv_fallback_listing_holds(
                self._mutant(NV_FALLBACK_HEADER)))
```
New `review_again_bullet_holds(text)` should require: the bullet key, `` `stale` `` list rendered by the join rule, the ~10-row cap + "+N more", the same-scope command per route, the phrase that a review starts the paid reviewers, "Do NOT write REVIEW.md or archive state", and "and stop"; and must reject any dispatch/re-entry wording. One mutant subTest per required phrase (house style: `LockCase.assert_holds/assert_trips` 963-969, `_mutant` 1366-1370).

**Placement gotcha:** `write_bullet()` (1871-1873) slices from the `write-review-md` bullet to `- \`stop-refused\``; and the retry lock (`retry_rule_holds`, mutant at 1404-1406) pins "A `next` of `stop-refused` is never retried." Put the new bullet AFTER `stop-refused` (or before `write-review-md`) so `write_bullet` is unchanged, and add "A `next` of `<new>` is never retried." beside the existing sentence with its own mutant.

---

### `scripts/test_decision_continuity.py` (EDIT — 999.44 shape 1/2 fixtures)

**Analog:** `far_twin_scenario` (966-990) + `test_p4_far_twin_new_copy_is_not_evidence` (1726-1749) — this is the D-21 control D-11 must keep passing. Shape 1 (deleted-original) is the same setup with the original line deleted instead of kept:
```python
    L0 = base_file()
    L0[9] = L0[29] = "return None"
    s1, hA = pass1(L0, conf=STABLE_CONF)
    s2, r2 = run_pass(s1, L0, [fresh("bugs", 30, L0, TITLE_A, conf=100)], 2,
                      {F: [[33, 33]]})
```
The relocation simulator is `relocate_decided` (112-158), case 2 "exactly one match ... -> that line" (154-155) is where a bounded re-ask would sit (D-14), with the matching prose in `phases/review/30-collect-score.md` step 0. Real-diff ranges come from `_RealChain` + `RealDiffRepo` + `_builder()` (see `TestRealDiffRanges60` 3998-4040). Shape 2 producibility goes through `decide_on` (252-258) -> `carry_state.record_decisions`.

---

### `scripts/test_worktree_snap.py` (EDIT — `--all` now records `reviewed_tree`, D-12)

`TestProse.test_every_snapshot_call_states_the_finalize_and_all_skip` (1074-1085) asserts each take paragraph contains `--all` (the skip). After D-12 this lock must change: the default-route skip sentence keeps `--finalize`, and a new take in `00-scope-all.md` must be locked the same way:
```python
        for take in (P0_DEFAULT, P0_PR, P0_RANGE,
                     "take the same working-tree snapshot as mode 1"):
            with self.subTest(take=take):
                at = scope.index(take)
                para = scope[at:scope.index("\n\n", at)]
                self.assertIn("--finalize", para)
                self.assertIn("FINALIZE_MODE=1", para)
                self.assertIn("--all", para)
```
`test_collect_fence_is_one_call_with_state_file` (1100-1110) counts exactly 3 collect fences — decide whether `--all` reuses the default-route fence (preferred; count unchanged) or gets its own. `test_schema_allows_reviewed_tree_as_optional_pass_key` (1119-1123) already passes. Add a real-chain `--all` test via `_Phases.run_pass_fences` (106-131) with `_lookup_fences` extended for an `"all"` route.

---

### `phases/shared/90-finalize.md` (EDIT — new `next` bullet)

**Analog:** `stop-fallback-nv` bullet (lines 45-48) for list-rendering + `stop-refused` (66) for the stop clause:
```markdown
- `stop-fallback-nv` — the gate's `fallback` with `outstanding_cw` empty and `undecided_nv` non-empty ...:
  - Print: "Cannot finalize — {{N}} Needs-verification item(s) undecided:"
  - List each item whose hash is in `undecided_nv_hashes` as `{{file}}:{{line}} — {{title}}` by the join rule above; ...
  - Tell the user "Fix these, or decide them interactively, then re-run with `--finalize`." and stop. No asks, no writes.
...
- `stop-refused` — print "I'm uncertain about Finalize mode — finalize_gate.py refused its input" and stop. Do NOT write REVIEW.md or archive state.
```
Also update line 36 ("Branch on `next`. Any other value ... is treated as `stop-refused`") only if needed (an older prose already fails toward stopping), and line 38's retry paragraph ("A `next` of `stop-refused` is never retried.") to add the new value. The join rule is defined in the `stop-fallback-cw` bullet (line 43). Per-route command text (D-02/D-13/D-15): default/GSD `/review [<phase>]`, PR `/review <ref>`, range `/review <range>`, `--all` `/review --all [<narrow>]`, plus the untracked ("add the file to git, then review again") and PR/range-disk ("commit or revert the nearby edits, or check out the reviewed commit, then review again") variants keyed off `stale[].cause`. Footprint: `90-finalize.md` is in `footprint.py` `MODE_PATHS["finalize"]` (footprint.py ~98-103), so its byte growth shows up in footprint records.

---

### `phases/review/00-scope-all.md` (EDIT — take on `--all`)

**Analog:** `phases/review/00-scope.md` mode-1 take, lines 37-42:
```markdown
   ```bash
   GREPO=$(git rev-parse --show-toplevel)
   python3 "$VC_ROOT/scripts/worktree_snap.py" take --root "$GREPO"
   ```
   It prints `REVIEWED_SNAPSHOT=<nonce>` (empty on failure, never an error); carry that printed literal to Phase 3's `worktree_snap.py collect --before` (a shell variable does not survive into a separate Bash call). ... Skip it on `--finalize` (`FINALIZE_MODE=1`) and `--all`. Then assemble diff via:
```
Edit `00-scope.md` line 42's "Skip it on `--finalize` (`FINALIZE_MODE=1`) and `--all`." (and the same skip sentences at 59, 72, 109) only as far as D-12 needs; add the same fence in `00-scope-all.md` step e (before `$REVIEW_SET` is sent to agents), with the `--finalize` skip. GSD-route precedent for "take the same snapshot as mode 1" is `00-scope.md` line 109.

### `phases/review/30-collect-score.md` (EDIT)

Line 90 heading "every route except `--all` (999.28)" and the default fence at 93-96 become `--all`-inclusive. Line 122 (`nearby_line_ranges` envelope key "only when the since-review call printed a non-empty `NEARBY_LINE_RANGES=`") must state `--all` never sends it (D-12: no scorer effect; `--all` never stamps). Lock with a phrase test alongside `test_envelope_names_nearby_line_ranges` (test_worktree_snap.py 1125-1126).

### `phases/review/45-persist.md` + `45-persist-all.md` (EDIT)

`45-persist.md` line 21 comment `// OPTIONAL — every route except --all, present ONLY when ...` and line 39 table cell "Omitted when the printed value was empty, and on the `--all` route" drop the `--all` exclusion. `45-persist-all.md` lists only the three `--all`-only keys; `reviewed_tree` is NOT one of them (it stays a `pass_optional` key, `future-schema.json` line 9), so `45-persist-all.md` needs at most a one-line pointer. `state_shape.check_pass_entry` (state_shape.py 222-250) already accepts `reviewed_tree` in any mode — no code change; existing lock `test_persist_names_reviewed_tree` (test_worktree_snap.py 1113-1117).

### `scripts/fixtures/future-schema.json` (EDIT — history note only)

Line 9 already has `"pass_optional": ["resolved", "reviewed_tree"]`; no structural edit. Append a sentence to the `_purpose` string (line 2) in its existing history style ("999.28 (2.14.1 fix ...) added the optional pass key `reviewed_tree` ...") recording that v2.16 Phase 66 (D-12) also writes it on `--all`; rollback stays `_rollback.fix999_28_added` (line 41). The `_purpose` says "Changing this file is an envelope change and needs a recorded decision" — D-12 is that decision.

---

## Shared Patterns

### Fail closed, fixed reasons, no echo
**Source:** `scripts/finalize_inputs.py` 23-30, 422-425
**Apply to:** `closeout_fresh.py`, `finalize_inputs.py` refusal path
```python
def _refuse(code, line):
    if line:
        sys.stderr.write(line)
    return code, ""
```
The helper never prints a path, hash or title on stderr; the refusal is data in the JSON result (`stale`: hashes + kind + cause tokens), and prose renders titles via the join rule.

### Untrusted finding paths
**Source:** `scripts/finalize_inputs.py` 257-259 (`PATH_RE.match(f)` before any git), `fixcommit.PATH_RE`
**Apply to:** `closeout_fresh.py` — but stronger: never put a finding path on a git argv at all (diff the whole tree with a trailing `--`, then look up paths in the parsed map). Paths failing `PATH_RE`, non-int lines -> stale "unverifiable".

### Subprocess discipline
**Source:** `worktree_snap.py` 117-129; `finalize_inputs.py` 159-169
argv list, `stdin=subprocess.DEVNULL`, `stdout/stderr=PIPE`, `timeout=GIT_TIMEOUT`, catch `(OSError, subprocess.TimeoutExpired)`, stderr dropped.

### Mirrored constant + lock test (avoid importing score.py)
**Source:** `scripts/carry_state.py` 549-551 and `scripts/test_carry_state.py` 4163-4167
```python
# Band order for the direction-aware compare. Mirror of score._BAND_SEVERITY
# without its None key (this module may not import score).
_BAND_RANK = {"critical": 4, "warning": 3, "medium": 2, "low": 1}
```
```python
    def test_mirror_lock(self):
        for s in self.SAMPLES:
            with self.subTest(sample=s):
                self.assertEqual(carry_state._nv_code_key(s),
                                 score._nv_code_key(s))
```
**Apply to:** `closeout_fresh._NEARBY_LINES = 5` with a test asserting `== score._NEARBY_LINES` (D-05), and a window-function equality test against `score._nearby_changed` over edge lines 4/5/15/16.

### Temp repos in tests
**Source:** `scripts/gitfixture.py` 23-69 (`helper_env`, `git`, `make_repo`, `write`)
**Apply to:** every new real-git test. Never ad hoc `git init`; always `helper_env()`; cleanup via `TemporaryDirectory().cleanup()` in `tearDown`.

### Mutation-test every guard
**Source:** `scripts/test_finalize_inputs.py` 12-15 (docstring rule), 133-144 (`mutant`), 556-660 (`TestMutants`); prose side `test_finalize_card.py` `LockCase` + `_mutant`.
**Apply to:** the nine mutation checks in RESEARCH "Validation Architecture" and every new prose phrase lock.

### Two-sided differential vs a literal old version
**Source:** `scripts/test_finalize_parity_grid.py` (whole module; pin at 93, `source_text` 121-132, byte-identity 190-207)
**Apply to:** the FRESH-02 / SC4 differential against `d5acc19`.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| (none fully) | — | — | Every file has an analog. Partial gaps: (1) no existing READ-ONLY store env — `worktree_snap._store_env` creates the store; the new module needs a no-`makedirs` twin. (2) No existing multi-module "materialize a whole sibling set at a commit" helper — parity grid reads one doc and hash-checks modules; replay/path_records load one module. Combine those patterns as described above. (3) No reverse-diff (`-R`) call exists anywhere in the repo; RESEARCH Pattern 1 flags are the spec. |

## Conventions

Convention derivation skipped (`verify conventions --derive --scope plugins/vibe-check/scripts` returned `{"skipped": true, "reason": "no-app-files"}`). Observed by reading instead: snake_case module and function names, private helpers prefixed `_`, UPPER_CASE module constants, no `__all__`, sibling imports via `sys.path.insert` + `# noqa: E402 (reason)`, tests as `unittest.TestCase` classes collected by bare `pytest`, stdlib-only runtime (CI `.github/scripts/stdlib_only.py plugins/vibe-check`). The CJS/ESM dual-resolver split named in the mapper template does not apply to this Python-only plugin; match the local directory's style.

## Metadata

**Analog search scope:** `plugins/vibe-check/scripts/` (helpers + tests + fixtures), `plugins/vibe-check/phases/review/`, `plugins/vibe-check/phases/shared/`, `docs/design/lean-v2.15/tools/`
**Files scanned:** ~25 (read in part: finalize_inputs.py, worktree_snap.py, gitfixture.py, carry_state.py, score.py, state_shape.py, footprint.py, replay.py, path_records.py, test_finalize_inputs.py, test_finalize_parity_grid.py, test_decision_continuity.py, test_worktree_snap.py, test_finalize_card.py, test_carry_state.py, 90-finalize.md, 00-scope.md, 00-scope-all.md, 30-collect-score.md, 45-persist.md, 45-persist-all.md, future-schema.json)
**Pattern extraction date:** 2026-11-17
