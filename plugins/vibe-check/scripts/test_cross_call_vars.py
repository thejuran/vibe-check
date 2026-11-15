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
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gitfixture  # noqa: E402  (shared temp-repo helper)

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


# --------------------------------------------------------------------------- #
# The whole tree.
# --------------------------------------------------------------------------- #
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(PLUGIN_ROOT))
STEP_COUNT_PY = os.path.join(
    REPO_ROOT, "docs", "design", "lean-v2.15", "tools", "step_count.py")

# Today's flagged places, by file and variable name, each with the id of its
# fresh-shell reproduction record. The check fails on a flag not listed here
# AND on a listed pair that no longer flags, so the list can only shrink.
EXCEPTIONS = {
    ("phases/review/05-state.md", "LEGACY_STATE_FILE"): "X2",
    ("phases/review/05-state.md", "STATE_FILE"): "X3",
    ("phases/review/06-config.md", "CODEX_FLAG_VAL"): "X4",
    ("phases/review/06-config.md", "CONFIG_REPO_ROOT"): "X5",
    ("phases/review/06-config.md", "MIN_CONFIDENCE_FLAG_VAL"): "X6",
}

KNOWN_LIMITS = (
    "The check covers plugins/vibe-check/phases/ only; command and agent "
    "files are not scanned.",
    "The check is same-file: a read whose setter is in another file is not "
    "checked.",
)


def phase_files():
    """Every .md file under PLUGIN_ROOT/phases, in sorted order."""
    found = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(PLUGIN_ROOT, "phases")):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        found += [os.path.join(dirpath, n) for n in filenames if n.endswith(".md")]
    return sorted(found)


def flagged_pairs():
    """{(path under the plugin root, NAME)} for every cross-call read."""
    pairs = set()
    for path in phase_files():
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        rel = os.path.relpath(path, PLUGIN_ROOT).replace(os.sep, "/")
        pairs |= {(rel, name) for name, _, _ in cross_call_reads(text)}
    return pairs


def check_exceptions(flagged, exceptions):
    """Problems when the flagged set and the named exceptions differ."""
    listed = set(exceptions)
    return (["new cross-call read: %s %s" % p for p in sorted(flagged - listed)]
            + ["listed but no longer flagged: %s %s" % p
               for p in sorted(listed - flagged)])


