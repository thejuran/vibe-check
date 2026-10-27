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
import finalize_gate  # noqa: E402  (sibling module: FLAGS, the REVIEW.md stamp)
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


PHASE57_DECISIONS = (
    "the line number is stored, not compared",
    "snapshot.nearby_at",
    "a drop keeps the decision",
    "re-asks only with new corroboration",
    "recorded as covered at decision time",
    'stale.cause == "nearby"',
    "now also report(s) it",
    "joined it",
    "within 5 lines above or below",
    "whose title is not a covered title",
    "separately-owed obligation is never covered",
    "did not report this concern at decision time",
)


def check_phase57_decisions(text):
    """The Open/Closed contract and the stale-suffix bullets say what the
    helper does: the line is not compared, a nearby change reopens, a drop
    keeps, a rise reopens only with a new lane, coverage recorded at decision
    time is the one inheritance path, and the three new suffixes exist."""
    return [n for n in PHASE57_DECISIONS if n not in text]


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


LIST_IN_CARD = (
    "copy the `card_text` field of `$ROWSFILE` verbatim into Q1",
    "never print it only from a shell command",
    "When `card_text_truncated` is true",
    "ALSO print the `list_text` field verbatim as message text",
)
ECHO_VISIBLE = (
    "it must never be visible only inside a Bash call's output",
    "as the opening lines of the next message you print",
    "when step 2 routes to the fix-loop card, that card is not shown (the "
    "subset goes straight to its Step B), so print `echo_text` as message "
    "text before reading `50-fix-loop.md`",
    "whose summary message opens with `echo_text`",
    "the stop message opens with `echo_text`",
)


def q1_line(text):
    start = text.index("> **Q1** — header \"Decide\"")
    return text[start:text.index("\n", start)]


def check_list_in_card(text):
    section = card_section(text)
    problems = [n for n in LIST_IN_CARD + ECHO_VISIBLE
                if section.count(n) != 1]
    q1 = q1_line(section)
    for needle in ("{{card_text}}", "listed below"):
        if needle not in q1:
            problems.append("Q1 lacks " + needle)
    if "(message text above the card" in section:
        problems.append("list printed as message text above the card")
    if "print the `echo` lines verbatim as message text" in section:
        problems.append("echo printed as message text only")
    return problems


def parse_q1_spec(text):
    """The Parse step's description of the Q1 value written to $ANSWERFILE."""
    section = card_section(text)
    m = re.search(r'\*\*Parse\.\*\*.*?"q1": "<(.*?)>", "q2"', section, re.S)
    return m.group(1) if m else ""


def q1_full_string_holds(text):
    """The parser gets the whole Q1 answer: notes text and inline reason too."""
    spec = parse_q1_spec(text)
    return all(n in spec for n in ("FULL Q1 answer string", "`notes:`",
                                   "`-- reason`", "verbatim"))


def need_text_bullet(text):
    for line in card_section(text).splitlines():
        if line.startswith("- `need_text` true"):
            return line
    return ""


def bare_mixed_one_clarification_holds(text):
    """A bare Mixed… re-asks exactly once and never decides a row itself."""
    bullet = need_text_bullet(text)
    return all(n in bullet for n in ("ONCE", "Never infer",
                                     "(no option selected) notes:"))


# --------------------------------------------------------------------------- #
# The card says what the parser does; a plain-English answer is translated.
# --------------------------------------------------------------------------- #
OPT_FIX_ALL = '> 3. **Fix all** — "{{bulk_fix_text}}"'
BULK_SLOT = "{{bulk_fix_text}}"
BULK_SOURCE = ("it is the `bulk_fix_text` field of `$ROWSFILE`, verbatim — the "
               "helper names the Needs-verification rows Fix all leaves out by "
               "number")
OPT_DISMISS = ("Critical, warning and Needs-verification rows stay open unless "
               "you name them by number in Mixed…")
OPT_DEFER = "same rule for critical, warning and Needs-verification rows"
OPT_MIXED = ("`fix all` covers critical, warning and medium rows; `dismiss all` "
             "/ `defer all` cover medium rows only; a Needs-verification row is "
             "never reached by `all` or `rest`")
