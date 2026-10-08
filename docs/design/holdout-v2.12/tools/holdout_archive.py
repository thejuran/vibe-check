"""holdout_archive.py — encrypt, verify, decrypt, leak scan and scrub.

After the seal the owner turns the plaintext holdout into one encrypted
archive and removes every plaintext copy:

  * encrypt  — tars everything in the folder except archive/, tmp/ and the
               two process ledgers, encrypts the tar with the system openssl
               (the passphrase is typed at openssl's own terminal prompt),
               decrypts the result into tmp/owner/verify, re-hashes it against
               SEAL.json and only then records archive_sha256 in SEAL.json.
               Any failure after the archive was written deletes it.
  * decrypt  — the way back (Phase 55, or the owner's recovery): openssl to a
               staged tar under tmp/owner, then tar into the destination.
  * leakscan — searches the tuning side for distinctive diff and key lines,
               in the raw text and in every JSON-decoded string, and prints
               counts, locations and slots only.
  * scrub    — refuses unless the archive is verified, then deletes every
               file in the folder that is not on an explicit survivor list.

Passphrase hygiene: no code here reads, passes, stores or prompts for the
passphrase. openssl is run with its terminal inherited (capture=False) and
asks for it itself; no passphrase option ever appears in its argv. All four
commands refuse in any Claude-spawned shell.

Writer barrier: encrypt and scrub refuse while any process outside the kit's
own process tree holds the folder (cwd or an open file under it, via lsof, or
an argv naming it, via pgrep). They refuse as well when lsof or pgrep cannot
run: the check fails closed and has no override.

I/O: imports exactly {json, os, re, shutil, stat, sys, time} plus
holdout_kit and holdout_manifest; every subprocess goes through
holdout_kit.run_argv (argv list, timeout, never a shell).
"""

import json
import os
import re
import shutil
import stat
import sys
import time

import holdout_kit
import holdout_manifest
from holdout_kit import KitError

OPENSSL_BIN = "/usr/bin/openssl"
TAR_BIN = "/usr/bin/tar"
LSOF_BIN = "/usr/sbin/lsof"
PGREP_BIN = "/usr/bin/pgrep"
PS_BIN = "/bin/ps"

# The cipher and key derivation, passed to openssl verbatim. There is never a
# passphrase option: openssl prompts on the terminal.
ENC_ARGS = ["enc", "-aes-256-cbc", "-md", "sha256", "-pbkdf2", "-iter",
            "600000", "-salt"]

ARCHIVE_RELPATH = "archive/holdout-v2.12.tar.enc"
# Top-level names never put into the archive: the archive itself, the whole
# per-role scratch tree (tmp/finder, tmp/owner, tmp/crosscheck/*; scrub
# deletes it instead), and the two live process ledgers, which must never be
# overwritten by a later decrypt into the folder. Everything else at the top
# level is archived, including logs, stray files and every cross-check
# generation.
ARCHIVE_EXCLUDES = ("archive", "tmp", "LEAKSCAN.json", "RETIRED.json")

OWNER_TMP = "tmp/owner"
STAGE_NAME = "stage.tar"
VERIFY_NAME = "verify"
DECRYPT_STAGE_NAME = "decrypt-stage.tar"

SCRUB_SETTLE_SECONDS = 2.0

TAR_TIMEOUT = 600
OPENSSL_TIMEOUT = 3600

WRITERS_UNAVAILABLE_MSG = ("cannot check for active writers (%s unavailable); "
                           "refusing to continue")
WRITERS_BUSY_MSG = ("holdout folder is still in use by %d process(es): %s; "
                    "close every finder and cross-check session (/exit, then "
                    "close the window), wait a few seconds, and run this "
                    "again")
DECRYPT_FAILED_MSG = "archive did not decrypt or extract"
UNSAFE_MEMBER_MSG = "the archive holds an unsafe path; nothing was extracted"
VERIFY_FAILED_MSG = "archive verification failed; the archive was deleted"


# ---------------------------------------------------------------- refusal


def _refuse():
    """Refuse in every Claude-spawned shell, isolated sessions included: the
    owner runs these commands from a plain Terminal window only."""
    holdout_kit.refuse_if_claude_spawned(None)


# ---------------------------------------------------------------- writers


