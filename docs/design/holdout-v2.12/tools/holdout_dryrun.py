"""holdout_dryrun.py — a dummy holdout for rehearsing the whole pipeline.

`dryrun --populate` fills a freshly `setup` folder with six obviously fake
cases, so the owner can rehearse validate -> seal -> encrypt (real openssl
prompts) -> rehash -> leakscan -> scrub before any real case exists. The same
functions drive the automated end-to-end test.

What populate writes:
  * two tiny git repos, <folder>/dryrun-repos/dryrun-alpha and dryrun-beta,
    made with synthetic commits only (never the owner's repos), and their
    paths appended to kit/eligible-repos.json so validate accepts them;
  * six organic-shaped cases (C1..C3 catch, Q1..Q3 quiet), each a separate
    shell module whose feature commit rewrites every value line. A catch
    module starts printing "unsafe", so its proof fails on the changed tree;
    a quiet module keeps printing "safe". Every key and module line carries
    the "DRY RUN: synthetic" tag plus the slot and variant, so leakscan
    probes cannot collide with real repos, and no probe-length line appears
    verbatim in this source file;
  * proof-results.json recorded by actually running each proof through
    holdout_validate.run_proof (the same runner validate uses);
  * a completed blind cross-check: one packet per case in generation 1, an
    agreeing structured blind.json, the all-or-nothing reveal, and a
    final.json that echoes REVEAL-TOKEN and the recorded exits.

`replace_case` is the dummy form of "replace the slot through the finder":
it retires the old case by content first (holdout_manifest.retire_case),
removes it, writes a different change for the same slot under a fresh ID and
completes its cross-check in whatever generation prepare opens.

`replace_dummy_slot` is what `autopilot --dry-run --replace-retired` uses
after it has removed a retired case: it writes genuinely different dummy
material for the slot (new commits, so new revisions; a new module variant
and a fresh 16-hex-digit random tag, so different diff lines and key) and
refuses, removing what it wrote, if the new case still matches any
RETIRED.json entry on any field. The cross-check is left to the autopilot's
blind judging round in a fresh generation.

Imports: {os, shutil, sys, time} plus the kit modules. Test helpers are
never imported here.
"""

import os
import shutil
import sys
import time

import holdout_kit
import holdout_manifest
import holdout_seal
import holdout_validate

KitError = holdout_kit.KitError

REPOS_DIRNAME = "dryrun-repos"
REPO_NAMES = ("dryrun-alpha", "dryrun-beta")
# Slot -> (repo, causal_failure_category or None for quiet). C1 and Q2 come
# from different repos, as the validator requires.
LAYOUT = {
    "C1": ("dryrun-alpha", "missing-input-validation"),
    "C2": ("dryrun-alpha", "missing-authz-check"),
    "C3": ("dryrun-beta", "logic-error"),
    "Q1": ("dryrun-alpha", None),
    "Q2": ("dryrun-beta", None),
    "Q3": ("dryrun-beta", None),
}
SYNTHETIC_TAG = "DRY RUN: synthetic case, not real"
VALUE_LINES = 6
# Module line numbers: 1 shebang, 2 header, 3..8 values, 9 note, 10 echo.
LOCATION_START = 3
LOCATION_END = 3 + VALUE_LINES + 1
GIT_IDENTITY = ("-c", "user.name=holdout dry run",
                "-c", "user.email=dryrun@example.invalid",
                "-c", "commit.gpgsign=false",
                "-c", "core.hooksPath=/dev/null")
ORDER_RULE = "dry run: synthetic commits, newest first"
PROOF_SCRIPT = """#!/bin/sh
out=$(sh ./%s)
[ "$out" = "safe" ]
"""
POPULATED_MSG = ("dummy holdout populated with 6 synthetic cases. Next: "
                 "bin/holdout validate, then seal, encrypt, rehash, "
                 "leakscan, scrub.")
SEALED_REFUSAL = ("already sealed (SEAL.json exists); delete SEAL.json and "
                  "archive/ deliberately first")
SAME_MATERIAL_MSG = ("the new dummy material for slot %s still matches retired "
                     "material, so it was removed again; run the same command "
                     "again (it draws a fresh random tag)")


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load(path, what):
    return holdout_kit.load_json(path, what=what)


# ---------------------------------------------------------------- git


