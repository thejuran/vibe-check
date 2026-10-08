"""holdout_kit.py — the owner-run launch kit for the v2.12 sealed holdout.

The holdout is six review cases (three catch, three quiet) that the tuning side
must never see until the Phase-55 evaluation. Four roles touch it:

  * tuning      — this repo's ordinary sessions. They never read the holdout;
                  holdout_guard.py denies every tool call that reaches it.
  * finder      — a fresh, isolated Claude session (bin/finder) that receives
                  only the kit, searches the eligible repos and writes the
                  cases into sealed/.
  * cross-check — a second isolated session (bin/crosscheck, and one fresh
                  generation per reveal) that judges each case blind, without
                  slot, key or proof, and is then shown the key.
  * evaluation  — Phase 55 decrypts the archive and re-hashes it against the
                  committed SEAL.json.

This module is the CLI entry point and the shared helper library. `setup`
lives here; the other subcommands live in sibling modules (holdout_validate,
holdout_manifest, holdout_seal, holdout_archive, holdout_dryrun) that are
imported lazily through COMMANDS, so a kit copy missing one of them still runs
the others and says plainly which command is not installed.

Rules:
  * The holdout folder is ALWAYS an explicit --folder argument. No argument
    defaults to the holdout path (a repo tool that defaulted to it would read
    the holdout without naming it on its command line).
  * Every holdout-touching subcommand calls refuse_if_claude_spawned(folder)
    first: when CLAUDECODE is set and CLAUDE_CONFIG_DIR is not inside the
    folder, the command refuses with a fixed message. The owner runs the kit
    from a plain Terminal window.
  * I/O: stdlib only, imports exactly {argparse, hashlib, hmac, importlib,
    json, os, re, secrets, shutil, stat, subprocess, sys, tarfile, tempfile}.
    Every subprocess.run is an argv list with a timeout, never a shell.
    openssl never receives -pass or -k: the passphrase comes from its own tty
    prompt.
  * Output is one plain-language line per step ("OK: ..." / "PROBLEM: ...")
    and never echoes case content.

Exit codes: 0 success, 1 a plain-language refusal or failure ("holdout: ..."
on stderr), 2 a usage error.
"""

import argparse
import hashlib
import hmac
import importlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)


class KitError(Exception):
    """One plain-language line; the CLI prints it and exits 1."""


SLOTS = ("C1", "C2", "C3", "Q1", "Q2", "Q3")
CATCH_SLOTS = ("C1", "C2", "C3")
QUIET_SLOTS = ("Q1", "Q2", "Q3")
ID_RE = re.compile(r"^H-[0-9a-f]{8}$")
XID_RE = re.compile(r"^X-[0-9a-f]{8}$")
CASE_FILES = frozenset({"case.json", "base.tar", "change.diff"})
KEY_FILES = frozenset({"key.json", "provenance.json", "proof-results.json",
                       "xcheck-ledger.json", "crosscheck.json",
                       "resolution.md"})
# Files that live directly in sealed/ and are excluded from per-case
# serialization and the private inventory. SANDBOX-SENTINEL is a harmless
# fixed-text read target for the cross-check sandbox probe.
SEALED_PRIVATE = ("HMAC-KEY", "INVENTORY.json", "SANDBOX-SENTINEL")
SANDBOX_SENTINEL_TEXT = ("holdout sandbox sentinel. If a cross-check session "
                         "can print this line, its sandbox is not enforcing "
                         "denyRead. Stop.\n")

REFUSE_MSG = ("holdout: refusing to run inside a Claude-spawned shell. "
              "Open a plain Terminal window and run this again.")
NOT_INSTALLED_MSG = "command '%s' is not installed in this kit copy"
ERR_PREFIX = "holdout: "


def new_case_id():
    """A fresh opaque case id: "H-" + 8 random hex digits, never content-derived."""
    return "H-" + secrets.token_hex(4)


def new_xcheck_id():
    """A fresh opaque cross-check id: "X-" + 8 random hex digits."""
    return "X-" + secrets.token_hex(4)


# ---------------------------------------------------------------- refusal


def _inside(path, root):
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def refuse_if_claude_spawned(folder):
    """Raise KitError(REFUSE_MSG) inside a Claude-spawned shell.

    A shell is Claude-spawned when CLAUDECODE is set. The one exception is an
    isolated holdout session, whose CLAUDE_CONFIG_DIR lives inside the folder.
    """
    if not os.environ.get("CLAUDECODE"):
        return
    cfg = os.environ.get("CLAUDE_CONFIG_DIR") or ""
    if not folder or not cfg:
        raise KitError(REFUSE_MSG)
    if not _inside(os.path.realpath(cfg), os.path.realpath(folder)):
        raise KitError(REFUSE_MSG)


# ---------------------------------------------------------------- JSON


