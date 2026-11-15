"""A name that is printed in one Bash call and pasted into a later one is
refused before it is printed when it holds a character that is live inside
double quotes.

`00-scope.md` prints `PHASE_DIR=` and `05-state.md` prints
`LEGACY_STATE_FILE=` / `STATE_FILE=`; later blocks are told to paste those
literals inside double quotes. The values come from the reviewed repo's
folder name, branch name and `.planning/` directory names, so a crafted name
holding `$(...)`, a backtick or a `"` would run as a command when pasted. Each
print site refuses such a value (`$`, backtick, `"`, `\\`, newline, carriage
return) and stops with one message on stderr, printing no `NAME=` line.

Every case runs the real fenced blocks, taken from the live files, each in a
fresh `/bin/bash -s` (the shell the shipped fences run under on macOS) inside
a temporary git repo. A harness then pastes whatever the setter printed into
the later blocks the way the model would, and the test checks that no marker
file appeared. The payloads only ever `touch` a file inside the temp repo.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gitfixture  # noqa: E402  (shared temp-repo helper)
from test_cross_call_vars import (  # noqa: E402
    PLUGIN_ROOT, SCOPE_REL, STATE_REL, fence_holding, substitute)

BASH = "/bin/bash"
MARKER = "PWNED"
GUARD_NEEDLE = "in *[\\$\\`\\\"\\\\$'\\n\\r']*)"


def unguarded(body):
    """`body` with its guard line removed (the mutant)."""
    lines = body.split("\n")
    kept = [l for l in lines if GUARD_NEEDLE not in l]
    if len(kept) != len(lines) - 1:
        raise AssertionError("want exactly one guard line in %r" % body)
    return "\n".join(kept)


def run_bash(script, cwd, extra_env=None):
    tmpdir = tempfile.mkdtemp(dir=os.path.dirname(os.path.dirname(cwd)))
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "VC_ROOT": PLUGIN_ROOT, "TMPDIR": tmpdir,
           "GUARD_PY": os.path.join(PLUGIN_ROOT, "scripts", "guard.py"),
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    env.update(extra_env or {})
    proc = subprocess.run([BASH, "-s"], input=script + "\n", cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=60)
    return proc.returncode, proc.stdout, proc.stderr


def printed(out, name):
    """Every value printed on a `NAME=` line."""
    return [l[len(name) + 1:] for l in out.split("\n")
            if l.startswith(name + "=")]


def markers(root):
    """Paths of every marker file under `root`."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        found += [os.path.join(dirpath, n) for n in filenames if n == MARKER]
    return found


def paste(readers, names, out):
    """The readers with each `$NAME` replaced by what the setter printed
    after `NAME=` (empty when it printed no such line), as the model would."""
    carried = []
    for body in readers:
        for name in names:
            values = printed(out, name)
            body = body.replace("$" + name, values[0] if values else "")
        carried.append(body)
    return carried


# Values that must be refused, by the character they carry. The `$(` and
# backtick payloads run `touch PWNED` when pasted unguarded; the `"` payload
# breaks out of the double quotes it is pasted into.
DOLLAR = "x$(touch${IFS}%s)" % MARKER
BACKTICK = "x`touch${IFS}%s`" % MARKER
QUOTE = 'x";touch${IFS}%s;"' % MARKER


