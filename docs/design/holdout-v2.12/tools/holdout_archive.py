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
# deletes it instead), the two live process ledgers and the autopilot's
# resume journal, which must never be overwritten by a later decrypt into the
# folder. Everything else at the top
# level is archived, including logs, stray files and every cross-check
# generation.
ARCHIVE_EXCLUDES = ("archive", "tmp", "LEAKSCAN.json", "RETIRED.json",
                    holdout_kit.LEAK_WAIVER, "AUTOPILOT.json")

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
    if "archive_sha256" in seal and not os.path.lexists(archive):
        # A run interrupted after SEAL.json recorded the hash but before it
        # finished deletes the archive in finally: the hash names nothing.
        # Drop it (on disk too, so the archived SEAL.json never carries it)
        # and encrypt again.
        del seal["archive_sha256"]
        holdout_kit.write_json_atomic(
            os.path.join(h, holdout_manifest.SEAL_NAME), seal)
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
        # A dry-run folder verifies its own dry-run seal; any other folder
        # gets the real-run check, which refuses every dry-run mark.
        result = holdout_manifest.rehash_folder(
            os.path.join(h, holdout_manifest.SEAL_NAME),
            os.path.join(verify, "sealed"),
            dry_run=holdout_kit.dry_run_marker_ok(h))
        if not result.get("ok"):
            raise KitError(VERIFY_FAILED_MSG)
        holdout_kit.print_ok("archive decrypts and re-hashes clean (%d cases)"
                             % len(result["cases"]))
        seal["archive_sha256"] = holdout_kit.sha256_file(archive)
        holdout_kit.write_json_atomic(
            os.path.join(h, holdout_manifest.SEAL_NAME), seal)
        # Set at once: from here SEAL.json names this archive, so finally
        # must keep it.
        ok = True
        holdout_kit.print_ok("archive_sha256 recorded in SEAL.json")
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


# ---------------------------------------------------------------- leak scan

DECODE_DEPTH = 3
PROBE_MIN_LEN = 30
# One JSON string literal: a quote, then any run of non-quote/non-backslash
# characters or backslash escapes, then a quote. Unambiguous, so linear.
_LITERAL_RE = re.compile(r'"(?:[^"\\]|\\.)*"', re.S)
_DIFF_HEADER_RE = re.compile(r"^(---|\+\+\+) (a/|b/|/dev/null)")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_BIN = "git"
GIT_LOG_LOCATION = "git log -p --all"
NO_SEALED_MSG = "no sealed/ to build probes from; use --from-archive"
NO_PROBES_MSG = ("no diff or key line of 30+ characters was found; a leak "
                 "scan would prove nothing")
LEDGER_MALFORMED_MSG = ("LEAKSCAN.json is malformed; repair it (never delete "
                        "it) and scan again")
LEAK_REMEDY_MSG = ("publish will refuse until these slots are replaced "
                   "through the finder and a fresh cross-check and the "
                   "holdout is re-sealed; deleting the matched files is "
                   "cleanup, not a remedy")
RETIRED_LINE = ("retired %s (%s): its revision and content cannot be "
                "re-sealed under any ID")


def decoded_strings(text, depth=None):
    """Every JSON string literal in `text`, decoded (escapes undone), plus,
    recursively up to `depth` levels (default DECODE_DEPTH), the literals
    inside each decoded value. Literals that do not decode are skipped.
    Returns the decoded values only, never the raw text."""
    if depth is None:
        depth = DECODE_DEPTH
    out = []
    frontier = [text]
    for _ in range(max(depth, 0)):
        nxt = []
        for chunk in frontier:
            if '"' not in chunk:
                continue
            for match in _LITERAL_RE.finditer(chunk):
                try:
                    value = json.loads(match.group(0), strict=False)
                except ValueError:
                    continue
                if isinstance(value, str):
                    out.append(value)
                    nxt.append(value)
        frontier = nxt
    return out


