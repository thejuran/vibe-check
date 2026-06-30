# Phase 30: Config surface foundation - Pattern Map

**Mapped:** 2026-06-30
**Files analyzed:** 7 (2 new + 5 modified)
**Analogs found:** 7 / 7 (every file has a sibling analog in-repo — this is a clone-and-extend phase, not greenfield)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `plugins/vibe-check/scripts/config.py` (NEW) | utility (I/O boundary helper) | file-I/O → transform | `plugins/vibe-check/scripts/score.py` | role-match (same module layout; INVERTED fail posture) |
| `plugins/vibe-check/scripts/test_config.py` (NEW) | test | transform (assertions) | `plugins/vibe-check/scripts/test_score.py` | exact (same unittest harness) |
| `plugins/vibe-check/scripts/score.py` (MODIFY) | utility (pure scorer) | transform (stdin→stdout) | itself — `band_for()` (:86), `run()` (:668) | self (additive envelope key) |
| `plugins/vibe-check/scripts/test_score.py` (MODIFY) | test | transform (assertions) | itself — `TestBandBoundaries` (:86), `TestStableHashGolden` (:1180) | self (new class + regression lock) |
| `plugins/vibe-check/commands/review.md` (MODIFY) | config (orchestrator prose) | request-response (dispatch) | itself — score.py resolution+envelope (:697-743), Selection table (:527), model tiering (:553) | self (parallel wiring) |
| `plugins/vibe-check/commands/deep-review.md` (MODIFY) | config (orchestrator prose) | request-response (dispatch) | itself — top-model resolution (:55) | self (parallel touch) |
| `README.md` (MODIFY) | config (docs) | — | `README.md` `## ⚙️ Configuration` (:59-74) | self (extend existing section) |

**Boundary invariant (D-03):** `config.py` is the ONLY new file allowed filesystem I/O. `score.py` stays pure (import set frozen at `{json, hashlib, re, sys}` by the AST test). Do NOT add `tomllib` to `score.py`.

---

## Pattern Assignments

### `plugins/vibe-check/scripts/config.py` (utility, file-I/O → transform)

**Analog:** `plugins/vibe-check/scripts/score.py`

**(A) Module-doc + constants + pure-helper layout to MIRROR** (score.py lines 1-58). Copy this house style — a triple-quoted module docstring that states the boundary contract and the I/O shape, then a banner-commented constants block, then a banner-commented helpers block:

```python
# score.py:1-17 — module docstring states the boundary + I/O contract up front
"""score.py — the deterministic-core scoring filter for the vibe-check plugin.
...
Pure-function boundary (D-05): the script does NO filesystem, git, or shell-out
I/O. ... Import set is EXACTLY {json, hashlib, re, sys} — nothing else (the AST
import-set test enforces this).

I/O: one JSON envelope on stdin -> one JSON envelope on stdout. The __main__ shim
fails CLOSED ...
"""

# score.py:19-22 — bare stdlib imports, alphabetical, one per line (NO `from x import y` for stdlib)
import hashlib
import json
import re
import sys

# score.py:29-32 — banner-commented constants block (UPPER_SNAKE names)
# --------------------------------------------------------------------------- #
# Constants — ...
# --------------------------------------------------------------------------- #
```

> **config.py's docstring MUST state the INVERTED contract:** score.py's docstring says "fails CLOSED — unparseable stdin propagates"; config.py's must say the opposite — "NEVER raises to the orchestrator; a missing/unparseable/partial config degrades per-key to defaults (CONFIG-03). I/O: reads `$REPO_ROOT/.vibe-check.toml` (the ONE allowed filesystem read); emits `{values, warnings}` JSON on stdout." This is the single most important divergence from the analog.

**(B) Defensive coerce-or-default helper pattern to COPY** (score.py:440-449, `_category_domain`). This is the exact never-raise idiom config.py's per-key validators (`_validate_thresholds`, `_validate_disabled`, `_validate_top_model`) must follow — `isinstance`-guard, return a default + (optionally) a warning, never raise:

```python
# score.py:440-449  — coerce-or-default, never raise
def _category_domain(category):
    """Map a finding's `category` to its coarse domain, or None.

    Defensive (D-02 / Pattern 1): a missing / null / non-str / unknown category
    maps to None (NO domain) rather than raising — a single malformed finding
    must not crash run() ...
    """
    if not isinstance(category, str):
        return None
    return CATEGORY_DOMAIN.get(category)
```

Companion coercion examples in the same file to lean on: `_as_line` (score.py:842-850, int-or-None sentinel), `_safe_window` (score.py:879-894, list-of-str-or-empty — the container+element double guard, directly applicable to validating a `disabled` list whose elements must be strings).

**(C) `__main__` stdin/stdout shim — COPY the SHAPE, INVERT the posture** (score.py:973-983). score.py fails CLOSED; config.py must degrade. Use the shim shape (read stdin/args → `run` → `json.dump` to stdout) but the helper's own logic never raises:

```python
# score.py:973-983 — the shim to mirror STRUCTURALLY (NOT the fail-closed comment)
# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY I/O. Fails CLOSED on bad input (finding #1).
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    envelope = json.load(sys.stdin)   # score.py: deliberately NOT wrapped (propagate)
    result = run(envelope)
    json.dump(result, sys.stdout)
```

> **config.py inversion (Pitfall 4):** config.py's `__main__` takes `$REPO_ROOT` (env var) instead of stdin, calls `load_config(...)` which CANNOT raise, and `json.dump`s `{values, warnings}`. There is no fail-closed propagate here — the helper catches `ImportError` (no tomllib, D-01), `tomllib.TOMLDecodeError`/`OSError` (unparseable/unreadable), and per-key type errors internally. See RESEARCH.md Pattern 2 for the full `load_config` skeleton and Pitfalls 2/3 for `open(path, "rb")` (binary mode REQUIRED) and `tomllib.TOMLDecodeError` (the correct exception, a `ValueError` subclass).

---

### `plugins/vibe-check/scripts/test_config.py` (test)

**Analog:** `plugins/vibe-check/scripts/test_score.py`

**(A) Test-file header + sibling-import bootstrap to COPY** (test_score.py:1-29). This is exactly how a sibling test module resolves its module under test under `python3 -m unittest`:

```python
# test_score.py:16-29 — imports, sys.path bootstrap, module-under-test import, file path const
import ast
import os
import sys
import unittest

# Make `import score` resolve when unittest discovery runs from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import score  # noqa: E402  (sibling module under test)

SCORE_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "score.py")
```

> For `test_config.py`: `import config` + `CONFIG_PY = os.path.join(...)`. Importing `os`/`ast`/`tempfile`/`subprocess` in the TEST file is FINE (test_score.py:12-13 explicitly scopes the import ban to score.py only).

**(B) `unittest.TestCase` class structure to MIRROR** (test_score.py:86-111, `TestBandBoundaries`) — one class per behavior cluster, one `assertEqual` per boundary, descriptive `test_<condition>_is_<expected>` names:

```python
# test_score.py:86-111 — boundary-table test class shape
class TestBandBoundaries(unittest.TestCase):
    def test_95_is_critical(self):
        self.assertEqual(score.band_for(95), "critical")
    def test_94_is_warning(self):
        self.assertEqual(score.band_for(94), "warning")
    def test_70_is_medium(self):
        self.assertEqual(score.band_for(70), "medium")
    def test_69_is_below_both_thresholds(self):
        self.assertIsNone(score.band_for(69))
```

> `test_config.py` mirrors this with `class TestFailSafe` (absent/unparseable/bad-key/no-tomllib branches), `class TestPrecedence` (flag>toml>default), per RESEARCH.md Validation Architecture's Test→Req map.

**(C) AST import-ban test to ADAPT (optional hardening, A4)** (test_score.py:1207-1262, `TestImportSet`). This is the pattern that FORCES config.py to be a separate module. For config.py the ban is LOOSER (tomllib + os.path ARE allowed); reuse the AST-walk machinery but swap the allowlist/forbidden set to pin config.py's I/O surface (e.g. forbid `subprocess`/`os.system`/`eval`/`exec`), NOT the score.py `{json,hashlib,re,sys}` set:

```python
# test_score.py:1207-1231 — the AST-walk import-set guard (machinery to reuse)
class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "hashlib", "re", "sys"}      # config.py: widen to add tomllib, os, json, sys
    def _tree(self):
        with open(SCORE_PY, "r", encoding="utf-8") as fh:
            return ast.parse(fh.read())
    def test_import_set_subset_of_allowed(self):
        tree = self._tree()
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        self.assertTrue(imported.issubset(self.ALLOWED), ...)
```

> **Do NOT extend score.py's existing `TestImportSet.ALLOWED`** — that test must keep enforcing `{json,hashlib,re,sys}` on score.py unchanged. Any config.py guard is a NEW, SEPARATE test class with its own allowlist.

**(D) subprocess fail-mode test for the `__main__` shim** (test_score.py:1268-1289, `TestFailClosed`). config.py's analog test asserts the OPPOSITE: a broken/missing config makes the process exit ZERO with defaults, never non-zero:

```python
# test_score.py:1272-1279 — subprocess invocation of the shim (shape to reuse, ASSERTION inverted)
proc = subprocess.run([sys.executable, SCORE_PY], input=b"not json",
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
self.assertNotEqual(proc.returncode, 0)   # config.py test: assertEqual(rc, 0) — degrade, never abort
```

---

### `plugins/vibe-check/scripts/score.py` (utility, transform) — MODIFY

**Analog:** itself — the additive-envelope-key idiom at `run()` (score.py:682-686) and the single `band_for` call site (score.py:810).

**(A) `band_for()` — parameterize from hardcoded literals to an optional `thresholds` arg** (score.py:86-94, the CURRENT version):

```python
# score.py:86-94 — CURRENT (the literals thresholds parameterizes)
def band_for(score):
    """Score -> band (scoring.md:37-42). <70 is below both thresholds => None."""
    if score >= 95:
        return "critical"
    if score >= 80:
        return "warning"
    if score >= 70:
        return "medium"
    return None
```

> Replace with the default-inert parameterized form (RESEARCH.md Pattern 1): add a module constant `_DEFAULT_BANDS = {"critical": 95, "warning": 80, "medium": 70}` (alongside the existing constants block, score.py:29-53) and `def band_for(score, thresholds=None):` defaulting the WHOLE set to today's literals. **D-02 byte-stability:** `band_for(s) == band_for(s, None) == band_for(s, _DEFAULT_BANDS)` for every score. The exact sub-key→boundary mapping + monotonicity validation is the PLANNER's call (CONTEXT.md Discretion; RESEARCH.md Pattern 1 "Open design question" + the recommended 3-sub-key strict-monotonic-descent starting point).

**(B) `run()` — consume `thresholds` via the EXISTING `envelope.get(key, default)` idiom** (score.py:682-686, the template to copy):

```python
# score.py:682-686 — the additive-envelope-key default idiom thresholds MUST follow
command = envelope.get("command", "review")
all_mode = bool(envelope.get("all_mode", False))
changed_line_ranges = envelope.get("changed_line_ranges", {}) or {}
reviewed_union = set(envelope.get("reviewed_union", []) or [])
file_line_totals = envelope.get("file_line_totals", {}) or {}
# → ADD, same shape: thresholds = envelope.get("thresholds")  # None absent → band_for uses literals
```

**(C) Thread it to the SINGLE `band_for` call site** (score.py:810 — the ONLY place bands are written, the single-writer invariant):

```python
# score.py:808-816 — the single band write; thread `thresholds` into THIS call only
survivor = dict(best_member)
survivor["orchestrator_score"] = best_score
survivor["band"] = band_for(best_score)              # → band_for(best_score, thresholds)
survivor["attribution"] = attribution
survivor["stable_hash"] = stable_hash(...)
```

> **Anti-pattern (RESEARCH.md):** do NOT compute bands anywhere else. `band_for` is called in EXACTLY one place (verified: def at :86, call at :810). `thresholds` flows through that one call so `score.py` stays the single writer of `band`. `stable_hash` (score.py:59-83, GOLDEN_DIGEST-locked) is UNTOUCHED.

