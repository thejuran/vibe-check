"""Prose locks for the finalize card in phases/shared/90-finalize.md and the
REVIEW.md rendering rules in templates/review-md-schema.md.

Finalize asks the owner ONE card (two questions: what to do, and one reason)
for every undecided finding. The rows, the parse of the answer, the
record-decisions payload and the fix subset all come from `batch_card.py`;
the prose only renders and routes. These tests pin that shape.

The Finalize path itself is locked too: every temp path any fence creates is
printed (`check_printed_paths`, whole file) and every path a fence reads was
created by a fence (`check_file_refs_created`); the gate inputs come from one
fence that calls `finalize_inputs.py` with its stderr left on screen
(`inputs_block_holds`); the rebuild-once, refused-step and write-boundary rules
(`retry_rule_holds`, `refused_rule_holds`, `write_boundary_holds`); and a
fresh-shell walk runs the real fences on both routes
(`TestFinalizeFreshShellWalk`).

Every lock is a check function that returns a list of problems. Each one is
applied to the real text (must return []) AND to a mutant of it (must return
something), so no lock is decorative: a check that cannot trip fails here.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_card  # noqa: E402  (sibling module: KNOWN_FLAGS, build_rows)
import batch_parse  # noqa: E402  (sibling module: the card labels)
import carry_state  # noqa: E402  (sibling module: KNOWN_FLAGS)
import finalize_gate  # noqa: E402  (sibling module: FLAGS, the REVIEW.md stamp)
import gitfixture  # noqa: E402  (shared temp-repo helper)
from finalize_inputs import NEXT_ACTIONS  # noqa: E402  (the next-action vocabulary)
from test_batch_card import HB, successor_state  # noqa: E402
from test_carry_state import (ARCH_FILE, ARCH_HASH, load_fixture,  # noqa: E402
                              obsolete_verdict)
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
    'suggest --rows "$ROWSFILE" --answer "$SUGGESTFILE"',
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
    'header "How many"',
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
STALE_CARD_SOURCE = "printed after `CARDROWSFILE=`"
STALE_NEVER_SUBSET = "never a path printed only after `ROWSFILE=`"
STALE_ORDINARY = "the ordinary fence that rendered the card the owner read"
STALE_NEEDLES = ("`prior_number`", "by finding identity",
                 "shows the new numbers",
                 "the fix-loop card shown before Close out in this session",
                 STALE_CARD_SOURCE, STALE_NEVER_SUBSET, STALE_ORDINARY,
                 "no longer available")
# The unreachable prior-card source: no earlier --finalize card survives into
# a later invocation, and a rows path is never carried as a shell variable.
STALE_FORBIDDEN = ("an earlier `--finalize`",
                   "that card's `$ROWSFILE` path, used as is")
# Checked against the Stale card paragraph only: a positional "last printed"
# rule binds the subset fence's fix set after a D-17 pass, and a
# `ROWSFILE=`-only source cannot tell the card's print from the subset's
# (WR-03). Elsewhere "the printed `ROWSFILE=`" is the ordinary substitution.
STALE_PARA_FORBIDDEN = ("the last `ROWSFILE=` line",
                        "rows fence printed after `ROWSFILE=`")
STALE_HEAD = "**Stale card (D-07).**"


def stale_paragraph(text):
    """The Finalize **Stale card (D-07)** paragraph, up to its twin fence."""
    section = card_section(text)
    start = section.find(STALE_HEAD)
    if start < 0:
        return ""
    end = section.find("```bash", start)
    return section[start:end if end >= 0 else len(section)]


def check_stale(text):
    """A stale Finalize card is re-mapped by identity through the
    --prior-rows twin fence from the fix-loop card's printed rows path, and
    the echo shows the new numbers; with no printed path it falls back."""
    section = card_section(text)
    problems = [n for n in STALE_NEEDLES if n not in section]
    problems += ["stale source still names %r" % n for n in STALE_FORBIDDEN
                 if n in section]
    para = stale_paragraph(text)
    if not para:
        problems.append("no Stale card paragraph")
    problems += ["stale source binds %r" % n for n in STALE_PARA_FORBIDDEN
                 if n in para]
    if not any(STALE_CALL in f for f in bash_fences(section)):
        problems.append("no --prior-rows twin resolve fence")
    return problems


MKTEMP_RE = re.compile(r"^\s*(?:if )?([A-Z_]+FILE)=\$\(mktemp", re.M)
PATH_CONVENTION = ("a path printed after `NAME=` is reused in a later fence "
                   "only as that literal, substituted for `\"$NAME\"`")


def check_printed_paths(text):
    """Every temp file ANY Finalize fence creates prints its path in the same
    fence (the whole file: a card-section-only scan is how 999.25 slipped,
    58 SA-01), and one card sentence says a printed path is reused only as
    that literal."""
    section = card_section(text)
    problems = []
    for body in bash_fences(text):
        for name in MKTEMP_RE.findall(body):
            printf = "printf '%s=%%s\\n' \"$%s\"" % (name, name)
            if printf not in body:
                problems.append("%s created but its path is not printed" % name)
    count = section.count(PATH_CONVENTION)
    if count != 1:
        problems.append("path convention sentence appears %d times" % count)
    return problems


# Paths a Finalize fence may read without creating them in this file:
# STATE_FILE is bound by Phase 0.5; PRIORROWSFILE is bound to the path the
# fix-loop card's rows fence printed after `CARDROWSFILE=` (50-fix-loop.md).
EXTERNAL_FILE_REFS = {
    "STATE_FILE": None,
    "PRIORROWSFILE": ("bind `$PRIORROWSFILE` to the path the fix-loop card's "
                      "rows fence printed after `CARDROWSFILE=`"),
}


def check_file_refs_created(text):
    """Every `"$NAME"` a fence reads is created by a `NAME=$(mktemp` fence of
    this file, except the externally bound paths, whose binding sentence
    must be present."""
    fences = bash_fences(text)
    made = set()
    for body in fences:
        made |= set(MKTEMP_RE.findall(body))
    reads = set()
    for body in fences:
        reads |= set(_FILE_REF_RE.findall(body))
    problems = []
    for name in sorted(reads - made):
        if name not in EXTERNAL_FILE_REFS:
            problems.append("%s read but never created by a fence" % name)
        elif (EXTERNAL_FILE_REFS[name] is not None
              and EXTERNAL_FILE_REFS[name] not in text):
            problems.append("%s read with no binding sentence" % name)
    return problems


ANSWER_FILES_CLEAR = 'rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"'
TRANSLATION_FILES_CLEAR = 'rm -f "$REFSFILE" "$RESOLVEFILE"'
KEEP_SUGGEST = "keep `$SUGGESTFILE`"
FULL_CARD_ONCE = "show the full card once"
Q1_SUGGEST_COND = "the `suggest` fence below exited 0 for this card"
Q1_SUGGEST_OLD = "printed a `SUGGESTFILE=` path created for this card"
STEP2_HEAD = "  2. `fix` non-empty"
STEP3_HEAD = "  3. `fix` empty"
STEP3_END = "Never jump to `write`"
FIXLOOP_READ = "Read $VC_ROOT/phases/review/50-fix-loop.md"
D08_HEAD = "one follow-up per gap (D-08)"
PARSE_HEAD = "**Parse.**"
BOTTOM_HEAD = "**Bottom line as a choice (D-09).**"
SUGGEST_OLD = "`$SUGGESTFILE` exists for this card"


def _line_starting(section, head):
    for line in section.splitlines():
        if line.startswith(head):
            return line
    return ""


def _clear_before(chunk, anchor, where):
    i, j = chunk.find(ANSWER_FILES_CLEAR), chunk.find(anchor)
    if j < 0:
        return ["%s: anchor %r missing" % (where, anchor)]
    if i < 0 or i > j:
        return ["%s: answer files not cleared before %r" % (where, anchor)]
    return []


def d08_fallback_problems(chunk):
    """The D-08 full-card fallback removes only the translation's refs and
    resolve files and keeps the suggestion: the full card shown next is the
    same card, so its `Bottom line suggests:` line must still work (WR-01)."""
    problems = []
    if TRANSLATION_FILES_CLEAR not in chunk:
        problems.append("D-08 fallback: refs/resolve files not cleared "
                        "before the full card")
    if KEEP_SUGGEST not in chunk:
        problems.append("D-08 fallback: keep sentence missing")
    if ANSWER_FILES_CLEAR in chunk or '"$SUGGESTFILE" "$REFSFILE"' in chunk:
        problems.append("D-08 fallback still removes the suggestion file")
    return problems


def check_answer_files(text):
    """Once the answer is acted on, the suggestion/refs/resolve files are
    removed (fix-loop hand-off, gate re-run, D-08 fallback), and a Bottom
    line suggestion counts only when printed on the card currently shown."""
    section = card_section(text)
    problems = []
    s2, s3 = section.find(STEP2_HEAD), section.find(STEP3_HEAD)
    s3_end = section.find(STEP3_END, s3)
    if s2 < 0 or s3 < s2 or s3_end < s3:
        return ["After the answer steps 2/3 not found"]
    problems += _clear_before(section[s2:s3], FIXLOOP_READ, "step 2")
    problems += _clear_before(section[s3:s3_end], "RE-RUN the counts step",
                              "step 3")
    para = followup_paragraph(text)
    d08 = para.find(D08_HEAD)
    if d08 < 0 or para.find(FULL_CARD_ONCE, d08) < 0:
        problems.append("D-08 fallback sentence missing")
    else:
        problems += d08_fallback_problems(
            para[d08:para.index(FULL_CARD_ONCE, d08)])
    parse = _line_starting(section, PARSE_HEAD)
    if SUGGEST_OLD in parse:
        problems.append("Parse still trusts any existing $SUGGESTFILE")
    if "printed on the card currently shown" not in parse:
        problems.append("Parse does not tie 'bottom line' to the shown card")
    q1 = q1_line(section)
    if Q1_SUGGEST_COND not in q1:
        problems.append("Q1 suggestion line not tied to the suggest exit")
    if Q1_SUGGEST_OLD in q1:
        problems.append("Q1 suggestion line still keyed to a printed path")
    if "was removed at Close out" not in _line_starting(section, BOTTOM_HEAD):
        problems.append("D-09 does not say the fix-loop file was removed")
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


# --------------------------------------------------------------------------- #
# Translate / Ask / Bottom line against the helper's own rules (twin of the
# fix-loop card's locks).
# --------------------------------------------------------------------------- #
TITLE_TEXT_NEW = '"text": "<the owner\'s words for that row, verbatim>"'
TITLE_TEXT_OLD = '"text": "<the owner\'s words>"}'
STRICT_MATCH = ("every word the owner used for a row, filler aside, "
                "must be in that row's title")
PARTIAL_ASKS = "a partial match is not a match — ask"
TITLE_RULE_NEEDLES = (TITLE_TEXT_NEW, "do not trim or clean them",
                      "whole words only", "ignoring filler",
                      "`port` never matches `import`",
                      "the Browse recovery issue", STRICT_MATCH, PARTIAL_ASKS)
_FILLER_LIST = re.compile(r"ignoring filler \(([^)]*)\)")

PARSE_REFUSAL_BULLET = ("every ref is `one` or `bulk`, `needs_reason` is "
                        "false and `parse_reason` is set")
PARSE_REFUSAL_AFTER = ("no piece to narrow", "full-card fallback",
                       "combined two bulk groups", "could not be checked")
BLOCKED_BULLET = "- A `blocked` ref is never asked about"

COUNT_NEEDED_HEAD = 'A `count_needed` ref → header "How many"'
COUNT_NEEDED_NEEDLES = (COUNT_NEEDED_HEAD,
                        "critical, warning or Needs-verification rows",
                        "dismissed or deferred only when you state how many "
                        "(D-18)",
                        "`candidates`", "`#n file:line`", "through Other",
                        '`"count": C`', "`number` refs",
                        "(a Q2 pick never supplies a count)")
COMPLETED_REFS = "Then write the completed refs"

SUGGEST_CALL = ('batch_card.py" suggest --rows "$ROWSFILE" --answer '
                '"$SUGGESTFILE" > "$SUGGESTFILE.tmp" && mv '
                '"$SUGGESTFILE.tmp" "$SUGGESTFILE"')
SUGGEST_ELSE = 'rm -f "$SUGGESTFILE" "$SUGGESTFILE.tmp"'
SUGGEST_SHOW = 'cat "$SUGGESTFILE"'
SUGGEST_SCOPE = ("`fix` for any row but `dismiss`/`defer` for MEDIUM rows "
                 "only (D-19)")
SUGGEST_OWN_WORDS = "still needs your own words"
PARSE_DRY_RUN = 'parse --rows "$ROWSFILE" --answer "$SUGGESTFILE"'


def translate_paragraph(text):
    """The Finalize **Translate the answer** paragraph, up to its fence."""
    section = card_section(text)
    start = section.find(TRANSLATE_HEAD)
    if start < 0:
        return ""
    end = section.find("```bash", start)
    return section[start:end if end >= 0 else len(section)]


def _bullet(para, needle):
    """The whole line of `para` that holds `needle`."""
    at = para.index(needle)
    bol = para.rindex("\n", 0, at) + 1
    eol = para.find("\n", at)
    return para[bol:eol if eol >= 0 else len(para)]


def check_title_rule(text):
    """Translate passes the owner's title words verbatim and states the
    helper's rule: whole words, filler ignored (WR-03)."""
    para = translate_paragraph(text)
    if not para:
        return ["no Translate paragraph"]
    problems = ["Translate lacks: " + n for n in TITLE_RULE_NEEDLES
                if n not in para]
    if TITLE_TEXT_OLD in text:
        problems.append("the unqualified title text form is still present")
    m = _FILLER_LIST.search(para)
    if not m:
        problems.append("Translate lists no filler words")
    else:
        problems += ["filler word the helper does not ignore: " + w
                     for w in (w.strip() for w in m.group(1).split("/"))
                     if w not in batch_card._TITLE_FILLER]
    return problems


