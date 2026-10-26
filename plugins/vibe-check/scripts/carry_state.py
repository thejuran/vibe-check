"""carry_state.py — the carry-forward state as executable reads and writes.

The one deterministic helper behind every carry-forward read and write the
review state needs. Prose supplies inputs and renders; this module decides.

WHAT IT DECIDES

  finalize-counts  The three counts `finalize_gate.py` consumes (90-finalize.md):
                   `outstanding_cw`, `unacknowledged_medium` and `undecided_nv`
                   (open Needs-verification items with no current owner
                   decision), each with the hash list behind it.
  pending          "Unchanged since pass N, decision pending": every open,
                   unclosed obligation whose decision snapshot is older than
                   the last pass.
  decided          Read-only: the hashes (rows and member obligations) whose
                   owner decision is current. Phase 0.5 binds it as
                   `$DECIDED_HASHES` to relocate decided records by content.
  record-decisions     The ONLY write path for the root `decisions` family
                       (owner dismiss/defer, written by Finalize and by the
                       fix-loop card, 50-fix-loop.md).
  record-fix-verdicts  The ONLY write path for the root `fix_verdicts` family
                       (fix-agent `obsolete`, written by Phase 5, 50-fix-loop.md).

WHAT IS OPEN. The last pass's findings with status in OPEN_STATUSES — the same
allowlist 05-state.md uses for `$CARRYFORWARD` (`audit` excluded: it is
regenerated each pass, never carried). Each open row ALSO carries, in
`members[].obligation`, every previously raised finding that was folded into
it. Such an absorbed obligation is its own finding: it is enumerated as its own
record, deduplicated by its own `stable_hash`, and closing the row that absorbed
it closes nothing for it. A kept-open row (`kept_open`) is as open as any other:
open is keyed on status only, never on scores or confidence, so a
min_confidence or threshold change can never close a finding.

WHAT CLOSES. Exactly one of:
  * an owner decision that still holds. Every `medium_acknowledgments` entry
    (legacy) closes unconditionally, and so does a `decisions` record WITHOUT
    an `evidence` key (written before decisions were evidence-bound); an old
    file is never rewritten, so an old state counts exactly as before. A
    `decisions` record WITH an `evidence` key closes only while that evidence
    (the finding's snapshot at decision time — or, for a snapshotless finding,
    its own file/line/canonical_line_content/band) still holds
    (`decision_state`). An ordinary decision compares the file and the
    canonical line content, never the line number: a pure line shift keeps the
    decision. A change in the 5-line window beneath the flagged line (the
    pass score.py stamps into `snapshot.nearby_at`) re-asks it. A band drop
    keeps it; a band rise re-asks only when a reviewer lane absent from the
    decision's saved `attribution` now reports the finding (a record written
    before decisions saved `attribution` re-asks on any rise); an unknown band
    re-asks. A decision also records the findings it covered (`covers`: the
    decided finding and every member of its row at decision time, by agent,
    file, title and code line; written only by `record-decisions`, never
    rewritten later). A decided row that later holds a newcomer concern (a
    member with no obligation of its own, from a lane/title pair not in
    `covers` and with a title that is not a covered title) re-asks the whole
    row with cause `joined`; a member repeating a covered title from another
    lane is corroboration and is governed by the band rule only (a second
    reviewer repeating the same concern re-asks only when the band rose).
    Defer and dismiss follow the same rule. An edit to the decided
    line re-hashes it, so the new hash carries no decision at all. A
    Needs-verification decision is compared on _NV_EVIDENCE_KEYS instead: the
    line is dropped (a carried item relocated by content keeps its hash, so a
    pure line shift never re-asks) and the whole-snippet `current_code`
    fingerprint (_nv_code_key) is added (a changed body under a surviving first
    line or symbol name re-asks). An `evidence`
    key that is null or malformed never closes (fail closed). A superseded
    record is kept in the new record's `history`; nothing is deleted;
  * a fix-agent `obsolete` verdict recorded on the LATEST pass whose
    `verified_blob` (the file's blob when the fix agent judged it) still equals
    HEAD's blob for that file. A stale verdict never closes; a verdict whose
    code has since changed never closes; without a HEAD blob map nothing closes
    by verdict (fail closed).
A fix-agent `applied` verdict (a confirmed fix of a Needs-verification item) is
the fixer's own evidence and never closes here: the item closes only on a
rerun, through score.py's routed independent re-check (`resolved[]`). It is
forwarded and judged whatever its `at_pass`: finalize-counts lists it in
`confirmed_fix_awaiting_recheck_hashes` on every pass until score.py's routed
independent re-check closes it or a reviewer's still-applies settles it
(`recheck_settled`) until the fingerprinted code changes.
Nothing else closes a finding: no age, no pass count. Closure is evaluated per
record and is never inherited from a lead.

WHAT IT DOES NOT DO. It never renders REVIEW.md, never prints a finding, and
never writes a file: the `record-*` subcommands print the new state on stdout
and the prose redirects it to `$STATE_FILE.tmp` and `mv`s it on success. It
never edits `passes` or `medium_acknowledgments`.

FAIL CLOSED. Any shape problem returns None; the CLI then prints one fixed line
from REASONS on stderr, prints NOTHING on stdout and exits 2, so the prose halts
instead of reading a silent zero. Reasons name a key at most — never a hash, a
title or a path (finding text is attacker-influenced).

Owner reason text and fix verdicts arrive in files written by the orchestrator
with its Write tool and are passed by path; no free text is ever on argv
(the fixstage/fixcommit library pattern).

CLI (stdin is always the parsed state object; stdout is JSON):

    python3 carry_state.py finalize-counts [--head-blobs PATH] < state.json
    python3 carry_state.py pending < state.json
    python3 carry_state.py decided < state.json
    python3 carry_state.py record-decisions --decisions-file PATH < state.json
    python3 carry_state.py record-fix-verdicts --verdicts-file PATH < state.json

ROLLBACK (reverting this file to its pre-47 version): the older reader closes
a decided hash unconditionally — re-closing findings whose evidence changed
after the decision — and the older writer replaces a decision record whole,
dropping `evidence` and `history`. So, in order:
  1. stop any running review or finalize session;
  2. back up `.turingmind/state/` (copy the directory aside);
  3. while THIS version is still importable, move every state file for which
     `has_evidence_bound_decisions` is True into
     `.turingmind/state/quarantine-47/`. Per file:
       python3 -c 'import json,sys,carry_state; sys.exit(0 if carry_state.has_evidence_bound_decisions(json.load(open(sys.argv[1]))) else 1)' FILE
     (exit 0 = quarantine it);
  4. revert;
  5. the quarantined reviews restart cleanly (no state = a fresh review; the
     backup keeps the audit trail).
Legacy state files (no `evidence` / `history` on any decision) are untouched by
the procedure.

ROLLBACK past the line-free compare (reverting to a reader that compares
`line` and ignores `attribution` / `nearby_at`): that reader re-asks a decided
finding whose line shifted and any band change, so it fails toward asking and
needs no quarantine; the extra `attribution` key on newer decision records is
ignored by it. So is the `covers` key: that reader never inherits a
decision through it and never re-asks a row for a joined newcomer, so a
covered member that splits into its own row is asked again (fails toward
asking) and a joined newcomer is not re-asked (the pre-57 behaviour).

stdlib only; imports exactly {json, os, sys} (`os` for `os.path.isfile`).
"""