def load_step_count():
    spec = importlib.util.spec_from_file_location("step_count", STEP_COUNT_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def remove(text, needle):
    assert needle in text, needle
    return text.replace(needle, "")


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
# The whole tree: every phase file, today's flagged places by name.
# --------------------------------------------------------------------------- #
FINALIZE_REL = "phases/shared/90-finalize.md"
STATE_REL = "phases/review/05-state.md"
BLOBFILE_PRINT = "printf 'BLOBFILE=%s\\n' \"$BLOBFILE\""


def read_rel(relpath):
    with open(os.path.join(PLUGIN_ROOT, relpath), encoding="utf-8") as fh:
        return fh.read()


def flagged_names(text):
    return {name for name, _, _ in cross_call_reads(text)}


class TestWholeTree(LockCase):
    def test_flagged_places_are_exactly_the_named_exceptions(self):
        self.assert_holds(check_exceptions, flagged_pairs(), EXCEPTIONS)

    def test_walk_sees_every_phase_file_and_its_fences(self):
        # Guards a scan that finds nothing: 27 phase files, >= 70 Bash fences.
        files = list(phase_files())
        self.assertEqual(len(files), 27)
        fences = 0
        for path in files:
            with open(path, encoding="utf-8") as fh:
                fences += len(bash_fences(fh.read()))
        self.assertGreaterEqual(fences, 70)

    def test_walk_includes_indented_and_four_backtick_fences(self):
        indented = four = 0
        for path in phase_files():
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            for line_no, _ in bash_fences("\n".join(lines)):
                opener = lines[line_no - 1]
                indented += opener[:1] in (" ", "\t")
                four += opener.lstrip(" \t").startswith("````")
        self.assertGreater(indented, 0)
        self.assertGreater(four, 0)

    def test_fence_rule_equals_step_count_on_finalize(self):
        text = read_rel(FINALIZE_REL)
        step_count = load_step_count()
        self.assertEqual(len(bash_fences(text)), len(step_count.fences(text)))
        self.assertEqual([b for _, b in bash_fences(text)],
                         step_count.fences(text))

    def test_exception_ids_are_unique_repro_ids(self):
        self.assertEqual(len(set(EXCEPTIONS.values())), len(EXCEPTIONS))
        for key, repro in EXCEPTIONS.items():
            with self.subTest(key=key):
                self.assertRegex(repro, r"^X[0-9]+$")
                relpath, name = key
                self.assertTrue(relpath.startswith("phases/"))
                self.assertRegex(name, r"^[A-Za-z_][A-Za-z0-9_]*$")

    def test_known_limits_are_written_down(self):
        self.assertEqual(len(KNOWN_LIMITS), 2)
        joined = " ".join(KNOWN_LIMITS)
        for needle in ("command", "agent", "another file"):
            with self.subTest(needle):
                self.assertIn(needle, joined)


class TestMutants(LockCase):
    def test_c_blobfile_print_removed_from_finalize_trips(self):
        text = read_rel(FINALIZE_REL)
        self.assertNotIn("BLOBFILE", flagged_names(text))
        mutant = remove(text, BLOBFILE_PRINT)
        self.assertNotIn(BLOBFILE_PRINT, mutant)
        self.assertIn("BLOBFILE", flagged_names(mutant))

    def test_d_cross_call_gate_variable_reinserted_trips(self):
        text = read_rel(FINALIZE_REL)
        self.assertNotIn("FINALIZE_GATE_INPUT_JSON", flagged_names(text))
        mutant = text + (
            "\n```bash\nFINALIZE_GATE_INPUT_JSON='{\"flags\": {}}'\n```\n"
            "\n```bash\nprintf '%s' \"$FINALIZE_GATE_INPUT_JSON\" | "
            "python3 \"$VC_ROOT/scripts/finalize_gate.py\"\n```\n")
        self.assertEqual(len(bash_fences(mutant)), len(bash_fences(text)) + 2)
        self.assertIn("FINALIZE_GATE_INPUT_JSON", flagged_names(mutant))

    def test_a_setter_and_reader_appended_to_a_real_file(self):
        text = read_rel(STATE_REL)
        self.assertNotIn("XVAR_MUTANT", text)
        base = len(bash_fences(text))
        mutant = text + ("\n```bash\nXVAR_MUTANT=$(pwd)\n```\n"
                         "\n```bash\nls \"$XVAR_MUTANT\"\n```\n")
        self.assertEqual(len(bash_fences(mutant)), base + 2)
        self.assertIn(("XVAR_MUTANT", base, base + 1), cross_call_reads(mutant))
        with self.subTest("the same with the value printed holds"):
            printed = text + (
                "\n```bash\nXVAR_MUTANT=$(pwd)\n"
                "printf 'XVAR_MUTANT=%s\\n' \"$XVAR_MUTANT\"\n```\n"
                "\n```bash\nls \"$XVAR_MUTANT\"\n```\n")
            self.assertNotIn("XVAR_MUTANT", flagged_names(printed))

    def test_x1_phase_dir_print_removed_trips(self):
        text = read_rel(SCOPE_REL)
        self.assertNotIn("PHASE_DIR", flagged_names(text))
        mutant = remove(text, "printf 'PHASE_DIR=%s\\n' \"$PHASE_DIR\"")
        self.assertIn("PHASE_DIR", flagged_names(mutant))

    def test_h_new_flag_and_stale_entry_both_trip(self):
        flagged = flagged_pairs()
        with self.subTest("an unlisted pair"):
            fake = ("phases/review/00-scope.md", "XVAR_UNLISTED")
            self.assertNotIn(fake, EXCEPTIONS)
            self.assert_trips(check_exceptions, flagged | {fake}, EXCEPTIONS)
        with self.subTest("a listed pair that no longer flags"):
            stale = ("phases/review/00-scope.md", "XVAR_STALE")
            self.assertNotIn(stale, flagged)
            self.assert_trips(check_exceptions, flagged,
                              {**EXCEPTIONS, stale: "X99"})
        for key in sorted(EXCEPTIONS):
            with self.subTest("a listed pair dropped from the flags", key=key):
                self.assert_trips(check_exceptions, flagged - {key}, EXCEPTIONS)


# --------------------------------------------------------------------------- #
# Fresh-shell reproductions of the flagged places.
#
# The standard, the same for every flagged (file, NAME) pair:
#   1. Fresh run: the real setter block and each real reader block, found in
#      the live file by a needle, each run as its own `bash -s` process with
#      only PATH, VC_ROOT, TMPDIR and the bootstrap names GUARD_PY / CONFIG_PY
#      (plus the null git config every fixture repo uses), in a temp git repo,
#      with the literals the instruction says to substitute substituted and
#      NAME not supplied.
#   2. Control run: the same blocks, same environment, in ONE `bash -s`.
#   3. Outcome class: "stop" (a fresh block exits non-zero where the control
#      does not), "wrong-file" (the files on disk differ from the control's),
#      "ignored-setting" (both exit 0, the files agree, the printed result
#      differs: the setting had no effect), "harmless" (same exit codes,
#      output and files).
#   4. Reproduced means any class other than "harmless".
# --------------------------------------------------------------------------- #
OUTCOMES = ("stop", "wrong-file", "ignored-setting", "harmless")


def fence_holding(relpath, needle):
    """The body of the one Bash fence of `relpath` that holds `needle`."""
    bodies = [b for _, b in bash_fences(read_rel(relpath)) if needle in b]
    if len(bodies) != 1:
        raise AssertionError("%s: %d Bash fences hold %r (want 1)"
                             % (relpath, len(bodies), needle))
    return bodies[0]


def substitute(body, literals):
    """`body` with each token the instruction says to substitute replaced by
    its literal; every token must be present."""
    for token, literal in literals:
        if token not in body:
            raise AssertionError("token %r absent from the fence" % token)
        body = body.replace(token, literal)
    return body


def printed_literal(out, name):
    """The value one fence printed as `NAME=<value>` (exactly one line)."""
    found = [l[len(name) + 1:] for l in out.splitlines()
             if l.startswith(name + "=")]
    if len(found) != 1:
        raise AssertionError("%d %s= lines in %r (want 1)"
                             % (len(found), name, out))
    return found[0]


def tree_files(root):
    """{path relative to root: bytes} for every file outside .git."""
    found = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            path = os.path.join(dirpath, name)
            with open(path, "rb") as fh:
                found[os.path.relpath(path, root)] = fh.read()
    return found


class ShellRun:
    """One fixture repo, copied twice: run once fresh, once as the control."""

    def __init__(self, work, build):
        """`build(repo)` prepares the repo the instruction expects."""
        self.work = work
        base = gitfixture.make_repo(os.path.join(work, "base"))
        build(base)
        # Both copies are named `repo`, like the base, so a key built from
        # the repo's directory name is the same in both runs.
        self.fresh_repo = os.path.join(work, "fresh", "repo")
        self.control_repo = os.path.join(work, "control", "repo")
        shutil.copytree(base, self.fresh_repo, symlinks=True)
        shutil.copytree(base, self.control_repo, symlinks=True)

    def _bash(self, script, repo):
        tmpdir = tempfile.mkdtemp(dir=self.work)
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
               "VC_ROOT": PLUGIN_ROOT, "TMPDIR": tmpdir,
               "GUARD_PY": os.path.join(PLUGIN_ROOT, "scripts", "guard.py"),
               "CONFIG_PY": os.path.join(PLUGIN_ROOT, "scripts", "config.py"),
               "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        proc = subprocess.run(["bash", "-s"], input=script, cwd=repo, env=env,
                              capture_output=True, text=True, timeout=60)
        return (proc.returncode, proc.stdout.replace(repo, "<repo>"),
                proc.stderr.replace(repo, "<repo>"))

    def fresh(self, fences):
        """[(rc, stdout, stderr)], one fresh process per fence, in order."""
        return [self._bash(body + "\n", self.fresh_repo) for body in fences]

    def control(self, fences):
        """(rc, stdout, stderr) of the same fences in one process."""
        return self._bash("\n".join(fences) + "\n", self.control_repo)