OLD_FIX_ALL = "Send every row, any band"


def check_option_descriptions(text):
    section = card_section(text)
    problems = [n for n in (OPT_FIX_ALL, BULK_SOURCE, OPT_DISMISS, OPT_DEFER,
                            OPT_MIXED) if section.count(n) != 1]
    if text.count(BULK_SLOT) != 1:
        problems.append("{{bulk_fix_text}} x%d" % text.count(BULK_SLOT))
    if "lowest band" in section:
        problems.append("Mixed… still says lowest band")
    if OLD_FIX_ALL in text:
        problems.append("Fix all still says any band")
    return problems


Q1_COUNTS = ("({{C}} critical/warning, {{V}} needs-verification, {{M}} medium"
             "{{; P")
Q1_V_DEFINED = "`C` / `V` / `M` = rows by band; C + V + M = N"


def check_q1_header(text):
    q1 = q1_line(card_section(text))
    return [n for n in (Q1_COUNTS, Q1_V_DEFINED) if n not in q1]


TRANSLATE_HEAD = "**Translate the answer (D-01).**"
RESOLVE_CALL = 'resolve --rows "$ROWSFILE" --answer "$REFSFILE"'
TRANSLATE_NEEDLES = (
    "On `refused: empty answer` re-show the card once",
    "On any other refusal go to **Translate the answer (D-01)**",
    TRANSLATE_HEAD,
    "from the OWNER's text only",
    "to `$REFSFILE` with the Write tool",
    "run the SAME parse fence above",
    "Read your answer as: ",
    "no confirm card",
    "continue at **After the answer**",
    "the Q2 pick still supplies the reason when the owner's text gave none",
    "`close_out` is always false here",
    "→ **Ask only what is missing (D-05, D-06)**",
    'cp "$SUGGESTFILE" "$ANSWERFILE"',
)


def check_translate_path(text):
    section = card_section(text)
    problems = [n for n in TRANSLATE_NEEDLES if n not in section]
    if "Re-show the SAME card" in section:
        problems.append("a refusal still re-shows the SAME card")
    if "close-out-after-rerun" in text:
        problems.append("Finalize writes the close-out carrier")
    fences = bash_fences(section)
    # The plain resolve fence, once; its --prior-rows twin is check_stale's.
    plain = sum(RESOLVE_CALL in f and "--prior-rows" not in f for f in fences)
    if plain != 1:
        problems.append("resolve fence x%d" % plain)
    if not any('["grammar"]' in f and '"$ANSWERFILE"' in f for f in fences):
        problems.append("grammar not copied file-to-file into $ANSWERFILE")
    parse_at = section.find(PARSE_CALL)
    head_at = section.find(TRANSLATE_HEAD)
    after_at = section.find("**After the answer** (branch on")
    if not 0 <= parse_at < head_at < after_at:
        problems.append("Translate paragraph not between the parse fence "
                        "and After the answer")
    return problems


NV_STOP_NEW = ("re-checked automatically on every later run that reviews "
               "changes while the repaired code is unchanged")
NV_STOP_OLD = "re-checks it once"


def check_nv_stop_reconciled(text):
    problems = [] if NV_STOP_NEW in text else ["NV stop text not reconciled"]
    if NV_STOP_OLD in text:
        problems.append("NV stop text still says re-checks it once")
    return problems


BOTTOM_SLOT = ('{{\\n\\nBottom line suggests: <grammar> — type "bottom line" '
               'in Other to take it}}')
BOTTOM_NEEDLES = (
    "**Bottom line as a choice (D-09).**",
    "THIS session rendered the last pass's Bottom line",
    "a separate `--finalize` invocation renders no report",
    "re-translated against THIS card's rows",
    "Finalize numbering differs from the fix-loop card",
    'parse --rows "$ROWSFILE" --answer "$SUGGESTFILE"',
    'rm -f "$SUGGESTFILE"',
    "never print a guessed one",
)


def check_bottom_line(text):
    section = card_section(text)
    problems = [] if BOTTOM_SLOT in q1_line(section) else ["Q1 lacks the slot"]
    problems += [n for n in BOTTOM_NEEDLES if n not in section]
    return problems


