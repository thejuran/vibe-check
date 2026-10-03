"""carry_state.py — the carry-forward state as executable reads and writes.

The one deterministic helper behind every carry-forward read and write the
review state needs. Prose supplies inputs and renders; this module decides.

WHAT IT DECIDES

  finalize-counts  The two counts `finalize_gate.py` consumes (90-finalize.md).
                   The gate itself is unchanged; only where its input counts
                   come from moved here.
  pending          "Unchanged since pass N, decision pending": every open,
                   unclosed obligation whose decision snapshot is older than
                   the last pass.
  record-decisions     The ONLY write path for the root `decisions` family
                       (owner dismiss/defer, written by Finalize).
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
    its own file/line/canonical_line_content/band) still equals the finding's
    current evidence on those four keys (`decision_state`). A same-hash band
    change or line move re-opens the finding; an edit to the decided line
    re-hashes it, so the new hash carries no decision at all. An `evidence`
    key that is null or malformed never closes (fail closed). A superseded
    record is kept in the new record's `history`; nothing is deleted;
  * a fix-agent `obsolete` verdict recorded on the LATEST pass whose
    `verified_blob` (the file's blob when the fix agent judged it) still equals
    HEAD's blob for that file. A stale verdict never closes; a verdict whose
    code has since changed never closes; without a HEAD blob map nothing closes
    by verdict (fail closed).
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
(the fixcommit.py pattern).

CLI (stdin is always the parsed state object; stdout is JSON):

    python3 carry_state.py finalize-counts [--head-blobs PATH] < state.json
    python3 carry_state.py pending < state.json
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

stdlib only; imports exactly {json, os, sys} (`os` for `os.path.isfile`).
"""

import json
import os
import sys

# Mirror of the 05-state.md `$CARRYFORWARD` allowlist. Never add "audit".
OPEN_STATUSES = ("new", "persisted", "needs-recheck")
DECISIONS = ("dismiss", "defer")
# Lows never block Finalize.
BLOCKING_BANDS = ("critical", "warning", "medium")
_CW_BANDS = ("critical", "warning")

SUBCOMMANDS = ("finalize-counts", "pending", "record-decisions",
               "record-fix-verdicts")
# The ONLY flags this CLI accepts. There is deliberately no flag that carries a
# reason, a hash or a title: such text on a command line is expanded by the
# shell before Python runs.
KNOWN_FLAGS = ("--decisions-file", "--verdicts-file", "--head-blobs")
# subcommand -> (required flags, optional flags)
_FLAGS_BY_SUBCOMMAND = {
    "finalize-counts": ((), ("--head-blobs",)),
    "pending": ((), ()),
    "record-decisions": (("--decisions-file",), ()),
    "record-fix-verdicts": (("--verdicts-file",), ()),
}

