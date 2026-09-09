"""fixcommit.py — the ONE tested owner of the fix agent's commit construction.

Before this module, `agents/fix.md` (and its restatement in the Phase-5 fix loop)
carried the commit-title allowlist, the path pre-filter regex, and the message
format as PROSE, re-typed in two places. Prose copies drift; the Fable A7/B2
incident is what a drifted copy of a security check costs. This module is the
source; the prose calls it.

Division of labour (the purity rule, mirroring score.py / guard.py / chunks.py):
this module VALIDATES and BUILDS. It never runs git and never runs a shell — bash
does `git add` / `git commit`. Process-spawning modules are forbidden here by
design, and `test_fixcommit.py` scans this file's TEXT for their names, so no
example in these docs may spell one.

## The two allowlists

`PATH_RE = ^[A-Za-z0-9._/-]+$` is a **PRE-FILTER ONLY**. It denies spaces and
shell metacharacters, and it does NOT block `..`-traversal: every character of
`../../.git/hooks/pre-commit` is inside the class. **Containment is what stops
traversal**, and containment is the one tested `guard.py`, imported and called —
never an inline `case "$REAL/" in "$ROOT/"*` transcription. (Fable A7/B2: the
hand-copied inline form guarding THIS auto-committing path failed OPEN when
`$ROOT` was empty — the pattern degenerated to `/*`, matching any absolute path.
guard.py fails CLOSED on an empty root, refuses absolute escapes and
`/repo-other` masquerades, and judges a deleted-file path lexically, so a
multi-site fix touching a just-deleted sibling still validates.)

`TITLE_ALLOWED = ^[A-Za-z0-9 ._:/()#=-]+$` is the commit-title allowlist
(`-` stays last so it is a literal, not a range; `=` sits just before it). It is
load-bearing:

  * It excludes newlines, carriage returns and ASCII control chars
    (`\\x00`-`\\x1F`, `\\x7F`). The message is written verbatim, so a control
    char would let a title forge commit trailers (e.g. a `Co-Authored-By:`
    line). **That exclusion is the non-negotiable trailer-forgery guard.**
  * It PERMITS `=`, because a `flag=value` title (`Avoid shell=True when
    spawning`, `verify=False`) is legitimate and must be committable. `=` is
    inert in a one-line subject given the `%s`-arg formatting + `-F msgfile` +
    `--cleanup=verbatim` mechanics: it cannot start a new line, so it cannot
    forge a trailer without a newline.
  * It EXCLUDES `"`, `'` and `,` — deliberately STRICTER than
    `agents/codex-adversarial.md`'s display title-sanitization class, which
    keeps all three. That is not a disagreement: a display string is rendered,
    a commit subject is constructed, and the quote characters are not
    demonstrably safe at a construction site. **Do NOT re-widen this class.**
    `test_codex_translate.py::TestAllowlistRelationship` pins the relationship
    one-directionally (everything this class permits survives the display
    sanitizer unchanged; the reverse must not hold).

Rejection is REJECTION, never sanitization: a stripped title yields a
plausible-looking commit that hides the injection attempt. There is deliberately
no `sanitize_title` here.

## FL-03 (R4) — why the title arrives as JSON, never on argv

The finding title originates in reviewer-agent output derived from the reviewed
repo, i.e. attacker-influenced. The previous caller substituted it into a bash
command line as `--title "<finding.title>"`, so **the shell expanded it before
this module ever ran** — a title containing a command substitution executed at
expansion time. Reproduced. Python validation cannot protect bytes that a shell
already consumed.

So the CLI takes `--finding-json <path>`: the agent writes the finding record
(`pass_number`, `title`, `paths`) to a temp file with its `Write` tool, and bash
passes only that path. No attacker-influenced byte ever appears on a command
line. There is intentionally NO `--title` / `--pass` / `--path` flag; adding one
would restore the defect.

## Fail-closed CLI contract (D-13 gate semantics, F5)

Exit 0 only when every path is contained AND the title is clean AND the message
file was written. On ANY rejection: a fixed reason on stderr, NOTHING written,
exit 1. Reasons name the FAILING RULE, never the offending path or title
(Shared Pattern 3 / T-40-23c).

The caller must branch with `if ...; then <git ops>; else <record errored>; fi`.
An or-brace gate whose failure branch is the shell no-op builtin SUCCEEDS, so
execution falls straight through into `git add`/`git commit` after a rejection.
That was reproduced; a rejection must make the side effect UNREACHABLE, not
merely logged.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import guard  # noqa: E402  (the ONE containment source; never re-inlined here)

# Pre-filter only — see the module docstring. Containment stops traversal.
PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")

# Commit-title allowlist — stricter than the display sanitizer ON PURPOSE.
TITLE_ALLOWED = re.compile(r"^[A-Za-z0-9 ._:/()#=-]+$")

# Pass numbers are digits only; anything else could reach the subject line.
PASS_RE = re.compile(r"^[0-9]+$")


def validate_title(title):
    """Is `title` safe to construct a commit subject from? -> (ok, reason).

    Rejects, never strips (`agents/fix.md`: "reject (do NOT silently strip)").
    The reason names the failing rule and never echoes the title.
    """
    if not isinstance(title, str):
        return False, "refused: title is not a string (fail closed)"
    if not title:
        return False, "refused: empty title (fail closed)"
    if TITLE_ALLOWED.match(title) is None:
        return False, ("refused: title contains a character outside the commit "
                       "allowlist (control chars, quotes and comma are excluded)")
    return True, "accepted"


def validate_paths(root, paths):
    """Is every path in the finding's file set safe? -> (ok, reason).

    Two checks per path, in order: the `PATH_RE` pre-filter, then containment.

    **F4 — `guard.contained` takes ONE STRING candidate, not a list.** Its first
    action on the candidate is `.strip()`, so a list fails the isinstance check
    and returns `(False, "refused: empty path (fail closed)")`. A single "bulk"
    call would therefore refuse every ordinary multi-file fix. The bulk shape
    lives in guard's CLI loop — the `--path a --path b` form the bash gates use.
    The Python API is per-candidate, so this LOOPS, one `str` at a time, and
    short-circuits on the first refusal (a refusal is a refusal).
    """
    if not isinstance(paths, list) or not paths:
        return False, "refused: empty or non-list path set (fail closed)"
    for path in paths:
        if not isinstance(path, str) or not path.strip():
            return False, "refused: empty or non-string path (fail closed)"
        if path.startswith("-"):
            # A leading `-` is the option-injection shape (`--upload-pack=...`).
            # The `--` end-of-options guard on the git calls is the other half;
            # refusing here means a crafted path never gets that far.
            return False, "refused: path begins with a dash (option injection)"
        if PATH_RE.match(path) is None:
            return False, ("refused: path fails the character pre-filter "
                           "(spaces and shell metacharacters are denied)")
        ok, _ = guard.contained(root, path)
        if not ok:
            return False, "refused: path fails containment under the repo root"
    return True, "accepted"


def build_message(pass_number, title):
    """The commit message for one applied finding. Raises ValueError if unsafe.

    Exactly one line plus one trailing newline; `--cleanup=verbatim` keeps it
    byte-for-byte, so the validation above is the only thing standing between a
    crafted title and a forged trailer.
    """
    if isinstance(pass_number, bool) or not isinstance(pass_number, (int, str)):
        return _reject("refused: pass number is not an int or digit string")
    text = str(pass_number)
    if PASS_RE.match(text) is None:
        return _reject("refused: pass number is not digits-only")
    ok, reason = validate_title(title)
    if not ok:
        return _reject(reason)
    return "fix(review-pass-%s): %s\n" % (text, title)


def _reject(reason):
    raise ValueError(reason)


# The ONLY flags this CLI accepts. FL-03: `--title`, `--pass` and `--path` are
# deliberately ABSENT — an attacker-influenced value on a command line is
# expanded by the shell before Python runs, so those flags cannot exist here.
KNOWN_FLAGS = ("--finding-json", "--root", "--msgfile")

USAGE = ("usage: fixcommit.py --finding-json <path> --root <repo> "
         "--msgfile <path>\n")


def parse_argv(argv):
    """Hand-rolled so an UNKNOWN flag is a usage error, not a silent default.

    Deliberately not argparse: the import set for this module is
    {json, os, re, sys, guard}, and a hand parser lets the FL-03 rejection of a
    `--title` flag be an explicit, testable "unrecognized arguments" error.
    Returns (values, None) or (None, error message).
    """
    values = {}
    i = 0
    while i < len(argv):
        token = argv[i]
        if token not in KNOWN_FLAGS:
            return None, "unrecognized arguments: %s\n" % token
        if i + 1 >= len(argv):
            return None, "argument %s: expected one argument\n" % token
        if token in values:
            return None, "argument %s: given more than once\n" % token
        values[token] = argv[i + 1]
        i += 2
    missing = [f for f in KNOWN_FLAGS if f not in values]
    if missing:
        return None, ("the following arguments are required: %s\n"
                      % ", ".join(missing))
    return values, None


def run(argv):
    """CLI. Exit 0 on success (msgfile written), 1 on any rejection, 2 on usage.

    Never runs git. The caller stages and commits ONLY inside the success branch
    of an `if`; see the docstring's fail-closed contract.
    """
    values, err = parse_argv(argv)
    if err is not None:
        sys.stderr.write(USAGE)
        sys.stderr.write(err)
        return 2  # usage errors are non-zero too — callers treat that as refused

    try:
        with open(values["--finding-json"], "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError, UnicodeDecodeError):
        sys.stderr.write("refused: finding record is missing or not valid JSON\n")
        return 1
    if not isinstance(record, dict):
        sys.stderr.write("refused: finding record is not an object\n")
        return 1

    ok, reason = validate_paths(values["--root"], record.get("paths"))
    if not ok:
        sys.stderr.write(reason + "\n")
        return 1
    try:
        message = build_message(record.get("pass_number"), record.get("title"))
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1

    try:
        with open(values["--msgfile"], "w", encoding="utf-8") as fh:
            fh.write(message)
    except OSError:
        sys.stderr.write("refused: could not write the message file\n")
        return 1

    for path in record["paths"]:
        sys.stdout.write(path + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
