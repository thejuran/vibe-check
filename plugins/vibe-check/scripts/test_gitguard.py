"""Tests for gitguard.classify — the fail-closed review-agent Bash classifier.

The classifier answers one question for a Bash command issued by a vibe-check
review (detection) agent: could this change the reviewed repo — through git, or
through any path that reaches git without naming it? Anything it cannot prove
read-only is refused.

Locked here:
  * DENY: every mutating git form, every ambiguous/unanalyzable form
    (indirection, substitution, -c config, GIT_* env, aliases, chained and
    newline-separated commands, quote-split `g''it`).
  * TRUSTED_BYPASS_DENY: the plugin's own mutating scripts (fixstage.py commit
    performs a real commit and contains no word `git`) are refused by basename.
  * NON_GIT_DENY: interpreters, shells, unlisted command words, implicit-write
    words (uniq's output operand, sort -o, file -C), substitution, file
    redirection and reader exec/write flags — each with its fixed reason.
  * ALLOW: read-only git and the search/read words detection agents use.
  * TestAllowlistAudit pins SAFE_COMMAND_WORDS / PURE_READERS to the exact
    audited sets and ties each kept word to the docstring audit.
  * TestClassifyMutants proves every lock trips when weakened.
"""

import ast
import json
import os
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gitguard  # noqa: E402  (sibling module under test)
import gitfixture  # noqa: E402  (shared temp-repo helper)

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
GITGUARD_PY = os.path.join(SCRIPTS_DIR, "gitguard.py")

SENTINEL = "SENTINEL_9f3c"

FIXSTAGE_BYPASS = ('python3 "$VC_ROOT/scripts/fixstage.py" commit --root . '
                   '--finding-json f.json')

# --------------------------------------------------------------------------- #
# tables
# --------------------------------------------------------------------------- #
DENY = (
    "git stash",
    "git stash pop",
    "git stash apply",
    "git stash drop",
    "git stash push -m x",
    "git commit -m x",
    "git checkout main",
    "git switch main",
    "git reset --hard",
    "git restore f",
    "git add .",
    "git merge x",
    "git rebase main",
    "git clean -fd",
    "git branch -D x",
    "git branch foo",
    "git push",
    "git fetch",
    "git pull",
    "git cherry-pick x",
    "git revert x",
    "git update-ref r x",
    "git tag v1",
    "git config user.name x",
    "git co main",
    "git -c core.fsmonitor=x status",
    "git --git-dir=/tmp/x log",
    "git --work-tree=. status",
    "GIT_DIR=/x git log",
    "GIT_EXTERNAL_DIFF=x git diff",
    "git log && git checkout main",
    "git log; git stash pop",
    "git log | sh",
    "git log\ngit stash pop",
    "g''it stash",
    '"git" stash pop',
    "\\git stash",
    "GIT stash",
    "/usr/bin/git stash",
    "git log $(git stash)",
    "git log `x`",
    "git ${X} log",
    "eval git stash",
    'sh -c "git stash"',
    "bash -c 'git log'",
    "xargs git stash",
    "env GIT_DIR=x git log",
    "git diff --output=/tmp/x",
    "git log --output x",
    "git grep -O foo",
    "git diff --ext-diff",
    "git log > .git/x",
    "timeout 5 git stash",
    "cat x | git apply",
    "find . -name x -exec git add {} ;",
    "python3 -c \"import os; os.system('git stash')\"",
    'git log "unbalanced',
    "git ls-remote --upload-pack='git stash pop; git-upload-pack' .",
    "git ls-remote --upload-p=x .",
    "git ls-remote origin",
    # bare-repo probe: `remote show` without -n runs remote.origin.uploadpack
    "git remote show origin",
    "git remote show --verbose origin",
    # -C / cd to anything but the reviewed repo root (repo_root unknown here)
    "git -C sub diff HEAD~1 | head -20",
    "git -C vendor/x.git show HEAD",
    "git -C /elsewhere log -1",
    "cd vendor/x.git && git show HEAD",
    "cd && git status",
    "cd - && git status",
    # unquoted zsh glob qualifier / process substitution stay operators
    "ls *(e:'git stash':)",
    "print -l =(cmd)",
    "git log; git stash pop # quoted ';' elsewhere: 'a;b'",
)

# (command, expected reason constant name, plugin_scripts)
TRUSTED_BYPASS_DENY = (
    (FIXSTAGE_BYPASS, "REASON_TRUSTED_SCRIPT", frozenset()),
    ("python3 /abs/plugins/vibe-check/scripts/fixstage.py commit --root /r "
     "--finding-json /r/f.json", "REASON_TRUSTED_SCRIPT", frozenset()),
    ("/abs/plugins/vibe-check/scripts/fixstage.py commit --root /r",
     "REASON_TRUSTED_SCRIPT", frozenset()),
    ("./fixstage.py undo --root .", "REASON_TRUSTED_SCRIPT", frozenset()),
    ("python3 FIXSTAGE.PY commit", "REASON_TRUSTED_SCRIPT", frozenset()),
    ("python3 x/gitsnap.py check", "REASON_TRUSTED_SCRIPT", frozenset()),
    ("python3 x/fixcheck.py after", "REASON_TRUSTED_SCRIPT", frozenset()),
    ("python3 x/fixcommit.py f.json", "REASON_TRUSTED_SCRIPT",
     frozenset()),
    ("python3 x/gitguard.py reset --root .", "REASON_TRUSTED_SCRIPT",
     frozenset()),
    ("cat /abs/scripts/gitsnap.py", "REASON_TRUSTED_SCRIPT", frozenset()),
    ("cat /abs/scripts/batchsnap.py", "REASON_TRUSTED_SCRIPT",
     frozenset({"batchsnap.py"})),
)

# (command, expected reason constant name)
NON_GIT_DENY = (
    # interpreters / shells / indirection
    ("python3 -c 'print(1)'", "REASON_INDIRECTION"),
    ("python3 run.py", "REASON_INDIRECTION"),
    ("node x.js", "REASON_INDIRECTION"),
    ("perl -e 1", "REASON_INDIRECTION"),
    ("ruby x.rb", "REASON_INDIRECTION"),
    ("bash x.sh", "REASON_INDIRECTION"),
    ("sh < x.sh", "REASON_INDIRECTION"),
    ("cat x | sh", "REASON_INDIRECTION"),
    ("xargs rm", "REASON_INDIRECTION"),
    ("sudo ls", "REASON_INDIRECTION"),
    ("eval ls", "REASON_INDIRECTION"),
    ("exec ls", "REASON_INDIRECTION"),
    (". ./env.sh", "REASON_INDIRECTION"),
    ("source x", "REASON_INDIRECTION"),
    ("env python3 x.py", "REASON_INDIRECTION"),
    ("timeout 5 python3 x.py", "REASON_INDIRECTION"),
    ("osascript -e 1", "REASON_INDIRECTION"),
    ("find . -delete", "REASON_INDIRECTION"),
    ("find . -name x -exec rm {} ;", "REASON_INDIRECTION"),
    ("find . -ok rm {} ;", "REASON_INDIRECTION"),
    ("find . -okdir rm {} ;", "REASON_INDIRECTION"),
    # implicit-write words (pass-4 finding 1) — not allowlisted
    ("uniq /dev/null src/app.py", "REASON_NOT_ALLOWLISTED"),
    ("uniq a b", "REASON_NOT_ALLOWLISTED"),
    ("uniq -c f", "REASON_NOT_ALLOWLISTED"),
    ("sort -o src/app.py src/app.py", "REASON_NOT_ALLOWLISTED"),
    ("sort --output=f f", "REASON_NOT_ALLOWLISTED"),
    ("sort f", "REASON_NOT_ALLOWLISTED"),
    ("split -l 1 f", "REASON_NOT_ALLOWLISTED"),
    ("csplit f 1", "REASON_NOT_ALLOWLISTED"),
    ("file -C -m x", "REASON_NOT_ALLOWLISTED"),
    ("file f.py", "REASON_NOT_ALLOWLISTED"),
    ("diff a b", "REASON_NOT_ALLOWLISTED"),
    ("cmp a b", "REASON_NOT_ALLOWLISTED"),
    ("comm a b", "REASON_NOT_ALLOWLISTED"),
    ("nl f", "REASON_NOT_ALLOWLISTED"),
    ("column f", "REASON_NOT_ALLOWLISTED"),
    ("dd if=a of=b", "REASON_NOT_ALLOWLISTED"),
    ("truncate -s 0 f", "REASON_NOT_ALLOWLISTED"),
    ("install a b", "REASON_NOT_ALLOWLISTED"),
    ("ln -s a b", "REASON_NOT_ALLOWLISTED"),
    ("patch f", "REASON_NOT_ALLOWLISTED"),
    ("tar xf a.tar", "REASON_NOT_ALLOWLISTED"),
    ("curl -o f x", "REASON_NOT_ALLOWLISTED"),
    ("ed f", "REASON_NOT_ALLOWLISTED"),
    # general unlisted words
    ("make", "REASON_NOT_ALLOWLISTED"),
    ("npm test", "REASON_NOT_ALLOWLISTED"),
    ("rm -rf x", "REASON_NOT_ALLOWLISTED"),
    ("mv a b", "REASON_NOT_ALLOWLISTED"),
    ("cp a b", "REASON_NOT_ALLOWLISTED"),
    ("touch x", "REASON_NOT_ALLOWLISTED"),
    ("tee f", "REASON_NOT_ALLOWLISTED"),
    ("sed -i s/a/b/ f", "REASON_SED_FORM"),
    ("awk '{system(\"x\")}' f", "REASON_NOT_ALLOWLISTED"),
    ("alias g=fixstage", "REASON_NOT_ALLOWLISTED"),
    ("$CMD arg", "REASON_NOT_ALLOWLISTED"),
    ("./run", "REASON_NOT_ALLOWLISTED"),
    ("/tmp/x/grep foo", "REASON_NOT_ALLOWLISTED"),
    # substitution / heredoc
    ("ls $(echo x)", "REASON_SUBSTITUTION"),
    ("ls ${HOME}", "REASON_SUBSTITUTION"),
    ("ls `pwd`", "REASON_SUBSTITUTION"),
    ("cat <(ls)", "REASON_SUBSTITUTION"),
    ("cat <<EOF\nx\nEOF", "REASON_SUBSTITUTION"),
    # file output redirection
    ("echo x > f.txt", "REASON_REDIRECT"),
    ("cat a >> b", "REASON_REDIRECT"),
    ("ls 1> out", "REASON_REDIRECT"),
    # reader exec/write flags
    ("rg --pre ./x foo", "REASON_NOT_ALLOWLISTED"),
    ("rg --pre=x foo", "REASON_NOT_ALLOWLISTED"),
    ("rg --pre-glob '*' --pre x foo", "REASON_NOT_ALLOWLISTED"),
    ("rg --hostname-bin ./x foo", "REASON_NOT_ALLOWLISTED"),
    ("rg --hostname-bin=./x foo", "REASON_NOT_ALLOWLISTED"),
    ("rg -z foo", "REASON_NOT_ALLOWLISTED"),
    ("rg -nz foo", "REASON_NOT_ALLOWLISTED"),
    ("rg --search-zip foo", "REASON_NOT_ALLOWLISTED"),
    ("find . -fprint out", "REASON_NOT_ALLOWLISTED"),
    ("find . -fprint0 out", "REASON_NOT_ALLOWLISTED"),
    ("find . -fprintf out x", "REASON_NOT_ALLOWLISTED"),
    ("find . -fls out", "REASON_NOT_ALLOWLISTED"),
    # sed outside the numeric-print grammar (whole script validated, D-19)
    ("sed -i 's/a/b/' f", "REASON_SED_FORM"),
    ("sed -n 'w /tmp/x' f", "REASON_SED_FORM"),
    ("sed -n '1p' -i f", "REASON_SED_FORM"),
    ("sed -n '/re/p' f", "REASON_SED_FORM"),
    ("sed -n 's/a/b/w x' f", "REASON_SED_FORM"),
    ("sed -n -e '1p' -e 'e' f", "REASON_SED_FORM"),
    ("sed -f script f", "REASON_SED_FORM"),
    ("sed -n -f script f", "REASON_SED_FORM"),
    ("sed -n '1p;e' f", "REASON_SED_FORM"),
    ("sed -n '1r /etc/passwd' f", "REASON_SED_FORM"),
    ("sed -n '1R x' f", "REASON_SED_FORM"),
    ("sed -n '1W x' f", "REASON_SED_FORM"),
    ("sed -n '1,5p w x' f", "REASON_SED_FORM"),
    ("sed -n '1e date' f", "REASON_SED_FORM"),
    ("sed '1p' f", "REASON_SED_FORM"),
    ("sed -n", "REASON_SED_FORM"),
    ("sed -n -e", "REASON_SED_FORM"),
    ("sed -n 'p' f", "REASON_SED_FORM"),
    ("sed -n '1,5 p' f", "REASON_SED_FORM"),
    ("sed -ne '1p' f", "REASON_SED_FORM"),
    ("sed -n -E '1p' f", "REASON_SED_FORM"),
    ("sed -n --in-place '1p' f", "REASON_SED_FORM"),
    ("sed -n --expression=1p f", "REASON_SED_FORM"),
    ("sed -n '1p' -- f", "REASON_SED_FORM"),
    ("sed -n '1p' -s f", "REASON_SED_FORM"),
    ("sed -n '0~2p' f", "REASON_SED_FORM"),
    ("sed -n '1!p' f", "REASON_SED_FORM"),
    ("sed -n '1p' f -i", "REASON_SED_FORM"),
    ("cat f | sed -n 'w out'", "REASON_SED_FORM"),
    # cd grammar (no repo root known: every absolute operand refuses)
    ("cd a b", "REASON_CD_FORM"),
    ("cd -", "REASON_CD_FORM"),
    ("cd", "REASON_CD_FORM"),
    ("cd && grep x f", "REASON_CD_FORM"),
    ("cd ~", "REASON_CD_FORM"),
    ("cd -e /x", "REASON_CD_FORM"),
    ("cd -- /x", "REASON_CD_FORM"),
    ("cd sub && grep x f", "REASON_CD_FORM"),
    ("cd /outside && grep x f", "REASON_CD_FORM"),
    # legitimately unprovable forms stay refused
    ("wc -l f | sort -n", "REASON_NOT_ALLOWLISTED"),
    ("for f in *; do cat $f; done", "REASON_NOT_ALLOWLISTED"),
    ("xargs cat", "REASON_INDIRECTION"),
)

