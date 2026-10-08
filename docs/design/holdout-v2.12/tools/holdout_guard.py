"""holdout_guard.py — the fail-closed PreToolUse deny hook for the sealed holdout.

The v2.12 holdout lives in ~/.vibe-check-holdout. Tuning sessions (the main
thread, every subagent, every plugin's agents, MCP tools) must never reach it.
`classify(tool_name, tool_input)` answers one question for a tool call: could
this call read, list, search, copy or write anything under the holdout root?
Anything it cannot prove clear is refused. This is a barrier, not proof;
encryption is the control. The hook narrows the accidental paths; the sealed
files stay encrypted at rest with an owner-held key.

Contract (fail CLOSED on every ambiguity):
  - four ordered deny tests, each a separately named function:
      1. name test (`_name_hit`): NFC + casefold, and for command tools the
         characters ' " and backslash are deleted first, then the token
         `vibe-check-holdout` anywhere in the value denies (this also catches
         the Claude transcript slug and the scratchpad slug)
      2. resolution test (`_resolves_under`): ~, $HOME and ${HOME} are
         expanded, then realpath; equal to or under the root denies (catches
         pre-existing symlinks into the root)
      3. glob test (`_glob_hit`): a path component holding * ? [ or {..}
         that can match `.vibe-check-holdout` under shell dot rules denies
      4. ancestor-recursion test (`_ancestor_recursion`): a recursive reader
         (Grep/Glob tools; find, grep -r, rg, du, tar, rsync, cp -r, ls -R,
         zip -r, tree, fd) pointed at an ancestor of the root denies
  - fields scanned: file_path / notebook_path for file tools, path + glob for
    Grep, path + pattern for Glob, command for Bash / PowerShell / Monitor,
    every string (recursively) for every other tool (mcp__*, WebFetch, LS,
    unknown). Never scanned: Write content, Edit old/new strings, MultiEdit
    edits, NotebookEdit new_source, Grep pattern (a regex, not a path), and
    Agent / Task / TodoWrite / SendMessage / AskUserQuestion / Skill inputs
    (a subagent's own tool calls pass through this hook)
  - malformed stdin, a non-dict payload, a non-string tool_name, a non-dict
    tool_input, an unknown role, or any internal error: deny (exit 2)
  - reasons are FIXED strings that never echo the command or the path
  - no agent_id filter: every caller is guarded
  - the root is a constant; there is no override of any kind
  - the hook path writes no files

Roles (`hook --role`):
  - tuning (default): protects the holdout root
  - finder / xcheck: the isolated holdout sessions; they may read the holdout
    but not the tuning side (the repo, the marketplace clone, ~/.claude,
    ~/.codex, ~/.b3, ~/.vibe-check-snapshots); name + resolution + ancestor
  - `--protect PATH` (repeatable) adds roots for every role, denied by the
    resolution and ancestor tests

Residuals (what this hook does NOT stop):
  - deliberate obfuscation: variable concatenation (`d=.vibe-check-hol;
    cat ~/${d}dout`), command substitution, interpreter-built strings
  - recursive reads of an ancestor are caught only for the listed readers,
    and relative paths resolve against the hook's working directory (a Grep
    or Glob with no path, run from $HOME, is not caught)
  - Codex and any non-Claude process; linked worktrees or disposable copies
    without the user-level install
  - the hook fails OPEN when python3 is missing, the script path is wrong, or
    the hook times out; `check-install` and the SessionStart self-check exist
    for that reason
  - dotglob: a bare `*` component (`~/*`) is not treated as reaching a
    dotfile, which is wrong when the shell has dotglob on
  - false positives are accepted: a sed/grep expression whose text happens to
    match `.vibe-check-holdout` as a glob is refused

CLI (python3 holdout_guard.py <subcommand>):
  hook [--role tuning|finder|xcheck] [--protect PATH ...]
                     PreToolUse hook; stdin = the tool-call JSON.
                     exit 0 allow | 2 deny (+ one fixed stderr line).
  install (--repo ROOT | --user)
                     merge the hook, a SessionStart self-check and the deny
                     rules into ROOT/.claude/settings.local.json or
                     ~/.claude/settings.json; idempotent, atomic, keeps every
                     other entry; first write keeps a .pre-holdout.bak copy.
  uninstall (--repo ROOT | --user)
                     remove exactly what install added.
  check-install [--settings PATH ...] [--quiet-ok]
                     verify the install and run a live probe; exit 0 OK | 1.

I/O: stdlib only. The module's full import set is {argparse, fnmatch, json,
os, re, sys, unicodedata}; it never imports subprocess, shutil or socket.
"""

