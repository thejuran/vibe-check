"""test_codex_translate.py — Family 3 (Codex output sanitization + translation).

Two properties are load-bearing here:

* T-40-05 — the title sanitization codepoint list. `title` is untrusted model
  output that flows into the rendered report AND the autonomous fix-agent
  prompt. A crafted U+202E can visually reverse a rendered title so it reads as
  something other than what was flagged; a zero-width run can smuggle bytes past
  a reviewer's eye; a U+2028 can start a second line in renderers that treat it
  as a break. The posture is sanitize-and-KEEP: the finding is never dropped
  over its title, only the dangerous codepoints are removed.
* T-40-06 — the path two-check. `file` IS a security boundary (it drives the fix
  agent's reads/edits), so it gets the opposite posture: any failure drops the
  finding and appends a FIXED note that never echoes the rejected path.

FIXTURE INTEGRITY (the 40-03 F9a lesson). Every fixture below that carries a
control character, a bidi override, or a zero-width codepoint asserts its own
contents BEFORE asserting behavior on it. A sanitization test whose fixture
silently lost the dangerous codepoint (a source-encoding round-trip, an editor
normalizing the file, an escape that parsed as something else) passes while
exercising nothing. `_assert_contains_codepoint` is that guard; it is called on
every such fixture.
"""

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest

# Make `import codex_translate` resolve when unittest discovery runs from root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import codex_translate  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
CODEX_TRANSLATE_PY = os.path.join(HERE, "codex_translate.py")

# Dangerous codepoints, written as escapes so the fixture cannot depend on this
# source file's own encoding surviving a round-trip.
RLO = "‮"       # RIGHT-TO-LEFT OVERRIDE (bidi)
LRE = "‪"       # LEFT-TO-RIGHT EMBEDDING (bidi, low end of the range)
PDI = "⁩"       # POP DIRECTIONAL ISOLATE (bidi isolate, high end)
ZWSP = "​"      # ZERO WIDTH SPACE
ZWJ = "‍"       # ZERO WIDTH JOINER (high end of the zero-width range)
BOM = "﻿"       # ZERO WIDTH NO-BREAK SPACE / BOM
LSEP = " "      # LINE SEPARATOR
PSEP = " "      # PARAGRAPH SEPARATOR
BELL = "\x07"        # ASCII control
NUL = "\x00"         # ASCII control (low end)
DEL = "\x7f"         # ASCII control (DEL)

# agents/fix.md:44 — the commit-construction allowlist. DELIBERATELY STRICTER
# than this module's display sanitizer: `"`, `'` and `,` are rejected there
# because the title is substituted into a shell command line where a `"` can
# break out of the single argument. Not a disagreement — see the docstring of
# TestAllowlistRelationship.
FIX_MD_COMMIT_CLASS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    " ._:/()#=-"
)


def _assert_contains_codepoint(case, fixture, codepoint, label):
    """Fail loudly if a fixture does not actually carry the codepoint.

    The 40-03 F9a failure mode in miniature: a guard that never trips is worse
    than no guard, because it reports success for an input it never saw.
    """
    case.assertIn(
        codepoint, fixture,
        "FIXTURE INTEGRITY: %s (U+%04X) is absent from the fixture %r — the "
        "test would pass without exercising the sanitizer"
        % (label, ord(codepoint), fixture),
    )


# --------------------------------------------------------------------------- #
# sanitize_title — T-40-05
# --------------------------------------------------------------------------- #
class TestSanitizeTitleFixtureIntegrity(unittest.TestCase):
    """The escapes above must denote the codepoints their names claim."""

    def test_escape_constants_are_the_named_codepoints(self):
        self.assertEqual(ord(RLO), 0x202E)
        self.assertEqual(ord(LRE), 0x202A)
        self.assertEqual(ord(PDI), 0x2069)
        self.assertEqual(ord(ZWSP), 0x200B)
        self.assertEqual(ord(ZWJ), 0x200D)
        self.assertEqual(ord(BOM), 0xFEFF)
        self.assertEqual(ord(LSEP), 0x2028)
        self.assertEqual(ord(PSEP), 0x2029)
        self.assertEqual(ord(BELL), 0x07)
        self.assertEqual(ord(NUL), 0x00)
        self.assertEqual(ord(DEL), 0x7F)
        # Each is a SINGLE codepoint, not a multi-char escape that parsed wrong.
        for cp in (RLO, LRE, PDI, ZWSP, ZWJ, BOM, LSEP, PSEP, BELL, NUL, DEL):
            self.assertEqual(len(cp), 1)


