"""Tests for holdout_autopilot — the owner's one-command run.

A fake `claude` binary stands in for every headless session: it is written
into <tmp>/fakebin, put FIRST on PATH, and reached only through the kit's own
launchers (bin/finder, bin/crosscheck[-rN]), exactly as the real CLI would
be. It records every invocation in calls.jsonl (argv, cwd, the config dir the
launcher exported, the sorted env key names, a timestamp) and reads its
behaviour from control.json, never from the environment. It keeps a session
registry in sessions.json: `--session-id <u>` registers u BEFORE it acts on
the prompt, `--resume <u>` with an unknown u answers "No conversation found",
so a crash after partial writes leaves the id resumable, as the real CLI does.

openssl is the reversible XOR shim from test_holdout_archive. Every folder is
a temp dir; residue and leak-scan roots are temp dirs too. No real claude
session ever runs and nothing here reads the owner's holdout.

Every lock is paired with a mutant (or synthetic violation) that patches the
guard out and shows the wrong outcome happens.
"""

import ast
import contextlib
import io
import functools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

import holdout_fixture  # noqa: E402
import holdout_kit  # noqa: E402
import holdout_manifest  # noqa: E402
import holdout_seal  # noqa: E402
import holdout_validate  # noqa: E402
import holdout_archive  # noqa: E402
import holdout_dryrun  # noqa: E402
from test_holdout_archive import make_shim  # noqa: E402
from test_holdout_dryrun import all_probes, setup_folder  # noqa: E402

import holdout_autopilot as ap  # noqa: E402

KitError = holdout_kit.KitError
AUTOPILOT_PY = os.path.join(TOOLS_DIR, "holdout_autopilot.py")
README = os.path.join(os.path.dirname(TOOLS_DIR), "README.md")
RESULT_MARK = "[fake-session-result]"

FAKE_CLAUDE_SRC = r'''#!@@EXE@@
"""Fake claude for the autopilot tests (auth status, --version, -p)."""
import json
import os
import re
import shutil
import sys
import time
import uuid

sys.path.insert(0, @@TOOLS@@)
HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "[fake-session-result]"


def _load(name, default):
    try:
        with open(os.path.join(HERE, name), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _save(name, obj):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


def _now():
    ns = time.time_ns()
    secs, frac = divmod(ns, 1000000000)
    return "%s.%06dZ" % (time.strftime("%Y-%m-%dT%H:%M:%S",
                                       time.gmtime(secs)), frac // 1000)


def _reply(sid, text, is_error=False, code=0):
    print("warning: a line before the JSON")
    print(json.dumps({"session_id": sid, "is_error": is_error,
                      "result": text + "\n" + MARK, "num_turns": 1,
                      "permission_denials": []}))
    sys.stdout.flush()
    sys.exit(code)


argv = sys.argv[1:]
cfg = os.environ.get("CLAUDE_CONFIG_DIR", "")
control = _load("control.json", {})
with open(os.path.join(HERE, "calls.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"argv": argv, "cwd": os.getcwd(),
                         "config_dir": cfg, "env": sorted(os.environ),
                         "at": _now()}) + "\n")

if "--version" in argv and "-p" not in argv:
    print("2.1.281 (fake)")
    sys.exit(0)

name = os.path.basename(cfg)
if argv[:3] == ["auth", "status", "--json"]:
    logged = control.get("logged_in", {}).get(name, True)
    print(json.dumps({"loggedIn": bool(logged),
                      "authMethod": "claude.ai" if logged else "none",
                      "configDirectory": cfg}))
    sys.exit(0 if logged else 1)

if "-p" not in argv:
    sys.exit(2)

prompt = argv[argv.index("-p") + 1]
H = os.path.dirname(cfg)
role = "finder" if name == "cfg-finder" else "xcheck"
gen = 1
m = re.match(r"^cfg-xcheck-r([0-9]+)$", name)
if m:
    gen = int(m.group(1))

sessions = _load("sessions.json", [])
if control.get("forget_sessions"):
    sessions = []
    control["forget_sessions"] = False
    _save("control.json", control)
    _save("sessions.json", sessions)
if "--session-id" in argv:
    sid = argv[argv.index("--session-id") + 1]
    if sid in sessions:
        _reply(sid, "Session ID already in use", True, 1)
    sessions.append(sid)
    _save("sessions.json", sessions)
elif "--resume" in argv:
    sid = argv[argv.index("--resume") + 1]
    if control.get("forget_on_resume"):
        sessions = []
        _save("sessions.json", sessions)
    if sid not in sessions:
        _reply(sid, "No conversation found with session ID: %s" % sid,
               True, 1)
    if control.get("resume_broken"):
        sid = str(uuid.uuid4())
else:
    sid = str(uuid.uuid4())

sleep_on = control.get("sleep_on")
if control.get("sleep_seconds") and (not sleep_on or sleep_on in prompt):
    time.sleep(control["sleep_seconds"])
if control.get("garbage"):
    print("this is not json")
    sys.exit(0)

import holdout_dryrun  # noqa: E402
import holdout_kit  # noqa: E402
import holdout_validate  # noqa: E402


def present_slots():
    return {holdout_validate.slot_of(H, c): c
            for c in holdout_kit.case_ids(H)}


def drop_slot(slot):
    cid = present_slots()[slot]
    for part in ("cases", "keys"):
        shutil.rmtree(os.path.join(H, "sealed", part, cid))


def recreate(only=None, limit=None):
    if not os.path.isdir(os.path.join(H, holdout_dryrun.REPOS_DIRNAME)):
        # The earlier turn died before it wrote anything: do it now.
        holdout_dryrun.populate(H, complete_crosscheck=False, mark_dry_run=False)
        return
    made = 0
    for slot in holdout_kit.SLOTS:
        if (only and slot not in only) or slot in present_slots():
            continue
        repo = os.path.join(H, holdout_dryrun.REPOS_DIRNAME,
                            holdout_dryrun.LAYOUT[slot][0])
        cid = holdout_dryrun._new_id(H)
        holdout_dryrun._write_case(H, repo, slot,
                                   holdout_dryrun._next_variant(repo, slot),
                                   cid)
        made += 1
        if limit is not None and made >= limit:
            os._exit(143)


def _keep_copy(xid, name, path):
    """What the judge wrote, kept outside the holdout so a test can prove
    the autopilot never rewrote it."""
    keep = os.path.join(HERE, "written")
    os.makedirs(keep, exist_ok=True)
    shutil.copyfile(path, os.path.join(keep, "%s-%s" % (xid, name)))


def ledgers():
    out = {}
    keys = os.path.join(H, "sealed", "keys")
    for cid in os.listdir(keys):
        path = os.path.join(keys, cid, "xcheck-ledger.json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                led = json.load(fh)
            if led.get("xid"):
                out[led["xid"]] = cid
    return out


def packets():
    return sorted(n for n in os.listdir(os.getcwd())
                  if re.match(r"^X-[0-9a-f]{8}$", n))


def write_blinds(limit=None):
    by_xid = ledgers()
    made = 0
    for xid in packets():
        blind = os.path.join(os.getcwd(), xid, "blind.json")
        if os.path.exists(blind) or xid not in by_xid:
            continue
        with open(os.path.join(H, "sealed", "keys", by_xid[xid],
                               "key.json"), encoding="utf-8") as fh:
            key = json.load(fh)
        data = holdout_dryrun._blind(key)
        if control.get("disagree_slot") == key["slot"]:
            same = (holdout_kit.CATCH_SLOTS
                    if key["slot"] in holdout_kit.CATCH_SLOTS
                    else holdout_kit.QUIET_SLOTS)
            data["type_guess"] = [s for s in same if s != key["slot"]][0]
        with open(blind, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        _keep_copy(xid, "blind.json", blind)
        made += 1
        if limit is not None and made >= limit:
            os._exit(143)


def write_finals():
    for xid in packets():
        packet = os.path.join(os.getcwd(), xid)
        final = os.path.join(packet, "final.json")
        if os.path.isdir(os.path.join(packet, "revealed")) \
                and not os.path.exists(final):
            data = holdout_dryrun._final(packet)
            with open(os.path.join(packet, "revealed", "key.json"),
                      encoding="utf-8") as fh:
                slot = json.load(fh)["slot"]
            if control.get("no_rerun_slot") == slot:
                data.update(proof_agrees=False, proof_rerun_exit=None)
            with open(final, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            _keep_copy(xid, "final.json", final)


text = "ok"
if "sandbox-probe.py" in prompt:
    total = control.get("probe_total") or 8 + 3 * (gen - 1)
    if control.get("probe_fail"):
        text = ("PROBLEM: sandbox did not deny 1 of %d protected reads."
                % total)
    else:
        text = "OK: sandbox denied %d/%d protected reads" % (total, total)
elif "reply only with its first heading" in prompt:
    text = {"bad": "nothing to see",
            "no-read": "The Read was refused.\nfinder-write-ok",
            "no-write": "# Finder brief\nOperation not permitted"}.get(
        "bad" if control.get("finder_check_bad")
        else control.get("finder_check_half"),
        "# Finder brief\nfinder-write-ok")
elif prompt.startswith("Reply with the single word ready"):
    text = "ready"
elif role == "finder" and prompt.startswith("Read ../kit/FINDER-BRIEF.md "
                                            "and begin"):
    holdout_dryrun.populate(H, complete_crosscheck=False, mark_dry_run=False)
    if control.get("finder_short"):
        drop_slot("Q3")
    if control.get("finder_crash_after") == "begin":
        os._exit(143)
    if control.get("finder_partial"):
        for slot in holdout_kit.SLOTS[control["finder_partial"]:]:
            drop_slot(slot)
        os._exit(143)
    text = "the finder is done"
elif role == "finder" and "were withdrawn and retired" in prompt:
    slots = re.search(r"Slots ([A-Z0-9,]+) were", prompt).group(1)
    recreate(only=slots.split(","),
             limit=control.get("finder_crash_after_replace_slots"))
    text = "replaced"
elif role == "finder" and ("previous turn was interrupted" in prompt
                           or "previous session was lost" in prompt):
    if control.get("finder_crash_on_resume"):
        os._exit(143)
    recreate()
    text = "finished"
elif role == "finder" and "validate reported" in prompt:
    if not control.get("never_fix"):
        recreate()
    text = "fixed"
elif role == "xcheck" and ("CROSSCHECK-BRIEF.md and begin" in prompt
                           or "Write blind.json" in prompt):
    write_blinds(limit=control.get("xcheck_crash_after_blind"))
    text = "blind verdicts written"
elif role == "xcheck" and ("revealed. Continue" in prompt
                           or "Write final.json" in prompt):
    crash = control.get("xcheck_crash_on_continue")
    if crash == "before":
        os._exit(143)
    write_finals()
    if crash == "after":
        os._exit(143)
    text = "final verdicts written"
_reply(sid, text)
'''


# ================================================================ helpers


def make_fake_claude(directory):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "claude")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(FAKE_CLAUDE_SRC.replace("@@EXE@@", sys.executable)
                 .replace("@@TOOLS@@", repr(TOOLS_DIR)))
    os.chmod(path, 0o700)
    return directory


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)


def tree_hashes(folder, cids):
    """sha256 of every file under sealed/cases/<ID> and sealed/keys/<ID>."""
    out = {}
    for cid in cids:
        for part in ("cases", "keys"):
            root = os.path.join(folder, "sealed", part, cid)
            for rel in holdout_kit.walk_regular(root):
                out[(part, cid, rel)] = holdout_kit.sha256_file(
                    os.path.join(root, rel))
    return out


def packet_files(folder):
    """{(XID, name): bytes} of every blind.json / final.json in every
    cross-check workspace."""
    out = {}
    for ws in os.listdir(folder):
        if not re.match(r"^xcheck(-r[0-9]+)?$", ws):
            continue
        for xid in os.listdir(os.path.join(folder, ws)):
            for name in ("blind.json", "final.json"):
                path = os.path.join(folder, ws, xid, name)
                if os.path.isfile(path):
                    with open(path, "rb") as fh:
                        out[(xid, name)] = fh.read()
    return out


def slot_ids(folder):
    return {holdout_validate.slot_of(folder, c): c
            for c in holdout_kit.case_ids(folder)}