def _key_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from _key_strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _key_strings(value)


def _probes(folder):
    """[(probe, slot, case_id)]: every added/removed diff line (marker and
    surrounding whitespace dropped) and every key.json string value of at
    least PROBE_MIN_LEN characters, per sealed case under `folder`."""
    sealed = os.path.join(folder, "sealed")
    if os.path.islink(sealed) or not os.path.isdir(sealed):
        raise KitError(NO_SEALED_MSG)
    out = []
    for cid in holdout_kit.case_ids(folder):
        key = holdout_kit.load_json(
            os.path.join(sealed, "keys", cid, "key.json"), what="a key.json")
        slot = key.get("slot")
        if slot not in holdout_kit.SLOTS:
            raise KitError("a key.json has no valid slot")
        diff = os.path.join(sealed, "cases", cid, "change.diff")
        try:
            with open(diff, "rb") as fh:
                text = fh.read().decode("utf-8", "replace")
        except OSError:
            raise KitError("a change.diff is missing or unreadable")
        seen = set()
        candidates = []
        for line in text.splitlines():
            if _DIFF_HEADER_RE.match(line):
                continue
            if line[:1] in ("+", "-"):
                candidates.append(line[1:])
        candidates.extend(_key_strings(key))
        for raw in candidates:
            probe = raw.strip()
            if len(probe) >= PROBE_MIN_LEN and probe not in seen \
                    and "\0" not in probe:
                seen.add(probe)
                out.append((probe, slot, cid))
    return out


def _index(probes):
    index = {}
    for probe, slot, cid in probes:
        slots, ids = index.setdefault(probe, (set(), set()))
        slots.add(slot)
        ids.add(cid)
    return index


def _match(text, index):
    """(raw-matched probes, decoded-matched probes) for one text."""
    raw = {p for p in index if p in text}
    joined = "\0".join(decoded_strings(text))
    decoded = {p for p in index if p in joined} if joined else set()
    return raw, decoded


def _hit(location, raw, decoded, index):
    if not raw and not decoded:
        return None
    matched = raw | decoded
    return {"location": location, "count": len(raw) + len(decoded),
            "decoded": not raw,
            "slots": sorted({s for p in matched for s in index[p][0]}),
            "case_ids": sorted({c for p in matched for c in index[p][1]})}


def _scan_file(path, index):
    """The hit for one file (raw pass + JSON-decoded pass), or None."""
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8", "replace")
    raw, decoded = _match(text, index)
    return _hit(path, raw, decoded, index)


def _under(path, root):
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def _iter_files(root, skip, skip_names=()):
    """Regular files under `root` (a file or a folder), never following a
    link and never entering `skip` (the holdout folder)."""
    try:
        mode = os.lstat(root).st_mode
    except OSError:
        return
    if stat.S_ISLNK(mode):
        return
    if stat.S_ISREG(mode):
        if not _under(os.path.realpath(root), skip):
            yield root
        return
    if not stat.S_ISDIR(mode) or _under(os.path.realpath(root), skip):
        return
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(
            d for d in dirnames if d not in skip_names
            and not _under(os.path.realpath(os.path.join(dirpath, d)), skip))
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            try:
                if not stat.S_ISREG(os.lstat(path).st_mode):
                    continue
            except OSError:
                continue
            yield path


def _git_log(repo):
    proc = holdout_kit.run_argv(
        [GIT_BIN, "-C", repo, "log", "-p", "--all", "--no-color",
         "--no-ext-diff", "--no-textconv"], timeout=600)
    if proc.returncode != 0:
        raise KitError("git log could not read the tuning repo")
    return proc.stdout.decode("utf-8", "replace")