class TestSanitizeTitle(unittest.TestCase):
    def test_trailing_period_stripped(self):
        self.assertEqual(
            codex_translate.sanitize_title("Use shell=True carefully."),
            "Use shell=True carefully",
        )

    def test_equals_is_kept(self):
        """CRITICAL (codex-adversarial.md:122): the class MUST NOT reject `=`."""
        self.assertEqual(
            codex_translate.sanitize_title("shell=True"), "shell=True")
        self.assertEqual(
            codex_translate.sanitize_title("verify=False"), "verify=False")

    def test_bidi_override_removed(self):
        fixture = "a" + RLO + "b"
        _assert_contains_codepoint(self, fixture, RLO, "RIGHT-TO-LEFT OVERRIDE")
        self.assertEqual(codex_translate.sanitize_title(fixture), "ab")

    def test_bidi_range_endpoints_removed(self):
        for cp, label in ((LRE, "U+202A"), (RLO, "U+202E"),
                          ("⁦", "U+2066"), (PDI, "U+2069")):
            fixture = "x" + cp + "y"
            _assert_contains_codepoint(self, fixture, cp, label)
            self.assertEqual(codex_translate.sanitize_title(fixture), "xy")

    def test_zero_width_removed(self):
        for cp, label in ((ZWSP, "U+200B"), ("‌", "U+200C"),
                          (ZWJ, "U+200D"), (BOM, "U+FEFF")):
            fixture = "x" + cp + "y"
            _assert_contains_codepoint(self, fixture, cp, label)
            self.assertEqual(codex_translate.sanitize_title(fixture), "xy")

    def test_single_line_reduction_on_newline(self):
        self.assertEqual(
            codex_translate.sanitize_title("first\nsecond"), "first")

    def test_single_line_reduction_on_unicode_separators(self):
        for cp, label in ((LSEP, "U+2028"), (PSEP, "U+2029")):
            fixture = "first" + cp + "second"
            _assert_contains_codepoint(self, fixture, cp, label)
            self.assertEqual(codex_translate.sanitize_title(fixture), "first")
        self.assertEqual(
            codex_translate.sanitize_title("first\rsecond"), "first")

    def test_backticks_and_fences_removed(self):
        self.assertEqual(
            codex_translate.sanitize_title("run `rm -rf` now"),
            "run rm -rf now",
        )
        self.assertEqual(
            codex_translate.sanitize_title("```bash injected"),
            "bash injected",
        )

    def test_ascii_controls_removed(self):
        for cp, label in ((BELL, "BEL"), (NUL, "NUL"), (DEL, "DEL")):
            fixture = cp + "bell"
            _assert_contains_codepoint(self, fixture, cp, label)
            self.assertEqual(codex_translate.sanitize_title(fixture), "bell")

    def test_prose_punctuation_kept(self):
        self.assertEqual(
            codex_translate.sanitize_title('say "hi" (now)'),
            'say "hi" (now)',
        )

    def test_non_ascii_letters_kept(self):
        self.assertEqual(
            codex_translate.sanitize_title("naïve café über"),
            "naïve café über",
        )

    def test_never_returns_none_for_non_string(self):
        """sanitize-and-KEEP: a non-string title degrades to empty, never raises."""
        self.assertEqual(codex_translate.sanitize_title(None), "")
        self.assertEqual(codex_translate.sanitize_title(42), "")


