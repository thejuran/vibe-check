# Phase 62: Baseline and continuous test run - Pattern Map

**Mapped:** 2026-11-13
**Files analyzed:** 17 new files or file groups (0 plugin files modified; D-16 keeps `plugins/` byte-identical to `v2.14.1`)
**Analogs found:** 15 / 17 (the workflow YAML and the red/green CI record have no in-repo analog)

All new code lives **outside `plugins/vibe-check/`**: in `.github/` and `docs/design/lean-v2.15/`. That follows the freeze-v2.12 precedent (`docs/design/freeze-v2.12/tools/freeze_common.py:7-8`: "The kit lives outside `plugins/`, so it never enters the plugin file set it hashes"). Every lock gets a mutant that trips it (the house rule in `test_finalize_card.py:17-19`).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `.github/workflows/offline-suite.yml` | config (CI) | event-driven | none in repo (first workflow); RESEARCH §Code Examples + `61-RELEASE-RECORD.md` G1/G8 commands | no analog |
| `.github/scripts/stdlib_only.py` | utility (gate CLI) | batch / file-I/O scan | `plugins/vibe-check/scripts/footprint.py` (CLI shape) + `test_footprint.py:93-106` (AST import walk) | role-match |
| `.github/scripts/test_stdlib_only.py` | test (lock + mutant) | batch | `plugins/vibe-check/scripts/test_footprint.py` | exact |
| `.github/scripts/test_workflow_shape.py` | test (text lock + mutant) | transform | `plugins/vibe-check/scripts/test_finalize_card.py` (`LockCase` check functions) | role-match |
| `docs/design/lean-v2.15/tools/step_count.py` (D-05 counting rule) | utility | transform (prose → counts) | fence extractors in `test_finalize_card.py:526, 1810-1845` + `footprint.read_content` `--rev` | role-match |
| `docs/design/lean-v2.15/tools/test_step_count.py` | test | transform | `test_footprint.py` (`TestPinnedRev`) + `test_finalize_card.py` mutant style | exact |
| `docs/design/lean-v2.15/tools/finalize_capture.py` (five D-07 situations) | utility (driver) | request-response (subprocess per fence) | `test_finalize_card.py:1973-2131` `TestFinalizeFreshShellWalk` | exact |
| `docs/design/lean-v2.15/tools/baseline_records.py` (fingerprints, replay normalization, footprint and trace assembly) | utility | transform / file-I/O | `docs/design/freeze-v2.12/tools/freeze_common.py:185-249` + `freeze_tally.py` (CLI, sibling import) | exact |
| `docs/design/lean-v2.15/tools/test_baseline_records.py` | test (re-derive committed evidence + tamper mutant) | file-I/O | `docs/design/freeze-v2.12/tools/test_freeze_manifest.py:628-672` (`verify_self` tamper tests) | exact |
| Trace extraction (inside `baseline_records.py` or `traces.py`) | utility | file-I/O (JSONL) | `plugins/vibe-check/scripts/tracecheck.py:152-204` | exact (reuse, don't copy) |
| `docs/design/lean-v2.15/tools/usage_fields.py` (cost reader, BASE-01) | utility | batch / file-I/O (JSONL) | `tracecheck.events` (JSONL + `subagents/*.meta.json` linking) | role-match |
| `docs/design/lean-v2.15/tools/test_usage_fields.py` | test (synthetic fixtures + never-echo) | file-I/O | `plugins/vibe-check/scripts/test_tracecheck.py:59-191, 480-489` | exact |
| `docs/design/lean-v2.15/BASELINE-v2.14.1.md`, `CRITERION.md`, `README.md` | docs (design evidence) | — | `docs/design/prose-diet-footprint-v2.10.md`, `docs/design/freeze-v2.12/README.md` | exact |
| `docs/design/lean-v2.15/baseline/*.json`, `*.md`, `*.sha256` | data records | — | `footprint.py --json` output shape; `docs/design/freeze-v2.12/evidence/*.json` | role-match |
| `.planning/phases/62-…/62-COST-NOTE.md` | doc (go/no-go) | — | `.planning/milestones/v2.12-phases/54-…/54-BUDGET.md` §1 (source + "counted once per message"), **minus all pricing** | role-match |
| `.planning/phases/62-…/62-CI-RECORD.md` (red/green run links, tree identity) | doc (record) | — | `.planning/milestones/v2.14-phases/61-…/61-RELEASE-RECORD.md` (gate table + tree-identity line) | role-match |
| `.planning/STATE.md`, `.planning/ROADMAP.md` (backlog item for the smallest usage report if "go") | config (planning) | — | `/Users/julianamacbook/Documents/Codex/planning/PLANNING-FORMAT.md` | format rule, not code |

## Pattern Assignments

### `.github/scripts/stdlib_only.py` (utility gate, batch scan)

**Analog:** `plugins/vibe-check/scripts/footprint.py` (CLI shape and docstring) and `test_footprint.py` (AST walk).

**Module docstring declares the import lock and the CLI** (`footprint.py:24-27`):
```python
I/O: stdlib only, imports exactly {json, os, subprocess, sys}. CLI:

    python3 footprint.py [--root <plugin root>] [--rev <sha>] [--json] [--measure]
```

**AST import walk to reuse** (`test_footprint.py:96-106`, also in `TestImportSet` for 23 modules):
```python
with open(FOOTPRINT_PY) as fh:
    tree = ast.parse(fh.read())
found = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for a in node.names:
            found.add(a.name.split(".")[0])
    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        found.add(node.module.split(".")[0])
```
Extend it with `sys.stdlib_module_names` plus the set of sibling module basenames, as in RESEARCH §"Stdlib-only scan".

**Exit-code convention** (`freeze_tally.py:20, 309-326` — 0 clean / 1 violation / 2 usage):
```python
def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        return COMMANDS[args.cmd](args)
    ...
    except UsageError as exc:
        sys.stderr.write("freeze_tally.py: %s\n" % exc)
        return 2

if __name__ == "__main__":
    sys.exit(main())
```
`tracecheck.py` uses the same 0/1/2 contract (`docs/design/mode-path-validation-v2.10.md:30`: "Exit 0 clean, 1 violation, 2 unusable input").

**Scope fact for the plan:** `git ls-files 'plugins/vibe-check/scripts/*.py' | grep -v /test_` = **33** files, all in `scripts/`. No `.py` exists elsewhere under `plugins/vibe-check`. Phase 61 G8 reported "32 shipped .py files" (`61-RELEASE-RECORD.md:22`), so it apparently excluded `gitfixture.py`. The plan must state which count it uses (RESEARCH Open Question 3 recommends scanning `gitfixture.py`, giving 33) and print the file count, as G8 did.

---

### `.github/scripts/test_stdlib_only.py` (test, lock + mutant)

**Analog:** `plugins/vibe-check/scripts/test_footprint.py`

**Header and sibling import** (`test_footprint.py:31-46`):
```python
import ast
import glob
import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import footprint  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
FOOTPRINT_PY = os.path.join(HERE, "footprint.py")
PLUGIN_ROOT = os.path.abspath(os.path.join(HERE, ".."))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
```
For `.github/scripts/`, `REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))`.

**CLI test through a subprocess** (`test_footprint.py:295-300, 328-333`):
```python
def _run(self, *argv):
    return subprocess.run([sys.executable, FOOTPRINT_PY, *argv],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=60)
```

**Mutant:** build a temp tree with `tempfile.mkdtemp()` and `self.addCleanup(shutil.rmtree, tmp, True)` (`test_finalize_card.py:1992-1993`), plant `import requests` in a non-test module, and assert exit 1 with the module named. The real tree must give exit 0. Add a second mutant that plants the import in a `test_*.py` or `gitfixture.py`, matching the scope the plan picks, so the include/exclude rule itself is locked.

**Own import lock** (`test_freeze_tally.py:354-365`, subset style for tool kits):
```python
class TestImportSet(unittest.TestCase):
    def test_module_level_imports(self):
        with open(os.path.join(HERE, "freeze_tally.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in tree.body:
            ...
        allowed = {"argparse", "json", "os", "sys", "tempfile"}
        self.assertTrue(all(n in allowed or n.startswith("freeze_") for n in names), names)
```

---

### `.github/scripts/test_workflow_shape.py` (test, static YAML text lock + mutant)

**Analog:** `plugins/vibe-check/scripts/test_finalize_card.py`. Its prose locks are check functions that return a list of problems and are run on the real text and on a mutant.

**LockCase** (`test_finalize_card.py:909-914`):
```python
class LockCase(unittest.TestCase):
    def assert_holds(self, check, *texts):
        self.assertEqual(check(*texts), [])

    def assert_trips(self, check, *mutant_texts):
        self.assertNotEqual(check(*mutant_texts), [])
```

**Check function returning problems** (`test_finalize_card.py:1898-1904`):
```python
def retry_rule_holds(text):
    para = retry_paragraph(text)
    if not para:
        return ["no rebuild-once paragraph"]
    return ["rebuild rule lacks: " + n for n in RETRY_NEEDLES if n not in para]
```

**Mutant inside the same test, with a "the mutation actually happened" guard** (`test_finalize_card.py:2529-2535`):
```python
with self.subTest("mutant: the .err redirect removed"):
    self.assertIn(GATE_ERR_REDIRECT, self.text)
    mutant = self.text.replace(GATE_ERR_REDIRECT, "", 1)
    self.assertNotEqual(mutant, self.text)
    problems = self._gate_owner_view(mutant, "")
    self.assertNotEqual(problems, [])
```
Apply it to the workflow text: `push` `branches: ['**']`; `pull_request` `branches: [main]`; `permissions: contents: read`; no `secrets.`; no `${{ github.event` inside `run:`; every `uses:` pinned to 40-hex; `fetch-depth: 0`; a named stdlib-only step; the deselect count guard. Stdlib only, so use regex and line checks with no YAML library (RESEARCH §Validation). Each check gets one mutant. The `assertIn` / `assertNotEqual(mutant, text)` pair stops a decorative mutant (see the memory note "Decorative guards").

---

### `docs/design/lean-v2.15/tools/step_count.py` (D-05 counting rule, transform)

**Analog:** the fence and literal regexes in `test_finalize_card.py`, and `footprint.read_content` for reading at a revision.

**Regexes for the countable things** (`test_finalize_card.py:526, 1810-1811, 1844-1845`):
```python
MKTEMP_RE = re.compile(r"^\s*(?:if )?([A-Z_]+FILE)=\$\(mktemp", re.M)
_PRINTED_RE = re.compile(r"^([A-Z_]+FILE)=(.+)$", re.M)
_FILE_REF_RE = re.compile(r'"\$([A-Z_]+FILE)"')

def _print_line(name):
    return "printf '%s=%%s\\n' \"$%s\"" % (name, name)
```

**Fence extraction** (`test_finalize_card.py:75` `bash_fences`, `1824-1841`):
```python
def _fence_holding(text, needle):
    """Body of the ```bash fence that holds `needle` (None if absent)."""
    if needle not in text:
        return None
    at = text.index(needle)
    start = text.rindex("```bash\n", 0, at) + len("```bash\n")
    return text[start:text.index("```", at)]
```

**Read at a pinned revision, never from the worktree** (`footprint.py:121-143`):
```python
if rev:
    proc = subprocess.run(
        ["git", "-C", _repo_root(root), "show",
         "%s:%s/%s" % (rev, _PLUGIN_PREFIX, rel)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=30, check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout
```
Take the file set from `footprint.MODE_PATHS["finalize"]` (`footprint.py:98-103`) by import, not by copying, so Phase 63 counts the same set. Import the plugin modules with the `freeze_tally._score43` sys.path pattern (`freeze_tally.py:133-138`):
```python
scripts = os.path.join(repo, PLUGIN_SCRIPTS_REL)
if scripts not in sys.path:
    sys.path.insert(0, scripts)
import score43
```
Do **not** copy the regexes out of `test_finalize_card.py` by importing that test module: it is a 2,538-line test file. Copy the three regexes and `_fence_holding` into the tool and lock them there. Every `subprocess.run` needs an explicit `timeout`. That rule is itself locked in `test_footprint.py:108-119`, so copy that lock as well.

---

### `docs/design/lean-v2.15/tools/test_step_count.py` (test)

**Analog:** `test_footprint.py` `TestPinnedRev` (`:122-140`). It pins the number at a revision and recomputes it independently:
```python
def test_before_numbers_come_from_pinned_rev_not_worktree(self):
    stats = footprint.file_stats(PLUGIN_ROOT, "commands/review.md",
                                 rev=footprint.PRE_PHASE_REV)
    self.assertEqual(stats["bytes"], REVIEW_MD_BYTES_AT_PIN)
    ...
    # Independently recomputed, so the assertion is not just echoing the
    # module's own arithmetic.
    self.assertEqual(stats["bytes"], len(self._git_show_bytes("commands/review.md")))
```
Pin the committed `steps-v2.14.1.json` figures at `v2.14.1`. Mutants: a temp copy with one more fence gives +1, one more printed literal gives +1, and one more carried-literal use gives +1, as RESEARCH Pattern 4 requires. Pin-constant style: `test_footprint.py:55-60` holds the module-level constants with a comment saying where each number was verified.

---

### `docs/design/lean-v2.15/tools/finalize_capture.py` (five D-07 situations, request-response per fence)

**Analog:** `plugins/vibe-check/scripts/test_finalize_card.py:1973-2131` `TestFinalizeFreshShellWalk`

**Fresh shell with exactly four env vars** (`:1996-2005`):
```python
def _run_fresh(self, script, state_file=SIX_ROW_FIXTURE):
    tmpdir = tempfile.mkdtemp(dir=self.tmp)
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "VC_ROOT": PLUGIN_DIR, "TMPDIR": tmpdir,
           "STATE_FILE": state_file}
    proc = subprocess.run(["bash", "-s"], input=textwrap.dedent(script),
                          env=env, cwd=tmpdir, capture_output=True,
                          text=True, timeout=60)
    return proc.returncode, proc.stdout, proc.stderr
```

**Carry printed literals into later fences** (`:2007-2032`): `_literal(fence, subs)` replaces `"$NAME"` and `"$NAME.` with the printed path. `_mint(name)` runs the fence that prints `NAME=` and returns that path.

**Gate input from real sources** (`:2054-2069`): `_flags(counts, state_file)` builds the seven-key `flags` object and asserts `set(flags) == set(finalize_gate.FLAGS)`.

**Situation → existing walk** (copy the step sequences, not the assertions):

| D-07 | Walk to mirror | Lines |
|---|---|---|
| 1 clean close | `test_walk_reaches_counts_gate_report` (`_write_route_state` → mint BLOBFILE → counts → gate `write` → `decisions-report`) | `:2098-2131` |
| 2 card first | `test_card_route_records_then_writes` (SIX_ROW fixture → `outstanding-to-phase-5` → rows → parse → record-decisions → recount → `write`) | `:2133-…` |
| 3 one rebuild | `test_retry_mints_new_blobfile_after_missing_path`, `test_retry_mints_new_gatefile_after_gate_input_failure` | `:2224-2238`, `:2264-2304` |
| 4 refused / writes nothing | `test_malformed_gatefile_shows_only_stop_sentence`; `GATE_HALT` and `STOP_SENTENCE` constants | `:2523-2535`, `:1859-1863` |
| 5 fresh shell restart | `test_post_decision_rerun_decides_on_a_fresh_gatefile`, `test_post_decision_recount_refingerprints_head` | `:2306`, `:2382` |

**Fixtures to reuse (read-only, inside `plugins/`):** `plugins/vibe-check/scripts/fixtures/iplayarr45-six-row-state.json` (`SIX_ROW_FIXTURE`, `:1808-1809`) and `phase45-loop-state.json` (through `test_carry_state.load_fixture`).

**Design constraint (RESEARCH Pattern 2):** define each situation by its inputs and observable outputs, with a thin per-version driver. In 2.14.1 the driver extracts fences; in Phase 63 it calls the helpers. Before hashing, normalise `mktemp` paths (`vc.XXXXXX`) and timestamps to placeholders. Use `tempfile.mkdtemp` with `try/finally` cleanup in the CLI (`addCleanup` in tests).

---

### `docs/design/lean-v2.15/tools/baseline_records.py` (fingerprints and records, transform)

**Analog:** `docs/design/freeze-v2.12/tools/freeze_common.py` (hashing) + `freeze_tally.py` (CLI)

**Kit docstring and import lock** (`freeze_common.py:1-15`):
```python
"""Shared helpers for the v2.12 freeze kit.

Every hash this kit records comes from content: blobs read from the git
object store of a candidate commit, or bytes read from a live directory.
Version strings and mtimes never stand in for content.

Stdlib only (import lock: hashlib, json, os, re, subprocess). The kit lives
outside `plugins/`, so it never enters the plugin file set it hashes.
"""
```

**Canonical JSON fingerprint** (`freeze_common.py:185-186, 240-249`):
```python
def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def canonical_json(obj):
    """Canonical JSON text: sorted keys, compact separators, UTF-8 kept."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)

def canonical_sha256(obj):
    return sha256_bytes(canonical_json(obj).encode("utf-8"))
```

**Replay volatile header lines to strip** (`plugins/vibe-check/scripts/replay.py:865-866` baseline/candidate; `:1266-1267` diff):
```python
("HEAD", _head_sha()),
("generated (UTC)", _utc_now()),
...
("head", _head_sha()),
("generated", _utc_now())]
```
Normalisation rule (RESEARCH): drop lines matching `^- (HEAD|head|generated( \(UTC\))?): `, then sha256 what remains. Write the rule next to the hash.

**Footprint (declared):** call `footprint.path_stats(root, mode, rev="v2.14.1")` (`footprint.py:172-194`), or capture `footprint.py --rev v2.14.1 --json`. Keep the `tokens@3.5` / `tokens@2.7` keys labelled as proxies (`footprint.py:107-109`). Never put them in the bytes column.

**Traces (observed):** call `tracecheck.events(path, subagent_dir)` and `tracecheck.successful_reads(evts, main_only=True)` (`tracecheck.py:152-204`) directly. Do not write another JSONL parser. Store `observed` and `declared` lists side by side with a label on each (RESEARCH Pattern 3).

**Output location rule:** nothing goes under `docs/design/b3-ground-truth/` or `docs/design/reachability-dev/`, because `test_replay` pins their census (RESEARCH §Recommended Project Structure).

---

### `docs/design/lean-v2.15/tools/test_baseline_records.py` (re-derive committed evidence + tamper mutant)

**Analog:** `docs/design/freeze-v2.12/tools/test_freeze_manifest.py:628-672` (`verify_self` tamper family)

```python
def test_verify_self_passes_fresh(self):
    self.assertEqual(fm.verify_self(self.fx.repo, self.path), [])

