"""Tests for fixcommit.py — the fix agent's commit-construction owner (plan 40-07).

Three defect families are locked here, each reproduced live before the fix:

  * **F4 — the guard API is per-candidate, not bulk.** `guard.contained(root, candidate)`
    takes ONE STRING. Handing it a LIST makes `candidate.strip()` fail the isinstance
    check and returns `(False, "refused: empty path (fail closed)")`, so a
    "one bulk call" implementation would have refused every ordinary multi-file fix.
    `validate_paths` therefore LOOPS. Pinned three ways: a counting wrapper that
    records the argument TYPES, a direct assertion that a list argument is refused,
    and a CLI test showing the `--path a --path b` form is the supported bulk shape.

  * **F5 — the gate must fail CLOSED by control flow.** The prose gate used to be
    `python3 ... || { : ...; }`; the shell no-op builtin SUCCEEDS, so execution fell
    straight through into `git add`/`git commit` after a rejection (reproduced:
    AFTER_REJECT_REACHED). Here: a rejection writes NO msgfile and exits non-zero, so
    an `if/then/else` caller cannot reach its git operations.

  * **FL-03 (R4) — the title must never reach a shell command line.** The finding title
    is attacker-influenced and the caller SUBSTITUTED it into bash, so the shell expanded
    it BEFORE any Python validation ran. A command substitution executed at expansion
    time. The fix: the title arrives only through a serialized JSON data channel
    (`--finding-json`), never on argv. The tests below assert both that the channel
    exists and that no argv surface accepts a title.
"""

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixcommit  # noqa: E402  (sibling module under test)
import guard  # noqa: E402  (the containment source fixcommit must delegate to)

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXCOMMIT_PY = os.path.join(SCRIPTS_DIR, "fixcommit.py")
GUARD_PY = os.path.join(SCRIPTS_DIR, "guard.py")

SENTINEL_PATH = "../../SENTINEL-PATH"
SENTINEL_TITLE = "SENTINEL-TITLE"


