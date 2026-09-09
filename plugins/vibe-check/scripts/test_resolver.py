"""Tests for the TRUST-01 trusted-root helper resolver (Phase 40, plan 40-02).

The threat: before TRUST-01, review.md and fix.md resolved score.py / guard.py /
config.py by looking under the REVIEWED REPO first
(`$(git rev-parse --show-toplevel)/plugins/vibe-check/scripts/...`). A reviewed
diff that plants those paths got its own code executed by the orchestrator, and
a planted guard.py neutralized the fix agent's traversal guard.

TRUST-01 replaces all four copies with ONE resolver whose arms are
  (1) the load-time-substituted plugin root — delivered to the orchestrator body
      by the SEAT line in a loader-processed command file, and spelled directly
      in the loader-processed fix-agent twin,
  (2) the single owner-exported `VIBE_CHECK_PLUGIN_ROOT`,
  (3) a per-consumer terminal arm (D-13: guard/score FAIL CLOSED, config DEGRADES).

There is no repo-relative arm and no cache-glob / marketplace arm.

Two kinds of test live here:
  * STATIC — scan the prose corpus (commands/*.md, agents/*.md, phases/**/*.md)
    for the resolver's exact text and for the strings that must never reappear.
    The corpus is GLOBBED, never keyed on `commands/review.md`, so plan 40-08's
    relocation of the body to `phases/shared/01-bootstrap.md` needs no edit here.
  * DYNAMIC — extract the resolver text from the prose, run it under real bash
    with cwd inside a PLANTED repo whose `plugins/vibe-check/scripts/*.py` each
    drop a `.canary` file, and assert no canary ever appears.
"""

import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(SCRIPTS_DIR)
COMMANDS_DIR = os.path.join(PLUGIN_ROOT, "commands")
AGENTS_DIR = os.path.join(PLUGIN_ROOT, "agents")
PHASES_DIR = os.path.join(PLUGIN_ROOT, "phases")

FIX_MD = os.path.join(AGENTS_DIR, "fix.md")

# --- the exact texts the prose must carry -------------------------------- #

BLOCK_OPEN = "# TRUST-01 resolver"
BLOCK_CLOSE = "# /TRUST-01 resolver"
TWIN_MARKER = "(fix agent twin)"

SEAT_LINE = 'export VIBE_CHECK_PLUGIN_ROOT_SUBST="${CLAUDE_PLUGIN_ROOT}"'

# The orchestrator BODY's two arms. Arm (1) reads the value the SEAT exported —
# the body's bytes arrive through `Read`, which is NOT loader-processed, so the
# body must never spell the token itself (A1/D-14).
BODY_ARM_1 = 'VC_ROOT="${VIBE_CHECK_PLUGIN_ROOT_SUBST:-}"'
BODY_ARM_2 = '[ -z "$VC_ROOT" ] && VC_ROOT="${VIBE_CHECK_PLUGIN_ROOT:-}"'

# The fix-agent TWIN's two arms. `agents/*.md` IS loader-processed and the agent
# is a separate process that does not inherit the orchestrator's shell, so the
# twin spells the token DIRECTLY and gets no seat. Arm (1) is deliberately NOT
# byte-identical to the body's (A1) — these are two separate expectations.
TWIN_ARM_1 = 'VC_ROOT="${CLAUDE_PLUGIN_ROOT}"'
TWIN_ARM_2 = '[ -z "$VC_ROOT" ] && VC_ROOT="${VIBE_CHECK_PLUGIN_ROOT:-}"'

EXACT_TOKEN = "${CLAUDE_PLUGIN_ROOT}"
SUBST_VAR = "VIBE_CHECK_PLUGIN_ROOT_SUBST"

# Repo-first / marketplace resolution strings that must not survive anywhere in
# the prose corpus. (deep-review.md's `cache/openai-codex` and
# `marketplaces/openai-codex` lines resolve a DIFFERENT plugin and are NOT here.)
FORBIDDEN_STRINGS = (
    "plugins/vibe-check/scripts",
    "cache/thejuran",
    "marketplaces/thejuran",
)