USAGE = ("usage: carry_state.py finalize-counts [--head-blobs PATH] | pending"
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


def _fix_closes(record, state, last, head_blobs):
    verdict = state.get("fix_verdicts", {}).get(record["stable_hash"])
    if not isinstance(verdict, dict):
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


def _evidence_of(record):
    """The record's current evidence on EVIDENCE_KEYS: from its snapshot when
    that is a dict, else from the record's own fields (score.py builds the
    next snapshot from those same fields, so the two agree when nothing
    changed). Always a dict."""
    snapshot = record.get("snapshot")
    source = snapshot if isinstance(snapshot, dict) else record
    return {k: source.get(k) for k in EVIDENCE_KEYS}


def _full_evidence(evidence):
    return isinstance(evidence, dict) and all(k in evidence
                                              for k in EVIDENCE_KEYS)


def decision_state(record, state):
    """"current" | "stale" | None for the owner decision on this record.

    None: no decision. "current": a legacy medium acknowledgment, a decision
    that predates evidence binding (not a dict, or a dict with NO `evidence`
    key), or evidence equal to the record's current evidence on all four
    EVIDENCE_KEYS. "stale": any key differs, or the `evidence` key is present
    but null / not a dict / missing a key (fail closed — the writer never
    produces that)."""
    h = record["stable_hash"]
    if h in state.get("medium_acknowledgments", {}):
        return "current"
    decisions = state.get("decisions", {})
    if h not in decisions:
        return None
    decision = decisions[h]
    if not isinstance(decision, dict) or "evidence" not in decision:
        return "current"
    evidence = decision["evidence"]
    if not _full_evidence(evidence):
        return "stale"
    current = _evidence_of(record)
    if all(evidence[k] == current[k] for k in EVIDENCE_KEYS):
        return "current"
    return "stale"


def stale_cause(record, state):
    """None unless the decision is stale; "severity" when only the band
    differs from the decision's evidence, else "code" (including a null or
    malformed `evidence`)."""
    if decision_state(record, state) != "stale":
        return None
    evidence = state.get("decisions", {}).get(record["stable_hash"])
    evidence = evidence.get("evidence") if isinstance(evidence, dict) else None
    if not _full_evidence(evidence):
        return "code"
    current = _evidence_of(record)
    if all(evidence[k] == current[k]
           for k in ("file", "line", "canonical_line_content")):
        return "severity"
    return "code"


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
    """The two gate counts plus the hash lists behind them, or None when the
    state is malformed. `head_blobs` is {file: HEAD blob}; without it a fix
    verdict closes nothing."""
    last, records, reason = _check_state(state)
    if reason is not None:
        return None
    cw = []
    medium = []
    obsolete = []
    for rec in records:
        if _fix_closes(rec, state, last, head_blobs):
            obsolete.append(rec["stable_hash"])
        if _closed(rec, state, last, head_blobs):
            continue
        if rec["band"] in _CW_BANDS:
            cw.append(rec["stable_hash"])
        elif rec["band"] == "medium":
            medium.append(rec["stable_hash"])
    return {
        "outstanding_cw": len(cw),
        "unacknowledged_medium": len(medium),
        "outstanding_cw_hashes": sorted(cw),
        "unacknowledged_medium_hashes": sorted(medium),
        "verified_obsolete_hashes": sorted(obsolete),
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


# --------------------------------------------------------------------------- #
# Writes. Each returns a NEW state object (the input is never mutated) and
# writes exactly one root family; `passes` and `medium_acknowledgments` are
# copied through untouched. The owner creates its family lazily.
# --------------------------------------------------------------------------- #
_DECISION_PAYLOAD_KEYS = ("at_pass", "decisions")
_DECISION_ENTRY_KEYS = ("stable_hash", "decision", "reason")
_VERDICT_PAYLOAD_REQUIRED = ("at_pass", "head_sha", "sent", "results")
_VERDICT_PAYLOAD_OPTIONAL = ("blobs",)


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


def record_decisions(state, payload):
    """Record owner dismiss/defer decisions; the new state, or None on refusal.

    `payload` = {"at_pass": int, "decisions": [{stable_hash, decision, reason}]}.
    The hash must be an open record of the last pass (a member obligation's own
    hash included); the stored band is that record's band, never the payload's.
    The record also stores `evidence`: the finding's current evidence
    (`_evidence_of`), always a four-key dict, never null. A later decision for
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
            "evidence": json.loads(json.dumps(_evidence_of(by_hash[h]))),
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
    return (_is_count(payload["at_pass"])
            and (head is None or isinstance(head, str))
            and isinstance(payload["sent"], list)
            and all(isinstance(h, str) for h in payload["sent"])
            and isinstance(payload["results"], list)
            and all(isinstance(r, dict) for r in payload["results"]))


def record_fix_verdicts(state, payload, skipped=None):
    """Record fix-agent `obsolete` verdicts; the new state, or None on refusal.

    `payload` = {"at_pass", "head_sha", "sent", "results", "blobs"}. A verdict
    is written only for an `obsolete` result whose id is a FULL hash that was
    sent to the fix agent AND is an open record of the last pass AND whose file
    has a blob in `blobs` (the code the fix agent saw). Without that
    fingerprint the verdict could never close anything, so it is not recorded;
    its id is appended to `skipped` when a list is given.

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
        if not (result.get("status") == "obsolete" and isinstance(h, str)
                and h in sent and h in by_hash):
            continue
        blob = blobs.get(by_hash[h].get("file")) if isinstance(blobs,
                                                               dict) else None
        if not isinstance(blob, str):
            if isinstance(skipped, list):
                skipped.append(h)
            continue
        summary = result.get("summary")
        if not isinstance(new.get("fix_verdicts"), dict):
            new["fix_verdicts"] = {}
        new["fix_verdicts"][h] = {
            "verdict": "obsolete",
            "agent": "fix",
            "head_sha": payload["head_sha"],
            "at_pass": payload["at_pass"],
            "verified_blob": blob,
            "reason": "" if summary is None else str(summary),
        }
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


def _load_json_text(text):
    return json.loads(text, parse_constant=_reject_constant)


def read_json_file(path):
    """The parsed file, or None when it is missing or not valid JSON."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return _load_json_text(fh.read())
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
        state = _load_json_text(stdin_text)
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
            sys.stderr.write(REASON_NO_FINGERPRINT)

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
