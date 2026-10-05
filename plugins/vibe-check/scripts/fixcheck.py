"""fixcheck.py — the fix agent's real check: pick it, baseline it, re-run it.

## Purpose (D-03)

"Verified" must mean that something real ran. For each file a fix touches,
this module picks the cheapest RELEVANT automated check from a fixed
allowlist, runs it once BEFORE the edit (baseline) and once AFTER, and reports
which check ran together with the owner-facing label. The fix agent keeps the
semantic re-check of the cited condition (model judgement); this module only
supplies the automated check and its honest label.

## The allowlist (strongest first)

    test       .py: sibling `test_<stem>.py` / `<stem>_test.py`, `tests/test_<stem>.py`
                    walking up to the root, or the file itself when it is a test;
                    runner `<root>/.venv/bin/pytest`, else `pytest` on PATH
               .ts/.tsx/.js/.jsx: `<stem>.test.*` / `<stem>.spec.*` / `__tests__/<stem>.*`;
                    runner `<root>/node_modules/.bin/vitest` (run) or `jest` only
               .go: `<stem>_test.go` -> `go test ./<pkgdir>`
    typecheck  `<root>/node_modules/.bin/tsc --noEmit -p <nearest tsconfig.json>`;
               `go vet ./<pkgdir>`
    lint       `<root>/node_modules/.bin/eslint <file>`; `ruff check` / `flake8`
               only when on PATH AND the repo carries that tool's config
    syntax     .py in-process ast.parse (nothing written, unlike py_compile);
               .json in-process json.loads; .sh `bash -n`; .js `node --check`
    none       anything else

## The baseline rule

A check that is already red before the fix proves nothing about the fix. On
this machine `python3 -m pytest` fails outright ("No module named pytest"), so
an unbaselined check would wrongly undo good fixes. `baseline` therefore runs
each available candidate BEFORE the edit and keeps the first that passes; a
red or timed-out candidate is skipped (the walk ends at `none`, labelled
"already failing"), and a candidate that cannot run at all is simply
unavailable. Only the kept check judges the fix in `after`.

## Attempt scoping

A baseline belongs to exactly one fix attempt (the 32-hex id from
`fixstage.py begin`). `baseline` discards a record written under any other
attempt (an interrupted earlier run) before walking; `after` refuses one
(exit 2, fail closed). A stale record can never judge a fresh attempt.

## Security posture

The command is never built from finding text: the finding record is a JSON
file (FL-03, see fixcommit.py), every path in it is validated by
`fixcommit.validate_paths` (pre-filter + guard containment), and every check
is an argv list from the fixed shapes above, run with no shell. Binaries are
repo-local (`.venv/bin`, `node_modules/.bin`) or one of the fixed PATH names
in PATH_RUNNERS. A package-runner that downloads and executes packages on
demand is deliberately absent from the allowlist. A timeout kills the whole
process group, so a runner's children die with it.

## CLI and exit codes

    pick     --root R --path P                    (diagnostic, trusted caller)
        0 JSON list of available candidates, strongest first | 1 refused | 2 usage
    baseline --root R --finding-json J --attempt A
        0 one-line JSON summary | 1 refused | 2 usage
    after    --root R --finding-json J --attempt A
        0 outcome passed|not-run | 1 outcome failed|timeout|unavailable
        | 2 usage, no baseline record, or a record from another attempt

The fix agent must give the Bash call that runs `baseline` or `after` a
300000 ms timeout: a single check may take up to 120 s.

I/O: imports {ast, json, os, re, shutil, signal, subprocess, sys} plus the
sibling fixcommit; writes only `<root>/.turingmind/fixcheck/<id>.json`.
"""

import ast  # noqa: F401  (in-process syntax parse)
import json
import os
import re
import shutil
import signal  # noqa: F401  (process-group kill on timeout)
import subprocess  # noqa: F401  (argv-only check runs)
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixcommit  # noqa: E402  (the ONE path-validation source)

KIND_ORDER = ("test", "typecheck", "lint", "syntax", "none")

# The only bare names ever resolved on PATH. Everything else is repo-local.
PATH_RUNNERS = ("pytest", "go", "ruff", "flake8", "bash", "node")

LABEL_NONE = "problem re-checked; no automated check available"
LABEL_SYNTAX = "syntax check only"
LABEL_NONE_ALREADY_FAILING = (LABEL_NONE + " (the existing check was already "
                              "failing before the fix)")

JS_EXTS = (".ts", ".tsx", ".js", ".jsx")
TS_EXTS = (".ts", ".tsx")
JS_TEST_RE = re.compile(r"\.(test|spec)\.(ts|tsx|js|jsx)$")

