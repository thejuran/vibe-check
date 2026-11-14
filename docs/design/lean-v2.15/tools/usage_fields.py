"""usage_fields.py — read-only usage-field reader for recorded Claude Code sessions.

Answers one question from records that already exist: which usage fields are
present in a session log, and can they be tied to a review run and to a
reviewer lane? It reads a fixed list of session files and prints field names,
presence counts and token sums. It starts nothing, writes nothing and copies
no log anywhere.

What leaves the logs:
  * field names (the key names inside `usage` objects, and key names holding
    `retry`), each checked against a safe pattern;
  * counts (records, unique messages, duplicates, malformed lines, files) and
    token sums;
  * model names and lane names (a subagent meta file's `agentType`) that
    match a safe pattern; anything else is reported as `other`;
  * labels the reader chose (session labels given on the command line).

What never leaves the logs: message text, tool inputs and results, paths,
working directories, message ids, account details, or any other string value.
Sessions are reported by the label given on the command line, never by path.

Counting rules:
  * Claude Code logs one record per content block of an API message, each
    carrying the same `usage`. Usage is summed once per message id (`message.id`,
    falling back to `requestId`). When the duplicates of one id disagree, the
    last record wins and the id is counted in `duplicate_usage_conflicts`.
  * A subagent file `<session>/subagents/<stem>.jsonl` belongs to the lane named
    by `<stem>.meta.json`'s `agentType`. With no readable meta file it is counted
    under `lanes_unattributed`; it is never guessed into a lane.
  * The run row is the session plus every subagent file. It is the sum of the
    same per-message figures, so it is labelled `sum of parts`. An independent
    run total is reported only if a record carries one explicitly
    (`run_total_source`); otherwise that field reads `none found`.
  * Elapsed time is last minus first record timestamp. It includes the time the
    owner spent answering prompts, so it is not a performance measure.

Nothing is priced. The reader checks its own output for a dollar sign or any
key or table heading naming cost, price or usd, and stops instead of printing.

Usage:
  python3 -I docs/design/lean-v2.15/tools/usage_fields.py \
      --session <label>=<kind>=<path> [--session ...] \
      [--archive-root <dir> ...] [--json]
  python3 -I docs/design/lean-v2.15/tools/usage_fields.py check-note <path>

`check-note` checks a written note for a price (as above), a home-directory or
session-log path, and a full 36-character session id.

Exit codes: 0 ok; 1 the output or note holds a price or private detail;
2 unusable input (bad argument, missing or unreadable file).
"""

import argparse
import json
import os
import re
import sys

TOKEN_FIELDS = ("input_tokens", "output_tokens",
                "cache_creation_input_tokens", "cache_read_input_tokens")
PRESENCE_FIELDS = ("model",) + TOKEN_FIELDS
RUN_TOTAL_KEYS = ("totalTokens", "total_tokens", "totalUsage", "total_usage")
WALL_CLOCK_LABEL = "includes the owner's waiting time — not a performance measure"

SAFE_LANE = re.compile(r"^[A-Za-z0-9:_.-]{1,64}$")
SAFE_LABEL = re.compile(r"^[A-Za-z0-9:_./-]{1,64}$")
SAFE_MODEL = re.compile(r"^[A-Za-z0-9:_.<>\[\]-]{1,64}$")
SAFE_KEY = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
PRICE_WORD = re.compile(r"cost|price|usd", re.IGNORECASE)
JSON_KEY = re.compile(r'"((?:[^"\\]|\\.)*)"\s*:')
TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
SESSION_ID = re.compile(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}")
TIMESTAMP = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?"
                       r"(Z|[+-]\d{2}:?\d{2})?$")
MAX_DEPTH = 64


def _safe(value, pattern):
    """`value` when it is a string matching `pattern`, else `other`."""
    if isinstance(value, str) and pattern.match(value):
        return value
    return "other"


