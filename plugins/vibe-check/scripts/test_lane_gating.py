"""test_lane_gating.py — prose locks for evidence-gated lane selection.

GATE-02: every lane's trigger is pinned. Both selection tables (the `/review`
table in phases/review/20-dispatch.md and the `/deep-review` table in
phases/deep-review/20-selection.md) are parsed and compared cell by cell to a
hand-written golden, so changing any lane's condition or Always mark fails a
test. The `framework-skill` rule gets a targeted checker on top of the golden
(conditional, keyed on the quoted `"skill"` token, the token used by no other
row), and the triage `"skill"` file-shape exception sentence is pinned.

GATE-01: the diff-mode coverage gate is wired at exactly one point. The
helper is invoked once in 01d-coverage.md and never from the shared dispatch
files; the selection-time gating paragraph sits after the `$CONFIG_DISABLED`
subtraction and is the only place `test-sufficiency` is removed; the slugs the
prose names come from `coverage_gate.CASES` and are never retyped here; the
render strings are fixed; and no prose line reads as a Phase 2 skip line under
tracecheck's own announcement regex.

Every scanner is a pure function over text. Each lock has a mutation test that
plants the regression in memory and asserts the scanner reports the specific
problem; no test writes a file. A lock with no tripping mutation is decorative
and does not count.
"""

import os
import re
import sys
import unittest

# Make sibling imports resolve when unittest discovery runs from the root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_agent_prompts import norm, read, missing_clauses, _ordered  # noqa: E402

import coverage_gate  # noqa: E402  (the sealed slug vocabulary)
import tracecheck  # noqa: E402  (ANNOUNCE_RE: what counts as a phase announcement)

HERE = os.path.dirname(os.path.abspath(__file__))

REVIEW_DISPATCH = "phases/review/20-dispatch.md"
REVIEW_DISPATCH_ALL = "phases/review/20-dispatch-all.md"
DEEP_SELECTION = "phases/deep-review/20-selection.md"
DEEP_COVERAGE = "phases/deep-review/01d-coverage.md"
DEEP_COMMAND = "commands/deep-review.md"
TRIAGE = "agents/triage.md"

REVIEW_TABLE_HEADING = "### Selection table"

_AGENT_CELL = re.compile(r"`([a-z-]+)`")


# --------------------------------------------------------------------------- #
# Selection-table parser
# --------------------------------------------------------------------------- #
def selection_rows(text, heading=None):
    """Rows of the first markdown table after `heading` (or the first table in
    `text` when heading is None) as (always, condition, agent, model) tuples.

    `model` is None for a 3-column table. Raises ValueError on a row whose cell
    count is not 3 or 4, whose Always cell is neither blank nor a check mark,
    or whose agent cell is not a single backticked name.
    """
    lines = text.splitlines()
    start = 0
    if heading is not None:
        for i, line in enumerate(lines):
            if line.strip() == heading:
                start = i + 1
                break
        else:
            raise ValueError("heading not found: %r" % heading)
    i = start
    while i < len(lines) and not lines[i].startswith("|"):
        i += 1
    if i >= len(lines):
        raise ValueError("no table found")
    i += 1  # header row
    if i >= len(lines) or not lines[i].startswith("|---"):
        raise ValueError("table has no separator row")
    i += 1
    rows = []
    while i < len(lines) and lines[i].startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if len(cells) not in (3, 4):
            raise ValueError("row has %d cells: %r" % (len(cells), lines[i]))
        mark = cells[0]
        if mark not in ("", "✓"):
            raise ValueError("unexpected Always cell %r" % mark)
        m = _AGENT_CELL.fullmatch(cells[2])
        if not m:
            raise ValueError("agent cell is not a single backticked name: %r" % cells[2])
        model = cells[3] if len(cells) == 4 else None
        rows.append((mark == "✓", cells[1], m.group(1), model))
        i += 1
    return rows