class TestAllowlistRelationship(unittest.TestCase):
    """The display sanitizer is WIDER than the commit-construction allowlist.

    `agents/fix.md:44` rejects a title containing any character outside
    `[A-Za-z0-9 ._:/()#=-]`. That class excludes `"`, `'` and `,`, which THIS
    module deliberately keeps. The relationship is one-directional and must stay
    that way:

      * every character fix.md permits must survive sanitize_title unchanged
        (otherwise the display path would mangle a title the commit path
        considers legitimate), and
      * sanitize_title additionally keeps `"`, `'` and `,` — which the commit
        path (plan 40-07's fixcommit) REJECTS, because at the
        `printf ... "<finding.title>"` substitution site a `"` can break out of
        the shell argument. Do NOT re-widen the commit allowlist to match.
    """

    def test_every_commit_class_character_survives_sanitize(self):
        for ch in FIX_MD_COMMIT_CLASS:
            title = "a" + ch + "b"
            self.assertEqual(
                codex_translate.sanitize_title(title), title,
                "sanitize_title altered %r, which fix.md:44 permits" % ch,
            )

    def test_display_keeps_the_three_characters_commit_path_rejects(self):
        for ch in ('"', "'", ","):
            self.assertNotIn(
                ch, FIX_MD_COMMIT_CLASS,
                "fix.md's commit class must NOT contain %r" % ch,
            )
            title = "a" + ch + "b"
            self.assertEqual(codex_translate.sanitize_title(title), title)


# --------------------------------------------------------------------------- #
# cap_note
# --------------------------------------------------------------------------- #
class TestCapNote(unittest.TestCase):
    def test_note_cap_constant(self):
        self.assertEqual(codex_translate.NOTE_CAP, 300)

    def test_301_chars_capped_to_300(self):
        fixture = "x" * 301
        self.assertEqual(len(fixture), 301)  # fixture integrity
        self.assertEqual(len(codex_translate.cap_note(fixture)), 300)

    def test_300_chars_unchanged(self):
        fixture = "y" * 300
        self.assertEqual(codex_translate.cap_note(fixture), fixture)

    def test_single_line_reduction(self):
        self.assertEqual(codex_translate.cap_note("l1\nl2"), "l1")

    def test_unicode_separator_reduction(self):
        fixture = "l1" + LSEP + "l2"
        _assert_contains_codepoint(self, fixture, LSEP, "U+2028")
        self.assertEqual(codex_translate.cap_note(fixture), "l1")

    def test_multiline_then_capped(self):
        """Both bounds apply: first line first, then the 300-char cap."""
        fixture = ("a" * 400) + "\n" + ("b" * 400)
        self.assertEqual(codex_translate.cap_note(fixture), "a" * 300)

    def test_non_string_degrades_to_empty(self):
        self.assertEqual(codex_translate.cap_note(None), "")


# --------------------------------------------------------------------------- #
# translate_finding / translate
# --------------------------------------------------------------------------- #
def _finding(**overrides):
    base = {
        "severity": "high",
        "title": "Session token is trusted without re-validation after refresh.",
        "body": "handleRefresh() copies the old role claim, so a revoked admin "
                "keeps admin until logout.",
        "file": "src/auth/session.ts",
        "line_start": 88,
        "line_end": 94,
        "confidence": 0.82,
        "recommendation": "Re-read the role claim from the session store.",
    }
    base.update(overrides)
    return base