def classify(fresh, control, fresh_files, control_files):
    """The outcome class of a fresh run against its control."""
    if control[0] != 0:
        raise AssertionError("the control did not complete: %r" % (control,))
    if any(rc != 0 for rc, _, _ in fresh):
        return "stop"
    if fresh_files != control_files:
        return "wrong-file"
    if "".join(out for _, out, _ in fresh) != control[1]:
        return "ignored-setting"
    return "harmless"


class TestClassify(unittest.TestCase):
    """The outcome rule itself, on hand-made results."""
    OK = (0, "x\n", "")

    def test_each_class(self):
        files = {"a": b"1"}
        self.assertEqual(classify([(0, "", ""), (1, "", "e")], self.OK,
                                  files, files), "stop")
        self.assertEqual(classify([(0, "x\n", "")], self.OK,
                                  files, {"a": b"2"}), "wrong-file")
        self.assertEqual(classify([(0, "y\n", "")], self.OK,
                                  files, files), "ignored-setting")
        self.assertEqual(classify([(0, "", ""), (0, "x\n", "")], self.OK,
                                  files, files), "harmless")

    def test_a_failed_control_is_a_broken_fixture(self):
        with self.assertRaises(AssertionError):
            classify([(0, "", "")], (1, "", "e"), {}, {})

    def test_a_missing_needle_fails(self):
        with self.assertRaises(AssertionError):
            fence_holding(STATE_REL, "XVAR_NO_SUCH_NEEDLE")
        with self.assertRaises(AssertionError):
            substitute("echo hi", [("<arg>", "02")])