# Goldens are transcribed by hand from the files, never produced by the parser.
EXPECTED_REVIEW_ROWS = (
    (True, "—", "bugs", None),
    (True, "—", "security", None),
    (False, "`CLAUDE.md` or `AGENTS.md` in repo root or changed dir", "compliance", None),
    (False, "`.ts/.tsx/.js/.jsx/.mjs/.cjs/.vue` in diff", "language-typescript", None),
    (False, "`.py` in diff", "language-python", None),
    (False, "any `.go` in diff", "language-go", None),
    (False, "any `.rs` in diff", "language-rust", None),
    (False, 'triage.frameworks includes "react"', "framework-react", None),
    (False, 'triage.frameworks includes "fastapi"', "framework-fastapi", None),
    (False, 'triage.frameworks includes "skill" (`SKILL.md` / agent `.md` / plugin manifest)',
     "framework-skill", None),
    (False, 'triage.frameworks includes "express"', "framework-express", None),
    (False, 'triage.frameworks includes "vue"', "framework-vue", None),
    (False, 'triage.frameworks includes "angular"', "framework-angular", None),
    (False, 'triage.frameworks includes "electron"', "framework-electron", None),
    (False, 'triage.frameworks includes "react-native"', "framework-react-native", None),
)

EXPECTED_DEEP_ROWS = (
    (True, "—", "bugs", "**top** (per-call override)"),
    (True, "—", "security", "sonnet"),
    (True, "—", "architecture", "**top** (per-call override)"),
    (True, "—", "impact", "opus (frontmatter)"),
    (True, "—", "test-sufficiency", "opus (frontmatter)"),
    (False, "`CLAUDE.md`/`AGENTS.md` exists", "compliance", "sonnet"),
    (False, "TS/JS/.vue in diff", "language-typescript", "sonnet"),
    (False, "Python in diff", "language-python", "sonnet"),
    (False, "Go in diff", "language-go", "sonnet"),
    (False, "Rust in diff", "language-rust", "sonnet"),
    (False, "React imports", "framework-react", "sonnet"),
    (False, "FastAPI imports", "framework-fastapi", "sonnet"),
    (False, '"skill" (`SKILL.md` / agent `.md` / plugin manifest)', "framework-skill", "sonnet"),
    (False, "Express imports", "framework-express", "sonnet"),
    (False, "Vue imports / `.vue` SFC", "framework-vue", "sonnet"),
    (False, "Angular imports", "framework-angular", "sonnet"),
    (False, "Electron imports", "framework-electron", "sonnet"),
    (False, 'React Native imports (triage.frameworks "react-native")',
     "framework-react-native", "sonnet"),
)


# --------------------------------------------------------------------------- #
# framework-skill rule + triage clause
# --------------------------------------------------------------------------- #
SKILL_TOKEN = '"skill"'
SKILL_TRIAGE_PHRASE = 'triage.frameworks includes "skill"'


def skill_rule_problems(rows, require_triage_phrase):
    """Problems with the framework-skill trigger rule in parsed table rows."""
    problems = []
    skill_rows = [r for r in rows if r[2] == "framework-skill"]
    if not skill_rows:
        problems.append("missing framework-skill row")
    elif len(skill_rows) > 1:
        problems.append("duplicate framework-skill row")
    for always, condition, _agent, _model in skill_rows[:1]:
        if always:
            problems.append("framework-skill marked Always")
        if SKILL_TOKEN not in condition:
            problems.append('framework-skill condition lacks "skill"')
        if require_triage_phrase and SKILL_TRIAGE_PHRASE not in condition:
            problems.append("framework-skill condition lacks 'triage.frameworks includes \"skill\"'")
    for _always, condition, agent, _model in rows:
        if agent != "framework-skill" and SKILL_TOKEN in condition:
            problems.append('"skill" leaked into %s condition' % agent)
    return problems


TRIAGE_SKILL_ANCHOR = '**Exception — `"skill"` is detected by file shape, not imports:**'
TRIAGE_SKILL_CLAUSES = [
    TRIAGE_SKILL_ANCHOR,
    "a file named `SKILL.md`",
    "an agent prompt under an `agents/` directory whose markdown frontmatter has both "
    "`name:` and `description:` fields",
    "a plugin manifest (`plugin.json` or `.claude-plugin/plugin.json`)",
    "This is the one framework keyed off file shape rather than an import statement.",
]