# The unbraced form is NOT substituted by the loader (D-14), so a resolver that
# spelled it would silently resolve to empty.
UNBRACED_TOKEN_RE = re.compile(r"\$CLAUDE_PLUGIN_ROOT(?!\})")
# Likewise the bash-default form is NOT substituted.
DEFAULT_FORM_TOKEN = "${CLAUDE_PLUGIN_ROOT:-"

HALT_TEXT = "scoring cannot run, review HALTED"

_BLOCK_RE = re.compile(
    re.escape(BLOCK_OPEN) + r"(?P<body>.*?)" + re.escape(BLOCK_CLOSE),
    re.DOTALL,
)


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _resolver_blocks(text):
    """Every resolver block in `text`, marker lines included."""
    return [BLOCK_OPEN + m.group("body") + BLOCK_CLOSE
            for m in _BLOCK_RE.finditer(text)]


def _is_twin(block):
    """A twin carries the fix-agent marker on its opening comment line."""
    return TWIN_MARKER in block.split("\n", 1)[0]


def _prose_files(subdir):
    if subdir == "phases":
        return sorted(glob.glob(os.path.join(PHASES_DIR, "**", "*.md"),
                                recursive=True))
    return sorted(glob.glob(os.path.join(
        COMMANDS_DIR if subdir == "commands" else AGENTS_DIR, "*.md")))


def _all_prose_files():
    """commands/*.md UNION agents/*.md UNION phases/**/*.md.

    The phases glob is EMPTY until plan 40-08 creates the tree; assertions over
    it are vacuously true until then and load-bearing afterwards.
    """
    return _prose_files("commands") + _prose_files("agents") + _prose_files("phases")


def _corpus():
    return [(p, _read(p)) for p in _all_prose_files()]


def _all_blocks():
    """(path, block) for every resolver block across the whole corpus."""
    out = []
    for path, text in _corpus():
        for block in _resolver_blocks(text):
            out.append((path, block))
    return out


def _bodies():
    return [(p, b) for p, b in _all_blocks() if not _is_twin(b)]


def _twins():
    return [(p, b) for p, b in _all_blocks() if _is_twin(b)]


def _seat_files():
    """commands/*.md files that carry a seat line, with their occurrence count."""
    out = []
    for path in _prose_files("commands"):
        n = _read(path).count(SEAT_LINE)
        if n:
            out.append((path, n))
    return out


def _assert_lines_in_order(case, block, first, second, label):
    case.assertIn(first, block, "%s: missing arm (1) %r" % (label, first))
    case.assertIn(second, block, "%s: missing arm (2) %r" % (label, second))
    case.assertLess(block.index(first), block.index(second),
                    "%s: arm (1) must precede arm (2)" % label)


# ======================================================================== #
# STATIC
# ======================================================================== #


class TestResolverBlockOnce(unittest.TestCase):
    """The resolver TEXT exists exactly once — wherever it lives (F1).

    Deliberately location-independent: 40-08 moves the body from
    `commands/review.md` to `phases/shared/01-bootstrap.md` and these
    assertions must survive that move unedited.
    """

    def test_exactly_one_orchestrator_body_in_corpus(self):
        bodies = _bodies()
        self.assertEqual(
            len(bodies), 1,
            "expected exactly ONE orchestrator resolver body across the corpus, "
            "found %d: %s" % (len(bodies), [p for p, _ in bodies]))

    def test_exactly_one_fix_agent_twin_and_it_lives_in_fix_md(self):
        twins = _twins()
        self.assertEqual(
            len(twins), 1,
            "expected exactly ONE fix-agent twin, found %d: %s"
            % (len(twins), [p for p, _ in twins]))
        self.assertEqual(os.path.abspath(twins[0][0]), os.path.abspath(FIX_MD))

    def test_body_carries_its_two_arms_in_order(self):
        _, block = _bodies()[0]
        _assert_lines_in_order(self, block, BODY_ARM_1, BODY_ARM_2, "body")

    def test_twin_carries_its_own_two_arms_in_order(self):
        # SEPARATE expectation from the body's (A1): the twin is loader-processed
        # and seatless, so its arm (1) spells the token directly.
        _, block = _twins()[0]
        _assert_lines_in_order(self, block, TWIN_ARM_1, TWIN_ARM_2, "twin")

    def test_body_never_spells_the_token(self):
        # The body's bytes arrive via `Read`, which performs no substitution.
        _, block = _bodies()[0]
        self.assertNotIn(EXACT_TOKEN, block)


