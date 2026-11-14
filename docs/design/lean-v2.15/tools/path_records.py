"""path_records.py — declared mode-path bytes and loaded-file traces at 2.14.1.

The footprint record lists, for every mode path in footprint.py's MODE_PATHS,
each file the path declares with its bytes and whitespace-split words at the
pinned commit, plus per-path totals. Token figures are derived from bytes and
are PROXIES: they live only in the record's `proxies` block, never beside the
byte counts, and no price is ever written.

Standing check versus capture check. The committed record stores each file's
path and bytes, and `verify` recounts those bytes straight from
`git show <commit>:plugins/vibe-check/<path>`; the declared file lists come from
footprint.py as it stood AT the pinned commit (read with `git show`), so the
standing check stays valid when a later change edits footprint.py. Agreement
with the live `footprint.path_stats(rev=<commit>)` is enforced once, at
capture: `footprint` refuses to write a record that disagrees with it.

CLI:

    python3 docs/design/lean-v2.15/tools/path_records.py footprint --repo <root> --out <json>
    python3 docs/design/lean-v2.15/tools/path_records.py traces --repo <root> --out <json> \\
        --session <kind>=<version label>=<path> ...
    python3 docs/design/lean-v2.15/tools/path_records.py verify --repo <root> \\
        --footprint <json> --traces <json>
    python3 docs/design/lean-v2.15/tools/path_records.py verify-traces --traces <json> \\
        --session <kind>=<version label>=<path> ...

`--commit <sha>` overrides the pinned commit for `footprint` and `traces`.

Exit codes: 0 ok; 1 a difference or a refusal; 2 unusable input (unknown
commit, unreadable record, missing session file, bad arguments).

Stdlib only.
"""

import argparse
import json
import os
import subprocess
import sys

BASELINE_COMMIT = "dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4"  # tag v2.14.1
SCHEMA = 1
REQUIRED = {"review-plain": "plain review", "deep-plain": "deep review",
            "finalize": "Finalize"}
PROXY_LABEL = "PROXY — derived from bytes, not measured, not a bill"
PLUGIN_PREFIX = "plugins/vibe-check"
SCRIPTS_REL = os.path.join("plugins", "vibe-check", "scripts")

REFUSE_RECOUNT = "FOOTPRINT RECOUNT DISAGREES WITH footprint.py — STOPPING"


class UnusableInput(Exception):
    """Input the tool cannot work from (exit 2)."""


class Refusal(Exception):
    """A capture that would write a wrong record (exit 1)."""


# --------------------------------------------------------------------------- #
# Plugin modules and git
# --------------------------------------------------------------------------- #

def load_plugin_module(repo, name):
    """Import footprint or tracecheck from <repo>/plugins/vibe-check/scripts."""
    scripts = os.path.join(os.path.abspath(repo), SCRIPTS_REL)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    if name == "footprint":
        import footprint
        return footprint
    if name == "tracecheck":
        import tracecheck
        return tracecheck
    raise KeyError(name)


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=30, check=False)


def resolve_commit(repo, commit):
    """Full sha of `commit`, or UnusableInput when git does not know it."""
    proc = _git(repo, "rev-parse", "--verify", "--quiet", "%s^{commit}" % commit)
    if proc.returncode != 0:
        raise UnusableInput("unknown commit: %s" % commit)
    return proc.stdout.decode("ascii").strip()


def git_bytes(repo, commit, rel):
    """The plugin file `rel` at `commit`, or None when it is absent there."""
    proc = _git(repo, "show", "%s:%s/%s" % (commit, PLUGIN_PREFIX, rel))
    if proc.returncode != 0:
        return None
    return proc.stdout


def baseline_mode_paths(repo, commit):
    """MODE_PATHS as footprint.py defined it AT `commit`.

    The module source is read from this repository's own history with
    `git show` and evaluated with a non-main `__name__`, so its CLI does not
    run. Reading it from the commit keeps the standing check independent of
    later edits to footprint.py.
    """
    proc = _git(repo, "show", "%s:%s/scripts/footprint.py" % (commit, PLUGIN_PREFIX))
    if proc.returncode != 0:
        raise UnusableInput("footprint.py absent at %s" % commit)
    namespace = {"__name__": "footprint_at_commit"}
    exec(compile(proc.stdout.decode("utf-8"), "footprint.py@%s" % commit[:12], "exec"),
         namespace)
    paths = namespace.get("MODE_PATHS")
    if not isinstance(paths, dict):
        raise UnusableInput("footprint.py at %s has no MODE_PATHS" % commit)
    return {mode: list(files) for mode, files in paths.items()}


