"""gitguard.py — the fail-closed Bash classifier for vibe-check review agents.

A vibe-check review (detection) agent must never change the reviewed repo. In a
past review the compliance agent ran `git stash pop` in the reviewed clone and
popped the owner's unrelated stash. `classify(command)` answers one question
for a Bash command string a review agent wants to run: could this change the
repo — through git, or through any path that reaches git without naming it?
Anything it cannot prove read-only is refused.

Review-agent Bash is held to a fixed allowlist of read-only command words: git
under its own argv rules, plus the search/read words detection agents need
(Grep/Glob tools are not available to them, so they search through Bash). The
plugin's own trusted mutating scripts (`fixstage.py commit` performs a real
commit and contains no word `git`) are refused by basename before anything else.

Contract (fail CLOSED on every ambiguity):
  - every ambiguous or unanalyzable form refuses: unbalanced quotes, command or
    process substitution, heredocs, `$` expansion in a command that mentions
    git, `-c`/`--config-env`/`--git-dir`/`--work-tree` global options, unsafe
    leading NAME=VALUE assignments (GIT_DIR, GIT_EXTERNAL_DIFF, ...), aliases
    and unknown git subcommands, newline- or operator-chained second commands
  - interpreters, shells and indirection words (python*, node, perl, ruby, sh,
    bash, zsh, eval, exec, source, `.`, xargs, sudo, find -exec/-delete, ...)
    refuse whether or not `git` appears — an interpreter can run a file or a
    heredoc that shells out
  - any command word outside SAFE_COMMAND_WORDS refuses; a path-form command
    word is accepted only from /bin, /usr/bin, /usr/local/bin or
    /opt/homebrew/bin
  - any output redirection to a file refuses (only /dev/null and fd dups pass)
  - any token whose basename is a trusted plugin script refuses
  - reasons are FIXED strings that never echo the command (callers render a
    sanitized command separately)
  - classify itself is pure — no I/O; only the CLI below does I/O

CLI (python3 gitguard.py <subcommand>):
  hook                      PreToolUse hook; stdin = the tool-call JSON.
                            exit 0 allow | 2 deny (+ one fixed stderr line).
                            Guards only `vibe-check:*` agents other than
                            `vibe-check:fix`; never the main session or other
                            plugins. Each refusal is appended to
                            <repo>/.turingmind/git-guard/blocks.jsonl.
  notices --root R [--consume] [--repo-changed]
                            prints one sanitized line per recorded block
                            ("Blocked: <agent> tried `<cmd>` — repo
                            untouched."), at most 10 plus a "…and N more"
                            line; --consume deletes the record file after.
                            The orchestrator must copy these lines into the
                            review as its own message text — never leave them
                            only inside Bash output, which the owner may not
                            see. exit 0 | 2 usage.
  reset --root R            deletes the record file if present. exit 0 | 2.

I/O: stdlib only. The module's full import set is {argparse, json, os, re,
shlex, sys}; it never imports subprocess, shutil or socket.

Tokenizing notes: shlex treats a newline as plain whitespace, so unquoted
newlines become ` ; ` before tokenizing; shlex comment handling is turned off
because shlex starts a comment at `#` even mid-word (bash does not), which would
hide a second command. A redirect's fd number (`2` in `2>/dev/null`) stays in
the argv as an extra argument — that can only make a command look less safe,
never more.

Allowlist audit (every kept word was checked for implicit writes — positional
output operands, output flags, exec/compile flags — in both BSD and GNU forms):
  - cat: no output-file operand, no output/exec flag; writes only to stdout
  - head: no output-file operand, no output/exec flag; writes only to stdout
  - tail: no output-file operand, no output/exec flag; writes only to stdout
  - wc: no output-file operand, no output/exec flag; writes only to stdout
  - grep: no output-file operand, no output/exec flag; writes only to stdout
  - stat: no output-file operand, no output/exec flag; writes only to stdout
  - ls: no output-file operand, no output/exec flag; writes only to stdout
  - cut: no output-file operand, no output/exec flag; writes only to stdout
  - tr: no output-file operand, no output/exec flag; writes only to stdout
  - echo: no output-file operand, no output/exec flag; writes only to stdout
  - printf: no output-file operand, no output/exec flag; writes only to stdout
  - true: no output-file operand, no output/exec flag; writes nothing
  - false: no output-file operand, no output/exec flag; writes nothing
  - basename: no output-file operand, no output/exec flag; writes only to stdout
  - dirname: no output-file operand, no output/exec flag; writes only to stdout
  - pwd: no output-file operand, no output/exec flag; writes only to stdout
  - rg: writes only to stdout; its exec paths are exactly the rg entries of
    DENIED_READER_FLAGS (--pre, --pre-glob, --hostname-bin, --search-zip, -z)
  - find: its write/exec paths are exactly -fprint/-fprint0/-fprintf/-fls
    (DENIED_READER_FLAGS) and -exec/-execdir/-ok/-okdir/-delete (refused as
    indirection)
  - git: governed by its own argv rules (READ_ONLY_SUBCOMMANDS,
    CONDITIONAL_SUBCOMMANDS, DENIED_SUBCOMMAND_FLAGS)
  stdout itself is confined by the redirect rule.

Removed words and why: uniq (its second positional operand is an OUTPUT file —
`uniq /dev/null src/app.py` truncates src/app.py with no flag or redirect),
sort (-o/--output, --compress-program), file (-C compiles a .mgc into the cwd;
-z spawns decompressors), diff/cmp/comm/nl/column (not needed for search/read —
removal is cheaper and safer than auditing every platform variant). Any future
addition must extend this audit and the exact-set test in the same commit.

Residuals (what this deterministic rule cannot see, and the belt for each):
  - a binary already on PATH under an allowlisted name that a non-agent process
    replaced
  - another plugin's hook overriding this deny
  - python3 missing, so the hook cannot run (the hook fails open)
  The git-metadata effects of these (HEAD, index, stash, branches/tags, HEAD
  reflog) are caught after the fact by the gitsnap before/after snapshot around
  the review fan-out. gitsnap does NOT see working-tree byte writes, which is
  why the allowlist itself must be write-free and is pinned to the exact
  audited set by TestAllowlistAudit.
"""