class TestNoRepoFirstArms(unittest.TestCase):
    """The reviewed repo is never a resolution source (TRUST-01, D-12)."""

    def test_forbidden_strings_absent_from_whole_corpus(self):
        for path, text in _corpus():
            for needle in FORBIDDEN_STRINGS:
                with self.subTest(path=os.path.basename(path), needle=needle):
                    self.assertNotIn(
                        needle, text,
                        "%s still contains the repo-first/marketplace string %r"
                        % (path, needle))

    def test_no_repo_root_derived_plugin_path(self):
        pattern = re.compile(r"show-toplevel.*plugins/vibe-check", re.DOTALL)
        for path, text in _corpus():
            with self.subTest(path=os.path.basename(path)):
                for line in text.split("\n"):
                    self.assertIsNone(
                        pattern.search(line),
                        "%s derives a plugin path from the reviewed repo root" % path)

    def test_no_cache_glob_in_resolver_blocks(self):
        for path, block in _all_blocks():
            with self.subTest(path=os.path.basename(path)):
                self.assertNotIn("sort -V", block)
                self.assertNotIn("rev-parse --show-toplevel", block.replace(
                    "GREPO=$(git rev-parse --show-toplevel 2>/dev/null)", ""))


class TestExactTokenForm(unittest.TestCase):
    """Only the exact braced token is loader-substituted (D-14)."""

    def test_unbraced_form_absent(self):
        for path, text in _corpus():
            with self.subTest(path=os.path.basename(path)):
                self.assertIsNone(
                    UNBRACED_TOKEN_RE.search(text),
                    "%s spells the UNBRACED token, which is never substituted" % path)

    def test_bash_default_form_absent(self):
        for path, text in _corpus():
            with self.subTest(path=os.path.basename(path)):
                self.assertNotIn(
                    DEFAULT_FORM_TOKEN, text,
                    "%s spells the bash-default token form, never substituted" % path)

    def test_token_only_in_loader_processed_files(self):
        # F2: `Read` returns bytes and nothing processes them, so a token under
        # phases/ would be dead text. Vacuous until 40-08, load-bearing after.
        for path in _prose_files("phases"):
            with self.subTest(path=os.path.relpath(path, PLUGIN_ROOT)):
                self.assertNotIn(
                    EXACT_TOKEN, _read(path),
                    "%s is Read-loaded, so the token would never be substituted" % path)


