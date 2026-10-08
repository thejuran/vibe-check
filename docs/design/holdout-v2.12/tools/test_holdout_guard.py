"""Tests for holdout_guard — the fail-closed PreToolUse deny hook that keeps
tuning sessions (main thread and every subagent) away from the sealed holdout.

Locked here:
  * DENY: every path, glob, symlink, casefold, quote-split, brace and
    recursive-ancestor form that reaches the holdout root, for main-thread and
    subagent payloads, both in-process and through the real `hook` CLI (exit 2,
    fixed stderr reason that never echoes the call).
  * ALLOW: ordinary tuning work — repo reads, commits that say "seal holdout",
    Write/Edit content and Agent prompts that merely NAME the path.
  * Malformed / empty / non-dict input fails CLOSED.
  * Roles: finder/xcheck sessions may read the holdout but not tuning-side
    files; --protect roots are honored for every role.
  * Mutants: disabling the classifier, the glob step, the casefold step, the
    resolution step, the ancestor step or the error verdict flips a verdict.
  * TestImportSet pins the stdlib import set; no production root override.
"""

import ast
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import holdout_guard  # noqa: E402  (sibling module under test)

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
GUARD_PY = os.path.join(TOOLS_DIR, "holdout_guard.py")
REPO_ROOT = os.path.abspath(os.path.join(TOOLS_DIR, "..", "..", "..", ".."))
HOME = os.path.expanduser("~")

# A fake sealed root for the resolution / symlink tests. Its name carries no
# holdout token, so only the resolution test can catch paths under it.
FAKE_BASE = tempfile.mkdtemp(prefix="hg-test-")
FAKE_ROOT = os.path.join(FAKE_BASE, "sealed-root")
os.makedirs(os.path.join(FAKE_ROOT, "keys"))
FAKE_LINK = os.path.join(FAKE_BASE, "link-to-root")
os.symlink(FAKE_ROOT, FAKE_LINK)


def tearDownModule():
    shutil.rmtree(FAKE_BASE, ignore_errors=True)


# Name-token and glob forms: caught without touching the filesystem, so they
# are asserted through the real CLI against the real root as well.
DENY_NAME = (
    ("Read", {"file_path": "~/.vibe-check-holdout/v2.12/sealed/keys/x"}),
    ("Read", {"file_path": HOME + "/.vibe-check-holdout/x"}),
    ("Read", {"file_path": "$HOME/.vibe-check-holdout/x"}),
    ("Read", {"file_path": "${HOME}/.vibe-check-holdout/x"}),
    ("Read", {"file_path": "~/.VIBE-CHECK-HOLDOUT/x"}),
    ("Edit", {"file_path": "~/.vibe-check-holdout/a", "old_string": "a",
              "new_string": "b"}),
    ("Write", {"file_path": "~/.vibe-check-holdout/a", "content": "x"}),
    ("MultiEdit", {"file_path": "~/.vibe-check-holdout/a", "edits": []}),
    ("NotebookEdit", {"notebook_path": "~/.vibe-check-holdout/n.ipynb",
                      "new_source": "x"}),
    ("Grep", {"pattern": "x", "path": "~/.vibe-check-holdout"}),
    ("Glob", {"pattern": "~/.vibe*/**"}),
    ("Bash", {"command": "cat ~/.vibe-check-holdout/v2.12/SEAL.json"}),
    ("Bash", {"command": "cat '.vibe-check-'hold\"out\"/x"}),
    ("Bash", {"command": "cat ~/.vibe-check-hold\\out/x"}),
    ("Bash", {"command": "cat ~/.vibe*/v2.12/x"}),
    ("Bash", {"command": "cat ~/.[v]ibe-check-holdout/x"}),
    ("Bash", {"command": "cat ~/.vibe-check-h?ldout/x"}),
    ("Bash", {"command": "cat ~/.{vibe-check-holdout,foo}/x"}),
    ("Bash", {"command": "du -sh ~/.*"}),
    ("Bash", {"command": "ls ~/.claude/projects/-Users-u--vibe-check-holdout-v2-12/"}),
    ("Bash", {"command": "cat /private/tmp/claude-501/-Users-u--vibe-check-holdout-v2-12/x"}),
    ("WebFetch", {"url": "file:///Users/u/.vibe-check-holdout/x",
                  "prompt": "read"}),
    ("mcp__fs__read", {"request": {"targets": [{"p": ["~/.vibe-check-holdout/x"]}]}}),
    ("Monitor", {"command": "tail -f ~/.vibe-check-holdout/log"}),
)

# Recursive readers rooted at an ancestor of the holdout (no token in the call).
DENY_ANCESTOR = (
    ("Grep", {"pattern": "SEAL", "path": "~"}),
    ("Glob", {"pattern": "**/SEAL.json", "path": "/Users"}),
    ("Bash", {"command": "find ~ -name SEAL.json"}),
    ("Bash", {"command": "grep -r token /Users"}),
    ("Bash", {"command": "rg x $HOME"}),
    ("Bash", {"command": "tar czf /tmp/a.tgz ~"}),
    ("Bash", {"command": "cp -R ~ /tmp/x"}),
)

# Resolution forms against FAKE_ROOT (holdout_guard.HOLDOUT_ROOT patched).
DENY_RESOLVE = (
    ("Read", {"file_path": os.path.join(FAKE_ROOT, "keys", "x")}),
    ("Read", {"file_path": os.path.join(FAKE_LINK, "keys", "x")}),
    ("Edit", {"file_path": os.path.join(FAKE_ROOT, "a"), "old_string": "a",
              "new_string": "b"}),
    ("Bash", {"command": "cat " + os.path.join(FAKE_LINK, "x")}),
    ("Grep", {"pattern": "x", "path": FAKE_BASE}),
)