def _git(repo, *args):
    proc = holdout_kit.run_argv(["git", *GIT_IDENTITY, "-C", repo, *args],
                                timeout=120)
    if proc.returncode != 0:
        raise KitError("git %s failed in the dry-run repo %s"
                       % (args[0], os.path.basename(repo)))
    return proc.stdout


def _head(repo):
    return _git(repo, "rev-parse", "HEAD").decode("ascii").strip()


def _make_repo(path):
    if os.path.lexists(path):
        raise KitError("the dry-run repo %s already exists"
                       % os.path.basename(path))
    os.makedirs(path)
    proc = holdout_kit.run_argv(["git", *GIT_IDENTITY, "init", "-q", "-b",
                                 "main", path], timeout=120)
    if proc.returncode != 0:
        raise KitError("git init failed for the dry-run repo %s"
                       % os.path.basename(path))
    with open(os.path.join(path, "README.txt"), "w", encoding="utf-8") as fh:
        fh.write("%s: %s repo for the holdout dry run.\n"
                 % (SYNTHETIC_TAG, os.path.basename(path)))
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "dry run: initial commit")
    return os.path.realpath(path)


def _module_name(slot, variant):
    return "dummy_%s_v%d.sh" % (slot.lower(), variant)


def _module_text(slot, variant, version, verdict, nonce):
    s = slot.lower()
    lines = ["#!/bin/sh",
             "# holdout dry run module for slot %s (variant %d); %s"
             % (slot, variant, SYNTHETIC_TAG)]
    for i in range(1, VALUE_LINES + 1):
        lines.append('value_%s_%d="DRY RUN synthetic value %s-v%d-%d-%s-%s"'
                     % (s, i, slot, variant, i, version, nonce))
    # A line with a double quote and a backslash, so a JSON-escaped copy is
    # only found by leakscan's decoded pass.
    lines.append('note_%s="DRY RUN quote \\" and backslash \\\\ '
                 '(%s v%d %s %s)"' % (s, slot, variant, version, nonce))
    lines.append("echo %s" % verdict)
    return "\n".join(lines) + "\n"


def _key(slot, variant, category, nonce):
    tag = "%s (slot %s, variant %d, %s)" % (SYNTHETIC_TAG, slot, variant,
                                            nonce)
    if category is not None:
        return {"slot": slot, "class": "catch",
                "defect": "%s: the changed module prints unsafe" % tag,
                "location": {"file": _module_name(slot, variant),
                             "line_start": LOCATION_START,
                             "line_end": LOCATION_END},
                "causal_failure": "%s: the synthetic verdict line flips" % tag,
                "causal_failure_category": category}
    return {"slot": slot, "class": "quiet",
            "expected_quiet_rationale": "%s: only values change" % tag,
            "supported_behavior": "%s: the module still prints safe" % tag,
            "exposure_check": "%s: no new input reaches the module" % tag}


def _write_json(path, obj):
    holdout_kit.write_json_atomic(path, obj)


def _write_case(h, repo, slot, variant, cid, nonce=None):
    """Commit a base and a feature revision of this slot's module in `repo`
    and write the sealed case `cid` from them, proof results included."""
    category = LAYOUT[slot][1]
    catch = category is not None
    # A fresh random tag per case: no probe built from this case can already
    # sit in any transcript, history or source file on the tuning side.
    if nonce is None:
        nonce = holdout_kit.new_xcheck_id()[2:]
    name = _module_name(slot, variant)
    module = os.path.join(repo, name)
    with open(module, "w", encoding="utf-8") as fh:
        fh.write(_module_text(slot, variant, "old", "safe", nonce))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "dry run: base %s v%d" % (slot, variant))
    base_rev = _head(repo)
    with open(module, "w", encoding="utf-8") as fh:
        fh.write(_module_text(slot, variant, "new",
                              "unsafe" if catch else "safe", nonce))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m",
         "dry run: change %s v%d" % (slot, variant))
    feature_rev = _head(repo)

    sealed = holdout_kit.sealed_dir(h)
    cdir = os.path.join(sealed, "cases", cid)
    kdir = os.path.join(sealed, "keys", cid)
    os.makedirs(cdir)
    os.makedirs(os.path.join(kdir, "proof"))
    with open(os.path.join(cdir, "base.tar"), "wb") as fh:
        fh.write(_git(repo, "archive", "--format=tar", base_rev))
    with open(os.path.join(cdir, "change.diff"), "wb") as fh:
        fh.write(_git(repo, "diff", "--no-color", "--no-ext-diff",
                      "--no-textconv", "--src-prefix=a/", "--dst-prefix=b/",
                      base_rev, feature_rev))
    _write_json(os.path.join(cdir, "case.json"),
                {"id": cid, "base": "base.tar", "diff": "change.diff",
                 "apply_with": "git apply"})
    _write_json(os.path.join(kdir, "key.json"),
                _key(slot, variant, category, nonce))
    _write_json(os.path.join(kdir, "provenance.json"), {
        "slot": slot, "kind": "organic", "source_repo": repo,
        "repo_name": os.path.basename(repo), "repo_in_b3": False,
        "base_rev": base_rev, "feature_rev": feature_rev,
        "search": {"budget": 25, "order_rule": ORDER_RULE, "screened": 1,
                   "rejections": []},
        "selected_using_reviewer_output": False, "found_at": _now_iso()})
    run = os.path.join(kdir, "proof", "run")
    with open(run, "w", encoding="utf-8") as fh:
        fh.write(PROOF_SCRIPT % name)
    os.chmod(run, 0o755)
    record_proof_results(h, cid)


