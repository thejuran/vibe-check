"""Tests for harness_driver_sdk — stdlib only; the Agent SDK is never imported.

The SDK result classes are replaced through the module's `_sdk()` accessor,
so the permission dispatch, the turn-end handling and the structural
no-write rules are all exercised without a live session.
"""

import ast
import asyncio
import collections
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import harness_driver_sdk as d  # noqa: E402
import harness_sandbox  # noqa: E402

SOURCE = (HERE / "harness_driver_sdk.py").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# fakes
# --------------------------------------------------------------------------- #
class FakeAllow:
    def __init__(self, behavior="allow", updated_input=None,
                 updated_permissions=None):
        self.behavior = behavior
        self.updated_input = updated_input


class FakeDeny:
    def __init__(self, behavior="deny", message="", interrupt=False):
        self.behavior = behavior
        self.message = message
        self.interrupt = interrupt


def fake_sdk():
    return types.SimpleNamespace(PermissionResultAllow=FakeAllow,
                                 PermissionResultDeny=FakeDeny)


Decision = collections.namedtuple("Decision", "answers fail")


class FakeCore:
    def __init__(self, card_fail=None, turn=("done", None)):
        self.calls = []
        self.card_fail = card_fail
        self.turn = turn

    def observe_state(self, label):
        self.calls.append(("observe_state", label))

    def collect_evidence(self):
        self.calls.append(("collect_evidence",))
        return "e" * 64

    def on_card(self, input_data, evidence):
        self.calls.append(("on_card", evidence))
        if self.card_fail:
            return Decision({}, self.card_fail)
        return Decision({input_data["questions"][0]["question"]: "Apply all"},
                        None)

    def on_turn_end(self, text):
        self.calls.append(("on_turn_end", text))
        return self.turn


class _Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = os.path.realpath(self._tmp.name)
        self.copy = types.SimpleNamespace(root=os.path.join(base, "ws",
                                                            "repo"))
        self.snapshot = types.SimpleNamespace(
            path=os.path.join(base, "ws", "plugin"))
        self.out = os.path.join(base, "out")
        for p in (self.copy.root, self.snapshot.path, self.out):
            os.makedirs(p)
        self.core = FakeCore()
        self.session = d.Session(self.copy, self.snapshot, self.core,
                                 self.out)
        patcher = mock.patch.object(d, "_sdk", fake_sdk)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.session.close)
        self.addCleanup(self._tmp.cleanup)

    def call(self, tool, data):
        return asyncio.run(self.session.can_use_tool(tool, data, None))

    def harness_lines(self):
        self.session.close()
        with open(os.path.join(self.out, d.TRANSCRIPT_NAME),
                  encoding="utf-8") as fh:
            objs = [json.loads(line) for line in fh]
        return [o for o in objs if o.get("harness") == "can_use_tool"]


