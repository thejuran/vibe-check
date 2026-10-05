"""Prose pins for the review orchestrator's git-safety snapshot and gate.

Phase 1 (phases/review/10-triage.md) fingerprints the reviewed repo's git
state with `gitsnap.py take` and clears old block records with
`gitguard.py reset` in its own Bash call, before the triage Task. Phase 3
(phases/review/30-collect-score.md) compares against that snapshot before
step 0, renders the guard's block lines as message text, and halts the pass
on any change: no scoring, no render, no persist, no fix loop.

Every lock is a pure `..._holds(text) -> bool` function. Each has a test on
the real file and at least one mutant test proving the lock would trip.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.normpath(os.path.join(HERE, ".."))
TRIAGE = os.path.join(PLUGIN_DIR, "phases", "review", "10-triage.md")
COLLECT = os.path.join(PLUGIN_DIR, "phases", "review", "30-collect-score.md")
CONTRACT = os.path.join(PLUGIN_DIR, "phases", "shared", "00-contract.md")
SPINES = {
    "review": os.path.join(PLUGIN_DIR, "commands", "review.md"),
    "deep-review": os.path.join(PLUGIN_DIR, "commands", "deep-review.md"),
}

TAKE_CALL = 'gitsnap.py" take'
RESET_CALL = 'gitguard.py" reset'
COMPARE_CALL = 'gitsnap.py" compare'
NOTICES_CALL = 'gitguard.py" notices'
TRIAGE_DISPATCH = "Dispatch a single Task call to `triage` agent."
STEP0 = "0. **Raw-fact collection"
GATE_HEAD = "**Git-safety gate"
TAKE_HALT_ECHO = "review HALTED before any agent ran"
CODEX_JOIN = ("and, in `/deep-review`, after `30-codex-collect.md` has joined "
              "the Codex result")

HALT_PHRASES = ("do NOT score", "do NOT render findings",
                "do NOT run Phase 4.5", "do NOT enter the fix loop",
                "persist nothing")
HALT_WORDING = (
    "this pass is halted.",
    "This was either a review agent or you in another window — the snapshot "
    "cannot tell which.",
    "`git stash list`", "`git reflog -10`", "`git status`",
)
SCRATCH_PATHS = (".turingmind/git-guard/", ".turingmind/fixstage/",
                 ".turingmind/fixcheck/")

OPTIONAL_EXPANSION = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*:\+")
FENCE = re.compile(r"```bash\n(.*?)```", re.S)


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _fence_with(text, needle):
    """(start, end, body) of the first ```bash fence containing needle."""
    for m in FENCE.finditer(text):
        if needle in m.group(1):
            return m.start(), m.end(), m.group(1)
    return None


def _gate_section(text):
    """Text from the gate heading up to step 0 ('' when either is missing)."""
    start = text.find(GATE_HEAD)
    end = text.find(STEP0)
    if start < 0 or end < 0 or end < start:
        return ""
    return text[start:end]


def _skip_section(text):
    start = text.find("### Skip conditions")
    if start < 0:
        return ""
    nxt = re.search(r"\n#{2,3} ", text[start + 1:])
    return text[start:start + 1 + nxt.start()] if nxt else text[start:]


# --------------------------------------------------------------------------- #
# locks
# --------------------------------------------------------------------------- #
def take_precedes_triage_task_holds(text):
    fence = _fence_with(text, TAKE_CALL)
    dispatch = text.find(TRIAGE_DISPATCH)
    if fence is None or dispatch < 0:
        return False
    start, end, body = fence
    return (end <= dispatch and RESET_CALL in body and "Task" not in body
            and "its own Bash call, BEFORE the triage Task" in text[:start])


def take_failure_halts_holds(text):
    fence = _fence_with(text, TAKE_CALL)
    if fence is None:
        return False
    body = fence[2]
    else_part = body.split("else", 1)[1] if "else" in body else ""
    return (TAKE_HALT_ECHO in else_part
            and "STOP the review" in text[fence[1]:text.find(TRIAGE_DISPATCH)])


def take_once_per_pass_holds(text):
    head = text[:max(text.find(TRIAGE_DISPATCH), 0)]
    return ("take it ONCE, before the first chunk's triage" in head
            and "never once per chunk" in head)


def gate_precedes_step0_holds(text):
    step0 = text.find(STEP0)
    compare = text.find(COMPARE_CALL)
    notices = text.find(NOTICES_CALL)
    return step0 >= 0 and 0 <= compare < step0 and 0 <= notices < step0


def gate_after_codex_join_holds(text):
    gate = _gate_section(text)
    return "`30-codex-collect.md`" in gate and "has joined" in gate


def halt_skips_everything_holds(text):
    gate = _gate_section(text)
    return bool(gate) and all(p in gate for p in HALT_PHRASES)


def halt_wording_holds(text):
    gate = _gate_section(text)
    return bool(gate) and all(p in gate for p in HALT_WORDING)


def notices_copied_as_message_text_holds(text):
    gate = _gate_section(text)
    return "message text in this same turn" in gate


def uses_case_not_optional_expansion_holds(*texts):
    gate_fence = None
    for text in texts:
        if OPTIONAL_EXPANSION.search(text):
            return False
        gate_fence = gate_fence or _fence_with(text, COMPARE_CALL)
    if gate_fence is None:
        return False
    body = gate_fence[2]
    nonzero = [ln for ln in body.splitlines() if ln.strip().startswith("*)")]
    return ("; rc=$?" in body and 'case "$rc" in' in body
            and len(nonzero) == 1 and "--repo-changed" in nonzero[0]
            and "pass halted" in nonzero[0])


def contract_lists_scratch_paths_holds(text):
    return all(p in text for p in SCRATCH_PATHS)


def skip_section_untouched_holds(text):
    section = _skip_section(text)
    return bool(section) and not any(
        w in section for w in ("gitsnap", "gitguard", "git-safety"))


def spine_names_gates_holds(text):
    return ("its git-safety snapshot runs first, in its own turn" in text
            and "Its git-safety entry gate (after the Codex join in "
                "deep-review) can also halt the pass." in text)


# --------------------------------------------------------------------------- #
# tests
# --------------------------------------------------------------------------- #
class TestTriageSnapshot(unittest.TestCase):
    def setUp(self):
        self.text = _read(TRIAGE)

    # (1) take fence precedes the triage Task and dispatches nothing
    def test_take_precedes_triage_task(self):
        self.assertTrue(take_precedes_triage_task_holds(self.text))

    def test_mutant_take_moved_below_dispatch(self):
        start, end, _ = _fence_with(self.text, TAKE_CALL)
        fence = self.text[start:end]
        mutant = self.text[:start] + self.text[end:]
        mutant = mutant + "\n" + fence + "\n"
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(take_precedes_triage_task_holds(mutant))

    def test_mutant_task_dispatch_inside_fence(self):
        mutant = self.text.replace(
            'echo "git-safety snapshot taken"',
            'echo "git-safety snapshot taken"; Task triage', 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(take_precedes_triage_task_holds(mutant))

    # (2) a failed snapshot halts before any agent runs
    def test_take_failure_halts(self):
        self.assertTrue(take_failure_halts_holds(self.text))

    def test_mutant_else_branch_continues(self):
        mutant = self.text.replace(
            TAKE_HALT_ECHO, "continuing without a snapshot", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(take_failure_halts_holds(mutant))

    def test_mutant_prose_drops_stop(self):
        mutant = self.text.replace("STOP the review", "note it", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(take_failure_halts_holds(mutant))

    # (2b) --all takes the snapshot once per pass
    def test_take_once_per_pass(self):
        self.assertTrue(take_once_per_pass_holds(self.text))

    def test_mutant_take_per_chunk(self):
        mutant = self.text.replace("never once per chunk",
                                   "again for each chunk", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(take_once_per_pass_holds(mutant))


class TestCollectGate(unittest.TestCase):
    def setUp(self):
        self.text = _read(COLLECT)

    # (3) compare + notices precede step 0
    def test_gate_precedes_step0(self):
        self.assertTrue(gate_precedes_step0_holds(self.text))

    def test_mutant_gate_moved_after_step0(self):
        start = self.text.find(GATE_HEAD)
        end = self.text.find(STEP0)
        mutant = self.text[:start] + self.text[end:] + "\n" + \
            self.text[start:end]
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(gate_precedes_step0_holds(mutant))

    # (4) the gate runs after the Codex join
    def test_gate_after_codex_join(self):
        self.assertTrue(gate_after_codex_join_holds(self.text))

    def test_mutant_codex_sentence_dropped(self):
        mutant = self.text.replace(CODEX_JOIN, "", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(gate_after_codex_join_holds(mutant))

    # (5) the halt skips scoring, render, persist and the fix loop
    def test_halt_skips_everything(self):
        self.assertTrue(halt_skips_everything_holds(self.text))

    def test_mutant_each_halt_phrase(self):
        for phrase in HALT_PHRASES:
            with self.subTest(phrase=phrase):
                mutant = self.text.replace(phrase, "carry on", 1)
                self.assertNotEqual(mutant, self.text)
                self.assertFalse(halt_skips_everything_holds(mutant))

    # (5b) halt wording: agent-or-owner sentence and recovery hints
    def test_halt_wording(self):
        self.assertTrue(halt_wording_holds(self.text))

    def test_mutant_each_halt_wording(self):
        for phrase in HALT_WORDING:
            with self.subTest(phrase=phrase):
                mutant = self.text.replace(phrase, "", 1)
                self.assertNotEqual(mutant, self.text)
                self.assertFalse(halt_wording_holds(mutant))

    # (6) output copied as message text, not left in the shell output
    def test_notices_copied_as_message_text(self):
        self.assertTrue(notices_copied_as_message_text_holds(self.text))

    def test_mutant_message_text_removed(self):
        mutant = self.text.replace("message text in this same turn",
                                   "the shell output", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(notices_copied_as_message_text_holds(mutant))


class TestZshSafety(unittest.TestCase):
    def setUp(self):
        self.triage = _read(TRIAGE)
        self.collect = _read(COLLECT)

    # (7) rc=$? + case, never ${VAR:+...}
    def test_uses_case_not_optional_expansion(self):
        self.assertTrue(
            uses_case_not_optional_expansion_holds(self.triage, self.collect))

    def test_mutant_optional_expansion_injected(self):
        for name in ("triage", "collect"):
            with self.subTest(file=name):
                texts = {"triage": self.triage, "collect": self.collect}
                if name == "collect":
                    mutant = self.collect.replace(
                        "--consume --repo-changed;",
                        "--consume ${REPO_CHANGED:+--repo-changed};", 1)
                else:
                    mutant = self.triage.replace(
                        '--root "$GREPO"; then',
                        '--root "$GREPO" ${X:+--x}; then', 1)
                self.assertNotEqual(mutant, texts[name])
                texts[name] = mutant
                self.assertFalse(uses_case_not_optional_expansion_holds(
                    texts["triage"], texts["collect"]))

    def test_mutant_rc_capture_dropped(self):
        mutant = self.collect.replace("; rc=$?", "", 1)
        self.assertNotEqual(mutant, self.collect)
        self.assertFalse(
            uses_case_not_optional_expansion_holds(self.triage, mutant))

    def test_mutant_nonzero_branch_loses_repo_changed(self):
        mutant = self.collect.replace("--consume --repo-changed;",
                                      "--consume;", 1)
        self.assertNotEqual(mutant, self.collect)
        self.assertFalse(
            uses_case_not_optional_expansion_holds(self.triage, mutant))


class TestContractAndSpines(unittest.TestCase):
    # (8) write contract names the scratch paths
    def test_contract_lists_scratch_paths(self):
        self.assertTrue(contract_lists_scratch_paths_holds(_read(CONTRACT)))

    def test_mutant_contract_drops_fixcheck(self):
        text = _read(CONTRACT)
        mutant = text.replace(".turingmind/fixcheck/", "", 1)
        self.assertNotEqual(mutant, text)
        self.assertFalse(contract_lists_scratch_paths_holds(mutant))

    # (9) the halt never moved into a Phase 5 skip condition
    def test_skip_sections_untouched(self):
        for name, path in SPINES.items():
            with self.subTest(spine=name):
                self.assertTrue(skip_section_untouched_holds(_read(path)))

    def test_mutant_skip_section_mentions_gitsnap(self):
        for name, path in SPINES.items():
            with self.subTest(spine=name):
                text = _read(path)
                mutant = text.replace(
                    "### Skip conditions\n",
                    "### Skip conditions\n\n- gitsnap compare changed\n", 1)
                self.assertNotEqual(mutant, text)
                self.assertFalse(skip_section_untouched_holds(mutant))

    # (10) both spines name the two gates
    def test_spines_name_gates(self):
        for name, path in SPINES.items():
            with self.subTest(spine=name):
                self.assertTrue(spine_names_gates_holds(_read(path)))

    def test_mutant_spine_drops_gate_sentence(self):
        for name, path in SPINES.items():
            with self.subTest(spine=name):
                text = _read(path)
                mutant = text.replace(" can also halt the pass.", ".", 1)
                self.assertNotEqual(mutant, text)
                self.assertFalse(spine_names_gates_holds(mutant))


if __name__ == "__main__":
    unittest.main()
