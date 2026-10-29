"""Tests for diff_ranges.py — exact changed-line ranges from a unified diff.

Contract under test: `ranges_from_diff(text)` walks each hunk body by its `+`
and `-` markers (never by the header's display-context counts) and returns
`{path: [[start, end], ...]}` in new-side line numbers, sorted and merged per
file:

- an added line counts as changed;
- a pure deletion counts the two lines either side of the deletion point,
  `[max(T, 1), T + 1]` where T is the last new-side line before it;
- a replace block that removes more lines than it adds also covers the one
  new-side line just after it (net deletion);
- the same change gives the same ranges under `git diff`, `-U0` and `-U10`.

Structurally inconsistent input (a commit series, a combined `@@@` hunk, a
body shorter or longer than its header, an unexpected body line) raises
`RangeError` with a fixed reason; the CLI turns that into exit 2 with the
reason on stderr and nothing on stdout.

Every diff here is produced by real git in a throwaway repo built with
gitfixture (null global and system git config). Tests reach the module
through `self.dr` so the mutant tests can rerun a named test against a
mutated copy of the module.

Route coverage (the TestRoute* classes and TestProseRangeFence) runs each
review route's range source through the same builder: default, GSD,
incremental and range on temp repos, the PR route on a checked-in capture,
and `--all` as an asserted unsupported-fixture record (it has no diff).

PR fixture provenance (`fixtures/pr-cumulative.diff`): captured from `gh`
(not a fallback) on 2026-10-29 with `gh pr diff 5 --color never`, PR #5 of
this repo ("v2.14 Phase 59: stale decisions and lost deferrals"; base
f2b6a3674d0d0dc62ab6dca3a00816c070943884, head
98f63aa7834af6a04c5a38d925d8b1ca457111bc, squash-merged as the single-parent
commit 6dfac6436427cc385fe1937f73ed841fef6c8ffb). Cut rule: four whole file
sections taken verbatim at `diff --git` boundaries (50-fix-loop.md,
90-finalize.md, batch_card.py, carry_state.py; capture lines 4897-5182).
At capture time the same four paths read locally with `git diff --no-color
--no-ext-diff --src-prefix=a/ --dst-prefix=b/ f2b6a36 98f63aa` (f2b6a36 is
the merge base) gave the identical ranges. No test fetches anything.

Run with bare `pytest` from plugins/vibe-check/scripts.
"""

import ast
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

import diff_ranges  # noqa: E402  (module under test)
import gitfixture  # noqa: E402  (shared temp-repo helper)
import replay  # noqa: E402  (pinned header-based reader)
import score  # noqa: E402  (the real scorer, for the --all record)
import test_decision_continuity as tdc  # noqa: E402  (real-chain helpers)

DIFF_RANGES_PY = os.path.join(SCRIPTS_DIR, "diff_ranges.py")
PLUGIN_ROOT = os.path.dirname(SCRIPTS_DIR)
COLLECT_MD = os.path.join(PLUGIN_ROOT, "phases", "review",
                          "30-collect-score.md")
STATE_ALL_MD = os.path.join(PLUGIN_ROOT, "phases", "review",
                            "05-state-all.md")
PR_FIXTURE = os.path.join(SCRIPTS_DIR, "fixtures", "pr-cumulative.diff")

# The flags every range-building git call in the review prose passes.
PROSE_FLAGS = ("--no-color", "--no-ext-diff", "--src-prefix=a/",
               "--dst-prefix=b/")

BASE = [str(n) for n in range(1, 31)]


def _is_mbox_line(line):
    """A real mbox separator: `From`, a 40-hex sha, then the date text."""
    parts = line.split(" ")
    return (len(parts) > 2 and parts[0] == "From" and len(parts[1]) == 40
            and all(c in "0123456789abcdef" for c in parts[1]))


class _Repo(unittest.TestCase):
    """Base: a temp repo with `f.txt` = lines "1".."30" committed."""

    dr = diff_ranges

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = gitfixture.make_repo(os.path.realpath(self._tmp.name))
        self.commit_lines(BASE)

    # ------------------------------------------------------------ helpers

    def git(self, *args, check=True):
        return gitfixture.git(self.repo, *args, check=check)

    def write_lines(self, lines, rel="f.txt", newline=True):
        text = "\n".join(lines) + ("\n" if newline else "")
        gitfixture.write(self.repo, rel, text)

    def commit_lines(self, lines, rel="f.txt", newline=True):
        self.write_lines(lines, rel, newline)
        self.git("add", "--", rel)
        self.git("commit", "-q", "-m", "commit %s" % rel)

    def diff(self, *args):
        """`git diff <prose flags> <args> HEAD` (working tree vs HEAD)."""
        return self.git("diff", *PROSE_FLAGS, *args, "HEAD").stdout

    def three_contexts(self):
        return (self.diff(), self.diff("-U0"), self.diff("-U10"))

    def ranges(self, text):
        return self.dr.ranges_from_diff(text)

    def assert_all_contexts(self, want):
        """Ranges are identical under default, -U0 and -U10 and equal `want`."""
        for label, text in zip(("default", "-U0", "-U10"),
                               self.three_contexts()):
            with self.subTest(context=label):
                self.assertEqual(self.ranges(text), want)