DENY_MALFORMED_STDIN = (
    "",
    "not json",
    "[]",
    "null",
    json.dumps({"tool_name": None, "tool_input": {"file_path": "a"}}),
    json.dumps({"tool_name": "Read", "tool_input": "a"}),
    json.dumps({"tool_name": "Read"}),
)

DENY = DENY_NAME + DENY_ANCESTOR + DENY_RESOLVE

ALLOW = (
    ("Read", {"file_path": "docs/design/holdout-v2.12/SEAL.json"}),
    ("Read", {"file_path": "docs/design/holdout-v2.12/tools/holdout_guard.py"}),
    ("Bash", {"command": "git commit -m \"seal holdout v2.12\""}),
    ("Bash", {"command": "pytest -q docs/design/holdout-v2.12/tools"}),
    ("Bash", {"command": "ls ~/turingmind-code-review"}),
    ("Bash", {"command": "grep -rn holdout docs/design/holdout-v2.12"}),
    ("Bash", {"command": "ls ~/*/.git"}),
    ("Write", {"file_path": "docs/design/holdout-v2.12/README.md",
               "content": "The sealed folder is ~/.vibe-check-holdout."}),
    ("Edit", {"file_path": "docs/design/holdout-v2.12/README.md",
              "old_string": "~/.vibe-check-holdout/a",
              "new_string": "~/.vibe-check-holdout/b"}),
    ("Agent", {"prompt": "never open ~/.vibe-check-holdout",
               "subagent_type": "general-purpose"}),
    ("Task", {"prompt": "never open ~/.vibe-check-holdout"}),
    ("TodoWrite", {"todos": [{"content": "seal ~/.vibe-check-holdout"}]}),
    ("AskUserQuestion", {"questions": [{"question": "~/.vibe-check-holdout?"}]}),
    ("Skill", {"skill": "x", "args": "~/.vibe-check-holdout"}),
    ("Grep", {"pattern": "vibe-check-holdout", "path": "docs/design"}),
)


def _payload(tool, tool_input, subagent=False):
    data = {"session_id": "s", "hook_event_name": "PreToolUse",
            "tool_name": tool, "tool_input": tool_input, "cwd": REPO_ROOT}
    if subagent:
        data["agent_id"] = "a1"
        data["agent_type"] = "general-purpose"
    return data


def _run_hook(payload, extra_args=()):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run([sys.executable, GUARD_PY, "hook"] + list(extra_args),
                          input=text, capture_output=True, text=True,
                          cwd=REPO_ROOT, timeout=30)
    return proc.returncode, proc.stderr


def _hook_in_process(payload, **kw):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    err = io.StringIO()
    with mock.patch.object(sys, "stderr", err):
        rc = holdout_guard.hook_main(text, **kw)
    return rc, err.getvalue()


def _fake_root():
    return mock.patch.object(holdout_guard, "HOLDOUT_ROOT", FAKE_ROOT)


class TestFixturePremises(unittest.TestCase):
    def test_symlink_resolves_under_fake_root(self):
        real = os.path.realpath(os.path.join(FAKE_LINK, "x"))
        self.assertTrue(real.startswith(os.path.realpath(FAKE_ROOT) + os.sep))

    def test_fake_root_has_no_token(self):
        self.assertNotIn("vibe-check-holdout", FAKE_BASE.casefold())

    def test_resolve_entries_have_no_token(self):
        for tool, ti in DENY_RESOLVE + DENY_ANCESTOR:
            self.assertNotIn("vibe-check-holdout", json.dumps(ti).casefold())


class TestDenyInProcess(unittest.TestCase):
    def test_name_table(self):
        for tool, ti in DENY_NAME:
            with self.subTest(tool=tool, ti=ti):
                deny, reason = holdout_guard.classify(tool, ti)
                self.assertIs(deny, True)
                self.assertEqual(reason, holdout_guard.REASON_HOLDOUT)

    def test_ancestor_table(self):
        for tool, ti in DENY_ANCESTOR:
            with self.subTest(tool=tool, ti=ti):
                self.assertIs(holdout_guard.classify(tool, ti)[0], True)

    def test_resolve_table(self):
        with _fake_root():
            for tool, ti in DENY_RESOLVE:
                with self.subTest(tool=tool, ti=ti):
                    self.assertIs(holdout_guard.classify(tool, ti)[0], True)

    def test_resolve_table_allowed_without_fake_root(self):
        # The resolution entries only deny because of the patched root.
        for tool, ti in DENY_RESOLVE:
            with self.subTest(tool=tool, ti=ti):
                self.assertIs(holdout_guard.classify(tool, ti)[0], False)

    def test_tool_name_none_denies(self):
        self.assertIs(holdout_guard.classify(None, {"file_path": "a"})[0], True)

    def test_tool_input_not_dict_denies(self):
        self.assertIs(holdout_guard.classify("Read", "a")[0], True)
        self.assertIs(holdout_guard.classify("Read", None)[0], True)

    def test_command_not_string_denies(self):
        self.assertIs(holdout_guard.classify("Bash", {"command": ["cat"]})[0],
                      True)

    def test_unknown_role_denies(self):
        self.assertIs(holdout_guard.classify("Read", {"file_path": "a"},
                                             role="nobody")[0], True)

    def test_deep_nesting_fails_closed(self):
        obj = cur = {}
        for _ in range(500):
            cur["k"] = {}
            cur = cur["k"]
        deny, reason = holdout_guard.classify("mcp__x__y", obj)
        self.assertIs(deny, True)
        self.assertEqual(reason, holdout_guard.REASON_INTERNAL)