def load_json(path, required=(), what="file"):
    """Strict JSON object load.

    `required` is either an iterable of keys that must be present, or a dict
    {key: type or tuple of types}. Booleans never satisfy an int requirement.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        raise KitError("%s is missing or unreadable" % what)
    if not isinstance(data, dict):
        raise KitError("%s has the wrong shape" % what)
    if isinstance(required, dict):
        items = required.items()
    else:
        items = ((key, None) for key in required)
    for key, types in items:
        if key not in data:
            raise KitError("%s has the wrong shape (%s)" % (what, key))
        if types is None:
            continue
        value = data[key]
        wants_bool = types is bool or (isinstance(types, tuple)
                                       and bool in types)
        if not isinstance(value, types) or (isinstance(value, bool)
                                            and not wants_bool):
            raise KitError("%s has the wrong shape (%s)" % (what, key))
    return data


def write_json_atomic(path, obj):
    """Write `obj` as sorted, indented JSON via a temp file and os.replace."""
    parent = os.path.dirname(os.path.abspath(path))
    tmp = None
    try:
        os.makedirs(parent, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=parent,
                                   prefix="." + os.path.basename(path) + ".",
                                   suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    except OSError:
        raise KitError("cannot write %s" % os.path.basename(path))
    finally:
        if tmp is not None and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _write_text(path, text, mode=None):
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        if mode is not None:
            os.chmod(path, mode)
    except OSError:
        raise KitError("cannot write %s" % os.path.basename(path))


# ---------------------------------------------------------------- subprocess


def run_argv(argv, cwd=None, timeout=60, stdin_bytes=None, capture=True):
    """Run an argv list (never a shell) with a timeout.

    Raises KitError naming only the program's basename when it cannot start
    or times out.
    """
    pipe = subprocess.PIPE if capture else None
    try:
        return subprocess.run(list(argv), cwd=cwd, input=stdin_bytes,
                              stdout=pipe, stderr=pipe, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise KitError("%s could not run (%s)"
                       % (os.path.basename(str(argv[0])),
                          type(exc).__name__))


# ---------------------------------------------------------------- hashing


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 16), b""):
                digest.update(chunk)
    except OSError:
        raise KitError("cannot read %s" % os.path.basename(path))
    return digest.hexdigest()


def hmac_hex(key, data):
    return hmac.new(key, data, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------- file walks


def walk_regular(root):
    """Sorted '/'-separated relpaths of every regular file under `root`.

    Refuses (KitError) any symlink, file or directory, and any special file.
    """
    out = []
    base = os.path.basename(os.path.normpath(root))
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in list(dirnames) + list(filenames):
            full = os.path.join(dirpath, name)
            try:
                mode = os.lstat(full).st_mode
            except OSError:
                raise KitError("cannot read an entry under %s" % base)
            if stat.S_ISLNK(mode):
                raise KitError("a symbolic link was found under %s; "
                               "remove it and run this again" % base)
            if stat.S_ISDIR(mode):
                continue
            if not stat.S_ISREG(mode):
                raise KitError("a special file was found under %s; "
                               "remove it and run this again" % base)
            rel = os.path.relpath(full, root)
            out.append(rel.replace(os.sep, "/"))
    return sorted(out)


def safe_extract_tar(tar_path, dest):
    """Extract a tar of plain files and directories into `dest`.

    Refuses absolute member names, any `..` segment, and every member that is
    not a regular file or a directory (symlinks, hardlinks, devices, fifos).
    All members are checked before anything is written.
    """
    dest_real = os.path.realpath(dest)
    try:
        with tarfile.open(tar_path, "r:*") as tar:
            members = tar.getmembers()
            for m in members:
                name = m.name
                parts = name.replace("\\", "/").split("/")
                if name.startswith("/") or os.path.isabs(name) \
                        or ".." in parts:
                    raise KitError("the archive holds an unsafe path; "
                                   "nothing was extracted")
                if m.issym() or m.islnk() or m.isdev() \
                        or not (m.isfile() or m.isdir()):
                    raise KitError("the archive holds a link or special "
                                   "file; nothing was extracted")
                target = os.path.realpath(os.path.join(dest_real, name))
                if not _inside(target, dest_real):
                    raise KitError("the archive holds an unsafe path; "
                                   "nothing was extracted")
            for m in members:
                tar.extract(m, dest_real)
    except (OSError, tarfile.TarError):
        raise KitError("cannot read or extract %s"
                       % os.path.basename(tar_path))


def sealed_dir(folder):
    return os.path.join(folder, "sealed")


def case_ids(folder):
    """Sorted case ids under sealed/cases; KitError on any other name."""
    cases = os.path.join(sealed_dir(folder), "cases")
    try:
        names = os.listdir(cases)
    except OSError:
        raise KitError("sealed/cases is missing or unreadable")
    for name in names:
        if not ID_RE.match(name):
            raise KitError("sealed/cases holds an entry that is not a case "
                           "id; remove it and run this again")
    return sorted(names)


def print_ok(msg):
    print("OK: %s" % msg)


def print_problem(msg):
    print("PROBLEM: %s" % msg)


# ---------------------------------------------------------------- setup


def add_parser(sub, name):
    if name == "setup":
        p = sub.add_parser(
            "setup", help="create the isolated holdout folder, launchers "
                          "and session settings")
        p.add_argument("--repo", action="append", required=True,
                       metavar="PATH",
                       help="an eligible source repo (repeat for each)")
        p.add_argument("--skip-system-exclusions", action="store_true",
                       help="do not run tmutil (tests only)")


def cmd(args):
    if args.cmd == "setup":
        refuse_if_claude_spawned(args.folder)
        setup(args.folder, args.repo,
              skip_system_exclusions=args.skip_system_exclusions)
        return 0
    raise KitError("unknown command")


def _check_repos(repos):
    out = []
    for repo in repos:
        real = os.path.realpath(repo)
        base = os.path.basename(real)
        if not os.path.exists(os.path.join(real, ".git")):
            raise KitError("%s is not a git repository" % base)
        out.append(real)
    return out


def setup(folder, repos, skip_system_exclusions=False):
    """Create the isolated holdout folder at the explicit `folder`."""
    refuse_if_claude_spawned(folder)
    if os.path.lexists(folder) and (not os.path.isdir(folder)
                                    or os.listdir(folder)):
        raise KitError("folder already exists and is not empty")
    _check_repos(repos)
    raise KitError("setup is not available in this kit copy yet")


# ---------------------------------------------------------------- CLI

COMMANDS = {
    "setup": "holdout_kit",
    "validate": "holdout_validate",
    "seal-build": "holdout_manifest",
    "rehash": "holdout_manifest",
    "extract": "holdout_manifest",
    "seal-order": "holdout_manifest",
    "publish": "holdout_manifest",
    "retire": "holdout_manifest",
    "resume-check": "holdout_manifest",
    "crosscheck-prepare": "holdout_seal",
    "crosscheck-reveal": "holdout_seal",
    "crosscheck-reset": "holdout_seal",
    "seal": "holdout_seal",
    "encrypt": "holdout_archive",
    "decrypt": "holdout_archive",
    "leakscan": "holdout_archive",
    "scrub": "holdout_archive",
    "dryrun": "holdout_dryrun",
}
# The ONLY commands run() dispatches without --folder. seal-order and publish
# take --repo; resume-check reads a checkpoint reply from stdin.
NO_FOLDER_COMMANDS = frozenset({"seal-order", "publish", "resume-check"})
# Commands whose cmd() does not call refuse_if_claude_spawned: they touch no
# holdout content. publish still refuses (it reads the holdout SEAL.json).
NO_REFUSAL_COMMANDS = frozenset({"seal-order", "resume-check"})


def _load_module(name):
    """Import a command module; None when that module is not in this kit copy."""
    if name == "holdout_kit":
        return sys.modules[__name__]
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name == name:
            return None
        raise


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="holdout",
        description="Owner-run launch kit for the v2.12 sealed holdout. "
                    "Run it from a plain Terminal window.")
    parser.add_argument("--folder", metavar="PATH",
                        help="the holdout folder, always explicit")
    sub = parser.add_subparsers(dest="cmd", metavar="COMMAND")
    modules, missing = {}, set()
    loaded = {}
    for name, modname in COMMANDS.items():
        if modname not in loaded:
            loaded[modname] = _load_module(modname)
        module = loaded[modname]
        if module is None:
            p = sub.add_parser(name, help="(not installed in this kit copy)")
            p.add_argument("rest", nargs=argparse.REMAINDER)
            missing.add(name)
            continue
        module.add_parser(sub, name)
        modules[name] = module
    return parser, modules, missing


def _command_and_folder(argv):
    """(command, folder given?) from the top-level arguments, without parsing
    the subcommand's own options."""
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--folder")
    pre.add_argument("cmd", nargs="?")
    pre.add_argument("rest", nargs=argparse.REMAINDER)
    try:
        ns, _ = pre.parse_known_args(argv)
    except SystemExit:
        return None, False
    return ns.cmd, ns.folder is not None


def _err(msg):
    text = str(msg)
    if not text.startswith(ERR_PREFIX):
        text = ERR_PREFIX + text
    sys.stderr.write(text + "\n")


def run(argv):
    parser, modules, missing = _build_parser()
    command, has_folder = _command_and_folder(argv)
    if command in COMMANDS and not has_folder \
            and command not in NO_FOLDER_COMMANDS:
        parser.print_usage(sys.stderr)
        sys.stderr.write("holdout: error: --folder PATH is required for "
                         "'%s'\n" % command)
        return 2
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    if not args.cmd:
        parser.print_usage(sys.stderr)
        return 2
    if args.cmd in missing:
        _err(NOT_INSTALLED_MSG % args.cmd)
        return 1
    try:
        return modules[args.cmd].cmd(args)
    except KitError as exc:
        _err(exc)
        return 1


if __name__ == "__main__":
    # Sibling modules import `holdout_kit`; make that the running module so
    # they share one KitError class and one set of helpers.
    sys.modules.setdefault("holdout_kit", sys.modules[__name__])
    sys.exit(run(sys.argv[1:]))