def default_scan_roots(home=None):
    """The owner-side locations a leak could land in (never the holdout)."""
    home = home or os.path.expanduser("~")
    return [os.path.join(home, ".claude"),
            os.path.join(home, ".claude", "history.jsonl"),
            "/private/tmp/claude-%d" % os.getuid(),
            os.path.join(home, ".codex"),
            os.path.join(home, ".zsh_history")]


def record_leakscan(folder, result):
    """Append one entry (counts, hit case IDs and slots; never a location, a
    probe or any decoded text) to <folder>/LEAKSCAN.json. Existing entries
    are never modified; a malformed ledger is refused, never replaced."""
    path = os.path.join(folder, holdout_manifest.LEAKSCAN_RELPATH)
    if os.path.lexists(path):
        if os.path.islink(path):
            raise KitError(LEDGER_MALFORMED_MSG)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                ledger = json.load(fh)
        except (OSError, ValueError):
            raise KitError(LEDGER_MALFORMED_MSG)
        if not isinstance(ledger, dict) \
                or ledger.get("schema") != holdout_manifest.LEAKSCAN_SCHEMA \
                or not isinstance(ledger.get("scans"), list):
            raise KitError(LEDGER_MALFORMED_MSG)
    else:
        ledger = {"schema": holdout_manifest.LEAKSCAN_SCHEMA, "scans": []}
    seal_path = os.path.join(folder, holdout_manifest.SEAL_NAME)
    entry = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "seal_sha256": (holdout_kit.sha256_file(seal_path)
                             if os.path.isfile(seal_path) else None),
             "probes": result["probes"],
             "hits": len(result["hits"]),
             "hit_case_ids": list(result["hit_case_ids"]),
             "hit_slots": list(result["hit_slots"])}
    ledger["scans"].append(entry)
    holdout_kit.write_json_atomic(path, ledger)
    return ledger


def _report(result, unreadable):
    if unreadable:
        holdout_kit.print_problem("leak scan could not read %d file(s); they "
                                  "were not checked" % unreadable)
    hits = result["hits"]
    if not hits:
        holdout_kit.print_ok("leak scan: 0 matches across %d probes (raw + "
                             "JSON-decoded)" % result["probes"])
        return
    holdout_kit.print_problem("leak scan: %d location(s) contain holdout "
                              "text:" % len(hits))
    for hit in hits:
        line = "  %s: %d (slots: %s)" % (hit["location"], hit["count"],
                                         ", ".join(hit["slots"]))
        if hit["decoded"]:
            line += " (JSON-decoded)"
        print(line)
    holdout_kit.print_problem("slots to replace: %s"
                              % ", ".join(result["hit_slots"]))
    holdout_kit.print_problem(LEAK_REMEDY_MSG)


def leakscan(folder, scan_roots=None, repo=None, from_archive=False,
             openssl=None, tar=None):
    """Search the tuning side for holdout text; record the scan in
    LEAKSCAN.json and retire every case it names. Prints counts, locations
    and slots only.

    With from_archive the probes come from the archive, decrypted into
    tmp/owner/verify and removed in finally (for use after scrub).
    """
    _refuse()
    h = os.path.realpath(folder)
    roots = list(scan_roots) if scan_roots is not None \
        else default_scan_roots()
    verify = None
    try:
        if from_archive:
            archive = archive_path(h)
            if not os.path.isfile(archive) or os.path.islink(archive):
                raise KitError("the archive is missing; nothing to build "
                               "probes from")
            owner_tmp = _owner_tmp(h)
            verify = os.path.join(owner_tmp, VERIFY_NAME)
            _remove(verify)
            print("Decrypting: openssl will ask for the passphrase")
            sys.stdout.flush()
            decrypt_to(archive, verify, openssl=openssl, tar=tar,
                       stage_dir=owner_tmp)
            source = verify
        else:
            source = h
        probes = _probes(source)
        if not probes:
            raise KitError(NO_PROBES_MSG)
        index = _index(probes)
        slot_of = {cid: slot for _, slot, cid in probes}
        hits, seen, unreadable = [], set(), 0
        sources = [(root, ()) for root in roots]
        if repo:
            sources.append((os.path.realpath(repo), (".git",)))
        for root, skip_names in sources:
            for path in _iter_files(root, h, skip_names):
                real = os.path.realpath(path)
                if real in seen:
                    continue
                seen.add(real)
                try:
                    hit = _scan_file(path, index)
                except OSError:
                    unreadable += 1
                    continue
                if hit:
                    hits.append(hit)
        if repo:
            raw, decoded = _match(_git_log(os.path.realpath(repo)), index)
            hit = _hit(GIT_LOG_LOCATION, raw, decoded, index)
            if hit:
                hits.append(hit)
        result = {"probes": len(index), "hits": hits,
                  "hit_case_ids": sorted({c for h_ in hits
                                          for c in h_["case_ids"]}),
                  "hit_slots": sorted({s for h_ in hits
                                       for s in h_["slots"]})}
        _report(result, unreadable)
        record_leakscan(h, result)
        for cid in result["hit_case_ids"]:
            holdout_manifest.retire_case(h, cid, "leakscan",
                                         content_folder=source)
            holdout_kit.print_problem(RETIRED_LINE % (slot_of[cid], cid))
        return result
    finally:
        if verify is not None:
            _remove(verify)