---

### `plugins/vibe-check/scripts/test_score.py` (test) — MODIFY

**Analog:** itself — `TestBandBoundaries` (:86-111), `TestStableHashGolden` (:1180-1201), the `GOLDEN_DIGEST` constant (:37), and the `TestRunEndToEnd._envelope` fixture (:1296-1309).

**(A) KEEP the existing regression locks GREEN, UNCHANGED:**

```python
# test_score.py:37 — the frozen digest; MUST NOT be re-pinned (keys persisted dismissals, Pitfall 1)
GOLDEN_DIGEST = "7a516d0120c0ff3110198c731f49a775d55dd06071e1831e4a554c7bff793124"
```

The 8 `TestBandBoundaries` assertions (test_score.py:87-111) and `TestStableHashGolden.test_golden_digest_frozen` (:1181-1189) are the byte-stability lock — they must stay green with the parameterized `band_for` (because the default path is unchanged).

**(B) ADD a `TestThresholdsOverride` class** (model it on `TestBandBoundaries`, :86-111): assert a non-default `thresholds` arg moves the band (e.g. `band_for(82, {"critical": 80, "warning": 70, "medium": 60}) == "critical"`).

**(C) ADD a default-byte-stable regression case** proving parameterization is inert when absent — model on the boundary assertions:

```python
# new — proves the parameterized default == today's literals (D-02 byte-stability)
def test_default_arg_matches_no_arg(self):
    for s in (0, 69, 70, 79, 80, 94, 95, 100):
        self.assertEqual(score.band_for(s), score.band_for(s, None))
```

**(D) ADD a zero-config `run()` envelope test** — model on `TestRunEndToEnd` (:1295-1366); assert an envelope with NO `thresholds` key produces the same survivor `band`/`orchestrator_score`/`stable_hash` as before:

```python
# test_score.py:1296-1309 — the run() envelope fixture to clone for the no-thresholds-key case
def _envelope(self, **over):
    base = {"command": "review", "all_mode": False, "pass_number": 1,
            "changed_line_ranges": {"src/a.py": [[8, 14]]}, "carryforward": [],
            "findings": [make_finding(id="keep-1", agent_confidence=85, ...)]}
    base.update(over)
    return base
```

---

### `plugins/vibe-check/commands/review.md` (config, request-response) — MODIFY

**Analog:** itself — four distinct in-file idioms to mirror.

**(A) Dev-safe helper resolution — COPY the ORDER, INVERT the terminal posture** (review.md:697-722, the `$SCORE_PY` resolution). Reuse the working-tree-first / cache-glob / marketplace fallback chain verbatim, substituting `config.py` for `score.py`, BUT change the final arm from `exit 1` to degrade-to-no-config (Pitfall 4):

```bash
# review.md:702-721 — the resolution ORDER to clone for $CONFIG_PY (terminal posture DIFFERS)
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
SCORE_PY=""
if [ -n "$REPO_ROOT" ] && [ -f "$REPO_ROOT/plugins/vibe-check/scripts/score.py" ]; then
  SCORE_PY="$REPO_ROOT/plugins/vibe-check/scripts/score.py"
fi
# (2) FALLBACK — newest versioned plugin cache
if [ -z "$SCORE_PY" ]; then
  SCORE_ROOT=$(ls -d "$HOME"/.claude/plugins/cache/thejuran/vibe-check/*/ 2>/dev/null | sort -V | tail -1)
  SCORE_ROOT="${SCORE_ROOT%/}"
  [ -n "$SCORE_ROOT" ] && [ -f "$SCORE_ROOT/scripts/score.py" ] && SCORE_PY="$SCORE_ROOT/scripts/score.py"
fi
# (3) FALLBACK — marketplace install. (4) FAIL CLOSED — none resolved:
if [ -z "$SCORE_PY" ]; then
  echo "score.py not found ... review HALTED." >&2
  exit 1                       # ← for $CONFIG_PY: do NOT exit 1 — degrade to no-config (all defaults)
fi
```

