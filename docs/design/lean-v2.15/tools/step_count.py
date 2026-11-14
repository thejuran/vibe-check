"""step_count.py — count the mechanical steps the model carries out itself.

Finalize asks the model to do a series of mechanical things by hand: run
shell commands, write files with the Write tool, and copy values printed by
one command into later commands. This script counts those things over the
files a mode path declares (`footprint.MODE_PATHS`), so the count before and
after a change can be compared with one fixed rule.

What is counted, per file:

- `bash_fences` — every bash block. A block opens on a line that is optional
  leading whitespace, then three or four backticks, then `bash`, then end of
  line; it closes on the next line that is optional leading whitespace and the
  same number of backticks, nothing else. Indented blocks and four-backtick
  blocks count. Each block is one command the model runs.
- `inline_commands` — inline code spans (single backticks, on one line,
  outside every fence of any language) that start with a lowercase command
  word and a space, hold `"$NAME"` or `"$NAME.` for a printed name, and are
  directly preceded by one of `INLINE_RUN_LEADS`. Each is one command the
  model runs.
- `write_tool_writes` — occurrences of a phrase in `WRITE_PHRASES`. Each is
  one file the model writes with the Write tool.
- `carried_paste_sites` — for every name a bash block prints with
  `printf 'NAME=%s\\n' "$..."`, the occurrences of `"$NAME"` or `"$NAME.` in
  bash blocks other than the one that prints it, plus those inside counted
  inline commands. Each is one value copied from earlier output.
- `printed_literals_distinct` — distinct printed names. Reported, never added
  to the total: every copy of a printed value is already a paste site.
- `model_run_steps` = bash_fences + inline_commands + write_tool_writes +
  carried_paste_sites.

The count is static over the declared files, so it is an upper bound: one
Finalize run does not execute every block. The figures are operation counts,
not tokens and not price.

Stdlib only (module-level imports: argparse, json, os, re, subprocess, sys).
CLI:

    python3 docs/design/lean-v2.15/tools/step_count.py [--repo <root>]
        (--rev <commit> | --root <plugin root>) [--mode finalize] [--json]
        [--out <path>]

`verify_steps(repo, record_path)` recounts a committed record over the file
list stored in the record itself, at the record's revision.

Exit codes: 0 ok, 2 unusable input (unknown revision, a missing file, an
unknown mode). Nothing is printed on stdout when the exit is 2.
"""

import argparse
import json
import os
import re
import subprocess
import sys

RULE_VERSION = 1

# Tag v2.14.1, pinned by full commit id so a shallow checkout resolves it.
BASELINE_COMMIT = "dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4"

KIND = "operation count — not tokens, not price"

PLUGIN_PREFIX = "plugins/vibe-check"
PLUGIN_SCRIPTS_REL = os.path.join("plugins", "vibe-check", "scripts")

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

# Phrases that instruct the model to write a file with the Write tool. At
# BASELINE_COMMIT every Finalize-path line naming the Write tool instructs a
# write (six "with the Write tool", one "Use Write to create"); CRITERION.md
# holds the line-by-line classification.
WRITE_PHRASES = ("with the Write tool", "Use Write to create")

# Text that, directly before an inline code span, makes it an instruction to
# run that command (as opposed to a mention of it). At BASELINE_COMMIT the five
# candidate spans all instruct a run, led by "run " (two), "Run " (one), "→ "
# (one) and "file-to-file with " (one); CRITERION.md holds the classification.
INLINE_RUN_LEADS = ("run ", "Run ", "→ ", "file-to-file with ")

# The one test for a bash fence's opening line.
FENCE_OPEN = re.compile(r"^[ \t]*`{3,4}bash$")
# Any fence opening line, of any language (used to skip non-bash fences).
_ANY_FENCE_OPEN = re.compile(r"^[ \t]*(`{3,})[^`]*$")
_PRINT_RE = re.compile(r"printf '([A-Z_]+FILE)=%s\\n' \"\$[A-Za-z_][A-Za-z0-9_]*\"")
_SPAN_RE = re.compile(r"`([^`\n]+)`")
_COMMAND_WORD = re.compile(r"^[a-z][a-z0-9._-]*\s")

COUNTED = ("bash_fences", "inline_commands", "write_tool_writes",
           "carried_paste_sites")


