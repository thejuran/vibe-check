# finalize_step1_2141.sh: the 2.14.1 Finalize "HEAD fingerprints" step for
# ONE finding file, kept as a test fixture. It is never run by the plugin.
#
# Source: commit dd8e4ab (tag v2.14.1),
#   plugins/vibe-check/phases/shared/90-finalize.md, lines 13-22
#   (Finalize mode, step 1 "HEAD fingerprints").
# Line 13 gives the per-file procedure: the file name must match
# `^[A-Za-z0-9._/-]+$` AND
#   python3 "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "<file>"
# must exit 0; then, for a validated name, run
#   git rev-parse "HEAD:<file>"
#   git diff --quiet HEAD -- <file>
#   git diff --cached --quiet -- <file>
# Line 22 keeps the file "ONLY when all three exit 0", with the blob that
# `git rev-parse` printed. Every command runs in the session's folder (the
# shell's working directory); nothing here changes directory.
#
# Transcription choices, each equivalent to the text:
# - The pattern is applied with Python's `re.match`, as the PATH_RE pre-filter
#   the text names (agents/fix.md step 0, fixcommit.PATH_RE) applies it; `$`
#   there also matches before one final line break.
# - The text writes `<file>` unquoted after `--`. Every name reaching that line
#   has passed the pattern (no space, tab, line break inside, `*`, `?` or `[`),
#   so quoting it cannot change how the shell splits or expands it.
# - The blob is what `$(...)` keeps of git's output: trailing line breaks
#   dropped, nothing else.
#
# Usage: sh finalize_step1_2141.sh <file> <blob-out>
#   exit 0  the file is fingerprinted; its blob is written to <blob-out>
#   exit 1  the file is left out of the fingerprint map
# Needs `python3` and `git` on PATH and GUARD_PY naming guard.py. Every
# expansion is quoted; nothing derived from the file name is run as code.
# test_finalize_parity_grid.py pins each command line below to the dd8e4ab
# text, so this file cannot drift from 2.14.1 unnoticed.

f=$1
out=$2
python3 -c 'import re, sys; sys.exit(0 if re.match(r"^[A-Za-z0-9._/-]+$", sys.argv[1]) else 1)' "$f" || exit 1
python3 "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "$f" || exit 1
blob=$(git rev-parse "HEAD:$f") || exit 1
git diff --quiet HEAD -- "$f" || exit 1
git diff --cached --quiet -- "$f" || exit 1
printf '%s' "$blob" > "$out"
