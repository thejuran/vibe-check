"""harness_record.py — the FLOW-05 run record, written so that it cannot
overstate what a scripted run proves.

`build_record(**fields)` assembles one JSON-able dict per run. It fills the
honesty fields itself, so no caller can set them:

  execution_seconds_label   "automated execution time" — the run is scripted
  waiting_on_owner_seconds  None — nobody waited; nothing was measured (D-13)
  waiting_on_owner_note     says so in words
  would_be_owner_questions  questions + turn-end questions + repeats, i.e.
                            every question a human would have had to answer

`containment` (the 52-14 sandbox facts) and `obligations` (the counts derived
from the verdict's dispositions) are passed in by the driver and never
defaulted: a record must prove the sandbox was on and the obligation ledger
was kept.

`validate_record(record)` returns every problem; `write_record(path, record)`
refuses (RecordError) on any problem and otherwise writes atomically
(tmp + os.replace), so a refused record leaves nothing at `path`.

What a record can never say:
  * a numeric owner-waiting time, or the run's time without its label;
  * that the sandbox was off, could fail open, or allowed an unsandboxed
    retry;
  * COMPLETE after a protected-path denial;
  * COMPLETE with a missing, ambiguous, band-downgraded or unresolved-
    regression obligation (D-15(3));
  * a retained-open count that disagrees with its listed hashes — the owner
    ruled open, non-blocking, visibly retained obligations are an allowed
    terminal state that the record must count AND list;
  * that a ledger with fewer than two snapshots (the seed plus at least one
    observation of the run) watched the run;
  * a copy that lives inside the plugin's source checkout.

Stdlib only.
"""

import json
import os
import re
import tempfile

EXECUTION_LABEL = "automated execution time"
WAITING_NOTE = "not measured — scripted run, no human in the loop"

DECISION_KEYS = ("cards", "questions", "turn_end_questions", "owner_commands",
                 "repeats", "deferred_non_seeded")
CONTAINMENT_KEYS = ("sandbox_enabled", "fail_if_unavailable",
                    "unsandboxed_retry", "probe_fingerprint", "denials",
                    "protected_path_denials")
DISPOSITION_COUNTS = ("resolved", "fix_verified", "decided",
                      "visible_open_nonblocking", "downgraded", "regression",
                      "missing", "ambiguous")
OBLIGATION_KEYS = ("tracked", "snapshots") + DISPOSITION_COUNTS + (
    "visible_open_nonblocking_hashes",)
# A certified run cannot have lost, downgraded or regressed an obligation.
NOT_ON_COMPLETE = ("missing", "ambiguous", "downgraded", "regression")
VERDICTS = ("COMPLETE", "FAILED")
ENTRIES = ("review", "finalize")

REQUIRED_KEYS = (
    "case_id", "mode", "kind", "entry", "plugin_path", "plugin_source_path",
    "plugin_sha", "plugin_snapshot_sha256", "plugin_tree_dirty", "copy_root",
    "cli_version", "model", "setting_sources", "decisions",
    "would_be_owner_questions", "execution_seconds", "execution_seconds_label",
    "harness_answer_seconds", "waiting_on_owner_seconds",
    "waiting_on_owner_note", "clean_tree_checkpoint", "containment",
    "obligations", "verdict", "reasons", "transcript_sha256",
    "manifest_id", "check_digest", "candidate_sha")

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class RecordError(Exception):
    """The record was refused; nothing was written."""


def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) \
        and value >= 0


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and value >= 0


def _question_total(decisions):
    if not isinstance(decisions, dict):
        return None
    parts = [decisions.get(k) for k in ("questions", "turn_end_questions",
                                        "repeats")]
    if not all(_is_count(p) for p in parts):
        return None
    return sum(parts)