def _own_pids():
    """This process and every ancestor (the owner's shell and the bin/holdout
    wrapper hold the folder legitimately)."""
    pids = {os.getpid()}
    pid = os.getpid()
    for _ in range(128):
        try:
            proc = holdout_kit.run_argv([PS_BIN, "-o", "ppid=", "-p",
                                         str(pid)], cwd="/", timeout=30)
        except KitError:
            break
        if proc.returncode != 0:
            break
        try:
            parent = int(proc.stdout.decode("ascii", "replace").strip())
        except ValueError:
            break
        if parent <= 1 or parent in pids:
            break
        pids.add(parent)
        pid = parent
    return pids


def _comm(pid):
    try:
        proc = holdout_kit.run_argv([PS_BIN, "-o", "comm=", "-p", str(pid)],
                                    cwd="/", timeout=30)
    except KitError:
        return "?"
    name = proc.stdout.decode("utf-8", "replace").strip()
    return os.path.basename(name) or "?"


def _ere_escape(text):
    return re.sub(r"([.\[\]()*+?{}|^$\\])", r"\\\1", text)


def active_writers(folder):
    """[(pid, command basename)] for every process outside this process tree
    that has its cwd or an open file under `folder` (lsof +D) or whose argv
    names the folder (pgrep -f). Sorted by pid; never carries a path.

    KitError (fail closed) when either tool cannot run or errors.
    """
    real = os.path.realpath(folder)
    if not os.path.isdir(real):
        raise KitError("the holdout folder does not exist")
    found = {}
    # Every helper runs from "/": a child started from a cwd inside the
    # folder would otherwise report itself.
    proc_cwd = "/"
    try:
        proc = holdout_kit.run_argv([LSOF_BIN, "-w", "-F", "pc", "+D", real],
                                    cwd=proc_cwd, timeout=60)
    except KitError:
        raise KitError(WRITERS_UNAVAILABLE_MSG % "lsof")
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace").strip()
    if proc.returncode not in (0, 1) or (proc.returncode == 1
                                         and not out.strip() and err):
        raise KitError(WRITERS_UNAVAILABLE_MSG % "lsof")
    pid = None
    for line in out.splitlines():
        if line.startswith("p"):
            try:
                pid = int(line[1:])
            except ValueError:
                raise KitError(WRITERS_UNAVAILABLE_MSG % "lsof")
            found.setdefault(pid, "?")
        elif line.startswith("c") and pid is not None:
            found[pid] = os.path.basename(line[1:]) or "?"
    try:
        proc = holdout_kit.run_argv([PGREP_BIN, "-f", "--", _ere_escape(real)],
                                    cwd=proc_cwd, timeout=60)
    except KitError:
        raise KitError(WRITERS_UNAVAILABLE_MSG % "pgrep")
    if proc.returncode not in (0, 1):
        raise KitError(WRITERS_UNAVAILABLE_MSG % "pgrep")
    for line in proc.stdout.decode("ascii", "replace").split():
        try:
            found.setdefault(int(line), None)
        except ValueError:
            raise KitError(WRITERS_UNAVAILABLE_MSG % "pgrep")
    own = _own_pids()
    writers = []
    for pid in sorted(found):
        if pid in own:
            continue
        name = found[pid] or _comm(pid)
        writers.append((pid, name))
    return writers


def require_no_writers(folder):
    writers = active_writers(folder)
    if writers:
        listing = ", ".join("%d %s" % (pid, name) for pid, name in writers)
        raise KitError(WRITERS_BUSY_MSG % (len(writers), listing))


# ---------------------------------------------------------------- helpers


def _remove(path):
    """Remove a file or a directory tree if it exists (never follows links)."""
    try:
        if os.path.islink(path) or os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
    except OSError:
        raise KitError("cannot remove %s" % os.path.basename(path))


def _owner_tmp(folder):
    path = os.path.join(folder, *OWNER_TMP.split("/"))
    if os.path.islink(path):
        raise KitError("tmp/owner is a symbolic link; remove it and run this "
                       "again")
    os.makedirs(path, mode=0o700, exist_ok=True)
    os.chmod(path, 0o700)
    return path


def archive_path(folder):
    return os.path.join(folder, *ARCHIVE_RELPATH.split("/"))


def archive_members(folder):
    """Sorted top-level names that go into the archive: everything except
    ARCHIVE_EXCLUDES. A top-level symlink is refused."""
    names = []
    try:
        listing = os.listdir(folder)
    except OSError:
        raise KitError("the holdout folder is missing or unreadable")
    for name in listing:
        if name in ARCHIVE_EXCLUDES:
            continue
        if stat.S_ISLNK(os.lstat(os.path.join(folder, name)).st_mode):
            raise KitError("a symbolic link was found at the top of the "
                           "holdout folder; remove it and run this again")
        names.append(name)
    return sorted(names)