def record_proof_results(folder, case_id):
    """Run the case's proof on the base and the changed export (the runner
    validate uses) and write proof-results.json from what it observed."""
    results = {"runnable": True}
    for which in ("base", "changed"):
        code, digest = holdout_validate.run_proof(folder, case_id, which)
        results[which] = {"exit": code, "output_sha256": digest,
                          "ran_at": _now_iso()}
    _write_json(os.path.join(holdout_kit.sealed_dir(folder), "keys", case_id,
                             "proof-results.json"), results)
    return results


def _new_id(folder):
    taken = set(holdout_kit.case_ids(folder))
    while True:
        cid = holdout_kit.new_case_id()
        if cid not in taken:
            return cid


def _add_eligible(h, repos):
    path = os.path.join(h, "kit", holdout_kit.ELIGIBLE_REPOS)
    data = holdout_kit.load_json(path, required={"repos": list},
                                 what="kit/eligible-repos.json")
    for repo in repos:
        if repo not in data["repos"]:
            data["repos"].append(repo)
    _write_json(path, data)


# ---------------------------------------------------------------- cross-check


def _packet(folder, ledger):
    path = holdout_seal._packet_dir(folder, ledger)
    if path is None:
        raise KitError("the cross-check ledger names no live packet")
    return path


def _ledger(folder, cid):
    return holdout_seal._load_ledger(folder, cid)


def _blind(key):
    slot = key["slot"]
    reasoning = "%s: blind verdict written by the dry run" % SYNTHETIC_TAG
    if slot in holdout_kit.CATCH_SLOTS:
        return {"verdict": "catch", "type_guess": slot,
                "location": dict(key["location"]),
                "defect_category": key["causal_failure_category"],
                "reasoning": reasoning}
    return {"verdict": "quiet", "type_guess": slot, "location": None,
            "defect_category": None, "reasoning": reasoning}


def _final(packet):
    rev = os.path.join(packet, "revealed")
    with open(os.path.join(rev, "REVEAL-TOKEN"), encoding="utf-8") as fh:
        token = fh.read().strip()
    key = _load(os.path.join(rev, "key.json"), "the revealed key")
    results = _load(os.path.join(rev, "proof-results.json"),
                    "the revealed proof results")
    exits = None
    if results.get("runnable") is True:
        exits = {"base": results["base"]["exit"],
                 "changed": results["changed"]["exit"]}
    confirmed = None
    if key.get("slot") in holdout_kit.QUIET_SLOTS:
        confirmed = {"supported_behavior": True, "exposure_check": True}
    return {"reveal_token": token, "type_agrees": True, "defect_agrees": True,
            "causal_failure_agrees": True, "proof_agrees": True,
            "proof_rerun_exit": exits, "quiet_confirmed": confirmed,
            "notes": "%s: final verdict written by the dry run"
                     % SYNTHETIC_TAG}


