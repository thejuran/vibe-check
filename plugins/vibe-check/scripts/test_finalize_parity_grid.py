"""Side by side: the literal 2.14.1 Finalize step 1 beside finalize_inputs.py.

The 2.14.1 side is `fixtures/finalize_step1_2141.sh`, the per-file "HEAD
fingerprints" procedure of `phases/shared/90-finalize.md` at dd8e4ab (tag
v2.14.1) transcribed as a small shell script, run through `/bin/sh` in the
session folder, followed by the 2.14.1 counting command
(`carry_state.py finalize-counts`) and the gate (`finalize_gate.py`). The
helper side is `finalize_inputs.py`, run as a command from the same folder
with the same interpreter and environment. A scenario agrees only when the
fingerprint map, the three counts and the gate action are all equal.

`TestStep1ScriptIsPinned` holds the script to the dd8e4ab text (each command
line must appear there verbatim, in order). The 2.14.1 side never runs the
working-tree modules: `materialize_dd8e4ab` writes `guard.py`,
`carry_state.py`, `finalize_gate.py` and `fixcommit.py` as committed at
dd8e4ab into a temp folder, and the step-1 script, the counting command and
the gate run from there, so the 2.14.1 side really is 2.14.1. `guard.py`,
`finalize_gate.py` and `fixcommit.py` are also still pinned byte-identical
to dd8e4ab in the working tree. `carry_state.py` is not: Phase 66 (999.44
shape 2) edited `_covering`; the 2.14.1 side is now materialized from
dd8e4ab.

`TestParityGrid` builds temp-repo scenarios over a covering grid (every pair
of axis values at least once, plus named regression rows) and compares the
two sides end to end. Axes: the repo folder-name ending, what sits at the
trimmed name, the session folder, git settings and `GIT_*` variables, the
file-name shape, the content state and the verdict shape.

Differences are handled narrowly, never by skipping:
- D-19 (owner decision): with the session in a subfolder of the repo and the
  file carrying unsaved or staged edits, 2.14.1's two `git diff` checks read
  the name relative to the subfolder, match nothing and pass, so 2.14.1
  fingerprints the edited file; the helper must not. Only that exact shape of
  difference is allowed, and both sides' outcomes are asserted.
- FRESHNESS_REFUSALS (owner decision D-09, fail closed): Close out refuses a
  dismissal whose reviewed code it cannot compare with the code on disk.
  Where the session's git cannot see the reviewed work tree (session
  outside the repo, inside `.git`, git not on PATH, `core.worktree` or
  `GIT_DIR` pointing elsewhere, a ceiling hiding the repo), the helper
  refuses with `next: stop-review-again` while 2.14.1 wrote or opened the
  card. Each such scenario is listed with its 2.14.1 outcome and the stale
  cause; the helper's fingerprints and counts must equal 2.14.1's, only the
  action differs. Exhaustive both ways: an unlisted refusal is unexpected,
  and a listed one that no longer refuses fails.
- KNOWN_DIFFERENCES: a shrink-only list of further differences awaiting an
  owner decision, each with both outcomes asserted. The test fails when an
  entry disappears or changes, so the list cannot rot.
Every other scenario must agree exactly.

D-27 (the helper's 60-second limit per git call, accepted by name) is not
exercised: no scenario makes git slow.

A scenario whose folder or file name this filesystem refuses (a folder name
that is not valid UTF-8 on macOS, for one) is counted in an asserted
"not creatable here" list, not skipped; where the filesystem accepts it (Linux
CI) it runs and must agree like any other.

Every repo is built under a fresh temporary folder with the developer's git
config and every inherited `GIT_*` variable removed (gitfixture.helper_env,
then the `GIT_*` keys dropped) and `GIT_CEILING_DIRECTORIES` at the temp root.
Names reach git and the shell only as separate arguments; nothing derived
from a scenario is run as code.

Every grid state dismisses one finding (BUGS_HASH, in DECIDED_FILE). Each
repo commits that file and the state's last pass carries the repo's
reviewed commit and tree (`reviewed_tree`), so the dismissal rests on real
reviewed code that is unchanged on disk; `TestGridStatesBindReviewedTree`
holds every scenario to that.

`TestNameFormGrid` adds what the first grid lacked (verification round 4,
gap 5): the same file name at the top, in the session subfolder and one
level deeper, with different content, named in `./`, `../`, `dir/`,
`./dir/`, `dir/../`, `../dir/`, `dir/./` and other forms, crossed with the
session folder, the layout (the name existing at the top only, in the
subfolder only, or at every level) and which of the files is changed and how
(clean, unsaved edit, staged edit, staged edit with the working copy
restored). Each side is also predicted from a model of git's name rules that
a test checks against real git; the D-19 difference is tolerated there only
for a plain name below the top, in its two exact shapes (D-19 and its
second direction, note N-13), and every `./` or `../` name must agree.

Both grid classes print their summary line (scenario count, agree, D-19,
unexpected, not creatable here) and raise it as a GridSummary warning, so
`pytest -q` lists it in its warnings section even when every test passes.
On Linux nothing may be "not creatable here".

Run directly (`python3 test_finalize_parity_grid.py --grid [helper.py]`) to
run both grid classes against a helper (for a mutant, a copy of the scripts
folder with finalize_inputs.py changed); the exit status is non-zero when any
grid assertion fails.
"""

import collections
import concurrent.futures
import json
import os
import random
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import warnings

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import carry_state  # noqa: E402  (fixture building only: record_decisions)
import gitfixture  # noqa: E402  (helper_env isolation)
import guard  # noqa: E402  (the dd8e4ab module; the name-form model's guard)
from test_finalize_inputs import (check_decided_fixture,  # noqa: E402
                                  decided_files)

SOURCE_COMMIT = "dd8e4ab"
SOURCE_DOC = "plugins/vibe-check/phases/shared/90-finalize.md"
SOURCE_LINES = (13, 22)  # the step 1 text the script transcribes (1-based)
STEP1_SH = os.path.join(SCRIPTS_DIR, "fixtures", "finalize_step1_2141.sh")
HELPER_PY = os.path.join(SCRIPTS_DIR, "finalize_inputs.py")
FIXTURE = os.path.join(SCRIPTS_DIR, "fixtures", "phase45-loop-state.json")
SHARED_WITH_2141 = ("guard.py", "carry_state.py", "finalize_gate.py",
                    "fixcommit.py")
# The shared modules still pinned byte-identical to dd8e4ab in the working
# tree. carry_state.py left the pin when Phase 66 (999.44 shape 2) edited
# `_covering`; the 2.14.1 side is now materialized from dd8e4ab
# (`materialize_dd8e4ab`), so the differential stays literal.
PINNED_TO_2141 = ("guard.py", "finalize_gate.py", "fixcommit.py")
SCRIPTS_REL = "plugins/vibe-check/scripts/"

ARCH_HASH = "5e78e90a6bf05e6a409b4aa3271e5e4df072735a074a9947a0a766a3d794af67"
BUGS_HASH = "7479a9b5fd5b36bce327aea4d49db8dcbe4193208c2b2ca3f1d3ac98368e6644"
# The file of the finding every grid state dismisses (BUGS_HASH, line 38). It
# is committed in each grid repo and the state's last pass carries that
# reviewed tree, so the dismissal rests on real, unchanged reviewed code.
DECIDED_FILE = "plugins/vibe-check/phases/deep-review/20-selection.md"
DECIDED_TEXT = "".join("s%d\n" % i for i in range(1, 45))
CALL_TIMEOUT = 120


def clean_env():
    """os.environ with the developer's git config off and no inherited
    `GIT_*` variable (a hook or a linked worktree may set GIT_DIR)."""
    env = gitfixture.helper_env()
    for key in list(env):
        if key.startswith("GIT_") and key not in ("GIT_CONFIG_GLOBAL",
                                                  "GIT_CONFIG_NOSYSTEM"):
            del env[key]
    return env


def source_text():
    """`90-finalize.md` as committed at dd8e4ab."""
    proc = subprocess.run(
        ["git", "show", SOURCE_COMMIT + ":" + SOURCE_DOC], cwd=SCRIPTS_DIR,
        env=clean_env(), stdin=subprocess.DEVNULL, capture_output=True,
        timeout=60)
    if proc.returncode != 0:
        raise AssertionError("cannot read %s at %s (needs full history): %s"
                             % (SOURCE_DOC, SOURCE_COMMIT,
                                proc.stderr.decode(errors="replace")))
    return proc.stdout.decode("utf-8")