def test_verify_self_tamper_plugin_hash_named(self):
    m = self._load()
    entry = m["plugin"]["files"]["scripts/x.py"]
    entry["sha256"] = ("0" if entry["sha256"][0] != "0" else "1") + entry["sha256"][1:]
    m["manifest_id"] = fm.manifest_id(m)
    self._rewrite(m)
    problems = fm.verify_self(self.fx.repo, self.path)
    self.assertIn("plugin file differs: scripts/x.py", problems)
```
The source pattern is `freeze_manifest.verify_self` (`freeze_manifest.py:1135-1170`): it returns `[]` or one line per difference. Copy that "problems list" return into a `verify_baseline()` that recomputes footprint bytes at `v2.14.1` and the normalised sha256 of each committed record. Mutants: change one byte count, relabel `observed` as `declared`, and edit one character in a record. Each must be named in the problems.

**Environment caveat:** the replay baseline was captured with `transcripts: 12` (primary checkout). A CI linked worktree sees 0. Gate any re-derivation of the replay hash on `IN_LINKED_WORKTREE` the way `test_replay.py:67-68` does, and **do not** silently skip the check. Compare the stored hash text, or use a disclosed `skipIf` with its reason printed, as at `test_replay.py:281`. The plan picks one and states it.
```python
IN_LINKED_WORKTREE = os.path.isfile(os.path.join(REPO_ROOT, ".git"))
EXPECTED_TRANSCRIPTS = 0 if IN_LINKED_WORKTREE else 12
```

---

### `docs/design/lean-v2.15/tools/usage_fields.py` (cost reader, file-I/O batch)

**Analog:** `plugins/vibe-check/scripts/tracecheck.py:152-180` (JSONL main session + `subagents/<stem>.meta.json` → `<stem>.jsonl` linking):
```python
for name in sorted(os.listdir(subagent_dir)):
    if not name.endswith(".meta.json"):
        continue
    with open(os.path.join(subagent_dir, name), encoding="utf-8") as fh:
        try:
            meta = json.load(fh)
        except ValueError:
            meta = None
    side = os.path.join(subagent_dir, name[:-len(".meta.json")] + ".jsonl")
    parent = meta.get("toolUseId") if isinstance(meta, dict) else None
    if not isinstance(parent, str) or not parent or not os.path.isfile(side):
        out.append(("malformed", None, None, {"parent": None}))
        continue