class TestSeatInvariant(unittest.TestCase):
    """The SEAT is the only place the token may appear on the orchestrator path (A1)."""

    def test_seated_command_files_carry_exactly_one_seat(self):
        # Conditioned on "contains a seat", NOT on "reaches a helper consumer"
        # (A3): commands/deep-review.md is a consumer from wave 1 but is not
        # seated until 40-11, so the consumer-based spelling would make this
        # suite RED in its own wave. The universal form is 40-11's criterion;
        # until then a seatless consumer is covered by the no-orphaned-body test.
        seated = _seat_files()
        self.assertTrue(seated, "no commands/*.md carries the TRUST-01 seat line")
        for path, count in seated:
            with self.subTest(path=os.path.basename(path)):
                self.assertEqual(count, 1,
                                 "%s carries %d seat lines, expected exactly 1"
                                 % (path, count))

    def test_every_token_in_commands_is_a_seat_or_a_read_path(self):
        for path in _prose_files("commands"):
            for lineno, line in enumerate(_read(path).split("\n"), 1):
                if EXACT_TOKEN not in line:
                    continue
                with self.subTest(path=os.path.basename(path), line=lineno):
                    self.assertTrue(
                        line.strip() == SEAT_LINE or "Read" in line,
                        "%s:%d spells the token outside a seat line or a Read "
                        "path instruction: %r" % (path, lineno, line.strip()))

    def test_agents_carry_no_seat_and_no_subst_var(self):
        # The agent is a separate process; it neither inherits nor may appear to
        # inherit the orchestrator's exported value.
        for path in _prose_files("agents"):
            with self.subTest(path=os.path.basename(path)):
                text = _read(path)
                self.assertNotIn(SEAT_LINE, text)
                self.assertNotIn(SUBST_VAR, text)

    def test_no_orphaned_body(self):
        # A body with no seat resolves empty on arm (1) and would silently take
        # every terminal arm. That must be a test failure, not a fail-closed run.
        if _bodies():
            self.assertTrue(
                _seat_files(),
                "a resolver body exists but no commands/*.md carries the seat line")


class TestTerminalArmsPerConsumer(unittest.TestCase):
    """D-13's deliberate inversion survives: score/guard fail closed, config degrades."""

    REVIEW_MD = os.path.join(COMMANDS_DIR, "review.md")

    def test_score_consumer_fails_closed_with_the_exact_halt_text(self):
        self.assertIn(HALT_TEXT, _read(self.REVIEW_MD))

    def test_config_consumer_documents_its_degrade_posture(self):
        self.assertIn("Do NOT \"fix\" this terminal arm back to fail-closed",
                      _read(self.REVIEW_MD).replace("'", '"'))

    def test_guard_callers_still_branch_on_the_exit_code(self):
        self.assertIn("EXIT CODE", _read(self.REVIEW_MD))
        self.assertIn("EXIT CODE", _read(FIX_MD))

    def test_resolver_body_itself_never_exits(self):
        # The block binds; the CONSUMER sites own the exit/degrade decision.
        _, block = _bodies()[0]
        for line in block.split("\n"):
            self.assertNotIn("exit 1", line)