import argparse
import fnmatch
import json
import os
import re
import sys
import unicodedata

HOLDOUT_TOKEN = "vibe-check-holdout"
HOLDOUT_NAME = "." + HOLDOUT_TOKEN
HOLDOUT_ROOT = os.path.expanduser("~/.vibe-check-holdout")
TUNING_PROTECTED = (
    "~/turingmind-code-review",
    "~/thejuran-marketplace",
    "~/.claude",
    "~/.codex",
    "~/.b3",
    "~/.vibe-check-snapshots",
)

REASON_HOLDOUT = ("Blocked: this tool call reaches the sealed holdout folder "
                  "(v2.12 barrier).\n")
REASON_INTERNAL = ("Blocked: holdout guard could not classify the call "
                   "(fail closed).\n")
REASON_PROTECTED = ("Blocked: this isolated session may not reach tuning-side "
                    "files.\n")

ROLES = ("tuning", "finder", "xcheck")

PATH_FIELDS = {
    "Read": ("file_path",),
    "Edit": ("file_path",),
    "Write": ("file_path",),
    "MultiEdit": ("file_path",),
    "NotebookEdit": ("notebook_path",),
    "Grep": ("path", "glob"),
    "Glob": ("path", "pattern"),
}
COMMAND_TOOLS = frozenset({"Bash", "PowerShell", "Monitor"})
SKIP_TOOLS = frozenset({"Agent", "Task", "TodoWrite", "SendMessage",
                        "AskUserQuestion", "Skill"})
SEARCH_TOOLS = frozenset({"Grep", "Glob"})

GLOB_CHARS = "*?[{"
QUOTE_CHARS = "'\"\\"
MAX_DEPTH = 64

_SEGMENT_SPLIT = re.compile(r"\n|;|&&|\|\||\||&")
_TOKEN_SPLIT = re.compile(r"[\s<>()`]+")
_BRACE = re.compile(r"\{([^{}]*)\}")

ALWAYS_RECURSIVE = frozenset({"find", "rg", "du", "tar", "rsync", "tree",
                              "fd", "ag"})
FLAG_RECURSIVE = {
    "grep": ("rR", ("--recursive", "--dereference-recursive")),
    "egrep": ("rR", ("--recursive", "--dereference-recursive")),
    "fgrep": ("rR", ("--recursive", "--dereference-recursive")),
    "cp": ("rRa", ("--recursive", "--archive")),
    "ls": ("R", ("--recursive",)),
    "zip": ("r", ("--recurse-paths",)),
}


class GuardError(Exception):
    """A settings operation that cannot proceed; message is fixed text."""


# --------------------------------------------------------------------------- #
# Classifier (pure apart from realpath lookups; never raises via classify)
# --------------------------------------------------------------------------- #

def _norm(s):
    return unicodedata.normalize("NFC", s).casefold()


def _strip_quotes(s):
    for ch in QUOTE_CHARS:
        s = s.replace(ch, "")
    return s


def _expand(token):
    home = os.path.expanduser("~")
    t = token.replace("${HOME}", home).replace("$HOME", home)
    if t == "~" or t.startswith("~/"):
        t = home + t[1:]
    elif t.startswith("~"):
        t = os.path.expanduser(t)
    return t


