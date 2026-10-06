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
    ("python3 x/fixcommit.py --finding-json f", "REASON_TRUSTED_SCRIPT",
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
    ("sed -i s/a/b/ f", "REASON_NOT_ALLOWLISTED"),
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
)

ALLOW = (
    "git log --oneline -5",
    "git diff HEAD~1",
    "git show HEAD:f.py",
    "git blame -L 1,5 f.py",
    "git status --porcelain",
    "git rev-parse --show-toplevel",
    "git ls-files -s",
    "git -C sub diff HEAD~1 | head -20",
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
)

AUDITED_READERS = frozenset(
    {"cat", "head", "tail", "ls", "wc", "grep", "rg", "stat", "find"})
AUDITED_WORDS = frozenset({"git"}) | AUDITED_READERS | frozenset(
    {"echo", "printf", "true", "false", "cut", "tr", "basename", "dirname",
     "pwd"})
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
                    "echo x > " + SENTINEL):
            with self.subTest(cmd=cmd):
                allowed, reason = gitguard.classify(cmd)
                self.assertIs(allowed, False)
                self.assertNotIn(SENTINEL, reason)
                self.assertNotIn(SENTINEL.lower(), reason)

    def test_hash_does_not_hide_a_second_command(self):
        # shlex treats `#` as a comment start even mid-word; bash does not.
        self.assertIs(gitguard.classify("echo a#b; git stash pop")[0], False)


# --------------------------------------------------------------------------- #
# module purity
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    ALLOWED = {"argparse", "json", "os", "re", "shlex", "sys"}
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

    def test_o_file_readded(self):
        readers = gitguard.PURE_READERS | {"file"}
        words = gitguard.SAFE_COMMAND_WORDS | {"file"}
        self.assertNotEqual(words, gitguard.SAFE_COMMAND_WORDS)
        self.assertDenied("file -C -m x")
        with mock.patch.object(gitguard, "PURE_READERS", readers), \
                mock.patch.object(gitguard, "SAFE_COMMAND_WORDS", words):
            self.assertAllowed("file -C -m x")


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
    ("vibe-check:bugs", "git -C sub diff HEAD~1 | head", 0),
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

        def unwired(command, plugin_scripts=frozenset()):
            seen.append(plugin_scripts)
            return real(command)
        self.assertEqual(self._rc("vibe-check:bugs", CARRY_STATE_CMD), 2)
        with mock.patch.object(gitguard, "classify", unwired):
            self.assertEqual(self._rc("vibe-check:bugs", CARRY_STATE_CMD), 0)
        self.assertTrue(seen and "carry_state.py" in seen[0])


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


def _rec(agent="compliance", tool="Bash", command="git stash pop"):
    return {"agent": agent, "tool": tool, "command": command,
            "reason": "refused: x"}


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
            "Blocked: compliance tried `git stash pop` — repo untouched.",
            "Blocked: bugs tried `git checkout main` — repo untouched.",
            "Blocked: bugs tried to use the `Agent` tool — repo untouched.",
        ])

    def test_repo_changed_suffix(self):
        _write_blocks(self.root, [_rec(), _rec(tool="Agent", command="")])
        lines = self._notices("--repo-changed")
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertTrue(line.endswith("— this attempt was refused."),
                            line)
            self.assertNotIn("repo untouched", line)

    def test_cap_at_ten(self):
        _write_blocks(self.root, [_rec() for _ in range(13)])
        lines = self._notices()
        self.assertEqual(len(lines), 11)
        self.assertEqual(lines[-1], "…and 3 more blocked attempts")
        self.assertTrue(all(l.startswith("Blocked: ") for l in lines[:10]))

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
            "— repo untouched."] * 2)
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
        self.assertEqual(
            lines[0], "Blocked: compliance tried `git stash pop` "
                      "— repo untouched.")

    def test_render_notices_pure(self):
        lines = gitguard.render_notices([_rec()], repo_changed=False)
        self.assertEqual(lines, [
            "Blocked: compliance tried `git stash pop` — repo untouched."])
        self.assertEqual(gitguard.render_notices([], repo_changed=True), [])

    def test_end_to_end_from_hook(self):
        repo = _make_repo(self)
        rc, _ = _run_hook(_payload("vibe-check:compliance",
                                   command="git stash pop", cwd=repo), repo)
        self.assertEqual(rc, 2)
        rc, out, _ = _run_cli(["notices", "--root", repo, "--consume"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.splitlines(), [
            "Blocked: compliance tried `git stash pop` — repo untouched."])
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
