"""Recovery pairs: what happens next run and what the owner can do.

Every open row that carries a `verdict: fix not …` or `verdict: confirmed fix …`
reason from score.py renders that reason plus one fixed pair from the
Recovery pairs table in phases/review/40-render.md:

    Next run: <what the next run does on its own>
    You can:  <one or two bounded actions, by number>

This file locks the table to the score.py reason constants, so the guidance
never disagrees with the code:
  - every such constant has exactly one row, keyed by its exact literal;
  - "retried" (or retry/retries) appears only for the reasons the code
    actually re-asks on a later run: no eligible reviewer, no answer, and a
    snapshot mismatch. A reviewer's still-applies answer, an unchanged file
    (no trigger) and an unchanged Needs-verification item are not retried
    until their code changes;
  - no row and no Needs-verification suffix sends the owner to /deep-review:
    a run with nothing new to review dispatches no reviewer under either
    command;
  - the README limitation bullet and the output template say the same.
"""

import os
import re
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import score  # noqa: E402
from test_verified_fixes import NV_RENDER_LINE  # noqa: E402

PLUGIN_DIR = os.path.normpath(os.path.join(HERE, ".."))
README = os.path.normpath(os.path.join(PLUGIN_DIR, "..", "..", "README.md"))
RENDER_MD = "phases/review/40-render.md"
OUTPUT_MD = "templates/output-format.md"

MARKER = "**Recovery pairs (D-13).**"
PREFIXES = ("verdict: fix not", "verdict: confirmed fix")
EXCLUDED = ("_R_ROUTED_ORPHAN", "_R_CONTRADICTED")
RETRY_RE = re.compile(r"\bretr(y|ied|ies)\b", re.IGNORECASE)
RETRYING_NAMES = ("_R_IR_NO_REVIEWER", "_R_IR_NO_ANSWER", "_R_IR_SNAPSHOT",
                  "_R_CF_NO_REVIEWER", "_R_CF_NO_ANSWER", "_R_CF_SNAPSHOT")
# getattr, not a literal copy: a renamed constant fails loudly here.
RETRYING = frozenset(getattr(score, n) for n in RETRYING_NAMES)

NV_SUFFIX = ("code changed since last pass; Fix not yet confirmed: no eligible "
             "reviewer ran this pass — Next run: retried automatically on the "
             "next review of new changes. You can: commit further work and "
             "re-run, or dismiss/defer it by number")
CF_STAYS_OPEN = "The row stays in the section — it is still open."
IR_STAYS_OPEN = "The row stays in its section — it is still open."
TABLE_RULE = "the pair for that reason from the table below"
README_NEW = "every later run that reviews changes"
README_OLD = "gets **one** automatic independent re-check"
OLD_TAIL = "retried on the next run that reviews changes"
# 40-render.md has exactly these heading lines; the table lives inside an
# existing rule, never under a new manual section.
RENDER_HEADING_LINES = 4


def _read(rel):
    with open(os.path.join(PLUGIN_DIR, rel), "r", encoding="utf-8") as fh:
        return fh.read()


def _read_readme():
    with open(README, "r", encoding="utf-8") as fh:
        return fh.read()


def reasons(mod=score):
    """Every score.py reason a recovery pair must exist for."""
    return [v for k, v in vars(mod).items()
            if k.startswith("_R_") and isinstance(v, str) and v.startswith(PREFIXES)]


def pairs_table(text):
    """Parse the Recovery pairs table into [(reason, next_run, you_can)].

    None when the marker is missing. The table is the run of `| `verdict: …`
    rows after the marker; it ends at the first blank line after a row."""
    i = text.find(MARKER)
    if i < 0:
        return None
    rows = []
    started = False
    for line in text[i + len(MARKER):].splitlines():
        s = line.strip()
        if s.startswith("|"):
            started = True
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) != 3 or not cells[0].startswith("`verdict: "):
                continue
            rows.append((cells[0].strip("`"), cells[1], cells[2]))
        elif started and not s:
            break
    return rows


def coverage_problems(rows, wanted):
    """Every wanted reason has exactly one row, keyed by its exact literal,
    and nothing else is in the table."""
    if rows is None:
        return ["marker not found: " + MARKER]
    problems = []
    keys = [r[0] for r in rows]
    for reason in wanted:
        n = keys.count(reason)
        if n != 1:
            problems.append("%d rows for %r" % (n, reason))
    for k in keys:
        if k not in wanted:
            problems.append("row for unknown reason %r" % k)
    return problems


def cell_problems(rows):
    """Every Next run cell says something; every You can cell is one or two
    bounded actions and offers a by-number decision."""
    if rows is None:
        return ["marker not found: " + MARKER]
    problems = []
    for reason, nxt, can in rows:
        if not nxt.startswith("Next run: ") or len(nxt) <= len("Next run: ") + 3:
            problems.append("empty Next run for %r" % reason)
        if not can.startswith("You can: "):
            problems.append("no You can for %r" % reason)
        if "by number" not in can:
            problems.append("You can names no by-number action for %r" % reason)
        if len(can.split(", or ")) > 2:
            problems.append("more than two actions for %r" % reason)
    return problems


def honesty_problems(rows, retrying=RETRYING):
    """The retry word appears iff the code retries the reason; no cell
    promises /deep-review."""
    if rows is None:
        return ["marker not found: " + MARKER]
    problems = []
    for reason, nxt, can in rows:
        says_retry = bool(RETRY_RE.search(nxt + " " + can))
        if says_retry != (reason in retrying):
            problems.append("retry word %s for %r" % (
                "present" if says_retry else "missing", reason))
        if "deep-review" in nxt + can:
            problems.append("/deep-review promised for %r" % reason)
    return problems