def _git_blob(spec):
    """The bytes of `git show <spec>` in this repo (needs full history)."""
    proc = subprocess.run(
        ["git", "show", spec], cwd=SCRIPTS_DIR, env=clean_env(),
        stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
    if proc.returncode != 0:
        raise AssertionError("cannot read %s (needs full history): %s"
                             % (spec, proc.stderr.decode(errors="replace")))
    return proc.stdout


def materialize_dd8e4ab(case):
    """Write every SHARED_WITH_2141 module as committed at dd8e4ab into a
    fresh temp folder -> the folder. The folder is removed when `case` ends
    (a TestCase instance) or when its class is torn down (a TestCase class),
    on every path. The 2.14.1 side runs these files, never the working
    tree's."""
    tmp = os.path.realpath(tempfile.mkdtemp(prefix="vc-2141-"))
    if isinstance(case, type):
        case.addClassCleanup(shutil.rmtree, tmp, ignore_errors=True)
    else:
        case.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
    for name in SHARED_WITH_2141:
        data = _git_blob(SOURCE_COMMIT + ":" + SCRIPTS_REL + name)
        with open(os.path.join(tmp, name), "wb") as fh:
            fh.write(data)
    return tmp


def old_side_paths(old_dir):
    """{"guard", "carry_state", "finalize_gate"} -> the module files the
    2.14.1 side runs, all in `old_dir` (a `materialize_dd8e4ab` folder)."""
    return {"guard": os.path.join(old_dir, "guard.py"),
            "carry_state": os.path.join(old_dir, "carry_state.py"),
            "finalize_gate": os.path.join(old_dir, "finalize_gate.py")}


def script_command_lines():
    with open(STEP1_SH, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    return [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]


# --------------------------------------------------------------------------- #
# The pin: the script is the dd8e4ab text, and the shared modules are dd8e4ab.
# --------------------------------------------------------------------------- #
FILTER_LINE_RE = re.compile(
    r"""^python3 -c 'import re, sys; sys\.exit\(0 if re\.match\(r"(?P<pat>[^"]+)", """
    r"""sys\.argv\[1\]\) else 1\)' "\$f" \|\| exit 1$""")


class TestStep1ScriptIsPinned(unittest.TestCase):

    def step1_text(self):
        lines = source_text().splitlines()
        first, last = SOURCE_LINES
        text = "\n".join(lines[first - 1:last])
        self.assertIn("**HEAD fingerprints.**", text)
        self.assertIn("including a file ONLY when all three exit 0", text)
        return text

    def test_script_lines_are_the_dd8e4ab_commands(self):
        text = self.step1_text()
        lines = script_command_lines()
        self.assertEqual(len(lines), 8, lines)
        self.assertEqual(lines[0], "f=$1")
        self.assertEqual(lines[1], "out=$2")
        self.assertEqual(lines[7], """printf '%s' "$blob" > "$out\"""")
        # The pre-filter pattern, character for character.
        m = FILTER_LINE_RE.match(lines[2])
        self.assertIsNotNone(m, lines[2])
        self.assertIn("`" + m.group("pat") + "`", text)
        # The guard command and the three git calls, verbatim and in order.
        tail = " || exit 1"
        transcribed = []
        for ln in lines[3:7]:
            self.assertTrue(ln.endswith(tail), ln)
            transcribed.append(ln[:-len(tail)])
        guard, rev, diff, cached = transcribed
        self.assertTrue(rev.startswith("blob=$(") and rev.endswith(")"), rev)
        rev = rev[len("blob=$("):-1]
        expected = [guard.replace('"$f"', '"<file>"'),
                    rev.replace('"HEAD:$f"', '"HEAD:<file>"'),
                    diff.replace('"$f"', "<file>"),
                    cached.replace('"$f"', "<file>")]
        at = -1
        for cmd in expected:
            self.assertNotIn("$f", cmd)
            where = text.find("`" + cmd + "`")
            self.assertGreater(where, at, "not in the 2.14.1 text, or out of "
                                          "order: %r" % cmd)
            at = where

    def test_shared_modules_are_byte_identical_to_dd8e4ab(self):
        """guard.py, finalize_gate.py and fixcommit.py are pinned. Phase 66
        (999.44 shape 2) edited _covering; the 2.14.1 side is now
        materialized from dd8e4ab, so carry_state.py is not pinned here."""
        self.assertEqual(set(SHARED_WITH_2141) - set(PINNED_TO_2141),
                         {"carry_state.py"})
        env = clean_env()
        for name in PINNED_TO_2141:
            with self.subTest(module=name):
                rel = "plugins/vibe-check/scripts/" + name
                old = subprocess.run(
                    ["git", "rev-parse", SOURCE_COMMIT + ":" + rel],
                    cwd=SCRIPTS_DIR, env=env, capture_output=True, text=True,
                    timeout=60)
                self.assertEqual(old.returncode, 0, old.stderr)
                now = subprocess.run(
                    ["git", "hash-object", "--no-filters",
                     os.path.join(SCRIPTS_DIR, name)],
                    cwd=SCRIPTS_DIR, env=env, capture_output=True, text=True,
                    timeout=60)
                self.assertEqual(now.returncode, 0, now.stderr)
                self.assertEqual(now.stdout.strip(), old.stdout.strip())

    def test_2141_side_runs_modules_materialized_from_dd8e4ab(self):
        """Every module the 2.14.1 side runs is the dd8e4ab blob, in a
        folder that is not the working tree's scripts folder."""
        env = clean_env()
        old_dir = materialize_dd8e4ab(self)
        self.assertNotEqual(old_dir, os.path.realpath(SCRIPTS_DIR))
        paths = old_side_paths(old_dir)
        self.assertEqual(sorted(paths),
                         ["carry_state", "finalize_gate", "guard"])
        for key, path in paths.items():
            with self.subTest(path=key):
                self.assertEqual(os.path.dirname(path), old_dir)
        for name in SHARED_WITH_2141:
            with self.subTest(module=name):
                old = subprocess.run(
                    ["git", "rev-parse",
                     SOURCE_COMMIT + ":" + SCRIPTS_REL + name],
                    cwd=SCRIPTS_DIR, env=env, capture_output=True, text=True,
                    timeout=60)
                self.assertEqual(old.returncode, 0, old.stderr)
                now = subprocess.run(
                    ["git", "hash-object", "--no-filters",
                     os.path.join(old_dir, name)],
                    cwd=SCRIPTS_DIR, env=env, capture_output=True, text=True,
                    timeout=60)
                self.assertEqual(now.returncode, 0, now.stderr)
                self.assertEqual(now.stdout.strip(), old.stdout.strip())


# --------------------------------------------------------------------------- #
# Scenarios.
# --------------------------------------------------------------------------- #
ENDINGS = collections.OrderedDict((
    ("plain", ""), ("space", " "), ("tab", "\t"), ("cr", "\r"),
    ("nbsp", " "), ("lf", "\n"), ("lflf", "\n\n"), ("space-lf", " \n"),
    ("non-utf8", os.fsdecode(b"\xff")),
))
NEIGHBOURS = ("none", "folder", "repo-same", "repo-diff")
SESSIONS = ("root", "sub", "deeper", "outside", "inside-git")
SETTINGS = ("none", "worktree-folder", "worktree-repo", "git-dir",
            "git-dir-relative", "git-dir-work-tree", "git-work-tree-other",
            "ceiling-parent", "ceiling-repo", "quotepath", "linked-worktree",
            "symlink-path", "dotdot-path", "literal-pathspecs",
            "icase-pathspecs", "noglob-pathspecs", "git-prefix", "no-git")
NAMES = ("x.ts", "dir/y.ts", "-x.ts", "-1.ts", "dir", "dir/", "missing.ts",
         "link.ts", "out.ts", "a b.ts", "dir/../x.ts", "./x.ts",
         ".git/config", "nl.ts\n")
CONTENTS = ("clean", "edit", "staged", "staged-restored", "deleted",
            "untracked")
VERDICTS = ("obsolete-head", "obsolete-old", "earlier-pass", "applied")
AXES = collections.OrderedDict((
    ("ending", tuple(ENDINGS)), ("neighbour", NEIGHBOURS),
    ("session", SESSIONS), ("setting", SETTINGS), ("name", NAMES),
    ("content", CONTENTS), ("verdict", VERDICTS),
))
Scenario = collections.namedtuple("Scenario", list(AXES))

# Only these axis values may be refused by a filesystem.
MAY_BE_UNCREATABLE = {("ending", "non-utf8"), ("name", "nl.ts\n")}

SUBFOLDER = "dir"
DEEPER = "dir/deep é"
FILES = collections.OrderedDict((
    ("x.ts", "x1\n"), ("dir/y.ts", "y1\n"), (DEEPER + "/k.ts", "k1\n"),
    ("-x.ts", "dash\n"), ("-1.ts", "digit dash\n"), ("a b.ts", "space\n"),
))
LINKS = (("link.ts", "x.ts"), ("out.ts", "../outside.txt"))
# The file a content state changes for each name (`.git/config` itself is
# never edited: that would break the repo, not test the name).
TARGETS = {"dir": "dir/y.ts", "dir/": "dir/y.ts", "dir/../x.ts": "x.ts",
           "./x.ts": "x.ts", ".git/config": "x.ts"}
EDITED = ("edit", "staged", "staged-restored", "deleted")
# Session folders that sit below the repo folder (D-19's "subfolder"). With
# GIT_WORK_TREE naming the repo, `.git` itself is such a folder to git.
BELOW_TOP = ("sub", "deeper", "inside-git")


def key_of(sc):
    return "|".join(repr(v) if f == "name" else v
                    for f, v in zip(Scenario._fields, sc))


def valid_partial(assigned):
    """Constraints on a (partial) row: a plain folder name has no trimmed
    neighbour."""
    if assigned.get("ending") == "plain":
        return assigned.get("neighbour", "none") == "none"
    return True


def pairwise_rows(seed=63, tries=12):
    """A deterministic greedy covering array: every valid pair of axis
    values appears in at least one row."""
    keys = list(AXES)
    n = len(keys)

    def pair(i, a, j, b):
        return ((i, a), (j, b)) if i < j else ((j, b), (i, a))

    uncovered = set()
    for i in range(n):
        for j in range(i + 1, n):
            for a in AXES[keys[i]]:
                for b in AXES[keys[j]]:
                    if valid_partial({keys[i]: a, keys[j]: b}):
                        uncovered.add(((i, a), (j, b)))
    rng = random.Random(seed)
    rows = []
    while uncovered:
        pool = sorted(uncovered)
        best, best_cov = None, -1
        for t in range(tries):
            (i, a), (j, b) = pool[0] if t == 0 else rng.choice(pool)
            row = {i: a, j: b}
            order = [k for k in range(n) if k not in row]
            rng.shuffle(order)
            for k in order:
                best_v, best_c = None, -1
                for v in AXES[keys[k]]:
                    cand = dict(row)
                    cand[k] = v
                    if not valid_partial({keys[m]: cand[m] for m in cand}):
                        continue
                    c = sum(1 for m, val in row.items()
                            if pair(m, val, k, v) in uncovered)
                    if c > best_c:
                        best_v, best_c = v, c
                row[k] = best_v
            cov = sum(1 for x in range(n) for y in range(x + 1, n)
                      if ((x, row[x]), (y, row[y])) in uncovered)
            if cov > best_cov:
                best, best_cov = row, cov
        rows.append(Scenario(*(best[k] for k in range(n))))
        uncovered -= {((x, best[x]), (y, best[y]))
                      for x in range(n) for y in range(x + 1, n)}
    return rows


def S(ending, neighbour, session, setting, name, content, verdict):
    return Scenario(ending, neighbour, session, setting, name, content,
                    verdict)


WRITE = ([0, 0, 0], "write")
OPEN = ([1, 0, 0], "outstanding-to-phase-5")

# Named rows found in verification rounds 1-3, with the 2.14.1 outcome
# (counts, gate action). Each must agree with the helper.
REGRESSION_ROWS = (
    # Gap 3: a folder name ending in a line break, a folder at the trimmed name.
    (S("lf", "repo-same", "root", "none", "x.ts", "edit", "obsolete-head"), OPEN),
    (S("lf", "folder", "root", "none", "x.ts", "clean", "obsolete-head"), WRITE),
    (S("lf", "repo-diff", "root", "none", "x.ts", "clean", "obsolete-head"), WRITE),
    (S("lflf", "repo-same", "root", "none", "x.ts", "edit", "obsolete-head"), OPEN),
    (S("space-lf", "repo-same", "root", "none", "x.ts", "edit", "obsolete-head"), OPEN),
    (S("lf", "none", "root", "none", "x.ts", "clean", "obsolete-head"), OPEN),
    # Gap 3: core.worktree pointing elsewhere.
    (S("plain", "none", "root", "worktree-folder", "x.ts", "clean", "obsolete-head"), WRITE),
    (S("plain", "none", "root", "worktree-repo", "x.ts", "staged", "obsolete-head"), OPEN),
    (S("plain", "none", "root", "worktree-repo", "x.ts", "clean", "obsolete-head"), WRITE),
    # Gap 3, further rows the grid found on the merged helper (same mechanism).
    (S("plain", "none", "root", "worktree-folder", "dir", "clean", "obsolete-head"), WRITE),
    (S("plain", "none", "root", "worktree-folder", "nl.ts\n", "clean", "obsolete-head"), WRITE),
    (S("lflf", "repo-diff", "root", "git-prefix", "dir/y.ts", "staged-restored",
       "obsolete-head"), OPEN),
    (S("space-lf", "repo-diff", "sub", "icase-pathspecs", "-1.ts", "untracked",
       "obsolete-head"), OPEN),
    (S("lf", "repo-diff", "root", "none", "x.ts", "edit", "obsolete-head"), OPEN),
    (S("plain", "none", "root", "worktree-repo", "./x.ts", "clean", "obsolete-head"), OPEN),
    (S("plain", "none", "root", "git-work-tree-other", "./x.ts", "clean",
       "obsolete-head"), OPEN),
    (S("nbsp", "none", "inside-git", "worktree-repo", "nl.ts\n", "staged-restored",
       "obsolete-head"), OPEN),
    (S("lflf", "repo-same", "deeper", "literal-pathspecs", "x.ts", "untracked",
       "obsolete-old"), OPEN),
    (S("nbsp", "none", "root", "worktree-folder", "link.ts", "clean", "obsolete-head"), WRITE),
    (S("tab", "none", "root", "worktree-folder", "x.ts", "clean", "obsolete-head"), WRITE),
    (S("plain", "none", "root", "worktree-folder", "dir/", "clean", "obsolete-head"), WRITE),
    # Gap 2 (D-25): a folder name ending in whitespace other than a line break.
    (S("space", "none", "root", "none", "x.ts", "clean", "obsolete-head"), WRITE),
    (S("space", "repo-same", "root", "none", "x.ts", "edit", "obsolete-head"), OPEN),
    (S("tab", "repo-same", "root", "none", "x.ts", "edit", "obsolete-head"), OPEN),
    (S("cr", "repo-same", "root", "none", "x.ts", "edit", "obsolete-head"), OPEN),
    (S("nbsp", "folder", "root", "none", "x.ts", "clean", "obsolete-head"), WRITE),
    # Gap 1 (D-24): a top-level name starting with `-`.
    (S("plain", "none", "root", "none", "-x.ts", "clean", "obsolete-head"), OPEN),
    # Controls.
    (S("plain", "none", "root", "none", "x.ts", "clean", "obsolete-head"), WRITE),
    (S("plain", "none", "root", "none", "x.ts", "edit", "obsolete-head"), OPEN),
    (S("plain", "none", "sub", "none", "x.ts", "clean", "obsolete-head"), WRITE),
    (S("plain", "none", "root", "linked-worktree", "x.ts", "clean", "obsolete-head"), WRITE),
    (S("plain", "none", "sub", "linked-worktree", "dir/y.ts", "clean", "obsolete-head"), WRITE),
)

# D-19 rows: 2.14.1 fingerprints the edited file and writes; the helper
# leaves it out and the finding stays open.
D19_ROWS = (
    S("plain", "none", "sub", "none", "x.ts", "edit", "obsolete-head"),
    S("plain", "none", "deeper", "none", "x.ts", "staged", "obsolete-head"),
    S("plain", "none", "sub", "none", "dir/y.ts", "staged-restored", "obsolete-head"),
    S("plain", "none", "sub", "none", "x.ts", "deleted", "obsolete-head"),
    S("plain", "none", "sub", "linked-worktree", "x.ts", "edit", "obsolete-head"),
    S("lf", "repo-same", "sub", "none", "x.ts", "edit", "obsolete-head"),
    S("plain", "none", "inside-git", "git-dir-work-tree", "x.ts", "edit",
      "obsolete-head"),
)

# D-09 (owner decision): when no reviewed content can be compared with the
# code on disk, the decision is stale and Close out refuses (fail closed).
# These scenarios put the session where its git cannot see the reviewed work
# tree, so the dismissal (BUGS_HASH) cannot be checked: the helper refuses
# where 2.14.1 wrote or opened the card. Each entry is (scenario, stale
# cause); `freshness_refusal` holds every other part of the result to
# 2.14.1's. Which of write or open 2.14.1 gives is not pinned here: for a
# name like `-1.ts` it follows the Python version's argparse (as on both
# sides of every other row), and the regression rows pin it where it matters.
FRESHNESS_REFUSALS = (
    (S("cr", "none", "sub", "worktree-folder", "dir/y.ts",
       "edit", "obsolete-old"), "unverifiable"),
    (S("cr", "repo-same", "outside", "git-dir", "-1.ts",
       "staged-restored", "applied"), "deleted"),
    (S("space", "repo-same", "sub", "ceiling-repo", "-x.ts",
       "deleted", "obsolete-head"), "unverifiable"),
    (S("tab", "repo-same", "inside-git", "none", "dir/y.ts",
       "untracked", "earlier-pass"), "unverifiable"),
    (S("space", "repo-diff", "root", "no-git", "dir",
       "edit", "applied"), "unverifiable"),
    (S("lf", "repo-diff", "outside", "none", "dir/../x.ts",
       "deleted", "obsolete-old"), "unverifiable"),
    (S("lflf", "folder", "outside", "git-dir-relative", "dir/",
       "edit", "earlier-pass"), "unverifiable"),
    (S("space-lf", "folder", "inside-git", "dotdot-path", "dir",
       "deleted", "obsolete-old"), "unverifiable"),
    (S("lflf", "repo-diff", "inside-git", "worktree-folder", ".git/config",
       "staged", "obsolete-head"), "unverifiable"),
    (S("space", "none", "inside-git", "literal-pathspecs", "out.ts",
       "staged", "earlier-pass"), "unverifiable"),
    (S("space-lf", "none", "outside", "noglob-pathspecs", "x.ts",
       "staged", "applied"), "unverifiable"),
    (S("cr", "repo-diff", "inside-git", "ceiling-repo", "link.ts",
       "untracked", "applied"), "unverifiable"),
    (S("plain", "none", "sub", "no-git", "./x.ts",
       "staged", "obsolete-head"), "unverifiable"),
    (S("lf", "folder", "inside-git", "icase-pathspecs", "a b.ts",
       "staged", "obsolete-old"), "unverifiable"),
    (S("space", "repo-same", "outside", "worktree-folder", "nl.ts\n",
       "clean", "earlier-pass"), "unverifiable"),
    (S("tab", "folder", "deeper", "no-git", ".git/config",
       "deleted", "obsolete-old"), "unverifiable"),
    (S("lflf", "folder", "outside", "linked-worktree", "-x.ts",
       "staged-restored", "obsolete-head"), "unverifiable"),
    (S("lf", "repo-diff", "deeper", "git-dir", "nl.ts\n",
       "edit", "obsolete-old"), "deleted"),
    (S("space", "repo-same", "inside-git", "git-dir-relative", "./x.ts",
       "untracked", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "outside", "ceiling-repo", ".git/config",
       "clean", "earlier-pass"), "unverifiable"),
    (S("cr", "repo-same", "inside-git", "no-git", "dir/../x.ts",
       "clean", "earlier-pass"), "unverifiable"),
    (S("cr", "repo-diff", "sub", "git-dir-relative", "missing.ts",
       "staged", "obsolete-old"), "unverifiable"),
    (S("nbsp", "repo-diff", "outside", "ceiling-parent", "dir/y.ts",
       "staged", "applied"), "unverifiable"),
    (S("tab", "folder", "outside", "git-prefix", "link.ts",
       "edit", "obsolete-head"), "unverifiable"),
    (S("space", "folder", "sub", "git-dir", ".git/config",
       "untracked", "obsolete-head"), "deleted"),
    (S("space-lf", "repo-same", "outside", "symlink-path", "out.ts",
       "clean", "earlier-pass"), "unverifiable"),
    (S("space", "repo-diff", "inside-git", "linked-worktree", "missing.ts",
       "untracked", "applied"), "unverifiable"),
    (S("space", "repo-diff", "inside-git", "noglob-pathspecs", "dir/../x.ts",
       "edit", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "outside", "dotdot-path", "a b.ts",
       "edit", "obsolete-head"), "unverifiable"),
    (S("nbsp", "none", "deeper", "ceiling-repo", "dir",
       "staged", "obsolete-head"), "unverifiable"),
    (S("space-lf", "none", "outside", "no-git", "-x.ts",
       "untracked", "obsolete-head"), "unverifiable"),
    (S("space", "none", "inside-git", "symlink-path", "dir/",
       "untracked", "obsolete-head"), "unverifiable"),
    (S("cr", "none", "outside", "icase-pathspecs", "out.ts",
       "staged-restored", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "outside", "literal-pathspecs", "dir/y.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("tab", "none", "inside-git", "quotepath", "./x.ts",
       "edit", "obsolete-head"), "unverifiable"),
    (S("lflf", "none", "inside-git", "git-dir", "dir/y.ts",
       "clean", "obsolete-head"), "deleted"),
    (S("lf", "none", "root", "worktree-folder", "./x.ts",
       "staged-restored", "obsolete-head"), "unverifiable"),
    (S("lf", "none", "root", "no-git", "dir/",
       "staged-restored", "obsolete-head"), "unverifiable"),
    (S("space-lf", "none", "root", "worktree-folder", "dir/../x.ts",
       "untracked", "obsolete-head"), "unverifiable"),
    (S("nbsp", "none", "root", "worktree-folder", "link.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("lflf", "none", "root", "no-git", "nl.ts\n",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "worktree-folder", "-x.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("nbsp", "none", "root", "no-git", "x.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("tab", "none", "root", "worktree-folder", "x.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "no-git", "-1.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "no-git", "a b.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "no-git", "link.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "no-git", "missing.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "no-git", "out.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "worktree-folder", "-1.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "worktree-folder", "a b.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "worktree-folder", "dir",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "worktree-folder", "dir/",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "worktree-folder", "missing.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "worktree-folder", "x.ts",
       "clean", "obsolete-head"), "unverifiable"),
    (S("plain", "none", "root", "worktree-folder", "nl.ts\n",
       "clean", "obsolete-head"), "unverifiable"),
)


def freshness_refusal(sc, old, new, cause):
    """True only for the D-09 shape: 2.14.1 wrote or opened the card, the
    helper wrote the same fingerprints and counts but refused with
    `next: stop-review-again`, naming exactly the grid's dismissal as stale
    with `cause`."""
    if old is None or new is None or "stop" in old or "stop" in new:
        return False
    if outcome(old) not in (WRITE, OPEN) or "stale" in old:
        return False
    return (new["blobs"] == old["blobs"] and new["counts"] == old["counts"]
            and new["action"] == "refuse"
            and new.get("next") == "stop-review-again"
            and new.get("stale") == [{"hash": BUGS_HASH, "kind": "dismissed",
                                      "cause": cause}])


# Differences with a mechanism not yet ruled on by the owner. Shrink-only:
# each entry is (scenario, 2.14.1 outcome, helper outcome) and must still be
# found, exactly, by the grid.
KNOWN_DIFFERENCES = ()


def all_scenarios():
    rows = list(pairwise_rows())
    for sc, _ in REGRESSION_ROWS:
        rows.append(sc)
    rows.extend(D19_ROWS)
    for sc, _ in FRESHNESS_REFUSALS:
        rows.append(sc)
    for sc, _, _ in KNOWN_DIFFERENCES:
        rows.append(sc)
    seen, out = set(), []
    for sc in rows:
        if sc not in seen:
            seen.add(sc)
            out.append(sc)
    return out


class NotCreatable(Exception):
    pass


class Builder:
    """Runs setup git (never the code under test) with a clean environment."""

    def __init__(self, top):
        self.top = top
        self.env = clean_env()
        self.env["GIT_CEILING_DIRECTORIES"] = top

    def git(self, cwd, *args):
        proc = subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t",
             "-c", "commit.gpgsign=false", *args],
            cwd=cwd, env=self.env, stdin=subprocess.DEVNULL,
            capture_output=True, timeout=CALL_TIMEOUT)
        if proc.returncode != 0:
            raise AssertionError("setup git %r failed: %s"
                                 % (args[:3], proc.stderr.decode(errors="replace")))
        return proc.stdout

    def init_repo(self, path, files, links=(), extra=()):
        os.makedirs(path)
        self.git(path, "init", "-q", "-b", "main")
        for k, v in (("user.name", "t"), ("user.email", "t@t"),
                     ("commit.gpgsign", "false")):
            self.git(path, "config", k, v)
        for rel, data in list(files.items()) + list(extra):
            write_file(os.path.join(path, rel), data)
        for rel, target in links:
            os.symlink(target, os.path.join(path, rel))
        self.git(path, "add", "-A")
        self.git(path, "commit", "-q", "-m", "c")
        return path


def write_file(path, data):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data)


