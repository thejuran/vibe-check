"""Executable lock on Phase 0's `$SCOPE_ARGS` normalizer (BATCH-01 Close out).

The fix-loop card's "Close out" re-enters the command with
`$ARGUMENTS = "${original_args} --finalize"` (phases/review/50-fix-loop.md),
and a user may type `/review [<phase>] --finalize`. The command spines trigger
Finalize from raw `$ARGUMENTS`, but Phase 0 derives the scope from
`$SCOPE_ARGS`. If `--finalize` survives into `$SCOPE_ARGS`, a GSD phase pass
fails the sandbox ("Invalid phase id") and a default-diff pass becomes a phase
lookup ("Phase not found"). See `.planning/v2.11-MILESTONE-AUDIT.md` (BATCH-01).

This module runs the REAL normalizer fence from phases/review/00-scope.md under
/bin/bash and /bin/zsh and pins:
  * `<args> --finalize` and `--finalize <args>` resolve the same `$SCOPE_ARGS`
    as `<args>` (Close out resolves the scope of the pass it closes);
  * the strip is whole-token only (`foo--finalize`, `path/--finalize` survive);
  * every invocation without `--finalize` is unchanged;
  * the spines' finalize trigger and the fix loop's re-entry string still exist.
Mutants prove each lock can fail.

The fence and the sandbox regex are extracted from 00-scope.md, never retyped.
"""

import os
import re
import subprocess
import unittest

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPE = os.path.join(PLUGIN_DIR, "phases", "review", "00-scope.md")
STATE = os.path.join(PLUGIN_DIR, "phases", "review", "05-state.md")
SPINES = [
    os.path.join(PLUGIN_DIR, "commands", "review.md"),
    os.path.join(PLUGIN_DIR, "commands", "deep-review.md"),
]
FIX_LOOP = os.path.join(PLUGIN_DIR, "phases", "review", "50-fix-loop.md")

FENCE = re.compile(r"```bash\n(.*?)```", re.S)
NEEDLE = "SCOPE_ARGS=$(printf '%s' \"$ARGUMENTS\""
# The whole-token strip expression the normalizer carries; M2 targets it.
STRIP_EXPR = "s/ --finalize( --finalize)* / /g"

TRIGGER = "Runs iff `$ARGUMENTS` contains `--finalize`"
REENTRY = "${original_args} --finalize"

SHELLS = ["/bin/bash"] + (["/bin/zsh"] if os.path.exists("/bin/zsh") else [])

R1_INPUT = "49-measure-release-2-11-0 --finalize"
R1_EXPECTED = "49-measure-release-2-11-0"

FINALIZE_CASES = [
    # R1
    (R1_INPUT, R1_EXPECTED),
    # R2
    ("--finalize", ""),
    ("--finalize --finalize", ""),
    ("--finalize --min-confidence=40", ""),
    # R3
    ("--all --finalize", "--all"),
    ("--finalize --all", "--all"),
    ("--all src --finalize", "--all src"),
    ("all --finalize", "all"),
    ("--finalize 49", "49"),
    # flag combos
    ("49-x --codex off --finalize", "49-x"),
    ("a --finalize --finalize b", "a b"),
    ("\t--finalize\t49 ", "49"),
]

WHOLE_TOKEN_NEGATIVES = [
    "foo--finalize",
    "--finalize-x",
    "--finalizex 49",
    "path/--finalize",
    "49 --finalize=1",
]

REGRESSION_CASES = [
    ("", ""),
    ("49", "49"),
    ("--codex off", ""),
    ("33 --codex off", "33"),
    ("--all --min-confidence 75", "--all"),
    ("--all src --codex=on", "--all src"),
    ("--all --full --fix --include-docs", "--all --full --fix --include-docs"),
    ("a..b", "a..b"),
    ("42", "42"),
]

INVARIANCE_BASES = ["", "49-foo", "01", "42", "--all", "--all src", "all",
                    "a..b", "--codex off", "--min-confidence 75", "--all --full"]


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def normalizer_block(text):
    hits = [b for b in FENCE.findall(text) if NEEDLE in b]
    assert len(hits) == 1, (
        "expected exactly one normalizer fence in 00-scope.md, found %d" % len(hits))
    return hits[0]


def sandbox_regex(text):
    m = re.search(r"does not match `([^`]+)`", text)
    assert m, "GSD sandbox sentence ('does not match `<regex>`') not found in 00-scope.md"
    pattern = m.group(1)
    assert pattern.startswith("^") and pattern.endswith("$"), pattern
    return re.compile(pattern)