class AutopilotCase(unittest.TestCase):
    """A freshly set-up holdout, the fake claude first on PATH, the openssl
    shim, and temp residue and scan roots."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = os.path.realpath(self._tmp.name)
        self.fakebin = make_fake_claude(os.path.join(self.tmp, "fakebin"))
        self.F = setup_folder(self.tmp)
        self.R = holdout_fixture.make_source_repo(self.tmp, "tuning-repo")
        self.shim = make_shim(os.path.join(self.tmp, "shim"))
        self.home = os.path.join(self.tmp, "home")
        self.ctmp = os.path.join(self.tmp, "ctmp")
        self.scan = os.path.join(self.tmp, "scan")
        for path in (self.home, self.ctmp, self.scan):
            os.makedirs(path)
        env = holdout_fixture.kit_env()
        env["PATH"] = self.fakebin + os.pathsep + env.get("PATH", "")
        for name in ap.STRIPPED_ENV:
            env.pop(name, None)
        self.bases = {"home": self.home, "tmp": self.ctmp}
        for patcher in (
                mock.patch.dict(os.environ, env, clear=True),
                mock.patch.object(holdout_archive, "OPENSSL_BIN", self.shim),
                mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS",
                                  0.0),
                mock.patch.object(holdout_archive, "_default_residue_bases",
                                  return_value=self.bases),
                mock.patch.object(holdout_archive, "default_scan_roots",
                                  return_value=[self.scan]),
                mock.patch("os.isatty", return_value=True)):
            patcher.start()
            self.addCleanup(patcher.stop)

    # ------------------------------------------------------------ fake

    def control(self, **kw):
        dump(os.path.join(self.fakebin, "control.json"), kw)

    def calls(self):
        path = os.path.join(self.fakebin, "calls.jsonl")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def p_calls(self, calls=None):
        return [c for c in (self.calls() if calls is None else calls)
                if "-p" in c["argv"]]

    @staticmethod
    def prompt(call):
        return call["argv"][call["argv"].index("-p") + 1]

    @staticmethod
    def flag(call, name):
        argv = call["argv"]
        return argv[argv.index(name) + 1] if name in argv else None

    @staticmethod
    def cfg(call):
        return os.path.basename(call["config_dir"])

    # ------------------------------------------------------------ runs

    def capture(self, fn, *args, **kwargs):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = fn(*args, **kwargs)
        return result, out.getvalue(), err.getvalue()

    def cli(self, *extra, repo=True):
        argv = ["--folder", self.F, "autopilot"]
        if repo:
            argv += ["--repo", self.R]
        return self.capture(holdout_kit.run, argv + list(extra))

    def journal(self):
        return load(os.path.join(self.F, ap.JOURNAL_RELPATH))

    @staticmethod
    def last_line(out):
        lines = [line for line in out.splitlines() if line.strip()]
        return lines[-1] if lines else ""


# ================================================================ refusal


class TestRefusal(AutopilotCase):

    def test_refuses_in_claude_spawned_shell(self):
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1"}):
            rc, out, err = self.cli()
        self.assertEqual(rc, 1)
        self.assertEqual(err, holdout_kit.REFUSE_MSG + "\n")
        self.assertEqual(out, "")
        self.assertEqual(self.calls(), [])
        self.assertFalse(os.path.exists(os.path.join(
            self.fakebin, "calls.jsonl")))

    def test_refuses_even_from_an_isolated_session(self):
        # Stricter than the per-folder rule: a finder session (config dir
        # inside the folder) must never start the orchestrator either.
        env = {"CLAUDECODE": "1",
               "CLAUDE_CONFIG_DIR": os.path.join(self.F, "cfg-finder")}
        with mock.patch.dict(os.environ, env):
            rc, _, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 1)
        self.assertEqual(err, holdout_kit.REFUSE_MSG + "\n")
        self.assertEqual(self.calls(), [])


# ================================================================ shape


def _imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module)
    return names


def _call_name(node):
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


class TestModuleShape(unittest.TestCase):

    def setUp(self):
        with open(AUTOPILOT_PY, encoding="utf-8") as fh:
            self.text = fh.read()
        self.tree = ast.parse(self.text)

    def test_registration(self):
        self.assertEqual(holdout_kit.COMMANDS["autopilot"],
                         "holdout_autopilot")
        self.assertNotIn("autopilot", holdout_kit.NO_FOLDER_COMMANDS)
        self.assertNotIn("autopilot", holdout_kit.NO_REFUSAL_COMMANDS)

    def test_import_set(self):
        self.assertEqual(_imports(self.tree),
                         {"contextlib", "json", "os", "re", "shutil", "sys",
                          "time", "uuid", "holdout_kit", "holdout_validate",
                          "holdout_manifest", "holdout_seal",
                          "holdout_archive", "holdout_dryrun"})

    def test_forbidden_text_absent(self):
        for bad in ("vibe-check-holdout", "subprocess", "--bare",
                    "--dangerously-skip-permissions",
                    "--no-session-persistence", "bypassPermissions",
                    "holdout_fixture", "CLAUDE_CODE_OAUTH_TOKEN=",
                    "scrubbed"):
            self.assertNotIn(bad, self.text, bad)

    def test_synthetic_violation_is_detected(self):
        # The text lock is real: a module that spelled a forbidden flag out
        # would be caught by the same check.
        mutant = self.text + '\nEXTRA = ["--bare"]\n'
        self.assertIn("--bare", mutant)

    def test_print_args(self):
        args = ap.PRINT_ARGS
        for token in ("--permission-prompts", "none", "--permission-mode",
                      "dontAsk", "--output-format", "json", "--max-turns",
                      "--max-budget-usd", "--settings", "--allowedTools"):
            self.assertIn(token, args, token)
        settings = json.loads(args[args.index("--settings") + 1])
        self.assertIs(settings["sandbox"]["allowUnsandboxedCommands"], False)
        self.assertEqual(args[args.index("--permission-mode") + 1],
                         "dontAsk")
        for bad in ap.FORBIDDEN_ARGS:
            if bad != "--permission-mode":
                self.assertNotIn(bad, args)
        for name in ("bare", "safe-mode", "restricted",
                     "no-session-persistence", "bg"):
            self.assertIn("--" + name, ap.FORBIDDEN_ARGS)
        self.assertIn("bypass" + "Permissions", ap.FORBIDDEN_ARGS)
        self.assertIn("--dangerously-skip-" + "permissions",
                      ap.FORBIDDEN_ARGS)

    def test_argv_self_check(self):
        good = ["/x/bin/finder", "-p", "hi", *ap.PRINT_ARGS,
                "--session-id", "u"]
        ap.check_argv(good)
        for extra in (["--bare"], ["--no-session-" + "persistence"],
                      ["--permission-mode", "bypass" + "Permissions"]):
            with self.assertRaises(KitError):
                ap.check_argv(good + extra)
        # The prompt itself is never mistaken for a flag.
        ap.check_argv(["/x/bin/finder", "-p", "--bare", *ap.PRINT_ARGS,
                       "--resume", "u"])

    def test_every_run_session_call_names_its_session(self):
        found = 0
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and _call_name(node) in \
                    ("run_session", "_launch"):
                found += 1
                kws = {k.arg for k in node.keywords}
                self.assertTrue({"session_id", "resume"} & kws,
                                "line %d" % node.lineno)
        self.assertGreater(found, 3)

    def test_constants(self):
        self.assertEqual(sorted(ap.STRIPPED_ENV), sorted((
            "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
            "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_PROFILE",
            "ANTHROPIC_FEDERATION_RULE_ID", "ANTHROPIC_ORGANIZATION_ID")))
        self.assertEqual(ap.expected_probe_total(1), 8)
        self.assertEqual(ap.expected_probe_total(3), 14)
        self.assertEqual(ap.JOURNAL_RELPATH, "AUTOPILOT.json")
        self.assertEqual(ap.LOG_RELDIR, "tmp/owner/autopilot")
        self.assertEqual(ap.MAX_FIX_ROUNDS, 3)
        self.assertEqual(ap.CLAUDE_BIN, "claude")

    def test_finder_check_prompt_is_the_readme_line(self):
        with open(README, encoding="utf-8") as fh:
            readme = fh.read()
        self.assertIn("`%s`" % ap.FINDER_CHECK_PROMPT, readme)
        self.assertIn("`%s`" % ap.PROBE_PROMPT, readme)


# ================================================================ preflight


class TestPreflight(AutopilotCase):

    def test_strips_credentials(self):
        planted = {name: "secret-%d" % i
                   for i, name in enumerate(ap.STRIPPED_ENV[:4])}
        os.environ.update(planted)
        self.capture(ap.preflight, self.F, "real")
        calls = self.calls()
        self.assertTrue(calls)
        for call in calls:
            for name in ap.STRIPPED_ENV:
                self.assertNotIn(name, call["env"])
        for name in ap.STRIPPED_ENV:
            self.assertNotIn(name, os.environ)

    def test_mutant_no_stripping_leaks_credentials(self):
        os.environ["ANTHROPIC_API_KEY"] = "secret"
        with mock.patch.object(ap, "STRIPPED_ENV", ()):
            self.capture(ap.preflight, self.F, "real")
        self.assertTrue(any("ANTHROPIC_API_KEY" in c["env"]
                            for c in self.calls()))

    def test_auth_missing_xcheck_stops_with_instruction(self):
        self.control(logged_in={"cfg-xcheck": False})
        rc, out, err = self.cli()
        self.assertEqual(rc, 1, err)
        self.assertEqual(out, (
            "PROBLEM: the cross-check session is not logged in. In a new "
            "Terminal window run %s/bin/crosscheck, type /login, finish the "
            "browser login, type /exit, then run bin/holdout autopilot "
            "again.\n" % self.F))
        self.assertEqual(self.p_calls(), [])
        self.assertTrue(any(c["argv"][:3] == ["auth", "status", "--json"]
                            for c in self.calls()))

    def test_auth_missing_finder_names_bin_finder(self):
        self.control(logged_in={"cfg-finder": False})
        rc, out, _ = self.cli()
        self.assertEqual(rc, 1)
        self.assertIn("the finder session is not logged in. In a new "
                      "Terminal window run %s/bin/finder, type /login"
                      % self.F, out)
        self.assertEqual(self.p_calls(), [])

    def mint_generation_two(self):
        holdout_kit.make_xcheck_workspace(self.F, 2,
                                          prior=[holdout_kit.xcheck_names(1)])
        first = holdout_seal._new_generation(1)
        first["revealed_at"] = holdout_seal._now()
        holdout_seal._save_registry(self.F, {"generations": [
            first, holdout_seal._new_generation(2)]})

    def test_auth_missing_generation_two(self):
        self.mint_generation_two()
        self.control(logged_in={"cfg-xcheck-r2": False})
        rc, out, _ = self.cli()
        self.assertEqual(rc, 1)
        self.assertIn("run %s/bin/crosscheck-r2, type /login" % self.F, out)
        self.assertEqual(self.p_calls(), [])

    def test_mutant_skipped_auth_lets_a_session_run(self):
        self.control(logged_in={"cfg-xcheck": False})
        with mock.patch.object(ap, "_auth_problem", return_value=None):
            self.cli()
        self.assertTrue(self.p_calls())

    def test_auth_goes_through_the_launcher(self):
        seen = []
        real = holdout_kit.run_argv

        def spy(argv, *a, **kw):
            seen.append(list(argv))
            return real(argv, *a, **kw)

        with mock.patch.object(holdout_kit, "run_argv", side_effect=spy):
            self.capture(ap.preflight, self.F, "real")
        auth = [a for a in seen if a[1:4] == ["auth", "status", "--json"]]
        self.assertEqual(sorted(a[0] for a in auth),
                         [os.path.join(self.F, "bin", "crosscheck"),
                          os.path.join(self.F, "bin", "finder")])
        dirs = sorted(c["config_dir"] for c in self.calls()
                      if c["argv"][:3] == ["auth", "status", "--json"])
        self.assertEqual(dirs, [os.path.join(self.F, "cfg-finder"),
                                os.path.join(self.F, "cfg-xcheck")])
        self.assertNotIn("CLAUDE_CONFIG_DIR", os.environ)

    def assert_precondition(self, needle):
        with self.assertRaises(ap.Precondition) as cm:
            self.capture(ap.preflight, self.F, "real")
        msg = str(cm.exception)
        self.assertIn(needle, msg)
        self.assertNotIn("sealed/", msg)
        self.assertEqual(self.p_calls(), [])
        return msg

    def test_requires_a_tty(self):
        with mock.patch("os.isatty", return_value=False):
            self.assert_precondition("plain Terminal window")
        self.assertEqual(self.calls(), [])

    def test_requires_claude_on_path(self):
        os.environ["PATH"] = "/usr/bin:/bin"
        self.assert_precondition("claude is not installed")

    def test_requires_each_tool(self):
        seen = set()
        for const in ("OPENSSL_BIN", "TAR_BIN", "LSOF_BIN", "PGREP_BIN"):
            with mock.patch.object(holdout_archive, const,
                                   os.path.join(self.tmp, "no-such-tool")):
                seen.add(self.assert_precondition("is missing"))
        self.assertEqual(len(seen), 4)

    def test_requires_clean_settings(self):
        with mock.patch.object(holdout_kit, "finder_settings_problems",
                               return_value=["x"]):
            a = self.assert_precondition("finder settings")
        with mock.patch.object(holdout_kit, "xcheck_settings_problems",
                               return_value=["x"]):
            b = self.assert_precondition("cross-check settings")
        self.assertNotEqual(a, b)

    def test_requires_the_role_env(self):
        # A folder whose launchers predate CLAUDE_ENV_FILE (or whose
        # bin/role-env.sh is gone) stops before any session, naming
        # refresh-kit.
        env = os.path.join(self.F, "bin", "role-env.sh")
        os.remove(env)
        self.assertIn("refresh-kit", self.assert_precondition(
            "bin/role-env.sh predate"))
        holdout_kit._write_text(env, holdout_kit.ROLE_ENV_TEXT, 0o600)
        finder = os.path.join(self.F, "bin", "finder")
        with open(finder, encoding="utf-8") as fh:
            good = fh.read()
        with open(finder, "w", encoding="utf-8") as fh:
            fh.write(good.replace(holdout_kit.ROLE_ENV_LINE + "\n", ""))
        self.assert_precondition("bin/role-env.sh predate")
        self.assertEqual(self.p_calls(), [])
        with mock.patch.object(holdout_kit, "role_env_problems",
                               return_value=[]):
            self.capture(ap.preflight, self.F, "real")

    def post_encrypt_folder(self, archive=True, match=True):
        folder = os.path.join(self.tmp, "post")
        for rel in ("bin", "kit", "archive"):
            os.makedirs(os.path.join(folder, rel))
        with open(os.path.join(folder, "bin", "holdout"), "w") as fh:
            fh.write("#!/bin/sh\n")
        holdout_kit.write_json_atomic(
            os.path.join(folder, "kit", holdout_kit.KIT_INVENTORY),
            {"schema": holdout_kit.KIT_INVENTORY_SCHEMA, "files": {}})
        with open(os.path.join(folder, ".metadata_never_index"), "w"):
            pass
        path = os.path.join(folder,
                            *holdout_archive.ARCHIVE_RELPATH.split("/"))
        with open(path, "wb") as fh:
            fh.write(b"dummy archive")
        sha = holdout_kit.sha256_file(path)
        if not archive:
            os.remove(path)
        holdout_kit.write_json_atomic(
            os.path.join(folder, "SEAL.json"),
            {"archive_sha256": sha if match else "0" * 64})
        return folder

    def test_phase_post_encrypt_launches_nothing(self):
        folder = self.post_encrypt_folder()
        self.assertEqual(ap._phase(folder), "post-encrypt")
        _, out, _ = self.capture(ap.preflight, folder, "real")
        self.assertEqual(self.calls(), [])
        self.assertNotIn("setup", out)

    def test_phase_full_without_verified_archive(self):
        for kw in ({"archive": False}, {"match": False}):
            folder = self.post_encrypt_folder(**kw)
            self.assertEqual(ap._phase(folder), "full")
            with self.assertRaises(ap.Precondition) as cm:
                self.capture(ap.preflight, folder, "real")
            self.assertIn("run setup first", str(cm.exception))
            shutil.rmtree(folder)

    def test_mutant_phase_always_full_refuses_recovery(self):
        folder = self.post_encrypt_folder()
        with mock.patch.object(ap, "_phase", return_value="full"):
            with self.assertRaises(ap.Precondition) as cm:
                self.capture(ap.preflight, folder, "real")
        self.assertIn("run setup first", str(cm.exception))

    def test_replacement_is_always_full_phase(self):
        folder = self.post_encrypt_folder()
        self.assertEqual(ap._phase(folder, replace_retired=True), "full")
        j = ap.journal_load(folder)
        j["replace"]["pending"] = [{"id": "H-00000000", "slot": "C1"}]
        self.assertEqual(ap._phase(folder, j), "full")

    def test_probe_ok_passes(self):
        _, out, _ = self.capture(ap.preflight, self.F, "real")
        self.assertIn("step preflight: sandbox probe ok (8/8)", out)
        self.assertIs(self.journal()["xcheck"]["1"]["probe_ok"], True)
        self.assertNotIn(RESULT_MARK, out)

    def test_probe_failure_stops_sandbox(self):
        for control in ({"probe_fail": True}, {"probe_total": 5}):
            self.control(**control)
            with self.assertRaises(ap.Stop) as cm:
                self.capture(ap.preflight, self.F, "dry-run")
            self.assertEqual(cm.exception.kind, "sandbox")
            self.assertEqual(cm.exception.instruction,
                             ap.STOP_INSTRUCTIONS["sandbox"])

    def test_probe_failure_ends_blocked_sandbox(self):
        self.control(probe_fail=True)
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked sandbox")
        self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS["sandbox"])
        self.assertFalse(any(self.prompt(c) == ap.FINDER_BEGIN_PROMPT
                             for c in self.p_calls()))

    def test_mutant_probe_count_from_reply_passes_a_short_probe(self):
        self.control(probe_total=5)
        with mock.patch.object(ap, "expected_probe_total", return_value=5):
            self.capture(ap.preflight, self.F, "dry-run")
        self.assertIs(self.journal()["xcheck"]["1"]["probe_ok"], True)

    def test_finder_check_failure_stops_sandbox(self):
        self.control(finder_check_bad=True)
        with self.assertRaises(ap.Stop) as cm:
            self.capture(ap.preflight, self.F, "real")
        self.assertEqual(cm.exception.kind, "sandbox")
        checks = [c for c in self.p_calls()
                  if self.prompt(c) == ap.FINDER_CHECK_PROMPT]
        self.assertEqual(len(checks), 1)
        self.assertEqual(self.flag(checks[0], "--session-id"),
                         self.journal()["preflight"]["check_session_id"])

    def finder_check_stop(self, **control):
        self.control(**control)
        with self.assertRaises(ap.Stop) as cm:
            self.capture(ap.preflight, self.F, "real")
        self.assertEqual(cm.exception.kind, "sandbox")
        self.assertEqual(cm.exception.line, "blocked sandbox")
        self.assertIs(self.journal()["finder"]["check_ok"], False)
        text = cm.exception.instruction
        self.assertIn("README section 6 step 3", text)
        self.assertNotIn(self.F, text)
        return text

    def test_finder_check_both_halves_failed(self):
        text = self.finder_check_stop(finder_check_bad=True)
        self.assertEqual(text, ap.STOP_INSTRUCTIONS["finder-check"])
        self.assertIn("could neither read the kit nor write sealed/", text)

    def test_finder_check_read_half_failed(self):
        text = self.finder_check_stop(finder_check_half="no-read")
        self.assertEqual(text, ap.STOP_INSTRUCTIONS["finder-check-read"])
        self.assertIn("could not read the kit", text)
        self.assertNotIn("could not write", text)

    def test_finder_check_write_half_failed(self):
        text = self.finder_check_stop(finder_check_half="no-write")
        self.assertEqual(text, ap.STOP_INSTRUCTIONS["finder-check-write"])
        self.assertIn("could not write sealed/", text)
        self.assertNotIn("could not read", text)

    def test_finder_check_stops_cover_every_failure(self):
        self.assertEqual(set(ap.FINDER_CHECK_STOPS),
                         {(False, False), (False, True), (True, False)})
        keys = list(ap.FINDER_CHECK_STOPS.values())
        self.assertEqual(len(set(ap.STOP_INSTRUCTIONS[k] for k in keys)), 3)

    def test_requires_finder_user_settings(self):
        os.remove(os.path.join(self.F, "cfg-finder", "settings.json"))
        with self.assertRaises(ap.Precondition) as cm:
            self.capture(ap.preflight, self.F, "real")
        self.assertIn("finder settings", str(cm.exception))
        self.assertEqual(self.p_calls(), [])

    def test_order_of_preflight_sessions(self):
        self.capture(ap.preflight, self.F, "real")
        prompts = [self.prompt(c) for c in self.p_calls()]
        self.assertEqual(prompts, [ap.PROBE_PROMPT, ap.RESUME_CHECK_PROMPT_1,
                                   ap.RESUME_CHECK_PROMPT_2,
                                   ap.FINDER_CHECK_PROMPT])
        first_p = self.calls().index(self.p_calls()[0])
        auth = [i for i, c in enumerate(self.calls())
                if c["argv"][:3] == ["auth", "status", "--json"]]
        self.assertEqual(len(auth), 2)
        self.assertLess(max(auth), first_p)

    def test_real_mode_skips_recorded_checks(self):
        self.capture(ap.preflight, self.F, "real")
        n = len(self.p_calls())
        self.capture(ap.preflight, self.F, "real")
        self.assertEqual(len(self.p_calls()), n)


# ================================================================ sessions


class TestRunSession(AutopilotCase):

    def test_needs_exactly_one_identity(self):
        for kw in ({}, {"session_id": "a", "resume": "b"}):
            with self.assertRaises(KitError) as cm:
                ap.run_session(self.F, "finder", "hello", **kw)
            self.assertEqual(str(cm.exception), ap.RUN_SESSION_ARGS_MSG)
        self.assertEqual(self.calls(), [])

    def test_fresh_finder_argv(self):
        u = ap.new_session_id()
        res, out, _ = self.capture(ap.run_session, self.F, "finder", "hello",
                                   session_id=u)
        call = self.p_calls()[0]
        self.assertEqual(call["argv"], ["-p", "hello", *ap.PRINT_ARGS,
                                        "--session-id", u])
        self.assertEqual(call["config_dir"],
                         os.path.join(self.F, "cfg-finder"))
        self.assertEqual(call["cwd"], os.path.join(self.F, "work"))
        self.assertFalse(res.is_error)
        self.assertEqual(res.session_id, u)
        self.assertEqual(res.exit_code, 0)
        self.assertIn(RESULT_MARK, res.text)
        self.assertNotIn(RESULT_MARK, out)
        self.assertTrue(res.log_path.startswith(
            os.path.join(self.F, "tmp", "owner", "autopilot") + os.sep))
        with open(res.log_path, encoding="utf-8") as fh:
            self.assertIn('"session_id": "%s"' % u, fh.read())
        self.assertEqual(os.stat(res.log_path).st_mode & 0o777, 0o600)

    def test_xcheck_generation_launcher_and_resume(self):
        holdout_kit.make_xcheck_workspace(self.F, 2,
                                          prior=[holdout_kit.xcheck_names(1)])
        u = ap.new_session_id()
        self.capture(ap.run_session, self.F, "xcheck", "hello", gen=2,
                     session_id=u)
        res, _, _ = self.capture(ap.run_session, self.F, "xcheck", "again",
                                 gen=2, resume=u)
        first, second = self.p_calls()
        self.assertEqual(self.cfg(first), "cfg-xcheck-r2")
        self.assertEqual(self.flag(second, "--resume"), u)
        self.assertNotIn("--session-id", second["argv"])
        self.assertFalse(res.is_error)

    def test_garbage_and_error_are_failures(self):
        self.control(garbage=True)
        res, out, _ = self.capture(ap.run_session, self.F, "finder", "hi",
                                   session_id=ap.new_session_id())
        self.assertTrue(res.is_error)
        self.assertEqual(out, "session finder: failed (see the log inside "
                              "the holdout folder)\n")
        self.control()
        res, out, _ = self.capture(ap.run_session, self.F, "finder", "hi",
                                   resume=ap.new_session_id())
        self.assertTrue(res.is_error)
        self.assertTrue(res.not_found)
        self.assertNotIn("No conversation", out)
        self.assertNotIn(RESULT_MARK, out)

    def test_different_session_id_is_an_error(self):
        u = ap.new_session_id()
        self.capture(ap.run_session, self.F, "finder", "hi", session_id=u)
        self.control(resume_broken=True)
        res, out, _ = self.capture(ap.run_session, self.F, "finder", "more",
                                   resume=u)
        self.assertTrue(res.is_error)
        self.assertEqual(out, "session finder: answered under a different "
                              "session id (see the log inside the holdout "
                              "folder)\n")
        self.assertNotIn(u, out)

    def test_mutant_no_id_check_accepts_a_foreign_session(self):
        u = ap.new_session_id()
        self.capture(ap.run_session, self.F, "finder", "hi", session_id=u)
        self.control(resume_broken=True)
        with mock.patch.object(ap, "_ids_match", return_value=True):
            res, _, _ = self.capture(ap.run_session, self.F, "finder",
                                     "more", resume=u)
        self.assertFalse(res.is_error)

    def test_timeout_is_a_resumable_failure(self):
        self.control(sleep_seconds=3)
        u = ap.new_session_id()
        res, out, _ = self.capture(ap.run_session, self.F, "finder", "hi",
                                   session_id=u, timeout=0.3)
        self.assertTrue(res.is_error)
        self.assertTrue(res.timed_out)
        self.assertIsNone(res.exit_code)
        self.assertEqual(res.session_id, u)
        self.assertEqual(res.text, "")
        self.assertRegex(out, r"^session finder: timed out after \d+ s "
                              r"\(see the log inside the holdout folder\)\n$")
        self.assertNotIn("hi", out)

    def test_missing_launcher_is_not_swallowed(self):
        os.remove(os.path.join(self.F, "bin", "finder"))
        with self.assertRaises(KitError) as cm:
            self.capture(ap.run_session, self.F, "finder", "hi",
                         session_id=ap.new_session_id())
        self.assertIn("could not run", str(cm.exception))


class TestResumeCheck(AutopilotCase):

    def test_round_trip(self):
        j = ap.journal_load(self.F)
        _, out, _ = self.capture(ap.resume_check, self.F, j)
        u = self.journal()["preflight"]["resume_session_id"]
        uuid.UUID(u, version=4)
        first, second = self.p_calls()
        self.assertEqual(self.prompt(first), ap.RESUME_CHECK_PROMPT_1)
        self.assertEqual(self.flag(first, "--session-id"), u)
        self.assertEqual(self.prompt(second), ap.RESUME_CHECK_PROMPT_2)
        self.assertEqual(self.flag(second, "--resume"), u)
        self.assertIs(self.journal()["preflight"]["resume_ok"], True)
        self.assertIn("step preflight: resume by session id ok", out)

    def test_broken_or_forgetting_resume_stops(self):
        for control in ({"resume_broken": True}, {"forget_on_resume": True}):
            self.control(**control)
            with self.assertRaises(ap.Stop) as cm:
                self.capture(ap.resume_check, self.F,
                             ap.journal_load(self.F))
            self.assertEqual(cm.exception.kind, "other")
            self.assertEqual(cm.exception.instruction,
                             ap.STOP_INSTRUCTIONS["resume-unverified"])

    def test_unverified_resume_ends_blocked_other(self):
        self.control(forget_on_resume=True)
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        self.assertEqual(self.last_line(out), "blocked other")
        prompts = [self.prompt(c) for c in self.p_calls()]
        self.assertNotIn(ap.FINDER_BEGIN_PROMPT, prompts)
        self.assertNotIn(ap.XCHECK_BEGIN_PROMPT, prompts)

    def test_mutant_skipped_resume_call_passes_a_forgetting_cli(self):
        self.control(forget_on_resume=True)
        real = ap.run_session

        def skip_resume(folder, role, prompt, **kw):
            if kw.get("resume"):
                return ap.SessionResult(kw["resume"], "ready", False, 0,
                                        None)
            return real(folder, role, prompt, **kw)

        with mock.patch.object(ap, "run_session", side_effect=skip_resume):
            self.capture(ap.resume_check, self.F, ap.journal_load(self.F))
        self.assertIs(self.journal()["preflight"]["resume_ok"], True)

    def test_dry_run_always_rechecks(self):
        self.capture(ap.preflight, self.F, "dry-run")
        n = len(self.p_calls())
        self.capture(ap.preflight, self.F, "dry-run")
        self.assertEqual(len(self.p_calls()), 2 * n)


# ================================================================ journal


class TestJournal(AutopilotCase):

    def test_fresh_journal(self):
        j = ap.journal_load(self.F)
        self.assertEqual(j["schema"], ap.JOURNAL_SCHEMA)
        self.assertEqual(j["schema"], "vibe-check-holdout-autopilot/1")
        self.assertIsNone(j["finder"]["session_id"])
        self.assertEqual(j["finder"]["lost_session_ids"], [])
        self.assertEqual(j["finder"]["restarts"], 0)
        self.assertEqual(j["xcheck"], {})
        self.assertIsNone(j["preflight"]["resume_session_id"])
        self.assertIs(j["preflight"]["resume_ok"], False)
        self.assertEqual(j["replace"], {"pending": [], "removed": [],
                                        "seal_cleared": False,
                                        "prompt_sent": False})
        self.assertFalse(os.path.exists(ap.journal_path(self.F)))

    def test_round_trip_and_atomic(self):
        j = ap.journal_load(self.F)
        ap.mark(j, "finder", "pending", session_id="x")
        with mock.patch.object(holdout_kit, "write_json_atomic",
                               wraps=holdout_kit.write_json_atomic) as spy:
            ap.journal_save(self.F, j)
        spy.assert_called_once()
        again = ap.journal_load(self.F)
        self.assertEqual(again["steps"]["finder"]["status"], "pending")
        with self.assertRaises(KitError):
            ap.mark(j, "finder", "finished")

    def test_wrong_schema_or_symlink_refused(self):
        dump(ap.journal_path(self.F), {"schema": "other/1"})
        with self.assertRaises(KitError) as cm:
            ap.journal_load(self.F)
        self.assertEqual(str(cm.exception), ap.JOURNAL_BAD_MSG)
        os.remove(ap.journal_path(self.F))
        target = os.path.join(self.tmp, "elsewhere.json")
        dump(target, ap.journal_load(self.F))
        os.symlink(target, ap.journal_path(self.F))
        with self.assertRaises(KitError):
            ap.journal_load(self.F)

    def test_journal_stays_opaque_after_preflight(self):
        self.capture(ap.preflight, self.F, "real")
        with open(ap.journal_path(self.F), encoding="utf-8") as fh:
            text = fh.read()
        self.assertNotIn("sealed/", text)
        self.assertNotIn("sandbox denied", text)
        self.assertNotIn(RESULT_MARK, text)
        self.assertNotIn(self.F, text)

    def test_new_session_ids(self):
        a, b = ap.new_session_id(), ap.new_session_id()
        uuid.UUID(a, version=4)
        self.assertEqual(str(uuid.UUID(a, version=4)), a)
        self.assertNotEqual(a, b)


class TestRegistration(AutopilotCase):

    def test_journal_is_excluded_and_survives(self):
        self.assertEqual(holdout_archive.ARCHIVE_EXCLUDES[-1],
                         "AUTOPILOT.json")
        self.assertEqual(holdout_archive.SCRUB_FIXED_SURVIVORS[-1],
                         "AUTOPILOT.json")
        self.assertNotIn("AUTOPILOT.json", holdout_archive.REQUIRED_SURVIVORS)
        ap.journal_save(self.F, ap.journal_load(self.F))
        self.assertNotIn("AUTOPILOT.json",
                         holdout_archive.archive_members(self.F))
        self.assertIn("AUTOPILOT.json",
                      holdout_archive.survivor_allowlist(self.F))


# ================================================================ pipeline

ALLOWED_LINE = re.compile(
    r"^(step [a-z-]+: .+|OK: .+|PROBLEM: .+|session [a-z0-9-]+: .+"
    r"|sealed( non-runnable=[0-6])?|replaced slots=[A-Z0-9,]+"
    r"( non-runnable=[0-6])?|dry run ok.*|blocked [a-z-]+)$")


class PipelineCase(AutopilotCase):
    """Helpers for full runs: probe capture before scrub, opacity checks,
    run boundaries in calls.jsonl."""

    def setUp(self):
        AutopilotCase.setUp(self)
        self.probes = set()
        self.registry_before_scrub = None
        self.hashes_before_scrub = {}
        self.packets_before_scrub = {}
        self.synthetic_before_scrub = None
        self.marker_before_scrub = None
        real_scrub = holdout_archive.scrub

        def capture_then_scrub(folder, *a, **kw):
            sealed = os.path.join(folder, "sealed")
            if os.path.isdir(sealed) and holdout_kit.walk_regular(sealed):
                self.probes |= all_probes(folder)
                reg = os.path.join(folder, *holdout_seal.WORKSPACES_RELPATH
                                   .split("/"))
                if os.path.exists(reg):
                    self.registry_before_scrub = load(reg)
                self.hashes_before_scrub = tree_hashes(
                    folder, holdout_kit.case_ids(folder))
                self.packets_before_scrub = packet_files(folder)
                syn = os.path.join(folder, holdout_kit.SYNTHETIC_AGREEMENT)
                self.synthetic_before_scrub = (load(syn) if os.path.exists(
                    syn) else None)
                self.marker_before_scrub = holdout_kit.dry_run_marker_ok(
                    folder)
            return real_scrub(folder, *a, **kw)

        patcher = mock.patch.object(holdout_archive, "scrub",
                                    side_effect=capture_then_scrub)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_trees_kept(self, before):
        """Every file hashed in `before` was byte-identical when the last
        scrub began."""
        self.assertTrue(before)
        for key, sha in before.items():
            self.assertEqual(self.hashes_before_scrub.get(key), sha, key)

    def mark_calls(self):
        return len(self.calls())

    def since(self, n):
        return self.calls()[n:]

    def assert_opaque(self, *texts):
        probes = set(self.probes)
        sealed = os.path.join(self.F, "sealed")
        if os.path.isdir(sealed) and holdout_kit.walk_regular(sealed):
            probes |= all_probes(self.F)
        for text in texts:
            self.assertNotIn(RESULT_MARK, text)
            for probe in probes:
                self.assertNotIn(probe, text)
            for rel in ("sealed", "work", "xcheck"):
                self.assertNotIn(os.path.join(self.F, rel) + os.sep, text)
        if os.path.exists(ap.journal_path(self.F)):
            with open(ap.journal_path(self.F), encoding="utf-8") as fh:
                jtext = fh.read()
            self.assertNotIn(RESULT_MARK, jtext)
            self.assertNotIn("sealed/", jtext)
            for probe in probes:
                self.assertNotIn(probe, jtext)

    def published(self):
        return os.path.join(self.R, *holdout_manifest.SEAL_RELPATH.split("/"))

    def run_ok(self, *extra):
        rc, out, err = self.cli(*extra)
        self.assertEqual(rc, 0, out + err)
        return out

    def ids_in(self, cfgname, flag, calls=None):
        return [self.flag(c, flag) for c in self.p_calls(calls)
                if self.cfg(c) == cfgname and flag in c["argv"]]

    def plant_leak(self, slots):
        """A wrapper around leakscan that, on its first call, writes one
        probe of each named slot into the tuning repo's tree."""
        real = holdout_archive.leakscan
        planted = os.path.join(self.R, "notes", "pasted.txt")
        state = {"done": False}

        def plant_then_scan(folder, *a, **kw):
            if not state["done"]:
                state["done"] = True
                by_slot = {}
                for probe, slot, _ in holdout_archive._probes(folder):
                    by_slot.setdefault(slot, probe)
                os.makedirs(os.path.dirname(planted), exist_ok=True)
                with open(planted, "w", encoding="utf-8") as fh:
                    for slot in slots:
                        fh.write(by_slot[slot] + "\n")
            return real(folder, *a, **kw)

        return mock.patch.object(holdout_archive, "leakscan",
                                 side_effect=plant_then_scan), planted


