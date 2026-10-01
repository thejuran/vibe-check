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


# --------------------------------------------------------------------------- #
# GATE-01: diff-mode coverage gate prose
# --------------------------------------------------------------------------- #
CASES = coverage_gate.CASES
GATED_CASES = coverage_gate.CASES[1:]

INVOCATION = 'python3 "$VC_ROOT/scripts/coverage_gate.py"'
EMPTY_CASE_ANCHOR = "**EMPTY CASE (D-02).**"
GATE_01D_ANCHOR = "**DIFF-MODE COVERAGE GATE ("
CHUNK_SCOPING_ANCHOR = "**`--all` CHUNK SCOPING"
RESET_CLAUSE = ("`$TS_GATE_CASE` and `$TS_GATED` both start UNSET at the beginning of "
                "every invocation and every pass")

DISABLED_ANCHOR = "**Subtract `$CONFIG_DISABLED`"
GATE_SEL_ANCHOR = "**DIFF-MODE COVERAGE GATE — remove"
TOP_TIER_ANCHOR = "**Why the top tier"

ANNOUNCE_SUFFIX = {
    coverage_gate.CASES[1]: "test-sufficiency not dispatched: no coverage artifact found",
    coverage_gate.CASES[2]: "test-sufficiency not dispatched: coverage artifacts found, "
                            "none usable for the changed files",
}

RENDER_ANCHOR = "If `$TS_GATED` is set"
NOTE_PREFIX = "no coverage data available, skipped"

_SLUG_SHAPED = re.compile(r"`([a-z]+-[a-z]+)`")
_BACKTICKED = re.compile(r"`([^`]*)`")


def _between(text, start_anchor, end_anchor):
    """Text from `start_anchor` up to (not including) `end_anchor`; "" if absent."""
    try:
        start = text.index(start_anchor)
        end = text.index(end_anchor, start)
    except ValueError:
        return ""
    return text[start:end]


def gate_call_problems(text_01d, text_dispatch, text_dispatch_all):
    """Problems with the single coverage_gate.py invocation and its paragraph."""
    problems = []
    if text_01d.count(INVOCATION) != 1:
        problems.append("invocation count != 1")
    if not _ordered(text_01d, EMPTY_CASE_ANCHOR, INVOCATION, CHUNK_SCOPING_ANCHOR):
        problems.append("invocation not between EMPTY CASE and --all CHUNK SCOPING")
    if "coverage_gate" in text_dispatch:
        problems.append("coverage_gate mentioned in 20-dispatch.md")
    if "coverage_gate" in text_dispatch_all:
        problems.append("coverage_gate mentioned in 20-dispatch-all.md")
    para = norm(_between(text_01d, GATE_01D_ANCHOR, CHUNK_SCOPING_ANCHOR))
    if "$ALL_MODE" not in para:
        problems.append("gate paragraph missing $ALL_MODE guard")
    if "dispatches as before" not in para:
        problems.append("gate paragraph lacks fail-toward-dispatch sentence")
    if norm(RESET_CLAUSE) not in para:
        problems.append("gate paragraph lacks UNSET reset clause")
    return problems


def selection_gate_problems(text_sel):
    """Problems with the selection-time gating paragraph in 20-selection.md."""
    problems = []
    if not _ordered(text_sel, DISABLED_ANCHOR, GATE_SEL_ANCHOR, TOP_TIER_ANCHOR):
        problems.append("gating paragraph not after $CONFIG_DISABLED paragraph")
    for always, condition, agent, _model in selection_rows(text_sel):
        if agent == "test-sufficiency" and (not always or condition != "—"):
            problems.append("test-sufficiency row is not always-on")
    raw = _between(text_sel, GATE_SEL_ANCHOR, TOP_TIER_ANCHOR)
    para = norm(raw)
    if "$TS_GATED=" not in para:
        problems.append("gating paragraph does not bind $TS_GATED in the removal step")
    if "$CONFIG_DISABLED" not in para or "stays unset" not in para:
        problems.append("gating paragraph lacks disabled-wins clause")
    for slug in GATED_CASES:
        if "`%s`" % slug not in para:
            problems.append("gating paragraph does not name %s" % slug)
        if norm(ANNOUNCE_SUFFIX[slug]) not in para:
            problems.append("gating paragraph lacks announce suffix for %s" % slug)
    for token in _SLUG_SHAPED.findall(raw):
        if token.endswith(("-artifact", "-usable")) and token not in CASES:
            problems.append("gating paragraph names an unknown slug %s" % token)
    if "$ALL_MODE" not in para:
        problems.append("gating paragraph lacks --all exclusion")
    return problems