def copy_tree(src, dst):
    shutil.copytree(src, dst, symlinks=True,
                    ignore=shutil.ignore_patterns(".git"))


def modify(path):
    if os.path.islink(path):
        os.remove(path)
        os.symlink("dir/y.ts", path)
    elif os.path.isfile(path):
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("edited after the verdict\n")
    else:
        write_file(path, "added after the verdict\n")


def snapshot_of(path):
    if os.path.islink(path):
        return ("link", os.readlink(path))
    if os.path.isfile(path):
        with open(path, "rb") as fh:
            return ("file", fh.read())
    return None


def restore(path, snap):
    if os.path.lexists(path):
        os.remove(path)
    if snap is None:
        return
    kind, data = snap
    if kind == "link":
        os.symlink(data, path)
    else:
        with open(path, "wb") as fh:
            fh.write(data)


def apply_content(b, checkout, name, content):
    target = TARGETS.get(name, name)
    path = os.path.join(checkout, target)
    if content == "clean":
        return
    if content == "edit":
        modify(path)
    elif content == "staged":
        modify(path)
        b.git(checkout, "add", "-A", "--", target)
    elif content == "staged-restored":
        snap = snapshot_of(path)
        modify(path)
        b.git(checkout, "add", "-A", "--", target)
        restore(path, snap)
    elif content == "deleted":
        if os.path.lexists(path):
            os.remove(path)
    elif content == "untracked":
        b.git(checkout, "rm", "-r", "-q", "--cached", "--ignore-unmatch",
              "--", target)
        b.git(checkout, "commit", "-q", "--allow-empty", "-m", "untrack")
        if not os.path.lexists(path):
            write_file(path, "untracked\n")


