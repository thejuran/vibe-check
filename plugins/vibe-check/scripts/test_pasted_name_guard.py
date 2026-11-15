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


# The guard's character class, and the same class with one member taken out
# (the per-character mutants).
BRACKET = "[\\$\\`\\\"\\\\$'\\n\\r']"
assert GUARD_NEEDLE == "in *" + BRACKET + "*)"
BLOCKED = [("dollar", "$"), ("backtick", "`"), ("quote", '"'),
           ("backslash", "\\"), ("newline", "\n"), ("carriage return", "\r")]
WITHOUT = {
    "$": "[\\`\\\"\\\\$'\\n\\r']",
    "`": "[\\$\\\"\\\\$'\\n\\r']",
    '"': "[\\$\\`\\\\$'\\n\\r']",
    "\\": "[\\$\\`\\\"$'\\n\\r']",
    "\n": "[\\$\\`\\\"\\\\$'\\r']",
    "\r": "[\\$\\`\\\"\\\\$'\\n']",
}


def drop_member(body, char):
    """`body` with only `char` taken out of its one guard pattern."""
    if body.count(GUARD_NEEDLE) != 1:
        raise AssertionError("want exactly one guard line in %r" % body)
    return body.replace(GUARD_NEEDLE, "in *" + WITHOUT[char] + "*)")


def mutant_tripped(first, name, value):
    """True only when the setter exited 0 and printed exactly
    `NAME=<value>` on its own line(s) -- the bad value got through."""
    rc, out, _ = first
    line = "%s=%s\n" % (name, value)
    return rc == 0 and (out.startswith(line) or ("\n" + line) in out)