# --------------------------------------------------------------------------- #
# The shape table: real git, three display contexts, one expected answer
# --------------------------------------------------------------------------- #
class TestShapesRealGit(_Repo):

    def test_delete_one_line(self):
        L = list(BASE)
        del L[8]  # line 9
        self.write_lines(L)
        self.assert_all_contexts({"f.txt": [[8, 9]]})

    def test_replace_one_line(self):
        L = list(BASE)
        L[9] = "ten"
        self.write_lines(L)
        self.assert_all_contexts({"f.txt": [[10, 10]]})

    def test_insert_one_line(self):
        L = list(BASE)
        L.insert(15, "new")  # after line 15
        self.write_lines(L)
        self.assert_all_contexts({"f.txt": [[16, 16]]})

    def test_delete_three_lines(self):
        L = list(BASE)
        del L[9:12]  # lines 10-12
        self.write_lines(L)
        self.assert_all_contexts({"f.txt": [[9, 10]]})

    def test_net_deletion_replace_extends_one_line(self):
        L = list(BASE)
        L[9:12] = ["one"]  # lines 10-12 become one line
        self.write_lines(L)
        self.assert_all_contexts({"f.txt": [[10, 11]]})

    def test_two_edits_in_one_default_hunk_stay_separate(self):
        L = list(BASE)
        L[4] = "five"
        L[9] = "ten"
        self.write_lines(L)
        default = self.diff()
        # The fixture holds what it claims: git merges both edits into ONE
        # default-context hunk, yet the ranges keep them apart.
        self.assertIn("@@ -2,12 +2,12 @@", default)
        self.assertEqual(default.count("\n@@ "), 1)
        self.assert_all_contexts({"f.txt": [[5, 5], [10, 10]]})

    def test_delete_first_line(self):
        L = list(BASE)
        del L[0]
        self.write_lines(L)
        self.assert_all_contexts({"f.txt": [[1, 1]]})

    def test_delete_last_two_lines(self):
        L = list(BASE)
        del L[28:30]  # lines 29-30; the cursor lands past EOF, harmless
        self.write_lines(L)
        self.assert_all_contexts({"f.txt": [[28, 29]]})

    def test_relocated_block(self):
        L = list(BASE)
        moved = L[2:4]  # lines 3-4
        del L[2:4]
        L[18:18] = moved  # re-inserted after old line 20
        self.write_lines(L)
        self.assert_all_contexts({"f.txt": [[2, 3], [19, 20]]})

    def test_adjacent_blocks_merge(self):
        L = list(BASE)
        del L[10]  # line 11
        del L[8]   # line 9; the two deletion pairs [8, 9] and [9, 10] touch
        self.write_lines(L)
        self.assert_all_contexts({"f.txt": [[8, 10]]})

    def test_new_file(self):
        self.write_lines(["a", "b", "c"], rel="g.txt")
        self.git("add", "--", "g.txt")
        self.assert_all_contexts({"g.txt": [[1, 3]]})

    def test_deleted_file_has_no_key(self):
        os.remove(os.path.join(self.repo, "f.txt"))
        self.assertIn("+++ /dev/null", self.diff())
        self.assert_all_contexts({})

    def test_two_files_both_keys_sorted(self):
        L = list(BASE)
        L[2] = "three"
        self.write_lines(L)
        self.write_lines(["z1", "z2"], rel="z.txt")
        self.git("add", "--", "z.txt")
        want = {"f.txt": [[3, 3]], "z.txt": [[1, 2]]}
        self.assert_all_contexts(want)
        # Feed the files in reverse order: the keys still come out sorted.
        text = self.diff()
        cut = text.index("diff --git a/z.txt")
        reordered = text[cut:] + text[:cut]
        got = self.ranges(reordered)
        self.assertEqual(got, want)
        self.assertEqual(list(got), ["f.txt", "z.txt"])


# --------------------------------------------------------------------------- #
# Diff-text hazards
# --------------------------------------------------------------------------- #
class TestHazards(_Repo):

    def test_content_lines_that_look_like_file_headers(self):
        L = list(BASE)
        L[4] = "-- x"
        self.commit_lines(L)
        L[4] = "++ y"
        L[24] = "twenty-five"
        self.write_lines(L)
        default = self.diff()
        # Inside the hunk body the edit prints as `--- x` / `+++ y`.
        self.assertIn("\n--- x\n", default)
        self.assertIn("\n+++ y\n", default)
        for label, text in zip(("default", "-U0", "-U10"),
                               self.three_contexts()):
            with self.subTest(context=label):
                got = self.ranges(text)
                self.assertNotIn("y", got)
                self.assertEqual(got, {"f.txt": [[5, 5], [25, 25]]})

    def test_path_with_space_trailing_tab(self):
        self.commit_lines(BASE, rel="a b.txt")
        L = list(BASE)
        L[6] = "seven"
        self.write_lines(L, rel="a b.txt")
        self.assertIn("+++ b/a b.txt\t\n", self.diff())
        self.assert_all_contexts({"a b.txt": [[7, 7]]})

    def test_no_newline_marker_consumes_no_budget(self):
        self.commit_lines(BASE, newline=False)
        L = list(BASE)
        L[29] = "thirty"
        self.write_lines(L, newline=False)
        self.assertIn("\\ No newline at end of file", self.diff())
        self.assert_all_contexts({"f.txt": [[30, 30]]})

    def test_hostile_repo_config_does_not_change_ranges(self):
        L = list(BASE)
        L[11] = "twelve"
        self.write_lines(L)
        clean = [self.ranges(t) for t in self.three_contexts()]
        self.git("config", "color.ui", "always")
        self.git("config", "diff.mnemonicPrefix", "true")
        self.git("config", "diff.noprefix", "true")
        self.git("config", "diff.external", "false")
        # The hostile config really changes git's own output...
        raw = self.git("diff", "--no-ext-diff", "HEAD").stdout
        self.assertIn("\x1b[", raw)
        self.assertNotIn("+++ b/f.txt", raw)
        # ...but the prose flags restore the same ranges and keys.
        hostile = [self.ranges(t) for t in self.three_contexts()]
        self.assertEqual(hostile, clean)
        self.assertEqual(clean[0], {"f.txt": [[12, 12]]})

    def test_form_feed_and_line_separator_do_not_desync(self):
        L = list(BASE)
        L[6] = "a\x0cb"
        L[7] = "c d"
        self.commit_lines(L)
        L[9] = "ten"
        self.write_lines(L)
        self.assertIn("\x0c", self.diff())
        self.assertIn(" ", self.diff())
        self.assert_all_contexts({"f.txt": [[10, 10]]})

    def test_quoted_path_is_skipped(self):
        # git C-quotes a non-ASCII name; such a path can never carry a
        # finding, so its hunks are skipped instead of keyed by quoted text.
        self.commit_lines(BASE, rel="é.txt")
        L = list(BASE)
        L[3] = "four"
        self.write_lines(L, rel="é.txt")
        self.assertIn('+++ "b/', self.diff())
        self.assert_all_contexts({})