```
Copy the shape. Read the lane from `meta["agentType"]` instead of `toolUseId`. Count a malformed line instead of dropping it. Dedupe by `message.id` (or `requestId`) before summing `usage`. 54-BUDGET §1 used the same rule: "counted once per message" (`54-BUDGET.md:7`). Output: field names, presence counts and aggregates only, each labelled `measured` / `estimated` / `missing`. No dollar column; 54-BUDGET's price table (`:7-14`) is the part **not** to copy. Run with `python3 -I`. Inputs are a fixed path list named in the plan (D-13).

---

### `docs/design/lean-v2.15/tools/test_usage_fields.py` (synthetic fixtures + never-echo)

**Analog:** `plugins/vibe-check/scripts/test_tracecheck.py`

**Synthetic record builder** (`:59-84`): a `Builder` class that appends stream-json dicts, with ids from a counter. Copy it, and add a `usage` dict plus a repeated `message.id` across content blocks so the dedupe mutant has something to trip on.

**Temp-file writer** (`:168-182`):
```python
class TraceCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
    def tearDown(self):
        shutil.rmtree(self._tmp)
    def write(self, records, name="trace.jsonl", raw_lines=()):
        path = os.path.join(self._tmp, name)
        with open(path, "w") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")
```

**Never-echo lock** (`:480-489`). This is the D-10 lock: copy it directly.
```python
def test_never_echo(self):
    sentinel = "SENTINEL-7f3a9c"
    b = passing_builder(3, "review-plain")
    b.read("phases/review/06-config.md", content="secret " + sentinel)
    ...
    self.assertNotIn(sentinel, p.stdout + p.stderr)