ALLOW = (
    "git log --oneline -5",
    "git diff HEAD~1",
    "git show HEAD:f.py",
    "git blame -L 1,5 f.py",
    "git status --porcelain",
    "git rev-parse --show-toplevel",
    "git ls-files -s",
    "git -C . diff HEAD~1 | head -20",
    "git -C ./ log -1",
    "git remote show -n origin",
    "git --no-pager log -1",
    "git log 2>/dev/null",
    "git diff 2>&1 | head",
    "GIT_PAGER=cat git log -3",
    "git stash list",
    "git stash show -p stash@{0}",
    "git branch",
    "git branch -a",
    "git branch --show-current",
    "git branch --list 'feat/*'",
    "git tag",
    "git tag -l 'v*'",
    "git remote -v",
    "git config --get user.name",
    "git config --list",
    "git worktree list",
    "git reflog",
    "git merge-base HEAD main",
    "git cat-file -p HEAD",
    "grep -rn foo src",
    "rg TODO",
    "find . -name '*.py'",
    "cat .github/workflows/ci.yml",
    "grep -rn x .gitignore",
    "ls -la",
    "wc -l f.py",
    "echo hi",
    "cat .git/HEAD",
    "grep -rn fixstage src",
    'rg -n "def commit" plugins/vibe-check/scripts',
    "/usr/bin/grep -rn foo .",
    "rg -n foo src | cut -d: -f1",
    "grep -c foo f.py | head -1",
    "rg -n -g '*.py' foo",
    "stat f.py",
    "tail -n 5 f.py",
    "ls 2>/dev/null",
    "pwd",
    # escaped / quoted punctuation is a literal word, not an operator
    r'find . -maxdepth 1 -type f \( -name "PLAN.md" -o -name "*.md" \)',
    'grep -n "a;b" file',
    "grep -n 'x|y' file",
    'grep -n ">" file',
    "grep -n '&&' file",
    # sed only as `sed -n` + numeric-address print scripts
    "sed -n '560,760p' file",
    "git show HEAD:f | sed -n '598,606p;664,672p'",
    "sed -n '$p' f",
    "sed -n '1,+5p' f",
    "sed -n '1,$p' f",
    "sed --quiet '3p' f",
    "sed --silent 3p f",
    "sed -n -e '1p' -e '5,6p' f",
    "sed -n '1p;' a b",
    "cat f | sed -n '2,3p'",
    "git grep -n token -- '*.md'",
    "cd . && grep x f",
)

# (command, expected verdict) with repo_root="/r": "allowed" or a reason name.
DIR_ROOT = "/r"
DIR_TARGET_CASES = (
    ("git -C . log -1", "allowed"),
    ("git -C /r log -1", "allowed"),
    ("git -C /r/ log -1", "allowed"),
    ("git -C /r/./ log -1", "allowed"),
    ("git -C /r -C . log -1", "allowed"),
    ("git -C /r/vendor/x.git show HEAD", "REASON_GIT_OTHER_DIR"),
    ("git -C vendor/x.git show HEAD", "REASON_GIT_OTHER_DIR"),
    ("git -C /r/vendor/x.git/link/.. show HEAD", "REASON_GIT_OTHER_DIR"),
    ("git -C /r/sub/.. log -1", "REASON_GIT_OTHER_DIR"),
    ("git -C /r/sub log -1", "REASON_GIT_OTHER_DIR"),
    ("git -C /elsewhere show HEAD", "REASON_GIT_OTHER_DIR"),
    ("git -C //r log -1", "REASON_GIT_OTHER_DIR"),
    ("git -C ~ log -1", "REASON_GIT_OTHER_DIR"),
    ("git -C '' log -1", "REASON_GIT_OTHER_DIR"),
    ("git -C /r -C sub log -1", "REASON_GIT_OTHER_DIR"),
    ("git -C=/r log -1", "REASON_GIT_GLOBAL_OPT"),
    ("git -C/r log -1", "REASON_GIT_GLOBAL_OPT"),
    ("cd vendor/x.git && git show HEAD", "REASON_GIT_OTHER_DIR"),
    ("cd /r/vendor/x.git/link/.. && git show HEAD", "REASON_GIT_OTHER_DIR"),
    ("cd -P /r/vendor/x.git/link/.. && git show HEAD",
     "REASON_GIT_OTHER_DIR"),
    ("cd -L /r/vendor/x.git && git show HEAD", "REASON_GIT_OTHER_DIR"),
    ("cd && git status", "REASON_GIT_OTHER_DIR"),
    ("cd - && git status", "REASON_GIT_OTHER_DIR"),
    ("cd ~ && git status", "REASON_GIT_OTHER_DIR"),
    ("cd /r /x && git status", "REASON_GIT_OTHER_DIR"),
    # only -L/-P are skipped as flags; anything else counts as an operand
    ("cd -e /r && git log -1", "REASON_GIT_OTHER_DIR"),
    ("cd -- /r && git log -1", "REASON_GIT_OTHER_DIR"),
    ("cd /r/sub; git log -1", "REASON_GIT_OTHER_DIR"),
    ("git log -1; cd /r/sub", "REASON_GIT_OTHER_DIR"),
    ("cd /r/sub && timeout 5 git log -1", "REASON_GIT_OTHER_DIR"),
    ("cd /r/sub && /usr/bin/git log -1", "REASON_GIT_OTHER_DIR"),
    ("command cd /r/sub && git log -1", "REASON_GIT_OTHER_DIR"),
    ("CD /r/sub && git log -1", "REASON_GIT_OTHER_DIR"),
    # cd to the root (spelled absolute or `.`) then git is allowed
    ("cd /r && git log -1", "allowed"),
    ("cd . && git log -1", "allowed"),
    ("cd /r; grep -n \"finalize\" commands/review.md", "allowed"),
    ("cd /r && grep -rn x .", "allowed"),
    # a git-less cd to a directory that does not exist is a cd-form refusal
    ("cd /r/sub && ls", "REASON_CD_FORM"),
    ("cd a b", "REASON_CD_FORM"),
    ("cd sub && grep x f", "REASON_CD_FORM"),
    ("cd && grep x f", "REASON_CD_FORM"),
)


def _old_lenient_remote(args):
    """The pre-hardening `remote` validator: `show` without -n allowed."""
    if not args:
        return True, "allowed"
    if args in (["-v"], ["--verbose"]):
        return True, "allowed"
    if args[0] == "get-url" and all(
            a in ("--push", "--all") or not a.startswith("-")
            for a in args[1:]):
        return True, "allowed"
    if args[0] == "show" and all(
            a == "-n" or not a.startswith("-") for a in args[1:]):
        return True, "allowed"
    return False, gitguard.REASON_GIT_ARGS


def _realpath_dir_target(operand, repo_root):
    """The rejected realpath design: physical resolution vs the root."""
    if os.path.realpath(os.path.join(repo_root, operand)) \
            == os.path.realpath(repo_root):
        return "root", None
    return None, gitguard.REASON_GIT_OTHER_DIR


AUDITED_READERS = frozenset(
    {"cat", "head", "tail", "ls", "wc", "grep", "rg", "stat", "find"})
AUDITED_WORDS = frozenset({"git"}) | AUDITED_READERS | frozenset(
    {"echo", "printf", "true", "false", "cut", "tr", "basename", "dirname",
     "pwd", "cd", "sed"})
REMOVED_WORDS = frozenset(
    {"uniq", "sort", "diff", "cmp", "comm", "nl", "column", "file", "tee",
     "split", "csplit", "dd", "truncate"})

FUZZ = (
    "'", '"', "\\", "&&&", "|", "(", "{", "}", ")", ";", ";;", "&", "||",
    "git '", 'git "', "git \\", "`", "$", "$(", "${", "<", ">", ">>", "<<",
    "\n", "\t", "git\n\n", "a\\\nb", "''", '""', "git -C", "git -c",
    "env", "timeout", "nice -n", "command",
    "\x00", "git\x00stash", "éè git", "cat <>",
)


def _tokenize_legacy(command):
    """The pre-hardening tokenizer: shlex with punctuation_chars, which makes
    an escaped `\\(` or a quoted `">"` an operator token."""
    import shlex
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


FIND_ESCAPED = (r'find . -maxdepth 1 -type f \( -name "PLAN.md" '
                r'-o -name "*.md" \)')


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _reason(name):
    return getattr(gitguard, name)


def _audit_section():
    """The 'Allowlist audit' section of the module docstring."""
    doc = gitguard.__doc__ or ""
    start = doc.find("Allowlist audit")
    if start < 0:
        return ""
    end = doc.find("Removed words", start)
    return doc[start:end if end > start else len(doc)]


def _audit_lock_holds():
    """The exact-set assertions TestAllowlistAudit makes (reused by mutants)."""
    return (gitguard.SAFE_COMMAND_WORDS == AUDITED_WORDS
            and gitguard.PURE_READERS == AUDITED_READERS
            and not (REMOVED_WORDS & gitguard.SAFE_COMMAND_WORDS))


