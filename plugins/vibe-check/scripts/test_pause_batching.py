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

import hashlib
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

FIX_LOOP_MD = "phases/review/50-fix-loop.md"
ESTIMATE_GATE_MD = "phases/review/03-estimate-gate.md"

# Phrases from the old fix-loop / finalize shape (two menus per pass, one ask
# per finding at finalize, the Medium acknowledgement loop). Any occurrence
# outside the byte-pinned NONINTERACTIVE lines would send the model looking
# for a menu that no longer exists.
BANNED_OLD_SHAPE = (
    "Step A",
    "Step C",
    "I'll apply them myself",
    "Abandon for now",
    "per-finding asks",
    "minimal shape",
    "Look again",
    "Will fix",
    "acknowledgement loop",
)
CORPUS_DIRS = ("commands", "phases", "agents", "templates")
CORPUS_FILES = ("scripts/finalize_gate.py", "scripts/test_finalize_gate.py")


def corpus_paths():
    """Plugin-relative paths of every prose file the old-shape lock covers."""
    paths = []
    for top in CORPUS_DIRS:
        for root, dirs, files in os.walk(os.path.join(PLUGIN_DIR, top)):
            dirs.sort()
            for name in sorted(files):
                if name.endswith(".md"):
                    full = os.path.join(root, name)
                    paths.append(os.path.relpath(full, PLUGIN_DIR))
    paths.extend(CORPUS_FILES)
    return sorted(paths)


def strip_pins(relpath, text):
    """Remove each byte-pinned literal for this file. Exact replacement is
    the only exemption: a neighbour or a one-character variant survives."""
    for pin in PINS.get(relpath, ()):
        text = text.replace(pin, "")
    return text


def old_shape_hits(relpath, text):
    stripped = strip_pins(relpath, text)
    return sorted(n for n in BANNED_OLD_SHAPE if n in stripped)


MEDIUM_FALLBACK_PIN = next(
    pin for pin in PINS[FINALIZE_MD] if "Will fix" in pin)


class TestOldFixLoopShapeGone(unittest.TestCase):
    def test_corpus_is_clean(self):
        for path in corpus_paths():
            with self.subTest(path=path):
                self.assertEqual(old_shape_hits(path, read_prose(path)), [])

    def test_corpus_is_nonempty(self):
        """A walk that silently collects nothing would make the clean check
        pass vacuously."""
        paths = corpus_paths()
        self.assertGreaterEqual(len(paths), 40)
        for required in (REVIEW_MD, DEEP_REVIEW_MD, FIX_LOOP_MD, FINALIZE_MD,
                         ESTIMATE_GATE_MD, *CORPUS_FILES):
            with self.subTest(required=required):
                self.assertIn(required, paths)

    def test_mutants_trip(self):
        text = read_prose(FINALIZE_MD)
        for needle in BANNED_OLD_SHAPE:
            with self.subTest(needle=needle):
                self.assertIn(
                    needle, old_shape_hits(FINALIZE_MD, text + "\n" + needle))

    def test_pin_exemption_is_exact(self):
        text = read_prose(FINALIZE_MD)
        self.assertEqual(text.count(MEDIUM_FALLBACK_PIN), 1)
        # A banned phrase right after the pinned line is still caught.
        end = text.index(MEDIUM_FALLBACK_PIN) + len(MEDIUM_FALLBACK_PIN)
        neighbour = text[:end] + " Will fix" + text[end:]
        self.assertIn("Will fix", old_shape_hits(FINALIZE_MD, neighbour))
        # A pinned line drifted by one character is no longer exempt.
        drifted_pin = MEDIUM_FALLBACK_PIN.replace("Will fix", "Will  fix", 1)
        self.assertNotEqual(drifted_pin, MEDIUM_FALLBACK_PIN)
        drifted = text.replace(MEDIUM_FALLBACK_PIN, drifted_pin)
        self.assertIn("Will  fix", strip_pins(FINALIZE_MD, drifted))
        self.assertIn("acknowledgement loop",
                      old_shape_hits(FINALIZE_MD, drifted))


SPINES = (REVIEW_MD, DEEP_REVIEW_MD)
SPINE_ROW = "or when the finalize card routes a fix set into the fix-loop card"
SPINE_SENTENCE = (
    "Phase 5 runs only if the finalize card routes a fix set into the "
    "fix-loop card.")
PHASE_5_ROW_PREFIX = "| 5 | `phases/review/50-fix-loop.md` |"
FINALIZE_SECTION = "## Finalize mode (`--finalize`)"


def spine_row_ok(text):
    rows = [ln for ln in text.splitlines() if SPINE_ROW in ln]
    return (text.count(SPINE_ROW) == 1 and len(rows) == 1
            and rows[0].startswith(PHASE_5_ROW_PREFIX))