```
Mutants: turn off dedupe and the totals double; drop the meta.json and the lane becomes `missing`. **Never commit a real log as a fixture** (D-10).

---

### `.github/workflows/offline-suite.yml` (CI config, event-driven) — NO ANALOG

`.github/` does not exist (`git ls-files | grep -c .github/` = 0). Use RESEARCH §Code Examples verbatim as the starting shape. Conventions to carry over from the repo:
- Suite invocation: `pytest -q -p no:cacheprovider` (`61-RELEASE-RECORD.md:35` G1). Use bare `pytest`, never `python3 -m pytest`.
- Stdlib check run with `python3 -I` (G8, `61-RELEASE-RECORD.md:44`).
- Linked-worktree mode is the suite's own documented "no private transcripts" switch (`test_replay.py:67-68`).
- Stop messages in caps ending `— STOPPING` (RESEARCH §Project Constraints).
- The five deselects are **pending the owner decision** (RESEARCH Open Question 1). Keep `checkpoint:decision` before the workflow is finalised.

---

### `docs/design/lean-v2.15/BASELINE-v2.14.1.md`, `CRITERION.md`, `README.md` (design evidence docs)

**Analog:** `docs/design/prose-diet-footprint-v2.10.md:1-35`
- Bold headline result first (`:3-5`). The owner reads results in plain terms with numbers up front (CONTEXT §Specifics).
- A "How to read this" section that names where every row comes from (the tool and `--rev`), and says which numbers are measured and which are proxies (`:7-31`).
- The "Do not re-run the BEFORE leg" warning (`:18-27`) is the precedent for writing down the replay environment fact (`transcripts: 12`) and the footprint declared-vs-observed caveat.

**Tool-kit README analog:** `docs/design/freeze-v2.12/README.md:1-15`. It has a `| Tool | Job |` table listing every tool in `tools/` with its subcommands. Use it for `docs/design/lean-v2.15/README.md`.

---

### `.planning/phases/62-…/62-COST-NOTE.md` and `62-CI-RECORD.md` (phase records)

- **Cost note:** structure after `54-BUDGET.md:1-20`. It opens with a status line ("Analysis only: no runs started…"), then a "How … was measured" section with **Source**, **Not included** and **Scripts** bullets. Replace the price table with the D-11 field table (field, presence, attribution, consistency, label). The verdict line (go / no-go) goes first.
- **CI record / tree identity:** structure after `61-RELEASE-RECORD.md:7-27`: a precondition line, a `| # | Gate | Requirement | Result | Verdict |` table, then the tree-identity sentence:
  > `git rev-parse 0d2be77:plugins 47978aa:plugins` both `9387dcd…`
  
  Here that becomes `git rev-parse v2.14.1:plugins HEAD:plugins` (both `90e0697…`), plus the red run URL, the phase-branch green URL and `main`'s first green URL from `gh run list … --json databaseId,conclusion,url,headSha`.