def _days_from_civil(y, m, d):
    y -= 1 if m <= 2 else 0
    era = (y if y >= 0 else y - 399) // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def _epoch_seconds(ts):
    """Seconds since the epoch for an ISO-8601 timestamp, or None."""
    if not isinstance(ts, str):
        return None
    m = TIMESTAMP.match(ts.strip())
    if not m:
        return None
    y, mo, d, hh, mm, ss = (int(m.group(i)) for i in range(1, 7))
    frac = float(m.group(7)) if m.group(7) else 0.0
    secs = _days_from_civil(y, mo, d) * 86400 + hh * 3600 + mm * 60 + ss + frac
    tz = m.group(8)
    if tz and tz != "Z":
        digits = tz[1:].replace(":", "")
        offset = int(digits[:2]) * 3600 + int(digits[2:]) * 60
        secs -= offset if tz[0] == "+" else -offset
    return secs


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _walk_keys(obj, depth=0):
    """Every dict key name anywhere under `obj` (names only, never values)."""
    if depth > MAX_DEPTH:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk_keys(v, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_keys(v, depth + 1)


class _FileStats:
    """What one or more JSONL files hold, reduced to names, numbers and safe labels."""

    def __init__(self):
        self.files = 0
        self.records = 0
        self.malformed = 0
        self.entries = []          # (message id or None, model or None, numeric usage)
        self.first = None
        self.last = None
        self.usage_keys = set()
        self.price_keys = set()
        self.other_keys = 0
        self.retry_keys = set()
        self.run_totals = {}

    def read(self, path):
        self.files += 1
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    self.malformed += 1
                    continue
                if not isinstance(rec, dict):
                    self.malformed += 1
                    continue
                self._record(rec)

    def _record(self, rec):
        self.records += 1
        t = _epoch_seconds(rec.get("timestamp"))
        if t is not None:
            self.first = t if self.first is None else min(self.first, t)
            self.last = t if self.last is None else max(self.last, t)
        for name in _walk_keys(rec):
            if isinstance(name, str) and "retry" in name.lower():
                if SAFE_KEY.match(name):
                    self.retry_keys.add(name)
                else:
                    self.other_keys += 1
        for holder in (rec, rec.get("toolUseResult")):
            if isinstance(holder, dict):
                for key in RUN_TOTAL_KEYS:
                    if key in holder and (_is_number(holder[key]) or isinstance(holder[key], dict)):
                        self.run_totals[key] = self.run_totals.get(key, 0) + 1
        msg = rec.get("message")
        if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
            return
        usage = msg["usage"]
        nums = {}
        for k, v in usage.items():
            if not isinstance(k, str) or not SAFE_KEY.match(k):
                self.other_keys += 1
                continue
            if PRICE_WORD.search(k):
                self.price_keys.add(k)
                continue
            self.usage_keys.add(k)
            if _is_number(v):
                nums[k] = v
        mid = msg.get("id")
        if not isinstance(mid, str) or not mid:
            mid = rec.get("requestId")
        if not isinstance(mid, str) or not mid:
            mid = None
        model = msg.get("model") if isinstance(msg.get("model"), str) else None
        self.entries.append((mid, model, nums))


def _unique_by_message(entries):
    """(entries kept once per message id, count of ids whose duplicates disagree).

    The last record of an id wins; entries without an id are each kept."""
    order, latest, first_nums, conflicts = [], {}, {}, set()
    anonymous = []
    for entry in entries:
        mid = entry[0]
        if mid is None:
            anonymous.append(entry)
            continue
        if mid not in latest:
            order.append(mid)
            first_nums[mid] = entry[2]
        elif entry[2] != first_nums[mid]:
            conflicts.add(mid)
        latest[mid] = entry
    return [latest[m] for m in order] + anonymous, len(conflicts)


def _summarise_files(paths):
    st = _FileStats()
    for p in paths:
        st.read(p)
    unique, conflicts = _unique_by_message(st.entries)
    tokens = {f: 0 for f in TOKEN_FIELDS}
    fields = {f: {"present": 0, "of": len(unique)} for f in PRESENCE_FIELDS}
    models = set()
    for _mid, model, nums in unique:
        if model is not None:
            fields["model"]["present"] += 1
            models.add(_safe(model, SAFE_MODEL))
        for f in TOKEN_FIELDS:
            if f in nums:
                fields[f]["present"] += 1
                tokens[f] += nums[f]
    if st.run_totals:
        run_total = ", ".join("%s in %d record%s" % (k, n, "" if n == 1 else "s")
                              for k, n in sorted(st.run_totals.items()))
    else:
        run_total = "none found"
    wall = None if st.first is None else round(st.last - st.first, 3)
    return {
        "files": st.files,
        "records": st.records,
        "unique_messages": len(unique),
        "duplicates_dropped": len(st.entries) - len(unique),
        "duplicate_usage_conflicts": conflicts,
        "tokens": tokens,
        "fields": fields,
        "models": sorted(models),
        "usage_key_names": sorted(st.usage_keys),
        "charge_like_keys_withheld": len(st.price_keys),
        "other_keys_withheld": st.other_keys,
        "retry_key_names": sorted(st.retry_keys),
        "wall_clock_seconds": wall,
        "wall_clock_label": WALL_CLOCK_LABEL,
        "malformed_lines": st.malformed,
        "run_total_source": run_total,
    }


def _read_meta(path):
    """The meta file's `agentType`, or None when absent or unreadable."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            meta = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(meta, dict):
        return None
    agent = meta.get("agentType")
    return agent if isinstance(agent, str) and agent else None


def summarise_session(path):
    """Usage summary for one session file plus its `<stem>/subagents` folder.

    Top-level fields describe the main session file alone. `lanes` maps each
    lane name to the same summary over its subagent files; `lanes_unattributed`
    covers subagent files with no readable meta file; `run` covers every file.
    Raises OSError when the session file cannot be read."""
    out = _summarise_files([path])
    sub_dir = os.path.join(os.path.splitext(path)[0], "subagents")
    by_lane, unattributed = {}, []
    if os.path.isdir(sub_dir):
        for name in sorted(os.listdir(sub_dir)):
            if not name.endswith(".jsonl"):
                continue
            side = os.path.join(sub_dir, name)
            agent = _read_meta(os.path.join(sub_dir, name[:-len(".jsonl")] + ".meta.json"))
            if agent is None:
                unattributed.append(side)
            else:
                by_lane.setdefault(_safe(agent, SAFE_LANE), []).append(side)
    out["lanes"] = {lane: _summarise_files(paths) for lane, paths in sorted(by_lane.items())}
    out["lanes_unattributed"] = _summarise_files(unattributed)
    every = [path] + [p for ps in by_lane.values() for p in ps] + unattributed
    run = _summarise_files(every)
    parts = [out] + list(out["lanes"].values()) + [out["lanes_unattributed"]]
    run["source"] = "sum of parts"
    run["cross_file_duplicate_ids"] = sum(p["unique_messages"] for p in parts) - run["unique_messages"]
    out["run"] = run
    return out


def census_archives(root):
    """Counts of `transcript.jsonl` files under `root`: how many, how many carry
    any `usage` object, how many have a `subagents` folder beside them.
    Lines that are not valid JSON are skipped for the usage test."""
    counts = {"files": 0, "with_usage": 0, "with_subagents": 0}
    for dirpath, _dirs, names in os.walk(root):
        if "transcript.jsonl" not in names:
            continue
        counts["files"] += 1
        if os.path.isdir(os.path.join(dirpath, "subagents")):
            counts["with_subagents"] += 1
        if _has_usage(os.path.join(dirpath, "transcript.jsonl")):
            counts["with_usage"] += 1
    return counts


def _has_usage(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"usage"' not in line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if _holds_usage(rec, 0):
                return True
    return False


def _holds_usage(obj, depth):
    if depth > MAX_DEPTH:
        return False
    if isinstance(obj, dict):
        if isinstance(obj.get("usage"), dict):
            return True
        return any(_holds_usage(v, depth + 1) for v in obj.values())
    if isinstance(obj, list):
        return any(_holds_usage(v, depth + 1) for v in obj)
    return False


def _row(cells):
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _scopes(summary):
    yield "main", summary
    for lane, s in summary["lanes"].items():
        yield "lane " + lane, s
    if summary["lanes_unattributed"]["files"]:
        yield "unattributed", summary["lanes_unattributed"]
    yield "run (sum of parts)", summary["run"]


def render(sessions, archives):
    """Plain-text tables of what `main` gathered. Names and numbers only."""
    lines = ["# Usage fields (token counts, deduplicated by message id)", ""]
    head = ["session", "kind", "scope", "files", "records", "messages", "duplicates dropped",
            "conflicting duplicates", "malformed lines"] + list(TOKEN_FIELDS) + ["wall clock s"]
    lines += [_row(head), _row(["---"] * len(head))]
    for s in sessions:
        for scope, part in _scopes(s["summary"]):
            wall = "-" if part["wall_clock_seconds"] is None else part["wall_clock_seconds"]
            lines.append(_row([s["label"], s["kind"], scope, part["files"], part["records"],
                               part["unique_messages"], part["duplicates_dropped"],
                               part["duplicate_usage_conflicts"], part["malformed_lines"]]
                              + [part["tokens"][f] for f in TOKEN_FIELDS] + [wall]))
    lines += ["", "## Field presence (messages carrying the field / messages)", ""]
    head = ["session", "scope"] + list(PRESENCE_FIELDS) + ["models seen"]
    lines += [_row(head), _row(["---"] * len(head))]
    for s in sessions:
        for scope, part in _scopes(s["summary"]):
            cells = ["%d/%d" % (part["fields"][f]["present"], part["fields"][f]["of"])
                     for f in PRESENCE_FIELDS]
            lines.append(_row([s["label"], scope] + cells
                              + [", ".join(part["models"]) or "-"]))
    lines += ["", "## Per session", ""]
    for s in sessions:
        m = s["summary"]
        run = m["run"]
        lines.append("- %s: usage key names: %s; charge-like key names withheld (cost, price or usd): %d; "
                     "other key names withheld: %d; retry key names: %s; run total source: %s; "
                     "cross-file duplicate ids: %d" % (
                         s["label"], ", ".join(run["usage_key_names"]) or "none",
                         run["charge_like_keys_withheld"], run["other_keys_withheld"],
                         ", ".join(run["retry_key_names"]) or "none",
                         run["run_total_source"], run["cross_file_duplicate_ids"]))
    lines.append("")
    lines.append("Wall clock: " + WALL_CLOCK_LABEL + ".")
    if archives:
        lines += ["", "## Archives", ""]
        head = ["archive root", "transcript files", "with usage", "with subagents folder"]
        lines += [_row(head), _row(["---"] * len(head))]
        for a in archives:
            lines.append(_row([a["root"], a["files"], a["with_usage"], a["with_subagents"]]))
    return "\n".join(lines) + "\n"


def price_problems(text):
    """Problems naming each line that holds a dollar sign, a JSON key naming
    cost, price or usd, or a table heading cell naming one. Prose and section
    titles are not checked for those words."""
    problems = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if "$" in line:
            problems.append("line %d: dollar sign" % i)
        if any(PRICE_WORD.search(k) for k in JSON_KEY.findall(line)):
            problems.append("line %d: a JSON key names cost, price or usd" % i)
        if ("|" in line and i < len(lines) and TABLE_SEPARATOR.match(lines[i])
                and not TABLE_SEPARATOR.match(line)):
            if any(PRICE_WORD.search(c) for c in line.split("|")):
                problems.append("line %d: a table heading names cost, price or usd" % i)
    return problems


def note_problems(text):
    """Price problems plus home-directory paths, session-log paths and full
    36-character session ids, each named by line number."""
    problems = price_problems(text)
    for i, line in enumerate(text.splitlines(), 1):
        if "/Users/" in line:
            problems.append("line %d: home-directory path" % i)
        if ".claude/projects" in line:
            problems.append("line %d: session-log path" % i)
        if SESSION_ID.search(line):
            problems.append("line %d: full session id (use the 8-character prefix)" % i)
    return problems


def _check_note(argv):
    if len(argv) != 1:
        print("usage: usage_fields.py check-note <path>", file=sys.stderr)
        return 2
    try:
        with open(argv[0], encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        print("NOTE NOT FOUND OR UNREADABLE — STOPPING", file=sys.stderr)
        return 2
    problems = note_problems(text)
    for p in problems:
        print(p)
    if problems:
        print("NOTE HOLDS A PRICE OR PRIVATE DETAIL — STOPPING", file=sys.stderr)
        return 1
    print("note clean")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "check-note":
        return _check_note(argv[1:])
    parser = argparse.ArgumentParser(prog="usage_fields.py",
                                     description="Read-only usage-field reader.")
    parser.add_argument("--session", action="append", default=[],
                        help="label=kind=path of a session JSONL file (repeatable)")
    parser.add_argument("--archive-root", action="append", default=[],
                        help="directory to census for transcript.jsonl files (repeatable)")
    parser.add_argument("--json", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2
    if not args.session and not args.archive_root:
        parser.print_usage(sys.stderr)
        return 2
    sessions = []
    for spec in args.session:
        parts = spec.split("=", 2)
        if (len(parts) != 3 or not SAFE_LABEL.match(parts[0])
                or not SAFE_LANE.match(parts[1]) or not parts[2]):
            print("BAD --session (want label=kind=path with a plain label and kind) — STOPPING",
                  file=sys.stderr)
            return 2
        label, kind, path = parts
        if not os.path.isfile(path):
            print("SESSION NOT FOUND: %s — STOPPING" % label, file=sys.stderr)
            return 2
        try:
            summary = summarise_session(path)
        except OSError:
            print("SESSION UNREADABLE: %s — STOPPING" % label, file=sys.stderr)
            return 2
        sessions.append({"label": label, "kind": kind, "summary": summary})
    archives = []
    for root in args.archive_root:
        name = _safe(os.path.basename(os.path.normpath(root)), SAFE_LABEL)
        if not os.path.isdir(root):
            print("ARCHIVE ROOT NOT FOUND: %s — STOPPING" % name, file=sys.stderr)
            return 2
        try:
            counts = census_archives(root)
        except OSError:
            print("ARCHIVE UNREADABLE: %s — STOPPING" % name, file=sys.stderr)
            return 2
        archives.append(dict(root=name, **counts))
    if args.json:
        text = json.dumps({"sessions": sessions, "archives": archives},
                          indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    else:
        text = render(sessions, archives)
    if price_problems(text):
        print("OUTPUT HOLDS A PRICE — STOPPING", file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