class StepCountError(Exception):
    """Unusable input: the caller reports it and exits 2."""


def _ticks(line):
    stripped = line.lstrip(" \t")
    return len(stripped) - len(stripped.lstrip("`"))


def _scan(text):
    """(bash fence bodies, lines outside every fence) for `text`."""
    bodies = []
    outside = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        is_bash = bool(FENCE_OPEN.match(line))
        if is_bash or _ANY_FENCE_OPEN.match(line):
            n = _ticks(line)
            close = re.compile(r"^[ \t]*`{%d}$" % n)
            body = []
            i += 1
            while i < len(lines) and not close.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1  # past the closing line (or the end of the text)
            if is_bash:
                bodies.append("\n".join(body))
            continue
        outside.append(line)
        i += 1
    return bodies, outside


def fences(text):
    """The bodies of every bash fence in `text`, in order."""
    return _scan(text)[0]


def outside_fence_lines(text):
    """The lines of `text` that sit outside every fence of any language."""
    return _scan(text)[1]


def _ref_re(name):
    return re.compile(r'"\$' + re.escape(name) + r'(?=[".])')


def _prints(body, name):
    return name in _PRINT_RE.findall(body)


def _fences_for_pastes(bodies, name):
    """The fences where a paste of `name` counts: all but its printer(s)."""
    return [b for b in bodies if not _prints(b, name)]


def inline_candidates(text, printed=None):
    """Inline spans outside fences that look like a command on a printed name.

    Returns `(line_text, span, preceding_text)` for each candidate, whether or
    not a lead-in precedes it; the count keeps only those with a lead-in.
    """
    bodies, outside = _scan(text)
    if printed is None:
        printed = sorted({n for b in bodies for n in _PRINT_RE.findall(b)})
    refs = [_ref_re(n) for n in printed]
    out = []
    for line in outside:
        for m in _SPAN_RE.finditer(line):
            span = m.group(1)
            if not _COMMAND_WORD.match(span):
                continue
            if not any(r.search(span) for r in refs):
                continue
            out.append((line, span, line[:m.start()]))
    return out


def count_text(text):
    """The counts for one file's text (see the module docstring)."""
    bodies, _ = _scan(text)
    printed = sorted({n for b in bodies for n in _PRINT_RE.findall(b)})
    inline = [span for _, span, before in inline_candidates(text, printed)
              if any(before.endswith(lead) for lead in INLINE_RUN_LEADS)]
    pastes = 0
    for name in printed:
        ref = _ref_re(name)
        for body in _fences_for_pastes(bodies, name):
            pastes += len(ref.findall(body))
        for span in inline:
            pastes += len(ref.findall(span))
    writes = sum(text.count(p) for p in WRITE_PHRASES)
    counts = {
        "bash_fences": len(bodies),
        "inline_commands": len(inline),
        "printed_literals": printed,
        "printed_literals_distinct": len(printed),
        "carried_paste_sites": pastes,
        "write_tool_writes": writes,
    }
    counts["model_run_steps"] = sum(counts[k] for k in COUNTED)
    return counts


