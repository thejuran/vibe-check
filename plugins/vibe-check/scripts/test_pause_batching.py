"""test_pause_batching.py — the NONINTERACTIVE output contract as byte pins.

When `$TURINGMIND_NONINTERACTIVE` is truthy, a review run never asks: the
Phase 5 spine's skip bullet disables the fix loop (a one-line summary is
printed instead), and Finalize mode's gate returns `fallback`, which prints the
outstanding list and the legacy "re-run with `--finalize`" instruction and
stops. CI and scripted callers depend on that text staying exactly as it is.

The interactive branches of the same prose (the per-finding asks in Phase 5
and in the finalize loop) share paragraphs with the fallback branch — the
"Cannot finalize…" header and the join-rule list line are rendered by both. A
rewrite of the interactive path can therefore change the NONINTERACTIVE output
without anyone noticing. These pins make any such drift fail the suite.

The literals in PINS were copied from HEAD 116f14a — never regenerate them
from the worktree. Regenerating from the current files would make the test
agree with whatever drift it is supposed to catch.
"""

import os
import sys
import unittest

# Make `import finalize_gate` resolve when unittest discovery runs from root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import finalize_gate  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(HERE)


def read_prose(relpath):
    with open(os.path.join(PLUGIN_DIR, relpath), "r", encoding="utf-8") as fh:
        return fh.read()


REVIEW_MD = "commands/review.md"
DEEP_REVIEW_MD = "commands/deep-review.md"
FINALIZE_MD = "phases/shared/90-finalize.md"

# Literals copied from HEAD 116f14a — never regenerate from the worktree.
REVIEW_SKIP_PIN = (
    "- The `$TURINGMIND_NONINTERACTIVE` env var is NOT set to a truthy value "
    "(CI / scripted runs disable the loop; print a one-line summary instead)"
)
DEEP_REVIEW_SKIP_PIN = (
    "- `$TURINGMIND_NONINTERACTIVE` is NOT set to a truthy value "
    "(CI / scripted runs print a one-line summary instead)"
)

PINS = {
    REVIEW_MD: (REVIEW_SKIP_PIN,),
    DEEP_REVIEW_MD: (DEEP_REVIEW_SKIP_PIN,),
    FINALIZE_MD: (
        "  - `noninteractive` — `$TURINGMIND_NONINTERACTIVE` is set to a "
        "truthy value",
        "  - Print: \"Cannot finalize — {{N}} Critical/Warning findings remain:\"",
        "  - List each obligation whose hash is in `outstanding_cw_hashes` as "
        "`{{file}}:{{line}} — {{title}}`. **Join rule** (also used by the "
        "Medium loop for `unacknowledged_medium_hashes`): match the hash to a "
        "row of `state.passes[-1].findings` by `stable_hash`; when no row "
        "matches, match it to the `members[]` entry whose "
        "`obligation.stable_hash` equals it and render that member's "
        "file/line/title/agent, with the band read from `obligation.band`, "
        "and the suffix `(absorbed into \"{{lead title}}\" — decided on its "
        "own)`.",
        "  - `fallback` — Phase 5 is unavailable (e.g. "
        "`$TURINGMIND_NONINTERACTIVE` is set, or PR/range mode); fall back to "
        "the legacy behavior: tell user "
        "\"Fix these, re-run with `--finalize`.\" and stop. No asks, no writes.",
        "- `fallback` with `outstanding_cw` empty — the Medium acknowledgement "
        "loop needs an interactive Phase 5 too (its \"Will fix\" answer "
        "defers to Phase 5): list each unacknowledged Medium as "
        "`{{file}}:{{line}} — {{title}}` (join rule above), tell the user "
        "\"Acknowledge these interactively, or fix them, then re-run with "
        "`--finalize`.\" and stop. Do NOT write REVIEW.md or archive state.",
    ),
}


def skip_conditions_section(text):
    """The Phase 5 "### Skip conditions" list, up to the next H2 or the
    report-first paragraph that follows the list in review.md."""
    start = text.index("### Skip conditions")
    ends = [
        i for i in (
            text.find("\n## ", start),
            text.find("\nWhen the report-first", start),
        ) if i != -1
    ]
    return text[start:min(ends)] if ends else text[start:]


def flip(ch):
    """A different character at the same position (codepoint low bit
    toggled), so the mutant has the same length as the pin."""
    return chr(ord(ch) ^ 1)


class TestNoninteractiveBytePin(unittest.TestCase):
    def test_each_pin_present_exactly_once(self):
        for path, pins in PINS.items():
            text = read_prose(path)
            for pin in pins:
                with self.subTest(path=path, pin=pin[:40]):
                    self.assertEqual(text.count(pin), 1)

    def test_pins_are_nonempty_and_single_line(self):
        for path, pins in PINS.items():
            for pin in pins:
                with self.subTest(path=path, pin=pin[:40]):
                    self.assertTrue(pin.strip())
                    self.assertNotIn("\n", pin)

    def test_mutation_detects_drift(self):
        """A one-character change anywhere in a pinned sentence (first,
        middle, last position) must make the exact-count check miss — proof
        that test_each_pin_present_exactly_once is load-bearing."""
        for path, pins in PINS.items():
            text = read_prose(path)
            for pin in pins:
                for pos in (0, len(pin) // 2, len(pin) - 1):
                    mutant = pin[:pos] + flip(pin[pos]) + pin[pos + 1:]
                    with self.subTest(path=path, pin=pin[:40], pos=pos):
                        self.assertNotEqual(mutant, pin)
                        self.assertEqual(text.count(mutant), 0)

    def test_case_flip_of_not_detects_drift(self):
        """The skip bullets' meaning hinges on "NOT"; lower-casing it is the
        smallest edit a prose rewrite could make, and it must fail."""
        for path, pin in ((REVIEW_MD, REVIEW_SKIP_PIN),
                          (DEEP_REVIEW_MD, DEEP_REVIEW_SKIP_PIN)):
            mutant = pin.replace("NOT", "not", 1)
            with self.subTest(path=path):
                self.assertNotEqual(mutant, pin)
                self.assertEqual(read_prose(path).count(mutant), 0)

    def test_skip_pins_live_in_the_skip_conditions_list(self):
        """The skip bullet must sit in Phase 5's skip list, not elsewhere."""
        for path, pin in ((REVIEW_MD, REVIEW_SKIP_PIN),
                          (DEEP_REVIEW_MD, DEEP_REVIEW_SKIP_PIN)):
            section = skip_conditions_section(read_prose(path))
            with self.subTest(path=path):
                self.assertEqual(section.count(pin), 1)

    def test_noninteractive_gate_is_fallback(self):
        """The gate still routes NONINTERACTIVE runs to the pinned fallback
        branch, for outstanding Critical/Warning and for Medium-only states."""
        base = {
            "state_file_present": True,
            "outstanding_cw": 1,
            "unacknowledged_medium": 0,
            "noninteractive": True,
            "pr_mode": False,
            "range_mode": False,
        }
        self.assertEqual(finalize_gate.decide(base)["action"], "fallback")
        medium_only = dict(base, outstanding_cw=0, unacknowledged_medium=2)
        self.assertEqual(
            finalize_gate.decide(medium_only)["action"], "fallback")


# Cross-reference locks for the batched-card prose go below.


if __name__ == "__main__":
    unittest.main()
