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
import re
import unittest

# --------------------------------------------------------------------------- #
# The fence rule, transcribed from docs/design/lean-v2.15/tools/step_count.py:
# an optional indent, three or four backticks and `bash` open a Bash fence; the
# close is the same number of backticks; fences in other languages are skipped
# whole.
# --------------------------------------------------------------------------- #
FENCE_OPEN = re.compile(r"^[ \t]*`{3,4}bash$")
_ANY_FENCE_OPEN = re.compile(r"^[ \t]*(`{3,})[^`]*$")


def _ticks(line):
    stripped = line.lstrip(" \t")
    return len(stripped) - len(stripped.lstrip("`"))


def bash_fences(text):
    """[(line number of the opening fence line, 1-based, body text)] for
    every Bash fence in `text`, in order."""
    fences = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        is_bash = bool(FENCE_OPEN.match(line))
        if is_bash or _ANY_FENCE_OPEN.match(line):
            opened_at = i + 1
            close = re.compile(r"^[ \t]*`{%d}$" % _ticks(line))
            body = []
            i += 1
            while i < len(lines) and not close.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1  # past the closing line (or the end of the text)
            if is_bash:
                fences.append((opened_at, "\n".join(body)))
            continue
        i += 1
    return fences


# --------------------------------------------------------------------------- #
# Reading shell text one line at a time.
# --------------------------------------------------------------------------- #
_NAME = r"[A-Za-z_][A-Za-z0-9_]*"
_HEREDOC = re.compile(
    r"<<-?[ \t]*(?:'([^']*)'|\"([^\"]*)\"|\\?(%s))" % _NAME)
_WORD_START = " \t;&|()"


def _code_lines(body):
    """[(line index, kind, read_view, assign_view)] for the lines of a fence.

    `kind` is "code" or "heredoc" (the body of a heredoc whose delimiter is
    unquoted; the body of a quoted-delimiter heredoc is dropped). On a code
    line, `read_view` blanks single-quoted text, escaped characters and the
    heredoc operator, and ends where a comment starts; `assign_view` also
    blanks double-quoted text. Blanked characters become spaces, so a column
    means the same place in the line and in both views. Quote state carries
    across lines, as in the shell."""
    out = []
    lines = body.split("\n")
    in_single = in_double = False
    heredocs = []  # [(delimiter, quoted)] opened on the current line
    i = 0
    while i < len(lines):
        line = lines[i]
        read_view, assign_view = [], []

        def keep(text, in_assign=True):
            read_view.append(text)
            assign_view.append(text if in_assign else " " * len(text))

        def blank(n):
            read_view.append(" " * n)
            assign_view.append(" " * n)

        j = 0
        while j < len(line):
            c = line[j]
            if in_single:
                if c == "'":
                    in_single = False
                    keep(c)
                else:
                    blank(1)
                j += 1
                continue
            if c == "\\":
                # an escaped character is never a quote, `$` or `#`
                blank(len(line[j:j + 2]))
                j += 2
                continue
            if in_double:
                if c == '"':
                    in_double = False
                    keep(c)
                else:
                    keep(c, in_assign=False)
                j += 1
                continue
            if c == "'":
                in_single = True
            elif c == '"':
                in_double = True
            elif c == "#" and (j == 0 or line[j - 1] in _WORD_START):
                break  # the rest of the line is a comment
            elif line.startswith("<<", j) and not line.startswith("<<<", j):
                m = _HEREDOC.match(line, j)
                if m:
                    quoted = m.group(3) is None
                    delim = m.group(1) if m.group(1) is not None else (
                        m.group(2) if m.group(2) is not None else m.group(3))
                    heredocs.append((delim, quoted))
                    blank(m.end() - j)
                    j = m.end()
                    continue
            keep(c)
            j += 1
        out.append((i, "code", "".join(read_view), "".join(assign_view)))
        i += 1
        for delim, quoted in heredocs:
            while i < len(lines) and lines[i].strip() != delim:
                if not quoted:
                    view = lines[i].replace("\\$", "  ")
                    out.append((i, "heredoc", view, " " * len(view)))
                i += 1
            i += 1  # past the delimiter line
        heredocs = []
    return out


_ASSIGN = re.compile(
    r"(?:^|(?<=[ \t;&|(!]))"
    r"(?:(?:export|local|readonly|declare|typeset)(?:[ \t]+-[A-Za-z]+)*[ \t]+)?"
    r"(%s)\+?=(?!=)" % _NAME)
_FOR = re.compile(r"(?:^|(?<=[ \t;&|(]))for[ \t]+(%s)[ \t]+in\b" % _NAME)
_READ = re.compile(r"(?:^|(?<=[ \t;&|(]))read((?:[ \t]+[^ \t;&|<>()]+)+)")
_READ_ARG_OPTS = {"-d", "-p", "-t", "-n", "-N", "-u", "-i"}
_READ_NAME = re.compile(r"^%s$" % _NAME)
_READ_REF = re.compile(r"\$\{?#?(%s)" % _NAME)
# What ends one command and starts the next on the same line.
_SEPARATOR = re.compile(r";|&&|\|\||(?<![A-Za-z0-9_])(?:then|do)(?![A-Za-z0-9_])")