FOLLOWUP_HEAD = "**Ask only what is missing (D-05, D-06).**"
AFTER_HEAD = "**After the answer** (branch on"
FOLLOWUP_NEEDLES = (
    FOLLOWUP_HEAD,
    "record nothing",
    "never half-apply",
    "ONE short AskUserQuestion",
    "only the unclear piece",
    "`#n file:line`",
    'header "Which row";',
    'header "Which rows"',
    'header "Reason"',
    "asked only when both are absent",
    "one follow-up per gap",
    "show the full card once",
    "could not be matched",
    "continue at **After the answer**",
)


def followup_paragraph(text):
    """The Finalize follow-up paragraph: from its heading to After the answer."""
    section = card_section(text)
    start = section.find(FOLLOWUP_HEAD)
    end = section.find(AFTER_HEAD)
    if start < 0 or end < start:
        return ""
    return section[start:end]


def check_followup(text):
    """A partly readable answer records nothing, asks ONE question about only
    the gap (a reason only when neither the owner's text nor Q2 gave one),
    and a second unclear reply shows the full card once, then stops."""
    para = followup_paragraph(text)
    if not para:
        return ["no Ask-only-what-is-missing paragraph before After the answer"]
    problems = [n for n in FOLLOWUP_NEEDLES if n not in para]
    problems += ["Q2 label %r not offered" % q for q in batch_parse.FINALIZE_Q2
                 if "`%s`" % q not in para]
    return problems


STALE_CALL = ('resolve --rows "$ROWSFILE" --answer "$REFSFILE" '
              '--prior-rows "$PRIORROWSFILE"')
STALE_NEEDLES = ("`prior_number`", "by finding identity",
                 "shows the new numbers", "an earlier `--finalize`")


def check_stale(text):
    """A stale Finalize card is re-mapped by identity through the
    --prior-rows twin fence, and the echo shows the new numbers."""
    section = card_section(text)
    problems = [n for n in STALE_NEEDLES if n not in section]
    if not any(STALE_CALL in f for f in bash_fences(section)):
        problems.append("no --prior-rows twin resolve fence")
    return problems


BUDGET_HEAD = "**Card budget.**"
BUDGET_NEEDLES = (
    "Finalize costs one card",
    "a plain-English answer that needs one detail (at most one follow-up "
    "card per gap, D-06)",
    "a second unclear reply (which shows the full card once, D-08)",
    "A bare Mixed… buys exactly one clarification.",
)
BUDGET_OLD = "or an unparseable answer adds another"


def budget_line(text):
    for line in card_section(text).splitlines():
        if line.startswith(BUDGET_HEAD):
            return line
    return ""