def run_bash(script, cwd, extra_env=None):
    tmpdir = tempfile.mkdtemp(dir=os.path.dirname(os.path.dirname(cwd)))
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "VC_ROOT": PLUGIN_ROOT, "TMPDIR": tmpdir,
           "GUARD_PY": os.path.join(PLUGIN_ROOT, "scripts", "guard.py"),
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    env.update(extra_env or {})
    # Bytes in and out, decoded without newline translation, so a carriage
    # return in a printed value reaches the checks as itself.
    proc = subprocess.run([BASH, "-s"], input=(script + "\n").encode(),
                          cwd=cwd, env=env, capture_output=True, timeout=60)
    return (proc.returncode, proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"))


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

    def assert_mutant_trips(self, first, name, value, label):
        """Without (part of) the guard the case would fail: the setter
        completed and printed exactly `NAME=<the bad value>`. A refused run,
        or a printed line whose value lacks the bad character, does not
        count (`mutant_tripped`)."""
        self.assertTrue(mutant_tripped(first, name, value), label)


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
                self.assert_mutant_trips(first, "PHASE_DIR", rel, label)
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
        """(label, repo, setter, env, the STATE_FILE value it would print)."""
        for label, phase_id in self.GSD_BAD:
            repo = self.repo()
            yield ("gsd " + label, repo, self.setter(self.GSD_NEEDLE, mutant),
                   {"PHASE_ID": phase_id},
                   ".turingmind/state/format-53/%s.json" % phase_id)
        for label, folder, branch in self.BRANCH_BAD:
            repo = self.repo(folder, None if branch == "main" else branch)
            yield ("branch " + label, repo,
                   self.setter(self.BRANCH_NEEDLE, mutant), None,
                   ".turingmind/state/format-53/%s-%s.json" % (folder, branch))

    def test_bad_names_are_refused_and_nothing_runs(self):
        for label, repo, setter, env, _ in self.bad_cases():
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
        for label, repo, setter, env, value in self.bad_cases(mutant=True):
            with self.subTest(label):
                first, _, found = self.run_case(
                    repo, setter, self.readers(), self.NAMES, env)
                self.assert_mutant_trips(first, "STATE_FILE", value, label)
                if "dollar" in label or "backtick" in label:
                    self.assertTrue(found, label)


ALL_STATE_REL = "phases/review/05-state-all.md"
ALL_NEEDLE = "ALL_STATE_FILE=$(set -o pipefail"

# Shell functions put in front of a real block to hand it a value that the
# filesystem or git cannot carry. The block itself is unchanged.
FAKE_HEAD = "head() { printf '%s\\n' \"$INJECT\"; }\n"
FAKE_GIT_BRANCH = ('git() { if [ "$1" = branch ]; then printf \'%s\\n\' '
                   '"$INJECT"; else command git "$@"; fi; }\n')
STUB_STATEPATH = ("import json, os, sys\nsys.stdin.read()\n"
                  "print(json.dumps({'current_path': os.environ['INJECT'], "
                  "'reason': ''}))\n")


class TestEachCharacterAtEachSite(GuardCase):
    """Each blocked character on its own, at each guarded print site: a name
    holding only that one bad character is refused, and taking only that
    character out of the guard pattern lets it through. Where the filesystem
    or git cannot carry the character, the real block is handed the value
    (`how` says which)."""

    SITES = ("00-scope.md PHASE_DIR", "05-state.md GSD key",
             "05-state.md repo-and-branch key", "05-state-all.md --all key")

    def site_case(self, site, char, mutant):
        """(first result, NAME, the value it would print, how carried)."""
        bad = "x%sy" % char
        if site == "00-scope.md PHASE_DIR":
            body = fence_holding(SCOPE_REL, "PHASE_DIR=$(find")
            body = substitute(drop_member(body, char) if mutant else body,
                              [("<arg>", "02")])
            rel = ".planning/phases/02-" + bad
            if char == "\n":
                # find's output is read a line at a time (`head -1`, and
                # `grep -c .` for a unique prefix), so a folder name cannot
                # carry a newline into PHASE_DIR; `head` hands it over.
                repo = self.repo()
                first = run_bash(FAKE_HEAD + body, repo, {"INJECT": rel})
                return first, "PHASE_DIR", rel, "injected (head)"
            repo = TestPhaseDirGuard.phase_repo(self, rel)
            return run_bash(body, repo), "PHASE_DIR", rel, "real folder"
        if site == "05-state.md GSD key":
            body = fence_holding(STATE_REL, TestStateFileGuard.GSD_NEEDLE)
            body = drop_member(body, char) if mutant else body
            value = ".turingmind/state/format-53/02-%s.json" % bad
            first = run_bash(body, self.repo(), {"PHASE_ID": "02-" + bad})
            return first, "STATE_FILE", value, "injected (PHASE_ID)"
        if site == "05-state.md repo-and-branch key":
            body = fence_holding(STATE_REL, TestStateFileGuard.BRANCH_NEEDLE)
            body = drop_member(body, char) if mutant else body
            if char in "$`\"":
                value = ".turingmind/state/format-53/repo-%s.json" % bad
                return (run_bash(body, self.repo("repo", bad)), "STATE_FILE",
                        value, "real branch")
            if char == "\r":
                value = ".turingmind/state/format-53/%s-main.json" % bad
                return (run_bash(body, self.repo(bad)), "STATE_FILE", value,
                        "real folder")
            # git refuses a backslash or a newline in a branch name, and
            # `xargs basename` drops a backslash and splits on a newline in
            # the folder name; `git branch` hands the value over.
            value = ".turingmind/state/format-53/repo-%s.json" % bad
            first = run_bash(FAKE_GIT_BRANCH + body, self.repo(),
                             {"INJECT": bad})
            return first, "STATE_FILE", value, "injected (git branch)"
        if site == "05-state-all.md --all key":
            # The --all key is a 12-hex digest from statepath.py, so no repo
            # or branch name can carry a character into it; a stub
            # statepath.py under a stand-in VC_ROOT hands the value over.
            body = fence_holding(ALL_STATE_REL, ALL_NEEDLE)
            body = drop_member(body, char) if mutant else body
            root = os.path.join(self.tmp, "vc%d" % self.n)
            os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
            with open(os.path.join(root, "scripts", "statepath.py"), "w") as fh:
                fh.write(STUB_STATEPATH)
            value = ".turingmind/state/format-53/by-mode/all/%s.json" % bad
            first = run_bash(body, self.repo(),
                             {"VC_ROOT": root, "INJECT": value})
            return first, "STATE_FILE", value, "injected (statepath.py)"
        raise AssertionError(site)

    def test_each_character_alone_is_refused_at_each_site(self):
        for site in self.SITES:
            for label, char in BLOCKED:
                with self.subTest(site=site, char=label):
                    first, name, _, _ = self.site_case(site, char, False)
                    rc, out, err = first
                    self.assertNotEqual(rc, 0, first)
                    self.assertNotIn(name + "=", out)
                    self.assertNotIn("STATE_FILE=", out)
                    self.assertIn("Review halted", err)

    def test_dropping_one_character_from_the_guard_lets_it_through(self):
        for site in self.SITES:
            for label, char in BLOCKED:
                with self.subTest(site=site, char=label):
                    first, name, value, _ = self.site_case(site, char, True)
                    self.assert_mutant_trips(first, name, value,
                                             "%s %s" % (site, label))

    def test_the_mutant_check_cannot_pass_vacuously(self):
        value = ".turingmind/state/format-53/x\ny.json"
        refused = (1, "", "Review halted")
        harmless = (0, "STATE_FILE=.turingmind/state/format-53/x.json\n", "")
        cut = (0, "STATE_FILE=.turingmind/state/format-53/x\n", "")
        through = (0, "LEGACY_STATE_FILE=a\nSTATE_FILE=%s\n" % value, "")
        self.assertFalse(mutant_tripped(refused, "STATE_FILE", value))
        self.assertFalse(mutant_tripped(harmless, "STATE_FILE", value))
        self.assertFalse(mutant_tripped(cut, "STATE_FILE", value))
        self.assertFalse(mutant_tripped((1,) + through[1:], "STATE_FILE",
                                        value))
        self.assertTrue(mutant_tripped(through, "STATE_FILE", value))

    def test_each_mutant_drops_only_its_own_character(self):
        # Each member is written as two characters in the pattern; a mutant
        # is the pattern two characters shorter, every other member kept.
        members = {"$": "\\$", "`": "\\`", '"': '\\"', "\\": "\\\\",
                   "\n": "\\n", "\r": "\\r"}
        for label, char in BLOCKED:
            with self.subTest(label):
                self.assertEqual(len(WITHOUT[char]), len(BRACKET) - 2)
                self.assertEqual(BRACKET.replace(members[char], "", 1),
                                 WITHOUT[char])


if __name__ == "__main__":
    unittest.main()
