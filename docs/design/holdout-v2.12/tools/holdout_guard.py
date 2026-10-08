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

def install_into(settings_path, script_path):
    raise GuardError("install is not available yet")


def uninstall_from(settings_path, script_path):
    raise GuardError("uninstall is not available yet")


def settings_problems(settings_text, script_path):
    return ["settings check is not available yet"]


def check_install(settings_paths, script_path):
    return ["check-install is not available yet"]


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
    sys.stdout.write("%s is not implemented\n" % args.cmd)
    return 2


def _main(argv):
    try:
        return run(argv)
    except Exception:  # noqa: BLE001 — any crash denies rather than opens
        sys.stderr.write(REASON_INTERNAL)
        return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