def _render_paragraph(text_cmd):
    try:
        start = text_cmd.index(RENDER_ANCHOR)
    except ValueError:
        return ""
    end = text_cmd.find("\n\n", start)
    return norm(text_cmd[start:] if end == -1 else text_cmd[start:end])


def render_note_problems(text_cmd):
    """Problems with the fixed Test Coverage notes in the Phase 4 render paragraph.

    Each gated slug must be paired ("for `<slug>`, `<note>`") with exactly one
    backticked note that starts with the agent's own skip note.
    """
    problems = []
    para = _render_paragraph(text_cmd)
    for slug in GATED_CASES:
        pair = re.compile(r"for `%s`, `%s \([^`]*\)`" % (re.escape(slug), re.escape(NOTE_PREFIX)))
        hits = len(pair.findall(para))
        if hits == 0:
            problems.append("render note missing for %s" % slug)
        elif hits > 1:
            problems.append("render note duplicated for %s" % slug)
    for literal in _BACKTICKED.findall(para):
        if "skipped (" in literal and not literal.startswith(NOTE_PREFIX):
            problems.append("render note does not start with the agent's literal note")
            break
    if "inert display text" not in para:
        problems.append("inert display text sentence dropped")
    return problems


def phase2_skip_lines(texts):
    """`<relpath>: <line>` for every line tracecheck would read as a Phase 2 skip."""
    hits = []
    for relpath, text in texts.items():
        for m in tracecheck.ANNOUNCE_RE.finditer(text):
            if m.group(1) == tracecheck.SKIP_MARK and m.group(2) == "2":
                # The regex's leading class can swallow newlines, so locate the
                # line from the mark itself, not from the match start.
                line_start = text.rfind("\n", 0, m.start(1)) + 1
                line_end = text.find("\n", m.start(1))
                line = text[line_start:] if line_end == -1 else text[line_start:line_end]
                hits.append("%s: %s" % (relpath, line.strip()))
    return hits


SKIP_LINE_CORPUS = (DEEP_COVERAGE, DEEP_SELECTION, DEEP_COMMAND, REVIEW_DISPATCH)


def _corpus():
    return {rel: read(rel) for rel in SKIP_LINE_CORPUS}


# --------------------------------------------------------------------------- #
# GATE-01 live locks
# --------------------------------------------------------------------------- #
class TestSlugVocabulary(unittest.TestCase):
    def test_cases_are_the_sealed_tuple(self):
        self.assertEqual(coverage_gate.CASES[1:], ("no-artifact", "none-usable"))

    def test_slug_literals_appear_only_in_the_pin(self):
        with open(os.path.join(HERE, "test_lane_gating.py"), encoding="utf-8") as fh:
            src = fh.read()
        for slug in GATED_CASES:
            self.assertEqual(src.count('"' + slug + '"'), 1, slug)


class TestGateCall(unittest.TestCase):
    def test_gate_call(self):
        self.assertEqual(gate_call_problems(read(DEEP_COVERAGE), read(REVIEW_DISPATCH),
                                            read(REVIEW_DISPATCH_ALL)), [])


class TestSelectionGate(unittest.TestCase):
    def test_selection_gate(self):
        self.assertEqual(selection_gate_problems(read(DEEP_SELECTION)), [])


class TestRenderNote(unittest.TestCase):
    def test_render_note(self):
        self.assertEqual(render_note_problems(read(DEEP_COMMAND)), [])


class TestPhase2SkipLine(unittest.TestCase):
    def test_no_phase2_skip_line(self):
        self.assertEqual(phase2_skip_lines(_corpus()), [])


class TestEmptyCases(unittest.TestCase):
    """Both empty cases carry all three outputs: removal, announce, note."""

    def test_each_empty_case(self):
        para = norm(_between(read(DEEP_SELECTION), GATE_SEL_ANCHOR, TOP_TIER_ANCHOR))
        render = render_note_problems(read(DEEP_COMMAND))
        self.assertIn("REMOVE `test-sufficiency`", para)
        for slug in GATED_CASES:
            with self.subTest(slug=slug):
                self.assertIn("`%s`" % slug, para)
                self.assertIn(norm(ANNOUNCE_SUFFIX[slug]), para)
                self.assertFalse([p for p in render if p.endswith(" " + slug)])

    def test_disabled_and_empty(self):
        text = read(DEEP_SELECTION)
        para = norm(_between(text, GATE_SEL_ANCHOR, TOP_TIER_ANCHOR))
        self.assertIn("$CONFIG_DISABLED", para)
        self.assertIn("stays unset", para)
        self.assertEqual(text.count("$TS_GATED="), 1)
        self.assertFalse([r for r in selection_rows(text) if "coverage" in r[1].lower()])