def _forms(path):
    """Comparable forms of a path: normalized absolute and realpath."""
    expanded = _expand(path)
    return {_norm(os.path.normpath(os.path.abspath(expanded))),
            _norm(os.path.realpath(expanded))}


def _under(path, root):
    if path == root:
        return True
    return path.startswith(root.rstrip("/") + "/")


def _name_hit(value, strip_quotes=False, tokens=(HOLDOUT_TOKEN,)):
    if not value:
        return False
    s = _norm(_strip_quotes(value) if strip_quotes else value)
    return any(_norm(t) in s for t in tokens)


def _resolves_under(value, roots):
    if not value:
        return False
    paths = _forms(value)
    for root in roots:
        for r in _forms(root):
            if any(_under(p, r) for p in paths):
                return True
    return False


def _brace_alts(component):
    m = _BRACE.search(component)
    if not m or "," not in m.group(1):
        return [component]
    head, tail = component[:m.start()], component[m.end():]
    return [head + part + tail for part in m.group(1).split(",")]


def _glob_hit(value):
    if not value:
        return False
    for comp in re.split(r"[\s/]+", value):
        if not comp or not any(c in comp for c in GLOB_CHARS):
            continue
        for alt in _brace_alts(comp):
            a = _norm(alt)
            # Shell dot rule: only a component that starts with . (or a
            # bracket / ? — fail closed) can reach a dotfile.
            if a[:1] in ".[?" and fnmatch.fnmatchcase(HOLDOUT_NAME, a):
                return True
    return False


def _literal_prefix(value):
    comps = value.split("/")
    kept = []
    for comp in comps:
        if any(c in comp for c in GLOB_CHARS):
            break
        kept.append(comp)
    prefix = "/".join(kept)
    if not prefix and value.startswith("/"):
        prefix = "/"
    return prefix


def _hits_ancestor(token, roots):
    if not token:
        return False
    paths = _forms(token)
    for root in roots:
        for r in _forms(root):
            if any(_under(r, p) for p in paths):
                return True
    return False


def _is_recursive(words):
    names = [os.path.basename(w) for w in words]
    if any(n in ALWAYS_RECURSIVE for n in names):
        return True
    shorts = "".join(w[1:] for w in words
                     if w.startswith("-") and not w.startswith("--"))
    longs = {w.split("=", 1)[0] for w in words if w.startswith("--")}
    for n in names:
        if n in FLAG_RECURSIVE:
            chars, long_flags = FLAG_RECURSIVE[n]
            if any(c in shorts for c in chars) or longs & set(long_flags):
                return True
    return False


def _ancestor_recursion(tool, tool_input, value, roots):
    if not value:
        return False
    if tool in SEARCH_TOOLS:
        return _hits_ancestor(_literal_prefix(value), roots)
    if tool not in COMMAND_TOOLS:
        return False
    for segment in _SEGMENT_SPLIT.split(_strip_quotes(value)):
        words = [w for w in _TOKEN_SPLIT.split(segment) if w]
        if not _is_recursive(words):
            continue
        for w in words:
            if w.startswith("-"):
                if "=" not in w:
                    continue
                w = w.split("=", 1)[1]
            if _hits_ancestor(w, roots):
                return True
    return False


def _all_strings(obj, depth=0):
    if depth > MAX_DEPTH:
        raise ValueError("tool_input nested too deeply")
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                yield k
            for s in _all_strings(v, depth + 1):
                yield s
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            for s in _all_strings(v, depth + 1):
                yield s


def _command_paths(command):
    """Path-like tokens of a command (quotes already stripped)."""
    out = []
    for w in _TOKEN_SPLIT.split(command):
        for part in w.split("="):
            if "/" in part or part.startswith("~") or part.startswith("$"):
                out.append(part)
    return out


def _looks_like_path(s):
    return "/" in s or s.startswith("~") or s.startswith("$")


