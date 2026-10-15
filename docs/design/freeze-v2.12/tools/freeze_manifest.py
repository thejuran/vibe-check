"""Freeze manifest: the content identity of a release candidate.

`generate` records, for candidate commit C:
  * the plugin file map from the git tree of C (every blob under
    plugins/vibe-check, sha256 + mode) — never the working tree;
  * the file maps of every runtime-consumed instruction, configuration and
    script outside the plugin (fix-harness kit, holdout tools, the freeze kit,
    the B3 runner layer, reachability-dev cases, B3 answer keys and allowances);
  * agent model pins, the `<TOP>` model with its source, launch models;
  * the Codex CLI version, its three behavior keys and companion identity;
  * per-runner environment profiles: CLI binary identities, the user-level
    settings projection the session inherits, the runner settings template.

Copy rule: copy only allowlisted non-secret shapes, hash everything else.
`MANIFEST_SCHEMA` is the only authority on which keys may exist;
`assert_no_secrets` validates the whole manifest against it and scans every
string leaf for credential-shaped values. Problem text names dotted paths,
never values.

CLI:
  freeze_manifest.py generate --candidate <rev> --out <path> [--home H]
      [--codex-home C] [--harness-venv V] [--previous <manifest>]
      [--allow-missing-runner-settings]
  freeze_manifest.py show --manifest M
  freeze_manifest.py verify-self --manifest M
Exit 0 ok / 1 refused or problems / 2 usage error.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import tomllib
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import freeze_common  # noqa: E402
from freeze_common import FreezeError  # noqa: E402

SCHEMA = "freeze-manifest/1"
PLUGIN_ROOT = "plugins/vibe-check"
CLI_TIMEOUT = 60

# Mirrors score43.RUNTIME_ROOTS (a test pins the two equal).
RUNTIME_ROOTS = (".claude-plugin", "agents", "commands", "scripts", "templates",
                 "hooks", "phases")

# Runtime-consumed paths outside the plugin: (prefix, basename glob or None).
COVERED = (
    ("docs/design/fix-harness/tools", None),
    ("docs/design/fix-harness/fixtures", None),
    ("docs/design/fix-harness/keys", None),
    ("docs/design/fix-harness/requirements.txt", None),
    ("docs/design/holdout-v2.12/tools", None),
    ("docs/design/freeze-v2.12/tools", None),
    ("docs/design/freeze-v2.12/PATH-MAP.json", None),
    ("docs/design/freeze-v2.12/README.md", None),
    ("docs/design/b3-ground-truth/b3-runner-v2.12", None),
    # the B3 live-check runbook: b3_block executes its blocks (D-18: Markdown, still covered)
    ("docs/design/reachability-dev/RUN-PHASE54-live.md", None),
    ("docs/design/reachability-dev/cases", None),
    ("docs/design/b3-ground-truth", "ANSWER-KEY-*.md"),
    ("docs/design/b3-ground-truth", "REPLAY-CATCH-MANIFEST-*.json"),
    ("docs/design/b3-ground-truth", "SUPERSESSIONS-*.md"),
    ("docs/design/b3-ground-truth", "ALLOWANCES-*.json"),
    ("docs/design/b3-ground-truth", "CALIBRATION-*.md"),
)
# Generated freeze data never enters a map it is checked against.
COVERED_EXCLUDED_GLOBS = ("docs/design/freeze-v2.12/**/FREEZE-MANIFEST-*.json",
                          "docs/design/freeze-v2.12/evidence/**")

HARNESS_KIT_PREFIXES = ("docs/design/fix-harness/tools",
                        "docs/design/fix-harness/fixtures",
                        "docs/design/fix-harness/keys")
HOLDOUT_KIT_PREFIX = "docs/design/holdout-v2.12/tools"
HARNESS_REQUIREMENTS = "docs/design/fix-harness/requirements.txt"
HARNESS_PROBE = "docs/design/fix-harness/fixtures/probe/sandbox-probe.json"
HARNESS_VENV_DEFAULT = "docs/design/fix-harness/.venv"
B3_RUNNER_DIR = "docs/design/b3-ground-truth/b3-runner-v2.12"
RUNNER_TEMPLATE = B3_RUNNER_DIR + "/settings-measured.json"
RUNNER_STATUSLINE = B3_RUNNER_DIR + "/statusline-capture.sh"
RUNNER_SUBSTITUTION = {"key": "statusLine.command", "placeholder": "<RUNNER>"}
B3_LAUNCH_MODEL = "claude-fable-5-1[1m]"
COMPANION_PLUGIN = "codex@openai-codex"
GATEWAY_PLUGIN = "model-gateway@eigenwise-toolshed"
CONTEXT_WINDOW_EXPECTED = 1000000
UPDATES_EXPECTED = {"DISABLE_AUTOUPDATER": "1", "DISABLE_UPDATES": "1"}
TOP_ALLOWED = ("opus", "fable")

# Never projected: cosmetic settings do not stop runs.
COSMETIC_KEYS = ("theme", "tui", "statusLine", "agentPushNotifEnabled",
                 "skipWorkflowUsageWarning")

ENV_ALLOWLIST = (
    "ANTHROPIC_BASE_URL", "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_FABLE_MODEL", "ANTHROPIC_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL", "CLAUDE_CODE_MAX_OUTPUT_TOKENS",
    "CLAUDE_CODE_DISABLE_1M_CONTEXT", "CLAUDE_CODE_EFFORT_LEVEL",
    "CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK",
    "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY", "ENABLE_TOOL_SEARCH",
    "DISABLE_AUTOUPDATER", "DISABLE_UPDATES", "VIBE_CHECK_TOP_MODEL",
)

_MODEL_RE = r"^[A-Za-z0-9._\[\]-]{1,64}$"
_FLAG_RE = r"^(0|1|true|false)$"
URL_SHAPE = "url"
ENV_VALUE_SHAPES = {
    "ANTHROPIC_BASE_URL": URL_SHAPE,
    "ANTHROPIC_DEFAULT_OPUS_MODEL": _MODEL_RE,
    "ANTHROPIC_DEFAULT_SONNET_MODEL": _MODEL_RE,
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": _MODEL_RE,
    "ANTHROPIC_DEFAULT_FABLE_MODEL": _MODEL_RE,
    "ANTHROPIC_MODEL": _MODEL_RE,
    "CLAUDE_CODE_SUBAGENT_MODEL": _MODEL_RE,
    "VIBE_CHECK_TOP_MODEL": _MODEL_RE,
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": r"^[0-9]{1,7}$",
    "CLAUDE_CODE_EFFORT_LEVEL": r"^[a-z]{1,16}$",
    "CLAUDE_CODE_DISABLE_1M_CONTEXT": _FLAG_RE,
    "CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK": _FLAG_RE,
    "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": _FLAG_RE,
    "ENABLE_TOOL_SEARCH": _FLAG_RE,
    "DISABLE_AUTOUPDATER": _FLAG_RE,
    "DISABLE_UPDATES": _FLAG_RE,
}

LIMITATIONS = (
    "local hashes cannot prove the remote gateway/model service stayed unchanged",
    "--config auto semgrep rules are fetched live",
    "the gateway version id is best effort and null when the gateway exposes none",
    "verify-self reproduces the git-derived sections only; the live user-level "
    "projection is compared by the runner identity check",
)
PER_CALL_OVERRIDES = (
    "bugs: <TOP> (per-call override)",
    "architecture: <TOP> (per-call override)",
    "impact: opus (agent frontmatter)",
    "test-sufficiency: opus (agent frontmatter)",
)
HOLDOUT_EVAL_CONTRACT = (
    "Phase 55 launcher; must call freeze_check.verify(runner='holdout-eval')",
)
SETTING_SOURCES = ()

SECRET_VALUE_RE = re.compile(
    r"sk-ant-|^Bearer |ghp_|gho_|xox[abp]-|AKIA[0-9A-Z]{16}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----")
# Applies to field NAMES inside settingsmap nodes only (never to path keys).
CRED_FIELD_RE = re.compile(
    r"(?i)(?:api[_-]?key)|token|secret|password|cookie|authorization")

_URL_SHAPE_RE = re.compile(r"^https?://[A-Za-z0-9.-]+(:[0-9]{1,5})?(/[A-Za-z0-9._/-]*)?$")
_VERSION_RE = r"^[A-Za-z0-9._+-]{1,64}$"
_PATH_RE = r"^[A-Za-z0-9._/@ ~-]+$"
_PATHMAP_KEY_RE = re.compile(r"^(?:~/)?[A-Za-z0-9._/@ -]+$")
_COVERED_KEY_RE = re.compile(r"^[A-Za-z0-9._/@ *-]+$")
_PLUGIN_NAME_RE = r"^[A-Za-z0-9._@-]{1,128}$"
_AGENT_NAME_RE = r"^[A-Za-z0-9._-]{1,64}$"
_ISO_RE = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
_CLI_VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+[A-Za-z0-9._+-]*")
_FRONTMATTER_MODEL_RE = re.compile(r"^model:\s*(\S+)\s*$")
_SDK_DIST_RE = re.compile(r"^claude_agent_sdk-([A-Za-z0-9._+-]+)\.dist-info$")
_SDK_PIN_RE = re.compile(r"^claude-agent-sdk==([A-Za-z0-9._+-]+)\s*$", re.M)
_TOKEN_RE = re.compile(r'"([^"]*)"|\'([^\']*)\'|(\S+)')


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #

class _Node:
    def __init__(self, kind, **attrs):
        self.kind = kind
        self.__dict__.update(attrs)


def obj(fields):
    return _Node("obj", fields=fields)


def settingsmap(fields):
    """A closed field set over private settings: unknown fields are refused
    and a credential-named field is refused even when listed."""
    return _Node("settingsmap", fields=fields)


def pathmap(value):
    return _Node("pathmap", value=value)


def coveredmap(value):
    return _Node("coveredmap", value=value)


def envmap():
    return _Node("envmap")


def strmap(key_re, value):
    return _Node("strmap", key_re=key_re, value=value)


def identitymap():
    return _Node("identitymap")


def hex40():
    return _Node("hex40")


def hex64():
    return _Node("hex64")


def hex64_or_null():
    return _Node("hex64_or_null")


def boolean():
    return _Node("bool")


def integer():
    return _Node("int")


def string(regex):
    return _Node("str", regex=regex)


def url():
    return _Node("url")


def constlist(name):
    return _Node("constlist", name=name)


def listof(node):
    return _Node("list", item=node)


def opt(node):
    return _Node("opt", item=node)


FILE_ENTRY = obj({"sha256": hex64(), "mode": string(r"^(100644|100755|120000)$")})
IDENTITY = obj({"version": string(_VERSION_RE), "gitCommitSha": opt(hex40()),
                "tree_sha256": hex64()})
_MODEL = string(_MODEL_RE)
_LAUNCH = obj({"value": _MODEL,
               "source": string(r"^(runner-contract|probe-record)$")})
_CLI = obj({"kind": string(r"^native$"), "version": string(_VERSION_RE),
            "path": string(_PATH_RE), "sha256": hex64()})
_KIT = obj({"tree_sha256": hex64()})
_UPDATES = obj({"DISABLE_AUTOUPDATER": string(r"^1$"),
                "DISABLE_UPDATES": string(r"^1$")})
_USER_LEVEL = settingsmap({
    "claude_md_sha256": hex64_or_null(),
    "hooks": hex64_or_null(),
    "hook_scripts": pathmap(hex64()),
    "permissions": hex64_or_null(),
    "enabled_plugins": identitymap(),
    "env": envmap(),
    "effortLevel": opt(string(r"^[a-z]{1,16}$")),
    "modelSettings": obj({"sha256": hex64_or_null(),
                          "effort": strmap(_MODEL_RE, string(r"^[a-z]{1,16}$"))}),
    "alwaysThinkingEnabled": opt(boolean()),
})
_RUNNER_SETTINGS = opt(settingsmap({
    "template_path": string(_PATH_RE),
    "template_canonical_sha256": hex64(),
    "statusline_script_sha256": hex64(),
    "substitution": obj({"key": string(r"^statusLine\.command$"),
                         "placeholder": string(r"^<RUNNER>$")}),
}))
_GATEWAY = obj({"plugin_version": opt(string(_VERSION_RE)),
                "tree_sha256": hex64_or_null(),
                "base_url": opt(url()),
                "version_id": opt(string(_VERSION_RE))})

MANIFEST_SCHEMA = obj({
    "schema": string(r"^freeze-manifest/1$"),
    "generated_at": string(_ISO_RE),
    "candidate_sha": hex40(),
    "candidate_tree": hex40(),
    "plugin": obj({
        "root": string(r"^plugins/vibe-check$"),
        "files": pathmap(FILE_ENTRY),
        "file_count": integer(),
        "tree_sha256": hex64(),
        "runtime_fingerprint": hex64(),
        "plugin_json_version": string(_VERSION_RE),
    }),
    "covered": coveredmap(obj({"files": pathmap(FILE_ENTRY),
                               "tree_sha256": hex64()})),
    "models": settingsmap({
        "agent_pins": strmap(_AGENT_NAME_RE, _MODEL),
        "top": obj({"value": _MODEL,
                    "source": string(r"^(env|toml|default|env-invalid)$")}),
        "per_call_overrides": constlist("PER_CALL_OVERRIDES"),
        "launch_model": obj({"b3": _LAUNCH, "fix-harness": _LAUNCH,
                             "holdout-eval": _LAUNCH}),
    }),
    "codex": obj({
        "cli_version": string(_VERSION_RE),
        "config": settingsmap({"model": opt(string(_MODEL_RE)),
                               "model_reasoning_effort": opt(string(r"^[a-z]{1,16}$")),
                               "service_tier": opt(string(r"^[a-z]{1,16}$"))}),
        "config_sha256": hex64_or_null(),
        "companion": opt(IDENTITY),
        "project_codex_dir_absent": boolean(),
    }),
    "runners": obj({
        "b3": obj({
            "cli": _CLI,
            "runner_settings": _RUNNER_SETTINGS,
            "launch_model": _LAUNCH,
            "user_level": _USER_LEVEL,
            "gateway": _GATEWAY,
            "context_window_expected": integer(),
            "updates": _UPDATES,
        }),
        "fix-harness": obj({
            "sdk_version": string(_VERSION_RE),
            "sdk_requirements_pin": opt(string(_VERSION_RE)),
            "requirements_sha256": hex64_or_null(),
            "bundled_cli": obj({"version": string(_VERSION_RE),
                                "path": string(_PATH_RE), "sha256": hex64()}),
            "kit": _KIT,
            "setting_sources": constlist("SETTING_SOURCES"),
            "env": envmap(),
            "launch_model": _LAUNCH,
            "probe_settings_fingerprint": hex64(),
            "context_window_expected": integer(),
            "updates": _UPDATES,
        }),
        "holdout-autopilot": obj({"cli": _CLI, "kit": _KIT,
                                  "loads_plugin": boolean()}),
        "holdout-eval": obj({
            "contract": constlist("HOLDOUT_EVAL_CONTRACT"),
            "cli": _CLI,
            "kit": _KIT,
            "user_level": _USER_LEVEL,
            "runner_settings": _RUNNER_SETTINGS,
            "launch_model": _LAUNCH,
        }),
    }),
    "limitations": constlist("LIMITATIONS"),
    "lineage": obj({"previous_manifest_id": hex64_or_null(),
                    "previous_candidate_sha": opt(hex40())}),
    "manifest_id": hex64(),
})


def validate_url(value):
    """Parse `value` with urllib.parse.urlsplit (never a regex alone).
    None when `value` is an http(s) URL with a host and no userinfo,
    query or fragment; otherwise a short problem text (never the value)."""
    if not isinstance(value, str):
        return "url is not a string"
    try:
        parts = urllib.parse.urlsplit(value)
        host = parts.hostname
        parts.port  # noqa: B018 - raises ValueError on a malformed port
    except ValueError:
        return "url is malformed"
    if parts.scheme not in ("http", "https"):
        return "url scheme must be http or https"
    if not host:
        return "url has no host"
    if parts.username is not None or parts.password is not None:
        return "url carries userinfo"
    if parts.query or parts.fragment:
        return "url carries a query string or fragment"
    if not _URL_SHAPE_RE.match(value):
        return "url is outside the allowed shape"
    return None


def _join(path, key):
    return "%s.%s" % (path, key) if path else str(key)


def _obj_unknown(fields, value, path):
    return ["%s: unknown field" % _join(path, k) for k in sorted(value)
            if k not in fields]


def _settingsmap_unknown(fields, value, path):
    return ["%s: unknown field" % _join(path, k) for k in sorted(value)
            if k not in fields]


def _constlist_problem(name, value, path):
    if value != list(globals()[name]):
        return "%s: must equal %s" % (path, name)
    return None


def _env_value_problem(key, value, path):
    if value is None:
        return None
    shape = ENV_VALUE_SHAPES[key]
    if shape == URL_SHAPE:
        problem = validate_url(value)
        return "%s: %s" % (path, problem) if problem else None
    if not isinstance(value, str) or not re.match(shape, value):
        return "%s: value outside the allowed shape" % path
    return None


def _key_ok(regex, key):
    return isinstance(key, str) and bool(regex.match(key)) \
        and ".." not in key.split("/")


def validate_schema(node, value, path=""):
    """Problems (dotted path + reason, never a value) of `value` against
    schema `node`; [] when it conforms."""
    k = node.kind
    if k == "opt":
        return [] if value is None else validate_schema(node.item, value, path)
    if k in ("obj", "settingsmap"):
        if not isinstance(value, dict):
            return ["%s: not an object" % (path or "<root>")]
        if k == "obj":
            problems = _obj_unknown(node.fields, value, path)
        else:
            problems = _settingsmap_unknown(node.fields, value, path)
        for name in sorted(node.fields):
            sub = _join(path, name)
            if k == "settingsmap" and CRED_FIELD_RE.search(name):
                problems.append("%s: credential-named field refused" % sub)
                continue
            if name not in value:
                problems.append("%s: missing field" % sub)
                continue
            problems += validate_schema(node.fields[name], value[name], sub)
        return problems
    if k in ("pathmap", "coveredmap", "strmap"):
        if not isinstance(value, dict):
            return ["%s: not an object" % path]
        regex = {"pathmap": _PATHMAP_KEY_RE, "coveredmap": _COVERED_KEY_RE}.get(k)
        if regex is None:
            regex = re.compile(node.key_re)
        problems = []
        for key in sorted(value, key=str):
            if not _key_ok(regex, key):
                problems.append("%s: key outside the allowed path shape" % path)
                continue
            problems += validate_schema(node.value, value[key], _join(path, key))
        return problems
    if k == "identitymap":
        if not isinstance(value, dict):
            return ["%s: not an object" % path]
        problems = []
        for key in sorted(value, key=str):
            if not isinstance(key, str) or not re.match(_PLUGIN_NAME_RE, key):
                problems.append("%s: plugin name outside the allowed shape" % path)
                continue
            problems += validate_schema(IDENTITY, value[key], _join(path, key))
        return problems
    if k == "envmap":
        if not isinstance(value, dict):
            return ["%s: not an object" % path]
        problems = ["%s: env key not in the allowlist: %s" % (path, key)
                    for key in sorted(value, key=str) if key not in ENV_ALLOWLIST]
        for key in ENV_ALLOWLIST:
            if key not in value:
                problems.append("%s: missing field" % _join(path, key))
                continue
            problem = _env_value_problem(key, value[key], _join(path, key))
            if problem:
                problems.append(problem)
        return problems
    if k == "constlist":
        problem = _constlist_problem(node.name, value, path)
        return [problem] if problem else []
    if k == "list":
        if not isinstance(value, list):
            return ["%s: not a list" % path]
        problems = []
        for i, item in enumerate(value):
            problems += validate_schema(node.item, item, "%s[%d]" % (path, i))
        return problems
    if k == "url":
        problem = validate_url(value)
        return ["%s: %s" % (path, problem)] if problem else []
    if k == "hex40":
        ok = isinstance(value, str) and bool(freeze_common.HEX40_RE.match(value))
    elif k == "hex64":
        ok = isinstance(value, str) and bool(freeze_common.HEX64_RE.match(value))
    elif k == "hex64_or_null":
        ok = value is None or (isinstance(value, str)
                               and bool(freeze_common.HEX64_RE.match(value)))
    elif k == "bool":
        ok = isinstance(value, bool)
    elif k == "int":
        ok = isinstance(value, int) and not isinstance(value, bool)
    elif k == "str":
        ok = isinstance(value, str) and bool(re.match(node.regex, value))
    else:
        return ["%s: unknown schema node kind" % path]
    return [] if ok else ["%s: value outside the allowed %s shape" % (path, k)]


def _scan_values(value, path, problems):
    if isinstance(value, dict):
        for key in sorted(value, key=str):
            _scan_values(value[key], _join(path, key), problems)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _scan_values(item, "%s[%d]" % (path, i), problems)
    elif isinstance(value, str) and SECRET_VALUE_RE.search(value):
        problems.append("%s: credential-shaped value refused" % path)


def assert_no_secrets(manifest):
    """Raise FreezeError unless the WHOLE manifest conforms to
    MANIFEST_SCHEMA and no string leaf carries a credential-shaped value."""
    problems = validate_schema(MANIFEST_SCHEMA, manifest)
    _scan_values(manifest, "", problems)
    if problems:
        raise FreezeError("manifest refused: " + "; ".join(problems))


# --------------------------------------------------------------------------- #
# Git-derived sections
# --------------------------------------------------------------------------- #

def expected_plugin_files(repo, sha):
    """{rel: {"sha256", "mode"}} of every blob under plugins/vibe-check at C."""
    return freeze_common.tree_files_at(repo, sha, PLUGIN_ROOT)


def runtime_fingerprint_of_map(files_map):
    """score43.runtime_fingerprint computed from a git file map: sha256 over
    the sorted `<rel>\\0<sha256>\\n` lines of the runtime-root files, minus
    caches, `.pyc` and the `.in_use` marker."""
    lines = []
    for rel, entry in files_map.items():
        segs = rel.split("/")
        if segs[0] not in RUNTIME_ROOTS or len(segs) < 2:
            continue
        if any(s in freeze_common.EXCLUDED_DIRS for s in segs[:-1]):
            continue
        if segs[-1] in freeze_common.EXCLUDED_NAMES \
                or segs[-1].endswith(freeze_common.EXCLUDED_SUFFIXES):
            continue
        lines.append("%s\0%s\n" % (rel, freeze_common.file_sha(entry)))
    return freeze_common.sha256_bytes("".join(sorted(lines)).encode("utf-8"))


def _covered_key(prefix, pattern):
    return prefix + "/" + pattern if pattern else prefix


def _covered_excluded(full):
    return any(freeze_common.glob_to_regex(g).match(full)
               for g in COVERED_EXCLUDED_GLOBS)


def covered_tree_files(repo, sha):
    """{covered key: {"files", "tree_sha256"}} for every COVERED entry."""
    out = {}
    for prefix, pattern in COVERED:
        files = freeze_common.tree_files_at(repo, sha, prefix, pattern=pattern,
                                            recursive=pattern is None)
        files = {rel: v for rel, v in files.items()
                 if not _covered_excluded(prefix + "/" + rel)
                 and not (rel == os.path.basename(prefix)
                          and _covered_excluded(prefix))}
        out[_covered_key(prefix, pattern)] = {
            "files": files, "tree_sha256": freeze_common.tree_sha256_of_map(files)}
    return out


def _kit_tree(covered, prefixes):
    combined = {}
    for prefix in prefixes:
        for rel, entry in covered[prefix]["files"].items():
            combined[prefix + "/" + rel] = entry
    return {"tree_sha256": freeze_common.tree_sha256_of_map(combined)}


def _agent_pins(repo, sha, plugin_files):
    pins = {}
    for rel in sorted(plugin_files):
        segs = rel.split("/")
        if len(segs) != 2 or segs[0] != "agents" or not segs[1].endswith(".md"):
            continue
        data = freeze_common.blob_at(repo, sha, PLUGIN_ROOT + "/" + rel) or b""
        model = _frontmatter_model(data.decode("utf-8", errors="replace"))
        if model is not None:
            pins[segs[1][:-3]] = model
    return pins


def _frontmatter_model(text):
    """The `model:` value of the leading `---` YAML block, or None. Body
    text after the block is never read."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            return None
        m = _FRONTMATTER_MODEL_RE.match(line)
        if m:
            return m.group(1).strip("'\"")
    return None


