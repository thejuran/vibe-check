"""tracecheck.py — did the run actually READ each phase body before running it?

Phase bodies live in sub-files the orchestrator reads only when a phase fires.
The failure this module exists to catch is silent: a spine step whose Read
instruction is ignored, so the phase executes from the model's memory of its
title and the report looks normal. Static checks over the repo cannot see it;
only the run's tool events can.

Evidence rules:

* Coverage is counted ONLY from a `Read` tool_use whose paired tool_result
  exists and is not an error. An announcement line is never evidence of a read,
  a failed Read is not coverage, and a tool_use with no answer (a truncated
  transcript) is not coverage and is reported.
* Every mode path declares an expected phase sequence, so a phase omitted
  entirely is a failure rather than an invisible absence.
* Expectations are DATA keyed by (batch, mode): the sub-file layout changes
  between batches, and a trace is only meaningful against the layout it ran on.
  An unknown pair is a usage error — silently checking nothing is the failure
  this module exists to prevent.
* A plugin file must be read from under the plugin root actually in use. That
  is the end-to-end proof that nested reads resolve against the loaded plugin
  rather than the installed cache or another checkout.

Reasons are fixed strings naming phase labels or file basenames only — never a
full foreign path and never transcript content.

Input is `claude -p --output-format stream-json --verbose` JSONL, or an
interactive session's JSONL with its `subagents/` directory (`--subagents`),
whose `*.meta.json` files link each sidechain to the dispatching tool_use.

    python3 tracecheck.py --trace <file.jsonl> --mode <mode> --batch <N>
        --plugin-root <path> [--expectations <path>] [--subagents <dir>]

Exit 0 clean / 1 violation (reasons on stderr, one per line) / 2 unusable input.
This module analyzes a transcript; it never runs anything.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXPECTATIONS = os.path.join(HERE, "fixtures", "mode-path-expectations.json")

REASONS = (
    "malformed transcript lines: %d",
    "unpaired tool_use with no tool_result: %d",
    "no phase announcements in transcript",
    "phase absent from run: %s",
    "phase announced as skipped on a mode path that must run it: %s",
    "phase ran on a mode path that must skip it: %s",
    "unexpected phase in run: %s",
    "phase order differs from the mode path at: %s",
    "always-read file not read before the first phase: %s",
    "phase executed without a preceding successful read: %s",
    "required file never successfully read: %s",
    "file read on a mode path that must not load it: %s",
    "read from outside the plugin root: %s",
    "required agent never dispatched: %s",
    "dispatched agent has no child events: %s",
)
(R_MALFORMED, R_UNPAIRED, R_NO_ANNOUNCE, R_ABSENT, R_SKIPPED_REQUIRED, R_RAN_SKIP_ONLY,
 R_UNEXPECTED, R_ORDER, R_ALWAYS, R_NO_READ, R_REQUIRED, R_FORBIDDEN, R_PROVENANCE,
 R_NO_DISPATCH, R_NO_CHILDREN) = REASONS

USAGE_REASONS = (
    "usage: tracecheck.py --trace <file> --mode <mode> --batch <N> --plugin-root <path>",
    "trace unreadable",
    "subagents directory unreadable",
    "expectations unreadable",
    "unknown (batch, mode) pair",
    "malformed expectation entry",
)

RUN_MARK, SKIP_MARK = "✓", "⊘"
# A line that STARTS with the mark (after whitespace or list/quote/emphasis
# punctuation). A mid-sentence mention is not an announcement.
ANNOUNCE_RE = re.compile(
    r"^[\s>*_`-]*([✓⊘])\s*(?:\*\*)?\s*Phase\s+([0-9]+(?:\.[0-9]+)?[a-z]?)(?![0-9A-Za-z.])",
    re.MULTILINE)
# A plugin-shaped markdown file. Only paths that also name the plugin are held
# to provenance, so a reviewed repo's own docs are not a provenance question.
PLUGIN_SHAPED_RE = re.compile(r"/(commands|agents|templates|phases/[a-z-]+)/[^/]+\.md$")
DISPATCH_TOOLS = ("Task", "Agent")
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]")


def _safe_basename(path):
    return _SAFE_NAME_RE.sub("?", os.path.basename(path))[:80] or "?"


def _parse_line(line, parent_override, out):
    """Append the events one JSONL line carries; return False when malformed."""
    try:
        rec = json.loads(line)
    except ValueError:
        return False
    if not isinstance(rec, dict):
        return False
    if rec.get("type") not in ("assistant", "user"):
        return True
    msg = rec.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    if not isinstance(content, list):
        return True
    parent = parent_override or rec.get("parent_tool_use_id") or None
    for c in content:
        if not isinstance(c, dict):
            continue
        kind = c.get("type")
        if kind == "tool_use" and rec["type"] == "assistant":
            inp = c.get("input") if isinstance(c.get("input"), dict) else {}
            out.append(("tool_use", c.get("id"), c.get("name"),
                        {"input": inp, "parent": parent}))
        elif kind == "tool_result" and rec["type"] == "user":
            out.append(("tool_result", c.get("tool_use_id"), None,
                        {"is_error": c.get("is_error") is True, "parent": parent}))
        elif kind == "text" and rec["type"] == "assistant" and isinstance(c.get("text"), str):
            out.append(("text", None, None, {"text": c["text"], "parent": parent}))
    return True


def _parse_file(path, parent_override, out):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.strip() and not _parse_line(line, parent_override, out):
                out.append(("malformed", None, None, {"parent": parent_override}))


def events(path, subagent_dir=None):
    """Ordered (kind, id, name, payload) events. Kinds: tool_use, tool_result,
    text, malformed. A malformed line is kept as an event so it is counted.

    With `subagent_dir`, each `<stem>.meta.json` names the dispatching
    `toolUseId`, and `<stem>.jsonl`'s events are appended as its children.
    Raises OSError on an unreadable file (the CLI maps it to exit 2).
    """
    out = []
    _parse_file(path, None, out)
    if subagent_dir is not None:
        for name in sorted(os.listdir(subagent_dir)):
            if not name.endswith(".meta.json"):
                continue
            with open(os.path.join(subagent_dir, name), encoding="utf-8") as fh:
                try:
                    meta = json.load(fh)
                except ValueError:
                    meta = None
            side = os.path.join(subagent_dir, name[:-len(".meta.json")] + ".jsonl")
            parent = meta.get("toolUseId") if isinstance(meta, dict) else None
            if not isinstance(parent, str) or not parent or not os.path.isfile(side):
                out.append(("malformed", None, None, {"parent": None}))
                continue
            _parse_file(side, parent, out)
    return out


def _results(evts):
    return {e[1]: e[3]["is_error"] for e in evts if e[0] == "tool_result" and e[1]}


def read_attempts(evts):
    """Every Read tool_use, answered or not: (index, path, parent)."""
    return [(i, e[3]["input"].get("file_path"), e[3]["parent"]) for i, e in enumerate(evts)
            if e[0] == "tool_use" and e[2] == "Read"
            and isinstance(e[3]["input"].get("file_path"), str)]


def successful_reads(evts, main_only=False):
    """(index, abs_path) of Reads whose paired tool_result exists and is not an error."""
    results = _results(evts)
    idx = {e[1]: i for i, e in enumerate(evts) if e[0] == "tool_use"}
    out = []
    for i, path, parent in read_attempts(evts):
        tid = evts[i][1]
        if main_only and parent:
            continue
        if tid in results and results[tid] is False and idx.get(tid) == i:
            out.append((i, path))
    return out


def announcements(evts, pattern=ANNOUNCE_RE):
    """(index, phase_label, mark) from orchestrator text, in transcript order."""
    out = []
    for i, e in enumerate(evts):
        if e[0] == "text" and not e[3]["parent"]:
            for m in pattern.finditer(e[3]["text"]):
                out.append((i, m.group(2), m.group(1)))
    return out


def dispatches(evts, agent):
    """Answered, non-error dispatches of `agent`: list of (index, tool_use_id)."""
    results = _results(evts)
    out = []
    for i, e in enumerate(evts):
        if e[0] != "tool_use" or e[2] not in DISPATCH_TOOLS or e[3]["parent"]:
            continue
        sub = e[3]["input"].get("subagent_type")
        if isinstance(sub, str) and (sub == agent or sub.endswith(":" + agent)) \
                and results.get(e[1]) is False:
            out.append((i, e[1]))
    return out


def _as_list(v):
    return v if isinstance(v, list) else [v]


def _roots(plugin_root):
    roots = {os.path.normpath(plugin_root), os.path.realpath(plugin_root)}
    return [r for r in roots if r and r != os.sep]


def _under(path, roots):
    p = os.path.normpath(path)
    return any(p == r or p.startswith(r + os.sep) for r in roots)


def _is(path, rel, roots):
    p = os.path.normpath(path)
    return any(p == os.path.join(r, rel) for r in roots)


def _known_rels(expectation):
    rels = set(expectation["always_read"]) | set(expectation["required_reads"])
    rels |= set(expectation["forbidden_reads"])
    for v in expectation["mandatory_reads"].values():
        rels |= set(_as_list(v))
    return rels


def _plugin_shaped(path, known):
    p = os.path.normpath(path)
    if any(p.endswith("/" + rel) for rel in known):
        return True
    return "vibe-check" in p and PLUGIN_SHAPED_RE.search(p) is not None


def _add(reasons, reason):
    if reason not in reasons:
        reasons.append(reason)


def _check_sequence(anns, exp, reasons):
    first_any, first_run = {}, {}
    for i, label, mark in anns:
        first_any.setdefault(label, i)
        if mark == RUN_MARK:
            first_run.setdefault(label, i)
    expected = exp["expected_phases"]
    skip_only, optional = set(exp["skip_only_phases"]), set(exp["optional_phases"])
    for label in expected:
        if label not in first_any:
            _add(reasons, R_ABSENT % label)
        elif label not in first_run:
            _add(reasons, R_SKIPPED_REQUIRED % label)
    for label in sorted(first_any, key=first_any.get):
        if label in expected or label in optional:
            continue
        if label in skip_only:
            if label in first_run:
                _add(reasons, R_RAN_SKIP_ONLY % label)
        else:
            _add(reasons, R_UNEXPECTED % label)
    ran = sorted((l for l in expected if l in first_run), key=first_run.get)
    want = [l for l in expected if l in first_run]
    for got, exp_label in zip(ran, want):
        if got != exp_label:
            _add(reasons, R_ORDER % got)
            break
    return first_any, first_run


def check(evts, expectation, plugin_root, known_rels=None):
    """Fixed-string failure reasons for one transcript against one expectation."""
    reasons = []
    roots = _roots(plugin_root)
    malformed = sum(1 for e in evts if e[0] == "malformed")
    if malformed:
        _add(reasons, R_MALFORMED % malformed)
    results = _results(evts)
    unpaired = sum(1 for e in evts if e[0] == "tool_use" and e[1] not in results)
    if unpaired:
        _add(reasons, R_UNPAIRED % unpaired)

    anns = announcements(evts)
    if not anns:
        _add(reasons, R_NO_ANNOUNCE)
    first_any, first_run = _check_sequence(anns, expectation, reasons)

    main_reads = successful_reads(evts, main_only=True)
    all_reads = successful_reads(evts)
    first_ann = min(first_any.values()) if first_any else len(evts)

    def read_before(rel, limit):
        return any(i < limit and _is(p, rel, roots) for i, p in main_reads)

    for rel in expectation["always_read"]:
        if not read_before(rel, first_ann):
            _add(reasons, R_ALWAYS % _safe_basename(rel))
    for label, rels in expectation["mandatory_reads"].items():
        if label in first_run and not all(read_before(r, first_run[label])
                                          for r in _as_list(rels)):
            _add(reasons, R_NO_READ % label)
    for rel in expectation["required_reads"]:
        if not read_before(rel, len(evts)):
            _add(reasons, R_REQUIRED % _safe_basename(rel))
    for rel in expectation["forbidden_reads"]:
        if any(os.path.normpath(p).endswith("/" + rel) for _, p in all_reads):
            _add(reasons, R_FORBIDDEN % _safe_basename(rel))

    known = _known_rels(expectation) | set(known_rels or ())
    for _, p in all_reads:
        if _plugin_shaped(p, known) and not _under(p, roots):
            _add(reasons, R_PROVENANCE % _safe_basename(p))

    parents = {e[3]["parent"] for e in evts if e[0] != "malformed" and e[3]["parent"]}
    for agent in expectation["required_dispatches"]:
        found = dispatches(evts, agent)
        if not found:
            _add(reasons, R_NO_DISPATCH % _safe_basename(agent))
        elif not any(tid in parents for _, tid in found):
            _add(reasons, R_NO_CHILDREN % _safe_basename(agent))
    return reasons


_ENTRY_SHAPE = (("expected_phases", list), ("optional_phases", list),
                ("skip_only_phases", list), ("mandatory_reads", dict), ("always_read", list),
                ("required_reads", list), ("forbidden_reads", list),
                ("required_dispatches", list))


def _valid_entry(entry):
    return isinstance(entry, dict) and all(isinstance(entry.get(k), t) for k, t in _ENTRY_SHAPE)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def run(argv):
    parser = _Parser(add_help=False)
    parser.add_argument("--trace", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--plugin-root", required=True)
    parser.add_argument("--expectations", default=DEFAULT_EXPECTATIONS)
    parser.add_argument("--subagents")
    try:
        args = parser.parse_args(argv)
    except ValueError:
        print(USAGE_REASONS[0], file=sys.stderr)
        return 2
    if not args.plugin_root:
        print(USAGE_REASONS[0], file=sys.stderr)
        return 2
    try:
        with open(args.expectations, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        print(USAGE_REASONS[3], file=sys.stderr)
        return 2
    batches = data.get("batches") if isinstance(data, dict) else None
    batch = batches.get(args.batch) if isinstance(batches, dict) else None
    entry = batch.get(args.mode) if isinstance(batch, dict) else None
    if entry is None:
        print(USAGE_REASONS[4], file=sys.stderr)
        return 2
    if not _valid_entry(entry):
        print(USAGE_REASONS[5], file=sys.stderr)
        return 2
    if args.subagents is not None and not os.path.isdir(args.subagents):
        print(USAGE_REASONS[2], file=sys.stderr)
        return 2
    if not os.path.isfile(args.trace):
        print(USAGE_REASONS[1], file=sys.stderr)
        return 2
    try:
        evts = events(args.trace, args.subagents)
    except OSError:
        print(USAGE_REASONS[1], file=sys.stderr)
        return 2
    known = set()
    for modes in batches.values():
        for e in (modes.values() if isinstance(modes, dict) else ()):
            if _valid_entry(e):
                known |= _known_rels(e)
    reasons = check(evts, entry, args.plugin_root, known)
    for r in reasons:
        print(r, file=sys.stderr)
    return 1 if reasons else 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
