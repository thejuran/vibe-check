"""holdout_seal.py — the blind cross-check and the `seal` gate of the kit.

Every case gets a second, independent judgment before it can be sealed. The
flow, and what binds each step to the next:

  1. crosscheck-prepare writes one packet per case into the open cross-check
     workspace: <ws>/<XID>/ with the base tree, change.diff, CASE-TYPES.md and
     CROSSCHECK-BRIEF.md, and nothing else (no slot, key, proof, provenance or
     finder brief). XIDs are fresh random names. The ID -> XID mapping, the
     workspace generation, the preparation time and the sha256 of base.tar,
     change.diff and CASE-TYPES.md go into sealed/keys/<ID>/xcheck-ledger.json,
     which no cross-check session can read.
  2. The cross-check session (owner-launched) writes a structured blind.json
     per packet without any key in view.
  3. crosscheck-reveal reveals a whole workspace at once, and only when every
     packet in it has a well-formed blind.json. It first freezes, in every
     ledger, sha256(blind.json), a fresh reveal token and the sha256 of
     key.json, proof-results.json and proof/; marks the workspace revealed in
     sealed/keys/xcheck-workspaces.json; and only then copies the key, the
     proof, its results and the token into <ws>/<XID>/revealed/. The
     workspace is now burned: its session has seen keys.
  4. The session writes final.json, echoing the reveal token.
  5. seal checks validation (proofs re-run), retired content, every binding
     (inputs, revealed files, blind hash, token), workspace freshness, and the
     AGREEMENT, PROOF EXITS and NON-RUNNABLE rules, recomputed from blind.json,
     key.json and proof-results.json rather than taken from the session's
     flags. Only then does it write SEAL.json.

Dry run: `seal --dry-run` works only in a folder carrying a valid
DRY-RUN.json and writes a SEAL.json marked "dry-run" (rejected by publish and
the Phase-55 rehash). Only there may SYNTHETIC-AGREEMENT.json, written by
`autopilot --dry-run` (record_synthetic_agreement), stand in for the
agreement rule on a real judge's well-formed, hash-bound disagreement; the
judge's verdict files are never written. A real seal refuses any folder
holding either file.

crosscheck-reset is the only regeneration path. It archives the current round
in the ledger and removes the packet; the next crosscheck-prepare gives the
case a new XID. When the open workspace has already seen a reveal, prepare
mints the next generation (its own workspace, config dir, scratch root and
launcher, with every earlier generation denied), so a reset case is always
judged by a session that has never seen a key.

Commands: crosscheck-prepare, crosscheck-reveal, crosscheck-reset, seal. Each
refuses inside a Claude-spawned shell. Output names slots, opaque IDs, XIDs
and workspace names only; never key text or verdicts.

I/O: stdlib only, imports exactly {json, os, secrets, shutil, sys, time} plus
holdout_kit, holdout_validate and holdout_manifest. No subprocess here: the
proofs run inside holdout_validate.
"""

import json
import os
import secrets
import shutil
import sys
import time

import holdout_kit
import holdout_manifest
import holdout_validate

KitError = holdout_kit.KitError

# ---------------------------------------------------------------- constants

DISAGREE_MSG = ("Case %s: the independent check disagreed (%s). Resolve it "
                "with evidence (write keys/<ID>/resolution.md, then "
                "crosscheck-reset <ID> --reason resolved) or replace the "
                "case.")
INPUTS_CHANGED_MSG = ("Case %s: sealed inputs changed after the cross-check "
                      "(%s). Run crosscheck-reset <ID> --reason "
                      "inputs-changed and redo the cross-check for this "
                      "case.")
STALE_WORKSPACE_MSG = ("Case %s: round %d was judged in cross-check workspace "
                       "%s, which had already seen a revealed key. A reset "
                       "case must be judged by a fresh session: run "
                       "crosscheck-reset <ID> --reason owner, then "
                       "crosscheck-prepare --case <ID> (it mints the next "
                       "workspace).")
ALREADY_SEALED_MSG = ("already sealed (SEAL.json exists); delete it "
                      "deliberately if you must re-seal")
LINE_SLACK = 5
WORKSPACES_RELPATH = "sealed/keys/" + holdout_kit.XCHECK_REGISTRY
LEDGER_NAME = "xcheck-ledger.json"
RESET_REASONS = ("inputs-changed", "resolved", "owner")
PACKET_DOCS = ("CASE-TYPES.md", "CROSSCHECK-BRIEF.md")
INPUT_MEMBERS = ("base.tar", "change.diff", "CASE-TYPES.md")
REVEALED_MEMBERS = ("key.json", "proof-results.json", "proof")
BLIND_KEYS = frozenset({"verdict", "type_guess", "location",
                        "defect_category", "reasoning"})
# The fields of the current round. reset moves them into ledger["rounds"].
ROUND_FIELDS = ("xid", "round", "generation", "workspace", "prepared_at",
                "inputs", "blind_sha256", "revealed_at", "reveal_token",
                "revealed", "resolution_sha256")
NOT_DRY_RUN_FOLDER_MSG = ("seal --dry-run needs a dry-run folder (a valid "
                          "DRY-RUN.json, written by dryrun --populate or by "
                          "refresh-kit for a provable dry run); nothing was "
                          "sealed")
SYNTHETIC_REFUSED_MSG = ("synthetic agreement is recorded only by autopilot "
                         "--dry-run in a dry-run folder; nothing was written")
JUDGE_VERDICT_BAD_MSG = ("%s: the cross-check session's verdict is not "
                         "well-formed (%s)")
FINAL_REQUIRED = {"reveal_token": str, "type_agrees": bool,
                  "defect_agrees": bool, "causal_failure_agrees": bool,
                  "proof_agrees": bool, "notes": str}
LAUNCH_MSG = ("fresh cross-check workspace %s. Close the previous cross-check "
              "session, then launch %s (a new session; /login if asked) and "
              "type: Read CROSSCHECK-BRIEF.md and begin.")


# ---------------------------------------------------------------- helpers


def _now():
    """UTC timestamp with microseconds. Fixed width, so timestamps written by
    this module compare correctly as strings."""
    ns = time.time_ns()
    secs, frac = divmod(ns, 1000000000)
    return "%s.%06dZ" % (time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(secs)),
                         frac // 1000)


def _now_after(floor):
    """_now(), strictly later than `floor` (a timestamp from _now or None)."""
    ts = _now()
    while floor is not None and ts <= floor:
        ts = _now()
    return ts


def _keys(folder, cid):
    return os.path.join(holdout_kit.sealed_dir(folder), "keys", cid)


def _cases(folder, cid):
    return os.path.join(holdout_kit.sealed_dir(folder), "cases", cid)


def _ledger_path(folder, cid):
    return os.path.join(_keys(folder, cid), LEDGER_NAME)


def _registry_path(folder):
    return os.path.join(folder, *WORKSPACES_RELPATH.split("/"))