def nv_row_problems(rows):
    if rows is None:
        return ["marker not found: " + MARKER]
    nv = [r for r in rows if r[0] == score._R_IR_NV_NO_CHANGE]
    if len(nv) != 1 or NV_RENDER_LINE not in nv[0][1]:
        return ["NV_NO_CHANGE row does not carry the stays-open sentence"]
    return []


def all_problems(text, mod=score):
    rows = pairs_table(text)
    return (coverage_problems(rows, reasons(mod)) + cell_problems(rows)
            + honesty_problems(rows) + nv_row_problems(rows))


def _row_line(text, reason):
    for line in text.splitlines():
        if line.startswith("| `" + reason + "`"):
            return line
    raise AssertionError("no row for " + reason)


class TestReasonInventory(unittest.TestCase):
    """The collector finds the 12 rendered reasons and nothing else."""

    def test_twelve_reasons(self):
        got = reasons()
        self.assertEqual(len(got), 12, got)
        self.assertEqual(len(set(got)), 12)

    def test_other_verdicts_excluded(self):
        got = reasons()
        for name in EXCLUDED:
            self.assertNotIn(getattr(score, name), got, name)

    def test_retrying_is_a_subset(self):
        self.assertEqual(len(RETRYING), 6)
        self.assertTrue(RETRYING <= set(reasons()))


class TestPairsCoverage(unittest.TestCase):
    """One row per reason, exact literal, both cells well formed."""

    def setUp(self):
        self.rows = pairs_table(_read(RENDER_MD))

    def test_every_reason_has_one_row(self):
        self.assertEqual(coverage_problems(self.rows, reasons()), [])

    def test_cells_well_formed(self):
        self.assertEqual(cell_problems(self.rows), [])

    def test_nv_row_keeps_stays_open_sentence(self):
        self.assertEqual(nv_row_problems(self.rows), [])

    def test_rules_point_at_the_table(self):
        text = _read(RENDER_MD)
        self.assertEqual(text.count(TABLE_RULE), 2)


class TestRetryHonesty(unittest.TestCase):
    """Retry wording only where the code retries; no /deep-review promise."""

    def test_retry_word_iff_retrying(self):
        self.assertEqual(honesty_problems(pairs_table(_read(RENDER_MD))), [])

    def test_no_deep_review_promise_anywhere(self):
        for rel in (RENDER_MD, OUTPUT_MD):
            with self.subTest(file=rel):
                text = _read(rel)
                self.assertNotIn("run /deep-review", text)
                self.assertNotIn(OLD_TAIL, text)


class TestReconciled(unittest.TestCase):
    """README, NV suffix and output template agree with the code."""

    def test_readme_says_every_later_run(self):
        text = _read_readme()
        self.assertTrue(README_NEW in text, "README lacks: " + README_NEW)
        self.assertFalse(README_OLD in text, "README still says: " + README_OLD)

    def test_nv_suffix_in_both_files(self):
        for rel in (RENDER_MD, OUTPUT_MD):
            with self.subTest(file=rel):
                text = _read(rel)
                self.assertIn(NV_SUFFIX, text)
                self.assertIn(NV_RENDER_LINE, text)

    def test_rows_stay_open(self):
        text = _read(RENDER_MD)
        self.assertIn(CF_STAYS_OPEN, text)
        self.assertIn(IR_STAYS_OPEN, text)

    def test_no_new_heading(self):
        text = _read(RENDER_MD)
        n = sum(1 for line in text.splitlines() if line.startswith("#"))
        self.assertEqual(n, RENDER_HEADING_LINES)


class TestLockTrips(unittest.TestCase):
    """Each named mutant of the shipped table is caught."""

    def setUp(self):
        self.text = _read(RENDER_MD)
        self.assertEqual(all_problems(self.text), [])

    def _trips(self, mutated, mod=score):
        self.assertNotEqual(mutated, self.text, "mutant did not change the text")
        self.assertNotEqual(all_problems(mutated, mod), [])

    def test_a_retried_added_to_still_row(self):
        line = _row_line(self.text, score._R_IR_STILL)
        bad = line.replace("| You can:", "It is retried next run. | You can:")
        with self.subTest(mutant="a"):
            self._trips(self.text.replace(line, bad))

    def test_b_no_trigger_row_deleted(self):
        line = _row_line(self.text, score._R_IR_NO_TRIGGER)
        with self.subTest(mutant="b"):
            self._trips(self.text.replace(line + "\n", ""))

    def test_c_synthetic_reason_has_no_row(self):
        with mock.patch.object(score, "_R_IR_SYNTHETIC",
                               "verdict: fix not confirmed: synthetic",
                               create=True):
            self.assertEqual(len(reasons()), 13)
            self.assertNotEqual(all_problems(self.text), [])

    def test_d_deep_review_added_to_you_can(self):
        line = _row_line(self.text, score._R_IR_NO_ANSWER)
        bad = line.rstrip().rstrip("|").rstrip() + " or run /deep-review |"
        with self.subTest(mutant="d"):
            self._trips(self.text.replace(line, bad))

    def test_e_marker_removed(self):
        with self.subTest(mutant="e"):
            self._trips(self.text.replace(MARKER, ""))
        self.assertIsNone(pairs_table(self.text.replace(MARKER, "")))


if __name__ == "__main__":
    unittest.main()