def reviewed_of(b, repo):
    """(HEAD commit, HEAD tree) of a freshly built grid repo: the review the
    grid state's dismissal was made on."""
    return (b.git(repo, "rev-parse", "HEAD").decode().strip(),
            b.git(repo, "rev-parse", "HEAD^{tree}").decode().strip())


def fixture_state(name, verdict, blob, reviewed=None):
    """The grid state: BUGS_HASH dismissed, ARCH_HASH's row pointed at
    `name` with a `verdict`-shaped fix verdict on `blob`. With `reviewed`
    ((commit, tree) from `reviewed_of`) the last pass carries that review."""
    with open(FIXTURE, "r", encoding="utf-8") as fh:
        s = json.load(fh)
    s = carry_state.record_decisions(s, {
        "at_pass": s["passes"][-1]["pass_number"],
        "decisions": [{"stable_hash": BUGS_HASH, "decision": "dismiss",
                       "reason": "grid"}]})
    last = s["passes"][-1]
    for r in last["findings"]:
        if r["stable_hash"] == ARCH_HASH:
            r["file"] = name
    at = last["pass_number"] - 1 if verdict == "earlier-pass" \
        else last["pass_number"]
    recorded = blob or "0" * 40
    if verdict == "obsolete-old":
        recorded = "1" * 40
    s["fix_verdicts"] = {ARCH_HASH: {
        "verdict": "applied" if verdict == "applied" else "obsolete",
        "agent": "fix", "head_sha": last["head_sha"], "at_pass": at,
        "reason": "grid", "verified_blob": recorded}}
    if reviewed is not None:
        last["head_sha"], last["reviewed_tree"] = reviewed
    return s


def build(sc, base, top, shim_path):
    """Create the scenario under `base` -> (session folder, env, state,
    HEAD blob of the name or None). Raises NotCreatable when this
    filesystem refuses a folder or file name."""
    b = Builder(top)
    os.makedirs(base)
    write_file(os.path.join(base, "outside.txt"), "outside\n")
    folder = "repo" + ENDINGS[sc.ending]
    repo = os.path.join(base, folder)
    extra = [(DECIDED_FILE, DECIDED_TEXT)]
    if sc.name == "nl.ts\n":
        extra.append(("nl.ts\n", "newline name\n"))
    try:
        b.init_repo(repo, FILES, LINKS, extra)
    except OSError as exc:
        raise NotCreatable(str(exc))
    reviewed = reviewed_of(b, repo)
    if sc.neighbour != "none":
        trimmed = folder.rstrip("\n")
        if trimmed == folder:
            trimmed = "repo"
        dst = os.path.join(base, trimmed)
        if sc.neighbour == "folder":
            copy_tree(repo, dst)
        elif sc.neighbour == "repo-same":
            b.init_repo(dst, FILES, LINKS, extra)
        else:
            b.init_repo(dst, {k: "other " + v for k, v in FILES.items()},
                        LINKS, extra)
    checkout = repo
    other = os.path.join(base, "other")
    if sc.setting == "linked-worktree":
        checkout = os.path.join(base, "wt")
        b.git(repo, "worktree", "add", "-q", checkout, "-b", "side")
    elif sc.setting in ("worktree-folder", "git-work-tree-other"):
        copy_tree(repo, other)
    elif sc.setting == "worktree-repo":
        b.init_repo(other, FILES, LINKS, extra)
    rev = subprocess.run(["git", "rev-parse", "HEAD:" + sc.name],
                         cwd=checkout, env=b.env, stdin=subprocess.DEVNULL,
                         capture_output=True, timeout=CALL_TIMEOUT)
    blob = rev.stdout.decode().strip() if rev.returncode == 0 else None
    apply_content(b, checkout, sc.name, sc.content)
    env = clean_env()
    env["GIT_CEILING_DIRECTORIES"] = top
    env["PATH"] = shim_path + os.pathsep + env.get("PATH", "")
    env["PYTHONIOENCODING"] = "utf-8:strict"
    if sc.setting in ("worktree-folder", "worktree-repo"):
        b.git(repo, "config", "core.worktree", other)
    elif sc.setting == "quotepath":
        b.git(repo, "config", "core.quotepath", "true")
    elif sc.setting == "git-dir":
        env["GIT_DIR"] = os.path.join(repo, ".git")
    elif sc.setting == "git-dir-relative":
        env["GIT_DIR"] = ".git"
    elif sc.setting == "git-dir-work-tree":
        env["GIT_DIR"] = os.path.join(repo, ".git")
        env["GIT_WORK_TREE"] = repo
    elif sc.setting == "git-work-tree-other":
        env["GIT_DIR"] = os.path.join(repo, ".git")
        env["GIT_WORK_TREE"] = other
    elif sc.setting == "ceiling-parent":
        env["GIT_CEILING_DIRECTORIES"] = base
    elif sc.setting == "ceiling-repo":
        env["GIT_CEILING_DIRECTORIES"] = repo
    elif sc.setting == "literal-pathspecs":
        env["GIT_LITERAL_PATHSPECS"] = "1"
    elif sc.setting == "icase-pathspecs":
        env["GIT_ICASE_PATHSPECS"] = "1"
    elif sc.setting == "noglob-pathspecs":
        env["GIT_NOGLOB_PATHSPECS"] = "1"
    elif sc.setting == "git-prefix":
        env["GIT_PREFIX"] = SUBFOLDER + "/"
    elif sc.setting == "no-git":
        env["PATH"] = shim_path
    view = checkout
    if sc.setting == "symlink-path":
        view = os.path.join(base, "link")
        os.symlink(checkout, view)
    rel = {"root": "", "sub": SUBFOLDER, "deeper": DEEPER}.get(sc.session)
    if sc.session == "inside-git":
        session = os.path.join(repo, ".git")
    elif rel is None:
        session = os.path.join(base, "elsewhere")
        os.makedirs(session)
    elif sc.setting == "dotdot-path":
        session = os.path.join(view, SUBFOLDER, "..", rel) if rel \
            else os.path.join(view, SUBFOLDER, "..")
    else:
        session = os.path.join(view, rel) if rel else view
    return (session, env, fixture_state(sc.name, sc.verdict, blob, reviewed),
            blob)