> **Pitfall 4 (load-bearing):** the scorer is mandatory (no scoring → no honest report → fail closed); the config reader is OPTIONAL (no config → v2.7 behavior). A missing `$CONFIG_PY` must NOT abort — set empty resolved values + optionally one warning, and continue.

**(B) Compound-Bash invocation — MIRROR the heredoc / capture-to-var shape** (review.md:187 for the env-var-in/stdout-out heredoc idiom; review.md:727-731 for the resolved-file invocation shape). config.py is a real file (like score.py), so invoke the resolved `$CONFIG_PY` with env-var input, NOT an inline heredoc:

```bash
# review.md:187 — the env-var-in / stdout-captured-to-var / no-temp-file heredoc idiom
REAL=$(ROOT="$ROOT" LP="$LITERAL_PREFIX" python3 - <<'PY' 2>/dev/null
import os, sys
...
PY
)
# review.md:729 — invoking a RESOLVED script file (the shape config.py uses)
SCORED=$(printf '%s' "$FINDINGS_ENVELOPE_JSON" | python3 "$SCORE_PY")
# → config: CONFIG_JSON=$(REPO_ROOT="$REPO_ROOT" python3 "$CONFIG_PY")  # prints {values,warnings}
```

> Do NOT add `python3` to frontmatter `allowed-tools` — it runs under the existing compound-Bash convention (review.md:724 states this explicitly).

**(C) Pass `thresholds` into the score.py envelope** — extend the envelope-build keys (review.md:724-726). Add `thresholds` to the JSON object alongside `command`/`all_mode`/`changed_line_ranges`/etc., sourced from the parsed `CONFIG_JSON`. Inject today's literals as the default (or omit when absent) so a zero-config run stays byte-identical (Anti-pattern: never inject a NON-default `thresholds` on a zero-config run).

**(D) `disabled` agents — enforce at the Selection table BEFORE dispatch** (review.md:527-547):

```
# review.md:529-545 — the Selection table; remove `disabled` rows BEFORE the Phase-2 fan-out
| Always | Condition | Agent |
| ✓ | — | `bugs` |
| ✓ | — | `security` |
|  | `.py` in diff | `language-python` |
|  | triage.frameworks includes "react" | `framework-react` |
...
```

> Subtract the `disabled` roster from the selected agents before the "Dispatching N agents" announcement (review.md:547). **Pitfall 5:** `bugs`/`security` are the two always-on agents (rows :531-532) — decide the policy (honor-with-config-health-note recommended) and surface it on the config-health line so disabling a core agent is never silent ("never silently drop").

**(E) `top_model` — enforce at model resolution alongside `$VIBE_CHECK_TOP_MODEL`** (review.md:549-553). `/review` uses no top tier today (:551), so the live precedence lives in deep-review.md — but document the env>toml>default order here too for consistency. The validated allowlist is opus/fable (see deep-review.md:55 below).

**(F) Config-health warning block near the top of the Phase-4 report** (D-04). Render the collected `warnings[]` from `CONFIG_JSON` as ONE aggregated block near the report header (the `## Code Review` header region, review.md Phase 4). An absent file produces NO warning (CONFIG-01 silence). **Security note (RESEARCH.md V5):** warnings name the KEY + a fixed reason string — do NOT echo raw config-supplied value text verbatim into the report (mirrors the "treat agent text as inert display" posture).

---

### `plugins/vibe-check/commands/deep-review.md` (config, request-response) — MODIFY

**Analog:** itself — the top-model resolution at deep-review.md:55.

**(A) `top_model` parallel touch — reuse the EXISTING opus/fable validation + fallback** (deep-review.md:55, the authoritative validation site):

```
# deep-review.md:55 — the existing $VIBE_CHECK_TOP_MODEL resolution + allowlist + fallback to mirror
**Top-tier model resolution (do this first, once per run).** Read the env var
$VIBE_CHECK_TOP_MODEL. If set to a non-empty value, that is <TOP> (e.g. fable).
If unset or empty, <TOP> defaults to opus. ... Only opus and fable are supported
values; if it's set to anything else, fall back to opus and tell the user once:
"⚠ Unrecognized $VIBE_CHECK_TOP_MODEL — using opus." Do NOT print anything when
it resolves normally.
```

