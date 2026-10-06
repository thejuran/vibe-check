"""count_cards.py — the REL-02 fix-loop card counter.

Method: a "card" is one main-session AskUserQuestion tool_use block in a run's
Claude Code transcript, deduplicated by its tool_use id. Only records with
type "assistant" and no truthy isSidechain count, so a subagent's question is
never a card and a streamed assistant message that repeats the same block
across two records is counted once. The user record that carries the answer
(toolUseResult.answers) is not a card.

Why not `grep -c AskUserQuestion`: the tool name also appears in the answer
record and in streamed duplicates, so a grep over-counts (4 vs 2 per Phase-43
run). This module counts blocks, not substrings.

Evidence rules: transcripts are local-only (never committed). A run's
transcript is bound to its committed evidence by `transcript.jsonl.sha256`;
`tally` refuses a run whose transcript is missing or whose sha256 differs
from the first token of that file. Output is counts only — never transcript
text, question text or answer labels — and errors name a fixed reason plus
the exception class only.

    python3 count_cards.py count --transcript PATH
        cards: <n>
        malformed: <m>
    python3 count_cards.py tally --runs-root R
        <diff> run-<n> cards=<k>       (one per R/<diff>/run-1..3)
        firings: F                     (scored runs)
        fix-loop firings: R            (runs with >= 1 card)
        cards: C
        cards per fix-loop firing: C/R (x.xx) | unavailable
        cards per firing: C/F (x.xx)
        malformed lines: M

Imports exactly {argparse, hashlib, json, os, re, sys}.
Exit 0 ok / 1 integrity failure / 2 usage error or unreadable input.
"""

import argparse
import hashlib
import json
import os
import re
import sys

CARD_TOOL = "AskUserQuestion"
RUN_RE = re.compile(r"^run-[1-3]$")
TRANSCRIPT = "transcript.jsonl"


class IntegrityError(Exception):
    """A run whose transcript cannot be bound to its committed sha (exit 1)."""


def _is_main(rec):
    return not rec.get("isSidechain")


def _dedupe_key(block):
    return block.get("id")


def _blocks(rec):
    msg = rec.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    for c in content if isinstance(content, list) else []:
        if isinstance(c, dict) and c.get("type") == "tool_use" and isinstance(c.get("id"), str):
            yield c


def count_cards(path):
    """(cards, malformed) for one transcript."""
    seen = set()
    malformed = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
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
            if rec.get("type") != "assistant" or not _is_main(rec):
                continue
            for block in _blocks(rec):
                if block.get("name") == CARD_TOOL:
                    seen.add(_dedupe_key(block))
    return len(seen), malformed


def _sha_ok(transcript, sha_file):
    if not (os.path.isfile(transcript) and os.path.isfile(sha_file)):
        return False
    with open(sha_file, encoding="utf-8", errors="replace") as fh:
        tokens = fh.read().split()
    if not tokens:
        return False
    h = hashlib.sha256()
    with open(transcript, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest() == tokens[0].lower()


def tally(runs_root):
    """Per-run card counts over R/<diff>/run-1..3 plus the totals."""
    rows = []
    malformed = 0
    for diff in sorted(os.listdir(runs_root)):
        ddir = os.path.join(runs_root, diff)
        if not os.path.isdir(ddir):
            continue
        for run in sorted(os.listdir(ddir)):
            rdir = os.path.join(ddir, run)
            if not RUN_RE.match(run) or not os.path.isdir(rdir):
                continue
            transcript = os.path.join(rdir, TRANSCRIPT)
            if not _sha_ok(transcript, transcript + ".sha256"):
                raise IntegrityError("transcript missing or sha mismatch: %s/%s" % (diff, run))
            cards, bad = count_cards(transcript)
            malformed += bad
            rows.append((diff, run, cards))
    return rows, malformed


def _ratio(num, den):
    return "%d/%d (%.2f)" % (num, den, float(num) / den)


def _cmd_tally(runs_root):
    rows, malformed = tally(runs_root)
    firings = len(rows)
    fix_loop = sum(1 for _d, _r, k in rows if k >= 1)
    cards = sum(k for _d, _r, k in rows)
    for diff, run, k in rows:
        print("%s %s cards=%d" % (diff, run, k))
    print("firings: %d" % firings)
    print("fix-loop firings: %d" % fix_loop)
    print("cards: %d" % cards)
    print("cards per fix-loop firing: %s" % (_ratio(cards, fix_loop) if fix_loop
                                              else "unavailable"))
    print("cards per firing: %s" % (_ratio(cards, firings) if firings else "unavailable"))
    print("malformed lines: %d" % malformed)
    return 0


def _parser():
    parser = argparse.ArgumentParser(prog="count_cards.py",
                                     description="REL-02 card counter (see module docstring).")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("count")
    p.add_argument("--transcript", required=True)
    p = sub.add_parser("tally")
    p.add_argument("--runs-root", required=True)
    return parser


def run(argv):
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    if not args.cmd:
        parser.print_usage(sys.stderr)
        return 2
    try:
        if args.cmd == "count":
            cards, malformed = count_cards(args.transcript)
            print("cards: %d" % cards)
            print("malformed: %d" % malformed)
            return 0
        if args.cmd == "tally":
            return _cmd_tally(args.runs_root)
    except IntegrityError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    except (OSError, ValueError) as exc:
        sys.stderr.write("unreadable input: %s\n" % type(exc).__name__)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