class TestTranslateFinding(unittest.TestCase):
    def test_ids_are_one_based_and_zero_padded(self):
        self.assertEqual(
            codex_translate.translate_finding(1, _finding())["id"], "codex-001")
        self.assertEqual(
            codex_translate.translate_finding(2, _finding())["id"], "codex-002")

    def test_confidence_rounds_to_integer_percent(self):
        out = codex_translate.translate_finding(
            1, _finding(confidence=0.874))
        self.assertEqual(out["agent_confidence"], 87)
        self.assertIsInstance(out["agent_confidence"], int)

    def test_empty_recommendation_becomes_null_fix_hint(self):
        out = codex_translate.translate_finding(1, _finding(recommendation=""))
        self.assertIsNone(out["fix_hint"])

    def test_missing_recommendation_becomes_null_fix_hint(self):
        f = _finding()
        del f["recommendation"]
        self.assertIsNone(codex_translate.translate_finding(1, f)["fix_hint"])

    def test_why_it_matters_is_the_body_verbatim(self):
        """Pinned deterministic choice: the script does not paraphrase."""
        f = _finding()
        out = codex_translate.translate_finding(1, f)
        self.assertEqual(out["why_it_matters"], f["body"])
        self.assertEqual(out["problem"], f["body"])

    def test_no_per_finding_agent_key(self):
        self.assertNotIn("agent", codex_translate.translate_finding(1, _finding()))

    def test_backfilled_fields_are_not_emitted_here(self):
        """deep-review.md:317 — those are review.md Phase 3 step 0/2's job."""
        out = codex_translate.translate_finding(1, _finding())
        for key in ("current_code", "in_diff", "silenced_marker_nearby"):
            self.assertNotIn(key, out)
        self.assertIsNone(out["intent_doc_match"])

    def test_key_set_matches_the_worked_example(self):
        self.assertEqual(
            set(codex_translate.translate_finding(1, _finding())),
            {"id", "file", "line", "title", "category", "cwe", "severity",
             "agent_confidence", "problem", "why_it_matters", "fix_hint",
             "intent_doc_match"},
        )


class TestTranslateGolden(unittest.TestCase):
    """A fixed result with two findings translates to a literal JSON golden."""

    GOLDEN = {
        "agent": "codex-adversarial",
        "findings": [
            {
                "id": "codex-001",
                "file": "src/auth/session.ts",
                "line": 88,
                "title": "Session token is trusted without re-validation "
                         "after refresh",
                "category": "adversarial",
                "cwe": None,
                "severity": "high",
                "agent_confidence": 87,
                "problem": "handleRefresh() copies the old role claim, so a "
                           "revoked admin keeps admin until logout.",
                "why_it_matters": "handleRefresh() copies the old role claim, "
                                  "so a revoked admin keeps admin until logout.",
                "fix_hint": "Re-read the role claim from the session store.",
                "intent_doc_match": None,
            },
            {
                "id": "codex-002",
                "file": "src/api/handler.py",
                "line": 12,
                "title": "Avoid shell=True in subprocess",
                "category": "adversarial",
                "cwe": None,
                "severity": "medium",
                "agent_confidence": 50,
                "problem": "The command string is built from request data.",
                "why_it_matters": "The command string is built from request data.",
                "fix_hint": None,
                "intent_doc_match": None,
            },
        ],
        "agent_notes": ["One auth gap; otherwise safe to ship."],
    }

    def test_golden(self):
        result = {
            "verdict": "needs-attention",
            "summary": "One auth gap; otherwise safe to ship.",
            "findings": [
                _finding(confidence=0.874),
                _finding(
                    severity="medium",
                    title="Avoid shell=True in subprocess.",
                    body="The command string is built from request data.",
                    file="src/api/handler.py",
                    line_start=12,
                    line_end=12,
                    confidence=0.5,
                    recommendation="",
                ),
            ],
            "next_steps": ["Add a regression test."],
        }
        out = codex_translate.translate(
            result, ["src/auth/session.ts", "src/api/handler.py"])
        self.assertEqual(out, self.GOLDEN)
        # next_steps is dropped, never carried anywhere.
        self.assertNotIn("regression test", json.dumps(out))

    def test_approve_emits_zero_findings_with_the_note(self):
        out = codex_translate.translate(
            {"verdict": "approve",
             "summary": "Nothing blocking.",
             "findings": [_finding()]},
            ["src/auth/session.ts"],
        )
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["agent_notes"], ["Nothing blocking."])
        self.assertEqual(out["agent"], "codex-adversarial")

    def test_missing_summary_yields_empty_notes(self):
        out = codex_translate.translate(
            {"verdict": "approve", "findings": []}, [])
        self.assertEqual(out["agent_notes"], [])

    def test_summary_is_single_lined_and_capped_in_notes(self):
        out = codex_translate.translate(
            {"verdict": "approve", "summary": ("s" * 400) + "\nsecond line",
             "findings": []},
            [],
        )
        self.assertEqual(out["agent_notes"], ["s" * 300])


