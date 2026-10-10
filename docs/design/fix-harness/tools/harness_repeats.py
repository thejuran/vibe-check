"""harness_repeats.py — the question ledger: repeats and bounded retries.

A card asked again is a failure only when nothing relevant changed since it
was answered. A re-ask after a material change is allowed and still counted.

* `card_key(kind, rows, question_text)` identifies a card: its kind, the set
  of row identities (`file:line — title`, row numbers ignored) and the
  question text with pass numbers blanked.
* `evidence_fingerprint(head_sha, status_porcelain_v2, state_bytes)` is a
  sha256 over the HEAD sha, `git status --porcelain=v2` (any entry naming a
  `.turingmind/` path dropped) and the scope state file's bytes.
* `Ledger.observe(key, evidence, answered_as)` returns OK, REPEAT (same key
  already answered with identical evidence) or EXHAUSTED (more than
  `max_total` cards, or more than `max_same_kind` cards of one kind).
* `Ledger.observe_fix_loop_after_finalize(rows, evidence)` returns REPEAT when
  a fix-loop card asks about rows a finalize card already answered `fix` for,
  with identical evidence.

The counters (`total_questions`, `cards`, `by_kind`, `repeats`) feed the run
record. Pure: the driver collects the git and state strings and passes them
in.
"""

import collections
import hashlib
import re

OK = "ok"
REPEAT = "repeat"
EXHAUSTED = "exhausted"

FINALIZE_KIND = "finalize"
TOOL_DIR = ".turingmind"

_PASS_RE = re.compile(r"\b([Pp])ass [0-9]+")
_STATUS_SPLIT_RE = re.compile(r"[\0\n]")


def row_identity(row):
    """`file:line — title` for a row `(n, file, line, title, band)`."""
    _n, file, line, title = row[0], row[1], row[2], row[3]
    return "%s:%s — %s" % (file, "?" if line is None else line, title)


def card_key(kind, rows, question_text):
    """(kind, frozenset of row identities, question text with `Pass N` and
    `pass N` written as `Pass #` / `pass #`)."""
    return (kind, frozenset(row_identity(r) for r in rows),
            _PASS_RE.sub(lambda m: m.group(1) + "ass #", question_text))


def _names_tool_path(entry):
    for token in entry.split():
        if token == TOOL_DIR or token.startswith(TOOL_DIR + "/"):
            return True
    return False


def _field(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return b"%d:" % len(data) + data + b"\n"


def evidence_fingerprint(head_sha, status_porcelain_v2, state_bytes):
    """sha256 hex over HEAD, the status entries outside `.turingmind/` (NUL
    or newline separated), and the state file's bytes. Each field is length
    prefixed so fields cannot run together."""
    entries = [e for e in _STATUS_SPLIT_RE.split(status_porcelain_v2 or "")
               if e.strip() and not _names_tool_path(e)]
    digest = hashlib.sha256()
    digest.update(_field(head_sha or ""))
    digest.update(_field("\n".join(entries)))
    digest.update(_field(state_bytes or b""))
    return digest.hexdigest()


def _same_evidence(a, b):
    return a == b


def _positive_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("%s must be a positive integer" % name)
    return value


class Ledger:
    """Every card the run saw, the evidence it was answered under, and the
    bounds that end a run that keeps getting asked."""

    def __init__(self, max_total=12, max_same_kind=4):
        self.max_total = _positive_int(max_total, "max_total")
        self.max_same_kind = _positive_int(max_same_kind, "max_same_kind")
        self.total_questions = 0
        self.cards = 0
        self.by_kind = collections.Counter()
        self.repeats = 0
        self._answered = collections.defaultdict(list)
        self._finalize_fixed = []

    def observe(self, key, evidence, answered_as, questions=1,
                fixed_rows=()):
        """OK, REPEAT or EXHAUSTED for one card. Every call is counted.

        `questions` is the number of questions in the payload. For a finalize
        card, `fixed_rows` are the rows the answer chose to fix; a later
        fix-loop card asking about them is checked by
        `observe_fix_loop_after_finalize`.
        """
        kind = key[0]
        self.total_questions += questions
        self.cards += 1
        self.by_kind[kind] += 1
        seen = self._answered[key]
        repeated = any(_same_evidence(old, evidence) for old, _ in seen)
        seen.append((evidence, answered_as))
        if kind == FINALIZE_KIND and fixed_rows:
            self._finalize_fixed.append(
                (evidence, frozenset(row_identity(r) for r in fixed_rows)))
        if repeated:
            self.repeats += 1
            return REPEAT
        if (self.cards > self.max_total
                or self.by_kind[kind] > self.max_same_kind):
            return EXHAUSTED
        return OK

    def observe_fix_loop_after_finalize(self, rows, evidence):
        """REPEAT when every row of a fix-loop card was already answered `fix`
        at a finalize card under identical evidence; else OK."""
        wanted = frozenset(row_identity(r) for r in rows)
        if not wanted:
            return OK
        for old, fixed in self._finalize_fixed:
            if _same_evidence(old, evidence) and wanted <= fixed:
                self.repeats += 1
                return REPEAT
        return OK