class TestAllowInProcess(unittest.TestCase):
    def test_allow_table(self):
        for tool, ti in ALLOW:
            with self.subTest(tool=tool, ti=ti):
                self.assertEqual(holdout_guard.classify(tool, ti), (False, ""))


class TestTableSelfChecks(unittest.TestCase):
    def _commands(self, table):
        return [ti.get("command") for tool, ti in table if "command" in ti]

    def test_deny_has_edge_literals(self):
        cmds = self._commands(DENY)
        for literal in ("cat '.vibe-check-'hold\"out\"/x",
                        "cat ~/.vibe-check-hold\\out/x",
                        "cat ~/.{vibe-check-holdout,foo}/x",
                        "cat ~/.vibe*/v2.12/x",
                        "find ~ -name SEAL.json"):
            self.assertIn(literal, cmds)
        paths = [ti.get("file_path") for tool, ti in DENY]
        for literal in ("$HOME/.vibe-check-holdout/x",
                        "${HOME}/.vibe-check-holdout/x",
                        "~/.VIBE-CHECK-HOLDOUT/x"):
            self.assertIn(literal, paths)
        self.assertIn(os.path.join(FAKE_LINK, "keys", "x"), paths)
        self.assertTrue(any(tool.startswith("mcp__") for tool, _ in DENY))

    def test_allow_has_content_and_commit_literals(self):
        self.assertIn("git commit -m \"seal holdout v2.12\"",
                      self._commands(ALLOW))
        contents = [ti.get("content") for tool, ti in ALLOW]
        self.assertTrue(any(c and "~/.vibe-check-holdout" in c
                            for c in contents))


class TestHookSubprocess(unittest.TestCase):
    def test_name_and_ancestor_deny_main_and_subagent(self):
        for tool, ti in DENY_NAME + DENY_ANCESTOR:
            for sub in (False, True):
                with self.subTest(tool=tool, ti=ti, subagent=sub):
                    rc, err = _run_hook(_payload(tool, ti, sub))
                    self.assertEqual(rc, 2)
                    self.assertEqual(err, holdout_guard.REASON_HOLDOUT)

    def test_resolve_deny_via_protect_flag(self):
        for tool, ti in DENY_RESOLVE:
            for sub in (False, True):
                with self.subTest(tool=tool, ti=ti, subagent=sub):
                    rc, err = _run_hook(_payload(tool, ti, sub),
                                        ["--role", "xcheck",
                                         "--protect", FAKE_ROOT])
                    self.assertEqual(rc, 2)
                    self.assertEqual(err, holdout_guard.REASON_PROTECTED)

    def test_allow_table_exits_zero_silently(self):
        for tool, ti in ALLOW:
            for sub in (False, True):
                with self.subTest(tool=tool, ti=ti, subagent=sub):
                    self.assertEqual(_run_hook(_payload(tool, ti, sub)),
                                     (0, ""))

    def test_malformed_stdin_fails_closed(self):
        for text in DENY_MALFORMED_STDIN:
            with self.subTest(text=text):
                rc, err = _run_hook(text)
                self.assertEqual(rc, 2)
                self.assertEqual(err, holdout_guard.REASON_INTERNAL)

    def test_reason_never_echoes_the_call(self):
        rc, err = _run_hook(_payload(
            "Bash", {"command": "cat ~/.vibe-check-holdout/SECRET-NAME"}))
        self.assertEqual(rc, 2)
        self.assertNotIn("SECRET-NAME", err)

    def test_bad_cli_args_exit_two(self):
        proc = subprocess.run([sys.executable, GUARD_PY, "hook", "--role",
                               "bogus"], input="{}", capture_output=True,
                              text=True, timeout=30)
        self.assertEqual(proc.returncode, 2)
        proc = subprocess.run([sys.executable, GUARD_PY], input="",
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 2)


class TestHookInProcess(unittest.TestCase):
    def test_deny_payload_returns_two_with_fixed_reason(self):
        rc, err = _hook_in_process(_payload(
            "Read", {"file_path": "~/.vibe-check-holdout/x"}, True))
        self.assertEqual((rc, err), (2, holdout_guard.REASON_HOLDOUT))

    def test_allow_payload_returns_zero(self):
        self.assertEqual(_hook_in_process(_payload(
            "Read", {"file_path": "docs/design/holdout-v2.12/SEAL.json"})),
            (0, ""))

    def test_malformed_in_process(self):
        for text in DENY_MALFORMED_STDIN:
            with self.subTest(text=text):
                self.assertEqual(_hook_in_process(text)[0], 2)

    def test_none_stdin_fails_closed(self):
        err = io.StringIO()
        with mock.patch.object(sys, "stderr", err):
            self.assertEqual(holdout_guard.hook_main(None), 2)

    def test_protect_roots_reach_hook_main(self):
        payload = _payload("Read", {"file_path": os.path.join(FAKE_ROOT, "k")})
        self.assertEqual(_hook_in_process(payload)[0], 0)
        self.assertEqual(_hook_in_process(
            payload, extra_protect=(FAKE_ROOT,))[0], 2)


