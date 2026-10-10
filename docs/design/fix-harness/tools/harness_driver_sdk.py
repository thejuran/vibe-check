"""harness_driver_sdk.py — drive one `/vibe-check:review` session through the
Claude Agent SDK under the harness containment policy.

This is the only module that imports `claude_agent_sdk`, and it does so
lazily inside `_sdk()`, so every other harness module (and this one) imports
without the SDK installed.

What the driver does:

* Refuses to launch unless `harness_sandbox.settings_is_fail_closed(settings)`
  holds. The whole sandbox object travels inside the inline flag-layer
  `settings` JSON; `options.sandbox` is never set (its type has no
  `failIfUnavailable`).
* Loads the plugin snapshot by local path with `setting_sources=[]`, so the
  installed plugin cache, user settings and global instructions stay out, and
  asserts that the init message lists exactly one `vibe-check` at the
  snapshot path.
* Answers every AskUserQuestion through the injected `core`: it first asks
  the core to observe the plugin's state (read-only), then hands the card to
  `core.on_card`. A core failure denies the card and fails the run.
* Bounds every other tool call with `harness_sandbox.path_allowed`. A
  protected path is denied and fails the run; a path outside the copy is
  denied and counted. Bash is allowed here: the OS sandbox enforces it.
* After every turn asks the core to observe the state again and to classify
  the turn end; an owner command the core returns is sent as the next query.
* Logs every SDK message and every permission decision to
  `<out_dir>/transcript.jsonl`, with tool_use ids/inputs and tool_result
  ids/is_error preserved.

The driver never writes anywhere but `out_dir`: it opens no other file, and
it imports none of the modules that build, seed or plant the copy.
"""

import asyncio
import collections
import hashlib
import json
import os
import time

import harness_sandbox

TRANSCRIPT_NAME = "transcript.jsonl"
RESULT_TEXT_LIMIT = 4096
STDERR_TAIL = 40
DEFAULT_TIMEOUT_S = 3600
MAX_OWNER_COMMANDS = 3

DENY_PROTECTED = "harness containment: protected path"
DENY_OUTSIDE = "harness containment: path outside the disposable copy"
DENY_EXTERNAL = "harness containment: external tool"
FAIL_PROTECTED = "containment: session reached a protected path"
FAIL_EXTERNAL = "containment: session reached an external tool"
HARNESS_STOP = "harness stop: "

DriveResult = collections.namedtuple(
    "DriveResult",
    "init owner_commands containment_denials protected_denials "
    "failed_reason transcript_sha256 cli_version model")


class DriverError(RuntimeError):
    """The session could not be run as specified."""


def _sdk():
    """The SDK names the driver uses (lazy import; tests inject fakes)."""
    import claude_agent_sdk
    from claude_agent_sdk import types as sdk_types
    return collections.namedtuple("Sdk", (
        "ClaudeSDKClient ClaudeAgentOptions PermissionResultAllow "
        "PermissionResultDeny HookMatcher SystemMessage ResultMessage "
        "version"))(
        claude_agent_sdk.ClaudeSDKClient, claude_agent_sdk.ClaudeAgentOptions,
        sdk_types.PermissionResultAllow, sdk_types.PermissionResultDeny,
        sdk_types.HookMatcher, sdk_types.SystemMessage,
        sdk_types.ResultMessage, claude_agent_sdk.__version__)


def session_env(environ=None):
    """The session's environment: the parent's, minus `CLAUDECODE`, with the
    owner's claude.ai account MCP connectors switched off."""
    env = dict(os.environ if environ is None else environ)
    env.pop("CLAUDECODE", None)
    env["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"
    return env


def check_no_mcp_servers(init_data):
    """Raise when the session loaded any MCP server (account connectors
    included): MCP tools run outside the OS sandbox."""
    servers = init_data.get("mcp_servers") if isinstance(init_data, dict) \
        else None
    if servers:
        raise DriverError("mcp servers loaded: %r" % [
            s.get("name") if isinstance(s, dict) else s for s in servers])


def check_plugin_identity(init_data, snapshot_path):
    """Raise unless exactly one `vibe-check` plugin is loaded, from the
    snapshot path."""
    plugins = init_data.get("plugins") if isinstance(init_data, dict) else None
    if not isinstance(plugins, list):
        raise DriverError("plugin identity: init message lists no plugins")
    hits = [p for p in plugins if isinstance(p, dict)
            and p.get("name") == "vibe-check"]
    want = os.path.realpath(snapshot_path)
    if len(hits) != 1 or not isinstance(hits[0].get("path"), str) \
            or os.path.realpath(hits[0]["path"]) != want:
        raise DriverError("plugin identity: expected exactly one vibe-check "
                          "at %s, init lists %r" % (want, plugins))


# --------------------------------------------------------------------------- #
# transcript serialisation
# --------------------------------------------------------------------------- #
def _result_text(content):
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n".join(
            item["text"] if isinstance(item, dict)
            and isinstance(item.get("text"), str) else
            (item if isinstance(item, str) else "")
            for item in content)
    else:
        text = ""
    return text[:RESULT_TEXT_LIMIT]


