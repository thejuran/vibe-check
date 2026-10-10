"""fixcommit.py — the ONE tested owner of the fix agent's commit construction.

Before this module, `agents/fix.md` (and its restatement in the Phase-5 fix loop)
carried the commit-title allowlist, the path pre-filter regex, and the message
format as PROSE, re-typed in two places. Prose copies drift; the Fable A7/B2
incident is what a drifted copy of a security check costs. This module is the
source, and it is a LIBRARY: `fixstage.py commit` (and `fixcheck.py`) import it.
It has no command-line interface of its own (see "Retired CLI" below).

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

`TITLE_ALLOWED = ^[A-Za-z0-9 ._:/()#=,-]+$` is the commit-title allowlist
(`-` stays last so it is a literal, not a range; `=` and `,` sit just before it). It is
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
  * It PERMITS `,` (owner decision D-16, Phase 48): finding titles routinely
    carry commas, and a comma is inert in a one-line `-F msgfile` +
    `--cleanup=verbatim` subject — it cannot start a new line, so it cannot
    forge a trailer.
  * It still EXCLUDES `"` and `'` (and every control character) — deliberately
    STRICTER than `agents/codex-adversarial.md`'s display title-sanitization
    class, which keeps them. That is not a disagreement: a display string is
    rendered, a commit subject is constructed, and the quote characters are not
    demonstrably safe at a construction site. **Do NOT re-widen this class to
    admit quotes, apostrophes or control characters.**
    `test_codex_translate.py::TestAllowlistRelationship` pins the relationship
    one-directionally (everything this class permits survives the display
    sanitizer unchanged; the reverse must not hold).

## Commit subjects are sanitized deterministically (owner decision D-08)

A verified fix is never refused over title punctuation. `commit_subject` maps
the title into the class above: `"` and `'` are dropped; `;` becomes `,`; every
other character outside the class becomes a space (that covers control
characters, U+0085, the line and paragraph separators, bidi controls and
zero-width characters); runs of spaces are collapsed and the ends trimmed. A title that sanitizes to
nothing becomes `finding <first 8 hex chars of the finding id>`.

The trailer-forgery invariant is preserved, not traded away: no newline or
other control character can survive, and `build_message` re-checks the result
with `TITLE_ALLOWED.fullmatch` as a belt, refusing if the sanitizer ever let
something through. The injection attempt stays visible as plain text on the
one subject line. `validate_title` remains a pure predicate ("is this already a
legal subject?"); it never cleans.

## FL-03 (R4) — why the title arrives as JSON, never on argv

The finding title originates in reviewer-agent output derived from the reviewed
repo, i.e. attacker-influenced. An earlier caller substituted it into a bash
command line as `--title "<finding.title>"`, so **the shell expanded it before
this module ever ran** — a title containing a command substitution executed at
expansion time. Reproduced. Python validation cannot protect bytes that a shell
already consumed. So the title reaches this module only as data: fixstage reads
the finding record from a JSON file the agent wrote, and hands the parsed title
to `build_message`. No attacker-influenced byte ever appears on a command line.

## Retired CLI

This module once had its own `--finding-json/--root/--msgfile` command line.
`fixstage.py commit` owns the commit path now, so that interface is gone.
Running this file directly writes a retirement notice to stderr and exits 2 —
never 0, because a stale `if <run this file>; then git commit; fi` fence would
otherwise fall straight through into the commit.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import guard  # noqa: E402  (the ONE containment source; never re-inlined here)

# Pre-filter only — see the module docstring. Containment stops traversal.
PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")

# Commit-title allowlist — stricter than the display sanitizer ON PURPOSE.
TITLE_ALLOWED = re.compile(r"^[A-Za-z0-9 ._:/()#=,-]+$")

# Pass numbers are digits only; anything else could reach the subject line.
PASS_RE = re.compile(r"^[0-9]+$")

# commit_subject's character maps (see the docstring, D-08). `_OUTSIDE_TITLE`
# is the complement of TITLE_ALLOWED's class, so every control character,
# U+0085, line/paragraph separator, bidi control and zero-width character is
# mapped to a space by it; the belt in build_message keeps the two honest.
_DROPPED = re.compile("[\"']")
_OUTSIDE_TITLE = re.compile(r"[^A-Za-z0-9 ._:/()#=,-]")
_SPACE_RUN = re.compile(r" {2,}")

# The finding id (fixstage validates it as lowercase hex, 8-64 chars).
_FINDING_ID_RE = re.compile(r"^[0-9a-f]{8,64}$")


def validate_title(title):
    """Is `title` safe to construct a commit subject from? -> (ok, reason).

    A pure predicate: it never cleans (`commit_subject` does that, D-08).
    The reason names the failing rule and never echoes the title.
    """
    if not isinstance(title, str):
        return False, "refused: title is not a string (fail closed)"
    if not title:
        return False, "refused: empty title (fail closed)"
    if TITLE_ALLOWED.match(title) is None:
        return False, ("refused: title contains a character outside the commit "
                       "allowlist (control chars and quotes are excluded)")
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


# Directories a staged fix may never snapshot, check or write: git's own state
# and this tool's state. Matched against EVERY path segment (a nested
# `x/.git/hooks/pre-commit` is a submodule/worktree git dir just the same),
# case-insensitively for case-insensitive filesystems.
RESERVED_DIRS = (".git", ".turingmind")


def _has_reserved_segment(path):
    return any(seg.lower() in RESERVED_DIRS for seg in path.split("/"))


def validate_fix_paths(root, paths):
    """validate_paths plus normal form and reserved directories -> (ok, reason).

    The ONE source for fixstage.py and fixcheck.py (never re-copied there).
    On top of `validate_paths`, every path must be in normal form (`a/./b`,
    `a/../b` or a trailing slash would give one file two keys) and no segment
    of it — as written, or after resolving symlinks under the real root — may
    be a reserved directory.
    """
    ok, reason = validate_paths(root, paths)
    if not ok:
        return ok, reason
    for path in paths:
        if os.path.normpath(path) != path:
            return False, "refused: path is not in normal form"
        if _has_reserved_segment(path):
            return False, "refused: path is inside a reserved directory"
        # Symlink resolution is guard's (the ONE canonicalization source).
        resolved = guard.resolved_relpath(root, path)
        if resolved is None:
            return False, "refused: path fails containment under the repo root"
        if _has_reserved_segment(resolved):
            return False, "refused: path is inside a reserved directory"
    return True, "accepted"


def commit_subject(title, finding_id):
    """The deterministic, single-line commit subject for a finding title (D-08).

    Never refuses over punctuation. Raises ValueError only for a non-string
    title, or for a title that sanitizes to nothing when there is no valid
    finding id to fall back on. The result always matches TITLE_ALLOWED.
    """
    if not isinstance(title, str):
        return _reject("refused: title is not a string (fail closed)")
    subject = _DROPPED.sub("", title)
    subject = subject.replace(";", ",")
    subject = _OUTSIDE_TITLE.sub(" ", subject)
    subject = _SPACE_RUN.sub(" ", subject).strip()
    if subject:
        return subject
    if (not isinstance(finding_id, str)
            or _FINDING_ID_RE.fullmatch(finding_id) is None):
        return _reject("refused: title is empty after sanitizing and the "
                       "finding id is not lowercase hex")
    return "finding " + finding_id[:8]


def build_message(pass_number, title, finding_id=None):
    """The commit message for one applied finding. Raises ValueError if unsafe.

    Exactly one line plus one trailing newline; `--cleanup=verbatim` keeps it
    byte-for-byte. The subject comes from `commit_subject`; the
    `TITLE_ALLOWED.fullmatch` belt below is what guarantees no newline (and so
    no forged trailer) can reach the message even if the sanitizer regresses.
    """
    if isinstance(pass_number, bool) or not isinstance(pass_number, (int, str)):
        return _reject("refused: pass number is not an int or digit string")
    text = str(pass_number)
    if PASS_RE.match(text) is None:
        return _reject("refused: pass number is not digits-only")
    subject = commit_subject(title, finding_id)
    if not isinstance(subject, str) or TITLE_ALLOWED.fullmatch(subject) is None:
        return _reject("refused: sanitized title is outside the commit "
                       "allowlist (fail closed)")
    return "fix(review-pass-%s): %s\n" % (text, subject)


def _reject(reason):
    raise ValueError(reason)


if __name__ == "__main__":
    sys.stderr.write("fixcommit CLI is retired — fixstage.py commit owns the "
                     "commit path\n")
    sys.exit(2)