def check_budget(text):
    """The budget names every extra card the file can show, and no longer
    the open-ended 'unparseable answer' re-ask."""
    line = budget_line(text)
    problems = [n for n in BUDGET_NEEDLES if n not in line]
    if BUDGET_OLD in text:
        problems.append("budget still lets an unparseable answer add a card")
    return problems + check_turn_and_budget(text)


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

    def test_phase57_decision_contract(self):
        self.assert_holds(check_phase57_decisions, self.text)
        for needle in PHASE57_DECISIONS:
            with self.subTest("mutant: removed " + needle):
                mutant = remove(self.text, needle)
                self.assertNotEqual(mutant, self.text)
                self.assert_trips(check_phase57_decisions, mutant)

    def test_phase57_old_closed_rule_gone(self):
        self.assertNotIn("equals the same four values now", self.text)
        # The nearby window is symmetric (D-14); the one-sided wording is gone.
        self.assertNotIn("5-line window beneath", self.text)
        self.assertEqual(self.text.count("helper links an edited finding"), 1)

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

    def test_q1_full_string_reaches_the_parser(self):
        self.assertTrue(q1_full_string_holds(self.text))
        for needle in ("including any `notes:` text and any trailing "
                       "`-- reason` — ", "FULL ", " — verbatim"):
            with self.subTest("mutant: %r removed" % needle):
                mutant = remove(self.text, needle)
                self.assertNotEqual(mutant, self.text)
                self.assertFalse(q1_full_string_holds(mutant))
        with self.subTest("mutant: the phrase moved out of the Parse step"):
            mutant = self.text.replace(
                "the tool result's FULL Q1 answer string — including any "
                "`notes:` text and any trailing `-- reason` — verbatim",
                "Q1 answer", 1) + "\nFULL Q1 answer string `notes:` " \
                "`-- reason` verbatim\n"
            self.assertNotEqual(mutant, self.text)
            self.assertFalse(q1_full_string_holds(mutant))

    def test_bare_mixed_buys_one_clarification(self):
        self.assertTrue(bare_mixed_one_clarification_holds(self.text))
        self.assertIn("A bare Mixed… buys exactly one clarification.",
                      card_section(self.text))
        for needle in ("re-show the same card ONCE",
                       " Never infer fix/defer/dismiss from a bare selection"):
            with self.subTest("mutant: %r removed" % needle):
                mutant = remove(self.text, needle)
                self.assertNotEqual(mutant, self.text)
                self.assertFalse(bare_mixed_one_clarification_holds(mutant))
        with self.subTest("mutant: rule moved off the need_text bullet"):
            bullet = need_text_bullet(self.text)
            mutant = self.text.replace(
                bullet, "- `need_text` true → re-show the same card.", 1)
            self.assertNotEqual(mutant, self.text)
            self.assertFalse(bare_mixed_one_clarification_holds(mutant))

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

    # The fix-loop's subset fence takes the literal path, so Finalize must
    # print it: a shell variable does not survive into a later Bash call.
    def test_subset_path_is_printed_for_the_fix_loop(self):
        printed = "printf 'SUBSETFILE=%s\\n' \"$SUBSETFILE\""
        fences = [b for b in bash_fences(self.text) if '["fix_targets"]' in b]
        self.assertEqual(len(fences), 1)
        self.assertIn(printed, fences[0])
        self.assertIn("carry the literal path this fence printed", self.text)

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


    def test_list_and_echo_visible_on_screen(self):
        """D1: the numbered list rides in Q1 and the parse echo opens the
        next visible message, never only a Bash call's collapsed output."""
        self.assert_holds(check_list_in_card, self.text)
        q1 = q1_line(self.text)
        with self.subTest("mutant: card_text dropped from Q1"):
            self.assert_trips(check_list_in_card, self.text.replace(
                q1, q1.replace("{{card_text}}", ""), 1))
        with self.subTest("mutant: back to a list above the card"):
            self.assert_trips(check_list_in_card, inject_into_card(
                self.text, "**The list (message text above the card, D-05).**"))
        with self.subTest("mutant: echo back to message text only"):
            self.assert_trips(check_list_in_card, remove(
                self.text, "as the opening lines of the next message you print"))