def run(argv, cwd, env, stdin_bytes=b""):
    return subprocess.run(argv, cwd=cwd, env=env, input=stdin_bytes,
                          capture_output=True, timeout=CALL_TIMEOUT)


def side_2141(state, state_path, files_dir, session, env, shell, old_dir,
              memo=None):
    """Step 1 through the 2.14.1 script for each last-pass fix verdict, then
    the 2.14.1 counting command and gate, every module run from `old_dir`
    (the dd8e4ab files `materialize_dd8e4ab` wrote). With a `memo` dict, the counting
    command and the gate (pure functions of the state bytes and the
    fingerprint map) are run once per distinct input and their output
    reused; step 1 always runs."""
    paths = old_side_paths(old_dir)
    blobs = {}
    last = state["passes"][-1]
    for h, v in state["fix_verdicts"].items():
        if not isinstance(v, dict) or v.get("at_pass") != last["pass_number"]:
            continue
        rows = [r for r in last["findings"] if r.get("stable_hash") == h]
        if not rows or not isinstance(rows[0].get("file"), str):
            continue
        f = rows[0]["file"]
        out = os.path.join(files_dir, "blob-2141.txt")
        if os.path.exists(out):
            os.remove(out)
        proc = run([shell, STEP1_SH, f, out], session, dict(env, GUARD_PY=paths["guard"]))
        if proc.returncode == 0:
            with open(out, "rb") as fh:
                blobs[f] = fh.read().decode("utf-8")
    bp = os.path.join(files_dir, "blobs-2141.json")
    with open(bp, "w", encoding="utf-8") as fh:
        json.dump(blobs, fh)
    with open(state_path, "rb") as fh:
        state_bytes = fh.read()
    key = (state_bytes, json.dumps(blobs, sort_keys=True))
    if memo is not None and key in memo:
        return dict(memo[key], blobs=blobs)
    got = _counts_and_gate_2141(state_bytes, bp, session, env, paths)
    if memo is not None:
        memo[key] = got
    return dict(got, blobs=blobs) if "stop" not in got else got


def _counts_and_gate_2141(state_bytes, bp, session, env, paths):
    c = run([sys.executable, paths["carry_state"], "finalize-counts", "--head-blobs",
             bp], session, env, state_bytes)
    if c.returncode != 0:
        return {"stop": "state"}
    counts = json.loads(c.stdout)
    flags = {"state_file_present": True,
             "outstanding_cw": counts["outstanding_cw"],
             "unacknowledged_medium": counts["unacknowledged_medium"],
             "undecided_nv": counts["undecided_nv"],
             "noninteractive": False, "pr_mode": False, "range_mode": False}
    g = run([sys.executable, paths["finalize_gate"]], session, env,
            json.dumps({"flags": flags}).encode())
    if g.returncode != 0:
        return {"stop": "gate"}
    return {"counts": [counts["outstanding_cw"], counts["unacknowledged_medium"],
                       counts["undecided_nv"]],
            "action": json.loads(g.stdout)["action"]}


def side_helper(state_path, files_dir, session, env, helper=None):
    helper = helper or HELPER_PY
    bp = os.path.join(files_dir, "blobs-helper.json")
    with open(bp, "w"):
        pass
    proc = run([sys.executable, helper, "--state-file", state_path,
                "--blob-out", bp, "--noninteractive", "false",
                "--pr-mode", "false", "--range-mode", "false"], session, env)
    if proc.returncode == 3:
        return {"stop": "state"}
    if proc.returncode == 4:
        return {"stop": "gate"}
    if proc.returncode != 0:
        return {"stop": "exit %d" % proc.returncode}
    got = json.loads(proc.stdout)
    with open(bp, "r", encoding="utf-8") as fh:
        blobs = json.load(fh)
    c = got["counts"]
    out = {"blobs": blobs,
           "counts": [c["outstanding_cw"], c["unacknowledged_medium"],
                      c["undecided_nv"]],
           "action": got["action"]}
    if "stale" in got:  # a freshness refusal; never present otherwise
        out["next"] = got["next"]
        out["stale"] = got["stale"]
    return out


def make_shim(top):
    """A folder whose `python3` runs this interpreter, put first on PATH so
    the script's `python3` is the same interpreter the helper runs under
    (argparse's option reading differs between Python versions)."""
    shim = os.path.join(top, "shim")
    os.makedirs(shim)
    path = os.path.join(shim, "python3")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("#!/bin/sh\nexec %s \"$@\"\n" % shlex.quote(sys.executable))
    os.chmod(path, 0o755)
    return shim


def run_one(index, sc, top, shim, old_dir, shell="/bin/sh", helper=None):
    base = os.path.join(top, "s%04d" % index)
    files_dir = os.path.join(top, "f%04d" % index)
    os.makedirs(files_dir)
    try:
        session, env, state, blob = build(sc, base, top, shim)
    except NotCreatable as exc:
        return sc, None, None, None, str(exc)
    state_path = os.path.join(files_dir, "state.json")
    with open(state_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh)
    old = side_2141(state, state_path, files_dir, session, env, shell,
                    old_dir)
    new = side_helper(state_path, files_dir, session, env, helper)
    return sc, old, new, blob, None


def run_grid(scenarios, old_dir, shell="/bin/sh", helper=None, workers=None):
    """[(scenario, 2.14.1 outcome, helper outcome, HEAD blob, not-creatable
    reason)] in scenario order; every temp folder is removed afterwards.
    `old_dir` holds the dd8e4ab modules (`materialize_dd8e4ab`)."""
    top = os.path.realpath(tempfile.mkdtemp(prefix="vc-grid-"))
    try:
        shim = make_shim(top)
        workers = workers or min(8, os.cpu_count() or 2)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run_one, i, sc, top, shim, old_dir,
                                   shell, helper)
                       for i, sc in enumerate(scenarios)]
            return [f.result() for f in futures]
    finally:
        shutil.rmtree(top, ignore_errors=True)


def outcome(o):
    return None if o is None or "stop" in o else (o["counts"], o["action"])


def session_relative(name):
    """Does git read `HEAD:<name>` relative to the session folder? git does
    so exactly when the name starts with `./` or `../`; any other name is
    read from the top of the work tree."""
    return name.startswith(("./", "../"))


def d19_difference(sc, old, new, blob):
    """True only for the D-19 shape: session in a subfolder, a plain file
    name (one git reads from the top in `HEAD:<name>` but relative to the
    session in the two checks), the file edited or staged, 2.14.1
    fingerprints it with its HEAD blob, the helper leaves exactly that file
    out, and the two decisions follow from that."""
    if sc.session not in BELOW_TOP or sc.content not in EDITED:
        return False
    if session_relative(sc.name):
        return False
    if "stop" in old or "stop" in new:
        return False
    f = sc.name
    if old["blobs"].get(f) != blob or blob is None or f in new["blobs"]:
        return False
    if {k: v for k, v in old["blobs"].items() if k != f} != new["blobs"]:
        return False
    closes = sc.verdict == "obsolete-head"
    return (outcome(old) == (WRITE if closes else OPEN)
            and outcome(new) == OPEN)


def classify(results):
    """-> dict of lists: agree, d19, fresh, known, unexpected,
    not_creatable."""
    known = {sc: (o, n) for sc, o, n in KNOWN_DIFFERENCES}
    fresh = dict(FRESHNESS_REFUSALS)
    out = {"agree": [], "d19": [], "fresh": [], "known": [], "unexpected": [],
           "not_creatable": []}
    for sc, old, new, blob, why in results:
        if why is not None:
            out["not_creatable"].append((sc, why))
        elif old == new:
            out["agree"].append(sc)
        elif d19_difference(sc, old, new, blob):
            out["d19"].append((sc, old, new))
        elif sc in fresh and freshness_refusal(sc, old, new, fresh[sc]):
            out["fresh"].append(sc)
        elif sc in known and known[sc] == (old, new):
            out["known"].append(sc)
        else:
            out["unexpected"].append((sc, old, new))
    return out


