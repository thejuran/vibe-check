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
                    holdout_kit.LEAK_WAIVER, "LEAK-CLEARED.json",
                    "AUTOPILOT.json")

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
             openssl=None, tar=None, home=None, setup_time=None):
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
        by_slot, slot_repo = _slot_probes(source)
        tuning = os.path.realpath(repo) if repo else None
        places = _Places(home or os.path.expanduser("~"), tuning)
        setup = _setup_time(h) if setup_time is None else setup_time
        found = {slot: [] for slot in by_slot}
        hits, seen, unreadable = [], set(), 0
        sources = [(root, ()) for root in roots]
        if tuning:
            sources.append((tuning, (".git",)))
        for root, skip_names in sources:
            for path in _iter_files(root, h, skip_names):
                real = os.path.realpath(path)
                if real in seen:
                    continue
                seen.add(real)
                try:
                    with open(path, "rb") as fh:
                        text = fh.read().decode("utf-8", "replace")
                except OSError:
                    unreadable += 1
                    continue
                raw, decoded = _match(text, index)
                hit = _hit(path, raw, decoded, index)
                if hit:
                    hits.append(hit)
                    for f in _file_findings(path, text, by_slot, slot_repo,
                                            places, setup):
                        found[f[0]].append(f)
        if tuning:
            log = _git_log(tuning)
            raw, decoded = _match(log, index)
            hit = _hit(GIT_LOG_LOCATION, raw, decoded, index)
            if hit:
                hits.append(hit)
                for slot in hit["slots"]:
                    found[slot].append((slot, "tuning-gitlog", "holdout",
                                        "unknown"))
        hits, benign = _apply_owner_rule(hits, found, slot_of)
        if benign:
            holdout_kit.print_ok(OWN_SOURCE_LINE % benign)
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


# ---------------------------------------------------------------- leakdiag
#
# Read-only: the same probes and places as leakscan, but nothing is recorded
# or retired, and each slot's matches are sorted in fixed words.
#
# Owner rule (2026-10-09): a case's own source code in the AI history of
# that same repo is not a leak. So each probe is `source` when its text is in
# the case's source repo history (git log -p --all; the repo's own code,
# even when a key quotes it) and `holdout` otherwise (the finder's own
# words, a constructed line, or a repo that cannot be read). Each match is
# placed: the case's own repo (Claude transcripts or prompts, Codex sessions
# run there), a tuning-side place, or elsewhere. Per slot:
#   exposed          any holdout probe matched, or any match tuning-side
#   origin-history   only source probes, only in the slot's own repo places
#   prior-elsewhere  only source probes, some in other or unattributed stores

_OWN_WHERE = frozenset({"own-transcript", "own-history", "codex-own"})
_TUNING_WHERE = frozenset({"tuning-transcript", "tuning-tree",
                           "tuning-gitlog", "tuning-plugin", "codex-tuning",
                           "shared-tmp", "zsh-history", "other"})
_ALL_WHERE = tuple(sorted(_OWN_WHERE | _TUNING_WHERE | {
    "other-transcript", "claude-history", "claude-plugins", "claude-debug",
    "claude-other", "codex-other", "codex"}))
TUNING_PLUGIN = "vibe-check"


def _setup_time(folder):
    st = os.stat(folder)
    return getattr(st, "st_birthtime", st.st_ctime)