def check_parse_refusal_branch(text):
    """An `ok` false result with every ref clear (the parser refused the
    built grammar) goes straight to the full-card fallback (WR-04)."""
    para = followup_paragraph(text)
    if PARSE_REFUSAL_BULLET not in para:
        return ["Ask paragraph lacks the parser-refusal bullet"]
    bullet = _bullet(para, PARSE_REFUSAL_BULLET)
    problems = []
    if not bullet.lstrip().startswith("- "):
        problems.append("the parser-refusal branch is not its own bullet")
    tail = bullet[bullet.index(PARSE_REFUSAL_BULLET):]
    problems += ["parser-refusal bullet lacks: " + n
                 for n in PARSE_REFUSAL_AFTER if n not in tail]
    if batch_parse.REASON_REST_TWICE.strip() not in bullet:
        problems.append("parser-refusal bullet does not name the "
                        "rest-twice refusal")
    if BLOCKED_BULLET not in para or \
            para.index(PARSE_REFUSAL_BULLET) > para.index(BLOCKED_BULLET):
        problems.append("parser-refusal bullet is not before the blocked "
                        "bullet")
    return problems


def check_count_needed(text):
    """An uncounted serious group is asked only its count (D-18); a Q2 pick
    never stands in for the count."""
    para = followup_paragraph(text)
    if COUNT_NEEDED_HEAD not in para:
        return ["Ask paragraph lacks the count_needed bullet"]
    bullet = _bullet(para, COUNT_NEEDED_HEAD)
    problems = ["count_needed bullet lacks: " + n
                for n in COUNT_NEEDED_NEEDLES if n not in bullet]
    if COMPLETED_REFS not in para:
        return problems + ["no completed-refs sentence"]
    at = para.index(COMPLETED_REFS)
    end = para.find("re-run the resolve fence", at)
    sentence = para[at:end if end >= 0 else len(para)]
    if "`count_needed`" not in sentence:
        problems.append("completed-refs sentence does not say how a "
                        "count_needed ref is completed")
    return problems


def check_suggest_fence(text):
    """The D-09 line comes from `batch_card.py suggest`, which keeps
    dismiss/defer for medium rows only (D-19); no parse dry-run is left."""
    section = card_section(text)
    start = section.find(BOTTOM_HEAD)
    if start < 0:
        return ["no Bottom line paragraph"]
    end = section.find("\n\n**", start)
    para = section[start:end if end >= 0 else len(section)]
    problems = []
    fences = [f for f in bash_fences(para) if SUGGEST_CALL in f]
    if len(fences) != 1 or text.count(SUGGEST_CALL) != 1:
        problems.append("the D-09 paragraph lacks the suggest call once")
    else:
        body = fences[0]
        if "else" not in body:
            problems.append("suggest fence has no else arm")
        else:
            then, other = body.split("else", 1)
            if SUGGEST_SHOW not in then:
                problems.append("suggest fence does not print the result")
            if SUGGEST_ELSE not in other:
                problems.append("suggest fence's else arm keeps a file")
    problems += ["Bottom line paragraph lacks: " + n
                 for n in (SUGGEST_SCOPE, SUGGEST_OWN_WORDS) if n not in para]
    if PARSE_DRY_RUN in text:
        problems.append("the parse dry-run of the suggestion is still there")
    return problems


