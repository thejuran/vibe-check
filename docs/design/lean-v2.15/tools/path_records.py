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
import hashlib
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
REFUSE_PRIVATE = "TRACES RECORD HOLDS PRIVATE CONTENT — STOPPING"
REFUSE_SELF_CHECK = "TRACES RECORD FAILS ITS OWN CHECK — STOPPING"
SESSIONS_ABSENT = "SESSION FILES NOT ON THIS MACHINE — RE-EXTRACTION NOT RUN"

OBSERVED = "observed"
NOT_OBSERVED = "declared, not observed"
GAP_NONE = "no recorded 2.14.x session for this path; nothing was run to fill it (D-09)"
PLUGIN_DIRS = ("commands", "phases", "templates", "agents", "scripts")
PRIVATE_MARKERS = ("/Users/", "/private/", "/home/", ".claude/projects")
MAX_STRING = 200
SESSION_PREFIX_LEN = 8
DEFAULT_REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "..", "..", "..", ".."))


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
                problems.append("%s: %s declared but missing from record" % (mode, _show(rel)))
        for rel in recorded:
            if rel not in rels:
                problems.append("%s: %s recorded but not declared" % (mode, _show(rel)))
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
# Loaded-file traces
# --------------------------------------------------------------------------- #

def plugin_relative(abs_path):
    """`<dir>/...` for a path inside a vibe-check plugin tree, else None.

    The plugin tree is a `vibe-check` segment followed directly, or after one
    version segment, by one of PLUGIN_DIRS. Everything before it (the private
    install location) is dropped.
    """
    if not isinstance(abs_path, str) or not abs_path.startswith("/"):
        return None
    parts = abs_path.split("/")
    for i, part in enumerate(parts):
        if part != "vibe-check":
            continue
        for j in (i + 1, i + 2):
            if j < len(parts) and parts[j] in PLUGIN_DIRS:
                rest = parts[j:]
                if len(rest) < 2 or any(p in ("", ".", "..") for p in rest):
                    return None
                return "/".join(rest)
    return None


def _is_plugin_rel(rel):
    return isinstance(rel, str) and plugin_relative("/r/vibe-check/" + rel) == rel


def _show(rel):
    """A recorded path safe to print in a problem line."""
    return rel if _is_plugin_rel(rel) else "<not a plugin-relative path>"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def session_prefix(path):
    return os.path.basename(path)[:SESSION_PREFIX_LEN]


def observed_trace(session_path, kind, version_label, repo, commit=BASELINE_COMMIT,
                   declared=None):
    """The labelled observed trace of one recorded session.

    Only plugin-relative names, counts, byte figures, the version label, the
    8-character session prefix and the file hash are kept. Read content,
    message text and any path outside the plugin never enter the result.
    """
    repo = os.path.abspath(repo)
    tc = load_plugin_module(repo, "tracecheck")
    if declared is None:
        declared = baseline_mode_paths(repo, commit)[kind]
    stem = os.path.splitext(os.path.basename(session_path))[0]
    subagents = os.path.join(os.path.dirname(session_path), stem, "subagents")
    evts = tc.events(session_path, subagents if os.path.isdir(subagents) else None)
    reads = []
    non_plugin = 0
    sizes = {}
    for _, path in tc.successful_reads(evts, main_only=True):
        rel = plugin_relative(path)
        if rel is None:
            non_plugin += 1
            continue
        if rel not in sizes:
            content = git_bytes(repo, commit, rel)
            sizes[rel] = None if content is None else len(content)
        size = sizes[rel]
        reads.append({"path": rel, "bytes_at_baseline": size,
                      "at_baseline": "absent" if size is None else "present",
                      "in_declared": rel in declared})
    tool_calls = {}
    for e in evts:
        if e[0] == "tool_use" and not e[3]["parent"]:
            name = e[2] if isinstance(e[2], str) else "?"
            tool_calls[name] = tool_calls.get(name, 0) + 1
    return {
        "label": OBSERVED,
        "kind": kind,
        "version": version_label,
        "smoke_session": "smoke session" in version_label,
        "session": session_prefix(session_path),
        "session_sha256": sha256_file(session_path),
        "reads": reads,
        "non_plugin_reads": non_plugin,
        "tool_calls": tool_calls,
        "malformed_lines": sum(1 for e in evts if e[0] == "malformed"),
    }