class TestRoles(unittest.TestCase):
    def test_finder_may_read_holdout(self):
        # realpath patched so the test never stats the real sealed folder.
        with mock.patch.object(holdout_guard.os.path, "realpath",
                               os.path.abspath):
            self.assertEqual(holdout_guard.classify(
                "Read", {"file_path": "~/.vibe-check-holdout/v2.12/sealed/x"},
                role="finder"), (False, ""))

    def test_finder_denied_repo(self):
        self.assertEqual(holdout_guard.classify(
            "Read", {"file_path": "~/turingmind-code-review/x"},
            role="finder"), (True, holdout_guard.REASON_PROTECTED))

    def test_finder_denied_claude_history(self):
        deny, reason = holdout_guard.classify(
            "Bash", {"command": "cat ~/.claude/history.jsonl"}, role="finder")
        self.assertEqual((deny, reason), (True, holdout_guard.REASON_PROTECTED))

    def test_finder_denied_snapshots_by_resolution(self):
        deny, _ = holdout_guard.classify(
            "Read", {"file_path": HOME + "/./.codex/auth.json"}, role="finder")
        self.assertIs(deny, True)

    def test_xcheck_extra_protect(self):
        tmp = tempfile.mkdtemp(prefix="hg-xc-")
        try:
            sealed = os.path.join(tmp, "sealed")
            os.makedirs(sealed)
            self.assertIs(holdout_guard.classify(
                "Read", {"file_path": os.path.join(sealed, "k")},
                role="xcheck", extra_protect=[sealed])[0], True)
            self.assertEqual(holdout_guard.classify(
                "Read", {"file_path": os.path.join(
                    tmp, "xcheck", "X-1", "base", "a.py")},
                role="xcheck", extra_protect=[sealed]), (False, ""))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_extra_protect_honored_for_tuning(self):
        deny, reason = holdout_guard.classify(
            "Read", {"file_path": os.path.join(FAKE_ROOT, "k")},
            extra_protect=[FAKE_ROOT])
        self.assertEqual((deny, reason), (True, holdout_guard.REASON_PROTECTED))

    def test_roots_injectable(self):
        self.assertIs(holdout_guard.classify(
            "Read", {"file_path": os.path.join(FAKE_ROOT, "k")},
            roots=(FAKE_ROOT,))[0], True)


class TestMutants(unittest.TestCase):
    DENY_READ = _payload("Read", {"file_path": "~/.vibe-check-holdout/x"})

    def test_mutant_classify_forced_allow(self):
        self.assertEqual(_hook_in_process(self.DENY_READ)[0], 2)
        with mock.patch.object(holdout_guard, "classify",
                               lambda *a, **k: (False, "")):
            self.assertEqual(_hook_in_process(self.DENY_READ)[0], 0)

    def test_mutant_glob_step_disabled(self):
        ti = {"command": "cat ~/.vibe*/v2.12/x"}
        self.assertIs(holdout_guard.classify("Bash", ti)[0], True)
        with mock.patch.object(holdout_guard, "_glob_hit",
                               lambda *a, **k: False):
            self.assertIs(holdout_guard.classify("Bash", ti)[0], False)

    def test_mutant_casefold_disabled(self):
        ti = {"file_path": "~/.VIBE-CHECK-HOLDOUT/x"}
        with _fake_root():
            self.assertIs(holdout_guard.classify("Read", ti)[0], True)
            with mock.patch.object(holdout_guard, "_norm", lambda s: s):
                self.assertIs(holdout_guard.classify("Read", ti)[0], False)

    def test_mutant_resolution_disabled(self):
        ti = {"command": "cat " + os.path.join(FAKE_LINK, "x")}
        with _fake_root():
            self.assertIs(holdout_guard.classify("Bash", ti)[0], True)
            with mock.patch.object(holdout_guard, "_resolves_under",
                                   lambda *a, **k: False):
                self.assertIs(holdout_guard.classify("Bash", ti)[0], False)

    def test_mutant_ancestor_disabled(self):
        ti = {"command": "find ~ -name x"}
        self.assertIs(holdout_guard.classify("Bash", ti)[0], True)
        with mock.patch.object(holdout_guard, "_ancestor_recursion",
                               lambda *a, **k: False):
            self.assertIs(holdout_guard.classify("Bash", ti)[0], False)

    def test_mutant_error_verdict_allows(self):
        def boom(*a, **k):
            raise RuntimeError("x")
        allow = lambda: (False, "")  # noqa: E731
        self.assertNotEqual(holdout_guard._guard_error_verdict(), allow())
        payload = _payload("Read", {"file_path": "docs/x"})
        with mock.patch.object(holdout_guard, "classify", boom):
            self.assertEqual(_hook_in_process(payload)[0], 2)
            with mock.patch.object(holdout_guard, "_guard_error_verdict",
                                   allow):
                self.assertEqual(_hook_in_process(payload)[0], 0)

    def test_classify_wrapper_catches_internal_errors(self):
        def boom(*a, **k):
            raise RuntimeError("x")
        with mock.patch.object(holdout_guard, "_classify", boom):
            self.assertEqual(holdout_guard.classify("Read", {"file_path": "a"}),
                             (True, holdout_guard.REASON_INTERNAL))