class TestFixAgentOrdering(unittest.TestCase):
    """TRUST-02: a prose edit must not move validation back behind the first disk touch.

    D-15 requires THREE gates in `agents/fix.md`, and their ORDER is the whole
    requirement:

      1. step 0 validates every path known at dispatch — BEFORE the first `Read`;
      2. a sibling discovered while designing the fix is validated before it is
         **READ**, not merely before it is edited (F6: the earlier wording gated
         only the `Edit`, so a traversal path introduced as a "sibling" was still
         READ first — which is exactly what TRUST-02 forbids);
      3. the pre-commit gate re-validates the COMPLETE set at step 6 (D-15 moves
         validation AHEAD of step 1; it does not relocate it).

    Every gate must also fail CLOSED by CONTROL FLOW. `|| { : ...; }` does not:
    the shell no-op builtin SUCCEEDS, so execution falls through into `git add`
    and `git commit` after a rejection (reproduced as AFTER_REJECT_REACHED). The
    scan below forbids that literal across the whole prose corpus.
    """

    # Anchored on the numbered HEADING, not the bare words "step 0": the
    # tool-use sentence in the file's header also says "step 0", so an index
    # compare on that substring would pass no matter where the gate actually
    # sits (caught by mutation-testing this very class).
    STEP0 = "0. **Validate every path — BEFORE you read or write anything.**"
    FIRST_READ = "**Read the file.**"
    FALL_THROUGH = "|| { : "

    def setUp(self):
        self.text = _read(FIX_MD)

    # -- gate 1: validation precedes the first disk touch ------------------ #

    def test_step_0_block_precedes_the_first_read_instruction(self):
        self.assertIn(self.STEP0, self.text)
        self.assertIn(self.FIRST_READ, self.text)
        self.assertLess(
            self.text.index(self.STEP0), self.text.index(self.FIRST_READ),
            "step 0 must precede the first Read instruction (TRUST-02, D-15)")

    def test_step_0_is_a_numbered_procedure_step_before_step_1(self):
        proc = self.text.index("## Procedure")
        step0 = self.text.index("\n0. ", proc)
        step1 = self.text.index("\n1. ", proc)
        self.assertLess(step0, step1, "step 0. must be numbered before step 1.")

    def test_prose_states_nothing_is_touched_before_the_gate(self):
        self.assertIn("Nothing is read and nothing is written until this passes",
                      self.text)

    # -- gate 2: the sibling is validated before its READ (F6) ------------- #

    def test_sibling_rule_names_read_before_edit(self):
        """The F6 lock. The instruction must gate the READ, not just the Edit.

        Mutating the sentence to the old Edit-only phrasing must fail HERE.
        """
        sentence = ("A sibling discovered while designing the fix (step 3/4) is "
                    "validated by this SAME gate **BEFORE you READ it**")
        self.assertIn(sentence, self.text,
                      "the sibling rule must gate the sibling's READ (F6)")
        idx = self.text.index(sentence)
        window = self.text[idx:idx + 400]
        self.assertLess(
            window.index("READ"), window.index("edited"),
            "the sibling rule must name READ before it names editing (F6)")
        self.assertIn("never read and never edited unvalidated", self.text)

    def test_sibling_gate_bash_permits_the_read_only_on_success(self):
        gate = self.text.index("<sibling-path>")
        window = self.text[gate:gate + 500]
        self.assertIn("may now be READ", window)
        self.assertIn("the sibling was not read", window)
        self.assertIn("Do not read the sibling", window)

    def test_old_edit_only_sibling_phrasing_is_absent(self):
        for stale in ("before it is edited", "before its Edit",
                      "validated before the Edit"):
            with self.subTest(phrase=stale):
                self.assertNotIn(stale, self.text)

    # -- gate 3: the pre-commit gate survives ------------------------------ #

    def test_all_three_gates_reference_the_guard_or_its_owner(self):
        """Three gates, none removed — counted by INVOCATION, not by mention.

        Counting occurrences of the string `guard.py` is decorative: the prose
        names it many times, so deleting the entire sibling gate left the count
        unchanged (proved by mutation-testing this class). Count the executable
        gate calls instead.
        """
        guard_calls = self.text.count('python3 "$GUARD_PY" --root "$GREPO"')
        self.assertEqual(
            guard_calls, 2,
            "expected TWO guard.py gate invocations (step 0 + the sibling gate), "
            "found %d" % guard_calls)
        fixcommit_calls = self.text.count(
            'python3 "$VC_ROOT/scripts/fixcommit.py"')
        self.assertEqual(fixcommit_calls, 1,
                         "expected the step-6 gate to invoke fixcommit.py once")
        self.assertIn("validated a SECOND time", self.text)

    def test_step_6_gate_follows_the_first_read(self):
        # Scoped to the INVOCATION, not to the first mention: the tool-use
        # sentence at the head of the file names `fixcommit.py` too, and that
        # mention legitimately precedes step 1.
        invocation = self.text.index('--finding-json "$findingfile"')
        self.assertLess(self.text.index(self.FIRST_READ), invocation,
                        "the pre-commit gate is the SECOND gate, not the first")
        self.assertLess(self.text.index(self.STEP0), invocation,
                        "step 0 is the FIRST gate")

    def test_retained_commit_mechanics(self):
        for needle in ("EXIT CODE", "--cleanup=verbatim", '-F "$msgfile"',
                       "trap 'rm -f", "Never use `--no-verify`",
                       "End-of-options `--`"):
            with self.subTest(needle=needle):
                self.assertIn(needle, self.text)

    def test_hard_rules_one_through_five_survive(self):
        rules = self.text[self.text.index("## Hard rules"):]
        for n in range(1, 6):
            with self.subTest(rule=n):
                self.assertIn("\n%d. **" % n, rules)

    # -- FL-03 (R4): no attacker-influenced value on a command line -------- #

    def test_title_is_not_interpolated_into_a_shell_command(self):
        """FL-03: the shell expands a command line before the helper runs.

        `--title "<finding.title>"` let a command-substitution title execute at
        expansion time. Reproduced. The title now travels as serialized JSON.
        """
        self.assertNotIn('--title "<finding.title>"', self.text)
        self.assertNotIn("--title", self.text)
        self.assertIn("--finding-json", self.text)
        self.assertIn("Never put a finding's title or paths on a command line",
                      self.text)

    def test_printf_title_substitution_site_is_gone(self):
        # The old construction site: printf 'fix(review-pass-%s): %s\n' ... "<finding.title>"
        self.assertNotIn("printf 'fix(review-pass-", self.text)

    # -- F5: no fall-through gate anywhere in the prose corpus ------------- #

    def test_no_fall_through_gate_in_fix_md(self):
        self.assertNotIn(self.FALL_THROUGH, self.text,
                         "a successful-no-op gate lets a rejection fall through "
                         "into git add / git commit (F5)")

    def test_no_fall_through_gate_anywhere_in_the_corpus(self):
        for path, text in _corpus():
            with self.subTest(path=os.path.relpath(path, PLUGIN_ROOT)):
                self.assertNotIn(
                    self.FALL_THROUGH, text,
                    "%s carries a successful-no-op gate; a rejection there falls "
                    "through into the guarded side effect (F5)" % path)

    def test_the_git_calls_are_inside_the_success_branch(self):
        start = self.text.index("--finding-json \"$findingfile\"")
        window = self.text[start:start + 1800]
        self.assertIn("; then", window)
        else_idx = window.index("\n   else")
        for call in ("git add --", "git commit --cleanup=verbatim"):
            with self.subTest(call=call):
                self.assertIn(call, window)
                self.assertLess(window.index(call), else_idx,
                                "%s must sit in the success branch, above else" % call)
        self.assertIn("NOTHING is staged and NOTHING is committed",
                      window[else_idx:])

    # -- the tool-use sentence names both trusted scripts ------------------ #

    def test_tool_sentence_names_both_trusted_scripts(self):
        head = self.text[:self.text.index("## Procedure")]
        self.assertIn("`guard.py` at step 0", head)
        self.assertIn("`fixcommit.py` at step 6", head)
        self.assertNotIn("in the commit step (nothing else", head)