ROWS_PRINT = "printf 'ROWSFILE=%s\\n' \"$ROWSFILE\""
CARD_PRINT = "printf 'CARDROWSFILE=%s\\n' \"$ROWSFILE\""
# Every helper call on this card reads the card's rows as `"$ROWSFILE"`;
# the counts are pinned so no call is moved onto another name (T-58-21-04).
ROWS_CALL_PINS = {
    'suggest --rows "$ROWSFILE" --answer "$SUGGESTFILE"': 1,
    'parse --rows "$ROWSFILE" --answer "$ANSWERFILE"': 1,
    'resolve --rows "$ROWSFILE" --answer "$REFSFILE" > "$RESOLVEFILE"': 1,
    'resolve --rows "$ROWSFILE" --answer "$REFSFILE" --prior-rows '
    '"$PRIORROWSFILE"': 1,
    '--rows "$ROWSFILE"': 4,
}


def check_card_rows_print(text):
    """Finalize's rows fence renders a card, so besides `ROWSFILE=` it prints
    the same path as `CARDROWSFILE=` -- the next fix-loop pass re-maps a
    stale answer from that print only. Nothing reads `$CARDROWSFILE`."""
    section = card_section(text)
    fences = [f for f in bash_fences(section) if ROWS_CALL in f]
    if len(fences) != 1:
        return ["Finalize rows fence not found once"]
    body = fences[0]
    problems = []
    if ROWS_PRINT not in body:
        problems.append("rows fence prints no ROWSFILE=")
    elif CARD_PRINT not in body[body.index(ROWS_PRINT):]:
        problems.append("rows fence prints no CARDROWSFILE= after ROWSFILE=")
    for needle in ("printf 'ROWSFILE=%s", "printf 'CARDROWSFILE=%s"):
        n = text.count(needle)
        if n != 1:
            problems.append("%s printed %d times" % (needle, n))
    if "$CARDROWSFILE" in text:
        problems.append("$CARDROWSFILE is consumed")
    for call, want in ROWS_CALL_PINS.items():
        n = text.count(call)
        if n != want:
            problems.append("%r appears %d times, want %d" % (call, n, want))
    return problems


TRIM_HEAD = "Exit 0 → fill the card's"
TRIM_NOTE = "need your own words)"
TRIM_COUNT_ONLY = "the count only, never which rows"


def check_trim_note(text):
    """A trimmed Bottom line suggestion ends with a count-only note (IN-01)."""
    line = _line_starting(card_section(text), TRIM_HEAD)
    if not line:
        return ["no Exit 0 sentence"]
    return ["Exit 0 sentence lacks: " + n
            for n in (TRIM_NOTE, TRIM_COUNT_ONLY) if n not in line]


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


class TestGapRoundFinalize(LockCase):
    """Every Finalize temp path is printed and reused only as a literal; the
    answer files are cleared once the answer is acted on; the stale re-map
    reads the fix-loop card's printed rows path or falls back."""

    def setUp(self):
        self.text = read_prose(FINALIZE_MD)

    def _mutant(self, old, new=""):
        self.assertIn(old, self.text)
        mutant = self.text.replace(old, new, 1)
        self.assertNotEqual(mutant, self.text)
        return mutant

    def test_printed_paths_holds(self):
        self.assert_holds(check_printed_paths, self.text)

    def test_mutant_printed_paths(self):
        with self.subTest("mutant: RESOLVEFILE path not printed"):
            self.assert_trips(check_printed_paths, self._mutant(
                "printf 'RESOLVEFILE=%s\\n' \"$RESOLVEFILE\"\n"))
        with self.subTest("mutant: BLOBFILE path not printed"):
            self.assert_trips(check_printed_paths, self._mutant(
                "printf 'BLOBFILE=%s\\n' \"$BLOBFILE\"\n"))
        with self.subTest("mutant: convention sentence dropped"):
            self.assert_trips(check_printed_paths, self._mutant(
                PATH_CONVENTION, "a path is reused"))

    def test_retry_rule_holds(self):
        self.assert_holds(retry_rule_holds, self.text)

    def test_mutant_retry_rule(self):
        with self.subTest("mutant: earlier attempt's BLOBFILE may be reused"):
            self.assert_trips(retry_rule_holds, self._mutant(
                "Never reuse a `BLOBFILE=` printed by an earlier attempt "
                "or an earlier session: "))
        with self.subTest("mutant: rebuild reuses the old file"):
            self.assert_trips(retry_rule_holds, self._mutant(
                "it mints and prints a NEW `BLOBFILE=`",
                "it reuses the same `BLOBFILE=`"))
        with self.subTest("mutant: rebuild runs a different step"):
            self.assert_trips(retry_rule_holds, self._mutant(
                "run the SAME fence again ONCE", "re-run the counts once"))
        with self.subTest("mutant: exit 5 rebuilt"):
            self.assert_trips(retry_rule_holds, self._mutant(
                "Exit 5 stops at once", "Exit 5 is rebuilt"))
        with self.subTest("mutant: stop-refused retried"):
            self.assert_trips(retry_rule_holds, self._mutant(
                "A `next` of `stop-refused` is never retried. "))
        with self.subTest("mutant: a GATEFILE rule put back"):
            para = retry_paragraph(self.text)
            self.assert_trips(retry_rule_holds, self._mutant(
                para, para + " Never reuse a `GATEFILE=`."))
        with self.subTest("mutant: rebuild paragraph gone"):
            self.assert_trips(retry_rule_holds, self._mutant(RETRY_HEAD, ""))

    def test_refused_rule_holds(self):
        self.assert_holds(refused_rule_holds, self.text)

    def test_mutant_refused_rule(self):
        with self.subTest("mutant: refused step retried"):
            self.assert_trips(refused_rule_holds, self._mutant(
                "A step the owner refused (permission denied) is never "
                "retried and stops at once. "))
        with self.subTest("mutant: stop sentence dropped"):
            self.assert_trips(refused_rule_holds, self._mutant(
                'The stop is exactly one sentence: "' + STOP_SENTENCE + '"',
                "The attempt stops."))

    def test_write_boundary_holds(self):
        self.assert_holds(write_boundary_holds, self.text)

    def test_mutant_write_boundary(self):
        with self.subTest("mutant (a): REVIEW.md/archive prohibition deleted"):
            self.assert_trips(write_boundary_holds,
                              self._mutant(WRITE_BOUNDARY + " "))
        with self.subTest("mutant (b): blanket record-decisions ban re-added"):
            self.assert_trips(write_boundary_holds, self._mutant(
                WRITE_BOUNDARY, WRITE_BOUNDARY + " Before that: no REVIEW.md, "
                "no archive, no `record-decisions` call."))
        with self.subTest("mutant (c): the record-decisions fence deleted"):
            fence = _fence_holding(self.text, RECORD_CALL)
            self.assert_trips(write_boundary_holds, self._mutant(fence, ""))

    def test_file_refs_created_holds(self):
        self.assert_holds(check_file_refs_created, self.text)

    def test_mutant_file_refs_created(self):
        with self.subTest("mutant: BLOBFILE mktemp fence removed"):
            fence = blobfile_fence(self.text)
            self.assertIsNotNone(fence)
            mutant = self._mutant("```bash\n" + fence + "```", "")
            self.assert_trips(check_file_refs_created, mutant)
            # the walk's extractor finds no BLOBFILE= fence to run either
            self.assertIsNone(blobfile_fence(mutant))
        with self.subTest("mutant: PRIORROWSFILE binding sentence dropped"):
            self.assert_trips(check_file_refs_created, self._mutant(
                EXTERNAL_FILE_REFS["PRIORROWSFILE"], "use a prior rows file"))

    def test_answer_files_holds(self):
        self.assert_holds(check_answer_files, self.text)

    def test_mutant_answer_files(self):
        s2 = self.text.index(STEP2_HEAD)
        s3 = self.text.index(STEP3_HEAD)
        step2 = self.text[s2:s3]
        with self.subTest("mutant: step 2 keeps the answer files"):
            mutant = (self.text[:s2]
                      + step2.replace(ANSWER_FILES_CLEAR, "true", 1)
                      + self.text[s3:])
            self.assert_trips(check_answer_files, mutant)
        with self.subTest("mutant: any existing SUGGESTFILE counts again"):
            self.assert_trips(check_answer_files, self._mutant(
                "printed on the card currently shown",
                "printed on the card currently shown and " + SUGGEST_OLD))
        with self.subTest("mutant: D-09 forgets the Close out removal"):
            self.assert_trips(check_answer_files, self._mutant(
                "was removed at Close out", "was kept"))

    def test_stale_source_holds(self):
        self.assert_holds(check_stale, self.text)

    def test_mutant_stale_source(self):
        anchor = "the fix-loop card shown before Close out in this session"
        with self.subTest("mutant: earlier --finalize case restored"):
            self.assert_trips(check_stale, self._mutant(
                anchor, anchor + ", or " + STALE_FORBIDDEN[0]
                + " built a card the owner is still answering"))
        with self.subTest("mutant: 'used as is' source restored"):
            self.assert_trips(check_stale, self._mutant(
                STALE_CARD_SOURCE,
                STALE_CARD_SOURCE + " (" + STALE_FORBIDDEN[1] + ")"))
        with self.subTest("mutant: no-path fallback dropped"):
            self.assert_trips(check_stale, self._mutant(
                "no longer available", "gone"))


    def _step3_mutant(self, old, new=""):
        """Replace `old` inside the step-3 line only (the rebuild-once
        paragraph carries similar wording)."""
        line = step3_line(self.text)
        self.assertIn(old, line)
        return self._mutant(line, line.replace(old, new, 1))

    def test_step3_rerun_rule_holds(self):
        self.assert_holds(step3_rerun_rule_holds, self.text)

    def test_mutant_step3_rerun_rule(self):
        for needle in STEP3_NEEDLES:
            with self.subTest("mutant: step 3 drops " + needle):
                self.assert_trips(step3_rerun_rule_holds,
                                  self._step3_mutant(needle))
        with self.subTest("mutant: step 3 recounts on the pre-card "
                          "BLOBFILE again"):
            line = step3_line(self.text)
            mutant = self._mutant(line, line + " (" + STEP3_OLD + ")")
            self.assertTrue(all(n in step3_line(mutant)
                                for n in STEP3_NEEDLES))
            self.assert_trips(step3_rerun_rule_holds, mutant)

    def test_mutant_step3_reinserts_stale_fingerprint_claim(self):
        """Every needle stays present; only the reinserted claim that the
        pre-card fingerprints are still current can trip the lock."""
        line = step3_line(self.text)
        self.assertNotIn(STEP3_STALE_OLD, line)
        mutant = self._mutant(
            line, line + " — " + STEP3_STALE_OLD + ", only the decisions have")
        self.assertTrue(all(n in step3_line(mutant) for n in STEP3_NEEDLES))
        self.assert_trips(step3_rerun_rule_holds, mutant)

    def test_step3_keeps_answer_files_anchor(self):
        self.assertEqual(check_answer_files(self.text), [])


