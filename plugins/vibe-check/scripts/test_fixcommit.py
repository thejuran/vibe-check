"""Tests for fixcommit.py — the commit-construction library fixstage imports.

Defect families locked here, each reproduced live before the fix:

  * **F4 — the guard API is per-candidate, not bulk.** `guard.contained(root, candidate)`
    takes ONE STRING. Handing it a LIST makes `candidate.strip()` fail the isinstance
    check and returns `(False, "refused: empty path (fail closed)")`, so a
    "one bulk call" implementation would have refused every ordinary multi-file fix.
    `validate_paths` therefore LOOPS. Pinned three ways: a counting wrapper that
    records the argument TYPES, a direct assertion that a list argument is refused,
    and a guard-CLI test showing the `--path a --path b` form is the supported bulk
    shape.

  * **Bug E (D-08) — a verified fix is never refused over title punctuation.** The
    subject is built by `commit_subject`, which sanitizes deterministically (quotes
    dropped, `;` -> `,`, control/separator/bidi/zero-width characters -> space). The
    trailer-forgery invariant still holds: no newline survives, and a final
    `TITLE_ALLOWED.fullmatch` belt refuses anything the sanitizer missed.

  * **The standalone CLI is retired.** `fixstage.py commit` owns the commit path.
    Running `fixcommit.py` directly exits 2 (never 0, so a stale
    `if python3 fixcommit.py ...; then git commit` fence cannot proceed), and no
    prose or script may invoke it.
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
FID = "abcdef0123456789"


def _one_line(message):
    """Exactly one line, newline-terminated: no trailer can follow it."""
    return (message.endswith("\n") and message.count("\n") == 1
            and "\r" not in message)


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

    def test_validate_title_stays_a_predicate(self):
        # validate_title answers "is this already a legal subject?"; it never
        # cleans. Cleaning is commit_subject's job (D-08).
        hostile = "ok part\nCo-Authored-By: e@v.il"
        ok, _ = fixcommit.validate_title(hostile)
        self.assertFalse(ok)
        self.assertTrue(hasattr(fixcommit, "commit_subject"))

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

    def test_newline_title_cannot_forge_a_trailer(self):
        msg = fixcommit.build_message(2, "t\nCo-Authored-By: evil <e@x>", FID)
        self.assertTrue(_one_line(msg), repr(msg))
        self.assertIn("Co-Authored-By: evil", msg.split("\n")[0])

    def test_punctuated_title_builds_a_sanitized_subject(self):
        self.assertEqual(fixcommit.build_message(2, "Don't; x", FID),
                         "fix(review-pass-2): Dont, x\n")

    def test_non_string_title_refused(self):
        for value in (None, 5, ["a"]):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    fixcommit.build_message(2, value, FID)

    def test_empty_after_sanitizing_without_an_id_refused(self):
        with self.assertRaises(ValueError):
            fixcommit.build_message(2, "'" * 3, None)
        self.assertEqual(fixcommit.build_message(2, "'" * 3, FID),
                         "fix(review-pass-2): finding abcdef01\n")


# --------------------------------------------------------------------------- #
# commit_subject — D-08 deterministic sanitization, belt, and fallback
# --------------------------------------------------------------------------- #
class TestCommitSubject(unittest.TestCase):
    TABLE = (
        ("Don't trust the user's input; sanitize",
         "Dont trust the users input, sanitize"),
        ("a\tb\nc d\u200be", "a b c d e"),
        ("ok title", "ok title"),
        ('say "hi"', "say hi"),
        ("a\u2028b\u0085c\u202ed\ufeffe\u2066f", "a b c d e f"),
        ("x\r\ny\x00z\x7fw", "x y z w"),
        ("  spaced   out  ", "spaced out"),
        ("h\u00e9llo", "h llo"),
        ("$(touch pwned)", "(touch pwned)"),
        ("Avoid shell=True, use argv #2 (a/b.py: x_y-z)",
         "Avoid shell=True, use argv #2 (a/b.py: x_y-z)"),
    )

    def test_table(self):
        for title, want in self.TABLE:
            with self.subTest(title=title):
                got = fixcommit.commit_subject(title, FID)
                self.assertEqual(got, want)
                self.assertIsNotNone(fixcommit.TITLE_ALLOWED.fullmatch(got))

    def test_empty_after_sanitizing_falls_back_to_the_id(self):
        for title in ("'" * 3, "  \n\t ", ""):
            with self.subTest(title=title):
                self.assertEqual(
                    fixcommit.commit_subject(title, "deadbeefcafe"),
                    "finding deadbeef")

    def test_fallback_needs_a_hex_id(self):
        for fid in (None, "", "NOTHEX!!", "abc", 5):
            with self.subTest(fid=repr(fid)):
                with self.assertRaises(ValueError):
                    fixcommit.commit_subject("'" * 3, fid)

    def test_every_codepoint_maps_into_the_allowlist(self):
        """No input character can survive outside TITLE_ALLOWED's class."""
        bad = []
        for cp in range(0, 0x3100):
            got = fixcommit.commit_subject("a" + chr(cp) + "b", FID)
            if fixcommit.TITLE_ALLOWED.fullmatch(got) is None:
                bad.append(hex(cp))
        self.assertEqual(bad, [])

    def test_mutant_no_sanitizing_trips_the_belt(self):
        """Belt lock: with commit_subject an identity, an apostrophe title must
        NOT reach the message; the TITLE_ALLOWED.fullmatch belt refuses it."""
        with mock.patch.object(fixcommit, "commit_subject", lambda t, i: t):
            with self.assertRaises(ValueError):
                fixcommit.build_message(1, "Don't", FID)
            with self.assertRaises(ValueError):
                fixcommit.build_message(1, "t\nCo-Authored-By: e <e@x>", FID)

    def test_mutant_no_belt_and_no_sanitizing_forges_a_trailer(self):
        """The one-line predicate the forgery test relies on can trip."""
        permissive = re.compile(r"^.+$", re.DOTALL)
        with mock.patch.object(fixcommit, "commit_subject", lambda t, i: t), \
                mock.patch.object(fixcommit, "TITLE_ALLOWED", permissive):
            msg = fixcommit.build_message(1, "t\nCo-Authored-By: e <e@x>", FID)
        self.assertFalse(_one_line(msg), "forgery predicate is not live")

    def test_mutant_newline_kept_is_caught(self):
        """A sanitizer that forgot newlines is refused by the belt, not shipped."""
        def leaky(title, fid):
            return title.replace("'", "")
        with mock.patch.object(fixcommit, "commit_subject", leaky):
            with self.assertRaises(ValueError):
                fixcommit.build_message(1, "a\nCo-Authored-By: e", FID)