class TestHappyPath(PipelineCase):

    def test_sealed_end_to_end(self):
        enc_at = {}
        real_encrypt = holdout_archive.encrypt

        def spy_encrypt(folder, *a, **kw):
            enc_at["n"] = len(self.p_calls())
            return real_encrypt(folder, *a, **kw)

        with mock.patch.object(holdout_archive, "encrypt",
                               side_effect=spy_encrypt):
            rc, out, err = self.cli()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), "sealed")
        self.assertEqual(holdout_manifest.resume_reply_kind("sealed"),
                         "sealed")
        with open(self.published(), "rb") as a, \
                open(os.path.join(self.F, "SEAL.json"), "rb") as b:
            self.assertEqual(a.read(), b.read())
        self.assertFalse(os.path.exists(os.path.join(self.F, "sealed")))
        self.assertTrue(os.path.isfile(holdout_archive.archive_path(self.F)))
        self.assertFalse(os.path.exists(os.path.join(
            self.F, *ap.LOG_RELDIR.split("/"))))
        j = self.journal()
        self.assertEqual(j["result_line"], "sealed")
        for step in ap.STEPS[:-1]:
            self.assertEqual(j["steps"][step]["status"], "done", step)

        calls = self.calls()
        pcalls = self.p_calls()
        first_p = calls.index(pcalls[0])
        auth = {self.cfg(c) for c in calls[:first_p]
                if c["argv"][:3] == ["auth", "status", "--json"]}
        self.assertEqual(auth, {"cfg-finder", "cfg-xcheck"})
        prompts = [self.prompt(c) for c in pcalls]
        self.assertLess(prompts.index(ap.PROBE_PROMPT),
                        prompts.index(ap.XCHECK_BEGIN_PROMPT))
        self.assertLess(prompts.index(ap.RESUME_CHECK_PROMPT_2),
                        prompts.index(ap.FINDER_CHECK_PROMPT))
        self.assertLess(prompts.index(ap.FINDER_CHECK_PROMPT),
                        prompts.index(ap.FINDER_BEGIN_PROMPT))
        conts = [c for c in pcalls
                 if self.prompt(c) == ap.XCHECK_CONTINUE_PROMPT]
        self.assertEqual(len(conts), 1)
        revealed_at = self.registry_before_scrub["generations"][0][
            "revealed_at"]
        self.assertGreater(conts[0]["at"], revealed_at)
        self.assertEqual(len(pcalls), enc_at["n"])
        ids = ap._journaled_ids(j)
        seen = {}
        for c in pcalls:
            fresh, resumed = (self.flag(c, "--session-id"),
                              self.flag(c, "--resume"))
            self.assertEqual((fresh is None) + (resumed is None), 1)
            if fresh:
                self.assertIn(fresh, ids)
                seen.setdefault(self.cfg(c), set()).add(fresh)
            else:
                self.assertIn(resumed, seen.get(self.cfg(c), set()))
        for line in out.splitlines():
            self.assertRegex(line, ALLOWED_LINE)
        self.assertTrue(self.probes)
        self.assert_opaque(out, err)
        with open(self.published(), encoding="utf-8") as fh:
            self.assert_opaque(fh.read())

    def test_mutant_printing_session_text_breaks_opacity(self):
        real = ap.run_session

        def leaky(*a, **kw):
            res = real(*a, **kw)
            print(res.text)
            return res

        with mock.patch.object(ap, "run_session", side_effect=leaky):
            _, out, _ = self.cli()
        self.assertIn(RESULT_MARK, out)


class TestSessionTimeout(PipelineCase):

    def test_timeout_is_a_resumable_stop(self):
        self.control(sleep_seconds=3, sleep_on=ap.FINDER_BEGIN_PROMPT)
        rc, out, _ = self.cli("--session-timeout", "1")
        self.assertEqual(rc, 3)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked other")
        self.assertIn("session finder: timed out after 1 s (see the log "
                      "inside the holdout folder)", lines)
        j = self.journal()
        self.assertEqual(j["steps"]["finder"]["status"], "pending")
        sid = j["finder"]["session_id"]
        self.assertIsNotNone(sid)
        self.assertIsNotNone(j["finder"]["started_at"])
        begin = [c for c in self.p_calls()
                 if self.prompt(c) == ap.FINDER_BEGIN_PROMPT]
        self.assertEqual(self.flag(begin[0], "--session-id"), sid)

        # A timeout on the --resume keeps the same id again.
        self.control(sleep_seconds=3, sleep_on="previous turn was")
        n = self.mark_calls()
        rc, out, _ = self.cli("--session-timeout", "1")
        self.assertEqual(rc, 3)
        self.assertEqual(self.journal()["finder"]["session_id"], sid)
        self.assertEqual(self.ids_in("cfg-finder", "--resume", self.since(n)),
                         [sid])

        self.control()
        n = self.mark_calls()
        out = self.run_ok()
        self.assertEqual(self.last_line(out), "sealed")
        run2 = self.since(n)
        finder = [c for c in self.p_calls(run2) if self.cfg(c) == "cfg-finder"]
        self.assertEqual(self.prompt(finder[0]), ap.FINDER_RESUME_PROMPT)
        self.assertEqual(self.flag(finder[0], "--resume"), sid)
        self.assertEqual(self.ids_in("cfg-finder", "--session-id", run2), [])
        self.assertNotIn(ap.FINDER_BEGIN_PROMPT,
                         [self.prompt(c) for c in self.p_calls(run2)])
        self.assert_opaque(out)

    def test_mutant_uncaught_timeout_breaks_the_grammar(self):
        self.control(sleep_seconds=3, sleep_on=ap.FINDER_BEGIN_PROMPT)
        with mock.patch.object(ap, "_is_timeout", return_value=False):
            rc, out, err = self.cli("--session-timeout", "1")
        self.assertEqual(rc, 1)
        self.assertIsNone(holdout_manifest.resume_reply_kind(
            self.last_line(out)))
        self.assertIn("could not run", err)


class TestValidateLoop(PipelineCase):

    def test_fix_round_then_sealed(self):
        self.control(finder_short=True)
        out = self.run_ok()
        self.assertEqual(self.last_line(out), "sealed")
        fixes = [c for c in self.p_calls()
                 if self.prompt(c).startswith(ap.FINDER_FIX_PROMPT)]
        self.assertTrue(1 <= len(fixes) <= ap.MAX_FIX_ROUNDS)
        sid = self.journal()["finder"]["session_id"]
        for c in fixes:
            self.assertEqual(self.flag(c, "--resume"), sid)
        self.assertIn("step validate: PROBLEM", out)
        self.assert_opaque(out)

    def test_never_fixed_stops_blocked_validation(self):
        self.control(finder_short=True, never_fix=True)
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked validation")
        self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS["validation"].replace(
            "<H>", self.F) % ap.MAX_FIX_ROUNDS)
        self.assertEqual(self.journal()["steps"]["validate"]["status"],
                         "blocked")
        fixes = [c for c in self.p_calls()
                 if self.prompt(c).startswith(ap.FINDER_FIX_PROMPT)]
        self.assertEqual(len(fixes), ap.MAX_FIX_ROUNDS)
        self.assertNotIn(ap.XCHECK_BEGIN_PROMPT,
                         [self.prompt(c) for c in self.p_calls()])
        self.assert_opaque(out)

    def test_mutant_zero_fix_rounds(self):
        self.control(finder_short=True)
        with mock.patch.object(ap, "MAX_FIX_ROUNDS", 0):
            _, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "blocked validation")