def _guards(role, roots, extra_protect):
    if role == "tuning":
        guards = [{"names": (HOLDOUT_TOKEN,), "glob": True,
                   "roots": tuple(roots) if roots else (HOLDOUT_ROOT,),
                   "reason": REASON_HOLDOUT}]
    else:
        guards = [{"names": tuple(os.path.basename(p)
                                  for p in TUNING_PROTECTED),
                   "glob": False,
                   "roots": (tuple(roots) if roots else
                             tuple(os.path.expanduser(p)
                                   for p in TUNING_PROTECTED)),
                   "reason": REASON_PROTECTED}]
    extra = tuple(os.path.expanduser(p) for p in (extra_protect or ()) if p)
    if extra:
        guards.append({"names": (), "glob": False, "roots": extra,
                       "reason": REASON_PROTECTED})
    return guards


def _classify(tool_name, tool_input, role="tuning", roots=None,
              extra_protect=()):
    if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
        return True, REASON_INTERNAL
    if role not in ROLES:
        return True, REASON_INTERNAL
    if tool_name in SKIP_TOOLS:
        return False, ""
    is_command = tool_name in COMMAND_TOOLS
    if is_command or tool_name in PATH_FIELDS:
        fields = ("command",) if is_command else PATH_FIELDS[tool_name]
        values = []
        for field in fields:
            v = tool_input.get(field)
            if v is None:
                continue
            if not isinstance(v, str):
                return True, REASON_INTERNAL
            values.append(v)
    else:
        values = list(_all_strings(tool_input))
    for value in values:
        for guard in _guards(role, roots, extra_protect):
            reason = guard["reason"]
            if guard["names"] and _name_hit(value, is_command, guard["names"]):
                return True, reason
            if is_command:
                candidates = _command_paths(_strip_quotes(value))
            elif tool_name in PATH_FIELDS:
                candidates = [value]
            else:
                candidates = [value] if _looks_like_path(value) else []
            for c in candidates:
                if _resolves_under(c, guard["roots"]):
                    return True, reason
            if guard["glob"] and _glob_hit(
                    _strip_quotes(value) if is_command else value):
                return True, reason
            if _ancestor_recursion(tool_name, tool_input, value,
                                   guard["roots"]):
                return True, reason
    return False, ""


def classify(tool_name, tool_input, role="tuning", roots=None,
             extra_protect=()):
    """Could this tool call reach a protected root? -> (deny, reason).

    Never raises: any internal error denies with REASON_INTERNAL.
    """
    try:
        return _classify(tool_name, tool_input, role=role, roots=roots,
                         extra_protect=extra_protect)
    except Exception:  # noqa: BLE001 — fail closed on any classifier defect
        return _guard_error_verdict()


def _guard_error_verdict():
    return True, REASON_INTERNAL


def hook_main(stdin_text, role="tuning", extra_protect=(), err=None):
    """PreToolUse decision -> 0 allow | 2 deny (one fixed line on `err`)."""
    out = err if err is not None else sys.stderr
    try:
        data = json.loads(stdin_text)
        if not isinstance(data, dict):
            deny, reason = True, REASON_INTERNAL
        else:
            tool_name = data.get("tool_name")
            tool_input = data.get("tool_input")
            if not isinstance(tool_name, str) \
                    or not isinstance(tool_input, dict):
                deny, reason = True, REASON_INTERNAL
            else:
                deny, reason = classify(tool_name, tool_input, role=role,
                                        extra_protect=extra_protect)
    except Exception:  # noqa: BLE001 — fail closed: a crashed guard must not open
        deny, reason = _guard_error_verdict()
    if not deny:
        return 0
    out.write(reason or REASON_INTERNAL)
    return 2


# --------------------------------------------------------------------------- #
# Settings install / verification
# --------------------------------------------------------------------------- #

