"""Tests for the holdout kit documents the isolated sessions receive.

Locked here:
  * No leak: the four kit briefs and the two settings templates carry no
    earlier-benchmark case names, file names, commit ids, reviewer agent names
    or patch lines. Matches are only ever counted, never printed, so a failing
    run does not itself leak the content. Each lock is also run against a
    synthetic violation so it is known to be able to trip.
  * Schema consistency: every field name in VALIDITY-RULES.md's per-file JSON
    examples appears in the verbatim schema block, in the brief of the session
    that writes that file, and (once it exists) as a string literal in
    holdout_validate.py.
  * Required sections, cross-check fields, reset blindness, budget and the
    write boundary in the finder and cross-check briefs.
"""

import glob
import os
import re
import sys
import unittest

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
KIT_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "kit")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(TOOLS_DIR))))
PATCH_GLOB = os.path.join(REPO_ROOT, "docs", "design", "b3-ground-truth",
                          "diffs", "*.patch")
VALIDATE_PY = os.path.join(TOOLS_DIR, "holdout_validate.py")

CASE_TYPES = "CASE-TYPES.md"
VALIDITY = "VALIDITY-RULES.md"
FINDER = "FINDER-BRIEF.md"
XCHECK = "CROSSCHECK-BRIEF.md"
BRIEF_DOCS = (CASE_TYPES, VALIDITY, FINDER, XCHECK)
TEMPLATES = ("finder-settings.json", "crosscheck-settings.json")

FORBIDDEN = (
    "b3-ground-truth", "ANSWER-KEY", "PREREGISTRATION", "should-quiet-",
    "should-catch", "triggarr-autoescape", "triggarr-secret",
    "triggarr-session", "triggarr-settings", "dashboard-unbounded", ".BUGGY",
    "vibe-check:bugs", "vibe-check:security", "plugins/vibe-check/agents",
)
HEX40 = re.compile(r"\b[0-9a-f]{40}\b")
PLANNING_POINTERS = ("tmux", "turingmind-code-review/.planning",
                     "CONTEXT.md", "RESEARCH.md")

CAUSAL_CATEGORIES = (
    "missing-input-validation", "missing-authz-check", "injection",
    "path-traversal", "unsafe-deserialization", "resource-exhaustion",
    "race-condition", "error-handling", "crypto-misuse", "info-disclosure",
    "logic-error", "other",
)

FINDER_FILES = ("case.json", "key.json", "provenance.json",
                "proof-results.json")
XCHECK_FILES = ("blind.json", "final.json")
VALIDATOR_FILES = ("key.json", "provenance.json", "proof-results.json")

FINDER_SECTIONS = ("Your role", "What you may read", "What you must never do",
                   "Search procedure", "Proof procedure", "What to write",
                   "When you are done")
XCHECK_SECTIONS = ("Your role", "Before reveal", "After reveal",
                   "If the owner resets a case", "What you must never do")

KEY_RE = re.compile(r'"([A-Za-z_][A-Za-z0-9_.-]*)"\s*:')


def read(name, folder=KIT_DIR):
    with open(os.path.join(folder, name), encoding="utf-8") as fh:
        return fh.read()


def _norm(line):
    return line.strip().lstrip("+-").strip()


def patch_lines():
    """Lines longer than 30 chars (after stripping +/-) from the earlier
    benchmark's patches. Held in memory only; never printed."""
    lines = set()
    for path in sorted(glob.glob(PATCH_GLOB)):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                line = _norm(raw)
                if len(line) > 30:
                    lines.add(line)
    return lines


def leak_count(text, patch_set):
    """Number of leak hits in text: forbidden substrings, 40-hex ids and
    lines that also occur in a benchmark patch."""
    hits = sum(1 for s in FORBIDDEN if s in text)
    hits += len(HEX40.findall(text))
    hits += sum(1 for line in text.splitlines() if _norm(line) in patch_set)
    return hits


def sections(text, level="## "):
    """{heading: body} for headings of exactly the given level."""
    out, current, buf = {}, None, []
    for line in text.splitlines():
        if line.startswith(level) and not line.startswith(level.strip() + "#"):
            if current is not None:
                out[current] = "\n".join(buf)
            current, buf = line[len(level):].strip(), []
        elif current is not None:
            buf.append(line)
    if current is not None:
        out[current] = "\n".join(buf)
    return out