class TestDisagreement(PipelineCase):

    def test_disagreement_stops_and_is_never_resolved(self):
        self.control(disagree_slot="C3")
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        cid = slot_ids(self.F)["C3"]
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked disagreement")
        self.assertEqual(lines[-2], ap._render(
            ap.STOP_INSTRUCTIONS["disagreement"] % (cid, "C3", "C3"),
            os.path.realpath(self.F)))
        self.assertIn("bin/holdout diagnose --slot C3", lines[-2])
        self.assertNotIn("retire --slot", lines[-2])
        led = load(os.path.join(self.F, "sealed", "keys", cid,
                                "xcheck-ledger.json"))
        self.assertEqual(led["rounds"], [])
        self.assertFalse(os.path.exists(os.path.join(
            self.F, "sealed", "keys", cid, "resolution.md")))
        self.assertFalse(os.path.exists(os.path.join(self.F, "SEAL.json")))
        self.assertFalse(os.path.exists(holdout_archive.archive_path(self.F)))
        begins = [c for c in self.p_calls()
                  if self.prompt(c) == ap.XCHECK_BEGIN_PROMPT]
        self.assertEqual(len(begins), 1)
        self.assertEqual(len(load(os.path.join(
            self.F, *holdout_seal.WORKSPACES_RELPATH.split("/")))
            ["generations"]), 1)
        self.assert_opaque(out)

    def test_mutant_no_blockers_seals_a_disagreement(self):
        self.control(disagree_slot="C3")
        with mock.patch.object(holdout_seal, "seal_blockers",
                               return_value=[]):
            _, out, _ = self.cli()
        self.assertNotEqual(self.last_line(out), "blocked disagreement")
        self.assertTrue(os.path.exists(os.path.join(self.F, "SEAL.json")))


class TestRejudge(PipelineCase):
    """--rejudge SLOT re-judges, in a fresh generation, ONLY a round whose
    judge agreed on substance but recorded no proof re-run exits."""

    def stop_without_rerun(self):
        self.control(no_rerun_slot="C3")
        rc, out, _ = self.cli()
        self.assertEqual((rc, self.last_line(out)), (3, "blocked disagreement"))
        cid = slot_ids(self.F)["C3"]
        self.assertEqual(holdout_seal.diagnose(self.F, slot="C3"),
                         [("C3", "proof-mismatch",
                           ["judge-proof-false", "proof-rerun-missing"])])
        return cid

    def gens(self):
        """Distinct cross-check generations a judge session began in (the
        registry itself is gone once scrub has run)."""
        return len({self.cfg(c) for c in self.p_calls()
                    if self.prompt(c) == ap.XCHECK_BEGIN_PROMPT})

    def test_rejudge_finishes_in_a_fresh_generation(self):
        self.stop_without_rerun()
        self.control()
        rc, out, _ = self.cli("--rejudge", "C3")
        self.assertEqual(self.last_line(out), "sealed", out)
        self.assertEqual(rc, 0)
        self.assertEqual(self.gens(), 2)
        self.assertIn("step crosscheck: case C3 sent to a fresh generation "
                      "(re-judge)", out)
        self.assert_opaque(out)

    def test_rejudge_refuses_a_real_disagreement(self):
        self.control(disagree_slot="C3")
        self.cli()
        cid = slot_ids(self.F)["C3"]
        before = load(os.path.join(self.F, "sealed", "keys", cid,
                                   "xcheck-ledger.json"))
        self.control()
        rc, out, err = self.cli("--rejudge", "C3")
        self.assertNotEqual(rc, 0)
        self.assertIn(ap.REJUDGE_REFUSED_MSG % "C3", out + err)
        self.assertEqual(load(os.path.join(self.F, "sealed", "keys", cid,
                                           "xcheck-ledger.json")), before)
        self.assertEqual(self.gens(), 1)

    def test_rejudge_refuses_an_agreeing_slot(self):
        self.stop_without_rerun()
        self.control()
        rc, out, err = self.cli("--rejudge", "C1")
        self.assertNotEqual(rc, 0)
        self.assertIn(ap.REJUDGE_REFUSED_MSG % "C1", out + err)

    def test_mutant_rejudge_guard(self):
        self.control(disagree_slot="C3")
        self.cli()
        self.control()
        with mock.patch.object(ap, "rejudge_allowed", return_value=True):
            _, out, _ = self.cli("--rejudge", "C3")
        self.assertEqual(self.gens(), 2)


class TestFinderResume(PipelineCase):

    def crash_with_three_cases(self):
        self.control(finder_partial=3)
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        self.assertIn("session finder: failed (see the log inside the "
                      "holdout folder)", out)
        self.assertEqual(self.last_line(out), "blocked other")
        j = self.journal()
        sid = j["finder"]["session_id"]
        begin = [c for c in self.p_calls()
                 if self.prompt(c) == ap.FINDER_BEGIN_PROMPT]
        self.assertEqual(len(begin), 1)
        self.assertEqual(self.flag(begin[0], "--session-id"), sid)
        self.assertEqual(j["steps"]["finder"]["status"], "pending")
        survivors = holdout_kit.case_ids(self.F)
        self.assertEqual(len(survivors), 3)
        return sid, tree_hashes(self.F, survivors)

    def test_crash_after_partial_writes_resumes_same_session(self):
        sid, before = self.crash_with_three_cases()
        self.control()
        n = self.mark_calls()
        out = self.run_ok()
        self.assertEqual(self.last_line(out), "sealed")
        run2 = self.p_calls(self.since(n))
        prompts = [self.prompt(c) for c in run2]
        for once in (ap.PROBE_PROMPT, ap.FINDER_CHECK_PROMPT,
                     ap.RESUME_CHECK_PROMPT_1, ap.FINDER_BEGIN_PROMPT):
            self.assertNotIn(once, prompts)
        self.assertEqual([c for c in run2 if "--session-id" in c["argv"]],
                         [])
        resumed = [c for c in run2
                   if self.prompt(c) == ap.FINDER_RESUME_PROMPT]
        self.assertEqual(len(resumed), 1)
        self.assertEqual(self.flag(resumed[0], "--resume"), sid)
        self.assertIn("never re-screen a recorded candidate",
                      self.prompt(resumed[0]))
        self.assert_trees_kept(before)
        self.assert_opaque(out)

    def test_crash_again_on_resume_keeps_the_id(self):
        sid, before = self.crash_with_three_cases()
        self.control(finder_crash_on_resume=True)
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        self.assertEqual(self.last_line(out), "blocked other")
        self.assertEqual(self.journal()["finder"]["session_id"], sid)
        self.control()
        out = self.run_ok()
        self.assertEqual(self.last_line(out), "sealed")

    def test_mutant_fresh_call_without_id_cannot_resume(self):
        with mock.patch.object(ap, "_identity_args",
                               side_effect=lambda sid, resume:
                               [] if sid else ["--resume", resume]), \
                mock.patch.object(ap, "check_argv"):
            self.control(finder_partial=3)
            self.cli()
            self.control()
            _, out, _ = self.cli()
        self.assertNotEqual(self.last_line(out), "sealed")

    def kill_during_begin(self):
        real = ap.run_session

        def killed(folder, role, prompt, **kw):
            res = real(folder, role, prompt, **kw)
            if prompt == ap.FINDER_BEGIN_PROMPT:
                raise RuntimeError("synthetic kill of the autopilot")
            return res

        with mock.patch.object(ap, "run_session", side_effect=killed):
            with self.assertRaises(RuntimeError):
                self.cli()

    def test_uuid_is_on_disk_before_the_launch(self):
        self.kill_during_begin()
        sid = self.journal()["finder"]["session_id"]
        begin = [c for c in self.p_calls()
                 if self.prompt(c) == ap.FINDER_BEGIN_PROMPT]
        self.assertEqual(self.flag(begin[0], "--session-id"), sid)

    def test_mutant_late_journaling_loses_the_uuid(self):
        def no_save(folder, j, holder, key="session_id"):
            holder[key] = ap.new_session_id()
            return holder[key]

        with mock.patch.object(ap, "_allocate", side_effect=no_save), \
                mock.patch.object(ap, "_assert_journaled"):
            self.kill_during_begin()
        self.assertIsNone(self.journal()["finder"]["session_id"])


class TestLostSession(PipelineCase):

    def test_lost_session_never_restarts_silently(self):
        self.control(finder_partial=3)
        self.cli()
        sid = self.journal()["finder"]["session_id"]
        survivors = holdout_kit.case_ids(self.F)
        before = tree_hashes(self.F, survivors)
        for _ in range(2):
            self.control(forget_sessions=True)
            n = self.mark_calls()
            rc, out, _ = self.cli()
            self.assertEqual(rc, 3)
            lines = out.strip().splitlines()
            self.assertEqual(lines[-1], "blocked other")
            self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS[
                "resume-lost"].replace("<H>", self.F))
            run = self.p_calls(self.since(n))
            self.assertNotIn(ap.FINDER_BEGIN_PROMPT,
                             [self.prompt(c) for c in run])
            self.assertEqual([c for c in run if "--session-id" in c["argv"]],
                             [])
            self.assertEqual(self.journal()["finder"]["session_id"], sid)
            self.assertEqual(tree_hashes(self.F, survivors), before)

        self.control()
        n = self.mark_calls()
        out = self.run_ok("--restart-finder")
        self.assertEqual(self.last_line(out), "sealed")
        j = self.journal()
        self.assertEqual(j["finder"]["lost_session_ids"], [sid])
        self.assertEqual(j["finder"]["restarts"], 1)
        new = j["finder"]["session_id"]
        self.assertNotEqual(new, sid)
        run = self.p_calls(self.since(n))
        restart = [c for c in run if self.prompt(c) == ap.FINDER_RESTART_PROMPT]
        self.assertEqual(len(restart), 1)
        self.assertEqual(self.flag(restart[0], "--session-id"), new)
        self.assertNotIn(ap.FINDER_BEGIN_PROMPT,
                         [self.prompt(c) for c in run])
        self.assert_trees_kept(before)
        self.assert_opaque(out)

    def test_restart_without_a_lost_session_is_refused(self):
        n = self.mark_calls()
        rc, _, err = self.cli("--restart-finder")
        self.assertEqual(rc, 1)
        self.assertIn(ap.RESTART_MSG, err)
        self.assertEqual(self.p_calls(self.since(n)), [])

    def test_mutant_lost_branch_falling_through_begins_again(self):
        self.control(finder_partial=3)
        self.cli()
        self.control(forget_sessions=True)

        def fall_through(run):
            run.j["finder"]["session_id"] = None
            return ap._step_finder(run)

        n = self.mark_calls()
        with mock.patch.object(ap, "_lost_finder", side_effect=fall_through):
            self.cli()
        self.assertIn(ap.FINDER_BEGIN_PROMPT,
                      [self.prompt(c) for c in self.p_calls(self.since(n))])


class TestCrosscheckResume(PipelineCase):

    def test_crash_mid_blinds_resumes_same_generation_session(self):
        self.control(xcheck_crash_after_blind=3)
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        self.assertEqual(self.last_line(out), "blocked other")
        sid = self.journal()["xcheck"]["1"]["session_id"]
        self.assertEqual(self.ids_in("cfg-xcheck", "--session-id"), [sid])
        begin = [c for c in self.p_calls()
                 if self.prompt(c) == ap.XCHECK_BEGIN_PROMPT]
        self.assertEqual(self.flag(begin[0], "--resume"), sid)
        self.control()
        n = self.mark_calls()
        out = self.run_ok()
        self.assertEqual(self.last_line(out), "sealed")
        run2 = self.since(n)
        self.assertEqual(self.ids_in("cfg-xcheck", "--session-id", run2), [])
        self.assertIn(sid, self.ids_in("cfg-xcheck", "--resume", run2))
        self.assert_opaque(out)

    def crash_after_reveal(self):
        self.control(xcheck_crash_on_continue="before")
        rc, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "blocked other")
        reg = load(os.path.join(self.F,
                                *holdout_seal.WORKSPACES_RELPATH.split("/")))
        self.assertIsNotNone(reg["generations"][0]["revealed_at"])
        return reg["generations"][0]["cases"][0]

    def assert_burned_stop(self, first, n):
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked other")
        self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS["burned"].replace(
            "<H>", self.F) % (1, first))
        run = self.p_calls(self.since(n))
        xc = [c for c in run if self.cfg(c) == "cfg-xcheck"]
        for c in xc:
            self.assertNotEqual(self.prompt(c), ap.XCHECK_BEGIN_PROMPT)
            self.assertNotIn("--session-id", c["argv"])

    def test_burned_generation_without_session_id(self):
        first = self.crash_after_reveal()
        j = self.journal()
        del j["xcheck"]["1"]
        dump(ap.journal_path(self.F), j)
        self.control()
        self.assert_burned_stop(first, self.mark_calls())

    def test_burned_generation_whose_session_is_gone(self):
        first = self.crash_after_reveal()
        self.control(forget_sessions=True)
        self.assert_burned_stop(first, self.mark_calls())

    def test_mutant_ignoring_reveal_judges_in_a_burned_workspace(self):
        self.crash_after_reveal()
        j = self.journal()
        del j["xcheck"]["1"]
        dump(ap.journal_path(self.F), j)
        self.control()
        n = self.mark_calls()
        with mock.patch.object(ap, "_generation_revealed",
                               return_value=False):
            self.cli()
        fresh = self.ids_in("cfg-xcheck", "--session-id", self.since(n))
        self.assertTrue(fresh)


class TestEvidence(PipelineCase):

    def test_missing_journal_after_completion(self):
        self.run_ok()
        os.remove(ap.journal_path(self.F))
        n = self.mark_calls()
        with mock.patch.object(holdout_archive, "scrub",
                               wraps=holdout_archive.scrub) as spy:
            out = self.run_ok()
        self.assertEqual(spy.call_count, 1)
        self.assertEqual(self.last_line(out), "sealed")
        self.assertEqual(self.since(n), [])

    def test_missing_journal_cannot_prove_a_changed_repo_copy(self):
        self.run_ok()
        os.remove(ap.journal_path(self.F))
        with open(self.published(), "a", encoding="utf-8") as fh:
            fh.write(" ")
        rc, out, _ = self.cli()
        self.assertEqual(rc, 1)
        self.assertEqual(self.last_line(out),
                         ap.STOP_INSTRUCTIONS["journal-missing"])
        self.assertNotIn("\nsealed\n", "\n" + out)

    def test_missing_journal_with_retired_cases(self):
        self.run_ok()
        os.remove(ap.journal_path(self.F))
        holdout_kit.write_json_atomic(
            os.path.join(self.F, "RETIRED.json"),
            {"schema": holdout_manifest.RETIRED_SCHEMA, "retired": [
                {"at": "2026-01-01T00:00:00Z", "slot": "C1",
                 "reason": "owner",
                 "source": {"repo_name": None, "base_rev": None,
                            "feature_rev": None},
                 "diff_sha256": None, "lines_sha256": None,
                 "key_sha256": None}]})
        rc, out, _ = self.cli()
        self.assertEqual(rc, 1)
        self.assertEqual(self.last_line(out),
                         ap.STOP_INSTRUCTIONS["journal-missing"])

    def test_mutant_missing_journal_trusts_the_seal(self):
        self.run_ok()
        os.remove(ap.journal_path(self.F))
        with open(self.published(), "a", encoding="utf-8") as fh:
            fh.write(" ")
        with mock.patch.object(ap, "_proven_complete", return_value=True):
            _, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "sealed")

    def stop_at_leakscan(self):
        with mock.patch.object(holdout_archive, "leakscan",
                               side_effect=KitError("synthetic failure")):
            rc, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "blocked other")
        self.assertEqual(self.journal()["steps"]["encrypt"]["status"], "done")
        os.remove(holdout_archive.archive_path(self.F))

    def shim_count(self):
        log = os.path.join(os.path.dirname(self.shim), "argv.jsonl")
        with open(log, encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())

    def test_archive_evidence_beats_the_journal(self):
        self.stop_at_leakscan()
        before = self.shim_count()
        out = self.run_ok()
        self.assertEqual(self.last_line(out), "sealed")
        self.assertGreater(self.shim_count(), before)

    def test_mutant_journal_over_evidence_skips_encrypt(self):
        self.stop_at_leakscan()
        before = self.shim_count()
        with mock.patch.object(ap, "_encrypt_evidence",
                               side_effect=lambda run: ap._status(
                                   run.j, "encrypt") == "done"):
            _, out, _ = self.cli()
        self.assertNotEqual(self.last_line(out), "sealed")
        self.assertEqual(self.shim_count(), before)


class TestInputsChanged(PipelineCase):

    def touch_proof_after_finals(self):
        self.control(xcheck_crash_on_continue="after")
        _, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "blocked other")
        cid = slot_ids(self.F)["C1"]
        run = os.path.join(self.F, "sealed", "keys", cid, "proof", "run")
        with open(run, "a", encoding="utf-8") as fh:
            fh.write("# trailing comment added after the cross-check\n")
        time.sleep(1.1)
        holdout_dryrun.record_proof_results(self.F, cid)
        self.control()
        return cid

    def test_inputs_changed_is_a_mechanical_reset(self):
        cid = self.touch_proof_after_finals()
        n = self.mark_calls()
        out = self.run_ok()
        self.assertEqual(self.last_line(out), "sealed")
        run = self.p_calls(self.since(n))
        probes = [c for c in run if self.prompt(c) == ap.PROBE_PROMPT]
        self.assertEqual([self.cfg(c) for c in probes], ["cfg-xcheck-r2"])
        self.assertIn("step crosscheck: generation 2 probe ok (11/11)", out)
        gens = self.registry_before_scrub["generations"]
        self.assertEqual(len(gens), 2)
        self.assertIn(cid, gens[1]["cases"])
        self.assertEqual(self.journal()["input_resets"], {cid: 1})
        self.assert_opaque(out)

    def test_reset_cap(self):
        cid = self.touch_proof_after_finals()
        with mock.patch.object(ap, "MAX_INPUT_RESETS", 0):
            rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked other")
        self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS["inputs-reset"]
                         .replace("<H>", self.F) % cid)