# --------------------------------------------------------------------------- #
# Refusals: fixed reasons, never input text
# --------------------------------------------------------------------------- #
class TestRefusals(_Repo):

    def _refusal(self, text):
        with self.assertRaises(self.dr.RangeError) as cm:
            self.ranges(text)
        reason = str(cm.exception)
        self.assertIn(reason, self.dr.REASONS)
        self.assertNotIn("f.txt", reason)
        return reason

    def _series(self):
        root = self.git("rev-parse", "HEAD").stdout.strip()
        for n in (3, 20):
            L = list(BASE)
            L[n] = "edit%d" % n
            self.commit_lines(L)
        text = self.git("format-patch", "--stdout", "%s..HEAD" % root).stdout
        heads = [ln for ln in text.split("\n") if _is_mbox_line(ln)]
        self.assertEqual(len(heads), 2)  # a real two-commit series
        return text

    def test_refuses_commit_series(self):
        self.assertEqual(self._refusal(self._series()), self.dr.REASON_MBOX)

    def test_refuses_combined_diff(self):
        self.git("checkout", "-q", "-b", "side")
        L = list(BASE)
        L[4] = "side"
        self.commit_lines(L)
        self.git("checkout", "-q", "main")
        L[4] = "main"
        self.commit_lines(L)
        self.git("merge", "-q", "side", check=False)  # conflicts on line 5
        text = self.git("diff", *PROSE_FLAGS).stdout
        self.assertIn("@@@ ", text)
        self.assertEqual(self._refusal(text), self.dr.REASON_COMBINED)

    def test_refuses_short_body(self):
        L = list(BASE)
        L[9] = "ten"
        self.write_lines(L)
        text = self.diff().rstrip("\n")
        cut = text[:text.rindex("\n")]  # drop the last body line
        self.assertEqual(self._refusal(cut + "\n"),
                         self.dr.REASON_SHORT_BODY)

    def test_refuses_long_body(self):
        L = list(BASE)
        L[9] = "ten"
        self.write_lines(L)
        text = self.diff("-U0")
        self.assertTrue(text.endswith("+ten\n"))
        self.assertEqual(self._refusal(text + "+extra\n"),
                         self.dr.REASON_LONG_BODY)

    def test_refuses_extra_deleted_line_inside_budget(self):
        L = list(BASE)
        L[9] = "ten"
        self.write_lines(L)
        text = self.diff("-U0")
        self.assertIn("\n-10\n+ten\n", text)
        bad = text.replace("\n-10\n", "\n-10\n-extra\n", 1)
        self.assertEqual(self._refusal(bad), self.dr.REASON_LONG_BODY)

    def test_refuses_long_body_after_no_newline_marker(self):
        self.commit_lines(BASE, newline=False)
        L = list(BASE)
        L[29] = "thirty"
        self.write_lines(L, newline=False)
        text = self.diff("-U0")
        self.assertTrue(text.endswith("\\ No newline at end of file\n"))
        self.assertEqual(self._refusal(text + "+extra\n"),
                         self.dr.REASON_LONG_BODY)

    def test_refuses_unexpected_body_line(self):
        L = list(BASE)
        L[9] = "ten"
        self.write_lines(L)
        text = self.diff()
        self.assertIn("\n 8\n", text)
        bad = text.replace("\n 8\n", "\nx8\n", 1)
        self.assertEqual(self._refusal(bad), self.dr.REASON_BAD_BODY_LINE)

    def test_reasons_are_fixed_text(self):
        self.assertEqual(
            self.dr.REASONS,
            (self.dr.REASON_MBOX, self.dr.REASON_COMBINED,
             self.dr.REASON_SHORT_BODY, self.dr.REASON_LONG_BODY,
             self.dr.REASON_BAD_BODY_LINE))
        self.assertTrue(issubclass(self.dr.RangeError, ValueError))

    def test_empty_diff_is_empty_result(self):
        self.assertEqual(self.diff(), "")
        self.assertEqual(self.ranges(""), {})
        self.assertEqual(self.ranges("\n"), {})