class TestGapRoundFinalizeTranslate(LockCase):
    """Finalize's Translate, Ask and Bottom line match the helper the same
    way the fix-loop card does: verbatim title words, the parser-refusal
    branch, the How many question, the suggest fence."""

    def setUp(self):
        self.text = read_prose(FINALIZE_MD)

    def _mutant(self, old, new=""):
        self.assertIn(old, self.text)
        mutant = self.text.replace(old, new, 1)
        self.assertNotEqual(mutant, self.text)
        return mutant

    def _drop_line(self, needle):
        self.assertIn(needle, self.text)
        return self._mutant(_bullet(self.text, needle) + "\n")

    def test_title_rule_holds(self):
        self.assert_holds(check_title_rule, self.text)

    def test_mutant_title_rule(self):
        cases = {
            "old text form": (TITLE_TEXT_NEW + "}", TITLE_TEXT_OLD),
            "rule dropped": ("whole words only", "words"),
            "filler the helper keeps": ("filler (the / a", "filler (the / of"),
        }
        for label, (old, new) in cases.items():
            with self.subTest(label):
                self.assert_trips(check_title_rule, self._mutant(old, new))

    def test_parse_refusal_branch_holds(self):
        self.assert_holds(check_parse_refusal_branch, self.text)

    def test_mutant_parse_refusal_branch(self):
        self.assert_trips(check_parse_refusal_branch,
                          self._drop_line(PARSE_REFUSAL_BULLET))

    def test_count_needed_holds(self):
        self.assert_holds(check_count_needed, self.text)
        self.assert_holds(check_followup, self.text)

    def test_mutant_count_needed(self):
        mutant = self._drop_line(COUNT_NEEDED_HEAD)
        self.assert_trips(check_count_needed, mutant)
        self.assert_trips(check_followup, mutant)
        with self.subTest("Q2 clause dropped"):
            self.assert_trips(check_count_needed, self._mutant(
                " (a Q2 pick never supplies a count)"))

    def test_suggest_fence_holds(self):
        self.assert_holds(check_suggest_fence, self.text)
        self.assert_holds(check_bottom_line, self.text)

    def test_mutant_suggest_fence(self):
        restored = ('batch_card.py" parse --rows "$ROWSFILE" --answer '
                    '"$SUGGESTFILE" > /dev/null')
        cases = {
            "parse dry-run restored": (SUGGEST_CALL, restored),
            "else keeps the tmp file": (SUGGEST_ELSE, 'rm -f "$SUGGESTFILE"'),
            "scope sentence dropped": (SUGGEST_SCOPE, "any verb"),
        }
        for label, (old, new) in cases.items():
            with self.subTest(label):
                self.assert_trips(check_suggest_fence, self._mutant(old, new))
        self.assert_trips(check_bottom_line,
                          self._mutant(SUGGEST_CALL, restored))


class TestFinalRoundFinalize(LockCase):
    """WR-01, WR-03(a), WR-02 and IN-01 on the Finalize card, the mirror of
    the fix loop's final round, each with mutants restoring the defect."""

    def setUp(self):
        self.text = read_prose(FINALIZE_MD)

    def _mutant(self, old, new=""):
        self.assertIn(old, self.text)
        mutant = self.text.replace(old, new, 1)
        self.assertNotEqual(mutant, self.text)
        return mutant

    def _d08_mutant(self, old, new):
        """Replace `old` inside the D-08 sentence only."""
        start = self.text.index(D08_HEAD)
        end = self.text.index(FULL_CARD_ONCE, start)
        chunk = self.text[start:end]
        self.assertIn(old, chunk)
        return (self.text[:start] + chunk.replace(old, new, 1)
                + self.text[end:])

    def test_answer_files_holds(self):
        self.assert_holds(check_answer_files, self.text)

    def test_stale_source_holds(self):
        self.assert_holds(check_stale, self.text)

    def test_card_rows_print_holds(self):
        self.assert_holds(check_card_rows_print, self.text)
        self.assert_holds(check_printed_paths, self.text)

    def test_trim_note_holds(self):
        self.assert_holds(check_trim_note, self.text)

    def test_title_rule_holds(self):
        self.assert_holds(check_title_rule, self.text)

    def test_mutant_answer_files(self):
        with self.subTest("fallback deletes the suggestion"):
            self.assert_trips(check_answer_files, self._d08_mutant(
                TRANSLATION_FILES_CLEAR, ANSWER_FILES_CLEAR))
        with self.subTest("fallback drops keep"):
            self.assert_trips(check_answer_files, self._d08_mutant(
                KEEP_SUGGEST, "remove `$SUGGESTFILE`"))
        with self.subTest("Q1 condition restored"):
            self.assert_trips(check_answer_files, self._mutant(
                Q1_SUGGEST_COND, "the suggestion fence below "
                + Q1_SUGGEST_OLD))

    def test_mutant_stale_source(self):
        para = stale_paragraph(self.text)
        self.assertIn(STALE_NEVER_SUBSET, para)
        never = para[para.index(STALE_NEVER_SUBSET):]
        never = never[:never.index("prior card)") + len("prior card)")]
        cases = {
            "never-clause deleted": (never, ""),
            "last printed rule": (STALE_CARD_SOURCE,
                                  "printed on the last `ROWSFILE=` line "
                                  "printed in this session"),
            "ROWSFILE= source": ("the fix-loop card's rows fence "
                                 + STALE_CARD_SOURCE,
                                 "that card's rows fence printed after "
                                 "`ROWSFILE=`"),
        }
        for label, (old, new) in cases.items():
            with self.subTest(label):
                self.assert_trips(check_stale, self._mutant(old, new))

    def test_mutant_card_rows_print(self):
        cases = {
            "fence loses CARDROWSFILE=": (CARD_PRINT + "\n", ""),
            "twin reads CARDROWSFILE": (
                'resolve --rows "$ROWSFILE" --answer "$REFSFILE" --prior-rows',
                'resolve --rows "$CARDROWSFILE" --answer "$REFSFILE" '
                '--prior-rows'),
        }
        for label, (old, new) in cases.items():
            with self.subTest(label):
                self.assert_trips(check_card_rows_print,
                                  self._mutant(old, new))

    def test_mutant_trim_note(self):
        for label, (old, new) in {
                "note dropped": (TRIM_NOTE, ")"),
                "names rows": (TRIM_COUNT_ONLY, "list which rows"),
        }.items():
            with self.subTest(label):
                self.assert_trips(check_trim_note, self._mutant(old, new))

    def test_mutant_title_rule(self):
        for label, needle in {"strict rule dropped": STRICT_MATCH,
                              "partial asks dropped": PARTIAL_ASKS}.items():
            with self.subTest(label):
                self.assert_trips(check_title_rule,
                                  self._mutant(needle, "the row"))


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