import argparse
import json
import os
import re
import shlex
import sys

# --------------------------------------------------------------------------- #
# fixed reasons
# --------------------------------------------------------------------------- #
ALLOWED = "allowed"
REASON_NO_COMMAND = "refused: no command string (fail closed)"
REASON_INTERNAL = "refused: classifier error (fail closed)"
REASON_TRUSTED_SCRIPT = (
    "refused: references a vibe-check trusted script (fail closed)")
REASON_INDIRECTION = (
    "refused: interpreter, shell or indirection word (fail closed)")
REASON_NOT_ALLOWLISTED = (
    "refused: command is not on the review-agent read-only allowlist "
    "(fail closed)")
REASON_SUBSTITUTION = (
    "refused: command substitution, process substitution or heredoc "
    "(fail closed)")
REASON_REDIRECT = "refused: output redirection to a file (fail closed)"
REASON_UNPARSEABLE = "refused: command cannot be parsed (fail closed)"
REASON_GIT_EXPANSION = (
    "refused: shell expansion in a command that mentions git (fail closed)")
REASON_ENV = "refused: unsafe environment assignment (fail closed)"
REASON_GIT_GLOBAL_OPT = "refused: git global option not allowed (fail closed)"
REASON_GIT_SUBCOMMAND = (
    "refused: git subcommand is not read-only (fail closed)")
REASON_GIT_FLAG = "refused: git flag writes a file or runs a program (fail closed)"
REASON_GIT_ARGS = (
    "refused: git subcommand form is not read-only (fail closed)")
REASON_GIT_AS_ARGUMENT = (
    "refused: git passed as an argument to another command (fail closed)")
REASON_GIT_DIR_PATH = (
    "refused: .git path used by a non-reader command (fail closed)")

# --------------------------------------------------------------------------- #
# command-word policy
# --------------------------------------------------------------------------- #
TRUSTED_SCRIPT_BASENAMES = frozenset({
    "fixstage.py", "fixcheck.py", "gitsnap.py", "gitguard.py", "fixcommit.py",
    "guard.py",
})

PURE_READERS = frozenset(
    {"cat", "head", "tail", "ls", "wc", "grep", "rg", "stat", "find"})

SAFE_COMMAND_WORDS = frozenset({"git"}) | PURE_READERS | frozenset({
    "echo", "printf", "true", "false", "cut", "tr", "basename", "dirname",
    "pwd",
})

DENIED_READER_FLAGS = {
    "rg": frozenset(
        {"--pre", "--pre-glob", "--hostname-bin", "--search-zip", "-z"}),
    "find": frozenset({"-fprint", "-fprint0", "-fprintf", "-fls"}),
}