class TestLeakAndReplace(PipelineCase):

    def test_leak_stops_then_replace_retired_continues(self):
        patcher, planted = self.plant_leak(["C2"])
        with patcher:
            rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked leakscan")
        self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS["leakscan"] % "C2")
        self.assertEqual(self.journal()["replaced_slots"], ["C2"])
        scans = load(os.path.join(self.F, "LEAKSCAN.json"))["scans"]
        self.assertGreater(scans[-1]["hits"], 0)
        retired = load(os.path.join(self.F, "RETIRED.json"))["retired"]
        self.assertEqual([e["slot"] for e in retired], ["C2"])
        self.assertFalse(os.path.exists(self.published()))
        old = slot_ids(self.F)["C2"]
        self.assert_opaque(out)

        os.remove(planted)
        rc, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "blocked leakscan")
        # The real run's leak path is unchanged by the dry-run rule: a clean
        # re-scan still names the slot, and nothing is ever waived.
        self.assertEqual(out.strip().splitlines()[-2],
                         ap.STOP_INSTRUCTIONS["leakscan"] % "C2")
        self.assertFalse(os.path.exists(
            os.path.join(self.F, holdout_kit.LEAK_WAIVER)))
        self.assertFalse(os.path.exists(self.published()))

        n = self.mark_calls()
        out = self.run_ok("--replace-retired")
        self.assertEqual(self.last_line(out), "replaced slots=C2")
        self.assertEqual(holdout_manifest.resume_reply_kind(
            self.last_line(out)), "replaced")
        run = self.p_calls(self.since(n))
        replace = [c for c in run if self.prompt(c) ==
                   ap.FINDER_REPLACE_PROMPT % "C2"]
        self.assertEqual(len(replace), 1)
        self.assertEqual(self.flag(replace[0], "--resume"),
                         self.journal()["finder"]["session_id"])
        self.assertNotIn(old, load(self.published())["cases"])
        self.assertIn("step crosscheck: generation 2 probe ok (11/11)", out)
        self.assert_opaque(out)

    def test_mutant_blind_leakscan_publishes(self):
        patcher, planted = self.plant_leak(["C2"])
        real = holdout_archive.leakscan
        empty = os.path.join(self.tmp, "empty-root")
        os.makedirs(empty)

        def blind_scan(folder, *a, **kw):
            kw.pop("repo", None)
            kw.pop("scan_roots", None)
            return real(folder, *a, scan_roots=[empty], **kw)

        with patcher, mock.patch.object(holdout_archive, "leakscan",
                                        side_effect=blind_scan):
            _, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "sealed")
        self.assertTrue(os.path.exists(self.published()))

    def test_mutant_ignored_hits_fall_to_publish(self):
        # With the leakscan step's two guards patched out (the hit list and
        # the still-sealed check) the run gets past leakscan; only publish's
        # own refusal is left, so the guards are what stop it at leakscan.
        patcher, _ = self.plant_leak(["C2"])
        with patcher, mock.patch.object(ap, "_leak_hits", return_value=[]), \
                mock.patch.object(ap, "_unreplaced_slots", return_value=[]):
            _, out, _ = self.cli()
        steps = self.journal()["steps"]
        self.assertEqual(steps["leakscan"]["status"], "done")
        self.assertEqual(steps["publish"]["status"], "blocked")
        self.assertEqual(self.last_line(out), "blocked leakscan")
        self.assertFalse(os.path.exists(self.published()))

    def test_mutant_kept_case_tree_never_replaces(self):
        patcher, planted = self.plant_leak(["C2"])
        with patcher:
            self.cli()
        os.remove(planted)
        with mock.patch.object(ap, "_remove_case_trees"):
            _, out, _ = self.cli("--replace-retired")
        self.assertNotEqual(self.last_line(out), "replaced slots=C2")

    def test_nothing_to_replace(self):
        rc, _, err = self.cli("--replace-retired")
        self.assertEqual(rc, 1)
        self.assertIn(ap.NOTHING_TO_REPLACE_MSG, err)


class TestReplacementInterrupted(PipelineCase):

    def leak_two(self):
        patcher, planted = self.plant_leak(["C2", "Q1"])
        with patcher:
            _, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "blocked leakscan")
        os.remove(planted)
        ids = slot_ids(self.F)
        keep = [ids[s] for s in ("C1", "C3", "Q2", "Q3")]
        return ids, keep, tree_hashes(self.F, keep)

    def crash_on_second_tree(self, ids):
        real = shutil.rmtree
        state = {"first": None}
        retired = {ids["C2"], ids["Q1"]}

        def rmtree_once(path, *a, **kw):
            cid = os.path.basename(os.path.normpath(path))
            if cid in retired:
                if state["first"] is None:
                    state["first"] = cid
                elif cid != state["first"]:
                    raise RuntimeError("synthetic crash")
            return real(path, *a, **kw)

        n = self.mark_calls()
        with mock.patch.object(shutil, "rmtree", side_effect=rmtree_once):
            with self.assertRaises(RuntimeError):
                self.cli("--replace-retired")
        return state["first"], n

    def test_two_crashes_then_replaced(self):
        ids, keep, before = self.leak_two()
        first, n = self.crash_on_second_tree(ids)
        j = self.journal()
        pending = j["replace"]["pending"]
        self.assertEqual(sorted((e["slot"], e["id"]) for e in pending),
                         [("C2", ids["C2"]), ("Q1", ids["Q1"])])
        self.assertEqual(j["replace"]["removed"], [first])
        self.assertIs(j["replace"]["seal_cleared"], False)
        other = ids["Q1"] if first == ids["C2"] else ids["C2"]
        self.assertIn(other, holdout_kit.case_ids(self.F))
        self.assertEqual(tree_hashes(self.F, keep), before)
        self.assertEqual(self.p_calls(self.since(n)), [])

        self.control(finder_crash_after_replace_slots=1)
        n = self.mark_calls()
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        self.assertEqual(self.last_line(out), "blocked other")
        prompts = [self.prompt(c) for c in self.p_calls(self.since(n))]
        self.assertIn(ap.FINDER_REPLACE_PROMPT % "C2,Q1", prompts)
        self.assertNotIn(other, holdout_kit.case_ids(self.F))
        self.assertFalse(os.path.exists(os.path.join(self.F, "SEAL.json")))
        self.assertIs(self.journal()["replace"]["seal_cleared"], True)
        sid = self.journal()["finder"]["session_id"]

        self.control()
        n = self.mark_calls()
        out = self.run_ok()
        self.assertEqual(self.last_line(out), "replaced slots=C2,Q1")
        self.assertEqual(holdout_manifest.resume_reply_kind(
            self.last_line(out)), "replaced")
        resumed = [c for c in self.p_calls(self.since(n))
                   if self.prompt(c) == ap.FINDER_RESUME_PROMPT]
        self.assertEqual([self.flag(c, "--resume") for c in resumed], [sid])
        self.assertEqual(self.journal()["replace"]["pending"], [])
        self.assert_trees_kept(before)
        self.assert_opaque(out)

    def test_mutant_slots_from_disk_lose_a_slot(self):
        ids, _, _ = self.leak_two()
        self.crash_on_second_tree(ids)

        def from_disk(run):
            return sorted(slot for _, slot in ap._retired_present(run.h))

        with mock.patch.object(ap, "_finder_replace_slots",
                               side_effect=from_disk):
            _, out, err = self.cli()
        self.assertNotEqual(self.last_line(out), "replaced slots=C2,Q1")

    def crash_on_first_tree(self, ids):
        real = shutil.rmtree
        retired = {ids["C2"], ids["Q1"]}

        def rmtree_never(path, *a, **kw):
            if os.path.basename(os.path.normpath(path)) in retired:
                raise RuntimeError("synthetic crash")
            return real(path, *a, **kw)

        with mock.patch.object(shutil, "rmtree", side_effect=rmtree_never):
            with self.assertRaises(RuntimeError):
                self.cli("--replace-retired")

    def test_intent_is_on_disk_before_the_first_delete(self):
        ids, _, _ = self.leak_two()
        self.crash_on_first_tree(ids)
        j = self.journal()
        self.assertEqual(sorted(e["slot"] for e in j["replace"]["pending"]),
                         ["C2", "Q1"])
        self.assertEqual(j["replace"]["removed"], [])

    def test_mutant_intent_after_first_delete(self):
        ids, _, _ = self.leak_two()
        real = ap._record_replace_intent

        def unsaved(run, present):
            with mock.patch.object(ap, "journal_save"):
                real(run, present)

        with mock.patch.object(ap, "_record_replace_intent",
                               side_effect=unsaved):
            self.crash_on_first_tree(ids)
        self.assertEqual(self.journal()["replace"]["pending"], [])

    def test_mutant_flag_required_on_rerun(self):
        ids, _, _ = self.leak_two()
        self.crash_on_second_tree(ids)
        with mock.patch.object(ap, "_replacement_active",
                               side_effect=lambda j, flag: bool(flag)):
            _, out, _ = self.cli()
        self.assertNotEqual(self.last_line(out), "replaced slots=C2,Q1")


class TestWriterBarrier(PipelineCase):

    def test_open_process_stops_close_sessions(self):
        holder = subprocess.Popen(["sleep", "30"],
                                  cwd=os.path.join(self.F, "xcheck"))
        try:
            rc, out, _ = self.cli()
            self.assertEqual(rc, 3)
            lines = out.strip().splitlines()
            self.assertEqual(lines[-1], "blocked other")
            self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS["writers"])
            self.assertTrue(lines[-3].startswith(
                "PROBLEM: holdout folder is still in use by 1 process(es): "
                "%d sleep" % holder.pid), lines[-3])
            self.assertEqual(self.journal()["steps"]["close-sessions"]
                             ["status"], "blocked")
            self.assertFalse(os.path.exists(
                holdout_archive.archive_path(self.F)))
        finally:
            holder.terminate()
            holder.wait()
        n = self.mark_calls()
        out = self.run_ok()
        self.assertEqual(self.last_line(out), "sealed")
        self.assertEqual(self.p_calls(self.since(n)), [])

    def test_mutant_no_writer_check_encrypts_under_a_holder(self):
        holder = subprocess.Popen(["sleep", "30"],
                                  cwd=os.path.join(self.F, "xcheck"))
        try:
            with mock.patch.object(holdout_archive, "require_no_writers"):
                _, out, _ = self.cli()
            self.assertTrue(os.path.exists(
                holdout_archive.archive_path(self.F)))
        finally:
            holder.terminate()
            holder.wait()


class TestDryRun(PipelineCase):

    def test_dry_run_ok(self):
        rc, out, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), "dry run ok prompted sandbox=ok")
        self.assertEqual(holdout_manifest.resume_reply_kind(
            self.last_line(out)), "dry-run-ok")
        probes = [(self.cfg(c)) for c in self.p_calls()
                  if self.prompt(c) == ap.PROBE_PROMPT]
        self.assertEqual(probes, ["cfg-xcheck", "cfg-xcheck-r2"])
        self.assertIn("step preflight: sandbox probe ok (8/8)", out)
        self.assertIn("step crosscheck: generation 2 probe ok (11/11)", out)
        prompts = [(self.cfg(c), self.prompt(c)) for c in self.p_calls()]
        self.assertIn(("cfg-xcheck-r2", ap.XCHECK_BEGIN_PROMPT), prompts)
        self.assertIn(("cfg-xcheck-r2", ap.XCHECK_CONTINUE_PROMPT), prompts)
        self.assertNotIn(ap.FINDER_BEGIN_PROMPT, [p for _, p in prompts])
        self.assertFalse(os.path.exists(os.path.join(self.F, "sealed")))
        self.assertEqual(self.journal()["mode"], "dry-run")
        for line in out.splitlines():
            self.assertRegex(line, ALLOWED_LINE)
        self.assert_opaque(out, err)

    def test_dry_run_never_publishes(self):
        rc, out, _ = self.cli("--dry-run")
        self.assertEqual(rc, 0)
        self.assertEqual(self.last_line(out), "dry run ok prompted sandbox=ok")
        self.assertFalse(os.path.exists(self.published()))
        self.assertNotIn("publish", ap.DRY_RUN_STEPS)
        tree = ast.parse(open(AUTOPILOT_PY, encoding="utf-8").read())
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in (
                    "dry_run", "_dry_handlers"):
                self.assertNotIn("publish", ast.unparse(node))

    def test_dry_run_probe_failure(self):
        self.control(probe_fail=True)
        rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 3)
        self.assertEqual(self.last_line(out), "blocked sandbox")

    def test_dry_run_openssl_failure_is_no_prompt(self):
        os.environ["FAKE_OPENSSL_FAIL"] = "1"
        rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 3)
        self.assertEqual(self.last_line(out), "dry run ok no-prompt")
        self.assertEqual(holdout_manifest.resume_reply_kind(
            self.last_line(out)), "dry-run-failed")


DRY_OK = "dry run ok prompted sandbox=ok"