# --------------------------------------------------------------------------- #
# structural rules (D-21, lazy import)
# --------------------------------------------------------------------------- #
class TestStructure(unittest.TestCase):
    def test_sdk_import_is_lazy(self):
        tree = ast.parse(SOURCE)
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + [
                    getattr(node, "module", None) or ""]
                self.assertFalse(any("claude_agent_sdk" in n for n in names),
                                 "module-level SDK import")
        self.assertIn("claude_agent_sdk", SOURCE)
        self.assertNotIn("claude_agent_sdk", sys.modules)

    def test_every_open_targets_the_out_dir(self):
        tree = ast.parse(SOURCE)
        opens = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == "open"]
        self.assertTrue(opens)
        for call in opens:
            arg = call.args[0]
            names = {n.id for n in ast.walk(arg) if isinstance(n, ast.Name)}
            attrs = {n.attr for n in ast.walk(arg)
                     if isinstance(n, ast.Attribute)}
            self.assertTrue("out_dir" in names or "out_dir" in attrs,
                            ast.unparse(arg))
        self.assertNotIn("os.fdopen", SOURCE)
        self.assertNotIn("Path(", SOURCE)

    def test_forbidden_modules_and_writers(self):
        tree = ast.parse(SOURCE)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {a.name for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
                imported |= {"%s.%s" % (node.module, a.name)
                             for a in node.names}
        for banned in ("shutil", "harness_seed", "harness_sentinels",
                       "harness_fixture", "harness_verdict",
                       "harness_sandbox.snapshot_plugin",
                       "harness_sandbox.make_workspace"):
            self.assertNotIn(banned, imported)
        attrs = {(n.value.id, n.attr) for n in ast.walk(tree)
                 if isinstance(n, ast.Attribute)
                 and isinstance(n.value, ast.Name)}
        for banned in (("harness_sandbox", "snapshot_plugin"),
                       ("harness_sandbox", "make_workspace"),
                       ("os", "remove"), ("os", "unlink"), ("os", "rename"),
                       ("os", "replace"), ("os", "makedirs"),
                       ("os", "mkdir"), ("subprocess", "run")):
            self.assertNotIn(banned, attrs)


# --------------------------------------------------------------------------- #
# env and plugin identity (Pitfalls 8, 9)
# --------------------------------------------------------------------------- #
class TestEnvAndIdentity(unittest.TestCase):
    def test_claudecode_is_stripped(self):
        env = d.session_env({"CLAUDECODE": "1", "PATH": "/bin", "HOME": "/h"})
        self.assertEqual(env, {"PATH": "/bin", "HOME": "/h",
                               "ENABLE_CLAUDEAI_MCP_SERVERS": "false"})
        env = d.session_env({"ENABLE_CLAUDEAI_MCP_SERVERS": "true"})
        self.assertEqual(env["ENABLE_CLAUDEAI_MCP_SERVERS"], "false")

    def test_session_env_default_reads_os_environ(self):
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1"}):
            self.assertNotIn("CLAUDECODE", d.session_env())

    def test_no_mcp_server_may_load(self):
        d.check_no_mcp_servers({"mcp_servers": []})
        d.check_no_mcp_servers({})
        with self.assertRaises(d.DriverError) as cm:
            d.check_no_mcp_servers({"mcp_servers": [
                {"name": "claude.ai Gmail", "source": "claudeai",
                 "status": "pending"}]})
        self.assertIn("mcp servers loaded", str(cm.exception))

    def test_identity_exactly_one_at_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap = os.path.realpath(tmp)
            d.check_plugin_identity(
                {"plugins": [{"name": "vibe-check", "path": snap}]}, snap)
            d.check_plugin_identity(
                {"plugins": [{"name": "vibe-check", "path": snap + "/"},
                             {"name": "other", "path": "/x"}]}, snap)
            for plugins in (
                    [{"name": "vibe-check", "path": snap},
                     {"name": "vibe-check", "path": "/cache/vibe-check"}],
                    [{"name": "vibe-check", "path": "/cache/vibe-check"}],
                    [],
                    None):
                with self.assertRaises(d.DriverError) as cm:
                    d.check_plugin_identity({"plugins": plugins}, snap)
                self.assertIn("plugin identity", str(cm.exception))


# --------------------------------------------------------------------------- #
# fail-closed refusal
# --------------------------------------------------------------------------- #
class TestFailClosed(_Case):
    def settings(self):
        return harness_sandbox.build_session_settings(
            self.copy.root, self.snapshot.path, self.out)

    def drive(self, settings):
        return d.drive(self.copy, self.snapshot, "/vibe-check:review",
                       self.core, self.out, settings)

    def test_open_settings_are_refused_before_any_sdk_use(self):
        s = self.settings()
        s["sandbox"].pop("failIfUnavailable")
        with mock.patch.object(d, "_sdk", side_effect=AssertionError("sdk")):
            with self.assertRaises(d.DriverError) as cm:
                self.drive(s)
        self.assertIn("settings not fail-closed", str(cm.exception))

    def test_mutant_fail_closed_always_true_removes_the_refusal(self):
        s = self.settings()
        s["sandbox"].pop("failIfUnavailable")
        with mock.patch.object(d.harness_sandbox, "settings_is_fail_closed",
                               lambda _s: True), \
                mock.patch.object(d, "_run_session",
                                  side_effect=RuntimeError("launched")):
            with self.assertRaises(RuntimeError) as cm:
                self.drive(s)
        self.assertEqual(str(cm.exception), "launched")

    def test_options_carry_the_policy(self):
        s = self.settings()
        captured = {}

        class Opts:
            def __init__(self, **kw):
                captured.update(kw)

        sdk = types.SimpleNamespace(ClaudeAgentOptions=Opts,
                                    HookMatcher=lambda **kw: kw)
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1"}):
            d.build_options(sdk, self.session, s, None)
        self.assertEqual(captured["cwd"], self.copy.root)
        self.assertEqual(captured["plugins"],
                         [{"type": "local", "path": self.snapshot.path}])
        self.assertEqual(json.loads(captured["settings"]), s)
        self.assertEqual(captured["setting_sources"], [])
        self.assertEqual(captured["permission_mode"], "default")
        self.assertNotIn("CLAUDECODE", captured["env"])
        self.assertNotIn("sandbox", captured)
        self.assertIs(captured["strict_mcp_config"], True)
        self.assertEqual(captured["mcp_servers"], {})
        self.assertEqual(captured["env"]["ENABLE_CLAUDEAI_MCP_SERVERS"],
                         "false")


# --------------------------------------------------------------------------- #
# can_use_tool dispatch
# --------------------------------------------------------------------------- #
CARD = {"questions": [{"question": "#1 src/clamp.py:13 — x (warning)",
                       "options": [{"label": "Apply all"}]}]}


class TestDispatch(_Case):
    def test_card_observes_state_before_answering(self):
        res = self.call("AskUserQuestion", CARD)
        self.assertIsInstance(res, FakeAllow)
        self.assertEqual(res.updated_input["questions"], CARD["questions"])
        self.assertEqual(res.updated_input["answers"],
                         {CARD["questions"][0]["question"]: "Apply all"})
        kinds = [c[0] for c in self.core.calls]
        self.assertEqual(kinds, ["observe_state", "collect_evidence",
                                 "on_card"])
        self.assertEqual(self.core.calls[0], ("observe_state", "card"))

    def test_card_fail_denies_and_fails_the_run(self):
        self.core.card_fail = "repeat"
        res = self.call("AskUserQuestion", CARD)
        self.assertIsInstance(res, FakeDeny)
        self.assertEqual(res.message, "harness stop: repeat")
        self.assertEqual(self.session.failed_reason, "repeat")

    def test_turn_end_observes_state_before_classifying(self):
        action = self.session.on_result("No changes to review.")
        self.assertEqual(action, ("done", None))
        self.assertEqual(self.core.calls,
                         [("observe_state", "turn_end"),
                          ("on_turn_end", "No changes to review.")])

    def test_key_read_is_a_protected_denial(self):
        key = os.path.join(harness_sandbox.KEYS_DIR, "py-clamp-01.json")
        res = self.call("Read", {"file_path": key})
        self.assertIsInstance(res, FakeDeny)
        self.assertEqual(res.message, "harness containment: protected path")
        self.assertEqual(self.session.protected_denials, 1)
        self.assertEqual(self.session.failed_reason,
                         "containment: session reached a protected path")
        line = self.harness_lines()[-1]
        self.assertEqual(line, {"harness": "can_use_tool", "tool": "Read",
                                "path": key, "command": None,
                                "decision": "deny", "kind": "protected"})

    def test_copy_read_is_allowed_unchanged(self):
        inp = {"file_path": os.path.join(self.copy.root, "src", "clamp.py")}
        res = self.call("Read", inp)
        self.assertIsInstance(res, FakeAllow)
        self.assertEqual(res.updated_input, inp)
        self.assertIsNone(self.session.failed_reason)

    def test_outside_write_is_counted_not_fatal(self):
        inp = {"file_path": self.copy.root + "/../x", "content": "y"}
        res = self.call("Write", inp)
        self.assertIsInstance(res, FakeDeny)
        self.assertEqual(res.message,
                         "harness containment: path outside the disposable "
                         "copy")
        self.assertEqual(self.session.containment_denials, 1)
        self.assertEqual(self.session.protected_denials, 0)
        self.assertIsNone(self.session.failed_reason)

    def test_mcp_call_is_denied_and_fails_the_run(self):
        res = self.call("mcp__claude_ai_Claude_Docs__update",
                        {"payload": {"note": "x"},
                         "ref": {"id": "src/clamp.py", "object": "file"}})
        self.assertIsInstance(res, FakeDeny)
        self.assertEqual(res.message, "harness containment: external tool")
        self.assertEqual(self.session.containment_denials, 1)
        self.assertEqual(self.session.failed_reason,
                         "containment: session reached an external tool")

    def test_bash_is_allowed_and_logged(self):
        res = self.call("Bash", {"command": "git status"})
        self.assertIsInstance(res, FakeAllow)
        line = self.harness_lines()[-1]
        self.assertEqual(line["command"], "git status")
        self.assertIsNone(line["path"])
        self.assertEqual(line["decision"], "allow")

    def test_mutant_path_allowed_always_ok_flips_the_key_read(self):
        key = os.path.join(harness_sandbox.KEYS_DIR, "py-clamp-01.json")
        with mock.patch.object(
                d.harness_sandbox, "path_allowed",
                lambda *a, **k: harness_sandbox.Decision(True, "copy", key)):
            res = self.call("Read", {"file_path": key})
        self.assertIsInstance(res, FakeAllow)
        self.assertEqual(self.session.protected_denials, 0)

    def test_core_exception_is_logged_and_reraised(self):
        def boom(_label):
            raise RuntimeError("state read failed")
        self.core.observe_state = boom
        with self.assertRaises(RuntimeError):
            self.call("AskUserQuestion", CARD)
        self.session.close()
        with open(os.path.join(self.out, d.TRANSCRIPT_NAME),
                  encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("state read failed", text)


# --------------------------------------------------------------------------- #
# transcript serialisation
# --------------------------------------------------------------------------- #
class TestSerialise(unittest.TestCase):
    def test_blocks_keep_ids_and_is_error(self):
        ToolUseBlock = type("ToolUseBlock", (), {})
        ToolResultBlock = type("ToolResultBlock", (), {})
        AssistantMessage = type("AssistantMessage", (), {})
        use = ToolUseBlock()
        use.id, use.name, use.input = "t1", "Read", {"file_path": "/x",
                                                     "limit": 3}
        res = ToolResultBlock()
        res.tool_use_id, res.is_error = "t1", True
        res.content = [{"type": "text", "text": "z" * 5000}]
        msg = AssistantMessage()
        msg.content, msg.model = [use, res], "m"
        obj = d.message_to_dict(msg)
        self.assertEqual(obj["type"], "assistant")
        self.assertEqual(obj["content"][0], {
            "type": "tool_use", "id": "t1", "name": "Read",
            "input": {"file_path": "/x", "limit": 3}})
        self.assertEqual(obj["content"][1]["tool_use_id"], "t1")
        self.assertIs(obj["content"][1]["is_error"], True)
        self.assertEqual(len(obj["content"][1]["content"]),
                         d.RESULT_TEXT_LIMIT)
        events = harness_sandbox.probe_events_from_transcript(
            [json.dumps(obj)], "/c")
        self.assertEqual(len(events), 1)
        self.assertIs(events[0].is_error, True)


if __name__ == "__main__":
    unittest.main()