# --------------------------------------------------------------------------- #
# GATE-01 mutations
# --------------------------------------------------------------------------- #
class TestGateCallMutation(unittest.TestCase):
    def setUp(self):
        self.d01 = read(DEEP_COVERAGE)
        self.dispatch = read(REVIEW_DISPATCH)
        self.dispatch_all = read(REVIEW_DISPATCH_ALL)

    def _check(self, d01=None, dispatch_all=None):
        return gate_call_problems(d01 if d01 is not None else self.d01, self.dispatch,
                                  dispatch_all if dispatch_all is not None else self.dispatch_all)

    def _in_para(self, old, new):
        para = _between(self.d01, GATE_01D_ANCHOR, CHUNK_SCOPING_ANCHOR)
        return self.d01.replace(para, para.replace(old, new))

    def test_invocation_deleted(self):
        planted = self.d01.replace(INVOCATION, "true")
        self.assertNotEqual(planted, self.d01)
        self.assertIn("invocation count != 1", self._check(d01=planted))

    def test_invocation_duplicated(self):
        planted = self.d01.replace(INVOCATION, INVOCATION + " || " + INVOCATION)
        self.assertNotEqual(planted, self.d01)
        self.assertIn("invocation count != 1", self._check(d01=planted))

    def test_invocation_moved_after_chunk_scoping(self):
        planted = self.d01.replace(INVOCATION, "true")
        planted = planted.replace(CHUNK_SCOPING_ANCHOR, CHUNK_SCOPING_ANCHOR + " " + INVOCATION)
        self.assertNotEqual(planted, self.d01)
        self.assertEqual(self._check(d01=planted),
                         ["invocation not between EMPTY CASE and --all CHUNK SCOPING"])

    def test_mentioned_in_dispatch_all(self):
        planted = self.dispatch_all + "\nRun coverage_gate here.\n"
        self.assertNotEqual(planted, self.dispatch_all)
        self.assertEqual(self._check(dispatch_all=planted),
                         ["coverage_gate mentioned in 20-dispatch-all.md"])

    def test_all_mode_guard_removed(self):
        planted = self._in_para("$ALL_MODE", "$MODE")
        self.assertNotEqual(planted, self.d01)
        self.assertEqual(self._check(d01=planted), ["gate paragraph missing $ALL_MODE guard"])

    def test_fail_toward_dispatch_removed(self):
        planted = self._in_para("dispatches as before", "is skipped")
        self.assertNotEqual(planted, self.d01)
        self.assertEqual(self._check(d01=planted),
                         ["gate paragraph lacks fail-toward-dispatch sentence"])

    def test_reset_clause_removed(self):
        planted = self._in_para(RESET_CLAUSE, "`$TS_GATE_CASE` is carried")
        self.assertNotEqual(planted, self.d01)
        self.assertEqual(self._check(d01=planted), ["gate paragraph lacks UNSET reset clause"])


class TestSelectionGateMutation(unittest.TestCase):
    def setUp(self):
        self.sel = read(DEEP_SELECTION)
        self.para = _between(self.sel, GATE_SEL_ANCHOR, TOP_TIER_ANCHOR)

    def _in_para(self, old, new):
        return self.sel.replace(self.para, self.para.replace(old, new))

    def test_paragraph_moved_before_disabled(self):
        without = self.sel.replace(self.para, "")
        planted = without.replace(DISABLED_ANCHOR, self.para + DISABLED_ANCHOR)
        self.assertNotEqual(planted, self.sel)
        self.assertIn("gating paragraph not after $CONFIG_DISABLED paragraph",
                      selection_gate_problems(planted))

    def test_slug_renamed(self):
        planted = self._in_para("`%s`" % GATED_CASES[1], "`part-usable`")
        self.assertNotEqual(planted, self.sel)
        problems = selection_gate_problems(planted)
        self.assertIn("gating paragraph does not name %s" % GATED_CASES[1], problems)
        self.assertIn("gating paragraph names an unknown slug part-usable", problems)

    def test_all_mode_exclusion_removed(self):
        planted = self._in_para("$ALL_MODE", "$MODE")
        self.assertNotEqual(planted, self.sel)
        self.assertEqual(selection_gate_problems(planted), ["gating paragraph lacks --all exclusion"])