class GuardCase(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.n = 0

    def repo(self, folder="repo", branch=None):
        """A fresh repo at <tmp>/<case>/<folder> with one commit."""
        self.n += 1
        work = os.path.join(self.tmp, "c%d" % self.n)
        os.makedirs(work)
        made = gitfixture.make_repo(work)
        gitfixture.write(made, "src/a.txt", "a\n")
        gitfixture.git(made, "add", "-A")
        gitfixture.git(made, "commit", "-qm", "base")
        if branch is not None:
            gitfixture.git(made, "checkout", "-qb", branch)
        path = os.path.join(work, folder)
        if path != made:
            os.rename(made, path)
        return path

    def run_case(self, repo, setter, readers, names, extra_env=None):
        """(setter result, reader results, marker files)."""
        first = run_bash(setter, repo, extra_env)
        rest = [run_bash(b, repo) for b in paste(readers, names, first[1])]
        return first, rest, markers(os.path.dirname(repo))

    def assert_refused(self, first, names, found, label):
        rc, out, err = first
        self.assertNotEqual(rc, 0, label)
        for name in names:
            self.assertEqual(printed(out, name), [], label)
        self.assertIn("Review halted", err, label)
        self.assertEqual(found, [], label)

    def assert_mutant_trips(self, first, names, found, label):
        """Without the guard the case would fail: a NAME= line is printed or
        the pasted value ran the marker command."""
        tripped = bool(found) or any(printed(first[1], n) for n in names)
        self.assertTrue(tripped, label)


class TestPhaseDirGuard(GuardCase):
    """00-scope.md mode 4: the phase dir found under `.planning/`."""

    NAMES = ["PHASE_DIR"]

    def setter(self, arg, mutant=False):
        body = fence_holding(SCOPE_REL, "PHASE_DIR=$(find")
        body = unguarded(body) if mutant else body
        return substitute(body, [("<arg>", arg)])

    @staticmethod
    def readers():
        return [fence_holding(SCOPE_REL,
                              'python3 "$GUARD_PY" --root "$PWD/.planning"'),
                fence_holding(SCOPE_REL, "PHASE_START=$(git log")]

    def phase_repo(self, rel):
        repo = self.repo()
        gitfixture.write(repo, os.path.join(rel, "02-01-PLAN.md"), "plan\n")
        gitfixture.git(repo, "add", "-A")
        gitfixture.git(repo, "commit", "-qm", "phase")
        return repo

    # (label, phase dir under the repo, the id the owner typed)
    BAD = [
        ("dollar", ".planning/phases/02-" + DOLLAR, "02"),
        ("backtick", ".planning/phases/02-x`touch %s`" % MARKER, "02"),
        ("quote", ".planning/phases/02-" + QUOTE, "02"),
        ("backslash", ".planning/phases/02-a\\b", "02"),
        ("carriage return", ".planning/phases/02-a\rb", "02"),
        ("dollar in the milestone folder",
         ".planning/milestones/v1%s-phases/02-code-review" % DOLLAR,
         "02-code-review"),
    ]
    GOOD = [
        ("plain", ".planning/phases/02-code-review", "02"),
        ("space", ".planning/phases/02-my phase", "02"),
        ("punctuation", ".planning/milestones/v1.2_(a)-phases/02-x+y,z", "02"),
    ]

    def test_bad_names_are_refused_and_nothing_runs(self):
        for label, rel, arg in self.BAD:
            with self.subTest(label):
                repo = self.phase_repo(rel)
                first, _, found = self.run_case(
                    repo, self.setter(arg), self.readers(), self.NAMES)
                self.assert_refused(first, self.NAMES, found, label)

    def test_good_names_print_and_round_trip(self):
        for label, rel, arg in self.GOOD:
            with self.subTest(label):
                repo = self.phase_repo(rel)
                first, rest, found = self.run_case(
                    repo, self.setter(arg), self.readers(), self.NAMES)
                self.assertEqual(first[0], 0, first)
                self.assertEqual(printed(first[1], "PHASE_DIR"), [rel])
                self.assertEqual([r[0] for r in rest], [0, 0], rest)
                self.assertIn("contained", rest[0][1])
                sha = gitfixture.git(repo, "log", "--format=%H", "-1",
                                     "--", ".planning").stdout.strip()
                self.assertEqual(rest[1][1], "PHASE_START=%s\n" % sha)
                self.assertEqual(found, [])

    def test_without_the_guard_the_cases_fail(self):
        for label, rel, arg in self.BAD:
            with self.subTest(label):
                repo = self.phase_repo(rel)
                first, _, found = self.run_case(
                    repo, self.setter(arg, mutant=True), self.readers(),
                    self.NAMES)
                self.assert_mutant_trips(first, self.NAMES, found, label)
                if "dollar" in label or label == "backtick":
                    self.assertTrue(found, label)


class TestStateFileGuard(GuardCase):
    """05-state.md: both state-file key branches."""

    NAMES = ["LEGACY_STATE_FILE", "STATE_FILE"]
    GSD_NEEDLE = 'STATE_FILE=".turingmind/state/format-53/${PHASE_ID}'
    BRANCH_NEEDLE = "BRANCH_SLUG=$(git branch"

    @staticmethod
    def readers():
        return [fence_holding(STATE_REL, 'review_archive.py" migrate'),
                substitute(fence_holding(STATE_REL, "last-head-sha"),
                           [('"$FINALIZE_MODE"', '"0"')]),
                fence_holding(STATE_REL, 'carry_state.py" decided'),
                fence_holding(STATE_REL, 'carry_state.py" deferred')]

    def setter(self, needle, mutant=False):
        body = fence_holding(STATE_REL, needle)
        return unguarded(body) if mutant else body

    @staticmethod
    def seed_state(repo, key):
        sha = gitfixture.git(repo, "rev-parse", "HEAD").stdout.strip()
        gitfixture.write(repo, ".turingmind/state/%s.json" % key,
                         json.dumps({"passes": [{"pass_number": 1,
                                                 "head_sha": sha,
                                                 "findings": []}]}))
        return sha

    # GSD key: `${PHASE_ID}` is left in the block and supplied from the
    # environment, so the raw name reaches the value exactly as written.
    GSD_BAD = [("dollar", "02-" + DOLLAR), ("backtick", "02-" + BACKTICK),
               ("quote", "02-" + QUOTE), ("backslash", "02-a\\b"),
               ("newline", "02-a\nb"), ("carriage return", "02-a\rb")]
    GSD_GOOD = [("plain", "02-code-review"), ("space", "02-my phase")]
    # Repo-and-branch key: (label, repo folder, branch). git refuses a
    # backslash, newline or carriage return in a branch name.
    BRANCH_BAD = [("dollar in the branch", "repo", DOLLAR),
                  ("backtick in the branch", "repo", BACKTICK),
                  ("quote in the branch", "repo", QUOTE),
                  ("dollar in the folder", "r" + DOLLAR, "main"),
                  ("backtick in the folder", "r" + BACKTICK, "main")]
    BRANCH_GOOD = [("plain", "repo", "main"),
                   ("punctuation", "repo.v2_(a)", "feat/x-1.2_(y)")]

    def bad_cases(self, mutant=False):
        for label, phase_id in self.GSD_BAD:
            repo = self.repo()
            yield ("gsd " + label, repo, self.setter(self.GSD_NEEDLE, mutant),
                   {"PHASE_ID": phase_id})
        for label, folder, branch in self.BRANCH_BAD:
            repo = self.repo(folder, None if branch == "main" else branch)
            yield ("branch " + label, repo,
                   self.setter(self.BRANCH_NEEDLE, mutant), None)

    def test_bad_names_are_refused_and_nothing_runs(self):
        for label, repo, setter, env in self.bad_cases():
            with self.subTest(label):
                first, _, found = self.run_case(
                    repo, setter, self.readers(), self.NAMES, env)
                self.assert_refused(first, self.NAMES, found, label)

    def test_good_names_print_and_round_trip(self):
        cases = [("gsd " + l, self.repo(), self.GSD_NEEDLE, {"PHASE_ID": p},
                  p) for l, p in self.GSD_GOOD]
        for label, folder, branch in self.BRANCH_GOOD:
            repo = self.repo(folder, None if branch == "main" else branch)
            cases.append(("branch " + label, repo, self.BRANCH_NEEDLE, None,
                          "%s-%s" % (folder, branch.replace("/", "-"))))
        for label, repo, needle, env, key in cases:
            with self.subTest(label):
                sha = self.seed_state(repo, key)
                first, rest, found = self.run_case(
                    repo, self.setter(needle), self.readers(), self.NAMES,
                    env)
                self.assertEqual(first[0], 0, first)
                self.assertEqual(
                    printed(first[1], "STATE_FILE"),
                    [".turingmind/state/format-53/%s.json" % key])
                self.assertEqual([r[0] for r in rest], [0, 0, 0, 0], rest)
                self.assertEqual(rest[1][1], "LAST_REVIEWED_SHA=%s\n" % sha)
                self.assertTrue(os.path.isfile(os.path.join(
                    repo, ".turingmind/state/format-53/%s.json" % key)))
                self.assertEqual(found, [])

    def test_without_the_guard_the_cases_fail(self):
        for label, repo, setter, env in self.bad_cases(mutant=True):
            with self.subTest(label):
                first, _, found = self.run_case(
                    repo, setter, self.readers(), self.NAMES, env)
                self.assert_mutant_trips(first, self.NAMES, found, label)
                if "dollar" in label or "backtick" in label:
                    self.assertTrue(found, label)


if __name__ == "__main__":
    unittest.main()