class TestPhase58Finalize(LockCase):
    """Each description says what `batch_card.py parse` does, and a typed
    answer the grammar refuses is translated, checked and acted on."""

    def setUp(self):
        self.text = read_prose(FINALIZE_MD)

    def _mutant(self, old, new=""):
        self.assertIn(old, self.text)
        mutant = self.text.replace(old, new)
        self.assertNotEqual(mutant, self.text)
        return mutant

    def test_option_descriptions_holds(self):
        self.assert_holds(check_option_descriptions, self.text)

    def test_mutant_option_descriptions(self):
        with self.subTest("mutant: Fix all back to any band"):
            self.assert_trips(check_option_descriptions, self._mutant(
                OPT_FIX_ALL,
                '> 3. **Fix all** — "Send every row, any band, to the '
                'fix-loop card"'))
        with self.subTest("mutant: Mixed… says lowest band again"):
            self.assert_trips(check_option_descriptions, self._mutant(
                OPT_MIXED, "`all` means every row of the lowest band"))
        with self.subTest("mutant: Dismiss all forgets NV rows"):
            self.assert_trips(check_option_descriptions, self._mutant(
                OPT_DISMISS, "Critical/warning rows stay open unless you name "
                             "them by number in Mixed…"))

    def test_q1_header_holds(self):
        self.assert_holds(check_q1_header, self.text)

    def test_mutant_q1_header(self):
        with self.subTest("mutant: NV count dropped from the header"):
            self.assert_trips(check_q1_header, self._mutant(
                "{{V}} needs-verification, ", ""))

    def test_translate_path_holds(self):
        self.assert_holds(check_translate_path, self.text)

    def test_mutant_translate_path(self):
        with self.subTest("mutant: refusal re-shows the SAME card again"):
            self.assert_trips(check_translate_path, self._mutant(
                "On any other refusal go to **Translate the answer (D-01)**.",
                "Re-show the SAME card (D-06: an unparseable answer re-asks, "
                "never guesses)."))
        with self.subTest("mutant: Q2 no longer the fallback reason"):
            self.assert_trips(check_translate_path, self._mutant(
                "the Q2 pick still supplies the reason when the owner's text "
                "gave none"))
        with self.subTest("mutant: Finalize writes the close-out carrier"):
            self.assert_trips(check_translate_path, inject_into_card(
                self.text, "Re-enter with `--close-out-after-rerun`."))
        with self.subTest("mutant: resolve fence removed"):
            self.assert_trips(check_translate_path, self._mutant(
                RESOLVE_CALL, 'resolve --rows "$ROWSFILE"'))

    def test_nv_stop_reconciled_holds(self):
        self.assert_holds(check_nv_stop_reconciled, self.text)

    def test_mutant_nv_stop_reconciled(self):
        with self.subTest("mutant: re-checks it once restored"):
            self.assert_trips(check_nv_stop_reconciled, self._mutant(
                NV_STOP_NEW, "the next review run re-checks it once"))

    def test_mutant_echo_visible(self):
        with self.subTest("mutant: old From-your-finalize-answer needle"):
            self.assert_trips(check_list_in_card, self._mutant(
                ECHO_VISIBLE[2],
                "when step 2 routes to the fix-loop card, as that card's "
                "closing \"From your finalize answer:\" block"))

    def test_bottom_line_holds(self):
        self.assert_holds(check_bottom_line, self.text)
        self.assert_holds(check_no_nudge, self.text)

    def test_mutant_bottom_line(self):
        with self.subTest("mutant: guessed suggestion allowed"):
            self.assert_trips(check_bottom_line,
                              self._mutant("never print a guessed one"))
        with self.subTest("mutant: session condition dropped"):
            self.assert_trips(check_bottom_line, self._mutant(
                "THIS session rendered the last pass's Bottom line"))
        with self.subTest("mutant: nudge on the suggestion slot"):
            self.assert_trips(check_no_nudge, self._mutant(
                "in Other to take it}}", "in Other to take it (Recommended)}}"))


class TestPhase58FinalizeRouting(LockCase):
    """A partly readable Finalize answer asks only the gap, once; a stale
    card is re-mapped by identity; the budget names every extra card."""

    def setUp(self):
        self.text = read_prose(FINALIZE_MD)

    def _mutant(self, old, new=""):
        self.assertIn(old, self.text)
        mutant = self.text.replace(old, new)
        self.assertNotEqual(mutant, self.text)
        return mutant

    def test_followup_holds(self):
        self.assert_holds(check_followup, self.text)

    def test_mutant_followup(self):
        with self.subTest("mutant: follow-up no longer records nothing"):
            self.assert_trips(check_followup, self._mutant("record nothing"))
        with self.subTest("mutant: reason asked even when Q2 gave one"):
            self.assert_trips(check_followup, self._mutant(
                "asked only when both are absent"))
        with self.subTest("mutant: open-ended re-asking"):
            self.assert_trips(check_followup, self._mutant(
                "show the full card once"))

    def test_stale_holds(self):
        self.assert_holds(check_stale, self.text)

    def test_mutant_stale(self):
        with self.subTest("mutant: stale card without --prior-rows"):
            self.assert_trips(check_stale, self._mutant(
                ' --prior-rows "$PRIORROWSFILE"'))
        with self.subTest("mutant: echo keeps the old numbers"):
            self.assert_trips(check_stale, self._mutant(
                "shows the new numbers"))

    def test_budget_holds(self):
        self.assert_holds(check_budget, self.text)

    def test_mutant_budget(self):
        with self.subTest("mutant: old 'unparseable answer' clause restored"):
            line = budget_line(self.text)
            self.assertTrue(line)
            self.assert_trips(check_budget, self._mutant(
                line, "**Card budget.** Finalize costs one card. Only "
                      "`look N`, a bare Mixed…, or an unparseable answer adds "
                      "another, each at the owner's request. A bare Mixed… "
                      "buys exactly one clarification. Nothing else in this "
                      "file asks a question."))
        with self.subTest("mutant: D-08 fallback dropped from the budget"):
            self.assert_trips(check_budget, self._mutant(
                " or a second unclear reply (which shows the full card once, "
                "D-08)"))


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