DENY_RULES = [
    "Read(~/.vibe-check-holdout)",
    "Read(~/.vibe-check-holdout/**)",
    "Edit(~/.vibe-check-holdout/**)",
    "Read(~/.claude/projects/*vibe-check-holdout*/**)",
]
SCRIPT_BASENAME = "holdout_guard.py"
PROBE_PAYLOAD = ('{"tool_name":"Read","tool_input":'
                 '{"file_path":"~/.vibe-check-holdout/probe"}}')
MSG_UNREADABLE = "settings JSON unreadable"


def HOOK_ENTRY(script_path):  # noqa: N802 — contract name
    return {"matcher": "*",
            "hooks": [{"type": "command", "command": "python3",
                       "args": [script_path, "hook"], "timeout": 10}]}


def SESSION_ENTRY(script_path, settings_path):  # noqa: N802 — contract name
    return {"hooks": [{"type": "command", "command": "python3",
                       "args": [script_path, "check-install", "--quiet-ok",
                                "--settings", settings_path]}]}


def _hook_list(group):
    hooks = group.get("hooks") if isinstance(group, dict) else None
    return [h for h in hooks if isinstance(h, dict)] \
        if isinstance(hooks, list) else []


def _args(hook):
    args = hook.get("args")
    return [a for a in args if isinstance(a, str)] \
        if isinstance(args, list) else []


def _is_ours(group, kind, script_path=None):
    """A hook group this guard owns: python3 <.../holdout_guard.py> <kind>."""
    for hook in _hook_list(group):
        args = _args(hook)
        if hook.get("command") != "python3" or len(args) < 2:
            continue
        if args[1] != kind:
            continue
        if script_path is not None:
            if args[0] == script_path:
                return True
        elif os.path.basename(args[0]) == SCRIPT_BASENAME:
            return True
    return False


def _merge_entry(groups, entry, kind):
    """Replace the first group of ours in place (dropping duplicates), or
    append. Every other group keeps its position and value."""
    out, placed = [], False
    for group in groups:
        if _is_ours(group, kind):
            if not placed:
                out.append(entry)
                placed = True
            continue
        out.append(group)
    if not placed:
        out.append(entry)
    return out


def _load_settings(path):
    """-> (data, existed). Raises GuardError on unreadable JSON."""
    if not os.path.exists(path):
        return {}, False
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        raise GuardError(MSG_UNREADABLE)
    if not isinstance(data, dict):
        raise GuardError(MSG_UNREADABLE)
    return data, True


def _section(parent, key, kind):
    value = parent.get(key)
    if value is None:
        value = kind()
        parent[key] = value
    if not isinstance(value, kind):
        raise GuardError("settings key %s has an unexpected shape" % key)
    return value


def _mode_of(path):
    """Permission bits of an existing file; 0o600 for a new one. Settings may
    hold tokens (the user-level file is 0600), so a rewrite or a backup never
    widens them."""
    try:
        return os.stat(path).st_mode & 0o777
    except OSError:
        return 0o600


def _open_with_mode(path, mode, binary=False):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        os.fchmod(fd, mode)
    except OSError:
        os.close(fd)
        raise
    if binary:
        return os.fdopen(fd, "wb")
    return os.fdopen(fd, "w", encoding="utf-8")


def _atomic_write(path, data):
    parent = os.path.dirname(os.path.abspath(path))
    tmp = path + ".tmp"
    try:
        os.makedirs(parent, exist_ok=True)
        with _open_with_mode(tmp, _mode_of(path)) as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    except OSError:
        raise GuardError("cannot write the settings file")
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _backup_once(path):
    bak = path + ".pre-holdout.bak"
    if os.path.exists(bak):
        return
    try:
        with open(path, "rb") as src:
            raw = src.read()
        with _open_with_mode(bak, _mode_of(path), binary=True) as dst:
            dst.write(raw)
    except OSError:
        raise GuardError("cannot write the one-time settings backup")