# --------------------------------------------------------------------------- #
# The record: one row per flagged pair, what the fresh run showed, what the
# owner would see and the proposed disposition (the owner confirms it before
# anything is changed). `fixture` names the TestRepro63 test that reproduces it.
# --------------------------------------------------------------------------- #
SCOPE_REL = "phases/review/00-scope.md"
CONFIG_REL = "phases/review/06-config.md"
# What the owner decided for each row (63-REPRO.md, "Owner decision"): a
# fixed row is off the exceptions list; a pinned row stays on it by name.
FIXED = "reproduced; fixed by 63-10"
PINNED = "pinned; carried to backlog"

REPRO_63 = [
    {"id": "X1", "file": SCOPE_REL, "name": "PHASE_DIR",
     "outcome": "stop",
     "owner_sees": "A review of a GSD phase stops at the safety check with "
                   "'Phase resolution escaped .planning/ — refusing.' even "
                   "though the phase exists.",
     "proposed": "fix",
     "fixture": "TestRepro63.test_x1_phase_dir",
     "disposition": FIXED},
    {"id": "X2", "file": STATE_REL, "name": "LEGACY_STATE_FILE",
     "outcome": "wrong-file",
     "owner_sees": "A review whose saved progress is still in the old "
                   "location is not moved forward, so it starts again at "
                   "pass 1 instead of carrying on.",
     "proposed": "fix",
     "fixture": "TestRepro63.test_x2_legacy_state_file",
     "disposition": PINNED},
    {"id": "X3", "file": STATE_REL, "name": "STATE_FILE",
     "outcome": "stop",
     "owner_sees": "A second pass of a review stops with 'the state file's "
                   "last-pass head_sha is not a commit sha' although the "
                   "saved progress is fine.",
     "proposed": "fix",
     "fixture": "TestRepro63.test_x3_state_file",
     "disposition": PINNED},
    {"id": "X4", "file": CONFIG_REL, "name": "CODEX_FLAG_VAL",
     "outcome": "ignored-setting",
     "owner_sees": "Asking for '--codex off' has no effect: the review "
                   "runs with the Codex setting on its default instead.",
     "proposed": "owner decides",
     "fixture": "TestRepro63.test_x4_codex_flag_val",
     "disposition": PINNED},
    {"id": "X5", "file": CONFIG_REL, "name": "CONFIG_REPO_ROOT",
     "outcome": "ignored-setting",
     "owner_sees": "The repo's settings file is not read at all, so every "
                   "setting in it is silently replaced by the defaults.",
     "proposed": "owner decides",
     "fixture": "TestRepro63.test_x5_config_repo_root",
     "disposition": PINNED},
    {"id": "X6", "file": CONFIG_REL, "name": "MIN_CONFIDENCE_FLAG_VAL",
     "outcome": "ignored-setting",
     "owner_sees": "Asking for '--min-confidence 45' has no effect: no "
                   "low-confidence finding is filtered out.",
     "proposed": "owner decides",
     "fixture": "TestRepro63.test_x6_min_confidence_flag_val",
     "disposition": PINNED},
]