class TestDryRunReplace(PipelineCase):
    """51-09 dry-run recovery: a retired dummy case is replaced with
    genuinely different dummy material and judged blind in a fresh
    generation; --replace-retired is honoured under --dry-run."""

    def login_marks(self):
        """A stand-in login file in every config dir that exists now; the
        fake claude never writes there, so any change is the autopilot's."""
        marks = {}
        for name in sorted(os.listdir(self.F)):
            if name.startswith("cfg-"):
                path = os.path.join(self.F, name, "fake-login")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("logged in: %s\n" % name)
                marks[path] = holdout_kit.sha256_file(path)
        return marks

    def disagree_then_retire(self):
        """Dry run -> the generation-2 judge disagrees on C1 (recorded, never
        a stop) -> openssl fails at encrypt, so the run stops with the dummy
        seal written -> the owner retires C1 by hand (reason owner)."""
        self.control(disagree_slot="C1")
        os.environ["FAKE_OPENSSL_FAIL"] = "1"
        try:
            rc, out, _ = self.cli("--dry-run", repo=False)
        finally:
            os.environ.pop("FAKE_OPENSSL_FAIL", None)
        self.assertEqual(rc, 3)
        self.assertEqual(self.last_line(out), "dry run ok no-prompt")
        self.assertIn("step crosscheck: real judge verdict recorded "
                      "(disagreed)", out)
        self.control()
        old = slot_ids(self.F)
        rc, _, err = self.capture(holdout_kit.run, [
            "--folder", self.F, "retire", "--slot", "C1", "--reason",
            "owner"])
        self.assertEqual(rc, 0, err)
        keep = [old[s] for s in holdout_kit.SLOTS if s != "C1"]
        return old, keep, tree_hashes(self.F, keep)

    def leak_stop(self, slot="Q2"):
        """Dry run -> leakscan finds one probe of `slot` planted in a scan
        root -> blocked leakscan (leakscan retired the case); the planted
        file is removed again."""
        real = holdout_archive.leakscan
        planted = os.path.join(self.scan, "pasted.txt")
        state = {"done": False}

        def plant_then_scan(folder, *a, **kw):
            if not state["done"]:
                state["done"] = True
                by_slot = {}
                for probe, s, _ in holdout_archive._probes(folder):
                    by_slot.setdefault(s, probe)
                with open(planted, "w", encoding="utf-8") as fh:
                    fh.write(by_slot[slot] + "\n")
            return real(folder, *a, **kw)

        with mock.patch.object(holdout_archive, "leakscan",
                               side_effect=plant_then_scan):
            rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 3)
        self.assertEqual(self.last_line(out), "blocked leakscan")
        os.remove(planted)
        return out

    def assert_differs_on_every_field(self, cid):
        fp = holdout_manifest.case_fingerprint(self.F, cid)
        retired = holdout_manifest.load_retired(self.F)["retired"]
        self.assertTrue(retired)
        for entry in retired:
            self.assertEqual(holdout_manifest._matched_fields(fp, entry), [])
            for k in ("base_rev", "feature_rev"):
                self.assertNotEqual(fp["source"][k], entry["source"][k])
            for k in ("diff_sha256", "lines_sha256", "key_sha256"):
                self.assertNotEqual(fp[k], entry[k], k)

    def test_plain_rerun_after_an_owner_retire_replaces_nothing(self):
        # Owner decision (51-09): no retirement or new generation just to
        # obtain agreement. A dummy case the owner already retired is kept
        # (its retirement is waived in the dry-run seal), nothing is judged
        # again and no new generation or login is needed.
        old, _, _ = self.disagree_then_retire()
        n = self.mark_calls()
        rc, out, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), DRY_OK)
        since = self.p_calls(self.since(n))
        self.assertNotIn(ap.XCHECK_BEGIN_PROMPT,
                         [self.prompt(c) for c in since])
        self.assertFalse([c for c in since
                          if self.cfg(c).startswith("cfg-xcheck-r3")])
        self.assertEqual([g["gen"] for g in
                          self.registry_before_scrub["generations"]], [1, 2])
        self.assertEqual(self.journal()["replace"]["pending"], [])
        seal = load(os.path.join(self.F, "SEAL.json"))
        self.assertEqual(seal["status"], "dry-run")
        self.assertIn(old["C1"], seal["cases"])

    def test_plain_rerun_after_a_leak_finishes_on_a_clean_rescan(self):
        # Owner-approved dry-run rule: the hit is recorded and the dummy
        # case retired; once the leaked copy is gone, plain --dry-run scans
        # afresh and, on a clean scan, finishes without replacement.
        out = self.leak_stop()
        self.assertIn(ap.STOP_INSTRUCTIONS["leakscan-dry"] % "Q2", out)
        self.assertIn("bin/holdout autopilot --dry-run: a fresh scan", out)
        old = slot_ids(self.F)
        before = tree_hashes(self.F, list(old.values()))
        reg = load(os.path.join(self.F, *holdout_seal.WORKSPACES_RELPATH
                                .split("/")))
        retired = load(os.path.join(self.F, "RETIRED.json"))["retired"]
        self.assertEqual([e["slot"] for e in retired], ["Q2"])
        n = self.mark_calls()
        rc, out, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), DRY_OK)
        self.assertIn("step leakscan: 0 match(es)", out)
        self.assertIn("step leakscan: clean; leak waived (dry-run) for dummy "
                      "slots Q2, kept without replacement", out)
        self.assertNotIn("recorded for this seal", out)
        # No replacement, no new generation, no session of any kind.
        self.assertEqual(self.p_calls(self.since(n)), [])
        self.assert_trees_kept(before)
        self.assertEqual(self.registry_before_scrub["generations"],
                         reg["generations"])
        # The hit and the retirement stay on record; the waiver keeps the
        # same dummy case, marked.
        scans = load(os.path.join(self.F, "LEAKSCAN.json"))["scans"]
        self.assertGreater(scans[0]["hits"], 0)
        self.assertEqual(scans[-1]["hits"], 0)
        self.assertEqual(load(os.path.join(self.F, "RETIRED.json"))["retired"],
                         retired)
        waiver = load(os.path.join(self.F, holdout_kit.LEAK_WAIVER))
        self.assertEqual(waiver["mode"], "dry-run")
        self.assertEqual(waiver["cases"], {old["Q2"]: {
            "slot": "Q2", "leak": "waived (dry-run)",
            "named_at": scans[0]["at"]}})
        seal = load(os.path.join(self.F, "SEAL.json"))
        self.assertEqual(holdout_manifest.leak_waiver_problems(self.F, seal),
                         [])
        # A second plain re-run finds the scan recorded for this seal.
        rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0)
        self.assertIn("step leakscan: skipped (recorded for this seal)", out)

    def test_rerun_with_the_leak_still_present_scans_again(self):
        # A recorded scan with hits never counts as "recorded for this
        # seal": the resume scans afresh, and a hit stops it again.
        self.leak_stop()
        seal = load(os.path.join(self.F, "SEAL.json"))
        by_slot = {}
        for probe, s_, _ in holdout_archive._probes(self.F):
            by_slot.setdefault(s_, probe)
        planted = os.path.join(self.scan, "still-there.txt")
        with open(planted, "w", encoding="utf-8") as fh:
            fh.write(by_slot["Q2"] + "\n")
        n_scans = len(load(os.path.join(self.F, "LEAKSCAN.json"))["scans"])
        rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 3)
        self.assertEqual(self.last_line(out), "blocked leakscan")
        self.assertIn(ap.STOP_INSTRUCTIONS["leakscan-dry"] % "Q2", out)
        self.assertEqual(len(load(os.path.join(self.F, "LEAKSCAN.json"))
                             ["scans"]), n_scans + 1)
        self.assertFalse(os.path.exists(
            os.path.join(self.F, holdout_kit.LEAK_WAIVER)))
        with self.assertRaises(KitError) as cm:
            holdout_manifest.write_leak_waiver(self.F, seal)
        self.assertEqual(str(cm.exception),
                         holdout_manifest.WAIVER_NOT_CLEAN_MSG)
        os.remove(planted)
        rc, out, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), DRY_OK)

    def test_mutant_recorded_hits_skip_the_rescan(self):
        # If a recorded scan with hits counted as "recorded for this seal",
        # the resume would skip the scan and finish the dry run on the hit:
        # no fresh scan, no clean result, nothing waived.
        self.leak_stop()
        with mock.patch.object(holdout_manifest, "leak_ledger_problems",
                               return_value=[]):
            rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0)
        self.assertIn("step leakscan: skipped (recorded for this seal)", out)
        self.assertFalse(os.path.exists(
            os.path.join(self.F, holdout_kit.LEAK_WAIVER)))
        scans = load(os.path.join(self.F, "LEAKSCAN.json"))["scans"]
        self.assertGreater(scans[-1]["hits"], 0)

    def waived_folder(self):
        """leak_stop, then a plain --dry-run that finishes on a clean
        re-scan (the folder is scrubbed; the seal, ledgers, markers and
        waiver survive). Returns the waived case's ID."""
        self.leak_stop()
        cid = slot_ids(self.F)["Q2"]
        rc, out, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertTrue(os.path.exists(
            os.path.join(self.F, holdout_kit.LEAK_WAIVER)))
        return cid

    def test_waiver_never_counts_outside_dry_run(self):
        cid = self.waived_folder()
        seal = load(os.path.join(self.F, "SEAL.json"))
        real_check = holdout_manifest.leak_ledger_problems
        self.assertEqual(real_check(self.F, seal, dry_run=True), [])
        problems = real_check(self.F, seal)
        self.assertEqual(len(problems), 1)
        self.assertIn("case Q2 (%s) was named by a leak scan" % cid,
                      problems[0])
        # Mutant: a real-mode check that honoured the waiver (dry_run
        # forced on) clears the gate, so the assertion above is what
        # catches a waiver accepted outside the dry run.
        mutant = functools.partial(real_check, dry_run=True)
        self.assertEqual(mutant(self.F, seal), [])
        self.assertNotEqual(mutant(self.F, seal), problems)
        # The waiver alone is a dry-run marker: with DRY-RUN.json and
        # SYNTHETIC-AGREEMENT.json gone and a public-shaped seal, real
        # publish and rehash still refuse.
        for name in (holdout_kit.DRYRUN_MARKER,
                     holdout_kit.SYNTHETIC_AGREEMENT):
            path = os.path.join(self.F, name)
            if os.path.exists(path):
                os.remove(path)
        path = os.path.join(self.F, "SEAL.json")
        dump(path, holdout_manifest._dry_seal_public_view(load(path)))
        self.assertEqual(holdout_kit.dry_run_markers_present(self.F),
                         [holdout_kit.LEAK_WAIVER])
        with self.assertRaises(KitError) as ctx:
            holdout_manifest.publish(self.F, self.R)
        self.assertIn(holdout_kit.DRY_RUN_REFUSED_MSG, str(ctx.exception))
        self.assertEqual(holdout_manifest.dry_run_problems(
            self.F, load(path)), [holdout_kit.DRY_RUN_REFUSED_MSG])
        self.assertFalse(os.path.exists(self.published()))
        # Outside a marked dry-run folder the waiver is never valid.
        self.assertEqual(holdout_manifest.leak_waiver_problems(
            self.F, load(path)), [holdout_manifest.WAIVER_NOT_DRY_MSG])
        with self.assertRaises(KitError) as ctx:
            holdout_manifest.write_leak_waiver(self.F, load(path))
        self.assertEqual(str(ctx.exception),
                         holdout_manifest.WAIVER_NOT_DRY_MSG)

    def test_mutant_waiver_dropped_from_the_markers_reaches_the_leak_gate(
            self):
        # One lock out (the waiver is no dry-run marker): publish gets past
        # the dry-run gate, and the real leak gate (which never reads the
        # waiver) still refuses the unreplaced case.
        self.waived_folder()
        for name in (holdout_kit.DRYRUN_MARKER,
                     holdout_kit.SYNTHETIC_AGREEMENT):
            path = os.path.join(self.F, name)
            if os.path.exists(path):
                os.remove(path)
        path = os.path.join(self.F, "SEAL.json")
        dump(path, holdout_manifest._dry_seal_public_view(load(path)))
        with mock.patch.object(holdout_kit, "DRY_RUN_MARKERS",
                               (holdout_kit.DRYRUN_MARKER,
                                holdout_kit.SYNTHETIC_AGREEMENT)):
            self.assertEqual(holdout_manifest.dry_run_problems(
                self.F, load(path)), [])
            self.assertTrue(holdout_manifest.leak_ledger_problems(
                self.F, load(path)))
        self.assertFalse(os.path.exists(self.published()))

    def test_waiver_without_a_clean_rescan_is_refused(self):
        self.leak_stop()
        seal = load(os.path.join(self.F, "SEAL.json"))
        cid = slot_ids(self.F)["Q2"]
        with self.assertRaises(KitError) as ctx:
            holdout_manifest.write_leak_waiver(self.F, seal)
        self.assertEqual(str(ctx.exception),
                         holdout_manifest.WAIVER_NOT_CLEAN_MSG)
        # A hand-made waiver (as the writer would make it, minus the clean
        # re-scan) is not valid and waives nothing.
        scans = load(os.path.join(self.F, "LEAKSCAN.json"))["scans"]
        dump(os.path.join(self.F, holdout_kit.LEAK_WAIVER), {
            "schema": holdout_kit.LEAK_WAIVER_SCHEMA, "mode": "dry-run",
            "folder": self.F,
            "seal_sha256": holdout_kit.sha256_file(
                os.path.join(self.F, "SEAL.json")),
            "clean_scan_at": scans[-1]["at"],
            "cases": {cid: {"slot": "Q2", "leak": "waived (dry-run)",
                            "named_at": scans[0]["at"]}}})
        self.assertEqual(holdout_manifest.leak_waiver_problems(self.F, seal),
                         [holdout_manifest.WAIVER_NOT_CLEAN_MSG])
        problems = holdout_manifest.leak_ledger_problems(self.F, seal,
                                                         dry_run=True)
        self.assertIn(holdout_manifest.LEAK_FOUND_MSG, problems)
        self.assertTrue(any("was named by a leak scan" in p
                            for p in problems))
        # Mutant: accepting that waiver still leaves the hit as the last
        # scan, so the dry run never counts the scan as settled.
        with mock.patch.object(holdout_manifest, "leak_waiver_problems",
                               return_value=[]):
            self.assertEqual(holdout_manifest.leak_ledger_problems(
                self.F, seal, dry_run=True),
                [holdout_manifest.LEAK_FOUND_MSG])

    def test_waiver_is_bound_to_the_seal_and_the_scan(self):
        self.waived_folder()
        path = os.path.join(self.F, "SEAL.json")
        seal = load(path)
        self.assertEqual(holdout_manifest.leak_waiver_problems(self.F, seal),
                         [])
        wpath = os.path.join(self.F, holdout_kit.LEAK_WAIVER)
        good = load(wpath)
        for key, value in (("folder", "/elsewhere"),
                           ("clean_scan_at", "1999-01-01T00:00:00Z"),
                           ("seal_sha256", "0" * 64), ("mode", "real")):
            dump(wpath, dict(good, **{key: value}))
            self.assertEqual(holdout_manifest.leak_waiver_problems(
                self.F, seal), [holdout_manifest.WAIVER_INVALID_MSG], key)
        bad = json.loads(json.dumps(good))
        next(iter(bad["cases"].values()))["leak"] = "waived"
        dump(wpath, bad)
        self.assertEqual(holdout_manifest.leak_waiver_problems(self.F, seal),
                         [holdout_manifest.WAIVER_INVALID_MSG])
        dump(wpath, good)
        # Another seal (a re-seal changes its bytes): the last scan is no
        # longer against the current seal, so nothing is waived.
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\n")
        self.assertEqual(holdout_manifest.leak_waiver_problems(self.F, seal),
                         [holdout_manifest.WAIVER_NOT_CLEAN_MSG])

    def test_replace_retired_under_dry_run(self):
        old, keep, before = self.disagree_then_retire()
        marks = self.login_marks()
        j0 = self.journal()
        g1, g2 = (j0["xcheck"]["1"]["session_id"],
                  j0["xcheck"]["2"]["session_id"])
        n = self.mark_calls()
        scrub = holdout_archive.scrub
        kept = {}

        def check_then_scrub(folder, *a, **kw):
            # A finished dry run scrubs the folder, config dirs included;
            # every login must still be intact when scrub begins.
            kept.update({p: holdout_kit.sha256_file(p) for p in marks})
            return scrub(folder, *a, **kw)

        with mock.patch.object(holdout_archive, "scrub",
                               side_effect=check_then_scrub):
            rc, out, err = self.cli("--dry-run", "--replace-retired",
                                    repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), DRY_OK)
        self.assertEqual(holdout_manifest.resume_reply_kind(
            self.last_line(out)), "dry-run-ok")
        self.assertIn("step populate: replaced 1 retired dummy case(s), "
                      "slots C1", out)
        self.assertIn("step crosscheck: generation 3 probe ok (14/14)", out)
        # A fresh blind judging round in generation 3 (never a burned one).
        prompts = [(self.cfg(c), self.prompt(c))
                   for c in self.p_calls(self.since(n))]
        self.assertIn(("cfg-xcheck-r3", ap.XCHECK_BEGIN_PROMPT), prompts)
        self.assertNotIn(ap.XCHECK_BEGIN_PROMPT,
                         [p for c, p in prompts if c != "cfg-xcheck-r3"])
        reg = self.registry_before_scrub
        self.assertEqual([g["gen"] for g in reg["generations"]], [1, 2, 3])
        # Different dummy material on every fingerprint field.
        new = [cid for (part, cid, rel) in self.hashes_before_scrub
               if cid not in old.values()]
        self.assertEqual(len(set(new)), 1)
        self.assertNotIn(old["C1"], {c for (_, c, _) in
                                     self.hashes_before_scrub})
        # Completed work, the journal's sessions and the logins are kept.
        self.assert_trees_kept(before)
        self.assertEqual(kept, marks)
        j = self.journal()
        self.assertEqual(j["xcheck"]["1"]["session_id"], g1)
        self.assertEqual(j["xcheck"]["2"]["session_id"], g2)
        self.assertEqual(j["replace"]["pending"], [])
        self.assertEqual(j["replaced_slots"], ["C1"])
        for line in out.splitlines():
            self.assertRegex(line, ALLOWED_LINE)
        self.assert_opaque(out, err)

        # A plain dry-run re-run after success launches nothing and repeats
        # the dry-run ok line.
        n = self.mark_calls()
        rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0)
        self.assertEqual(self.last_line(out), DRY_OK)
        self.assertEqual(self.p_calls(self.since(n)), [])

    def test_new_material_differs_on_every_field(self):
        old, _, _ = self.disagree_then_retire()
        real = holdout_seal.prepare_crosscheck
        seen = {}

        def capture(folder, *a, **kw):
            new = slot_ids(folder).get("C1")
            if new and new != old["C1"]:
                seen["C1"] = new
                self.assert_differs_on_every_field(new)
            return real(folder, *a, **kw)

        with mock.patch.object(holdout_seal, "prepare_crosscheck",
                               side_effect=capture):
            rc, out, err = self.cli("--dry-run", "--replace-retired",
                                    repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("C1", seen)

    def test_new_generation_needs_its_own_login(self):
        self.disagree_then_retire()
        self.control(logged_in={"cfg-xcheck-r3": False})
        rc, out, err = self.cli("--dry-run", "--replace-retired", repo=False)
        self.assertEqual(rc, 1)
        problem = [line for line in (out + err).splitlines()
                   if line.startswith("PROBLEM: ")]
        self.assertEqual(len(problem), 1, out + err)
        self.assertIn(os.path.join(self.F, "bin", "crosscheck-r3"), problem[0])
        self.assertIn("/login", problem[0])
        self.assertIn("bin/holdout autopilot --dry-run again", problem[0])
        self.assertEqual(self.journal()["replace"]["pending"], [])
        # After the login a plain dry-run rerun finishes.
        self.control()
        rc, out, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), DRY_OK)

    def test_leak_during_dry_run_then_replace(self):
        real = holdout_archive.leakscan
        planted = os.path.join(self.scan, "pasted.txt")
        state = {"done": False}

        def plant_then_scan(folder, *a, **kw):
            if not state["done"]:
                state["done"] = True
                by_slot = {}
                for probe, slot, _ in holdout_archive._probes(folder):
                    by_slot.setdefault(slot, probe)
                with open(planted, "w", encoding="utf-8") as fh:
                    fh.write(by_slot["Q2"] + "\n")
            return real(folder, *a, **kw)

        with mock.patch.object(holdout_archive, "leakscan",
                               side_effect=plant_then_scan):
            rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 3)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked leakscan")
        self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS["leakscan-dry"]
                         % "Q2")
        self.assertTrue(os.path.exists(os.path.join(self.F, "SEAL.json")))
        os.remove(planted)
        old = slot_ids(self.F)
        keep = [old[s] for s in holdout_kit.SLOTS if s != "Q2"]
        before = tree_hashes(self.F, keep)
        rc, out, err = self.cli("--dry-run", "--replace-retired", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), DRY_OK)
        self.assert_trees_kept(before)
        self.assertIn("step crosscheck: generation 3 probe ok (14/14)", out)

    def test_interrupted_write_resumes_without_the_flag(self):
        old, keep, before = self.disagree_then_retire()
        real = holdout_dryrun.record_proof_results

        def crash(*a, **kw):
            raise RuntimeError("synthetic crash")

        with mock.patch.object(holdout_dryrun, "record_proof_results",
                               side_effect=crash):
            with self.assertRaises(RuntimeError):
                self.cli("--dry-run", "--replace-retired", repo=False)
        j = self.journal()
        self.assertEqual([e["slot"] for e in j["replace"]["pending"]], ["C1"])
        self.assertEqual(j["replace"]["removed"], [old["C1"]])
        partial = j["replace"]["pending"][0]["new_id"]
        self.assertIn(partial, holdout_kit.case_ids(self.F))
        self.assertIs(real, holdout_dryrun.record_proof_results)
        rc, out, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), DRY_OK)
        self.assert_trees_kept(before)

    def test_intent_is_on_disk_before_the_delete(self):
        old, _, _ = self.disagree_then_retire()
        real = shutil.rmtree

        def never(path, *a, **kw):
            if os.path.basename(os.path.normpath(path)) == old["C1"]:
                raise RuntimeError("synthetic crash")
            return real(path, *a, **kw)

        with mock.patch.object(shutil, "rmtree", side_effect=never):
            with self.assertRaises(RuntimeError):
                self.cli("--dry-run", "--replace-retired", repo=False)
        j = self.journal()
        self.assertEqual(j["replace"]["pending"],
                         [{"id": old["C1"], "slot": "C1"}])
        self.assertEqual(j["replace"]["removed"], [])

    def test_mutant_flag_dropped_under_dry_run_loops(self):
        # The pre-fix behaviour: cmd() never handed the flag to dry_run, so
        # a leak-retired dummy case was never replaced.
        self.leak_stop()
        real = ap.dry_run

        def dropped(folder, repo=None, replace_retired=False, **kw):
            return real(folder, repo=repo, **kw)

        old = slot_ids(self.F)["Q2"]
        with mock.patch.object(ap, "dry_run", side_effect=dropped):
            rc, out, _ = self.cli("--dry-run", "--replace-retired",
                                  repo=False)
        # The owner asked for a replacement and silently got the plain
        # path: the leak-named case is kept (waived), nothing replaced.
        self.assertEqual(rc, 0)
        self.assertNotIn("step populate: replaced", out)
        self.assertIn("leak waived (dry-run)", out)
        self.assertIn(old, load(os.path.join(
            self.F, holdout_kit.LEAK_WAIVER))["cases"])

    def test_flag_honoured_replaces_instead_of_waiving(self):
        self.leak_stop()
        old = slot_ids(self.F)["Q2"]
        rc, out, err = self.cli("--dry-run", "--replace-retired", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), DRY_OK)
        self.assertIn("step populate: replaced 1 retired dummy case(s), "
                      "slots Q2", out)
        self.assertNotIn(old, load(os.path.join(self.F, "SEAL.json"))["cases"])
        self.assertFalse(os.path.exists(
            os.path.join(self.F, holdout_kit.LEAK_WAIVER)))

    def test_mutant_same_material_is_refused(self):
        # Regenerating the retired material (same nonce, same variant) must
        # never reach the seal: the fingerprint guard refuses it.
        old, _, _ = self.disagree_then_retire()
        key = load(os.path.join(self.F, "sealed", "keys", old["C1"],
                                "key.json"))
        nonce = re.search(r"variant 0, ([0-9a-f]+)\)", key["defect"]).group(1)
        with mock.patch.object(holdout_dryrun, "_replacement_nonce",
                               return_value=nonce), \
                mock.patch.object(holdout_dryrun, "_next_variant",
                                  return_value=0):
            rc, _, err = self.cli("--dry-run", "--replace-retired",
                                  repo=False)
        self.assertEqual(rc, 1)
        self.assertIn(holdout_dryrun.SAME_MATERIAL_MSG % "C1", err)

    def test_mutant_unguarded_same_material_blocks_seal(self):
        old, _, _ = self.disagree_then_retire()
        key = load(os.path.join(self.F, "sealed", "keys", old["C1"],
                                "key.json"))
        nonce = re.search(r"variant 0, ([0-9a-f]+)\)", key["defect"]).group(1)
        with mock.patch.object(holdout_dryrun, "_replacement_nonce",
                               return_value=nonce), \
                mock.patch.object(holdout_dryrun, "_next_variant",
                                  return_value=0), \
                mock.patch.object(holdout_dryrun, "_retired_matches",
                                  return_value=[]):
            _, out, _ = self.cli("--dry-run", "--replace-retired",
                                 repo=False)
        self.assertNotEqual(self.last_line(out), DRY_OK)