# --------------------------------------------------------------------------- #
# Needs-verification at finalize (Phase 53 R10) and the REVIEW.md format stamp.
# Each predicate returns True when the lock holds; each test also runs it on a
# mutant that must return False.
# --------------------------------------------------------------------------- #
FLAGS_LITERAL_RE = re.compile(r'`\{"flags": \{([^`]*)\}\}`')
NV_BY_NUMBER = (
    "never cover a Needs-verification item",
    "a critical, warning or needs-verification row is dismissed or deferred "
    "only when named by number",
    "several may be named at once with one reason",
    "each is recorded individually (R10)",
)
NV_FALLBACK_HEADER = ("Print: \"Cannot finalize — {{N}} Needs-verification "
                      "item(s) undecided:\"")
REVIEW_CLOSED_CALL = 'finalize_gate.py" review-closed'
UNSTAMPED_ARCHIVE = "REVIEW-unstamped-"


def seven_key_flags_holds(text):
    literals = FLAGS_LITERAL_RE.findall(text)
    if len(literals) != 1:
        return False
    keys = re.findall(r'"([a-z_]+)":', literals[0])
    return (sorted(keys) == sorted(finalize_gate.FLAGS)
            and "exactly the seven keys" in text
            and "exactly the six keys" not in text)


def nv_by_number_rule_holds(text):
    section = card_section(text)
    return all(phrase in section for phrase in NV_BY_NUMBER)


def nv_fallback_listing_holds(text):
    i = text.find(NV_FALLBACK_HEADER)
    if i < 0:
        return False
    bullet_end = text.find("\n- ", i)
    bullet = text[i:bullet_end if bullet_end >= 0 else len(text)]
    return "`undecided_nv_hashes`" in bullet and "and stop" in bullet


def write_bullet(text):
    start = text.index("- `write` (only on the gate's `write`")
    return text[start:text.index("- `refuse`", start)]


def schema_template_lines(schema):
    body = schema.split("````markdown\n", 1)[1].split("\n````", 1)[0]
    return body.split("\n")


def review_stamp_written_holds(text, schema=None):
    schema = read_prose(SCHEMA_MD) if schema is None else schema
    bullet = write_bullet(text)
    if (finalize_gate.REVIEW_FORMAT_STAMP not in bullet
            or REVIEW_CLOSED_CALL not in bullet):
        return False
    lines = schema_template_lines(schema)
    if lines.count(finalize_gate.APPROVED_LINE) != 1:
        return False
    i = lines.index(finalize_gate.APPROVED_LINE)
    return (i + 1 < len(lines)
            and lines[i + 1] == finalize_gate.REVIEW_FORMAT_STAMP
            and lines.count(finalize_gate.REVIEW_FORMAT_STAMP) == 1)


def archive_fence(text):
    fences = re.findall(r"````bash\n(.*?)\n````", text, re.S)
    hits = [f for f in fences if "PRIOR_PHASE=" in f]
    return hits[0] if len(hits) == 1 else None


def unstamped_review_archived_holds(text):
    fence = archive_fence(text)
    if fence is None:
        return False
    prior = fence.find("PRIOR_PHASE=")
    check = fence.find(REVIEW_CLOSED_CALL)
    moved = fence.find(UNSTAMPED_ARCHIVE)
    return 0 <= check < prior and 0 <= moved < prior and check < moved