import json
import os
import sys

# Mirror of the 05-state.md `$CARRYFORWARD` allowlist. Never add "audit".
OPEN_STATUSES = ("new", "persisted", "needs-recheck")
DECISIONS = ("dismiss", "defer")
# score.py's Needs-verification band, and the string obligation its rows carry
# on their own member ref (mirror of score._NV_MEMBER_OBLIGATION).
NV_BAND = "needs-verification"
NV_MEMBER_OBLIGATION = NV_BAND
# Lows never block Finalize. Needs-verification rows are fix-loop / finalize
# obligations like critical and warning: open until the owner decides them.
BLOCKING_BANDS = ("critical", "warning", NV_BAND, "medium")
_CW_BANDS = ("critical", "warning")

SUBCOMMANDS = ("finalize-counts", "pending", "decided", "record-decisions",
               "record-fix-verdicts")
# The ONLY flags this CLI accepts. There is deliberately no flag that carries a
# reason, a hash or a title: such text on a command line is expanded by the
# shell before Python runs.
KNOWN_FLAGS = ("--decisions-file", "--verdicts-file", "--head-blobs")
# subcommand -> (required flags, optional flags)
_FLAGS_BY_SUBCOMMAND = {
    "finalize-counts": ((), ("--head-blobs",)),
    "pending": ((), ()),
    "decided": ((), ()),
    "record-decisions": (("--decisions-file",), ()),
    "record-fix-verdicts": (("--verdicts-file",), ()),
}

USAGE = ("usage: carry_state.py finalize-counts [--head-blobs PATH] | pending"
         " | decided"
         " | record-decisions --decisions-file PATH"
         " | record-fix-verdicts --verdicts-file PATH  (state on stdin)\n")

REASON_STATE_JSON = "refused: state is not valid JSON\n"
REASON_STATE = "refused: malformed state\n"
REASON_PASSES = "refused: malformed state: passes\n"
REASON_FINDINGS = "refused: malformed state: findings\n"
REASON_MEMBERS = "refused: malformed state: members\n"
REASON_OBLIGATION = "refused: malformed state: obligation\n"
REASON_DECISIONS = "refused: malformed state: decisions\n"
REASON_FIX_VERDICTS = "refused: malformed state: fix_verdicts\n"
REASON_ACKS = "refused: malformed state: medium_acknowledgments\n"
REASON_HEAD_BLOBS = "refused: head-blobs file is missing or not a JSON object\n"
REASON_DECISIONS_FILE = "refused: decisions file is missing or not valid JSON\n"
REASON_DECISIONS_PAYLOAD = "refused: malformed decisions payload\n"
REASON_VERDICTS_FILE = "refused: verdicts file is missing or not valid JSON\n"
REASON_VERDICTS_PAYLOAD = "refused: malformed verdicts payload\n"
REASON_NO_FINGERPRINT = "fix verdict skipped: no file fingerprint\n"
REASON_NO_FIX_EVIDENCE = "fix verdict skipped: no verification evidence\n"

REASONS = (
    REASON_STATE_JSON,
    REASON_STATE,
    REASON_PASSES,
    REASON_FINDINGS,
    REASON_MEMBERS,
    REASON_OBLIGATION,
    REASON_DECISIONS,
    REASON_FIX_VERDICTS,
    REASON_ACKS,
    REASON_HEAD_BLOBS,
    REASON_DECISIONS_FILE,
    REASON_DECISIONS_PAYLOAD,
    REASON_VERDICTS_FILE,
    REASON_VERDICTS_PAYLOAD,
    REASON_NO_FINGERPRINT,
    REASON_NO_FIX_EVIDENCE,
)