# --------------------------------------------------------------------------- #
# CLI shim
# --------------------------------------------------------------------------- #
class TestCli(_Repo):

    def cli(self, data, *argv):
        return subprocess.run(
            [sys.executable, DIFF_RANGES_PY, *argv], input=data,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
            env=gitfixture.helper_env())

    def _two_file_diff(self):
        L = list(BASE)
        L[2] = "three"
        self.write_lines(L)
        self.write_lines(["z1"], rel="z.txt")
        self.git("add", "--", "z.txt")
        text = self.diff()
        cut = text.index("diff --git a/z.txt")
        return text[cut:] + text[:cut]  # z.txt first on input

    def test_valid_diff_prints_sorted_json(self):
        text = self._two_file_diff()
        proc = self.cli(text.encode("utf-8"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        want = diff_ranges.ranges_from_diff(text)
        self.assertEqual(json.loads(proc.stdout), want)
        self.assertEqual(proc.stdout.decode("utf-8"),
                         json.dumps(want, sort_keys=True) + "\n")
        self.assertTrue(proc.stdout.startswith(b'{"f.txt"'))

    def test_empty_stdin_prints_empty_object(self):
        proc = self.cli(b"")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, b"{}\n")
        self.assertEqual(proc.stderr, b"")

    def test_series_exits_two_with_reason_only(self):
        root = self.git("rev-parse", "HEAD").stdout.strip()
        L = list(BASE)
        L[3] = "four"
        self.commit_lines(L)
        series = self.git("format-patch", "--stdout",
                          "%s..HEAD" % root).stdout
        proc = self.cli(series.encode("utf-8"))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertEqual(proc.stderr.decode("utf-8"),
                         diff_ranges.REASON_MBOX + "\n")

    def test_any_argv_exits_two(self):
        for argv in (["--help"], ["x"]):
            with self.subTest(argv=argv):
                proc = self.cli(b"", *argv)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")

    def test_undecodable_bytes_in_content(self):
        gitfixture.write(self.repo, "f.txt",
                         b"\n".join(x.encode() for x in BASE[:5])
                         + b"\n\xff\xfe\n"
                         + b"\n".join(x.encode() for x in BASE[6:]) + b"\n")
        raw = subprocess.run(
            ["git", "diff", *PROSE_FLAGS, "--text", "HEAD"], cwd=self.repo,
            stdout=subprocess.PIPE, env=gitfixture.helper_env(),
            timeout=60, check=True).stdout
        self.assertIn(b"\xff", raw)
        proc = self.cli(raw)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), {"f.txt": [[6, 6]]})


# --------------------------------------------------------------------------- #
# Import lock: a pure parser — no git, file or shell I/O
# --------------------------------------------------------------------------- #
class TestImportLock(unittest.TestCase):

    def _source(self):
        with open(DIFF_RANGES_PY, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_import_set_is_exact(self):
        imported = set()
        for node in ast.walk(ast.parse(self._source())):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        self.assertEqual(imported, {"json", "re", "sys"})

    def test_no_forbidden_names(self):
        banned = {"os", "subprocess", "open", "eval", "exec", "compile",
                  "__import__", "shutil", "pathlib"}
        for node in ast.walk(ast.parse(self._source())):
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id, banned)

    def test_no_forbidden_text(self):
        src = self._source()
        self.assertNotIn("subprocess", src)
        self.assertNotIn("open(", src)
        self.assertNotIn("splitlines", src)


# --------------------------------------------------------------------------- #
# replay.hunk_ranges stays header-based (pinned)
# --------------------------------------------------------------------------- #
DELETE_LINE_9_DEFAULT = """\
diff --git a/f.txt b/f.txt
index 0000000..1111111 100644
--- a/f.txt
+++ b/f.txt
@@ -6,7 +6,6 @@
 6
 7
 8
-9
 10
 11
 12
"""


class TestReplayPin(unittest.TestCase):
    """replay.hunk_ranges rebuilds the envelopes of recorded runs, whose
    ranges were read from hunk headers with git's context lines included.
    The replay gate compares against those recordings, so this reader must
    keep returning the header-based (context-included) range and must not be
    switched to the exact builder."""

    def test_replay_keeps_context_in_ranges(self):
        self.assertEqual(replay.hunk_ranges(DELETE_LINE_9_DEFAULT),
                         {"f.txt": [[6, 11]]})

    def test_builder_differs_on_the_same_text(self):
        self.assertEqual(diff_ranges.ranges_from_diff(DELETE_LINE_9_DEFAULT),
                         {"f.txt": [[8, 9]]})


# --------------------------------------------------------------------------- #
# Mutants: every guard is load-bearing
# --------------------------------------------------------------------------- #
with open(DIFF_RANGES_PY, "r", encoding="utf-8") as _fh:
    SOURCE = _fh.read()