PROPOSED_FOR = {"stop": "fix", "wrong-file": "fix",
                "ignored-setting": "owner decides", "harmless": "pin"}
ROW_KEYS = {"id", "file", "name", "outcome", "owner_sees", "proposed",
            "fixture", "disposition"}


def record_problems(rows, exceptions):
    """Problems with the record against the exceptions list."""
    problems = []
    want = {repro: key for key, repro in exceptions.items()}
    ids = [r.get("id") for r in rows]
    for rid in sorted(set(want) - set(ids)):
        problems.append("no record row for %s" % rid)
    for rid in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append("more than one row for %s" % rid)
    for row in rows:
        rid = row.get("id")
        if set(row) != ROW_KEYS:
            problems.append("%s: keys %s" % (rid, sorted(row)))
            continue
        if row["disposition"] == FIXED:
            if rid in want:
                problems.append("%s: fixed but still an exception" % rid)
        elif row["disposition"] != PINNED:
            problems.append("%s: unknown disposition %r"
                            % (rid, row["disposition"]))
        elif rid not in want:
            problems.append("%s: pinned but not an exception" % rid)
        elif (row["file"], row["name"]) != want[rid]:
            problems.append("%s: file/name differ from the exception" % rid)
        if row["outcome"] not in OUTCOMES:
            problems.append("%s: unknown outcome %r" % (rid, row["outcome"]))
        elif row["proposed"] != PROPOSED_FOR[row["outcome"]]:
            problems.append("%s: proposed %r does not follow the rule"
                            % (rid, row["proposed"]))
        cls, _, method = row["fixture"].partition(".")
        target = globals().get(cls)
        if not (isinstance(target, type) and method.startswith("test_")
                and callable(getattr(target, method, None))):
            problems.append("%s: no fixture %s" % (rid, row["fixture"]))
        if not row["owner_sees"].strip():
            problems.append("%s: empty owner sentence" % rid)
    return problems