def _check_members(folder, names):
    for name in names:
        path = os.path.join(folder, name)
        mode = os.lstat(path).st_mode
        if stat.S_ISDIR(mode):
            holdout_kit.walk_regular(path)
        elif not stat.S_ISREG(mode):
            raise KitError("a special file was found at the top of the "
                           "holdout folder; remove it and run this again")


def _load_seal(folder):
    path = os.path.join(folder, holdout_manifest.SEAL_NAME)
    if not os.path.isfile(path) or os.path.islink(path):
        raise KitError("SEAL.json is missing; seal first")
    return holdout_kit.load_json(path, what="SEAL.json")


def _safe_member(name):
    parts = name.replace("\\", "/").split("/")
    return not (name.startswith("/") or ".." in parts)


# ---------------------------------------------------------------- decrypt


def decrypt_to(archive, dest, openssl=None, tar=None, stage_dir=None):
    """Decrypt `archive` (interactive openssl) into `dest`.

    openssl writes a staged tar under `stage_dir` (default: dest's parent),
    whose member names are checked (no absolute path, no `..`) before tar
    extracts them into `dest`; the stage is removed in finally. `dest` may
    already exist (the recovery decrypts back into the holdout folder); a
    symlink under it is refused before and after extraction. A `dest` this
    call created is removed again on failure.
    """
    openssl = openssl or OPENSSL_BIN
    tar = tar or TAR_BIN
    archive = os.path.abspath(archive)
    dest = os.path.abspath(dest)
    if not os.path.isfile(archive) or os.path.islink(archive):
        raise KitError("the archive is missing")
    created = not os.path.lexists(dest)
    if not created:
        if os.path.islink(dest) or not os.path.isdir(dest):
            raise KitError("the destination is not a folder")
        holdout_kit.walk_regular(dest)
    stage_dir = os.path.abspath(stage_dir or os.path.dirname(dest))
    stage = os.path.join(stage_dir, DECRYPT_STAGE_NAME)
    ok = False
    try:
        os.makedirs(stage_dir, mode=0o700, exist_ok=True)
        _remove(stage)
        proc = holdout_kit.run_argv(
            [openssl, "enc", "-d", *ENC_ARGS[1:], "-in", archive,
             "-out", stage], capture=False, timeout=OPENSSL_TIMEOUT)
        if proc.returncode != 0 or not os.path.isfile(stage):
            raise KitError(DECRYPT_FAILED_MSG)
        listing = holdout_kit.run_argv([tar, "-tf", stage],
                                       timeout=TAR_TIMEOUT)
        if listing.returncode != 0:
            raise KitError(DECRYPT_FAILED_MSG)
        names = listing.stdout.decode("utf-8", "replace").splitlines()
        if not all(_safe_member(n) for n in names):
            raise KitError(UNSAFE_MEMBER_MSG)
        os.makedirs(dest, mode=0o700, exist_ok=True)
        proc = holdout_kit.run_argv([tar, "-xf", stage, "-C", dest],
                                    timeout=TAR_TIMEOUT)
        if proc.returncode != 0:
            raise KitError(DECRYPT_FAILED_MSG)
        holdout_kit.walk_regular(dest)
        ok = True
    finally:
        _remove(stage)
        if not ok and created:
            _remove(dest)


# ---------------------------------------------------------------- encrypt


