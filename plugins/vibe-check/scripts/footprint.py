"""footprint.py — per-mode-path prose footprint for DIET-01.

D-09 splits the two orchestrator monoliths into a spine plus lazily-read
per-phase sub-files, so "how big is review.md" stops being a meaningful
question: what matters is how much prose each MODE PATH actually loads. A
plain diff review should not pay for the `--all` chunking phases, the finalize
mode, or the Phase-5 fix loop. `MODE_PATHS` below is the one place that
accounting lives.

D-10/D-01 discipline. The 40% reduction is a SOFT target, not a gate — the
batch checks and the catch-rate are the gates, and nothing is ever cut for the
number. The token columns here are PROXIES (bytes divided by a chars-per-token
constant) and are labelled as such in every output: the legacy 3.5 proxy and
the D-11 restatement at 2.7, since the 4.7+ tokenizer runs roughly 30% more
tokens per character. A proxy is never presented as a measurement. The real
measured figures come from `--measure` and are recorded once, with their
method, in the phase SUMMARY.

D-13 inversion. This module is OPTIONAL CONTEXT, not a gate: a missing file
degrades into the `missing` list and `run` still exits 0. Contrast
state_shape.py, which exits non-zero on any violation. A footprint number must
never be able to block a batch.

I/O: stdlib only, imports exactly {json, os, subprocess, sys}. CLI:

    python3 footprint.py [--root <plugin root>] [--rev <sha>] [--json] [--measure]
"""

import json
import os
import subprocess
import sys

# BEFORE numbers are read from THIS revision via git show, never from the
# worktree — wave-1 plans edit commands/review.md concurrently (F11).
PRE_PHASE_REV = "7a386ed"

# One place. 40-08 rewrote review-plain; 40-10 rewrote review-all, finalize and
# fix-loop; 40-11 owns deep-*.
# deep-* still carry the monolith-era lists until 40-11 lands: they list BOTH
# commands because deep-review.md makes the deep path read review.md, which is
# now the spine.
# review-plain is the UPPER BOUND of a non-`--all` review: it includes the
# first-run file (Phase 0.7) and the GSD-mode intent file (Phase 1.5), each of
# which a given plain run may skip. review-all is the same upper bound plus the
# `--all`-only files (a `--all` run never reads the Phase-1.5 intent file).
_SPINE_HEAD = [
    "commands/review.md",
    "phases/shared/00-contract.md",
    "phases/shared/01-bootstrap.md",
]
_REVIEW_ALWAYS_ON = [
    "phases/review/00-scope.md",
    "phases/review/05-state.md",
    "phases/review/06-config.md",
    "phases/review/07-first-run.md",
    "phases/review/10-triage.md",
    "phases/review/15-intent.md",
    "phases/review/20-dispatch.md",
    "phases/review/30-collect-score.md",
    "phases/review/40-render.md",
    "phases/review/45-persist.md",
]
# The `--all`-only files, in phase order. A `--all` review reads every one of
# them (0.2 and 0.3 are whole phases; the rest are nested reads).
_REVIEW_ALL_ONLY = [
    "phases/review/00-scope-all.md",
    "phases/review/02-chunk-plan.md",
    "phases/review/03-estimate-gate.md",
    "phases/review/05-state-all.md",
    "phases/review/20-dispatch-all.md",
    "phases/review/40-render-all.md",
    "phases/review/45-persist-all.md",
]
MODE_PATHS = {
    "review-plain": _SPINE_HEAD + _REVIEW_ALWAYS_ON,
    "review-all": _SPINE_HEAD + _REVIEW_ALWAYS_ON + _REVIEW_ALL_ONLY,
    "deep-plain": ["commands/deep-review.md", "commands/review.md"],
    "deep-all": ["commands/deep-review.md", "commands/review.md"],
    # Finalize runs Phase 0, 0.5 and the unconditional 0.6, then the shared
    # finalize file; it never reads the review phases after 0.6.
    "finalize": _SPINE_HEAD + [
        "phases/review/00-scope.md",
        "phases/review/05-state.md",
        "phases/review/06-config.md",
        "phases/shared/90-finalize.md",
    ],
    "fix-loop": _SPINE_HEAD + _REVIEW_ALWAYS_ON + ["phases/review/50-fix-loop.md"],
}

# Labelled proxies: the legacy constant and the D-11 restatement. Both are
# PROXIES and every renderer says so.
PROXIES = (("tokens@3.5", 3.5), ("tokens@2.7", 2.7))

# The plugin subdirectory a --root points into, used to build the git show
# path when reading from a revision.
_PLUGIN_PREFIX = "plugins/vibe-check"


def _repo_root(root):
    """The git repo containing `root` (two levels above plugins/vibe-check)."""
    return os.path.abspath(os.path.join(root, "..", ".."))