def report(results, seconds):
    c = classify(results)
    lines = ["%d scenarios in %.1f s: %d agree, %d D-19, %d D-09 refusals, "
             "%d known differences, %d unexpected, %d not creatable here"
             % (len(results), seconds, len(c["agree"]), len(c["d19"]),
                len(c["fresh"]), len(c["known"]), len(c["unexpected"]),
                len(c["not_creatable"]))]
    for sc, why in c["not_creatable"]:
        lines.append("  not creatable here: %s (%s)" % (key_of(sc), why))
    for sc, old, new in c["unexpected"]:
        lines.append("  DIFFERENT %s\n      2.14.1 %r\n      helper %r"
                     % (key_of(sc), old, new))
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# The name-form grid: one file name at several folder levels.
#
# The repo holds `n.ts` at the top, in `dir` and in `dir/deep` (or only one
# of them), each with different content, and the finding names it in one of
# the NF_FORMS shapes. Full cross of: repo folder name x layout x content
# (which of the files is changed, and how) x session folder x name form.
# Every form passes the 2.14.1 character filter; the guard command decides
# the rest on both sides.
#
# Each side is predicted from a model of git's own rules (`nf_blob_path`,
# `nf_pathspec_path`), and `test_model_is_what_git_does` checks that model
# against real git for every session and form, so the prediction is not an
# assumption:
#   2.14.1 fingerprints  iff the guard passes, `HEAD:<name>` names a file B,
#                        the pathspec names a file D (git does not refuse
#                        it) and D is unchanged;
#   D-19 (the helper)    iff the guard passes, B exists and B is unchanged.
# The two differ only where B != D, which is only a plain name (not
# starting with `./` or `../`) with the session below the top: the 2.14.1
# hole D-19 closed. There the difference is tolerated in its two exact
# shapes, D-19 (B changed: 2.14.1 fingerprints an edited file, the helper
# does not) and its second direction, note N-13 (B unchanged, the
# same-named file in the session folder changed: 2.14.1 leaves B out by
# accident, the helper fingerprints it). Everywhere else, and for every
# `./` or `../` name, the two sides must agree exactly.
# --------------------------------------------------------------------------- #
NF_FILES = collections.OrderedDict((
    ("top", ("n.ts", "n top\n")), ("sub", ("dir/n.ts", "n sub\n")),
    ("deep", ("dir/deep/n.ts", "n deep\n")),
))
NF_ALWAYS = (("dir/deep/other.txt", "other\n"),)  # keeps `dir/deep` tracked
NF_LAYOUTS = collections.OrderedDict((
    ("all", ("top", "sub", "deep")), ("top-only", ("top",)),
    ("sub-only", ("sub",)),
))
NF_SESSIONS = collections.OrderedDict((
    ("root", ""), ("sub", "dir"), ("deeper", "dir/deep"),
))
# Forms crossed with every layout and every content: the shapes that name
# an existing file from some session.
NF_FORMS = ("n.ts", "./n.ts", "dir/n.ts", "./dir/n.ts", "./deep/n.ts")
# Forms crossed with every session and NF_SECONDARY_CONTENTS of the `all`
# layout: names git reads with `..` or `.` inside, names leaving the repo,
# names that never exist, and deeper names.
NF_SECONDARY_FORMS = ("./dir/../n.ts", "dir/deep/n.ts", "./dir/deep/n.ts",
                      "../n.ts", "./../n.ts", "../dir/n.ts", "../../n.ts",
                      "dir/../n.ts", "dir/./n.ts", "deep/n.ts")
# With the repo folder itself named `dir`, a name leaving the repo and
# coming back in (`../dir/...`) passes the guard, which resolves it against
# the repo folder, while git resolves it against the session folder.
NF_REENTRY_FORMS = ("../dir/n.ts", "../dir/deep/n.ts", "./../dir/n.ts")
NF_STATES = ("edit", "staged", "staged-restored")
NF_TARGETS = collections.OrderedDict((
    ("all", (("top",), ("sub",), ("deep",), ("top", "sub"))),
    ("top-only", (("top",),)), ("sub-only", (("sub",),)),
))
# Every target and every state at least once.
NF_SECONDARY_CONTENTS = (((), "clean"), (("top",), "edit"), (("sub",), "edit"),
                         (("sub",), "staged"), (("deep",), "staged-restored"),
                         (("top", "sub"), "staged-restored"))
NFScenario = collections.namedtuple(
    "NFScenario", "root layout target state session form")


def nf_contents(layout):
    """(target, state) pairs for a layout; ((), "clean") is no change."""
    out = [((), "clean")]
    for target in NF_TARGETS[layout]:
        for state in NF_STATES:
            out.append((target, state))
    return out


def nf_scenarios():
    rows = []
    for layout in NF_LAYOUTS:
        for target, state in nf_contents(layout):
            for session in NF_SESSIONS:
                for form in NF_FORMS:
                    rows.append(NFScenario("repo", layout, target, state,
                                           session, form))
    for root, forms in (("repo", NF_SECONDARY_FORMS), ("dir", NF_REENTRY_FORMS)):
        for target, state in NF_SECONDARY_CONTENTS:
            for session in NF_SESSIONS:
                for form in forms:
                    rows.append(NFScenario(root, "all", target, state,
                                           session, form))
    return rows


def nf_key(sc):
    return "%s|%s|%s|%s|%s|%s" % (sc.root, sc.layout, "+".join(sc.target)
                                  or "-", sc.state, sc.session, sc.form)


def _git_normalise(path):
    """Collapse `//`, `.` and `..` as git does for a session-relative name
    and for a pathspec -> top-relative path, or None when it climbs above
    the top (git refuses it)."""
    out = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not out:
                return None
            out.pop()
        else:
            out.append(part)
    return "/".join(out)


def nf_blob_path(prefix, form):
    """The top-relative path `git rev-parse HEAD:<form>` reads in a session
    whose `--show-prefix` is `prefix`, or None when git can name no path:
    a `./` or `../` name is resolved from the session folder and normalised;
    any other name is looked up from the top exactly as written, so an
    empty, `.` or `..` part makes the lookup fail."""
    if session_relative(form):
        return _git_normalise(prefix + form)
    if any(part in ("", ".", "..") for part in form.split("/")):
        return None
    return form


def nf_pathspec_path(prefix, form):
    """The top-relative path the pathspec `<form>` after `--` addresses in
    that session (always read from the session folder), or None when git
    refuses it (outside the repository, exit 128)."""
    return _git_normalise(prefix + form)


def nf_repo_files(layout):
    return [NF_FILES[k][0] for k in NF_LAYOUTS[layout]]


def nf_changed(sc):
    return set() if sc.state == "clean" else {NF_FILES[k][0] for k in sc.target}


def nf_guard_ok(root, form):
    return guard.contained(root, form)[0]


def nf_predict(sc, root):
    """(2.14.1 fingerprints?, D-19 fingerprints?, B, D) for a scenario."""
    prefix = NF_SESSIONS[sc.session] + "/" if NF_SESSIONS[sc.session] else ""
    b = nf_blob_path(prefix, sc.form)
    d = nf_pathspec_path(prefix, sc.form)
    files = nf_repo_files(sc.layout)
    changed = nf_changed(sc)
    if not nf_guard_ok(root, sc.form) or b not in files:
        return False, False, b, d
    return (d is not None and d not in changed), (b not in changed), b, d


def nf_build(root_name, layout, target, state, base, top):
    """The repo for one (root name, layout, content) under `base` -> (repo,
    {top-relative path: HEAD blob}, (commit, tree) of the review).
    DECIDED_FILE is committed beside the layout files."""
    b = Builder(top)
    os.makedirs(base)
    repo = os.path.join(base, root_name)
    files = collections.OrderedDict(NF_FILES[k] for k in NF_LAYOUTS[layout])
    files.update(NF_ALWAYS)
    b.init_repo(repo, files, extra=((DECIDED_FILE, DECIDED_TEXT),))
    reviewed = reviewed_of(b, repo)
    blobs = {}
    for rel in files:
        blobs[rel] = b.git(repo, "rev-parse", "HEAD:" + rel).decode().strip()
    for k in target:
        rel = NF_FILES[k][0]
        path = os.path.join(repo, rel)
        if state == "edit":
            modify(path)
        elif state == "staged":
            modify(path)
            b.git(repo, "add", "--", rel)
        elif state == "staged-restored":
            snap = snapshot_of(path)
            modify(path)
            b.git(repo, "add", "--", rel)
            restore(path, snap)
    return repo, blobs, reviewed


def nf_state(form, blob, reviewed=None):
    return fixture_state(form, "obsolete-head", blob, reviewed)


def nf_run(scenarios, old_dir, helper=None, workers=None):
    """[(scenario, 2.14.1 outcome, helper outcome, prediction)] in order.
    One repo per (root name, layout, content); every temp folder is removed
    afterwards. `old_dir` holds the dd8e4ab modules
    (`materialize_dd8e4ab`)."""
    top = os.path.realpath(tempfile.mkdtemp(prefix="vc-nfgrid-"))
    try:
        shim = make_shim(top)
        env = clean_env()
        env["GIT_CEILING_DIRECTORIES"] = top
        env["PATH"] = shim + os.pathsep + env.get("PATH", "")
        env["PYTHONIOENCODING"] = "utf-8:strict"
        workers = workers or min(8, os.cpu_count() or 2)
        repo_keys = []
        for sc in scenarios:
            k = (sc.root, sc.layout, sc.target, sc.state)
            if k not in repo_keys:
                repo_keys.append(k)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            built = list(pool.map(
                lambda ik: nf_build(*ik[1], os.path.join(top, "r%03d" % ik[0]),
                                    top),
                enumerate(repo_keys)))
            repos = dict(zip(repo_keys, built))
            memo = {}

            def one(index, sc):
                repo, head, reviewed = repos[(sc.root, sc.layout, sc.target,
                                              sc.state)]
                fizz, d19, b, d = nf_predict(sc, repo)
                session = os.path.join(repo, NF_SESSIONS[sc.session]) \
                    if NF_SESSIONS[sc.session] else repo
                files_dir = os.path.join(top, "f%04d" % index)
                os.makedirs(files_dir)
                blob = head.get(b) if b is not None else None
                state = nf_state(sc.form, blob, reviewed)
                state_path = os.path.join(files_dir, "state.json")
                with open(state_path, "w", encoding="utf-8") as fh:
                    json.dump(state, fh)
                old = side_2141(state, state_path, files_dir, session, env,
                                "/bin/sh", old_dir, memo)
                new = side_helper(state_path, files_dir, session, env, helper)
                return sc, old, new, (fizz, d19, b, d, blob)

            futures = [pool.submit(one, i, sc) for i, sc in enumerate(scenarios)]
            return [f.result() for f in futures]
    finally:
        shutil.rmtree(top, ignore_errors=True)


