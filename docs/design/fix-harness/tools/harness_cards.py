"""harness_cards.py — classify and answer the plugin's cards from the seeded
finding alone, and classify the text a turn ends on.

Every option label comes from the plugin's own `batch_parse` tuples, so the
harness cannot disagree with the product it drives about what a card says.

* `classify_card(input_data)` names an AskUserQuestion payload by its option
  labels: FIX_LOOP, FIX_LOOP_SELECT, STOP, FINALIZE, or UNKNOWN. Anything the
  harness does not recognise (the first-run migration card, the estimate gate,
  an edited option list) is UNKNOWN.
* `answer_card(kind, input_data, seeded, seeded_resolved)` answers using only
  the seeded identity `(file, title)`. It never picks a row because the review
  found it. An UNKNOWN card, a missing seeded row, or a Stop card shown before
  the seeded finding resolved returns a `fail` reason and no answers.
* `classify_turn_end(text)` names the plugin one-liner a turn ended on.
  Anything else, including any prose question, is UNKNOWN: a would-be owner
  question.
* `next_owner_command(kind, mode)` is the command the owner would type next.

Pure and stdlib only: no I/O, no git, no network.
"""

import collections
import re
import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent.parent
PLUGIN_SCRIPTS_DIR = (HARNESS_DIR.parent.parent.parent
                      / "plugins" / "vibe-check" / "scripts").resolve()

if str(PLUGIN_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SCRIPTS_DIR))

import batch_parse  # noqa: E402

# Card kinds.
FIX_LOOP = "fix-loop"
FIX_LOOP_SELECT = "fix-loop-select"
STOP = "stop"
FINALIZE = "finalize"
UNKNOWN = "unknown"
CARD_KINDS = (FIX_LOOP, FIX_LOOP_SELECT, STOP, FINALIZE, UNKNOWN)

# Turn-end kinds.
NO_CHANGES = "no-changes"
NO_NEW_CHANGES = "no-new-changes"
NO_ISSUES = "no-issues"
PAUSED = "paused"
REVIEW_WRITTEN = "review-written"
TURN_END_KINDS = (NO_CHANGES, NO_NEW_CHANGES, NO_ISSUES, PAUSED,
                  REVIEW_WRITTEN, UNKNOWN)

# The labels the harness answers with, indexed from the plugin's tuples.
APPLY_ALL = batch_parse.FIX_LOOP_OPTIONS[0]
APPLY_SELECTED = batch_parse.FIX_LOOP_OPTIONS[1]
CLOSE_OUT = batch_parse.STOP_OPTIONS[0]
FIX_ALL = batch_parse.FINALIZE_Q1[2]
OUT_OF_SCOPE = batch_parse.FINALIZE_Q2[2]

# The reason recorded for every finalize row that is not the seeded finding.
# The typed answer `defer <n,...> -- <reason>` relies on batch_parse's inline
# `-- reason` grammar.
DEFER_REASON = "harness: not the seeded finding"

FAIL_UNEXPECTED_CARD = "unexpected card"
FAIL_MALFORMED_CARD = "malformed card"
FAIL_SEEDED_NOT_LISTED = "seeded finding not listed"
FAIL_SEEDED_AMBIGUOUS = "seeded finding matches more than one row"
FAIL_STOP_EARLY = "stop card before the seeded finding resolved"
FAIL_NO_ROWS = "finalize card lists no rows"
FAIL_TRUNCATED = "card list is truncated"
FAIL_UNPARSED_ROW = "card row could not be parsed"
FAIL_PAUSED = "run paused"
FAIL_TURN_END = "turn ended on unrecognised text"

Row = collections.namedtuple("Row", "n file line title band")
Decision = collections.namedtuple(
    "Decision", "answers questions_asked deferred_non_seeded fail")
Next = collections.namedtuple("Next", "command fail")

# A needs-verification row is never the seeded finding; finalize defers it by
# number like any other non-seeded row.
_BAND_WORDS = ("critical", "warning", "medium", "needs-verification")
_ROW_RE = re.compile(
    r"^#([0-9]+) (.+?):([0-9]+|\?) — (.*?) \(("
    + "|".join(_BAND_WORDS) + r")\)(?=$|\s)")
_SELECT_LABEL_RE = re.compile(r"^#([0-9]+) (\S+):([0-9]+|\?)$")
_TRUNCATED_RE = re.compile(r"^… and [0-9]+ more", re.MULTILINE)
_ELLIPSIS = "…"
_COMMANDS = {"review": "/vibe-check:review",
             "deep-review": "/vibe-check:deep-review"}


# --- classification --------------------------------------------------------

def _questions(input_data):
    """The question list when the payload is well formed, else None."""
    if not isinstance(input_data, dict):
        return None
    questions = input_data.get("questions")
    if not isinstance(questions, list) or not questions:
        return None
    for q in questions:
        if not isinstance(q, dict) or not isinstance(q.get("question"), str):
            return None
        options = q.get("options")
        if not isinstance(options, list) or not options:
            return None
        for opt in options:
            if not isinstance(opt, dict) or not isinstance(opt.get("label"),
                                                           str):
                return None
    return questions