def schema_examples(text):
    """{file name: set(field names)} from the '#### <file> ...' headings and
    their ```json fences in the Schemas section of VALIDITY-RULES.md."""
    schemas = sections(text)["Schemas"]
    out, current, in_fence = {}, None, False
    for line in schemas.splitlines():
        if line.startswith("#### "):
            current = line[5:].split()[0]
            continue
        if line.startswith("```"):
            in_fence = line.strip() == "```json" and current is not None
            continue
        if in_fence:
            out.setdefault(current, set()).update(KEY_RE.findall(line))
    return out


def verbatim_block(text):
    schemas = sections(text)["Schemas"]
    m = re.search(r"```text\n(.*?)\n```", schemas, re.S)
    return m.group(1) if m else ""


def mentions(text, field):
    return ('"%s"' % field) in text or ("`%s`" % field) in text


class TestNoLeak(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.patches = patch_lines()

    def test_patch_lines_loaded(self):
        # The patch-line lock is only real if it actually holds lines.
        self.assertTrue(glob.glob(PATCH_GLOB), "no benchmark patches found")
        self.assertGreater(len(self.patches), 0)

    def test_docs_and_templates_do_not_leak(self):
        for name in BRIEF_DOCS + TEMPLATES:
            with self.subTest(name=name):
                n = leak_count(read(name), self.patches)
                self.assertEqual(n, 0, "%d leak hit(s) in %s" % (n, name))

    def test_detector_trips_on_each_forbidden_substring(self):
        for s in FORBIDDEN:
            with self.subTest(i=FORBIDDEN.index(s)):
                self.assertEqual(leak_count("x %s y" % s, set()), 1)

    def test_detector_trips_on_commit_id(self):
        self.assertEqual(leak_count("rev " + "ab" * 20 + " end", set()), 1)
        self.assertEqual(leak_count("sha " + "ab" * 32, set()), 0)

    def test_detector_trips_on_patch_line(self):
        sample = sorted(self.patches)[0]
        text = "intro\n+  %s\noutro" % sample
        self.assertEqual(leak_count(text, self.patches), 1)

    def test_briefs_do_not_point_at_planning(self):
        for name in (FINDER, XCHECK):
            text = read(name).lower()
            for s in PLANNING_POINTERS:
                with self.subTest(name=name, s=s):
                    self.assertNotIn(s.lower(), text)


class TestSchemaConsistency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rules = read(VALIDITY)
        cls.examples = schema_examples(cls.rules)

    def test_examples_cover_every_written_file(self):
        for f in FINDER_FILES + XCHECK_FILES + ("xcheck-ledger.json",):
            with self.subTest(file=f):
                self.assertTrue(self.examples.get(f), f)

    def test_example_fields_are_in_the_verbatim_block(self):
        block = verbatim_block(self.rules)
        self.assertIn("AGREEMENT RULE", block)
        self.assertIn("NON-RUNNABLE RULE", block)
        for f, fields in self.examples.items():
            for field in fields:
                with self.subTest(file=f, field=field):
                    self.assertIn('"%s"' % field, block)

    def test_finder_brief_names_every_finder_field(self):
        brief = read(FINDER)
        for f in FINDER_FILES:
            for field in sorted(self.examples[f]):
                with self.subTest(file=f, field=field):
                    self.assertTrue(mentions(brief, field), field)

    def test_crosscheck_brief_names_every_session_field(self):
        brief = read(XCHECK)
        for f in XCHECK_FILES:
            for field in sorted(self.examples[f]):
                with self.subTest(file=f, field=field):
                    self.assertTrue(mentions(brief, field), field)

    def test_detector_trips_on_missing_field(self):
        brief = read(FINDER).replace('"causal_failure_category"', '"x"') \
                            .replace("`causal_failure_category`", "`x`")
        self.assertFalse(mentions(brief, "causal_failure_category"))

    def test_case_types_categories_match(self):
        text = sections(read(CASE_TYPES))["Causal-failure categories"]
        listed = re.findall(r"^- `([a-z-]+)`", text, re.M)
        self.assertEqual(tuple(listed), CAUSAL_CATEGORIES)
        for c in CAUSAL_CATEGORIES:
            self.assertIn('"%s"' % c, verbatim_block(self.rules))

    def test_validator_literals(self):
        if not os.path.exists(VALIDATE_PY):
            self.skipTest("holdout_validate.py not installed yet")
        with open(VALIDATE_PY, encoding="utf-8") as fh:
            src = fh.read()
        for f in VALIDATOR_FILES:
            for field in sorted(self.examples[f]):
                with self.subTest(file=f, field=field):
                    self.assertTrue(('"%s"' % field) in src
                                    or ("'%s'" % field) in src, field)
        sys.path.insert(0, TOOLS_DIR)
        import holdout_validate  # noqa: E402
        self.assertEqual(set(holdout_validate.CAUSAL_CATEGORIES),
                         set(CAUSAL_CATEGORIES))


class TestRequiredSections(unittest.TestCase):

    def _assert_in_order(self, name, wanted):
        headings = list(sections(read(name)))
        for h in wanted:
            self.assertIn(h, headings, "%s lacks '%s'" % (name, h))
        self.assertEqual([h for h in headings if h in wanted], list(wanted))

    def test_finder_sections(self):
        self._assert_in_order(FINDER, FINDER_SECTIONS)

    def test_crosscheck_sections(self):
        self._assert_in_order(XCHECK, XCHECK_SECTIONS)

    def test_case_types_slots_in_order(self):
        slots = re.findall(r"^## ([CQ][123])\s*$", read(CASE_TYPES), re.M)
        self.assertEqual(slots, ["C1", "C2", "C3", "Q1", "Q2", "Q3"])

    def test_validity_rules_numbered(self):
        rules = re.findall(r"^(R-\d\d) ", read(VALIDITY), re.M)
        self.assertEqual(rules, ["R-%02d" % i for i in range(1, 13)])


class TestCrosscheckFields(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = read(XCHECK)

    def test_names_every_field(self):
        for f in ("defect_category", "type_guess", "reveal_token",
                  "type_agrees", "defect_agrees", "causal_failure_agrees",
                  "proof_agrees", "quiet_confirmed", "proof_rerun_exit"):
            with self.subTest(field=f):
                self.assertIn("`%s`" % f, self.text)
        self.assertIn("REVEAL-TOKEN", self.text)

    def test_names_every_category(self):
        for c in CAUSAL_CATEGORIES:
            with self.subTest(category=c):
                self.assertIn("`%s`" % c, self.text)

    def test_other_blocks(self):
        self.assertRegex(self.text, r"`other`[^\n]*\b(block|blocks)\b")

    def test_nonrunnable_subsection_under_after_reveal(self):
        after = sections(self.text)["After reveal"]
        sub = sections(after, "### ")
        self.assertIn("Non-runnable proofs", sub)
        body = sub["Non-runnable proofs"]
        for s in ("`runnable`", "`nonrunnable_reason`", "`manual_evidence`",
                  "`proof_rerun_exit`", "`null`"):
            with self.subTest(s=s):
                self.assertIn(s, body)
        self.assertRegex(body, r"owner[^.]*decid|decision[^.]*owner")
        self.assertEqual(self.text.count("### Non-runnable proofs"), 1)

    def test_no_case_ids_or_expected_verdicts(self):
        self.assertIsNone(re.search(r"\b[HX]-[0-9a-f]{8}\b", self.text))
        self.assertNotRegex(self.text.lower(),
                            r"expected verdict (is|for [a-z0-9-]+ is)")


class TestResetBlindness(unittest.TestCase):

    def test_reset_section(self):
        body = sections(read(XCHECK))["If the owner resets a case"]
        low = body.lower()
        for s in ("fresh workspace", "different cross-check session",
                  "never asked to judge"):
            with self.subTest(s=s):
                self.assertIn(s, low)
        for s in ("new xid", "judge it from scratch"):
            with self.subTest(s=s):
                self.assertNotIn(s, low)


class TestBudgetAndRules(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = read(FINDER)

    def test_budget_and_reviewer_rule(self):
        self.assertRegex(self.text, r"\b25\b")
        self.assertIn("selected_using_reviewer_output", self.text)
        self.assertIn("do not run any code-review tool", self.text.lower())

    def test_retired_revisions(self):
        self.assertGreaterEqual(self.text.count("RETIRED-REVISIONS.json"), 2)

    def test_write_boundary(self):
        self.assertRegex(self.text,
                         r"only[^.\n]*`sealed/`[^.\n]*`work/`"
                         r"|`sealed/`[^.\n]*`work/`[^.\n]*only")

    def test_exports_not_worktrees(self):
        self.assertIn("git archive", self.text.replace("-C <repo> ", ""))
        self.assertIn("git worktree", self.text)

    def test_done_line(self):
        self.assertIn("Six cases written. Run bin/holdout validate.",
                      self.text)


if __name__ == "__main__":
    unittest.main()