class TestMutants(unittest.TestCase):
    """Each mutant swaps one exact piece of diff_ranges.py source (asserted
    present exactly once, so a refactor cannot leave a mutant that changes
    nothing), executes the swapped copy as a module, and reruns a named test
    against it through `dr`. The named test must pass on the real module and
    fail on the mutant."""

    def mutant(self, old, new):
        self.assertEqual(SOURCE.count(old), 1, "mutant anchor not unique: %r"
                         % old)
        mod = types.ModuleType("diff_ranges_mutant")
        mod.__file__ = DIFF_RANGES_PY
        code = compile(SOURCE.replace(old, new), "<diff_ranges mutant>",
                       "exec")
        exec(code, mod.__dict__)  # our own source, one token swapped
        return mod

    @staticmethod
    def _passes(cls, name, mod):
        case = cls(name)
        case.dr = mod
        result = unittest.TestResult()
        case.run(result)
        return result.wasSuccessful()

    def assert_trips(self, old, new, cls, name):
        mod = self.mutant(old, new)
        self.assertTrue(self._passes(cls, name, diff_ranges),
                        "%s.%s fails on the real module" % (cls.__name__, name))
        self.assertFalse(self._passes(cls, name, mod),
                         "mutant survives %s.%s" % (cls.__name__, name))
        return mod

    # M1: read the header counts instead of walking the markers.
    def test_m1_header_count_reader(self):
        mod = self.assert_trips(
            "    _close_block(out, path, block)\n    return i\n",
            "    out.setdefault(path, []).append(\n"
            "        [new_start, new_start + new_count - 1])\n    return i\n",
            TestShapesRealGit, "test_delete_one_line")
        self.assertEqual(mod.ranges_from_diff(DELETE_LINE_9_DEFAULT),
                         {"f.txt": [[6, 11]]})

    # M2: drop the net-deletion extension (D-02).
    def test_m2_net_deletion_extension(self):
        mod = self.assert_trips(
            "            if deleted > added:\n",
            "            if False:\n",
            TestShapesRealGit, "test_net_deletion_replace_extends_one_line")
        text = ("diff --git a/f.txt b/f.txt\n--- a/f.txt\n+++ b/f.txt\n"
                "@@ -10,3 +10 @@\n-10\n-11\n-12\n+one\n")
        self.assertEqual(mod.ranges_from_diff(text), {"f.txt": [[10, 10]]})
        self.assertEqual(diff_ranges.ranges_from_diff(text),
                         {"f.txt": [[10, 11]]})

    # M3: stop the body at a `+++ ` line instead of consuming the budget.
    def test_m3_budget_consumption(self):
        self.assert_trips(
            "        body = lines[i]\n",
            "        body = lines[i]\n"
            "        if body.startswith(\"+++ \"):\n"
            "            break\n",
            TestHazards, "test_content_lines_that_look_like_file_headers")

    # M4: drop the commit-series refusal.
    def test_m4_mbox_refusal(self):
        self.assert_trips(
            "        if _is_mbox(line):\n",
            "        if False:\n",
            TestRefusals, "test_refuses_commit_series")

    # M5: universal line splitting instead of "\n" only.
    def test_m5_split_on_newline_only(self):
        self.assert_trips(
            'lines = text.split("\\n")',
            "lines = (text.splitlines() or [\"\"])",
            TestHazards, "test_form_feed_and_line_separator_do_not_desync")

    # M6: a pure deletion covers only one line.
    def test_m6_pure_deletion_pair(self):
        self.assert_trips(
            "[max(start - 1, 1), start]",
            "[start, start]",
            TestShapesRealGit, "test_delete_one_line")

    # M7: ignore that an empty new side is numbered by the line before it.
    def test_m7_zero_count_cursor(self):
        self.assert_trips(
            "cursor = new_start + 1 if new_count == 0 else new_start",
            "cursor = new_start",
            TestShapesRealGit, "test_delete_one_line")

    # M8: drop the combined-diff refusal.
    def test_m8_combined_refusal(self):
        self.assert_trips(
            '        if line.startswith("@@@"):\n',
            "        if False:\n",
            TestRefusals, "test_refuses_combined_diff")

    # M9: a short body ends quietly instead of refusing.
    def test_m9_short_body_refusal(self):
        self.assert_trips(
            "            raise RangeError(REASON_SHORT_BODY)\n",
            "            break\n",
            TestRefusals, "test_refuses_short_body")

    # M10: no overflow check inside the hunk.
    def test_m10_budget_overflow_refusal(self):
        self.assert_trips(
            "        if old_left < 0 or new_left < 0:\n",
            "        if False:\n",
            TestRefusals, "test_refuses_extra_deleted_line_inside_budget")

    # M11: no check for body lines left over after the hunk.
    def test_m11_leftover_body_refusal(self):
        self.assert_trips(
            "        if after_hunk and _is_stray_body_line(line):\n",
            "        if False:\n",
            TestRefusals, "test_refuses_long_body")

    # M12: an unexpected body line is skipped instead of refused.
    def test_m12_bad_body_line_refusal(self):
        self.assert_trips(
            "        else:\n            raise RangeError(REASON_BAD_BODY_LINE)\n",
            "        else:\n            continue\n",
            TestRefusals, "test_refuses_unexpected_body_line")

    # M13: a `\` marker inside the body is not skipped.
    def test_m13_no_newline_marker_in_body(self):
        self.assert_trips(
            '        if tag == "\\\\":\n            continue\n',
            "",
            TestHazards, "test_no_newline_marker_consumes_no_budget")

    # M14: a `\` marker after the hunk resets the leftover-line check.
    def test_m14_no_newline_marker_after_hunk(self):
        self.assert_trips(
            '        if line.startswith("\\\\"):\n            continue\n',
            "",
            TestRefusals, "test_refuses_long_body_after_no_newline_marker")

    # M15: keep git's trailing tab on a path with a space.
    def test_m15_trailing_tab(self):
        self.assert_trips(
            '    if path.endswith("\\t"):\n',
            "    if False:\n",
            TestHazards, "test_path_with_space_trailing_tab")

    # M16: key a C-quoted path by its quoted text.
    def test_m16_quoted_path(self):
        self.assert_trips(
            " or path.startswith('\"')",
            "",
            TestHazards, "test_quoted_path_is_skipped")

    # M17: treat `/dev/null` as a file.
    def test_m17_dev_null(self):
        self.assert_trips(
            'path == "/dev/null" or ',
            "",
            TestShapesRealGit, "test_deleted_file_has_no_key")

    # M18: never merge touching ranges.
    def test_m18_merge(self):
        self.assert_trips(
            "        if merged and start <= merged[-1][1] + 1:\n",
            "        if False:\n",
            TestShapesRealGit, "test_adjacent_blocks_merge")

    # M19: keys in input order instead of sorted.
    def test_m19_sorted_keys(self):
        self.assert_trips(
            "for p in sorted(out)}",
            "for p in out}",
            TestShapesRealGit, "test_two_files_both_keys_sorted")