TRACE_NOTES = [
    "commands/review.md reaches the model by command expansion, not a Read; "
    "its absence from reads is expected",
    "reads: successful main-session Reads of plugin files, plugin-relative, in order; "
    "failed Reads are left out",
    "non_plugin_reads and tool_calls are counts only; no path outside the plugin is kept",
    "bytes_at_baseline: git show at baseline_commit, whatever version the session ran",
    "declared and observed are separate lists and are never merged",
    "smoke sessions are this project's own recorded test sessions (D-19)",
]


def traces_record(repo, commit, sessions):
    """Declared list plus labelled observed traces for each required path.

    `sessions` is a list of (kind, version label, session path). A listed
    session file that is absent is named by its prefix in the path's `gap`;
    nothing stands in for it.
    """
    repo = os.path.abspath(repo)
    commit = resolve_commit(repo, commit)
    declared_all = baseline_mode_paths(repo, commit)
    paths = {}
    for mode in REQUIRED:
        declared = list(declared_all[mode])
        observed = []
        missing = []
        for kind, version, path in sessions:
            if kind != mode:
                continue
            if not os.path.isfile(path):
                missing.append(session_prefix(path))
                continue
            observed.append(observed_trace(path, kind, version, repo, commit, declared))
        entry = {"declared": declared, "observed": observed}
        if observed:
            entry["label"] = OBSERVED
        else:
            entry["label"] = NOT_OBSERVED
            entry["gap"] = GAP_NONE
        if missing:
            entry["gap"] = ("listed session %s not on this machine; no stand-in used (D-09)"
                            % ", ".join(missing))
        paths[mode] = entry
    return {"schema": SCHEMA, "baseline_commit": commit, "notes": list(TRACE_NOTES),
            "paths": paths}


def private_content_problems(record):
    """One problem line per private-looking key or string, by JSON location.

    Flags any string holding a private path marker, any string over
    MAX_STRING characters, and any `session` value over SESSION_PREFIX_LEN
    characters. The offending text is never echoed.
    """
    problems = []

    def check(text, loc):
        if any(m in text for m in PRIVATE_MARKERS):
            problems.append("%s: private path marker" % loc)
        if len(text) > MAX_STRING:
            problems.append("%s: string longer than %d characters" % (loc, MAX_STRING))

    def walk(obj, loc):
        if isinstance(obj, dict):
            for key, value in obj.items():
                key = str(key)
                before = len(problems)
                check(key, "%s key" % (loc or "<root>"))
                shown = key if len(problems) == before else "<key>"
                child = "%s.%s" % (loc, shown) if loc else shown
                if key == "session" and isinstance(value, str) \
                        and len(value) > SESSION_PREFIX_LEN:
                    problems.append("%s: session id longer than %d characters"
                                    % (child, SESSION_PREFIX_LEN))
                walk(value, child)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, "%s[%d]" % (loc, i))
        elif isinstance(obj, str):
            check(obj, loc or "<root>")

    walk(record, "")
    return problems