def read_content(root, rel, rev=None):
    """Read one file's bytes, from a revision or from the worktree.

    When `rev` is given the content comes from `git show <rev>:<path>` — this
    is the F11 fix, and it is why a BEFORE number can never be contaminated by
    a concurrent edit. A non-zero git exit (the file did not exist at that
    revision) returns None, and the caller records the path as missing rather
    than raising.
    """
    if rev:
        proc = subprocess.run(
            ["git", "-C", _repo_root(root), "show",
             "%s:%s/%s" % (rev, _PLUGIN_PREFIX, rel)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, check=False)
        if proc.returncode != 0:
            return None
        return proc.stdout
    try:
        with open(os.path.join(root, rel), "rb") as handle:
            return handle.read()
    except OSError:
        return None


def file_stats(root, rel, rev=None):
    """Stats for one file. `bytes` is None when the file is absent at `rev`."""
    content = read_content(root, rel, rev=rev)
    if content is None:
        row = {"path": rel, "bytes": None, "words": None}
        for name, _ in PROXIES:
            row[name] = None
        return row
    row = {
        "path": rel,
        "bytes": len(content),
        # Whitespace-separated tokens. Deliberately NOT `wc -w`, whose count is
        # LOCALE-DEPENDENT: under en_US.UTF-8 the BSD `wc` splits on a few
        # multibyte symbols (U+2260 in `off≠config`, U+2298 in the render-style
        # note), reporting review.md as 27148 and deep-review.md as 12134,
        # while `LC_ALL=C wc -w` and this function both report 27146 / 12132 —
        # a +2 drift per file that comes from the environment, not the prose.
        # Plan 40-14 transcribes these rows, so the recorded number is the one
        # that cannot move with $LC_ALL. The SUMMARY notes both figures.
        "words": len(content.split()),
    }
    for name, divisor in PROXIES:
        row[name] = int(len(content) / divisor)
    return row


def path_stats(root, mode, rev=None):
    """Summed stats for one mode path. Degrades on a missing file (D-13)."""
    if mode not in MODE_PATHS:
        raise KeyError("unknown mode path: %s" % mode)
    files = []
    missing = []
    for rel in MODE_PATHS[mode]:
        row = file_stats(root, rel, rev=rev)
        if row["bytes"] is None:
            missing.append(rel)
        else:
            files.append(row)
    stats = {
        "mode": mode,
        "rev": rev if rev else "worktree",
        "files": files,
        "bytes": sum(f["bytes"] for f in files),
        "words": sum(f["words"] for f in files),
        "missing": missing,
    }
    for name, _ in PROXIES:
        stats[name] = sum(f[name] for f in files)
    return stats


def _render_table(rows, rev_label):
    header_cells = ["mode", "files", "bytes", "words",
                    "tokens@3.5 (proxy)", "tokens@2.7 (proxy)"]
    widths = [14, 5, 9, 8, 18, 18]
    lines = ["Prose footprint per mode path @ %s" % rev_label,
             "Token columns are PROXIES (bytes / chars-per-token), not measurements.",
             ""]
    lines.append("  ".join(c.ljust(w) for c, w in zip(header_cells, widths)))
    lines.append("  ".join("-" * w for w in widths))
    for row in rows:
        cells = [row["mode"], str(len(row["files"])), str(row["bytes"]),
                 str(row["words"]), str(row["tokens@3.5"]), str(row["tokens@2.7"])]
        lines.append("  ".join(c.ljust(w) for c, w in zip(cells, widths)))
    return "\n".join(lines) + "\n"


USAGE = ("usage: footprint.py [--root <plugin root>] [--rev <sha>] [--json] "
         "[--measure]\n")


def _parse(argv):
    root = None
    rev = None
    as_json = False
    measure = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--root":
            if index + 1 >= len(argv):
                raise ValueError("--root requires a value")
            root = argv[index + 1]
            index += 2
        elif arg == "--rev":
            if index + 1 >= len(argv):
                raise ValueError("--rev requires a value")
            rev = argv[index + 1]
            index += 2
        elif arg == "--json":
            as_json = True
            index += 1
        elif arg == "--measure":
            measure = True
            index += 1
        else:
            raise ValueError("unknown argument")
    if root is None:
        root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    return root, rev, as_json, measure


def run(argv):
    """CLI shim. Exit 0 ALWAYS for the stats leg, even with missing files."""
    try:
        root, rev, as_json, measure = _parse(argv)
    except ValueError as exc:
        sys.stderr.write("%s\n%s" % (exc, USAGE))
        return 2

    if measure:
        sys.stderr.write(
            "--measure shells `claude -p` and costs money; it is assistant-run "
            "only and is never invoked by the test suite. The measured Phase-40 "
            "BEFORE figures are already recorded in the 40-05 SUMMARY; do not "
            "re-measure a number we hold.\n")
        return 0

    rows = [path_stats(root, mode, rev=rev) for mode in MODE_PATHS]
    warnings = [(r["mode"], m) for r in rows for m in r["missing"]]
    for mode, rel in warnings:
        sys.stderr.write("warning: %s lists a file absent at %s: %s\n"
                         % (mode, rev if rev else "worktree", rel))

    if as_json:
        sys.stdout.write(json.dumps({r["mode"]: r for r in rows}, indent=2) + "\n")
    else:
        sys.stdout.write(_render_table(rows, rev if rev else "worktree"))
    # Optional context never gates a batch (D-13).
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