# --------------------------------------------------------------------------- #
# Route coverage: every review route's range source through the builder
# --------------------------------------------------------------------------- #
F = tdc.F


def _git_diff(repo, *args):
    """`git diff <prose flags> <args>` in a RealDiffRepo."""
    return repo.git("diff", *PROSE_FLAGS, *args).stdout


class TestRouteDefault(tdc._RealChain):
    """Default route: the range source is `git diff HEAD` alone, in
    working-tree line numbers. A decision at 40; an edit at line `at` is
    staged with a real `git add`, then ten lines are inserted at the top
    without staging, so on disk the decided line is 50 and the staged edit
    is at `at + 10`."""

    def _staged(self, at):
        L0, s1, hA = self._decide40()
        repo = tdc.RealDiffRepo.make(self, L0)
        repo.write(tdc._edited(L0, at))
        repo.git("add", F)
        L2 = tdc.TOP_TEN + tdc._edited(L0, at)
        repo.write(L2)
        return repo, L2, s1, hA

    def test_head_alone_covers_staged_and_unstaged_and_keeps(self):
        repo, L2, s1, hA = self._staged(48)
        ranges = diff_ranges.ranges_from_diff(_git_diff(repo, "HEAD"))
        # Both the unstaged insertion (1-10) and the staged edit (now 58).
        self.assertEqual(ranges, {F: [[1, 10], [58, 58]]})
        self.assertEqual(
            ranges, diff_ranges.ranges_from_diff(_git_diff(repo, "-U0",
                                                           "HEAD")))
        self.assert_keeps(self._pass2(s1, L2, ranges), hA, 50)

    def test_appending_the_staged_section_wrongly_reopens(self):
        """Documenting assertion: the old HEAD + `--staged` assembly adds
        the index-coordinate line 48, which reopens the decision."""
        repo, L2, s1, hA = self._staged(48)
        staged = _git_diff(repo, "--staged")
        self.assertEqual(diff_ranges.ranges_from_diff(staged), {F: [[48, 48]]})
        concat = diff_ranges.ranges_from_diff(_git_diff(repo, "HEAD") + staged)
        self.assertEqual(concat, {F: [[1, 10], [48, 48], [58, 58]]})
        self.assert_reopens(self._pass2(s1, L2, concat), hA, 50)

    def test_boundary_staged_edit_at_45_reopens(self):
        repo, L2, s1, hA = self._staged(45)
        ranges = diff_ranges.ranges_from_diff(_git_diff(repo, "HEAD"))
        self.assertEqual(ranges, {F: [[1, 10], [55, 55]]})
        self.assert_reopens(self._pass2(s1, L2, ranges), hA, 50)

    def test_findings_and_ranges_share_working_tree_lines(self):
        """The staged-section probe: line 48 is the staged edit only in the
        index's numbering; on disk it is unchanged code (old line 38), so it
        is correctly outside the ranges, and the staged edit's working-tree
        line 58 is inside them."""
        repo, L2, _, _ = self._staged(48)
        ranges = diff_ranges.ranges_from_diff(_git_diff(repo, "HEAD"))
        self.assertEqual(L2[47], tdc.base_file()[37])
        self.assertTrue(tdc.scored_in_diff(L2, 58, ranges))
        self.assertFalse(tdc.scored_in_diff(L2, 48, ranges))


class _CommittedThenUncommitted(tdc._RealChain):
    """A decision at 40; a COMMITTED edit at line 35 after `base`, then an
    uncommitted ten-line insertion at the top: on disk the decided line is
    50 and the committed edit is at 45 (inside 45..55)."""

    def _repo(self):
        L0, s1, hA = self._decide40()
        repo = tdc.RealDiffRepo.make(self, L0)
        repo.write(tdc._edited(L0, 35))
        repo.commit("edit line 35")
        L2 = tdc.TOP_TEN + tdc._edited(L0, 35)
        repo.write(L2)
        return repo, L2, s1, hA

    def _check(self, base):
        repo, L2, s1, hA = self._repo()
        sha = base(repo)
        ranges = diff_ranges.ranges_from_diff(_git_diff(repo, sha))
        # The committed edit lands at its working-tree line, 45.
        self.assertEqual(ranges, {F: [[1, 10], [45, 45]]})
        self.assert_reopens(self._pass2(s1, L2, ranges), hA, 50)
        with self.subTest("old three-part assembly: silent keep"):
            concat = (_git_diff(repo, "%s..HEAD" % sha)
                      + _git_diff(repo, "--staged") + _git_diff(repo))
            old = diff_ranges.ranges_from_diff(concat)
            self.assertEqual(old, {F: [[1, 10], [35, 35]]})
            self.assert_keeps(self._pass2(s1, L2, old), hA, 50)


class TestRouteGSD(_CommittedThenUncommitted):
    """GSD route, pass 1: `git diff $PHASE_START` (commit vs working tree);
    `git diff HEAD` when `$PHASE_START` is empty."""

    def test_phase_start_single_diff_uses_working_tree_lines(self):
        self._check(lambda repo: repo.base)

    def test_empty_phase_start_falls_back_to_head(self):
        repo, L2, s1, hA = self._repo()
        ranges = diff_ranges.ranges_from_diff(_git_diff(repo, "HEAD"))
        self.assertEqual(ranges, {F: [[1, 10]]})