class TestEmptyCaseMutation(unittest.TestCase):
    def setUp(self):
        self.sel = read(DEEP_SELECTION)
        self.para = _between(self.sel, GATE_SEL_ANCHOR, TOP_TIER_ANCHOR)

    def _in_para(self, old, new):
        return self.sel.replace(self.para, self.para.replace(old, new))

    def test_row_made_conditional(self):
        planted = _replace_in_row(self.sel, "test-sufficiency", "| ✓ |", "|  |")
        self.assertNotEqual(planted, self.sel)
        self.assertEqual(selection_gate_problems(planted), ["test-sufficiency row is not always-on"])

    def test_no_artifact_suffix_deleted(self):
        slug = GATED_CASES[0]
        planted = self._in_para(ANNOUNCE_SUFFIX[slug], "")
        self.assertNotEqual(planted, self.sel)
        self.assertEqual(selection_gate_problems(planted),
                         ["gating paragraph lacks announce suffix for %s" % slug])

    def test_none_usable_suffix_deleted(self):
        slug = GATED_CASES[1]
        planted = self._in_para(ANNOUNCE_SUFFIX[slug], "")
        self.assertNotEqual(planted, self.sel)
        self.assertEqual(selection_gate_problems(planted),
                         ["gating paragraph lacks announce suffix for %s" % slug])

    def test_binding_deleted(self):
        planted = self._in_para("$TS_GATED=", "$TS_GATED ")
        self.assertNotEqual(planted, self.sel)
        self.assertEqual(selection_gate_problems(planted),
                         ["gating paragraph does not bind $TS_GATED in the removal step"])

    def test_disabled_wins_clause_dropped(self):
        planted = self._in_para("stays unset", "is set")
        self.assertNotEqual(planted, self.sel)
        self.assertEqual(selection_gate_problems(planted),
                         ["gating paragraph lacks disabled-wins clause"])


class TestRenderNoteMutation(unittest.TestCase):
    def setUp(self):
        self.cmd = read(DEEP_COMMAND)
        para = _render_paragraph(self.cmd)
        slug = GATED_CASES[0]
        m = re.search(r"for `%s`, (`[^`]*`)" % re.escape(slug), para)
        self.slug = slug
        self.note = m.group(1)
        self.pair = "for `%s`, %s" % (slug, self.note)

    def test_note_deleted(self):
        planted = self.cmd.replace(self.note, "")
        self.assertNotEqual(planted, self.cmd)
        self.assertEqual(render_note_problems(planted), ["render note missing for %s" % self.slug])

    def test_note_duplicated(self):
        planted = self.cmd.replace(self.pair, self.pair + "; " + self.pair)
        self.assertNotEqual(planted, self.cmd)
        self.assertEqual(render_note_problems(planted),
                         ["render note duplicated for %s" % self.slug])

    def test_prefix_changed(self):
        planted = self.cmd.replace(self.note, self.note.replace(NOTE_PREFIX, "coverage skipped"))
        self.assertNotEqual(planted, self.cmd)
        self.assertIn("render note does not start with the agent's literal note",
                      render_note_problems(planted))

    def test_inert_sentence_dropped(self):
        planted = self.cmd.replace("inert display text", "display text")
        self.assertNotEqual(planted, self.cmd)
        self.assertEqual(render_note_problems(planted), ["inert display text sentence dropped"])


class TestPhase2SkipLineMutation(unittest.TestCase):
    def test_phase2_skip_line_planted(self):
        corpus = _corpus()
        original = corpus[DEEP_SELECTION]
        planted = original + "\n⊘ Phase 2 — test-sufficiency skipped\n"
        self.assertNotEqual(planted, original)
        corpus[DEEP_SELECTION] = planted
        self.assertEqual(phase2_skip_lines(corpus),
                         [DEEP_SELECTION + ": ⊘ Phase 2 — test-sufficiency skipped"])

    def test_phase2c_line_is_not_a_phase2_skip(self):
        corpus = _corpus()
        original = corpus[DEEP_SELECTION]
        planted = original + "\n⊘ Phase 2c — Codex kickoff (skipped)\n"
        self.assertNotEqual(planted, original)
        corpus[DEEP_SELECTION] = planted
        self.assertEqual(phase2_skip_lines(corpus), [])


if __name__ == "__main__":
    unittest.main()
