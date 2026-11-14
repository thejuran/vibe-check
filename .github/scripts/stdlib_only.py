"""Stdlib-only import gate for the vibe-check plugin tree.

The plugin promises to run on a stock Python with nothing installed, so every
module it ships may import only the standard library and its own sibling
modules. This script parses each shipped module and names any other import.

Scope: every `*.py` under the given plugin root whose basename does not start
with `test_` (33 files at 2.14.1). `scripts/gitfixture.py` is included: it is
installed with the plugin, so a third-party import there breaks an install like
any other shipped module. `test_*.py` files are excluded because the plugin
never runs them at runtime. `__pycache__` folders are skipped.

Allowed top-level imports: `sys.stdlib_module_names` plus the basename of every
`.py` file found under the root (sibling modules). Relative imports
(`from . import x`) are local by construction and are not checked.

Known limit: imports made through `importlib` or `__import__` strings are not
detected; only `import` and `from ... import` statements are inspected.

I/O: stdlib only, imports exactly {ast, os, sys}. CLI:

    python3 -I .github/scripts/stdlib_only.py <plugin root>

Exit codes: 0 clean (prints the file count), 1 a third-party import was found
(each file and module is named), 2 usage error or unusable input (missing
root, no shipped files, a file that cannot be read or parsed).
"""

import ast
import os
import sys


class UnusableInput(Exception):
    pass


def stdlib_names():
    """The standard-library top-level module names for this interpreter."""
    return frozenset(sys.stdlib_module_names)


def _shipped_files(root):
    found = []
    every_py = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            every_py.append(rel)
            if not name.startswith("test_"):
                found.append(rel)
    return sorted(found), every_py


def _imports(path):
    try:
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise UnusableInput("CANNOT READ %s (%s)" % (path, type(exc).__name__))
    try:
        tree = ast.parse(source, filename=path)
    except (SyntaxError, ValueError) as exc:
        raise UnusableInput("CANNOT PARSE %s (%s)" % (path, type(exc).__name__))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    return mods


def scan(root):
    """Return (files, bad).

    files: sorted root-relative paths of the shipped modules scanned.
    bad: maps a root-relative path to the sorted list of top-level module
    names it imports that are neither stdlib nor a sibling module.
    Raises UnusableInput if the root is missing, holds no shipped module, or a
    shipped module cannot be read or parsed.
    """
    if not os.path.isdir(root):
        raise UnusableInput("PLUGIN ROOT NOT FOUND: %s" % root)
    files, every_py = _shipped_files(root)
    if not files:
        raise UnusableInput("NO SHIPPED .py FILES FOUND under %s" % root)
    local = {os.path.basename(p)[:-3] for p in every_py}
    std = stdlib_names()
    bad = {}
    for rel in files:
        offending = [m for m in _imports(os.path.join(root, rel))
                     if m not in std and m not in local]
        if offending:
            bad[rel] = sorted(set(offending))
    return files, bad


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if len(args) != 1:
        sys.stderr.write("usage: stdlib_only.py <plugin root> — STOPPING\n")
        return 2
    try:
        files, bad = scan(args[0])
    except UnusableInput as exc:
        sys.stderr.write("%s — STOPPING\n" % exc)
        return 2
    if bad:
        for rel in sorted(bad):
            sys.stderr.write("%s: %s\n" % (rel, ", ".join(bad[rel])))
        sys.stderr.write("THIRD-PARTY IMPORT FOUND — STOPPING\n")
        return 1
    sys.stdout.write("%d shipped .py files; third-party imports: none\n" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