def install_into(settings_path, script_path):
    """Merge the hook, the SessionStart self-check and DENY_RULES into a
    settings file. -> "installed" | "already-installed"."""
    data, existed = _load_settings(settings_path)
    before = json.loads(json.dumps(data))
    hooks = _section(data, "hooks", dict)
    pre = _section(hooks, "PreToolUse", list)
    start = _section(hooks, "SessionStart", list)
    hooks["PreToolUse"] = _merge_entry(pre, HOOK_ENTRY(script_path), "hook")
    hooks["SessionStart"] = _merge_entry(
        start, SESSION_ENTRY(script_path, settings_path), "check-install")
    perms = _section(data, "permissions", dict)
    deny = _section(perms, "deny", list)
    for rule in DENY_RULES:
        if rule not in deny:
            deny.append(rule)
    if existed and data == before:
        return "already-installed"
    if existed:
        _backup_once(settings_path)
    _atomic_write(settings_path, data)
    return "installed"


def uninstall_from(settings_path, script_path):
    """Remove exactly what install added. -> "removed" | "not-present"."""
    data, existed = _load_settings(settings_path)
    if not existed:
        return "not-present"
    before = json.loads(json.dumps(data))
    hooks = data.get("hooks")
    if isinstance(hooks, dict):
        for key, kind in (("PreToolUse", "hook"),
                          ("SessionStart", "check-install")):
            groups = hooks.get(key)
            if not isinstance(groups, list):
                continue
            kept = [g for g in groups if not _is_ours(g, kind, script_path)]
            if len(kept) != len(groups):
                if kept:
                    hooks[key] = kept
                else:
                    del hooks[key]
        if not hooks:
            del data["hooks"]
    perms = data.get("permissions")
    if isinstance(perms, dict) and isinstance(perms.get("deny"), list):
        kept = [r for r in perms["deny"] if r not in DENY_RULES]
        if len(kept) != len(perms["deny"]):
            if kept:
                perms["deny"] = kept
            else:
                del perms["deny"]
            if not perms:
                del data["permissions"]
    if data == before:
        return "not-present"
    _atomic_write(settings_path, data)
    return "removed"


def _find_hook(groups, kind):
    """First (group, hook) whose args name this script with `kind` at [1],
    or whose args or command mention the script at all (for diagnosis)."""
    for group in groups if isinstance(groups, list) else []:
        for hook in _hook_list(group):
            args = _args(hook)
            command = hook.get("command") if isinstance(
                hook.get("command"), str) else ""
            if any(a.endswith(SCRIPT_BASENAME) for a in args) \
                    or SCRIPT_BASENAME in command:
                if kind is None or kind in args:
                    return group, hook
    return None, None


def settings_problems(settings_text, script_path):
    """Static contract check of one settings file -> list of problems."""
    try:
        data = json.loads(settings_text)
    except (TypeError, ValueError):
        return [MSG_UNREADABLE]
    if not isinstance(data, dict):
        return [MSG_UNREADABLE]
    problems = []
    hooks = data.get("hooks") if isinstance(data.get("hooks"), dict) else {}
    group, hook = _find_hook(hooks.get("PreToolUse"), None)
    if hook is None:
        problems.append("PreToolUse hook missing")
    else:
        args = hook.get("args") if isinstance(hook.get("args"), list) else []
        if group.get("matcher") != "*":
            problems.append("matcher is not *")
        if hook.get("type") != "command" or hook.get("command") != "python3":
            problems.append("hook command is not python3")
        if not args or args[0] != script_path:
            problems.append("hook path is not " + script_path)
        if len(args) < 2 or args[1] != "hook":
            problems.append("hook arg is not 'hook'")
        timeout = hook.get("timeout")
        if not (isinstance(timeout, (int, float))
                and not isinstance(timeout, bool) and 0 < timeout <= 10):
            problems.append("hook timeout missing or > 10")
    perms = data.get("permissions")
    deny = perms.get("deny") if isinstance(perms, dict) else None
    deny = deny if isinstance(deny, list) else []
    for rule in DENY_RULES:
        if rule not in deny:
            problems.append("deny rule missing: " + rule)
    s_group, s_hook = _find_hook(hooks.get("SessionStart"), "check-install")
    if s_hook is None or _args(s_hook)[:1] != [script_path] \
            or s_hook.get("command") != "python3":
        problems.append("SessionStart check-install missing")
    return problems


