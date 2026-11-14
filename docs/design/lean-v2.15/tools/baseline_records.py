"""baseline_records.py — the 2.14.1 behavioural baseline: suite, replay, manifest.

The records in `docs/design/lean-v2.15/baseline/` pin what vibe-check 2.14.1
(commit `dd8e4ab`, tag v2.14.1) does, so later changes can be compared with it:

- `steps-v2.14.1.json` — the model-run step count on the Finalize path,
  rechecked by `step_count.verify_steps` over the file list stored in the
  record itself.
- `finalize-situations-v2.14.1.json` (+ `.sha256`) — the five Finalize
  situations, rechecked by `finalize_capture.verify`.
- `footprint-v2.14.1.json` — declared bytes per mode path, rechecked by
  `path_records.verify_footprint`.
- `traces-v2.14.1.json` — loaded-file traces, rechecked by
  `path_records.verify_traces_record` (the structural check, which needs no
  private session files).
- `suite-v2.14.1.json` — the offline suite result at the 2.14.1 plugin tree:
  the verbatim pytest summary line, its counts, the runner, the Python
  version, the platform (system and release only), the commit and the
  plugin tree id.
- `replay-baseline-v2.14.1.md` and `replay-baseline-v2.14.1.no-private.md`
  (each with a `.sha256`) — the archived replay report (`replay.py
  baseline`), taken twice at the same commit.
- `MANIFEST.json` — sha256 of every file above plus the environment facts.

Replay in two conditions. The replay report depends on how many of the
owner's private recordings (gitignored transcripts) the checkout holds: the
primary checkout holds 12, a linked worktree or a CI checkout holds none. The
report is recorded once in each condition, each with its own fingerprint. The
check asks `replay.py census` how many recordings this checkout has,
re-derives the report and compares it with the fingerprint recorded for that
count. Any other count stops with `UNEXPECTED RECORDING COUNT <N> — STOPPING`.
Nothing is skipped: every checkout re-derives the replay result.

Normalisation rule for replay fingerprints: drop every line matching
`^- (HEAD|head|generated( \\(UTC\\))?): ` (the commit the report was run at and
the time it was written), then sha256 the remaining bytes. Both `.sha256`
files hold that fingerprint and a newline.

CLI:

    python3 docs/design/lean-v2.15/tools/baseline_records.py capture-replay
        --scripts-dir <dir> --out <md>
    python3 docs/design/lean-v2.15/tools/baseline_records.py suite-record
        --summary-line <text> --seconds <n> --captured <YYYY-MM-DD>
        --out <json> [--repo <root>]
    python3 docs/design/lean-v2.15/tools/baseline_records.py manifest
        --repo <root> --captured <YYYY-MM-DD> --replay-diff <text>
    python3 docs/design/lean-v2.15/tools/baseline_records.py verify
        --repo <root> [--baseline-dir <dir>] [--scripts-dir <dir>]

`replay.py` is only ever run as a subprocess (argument list, no shell, fixed
subcommands, 300-second timeout); which checkout's copy runs decides which
recordings it sees.

Exit codes: 0 ok, 1 difference (`BASELINE DIFFERS — STOPPING` and one line
per problem), 2 unusable input.
"""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import finalize_capture  # noqa: E402  (sibling tool)
import path_records  # noqa: E402  (sibling tool)
import step_count  # noqa: E402  (sibling tool)

BASELINE_COMMIT = "dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4"  # tag v2.14.1
PLUGINS_TREE = "90e0697363ee5c09bb7942a963cf670e16717c4a"
SCHEMA = 1
DEFAULT_REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
BASELINE_REL = os.path.join("docs", "design", "lean-v2.15", "baseline")
SCRIPTS_REL = os.path.join("plugins", "vibe-check", "scripts")

REPLAY_VOLATILE_RE = re.compile(rb"^- (HEAD|head|generated( \(UTC\))?): ")
REPLAY_RULE = ("drop every line matching %s (the commit the report was run at and "
               "the time it was written), then sha256 the remaining bytes"
               % REPLAY_VOLATILE_RE.pattern.decode("ascii"))
REPLAY_FILES = {12: "replay-baseline-v2.14.1.md",
                0: "replay-baseline-v2.14.1.no-private.md"}
REPLAY_TIMEOUT = 300
GIT_TIMEOUT = 60