class TestRouteIncremental(_CommittedThenUncommitted):
    """Any stateful route, pass >= 2: `git diff $LAST_REVIEWED_SHA`."""

    def test_last_reviewed_sha_single_diff_uses_working_tree_lines(self):
        self._check(lambda repo: repo.base)

    def test_last_reviewed_sha_after_more_commits(self):
        L0, s1, hA = self._decide40()
        repo = tdc.RealDiffRepo.make(self, L0)
        repo.write(tdc._edited(L0, 20))
        repo.commit("reviewed on pass 1")
        last = repo.git("rev-parse", "HEAD").stdout.strip()
        L1 = tdc._edited(tdc._edited(L0, 20), 35)
        repo.write(L1)
        repo.commit("edit line 35 after the review")
        L2 = tdc.TOP_TEN + L1
        repo.write(L2)
        ranges = diff_ranges.ranges_from_diff(_git_diff(repo, last))
        self.assertEqual(ranges, {F: [[1, 10], [45, 45]]})


class TestRouteRange(_Repo):
    """Range route: `git diff <range>` between two commits."""

    def test_range_between_commits_matches_u0(self):
        a = self.git("rev-parse", "HEAD").stdout.strip()
        L = list(BASE)
        L[4] = "five"
        del L[19]  # line 20
        L.insert(25, "new")  # new line 26 (after the deletion)
        self.commit_lines(L)
        b = self.git("rev-parse", "HEAD").stdout.strip()
        rng = "%s..%s" % (a, b)
        default = self.git("diff", *PROSE_FLAGS, rng).stdout
        exact = self.git("diff", *PROSE_FLAGS, "-U0", rng).stdout
        want = {"f.txt": [[5, 5], [19, 20], [26, 26]]}
        self.assertEqual(self.ranges(default), want)
        self.assertEqual(self.ranges(exact), want)


# Ranges of fixtures/pr-cumulative.diff, pinned when it was captured.
PR_FIXTURE_RANGES = {
    "plugins/vibe-check/phases/review/50-fix-loop.md": [[62, 62]],
    "plugins/vibe-check/phases/shared/90-finalize.md": [[110, 111],
                                                        [114, 114]],
    "plugins/vibe-check/scripts/batch_card.py": [
        [237, 245], [271, 272], [530, 582], [588, 590], [620, 620],
        [633, 633]],
    "plugins/vibe-check/scripts/carry_state.py": [
        [308, 400], [402, 406], [445, 445], [840, 856]],
}


class TestRoutePR(_Repo):
    """PR route: the cumulative `gh pr diff <ref> --color never`, proven on a
    checked-in capture; the `--patch` commit series is refused."""

    def _fixture(self):
        with open(PR_FIXTURE, encoding="utf-8") as fh:
            return fh.read()

    def test_fixture_is_a_single_cumulative_diff(self):
        text = self._fixture()
        self.assertTrue(text.strip())
        lines = text.split("\n")
        self.assertFalse([ln for ln in lines if _is_mbox_line(ln)])
        self.assertGreaterEqual(
            sum(1 for ln in lines if ln.startswith("diff --git ")), 2)
        self.assertLessEqual(len(lines), 401)

    def test_fixture_ranges_are_pinned(self):
        self.assertEqual(self.ranges(self._fixture()), PR_FIXTURE_RANGES)

    def test_every_key_is_a_new_side_path(self):
        text = self._fixture()
        paths = {ln[len("+++ b/"):] for ln in text.split("\n")
                 if ln.startswith("+++ b/")}
        self.assertEqual(set(self.ranges(text)), paths)

    def _two_commit_pr(self):
        """Commit A edits line 10; commit B inserts five lines at the top."""
        base = self.git("rev-parse", "HEAD").stdout.strip()
        LA = list(BASE)
        LA[9] = "ten"
        self.commit_lines(LA)
        self.commit_lines(["top%d" % i for i in range(5)] + LA)
        return base

    def test_cumulative_diff_gives_head_lines(self):
        base = self._two_commit_pr()
        text = self.git("diff", *PROSE_FLAGS, base, "HEAD").stdout
        self.assertEqual(self.ranges(text), {"f.txt": [[1, 5], [15, 15]]})

    def test_commit_series_is_refused(self):
        """Regression guard: a `--patch`-style series (format-patch mbox)
        fails closed instead of yielding per-commit line numbers."""
        base = self._two_commit_pr()
        series = self.git("format-patch", "--stdout", *PROSE_FLAGS,
                          "%s..HEAD" % base).stdout
        self.assertEqual(
            sum(1 for ln in series.split("\n") if _is_mbox_line(ln)), 2)
        with self.assertRaises(self.dr.RangeError) as cm:
            self.ranges(series)
        self.assertEqual(str(cm.exception), self.dr.REASON_MBOX)