class TestRepro63(unittest.TestCase):
    """Each flagged pair run fresh (one process per Bash block) next to a
    control (the same blocks in one process). Each test asserts what is
    observed today, not what should be."""

    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def run_pair(self, label, build, fences):
        """(fresh, control, outcome, fresh files, control files)."""
        work = os.path.join(self.tmp, label)
        os.makedirs(work)
        run = ShellRun(work, build)
        fresh = run.fresh(fences)
        control = run.control(fences)
        fresh_files = tree_files(run.fresh_repo)
        control_files = tree_files(run.control_repo)
        self.assertEqual(control[0], 0, control)
        return (fresh, control,
                classify(fresh, control, fresh_files, control_files),
                fresh_files, control_files)

    def run_carried(self, label, build, setter, readers, names):
        """Like run_pair, but the fresh readers get the literal each NAME's
        setter printed as `NAME=<value>`, substituted for `$NAME`, the way
        the instruction tells the model to carry it into a later Bash call."""
        work = os.path.join(self.tmp, label)
        os.makedirs(work)
        run = ShellRun(work, build)
        first = run.fresh([setter])
        literals = [("$" + n, printed_literal(first[0][1], n)) for n in names]
        carried = []
        for body in readers:
            for token, literal in literals:
                body = body.replace(token, literal)
            carried.append(body)
        for token, _ in literals:
            self.assertFalse(any(token in b for b in carried), token)
        fresh = first + run.fresh(carried)
        control = run.control([setter] + readers)
        fresh_files = tree_files(run.fresh_repo)
        control_files = tree_files(run.control_repo)
        self.assertEqual(control[0], 0, control)
        return (fresh, control,
                classify(fresh, control, fresh_files, control_files),
                fresh_files, control_files)

    # -- 00-scope.md ------------------------------------------------------- #
    @staticmethod
    def build_gsd_phase(repo):
        gitfixture.write(repo, "src/a.txt", "a\n")
        gitfixture.git(repo, "add", "-A")
        gitfixture.git(repo, "commit", "-qm", "base")
        gitfixture.write(repo, ".planning/phases/02-code-review/02-01-PLAN.md",
                         "plan\n")
        gitfixture.git(repo, "add", "-A")
        gitfixture.git(repo, "commit", "-qm", "phase")

    def test_x1_phase_dir(self):
        setter = substitute(fence_holding(SCOPE_REL, "PHASE_DIR=$(find"),
                            [("<arg>", "02")])
        readers = [
            fence_holding(SCOPE_REL,
                          'python3 "$GUARD_PY" --root "$PWD/.planning"'),
            fence_holding(SCOPE_REL, "PHASE_START=$(git log"),
        ]
        fresh, control, outcome, _, _ = self.run_carried(
            "x1", self.build_gsd_phase, setter, readers, ["PHASE_DIR"])
        phase_sha = gitfixture.git(
            os.path.join(self.tmp, "x1", "control", "repo"),
            "log", "--format=%H", "-1", "--", ".planning").stdout.strip()
        # The setter prints the phase dir; the guard and the phase range,
        # each run fresh with that literal, do what the one-shell run does.
        self.assertEqual(fresh[0][1],
                         "PHASE_DIR=.planning/phases/02-code-review\n")
        self.assertEqual([rc for rc, _, _ in fresh], [0, 0, 0])
        self.assertIn("contained", fresh[1][1])
        self.assertEqual(fresh[2][1], "PHASE_START=%s\n" % phase_sha)
        self.assertIn("PHASE_START=%s\n" % phase_sha, control[1])
        self.assertEqual(outcome, "harmless")

    # -- 05-state.md ------------------------------------------------------- #
    STATE_SETTERS = (
        ("gsd", 'STATE_FILE=".turingmind/state/format-53/${PHASE_ID}',
         [("${PHASE_ID}", "02-code-review")], "02-code-review"),
        ("branch", "BRANCH_SLUG=$(git branch", [], "repo-main"),
    )

    @staticmethod
    def build_state(key):
        """A repo with one commit and a pass-1 state file in the old place."""
        def build(repo):
            gitfixture.write(repo, "src/a.txt", "a\n")
            gitfixture.git(repo, "add", "-A")
            gitfixture.git(repo, "commit", "-qm", "base")
            sha = gitfixture.git(repo, "rev-parse", "HEAD").stdout.strip()
            gitfixture.write(repo, ".turingmind/state/%s.json" % key,
                             json.dumps({"passes": [{"pass_number": 1,
                                                     "head_sha": sha,
                                                     "findings": []}]}))
        return build

    def state_setter(self, needle, literals):
        body = fence_holding(STATE_REL, needle)
        return substitute(body, literals) if literals else body

    STATE_NAMES = ["LEGACY_STATE_FILE", "STATE_FILE"]

    def test_x2_legacy_state_file(self):
        migrate = fence_holding(STATE_REL, 'review_archive.py" migrate')
        for mode, needle, literals, key in self.STATE_SETTERS:
            with self.subTest(mode=mode):
                fresh, control, outcome, fresh_files, control_files = (
                    self.run_carried("x2-" + mode, self.build_state(key),
                                     self.state_setter(needle, literals),
                                     [migrate], self.STATE_NAMES))
                old = ".turingmind/state/%s.json" % key
                new = ".turingmind/state/format-53/%s.json" % key
                # The setter prints both names; the move-forward block, run
                # fresh with those literals, moves the old file forward and
                # archives it, as the one-shell run does.
                self.assertEqual(fresh[0][1],
                                 "LEGACY_STATE_FILE=%s\nSTATE_FILE=%s\n"
                                 % (old, new))
                self.assertEqual([rc for rc, _, _ in fresh], [0, 0])
                self.assertIn("state migrated forward to " + new, fresh[1][1])
                self.assertIn(new, fresh_files)
                self.assertNotIn(old, fresh_files)
                self.assertEqual(fresh_files, control_files)
                self.assertEqual(outcome, "harmless")

    def test_x3_state_file(self):
        readers = [
            fence_holding(STATE_REL, 'review_archive.py" migrate'),
            substitute(fence_holding(STATE_REL, "last-head-sha"),
                       [('"$FINALIZE_MODE"', '"0"')]),
            fence_holding(STATE_REL, 'carry_state.py" decided'),
            fence_holding(STATE_REL, 'carry_state.py" deferred'),
        ]
        for mode, needle, literals, key in self.STATE_SETTERS:
            with self.subTest(mode=mode):
                fresh, control, outcome, _, _ = self.run_carried(
                    "x3-" + mode, self.build_state(key),
                    self.state_setter(needle, literals), readers,
                    self.STATE_NAMES)
                sha = gitfixture.git(
                    os.path.join(self.tmp, "x3-" + mode, "control", "repo"),
                    "rev-parse", "HEAD").stdout.strip()
                # Each block that reads the state file, run fresh with the
                # printed literal, carries the review as the one-shell run
                # does: the last pass and the decided and deferred lists.
                self.assertIn("LAST_REVIEWED_SHA=%s\n[]\n[]\n" % sha,
                              control[1])
                self.assertEqual([rc for rc, _, _ in fresh], [0, 0, 0, 0, 0])
                self.assertEqual(fresh[2][1], "LAST_REVIEWED_SHA=%s\n" % sha)
                self.assertEqual(fresh[3][1], "[]\n")
                self.assertEqual(fresh[4][1], "[]\n")
                self.assertEqual(outcome, "harmless")
        with self.subTest(mode="gsd, --finalize"):
            # On a Close-out run the head_sha block binds nothing; the
            # decided and deferred blocks still read the state file.
            mode, needle, literals, key = self.STATE_SETTERS[0]
            readers_finalize = [
                readers[0],
                substitute(fence_holding(STATE_REL, "last-head-sha"),
                           [('"$FINALIZE_MODE"', '"1"')]),
                readers[2], readers[3]]
            fresh, control, outcome, _, _ = self.run_carried(
                "x3-finalize", self.build_state(key),
                self.state_setter(needle, literals), readers_finalize,
                self.STATE_NAMES)
            self.assertNotIn("LAST_REVIEWED_SHA=", control[1])
            self.assertIn("[]\n[]\n", control[1])
            self.assertEqual([rc for rc, _, _ in fresh], [0, 0, 0, 0, 0])
            self.assertEqual(outcome, "harmless")

    # -- 06-config.md ------------------------------------------------------ #
    # The owner's invocation, substituted for "$ARGUMENTS", and a repo config
    # that disables one agent. The invoke block prints nothing, so the same
    # one observation line is appended to it in both runs.
    CONFIG_ARGS = '"--min-confidence 45 --codex off"'
    CONFIG_PROBE = "printf 'CONFIG_JSON=%s\\n' \"$CONFIG_JSON\""

    @staticmethod
    def build_config(repo):
        gitfixture.write(repo, ".vibe-check.toml",
                         '[agents]\ndisabled = ["style"]\n')
        gitfixture.git(repo, "add", "-A")
        gitfixture.git(repo, "commit", "-qm", "base")

    def config_pair(self, label, setter):
        fences = [setter,
                  fence_holding(CONFIG_REL, "CONFIG_JSON=$(REPO_ROOT=")
                  + "\n" + self.CONFIG_PROBE]
        fresh, control, outcome, _, _ = self.run_pair(
            label, self.build_config, fences)
        self.assertEqual([rc for rc, _, _ in fresh], [0, 0])
        self.assertEqual(fresh[0][1], "")
        return (self.config_values(fresh[1][1]), self.config_values(control[1]),
                outcome)

    def config_values(self, out):
        line = [l for l in out.splitlines() if l.startswith("CONFIG_JSON=")]
        self.assertEqual(len(line), 1, out)
        return json.loads(line[0][len("CONFIG_JSON="):])["values"]

    def flag_setter(self, needle):
        return substitute(fence_holding(CONFIG_REL, needle),
                          [('"$ARGUMENTS"', self.CONFIG_ARGS)])

    def test_x4_codex_flag_val(self):
        fresh, control, outcome = self.config_pair(
            "x4", self.flag_setter("CODEX_FLAG_VAL=$(printf"))
        self.assertEqual(control["codex"], "off")
        self.assertEqual(fresh["codex"], "auto")
        self.assertEqual(outcome, "ignored-setting")

    def test_x5_config_repo_root(self):
        fresh, control, outcome = self.config_pair(
            "x5", fence_holding(CONFIG_REL, "CONFIG_REPO_ROOT=$(git rev-parse"))
        # An empty repo root does not make the helper refuse: it reads no
        # config file at all and returns the defaults.
        self.assertEqual(control["disabled"], ["style"])
        self.assertEqual(fresh["disabled"], [])
        self.assertEqual(outcome, "ignored-setting")

    def test_x6_min_confidence_flag_val(self):
        fresh, control, outcome = self.config_pair(
            "x6", self.flag_setter("MIN_CONFIDENCE_FLAG_VAL=$(printf"))
        self.assertEqual(control["min_confidence"], 45)
        self.assertIsNone(fresh["min_confidence"])
        self.assertEqual(outcome, "ignored-setting")