def _verify_observed(repo, commit, mode, k, obs, declared, problems):
    where = "%s: observed[%d]" % (mode, k)
    if not isinstance(obs, dict):
        problems.append("%s is not an object" % where)
        return
    if obs.get("label") != OBSERVED:
        problems.append("%s label is not %r" % (where, OBSERVED))
    if obs.get("kind") != mode:
        problems.append("%s kind is not %r" % (where, mode))
    if not isinstance(obs.get("version"), str) or not obs["version"].strip():
        problems.append("%s has no version label" % where)
    sha = obs.get("session_sha256")
    if not (isinstance(sha, str) and len(sha) == 64
            and all(c in "0123456789abcdef" for c in sha)):
        problems.append("%s session_sha256 missing or not 64-hex" % where)
    if not isinstance(obs.get("session"), str) or len(obs["session"]) != SESSION_PREFIX_LEN:
        problems.append("%s session is not an %d-character prefix"
                        % (where, SESSION_PREFIX_LEN))
    if not isinstance(obs.get("smoke_session"), bool):
        problems.append("%s smoke_session is not true/false" % where)
    reads = obs.get("reads")
    if not isinstance(reads, list):
        problems.append("%s has no reads list" % where)
        return
    for i, row in enumerate(reads):
        rel = row.get("path") if isinstance(row, dict) else None
        if not _is_plugin_rel(rel):
            problems.append("%s read %d is not a plugin-relative path" % (where, i))
            continue
        content = git_bytes(repo, commit, rel)
        if content is None:
            if row.get("bytes_at_baseline") is not None or row.get("at_baseline") != "absent":
                problems.append("%s: %s absent at baseline but recorded with bytes"
                                % (mode, rel))
        elif row.get("bytes_at_baseline") != len(content) \
                or row.get("at_baseline") != "present":
            problems.append("%s: %s bytes_at_baseline recorded %r, git %d"
                            % (mode, rel, row.get("bytes_at_baseline"), len(content)))
        if row.get("in_declared") is not (rel in declared):
            problems.append("%s: %s in_declared is wrong" % (mode, rel))


def verify_traces_record(repo, record):
    """Problem lines for a traces record; [] when it holds."""
    repo = os.path.abspath(repo)
    if not isinstance(record, dict) or not isinstance(record.get("paths"), dict):
        return ["traces record has no paths block"]
    commit = record.get("baseline_commit")
    if not isinstance(commit, str):
        return ["traces record has no baseline_commit"]
    try:
        commit = resolve_commit(repo, commit)
        declared_all = baseline_mode_paths(repo, commit)
    except UnusableInput as exc:
        return ["traces record: %s" % exc]
    problems = []
    paths = record["paths"]
    if set(paths) - set(REQUIRED):
        problems.append("traces record holds a path outside %s" % ", ".join(REQUIRED))
    for mode in REQUIRED:
        entry = paths.get(mode)
        if not isinstance(entry, dict):
            problems.append("%s: path missing from traces record" % mode)
            continue
        declared = declared_all[mode]
        if entry.get("declared") != declared:
            problems.append("%s: declared list differs from MODE_PATHS at baseline "
                            "(observed reads merged in?)" % mode)
        observed = entry.get("observed")
        if not isinstance(observed, list):
            problems.append("%s: observed is not a list" % mode)
            continue
        label = entry.get("label")
        if observed and label != OBSERVED:
            problems.append("%s: path label is %r but observed entries are present"
                            % (mode, label))
        if not observed:
            if label != NOT_OBSERVED:
                problems.append("%s: path label is not %r with no observed entry"
                                % (mode, NOT_OBSERVED))
            gap = entry.get("gap")
            if not isinstance(gap, str) or not gap.strip():
                problems.append("%s: declared, not observed without a gap sentence" % mode)
        for k, obs in enumerate(observed):
            _verify_observed(repo, commit, mode, k, obs, declared, problems)
    return problems + private_content_problems(record)


def parse_session(arg):
    """`<kind>=<version label>=<path>` → (kind, version, path)."""
    if not isinstance(arg, str) or arg.count("=") < 2:
        raise UnusableInput("--session wants <kind>=<version label>=<path>")
    kind, rest = arg.split("=", 1)
    version, path = rest.rsplit("=", 1)
    if kind not in REQUIRED:
        raise UnusableInput("--session kind must be one of %s" % ", ".join(REQUIRED))
    if not version.strip() or not path:
        raise UnusableInput("--session wants a version label and a path")
    return kind, version, os.path.expanduser(path)


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
    sys.stdout.write("wrote %s\n" % os.path.basename(args.out))
    return 0



def _cmd_traces(args):
    sessions = [parse_session(a) for a in args.session]
    record = traces_record(args.repo, args.commit, sessions)
    private = private_content_problems(record)
    if private:
        sys.stderr.write("%s\n%s\n" % (REFUSE_PRIVATE, "\n".join(private)))
        return 1
    problems = verify_traces_record(args.repo, record)
    if problems:
        sys.stderr.write("%s\n%s\n" % (REFUSE_SELF_CHECK, "\n".join(problems)))
        return 1
    write_record(args.out, record)
    sys.stdout.write("wrote %s\n" % os.path.basename(args.out))
    return 0


