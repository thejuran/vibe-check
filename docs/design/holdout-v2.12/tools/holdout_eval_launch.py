"""holdout_eval_launch.py — the holdout MEASUREMENT launcher.

Every holdout evaluation run (detection and accepted-fix) starts here. The
owner runs it from a plain Terminal (README section 10); the assistant never
drives it, and it refuses in a Claude-spawned shell exactly like the
autopilot.

  holdout_eval_launch.py eval-launch --run-dir <new dir> --case <case folder>
                                     [--candidate C] [--manifest M]
                                     [--model MODEL]

Before EVERY launch, retries included, it:

  1. loads the active freeze manifest (no manifest, no run);
  2. builds a disposable copy of plugins/vibe-check and the measured runner
     settings from the candidate commit's git objects, never the working tree
     (<run dir>/frozen-build/);
  3. runs the freeze identity check (runner profile `holdout-eval`) on that
     copy, those settings, the launch model and the exact environment the
     session will get;
  4. on any difference prints each one and `IDENTITY MISMATCH — STOPPING`,
     exits 1 and launches nothing. There is no override;
  5. writes <run dir>/identity.json (manifest_id, check_digest, candidate_sha,
     case_id, run_name: the eligibility record freeze_policy.read_record
     reads) and refuses to overwrite one: a retry is a NEW run dir;
  6. replaces itself with the session (LAUNCH_ARGV), working directory the
     run dir.

The case folder is an opaque argument. Its basename is the case's opaque id
(H-<8 hex>); nothing under it is read, listed or hashed here, and it reaches
the session only as an `--add-dir` value.

Exit codes: 0 launched, 1 refused or identity stop, 2 usage.
"""

import argparse
import json
import os
import re
import sys
import time

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import holdout_kit  # noqa: E402
import holdout_autopilot  # noqa: E402  (puts the freeze kit on sys.path)

try:
    import freeze_check  # noqa: E402
    import freeze_common  # noqa: E402
except ModuleNotFoundError as _exc:
    if _exc.name not in ("freeze_check", "freeze_common"):
        raise
    freeze_check = freeze_common = None

KitError = holdout_kit.KitError

# ---------------------------------------------------------------- constants

RUNNER = "holdout-eval"
REPO_ROOT = holdout_autopilot.REPO_ROOT
IDENTITY_STOP = "IDENTITY MISMATCH — STOPPING"
IDENTITY_NAME = "identity.json"
BUILD_DIRNAME = "frozen-build"
PLUGIN_REL = "plugins/vibe-check"
# The measured runner settings and their status-line script, read from the
# candidate commit (the freeze manifest pins the same two files).
RUNNER_TEMPLATE = "docs/design/b3-ground-truth/b3-runner-v2.12/settings-measured.json"
RUNNER_STATUSLINE = "docs/design/b3-ground-truth/b3-runner-v2.12/statusline-capture.sh"
RUNNER_PLACEHOLDER = "<RUNNER>"
SETTINGS_NAME = "settings-measured.json"
STATUSLINE_NAME = "statusline-capture.sh"
FILE_MODES = {"100644": 0o644, "100755": 0o755}

# Reused from the autopilot so both holdout runners share one rule set.
STRIPPED_ENV = holdout_autopilot.STRIPPED_ENV
FORBIDDEN_ARGS = holdout_autopilot.FORBIDDEN_ARGS
# The update pins (DISABLE_AUTOUPDATER / DISABLE_UPDATES) are NOT added to the
# process env: the materialized runner settings pin them in their `env`, as
# for B3 and the fix harness. The identity check holds the process env to the
# manifest's baseline, taken from the generating shell.

# The session argv; every {field} is filled by build_argv and the result is
# validated by the autopilot's check_argv (no forbidden flag, exactly one
# `--permission-mode dontAsk`, exactly one session identity).
LAUNCH_ARGV = ("claude",
               "--plugin-dir", "{plugin_dir}",
               "--settings", "{settings_path}",
               "--model", "{model}",
               "--add-dir", "{case}",
               "--permission-mode", "dontAsk",
               "--session-id", "{session_id}")

CASE_ID_RE = holdout_kit.ID_RE
RUN_NAME_RE = re.compile(r"^run-[0-9]+$")

FREEZE_KIT_MISSING_MSG = ("the freeze kit was not found; run this from the "
                          "tuning repo checkout")
NO_MANIFEST_MSG = "no active freeze manifest — STOPPING"
CASE_ID_MSG = ("--case must name a case folder whose name is its opaque id "
               "(H-<8 hex>)")
RUN_NAME_MSG = "--run-dir must be a directory named run-<n>"
IDENTITY_EXISTS_MSG = ("%s already holds identity.json; every launch, retries "
                       "included, needs a NEW run dir")
SETTINGS_PAIR_MSG = "a supplied plugin dir needs its runner settings path"


# ---------------------------------------------------------------- pieces