class TestNeedsVerificationFinalizeProse(LockCase):
    def setUp(self):
        self.text = read_prose(FINALIZE_MD)
        self.schema = read_prose(SCHEMA_MD)

    def _mutant(self, old, new=""):
        mutant = self.text.replace(old, new)
        self.assertNotEqual(mutant, self.text)
        return mutant

    def test_seven_key_flags(self):
        self.assertTrue(seven_key_flags_holds(self.text))
        with self.subTest("mutant: undecided_nv dropped from the literal"):
            self.assertFalse(seven_key_flags_holds(
                self._mutant('"undecided_nv": 0, ')))
        with self.subTest("mutant: back to six keys"):
            self.assertFalse(seven_key_flags_holds(
                self._mutant("exactly the seven keys", "exactly the six keys")))

    def test_nv_by_number_rule(self):
        self.assertTrue(nv_by_number_rule_holds(self.text))
        for phrase in NV_BY_NUMBER:
            with self.subTest(mutant=phrase[:40]):
                self.assertFalse(nv_by_number_rule_holds(self._mutant(phrase)))

    def test_nv_fallback_listing(self):
        self.assertTrue(nv_fallback_listing_holds(self.text))
        with self.subTest("mutant: header removed"):
            self.assertFalse(nv_fallback_listing_holds(
                self._mutant(NV_FALLBACK_HEADER)))
        with self.subTest("mutant: hash list not named"):
            i = self.text.index(NV_FALLBACK_HEADER)
            j = self.text.index("`undecided_nv_hashes`", i)
            mutant = (self.text[:j] + "`the hashes`"
                      + self.text[j + len("`undecided_nv_hashes`"):])
            self.assertNotEqual(mutant, self.text)
            self.assertFalse(nv_fallback_listing_holds(mutant))

    def test_review_stamp_written(self):
        self.assertTrue(review_stamp_written_holds(self.text, self.schema))
        stamp = finalize_gate.REVIEW_FORMAT_STAMP
        with self.subTest("mutant: stamp dropped from the write bullet"):
            bullet = write_bullet(self.text)
            mutant = self.text.replace(bullet, bullet.replace(stamp, ""))
            self.assertNotEqual(mutant, self.text)
            self.assertFalse(review_stamp_written_holds(mutant, self.schema))
        with self.subTest("mutant: stamp removed from the schema"):
            mutant = self.schema.replace(stamp + "\n", "", 1)
            self.assertNotEqual(mutant, self.schema)
            self.assertFalse(review_stamp_written_holds(self.text, mutant))
        with self.subTest("mutant: stamp moved into a code fence"):
            mutant = self.schema.replace(stamp + "\n",
                                         "```\n" + stamp + "\n```\n", 1)
            self.assertNotEqual(mutant, self.schema)
            self.assertFalse(review_stamp_written_holds(self.text, mutant))
        with self.subTest("mutant: stamp not directly under the verdict"):
            mutant = self.schema.replace(stamp + "\n", "", 1).replace(
                "## Coverage", stamp + "\n\n## Coverage", 1)
            self.assertNotEqual(mutant, self.schema)
            self.assertFalse(review_stamp_written_holds(self.text, mutant))

    def test_unstamped_review_archived(self):
        self.assertTrue(unstamped_review_archived_holds(self.text))
        with self.subTest("mutant: unstamped archive removed"):
            self.assertFalse(unstamped_review_archived_holds(
                self._mutant(UNSTAMPED_ARCHIVE, "REVIEW-")))
        with self.subTest("mutant: check moved after the phase archive"):
            fence = archive_fence(self.text)
            head, tail = fence.split("if [ -f .turingmind/REVIEW.md ]; then\n", 1)
            moved = "if [ -f .turingmind/REVIEW.md ]; then\n" + tail + "\n" + head
            mutant = self.text.replace(fence, moved)
            self.assertNotEqual(mutant, self.text)
            self.assertFalse(unstamped_review_archived_holds(mutant))

    def test_state_file_is_the_format53_location(self):
        self.assertIn("`.turingmind/state/format-53/`", self.text)
        self.assertIn("format-53/", self.schema)


if __name__ == "__main__":
    unittest.main()