def nf_expected(sc, fingerprinted, blob):
    """The outcome a side must give: its map and its decision."""
    if fingerprinted:
        return {"blobs": {sc.form: blob}, "counts": WRITE[0], "action": WRITE[1]}
    return {"blobs": {}, "counts": OPEN[0], "action": OPEN[1]}


def nf_classify(results):
    """-> dict of lists: agree, d19, n13, unexpected, model (2.14.1 side not
    as the git model predicts: the model or the script is wrong)."""
    out = {"agree": [], "d19": [], "n13": [], "unexpected": [], "model": []}
    for sc, old, new, (fizz, d19, b, d, blob) in results:
        if old != nf_expected(sc, fizz, blob):
            out["model"].append((sc, old, new))
        if old == new:
            out["agree"].append(sc)
            continue
        hole = (sc.session != "root" and not session_relative(sc.form)
                and b is not None and d is not None and b != d)
        if hole and new == nf_expected(sc, d19, blob):
            if b in nf_changed(sc):
                out["d19"].append((sc, old, new))
                continue
            if d in nf_changed(sc):
                out["n13"].append((sc, old, new))
                continue
        out["unexpected"].append((sc, old, new))
    return out


def nf_report(results, seconds):
    c = nf_classify(results)
    lines = ["%d name-form scenarios in %.1f s: %d agree, %d D-19, %d D-19 "
             "second direction (N-13), %d unexpected, %d off the git model"
             % (len(results), seconds, len(c["agree"]), len(c["d19"]),
                len(c["n13"]), len(c["unexpected"]), len(c["model"]))]
    for sc, old, new in c["unexpected"]:
        lines.append("  DIFFERENT %s\n      2.14.1 %r\n      helper %r"
                     % (nf_key(sc), old, new))
    for sc, old, new in c["model"]:
        lines.append("  OFF MODEL %s\n      2.14.1 %r" % (nf_key(sc), old))
    return "\n".join(lines)


def NF(root, layout, target, state, session, form):
    return NFScenario(root, layout, tuple(target), state, session, form)


# Gap 5 (found by the fourth verification round): a `./` or `../` name with
# the session in a subfolder. 2.14.1 reads all three from the same
# session-relative file, so these must agree, with these 2.14.1 outcomes.
NF_REGRESSION_ROWS = (
    # (a) the session folder's own file edited / staged: open.
    (NF("repo", "all", ["sub"], "edit", "sub", "./n.ts"), OPEN),
    (NF("repo", "all", ["sub"], "staged", "sub", "./n.ts"), OPEN),
    (NF("repo", "all", ["sub"], "staged-restored", "sub", "./n.ts"), OPEN),
    (NF("repo", "all", ["deep"], "edit", "deeper", "./n.ts"), OPEN),
    (NF("repo", "all", ["deep"], "staged", "sub", "./deep/n.ts"), OPEN),
    (NF("repo", "sub-only", ["sub"], "edit", "sub", "./n.ts"), OPEN),
    # (b) only the same-named top-level file edited: the named file is clean.
    (NF("repo", "all", ["top"], "edit", "sub", "./n.ts"), WRITE),
    (NF("repo", "all", ["top"], "staged", "deeper", "./n.ts"), WRITE),
    # (c) a name leaving the repo and coming back in, clean and edited.
    (NF("dir", "all", [], "clean", "sub", "../dir/n.ts"), WRITE),
    (NF("dir", "all", ["sub"], "edit", "sub", "../dir/n.ts"), OPEN),
    # `./../n.ts` from `dir/deep` is `dir/n.ts` to git, but the guard
    # resolves it against the repo folder (outside): left out on both sides.
    (NF("repo", "all", [], "clean", "deeper", "./../n.ts"), OPEN),
    (NF("repo", "all", ["sub"], "edit", "deeper", "./../n.ts"), OPEN),
    # Clean controls.
    (NF("repo", "all", [], "clean", "sub", "./n.ts"), WRITE),
    (NF("repo", "all", [], "clean", "root", "./n.ts"), WRITE),
    (NF("repo", "all", [], "clean", "sub", "n.ts"), WRITE),
)

# The D-19 rows of this grid: (scenario, 2.14.1 outcome, helper outcome).
NF_D19_ROWS = (
    # D-19: session in `dir`, the top-level n.ts (the file the finding
    # names) edited: 2.14.1 checks `dir/n.ts`, fingerprints the edited file
    # and approves; the helper keeps the finding open.
    (NF("repo", "all", ["top"], "edit", "sub", "n.ts"), WRITE, OPEN),
    (NF("repo", "all", ["top"], "staged", "deeper", "n.ts"), WRITE, OPEN),
    (NF("repo", "top-only", ["top"], "staged-restored", "sub", "n.ts"), WRITE,
     OPEN),
    (NF("repo", "all", ["sub"], "edit", "deeper", "dir/n.ts"), WRITE, OPEN),
    # D-19's second direction (verification note N-13), part of the
    # accepted mechanism: the top-level n.ts is unchanged and a different,
    # same-named `dir/n.ts` is edited. 2.14.1 checks that other file, sees
    # the edit and keeps the finding open by accident; the helper checks the
    # file the finding names, finds it clean and approves. `main` does the
    # same.
    (NF("repo", "all", ["sub"], "edit", "sub", "n.ts"), OPEN, WRITE),
    (NF("repo", "all", ["sub"], "staged", "sub", "n.ts"), OPEN, WRITE),
    (NF("repo", "all", ["deep"], "edit", "deeper", "n.ts"), OPEN, WRITE),
)


class TestNameFormGrid(unittest.TestCase):
    """The name-form grid, run once for the class."""

    @classmethod
    def setUpClass(cls):
        cls.scenarios = nf_scenarios()
        start = time.time()
        cls.results = nf_run(cls.scenarios, materialize_dd8e4ab(cls))
        cls.seconds = time.time() - start
        cls.by_scenario = {r[0]: r for r in cls.results}
        cls.classes = nf_classify(cls.results)
        cls.summary = nf_report(cls.results, cls.seconds)
        show_summary(cls.summary)

    def test_every_form_passes_the_2141_character_filter(self):
        for form in NF_FORMS + NF_SECONDARY_FORMS + NF_REENTRY_FORMS:
            self.assertRegex(form, r"^[A-Za-z0-9._/-]+$")

    def test_named_rows_are_in_the_grid(self):
        names = set(self.scenarios)
        for sc, _ in NF_REGRESSION_ROWS:
            self.assertIn(sc, names)
        for sc, _, _ in NF_D19_ROWS:
            self.assertIn(sc, names)

    def test_model_is_what_git_does(self):
        """For each session and form, the file `HEAD:<form>` reads and the
        file the pathspec addresses are what nf_blob_path and
        nf_pathspec_path say, by real git."""
        top = os.path.realpath(tempfile.mkdtemp(prefix="vc-nfmodel-"))
        try:
            repo, head, _ = nf_build("repo", "all", (), "clean",
                                     os.path.join(top, "b"), top)
            by_blob = {v: k for k, v in head.items()}
            env = clean_env()
            env["GIT_CEILING_DIRECTORIES"] = top
            for session, rel in NF_SESSIONS.items():
                cwd = os.path.join(repo, rel) if rel else repo
                prefix = rel + "/" if rel else ""
                for form in NF_FORMS + NF_SECONDARY_FORMS + NF_REENTRY_FORMS:
                    with self.subTest(session=session, form=form):
                        rev = run(["git", "rev-parse", "--verify", "-q",
                                   "HEAD:" + form], cwd, env)
                        got_b = by_blob.get(rev.stdout.decode().strip()) \
                            if rev.returncode == 0 else None
                        want_b = nf_blob_path(prefix, form)
                        self.assertEqual(got_b, want_b
                                         if want_b in head else None)
                        ls = run(["git", "ls-files", "--full-name", "--",
                                  form], cwd, env)
                        want_d = nf_pathspec_path(prefix, form)
                        if want_d is None:
                            self.assertEqual(ls.returncode, 128)
                        else:
                            self.assertEqual(ls.returncode, 0)
                            got = ls.stdout.decode().splitlines()
                            self.assertEqual(got, [want_d] if want_d in head
                                             else [])
        finally:
            shutil.rmtree(top, ignore_errors=True)

    def test_2141_side_is_what_the_git_model_predicts(self):
        self.assertEqual(self.classes["model"], [], self.summary)

    def test_every_scenario_agrees_except_d19(self):
        self.assertEqual(self.classes["unexpected"], [], self.summary)

    def test_session_relative_names_never_differ(self):
        for sc, old, new, _ in self.results:
            if session_relative(sc.form):
                with self.subTest(scenario=nf_key(sc)):
                    self.assertEqual(new, old)

    def test_no_difference_at_the_repo_top(self):
        for sc, old, new, _ in self.results:
            if sc.session == "root":
                with self.subTest(scenario=nf_key(sc)):
                    self.assertEqual(new, old)

    def test_regression_rows_give_the_2141_decision(self):
        for sc, expected in NF_REGRESSION_ROWS:
            with self.subTest(scenario=nf_key(sc)):
                _, old, new, _ = self.by_scenario[sc]
                self.assertEqual(outcome(old), expected)
                self.assertEqual(new, old)

    def test_d19_rows_differ_exactly_as_decided(self):
        for sc, want_old, want_new in NF_D19_ROWS:
            with self.subTest(scenario=nf_key(sc)):
                _, old, new, (_, _, _, _, blob) = self.by_scenario[sc]
                self.assertIsNotNone(blob)
                self.assertEqual(outcome(old), want_old)
                self.assertEqual(outcome(new), want_new)
                self.assertEqual(old["blobs"], {sc.form: blob}
                                 if want_old == WRITE else {})
                self.assertEqual(new["blobs"], {sc.form: blob}
                                 if want_new == WRITE else {})
        self.assertGreaterEqual(len(self.classes["d19"]), 4)
        self.assertGreaterEqual(len(self.classes["n13"]), 3)