def _load_dict_or_none(path):
    """A JSON object from `path`, or None when it is missing, unreadable or
    not an object."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _load_ledger(folder, cid):
    path = _ledger_path(folder, cid)
    if not os.path.lexists(path):
        return None
    data = _load_dict_or_none(path)
    if data is None or not isinstance(data.get("rounds", []), list):
        raise KitError("the cross-check ledger of case %s is malformed; "
                       "repair it (never delete it) and run this again" % cid)
    data.setdefault("rounds", [])
    return data


def _save_ledger(folder, cid, ledger):
    holdout_kit.write_json_atomic(_ledger_path(folder, cid), ledger)


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _refuse_if_sealed(folder):
    if os.path.lexists(os.path.join(folder, holdout_manifest.SEAL_NAME)):
        raise KitError(ALREADY_SEALED_MSG)


def _slot(folder, cid):
    return holdout_validate.slot_of(folder, cid)


def _packet_dir(folder, ledger):
    """<folder>/<workspace>/<xid> of the ledger's current round, or None when
    either name is missing or not a recognized workspace / XID."""
    if not isinstance(ledger, dict):
        return None
    ws, xid = ledger.get("workspace"), ledger.get("xid")
    if not isinstance(ws, str) or not holdout_kit.XCHECK_WS_RE.match(ws):
        return None
    if not isinstance(xid, str) or not holdout_kit.XID_RE.match(xid):
        return None
    return os.path.join(folder, ws, xid)


def _remove_tree(path):
    """Remove a packet, first making its directories writable (a session may
    have made a tree read-only). Never follows a link."""
    if not os.path.lexists(path):
        return
    if os.path.islink(path) or not os.path.isdir(path):
        os.remove(path)
        return
    os.chmod(path, 0o700)
    for dirpath, dirnames, _ in os.walk(path):
        for name in dirnames:
            full = os.path.join(dirpath, name)
            if not os.path.islink(full):
                os.chmod(full, 0o700)
    shutil.rmtree(path)


def _proof_aggregate_sha256(proof_dir):
    """sha256 over the sorted lines "relpath\\0sha256\\n" of every regular file
    under proof/. A symlink or special file is a KitError (walk_regular)."""
    if os.path.islink(proof_dir) or not os.path.isdir(proof_dir):
        raise KitError("proof/ is missing or not a folder")
    lines = []
    for rel in holdout_kit.walk_regular(proof_dir):
        digest = holdout_kit.sha256_file(os.path.join(proof_dir,
                                                      *rel.split("/")))
        lines.append("%s\0%s\n" % (rel, digest))
    return holdout_kit.sha256_bytes("".join(sorted(lines)).encode("utf-8"))


def _input_hashes(folder, cid):
    return {
        "base.tar": holdout_kit.sha256_file(os.path.join(_cases(folder, cid),
                                                         "base.tar")),
        "change.diff": holdout_kit.sha256_file(
            os.path.join(_cases(folder, cid), "change.diff")),
        "CASE-TYPES.md": holdout_kit.sha256_file(
            os.path.join(folder, "kit", "CASE-TYPES.md")),
    }


def _revealed_hashes(folder, cid):
    k = _keys(folder, cid)
    return {
        "key.json": holdout_kit.sha256_file(os.path.join(k, "key.json")),
        "proof-results.json": holdout_kit.sha256_file(
            os.path.join(k, "proof-results.json")),
        "proof": _proof_aggregate_sha256(os.path.join(k, "proof")),
    }


def _changed_members(recorded, current, members):
    recorded = recorded if isinstance(recorded, dict) else {}
    return [m for m in members if recorded.get(m) != current[m]]


# ---------------------------------------------------------------- registry


def _load_registry(folder):
    """The workspace registry, or None when it does not exist yet. A
    registry that is not exactly generations 1..N with their kit names is a
    KitError."""
    path = _registry_path(folder)
    if not os.path.lexists(path):
        return None
    reg = _load_dict_or_none(path)
    gens = reg.get("generations") if reg is not None else None
    ok = isinstance(gens, list) and not os.path.islink(path)
    if ok:
        for n, g in enumerate(gens, start=1):
            if not isinstance(g, dict) or g.get("gen") != n \
                    or not isinstance(g.get("cases"), list):
                ok = False
                break
            names = holdout_kit.xcheck_names(n)
            if any(g.get(k) != v for k, v in names.items()):
                ok = False
                break
    if not ok:
        raise KitError("the cross-check workspace registry is malformed; "
                       "repair it (never delete it) and run this again")
    return reg


def _save_registry(folder, reg):
    holdout_kit.write_json_atomic(_registry_path(folder), reg)


def _new_generation(gen):
    entry = dict(holdout_kit.xcheck_names(gen))
    entry.update(gen=gen, created_at=_now(), cases=[], revealed_at=None)
    return entry


def _generation(reg, gen):
    for g in (reg or {}).get("generations", []):
        if g.get("gen") == gen:
            return g
    return None


def _open_workspace(folder):
    """The registry entry of the workspace new packets go into.

    The newest generation while it has not seen a reveal. With no registry,
    generation 1 (setup's xcheck/) is registered. When the newest generation
    has been revealed, generation N+1 is minted with
    holdout_kit.make_xcheck_workspace (every earlier generation denied) and
    registered, and the launch line is printed."""
    reg = _load_registry(folder)
    if reg is None:
        ws = os.path.join(folder, holdout_kit.xcheck_names(1)["workspace"])
        if os.path.islink(ws) or not os.path.isdir(ws):
            raise KitError("the cross-check workspace xcheck is missing; run "
                           "setup first")
        reg = {"generations": [_new_generation(1)]}
        _save_registry(folder, reg)
        return reg["generations"][0]
    newest = reg["generations"][-1] if reg["generations"] else None
    if newest is not None and newest.get("revealed_at") is None:
        return newest
    n = len(reg["generations"])
    names = holdout_kit.xcheck_names(n + 1)
    if os.path.lexists(os.path.join(folder, names["workspace"])):
        raise KitError("unregistered cross-check workspace %s; remove it "
                       "deliberately" % names["workspace"])
    holdout_kit.make_xcheck_workspace(
        folder, n + 1, prior=[holdout_kit.xcheck_names(k)
                              for k in range(1, n + 1)])
    entry = _new_generation(n + 1)
    reg["generations"].append(entry)
    _save_registry(folder, reg)
    holdout_kit.print_ok(LAUNCH_MSG % (names["workspace"], names["launcher"]))
    sys.stdout.flush()
    return entry


def _live_packets(folder, entry):
    """(ID, ledger) of every case whose current round sits in this
    generation."""
    out = []
    for cid in entry.get("cases", []):
        if not isinstance(cid, str) or not holdout_kit.ID_RE.match(cid):
            continue
        led = _load_ledger(folder, cid)
        if led and led.get("xid") and led.get("generation") == entry["gen"]:
            out.append((cid, led))
    return out


# ---------------------------------------------------------------- prepare


def prepare_crosscheck(folder, case_id=None):
    """Write a blind packet for every case without a live one (or exactly
    `case_id`); return {ID: XID}."""
    _refuse_if_sealed(folder)
    ids = holdout_kit.case_ids(folder)
    if case_id is not None:
        if case_id not in ids:
            raise KitError("no sealed case %s" % case_id)
        led = _load_ledger(folder, case_id)
        if led and led.get("xid"):
            raise KitError("cross-check folder already exists for %s; run "
                           "crosscheck-reset first" % _slot(folder, case_id))
        targets = [case_id]
    else:
        targets, live = [], []
        for cid in ids:
            led = _load_ledger(folder, cid)
            (live if led and led.get("xid") else targets).append(cid)
        if not targets:
            raise KitError("cross-check folder already exists for %s; run "
                           "crosscheck-reset first" % _slot(folder, live[0]))
    for cid in targets:
        _slot(folder, cid)
    entry = _open_workspace(folder)
    ws = entry["workspace"]
    kit = os.path.join(folder, "kit")
    mapping = {}
    for cid in targets:
        xid = holdout_kit.new_xcheck_id()
        while os.path.lexists(os.path.join(folder, ws, xid)):
            xid = holdout_kit.new_xcheck_id()
        dest = os.path.join(folder, ws, xid)
        led = _load_ledger(folder, cid) or {"rounds": []}
        try:
            os.makedirs(os.path.join(dest, "base"))
            holdout_kit.safe_extract_tar(
                os.path.join(_cases(folder, cid), "base.tar"),
                os.path.join(dest, "base"))
            shutil.copyfile(os.path.join(_cases(folder, cid), "change.diff"),
                            os.path.join(dest, "change.diff"))
            for doc in PACKET_DOCS:
                src = os.path.join(kit, doc)
                if os.path.islink(src) or not os.path.isfile(src):
                    raise KitError("kit/%s is missing" % doc)
                shutil.copyfile(src, os.path.join(dest, doc))
            led.update(xid=xid, round=len(led["rounds"]) + 1,
                       generation=entry["gen"], workspace=ws,
                       prepared_at=_now(), inputs=_input_hashes(folder, cid))
            _save_ledger(folder, cid, led)
        except BaseException as exc:
            try:
                _remove_tree(dest)
            except OSError:
                pass
            if isinstance(exc, OSError):
                raise KitError("cannot write the cross-check packet %s" % xid)
            raise
        if cid not in entry["cases"]:
            reg = _load_registry(folder)
            _generation(reg, entry["gen"])["cases"].append(cid)
            _save_registry(folder, reg)
            entry["cases"].append(cid)
        mapping[cid] = xid
        holdout_kit.print_ok("prepared %s in %s" % (xid, ws))
    return mapping


# ---------------------------------------------------------------- blind shape


def _location_ok(loc):
    return (isinstance(loc, dict)
            and set(loc) == {"file", "line_start", "line_end"}
            and isinstance(loc["file"], str) and loc["file"].strip() != ""
            and _is_int(loc["line_start"]) and _is_int(loc["line_end"])
            and 1 <= loc["line_start"] <= loc["line_end"])


def _blind_shape_problems(blind):
    """[] when blind.json has the structured schema of CROSSCHECK-BRIEF.md;
    otherwise the names of the offending fields."""
    if not isinstance(blind, dict):
        return ["not an object"]
    problems = []
    if set(blind) != BLIND_KEYS:
        problems.append("fields")
    verdict = blind.get("verdict")
    guess = blind.get("type_guess")
    if verdict not in ("catch", "quiet"):
        problems.append("verdict")
    if guess not in holdout_kit.SLOTS:
        problems.append("type_guess")
    elif verdict == "catch" and guess not in holdout_kit.CATCH_SLOTS \
            or verdict == "quiet" and guess not in holdout_kit.QUIET_SLOTS:
        problems.append("type_guess")
    reasoning = blind.get("reasoning")
    if not isinstance(reasoning, str) or not reasoning.strip():
        problems.append("reasoning")
    if verdict == "catch":
        if not _location_ok(blind.get("location")):
            problems.append("location")
        if blind.get("defect_category") not in \
                holdout_validate.CAUSAL_CATEGORIES:
            problems.append("defect_category")
    elif verdict == "quiet":
        if blind.get("location") is not None:
            problems.append("location")
        if blind.get("defect_category") is not None:
            problems.append("defect_category")
    return problems


def _read_blind(packet, xid):
    path = os.path.join(packet, "blind.json")
    if not os.path.lexists(path):
        raise KitError("blind.json is missing for %s" % xid)
    if os.path.islink(path) or not os.path.isfile(path):
        raise KitError("blind.json for %s is not a regular file" % xid)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            blind = json.load(fh)
    except (OSError, ValueError):
        raise KitError("blind.json for %s is not valid JSON" % xid)
    if _blind_shape_problems(blind):
        raise KitError("blind.json has the wrong shape for %s (%s)"
                       % (xid, ", ".join(_blind_shape_problems(blind))))
    return path


def _final_shape_problems(final, slot, runnable=True):
    """[] when final.json has the VALIDITY-RULES shape for this slot;
    otherwise the names of the offending fields. Field values are checked
    for type only: what the session concluded is never judged here."""
    if not isinstance(final, dict):
        return ["not an object"]
    problems = []
    for name, typ in sorted(FINAL_REQUIRED.items()):
        value = final.get(name)
        if not isinstance(value, typ) or (typ is str and not value.strip()):
            problems.append(name)
    rerun = final.get("proof_rerun_exit")
    if runnable and _exit_pair(rerun) is None:
        problems.append("proof_rerun_exit")
    if not runnable and rerun is not None:
        problems.append("proof_rerun_exit")
    confirmed = final.get("quiet_confirmed", "missing")
    if confirmed is None:
        if slot in holdout_kit.QUIET_SLOTS:
            problems.append("quiet_confirmed")
    elif not (isinstance(confirmed, dict)
              and set(confirmed) == {"supported_behavior", "exposure_check"}
              and all(isinstance(v, bool) for v in confirmed.values())):
        problems.append("quiet_confirmed")
    return problems


# ---------------------------------------------------------------- reveal


def _missing_blind_msg(ws, n):
    return ("workspace %s has packets without blind.json (%d); reveal is "
            "all-or-nothing per workspace so no verdict is written after a "
            "key is shown" % (ws, n))


def _copy_file(src, dst):
    if os.path.islink(src) or not os.path.isfile(src):
        raise KitError("%s is missing" % os.path.basename(src))
    shutil.copy2(src, dst, follow_symlinks=False)


def _copy_revealed(folder, cid, packet, token):
    """Copy the key, the proof, its results and any resolution into
    <packet>/revealed/; REVEAL-TOKEN is written last."""
    k = _keys(folder, cid)
    rev = os.path.join(packet, "revealed")
    os.makedirs(rev, exist_ok=True)
    _copy_file(os.path.join(k, "key.json"), os.path.join(rev, "key.json"))
    _copy_file(os.path.join(k, "proof-results.json"),
               os.path.join(rev, "proof-results.json"))
    proof = os.path.join(k, "proof")
    for rel in holdout_kit.walk_regular(proof):
        dst = os.path.join(rev, "proof", *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        _copy_file(os.path.join(proof, *rel.split("/")), dst)
    res = os.path.join(k, "resolution.md")
    if os.path.isfile(res) and not os.path.islink(res):
        _copy_file(res, os.path.join(rev, "resolution.md"))
    with open(os.path.join(rev, "REVEAL-TOKEN"), "w", encoding="utf-8") as fh:
        fh.write(token)


def reveal_workspace(folder, gen):
    """Reveal every packet of generation `gen`; return the IDs revealed.

    All-or-nothing: refuses unless every live packet has a well-formed
    blind.json and unchanged inputs. Then every ledger gets blind_sha256,
    revealed_at, a fresh reveal_token, the revealed-file hashes and (when
    keys/<ID>/resolution.md exists) resolution_sha256, and the registry marks
    the generation revealed, all before any key is copied."""
    _refuse_if_sealed(folder)
    reg = _load_registry(folder)
    entry = _generation(reg, gen)
    if entry is None:
        raise KitError("no registered cross-check workspace for generation "
                       "%s" % gen)
    ws = entry["workspace"]
    if entry.get("revealed_at") is not None:
        raise KitError("workspace %s already revealed" % ws)
    packets = _live_packets(folder, entry)
    if not packets:
        raise KitError("workspace %s has no packets to reveal" % ws)
    missing = [led["xid"] for _, led in packets
               if not os.path.lexists(os.path.join(folder, ws, led["xid"],
                                                   "blind.json"))]
    if missing:
        raise KitError(_missing_blind_msg(ws, len(missing)))
    blinds = {}
    for cid, led in packets:
        blinds[cid] = _read_blind(os.path.join(folder, ws, led["xid"]),
                                  led["xid"])
    for cid, led in packets:
        changed = _changed_members(led.get("inputs"),
                                   _input_hashes(folder, cid), INPUT_MEMBERS)
        if changed:
            raise KitError("%s: sealed inputs changed since "
                           "crosscheck-prepare (%s); run crosscheck-reset "
                           "%s --reason inputs-changed"
                           % (_slot(folder, cid), ", ".join(changed), cid))
    ts = _now_after(max(led.get("prepared_at") or "" for _, led in packets))
    tokens = {}
    for cid, led in packets:
        tokens[cid] = secrets.token_hex(8)
        led.update(blind_sha256=holdout_kit.sha256_file(blinds[cid]),
                   revealed_at=ts, reveal_token=tokens[cid],
                   revealed=_revealed_hashes(folder, cid))
        res = os.path.join(_keys(folder, cid), "resolution.md")
        if os.path.isfile(res) and not os.path.islink(res):
            led["resolution_sha256"] = holdout_kit.sha256_file(res)
        else:
            led.pop("resolution_sha256", None)
    for cid, led in packets:
        _save_ledger(folder, cid, led)
    _generation(reg, gen)["revealed_at"] = ts
    _save_registry(folder, reg)
    for cid, led in packets:
        try:
            _copy_revealed(folder, cid, os.path.join(folder, ws, led["xid"]),
                           tokens[cid])
        except OSError:
            raise KitError("cannot copy the revealed files for %s; workspace "
                           "%s is burned: reset its cases and prepare them "
                           "again" % (led["xid"], ws))
    return [cid for cid, _ in packets]


def _find_xid(folder, xid):
    """(ID, ledger) of the case whose current round is `xid`."""
    if not isinstance(xid, str) or not holdout_kit.XID_RE.match(xid):
        raise KitError("not a cross-check id (X- followed by 8 hex digits)")
    for cid in holdout_kit.case_ids(folder):
        led = _load_ledger(folder, cid)
        if led and led.get("xid") == xid:
            return cid, led
    raise KitError("no live cross-check packet %s" % xid)


def reveal(folder, xid):
    """Reveal the workspace that holds packet `xid` (the whole workspace:
    reveal is all-or-nothing); return the ID of `xid`'s case."""
    _refuse_if_sealed(folder)
    cid, led = _find_xid(folder, xid)
    entry = _generation(_load_registry(folder), led.get("generation"))
    if entry is None or entry["workspace"] != led.get("workspace"):
        raise KitError("packet %s is not in a registered workspace" % xid)
    if entry.get("revealed_at") is not None:
        raise KitError("%s already revealed" % xid)
    own = os.path.join(_packet_dir(folder, led), "blind.json")
    if not os.path.lexists(own):
        n = sum(1 for _, other in _live_packets(folder, entry)
                if not os.path.lexists(os.path.join(
                    _packet_dir(folder, other), "blind.json")))
        raise KitError("blind.json is missing for %s; %s"
                       % (xid, _missing_blind_msg(entry["workspace"], n)))
    reveal_workspace(folder, entry["gen"])
    return cid


def reveal_ready(folder):
    """Reveal every unrevealed workspace whose packets all have a blind.json.

    Returns (revealed XIDs, problem lines)."""
    _refuse_if_sealed(folder)
    reg = _load_registry(folder)
    revealed, problems = [], []
    for entry in (reg or {}).get("generations", []):
        if entry.get("revealed_at") is not None:
            continue
        packets = _live_packets(folder, entry)
        if not packets:
            continue
        missing = sum(1 for _, led in packets
                      if not os.path.lexists(os.path.join(
                          _packet_dir(folder, led), "blind.json")))
        if missing:
            problems.append("workspace %s has packets without blind.json "
                            "(%d); nothing revealed there"
                            % (entry["workspace"], missing))
            continue
        try:
            ids = reveal_workspace(folder, entry["gen"])
        except KitError as exc:
            problems.append(str(exc))
            continue
        revealed.extend(_load_ledger(folder, cid)["xid"] for cid in ids)
    return revealed, problems


# ---------------------------------------------------------------- reset


def reset_crosscheck(folder, case_id, reason):
    """Archive the case's current round and remove its packet; return the old
    XID. Never touches the sealed case, the workspace or the registry."""
    if reason not in RESET_REASONS:
        raise KitError("reset reason must be one of %s"
                       % ", ".join(RESET_REASONS))
    _refuse_if_sealed(folder)
    if case_id not in holdout_kit.case_ids(folder):
        raise KitError("no sealed case %s" % case_id)
    slot = _slot(folder, case_id)
    led = _load_ledger(folder, case_id)
    if not led or not led.get("xid"):
        raise KitError("cross-check not prepared for %s" % slot)
    packet = _packet_dir(folder, led)
    archived = {f: led[f] for f in ROUND_FIELDS if f in led}
    for name, field in (("blind.json", "blind_sha256_at_reset"),
                        ("final.json", "final_sha256_at_reset")):
        path = os.path.join(packet, name) if packet else None
        if path and os.path.isfile(path) and not os.path.islink(path):
            archived[field] = holdout_kit.sha256_file(path)
        else:
            archived[field] = None
    archived.update(reset_reason=reason, reset_at=_now())
    for f in ROUND_FIELDS:
        led.pop(f, None)
    led["rounds"].append(archived)
    _save_ledger(folder, case_id, led)
    try:
        if packet:
            _remove_tree(packet)
        verdict = os.path.join(_keys(folder, case_id), "crosscheck.json")
        if os.path.lexists(verdict):
            os.remove(verdict)
    except OSError:
        raise KitError("the round was archived but the packet could not be "
                       "removed; remove %s by hand" % archived["xid"])
    return archived["xid"]


# ---------------------------------------------------------------- agreement


def _exit_pair(value):
    """{"base": int, "changed": int} or None (bools are not exits)."""
    if not isinstance(value, dict):
        return None
    base, changed = value.get("base"), value.get("changed")
    if not _is_int(base) or not _is_int(changed):
        return None
    return {"base": base, "changed": changed}


def _recorded_exits(proof_results):
    """The finder's recorded base/changed exits from proof-results.json when
    it is runnable and well formed; None otherwise. Never raises."""
    if not isinstance(proof_results, dict) \
            or proof_results.get("runnable") is not True:
        return None
    runs = []
    for tree in ("base", "changed"):
        rec = proof_results.get(tree)
        code = rec.get("exit") if isinstance(rec, dict) else None
        if not _is_int(code):
            return None
        runs.append(code)
    return {"base": runs[0], "changed": runs[1]}


def _slot_pattern_ok(slot, pair):
    if slot in holdout_kit.CATCH_SLOTS:
        return pair["base"] == 0 and pair["changed"] != 0
    return pair["base"] == 0 and pair["changed"] == 0


def _norm_file(name):
    if not isinstance(name, str):
        return None
    name = name.strip()
    while name.startswith("./"):
        name = name[2:]
    return os.path.normpath(name) if name else None


def _location_agrees(key_loc, blind_loc):
    """Same file, and the blind range overlaps the key range widened by
    LINE_SLACK lines on each side."""
    if not _location_ok(key_loc) or not _location_ok(blind_loc):
        return False
    if _norm_file(key_loc["file"]) != _norm_file(blind_loc["file"]):
        return False
    return (blind_loc["line_start"] <= key_loc["line_end"] + LINE_SLACK
            and blind_loc["line_end"] >= key_loc["line_start"] - LINE_SLACK)


def agreement_problems(slot, key, blind, final, runnable=True,
                       resolution_bound=False, recorded_exits=None):
    """The failed parts of the AGREEMENT, PROOF EXITS and NON-RUNNABLE
    rules; [] only when every part holds.

    Type, location and category are recomputed from blind.json against
    key.json; the session's flags are required too but never override a
    mechanical mismatch. A runnable proof needs the independent re-run exits
    (final.proof_rerun_exit) to equal the recorded exits (`recorded_exits`,
    from proof-results.json; None fails closed) and both to fit the slot
    pattern. A non-runnable proof needs proof_rerun_exit null, proof_agrees
    true and an owner resolution bound at reveal (`resolution_bound`)."""
    parts = []

    def fail(part):
        if part not in parts:
            parts.append(part)

    key = key if isinstance(key, dict) else {}
    blind = blind if isinstance(blind, dict) else {}
    final_ok = isinstance(final, dict)
    final = final if final_ok else {}
    catch = slot in holdout_kit.CATCH_SLOTS
    want_verdict = "catch" if catch else "quiet"

    if blind.get("verdict") != want_verdict or blind.get("type_guess") != slot:
        fail("type")
    if catch and blind.get("verdict") == "catch":
        if not _location_agrees(key.get("location"), blind.get("location")):
            fail("defect location")
        key_cat = key.get("causal_failure_category")
        blind_cat = blind.get("defect_category")
        if key_cat not in holdout_validate.CAUSAL_CATEGORIES \
                or blind_cat != key_cat:
            fail("causal-failure category")
        if holdout_validate.OTHER_CATEGORY in (key_cat, blind_cat):
            fail("category other")
    if not catch:
        confirmed = final.get("quiet_confirmed")
        if not isinstance(confirmed, dict) \
                or confirmed.get("supported_behavior") is not True \
                or confirmed.get("exposure_check") is not True:
            fail("quiet confirmation")

    flags = ["type_agrees", "proof_agrees"]
    if catch:
        flags += ["defect_agrees", "causal_failure_agrees"]
    if not final_ok or any(final.get(f) is not True for f in flags):
        fail("final flags")

    rerun = final.get("proof_rerun_exit")
    if runnable:
        independent = _exit_pair(rerun)
        recorded = _exit_pair(recorded_exits)
        if independent is None:
            fail("final flags")
        if recorded is None:
            fail("proof exits")
        elif not _slot_pattern_ok(slot, recorded):
            fail("proof exits")
        if independent is not None and recorded is not None \
                and independent != recorded:
            fail("proof exits")
        if independent is not None and not _slot_pattern_ok(slot,
                                                             independent):
            fail("proof exits")
    else:
        if rerun is not None:
            fail("non-runnable proof")
        if resolution_bound is not True:
            fail("non-runnable proof")
    return parts


# ---------------------------------------------------------------- seal gate


class SealBlocked(KitError):
    """seal refused; `blockers` holds every plain-language line."""

    def __init__(self, blockers):
        KitError.__init__(self, "%d blocker(s); nothing was sealed"
                          % len(blockers))
        self.blockers = list(blockers)


class _CaseView:
    """What the per-case blockers read, loaded once per case."""

    def __init__(self, folder, cid, registry, synthetic=None):
        self.folder = folder
        self.cid = cid
        self.registry = registry
        self.synthetic = synthetic
        self.used_synthetic = False
        try:
            self.slot = _slot(folder, cid)
        except KitError:
            self.slot = cid
        try:
            self.ledger = _load_ledger(folder, cid)
        except KitError:
            self.ledger = None
        self.packet = _packet_dir(folder, self.ledger)

    def packet_file(self, name):
        return os.path.join(self.packet, name) if self.packet else None

    def load_packet_json(self, name):
        path = self.packet_file(name)
        if path is None or os.path.islink(path):
            return None
        return _load_dict_or_none(path)


def _blocker_validate(folder, checks=None):
    """One line per failed validate check (proofs re-run, never skipped)."""
    if checks is None:
        checks = holdout_validate.validate_folder(folder)
    failed = []
    for c in checks:
        if not c.ok and c.name not in failed:
            failed.append(c.name)
    return ["validation failed: %s" % name for name in failed]


def _blocker_retired(folder):
    """Every current case whose content matches retired material."""
    return holdout_manifest.retired_problems(folder)


def _blocker_prepared(view):
    led = view.ledger
    if not led or not led.get("xid") or view.packet is None:
        return "cross-check not prepared for %s" % view.slot
    return None


def _blocker_revealed(view):
    if not (view.ledger or {}).get("blind_sha256"):
        return "%s: not yet revealed" % view.slot
    return None


def _blocker_workspace_fresh(view):
    """The round was judged in a registered workspace that had not seen a key
    when the packet was prepared, in a generation newer than every earlier
    revealed round of the case."""
    led = view.ledger or {}
    unbound = ("%s: cross-check round is not bound to a registered workspace"
               % view.slot)
    gen, ws = led.get("generation"), led.get("workspace")
    entry = _generation(view.registry, gen) if _is_int(gen) else None
    if entry is None or entry.get("workspace") != ws:
        return unbound
    for past in led.get("rounds", []):
        if not isinstance(past, dict) or past.get("revealed_at") is None:
            continue
        past_gen = past.get("generation")
        if not _is_int(past_gen) or gen <= past_gen:
            n = led.get("round")
            return STALE_WORKSPACE_MSG % (view.slot, n if _is_int(n) else 0,
                                          ws)
    if view.cid not in entry.get("cases", []):
        return "%s: packet is not registered in workspace %s" % (view.slot,
                                                                 ws)
    revealed_at, prepared_at = entry.get("revealed_at"), led.get("prepared_at")
    if not isinstance(revealed_at, str) or not revealed_at:
        return unbound
    if not isinstance(prepared_at, str) or not prepared_at < revealed_at:
        return "%s: packet prepared after its workspace was revealed" \
            % view.slot
    return None


def _blocker_blind_intact(view):
    path = view.packet_file("blind.json")
    frozen = view.ledger.get("blind_sha256")
    if path is None or os.path.islink(path) or not os.path.isfile(path) \
            or holdout_kit.sha256_file(path) != frozen:
        return "%s: blind verdict changed after reveal" % view.slot
    return None


def _blocker_blind_shape(view):
    if _blind_shape_problems(view.load_packet_json("blind.json")):
        return "%s: blind verdict has the wrong shape" % view.slot
    return None


def _blocker_inputs_bound(view):
    """Every input recorded at prepare and every file revealed still has the
    same sha256; re-running validate or the proof never clears this."""
    led = view.ledger
    changed = _changed_members(led.get("inputs"),
                               _input_hashes(view.folder, view.cid),
                               INPUT_MEMBERS)
    changed += _changed_members(led.get("revealed"),
                                _revealed_hashes(view.folder, view.cid),
                                REVEALED_MEMBERS)
    if changed:
        order = ("base.tar", "change.diff", "key.json", "proof-results.json",
                 "proof", "CASE-TYPES.md")
        changed.sort(key=order.index)
        return INPUTS_CHANGED_MSG % (view.slot, ", ".join(changed))
    return None


def _blocker_final_present(view):
    path = view.packet_file("final.json")
    if path is None or not os.path.lexists(path):
        return "%s: final.json missing" % view.slot
    if view.load_packet_json("final.json") is None:
        return "%s: final.json is unreadable or not a JSON object" % view.slot
    return None


def _blocker_final_bound(view):
    final = view.load_packet_json("final.json") or {}
    token = final.get("reveal_token")
    if not isinstance(token, str) or token != view.ledger.get("reveal_token"):
        return ("%s: final.json is not bound to this reveal (reveal_token "
                "mismatch)" % view.slot)
    return None


def _runnable(view):
    proof_results = _load_dict_or_none(os.path.join(
        _keys(view.folder, view.cid), "proof-results.json"))
    return not (isinstance(proof_results, dict)
                and proof_results.get("runnable") is False)


def _agreement_parts(view):
    """The failed parts of the agreement rules for this case ([] = agrees).
    proof-results.json is read once for `runnable` and the recorded exits;
    the owner's resolution counts only when its sha256 was bound at reveal
    (its prose is never read here)."""
    k = _keys(view.folder, view.cid)
    key = _load_dict_or_none(os.path.join(k, "key.json"))
    proof_results = _load_dict_or_none(os.path.join(k, "proof-results.json"))
    runnable = not (isinstance(proof_results, dict)
                    and proof_results.get("runnable") is False)
    res = os.path.join(k, "resolution.md")
    bound = view.ledger.get("resolution_sha256")
    resolution_bound = bool(
        os.path.isfile(res) and not os.path.islink(res)
        and isinstance(bound, str)
        and bound == holdout_kit.sha256_file(res))
    return agreement_problems(view.slot, key,
                              view.load_packet_json("blind.json"),
                              view.load_packet_json("final.json"),
                              runnable=runnable,
                              resolution_bound=resolution_bound,
                              recorded_exits=_recorded_exits(proof_results))


def _synthetic_covers(view):
    """True when the dry run's synthetic-agreement record (view.synthetic,
    loaded only in dry-run mode in a marked folder) covers exactly this
    case's current, well-formed real-judge round: same XID and generation,
    the frozen blind hash, and the final.json bytes on disk."""
    rec = view.synthetic
    if not isinstance(rec, dict):
        return False
    entry = rec["cases"].get(view.cid)
    led = view.ledger or {}
    final = view.packet_file("final.json")
    if not isinstance(entry, dict) or entry.get("agreement") != "synthetic" \
            or entry.get("judge_outcome") != "disagreed" \
            or entry.get("mode") != "dry-run":
        return False
    if entry.get("xid") != led.get("xid") \
            or entry.get("generation") != led.get("generation") \
            or entry.get("blind_sha256") != led.get("blind_sha256"):
        return False
    if final is None or os.path.islink(final) or not os.path.isfile(final) \
            or holdout_kit.sha256_file(final) != entry.get("final_sha256"):
        return False
    return not _final_shape_problems(view.load_packet_json("final.json"),
                                     view.slot, _runnable(view))


def _blocker_agreement(view):
    """The AGREEMENT, PROOF EXITS and NON-RUNNABLE rules. A failure is
    DISAGREE_MSG naming the failed parts; a changed input is
    INPUTS_CHANGED_MSG from _blocker_inputs_bound instead.

    Dry run only: a real-judge disagreement covered by the synthetic-
    agreement record is let through (and noted on the view); the judge's
    files are never touched, so the disagreement stays on the record."""
    parts = _agreement_parts(view)
    if parts and _synthetic_covers(view):
        view.used_synthetic = True
        return None
    if parts:
        return DISAGREE_MSG % (view.slot, ", ".join(parts))
    return None


# Per-case blockers in order; the first that fails is the case's line. Looked
# up by name at call time so each one can be patched out by a mutant test.
CASE_BLOCKERS = ("_blocker_prepared", "_blocker_revealed",
                 "_blocker_workspace_fresh", "_blocker_blind_intact",
                 "_blocker_blind_shape", "_blocker_inputs_bound",
                 "_blocker_final_present", "_blocker_final_bound",
                 "_blocker_agreement")


def _dry_run_refusal(folder, dry_run):
    """None when sealing in this mode may proceed in this folder. A real
    seal refuses any dry-run marker (any content); a dry-run seal needs a
    valid DRY-RUN.json for this folder."""
    if dry_run:
        return None if holdout_kit.dry_run_marker_ok(folder) \
            else NOT_DRY_RUN_FOLDER_MSG
    if holdout_kit.dry_run_markers_present(folder):
        return holdout_kit.DRY_RUN_REFUSED_MSG
    return None


def load_synthetic(folder):
    """The synthetic-agreement record of a dry run, strictly; None when it
    is absent or is not this kit's record for this folder."""
    path = os.path.join(folder, holdout_kit.SYNTHETIC_AGREEMENT)
    if os.path.islink(path) or not os.path.isfile(path):
        return None
    rec = _load_dict_or_none(path)
    if not isinstance(rec, dict) \
            or set(rec) != {"schema", "mode", "folder", "judged", "cases"} \
            or rec["schema"] != holdout_kit.SYNTHETIC_AGREEMENT_SCHEMA \
            or rec["mode"] != "dry-run" \
            or rec["folder"] != os.path.realpath(folder) \
            or not isinstance(rec["judged"], dict) \
            or not isinstance(rec["cases"], dict):
        return None
    return rec


def _synthetic_for(folder, dry_run):
    """The record the agreement blocker may use: only in dry-run mode, only
    in a folder with a valid dry-run marker."""
    if not dry_run or not holdout_kit.dry_run_marker_ok(folder):
        return None
    return load_synthetic(folder)


def _gate(folder, checks=None, dry_run=False):
    """(blockers, IDs sealed on synthetic agreement, IDs whose owner
    retirement the dry run waives)."""
    refusal = _dry_run_refusal(folder, dry_run)
    if refusal:
        return [refusal], set(), set()
    blockers = list(_blocker_validate(folder, checks) or [])
    waived = set()
    if dry_run:
        # A dummy case the owner retired as itself (the old 7b loop) is not
        # replaced just to seal a dry run. A leak-scan retirement, or a new
        # case that reuses retired material, still blocks.
        for cid, line, reasons in holdout_manifest.retired_matches(folder):
            if reasons == {"owner:exact"}:
                waived.add(cid)
            else:
                blockers.append(line)
    else:
        blockers += list(_blocker_retired(folder) or [])
    try:
        registry = _load_registry(folder)
    except KitError:
        registry = None
    synthetic = _synthetic_for(folder, dry_run)
    used = set()
    module = sys.modules[__name__]
    for cid in holdout_kit.case_ids(folder):
        view = _CaseView(folder, cid, registry, synthetic)
        for name in CASE_BLOCKERS:
            try:
                line = getattr(module, name)(view)
            except KitError as exc:
                line = "%s: %s" % (view.slot, exc)
            if line:
                blockers.append(line)
                break
        if view.used_synthetic:
            used.add(cid)
    return blockers, used, waived


def seal_blockers(folder, checks=None, dry_run=False):
    """Plain-language blockers, [] when the holdout may be sealed: the
    dry-run gate first (a real seal refuses any dry-run marker; a dry-run
    seal needs a marked folder), validation, retired content, then one line
    per case that fails a cross-check blocker."""
    return _gate(folder, checks, dry_run)[0]


def do_seal(folder, dry_run=False):
    """Seal when there is no blocker: copy each final.json to
    keys/<ID>/crosscheck.json, build the seal and the private inventory, and
    write SEAL.json last. Returns the seal.

    dry_run=True (a marked dry-run folder only) writes a dry-run seal:
    status "dry-run", the real judge's outcome per judged case, `agreement:
    synthetic` on every case the synthetic record let through, and
    `retired_material: waived` on a waived retirement. public_shape_problems
    rejects it, so publish and the Phase-55 rehash never accept it."""
    _refuse_if_sealed(folder)
    blockers = seal_blockers(folder, dry_run=dry_run)
    if blockers:
        raise SealBlocked(blockers)
    used, waived = set(), set()
    if dry_run:
        blockers, used, waived = _gate(folder, dry_run=True)
        if blockers:
            raise SealBlocked(blockers)
    for cid in holdout_kit.case_ids(folder):
        led = _load_ledger(folder, cid)
        src = os.path.join(_packet_dir(folder, led), "final.json")
        try:
            shutil.copyfile(src, os.path.join(_keys(folder, cid),
                                              "crosscheck.json"))
        except OSError:
            raise KitError("cannot copy the cross-check verdict of %s"
                           % _slot(folder, cid))
    seal = holdout_manifest.build_seal(folder)
    if dry_run:
        rec = load_synthetic(folder) or {}
        holdout_manifest.mark_dry_run_seal(
            seal, judged=rec.get("judged") or {}, synthetic=used,
            waived=waived)
    holdout_manifest.write_inventory(folder)
    holdout_kit.write_json_atomic(
        os.path.join(folder, holdout_manifest.SEAL_NAME), seal)
    return seal


# ---------------------------------------------------------------- diagnose
#
# Why a case failed the agreement rule, in holdout_manifest's closed
# vocabulary, sorted into a case/key problem or a tuning-side suspect. Read
# only: it recomputes agreement_problems and never changes what agrees, and
# it prints no field value (no file, line, category, prose or case ID), so
# its line may cross to the tuning session.

_JUDGE_FLAG_CHECKS = (("type_agrees", "judge-type-false"),
                      ("defect_agrees", "judge-defect-false"),
                      ("causal_failure_agrees", "judge-category-false"),
                      ("proof_agrees", "judge-proof-false"))
_KEY_CHECKS = frozenset({"category-key-other", "proof-recorded-bad"})
_JUDGE_CHECKS = frozenset({
    "type-judged-quiet", "type-judged-catch", "type-other-slot",
    "category-differs", "category-judge-other", "quiet-unconfirmed",
    "judge-type-false", "judge-defect-false", "judge-category-false",
    "final-malformed", "nonrunnable-rerun-set", "nonrunnable-unresolved"})
_PROOF_CHECKS = frozenset({"proof-rerun-differs", "proof-rerun-base-failed",
                           "proof-rerun-changed-passed"})

DIAG_ACTIONS = {
    "agrees": "this case agrees; nothing to fix for it.",
    "incomplete": ("this case's cross-check round is not complete; run "
                   "bin/holdout autopilot again (it finishes the round)."),
    "key-unsealable": (
        "the case's own key or recorded proof can never pass the agreement "
        "rule (a case/key problem). Replace it: bin/holdout retire --slot "
        "%s --reason owner, then bin/holdout autopilot --replace-retired."),
    "judge-disagrees": (
        "the independent judge, after reading the key, still disagrees (a "
        "case/key problem). Resolve it with evidence (README 7b) or replace "
        "it. Before a second replacement of the same slot, reply in the "
        "tuning session with the diagnosis line below."),
    "checker-suspect": (
        "the judge accepted the key but the mechanical check did not: the "
        "agreement check is suspect. Do NOT retire, reset or replace. Reply "
        "in the tuning session with the diagnosis line below, nothing "
        "else."),
    "proof-mismatch": (
        "the judge's re-run of the proof did not reproduce the recorded "
        "exits: the proof or the judge's environment. Do NOT retire, reset "
        "or replace. Reply in the tuning session with the diagnosis line "
        "below, nothing else."),
}


def _path_form(key_file, blind_file):
    """True when the two names are the same file written in a different
    form: one is the other with leading directories (a tree prefix such as
    changed/, or an absolute path), compared on whole path components."""
    k, b = _norm_file(key_file), _norm_file(blind_file)
    if not k or not b or k == b:
        return False
    kp, bp = k.split("/"), b.split("/")
    short, long_ = (kp, bp) if len(kp) < len(bp) else (bp, kp)
    return len(short) < len(long_) and long_[-len(short):] == short


def diagnose_parts(slot, key, blind, final, runnable=True,
                   resolution_bound=False, recorded_exits=None):
    """(cause, checks) for one case's round: ("agrees", []) exactly when
    agreement_problems is []. Same inputs as agreement_problems."""
    parts = agreement_problems(slot, key, blind, final, runnable=runnable,
                               resolution_bound=resolution_bound,
                               recorded_exits=recorded_exits)
    if not parts:
        return "agrees", []
    checks = []

    def add(check):
        if check not in checks:
            checks.append(check)

    final_ok = isinstance(final, dict)
    key = key if isinstance(key, dict) else {}
    blind = blind if isinstance(blind, dict) else {}
    final = final if final_ok else {}
    catch = slot in holdout_kit.CATCH_SLOTS

    if "type" in parts:
        verdict = blind.get("verdict")
        if catch and verdict != "catch":
            add("type-judged-quiet")
        elif not catch and verdict != "quiet":
            add("type-judged-catch")
        else:
            add("type-other-slot")
        add("judge-type-false" if final.get("type_agrees") is not True
            else "judge-flag-contradicts")
    if "defect location" in parts:
        kl, bl = key.get("location"), blind.get("location")
        both = _location_ok(kl) and _location_ok(bl)
        if both and _path_form(kl["file"], bl["file"]):
            add("location-path-form")
        elif not both or _norm_file(kl["file"]) != _norm_file(bl["file"]):
            add("location-file-differs")
        else:
            add("location-lines-apart")
        if final.get("defect_agrees") is not True:
            add("judge-defect-false")
    if "causal-failure category" in parts or "category other" in parts:
        key_cat = key.get("causal_failure_category")
        blind_cat = blind.get("defect_category")
        key_bad = key_cat not in holdout_validate.CAUSAL_CATEGORIES \
            or key_cat == holdout_validate.OTHER_CATEGORY
        if key_bad:
            add("category-key-other")
        if blind_cat == holdout_validate.OTHER_CATEGORY:
            add("category-judge-other")
        if not key_bad and blind_cat != holdout_validate.OTHER_CATEGORY:
            add("category-differs")
        add("judge-category-false"
            if final.get("causal_failure_agrees") is not True
            else "judge-flag-contradicts")
    if "quiet confirmation" in parts:
        add("quiet-unconfirmed")
    if "final flags" in parts:
        if not final_ok:
            add("final-malformed")
        flags = _JUDGE_FLAG_CHECKS if catch else (_JUDGE_FLAG_CHECKS[0],
                                                  _JUDGE_FLAG_CHECKS[3])
        for flag, check in flags:
            if final.get(flag) is not True:
                add(check)
        if runnable and _exit_pair(final.get("proof_rerun_exit")) is None:
            add("final-malformed")
    if "proof exits" in parts:
        recorded = _exit_pair(recorded_exits)
        independent = _exit_pair(final.get("proof_rerun_exit"))
        if recorded is None or not _slot_pattern_ok(slot, recorded):
            add("proof-recorded-bad")
        if independent is not None and recorded is not None \
                and independent != recorded:
            add("proof-rerun-differs")
        if independent is not None \
                and not _slot_pattern_ok(slot, independent):
            if independent["base"] != 0:
                add("proof-rerun-base-failed")
            elif catch:
                add("proof-rerun-changed-passed")
    if "non-runnable proof" in parts:
        if final.get("proof_rerun_exit") is not None:
            add("nonrunnable-rerun-set")
        if resolution_bound is not True:
            add("nonrunnable-unresolved")

    found = set(checks)
    defect_accepted = final.get("defect_agrees") is True
    if found & _KEY_CHECKS:
        cause = "key-unsealable"
    elif found & _JUDGE_CHECKS:
        cause = "judge-disagrees"
    elif "location-path-form" in found or (
            defect_accepted and found & {"location-lines-apart",
                                         "location-file-differs"}):
        cause = "checker-suspect"
    elif found & _PROOF_CHECKS:
        cause = "proof-mismatch"
    else:
        cause = "judge-disagrees"
    return cause, checks


def _diagnose_view(view):
    module = sys.modules[__name__]
    for name in CASE_BLOCKERS:
        if name == "_blocker_agreement":
            continue
        try:
            line = getattr(module, name)(view)
        except KitError:
            line = "error"
        if line:
            return "incomplete", ["round-incomplete"]
    k = _keys(view.folder, view.cid)
    proof_results = _load_dict_or_none(os.path.join(k, "proof-results.json"))
    res = os.path.join(k, "resolution.md")
    bound = view.ledger.get("resolution_sha256")
    return diagnose_parts(
        view.slot, _load_dict_or_none(os.path.join(k, "key.json")),
        view.load_packet_json("blind.json"),
        view.load_packet_json("final.json"),
        runnable=_runnable(view),
        resolution_bound=bool(
            os.path.isfile(res) and not os.path.islink(res)
            and isinstance(bound, str)
            and bound == holdout_kit.sha256_file(res)),
        recorded_exits=_recorded_exits(proof_results))


def diagnose(folder, slot=None):
    """[(slot, cause, checks)] in slot order: every case that does not agree,
    or exactly the named slot whatever its cause. Reads only; real and dry
    runs alike (the synthetic-agreement record is never consulted)."""
    try:
        registry = _load_registry(folder)
    except KitError:
        registry = None
    order = list(holdout_kit.SLOTS)
    out = []
    for cid in holdout_kit.case_ids(folder):
        view = _CaseView(folder, cid, registry)
        if slot is not None and view.slot != slot:
            continue
        cause, checks = _diagnose_view(view)
        if slot is not None or cause != "agrees":
            out.append((view.slot, cause, checks))
    return sorted(out, key=lambda o: order.index(o[0])
                  if o[0] in order else len(order))


def diagnosis_line(slot, cause, checks):
    return "diagnosis %s cause=%s checks=%s" % (
        slot, cause, ",".join(checks) if checks else "none")


# ---------------------------------------------------------------- dry run


def _real_judge_problems(view):
    """[] when a real-judge round is complete and well formed: revealed,
    blind.json intact and of the brief's shape, final.json present, bound to
    this reveal and of the VALIDITY-RULES shape."""
    for name in ("_blocker_prepared", "_blocker_revealed",
                 "_blocker_blind_intact", "_blocker_blind_shape",
                 "_blocker_final_present", "_blocker_final_bound"):
        if getattr(sys.modules[__name__], name)(view):
            return [name[len("_blocker_"):]]
    return _final_shape_problems(view.load_packet_json("final.json"),
                                 view.slot, _runnable(view))


def record_synthetic_agreement(folder, generations, dry_run=False):
    """Dry run only: record what the real judge decided for every case
    whose current round was judged by a headless session in one of
    `generations`, and write SYNTHETIC-AGREEMENT.json covering each case it
    disagreed on. Returns [(slot, "agreed"|"disagreed")] in slot order.

    The judge's blind.json and final.json are read, never written; the
    record binds their hashes, so a later change voids it. A round that is
    not well formed is a KitError (JUDGE_VERDICT_BAD_MSG): the dry run then
    cannot show the judging machinery works. Refuses (SYNTHETIC_REFUSED_MSG)
    unless dry_run is set and the folder carries a valid dry-run marker."""
    holdout_kit.refuse_if_claude_spawned(folder)
    h = os.path.realpath(folder)
    if not dry_run or not holdout_kit.dry_run_marker_ok(h):
        raise KitError(SYNTHETIC_REFUSED_MSG)
    registry = _load_registry(h)
    gens = set(generations)
    judged, covered, outcomes = {}, {}, []
    for cid in holdout_kit.case_ids(h):
        view = _CaseView(h, cid, registry)
        led = view.ledger or {}
        if led.get("generation") not in gens:
            continue
        bad = _real_judge_problems(view)
        if bad:
            raise KitError(JUDGE_VERDICT_BAD_MSG % (view.slot,
                                                    ", ".join(bad)))
        outcome = "disagreed" if _agreement_parts(view) else "agreed"
        judged[cid] = outcome
        outcomes.append((view.slot, outcome))
        if outcome == "disagreed":
            covered[cid] = {
                "mode": "dry-run", "agreement": "synthetic",
                "judge_outcome": "disagreed", "xid": led["xid"], "generation": led["generation"],
                "blind_sha256": led["blind_sha256"],
                "final_sha256": holdout_kit.sha256_file(
                    view.packet_file("final.json"))}
    holdout_kit.write_json_atomic(
        os.path.join(h, holdout_kit.SYNTHETIC_AGREEMENT),
        {"schema": holdout_kit.SYNTHETIC_AGREEMENT_SCHEMA, "mode": "dry-run",
         "folder": h, "judged": judged, "cases": covered})
    order = list(holdout_kit.SLOTS)
    return sorted(outcomes, key=lambda o: order.index(o[0])
                  if o[0] in order else len(order))


# ---------------------------------------------------------------- CLI


def add_parser(sub, name):
    if name == "crosscheck-prepare":
        p = sub.add_parser(name, help="write blind cross-check packets")
        p.add_argument("--case", metavar="ID",
                       help="prepare only this case (after a reset)")
    elif name == "crosscheck-reveal":
        p = sub.add_parser(name, help="freeze the blind verdicts of a "
                                      "workspace, then reveal its keys")
        group = p.add_mutually_exclusive_group(required=True)
        group.add_argument("xid", nargs="?", metavar="XID",
                           help="reveal the workspace holding this packet")
        group.add_argument("--ready", action="store_true",
                           help="reveal every workspace whose packets all "
                                "have a blind.json")
    elif name == "crosscheck-reset":
        p = sub.add_parser(name, help="archive a case's cross-check round "
                                      "and remove its packet")
        p.add_argument("case", metavar="ID")
        p.add_argument("--reason", required=True, choices=RESET_REASONS)
    elif name == "diagnose":
        p = sub.add_parser(name, help="say, in fixed words only, why a case "
                                      "failed the agreement rule (reads "
                                      "only)")
        p.add_argument("--slot", choices=holdout_kit.SLOTS,
                       help="diagnose only this slot")
    elif name == "seal":
        p = sub.add_parser(name, help="check every blocker, then write "
                                      "SEAL.json")
        p.add_argument("--dry-run", action="store_true",
                       help="seal a dry-run folder (writes a dry-run seal "
                            "that publish and rehash refuse)")
    else:
        raise KitError("unknown seal command")


def _cmd_prepare(args):
    mapping = prepare_crosscheck(args.folder, case_id=args.case)
    if not mapping:
        holdout_kit.print_ok("nothing to prepare")
    return 0


def _cmd_reveal(args):
    if args.ready:
        revealed, problems = reveal_ready(args.folder)
        for xid in revealed:
            holdout_kit.print_ok("revealed %s" % xid)
        for line in problems:
            holdout_kit.print_problem(line)
        if not revealed and not problems:
            holdout_kit.print_ok("nothing to reveal")
        return 1 if problems else 0
    try:
        cid = reveal(args.folder, args.xid)
    except KitError as exc:
        holdout_kit.print_problem(str(exc))
        return 1
    led = _load_ledger(args.folder, cid)
    entry = _generation(_load_registry(args.folder), led["generation"])
    for _, oled in _live_packets(args.folder, entry):
        holdout_kit.print_ok("revealed %s" % oled["xid"])
    return 0


def _cmd_reset(args):
    led = _load_ledger(args.folder, args.case) \
        if holdout_kit.ID_RE.match(args.case or "") else None
    n = (led or {}).get("round")
    reset_crosscheck(args.folder, args.case, args.reason)
    holdout_kit.print_ok("cross-check reset for %s (round %s archived). "
                         "Next: bin/holdout crosscheck-prepare --case %s"
                         % (_slot(args.folder, args.case), n, args.case))
    return 0


def _cmd_seal(args):
    try:
        seal = do_seal(args.folder,
                       dry_run=bool(getattr(args, "dry_run", False)))
    except SealBlocked as exc:
        for line in exc.blockers:
            holdout_kit.print_problem(line)
        holdout_kit.print_problem("nothing was sealed (%d blocker(s)); fix "
                                  "the lines above and run seal again"
                                  % len(exc.blockers))
        return 1
    holdout_kit.print_ok("sealed %d cases. Next: bin/holdout encrypt"
                         % len(seal["cases"]))
    return 0


def _cmd_diagnose(args):
    got = diagnose(args.folder, slot=args.slot)
    if not got:
        print("action: %s" % DIAG_ACTIONS["agrees"])
        print(diagnosis_line("all", "agrees", []))
        return 0
    for slot, cause, _ in got:
        action = DIAG_ACTIONS[cause]
        print("action %s: %s" % (slot, action % slot if "%s" in action
                                 else action))
    for slot, cause, checks in got:
        print(diagnosis_line(slot, cause, checks))
    return 0


_HANDLERS = {
    "diagnose": _cmd_diagnose,
    "crosscheck-prepare": _cmd_prepare,
    "crosscheck-reveal": _cmd_reveal,
    "crosscheck-reset": _cmd_reset,
    "seal": _cmd_seal,
}


def cmd(args):
    holdout_kit.refuse_if_claude_spawned(args.folder)
    handler = _HANDLERS.get(args.cmd)
    if handler is None:
        raise KitError("unknown seal command")
    return handler(args)