# --------------------------------------------------------------------------- #
# The standalone CLI is retired; fixstage.py commit owns the commit path
# --------------------------------------------------------------------------- #
class TestCliRetired(_RootCase):
    def test_running_the_module_exits_two_with_the_retirement_message(self):
        fj = os.path.join(self.root, "finding.json")
        with open(fj, "w", encoding="utf-8") as fh:
            json.dump({"pass_number": 2, "title": "Fix leak",
                       "paths": ["src/a.py"]}, fh)
        msg = os.path.join(self.root, "msg.txt")
        proc = subprocess.run(
            [sys.executable, FIXCOMMIT_PY, "--finding-json", fj,
             "--root", self.root, "--msgfile", msg],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            timeout=30)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("fixcommit CLI is retired", proc.stderr)
        self.assertIn("fixstage.py commit", proc.stderr)
        self.assertFalse(os.path.exists(msg))

    def test_no_cli_surface_remains(self):
        for name in ("parse_argv", "run", "KNOWN_FLAGS", "USAGE"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(fixcommit, name))
        self.assertTrue(hasattr(fixcommit, "commit_subject"))


# --------------------------------------------------------------------------- #
# No prose or script invokes the retired CLI
# --------------------------------------------------------------------------- #
PLUGIN_DIR = os.path.normpath(os.path.join(SCRIPTS_DIR, ".."))
LOCK_DIRS = ("phases", "agents", "commands", "scripts")
CLI_INVOCATION_RE = re.compile(
    r"fixcommit\.py[\"']?\s+--|scripts/fixcommit\.py\"")


def _invokes_retired_cli(text):
    return CLI_INVOCATION_RE.search(text) is not None


class TestNoCliInvocation(unittest.TestCase):
    """A mention ("fixcommit.py's docstring", `fixcommit.TITLE_ALLOWED`) is fine;
    an invocation form of the old command line is not."""

    def _files(self):
        for sub in LOCK_DIRS:
            for dirpath, _dirs, names in os.walk(os.path.join(PLUGIN_DIR, sub)):
                for name in names:
                    if name.endswith((".md", ".py")):
                        yield os.path.join(dirpath, name)

    def test_no_file_invokes_the_retired_cli(self):
        this = os.path.abspath(__file__)
        scanned, offenders = 0, []
        for path in self._files():
            if os.path.abspath(path) == this:
                continue  # this file spells the patterns to test them
            scanned += 1
            with open(path, "r", encoding="utf-8") as fh:
                if _invokes_retired_cli(fh.read()):
                    offenders.append(os.path.relpath(path, PLUGIN_DIR))
        self.assertGreater(scanned, 50, "the walk found too few files")
        self.assertEqual(offenders, [])

    def test_walk_covers_the_prose_that_used_to_invoke_it(self):
        rels = {os.path.relpath(p, PLUGIN_DIR) for p in self._files()}
        for rel in ("agents/fix.md", "phases/review/50-fix-loop.md",
                    "phases/shared/90-finalize.md", "scripts/fixstage.py"):
            with self.subTest(rel=rel):
                self.assertIn(rel, rels)

    def test_mutant_invocations_are_flagged(self):
        for text in ('python3 "$VC_ROOT/scripts/fixcommit.py" --finding-json f',
                     "python3 x/fixcommit.py --finding-json f",
                     "if python3 fixcommit.py --root .; then git commit; fi"):
            with self.subTest(text=text):
                self.assertTrue(_invokes_retired_cli(text))

    def test_mentions_are_not_flagged(self):
        for text in ("(fixcommit.py's docstring carries the full reasoning)",
                     "`fixcommit.TITLE_ALLOWED`",
                     "the same rule as `fixcommit.py`'s `--finding-json`",
                     "(the fixstage/fixcommit library pattern)"):
            with self.subTest(text=text):
                self.assertFalse(_invokes_retired_cli(text))


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
                     "validate_title", "build_message", "commit_subject",
                     "validate_fix_paths"):
            self.assertTrue(hasattr(fixcommit, name),
                            "fixcommit.%s is missing" % name)


if __name__ == "__main__":
    unittest.main()