SIX_ROW_FIXTURE = os.path.join(HERE, "fixtures",
                               "iplayarr45-six-row-state.json")
_PRINTED_RE = re.compile(r"^([A-Z_]+FILE)=(.+)$", re.M)
_FILE_REF_RE = re.compile(r'"\$([A-Z_]+FILE)"')

# The Finalize-inputs fence: one block that mints and prints BLOBFILE=, calls
# finalize_inputs.py with its stderr left on screen, and maps the helper's
# exit code to the 2.14.1 sentences.
INPUTS_CALL = ('finalize_inputs.py" --state-file "$STATE_FILE" '
               '--blob-out "$BLOBFILE"')
SWITCH_SLOTS = ('--noninteractive "<true|false>"',
                '--pr-mode "<true|false>"',
                '--range-mode "<true|false>"')
COUNTS_HALT = ("I'm uncertain about Finalize mode — carry_state.py failed; "
               "nothing was written or archived.")
GATE_HALT = ("I'm uncertain about Finalize mode — finalize_gate.py failed; "
             "nothing was written or archived.")
REPORT_HALT = ("I'm uncertain about Finalize mode — batch_card.py "
               "decisions-report failed; nothing was written or archived.")
STOP_SENTENCE = ("Finalize stopped — nothing was written or archived; run "
                 "`--finalize` again.")
INPUTS_FORBIDDEN = ("GATEFILE", "FINALIZE_GATE_JSON", "COUNTS_JSON=$(",
                    "BLOBFILE.err")
INPUTS_REDIRECT_MUTANT = ' 2>"$BLOBFILE.err"'


def _printed(stdout):
    """{NAME: path} for every `NAME=path` line a fence printed."""
    return dict(_PRINTED_RE.findall(stdout))


def _fence_holding(text, needle):
    """Body of the ```bash fence that holds `needle` (None if absent)."""
    if needle not in text:
        return None
    at = text.index(needle)
    start = text.rindex("```bash\n", 0, at) + len("```bash\n")
    return text[start:text.index("```", at)]


def _print_line(name):
    return "printf '%s=%%s\\n' \"$%s\"" % (name, name)


def blobfile_fence(text):
    """The fence that creates the HEAD-fingerprints file and prints
    `BLOBFILE=<path>`, or None."""
    return _fence_holding(text, _print_line("BLOBFILE"))


def inputs_fence(text):
    """The Finalize-inputs fence (the one calling finalize_inputs.py)."""
    return _fence_holding(text, INPUTS_CALL)


def inputs_call_line(text):
    """The line of the Finalize-inputs fence that calls the helper, or ""."""
    fence = inputs_fence(text) or ""
    for line in fence.splitlines():
        if INPUTS_CALL in line:
            return line
    return ""


def inputs_block_holds(text):
    """D-01 / D-05 / D-18: exactly one fence calls finalize_inputs.py; it mints
    and prints BLOBFILE=, carries the three switch slots, holds the three
    uncertain sentences and the stop sentence byte for byte, and redirects
    no stderr (the helper's one counting line stays on screen). The 2.14.1
    hand-run gate inputs are gone."""
    problems = []
    count = text.count(INPUTS_CALL)
    if count != 1:
        problems.append("the helper call appears %d times" % count)
    fence = inputs_fence(text)
    if fence is None:
        return problems + ["no Finalize-inputs fence"]
    if _print_line("BLOBFILE") not in fence:
        problems.append("the fence does not print BLOBFILE=")
    for slot in SWITCH_SLOTS:
        if slot not in fence:
            problems.append("switch slot missing: " + slot)
    for sentence in (COUNTS_HALT, GATE_HALT, REPORT_HALT, STOP_SENTENCE):
        if sentence not in fence:
            problems.append("sentence missing: " + sentence[:50])
    if "2>" in fence:
        problems.append("the fence redirects stderr (D-18)")
    problems += ["2.14.1 hand-run input still present: " + n
                 for n in INPUTS_FORBIDDEN if n in text]
    return problems


RETRY_HEAD = "**One automatic rebuild, then stop (D-07/D-08).**"
RETRY_NEEDLES = (
    "run the SAME fence again ONCE",
    "it mints and prints a NEW `BLOBFILE=`",
    "rebuilds the fingerprints from the current HEAD, index and working tree",
    "this rebuild is the snapshot-freshness revalidation",
    "Never reuse a `BLOBFILE=` printed by an earlier attempt or an earlier "
    "session",
    "A second failure stops.",
    "Exit 5 stops at once",
    "A `next` of `stop-refused` is never retried.",
)
RETRY_FORBIDDEN = ("GATEFILE", "Exit 5 is rebuilt")
REFUSED_NEEDLES = (
    "A step the owner refused (permission denied) is never retried",
    'The stop is exactly one sentence: "' + STOP_SENTENCE + '"',
)
WRITE_BOUNDARY = ("No REVIEW.md is written and no archive move is made before "
                  "the gate returns `write`.")
WRITE_BOUNDARY_FORBIDDEN = ("no `record-decisions` call", "no `record-decisions`")
ONLY_STATE_WRITE = ("Finalize's only state write is the `record-decisions` "
                    "step above")


def retry_paragraph(text):
    """The rebuild-once paragraph (one line), or ""."""
    if RETRY_HEAD not in text:
        return ""
    at = text.index(RETRY_HEAD)
    end = text.find("\n", at)
    return text[at:end if end >= 0 else len(text)]


def retry_rule_holds(text):
    """D-07: one rebuild, by running the same Finalize-inputs fence once more
    into a NEW blob file, never an earlier attempt's file; exit 5 and a
    refusal are never rebuilt; then stop."""
    para = retry_paragraph(text)
    if not para:
        return ["no rebuild-once paragraph"]
    problems = ["rebuild rule lacks: " + n
                for n in RETRY_NEEDLES if n not in para]
    problems += ["rebuild rule still says: " + n
                 for n in RETRY_FORBIDDEN if n in para]
    return problems


def refused_rule_holds(text):
    """D-08: a refused step is never retried and stops with the one plain
    sentence."""
    para = retry_paragraph(text)
    if not para:
        return ["no rebuild-once paragraph"]
    return ["refused-step rule lacks: " + n
            for n in REFUSED_NEEDLES if n not in para]


def write_boundary_holds(text):
    """No REVIEW.md or archive before the gate's `write`, while the validated
    `record-decisions` single writer (the card route's pre-`write` state
    change) stays allowed and present."""
    problems = []
    if WRITE_BOUNDARY not in retry_paragraph(text):
        problems.append("no REVIEW.md / archive boundary sentence")
    problems += ["forbids record-decisions before write: %r" % n
                 for n in WRITE_BOUNDARY_FORBIDDEN if n in text]
    if _fence_holding(text, RECORD_CALL) is None:
        problems.append("the record-decisions fence is gone")
    if ONLY_STATE_WRITE not in text:
        problems.append("the only-state-write sentence is gone")
    return problems


STEP3_NEEDLES = (
    "RE-RUN the counts step ONCE by running the Finalize-inputs fence again",
    "it prints a NEW `BLOBFILE=`",
    "fingerprints rebuilt from the current HEAD, index and working tree",
    "the pre-card `BLOBFILE=` is never reused",
    "branch on its `next`",
    "never on the result this attempt read before the card",
)
STEP3_OLD = "the same `BLOBFILE=` literal this attempt printed"
STEP3_STALE_OLD = "the fingerprints have not changed"


