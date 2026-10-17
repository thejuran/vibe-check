"""The shared pre-run identity check: is the environment a runner is about
to load exactly the environment the active freeze manifest pinned?

`verify(manifest, runner, ...)` observes the LIVE environment with the same
collector functions `freeze_manifest.generate` used, compares it against the
manifest and returns every difference as one named line. `[]` means launch;
anything else means stop. There is no override: no flag, no keyword, no
environment variable turns a class off. A collector that fails is a problem
line (`observe failed: ...`), never a pass.

Identity is content. A matching plugin.json version with one differing file
byte is a mismatch; version strings are reported as context only.

Runner profiles (the identity classes each runner actually loads):
  b3                plugin files, runtime fingerprint, native CLI, user-level
                    projection, gateway, process env, `.vibe-check.toml`
                    absence, runner settings, launch model, Codex, covered
                    trees, repo state
  holdout-eval      as b3, plus the holdout kit tree (the session routes
                    through the same model gateway)
  fix-harness       plugin snapshot, SDK version, bundled CLI, kit tree,
                    requirements.txt, process env handed to the SDK, launch
                    model, repo state
  holdout-autopilot holdout kit tree, native CLI, repo state

Repo state (every profile, and standalone as `candidate_guard`):
  1. the candidate is an ancestor of HEAD;
  2. every path changed since the candidate classifies as reporting-only
     under the PATH-MAP pinned AT the candidate;
  3. the plugin root and every covered path are clean in the working tree;
  4. the git tree at HEAD equals the pinned file maps byte for byte for the
     plugin root and every covered prefix (so a wrong PATH-MAP rule can never
     let a covered change through).

CLI:
  freeze_check.py verify --runner R [--manifest M] [--plugin-dir D]
      [--settings S] [--model M] [--clone-dir C] [--repo R]
      [--harness-venv V] [--home H] [--codex-home C]
  freeze_check.py candidate-guard --candidate C [--repo R]
Exit 0 match / 1 mismatch (stops) / 2 usage or unreadable manifest (stops).
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import freeze_common  # noqa: E402
import freeze_manifest as fm  # noqa: E402
import freeze_policy  # noqa: E402
from freeze_common import FreezeError  # noqa: E402

RUNNERS = ("b3", "fix-harness", "holdout-autopilot", "holdout-eval")
REPO_DEFAULT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(HERE))))
MANIFEST_DIR = "docs/design/freeze-v2.12"
MANIFEST_RE = re.compile(r"^FREEZE-MANIFEST-([0-9]+)\.json$")
SHORT = 12
DESIGN_PREFIX = "docs/design/"

# Working-tree walks skip what git ignores and no runner consumes.
WALK_EXCLUDES = (freeze_common.EXCLUDED_DIRS + (".venv",),
                 freeze_common.EXCLUDED_NAMES + (".DS_Store",),
                 freeze_common.EXCLUDED_SUFFIXES)

B3_COVERED_KEYS = (
    "docs/design/b3-ground-truth/b3-runner-v2.12",
    "docs/design/reachability-dev/RUN-PHASE54-live.md",
    "docs/design/reachability-dev/RUN-PHASE53-dev.md",
    "docs/design/reachability-dev/README.md",
    "docs/design/reachability-dev/CATCH-SITES-dev.json",
    "docs/design/b3-ground-truth/diffs",
    "docs/design/reachability-dev/cases",
    "docs/design/b3-ground-truth/ANSWER-KEY-*.md",
    "docs/design/b3-ground-truth/REPLAY-CATCH-MANIFEST-*.json",
    "docs/design/b3-ground-truth/SUPERSESSIONS-*.md",
    "docs/design/b3-ground-truth/ALLOWANCES-*.json",
    "docs/design/b3-ground-truth/CALIBRATION-*.md",
)

PROFILE_CLASSES = {
    "b3": ("plugin_files", "runtime_fingerprint", "native_cli", "user_level",
           "gateway", "process_env", "toml_absent", "runner_settings",
           "launch_model", "codex", "covered_trees", "repo_state"),
    "holdout-eval": ("plugin_files", "runtime_fingerprint", "native_cli",
                     "user_level", "gateway", "process_env", "toml_absent",
                     "runner_settings", "launch_model", "codex",
                     "covered_trees", "kit_tree", "repo_state"),
    "fix-harness": ("plugin_files", "sdk_version", "bundled_cli", "kit_tree",
                    "requirements", "process_env", "launch_model",
                    "repo_state"),
    "holdout-autopilot": ("kit_tree", "native_cli", "repo_state"),
}

KIT_KEYS = {
    "fix-harness": fm.HARNESS_KIT_PREFIXES,
    "holdout-autopilot": (fm.HOLDOUT_KIT_PREFIX,),
    "holdout-eval": (fm.HOLDOUT_KIT_PREFIX,),
}

PLUGIN_DIR_MISSING = "plugin dir not supplied"
SETTINGS_MISSING = "runner settings not supplied"
SETTINGS_UNPINNED = "runner settings not pinned in the manifest"
CLONE_DIR_MISSING = "clone dir not supplied"
MISMATCH_LINE = "IDENTITY MISMATCH — STOPPING"
MOVED_LINE = "CANDIDATE MOVED — STOPPING"

_SHAPE_VERSION = fm._VERSION_RE
_SHAPE_MODEL = fm._MODEL_RE
_SHAPE_WORD = r"^[a-z]{1,16}$"


class CheckResult:
    """The verdict of one check: `problems` ([] = launch), the manifest it
    was checked against, the digest of the live observation and the
    candidate commit."""

    def __init__(self, problems, manifest_id, check_digest, candidate_sha,
                 observed):
        self.problems = problems
        self.manifest_id = manifest_id
        self.check_digest = check_digest
        self.candidate_sha = candidate_sha
        self.observed = observed

    @property
    def ok(self):
        return not self.problems


# --------------------------------------------------------------------------- #
# Manifest loading
# --------------------------------------------------------------------------- #

def active_manifest(repo=REPO_DEFAULT):
    """Path of the highest-N FREEZE-MANIFEST-<N>.json; no manifest, no run."""
    d = os.path.join(repo, MANIFEST_DIR)
    best = None
    for name in (os.listdir(d) if os.path.isdir(d) else []):
        m = MANIFEST_RE.match(name)
        if m and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), name)
    if best is None:
        raise FreezeError("no freeze manifest under %s — no run" % MANIFEST_DIR)
    return os.path.join(d, best[1])


def load_manifest(path):
    """Read, schema-validate and id-check a manifest; FreezeError names the
    file on any problem (a tampered manifest never loads)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            m = json.load(fh)
    except (OSError, ValueError):
        raise FreezeError("manifest unreadable or not JSON: %s" % path)
    if not isinstance(m, dict):
        raise FreezeError("manifest is not a JSON object: %s" % path)
    try:
        fm.assert_no_secrets(m)
    except FreezeError as exc:
        raise FreezeError("manifest invalid: %s: %s" % (path, exc))
    if m["manifest_id"] != fm.manifest_id(m):
        raise FreezeError("manifest_id does not match the content of %s" % path)
    return m


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _short(h):
    return h[:SHORT] if isinstance(h, str) else "null"