def _plugin_json_version(repo, sha):
    data = freeze_common.blob_at(repo, sha, PLUGIN_ROOT + "/.claude-plugin/plugin.json")
    if data is None:
        raise FreezeError("plugin.json absent at the candidate")
    try:
        version = json.loads(data.decode("utf-8")).get("version")
    except (ValueError, AttributeError):
        raise FreezeError("plugin.json at the candidate is not a JSON object")
    if not isinstance(version, str):
        raise FreezeError("plugin.json at the candidate has no version")
    return version


def _runner_settings(repo, sha, require):
    template = freeze_common.blob_at(repo, sha, RUNNER_TEMPLATE)
    if template is None:
        if require:
            raise FreezeError("runner settings template absent at the candidate: "
                              + RUNNER_TEMPLATE)
        return None
    script = freeze_common.blob_at(repo, sha, RUNNER_STATUSLINE)
    if script is None:
        raise FreezeError("statusline capture script absent at the candidate: "
                          + RUNNER_STATUSLINE)
    try:
        parsed = json.loads(template.decode("utf-8"))
    except ValueError:
        raise FreezeError("runner settings template is not JSON")
    return {"template_path": RUNNER_TEMPLATE,
            "template_canonical_sha256": freeze_common.canonical_sha256(parsed),
            "statusline_script_sha256": freeze_common.sha256_bytes(script),
            "substitution": dict(RUNNER_SUBSTITUTION)}


