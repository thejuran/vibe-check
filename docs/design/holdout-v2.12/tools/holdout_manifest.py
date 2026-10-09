"""holdout_manifest.py — keyed hashes and the public seal manifest for the
v2.12 holdout.

What is committed, and why it reveals nothing:

  * Every case is reduced to a deterministic listing of its sealed files:
    one line "<relpath under sealed/>\\0<sha256 of the file>\\n" for every
    regular file under sealed/cases/<ID>/ and sealed/keys/<ID>/, the lines
    sorted bytewise. The listing covers the base tree, the diff, the answer
    key, the proof and its recorded results, the cross-check verdict and the
    provenance.
  * That listing is hashed with HMAC-SHA256 under a private 256-bit key. The
    key is 32 random bytes written once to sealed/HMAC-KEY (mode 0600). It
    never leaves the holdout: it is archived with the plaintext and scrubbed
    with it. A plain SHA-256 of a known commit or a known diff could be
    confirmed by anyone who guesses the candidate; a keyed hash cannot.
  * SEAL.json (the only file that is ever copied into the repo) carries, per
    opaque case ID, the slot and that keyed hash; plus a SHA-256 commitment to
    the key, the schema, the milestone, the status, a fixed description of
    the construction, and (after encryption) the archive's SHA-256. No file
    names, repo names, dates or other metadata. public_shape_problems is the
    allowlist that enforces this.
  * The per-file inventory (sealed/INVENTORY.json) is private: it lives inside
    the archive and lets the Phase-55 `rehash` name exactly which file is
    mismatched, missing or extra. The files that live in sealed/ but are not
    case content are holdout_kit.SEALED_PRIVATE; this module binds that tuple
    once (_private_names) and both the inventory writer and rehash filter
    through that one name.

Ledgers that live in the holdout folder (never archived, never public):

  * LEAKSCAN.json — written by leakscan; publish refuses unless the last scan
    was clean, was taken against the current SEAL.json bytes, and no case a
    scan ever named is still sealed.
  * RETIRED.json — ID-independent content fingerprints of every case a leak
    scan named or the owner withdrew. publish (and seal) refuse any current
    case that matches one, so a retired change cannot come back under a new
    opaque ID.
  * LEAK-WAIVER.json — dry run only (owner decision, 51-09): written by
    `autopilot --dry-run` after a scan named dummy cases and a later fresh
    scan against the same seal came back clean; it keeps those cases,
    marked `leak: waived (dry-run)`. It is a dry-run marker, so every real
    path refuses the folder, and only leak_ledger_problems(dry_run=True)
    reads it.

Commands registered in holdout_kit.COMMANDS: seal-build, rehash, extract,
seal-order, publish, retire, resume-check. Every one refuses inside a
Claude-spawned shell except seal-order and resume-check: they touch no
holdout content (seal-order reads the tuning repo's git history; resume-check
reads one owner reply from stdin and never echoes it), and the tuning side
legitimately runs both.
"""

import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import stat
import sys
import time

import holdout_kit

KitError = holdout_kit.KitError

SEAL_SCHEMA = "vibe-check-holdout-seal/2"
MILESTONE = "v2.12"
SEAL_NAME = "SEAL.json"
SEAL_RELPATH = "docs/design/holdout-v2.12/SEAL.json"
PUBLIC_KEYS = frozenset({"schema", "milestone", "status", "mac",
                         "key_commitment_sha256", "cases", "archive_sha256"})
# archive_sha256 is added by encrypt after the seal is built.
REQUIRED_KEYS = PUBLIC_KEYS - {"archive_sha256"}
CASE_KEYS = frozenset({"slot", "hmac"})
MAX_SEAL_BYTES = 16384
MAC_DESCRIPTION = ("HMAC-SHA256(key, sorted lines of '<relpath>\\0<sha256(file)>"
                   "\\n' over sealed/cases/<id>/** and sealed/keys/<id>/**); "
                   "key committed as SHA-256(key)")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

# The one binding of the names that live in sealed/ but are not case content.
# write_inventory and rehash_folder both filter through this name.
_private_names = holdout_kit.SEALED_PRIVATE
# Positions in SEALED_PRIVATE: the key file and the inventory file.
_KEY_NAME = holdout_kit.SEALED_PRIVATE[0]
_INVENTORY_NAME = holdout_kit.SEALED_PRIVATE[1]


def _sealed(folder):
    return holdout_kit.sealed_dir(folder)


def _join_rel(root, rel):
    return os.path.join(root, *rel.split("/"))


# ---------------------------------------------------------------- serialization


def case_serialization(folder, case_id):
    """Deterministic listing of one case's sealed files (bytes).

    One line "<relpath from sealed/>\\0<sha256 hex>\\n" per regular file under
    sealed/cases/<ID>/ and sealed/keys/<ID>/, sorted bytewise. A symlink or a
    special file anywhere in either tree, or a missing tree, is a KitError.
    """
    if not isinstance(case_id, str) or not holdout_kit.ID_RE.match(case_id):
        raise KitError("not an opaque case id")
    sealed = _sealed(folder)
    lines = []
    for part in ("cases", "keys"):
        root = os.path.join(sealed, part, case_id)
        if os.path.islink(root):
            raise KitError("a symbolic link was found under %s/%s; remove it "
                           "and run this again" % (part, case_id))
        if not os.path.isdir(root):
            raise KitError("case %s is incomplete (%s/ missing)"
                           % (case_id, part))
        for rel in holdout_kit.walk_regular(root):
            relpath = "%s/%s/%s" % (part, case_id, rel)
            digest = holdout_kit.sha256_file(_join_rel(root, rel))
            lines.append(("%s\0%s\n" % (relpath, digest)).encode("utf-8"))
    return b"".join(sorted(lines))


def case_hmac(key, folder, case_id):
    """HMAC-SHA256 (hex) of case_serialization under `key`."""
    return holdout_kit.hmac_hex(key, case_serialization(folder, case_id))


# ---------------------------------------------------------------- key


def _read_key(sealed):
    path = os.path.join(sealed, _KEY_NAME)
    try:
        mode = os.lstat(path).st_mode
    except FileNotFoundError:
        raise KitError("HMAC key missing under sealed/; the folder is not a "
                       "complete sealed holdout")
    except OSError:
        raise KitError("HMAC key file is malformed (unreadable)")
    if not stat.S_ISREG(mode):
        raise KitError("HMAC key file is malformed (not a regular file)")
    try:
        with open(path, "r", encoding="ascii") as fh:
            text = fh.read().strip()
    except (OSError, UnicodeDecodeError):
        raise KitError("HMAC key file is malformed")
    if not _HEX64.match(text):
        raise KitError("HMAC key file is malformed")
    return bytes.fromhex(text)


def load_or_create_key(folder):
    """The 32-byte HMAC key at sealed/HMAC-KEY, created once (mode 0600)."""
    sealed = _sealed(folder)
    path = os.path.join(sealed, _KEY_NAME)
    if os.path.lexists(path):
        return _read_key(sealed)
    if not os.path.isdir(sealed):
        raise KitError("sealed/ is missing; run setup first")
    key = secrets.token_bytes(32)
    tmp = os.path.join(sealed, ".%s.%s.tmp" % (_KEY_NAME, secrets.token_hex(4)))
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="ascii") as fh:
            fh.write(key.hex() + "\n")
        os.replace(tmp, path)
        os.chmod(path, 0o600)
    except OSError:
        raise KitError("cannot write the HMAC key")
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
    return key


# ---------------------------------------------------------------- seal


def _case_slot(sealed, case_id):
    data = holdout_kit.load_json(
        os.path.join(sealed, "keys", case_id, "key.json"),
        required={"slot": str}, what="key.json of case %s" % case_id)
    return data["slot"]