def _read(repo, rev, root, rel):
    if root is not None:
        try:
            with open(os.path.join(root, rel), "rb") as fh:
                data = fh.read()
        except OSError:
            raise StepCountError("cannot read %s under %s" % (rel, root))
    else:
        try:
            proc = subprocess.run(
                ["git", "-C", repo, "show", "%s:%s/%s" % (rev, PLUGIN_PREFIX, rel)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise StepCountError("cannot run git show for %s: %s" % (rel, exc))
        if proc.returncode != 0:
            raise StepCountError("%s is not readable at revision %s" % (rel, rev))
        data = proc.stdout
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise StepCountError("%s is not UTF-8" % rel)


def count_files(repo, rev, files, root=None, mode="finalize"):
    """Count an explicit file list at `rev` (or under `root`).

    Reads every file before returning, so an unreadable file raises
    StepCountError and no partial record is produced.
    """
    if root is None and not rev:
        raise StepCountError("give a revision or a plugin root")
    rows = []
    for rel in files:
        row = {"path": rel}
        row.update(count_text(_read(repo, rev, root, rel)))
        rows.append(row)
    totals = {k: sum(r[k] for r in rows) for k in COUNTED + ("model_run_steps",)}
    totals["printed_literals_distinct"] = len(
        {n for r in rows for n in r["printed_literals"]})
    return {
        "rule_version": RULE_VERSION,
        "rev": rev if root is None else None,
        "mode": mode,
        "files": rows,
        "totals": totals,
        "kind": KIND,
        "write_phrases": list(WRITE_PHRASES),
        "inline_run_leads": list(INLINE_RUN_LEADS),
    }


def count_path(repo, rev=None, root=None, mode="finalize"):
    """Count the files `footprint.MODE_PATHS[mode]` declares."""
    scripts = os.path.join(repo, PLUGIN_SCRIPTS_REL)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        import footprint
    except ImportError as exc:
        raise StepCountError("cannot import footprint from %s: %s" % (scripts, exc))
    if mode not in footprint.MODE_PATHS:
        raise StepCountError("unknown mode path: %s" % mode)
    return count_files(repo, rev, list(footprint.MODE_PATHS[mode]),
                       root=root, mode=mode)


def verify_steps(repo, record_path):
    """Recount a committed record over its own file list at its own revision.

    Never imports `footprint`: the baseline is tied to the files named in the
    record, so a later change to `MODE_PATHS` cannot move it. Returns `[]` when
    the recount equals the record, else one line per differing file or total.
    """
    try:
        with open(record_path, encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError) as exc:
        return ["record unreadable: %s" % exc]
    try:
        files = [row["path"] for row in record["files"]]
        fresh = count_files(repo, record["rev"], files, mode=record.get("mode", "finalize"))
    except (KeyError, TypeError) as exc:
        return ["record malformed: %s" % exc]
    except StepCountError as exc:
        return ["recount failed: %s" % exc]
    problems = []
    for want, got in zip(record["files"], fresh["files"]):
        diffs = sorted(k for k in set(want) | set(got) if want.get(k) != got.get(k))
        if diffs:
            problems.append("file differs: %s (%s)" % (want["path"], ", ".join(diffs)))
    for key in sorted(set(record.get("totals", {})) | set(fresh["totals"])):
        if record.get("totals", {}).get(key) != fresh["totals"].get(key):
            problems.append("total differs: %s (record %r, recount %r)" % (
                key, record.get("totals", {}).get(key), fresh["totals"].get(key)))
    for key in ("rule_version", "write_phrases", "inline_run_leads", "kind"):
        if record.get(key) != fresh[key]:
            problems.append("rule differs: %s" % key)
    return problems


def _render(record):
    cols = ("bash_fences", "inline_commands", "write_tool_writes",
            "carried_paste_sites", "model_run_steps")
    head = ["path"] + list(cols)
    out = ["%-34s %s" % (head[0], " ".join("%20s" % c for c in cols))]
    for row in record["files"] + [dict(record["totals"], path="TOTAL")]:
        out.append("%-34s %s" % (row["path"], " ".join("%20d" % row[c] for c in cols)))
    out.append("printed literals (distinct): %d" % record["totals"]["printed_literals_distinct"])
    out.append("rev: %s  rule_version: %d  (%s)" % (record["rev"], record["rule_version"],
                                                     record["kind"]))
    return "\n".join(out) + "\n"


def dump_json(record):
    return json.dumps(record, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def build_parser():
    p = argparse.ArgumentParser(prog="step_count.py",
                                description="Count model-run mechanical steps.")
    p.add_argument("--repo", default=DEFAULT_REPO)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--rev")
    src.add_argument("--root")
    p.add_argument("--mode", default="finalize")
    p.add_argument("--json", action="store_true")
    p.add_argument("--out", help="write the JSON record to this path")
    return p


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        record = count_path(args.repo, rev=args.rev, root=args.root, mode=args.mode)
    except StepCountError as exc:
        sys.stderr.write("step_count.py: %s\n" % exc)
        return 2
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(dump_json(record))
        except OSError as exc:
            sys.stderr.write("step_count.py: cannot write %s: %s\n" % (args.out, exc))
            return 2
        return 0
    sys.stdout.write(dump_json(record) if args.json else _render(record))
    return 0


if __name__ == "__main__":
    sys.exit(main())
