"""Tests for step_count: the counting rule for model-run mechanical steps.

Every lock here lands with a mutant that trips it, and every mutant first
asserts that the mutation really happened (the inserted text is present in
the mutated copy and absent from the original), so no guard is decorative.
"""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import step_count  # noqa: E402  (sibling module under test)

STEP_COUNT_PY = os.path.join(HERE, "step_count.py")
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PLUGIN_SCRIPTS = os.path.join(REPO_ROOT, "plugins", "vibe-check", "scripts")

BASELINE_COMMIT = "dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4"
FINALIZE_MD = "phases/shared/90-finalize.md"

# Per-file bash fences at BASELINE_COMMIT, in footprint.MODE_PATHS["finalize"]
# order. Recounted twice on 2026-11-13 (plan checker, then planner) and again
# on 2026-11-14 by this file's two independent recounts below: a plain
# `^\s*`{3,4}bash$` line loop over `git show`, and the house expression copied
# from test_finalize_card.bash_fences.
BASH_FENCES_AT_PIN = [1, 0, 1, 10, 7, 5, 18]
BASH_FENCES_TOTAL_AT_PIN = 42
# What the wrong rule (three backticks at column 0 only) finds at the pin.
WRONG_RULE_TOTAL_AT_PIN = 18
WRONG_RULE_PATTERN = r"^```bash$"

# 2.14.1 totals and file list: verified at dd8e4ab on 2026-11-14 by
# step_count.py and the two independent fence recounts below.
INLINE_COMMANDS_AT_PIN = 5
WRITE_TOOL_WRITES_AT_PIN = 7
CARRIED_PASTE_SITES_AT_PIN = 38
MODEL_RUN_STEPS_AT_PIN = 92
PRINTED_LITERALS_AT_PIN = 11
FINALIZE_FILES_AT_PIN = [
    "commands/review.md",
    "phases/shared/00-contract.md",
    "phases/shared/01-bootstrap.md",
    "phases/review/00-scope.md",
    "phases/review/05-state.md",
    "phases/review/06-config.md",
    "phases/shared/90-finalize.md",
]
# footprint.py --rev dd8e4ab --json, mode finalize, read 2026-11-14.
FOOTPRINT_FINALIZE_BYTES_AT_PIN = 136114
FOOTPRINT_FINALIZE_FILES_AT_PIN = 7

# Hand classification at dd8e4ab (CRITERION.md holds the tables).
# Lines naming the Write tool in the seven files: all in 90-finalize.md,
# lines 22, 55, 169, 184, 198, 243 and 301; every one instructs a write.
WRITE_INSTRUCTION_LINES = [22, 55, 169, 184, 198, 243, 301]
# Candidate inline spans: all in 90-finalize.md, lines 180, 184, 243, 271
# and 272; every one instructs a run.
INLINE_INSTRUCTION_LINES = [180, 184, 243, 271, 272]
RM_SPAN = 'rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"'

RECORD_PATH = os.path.abspath(
    os.path.join(HERE, "..", "baseline", "steps-v2.14.1.json"))
CRITERION_PATH = os.path.abspath(os.path.join(HERE, "..", "CRITERION.md"))

SITUATION_IDS = ("clean-close", "card-first", "one-rebuild", "refused-close",
                 "fresh-shell-restart")
CRITERION_HEADINGS = (
    "## The rule in one paragraph",
    "## Baseline numbers (2.14.1)",
    "## Counting rule",
    "## Maintenance added",
    "## If neither count drops",
    "## Comparison workload",
    '## What "same behaviour" means',
    "## Usage and cost",
)

# test_finalize_card.bash_fences, copied character for character.
_HOUSE_FENCE_RE = r"```bash\n(.*?)\n[ \t]*```"
_PLAIN_FENCE_LINE = re.compile(r"^\s*`{3,4}bash$")


