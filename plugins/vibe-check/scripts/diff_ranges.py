"""diff_ranges.py — exact changed-line ranges from one unified diff.

Contract:

    ranges_from_diff(text) -> {path: [[start, end], ...]}

The ranges are new-side line numbers, sorted and merged per file, built from
the `+` and `-` markers of each hunk body. The header supplies only the first
new-side line and the body's line budgets, never the range itself, so git's
display context (`-U0`, the default 3 lines, `-U10`) does not change the
result. Per contiguous change block starting at new-side line s:

- a added lines           -> [s, s + a - 1]
- a added, d > a deleted  -> [s, s + a]  (net deletion: the line just after
                                           the replacement also counts)
- pure deletion           -> [max(T, 1), T + 1]  with T = s - 1, the last
                                           new-side line before the deletion
                                           (`-U0` prints it as `+T,0`)

Hunk bodies are consumed against the header's old/new budgets, so a content
line that prints as `--- x` or `+++ y` is never read as a file header. A
`\\ No newline at end of file` line consumes no budget. An empty line inside
a hunk body is a blank context line (`diff.suppressBlankEmpty`). Deleted files
(`+++ /dev/null`) and C-quoted paths (names git had to escape, which can
never carry a finding) contribute no ranges. An empty diff gives `{}`.

Structurally inconsistent input raises RangeError with one of the fixed
REASONS (never text from the input): a commit series (mbox `From <sha>`
separator), a combined `@@@` hunk, a body shorter or longer than its header,
a body line that is not ` `, `+`, `-`, `\\` or empty, a line starting with
an escape byte (a colored or escaped diff), or non-empty text with no diff
structure at all (an error message, `--stat` output). A diff with file
headers but no hunk (binary-only, mode-only) gives `{}`.

Pure: no git, file or shell I/O; the caller runs git and pipes the text in.
Imports exactly {json, re, sys}. CLI:

    git diff --no-color --no-ext-diff --no-textconv --no-relative \\
      --src-prefix=a/ --dst-prefix=b/ HEAD \\
      | python3 diff_ranges.py

Exit 0: the ranges as JSON (sorted keys) on stdout. Exit 2: a refusal reason
on stderr and nothing on stdout; any argv also exits 2. Any other error
propagates, so the process exits non-zero (fails closed).
"""

import json
import re
import sys

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_MBOX = re.compile(r"^From [0-9a-f]{40} ")


class RangeError(ValueError):
    """The diff text is not one consistent unified diff."""


REASON_MBOX = "commit series, not a single diff"
REASON_COMBINED = "combined diff"
REASON_SHORT_BODY = "hunk body shorter than its header"
REASON_LONG_BODY = "hunk body longer than its header"
REASON_BAD_BODY_LINE = "unexpected line in hunk body"
REASON_ESCAPE = "colored or escaped diff"
REASON_NOT_A_DIFF = "not a unified diff"

REASONS = (
    REASON_MBOX,
    REASON_COMBINED,
    REASON_SHORT_BODY,
    REASON_LONG_BODY,
    REASON_BAD_BODY_LINE,
    REASON_ESCAPE,
    REASON_NOT_A_DIFF,
)


def _split_lines(text):
    """Split on "\\n" only. Python's universal line splitting would also
    break content lines at form feeds and Unicode line separators and
    desynchronise the body count. The empty piece after a final newline is
    not a line."""
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines


def _is_mbox(line):
    return _MBOX.match(line) is not None


def _file_path(line):
    """The new-side path of a `+++ ` header, or None when it has none."""
    path = line[4:]
    if path.endswith("\t"):
        path = path[:-1]
    if path == "/dev/null" or path.startswith('"'):
        return None
    return path[2:] if path.startswith("b/") else path


def _count(group):
    return 1 if group is None else int(group)


def _close_block(out, path, block):
    """Record one change block [start, added, deleted]; returns the empty
    block so the caller can reset in one statement."""
    if block is not None and path is not None:
        start, added, deleted = block
        if added:
            end = start + added - 1
            if deleted > added:
                end += 1
            out.setdefault(path, []).append([start, end])
        elif deleted:
            out.setdefault(path, []).append([max(start - 1, 1), start])
    return None


def _walk_hunk(lines, i, match, path, out):
    """Consume one hunk body starting at lines[i]; return the next index."""
    old_count = _count(match.group(2))
    new_start = int(match.group(3))
    new_count = _count(match.group(4))
    old_left, new_left = old_count, new_count
    # git numbers an empty new side by the line BEFORE it (`+8,0` follows
    # line 8), so the first new-side line after the hunk is one further on.
    cursor = new_start + 1 if new_count == 0 else new_start
    block = None
    while old_left > 0 or new_left > 0:
        if i >= len(lines):
            raise RangeError(REASON_SHORT_BODY)
        body = lines[i]
        i += 1
        tag = body[:1] if body else " "
        if tag == "\\":
            continue
        if tag == " ":
            block = _close_block(out, path, block)
            cursor += 1
            old_left -= 1
            new_left -= 1
        elif tag == "+":
            if block is None:
                block = [cursor, 0, 0]
            block[1] += 1
            cursor += 1
            new_left -= 1
        elif tag == "-":
            if block is None:
                block = [cursor, 0, 0]
            block[2] += 1
            old_left -= 1
        else:
            raise RangeError(REASON_BAD_BODY_LINE)
        if old_left < 0 or new_left < 0:
            raise RangeError(REASON_LONG_BODY)
    _close_block(out, path, block)
    return i


def _is_stray_body_line(line):
    """A body line left over once a hunk's budgets are spent."""
    if line.startswith("+++ ") or line.startswith("--- "):
        return False
    return line[:1] in ("+", "-", " ")


def _merge(ranges):
    """Sort and merge overlapping or adjacent [start, end] ranges."""
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def ranges_from_diff(text):
    """{path: [[start, end], ...]} of the lines a unified diff changes."""
    out = {}
    path = None
    after_hunk = False
    saw_diff = False
    lines = _split_lines(text)
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.startswith("\x1b"):
            raise RangeError(REASON_ESCAPE)
        if _is_mbox(line):
            raise RangeError(REASON_MBOX)
        if line.startswith("@@@"):
            raise RangeError(REASON_COMBINED)
        if line.startswith("\\"):
            continue
        if after_hunk and _is_stray_body_line(line):
            raise RangeError(REASON_LONG_BODY)
        after_hunk = False
        if line.startswith(("diff --", "--- ", "+++ ")):
            saw_diff = True
        if line.startswith("+++ "):
            path = _file_path(line)
            continue
        match = _HUNK.match(line)
        if match is None:
            continue
        saw_diff = True
        i = _walk_hunk(lines, i, match, path, out)
        after_hunk = True
    if not saw_diff and any(lines):
        raise RangeError(REASON_NOT_A_DIFF)
    return {p: _merge(out[p]) for p in sorted(out)}


def run(argv, stdin_bytes):
    """CLI body: 0 with JSON on stdout, or 2 with a reason on stderr."""
    if argv:
        return 2
    text = stdin_bytes.decode("utf-8", errors="surrogateescape")
    try:
        result = ranges_from_diff(text)
    except RangeError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    json.dump(result, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:], sys.stdin.buffer.read()))
