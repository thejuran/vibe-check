"""Prose pins for the fix-loop card in phases/review/50-fix-loop.md.

The fix loop asks the owner ONE card per pass (Apply all & rerun / Apply
selected… / Skip & rerun / Stop here…); Apply selected… and Stop here… each
open exactly one more. Step B dispatches exactly what `batch_card.py payload`
prints, so the fix agent only ever receives the selected record's own defect.

Every assertion is on an exact literal. The no-nudge, dispatch and header
checks each carry a mutant subtest proving the check would trip.
"""

import hashlib
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_parse  # noqa: E402  (sibling module: the card labels)

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.normpath(os.path.join(HERE, ".."))
FIX_LOOP = os.path.join(PLUGIN_DIR, "phases", "review", "50-fix-loop.md")
FIX_MD = os.path.join(PLUGIN_DIR, "agents", "fix.md")

# sha256 of agents/fix.md when this lock was written. The milestone forbids
# any change to agents/*.md; the payload's fields are fix.md's existing input.
FIX_MD_SHA256 = (
    "b1c4b166e40df29d59e2b9257dea724dc88f5f0f43ded9b15b04cffbb5468869")

CARD_HEADING = "### The fix-loop card"
STEP_B_HEADING = "### Step B"
TERMINATION_HEADING = "### Loop termination guarantees"

PAUSED_REVIEW = ("Paused. Resume with `/vibe-check:review ${original_args}` "
                 "or close out later with `--finalize`.")
PAUSED_DEEP = ("Paused. Resume with `/vibe-check:deep-review "
               "${original_args}` or close out later with `--finalize`.")

ROWS_CALL = 'batch_card.py" rows --mode fix-loop'
SELECT_QUESTIONS_CALL = 'batch_card.py" select-questions --rows'
PAYLOAD_CALL = 'batch_card.py" payload --rows "$ROWSFILE" --answer "$ANSWERFILE"'
SELECT_CALL = 'batch_card.py" select --rows'

FIX_SENT_BINDING = "Bind `$FIX_SENT` = `$PAYLOADFILE`'s `sent` array"
FINDINGS_VERBATIM = "`$PAYLOADFILE`'s `findings` array, inserted verbatim"
OLD_PLACEHOLDER = "JSON array of selected findings"

CARD_HEADER = 'header "Pass {{$PASS_NUMBER}}"'
STOP_HEADER = 'header "Stop here"'
MAX_HEADER_CHARS = 12

STEP_B_NEEDLES = ("PRE_BLOBS", "POST_BLOBS", "PRE_CLEAN", "POST_CLEAN",
                  "files_touched", "record-fix-verdicts", "^[A-Za-z0-9._/-]+$")


def read_text():
    with open(FIX_LOOP, "r", encoding="utf-8") as fh:
        return fh.read()


def card_section(text):
    start = text.index(CARD_HEADING)
    return text[start:text.index(STEP_B_HEADING, start)]


def step_b_section(text):
    start = text.index(STEP_B_HEADING)
    return text[start:text.index(TERMINATION_HEADING, start)]


def nudge_count(text):
    """Occurrences of a preferred-default nudge anywhere in the file."""
    return text.count("(Recommended)") + text.count("Recommended")


def dispatch_pins_hold(text):
    """True when Step B dispatches exactly the payload output (D-10)."""
    step_b = step_b_section(text)
    card = card_section(text)
    return (FIX_SENT_BINDING in step_b
            and FINDINGS_VERBATIM in step_b
            and OLD_PLACEHOLDER not in text
            and "routed through" in card
            and "which is not being fixed" in card)


def header_value(literal):
    """The quoted header value with its {{placeholder}} parts removed."""
    value = literal.split('"', 2)[1]
    while "{{" in value:
        a = value.index("{{")
        value = value[:a] + value[value.index("}}", a) + 2:]
    return value.strip()


