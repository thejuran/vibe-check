"""Read-only replica of the orchestrator harness's semgrep half, with the
coverage evidence the harness discards.

The orchestrator's security harness (julian-orchestrator 0.11.1,
scripts/security-scan.sh) scans a phase range with semgrep but records a
degraded run as a bare status token. This tool reproduces the same scan and
writes an evidence file that proves what was scanned:

  * target selection: `git diff -z --name-only --diff-filter=d <base> <head> --`
    (changed files in base..head that exist at head, NUL-delimited);
  * materialization: every target's head blob via `git cat-file blob
    <head>:<path>` into a fresh scratch directory, each write containment
    checked. The working tree is never read and never written;
  * the FIXED argv `semgrep scan --json --config auto -- <paths>`, run with
    cwd = the scratch directory, an argv list and a timeout;
  * the harness's `errors[]` classification (FATAL_ERROR_KINDS and the
    benign parse kinds below, copied from `_sast_error_reason`).

The evidence records `semgrep --version`, the exit code, `errors[]`, the
fatal subset, the scanned count against the intended count, the missing
paths and the result count. `--config auto` fetches its rules live from the
semgrep registry, so the rule set is not pinned; the evidence says so with
`rules_pinned: false`.

Verdict: `ran` only when the exit code is 0 or 1, no error is fatal, and
every intended file was scanned with at least one intended file. Anything
else is `degraded:<reason>` and the CLI exits 1.

The release security gate runs this tool on the gated candidate and commits
the evidence file; a degraded verdict blocks the gate.

Known divergences from the harness:
  * an empty target list is `degraded:zero-scanned` here, where the harness
    calls it an honest clean. The release gate needs a positive proof that
    files were scanned, so "nothing to scan" cannot pass it;
  * a target path starting with `-` is refused (the run degrades with reason
    `refused`) where the harness rewrites it to `./-name`. Refusal keeps the
    argv free of anything semgrep could parse as an option;
  * the harness's 120 s budget is a parameter here (default 600 s);
  * on a timeout the exit code is recorded as 124, the harness's convention.

Exit codes: 0 ran, 1 degraded, 2 usage error.
Stdlib only (import lock: argparse, json, os, shutil, subprocess, sys,
tempfile) plus freeze_common.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from freeze_common import FreezeError, git, validate_rev  # noqa: E402

SEMGREP_TIMEOUT = 600
VERSION_TIMEOUT = 60
TIMEOUT_EXIT = 124
# The harness's fixed argv after the executable; the targets follow `--`.
SCAN_ARGV = ("scan", "--json", "--config", "auto", "--")

# Copied from julian-orchestrator 0.11.1 scripts/security-scan.sh
# `_sast_error_reason`. An error of one of these kinds (after removing
# whitespace, `_` and `-` and lowercasing the type) is fatal wherever it
# points. Re-copy when the harness version moves.
FATAL_ERROR_KINDS = ("fatalerror", "semgreperror", "ruleparseerror",
                     "ruleparsingerror", "ruleloadingerror",
                     "invalidruleschemaerror", "patternparseerror",
                     "matchingerror", "internalerror", "timeout",
                     "outofmemory", "stackoverflow", "invalidyaml",
                     "unknownlanguageerror")
# Same source: identified per-file parse diagnostics, benign at a non-fatal
# level when they name a usable path.
BENIGN_PARSE_KINDS = ("syntaxerror", "parseerror", "othersyntaxerror",
                      "otherparseerror", "lexicalerror", "partialparsing")
FATAL_LEVELS = ("fatal", "error")


def _check_target(path):
    """Refuse a target path that could escape a directory or read as an
    option: empty, NUL, absolute, a leading `-`, or an empty/`.`/`..`
    segment."""
    if not isinstance(path, str) or not path or "\0" in path:
        raise FreezeError("refused: empty or NUL-bearing target path")
    if path.startswith("/") or os.path.isabs(path):
        raise FreezeError("refused: absolute target path")
    if path.startswith("-"):
        raise FreezeError("refused: target path starts with '-'")
    if any(seg in ("", ".", "..") for seg in path.split("/")):
        raise FreezeError("refused: target path has an empty, '.' or '..' "
                          "segment")
    return path


def targets(repo, base, head):
    """The changed files in base..head that exist at head, in git's order.

    Same enumeration as the harness's `_ss_git_changed`: `-z` (no quoting),
    `--diff-filter=d` (deleted files excluded), trailing `--`. Every path is
    checked by `_check_target`; one bad path refuses the whole run rather
    than silently shrinking the intended set."""
    validate_rev(base)
    validate_rev(head)
    out = git(repo, "diff", "-z", "--name-only", "--diff-filter=d",
              base, head, "--")
    paths = []
    for raw in out.split(b"\0"):
        if not raw:
            continue
        paths.append(_check_target(raw.decode("utf-8", "surrogateescape")))
    return paths


def _contained(root, dest):
    root = os.path.realpath(root)
    real = os.path.realpath(dest)
    return real == root or real.startswith(root + os.sep)


def materialize(repo, head, paths, scratch):
    """Write each `<head>:<path>` blob to `scratch/<path>`.

    Every path is checked (and containment proven) before the first write,
    so a refused path leaves the scratch directory untouched. Files are
    created exclusively and never through a symlink."""
    validate_rev(head)
    for path in paths:
        _check_target(path)
        if not _contained(scratch, os.path.join(scratch, path)):
            raise FreezeError("refused: target path escapes the scratch dir")
    for path in paths:
        dest = os.path.join(scratch, path)
        data = git(repo, "cat-file", "blob", "%s:%s" % (head, path))
        parent = os.path.dirname(dest)
        os.makedirs(parent, exist_ok=True)
        if not _contained(scratch, parent):
            raise FreezeError("refused: target path escapes the scratch dir")
        fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                     | getattr(os, "O_NOFOLLOW", 0), 0o644)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)


def _relpath(p, scratch):
    """A semgrep path made relative to the scan root: strip the scratch
    prefix (semgrep may report absolute paths) and any `./` prefix."""
    p = str(p)
    for root in (scratch.rstrip("/"), os.path.realpath(scratch).rstrip("/")):
        if p == root:
            return ""
        if p.startswith(root + "/"):
            p = p[len(root) + 1:]
            break
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def _error_paths(error):
    """(paths, invalid) named by an error's path/file/spans/location keys,
    including the location list inside a tagged `[kind, [...]]` type."""
    paths = []
    invalid = [False]

    def collect(node):
        if isinstance(node, list):
            for child in node:
                collect(child)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key in ("path", "file"):
                    if isinstance(value, str) and value.strip():
                        paths.append(value)
                    else:
                        invalid[0] = True
                elif key in ("spans", "location"):
                    collect(value)

    collect(error)
    kind = error.get("type")
    if isinstance(kind, list) and len(kind) == 2:
        collect(kind[1])
    return paths, invalid[0]


def classify_error(error):
    """The harness's reason for one `errors[]` entry: `unparseable` (fatal
    level, code 2 or a FATAL_ERROR_KINDS kind), `unclassified-error` (an
    unknown kind or no usable path), or None (a benign parse diagnostic)."""
    if not isinstance(error, dict):
        return "unclassified-error"
    kind = error.get("type")
    kind = kind[0] if isinstance(kind, list) and kind else kind
    kind = "".join(ch for ch in kind if ch not in " \t\r\n_-").lower() \
        if isinstance(kind, str) else ""
    level = str(error.get("level", "")).lower()
    if level in FATAL_LEVELS or error.get("code") == 2 \
            or kind in FATAL_ERROR_KINDS:
        return "unparseable"
    paths, invalid = _error_paths(error)
    if kind not in BENIGN_PARSE_KINDS or not paths or invalid:
        return "unclassified-error"
    return None


def _fatal_errors(errors, results):
    """The fatal subset of `errors`. As in the harness, errors alongside no
    well-formed result mean the ruleset never applied: all are fatal."""
    if not errors:
        return []
    has_result = any(isinstance(r, dict)
                     and isinstance(r.get("check_id"), str) and r["check_id"]
                     and isinstance(r.get("path"), str) and r["path"]
                     for r in results)
    if not has_result:
        return list(errors)
    return [e for e in errors if classify_error(e) is not None]


def _version(semgrep):
    try:
        proc = subprocess.run([semgrep, "--version"], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=VERSION_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace").strip() or None


def run(scratch, paths, semgrep="semgrep", timeout=SEMGREP_TIMEOUT):
    """Run the harness argv over `paths` inside `scratch`; return the
    evidence record (see the module docstring)."""
    intended = list(paths)
    record = {"version": _version(semgrep), "exit_code": None,
              "intended_count": len(intended), "scanned_count": 0,
              "missing_paths": sorted(intended), "errors": [],
              "fatal_errors": [], "results_count": 0, "rules_pinned": False}
    argv = [semgrep, *SCAN_ARGV, *intended]
    try:
        proc = subprocess.run(argv, cwd=scratch, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        record["exit_code"] = TIMEOUT_EXIT
        record["fatal_errors"] = [{"type": "replica-timeout"}]
        return record
    except OSError:
        record["exit_code"] = 127
        record["fatal_errors"] = [{"type": "replica-semgrep-not-startable"}]
        return record
    record["exit_code"] = proc.returncode
    try:
        doc = json.loads(proc.stdout.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        doc = None
    if not isinstance(doc, dict):
        record["fatal_errors"] = [{"type": "replica-unparseable-output"}]
        return record
    errors = doc.get("errors")
    errors = [] if errors is None else errors
    if not isinstance(errors, list):
        errors = [{"type": "replica-errors-not-a-list"}]
    results = doc.get("results")
    results = results if isinstance(results, list) else []
    paths_obj = doc.get("paths") if isinstance(doc.get("paths"), dict) else {}
    scanned_raw = paths_obj.get("scanned")
    scanned_raw = scanned_raw if isinstance(scanned_raw, list) else []
    scanned = set(_relpath(p, scratch) for p in scanned_raw)
    scanned.discard("")
    record["errors"] = errors
    record["fatal_errors"] = _fatal_errors(errors, results)
    record["results_count"] = len(results)
    record["scanned_count"] = len(scanned & set(intended))
    record["missing_paths"] = sorted(set(intended) - scanned)
    return record


def verdict(record):
    """`ran` iff exit code in (0, 1), no fatal error, and every one of a
    non-empty intended set was scanned; else `degraded:<reason>`."""
    if record.get("fatal_errors"):
        return "degraded:fatal-errors"
    intended = record.get("intended_count") or 0
    scanned = record.get("scanned_count") or 0
    if intended <= 0 or scanned <= 0:
        return "degraded:zero-scanned"
    if scanned != intended or record.get("missing_paths"):
        return "degraded:coverage-gap"
    code = record.get("exit_code")
    if code not in (0, 1):
        return "degraded:exit-%s" % code
    return "ran"


def write_evidence(path, evidence):
    """Write `evidence` as sorted, indented JSON; never overwrite."""
    text = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    try:
        with open(path, "x", encoding="utf-8") as fh:
            fh.write(text)
    except FileExistsError:
        raise FreezeError("refused: evidence file already exists")


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("usage error: %s\n" % message)
        raise SystemExit(2)


def main(argv=None):
    parser = _Parser(prog="semgrep_replica.py",
                     description="Replay the harness semgrep half with "
                                 "coverage evidence.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--semgrep", default="semgrep")
    parser.add_argument("--timeout", type=int, default=SEMGREP_TIMEOUT)
    args = parser.parse_args(argv)
    if os.path.lexists(args.out):
        sys.stderr.write("usage error: evidence file already exists\n")
        return 2
    try:
        validate_rev(args.base)
        validate_rev(args.head)
        base_sha = git(args.repo, "rev-parse", "--verify",
                       args.base + "^{commit}").decode().strip()
        head_sha = git(args.repo, "rev-parse", "--verify",
                       args.head + "^{commit}").decode().strip()
    except FreezeError as exc:
        sys.stderr.write("usage error: %s\n" % exc)
        return 2
    evidence = {"candidate_sha": head_sha,
                "range": {"base": base_sha, "head": head_sha,
                          "base_arg": args.base, "head_arg": args.head},
                "argv": ["semgrep", *SCAN_ARGV, "<intended paths>"]}
    scratch = tempfile.mkdtemp(prefix="semgrep-replica-")
    try:
        try:
            paths = targets(args.repo, base_sha, head_sha)
            materialize(args.repo, head_sha, paths, scratch)
        except FreezeError as exc:
            record = {"version": None, "exit_code": None,
                      "intended_count": 0, "scanned_count": 0,
                      "missing_paths": [], "errors": [], "fatal_errors": [],
                      "results_count": 0, "rules_pinned": False,
                      "refusal": str(exc)}
            result = "degraded:refused"
        else:
            record = run(scratch, paths, semgrep=args.semgrep,
                         timeout=args.timeout)
            record["intended_paths"] = paths
            result = verdict(record)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    evidence.update(record)
    evidence["verdict"] = result
    try:
        write_evidence(args.out, evidence)
    except (FreezeError, OSError) as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 1
    print(result)
    return 0 if result == "ran" else 1


if __name__ == "__main__":
    sys.exit(main())
