"""Prose locks for the finalize card in phases/shared/90-finalize.md and the
REVIEW.md rendering rules in templates/review-md-schema.md.

Finalize asks the owner ONE card (two questions: what to do, and one reason)
for every undecided finding. The rows, the parse of the answer, the
record-decisions payload and the fix subset all come from `batch_card.py`;
the prose only renders and routes. These tests pin that shape.

Every lock is a check function that returns a list of problems. Each one is
applied to the real text (must return []) AND to a mutant of it (must return
something), so no lock is decorative: a check that cannot trip fails here.
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_card  # noqa: E402  (sibling module: KNOWN_FLAGS, build_rows)
import batch_parse  # noqa: E402  (sibling module: the card labels)
import carry_state  # noqa: E402  (sibling module: KNOWN_FLAGS)
from test_batch_card import HB, successor_state  # noqa: E402
from test_pause_batching import FINALIZE_MD, PINS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.normpath(os.path.join(HERE, ".."))
SCHEMA_MD = "templates/review-md-schema.md"

CARD_HEADING = "### The finalize card"
RECORDING_HEADING = "### Recording decisions"
WRITING_HEADING = "### Writing REVIEW.md"

ALL_KNOWN_FLAGS = batch_card.KNOWN_FLAGS + carry_state.KNOWN_FLAGS

ROWS_CALL = 'batch_card.py" rows --mode finalize --head-blobs "$BLOBFILE"'
PARSE_CALL = 'batch_card.py" parse --rows "$ROWSFILE" --answer "$ANSWERFILE"'
REPORT_CALL = 'batch_card.py" decisions-report < "$STATE_FILE"'
RECORD_CALL = 'record-decisions --decisions-file "$DECFILE"'

OLD_HEADING = "Medium findings — dismissed"


def read_prose(relpath):
    with open(os.path.join(PLUGIN_DIR, relpath), "r", encoding="utf-8") as fh:
        return fh.read()


def card_section(text):
    start = text.index(CARD_HEADING)
    return text[start:text.index(RECORDING_HEADING, start)]


def writing_section(text):
    return text[text.index(WRITING_HEADING):]


def bash_fences(text):
    """The bodies of every ```bash fence (indented fences included)."""
    return re.findall(r"```bash\n(.*?)\n[ \t]*```", text, re.S)


def helper_flag_violations(text):
    """Every helper invocation line that could carry owner text: an unknown
    flag, a `{{…}}` placeholder, or a $Q1/$Q2/$REASON variable."""
    bad = []
    for body in bash_fences(text):
        for line in body.splitlines():
            if 'batch_card.py"' not in line and 'carry_state.py"' not in line:
                continue
            for flag in re.findall(r"--[a-z-]+", line):
                if flag not in ALL_KNOWN_FLAGS:
                    bad.append((flag, line.strip()))
            for marker in ("{{", "$Q1", "$Q2", "$REASON"):
                if marker in line:
                    bad.append((marker, line.strip()))
    return bad


def inject_into_card(text, snippet):
    """`text` with `snippet` inserted at the end of the card section."""
    i = text.index(RECORDING_HEADING)
    return text[:i] + snippet + "\n\n" + text[i:]


def remove(text, needle):
    assert needle in text, needle
    return text.replace(needle, "")


# --------------------------------------------------------------------------- #
# Checks (each returns a list of problems; [] means the lock holds).
# --------------------------------------------------------------------------- #
def check_labels(text):
    section = card_section(text)
    return ["%s x%d" % (label, section.count("**%s**" % label))
            for label in batch_parse.FINALIZE_Q1 + batch_parse.FINALIZE_Q2
            if section.count("**%s**" % label) != 1]


def check_no_nudge(text):
    outside = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return ["Recommended outside a comment"] if "Recommended" in outside else []


def check_old_loops_gone(text):
    problems = [n for n in ("Step A", "Step C", "Look again", "minimal shape",
                            "per-finding asks") if n in text]
    if text.count("Will fix") != 1:
        problems.append("Will fix x%d" % text.count("Will fix"))
    pinned = [p for p in PINS[FINALIZE_MD] if "Will fix" in p]
    if len(pinned) != 1 or pinned[0] not in text:
        problems.append("Will fix not inside the pinned fallback line")
    return problems


def check_helper_calls(text):
    return ["%s x%d" % (n, text.count(n))
            for n in (ROWS_CALL, PARSE_CALL, REPORT_CALL, RECORD_CALL)
            if text.count(n) != 1]


ANNOTATIONS = (
    "unchanged since pass {{pending_since}}, decision pending",
    "code changed since your decision on pass",
    "severity changed (",
    "(was: {{dismissed|deferred}} — {{stale.reason}})",
    "the line itself was edited",
)


def check_annotations(text):
    section = card_section(text)
    return [n for n in ANNOTATIONS if n not in section]


TURN_AND_BUDGET = ("THIS assistant turn", "Finalize costs one card",
                   "never re-show the card after recording",
                   "there is NO confirm card")


def check_turn_and_budget(text):
    section = card_section(text)
    return [n for n in TURN_AND_BUDGET if n not in section]


D12 = ("apply to mediums only", "named by number",
       "`batch_card.py parse` enforces this")


def check_d12(text):
    section = card_section(text)
    return [n for n in D12 if n not in section]


FIX_ROUTING = ("$SUBSETFILE", '["fix_targets"]', "absorbed_into",
               "50-fix-loop.md", "The fix-loop card",
               "Do NOT write REVIEW.md or archive state")


def check_fix_routing(text):
    section = card_section(text)
    problems = [n for n in FIX_ROUTING if n not in section]
    if "deduplicate" in section:
        problems.append("prose rebuilds the subset")
    return problems


def check_no_git_in_card(text):
    bad = []
    for body in bash_fences(card_section(text)):
        for line in body.splitlines():
            if line.strip().startswith("git ") or "$(git " in line:
                bad.append(line.strip())
    return bad


LOOK_MEMBER = ("read them from the MEMBER record instead",
               "never from that entry's `obligation`")


def check_look_member(text):
    section = card_section(text)
    return [n for n in LOOK_MEMBER if section.count(n) != 1]


def check_schema_heading(schema, finalize):
    problems = []
    if schema.count("\n## Findings dismissed\n") != 1:
        problems.append("Findings dismissed heading")
    if schema.count("## Findings deferred") != 1:
        problems.append("Findings deferred heading")
    for name, text in (("schema", schema), ("finalize", finalize)):
        if OLD_HEADING in text:
            problems.append("old heading in " + name)
    return problems


def check_superseded(schema, finalize):
    problems = []
    if schema.count("(superseded)") < 3:
        problems.append("schema (superseded) x%d" % schema.count("(superseded)"))
    if "(superseded)" not in writing_section(finalize):
        problems.append("finalize fill has no (superseded)")
    if "never dropped" not in schema:
        problems.append("schema note lost 'never dropped'")
    return problems


class LockCase(unittest.TestCase):
    def assert_holds(self, check, *texts):
        self.assertEqual(check(*texts), [])

    def assert_trips(self, check, *mutant_texts):
        self.assertNotEqual(check(*mutant_texts), [])


# --------------------------------------------------------------------------- #
# The finalize card.
# --------------------------------------------------------------------------- #
class TestFinalizeCard(LockCase):
    def setUp(self):
        self.text = read_prose(FINALIZE_MD)

    def test_q1_q2_labels_once(self):
        self.assert_holds(check_labels, self.text)
        with self.subTest("mutant: Mixed… removed"):
            self.assert_trips(check_labels, remove(self.text, "**Mixed…**"))

    def test_no_nudge(self):
        self.assert_holds(check_no_nudge, self.text)
        with self.subTest("mutant: nudge on Fix all"):
            mutant = self.text.replace("**Fix all**",
                                       "**Fix all (Recommended)**", 1)
            self.assert_trips(check_no_nudge, mutant)
        with self.subTest("a commented mention is not a nudge"):
            self.assert_holds(check_no_nudge,
                              self.text + "\n<!-- no (Recommended) tag -->\n")

    def test_old_loops_gone(self):
        self.assert_holds(check_old_loops_gone, self.text)
        with self.subTest("mutant: a Will fix option returns"):
            mutant = inject_into_card(self.text,
                                      "    - **Will fix** → collect it")
            self.assert_trips(check_old_loops_gone, mutant)
        with self.subTest("mutant: the old Look again option returns"):
            mutant = inject_into_card(self.text, "- **Look again** → re-ask")
            self.assert_trips(check_old_loops_gone, mutant)

    def test_owner_text_never_on_argv(self):
        self.assertEqual(helper_flag_violations(self.text), [])
        # The scan really sees the helper calls it is meant to police.
        lines = [line for body in bash_fences(self.text)
                 for line in body.splitlines()
                 if 'batch_card.py"' in line or 'carry_state.py"' in line]
        self.assertGreaterEqual(len(lines), 5)
        for name, line in (
                ("mutant: answer on argv",
                 'python3 "$VC_ROOT/scripts/batch_card.py" parse --q1 '
                 '"{{answer}}"'),
                ("mutant: reason on argv",
                 'python3 "$VC_ROOT/scripts/carry_state.py" record-decisions '
                 '--reason "$REASON"')):
            with self.subTest(name):
                mutant = inject_into_card(self.text,
                                          "```bash\n%s\n```" % line)
                self.assertNotEqual(helper_flag_violations(mutant), [])

    def test_helper_calls_present(self):
        self.assert_holds(check_helper_calls, self.text)

    def test_pending_and_stale_annotations(self):
        self.assert_holds(check_annotations, self.text)
        for needle in ("severity changed (", "the line itself was edited"):
            with self.subTest("mutant: removed " + needle):
                self.assert_trips(check_annotations,
                                  remove(self.text, needle))

    def test_successor_rows_carry_every_suffix_key(self):
        """The stale suffix reads stale.at_pass, stale.decision and
        stale.reason; a re-hashed successor row must carry all three."""
        doc, reason = batch_card.build_rows(successor_state(), "finalize", {})
        self.assertIsNone(reason)
        row = [r for r in doc["rows"] if r["stable_hash"] == HB][0]
        self.assertEqual(row["stale"]["via"], "successor")
        self.assertEqual(row["stale"]["cause"], "code")
        for key in ("at_pass", "decision", "reason"):
            with self.subTest(key=key):
                self.assertIsNotNone(row["stale"][key])
        self.assertIn(row["stale"]["decision"], ("dismiss", "defer"))

    def test_same_turn_and_budget(self):
        self.assert_holds(check_turn_and_budget, self.text)
        with self.subTest("mutant: no-re-show rule removed"):
            self.assert_trips(check_turn_and_budget, remove(
                self.text, "never re-show the card after recording"))

    def test_d12_stated_and_delegated(self):
        self.assert_holds(check_d12, self.text)
        with self.subTest("mutant: mediums-only rule removed"):
            self.assert_trips(check_d12,
                              remove(self.text, "apply to mediums only"))

    def test_fix_routes_to_fix_loop_with_subset(self):
        self.assert_holds(check_fix_routing, self.text)
        with self.subTest("mutant: $SUBSETFILE removed"):
            self.assert_trips(check_fix_routing,
                              remove(self.text, "$SUBSETFILE"))
        with self.subTest("mutant: raw fix list instead of fix_targets"):
            mutant = self.text.replace('["fix_targets"]', '["fix"]')
            self.assert_trips(check_fix_routing, mutant)
        with self.subTest("mutant: prose rebuilds the subset"):
            mutant = inject_into_card(self.text,
                                      "Then deduplicate the fix list by lead.")
            self.assert_trips(check_fix_routing, mutant)

    def test_card_section_has_no_git_call(self):
        self.assert_holds(check_no_git_in_card, self.text)
        with self.subTest("mutant: git call on a finding path"):
            mutant = inject_into_card(
                self.text,
                '```bash\ngit log -L "{{line}},{{line}}:{{file}}"\n```')
            self.assert_trips(check_no_git_in_card, mutant)

    def test_no_fallthrough_gate(self):
        self.assertNotIn("|| { :", self.text)

    def test_pins_still_exactly_once(self):
        for pin in PINS[FINALIZE_MD]:
            with self.subTest(pin=pin[:40]):
                self.assertEqual(self.text.count(pin), 1)

    def test_look_reads_member_record(self):
        """`look N` on an absorbed row reads the MEMBER record's text, never
        members[].obligation (identity and scoring only) nor the lead."""
        self.assert_holds(check_look_member, self.text)
        with self.subTest("mutant: look reads members[].obligation"):
            mutant = self.text.replace(
                "read them from the MEMBER record instead",
                "read them from `members[].obligation` instead")
            self.assert_trips(check_look_member, mutant)


# --------------------------------------------------------------------------- #
# REVIEW.md rendering.
# --------------------------------------------------------------------------- #
class TestReviewMdRendering(LockCase):
    def setUp(self):
        self.schema = read_prose(SCHEMA_MD)
        self.finalize = read_prose(FINALIZE_MD)

    def test_heading_renamed(self):
        self.assert_holds(check_schema_heading, self.schema, self.finalize)
        with self.subTest("mutant: old heading re-inserted"):
            mutant = self.schema.replace("## Findings dismissed",
                                         "## " + OLD_HEADING, 1)
            self.assert_trips(check_schema_heading, mutant, self.finalize)

    def test_superseded_kept(self):
        self.assert_holds(check_superseded, self.schema, self.finalize)
        with self.subTest("mutant: every (superseded) removed from schema"):
            self.assert_trips(check_superseded,
                              remove(self.schema, "(superseded)"),
                              self.finalize)

    def test_pre_git_validations_kept(self):
        section = writing_section(self.finalize)
        for needle in ("^[A-Za-z0-9._/-]+$", "$GUARD_PY", "^[1-9][0-9]*$",
                       "Finalize's only state write is the "
                       "`record-decisions` step above"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)


if __name__ == "__main__":
    unittest.main()