def step3_line(text):
    """The After-the-answer step-3 list item (one line), or ""."""
    return _line_starting(card_section(text), STEP3_HEAD)


def step3_rerun_rule_holds(text):
    """FINL-02 / WR-01 / WR-02: after the owner's answers are recorded, step
    3 runs the Finalize-inputs fence again, which re-fingerprints HEAD into a
    NEW BLOBFILE, recounts and asks the gate, and branches on that result's
    `next`, never on the result read before the card. An edit made while the
    owner answered the card reopens a fix-obsolete verdict instead of being
    closed by it."""
    line = step3_line(text)
    if not line:
        return ["no step 3 line"]
    problems = ["step 3 lacks: " + n for n in STEP3_NEEDLES if n not in line]
    if STEP3_OLD in line:
        problems.append("step 3 still recounts on this attempt's BLOBFILE")
    if STEP3_STALE_OLD in line:
        problems.append("step 3 still claims the pre-card fingerprints are "
                        "current")
    if "GATEFILE" in line:
        problems.append("step 3 still names a GATEFILE")
    return problems


class TestFinalizeInputsBlock(LockCase):
    """D-01 / D-05 / D-18: the gate inputs are one fence calling the helper,
    with the 2.14.1 sentences byte for byte and no stderr redirect."""

    def setUp(self):
        self.text = read_prose(FINALIZE_MD)

    def _mutant(self, old, new=""):
        self.assertIn(old, self.text)
        mutant = self.text.replace(old, new, 1)
        self.assertNotEqual(mutant, self.text)
        return mutant

    def test_inputs_block_holds(self):
        self.assert_holds(inputs_block_holds, self.text)

    def test_mutant_inputs_block(self):
        line = inputs_call_line(self.text)
        self.assertTrue(line)
        with self.subTest("mutant: the helper's stderr sent to a side file"):
            self.assertTrue(line.endswith(")"))
            self.assert_trips(inputs_block_holds, self._mutant(
                line, line[:-1] + INPUTS_REDIRECT_MUTANT + ")"))
        for sentence in (COUNTS_HALT, GATE_HALT, REPORT_HALT):
            with self.subTest("mutant: reason clause added", s=sentence[30:60]):
                self.assert_trips(inputs_block_holds, self._mutant(
                    sentence, sentence[:-1] + " (see the .err file)."))
        with self.subTest("mutant: a switch slot defaulted"):
            self.assert_trips(inputs_block_holds, self._mutant(
                SWITCH_SLOTS[0], '--noninteractive "false"'))
        with self.subTest("mutant: the GATEFILE fence put back"):
            self.assert_trips(inputs_block_holds, self.text + (
                "\n```bash\nGATEFILE=$(mktemp)\n```\n"))
        with self.subTest("mutant: the counts fence put back"):
            self.assert_trips(inputs_block_holds, self.text + (
                "\n```bash\nCOUNTS_JSON=$(true)\n```\n"))
        with self.subTest("mutant: the helper called twice"):
            self.assert_trips(inputs_block_holds, self.text + "\n" + line)