def _complete(folder, cids, prepare_all=False):
    """Prepare (when no live packet), write the blind verdicts, reveal every
    generation that holds them, then write the final verdicts. Each case is
    completed in the workspace its ledger names."""
    pending = [c for c in cids if not (_ledger(folder, c) or {}).get("xid")]
    if pending:
        if prepare_all:
            holdout_seal.prepare_crosscheck(folder)
        else:
            for cid in pending:
                holdout_seal.prepare_crosscheck(folder, case_id=cid)
    gens = set()
    for cid in cids:
        led = _ledger(folder, cid)
        if led.get("blind_sha256"):
            continue
        packet = _packet(folder, led)
        blind = os.path.join(packet, "blind.json")
        if not os.path.lexists(blind):
            key = _load(os.path.join(holdout_kit.sealed_dir(folder), "keys",
                                     cid, "key.json"), "a key.json")
            _write_json(blind, _blind(key))
        gens.add(led["generation"])
    for gen in sorted(gens):
        holdout_seal.reveal_workspace(folder, gen)
    for cid in cids:
        packet = _packet(folder, _ledger(folder, cid))
        final = os.path.join(packet, "final.json")
        if not os.path.lexists(final):
            _write_json(final, _final(packet))


def complete_case_crosscheck(folder, case_id):
    """prepare --case (unless a packet is live), blind, reveal and final for
    one case, in the workspace its ledger names (a fresh generation when the
    newest one has already been revealed)."""
    holdout_kit.refuse_if_claude_spawned(folder)
    _complete(os.path.realpath(folder), [case_id])


# ---------------------------------------------------------------- populate


def populate(folder, repos_parent=None, complete_crosscheck=True):
    """Fill a freshly set-up holdout with six synthetic cases and a completed
    cross-check; return {slot: ID}. The folder is then ready for validate and
    seal.

    With complete_crosscheck=False only the cases, keys, proofs and eligible
    repos are written (what a finder leaves behind); the cross-check is left
    to its sessions."""
    holdout_kit.refuse_if_claude_spawned(folder)
    if not folder or not os.path.isdir(folder):
        raise KitError("the holdout folder does not exist; run setup first")
    h = os.path.realpath(folder)
    for rel in ("kit/" + holdout_kit.ELIGIBLE_REPOS, "sealed/cases",
                "sealed/keys", "xcheck"):
        if not os.path.exists(os.path.join(h, rel)):
            raise KitError("the holdout folder is not set up; run setup first")
    if os.path.lexists(os.path.join(h, holdout_manifest.SEAL_NAME)):
        raise KitError(SEALED_REFUSAL)
    if holdout_kit.case_ids(h):
        raise KitError("folder already has cases; populate needs a freshly "
                       "set-up folder")
    parent = os.path.realpath(repos_parent or os.path.join(h, REPOS_DIRNAME))
    repos = {name: _make_repo(os.path.join(parent, name))
             for name in REPO_NAMES}
    _add_eligible(h, [repos[name] for name in REPO_NAMES])
    ids = {}
    for slot in holdout_kit.SLOTS:
        cid = _new_id(h)
        ids[slot] = cid
        _write_case(h, repos[LAYOUT[slot][0]], slot, 0, cid)
    if complete_crosscheck:
        _complete(h, [ids[s] for s in holdout_kit.SLOTS], prepare_all=True)
    return ids


# ---------------------------------------------------------------- replace


def _case_of_slot(folder, slot):
    found = [cid for cid in holdout_kit.case_ids(folder)
             if holdout_validate.slot_of(folder, cid) == slot]
    if len(found) != 1:
        raise KitError("no single case holds slot %s" % slot)
    return found[0]


def _next_variant(repo, slot):
    prefix = "dummy_%s_v" % slot.lower()
    used = []
    for name in os.listdir(repo):
        if name.startswith(prefix) and name.endswith(".sh"):
            digits = name[len(prefix):-len(".sh")]
            if digits.isdigit():
                used.append(int(digits))
    return max(used) + 1 if used else 0


def replace_case(folder, slot):
    """Replace a slot with a different change under a fresh ID; return
    (old ID, new ID).

    The old case is retired by content BEFORE anything is removed, then its
    case and key folders and its live packet go, a new variant of the slot's
    module is committed and written as the new case, and its cross-check is
    completed (in a fresh generation when the newest one was revealed)."""
    holdout_kit.refuse_if_claude_spawned(folder)
    h = os.path.realpath(folder)
    if os.path.lexists(os.path.join(h, holdout_manifest.SEAL_NAME)):
        raise KitError(SEALED_REFUSAL)
    if slot not in holdout_kit.SLOTS:
        raise KitError("slot must be one of C1..Q3")
    old = _case_of_slot(h, slot)
    sealed = holdout_kit.sealed_dir(h)
    prov = _load(os.path.join(sealed, "keys", old, "provenance.json"),
                 "a provenance.json")
    repo = prov.get("source_repo")
    if not isinstance(repo, str) or not os.path.isdir(os.path.join(repo,
                                                                   ".git")):
        raise KitError("the dry-run repo of slot %s is missing" % slot)
    holdout_manifest.retire_case(h, old, "owner")
    if (_ledger(h, old) or {}).get("xid"):
        holdout_seal.reset_crosscheck(h, old, "owner")
    for part in ("cases", "keys"):
        shutil.rmtree(os.path.join(sealed, part, old))
    new = _new_id(h)
    _write_case(h, repo, slot, _next_variant(repo, slot), new)
    _complete(h, [new])
    return old, new


