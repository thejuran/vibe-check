"""replay.py — offline re-scoring of the archived B3 runs (SCORER-01).

A scorer change is only allowed to cost an owner run after it has been shown,
offline, that it silences none of the recorded catches. This module rebuilds
each archived run's score.py input envelope from committed evidence, re-scores
it through the REAL scorer (the baseline blob, a committed revision, or a file
under this scripts directory, optionally with named module constants
overridden), measures how faithfully the baseline reproduces the archive, and
gates a candidate on the zero-catch-regression guardrail.

Evidence rules:

* Input is ONLY the committed archives under `docs/design/b3-ground-truth/`
  (`runs/`, `runs-v2.10/`, `runs-v2.10-phase40/`) plus the committed catch
  manifest and supersession ledger. Never `.turingmind/state/`, never a
  reviewed repository.
* A scoreable run is a directory named `run-<N>` holding `state.json`; the
  `run-N.failed-<epoch>` directories are excluded by that rule.
* Envelope reconstruction is one rule for every run: the survivors of the last
  pass with the scorer-written keys removed, the hunk ranges (context included)
  of the run's own `tree.diff` as `changed_line_ranges`, `command:
  deep-review`, no carry-forward, zero-config knobs; runs that kept a
  `transcript.jsonl` also get the agents' raw returns that did not survive.
* Codex participation in the replayed envelope is inferred from the archived
  survivors' `agent` field, never from the pass-level record.
* The scorer is imported ONLY from `plugins/vibe-check/scripts/score.py` in
  this repository or from a git blob/revision of that path. Nothing found in
  an archive is ever imported or executed; transcripts are parsed as data.
* Every comparison of a candidate is against the BASELINE REPLAY, never
  against a band recorded in an archive. Baseline fidelity drift is disclosed
  and never removes a run from the protected set: the guardrail denominator is
  always the manifest's 26 protected catch runs.

Output rule: reports and messages name agent / file / line / band / score /
stable_hash only — never a finding title, `problem` text, or transcript text.

Imports exactly {argparse, hashlib, importlib, json, os, re, shutil,
subprocess, sys, tempfile, time}; every git call carries a 120-second
timeout.

    python3 replay.py census
    python3 replay.py check-manifest [--manifest <abs>]
    python3 replay.py dump-envelope <run-rel-path>
    python3 replay.py baseline --out <md> [--manifest <abs>]
    python3 replay.py candidate --name <slug> --scorer <spec>
        [--override NAME=JSON ...] --out <md> [--manifest <abs>]

A scorer spec is `blob:<sha>`, `rev:<rev>` or `path:<abs>`.
Exit 0 clean / 1 gate failure / 2 usage error or unreadable input.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

GROUND_TRUTH_REL = "docs/design/b3-ground-truth"
ARCHIVE_ROOTS = ("docs/design/b3-ground-truth/runs",
                 "docs/design/b3-ground-truth/runs-v2.10",
                 "docs/design/b3-ground-truth/runs-v2.10-phase40")
MANIFEST_REL = "docs/design/b3-ground-truth/REPLAY-CATCH-MANIFEST-v2.10.json"
LEDGER_REL = "docs/design/b3-ground-truth/SUPERSESSIONS-v2.10.md"
SCORE_REL = "plugins/vibe-check/scripts/score.py"
SCRIPTS_DIR_REL = os.path.join("plugins", "vibe-check", "scripts")

# The pre-Wave-1 score.py (the last revision before the Phase-41 scorer
# changes). A blob, not a commit: it is stable under rebase and cherry-pick.
# The v2.9 archives were scored by earlier revisions; that is part of the
# disclosed fidelity drift.
BASELINE_SCORE_BLOB = "b21f7f3d556e1522e9853511ed8e126057c417c0"

RUN_DIR_RE = re.compile(r"^run-[0-9]+$")
EXPECTED_SCOREABLE = 66
# D-05: the guardrail denominator is ALWAYS every recorded catch.
EXPECTED_PROTECTED = 26

SCORED_KEYS = ("orchestrator_score", "band", "stable_hash", "attribution", "status", "members")
CODEX_AGENT = "codex-adversarial"

_HUNK_RE = re.compile(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@")
_RESULT_RE = re.compile(r"<result>(.*?)</result>", re.DOTALL)
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
_REV_RE = re.compile(r"^[A-Za-z0-9._/~^-]+$")
_OVERRIDE_NAME_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_HANDBACK_TOOL = "SubagentHandback"
# Records that deliver a subagent's task notification: the queued copy and,
# when the orchestrator was idle, the user-turn copy (dedupe collapses both).
_NOTIFICATION_RECORDS = ("user", "queue-operation")


class ReplayError(Exception):
    """An input the harness refuses or cannot read (exit 2)."""


def _abs(rel, repo_root=REPO_ROOT):
    return os.path.join(repo_root, rel)


def _read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path):
    with open(path, "rb") as fh:
        return _sha256_bytes(fh.read())


# --------------------------------------------------------------------------- #
# Archive walk
# --------------------------------------------------------------------------- #

def excluded_run_dirs(repo_root=REPO_ROOT):
    """Directories that look like runs but are not scoreable (`run-N.failed-*`)."""
    out = []
    for root_rel in ARCHIVE_ROOTS:
        base = _abs(root_rel, repo_root)
        for dirpath, dirnames, _files in os.walk(base):
            for d in dirnames:
                if d.startswith("run-") and not RUN_DIR_RE.match(d):
                    out.append(os.path.relpath(os.path.join(dirpath, d),
                                               _abs(GROUND_TRUTH_REL, repo_root)))
    return sorted(out)


def iter_runs(repo_root=REPO_ROOT):
    """Every scoreable archived run, sorted by rel_path.

    Each record: rel_path (relative to docs/design/b3-ground-truth/, the
    manifest's key space), archive (root basename), diff (diff directory name),
    state (parsed state.json), tree_diff (text, or None when missing),
    transcript_path (absolute, or None), problems (fixed strings).
    """
    gt_root = _abs(GROUND_TRUTH_REL, repo_root)
    runs = []
    for root_rel in ARCHIVE_ROOTS:
        base = _abs(root_rel, repo_root)
        archive = os.path.basename(root_rel)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames.sort()
            if not RUN_DIR_RE.match(os.path.basename(dirpath)):
                continue
            if "state.json" not in filenames:
                continue
            rel_path = os.path.relpath(dirpath, gt_root).replace(os.sep, "/")
            with open(os.path.join(dirpath, "state.json"), encoding="utf-8") as fh:
                state = json.load(fh)
            problems = []
            tree_diff = None
            diff_path = os.path.join(dirpath, "tree.diff")
            if os.path.isfile(diff_path):
                with open(diff_path, encoding="utf-8", errors="replace") as fh:
                    tree_diff = fh.read()
            else:
                problems.append(rel_path + ": missing tree.diff")
            tp = os.path.join(dirpath, "transcript.jsonl")
            runs.append({
                "rel_path": rel_path,
                "archive": archive,
                "diff": os.path.basename(os.path.dirname(dirpath)),
                "state": state,
                "tree_diff": tree_diff,
                "transcript_path": tp if os.path.isfile(tp) else None,
                "problems": problems,
            })
    runs.sort(key=lambda r: r["rel_path"])
    return runs


def _run_index(runs):
    return {r["rel_path"]: r for r in runs}


# --------------------------------------------------------------------------- #
# Envelope reconstruction
# --------------------------------------------------------------------------- #

def hunk_ranges(diff_text):
    """{file: [[start, end], ...]} from the new-side hunk headers, context included."""
    out = {}
    cur = None
    for ln in (diff_text or "").splitlines():
        if ln.startswith("+++ "):
            p = ln[4:].strip()
            if p == "/dev/null":
                cur = None
            else:
                cur = p[2:] if p.startswith("b/") else p
            continue
        m = _HUNK_RE.match(ln)
        if m and cur:
            start = int(m.group(1))
            count = int(m.group(2)) if m.group(2) is not None else 1
            if count > 0:
                out.setdefault(cur, []).append([start, start + count - 1])
    return out


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _decode_object(text):
    """The first JSON object in `text` (an agent return may be fenced), else None."""
    if not isinstance(text, str):
        return None
    start = text.find("{")
    if start < 0:
        return None
    try:
        obj, _end = json.JSONDecoder().raw_decode(text[start:])
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def _line_objects(text):
    """Every JSON object that starts at the beginning of a line of `text`."""
    decoder = json.JSONDecoder()
    offset = 0
    for line in text.splitlines(True):
        if line.startswith("{"):
            try:
                obj, _end = decoder.raw_decode(text, offset)
            except ValueError:
                obj = None
            if isinstance(obj, dict):
                yield obj
        offset += len(line)


def _tool_result_texts(content):
    for c in content:
        if not isinstance(c, dict) or c.get("type") != "tool_result":
            continue
        inner = c.get("content")
        if isinstance(inner, str):
            yield inner
        elif isinstance(inner, list):
            for part in inner:
                if (isinstance(part, dict) and part.get("type") == "text"
                        and isinstance(part.get("text"), str)):
                    yield part["text"]


def _accept_return(obj, sink, seen):
    if not isinstance(obj, dict) or not isinstance(obj.get("findings"), list):
        return
    agent = obj.get("agent")
    for f in obj["findings"]:
        if not isinstance(f, dict):
            continue
        item = {"agent": agent, "finding": f}
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            sink.append(item)


def recover_transcript_findings(transcript_path, meta=None):
    """Raw agent findings from a Phase-40 transcript, as [{"agent", "finding"}].

    Only three channels are read, because a looser scan also matches the
    example JSON inside templates the orchestrator Read and files it Wrote:
      A. `<result>` bodies inside the strings of `user` message content or a
         `queue-operation` record's content (subagent task notifications);
      B. `assistant` tool_use named SubagentHandback -> input.message;
      C. a `user` tool_result text holding, at the start of a line, a JSON
         object whose top-level agent is codex-adversarial (the codex
         translator's output, usually after a label line). A codex object
         that only ever appears inside an orchestrator Write payload is not
         recovered: Write payloads are not a channel.
    Malformed lines are skipped and counted in meta["malformed"].
    """
    found, seen = [], set()
    malformed = 0
    with open(transcript_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                malformed += 1
                continue
            if not isinstance(rec, dict):
                malformed += 1
                continue
            kind = rec.get("type")
            msg = rec.get("message")
            content = msg.get("content") if isinstance(msg, dict) else None
            if kind in _NOTIFICATION_RECORDS:
                carrier = msg if kind == "user" else rec.get("content")
                for s in _strings(carrier):
                    for body in _RESULT_RE.findall(s):
                        _accept_return(_decode_object(body), found, seen)
            if kind == "user" and isinstance(content, list):
                for text in _tool_result_texts(content):
                    for obj in _line_objects(text):
                        if obj.get("agent") == CODEX_AGENT:
                            _accept_return(obj, found, seen)
            elif kind == "assistant" and isinstance(content, list):
                for c in content:
                    if (isinstance(c, dict) and c.get("type") == "tool_use"
                            and c.get("name") == _HANDBACK_TOOL):
                        inp = c.get("input") if isinstance(c.get("input"), dict) else {}
                        message = inp.get("message")
                        obj = message if isinstance(message, dict) else _decode_object(message)
                        _accept_return(obj, found, seen)
    if meta is not None:
        meta["malformed"] = malformed
    return found


def _finding_key(agent, f):
    return (agent, f.get("file"), f.get("line"), f.get("title"))


def reconstruct_envelope(run):
    """(envelope, meta) for one archived run. meta: codex_joined, survivors, recovered."""
    passes = run["state"].get("passes") or []
    if not passes:
        raise ReplayError(run["rel_path"] + ": state has no passes")
    archived = passes[-1].get("findings") or []
    survivors = [{k: v for k, v in f.items() if k not in SCORED_KEYS}
                 for f in archived if isinstance(f, dict)]
    survivor_keys = {_finding_key(f.get("agent"), f) for f in survivors}
    recovered = []
    malformed = 0
    unrecovered = None
    if run.get("transcript_path"):
        tmeta = {}
        items = recover_transcript_findings(run["transcript_path"], tmeta)
        unrecovered = sorted({f.get("agent") for f in survivors if f.get("agent")}
                             - {i["agent"] for i in items})
        for item in items:
            f = dict(item["finding"])
            if item["agent"] is not None:
                f["agent"] = item["agent"]
            for k in SCORED_KEYS:
                f.pop(k, None)
            key = _finding_key(f.get("agent"), f)
            if key in survivor_keys:
                continue
            survivor_keys.add(key)
            recovered.append(f)
        malformed = tmeta.get("malformed", 0)
    codex_joined = any(f.get("agent") == CODEX_AGENT for f in survivors)
    envelope = {
        "command": "deep-review",
        "all_mode": False,
        "pass_number": 1,
        "carryforward": [],
        "changed_line_ranges": hunk_ranges(run.get("tree_diff") or ""),
        "findings": survivors + recovered,
        "codex": {"status": "joined" if codex_joined else "skipped"},
    }
    meta = {"codex_joined": codex_joined, "survivors": len(survivors),
            "recovered": len(recovered), "malformed": malformed,
            "has_transcript": bool(run.get("transcript_path")),
            "unrecovered_agents": unrecovered}
    return envelope, meta


# --------------------------------------------------------------------------- #
# Scorer loading
# --------------------------------------------------------------------------- #

def _git(*argv):
    proc = subprocess.run(["git", "-C", REPO_ROOT, *argv],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=120)
    if proc.returncode != 0:
        raise ReplayError("git %s failed (exit %d)" % (argv[0], proc.returncode))
    return proc.stdout


_LOAD_COUNTER = [0]


def load_scorer(spec, overrides=None):
    """Import the real scorer named by `spec`; set each override as a module attribute.

    spec: `blob:<sha>` | `rev:<rev>` (the score.py path at that revision) |
    `path:<abs>` (must resolve inside plugins/vibe-check/scripts/ of this repo).
    The returned module carries `_replay_spec` and `_replay_sha256` (of its text).
    """
    if not isinstance(spec, str) or ":" not in spec:
        raise ReplayError("refused: scorer spec must be blob:<sha>, rev:<rev> or path:<abs>")
    kind, _, value = spec.partition(":")
    tmpdir = None
    try:
        if kind == "blob":
            if not _SHA_RE.match(value):
                raise ReplayError("refused: blob must be a hex object id")
            data = _git("cat-file", "-p", value)
        elif kind == "rev":
            if not _REV_RE.match(value) or value.startswith("-"):
                raise ReplayError("refused: rev contains characters outside [A-Za-z0-9._/~^-]")
            data = _git("show", value + ":" + SCORE_REL)
        elif kind == "path":
            real = os.path.realpath(value)
            allowed = os.path.join(os.path.realpath(REPO_ROOT), SCRIPTS_DIR_REL) + os.sep
            if not real.startswith(allowed) or not os.path.isfile(real):
                raise ReplayError("refused: scorer path outside plugins/vibe-check/scripts")
            with open(real, "rb") as fh:
                data = fh.read()
        else:
            raise ReplayError("refused: unknown scorer spec kind")
        tmpdir = tempfile.mkdtemp(prefix="replay-scorer-")
        src = os.path.join(tmpdir, "score_candidate.py")
        with open(src, "wb") as fh:
            fh.write(data)
        _LOAD_COUNTER[0] += 1
        name = "replay_scorer_%d" % _LOAD_COUNTER[0]
        mod_spec = importlib.util.spec_from_file_location(name, src)
        module = importlib.util.module_from_spec(mod_spec)
        mod_spec.loader.exec_module(module)
    finally:
        if tmpdir is not None:
            shutil.rmtree(tmpdir, ignore_errors=True)
    for attr, val in (overrides or {}).items():
        if not _OVERRIDE_NAME_RE.match(attr):
            raise ReplayError("refused: override name must be an UPPER_CASE constant")
        if not hasattr(module, attr):
            raise ReplayError("refused: override names no existing scorer constant: " + attr)
        setattr(module, attr, val)
    module._replay_spec = spec
    module._replay_sha256 = _sha256_bytes(data)
    return module


def replay_run(scorer, envelope):
    return scorer.run(json.loads(json.dumps(envelope)))


def fires(result):
    return any(isinstance(f, dict) and f.get("band") in ("critical", "warning")
               for f in result.get("findings", []))


def _triple(f):
    return (str(f.get("band")), f.get("orchestrator_score")
            if isinstance(f.get("orchestrator_score"), int) else -1,
            str(f.get("stable_hash")))


def fidelity(archived_pass, result):
    """(exact, detail): exact iff the (band, score, stable_hash) multisets agree."""
    archived = sorted(_triple(f) for f in archived_pass.get("findings") or []
                      if isinstance(f, dict))
    replayed = sorted(_triple(f) for f in result.get("findings") or []
                      if isinstance(f, dict))
    if archived == replayed:
        return True, "exact"
    a_bands = {}
    for band, _s, h in archived:
        a_bands.setdefault(h, set()).add(band)
    r_bands = {}
    for band, _s, h in replayed:
        r_bands.setdefault(h, set()).add(band)
    archived_only = sorted(set(a_bands) - set(r_bands))
    replay_only = sorted(set(r_bands) - set(a_bands))
    band_moved = sorted(h for h in set(a_bands) & set(r_bands) if a_bands[h] != r_bands[h])
    score_moved = len([1 for t in archived if t not in replayed])
    if sorted(t[:2] for t in archived) == sorted(t[:2] for t in replayed):
        cause = "stable_hash only (band and score multisets agree)"
    elif band_moved:
        cause = "score/band moved"
    elif archived_only and not replay_only:
        cause = "archived row not re-emitted"
    else:
        cause = "score moved"
    detail = ("archived-only %d · replay-only %d · band-moved %d · rows-differing %d · cause: %s"
              % (len(archived_only), len(replay_only), len(band_moved), score_moved, cause))
    return False, detail


# --------------------------------------------------------------------------- #
# Manifest
# --------------------------------------------------------------------------- #

EXPECTED_CATCH_RUNS = 29
EXPECTED_CALIBRATION = 21
EXPECTED_QUIET = {"headline": 18, "phase40": 6, "v29_informational": 9}
EXPECTED_EXCLUDED = {"should-quiet-7": 3}
_LEDGER_ENTRY_RE = re.compile(r"^[0-9]{3}$")
_LEDGER_HEADING_RE = re.compile(r"^## ([0-9]{3}) —", re.MULTILINE)


def load_manifest(repo_root=REPO_ROOT, path=None):
    """The committed catch manifest (or, for the mutation proofs, `path`)."""
    manifest_path = path or _abs(MANIFEST_REL, repo_root)
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("catch_runs"), dict):
        raise ReplayError("manifest has no catch_runs object")
    return manifest


def _protected_runs(manifest):
    return sorted(k for k, e in manifest.get("catch_runs", {}).items()
                  if isinstance(e, dict) and e.get("guardrail") is True)


def _in_site(finding, site):
    if not isinstance(site, dict) or finding.get("file") != site.get("file"):
        return False
    line = finding.get("line")
    if not isinstance(line, int) or isinstance(line, bool):
        return False
    for pair in site.get("lines") or []:
        if (isinstance(pair, (list, tuple)) and len(pair) == 2
                and pair[0] <= line <= pair[1]):
            return True
    return False


def _resolution_key(f):
    return (f.get("agent"), f.get("line"), f.get("title"), f.get("stable_hash"))


def _at(f):
    return "%s@%s" % (f.get("agent"), f.get("line"))


def check_manifest(manifest, runs, ledger_text=None):
    """Problems as fixed strings (run path + kind; agent@line, never a title)."""
    problems = []
    idx = _run_index(runs)
    catch = manifest.get("catch_runs") or {}
    guard_n = len(_protected_runs(manifest))
    calib_n = sum(1 for e in catch.values() if isinstance(e, dict) and e.get("calibration") is True)
    if len(catch) != EXPECTED_CATCH_RUNS:
        problems.append("manifest: catch_runs %d != %d" % (len(catch), EXPECTED_CATCH_RUNS))
    if guard_n != EXPECTED_PROTECTED:
        problems.append("manifest: guardrail runs %d != %d" % (guard_n, EXPECTED_PROTECTED))
    if calib_n != EXPECTED_CALIBRATION:
        problems.append("manifest: calibration runs %d != %d" % (calib_n, EXPECTED_CALIBRATION))
    for group, want in EXPECTED_QUIET.items():
        paths = (manifest.get("quiet_runs") or {}).get(group) or []
        if len(paths) != want:
            problems.append("manifest: quiet_runs.%s %d != %d" % (group, len(paths), want))
        for p in paths:
            if p not in idx:
                problems.append("%s: quiet run not found" % p)
    for group, want in EXPECTED_EXCLUDED.items():
        paths = (manifest.get("excluded_runs") or {}).get(group) or []
        if len(paths) != want:
            problems.append("manifest: excluded_runs.%s %d != %d" % (group, len(paths), want))
        for p in paths:
            if p not in idx:
                problems.append("%s: excluded run not found" % p)
    for run_path in sorted(catch):
        entry = catch[run_path]
        if ".failed" in run_path:
            problems.append("%s: non-scoreable run listed" % run_path)
            continue
        if run_path not in idx:
            problems.append("%s: run not found" % run_path)
            continue
        if not isinstance(entry, dict):
            problems.append("%s: entry is not an object" % run_path)
            continue
        archived = [f for f in (idx[run_path]["state"]["passes"][-1].get("findings") or [])
                    if isinstance(f, dict)]
        survivors = entry.get("survivors_at_site") or []
        listed = set()
        for s in survivors:
            key = _resolution_key(s)
            matches = [f for f in archived if _resolution_key(f) == key]
            if len(matches) != 1:
                problems.append("%s: unresolved survivor %s" % (run_path, _at(s)))
            listed.add(key)
        for f in archived:
            if _in_site(f, entry.get("site")) and _resolution_key(f) not in listed:
                problems.append("%s: survivor at SITE missing from manifest %s"
                                % (run_path, _at(f)))
        if not any(s.get("axis") is True for s in survivors):
            problems.append("%s: no axis=true survivor at SITE" % run_path)
    amendments = manifest.get("guardrail_amendments", {})
    if not isinstance(amendments, dict):
        problems.append("manifest: guardrail_amendments is not an object")
        amendments = {}
    if amendments:
        if ledger_text is None:
            ledger_text = _read_text(_abs(LEDGER_REL))
        headings = set(_LEDGER_HEADING_RE.findall(ledger_text))
        protected = set(_protected_runs(manifest))
        for run_path in sorted(amendments):
            amend = amendments[run_path]
            if run_path not in protected:
                problems.append("%s: amendment for a non-protected run" % run_path)
            entry_no = amend.get("ledger_entry") if isinstance(amend, dict) else None
            if not isinstance(entry_no, str) or not _LEDGER_ENTRY_RE.match(entry_no):
                problems.append("%s: amendment ledger entry malformed" % run_path)
            elif entry_no not in headings:
                problems.append("%s: amendment ledger entry %s not found" % (run_path, entry_no))
            if not isinstance(amend, dict) or not amend.get("reason"):
                problems.append("%s: amendment has no reason" % run_path)
    return problems


# --------------------------------------------------------------------------- #
# Guardrail
# --------------------------------------------------------------------------- #

_BAND_RANK = {"critical": 3, "warning": 2, "medium": 1, None: 0}


def _rank(band):
    return _BAND_RANK.get(band, 0)


def _rows_at_site(result, site):
    return [f for f in (result or {}).get("findings") or []
            if isinstance(f, dict) and _in_site(f, site)]


def catch_status(result, entry):
    """(ok, basis): SITE + BAND >= floor on the surviving row, AXIS on its own
    title or any members[].title (SUPERSESSIONS-v2.10.md entry 007)."""
    site = entry.get("site")
    rows = _rows_at_site(result, site)
    if not rows:
        return False, "no-row-at-site"
    floor = _rank(entry.get("floor"))
    qualifying = [f for f in rows if _rank(f.get("band")) >= floor]
    if not qualifying:
        return False, "below-floor"
    axis_true = {(s.get("agent"), s.get("title"))
                 for s in entry.get("survivors_at_site") or []
                 if isinstance(s, dict) and s.get("axis") is True}
    for row in qualifying:
        if (row.get("agent"), row.get("title")) in axis_true:
            return True, "survivor-title"
        members = row.get("members")
        for m in members if isinstance(members, list) else []:
            if isinstance(m, dict) and (m.get("agent"), m.get("title")) in axis_true:
                return True, "member-title"
    return False, "axis-false"


def protected_status(base_results, manifest):
    """Baseline reproduction of EVERY protected catch (exactly EXPECTED_PROTECTED)."""
    protected = _protected_runs(manifest)
    if len(protected) != EXPECTED_PROTECTED:
        raise ReplayError("manifest protects %d runs; D-05 requires %d"
                          % (len(protected), EXPECTED_PROTECTED))
    amendments = manifest.get("guardrail_amendments") or {}
    out = {}
    for run_path in protected:
        entry = manifest["catch_runs"][run_path]
        if run_path in base_results:
            ok, basis = catch_status(base_results[run_path], entry)
        else:
            ok, basis = False, "not-replayed"
        if ok:
            out[run_path] = {"status": "REPRODUCED", "basis": basis, "ledger_entry": None}
        elif run_path in amendments:
            amend = amendments[run_path]
            out[run_path] = {"status": "AMENDED", "basis": basis,
                             "ledger_entry": amend.get("ledger_entry")
                             if isinstance(amend, dict) else None}
        else:
            out[run_path] = {"status": "UNEVALUABLE", "basis": basis, "ledger_entry": None}
    return out


def guardrail(base_results, cand_results, manifest):
    """Candidate vs BASELINE REPLAY for every protected run; fails closed."""
    prot = protected_status(base_results, manifest)
    out = {}
    for run_path, ps in prot.items():
        entry = manifest["catch_runs"][run_path]
        if run_path in cand_results:
            cand_ok, cand_basis = catch_status(cand_results[run_path], entry)
        else:
            cand_ok, cand_basis = False, "not-replayed"
        if ps["status"] == "REPRODUCED":
            status = "kept" if cand_ok else "REGRESSED"
        else:
            status = ps["status"]
        out[run_path] = {"status": status, "base": ps["basis"], "cand": cand_basis,
                         "ledger_entry": ps["ledger_entry"]}
    return out


def fp_prediction(results, paths):
    """A run is a false positive iff it fires any critical/warning row."""
    fired = []
    for p in paths:
        if p not in results:
            raise ReplayError("%s: no replay result" % p)
        if fires(results[p]):
            fired.append(p)
    return {"fired": fired, "count": len(fired), "denominator": len(paths)}


# --------------------------------------------------------------------------- #
# Report writer
# --------------------------------------------------------------------------- #

_ROW_COLUMNS = ("agent", "file", "line", "band", "score", "stable_hash")


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def _finding_row(f):
    """The ONLY projection of a finding that reaches a report."""
    h = f.get("stable_hash")
    return "| %s |" % " | ".join(_cell(v) for v in (
        f.get("agent"), f.get("file"), f.get("line"), f.get("band"),
        f.get("orchestrator_score"), h[:12] if isinstance(h, str) else h))


# --------------------------------------------------------------------------- #
# Public helper surface for sibling measurement scripts (lanearchive.py,
# score43.py). Siblings use THESE names; the underscore originals stay as the
# in-module spellings (and for test_replay.py), so renaming or reshaping one of
# them must keep its public alias here in step.
# --------------------------------------------------------------------------- #

RESULT_RE = _RESULT_RE
HANDBACK_TOOL = _HANDBACK_TOOL
decode_object = _decode_object
tool_result_texts = _tool_result_texts
rank = _rank
rows_at_site = _rows_at_site
finding_row = _finding_row


def write_report(path, header, sections):
    """Markdown report. header: [(label, value)]; sections: [{"heading", "body":
    [lines], "tables": [(caption, [finding dicts])]}]. Finding dicts are rendered
    through `_finding_row` only, so titles and problem text never reach the file."""
    lines = []
    for label, value in header:
        if label == "#":
            lines += ["# " + str(value), ""]
        else:
            lines.append("- %s: %s" % (label, value))
    lines += ["", "_no rounding — exact fractions_", ""]
    for sec in sections:
        lines += ["## " + sec["heading"], ""]
        lines += list(sec.get("body") or [])
        for caption, findings in sec.get("tables") or []:
            lines += ["", caption, "", "| %s |" % " | ".join(_ROW_COLUMNS),
                      "|" + "---|" * len(_ROW_COLUMNS)]
            lines += [_finding_row(f) for f in findings if isinstance(f, dict)]
        lines.append("")
    text = "\n".join(lines)
    if '"title"' in text or "<result>" in text:
        raise ReplayError("report writer refused: forbidden token in report text")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# --------------------------------------------------------------------------- #
# Batch replay + CLI
# --------------------------------------------------------------------------- #

def replay_all(scorer, runs):
    """{rel_path: {"result", "meta", "exact", "detail"}} for every run."""
    out = {}
    for run in runs:
        envelope, meta = reconstruct_envelope(run)
        result = replay_run(scorer, envelope)
        exact, detail = fidelity(run["state"]["passes"][-1], result)
        out[run["rel_path"]] = {"result": result, "meta": meta,
                                "exact": exact, "detail": detail}
    return out


def _head_sha():
    try:
        return _git("rev-parse", "HEAD").decode("ascii", "replace").strip()
    except (ReplayError, OSError, subprocess.SubprocessError):
        return "unknown"


def _utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _fidelity_lines(runs, replays):
    exact_n = sum(1 for r in runs if replays[r["rel_path"]]["exact"])
    table = ["| run | exact | recovered | detail |", "|---|---|---|---|"]
    drift = []
    for r in runs:
        rp = replays[r["rel_path"]]
        rec = ("recovered: %d" % rp["meta"]["recovered"]) if rp["meta"]["has_transcript"] else "—"
        table.append("| %s | %s | %s | %s |" % (r["rel_path"], "yes" if rp["exact"] else "no",
                                                 rec, rp["detail"]))
        if not rp["exact"]:
            drift.append("- %s — %s" % (r["rel_path"], rp["detail"]))
    return exact_n, table, drift


def _cmd_census(repo_root=REPO_ROOT):
    runs = iter_runs(repo_root)
    per = {}
    for r in runs:
        per[r["archive"]] = per.get(r["archive"], 0) + 1
    for root_rel in ARCHIVE_ROOTS:
        name = os.path.basename(root_rel)
        sys.stdout.write("%s: %d\n" % (name, per.get(name, 0)))
    for d in excluded_run_dirs(repo_root):
        sys.stdout.write("excluded: %s\n" % d)
    sys.stdout.write("transcripts: %d\n" % sum(1 for r in runs if r["transcript_path"]))
    sys.stdout.write("scoreable: %d\n" % len(runs))
    for r in runs:
        for p in r["problems"]:
            sys.stderr.write(p + "\n")
    return 0 if len(runs) == EXPECTED_SCOREABLE else 1


def _cmd_dump_envelope(rel_path):
    idx = _run_index(iter_runs())
    if rel_path not in idx:
        sys.stderr.write("unknown run: not a scoreable run path\n")
        return 2
    envelope, _meta = reconstruct_envelope(idx[rel_path])
    sys.stdout.write(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    return 0


def _manifest_header(manifest_path, manifest):
    return [
        ("manifest", os.path.relpath(manifest_path, REPO_ROOT)),
        ("manifest sha256", _sha256_file(manifest_path)),
        ("amendments in force", str(len(manifest.get("guardrail_amendments") or {}))),
        ("HEAD", _head_sha()),
        ("generated (UTC)", _utc_now()),
    ]


def _load_checked_manifest(runs, manifest_path):
    """(manifest, path) or None after printing every problem on stderr."""
    path = manifest_path or _abs(MANIFEST_REL)
    manifest = load_manifest(path=path)
    problems = check_manifest(manifest, runs)
    for p in problems:
        sys.stderr.write(p + "\n")
    return (None, path) if problems else (manifest, path)


def _protected_section(prot):
    counts = {k: sum(1 for v in prot.values() if v["status"] == k)
              for k in ("REPRODUCED", "UNEVALUABLE", "AMENDED")}
    body = ["| run | status | basis | ledger entry |", "|---|---|---|---|"]
    for run_path in sorted(prot):
        v = prot[run_path]
        body.append("| %s | %s | %s | %s |" % (run_path, v["status"], v["basis"],
                                              v["ledger_entry"] or "—"))
    body += ["", "REPRODUCED %d / %d · UNEVALUABLE %d · AMENDED %d"
             % (counts["REPRODUCED"], EXPECTED_PROTECTED, counts["UNEVALUABLE"],
                counts["AMENDED"])]
    section = {"heading": "Protected catches — %d (D-05) — baseline reproduction"
               % EXPECTED_PROTECTED, "body": body}
    return section, counts


def _report_unevaluable(prot):
    for run_path in sorted(prot):
        if prot[run_path]["status"] == "UNEVALUABLE":
            sys.stderr.write("UNEVALUABLE: %s (%s) — repair reconstruction or obtain an "
                             "owner amendment (SUPERSESSIONS-v2.10.md)\n"
                             % (run_path, prot[run_path]["basis"]))


def _fidelity_section(runs, replays, heading):
    exact_n, table, drift = _fidelity_lines(runs, replays)
    return exact_n, [
        {"heading": "Fidelity summary",
         "body": ["**%d/%d exact** (the replay's (band, score, stable_hash) multiset equals "
                  "the archive's)" % (exact_n, len(runs))]},
        {"heading": heading, "body": drift or ["- none"]},
        {"heading": "Fidelity per run", "body": table},
    ]


def _coverage_section(runs, replays):
    """Which runs had a transcript, and which surviving agents it did not carry."""
    with_t = [r["rel_path"] for r in runs if replays[r["rel_path"]]["meta"]["has_transcript"]]
    gaps = [(p, replays[p]["meta"]["unrecovered_agents"]) for p in with_t
            if replays[p]["meta"]["unrecovered_agents"]]
    body = ["%d / %d runs carry a session transcript (Phase-40 archives). The other %d runs are "
            "replayed from their state.json survivors only: findings the original scorer dropped "
            "were never archived for them." % (len(with_t), len(runs), len(runs) - len(with_t)),
            "",
            "%d / %d transcript runs recover a return for every surviving agent."
            % (len(with_t) - len(gaps), len(with_t))]
    if gaps:
        body += ["", "Surviving agents with no return on any recovery channel. The survivor "
                 "itself is exact from state.json, but none of that agent's non-surviving "
                 "findings can be recovered. In the archived runs this happens when the agent's "
                 "output reached the orchestrator only inside a file the orchestrator wrote, "
                 "which is not a recovery channel:", ""]
        body += ["- %s — %s" % (p, ", ".join(agents)) for p, agents in gaps]
    return {"heading": "Transcript coverage (disclosed)", "body": body}


def _cmd_check_manifest(manifest_path):
    manifest, _path = _load_checked_manifest(iter_runs(), manifest_path)
    return 0 if manifest is not None else 1


def _cmd_baseline(out_path, manifest_path=None):
    runs = iter_runs()
    manifest, mpath = _load_checked_manifest(runs, manifest_path)
    if manifest is None:
        return 1
    scorer = load_scorer("blob:" + BASELINE_SCORE_BLOB)
    replays = replay_all(scorer, runs)
    results = {k: v["result"] for k, v in replays.items()}
    prot = protected_status(results, manifest)
    prot_section, counts = _protected_section(prot)
    _exact_n, fid_sections = _fidelity_section(runs, replays, "Drift runs")
    header = [("#", "Replay report — baseline fidelity"),
              ("baseline", "blob: " + BASELINE_SCORE_BLOB),
              ("scorer sha256", scorer._replay_sha256)] + _manifest_header(mpath, manifest)
    write_report(out_path, header, [prot_section] + fid_sections[:2]
                 + [_coverage_section(runs, replays)] + fid_sections[2:])
    _report_unevaluable(prot)
    if len(runs) != EXPECTED_SCOREABLE:
        return 2
    return 1 if counts["UNEVALUABLE"] else 0


def _top_row(result, site):
    rows = _rows_at_site(result, site)
    if not rows:
        return None
    return sorted(rows, key=lambda f: (-_rank(f.get("band")),
                                       -(f.get("orchestrator_score") or 0)))[0]


def _fp_section(heading, paths, base_results, cand_results):
    b = fp_prediction(base_results, paths)
    c = fp_prediction(cand_results, paths)
    body = ["baseline **%d/%d** → candidate **%d/%d**"
            % (b["count"], b["denominator"], c["count"], c["denominator"]), "",
            "| run | baseline fires | candidate fires |", "|---|---|---|"]
    for p in paths:
        body.append("| %s | %s | %s |" % (p, "yes" if p in b["fired"] else "no",
                                          "yes" if p in c["fired"] else "no"))
    return {"heading": heading, "body": body}, c["fired"]


def _cmd_candidate(name, spec, override_pairs, out_path, manifest_path=None):
    overrides = _parse_overrides(override_pairs)
    runs = iter_runs()
    manifest, mpath = _load_checked_manifest(runs, manifest_path)
    if manifest is None:
        return 1
    base = load_scorer("blob:" + BASELINE_SCORE_BLOB)
    cand = load_scorer(spec, overrides)
    base_replays = replay_all(base, runs)
    cand_replays = replay_all(cand, runs)
    base_results = {k: v["result"] for k, v in base_replays.items()}
    cand_results = {k: v["result"] for k, v in cand_replays.items()}

    prot = protected_status(base_results, manifest)
    prot_section, _pcounts = _protected_section(prot)
    guard = guardrail(base_results, cand_results, manifest)
    gcounts = {k: sum(1 for v in guard.values() if v["status"] == k)
               for k in ("kept", "REGRESSED", "UNEVALUABLE", "AMENDED")}
    g_body = ["| run | baseline basis | candidate band/score/basis | status |",
              "|---|---|---|---|"]
    for run_path in sorted(guard):
        g = guard[run_path]
        top = _top_row(cand_results.get(run_path), manifest["catch_runs"][run_path]["site"])
        band_score = ("%s/%s" % (top.get("band"), top.get("orchestrator_score"))
                      if top else "—")
        g_body.append("| %s | %s | %s/%s | %s |" % (run_path, g["base"], band_score,
                                                     g["cand"], g["status"]))
    g_body += ["", "kept %d / protected %d" % (gcounts["kept"], EXPECTED_PROTECTED),
               "", "REGRESSED %d" % gcounts["REGRESSED"],
               "", "UNEVALUABLE %d" % gcounts["UNEVALUABLE"],
               "", "AMENDED %d" % gcounts["AMENDED"]]

    quiet = manifest.get("quiet_runs") or {}
    excluded = (manifest.get("excluded_runs") or {}).get("should-quiet-7") or []
    fp_specs = [
        ("FP prediction — headline quiet set (Phase-38 should-quiet-1..6 ×3)",
         quiet.get("headline") or []),
        ("Phase-40 should-quiet-5 (6 runs)", quiet.get("phase40") or []),
        ("Informational — v2.9 quiet (9 runs)", quiet.get("v29_informational") or []),
        ("Informational — should-quiet-7 (3 runs, UNLABELED per ledger 001; not gated, "
         "not calibrated)", excluded),
    ]
    fp_sections, fired_tables = [], []
    for heading, paths in fp_specs:
        sec, fired = _fp_section(heading, paths, base_results, cand_results)
        fp_sections.append(sec)
        for p in fired:
            rows = [f for f in cand_results[p].get("findings") or []
                    if isinstance(f, dict) and f.get("band") in ("critical", "warning")]
            fired_tables.append(("### " + p, rows))
    rows_section = {"heading": "Rows that fire under the candidate",
                    "body": [] if fired_tables else ["- none"], "tables": fired_tables}
    _exact_n, fid_sections = _fidelity_section(
        runs, base_replays,
        "Baseline fidelity drift (disclosed — score/band drift is why comparison is "
        "baseline-relative; it never removes a run from the protected 26)")

    header = [("#", "Replay report — candidate " + name),
              ("candidate scorer", cand._replay_spec),
              ("candidate scorer sha256", cand._replay_sha256),
              ("overrides", json.dumps(overrides, sort_keys=True)),
              ("baseline", "blob: " + BASELINE_SCORE_BLOB)] + _manifest_header(mpath, manifest)
    sections = ([prot_section, {"heading": "Guardrail — %d protected catch runs"
                                % EXPECTED_PROTECTED, "body": g_body}]
                + fp_sections + [rows_section] + fid_sections[:2])
    write_report(out_path, header, sections)
    _report_unevaluable(prot)
    return 1 if (gcounts["REGRESSED"] or gcounts["UNEVALUABLE"]) else 0


def _parse_overrides(pairs):
    out = {}
    for pair in pairs or []:
        name, sep, raw = pair.partition("=")
        if not sep or not name:
            raise ReplayError("override must be NAME=JSON")
        try:
            out[name] = json.loads(raw)
        except ValueError:
            raise ReplayError("override value is not valid JSON: " + name)
    return out


def run(argv):
    parser = argparse.ArgumentParser(
        prog="replay.py", description="Offline scorer replay (see module docstring).")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("census")
    p_cm = sub.add_parser("check-manifest")
    p_cm.add_argument("--manifest", default=None)
    p_de = sub.add_parser("dump-envelope")
    p_de.add_argument("rel_path")
    p_b = sub.add_parser("baseline")
    p_b.add_argument("--out", required=True)
    p_b.add_argument("--manifest", default=None)
    p_c = sub.add_parser("candidate")
    p_c.add_argument("--name", required=True)
    p_c.add_argument("--scorer", required=True)
    p_c.add_argument("--override", action="append", default=[])
    p_c.add_argument("--out", required=True)
    p_c.add_argument("--manifest", default=None)
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2  # usage error -> fail closed, never exit 0
    if not args.cmd:
        parser.print_usage(sys.stderr)
        return 2
    try:
        if args.cmd == "census":
            return _cmd_census()
        if args.cmd == "dump-envelope":
            return _cmd_dump_envelope(args.rel_path)
        if args.cmd == "baseline":
            return _cmd_baseline(args.out, args.manifest)
        if args.cmd == "check-manifest":
            return _cmd_check_manifest(args.manifest)
        if args.cmd == "candidate":
            return _cmd_candidate(args.name, args.scorer, args.override, args.out,
                                  args.manifest)
    except ReplayError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    except (OSError, ValueError) as exc:
        sys.stderr.write("unreadable input: %s\n" % type(exc).__name__)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
