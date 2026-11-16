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
line must appear there verbatim, in order) and asserts that the modules both
sides share (`guard.py`, `carry_state.py`, `finalize_gate.py`, `fixcommit.py`)
are byte-identical to dd8e4ab, so the 2.14.1 side really is 2.14.1.

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

Run directly (`python3 test_finalize_parity_grid.py --grid`) to print the
scenario count, the not-creatable list and the wall time.
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

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import carry_state  # noqa: E402  (fixture building only: record_decisions)
import gitfixture  # noqa: E402  (helper_env isolation)

SOURCE_COMMIT = "dd8e4ab"
SOURCE_DOC = "plugins/vibe-check/phases/shared/90-finalize.md"
SOURCE_LINES = (13, 22)  # the step 1 text the script transcribes (1-based)
STEP1_SH = os.path.join(SCRIPTS_DIR, "fixtures", "finalize_step1_2141.sh")
HELPER_PY = os.path.join(SCRIPTS_DIR, "finalize_inputs.py")
GUARD_PY = os.path.join(SCRIPTS_DIR, "guard.py")
CARRY_STATE_PY = os.path.join(SCRIPTS_DIR, "carry_state.py")
FINALIZE_GATE_PY = os.path.join(SCRIPTS_DIR, "finalize_gate.py")
FIXTURE = os.path.join(SCRIPTS_DIR, "fixtures", "phase45-loop-state.json")
SHARED_WITH_2141 = ("guard.py", "carry_state.py", "finalize_gate.py",
                    "fixcommit.py")

ARCH_HASH = "5e78e90a6bf05e6a409b4aa3271e5e4df072735a074a9947a0a766a3d794af67"
BUGS_HASH = "7479a9b5fd5b36bce327aea4d49db8dcbe4193208c2b2ca3f1d3ac98368e6644"
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
        env = clean_env()
        for name in SHARED_WITH_2141:
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

# Differences with a mechanism not yet ruled on by the owner. Shrink-only:
# each entry is (scenario, 2.14.1 outcome, helper outcome) and must still be
# found, exactly, by the grid.
KNOWN_DIFFERENCES = ()


def all_scenarios():
    rows = list(pairwise_rows())
    for sc, _ in REGRESSION_ROWS:
        rows.append(sc)
    rows.extend(D19_ROWS)
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


def fixture_state(name, verdict, blob):
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
    extra = []
    if sc.name == "nl.ts\n":
        extra.append(("nl.ts\n", "newline name\n"))
    try:
        b.init_repo(repo, FILES, LINKS, extra)
    except OSError as exc:
        raise NotCreatable(str(exc))
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
    return session, env, fixture_state(sc.name, sc.verdict, blob), blob


def run(argv, cwd, env, stdin_bytes=b""):
    return subprocess.run(argv, cwd=cwd, env=env, input=stdin_bytes,
                          capture_output=True, timeout=CALL_TIMEOUT)


def side_2141(state, state_path, files_dir, session, env, shell):
    """Step 1 through the 2.14.1 script for each last-pass fix verdict, then
    the 2.14.1 counting command and gate."""
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
        proc = run([shell, STEP1_SH, f, out], session, dict(env, GUARD_PY=GUARD_PY))
        if proc.returncode == 0:
            with open(out, "rb") as fh:
                blobs[f] = fh.read().decode("utf-8")
    bp = os.path.join(files_dir, "blobs-2141.json")
    with open(bp, "w", encoding="utf-8") as fh:
        json.dump(blobs, fh)
    with open(state_path, "rb") as fh:
        state_bytes = fh.read()
    c = run([sys.executable, CARRY_STATE_PY, "finalize-counts", "--head-blobs",
             bp], session, env, state_bytes)
    if c.returncode != 0:
        return {"stop": "state"}
    counts = json.loads(c.stdout)
    flags = {"state_file_present": True,
             "outstanding_cw": counts["outstanding_cw"],
             "unacknowledged_medium": counts["unacknowledged_medium"],
             "undecided_nv": counts["undecided_nv"],
             "noninteractive": False, "pr_mode": False, "range_mode": False}
    g = run([sys.executable, FINALIZE_GATE_PY], session, env,
            json.dumps({"flags": flags}).encode())
    if g.returncode != 0:
        return {"stop": "gate"}
    return {"blobs": blobs,
            "counts": [counts["outstanding_cw"], counts["unacknowledged_medium"],
                       counts["undecided_nv"]],
            "action": json.loads(g.stdout)["action"]}


def side_helper(state_path, files_dir, session, env, helper=HELPER_PY):
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
    return {"blobs": blobs,
            "counts": [c["outstanding_cw"], c["unacknowledged_medium"],
                       c["undecided_nv"]],
            "action": got["action"]}


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