ID_RE = re.compile(r"^[0-9a-f]{8,64}$")
ATTEMPT_RE = re.compile(r"^[0-9a-f]{32}$")

RESERVED_TOP = (".git", ".turingmind")


class Refused(Exception):
    """A fixed, printable refusal reason (exit 1)."""


# ---------------------------------------------------------------- picking

def _exec_ok(abspath):
    return os.path.isfile(abspath) and os.access(abspath, os.X_OK)


def _on_path(name):
    if name not in PATH_RUNNERS:  # the fixed set is the whole allowlist
        return False
    return shutil.which(name) is not None


def _local_bin(root, rel):
    """Absolute path of a repo-local executable, or None."""
    p = os.path.join(root, rel)
    return p if _exec_ok(p) else None


def _isfile(root, rel):
    return os.path.isfile(os.path.join(root, rel))


def _join(*parts):
    return "/".join(p for p in parts if p not in ("", "."))


def _display(root, argv):
    words = list(argv)
    if words and os.path.isabs(words[0]) and words[0].startswith(root + os.sep):
        words[0] = os.path.relpath(words[0], root)
    return " ".join(words)


def _ext_cand(root, kind, argv, target):
    return {"kind": kind, "argv": argv, "display": _display(root, argv),
            "inproc": None, "target": target}


def _inproc_cand(kind_inproc, target):
    display = "python ast parse" if kind_inproc == "ast" else "json parse"
    return {"kind": "syntax", "argv": None, "display": display,
            "inproc": kind_inproc, "target": target}


def _dirs_up(root, d):
    """d, its parent, ... up to the root ('' == root), all repo-relative."""
    out = []
    while True:
        out.append(d)
        if d in ("", "."):
            return out
        d = os.path.dirname(d)


def _py_test_file(root, path):
    d, name = os.path.split(path)
    stem = name[:-3]
    if stem.startswith("test_") or stem.endswith("_test"):
        return path
    for cand in (_join(d, "test_%s.py" % stem), _join(d, "%s_test.py" % stem)):
        if _isfile(root, cand):
            return cand
    for up in _dirs_up(root, d):
        cand = _join(up, "tests", "test_%s.py" % stem)
        if _isfile(root, cand):
            return cand
    return None


def _pytest_runner(root):
    local = _local_bin(root, ".venv/bin/pytest")
    if local:
        return local
    if _on_path("pytest"):
        return "pytest"
    return None


def _py_lint(root, path):
    cands = []
    if _on_path("ruff") and _ruff_config(root):
        cands.append(_ext_cand(root, "lint", ["ruff", "check", path], path))
    if _on_path("flake8") and _flake8_config(root):
        cands.append(_ext_cand(root, "lint", ["flake8", path], path))
    return cands