## Shared Patterns

### Stdlib-only, explicit import lock per module
**Source:** `test_footprint.py:93-106`; `test_freeze_tally.py:354-365`
**Apply to:** every new `.py` in `.github/scripts/` and `docs/design/lean-v2.15/tools/`. Each tool gets a `TestImportSet` class.

### Every `subprocess.run` has a `timeout`
**Source:** `footprint.py:131-135`; lock at `test_footprint.py:108-119`
**Apply to:** `step_count.py`, `finalize_capture.py`, `baseline_records.py`, `stdlib_only.py` (if it shells out).

### Lock + mutant, with a guard that the mutation really happened
**Source:** `test_finalize_card.py:909-914, 2529-2535`; `test_freeze_tally.py:368-379` (`TestMutants._passes` runs a named test under `mock.patch` and expects it to fail)
**Apply to:** every test file in this phase (the phase-wide rule "Every lock lands with a mutant that trips it").

### Sibling and plugin imports
**Source:** `test_footprint.py:39` (`sys.path.insert(0, dirname(__file__))`); `freeze_tally.py:133-138` (insert `plugins/vibe-check/scripts` only if absent)
**Apply to:** tools that reuse `footprint`, `tracecheck`, `replay`, `carry_state`, `finalize_gate`, `batch_card`.
**Collision rule:** CI runs `plugins/vibe-check/scripts`, `.github/scripts` and `docs/design/lean-v2.15/tools` in **one pytest process** with no `__init__.py` and no conftest. New basenames must not repeat an existing one, or pytest reports an "import file mismatch". Never name a tool `replay.py`, `footprint.py`, `tracecheck.py` or `gitfixture.py`, and never name a test `test_footprint.py` and so on. The proposed names (`stdlib_only`, `step_count`, `finalize_capture`, `baseline_records`, `usage_fields` and their `test_*`) are all free today.