def _probe_record(repo, sha):
    data = freeze_common.blob_at(repo, sha, HARNESS_PROBE)
    if data is None:
        raise FreezeError("fix-harness probe record absent at the candidate")
    try:
        record = json.loads(data.decode("utf-8"))
    except ValueError:
        raise FreezeError("fix-harness probe record is not JSON")
    model = record.get("model") if isinstance(record, dict) else None
    if not isinstance(model, str) or not model:
        raise FreezeError("fix-harness probe record has no observed model")
    return {"value": model, "source": "probe-record"}, record.get("settings_fingerprint")


def _requirements(repo, sha):
    data = freeze_common.blob_at(repo, sha, HARNESS_REQUIREMENTS)
    if data is None:
        return None, None
    m = _SDK_PIN_RE.search(data.decode("utf-8", errors="replace"))
    return freeze_common.sha256_bytes(data), (m.group(1) if m else None)


def git_sections(repo, sha, require_runner_settings=True):
    """Everything the manifest derives from the git tree of `sha`."""
    plugin_files = expected_plugin_files(repo, sha)
    covered = covered_tree_files(repo, sha)
    launch, probe_fp = _probe_record(repo, sha)
    req_sha, req_pin = _requirements(repo, sha)
    return {
        "plugin": {
            "root": PLUGIN_ROOT,
            "files": plugin_files,
            "file_count": len(plugin_files),
            "tree_sha256": freeze_common.tree_sha256_of_map(plugin_files),
            "runtime_fingerprint": runtime_fingerprint_of_map(plugin_files),
            "plugin_json_version": _plugin_json_version(repo, sha),
        },
        "covered": covered,
        "agent_pins": _agent_pins(repo, sha, plugin_files),
        "runner_settings": _runner_settings(repo, sha, require_runner_settings),
        "harness_launch": launch,
        "probe_settings_fingerprint": probe_fp,
        "requirements_sha256": req_sha,
        "requirements_pin": req_pin,
        "harness_kit": _kit_tree(covered, HARNESS_KIT_PREFIXES),
        "holdout_kit": _kit_tree(covered, (HOLDOUT_KIT_PREFIX,)),
    }