def triage_skill_clause_problems(text):
    """Clauses missing from the triage "skill" exception sentence (anchor to end
    of its line), so a clause surviving elsewhere in triage.md does not count."""
    try:
        start = text.index(TRIAGE_SKILL_ANCHOR)
    except ValueError:
        return list(TRIAGE_SKILL_CLAUSES)
    end = text.find("\n", start)
    sentence = text[start:] if end == -1 else text[start:end]
    return missing_clauses(sentence, TRIAGE_SKILL_CLAUSES)


def _replace_in_row(text, agent, old, new):
    """Replace `old` with `new` on the single table row whose agent is `agent`."""
    out = []
    for line in text.splitlines(keepends=True):
        if line.startswith("|") and ("| `%s` |" % agent) in line:
            line = line.replace(old, new)
        out.append(line)
    return "".join(out)


def _row_line(text, agent):
    for line in text.splitlines(keepends=True):
        if line.startswith("|") and ("| `%s` |" % agent) in line:
            return line
    raise ValueError("no row for %s" % agent)


# --------------------------------------------------------------------------- #
# GATE-02 live locks
# --------------------------------------------------------------------------- #
class TestSelectionRows(unittest.TestCase):
    def test_selection_rows_counts(self):
        review = selection_rows(read(REVIEW_DISPATCH), REVIEW_TABLE_HEADING)
        deep = selection_rows(read(DEEP_SELECTION))
        self.assertEqual(len(review), 15)
        self.assertEqual(len(deep), 18)
        self.assertEqual(sum(r[2] == "framework-skill" for r in review), 1)
        self.assertEqual(sum(r[2] == "framework-skill" for r in deep), 1)

    def test_selection_rows_rejects_bad_cell_count(self):
        bad = "| Always | Condition |\n|---|---|\n| ✓ | — |\n"
        with self.assertRaises(ValueError):
            selection_rows(bad)

    def test_selection_rows_rejects_unbackticked_agent(self):
        bad = "| Always | Condition | Agent |\n|---|---|---|\n| ✓ | — | bugs |\n"
        with self.assertRaises(ValueError):
            selection_rows(bad)

    def test_selection_rows_rejects_odd_always_mark(self):
        bad = "| Always | Condition | Agent |\n|---|---|---|\n| x | — | `bugs` |\n"
        with self.assertRaises(ValueError):
            selection_rows(bad)


class TestGoldenPin(unittest.TestCase):
    def test_review_table_matches_golden(self):
        rows = selection_rows(read(REVIEW_DISPATCH), REVIEW_TABLE_HEADING)
        self.assertEqual(tuple(rows), EXPECTED_REVIEW_ROWS)

    def test_deep_table_matches_golden(self):
        self.assertEqual(tuple(selection_rows(read(DEEP_SELECTION))), EXPECTED_DEEP_ROWS)

    def test_deep_golden_keeps_test_sufficiency_always_on(self):
        ts = [r for r in EXPECTED_DEEP_ROWS if r[2] == "test-sufficiency"]
        self.assertEqual(ts, [(True, "—", "test-sufficiency", "opus (frontmatter)")])


class TestSkillRule(unittest.TestCase):
    def test_review_skill_rule(self):
        rows = selection_rows(read(REVIEW_DISPATCH), REVIEW_TABLE_HEADING)
        self.assertEqual(skill_rule_problems(rows, require_triage_phrase=True), [])

    def test_deep_skill_rule(self):
        rows = selection_rows(read(DEEP_SELECTION))
        self.assertEqual(skill_rule_problems(rows, require_triage_phrase=False), [])


class TestTriageClause(unittest.TestCase):
    def test_triage_skill_clause(self):
        self.assertEqual(triage_skill_clause_problems(read(TRIAGE)), [])