# --------------------------------------------------------------------------- #
# Path two-check — T-40-06
# --------------------------------------------------------------------------- #
class TestPathTwoCheck(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        os.makedirs(os.path.join(self.root, "src"))

    def tearDown(self):
        self._tmp.cleanup()

    def _translate(self, path, diff_files=None):
        return codex_translate.translate(
            {"verdict": "needs-attention", "summary": "s",
             "findings": [_finding(file=path)]},
            ["src/a.py"] if diff_files is None else diff_files,
            root=self.root,
        )

    def test_valid_path_is_kept(self):
        out = self._translate("src/a.py")
        self.assertEqual(len(out["findings"]), 1)
        self.assertEqual(out["findings"][0]["file"], "src/a.py")
        self.assertEqual(out["agent_notes"], ["s"])

    def test_absolute_path_dropped(self):
        out = self._translate("/etc/passwd", diff_files=["/etc/passwd"])
        self.assertEqual(out["findings"], [])
        self.assertIn(codex_translate.DOWNGRADE_NOTE, out["agent_notes"])

    def test_option_like_path_dropped(self):
        out = self._translate("-x", diff_files=["-x"])
        self.assertEqual(out["findings"], [])
        self.assertIn(codex_translate.DOWNGRADE_NOTE, out["agent_notes"])

    def test_dot_dot_segment_dropped(self):
        """The (c) regex matches `a/../b` fully — only (b) rejects it."""
        out = self._translate("a/../b", diff_files=["a/../b"])
        self.assertEqual(out["findings"], [])

    def test_traversal_that_passes_the_regex_is_dropped(self):
        out = self._translate("../../.git/hooks/pre-commit",
                              diff_files=["../../.git/hooks/pre-commit"])
        self.assertEqual(out["findings"], [])

    def test_space_in_path_dropped_by_regex(self):
        out = self._translate("src/a b.py", diff_files=["src/a b.py"])
        self.assertEqual(out["findings"], [])

    def test_path_outside_diff_set_dropped(self):
        out = self._translate("src/other.py", diff_files=["src/a.py"])
        self.assertEqual(out["findings"], [])

    def test_deleted_diff_member_still_kept(self):
        """A file the range DELETED is a legal diff-set member (A10/B3)."""
        out = codex_translate.translate(
            {"verdict": "needs-attention", "summary": "s",
             "findings": [_finding(file="src/deleted.py")]},
            ["src/deleted.py"],
            root=self.root,
        )
        self.assertEqual(len(out["findings"]), 1)

    def test_unresolved_root_fails_closed(self):
        """An empty root must downgrade, not pass through (the empty-$ROOT bug)."""
        out = codex_translate.translate(
            {"verdict": "needs-attention", "summary": "s",
             "findings": [_finding(file="src/a.py")]},
            ["src/a.py"],
            root="",
        )
        self.assertEqual(out["findings"], [])

    def test_one_note_per_dropped_finding(self):
        out = codex_translate.translate(
            {"verdict": "needs-attention", "summary": "s",
             "findings": [_finding(file="/etc/passwd"),
                          _finding(file="-x"),
                          _finding(file="src/a.py")]},
            ["src/a.py", "/etc/passwd", "-x"],
            root=self.root,
        )
        self.assertEqual(len(out["findings"]), 1)
        self.assertEqual(
            out["agent_notes"].count(codex_translate.DOWNGRADE_NOTE), 2)

    def test_ids_renumber_contiguously_after_drops(self):
        out = codex_translate.translate(
            {"verdict": "needs-attention", "summary": "s",
             "findings": [_finding(file="/etc/passwd"),
                          _finding(file="src/a.py"),
                          _finding(file="src/b.py")]},
            ["src/a.py", "src/b.py", "/etc/passwd"],
            root=self.root,
        )
        self.assertEqual([f["id"] for f in out["findings"]],
                         ["codex-001", "codex-002"])

    def test_rejected_path_never_echoed(self):
        """The whole output must not contain any part of the rejected path."""
        secret = "src/zzsecretnamezz.py"
        out = codex_translate.translate(
            {"verdict": "needs-attention", "summary": "s",
             "findings": [_finding(file=secret)]},
            ["src/a.py"],
            root=self.root,
        )
        blob = json.dumps(out, ensure_ascii=False)
        self.assertNotIn("zzsecretnamezz", blob)
        self.assertNotIn(secret, blob)

    def test_rejected_absolute_path_never_echoed(self):
        out = self._translate("/etc/zzsecretnamezz",
                              diff_files=["/etc/zzsecretnamezz"])
        self.assertNotIn("zzsecretnamezz",
                         json.dumps(out, ensure_ascii=False))

    def test_downgrade_note_is_the_fixed_string(self):
        self.assertEqual(
            codex_translate.DOWNGRADE_NOTE,
            "codex finding downgraded: file path failed validation",
        )

    def test_no_root_skips_only_the_containment_leg(self):
        """root=None still applies (a)-(c); only guard.contained is skipped."""
        out = codex_translate.translate(
            {"verdict": "needs-attention", "summary": "s",
             "findings": [_finding(file="a/../b")]},
            ["a/../b"],
        )
        self.assertEqual(out["findings"], [])


# --------------------------------------------------------------------------- #
# run() envelope + CLI
# --------------------------------------------------------------------------- #
class TestRunEnvelope(unittest.TestCase):
    def test_run_threads_the_envelope(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "src"))
            out = codex_translate.run({
                "result": {"verdict": "needs-attention", "summary": "s",
                           "findings": [_finding(file="src/a.py")]},
                "diff_files": ["src/a.py"],
                "root": root,
            })
        self.assertEqual(len(out["findings"]), 1)

    def test_run_without_root_still_validates(self):
        out = codex_translate.run({
            "result": {"verdict": "approve", "summary": "ok", "findings": []},
            "diff_files": [],
        })
        self.assertEqual(out["findings"], [])