# --------------------------------------------------------------------------- #
# Local environment sections
# --------------------------------------------------------------------------- #

def _which(name):
    for d in os.environ.get("PATH", "").split(os.pathsep):
        cand = os.path.join(d, name)
        if d and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def _cli_version(argv):
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=CLI_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        raise FreezeError("%s --version could not run" % os.path.basename(argv[0]))
    if proc.returncode != 0:
        raise FreezeError("%s --version failed (exit %d)"
                          % (os.path.basename(argv[0]), proc.returncode))
    m = _CLI_VERSION_RE.search(proc.stdout.decode("utf-8", errors="replace"))
    if not m:
        raise FreezeError("%s --version printed no version"
                          % os.path.basename(argv[0]))
    return m.group(0)


def _display_path(path, home, repo):
    path = os.path.realpath(path)
    for base, label in ((os.path.realpath(repo), None),
                        (os.path.realpath(home), "~")):
        if path == base or path.startswith(base + os.sep):
            rel = os.path.relpath(path, base).replace(os.sep, "/")
            return rel if label is None else label + "/" + rel
    return path


def _native_cli(home, repo):
    found = _which("claude")
    if found is None:
        raise FreezeError("claude CLI not found on PATH")
    resolved = os.path.realpath(found)
    return {"kind": "native", "version": _cli_version([found, "--version"]),
            "path": _display_path(resolved, home, repo),
            "sha256": freeze_common.sha256_file(resolved)}


