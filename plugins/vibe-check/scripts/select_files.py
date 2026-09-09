"""select_files.py — the `--all` candidate-set filters: git mode + skip rules.

Phase 40 (DIET-02, second tier). This is a BEHAVIOR-PRESERVING extraction of
review.md Phase 0 mode-5 step c (the regular-files-only git mode filter) and
step d (the skip-rules matcher). The pattern table is transcribed from
templates/skip-rules.md, which stays the single source of truth: a test parses
that template's bullet lists and asserts set equality with the table below, so
the two cannot drift apart silently.

Pure-function boundary (keep-list D-08): the script does NO filesystem, git, or
shell-out I/O. `git ls-files -s -z` is run by the orchestrator and its raw bytes
arrive on stdin — either directly under `--raw` or base64-encoded inside the
JSON envelope. Import set is EXACTLY {base64, fnmatch, json, sys} (the AST
import-set test enforces this).

The mode filter is a security control, not a tidiness rule (T-40-14). Only
100644 (regular) and 100755 (executable) survive. `git ls-files` also lists
tracked symlinks (120000), and reading one could follow a link OUTSIDE the repo
and disclose local files, so the drop happens BEFORE any file content is read.
Anything else — notably a 160000 gitlink pointing at a submodule — is dropped as
non-regular rather than being treated as a file.

I/O: JSON envelope on stdin -> JSON envelope on stdout, or raw bytes in under
`--raw`. The __main__ shim fails CLOSED — unparseable stdin propagates so the
process exits non-zero and the orchestrator can refuse rather than review a set
it could not derive.
"""

import base64
import fnmatch
import json
import sys

# --------------------------------------------------------------------------- #
# git mode bits — review.md:241 (Phase 0 mode-5 step c)
# --------------------------------------------------------------------------- #
REGULAR_MODES = ("100644", "100755")  # regular file / executable — the ONLY keeps
SYMLINK_MODE = "120000"  # tracked symlink: dropped AND counted (T-40-14)

# --------------------------------------------------------------------------- #
# Skip patterns — transcribed from templates/skip-rules.md. The template is the
# canonical source; the drift-lock test asserts these sets equal its bullets.
# --------------------------------------------------------------------------- #
SKIP_GROUPS = {
    # skip-rules.md:45-52 — vendored / dependency directories. Matched as a
    # DIRECTORY SEGMENT (any path component equal to the name), not a prefix.
    "vendored": (
        "node_modules/", "vendor/", ".venv/", "dist/", "build/",
        ".next/", "__pycache__/", "target/",
    ),
    # skip-rules.md:56-59 — generated / minified output (basename globs).
    "generated": ("*.min.js", "*.min.css", "*.map", "*.snap"),
    # skip-rules.md:64-72 — lockfiles.
    "lockfiles": (
        "*.lock", "*-lock.json", "*.lockb", "package-lock.json",
        "pnpm-lock.yaml", "yarn.lock", "Cargo.lock", "go.sum", "poetry.lock",
    ),
    # skip-rules.md:76-92 — binary / image / font / archive.
    "binary": (
        "*.bin", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico", "*.pdf",
        "*.woff", "*.woff2", "*.ttf", "*.zip", "*.gz", "*.tar", "*.so",
        "*.dylib", "*.exe", "*.wasm",
    ),
    # skip-rules.md:100-106 — docs / planning, matched on the PATH SEGMENT
    # anywhere in the path (tracked paths are repo-relative, so a root-anchored
    # `docs/` rule would miss plugins/vibe-check/docs/architecture.md).
    "docs_segments": (".planning", "docs", "specs"),
    # skip-rules.md:105-111 — "top-level" means the repo ROOT only: a
    # README*/CHANGELOG* whose repo-relative path contains NO `/`. A nested
    # src/api/README.md is source-adjacent documentation and is KEPT.
    "docs_toplevel": ("README*", "CHANGELOG*"),
}

# skip-rules.md:124-127 — the allowlist override, evaluated AFTER every denylist
# group and taking precedence over all of them. These directories hold
# vibe-check's own instructional .md, which IS the program; a docs pattern must
# never silently drop them.
ALLOWLIST_SEGMENTS = ("agents", "commands", "templates", "skills")

# The docs group is the only one `--include-docs` re-includes.
_DOCS_KEYS = ("docs_segments", "docs_toplevel")