class TestCLIFailClosed(unittest.TestCase):
    def _run(self, payload):
        return subprocess.run(
            [sys.executable, CODEX_TRANSLATE_PY],
            input=payload,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )

    def test_valid_stdin_round_trips(self):
        payload = json.dumps({
            "result": {"verdict": "approve", "summary": "fine", "findings": []},
            "diff_files": [],
        }).encode()
        proc = self._run(payload)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        out = json.loads(proc.stdout.decode())
        self.assertEqual(out["agent"], "codex-adversarial")
        self.assertEqual(out["agent_notes"], ["fine"])

    def test_invalid_json_exits_nonzero(self):
        self.assertNotEqual(self._run(b"not json").returncode, 0)

    def test_empty_stdin_exits_nonzero(self):
        self.assertNotEqual(self._run(b"").returncode, 0)


# --------------------------------------------------------------------------- #
# Purity — the import set is EXACTLY {json, re, sys, guard}
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "re", "sys", "guard"}
    FORBIDDEN_NAMES = {"subprocess", "os", "pathlib", "shutil", "glob",
                       "eval", "exec", "compile", "__import__", "open"}

    def _tree(self):
        with open(CODEX_TRANSLATE_PY, "r", encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def _imported(self):
        imported = set()
        for node in ast.walk(self._tree()):
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
            "codex_translate.py imports outside the allowed set: "
            + str(imported - self.ALLOWED),
        )

    def test_guard_is_actually_imported(self):
        """The containment leg must be guard.py, not a re-inlined copy."""
        self.assertIn("guard", self._imported())

    def test_no_forbidden_module_imported(self):
        for name in self._imported():
            self.assertNotIn(name, self.FORBIDDEN_NAMES)

    def test_no_forbidden_calls_or_attributes(self):
        banned_call_names = {"eval", "exec", "compile", "__import__", "open"}
        banned_attr_roots = {"os", "subprocess", "pathlib", "shutil", "glob"}
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, banned_call_names,
                                 "forbidden call: " + node.func.id)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                self.assertNotIn(node.value.id, banned_attr_roots,
                                 "forbidden attribute access on: "
                                 + node.value.id)


if __name__ == "__main__":
    unittest.main()