# ---------------------------------------------------------------- scrub

# Files that outlive the plaintext, besides the unmodified kit files listed in
# kit/KIT-INVENTORY.json. LEAKSCAN.json (counts, opaque IDs, slots) and
# RETIRED.json (ID-independent fingerprints) must survive so later scans,
# publish and seal keep seeing every earlier leak and retirement.
# DRY-RUN.json, SYNTHETIC-AGREEMENT.json and LEAK-WAIVER.json (fixed fields,
# opaque IDs, slots and hashes) survive so a scrubbed dry-run folder stays
# marked: publish and rehash keep refusing its seal. AUTOPILOT.json (step names, opaque IDs,
# session ids, slots) survives so a re-run of the autopilot after scrub
# still knows how the run ended.
SCRUB_FIXED_SURVIVORS = ("SEAL.json", ".metadata_never_index",
                         ARCHIVE_RELPATH, "bin/holdout",
                         "kit/KIT-INVENTORY.json", "LEAKSCAN.json",
                         "RETIRED.json", holdout_kit.DRYRUN_MARKER,
                         holdout_kit.SYNTHETIC_AGREEMENT,
                         holdout_kit.LEAK_WAIVER, "AUTOPILOT.json")
# Survivors that must be present after scrub; any other may be absent.
REQUIRED_SURVIVORS = ("SEAL.json", ".metadata_never_index", ARCHIVE_RELPATH,
                      "bin/holdout")
KEEP_DIRS = ("archive", "bin", "kit")
RESIDUE_MARK = "vibe-check-holdout"
ARCHIVE_UNVERIFIED_MSG = "archive missing or not verified; run encrypt first"
INVENTORY_MSG = ("kit/KIT-INVENTORY.json is missing or malformed; scrub "
                 "cannot know what to keep")


def _safe_rel(rel):
    if not isinstance(rel, str) or not rel or rel.startswith("/") \
            or "\\" in rel:
        return False
    return all(part not in ("", ".", "..") for part in rel.split("/"))


def survivor_allowlist(folder):
    """{relpath: required sha256 or None}: SCRUB_FIXED_SURVIVORS plus every
    kit file listed in kit/KIT-INVENTORY.json with its recorded hash."""
    path = os.path.join(folder, "kit", holdout_kit.KIT_INVENTORY)
    if os.path.islink(path):
        raise KitError(INVENTORY_MSG)
    try:
        inventory = holdout_kit.load_json(path, required={"files": dict},
                                          what="kit/KIT-INVENTORY.json")
    except KitError:
        raise KitError(INVENTORY_MSG)
    allow = {rel: None for rel in SCRUB_FIXED_SURVIVORS}
    for rel, sha in inventory["files"].items():
        if not _safe_rel(rel) or not isinstance(sha, str) \
                or not _HEX64_RE.match(sha):
            raise KitError(INVENTORY_MSG)
        allow["kit/" + rel] = sha
    return allow


