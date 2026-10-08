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
        for name in self.EXPORTS:
            self.assertTrue(callable(getattr(holdout_guard, name, None)), name)

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


if __name__ == "__main__":
    unittest.main()