### Read at a pinned revision
**Source:** `footprint.py:121-143` (`git show <rev>:plugins/vibe-check/<rel>`), plus the `test_footprint.py:122-140` independent recompute
**Apply to:** footprint, step-count and capture records. The baseline is pinned to `v2.14.1`, never the worktree.

### Temp resources released on every path
**Source:** `test_finalize_card.py:1992-1993` (`addCleanup(shutil.rmtree, tmp, True)`); `freeze_tally.py:170` (`with tempfile.TemporaryDirectory()`)
**Apply to:** `finalize_capture.py`, all tests, and the CI worktree (`git worktree add` lives in `$RUNNER_TEMP`).

### Nothing private leaves the logs
**Source:** `test_tracecheck.py:480-489` (sentinel never-echo)
**Apply to:** `usage_fields.py`, `baseline_records.py` (trace extraction prints plugin-relative paths only), and the cost note.

### Shell fences
Multi-line shell in plans and records uses `bash -s <<'BASH' … BASH`, because the Bash tool runs zsh (RESEARCH §Code Examples replay fingerprint).

## Conventions

| Axis | Dominant | Share | Entropy | Status |
|---|---|---|---|---|
| file-name casing | snake (`freeze_tally.py`, `test_*.py`) | 100% (15/15) | 0 | named contract |
| identifier casing | Pascal (test classes); functions are snake by inspection | 79% (57/72) | 0.51 | named contract |
| export style | n/a (Python, no exports) | — | — | insufficient data |
| import style | absolute (`py-import-relativity`), explicit (no wildcard) | 100% (15/15, 12/12) | 0 | named contract |

