"""batch_parse.py — deterministic grammar for the owner's batch-card answers.

Pure functions over a rows list. No I/O: this module never opens a file, never
reads argv, and never imports the state helper. The CLI that wraps it reads the
owner's text from a file, so owner text is never on a command line.

* `parse_answer(rows, q1, q2)` reads the finalize card. Q1 is a button label or
  typed text in the Mixed… grammar; Q2 is the one reason covering every
  dismissed and deferred row.
* `parse_selection(rows, labels=None, text=None)` maps a multi-select answer
  (labels shaped `#n file:line`) or a typed list (`1,3-5`) to row numbers by
  the leading number only, never by title text.

Grammar (case-insensitive, whitespace-tolerant, trailing ';' allowed):

    answer  := clause ( ';' clause )*
    clause  := verb targets | 'look' N
    verb    := 'fix' | 'defer' | 'dismiss'
    targets := 'rest' | item ( ',' item )*
    item    := N | N '-' N          1 <= N <= len(rows); ranges ascending

`rest` expands after the explicit items, over the unassigned rows whose band is
in `_rest_bands_for(verb)`: every band for `fix`, MEDIUM only for `dismiss` and
`defer`. A critical or warning row is therefore dismissed or deferred only when
the owner names it by number; otherwise it stays undecided and finalize stays
blocked.

The parse never guesses. Anything outside the grammar is refused with one fixed
string from REASONS, and no refusal ever contains owner text.
"""

import re

FIX_LOOP_OPTIONS = ("Apply all & rerun", "Apply selected…", "Skip & rerun",
                    "Stop here…")
STOP_OPTIONS = ("Close out", "Abandon", "I'll fix by hand, then rerun")
FINALIZE_Q1 = ("Dismiss all", "Defer all", "Fix all", "Mixed…")
FINALIZE_Q2 = ("False positive", "Accepted risk",
               "Out of scope for this milestone")

REASON_EMPTY = "refused: empty answer\n"
REASON_TOKEN = "refused: answer does not match the grammar\n"
REASON_RANGE = "refused: row number out of range\n"
REASON_DUPLICATE = "refused: a row is named more than once\n"
REASON_REST_TWICE = "refused: 'rest' may appear in only one clause\n"
REASON_LOOK_MIXED = "refused: 'look N' must be the only clause\n"
REASON_NO_REASON = "refused: dismiss/defer needs a reason\n"
REASON_LABEL = "refused: selection label does not start with '#n '\n"

REASONS = (
    REASON_EMPTY,
    REASON_TOKEN,
    REASON_RANGE,
    REASON_DUPLICATE,
    REASON_REST_TWICE,
    REASON_LOOK_MIXED,
    REASON_NO_REASON,
    REASON_LABEL,
)

VERBS = ("fix", "dismiss", "defer")
_BANDS = ("critical", "warning", "medium")
_CW_BANDS = ("critical", "warning")

# Each button is the same grammar the owner could type.
_BUTTON_TEXT = {
    FINALIZE_Q1[0]: "dismiss rest",
    FINALIZE_Q1[1]: "defer rest",
    FINALIZE_Q1[2]: "fix rest",
}
_MIXED = FINALIZE_Q1[3]

_CLAUSE_RE = re.compile(r"(fix|defer|dismiss)\s+(rest|[0-9,\s-]+)")
_LOOK_RE = re.compile(r"look\s+([0-9]+)")
_ITEM_RE = re.compile(r"([0-9]+)(?:-([0-9]+))?")
_LABEL_RE = re.compile(r"#([0-9]+) +\S")


class _Refusal(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _rest_bands_for(verb):
    """Bands a `rest` clause may reach. The bulk-safety rule lives here only."""
    if verb == "fix":
        return _BANDS
    return ("medium",)


def _assign(assigned, n, verb):
    """Assign row n to verb; False when n already has a verb."""
    if n in assigned:
        return False
    assigned[n] = verb
    return True


def _validate_rows(rows):
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("row must be a dict")
        n = row.get("n")
        if isinstance(n, bool) or not isinstance(n, int) or n != i + 1:
            raise ValueError("row numbers must be contiguous from 1")
        if not isinstance(row.get("stable_hash"), str) or not row["stable_hash"]:
            raise ValueError("row stable_hash must be a non-empty string")
        if row.get("band") not in _BANDS:
            raise ValueError("row band must be critical, warning or medium")


def _items(spec, count):
    """Row numbers named by an item list, in the order written."""
    out = []
    for item in spec.split(","):
        m = _ITEM_RE.fullmatch(item.strip())
        if not m:
            raise _Refusal(REASON_TOKEN)
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) is not None else lo
        if lo < 1 or hi > count or hi < lo:
            raise _Refusal(REASON_RANGE)
        out.extend(range(lo, hi + 1))
    return out


def _site(row):
    line = row.get("line")
    if isinstance(line, int) and not isinstance(line, bool):
        return "#%d %s:%d" % (row["n"], row.get("file", ""), line)
    return "#%d %s" % (row["n"], row.get("file", ""))


def _empty_result(**overrides):
    out = {"ok": True, "need_text": False, "look": None, "fix": [],
           "dismiss": [], "defer": [], "undecided": [], "echo": [],
           "reason": None}
    out.update(overrides)
    return out