# --------------------------------------------------------------------------- #
# GATE-02 mutations
# --------------------------------------------------------------------------- #
class TestSkillRuleMutation(unittest.TestCase):
    def setUp(self):
        self.review = read(REVIEW_DISPATCH)
        self.deep = read(DEEP_SELECTION)

    def _review(self, text):
        return skill_rule_problems(selection_rows(text, REVIEW_TABLE_HEADING), True)

    def _deep(self, text):
        return skill_rule_problems(selection_rows(text), False)

    def test_marked_always_trips(self):
        for original, check in ((self.review, self._review), (self.deep, self._deep)):
            planted = _replace_in_row(original, "framework-skill", "|  |", "| ✓ |")
            self.assertNotEqual(planted, original)
            self.assertIn("framework-skill marked Always", check(planted))

    def test_token_renamed_trips(self):
        for original, check in ((self.review, self._review), (self.deep, self._deep)):
            planted = _replace_in_row(original, "framework-skill", SKILL_TOKEN, '"skills"')
            self.assertNotEqual(planted, original)
            self.assertIn('framework-skill condition lacks "skill"', check(planted))

    def test_row_deleted_trips(self):
        for original, check in ((self.review, self._review), (self.deep, self._deep)):
            planted = original.replace(_row_line(original, "framework-skill"), "")
            self.assertNotEqual(planted, original)
            self.assertEqual(check(planted), ["missing framework-skill row"])

    def test_row_duplicated_trips(self):
        for original, check in ((self.review, self._review), (self.deep, self._deep)):
            line = _row_line(original, "framework-skill")
            planted = original.replace(line, line + line)
            self.assertNotEqual(planted, original)
            self.assertIn("duplicate framework-skill row", check(planted))

    def test_token_leak_trips(self):
        planted = _replace_in_row(self.review, "framework-react", '"react"', '"react" or "skill"')
        self.assertNotEqual(planted, self.review)
        self.assertEqual(self._review(planted), ['"skill" leaked into framework-react condition'])
        planted = _replace_in_row(self.deep, "framework-react", "React imports",
                                  'React imports or "skill"')
        self.assertNotEqual(planted, self.deep)
        self.assertEqual(self._deep(planted), ['"skill" leaked into framework-react condition'])

    def test_review_triage_phrase_dropped_trips(self):
        planted = _replace_in_row(self.review, "framework-skill", SKILL_TRIAGE_PHRASE, SKILL_TOKEN)
        self.assertNotEqual(planted, self.review)
        self.assertEqual(self._review(planted),
                         ["framework-skill condition lacks 'triage.frameworks includes \"skill\"'"])


class TestGoldenPinMutation(unittest.TestCase):
    def setUp(self):
        self.review = read(REVIEW_DISPATCH)
        self.deep = read(DEEP_SELECTION)

    def test_review_language_go_condition_changed(self):
        planted = _replace_in_row(self.review, "language-go", "any `.go` in diff",
                                  "any `.go` or `.mod` in diff")
        self.assertNotEqual(planted, self.review)
        self.assertNotEqual(tuple(selection_rows(planted, REVIEW_TABLE_HEADING)),
                            EXPECTED_REVIEW_ROWS)

    def test_deep_language_go_condition_changed(self):
        planted = _replace_in_row(self.deep, "language-go", "Go in diff", "Go or go.mod in diff")
        self.assertNotEqual(planted, self.deep)
        self.assertNotEqual(tuple(selection_rows(planted)), EXPECTED_DEEP_ROWS)

    def test_bugs_always_blanked(self):
        planted = _replace_in_row(self.review, "bugs", "| ✓ |", "|  |")
        self.assertNotEqual(planted, self.review)
        self.assertNotEqual(tuple(selection_rows(planted, REVIEW_TABLE_HEADING)),
                            EXPECTED_REVIEW_ROWS)
        planted = _replace_in_row(self.deep, "bugs", "| ✓ |", "|  |")
        self.assertNotEqual(planted, self.deep)
        self.assertNotEqual(tuple(selection_rows(planted)), EXPECTED_DEEP_ROWS)

    def test_deep_test_sufficiency_made_conditional(self):
        planted = _replace_in_row(self.deep, "test-sufficiency", "| ✓ |", "|  |")
        self.assertNotEqual(planted, self.deep)
        self.assertNotEqual(tuple(selection_rows(planted)), EXPECTED_DEEP_ROWS)


class TestTriageClauseMutation(unittest.TestCase):
    def test_skill_md_subclause_deleted(self):
        original = read(TRIAGE)
        planted = original.replace("a file named `SKILL.md`, ", "")
        self.assertNotEqual(planted, original)
        self.assertEqual(triage_skill_clause_problems(planted), ["a file named `SKILL.md`"])


if __name__ == "__main__":
    unittest.main()