def scope_args(block, arguments, shell="/bin/bash"):
    flags = ["-f"] if shell.endswith("zsh") else []
    proc = subprocess.run(
        [shell, *flags, "-c", block + '\nprintf "%s" "$SCOPE_ARGS"\n'],
        env=dict(os.environ, ARGUMENTS=arguments),
        capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def finalize_trigger_present(text):
    return TRIGGER in text


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read(SCOPE)
        cls.block = normalizer_block(cls.text)

    def check_table(self, cases):
        for shell in SHELLS:
            for arguments, expected in cases:
                with self.subTest(shell=shell, arguments=arguments):
                    self.assertEqual(scope_args(self.block, arguments, shell), expected)


class TestFinalizeStrip(_Base):
    def test_finalize_table(self):
        self.check_table(FINALIZE_CASES)

    def test_r1_passes_gsd_sandbox(self):
        sandbox = sandbox_regex(self.text)
        for shell in SHELLS:
            with self.subTest(shell=shell):
                out = scope_args(self.block, R1_INPUT, shell)
                self.assertEqual(out, R1_EXPECTED)
                self.assertTrue(sandbox.fullmatch(out), out)

    def test_r2_bare_finalize_is_default_diff(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                self.assertEqual(scope_args(self.block, "--finalize", shell), "")


class TestWholeToken(_Base):
    def test_negatives_unchanged(self):
        self.check_table([(x, x) for x in WHOLE_TOKEN_NEGATIVES])

    def test_path_finalize_still_rejected_by_sandbox(self):
        sandbox = sandbox_regex(self.text)
        out = scope_args(self.block, "path/--finalize")
        self.assertIsNone(sandbox.fullmatch(out))


class TestRegression(_Base):
    def test_no_finalize_shapes_unchanged(self):
        self.check_table(REGRESSION_CASES)


class TestInvariance(_Base):
    def test_finalize_suffix_and_prefix_are_neutral(self):
        for shell in SHELLS:
            for base in INVARIANCE_BASES:
                want = scope_args(self.block, base, shell)
                for arguments in ((base + " --finalize").strip(),
                                  ("--finalize " + base).strip()):
                    with self.subTest(shell=shell, arguments=arguments):
                        self.assertEqual(scope_args(self.block, arguments, shell), want)


@unittest.skipUnless(len(SHELLS) == 2, "/bin/zsh not present")
class TestShellParity(_Base):
    def test_bash_equals_zsh(self):
        inputs = ([a for a, _ in FINALIZE_CASES] + WHOLE_TOKEN_NEGATIVES
                  + [a for a, _ in REGRESSION_CASES])
        for arguments in inputs:
            with self.subTest(arguments=arguments):
                self.assertEqual(scope_args(self.block, arguments, "/bin/bash"),
                                 scope_args(self.block, arguments, "/bin/zsh"))


class TestMutants(_Base):
    def test_m1_strip_neutralized_breaks_r1_and_r2(self):
        mutant = self.block.replace("--finalize", "--no-such-flag")
        self.assertNotEqual(mutant, self.block, "M1 is vacuous: no --finalize in the fence")
        self.assertNotEqual(scope_args(mutant, R1_INPUT), R1_EXPECTED)
        self.assertNotEqual(scope_args(mutant, "--finalize"), "")

    def test_m2_unanchored_strip_breaks_whole_token(self):
        self.assertIn(STRIP_EXPR, self.block)
        mutant = self.block.replace(STRIP_EXPR, "s/--finalize//g")
        self.assertNotEqual(mutant, self.block)
        self.assertNotEqual(scope_args(mutant, "foo--finalize"), "foo--finalize")


class TestBoundary(unittest.TestCase):
    def test_spines_keep_finalize_trigger(self):
        for spine in SPINES:
            with self.subTest(spine=os.path.basename(spine)):
                self.assertTrue(finalize_trigger_present(read(spine)))

    def test_fix_loop_reenters_with_finalize(self):
        self.assertIn(REENTRY, read(FIX_LOOP))

    def test_trigger_lock_mutant(self):
        text = read(SPINES[0])
        self.assertIn(TRIGGER, text)
        mutant = text.replace(TRIGGER, "Runs when finalizing")
        self.assertFalse(finalize_trigger_present(mutant))


if __name__ == "__main__":
    unittest.main()
