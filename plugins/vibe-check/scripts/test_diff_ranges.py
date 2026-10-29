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

DIFF_RANGES_PY = os.path.join(SCRIPTS_DIR, "diff_ranges.py")

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


if __name__ == "__main__":
    unittest.main()