def run_one(index, sc, top, shim, shell="/bin/sh", helper=HELPER_PY):
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
    old = side_2141(state, state_path, files_dir, session, env, shell)
    new = side_helper(state_path, files_dir, session, env, helper)
    return sc, old, new, blob, None


def run_grid(scenarios, shell="/bin/sh", helper=HELPER_PY, workers=None):
    """[(scenario, 2.14.1 outcome, helper outcome, HEAD blob, not-creatable
    reason)] in scenario order; every temp folder is removed afterwards."""
    top = os.path.realpath(tempfile.mkdtemp(prefix="vc-grid-"))
    try:
        shim = make_shim(top)
        workers = workers or min(8, os.cpu_count() or 2)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(run_one, i, sc, top, shim, shell, helper)
                       for i, sc in enumerate(scenarios)]
            return [f.result() for f in futures]
    finally:
        shutil.rmtree(top, ignore_errors=True)


def outcome(o):
    return None if o is None or "stop" in o else (o["counts"], o["action"])


def d19_difference(sc, old, new, blob):
    """True only for the D-19 shape: session in a subfolder, the file edited
    or staged, 2.14.1 fingerprints it with its HEAD blob, the helper leaves
    exactly that file out, and the two decisions follow from that."""
    if sc.session not in BELOW_TOP or sc.content not in EDITED:
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
    """-> dict of lists: agree, d19, known, unexpected, not_creatable."""
    known = {sc: (o, n) for sc, o, n in KNOWN_DIFFERENCES}
    out = {"agree": [], "d19": [], "known": [], "unexpected": [],
           "not_creatable": []}
    for sc, old, new, blob, why in results:
        if why is not None:
            out["not_creatable"].append((sc, why))
        elif old == new:
            out["agree"].append(sc)
        elif d19_difference(sc, old, new, blob):
            out["d19"].append((sc, old, new))
        elif sc in known and known[sc] == (old, new):
            out["known"].append(sc)
        else:
            out["unexpected"].append((sc, old, new))
    return out


def report(results, seconds):
    c = classify(results)
    lines = ["%d scenarios in %.1f s: %d agree, %d D-19, %d known differences, "
             "%d unexpected, %d not creatable here"
             % (len(results), seconds, len(c["agree"]), len(c["d19"]),
                len(c["known"]), len(c["unexpected"]), len(c["not_creatable"]))]
    for sc, why in c["not_creatable"]:
        lines.append("  not creatable here: %s (%s)" % (key_of(sc), why))
    for sc, old, new in c["unexpected"]:
        lines.append("  DIFFERENT %s\n      2.14.1 %r\n      helper %r"
                     % (key_of(sc), old, new))
    return "\n".join(lines)


class TestParityGrid(unittest.TestCase):
    """The grid, run once for the class (about 20-30 seconds)."""

    @classmethod
    def setUpClass(cls):
        cls.scenarios = all_scenarios()
        start = time.time()
        cls.results = run_grid(cls.scenarios)
        cls.seconds = time.time() - start
        cls.by_scenario = {r[0]: r for r in cls.results}
        cls.classes = classify(cls.results)
        print("\n" + report(cls.results, cls.seconds))

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

    def test_regression_rows_give_the_2141_decision(self):
        for sc, expected in REGRESSION_ROWS:
            with self.subTest(scenario=key_of(sc)):
                _, old, new, _, why = self.by_scenario[sc]
                self.assertIsNone(why)
                self.assertEqual(outcome(old), expected)
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

    def test_known_differences_are_still_found_exactly(self):
        for sc, old, new in KNOWN_DIFFERENCES:
            with self.subTest(scenario=key_of(sc)):
                _, got_old, got_new, _, why = self.by_scenario[sc]
                self.assertIsNone(why)
                self.assertEqual((got_old, got_new), (old, new))
                self.assertNotEqual(old, new)


class TestScriptUnderBash(unittest.TestCase):
    """The script is POSIX sh; under bash (3.2 on macOS) it gives the same
    result on the regression and D-19 rows."""

    def test_bash_matches_sh(self):
        bash = "/bin/bash"
        self.assertTrue(os.path.exists(bash))
        rows = [sc for sc, _ in REGRESSION_ROWS] + list(D19_ROWS)
        a = run_grid(rows, shell="/bin/sh")
        b = run_grid(rows, shell=bash)
        for (sc, old_sh, _, _, _), (_, old_bash, _, _, _) in zip(a, b):
            with self.subTest(scenario=key_of(sc)):
                self.assertEqual(old_bash, old_sh)


def main(argv):
    if argv[:1] == ["--grid"]:
        helper = argv[1] if len(argv) > 1 else HELPER_PY
        scenarios = all_scenarios()
        start = time.time()
        results = run_grid(scenarios, helper=helper)
        print(report(results, time.time() - start))
        return 1 if classify(results)["unexpected"] else 0
    return unittest.main(argv=[sys.argv[0]] + argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
