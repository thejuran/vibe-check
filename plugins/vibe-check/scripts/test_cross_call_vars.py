"""A shell variable set in one Bash call is read in a later one only by its
printed value.

Every Bash fence in a phase file runs as its own Bash call, so a variable a
fence sets is gone when the next fence runs. A later fence that reads it gets
an empty string. The only safe hand-over is for the setting fence to print the
value as `NAME=<value>` and for the later fence to use that printed literal.

This module walks every phase file and flags each read of a variable that an
earlier fence of the same file set without printing it.
"""
import ast
import os
import unittest


class LockCase(unittest.TestCase):
    def assert_holds(self, check, *texts):
        self.assertEqual(check(*texts), [])

    def assert_trips(self, check, *mutant_texts):
        self.assertNotEqual(check(*mutant_texts), [])


def doc(*fence_bodies, lang="bash", ticks=3, indent=""):
    """A small Markdown document with one fence per body, prose between."""
    parts = ["# A phase\n"]
    for body in fence_bodies:
        fence = "`" * ticks
        parts.append("Some prose.\n")
        parts.append(indent + fence + lang)
        for line in body.splitlines():
            parts.append(indent + line)
        parts.append(indent + fence + "\n")
    return "\n".join(parts) + "\n"


# --------------------------------------------------------------------------- #
# The fence rule.
# --------------------------------------------------------------------------- #
class TestBashFences(unittest.TestCase):
    def test_plain_fence_body_and_line(self):
        text = "intro\n```bash\nX=1\necho \"$X\"\n```\nafter\n"
        fences = bash_fences(text)
        self.assertEqual(len(fences), 1)
        line, body = fences[0]
        self.assertEqual(line, 2)
        self.assertEqual(body, 'X=1\necho "$X"')

    def test_indented_fence_is_scanned(self):
        text = "- step\n   ```bash\n   X=1\n   ```\n"
        self.assertEqual(len(bash_fences(text)), 1)
        self.assertIn("X=1", bash_fences(text)[0][1])

    def test_four_backtick_fence_is_scanned(self):
        text = "````bash\nX=1\n```\nstill inside\n````\n"
        fences = bash_fences(text)
        self.assertEqual(len(fences), 1)
        self.assertIn("still inside", fences[0][1])

    def test_other_language_fence_is_skipped_whole(self):
        text = ("```bash\nX=1\n```\n"
                "```python\nprint('$X')\n```bash\n```\n"
                "```bash\necho ok\n```\n")
        fences = bash_fences(text)
        self.assertEqual(len(fences), 2)
        self.assertNotIn("print", fences[0][1] + fences[1][1])

    def test_unlabelled_fence_is_skipped(self):
        self.assertEqual(bash_fences("```\nX=1\n```\n"), [])


# --------------------------------------------------------------------------- #
# Assignments, reads and printed names inside one fence.
# --------------------------------------------------------------------------- #
class TestAssignments(unittest.TestCase):
    FORMS = {
        "plain X=": "X=1",
        "append X+=": "X+=more",
        "if X=$(": 'if X=$(cmd); then :; fi',
        "export X=": "export X=1",
        "local X=": "local X=1",
        "readonly X=": "readonly X=1",
        "declare X=": "declare X=1",
        "declare -a X=": "declare -a X=(1 2)",
        "for X in": "for X in a b; do :; done",
        "read X": "read X < file",
        "after && on one line": 'cd here && X=1',
        "while IFS= read -r X": "while IFS= read -r X; do :; done",
    }

    def test_recognised_forms(self):
        for case, line in self.FORMS.items():
            with self.subTest(case):
                self.assertIn("X", [n for _, n in assignments(line)])

    def test_read_dash_r_two_names(self):
        names = [n for _, n in assignments("read -r X Y")]
        self.assertIn("X", names)
        self.assertIn("Y", names)

    def test_line_index_is_kept(self):
        self.assertEqual(assignments("echo hi\nX=1"), [(1, "X")])

    def test_not_assignments(self):
        for case, line in {
            "inside single quotes": "printf 'X=%s\\n' \"$A\"",
            "inside double quotes": 'echo "A=$A X=$X"',
            "comparison ==": '[[ "$A" == b ]]',
            "long option": "cmd --flag=1",
            "comment line": "# X=1",
            "trailing comment": "echo hi  # X=1",
            "quoted heredoc body": "cat <<'EOF'\nX=1\nEOF",
            "unquoted heredoc body": "cat <<EOF\nX=1\nEOF",
        }.items():
            with self.subTest(case):
                self.assertNotIn("X", [n for _, n in assignments(line)])


class TestReads(unittest.TestCase):
    def names(self, body):
        return [n for _, n in reads(body)]

    def test_read_forms(self):
        for case, line in {
            'double-quoted "$X"': 'echo "$X"',
            "bare $X": "echo $X",
            "braced ${X}": "echo ${X}",
            "default ${X:-d}": 'echo "${X:-d}"',
            "unquoted heredoc body": "cat <<EOF\n$X\nEOF",
            "apostrophe inside double quotes": 'echo "it\'s $X"',
        }.items():
            with self.subTest(case):
                self.assertIn("X", self.names(line))

    def test_not_reads(self):
        for case, line in {
            "single-quoted '$X'": "echo '$X'",
            "escaped \\$X": 'echo "\\$X"',
            "comment line": "# uses $X",
            "trailing comment": "echo hi  # uses $X",
            "quoted heredoc 'EOF'": "cat <<'EOF'\n$X\nEOF",
            'quoted heredoc "EOF"': 'cat <<"EOF"\n$X\nEOF',
            "multi-line single quotes": "jq '\n  $X\n' f",
        }.items():
            with self.subTest(case):
                self.assertNotIn("X", self.names(line))

    def test_special_parameters_are_never_reads(self):
        for special in ("$1", "$?", "$@", "$$", "$#", "$*", "$!", "$-", "$0"):
            with self.subTest(special):
                self.assertEqual(reads("echo %s" % special), [])

    def test_command_substitution_is_not_a_read(self):
        self.assertEqual(reads("echo $(date)"), [])

    def test_line_index_is_kept(self):
        self.assertEqual(reads("X=1\necho \"$X\""), [(1, "X")])

    def test_line_after_quoted_heredoc_is_read(self):
        self.assertIn("X", self.names("cat <<'EOF'\nbody\nEOF\necho \"$X\""))