def _cmd_verify(args):
    footprint = read_record(args.footprint)
    traces = read_record(args.traces)
    problems = verify_footprint(args.repo, footprint)
    problems += private_content_problems(footprint)
    problems += verify_traces_record(args.repo, traces)
    fp_paths = footprint.get("paths") if isinstance(footprint.get("paths"), dict) else {}
    tr_paths = traces.get("paths") if isinstance(traces.get("paths"), dict) else {}
    for mode in REQUIRED:
        fp_entry = fp_paths.get(mode) if isinstance(fp_paths.get(mode), dict) else {}
        tr_entry = tr_paths.get(mode) if isinstance(tr_paths.get(mode), dict) else {}
        rows = fp_entry.get("files") if isinstance(fp_entry.get("files"), list) else []
        listed = [r.get("path") for r in rows if isinstance(r, dict)]
        if tr_entry.get("declared") != listed:
            problems.append("%s: traces declared list differs from the footprint record"
                            % mode)
    for line in problems:
        sys.stdout.write(line + "\n")
    sys.stdout.write("%s\n" % ("records hold" if not problems
                               else "%d problem(s)" % len(problems)))
    return 1 if problems else 0


def _cmd_verify_traces(args):
    sessions = [parse_session(a) for a in args.session]
    absent = [session_prefix(p) for _, _, p in sessions if not os.path.isfile(p)]
    if absent:
        sys.stderr.write("%s (%s)\n" % (SESSIONS_ABSENT, ", ".join(absent)))
        return 2
    record = read_record(args.traces)
    repo = os.path.abspath(args.repo)
    commit = record.get("baseline_commit")
    if not isinstance(commit, str) or not isinstance(record.get("paths"), dict):
        raise UnusableInput("traces record has no baseline_commit or paths block")
    recorded = {}
    for mode, entry in record["paths"].items():
        for obs in (entry.get("observed") or []) if isinstance(entry, dict) else []:
            if isinstance(obs, dict):
                recorded[(mode, obs.get("session"))] = obs
    problems = []
    seen = set()
    for kind, version, path in sessions:
        key = (kind, session_prefix(path))
        seen.add(key)
        fresh = observed_trace(path, kind, version, repo, commit)
        if key not in recorded:
            problems.append("session %s (%s): not in the record" % (key[1], kind))
        elif recorded[key] != fresh:
            diff = sorted(k for k in set(fresh) | set(recorded[key])
                          if fresh.get(k) != recorded[key].get(k))
            problems.append("session %s (%s): re-extracted trace differs in %s"
                            % (key[1], kind, ", ".join(diff)))
    for key in sorted(set(recorded) - seen, key=str):
        problems.append("session %s (%s): in the record but not re-extracted"
                        % (key[1], key[0]))
    for line in problems:
        sys.stderr.write(line + "\n")
    if not problems:
        sys.stdout.write("re-extracted %d session(s); record holds\n" % len(sessions))
    return 1 if problems else 0

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
    tr = sub.add_parser("traces")
    tr.add_argument("--repo", required=True)
    tr.add_argument("--out", required=True)
    tr.add_argument("--commit", default=BASELINE_COMMIT)
    tr.add_argument("--session", action="append", default=[])
    ve = sub.add_parser("verify")
    ve.add_argument("--repo", required=True)
    ve.add_argument("--footprint", required=True)
    ve.add_argument("--traces", required=True)
    vt = sub.add_parser("verify-traces")
    vt.add_argument("--repo", default=DEFAULT_REPO)
    vt.add_argument("--traces", required=True)
    vt.add_argument("--session", action="append", default=[], required=True)
    return parser


def run(argv):
    try:
        args = _parser().parse_args(argv)
    except _ArgError as exc:
        sys.stderr.write("%s\n" % exc)
        return 2
    handlers = {"footprint": _cmd_footprint, "traces": _cmd_traces,
                "verify": _cmd_verify, "verify-traces": _cmd_verify_traces}
    try:
        return handlers[args.command](args)
    except UnusableInput as exc:
        sys.stderr.write("%s\n" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