def _labels(question):
    return [opt["label"] for opt in question["options"]]


def _label_set_is(question, expected):
    labels = _labels(question)
    return len(labels) == len(expected) and set(labels) == set(expected)


def classify_card(input_data):
    """FIX_LOOP | FIX_LOOP_SELECT | STOP | FINALIZE | UNKNOWN."""
    questions = _questions(input_data)
    if questions is None:
        return UNKNOWN
    first = questions[0]
    if len(questions) == 1:
        if _label_set_is(first, batch_parse.FIX_LOOP_OPTIONS):
            return FIX_LOOP
        if _label_set_is(first, batch_parse.STOP_OPTIONS):
            return STOP
    if (len(questions) <= 2
            and _label_set_is(first, batch_parse.FINALIZE_Q1)
            and (len(questions) == 1
                 or _label_set_is(questions[1], batch_parse.FINALIZE_Q2))):
        return FINALIZE
    if all(q.get("multiSelect") is True
           and all(batch_parse._LABEL_RE.match(label) for label in _labels(q))
           for q in questions):
        return FIX_LOOP_SELECT
    return UNKNOWN


# --- rows and the seeded identity ------------------------------------------

def parse_rows(question_text):
    """[Row(n, file, line or None, title, band)] from `#n file:line — title
    (band)` lines. Lines of any other shape are skipped."""
    rows = []
    for line in question_text.splitlines():
        m = _ROW_RE.match(line)
        if m:
            line_no = None if m.group(3) == "?" else int(m.group(3))
            rows.append(Row(int(m.group(1)), m.group(2), line_no,
                            m.group(4), m.group(5)))
    return rows


def _row_numbers(question_text):
    """Every line shaped like a row (`#n ...`), parsed or not."""
    return [int(m.group(1)) for m in
            (batch_parse._LABEL_RE.match(line)
             for line in question_text.splitlines()) if m]


def _title_matches(shown, seeded_title):
    """Exact title, or the plugin's compact cut (`prefix…`) of it."""
    if shown == seeded_title:
        return True
    if shown.endswith(_ELLIPSIS):
        prefix = shown[:-len(_ELLIPSIS)]
        return bool(prefix) and seeded_title.startswith(prefix)
    return False


def _find_seeded(rows, seeded):
    """(row, None) for the one row matching the seeded identity; (None, None)
    when no row matches; (None, reason) when more than one does."""
    file, title = seeded
    hits = [r for r in rows if r.file == file and _title_matches(r.title,
                                                                  title)]
    if len(hits) > 1:
        return None, FAIL_SEEDED_AMBIGUOUS
    return (hits[0] if hits else None), None


def _label_file(file):
    """The file as the plugin writes it into a selection label."""
    return "".join("_" if (c.isspace() or c == ",") else c for c in file)


def _select_rows(questions, seeded_title):
    """[(question_text, label, Row)] for every option of a selection card.

    The option description is `title` or `title — problem`; a description
    that opens with the seeded title is read as that title, any other is kept
    whole. Row.file is the label's file.
    """
    out = []
    for q in questions:
        for opt in q["options"]:
            m = _SELECT_LABEL_RE.match(opt["label"])
            if not m:
                continue
            desc = opt.get("description")
            desc = desc if isinstance(desc, str) else ""
            title = (seeded_title if (desc == seeded_title or desc.startswith(
                seeded_title + " — ")) else desc)
            out.append((q["question"], opt["label"],
                        Row(int(m.group(1)), m.group(2), None, title, None)))
    return out


# --- answers ---------------------------------------------------------------

def _answer_fix_loop(input_data, seeded, seeded_resolved):
    q = input_data["questions"][0]
    text = q["question"]
    if _TRUNCATED_RE.search(text):
        return {}, 0, FAIL_TRUNCATED
    row, fail = _find_seeded(parse_rows(text), seeded)
    if fail:
        return {}, 0, fail
    if row is None:
        return {}, 0, FAIL_SEEDED_NOT_LISTED
    choice = APPLY_ALL if len(_row_numbers(text)) == 1 else APPLY_SELECTED
    return {text: choice}, 0, None


def _answer_select(input_data, seeded, seeded_resolved):
    """Only the question holding the seeded row is answered; the other
    questions of a split selection card get no choice."""
    file, title = seeded
    entries = _select_rows(input_data["questions"], title)
    row, fail = _find_seeded([e[2] for e in entries],
                             (_label_file(file), title))
    if fail:
        return {}, 0, fail
    if row is None:
        return {}, 0, FAIL_SEEDED_NOT_LISTED
    question_text, label, _row = next(e for e in entries if e[2] is row)
    return {question_text: label}, 0, None


