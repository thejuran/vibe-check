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
        return sorted(os.listdir(keys))
    except OSError:
        raise KitError("sealed/keys is missing or unreadable")


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


# ---------------------------------------------------------------- CLI


def add_parser(sub, name):
    if name == "seal-build":
        sub.add_parser(name, help="write SEAL.json and the private inventory")
    elif name == "rehash":
        p = sub.add_parser(name, help="verify a decrypted sealed/ against "
                                      "SEAL.json")
        p.add_argument("--seal", required=True, metavar="PATH")
        p.add_argument("--sealed", required=True, metavar="PATH")
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
    seal = build_seal(args.folder)
    write_inventory(args.folder)
    holdout_kit.write_json_atomic(os.path.join(args.folder, SEAL_NAME), seal)
    holdout_kit.print_ok("seal manifest built: %d cases, key commitment "
                         "recorded" % len(seal["cases"]))
    return 0


def cmd(args):
    if args.cmd not in holdout_kit.NO_REFUSAL_COMMANDS:
        holdout_kit.refuse_if_claude_spawned(args.folder)
    if args.cmd == "seal-build":
        return _cmd_seal_build(args)
    raise KitError("command '%s' is not available yet" % args.cmd)