def _freeze():
    if freeze_check is None or freeze_common is None:
        raise KitError(FREEZE_KIT_MISSING_MSG)
    return freeze_check, freeze_common


def slot_identity(case_arg, run_dir):
    """(case_id, run_name) from the two path names alone; KitError when
    either is not a slot identity. Nothing under `case_arg` is touched."""
    if not isinstance(case_arg, str) or not case_arg \
            or case_arg.startswith("-"):
        raise KitError(CASE_ID_MSG)
    case_id = os.path.basename(case_arg.rstrip("/"))
    if not CASE_ID_RE.match(case_id):
        raise KitError(CASE_ID_MSG)
    run_name = os.path.basename(os.path.abspath(run_dir).rstrip("/"))
    if not RUN_NAME_RE.match(run_name):
        raise KitError(RUN_NAME_MSG)
    return case_id, run_name


def _write_file(path, data, mode):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    os.chmod(path, mode)


def materialize_plugin_from_candidate(repo, candidate, dest):
    """Write `plugins/vibe-check` at commit `candidate`, plus the measured
    runner settings, under `dest` (which must not exist); return the plugin
    dir `<dest>/plugins/vibe-check`.

    Every byte comes from the commit's git objects (ls-tree + one cat-file
    --batch), never the working tree, so an untracked or uncommitted file
    cannot enter the copy, and no export attribute can alter it. A symlink or
    submodule in the plugin tree is refused. `<dest>/settings-measured.json`
    is the candidate's template with `<RUNNER>` replaced by `dest` and nothing
    else edited; `<dest>/statusline-capture.sh` is the candidate's script."""
    _, fcm = _freeze()
    dest = os.path.realpath(dest)
    if os.path.lexists(dest):
        raise KitError("the build dir already exists: %s" % dest)
    sha, _tree = fcm.resolve_rev(repo, candidate)
    entries = fcm._ls_tree(repo, sha, PLUGIN_REL)
    if not entries:
        raise KitError("%s is empty or absent at %s" % (PLUGIN_REL, sha))
    for mode, kind, _oid, path in entries:
        if kind != "blob" or mode not in FILE_MODES:
            raise KitError("refused: %s is not a regular file at %s"
                           % (path, sha))
        fcm.validate_rel(path)
    template = fcm.blob_at(repo, sha, RUNNER_TEMPLATE)
    script = fcm.blob_at(repo, sha, RUNNER_STATUSLINE)
    if template is None or script is None:
        raise KitError("the measured runner settings are absent at %s" % sha)
    settings = template.decode("utf-8").replace(RUNNER_PLACEHOLDER, dest)
    try:
        json.loads(settings)
    except ValueError:
        raise KitError("the runner settings are not JSON once the build dir "
                       "is substituted; use a plainer run dir path")
    blobs = fcm._cat_blobs(repo, [oid for _m, _k, oid, _p in entries])
    os.makedirs(dest)
    plugin_dir = os.path.join(dest, *PLUGIN_REL.split("/"))
    for mode, _kind, oid, path in entries:
        full = os.path.join(dest, *path.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        _write_file(full, blobs[oid], FILE_MODES[mode])
    _write_file(os.path.join(dest, STATUSLINE_NAME), script, 0o755)
    _write_file(os.path.join(dest, SETTINGS_NAME), settings.encode("utf-8"),
                0o644)
    return plugin_dir


def session_environment(env=None):
    """The environment the check sees AND the session gets: the process env
    minus STRIPPED_ENV."""
    out = dict(os.environ if env is None else env)
    for name in STRIPPED_ENV:
        out.pop(name, None)
    return out


def build_argv(plugin_dir, settings_path, model, case, session_id):
    """LAUNCH_ARGV with its fields filled, validated by check_argv."""
    fields = {"plugin_dir": plugin_dir, "settings_path": settings_path,
              "model": model, "case": case, "session_id": session_id}
    argv = [part.format(**fields) if part.startswith("{") else part
            for part in LAUNCH_ARGV]
    holdout_autopilot.check_argv(argv)
    return argv


def write_identity(run_dir, result, case_id, run_name, session_id):
    """<run_dir>/identity.json — the eligibility record. Never overwrites."""
    record = {"manifest_id": result.manifest_id,
              "check_digest": result.check_digest,
              "candidate_sha": result.candidate_sha,
              "runner": RUNNER,
              "launched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                           time.gmtime()),
              "case_id": case_id, "run_name": run_name,
              "session_id": session_id}
    path = os.path.join(run_dir, IDENTITY_NAME)
    try:
        _write_file(path, (json.dumps(record, indent=2, sort_keys=True)
                           + "\n").encode("utf-8"), 0o644)
    except FileExistsError:
        raise KitError(IDENTITY_EXISTS_MSG % run_dir)
    return path


def exec_session(argv, env, cwd):
    """Replace this process with the session (owner's Terminal only)."""
    holdout_kit.refuse_if_claude_spawned(None)
    os.chdir(cwd)
    os.execvpe(argv[0], argv, env)


def _stop(out, problems):
    for line in problems:
        print(line, file=out)
    print(IDENTITY_STOP, file=out)
    out.flush()
    return 1


# ---------------------------------------------------------------- launch


def launch(run_dir, case_arg, candidate=None, manifest_path=None,
           plugin_dir=None, settings_path=None, launch_model=None, home=None,
           env=None, repo=None, verify=None, spawn=None, out=None):
    """Check, stamp, launch. Returns 0 when the session was handed over and
    1 when anything refused; `spawn` is never called on 1.

    Production passes no `home`: verify resolves the real home itself."""
    out = out or sys.stdout
    spawn = spawn or exec_session
    run_dir = os.path.abspath(run_dir)
    repo = os.path.realpath(repo or REPO_ROOT)
    try:
        case_id, run_name = slot_identity(case_arg, run_dir)
        if os.path.lexists(os.path.join(run_dir, IDENTITY_NAME)):
            raise KitError(IDENTITY_EXISTS_MSG % run_dir)
        fc, _ = _freeze()
        verify = verify or fc.verify
        try:
            path = manifest_path or fc.active_manifest(repo)
        except Exception:  # noqa: BLE001 - no manifest, no run
            raise KitError(NO_MANIFEST_MSG)
        manifest = fc.load_manifest(path)
        model = launch_model or \
            manifest["runners"][RUNNER]["launch_model"]["value"]
        os.makedirs(run_dir, exist_ok=True)
        problems = []
        if plugin_dir is None:
            build = os.path.join(run_dir, BUILD_DIRNAME)
            built_from = candidate or manifest["candidate_sha"]
            plugin_dir = materialize_plugin_from_candidate(repo, built_from,
                                                           build)
            settings_path = os.path.join(os.path.realpath(build),
                                         SETTINGS_NAME)
            sha, _tree = freeze_common.resolve_rev(repo, built_from)
            if sha != manifest["candidate_sha"]:
                problems.append("build commit %s is not the manifest "
                                "candidate %s" % (sha,
                                                  manifest["candidate_sha"]))
        elif settings_path is None:
            raise KitError(SETTINGS_PAIR_MSG)
        session_env = session_environment(env)
        try:
            result = verify(manifest, RUNNER, plugin_dir=plugin_dir,
                            settings_path=settings_path, launch_model=model,
                            clone_dir=run_dir, repo=repo, home=home,
                            env=session_env)
        except Exception as exc:  # noqa: BLE001 - fail closed
            return _stop(out, problems + ["identity check could not run: "
                                          "%s: %s" % (type(exc).__name__,
                                                      exc)])
        problems += list(result.problems)
        if problems:
            return _stop(out, problems)
        session_id = holdout_autopilot.new_session_id()
        argv = build_argv(plugin_dir=plugin_dir, settings_path=settings_path,
                          model=model, case=os.path.abspath(case_arg),
                          session_id=session_id)
        write_identity(run_dir, result, case_id, run_name, session_id)
    except KitError as exc:
        print("eval-launch: %s" % (exc,), file=out)
        out.flush()
        return 1
    except Exception as exc:  # noqa: BLE001 - FreezeError and friends
        return _stop(out, ["%s: %s" % (type(exc).__name__, exc)])
    print("IDENTITY OK manifest_id=%s check_digest=%s candidate_sha=%s"
          % (result.manifest_id, result.check_digest, result.candidate_sha),
          file=out)
    out.flush()
    spawn(argv, session_env, run_dir)
    return 0


# ---------------------------------------------------------------- CLI


def add_parser(sub, name):
    p = sub.add_parser(name, help="launch one holdout evaluation run after "
                                  "the freeze identity check")
    p.add_argument("--run-dir", required=True, metavar="DIR",
                   help="a NEW run dir named run-<n> (identity.json goes here)")
    p.add_argument("--case", required=True, metavar="FOLDER",
                   help="the case folder (opaque; named by its H- id)")
    p.add_argument("--candidate", metavar="SHA",
                   help="build commit (default: the manifest candidate)")
    p.add_argument("--manifest", metavar="PATH",
                   help="freeze manifest (default: the active one)")
    p.add_argument("--model", metavar="MODEL",
                   help="launch model (default: the manifest's holdout-eval "
                        "launch model)")
    return p


def cmd(args):
    holdout_kit.refuse_if_claude_spawned(None)
    return launch(args.run_dir, args.case, candidate=args.candidate,
                  manifest_path=args.manifest, launch_model=args.model)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="holdout_eval_launch.py",
        description="Holdout measurement launcher: freeze identity check "
                    "before every run. Run it from a plain Terminal.")
    sub = parser.add_subparsers(dest="cmd", metavar="COMMAND")
    add_parser(sub, "eval-launch")
    return parser


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    if args.cmd != "eval-launch":
        parser.print_usage(sys.stderr)
        return 2
    try:
        return cmd(args)
    except KitError as exc:
        print("eval-launch: %s" % (exc,), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