class TestRepro63Record(LockCase):
    """Every exception has exactly one record row, with a fixture that
    exists, an allowed outcome and the disposition the rule gives it."""

    def test_record_holds(self):
        self.assert_holds(record_problems, REPRO_63, EXCEPTIONS)

    def test_mutant_row_removed_trips(self):
        # An exception with no row trips (X1 put back on the list, its row
        # gone).
        fewer = [r for r in REPRO_63 if r["id"] != "X1"]
        self.assertEqual(len(fewer), len(REPRO_63) - 1)
        listed = {**EXCEPTIONS, (SCOPE_REL, "PHASE_DIR"): "X1"}
        self.assertEqual(record_problems(fewer, listed),
                         ["no record row for X1"])

    def test_mutant_fixture_misspelled_trips(self):
        rows = [dict(r) for r in REPRO_63]
        rows[0]["fixture"] = rows[0]["fixture"] + "_typo"
        self.assertEqual(record_problems(rows, EXCEPTIONS),
                         ["X1: no fixture %s" % rows[0]["fixture"]])

    def test_mutant_unknown_outcome_trips(self):
        rows = [dict(r) for r in REPRO_63]
        rows[0]["outcome"] = "flaky"
        self.assertEqual(record_problems(rows, EXCEPTIONS),
                         ["X1: unknown outcome 'flaky'"])

    def test_mutant_disposition_dropped_trips(self):
        rows = [dict(r) for r in REPRO_63]
        del rows[0]["disposition"]
        self.assertEqual(len(record_problems(rows, EXCEPTIONS)), 1)
        self.assertIn("X1: keys", record_problems(rows, EXCEPTIONS)[0])

    def test_mutant_disposition_off_the_list_trips(self):
        for row in REPRO_63:
            with self.subTest(row["id"]):
                key = (row["file"], row["name"])
                rows = [dict(r) for r in REPRO_63]
                flip = rows[REPRO_63.index(row)]
                if row["disposition"] == FIXED:
                    # a fixed row put back on the list
                    exc = {**EXCEPTIONS, key: row["id"]}
                    want = "%s: fixed but still an exception" % row["id"]
                else:
                    # a pinned row taken off the list
                    exc = {k: v for k, v in EXCEPTIONS.items() if k != key}
                    flip["disposition"] = PINNED
                    want = "%s: pinned but not an exception" % row["id"]
                self.assertIn(want, record_problems(rows, exc))
                flip["disposition"] = "maybe"
                self.assertIn("%s: unknown disposition 'maybe'" % row["id"],
                              record_problems(rows, EXCEPTIONS))

    def test_mutant_proposed_off_rule_trips(self):
        rows = [dict(r) for r in REPRO_63]
        rows[0]["proposed"] = "pin" if rows[0]["proposed"] != "pin" else "fix"
        self.assertEqual(record_problems(rows, EXCEPTIONS),
                         ["X1: proposed %r does not follow the rule"
                          % rows[0]["proposed"]])


# --------------------------------------------------------------------------- #
# This module stays stdlib only.
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    # gitfixture is the repo's own stdlib-only temp-repo helper.
    ALLOWED = {"ast", "importlib", "json", "os", "re", "shutil",
               "subprocess", "sys", "tempfile", "unittest", "gitfixture"}

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