def _is_count(value):
    """A plain non-negative int; `bool` is an int in Python and is rejected so
    `True` can never be read as pass 1."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_str_map(value):
    return isinstance(value, dict) and all(
        isinstance(k, str) and isinstance(v, str) for k, v in value.items())


# --------------------------------------------------------------------------- #
# State validation. Every public function goes through _check_state, so one
# shape rule decides "malformed" for counts, pending and both writers alike.
# --------------------------------------------------------------------------- #
def _last_pass(state):
    """(last pass, None) or (None, reason). Fails closed on any shape problem."""
    if not isinstance(state, dict):
        return None, REASON_STATE
    passes = state.get("passes")
    if not isinstance(passes, list) or not passes:
        return None, REASON_PASSES
    last = passes[-1]
    if not isinstance(last, dict) or not _is_count(last.get("pass_number")):
        return None, REASON_PASSES
    findings = last.get("findings")
    if not isinstance(findings, list):
        return None, REASON_FINDINGS
    for f in findings:
        if not (isinstance(f, dict) and isinstance(f.get("stable_hash"), str)
                and isinstance(f.get("band"), str)
                and isinstance(f.get("status"), str)):
            return None, REASON_FINDINGS
    return last, None


def _check_roots(state):
    """Reason for a malformed root family, or None."""
    for key, reason in (("decisions", REASON_DECISIONS),
                        ("medium_acknowledgments", REASON_ACKS)):
        if key in state and not isinstance(state[key], dict):
            return reason
    verdicts = state.get("fix_verdicts", {})
    if not isinstance(verdicts, dict):
        return REASON_FIX_VERDICTS
    for v in verdicts.values():
        if not isinstance(v, dict) or not _is_count(v.get("at_pass")):
            return REASON_FIX_VERDICTS
    return None


def _member_obligations(row):
    """(list of well-formed obligation sidecars with their member, None) or
    (None, reason)."""
    if "members" not in row:
        return [], None
    members = row["members"]
    if not isinstance(members, list):
        return None, REASON_MEMBERS
    out = []
    for m in members:
        if not isinstance(m, dict):
            return None, REASON_MEMBERS
        if "obligation" not in m:
            continue
        obl = m["obligation"]
        if row.get("band") == NV_BAND and obl == NV_MEMBER_OBLIGATION:
            # Phase 53 rollback marker: a reader without Needs-verification
            # support refuses this string obligation (REASON_OBLIGATION) so an
            # older finalize halts instead of counting the item as nothing;
            # this reader counts the NV row itself. Gated on the row's band:
            # the same string on any other band stays malformed.
            continue
        if not (isinstance(obl, dict) and isinstance(obl.get("stable_hash"), str)
                and isinstance(obl.get("band"), str)):
            return None, REASON_OBLIGATION
        out.append((m, obl))
    return out, None


def _check_state(state):
    """(last pass, open records, None) or (None, None, reason)."""
    last, reason = _last_pass(state)
    if reason is not None:
        return None, None, reason
    reason = _check_roots(state)
    if reason is not None:
        return None, None, reason
    rows = []
    sidecars = []
    for f in last["findings"]:
        obligations, reason = _member_obligations(f)
        if reason is not None:
            return None, None, reason
        if f["status"] not in OPEN_STATUSES:
            continue
        rows.append(f)
        for m, obl in obligations:
            sidecars.append({
                "stable_hash": obl["stable_hash"],
                "band": obl["band"],
                "file": m.get("file"),
                "line": m.get("line"),
                "title": m.get("title"),
                "agent": m.get("agent"),
                "canonical_line_content": m.get("canonical_line_content"),
                "status": f["status"],
                "snapshot": obl.get("snapshot"),
                "attribution": obl.get("attribution"),
                "absorbed_into": f["stable_hash"],
            })
    records = []
    seen = set()
    # Rows first, then member records in array order: a kept-open row whose own
    # sidecar repeats its hash is ONE obligation, represented by the row.
    for rec in rows + sidecars:
        if rec["stable_hash"] in seen:
            continue
        seen.add(rec["stable_hash"])
        records.append(rec)
    return last, records, None


def state_reason(state):
    """The fixed REASONS line explaining why `state` is malformed, or None."""
    return _check_state(state)[2]


# --------------------------------------------------------------------------- #
# Reads.
# --------------------------------------------------------------------------- #
def open_findings(state):
    """The last pass's obligation records (rows, then absorbed members), or None
    when the state is malformed."""
    return _check_state(state)[1]


def _sha40(value):
    """A full 40-hex lowercase commit id."""
    return (isinstance(value, str) and len(value) == 40
            and all(c in _HEX for c in value))


def _verdict_kind_valid(verdict, record):
    """Only `obsolete` closes a record here. `applied` (a confirmed fix of a
    Needs-verification item) is the fixer's own evidence and never closes
    alone: it closes only on a rerun, when score.py accepts an independent
    reviewer's routed `resolved` re-check for the repaired code (resolved[]).
    Any other verdict closes nothing."""
    kind = verdict.get("verdict")
    return kind == "obsolete"


def _settled_unchanged(record, head_blobs):
    """True while a reviewer's still-applies (`recheck_settled`) still holds:
    every fingerprinted file's HEAD blob equals its fingerprint. A path whose
    HEAD blob is unknown (no map, or the path is missing from it) counts as
    unchanged, so the item waits for the owner rather than being re-asked."""
    settled = record.get("recheck_settled")
    if not isinstance(settled, dict):
        return False
    fingerprint = settled.get("fingerprint")
    if not isinstance(fingerprint, dict) or not fingerprint:
        return False
    if not isinstance(head_blobs, dict):
        return True
    for path, blob in fingerprint.items():
        head = head_blobs.get(path)
        if isinstance(head, str) and head != blob:
            return False
    return True


def _confirmed_fix_awaiting(record, state, last, head_blobs=None):
    """True for an `applied` verdict, whatever its `at_pass`, on a
    Needs-verification record with its fix commit recorded: fixed, awaiting the
    independent re-check. Not while a still-applies settles it on unchanged
    code."""
    verdict = state.get("fix_verdicts", {}).get(record["stable_hash"])
    return (isinstance(verdict, dict) and verdict.get("verdict") == "applied"
            and record.get("band") == NV_BAND and _sha40(verdict.get("commit_sha"))
            and not _settled_unchanged(record, head_blobs))


def _fix_closes(record, state, last, head_blobs, kind=None):
    verdict = state.get("fix_verdicts", {}).get(record["stable_hash"])
    if not isinstance(verdict, dict) or not _verdict_kind_valid(verdict, record):
        return False
    if kind is not None and verdict.get("verdict") != kind:
        return False
    blob = verdict.get("verified_blob")
    return (verdict.get("at_pass") == last["pass_number"]
            and isinstance(blob, str)
            and isinstance(head_blobs, dict)
            and head_blobs.get(record.get("file")) == blob)


def is_closed(record, state, head_blobs):
    """True iff this ONE record is closed by an owner decision or a verified
    latest-pass fix verdict. Never inherited from the row that absorbed it."""
    last, _, reason = _check_state(state)
    if reason is not None:
        return False
    return _closed(record, state, last, head_blobs)


# The keys score.py's snapshot compares: "stale" means score.py would have
# refreshed the snapshot since the decision was taken.
EVIDENCE_KEYS = ("file", "line", "canonical_line_content", "band")

# The code evidence an ordinary decision is compared on. `line` is stored (for
# display and for the legacy fail-closed shape check) but never compared: a
# pure line shift is not new evidence. EVIDENCE_KEYS / _full_evidence stay as
# they are so a malformed stored record still fails closed.
_ORDINARY_COMPARE = ("file", "canonical_line_content")

# Band order for the direction-aware compare. Mirror of score._BAND_SEVERITY
# without its None key (this module may not import score).
_BAND_RANK = {"critical": 4, "warning": 3, "medium": 2, "low": 1}


# Needs-verification decision evidence (D-12 / O-2). A carried NV item is
# relocated by content and keeps its hash and snapshot, so a pure line shift is
# not new evidence and `line` is not compared. An edit to the item's own line, a
# changed body under a surviving first line or symbol name (score.py refreshes
# `current_code` to the confirmed HEAD window on a located needs-recheck), a
# failed relocation (null snapshot canonical) or a band change is new evidence
# and re-asks the decision.
_NV_EVIDENCE_KEYS = ("file", "canonical_line_content", "band", "current_code")


def _nv_code_key(text):
    """The Needs-verification evidence fingerprint, mirrored from score.py's
    `_nv_code_key` so the writer and this reader agree.

    Every non-blank line with trailing whitespace removed, then the common
    leading-whitespace prefix removed from every line (character by character,
    no tab expansion), joined by "\n". Relative indentation is preserved and
    only a uniform dedent is ignored: a per-line strip made a `return` moved
    outside its authorization guard fingerprint-equal to the guarded one.
    Non-str input -> "" (never raises).
    """
    if not isinstance(text, str):
        return ""
    lines = [ln.rstrip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return ""
    leads = [ln[:len(ln) - len(ln.lstrip())] for ln in lines]
    prefix = leads[0]
    for lead in leads[1:]:
        n = 0
        while n < len(prefix) and n < len(lead) and prefix[n] == lead[n]:
            n += 1
        prefix = prefix[:n]
    return "\n".join(ln[len(prefix):] for ln in lines)


def _is_nv(record):
    snapshot = record.get("snapshot")
    return (record.get("band") == NV_BAND
            or (isinstance(snapshot, dict) and snapshot.get("band") == NV_BAND))


def _evidence_of(record, nv=None):
    """The record's current evidence on EVIDENCE_KEYS: from its snapshot when
    that is a dict, else from the record's own fields (score.py builds the
    next snapshot from those same fields, so the two agree when nothing
    changed). For a Needs-verification record (or when `nv` is True) it also
    holds `current_code`: the _nv_code_key fingerprint of the RECORD's own
    `current_code` (a snapshot never holds code). Always a dict."""
    snapshot = record.get("snapshot")
    source = snapshot if isinstance(snapshot, dict) else record
    # `nearby_at`: the pass score.py last saw a change in the window beneath
    # the flagged line. Compared by decision_state but not part of
    # _full_evidence, so a record stored without it (absent = None) still
    # reads as complete.
    evidence = dict({k: source.get(k) for k in EVIDENCE_KEYS},
                    nearby_at=(snapshot.get("nearby_at")
                               if isinstance(snapshot, dict) else None))
    if nv if nv is not None else _is_nv(record):
        return dict(evidence,
                    current_code=_nv_code_key(record.get("current_code")))
    return evidence


def _evidence_keys(evidence, record):
    """_NV_EVIDENCE_KEYS when either side is a Needs-verification band, else
    EVIDENCE_KEYS."""
    if evidence.get("band") == NV_BAND or _is_nv(record):
        return _NV_EVIDENCE_KEYS
    return EVIDENCE_KEYS


def _full_evidence(evidence):
    return isinstance(evidence, dict) and all(k in evidence
                                              for k in EVIDENCE_KEYS)


def _str_lanes(value):
    return {a for a in value if isinstance(a, str)}


def gained_lanes(record, state):
    """Sorted reviewer lanes in the record's `attribution` that are absent
    from its own decision's saved `attribution`; [] when the record has no
    decision dict or either side lacks a list `attribution`."""
    decision = state.get("decisions", {}).get(record.get("stable_hash"))
    if not isinstance(decision, dict):
        return []
    saved = decision.get("attribution")
    now = record.get("attribution")
    if not (isinstance(saved, list) and isinstance(now, list)):
        return []
    return sorted(_str_lanes(now) - _str_lanes(saved))


def _band_rise_reopens(record, state, decision):
    """True when a band rise is new evidence: the decision predates saved
    `attribution` (fails toward asking), or a lane absent at decision time
    now reports the finding. A rise from the persistence bonus or a lifted
    single-reviewer cap alone keeps the decision."""
    if "attribution" not in decision:
        return True
    return bool(gained_lanes(record, state))


def _first_code_line(text):
    """The first non-blank line of `text`, stripped; None when `text` is not
    a non-empty str or holds only blank lines."""
    if not isinstance(text, str):
        return None
    for ln in text.split("\n"):
        if ln.strip():
            return ln.strip()
    return None


def _identity(item):
    """The cross-pass identity of a finding or member: (agent, file, title)."""
    return (item.get("agent"), item.get("file"), item.get("title"))


def _covers_of(record):
    """The findings a decision on `record` covers, frozen at decision time.

    One entry per (agent, file, title) identity, the record itself first:
    `code` is the record's `canonical_line_content` (when a str), and for each
    dict in `members[]` the first non-blank line of its `current_code`,
    stripped (None when there is none). A member with the record's own
    identity (the lead's own member record) is the record itself and is not
    listed twice."""
    canon = record.get("canonical_line_content")
    out = [{"agent": record.get("agent"), "file": record.get("file"),
            "title": record.get("title"),
            "code": canon if isinstance(canon, str) else None}]
    seen = {_identity(record)}
    members = record.get("members")
    for m in members if isinstance(members, list) else []:
        if not isinstance(m, dict) or _identity(m) in seen:
            continue
        seen.add(_identity(m))
        out.append({"agent": m.get("agent"), "file": m.get("file"),
                    "title": m.get("title"),
                    "code": _first_code_line(m.get("current_code"))})
    return out


def _covered_identities(decision):
    """(set of (agent, file, title), set of titles) the decision's `covers`
    names; (None, None) for a decision without a list `covers` (legacy: what
    it covered is unknown)."""
    covers = decision.get("covers") if isinstance(decision, dict) else None
    if not isinstance(covers, list):
        return None, None
    entries = [c for c in covers if isinstance(c, dict)]
    return ({_identity(c) for c in entries},
            {c.get("title") for c in entries})


def _own_decision(record, state):
    decisions = state.get("decisions", {})
    return (decisions.get(record.get("stable_hash"))
            if isinstance(decisions, dict) else None)


def newcomer_lanes(record, state):
    """Sorted reviewer lanes of the newcomer concerns on a decided row: the
    single source of truth for the D-08 newcomer test, read by
    `decision_state` / `stale_cause` (through `_joined_newcomer`) and by
    batch_card.py for the card wording, so the reopen and the card can never
    disagree.

    A newcomer is a dict `members[]` entry without an obligation of its own
    (a member with a dict `obligation` carrying a `stable_hash` is a record of
    its own) whose (agent, file, title) is not in the record's own decision's
    `covers` AND whose title is not a covered title: a second reviewer
    repeating a covered concern (same title) is corroboration, governed only
    by the severity rule. [] when the record has no own decision or that
    decision has no `covers` (legacy)."""
    identities, titles = _covered_identities(_own_decision(record, state))
    if identities is None:
        return []
    members = record.get("members")
    lanes = set()
    for m in members if isinstance(members, list) else []:
        if not isinstance(m, dict) or not isinstance(m.get("agent"), str):
            continue
        obl = m.get("obligation")
        if isinstance(obl, dict) and isinstance(obl.get("stable_hash"), str):
            continue
        if _identity(m) in identities or m.get("title") in titles:
            continue
        lanes.add(m["agent"])
    return sorted(lanes)


def covered_count(record, state):
    """The D-10 count the card prints: how many findings on this row the
    record's own decision covered (the lead, plus each member whose
    (agent, file, title) is in `covers`, the lead's own member record not
    counted twice). 0 when the record has no own decision or the decision has
    no `covers` (legacy: nothing is known to be covered). batch_card.py must
    read this, never `covers` itself."""
    identities, _ = _covered_identities(_own_decision(record, state))
    if identities is None:
        return 0
    members = record.get("members")
    covered = {_identity(m) for m in (members if isinstance(members, list)
                                      else [])
               if isinstance(m, dict) and _identity(m) in identities}
    covered.discard(_identity(record))
    return 1 + len(covered)


def _joined_newcomer(record, state):
    return bool(newcomer_lanes(record, state))


def decision_state(record, state):
    """"current" | "stale" | None for the owner decision on this record.

    None: no decision. "current": a legacy medium acknowledgment, or a
    decision that predates evidence binding (not a dict, or a dict with NO
    `evidence` key). "stale" when the `evidence` key is present but null / not
    a dict / missing a key (fail closed — the writer never produces that).

    An ordinary decision is otherwise compared in order: the file or canonical
    line content differs -> "stale" (the line number is never compared); the
    `nearby_at` stamp differs -> "stale"; a newcomer concern joined the row
    (`newcomer_lanes` non-empty) -> "stale"; then the band: an unknown band on
    either side -> "stale", a drop or no change -> "current", a rise ->
    "stale" only when `_band_rise_reopens`. Defer and dismiss are treated
    alike. A Needs-verification decision compares all of _NV_EVIDENCE_KEYS."""
    h = record["stable_hash"]
    if h in state.get("medium_acknowledgments", {}):
        return "current"
    decisions = state.get("decisions", {})
    if h not in decisions:
        # Hook: an inherited decision (a covering decision on another record)
        # is looked up here.
        return None
    decision = decisions[h]
    if not isinstance(decision, dict) or "evidence" not in decision:
        return "current"
    evidence = decision["evidence"]
    if not _full_evidence(evidence):
        return "stale"
    keys = _evidence_keys(evidence, record)
    current = _evidence_of(record, nv=keys is _NV_EVIDENCE_KEYS)
    if keys is _NV_EVIDENCE_KEYS:
        # A stored NV evidence dict lacking `current_code` (the writer never
        # produces one) compares as stale: fail closed.
        if all(k in evidence and evidence[k] == current[k] for k in keys):
            return "current"
        return "stale"
    if any(evidence[k] != current[k] for k in _ORDINARY_COMPARE):
        return "stale"
    if evidence.get("nearby_at") != current.get("nearby_at"):
        return "stale"
    if _joined_newcomer(record, state):
        return "stale"
    was = _BAND_RANK.get(evidence["band"])
    cur = _BAND_RANK.get(current["band"])
    if was is None or cur is None:
        return "stale"
    if cur <= was:
        return "current"
    return "stale" if _band_rise_reopens(record, state, decision) else "current"


def stale_cause(record, state):
    """None unless the decision is stale. Ordinary: "code" when the file or
    canonical line content differs (or `evidence` is null / malformed), else
    "nearby" when the `nearby_at` stamp differs, else "joined" when a
    newcomer concern joined the decided row, else "severity".
    Needs-verification: "severity" when only the band differs, else "code"."""
    if decision_state(record, state) != "stale":
        return None
    evidence = state.get("decisions", {}).get(record["stable_hash"])
    evidence = evidence.get("evidence") if isinstance(evidence, dict) else None
    if not _full_evidence(evidence):
        return "code"
    keys = _evidence_keys(evidence, record)
    current = _evidence_of(record, nv=keys is _NV_EVIDENCE_KEYS)
    if keys is _NV_EVIDENCE_KEYS:
        same = ("file", "canonical_line_content", "current_code")
        if all(k in evidence and evidence[k] == current[k] for k in same):
            return "severity"
        return "code"
    if any(evidence[k] != current[k] for k in _ORDINARY_COMPARE):
        return "code"
    if evidence.get("nearby_at") != current.get("nearby_at"):
        return "nearby"
    if _joined_newcomer(record, state):
        return "joined"
    return "severity"


def has_evidence_bound_decisions(state):
    """True when any `decisions` record carries an `evidence` key (any value,
    null included) or a `history` key — the state files the pre-47 reader
    would mis-close or the pre-47 writer would truncate. Read-only."""
    if not isinstance(state, dict):
        return False
    decisions = state.get("decisions")
    if not isinstance(decisions, dict):
        return False
    return any(isinstance(d, dict) and ("evidence" in d or "history" in d)
               for d in decisions.values())


def _closed(record, state, last, head_blobs):
    if decision_state(record, state) == "current":
        return True
    return _fix_closes(record, state, last, head_blobs)


def finalize_counts(state, head_blobs=None):
    """The three gate counts plus the hash lists behind them, or None when the
    state is malformed. `head_blobs` is {file: HEAD blob}; without it a fix
    verdict closes nothing."""
    last, records, reason = _check_state(state)
    if reason is not None:
        return None
    cw = []
    medium = []
    nv = []
    obsolete = []
    awaiting = []
    for rec in records:
        if _fix_closes(rec, state, last, head_blobs, kind="obsolete"):
            obsolete.append(rec["stable_hash"])
        if _closed(rec, state, last, head_blobs):
            continue
        if rec["band"] in _CW_BANDS:
            cw.append(rec["stable_hash"])
        elif rec["band"] == NV_BAND:
            nv.append(rec["stable_hash"])
        elif rec["band"] == "medium":
            medium.append(rec["stable_hash"])
        if _confirmed_fix_awaiting(rec, state, last, head_blobs):
            awaiting.append(rec["stable_hash"])
    return {
        "outstanding_cw": len(cw),
        "unacknowledged_medium": len(medium),
        "undecided_nv": len(nv),
        "outstanding_cw_hashes": sorted(cw),
        "unacknowledged_medium_hashes": sorted(medium),
        "undecided_nv_hashes": sorted(nv),
        "verified_obsolete_hashes": sorted(obsolete),
        "confirmed_fix_awaiting_recheck_hashes": sorted(set(awaiting)),
    }


def pending(state):
    """[{stable_hash, since_pass}] for every open, unclosed record whose
    snapshot predates the last pass, sorted by hash; None when malformed. A
    missing or malformed snapshot is simply not pending (fail soft)."""
    last, records, reason = _check_state(state)
    if reason is not None:
        return None
    out = []
    for rec in records:
        if _closed(rec, state, last, None):
            continue
        snapshot = rec.get("snapshot")
        if not isinstance(snapshot, dict):
            continue
        at_pass = snapshot.get("at_pass")
        if _is_count(at_pass) and at_pass < last["pass_number"]:
            out.append({"stable_hash": rec["stable_hash"],
                        "since_pass": at_pass})
    return sorted(out, key=lambda p: p["stable_hash"])


def decided(state):
    """Sorted `stable_hash` of every open record (rows and member
    obligations) whose owner decision is current; None when the state is
    malformed. Read-only. The orchestrator relocates exactly these records by
    content, so a refusal must never look like an empty list."""
    _, records, reason = _check_state(state)
    if reason is not None:
        return None
    return sorted(rec["stable_hash"] for rec in records
                  if decision_state(rec, state) == "current")


# --------------------------------------------------------------------------- #
# Writes. Each returns a NEW state object (the input is never mutated) and
# writes exactly one root family; `passes` and `medium_acknowledgments` are
# copied through untouched. The owner creates its family lazily.
# --------------------------------------------------------------------------- #
_DECISION_PAYLOAD_KEYS = ("at_pass", "decisions")
_DECISION_ENTRY_KEYS = ("stable_hash", "decision", "reason")
_VERDICT_PAYLOAD_REQUIRED = ("at_pass", "head_sha", "sent", "results")
_VERDICT_PAYLOAD_OPTIONAL = ("blobs", "commits", "clean_head_blobs")
# The fix agent's after-check outcomes that stand behind an `applied` result:
# a check that ran and passed, or no automated check (the agent's own re-check
# of the cited condition). failed / timeout / unavailable never do.
_CONFIRMED_CHECK_OUTCOMES = ("passed", "not-run")
_HEX = frozenset("0123456789abcdef")


def _valid_decision_entries(payload, open_hashes):
    if not (isinstance(payload, dict)
            and set(payload) == set(_DECISION_PAYLOAD_KEYS)
            and _is_count(payload["at_pass"])
            and isinstance(payload["decisions"], list)):
        return False
    seen = set()
    for entry in payload["decisions"]:
        if not (isinstance(entry, dict)
                and set(entry) == set(_DECISION_ENTRY_KEYS)):
            return False
        h = entry["stable_hash"]
        reason = entry["reason"]
        if not (isinstance(h, str) and h in open_hashes and h not in seen
                and entry["decision"] in DECISIONS
                and isinstance(reason, str) and reason.strip()):
            return False
        seen.add(h)
    return True


def _stored_evidence(record):
    """A JSON copy of `_evidence_of(record)` for a decision record. An absent
    `nearby_at` stamp is left out rather than stored as null, so a record
    without one has exactly the shape older readers wrote (absent and null
    compare equal in decision_state)."""
    evidence = _evidence_of(record)
    if isinstance(evidence, dict) and evidence.get("nearby_at") is None:
        evidence = {k: v for k, v in evidence.items() if k != "nearby_at"}
    return json.loads(json.dumps(evidence))


def _attribution_copy(value):
    """A list copy of the str lanes in `value`; [] for anything not a list."""
    if not isinstance(value, list):
        return []
    return [a for a in value if isinstance(a, str)]


def record_decisions(state, payload):
    """Record owner dismiss/defer decisions; the new state, or None on refusal.

    `payload` = {"at_pass": int, "decisions": [{stable_hash, decision, reason}]}.
    The hash must be an open record of the last pass (a member obligation's own
    hash included); the stored band is that record's band, never the payload's.
    The record also stores `evidence`: the finding's current evidence
    (`_evidence_of`), never null — the four EVIDENCE_KEYS, plus the
    `current_code` fingerprint for a Needs-verification record — and
    `attribution`: the reviewer lanes reporting the finding at decision time,
    read from the state (a payload can never set it) — and `covers`
    (`_covers_of`): the findings the decision covered, also read from the
    state only and frozen there (an older record is never rewritten). A
    later decision for
    the same hash replaces the earlier one, and the earlier record (minus its
    own `history`) is kept first in the new record's `history`.
    """
    _, records, reason = _check_state(state)
    if reason is not None:
        return None
    by_hash = {rec["stable_hash"]: rec for rec in records}
    if not _valid_decision_entries(payload, by_hash):
        return None
    new = json.loads(json.dumps(state))
    if not isinstance(new.get("decisions"), dict):
        new["decisions"] = {}
    for entry in payload["decisions"]:
        h = entry["stable_hash"]
        prior = new["decisions"].get(h)
        record = {
            "decision": entry["decision"],
            "reason": entry["reason"],
            "at_pass": payload["at_pass"],
            "band": by_hash[h]["band"],
            "evidence": _stored_evidence(by_hash[h]),
            "attribution": _attribution_copy(by_hash[h].get("attribution")),
            "covers": json.loads(json.dumps(_covers_of(by_hash[h]))),
        }
        if isinstance(prior, dict):
            hist = ([{k: v for k, v in prior.items() if k != "history"}]
                    + list(prior.get("history") or []))
            record = dict(record, history=hist)
        new["decisions"][h] = record
    return new


def _valid_verdict_payload(payload):
    if not isinstance(payload, dict):
        return False
    keys = set(payload)
    if not (set(_VERDICT_PAYLOAD_REQUIRED) <= keys
            <= set(_VERDICT_PAYLOAD_REQUIRED + _VERDICT_PAYLOAD_OPTIONAL)):
        return False
    head = payload["head_sha"]
    for key in ("commits", "clean_head_blobs"):
        if key in payload and not isinstance(payload[key], dict):
            return False
    return (_is_count(payload["at_pass"])
            and (head is None or isinstance(head, str))
            and isinstance(payload["sent"], list)
            and all(isinstance(h, str) for h in payload["sent"])
            and isinstance(payload["results"], list)
            and all(isinstance(r, dict) for r in payload["results"]))


def _confirmed_fix_evidence(result, record, payload):
    """(commit_sha, blob) when an `applied` result on a Needs-verification
    record carries evidence tied to the finding and the repaired code, else
    None.

    Required, all of:
      - `commit_sha` is a full 40-hex id the orchestrator found as a commit
        reachable from HEAD (`commits[sha]` present);
      - that commit touches the finding's file (`commits[sha].files`), and the
        result's `files_touched` names it;
      - the fix agent's re-check and after-check stand behind it (`check` is
        an object whose `outcome` is in _CONFIRMED_CHECK_OUTCOMES);
      - the repaired code is what HEAD holds: the file's blob in that commit
        (`commits[sha].blobs[file]`) equals `clean_head_blobs[file]`, HEAD's
        blob read after the batch for a file that was clean (HEAD = index =
        working tree) both before and after it.
    """
    sha = result.get("commit_sha")
    file = record.get("file")
    if not (_sha40(sha) and isinstance(file, str) and file):
        return None
    touched = result.get("files_touched")
    if not (isinstance(touched, list) and file in touched):
        return None
    check = result.get("check")
    if not isinstance(check, dict) or check.get("outcome") not in _CONFIRMED_CHECK_OUTCOMES:
        return None
    commit = (payload.get("commits") or {}).get(sha)
    if not isinstance(commit, dict) or not isinstance(commit.get("files"), list):
        return None
    if file not in commit.get("files"):
        return None
    blobs = commit.get("blobs")
    blob = blobs.get(file) if isinstance(blobs, dict) else None
    clean = payload.get("clean_head_blobs") or {}
    if not isinstance(blob, str) or clean.get(file) != blob:
        return None
    return sha, blob


def record_fix_verdicts(state, payload, skipped=None):
    """Record fix-agent verdicts; the new state, or None on refusal.

    `payload` = {"at_pass", "head_sha", "sent", "results", "blobs",
    "commits", "clean_head_blobs"}. Every verdict needs a result whose id is a
    FULL hash that was sent to the fix agent AND is an open record of the last
    pass.

    `obsolete`: written only when the record's file has a blob in `blobs`
    (the code the fix agent saw). Without that fingerprint the verdict could
    never close anything, so it is not recorded.

    `applied` on a Needs-verification record (a confirmed fix: Needs-
    verification rows are sent only when the owner names them): written only
    with the evidence `_confirmed_fix_evidence` requires, as verdict `applied`
    with `verified_blob` = the repaired file's blob and `commit_sha`. An
    applied result on any other band records nothing (those findings close
    through the rerun as before).

    A skipped verdict's id is appended to `skipped` when a list is given.

    `at_pass` must equal the last pass's `pass_number`: a verdict stamped with
    any other pass (e.g. Finalize's next-pass `$PASS_NUMBER`, for which no pass
    was persisted) could never be honoured by `_fix_closes` nor forwarded by
    Phase 0.5, so the whole payload is refused rather than silently inert.
    """
    last, records, reason = _check_state(state)
    if reason is not None or not _valid_verdict_payload(payload):
        return None
    if payload["at_pass"] != last["pass_number"]:
        return None
    by_hash = {rec["stable_hash"]: rec for rec in records}
    sent = set(payload["sent"])
    blobs = payload.get("blobs")
    new = json.loads(json.dumps(state))
    for result in payload["results"]:
        h = result.get("id")
        status = result.get("status")
        if not (status in ("obsolete", "applied") and isinstance(h, str)
                and h in sent and h in by_hash):
            continue
        summary = result.get("summary")
        entry = {
            "agent": "fix",
            "head_sha": payload["head_sha"],
            "at_pass": payload["at_pass"],
            "reason": "" if summary is None else str(summary),
        }
        if status == "applied":
            if not by_hash[h].get("band") == NV_BAND:
                continue
            evidence = _confirmed_fix_evidence(result, by_hash[h], payload)
            if evidence is None:
                if isinstance(skipped, list):
                    skipped.append(h)
                continue
            entry = dict(entry, verdict="applied", verified_blob=evidence[1],
                         commit_sha=evidence[0])
        else:
            blob = blobs.get(by_hash[h].get("file")) if isinstance(
                blobs, dict) else None
            if not isinstance(blob, str):
                if isinstance(skipped, list):
                    skipped.append(h)
                continue
            entry = dict(entry, verdict="obsolete", verified_blob=blob)
        if not isinstance(new.get("fix_verdicts"), dict):
            new["fix_verdicts"] = {}
        new["fix_verdicts"][h] = {k: entry[k] for k in (
            "verdict", "agent", "head_sha", "at_pass", "verified_blob",
            "commit_sha", "reason") if k in entry}
    return new


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def parse_argv(argv):
    """(subcommand, {flag: value}) or None on any usage error. Hand-rolled so an
    unknown flag is an error, never a silent default."""
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
    return sub, values


def _reject_constant(_name):
    raise ValueError("non-finite number")


def load_json_text(text):
    """Parse JSON text strictly: NaN/Infinity raise ValueError.

    Public so batch_card.py shares the same strict loader for its state input.
    """
    return json.loads(text, parse_constant=_reject_constant)


def read_json_file(path):
    """The parsed file, or None when it is missing or not valid JSON."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return load_json_text(fh.read())
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def _refuse(reason):
    sys.stderr.write(reason)
    return 2