class TestDryRunPassRule(PipelineCase):
    """51-09 owner decision: the dry run proves the machinery works. The real
    headless judge still runs (probe, sandbox, blind verdict, reveal, final)
    and must write well-formed verdicts; its agreement is RECORDED, never
    required and never rewritten. A disagreement is sealed on an explicitly
    marked synthetic-agreement record that only a dry-run seal in a dry-run
    folder accepts; no 7b stop, retire, replacement or new generation."""

    def written(self):
        """{(XID, name): bytes} the fake judge wrote (X-xxxxxxxx-<name>)."""
        keep = os.path.join(self.fakebin, "written")
        out = {}
        for name in sorted(os.listdir(keep)) if os.path.isdir(keep) else []:
            with open(os.path.join(keep, name), "rb") as fh:
                out[(name[:10], name[11:])] = fh.read()
        return out

    def assert_verdicts_preserved(self, cid):
        """Every verdict the real judge wrote is byte-identical in its packet
        when scrub begins, and the sealed crosscheck.json of `cid` is its
        final.json."""
        written = self.written()
        self.assertTrue(written)
        for key, data in written.items():
            self.assertEqual(self.packets_before_scrub.get(key), data, key)
        finals = [d for (x, n), d in written.items() if n == "final.json"]
        self.assertEqual(len(finals), 1)
        self.assertEqual(self.hashes_before_scrub[
            ("keys", cid, "crosscheck.json")],
            holdout_kit.sha256_bytes(finals[0]))

    def test_disagreement_is_recorded_not_required(self):
        self.control(disagree_slot="C1")
        rc, out, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), DRY_OK)
        self.assertIn("step crosscheck: real judge verdict recorded "
                      "(disagreed)", out)
        self.assertNotRegex(out, r"(?<![0-9a-f])7b(?![0-9a-f])")
        cid = sealed_slot(self.F, "C1")
        # One real judging round, in generation 2; no further generation.
        begins = [self.cfg(c) for c in self.p_calls()
                  if self.prompt(c) == ap.XCHECK_BEGIN_PROMPT]
        self.assertEqual(begins, ["cfg-xcheck-r2"])
        self.assertEqual([g["gen"] for g in
                          self.registry_before_scrub["generations"]], [1, 2])
        # The judge's verdict is kept as written (lock c).
        self.assert_verdicts_preserved(cid)
        # The synthetic record is explicit, dry-run only, covers C1 alone
        # and binds the judge's final.json bytes.
        rec = self.synthetic_before_scrub
        self.assertEqual(rec["mode"], "dry-run")
        self.assertEqual(rec["judged"], {cid: "disagreed"})
        self.assertEqual(sorted(rec["cases"]), [cid])
        entry = rec["cases"][cid]
        self.assertEqual((entry["agreement"], entry["judge_outcome"],
                          entry["mode"]), ("synthetic", "disagreed",
                                           "dry-run"))
        final = [d for (x, n), d in self.written().items()
                 if n == "final.json"][0]
        self.assertEqual(entry["final_sha256"],
                         holdout_kit.sha256_bytes(final))
        # The seal says so, and can never pass for the real one.
        seal = load(os.path.join(self.F, "SEAL.json"))
        self.assertEqual(seal["status"], "dry-run")
        self.assertEqual(seal["mode"], "dry-run")
        self.assertEqual(seal["cases"][cid]["agreement"], "synthetic")
        self.assertEqual(seal["cases"][cid]["judge_outcome"], "disagreed")
        for other, e in seal["cases"].items():
            if other != cid:
                self.assertEqual(set(e), {"slot", "hmac"})
        self.assertTrue(holdout_manifest.is_dry_run_seal(seal))
        self.assertIn("status is not sealed",
                      holdout_manifest.public_shape_problems(seal))
        for line in out.splitlines():
            self.assertRegex(line, ALLOWED_LINE)
        self.assert_opaque(out, err)

    def test_agreement_is_recorded_too(self):
        rc, out, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("step crosscheck: real judge verdict recorded "
                      "(agreed)", out)
        cid = sealed_slot(self.F, "C1")
        self.assertEqual(self.synthetic_before_scrub["cases"], {})
        seal = load(os.path.join(self.F, "SEAL.json"))
        self.assertEqual(seal["cases"][cid], {
            "slot": "C1", "hmac": seal["cases"][cid]["hmac"],
            "judge_outcome": "agreed"})
        self.assert_verdicts_preserved(cid)

    def test_mutant_overwritten_verdict_is_caught(self):
        # Lock c: an autopilot that "fixed" the judge's final.json into an
        # agreeing one would still finish; the preservation check catches it.
        self.control(disagree_slot="C1")
        real = holdout_seal.record_synthetic_agreement

        def overwrite_then_record(folder, *a, **kw):
            for ws in os.listdir(folder):
                if ws == "xcheck-r2":
                    for xid in os.listdir(os.path.join(folder, ws)):
                        packet = os.path.join(folder, ws, xid)
                        if os.path.isdir(os.path.join(packet, "revealed")):
                            holdout_kit.write_json_atomic(
                                os.path.join(packet, "final.json"),
                                dict(holdout_dryrun._final(packet),
                                     notes="rewritten"))
            return real(folder, *a, **kw)

        with mock.patch.object(holdout_seal, "record_synthetic_agreement",
                               side_effect=overwrite_then_record):
            rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(self.last_line(out), DRY_OK)
        with self.assertRaises(AssertionError):
            self.assert_verdicts_preserved(sealed_slot(self.F, "C1"))

    def test_malformed_final_stops_without_retire(self):
        self.control(disagree_slot="C1")
        real = holdout_seal.record_synthetic_agreement

        def break_then_record(folder, *a, **kw):
            for xid in os.listdir(os.path.join(folder, "xcheck-r2")):
                final = os.path.join(folder, "xcheck-r2", xid, "final.json")
                if os.path.isfile(final):
                    data = load(final)
                    data.pop("notes")
                    dump(final, data)
            return real(folder, *a, **kw)

        with mock.patch.object(holdout_seal, "record_synthetic_agreement",
                               side_effect=break_then_record):
            rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 3)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked other")
        self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS["judge-malformed"])
        self.assertFalse(os.path.exists(os.path.join(self.F, "SEAL.json")))
        self.assertFalse(os.path.exists(os.path.join(
            self.F, holdout_kit.SYNTHETIC_AGREEMENT)))

    def test_mutant_unrecorded_disagreement_never_takes_the_7b_path(self):
        # Without the recorded synthetic agreement the dry-run seal refuses;
        # the stop names neither README 7b nor a retire/replace command.
        self.control(disagree_slot="C1")
        with mock.patch.object(ap, "_record_outcomes", return_value=None):
            for _ in range(2):
                rc, out, _ = self.cli("--dry-run", repo=False)
                self.assertEqual(rc, 3)
                lines = out.strip().splitlines()
                self.assertEqual(lines[-1], "blocked other")
                cid = slot_ids(self.F)["C1"]
                self.assertEqual(lines[-2], _render_h(
                    ap.STOP_INSTRUCTIONS["disagreement-dry"] % (cid, "C1"),
                    self.F))
                self.assertNotRegex(out, r"(?<![0-9a-f])7b(?![0-9a-f])")
                self.assertNotIn("--replace-retired", out)
        self.assertEqual(len(load(os.path.join(
            self.F, *holdout_seal.WORKSPACES_RELPATH.split("/")))
            ["generations"]), 2)

    def test_real_run_disagreement_path_unchanged(self):
        # The 7b stop of the real run is untouched (TestDisagreement holds
        # the full lock); a real folder never gets synthetic agreement.
        self.control(disagree_slot="C3")
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        self.assertEqual(self.last_line(out), "blocked disagreement")
        self.assertFalse(holdout_kit.dry_run_markers_present(self.F))
        with self.assertRaises(KitError):
            holdout_seal.record_synthetic_agreement(self.F, [1],
                                                    dry_run=True)
        self.assertFalse(holdout_kit.dry_run_markers_present(self.F))


def sealed_slot(folder, slot):
    """The ID the folder's SEAL.json gives `slot` (works after scrub)."""
    seal = load(os.path.join(folder, "SEAL.json"))
    return [c for c, e in seal["cases"].items() if e["slot"] == slot][0]


def _render_h(text, h):
    return text.replace("<H>", h)


class TestDryRunLegacyResume(PipelineCase):
    """An existing dry-run folder left by the old retire/replace loop
    (extra generations, a retired case, no marker): refresh-kit adds the
    marker only on mechanical proof, then ONE plain dry run finishes from
    the current state with no retirement, replacement or new generation."""

    def legacy(self, retire=False, extra_generation=False):
        self.control(disagree_slot="C1")
        with mock.patch.object(ap, "_record_outcomes", return_value=None):
            rc, out, _ = self.cli("--dry-run", repo=False)
            self.assertEqual(self.last_line(out), "blocked other")
            if extra_generation:
                self.retire("C1")
                rc, out, _ = self.cli("--dry-run", "--replace-retired",
                                      repo=False)
                self.assertEqual(self.last_line(out), "blocked other")
        if retire:
            self.retire("C1")
        # A folder from before this fix carries neither file.
        for name in holdout_kit.DRY_RUN_MARKERS:
            path = os.path.join(self.F, name)
            if os.path.exists(path):
                os.remove(path)
        self.control()
        return self.generations()

    def retire(self, slot):
        rc, _, err = self.capture(holdout_kit.run, [
            "--folder", self.F, "retire", "--slot", slot, "--reason",
            "owner"])
        self.assertEqual(rc, 0, err)

    def generations(self):
        return [g["gen"] for g in load(os.path.join(
            self.F, *holdout_seal.WORKSPACES_RELPATH.split("/")))
            ["generations"]]

    def refresh(self):
        rc, out, err = self.capture(holdout_kit.run,
                                    ["--folder", self.F, "refresh-kit"])
        self.assertEqual(rc, 0, out + err)
        return out

    def resume_once(self, gens):
        n = self.mark_calls()
        cfgs = sorted(n for n in os.listdir(self.F) if n.startswith("cfg-"))
        rc, out, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(self.last_line(out), DRY_OK)
        self.assertIn("step crosscheck: real judge verdict recorded "
                      "(disagreed)", out)
        since = self.p_calls(self.since(n))
        self.assertNotIn(ap.XCHECK_BEGIN_PROMPT,
                         [self.prompt(c) for c in since])
        self.assertEqual([g["gen"] for g in
                          self.registry_before_scrub["generations"]], gens)
        # No new generation, so no new config dir and no new login.
        self.assertEqual({self.cfg(c) for c in self.calls()[n:]}
                         - set(cfgs), set())
        self.assertEqual(self.journal()["replace"]["pending"], [])
        self.assertNotIn("replace", out)
        for line in out.splitlines():
            self.assertRegex(line, ALLOWED_LINE)
        self.assert_opaque(out, err)
        return out, load(os.path.join(self.F, "SEAL.json"))

    def test_stopped_at_disagreement(self):
        gens = self.legacy()
        self.assertEqual(gens, [1, 2])
        out = self.refresh()
        self.assertIn("OK: dry-run marker added", out)
        self.assertTrue(holdout_kit.dry_run_marker_ok(self.F))
        _, seal = self.resume_once([1, 2])
        cid = sealed_slot(self.F, "C1")
        self.assertEqual(seal["cases"][cid]["agreement"], "synthetic")
        self.assertEqual(seal["cases"][cid]["judge_outcome"], "disagreed")

    def test_retired_and_not_replaced(self):
        gens = self.legacy(retire=True)
        self.assertEqual(gens, [1, 2])
        self.refresh()
        _, seal = self.resume_once([1, 2])
        cid = sealed_slot(self.F, "C1")
        self.assertEqual(seal["cases"][cid]["retired_material"], "waived")
        self.assertEqual(seal["cases"][cid]["agreement"], "synthetic")

    def test_extra_generation_then_retired_again(self):
        gens = self.legacy(retire=True, extra_generation=True)
        self.assertEqual(gens, [1, 2, 3])
        self.refresh()
        _, seal = self.resume_once([1, 2, 3])
        cid = sealed_slot(self.F, "C1")
        self.assertEqual(seal["cases"][cid]["judge_outcome"], "disagreed")
        self.assertEqual(seal["cases"][cid]["retired_material"], "waived")

    def test_without_refresh_names_refresh_kit(self):
        self.legacy()
        n = self.mark_calls()
        rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 3)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked other")
        self.assertEqual(lines[-2], ap.for_mode(
            ap.STOP_INSTRUCTIONS["not-dry-folder"], "dry-run"))
        self.assertNotIn(ap.XCHECK_BEGIN_PROMPT,
                         [self.prompt(c) for c in self.p_calls(self.since(n))])
        self.assertFalse(holdout_kit.dry_run_markers_present(self.F))

    def test_refresh_is_idempotent(self):
        self.legacy()
        self.refresh()
        marker = os.path.join(self.F, holdout_kit.DRYRUN_MARKER)
        before = holdout_kit.sha256_file(marker)
        out = self.refresh()
        self.assertIn("OK: dry-run marker present", out)
        self.assertEqual(holdout_kit.sha256_file(marker), before)


class TestDryRunMarkerProof(PipelineCase):
    """refresh-kit adds DRY-RUN.json only when the folder is provably a dry
    run, and never to a real folder."""

    def refresh(self):
        return self.capture(holdout_kit.run,
                            ["--folder", self.F, "refresh-kit"])

    def real_folder_mid_run(self):
        # The hardest real case: a real autopilot run whose (fake) finder
        # wrote dummy-shaped cases from the dry-run repos. Only the journal
        # says it is real.
        self.control(disagree_slot="C3")
        rc, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "blocked disagreement")
        self.control()
        self.assertEqual(self.journal()["mode"], "real")

    def test_real_folder_is_never_marked(self):
        self.real_folder_mid_run()
        self.assertEqual(ap.dry_run_folder_problems(self.F),
                         ["the autopilot journal is not a dry run's"])
        rc, out, err = self.refresh()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("OK: dry-run marker: not added", out)
        self.assertFalse(holdout_kit.dry_run_markers_present(self.F))

    def test_mutant_unproven_marker_marks_a_real_folder(self):
        self.real_folder_mid_run()
        with mock.patch.object(ap, "dry_run_folder_problems",
                               return_value=[]):
            self.refresh()
        self.assertTrue(holdout_kit.dry_run_marker_ok(self.F))

    def test_journal_less_folder_is_not_proven(self):
        with mock.patch.dict(os.environ, holdout_fixture.kit_env()):
            holdout_dryrun.populate(self.F, mark_dry_run=False)
        self.assertEqual(ap.dry_run_folder_problems(self.F),
                         ["no autopilot journal"])

    def dry_folder_without_marker(self):
        with mock.patch.object(ap, "_record_outcomes", return_value=None):
            self.control(disagree_slot="C1")
            self.cli("--dry-run", repo=False)
        os.remove(os.path.join(self.F, holdout_kit.DRYRUN_MARKER))
        self.control()
        self.assertEqual(ap.dry_run_folder_problems(self.F), [])

    def test_foreign_case_blocks_the_proof(self):
        self.dry_folder_without_marker()
        cid = slot_ids(self.F)["Q3"]
        prov = os.path.join(self.F, "sealed", "keys", cid, "provenance.json")
        data = load(prov)
        data["source_repo"] = self.R
        dump(prov, data)
        self.assertEqual(ap.dry_run_folder_problems(self.F),
                         ["a case does not come from the dry-run repos"])
        rc, out, _ = self.refresh()
        self.assertEqual(rc, 0)
        self.assertFalse(holdout_kit.dry_run_markers_present(self.F))

    def test_non_synthetic_key_blocks_the_proof(self):
        self.dry_folder_without_marker()
        cid = slot_ids(self.F)["Q1"]
        key = os.path.join(self.F, "sealed", "keys", cid, "key.json")
        data = load(key)
        for k, v in list(data.items()):
            if isinstance(v, str):
                data[k] = v.replace(holdout_dryrun.SYNTHETIC_TAG, "real")
        dump(key, data)
        self.assertEqual(ap.dry_run_folder_problems(self.F),
                         ["a case key is not synthetic"])

    def test_missing_dry_run_repo_blocks_the_proof(self):
        self.dry_folder_without_marker()
        shutil.rmtree(os.path.join(self.F, holdout_dryrun.REPOS_DIRNAME,
                                   "dryrun-beta"))
        self.assertEqual(ap.dry_run_folder_problems(self.F),
                         ["a dry-run repo is missing"])

    def test_invalid_marker_is_a_problem_and_kept(self):
        self.dry_folder_without_marker()
        path = os.path.join(self.F, holdout_kit.DRYRUN_MARKER)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{}\n")
        rc, out, _ = self.refresh()
        self.assertEqual(rc, 1)
        self.assertIn("DRY-RUN.json exists but is not a valid marker", out)
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "{}\n")

    def test_copied_marker_is_not_valid_elsewhere(self):
        self.dry_folder_without_marker()
        other = os.path.join(self.tmp, "elsewhere")
        os.makedirs(other)
        holdout_kit.write_dry_run_marker(self.F, "2026-10-08T00:00:00Z")
        shutil.copy(os.path.join(self.F, holdout_kit.DRYRUN_MARKER), other)
        self.assertTrue(holdout_kit.dry_run_marker_ok(self.F))
        self.assertFalse(holdout_kit.dry_run_marker_ok(other))
        self.assertEqual(holdout_kit.dry_run_markers_present(other),
                         [holdout_kit.DRYRUN_MARKER])