def _key_dir_ids(sealed):
    keys = os.path.join(sealed, "keys")
    try:
        names = os.listdir(keys)
    except OSError:
        raise KitError("sealed/keys is missing or unreadable")
    registry = os.path.join(keys, holdout_kit.XCHECK_REGISTRY)
    if not os.path.islink(registry) and os.path.isfile(registry):
        names.remove(holdout_kit.XCHECK_REGISTRY)
    return sorted(names)


def build_seal(folder):
    """The public seal dict (without archive_sha256) for the six cases."""
    sealed = _sealed(folder)
    ids = holdout_kit.case_ids(folder)
    if _key_dir_ids(sealed) != ids:
        raise KitError("sealed/cases and sealed/keys do not hold the same "
                       "case ids")
    slots = {cid: _case_slot(sealed, cid) for cid in ids}
    if sorted(slots.values()) != sorted(holdout_kit.SLOTS):
        raise KitError("the sealed cases do not fill the six slots exactly "
                       "once (%d case(s) found)" % len(ids))
    key = load_or_create_key(folder)
    cases = {cid: {"slot": slots[cid], "hmac": case_hmac(key, folder, cid)}
             for cid in ids}
    return {"schema": SEAL_SCHEMA, "milestone": MILESTONE, "status": "sealed",
            "mac": MAC_DESCRIPTION,
            "key_commitment_sha256": holdout_kit.sha256_bytes(key),
            "cases": cases}


def _content_files(sealed):
    """Every regular file under sealed/ except the private top-level names."""
    return [rel for rel in holdout_kit.walk_regular(sealed)
            if rel not in _private_names]


def write_inventory(folder):
    """Write sealed/INVENTORY.json = {"files": {relpath: sha256}}; return it."""
    sealed = _sealed(folder)
    files = {rel: holdout_kit.sha256_file(_join_rel(sealed, rel))
             for rel in _content_files(sealed)}
    inventory = {"files": files}
    holdout_kit.write_json_atomic(os.path.join(sealed, _INVENTORY_NAME),
                                  inventory)
    return inventory


def _is_hex64(value):
    return isinstance(value, str) and bool(_HEX64.match(value))


def public_shape_problems(seal):
    """[] when `seal` is exactly the public shape; otherwise one line per
    problem. Problem lines never echo a value from the seal."""
    if not isinstance(seal, dict):
        return ["SEAL.json is not an object"]
    problems = []
    for key in sorted(k for k in seal if isinstance(k, str)):
        if key not in PUBLIC_KEYS:
            problems.append("unexpected key: %s" % key)
    if any(not isinstance(k, str) for k in seal):
        problems.append("unexpected key: (not a string)")
    for key in sorted(REQUIRED_KEYS):
        if key not in seal:
            problems.append("missing key: %s" % key)
    if "schema" in seal and seal["schema"] != SEAL_SCHEMA:
        problems.append("schema is not %s" % SEAL_SCHEMA)
    if "milestone" in seal and seal["milestone"] != MILESTONE:
        problems.append("milestone is not %s" % MILESTONE)
    if "status" in seal and seal["status"] != "sealed":
        problems.append("status is not sealed")
    if "mac" in seal and seal["mac"] != MAC_DESCRIPTION:
        problems.append("mac description differs from the kit's")
    for key in ("key_commitment_sha256", "archive_sha256"):
        if key in seal and not _is_hex64(seal[key]):
            problems.append("hash format: %s" % key)
    cases = seal.get("cases")
    if "cases" in seal and not isinstance(cases, dict):
        problems.append("cases is not an object")
        cases = None
    slots = []
    for cid, entry in sorted((cases or {}).items(), key=lambda kv: str(kv[0])):
        if not isinstance(cid, str) or not holdout_kit.ID_RE.match(cid):
            problems.append("a case key is not an opaque id")
            label = "(not an opaque id)"
        else:
            label = cid
        if not isinstance(entry, dict):
            problems.append("case %s: not an object" % label)
            continue
        if set(entry) - CASE_KEYS:
            problems.append("case %s: unexpected key" % label)
        if CASE_KEYS - set(entry):
            problems.append("case %s: missing key" % label)
        slot = entry.get("slot")
        if isinstance(slot, str) and slot in holdout_kit.SLOTS:
            slots.append(slot)
        else:
            problems.append("case %s: slot is not one of the six" % label)
        if "hmac" in entry and not _is_hex64(entry["hmac"]):
            problems.append("hash format: case %s" % label)
    if cases is not None and sorted(slots) != sorted(holdout_kit.SLOTS):
        problems.append("slots: the cases must hold each of the six slots "
                        "exactly once")
    try:
        size = len(json.dumps(seal, indent=2, sort_keys=True).encode("utf-8"))
    except (TypeError, ValueError):
        problems.append("SEAL.json is not plain JSON")
    else:
        if size >= MAX_SEAL_BYTES:
            problems.append("SEAL.json is too large (%d bytes)" % size)
    return problems


# ---------------------------------------------------------------- dry run

DRY_SEAL_STATUS = "dry-run"
# Keys only a dry-run seal carries: at the top, "mode"; per case, the
# synthetic-agreement record, the real judge's outcome and a waived
# owner retirement. public_shape_problems rejects every one of them.
DRY_SEAL_TOP_KEYS = frozenset({"mode"})
DRY_SEAL_CASE_KEYS = frozenset({"agreement", "judge_outcome",
                                "retired_material"})
NOT_A_DRY_FOLDER_MSG = ("rehash --dry-run needs a dry-run folder (a valid "
                        "DRY-RUN.json beside sealed/); nothing was verified")


def is_dry_run_seal(seal):
    """True when `seal` carries any dry-run mark (status, mode or a per-case
    dry-run key). Never raises."""
    if not isinstance(seal, dict):
        return False
    if seal.get("status") == DRY_SEAL_STATUS or "mode" in seal:
        return True
    cases = seal.get("cases")
    if isinstance(cases, dict):
        for entry in cases.values():
            if isinstance(entry, dict) and set(entry) & DRY_SEAL_CASE_KEYS:
                return True
    return False


def mark_dry_run_seal(seal, judged=None, synthetic=(), waived=()):
    """Mark a freshly built seal as a dry-run seal, in place; return it.
    `judged` maps case IDs to the real judge's outcome ("agreed" or
    "disagreed"), `synthetic` lists the IDs sealed on synthetic agreement and
    `waived` the IDs whose owner retirement the dry run did not replace."""
    seal["status"] = DRY_SEAL_STATUS
    seal["mode"] = "dry-run"
    for cid, entry in seal["cases"].items():
        if cid in (judged or {}):
            entry["judge_outcome"] = judged[cid]
        if cid in synthetic:
            entry["agreement"] = "synthetic"
        if cid in waived:
            entry["retired_material"] = "waived"
    return seal


def _dry_seal_public_view(seal):
    """The seal with its dry-run marks removed, for the shape check a
    dry-run rehash still runs."""
    view = {k: v for k, v in seal.items() if k not in DRY_SEAL_TOP_KEYS}
    if view.get("status") == DRY_SEAL_STATUS:
        view["status"] = "sealed"
    cases = view.get("cases")
    if isinstance(cases, dict):
        view["cases"] = {
            cid: ({k: v for k, v in e.items() if k not in DRY_SEAL_CASE_KEYS}
                  if isinstance(e, dict) else e)
            for cid, e in cases.items()}
    return view


def dry_run_problems(folder, seal):
    """[DRY_RUN_REFUSED_MSG] when the folder holds a dry-run marker or the
    seal is a dry-run seal; [] otherwise. The real-run gate of publish,
    rehash and seal-build."""
    if holdout_kit.dry_run_markers_present(folder) or is_dry_run_seal(seal):
        return [holdout_kit.DRY_RUN_REFUSED_MSG]
    return []


# ---------------------------------------------------------------- rehash