def _block_to_dict(block):
    kind = type(block).__name__
    if kind == "ToolUseBlock":
        return {"type": "tool_use", "id": block.id, "name": block.name,
                "input": block.input}
    if kind == "ToolResultBlock":
        return {"type": "tool_result", "tool_use_id": block.tool_use_id,
                "is_error": block.is_error,
                "content": _result_text(block.content)}
    if kind == "TextBlock":
        return {"type": "text", "text": block.text}
    if kind == "ThinkingBlock":
        return {"type": "thinking"}
    if isinstance(block, dict):
        return block
    return {"type": kind}


def message_to_dict(msg):
    """One transcript line for an SDK message; content blocks as dicts."""
    kind = type(msg).__name__
    obj = {"type": {"AssistantMessage": "assistant", "UserMessage": "user",
                    "SystemMessage": "system",
                    "ResultMessage": "result"}.get(kind, kind)}
    content = getattr(msg, "content", None)
    if isinstance(content, list):
        obj["content"] = [_block_to_dict(b) for b in content]
    elif isinstance(content, str):
        obj["content"] = content
    for field in ("model", "parent_tool_use_id", "subtype", "is_error",
                  "num_turns", "result", "stop_reason", "terminal_reason",
                  "permission_denials", "errors"):
        if hasattr(msg, field):
            obj[field] = getattr(msg, field)
    if kind == "SystemMessage":
        obj["data"] = getattr(msg, "data", None)
    return obj


# --------------------------------------------------------------------------- #
# the session
# --------------------------------------------------------------------------- #
class Session:
    """Permission callback, transcript and counters for one drive."""

    def __init__(self, copy, snapshot, core, out_dir):
        self.copy = copy
        self.snapshot = snapshot
        self.core = core
        self.out_dir = out_dir
        self.protected_roots = harness_sandbox.protected_roots(out_dir)
        self.containment_denials = 0
        self.protected_denials = 0
        self.owner_commands = 0
        self.failed_reason = None
        self.init = None
        self._fh = open(os.path.join(self.out_dir, TRANSCRIPT_NAME), "a",
                        encoding="utf-8")

    def log(self, obj):
        self._fh.write(json.dumps(obj, sort_keys=True, default=str) + "\n")
        self._fh.flush()

    def close(self):
        if not self._fh.closed:
            self._fh.close()

    def fail(self, reason):
        if self.failed_reason is None:
            self.failed_reason = reason

    def _decision_line(self, tool_name, input_data, decision, verdict):
        command = input_data.get("command") if tool_name == "Bash" \
            and isinstance(input_data, dict) else None
        self.log({"harness": "can_use_tool", "tool": tool_name,
                  "path": decision.path, "command": command,
                  "decision": verdict, "kind": decision.kind})

    async def can_use_tool(self, tool_name, input_data, context):
        sdk = _sdk()
        try:
            if tool_name == "AskUserQuestion":
                return self._card(sdk, input_data)
            return self._tool(sdk, tool_name, input_data)
        except Exception as exc:
            self.log({"harness": "error", "where": "can_use_tool",
                      "tool": tool_name, "error": repr(exc)})
            raise

    def _card(self, sdk, input_data):
        self.core.observe_state("card")
        evidence = self.core.collect_evidence()
        decision = self.core.on_card(input_data, evidence=evidence)
        self.log({"harness": "card", "answers": decision.answers,
                  "fail": decision.fail})
        if decision.fail:
            self.fail(decision.fail)
            return sdk.PermissionResultDeny(message=HARNESS_STOP
                                            + decision.fail, interrupt=True)
        return sdk.PermissionResultAllow(updated_input={
            "questions": input_data["questions"],
            "answers": decision.answers})

    def _tool(self, sdk, tool_name, input_data):
        decision = harness_sandbox.path_allowed(
            tool_name, input_data, self.copy.root, self.snapshot.path,
            self.protected_roots)
        if decision.ok:
            self._decision_line(tool_name, input_data, decision, "allow")
            return sdk.PermissionResultAllow(updated_input=input_data)
        self._decision_line(tool_name, input_data, decision, "deny")
        if decision.kind == "protected":
            self.protected_denials += 1
            self.fail(FAIL_PROTECTED)
            return sdk.PermissionResultDeny(message=DENY_PROTECTED)
        if decision.kind == "external":
            self.containment_denials += 1
            self.fail(FAIL_EXTERNAL)
            return sdk.PermissionResultDeny(message=DENY_EXTERNAL)
        self.containment_denials += 1
        return sdk.PermissionResultDeny(message=DENY_OUTSIDE)

    def on_result(self, text):
        """Observe the state, then let the core classify the turn end."""
        self.core.observe_state("turn_end")
        action = self.core.on_turn_end(text)
        self.log({"harness": "turn_end", "action": action[0],
                  "payload": action[1]})
        return action