def _read_json(path, what):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        raise FreezeError("%s is unreadable or not JSON" % what)


def _installed_plugins(home):
    data = _read_json(os.path.join(home, ".claude", "plugins",
                                   "installed_plugins.json"),
                      "installed_plugins.json")
    plugins = data.get("plugins") if isinstance(data, dict) else None
    return plugins if isinstance(plugins, dict) else {}


def _install_entry(installed, name):
    entries = installed.get(name)
    if isinstance(entries, dict):
        entries = [entries]
    if not isinstance(entries, list) or not entries:
        return None
    user = [e for e in entries if isinstance(e, dict) and e.get("scope") == "user"]
    entry = (user or [e for e in entries if isinstance(e, dict)] or [None])[0]
    return entry


def _plugin_identity(installed, name):
    entry = _install_entry(installed, name)
    if entry is None:
        return None
    path = entry.get("installPath")
    if not isinstance(path, str) or not os.path.isdir(path):
        raise FreezeError("installed plugin has no install directory: %s" % name)
    sha = entry.get("gitCommitSha")
    return {"version": entry.get("version"),
            "gitCommitSha": sha if isinstance(sha, str)
            and freeze_common.HEX40_RE.match(sha) else None,
            "tree_sha256": freeze_common.tree_sha256_of_map(
                freeze_common.live_files(path))}