def _archive_verified(h):
    archive = archive_path(h)
    seal_path = os.path.join(h, holdout_manifest.SEAL_NAME)
    try:
        seal = holdout_kit.load_json(seal_path, what="SEAL.json")
    except KitError:
        raise KitError(ARCHIVE_UNVERIFIED_MSG)
    recorded = seal.get("archive_sha256")
    if not isinstance(recorded, str) or os.path.islink(archive) \
            or not os.path.isfile(archive):
        raise KitError(ARCHIVE_UNVERIFIED_MSG)
    if holdout_kit.sha256_file(archive) != recorded:
        raise KitError(ARCHIVE_UNVERIFIED_MSG)


def _is_survivor(h, rel, allowlist):
    if rel not in allowlist:
        return False
    sha = allowlist[rel]
    return sha is None or holdout_kit.sha256_file(
        os.path.join(h, *rel.split("/"))) == sha


def _top(rel):
    return rel.split("/")[0]


def _planned_removals(h, allowlist):
    return [rel for rel in holdout_kit.walk_regular(h)
            if not _is_survivor(h, rel, allowlist)]


def _remove_non_survivors(folder, allowlist):
    """Delete every regular file that is not an allowlisted survivor (or
    whose bytes differ from its required hash); return (count, sorted
    top-level names)."""
    removed = _planned_removals(folder, allowlist)
    for rel in removed:
        try:
            os.remove(os.path.join(folder, *rel.split("/")))
        except OSError:
            raise KitError("cannot remove a file under %s" % _top(rel))
    return len(removed), sorted({_top(rel) for rel in removed})


def _prune(h):
    keep = {os.path.join(h, name) for name in KEEP_DIRS}
    for dirpath, _, _ in os.walk(h, topdown=False, followlinks=False):
        if dirpath == h or dirpath in keep:
            continue
        try:
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
        except OSError:
            raise KitError("cannot remove an empty folder under %s"
                           % _top(os.path.relpath(dirpath, h)))


def _rewalk_survivors(folder):
    return holdout_kit.walk_regular(folder)


def _check_survivors(h, walk, allowlist):
    unexpected = [rel for rel in walk if not _is_survivor(h, rel, allowlist)]
    if unexpected:
        raise KitError("scrub incomplete: %d unexpected file(s) remain under "
                       "%s" % (len(unexpected),
                               ", ".join(sorted({_top(r)
                                                 for r in unexpected}))))
    missing = [rel for rel in REQUIRED_SURVIVORS if rel not in walk]
    if missing:
        raise KitError("scrub incomplete: required survivor(s) missing: %s"
                       % ", ".join(missing))


def _default_residue_bases():
    return {"home": os.path.expanduser("~"),
            "tmp": "/private/tmp/claude-%d" % os.getuid()}


def _listdir(path):
    try:
        return sorted(os.listdir(path))
    except OSError:
        return []


def _history_lines(path, h):
    count = 0
    try:
        with open(path, "rb") as fh:
            for raw in fh:
                try:
                    entry = json.loads(raw.decode("utf-8", "replace"))
                except ValueError:
                    continue
                project = entry.get("project") if isinstance(entry, dict) \
                    else None
                if isinstance(project, str) and h in project:
                    count += 1
    except OSError:
        return 0
    return count