Derived with `gsd-tools verify conventions --derive --scope docs/design/freeze-v2.12/tools`. The `plugins/vibe-check/scripts` scope was skipped (`no-app-files`), but inspection matches: snake_case modules, `test_<module>.py` co-located, `unittest.TestCase`, absolute sibling imports with `# noqa: E402`.

**Contested hotspots (author's choice):** none apply to this repo, which is all Python with no CJS/ESM split. The general rule still holds: match the local directory's style. Plugin `scripts/` tests use an exact `ALLOWED ==` import set (`test_footprint.py:94`). The freeze kit uses a subset with a sibling prefix (`test_freeze_tally.py:364`). New tool kits under `docs/design/` should follow the freeze-kit style.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `.github/workflows/offline-suite.yml` | config | event-driven | No `.github/` in the repo; use RESEARCH §Code Examples (SHA-pinned actions, `fetch-depth: 0`, linked worktree, deselect guard) |
| Red/green CI evidence (inside `62-CI-RECORD.md`) | record | — | No prior CI run exists; follow the `61-RELEASE-RECORD.md` table format only |

## Metadata

**Analog search scope:** `plugins/vibe-check/scripts/` (footprint, tracecheck, replay, gitfixture, test_footprint, test_tracecheck, test_finalize_card), `docs/design/freeze-v2.12/tools/`, `docs/design/*.md`, `.planning/milestones/v2.14-phases/61-…/`, `.planning/milestones/v2.12-phases/54-…/`
**Files scanned:** ~20 read or grepped
**Pattern extraction date:** 2026-11-13