def env_projection(env):
    """{key: value-or-None} over ENV_ALLOWLIST; nothing else is copied."""
    out = {}
    for key in ENV_ALLOWLIST:
        value = env.get(key) if isinstance(env, dict) else None
        if isinstance(value, bool):
            value = "true" if value else "false"
        elif value is not None and not isinstance(value, str):
            value = str(value)
        out[key] = value
    return out


def _hooks_identity(settings):
    """sha256 of the canonical JSON of the hooks configuration (null when
    absent). The configuration itself is never placed in the manifest."""
    if "hooks" not in settings:
        return None
    return freeze_common.canonical_sha256(settings["hooks"])


def _hook_commands(node, out):
    if isinstance(node, dict):
        cmd = node.get("command")
        if isinstance(cmd, str):
            out.append(cmd)
        args = node.get("args")
        if isinstance(args, list):
            out.extend(a for a in args if isinstance(a, str))
        for value in node.values():
            if isinstance(value, (dict, list)):
                _hook_commands(value, out)
    elif isinstance(node, list):
        for item in node:
            _hook_commands(item, out)


def _hook_scripts(settings, home, repo):
    """{display path: sha256} for every command token in the hooks
    configuration that resolves to an existing file. Arguments that are not
    files are never recorded."""
    strings = []
    _hook_commands(settings.get("hooks"), strings)
    # settings.json is projected field by field; hashing it whole here would
    # turn a cosmetic edit into an identity difference.
    settings_path = os.path.realpath(os.path.join(home, ".claude", "settings.json"))
    out = {}
    for text in strings:
        for m in _TOKEN_RE.finditer(text):
            token = next(g for g in m.groups() if g is not None)
            for var in ("${HOME}", "$HOME"):
                token = token.replace(var, home)
            if token.startswith("~/"):
                token = os.path.join(home, token[2:])
            if not os.path.isabs(token) or not os.path.isfile(token) \
                    or os.path.realpath(token) == settings_path:
                continue
            out[_display_path(token, home, repo)] = \
                freeze_common.sha256_file(os.path.realpath(token))
    return out


def _model_settings(settings):
    raw = settings.get("modelSettings")
    effort = {}
    if isinstance(raw, dict):
        for model, conf in raw.items():
            if isinstance(conf, dict) and isinstance(conf.get("effortLevel"), str):
                effort[model] = conf["effortLevel"]
    return {"sha256": None if raw is None else freeze_common.canonical_sha256(raw),
            "effort": effort}


def user_level(home, repo):
    """The D-26 projection of ~/.claude: hashes for private content, copies
    only of allowlisted non-secret shapes. Cosmetic keys never enter it."""
    settings = _read_json(os.path.join(home, ".claude", "settings.json"),
                          "settings.json")
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        raise FreezeError("settings.json is not a JSON object")
    claude_md = os.path.join(home, ".claude", "CLAUDE.md")
    installed = _installed_plugins(home)
    enabled = {}
    for name, on in sorted((settings.get("enabledPlugins") or {}).items()):
        if on is not True:
            continue
        identity = _plugin_identity(installed, name)
        if identity is None:
            raise FreezeError("enabled plugin is not installed: %s" % name)
        enabled[name] = identity
    return {
        "claude_md_sha256": freeze_common.sha256_file(claude_md)
        if os.path.isfile(claude_md) else None,
        "hooks": _hooks_identity(settings),
        "hook_scripts": _hook_scripts(settings, home, repo),
        "permissions": freeze_common.canonical_sha256(settings["permissions"])
        if "permissions" in settings else None,
        "enabled_plugins": enabled,
        "env": env_projection(settings.get("env") or {}),
        "effortLevel": settings.get("effortLevel"),
        "modelSettings": _model_settings(settings),
        "alwaysThinkingEnabled": settings.get("alwaysThinkingEnabled"),
    }, settings


def _gateway(home, settings):
    installed = _installed_plugins(home)
    entry = _install_entry(installed, GATEWAY_PLUGIN)
    identity = _plugin_identity(installed, GATEWAY_PLUGIN) if entry else None
    version_id = None
    if entry:
        pkg = _read_json(os.path.join(entry["installPath"], "package.json"),
                         "gateway package.json")
        if isinstance(pkg, dict) and isinstance(pkg.get("version"), str):
            version_id = pkg["version"]
    env = settings.get("env") if isinstance(settings.get("env"), dict) else {}
    return {"plugin_version": identity["version"] if identity else None,
            "tree_sha256": identity["tree_sha256"] if identity else None,
            "base_url": env.get("ANTHROPIC_BASE_URL"),
            "version_id": version_id}


def _codex(home, codex_home, repo, sha):
    found = _which("codex")
    if found is None:
        raise FreezeError("codex CLI not found on PATH")
    path = os.path.join(codex_home, "config.toml")
    config = {"model": None, "model_reasoning_effort": None, "service_tier": None}
    config_sha = None
    if os.path.isfile(path):
        try:
            with open(path, "rb") as fh:
                raw = tomllib.load(fh)
        except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
            raise FreezeError("codex config.toml is unreadable or not TOML")
        for key in config:
            if isinstance(raw.get(key), str):
                config[key] = raw[key]
        config_sha = freeze_common.sha256_file(path)
    tracked = freeze_common.tree_files_at(repo, sha, ".codex")
    return {"cli_version": _cli_version([found, "--version"]),
            "config": config, "config_sha256": config_sha,
            "companion": _plugin_identity(_installed_plugins(home), COMPANION_PLUGIN),
            "project_codex_dir_absent": not tracked
            and not os.path.exists(os.path.join(repo, ".codex"))}