class TestImportSet(unittest.TestCase):
    ALLOWED = {"argparse", "fnmatch", "json", "os", "re", "sys", "unicodedata"}
    FORBIDDEN = {"subprocess", "shutil", "socket"}
    EXPORTS = ("classify", "hook_main", "run", "install_into", "uninstall_from",
               "check_install", "settings_problems")

    def _source(self):
        with open(GUARD_PY, "r", encoding="utf-8") as fh:
            return fh.read()

    def _imported(self):
        imported = set()
        for node in ast.walk(ast.parse(self._source())):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        return imported

    def test_import_set_subset_of_allowed(self):
        imported = self._imported()
        self.assertTrue(imported.issubset(self.ALLOWED),
                        str(imported - self.ALLOWED))

    def test_no_forbidden_import(self):
        self.assertFalse(self._imported() & self.FORBIDDEN)

    def test_exports_the_contracted_names(self):
        for name in self.EXPORTS + ("HOOK_ENTRY", "SESSION_ENTRY"):
            self.assertTrue(callable(getattr(holdout_guard, name, None)), name)

    def test_exports_the_contracted_constants(self):
        self.assertEqual(holdout_guard.DENY_RULES, [
            "Read(~/.vibe-check-holdout)", "Read(~/.vibe-check-holdout/**)",
            "Edit(~/.vibe-check-holdout/**)",
            "Read(~/.claude/projects/*vibe-check-holdout*/**)"])
        for name in ("REASON_HOLDOUT", "REASON_INTERNAL", "REASON_PROTECTED"):
            value = getattr(holdout_guard, name)
            self.assertTrue(value.startswith("Blocked: ") and
                            value.endswith("\n"), name)

    def test_no_root_override(self):
        src = self._source()
        self.assertNotIn("HOLDOUT_ROOT_OVERRIDE", src)
        self.assertNotIn("environ", src)

    def test_classifier_call_graph_reads_no_env(self):
        names = {"classify", "_classify", "_resolves_under",
                 "_ancestor_recursion", "_glob_hit", "_name_hit"}
        tree = ast.parse(self._source())
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in names:
                found.add(node.name)
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Attribute):
                        self.assertNotIn("environ", sub.attr, node.name)
                    if isinstance(sub, ast.Name):
                        self.assertNotIn("environ", sub.id, node.name)
        self.assertEqual(found, names)

    def test_docstring_names_residuals(self):
        doc = ast.get_docstring(ast.parse(self._source())) or ""
        self.assertIn("Residuals", doc)
        self.assertIn("barrier, not proof", doc)



# --------------------------------------------------------------------------- #
# install / uninstall / settings contract / check-install / CLI
# --------------------------------------------------------------------------- #

SCRIPT = GUARD_PY
LINT_HOOK = {"matcher": "Bash",
             "hooks": [{"type": "command", "command": "/x/lint-bash.sh"}]}
START_HOOK = {"hooks": [{"type": "command", "command": "/x/session-start.sh"}]}


def _user_shaped():
    """Shaped like the owner's user settings (fake values, no secrets)."""
    return {
        "env": {"FAKE_FLAG": "1"},
        "permissions": {"allow": ["Bash(ls:*)", "Read(/tmp/**)", "Skill(x)"],
                        "defaultMode": "default"},
        "hooks": {"PreToolUse": [LINT_HOOK], "SessionStart": [START_HOOK]},
        "enabledPlugins": {"vibe-check@thejuran": True},
        "model": "opus",
    }


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def _read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


class _TmpCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hg-inst-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, ".claude", "settings.json")