def _parse_clauses(text):
    """Split normalized text into ('look', N) / (verb, 'rest'|spec) tuples."""
    body = text.strip().lower().rstrip(";").strip()
    if not body:
        raise _Refusal(REASON_EMPTY)
    clauses = []
    for clause in re.split(r"\s*;\s*", body):
        m = _CLAUSE_RE.fullmatch(clause)
        if m:
            clauses.append((m.group(1), m.group(2).strip()))
            continue
        m = _LOOK_RE.fullmatch(clause)
        if m:
            clauses.append(("look", int(m.group(1))))
            continue
        raise _Refusal(REASON_TOKEN)
    return clauses


def _answer(rows, q1, q2):
    if not isinstance(q1, str) or not q1.strip():
        raise _Refusal(REASON_EMPTY)
    stripped = q1.strip()
    if stripped == _MIXED:
        return _empty_result(need_text=True)
    text = _BUTTON_TEXT.get(stripped, stripped)
    clauses = _parse_clauses(text)
    count = len(rows)

    looks = [c for c in clauses if c[0] == "look"]
    if looks:
        if len(clauses) != 1:
            raise _Refusal(REASON_LOOK_MIXED)
        n = looks[0][1]
        if n < 1 or n > count:
            raise _Refusal(REASON_RANGE)
        return _empty_result(look=n)

    rest_verbs = [verb for verb, spec in clauses if spec == "rest"]
    if len(rest_verbs) > 1:
        raise _Refusal(REASON_REST_TWICE)

    assigned = {}
    for verb, spec in clauses:
        if spec == "rest":
            continue
        for n in _items(spec, count):
            if not _assign(assigned, n, verb):
                raise _Refusal(REASON_DUPLICATE)
    rest_verb = rest_verbs[0] if rest_verbs else None
    if rest_verb is not None:
        bands = _rest_bands_for(rest_verb)
        for row in rows:
            if row["n"] not in assigned and row["band"] in bands:
                assigned[row["n"]] = rest_verb

    by_verb = {verb: [row for row in rows if assigned.get(row["n"]) == verb]
               for verb in VERBS}
    undecided = [row for row in rows if row["n"] not in assigned]

    reason = None
    if by_verb["dismiss"] or by_verb["defer"]:
        if not isinstance(q2, str) or not q2.strip():
            raise _Refusal(REASON_NO_REASON)
        reason = q2.strip()

    echo = []
    for verb in VERBS:
        if by_verb[verb]:
            echo.append("%s: %s" % (verb, ", ".join(_site(r) for r in by_verb[verb])))
    if undecided:
        echo.append("still open: %s" % ", ".join(_site(r) for r in undecided))
    open_cw = [r for r in undecided if r["band"] in _CW_BANDS]
    if open_cw:
        if rest_verb in ("dismiss", "defer"):
            echo.append("%d critical/warning not covered by '%s rest'"
                        " — still open; finalize stays blocked"
                        % (len(open_cw), rest_verb))
        else:
            echo.append("%d critical/warning undecided"
                        " — still open; finalize stays blocked" % len(open_cw))
    open_medium = [r for r in undecided if r["band"] == "medium"]
    if open_medium:
        echo.append("%d medium undecided — still open; finalize stays blocked"
                    % len(open_medium))

    return _empty_result(
        fix=[r["stable_hash"] for r in by_verb["fix"]],
        dismiss=[r["stable_hash"] for r in by_verb["dismiss"]],
        defer=[r["stable_hash"] for r in by_verb["defer"]],
        undecided=[r["stable_hash"] for r in undecided],
        echo=echo,
        reason=reason,
    )


def parse_answer(rows, q1, q2):
    """Parse the finalize card answer; a dict on success, (None, reason) else.

    Raises ValueError for a malformed rows list (a programming error, not an
    owner error).
    """
    _validate_rows(rows)
    try:
        return _answer(rows, q1, q2)
    except _Refusal as refusal:
        return (None, refusal.reason)


def _selection_numbers(rows, labels, text):
    if labels is not None:
        if isinstance(labels, str):
            labels = [part for part in labels.split(",") if part.strip()]
        if not isinstance(labels, (list, tuple)) or not labels:
            raise _Refusal(REASON_EMPTY)
        numbers = []
        for label in labels:
            if not isinstance(label, str):
                raise _Refusal(REASON_LABEL)
            m = _LABEL_RE.match(label.strip())
            if not m:
                raise _Refusal(REASON_LABEL)
            n = int(m.group(1))
            if n < 1 or n > len(rows):
                raise _Refusal(REASON_RANGE)
            numbers.append(n)
        return numbers
    if not isinstance(text, str) or not text.strip():
        raise _Refusal(REASON_EMPTY)
    return _items(text.strip(), len(rows))


def parse_selection(rows, labels=None, text=None):
    """Map a multi-select answer or typed list to rows; dict or (None, reason).

    Raises ValueError for a malformed rows list.
    """
    _validate_rows(rows)
    try:
        numbers = _selection_numbers(rows, labels, text)
    except _Refusal as refusal:
        return (None, refusal.reason)
    if len(set(numbers)) != len(numbers):
        return (None, REASON_DUPLICATE)
    ordered = sorted(numbers)
    return {"ok": True, "rows": ordered,
            "hashes": [rows[n - 1]["stable_hash"] for n in ordered]}
