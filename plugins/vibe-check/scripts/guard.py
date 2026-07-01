"""guard.py — the ONE tested path-containment check for the vibe-check plugin.

Fable A7/B2 (+ A10/B3): the containment logic used to live as >=5 hand-copied
inline snippets across commands/review.md, commands/deep-review.md, agents/fix.md,
and agents/codex-adversarial.md — and the copies had ALREADY drifted out of
agreement: the four bash `case "$REAL/" in "$ROOT/"*` copies FAIL OPEN when
$ROOT is empty (the pattern degenerates to `/*`, matching ANY absolute path —
including the copy guarding fix.md's auto-committing path), while the one
Python copy failed safe; and the deep-review/fix copies required the candidate
to EXIST on disk (BSD realpath prints nothing for a missing path), silently
downgrading a legitimate Codex finding about a file the diff DELETED. Every one
of those defects existed because the logic was transcribed rather than executed
from one tested source. This module is that source; the prose call sites now
invoke it instead of carrying their own copy. Do NOT re-inline the check.

Contract (fail CLOSED on every ambiguity):
  - empty/blank/missing root            -> refused (the empty-$ROOT fail-open, killed)
  - root that is not an existing dir    -> refused
  - empty/blank candidate path          -> refused
  - candidate resolving outside root    -> refused (covers `..` traversal,
    absolute escapes, and symlinked components — os.path.realpath resolves
    symlinks in every EXISTING prefix component, so a planted
    `coverage -> /outside` dir symlink is caught)
  - candidate that does NOT exist       -> still judged, LEXICALLY (the
    missing-path tolerance: os.path.realpath canonicalizes a non-existent path
    without requiring existence, so a file deleted in the reviewed range — a
    legal diff-set member — is contained iff its lexical position is inside
    the root; A10/B3)
  - sibling-dir masquerade (`/repo-other` vs `/repo`) -> refused (the compare
    is `== root` or `startswith(root + os.sep)`, the separator-safe form of
    the trailing-slash `case` compare)

I/O: stdlib-only (os/sys/argparse), no third-party deps, mirroring score.py's
conventions. CLI:

    python3 guard.py --root "$ROOT" --path "$CANDIDATE" [--path "$MORE" ...]

Exit 0 iff EVERY --path is contained under --root; exit 1 if ANY is refused;
exit 2 on usage errors (also fail closed — callers treat non-zero as refused).
One verdict line per path on stdout ("contained" or "refused: <reason>") in
argument order, for logging; callers branch on the EXIT CODE, never by parsing
stdout. Refusal reasons are FIXED strings that never echo the candidate path
(the codex-adversarial contract forbids echoing a rejected path verbatim).
"""

import argparse
import os
import sys


def contained(root, candidate):
    """Is `candidate` contained under `root`? -> (bool, fixed reason string).

    Pure decision function (the CLI below is the only I/O). `candidate` may be
    repo-relative (resolved against the root) or absolute (os.path.join lets an
    absolute path stand alone — it must then itself sit inside the root).
    Never raises on str inputs; every ambiguous input refuses (fail closed).
    """
    if not isinstance(root, str) or not root.strip():
        return False, "refused: empty root (fail closed)"
    if not isinstance(candidate, str) or not candidate.strip():
        return False, "refused: empty path (fail closed)"
    root_real = os.path.realpath(root)
    if not os.path.isdir(root_real):
        return False, "refused: root is not an existing directory (fail closed)"
    # Missing-path-TOLERANT canonicalization (A10/B3): realpath resolves
    # symlinks in existing prefix components and canonicalizes a non-existent
    # tail lexically — no existence requirement, unlike BSD `realpath`.
    cand_real = os.path.realpath(os.path.join(root_real, candidate))
    if cand_real == root_real or cand_real.startswith(root_real + os.sep):
        return True, "contained"
    return False, "refused: path resolves outside root"


def main(argv):
    parser = argparse.ArgumentParser(
        prog="guard.py",
        description="Fail-closed path containment (see module docstring).")
    parser.add_argument("--root", required=True,
                        help="the containment root (e.g. git rev-parse --show-toplevel)")
    parser.add_argument("--path", action="append", required=True,
                        help="candidate path to judge (repeatable; ALL must pass)")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        # argparse exits 2 on usage errors — keep that (non-zero => refused),
        # but never let it be exit 0.
        return 2
    ok = True
    for candidate in args.path:
        is_in, reason = contained(args.root, candidate)
        sys.stdout.write(reason + "\n")
        if not is_in:
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
