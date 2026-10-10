"""harness_fixture.py — build a disposable git copy of a synthetic harness case.

A case lives under `fixtures/<case-id>/`:
  base/      the correct project (sources + tests)
  defect/    files that replace their base counterparts to introduce the defect
  gsd/       PLAN.md / SUMMARY.md for the GSD layout
  recipe.json

`build_copy` creates `<dest>/repo` and commits, in order:
  1. base files + a `.gitignore` that ignores `.turingmind/`   (base_sha)
  2. GSD layout only: `.planning/phases/<phase-id>/<phase-id>-{PLAN,SUMMARY}.md`
  3. the defect files, subject "introduce <fixed-file stem>"    (head_sha)

So the defect is always committed at HEAD, and in the GSD layout the phase
directory's first commit precedes it, which puts the defect commit inside the
review's `PHASE_START..HEAD` range.

Only `base/`, `defect/` and `gsd/` content is copied. `recipe.json`, the
defect check and everything under `keys/` stay outside the copy.

Stdlib only. Git runs as an argv list with a timeout and the global/system git
config switched off; the copy's local config carries the identity.
"""

import argparse
import collections
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = HARNESS_DIR / "fixtures"
KEYS_DIR = HARNESS_DIR / "keys"
PLUGIN_SCRIPTS_DIR = (HARNESS_DIR.parent.parent.parent
                      / "plugins" / "vibe-check" / "scripts").resolve()

if str(PLUGIN_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SCRIPTS_DIR))

import gitfixture  # noqa: E402  (plugin test-support helper: make_repo/write)

CopyInfo = collections.namedtuple("CopyInfo", "root base_sha head_sha phase_id")

MODES = ("default", "gsd")
GIT_TIMEOUT = 60
CASE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
REQUIRED_KEYS = ("case_id", "fixed_file", "untouched_file", "test_cmd",
                 "defect_check", "hunk_lines", "sentinels", "gsd_phase_id")
COPY_GITIGNORE = ".turingmind/\n__pycache__/\n"
SKIP_DIRS = frozenset({"__pycache__", ".git"})
SKIP_SUFFIXES = (".pyc", ".pyo")


class FixtureError(RuntimeError):
    """A copy could not be built (git failure or a malformed case)."""


def _check_id(value, what):
    if not isinstance(value, str) or not CASE_ID_RE.match(value) \
            or ".." in value:
        raise ValueError("invalid %s: must match [A-Za-z0-9._-]+" % what)
    return value


def load_recipe(case_id):
    """Return the parsed `fixtures/<case_id>/recipe.json`."""
    _check_id(case_id, "case id")
    path = FIXTURES_DIR / case_id / "recipe.json"
    if not path.is_file():
        raise FileNotFoundError("no recipe for case %s" % case_id)
    with open(path, "r", encoding="utf-8") as fh:
        recipe = json.load(fh)
    if not isinstance(recipe, dict):
        raise ValueError("recipe for %s is not an object" % case_id)
    missing = [k for k in REQUIRED_KEYS if k not in recipe]
    if missing:
        raise ValueError("recipe for %s lacks %s" % (case_id,
                                                     ", ".join(missing)))
    if recipe["case_id"] != case_id:
        raise ValueError("recipe case_id does not match its directory")
    return recipe


def _git(repo, *args):
    proc = subprocess.run(["git", *args], cwd=repo, env=gitfixture.helper_env(),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=GIT_TIMEOUT)
    if proc.returncode != 0:
        raise FixtureError("git %s failed: %s" % (args[0], proc.stderr.strip()))
    return proc.stdout


def _tree_files(top):
    """Relative posix paths of the files under `top`, minus bytecode caches."""
    out = []
    for dirpath, dirnames, filenames in os.walk(top):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith(SKIP_SUFFIXES):
                continue
            full = Path(dirpath, name)
            out.append(full.relative_to(top).as_posix())
    return out


def _copy_tree(src_top, repo, rename=None):
    """Copy every file under `src_top` into `repo`; return the written paths."""
    written = []
    for rel in _tree_files(src_top):
        dest_rel = rename(rel) if rename else rel
        gitfixture.write(repo, dest_rel, (src_top / rel).read_bytes())
        written.append(dest_rel)
    return written


def _commit(repo, paths, subject):
    _git(repo, "add", "--", *paths)
    _git(repo, "commit", "-q", "-m", subject)
    return _git(repo, "rev-parse", "HEAD").strip()


def build_copy(recipe, mode, dest):
    """Build `<dest>/repo` for `recipe` in `mode` ("default" or "gsd")."""
    if mode not in MODES:
        raise ValueError("unknown mode %r (expected one of %s)"
                         % (mode, ", ".join(MODES)))
    case_id = _check_id(recipe.get("case_id"), "case id")
    case_dir = FIXTURES_DIR / case_id
    base_dir, defect_dir, gsd_dir = (case_dir / "base", case_dir / "defect",
                                     case_dir / "gsd")
    for d in (base_dir, defect_dir) + ((gsd_dir,) if mode == "gsd" else ()):
        if not d.is_dir():
            raise FixtureError("case %s has no %s/ directory"
                               % (case_id, d.name))
    fixed_file = recipe["fixed_file"]
    if not (defect_dir / fixed_file).is_file():
        raise FixtureError("case %s has no defect version of %s"
                           % (case_id, fixed_file))

    os.makedirs(dest, exist_ok=True)
    root = gitfixture.make_repo(str(dest))

    base_paths = _copy_tree(base_dir, root)
    gitfixture.write(root, ".gitignore", COPY_GITIGNORE)
    base_sha = _commit(root, base_paths + [".gitignore"],
                       "add %s base" % case_id)

    phase_id = None
    if mode == "gsd":
        phase_id = _check_id(recipe["gsd_phase_id"], "phase id")
        phase_rel = ".planning/phases/" + phase_id
        gsd_paths = _copy_tree(
            gsd_dir, root,
            rename=lambda rel: "%s/%s-%s" % (phase_rel, phase_id, rel))
        _commit(root, gsd_paths, "docs: plan %s" % phase_id)

    defect_paths = _copy_tree(defect_dir, root)
    head_sha = _commit(root, defect_paths,
                       "introduce %s" % Path(fixed_file).stem)
    return CopyInfo(root, base_sha, head_sha, phase_id)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a disposable git copy of a fix-harness case.")
    parser.add_argument("--case", required=True)
    parser.add_argument("--mode", required=True, choices=MODES)
    parser.add_argument("--dest", required=True)
    args = parser.parse_args(argv)
    try:
        info = build_copy(load_recipe(args.case), args.mode, args.dest)
    except (ValueError, FileNotFoundError, FixtureError) as exc:
        print("harness_fixture: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(info._asdict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