def _git_show(rel, rev=BASELINE_COMMIT):
    proc = subprocess.run(
        ["git", "-C", REPO_ROOT, "show", "%s:plugins/vibe-check/%s" % (rev, rel)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
    if proc.returncode != 0:
        raise AssertionError("git show failed for %s: %s" % (rel, proc.stderr))
    return proc.stdout.decode("utf-8")


def _finalize_paths():
    if PLUGIN_SCRIPTS not in sys.path:
        sys.path.insert(0, PLUGIN_SCRIPTS)
    import footprint
    return list(footprint.MODE_PATHS["finalize"])


def _passes(cls, name):
    result = unittest.TestResult()
    cls(name).run(result)
    return result.wasSuccessful()


SYNTH = (
    "Intro.\n"
    "```bash\n"
    "AFILE=$(mktemp)\n"
    "printf 'AFILE=%s\\n' \"$AFILE\"\n"
    "```\n"
    "Write it with the Write tool now.\n"
    "```bash\n"
    "cat \"$AFILE\" \"$AFILE\" 2>\"$AFILE.err\"\n"
    "```\n"
)


class TestCountText(unittest.TestCase):
    def test_synthetic_counts(self):
        got = step_count.count_text(SYNTH)
        self.assertEqual(got["bash_fences"], 2)
        self.assertEqual(got["inline_commands"], 0)
        self.assertEqual(got["printed_literals"], ["AFILE"])
        self.assertEqual(got["carried_paste_sites"], 3)
        self.assertEqual(got["write_tool_writes"], 1)
        self.assertEqual(got["model_run_steps"], 6)

    def test_paste_inside_printing_fence_not_counted(self):
        text = ("```bash\n"
                "AFILE=$(mktemp)\n"
                "printf 'AFILE=%s\\n' \"$AFILE\"\n"
                "echo \"$AFILE\" \"$AFILE.x\"\n"
                "```\n")
        got = step_count.count_text(text)
        self.assertEqual(got["printed_literals"], ["AFILE"])
        self.assertEqual(got["carried_paste_sites"], 0)

    def test_printed_name_with_a_different_variable(self):
        text = ("```bash\n"
                "printf 'CARDROWSFILE=%s\\n' \"$ROWSFILE\"\n"
                "```\n")
        self.assertEqual(step_count.count_text(text)["printed_literals"],
                         ["CARDROWSFILE"])


class TestFenceShapes(unittest.TestCase):
    def test_indented_by_spaces(self):
        text = "x\n     ```bash\n     echo hi\n     ```\n"
        self.assertEqual(step_count.count_text(text)["bash_fences"], 1)

    def test_indented_by_tab(self):
        text = "x\n\t```bash\n\techo hi\n\t```\n"
        self.assertEqual(step_count.count_text(text)["bash_fences"], 1)

    def test_four_backticks_counted_once(self):
        text = ("````bash\n"
                "echo one\n"
                "```\n"
                "```bash\n"
                "echo inner\n"
                "```\n"
                "````\n")
        self.assertEqual(step_count.count_text(text)["bash_fences"], 1)
        self.assertEqual(len(step_count.fences(text)), 1)
        self.assertIn("echo inner", step_count.fences(text)[0])

    def test_non_bash_fences_count_nothing(self):
        text = ("```json\n"
                "```bash\n"
                "echo hidden\n"
                "```\n"
                "```\n"
                "```bash\n"
                "printf 'AFILE=%s\\n' \"$AFILE\"\n"
                "```\n"
                "```\n")
        got = step_count.count_text(text)
        self.assertEqual(got["bash_fences"], 0)
        self.assertEqual(got["printed_literals"], [])
        self.assertEqual(got["model_run_steps"], 0)


class TestInlineCommands(unittest.TestCase):
    PRINTER = ("```bash\n"
               "printf 'AFILE=%s\\n' \"$AFILE\"\n"
               "printf 'BFILE=%s\\n' \"$BFILE\"\n"
               "```\n")

    def _count(self, extra):
        with mock.patch.object(step_count, "INLINE_RUN_LEADS", ("run ",)):
            base = step_count.count_text(self.PRINTER)
            got = step_count.count_text(self.PRINTER + extra)
        return base, got

    def test_run_lead_counts(self):
        base, got = self._count('then run `rm -f "$AFILE" "$BFILE"` and go on\n')
        self.assertEqual(got["inline_commands"], base["inline_commands"] + 1)
        self.assertEqual(got["carried_paste_sites"], base["carried_paste_sites"] + 2)
        self.assertEqual(got["model_run_steps"], base["model_run_steps"] + 3)

    def test_bare_mention_counts_nothing(self):
        base, got = self._count('the literal `"$AFILE"` is reused\n')
        self.assertEqual(got, base)

    def test_no_lead_counts_nothing(self):
        base, got = self._count('see `rm -f "$AFILE"` above\n')
        self.assertEqual(got, base)

    def test_inline_span_inside_fence_counts_nothing(self):
        base, got = self._count('```text\nthen run `rm -f "$AFILE"` and go\n```\n')
        self.assertEqual(got["inline_commands"], base["inline_commands"])
        self.assertEqual(got["carried_paste_sites"], base["carried_paste_sites"])


class TestCountPath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = step_count.count_path(REPO_ROOT, rev=BASELINE_COMMIT)

    def test_rows_follow_mode_paths(self):
        self.assertEqual([r["path"] for r in self.record["files"]], _finalize_paths())
        self.assertEqual(len(self.record["files"]), 7)

    def test_totals_are_column_sums(self):
        for key in ("bash_fences", "inline_commands", "write_tool_writes",
                    "carried_paste_sites", "model_run_steps"):
            self.assertEqual(self.record["totals"][key],
                             sum(r[key] for r in self.record["files"]), key)
        t = self.record["totals"]
        self.assertEqual(t["model_run_steps"],
                         t["bash_fences"] + t["inline_commands"]
                         + t["write_tool_writes"] + t["carried_paste_sites"])

    def test_count_files_gives_same_rows_without_footprint(self):
        paths = _finalize_paths()
        with mock.patch.dict(sys.modules, {"footprint": None}):
            direct = step_count.count_files(REPO_ROOT, BASELINE_COMMIT, paths)
        self.assertEqual(direct["files"], self.record["files"])
        self.assertEqual(direct["totals"], self.record["totals"])

    def test_pinned_fence_figures(self):
        # Counted here, not in setUpClass, so TestMutants can run this test on
        # its own (a lone TestCase.run skips class fixtures) under a patch.
        record = step_count.count_path(REPO_ROOT, rev=BASELINE_COMMIT)
        self.assertEqual([r["bash_fences"] for r in record["files"]],
                         BASH_FENCES_AT_PIN)
        self.assertEqual(record["totals"]["bash_fences"],
                         BASH_FENCES_TOTAL_AT_PIN)

    def test_kind_label_is_not_tokens(self):
        self.assertIn("not tokens", self.record["kind"])
        self.assertIn("not price", self.record["kind"])
        self.assertEqual(self.record["rule_version"], step_count.RULE_VERSION)


class TestIndependentRecounts(unittest.TestCase):
    def test_plain_line_loop(self):
        got = []
        for rel in _finalize_paths():
            n = 0
            for line in _git_show(rel).splitlines():
                if _PLAIN_FENCE_LINE.match(line):
                    n += 1
            got.append(n)
        self.assertEqual(got, BASH_FENCES_AT_PIN)

    def test_house_expression(self):
        got = [len(re.findall(_HOUSE_FENCE_RE, _git_show(rel), re.S))
               for rel in _finalize_paths()]
        self.assertEqual(got, BASH_FENCES_AT_PIN)

    def test_module_agrees_with_both(self):
        for rel, want in zip(_finalize_paths(), BASH_FENCES_AT_PIN):
            self.assertEqual(len(step_count.fences(_git_show(rel))), want, rel)


class TestFixtureFacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = _git_show(FINALIZE_MD)

    def test_indented_and_four_backtick_fences_exist(self):
        lines = self.text.splitlines()
        indented = [l for l in lines if re.match(r"^[ \t]+`{3,4}bash$", l)]
        four = [l for l in lines if re.match(r"^\s*````bash$", l)]
        self.assertGreaterEqual(len(indented), 1)
        self.assertEqual(len(four), 1)

    def test_blobfile_and_gatefile_printed(self):
        printed = step_count.count_text(self.text)["printed_literals"]
        self.assertIn("BLOBFILE", printed)
        self.assertIn("GATEFILE", printed)

    def test_blob_and_gate_printers_are_indented(self):
        lines = self.text.splitlines()
        for name in ("BLOBFILE", "GATEFILE"):
            needle = "printf '%s=%%s\\n' \"$%s\"" % (name, name)
            at = next(i for i, l in enumerate(lines) if needle in l)
            opener = next(lines[j] for j in range(at, -1, -1)
                          if re.match(r"^\s*`{3,4}bash$", lines[j]))
            self.assertTrue(opener[0] in " \t", (name, opener))

    def test_inline_rm_outside_fences(self):
        span = '`rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"`'
        self.assertIn(span, self.text)
        outside = step_count.outside_fence_lines(self.text)
        self.assertTrue(any(span in l for l in outside))
        for body in step_count.fences(self.text):
            self.assertNotIn(span, body)


class TestMutants(unittest.TestCase):
    """Mutants on a temp copy of the 2.14.1 Finalize files, read via --root."""

    @classmethod
    def setUpClass(cls):
        cls.paths = _finalize_paths()
        cls.texts = {rel: _git_show(rel) for rel in cls.paths}

    def _tree(self, mutated=None):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        for rel in self.paths:
            text = self.texts[rel]
            if mutated is not None and rel == FINALIZE_MD:
                text = mutated
            dest = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(text)
        return tmp

    def _diff(self, mutated, inserted):
        orig = self.texts[FINALIZE_MD]
        self.assertIn(inserted, mutated)
        self.assertNotIn(inserted, orig)
        self.assertNotEqual(mutated, orig)
        base = step_count.count_path(REPO_ROOT, root=self._tree())["totals"]
        got = step_count.count_path(REPO_ROOT, root=self._tree(mutated))["totals"]
        return {k: got[k] - base[k] for k in base if isinstance(base[k], int)}

    def _expect(self, delta, **want):
        for key in ("bash_fences", "inline_commands", "write_tool_writes",
                    "carried_paste_sites", "printed_literals_distinct",
                    "model_run_steps"):
            self.assertEqual(delta[key], want.get(key, 0), (key, delta))

    def test_mutant_column0_fence(self):
        ins = "\n```bash\necho mutant-col0\n```\n"
        d = self._diff(self.texts[FINALIZE_MD] + ins, ins)
        self._expect(d, bash_fences=1, model_run_steps=1)

    def test_mutant_indented_fence(self):
        ins = "\n     ```bash\n     echo mutant-indented\n     ```\n"
        d = self._diff(self.texts[FINALIZE_MD] + ins, ins)
        self._expect(d, bash_fences=1, model_run_steps=1)

    def test_mutant_four_backtick_fence(self):
        ins = "\n````bash\necho mutant-four\n```\nnot a close\n````\n"
        d = self._diff(self.texts[FINALIZE_MD] + ins, ins)
        self._expect(d, bash_fences=1, model_run_steps=1)

    def test_mutant_paste_site(self):
        anchor = "printf '%s\\n' \"$COUNTS_JSON\"   #"
        orig = self.texts[FINALIZE_MD]
        self.assertEqual(orig.count(anchor), 1)
        new = "printf '%s\\n' \"$COUNTS_JSON\" \"$BLOBFILE\"   #"
        d = self._diff(orig.replace(anchor, new), new)
        self._expect(d, carried_paste_sites=1, model_run_steps=1)

    def test_mutant_inline_command(self):
        ins = '\nThen run `rm -f "$GATEFILE"` once more.\n'
        d = self._diff(self.texts[FINALIZE_MD] + ins, ins)
        self._expect(d, inline_commands=1, carried_paste_sites=1, model_run_steps=2)

    def test_mutant_write_phrase(self):
        ins = "\nSave the mutant file with the Write tool.\n"
        d = self._diff(self.texts[FINALIZE_MD] + ins, ins)
        self._expect(d, write_tool_writes=1, model_run_steps=1)

    def test_mutant_printed_literal(self):
        anchor = "printf 'BLOBFILE=%s\\n' \"$BLOBFILE\"\n"
        orig = self.texts[FINALIZE_MD]
        self.assertEqual(orig.count(anchor), 1)
        ins = "printf 'ZEDMUTANTFILE=%s\\n' \"$BLOBFILE\"\n"
        d = self._diff(orig.replace(anchor, anchor + "     " + ins), ins)
        self._expect(d, printed_literals_distinct=1)

    def test_mutant_same_fence_exclusion_off(self):
        name = "test_paste_inside_printing_fence_not_counted"
        self.assertTrue(_passes(TestCountText, name))
        with mock.patch.object(step_count, "_fences_for_pastes",
                               lambda bodies, name: list(bodies)):
            self.assertFalse(_passes(TestCountText, name))

    def test_mutant_wrong_fence_rule(self):
        wrong = re.compile(WRONG_RULE_PATTERN)
        self.assertNotEqual(wrong.pattern, step_count.FENCE_OPEN.pattern)
        line_count = 0
        for rel in self.paths:
            for line in self.texts[rel].splitlines():
                if wrong.match(line):
                    line_count += 1
        self.assertTrue(_passes(TestCountPath, "test_pinned_fence_figures"))
        with mock.patch.object(step_count, "FENCE_OPEN", wrong):
            rec = step_count.count_path(REPO_ROOT, rev=BASELINE_COMMIT)
            printed = step_count.count_text(self.texts[FINALIZE_MD])["printed_literals"]
            pinned_holds = _passes(TestCountPath, "test_pinned_fence_figures")
        total = rec["totals"]["bash_fences"]
        self.assertLess(total, BASH_FENCES_TOTAL_AT_PIN)
        self.assertEqual(total, WRONG_RULE_TOTAL_AT_PIN)
        self.assertEqual(total, line_count)
        self.assertNotIn("BLOBFILE", printed)
        self.assertFalse(pinned_holds)


class TestClassification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = {rel: _git_show(rel) for rel in FINALIZE_FILES_AT_PIN}

    def _texts(self):
        # Read here too, so a lone run under a mutant (no class fixture) works.
        if not hasattr(self, "texts"):
            self.texts = {rel: _git_show(rel) for rel in FINALIZE_FILES_AT_PIN}
        return self.texts

    def test_write_phrases_count_exactly_the_instruction_lines(self):
        texts = self._texts()
        total = sum(step_count.count_text(t)["write_tool_writes"]
                    for t in texts.values())
        self.assertEqual(total, WRITE_TOOL_WRITES_AT_PIN)
        self.assertEqual(total, len(WRITE_INSTRUCTION_LINES))
        hits = []
        mentions = []
        for rel, text in texts.items():
            for n, line in enumerate(text.splitlines(), 1):
                if any(p in line for p in step_count.WRITE_PHRASES):
                    hits.append((rel, n))
                if "Write tool" in line or "Use Write" in line:
                    mentions.append((rel, n))
        want = [(FINALIZE_MD, n) for n in WRITE_INSTRUCTION_LINES]
        self.assertEqual(hits, want)
        # Every line naming the Write tool was classified "instructs a write".
        self.assertEqual(mentions, want)

    def test_inline_commands_count_exactly_the_instruction_spans(self):
        texts = self._texts()
        total = sum(step_count.count_text(t)["inline_commands"]
                    for t in texts.values())
        self.assertEqual(total, INLINE_COMMANDS_AT_PIN)
        self.assertEqual(total, len(INLINE_INSTRUCTION_LINES))
        found = []
        for rel, text in texts.items():
            lines = text.splitlines()
            for line, span, before in step_count.inline_candidates(text):
                counted = any(before.endswith(l) for l in step_count.INLINE_RUN_LEADS)
                found.append((rel, lines.index(line) + 1, counted))
        want = [(FINALIZE_MD, n, True) for n in INLINE_INSTRUCTION_LINES]
        self.assertEqual(found, want)

    def test_rm_instruction_is_counted(self):
        text = self._texts()[FINALIZE_MD]
        lines = text.splitlines()
        counted = [(lines.index(line) + 1, span)
                   for line, span, before in step_count.inline_candidates(text)
                   if any(before.endswith(l) for l in step_count.INLINE_RUN_LEADS)]
        self.assertIn((272, RM_SPAN), counted)

    def test_mutant_lead_list_back_to_run_only(self):
        name = "test_inline_commands_count_exactly_the_instruction_spans"
        self.assertTrue(_passes(TestClassification, name))
        with mock.patch.object(step_count, "INLINE_RUN_LEADS", ("run ",)):
            self.assertFalse(_passes(TestClassification, name))

    def test_mutant_write_phrases_back_to_one(self):
        name = "test_write_phrases_count_exactly_the_instruction_lines"
        self.assertTrue(_passes(TestClassification, name))
        with mock.patch.object(step_count, "WRITE_PHRASES", ("with the Write tool",)):
            self.assertFalse(_passes(TestClassification, name))


def _path_list_problems(record):
    paths = [row["path"] for row in record["files"]]
    if paths != FINALIZE_FILES_AT_PIN:
        return ["record path list differs: %r" % paths]
    return []


class TestRecord(unittest.TestCase):
    def _load(self):
        with open(RECORD_PATH, encoding="utf-8") as fh:
            return json.load(fh)

    def _tampered(self, record):
        self.assertNotEqual(record, self._load())
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "steps.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(step_count.dump_json(record))
        return path

    def test_record_shape_and_pins(self):
        rec = self._load()
        self.assertEqual(rec["rev"], BASELINE_COMMIT)
        self.assertEqual(rec["rule_version"], step_count.RULE_VERSION)
        t = rec["totals"]
        self.assertEqual(t["bash_fences"], BASH_FENCES_TOTAL_AT_PIN)
        self.assertEqual(t["inline_commands"], INLINE_COMMANDS_AT_PIN)
        self.assertEqual(t["write_tool_writes"], WRITE_TOOL_WRITES_AT_PIN)
        self.assertEqual(t["carried_paste_sites"], CARRIED_PASTE_SITES_AT_PIN)
        self.assertEqual(t["model_run_steps"], MODEL_RUN_STEPS_AT_PIN)
        self.assertEqual(t["printed_literals_distinct"], PRINTED_LITERALS_AT_PIN)
        self.assertEqual(rec["write_phrases"], list(step_count.WRITE_PHRASES))
        self.assertEqual(rec["inline_run_leads"], list(step_count.INLINE_RUN_LEADS))

    def test_record_file_is_the_cli_output(self):
        fresh = step_count.count_path(REPO_ROOT, rev=BASELINE_COMMIT)
        with open(RECORD_PATH, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), step_count.dump_json(fresh))

    def test_record_path_list(self):
        self.assertEqual(_path_list_problems(self._load()), [])

    def test_verify_steps_clean(self):
        self.assertEqual(step_count.verify_steps(REPO_ROOT, RECORD_PATH), [])

    def test_mutant_total_off_by_one(self):
        rec = self._load()
        rec["totals"]["model_run_steps"] += 1
        problems = step_count.verify_steps(REPO_ROOT, self._tampered(rec))
        self.assertTrue(any("model_run_steps" in p for p in problems), problems)

    def test_mutant_file_fences_off_by_one(self):
        rec = self._load()
        rec["files"][3]["bash_fences"] += 1
        problems = step_count.verify_steps(REPO_ROOT, self._tampered(rec))
        self.assertTrue(any("phases/review/00-scope.md" in p and "bash_fences" in p
                            for p in problems), problems)

    def test_mutant_row_removed(self):
        rec = self._load()
        del rec["files"][-1]
        self._tampered(rec)
        self.assertNotEqual(_path_list_problems(rec), [])

    def test_baseline_does_not_follow_live_mode_paths(self):
        if PLUGIN_SCRIPTS not in sys.path:
            sys.path.insert(0, PLUGIN_SCRIPTS)
        import footprint
        orig = list(footprint.MODE_PATHS["finalize"])
        shorter = orig[:-1]
        with mock.patch.dict(footprint.MODE_PATHS, {"finalize": shorter}):
            self.assertLess(len(footprint.MODE_PATHS["finalize"]), len(orig))
            self.assertEqual(step_count.verify_steps(REPO_ROOT, RECORD_PATH), [])
            # count_path does read the live list, so the patch really bites.
            live = step_count.count_path(REPO_ROOT, rev=BASELINE_COMMIT)
            self.assertEqual(len(live["files"]), len(shorter))


def criterion_problems(doc, record, footprint_bytes):
    """Problems with CRITERION.md against the record and the byte figure."""
    problems = []
    lines = doc.splitlines()
    for heading in CRITERION_HEADINGS:
        if heading not in lines:
            problems.append("missing heading: " + heading)
    for sid in SITUATION_IDS:
        if "`%s`" % sid not in doc:
            problems.append("missing situation: " + sid)
    t = record["totals"]
    row = ("| Model-run mechanical steps | %d | %d bash blocks, %d inline commands, "
           "%d files written, %d values copied |" % (
               t["model_run_steps"], t["bash_fences"], t["inline_commands"],
               t["write_tool_writes"], t["carried_paste_sites"]))
    if row not in doc:
        problems.append("step row does not match the record")
    if "and %d model-run mechanical steps" % t["model_run_steps"] not in doc:
        problems.append("headline steps do not match the record")
    flat = " ".join(doc.split())
    total_line = "= %d + %d + %d + %d = %d." % (
        t["bash_fences"], t["inline_commands"], t["write_tool_writes"],
        t["carried_paste_sites"], t["model_run_steps"])
    if total_line not in flat:
        problems.append("step sum line does not match the record")
    byte_row = "| Instructions loaded (bytes) | {:,} | {} files |".format(
        footprint_bytes, FOOTPRINT_FINALIZE_FILES_AT_PIN)
    if byte_row not in doc:
        problems.append("byte row does not match the footprint figure")
    if re.search(r"\$[0-9]", doc):
        problems.append("dollar amount present")
    if "%" in doc:
        problems.append("percent sign present")
    return problems


class TestCriterionDoc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CRITERION_PATH, encoding="utf-8") as fh:
            cls.doc = fh.read()
        with open(RECORD_PATH, encoding="utf-8") as fh:
            cls.record = json.load(fh)

    def _check(self, doc):
        return criterion_problems(doc, self.record, FOOTPRINT_FINALIZE_BYTES_AT_PIN)

    def test_doc_matches_record(self):
        self.assertEqual(self._check(self.doc), [])

    def test_footprint_figure_at_pin(self):
        if PLUGIN_SCRIPTS not in sys.path:
            sys.path.insert(0, PLUGIN_SCRIPTS)
        import footprint
        root = os.path.join(REPO_ROOT, "plugins", "vibe-check")
        stats = footprint.path_stats(root, "finalize", rev=BASELINE_COMMIT)
        self.assertEqual(stats["bytes"], FOOTPRINT_FINALIZE_BYTES_AT_PIN)
        self.assertEqual(len(stats["files"]), FOOTPRINT_FINALIZE_FILES_AT_PIN)
        self.assertEqual(stats["missing"], [])

    def test_pass_rule_wording(self):
        self.assertIn("at least one drops and neither grows", self.doc)
        self.assertIn("There is no percentage target", self.doc)

    def test_mutant_total_plus_one(self):
        total = self.record["totals"]["model_run_steps"]
        old = "| Model-run mechanical steps | %d |" % total
        self.assertIn(old, self.doc)
        mutant = self.doc.replace(old, "| Model-run mechanical steps | %d |" % (total + 1))
        self.assertNotEqual(mutant, self.doc)
        self.assertNotEqual(self._check(mutant), [])

    def test_mutant_missing_situation(self):
        self.assertIn("`one-rebuild`", self.doc)
        mutant = self.doc.replace("`one-rebuild`", "`one-retry`")
        self.assertNotEqual(self._check(mutant), [])

    def test_mutant_heading_renamed(self):
        self.assertIn("## Counting rule\n", self.doc)
        mutant = self.doc.replace("## Counting rule\n", "## Counting\n")
        self.assertNotEqual(self._check(mutant), [])