INDIRECTION_WORDS = frozenset({
    "eval", "exec", "source", ".", "xargs", "parallel", "sudo", "doas", "su",
    "sh", "bash", "zsh", "dash", "fish", "ksh", "csh", "tcsh", "busybox",
    "python", "python2", "python3", "python3.8", "python3.9", "python3.10",
    "python3.11", "python3.12", "python3.13", "python3.14", "pypy", "pypy3",
    "node", "nodejs", "deno", "bun", "perl", "ruby", "php", "lua", "tclsh",
    "osascript", "expect", "script",
})

FIND_ACTION_FLAGS = frozenset(
    {"-exec", "-execdir", "-ok", "-okdir", "-delete"})

SYSTEM_BIN_DIRS = frozenset(
    {"/bin", "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin"})

# NAME -> required value, or None for "any value".
SAFE_ENV_ASSIGNMENTS = {
    "GIT_PAGER": "cat",
    "PAGER": "cat",
    "LC_ALL": None,
    "LANG": None,
    "NO_COLOR": None,
    "TERM": "dumb",
}

WRAPPER_WORDS = frozenset({"command", "nice", "nohup", "time", "timeout", "env"})

# --------------------------------------------------------------------------- #
# git argv policy
# --------------------------------------------------------------------------- #
ALLOWED_GLOBAL_OPTS = frozenset({
    "-C", "--no-pager", "-P", "--no-optional-locks", "--literal-pathspecs",
    "--glob-pathspecs", "--noglob-pathspecs", "--icase-pathspecs",
    "--no-replace-objects",
})

DENIED_GLOBAL_OPTS = frozenset({
    "-c", "--config-env", "--git-dir", "--work-tree", "--exec-path",
    "--namespace", "--bare", "--super-prefix",
})

# Global options that consume the following token as their value.
GLOBAL_OPTS_WITH_VALUE = frozenset({
    "-C", "-c", "--config-env", "--git-dir", "--work-tree", "--namespace",
    "--super-prefix",
})

READ_ONLY_SUBCOMMANDS = frozenset({
    "log", "show", "diff", "diff-tree", "diff-index", "diff-files", "blame",
    "annotate", "status", "rev-parse", "rev-list", "ls-files", "ls-tree",
    "cat-file", "merge-base", "describe", "shortlog", "name-rev",
    "for-each-ref", "show-ref", "show-branch", "grep", "cherry", "range-diff",
    "whatchanged", "count-objects", "check-ignore", "check-attr",
    "check-ref-format", "var", "version",
})
# `ls-remote` is deliberately absent: `--upload-pack=<cmd>` (any unique
# abbreviation) runs an arbitrary program, and it reaches the network.
# It falls through to UNKNOWN_SUBCOMMAND_VERDICT (refused).

DENIED_SUBCOMMAND_FLAGS = frozenset({
    "--output", "-O", "--open-files-in-pager", "--ext-diff", "--textconv",
})

_PUNCT_CHARS = set("();<>|&")
_SEPARATOR_TOKENS = frozenset({"{", "}"})
_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_RG_Z_CLUSTER_RE = re.compile(r"^-[A-Za-z]*z[A-Za-z]*$")
_TRUSTED_SPLIT_RE = re.compile(r"[\s;&|(){}<>=]+")
_SUBSTITUTION_MARKERS = ("`", "$(", "${", "<(", ">(", "<<")


# --------------------------------------------------------------------------- #
# conditional git subcommands: each takes the argv after the subcommand
# --------------------------------------------------------------------------- #
def _ok():
    return True, ALLOWED


def _no():
    return False, REASON_GIT_ARGS


def _stash(args):
    if args and args[0] in ("list", "show"):
        return _ok()
    return _no()


_BRANCH_LIST_FLAGS = frozenset({
    "-a", "-r", "-l", "--list", "-v", "-vv", "--verbose", "--show-current",
    "--all", "--remotes", "--contains", "--no-contains", "--merged",
    "--no-merged", "--points-at", "--format", "--sort", "--column",
    "--no-column", "--color", "--no-color", "-i", "--ignore-case", "--abbrev",
    "--no-abbrev", "--omit-empty",
})
_BRANCH_VALUE_FLAGS = frozenset({
    "--contains", "--no-contains", "--merged", "--no-merged", "--points-at",
    "--format", "--sort",
})
_BRANCH_SHORT_CLUSTER_RE = re.compile(r"^-[arlvi]+$")


