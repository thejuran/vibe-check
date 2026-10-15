#!/usr/bin/env python3
"""fixharness.py — one command per accepted-fix harness run.

  fixharness.py run --case <id> --mode default|gsd --kind preservation|clean
                    --out <dir> [--candidate <rev>] [--manifest <path>]
                    [--command review|deep-review]
  fixharness.py probe-sandbox --out <dir> [--candidate <rev>]
  fixharness.py replay --case <id> --mode … --kind … --messages <jsonl> --out <dir>
  fixharness.py check --run <dir>

`run` composes, in this order and never otherwise:

  workspace → plugin snapshot → copy → seed (+ obligation ledger snapshot 0)
  → sentinels (preservation) → session settings → preflight (sandbox probe
  + freeze identity) → drive (state observed read-only at every card and
  every turn)
  → final ledger observation → obligations.json → verdict → run.json

Everything that writes into the copy happens before `drive`; a phase flag
refuses any of those writers once the session has launched. The preflight
refuses to launch without a passed, current sandbox probe record, and
without an exact match against the active freeze manifest.

The plugin snapshot is the candidate commit's tree (`--candidate`, default
the manifest's `candidate_sha`), never the working tree. The session is
launched with the manifest's fix-harness `launch_model` and the same
environment the identity check verified; an init-reported model that
differs fails the run. Each retry is a new invocation and is checked again.

Exit codes: 0 COMPLETE (or probe passed / replay without failure / check
clean), 1 FAILED, 2 usage, preflight or driver error (no record written).

The SDK is imported only by `harness_driver_sdk.drive`; this module runs on
any Python 3.9+ for `check`, `replay` and `--help`.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_cards  # noqa: E402
import harness_driver_sdk  # noqa: E402
import harness_fixture  # noqa: E402
import harness_record  # noqa: E402
import harness_repeats  # noqa: E402
import harness_sandbox  # noqa: E402
import harness_seed  # noqa: E402
import harness_sentinels  # noqa: E402
import harness_verdict  # noqa: E402

HARNESS_DIR = HERE.parent
PROBE_RECORD_PATH = str(HARNESS_DIR / "fixtures" / "probe" /
                        "sandbox-probe.json")
# Where the committed plugin tree lives in the checkout. The snapshot itself
# is materialized from a commit (plugin_sha / candidate_sha in the record).
PLUGIN_SOURCE_PATH = os.path.join(harness_sandbox.CHECKOUT_ROOT, "plugins",
                                  "vibe-check")
PROBE_DEFAULT_CANDIDATE = "HEAD"
FAIL_MODEL_DIFFERS = "model differs: launched %s init %s"
# The holdout kit's directory, named only so `--out` can refuse it. Built by
# concatenation so no harness source spells the name (test_harness_isolation).
HOLDOUT_DIR = os.path.join(harness_sandbox.CHECKOUT_ROOT, "docs", "design",
                           "holdout-" + "v2.12")
GIT_TIMEOUT = 30
KINDS = ("preservation", "clean")
COMMANDS = ("review", "deep-review")
TOOL_DIR = ".turingmind"

# The owner's documented close-out after a default-diff loop that leaves
# nothing to review (D-24), and the clean-tree default-diff entry (Pitfall 6).
FINALIZE_COMMAND = "/vibe-check:review --finalize"

FAIL_CLEAN_TREE = "clean-tree checkpoint: tree not clean before close out"
FAIL_CLEAN_TREE_NEVER = "clean-tree checkpoint never reached"
FAIL_FINALIZE_LOOP = "finalize did not close out"
FAIL_REPEAT = "repeat: card re-asked under unchanged evidence"
FAIL_REPEAT_AFTER_FINALIZE = ("repeat: fix-loop card re-asked after a "
                              "finalize fix answer")
FAIL_EXHAUSTED = "exhausted: card bound exceeded"
FAIL_PROBE_CARD = "probe session asked a question"


class UsageError(Exception):
    """Bad arguments; exit 2."""


# --------------------------------------------------------------------------- #
# read-only git
# --------------------------------------------------------------------------- #
def _git_read(root, *args):
    """git as an argv list, no optional locks (a plain read never rewrites
    the index), never through a shell."""
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    proc = subprocess.run(["git", "-C", root, *args], env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=GIT_TIMEOUT, check=False)
    if proc.returncode != 0:
        raise RuntimeError("git %s failed: %s"
                           % (args[0], proc.stderr.decode("utf-8",
                                                          "replace").strip()))
    return proc.stdout.decode("utf-8", "replace")


def head_sha(root):
    return _git_read(root, "rev-parse", "HEAD").strip()


def status_v2(root):
    return _git_read(root, "status", "--porcelain=v2", "-z")


def _status_outside_tool_dir(status):
    entries = [e for e in status.split("\0") if e.strip()]
    return [e for e in entries
            if not any(tok == TOOL_DIR or tok.startswith(TOOL_DIR + "/")
                       for tok in e.split())]


# --------------------------------------------------------------------------- #
# phase flag (D-21)
# --------------------------------------------------------------------------- #
class Phase:
    """Records the pre-launch writers and refuses any of them after launch."""

    def __init__(self):
        self.launched = False
        self.steps = []

    def pre(self, name, fn, *args, **kwargs):
        if self.launched:
            raise RuntimeError("pre-launch step %s after launch" % name)
        self.steps.append(name)
        return fn(*args, **kwargs)

    def launch(self):
        self.steps.append("drive")
        self.launched = True


# --------------------------------------------------------------------------- #
# the core the driver calls
# --------------------------------------------------------------------------- #
def entry_for(mode, kind, phase_id, command="review"):
    """(prompt, entry) for one run of the matrix (RESEARCH Pitfall 6)."""
    base = "/vibe-check:" + command
    if mode == "default" and kind == "clean":
        if command == "review":
            return FINALIZE_COMMAND, "finalize"
        return base + " --finalize", "finalize"
    if mode == "gsd":
        return "%s %s" % (base, phase_id), "review"
    return base, "review"


class Core:
    """Cards, repeats, obligation ledger, evidence and the clean-tree
    checkpoint for one run. Reads the copy; never writes it."""

    def __init__(self, copy, state_path, seeded, mode, kind, command="review",
                 ledger=None, repeats=None):
        self.copy = copy
        self.state_path = str(state_path)
        self.seeded = tuple(seeded.seeded_identity) \
            if hasattr(seeded, "seeded_identity") else tuple(seeded)
        self.seeded_hash = getattr(seeded, "stable_hash", None)
        self.mode = mode
        self.kind = kind
        self.command = command
        self.ledger = ledger if ledger is not None \
            else harness_verdict.ObligationLedger()
        self.repeats = repeats if repeats is not None \
            else harness_repeats.Ledger()
        self.cards = 0
        self.questions = 0
        self.turn_end_questions = 0
        self.owner_commands = 0
        self.deferred_non_seeded = 0
        self.answer_seconds = 0.0
        self.clean_tree_checkpoint = None
        self.fail_reasons = []

    # -- reads ------------------------------------------------------------ #
    def observe_state(self, label):
        """Feed the obligation ledger from the plugin's live state file:
        one read of the file and one `git rev-parse HEAD`, nothing else."""
        self.ledger.observe(harness_verdict.snapshot_obligations(
            self.state_path), label, head_sha(self.copy.root))

    def collect_evidence(self):
        try:
            with open(self.state_path, "rb") as fh:
                state = fh.read()
        except FileNotFoundError:
            state = b""
        return harness_repeats.evidence_fingerprint(
            head_sha(self.copy.root), status_v2(self.copy.root), state)

    def seeded_resolved(self):
        """The seeded finding has left the open set in the latest snapshot.

        Fail-closed: the plugin can re-hash a carried finding after the fix
        commit moves its line, so the seeded hash being gone is not enough.
        Any open finding left in the seeded file counts as not resolved.
        """
        snaps = self.ledger.snapshots
        if not snaps or self.seeded_hash is None:
            return False
        last = snaps[-1]
        if last.get("absent") or last.get("malformed"):
            return False
        hashes = last.get("hashes", {})
        if self.seeded_hash in hashes:
            return False
        return not any(isinstance(v, dict) and v.get("file") == self.seeded[0]
                       for v in hashes.values())

    def before_close_out(self):
        """FLOW-04: record the tree outside `.turingmind/` right before the
        session is told to close out. Returns a fail reason or None."""
        status = status_v2(self.copy.root)
        rest = _status_outside_tool_dir(status)
        self.clean_tree_checkpoint = {"passed": not rest,
                                      "status": "\n".join(rest)}
        if self.kind == "clean" and rest:
            return FAIL_CLEAN_TREE
        return None

    # -- cards ------------------------------------------------------------ #
    def _rows(self, kind, questions):
        if kind in (harness_cards.FIX_LOOP, harness_cards.FINALIZE):
            return harness_cards.parse_rows(questions[0]["question"])
        if kind == harness_cards.FIX_LOOP_SELECT:
            return [e[2] for e in harness_cards._select_rows(
                questions, self.seeded[1])]
        return []

    def _fail(self, reason, asked=0):
        self.fail_reasons.append(reason)
        return harness_cards.Decision({}, asked, 0, reason)

    def on_card(self, input_data, evidence):
        started = time.monotonic()
        try:
            return self._on_card(input_data, evidence)
        finally:
            self.answer_seconds += time.monotonic() - started

    def _on_card(self, input_data, evidence):
        kind = harness_cards.classify_card(input_data)
        questions = harness_cards._questions(input_data) or []
        self.cards += 1
        self.questions += len(questions)
        rows = self._rows(kind, questions) if questions else []
        if kind in (harness_cards.FIX_LOOP, harness_cards.FIX_LOOP_SELECT) \
                and self.repeats.observe_fix_loop_after_finalize(
                    rows, evidence) == harness_repeats.REPEAT:
            return self._fail(FAIL_REPEAT_AFTER_FINALIZE, len(questions))
        decision = harness_cards.answer_card(
            kind, input_data, self.seeded,
            seeded_resolved=self.seeded_resolved())
        fixed = []
        if kind == harness_cards.FINALIZE and not decision.fail:
            fixed = [r for r in rows
                     if harness_cards._find_seeded([r], self.seeded)[0]]
        text = "\n".join(q["question"] for q in questions)
        status = self.repeats.observe(
            harness_repeats.card_key(kind, rows, text), evidence,
            decision.answers, questions=0, fixed_rows=fixed)
        if status == harness_repeats.REPEAT:
            return self._fail(FAIL_REPEAT, len(questions))
        if status == harness_repeats.EXHAUSTED:
            return self._fail(FAIL_EXHAUSTED, len(questions))
        if decision.fail:
            return self._fail(decision.fail, len(questions))
        if kind == harness_cards.STOP:
            reason = self.before_close_out()
            if reason:
                return self._fail(reason, len(questions))
        self.deferred_non_seeded += decision.deferred_non_seeded
        return decision

    # -- turn ends -------------------------------------------------------- #
    def on_turn_end(self, text):
        kind = harness_cards.classify_turn_end(text)
        if kind == harness_cards.UNKNOWN:
            self.turn_end_questions += 1
        if kind in (harness_cards.NO_CHANGES, harness_cards.NO_NEW_CHANGES,
                    harness_cards.NO_ISSUES) and self.owner_commands:
            self.fail_reasons.append(FAIL_FINALIZE_LOOP)
            return ("fail", FAIL_FINALIZE_LOOP)
        args = self.copy.phase_id if self.mode == "gsd" else ""
        nxt = harness_cards.next_owner_command(kind, self.command, args or "")
        if nxt.fail:
            self.fail_reasons.append(nxt.fail)
            return ("fail", nxt.fail)
        if nxt.command is None:
            return ("done", None)
        reason = self.before_close_out()
        if reason:
            self.fail_reasons.append(reason)
            return ("fail", reason)
        self.owner_commands += 1
        self.ledger.observe(harness_verdict.snapshot_obligations(
            self.state_path), "owner_command", head_sha(self.copy.root))
        return ("command", nxt.command)

    def decisions(self):
        return {"cards": self.cards, "questions": self.questions,
                "turn_end_questions": self.turn_end_questions,
                "owner_commands": self.owner_commands,
                "repeats": self.repeats.repeats,
                "deferred_non_seeded": self.deferred_non_seeded}


class ProbeCore:
    """The probe asks no questions; any card fails it, any turn end ends it."""

    def __init__(self):
        self.fail_reasons = []

    def observe_state(self, label):
        return None

    def collect_evidence(self):
        return ""

    def on_card(self, input_data, evidence):
        self.fail_reasons.append(FAIL_PROBE_CARD)
        return harness_cards.Decision({}, 0, 0, FAIL_PROBE_CARD)

    def on_turn_end(self, text):
        return ("done", None)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def sdk_version():
    try:
        return importlib.metadata.version("claude-agent-sdk")
    except importlib.metadata.PackageNotFoundError:
        return None


def _atomic_write(path, text):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".fixharness-", suffix=".tmp",
                               dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _is_under(path, root):
    return path == root or path.startswith(root.rstrip("/") + "/")


def _check_case(case_id):
    if not isinstance(case_id, str) or "/" in case_id or os.sep in case_id \
            or "\\" in case_id:
        raise UsageError("case id must not contain a path separator")
    try:
        return harness_fixture.load_recipe(case_id)
    except (ValueError, FileNotFoundError):
        raise UsageError("unknown case id")


def _load_key(case_id):
    with open(os.path.join(harness_sandbox.KEYS_DIR, case_id + ".json"),
              "r", encoding="utf-8") as fh:
        return json.load(fh)


def _out_dir(raw, must_be_empty=True):
    out = os.path.realpath(os.path.abspath(raw))
    if _is_under(out, os.path.realpath(HOLDOUT_DIR)):
        raise UsageError("--out must not be under the holdout directory")
    if must_be_empty and os.path.isdir(out) and os.listdir(out):
        raise UsageError("--out must be a new or empty directory")
    return out


def _candidate(raw):
    """The full sha of the commit the plugin snapshot is taken from."""
    try:
        return harness_sandbox.resolve_commit(harness_sandbox.CHECKOUT_ROOT,
                                              raw)
    except harness_sandbox.SandboxError as exc:
        raise UsageError("--candidate: %s" % exc)


def _launch_model(manifest):
    """The frozen fix-harness launch model; never defaulted."""
    try:
        value = manifest["runners"]["fix-harness"]["launch_model"]["value"]
    except (KeyError, TypeError):
        value = None
    if not isinstance(value, str) or not value:
        raise UsageError("freeze manifest names no fix-harness launch_model")
    return value


def _model_problems(launched, init_model):
    """The session must run on the model it was launched with: an init
    message reporting another model fails the run."""
    if init_model != launched:
        return [FAIL_MODEL_DIFFERS % (launched, init_model)]
    return []


def _freeze_manifest(raw):
    """(path, manifest, launch_model, error line). A missing or unloadable
    manifest is a preflight refusal, never a pass."""
    try:
        path, manifest = harness_sandbox.load_freeze_manifest(raw)
    except harness_sandbox.NoManifestError:
        return None, None, None, harness_sandbox.NO_MANIFEST_PROBLEM
    except Exception as exc:  # noqa: BLE001 - FreezeError and I/O alike
        return None, None, None, "%s: %s" % (
            harness_sandbox.FREEZE_MISMATCH_PROBLEM, exc)
    return path, manifest, _launch_model(manifest), None


def _transcript_events(out):
    path = os.path.join(out, harness_driver_sdk.TRANSCRIPT_NAME)
    events = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    events.append(json.loads(line))
                except ValueError:
                    continue
    except FileNotFoundError:
        pass
    return events


def obligation_counts(ledger, dispositions):
    """Record `obligations` from the ledger and the verdict's dispositions.

    A ledger hash the verdict did not dispose of (e.g. the state was never
    archived, so conservation could not be judged) counts as `missing`.
    """
    disp = {h: dispositions.get(h, "missing") for h in ledger.all_hashes()}
    counts = {"tracked": len(disp), "snapshots": len(ledger.snapshots)}
    for name in ("resolved", "fix_verified", "decided", "downgraded",
                 "regression", "missing", "ambiguous"):
        counts[name] = sum(1 for v in disp.values() if v == name)
    open_hashes = sorted(h for h, v in disp.items() if v == "visible_open")
    counts["visible_open_nonblocking"] = len(open_hashes)
    counts["visible_open_nonblocking_hashes"] = open_hashes
    return counts


# --------------------------------------------------------------------------- #
# run
# --------------------------------------------------------------------------- #
def _drive(*args, **kwargs):
    return harness_driver_sdk.drive(*args, **kwargs)


def run(argv):
    parser = argparse.ArgumentParser(prog="fixharness.py run")
    parser.add_argument("--case", required=True)
    parser.add_argument("--mode", required=True, choices=harness_fixture.MODES)
    parser.add_argument("--kind", required=True, choices=KINDS)
    parser.add_argument("--out", required=True)
    parser.add_argument("--candidate", default=None)
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--command", default="review", choices=COMMANDS)
    args = parser.parse_args(argv)
    try:
        recipe = _check_case(args.case)
        out = _out_dir(args.out)
        manifest_path, manifest, launch_model, refusal = \
            _freeze_manifest(args.manifest)
        if refusal:
            print("fixharness: preflight: %s" % refusal, file=sys.stderr)
            return 2
        candidate = _candidate(args.candidate or manifest.get("candidate_sha"))
    except UsageError as exc:
        print("fixharness: %s" % exc, file=sys.stderr)
        return 2
    key = _load_key(args.case)
    os.makedirs(out, exist_ok=True)
    # One environment, computed once: the identity check verifies exactly
    # what the session is handed.
    session_env = harness_driver_sdk.session_env(os.environ)
    phase = Phase()

    ws = phase.pre("make_workspace", harness_sandbox.make_workspace)
    snapshot = phase.pre("snapshot_plugin",
                         harness_sandbox.snapshot_plugin_from_commit,
                         harness_sandbox.CHECKOUT_ROOT, candidate, ws)
    copy = phase.pre("build_copy", harness_fixture.build_copy, recipe,
                     args.mode, ws)
    pre_run_head = head_sha(copy.root)
    state_path = phase.pre("seed_state", harness_seed.seed_state, copy, key,
                           args.mode)
    core = Core(copy, state_path, state_path, args.mode, args.kind,
                args.command)
    snap0 = harness_verdict.snapshot_obligations(state_path)
    if not snap0 or snap0.get("malformed"):
        print("fixharness: seeding produced no readable state",
              file=sys.stderr)
        return 2
    phase.pre("ledger_seed", core.ledger.observe, snap0, "seed", pre_run_head)
    core.ledger.mark_seeded(snap0["hashes"])
    sentinels = None
    if args.kind == "preservation":
        sentinels = phase.pre("plant", harness_sentinels.plant, copy, recipe)
        _atomic_write(os.path.join(out, "sentinels.json"),
                      sentinels.to_json() + "\n")
    settings = harness_sandbox.build_session_settings(copy.root,
                                                      snapshot.path, out)
    problems, identity = phase.pre(
        "preflight", harness_sandbox.preflight_with_identity, copy.root,
        snapshot.path, settings, PROBE_RECORD_PATH, sdk_version(),
        manifest_path=manifest_path, env=session_env,
        launch_model=launch_model, candidate_sha=snapshot.git_sha)
    if problems or identity is None:
        for p in problems or [harness_sandbox.NO_MANIFEST_PROBLEM]:
            print("fixharness: preflight: %s" % p, file=sys.stderr)
        return 2
    print("fixharness: identity manifest_id=%s check_digest=%s "
          "candidate_sha=%s" % (identity.manifest_id, identity.check_digest,
                                identity.candidate_sha), file=sys.stderr)
    prompt, entry = entry_for(args.mode, args.kind, copy.phase_id,
                              args.command)

    session_tmp = phase.pre("make_session_tmp",
                            harness_sandbox.make_session_tmp)

    phase.launch()
    started = time.monotonic()
    try:
        result = _drive(copy, snapshot, prompt, core, out, settings,
                        env=session_env, model=launch_model,
                        tmp_root=session_tmp)
    except harness_driver_sdk.DriverError as exc:
        print("fixharness: driver: %s" % exc, file=sys.stderr)
        return 2
    execution_seconds = time.monotonic() - started

    core.ledger.observe(harness_verdict.snapshot_obligations(state_path),
                        "final", head_sha(copy.root))
    _atomic_write(os.path.join(out, "obligations.json"),
                  core.ledger.to_json() + "\n")

    v = harness_verdict.verdict(copy, recipe, key, sentinels,
                                _transcript_events(out), pre_run_head,
                                denied_roots=(out,), ledger=core.ledger)
    reasons = list(v.reasons)
    for reason in [result.failed_reason] + core.fail_reasons:
        if reason and reason not in reasons:
            reasons.append(reason)
    if args.kind == "clean" and core.clean_tree_checkpoint is None:
        reasons.append(FAIL_CLEAN_TREE_NEVER)
    for reason in _model_problems(launch_model, result.model):
        if reason not in reasons:
            reasons.append(reason)
    record = harness_record.build_record(
        case_id=args.case, mode=args.mode, kind=args.kind, entry=entry,
        plugin_path=snapshot.path, plugin_source_path=PLUGIN_SOURCE_PATH,
        plugin_sha=snapshot.git_sha,
        plugin_snapshot_sha256=snapshot.tree_sha256,
        plugin_tree_dirty=snapshot.dirty, copy_root=copy.root,
        cli_version=result.cli_version, model=result.model,
        setting_sources=[], decisions=core.decisions(),
        execution_seconds=round(execution_seconds, 3),
        harness_answer_seconds=round(core.answer_seconds, 3),
        clean_tree_checkpoint=core.clean_tree_checkpoint,
        containment={
            "sandbox_enabled": settings["sandbox"]["enabled"],
            "fail_if_unavailable": settings["sandbox"]["failIfUnavailable"],
            "unsandboxed_retry":
                settings["sandbox"]["allowUnsandboxedCommands"],
            "probe_fingerprint": harness_sandbox.settings_fingerprint(
                settings),
            "denials": result.containment_denials,
            "protected_path_denials": result.protected_denials},
        obligations=obligation_counts(core.ledger, v.dispositions),
        verdict="FAILED" if reasons else "COMPLETE", reasons=reasons,
        transcript_sha256=result.transcript_sha256,
        manifest_id=identity.manifest_id, check_digest=identity.check_digest,
        candidate_sha=identity.candidate_sha)
    # waiting_on_owner_seconds is fixed to None by build_record (D-13).
    record.update({"pre_run_head": pre_run_head, "phase_id": copy.phase_id,
                   "state_path": str(state_path), "prompt": prompt,
                   "owner_commands_issued": result.owner_commands})
    harness_record.write_record(os.path.join(out, "run.json"), record)
    print(json.dumps({"verdict": record["verdict"], "reasons": reasons,
                      "run": os.path.join(out, "run.json")}, indent=2))
    return 0 if record["verdict"] == "COMPLETE" else 1


# --------------------------------------------------------------------------- #
# probe-sandbox
# --------------------------------------------------------------------------- #
def _sha256_file(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def _exists_then_remove(path):
    found = os.path.lexists(path)
    if found:
        os.unlink(path)
    return found


def probe_script_facts(script_path, expected_text, sha_before):
    """The probe.sh integrity facts gathered after the session."""
    return {"probe_script_expected_sha": hashlib.sha256(
                expected_text.encode("utf-8")).hexdigest(),
            "probe_script_sha_before": sha_before,
            "probe_script_sha_after": _sha256_file(script_path)}


def probe_sandbox(argv):
    parser = argparse.ArgumentParser(prog="fixharness.py probe-sandbox")
    parser.add_argument("--out", required=True)
    # A capability probe, not measurement evidence: any commit will do.
    parser.add_argument("--candidate", default=PROBE_DEFAULT_CANDIDATE)
    args = parser.parse_args(argv)
    try:
        out = _out_dir(args.out)
        candidate = _candidate(args.candidate)
        recipe = _check_case("py-clamp-01")
    except UsageError as exc:
        print("fixharness: %s" % exc, file=sys.stderr)
        return 2
    key = _load_key("py-clamp-01")
    os.makedirs(out, exist_ok=True)
    phase = Phase()
    nonce = secrets.token_hex(8)
    ws = phase.pre("make_workspace", harness_sandbox.make_workspace)
    snapshot = phase.pre("snapshot_plugin",
                         harness_sandbox.snapshot_plugin_from_commit,
                         harness_sandbox.CHECKOUT_ROOT, candidate, ws)
    copy = phase.pre("build_copy", harness_fixture.build_copy, recipe,
                     "default", ws)
    protected = os.path.join(out, "protected")
    paths = {"PROTECTED": protected, "KEYS_DIR": harness_sandbox.KEYS_DIR,
             "CHECKOUT": harness_sandbox.CHECKOUT_ROOT,
             "SNAPSHOT": snapshot.path, "NONCE": nonce}
    copy_canary = "HARNESS-COPY-" + nonce
    protected_canary = "HARNESS-PROTECTED-" + nonce
    edit_target = os.path.join(snapshot.path, "PROBE-EDIT-TARGET.txt")
    script_text = harness_sandbox.fill_probe_script(**paths)
    script_path = harness_sandbox.probe_script_path(copy.root)

    def fixture_writes():
        with open(os.path.join(copy.root, "PROBE.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(copy_canary + "\n")
        with open(script_path, "w", encoding="utf-8") as fh:
            fh.write(script_text)
        os.makedirs(protected, exist_ok=True)
        with open(os.path.join(protected, "canary.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(protected_canary + "\n")
        with open(edit_target, "w", encoding="utf-8") as fh:
            fh.write("HARNESS-EDIT-TARGET-" + nonce)
    phase.pre("probe_fixture_writes", fixture_writes)
    script_sha_before = _sha256_file(script_path)
    snapshot_sha_before = harness_sandbox.tree_sha256(snapshot.path)
    key_file = os.path.join(harness_sandbox.KEYS_DIR, "py-clamp-01.json")
    pre = {"protected_canary_exists": os.path.isfile(
               os.path.join(protected, "canary.txt")),
           "key_file_exists": os.path.isfile(key_file),
           "protected_dir_exists": os.path.isdir(protected),
           "edit_target_exists": _read_text(edit_target)
           == "HARNESS-EDIT-TARGET-" + nonce}
    settings = harness_sandbox.build_session_settings(copy.root,
                                                      snapshot.path, out)
    prompt = harness_sandbox.fill_probe_prompt(
        PROTECTED=protected, KEYS_DIR=harness_sandbox.KEYS_DIR,
        CHECKOUT=harness_sandbox.CHECKOUT_ROOT, NONCE=nonce,
        SNAPSHOT=snapshot.path, COPY=copy.root)

    session_tmp = phase.pre("make_session_tmp",
                            harness_sandbox.make_session_tmp)

    phase.launch()
    try:
        result = _drive(copy, snapshot, prompt, ProbeCore(), out, settings,
                        tmp_root=session_tmp)
    except harness_driver_sdk.DriverError as exc:
        print("fixharness: driver: %s" % exc, file=sys.stderr)
        return 2

    facts = dict(pre)
    facts.update({
        "copy_root": copy.root, "protected_canary": protected_canary,
        "copy_canary": copy_canary, "key_title": key.get("title"),
        "escape_file_exists": _exists_then_remove(os.path.join(
            harness_sandbox.CHECKOUT_ROOT, "HARNESS-ESCAPE-" + nonce)),
        "snapshot_escape_exists": _exists_then_remove(os.path.join(
            snapshot.path, "HARNESS-ESCAPE-" + nonce)),
        "protected_escape_exists": os.path.lexists(
            os.path.join(protected, "escape.txt")),
        "snapshot_sha_before": snapshot_sha_before,
        "snapshot_sha_after": harness_sandbox.tree_sha256(snapshot.path),
        "copy_marker_exists": os.path.isfile(
            os.path.join(copy.root, "escape-ok.txt")),
        "copy_tool_marker_exists": os.path.isfile(
            os.path.join(copy.root, "tool-ok.txt")),
        "edit_target_intact": _read_text(edit_target)
        == "HARNESS-EDIT-TARGET-" + nonce,
        "expected_inputs": harness_sandbox.PROBE_TOOL_INPUTS(
            PROTECTED=protected, KEYS_DIR=harness_sandbox.KEYS_DIR,
            SNAPSHOT=snapshot.path, COPY=copy.root, NONCE=nonce)})
    facts.update(probe_script_facts(script_path, script_text,
                                    script_sha_before))
    with open(os.path.join(out, harness_driver_sdk.TRANSCRIPT_NAME), "r",
              encoding="utf-8") as fh:
        events = harness_sandbox.probe_events_from_transcript(
            fh.readlines(), copy.root)
    passed, checks = harness_sandbox.evaluate_probe(events, facts)
    record = {"passed": passed, "checks": checks,
              "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "sdk_version": sdk_version(), "cli_version": result.cli_version,
              "model": result.model,
              "settings_fingerprint": harness_sandbox.settings_fingerprint(
                  settings),
              "plugin_sha": snapshot.git_sha,
              # Context only: the probe proves the sandbox policy, so it is
              # bound to no freeze manifest.
              "candidate_sha": snapshot.git_sha,
              "host": {"platform": platform.platform(),
                       "sandbox_exec_present": os.access(
                           harness_sandbox.SEATBELT, os.X_OK)}}
    _atomic_write(os.path.join(out, "probe-result.json"),
                  json.dumps({"record": record, "workspace": ws,
                              "snapshot": snapshot.path, "copy": copy.root},
                             indent=2, sort_keys=True) + "\n")
    _print_probe_diagnostics(events, facts, checks)
    if passed:
        _atomic_write(PROBE_RECORD_PATH,
                      json.dumps(record, indent=2, sort_keys=True) + "\n")
        print("fixharness: sandbox probe PASSED -> %s" % PROBE_RECORD_PATH)
        return 0
    print("fixharness: sandbox probe FAILED (record not written)",
          file=sys.stderr)
    return 1


def _print_probe_diagnostics(events, facts, checks):
    for name in sorted(k for k, v in checks.items() if not v):
        print("FAILED CHECK: %s" % name, file=sys.stderr)
    expected = facts.get("expected_inputs") or {}
    for step in harness_sandbox.PROBE_STEPS:
        if step.channel == "bash":
            continue
        matches = [e for e in events if harness_sandbox._matches_step(
            e, step.name, expected, facts.get("copy_root"))]
        for e in matches:
            print("step %s: %s | %r" % (step.name,
                                        harness_sandbox.classify_result(e),
                                        (e.result_text or "")[:300]),
                  file=sys.stderr)
        if not matches:
            print("step %s: no matching tool call" % step.name,
                  file=sys.stderr)
    for e in events:
        if e.tool != "Bash" and not any(harness_sandbox._matches_step(
                e, name, expected, facts.get("copy_root"))
                for name in expected):
            print("unspecified tool call: %s %r" % (e.tool, e.input),
                  file=sys.stderr)
        elif e.tool == "Bash" and e.command != "bash ./probe.sh":
            print("unspecified Bash call: %r" % e.command, file=sys.stderr)


# --------------------------------------------------------------------------- #
# replay
# --------------------------------------------------------------------------- #
class _ReplayAllow:
    def __init__(self, updated_input=None, **_kw):
        self.behavior = "allow"
        self.updated_input = updated_input


class _ReplayDeny:
    def __init__(self, message="", interrupt=False, **_kw):
        self.behavior = "deny"
        self.message = message
        self.interrupt = interrupt


REPLAY_SDK = type("ReplaySdk", (), {"PermissionResultAllow": _ReplayAllow,
                                    "PermissionResultDeny": _ReplayDeny})


def replay_messages(session, messages):
    """Feed recorded messages through the driver's own dispatch: each item
    is {"card": input} | {"tool": name, "input": {...}} | {"turn_end": text}.
    Stops at the first failure, as a live run would."""
    for item in messages:
        if "card" in item:
            session._card(REPLAY_SDK, item["card"])
        elif "tool" in item:
            session._tool(REPLAY_SDK, item["tool"], item.get("input") or {})
        elif "turn_end" in item:
            action, payload = session.on_result(item["turn_end"])
            if action == "fail":
                session.fail(payload)
            elif action == "command":
                session.owner_commands += 1
        if session.failed_reason:
            break
    return session


def prepare_copy(case_id, mode, kind, out):
    """Workspace, snapshot, copy, seed and (preservation) sentinels — the
    pre-launch half of `run`, shared by replay and the tests."""
    recipe = _check_case(case_id)
    key = _load_key(case_id)
    ws = harness_sandbox.make_workspace()
    snapshot = harness_sandbox.snapshot_plugin_from_commit(
        harness_sandbox.CHECKOUT_ROOT, "HEAD", ws)
    copy = harness_fixture.build_copy(recipe, mode, ws)
    pre_run_head = head_sha(copy.root)
    state_path = harness_seed.seed_state(copy, key, mode)
    core = Core(copy, state_path, state_path, mode, kind)
    snap0 = harness_verdict.snapshot_obligations(state_path)
    core.ledger.observe(snap0, "seed", pre_run_head)
    core.ledger.mark_seeded(snap0["hashes"])
    sentinels = harness_sentinels.plant(copy, recipe) \
        if kind == "preservation" else None
    return ws, snapshot, copy, core, sentinels


def replay(argv):
    parser = argparse.ArgumentParser(prog="fixharness.py replay")
    parser.add_argument("--case", required=True)
    parser.add_argument("--mode", required=True, choices=harness_fixture.MODES)
    parser.add_argument("--kind", required=True, choices=KINDS)
    parser.add_argument("--messages", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        out = _out_dir(args.out)
        _check_case(args.case)
    except UsageError as exc:
        print("fixharness: %s" % exc, file=sys.stderr)
        return 2
    with open(args.messages, "r", encoding="utf-8") as fh:
        messages = [json.loads(line) for line in fh if line.strip()]
    os.makedirs(out, exist_ok=True)
    _ws, snapshot, copy, core, _s = prepare_copy(args.case, args.mode,
                                                 args.kind, out)
    session = harness_driver_sdk.Session(copy, snapshot, core, out)
    try:
        replay_messages(session, messages)
    finally:
        session.close()
    doc = {"verdict": "REPLAY", "failed_reason": session.failed_reason,
           "decisions": core.decisions(),
           "containment_denials": session.containment_denials,
           "protected_path_denials": session.protected_denials}
    _atomic_write(os.path.join(out, "replay.json"),
                  json.dumps(doc, indent=2, sort_keys=True) + "\n")
    print(json.dumps(doc, indent=2, sort_keys=True))
    return 1 if session.failed_reason else 0


# --------------------------------------------------------------------------- #
# check
# --------------------------------------------------------------------------- #
def check(argv):
    parser = argparse.ArgumentParser(prog="fixharness.py check")
    parser.add_argument("--run", required=True)
    args = parser.parse_args(argv)
    run_dir = os.path.realpath(args.run)
    try:
        with open(os.path.join(run_dir, "run.json"), "r",
                  encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError):
        print("fixharness: no readable run.json in %s" % run_dir,
              file=sys.stderr)
        return 2
    problems = harness_record.validate_record(record)
    copy_root = record.get("copy_root") if isinstance(record, dict) else None
    if not problems and isinstance(copy_root, str) and os.path.isdir(copy_root):
        recipe = harness_fixture.load_recipe(record["case_id"])
        key = _load_key(record["case_id"])
        copy = harness_fixture.CopyInfo(copy_root, None,
                                        record.get("pre_run_head"),
                                        record.get("phase_id"))
        sentinels = None
        spath = os.path.join(run_dir, "sentinels.json")
        if os.path.isfile(spath):
            with open(spath, "r", encoding="utf-8") as fh:
                sentinels = harness_sentinels.SentinelRecord.from_json(
                    fh.read())
        ledger = None
        lpath = os.path.join(run_dir, "obligations.json")
        if os.path.isfile(lpath):
            with open(lpath, "r", encoding="utf-8") as fh:
                ledger = harness_verdict.ObligationLedger.from_json(fh.read())
        v = harness_verdict.verdict(copy, recipe, key, sentinels,
                                    _transcript_events(run_dir),
                                    record.get("pre_run_head"),
                                    denied_roots=(run_dir,), ledger=ledger)
        problems += ["verdict: %s" % r for r in v.reasons]
    elif not problems:
        print("fixharness: copy %s no longer exists; record validated only"
              % copy_root)
    for p in problems:
        print("fixharness: %s" % p)
    return 1 if problems else 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
SUBCOMMANDS = {"run": run, "probe-sandbox": probe_sandbox, "replay": replay,
               "check": check}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: fixharness.py {%s} ..." % ",".join(SUBCOMMANDS),
              file=sys.stderr if not argv else sys.stdout)
        return 2 if not argv else 0
    fn = SUBCOMMANDS.get(argv[0])
    if fn is None:
        print("fixharness: unknown subcommand %r" % argv[0], file=sys.stderr)
        return 2
    return fn(argv[1:])


if __name__ == "__main__":
    sys.exit(main())
