"""lanearchive.py — per-run raw-lane and Codex archive extractor for a measured run.

A measured deep-review run archives its scored `state.json`, but the scorer's
input — every dispatched agent's raw return and the Codex payload — lives only
in the local session transcript and in a private temp directory that do not
survive the session. This module copies that evidence into the run directory so
a confound audit (which lane said what, did Codex really join) can be run later
from committed files alone.

Evidence rules:

* Transcripts are parsed as data, never imported or executed. Only these
  channels are read, so template examples and Write payloads are never mistaken
  for an agent return:
    A. a dispatch is an `Agent`/`Task` tool_use in a main-session assistant
       record; its return is matched by tool_use_id, from
         - the dispatch's own tool_result (a synchronous return; the async
           "agent launched" acknowledgement is not a return),
         - a `<task-notification>` naming the dispatch's `<tool-use-id>` and
           carrying a `<result>` body, in the plain-text content of a `user`
           record or a `queue-operation` record (never inside a tool_result),
         - a sidechain `SubagentHandback` tool_use, mapped to its dispatch
           through the agent id the launch acknowledgement or a notification
           names;
    B. a `Bash` tool_result holding, at the start of a line, a JSON object
       whose top-level agent is codex-adversarial (the Codex translator line).
* The Codex collection directory is the one a `Bash` tool_result printed on a
  `CODEX_DIR=` line (legacy `CODEX_OUT=<file>` gives its directory). It is
  followed only when it resolves strictly inside the user's temp root.
* The archive disposition is cross-checked against the run's own state: a run
  whose `passes[-1].codex.status` is `joined` MUST yield the Codex payload and a
  zero `rc`; `codex-absent.txt` is written only for `skipped` / `off`. Anything
  else is an extraction failure: nothing is left behind and the exit is 1.

Output rule: archive files carry lane returns and the Codex payload verbatim —
messages name pattern classes and fixed reasons only, never matched text or
transcript content. Every written file passes `privacy_scan`; on any hit the
files this run wrote are deleted and the exit is 1.

Imports exactly {argparse, json, os, re, shutil, sys, tempfile} plus the
sibling `replay`; it never spawns a child process.

    python3 lanearchive.py extract --transcript <jsonl> --state <state.json> --out-dir <dir>
    python3 lanearchive.py scan <file> [<file> ...]

Exit 0 clean / 1 refused (privacy hit, extraction failure, output already
present) / 2 usage error or unreadable input.
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import replay  # noqa: E402  (sibling module: shared transcript channel parsers)

DISPATCH_TOOLS = ("Agent", "Task")
# Tools whose tool_result can carry the Codex translator line or the CODEX_DIR
# line. A Read of a template that shows either is not a Bash result.
CODEX_LINE_TOOLS = ("Bash",)
_ASYNC_LAUNCH_MARKER = "Async agent launched"

_NOTIFICATION_RE = re.compile(r"<task-notification>(.*?)</task-notification>", re.DOTALL)
_NOTIF_TOOL_USE_RE = re.compile(r"<tool-use-id>([^<\s]+)</tool-use-id>")
_NOTIF_TASK_ID_RE = re.compile(r"<task-id>([^<\s]+)</task-id>")
_AGENT_ID_RE = re.compile(r"^agentId: ([A-Za-z0-9_-]+)", re.MULTILINE)
_CODEX_DIR_RE = re.compile(r"^CODEX_DIR=(/\S+)[ \t]*$", re.MULTILINE)
_CODEX_OUT_RE = re.compile(r"^CODEX_OUT=(/\S+)[ \t]*$", re.MULTILINE)

OUT_LANES = "lanes.json"
OUT_CONTEXT = "context.txt"
OUT_PAYLOAD = "codex-payload.json"
OUT_RC = "codex-rc.txt"
OUT_ABSENT = "codex-absent.txt"
OUT_NAMES = (OUT_LANES, OUT_CONTEXT, OUT_PAYLOAD, OUT_RC, OUT_ABSENT)

_USAGE_KEYS = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_EMAIL_ALLOWED = ("noreply@anthropic.com",)
PRIVACY_CLASSES = (
    ("nas-host", (re.compile(r"maguffynas"), re.compile(r"ssh nas"),
                  re.compile(r"sudoers"))),
    ("token", (re.compile(r"sk-ant-"), re.compile(r"\bsk-[A-Za-z0-9]{10,}"),
               re.compile(r"ghp_"), re.compile(r"github_pat_"),
               re.compile(r"AKIA[0-9A-Z]{12,}"),
               re.compile(r"Bearer [A-Za-z0-9._-]{16,}"))),
    ("private-instructions", (re.compile(r"NOPASSWD"), re.compile(r"claude-docker"),
                              re.compile(r"Division of Labor"))),
)


class ExtractionError(Exception):
    """A run whose archive cannot be completed honestly (exit 1)."""


# --------------------------------------------------------------------------- #
# Transcript walk
# --------------------------------------------------------------------------- #

def _records(transcript_path):
    """(records, malformed): every JSON-object line of the transcript."""
    out, malformed = [], 0
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
            out.append(rec)
    return out, malformed


def _content(rec):
    msg = rec.get("message")
    return msg.get("content") if isinstance(msg, dict) else None


def _is_main(rec):
    return not rec.get("isSidechain")


def _tool_uses(rec):
    content = _content(rec)
    for c in content if isinstance(content, list) else []:
        if isinstance(c, dict) and c.get("type") == "tool_use" and isinstance(c.get("id"), str):
            yield c


def _tool_results(rec):
    """(tool_use_id, [texts]) per tool_result block of a user record."""
    content = _content(rec)
    for c in content if isinstance(content, list) else []:
        if isinstance(c, dict) and c.get("type") == "tool_result":
            yield c.get("tool_use_id"), list(replay._tool_result_texts([c]))


def _notification_strings(rec):
    """Plain-text carriers of task notifications: a `user` record's string content
    or its text blocks, or a `queue-operation` record's content. Tool results are
    excluded — a Read of a template that shows a notification is not one."""
    kind = rec.get("type")
    if kind == "queue-operation":
        c = rec.get("content")
        return [c] if isinstance(c, str) else []
    if kind != "user":
        return []
    content = _content(rec)
    if isinstance(content, str):
        return [content]
    out = []
    for c in content if isinstance(content, list) else []:
        if isinstance(c, dict) and c.get("type") == "text" and isinstance(c.get("text"), str):
            out.append(c["text"])
    return out


def _line_object_spans(text):
    """(object, verbatim text) for every JSON object starting a line of `text`."""
    decoder = json.JSONDecoder()
    offset = 0
    for line in text.splitlines(True):
        if line.startswith("{"):
            try:
                obj, end = decoder.raw_decode(text, offset)
            except ValueError:
                obj, end = None, offset
            if isinstance(obj, dict):
                yield obj, text[offset:end]
        offset += len(line)


def _walk(records):
    """Index the main session: dispatches, tool names, agent ids, returns."""
    dispatches = {}   # tool_use_id -> subagent_type, in dispatch order
    tool_names = {}   # tool_use_id -> tool name (main session)
    agent_to_tool = {}
    for rec in records:
        if rec.get("type") != "assistant" or not _is_main(rec):
            continue
        for c in _tool_uses(rec):
            tool_names[c["id"]] = c.get("name")
            if c.get("name") in DISPATCH_TOOLS:
                inp = c.get("input") if isinstance(c.get("input"), dict) else {}
                dispatches.setdefault(c["id"], inp.get("subagent_type"))
    returns = {}      # tool_use_id -> [(channel, text)]
    codex = []        # (tool_use_id, verbatim, parsed)
    for rec in records:
        if not _is_main(rec):
            continue
        for s in _notification_strings(rec):
            for body in _NOTIFICATION_RE.findall(s):
                tid = _NOTIF_TOOL_USE_RE.search(body)
                if not tid or tid.group(1) not in dispatches:
                    continue
                aid = _NOTIF_TASK_ID_RE.search(body)
                if aid:
                    agent_to_tool.setdefault(aid.group(1), tid.group(1))
                for result in replay._RESULT_RE.findall(body):
                    returns.setdefault(tid.group(1), []).append(("task-result", result))
        if rec.get("type") != "user":
            continue
        for tool_id, texts in _tool_results(rec):
            if tool_id in dispatches:
                text = "\n".join(texts)
                if _ASYNC_LAUNCH_MARKER in text:
                    for aid in _AGENT_ID_RE.findall(text):
                        agent_to_tool.setdefault(aid, tool_id)
                elif text:
                    returns.setdefault(tool_id, []).append(("task-result", text))
            elif tool_names.get(tool_id) in CODEX_LINE_TOOLS:
                for text in texts:
                    for obj, raw in _line_object_spans(text):
                        if obj.get("agent") == replay.CODEX_AGENT:
                            codex.append((tool_id, raw, obj))
    for rec in records:
        if rec.get("type") != "assistant" or _is_main(rec):
            continue
        tool_id = agent_to_tool.get(rec.get("agentId"))
        if tool_id is None:
            continue
        for c in _tool_uses(rec):
            if c.get("name") != replay._HANDBACK_TOOL:
                continue
            inp = c.get("input") if isinstance(c.get("input"), dict) else {}
            message = inp.get("message")
            if isinstance(message, dict):
                message = json.dumps(message, sort_keys=True)
            if isinstance(message, str):
                returns.setdefault(tool_id, []).append(("handback", message))
    return dispatches, tool_names, returns, codex


def extract_lanes(transcript_path):
    """Every dispatched lane's verbatim return, plus the Codex translator line.

    One lane per dispatch that returned: the last handback when one exists,
    else the last task result (`returns_seen` counts the distinct returns). The
    Codex translator object is its own `codex-adversarial` lane.
    """
    records, malformed = _records(transcript_path)
    dispatches, _names, returns, codex = _walk(records)
    lanes, unrecovered = [], []
    for tool_id, subagent_type in dispatches.items():
        distinct = []
        for item in returns.get(tool_id, []):
            if item not in distinct:
                distinct.append(item)
        if not distinct:
            unrecovered.append({"tool_use_id": tool_id, "subagent_type": subagent_type})
            continue
        handbacks = [i for i in distinct if i[0] == "handback"]
        channel, text = (handbacks or distinct)[-1]
        lanes.append({"tool_use_id": tool_id, "subagent_type": subagent_type,
                      "source_channel": channel, "raw_return_text": text,
                      "parsed": replay._decode_object(text),
                      "returns_seen": len(distinct)})
    seen = set()
    codex_lines = 0
    for tool_id, raw, obj in codex:
        if raw in seen:
            continue
        seen.add(raw)
        codex_lines += 1
        lanes.append({"tool_use_id": tool_id, "subagent_type": replay.CODEX_AGENT,
                      "source_channel": "codex-line", "raw_return_text": raw,
                      "parsed": obj, "returns_seen": 1})
    return {"dispatched": len(dispatches), "recovered": len(dispatches) - len(unrecovered),
            "unrecovered": unrecovered, "codex_lines": codex_lines,
            "malformed": malformed, "lanes": lanes}


def _temp_roots():
    roots = []
    for r in (tempfile.gettempdir(), "/private/var/folders", "/var/folders"):
        real = os.path.realpath(r)
        if real not in roots:
            roots.append(real)
    return roots


def _inside_temp_root(path):
    real = os.path.realpath(path)
    return any(real.startswith(root.rstrip(os.sep) + os.sep) for root in _temp_roots())


def locate_codex_dir(transcript_path):
    """The Codex collection directory a Bash tool_result printed, else None.

    Raises ValueError when the printed path is outside the temp root or when
    two different directories were printed.
    """
    records, _malformed = _records(transcript_path)
    _d, tool_names, _r, _c = _walk(records)
    found = []
    for rec in records:
        if rec.get("type") != "user" or not _is_main(rec):
            continue
        for tool_id, texts in _tool_results(rec):
            if tool_names.get(tool_id) not in CODEX_LINE_TOOLS:
                continue
            for text in texts:
                paths = list(_CODEX_DIR_RE.findall(text))
                paths += [os.path.dirname(p) for p in _CODEX_OUT_RE.findall(text)]
                for p in paths:
                    if not _inside_temp_root(p):
                        raise ValueError("codex directory outside the temp root")
                    real = os.path.realpath(p)
                    if real not in found:
                        found.append(real)
    if len(found) > 1:
        raise ValueError("more than one codex directory printed")
    return found[0] if found else None


def peak_context(transcript_path):
    """Max over main-session assistant usage of input + cache-read + cache-creation."""
    records, _malformed = _records(transcript_path)
    peak = 0
    for rec in records:
        if rec.get("type") != "assistant" or not _is_main(rec):
            continue
        msg = rec.get("message")
        usage = msg.get("usage") if isinstance(msg, dict) else None
        if not isinstance(usage, dict):
            continue
        total = 0
        for k in _USAGE_KEYS:
            v = usage.get(k)
            if isinstance(v, int) and not isinstance(v, bool):
                total += v
        peak = max(peak, total)
    return peak


def privacy_scan(text):
    """Pattern-class names hit in `text` (fixed order), [] when clean."""
    hits = []
    if any(m not in _EMAIL_ALLOWED for m in _EMAIL_RE.findall(text)):
        hits.append("email")
    for name, patterns in PRIVACY_CLASSES:
        if any(p.search(text) for p in patterns):
            hits.append(name)
    return hits


# --------------------------------------------------------------------------- #
# Archive
# --------------------------------------------------------------------------- #

def _state_codex(state_path):
    with open(state_path, encoding="utf-8") as fh:
        state = json.load(fh)
    passes = state.get("passes") if isinstance(state, dict) else None
    if not isinstance(passes, list) or not passes or not isinstance(passes[-1], dict):
        raise ValueError("state has no passes")
    codex = passes[-1].get("codex")
    if not isinstance(codex, dict):
        raise ValueError("state has no codex record")
    return codex.get("status"), codex.get("reason")


def _codex_disposition(transcript_path, state_path):
    """("joined", payload_path, rc_path) or ("absent", line, None)."""
    status, reason = _state_codex(state_path)
    if status in ("skipped", "off"):
        return "absent", "codex.status=%s reason=%s\n" % (
            status, reason if isinstance(reason, str) else "null"), None
    if status != "joined":
        raise ExtractionError("codex extraction failed: unknown codex status in state")
    codex_dir = locate_codex_dir(transcript_path)
    if codex_dir is None:
        raise ExtractionError("codex extraction failed: joined run printed no CODEX_DIR line")
    payload = os.path.join(codex_dir, "payload.json")
    rc = os.path.join(codex_dir, "rc")
    for p in (payload, rc):
        if not os.path.isfile(p) or os.path.realpath(p) != os.path.join(codex_dir, os.path.basename(p)):
            raise ExtractionError("codex extraction failed: joined run has no %s"
                                  % os.path.basename(p))
    with open(rc, encoding="utf-8", errors="replace") as fh:
        if fh.read().strip() != "0":
            raise ExtractionError("codex extraction failed: joined run rc is not 0")
    return "joined", payload, rc


def extract(transcript_path, state_path, out_dir):
    """Write the archive files; returns the written names. Raises ExtractionError
    (nothing left behind) or OSError/ValueError (unreadable)."""
    if not os.path.isdir(out_dir):
        raise ValueError("out-dir is not a directory")
    present = [n for n in OUT_NAMES if os.path.lexists(os.path.join(out_dir, n))]
    if present:
        raise ExtractionError("already written: " + ", ".join(present))
    # Everything is read and decided before the first write, so a failure here
    # leaves the run directory untouched.
    lanes = extract_lanes(transcript_path)
    context = peak_context(transcript_path)
    kind, a, b = _codex_disposition(transcript_path, state_path)
    written = []
    try:
        def _write(name, text):
            path = os.path.join(out_dir, name)
            written.append(path)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)

        _write(OUT_LANES, json.dumps(lanes, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        _write(OUT_CONTEXT, "%d\n" % context)
        if kind == "joined":
            for src, name in ((a, OUT_PAYLOAD), (b, OUT_RC)):
                dst = os.path.join(out_dir, name)
                written.append(dst)
                shutil.copyfile(src, dst)
        else:
            _write(OUT_ABSENT, a)
        hits = []
        for path in written:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for h in privacy_scan(fh.read()):
                    if h not in hits:
                        hits.append(h)
        if hits:
            raise ExtractionError("privacy scan refused: " + ", ".join(hits))
    except BaseException:
        for path in written:
            if os.path.lexists(path):
                os.remove(path)
        raise
    return [os.path.basename(p) for p in written]


def _cmd_scan(paths):
    hits = []
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as fh:
            for h in privacy_scan(fh.read()):
                if h not in hits:
                    hits.append(h)
    if hits:
        sys.stderr.write("privacy scan refused: %s\n" % ", ".join(hits))
        return 1
    print("privacy scan clean: %d file(s)" % len(paths))
    return 0


def run(argv):
    parser = argparse.ArgumentParser(
        prog="lanearchive.py",
        description="Archive a measured run's raw lane returns and Codex payload "
                    "(see module docstring).")
    sub = parser.add_subparsers(dest="cmd")
    p_x = sub.add_parser("extract")
    p_x.add_argument("--transcript", required=True)
    p_x.add_argument("--state", required=True)
    p_x.add_argument("--out-dir", required=True)
    p_s = sub.add_parser("scan")
    p_s.add_argument("files", nargs="+")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2  # --help exits 0; a usage error never does
    if not args.cmd:
        parser.print_usage(sys.stderr)
        return 2
    try:
        if args.cmd == "scan":
            return _cmd_scan(args.files)
        names = extract(args.transcript, args.state, args.out_dir)
        print("archived: " + " ".join(names))
        return 0
    except ExtractionError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    except (OSError, ValueError) as exc:
        sys.stderr.write("unreadable input: %s\n" % type(exc).__name__)
        return 2


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
