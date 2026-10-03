"""batch_card.py — the owner's batch card as deterministic reads.

Renders nothing, decides numbering/tags/parse, writes nothing; prose calls by
path; owner text by file.

The two prose files that ask the owner one card per pass (the fix loop and
Finalize) call this helper for everything they must not compute themselves:

  rows              The numbered card rows. Numbering is decided here once, so
                    the list the owner reads and the parse of the owner's
                    answer always agree. Each row is tagged with
                    `pending_since` (unchanged since pass N, decision pending)
                    and `stale` (the owner's earlier decision no longer
                    matches the evidence it judged).
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
                    `#n file:line` (never a title, never a comma).
  select            A multi-select / typed-list answer -> row numbers + hashes.
  payload           THE fix-agent dispatch for the selected rows: each unit is
                    the selected record's own defect, copied from the state.
  parse             The finalize card answer -> fix / dismiss / defer lists,
                    the record-decisions payload and the fix targets.

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

Selection answers (select, payload): {"labels": [...] | "a, b"}, {"text":
"1,3-5"}, {"all": true} or {"none": true} — the typed-mode buttons map to
all / none. Finalize answers (parse): {"q1": str, "q2": str | null}.

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
_BAND_RANK = {"critical": 0, "warning": 1, "medium": 2}

SUBCOMMANDS = ("rows", "select-questions", "select", "payload", "parse",
               "decisions-report")
# The ONLY flags this CLI accepts. No flag ever carries owner text, a title or
# a reason: such text arrives in a file whose path is passed here.
KNOWN_FLAGS = ("--mode", "--head-blobs", "--subset", "--rows", "--answer")
# subcommand -> (required flags, optional flags)
_FLAGS_BY_SUBCOMMAND = {
    "rows": (("--mode",), ("--head-blobs", "--subset")),
    "select-questions": (("--rows",), ()),
    "select": (("--rows", "--answer"), ()),
    "payload": (("--rows", "--answer"), ()),
    "parse": (("--rows", "--answer"), ()),
    "decisions-report": ((), ()),
}
# Subcommands that read the state JSON on stdin.
_STATE_SUBCOMMANDS = ("rows", "payload", "decisions-report")

USAGE = ("usage: batch_card.py rows --mode fix-loop [--subset PATH]"
         " | rows --mode finalize --head-blobs PATH"
         " | select-questions --rows PATH | select --rows PATH --answer PATH"
         " | payload --rows PATH --answer PATH | parse --rows PATH"
         " --answer PATH | decisions-report  (state on stdin for rows,"
         " payload, decisions-report)\n")

REASON_STATE_JSON = carry_state.REASON_STATE_JSON
REASON_HEAD_BLOBS = carry_state.REASON_HEAD_BLOBS
REASON_SUBSET = "refused: subset file is missing or not a list of hashes\n"
REASON_SUBSET_EMPTY = "refused: subset names no last-pass finding\n"
REASON_ROWS = "refused: rows file is missing or malformed\n"
REASON_ANSWER = "refused: answer file is missing or malformed\n"
REASON_ROWS_STATE = "refused: rows file does not match this state\n"

REASONS = (
    USAGE,
    REASON_STATE_JSON,
    REASON_HEAD_BLOBS,
    REASON_SUBSET,
    REASON_SUBSET_EMPTY,
    REASON_ROWS,
    REASON_ANSWER,
    REASON_ROWS_STATE,
)

# AskUserQuestion limits: 1-4 questions, 2-4 options each, header <= 12.
_MAX_OPTIONS = 4
_MAX_QUESTIONS = 4
_MAX_MULTISELECT = _MAX_OPTIONS * _MAX_QUESTIONS
_DESCRIPTION_PROBLEM_CHARS = 80
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
    if not isinstance(decision, dict):
        return None
    evidence = decision.get("evidence")
    was_band = (evidence.get("band") if isinstance(evidence, dict)
                else decision.get("band"))
    return {
        "cause": carry_state.stale_cause(record, state),
        "decision": decision.get("decision"),
        "reason": decision.get("reason"),
        "at_pass": decision.get("at_pass"),
        "was_band": was_band,
        "via": "same_hash",
        "prior_hash": h,
    }


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

    fix-loop: every open, unclosed (no head blobs) critical/warning/medium
    record. finalize: exactly finalize_counts' outstanding critical/warning
    and unacknowledged medium hashes (head blobs honoured). Rows are ordered
    band -> file -> line (None last) -> hash and numbered from 1.
    With `subset` (fix-loop only): the dispatch targets from
    `resolve_fix_targets`, in subset order.
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
    return {"at_pass": last["pass_number"], "mode": mode, "rows": rows}, None


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
# Answer side: select-questions, select, parse, payload.
# --------------------------------------------------------------------------- #
def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_rows_doc(doc):
    """True for a rows document shaped like `rows` output."""
    if not (isinstance(doc, dict) and _is_count(doc.get("at_pass"))
            and isinstance(doc.get("rows"), list)):
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

    N <= 1: mode none (the one row applies directly). 2 <= N <= 16: ceil(N/4)
    multi-select questions, balanced so every question has >= 2 options.
    N > 16: mode typed — one single-choice question whose two buttons map to
    all / none and whose Other box takes a typed list such as 1,3-5.
    """
    count = len(rows)
    if count <= 1:
        return {"mode": "none", "questions": []}
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


def select(rows, answer):
    """({"hashes", "rows"}, None) or (None, reason) for a selection answer."""
    if not _valid_select_answer(answer):
        return None, REASON_ANSWER
    if "all" in answer:
        numbers = [r["n"] for r in rows]
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
                fix_targets=_dedup(result["fix"])), None


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
    return {
        "id": record["stable_hash"],
        "file": source.get("file"),
        "line": source.get("line"),
        "title": source.get("title"),
        "problem": _str_or(source.get("problem"), ""),
        "current_code": _str_or(source.get("current_code"), ""),
        "fix_hint": fix_hint if isinstance(fix_hint, str) else None,
        "why_it_matters": _str_or(source.get("why_it_matters"), ""),
    }


def build_payload(state, rows_doc, answer):
    """({"sent", "findings"}, None) or (None, reason): the fix-agent dispatch.

    Every field is copied from the state's last pass, never from the rows
    file. A subset row contributes its lead only when `lead_selected`, then
    each routed member's own defect; a member sidecar row contributes the
    member dict. The rows file must describe this state's last pass.
    """
    selection, reason = select(rows_doc["rows"], answer)
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
        state = carry_state._load_json_text(stdin_text)
    except ValueError:
        return None, REASON_STATE_JSON
    reason = carry_state.state_reason(state)
    if reason is not None:
        return None, reason
    return state, None


def _run_answer_side(sub, flags, state):
    rows_doc = carry_state.read_json_file(flags["--rows"])
    if not _valid_rows_doc(rows_doc):
        return _refuse(REASON_ROWS), ""
    if sub == "select-questions":
        return 0, json.dumps(select_questions(rows_doc["rows"]),
                             allow_nan=False)
    answer = carry_state.read_json_file(flags["--answer"])
    if answer is None:
        return _refuse(REASON_ANSWER), ""
    if sub == "select":
        result, reason = select(rows_doc["rows"], answer)
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