class TestCli(unittest.TestCase):
    def _run(self, *argv):
        return subprocess.run([sys.executable, STEP_COUNT_PY, *argv],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=120)

    def test_json_is_deterministic(self):
        a = self._run("--repo", REPO_ROOT, "--rev", BASELINE_COMMIT, "--json")
        b = self._run("--repo", REPO_ROOT, "--rev", BASELINE_COMMIT, "--json")
        self.assertEqual(a.returncode, 0, a.stderr)
        self.assertEqual(a.stdout, b.stdout)
        self.assertEqual(len(json.loads(a.stdout)["files"]), 7)

    def test_unknown_revision_exit_2(self):
        p = self._run("--repo", REPO_ROOT, "--rev", "0" * 40, "--json")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertIn("commands/review.md", p.stderr)

    def test_missing_file_exit_2(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        for rel in _finalize_paths():
            if rel == FINALIZE_MD:
                continue
            dest = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write("x\n")
        p = self._run("--repo", REPO_ROOT, "--root", tmp, "--json")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertIn(FINALIZE_MD, p.stderr)


class TestImportSet(unittest.TestCase):
    def _tree(self):
        with open(STEP_COUNT_PY, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_module_level_imports(self):
        names = set()
        for node in self._tree().body:
            if isinstance(node, ast.Import):
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module)
        allowed = {"argparse", "json", "os", "re", "subprocess", "sys"}
        self.assertTrue(names <= allowed, names)

    def test_every_subprocess_run_has_an_explicit_timeout(self):
        calls = 0
        for node in ast.walk(self._tree()):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "run"
                    and getattr(node.func.value, "id", None) == "subprocess"):
                calls += 1
                self.assertIn("timeout", [kw.arg for kw in node.keywords],
                              "every subprocess.run needs an explicit timeout")
        self.assertGreater(calls, 0, "expected at least one subprocess.run")

    def test_no_copy_of_the_finalize_file_list(self):
        with open(STEP_COUNT_PY, encoding="utf-8") as fh:
            self.assertNotIn("90-finalize.md", fh.read())


if __name__ == "__main__":
    unittest.main()
