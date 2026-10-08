"""holdout_seal.py — the blind cross-check and the `seal` gate of the holdout kit.

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
                "crosscheck-reset <ID> --reason resolved) or replace the case.")
INPUTS_CHANGED_MSG = ("Case %s: sealed inputs changed after the cross-check "
                      "(%s). Run crosscheck-reset <ID> --reason inputs-changed "
                      "and redo the cross-check for this case.")
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
LAUNCH_MSG = ("fresh cross-check workspace %s. Close the previous cross-check "
              "session, then launch %s (a new session; /login if asked) and "
              "type: Read CROSSCHECK-BRIEF.md and begin.")


# ---------------------------------------------------------------- small helpers


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
            raise KitError("%s: sealed inputs changed since crosscheck-prepare "
                           "(%s); run crosscheck-reset %s --reason "
                           "inputs-changed" % (_slot(folder, cid),
                                               ", ".join(changed), cid))
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
    elif name == "seal":
        sub.add_parser(name, help="check every blocker, then write SEAL.json")
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
    for other, oled in _live_packets(args.folder, entry):
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


_HANDLERS = {
    "crosscheck-prepare": _cmd_prepare,
    "crosscheck-reveal": _cmd_reveal,
    "crosscheck-reset": _cmd_reset,
}


def cmd(args):
    holdout_kit.refuse_if_claude_spawned(args.folder)
    handler = _HANDLERS.get(args.cmd)
    if handler is None:
        raise KitError("unknown seal command")
    return handler(args)