def _shown(value, regex):
    """A value fit for a message: null, the value when it fits the allowed
    shape, else a marker (live values are not trusted to be secret-free)."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        value = "true" if value else "false"
    if isinstance(value, str) and re.match(regex, value):
        return value
    return "<outside the allowed shape>"


def _env_shown(key, value):
    if value is None:
        return "null"
    if fm._env_value_problem(key, value, key) is None:
        return value
    return "<outside the allowed shape>"


def _label(path):
    return path[len(DESIGN_PREFIX):] if path.startswith(DESIGN_PREFIX) else path


def _git_mode(full):
    if os.path.islink(full):
        return "120000"
    return "100755" if os.stat(full).st_mode & 0o100 else "100644"


def _live_map(root, excludes=freeze_common.EXCLUDES):
    """{rel: {"sha256", "mode"}} of a live directory (or {basename: ...} of a
    single file; {} when absent)."""
    if os.path.isfile(root) or os.path.islink(root):
        name = os.path.basename(root)
        sha = (freeze_common.sha256_bytes(os.readlink(root).encode("utf-8"))
               if os.path.islink(root) else freeze_common.sha256_file(root))
        return {name: {"sha256": sha, "mode": _git_mode(root)}}
    if not os.path.isdir(root):
        return {}
    files = freeze_common.live_files(root, excludes)
    return {rel: {"sha256": sha, "mode": _git_mode(os.path.join(root, rel))}
            for rel, sha in files.items()}


def _diff_file_maps(label_of, want, got):
    """R7 file lines: differs (content, then mode), extra, missing; sorted."""
    problems = []
    for rel in sorted(set(want) | set(got)):
        if rel not in got:
            problems.append("file missing: %s" % label_of(rel))
        elif rel not in want:
            problems.append("file extra: %s" % label_of(rel))
        else:
            w, g = want[rel], got[rel]
            if freeze_common.file_sha(w) != freeze_common.file_sha(g):
                problems.append("file differs: %s (manifest %s live %s)" % (
                    label_of(rel), _short(freeze_common.file_sha(w)),
                    _short(freeze_common.file_sha(g))))
            elif isinstance(w, dict) and isinstance(g, dict) \
                    and w.get("mode") != g.get("mode"):
                problems.append("file differs: %s (mode manifest %s live %s)" % (
                    label_of(rel), w.get("mode"), g.get("mode")))
    return problems


def _deep_diff(a, b, prefix="", depth=None):
    """Dotted keys where `a` and `b` differ. Recurses only while both sides
    are objects (and `depth` allows); lists and scalars compare whole."""
    if isinstance(a, dict) and isinstance(b, dict) and depth != 0:
        out = []
        for key in sorted(set(a) | set(b), key=str):
            sub = "%s.%s" % (prefix, key) if prefix else str(key)
            if key not in a or key not in b:
                out.append(sub)
            else:
                out += _deep_diff(a[key], b[key], sub,
                                  None if depth is None else depth - 1)
        return out
    return [] if a == b else [prefix]


def _covered_live(repo, key):
    """Live {rel: entry} for a covered key (prefix, or prefix/glob)."""
    prefix, pattern = key, None
    if "*" in os.path.basename(key):
        prefix, pattern = os.path.dirname(key), os.path.basename(key)
    root = os.path.join(repo, prefix)
    if pattern is None:
        files = _live_map(root, WALK_EXCLUDES)
        if os.path.isfile(root):
            return files
        return {rel: v for rel, v in files.items()
                if not fm._covered_excluded(prefix + "/" + rel)}
    rx = freeze_common.glob_to_regex(pattern)
    out = {}
    for name in sorted(os.listdir(root) if os.path.isdir(root) else []):
        full = os.path.join(root, name)
        if rx.match(name) and (os.path.isfile(full) or os.path.islink(full)):
            out.update(_live_map(full))
    return out


def _covered_full(key, rel):
    """Repo path of `rel` under covered key `key`. A single-file key maps
    its one entry (named by the basename) back to the key itself."""
    if "*" in os.path.basename(key):
        return os.path.dirname(key) + "/" + rel
    if rel == os.path.basename(key):
        return key
    return key + "/" + rel


def _compare_covered(manifest, repo, keys):
    problems = []
    observed = {}
    covered = manifest["covered"]
    for key in keys:
        if key not in covered:
            problems.append("file missing: %s (covered key not in manifest)"
                            % _label(key))
            continue
        live = _covered_live(repo, key)
        observed[key] = live
        problems += _diff_file_maps(
            lambda rel, k=key: _label(_covered_full(k, rel)),
            covered[key]["files"], live)
    return problems, observed


# --------------------------------------------------------------------------- #
# Identity classes: each returns (problems, observation)
# --------------------------------------------------------------------------- #

def _check_plugin_files(manifest, live):
    """Exact file set of the plugin dir the session loads. The file diff is
    computed before plugin.json is read: the version is context, never a
    pass condition."""
    if live["plugin_dir"] is None:
        return [PLUGIN_DIR_MISSING], None
    root = live["plugin_dir"]
    if not os.path.isdir(root):
        return ["file missing: plugin dir %s" % root], None
    got = _live_map(root)
    problems = _diff_file_maps(lambda rel: rel, manifest["plugin"]["files"], got)
    version = None
    pj = os.path.join(root, ".claude-plugin", "plugin.json")
    try:
        with open(pj, "r", encoding="utf-8") as fh:
            version = json.load(fh).get("version")
    except (OSError, ValueError, AttributeError):
        version = None
    live["plugin_map"] = got
    return problems, {"files": got,
                      "plugin_json_version": version if isinstance(version, str)
                      else None}


def _check_runtime_fingerprint(manifest, live):
    got = live.get("plugin_map")
    if got is None:
        if live["plugin_dir"] is None or not os.path.isdir(live["plugin_dir"]):
            return [], None  # already reported by plugin_files
        got = _live_map(live["plugin_dir"])
    fp = fm.runtime_fingerprint_of_map(got)
    want = manifest["plugin"]["runtime_fingerprint"]
    if fp != want:
        return ["file differs: runtime fingerprint (manifest %s live %s)"
                % (_short(want), _short(fp))], fp
    return [], fp


def _cli_problems(name, want, got):
    problems = []
    if want["version"] != got["version"]:
        problems.append("version differs: %s (manifest %s live %s)" % (
            name, want["version"], _shown(got["version"], _SHAPE_VERSION)))
    if want["sha256"] != got["sha256"]:
        if want["version"] == got["version"]:
            problems.append("binary differs: %s (same version string, sha256 "
                            "differs: manifest %s live %s)" % (
                                name, _short(want["sha256"]),
                                _short(got["sha256"])))
        else:
            problems.append("binary differs: %s (sha256 manifest %s live %s)" % (
                name, _short(want["sha256"]), _short(got["sha256"])))
    return problems


def _check_native_cli(manifest, live):
    got = fm._native_cli(live["home"], live["repo"])
    return _cli_problems("claude-code", manifest["runners"][live["runner"]]["cli"],
                         got), got


def _harness(live):
    if "harness" not in live:
        live["harness"] = fm._harness_runtime(live["repo"], live["harness_venv"],
                                              live["home"])
    return live["harness"]


def _check_sdk_version(manifest, live):
    sdk_version, _ = _harness(live)
    want = manifest["runners"]["fix-harness"]["sdk_version"]
    if sdk_version != want:
        return ["version differs: claude-agent-sdk (manifest %s live %s)" % (
            want, _shown(sdk_version, _SHAPE_VERSION))], sdk_version
    return [], sdk_version


def _check_bundled_cli(manifest, live):
    _, bundled = _harness(live)
    return _cli_problems("agent-sdk-bundled-claude",
                         manifest["runners"]["fix-harness"]["bundled_cli"],
                         bundled), bundled


def _check_requirements(manifest, live):
    path = os.path.join(live["repo"], fm.HARNESS_REQUIREMENTS)
    got = freeze_common.sha256_file(path) if os.path.isfile(path) else None
    want = manifest["runners"]["fix-harness"]["requirements_sha256"]
    if got != want:
        return ["file differs: %s (manifest %s live %s)" % (
            _label(fm.HARNESS_REQUIREMENTS), _short(want), _short(got))], got
    return [], got


def _user_level(live):
    if "user_level" not in live:
        live["user_level"] = fm.user_level(live["home"], live["repo"])
    return live["user_level"]


# Per-key granularity for the projection's map-shaped fields.
_USER_LEVEL_DEPTH = {"env": 1, "enabled_plugins": 1, "hook_scripts": 1}


def _check_user_level(manifest, live):
    """Every field of the D-26 projection, driven by the manifest's field
    list (plus any field only the live side has), so no field can be
    skipped silently."""
    want = manifest["runners"][live["runner"]]["user_level"]
    got, _ = _user_level(live)
    problems = []
    for field in sorted(set(want) | set(got)):
        if field not in want or field not in got:
            problems.append("setting differs: %s" % field)
            continue
        depth = _USER_LEVEL_DEPTH.get(field, 0)
        for key in _deep_diff(want[field], got[field], field, depth):
            if field == "env" and key.startswith("env."):
                name = key[4:]
                problems.append("setting differs: %s (manifest %s live %s) "
                                "[user settings]" % (
                                    key, _env_shown(name, want["env"].get(name)),
                                    _env_shown(name, got["env"].get(name))))
            else:
                problems.append("setting differs: %s" % key)
    return problems, got


def _check_gateway(manifest, live):
    _, settings = _user_level(live)
    got = fm._gateway(live["home"], settings)
    want = manifest["runners"]["b3"]["gateway"]
    return ["setting differs: gateway.%s" % k[len("gateway."):]
            for k in _deep_diff(want, got, "gateway")], got


def _process_env_baseline(manifest):
    # The manifest records the generator's process-env projection once
    # (freeze_policy.PROCESS_ENV_FIELD); every runner's process env is held to
    # it, and the detection gates' inheritance binds the same field.
    present, value = freeze_policy._field_value(manifest,
                                                freeze_policy.PROCESS_ENV_FIELD)
    if not present or not isinstance(value, dict):
        raise FreezeError("manifest has no process-env baseline (%s)"
                          % freeze_policy.PROCESS_ENV_FIELD)
    return value


def _check_process_env(manifest, live):
    want = _process_env_baseline(manifest)
    got = fm.env_projection(live["env"])
    problems = []
    for key in fm.ENV_ALLOWLIST:
        if want.get(key) != got.get(key):
            problems.append("setting differs: env.%s (manifest %s live %s) "
                            "[process env]" % (key, _env_shown(key, want.get(key)),
                                               _env_shown(key, got.get(key))))
    return problems, got


def _check_toml_absent(manifest, live):
    clone = live["clone_dir"]
    if clone is None:
        # Fails closed for every profile that has this class: without the dir
        # the session runs in, the class cannot be checked.
        return [CLONE_DIR_MISSING], None
    present = os.path.exists(os.path.join(clone, ".vibe-check.toml"))
    source = manifest["models"]["top"]["source"]
    if source != "toml" and present:
        return ["setting differs: .vibe-check.toml present (manifest top model "
                "source %s)" % source], present
    if source == "toml" and not present:
        return ["setting differs: .vibe-check.toml absent (manifest top model "
                "source toml)"], present
    return [], present


_SCRIPT_TOKEN_RE = re.compile(r'"([^"]*)"|\'([^\']*)\'|(\S+)')


def _normalize_statusline(settings, template, rs, problems):
    """Replace the runner directory in statusLine.command with `<RUNNER>`
    when the referenced capture script has the pinned bytes — the ONLY
    normalization. A capture script with other bytes is a file difference
    and the command is left as is."""
    placeholder = rs["substitution"]["placeholder"]
    t_cmd = ((template.get("statusLine") or {}).get("command")
             if isinstance(template.get("statusLine"), dict) else None)
    line = settings.get("statusLine")
    if not isinstance(t_cmd, str) or not isinstance(line, dict) \
            or not isinstance(line.get("command"), str):
        return settings
    names = [m.group(0)[len(placeholder) + 1:]
             for m in re.finditer(re.escape(placeholder) + r"/[^\s\"']+", t_cmd)]
    cmd = line["command"]
    for m in _SCRIPT_TOKEN_RE.finditer(cmd):
        token = next(g for g in m.groups() if g is not None)
        if not os.path.isabs(token) or not any(token.endswith("/" + n)
                                               for n in names):
            continue
        if not os.path.isfile(token):
            continue
        sha = freeze_common.sha256_file(token)
        if sha != rs["statusline_script_sha256"]:
            problems.append("file differs: runner-settings.statusLine script "
                            "(manifest %s live %s)" % (
                                _short(rs["statusline_script_sha256"]), _short(sha)))
            return settings
        out = json.loads(json.dumps(settings))
        out["statusLine"]["command"] = cmd.replace(os.path.dirname(token),
                                                   placeholder)
        return out
    return settings


def _check_runner_settings(manifest, live):
    rs = manifest["runners"][live["runner"]]["runner_settings"]
    if rs is None:
        return [SETTINGS_UNPINNED], None
    path = live["settings_path"]
    if path is None:
        return [SETTINGS_MISSING], None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            settings = json.load(fh)
    except (OSError, ValueError):
        return ["file missing: runner settings unreadable or not JSON: %s"
                % path], None
    if not isinstance(settings, dict):
        return ["setting differs: runner-settings (not a JSON object)"], None
    blob = freeze_common.blob_at(live["repo"], manifest["candidate_sha"],
                                 rs["template_path"])
    if blob is None:
        return ["file missing: runner settings template at candidate: %s"
                % rs["template_path"]], None
    template = json.loads(blob.decode("utf-8"))
    problems = []
    if freeze_common.canonical_sha256(template) != rs["template_canonical_sha256"]:
        problems.append("file differs: runner settings template at candidate")
    normalized = _normalize_statusline(settings, template, rs, problems)
    got = freeze_common.canonical_sha256(normalized)
    if got != rs["template_canonical_sha256"]:
        diffs = _deep_diff(template, normalized)
        problems += ["setting differs: runner-settings.%s" % k for k in diffs]
        if not diffs:
            problems.append("setting differs: runner-settings (canonical sha256 "
                            "manifest %s live %s)" % (
                                _short(rs["template_canonical_sha256"]), _short(got)))
    return problems, {"canonical_sha256": got}


def _check_launch_model(manifest, live):
    want = manifest["runners"][live["runner"]]["launch_model"]["value"]
    got = live["launch_model"]
    if got != want:
        return ["setting differs: launch_model (manifest %s live %s)" % (
            want, _shown(got, _SHAPE_MODEL))], got
    return [], got


def _check_codex(manifest, live):
    got = fm._codex(live["home"], live["codex_home"], live["repo"],
                    manifest["candidate_sha"])
    want = manifest["codex"]
    problems = []
    if want["cli_version"] != got["cli_version"]:
        problems.append("version differs: codex (manifest %s live %s)" % (
            want["cli_version"], _shown(got["cli_version"], _SHAPE_VERSION)))
    for key in sorted(set(want["config"]) | set(got["config"])):
        w, g = want["config"].get(key), got["config"].get(key)
        if w != g:
            regex = _SHAPE_MODEL if key == "model" else _SHAPE_WORD
            problems.append("setting differs: codex.config.%s (manifest %s live %s)"
                            % (key, _shown(w, regex), _shown(g, regex)))
    if want["config_sha256"] != got["config_sha256"]:
        problems.append("file differs: codex-config (manifest %s live %s)" % (
            _short(want["config_sha256"]), _short(got["config_sha256"])))
    wc, gc = want["companion"], got["companion"]
    if (wc is None) != (gc is None):
        problems.append("file %s: codex-companion" % ("missing" if gc is None
                                                      else "extra"))
    elif wc is not None:
        if wc["tree_sha256"] != gc["tree_sha256"]:
            problems.append("file differs: codex-companion (manifest %s live %s)"
                            % (_short(wc["tree_sha256"]), _short(gc["tree_sha256"])))
        if wc["version"] != gc["version"]:
            problems.append("version differs: codex-companion (manifest %s live %s)"
                            % (wc["version"], _shown(gc["version"], _SHAPE_VERSION)))
        if wc["gitCommitSha"] != gc["gitCommitSha"]:
            problems.append("version differs: codex-companion gitCommitSha")
    if want["project_codex_dir_absent"] != got["project_codex_dir_absent"]:
        problems.append("setting differs: codex.project_codex_dir_absent "
                        "(manifest %s live %s)" % (
                            _shown(want["project_codex_dir_absent"], r"^.*$"),
                            _shown(got["project_codex_dir_absent"], r"^.*$")))
    return problems, got


def _check_covered_trees(manifest, live):
    return _compare_covered(manifest, live["repo"], B3_COVERED_KEYS)


def _check_kit_tree(manifest, live):
    runner = live["runner"]
    problems, observed = _compare_covered(manifest, live["repo"], KIT_KEYS[runner])
    combined = {}
    for key, files in observed.items():
        for rel, entry in files.items():
            combined[key + "/" + rel] = entry
    tree = freeze_common.tree_sha256_of_map(combined)
    want = manifest["runners"][runner]["kit"]["tree_sha256"]
    if not problems and tree != want:
        problems.append("file differs: %s kit tree (manifest %s live %s)" % (
            runner, _short(want), _short(tree)))
    return problems, {"tree_sha256": tree}


def _check_repo_state(manifest, live):
    return _repo_state(live["repo"], manifest["candidate_sha"],
                       manifest["plugin"]["files"],
                       {k: v["files"] for k, v in manifest["covered"].items()})


CHECKS = {
    "plugin_files": _check_plugin_files,
    "runtime_fingerprint": _check_runtime_fingerprint,
    "native_cli": _check_native_cli,
    "bundled_cli": _check_bundled_cli,
    "sdk_version": _check_sdk_version,
    "requirements": _check_requirements,
    "user_level": _check_user_level,
    "gateway": _check_gateway,
    "process_env": _check_process_env,
    "toml_absent": _check_toml_absent,
    "runner_settings": _check_runner_settings,
    "launch_model": _check_launch_model,
    "codex": _check_codex,
    "covered_trees": _check_covered_trees,
    "kit_tree": _check_kit_tree,
    "repo_state": _check_repo_state,
}


# --------------------------------------------------------------------------- #
# Repo state
# --------------------------------------------------------------------------- #

def _covered_pathspecs():
    specs = [fm.PLUGIN_ROOT]
    for prefix, pattern in fm.COVERED:
        specs.append(prefix + "/" + pattern if pattern else prefix)
    return specs


def _is_covered_path(path):
    if path == fm.PLUGIN_ROOT or path.startswith(fm.PLUGIN_ROOT + "/"):
        return True
    for prefix, pattern in fm.COVERED:
        if pattern is None:
            if path == prefix or path.startswith(prefix + "/"):
                return not fm._covered_excluded(path)
        elif os.path.dirname(path) == prefix and \
                freeze_common.glob_to_regex(pattern).match(os.path.basename(path)):
            return True
    return False


def _walk_excluded(path):
    return freeze_common.is_excluded_rel(path, WALK_EXCLUDES)


def _z_paths(raw):
    return [p.decode("utf-8") for p in raw.split(b"\0") if p]


def _cats_text(cats):
    return "[%s]" % ", ".join(c for c in freeze_policy.CATEGORIES if c in cats)


def _repo_state(repo, candidate, want_plugin, want_covered):
    """The four-step repo rule. `want_*` are the pinned file maps."""
    problems = []
    observed = {"candidate_sha": candidate}
    head = freeze_common.git(repo, "rev-parse", "--verify",
                             "HEAD^{commit}").decode().strip()
    observed["head"] = head
    # (1) candidate is an ancestor of HEAD
    try:
        freeze_common.git(repo, "merge-base", "--is-ancestor", candidate, head)
        ancestor = True
    except FreezeError:
        ancestor = False
        problems.append("repo: HEAD %s is not a descendant of candidate %s"
                        % (head, candidate))
    observed["descendant_commits"] = int(freeze_common.git(
        repo, "rev-list", "--count", "%s..%s" % (candidate, head)).decode().strip()) \
        if ancestor else None
    # (2) every changed path is reporting-only under the map pinned at C
    changed = _z_paths(freeze_common.git(repo, "diff", "--name-only", "-z",
                                         "--no-renames", candidate, head))
    observed["changed"] = changed
    if changed:
        blob = freeze_common.blob_at(repo, candidate, freeze_policy.MAP_SELF_PATH)
        path_map = None
        if blob is None:
            problems.append("repo: PATH-MAP absent at candidate")
        else:
            try:
                path_map = freeze_policy.validate_path_map(
                    json.loads(blob.decode("utf-8")))
            except (ValueError, FreezeError):
                problems.append("repo: PATH-MAP at candidate is invalid")
        if path_map is not None:
            for path, cats in sorted(freeze_policy.classify(changed,
                                                            path_map).items()):
                if cats & set(freeze_policy.RERUN_CATEGORIES):
                    problems.append("repo: non-reporting change after "
                                    "candidate: %s %s" % (path, _cats_text(cats)))
        else:
            for path in changed:
                problems.append("repo: non-reporting change after candidate: "
                                "%s %s" % (path, _cats_text(
                                    set(freeze_policy.RERUN_CATEGORIES))))
    # (3) covered paths clean in the working tree
    status = freeze_common.git(repo, "status", "--porcelain", "-z",
                               "--no-renames", "--untracked-files=all", "--",
                               *_covered_pathspecs())
    dirty = []
    for entry in _z_paths(status):
        path = entry[3:]
        if _is_covered_path(path) and not _walk_excluded(path):
            dirty.append(path)
    for path in sorted(set(dirty)):
        problems.append("repo: uncommitted change in covered path: %s" % path)
    # (4) covered-artifact equality at HEAD, independent of classification
    differs = set()
    at_head = freeze_common.tree_files_at(repo, head, fm.PLUGIN_ROOT)
    for rel in set(at_head) | set(want_plugin):
        if at_head.get(rel) != want_plugin.get(rel):
            differs.add(fm.PLUGIN_ROOT + "/" + rel)
    covered_head = fm.covered_tree_files(repo, head)
    for key in set(covered_head) | set(want_covered):
        got = (covered_head.get(key) or {}).get("files") or {}
        want = want_covered.get(key) or {}
        for rel in set(got) | set(want):
            if got.get(rel) != want.get(rel):
                differs.add(_covered_full(key, rel))
    for path in sorted(differs):
        problems.append("repo: covered artifact differs at HEAD: %s" % path)
    return problems, observed


def candidate_guard(repo, candidate):
    """The repo rule computed directly from `candidate` (no manifest needed):
    [] when HEAD descends from it by reporting-only commits and every covered
    artifact is unchanged."""
    problems, _ = _candidate_guard(repo, candidate)
    return problems


def _candidate_guard(repo, candidate):
    sha, _ = freeze_common.resolve_rev(repo, candidate)
    want_plugin = fm.expected_plugin_files(repo, sha)
    want_covered = {k: v["files"]
                    for k, v in fm.covered_tree_files(repo, sha).items()}
    return _repo_state(repo, sha, want_plugin, want_covered)


# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #

def verify(manifest, runner, plugin_dir=None, settings_path=None,
           launch_model=None, clone_dir=None, repo=None, env=None, home=None,
           codex_home=None, harness_venv=None):
    """Compare the live environment `runner` will load against `manifest`.
    Returns a CheckResult; `problems == []` only on an exact match."""
    home, codex_home = freeze_common.resolve_homes(home, codex_home)
    if runner not in RUNNERS:
        raise FreezeError("unknown runner: %r (one of %s)" % (runner,
                                                               ", ".join(RUNNERS)))
    live = {
        "runner": runner, "plugin_dir": plugin_dir,
        "settings_path": settings_path, "launch_model": launch_model,
        "clone_dir": clone_dir, "repo": repo or REPO_DEFAULT,
        "env": dict(os.environ) if env is None else dict(env),
        "home": home, "codex_home": codex_home, "harness_venv": harness_venv,
    }
    problems = []
    observed = {"runner": runner, "manifest_id": manifest["manifest_id"]}
    for name in PROFILE_CLASSES[runner]:
        try:
            found, obs = CHECKS[name](manifest, live)
        except FreezeError as exc:
            found, obs = ["observe failed: %s: %s" % (name, exc)], None
        except Exception as exc:  # noqa: BLE001 - fail closed on any collector error
            found, obs = ["observe failed: %s: %s" % (name, type(exc).__name__)], None
        problems += found
        observed[name] = obs
    digest = freeze_common.canonical_sha256(observed)
    return CheckResult(problems, manifest["manifest_id"], digest,
                       manifest["candidate_sha"], observed)


def stamp_lines(result):
    """The three identity lines every run result stores."""
    return ["manifest_id: %s" % result.manifest_id,
            "check_digest: %s" % result.check_digest,
            "candidate_sha: %s" % result.candidate_sha]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

class _Parser(argparse.ArgumentParser):
    """ArgumentParser with a public read-only view of its option strings, so
    the no-override property (no force/skip/override/allow/ignore option)
    can be asserted by introspection. Subparsers inherit the class."""

    @property
    def option_string_actions(self):
        return dict(self._option_string_actions)


def build_parser():
    p = _Parser(prog="freeze_check.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--runner", required=True, choices=RUNNERS)
    v.add_argument("--manifest")
    v.add_argument("--plugin-dir")
    v.add_argument("--settings")
    v.add_argument("--model")
    v.add_argument("--clone-dir")
    v.add_argument("--repo", default=REPO_DEFAULT)
    v.add_argument("--harness-venv")
    v.add_argument("--home")
    v.add_argument("--codex-home")
    g = sub.add_parser("candidate-guard")
    g.add_argument("--candidate", required=True)
    g.add_argument("--repo", default=REPO_DEFAULT)
    return p


def _main_verify(args):
    try:
        path = args.manifest or active_manifest(args.repo)
        manifest = load_manifest(path)
    except FreezeError as exc:
        print(str(exc), file=sys.stderr)
        print(MISMATCH_LINE, file=sys.stderr)
        return 2
    result = verify(manifest, args.runner, plugin_dir=args.plugin_dir,
                    settings_path=args.settings, launch_model=args.model,
                    clone_dir=args.clone_dir, repo=args.repo,
                    home=args.home, codex_home=args.codex_home,
                    harness_venv=args.harness_venv)
    if result.problems:
        for line in result.problems:
            print(line)
        print(MISMATCH_LINE)
        return 1
    print("IDENTITY OK manifest_id=%s check_digest=%s candidate_sha=%s" % (
        result.manifest_id, result.check_digest, result.candidate_sha))
    return 0


def _main_guard(args):
    try:
        problems, observed = _candidate_guard(args.repo, args.candidate)
    except FreezeError as exc:
        print(str(exc))
        print(MOVED_LINE)
        return 1
    if problems:
        for line in problems:
            print(line)
        print(MOVED_LINE)
        return 1
    print("CANDIDATE OK candidate=%s head=%s descendant_commits=%d "
          "(reporting-only)" % (observed["candidate_sha"], observed["head"],
                                observed["descendant_commits"]))
    return 0


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit:
        return 2  # usage error -> fail closed, never exit 0
    try:
        if args.cmd == "verify":
            return _main_verify(args)
        return _main_guard(args)
    except FreezeError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