# --------------------------------------------------------------------------- #
# Footprint record
# --------------------------------------------------------------------------- #

def _file_row(repo, commit, rel):
    content = git_bytes(repo, commit, rel)
    if content is None:
        return None
    return {"path": rel, "bytes": len(content),
            "words": len(content.decode("utf-8", errors="replace").split())}


def footprint_record(repo, commit=BASELINE_COMMIT):
    """The declared byte record for every mode path at `commit`.

    Raises UnusableInput for an unknown commit or a declared file absent at
    it, and Refusal when the live footprint.path_stats disagrees on any file
    or total.
    """
    repo = os.path.abspath(repo)
    commit = resolve_commit(repo, commit)
    fp = load_plugin_module(repo, "footprint")
    plugin_root = os.path.join(repo, PLUGIN_PREFIX)
    declared = baseline_mode_paths(repo, commit)
    word_note = ("words: whitespace-split count of the UTF-8 decoded text; "
                 "agrees with footprint.py for every file")
    paths = {}
    proxies = {}
    word_mismatch = False
    for mode, rels in declared.items():
        rows = []
        for rel in rels:
            row = _file_row(repo, commit, rel)
            if row is None:
                raise UnusableInput("%s: %s absent at %s" % (mode, rel, commit))
            rows.append(row)
        stats = fp.path_stats(plugin_root, mode, rev=commit)
        fp_rows = {r["path"]: r for r in stats["files"]}
        problems = []
        if stats["missing"] or [r["path"] for r in stats["files"]] != rels:
            problems.append("%s: file list differs" % mode)
        for row in rows:
            other = fp_rows.get(row["path"])
            if other is None or other["bytes"] != row["bytes"]:
                problems.append("%s: %s bytes" % (mode, row["path"]))
                continue
            if other["words"] != row["words"]:
                # Keep footprint.py's figure under its own name; say so in `source`.
                word_mismatch = True
                row["words_text_split"] = row["words"]
                row["words"] = other["words"]
        if stats["bytes"] != sum(r["bytes"] for r in rows):
            problems.append("%s: total bytes" % mode)
        if problems:
            raise Refusal("; ".join(problems))
        entry = {"files": rows, "file_count": len(rows),
                 "total_bytes": sum(r["bytes"] for r in rows),
                 "total_words": sum(r["words"] for r in rows)}
        if mode in REQUIRED:
            entry["label"] = REQUIRED[mode]
        paths[mode] = entry
        proxies[mode] = {name: int(entry["total_bytes"] / divisor)
                         for name, divisor in fp.PROXIES}
    if word_mismatch:
        word_note = ("words: footprint.py's bytes-split figure; words_text_split "
                     "is the UTF-8 decoded split where the two differ")
    return {
        "schema": SCHEMA,
        "baseline_commit": commit,
        "source": [
            "bytes and files: git show <baseline_commit>:plugins/vibe-check/<path>",
            "file lists: MODE_PATHS in scripts/footprint.py at baseline_commit",
            word_note,
            "capture checked against footprint.path_stats(rev=baseline_commit)",
        ],
        "paths": paths,
        "proxies": {"label": PROXY_LABEL,
                    "rule": "total_bytes divided by chars-per-token, rounded down",
                    "modes": proxies},
    }