class TestInstall(_TmpCase):
    def test_install_into_user_shaped_file(self):
        original = _user_shaped()
        _write_json(self.path, original)
        self.assertEqual(holdout_guard.install_into(self.path, SCRIPT),
                         "installed")
        d = _read_json(self.path)
        self.assertEqual(d["hooks"]["PreToolUse"],
                         [LINT_HOOK, holdout_guard.HOOK_ENTRY(SCRIPT)])
        self.assertEqual(d["hooks"]["SessionStart"],
                         [START_HOOK,
                          holdout_guard.SESSION_ENTRY(SCRIPT, self.path)])
        self.assertEqual(d["permissions"]["deny"], holdout_guard.DENY_RULES)
        self.assertEqual(d["permissions"]["allow"],
                         original["permissions"]["allow"])
        self.assertEqual(d["permissions"]["defaultMode"], "default")
        for key in ("env", "enabledPlugins", "model"):
            self.assertEqual(d[key], original[key], key)
        self.assertEqual(set(d), set(original))
        self.assertTrue(_read_bytes(self.path).endswith(b"\n"))

    def test_hook_entry_shape(self):
        self.assertEqual(holdout_guard.HOOK_ENTRY(SCRIPT), {
            "matcher": "*",
            "hooks": [{"type": "command", "command": "python3",
                       "args": [SCRIPT, "hook"], "timeout": 10}]})
        entry = holdout_guard.SESSION_ENTRY(SCRIPT, self.path)
        self.assertNotIn("matcher", entry)
        self.assertEqual(entry["hooks"][0]["args"],
                         [SCRIPT, "check-install", "--quiet-ok",
                          "--settings", self.path])

    def test_existing_deny_kept_first(self):
        data = _user_shaped()
        data["permissions"]["deny"] = ["Bash(rm -rf:*)",
                                       holdout_guard.DENY_RULES[1]]
        _write_json(self.path, data)
        holdout_guard.install_into(self.path, SCRIPT)
        deny = _read_json(self.path)["permissions"]["deny"]
        self.assertEqual(deny[:2], ["Bash(rm -rf:*)",
                                    holdout_guard.DENY_RULES[1]])
        self.assertEqual(sorted(deny[2:]),
                         sorted(r for r in holdout_guard.DENY_RULES
                                if r != holdout_guard.DENY_RULES[1]))

    def test_second_install_is_byte_identical(self):
        _write_json(self.path, _user_shaped())
        holdout_guard.install_into(self.path, SCRIPT)
        before = _read_bytes(self.path)
        self.assertEqual(holdout_guard.install_into(self.path, SCRIPT),
                         "already-installed")
        self.assertEqual(_read_bytes(self.path), before)

    def test_repo_shape_gets_hooks_and_deny(self):
        repo = {"permissions": {"allow": ["Skill(gsd:resume-work)"]}}
        _write_json(self.path, repo)
        holdout_guard.install_into(self.path, SCRIPT)
        d = _read_json(self.path)
        self.assertEqual(d["permissions"]["allow"], ["Skill(gsd:resume-work)"])
        self.assertEqual(d["permissions"]["deny"], holdout_guard.DENY_RULES)
        self.assertEqual(d["hooks"]["PreToolUse"],
                         [holdout_guard.HOOK_ENTRY(SCRIPT)])

    def test_missing_file_is_created(self):
        self.assertFalse(os.path.exists(self.path))
        self.assertEqual(holdout_guard.install_into(self.path, SCRIPT),
                         "installed")
        d = _read_json(self.path)
        self.assertEqual(set(d), {"hooks", "permissions"})
        self.assertEqual(d["permissions"], {"deny": holdout_guard.DENY_RULES})
        self.assertFalse(os.path.exists(self.path + ".pre-holdout.bak"))

    def test_stale_entry_from_other_clone_is_replaced(self):
        data = _user_shaped()
        stale = holdout_guard.HOOK_ENTRY("/old/clone/docs/holdout_guard.py")
        data["hooks"]["PreToolUse"].append(stale)
        _write_json(self.path, data)
        holdout_guard.install_into(self.path, SCRIPT)
        pre = _read_json(self.path)["hooks"]["PreToolUse"]
        self.assertEqual(pre, [LINT_HOOK, holdout_guard.HOOK_ENTRY(SCRIPT)])

    def test_atomic_when_replace_fails(self):
        _write_json(self.path, _user_shaped())
        before = _read_bytes(self.path)

        def fail(*a, **k):
            raise OSError("disk full")
        with mock.patch.object(holdout_guard.os, "replace", fail):
            with self.assertRaises(holdout_guard.GuardError):
                holdout_guard.install_into(self.path, SCRIPT)
        self.assertEqual(_read_bytes(self.path), before)
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_backup_written_once(self):
        _write_json(self.path, _user_shaped())
        original = _read_bytes(self.path)
        holdout_guard.install_into(self.path, SCRIPT)
        bak = self.path + ".pre-holdout.bak"
        self.assertEqual(_read_bytes(bak), original)
        holdout_guard.uninstall_from(self.path, SCRIPT)
        d = _read_json(self.path)
        d["model"] = "changed"
        _write_json(self.path, d)
        holdout_guard.install_into(self.path, SCRIPT)
        self.assertEqual(_read_bytes(bak), original)

    def test_unreadable_settings_refused_and_untouched(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        with self.assertRaises(holdout_guard.GuardError):
            holdout_guard.install_into(self.path, SCRIPT)
        self.assertEqual(_read_bytes(self.path), b"{not json")

    def test_non_dict_hooks_refused(self):
        _write_json(self.path, {"hooks": ["x"]})
        with self.assertRaises(holdout_guard.GuardError):
            holdout_guard.install_into(self.path, SCRIPT)

    def test_mutant_merge_dropping_user_hook(self):
        _write_json(self.path, _user_shaped())
        holdout_guard.install_into(self.path, SCRIPT)
        self.assertIn(LINT_HOOK, _read_json(self.path)["hooks"]["PreToolUse"])
        _write_json(self.path, _user_shaped())
        with mock.patch.object(holdout_guard, "_merge_entry",
                               lambda groups, entry, kind: [entry]):
            holdout_guard.install_into(self.path, SCRIPT)
        self.assertNotIn(LINT_HOOK,
                         _read_json(self.path)["hooks"]["PreToolUse"])


class TestUninstall(_TmpCase):
    def test_removes_only_ours(self):
        original = _user_shaped()
        original["permissions"]["deny"] = ["Bash(rm -rf:*)"]
        _write_json(self.path, original)
        holdout_guard.install_into(self.path, SCRIPT)
        self.assertEqual(holdout_guard.uninstall_from(self.path, SCRIPT),
                         "removed")
        self.assertEqual(_read_json(self.path), original)

    def test_second_uninstall_not_present(self):
        _write_json(self.path, _user_shaped())
        holdout_guard.install_into(self.path, SCRIPT)
        holdout_guard.uninstall_from(self.path, SCRIPT)
        before = _read_bytes(self.path)
        self.assertEqual(holdout_guard.uninstall_from(self.path, SCRIPT),
                         "not-present")
        self.assertEqual(_read_bytes(self.path), before)

    def test_missing_file_not_present(self):
        self.assertEqual(holdout_guard.uninstall_from(self.path, SCRIPT),
                         "not-present")
        self.assertFalse(os.path.exists(self.path))

    def test_empty_lists_removed_other_hook_keys_kept(self):
        post = {"matcher": "Edit", "hooks": [{"type": "command",
                                               "command": "/x/fmt.sh"}]}
        original = {"hooks": {"PostToolUse": [post]},
                    "permissions": {"allow": ["Skill(x)"]}}
        _write_json(self.path, original)
        holdout_guard.install_into(self.path, SCRIPT)
        holdout_guard.uninstall_from(self.path, SCRIPT)
        self.assertEqual(_read_json(self.path), original)

    def test_entry_for_other_script_survives(self):
        data = _user_shaped()
        other = holdout_guard.HOOK_ENTRY("/other/holdout_guard.py")
        data["hooks"]["PreToolUse"].append(other)
        _write_json(self.path, data)
        self.assertEqual(holdout_guard.uninstall_from(self.path, SCRIPT),
                         "not-present")
        self.assertIn(other, _read_json(self.path)["hooks"]["PreToolUse"])


class TestSettingsProblems(_TmpCase):
    def _text(self):
        _write_json(self.path, _user_shaped())
        holdout_guard.install_into(self.path, SCRIPT)
        with open(self.path, "r", encoding="utf-8") as fh:
            return fh.read()

    def _assert_reports(self, mutated, problem):
        text = self._text()
        self.assertNotEqual(mutated, text)
        self.assertEqual(holdout_guard.settings_problems(text, SCRIPT), [])
        self.assertIn(problem, holdout_guard.settings_problems(mutated, SCRIPT))

    def _json_mutant(self, fn):
        d = json.loads(self._text())
        fn(d)
        return json.dumps(d, indent=2) + "\n"

    def test_correct_file_has_no_problems(self):
        self.assertEqual(holdout_guard.settings_problems(self._text(), SCRIPT),
                         [])

    def test_static_mutant_hook_missing(self):
        mutated = self._json_mutant(
            lambda d: d["hooks"]["PreToolUse"].pop())
        self._assert_reports(mutated, "PreToolUse hook missing")

    def test_static_mutant_matcher(self):
        mutated = self._text().replace('"matcher": "*"', '"matcher": "Bash"')
        self._assert_reports(mutated, "matcher is not *")

    def test_static_mutant_command(self):
        text = self._text()
        mutated = text.replace('"command": "python3"', '"command": "python"',
                               1)
        self._assert_reports(mutated, "hook command is not python3")

    def test_static_mutant_script_path(self):
        mutated = self._text().replace(
            json.dumps(SCRIPT), json.dumps("/old/clone/holdout_guard.py"), 1)
        self._assert_reports(mutated, "hook path is not " + SCRIPT)

    def test_static_mutant_hook_arg(self):
        mutated = self._text().replace('"hook"', '"nohook"', 1)
        self._assert_reports(mutated, "hook arg is not 'hook'")

    def test_static_mutant_timeout_too_long(self):
        mutated = self._text().replace('"timeout": 10', '"timeout": 30', 1)
        self._assert_reports(mutated, "hook timeout missing or > 10")

    def test_static_mutant_timeout_missing(self):
        mutated = self._json_mutant(
            lambda d: d["hooks"]["PreToolUse"][1]["hooks"][0].pop("timeout"))
        self._assert_reports(mutated, "hook timeout missing or > 10")

    def test_static_mutant_each_deny_rule(self):
        for rule in holdout_guard.DENY_RULES:
            with self.subTest(rule=rule):
                mutated = self._json_mutant(
                    lambda d: d["permissions"]["deny"].remove(rule))
                self._assert_reports(mutated, "deny rule missing: " + rule)

    def test_static_mutant_session_start(self):
        mutated = self._text().replace('"check-install"', '"check-x"', 1)
        self._assert_reports(mutated, "SessionStart check-install missing")

    def test_static_mutant_unreadable(self):
        text = self._text()
        self._assert_reports(text[:-5], "settings JSON unreadable")

    def test_non_dict_json_unreadable(self):
        self.assertEqual(holdout_guard.settings_problems("[]", SCRIPT),
                         ["settings JSON unreadable"])


class TestCheckInstall(_TmpCase):
    def _installed(self, script=SCRIPT):
        _write_json(self.path, _user_shaped())
        holdout_guard.install_into(self.path, script)
        return self.path

    def test_good_install_has_no_problems(self):
        self.assertEqual(holdout_guard.check_install([self._installed()],
                                                     SCRIPT), [])

    def test_settings_problem_names_the_file(self):
        path = self._installed()
        d = _read_json(path)
        d["hooks"]["PreToolUse"][1]["matcher"] = "Bash"
        _write_json(path, d)
        problems = holdout_guard.check_install([path], SCRIPT)
        self.assertEqual(problems, ["matcher is not * (in %s)" % path])

    def test_missing_settings_file(self):
        missing = os.path.join(self.tmp, "nope.json")
        self.assertIn("settings file missing: " + missing,
                      holdout_guard.check_install([missing], SCRIPT))

    def test_script_missing(self):
        fake = os.path.join(self.tmp, "gone", "holdout_guard.py")
        path = self._installed(fake)
        self.assertEqual(holdout_guard.check_install([path], fake),
                         ["script missing: " + fake])

    def test_python3_not_on_path(self):
        path = self._installed()
        empty = os.path.join(self.tmp, "emptybin")
        os.makedirs(empty)
        self.assertEqual(holdout_guard.check_install([path], SCRIPT), [])
        with mock.patch.object(holdout_guard.os, "get_exec_path",
                               lambda *a: [empty]):
            self.assertEqual(holdout_guard.check_install([path], SCRIPT),
                             ["python3 not on PATH"])

    def test_mutant_live_probe(self):
        path = self._installed()
        self.assertEqual(holdout_guard.check_install([path], SCRIPT), [])
        with mock.patch.object(holdout_guard, "hook_main",
                               lambda *a, **k: 0):
            self.assertEqual(holdout_guard.check_install([path], SCRIPT),
                             ["live probe did not deny"])

    def test_probe_prints_nothing(self):
        path = self._installed()
        err = io.StringIO()
        with mock.patch.object(sys, "stderr", err):
            holdout_guard.check_install([path], SCRIPT)
        self.assertEqual(err.getvalue(), "")


class TestCli(_TmpCase):
    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdout", out), \
                mock.patch.object(sys, "stderr", err):
            rc = holdout_guard.run(argv)
        return rc, out.getvalue(), err.getvalue()

    def _repo_settings(self):
        return os.path.join(self.tmp, ".claude", "settings.local.json")

    def test_install_repo_then_already(self):
        rc, out, _ = self._run(["install", "--repo", self.tmp])
        self.assertEqual((rc, out), (0, "Installed the holdout guard into %s\n"
                                     % self._repo_settings()))
        rc, out, _ = self._run(["install", "--repo", self.tmp])
        self.assertEqual((rc, out), (0, "Already installed in %s\n"
                                     % self._repo_settings()))
        d = _read_json(self._repo_settings())
        self.assertEqual(d["hooks"]["PreToolUse"][0]["matcher"], "*")
        self.assertEqual(len(d["permissions"]["deny"]), 4)
        self.assertEqual(d["hooks"]["SessionStart"][0]["hooks"][0]["args"][-1],
                         self._repo_settings())

    def test_install_repo_via_subprocess(self):
        proc = subprocess.run([sys.executable, GUARD_PY, "install", "--repo",
                               self.tmp], capture_output=True, text=True,
                              timeout=30)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "Installed the holdout guard into %s\n"
                         % self._repo_settings())

    def test_check_install_ok_and_quiet(self):
        self._run(["install", "--repo", self.tmp])
        rc, out, _ = self._run(["check-install", "--settings",
                                self._repo_settings()])
        self.assertEqual((rc, out), (0, "OK: holdout guard installed and live "
                                     "(1 settings file(s))\n"))
        rc, out, err = self._run(["check-install", "--quiet-ok", "--settings",
                                  self._repo_settings()])
        self.assertEqual((rc, out, err), (0, "", ""))

    def test_check_install_problem_lines(self):
        self._run(["install", "--repo", self.tmp])
        d = _read_json(self._repo_settings())
        d["hooks"]["PreToolUse"][0]["matcher"] = "Bash"
        _write_json(self._repo_settings(), d)
        rc, out, _ = self._run(["check-install", "--settings",
                                self._repo_settings()])
        self.assertEqual(rc, 1)
        self.assertEqual(out, "PROBLEM: matcher is not * (in %s)\n"
                         % self._repo_settings())

    def test_quiet_ok_problems_also_on_stderr(self):
        rc, out, err = self._run(["check-install", "--quiet-ok", "--settings",
                                  self._repo_settings()])
        self.assertEqual(rc, 1)
        self.assertIn("PROBLEM: settings file missing", out)
        self.assertIn("PROBLEM: settings file missing", err)

    def test_uninstall_then_check_reports_missing_hook(self):
        self._run(["install", "--repo", self.tmp])
        rc, out, _ = self._run(["uninstall", "--repo", self.tmp])
        self.assertEqual((rc, out), (0, "Removed the holdout guard from %s\n"
                                     % self._repo_settings()))
        rc, out, _ = self._run(["check-install", "--settings",
                                self._repo_settings()])
        self.assertEqual(rc, 1)
        self.assertIn("PROBLEM: PreToolUse hook missing (in %s)"
                      % self._repo_settings(), out)

    def test_uninstall_not_present_line(self):
        rc, out, _ = self._run(["uninstall", "--repo", self.tmp])
        self.assertEqual((rc, out), (0, "Not installed in %s\n"
                                     % self._repo_settings()))

    def test_install_user_uses_patched_home(self):
        home = os.path.join(self.tmp, "home")
        real = os.path.expanduser

        def fake(p):
            return home + p[1:] if p.startswith("~") else real(p)
        with mock.patch.object(holdout_guard.os.path, "expanduser", fake):
            rc, out, _ = self._run(["install", "--user"])
        target = os.path.join(home, ".claude", "settings.json")
        self.assertEqual((rc, out), (0, "Installed the holdout guard into %s\n"
                                     % target))
        self.assertEqual(_read_json(target)["hooks"]["SessionStart"][0]
                         ["hooks"][0]["args"][-1], target)

    def test_install_unreadable_reports_problem(self):
        path = self._repo_settings()
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{bad")
        rc, out, err = self._run(["install", "--repo", self.tmp])
        self.assertEqual(rc, 1)
        self.assertEqual(err, "PROBLEM: settings JSON unreadable\n")

    def test_default_check_paths(self):
        home = os.path.join(self.tmp, "home")
        real = os.path.expanduser

        def fake(p):
            return home + p[1:] if p.startswith("~") else real(p)
        with mock.patch.object(holdout_guard.os.path, "expanduser", fake):
            paths = holdout_guard._default_settings_paths(SCRIPT)
        self.assertEqual(paths, [
            os.path.join(REPO_ROOT, ".claude", "settings.local.json"),
            os.path.join(home, ".claude", "settings.json")])

    def test_install_requires_a_target(self):
        self.assertEqual(self._run(["install"])[0], 2)
        self.assertEqual(self._run(["install", "--user", "--repo", "x"])[0], 2)

if __name__ == "__main__":
    unittest.main()