def _top_model(repo, env):
    raw = env.get("VIBE_CHECK_TOP_MODEL") if isinstance(env, dict) else None
    if raw:
        if raw in TOP_ALLOWED:
            return {"value": raw, "source": "env"}
        return {"value": "opus", "source": "env-invalid"}
    if os.path.isfile(os.path.join(repo, ".vibe-check.toml")):
        script = os.path.join(repo, PLUGIN_ROOT, "scripts", "config.py")
        try:
            proc = subprocess.run([sys.executable, script], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=CLI_TIMEOUT,
                                  env={"REPO_ROOT": repo,
                                       "PATH": os.environ.get("PATH", "")})
            top = json.loads(proc.stdout.decode("utf-8"))["values"]["top_model"]
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
            raise FreezeError("config.py could not resolve top_model")
        if top in TOP_ALLOWED:
            return {"value": top, "source": "toml"}
    return {"value": "opus", "source": "default"}


def _harness_runtime(repo, venv, home):
    venv = venv or os.path.join(repo, HARNESS_VENV_DEFAULT)
    lib = os.path.join(venv, "lib")
    sites = sorted(os.path.join(lib, d, "site-packages")
                   for d in (os.listdir(lib) if os.path.isdir(lib) else [])
                   if d.startswith("python"))
    for site in sites:
        if not os.path.isdir(site):
            continue
        versions = [m.group(1) for m in map(_SDK_DIST_RE.match, sorted(os.listdir(site)))
                    if m]
        bundled = os.path.join(site, "claude_agent_sdk", "_bundled", "claude")
        if versions and os.path.isfile(bundled):
            return versions[0], {
                "version": _cli_version([bundled, "--version"]),
                "path": _display_path(bundled, home, repo),
                "sha256": freeze_common.sha256_file(bundled)}
    raise FreezeError("fix-harness venv has no claude-agent-sdk with a bundled CLI")


# --------------------------------------------------------------------------- #
# Manifest
# --------------------------------------------------------------------------- #

def manifest_id(manifest):
    """sha256 of the canonical JSON of the manifest minus `manifest_id`."""
    body = {k: v for k, v in manifest.items() if k != "manifest_id"}
    return freeze_common.canonical_sha256(body)


def _lineage(previous):
    if previous is None:
        return {"previous_manifest_id": None, "previous_candidate_sha": None}
    prev = _read_json(previous, "previous manifest")
    if not isinstance(prev, dict) or prev.get("manifest_id") != manifest_id(prev):
        raise FreezeError("previous manifest is missing or its manifest_id "
                          "does not match its content")
    return {"previous_manifest_id": prev["manifest_id"],
            "previous_candidate_sha": prev.get("candidate_sha")}


def generate(repo, candidate, home=None, env=None, codex_home=None,
             harness_venv=None, clock=time.time, previous=None,
             require_runner_settings=True):
    """Build, validate and return the manifest for `candidate`."""
    home, codex_home = freeze_common.resolve_homes(home, codex_home)
    env = dict(os.environ) if env is None else env
    sha, tree = freeze_common.resolve_rev(repo, candidate)
    gs = git_sections(repo, sha, require_runner_settings)
    user, settings = user_level(home, repo)
    cli = _native_cli(home, repo)
    sdk_version, bundled = _harness_runtime(repo, harness_venv, home)
    b3_launch = {"value": B3_LAUNCH_MODEL, "source": "runner-contract"}
    manifest = {
        "schema": SCHEMA,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(clock())),
        "candidate_sha": sha,
        "candidate_tree": tree,
        "plugin": gs["plugin"],
        "covered": gs["covered"],
        "models": {
            "agent_pins": gs["agent_pins"],
            "top": _top_model(repo, env),
            "per_call_overrides": list(PER_CALL_OVERRIDES),
            "launch_model": {"b3": dict(b3_launch),
                             "fix-harness": dict(gs["harness_launch"]),
                             "holdout-eval": dict(b3_launch)},
        },
        "codex": _codex(home, codex_home, repo, sha),
        "runners": {
            "b3": {
                "cli": cli,
                "runner_settings": gs["runner_settings"],
                "launch_model": dict(b3_launch),
                "user_level": user,
                "gateway": _gateway(home, settings),
                "context_window_expected": CONTEXT_WINDOW_EXPECTED,
                "updates": dict(UPDATES_EXPECTED),
            },
            "fix-harness": {
                "sdk_version": sdk_version,
                "sdk_requirements_pin": gs["requirements_pin"],
                "requirements_sha256": gs["requirements_sha256"],
                "bundled_cli": bundled,
                "kit": gs["harness_kit"],
                "setting_sources": list(SETTING_SOURCES),
                "env": env_projection(env),
                "launch_model": dict(gs["harness_launch"]),
                "probe_settings_fingerprint": gs["probe_settings_fingerprint"],
                "context_window_expected": CONTEXT_WINDOW_EXPECTED,
                "updates": dict(UPDATES_EXPECTED),
            },
            "holdout-autopilot": {"cli": dict(cli), "kit": gs["holdout_kit"],
                                  "loads_plugin": False},
            "holdout-eval": {
                "contract": list(HOLDOUT_EVAL_CONTRACT),
                "cli": dict(cli),
                "kit": dict(gs["holdout_kit"]),
                "user_level": json.loads(json.dumps(user)),
                "runner_settings": json.loads(json.dumps(gs["runner_settings"])),
                "launch_model": dict(b3_launch),
            },
        },
        "limitations": list(LIMITATIONS),
        "lineage": _lineage(previous),
    }
    manifest["manifest_id"] = manifest_id(manifest)
    assert_no_secrets(manifest)
    return manifest


