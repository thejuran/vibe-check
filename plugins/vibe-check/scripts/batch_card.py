"""batch_card.py — the owner's batch card as deterministic reads.

Renders only the card's own text, decides numbering/tags/parse, writes
nothing; prose calls by path; owner text by file.

The two prose files that ask the owner one card per pass (the fix loop and
Finalize) call this helper for everything they must not compute themselves:

  rows              The numbered card rows. Numbering is decided here once, so
                    the list the owner reads and the parse of the owner's
                    answer always agree. Each row is tagged with
                    `pending_since` (unchanged since pass N, decision pending)
                    and `stale` (the owner's earlier decision no longer
                    matches the evidence it judged). The document also
                    carries `card_text`: the numbered list, rendered here,
                    that the prose copies verbatim INTO the AskUserQuestion
                    question, so the owner sees the rows on the card itself
                    (text printed only inside a tool call is collapsed by
                    the terminal and never seen). `list_text` is the full
                    rendering; `card_text` equals it when it fits the card
                    budget, else a compact form, else a compact form cut
                    short with `card_text_truncated` true.
  decisions-report  Every owner decision with its current / superseded /
                    orphan status, for REVIEW.md.

Open, closed and pending are never re-derived here: they come from
carry_state (one closure rule). This module never writes a file and never
mutates the state it reads; it prints JSON on stdout.

FAIL CLOSED. Any refusal prints exactly one fixed line from REASONS (or a
carry_state reason passed through) on stderr, prints NOTHING on stdout and
exits 2. Reasons never contain a hash, a title, a path or owner text.

  select-questions  The AskUserQuestion shape for "Apply selected…": at most
                    four multi-select questions of 2-4 options, labels
                    `#n file:line` (never a title, never a comma). With
                    one row (mode none) there is no second card and
                    `answer` is that row's label, the selection to send.
  select            A multi-select / typed-list answer -> row numbers + hashes.
  payload           THE fix-agent dispatch for the selected rows: each unit is
                    the selected record's own defect, copied from the state.
  parse             The finalize card answer -> fix / dismiss / defer lists,
                    the record-decisions payload and the fix targets.
  resolve           A plain-English answer's references -> current row
                    numbers and a grammar string for `parse` to validate.

FIX ROUTING. A fix target is not an undecided row. When the owner dismissed
an absorbed obligation's lead and then chose to fix the still-open member,
`rows --subset` returns the lead's row (the member is routed through it,
`lead_selected` false) even though a current decision closes the lead, and
`payload` dispatches only the member's own defect. The lead's decision is
never reopened: this module writes nothing.

CLI (stdin = the state JSON for `rows`, `payload` and `decisions-report`;
owner text only ever arrives in the --answer file):

    python3 batch_card.py rows --mode fix-loop [--subset PATH] < state.json
    python3 batch_card.py rows --mode finalize --head-blobs PATH < state.json
    python3 batch_card.py select-questions --rows ROWS.json
    python3 batch_card.py select --rows ROWS.json --answer ANS.json
    python3 batch_card.py payload --rows ROWS.json --answer ANS.json < state.json
    python3 batch_card.py parse --rows ROWS.json --answer ANS.json
    python3 batch_card.py decisions-report < state.json
    python3 batch_card.py resolve --rows ROWS.json --answer REFS.json \
        [--prior-rows OLD_ROWS.json]

Selection answers (select, payload): {"labels": [...] | "a, b"}, {"text":
"1,3-5"}, {"all": true} or {"none": true} — the typed-mode buttons map to
all / none. Finalize answers (parse): {"q1": str, "q2": str | null}.
References (resolve): {"refs": [...], "reason": str | null, "close_out":
bool}; see `resolve_refs`.

stdlib only; imports {json, os, sys} plus the sibling modules carry_state and
batch_parse.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import carry_state  # noqa: E402  (sibling module: the one closure rule)
import batch_parse  # noqa: E402  (sibling module: the answer grammar)

MODES = ("fix-loop", "finalize")
_BAND_RANK = {"critical": 0, "warning": 1, carry_state.NV_BAND: 2, "medium": 3}

SUBCOMMANDS = ("rows", "select-questions", "select", "payload", "parse",
               "decisions-report", "resolve")
# The ONLY flags this CLI accepts. No flag ever carries owner text, a title or
# a reason: such text arrives in a file whose path is passed here.
KNOWN_FLAGS = ("--mode", "--head-blobs", "--subset", "--rows", "--answer",
               "--prior-rows")
# subcommand -> (required flags, optional flags)
_FLAGS_BY_SUBCOMMAND = {
    "rows": (("--mode",), ("--head-blobs", "--subset")),
    "select-questions": (("--rows",), ()),
    "select": (("--rows", "--answer"), ()),
    "payload": (("--rows", "--answer"), ()),
    "parse": (("--rows", "--answer"), ()),
    "decisions-report": ((), ()),
    "resolve": (("--rows", "--answer"), ("--prior-rows",)),
}
# Subcommands that read the state JSON on stdin.
_STATE_SUBCOMMANDS = ("rows", "payload", "decisions-report")

USAGE = ("usage: batch_card.py rows --mode fix-loop [--subset PATH]"
         " | rows --mode finalize --head-blobs PATH"
         " | select-questions --rows PATH | select --rows PATH --answer PATH"
         " | payload --rows PATH --answer PATH | parse --rows PATH"
         " --answer PATH | decisions-report"
         " | resolve --rows PATH --answer PATH [--prior-rows PATH]"
         "  (state on stdin for rows, payload, decisions-report)\n")

REASON_STATE_JSON = carry_state.REASON_STATE_JSON
REASON_HEAD_BLOBS = carry_state.REASON_HEAD_BLOBS
REASON_SUBSET = "refused: subset file is missing or not a list of hashes\n"
REASON_SUBSET_EMPTY = "refused: subset names no last-pass finding\n"
REASON_ROWS = "refused: rows file is missing or malformed\n"
REASON_ANSWER = "refused: answer file is missing or malformed\n"
REASON_ROWS_STATE = "refused: rows file does not match this state\n"
REASON_REFS = "refused: refs file is missing or malformed\n"
REASON_PRIOR_ROWS = "refused: prior rows file is missing or malformed\n"
REASON_PRIOR_NEEDED = "refused: a prior-card reference needs --prior-rows\n"

REASONS = (
    USAGE,
    REASON_STATE_JSON,
    REASON_HEAD_BLOBS,
    REASON_SUBSET,
    REASON_SUBSET_EMPTY,
    REASON_ROWS,
    REASON_ANSWER,
    REASON_ROWS_STATE,
    REASON_REFS,
    REASON_PRIOR_ROWS,
    REASON_PRIOR_NEEDED,
)

# AskUserQuestion limits: 1-4 questions, 2-4 options each, header <= 12.
_MAX_OPTIONS = 4
_MAX_QUESTIONS = 4
_MAX_MULTISELECT = _MAX_OPTIONS * _MAX_QUESTIONS
_DESCRIPTION_PROBLEM_CHARS = 80
# The card's question text carries the numbered list. A budget keeps a long
# list from swamping the card; past it the list is compacted, then cut short.
CARD_TEXT_MAX_CHARS = 2400
_LIST_PROBLEM_CHARS = 120
_COMPACT_TITLE_CHARS = 60
TYPED_ALL = "All listed"
TYPED_NONE = "None — skip & rerun"


def _is_str_map(value):
    return isinstance(value, dict) and all(
        isinstance(k, str) and isinstance(v, str) for k, v in value.items())


def _str_or(value, default):
    return value if isinstance(value, str) else default


def _sort_key(row):
    line = row.get("line")
    has_line = isinstance(line, int) and not isinstance(line, bool)
    file = row.get("file")
    return (_BAND_RANK.get(row.get("band"), len(_BAND_RANK)),
            not isinstance(file, str), _str_or(file, ""),
            not has_line, line if has_line else 0,
            row["stable_hash"])


# --------------------------------------------------------------------------- #
# Tags.
# --------------------------------------------------------------------------- #
def _same_hash_stale(record, state):
    """The `stale` tag for a record whose own decision went stale, or None."""
    if carry_state.decision_state(record, state) != "stale":
        return None
    h = record["stable_hash"]
    decision = state.get("decisions", {}).get(h)
    via, prior = "same_hash", h
    if not isinstance(decision, dict):
        # A finding that inherits a decision recorded as covering it (it
        # split out of the decided row) shows that decision when it reopens.
        covering = carry_state.covering_decision(record, state)
        if covering is None:
            return None
        prior, decision = covering
        via = "covering"
    if via == "covering":
        # The band the inherited decision was taken at is the one recorded
        # for THIS finding (the same value carry_state compares), never the
        # decided row's evidence band; a legacy entry without one falls back
        # to the covering decision's band, as the comparator does.
        entry = carry_state.covering_entry(record, state)
        entry_band = entry.get("band") if isinstance(entry, dict) else None
        was_band = (entry_band if isinstance(entry_band, str)
                    else decision.get("band"))
    else:
        evidence = decision.get("evidence")
        was_band = (evidence.get("band") if isinstance(evidence, dict)
                    else decision.get("band"))
    cause = carry_state.stale_cause(record, state)
    tag = {
        "cause": cause,
        "decision": decision.get("decision"),
        "reason": decision.get("reason"),
        "at_pass": decision.get("at_pass"),
        "was_band": was_band,
        "via": via,
        "prior_hash": prior,
        "gained": carry_state.gained_lanes(record, state),
    }
    if cause == "joined":
        # Both values come from carry_state, the same functions the reopen
        # test reads, so the card and the comparator cannot disagree.
        tag["covered"] = carry_state.covered_count(record, state)
        tag["joined"] = carry_state.newcomer_lanes(record, state)
    return tag


def _row(record, state, lead_titles, pending_since):
    """One card row for a carry_state record (row or member sidecar)."""
    absorbed = record.get("absorbed_into")
    absorbed = absorbed if isinstance(absorbed, str) else None
    # An absorbed record's defect text lives on the member dict that carries
    # it (members[].obligation holds identity and scoring only); a row's own
    # text lives on the row. Never the lead's text for a member.
    source = (_unit_source(record, state["passes"][-1]) if absorbed
              else record) or {}
    return {
        "n": 0,
        "stable_hash": record["stable_hash"],
        "band": record["band"],
        "file": record.get("file"),
        "line": record.get("line"),
        "title": record.get("title"),
        "problem": _str_or(source.get("problem"), ""),
        "agent": record.get("agent"),
        "absorbed_into": absorbed,
        "lead_title": lead_titles.get(absorbed) if absorbed else None,
        "pending_since": pending_since.get(record["stable_hash"]),
        "stale": _same_hash_stale(record, state),
    }


def _context(state):
    """(last pass, records, lead titles, pending map) for a valid state."""
    last = state["passes"][-1]
    records = carry_state.open_findings(state)
    lead_titles = {f["stable_hash"]: f.get("title") for f in last["findings"]}
    pending_since = {p["stable_hash"]: p["since_pass"]
                     for p in carry_state.pending(state)}
    return last, records, lead_titles, pending_since


# --------------------------------------------------------------------------- #
# rows
# --------------------------------------------------------------------------- #
def build_rows(state, mode, head_blobs=None, subset=None):
    """({"at_pass", "mode", "rows"}, None) or (None, reason).

    fix-loop: every open, unclosed (no head blobs) critical/warning/
    needs-verification/medium record. finalize: exactly finalize_counts'
    outstanding critical/warning, undecided needs-verification and
    unacknowledged medium hashes (head blobs honoured). Rows are ordered
    band -> file -> line (None last) -> hash and numbered from 1.
    With `subset` (fix-loop only): the dispatch targets from
    `resolve_fix_targets`, in subset order; the document then carries
    `"subset": true`, so Apply all sends every row the owner named.
    """
    reason = carry_state.state_reason(state)
    if reason is not None:
        return None, reason
    last, records, lead_titles, pending_since = _context(state)
    if subset is not None:
        # Dispatch targets, NOT undecided rows: the closed-record filter
        # below must never touch them (an owner may fix through a lead
        # whose own decision closes it).
        rows = resolve_fix_targets(state, subset)
        if not rows:
            return None, REASON_SUBSET_EMPTY
    else:
        if mode == "finalize":
            counts = carry_state.finalize_counts(state, head_blobs)
            wanted = set(counts["outstanding_cw_hashes"]
                         + counts["undecided_nv_hashes"]
                         + counts["unacknowledged_medium_hashes"])
            chosen = [r for r in records if r["stable_hash"] in wanted]
        else:
            chosen = [r for r in records
                      if r["band"] in carry_state.BLOCKING_BANDS
                      and not carry_state.is_closed(r, state, None)]
        rows = [_row(r, state, lead_titles, pending_since) for r in chosen]
        rows.sort(key=_sort_key)
    # Row membership is fixed above; the linkage only annotates.
    links = successor_links(state, rows)
    for row in rows:
        if row["stale"] is None and row["stable_hash"] in links:
            row["stale"] = links[row["stable_hash"]]
    for i, row in enumerate(rows):
        row["n"] = i + 1
    doc = {"at_pass": last["pass_number"], "mode": mode, "rows": rows}
    if subset is not None:
        doc["subset"] = True
    doc.update(card_texts(rows, mode))
    doc.update(option_texts(rows, mode, subset is not None))
    return doc, None


def resolve_fix_targets(state, subset):
    """The fix-loop rows for an owner-chosen subset of hashes (a valid state).

    A subset hash naming a lead or plain row yields that row with
    `lead_selected` true; a member obligation's hash folds into its lead's
    row as a `routed_members` entry (creating the lead row with
    `lead_selected` false). The row is kept even when a current decision
    closes it (`lead_closed` says so). Hashes naming nothing are dropped.
    Rows are in subset order, unnumbered. Never touches `decisions`.
    """
    _, records, lead_titles, pending_since = _context(state)
    leads = {}
    members = {}
    for rec in records:
        if isinstance(rec.get("absorbed_into"), str):
            members[rec["stable_hash"]] = rec
        else:
            leads[rec["stable_hash"]] = rec
    rows = []
    by_lead = {}

    def lead_row(h):
        if h not in by_lead:
            row = _row(leads[h], state, lead_titles, pending_since)
            row["lead_closed"] = carry_state.is_closed(leads[h], state, None)
            row["lead_selected"] = False
            row["routed_members"] = []
            by_lead[h] = row
            rows.append(row)
        return by_lead[h]

    for h in subset:
        if h in leads:
            lead_row(h)["lead_selected"] = True
        elif h in members and members[h]["absorbed_into"] in leads:
            row = lead_row(members[h]["absorbed_into"])
            routed = [m["stable_hash"] for m in row["routed_members"]]
            if h not in routed:
                row["routed_members"].append(
                    {"stable_hash": h, "title": members[h].get("title")})
    return rows


def _earlier_identity(state, h):
    """(file, title) of the most recent finding row with hash `h` in any
    pass, else of the most recent member obligation with that hash; None
    when the hash was never seen. Earlier passes are read defensively."""
    passes = state.get("passes")
    for pass_ in reversed(passes):
        findings = pass_.get("findings") if isinstance(pass_, dict) else None
        if not isinstance(findings, list):
            continue
        for f in findings:
            if isinstance(f, dict) and f.get("stable_hash") == h:
                return f.get("file"), f.get("title")
    for pass_ in reversed(passes):
        findings = pass_.get("findings") if isinstance(pass_, dict) else None
        if not isinstance(findings, list):
            continue
        for f in findings:
            members = f.get("members") if isinstance(f, dict) else None
            if not isinstance(members, list):
                continue
            for m in members:
                obligation = m.get("obligation") if isinstance(m,
                                                               dict) else None
                if (isinstance(obligation, dict)
                        and obligation.get("stable_hash") == h):
                    return m.get("file"), m.get("title")
    return None


def _claim_key(claim):
    at_pass, h = claim
    return (-at_pass if _is_count(at_pass) else 1, h)


def successor_links(state, rows):
    """{row hash: stale tag} linking an orphaned decision to its re-hashed
    successor row (an edit to the decided line changes the hash).

    annotation only — never closes, never changes finalize_counts.

    An orphan is a decision whose hash is no open record. Its earlier
    identity is the (file, title) it last had. Its candidate successors are
    the rows in `rows` with that file and title and no decision or legacy
    acknowledgment of their own. Exactly one candidate -> the orphan claims
    it; more than one -> it annotates nothing. Several orphans claiming one
    row: the highest decision `at_pass` wins, then the smallest hash.
    """
    decisions = state.get("decisions", {})
    acks = state.get("medium_acknowledgments", {})
    open_hashes = {r["stable_hash"] for r in carry_state.open_findings(state)}
    claims = {}
    for h in sorted(decisions):
        decision = decisions[h]
        if not isinstance(decision, dict) or h in open_hashes:
            continue
        identity = _earlier_identity(state, h)
        if identity is None:
            continue
        candidates = [r for r in rows
                      if (r.get("file"), r.get("title")) == identity
                      and r["stable_hash"] not in decisions
                      and r["stable_hash"] not in acks]
        if len(candidates) == 1:
            claims.setdefault(candidates[0]["stable_hash"], []).append(
                (decision.get("at_pass"), h))
    links = {}
    for row_hash, row_claims in claims.items():
        _, h = min(row_claims, key=_claim_key)
        decision = decisions[h]
        evidence = decision.get("evidence")
        links[row_hash] = {
            "cause": "code",
            "decision": decision.get("decision"),
            "reason": decision.get("reason"),
            "at_pass": decision.get("at_pass"),
            "was_band": (evidence.get("band") if isinstance(evidence, dict)
                         else decision.get("band")),
            "via": "successor",
            "prior_hash": h,
        }
    return links


# --------------------------------------------------------------------------- #
# Card text: the numbered list the owner reads ON the card.
# --------------------------------------------------------------------------- #
def _one_line(value):
    """`value` as one printable line: every whitespace or control character
    becomes a space, so a title can never start a fake row of its own."""
    if not isinstance(value, str):
        return ""
    out = "".join(" " if (c.isspace() or ord(c) < 32 or 127 <= ord(c) < 160)
                  else c for c in value)
    return " ".join(out.split())


def _cut(text, limit):
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _where(row):
    file = _one_line(row.get("file")) or "?"
    line = row.get("line")
    has_line = isinstance(line, int) and not isinstance(line, bool)
    return "%s:%s" % (file, str(line) if has_line else "?")


def _decision_word(decision):
    return {"dismiss": "dismissed", "defer": "deferred"}.get(
        decision, _one_line(decision) or "decided")


def _kind_word(stale):
    return _decision_word(stale.get("decision"))


def _was(stale):
    reason = _one_line(stale.get("reason"))
    word = _kind_word(stale)
    return "(was: %s — %s)" % (word, reason) if reason else "(was: %s)" % word


def _lanes(value):
    """Reviewer lane names, each flattened to one line; empty names dropped."""
    lanes = [_one_line(v) for v in value] if isinstance(value, list) else []
    return [v for v in lanes if v]


def _joined_note(stale, compact):
    """The note for a decided row a new concern joined: how many findings
    here the decision already covered, its reason, and the new lanes."""
    count = stale.get("covered")
    count = count if isinstance(count, int) and not isinstance(
        count, bool) else 0
    lanes = _lanes(stale.get("joined"))
    concern = ("new concerns from %s joined it" if len(lanes) > 1
               else "a new concern from %s joined it") % ", ".join(lanes)
    head = " — %d %s here already %s" % (
        count, "finding" if count == 1 else "findings", _kind_word(stale))
    if compact:
        return "%s; %s" % (head, concern)
    reason = _one_line(stale.get("reason"))
    if not reason:
        return "%s; %s" % (head, concern)
    return "%s (your reason: %s); %s" % (head, reason, concern)


def _stale_suffix(row, stale, compact):
    at_pass = stale.get("at_pass")
    cause = stale.get("cause")
    gained = _lanes(stale.get("gained"))
    if cause == "nearby":
        return (" — code next to it changed since your decision on pass %s"
                % at_pass if compact else
                " — code next to it changed since your decision on pass "
                "%s %s" % (at_pass, _was(stale)))
    if cause == "severity" and gained:
        plural = "" if len(gained) > 1 else "s"
        return (" — severity rose since your decision on pass %s" % at_pass
                if compact else
                " — severity rose (%s → %s) since your decision on pass "
                "%s: %s now also report%s it %s"
                % (_one_line(stale.get("was_band")) or "?",
                   _one_line(row.get("band")), at_pass, ", ".join(gained),
                   plural, _was(stale)))
    if cause == "severity":
        return (" — severity changed since your decision on pass %s" % at_pass
                if compact else
                " — severity changed (%s → %s) since your decision on pass "
                "%s %s" % (_one_line(stale.get("was_band")) or "?",
                           _one_line(row.get("band")), at_pass, _was(stale)))
    if cause == "joined":
        return _joined_note(stale, compact)
    return (" — code changed since your decision on pass %s" % at_pass
            if compact else
            " — code changed since your decision on pass %s %s"
            % (at_pass, _was(stale)))


def _suffixes(row, compact):
    """The suffixes after a row's first line, in the prose's order:
    absorbed, pending, stale."""
    out = []
    if row.get("absorbed_into"):
        out.append(" (absorbed)" if compact else
                   ' (absorbed into "%s" — decided on its own)'
                   % _one_line(row.get("lead_title")))
    pending = row.get("pending_since")
    if pending is not None:
        out.append(" — pending since pass %s" % pending if compact else
                   " — unchanged since pass %s, decision pending" % pending)
    stale = row.get("stale")
    if isinstance(stale, dict):
        out.append(_stale_suffix(row, stale, compact))
    return "".join(out)


def _quoted_titles(members, compact):
    titles = []
    for m in members:
        title = _one_line(m.get("title"))
        titles.append('"%s"' % (_cut(title, _COMPACT_TITLE_CHARS)
                                if compact else title))
    return ", ".join(titles)


def _row_lines(row, mode, compact):
    """The list lines for one row (the first line, plus the problem line in
    finalize mode when the full form is rendered)."""
    title = _one_line(row.get("title"))
    if compact:
        title = _cut(title, _COMPACT_TITLE_CHARS)
    routed = row.get("routed_members") or []
    head = "#%d %s" % (row["n"], _where(row))
    if row.get("lead_selected") is False and routed:
        first = ('%s — fixing absorbed %s (routed through "%s", which is not '
                 "being fixed)" % (head, _quoted_titles(routed, compact),
                                   title))
    else:
        first = "%s — %s (%s)" % (head, title, _one_line(row.get("band")))
        if routed:
            first += (" — also fixing absorbed %s through this row"
                      % _quoted_titles(routed, compact))
    if row.get("lead_closed") is True:
        first += " (your earlier decision on this row stays)"
    first += _suffixes(row, compact)
    lines = [first]
    if mode == "finalize" and not compact:
        problem = row.get("problem")
        problem = problem.splitlines()[0] if (isinstance(problem, str)
                                              and problem.strip()) else ""
        problem = _one_line(problem)[:_LIST_PROBLEM_CHARS]
        if problem:
            lines.append("    " + problem)
    return lines


def _render(rows, mode, compact):
    return "\n".join(line for row in rows
                     for line in _row_lines(row, mode, compact))


def card_texts(rows, mode, limit=CARD_TEXT_MAX_CHARS):
    """{"card_text", "list_text", "card_text_truncated"} for numbered rows.

    list_text is the full rendering. card_text is list_text when it fits
    `limit`; else the compact rendering (titles cut, no problem line, short
    tags); else as many compact rows as fit, then one closing line naming
    the rows left out, with card_text_truncated true.
    """
    full = _render(rows, mode, compact=False)
    if len(full) <= limit:
        return {"card_text": full, "list_text": full,
                "card_text_truncated": False}
    compact = _render(rows, mode, compact=True)
    if len(compact) <= limit:
        return {"card_text": compact, "list_text": full,
                "card_text_truncated": False}
    lines = [_row_lines(row, mode, compact=True)[0] for row in rows]
    kept = 0
    used = 0
    # The compact form did not fit, so at least one row is always left out.
    while kept < len(rows) - 1:
        tail = _truncation_tail(rows, kept + 1)
        if used + len(lines[kept]) + 1 + len(tail) > limit:
            break
        used += len(lines[kept]) + 1
        kept += 1
    return {"card_text": "\n".join(lines[:kept]
                                   + [_truncation_tail(rows, kept)]),
            "list_text": full, "card_text_truncated": True}


def option_texts(rows, mode, subset):
    """{"nv_rows", "bulk_fix_text"} for the card's bulk-fix option.

    "Apply all & rerun" (fix-loop) and "Fix all" (finalize) never send a
    needs-verification row: `select` drops `carry_state.NV_BAND` rows and the
    finalize `fix rest` reaches only critical/warning/medium. nv_rows lists
    the row numbers so left out, read from the same `carry_state.NV_BAND`
    literal `select` uses, and bulk_fix_text names them by number in the
    option description. On a subset card every row was named by the owner
    and is sent, so nothing is left out. The text is built only from row
    numbers and fixed wording, never from diff-authored row fields.
    """
    nv_rows = [] if subset else [r["n"] for r in rows
                                 if r["band"] == carry_state.NV_BAND]
    numbers = ", ".join("#%d" % n for n in nv_rows)
    one = len(nv_rows) == 1
    if mode == "finalize":
        text = "Fix every critical, warning and medium row."
        if nv_rows:
            text += (" Needs-verification %s (%s) %s not included — name %s "
                     "by number in Mixed…"
                     % ("row" if one else "rows", numbers,
                        "is" if one else "are", "it" if one else "them"))
    else:
        text = "every listed row"
        if nv_rows:
            text += (" except Needs-verification %s %s — confirm, dismiss or "
                     "defer %s by number in Other (`fix N`, `dismiss N -- "
                     "reason`, `defer N -- reason`)"
                     % ("row" if one else "rows", numbers,
                        "it" if one else "those"))
    return {"nv_rows": nv_rows, "bulk_fix_text": text}


def _truncation_tail(rows, kept):
    """The closing line of a cut-short card list: the rows left out."""
    return ("… and %d more (#%d-#%d) — the full list is printed above this "
            "card." % (len(rows) - kept, rows[kept]["n"], rows[-1]["n"]))


# --------------------------------------------------------------------------- #
# Answer side: select-questions, select, parse, payload.
# --------------------------------------------------------------------------- #
def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_rows_doc(doc):
    """True for a rows document shaped like `rows` output."""
    if not (isinstance(doc, dict) and _is_count(doc.get("at_pass"))
            and isinstance(doc.get("rows"), list)):
        return False
    if "subset" in doc and not isinstance(doc["subset"], bool):
        return False
    for i, row in enumerate(doc["rows"]):
        if not isinstance(row, dict):
            return False
        n = row.get("n")
        if isinstance(n, bool) or n != i + 1:
            return False
        h = row.get("stable_hash")
        if not (isinstance(h, str) and h and isinstance(row.get("band"), str)):
            return False
        if "lead_selected" in row and not isinstance(row["lead_selected"],
                                                     bool):
            return False
        routed = row.get("routed_members", [])
        if not (isinstance(routed, list) and all(
                isinstance(m, dict) and isinstance(m.get("stable_hash"), str)
                for m in routed)):
            return False
    return True


def _label_file(file):
    """The file as it appears in an option label: no whitespace and no comma
    (multi-select answers come back comma-joined)."""
    if not isinstance(file, str) or not file:
        return "?"
    return "".join("_" if (c.isspace() or c == ",") else c for c in file)


def _label(row):
    line = row.get("line")
    has_line = isinstance(line, int) and not isinstance(line, bool)
    return "#%d %s:%s" % (row["n"], _label_file(row.get("file")),
                          str(line) if has_line else "?")


def _description(row):
    title = _str_or(row.get("title"), "")
    problem = _str_or(row.get("problem"), "")[:_DESCRIPTION_PROBLEM_CHARS]
    return "%s — %s" % (title, problem) if problem else title


def select_questions(rows):
    """The "Apply selected…" sub-card shape for `rows`.

    N <= 1: mode none — no second card; `answer` is the selection to send:
    the one row's own label (picking Apply selected… on a one-row card picks
    that row, exactly as ticking it would on a larger card, so a
    Needs-verification row is sent too), or `{"none": true}` with no rows.
    2 <= N <= 16: ceil(N/4) multi-select questions, balanced so every question
    has >= 2 options. N > 16: mode typed — one single-choice question whose two
    buttons map to all / none and whose Other box takes a typed list such as
    1,3-5.
    """
    count = len(rows)
    if count <= 1:
        answer = {"labels": [_label(rows[0])]} if rows else {"none": True}
        return {"mode": "none", "questions": [], "answer": answer}
    if count > _MAX_MULTISELECT:
        return {"mode": "typed", "questions": [{
            "question": ("%d findings are more than one card can list. Type "
                         "the row numbers to apply in Other (e.g. 1,3-5), or "
                         "pick a button." % count),
            "header": "Fix rows",
            "multiSelect": False,
            "options": [
                {"label": TYPED_ALL,
                 "description": "Apply every listed finding, then rerun"},
                {"label": TYPED_NONE,
                 "description": "Apply nothing this pass, then rerun"},
            ]}]}
    groups = -(-count // _MAX_OPTIONS)
    base, extra = divmod(count, groups)
    sizes = [base + 1 if i < extra else base for i in range(groups)]
    assert all(2 <= size <= _MAX_OPTIONS for size in sizes)
    questions = []
    start = 0
    for size in sizes:
        chunk = rows[start:start + size]
        start += size
        first, last = chunk[0]["n"], chunk[-1]["n"]
        questions.append({
            "question": ("Which of findings #%d-#%d should the fix agent "
                         "apply? Select any." % (first, last)),
            "header": "Fix %d-%d" % (first, last),
            "multiSelect": True,
            "options": [{"label": _label(r), "description": _description(r)}
                        for r in chunk],
        })
    return {"mode": "multiselect", "questions": questions}


def _valid_select_answer(answer):
    if not (isinstance(answer, dict) and len(answer) == 1):
        return False
    key, value = next(iter(answer.items()))
    if key in ("all", "none"):
        return value is True
    if key == "text":
        return isinstance(value, str)
    if key == "labels":
        return isinstance(value, str) or (
            isinstance(value, list) and all(isinstance(v, str)
                                            for v in value))
    return False


def select(rows, answer, subset=False):
    """({"hashes", "rows"}, None) or (None, reason) for a selection answer.

    `{"all": true}` on an ordinary card selects every row except
    needs-verification rows: an unverified hypothesis is fixed only when the
    owner names it. On a subset card (`subset` true) every row was already
    named by the owner, so all of them are sent.
    """
    if not _valid_select_answer(answer):
        return None, REASON_ANSWER
    if "all" in answer:
        numbers = [r["n"] for r in rows
                   if subset or r["band"] != carry_state.NV_BAND]
    elif "none" in answer:
        numbers = []
    else:
        # Selection maps by the leading #n only; the band is irrelevant to
        # it, so a non-blocking band (a routing lead) is normalized here.
        plain = [{"n": r["n"], "stable_hash": r["stable_hash"],
                  "band": r["band"] if r["band"] in carry_state.BLOCKING_BANDS
                  else "medium"} for r in rows]
        result = batch_parse.parse_selection(plain,
                                             labels=answer.get("labels"),
                                             text=answer.get("text"))
        if isinstance(result, tuple):
            return None, result[1]
        numbers = result["rows"]
    return {"hashes": [rows[n - 1]["stable_hash"] for n in numbers],
            "rows": numbers}, None


def _dedup(hashes):
    seen = set()
    out = []
    for h in hashes:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def _valid_parse_answer(answer):
    return (isinstance(answer, dict) and "q1" in answer
            and set(answer) <= {"q1", "q2"}
            and isinstance(answer["q1"], str)
            and (answer.get("q2") is None or isinstance(answer["q2"], str)))


def parse(rows_doc, answer):
    """(batch_parse result + payload + fix_targets, None) or (None, reason).

    payload is the record-decisions input (dismiss entries then defer
    entries, each in row order, one shared reason) or None when nothing was
    dismissed or deferred. fix_targets are the owner-chosen fix hashes in
    row order — never a lead the owner did not pick.
    """
    if not _valid_parse_answer(answer):
        return None, REASON_ANSWER
    try:
        result = batch_parse.parse_answer(rows_doc["rows"], answer["q1"],
                                          answer.get("q2"))
    except ValueError:
        return None, REASON_ROWS
    if isinstance(result, tuple):
        return None, result[1]
    decisions = (
        [{"stable_hash": h, "decision": "dismiss", "reason": result["reason"]}
         for h in result["dismiss"]]
        + [{"stable_hash": h, "decision": "defer", "reason": result["reason"]}
           for h in result["defer"]])
    payload = ({"at_pass": rows_doc["at_pass"], "decisions": decisions}
               if decisions else None)
    return dict(result, payload=payload,
                fix_targets=_dedup(result["fix"]),
                echo_text=echo_text(result)), None


# --------------------------------------------------------------------------- #
# resolve: a plain-English answer's references -> rows -> grammar for parse.
# --------------------------------------------------------------------------- #
REF_KINDS = ("number", "prior_number", "title", "marker")
REF_MARKER_REMAINING = "remaining"
REF_MARKERS = (REF_MARKER_REMAINING, "band:critical", "band:warning",
               "band:medium", "band:" + carry_state.NV_BAND, "pending",
               "changed", "absorbed")
REF_STATUSES = ("one", "none", "many", "count_mismatch", "conflict", "bulk",
                "blocked", "count_needed")
_REF_KEYS = {"number": {"verb", "kind", "n"},
             "prior_number": {"verb", "kind", "n"},
             "title": {"verb", "kind", "text"},
             "marker": {"verb", "kind", "marker"}}
_REFS_DOC_KEYS = {"refs", "reason", "close_out"}
_CANDIDATE_TITLE_CHARS = 80
# A title token is a maximal run of letters or digits. Filler is determiners
# and card nouns only; prepositions are not filler and match as words.
_TITLE_FILLER = frozenset((
    "the", "a", "an", "this", "that", "these", "those", "one", "ones",
    "issue", "issues", "bug", "bugs", "finding", "findings", "row", "rows",
    "item", "items", "thing", "things", "problem", "problems"))
# `changed` names rows whose card line says the finding changed; a `joined`
# row's line says a new concern joined it instead.
_CHANGED_CAUSES = ("code", "nearby", "severity")


def _is_positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _valid_ref(ref):
    if not (isinstance(ref, dict) and ref.get("verb") in batch_parse.VERBS
            and ref.get("kind") in REF_KINDS):
        return False
    kind = ref["kind"]
    keys = set(ref)
    if kind == "marker":
        if keys - {"count"} != _REF_KEYS[kind]:
            return False
        return (ref["marker"] in REF_MARKERS
                and ("count" not in ref or _is_positive_int(ref["count"])))
    if keys != _REF_KEYS[kind]:
        return False
    if kind == "title":
        return isinstance(ref["text"], str) and bool(ref["text"].split())
    return _is_positive_int(ref["n"])


def _valid_refs_doc(doc):
    """True for a refs document: exact keys, known verbs/kinds/markers,
    counts and row numbers >= 1, non-blank title text."""
    return (isinstance(doc, dict) and "refs" in doc
            and set(doc) <= _REFS_DOC_KEYS
            and isinstance(doc["refs"], list) and bool(doc["refs"])
            and all(_valid_ref(ref) for ref in doc["refs"])
            and (doc.get("reason") is None or isinstance(doc["reason"], str))
            and isinstance(doc.get("close_out", False), bool))


def _title_tokens(text):
    """The case-folded letter/digit runs of the one-line form of `text`."""
    spaced = "".join(ch if ch.isalnum() else " "
                     for ch in _one_line(text).casefold())
    return spaced.split()


def _match_title(rows, text):
    """Rows whose title holds every non-filler token of `text` as a whole
    token (maximal letter/digit runs, case-folded), in any order, never as
    a substring; filler-only text matches no row. Titles are diff data:
    matched as text, never interpreted."""
    wanted = [t for t in _title_tokens(text) if t not in _TITLE_FILLER]
    if not wanted:
        return []
    return [r for r in rows
            if set(_title_tokens(r.get("title"))).issuperset(wanted)]


def _marker_rows(rows, marker):
    """Rows carrying a card marker (band, pending, changed, absorbed)."""
    if marker.startswith("band:"):
        band = marker[len("band:"):]
        return [r for r in rows if r["band"] == band]
    if marker == "pending":
        return [r for r in rows if r.get("pending_since") is not None]
    if marker == "changed":
        return [r for r in rows if isinstance(r.get("stale"), dict)
                and r["stale"].get("cause") in _CHANGED_CAUSES]
    if marker == "absorbed":
        return [r for r in rows if r.get("absorbed_into") is not None]
    return []


def _count_status(matched, count):
    """A described group is clear when it names rows and, when the owner
    stated a count, exactly that many (D-02, D-16)."""
    if count is not None and len(matched) != count:
        return "count_mismatch"
    return "one" if matched else "none"


def _needs_count(ref, matched):
    """True when an uncounted described group would dismiss or defer a row
    that `rest` could not reach for that verb (critical, warning or
    needs-verification): the owner must state how many (D-18)."""
    if ref.get("count") is not None or ref["verb"] not in ("dismiss", "defer"):
        return False
    bulk_bands = batch_parse._rest_bands_for(ref["verb"])
    return any(r["band"] not in bulk_bands for r in matched)


def _remap_prior(prior_row, rows):
    """Current rows that are `prior_row`'s finding: the same stable_hash,
    else the same (file, title) — the successor_links identity rule (D-07).
    """
    same_hash = [r for r in rows
                 if r["stable_hash"] == prior_row["stable_hash"]]
    if same_hash:
        return same_hash
    identity = (prior_row.get("file"), prior_row.get("title"))
    return [r for r in rows if (r.get("file"), r.get("title")) == identity]


def _claim(claimed, numbers):
    """Claim `numbers` for one reference; False when any is already claimed
    by an earlier reference (nothing is claimed then)."""
    if claimed & set(numbers):
        return False
    claimed.update(numbers)
    return True


def _candidate(row):
    return {"label": _label(row),
            "title": _cut(_one_line(row.get("title")),
                          _CANDIDATE_TITLE_CHARS)}


def _ref_result(status, rows=(), candidates=()):
    return {"status": status, "rows": sorted(r["n"] for r in rows),
            "candidates": [_candidate(r) for r in candidates]}


def _grammar_for(clauses, reason):
    """The grammar for (verb, [numbers] | "rest") clauses: verbs in the
    order fix, dismiss, defer; numbers ascending; ` -- reason` only when a
    reason was given."""
    parts = []
    for verb in batch_parse.VERBS:
        numbers = sorted({n for v, spec in clauses
                          if v == verb and spec != "rest" for n in spec})
        if numbers:
            parts.append("%s %s" % (verb, ",".join(str(n) for n in numbers)))
        if (verb, "rest") in clauses:
            parts.append("%s rest" % verb)
    grammar = "; ".join(parts)
    return grammar + " -- " + reason if reason else grammar


def _resolve_one(ref, rows, prior_rows, claimed):
    """The result of one non-`remaining` reference; claims its rows."""
    kind = ref["kind"]
    if kind == "number":
        matched = [r for r in rows if r["n"] == ref["n"]]
        status = "one" if matched else "none"
    elif kind == "prior_number":
        if ref["n"] > len(prior_rows):
            matched = []
        else:
            matched = _remap_prior(prior_rows[ref["n"] - 1], rows)
        status = {0: "none", 1: "one"}.get(len(matched), "many")
    elif kind == "title":
        matched = _match_title(rows, ref["text"])
        status = {0: "none", 1: "one"}.get(len(matched), "many")
    else:
        matched = _marker_rows(rows, ref["marker"])
        if _needs_count(ref, matched):
            return _ref_result("count_needed", candidates=matched)
        status = _count_status(matched, ref.get("count"))
    if status == "many":
        return _ref_result("many", candidates=matched)
    if status == "count_mismatch":
        return _ref_result("count_mismatch", candidates=matched)
    if status == "none":
        return _ref_result("none")
    if not _claim(claimed, [r["n"] for r in matched]):
        return _ref_result("conflict", candidates=matched)
    return _ref_result("one", rows=matched)


def _resolve_remaining(ref, rows, claimed):
    """The result of a `remaining` reference over the still-unclaimed rows.
    With a count it names them by number, at any band, only when exactly
    that many remain (D-16); without one it is the parser's `rest` (D-04).
    """
    unclaimed = [r for r in rows if r["n"] not in claimed]
    count = ref.get("count")
    if count is None:
        reached = [r for r in unclaimed
                   if r["band"] in batch_parse._rest_bands_for(ref["verb"])]
        _claim(claimed, [r["n"] for r in reached])
        return _ref_result("bulk", rows=reached)
    status = _count_status(unclaimed, count)
    if status == "count_mismatch":
        return _ref_result("count_mismatch", candidates=unclaimed)
    if status == "none":
        return _ref_result("none")
    _claim(claimed, [r["n"] for r in unclaimed])
    return _ref_result("one", rows=unclaimed)


def _is_stale(rows_doc, prior_rows_doc):
    return (prior_rows_doc["at_pass"] != rows_doc["at_pass"]
            or [r["stable_hash"] for r in prior_rows_doc["rows"]]
            != [r["stable_hash"] for r in rows_doc["rows"]])


def resolve_refs(rows_doc, refs_doc, prior_rows_doc=None):
    """(result, None) or (None, reason): the owner's references, resolved.

    D-01: `parse` stays the only gate. This function decides nothing: it
    maps each reference to current rows, builds a grammar string from the
    clear ones, and dry-runs `parse` on it (parse writes nothing). The
    caller acts only on what parse then accepts.

    Owner text arrives only via the refs file (written with the Write tool,
    never on a command line). Finding titles are matched as data.

    Each reference gets a status: `one` (exactly one set of rows), `none`,
    `many` (candidates listed as `#n file:line` + title), `count_mismatch`
    (a stated count differs from the matched count, D-02/D-16; candidates
    are the matched rows), `conflict` (a row an earlier reference already
    named), `bulk` (`remaining` with no count -> the parser's `rest`, whose
    bulk rules then apply, D-04), `blocked` (`remaining` cannot be computed
    because another reference is unclear) or `count_needed` (a described
    group with no stated count that would dismiss or defer a critical,
    warning or needs-verification row, D-18; candidates are the matched
    rows). Non-`remaining` references are
    resolved first, in order; then each `remaining` reference over the rows
    still unclaimed.

    `prior_number` references a row of an older card (`prior_rows_doc`):
    it is re-mapped by stable_hash, then by unique (file, title), and
    `stale` reports whether the card changed since (D-07).

    `grammar` is built when every reference is `one` or `bulk` (even with no
    reason, so the follow-up can show it); `ok` is true only when, in
    addition, there is no conflict and parse accepts the grammar.
    `needs_reason` is true when parse refused only for a missing reason.
    `close_out` is echoed back unchanged.
    """
    if not _valid_refs_doc(refs_doc):
        return None, REASON_REFS
    refs = refs_doc["refs"]
    if prior_rows_doc is None and any(r["kind"] == "prior_number"
                                      for r in refs):
        return None, REASON_PRIOR_NEEDED
    rows = rows_doc["rows"]
    prior_rows = prior_rows_doc["rows"] if prior_rows_doc is not None else []
    results = [None] * len(refs)
    claimed = set()
    for i, ref in enumerate(refs):
        if not (ref["kind"] == "marker"
                and ref["marker"] == REF_MARKER_REMAINING):
            results[i] = _resolve_one(ref, rows, prior_rows, claimed)
    blocked = any(r is not None and r["status"] != "one" for r in results)
    for i, ref in enumerate(refs):
        if results[i] is None:
            results[i] = (_ref_result("blocked") if blocked
                          else _resolve_remaining(ref, rows, claimed))
    verbs = {verb: sorted(n for ref, res in zip(refs, results)
                          if ref["verb"] == verb for n in res["rows"])
             for verb in batch_parse.VERBS}
    grammar = None
    parse_reason = None
    if all(res["status"] in ("one", "bulk") for res in results):
        clauses = [(ref["verb"],
                    "rest" if res["status"] == "bulk" else res["rows"])
                   for ref, res in zip(refs, results)]
        grammar = _grammar_for(clauses, _one_line(refs_doc.get("reason")))
        _parsed, parse_reason = parse(rows_doc, {"q1": grammar, "q2": None})
    return {
        "ok": grammar is not None and parse_reason is None,
        "stale": (prior_rows_doc is not None
                  and _is_stale(rows_doc, prior_rows_doc)),
        "needs_reason": parse_reason == batch_parse.REASON_NO_REASON,
        "close_out": refs_doc.get("close_out", False),
        "refs": results,
        "verbs": verbs,
        "grammar": grammar,
        "parse_reason": parse_reason,
    }, None


def echo_text(result):
    """The parse echo as one block of message text: the `echo` lines, then
    "Reason: …" when a reason applies. The prose puts this block where the
    owner sees it (the next printed message, or the fix-loop card)."""
    lines = [_one_line(line) for line in result.get("echo") or []]
    reason = _one_line(result.get("reason"))
    if reason:
        lines.append("Reason: " + reason)
    return "\n".join(lines)


def _unit_source(record, last):
    """The dict a dispatch unit is copied from: the row itself, or for an
    absorbed obligation the member dict that carries it (never the lead)."""
    lead_hash = record.get("absorbed_into")
    if not isinstance(lead_hash, str):
        return record
    for finding in last["findings"]:
        if finding["stable_hash"] != lead_hash:
            continue
        for member in finding.get("members", []):
            obligation = member.get("obligation")
            if (isinstance(obligation, dict)
                    and obligation.get("stable_hash") == record["stable_hash"]):
                return member
    return None


def _unit(record, last):
    source = _unit_source(record, last)
    if source is None:
        return None
    fix_hint = source.get("fix_hint")
    unit = {
        "id": record["stable_hash"],
        "file": source.get("file"),
        "line": source.get("line"),
        "title": source.get("title"),
        "problem": _str_or(source.get("problem"), ""),
        "current_code": _str_or(source.get("current_code"), ""),
        "fix_hint": fix_hint if isinstance(fix_hint, str) else None,
        "why_it_matters": _str_or(source.get("why_it_matters"), ""),
    }
    # A confirmed needs-verification item carries its trigger, path and
    # consequence to the fix agent (string fields only; data, not prompt).
    nv = source.get("needs_verification")
    if isinstance(nv, dict):
        unit["needs_verification"] = {k: v for k, v in nv.items()
                                      if isinstance(k, str)
                                      and isinstance(v, str)}
    return unit


def build_payload(state, rows_doc, answer):
    """({"sent", "findings"}, None) or (None, reason): the fix-agent dispatch.

    Every field is copied from the state's last pass, never from the rows
    file. A subset row contributes its lead only when `lead_selected`, then
    each routed member's own defect; a member sidecar row contributes the
    member dict. The rows file must describe this state's last pass.
    """
    selection, reason = select(rows_doc["rows"], answer,
                               subset=rows_doc.get("subset", False))
    if reason is not None:
        return None, reason
    last = state["passes"][-1]
    if rows_doc["at_pass"] != last["pass_number"]:
        return None, REASON_ROWS_STATE
    by_hash = {r["stable_hash"]: r for r in carry_state.open_findings(state)}
    units = []
    for n in selection["rows"]:
        row = rows_doc["rows"][n - 1]
        record = by_hash.get(row["stable_hash"])
        if record is None:
            return None, REASON_ROWS_STATE
        targets = []
        if "lead_selected" in row:
            if row["lead_selected"]:
                targets.append(record)
            for member in row.get("routed_members", []):
                member_record = by_hash.get(member["stable_hash"])
                if (member_record is None or member_record.get(
                        "absorbed_into") != row["stable_hash"]):
                    return None, REASON_ROWS_STATE
                targets.append(member_record)
        else:
            targets.append(record)
        for target in targets:
            unit = _unit(target, last)
            if unit is None:
                return None, REASON_ROWS_STATE
            units.append(unit)
    findings = []
    seen = set()
    for unit in units:
        if unit["id"] not in seen:
            seen.add(unit["id"])
            findings.append(unit)
    return {"sent": [u["id"] for u in findings], "findings": findings}, None


# --------------------------------------------------------------------------- #
# decisions-report
# --------------------------------------------------------------------------- #
def _report_entry(h, decision, status, record):
    return {
        "stable_hash": h,
        "decision": decision.get("decision"),
        "reason": decision.get("reason"),
        "at_pass": decision.get("at_pass"),
        "band": decision.get("band"),
        "status": status,
        "file": record.get("file") if record else None,
        "line": record.get("line") if record else None,
        "title": record.get("title") if record else None,
        "agent": record.get("agent") if record else None,
    }


def decisions_report(state):
    """{"entries": [...]} for every owner decision, or None when malformed.

    current    the decision closes its open last-pass record;
    superseded a `history` entry, or a decision whose evidence went stale;
    orphan     the decided hash is no open last-pass record (the site
               re-hashed or left the diff).
    Entries are in hash order; each decision is followed by its history.
    """
    if carry_state.state_reason(state) is not None:
        return None
    by_hash = {r["stable_hash"]: r for r in carry_state.open_findings(state)}
    decisions = state.get("decisions", {})
    entries = []
    for h in sorted(decisions):
        decision = decisions[h]
        if not isinstance(decision, dict):
            continue
        record = by_hash.get(h)
        if record is None:
            status = "orphan"
        elif carry_state.decision_state(record, state) == "current":
            status = "current"
        else:
            status = "superseded"
        entries.append(_report_entry(h, decision, status, record))
        history = decision.get("history")
        if isinstance(history, list):
            for old in history:
                if isinstance(old, dict):
                    entries.append(_report_entry(h, old, "superseded", record))
    return {"entries": entries}


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def parse_argv(argv):
    """(subcommand, {flag: value}) or None on any usage error. An unknown,
    repeated or valueless flag is an error, never a silent default."""
    if not argv or argv[0] not in SUBCOMMANDS:
        return None
    sub = argv[0]
    required, optional = _FLAGS_BY_SUBCOMMAND[sub]
    values = {}
    rest = argv[1:]
    i = 0
    while i < len(rest):
        token = rest[i]
        if token not in KNOWN_FLAGS or token not in required + optional:
            return None
        if i + 1 >= len(rest) or token in values:
            return None
        values[token] = rest[i + 1]
        i += 2
    if any(f not in values for f in required):
        return None
    if sub == "rows":
        mode = values["--mode"]
        if mode not in MODES:
            return None
        # finalize rows ALWAYS take the blob map (verified-obsolete closure);
        # fix-loop rows never do, and a subset only routes fix-loop rows.
        if mode == "finalize" and ("--head-blobs" not in values
                                   or "--subset" in values):
            return None
        if mode == "fix-loop" and "--head-blobs" in values:
            return None
    return sub, values


def _refuse(reason):
    sys.stderr.write(reason)
    return 2


def _read_subset(path):
    subset = carry_state.read_json_file(path)
    if not (isinstance(subset, list)
            and all(isinstance(h, str) for h in subset)):
        return None
    return subset


def _run_rows(flags, state):
    head_blobs = None
    subset = None
    if "--head-blobs" in flags:
        head_blobs = carry_state.read_json_file(flags["--head-blobs"])
        if not _is_str_map(head_blobs):
            return _refuse(REASON_HEAD_BLOBS), ""
    if "--subset" in flags:
        subset = _read_subset(flags["--subset"])
        if subset is None:
            return _refuse(REASON_SUBSET), ""
    doc, reason = build_rows(state, flags["--mode"], head_blobs, subset)
    if reason is not None:
        return _refuse(reason), ""
    return 0, json.dumps(doc, allow_nan=False)


def _load_state(stdin_text):
    """(state, None) or (None, reason)."""
    try:
        state = carry_state.load_json_text(stdin_text)
    except ValueError:
        return None, REASON_STATE_JSON
    reason = carry_state.state_reason(state)
    if reason is not None:
        return None, reason
    return state, None


def _run_resolve(flags, rows_doc):
    """resolve: pure over the rows documents; reads no stdin."""
    refs_doc = carry_state.read_json_file(flags["--answer"])
    if not _valid_refs_doc(refs_doc):
        return _refuse(REASON_REFS), ""
    prior_rows_doc = None
    if "--prior-rows" in flags:
        prior_rows_doc = carry_state.read_json_file(flags["--prior-rows"])
        if not _valid_rows_doc(prior_rows_doc):
            return _refuse(REASON_PRIOR_ROWS), ""
    result, reason = resolve_refs(rows_doc, refs_doc, prior_rows_doc)
    if reason is not None:
        return _refuse(reason), ""
    return 0, json.dumps(result, allow_nan=False)


def _run_answer_side(sub, flags, state):
    rows_doc = carry_state.read_json_file(flags["--rows"])
    if not _valid_rows_doc(rows_doc):
        return _refuse(REASON_ROWS), ""
    if sub == "select-questions":
        return 0, json.dumps(select_questions(rows_doc["rows"]),
                             allow_nan=False)
    if sub == "resolve":
        return _run_resolve(flags, rows_doc)
    answer = carry_state.read_json_file(flags["--answer"])
    if answer is None:
        return _refuse(REASON_ANSWER), ""
    if sub == "select":
        result, reason = select(rows_doc["rows"], answer,
                                subset=rows_doc.get("subset", False))
    elif sub == "parse":
        result, reason = parse(rows_doc, answer)
    else:
        result, reason = build_payload(state, rows_doc, answer)
    if reason is not None:
        return _refuse(reason), ""
    return 0, json.dumps(result, allow_nan=False)


def run(argv, stdin_text):
    """CLI body. Returns (exit code, stdout text)."""
    parsed = parse_argv(argv)
    if parsed is None:
        return _refuse(USAGE), ""
    sub, flags = parsed
    state = None
    if sub in _STATE_SUBCOMMANDS:
        state, reason = _load_state(stdin_text)
        if reason is not None:
            return _refuse(reason), ""
    if sub == "rows":
        return _run_rows(flags, state)
    if sub == "decisions-report":
        return 0, json.dumps(decisions_report(state), allow_nan=False)
    return _run_answer_side(sub, flags, state)


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY process I/O.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    _parsed = parse_argv(sys.argv[1:])
    _stdin_text = ""
    if _parsed is not None and _parsed[0] in _STATE_SUBCOMMANDS:
        try:
            _stdin_text = sys.stdin.read()
        except UnicodeDecodeError:
            sys.stderr.write(REASON_STATE_JSON)
            sys.exit(2)
    _code, _out = run(sys.argv[1:], _stdin_text)
    if _out:
        sys.stdout.write(_out)
    sys.exit(_code)