def run(argv, stdin_text):
    """CLI body. Returns (exit code, stdout text)."""
    parsed = parse_argv(argv)
    if parsed is None:
        return _refuse(USAGE), ""
    sub, flags = parsed
    try:
        state = load_json_text(stdin_text)
    except ValueError:
        return _refuse(REASON_STATE_JSON), ""
    reason = state_reason(state)
    if reason is not None:
        return _refuse(reason), ""

    if sub == "finalize-counts":
        head_blobs = None
        if "--head-blobs" in flags:
            head_blobs = read_json_file(flags["--head-blobs"])
            if not _is_str_map(head_blobs):
                return _refuse(REASON_HEAD_BLOBS), ""
        result = finalize_counts(state, head_blobs)
    elif sub == "pending":
        result = pending(state)
    elif sub == "decided":
        result = decided(state)
    elif sub == "record-decisions":
        payload = read_json_file(flags["--decisions-file"])
        if not isinstance(payload, dict):
            return _refuse(REASON_DECISIONS_FILE), ""
        result = record_decisions(state, payload)
        if result is None:
            return _refuse(REASON_DECISIONS_PAYLOAD), ""
    else:
        payload = read_json_file(flags["--verdicts-file"])
        if not isinstance(payload, dict):
            return _refuse(REASON_VERDICTS_FILE), ""
        skipped = []
        result = record_fix_verdicts(state, payload, skipped)
        if result is None:
            return _refuse(REASON_VERDICTS_PAYLOAD), ""
        if skipped:
            statuses = {r.get("id"): r.get("status") for r in payload["results"]
                        if isinstance(r, dict)}
            if any(statuses.get(h) == "obsolete" for h in skipped):
                sys.stderr.write(REASON_NO_FINGERPRINT)
            if any(statuses.get(h) == "applied" for h in skipped):
                sys.stderr.write(REASON_NO_FIX_EVIDENCE)

    if result is None:
        return _refuse(REASON_STATE), ""
    return 0, json.dumps(result, allow_nan=False)


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY process I/O.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    try:
        stdin_text = sys.stdin.read()
    except UnicodeDecodeError:
        sys.stderr.write(REASON_STATE_JSON)
        sys.exit(2)
    code, out = run(sys.argv[1:], stdin_text)
    if out:
        sys.stdout.write(out)
    sys.exit(code)