def write_manifest(path, manifest):
    """Write `manifest` to a NEW file (refuses an existing path or link)."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o644)
    except FileExistsError:
        raise FreezeError("refused: manifest path already exists: %s" % path)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def _diff_maps(label, want, got, problems):
    for rel in sorted(set(want) | set(got)):
        if rel not in got:
            problems.append("%s file missing at candidate: %s" % (label, rel))
        elif rel not in want:
            problems.append("%s file not in manifest: %s" % (label, rel))
        elif want[rel] != got[rel]:
            problems.append("%s file differs: %s" % (label, rel))


def verify_self(repo, manifest_path):
    """[] when the manifest's git-derived sections and its manifest_id are
    reproduced from `candidate_sha`; otherwise one line per difference."""
    m = _read_json(manifest_path, "manifest")
    if not isinstance(m, dict):
        return ["manifest is missing or not a JSON object"]
    problems = []
    try:
        assert_no_secrets(m)
    except FreezeError as exc:
        problems.append(str(exc))
    if m.get("manifest_id") != manifest_id(m):
        problems.append("manifest_id does not match the manifest content")
    sha = m.get("candidate_sha")
    if not isinstance(sha, str) or not freeze_common.HEX40_RE.match(sha):
        return problems + ["candidate_sha is not a full commit id"]
    try:
        got_sha, tree = freeze_common.resolve_rev(repo, sha)
        gs = git_sections(repo, got_sha,
                          require_runner_settings=_runner_settings_of(m) is not None)
    except FreezeError as exc:
        return problems + [str(exc)]
    if tree != m.get("candidate_tree"):
        problems.append("candidate_tree differs")
    plugin = m.get("plugin") or {}
    _diff_maps("plugin", plugin.get("files") or {}, gs["plugin"]["files"], problems)
    for key in ("file_count", "tree_sha256", "runtime_fingerprint",
                "plugin_json_version"):
        if plugin.get(key) != gs["plugin"][key]:
            problems.append("plugin.%s differs" % key)
    covered = m.get("covered") or {}
    for key in sorted(set(covered) | set(gs["covered"])):
        want = (covered.get(key) or {})
        got = gs["covered"].get(key) or {}
        _diff_maps("covered " + key, want.get("files") or {},
                   got.get("files") or {}, problems)
        if want.get("tree_sha256") != got.get("tree_sha256"):
            problems.append("covered %s tree_sha256 differs" % key)
    runners = m.get("runners") or {}
    checks = (
        ("models.agent_pins", (m.get("models") or {}).get("agent_pins"),
         gs["agent_pins"]),
        ("runners.b3.runner_settings", _runner_settings_of(m), gs["runner_settings"]),
        ("runners.holdout-eval.runner_settings",
         (runners.get("holdout-eval") or {}).get("runner_settings"),
         gs["runner_settings"]),
        ("runners.fix-harness.launch_model",
         (runners.get("fix-harness") or {}).get("launch_model"), gs["harness_launch"]),
        ("runners.fix-harness.probe_settings_fingerprint",
         (runners.get("fix-harness") or {}).get("probe_settings_fingerprint"),
         gs["probe_settings_fingerprint"]),
        ("runners.fix-harness.requirements_sha256",
         (runners.get("fix-harness") or {}).get("requirements_sha256"),
         gs["requirements_sha256"]),
        ("runners.fix-harness.kit", (runners.get("fix-harness") or {}).get("kit"),
         gs["harness_kit"]),
        ("runners.holdout-autopilot.kit",
         (runners.get("holdout-autopilot") or {}).get("kit"), gs["holdout_kit"]),
        ("runners.holdout-eval.kit", (runners.get("holdout-eval") or {}).get("kit"),
         gs["holdout_kit"]),
    )
    for label, want, got in checks:
        if want != got:
            problems.append("%s differs" % label)
    return problems


def _runner_settings_of(m):
    return ((m.get("runners") or {}).get("b3") or {}).get("runner_settings")


def show_lines(m):
    runners = m.get("runners") or {}
    plugin = m.get("plugin") or {}
    models = m.get("models") or {}
    lines = [
        "manifest_id: %s" % m.get("manifest_id"),
        "candidate: %s (tree %s)" % (m.get("candidate_sha"), m.get("candidate_tree")),
        "plugin: version %s, %s files, tree %s" % (
            plugin.get("plugin_json_version"), plugin.get("file_count"),
            plugin.get("tree_sha256")),
        "covered: %d prefixes, %d files" % (
            len(m.get("covered") or {}),
            sum(len(v.get("files") or {}) for v in (m.get("covered") or {}).values())),
        "top model: %s (%s)" % ((models.get("top") or {}).get("value"),
                                (models.get("top") or {}).get("source")),
        "agent pins: %s" % ", ".join("%s=%s" % kv for kv in
                                     sorted((models.get("agent_pins") or {}).items())),
        "native CLI: %s" % ((runners.get("b3") or {}).get("cli") or {}).get("version"),
        "harness SDK: %s, bundled CLI %s" % (
            (runners.get("fix-harness") or {}).get("sdk_version"),
            ((runners.get("fix-harness") or {}).get("bundled_cli") or {}).get("version")),
        "codex CLI: %s" % (m.get("codex") or {}).get("cli_version"),
        "runner settings: %s" % ("pinned" if _runner_settings_of(m) else "absent"),
    ]
    return lines


def _parser():
    p = argparse.ArgumentParser(prog="freeze_manifest.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--candidate", required=True)
    g.add_argument("--out", required=True)
    g.add_argument("--repo", default=os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.dirname(HERE)))))
    g.add_argument("--home")
    g.add_argument("--codex-home")
    g.add_argument("--harness-venv")
    g.add_argument("--previous")
    g.add_argument("--allow-missing-runner-settings", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("--manifest", required=True)
    v = sub.add_parser("verify-self")
    v.add_argument("--manifest", required=True)
    v.add_argument("--repo", default=os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.dirname(HERE)))))
    return p


def main(argv=None):
    try:
        args = _parser().parse_args(argv)
    except SystemExit:
        return 2  # usage error -> fail closed, never exit 0
    try:
        if args.cmd == "generate":
            m = generate(args.repo, args.candidate, home=args.home,
                         codex_home=args.codex_home, harness_venv=args.harness_venv,
                         previous=args.previous,
                         require_runner_settings=not args.allow_missing_runner_settings)
            write_manifest(args.out, m)
            print("wrote %s (manifest_id %s)" % (args.out, m["manifest_id"]))
            return 0
        if args.cmd == "show":
            m = _read_json(args.manifest, "manifest")
            if not isinstance(m, dict):
                print("manifest is missing or not a JSON object", file=sys.stderr)
                return 1
            print("\n".join(show_lines(m)))
            return 0
        problems = verify_self(args.repo, args.manifest)
        for line in problems:
            print(line, file=sys.stderr)
        if problems:
            print("VERIFY-SELF FAILED (%d problems)" % len(problems), file=sys.stderr)
            return 1
        print("verify-self ok")
        return 0
    except FreezeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