# --------------------------------------------------------------------------- #
# parse_ls_files — the git mode filter (T-40-14)
# --------------------------------------------------------------------------- #
def parse_ls_files(data):
    """Parse `git ls-files -s -z` bytes into regular paths plus drop counts.

    Record shape: `<mode> <sha> <stage>\\t<path>` with a NUL separator. The tab
    is the path delimiter, which is why the `-s -z` form is used — a path may
    contain spaces, and `-z` keeps newlines in filenames from splitting records.

    Only 100644/100755 survive. 120000 increments symlink_count; every other
    mode (e.g. a 160000 gitlink) increments non_regular_count. Both are dropped
    BEFORE any content read, so a tracked link can never contribute its
    target's bytes to the `<files>` block.
    """
    regular = []
    symlink_count = 0
    non_regular_count = 0
    for record in data.split(b"\000"):
        if not record:
            continue
        head, tab, raw_path = record.partition(b"\t")
        if not tab:
            # No path delimiter — not a `-s` record; refuse to guess.
            non_regular_count += 1
            continue
        mode = head.split(b" ", 1)[0].decode("utf-8", "replace")
        path = raw_path.decode("utf-8", "surrogateescape")
        if mode in REGULAR_MODES:
            regular.append(path)
        elif mode == SYMLINK_MODE:
            symlink_count += 1
        else:
            non_regular_count += 1
    return {
        "regular": regular,
        "symlink_count": symlink_count,
        "non_regular_count": non_regular_count,
    }


# --------------------------------------------------------------------------- #
# apply_skip_rules — the denylist groups plus the allowlist override
# --------------------------------------------------------------------------- #
def _segments(path):
    return path.split("/")


def _basename(path):
    return path.rpartition("/")[2]


def _matches_group(path, key):
    """True when `path` matches denylist group `key`."""
    segments = _segments(path)
    if key == "vendored":
        # Directory-segment match: any path component equal to the directory
        # name. A prefix match would wrongly drop `distribution/a.py`.
        names = {pattern.rstrip("/") for pattern in SKIP_GROUPS[key]}
        return any(segment in names for segment in segments[:-1])
    if key == "docs_segments":
        return any(segment in SKIP_GROUPS[key] for segment in segments[:-1])
    if key == "docs_toplevel":
        # Repo root ONLY — a repo-relative path with no `/` in it.
        if "/" in path:
            return False
        return any(fnmatch.fnmatchcase(path, pattern)
                   for pattern in SKIP_GROUPS[key])
    # generated / lockfiles / binary are basename globs.
    name = _basename(path)
    return any(fnmatch.fnmatchcase(name, pattern)
               for pattern in SKIP_GROUPS[key])


def _allowlisted(path):
    """skip-rules.md:130 — the allowlist WINS over every denylist group."""
    return any(segment in ALLOWLIST_SEGMENTS for segment in _segments(path)[:-1])


def apply_skip_rules(paths, include_docs=False):
    """-> (kept, skipped_count).

    `include_docs=True` drops ONLY the docs/planning group (the review.md
    mode-5 step a escape hatch); every other denylist group still applies. The
    allowlist override is evaluated last either way — it only ever KEEPS files,
    so it is harmless under the flag.
    """
    active = [key for key in SKIP_GROUPS
              if not (include_docs and key in _DOCS_KEYS)]
    kept = []
    for path in paths:
        if _allowlisted(path):
            kept.append(path)
            continue
        if any(_matches_group(path, key) for key in active):
            continue
        kept.append(path)
    return kept, len(paths) - len(kept)


# --------------------------------------------------------------------------- #
# Envelope
# --------------------------------------------------------------------------- #
def run(envelope):
    """{"ls_files_z": "<base64 raw bytes>", "include_docs": bool} -> selection."""
    raw = base64.b64decode(envelope.get("ls_files_z") or "")
    parsed = parse_ls_files(raw)
    kept, skipped = apply_skip_rules(
        parsed["regular"], bool(envelope.get("include_docs", False))
    )
    return {
        "review_set": sorted(kept),
        "symlink_count": parsed["symlink_count"],
        "non_regular_count": parsed["non_regular_count"],
        "skipped_count": skipped,
    }


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY I/O. Fails CLOSED on bad input.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    _args = sys.argv[1:]
    if "--raw" in _args:
        # bash pipes `git ls-files -s -z` straight in; no base64 round-trip.
        _result = run({
            "ls_files_z": base64.b64encode(sys.stdin.buffer.read()).decode(),
            "include_docs": "--include-docs" in _args,
        })
    else:
        # Do NOT wrap json.load in a swallowing try/except: an unparseable
        # stdin must propagate so the process exits NON-ZERO and the
        # orchestrator refuses rather than reviewing a set it could not derive.
        _result = run(json.load(sys.stdin))
    json.dump(_result, sys.stdout, allow_nan=False)