class TestPrintedNames(unittest.TestCase):
    def test_printed_forms(self):
        for case, body in {
            "printf single name": "printf 'X=%s\\n' \"$X\"",
            "printf double-quoted format": 'printf "X=%s\\n" "$X"',
            "printf multi-name format": "printf 'A=%s\\nX=%s\\n' \"$A\" \"$X\"",
            'echo "X=$X"': 'echo "X=$X"',
            'echo "X=${X}"': 'echo "X=${X}"',
        }.items():
            with self.subTest(case):
                self.assertIn("X", printed_names(body))

    def test_not_printed(self):
        for case, body in {
            "printf of the value only": "printf '%s\\n' \"$X\"",
            "echo of another name": 'echo "Y=$X"',
            "no print": 'X=1',
        }.items():
            with self.subTest(case):
                self.assertNotIn("X", printed_names(body))


# --------------------------------------------------------------------------- #
# The cross-call rule over a whole document.
# --------------------------------------------------------------------------- #
class TestCrossCallReads(LockCase):
    def test_set_then_read_later_is_a_violation(self):
        self.assertEqual(cross_call_reads(doc("X=1", 'echo "$X"')),
                         [("X", 0, 1)])

    def test_printed_by_printf_is_no_violation(self):
        self.assertEqual(cross_call_reads(
            doc("X=1\nprintf 'X=%s\\n' \"$X\"", 'echo "$X"')), [])

    def test_printed_by_echo_is_no_violation(self):
        self.assertEqual(cross_call_reads(
            doc('X=1\necho "X=$X"', 'echo "$X"')), [])

    def test_printed_by_multi_name_format_is_no_violation(self):
        self.assertEqual(cross_call_reads(doc(
            "A=1\nX=2\nprintf 'A=%s\\nX=%s\\n' \"$A\" \"$X\"",
            'echo "$A $X"')), [])

    def test_reassigned_before_read_is_no_violation(self):
        self.assertEqual(cross_call_reads(doc("X=1", 'X=2\necho "$X"')), [])

    def test_read_before_reassignment_is_a_violation(self):
        self.assertEqual(cross_call_reads(doc("X=1", 'echo "$X"\nX=2')),
                         [("X", 0, 1)])

    def test_nearest_earlier_setter_is_named(self):
        self.assertEqual(cross_call_reads(doc("X=1", "X=2", 'echo "$X"')),
                         [("X", 1, 2)])

    def test_quoted_and_commented_reads_are_no_violation(self):
        for case, reader in {
            "single quotes": "echo '$X'",
            "escaped": 'echo "\\$X"',
            "comment": "# $X",
            "quoted heredoc": "cat <<'EOF'\n$X\nEOF",
        }.items():
            with self.subTest(case):
                self.assertEqual(cross_call_reads(doc("X=1", reader)), [])

    def test_braced_reads_are_violations(self):
        for reader in ('echo "${X}"', 'echo "${X:-d}"'):
            with self.subTest(reader):
                self.assertEqual(cross_call_reads(doc("X=1", reader)),
                                 [("X", 0, 1)])

    def test_name_set_in_no_earlier_fence_is_no_violation(self):
        # A cross-file name such as VC_ROOT is set in another phase file.
        self.assertEqual(cross_call_reads(
            doc('python3 "$VC_ROOT/scripts/x.py"', 'X=1')), [])

    def test_indented_and_four_backtick_fences_are_scanned(self):
        text = ("   ```bash\n   X=1\n   ```\n"
                "```python\nprint('$X')\n```\n"
                "````bash\necho \"$X\"\n````\n")
        self.assertEqual(cross_call_reads(text), [("X", 0, 1)])

    def test_other_language_fence_between_is_skipped(self):
        text = ("```bash\nX=1\n```\n"
                "```sh\necho \"$X\"\n```\n")
        self.assertEqual(cross_call_reads(text), [])

    def test_text_outside_fences_never_counts(self):
        text = ("Set X=1 in prose, then read \"$X\".\n"
                "```bash\necho \"$X\"\n```\n"
                "Prose X=2.\n"
                "```bash\necho \"$X\"\n```\n")
        self.assertEqual(cross_call_reads(text), [])

    def test_one_record_per_setter_reader_pair(self):
        self.assertEqual(cross_call_reads(doc("X=1", 'echo "$X" "$X"')),
                         [("X", 0, 1)])


# --------------------------------------------------------------------------- #
# This module stays stdlib only.
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    ALLOWED = {"ast", "importlib", "os", "re", "unittest"}

    def test_imports_are_stdlib_only(self):
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        self.assertLessEqual(imported, self.ALLOWED)


if __name__ == "__main__":
    unittest.main()