def _branch(args):
    listing = False
    positional = False
    i = 0
    while i < len(args):
        tok = args[i]
        if tok.startswith("-"):
            name = tok.split("=", 1)[0] if tok.startswith("--") else tok
            if name in _BRANCH_LIST_FLAGS:
                pass
            elif _BRANCH_SHORT_CLUSTER_RE.match(tok):
                pass
            else:
                return _no()
            if name in ("-l", "--list") or (
                    _BRANCH_SHORT_CLUSTER_RE.match(tok) and "l" in tok):
                listing = True
            if name in _BRANCH_VALUE_FLAGS and "=" not in tok \
                    and i + 1 < len(args):
                i += 2
                continue
        else:
            positional = True
        i += 1
    if positional and not listing:
        return _no()
    return _ok()


_TAG_LIST_FLAGS = frozenset({
    "-l", "--list", "--sort", "--contains", "--no-contains", "--merged",
    "--no-merged", "--points-at", "--format", "-i", "--ignore-case",
    "--column", "--no-column", "--color", "--no-color", "--omit-empty",
})
_TAG_VALUE_FLAGS = frozenset({
    "--sort", "--contains", "--no-contains", "--merged", "--no-merged",
    "--points-at", "--format",
})


def _tag(args):
    if not args:
        return _ok()
    listing = False
    positional = False
    i = 0
    while i < len(args):
        tok = args[i]
        if tok.startswith("-"):
            name = tok.split("=", 1)[0] if tok.startswith("--") else tok
            if re.match(r"^-n[0-9]*$", tok):
                listing = True
            elif name in _TAG_LIST_FLAGS:
                if name in ("-l", "--list"):
                    listing = True
                if name in _TAG_VALUE_FLAGS and "=" not in tok \
                        and i + 1 < len(args):
                    i += 2
                    continue
            else:
                return _no()
        else:
            positional = True
        i += 1
    if positional and not listing:
        return _no()
    return _ok()


def _remote(args):
    if not args:
        return _ok()
    if args in (["-v"], ["--verbose"]):
        return _ok()
    if args[0] == "get-url" and all(
            a in ("--push", "--all") or not a.startswith("-")
            for a in args[1:]):
        return _ok()
    if args[0] == "show" and all(
            a == "-n" or not a.startswith("-") for a in args[1:]):
        return _ok()
    return _no()


_CONFIG_READ_FLAGS = frozenset({
    "--get", "--get-all", "--get-regexp", "--list", "-l", "--show-origin",
    "--show-scope", "--name-only", "-z", "--null", "--global", "--local",
    "--system", "--worktree",
})
_CONFIG_READ_MODES = frozenset(
    {"--get", "--get-all", "--get-regexp", "--list", "-l"})
_CONFIG_SCOPE_FLAGS = frozenset(
    {"--global", "--local", "--system", "--worktree"})


def _config(args):
    rest = list(args)
    while rest and rest[0] in _CONFIG_SCOPE_FLAGS:
        rest.pop(0)
    if rest and rest[0] in ("get", "list"):
        if all(not a.startswith("-") or a in _CONFIG_READ_FLAGS
               for a in rest[1:]):
            return _ok()
        return _no()
    if not any(a in _CONFIG_READ_MODES for a in args):
        return _no()
    if all(not a.startswith("-") or a in _CONFIG_READ_FLAGS for a in args):
        return _ok()
    return _no()


def _worktree(args):
    if args and args[0] == "list":
        return _ok()
    return _no()


def _notes(args):
    if args and args[0] in ("list", "show"):
        return _ok()
    return _no()


def _reflog(args):
    # Bare `git reflog` and option-first forms are `reflog show`.
    if not args or args[0] == "show" or args[0].startswith("-"):
        return _ok()
    return _no()


def _submodule(args):
    if args and args[0] in ("status", "summary"):
        return _ok()
    return _no()


def _sparse_checkout(args):
    if args == ["list"]:
        return _ok()
    return _no()


def _symbolic_ref(args):
    positional = []
    for tok in args:
        if tok in ("-q", "--quiet", "--short", "--no-recurse"):
            continue
        if tok.startswith("-"):
            return _no()
        positional.append(tok)
    if len(positional) == 1:
        return _ok()
    return _no()


CONDITIONAL_SUBCOMMANDS = {
    "stash": _stash,
    "branch": _branch,
    "tag": _tag,
    "remote": _remote,
    "config": _config,
    "worktree": _worktree,
    "notes": _notes,
    "reflog": _reflog,
    "submodule": _submodule,
    "sparse-checkout": _sparse_checkout,
    "symbolic-ref": _symbolic_ref,
}

