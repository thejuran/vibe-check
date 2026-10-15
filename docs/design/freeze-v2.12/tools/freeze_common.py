"""Shared helpers for the v2.12 freeze kit.

Every hash this kit records comes from content: blobs read from the git
object store of a candidate commit, or bytes read from a live directory.
Version strings and mtimes never stand in for content.

Stdlib only (import lock: hashlib, json, os, re, subprocess). The kit lives
outside `plugins/`, so it never enters the plugin file set it hashes.
"""

import hashlib
import json
import os
import re
import subprocess

GIT_TIMEOUT = 120

# The exclusions score43.runtime_fingerprint applies to a live plugin copy.
EXCLUDED_DIRS = ("__pycache__", ".pytest_cache")
EXCLUDED_NAMES = (".in_use",)
EXCLUDED_SUFFIXES = (".pyc",)
EXCLUDES = (EXCLUDED_DIRS, EXCLUDED_NAMES, EXCLUDED_SUFFIXES)

HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
REV_RE = re.compile(r"^[A-Za-z0-9._/~^-]+$")
REL_PATH_RE = re.compile(r"^[A-Za-z0-9._/@ -]+$")
GIT_MODES = ("100644", "100755", "120000")


class FreezeError(Exception):
    """A freeze-kit refusal. Messages name paths and keys, never values."""


def git(repo, *argv, timeout=GIT_TIMEOUT, stdin=None):
    """Run `git -C repo <argv>`; return stdout bytes; raise FreezeError on a
    non-zero exit or a timeout."""
    try:
        proc = subprocess.run(["git", "-C", repo, *argv], input=stdin,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        raise FreezeError("git %s timed out" % argv[0])
    except OSError:
        raise FreezeError("git %s could not start" % argv[0])
    if proc.returncode != 0:
        raise FreezeError("git %s failed (exit %d)" % (argv[0], proc.returncode))
    return proc.stdout


def validate_rev(rev):
    """Refuse a revision outside [A-Za-z0-9._/~^-] or starting with '-'."""
    if not isinstance(rev, str) or not rev or not REV_RE.match(rev) \
            or rev.startswith("-"):
        raise FreezeError("refused: revision contains characters outside "
                          "[A-Za-z0-9._/~^-] or starts with '-'")
    return rev


def validate_rel(rel):
    """Refuse a relative path outside the safe character set or with a `..`
    segment, an absolute path or an empty segment."""
    if not isinstance(rel, str) or not rel or not REL_PATH_RE.match(rel) \
            or rel.startswith("/") \
            or any(seg in ("", ".", "..") for seg in rel.split("/")):
        raise FreezeError("refused: unsafe path in tree")
    return rel


def resolve_rev(repo, rev):
    """(full commit sha, tree sha) of `rev`."""
    validate_rev(rev)
    sha = git(repo, "rev-parse", "--verify", rev + "^{commit}").decode().strip()
    tree = git(repo, "rev-parse", "--verify", sha + "^{tree}").decode().strip()
    if not HEX40_RE.match(sha) or not HEX40_RE.match(tree):
        raise FreezeError("rev-parse returned an unexpected object id")
    return sha, tree


def _ls_tree(repo, rev, prefix, recursive=True):
    """[(mode, type, oid, path)] for the entries under `prefix` at `rev`."""
    validate_rev(rev)
    argv = ["ls-tree", "-z"]
    if recursive:
        argv.append("-r")
    # Without -r, `prefix/` lists the directory's entries; a bare `prefix`
    # would list the directory entry itself.
    argv += [rev, "--", prefix if recursive else prefix + "/"]
    out = git(repo, *argv)
    entries = []
    for raw in out.split(b"\0"):
        if not raw:
            continue
        meta, _, path = raw.partition(b"\t")
        parts = meta.split(b" ")
        if len(parts) != 3:
            raise FreezeError("ls-tree returned an unexpected entry")
        mode, kind, oid = (p.decode("ascii") for p in parts)
        entries.append((mode, kind, oid, path.decode("utf-8")))
    return entries


def _cat_blobs(repo, oids):
    """{oid: bytes} for every blob oid, via one `git cat-file --batch`."""
    if not oids:
        return {}
    unique = sorted(set(oids))
    out = git(repo, "cat-file", "--batch",
              stdin=("\n".join(unique) + "\n").encode("ascii"))
    blobs = {}
    pos = 0
    for _ in unique:
        nl = out.index(b"\n", pos)
        header = out[pos:nl].decode("ascii").split(" ")
        if len(header) != 3 or header[1] != "blob":
            raise FreezeError("cat-file returned a non-blob object")
        size = int(header[2])
        start = nl + 1
        blobs[header[0]] = out[start:start + size]
        pos = start + size + 1
    return blobs


def tree_files_at(repo, rev, prefix, pattern=None, recursive=True):
    """{rel: {"sha256", "mode"}} for every blob under `prefix` at `rev`,
    read from the git object store (never the working tree).

    `rel` is relative to `prefix`; a `prefix` naming a single file yields its
    basename. `pattern` (a glob, matched against the basename) narrows a
    non-recursive listing. A non-blob entry (submodule) is refused."""
    prefix = prefix.rstrip("/")
    validate_rel(prefix)
    entries = _ls_tree(repo, rev, prefix, recursive=recursive)
    matcher = glob_to_regex(pattern) if pattern else None
    picked = []
    for mode, kind, oid, path in entries:
        if path == prefix:
            rel = os.path.basename(path)
        elif path.startswith(prefix + "/"):
            rel = path[len(prefix) + 1:]
        else:
            continue
        if not recursive and kind == "tree":
            continue
        if matcher is not None and not matcher.match(os.path.basename(rel)):
            continue
        if kind != "blob" or mode not in GIT_MODES:
            raise FreezeError("refused: non-blob entry in tree: %s" % path)
        validate_rel(rel)
        picked.append((rel, mode, oid))
    blobs = _cat_blobs(repo, [oid for _, _, oid in picked])
    return {rel: {"sha256": hashlib.sha256(blobs[oid]).hexdigest(), "mode": mode}
            for rel, mode, oid in picked}


def blob_at(repo, rev, path):
    """The bytes of `path` at `rev`, or None when the path is absent."""
    validate_rel(path)
    entries = [e for e in _ls_tree(repo, rev, path, recursive=True)
               if e[3] == path]
    if not entries:
        return None
    mode, kind, oid, _ = entries[0]
    if kind != "blob":
        raise FreezeError("refused: non-blob entry in tree: %s" % path)
    return _cat_blobs(repo, [oid])[oid]


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def live_files(root, excludes=EXCLUDES):
    """{rel: sha256} for every regular file under `root`, minus the score43
    exclusions (cache dirs, the `.in_use` marker, `.pyc`). Symlinks are
    hashed by their target text, matching a git 120000 blob."""
    ex_dirs, ex_names, ex_suffixes = excludes
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in ex_dirs)
        for name in filenames:
            if name in ex_names or name.endswith(tuple(ex_suffixes)):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if os.path.islink(full):
                files[rel] = sha256_bytes(os.readlink(full).encode("utf-8"))
            elif os.path.isfile(full):
                files[rel] = sha256_file(full)
    return files