class TestDryRunRejectedOutsideDryRun(PipelineCase):
    """Synthetic agreement and dry-run marks are refused by real sealing,
    publish, seal-build and the Phase-55 rehash (locks a and b)."""

    def recorded_folder(self):
        """A dry-run folder stopped before seal with the real judge's C1
        disagreement recorded as synthetic agreement."""
        self.control(disagree_slot="C1")
        with mock.patch.object(ap, "_step_seal", side_effect=ap.Stop(
                "other", "stopped by the test")):
            rc, out, _ = self.cli("--dry-run", repo=False)
        self.assertEqual(self.last_line(out), "blocked other")
        self.assertIn("real judge verdict recorded (disagreed)", out)
        self.control()
        return slot_ids(self.F)["C1"]

    def test_lock_a_synthetic_only_in_dry_run_mode(self):
        cid = self.recorded_folder()
        self.assertEqual(holdout_seal.seal_blockers(self.F, dry_run=True), [])
        self.assertEqual(holdout_seal.seal_blockers(self.F),
                         [holdout_kit.DRY_RUN_REFUSED_MSG])
        rc, out, _ = self.capture(holdout_kit.run,
                                  ["--folder", self.F, "seal"])
        self.assertEqual(rc, 1)
        self.assertIn(holdout_kit.DRY_RUN_REFUSED_MSG, out)
        self.assertFalse(os.path.exists(os.path.join(self.F, "SEAL.json")))
        # Without the folder marker neither mode accepts the record.
        os.remove(os.path.join(self.F, holdout_kit.DRYRUN_MARKER))
        self.assertEqual(holdout_seal.seal_blockers(self.F),
                         [holdout_kit.DRY_RUN_REFUSED_MSG])
        self.assertEqual(holdout_seal.seal_blockers(self.F, dry_run=True),
                         [holdout_seal.NOT_DRY_RUN_FOLDER_MSG])
        self.assertIn(cid, holdout_kit.case_ids(self.F))

    def test_mutant_a_synthetic_accepted_in_real_mode_seals(self):
        cid = self.recorded_folder()
        # One guard out: the mode-gated record still does not apply.
        with mock.patch.object(holdout_seal, "_dry_run_refusal",
                               return_value=None):
            blockers = holdout_seal.seal_blockers(self.F)
        self.assertEqual(len(blockers), 1)
        self.assertIn("Case C1: the independent check disagreed", blockers[0])
        # Both guards out: a real seal accepts synthetic agreement.
        with mock.patch.object(holdout_seal, "_dry_run_refusal",
                               return_value=None), \
                mock.patch.object(holdout_seal, "_synthetic_for",
                                  side_effect=lambda f, d:
                                  holdout_seal.load_synthetic(f)):
            seal = holdout_seal.do_seal(self.F)
        self.assertEqual(seal["status"], "sealed")
        self.assertIn(cid, seal["cases"])

    def test_record_is_bound_to_the_judges_final_bytes(self):
        self.recorded_folder()
        led = holdout_seal._load_ledger(self.F, slot_ids(self.F)["C1"])
        final = os.path.join(holdout_seal._packet_dir(self.F, led),
                             "final.json")
        with open(final, "a", encoding="utf-8") as fh:
            fh.write(" ")
        blockers = holdout_seal.seal_blockers(self.F, dry_run=True)
        self.assertEqual(len(blockers), 1)
        self.assertIn("Case C1: the independent check disagreed", blockers[0])

    def test_record_needs_dry_run_mode_and_marker(self):
        self.recorded_folder()
        with self.assertRaises(KitError) as ctx:
            holdout_seal.record_synthetic_agreement(self.F, [2])
        self.assertEqual(str(ctx.exception),
                         holdout_seal.SYNTHETIC_REFUSED_MSG)
        os.remove(os.path.join(self.F, holdout_kit.DRYRUN_MARKER))
        with self.assertRaises(KitError):
            holdout_seal.record_synthetic_agreement(self.F, [2],
                                                    dry_run=True)

    def test_real_autopilot_refuses_a_dry_folder(self):
        self.recorded_folder()
        for name in (holdout_kit.DRYRUN_MARKER,
                     holdout_kit.SYNTHETIC_AGREEMENT):
            rc, out, err = self.cli()
            self.assertEqual(rc, 1)
            self.assertIn(ap.DRY_FOLDER_REAL_MSG, out + err)
            os.remove(os.path.join(self.F, name))

    def finished_dry_run(self):
        self.control(disagree_slot="C1")
        rc, out, err = self.cli("--dry-run", repo=False)
        self.assertEqual(rc, 0, out + err)
        self.control()
        return load(os.path.join(self.F, "SEAL.json"))

    def test_lock_b_dry_seal_is_never_published(self):
        seal = self.finished_dry_run()
        # Scrub keeps the folder markers, and the seal itself says so.
        self.assertEqual(holdout_kit.dry_run_markers_present(self.F),
                         [holdout_kit.DRYRUN_MARKER,
                          holdout_kit.SYNTHETIC_AGREEMENT])
        self.assertTrue(holdout_manifest.is_dry_run_seal(seal))
        rc, out, err = self.capture(holdout_kit.run, [
            "--folder", self.F, "publish", "--repo", self.R])
        self.assertEqual(rc, 1)
        self.assertIn(holdout_kit.DRY_RUN_REFUSED_MSG, err)
        self.assertFalse(os.path.exists(self.published()))
        # 51-09 Task 3's public-shape check rejects it too.
        self.assertTrue(holdout_manifest.public_shape_problems(seal))

    def test_scrubbed_old_format_seal_still_refused(self):
        # A dry-run folder whose seal lost its dry-run marks (an older kit's
        # seal): the surviving folder marker alone still refuses publish.
        self.finished_dry_run()
        path = os.path.join(self.F, "SEAL.json")
        dump(path, holdout_manifest._dry_seal_public_view(load(path)))
        self.assertEqual(holdout_manifest.public_shape_problems(load(path)),
                         [])
        with self.assertRaises(KitError) as ctx:
            holdout_manifest.publish(self.F, self.R)
        self.assertIn(holdout_kit.DRY_RUN_REFUSED_MSG, str(ctx.exception))
        self.assertFalse(os.path.exists(self.published()))

    def test_mutant_b_dry_seal_publishable(self):
        self.finished_dry_run()
        # One guard out: the public-shape check still refuses.
        with mock.patch.object(holdout_manifest, "dry_run_problems",
                               return_value=[]):
            with self.assertRaises(KitError):
                holdout_manifest.publish(self.F, self.R)
        self.assertFalse(os.path.exists(self.published()))
        # Both out: the dummy seal lands in the repo.
        with mock.patch.object(holdout_manifest, "dry_run_problems",
                               return_value=[]), \
                mock.patch.object(holdout_manifest, "public_shape_problems",
                                  return_value=[]):
            holdout_manifest.publish(self.F, self.R)
        self.assertTrue(os.path.exists(self.published()))

    def test_public_shaped_seal_in_a_marked_folder_is_refused(self):
        self.recorded_folder()
        self.assertEqual(holdout_seal.do_seal(self.F, dry_run=True)["status"],
                         "dry-run")
        path = os.path.join(self.F, "SEAL.json")
        dump(path, holdout_manifest._dry_seal_public_view(load(path)))
        self.assertFalse(holdout_manifest.is_dry_run_seal(load(path)))
        with self.assertRaises(KitError) as ctx:
            holdout_manifest.publish(self.F, self.R)
        self.assertIn(holdout_kit.DRY_RUN_REFUSED_MSG, str(ctx.exception))
        rc, _, _ = self.capture(holdout_kit.run, [
            "--folder", self.F, "seal-build"])
        self.assertEqual(rc, 1)

    def test_phase55_rehash_refuses_dry_marks(self):
        self.recorded_folder()
        holdout_seal.do_seal(self.F, dry_run=True)
        seal_path = os.path.join(self.F, "SEAL.json")
        sealed = os.path.join(self.F, "sealed")
        rc, out, _ = self.capture(holdout_kit.run, [
            "--folder", self.F, "rehash", "--seal", seal_path, "--sealed",
            sealed])
        self.assertEqual(rc, 1)
        self.assertIn(holdout_kit.DRY_RUN_REFUSED_MSG, out)
        rc, out, _ = self.capture(holdout_kit.run, [
            "--folder", self.F, "rehash", "--dry-run", "--seal", seal_path,
            "--sealed", sealed])
        self.assertEqual(rc, 0, out)
        # A public-shaped copy of the seal is still refused beside a marker.
        public = os.path.join(self.tmp, "public-seal.json")
        dump(public, holdout_manifest._dry_seal_public_view(load(seal_path)))
        with self.assertRaises(KitError) as ctx:
            holdout_manifest.rehash_folder(public, sealed)
        self.assertEqual(str(ctx.exception), holdout_kit.DRY_RUN_REFUSED_MSG)
        # --dry-run outside a marked folder is refused.
        os.remove(os.path.join(self.F, holdout_kit.DRYRUN_MARKER))
        rc, out, _ = self.capture(holdout_kit.run, [
            "--folder", self.F, "rehash", "--dry-run", "--seal", seal_path,
            "--sealed", sealed])
        self.assertEqual(rc, 1)
        self.assertIn(holdout_manifest.NOT_A_DRY_FOLDER_MSG, out)


class TestResultGrammar(AutopilotCase):

    LINES = ("sealed", "sealed non-runnable=2", "replaced slots=C2",
             "replaced slots=C1,Q2 non-runnable=1",
             "dry run ok prompted sandbox=ok", "dry run ok no-prompt",
             "blocked sandbox", "blocked disagreement", "blocked validation",
             "blocked leakscan", "blocked residue", "blocked other")

    def test_every_line_conforms(self):
        j = ap.journal_load(self.F)
        for line in self.LINES:
            kind = holdout_manifest.resume_reply_kind(line)
            self.assertIsNotNone(kind, line)
            rc, out, _ = self.capture(ap.result_line, self.F, j, line, [])
            self.assertEqual(out, line + "\n")
            blocking = kind in holdout_manifest.RESUME_BLOCKING_KINDS
            self.assertEqual(rc, 3 if blocking else 0, line)
            self.assertEqual(self.journal()["result_line"], line)

    def test_success_needs_a_clean_scrub_in_this_run(self):
        j = ap.journal_load(self.F)
        for residue in (None, ["/x"]):
            with self.assertRaises(KitError):
                self.capture(ap.result_line, self.F, j, "sealed", residue)
        rc, _, _ = self.capture(ap.result_line, self.F, j, "blocked other")
        self.assertEqual(rc, 3)

    def test_synthetic_non_conforming_line(self):
        j = ap.journal_load(self.F)
        for bad in ("sealed, C1 is from repo", "sealed ", "done"):
            with self.assertRaises(KitError):
                self.capture(ap.result_line, self.F, j, bad, [])
        with mock.patch.object(holdout_manifest, "resume_reply_kind",
                               return_value=None):
            with self.assertRaises(KitError):
                self.capture(ap.result_line, self.F, j, "sealed", [])


class TestResidue(PipelineCase):

    def plant_residue(self):
        # Residue is injected the way test_holdout_archive does it: through
        # holdout_archive._default_residue_bases, patched in setUp to temp
        # roots, so scrub never looks at the owner's real home.
        self.assertEqual(holdout_archive._default_residue_bases(), self.bases)
        proj = os.path.join(self.home, ".claude", "projects",
                            "-Users-x--" + holdout_archive.RESIDUE_MARK
                            + "-work")
        os.makedirs(proj)
        with open(os.path.join(proj, "s.jsonl"), "w") as fh:
            fh.write("{}\n")
        return proj

    def assert_blocked_residue(self, out, proj):
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked residue")
        self.assertEqual(holdout_manifest.resume_reply_kind(lines[-1]),
                         "blocked")
        self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS["residue"])
        self.assertIn("PROBLEM: residue: %s — delete it by hand" % proj,
                      lines)
        self.assertEqual(self.journal()["steps"]["scrub"]["status"],
                         "blocked")

    def test_residue_blocks_then_clears(self):
        proj = self.plant_residue()
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        self.assert_blocked_residue(out, proj)
        j = self.journal()
        for step in ap.STEPS[:ap.STEPS.index("scrub")]:
            self.assertEqual(j["steps"][step]["status"], "done", step)
        self.assertTrue(os.path.exists(self.published()))
        archive = holdout_archive.archive_path(self.F)
        sha = holdout_kit.sha256_file(archive)
        self.assertFalse(os.path.exists(os.path.join(self.F, "sealed")))
        shutil.rmtree(proj)
        n = self.mark_calls()
        with mock.patch.object(holdout_archive, "scrub",
                               wraps=holdout_archive.scrub) as spy:
            out = self.run_ok()
        self.assertEqual(spy.call_count, 1)
        self.assertEqual(self.last_line(out), "sealed")
        self.assertEqual(self.since(n), [])
        self.assertEqual(holdout_kit.sha256_file(archive), sha)

    def test_mutant_ignored_residue(self):
        self.plant_residue()
        with mock.patch.object(ap, "_scrub_residue", return_value=[]):
            rc, out, err = self.cli()
        self.assertEqual(rc, 1)
        self.assertIn(ap.RESULT_UNPROVEN_MSG, err)
        self.assertNotEqual(self.last_line(out), "blocked residue")

        def ignore_all(run):
            run.scrub_result = []

        with mock.patch.object(ap, "_scrub_residue", return_value=[]), \
                mock.patch.object(ap, "_step_scrub", side_effect=ignore_all):
            _, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "sealed")

    def interrupted_scrub(self):
        # Same residue hook (_default_residue_bases) as plant_residue; the
        # crash is injected into holdout_archive._prune, after the plaintext
        # files were deleted but before the survivor and residue checks.
        proj = self.plant_residue()
        with mock.patch.object(holdout_archive, "_prune",
                               side_effect=RuntimeError("synthetic crash")):
            with self.assertRaises(RuntimeError):
                self.cli()
        # The deletion ran (no plaintext file is left) but its folders,
        # the survivor checks and the residue check never did.
        self.assertEqual(holdout_kit.walk_regular(
            os.path.join(self.F, "sealed")), [])
        self.assertNotEqual(self.journal()["steps"]["scrub"].get("status"),
                            "done")
        stray = os.path.join(self.F, "work", "left.txt")
        os.makedirs(os.path.dirname(stray), exist_ok=True)
        with open(stray, "w") as fh:
            fh.write("missed\n")
        return proj, stray

    def test_interrupted_deletion_still_checks_everything(self):
        proj, stray = self.interrupted_scrub()
        n = self.mark_calls()
        with mock.patch.object(holdout_archive, "scrub",
                               wraps=holdout_archive.scrub) as spy:
            rc, out, _ = self.cli()
        self.assertEqual(spy.call_count, 1)
        self.assertEqual(rc, 3)
        self.assertFalse(os.path.exists(stray), out)
        self.assert_blocked_residue(out, proj)
        self.assertEqual(self.since(n), [])
        shutil.rmtree(proj)
        with mock.patch.object(holdout_archive, "scrub",
                               wraps=holdout_archive.scrub) as spy:
            out = self.run_ok()
        self.assertEqual(spy.call_count, 1)
        self.assertEqual(self.last_line(out), "sealed")

    def test_mutant_absent_sealed_shortcut(self):
        _, stray = self.interrupted_scrub()
        real = ap._step_scrub

        def shortcut(run):
            sealed = os.path.join(run.h, "sealed")
            if not holdout_kit.walk_regular(sealed) \
                    and ap._archive_verified(run.h):
                run.scrub_result = []
                return None
            return real(run)

        with mock.patch.object(ap, "_step_scrub", side_effect=shortcut):
            _, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "sealed")
        self.assertTrue(os.path.exists(stray))

    def test_mutant_preflight_requiring_sealed(self):
        self.interrupted_scrub()
        with mock.patch.object(ap, "POST_ENCRYPT_LAYOUT", ap.FULL_LAYOUT):
            rc, out, _ = self.cli()
        self.assertEqual(rc, 1)
        self.assertIn(ap.SETUP_MSG, out)

    def test_rerun_with_residue_still_present(self):
        proj = self.plant_residue()
        self.cli()
        with mock.patch.object(holdout_archive, "scrub",
                               wraps=holdout_archive.scrub) as spy:
            rc, out, _ = self.cli()
        self.assertEqual(spy.call_count, 1)
        self.assertEqual(rc, 3)
        self.assert_blocked_residue(out, proj)
        shutil.rmtree(proj)
        self.assertEqual(self.last_line(self.run_ok()), "sealed")

    def test_mutant_trusting_blocked_scrub(self):
        self.plant_residue()
        self.cli()
        real = ap._step_scrub

        def trust(run):
            if ap._status(run.j, "scrub") == "blocked":
                run.scrub_result = []
                return None
            return real(run)

        with mock.patch.object(ap, "_step_scrub", side_effect=trust):
            _, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "sealed")



class TestEncryptAndSealFallback(PipelineCase):

    def test_encrypt_failure_then_resume(self):
        os.environ["FAKE_OPENSSL_FAIL"] = "5"
        rc, out, _ = self.cli()
        self.assertEqual(rc, 3)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked other")
        self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS["encrypt"].replace(
            "<H>", self.F))
        self.assertIn("step encrypt: openssl will ask for the passphrase "
                      "(twice, then once to verify)", lines)
        self.assertEqual(self.journal()["steps"]["encrypt"]["status"],
                         "blocked")
        self.assertFalse(os.path.exists(holdout_archive.archive_path(self.F)))
        self.assertFalse(os.path.exists(os.path.join(self.F, "LEAKSCAN.json")))
        self.assertFalse(os.path.exists(self.published()))
        del os.environ["FAKE_OPENSSL_FAIL"]
        n = self.mark_calls()
        out = self.run_ok()
        self.assertEqual(self.last_line(out), "sealed")
        self.assertEqual(self.p_calls(self.since(n)), [])

    def test_unclassified_seal_blocker(self):
        with mock.patch.object(holdout_seal, "seal_blockers",
                               return_value=["something unclassified"]):
            rc, out, err = self.cli()
        self.assertEqual(rc, 3)
        lines = out.strip().splitlines()
        self.assertEqual(lines[-1], "blocked other")
        self.assertEqual(lines[-2], ap.STOP_INSTRUCTIONS["seal-other"]
                         .replace("<H>", self.F))
        self.assertIn("step seal: refused (see the log inside the holdout "
                      "folder)", lines)
        self.assertNotIn("something unclassified", out + err)
        self.assertEqual(self.journal()["steps"]["seal"]["status"], "blocked")
        self.assertFalse(os.path.exists(holdout_archive.archive_path(self.F)))

    def test_mutant_unclassified_as_disagreement(self):
        with mock.patch.object(holdout_seal, "seal_blockers",
                               return_value=["something unclassified"]), \
                mock.patch.object(ap, "_classify_blocker",
                                  return_value=("disagreement", "C1")):
            _, out, _ = self.cli()
        self.assertEqual(self.last_line(out), "blocked disagreement")


class TestKitAdditions(unittest.TestCase):

    def test_populate_without_crosscheck(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder = setup_folder(os.path.realpath(tmp.name))
        with mock.patch.dict(os.environ, holdout_fixture.kit_env(),
                             clear=True):
            ids = holdout_dryrun.populate(folder, complete_crosscheck=False)
        self.assertEqual(sorted(ids), list(holdout_kit.SLOTS))
        for cid in ids.values():
            self.assertFalse(os.path.exists(os.path.join(
                folder, "sealed", "keys", cid, "xcheck-ledger.json")))
        self.assertFalse(os.path.exists(os.path.join(
            folder, *holdout_seal.WORKSPACES_RELPATH.split("/"))))

    def test_load_retired_is_public(self):
        self.assertIs(holdout_manifest.load_retired,
                      holdout_manifest._load_retired)


if __name__ == "__main__":
    unittest.main()