def build_record(*, case_id, mode, kind, entry, plugin_path,
                 plugin_source_path, plugin_sha, plugin_snapshot_sha256,
                 plugin_tree_dirty, copy_root, cli_version, model,
                 setting_sources, decisions, execution_seconds,
                 harness_answer_seconds, clean_tree_checkpoint, containment,
                 obligations, verdict, reasons, transcript_sha256,
                 manifest_id, check_digest, candidate_sha):
    """One run record. Keyword arguments only; the honesty fields are fixed
    here and cannot be passed in. `manifest_id`, `check_digest` and
    `candidate_sha` are the freeze identity the pre-launch check verified."""
    return {
        "case_id": case_id,
        "mode": mode,
        "kind": kind,
        "entry": entry,
        "plugin_path": plugin_path,
        "plugin_source_path": plugin_source_path,
        "plugin_sha": plugin_sha,
        "plugin_snapshot_sha256": plugin_snapshot_sha256,
        "plugin_tree_dirty": plugin_tree_dirty,
        "copy_root": copy_root,
        "cli_version": cli_version,
        "model": model,
        "setting_sources": setting_sources,
        "decisions": dict(decisions) if isinstance(decisions, dict)
        else decisions,
        "would_be_owner_questions": _question_total(decisions),
        "execution_seconds": execution_seconds,
        "execution_seconds_label": EXECUTION_LABEL,
        "harness_answer_seconds": harness_answer_seconds,
        "waiting_on_owner_seconds": None,
        "waiting_on_owner_note": WAITING_NOTE,
        "clean_tree_checkpoint": clean_tree_checkpoint,
        "containment": dict(containment) if isinstance(containment, dict)
        else containment,
        "obligations": dict(obligations) if isinstance(obligations, dict)
        else obligations,
        "verdict": verdict,
        "reasons": list(reasons) if isinstance(reasons, (list, tuple))
        else reasons,
        "transcript_sha256": transcript_sha256,
        "manifest_id": manifest_id,
        "check_digest": check_digest,
        "candidate_sha": candidate_sha,
    }


# --------------------------------------------------------------------------- #
# validation: one private function per lock (each is a mutation target)
# --------------------------------------------------------------------------- #
def _timing_problems(record):
    """D-13: scripted timing is labelled; owner-waiting time is never a
    number."""
    problems = []
    if record.get("waiting_on_owner_seconds") is not None:
        problems.append("waiting_on_owner_seconds must be null (not measured)")
    if record.get("waiting_on_owner_note") != WAITING_NOTE:
        problems.append("waiting_on_owner_note is not the not-measured note")
    if record.get("execution_seconds_label") != EXECUTION_LABEL:
        problems.append("execution_seconds_label is not "
                        "\"automated execution time\"")
    if not _is_number(record.get("execution_seconds")):
        problems.append("execution_seconds is not a non-negative number")
    if not _is_number(record.get("harness_answer_seconds")):
        problems.append("harness_answer_seconds is not a non-negative number")
    return problems


def _question_problems(record):
    problems = []
    decisions = record.get("decisions")
    if not isinstance(decisions, dict) or \
            not all(_is_count(decisions.get(k)) for k in DECISION_KEYS):
        problems.append("decisions must carry %s as counts"
                        % ", ".join(DECISION_KEYS))
    total = _question_total(decisions)
    if total is None or record.get("would_be_owner_questions") != total:
        problems.append("would_be_owner_questions is not questions + "
                        "turn_end_questions + repeats")
    return problems


def _containment_problems(record):
    c = record.get("containment")
    if not isinstance(c, dict):
        return ["containment is missing"]
    problems = ["containment.%s is missing" % k for k in CONTAINMENT_KEYS
                if k not in c]
    if c.get("sandbox_enabled") is not True:
        problems.append("containment.sandbox_enabled is not true")
    if c.get("fail_if_unavailable") is not True:
        problems.append("containment.fail_if_unavailable is not true")
    if c.get("unsandboxed_retry") is not False:
        problems.append("containment.unsandboxed_retry is not false")
    for k in ("denials", "protected_path_denials"):
        if k in c and not _is_count(c[k]):
            problems.append("containment.%s is not a count" % k)
    if not isinstance(c.get("probe_fingerprint"), str) \
            or not c.get("probe_fingerprint"):
        problems.append("containment.probe_fingerprint is missing")
    if record.get("verdict") == "COMPLETE" \
            and c.get("protected_path_denials") != 0:
        problems.append("a COMPLETE record has protected-path denials")
    return problems