def show_summary(text):
    """Print a grid's summary line and also raise it as a GridSummary
    warning: `pytest -q` hides the print of a passing test but lists the
    warnings at the end of its output, so the line reaches the CI log."""
    print("\n" + text)
    warnings.warn(text.splitlines()[0], GridSummary, stacklevel=2)


class GridSummary(UserWarning):
    """The grid's one-line summary, surfaced in the pytest output."""


class TestParityGrid(unittest.TestCase):
    """The grid, run once for the class (about 20-30 seconds)."""

    @classmethod
    def setUpClass(cls):
        cls.scenarios = all_scenarios()
        start = time.time()
        cls.results = run_grid(cls.scenarios, materialize_dd8e4ab(cls))
        cls.seconds = time.time() - start
        cls.by_scenario = {r[0]: r for r in cls.results}
        cls.classes = classify(cls.results)
        show_summary(report(cls.results, cls.seconds))

    def test_grid_covers_every_pair(self):
        self.assertGreaterEqual(len(self.scenarios), 150)
        keys = list(AXES)
        rows = [s for s in self.scenarios]
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                seen = {(getattr(r, keys[i]), getattr(r, keys[j])) for r in rows}
                for a in AXES[keys[i]]:
                    for b in AXES[keys[j]]:
                        if valid_partial({keys[i]: a, keys[j]: b}):
                            self.assertIn((a, b), seen, (keys[i], keys[j]))

    def test_every_scenario_agrees_except_d19_and_known(self):
        self.assertEqual(self.classes["unexpected"], [],
                         report(self.results, self.seconds))

    def test_not_creatable_only_where_a_filesystem_may_refuse(self):
        for sc, why in self.classes["not_creatable"]:
            self.assertTrue(
                ("ending", sc.ending) in MAY_BE_UNCREATABLE
                or ("name", sc.name) in MAY_BE_UNCREATABLE,
                "%s not creatable: %s" % (key_of(sc), why))
        created = len(self.results) - len(self.classes["not_creatable"])
        self.assertGreaterEqual(created, 150)

    def test_everything_is_creatable_on_linux(self):
        """On Linux (the CI machine) every scenario must be built and run, so
        none can stop running there without a failure."""
        if not sys.platform.startswith("linux"):
            return
        self.assertEqual(self.classes["not_creatable"], [],
                         report(self.results, self.seconds))

    def test_regression_rows_give_the_2141_decision(self):
        fresh = dict(FRESHNESS_REFUSALS)
        for sc, expected in REGRESSION_ROWS:
            with self.subTest(scenario=key_of(sc)):
                _, old, new, _, why = self.by_scenario[sc]
                self.assertIsNone(why)
                self.assertEqual(outcome(old), expected)
                if sc in fresh:
                    # D-09: the helper refuses here, everything else equal.
                    self.assertTrue(freshness_refusal(sc, old, new,
                                                      fresh[sc]), new)
                else:
                    self.assertEqual(new, old)

    def test_d19_rows_differ_exactly_as_decided(self):
        for sc in D19_ROWS:
            with self.subTest(scenario=key_of(sc)):
                _, old, new, blob, why = self.by_scenario[sc]
                self.assertIsNone(why)
                self.assertIsNotNone(blob)
                self.assertEqual(old["blobs"], {sc.name: blob})
                self.assertEqual(outcome(old), WRITE)
                self.assertEqual(new["blobs"], {})
                self.assertEqual(outcome(new), OPEN)
        self.assertGreaterEqual(len(self.classes["d19"]), len(D19_ROWS))

    def test_freshness_refusals_are_found_exactly(self):
        listed = [sc for sc, _ in FRESHNESS_REFUSALS]
        self.assertEqual(len(set(listed)), len(listed))
        for sc, cause in FRESHNESS_REFUSALS:
            with self.subTest(scenario=key_of(sc)):
                _, old, new, _, why = self.by_scenario[sc]
                self.assertIsNone(why)
                self.assertIn(cause, ("unverifiable", "deleted"))
                self.assertTrue(freshness_refusal(sc, old, new, cause),
                                (old, new))
        self.assertEqual(sorted(map(key_of, self.classes["fresh"])),
                         sorted(map(key_of, listed)))
        # Nothing outside the list refuses for freshness.
        for sc, _, new, _, why in self.results:
            if why is None and new and "stale" in new:
                self.assertIn(sc, set(listed), key_of(sc))

    def test_mutant_freshness_refusal_rejects_other_shapes(self):
        sc, cause = FRESHNESS_REFUSALS[0]
        _, old, new, _, _ = self.by_scenario[sc]
        self.assertTrue(freshness_refusal(sc, old, new, cause))
        other = "deleted" if cause == "unverifiable" else "unverifiable"
        bad = (
            dict(new, counts=[9, 9, 9]),
            dict(new, blobs={"x.ts": "f" * 40}),
            dict(new, action="write"),
            dict(new, next="stop-refused"),
            dict(new, stale=new["stale"] * 2),
            dict(new, stale=[dict(new["stale"][0], cause=other)]),
        )
        for mutant in bad:
            with self.subTest(mutant=mutant):
                self.assertFalse(freshness_refusal(sc, old, mutant, cause))
        # 2.14.1 itself stopping, or refusing, is never a D-09 difference.
        self.assertFalse(freshness_refusal(sc, {"stop": "gate"}, new, cause))
        self.assertFalse(freshness_refusal(sc, dict(old, action="refuse"),
                                           new, cause))

    def test_known_differences_are_still_found_exactly(self):
        for sc, old, new in KNOWN_DIFFERENCES:
            with self.subTest(scenario=key_of(sc)):
                _, got_old, got_new, _, why = self.by_scenario[sc]
                self.assertIsNone(why)
                self.assertEqual((got_old, got_new), (old, new))
                self.assertNotEqual(old, new)


class TestGridStatesBindReviewedTree(unittest.TestCase):
    """Every grid state carries a dismissal (BUGS_HASH). Each one, in both
    grid classes, sits on a reviewed tree of its own repo that holds the
    dismissed file, unchanged on disk, so both sides see the write path for
    real reviewed code. Scenarios are built only (no side runs)."""

    def test_decision_bearing_states_bind_reviewed_tree(self):
        top = os.path.realpath(tempfile.mkdtemp(prefix="vc-gridlock-"))
        env = clean_env()
        saved = dict(os.environ)
        os.environ.clear()
        os.environ.update(env)
        try:
            shim = make_shim(top)

            def grid_one(index, sc):
                base = os.path.join(top, "s%04d" % index)
                try:
                    _, _, state, _ = build(sc, base, top, shim)
                except NotCreatable:
                    return None
                repo = os.path.join(base, "repo" + ENDINGS[sc.ending])
                return (key_of(sc), repo, state)

            def nf_one(index, layout):
                repo, head, reviewed = nf_build(
                    "repo", layout, (), "clean",
                    os.path.join(top, "n%03d" % index), top)
                rel = NF_FILES[NF_LAYOUTS[layout][0]][0]
                return ("nf " + layout, repo,
                        nf_state(rel, head[rel], reviewed))

            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=min(8, os.cpu_count() or 2)) as pool:
                built = list(pool.map(lambda a: grid_one(*a),
                                      enumerate(all_scenarios())))
                built += list(pool.map(lambda a: nf_one(*a),
                                       enumerate(NF_LAYOUTS)))
            built = [b for b in built if b is not None]
            self.assertGreaterEqual(len(built), 150)
            problems = {}
            for label, repo, state in built:
                if decided_files(state) != [DECIDED_FILE]:
                    problems[label] = decided_files(state)
                    continue
                found = check_decided_fixture(repo, state)
                if found:
                    problems[label] = found
            self.assertEqual(problems, {})
            # Mutant: a grid state without its reviewed tree is caught.
            label, repo, state = built[0]
            del state["passes"][-1]["reviewed_tree"]
            self.assertNotEqual(check_decided_fixture(repo, state), [])
        finally:
            os.environ.clear()
            os.environ.update(saved)
            shutil.rmtree(top, ignore_errors=True)


class TestScriptUnderBash(unittest.TestCase):
    """The script is POSIX sh; under bash (3.2 on macOS) it gives the same
    result on the regression and D-19 rows."""

    def test_bash_matches_sh(self):
        bash = "/bin/bash"
        self.assertTrue(os.path.exists(bash))
        rows = [sc for sc, _ in REGRESSION_ROWS] + list(D19_ROWS)
        old_dir = materialize_dd8e4ab(self)
        a = run_grid(rows, old_dir, shell="/bin/sh")
        b = run_grid(rows, old_dir, shell=bash)
        for (sc, old_sh, _, _, _), (_, old_bash, _, _, _) in zip(a, b):
            with self.subTest(scenario=key_of(sc)):
                self.assertEqual(old_bash, old_sh)


def main(argv):
    """`--grid [helper.py]` runs both grid classes (every assertion the
    test suite makes on them: agreement, the named regression rows, the
    D-19 rows, the known differences, the git model) against `helper.py`
    (default: finalize_inputs.py beside this file) and exits non-zero when
    any fails. Anything else is passed to unittest."""
    global HELPER_PY
    if argv[:1] == ["--grid"]:
        if len(argv) > 1:
            HELPER_PY = os.path.abspath(argv[1])
        suite = unittest.TestSuite()
        loader = unittest.defaultTestLoader
        for case in (TestParityGrid, TestNameFormGrid):
            suite.addTests(loader.loadTestsFromTestCase(case))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", GridSummary)
            result = unittest.TextTestRunner(verbosity=1).run(suite)
        return 0 if result.wasSuccessful() else 1
    return unittest.main(argv=[sys.argv[0]] + argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