# Verdict for any git subcommand that is neither read-only nor conditional
# (including every alias, which the classifier cannot resolve).
UNKNOWN_SUBCOMMAND_VERDICT = (False, REASON_GIT_SUBCOMMAND)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _trusted_names(plugin_scripts):
    names = set(TRUSTED_SCRIPT_BASENAMES)
    for name in plugin_scripts or ():
        if isinstance(name, str) and name:
            names.add(name.lower())
    return frozenset(names)


def _references_trusted_script(command, plugin_scripts):
    lowered = command.lower()
    for ch in ("'", '"', "\\"):
        lowered = lowered.replace(ch, "")
    names = _trusted_names(plugin_scripts)
    for piece in _TRUSTED_SPLIT_RE.split(lowered):
        if piece and piece.rsplit("/", 1)[-1] in names:
            return True
    return False


def _has_substitution(command):
    return any(marker in command for marker in _SUBSTITUTION_MARKERS)


def _mentions_git(command):
    lowered = command.lower()
    for ch in ("'", '"', "\\"):
        lowered = lowered.replace(ch, "")
    return "git" in lowered


def _normalise_newlines(command):
    """Replace newlines outside quotes with ` ; ` (shlex treats \\n as space)."""
    out = []
    quote = None
    i = 0
    n = len(command)
    while i < n:
        ch = command[i]
        if quote:
            out.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < n:
                out.append(command[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch == "\\" and i + 1 < n:
            if command[i + 1] == "\n":
                # Line continuation: bash joins the lines.
                i += 2
                continue
            out.append(ch)
            out.append(command[i + 1])
            i += 2
            continue
        elif ch in ("'", '"'):
            quote = ch
            out.append(ch)
        elif ch in ("\n", "\r"):
            out.append(" ; ")
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _tokenize(command):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _is_punct(token):
    return bool(token) and all(ch in _PUNCT_CHARS for ch in token)


def _is_redirect_op(token):
    return _is_punct(token) and ("<" in token or ">" in token)


def _redirect_is_safe(op, target):
    if target is None:
        return False
    if op in (">", ">>", ">|", "&>", "&>>") and target == "/dev/null":
        return True
    if op in (">&", "<&") and (target.isdigit() or target == "-"):
        return True
    if op == "<":
        return True
    return False


def _has_file_redirect(tokens):
    for i, tok in enumerate(tokens):
        if _is_redirect_op(tok):
            target = tokens[i + 1] if i + 1 < len(tokens) else None
            if target is not None and _is_punct(target):
                target = None
            if not _redirect_is_safe(tok, target):
                return True
    return False


def _strip_redirects(tokens):
    out = []
    i = 0
    while i < len(tokens):
        if _is_redirect_op(tokens[i]):
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            i += 2 if nxt is not None and not _is_punct(nxt) else 1
            continue
        out.append(tokens[i])
        i += 1
    return out


def _split_simple_commands(tokens):
    segments = []
    current = []
    for tok in tokens:
        if (_is_punct(tok) and not _is_redirect_op(tok)) \
                or tok in _SEPARATOR_TOKENS:
            if current:
                segments.append(current)
            current = []
        else:
            current.append(tok)
    if current:
        segments.append(current)
    return segments


def _safe_assignment(token):
    name, value = token.split("=", 1)
    if name not in SAFE_ENV_ASSIGNMENTS:
        return False
    required = SAFE_ENV_ASSIGNMENTS[name]
    return required is None or value == required


def _unwrap(argv):
    """Strip leading assignments and wrapper words -> (argv, deny reason|None)."""
    while argv and _ASSIGNMENT_RE.match(argv[0]):
        if not _safe_assignment(argv[0]):
            return argv, REASON_ENV
        argv = argv[1:]
    while argv and argv[0].lower() in WRAPPER_WORDS:
        word = argv[0].lower()
        argv = argv[1:]
        if word == "env":
            while argv and _ASSIGNMENT_RE.match(argv[0]):
                if not _safe_assignment(argv[0]):
                    return argv, REASON_ENV
                argv = argv[1:]
            if argv and argv[0].startswith("-"):
                return argv, REASON_NOT_ALLOWLISTED
        elif word == "timeout":
            if not argv or argv[0].startswith("-"):
                return argv, REASON_NOT_ALLOWLISTED
            argv = argv[1:]
        elif word == "nice":
            if argv and argv[0] == "-n" and len(argv) > 1:
                argv = argv[2:]
            elif argv and re.match(r"^-[0-9]+$", argv[0]):
                argv = argv[1:]
            elif argv and argv[0].startswith("-"):
                return argv, REASON_NOT_ALLOWLISTED
        elif word == "time":
            if argv and argv[0] == "-p":
                argv = argv[1:]
            elif argv and argv[0].startswith("-"):
                return argv, REASON_NOT_ALLOWLISTED
        else:  # command, nohup
            if argv and argv[0].startswith("-"):
                return argv, REASON_NOT_ALLOWLISTED
    if not argv:
        return argv, REASON_NOT_ALLOWLISTED
    return argv, None


def _command_basename(word):
    """-> (lowercased basename, deny reason|None) for the command word."""
    if word.startswith("$"):
        return None, REASON_NOT_ALLOWLISTED
    if "/" in word:
        directory, base = word.rsplit("/", 1)
        if directory not in SYSTEM_BIN_DIRS or not base:
            return None, REASON_NOT_ALLOWLISTED
        return base.lower(), None
    return word.lower(), None


def _is_denied_subcommand_flag(token):
    if not token.startswith("-"):
        return False
    if token.startswith("--"):
        name = token.split("=", 1)[0]
        if name in DENIED_SUBCOMMAND_FLAGS:
            return True
        # git accepts unique abbreviations of long options.
        return len(name) > 3 and any(
            flag.startswith(name) for flag in DENIED_SUBCOMMAND_FLAGS
            if flag.startswith("--"))
    for flag in DENIED_SUBCOMMAND_FLAGS:
        if len(flag) == 2 and not flag.startswith("--"):
            letter = flag[1]
            if token.startswith(flag):
                return True
            if re.match(r"^-[A-Za-z]+$", token) and letter in token[1:]:
                return True
    return False


def _classify_git_argv(args):
    i = 0
    while i < len(args):
        tok = args[i]
        if not tok.startswith("-"):
            break
        name = tok.split("=", 1)[0] if tok.startswith("--") else tok
        if name in DENIED_GLOBAL_OPTS:
            return False, REASON_GIT_GLOBAL_OPT
        if name not in ALLOWED_GLOBAL_OPTS:
            return False, REASON_GIT_GLOBAL_OPT
        if name in GLOBAL_OPTS_WITH_VALUE and "=" not in tok:
            if i + 1 >= len(args):
                return False, REASON_GIT_GLOBAL_OPT
            i += 2
            continue
        i += 1
    if i >= len(args):
        return False, REASON_GIT_SUBCOMMAND
    sub = args[i]
    rest = args[i + 1:]
    if any(_is_denied_subcommand_flag(tok) for tok in rest):
        return False, REASON_GIT_FLAG
    if sub in READ_ONLY_SUBCOMMANDS:
        return True, ALLOWED
    if sub in CONDITIONAL_SUBCOMMANDS:
        return CONDITIONAL_SUBCOMMANDS[sub](list(rest))
    return UNKNOWN_SUBCOMMAND_VERDICT


def _reader_flag_denied(word, args):
    denied = DENIED_READER_FLAGS.get(word)
    if not denied:
        return False
    for tok in args:
        name = tok.split("=", 1)[0] if tok.startswith("--") else tok
        if name in denied:
            return True
        if word == "rg" and not tok.startswith("--") \
                and _RG_Z_CLUSTER_RE.match(tok):
            return True
    return False


def _touches_git_dir(args):
    return any(".git" in tok.split("/") for tok in args)


def _classify_simple(argv):
    argv = _strip_redirects(argv)
    if not argv:
        return True, ALLOWED
    argv, reason = _unwrap(argv)
    if reason:
        return False, reason
    word, reason = _command_basename(argv[0])
    if reason:
        return False, reason
    args = argv[1:]
    if word in INDIRECTION_WORDS:
        return False, REASON_INDIRECTION
    if word == "find" and any(tok in FIND_ACTION_FLAGS for tok in args):
        return False, REASON_INDIRECTION
    if word == "git":
        return _classify_git_argv(args)
    if word not in SAFE_COMMAND_WORDS:
        return False, REASON_NOT_ALLOWLISTED
    if _reader_flag_denied(word, args):
        return False, REASON_NOT_ALLOWLISTED
    if any(tok.lower() == "git" for tok in args):
        return False, REASON_GIT_AS_ARGUMENT
    if _touches_git_dir(args) and word not in PURE_READERS:
        return False, REASON_GIT_DIR_PATH
    return True, ALLOWED


def _classify(command, plugin_scripts):
    if not isinstance(command, str) or not command.strip():
        return False, REASON_NO_COMMAND
    if _references_trusted_script(command, plugin_scripts):
        return False, REASON_TRUSTED_SCRIPT
    if _has_substitution(command):
        return False, REASON_SUBSTITUTION
    if _mentions_git(command) and "$" in command:
        return False, REASON_GIT_EXPANSION
    try:
        tokens = _tokenize(_normalise_newlines(command))
    except ValueError:
        return False, REASON_UNPARSEABLE
    if _has_file_redirect(tokens):
        return False, REASON_REDIRECT
    segments = _split_simple_commands(tokens)
    if not segments:
        return False, REASON_NO_COMMAND
    for segment in segments:
        allowed, reason = _classify_simple(segment)
        if not allowed:
            return False, reason
    return True, ALLOWED


def classify(command, plugin_scripts=frozenset()):
    """Could this review-agent Bash command change the repo? -> (bool, reason).

    `command` is the raw tool_input.command string. `plugin_scripts` is the set
    of the plugin's scripts/ basenames supplied by the hook (lowercased and
    unioned with TRUSTED_SCRIPT_BASENAMES). Returns (True, "allowed") or
    (False, <fixed reason>). Pure; never raises — any internal error refuses.
    """
    try:
        return _classify(command, plugin_scripts)
    except Exception:  # noqa: BLE001 — fail closed on any classifier defect
        return False, REASON_INTERNAL


# --------------------------------------------------------------------------- #
# PreToolUse hook entrypoint
# --------------------------------------------------------------------------- #
GUARDED_PREFIX = "vibe-check:"
EXEMPT_AGENTS = frozenset({"vibe-check:fix"})
DENY_TOOLS = frozenset({
    "Agent", "Task", "Write", "Edit", "MultiEdit", "NotebookEdit",
    "EnterWorktree", "ExitWorktree",
})

REASON_DENY_TOOL = (
    "review agents may not spawn agents, write files or switch worktrees")
REASON_GUARD_ERROR = "guard error (fail closed)"

DENY_MESSAGE = (
    "vibe-check: blocked — %s. Review agents may only use read-only git "
    "(diff, show, log, blame, status, rev-parse, ls-files). "
    "The repo was not changed.\n")

BLOCKS_RELPATH = os.path.join(".turingmind", "git-guard", "blocks.jsonl")
COMMAND_CAP = 120

_AGENT_RE = re.compile(r"^vibe-check:([a-z0-9-]{1,40})$")
_SHORT_AGENT_RE = re.compile(r"^[a-z0-9-]{1,40}$")
_TOOL_RE = re.compile(r"^[A-Za-z]{1,30}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f\u2028\u2029`]")
_SPACE_RE = re.compile(r"\s+")


def _plugin_script_names():
    """Lowercase basenames of the *.py / *.sh files in this scripts/ dir."""
    here = os.path.dirname(os.path.realpath(__file__))
    return frozenset(
        name.lower() for name in os.listdir(here)
        if name.lower().endswith((".py", ".sh")))


def _guard_error_verdict():
    return False, REASON_GUARD_ERROR


def _sanitize_command(command):
    if not isinstance(command, str):
        return ""
    text = _CONTROL_RE.sub(" ", command)
    text = _SPACE_RE.sub(" ", text).strip()
    if len(text) > COMMAND_CAP:
        text = text[:COMMAND_CAP] + "…"
    return text


def _short_agent(agent_type):
    match = _AGENT_RE.match(agent_type) if isinstance(agent_type, str) else None
    return match.group(1) if match else "unknown-agent"


def _short_tool(tool):
    if isinstance(tool, str) and _TOOL_RE.match(tool):
        return tool
    return "unknown-tool"


def _find_repo_root(cwd):
    """Walk up from cwd to the first directory holding a `.git` entry."""
    if not isinstance(cwd, str) or not cwd or not os.path.isabs(cwd):
        return None
    current = os.path.realpath(cwd)
    while True:
        if os.path.lexists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def _record_block(payload, reason):
    """Append one JSON line per refusal to <repo>/.turingmind/git-guard."""
    root = _find_repo_root(payload.get("cwd"))
    if root is None:
        sys.stderr.write("vibe-check: block not recorded (no repo found)\n")
        return
    tool = payload.get("tool_name")
    command = ""
    if tool == "Bash":
        tool_input = payload.get("tool_input")
        if isinstance(tool_input, dict):
            command = _sanitize_command(tool_input.get("command"))
    record = {
        "agent": _short_agent(payload.get("agent_type")),
        "tool": _short_tool(tool),
        "command": command,
        "reason": reason,
    }
    path = os.path.join(root, BLOCKS_RELPATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
    flags = (os.O_WRONLY | os.O_CREAT | os.O_APPEND
             | getattr(os, "O_NOFOLLOW", 0))
    fd = os.open(path, flags, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def hook_main(stdin_text):
    """PreToolUse decision -> 0 allow | 2 deny (one stderr line on deny).

    Fails OPEN for anything that cannot be attributed to a guarded agent
    (malformed input, the main session, the fix agent, other plugins) and
    fails CLOSED for vibe-check review agents.
    """
    try:
        data = json.loads(stdin_text)
    except (TypeError, ValueError):
        return 0
    if not isinstance(data, dict):
        return 0
    agent = data.get("agent_type")
    if not isinstance(agent, str) or not agent.startswith(GUARDED_PREFIX) \
            or agent in EXEMPT_AGENTS:
        return 0
    try:
        tool = data.get("tool_name")
        if tool == "Bash":
            tool_input = data.get("tool_input")
            command = (tool_input.get("command")
                       if isinstance(tool_input, dict) else None)
            ok, reason = classify(command,
                                  plugin_scripts=_plugin_script_names())
        elif tool in DENY_TOOLS:
            ok, reason = False, REASON_DENY_TOOL
        else:
            return 0
    except Exception:  # noqa: BLE001 — fail closed for review agents
        ok, reason = _guard_error_verdict()
    if ok:
        return 0
    try:
        _record_block(data, reason)
    except Exception as exc:  # noqa: BLE001 — recording never flips a deny
        sys.stderr.write("vibe-check: block not recorded (%s)\n"
                         % type(exc).__name__)
    sys.stderr.write(DENY_MESSAGE % reason)
    return 2


# --------------------------------------------------------------------------- #
# notices renderer
# --------------------------------------------------------------------------- #
NOTICE_CAP = 10
_GARBLED = object()


def _blocks_file(root):
    return os.path.join(root, BLOCKS_RELPATH)


def _remove_blocks(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def _load_records(path):
    """Parse blocks.jsonl -> list of dicts or _GARBLED; missing file -> []."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except FileNotFoundError:
        return []
    records = []
    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            record = _GARBLED
        records.append(record if isinstance(record, dict) else _GARBLED)
    return records


def _render_one(record, suffix):
    if not isinstance(record, dict):
        return "Blocked: unknown-agent tried an unreadable command — %s" % suffix
    agent = record.get("agent")
    if not (isinstance(agent, str) and _SHORT_AGENT_RE.match(agent)):
        agent = "unknown-agent"
    tool = _short_tool(record.get("tool"))
    if tool != "Bash":
        return "Blocked: %s tried to use the `%s` tool — %s" % (
            agent, tool, suffix)
    command = _sanitize_command(record.get("command"))
    if not command:
        return "Blocked: %s tried an unreadable command — %s" % (agent, suffix)
    return "Blocked: %s tried `%s` — %s" % (agent, command, suffix)


def render_notices(records, repo_changed):
    """One sanitized line per block, capped at NOTICE_CAP plus a tail line."""
    suffix = "this attempt was refused." if repo_changed else "repo untouched."
    records = list(records)
    lines = [_render_one(r, suffix) for r in records[:NOTICE_CAP]]
    extra = len(records) - NOTICE_CAP
    if extra > 0:
        lines.append("…and %d more blocked attempt%s"
                     % (extra, "" if extra == 1 else "s"))
    return lines


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_parser():
    parser = argparse.ArgumentParser(
        prog="gitguard.py",
        description="vibe-check review-agent git guard (see module docstring).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("hook", help="PreToolUse hook (stdin = hook JSON)")
    notices = sub.add_parser("notices", help="render recorded blocks")
    notices.add_argument("--root", required=True)
    notices.add_argument("--consume", action="store_true")
    notices.add_argument("--repo-changed", action="store_true")
    reset = sub.add_parser("reset", help="delete recorded blocks")
    reset.add_argument("--root", required=True)
    return parser


def run(argv):
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2
    if args.cmd == "hook":
        try:
            text = sys.stdin.read()
        except (OSError, ValueError):
            return 0
        return hook_main(text)
    path = _blocks_file(args.root)
    if args.cmd == "reset":
        _remove_blocks(path)
        return 0
    if args.cmd == "notices":
        try:
            records = _load_records(path)
        except OSError as exc:
            sys.stderr.write("gitguard: could not read block records (%s)\n"
                             % type(exc).__name__)
            return 1
        for line in render_notices(records, args.repo_changed):
            sys.stdout.write(line + "\n")
        sys.stdout.flush()
        if args.consume:
            _remove_blocks(path)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