def verify_footprint(repo, record):
    """Problem lines for a footprint record recounted from git; [] when it holds."""
    repo = os.path.abspath(repo)
    problems = []
    commit = record.get("baseline_commit") if isinstance(record, dict) else None
    if not isinstance(commit, str):
        return ["footprint record has no baseline_commit"]
    try:
        commit = resolve_commit(repo, commit)
        declared = baseline_mode_paths(repo, commit)
    except UnusableInput as exc:
        return ["footprint record: %s" % exc]
    paths = record.get("paths")
    if not isinstance(paths, dict):
        return ["footprint record has no paths block"]
    if "token" in json.dumps(paths):
        problems.append("paths block holds a token figure; proxies belong under proxies")
    proxies = record.get("proxies")
    if not isinstance(proxies, dict) or proxies.get("label") != PROXY_LABEL:
        problems.append("proxies block missing or not labelled PROXY")
    if "$" in json.dumps(record):
        problems.append("footprint record holds a price figure")
    for mode in sorted(set(paths) - set(declared)):
        problems.append("%s: mode not declared at %s" % (mode, commit[:12]))
    for mode, rels in declared.items():
        entry = paths.get(mode)
        if not isinstance(entry, dict) or not isinstance(entry.get("files"), list):
            problems.append("%s: mode missing from record" % mode)
            continue
        if mode in REQUIRED and entry.get("label") != REQUIRED[mode]:
            problems.append("%s: label is not %r" % (mode, REQUIRED[mode]))
        rows = [r for r in entry["files"] if isinstance(r, dict)]
        recorded = [r.get("path") for r in rows]
        for rel in rels:
            if rel not in recorded:
                problems.append("%s: %s declared but missing from record" % (mode, rel))
        for rel in recorded:
            if rel not in rels:
                problems.append("%s: %s recorded but not declared" % (mode, rel))
        if [r for r in recorded if r in rels] != [r for r in rels if r in recorded]:
            problems.append("%s: file order differs from MODE_PATHS" % mode)
        for row in rows:
            rel = row.get("path")
            if rel not in rels:
                continue
            content = git_bytes(repo, commit, rel)
            if content is None:
                problems.append("%s: %s absent at %s" % (mode, rel, commit[:12]))
                continue
            if row.get("bytes") != len(content):
                problems.append("%s: %s bytes recorded %r, git %d"
                                % (mode, rel, row.get("bytes"), len(content)))
            words = len(content.split())
            if row.get("words") != words:
                problems.append("%s: %s words recorded %r, git %d"
                                % (mode, rel, row.get("words"), words))
        byte_sum = sum(r.get("bytes") for r in rows if isinstance(r.get("bytes"), int))
        word_sum = sum(r.get("words") for r in rows if isinstance(r.get("words"), int))
        if entry.get("total_bytes") != byte_sum:
            problems.append("%s: total_bytes recorded %r, files sum to %d"
                            % (mode, entry.get("total_bytes"), byte_sum))
        if entry.get("total_words") != word_sum:
            problems.append("%s: total_words recorded %r, files sum to %d"
                            % (mode, entry.get("total_words"), word_sum))
        if entry.get("file_count") != len(rows):
            problems.append("%s: file_count recorded %r, %d files listed"
                            % (mode, entry.get("file_count"), len(rows)))
    return problems


# --------------------------------------------------------------------------- #
# I/O and CLI
# --------------------------------------------------------------------------- #

def write_record(path, record):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def read_record(path):
    try:
        with open(path, encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError) as exc:
        raise UnusableInput("unreadable record %s: %s" % (os.path.basename(path),
                                                         type(exc).__name__))
    if not isinstance(record, dict):
        raise UnusableInput("record %s is not an object" % os.path.basename(path))
    return record


def _cmd_footprint(args):
    try:
        record = footprint_record(args.repo, args.commit)
    except Refusal as exc:
        sys.stderr.write("%s\n%s\n" % (REFUSE_RECOUNT, exc))
        return 1
    write_record(args.out, record)
    sys.stdout.write("wrote %s\n" % args.out)
    return 0


class _ArgError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    """Argument errors become exit 2 through run(), never SystemExit."""

    def error(self, message):
        raise _ArgError(message)


def _parser():
    parser = _Parser(prog="path_records.py")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    fp = sub.add_parser("footprint")
    fp.add_argument("--repo", required=True)
    fp.add_argument("--out", required=True)
    fp.add_argument("--commit", default=BASELINE_COMMIT)
    return parser


def run(argv):
    try:
        args = _parser().parse_args(argv)
    except _ArgError as exc:
        sys.stderr.write("%s\n" % exc)
        return 2
    handlers = {"footprint": _cmd_footprint}
    try:
        return handlers[args.command](args)
    except UnusableInput as exc:
        sys.stderr.write("%s\n" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
