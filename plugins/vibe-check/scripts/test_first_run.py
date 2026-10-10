"""Executable lock on Phase 0.7's first-run gate (phases/review/07-first-run.md).

Phase 0.5 routes into Phase 0.7 whenever the CURRENT scope has no state file,
which happens on every new branch or GSD phase of a repo that already uses
vibe-check. The setup steps (mkdir, the .gitignore tip, the old-state migration
card) belong to the repo's first use only, so the whole file is gated on
`.turingmind/` existing at the repo top — not relative to the cwd.

This module:
  * runs the file's FIRST bash fence (the gate) under /bin/bash and /bin/zsh in a
    temp git repo, with and without `.turingmind/`, from the top and from a
    subdirectory;
  * locks the prose: the gate is the first fence, the FIRST_RUN=0 branch
    announces the skip with no tip and no card, and all three steps sit under
    the FIRST_RUN=1 branch;
  * mutates each lock to prove it can fail.
"""

import os
import re
import subprocess
import tempfile
import unittest

import gitfixture

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRST_RUN_MD = os.path.join(PLUGIN_DIR, "phases", "review", "07-first-run.md")

FENCE = re.compile(r"```bash\n(.*?)```", re.S)
ANY_FENCE = re.compile(r"```[A-Za-z0-9_-]*\n(.*?)```", re.S)
SHELLS = ["/bin/bash"] + (["/bin/zsh"] if os.path.exists("/bin/zsh") else [])

SKIP_LINE = "⊘ Phase 0.7 — First-run setup (skipped: .turingmind/ exists)"
BRANCH_SKIP = "**FIRST_RUN=0**"
BRANCH_RUN = "**FIRST_RUN=1**"
# One marker per setup step: mkdir, the .gitignore tip, the migration card.
STEP_MARKERS = [
    "mkdir -p",
    "Tip: add `.turingmind/` to your .gitignore",
    "Found old TuringMind state under `.gsd/`",
]
STEP3_HEAD = "3. Migration check"


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def gate_fence(text):
    fences = FENCE.findall(text)
    assert fences, "no bash fence in 07-first-run.md"
    return fences[0]


def run_gate(fence, cwd, shell):
    flags = ["-f"] if shell.endswith("zsh") else []
    proc = subprocess.run([shell, *flags, "-c", fence], cwd=cwd,
                          env=gitfixture.helper_env(), capture_output=True,
                          text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


# --------------------------------------------------------------------------- #
# locks
# --------------------------------------------------------------------------- #
def gate_fence_first_holds(text):
    fences = ANY_FENCE.findall(text)
    return bool(fences) and "FIRST_RUN=" in fences[0] and "git rev-parse --show-toplevel" in fences[0]


def skip_announce_holds(text):
    lines = [ln for ln in text.splitlines() if BRANCH_SKIP in ln]
    if len(lines) != 1:
        return False
    line = lines[0]
    return (SKIP_LINE in line and "no gitignore tip" in line
            and "no migration card" in line and "no AskUserQuestion" in line)


def steps_gated_holds(text):
    head = text.find(BRANCH_RUN)
    if head < 0 or text.count(BRANCH_RUN) != 1:
        return False
    before = text[:head]
    for marker in STEP_MARKERS:
        if marker in before or text.find(marker, head) < 0:
            return False
    return BRANCH_SKIP in before


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(FIRST_RUN_MD)


class TestGateFence(_Base):
    def _repo(self, tmp, with_state):
        repo = gitfixture.make_repo(tmp)
        os.makedirs(os.path.join(repo, "sub", "deeper"))
        if with_state:
            os.makedirs(os.path.join(repo, ".turingmind"))
        return repo

    def test_no_turingmind_is_first_run(self):
        fence = gate_fence(self.text)
        for shell in SHELLS:
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(tmp, with_state=False)
                self.assertEqual(run_gate(fence, repo, shell), "FIRST_RUN=1\n")

    def test_turingmind_present_is_not_first_run(self):
        fence = gate_fence(self.text)
        for shell in SHELLS:
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(tmp, with_state=True)
                self.assertEqual(run_gate(fence, repo, shell), "FIRST_RUN=0\n")

    def test_subdirectory_reads_repo_top(self):
        fence = gate_fence(self.text)
        for shell in SHELLS:
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(tmp, with_state=True)
                sub = os.path.join(repo, "sub", "deeper")
                self.assertFalse(os.path.exists(os.path.join(sub, ".turingmind")))
                self.assertEqual(run_gate(fence, sub, shell), "FIRST_RUN=0\n")

    def test_subdirectory_without_state_is_first_run(self):
        fence = gate_fence(self.text)
        for shell in SHELLS:
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(tmp, with_state=False)
                sub = os.path.join(repo, "sub")
                self.assertEqual(run_gate(fence, sub, shell), "FIRST_RUN=1\n")

    def test_cwd_relative_mutant_misreads_subdirectory(self):
        fence = gate_fence(self.text)
        self.assertIn('"$GREPO/.turingmind"', fence)
        mutant = fence.replace('"$GREPO/.turingmind"', ".turingmind")
        self.assertNotEqual(mutant, fence)
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp, with_state=True)
            sub = os.path.join(repo, "sub")
            self.assertEqual(run_gate(mutant, sub, "/bin/bash"), "FIRST_RUN=1\n")


class TestProseLocks(_Base):
    def test_gate_fence_is_first(self):
        self.assertTrue(gate_fence_first_holds(self.text))

    def test_skip_branch_announces_and_suppresses(self):
        self.assertTrue(skip_announce_holds(self.text))
        self.assertEqual(self.text.count(SKIP_LINE), 1)

    def test_steps_sit_under_first_run_branch(self):
        for marker in STEP_MARKERS:
            self.assertIn(marker, self.text)
        self.assertTrue(steps_gated_holds(self.text))

    def test_mkdir_uses_repo_top(self):
        self.assertIn('mkdir -p "$GREPO/.turingmind/state" "$GREPO/.turingmind/reviews"',
                      self.text)


class TestMutants(_Base):
    def test_reflattened_step3_fails_steps_gated(self):
        head = self.text.find(BRANCH_RUN)
        start = self.text.find(STEP3_HEAD)
        self.assertGreater(start, head)
        step3 = self.text[start:]
        mutant = self.text[:start].replace(BRANCH_RUN, step3 + "\n" + BRANCH_RUN, 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(steps_gated_holds(mutant))

    def test_deleted_skip_line_fails_skip_announce(self):
        mutant = self.text.replace(SKIP_LINE, "")
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(skip_announce_holds(mutant))

    def test_gate_moved_below_setup_fails_gate_first(self):
        fences = ANY_FENCE.findall(self.text)
        self.assertGreaterEqual(len(fences), 2)
        mutant = self.text.replace(fences[0], fences[1], 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(gate_fence_first_holds(mutant))


if __name__ == "__main__":
    unittest.main()