class _Sink(object):
    def write(self, _text):
        return 0


def _python3_on_path():
    for d in os.get_exec_path():
        candidate = os.path.join(d, "python3")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return True
    return False


def check_install(settings_paths, script_path):
    """Full verification -> list of problems ([] when installed and live)."""
    problems = []
    for path in settings_paths:
        if not os.path.isfile(path):
            problems.append("settings file missing: " + path)
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            text = None
        for p in settings_problems(text, script_path):
            problems.append("%s (in %s)" % (p, path))
    if not os.path.isfile(script_path):
        problems.append("script missing: " + script_path)
    if not _python3_on_path():
        problems.append("python3 not on PATH")
    if hook_main(PROBE_PAYLOAD, err=_Sink()) != 2:
        problems.append("live probe did not deny")
    return problems


def _script_path():
    return os.path.abspath(__file__)


def _repo_settings_path(repo_root):
    return os.path.join(os.path.abspath(repo_root), ".claude",
                        "settings.local.json")


def _user_settings_path():
    return os.path.expanduser("~/.claude/settings.json")


def _default_settings_paths(script_path):
    repo_root = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(script_path)), "..", "..", "..", ".."))
    return [_repo_settings_path(repo_root), _user_settings_path()]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _build_parser():
    parser = argparse.ArgumentParser(
        prog="holdout_guard.py",
        description="v2.12 holdout deny hook (see module docstring).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    hook = sub.add_parser("hook", help="PreToolUse hook (stdin = hook JSON)")
    hook.add_argument("--role", choices=ROLES, default="tuning")
    hook.add_argument("--protect", action="append", default=[])
    for name in ("install", "uninstall"):
        p = sub.add_parser(name)
        where = p.add_mutually_exclusive_group(required=True)
        where.add_argument("--repo")
        where.add_argument("--user", action="store_true")
    check = sub.add_parser("check-install")
    check.add_argument("--settings", action="append", default=[])
    check.add_argument("--quiet-ok", action="store_true")
    return parser


def run(argv):
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    if args.cmd == "hook":
        try:
            text = sys.stdin.read()
        except Exception:  # noqa: BLE001 — fail closed on an unreadable stdin
            sys.stderr.write(REASON_INTERNAL)
            return 2
        return hook_main(text, role=args.role,
                         extra_protect=tuple(args.protect))
    script = _script_path()
    if args.cmd in ("install", "uninstall"):
        target = (_user_settings_path() if args.user
                  else _repo_settings_path(args.repo))
        try:
            if args.cmd == "install":
                result = install_into(target, script)
            else:
                result = uninstall_from(target, script)
        except GuardError as exc:
            sys.stderr.write("PROBLEM: %s\n" % exc)
            return 1
        lines = {
            "installed": "Installed the holdout guard into %s\n",
            "already-installed": "Already installed in %s\n",
            "removed": "Removed the holdout guard from %s\n",
            "not-present": "Not installed in %s\n",
        }
        sys.stdout.write(lines[result] % target)
        return 0
    paths = args.settings or _default_settings_paths(script)
    problems = check_install(paths, script)
    if not problems:
        if not args.quiet_ok:
            sys.stdout.write("OK: holdout guard installed and live "
                             "(%d settings file(s))\n" % len(paths))
        return 0
    for p in problems:
        line = "PROBLEM: %s\n" % p
        sys.stdout.write(line)
        if args.quiet_ok:
            # SessionStart mode: also on stderr so a failed self-check is
            # visible to the person, not only to the session.
            sys.stderr.write(line)
    return 1


def _main(argv):
    try:
        return run(argv)
    except Exception:  # noqa: BLE001 — any crash denies rather than opens
        sys.stderr.write(REASON_INTERNAL)
        return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