def _read_text(root, rel):
    try:
        with open(os.path.join(root, rel), "r", encoding="utf-8",
                  errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _ruff_config(root):
    if _isfile(root, "ruff.toml") or _isfile(root, ".ruff.toml"):
        return True
    return "[tool.ruff" in _read_text(root, "pyproject.toml")


def _flake8_config(root):
    if _isfile(root, ".flake8"):
        return True
    return "[flake8]" in _read_text(root, "setup.cfg")


def _pick_python(root, path):
    cands = []
    test = _py_test_file(root, path)
    runner = _pytest_runner(root)
    if test and runner:
        cands.append(_ext_cand(root, "test", [
            runner, "-q", "-x", "-p", "no:cacheprovider", test], test))
    cands.extend(_py_lint(root, path))
    cands.append(_inproc_cand("ast", path))
    return cands


def _js_test_file(root, path):
    d, name = os.path.split(path)
    if JS_TEST_RE.search(name) or os.path.basename(d) == "__tests__":
        return path
    stem = os.path.splitext(name)[0]
    exts = [e.lstrip(".") for e in JS_EXTS]
    for e in exts:
        for cand in (_join(d, "%s.test.%s" % (stem, e)),
                     _join(d, "%s.spec.%s" % (stem, e)),
                     _join(d, "__tests__", "%s.%s" % (stem, e)),
                     _join(d, "__tests__", "%s.test.%s" % (stem, e))):
            if _isfile(root, cand):
                return cand
    return None


def _nearest_tsconfig(root, path):
    for up in _dirs_up(root, os.path.dirname(path)):
        cand = _join(up, "tsconfig.json")
        if _isfile(root, cand):
            return cand
    return None


def _pick_js(root, path, ext):
    cands = []
    test = _js_test_file(root, path)
    if test:
        vitest = _local_bin(root, "node_modules/.bin/vitest")
        jest = _local_bin(root, "node_modules/.bin/jest")
        if vitest:
            cands.append(_ext_cand(root, "test", [vitest, "run", test], test))
        elif jest:
            cands.append(_ext_cand(root, "test", [jest, test], test))
    if ext in TS_EXTS:
        tsc = _local_bin(root, "node_modules/.bin/tsc")
        tsconfig = _nearest_tsconfig(root, path)
        if tsc and tsconfig:
            cands.append(_ext_cand(root, "typecheck",
                                   [tsc, "--noEmit", "-p", tsconfig], tsconfig))
    eslint = _local_bin(root, "node_modules/.bin/eslint")
    if eslint:
        cands.append(_ext_cand(root, "lint", [eslint, path], path))
    if ext == ".js" and _on_path("node"):
        cands.append(_ext_cand(root, "syntax", ["node", "--check", path], path))
    return cands


def _pick_go(root, path):
    if not _on_path("go"):
        return []
    d, name = os.path.split(path)
    pkg = "./" + d if d else "."
    cands = []
    stem = name[:-3]
    if stem.endswith("_test") or _isfile(root, _join(d, stem + "_test.go")):
        cands.append(_ext_cand(root, "test", ["go", "test", pkg], path))
    cands.append(_ext_cand(root, "typecheck", ["go", "vet", pkg], path))
    return cands


def pick_checks(root, path):
    """Available candidate checks for `path`, strongest first ([] == none).

    `root` must be the repo's real path and `path` a validated repo-relative
    path; nothing here comes from finding text other than that path.
    """
    ext = os.path.splitext(path)[1]
    if ext == ".py":
        return _pick_python(root, path)
    if ext in JS_EXTS:
        return _pick_js(root, path, ext)
    if ext == ".go":
        return _pick_go(root, path)
    if ext == ".sh":
        if _on_path("bash"):
            return [_ext_cand(root, "syntax", ["bash", "-n", path], path)]
        return []
    if ext == ".json":
        return [_inproc_cand("json", path)]
    return []


def label_for(kind, command, already_failing):
    """The owner-facing label for a check kind (D-06, D-15)."""
    if kind in ("test", "typecheck", "lint"):
        return "verified by `%s`" % command
    if kind == "syntax":
        return LABEL_SYNTAX
    if already_failing:
        return LABEL_NONE_ALREADY_FAILING
    return LABEL_NONE


# ---------------------------------------------------------------- validation

def _validate_paths(root, paths):
    """fixcommit.validate_paths plus normal form and reserved-directory checks."""
    ok, reason = fixcommit.validate_paths(root, paths)
    if not ok:
        raise Refused(reason)
    for path in paths:
        if os.path.normpath(path) != path:
            raise Refused("refused: path is not in normal form")
        if path.split("/", 1)[0].lower() in RESERVED_TOP:
            raise Refused("refused: path is inside a reserved directory")


def _check_root(root):
    if not isinstance(root, str) or not root or not os.path.isdir(root):
        raise Refused("refused: root is not an existing directory")
    return os.path.realpath(root)


# ---------------------------------------------------------------- CLI

SUBCOMMAND_FLAGS = {
    "pick": ("--root", "--path"),
}

USAGE = "usage: fixcheck.py pick --root <repo> --path <p>\n"


def parse_argv(argv):
    """Hand-rolled (fixcommit shape) -> ((subcommand, values), None) or (None, err)."""
    if not argv:
        return None, "missing subcommand\n"
    sub = argv[0]
    if sub not in SUBCOMMAND_FLAGS:
        return None, "unknown subcommand: %s\n" % sub
    allowed = SUBCOMMAND_FLAGS[sub]
    values = {}
    rest = argv[1:]
    i = 0
    while i < len(rest):
        token = rest[i]
        if token not in allowed:
            return None, "unrecognized arguments: %s\n" % token
        if i + 1 >= len(rest):
            return None, "argument %s: expected one argument\n" % token
        if token in values:
            return None, "argument %s: given more than once\n" % token
        values[token] = rest[i + 1]
        i += 2
    missing = [f for f in allowed if f not in values]
    if missing:
        return None, ("the following arguments are required: %s\n"
                      % ", ".join(missing))
    return (sub, values), None


def cmd_pick(root, path):
    _validate_paths(root, [path])
    sys.stdout.write(json.dumps(pick_checks(root, path)) + "\n")
    return 0


def run(argv):
    parsed, err = parse_argv(argv)
    if err is not None:
        sys.stderr.write(USAGE)
        sys.stderr.write(err)
        return 2
    sub, values = parsed
    try:
        root = _check_root(values["--root"])
        return cmd_pick(root, values["--path"])
    except Refused as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