def encrypt(folder, openssl=None, tar=None):
    """Encrypt the holdout into archive/holdout-v2.12.tar.enc, verify it and
    record archive_sha256 in SEAL.json; return the archive path."""
    _refuse()
    openssl = openssl or OPENSSL_BIN
    tar = tar or TAR_BIN
    h = os.path.realpath(folder)
    require_no_writers(h)
    seal = _load_seal(h)
    archive = archive_path(h)
    if "archive_sha256" in seal or os.path.lexists(archive):
        raise KitError("already encrypted; delete archive/ deliberately to "
                       "redo")
    members = archive_members(h)
    _check_members(h, members)
    owner_tmp = _owner_tmp(h)
    stage = os.path.join(owner_tmp, STAGE_NAME)
    verify = os.path.join(owner_tmp, VERIFY_NAME)
    os.makedirs(os.path.dirname(archive), exist_ok=True)
    written = False
    ok = False
    try:
        _remove(stage)
        _remove(verify)
        proc = holdout_kit.run_argv(
            [tar, "-C", h, "-cf", stage] + ["./" + n for n in members],
            timeout=TAR_TIMEOUT)
        if proc.returncode != 0:
            raise KitError("tar could not stage the holdout (exit %d)"
                           % proc.returncode)
        print("Encrypting: openssl will ask for a new passphrase twice")
        sys.stdout.flush()
        written = True
        proc = holdout_kit.run_argv(
            [openssl, *ENC_ARGS, "-in", stage, "-out", archive],
            capture=False, timeout=OPENSSL_TIMEOUT)
        if proc.returncode != 0 or not os.path.isfile(archive):
            raise KitError("openssl could not encrypt (exit %d)"
                           % proc.returncode)
        _remove(stage)
        holdout_kit.print_ok("archive written")
        print("Verifying: openssl will ask for the passphrase once more")
        sys.stdout.flush()
        decrypt_to(archive, verify, openssl=openssl, tar=tar,
                   stage_dir=owner_tmp)
        result = holdout_manifest.rehash_folder(
            os.path.join(h, holdout_manifest.SEAL_NAME),
            os.path.join(verify, "sealed"))
        if not result.get("ok"):
            raise KitError(VERIFY_FAILED_MSG)
        holdout_kit.print_ok("archive decrypts and re-hashes clean (%d cases)"
                             % len(result["cases"]))
        seal["archive_sha256"] = holdout_kit.sha256_file(archive)
        holdout_kit.write_json_atomic(
            os.path.join(h, holdout_manifest.SEAL_NAME), seal)
        holdout_kit.print_ok("archive_sha256 recorded in SEAL.json")
        ok = True
    except KitError as exc:
        if written and str(exc) == DECRYPT_FAILED_MSG:
            raise KitError(VERIFY_FAILED_MSG)
        raise
    finally:
        _remove(stage)
        _remove(verify)
        if written and not ok:
            _remove(archive)
    return archive


# ---------------------------------------------------------------- CLI


def _resolve(folder, path):
    """A relative --archive/--dest is resolved against the holdout folder."""
    if os.path.isabs(path):
        return path
    return os.path.join(os.path.realpath(folder), path)


def add_parser(sub, name):
    if name == "encrypt":
        sub.add_parser(name, help="encrypt the holdout (openssl asks for the "
                                  "passphrase) and verify the archive")
    elif name == "decrypt":
        p = sub.add_parser(name, help="decrypt the archive into a folder "
                                      "(openssl asks for the passphrase)")
        p.add_argument("--archive", required=True, metavar="PATH",
                       help="the .tar.enc (relative paths are taken from the "
                            "holdout folder)")
        p.add_argument("--dest", required=True, metavar="PATH",
                       help="where to extract (may be the holdout folder)")
    elif name == "leakscan":
        p = sub.add_parser(name, help="search the tuning side for holdout "
                                      "text (counts and locations only)")
        p.add_argument("--repo", metavar="PATH",
                       help="the tuning repo (tree and git log -p --all)")
        p.add_argument("--scan-root", action="append", metavar="PATH",
                       help="scan this file or folder instead of the "
                            "default owner-side locations (repeatable)")
        p.add_argument("--from-archive", action="store_true",
                       help="build the probes from the decrypted archive "
                            "(after scrub)")
    elif name == "scrub":
        p = sub.add_parser(name, help="remove every plaintext copy, keeping "
                                      "only the survivor allowlist")
        p.add_argument("--yes", action="store_true",
                       help="actually delete (without it, print the plan)")
    else:
        raise KitError("unknown archive command")


def _cmd_encrypt(args):
    encrypt(args.folder)
    return 0


def _cmd_decrypt(args):
    _refuse()
    h = os.path.realpath(args.folder)
    dest = _resolve(h, args.dest)
    decrypt_to(_resolve(h, args.archive), dest, stage_dir=_owner_tmp(h))
    holdout_kit.print_ok("decrypted into %s (%d files)"
                         % (dest, len(holdout_kit.walk_regular(dest))))
    return 0


_HANDLERS = {
    "encrypt": _cmd_encrypt,
    "decrypt": _cmd_decrypt,
}


def cmd(args):
    _refuse()
    handler = _HANDLERS.get(args.cmd)
    if handler is None:
        raise KitError("unknown archive command")
    return handler(args)