# ======================================================================== #
# DYNAMIC — the planted-canary proof
# ======================================================================== #


class TestPlantedCanary(unittest.TestCase):
    """Run the REAL resolver text under bash inside a repo that plants helpers.

    If any arm ever resolves repo-first, the planted script is bound and the
    subsequent invocation drops a `.canary` file. No case may produce one.
    """

    PLANTED = "canary-planted"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = self._tmp.name

        # --- the TRUSTED root: the real helpers -------------------------- #
        self.trusted = os.path.join(base, "trusted")
        os.makedirs(os.path.join(self.trusted, "scripts"))
        for name in ("guard.py", "config.py", "score.py"):
            shutil.copy(os.path.join(SCRIPTS_DIR, name),
                        os.path.join(self.trusted, "scripts", name))

        # --- the PLANTED repo: a reviewed repo carrying an attack --------- #
        self.planted = os.path.join(base, "planted")
        planted_scripts = os.path.join(
            self.planted, "plugins", "vibe-check", "scripts")
        os.makedirs(planted_scripts)
        self.canary = os.path.join(self.planted, ".canary")
        for name in ("guard.py", "config.py", "score.py"):
            with open(os.path.join(planted_scripts, name), "w") as fh:
                fh.write(
                    "import os, sys\n"
                    "open(os.path.join(os.path.dirname(os.path.abspath(__file__)),\n"
                    "     '..', '..', '..', '.canary'), 'a').write('%s\\n')\n"
                    "sys.exit(0)\n" % self.PLANTED)
        subprocess.run(["git", "init", "-q", self.planted],
                       check=True, timeout=30)
        subprocess.run(
            ["git", "-C", self.planted,
             "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-q", "--allow-empty", "-m", "base"],
            check=True, timeout=30)
        with open(os.path.join(self.planted, "README.md"), "w") as fh:
            fh.write("planted\n")

        self.body = _bodies()[0][1]
        self.planted_root = os.path.join(self.planted, "plugins", "vibe-check")

    def tearDown(self):
        self._tmp.cleanup()

    # -- helpers ---------------------------------------------------------- #

    def _render(self, block, seat=None, substitute_with=None):
        """Render runnable bash: optional SEAT line, then the resolver body.

        `substitute_with` stands in for the loader: the seat's exact token text
        is replaced by a concrete path, which is precisely what Claude Code does
        to a command body at load time (A1).
        """
        parts = []
        if seat is not None:
            if substitute_with is not None:
                seat = seat.replace(EXACT_TOKEN, substitute_with)
            parts.append(seat)
        parts.append(block)
        parts.append('printf \'%s\\n%s\\n%s\\n\' "$GUARD_PY" "$CONFIG_PY" "$SCORE_PY"')
        return "\n".join(parts) + "\n"

    def _run_block(self, rendered, env_overrides):
        env = {k: v for k, v in os.environ.items()
               if k not in ("CLAUDE_PLUGIN_ROOT", "VIBE_CHECK_PLUGIN_ROOT",
                            SUBST_VAR)}
        env.update(env_overrides)
        proc = subprocess.run(["bash", "-c", rendered], cwd=self.planted,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, env=env, timeout=30)
        lines = proc.stdout.split("\n")
        # exactly three printed lines (guard, config, score), possibly empty
        self.assertGreaterEqual(len(lines), 4, "block printed %r" % proc.stdout)
        return proc, lines[0], lines[1], lines[2]

    def _assert_no_canary(self):
        self.assertFalse(
            os.path.exists(self.canary),
            "a planted helper EXECUTED — canary file present")

    def _assert_all_under_trusted(self, guard_py, config_py, score_py):
        for label, value in (("guard", guard_py), ("config", config_py),
                             ("score", score_py)):
            with self.subTest(helper=label):
                self.assertTrue(
                    value.startswith(self.trusted + "/scripts/"),
                    "%s resolved to %r, outside the trusted root" % (label, value))
                self.assertNotIn(self.planted, value)

    # -- case (a): neither the seat's value nor the override -------------- #

    def test_case_a_no_seat_no_override_binds_nothing(self):
        rendered = self._render(self.body)
        proc, guard_py, config_py, score_py = self._run_block(rendered, {})
        self.assertEqual(proc.returncode, 0,
                         "the resolver block itself must never exit non-zero")
        self.assertEqual([guard_py, config_py, score_py], ["", "", ""])
        self._assert_no_canary()

    # -- case (b): owner override only ------------------------------------ #

    def test_case_b_owner_override_resolves_trusted(self):
        rendered = self._render(self.body)
        _, guard_py, config_py, score_py = self._run_block(
            rendered, {"VIBE_CHECK_PLUGIN_ROOT": self.trusted})
        self._assert_all_under_trusted(guard_py, config_py, score_py)
        self._assert_no_canary()

    def test_case_b_resolved_guard_runs_clean_against_the_planted_repo(self):
        rendered = self._render(self.body)
        _, guard_py, _, _ = self._run_block(
            rendered, {"VIBE_CHECK_PLUGIN_ROOT": self.trusted})
        proc = subprocess.run(
            [sys.executable, guard_py, "--root", self.planted,
             "--path", "README.md"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self._assert_no_canary()

    # -- case (c): install beats the override ----------------------------- #

    def test_case_c_seat_value_beats_a_planted_override(self):
        rendered = self._render(self.body)
        _, guard_py, config_py, score_py = self._run_block(rendered, {
            SUBST_VAR: self.trusted,
            "VIBE_CHECK_PLUGIN_ROOT": self.planted_root,
        })
        self._assert_all_under_trusted(guard_py, config_py, score_py)
        self._assert_no_canary()

    # -- case (c2): the SEAT composes with the body ----------------------- #

    def test_case_c2_seat_line_composes_with_the_body(self):
        rendered = self._render(self.body, seat=SEAT_LINE,
                                substitute_with=self.trusted)
        _, guard_py, config_py, score_py = self._run_block(
            rendered, {"VIBE_CHECK_PLUGIN_ROOT": self.planted_root})
        self._assert_all_under_trusted(guard_py, config_py, score_py)
        self._assert_no_canary()

    # -- case (c2b): the seat OVERWRITES a hostile inherited value --------- #

    def test_case_c2b_seat_overwrites_a_hostile_inherited_subst_var(self):
        # T-40-24c's ACTUAL test. Case (c2) starts from an UNSET variable, so on
        # its own it proves composition but never exercises the overwrite the
        # threat row depends on: an attacker who gets a value into the parent
        # environment must not survive the seat's assignment.
        rendered = self._render(self.body, seat=SEAT_LINE,
                                substitute_with=self.trusted)
        _, guard_py, config_py, score_py = self._run_block(rendered, {
            SUBST_VAR: self.planted_root,
            "VIBE_CHECK_PLUGIN_ROOT": self.planted_root,
        })
        self._assert_all_under_trusted(guard_py, config_py, score_py)
        self._assert_no_canary()

    # -- case (c3): an orphaned body degrades, never to a repo path -------- #

    def test_case_c3_orphaned_body_degrades_to_empty(self):
        rendered = self._render(self.body)  # no seat, no env
        proc, guard_py, config_py, score_py = self._run_block(rendered, {})
        self.assertEqual(proc.returncode, 0)
        self.assertEqual([guard_py, config_py, score_py], ["", "", ""])
        self._assert_no_canary()

    # -- case (d): the D-13 split lives at the CONSUMER sites ------------- #

    def test_case_d_terminal_arm_split_is_consumer_side(self):
        review = _read(os.path.join(COMMANDS_DIR, "review.md"))
        # score consumer HALTS
        self.assertIn(HALT_TEXT, review)
        halt_idx = review.index(HALT_TEXT)
        self.assertIn("exit 1", review[halt_idx - 400:halt_idx + 400],
                      "the score consumer site must carry the fail-closed exit")
        # the block itself never exits (proved dynamically in case (a) too)
        _, block = _bodies()[0]
        self.assertNotIn("exit 1", block)

    def test_case_d_config_consumer_site_carries_no_exit(self):
        # The prose around this site legitimately CITES $SCORE_PY's `exit 1` to
        # document the deliberate inversion, so the assertion is scoped to the
        # site's executable bash, not to the paragraph that describes it.
        review = _read(os.path.join(COMMANDS_DIR, "review.md"))
        idx = review.replace("'", '"').index(
            'Do NOT "fix" this terminal arm back to fail-closed')
        window = review[idx:idx + 1200]
        fences = re.findall(r"```bash\n(.*?)```", window, re.DOTALL)
        self.assertTrue(fences, "the config consumer site has no bash block")
        for fence in fences:
            code = "\n".join(line for line in fence.split("\n")
                             if not line.lstrip().startswith("#"))
            self.assertNotIn("exit 1", code,
                             "the config consumer degrades — it must not exit")

    # -- refusal outputs never echo the planted path ---------------------- #

    def test_refusal_output_never_names_the_planted_path(self):
        rendered = self._render(self.body)
        proc, _, _, _ = self._run_block(rendered, {})
        self.assertNotIn(self.planted, proc.stdout)
        self.assertNotIn(self.planted, proc.stderr)


if __name__ == "__main__":
    unittest.main()