class _RootCase(unittest.TestCase):
    """A tmp root with two real files under src/."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        os.makedirs(os.path.join(self.root, "src"))
        for name in ("a.py", "b.py"):
            with open(os.path.join(self.root, "src", name), "w") as fh:
                fh.write("x = 1\n")

    def tearDown(self):
        self._tmp.cleanup()


# --------------------------------------------------------------------------- #
# validate_title — T-40-23 (trailer forgery) and the deliberate extra strictness
# --------------------------------------------------------------------------- #
class TestValidateTitle(unittest.TestCase):
    def test_ordinary_titles_accepted(self):
        for title in ("Avoid shell=True in subprocess",
                      "Fix auth/session.py (pass #2)",
                      "Guard: clamp value = 5"):
            with self.subTest(title=title):
                ok, reason = fixcommit.validate_title(title)
                self.assertTrue(ok, reason)

    def test_rejected_titles(self):
        cases = {
            "newline (trailer forgery)": "x\nCo-Authored-By: e@v.il",
            "carriage return": "a\rb",
            "NUL": "a\x00b",
            "DEL": "a\x7fb",
            "double quote": 'say "hi"',
            "single quote": "don't",
            "inner double quote": 'a"b',
            "inner apostrophe": "a'b",
            "inner newline": "a\nb",
            "non-ascii": "héllo",
            "empty": "",
        }
        for label, title in cases.items():
            with self.subTest(case=label):
                ok, reason = fixcommit.validate_title(title)
                self.assertFalse(ok, "%s was accepted" % label)
                self.assertTrue(reason.startswith("refused:"), reason)

    def test_rejects_never_strips(self):
        # fix.md:44 — "reject (do NOT silently strip)". A stripped title would
        # produce a plausible-looking commit that hides the injection attempt.
        hostile = "ok part\nCo-Authored-By: e@v.il"
        ok, _ = fixcommit.validate_title(hostile)
        self.assertFalse(ok)
        # and no API exists that returns a cleaned title
        self.assertFalse(hasattr(fixcommit, "sanitize_title"))
        self.assertFalse(hasattr(fixcommit, "strip_title"))

    def test_non_str_title_refused(self):
        for value in (None, 5, ["a"], {"a": 1}):
            with self.subTest(value=repr(value)):
                ok, _ = fixcommit.validate_title(value)
                self.assertFalse(ok)

    def test_reason_never_echoes_the_title(self):
        ok, reason = fixcommit.validate_title(SENTINEL_TITLE + "\x00")
        self.assertFalse(ok)
        self.assertNotIn(SENTINEL_TITLE, reason)

    def test_allowlist_excludes_quotes_and_apostrophe(self):
        # Deliberately STRICTER than codex-adversarial.md's display sanitizer.
        # 40-04's TestAllowlistRelationship pins the other direction.
        for ch in ('"', "'"):
            with self.subTest(ch=ch):
                self.assertIsNone(fixcommit.TITLE_ALLOWED.match("a" + ch + "b"))

    def test_allowlist_permits_comma(self):
        # D-16: a comma is inert in a one-line -F/--cleanup=verbatim subject.
        title = "Avoid shell=True, use argv"
        ok, reason = fixcommit.validate_title(title)
        self.assertTrue(ok, reason)
        self.assertEqual(fixcommit.build_message(3, title),
                         "fix(review-pass-3): Avoid shell=True, use argv\n")
        with self.subTest("mutant: the pre-D-16 pattern rejects the comma"):
            old = re.compile(r"^[A-Za-z0-9 ._:/()#=-]+$")
            with mock.patch.object(fixcommit, "TITLE_ALLOWED", old):
                ok, _ = fixcommit.validate_title(title)
            self.assertFalse(ok, "comma test is not live: old pattern accepted")

    def test_allowlist_permits_equals(self):
        # `flag=value` titles are legitimate and inert given printf '%s' +
        # -F msgfile + --cleanup=verbatim.
        self.assertIsNotNone(fixcommit.TITLE_ALLOWED.match("verify=False"))


# --------------------------------------------------------------------------- #
# validate_paths — T-40-21 / T-40-21c / T-40-22
# --------------------------------------------------------------------------- #
class TestValidatePaths(_RootCase):
    def test_contained_paths_accepted(self):
        ok, reason = fixcommit.validate_paths(self.root, ["src/a.py", "src/b.py"])
        self.assertTrue(ok, reason)

    def test_traversal_passes_regex_fails_containment(self):
        """THE regression this file exists for: the regex is not the guard.

        Every character of `../../.git/hooks/pre-commit` is inside PATH_RE's
        class, so the pre-filter accepts it. Only containment refuses it.
        """
        hostile = "../../.git/hooks/pre-commit"
        self.assertIsNotNone(
            fixcommit.PATH_RE.match(hostile),
            "fixture integrity: the traversal path must PASS the regex")
        ok, reason = fixcommit.validate_paths(self.root, [hostile])
        self.assertFalse(ok)
        self.assertIn("containment", reason)

    def test_other_rejected_paths(self):
        cases = {
            "absolute": "/etc/passwd",
            "space": "src/a b.py",
            "leading dash": "-x",
            "empty string": "",
        }
        for label, path in cases.items():
            with self.subTest(case=label):
                ok, reason = fixcommit.validate_paths(self.root, [path])
                self.assertFalse(ok, "%s accepted" % label)
                self.assertTrue(reason.startswith("refused:"), reason)

    def test_empty_list_refused(self):
        ok, reason = fixcommit.validate_paths(self.root, [])
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("refused:"), reason)

    def test_non_list_refused(self):
        for value in (None, "src/a.py", 5):
            with self.subTest(value=repr(value)):
                ok, _ = fixcommit.validate_paths(self.root, value)
                self.assertFalse(ok)

    def test_one_bad_path_refuses_the_whole_set(self):
        ok, _ = fixcommit.validate_paths(
            self.root, ["src/a.py", "../../.git/hooks/pre-commit"])
        self.assertFalse(ok)

    def test_reason_never_echoes_the_path(self):
        ok, reason = fixcommit.validate_paths(self.root, [SENTINEL_PATH])
        self.assertFalse(ok)
        self.assertNotIn("SENTINEL-PATH", reason)

    # --- F4: the loop, and why it must be a loop ------------------------- #

    def test_per_path_loop_calls_contained_once_per_path_with_a_str(self):
        """F4 lock: one `guard.contained(root, p)` call per path, `p` a `str`.

        A future "optimization" that passes the whole list in one call would
        hand `contained` a list, which it refuses — silently blocking every
        ordinary multi-file fix. The recorded argument TYPES are what catches it.
        """
        calls = []
        real = guard.contained

        def counting(root, candidate):
            calls.append((root, candidate))
            return real(root, candidate)

        fixcommit.guard.contained = counting
        try:
            ok, reason = fixcommit.validate_paths(
                self.root, ["src/a.py", "src/b.py"])
        finally:
            fixcommit.guard.contained = real
        self.assertTrue(ok, reason)
        self.assertEqual(len(calls), 2,
                         "expected one contained() call per path, got %d"
                         % len(calls))
        for root_arg, cand_arg in calls:
            self.assertIsInstance(cand_arg, str,
                                  "contained() must receive a str candidate, "
                                  "got %r" % type(cand_arg))
            self.assertIsInstance(root_arg, str)
        self.assertEqual([c for _, c in calls], ["src/a.py", "src/b.py"])

    def test_loop_short_circuits_on_the_first_refusal(self):
        calls = []
        real = guard.contained

        def counting(root, candidate):
            calls.append(candidate)
            return real(root, candidate)

        fixcommit.guard.contained = counting
        try:
            ok, _ = fixcommit.validate_paths(
                self.root, ["../escape", "src/b.py"])
        finally:
            fixcommit.guard.contained = real
        self.assertFalse(ok)
        self.assertEqual(calls, ["../escape"],
                         "a refusal is a refusal — stop at the first one")

    def test_contained_rejects_a_list_argument(self):
        """The bug F4 found, pinned at its source.

        This is WHY `validate_paths` loops. If guard's API ever gains real list
        support, this test fails and the change gets reviewed deliberately
        instead of being assumed.
        """
        ok, reason = guard.contained(self.root, ["src/a.py", "src/b.py"])
        self.assertFalse(ok)
        self.assertEqual(reason, "refused: empty path (fail closed)")

    def test_guard_cli_is_the_bulk_interface(self):
        """Bulk lives in guard's CLI loop (guard.py:89-94), not its Python API.

        The `--path a --path b` form is what the fix.md bash gates use.
        """
        both = subprocess.run(
            [sys.executable, GUARD_PY, "--root", self.root,
             "--path", "src/a.py", "--path", "src/b.py"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        self.assertEqual(both.returncode, 0, both.stdout + both.stderr)
        mixed = subprocess.run(
            [sys.executable, GUARD_PY, "--root", self.root,
             "--path", "src/a.py", "--path", "../../etc/passwd"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        self.assertEqual(mixed.returncode, 1, mixed.stdout + mixed.stderr)

    def test_containment_is_delegated_not_reimplemented(self):
        """Fable A7/B2: a hand-copied containment check failed OPEN.

        fixcommit must call guard, not carry its own realpath/startswith logic.
        """
        with open(FIXCOMMIT_PY, "r", encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("guard.contained(", src)
        self.assertNotIn("realpath", src)
        self.assertNotIn("startswith(root", src)


# --------------------------------------------------------------------------- #
# validate_fix_paths — the ONE every-segment reserved-dir check (fixstage +
# fixcheck call it; neither keeps a local copy)
# --------------------------------------------------------------------------- #
class TestValidateFixPaths(_RootCase):
    REFUSED_RESERVED = (
        ".git/hooks/pre-commit", "x/.git/hooks/pre-commit",
        "a/b/.GIT/config", ".turingmind/fixstage/x", "sub/.turingmind/x",
    )

    def test_plain_paths_accepted(self):
        ok, reason = fixcommit.validate_fix_paths(
            self.root, ["src/a.py", "x/.gitignore", "x.git/y"])
        self.assertTrue(ok, reason)

    def test_reserved_segment_anywhere_refused(self):
        for path in self.REFUSED_RESERVED:
            with self.subTest(path=path):
                ok, reason = fixcommit.validate_fix_paths(self.root, [path])
                self.assertFalse(ok)
                self.assertIn("reserved directory", reason)

    def test_non_normal_form_refused(self):
        for path in ("./f.txt", "a/./b", "a/../b", "a//b", "a/"):
            with self.subTest(path=path):
                ok, reason = fixcommit.validate_fix_paths(self.root, [path])
                self.assertFalse(ok)
                self.assertIn("normal form", reason)

    def test_symlink_into_reserved_dir_refused(self):
        os.makedirs(os.path.join(self.root, "x", ".git", "hooks"))
        os.symlink(os.path.join("x", ".git"),
                   os.path.join(self.root, "alias"))
        ok, reason = fixcommit.validate_fix_paths(
            self.root, ["alias/hooks/pre-commit"])
        self.assertFalse(ok)
        self.assertIn("reserved directory", reason)

    def test_base_rules_still_apply(self):
        ok, reason = fixcommit.validate_fix_paths(
            self.root, ["../../.git/hooks/pre-commit"])
        self.assertFalse(ok)
        self.assertIn("containment", reason)

    def test_mutant_top_segment_only_lets_nested_git_through(self):
        top_only = lambda p: p.split("/", 1)[0].lower() in (  # noqa: E731
            fixcommit.RESERVED_DIRS)
        with mock.patch.object(fixcommit, "_has_reserved_segment", top_only):
            ok, _ = fixcommit.validate_fix_paths(
                self.root, ["x/.git/hooks/pre-commit"])
        self.assertTrue(ok, "every-segment test is not live")

    def test_fixstage_and_fixcheck_keep_no_local_copy(self):
        import fixcheck
        import fixstage
        for mod in (fixstage, fixcheck):
            with self.subTest(mod=mod.__name__):
                self.assertFalse(hasattr(mod, "RESERVED_TOP"))
                with self.assertRaises(mod.Refused):
                    mod._validate_paths(self.root, ["x/.git/hooks/pre-commit"])
                with mock.patch.object(fixcommit, "validate_fix_paths",
                                       lambda r, p: (True, "accepted")):
                    mod._validate_paths(self.root, ["x/.git/hooks/pre-commit"])

    def test_f4_locks_live_under_validate_paths_not_here(self):
        """The F4 loop locks exercise validate_paths, so they belong to
        TestValidatePaths. A class inserted mid-body once absorbed them by
        indentation; trimming this class must never delete them."""
        f4 = ("test_per_path_loop_calls_contained_once_per_path_with_a_str",
              "test_loop_short_circuits_on_the_first_refusal",
              "test_contained_rejects_a_list_argument",
              "test_guard_cli_is_the_bulk_interface",
              "test_containment_is_delegated_not_reimplemented")
        for name in f4:
            with self.subTest(name=name):
                self.assertIn(name, vars(TestValidatePaths))
                self.assertNotIn(name, vars(TestValidateFixPaths))


# --------------------------------------------------------------------------- #
# build_message
# --------------------------------------------------------------------------- #
class TestBuildMessage(unittest.TestCase):
    def test_golden(self):
        self.assertEqual(fixcommit.build_message(2, "Fix leak"),
                         "fix(review-pass-2): Fix leak\n")

    def test_no_trailing_space_and_exactly_one_newline(self):
        msg = fixcommit.build_message(1, "Fix leak")
        self.assertTrue(msg.endswith("\n"))
        self.assertFalse(msg.endswith("\n\n"))
        self.assertNotIn(" \n", msg)

    def test_digit_string_pass_number_accepted(self):
        self.assertEqual(fixcommit.build_message("3", "Fix leak"),
                         "fix(review-pass-3): Fix leak\n")

    def test_bad_pass_number_rejected(self):
        for value in ("2; rm -rf /", "-1", "", None, 1.5, "1 2"):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    fixcommit.build_message(value, "Fix leak")

    def test_bad_title_rejected(self):
        with self.assertRaises(ValueError):
            fixcommit.build_message(2, "x\nCo-Authored-By: e@v.il")


# --------------------------------------------------------------------------- #
# CLI — fail-closed contract (F5) and the FL-03 data channel (R4)
# --------------------------------------------------------------------------- #
class TestCli(_RootCase):
    def _finding(self, **over):
        rec = {"pass_number": 2, "title": "Fix leak",
               "paths": ["src/a.py", "src/b.py"]}
        rec.update(over)
        return rec

    def _write_finding(self, rec):
        path = os.path.join(self.root, "finding.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(rec, fh)
        return path

    def _run(self, *argv):
        return subprocess.run([sys.executable, FIXCOMMIT_PY, *argv],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=30)

    def _msgfile(self):
        return os.path.join(self.root, "msg.txt")

    def test_success_writes_the_golden_message_and_exits_zero(self):
        fj = self._write_finding(self._finding())
        msg = self._msgfile()
        proc = self._run("--finding-json", fj, "--root", self.root,
                         "--msgfile", msg)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        with open(msg, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "fix(review-pass-2): Fix leak\n")

    def test_success_prints_the_validated_paths_one_per_line(self):
        fj = self._write_finding(self._finding())
        proc = self._run("--finding-json", fj, "--root", self.root,
                         "--msgfile", self._msgfile())
        self.assertEqual(proc.stdout.split("\n")[:2], ["src/a.py", "src/b.py"])
        self.assertNotIn("\x00", proc.stdout)

    def test_rejection_writes_no_msgfile_and_exits_one(self):
        """F5: the caller's `if` must have nothing to fall through into."""
        fj = self._write_finding(
            self._finding(paths=["../../.git/hooks/pre-commit"]))
        msg = self._msgfile()
        proc = self._run("--finding-json", fj, "--root", self.root,
                         "--msgfile", msg)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(os.path.exists(msg),
                         "a refused finding must leave NO message file")

    def test_bad_title_rejection_writes_no_msgfile(self):
        fj = self._write_finding(
            self._finding(title="x\nCo-Authored-By: e@v.il"))
        msg = self._msgfile()
        proc = self._run("--finding-json", fj, "--root", self.root,
                         "--msgfile", msg)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(os.path.exists(msg))

    def test_never_echo_path_or_title(self):
        fj = self._write_finding(
            self._finding(title=SENTINEL_TITLE + "\x00",
                          paths=[SENTINEL_PATH]))
        proc = self._run("--finding-json", fj, "--root", self.root,
                         "--msgfile", self._msgfile())
        self.assertEqual(proc.returncode, 1)
        for stream in (proc.stdout, proc.stderr):
            self.assertNotIn("SENTINEL-PATH", stream)
            self.assertNotIn(SENTINEL_TITLE, stream)

    def test_missing_or_malformed_finding_json_refused(self):
        msg = self._msgfile()
        missing = self._run("--finding-json",
                            os.path.join(self.root, "nope.json"),
                            "--root", self.root, "--msgfile", msg)
        self.assertEqual(missing.returncode, 1)
        bad = os.path.join(self.root, "bad.json")
        with open(bad, "w") as fh:
            fh.write("{not json")
        proc = self._run("--finding-json", bad, "--root", self.root,
                         "--msgfile", msg)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(os.path.exists(msg))

    def test_usage_error_exits_nonzero(self):
        proc = self._run("--root", self.root)  # no --finding-json
        self.assertNotEqual(proc.returncode, 0)

    def test_empty_root_refused(self):
        fj = self._write_finding(self._finding())
        proc = self._run("--finding-json", fj, "--root", "",
                         "--msgfile", self._msgfile())
        self.assertEqual(proc.returncode, 1)

    # --- FL-03 (R4): the title never touches a command line -------------- #

    def test_cli_exposes_no_title_or_pass_argv_flag(self):
        """FL-03: attacker-influenced bytes must not reach a shell command line.

        The caller substituted `--title "<finding.title>"` into bash, so the
        SHELL expanded the title before Python ever saw it — a command
        substitution ran at expansion time. Reproduced. The only channel is the
        serialized JSON file, so no argv surface may accept a title.
        """
        for flag in ("--title", "--pass", "--path"):
            with self.subTest(flag=flag):
                proc = self._run(flag, "x", "--root", self.root,
                                 "--msgfile", self._msgfile())
                self.assertNotEqual(
                    proc.returncode, 0,
                    "%s is still an accepted argv flag — the title/paths must "
                    "arrive only via --finding-json" % flag)
                self.assertIn("unrecognized arguments", proc.stderr)

    def test_command_substitution_title_has_no_side_effect(self):
        """A title containing `$(...)` produces NO file and NO commit.

        With the JSON channel the bytes never reach a shell, so the substitution
        is inert; fixcommit then REJECTS the title on the allowlist, so the
        caller's `if` records `errored` without staging or committing.
        """
        canary = os.path.join(self.root, "PWNED")
        hostile = 'Fix leak"; $(touch %s) #' % canary
        fj = self._write_finding(self._finding(title=hostile))
        msg = self._msgfile()
        proc = self._run("--finding-json", fj, "--root", self.root,
                         "--msgfile", msg)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(os.path.exists(canary),
                         "the command substitution EXECUTED — FL-03 regression")
        self.assertFalse(os.path.exists(msg))

    def test_backtick_title_rejected_without_execution(self):
        canary = os.path.join(self.root, "PWNED2")
        hostile = "Fix `touch %s` leak" % canary
        fj = self._write_finding(self._finding(title=hostile))
        proc = self._run("--finding-json", fj, "--root", self.root,
                         "--msgfile", self._msgfile())
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(os.path.exists(canary))