> **Pitfall 6 + Precedence (A2):** extend this block so the resolution becomes env > toml(`top_model`) > default(`opus`), reusing the SAME opus/fable allowlist + fallback-to-opus + one-time-warning so the two precedence sources can't diverge. A bogus `top_model` toml value falls back to opus with a warning, exactly like a bogus env var.

**(B) `disabled` parallel touch** — deep-review.md owns its own agent-selection "Differences" table (deep-review.md:57-77). Apply the `disabled` subtraction there too (it adds `architecture`/`impact`/`test-sufficiency` rows :61-63). `thresholds` is INHERITED via review.md delegation (deep-review.md step 7, :41 — deep runs review.md's Phase 3 verbatim), so NO `thresholds` edit is needed here.

> **Open Question 3 (RESEARCH.md):** confirm during planning by reading deep-review.md's model-resolution (:55) and Selection table (:57-77) — `thresholds` review.md-only; `top_model`/`disabled` touch BOTH command files.

---

### `README.md` (config, docs) — MODIFY

**Analog:** the existing `## ⚙️ Configuration` section (README.md:59-74).

**(A) Extend the existing Configuration section** — it already documents `VIBE_CHECK_TOP_MODEL` as a table (README.md:63-65). CONFIG-04 adds the `.vibe-check.toml` schema doc under this same section:

```markdown
# README.md:59-74 — the existing Configuration section + env-var table to EXTEND
## ⚙️ Configuration

The plugin works out of the box with no configuration. ...

| Env var | Default | Values | Effect |
|---|---|---|---|
| `VIBE_CHECK_TOP_MODEL` | `opus` | `opus`, `fable` | Model used for the `bugs` + `architecture` agents in `/deep-review`. |
```

> Add a `.vibe-check.toml` schema subsection documenting the three Phase-30 keys (`thresholds`, `disabled`, `top_model`) with defaults + the zero-config back-compat note (absent file = v2.7 behavior, no warning). Format is the PLANNER's call (CONTEXT.md Discretion). Note the env>toml>default precedence for `top_model` so the two surfaces are documented coherently.

---

## Shared Patterns

### Defensive coerce-or-default (never-raise) — the milestone keystone
**Source:** `score.py:440-449` (`_category_domain`), `score.py:842-850` (`_as_line`), `score.py:879-894` (`_safe_window`)
**Apply to:** every per-key validator in `config.py` (CONFIG-03 per-key fail-safe)
`isinstance`-guard the value, return a default (+ warning) on any type/range/allowlist violation, NEVER raise. This is the proven house idiom; config.py's `_validate_thresholds`/`_validate_disabled`/`_validate_top_model` are direct applications. `_safe_window`'s container+element double-guard (:879-894) maps directly to validating a `disabled` list whose elements must each be strings.

### Additive envelope key with `envelope.get(key, default)`
**Source:** `score.py:682-686`
**Apply to:** `score.py` `run()` consuming `thresholds`; `review.md` envelope build (:724-726)
A new key is read with a default so an absent key reproduces prior behavior byte-for-byte. The diff-mode envelope shape stays back-compatible (CONFIG-01).

### Dev-safe script resolution (working-tree → cache → marketplace)
**Source:** `review.md:697-722`
**Apply to:** `$CONFIG_PY` resolution in `review.md` — **but invert the terminal arm** (degrade, not `exit 1`; Pitfall 4)
Reuse the resolution ORDER; the config reader is optional where the scorer is mandatory.

### Compound-Bash heredoc / capture-to-var invocation
**Source:** `review.md:187` (env-var-in/stdout-out heredoc), `review.md:729` (resolved-file invocation)
**Apply to:** invoking `$CONFIG_PY` from `review.md`
No temp file, no `allowed-tools` change; env var in, JSON on stdout captured to a shell var.

### opus/fable allowlist + fallback-to-opus + one-time warning
**Source:** `deep-review.md:55`
**Apply to:** `top_model` toml validation in BOTH command files (Pitfall 6)
Reuse the exact allowlist so the env var and toml key can't diverge; bogus value → opus + warning.

### "Never silently drop" — loud-but-non-fatal
**Source:** the project principle, embodied in `score.py`'s `filtered[]` routing (`_route_malformed`, score.py:726-732) and the missing-config→defaults posture
**Apply to:** the config-health warning block (D-04) and the `disabled`-core-agent note (Pitfall 5)
A misconfiguration is surfaced, never swallowed; an absent file is silent (CONFIG-01).

---

## Conventions

Convention derivation via `gsd-tools.cjs verify conventions --derive` was **skipped** (`reason: no-readable-files` at all scopes — the tool does not recognize this repo's markdown-orchestrator + Python-scripts layout). The four axes below are derived manually from the `plugins/vibe-check/scripts/` directory (internally consistent across `score.py` + `test_score.py`), which is the subtree both new files (`config.py`, `test_config.py`) join.

| Axis | Dominant | Share | Entropy | Status |
|------|----------|-------|---------|--------|
| File-name casing | `snake_case.py` (`score.py`, `test_score.py`; tests `test_<module>.py`) | 100% | low | named contract |
| Identifier casing | `snake_case` functions, `_leading_underscore` private helpers, `PascalCase` `unittest.TestCase` classes, `UPPER_SNAKE` module constants | 100% | low | named contract |
| Export / module style | Python module: top-level `def`/class + `if __name__ == "__main__":` stdin/stdout (or env-var) shim; one JSON object out | 100% (within scripts/) | low | named contract |
| Import style | bare stdlib `import x`, one per line, alphabetical, at top of file (NO `from x import y` for stdlib in `score.py`) | 100% (score.py) | low | named contract |

All four axes are **named contracts** (≥70% dominance) within `plugins/vibe-check/scripts/` — `config.py`/`test_config.py` MUST match: `snake_case.py` filenames, `snake_case`/`PascalCase`/`UPPER_SNAKE` identifiers, the `__main__` shim shape, and alphabetical bare-stdlib imports. The ONE deliberate widening: `config.py` adds `tomllib` + `os.path` to its import set (the I/O boundary is its whole purpose) — this does NOT contest the import-style axis (still bare `import x`, alphabetical); it only widens score.py's frozen `{json,hashlib,re,sys}` allowlist, which is enforced per-file by separate AST tests, not shared.

**Contested hotspots (author's choice):** This repo's prototype intentional-contested split is the **CJS↔SDK dual resolver** — `bin/lib/**` is CommonJS (`module.exports`/`require`) while `sdk/src/**` is ESM (`export`/`import`); each half is internally consistent per-directory and contested only repo-wide. Phase 30 does not touch either of those trees, but the principle governs here too: **match the directory's local style.** The `plugins/vibe-check/scripts/` directory is uniformly Python-stdlib — there is no contested hotspot inside this phase's blast radius, so follow the `score.py`/`test_score.py` conventions above without deviation.

---

## No Analog Found

None. Every file in this phase has a direct in-repo sibling analog — this is a clone-and-extend phase. The one genuinely NEW capability (reading `.vibe-check.toml` via `tomllib`) is built by combining existing idioms (the score.py module layout + the defensive-coercion helpers + the dev-safe resolution), so even `config.py` has a strong structural analog (`score.py`) — it inverts the fail posture rather than inventing a new pattern.

## Metadata

**Analog search scope:** `plugins/vibe-check/scripts/` (score.py, test_score.py), `plugins/vibe-check/commands/` (review.md, deep-review.md), `README.md`
**Files scanned:** 6 (score.py 983L, test_score.py 2076L, review.md 977L, deep-review.md 372L, README.md 258L, + CONTEXT/RESEARCH)
**Pattern extraction date:** 2026-06-30
**Conventions tool:** `gsd-tools.cjs` 4.0.1 — `verify conventions --derive` returned `skipped: no-readable-files` (all scopes); conventions derived manually from the scripts/ subtree