# Path components rehash may print as they are; anything else is shown as
# "<file>" so a stray file's name can never carry case details into output.
_GENERIC_PARTS = (frozenset({"cases", "keys", "proof", "run"})
                  | holdout_kit.CASE_FILES | holdout_kit.KEY_FILES
                  | frozenset(holdout_kit.SEALED_PRIVATE)
                  | frozenset({holdout_kit.XCHECK_REGISTRY}))


def _generic(rel):
    parts = []
    for part in rel.split("/"):
        if part in _GENERIC_PARTS or holdout_kit.ID_RE.match(part):
            parts.append(part)
        else:
            parts.append("<file>")
    return "/".join(parts)


def _listdir_ids(path):
    try:
        names = os.listdir(path)
    except OSError:
        return set()
    return {n for n in names if holdout_kit.ID_RE.match(n)}


def rehash_folder(seal_path, sealed_folder, dry_run=False):
    """Verify a decrypted sealed/ folder against SEAL.json.

    Returns {"ok", "commitment_ok", "cases": {ID: bool}, "mismatched",
    "missing", "extra", "missing_cases", "extra_cases"}; file lists hold
    generic relpaths (opaque IDs and allowlisted names only). A missing key,
    a missing inventory, a symlink or a seal without the public shape is a
    KitError: nothing is verified then.

    Without dry_run (Phase 55, the real run's encrypt) a dry-run seal, or a
    dry-run marker beside sealed/, is refused with DRY_RUN_REFUSED_MSG.
    dry_run=True is for the dry run verifying itself (the caller has checked
    the folder's marker): a dry-run seal is shape-checked without its marks.
    """
    seal = holdout_kit.load_json(seal_path, what="SEAL.json")
    sealed = os.path.abspath(sealed_folder)
    folder = os.path.dirname(sealed)
    if not dry_run and dry_run_problems(folder, seal):
        raise KitError(holdout_kit.DRY_RUN_REFUSED_MSG)
    shape = public_shape_problems(
        _dry_seal_public_view(seal) if dry_run and is_dry_run_seal(seal)
        else seal)
    if shape:
        raise KitError("SEAL.json does not have the public shape (%s)"
                       % shape[0])
    if os.path.basename(sealed) != "sealed" or not os.path.isdir(sealed) \
            or os.path.islink(sealed):
        raise KitError("--sealed must be a folder named sealed")
    try:
        holdout_kit.walk_regular(sealed)
    except KitError:
        raise KitError("symlink refused: a link or special file is under "
                       "sealed/; nothing was verified")
    key = _read_key(sealed)
    commitment_ok = hmac.compare_digest(holdout_kit.sha256_bytes(key),
                                        seal["key_commitment_sha256"])
    results, missing_cases = {}, []
    for cid in sorted(seal["cases"]):
        present = all(os.path.isdir(os.path.join(sealed, part, cid))
                      for part in ("cases", "keys"))
        if not present:
            results[cid] = False
            missing_cases.append(cid)
            continue
        got = case_hmac(key, folder, cid)
        results[cid] = hmac.compare_digest(got, seal["cases"][cid]["hmac"])
    on_disk = (_listdir_ids(os.path.join(sealed, "cases"))
               | _listdir_ids(os.path.join(sealed, "keys")))
    extra_cases = sorted(on_disk - set(seal["cases"]))
    inventory = holdout_kit.load_json(os.path.join(sealed, _INVENTORY_NAME),
                                      required={"files": dict},
                                      what="sealed/INVENTORY.json")
    recorded = inventory["files"]
    actual = {rel: holdout_kit.sha256_file(_join_rel(sealed, rel))
              for rel in _content_files(sealed)}
    mismatched = sorted(_generic(r) for r in set(recorded) & set(actual)
                        if recorded[r] != actual[r])
    missing = sorted(_generic(r) for r in set(recorded) - set(actual))
    extra = sorted(_generic(r) for r in set(actual) - set(recorded))
    ok = (commitment_ok and all(results.values()) and not mismatched
          and not missing and not extra and not missing_cases
          and not extra_cases)
    return {"ok": ok, "commitment_ok": commitment_ok, "cases": results,
            "mismatched": mismatched, "missing": missing, "extra": extra,
            "missing_cases": missing_cases, "extra_cases": extra_cases,
            "inventory_files": len(recorded)}


# ---------------------------------------------------------------- extract