def file_sha(entry):
    """The sha256 of a file-map value: `{"sha256", "mode"}` or a bare hex."""
    return entry["sha256"] if isinstance(entry, dict) else entry


def tree_sha256_of_map(files_map):
    """sha256 over the sorted `<rel>\\0<sha256>\\n` lines of a file map.
    Deterministic; insensitive to dict order and to file modes."""
    lines = sorted("%s\0%s\n" % (rel, file_sha(v)) for rel, v in files_map.items())
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def canonical_json(obj):
    """Canonical JSON text: sorted keys, compact separators, UTF-8 kept."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def canonical_sha256(obj):
    return sha256_bytes(canonical_json(obj).encode("utf-8"))


def glob_to_regex(glob):
    """Compile a path glob: `**` spans directories, `*` and `?` stay inside
    one path segment; everything else is literal. Anchored both ends."""
    out = []
    i = 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def resolve_homes(home, codex_home):
    """(home, codex_home) with defaults filled in: `home` -> the real user
    home (`HOME` honored); `codex_home` -> `$CODEX_HOME` or `<home>/.codex`.
    None is a default, never a request to skip the user-level projection."""
    home = home or os.path.expanduser("~")
    codex_home = codex_home or os.environ.get("CODEX_HOME") \
        or os.path.join(home, ".codex")
    return home, codex_home
