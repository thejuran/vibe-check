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