class TestRouteAll(unittest.TestCase):
    """Unsupported fixture: --all has no diff on any pass; recorded per D-06,
    not a gap. 05-state-all.md (ii) forces a fresh pass 1 with no
    carry-forward, the empty diff gives no ranges, and the scorer keeps a
    reviewed-set finding without any in-diff term."""

    def test_state_all_still_forces_a_fresh_pass(self):
        with open(STATE_ALL_MD, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("$PASS_NUMBER = 1", text)
        self.assertIn("$CARRYFORWARD = []", text)

    def test_no_diff_gives_no_ranges(self):
        self.assertEqual(diff_ranges.ranges_from_diff(""), {})

    def test_reviewed_set_finding_kept_without_ranges(self):
        lines = tdc.base_file()
        finding = tdc.fresh("bugs", 40, lines, tdc.TITLE_A, conf=85,
                            severity="critical")
        envelope = {"command": "deep-review", "all_mode": True,
                    "pass_number": 1, "reviewed_union": [F],
                    "file_line_totals": {F: len(lines)},
                    "changed_line_ranges": {}, "carryforward": [],
                    "findings": [finding]}
        result = score.run(envelope)
        self.assertEqual([f["id"] for f in result["findings"]],
                         [finding["id"]])
        with self.subTest("outside the reviewed set it is dropped"):
            envelope["reviewed_union"] = ["src/other.py"]
            self.assertEqual(score.run(envelope)["findings"], [])


HALT_SENTENCE = ("Review halted — the changed lines could not be read from "
                 "the diff; nothing was scored.")


def _collect_text():
    with open(COLLECT_MD, encoding="utf-8") as fh:
        return fh.read()


def _range_bullet(text):
    start = text.index("**changed-line ranges**")
    end = text.find("\n   - **", start)
    return text[start:] if end < 0 else text[start:end]


def prose_range_fence(text):
    """The bash fence inside the `changed-line ranges` bullet of
    30-collect-score.md, dedented (exactly one fence in the bullet)."""
    bullet = _range_bullet(text)
    opens = bullet.count("```bash\n")
    if opens != 1:
        raise AssertionError("expected one bash fence in the bullet, got %d"
                             % opens)
    body_start = bullet.index("```bash\n") + len("```bash\n")
    body = bullet[body_start:bullet.index("```", body_start)]
    return "\n".join(ln.strip() for ln in body.split("\n"))


def prose_range_source(text, route):
    """The first backticked command in the range-source table row whose
    route cell starts with `route`."""
    for ln in _range_bullet(text).split("\n"):
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].startswith(route):
            m = cells[1].split("`")
            if len(m) >= 3:
                return m[1]
    raise AssertionError("no range-source row for %r" % route)


class TestProseRangeFence(_Repo):
    """The fence in 30-collect-score.md, read from the file (never retyped),
    run in a fresh `bash -s` inside a temp repo."""

    def setUp(self):
        super().setUp()
        self.text = _collect_text()
        self.fence = prose_range_fence(self.text)
        self.default_source = prose_range_source(self.text, "default")
        L = list(BASE)
        L[11] = "twelve"
        del L[20]  # line 21
        self.write_lines(L)

    def run_fence(self, source, vc_root=PLUGIN_ROOT):
        self.assertIn("<range source>", self.fence)
        script = self.fence.replace("<range source>", source)
        env = gitfixture.helper_env()
        env["VC_ROOT"] = vc_root
        return subprocess.run(["bash", "-s"], input=script, cwd=self.repo,
                              env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, timeout=60)

    def test_fence_shape(self):
        self.assertIn("set -o pipefail", self.fence)
        self.assertIn('python3 "$VC_ROOT/scripts/diff_ranges.py"', self.fence)
        self.assertEqual(
            self.default_source,
            "git diff --no-color --no-ext-diff --src-prefix=a/ "
            "--dst-prefix=b/ HEAD")
        self.assertEqual(prose_range_source(self.text, "PR"),
                         "gh pr diff <ref> --color never")

    def test_default_route_matches_in_process(self):
        proc = self.run_fence(self.default_source)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        want = self.ranges(self.diff())
        self.assertEqual(want, {"f.txt": [[12, 12], [20, 21]]})
        self.assertEqual(json.loads(proc.stdout), want)

    def test_hostile_external_diff_config_changes_nothing(self):
        clean = self.run_fence(self.default_source)
        self.git("config", "diff.external", "false")
        self.git("config", "color.ui", "always")
        self.git("config", "diff.noprefix", "true")
        hostile = self.run_fence(self.default_source)
        self.assertEqual(hostile.returncode, 0, hostile.stderr)
        self.assertEqual(hostile.stdout, clean.stdout)

    def test_empty_diff_prints_empty_object(self):
        self.git("checkout", "--", "f.txt")
        proc = self.run_fence(self.default_source)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), {})

    def _assert_halted(self, proc):
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertIn(HALT_SENTENCE, proc.stderr)

    def test_helper_failure_halts(self):
        fake = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(fake))
        os.makedirs(os.path.join(fake, "scripts"))
        with open(os.path.join(fake, "scripts", "diff_ranges.py"), "w",
                  encoding="utf-8") as fh:
            fh.write("import sys\nsys.exit(2)\n")
        self._assert_halted(self.run_fence(self.default_source, vc_root=fake))

    def test_commit_series_halts(self):
        self.git("commit", "-q", "-a", "-m", "second")
        series = ("git format-patch --stdout --no-color --src-prefix=a/ "
                  "--dst-prefix=b/ HEAD~1..HEAD")
        self._assert_halted(self.run_fence(series))

    def test_failing_range_source_halts_through_pipefail(self):
        """The helper reads empty stdin and prints `{}` with exit 0; only
        pipefail turns the failed git call into a halt."""
        source = self.default_source.replace("HEAD", "no-such-rev")
        self._assert_halted(self.run_fence(source))
        unguarded = self.fence.replace("set -o pipefail", "")
        script = unguarded.replace("<range source>", source)
        env = gitfixture.helper_env()
        env["VC_ROOT"] = PLUGIN_ROOT
        proc = subprocess.run(["bash", "-s"], input=script, cwd=self.repo,
                              env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout), {})


if __name__ == "__main__":
    unittest.main()
