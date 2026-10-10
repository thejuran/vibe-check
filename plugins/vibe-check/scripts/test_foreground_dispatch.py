"""Every subagent dispatch runs in the foreground.

The orchestrator collects each agent's result in the turn after the dispatch
(Phase 3 after the Phase-2 fan-out, the fix results after Step B). Claude Code
can run an `Agent`/`Task` call in the background when `run_in_background` is
left out; the turn then ends with nothing collected and the review stops
mid-pass. The hard contract (read before every run) and the Phase-2 dispatch
shape therefore require `run_in_background: false` on every dispatch.
"""
import os
import unittest

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACT = os.path.join(PLUGIN_DIR, "phases", "shared", "00-contract.md")
DISPATCH = os.path.join(PLUGIN_DIR, "phases", "review", "20-dispatch.md")
FIX_LOOP = os.path.join(PLUGIN_DIR, "phases", "review", "50-fix-loop.md")
TRIAGE = os.path.join(PLUGIN_DIR, "phases", "review", "10-triage.md")

FLAG = "`run_in_background: false`"
CONTRACT_RULE = ("**Subagents run in the foreground.** Every `Task` (Agent) "
                 "call this command makes sets " + FLAG)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def contract_requires_foreground(text):
    return CONTRACT_RULE in text


class TestForegroundDispatch(unittest.TestCase):
    def test_contract_rule(self):
        self.assertTrue(contract_requires_foreground(read(CONTRACT)))

    def test_rule_sits_under_phase_progression(self):
        text = read(CONTRACT)
        self.assertLess(text.index("**Phase progression — non-negotiable:**"),
                        text.index(CONTRACT_RULE))

    def test_every_dispatch_site_repeats_the_flag(self):
        for path in (DISPATCH, FIX_LOOP, TRIAGE):
            with self.subTest(file=os.path.basename(path)):
                self.assertIn(FLAG, read(path))

    def test_mutant_contract_without_rule_fails(self):
        text = read(CONTRACT)
        self.assertFalse(contract_requires_foreground(
            text.replace(CONTRACT_RULE, "")))


if __name__ == "__main__":
    unittest.main()