# --------------------------------------------------------------------------- #
# Fresh-shell walk over the Finalize fences. Each fence runs in its own
# `bash -s` with only PATH, VC_ROOT, TMPDIR and STATE_FILE, the way separate
# Bash calls run: a temp path survives from one fence to the next only as a
# printed `NAME=<path>` literal substituted for `"$NAME"`.
# --------------------------------------------------------------------------- #
class TestFinalizeFreshShellWalk(LockCase):
    """FINL-01 / FINL-02 / FINX-03: the Finalize-inputs fence, run in a fresh
    shell with its three switch slots substituted, reaches the gate's
    decision; on the card route rows -> parse -> record-decisions -> the
    fence again (a NEW BLOBFILE=) -> write.

    ## Finalize fresh-shell walk

    Each fence runs in its own `bash -s` with exactly PATH, VC_ROOT, TMPDIR
    and STATE_FILE, in a scratch cwd (or a temp repo). The Write tool is
    simulated by writing JSON to the printed path. The helper's stderr is
    not redirected (D-18): on a counting refusal its one line stays on
    screen above the fence's sentence, as the 2.14.1 counts fence showed it.
    A fingerprint file that is gone, or holds an earlier attempt's map, when
    the helper reads it is simulated by a `mktemp` on PATH that removes or
    fills the file it made; a report-stage exit by a stand-in helper
    (`_stand_in_root`).
    """

    def setUp(self):
        self.text = read_prose(FINALIZE_MD)
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.walked = []

    def _run_fresh(self, script, state_file=SIX_ROW_FIXTURE, cwd=None,
                   path_dir=None, vc_root=PLUGIN_DIR):
        """(returncode, stdout, stderr) of `script` in a fresh bash."""
        tmpdir = tempfile.mkdtemp(dir=self.tmp)
        path = os.environ.get("PATH", "/usr/bin:/bin")
        if path_dir is not None:
            path = path_dir + os.pathsep + path
        env = {"PATH": path, "VC_ROOT": vc_root, "TMPDIR": tmpdir,
               "STATE_FILE": state_file}
        proc = subprocess.run(["bash", "-s"], input=textwrap.dedent(script),
                              env=env, cwd=cwd or tmpdir, capture_output=True,
                              text=True, timeout=120)
        return proc.returncode, proc.stdout, proc.stderr

    def _literal(self, fence, subs):
        """`fence` with each printed path substituted for `"$NAME"`."""
        for name, path in subs.items():
            ref = '"$%s"' % name
            self.assertIn(ref, fence, "fence does not read " + ref)
            fence = fence.replace(ref, '"%s"' % path)
        return fence

    def _walk(self, fence, subs=None, state_file=SIX_ROW_FIXTURE):
        """Run a prose fence fresh with literals; remember it for the
        closure check."""
        self.assertIsNotNone(fence)
        self.walked.append(fence)
        return self._run_fresh(self._literal(fence, subs or {}), state_file)

    def _mint(self, name, subs=None, state_file=SIX_ROW_FIXTURE):
        """Run the fence that prints `NAME=` fresh; return the printed path."""
        fence = _fence_holding(self.text, _print_line(name))
        self.assertIsNotNone(fence, "no Finalize fence prints %s=" % name)
        rc, out, err = self._walk(fence, subs, state_file)
        self.assertEqual(rc, 0, err)
        printed = _printed(out)
        self.assertIn(name, printed)
        return printed[name]

    def _inputs(self, state_file, text=None, switches=("false",) * 3,
                substitute=True, cwd=None, path_dir=None, vc_root=PLUGIN_DIR):
        """Run the Finalize-inputs fence of `text` fresh, its switch slots
        substituted -> (exit, printed BLOBFILE or None, result or None,
        stderr)."""
        fence = inputs_fence(self.text if text is None else text)
        self.assertIsNotNone(fence, "no Finalize fence calls "
                             "finalize_inputs.py")
        if substitute:
            for slot, value in zip(SWITCH_SLOTS, switches):
                self.assertIn(slot, fence)
                fence = fence.replace(slot,
                                      slot.replace("<true|false>", value))
        self.walked.append(fence)
        rc, out, err = self._run_fresh(fence, state_file, cwd=cwd,
                                       path_dir=path_dir, vc_root=vc_root)
        blob = _printed(out).get("BLOBFILE")
        result = None
        if rc == 0:
            result = json.loads(out.strip().splitlines()[-1])
            self.assertIn(result["next"], NEXT_ACTIONS)
        return rc, blob, result, err

    def _mktemp_shim(self, content=None):
        """A PATH directory whose `mktemp` makes the file as usual, then
        removes it (`content` None) or fills it with `content` before the
        path is printed: an attempt whose fingerprint file is gone, or holds
        an earlier attempt's map, when the helper reads it."""
        real = shutil.which("mktemp")
        self.assertIsNotNone(real)
        shim_dir = tempfile.mkdtemp(dir=self.tmp)
        if content is None:
            after = 'rm -f "$p"'
        else:
            self.assertNotIn("'", content)
            after = "printf '%%s' '%s' > \"$p\"" % content
        with open(os.path.join(shim_dir, "mktemp"), "w",
                  encoding="utf-8") as fh:
            fh.write('#!/bin/sh\np=$("%s" "$@") || exit 1\n%s\n'
                     "printf '%%s\\n' \"$p\"\n" % (real, after))
        os.chmod(os.path.join(shim_dir, "mktemp"), 0o755)
        return shim_dir

    def _stand_in_root(self, code, line=""):
        """A VC_ROOT holding a copy of the plugin's scripts/ in which
        finalize_inputs.py is a stand-in that writes `line` to stderr and
        exits `code`: the only way to drive a chosen helper exit (e.g. 5)
        through the real fence text."""
        root = tempfile.mkdtemp(dir=self.tmp)
        scripts = os.path.join(root, "scripts")
        os.makedirs(scripts)
        for name in os.listdir(HERE):
            if name.endswith(".py") and not name.startswith("test_"):
                shutil.copy(os.path.join(HERE, name), scripts)
        with open(os.path.join(scripts, "finalize_inputs.py"), "w",
                  encoding="utf-8") as fh:
            fh.write("import sys\nsys.stderr.write(%r)\nsys.exit(%d)\n"
                     % (line, code))
        return root

    @staticmethod
    def _write_json(path, obj):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)

    def _state_copy(self, source):
        path = os.path.join(self.tmp, "state.json")
        shutil.copyfile(source, path)
        return path

    def _report(self, state_file):
        rc, out, err = self._walk(_fence_holding(self.text, REPORT_CALL),
                                  {}, state_file)
        self.assertEqual(rc, 0, err)
        return json.loads(out.strip().splitlines()[0])

    def _answer_card(self, blob, state):
        """The unchanged card fences with the printed BLOBFILE literal: rows,
        the owner dismisses every row, parse, the payload copy and
        record-decisions. Returns the row hashes."""
        rc, out, err = self._walk(_fence_holding(self.text, ROWS_CALL),
                                  {"BLOBFILE": blob}, state)
        self.assertEqual(rc, 0, err)
        printed = _printed(out)
        with open(printed["ROWSFILE"], encoding="utf-8") as fh:
            rows = json.load(fh)
        self.assertTrue(rows["rows"])
        numbers = ",".join(str(r["n"]) for r in rows["rows"])
        self._write_json(printed["ANSWERFILE"],
                         {"q1": "dismiss %s -- walk" % numbers, "q2": None})
        parsefile = self._mint("PARSEFILE",
                               {"ROWSFILE": printed["ROWSFILE"],
                                "ANSWERFILE": printed["ANSWERFILE"]}, state)
        decfile = self._mint("DECFILE", {"PARSEFILE": parsefile}, state)
        with open(decfile, encoding="utf-8") as fh:
            payload = json.load(fh)
        hashes = sorted(r["stable_hash"] for r in rows["rows"])
        self.assertEqual(sorted(d["stable_hash"]
                                for d in payload["decisions"]), hashes)
        with open(state, encoding="utf-8") as fh:
            before = fh.read()
        rc, _, err = self._walk(_fence_holding(self.text, RECORD_CALL),
                                {"DECFILE": decfile}, state)
        self.assertEqual(rc, 0, err)
        with open(state, encoding="utf-8") as fh:
            self.assertNotEqual(fh.read(), before)
        return hashes

    def _assert_closed(self):
        """Every path a walked fence reads was made by a walked fence."""
        reads, made = set(), set()
        for fence in self.walked:
            reads |= set(_FILE_REF_RE.findall(fence))
            made |= set(MKTEMP_RE.findall(fence))
        self.assertEqual(reads - made - {"STATE_FILE"}, set())

    def _write_route_state(self):
        """The phase-45 loop state with every open finding dismissed through
        carry_state's own record_decisions (a state the helpers accept and
        whose gate outcome is `write`)."""
        state = load_fixture()
        counts = carry_state.finalize_counts(state)
        hashes = (counts["outstanding_cw_hashes"]
                  + counts["unacknowledged_medium_hashes"]
                  + counts["undecided_nv_hashes"])
        self.assertTrue(hashes)
        state = carry_state.record_decisions(state, {
            "at_pass": state["passes"][-1]["pass_number"],
            "decisions": [{"stable_hash": h, "decision": "dismiss",
                           "reason": "walk"} for h in hashes]})
        self.assertIsNotNone(state)
        path = os.path.join(self.tmp, "write-route.json")
        self._write_json(path, state)
        return path

    @staticmethod
    def _three(counts):
        return (counts["outstanding_cw"], counts["unacknowledged_medium"],
                counts["undecided_nv"])

    def test_walk_reaches_counts_gate_report(self):
        """The clean route: the fence prints BLOBFILE= and a result whose
        `next` is `write-review-md`, with the report bundle."""
        state = self._write_route_state()
        rc, blob, result, err = self._inputs(state)
        self.assertEqual(rc, 0, err)
        self.assertEqual(err, "")
        self.assertIsNotNone(blob)
        self.assertEqual((result["action"], result["next"]),
                         ("write", "write-review-md"))
        self.assertEqual(self._three(result["counts"]), (0, 0, 0))
        self.assertTrue(result["report"]["entries"])
        self.assertTrue(self._report(state)["entries"])
        self._assert_closed()

    def test_card_route_records_then_writes(self):
        """The card route end to end: `finalize-card`, the unchanged card
        fences with the printed BLOBFILE= literal, record-decisions (the one
        pre-`write` state write), then the fence again prints a NEW
        BLOBFILE= and `write-review-md`."""
        state = self._state_copy(SIX_ROW_FIXTURE)
        rc, blob1, result, err = self._inputs(state)
        self.assertEqual(rc, 0, err)
        self.assertEqual((result["action"], result["next"]),
                         ("outstanding-to-phase-5", "finalize-card"))
        self.assertIsNone(result["report"])
        self._answer_card(blob1, state)
        rc, blob2, result, err = self._inputs(state)
        self.assertEqual(rc, 0, err)
        self.assertNotEqual(blob2, blob1)
        self.assertEqual(result["next"], "write-review-md")
        self.assertEqual(self._three(result["counts"]), (0, 0, 0))
        self.assertTrue(result["report"]["entries"])
        self.assertTrue(self._report(state)["entries"])
        self._assert_closed()

    def test_counts_fence_without_literal_exits_two(self):
        """The fence run as written, its `"<true|false>"` slots not
        substituted: the helper refuses the usage (exit 2, nothing on its
        stderr) and the fence stops with the counting sentence alone (fail
        closed, never read as `false`). The printed fingerprint file is left
        empty."""
        rc, blob, result, err = self._inputs(SIX_ROW_FIXTURE,
                                             substitute=False)
        self.assertNotEqual(rc, 0)
        self.assertIsNone(result)
        self.assertEqual(err.splitlines(), [COUNTS_HALT])
        self.assertEqual(os.path.getsize(blob), 0)
        proc = subprocess.run(
            [sys.executable, os.path.join(HERE, "finalize_inputs.py"),
             "--state-file", SIX_ROW_FIXTURE, "--blob-out", blob]
            + [a for slot in SWITCH_SLOTS
               for a in (slot.split(" ")[0], "<true|false>")],
            capture_output=True, text=True, timeout=60)
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr),
                         (2, "", ""))

    def test_retry_mints_new_blobfile_after_missing_path(self):
        """D-07: the attempt's printed fingerprint file is gone when the
        helper reads it -> the fence exits non-zero with the counting
        sentence; the rebuild (the same fence once more) prints a NEW
        BLOBFILE= and reaches `write-review-md`."""
        state = self._write_route_state()
        rc, path1, result, err = self._inputs(
            state, path_dir=self._mktemp_shim())
        self.assertNotEqual(rc, 0)
        self.assertIsNone(result)
        self.assertEqual(err.splitlines()[-1], COUNTS_HALT)
        self.assertFalse(os.path.exists(path1))
        rc, path2, result, err = self._inputs(state)
        self.assertEqual(rc, 0, err)
        self.assertNotEqual(path1, path2)
        self.assertEqual(result["next"], "write-review-md")
        self.assert_holds(retry_rule_holds, self.text)

    def test_stale_earlier_attempt_file_does_not_govern(self):
        """Pitfall 5 / T-60-09: a last-pass fix-obsolete verdict verified
        against blob B_old. A fingerprint file that already holds an earlier
        attempt's map {file: B_old} would close it: the fence refuses it
        (exit non-zero, the file is never read or rewritten), and the fresh
        attempt keeps the finding open."""
        b_old = "b" * 40
        s = load_fixture()
        s["fix_verdicts"] = {ARCH_HASH: obsolete_verdict(
            at_pass=s["passes"][-1]["pass_number"], blob=b_old)}
        state = os.path.join(self.tmp, "verdict.json")
        self._write_json(state, s)
        earlier = json.dumps({ARCH_FILE: b_old})
        rc, stale, result, err = self._inputs(
            state, path_dir=self._mktemp_shim(earlier))
        self.assertNotEqual(rc, 0)
        self.assertIsNone(result)
        self.assertEqual(err.splitlines(),
                         [carry_state.REASON_HEAD_BLOBS.strip(), COUNTS_HALT])
        with open(stale, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), earlier)
        rc, fresh, result, err = self._inputs(state)
        self.assertEqual(rc, 0, err)
        self.assertNotEqual(fresh, stale)
        self.assertNotIn(ARCH_HASH, result["counts"]["verified_obsolete_hashes"])
        self.assertIn(ARCH_HASH, result["counts"]["outstanding_cw_hashes"])
        self.assert_holds(retry_rule_holds, self.text)

    def _counting_line_problems(self, text, case):
        """What the owner reads when the counting step refuses, through the
        fence of `text`: exactly the helper's one carry_state line, then the
        counting sentence (D-18), no traceback, no side file."""
        if case == "fingerprint file removed":
            state, shim = self._write_route_state(), self._mktemp_shim()
            want = [carry_state.REASON_HEAD_BLOBS.strip(), COUNTS_HALT]
        else:
            state = os.path.join(self.tmp, "not-json.json")
            with open(state, "w", encoding="utf-8") as fh:
                fh.write("not json")
            shim = None
            want = [carry_state.REASON_STATE_JSON.strip(), COUNTS_HALT]
        rc, blob, _, err = self._inputs(state, text=text, path_dir=shim)
        problems = []
        if rc == 0:
            problems.append("exit 0")
        if err.splitlines() != want:
            problems.append("stderr is %r, not %r" % (err, want))
        if "Traceback" in err:
            problems.append("a traceback reached the owner")
        if blob is None:
            problems.append("no BLOBFILE= printed")
        elif os.path.exists(blob + ".err"):
            problems.append("a <BLOBFILE>.err side file was written")
        return problems

    def test_counting_line_stays_on_screen(self):
        """D-18: the counting step's own refusal line is shown above the
        counting sentence, as the 2.14.1 counts fence showed it; it is
        compared with carry_state's constants, never retyped."""
        cases = ("fingerprint file removed", "state not JSON")
        for case in cases:
            with self.subTest(case):
                self.assertEqual(self._counting_line_problems(self.text, case),
                                 [])
        line = inputs_call_line(self.text)
        self.assertTrue(line.endswith(")"))
        mutant = self.text.replace(
            line, line[:-1] + INPUTS_REDIRECT_MUTANT + ")", 1)
        self.assertNotEqual(mutant, self.text)
        for case in cases:
            with self.subTest("mutant: stderr sent to <BLOBFILE>.err",
                              case=case):
                problems = self._counting_line_problems(mutant, case)
                self.assertTrue(any("side file" in p for p in problems),
                                problems)
                self.assertTrue(any("stderr is" in p for p in problems),
                                problems)
        self.assert_trips(inputs_block_holds, mutant)

    def _report_stop_problems(self, text):
        """The report stage (helper exit 5) through the fence of `text`: the
        fence exits 5, the stand-in's own line stays above the report
        sentence, and nothing else is shown."""
        marker = "stand-in helper ran\n"
        rc, _, result, err = self._inputs(
            SIX_ROW_FIXTURE, text=text,
            vc_root=self._stand_in_root(5, marker))
        problems = []
        if rc != 5:
            problems.append("exit %d, not 5" % rc)
        if result is not None:
            problems.append("a result was printed")
        if err.splitlines() != [marker.strip(), REPORT_HALT]:
            problems.append("stderr is %r" % err)
        return problems

    def test_report_failure_stops_at_once(self):
        """D-07: a report failure (helper exit 5) stops at once with the
        report sentence and exit 5, which the rebuild rule never retries;
        the gate stage (exit 4) maps to the gate sentence. Both run the real
        fence text over a stand-in helper."""
        self.assertEqual(self._report_stop_problems(self.text), [])
        with self.subTest("control: the stand-in is the helper that ran"):
            rc, _, _, err = self._inputs(
                SIX_ROW_FIXTURE, vc_root=self._stand_in_root(4, "gate-x\n"))
            self.assertEqual(rc, 1)
            self.assertEqual(err.splitlines(), ["gate-x", GATE_HALT])
        fence = inputs_fence(self.text)
        arm = fence[fence.index("  5)"):fence.index("  *)")]
        self.assertIn(REPORT_HALT, arm)
        with self.subTest("mutant: the 5) arm removed"):
            problems = self._report_stop_problems(
                self.text.replace(arm, "", 1))
            self.assertIn("exit 1, not 5", problems)
        with self.subTest("mutant: 5) mapped to the counting sentence"):
            problems = self._report_stop_problems(self.text.replace(
                arm, arm.replace(REPORT_HALT, COUNTS_HALT), 1))
            self.assertTrue(any("stderr is" in p for p in problems), problems)
        self.assert_holds(retry_rule_holds, self.text)

    def test_post_decision_rerun_decides_on_fresh_counts(self):
        """FINL-02 / WR-02: after the card answer is recorded, the result
        read before the card still holds the pre-answer counts (5, 1, 0) and
        `finalize-card`; running the fence again recounts (0, 0, 0) and the
        gate returns `write-review-md`. Step 3 must say to do the second."""
        state = self._state_copy(SIX_ROW_FIXTURE)
        rc, blob1, before, err = self._inputs(state)
        self.assertEqual(rc, 0, err)
        self.assertEqual(self._three(before["counts"]), (5, 1, 0))
        self.assertEqual(before["next"], "finalize-card")
        self._answer_card(blob1, state)
        rc, blob2, after, err = self._inputs(state)
        self.assertEqual(rc, 0, err)
        self.assertNotEqual(blob2, blob1)
        self.assertEqual(self._three(after["counts"]), (0, 0, 0))
        self.assertEqual(after["next"], "write-review-md")
        self.assertEqual(before["next"], "finalize-card")
        self._assert_closed()
        self.assert_holds(step3_rerun_rule_holds, self.text)

    def test_post_decision_recount_refingerprints_head(self):
        """FINL-02 / WR-01 / FINX-03 on a real repo: a last-pass fix-obsolete
        verdict verified against HEAD's blob closes its finding; the card
        decides the rest. Re-run with nothing edited, the fence returns
        `write-review-md`; after an edit made while the card was open, the
        re-run (a NEW BLOBFILE=) reopens the finding and never writes."""
        repo = gitfixture.make_repo(self.tmp)
        gitfixture.write(repo, ARCH_FILE, "fixed\n")
        gitfixture.git(repo, "add", "-A")
        gitfixture.git(repo, "commit", "-q", "-m", "init")
        blob = gitfixture.git(repo, "rev-parse",
                              "HEAD:" + ARCH_FILE).stdout.strip()
        s = load_fixture()
        last = s["passes"][-1]
        s["fix_verdicts"] = {ARCH_HASH: dict(
            obsolete_verdict(at_pass=last["pass_number"], blob=blob),
            head_sha=last["head_sha"])}
        state = os.path.join(self.tmp, "verdict.json")
        self._write_json(state, s)

        rc, blob1, result, err = self._inputs(state, cwd=repo)
        self.assertEqual(rc, 0, err)
        self.assertEqual(result["next"], "finalize-card")
        self.assertEqual(result["counts"]["verified_obsolete_hashes"],
                         [ARCH_HASH])
        decided = self._answer_card(blob1, state)
        self.assertNotIn(ARCH_HASH, decided)

        with self.subTest("control: nothing edited during the card"):
            rc, blob2, result, err = self._inputs(state, cwd=repo)
            self.assertEqual(rc, 0, err)
            self.assertNotEqual(blob2, blob1)
            self.assertEqual(result["next"], "write-review-md")

        gitfixture.write(repo, ARCH_FILE, "edited while the card was open\n")
        with self.subTest("edit during the card: the finding reopens"):
            rc, blob3, result, err = self._inputs(state, cwd=repo)
            self.assertEqual(rc, 0, err)
            self.assertNotIn(blob3, (blob1, blob2))
            self.assertNotEqual(result["next"], "write-review-md")
            self.assertEqual(result["next"], "finalize-card")
            self.assertEqual(result["counts"]["outstanding_cw_hashes"],
                             [ARCH_HASH])
            self.assertEqual(result["counts"]["verified_obsolete_hashes"], [])
        self._assert_closed()
        self.assert_holds(step3_rerun_rule_holds, self.text)


if __name__ == "__main__":
    unittest.main()