MANIFEST_FILE = "MANIFEST.json"
SUITE_FILE = "suite-v2.14.1.json"
STEPS_FILE = "steps-v2.14.1.json"
SITUATIONS_FILE = "finalize-situations-v2.14.1.json"
FOOTPRINT_FILE = "footprint-v2.14.1.json"
TRACES_FILE = "traces-v2.14.1.json"

DIFFERS = "BASELINE DIFFERS — STOPPING"
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class UsageError(Exception):
    """Unusable input: the caller reports it and exits 2."""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(repo, *args):
    try:
        proc = subprocess.run(["git", "-C", repo] + list(args),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=GIT_TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise UsageError("cannot run git %s: %s" % (args[0], type(exc).__name__))
    if proc.returncode != 0:
        raise UsageError("git %s failed" % " ".join(args))
    return proc.stdout.decode("utf-8").strip()


def plugins_tree_at(repo, commit=BASELINE_COMMIT):
    return _git(repo, "rev-parse", "%s:plugins" % commit)


def _replay(scripts_dir, *args):
    try:
        return subprocess.run([sys.executable, "replay.py"] + list(args),
                              cwd=scripts_dir, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=REPLAY_TIMEOUT,
                              check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise UsageError("cannot run replay.py %s in %s: %s"
                         % (args[0], scripts_dir, type(exc).__name__))


# --------------------------------------------------------------------------- #
# Replay
# --------------------------------------------------------------------------- #
def normalise_replay(data):
    """The report bytes without the HEAD and generated header lines."""
    return b"".join(line for line in data.splitlines(keepends=True)
                    if not REPLAY_VOLATILE_RE.match(line))


def replay_fingerprint(data):
    return hashlib.sha256(normalise_replay(data)).hexdigest()


def recording_count(scripts_dir):
    """How many private recordings `replay.py census` sees from `scripts_dir`."""
    proc = _replay(scripts_dir, "census")
    out = proc.stdout.decode("utf-8", "replace")
    found = re.findall(r"^transcripts: (\d+)$", out, re.M)
    if proc.returncode != 0 or len(found) != 1:
        raise UsageError("replay.py census in %s gave no single transcripts line "
                         "(exit %d)" % (scripts_dir, proc.returncode))
    return int(found[0])


def expected_replay_file(count):
    if count not in REPLAY_FILES:
        raise UsageError("UNEXPECTED RECORDING COUNT %d — STOPPING" % count)
    return REPLAY_FILES[count]


def _run_baseline(scripts_dir, out_path):
    proc = _replay(scripts_dir, "baseline", "--out", out_path)
    if proc.returncode != 0 or not os.path.isfile(out_path):
        raise UsageError("replay.py baseline in %s exited %d"
                         % (scripts_dir, proc.returncode))
    with open(out_path, "rb") as fh:
        return fh.read()


def capture_replay(scripts_dir, out_path):
    """Write the replay report to `out_path`; return its count and fingerprint."""
    count = recording_count(scripts_dir)
    data = _run_baseline(scripts_dir, os.path.abspath(out_path))
    return {"transcripts": count, "sha256": replay_fingerprint(data),
            "rule": REPLAY_RULE}


def _read_sidecar(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().strip()


def verify_replay(repo, baseline_dir, scripts_dir=None):
    """Problems with the two replay records; [] when both hold.

    Always: each committed report's fingerprint equals its `.sha256`. Then the
    report is re-derived for this checkout's recording count and compared with
    the fingerprint recorded for that count."""
    scripts_dir = scripts_dir or os.path.join(repo, SCRIPTS_REL)
    problems = []
    for name in REPLAY_FILES.values():
        path = os.path.join(baseline_dir, name)
        try:
            with open(path, "rb") as fh:
                data = fh.read()
            recorded = _read_sidecar(path + ".sha256")
        except OSError as exc:
            problems.append("%s: report or %s.sha256 unreadable (%s)"
                            % (name, name, type(exc).__name__))
            continue
        if replay_fingerprint(data) != recorded:
            problems.append("%s: the committed report's fingerprint does not match "
                            "%s.sha256" % (name, name))
    try:
        count = recording_count(scripts_dir)
        name = expected_replay_file(count)
    except UsageError as exc:
        return problems + ["replay: %s" % exc]
    sidecar = os.path.join(baseline_dir, name + ".sha256")
    if not os.path.isfile(sidecar):
        return problems
    tmp = tempfile.mkdtemp(prefix="baseline-records-replay-")
    try:
        try:
            data = _run_baseline(scripts_dir, os.path.join(tmp, "replay.md"))
        except UsageError as exc:
            return problems + ["%s: %s" % (name, exc)]
        if replay_fingerprint(data) != _read_sidecar(sidecar):
            problems.append("%s: the re-derived report (transcripts: %d) differs from "
                            "the recorded fingerprint" % (name, count))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return problems


# --------------------------------------------------------------------------- #
# Suite record
# --------------------------------------------------------------------------- #
def _count(line, label):
    found = re.findall(r"(?:^|[\s,=])(\d+) %s\b" % label, line)
    return int(found[0]) if found else None


def parse_summary_line(line):
    """Counts from a pytest summary line; UsageError when no `passed` count."""
    passed = _count(line, "passed")
    if passed is None:
        raise UsageError("summary line has no passed count: %r" % line)
    return {"passed": passed,
            "failed": _count(line, "failed") or 0,
            "skipped": _count(line, "skipped") or 0,
            "errors": _count(line, "errors?") or 0,
            "subtests_passed": _count(line, "subtests passed") or 0}


def _pytest_runner():
    exe = shutil.which("pytest")
    if not exe:
        raise UsageError("pytest is not on PATH")
    proc = subprocess.run([exe, "--version"], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=GIT_TIMEOUT, check=False)
    m = re.search(r"pytest (\S+)", proc.stdout.decode("utf-8", "replace"))
    if not m:
        raise UsageError("pytest --version printed no version")
    python = None
    with open(exe, "rb") as fh:
        first = fh.readline().decode("utf-8", "replace").strip()
    interp = first[2:].strip() if first.startswith("#!") else ""
    if interp and os.path.isabs(interp) and " " not in interp and os.path.isfile(interp):
        out = subprocess.run([interp, "-c", "import platform; print(platform.python_version())"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=GIT_TIMEOUT, check=False)
        if out.returncode == 0:
            python = out.stdout.decode("ascii", "replace").strip()
    return "pytest " + m.group(1), python or platform.python_version()


def suite_record(repo, summary_line, seconds, captured):
    if not _DATE_RE.match(captured or ""):
        raise UsageError("--captured wants YYYY-MM-DD")
    record = {"summary_line": summary_line}
    record.update(parse_summary_line(summary_line))
    runner, python = _pytest_runner()
    record.update({
        "runner": runner,
        "python": python,
        "platform": "%s %s" % (platform.system(), platform.release()),
        "command": "pytest -q -p no:cacheprovider (from plugins/vibe-check/scripts)",
        "baseline_commit": BASELINE_COMMIT,
        "plugins_tree": plugins_tree_at(repo),
        "captured": captured,
        "seconds": seconds,
        "schema": SCHEMA,
    })
    return record


def verify_suite_record(repo, record):
    """Problems with a suite record; [] when it holds."""
    if not isinstance(record, dict):
        return ["record is not an object"]
    problems = []
    try:
        tree = plugins_tree_at(repo)
    except UsageError as exc:
        return ["cannot read the plugin tree at the baseline commit: %s" % exc]
    if record.get("plugins_tree") != tree or tree != PLUGINS_TREE:
        problems.append("plugins_tree %r is not the 2.14.1 plugin tree %s"
                        % (record.get("plugins_tree"), tree))
    if record.get("baseline_commit") != BASELINE_COMMIT:
        problems.append("baseline_commit is not %s" % BASELINE_COMMIT)
    if record.get("failed") != 0:
        problems.append("failed is %r, not 0" % record.get("failed"))
    passed = record.get("passed")
    if not (isinstance(passed, int) and not isinstance(passed, bool) and passed > 0):
        problems.append("passed is %r, not a positive integer" % (passed,))
    try:
        parsed = parse_summary_line(record.get("summary_line") or "")
    except UsageError as exc:
        problems.append("summary_line: %s" % exc)
    else:
        for key, value in sorted(parsed.items()):
            if record.get(key) != value:
                problems.append("summary_line says %s %d, the record says %r"
                                % (key, value, record.get(key)))
    return problems


# --------------------------------------------------------------------------- #
# Manifest
# --------------------------------------------------------------------------- #
def _record_files(baseline_dir):
    return sorted(n for n in os.listdir(baseline_dir)
                  if n != MANIFEST_FILE and os.path.isfile(os.path.join(baseline_dir, n)))


def build_manifest(baseline_dir, facts):
    return {"schema": SCHEMA,
            "baseline_commit": BASELINE_COMMIT,
            "plugins_tree": PLUGINS_TREE,
            "facts": facts,
            "files": {n: sha256_file(os.path.join(baseline_dir, n))
                      for n in _record_files(baseline_dir)}}


def write_manifest(baseline_dir, manifest):
    path = os.path.join(baseline_dir, MANIFEST_FILE)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return path


def verify_manifest(baseline_dir):
    """Problems naming each edited, added or removed record; [] when clean."""
    path = os.path.join(baseline_dir, MANIFEST_FILE)
    try:
        with open(path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, ValueError) as exc:
        return ["%s: unreadable (%s)" % (MANIFEST_FILE, type(exc).__name__)]
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, dict):
        return ["%s: no files object" % MANIFEST_FILE]
    problems = []
    for key, want in (("schema", SCHEMA), ("baseline_commit", BASELINE_COMMIT),
                      ("plugins_tree", PLUGINS_TREE)):
        if manifest.get(key) != want:
            problems.append("%s: %s is %r, not %r" % (MANIFEST_FILE, key,
                                                      manifest.get(key), want))
    present = _record_files(baseline_dir)
    for name in sorted(files):
        if name not in present:
            problems.append("%s: listed in %s but absent" % (name, MANIFEST_FILE))
        elif sha256_file(os.path.join(baseline_dir, name)) != files[name]:
            problems.append("%s: sha256 differs from %s" % (name, MANIFEST_FILE))
    for name in present:
        if name not in files:
            problems.append("%s: present but not listed in %s" % (name, MANIFEST_FILE))
    return problems


# --------------------------------------------------------------------------- #
# verify_baseline
# --------------------------------------------------------------------------- #
def _prefixed(name, lines):
    return ["%s: %s" % (name, line) for line in lines]


def _load(baseline_dir, name):
    with open(os.path.join(baseline_dir, name), encoding="utf-8") as fh:
        return json.load(fh)


def check_steps(repo, baseline_dir):
    """The step record recounted over its own stored file list."""
    return _prefixed(STEPS_FILE, step_count.verify_steps(
        repo, os.path.join(baseline_dir, STEPS_FILE)))


def check_situations(repo, baseline_dir):
    try:
        lines = finalize_capture.verify(repo, os.path.join(baseline_dir, SITUATIONS_FILE))
    except finalize_capture.UsageError as exc:
        lines = ["unusable: %s" % exc]
    return _prefixed(SITUATIONS_FILE, lines)


def check_footprint_and_traces(repo, baseline_dir):
    problems = []
    try:
        footprint = path_records.read_record(os.path.join(baseline_dir, FOOTPRINT_FILE))
    except path_records.UnusableInput as exc:
        footprint = None
        problems += _prefixed(FOOTPRINT_FILE, ["unusable: %s" % exc])
    try:
        traces = path_records.read_record(os.path.join(baseline_dir, TRACES_FILE))
    except path_records.UnusableInput as exc:
        traces = None
        problems += _prefixed(TRACES_FILE, ["unusable: %s" % exc])
    if footprint is not None:
        problems += _prefixed(FOOTPRINT_FILE, path_records.verify_footprint(repo, footprint)
                              + path_records.private_content_problems(footprint))
    if traces is not None:
        problems += _prefixed(TRACES_FILE, path_records.verify_traces_record(repo, traces))
    if footprint is not None and traces is not None:
        fp_paths = footprint.get("paths") if isinstance(footprint.get("paths"), dict) else {}
        tr_paths = traces.get("paths") if isinstance(traces.get("paths"), dict) else {}
        for mode in path_records.REQUIRED:
            fp_entry = fp_paths.get(mode) if isinstance(fp_paths.get(mode), dict) else {}
            tr_entry = tr_paths.get(mode) if isinstance(tr_paths.get(mode), dict) else {}
            rows = fp_entry.get("files") if isinstance(fp_entry.get("files"), list) else []
            listed = [r.get("path") for r in rows if isinstance(r, dict)]
            if tr_entry.get("declared") != listed:
                problems.append("%s: %s declared list differs from %s"
                                % (TRACES_FILE, mode, FOOTPRINT_FILE))
    return problems


def check_suite(repo, baseline_dir):
    try:
        record = _load(baseline_dir, SUITE_FILE)
    except (OSError, ValueError) as exc:
        return _prefixed(SUITE_FILE, ["unreadable (%s)" % type(exc).__name__])
    return _prefixed(SUITE_FILE, verify_suite_record(repo, record))


def verify_baseline(repo, baseline_dir=None, scripts_dir=None):
    """Every baseline check; [] only when all records hold."""
    repo = os.path.abspath(repo)
    baseline_dir = baseline_dir or os.path.join(repo, BASELINE_REL)
    scripts_dir = scripts_dir or os.path.join(repo, SCRIPTS_REL)
    problems = _prefixed(MANIFEST_FILE, verify_manifest(baseline_dir))
    problems += verify_replay(repo, baseline_dir, scripts_dir)
    problems += check_suite(repo, baseline_dir)
    problems += check_steps(repo, baseline_dir)
    problems += check_situations(repo, baseline_dir)
    problems += check_footprint_and_traces(repo, baseline_dir)
    return problems


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def _parser():
    ap = _Parser(prog="baseline_records.py")
    sub = ap.add_subparsers(dest="cmd", required=True, parser_class=_Parser)
    cap = sub.add_parser("capture-replay")
    cap.add_argument("--scripts-dir", required=True)
    cap.add_argument("--out", required=True)
    suite = sub.add_parser("suite-record")
    suite.add_argument("--repo", default=DEFAULT_REPO)
    suite.add_argument("--summary-line", required=True)
    suite.add_argument("--seconds", required=True, type=int)
    suite.add_argument("--captured", required=True)
    suite.add_argument("--out", required=True)
    man = sub.add_parser("manifest")
    man.add_argument("--repo", required=True)
    man.add_argument("--captured", required=True)
    man.add_argument("--replay-diff", required=True)
    ver = sub.add_parser("verify")
    ver.add_argument("--repo", required=True)
    ver.add_argument("--baseline-dir", default=None)
    ver.add_argument("--scripts-dir", default=None)
    return ap


def _cmd_capture_replay(args):
    got = capture_replay(args.scripts_dir, args.out)
    with open(args.out + ".sha256", "w", encoding="utf-8") as fh:
        fh.write(got["sha256"] + "\n")
    print("wrote %s (transcripts: %d, sha256 %s)"
          % (os.path.basename(args.out), got["transcripts"], got["sha256"]))
    return 0


def _cmd_suite_record(args):
    record = suite_record(args.repo, args.summary_line, args.seconds, args.captured)
    problems = verify_suite_record(args.repo, record)
    if problems:
        print(DIFFERS)
        for line in problems:
            print("  " + line)
        return 1
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("wrote %s (%d passed, %d failed)"
          % (os.path.basename(args.out), record["passed"], record["failed"]))
    return 0


def _cmd_manifest(args):
    if not _DATE_RE.match(args.captured):
        raise UsageError("--captured wants YYYY-MM-DD")
    baseline_dir = os.path.join(os.path.abspath(args.repo), BASELINE_REL)
    try:
        suite = _load(baseline_dir, SUITE_FILE)
    except (OSError, ValueError) as exc:
        raise UsageError("cannot read %s: %s" % (SUITE_FILE, type(exc).__name__))
    facts = {"suite_summary_line": suite.get("summary_line"),
             "suite_runner": suite.get("runner"),
             "suite_python": suite.get("python"),
             "suite_platform": suite.get("platform"),
             "transcripts_with_private": 12,
             "transcripts_without_private": 0,
             "replay_files": {str(k): v for k, v in sorted(REPLAY_FILES.items())},
             "replay_diff": args.replay_diff,
             "replay_normalisation": REPLAY_RULE,
             "captured": args.captured}
    path = write_manifest(baseline_dir, build_manifest(baseline_dir, facts))
    print("wrote %s (%d files)" % (os.path.basename(path),
                                   len(_record_files(baseline_dir))))
    return 0


def _cmd_verify(args):
    problems = verify_baseline(args.repo, args.baseline_dir, args.scripts_dir)
    if problems:
        print(DIFFERS)
        for line in problems:
            print("  " + line)
        return 1
    print("baseline holds")
    return 0


def main(argv=None):
    try:
        args = _parser().parse_args(argv)
        if args.cmd == "capture-replay":
            return _cmd_capture_replay(args)
        if args.cmd == "suite-record":
            return _cmd_suite_record(args)
        if args.cmd == "manifest":
            return _cmd_manifest(args)
        return _cmd_verify(args)
    except UsageError as exc:
        print("baseline_records: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