def _project_dir(path):
    """Claude Code's ~/.claude/projects folder name for a project path."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(path))


def _same_project(name, repo):
    want = _project_dir(repo)
    return name == want or name.startswith(want + "-")


def _utc_epoch(t):
    """Seconds since 1970 for a struct_time read as UTC (no local zone, so
    no daylight-saving shift)."""
    y, m = t.tm_year, t.tm_mon
    y -= m <= 2
    era = y // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + t.tm_mday - 1
    days = era * 146097 + yoe * 365 + yoe // 4 - yoe // 100 + doy - 719468
    return float(days * 86400 + t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec)


def _epoch(value):
    """A transcript timestamp (ISO UTC text, or epoch s/ms) as epoch s."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value / 1000.0 if value > 1e11 else float(value)
    if isinstance(value, str):
        try:
            return _utc_epoch(time.strptime(value[:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            return None
    return None


def _line_matches(text, probes):
    if any(p in text for p in probes):
        return True
    joined = "\0".join(decoded_strings(text))
    return bool(joined) and any(p in joined for p in probes)


def _json_or_none(text):
    try:
        obj = json.loads(text)
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def _codex_cwds(home):
    """{codex session id: cwd} from each session file's first line."""
    out = {}
    root = os.path.join(home, ".codex", "sessions")
    for path in _iter_files(root, "\0"):
        try:
            with open(path, "rb") as fh:
                first = fh.readline().decode("utf-8", "replace")
        except OSError:
            continue
        payload = (_json_or_none(first) or {}).get("payload")
        if isinstance(payload, dict) and isinstance(payload.get("cwd"), str):
            for key in ("id", "session_id"):
                if isinstance(payload.get(key), str):
                    out[payload[key]] = payload["cwd"]
    return out


def _attribute(cwd, slot_repo, tuning, own, tune, other):
    if isinstance(cwd, str) and cwd:
        real = os.path.realpath(cwd)
        if slot_repo and _under(real, os.path.realpath(slot_repo)):
            return own
        if tuning and _under(real, tuning):
            return tune
        return other
    return None


class _Places:
    """Where a matching file or entry is, relative to one slot's repo."""

    def __init__(self, home, tuning):
        self.home = home
        self.tuning = tuning
        self.claude = os.path.join(home, ".claude")
        self.codex = os.path.join(home, ".codex")
        self._cwds = None

    def codex_cwds(self):
        if self._cwds is None:
            self._cwds = _codex_cwds(self.home)
        return self._cwds

    def place(self, path, slot_repo, entry, file_cwd):
        projects = os.path.join(self.claude, "projects")
        if _under(path, projects):
            name = os.path.relpath(path, projects).split(os.sep)[0]
            if slot_repo and _same_project(name, slot_repo):
                return "own-transcript"
            if self.tuning and _same_project(name, self.tuning):
                return "tuning-transcript"
            return "other-transcript"
        if path == os.path.join(self.claude, "history.jsonl"):
            got = _attribute((entry or {}).get("project"), slot_repo,
                             self.tuning, "own-history", "tuning-transcript",
                             "claude-history")
            return got or "claude-history"
        if _under(path, os.path.join(self.claude, "plugins")):
            parts = os.path.relpath(path, self.claude).split(os.sep)
            return "tuning-plugin" if TUNING_PLUGIN in parts \
                else "claude-plugins"
        if _under(path, os.path.join(self.claude, "debug")):
            return "claude-debug"
        if _under(path, self.claude):
            return "claude-other"
        if _under(path, self.codex):
            cwd = file_cwd
            if cwd is None and isinstance(entry, dict):
                cwd = self.codex_cwds().get(entry.get("session_id"))
            got = _attribute(cwd, slot_repo, self.tuning, "codex-own",
                             "codex-tuning", "codex-other")
            return got or "codex"
        if any(_under(path, t) for t in ("/private/tmp/claude-%d"
                                         % os.getuid(),
                                         "/tmp/claude-%d" % os.getuid())):
            return "shared-tmp"
        if path == os.path.join(self.home, ".zsh_history"):
            return "zsh-history"
        if self.tuning and _under(os.path.realpath(path), self.tuning):
            return "tuning-tree"
        return "other"


def _file_cwd(path, text, places):
    """The cwd a Codex session file records on its first line, if any."""
    if not _under(path, os.path.join(places.codex, "sessions")):
        return None
    payload = (_json_or_none(text.split("\n", 1)[0]) or {}).get("payload")
    cwd = payload.get("cwd") if isinstance(payload, dict) else None
    return cwd if isinstance(cwd, str) else None


def _file_findings(path, text, by_slot, slot_repo, places, setup):
    """[(slot, place, origin, when)] for one file. jsonl files are read line
    by line so each matching entry carries its own place and timestamp."""
    out = []
    mtime = os.lstat(path).st_mtime
    jsonl = path.endswith(".jsonl")
    file_cwd = _file_cwd(path, text, places)
    for unit in (text.splitlines() if jsonl else [text]):
        entry = _json_or_none(unit) if jsonl else None
        for slot, origins in by_slot.items():
            hit = [o for o, probes in origins.items()
                   if probes and _line_matches(unit, probes)]
            if not hit:
                continue
            stamp = None
            if entry is not None:
                stamp = _epoch(entry.get("timestamp", entry.get("ts")))
            when = "after" if (stamp if stamp is not None else mtime) \
                >= setup else "before"
            place = places.place(path, slot_repo.get(slot), entry, file_cwd)
            out.extend((slot, place, o, when) for o in hit)
    return out


def _repo_history(repo):
    """The repo's whole history as text (git log -p --all), or None when it
    cannot be read: then no probe of that case counts as the repo's own."""
    if not repo or not os.path.isdir(repo):
        return None
    try:
        proc = holdout_kit.run_argv(
            [GIT_BIN, "-C", repo, "log", "-p", "--all", "--no-color",
             "--no-ext-diff", "--no-textconv"], timeout=600)
    except KitError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace")


def _slot_probes(source):
    """{slot: {"source": set, "holdout": set}} and {slot: source repo}."""
    repos, history = {}, {}
    for cid in holdout_kit.case_ids(source):
        key = holdout_kit.load_json(
            os.path.join(source, "sealed", "keys", cid, "key.json"),
            what="a key.json")
        try:
            prov = holdout_kit.load_json(
                os.path.join(source, "sealed", "keys", cid,
                             "provenance.json"), what="a provenance.json")
        except KitError:
            prov = {}
        repo = prov.get("source_repo")
        repo = repo if isinstance(repo, str) else None
        repos[key.get("slot")] = repo
        history[cid] = _repo_history(repo)
    by_slot = {}
    for probe, slot, cid in _probes(source):
        hist = history.get(cid)
        origin = "source" if hist is not None and probe in hist \
            else "holdout"
        by_slot.setdefault(slot, {"source": set(), "holdout": set()})[
            origin].add(probe)
    return by_slot, repos


def _slot_cause(found):
    if not found:
        return "none"
    places = {f[1] for f in found}
    origins = {f[2] for f in found}
    if "holdout" in origins or places & _TUNING_WHERE:
        return "exposed"
    if places <= _OWN_WHERE:
        return "origin-history"
    return "prior-elsewhere"


def leakdiag(folder, scan_roots=None, repo=None, from_archive=False,
             home=None, setup_time=None, openssl=None, tar=None):
    """{slot: {"cause", "where", "probe", "when"}} for every slot present,
    lists sorted. Reads only: never records a scan or retires a case."""
    _refuse()
    h = os.path.realpath(folder)
    home = home or os.path.expanduser("~")
    roots = list(scan_roots) if scan_roots is not None \
        else default_scan_roots(home)
    setup = _setup_time(h) if setup_time is None else setup_time
    verify = None
    try:
        source = h
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
        by_slot, slot_repo = _slot_probes(source)
        index = _index(_probes(source))
        tuning = os.path.realpath(repo) if repo else None
        places = _Places(home, tuning)
        found = {slot: [] for slot in by_slot}
        sources = [(root, ()) for root in roots]
        if tuning:
            sources.append((tuning, (".git",)))
        seen = set()
        for root, skip_names in sources:
            for path in _iter_files(root, h, skip_names):
                real = os.path.realpath(path)
                if real in seen:
                    continue
                seen.add(real)
                try:
                    with open(path, "rb") as fh:
                        text = fh.read().decode("utf-8", "replace")
                except OSError:
                    continue
                raw, decoded = _match(text, index)
                if not raw and not decoded:
                    continue
                for f in _file_findings(path, text, by_slot, slot_repo,
                                        places, setup):
                    found[f[0]].append(f)
        if tuning:
            log = _git_log(tuning)
            for slot, origins in by_slot.items():
                for origin, probes in origins.items():
                    if probes and _line_matches(log, probes):
                        found[slot].append((slot, "tuning-gitlog", origin,
                                            "unknown"))
        order = list(holdout_kit.SLOTS)
        return {slot: {"cause": _slot_cause(f),
                       "where": sorted({x[1] for x in f}),
                       "probe": sorted({x[2] for x in f}),
                       "when": sorted({x[3] for x in f})}
                for slot, f in sorted(found.items(),
                                      key=lambda kv: order.index(kv[0]))}
    finally:
        if verify is not None:
            _remove(verify)


def leakdiag_line(result):
    """The one line the owner may send to the tuning session."""
    where = sorted({w for r in result.values() for w in r["where"]})
    parts = ["%s=%s" % (slot, result[slot]["cause"] if slot in result
                        else "none") for slot in holdout_kit.SLOTS]
    return "leakdiag %s where=%s" % (" ".join(parts),
                                     ",".join(where) if where else "none")


# ---------------------------------------------------------------- owner rule in leakscan

OWN_SOURCE_LINE = ("leak scan: matched only the cases' own source code outside "
                   "tuning-side places (%d location(s); not a leak under the "
                   "owner rule)")


def _apply_owner_rule(hits, found, slot_of):
    """(hits, benign count): each hit keeps only the slots leakdiag's rule
    calls exposed; a hit left with none is dropped and counted as benign."""
    exposed = {slot for slot, f in found.items()
               if _slot_cause(f) == "exposed"}
    kept, benign = [], 0
    for hit in hits:
        slots = [s for s in hit["slots"] if s in exposed]
        if not slots:
            benign += 1
            continue
        kept.append(dict(hit, slots=slots, case_ids=[
            c for c in hit["case_ids"] if slot_of.get(c) in exposed]))
    return kept, benign


LEAK_CLEAR_NEEDS_MSG = ("leak-clear needs SEAL.json and the live sealed/ "
                        "(run it before scrub)")


def leak_clear(folder, repo=None, scan_roots=None, home=None,
               setup_time=None):
    """Owner rule (2026-10-09): append a clearance for every current case a
    leak scan named or a leakscan retirement covers whose slot leakdiag does
    not call exposed. Returns (cleared slots, kept slots), each sorted. The
    classification is recomputed here; nothing the owner types is trusted."""
    _refuse()
    h = os.path.realpath(folder)
    if not os.path.isfile(os.path.join(h, holdout_manifest.SEAL_NAME)) \
            or not os.path.isdir(os.path.join(h, "sealed")):
        raise KitError(LEAK_CLEAR_NEEDS_MSG)
    diag = leakdiag(h, scan_roots=scan_roots, repo=repo, home=home,
                    setup_time=setup_time)
    scans = holdout_manifest._load_scans(h) or []
    named = {cid for scan in scans for cid in scan["hit_case_ids"]}
    named |= {cid for cid, _, reasons in holdout_manifest.retired_matches(h)
              if any(r.startswith("leakscan:") for r in reasons)}
    cases, cleared, kept = {}, [], []
    for cid in holdout_kit.case_ids(h):
        if cid not in named:
            continue
        slot = _case_slot(h, cid)
        cause = diag.get(slot, {}).get("cause", "exposed")
        if cause == "exposed":
            kept.append(slot)
            continue
        cases[cid] = {"slot": slot, "cause": cause,
                      "identity": holdout_manifest.case_identity(h, cid)}
        cleared.append(slot)
    if cases:
        holdout_manifest.append_clearance(h, cases)
    order = list(holdout_kit.SLOTS)
    cleared.sort(key=order.index)
    kept.sort(key=order.index)
    print("leak-clear cleared=%s kept=%s" % (",".join(cleared) or "none",
                                             ",".join(kept) or "none"))
    return cleared, kept


def _case_slot(h, cid):
    key = holdout_kit.load_json(os.path.join(h, "sealed", "keys", cid,
                                             "key.json"), what="a key.json")
    return key.get("slot")


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
                         holdout_kit.LEAK_WAIVER,
                         holdout_manifest.LEAK_CLEARED_RELPATH,
                         "AUTOPILOT.json")
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
    elif name == "leakdiag":
        p = sub.add_parser(name, help="sort leak-scan matches per slot in "
                                      "fixed words (reads only; never "
                                      "records or retires)")
        p.add_argument("--repo", metavar="PATH",
                       help="the tuning repo (tree and git log -p --all)")
        p.add_argument("--from-archive", action="store_true",
                       help="build the probes from the decrypted archive "
                            "(after scrub)")
    elif name == "leak-clear":
        p = sub.add_parser(name, help="record, append-only, that the leak-"
                                      "named cases leakdiag does not call "
                                      "exposed are cleared (owner rule)")
        p.add_argument("--repo", metavar="PATH",
                       help="the tuning repo (tree and git log -p --all)")
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


def _cmd_leakdiag(args):
    result = leakdiag(args.folder, repo=args.repo,
                      from_archive=args.from_archive)
    for slot, r in result.items():
        print("slot %s: cause=%s where=%s probe=%s when=%s" % (
            slot, r["cause"], ",".join(r["where"]) or "none",
            ",".join(r["probe"]) or "none", ",".join(r["when"]) or "none"))
    print(leakdiag_line(result))
    return 0


def _cmd_leak_clear(args):
    leak_clear(args.folder, repo=args.repo)
    return 0


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
    "leakdiag": _cmd_leakdiag,
    "leak-clear": _cmd_leak_clear,
    "scrub": _cmd_scrub,
}


def cmd(args):
    _refuse()
    handler = _HANDLERS.get(args.cmd)
    if handler is None:
        raise KitError("unknown archive command")
    return handler(args)