def _residue(h, bases):
    """[(path, history line count or None)] for owner-side places outside
    the folder that may still hold holdout text. Never deleted here."""
    out = []
    claude = os.path.join(bases["home"], ".claude")
    projects = os.path.join(claude, "projects")
    for name in _listdir(projects):
        if RESIDUE_MARK in name:
            out.append((os.path.join(projects, name), None))
    history = os.path.join(claude, "history.jsonl")
    lines = _history_lines(history, h)
    if lines:
        out.append((history, lines))
    for name in ("file-history", "paste-cache"):
        path = os.path.join(claude, name)
        if os.path.lexists(path):
            out.append((path, None))
    for name in _listdir(bases["tmp"]):
        if RESIDUE_MARK in name:
            out.append((os.path.join(bases["tmp"], name), None))
    return out


def _scrub_checks(h):
    require_no_writers(h)
    _archive_verified(h)
    allowlist = survivor_allowlist(h)
    holdout_kit.walk_regular(h)
    for rel in REQUIRED_SURVIVORS:
        if not os.path.isfile(os.path.join(h, *rel.split("/"))):
            raise KitError("%s is missing; scrub would leave the folder "
                           "unusable" % rel)
    return allowlist


def scrub_plan(folder):
    """(top-level names scrub would remove, file count) without deleting."""
    _refuse()
    h = os.path.realpath(folder)
    allowlist = _scrub_checks(h)
    removals = _planned_removals(h, allowlist)
    return sorted({_top(rel) for rel in removals}), len(removals)


def scrub(folder, residue_bases=None):
    """Remove every plaintext copy inside the folder; return residue
    locations outside it that the owner must delete by hand."""
    _refuse()
    h = os.path.realpath(folder)
    allowlist = _scrub_checks(h)
    count, tops = _remove_non_survivors(h, allowlist)
    _prune(h)
    first = _rewalk_survivors(h)
    time.sleep(SCRUB_SETTLE_SECONDS)
    second = _rewalk_survivors(h)
    _check_survivors(h, first, allowlist)
    _check_survivors(h, second, allowlist)
    holdout_kit.print_ok("plaintext removed (%d file(s) under %s); "
                         "survivors: SEAL.json, the archive, bin/holdout and "
                         "the unmodified kit"
                         % (count, ", ".join(tops) or "nothing"))
    residue = _residue(h, residue_bases or _default_residue_bases())
    for path, lines in residue:
        if lines is None:
            holdout_kit.print_problem("residue: %s — delete it by hand"
                                      % path)
        else:
            holdout_kit.print_problem("residue: %s (%d line(s) name the "
                                      "holdout) — delete those lines by "
                                      "hand" % (path, lines))
    return [path for path, _ in residue]


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


def _cmd_leakscan(args):
    if not args.repo:
        holdout_kit.print_ok("tuning repo not scanned (pass --repo)")
    result = leakscan(args.folder, scan_roots=args.scan_root, repo=args.repo,
                      from_archive=args.from_archive)
    return 1 if result["hits"] else 0


def _cmd_scrub(args):
    try:
        if not args.yes:
            tops, count = scrub_plan(args.folder)
            print("Scrub will remove %d file(s) under: %s"
                  % (count, ", ".join(tops) or "nothing"))
            print("Survivors: %s, and every unmodified kit file listed in "
                  "kit/KIT-INVENTORY.json" % ", ".join(SCRUB_FIXED_SURVIVORS))
            print("Re-run with --yes to remove the plaintext.")
            return 0
        scrub(args.folder)
    except KitError as exc:
        if str(exc) == ARCHIVE_UNVERIFIED_MSG:
            holdout_kit.print_problem(ARCHIVE_UNVERIFIED_MSG)
            return 1
        raise
    return 0


_HANDLERS = {
    "encrypt": _cmd_encrypt,
    "decrypt": _cmd_decrypt,
    "leakscan": _cmd_leakscan,
    "scrub": _cmd_scrub,
}


def cmd(args):
    _refuse()
    handler = _HANDLERS.get(args.cmd)
    if handler is None:
        raise KitError("unknown archive command")
    return handler(args)