def _replacement_nonce():
    """A fresh 16-hex-digit tag drawn from the kit's secrets-backed id
    generator (never a seed): twice the entropy of a populate tag."""
    return holdout_kit.new_xcheck_id()[2:] + holdout_kit.new_xcheck_id()[2:]


def _retired_matches(folder, case_id):
    """The fields on which case `case_id` matches any RETIRED.json entry:
    the ones retired_problems checks (all three source revisions together,
    diff bytes, changed-line set, key) plus either revision on its own."""
    fp = holdout_manifest.case_fingerprint(folder, case_id)
    mine = {fp["source"].get("base_rev"), fp["source"].get("feature_rev")}
    mine.discard(None)
    found = []
    for entry in holdout_manifest.load_retired(folder)["retired"]:
        found += holdout_manifest._matched_fields(fp, entry)
        theirs = {entry["source"].get("base_rev"),
                  entry["source"].get("feature_rev")}
        if mine & theirs:
            found.append("revision")
    return found


def _slot_repo(h, slot):
    """The slot's dry-run repo; re-created (and listed as eligible) if it is
    gone."""
    path = os.path.join(h, REPOS_DIRNAME, LAYOUT[slot][0])
    if os.path.isdir(os.path.join(path, ".git")):
        return os.path.realpath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    repo = _make_repo(path)
    _add_eligible(h, [repo])
    return repo


def _remove_trees(h, case_id):
    sealed = holdout_kit.sealed_dir(h)
    for part in ("cases", "keys"):
        path = os.path.join(sealed, part, case_id)
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)


def replace_dummy_slot(folder, slot, case_id):
    """Write genuinely different dummy material for `slot` as the new case
    `case_id`; return case_id.

    The slot's retired case must already be gone. New commits give new
    revisions; the next module variant and a fresh random tag change every
    diff line and the key. If the new case still matches retired material on
    any field it is removed again and KitError(SAME_MATERIAL_MSG) is raised.
    No cross-check is written: the autopilot judges the case blind in a
    fresh generation."""
    holdout_kit.refuse_if_claude_spawned(folder)
    h = os.path.realpath(folder)
    if os.path.lexists(os.path.join(h, holdout_manifest.SEAL_NAME)):
        raise KitError(SEALED_REFUSAL)
    if slot not in holdout_kit.SLOTS:
        raise KitError("slot must be one of C1..Q3")
    if not isinstance(case_id, str) or not holdout_kit.ID_RE.match(case_id):
        raise KitError("not an opaque case id")
    ids = holdout_kit.case_ids(h)
    if case_id in ids:
        raise KitError("case %s already exists" % case_id)
    for cid in ids:
        try:
            held = holdout_validate.slot_of(h, cid)
        except KitError:
            continue
        if held == slot:
            raise KitError("slot %s still holds a case; remove the retired "
                           "case first" % slot)
    repo = _slot_repo(h, slot)
    _write_case(h, repo, slot, _next_variant(repo, slot), case_id,
                nonce=_replacement_nonce())
    if _retired_matches(h, case_id):
        _remove_trees(h, case_id)
        raise KitError(SAME_MATERIAL_MSG % slot)
    return case_id


# ---------------------------------------------------------------- CLI


def add_parser(sub, name):
    if name != "dryrun":
        raise KitError("unknown dryrun command")
    p = sub.add_parser(name, help="populate a dummy holdout for the dry run")
    p.add_argument("--populate", action="store_true", required=True,
                   help="write six synthetic cases and complete their "
                        "cross-check (a freshly set-up folder only)")


def cmd(args):
    holdout_kit.refuse_if_claude_spawned(args.folder)
    if args.cmd != "dryrun" or not args.populate:
        raise KitError("unknown dryrun command")
    populate(args.folder)
    sys.stdout.flush()
    holdout_kit.print_ok(POPULATED_MSG)
    return 0