def _answer_stop(input_data, seeded, seeded_resolved):
    if not seeded_resolved:
        return {}, 0, FAIL_STOP_EARLY
    return {input_data["questions"][0]["question"]: CLOSE_OUT}, 0, None


def _numbers(ns):
    return ",".join(str(n) for n in ns)


def _answer_finalize(input_data, seeded, seeded_resolved):
    questions = input_data["questions"]
    q1 = questions[0]["question"]
    q2 = questions[1]["question"] if len(questions) > 1 else None
    if _TRUNCATED_RE.search(q1):
        return {}, 0, FAIL_TRUNCATED
    rows = parse_rows(q1)
    numbers = _row_numbers(q1)
    if not numbers:
        return {}, 0, FAIL_NO_ROWS
    if sorted(r.n for r in rows) != sorted(numbers):
        return {}, 0, FAIL_UNPARSED_ROW
    row, fail = _find_seeded(rows, seeded)
    if fail:
        return {}, 0, fail
    others = sorted(n for n in numbers if row is None or n != row.n)
    if row is not None and not others:
        q1_answer = FIX_ALL
    elif row is not None:
        q1_answer = "fix %d; defer %s -- %s" % (row.n, _numbers(others),
                                                DEFER_REASON)
    else:
        q1_answer = "defer %s -- %s" % (_numbers(others), DEFER_REASON)
    answers = {q1: q1_answer}
    if q2 is not None:
        answers[q2] = OUT_OF_SCOPE
    return answers, len(others), None


def _answer_unknown(input_data, seeded, seeded_resolved):
    return {}, 0, FAIL_UNEXPECTED_CARD


_ANSWERERS = {
    FIX_LOOP: _answer_fix_loop,
    FIX_LOOP_SELECT: _answer_select,
    STOP: _answer_stop,
    FINALIZE: _answer_finalize,
    UNKNOWN: _answer_unknown,
}


def answer_card(kind, input_data, seeded, seeded_resolved=False):
    """Decision(answers, questions_asked, deferred_non_seeded, fail).

    `seeded` is the accepted finding's `(file, title)`; no other input
    chooses a row. `answers` maps each answered question's text to a label or
    typed text. `questions_asked` counts every question in the payload, even
    on a failure. `deferred_non_seeded` counts finalize rows deferred because
    they are not the seeded finding.
    """
    questions = _questions(input_data)
    asked = len(questions) if questions is not None else 0
    if questions is None and kind != UNKNOWN:
        return Decision({}, asked, 0, FAIL_MALFORMED_CARD)
    answerer = _ANSWERERS.get(kind, _answer_unknown)
    answers, deferred, fail = answerer(input_data, seeded, seeded_resolved)
    if fail:
        return Decision({}, asked, 0, fail)
    return Decision(answers, asked, deferred, None)


# --- turn ends -------------------------------------------------------------

_TURN_END_TESTS = (
    (NO_CHANGES, lambda t: "No changes to review." in t),
    (NO_NEW_CHANGES,
     lambda t: re.search(r"No new changes since pass [0-9]+\.", t)),
    (NO_ISSUES, lambda t: "No issues to fix." in t),
    (PAUSED,
     lambda t: re.search(r"Paused\. Resume with `/vibe-check:(?:deep-)?review",
                         t)),
    (REVIEW_WRITTEN,
     lambda t: ".turingmind/REVIEW.md" in t and "gitignored" in t.lower()),
)


def classify_turn_end(text):
    """The plugin one-liner the turn ended on, or UNKNOWN.

    A turn whose last line ends in a question mark is UNKNOWN even when it
    also contains a one-liner, and so is text matching more than one kind:
    both would make the owner answer something.
    """
    if not isinstance(text, str) or not text.strip():
        return UNKNOWN
    lines = [line.strip() for line in text.strip().splitlines()
             if line.strip()]
    if lines[-1].endswith("?"):
        return UNKNOWN
    hits = [kind for kind, test in _TURN_END_TESTS if test(text)]
    return hits[0] if len(hits) == 1 else UNKNOWN


def next_owner_command(kind, mode, args=""):
    """Next(command, fail): the command the owner types next.

    The three one-liners lead to `--finalize` (the documented close-out after
    a loop that leaves nothing to review); a written REVIEW.md ends the run;
    a pause or unrecognised text fails it.
    """
    if mode not in _COMMANDS:
        raise ValueError("mode must be one of %s" % ", ".join(sorted(_COMMANDS)))
    if kind in (NO_CHANGES, NO_NEW_CHANGES, NO_ISSUES):
        parts = [_COMMANDS[mode]] + ([args.strip()] if args.strip() else [])
        return Next(" ".join(parts + ["--finalize"]), None)
    if kind == REVIEW_WRITTEN:
        return Next(None, None)
    if kind == PAUSED:
        return Next(None, FAIL_PAUSED)
    return Next(None, FAIL_TURN_END)