def headers_fit(card):
    for literal in (CARD_HEADER, STOP_HEADER):
        if card.count(literal) != 1:
            return False
        if len(header_value(literal)) > MAX_HEADER_CHARS:
            return False
    return True


LIST_IN_CARD = (
    "copy the `card_text` field of `$ROWSFILE` verbatim into the question",
    "never print it only from a shell command",
    "When `card_text_truncated` is true",
    "ALSO print the `list_text` field verbatim as message text",
)


def question_line(card):
    """The fix-loop card's **Question:** line."""
    start = card.index("> **Question:** \"Pass {{$PASS_NUMBER}}")
    return card[start:card.index("\n", start)]


def list_in_card_problems(card):
    """[] when the numbered list is carried INSIDE the card's question."""
    problems = [n for n in LIST_IN_CARD if card.count(n) != 1]
    question = question_line(card)
    for needle in ("{{card_text}}", "From your finalize answer:",
                   "<echo_text>", "listed below"):
        if needle not in question:
            problems.append("question lacks " + needle)
    if "Message text above the card" in card:
        problems.append("list printed as message text above the card")
    return problems


class TestFixLoopCard(unittest.TestCase):

    def setUp(self):
        self.text = read_text()
        self.card = card_section(self.text)

    # (a) labels
    def test_every_label_appears_in_the_prose(self):
        for label in batch_parse.FIX_LOOP_OPTIONS + batch_parse.STOP_OPTIONS:
            with self.subTest(label=label):
                self.assertIn(label, self.text)

    def test_each_card_option_is_bold_exactly_once_in_the_card(self):
        for label in batch_parse.FIX_LOOP_OPTIONS:
            with self.subTest(label=label):
                self.assertEqual(self.card.count("**%s**" % label), 1)

    # (b) one card, same-turn rule, pending rows in the message text
    def test_one_card_and_same_turn_rule(self):
        self.assertIn("ONE card", self.card)
        self.assertIn("THIS assistant turn", self.card)
        self.assertIn(
            "unchanged since pass {{pending_since}}, decision pending",
            self.card)

    # (c) no nudge anywhere, lock proven load-bearing
    def test_no_recommended_nudge_anywhere(self):
        self.assertEqual(self.text.count("(Recommended)"), 0)
        self.assertEqual(self.text.count("Recommended"), 0)
        self.assertEqual(nudge_count(self.text), 0)

    def test_no_nudge_lock_trips_on_mutant(self):
        mutant = self.text.replace("**Apply all & rerun**",
                                   "**Apply all & rerun (Recommended)**", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertGreater(nudge_count(mutant), 0)

    # (d) section shape
    def test_old_menus_gone_and_step_b_kept(self):
        self.assertNotIn("### Step A", self.text)
        self.assertNotIn("### Step C", self.text)
        self.assertEqual(self.text.count("### Step B"), 1)
        self.assertEqual(self.text.count(CARD_HEADING), 1)

    # (e) Step B needles
    def test_step_b_needles_present(self):
        step_b = step_b_section(self.text)
        for needle in STEP_B_NEEDLES:
            with self.subTest(needle=needle):
                self.assertIn(needle, step_b)

    # (f) Paused. lines
    def test_paused_lines_exactly_once(self):
        self.assertEqual(self.text.count(PAUSED_REVIEW), 1)
        self.assertEqual(self.text.count(PAUSED_DEEP), 1)

    # (g) helper calls; payload is the one dispatch source
    def test_helper_calls(self):
        self.assertEqual(self.text.count(ROWS_CALL), 1)
        self.assertEqual(self.text.count(SELECT_QUESTIONS_CALL), 1)
        self.assertEqual(self.text.count(PAYLOAD_CALL), 1)
        self.assertNotIn(SELECT_CALL, self.text)

    # (g2) payload dispatch pins (Codex CRITICAL 2), with mutants
    def test_dispatch_is_the_payload_output(self):
        self.assertTrue(dispatch_pins_hold(self.text))

    def test_dispatch_pins_trip_on_old_placeholder(self):
        mutant = self.text.replace(FINDINGS_VERBATIM, OLD_PLACEHOLDER, 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(dispatch_pins_hold(mutant))

    def test_dispatch_pins_trip_on_every_row_binding(self):
        mutant = self.text.replace(
            FIX_SENT_BINDING, "Bind `$FIX_SENT` = every row's `stable_hash`", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(dispatch_pins_hold(mutant))

    # (g3) agents/fix.md untouched
    def test_fix_md_unchanged(self):
        with open(FIX_MD, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(digest, FIX_MD_SHA256)

    # (h) banned literals
    def test_no_fall_through_and_no_decision_writer(self):
        self.assertNotIn("|| { :", self.text)
        self.assertNotIn("record-decisions", self.text)

    # (i) card budget
    def test_card_budget_sentence(self):
        self.assertEqual(self.text.count("A pass costs one card"), 1)

    # (j) card headers, with a length mutant
    def test_card_headers_pinned_and_short(self):
        self.assertEqual(self.card.count(CARD_HEADER), 1)
        self.assertEqual(self.card.count(STOP_HEADER), 1)
        self.assertTrue(headers_fit(self.card))

    def test_header_length_check_trips_on_mutant(self):
        mutant = self.card.replace(STOP_HEADER,
                                   'header "Stop here and choose"', 1)
        self.assertNotEqual(mutant, self.card)
        self.assertFalse(headers_fit(mutant))
        self.assertGreater(len(header_value('header "Stop here and choose"')),
                           MAX_HEADER_CHARS)

    # (k) stale rows render in the card
    def test_stale_suffix_in_card(self):
        self.assertEqual(
            self.card.count("code changed since your decision on pass"), 1)
        self.assertIn('stale.via == "same_hash"', self.card)
        self.assertIn('stale.via == "successor"', self.card)

    # Typed mode (more than 16 rows) is a single-select with two exclusive
    # buttons; the typed list arrives through Other.
    def test_typed_mode_buttons(self):
        self.assertIn('"All listed"', self.card)
        self.assertIn('"None — skip & rerun"', self.card)
        self.assertIn("arrive through \"Other\"", self.card)

    # A Finalize-routed subset is consumed once: cleared before every rerun.
    def test_subset_cleared_before_rerun(self):
        rerun = self.card[self.card.index("**The Rerun.**"):]
        clear = 'rm -f "$SUBSETFILE"; unset SUBSETFILE'
        self.assertIn(clear, rerun)
        self.assertLess(rerun.index(clear), rerun.index("loop back to Phase 0"))


    # (l) the numbered list is carried IN the card (D1: text inside a Bash
    # call's output is collapsed by the terminal and never seen)
    def test_list_lives_in_the_card_question(self):
        self.assertEqual(list_in_card_problems(self.card), [])

    def test_list_in_card_trips_on_mutants(self):
        question = question_line(self.card)
        with self.subTest("mutant: card_text dropped from the question"):
            mutant = self.card.replace(
                question, question.replace("{{card_text}}", ""), 1)
            self.assertNotEqual(list_in_card_problems(mutant), [])
        with self.subTest("mutant: finalize echo dropped"):
            mutant = self.card.replace(
                question, question.replace("<echo_text>", ""), 1)
            self.assertNotEqual(list_in_card_problems(mutant), [])
        with self.subTest("mutant: back to a list printed above the card"):
            mutant = self.card + "\n**Message text above the card.** Print"
            self.assertNotEqual(list_in_card_problems(mutant), [])
        with self.subTest("mutant: verbatim-copy rule removed"):
            mutant = self.card.replace(LIST_IN_CARD[0], "render the list", 1)
            self.assertNotEqual(list_in_card_problems(mutant), [])

if __name__ == "__main__":
    unittest.main()