# --------------------------------------------------------------------------- #
# module purity
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    """{json, os, re, sys, guard} — the module validates and builds; bash runs git."""

    ALLOWED = {"json", "os", "re", "sys", "guard"}
    FORBIDDEN_NAMES = {"subprocess", "shutil", "glob", "socket", "shlex"}

    def _imported(self):
        with open(FIXCOMMIT_PY, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        return imported

    def test_import_set_subset_of_allowed(self):
        imported = self._imported()
        self.assertTrue(
            imported.issubset(self.ALLOWED),
            "fixcommit.py imports outside the allowed set: "
            + str(imported - self.ALLOWED))

    def test_no_forbidden_module_imported(self):
        for name in self._imported():
            self.assertNotIn(name, self.FORBIDDEN_NAMES)

    def test_no_git_or_shell_invocation(self):
        with open(FIXCOMMIT_PY, "r", encoding="utf-8") as fh:
            src = fh.read()
        for needle in ("subprocess", "os.system", "os.popen", "os.exec"):
            self.assertNotIn(needle, src,
                             "fixcommit.py must not run git or a shell — bash "
                             "executes, this module validates and builds")

    def test_exports_the_contracted_names(self):
        for name in ("TITLE_ALLOWED", "PATH_RE", "validate_paths",
                     "validate_title", "build_message", "run"):
            self.assertTrue(hasattr(fixcommit, name),
                            "fixcommit.%s is missing" % name)


if __name__ == "__main__":
    unittest.main()