def spine_sentence_ok(text):
    if text.count(SPINE_SENTENCE) != 1 or FINALIZE_SECTION not in text:
        return False
    start = text.index(FINALIZE_SECTION)
    end = text.find("\n## ", start + 1)
    section = text[start:end] if end != -1 else text[start:]
    return section.count(SPINE_SENTENCE) == 1


def fix_loop_target_ok(text):
    return text.count("\n### The fix-loop card") == 1


def finalize_target_ok(text):
    return sum(1 for ln in text.splitlines()
               if ln.startswith("### The finalize card")) == 1


class TestSpineCrossRefs(unittest.TestCase):
    def test_phase_table_row(self):
        for path in SPINES:
            with self.subTest(path=path):
                self.assertTrue(spine_row_ok(read_prose(path)))

    def test_finalize_mode_sentence(self):
        for path in SPINES:
            with self.subTest(path=path):
                self.assertTrue(spine_sentence_ok(read_prose(path)))

    def test_targets_resolve(self):
        self.assertTrue(fix_loop_target_ok(read_prose(FIX_LOOP_MD)))
        self.assertTrue(finalize_target_ok(read_prose(FINALIZE_MD)))

    def test_estimate_gate_points_at_card(self):
        self.assertGreaterEqual(
            read_prose(ESTIMATE_GATE_MD).count("the Phase 5 fix-loop card"), 2)

    def test_who_owns_what(self):
        lines = [ln for ln in read_prose(FINALIZE_MD).splitlines()
                 if ln.startswith("**Who owns what.**")]
        self.assertEqual(len(lines), 1)
        self.assertIn("open the finalize card", lines[0])

    def test_mutants_trip(self):
        fix_loop = read_prose(FIX_LOOP_MD)
        renamed = fix_loop.replace(
            "### The fix-loop card", "### The fix loop card")
        self.assertFalse(fix_loop_target_ok(renamed))
        finalize = read_prose(FINALIZE_MD)
        renamed = finalize.replace(
            "### The finalize card", "### The finalise card")
        self.assertFalse(finalize_target_ok(renamed))
        for path in SPINES:
            text = read_prose(path)
            with self.subTest(path=path, lock="row"):
                stale = text.replace(
                    SPINE_ROW, "or when finalize routes findings into Step A")
                self.assertFalse(spine_row_ok(stale))
            with self.subTest(path=path, lock="sentence"):
                stale = text.replace(
                    SPINE_SENTENCE,
                    "Phase 5 runs only if the finalize file routes findings "
                    "into its Step A.")
                self.assertFalse(spine_sentence_ok(stale))


def skip_section_to_h2(text):
    """From "### Skip conditions" up to (not including) the next H2."""
    start = text.index("### Skip conditions")
    end = text.find("\n## ", start)
    return text[start:end] if end != -1 else text[start:]


def sha256_hex(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Digests of HEAD 116f14a — never regenerate from the worktree.
SKIP_SHA256 = {
    REVIEW_MD:
        "9bedee388c5705da5b74c9109a8e7dcdfa0163f08a1a977b5e97d7e096a44394",
    DEEP_REVIEW_MD:
        "49f97fd165e2adac24f896bab33326f4937d1f7a122978ea856d5dcb3afa610c",
}

# Copied from HEAD 116f14a — never regenerate from the worktree.
ESTIMATE_GATE_PIN = (
    "Non-interactive mode — the estimate gate cannot prompt for approval. "
    "Re-run interactively to choose Run full / Cap, or (future) pass an "
    "explicit scope/cap flag. Nothing was dispatched."
)


class TestSkipSectionsByteIdentical(unittest.TestCase):
    def test_skip_sections_match_digest(self):
        for path, digest in SKIP_SHA256.items():
            with self.subTest(path=path):
                self.assertEqual(
                    sha256_hex(skip_section_to_h2(read_prose(path))), digest)

    def test_skip_digest_mutant(self):
        for path, digest in SKIP_SHA256.items():
            section = skip_section_to_h2(read_prose(path))
            pos = len(section) // 2
            mutant = section[:pos] + flip(section[pos]) + section[pos + 1:]
            with self.subTest(path=path):
                self.assertNotEqual(sha256_hex(mutant), digest)

    def test_estimate_gate_noninteractive_pin(self):
        text = read_prose(ESTIMATE_GATE_MD)
        self.assertEqual(text.count(ESTIMATE_GATE_PIN), 1)
        pos = len(ESTIMATE_GATE_PIN) // 2
        mutant = (ESTIMATE_GATE_PIN[:pos] + flip(ESTIMATE_GATE_PIN[pos])
                  + ESTIMATE_GATE_PIN[pos + 1:])
        self.assertEqual(text.count(mutant), 0)


if __name__ == "__main__":
    unittest.main()