def _obligation_problems(record):
    o = record.get("obligations")
    if not isinstance(o, dict):
        return ["obligations is missing"]
    missing = [k for k in OBLIGATION_KEYS if k not in o]
    if missing:
        return ["obligations.%s is missing" % k for k in missing]
    problems = []
    counts = ("tracked", "snapshots") + DISPOSITION_COUNTS
    bad = [k for k in counts if not _is_count(o[k])]
    problems.extend("obligations.%s is not a count" % k for k in bad)
    if bad:
        return problems
    if o["tracked"] != sum(o[k] for k in DISPOSITION_COUNTS):
        problems.append("obligations.tracked is not the sum of the "
                        "dispositions")
    if o["tracked"] == 0:
        problems.append("obligations.tracked is zero (the seeded finding "
                        "alone is one)")
    if o["snapshots"] < 2:
        problems.append("obligations.snapshots < 2 (the ledger never "
                        "watched the run)")
    hashes = o["visible_open_nonblocking_hashes"]
    if not (isinstance(hashes, list)
            and all(isinstance(h, str) and h for h in hashes)
            and hashes == sorted(set(hashes))
            and len(hashes) == o["visible_open_nonblocking"]):
        problems.append("obligations.visible_open_nonblocking_hashes must be "
                        "the sorted distinct list of the counted hashes")
    if record.get("verdict") == "COMPLETE":
        for k in NOT_ON_COMPLETE:
            if o[k] > 0:
                problems.append("a COMPLETE record has %s obligations" % k)
    return problems


def _repo_root_of(plugin_source_path):
    """The checkout root of a plugin source at `<repo>/plugins/<name>`
    (lexical)."""
    path = os.path.normpath(plugin_source_path)
    parent = os.path.dirname(path)
    if os.path.basename(parent) == "plugins":
        return os.path.dirname(parent)
    return path


def _is_under(path, root):
    root = root.rstrip("/") or "/"
    return path == root or path.startswith(root + "/")


def _identity_problems(record):
    problems = []
    if record.get("verdict") not in VERDICTS:
        problems.append("verdict is not COMPLETE or FAILED")
    reasons = record.get("reasons")
    if not isinstance(reasons, list) \
            or not all(isinstance(x, str) for x in reasons):
        problems.append("reasons is not a list of strings")
    elif (record.get("verdict") == "COMPLETE") != (not reasons):
        problems.append("verdict and reasons disagree")
    if record.get("entry") not in ENTRIES:
        problems.append("entry is not review or finalize")
    if not isinstance(record.get("plugin_tree_dirty"), bool):
        problems.append("plugin_tree_dirty is not a boolean")
    if not isinstance(record.get("transcript_sha256"), str) \
            or not _SHA256_RE.match(record["transcript_sha256"]):
        problems.append("transcript_sha256 is not a sha256 hex digest")
    for key in ("manifest_id", "check_digest"):
        if not isinstance(record.get(key), str) \
                or not _SHA256_RE.match(record[key]):
            problems.append("%s is not a sha256 hex digest" % key)
    if not isinstance(record.get("candidate_sha"), str) \
            or not _COMMIT_RE.match(record["candidate_sha"]):
        problems.append("candidate_sha is not a 40-hex commit")
    source = record.get("plugin_source_path")
    copy_root = record.get("copy_root")
    if not isinstance(source, str) or not os.path.isabs(source):
        problems.append("plugin_source_path is not an absolute path")
    elif not isinstance(copy_root, str) or not os.path.isabs(copy_root):
        problems.append("copy_root is not an absolute path")
    elif _is_under(os.path.normpath(copy_root), _repo_root_of(source)):
        problems.append("copy_root is inside the plugin's source checkout")
    return problems


def validate_record(record):
    """Every problem with `record`; [] when it may be written."""
    if not isinstance(record, dict):
        return ["record is not an object"]
    missing = [k for k in REQUIRED_KEYS if k not in record]
    problems = ["missing key: %s" % k for k in missing]
    return (problems + _timing_problems(record) + _question_problems(record)
            + _containment_problems(record) + _obligation_problems(record)
            + _identity_problems(record))


def write_record(path, record):
    """Validate, then write `record` to `path` atomically. Raises RecordError
    (and writes nothing) on any problem."""
    problems = validate_record(record)
    if problems:
        raise RecordError("; ".join(problems))
    data = json.dumps(record, indent=2, sort_keys=True,
                      ensure_ascii=False) + "\n"
    parent = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".run-", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
