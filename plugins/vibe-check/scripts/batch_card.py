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

CLI (stdin = the state JSON for `rows` and `decisions-report`):

    python3 batch_card.py rows --mode fix-loop [--subset PATH] < state.json
    python3 batch_card.py rows --mode finalize --head-blobs PATH < state.json
    python3 batch_card.py decisions-report < state.json

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

SUBCOMMANDS = ("rows", "decisions-report")
# The ONLY flags this CLI accepts. No flag ever carries owner text, a title or
# a reason: such text arrives in a file whose path is passed here.
KNOWN_FLAGS = ("--mode", "--head-blobs", "--subset", "--rows", "--answer")
# subcommand -> (required flags, optional flags)
_FLAGS_BY_SUBCOMMAND = {
    "rows": (("--mode",), ("--head-blobs", "--subset")),
    "decisions-report": ((), ()),
}
# Subcommands that read the state JSON on stdin.
_STATE_SUBCOMMANDS = ("rows", "decisions-report")

USAGE = ("usage: batch_card.py rows --mode fix-loop [--subset PATH]"
         " | rows --mode finalize --head-blobs PATH"
         " | decisions-report  (state on stdin)\n")

REASON_STATE_JSON = carry_state.REASON_STATE_JSON
REASON_HEAD_BLOBS = carry_state.REASON_HEAD_BLOBS
REASON_SUBSET = "refused: subset file is missing or not a list of hashes\n"
REASON_SUBSET_EMPTY = "refused: subset names no last-pass finding\n"

REASONS = (
    USAGE,
    REASON_STATE_JSON,
    REASON_HEAD_BLOBS,
    REASON_SUBSET,
    REASON_SUBSET_EMPTY,
)


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
    return {
        "n": 0,
        "stable_hash": record["stable_hash"],
        "band": record["band"],
        "file": record.get("file"),
        "line": record.get("line"),
        "title": record.get("title"),
        "problem": _str_or(record.get("problem"), ""),
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
    """
    reason = carry_state.state_reason(state)
    if reason is not None:
        return None, reason
    last, records, lead_titles, pending_since = _context(state)
    if mode == "finalize":
        counts = carry_state.finalize_counts(state, head_blobs)
        wanted = set(counts["outstanding_cw_hashes"]
                     + counts["unacknowledged_medium_hashes"])
        chosen = [r for r in records if r["stable_hash"] in wanted]
    else:
        chosen = [r for r in records
                  if r["band"] in carry_state.BLOCKING_BANDS
                  and not carry_state.is_closed(r, state, None)]
        if subset is not None:
            subset_set = set(subset)
            chosen = [r for r in chosen if r["stable_hash"] in subset_set]
    rows = [_row(r, state, lead_titles, pending_since) for r in chosen]
    rows.sort(key=_sort_key)
    if subset is not None:
        if not rows:
            return None, REASON_SUBSET_EMPTY
        for row in rows:
            row["lead_closed"] = False
            row["routed_members"] = []
    for i, row in enumerate(rows):
        row["n"] = i + 1
    return {"at_pass": last["pass_number"], "mode": mode, "rows": rows}, None


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


def run(argv, stdin_text):
    """CLI body. Returns (exit code, stdout text)."""
    parsed = parse_argv(argv)
    if parsed is None:
        return _refuse(USAGE), ""
    sub, flags = parsed
    state, reason = _load_state(stdin_text)
    if reason is not None:
        return _refuse(reason), ""
    if sub == "rows":
        return _run_rows(flags, state)
    return 0, json.dumps(decisions_report(state), allow_nan=False)


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