async def _keep_open(_input_data, _tool_use_id, _context):
    """PreToolUse no-op that keeps the stream open for can_use_tool."""
    return {"continue_": True}


def build_options(sdk, session, settings, env, stderr=None):
    return sdk.ClaudeAgentOptions(
        cwd=session.copy.root,
        plugins=[{"type": "local", "path": session.snapshot.path}],
        settings=json.dumps(settings),
        setting_sources=[],
        strict_mcp_config=True,
        mcp_servers={},
        permission_mode="default",
        can_use_tool=session.can_use_tool,
        hooks={"PreToolUse": [sdk.HookMatcher(matcher=None,
                                              hooks=[_keep_open])]},
        env=session_env(env),
        stderr=stderr)


def _turn_text(result_msg, last_text):
    text = getattr(result_msg, "result", None)
    return text if isinstance(text, str) and text.strip() else last_text


async def _run_session(sdk, session, prompt, settings, env, timeout_s):
    stderr_tail = collections.deque(maxlen=STDERR_TAIL)
    options = build_options(sdk, session, settings, env,
                            stderr=stderr_tail.append)
    try:
        async with asyncio.timeout(timeout_s):
            async with sdk.ClaudeSDKClient(options=options) as client:
                next_prompt = prompt
                while next_prompt is not None:
                    session.log({"harness": "query", "prompt": next_prompt})
                    await client.query(next_prompt)
                    next_prompt = None
                    last_text = ""
                    async for msg in client.receive_response():
                        obj = message_to_dict(msg)
                        session.log(obj)
                        if isinstance(msg, sdk.SystemMessage) \
                                and msg.subtype == "init" \
                                and session.init is None:
                            session.init = msg.data
                            check_plugin_identity(msg.data,
                                                  session.snapshot.path)
                            check_no_mcp_servers(msg.data)
                        texts = [b["text"] for b in obj.get("content") or ()
                                 if isinstance(b, dict)
                                 and b.get("type") == "text"]
                        if obj["type"] == "assistant" and texts:
                            last_text = "\n".join(texts)
                        if isinstance(msg, sdk.ResultMessage):
                            if session.failed_reason:
                                break
                            action, payload = session.on_result(
                                _turn_text(msg, last_text))
                            if action == "fail":
                                session.fail(payload)
                            elif action == "command":
                                if session.owner_commands \
                                        >= MAX_OWNER_COMMANDS:
                                    session.fail("owner command limit "
                                                 "reached")
                                else:
                                    session.owner_commands += 1
                                    next_prompt = payload
    except DriverError:
        raise
    except Exception as exc:
        session.log({"harness": "error", "where": "session",
                     "error": repr(exc), "stderr": list(stderr_tail)})
        if session.init is None:
            raise DriverError("session did not start: %s"
                              % " | ".join(stderr_tail)[-2000:]) from exc
        raise


def _transcript_sha256(out_dir):
    digest = hashlib.sha256()
    with open(os.path.join(out_dir, TRANSCRIPT_NAME), "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def drive(copy, snapshot, prompt, core, out_dir, settings, env=None,
          timeout_s=DEFAULT_TIMEOUT_S):
    """Run one session; return DriveResult. Raises DriverError when the
    session cannot be launched as specified (never falls back)."""
    if not harness_sandbox.settings_is_fail_closed(settings):
        raise DriverError("settings not fail-closed")
    sdk = _sdk()
    session = Session(copy, snapshot, core, out_dir)
    started = time.monotonic()
    try:
        session.log({"harness": "start",
                     "sdk_version": getattr(sdk, "version", None),
                     "copy_root": copy.root, "plugin_path": snapshot.path})
        asyncio.run(_run_session(sdk, session, prompt, settings, env,
                                 timeout_s))
        session.log({"harness": "end",
                     "seconds": round(time.monotonic() - started, 3)})
    finally:
        session.close()
    init = session.init or {}
    return DriveResult(init, session.owner_commands,
                       session.containment_denials, session.protected_denials,
                       session.failed_reason, _transcript_sha256(out_dir),
                       init.get("claude_code_version"), init.get("model"))