def extract_part(sealed_folder, part, dest):
    """Copy only sealed/<part>/ to <dest>/<part>/; return the file count.

    Phase 55 gives the review runner cases/ and the scorer keys/, never both.
    """
    if part not in ("cases", "keys"):
        raise KitError("extract copies exactly one part: cases or keys")
    src = os.path.join(sealed_folder, part)
    if os.path.islink(src) or not os.path.isdir(src):
        raise KitError("sealed/%s is missing or not a folder" % part)
    rels = holdout_kit.walk_regular(src)
    target = os.path.join(dest, part)
    if os.path.lexists(target):
        raise KitError("%s/ already exists under the destination; choose an "
                       "empty destination" % part)
    try:
        for rel in rels:
            out = _join_rel(target, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copy2(_join_rel(src, rel), out, follow_symlinks=False)
    except OSError:
        raise KitError("cannot copy %s/ to the destination" % part)
    return len(rels)


# ---------------------------------------------------------------- seal-order


def seal_order_problems(repo, before=None):
    """[] when SEAL.json has exactly one commit across every branch, tag and
    remote (full history), and that commit is an ancestor of `before`."""
    proc = holdout_kit.run_argv(
        ["git", "-C", repo, "log", "--format=%H", "--full-history",
         "--simplify-merges", "--topo-order", "--branches", "--tags",
         "--remotes", "--", SEAL_RELPATH], timeout=60)
    if proc.returncode != 0:
        return ["cannot read the git history of the repo"]
    revs = proc.stdout.decode("utf-8", "replace").split()
    if not revs:
        return ["SEAL.json has no commit"]
    if len(revs) != 1:
        return ["SEAL.json has %d commits; expected exactly 1" % len(revs)]
    if before is None:
        return []
    check = holdout_kit.run_argv(
        ["git", "-C", repo, "rev-parse", "--verify", "--quiet",
         str(before) + "^{commit}"], timeout=60)
    if check.returncode != 0:
        return ["cannot resolve %s to a commit" % before]
    anc = holdout_kit.run_argv(
        ["git", "-C", repo, "merge-base", "--is-ancestor", revs[0],
         str(before)], timeout=60)
    if anc.returncode == 0:
        return []
    if anc.returncode == 1:
        return ["seal commit is not an ancestor of %s" % before]
    return ["cannot check ancestry against %s" % before]


# ---------------------------------------------------------------- leak ledger

LEAKSCAN_RELPATH = "LEAKSCAN.json"
LEAKSCAN_SCHEMA = "vibe-check-holdout-leakscan/1"
NO_SCAN_MSG = "no leak scan recorded; run leakscan before publish"
LEAK_FOUND_MSG = ("the last leak scan found holdout text on the tuning side; "
                  "replace the slots it named, re-seal, and scan again")
LEAK_STALE_MSG = ("the last leak scan predates the current seal; run leakscan "
                  "again")
LEAK_NOT_REPLACED_MSG = ("case %s (%s) was named by a leak scan on %s and has "
                         "not been replaced; deleting the matched files is "
                         "cleanup, not a remedy: replace the slot through the "
                         "finder and a fresh cross-check, then re-seal")


def _scan_ok(scan):
    if not isinstance(scan, dict):
        return False
    hits = scan.get("hits")
    ids = scan.get("hit_case_ids")
    return (isinstance(hits, int) and not isinstance(hits, bool)
            and hits >= 0 and isinstance(scan.get("at"), str)
            and isinstance(ids, list)
            and all(isinstance(i, str) for i in ids)
            and (scan.get("seal_sha256") is None
                 or isinstance(scan.get("seal_sha256"), str)))


def _load_scans(folder):
    """The LEAKSCAN.json scan list, or None when it is missing or
    malformed."""
    try:
        with open(os.path.join(folder, LEAKSCAN_RELPATH), "r",
                  encoding="utf-8") as fh:
            ledger = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(ledger, dict) or ledger.get("schema") != LEAKSCAN_SCHEMA:
        return None
    scans = ledger.get("scans")
    if not isinstance(scans, list) or not scans \
            or not all(_scan_ok(s) for s in scans):
        return None
    return scans


def leak_ledger_problems(folder, seal, dry_run=False):
    """[] only when the last leak scan was clean, was taken against the
    current SEAL.json bytes, and no case any scan named is still sealed.

    dry_run=True is for the dry run checking itself (the caller runs in
    dry-run mode): a case named by an earlier scan that a valid
    LEAK-WAIVER.json (leak_waiver_problems == []) keeps is not reported.
    Without dry_run the waiver is never read; the real run's leak path is
    unchanged."""
    scans = _load_scans(folder)
    if scans is None:
        return [NO_SCAN_MSG]
    waived = set()
    if dry_run and not leak_waiver_problems(folder, seal):
        waived = set(_load_waiver(folder)["cases"])
    problems = []
    last = scans[-1]
    if last["hits"] != 0:
        problems.append(LEAK_FOUND_MSG)
    seal_path = os.path.join(folder, SEAL_NAME)
    current = (holdout_kit.sha256_file(seal_path)
               if os.path.isfile(seal_path) else None)
    if current is None or last.get("seal_sha256") != current:
        problems.append(LEAK_STALE_MSG)
    cases = seal.get("cases") if isinstance(seal, dict) else None
    cases = cases if isinstance(cases, dict) else {}
    # The LATEST scan that named each case: a clearance made before a later
    # scan named the case again does not cover that later exposure.
    named = {}
    for scan in scans:
        for cid in scan["hit_case_ids"]:
            named[cid] = max(named.get(cid, scan["at"]), scan["at"])
    for cid in sorted(named):
        if cid in cases and cid not in waived \
                and not _cleared_for_seal(folder, cid, named[cid], current):
            entry = cases[cid]
            slot = entry.get("slot", "?") if isinstance(entry, dict) else "?"
            problems.append(LEAK_NOT_REPLACED_MSG % (slot, cid, named[cid]))
    return problems


# ---------------------------------------------------------------- dry-run leak waiver

# Owner-approved dry-run rule (51-09): a leak scan that names dummy cases is
# recorded as usual (LEAKSCAN.json keeps the hit, RETIRED.json keeps the
# fingerprints). Once the owner has removed the leaked copy and a FRESH scan
# against the same seal comes back clean, the dry run may finish without
# replacing those cases: LEAK-WAIVER.json keeps them, each marked
# `leak: waived (dry-run)`. It is a dry-run marker (holdout_kit
# DRY_RUN_MARKERS), so real seal, seal-build, publish and rehash refuse any
# folder that holds it, and only leak_ledger_problems(dry_run=True) reads it.
LEAK_WAIVED = "waived (dry-run)"
WAIVER_KEYS = frozenset({"schema", "mode", "folder", "seal_sha256",
                         "clean_scan_at", "cases"})
WAIVER_CASE_KEYS = frozenset({"slot", "leak", "named_at"})
WAIVER_NOT_DRY_MSG = ("a leak waiver is for a dry run only (a valid "
                      "DRY-RUN.json and a dry-run SEAL.json); nothing was "
                      "waived")
WAIVER_NOT_CLEAN_MSG = ("the last leak scan was not clean against the current "
                        "seal; remove the leaked copy and scan again before a "
                        "dry-run leak can be waived")
WAIVER_NOTHING_MSG = "no sealed case was named by a leak scan; nothing to waive"
WAIVER_INVALID_MSG = "LEAK-WAIVER.json does not match this folder, seal or ledger"


def _load_waiver(folder):
    path = os.path.join(folder, holdout_kit.LEAK_WAIVER)
    if os.path.islink(path) or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _waiver_basis(folder, seal):
    """(clean last scan, {named-and-still-sealed ID: (slot, first named at)})
    or a problem line. Shared by the writer and the checker."""
    h = os.path.realpath(folder)
    if not holdout_kit.dry_run_marker_ok(h) or not is_dry_run_seal(seal):
        return WAIVER_NOT_DRY_MSG
    scans = _load_scans(h)
    seal_path = os.path.join(h, SEAL_NAME)
    current = (holdout_kit.sha256_file(seal_path)
               if os.path.isfile(seal_path) else None)
    if scans is None or current is None:
        return WAIVER_NOT_CLEAN_MSG
    last = scans[-1]
    if last["hits"] != 0 or last.get("seal_sha256") != current \
            or last["hit_case_ids"]:
        return WAIVER_NOT_CLEAN_MSG
    cases = seal.get("cases") if isinstance(seal.get("cases"), dict) else {}
    named = {}
    for scan in scans:
        for cid in scan["hit_case_ids"]:
            if cid in cases and cid not in named:
                entry = cases[cid]
                slot = entry.get("slot") if isinstance(entry, dict) else None
                named[cid] = (slot if isinstance(slot, str) else "?",
                              scan["at"])
    if not named:
        return WAIVER_NOTHING_MSG
    return last, named, current


def write_leak_waiver(folder, seal):
    """Dry run only: write LEAK-WAIVER.json keeping every sealed case a leak
    scan named, once the LAST scan (against the current SEAL.json bytes) is
    clean. Refuses (KitError, nothing written) outside a marked dry-run
    folder with a dry-run seal, without a clean last scan, or when no sealed
    case was named. Returns {ID: slot} of the waived cases."""
    basis = _waiver_basis(folder, seal)
    if isinstance(basis, str):
        raise KitError(basis)
    last, named, current = basis
    h = os.path.realpath(folder)
    path = os.path.join(h, holdout_kit.LEAK_WAIVER)
    if os.path.islink(path):
        raise KitError("LEAK-WAIVER.json is a symbolic link; remove it and "
                       "run this again")
    holdout_kit.write_json_atomic(path, {
        "schema": holdout_kit.LEAK_WAIVER_SCHEMA, "mode": "dry-run",
        "folder": h, "seal_sha256": current, "clean_scan_at": last["at"],
        "cases": {cid: {"slot": slot, "leak": LEAK_WAIVED, "named_at": at}
                  for cid, (slot, at) in sorted(named.items())}})
    return {cid: slot for cid, (slot, _) in named.items()}


def leak_waiver_problems(folder, seal):
    """[] only when LEAK-WAIVER.json is exactly what write_leak_waiver would
    write now: a marked dry-run folder and a dry-run seal, the last scan
    clean against the current SEAL.json bytes (and the one the waiver
    names), and the waived cases exactly the sealed cases a scan named, each
    marked `leak: waived (dry-run)`."""
    data = _load_waiver(folder)
    if data is None:
        return ["no LEAK-WAIVER.json"]
    basis = _waiver_basis(folder, seal)
    if isinstance(basis, str):
        return [basis]
    last, named, current = basis
    cases = data.get("cases")
    if set(data) != WAIVER_KEYS \
            or data.get("schema") != holdout_kit.LEAK_WAIVER_SCHEMA \
            or data.get("mode") != "dry-run" \
            or data.get("folder") != os.path.realpath(folder) \
            or data.get("seal_sha256") != current \
            or data.get("clean_scan_at") != last["at"] \
            or not isinstance(cases, dict) or set(cases) != set(named):
        return [WAIVER_INVALID_MSG]
    for cid, entry in cases.items():
        if not isinstance(entry, dict) or set(entry) != WAIVER_CASE_KEYS \
                or entry["leak"] != LEAK_WAIVED \
                or entry["slot"] != named[cid][0] \
                or entry["named_at"] != named[cid][1]:
            return [WAIVER_INVALID_MSG]
    return []


# ---------------------------------------------------------------- retirement

RETIRED_RELPATH = "RETIRED.json"
RETIRED_SCHEMA = "vibe-check-holdout-retired/1"
RETIRED_REVISIONS_RELPATH = "work/RETIRED-REVISIONS.json"
RETIRED_REVISIONS_SCHEMA = "vibe-check-holdout-retired-revisions/1"
RETIRE_REASONS = ("leakscan", "owner")
_SOURCE_KEYS = ("repo_name", "base_rev", "feature_rev")
_HASH_FIELDS = (("diff_sha256", "diff"), ("lines_sha256", "lines"),
                ("key_sha256", "key"))
# key.json fields that name the case rather than its content.
_KEY_IDENTITY_FIELDS = ("slot", "id", "case_id")
RETIRED_MSG = ("case %s (%s) reuses material retired on %s (%s); a retired "
               "change cannot return under a new ID: replace it with a "
               "different change (different revision AND different diff)")
RETIRED_MALFORMED_MSG = ("RETIRED.json is malformed; repair the ledger (never "
                         "delete it) and run this again")
_NO_CONTENT_MSG = ("case %s has no sealed content to fingerprint; retire "
                   "BEFORE deleting it")


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _hunk_counts(header):
    m = re.match(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", header)
    if not m:
        return None
    old = int(m.group(1)) if m.group(1) is not None else 1
    new = int(m.group(2)) if m.group(2) is not None else 1
    return old, new


def _diff_lines_sha256(data):
    """sha256 over the sorted, de-duplicated set of added/removed lines of a
    unified diff, marker removed and whitespace stripped. Context lines and
    headers are ignored (hunks are walked by their line counts), so the same
    change regenerated with a different -U context or re-indented matches.
    None when the diff has no non-blank changed line."""
    text = data.decode("utf-8", "replace")
    changed = set()
    old = new = 0
    for line in text.split("\n"):
        if old > 0 or new > 0:
            tag = line[:1]
            if tag == "\\":
                continue
            if tag == "-":
                old -= 1
            elif tag == "+":
                new -= 1
            else:
                old -= 1
                new -= 1
                continue
            stripped = line[1:].strip()
            if stripped:
                changed.add(stripped)
            continue
        if line.startswith("@@"):
            counts = _hunk_counts(line)
            if counts:
                old, new = counts
    if not changed:
        return None
    digest = hashlib.sha256()
    for item in sorted(changed):
        digest.update(item.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _load_dict_or_none(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def case_fingerprint(folder, case_id):
    """ID-independent content identity of one case.

    {"source": {repo_name, base_rev, feature_rev} from provenance.json (null
    when absent), "diff_sha256", "lines_sha256" (see _diff_lines_sha256),
    "key_sha256" (key.json minus slot/id/case_id, canonical JSON)}. case.json
    is not hashed because it carries the ID; the ID never enters any field.
    """
    sealed = _sealed(folder)
    cdir = os.path.join(sealed, "cases", case_id)
    kdir = os.path.join(sealed, "keys", case_id)
    for root in (cdir, kdir):
        if os.path.islink(root):
            raise KitError("a symbolic link was found in a case; remove it "
                           "and run this again")
        if os.path.isdir(root):
            holdout_kit.walk_regular(root)
    prov = _load_dict_or_none(os.path.join(kdir, "provenance.json")) or {}
    source = {}
    for k in _SOURCE_KEYS:
        v = prov.get(k)
        source[k] = v if isinstance(v, str) and v else None
    diff_path = os.path.join(cdir, "change.diff")
    if os.path.isfile(diff_path):
        diff_sha = holdout_kit.sha256_file(diff_path)
        try:
            with open(diff_path, "rb") as fh:
                lines_sha = _diff_lines_sha256(fh.read())
        except OSError:
            raise KitError("cannot read change.diff of case %s" % case_id)
    else:
        diff_sha = lines_sha = None
    key = _load_dict_or_none(os.path.join(kdir, "key.json"))
    if key is None:
        key_sha = None
    else:
        body = {k: v for k, v in key.items() if k not in _KEY_IDENTITY_FIELDS}
        key_sha = holdout_kit.sha256_bytes(json.dumps(
            body, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return {"source": source, "diff_sha256": diff_sha,
            "lines_sha256": lines_sha, "key_sha256": key_sha}


def _optional_hex(value):
    return value is None or _is_hex64(value)


def _entry_ok(entry):
    if not isinstance(entry, dict):
        return False
    if not all(isinstance(entry.get(k), str) for k in ("at", "slot",
                                                        "reason")):
        return False
    source = entry.get("source")
    if not isinstance(source, dict) or set(source) != set(_SOURCE_KEYS):
        return False
    if not all(v is None or isinstance(v, str) for v in source.values()):
        return False
    return all(f in entry and _optional_hex(entry[f])
               for f, _ in _HASH_FIELDS)


def _load_retired(folder):
    """The RETIRED.json ledger, strictly; a fresh empty ledger when absent."""
    path = os.path.join(folder, RETIRED_RELPATH)
    if not os.path.lexists(path):
        return {"schema": RETIRED_SCHEMA, "retired": []}
    if os.path.islink(path):
        raise KitError(RETIRED_MALFORMED_MSG)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            ledger = json.load(fh)
    except (OSError, ValueError):
        raise KitError(RETIRED_MALFORMED_MSG)
    if not isinstance(ledger, dict) or ledger.get("schema") != RETIRED_SCHEMA \
            or not isinstance(ledger.get("retired"), list) \
            or not all(_entry_ok(e) for e in ledger["retired"]):
        raise KitError(RETIRED_MALFORMED_MSG)
    return ledger


# Public name for the strict RETIRED.json loader (the autopilot reads it to
# decide whether a finished run can be proven from evidence alone).
load_retired = _load_retired


def _content_identity(entry):
    return (tuple(entry["source"][k] for k in _SOURCE_KEYS),
            entry["diff_sha256"], entry["lines_sha256"], entry["key_sha256"])


def _case_slot_lenient(sealed, case_id):
    key = _load_dict_or_none(os.path.join(sealed, "keys", case_id,
                                          "key.json")) or {}
    slot = key.get("slot")
    return slot if slot in holdout_kit.SLOTS else "?"


def sync_retired_revisions(folder):
    """Rewrite work/RETIRED-REVISIONS.json (the finder's skip list) from
    RETIRED.json; return the number of revisions listed."""
    ledger = _load_retired(folder)
    revisions = []
    for entry in ledger["retired"]:
        source = entry["source"]
        if not source.get("feature_rev"):
            continue
        rev = {k: source[k] for k in _SOURCE_KEYS}
        if rev not in revisions:
            revisions.append(rev)
    holdout_kit.write_json_atomic(
        os.path.join(folder, *RETIRED_REVISIONS_RELPATH.split("/")),
        {"schema": RETIRED_REVISIONS_SCHEMA, "revisions": revisions})
    return len(revisions)


def retire_case(folder, case_id, reason, content_folder=None):
    """Append the case's content fingerprint to <folder>/RETIRED.json.

    The fingerprint is read from `content_folder` (default: `folder`), so a
    leak scan over a decrypted copy can retire a case whose live plaintext is
    already scrubbed. Existing entries are never modified or removed; an
    identical fingerprint is not appended twice while an earlier entry for
    it is still in force; one a clearance voided is retired again with a
    fresh entry. Never writes a path, a line or any case text. Returns the
    ledger.
    """
    if reason not in RETIRE_REASONS:
        raise KitError("retire reason must be leakscan or owner")
    if not isinstance(case_id, str) or not holdout_kit.ID_RE.match(case_id):
        raise KitError("not an opaque case id")
    src = content_folder or folder
    sealed = _sealed(src)
    for part in ("cases", "keys"):
        root = os.path.join(sealed, part, case_id)
        if os.path.islink(root) or not os.path.isdir(root):
            raise KitError(_NO_CONTENT_MSG % case_id)
    ledger = _load_retired(folder)
    fp = case_fingerprint(src, case_id)
    if fp["diff_sha256"] is None or fp["key_sha256"] is None:
        raise KitError(_NO_CONTENT_MSG % case_id)
    entry = {"at": _now(), "slot": _case_slot_lenient(sealed, case_id),
             "reason": reason, "source": dict(fp["source"]),
             "diff_sha256": fp["diff_sha256"],
             "lines_sha256": fp["lines_sha256"],
             "key_sha256": fp["key_sha256"]}
    cleared = load_clearances(folder)
    seal_sha = _current_seal_sha(folder)
    if not any(_content_identity(e) == _content_identity(entry)
               and not _retirement_cleared(e, cleared, seal_sha)
               for e in ledger["retired"]):
        ledger["retired"].append(entry)
        holdout_kit.write_json_atomic(os.path.join(folder, RETIRED_RELPATH),
                                      ledger)
    sync_retired_revisions(folder)
    return ledger


def _matched_fields(fp, entry):
    matched = []
    mine, theirs = fp["source"], entry["source"]
    if all(mine.get(k) and theirs.get(k) for k in _SOURCE_KEYS) \
            and all(mine[k] == theirs[k] for k in _SOURCE_KEYS):
        matched.append("source")
    for field, label in _HASH_FIELDS:
        if fp[field] and entry[field] and fp[field] == entry[field]:
            matched.append(label)
    return matched


def retired_matches(folder):
    """[(ID, line, reasons)] for every current case whose content matches a
    retired entry: `line` is the case's RETIRED_MSG (from its first matching
    entry), `reasons` the set of retire reasons of every matching entry,
    each tagged ":exact" when that entry is this very case (every source
    revision, the diff, the changed lines and the key identical) and
    ":reused" when the case only reuses some of the entry's material."""
    ledger = _load_retired(folder)
    if not ledger["retired"]:
        return []
    cleared = load_clearances(folder)
    seal_sha = _current_seal_sha(folder)
    sealed = _sealed(folder)
    out = []
    for cid in holdout_kit.case_ids(folder):
        fp = case_fingerprint(folder, cid)
        line, reasons = None, set()
        for entry in ledger["retired"]:
            matched = _matched_fields(fp, entry)
            if not matched or _retirement_cleared(entry, cleared, seal_sha):
                continue
            ident = ({"source": dict(fp["source"]),
                      "diff_sha256": fp["diff_sha256"],
                      "lines_sha256": fp["lines_sha256"],
                      "key_sha256": fp["key_sha256"]})
            exact = (all(fp["source"].get(k) for k in _SOURCE_KEYS)
                     and _content_identity(entry) == _content_identity(ident))
            reasons.add("%s:%s" % (entry["reason"],
                                   "exact" if exact else "reused"))
            if line is None:
                line = RETIRED_MSG % (_case_slot_lenient(sealed, cid), cid,
                                      entry["at"], ",".join(matched))
        if line is not None:
            out.append((cid, line, reasons))
    return out


# ---------------------------------------------------------------- leak clearance
#
# Owner rule (2026-10-09): a case's own source code found outside tuning-side
# places is not a leak (holdout_archive.leakdiag decides; leak-clear writes).
# LEAK-CLEARED.json is append-only, like LEAKSCAN.json and RETIRED.json: a
# clearance names the cases it clears, their content identity and the
# SEAL.json it was made against. It lets a case a leak scan named stay in
# THAT seal, and voids a `leakscan` retirement of exactly that content.
# An `owner` retirement is never cleared.

LEAK_CLEARED_RELPATH = "LEAK-CLEARED.json"
LEAK_CLEARED_SCHEMA = "vibe-check-holdout-leak-cleared/1"
LEAK_CLEAR_RULE = "own-source-outside-tuning/2026-10-09"
CLEARED_MALFORMED_MSG = ("LEAK-CLEARED.json is malformed; repair it (never "
                         "delete it)")


def case_identity(folder, case_id):
    fp = case_fingerprint(folder, case_id)
    return {"source": dict(fp["source"]), "diff_sha256": fp["diff_sha256"],
            "lines_sha256": fp["lines_sha256"],
            "key_sha256": fp["key_sha256"]}


def _clearance_ok(entry):
    if not isinstance(entry, dict) or not isinstance(entry.get("at"), str) \
            or entry.get("rule") != LEAK_CLEAR_RULE \
            or not isinstance(entry.get("seal_sha256"), str) \
            or not isinstance(entry.get("cases"), dict):
        return False
    for cid, case in entry["cases"].items():
        if not holdout_kit.ID_RE.match(cid) or not isinstance(case, dict) \
                or case.get("slot") not in holdout_kit.SLOTS \
                or not isinstance(case.get("identity"), dict):
            return False
        try:
            _content_identity(case["identity"])
        except (KeyError, TypeError):
            return False
    return True


def load_clearances(folder):
    """The clearance list ([] when there is no file); KitError when it is
    malformed (never treated as empty)."""
    path = os.path.join(folder, LEAK_CLEARED_RELPATH)
    if not os.path.lexists(path):
        return []
    try:
        if os.path.islink(path):
            raise ValueError
        with open(path, "r", encoding="utf-8") as fh:
            ledger = json.load(fh)
    except (OSError, ValueError):
        raise KitError(CLEARED_MALFORMED_MSG)
    if not isinstance(ledger, dict) \
            or ledger.get("schema") != LEAK_CLEARED_SCHEMA \
            or not isinstance(ledger.get("clearances"), list) \
            or not all(_clearance_ok(e) for e in ledger["clearances"]):
        raise KitError(CLEARED_MALFORMED_MSG)
    return ledger["clearances"]


def append_clearance(folder, cases, at=None, seal_sha256=None):
    """Append one clearance ({ID: {slot, cause, identity}}) made against the
    current SEAL.json; existing entries are never modified."""
    clearances = load_clearances(folder)
    if seal_sha256 is None:
        seal_sha256 = holdout_kit.sha256_file(os.path.join(folder, SEAL_NAME))
    entry = {"at": at or _now(), "rule": LEAK_CLEAR_RULE,
             "seal_sha256": seal_sha256, "cases": cases}
    if not _clearance_ok(entry):
        raise KitError("a clearance must name opaque IDs, slots and content "
                       "identities")
    clearances.append(entry)
    holdout_kit.write_json_atomic(
        os.path.join(folder, LEAK_CLEARED_RELPATH),
        {"schema": LEAK_CLEARED_SCHEMA, "clearances": clearances})
    return entry


def _cleared_for_seal(folder, cid, named_at, seal_sha):
    """True when a clearance made against this seal, at or after the scan
    that named the case, clears it."""
    if seal_sha is None:
        return False
    return any(e["seal_sha256"] == seal_sha and cid in e["cases"]
               and e["at"] >= named_at for e in load_clearances(folder))


def _current_seal_sha(folder):
    """sha256 of <folder>/SEAL.json, or None when there is none."""
    path = os.path.join(folder, SEAL_NAME)
    return holdout_kit.sha256_file(path) if os.path.isfile(path) else None


def _retirement_cleared(entry, clearances, seal_sha):
    """A `leakscan` retirement voided by a later clearance of exactly the same
    content, made against the current SEAL.json (seal_sha); a clearance
    holds only for the seal it was made against."""
    if entry.get("reason") != "leakscan" or seal_sha is None:
        return False
    ident = _content_identity(entry)
    return any(c["seal_sha256"] == seal_sha and c["at"] >= entry["at"]
               and _content_identity(case["identity"]) == ident
               for c in clearances for case in c["cases"].values())


def cleared_slots(folder):
    """Slots cleared against the current SEAL.json, sorted."""
    path = os.path.join(folder, SEAL_NAME)
    if not os.path.isfile(path):
        return []
    sha = holdout_kit.sha256_file(path)
    return sorted({case["slot"] for e in load_clearances(folder)
                   if e["seal_sha256"] == sha for case in e["cases"].values()})


def retired_problems(folder):
    """One line per current case whose content matches a retired entry on
    source revisions, diff bytes, changed-line set or key; IDs are never
    compared. [] when nothing is retired; a malformed ledger is a KitError."""
    return [line for _, line, _ in retired_matches(folder)]


# ---------------------------------------------------------------- publish


def publish(folder, repo):
    """Copy <folder>/SEAL.json to <repo>/SEAL_RELPATH and nothing else.

    Refuses a dry-run folder or a dry-run seal (DRY_RUN_REFUSED_MSG), and
    unless the seal has the public shape, the leak ledger is clean for the
    current seal, and no current case reuses retired material. Never
    overwrites a different SEAL.json already in the repo. Returns the path.
    """
    if not folder:
        raise KitError("publish needs --folder PATH (the holdout folder)")
    seal_path = os.path.join(folder, SEAL_NAME)
    seal = holdout_kit.load_json(seal_path, what="SEAL.json")
    if dry_run_problems(folder, seal):
        raise KitError(holdout_kit.DRY_RUN_REFUSED_MSG + "; nothing was "
                       "published")
    shape = public_shape_problems(seal)
    if shape:
        raise KitError("SEAL.json does not have the public shape (%s); "
                       "nothing was published" % shape[0])
    leaks = leak_ledger_problems(folder, seal)
    if leaks:
        raise KitError(leaks[0])
    retired = retired_problems(folder)
    if retired:
        raise KitError(retired[0])
    if not os.path.isdir(repo):
        raise KitError("the repo path is not a folder")
    dest = os.path.join(repo, *SEAL_RELPATH.split("/"))
    with open(seal_path, "rb") as fh:
        data = fh.read()
    if os.path.lexists(dest):
        if os.path.islink(dest) or not os.path.isfile(dest):
            raise KitError("the repo's SEAL.json path is not a plain file")
        with open(dest, "rb") as fh:
            if fh.read() == data:
                return dest
        raise KitError("the repo already holds a different SEAL.json; a "
                       "published seal is never overwritten")
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(seal_path, dest)
    except OSError:
        raise KitError("cannot write SEAL.json into the repo")
    return dest


# ---------------------------------------------------------------- resume grammar

# The ONLY replies the tuning side accepts from the owner at a checkpoint:
# status words, slot names and small integers. Ordered, first match wins:
# the clean dry-run success form is tried before the general dry-run form.
# Syntax and success are separate questions: every entry is a conforming
# reply, and RESUME_BLOCKING_KINDS says which conforming replies report an
# outcome that must stop the run. At the dry-run checkpoint only
# "dry run ok prompted sandbox=ok" (openssl prompted for the passphrase AND
# the cross-check sandbox probe reported OK) may proceed; every other
# "dry run ok ..." reply (no-prompt, problems=..., or no explicit
# sandbox-probe OK) is dry-run-failed.
# The closed vocabulary of `diagnose` (holdout_seal.diagnose_parts): a cause
# that sorts a failed agreement into a case/key problem (key-unsealable,
# judge-disagrees) or a tuning-side suspect (checker-suspect,
# proof-mismatch), and the checks behind it. Fixed words only, so the line
# can cross to the tuning session without carrying case content.
DIAG_CAUSES = ("agrees", "incomplete", "key-unsealable", "judge-disagrees",
               "checker-suspect", "proof-mismatch")
DIAG_CHECKS = ("none", "round-incomplete", "type-judged-quiet",
               "type-judged-catch", "type-other-slot", "location-file-differs",
               "location-path-form", "location-lines-apart",
               "category-key-other", "category-judge-other",
               "category-differs", "quiet-unconfirmed", "judge-type-false",
               "judge-defect-false", "judge-category-false",
               "judge-proof-false", "judge-flag-contradicts",
               "final-malformed", "proof-recorded-bad", "proof-rerun-missing",
               "proof-rerun-differs",
               "proof-rerun-base-failed", "proof-rerun-changed-passed",
               "nonrunnable-rerun-set", "nonrunnable-unresolved")


# The closed vocabulary of `denials` (holdout_autopilot.denials_line): a
# permission denial in a cross-check session, named by tool and by the kind
# of place its input touched, never by its command or path.
DENIAL_TOOLS = ("bash", "read", "write", "edit", "glob", "grep", "webfetch",
                "websearch", "agent", "other")
DENIAL_WHERE = ("workspace", "holdout", "home", "temp", "system", "none")


# The closed vocabulary of `leakdiag` (holdout_archive.leakdiag): per slot,
# a cause for its leak-scan matches, and the kinds of place they were in.
LEAKDIAG_CAUSES = ("none", "origin-history", "prior-elsewhere", "exposed")
LEAKDIAG_WHERE = ("own-transcript", "own-history", "codex-own",
                  "tuning-transcript", "tuning-tree", "tuning-gitlog",
                  "tuning-plugin", "codex-tuning", "shared-tmp", "zsh-history",
                  "other", "other-transcript", "claude-history",
                  "claude-plugins", "claude-debug", "claude-other",
                  "codex-other", "codex")


def _alt(words):
    return "(?:%s)" % "|".join(re.escape(w) for w in words)


_DIAG_CHECK_RE = _alt(w for w in DIAG_CHECKS if w != "none")

_SLOTS_RE = r"(?:C[1-3]|Q[1-3])(?:,(?:C[1-3]|Q[1-3]))*"

RESUME_GRAMMAR = (
    ("dry-run-ok", re.compile(r"dry run ok prompted sandbox=ok")),
    ("dry-run-failed", re.compile(
        r"dry run ok(?: prompted| no-prompt)?(?: sandbox=ok)?"
        r"(?: problems=[0-9]+(?:,[0-9]+)*)?")),
    ("sealed", re.compile(r"sealed(?: cleared=" + _SLOTS_RE + r")?"
                          r"(?: non-runnable=[0-6])?")),
    ("replaced", re.compile(
        r"replaced slots=" + _SLOTS_RE + r"(?: cleared=" + _SLOTS_RE + r")?"
        r"(?: non-runnable=[0-6])?")),
    ("clean", re.compile(r"clean leakscan=0")),
    ("blocked", re.compile(
        r"blocked (?:disagreement|validation|leakscan|residue|no-prompt"
        r"|sandbox|other)")),
    ("diagnosis", re.compile(
        r"diagnosis (?:C[1-3]|Q[1-3]|all) cause=" + _alt(DIAG_CAUSES)
        + r" checks=(?:none|" + _DIAG_CHECK_RE + r"(?:," + _DIAG_CHECK_RE
        + r")*)")),
)
_DENIAL_RE = _alt("%s-%s" % (t, w) for t in DENIAL_TOOLS
                  for w in DENIAL_WHERE)
RESUME_GRAMMAR += (
    ("denials", re.compile(
        r"denials gen=[1-9][0-9]? count=[0-9]{1,4} (?:none|unknown|"
        + _DENIAL_RE + r"(?:," + _DENIAL_RE + r")*)")),
)
_LEAKDIAG_WHERE_RE = _alt(LEAKDIAG_WHERE)
RESUME_GRAMMAR += (
    ("leakdiag", re.compile(
        r"leakdiag " + " ".join(r"%s=%s" % (s, _alt(LEAKDIAG_CAUSES))
                                for s in ("C1", "C2", "C3", "Q1", "Q2", "Q3"))
        + r" where=(?:none|" + _LEAKDIAG_WHERE_RE + r"(?:,"
        + _LEAKDIAG_WHERE_RE + r")*)")),
)
RESUME_GRAMMAR += (
    ("leak-clear", re.compile(
        r"leak-clear cleared=(?:none|" + _SLOTS_RE + r") kept=(?:none|"
        + _SLOTS_RE + r")")),
)
RESUME_BLOCKING_KINDS = frozenset({"dry-run-failed", "blocked", "diagnosis",
                                   "denials", "leakdiag", "leak-clear"})
RESUME_PROBLEM_MSG = ("resume reply does not conform to the opaque grammar; "
                      "treat it as a contamination incident and do not "
                      "record its contents")


def resume_reply_kind(text):
    """The grammar kind of a checkpoint reply, or None. Surrounding
    whitespace is stripped; the rest must fullmatch one entry. Never raises."""
    if not isinstance(text, str):
        return None
    reply = text.strip()
    for kind, pattern in RESUME_GRAMMAR:
        if pattern.fullmatch(reply):
            return kind
    return None


def resume_reply_outcome(text):
    """"proceed", "blocking" or None (non-conforming)."""
    kind = resume_reply_kind(text)
    if kind is None:
        return None
    return "blocking" if kind in RESUME_BLOCKING_KINDS else "proceed"


# ---------------------------------------------------------------- CLI


def add_parser(sub, name):
    if name == "seal-build":
        sub.add_parser(name, help="write SEAL.json and the private inventory")
    elif name == "rehash":
        p = sub.add_parser(name, help="verify a decrypted sealed/ against "
                                      "SEAL.json")
        p.add_argument("--seal", required=True, metavar="PATH")
        p.add_argument("--sealed", required=True, metavar="PATH")
        p.add_argument("--dry-run", action="store_true",
                       help="verify a dry run's own seal (a dry-run folder "
                            "only; never for Phase 55)")
    elif name == "extract":
        p = sub.add_parser(name, help="copy only cases/ or only keys/")
        p.add_argument("--part", required=True, choices=("cases", "keys"))
        p.add_argument("--dest", required=True, metavar="PATH")
        p.add_argument("--sealed", metavar="PATH",
                       help="a sealed/ folder (default: <folder>/sealed)")
    elif name == "seal-order":
        p = sub.add_parser(name, help="prove SEAL.json has exactly one commit")
        p.add_argument("--repo", required=True, metavar="PATH")
        p.add_argument("--before", metavar="REV")
    elif name == "publish":
        p = sub.add_parser(name, help="copy SEAL.json into the repo")
        p.add_argument("--repo", required=True, metavar="PATH")
    elif name == "retire":
        p = sub.add_parser(name, help="retire a case's content for good")
        group = p.add_mutually_exclusive_group(required=True)
        group.add_argument("--case", metavar="ID")
        group.add_argument("--slot", choices=holdout_kit.SLOTS)
        group.add_argument("--sync", action="store_true")
        p.add_argument("--reason", choices=("leakscan", "owner"))
    elif name == "resume-check":
        sub.add_parser(name, help="check an owner checkpoint reply (stdin)")
    else:
        raise KitError("unknown manifest command")


def _cmd_seal_build(args):
    if holdout_kit.dry_run_markers_present(args.folder):
        raise KitError(holdout_kit.DRY_RUN_REFUSED_MSG + "; use seal "
                       "--dry-run")
    seal = build_seal(args.folder)
    write_inventory(args.folder)
    holdout_kit.write_json_atomic(os.path.join(args.folder, SEAL_NAME), seal)
    holdout_kit.print_ok("seal manifest built: %d cases, key commitment "
                         "recorded" % len(seal["cases"]))
    return 0


def _cmd_rehash(args):
    dry = bool(getattr(args, "dry_run", False))
    if dry and not holdout_kit.dry_run_marker_ok(
            os.path.dirname(os.path.abspath(args.sealed))):
        holdout_kit.print_problem(NOT_A_DRY_FOLDER_MSG)
        return 1
    try:
        result = rehash_folder(args.seal, args.sealed, dry_run=dry)
    except KitError as exc:
        holdout_kit.print_problem(str(exc))
        return 1
    if result["ok"]:
        holdout_kit.print_ok("all %d cases match the seal; key commitment "
                             "verified; %d files in inventory"
                             % (len(result["cases"]),
                                result["inventory_files"]))
        return 0
    if not result["commitment_ok"]:
        holdout_kit.print_problem("the HMAC key does not match the committed "
                                  "key")
    bad = sum(1 for v in result["cases"].values() if not v)
    if bad:
        holdout_kit.print_problem("%d case(s) differ from the seal" % bad)
    for label, key in (("mismatched", "mismatched"), ("missing", "missing"),
                       ("extra", "extra"), ("missing case", "missing_cases"),
                       ("extra case", "extra_cases")):
        for item in result[key]:
            holdout_kit.print_problem("%s: %s" % (label, item))
    return 1


def _cmd_extract(args):
    sealed = args.sealed or _sealed(args.folder)
    n = extract_part(sealed, args.part, args.dest)
    holdout_kit.print_ok("extracted %s/ only (%d files)" % (args.part, n))
    return 0


def _cmd_seal_order(args):
    problems = seal_order_problems(args.repo, before=args.before)
    if problems:
        for p in problems:
            holdout_kit.print_problem(p)
        return 1
    msg = "SEAL.json has exactly one commit"
    if args.before:
        msg += " and it is an ancestor of %s" % args.before
    holdout_kit.print_ok(msg)
    return 0


def _cmd_publish(args):
    dest = publish(args.folder, args.repo)
    holdout_kit.print_ok("SEAL.json published to %s. Commit it on its own."
                         % dest)
    return 0


def _usage(msg):
    sys.stderr.write("holdout: error: %s\n" % msg)
    return 2


def _resolve_slot(folder, slot):
    sealed = _sealed(folder)
    found = [cid for cid in holdout_kit.case_ids(folder)
             if _case_slot_lenient(sealed, cid) == slot]
    if len(found) != 1:
        raise KitError("no single sealed case holds slot %s" % slot)
    return found[0]


def _cmd_retire(args):
    if args.sync:
        if args.reason:
            return _usage("retire --sync takes no --reason")
        n = sync_retired_revisions(args.folder)
        holdout_kit.print_ok("finder skip list rewritten (%d retired "
                             "revision(s))" % n)
        return 0
    if not args.reason:
        return _usage("retire --case/--slot needs --reason leakscan|owner")
    if args.slot:
        case_id = _resolve_slot(args.folder, args.slot)
    else:
        case_id = args.case
        if not holdout_kit.ID_RE.match(case_id or ""):
            return _usage("--case takes an opaque case id")
    retire_case(args.folder, case_id, args.reason)
    slot = _case_slot_lenient(_sealed(args.folder), case_id)
    holdout_kit.print_ok("retired %s (%s): recorded in RETIRED.json; its "
                         "revision and content cannot be re-sealed under any "
                         "ID" % (slot, case_id))
    return 0


def _cmd_resume_check(args):
    try:
        reply = sys.stdin.read()
    except (OSError, UnicodeDecodeError, ValueError):
        reply = None
    kind = resume_reply_kind(reply)
    if kind is None:
        holdout_kit.print_problem(RESUME_PROBLEM_MSG)
        return 1
    holdout_kit.print_ok("resume reply conforms (%s)" % kind)
    if kind in RESUME_BLOCKING_KINDS:
        holdout_kit.print_problem("this reply reports a blocking outcome (%s); "
                                  "stop and do not proceed" % kind)
        return 3
    return 0


_HANDLERS = {
    "seal-build": _cmd_seal_build,
    "rehash": _cmd_rehash,
    "extract": _cmd_extract,
    "seal-order": _cmd_seal_order,
    "publish": _cmd_publish,
    "retire": _cmd_retire,
    "resume-check": _cmd_resume_check,
}


def cmd(args):
    """Exit codes: 0 success, 1 refusal or failure, 2 usage error, and for
    resume-check 3 when the reply conforms but reports a blocking outcome."""
    if args.cmd not in holdout_kit.NO_REFUSAL_COMMANDS:
        holdout_kit.refuse_if_claude_spawned(args.folder)
    handler = _HANDLERS.get(args.cmd)
    if handler is None:
        raise KitError("unknown manifest command")
    return handler(args)
