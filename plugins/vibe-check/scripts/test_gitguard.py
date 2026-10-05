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


if __name__ == "__main__":
    unittest.main()