# --------------------------------------------------------------------------- #
# DENY
# --------------------------------------------------------------------------- #
class TestClassifyDeny(unittest.TestCase):
    def test_deny_table(self):
        for cmd in DENY:
            with self.subTest(cmd=cmd):
                allowed, reason = gitguard.classify(cmd)
                self.assertIs(allowed, False, cmd)
                self.assertTrue(reason.startswith("refused:"), reason)

    def test_deny_table_with_repo_root(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.realpath(tmp)
            os.makedirs(os.path.join(root, "sub"))
            for cmd in DENY:
                with self.subTest(cmd=cmd):
                    allowed, reason = gitguard.classify(cmd, repo_root=root)
                    self.assertIs(allowed, False, cmd)
                    self.assertTrue(reason.startswith("refused:"), reason)

    def test_deny_table_has_the_incident_and_edge_forms(self):
        for literal in ("git stash pop", "g''it stash",
                        "git -c core.fsmonitor=x status"):
            self.assertIn(literal, DENY)
        self.assertTrue(any("\n" in c for c in DENY))


class TestClassifyNonGitBypass(unittest.TestCase):
    def test_trusted_script_bypass_table(self):
        for cmd, reason_name, scripts in TRUSTED_BYPASS_DENY:
            with self.subTest(cmd=cmd):
                allowed, reason = gitguard.classify(cmd, scripts)
                self.assertIs(allowed, False)
                self.assertEqual(reason, _reason(reason_name))

    def test_the_checker_bypass_is_refused(self):
        allowed, reason = gitguard.classify(FIXSTAGE_BYPASS)
        self.assertIs(allowed, False)
        self.assertEqual(reason, gitguard.REASON_TRUSTED_SCRIPT)

    def test_non_git_deny_table(self):
        for cmd, reason_name in NON_GIT_DENY:
            with self.subTest(cmd=cmd):
                allowed, reason = gitguard.classify(cmd)
                self.assertIs(allowed, False)
                self.assertEqual(reason, _reason(reason_name))

    def test_dynamic_set_is_needed_for_unlisted_script(self):
        # Without the hook-supplied listing batchsnap.py is just a file read.
        self.assertEqual(gitguard.classify("cat /abs/scripts/batchsnap.py"),
                         (True, "allowed"))


# --------------------------------------------------------------------------- #
# ALLOW
# --------------------------------------------------------------------------- #
class TestClassifyAllow(unittest.TestCase):
    def test_allow_table(self):
        for cmd in ALLOW:
            with self.subTest(cmd=cmd):
                self.assertEqual(gitguard.classify(cmd), (True, "allowed"))
                self.assertEqual(gitguard.classify(cmd, repo_root="/r"),
                                 (True, "allowed"))


class TestDirTarget(unittest.TestCase):
    """`git -C` and `cd`-then-git accept only the reviewed repo root."""

    def test_dir_target_table(self):
        for cmd, expected in DIR_TARGET_CASES:
            with self.subTest(cmd=cmd):
                verdict = gitguard.classify(cmd, repo_root=DIR_ROOT)
                if expected == "allowed":
                    self.assertEqual(verdict, (True, "allowed"))
                else:
                    self.assertEqual(verdict, (False, _reason(expected)))

    def test_no_repo_root_refuses_every_target_but_dot(self):
        self.assertEqual(gitguard.classify("git -C . log -1"),
                         (True, "allowed"))
        for cmd in ("git -C /r log -1", "git -C sub log -1",
                    "cd /r && git log -1"):
            with self.subTest(cmd=cmd):
                self.assertEqual(gitguard.classify(cmd),
                                 (False, gitguard.REASON_GIT_OTHER_DIR))

    def test_remote_show_requires_n(self):
        self.assertEqual(gitguard.classify("git remote show origin"),
                         (False, gitguard.REASON_GIT_ARGS))
        self.assertEqual(gitguard.classify("git remote show -n origin"),
                         (True, "allowed"))
        self.assertEqual(gitguard.classify("git remote show origin -n"),
                         (True, "allowed"))
        self.assertEqual(gitguard.classify("git remote -v"),
                         (True, "allowed"))
        self.assertEqual(gitguard.classify("git remote show -n -v origin"),
                         (False, gitguard.REASON_GIT_ARGS))

    def test_resolver_contract(self):
        r = gitguard._resolve_dir_target
        self.assertEqual(r(".", None), ("root", None))
        self.assertEqual(r("./", None), ("root", None))
        self.assertEqual(r(".", "/r"), ("root", None))
        self.assertEqual(r("/r", "/r"), ("root", None))
        self.assertEqual(r("/r/./", "/r"), ("root", None))
        for operand, root in (("sub", "/r"), ("/r", None), ("", "/r"),
                              (None, "/r"), ("-", "/r"), ("~", "/r"),
                              ("/r/x/..", "/r"), ("/rr", "/r"),
                              ("/", "/r"), ("/r/../r", "/r"),
                              ("r", "r"), ("vendor", "vendor")):
            with self.subTest(operand=operand, root=root):
                self.assertEqual(r(operand, root),
                                 (None, gitguard.REASON_CD_FORM))

    def test_resolver_subdir_kinds(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.realpath(tmp)
            for rel in ("src/a", "nested/inner", "bare/b", "sub.git/x"):
                os.makedirs(os.path.join(root, rel))
            open(os.path.join(root, "nested", ".git"), "w").close()
            for name in ("HEAD",):
                open(os.path.join(root, "bare", "b", name), "w").close()
            for name in ("objects", "refs"):
                os.makedirs(os.path.join(root, "bare", "b", name))
            os.symlink(os.path.join(root, "src"),
                       os.path.join(root, "link"))
            r = gitguard._resolve_dir_target
            self.assertEqual(r(root + "/src", root), ("subdir", None))
            self.assertEqual(r(root + "/src/a/", root), ("subdir", None))
            self.assertEqual(r(root + "/bare", root), ("subdir", None))
            for rel in ("nested", "nested/inner", "bare/b", "sub.git",
                        "sub.git/x"):
                with self.subTest(rel=rel):
                    self.assertEqual(r(root + "/" + rel, root),
                                     (None, gitguard.REASON_GIT_OTHER_DIR))
            # not a git dir, but still not provably safe: a cd-form refusal
            for rel in ("link", "link/a", "missing", "src/a/../a"):
                with self.subTest(rel=rel):
                    self.assertEqual(r(root + "/" + rel, root),
                                     (None, gitguard.REASON_CD_FORM))
            # git never accepts a subdir, even a clean one
            self.assertEqual(
                gitguard.classify("git -C %s/src log -1" % root,
                                  repo_root=root),
                (False, gitguard.REASON_GIT_OTHER_DIR))

    def test_allow_table_has_no_removed_word(self):
        self.assertFalse([c for c in ALLOW if c.split()[0] in REMOVED_WORDS])


# --------------------------------------------------------------------------- #
# fail closed
# --------------------------------------------------------------------------- #
class TestClassifyFailClosed(unittest.TestCase):
    def test_non_string_and_empty_refused(self):
        for value in (None, 123, b"git log", "", "   ", ["git", "log"]):
            with self.subTest(value=value):
                allowed, reason = gitguard.classify(value)
                self.assertIs(allowed, False)
                self.assertTrue(reason.startswith("refused:"))

    def test_never_raises(self):
        for cmd in FUZZ:
            with self.subTest(cmd=cmd):
                allowed, reason = gitguard.classify(cmd)
                self.assertIsInstance(allowed, bool)
                self.assertIsInstance(reason, str)

    def test_fuzz_git_forms_refused(self):
        for cmd in FUZZ:
            if "git" in cmd:
                with self.subTest(cmd=cmd):
                    self.assertIs(gitguard.classify(cmd)[0], False)

    def test_reason_never_echoes_command(self):
        for cmd in ("git stash pop " + SENTINEL,
                    "python3 x/fixstage.py " + SENTINEL,
                    SENTINEL + " arg",
                    "ls $(" + SENTINEL + ")",
                    "echo x > " + SENTINEL,
                    "git -C /" + SENTINEL + " log",
                    "cd /" + SENTINEL + " && git log"):
            with self.subTest(cmd=cmd):
                allowed, reason = gitguard.classify(cmd)
                self.assertIs(allowed, False)
                self.assertNotIn(SENTINEL, reason)
                self.assertNotIn(SENTINEL.lower(), reason)

    def test_hash_does_not_hide_a_second_command(self):
        # shlex treats `#` as a comment start even mid-word; bash does not.
        self.assertIs(gitguard.classify("echo a#b; git stash pop")[0], False)


# --------------------------------------------------------------------------- #
# tokenizer: only unquoted, unescaped punctuation is an operator
# --------------------------------------------------------------------------- #
class TestTokenize(unittest.TestCase):
    def _toks(self, command):
        return gitguard._tokenize(command)

    def _shape(self, command):
        return [(str(t), t.is_operator) for t in self._toks(command)]

    def test_tokenize_escaped_parens_are_words(self):
        self.assertEqual(self._shape(r"find . \( -name x \)"), [
            ("find", False), (".", False), ("(", False), ("-name", False),
            ("x", False), (")", False)])

    def test_tokenize_quoted_punctuation_is_a_word(self):
        self.assertEqual(self._shape("grep 'a;b' \"x|y\" \">\" f"), [
            ("grep", False), ("a;b", False), ("x|y", False), (">", False),
            ("f", False)])

    def test_tokenize_unquoted_operators_group_like_bash(self):
        self.assertEqual(self._shape("a&&b||c;d|e 2>&1 >/dev/null"), [
            ("a", False), ("&&", True), ("b", False), ("||", True),
            ("c", False), (";", True), ("d", False), ("|", True),
            ("e", False), ("2", False), (">&", True), ("1", False),
            (">", True), ("/dev/null", False)])

    def test_tokenize_unquoted_zsh_qualifier_paren_is_an_operator(self):
        shape = self._shape("ls *(e:'git stash':)")
        self.assertIn(("(", True), shape)
        self.assertIn((")", True), shape)

    def test_tokenize_quote_and_escape_flags(self):
        toks = self._toks("a 'b' c\\d \"\" x\"y\"")
        self.assertEqual([str(t) for t in toks], ["a", "b", "cd", "", "xy"])
        self.assertEqual([t.quoted for t in toks],
                         [False, True, False, True, True])
        self.assertEqual([t.escaped for t in toks],
                         [False, False, True, False, False])

    def test_tokenize_double_quote_escapes(self):
        self.assertEqual([str(t) for t in self._toks('"a\\"b" "\\x"')],
                         ['a"b', "\\x"])

    def test_tokenize_hash_is_literal(self):
        self.assertEqual([str(t) for t in self._toks("echo a#b")],
                         ["echo", "a#b"])

    def test_tokenize_unterminated_refuses(self):
        for cmd in ("grep 'x", 'grep "x', "grep x\\"):
            with self.subTest(cmd=cmd):
                with self.assertRaises(ValueError):
                    self._toks(cmd)
                self.assertEqual(gitguard.classify(cmd),
                                 (False, gitguard.REASON_UNPARSEABLE))

    def test_find_escaped_parens_allowed(self):
        self.assertEqual(gitguard.classify(FIND_ESCAPED), (True, "allowed"))

    def test_tokeniz_legacy_mutant_refuses_find_escaped(self):
        self.assertEqual(gitguard.classify(FIND_ESCAPED), (True, "allowed"))
        with mock.patch.object(gitguard, "_tokenize", _tokenize_legacy):
            allowed, reason = gitguard.classify(FIND_ESCAPED)
            self.assertIs(allowed, False, "legacy tokenizer mutant survived")
            self.assertEqual(reason, gitguard.REASON_NOT_ALLOWLISTED)
            self.assertEqual(gitguard.classify('grep -n ">" file'),
                             (False, gitguard.REASON_REDIRECT))

    def test_chained_second_command_still_split(self):
        self.assertEqual(gitguard.classify("git log; git stash pop"),
                         (False, gitguard.REASON_GIT_ARGS))


# --------------------------------------------------------------------------- #
# cd and sed argv validators (complete-command validation)
# --------------------------------------------------------------------------- #
# (command template with {R} = the fixture repo root, expected verdict)
CD_FIXTURE_CASES = (
    ("cd {R}; grep -n \"finalize\" commands/review.md", "allowed"),
    ("cd {R} && grep -rn x .", "allowed"),
    ("cd {R}/", "allowed"),
    ("cd {R}/sub && grep x f", "allowed"),
    ("cd -L {R}/sub && grep x f", "allowed"),
    ("cd -P {R}/sub && grep x f", "allowed"),
    ("cd {R}/sub/deep", "allowed"),
    ("cd {R} && git log -1", "allowed"),
    ("cd {R}/sub && git log -1", "REASON_GIT_OTHER_DIR"),
    ("cd {R}/sub/.. && grep x f", "REASON_CD_FORM"),
    ("cd {R}/lnk && grep x f", "REASON_CD_FORM"),
    ("cd {R}/vendor/x.git/link && grep x f", "REASON_GIT_OTHER_DIR"),
    ("cd {R}/vendor/x.git && grep x HEAD", "REASON_GIT_OTHER_DIR"),
    ("cd {R}/vendor/x.git", "REASON_GIT_OTHER_DIR"),
    ("cd {R}/vendor/x.git/refs && ls", "REASON_GIT_OTHER_DIR"),
    ("cd vendor/x.git && git show HEAD", "REASON_GIT_OTHER_DIR"),
    ("cd vendor/x.git && grep x HEAD", "REASON_CD_FORM"),
    ("cd {R}/missing && ls", "REASON_CD_FORM"),
    ("cd /outside && grep x f", "REASON_CD_FORM"),
    ("cd {R}/sub {R}", "REASON_CD_FORM"),
    ("cd -- {R}/sub", "REASON_CD_FORM"),
    ("cd -e {R}/sub", "REASON_CD_FORM"),
    ("cd -", "REASON_CD_FORM"),
    ("cd", "REASON_CD_FORM"),
    ("cd ~", "REASON_CD_FORM"),
    ("cd sub && grep x f", "REASON_CD_FORM"),
    # a glob or brace operand is not the directory bash will enter
    ("cd {R}/[v] && grep x HEAD", "REASON_CD_FORM"),
    ("cd {R}/su? && grep x f", "REASON_CD_FORM"),
    ("cd {R}/s* && grep x f", "REASON_CD_FORM"),
    ("cd {R}/{{sub,v}} && grep x f", "REASON_CD_FORM"),
)


def _make_cd_fixture(test):
    """A repo root with sub/deep, a bare-shaped vendor/x.git (whose link ->
    vendor), lnk -> sub, a bare-shaped v and a literal directory `[v]`."""
    import tempfile
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    root = os.path.realpath(tmp.name)
    os.makedirs(os.path.join(root, "sub", "deep"))
    os.makedirs(os.path.join(root, "[v]"))
    for bare in (os.path.join(root, "vendor", "x.git"),
                 os.path.join(root, "v")):
        os.makedirs(os.path.join(bare, "objects"))
        os.makedirs(os.path.join(bare, "refs"))
        open(os.path.join(bare, "HEAD"), "w").close()
    os.symlink(os.path.join(root, "vendor"),
               os.path.join(root, "vendor", "x.git", "link"))
    os.symlink(os.path.join(root, "sub"), os.path.join(root, "lnk"))
    return root


class TestCdSedValidators(unittest.TestCase):
    def setUp(self):
        self.root = _make_cd_fixture(self)

    def test_fixture_has_what_the_cases_assume(self):
        r = gitguard._resolve_dir_target
        self.assertEqual(r(self.root + "/sub", self.root), ("subdir", None))
        self.assertTrue(os.path.islink(self.root + "/lnk"))
        self.assertTrue(gitguard._is_bare_shaped(self.root + "/v"))
        # the resolver alone would accept the literal `[v]` directory, so
        # only the operand-form check stands between bash's glob (-> v, a
        # bare repo) and an allowed cd
        self.assertEqual(r(self.root + "/[v]", self.root), ("subdir", None))

    def test_cd_fixture_table(self):
        for template, expected in CD_FIXTURE_CASES:
            cmd = template.format(R=self.root)
            with self.subTest(cmd=cmd):
                verdict = gitguard.classify(cmd, repo_root=self.root)
                if expected == "allowed":
                    self.assertEqual(verdict, (True, "allowed"))
                else:
                    self.assertEqual(verdict, (False, _reason(expected)))

    def test_sed_validator_direct(self):
        ok = gitguard._classify_sed
        self.assertEqual(ok(["-n", "1p", "f"]), (True, "allowed"))
        self.assertEqual(ok(["-n", "-e", "1p", "-e", "$p"]),
                         (True, "allowed"))
        for args in ([], ["-n"], ["1p", "f"], ["-n", "1p", "-f"],
                     ["-n", "1pw"], ["-n", "1p;;2p"], ["-n", ";"],
                     ["-n", "+1p"], ["-n", "1,2,3p"], ["-n", "$,+p"]):
            with self.subTest(args=args):
                self.assertEqual(ok(args), (False, gitguard.REASON_SED_FORM))

    def test_cd_validator_has_no_path_logic_of_its_own(self):
        with open(GITGUARD_PY, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
              and n.name == "_classify_cd"][0]
        names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
        attrs = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
        self.assertIn("_resolve_dir_target", names)
        self.assertFalse({"realpath", "getcwd", "abspath", "normpath",
                          "isdir", "islink", "lexists"} & attrs, attrs)

    # mutants -------------------------------------------------------------
    def test_sed_validator_mutant(self):
        cmd = "sed -i 's/a/b/' f"
        self.assertEqual(gitguard.classify(cmd),
                         (False, gitguard.REASON_SED_FORM))
        with mock.patch.object(gitguard, "_classify_sed",
                               lambda args: (True, "allowed")):
            self.assertEqual(gitguard.classify(cmd), (True, "allowed"),
                             "sed validator mutant survived")

    def test_cd_validator_mutant(self):
        cmd = "cd a b"
        self.assertEqual(gitguard.classify(cmd, repo_root=self.root),
                         (False, gitguard.REASON_CD_FORM))
        with mock.patch.object(gitguard, "_classify_cd",
                               lambda args, repo_root: (True, "allowed")):
            self.assertEqual(gitguard.classify(cmd, repo_root=self.root),
                             (True, "allowed"), "cd validator mutant survived")

    def test_sed_and_cd_name_only_mutant(self):
        # with the argv dispatch skipped, the allowlist entry alone would
        # wave every sed and cd form through: the dispatch is what holds
        self.assertIn("sed", gitguard.SAFE_COMMAND_WORDS)
        self.assertIn("cd", gitguard.SAFE_COMMAND_WORDS)
        self.assertEqual(gitguard.ARGV_VALIDATED_WORDS,
                         frozenset({"cd", "sed"}))
        for cmd in ("sed -n 'w /tmp/x' f", "cd a b"):
            self.assertIs(gitguard.classify(cmd)[0], False, cmd)
        with mock.patch.object(gitguard, "ARGV_VALIDATED_WORDS", frozenset()):
            for cmd in ("sed -n 'w /tmp/x' f", "cd a b"):
                with self.subTest(cmd=cmd):
                    self.assertEqual(gitguard.classify(cmd),
                                     (True, "allowed"),
                                     "name-only mutant survived")

    def test_cd_resolver_bypass_mutant(self):
        bare = "cd %s/vendor/x.git && grep x HEAD" % self.root
        rel = "cd sub && grep x f"
        self.assertEqual(gitguard.classify(bare, repo_root=self.root),
                         (False, gitguard.REASON_GIT_OTHER_DIR))
        self.assertEqual(gitguard.classify(rel, repo_root=self.root),
                         (False, gitguard.REASON_CD_FORM))
        with mock.patch.object(gitguard, "_resolve_dir_target",
                               lambda o, r: ("subdir", None)):
            for cmd in (bare, rel):
                with self.subTest(cmd=cmd):
                    self.assertEqual(
                        gitguard.classify(cmd, repo_root=self.root),
                        (True, "allowed"), "resolver bypass survived")


# --------------------------------------------------------------------------- #
# module purity
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    ALLOWED = {"argparse", "json", "os", "re", "sys"}
    FORBIDDEN = {"subprocess", "shutil", "socket"}

    def _imported(self):
        with open(GITGUARD_PY, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        imported = set()
        for node in ast.walk(tree):
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
        for name in ("classify", "READ_ONLY_SUBCOMMANDS",
                     "CONDITIONAL_SUBCOMMANDS", "SAFE_COMMAND_WORDS",
                     "TRUSTED_SCRIPT_BASENAMES", "PURE_READERS",
                     "DENIED_READER_FLAGS", "ALLOWED_GLOBAL_OPTS",
                     "DENIED_GLOBAL_OPTS", "SAFE_ENV_ASSIGNMENTS",
                     "INDIRECTION_WORDS", "DENIED_SUBCOMMAND_FLAGS"):
            self.assertTrue(hasattr(gitguard, name), name)

    def test_trusted_basenames_are_the_contracted_set(self):
        self.assertEqual(gitguard.TRUSTED_SCRIPT_BASENAMES, frozenset(
            {"fixstage.py", "fixcheck.py", "gitsnap.py", "gitguard.py",
             "fixcommit.py", "guard.py"}))

    def test_conditional_subcommands_are_the_contracted_set(self):
        self.assertEqual(set(gitguard.CONDITIONAL_SUBCOMMANDS), {
            "stash", "branch", "tag", "remote", "config", "worktree", "notes",
            "reflog", "submodule", "sparse-checkout", "symbolic-ref"})


# --------------------------------------------------------------------------- #
# allowlist audit (pass-4 finding 1)
# --------------------------------------------------------------------------- #
class TestAllowlistAudit(unittest.TestCase):
    def test_safe_words_are_exactly_the_audited_set(self):
        self.assertEqual(gitguard.SAFE_COMMAND_WORDS, AUDITED_WORDS)

    def test_pure_readers_are_exactly_the_audited_set(self):
        self.assertEqual(gitguard.PURE_READERS, AUDITED_READERS)

    def test_removed_words_absent(self):
        self.assertFalse(REMOVED_WORDS & gitguard.SAFE_COMMAND_WORDS)

    def test_every_kept_word_is_named_in_the_docstring_audit(self):
        section = _audit_section()
        self.assertTrue(section, "module docstring lacks 'Allowlist audit'")
        for word in sorted(gitguard.SAFE_COMMAND_WORDS):
            with self.subTest(word=word):
                self.assertRegex(section, r"\b%s\b" % re.escape(word))

    def test_reader_flags_cover_rg_and_find(self):
        self.assertTrue({"--pre", "--pre-glob", "--hostname-bin",
                         "--search-zip", "-z"}
                        <= gitguard.DENIED_READER_FLAGS["rg"])
        self.assertTrue({"-fprint", "-fprint0", "-fprintf", "-fls"}
                        <= gitguard.DENIED_READER_FLAGS["find"])



# --------------------------------------------------------------------------- #
# mutants — every lock must trip when weakened
# --------------------------------------------------------------------------- #
class TestClassifyMutants(unittest.TestCase):
    def assertAllowed(self, cmd, scripts=frozenset()):
        self.assertEqual(gitguard.classify(cmd, scripts), (True, "allowed"),
                         "mutant did not flip " + repr(cmd))

    def assertDenied(self, cmd, scripts=frozenset()):
        self.assertIs(gitguard.classify(cmd, scripts)[0], False, cmd)

    def test_a_stash_read_only(self):
        mutated = gitguard.READ_ONLY_SUBCOMMANDS | {"stash"}
        self.assertNotEqual(mutated, gitguard.READ_ONLY_SUBCOMMANDS)
        self.assertDenied("git stash pop")
        with mock.patch.object(gitguard, "READ_ONLY_SUBCOMMANDS", mutated):
            self.assertAllowed("git stash pop")

    def test_a2_ls_remote_upload_pack_refused(self):
        cmd = "git ls-remote --upload-pack='git stash pop; git-upload-pack' ."
        mutated = gitguard.READ_ONLY_SUBCOMMANDS | {"ls-remote"}
        self.assertNotIn("ls-remote", gitguard.READ_ONLY_SUBCOMMANDS)
        self.assertDenied(cmd)
        with mock.patch.object(gitguard, "READ_ONLY_SUBCOMMANDS", mutated):
            self.assertAllowed(cmd)

    def test_b_branch_always_allowed(self):
        always = lambda args: (True, "allowed")  # noqa: E731
        self.assertIsNot(gitguard.CONDITIONAL_SUBCOMMANDS["branch"], always)
        self.assertDenied("git branch -D x")
        with mock.patch.dict(gitguard.CONDITIONAL_SUBCOMMANDS,
                             {"branch": always}):
            self.assertAllowed("git branch -D x")

    def test_c_dash_c_global_allowed(self):
        denied = gitguard.DENIED_GLOBAL_OPTS - {"-c"}
        allowed = gitguard.ALLOWED_GLOBAL_OPTS | {"-c"}
        self.assertNotEqual(denied, gitguard.DENIED_GLOBAL_OPTS)
        self.assertNotEqual(allowed, gitguard.ALLOWED_GLOBAL_OPTS)
        self.assertDenied("git -c core.fsmonitor=x status")
        with mock.patch.object(gitguard, "DENIED_GLOBAL_OPTS", denied), \
                mock.patch.object(gitguard, "ALLOWED_GLOBAL_OPTS", allowed):
            self.assertAllowed("git -c core.fsmonitor=x status")

    def test_d_indirection_layer_is_live(self):
        cmd = 'sh -c "git stash"'
        self.assertEqual(gitguard.classify(cmd)[1],
                         gitguard.REASON_INDIRECTION)
        self.assertNotEqual(gitguard.INDIRECTION_WORDS, frozenset())
        with mock.patch.object(gitguard, "INDIRECTION_WORDS", frozenset()):
            allowed, reason = gitguard.classify(cmd)
            self.assertIs(allowed, False)
            self.assertNotEqual(reason, gitguard.REASON_INDIRECTION)

    def test_e_newline_normalisation(self):
        cmd = "git log\ngit stash pop"
        identity = lambda c: c  # noqa: E731
        self.assertNotEqual(gitguard._normalise_newlines(cmd), cmd)
        self.assertDenied(cmd)
        with mock.patch.object(gitguard, "_normalise_newlines", identity):
            self.assertAllowed(cmd)

    def test_f_unknown_subcommand_default(self):
        self.assertNotEqual(gitguard.UNKNOWN_SUBCOMMAND_VERDICT,
                            (True, "allowed"))
        self.assertDenied("git co main")
        with mock.patch.object(gitguard, "UNKNOWN_SUBCOMMAND_VERDICT",
                               (True, "allowed")):
            self.assertAllowed("git co main")

    def test_g_trusted_basenames_are_the_first_layer(self):
        self.assertNotEqual(gitguard.TRUSTED_SCRIPT_BASENAMES, frozenset())
        self.assertDenied("cat /abs/scripts/gitsnap.py")
        with mock.patch.object(gitguard, "TRUSTED_SCRIPT_BASENAMES",
                               frozenset()):
            self.assertAllowed("cat /abs/scripts/gitsnap.py")
            allowed, reason = gitguard.classify(FIXSTAGE_BYPASS)
            self.assertIs(allowed, False)
            self.assertNotEqual(reason, gitguard.REASON_TRUSTED_SCRIPT)

    def test_h_dynamic_plugin_scripts_are_live(self):
        cmd = "cat /abs/scripts/batchsnap.py"
        scripts = frozenset({"batchsnap.py"})
        ignore = lambda plugin_scripts: gitguard.TRUSTED_SCRIPT_BASENAMES  # noqa: E731,E501
        self.assertNotEqual(gitguard._trusted_names(scripts), ignore(scripts))
        self.assertDenied(cmd, scripts)
        with mock.patch.object(gitguard, "_trusted_names", ignore):
            self.assertAllowed(cmd, scripts)

    def test_i_allowlist_default_deny(self):
        mutated = gitguard.SAFE_COMMAND_WORDS | {"make"}
        self.assertNotEqual(mutated, gitguard.SAFE_COMMAND_WORDS)
        self.assertDenied("make")
        with mock.patch.object(gitguard, "SAFE_COMMAND_WORDS", mutated):
            self.assertAllowed("make")

    def test_j_interpreter_barrier_is_two_layers(self):
        cmd = "python3 -c 'print(1)'"
        trusted = ("python3 /abs/plugins/vibe-check/scripts/fixstage.py "
                   "commit --root /r --finding-json /r/f.json")
        safe = gitguard.SAFE_COMMAND_WORDS | {"python3"}
        self.assertNotEqual(safe, gitguard.SAFE_COMMAND_WORDS)
        with mock.patch.object(gitguard, "INDIRECTION_WORDS", frozenset()):
            self.assertDenied(cmd)
        with mock.patch.object(gitguard, "SAFE_COMMAND_WORDS", safe):
            self.assertDenied(cmd)
        with mock.patch.object(gitguard, "INDIRECTION_WORDS", frozenset()), \
                mock.patch.object(gitguard, "SAFE_COMMAND_WORDS", safe):
            self.assertAllowed(cmd)
            self.assertEqual(gitguard.classify(trusted),
                             (False, gitguard.REASON_TRUSTED_SCRIPT))

    def test_k_file_redirect_rule(self):
        never = lambda tokens: False  # noqa: E731
        self.assertTrue(gitguard._has_file_redirect(["echo", "x", ">", "f"]))
        self.assertDenied("echo x > f.txt")
        with mock.patch.object(gitguard, "_has_file_redirect", never):
            self.assertAllowed("echo x > f.txt")

    def test_l_substitution_rule(self):
        never = lambda command: False  # noqa: E731
        self.assertTrue(gitguard._has_substitution("ls $(echo x)"))
        self.assertDenied("ls $(echo x)")
        with mock.patch.object(gitguard, "_has_substitution", never):
            self.assertAllowed("ls $(echo x)")

    def test_m_uniq_readded_trips_two_locks(self):
        cmd = "uniq /dev/null src/app.py"
        mutated = gitguard.SAFE_COMMAND_WORDS | {"uniq"}
        self.assertNotEqual(mutated, gitguard.SAFE_COMMAND_WORDS)
        self.assertTrue(_audit_lock_holds())
        self.assertIn((cmd, "REASON_NOT_ALLOWLISTED"), NON_GIT_DENY)
        with mock.patch.object(gitguard, "SAFE_COMMAND_WORDS", mutated):
            # lock 1: the NON_GIT_DENY row flips
            self.assertAllowed(cmd)
            # lock 2: the exact-set audit fails on its own
            self.assertFalse(_audit_lock_holds())
            with self.assertRaises(AssertionError):
                TestAllowlistAudit(
                    "test_safe_words_are_exactly_the_audited_set"
                ).test_safe_words_are_exactly_the_audited_set()

    def test_n_reader_flags(self):
        self.assertNotEqual(gitguard.DENIED_READER_FLAGS, {})
        cmds = ("rg --hostname-bin ./x foo", "rg -nz foo", "find . -fls out")
        for cmd in cmds:
            self.assertDenied(cmd)
        with mock.patch.object(gitguard, "DENIED_READER_FLAGS", {}):
            for cmd in cmds:
                with self.subTest(cmd=cmd):
                    self.assertAllowed(cmd)

    def test_p_remote_show_without_n(self):
        cmd = "git remote show origin"
        self.assertIsNot(gitguard.CONDITIONAL_SUBCOMMANDS["remote"],
                         _old_lenient_remote)
        self.assertDenied(cmd)
        with mock.patch.dict(gitguard.CONDITIONAL_SUBCOMMANDS,
                             {"remote": _old_lenient_remote}):
            self.assertAllowed(cmd)

    def test_q_other_dir_resolver_always_root(self):
        always = lambda o, r: ("root", None)  # noqa: E731
        with_cd = gitguard.SAFE_COMMAND_WORDS | {"cd"}
        dash_c = "git -C /elsewhere show HEAD"
        via_cd = "cd /r/vendor/x.git/link/.. && git show HEAD"
        self.assertEqual(gitguard.classify(dash_c, repo_root="/r"),
                         (False, gitguard.REASON_GIT_OTHER_DIR))
        with mock.patch.object(gitguard, "SAFE_COMMAND_WORDS", with_cd):
            # with `cd` allowlisted the dir rule alone holds the line
            self.assertEqual(gitguard.classify(via_cd, repo_root="/r"),
                             (False, gitguard.REASON_GIT_OTHER_DIR))
        with mock.patch.object(gitguard, "_resolve_dir_target", always):
            self.assertEqual(gitguard.classify(dash_c, repo_root="/r"),
                             (True, "allowed"))
            with mock.patch.object(gitguard, "SAFE_COMMAND_WORDS", with_cd):
                self.assertEqual(gitguard.classify(via_cd, repo_root="/r"),
                                 (True, "allowed"))

    def test_r_realpath_disagreement(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.realpath(tmp)
            bare = os.path.join(root, "vendor", "x.git")
            os.makedirs(bare)
            # link -> <root>/vendor: physically link/.. is <root>, while
            # bash's logical `cd link/..` lands back in vendor/x.git
            os.symlink(os.path.join(root, "vendor"),
                       os.path.join(bare, "link"))
            target = bare + "/link/.."
            self.assertEqual(os.path.realpath(target), root)
            with_cd = gitguard.SAFE_COMMAND_WORDS | {"cd"}
            via_cd = "cd %s && git show HEAD" % target
            dash_c = "git -C %s show HEAD" % target
            for cmd in (via_cd, dash_c):
                with mock.patch.object(gitguard, "SAFE_COMMAND_WORDS",
                                       with_cd):
                    self.assertEqual(gitguard.classify(cmd, repo_root=root),
                                     (False, gitguard.REASON_GIT_OTHER_DIR))
            with mock.patch.object(gitguard, "_resolve_dir_target",
                                   _realpath_dir_target):
                self.assertEqual(gitguard.classify(dash_c, repo_root=root),
                                 (True, "allowed"))
                with mock.patch.object(gitguard, "SAFE_COMMAND_WORDS",
                                       with_cd):
                    self.assertEqual(
                        gitguard.classify(via_cd, repo_root=root),
                        (True, "allowed"))

    def test_o_file_readded(self):
        readers = gitguard.PURE_READERS | {"file"}
        words = gitguard.SAFE_COMMAND_WORDS | {"file"}
        self.assertNotEqual(words, gitguard.SAFE_COMMAND_WORDS)
        self.assertDenied("file -C -m x")
        with mock.patch.object(gitguard, "PURE_READERS", readers), \
                mock.patch.object(gitguard, "SAFE_COMMAND_WORDS", words):
            self.assertAllowed("file -C -m x")


# --------------------------------------------------------------------------- #
# live bare-repo vectors — prove each vector runs a program, then prove the
# classifier refuses it
# --------------------------------------------------------------------------- #
LOGICAL_CD_CMD = "cd vendor/x.git/link/.. && git show HEAD"
VECTOR_MARKERS = {"uploadpack": "marker-uploadpack",
                  "diffext": "marker-diffext",
                  "textconv": "marker-textconv"}
VECTOR_TIMEOUT = 30


class TestBareRepoVectors(unittest.TestCase):
    """A reviewed repo R tracks an embedded bare clone vendor/x.git whose
    config names a marker program for remote.origin.uploadpack, diff.external
    and a textconv driver. vendor/x.git/link -> R/vendor, so physically
    link/.. is R while bash's logical `cd link/..` lands in vendor/x.git.
    Each test first proves its vector live (the marker file appears), then
    proves the classifier refuses it."""

    @classmethod
    def setUpClass(cls):
        import subprocess
        import tempfile
        cls._tmp = tempfile.TemporaryDirectory()
        base = os.path.realpath(cls._tmp.name)
        cls.markers = os.path.join(base, "markers")
        os.makedirs(cls.markers)
        scripts = {}
        for vector, body in (
                ("uploadpack", "exit 1\n"),
                ("diffext", "exit 0\n"),
                ("textconv", 'cat "$1"\n')):
            path = gitfixture.write(
                base, "bin/%s.sh" % vector,
                '#!/bin/sh\ntouch "$MARKER_DIR/%s"\n%s'
                % (VECTOR_MARKERS[vector], body))
            os.chmod(path, 0o755)
            scripts[vector] = path
        src = gitfixture.make_repo(os.path.join(base, "src"))
        gitfixture.write(src, "a.txt", "one\n")
        gitfixture.git(src, "add", "a.txt")
        gitfixture.git(src, "commit", "-q", "-m", "one")
        gitfixture.write(src, "a.txt", "two\n")
        gitfixture.git(src, "commit", "-q", "-am", "two")
        cls.root = gitfixture.make_repo(os.path.join(base, "r"))
        bare = os.path.join(cls.root, "vendor", "x.git")
        gitfixture.git(cls.root, "clone", "-q", "--bare", src, bare)
        gitfixture.git(bare, "config", "remote.origin.uploadpack",
                       scripts["uploadpack"])
        gitfixture.git(bare, "config", "diff.external", scripts["diffext"])
        gitfixture.git(bare, "config", "diff.m.textconv", scripts["textconv"])
        gitfixture.write(bare, "info/attributes", "*.txt diff=m\n")
        gitfixture.git(cls.root, "add", "vendor")
        gitfixture.git(cls.root, "commit", "-q", "-m", "vendor a bare repo")
        os.symlink(os.path.join(cls.root, "vendor"),
                   os.path.join(bare, "link"))
        cls.bare = bare
        cls.git_version = subprocess.run(
            ["git", "--version"], stdout=subprocess.PIPE, text=True,
            timeout=VECTOR_TIMEOUT).stdout.strip()

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _env(self):
        env = gitfixture.helper_env()
        env["MARKER_DIR"] = self.markers
        env["PWD"] = self.root
        env["GIT_PAGER"] = "cat"
        env["PAGER"] = "cat"
        return env

    def _marker(self, vector):
        return os.path.join(self.markers, VECTOR_MARKERS[vector])

    def _fires(self, argv, vector):
        """Run argv in R; -> True when it created the vector's marker."""
        import subprocess
        path = self._marker(vector)
        if os.path.exists(path):
            os.remove(path)
        subprocess.run(argv, cwd=self.root, env=self._env(),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=VECTOR_TIMEOUT)
        return os.path.exists(path)

    def _live_or_skip(self, argv, vector):
        if not self._fires(argv, vector):
            self.skipTest("vector not live on %s: %s" % (
                self.git_version, vector))

    def assertOtherDir(self, cmd):
        self.assertEqual(gitguard.classify(cmd, repo_root=self.root),
                         (False, gitguard.REASON_GIT_OTHER_DIR), cmd)

    def test_uploadpack_vector(self):
        self._live_or_skip(
            ["git", "-C", "vendor/x.git", "remote", "show", "origin"],
            "uploadpack")
        self.assertFalse(self._fires(
            ["git", "-C", "vendor/x.git", "remote", "show", "-n", "origin"],
            "uploadpack"), "remote show -n must not contact the remote")
        self.assertOtherDir("git -C vendor/x.git remote show origin")
        self.assertEqual(
            gitguard.classify("git remote show origin", repo_root=self.root),
            (False, gitguard.REASON_GIT_ARGS))

    def test_diff_external_vector(self):
        self._live_or_skip(
            ["git", "-C", "vendor/x.git", "diff", "HEAD~1", "HEAD"],
            "diffext")
        self.assertOtherDir("git -C vendor/x.git diff HEAD~1 HEAD")

    def test_textconv_vector(self):
        self._live_or_skip(
            ["git", "-C", "vendor/x.git", "show", "HEAD"], "textconv")
        self.assertOtherDir("git -C vendor/x.git show HEAD")
        self.assertOtherDir("cd vendor/x.git && git log -p -1")

    def test_logical_cd_symlink_vector(self):
        # The one shell call in this class: a fixed literal, never input.
        self._live_or_skip(["bash", "-c", LOGICAL_CD_CMD], "textconv")
        # A realpath check would have approved the path that just ran the
        # marker: physically link/.. is the repo root itself.
        self.assertEqual(
            os.path.realpath(os.path.join(self.root, "vendor/x.git/link/..")),
            self.root)
        self.assertOtherDir(LOGICAL_CD_CMD)
        self.assertOtherDir("cd %s/vendor/x.git/link/.. && git show HEAD"
                            % self.root)
        self.assertOtherDir("cd -P %s/vendor/x.git/link/.. && git show HEAD"
                            % self.root)
        self.assertOtherDir("git -C %s/vendor/x.git/link/.. show HEAD"
                            % self.root)
        self.assertOtherDir("cd %s/vendor/x.git/link && git show HEAD"
                            % self.root)

    def test_controls_not_over_blocked(self):
        self.assertEqual(gitguard.classify("git -C . log -1",
                                           repo_root=self.root),
                         (True, "allowed"))
        self.assertEqual(gitguard.classify("git -C %s status" % self.root,
                                           repo_root=self.root),
                         (True, "allowed"))
        self.assertEqual(gitguard.classify("cd %s && git status" % self.root,
                                           repo_root=self.root),
                         (True, "allowed"))

    def test_resolver_inputs_for_git_less_cd(self):
        r = gitguard._resolve_dir_target
        self.assertEqual(r(self.root + "/vendor", self.root),
                         ("subdir", None))
        refused = (None, gitguard.REASON_GIT_OTHER_DIR)
        self.assertEqual(r(self.bare, self.root), refused)
        self.assertEqual(r(self.bare + "/link", self.root), refused)
        self.assertEqual(r(self.bare + "/refs", self.root), refused)

    def test_bare_dir_refused_by_each_marker_alone(self):
        # HEAD+objects+refs and the .git suffix each refuse on their own.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.realpath(tmp)
            plain = os.path.join(root, "plain")
            os.makedirs(os.path.join(plain, "objects"))
            os.makedirs(os.path.join(plain, "refs"))
            open(os.path.join(plain, "HEAD"), "w").close()
            os.makedirs(os.path.join(root, "empty.git"))
            refused = (None, gitguard.REASON_GIT_OTHER_DIR)
            self.assertEqual(gitguard._resolve_dir_target(plain, root),
                             refused)
            self.assertEqual(
                gitguard._resolve_dir_target(root + "/empty.git", root),
                refused)


# --------------------------------------------------------------------------- #
# hook entrypoint (PreToolUse) — scoping, trusted scripts, recording, mutants
# --------------------------------------------------------------------------- #
HOOKS_JSON = os.path.join(os.path.dirname(SCRIPTS_DIR), "hooks", "hooks.json")

GUARDED_TOOLS = ("Bash", "Agent", "Task", "Write", "Edit", "MultiEdit",
                 "NotebookEdit", "EnterWorktree", "ExitWorktree")
DENIED_NON_BASH_TOOLS = GUARDED_TOOLS[1:]

HOOK_CASES = (  # (agent_type, command, expected rc)
    (None, "git stash pop", 0),
    ("vibe-check:fix", "git commit -F m", 0),
    ("other-plugin:x", "git stash pop", 0),
    ("general-purpose", "git stash pop", 0),
    ("vibe-check:compliance", "git stash pop", 2),
    ("vibe-check:compliance", "git log --oneline -5", 0),
    ("vibe-check:bugs", "git -C . diff HEAD~1 | head", 0),
    ("vibe-check:bugs", "git -C sub diff HEAD~1 | head", 2),
    ("vibe-check:bugs", "git remote show origin", 2),
    ("vibe-check:bugs", "git log && git checkout main", 2),
    ("vibe-check:triage", "git add .", 2),
    ("vibe-check:bugs", "grep -rn foo src", 0),
)

CARRY_STATE_CMD = "cat " + os.path.join(SCRIPTS_DIR, "carry_state.py")


def _git_env():
    env = dict(os.environ)
    env.update({"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@example.com"})
    return env


def _make_repo(test):
    import subprocess
    import tempfile
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    repo = os.path.realpath(tmp.name)
    env = _git_env()
    subprocess.run(["git", "init", "-q", repo], check=True, env=env)
    with open(os.path.join(repo, "a.txt"), "w", encoding="utf-8") as fh:
        fh.write("one\n")
    with open(os.path.join(repo, "f.json"), "w", encoding="utf-8") as fh:
        fh.write("{}\n")
    subprocess.run(["git", "-C", repo, "add", "a.txt"], check=True, env=env)
    subprocess.run(["git", "-C", repo, "commit", "-q", "-m", "init"],
                   check=True, env=env)
    return repo


def _rev_count(repo):
    import subprocess
    out = subprocess.run(["git", "-C", repo, "rev-list", "--count", "HEAD"],
                         check=True, capture_output=True, text=True,
                         env=_git_env())
    return int(out.stdout.strip())


def _payload(agent, tool="Bash", command=None, cwd=None, tool_input=None):
    data = {"session_id": "s", "hook_event_name": "PreToolUse",
            "tool_name": tool, "cwd": cwd}
    if tool_input is not None:
        data["tool_input"] = tool_input
    elif tool == "Bash":
        data["tool_input"] = {"command": command}
    else:
        data["tool_input"] = {"file_path": "x.txt"}
    if agent is not None:
        data["agent_type"] = agent
        data["agent_id"] = "a1"
    return data


def _run_hook(payload_text, cwd):
    import subprocess
    if not isinstance(payload_text, str):
        payload_text = json.dumps(payload_text)
    proc = subprocess.run([sys.executable, GITGUARD_PY, "hook"],
                          input=payload_text, capture_output=True, text=True,
                          cwd=cwd, timeout=30)
    return proc.returncode, proc.stderr


def _hook_in_process(payload):
    """Run hook_main in-process with stderr captured; -> (rc, stderr)."""
    import io
    err = io.StringIO()
    with mock.patch.object(sys, "stderr", err):
        rc = gitguard.hook_main(json.dumps(payload))
    return rc, err.getvalue()


def _blocks_path(repo):
    return os.path.join(repo, ".turingmind", "git-guard", "blocks.jsonl")


def _read_blocks(repo):
    with open(_blocks_path(repo), "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh.read().splitlines()]


def _hooks_json_problems(text):
    """Static contract check for hooks/hooks.json -> list of problems."""
    problems = []
    try:
        data = json.loads(text)
    except ValueError:
        return ["not valid JSON"]
    try:
        entry = data["hooks"]["PreToolUse"][0]
        hook = entry["hooks"][0]
    except (KeyError, IndexError, TypeError):
        return ["missing hooks.PreToolUse[0].hooks[0]"]
    matcher = entry.get("matcher")
    if not isinstance(matcher, str):
        return ["matcher missing"]
    for tool in GUARDED_TOOLS:
        if not re.fullmatch("(?:%s)" % matcher, tool):
            problems.append("matcher misses " + tool)
    if hook.get("type") != "command":
        problems.append("type is not command")
    if hook.get("command") != "python3":
        problems.append("command is not python3")
    if hook.get("args") != ["${CLAUDE_PLUGIN_ROOT}/scripts/gitguard.py",
                            "hook"]:
        problems.append("args are not the exec-form gitguard hook")
    timeout = hook.get("timeout")
    if not (isinstance(timeout, int) and not isinstance(timeout, bool)
            and 0 < timeout <= 10):
        problems.append("timeout not a positive int <= 10")
    return problems


class TestHookScoping(unittest.TestCase):
    def setUp(self):
        self.repo = _make_repo(self)

    def test_cases(self):
        for agent, cmd, expected in HOOK_CASES:
            with self.subTest(agent=agent, cmd=cmd):
                rc, _ = _run_hook(_payload(agent, command=cmd, cwd=self.repo),
                                  self.repo)
                self.assertEqual(rc, expected)

    def test_review_agent_denied_tools(self):
        for tool in DENIED_NON_BASH_TOOLS:
            with self.subTest(tool=tool):
                rc, _ = _run_hook(_payload("vibe-check:security", tool=tool,
                                           cwd=self.repo), self.repo)
                self.assertEqual(rc, 2)

    def test_review_agent_read_allowed(self):
        rc, _ = _run_hook(_payload("vibe-check:security", tool="Read",
                                   cwd=self.repo), self.repo)
        self.assertEqual(rc, 0)

    def test_fix_agent_write_allowed(self):
        rc, _ = _run_hook(_payload("vibe-check:fix", tool="Write",
                                   cwd=self.repo), self.repo)
        self.assertEqual(rc, 0)

    def test_main_session_agent_allowed(self):
        rc, _ = _run_hook(_payload(None, tool="Agent", cwd=self.repo),
                          self.repo)
        self.assertEqual(rc, 0)

    def test_main_session_vibe_agent_without_agent_id_allowed(self):
        payload = _payload("vibe-check:bugs", command="git stash pop",
                           cwd=self.repo)
        del payload["agent_id"]
        rc, _ = _run_hook(payload, self.repo)
        self.assertEqual(rc, 0)
        self.assertFalse(os.path.exists(_blocks_path(self.repo)))

    def test_main_session_vibe_agent_null_agent_id_allowed(self):
        payload = _payload("vibe-check:bugs", command="git stash pop",
                           cwd=self.repo)
        payload["agent_id"] = None
        rc, _ = _run_hook(payload, self.repo)
        self.assertEqual(rc, 0)
        self.assertFalse(os.path.exists(_blocks_path(self.repo)))

    def test_main_session_vibe_agent_denied_tools_allowed(self):
        for tool in DENIED_NON_BASH_TOOLS:
            with self.subTest(tool=tool):
                payload = _payload("vibe-check:security", tool=tool,
                                   cwd=self.repo)
                payload["agent_id"] = None
                rc, _ = _run_hook(payload, self.repo)
                self.assertEqual(rc, 0)

    def test_non_null_agent_id_stays_guarded(self):
        for agent_id in ("", 0, False, 123, "a9bf"):
            with self.subTest(agent_id=agent_id):
                payload = _payload("vibe-check:compliance",
                                   command="git stash pop", cwd=self.repo)
                payload["agent_id"] = agent_id
                rc, err = _run_hook(payload, self.repo)
                self.assertEqual(rc, 2)
                self.assertIn("vibe-check: blocked", err)

    def test_subagent_of_other_plugin_never_blocks(self):
        for agent in ("other-plugin:x", "general-purpose"):
            with self.subTest(agent=agent):
                payload = _payload(agent, command="git stash pop",
                                   cwd=self.repo)
                self.assertEqual(payload["agent_id"], "a1")
                rc, _ = _run_hook(payload, self.repo)
                self.assertEqual(rc, 0)

    def test_fix_subagent_still_exempt(self):
        payload = _payload("vibe-check:fix", tool="Write", cwd=self.repo)
        self.assertEqual(payload["agent_id"], "a1")
        rc, _ = _run_hook(payload, self.repo)
        self.assertEqual(rc, 0)

    def test_malformed_stdin_never_blocks(self):
        for text in ("not json", "", "[]"):
            with self.subTest(text=text):
                rc, _ = _run_hook(text, self.repo)
                self.assertEqual(rc, 0)

    def test_non_string_agent_type_never_blocks(self):
        payload = _payload(None, command="git stash pop", cwd=self.repo)
        payload["agent_type"] = 123
        payload["agent_id"] = "a1"
        rc, _ = _run_hook(payload, self.repo)
        self.assertEqual(rc, 0)

    def test_fail_closed_on_internal_error(self):
        def boom(*a, **k):
            raise RuntimeError("SENTINEL_boom")
        with mock.patch.object(gitguard, "classify", boom):
            rc, err = _hook_in_process(
                _payload("vibe-check:bugs", command="git log", cwd=self.repo))
            self.assertEqual(rc, 2)
            self.assertIn("guard error (fail closed)", err)
            self.assertNotIn("SENTINEL_boom", err)
            rc, _ = _hook_in_process(
                _payload(None, command="git log", cwd=self.repo))
            self.assertEqual(rc, 0)

    def test_deny_stderr_is_fixed_and_never_echoes_command(self):
        cmd = "git stash pop " + SENTINEL
        rc, err = _run_hook(_payload("vibe-check:bugs", command=cmd,
                                     cwd=self.repo), self.repo)
        self.assertEqual(rc, 2)
        self.assertNotIn(SENTINEL, err)
        self.assertIn("vibe-check: blocked", err)
        for verb in ("diff", "show", "log", "blame", "status", "rev-parse",
                     "ls-files"):
            self.assertIn(verb, err)

    def test_latency_smoke(self):
        import time
        payload = _payload(None, command="git status", cwd=self.repo)
        for _ in range(5):
            start = time.monotonic()
            rc, _ = _run_hook(payload, self.repo)
            self.assertEqual(rc, 0)
            self.assertLess(time.monotonic() - start, 2.0)


class TestHookTrustedScripts(unittest.TestCase):
    def setUp(self):
        self.repo = _make_repo(self)

    def _rc(self, agent, cmd):
        rc, err = _run_hook(_payload(agent, command=cmd, cwd=self.repo),
                            self.repo)
        return rc, err

    def test_checker_shape_denied_with_trusted_reason(self):
        rc, err = self._rc("vibe-check:bugs", FIXSTAGE_BYPASS)
        self.assertEqual(rc, 2)
        self.assertIn(gitguard.REASON_TRUSTED_SCRIPT, err)

    def test_absolute_fixstage_commit_denied_and_head_unmoved(self):
        before = _rev_count(self.repo)
        cmd = ("python3 %s/fixstage.py commit --root %s --finding-json "
               "%s/f.json" % (SCRIPTS_DIR, self.repo, self.repo))
        rc, _ = self._rc("vibe-check:bugs", cmd)
        self.assertEqual(rc, 2)
        self.assertEqual(_rev_count(self.repo), before)

    def test_gitsnap_direct_denied(self):
        rc, _ = self._rc("vibe-check:compliance",
                         "%s/gitsnap.py check --root %s"
                         % (SCRIPTS_DIR, self.repo))
        self.assertEqual(rc, 2)

    def test_dynamic_listing_denies_unlisted_static_script(self):
        self.assertNotIn("carry_state.py", gitguard.TRUSTED_SCRIPT_BASENAMES)
        self.assertTrue(os.path.isfile(os.path.join(SCRIPTS_DIR,
                                                    "carry_state.py")))
        self.assertEqual(gitguard.classify(CARRY_STATE_CMD), (True, "allowed"))
        rc, err = self._rc("vibe-check:bugs", CARRY_STATE_CMD)
        self.assertEqual(rc, 2)
        self.assertIn(gitguard.REASON_TRUSTED_SCRIPT, err)

    def test_colliding_basenames_in_the_repo_stay_readable(self):
        # A reviewed repo's own config.py / score.py share a plugin script's
        # basename; reading them is harmless and must not be refused.
        names = gitguard._plugin_script_names()
        self.assertTrue({"config.py", "score.py"} <= names)
        for cmd in ("cat src/config.py", "git show HEAD:src/config.py",
                    "git diff -- lib/score.py", "grep -n x config.py"):
            with self.subTest(cmd=cmd):
                self.assertEqual(gitguard.classify(cmd, names),
                                 (True, "allowed"))
                self.assertEqual(self._rc("vibe-check:bugs", cmd)[0], 0)
        self.assertEqual(
            gitguard.classify("cat /abs/plugin/scripts/config.py", names),
            (False, gitguard.REASON_TRUSTED_SCRIPT))
        self.assertEqual(gitguard.classify("cat src/fixstage.py", names),
                         (False, gitguard.REASON_TRUSTED_SCRIPT))

    def test_colliding_basename_mutant_trips(self):
        names = gitguard._plugin_script_names()
        always = lambda piece: True  # noqa: E731
        self.assertEqual(gitguard.classify("cat src/config.py", names),
                         (True, "allowed"))
        with mock.patch.object(gitguard, "_in_scripts_dir", always):
            self.assertEqual(gitguard.classify("cat src/config.py", names),
                             (False, gitguard.REASON_TRUSTED_SCRIPT))

    def test_interpreter_and_unlisted_words_denied(self):
        for cmd in ("python3 -c 'print(1)'", "make"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self._rc("vibe-check:bugs", cmd)[0], 2)

    def test_fix_agent_and_owner_not_blocked(self):
        self.assertEqual(self._rc("vibe-check:fix", FIXSTAGE_BYPASS)[0], 0)
        self.assertEqual(self._rc(None, FIXSTAGE_BYPASS)[0], 0)

    def test_plugin_script_names_lists_own_dir(self):
        names = gitguard._plugin_script_names()
        self.assertIsInstance(names, frozenset)
        self.assertIn("carry_state.py", names)
        self.assertIn("gitguard.py", names)
        self.assertTrue(all(n == n.lower() for n in names))
        self.assertTrue(all(n.endswith((".py", ".sh")) for n in names))

    def test_listing_error_fails_closed(self):
        def boom():
            raise OSError("SENTINEL_listdir")
        with mock.patch.object(gitguard, "_plugin_script_names", boom):
            rc, err = _hook_in_process(
                _payload("vibe-check:bugs", command="git log", cwd=self.repo))
        self.assertEqual(rc, 2)
        self.assertIn("guard error (fail closed)", err)


class TestHookRecording(unittest.TestCase):
    def setUp(self):
        self.repo = _make_repo(self)

    def test_deny_writes_one_line(self):
        rc, _ = _run_hook(_payload("vibe-check:compliance",
                                   command="git stash pop", cwd=self.repo),
                          self.repo)
        self.assertEqual(rc, 2)
        records = _read_blocks(self.repo)
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec["agent"], "compliance")
        self.assertEqual(rec["tool"], "Bash")
        self.assertEqual(rec["command"], "git stash pop")
        self.assertEqual(rec["reason"], gitguard.classify("git stash pop")[1])

    def test_allow_writes_nothing(self):
        rc, _ = _run_hook(_payload("vibe-check:compliance",
                                   command="git log", cwd=self.repo),
                          self.repo)
        self.assertEqual(rc, 0)
        self.assertFalse(os.path.exists(_blocks_path(self.repo)))

    def test_found_from_subdirectory(self):
        sub = os.path.join(self.repo, "a", "b")
        os.makedirs(sub)
        rc, _ = _run_hook(_payload("vibe-check:bugs", tool="Agent", cwd=sub),
                          sub)
        self.assertEqual(rc, 2)
        records = _read_blocks(self.repo)
        self.assertEqual(records[0]["agent"], "bugs")
        self.assertEqual(records[0]["tool"], "Agent")

    def test_command_sanitized(self):
        cmd = "git stash `pop`\nrm x " + "y" * 300
        rc, _ = _run_hook(_payload("vibe-check:bugs", command=cmd,
                                   cwd=self.repo), self.repo)
        self.assertEqual(rc, 2)
        with open(_blocks_path(self.repo), "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        self.assertEqual(len(lines), 1)
        stored = json.loads(lines[0])["command"]
        self.assertNotIn("`", stored)
        self.assertNotIn("\n", stored)
        self.assertLessEqual(len(stored), 121)
        self.assertTrue(stored.endswith("…"))

    def test_unknown_agent_and_tool_names_normalised(self):
        payload = _payload("vibe-check:" + "X" * 3, tool="Agent",
                           cwd=self.repo)
        rc, _ = _hook_in_process(payload)
        self.assertEqual(rc, 2)
        records = _read_blocks(self.repo)
        self.assertEqual(records[0]["agent"], "unknown-agent")
        self.assertEqual(gitguard._short_tool("Bad Tool!"), "unknown-tool")

    def test_unwritable_record_location_still_denies(self):
        with open(os.path.join(self.repo, ".turingmind"), "w",
                  encoding="utf-8") as fh:
            fh.write("not a dir\n")
        rc, err = _run_hook(_payload("vibe-check:bugs",
                                     command="git stash pop", cwd=self.repo),
                            self.repo)
        self.assertEqual(rc, 2)
        self.assertIn("vibe-check: blocked", err)

    def test_cwd_outside_repo_still_denies(self):
        import tempfile
        with tempfile.TemporaryDirectory() as outside:
            rc, _ = _run_hook(_payload("vibe-check:bugs",
                                       command="git stash pop", cwd=outside),
                              outside)
        self.assertEqual(rc, 2)


class TestHooksJson(unittest.TestCase):
    def _text(self):
        with open(HOOKS_JSON, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_static_contract(self):
        self.assertEqual(_hooks_json_problems(self._text()), [])

    def test_description_scopes_the_hook(self):
        data = json.loads(self._text())
        desc = data.get("description", "")
        self.assertIn("FIX-03", desc)
        self.assertIn("999.20", desc)
        self.assertIn("main session", desc)
        self.assertIn("fix agent", desc)

    def test_static_mutant_matcher_without_agent(self):
        text = self._text()
        mutated = text.replace("Agent|", "", 1)
        self.assertNotEqual(mutated, text)
        self.assertIn("matcher misses Agent", _hooks_json_problems(mutated))


README_MD = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(SCRIPTS_DIR))), "README.md")


def boundary_sentence_holds(text):
    """The WebFetch/MCP boundary decision appears byte-for-byte in `text`."""
    return isinstance(text, str) and gitguard.BOUNDARY_SENTENCE in text


class TestBoundaryDecision(unittest.TestCase):
    """WebFetch/MCP stay outside the guard by a documented decision; the
    same sentence must stay in the docstring, hooks.json and the README."""

    def _sites(self):
        with open(HOOKS_JSON, "r", encoding="utf-8") as fh:
            desc = json.load(fh)["description"]
        with open(README_MD, "r", encoding="utf-8") as fh:
            readme = fh.read()
        return {"docstring": gitguard.__doc__, "hooks.json": desc,
                "README.md": readme}

    def test_sentence_states_the_decision(self):
        sentence = gitguard.BOUNDARY_SENTENCE
        for part in ("WebFetch and MCP are outside the git-state guard",
                     "untrusted review input"):
            self.assertIn(part, sentence)

    def test_every_site_carries_the_sentence(self):
        for name, text in self._sites().items():
            with self.subTest(site=name):
                self.assertTrue(boundary_sentence_holds(text), name)

    def test_readme_no_longer_promises_a_future_release(self):
        self.assertNotIn("tracked for a future release",
                         self._sites()["README.md"])

    def test_boundary_is_not_a_guard_extension(self):
        for tool in ("WebFetch", "WebSearch"):
            self.assertNotIn(tool, gitguard.DENY_TOOLS)

    def test_mutant_dropping_the_sentence_trips(self):
        for name, text in self._sites().items():
            with self.subTest(site=name):
                mutated = text.replace(gitguard.BOUNDARY_SENTENCE, "")
                self.assertNotEqual(mutated, text)
                self.assertFalse(boundary_sentence_holds(mutated))

    def test_mutant_rewording_the_sentence_trips(self):
        for name, text in self._sites().items():
            with self.subTest(site=name):
                mutated = text.replace("by decision (D-02)", "for now")
                self.assertNotEqual(mutated, text)
                self.assertFalse(boundary_sentence_holds(mutated))


class TestHookMutants(unittest.TestCase):
    def setUp(self):
        self.repo = _make_repo(self)

    def _rc(self, agent, cmd=None, tool="Bash"):
        return _hook_in_process(_payload(agent, tool=tool, command=cmd,
                                         cwd=self.repo))[0]

    def test_a_exemption_widened(self):
        class _AllVibe(frozenset):
            def __contains__(self, item):
                return isinstance(item, str) and item.startswith(
                    "vibe-check:")
        widened = _AllVibe({"vibe-check:fix"})
        self.assertIn("vibe-check:compliance", widened)
        self.assertNotIn("vibe-check:compliance", gitguard.EXEMPT_AGENTS)
        self.assertEqual(self._rc("vibe-check:compliance", "git stash pop"), 2)
        with mock.patch.object(gitguard, "EXEMPT_AGENTS", widened):
            self.assertEqual(
                self._rc("vibe-check:compliance", "git stash pop"), 0)

    def test_b_exemption_removed(self):
        self.assertNotEqual(gitguard.EXEMPT_AGENTS, frozenset())
        self.assertEqual(self._rc("vibe-check:fix", "git commit -F m"), 0)
        with mock.patch.object(gitguard, "EXEMPT_AGENTS", frozenset()):
            self.assertEqual(self._rc("vibe-check:fix", "git commit -F m"), 2)

    def test_c_prefix_typo(self):
        self.assertNotEqual(gitguard.GUARDED_PREFIX, "vibecheck:")
        with mock.patch.object(gitguard, "GUARDED_PREFIX", "vibecheck:"):
            self.assertEqual(
                self._rc("vibe-check:compliance", "git stash pop"), 0)

    def test_d_deny_tools_emptied(self):
        self.assertNotEqual(gitguard.DENY_TOOLS, frozenset())
        self.assertEqual(self._rc("vibe-check:security", tool="Agent"), 2)
        with mock.patch.object(gitguard, "DENY_TOOLS", frozenset()):
            self.assertEqual(self._rc("vibe-check:security", tool="Agent"), 0)

    def test_e_error_handler_allows(self):
        def boom(*a, **k):
            raise RuntimeError("x")
        allow = lambda: (True, gitguard.ALLOWED)  # noqa: E731
        self.assertNotEqual(gitguard._guard_error_verdict(), allow())
        with mock.patch.object(gitguard, "classify", boom):
            self.assertEqual(self._rc("vibe-check:bugs", "git log"), 2)
            with mock.patch.object(gitguard, "_guard_error_verdict", allow):
                self.assertEqual(self._rc("vibe-check:bugs", "git log"), 0)

    def test_f_dynamic_listing_emptied(self):
        empty = lambda: frozenset()  # noqa: E731
        self.assertNotEqual(gitguard._plugin_script_names(), empty())
        self.assertEqual(self._rc("vibe-check:bugs", CARRY_STATE_CMD), 2)
        with mock.patch.object(gitguard, "_plugin_script_names", empty):
            self.assertEqual(self._rc("vibe-check:bugs", CARRY_STATE_CMD), 0)

    def test_g_listing_not_wired_into_classify(self):
        real = gitguard.classify
        seen = []

        def unwired(command, plugin_scripts=frozenset(), repo_root=None):
            seen.append(plugin_scripts)
            return real(command, repo_root=repo_root)
        self.assertEqual(self._rc("vibe-check:bugs", CARRY_STATE_CMD), 2)
        with mock.patch.object(gitguard, "classify", unwired):
            self.assertEqual(self._rc("vibe-check:bugs", CARRY_STATE_CMD), 0)
        self.assertTrue(seen and "carry_state.py" in seen[0])

    def _rc_payload(self, agent, agent_id, cmd="git stash pop"):
        payload = _payload(agent, command=cmd, cwd=self.repo)
        payload["agent_id"] = agent_id
        return _hook_in_process(payload)[0]

    def test_h_agent_id_check_removed(self):
        self.assertTrue(callable(gitguard._is_subagent_call))
        self.assertEqual(self._rc_payload("vibe-check:bugs", None), 0)
        with mock.patch.object(gitguard, "_is_subagent_call",
                               lambda d: True):
            self.assertEqual(self._rc_payload("vibe-check:bugs", None), 2)

    def test_i_agent_id_check_narrowed_to_truthy(self):
        self.assertEqual(self._rc_payload("vibe-check:bugs", ""), 2)
        with mock.patch.object(gitguard, "_is_subagent_call",
                               lambda d: bool(d.get("agent_id"))):
            self.assertEqual(self._rc_payload("vibe-check:bugs", ""), 0)

    def test_j_prefix_conjunct_removed(self):
        self.assertEqual(self._rc_payload("other-plugin:x", "a1"), 0)
        with mock.patch.object(gitguard, "GUARDED_PREFIX", ""):
            self.assertEqual(self._rc_payload("other-plugin:x", "a1"), 2)

    def test_k_repo_root_wired_into_classify(self):
        real = gitguard.classify
        cmd = "git -C %s log -1" % self.repo

        def unwired(command, plugin_scripts=frozenset(), repo_root=None):
            return real(command, plugin_scripts)
        self.assertEqual(self._rc("vibe-check:bugs", cmd), 0)
        self.assertEqual(
            self._rc("vibe-check:bugs", "git -C %s/sub log -1" % self.repo),
            2)
        with mock.patch.object(gitguard, "classify", unwired):
            self.assertEqual(self._rc("vibe-check:bugs", cmd), 2)


# --------------------------------------------------------------------------- #
# notices / reset CLI (the orchestrator's block-notice source)
# --------------------------------------------------------------------------- #
def _run_cli(args, cwd=None):
    import subprocess
    proc = subprocess.run([sys.executable, GITGUARD_PY] + list(args),
                          capture_output=True, text=True, cwd=cwd, timeout=30)
    return proc.returncode, proc.stdout, proc.stderr


def _write_blocks(root, lines):
    path = _blocks_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for line in lines:
            fh.write((line if isinstance(line, str) else json.dumps(line))
                     + "\n")
    return path


def _rec(agent="compliance", tool="Bash", command="git stash pop",
         reason=None):
    return {"agent": agent, "tool": tool, "command": command,
            "reason": gitguard.REASON_GIT_ARGS if reason is None else reason}


def _expl(reason=None):
    return gitguard.EXPLANATIONS[
        gitguard.REASON_GIT_ARGS if reason is None else reason]


def _bline(agent="compliance", command="git stash pop", reason=None,
           suffix="repo untouched."):
    return "Blocked: %s tried `%s` — %s %s" % (agent, command, suffix,
                                               _expl(reason))


_COUNT_RE = re.compile(r" \(×([0-9]+)\)$")
_TAIL_RE = re.compile(r"^…and ([0-9]+) more blocked attempts?$")


def _records_accounted(lines):
    """Sum of the per-line counts plus the tail line's remainder."""
    total = 0
    for line in lines:
        tail = _TAIL_RE.match(line)
        if tail:
            total += int(tail.group(1))
            continue
        count = _COUNT_RE.search(line)
        total += int(count.group(1)) if count else 1
    return total


def _all_reasons():
    return {getattr(gitguard, n) for n in dir(gitguard)
            if n.startswith("REASON_")}


def _explanations_exhaustive(explanations):
    return (set(explanations) == _all_reasons()
            and all(isinstance(v, str) and v.strip()
                    for v in explanations.values()))


class TestExplanationsExhaustive(unittest.TestCase):
    def test_every_reason_has_an_explanation(self):
        reasons = _all_reasons()
        self.assertGreaterEqual(len(reasons), 20)
        self.assertEqual(set(gitguard.EXPLANATIONS), reasons,
                         reasons ^ set(gitguard.EXPLANATIONS))
        self.assertTrue(_explanations_exhaustive(gitguard.EXPLANATIONS))

    def test_explanations_are_plain_fixed_sentences(self):
        for reason, text in gitguard.EXPLANATIONS.items():
            with self.subTest(reason=reason):
                self.assertTrue(text.strip())
                self.assertNotIn("\n", text)
                self.assertTrue(text.endswith("."), text)
                self.assertNotIn("fail closed", text)
                # a backtick would unbalance the notice's `<cmd>` quoting
                self.assertNotIn("`", text)

    def test_named_explanations(self):
        e = gitguard.EXPLANATIONS
        self.assertIn("sed -n 'N,Mp' file", e[gitguard.REASON_SED_FORM])
        self.assertIn("absolute directory", e[gitguard.REASON_CD_FORM])
        self.assertIn("repo root", e[gitguard.REASON_GIT_OTHER_DIR])

    def test_mutant_missing_entry_trips(self):
        for reason in sorted(gitguard.EXPLANATIONS):
            with self.subTest(reason=reason):
                patched = dict(gitguard.EXPLANATIONS)
                del patched[reason]
                self.assertFalse(_explanations_exhaustive(patched))
        blanked = dict(gitguard.EXPLANATIONS)
        blanked[gitguard.REASON_SED_FORM] = " "
        self.assertFalse(_explanations_exhaustive(blanked))


class TestNoticeExplanations(unittest.TestCase):
    def test_every_reason_renders_its_explanation(self):
        for reason, text in gitguard.EXPLANATIONS.items():
            with self.subTest(reason=reason):
                for tool, command in (("Bash", "ls"), ("Agent", "")):
                    lines = gitguard.render_notices(
                        [_rec(tool=tool, command=command, reason=reason)],
                        repo_changed=False)
                    self.assertEqual(len(lines), 1)
                    self.assertTrue(lines[0].endswith(" " + text), lines[0])

    def test_unknown_or_malformed_reason_falls_back(self):
        fallback = gitguard.EXPLANATIONS[gitguard.REASON_INTERNAL]
        for reason in ("refused: x", None, ["a"], {"b": 1}, 7):
            with self.subTest(reason=reason):
                rec = _rec()
                rec["reason"] = reason
                lines = gitguard.render_notices([rec], repo_changed=False)
                self.assertEqual(len(lines), 1)
                self.assertTrue(lines[0].endswith(" " + fallback), lines[0])
        rec = _rec()
        del rec["reason"]
        self.assertTrue(gitguard.render_notices([rec], False)[0].endswith(
            " " + fallback))

    def test_dedupe_counts(self):
        r = {"agent": "logic", "tool": "Bash", "command": "sed -i x f",
             "reason": gitguard.REASON_SED_FORM}
        lines = gitguard.render_notices([r, r, r], False)
        self.assertEqual(len(lines), 1)
        self.assertIn("(×3)", lines[0])
        self.assertIn(gitguard.EXPLANATIONS[gitguard.REASON_SED_FORM],
                      lines[0])
        self.assertTrue(lines[0].endswith(" (×3)"))

    def test_dedupe_keeps_distinct_reasons_and_order(self):
        recs = [_rec(), _rec(command="cd a b",
                             reason=gitguard.REASON_CD_FORM),
                _rec(), _rec(agent="bugs"), _rec()]
        lines = gitguard.render_notices(recs, False)
        self.assertEqual(lines, [
            _bline() + " (×3)",
            _bline(command="cd a b", reason=gitguard.REASON_CD_FORM),
            _bline(agent="bugs")])
        self.assertEqual(_records_accounted(lines), len(recs))

    def test_sum_of_counts_with_cap_and_tail(self):
        recs = []
        for i in range(14):
            recs.extend([_rec(command="cat f%d" % i)] * (i % 3 + 1))
        lines = gitguard.render_notices(recs, False)
        self.assertEqual(len(lines), gitguard.NOTICE_CAP + 1)
        self.assertRegex(lines[-1], _TAIL_RE)
        self.assertEqual(_records_accounted(lines), len(recs))

    def test_mutant_dedupe_drops_instead_of_counting(self):
        recs = [_rec(), _rec(), _rec(agent="bugs")]
        self.assertEqual(_records_accounted(
            gitguard.render_notices(recs, False)), len(recs))

        def dropping(records, suffix):
            seen = []
            for rec in records:
                line = gitguard._render_one(rec, suffix)
                if line not in [l for l, _ in seen]:
                    seen.append((line, 1))
            return seen

        with mock.patch.object(gitguard, "_group_notices", dropping):
            self.assertNotEqual(_records_accounted(
                gitguard.render_notices(recs, False)), len(recs),
                "dedupe-drop mutant survived")


class TestDenyMessage(unittest.TestCase):
    def test_names_the_allowed_read_forms_and_ends_with_reason(self):
        msg = gitguard.DENY_MESSAGE % gitguard.REASON_SED_FORM
        for verb in ("diff", "show", "log", "blame", "status", "rev-parse",
                     "ls-files", "grep"):
            self.assertIn(verb, msg)
        for word in ("cat", "head", "tail", "ls", "wc", "rg", "stat",
                     "find"):
            self.assertRegex(msg, r"\b%s\b" % word)
        self.assertIn("sed -n 'N,Mp' file", msg)
        self.assertIn("cd <absolute dir inside the repo", msg)
        self.assertTrue(msg.endswith(gitguard.REASON_SED_FORM + ".\n"), msg)
        self.assertEqual(msg.count("\n"), 1)

    def test_hook_stderr_carries_the_forms(self):
        repo = _make_repo(self)
        rc, err = _hook_in_process(_payload(
            "vibe-check:bugs", command="sed -i 's/a/b/' a.txt", cwd=repo))
        self.assertEqual(rc, 2)
        self.assertIn("sed -n 'N,Mp' file", err)
        self.assertIn(gitguard.REASON_SED_FORM, err)


# The Phase-50 Blocked-notice noise: real read-only shapes review agents ran.
PHASE50_NOISE = (
    "cd {R}; grep -n \"finalize\" commands/review.md",
    "cd {R} && grep -rn finalize .",
    "cd {R}/sub && grep -n x f",
    "sed -n '560,760p' file",
    "git show HEAD:f | sed -n '598,606p;664,672p'",
    r'find . -maxdepth 1 -type f \( -name "PLAN.md" -o -name "*.md" \)',
    "git grep -n token -- '*.md'",
    "git show HEAD:f.py",
    'grep -rn "a;b|c" src',
)


class TestPhase50Noise(unittest.TestCase):
    def test_phase50_noise_corpus_allowed(self):
        repo = _make_repo(self)
        os.makedirs(os.path.join(repo, "sub"))
        self.assertEqual(len(PHASE50_NOISE), 9)
        for template in PHASE50_NOISE:
            roots = (repo,) if "{R}" in template else (repo, None, "/r")
            for root in roots:
                cmd = template.format(R=repo)
                with self.subTest(cmd=cmd, root=root):
                    self.assertEqual(gitguard.classify(cmd, repo_root=root),
                                     (True, "allowed"))

    def test_phase50_noise_produces_no_notice(self):
        repo = _make_repo(self)
        os.makedirs(os.path.join(repo, "sub"))
        for template in PHASE50_NOISE:
            cmd = template.format(R=repo)
            with self.subTest(cmd=cmd):
                rc, err = _hook_in_process(
                    _payload("vibe-check:bugs", command=cmd, cwd=repo))
                self.assertEqual((rc, err), (0, ""))
        self.assertFalse(os.path.exists(_blocks_path(repo)))
        rc, out, _ = _run_cli(["notices", "--root", repo])
        self.assertEqual((rc, out), (0, ""))


class TestNotices(unittest.TestCase):
    def setUp(self):
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name

    def _notices(self, *extra):
        rc, out, _ = _run_cli(["notices", "--root", self.root] + list(extra))
        self.assertEqual(rc, 0)
        return out.splitlines()

    def test_three_lines(self):
        _write_blocks(self.root, [_rec(), _rec(agent="bugs",
                                               command="git checkout main"),
                                  _rec(agent="bugs", tool="Agent",
                                       command="")])
        self.assertEqual(self._notices(), [
            _bline(),
            _bline(agent="bugs", command="git checkout main"),
            "Blocked: bugs tried to use the `Agent` tool — repo untouched. "
            + _expl(),
        ])

    def test_repo_changed_suffix(self):
        _write_blocks(self.root, [_rec(), _rec(tool="Agent", command="")])
        lines = self._notices("--repo-changed")
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertTrue(line.endswith(
                "— this attempt was refused. " + _expl()), line)
            self.assertNotIn("repo untouched", line)

    def test_cap_at_ten(self):
        _write_blocks(self.root,
                      [_rec(command="cat f%d" % i) for i in range(13)])
        lines = self._notices()
        self.assertEqual(len(lines), 11)
        self.assertEqual(lines[-1], "…and 3 more blocked attempts")
        self.assertTrue(all(l.startswith("Blocked: ") for l in lines[:10]))

    def test_identical_blocks_collapse_with_a_count(self):
        _write_blocks(self.root, [_rec() for _ in range(13)])
        self.assertEqual(self._notices(), [_bline() + " (×13)"])

    def test_consume(self):
        path = _write_blocks(self.root, [_rec()])
        self.assertEqual(len(self._notices("--consume")), 1)
        self.assertFalse(os.path.exists(path))
        self.assertEqual(self._notices("--consume"), [])

    def test_no_file_prints_nothing(self):
        self.assertEqual(self._notices(), [])

    def test_without_consume_keeps_file(self):
        path = _write_blocks(self.root, [_rec()])
        self._notices()
        self.assertTrue(os.path.exists(path))

    def test_garbled_line(self):
        _write_blocks(self.root, ["{not json " + SENTINEL, "", "[1, 2]"])
        lines = self._notices()
        self.assertEqual(lines, [
            "Blocked: unknown-agent tried an unreadable command "
            "— repo untouched. "
            + gitguard.EXPLANATIONS[gitguard.REASON_INTERNAL] + " (×2)"])
        self.assertNotIn(SENTINEL, "\n".join(lines))

    def test_render_resanitizes(self):
        _write_blocks(self.root, [_rec(agent="Evil`Agent", tool="Ba sh\n",
                                       command="git `stash`\npop\x1b[31m")])
        lines = self._notices()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].count("`"), 2)
        self.assertNotIn("\x1b", lines[0])
        self.assertTrue(lines[0].startswith("Blocked: unknown-agent tried "))

    def test_render_resanitizes_bash_command(self):
        _write_blocks(self.root, [_rec(command="git `stash`\npop")])
        lines = self._notices()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].count("`"), 2)
        self.assertEqual(lines[0], _bline())

    def test_render_notices_pure(self):
        lines = gitguard.render_notices([_rec()], repo_changed=False)
        self.assertEqual(lines, [_bline()])
        self.assertEqual(gitguard.render_notices([], repo_changed=True), [])

    def test_end_to_end_from_hook(self):
        repo = _make_repo(self)
        rc, _ = _run_hook(_payload("vibe-check:compliance",
                                   command="git stash pop", cwd=repo), repo)
        self.assertEqual(rc, 2)
        rc, out, _ = _run_cli(["notices", "--root", repo, "--consume"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.splitlines(), [_bline()])
        self.assertFalse(os.path.exists(_blocks_path(repo)))

    def test_usage_errors(self):
        for args in (["notices"], ["bogus"], [], ["notices", "--root"]):
            with self.subTest(args=args):
                self.assertEqual(_run_cli(args)[0], 2)


class TestReset(unittest.TestCase):
    def setUp(self):
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name

    def test_reset_deletes(self):
        path = _write_blocks(self.root, [_rec()])
        self.assertEqual(_run_cli(["reset", "--root", self.root])[0], 0)
        self.assertFalse(os.path.exists(path))

    def test_reset_without_file(self):
        self.assertEqual(_run_cli(["reset", "--root", self.root])[0], 0)

    def test_reset_usage(self):
        self.assertEqual(_run_cli(["reset"])[0], 2)


if __name__ == "__main__":
    unittest.main()