def _assignment_sites(lines):
    """[(line index, column, NAME)] over `_code_lines` output."""
    found = []
    for idx, kind, _, view in lines:
        if kind != "code":
            continue
        names = [(m.start(1), m.group(1)) for m in _ASSIGN.finditer(view)]
        names += [(m.start(1), m.group(1)) for m in _FOR.finditer(view)]
        for m in _READ.finditer(view):
            tokens = m.group(1).split()
            k = 0
            while k < len(tokens):
                tok = tokens[k]
                if tok.startswith("-"):
                    k += 2 if tok in _READ_ARG_OPTS else 1
                    continue
                if _READ_NAME.match(tok):
                    names.append((m.start(1), tok))
                k += 1
        found += [(idx, col, name) for col, name in sorted(names)]
    return found


def _read_sites(lines):
    """[(line index, column, NAME)] over `_code_lines` output."""
    found = []
    for idx, _, view, _ in lines:
        found += [(idx, m.start(), m.group(1)) for m in _READ_REF.finditer(view)]
    return found


def assignments(body):
    """[(line index, NAME)] for every shell variable `body` assigns."""
    return [(idx, name) for idx, _, name in _assignment_sites(_code_lines(body))]


def reads(body):
    """[(line index, NAME)] for every `$NAME` / `${NAME…}` `body` expands.
    Special parameters (`$1`, `$?`, `$@`, `$$`, `$#` …) never match."""
    return [(idx, name) for idx, _, name in _read_sites(_code_lines(body))]


def _assigned_before_read(lines, sites, line, col, name):
    """True when `name` is assigned before the read at (line, col): on an
    earlier line, or earlier on the same line with a command separator
    between (`X=1; echo "$X"`), not in the same command (`X=$(f "$X")`)."""
    views = {idx: view for idx, kind, _, view in lines if kind == "code"}
    for k, c, n in sites:
        if n != name:
            continue
        if k < line:
            return True
        if k == line and c < col and _SEPARATOR.search(views[k][c:col]):
            return True
    return False


_PRINTF_FORMAT = re.compile(
    r"\bprintf[ \t]+(?:--[ \t]+)?(?:'([^']*)'|\"([^\"]*)\")")
_FORMAT_NAME = re.compile(r"(?<![A-Za-z0-9_])(%s)=%%s" % _NAME)
_ECHO_STRING = re.compile(r"\becho[ \t]+(?:-[a-zA-Z]+[ \t]+)*\"([^\"]*)\"")
_ECHO_PAIR = re.compile(r"(?<![A-Za-z0-9_])(%s)=\$\{?(%s)\}?" % (_NAME, _NAME))


def printed_names(body):
    """Every NAME `body` prints as `NAME=<value>`: a `NAME=%s` in a printf
    format string, or `echo "NAME=$NAME"`."""
    names = set()
    for m in _PRINTF_FORMAT.finditer(body):
        fmt = m.group(1) if m.group(1) is not None else m.group(2)
        fmt = re.sub(r"\\.", " ", fmt)  # `\n`, `\t` … separate names
        names |= set(_FORMAT_NAME.findall(fmt))
    for m in _ECHO_STRING.finditer(body):
        names |= {a for a, b in _ECHO_PAIR.findall(m.group(1)) if a == b}
    return names


def cross_call_reads(text):
    """Sorted [(NAME, setter fence index, reader fence index)]: a read in
    fence j of a NAME that fence j has not assigned before it (an earlier
    line, or an earlier command on the same line), whose nearest earlier
    setter is fence i, with no fence from i to j-1 that both assigns and
    prints NAME. Same file only."""
    fences = [body for _, body in bash_fences(text)]
    lines = [_code_lines(b) for b in fences]
    sites = [_assignment_sites(ls) for ls in lines]
    set_names = [{n for _, _, n in s} for s in sites]
    printed = [printed_names(b) for b in fences]
    found = set()
    for j in range(len(fences)):
        for line, col, name in _read_sites(lines[j]):
            if _assigned_before_read(lines[j], sites[j], line, col, name):
                continue
            setters = [i for i in range(j) if name in set_names[i]]
            if not setters:
                continue
            i = setters[-1]
            if any(name in printed[k] for k in setters if i <= k < j):
                continue
            found.add((name, i, j))
    return sorted(found)


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

    def test_reassigned_earlier_on_the_same_line_is_no_violation(self):
        for case, reader in {
            "after ;": 'X=$(cmd); mkdir -p "$X/a"',
            "after &&": 'X=1 && echo "$X"',
            "if X=$(…); then": 'if X=$(cmd); then echo "$X"; fi',
        }.items():
            with self.subTest(case):
                self.assertEqual(cross_call_reads(doc("X=1", reader)), [])

    def test_read_in_the_same_command_as_the_reassignment_is_a_violation(self):
        for case, reader in {
            "read inside the right-hand side": 'X=$(cmd "$X")',
            "prefix assignment": 'X=1 cmd "$X"',
        }.items():
            with self.subTest(case):
                self.assertEqual(cross_call_reads(doc("X=1", reader)),
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
