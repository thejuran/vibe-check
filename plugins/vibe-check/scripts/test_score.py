"""Pinning unit tests for score.py — the deterministic-core extraction (Phase 16).

This is the FIRST test suite in the plugin. It pins the CURRENT scoring.md +
review.md behavior byte-for-byte so the extraction is provably equivalent
(Phase 17 hardens; Phase 16 only freezes the current outputs).

Run from repo root:
    python3 -m unittest discover -s plugins/vibe-check/scripts -p 'test_*.py'
Or from this dir:
    cd plugins/vibe-check/scripts && python3 -m unittest

NOTE: importing `os`/`ast`/`subprocess` in THIS test file is fine — the import
ban is on score.py exclusively. The AST test below enforces that ban on score.py.
"""

import ast
import itertools
import os
import re
import subprocess
import sys
import unittest

# Make `import score` resolve when unittest discovery runs from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import score  # noqa: E402  (sibling module under test)

SCORE_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "score.py")

# GOLDEN sha256 stable_hash digest (T-16-01) — the SINGLE source of truth.
# This is an INDEPENDENTLY hard-coded literal, NOT recomputed via
# score.stable_hash(...) (that would make the freeze tautological) and NOT
# re-pinned to a new value (it keys persisted medium_acknowledgments dismissals —
# any drift silently breaks them; Pitfall 4). Both golden-digest tests reference
# this one constant so the frozen value lives in exactly ONE place.
GOLDEN_DIGEST = "7a516d0120c0ff3110198c731f49a775d55dd06071e1831e4a554c7bff793124"


# --------------------------------------------------------------------------- #
# Test fixtures / helpers
# --------------------------------------------------------------------------- #
def make_finding(**overrides):
    """A minimal valid finding (agent-output-schema shape) with sane defaults.

    Defaults are chosen so the bare finding scores predictably:
    agent_confidence=100, severity=critical (+0), no diff/silenced/intent/etc.
    """
    f = {
        "id": "x-001",
        "file": "src/a.py",
        "line": 10,
        "title": "some bug",
        "category": "bug",
        "cwe": None,
        "severity": "critical",
        "agent_confidence": 100,
        "in_diff": False,
        "intent_doc_match": None,
        "problem": "p",
        "current_code": "  x = 1",
        "fix_hint": None,
        "why_it_matters": "w",
        "silenced_marker_nearby": False,
        "agent": "bugs",
    }
    f.update(overrides)
    return f


def score_of(finding, *, in_diff=False, silenced=False, cross_confirmed=False,
             persisted=False):
    """Convenience wrapper around score.compute_score with keyword overrides."""
    return score.compute_score(
        finding,
        in_diff=in_diff,
        silenced=silenced,
        cross_confirmed=cross_confirmed,
        persisted=persisted,
    )


# --------------------------------------------------------------------------- #
# band_for — every band boundary (D-07)
# --------------------------------------------------------------------------- #
class TestBandBoundaries(unittest.TestCase):
    def test_95_is_critical(self):
        self.assertEqual(score.band_for(95), "critical")

    def test_100_is_critical(self):
        self.assertEqual(score.band_for(100), "critical")

    def test_94_is_warning(self):
        self.assertEqual(score.band_for(94), "warning")

    def test_80_is_warning(self):
        self.assertEqual(score.band_for(80), "warning")

    def test_79_is_medium(self):
        self.assertEqual(score.band_for(79), "medium")

    def test_70_is_medium(self):
        self.assertEqual(score.band_for(70), "medium")

    def test_69_is_below_both_thresholds(self):
        # <70 is below both /review (80) and /deep-review (70) thresholds —
        # never a rendered band.
        self.assertIsNone(score.band_for(69))

    def test_0_is_below(self):
        self.assertIsNone(score.band_for(0))


# --------------------------------------------------------------------------- #
# Severity weight branches (scoring.md:21-26) — applied LAST before clamp
# --------------------------------------------------------------------------- #
class TestSeverityWeight(unittest.TestCase):
    # Base finding: agent_confidence=80, no other modifiers, so the result
    # isolates the severity weight: 80 + weight.
    def _base(self, severity):
        return make_finding(agent_confidence=80, severity=severity)

    def test_critical_plus_zero(self):
        self.assertEqual(score_of(self._base("critical")), 80)

    def test_high_minus_three(self):
        self.assertEqual(score_of(self._base("high")), 77)

    def test_medium_minus_eight(self):
        self.assertEqual(score_of(self._base("medium")), 72)

    def test_low_minus_twenty(self):
        self.assertEqual(score_of(self._base("low")), 60)

    def test_unset_severity_fallback_minus_eight(self):
        # severity missing entirely -> -8 medium-equivalent fallback.
        f = make_finding(agent_confidence=80)
        del f["severity"]
        self.assertEqual(score_of(f), 72)

    def test_unrecognized_severity_fallback_minus_eight(self):
        self.assertEqual(score_of(self._base("bogus")), 72)


# --------------------------------------------------------------------------- #
# Each additive modifier in isolation (scoring.md:11-19)
# --------------------------------------------------------------------------- #
class TestAdditiveModifiers(unittest.TestCase):
    def _base(self):
        # agent_confidence=50, severity critical (+0) so the delta is the modifier.
        return make_finding(agent_confidence=50, severity="critical")

    def test_in_diff_plus_twenty(self):
        self.assertEqual(score_of(self._base(), in_diff=True), 70)

    def test_silenced_minus_fifty(self):
        # 50 - 50 = 0 (pre-clamp 0, not <0, so it survives as 0).
        self.assertEqual(score_of(self._base(), silenced=True), 0)

    def test_compliance_agent_plus_twenty(self):
        f = self._base()
        f["agent"] = "compliance"
        self.assertEqual(score_of(f), 70)

    def test_non_compliance_agent_no_bonus(self):
        f = self._base()
        f["agent"] = "security"
        self.assertEqual(score_of(f), 50)

    def test_cross_confirmed_plus_ten(self):
        self.assertEqual(score_of(self._base(), cross_confirmed=True), 60)

    def test_persisted_plus_fifteen(self):
        self.assertEqual(score_of(self._base(), persisted=True), 65)

    def test_two_agent_finding_scores_exactly_ten_over_one_agent(self):
        base = score_of(self._base(), cross_confirmed=False)
        confirmed = score_of(self._base(), cross_confirmed=True)
        self.assertEqual(confirmed - base, 10)


# --------------------------------------------------------------------------- #
# Intent-doc MUTUAL EXCLUSION (D-12) — elif, strictly greater-than
# --------------------------------------------------------------------------- #
class TestIntentDocMutualExclusion(unittest.TestCase):
    def _base(self, confidence):
        return make_finding(
            agent_confidence=100,
            severity="critical",
            intent_doc_match={"doc": "PLAN.md", "section": "s", "quote": "q",
                              "confidence": confidence},
        )

    def test_strong_match_minus_100_only_not_130(self):
        # confidence 0.95 > 0.9 -> -100 ONLY (never -100 then -30 stacked).
        # 100 - 100 = 0 (survives at floor).
        self.assertEqual(score_of(self._base(0.95)), 0)

    def test_partial_match_minus_30(self):
        # confidence 0.8 -> -30. 100 - 30 = 70.
        self.assertEqual(score_of(self._base(0.8)), 70)

    def test_exactly_0_7_no_penalty_strictly_greater(self):
        # 0.7 is NOT > 0.7 -> no penalty. 100 - 0 = 100.
        self.assertEqual(score_of(self._base(0.7)), 100)

    def test_just_above_0_7_gets_penalty(self):
        self.assertEqual(score_of(self._base(0.71)), 70)

    def test_exactly_0_9_only_partial_penalty(self):
        # 0.9 is NOT > 0.9, but IS > 0.7 -> -30 (partial), not -100.
        self.assertEqual(score_of(self._base(0.9)), 70)

    def test_null_intent_doc_no_penalty(self):
        f = make_finding(agent_confidence=100, severity="critical",
                         intent_doc_match=None)
        self.assertEqual(score_of(f), 100)

    def test_malformed_intent_doc_treated_as_no_match(self):
        # Defensive (V5/T-16-02): a malformed intent_doc_match (missing
        # confidence) must be treated as no match, not crash.
        f = make_finding(agent_confidence=100, severity="critical",
                         intent_doc_match={"doc": "PLAN.md"})
        self.assertEqual(score_of(f), 100)


# --------------------------------------------------------------------------- #
# Clamp [0,100] at both ends (scoring.md:29)
# --------------------------------------------------------------------------- #
class TestClamp(unittest.TestCase):
    def test_over_100_clamps_to_100(self):
        # agent_confidence=100, +20 in_diff, +20 compliance, +10 cross,
        # +15 persisted = 165 pre-clamp -> clamp 100.
        f = make_finding(agent_confidence=100, severity="critical",
                         agent="compliance")
        self.assertEqual(
            score_of(f, in_diff=True, cross_confirmed=True, persisted=True),
            100,
        )

    def test_floor_survivor_clamps_to_0_not_dropped(self):
        # pre-clamp exactly 0 must survive as 0 (only pre-clamp <0 drops).
        f = make_finding(agent_confidence=50, severity="critical")
        self.assertEqual(score_of(f, silenced=True), 0)


# --------------------------------------------------------------------------- #
# DROP rule (D-14) — pre-clamp < 0 ⇒ DROP entirely (not clamp-to-0)
# --------------------------------------------------------------------------- #
class TestDropRule(unittest.TestCase):
    def test_pre_clamp_negative_returns_drop_signal(self):
        # agent_confidence=40, silenced -50, severity medium -8 = -18 pre-clamp.
        # < 0 -> DROP (compute_score returns None, the drop signal).
        f = make_finding(agent_confidence=40, severity="medium")
        self.assertIsNone(score_of(f, silenced=True))

    def test_drop_via_run_absent_from_findings_present_in_filtered(self):
        # The dropped finding must be ABSENT from output findings[] and PRESENT
        # in filtered[] (NOT clamped-to-0-and-emitted).
        f = make_finding(id="drop-1", agent_confidence=40, severity="medium",
                         silenced_marker_nearby=True,
                         source_window=["x", "# noqa", "y"])
        envelope = {
            "command": "deep-review",
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {},
            "carryforward": [],
            "findings": [f],
        }
        result = score.run(envelope)
        ids = [g["id"] for g in result["findings"]]
        self.assertNotIn("drop-1", ids)
        # It is recorded in filtered[] with a reason.
        filtered_titles = [x for x in result["filtered"]]
        self.assertTrue(len(filtered_titles) >= 1)


# --------------------------------------------------------------------------- #
# Per-command threshold filter (scoring.md:57-64) — one parameter, not 2 paths
# --------------------------------------------------------------------------- #
class TestThresholds(unittest.TestCase):
    def _envelope(self, command, agent_confidence):
        f = make_finding(id="t-1", agent_confidence=agent_confidence,
                         severity="critical", line=10,
                         source_window=["a", "b", "c", "d", "e"])
        return {
            "command": command,
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {},
            "carryforward": [],
            "findings": [f],
        }

    def test_review_filters_below_80(self):
        # score 79 < 80 -> filtered as sub-threshold under /review.
        result = score.run(self._envelope("review", 79))
        self.assertEqual([g["id"] for g in result["findings"]], [])
        self.assertTrue(
            any(x.get("reason") == "sub-threshold" for x in result["filtered"])
        )

    def test_review_keeps_80(self):
        result = score.run(self._envelope("review", 80))
        self.assertEqual([g["id"] for g in result["findings"]], ["t-1"])

    def test_deep_review_keeps_70(self):
        # score 70 >= 70 -> survives under /deep-review.
        result = score.run(self._envelope("deep-review", 70))
        self.assertEqual([g["id"] for g in result["findings"]], ["t-1"])

    def test_deep_review_filters_below_70(self):
        result = score.run(self._envelope("deep-review", 69))
        self.assertEqual([g["id"] for g in result["findings"]], [])
        self.assertTrue(
            any(x.get("reason") == "sub-threshold" for x in result["filtered"])
        )

    def test_deep_review_keeps_79_review_filters_79(self):
        # 79 is Medium band: surfaced only by /deep-review, filtered by /review.
        self.assertEqual(
            [g["id"] for g in score.run(self._envelope("deep-review", 79))["findings"]],
            ["t-1"],
        )
        self.assertEqual(
            [g["id"] for g in score.run(self._envelope("review", 79))["findings"]],
            [],
        )


# --------------------------------------------------------------------------- #
# silenced_nearby — ±2 window (D-13), the 5 canonical markers (review.md:685)
# --------------------------------------------------------------------------- #
class TestSilencedNearby(unittest.TestCase):
    MARKERS = ["eslint-disable", "# noqa", "// nolint", "@SuppressWarnings",
               "#[allow("]

    def test_each_canonical_marker_detected(self):
        for marker in self.MARKERS:
            with self.subTest(marker=marker):
                window = ["plain", "code " + marker + " here", "more"]
                self.assertTrue(score.silenced_nearby(window))

    def test_no_marker_returns_false(self):
        self.assertFalse(score.silenced_nearby(["a", "b", "c", "d", "e"]))

    def test_marker_at_window_edge_minus2(self):
        # Inclusive [L-2 .. L+2]: a marker at the far edge still counts.
        window = ["eslint-disable", "b", "c", "d", "e"]
        self.assertTrue(score.silenced_nearby(window))

    def test_marker_at_window_edge_plus2(self):
        window = ["a", "b", "c", "d", "x // nolint"]
        self.assertTrue(score.silenced_nearby(window))

    def test_empty_window_false(self):
        self.assertFalse(score.silenced_nearby([]))


# --------------------------------------------------------------------------- #
# carry_forward_status (review.md:672-678, D-11 strip both sides)
# --------------------------------------------------------------------------- #
class TestCarryForwardStatus(unittest.TestCase):
    def test_null_canonical_is_fixed_since_last(self):
        f = make_finding(current_code="  return q")
        self.assertEqual(score.carry_forward_status(f, None), "fixed-since-last")

    def test_matching_first_line_is_persisted(self):
        # First line of current_code stripped == canonical stripped -> persisted.
        f = make_finding(current_code="  return q\n  more")
        self.assertEqual(score.carry_forward_status(f, "return q"), "persisted")

    def test_whitespace_drift_both_sides_stripped_still_persisted(self):
        # D-11: strip BOTH sides — leading/trailing whitespace drift is NOT a
        # false "fixed".
        f = make_finding(current_code="    return q   ")
        self.assertEqual(score.carry_forward_status(f, "  return q  "), "persisted")

    def test_content_changed_is_needs_recheck(self):
        f = make_finding(current_code="  return q")
        self.assertEqual(
            score.carry_forward_status(f, "return DIFFERENT"), "needs-recheck"
        )

    def test_non_str_canonical_does_not_raise(self):
        # C1 (deep-review): a present-but-non-str canonical_line_content (a JSON
        # number/array/object from a malformed-but-parseable carryforward entry)
        # must NOT raise AttributeError on .strip() — the None guard above it
        # only covers null, not non-str-non-None. It coerces to "" and, since a
        # real current_code first line != "", classifies as needs-recheck.
        f = make_finding(current_code="  return q")
        for bad in (0, 1, [], {}, ["x"], {"k": "v"}, 3.14):
            with self.subTest(bad=bad):
                self.assertEqual(
                    score.carry_forward_status(f, bad), "needs-recheck"
                )

    def test_non_str_canonical_flows_through_run_without_raising(self):
        # End-to-end: a carryforward whose canonical_line_content is non-str
        # must not crash run() (which would propagate non-zero and trip the
        # orchestrator's fail-closed render halt on the WHOLE review pass).
        cf = make_finding(id="cf-badcanon", file="src/a.py", line=10,
                          title="odd carryforward", agent_confidence=85,
                          severity="critical", current_code="  return q",
                          canonical_line_content=[],
                          source_window=["a", "b", "c", "d", "e"])
        envelope = {
            "command": "deep-review",
            "all_mode": False,
            "pass_number": 2,
            "changed_line_ranges": {"src/a.py": [[8, 14]]},
            "carryforward": [cf],
            "findings": [],
        }
        result = score.run(envelope)  # must not raise
        self.assertTrue(result["scored_by_script"])
        survivors = {g["id"]: g for g in result["findings"]}
        self.assertIn("cf-badcanon", survivors)
        # Non-str canonical => needs-recheck (changed), NOT a false persisted.
        self.assertEqual(survivors["cf-badcanon"]["status"], "needs-recheck")


# --------------------------------------------------------------------------- #
# carry_forward_status — ROBUST-03 SYMMETRIC-OR-DEGRADE low-entropy carry key.
# The compare widens BOTH sides or NEITHER (never window-vs-single-line). An
# UNCHANGED finding stays "persisted" whether its stored snippet is one line or
# many — a low-entropy single-line snippet never falsely flips to needs-recheck.
# The frozen stable_hash golden does NOT move (D-07): _carry_key / canonical_window
# are SEPARATE from the canonical_for_hash path.
# --------------------------------------------------------------------------- #
class TestCarryForwardLowEntropyWindow(unittest.TestCase):
    # --- Test 1 (no churn, distinctive — same as the existing persisted test). #
    def test_distinctive_first_line_no_churn_persisted(self):
        # A distinctive (high-entropy) first line degrades to the first-line
        # compare exactly as today — byte-identical persisted classification.
        f = make_finding(current_code="  return q\n  more")
        self.assertEqual(
            score.carry_forward_status(f, "return q",
                                       canonical_window="return q\n  more"),
            "persisted",
        )

    # --- Test 3 (BLOCKER-1 single-line low-entropy NO-CHURN — round-2 fix). --- #
    def test_single_line_low_entropy_unchanged_stays_persisted(self):
        # Prior current_code "}" (SINGLE line, low-entropy), canonical "}",
        # canonical_window "}\n  nextLine()" (HEAD happens to have a next line).
        # The prior side has no usable 2nd line, so we do NOT widen — DEGRADE to
        # the first-line compare: "}" == "}" -> persisted (NOT needs-recheck).
        # This is the exact false-flip the round-1 fix caused; it must be gone.
        f = make_finding(current_code="}")
        self.assertEqual(
            score.carry_forward_status(f, "}",
                                       canonical_window="}\n  nextLine()"),
            "persisted",
        )

    # --- Test 4 (multi-line low-entropy disambiguation — collision gone). ---- #
    def test_multi_line_low_entropy_different_window_needs_recheck(self):
        # Both sides have >=2 non-blank lines and the first line is low-entropy,
        # so we WIDEN: the surrounding windows differ -> needs-recheck.
        f = make_finding(current_code="}\n  doThingA()")
        self.assertEqual(
            score.carry_forward_status(f, "}",
                                       canonical_window="}\n  doThingB()"),
            "needs-recheck",
        )

    # --- Test 5 (multi-line low-entropy UNCHANGED stays persisted). --------- #
    def test_multi_line_low_entropy_same_window_persisted(self):
        # WIDEN path with IDENTICAL windows on both sides -> persisted (no false
        # flip when the surrounding context is genuinely unchanged).
        f = make_finding(current_code="}\n  doThingA()")
        self.assertEqual(
            score.carry_forward_status(f, "}",
                                       canonical_window="}\n  doThingA()"),
            "persisted",
        )

    # --- Test 6 (degrade — no canonical_window at all). -------------------- #
    def test_low_entropy_no_window_degrades_to_first_line(self):
        # A low-entropy multi-line prior but canonical_window=None -> DEGRADE to
        # the first-line compare; an unchanged first line stays persisted and
        # does not raise.
        f = make_finding(current_code="}\n  doThingA()")
        self.assertEqual(
            score.carry_forward_status(f, "}", canonical_window=None),
            "persisted",
        )
        # default-arg (no canonical_window passed at all) is equivalent.
        self.assertEqual(score.carry_forward_status(f, "}"), "persisted")

    def test_low_entropy_single_line_window_degrades(self):
        # canonical_window present but only ONE non-blank line -> NOT widen-
        # eligible (RHS lacks a real window) -> DEGRADE; unchanged stays persisted.
        f = make_finding(current_code="}\n  doThingA()")
        self.assertEqual(
            score.carry_forward_status(f, "}", canonical_window="}"),
            "persisted",
        )

    def test_null_canonical_still_fixed_since_last_with_window(self):
        # A null canonical_line_content is fixed-since-last regardless of any
        # window the orchestrator may have resolved.
        f = make_finding(current_code="}\n  doThingA()")
        self.assertEqual(
            score.carry_forward_status(f, None,
                                       canonical_window="}\n  whatever()"),
            "fixed-since-last",
        )

    def test_widen_keys_on_three_nonblank_lines_ignoring_blanks(self):
        # _carry_key takes the first <=3 NON-BLANK lines; intervening blank lines
        # are skipped so cosmetic blank-line drift does not flip the key.
        f = make_finding(current_code="}\n\n  a()\n  b()\n  c()\n  d()")
        # canonical_window with the SAME 3 non-blank lines (different blank layout)
        # -> persisted (the window keys on the first 3 non-blank lines only).
        self.assertEqual(
            score.carry_forward_status(
                f, "}", canonical_window="}\n  a()\n\n  b()\n  c()"),
            "persisted",
        )

    def test_widen_genuine_third_line_change_needs_recheck(self):
        # Same first two lines, a DIFFERENT third non-blank line -> the <=3 window
        # differs -> needs-recheck (the window is wide enough to catch it).
        f = make_finding(current_code="}\n  a()\n  bOLD()")
        self.assertEqual(
            score.carry_forward_status(
                f, "}", canonical_window="}\n  a()\n  bNEW()"),
            "needs-recheck",
        )

    def test_non_str_current_code_does_not_raise(self):
        # Pattern 1: a non-str current_code must not crash the compare.
        f = make_finding()
        f["current_code"] = 12345
        # _first_line coerces to "" -> first line "" != "}" -> needs-recheck,
        # but crucially it does NOT raise.
        self.assertEqual(
            score.carry_forward_status(f, "}", canonical_window="}\n  x()"),
            "needs-recheck",
        )


# --------------------------------------------------------------------------- #
# _carry_key — the windowed key for ONE side (ROBUST-03), in isolation.
# --------------------------------------------------------------------------- #
class TestCarryKey(unittest.TestCase):
    def test_non_str_coerces_to_empty(self):
        self.assertEqual(score._carry_key(None), "")
        self.assertEqual(score._carry_key(12345), "")
        self.assertEqual(score._carry_key({"k": "v"}), "")

    def test_first_three_nonblank_lines_joined(self):
        self.assertEqual(
            score._carry_key("a\nb\nc\nd"), "a\nb\nc"
        )

    def test_blank_lines_skipped(self):
        self.assertEqual(
            score._carry_key("a\n\n  \nb\n\nc\nd"), "a\nb\nc"
        )

    def test_lines_stripped(self):
        self.assertEqual(
            score._carry_key("  a  \n\t b\t"), "a\nb"
        )

    def test_fewer_than_three_lines(self):
        self.assertEqual(score._carry_key("}"), "}")
        self.assertEqual(score._carry_key("}\n  next()"), "}\nnext()")


# --------------------------------------------------------------------------- #
# run() end-to-end — the widen path is reachable via the carryforward envelope.
# --------------------------------------------------------------------------- #
class TestCarryForwardWindowEndToEnd(unittest.TestCase):
    def _base(self, cf):
        return {
            "command": "review",
            "all_mode": False,
            "pass_number": 2,
            "changed_line_ranges": {"src/a.py": [[8, 14]]},
            "carryforward": [cf],
            "findings": [],
        }

    def test_single_line_low_entropy_carryforward_persists(self):
        # A legal single-line low-entropy carryforward snippet against an
        # unchanged HEAD (canonical_window has a next line) stays persisted (+15),
        # NOT flipped to needs-recheck (the BLOCKER-1 end-to-end pin).
        cf = make_finding(id="cf-brace", file="src/a.py", line=10,
                          title="dangling brace", agent_confidence=70,
                          severity="critical", current_code="}",
                          canonical_line_content="}",
                          canonical_window="}\n  nextLine()",
                          source_window=["a", "b", "c", "d", "e"])
        result = score.run(self._base(cf))
        survivors = {g["id"]: g for g in result["findings"]}
        self.assertIn("cf-brace", survivors)
        self.assertEqual(survivors["cf-brace"]["status"], "persisted")

    def test_multi_line_low_entropy_changed_window_needs_recheck(self):
        # A multi-line low-entropy carryforward whose surrounding window CHANGED
        # is needs-recheck (no +15 persistence) — it still scores/renders.
        cf = make_finding(id="cf-multi", file="src/a.py", line=10,
                          title="brace block", agent_confidence=85,
                          severity="critical",
                          current_code="}\n  doThingA()",
                          canonical_line_content="}",
                          canonical_window="}\n  doThingB()",
                          source_window=["a", "b", "c", "d", "e"])
        result = score.run(self._base(cf))
        survivors = {g["id"]: g for g in result["findings"]}
        self.assertIn("cf-multi", survivors)
        self.assertEqual(survivors["cf-multi"]["status"], "needs-recheck")

    def test_stable_hash_unchanged_for_low_entropy_carryforward(self):
        # The survivor's stable_hash derives from the UNCHANGED canonical_for_hash
        # path (canonical_line_content "}"), NOT from canonical_window. Pin it to
        # the by-hand stable_hash over the same single-line canonical.
        cf = make_finding(id="cf-hash", file="src/a.py", line=10,
                          title="t", agent_confidence=70, severity="critical",
                          current_code="}", canonical_line_content="}",
                          canonical_window="}\n  nextLine()",
                          source_window=["a", "b", "c", "d", "e"])
        result = score.run(self._base(cf))
        survivors = {g["id"]: g for g in result["findings"]}
        self.assertIn("cf-hash", survivors)
        self.assertEqual(
            survivors["cf-hash"]["stable_hash"],
            score.stable_hash("src/a.py", "}", "t"),
        )


# --------------------------------------------------------------------------- #
# cross_confirm_group (ROBUST-02): ORDER-INDEPENDENT category-domain confirm.
# Title is dropped as a match signal (D-01); two findings confirm iff same file
# AND |line| <= 2 AND their category DOMAINS overlap. `adversarial` bridges only
# an unambiguous single co-located native domain.
# --------------------------------------------------------------------------- #
class TestCrossConfirmGroup(unittest.TestCase):
    def test_different_file_not_grouped(self):
        # Same category-domain (both security) but different files -> not grouped.
        a = make_finding(id="a", file="src/a.py", line=10, category="injection")
        b = make_finding(id="b", file="src/b.py", line=10, category="auth")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 2)

    def test_line_distance_over_2_not_grouped(self):
        # Same domain, same file, but |10-13| = 3 > 2 -> not grouped.
        a = make_finding(id="a", file="src/a.py", line=10, category="injection")
        b = make_finding(id="b", file="src/a.py", line=13, category="auth")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 2)

    def test_single_finding_single_group_one_agent_attribution(self):
        a = make_finding(id="a", file="src/a.py", line=10, category="injection",
                         agent="bugs")
        groups = score.cross_confirm_group([a])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["attribution"], ["bugs"])

    # --- Test 1: confirm, same domain ------------------------------------- #
    def test_same_domain_co_located_confirms(self):
        # line 10 & 12, injection + auth (both -> "security") => ONE group, attr 2.
        a = make_finding(id="a", file="src/a.py", line=10, category="injection",
                         agent="security")
        b = make_finding(id="b", file="src/a.py", line=12, category="auth",
                         agent="bugs")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["attribution"]), 2)

    # --- Test 2: no-confirm, different domain ----------------------------- #
    def test_different_domain_co_located_does_not_confirm(self):
        # line 10 & 11, injection (security) + perf (impact) => TWO groups.
        a = make_finding(id="a", file="src/a.py", line=10, category="injection",
                         agent="security")
        b = make_finding(id="b", file="src/a.py", line=11, category="perf",
                         agent="impact")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 2)

    # --- Test 3: title game is dead --------------------------------------- #
    def test_identical_title_different_domain_not_grouped(self):
        # IDENTICAL title but injection (security) + duplication (design) -> TWO
        # groups. A shared title token alone can NEVER fire a confirmation (D-01).
        a = make_finding(id="a", file="src/a.py", line=10, title="SQL injection",
                         category="injection", agent="security")
        b = make_finding(id="b", file="src/a.py", line=11, title="SQL injection",
                         category="duplication", agent="design")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 2)

    # --- Test 4: security <-> adversarial confirm ------------------------- #
    def test_security_and_adversarial_co_located_confirm(self):
        # auth (security) + adversarial at line 10 & 12 => ONE group, attr 2,
        # for EVERY input ordering (order-independent bridge).
        a = make_finding(id="a", file="src/a.py", line=10, category="auth",
                         agent="security")
        b = make_finding(id="b", file="src/a.py", line=12, category="adversarial",
                         agent="codex-adversarial")
        for perm in itertools.permutations([a, b]):
            groups = score.cross_confirm_group(list(perm))
            with self.subTest(perm=[f["id"] for f in perm]):
                self.assertEqual(len(groups), 1)
                self.assertEqual(len(groups[0]["attribution"]), 2)
                self.assertEqual(
                    sorted(groups[0]["attribution"]),
                    ["codex-adversarial", "security"],
                )

    def test_injection_and_adversarial_confirm_every_ordering(self):
        # injection (security) + adversarial co-located DO confirm (attr 2) for
        # every ordering (acceptance-criteria explicit case).
        a = make_finding(id="a", file="src/a.py", line=10, category="injection",
                         agent="security")
        b = make_finding(id="b", file="src/a.py", line=11, category="adversarial",
                         agent="codex-adversarial")
        for perm in itertools.permutations([a, b]):
            groups = score.cross_confirm_group(list(perm))
            with self.subTest(perm=[f["id"] for f in perm]):
                self.assertEqual(len(groups), 1)
                self.assertEqual(len(groups[0]["attribution"]), 2)

    # --- Test 5: D-02 missing category = NON-overlap ---------------------- #
    def test_missing_category_co_located_does_not_confirm(self):
        # A missing/None/non-str category co-located with a native security
        # finding does NOT group (NON-overlap, D-02). run() does not raise.
        native = make_finding(id="sec", file="src/a.py", line=10,
                              category="injection", agent="security")
        for bad in (None, 12345, ["x"], {"k": "v"}):
            with self.subTest(bad=bad):
                other = make_finding(id="bad", file="src/a.py", line=11,
                                     category=bad, agent="bugs")
                groups = score.cross_confirm_group([native, other])
                self.assertEqual(len(groups), 2)
        # missing-key variant
        other = make_finding(id="nokey", file="src/a.py", line=11, agent="bugs")
        del other["category"]
        groups = score.cross_confirm_group([native, other])
        self.assertEqual(len(groups), 2)

    def test_unknown_category_co_located_does_not_confirm(self):
        # An unknown (not-in-map) category maps to NO domain => NON-overlap.
        native = make_finding(id="sec", file="src/a.py", line=10,
                              category="injection", agent="security")
        other = make_finding(id="unk", file="src/a.py", line=11,
                             category="totally-made-up-category", agent="bugs")
        groups = score.cross_confirm_group([native, other])
        self.assertEqual(len(groups), 2)

    # --- Test 6 (PERMUTATION / BLOCKER-2 core): ambiguous multi-domain ---- #
    def test_ambiguous_multi_domain_adversarial_bridges_nothing(self):
        # A line 10 injection (security), B line 12 adversarial, C line 14
        # duplication (design). B is co-located with BOTH A (security) and C
        # (design) — |12-14|=2 — so B sees TWO distinct native domains and
        # bridges NEITHER. A and C both emit alone, no +10, in EVERY ordering.
        a = make_finding(id="A", file="src/a.py", line=10, category="injection",
                         agent="security", agent_confidence=85, severity="critical",
                         source_window=["a", "b", "c", "d", "e"])
        b = make_finding(id="B", file="src/a.py", line=12, category="adversarial",
                         agent="codex-adversarial", agent_confidence=85,
                         severity="critical",
                         source_window=["a", "b", "c", "d", "e"])
        c = make_finding(id="C", file="src/a.py", line=14, category="duplication",
                         agent="design", agent_confidence=85, severity="critical",
                         source_window=["a", "b", "c", "d", "e"])
        for perm in itertools.permutations([a, b, c]):
            with self.subTest(perm=[f["id"] for f in perm]):
                groups = score.cross_confirm_group(list(perm))
                # No group has 2+ attribution (no cross-confirm anywhere).
                for g in groups:
                    self.assertLess(len(g["attribution"]), 2)
                # Through run(): A and C both survive (>=70), neither absorbed,
                # neither +10'd. B (adversarial, no bridge) also survives alone.
                envelope = {
                    "command": "deep-review",
                    "all_mode": False,
                    "pass_number": 1,
                    "changed_line_ranges": {},
                    "carryforward": [],
                    "findings": list(perm),
                }
                result = score.run(envelope)
                ids = {g["id"]: g for g in result["findings"]}
                self.assertIn("A", ids)
                self.assertIn("C", ids)
                # No +10: A's score is exactly its lone value (85 +0 critical = 85).
                self.assertEqual(ids["A"]["orchestrator_score"], 85)
                self.assertEqual(ids["C"]["orchestrator_score"], 85)
                # Attribution on each survivor is single-agent (no cross-confirm).
                self.assertLess(len(ids["A"]["attribution"]), 2)
                self.assertLess(len(ids["C"]["attribution"]), 2)

    def test_single_co_located_domain_adversarial_bridges_every_ordering(self):
        # A line 10 injection (security), B line 11 adversarial, C line 20
        # duplication (design, FAR away — not co-located with anything). B is
        # co-located with ONLY ONE native domain (A's security) => A<->B confirm
        # in EVERY ordering; C always emits alone.
        a = make_finding(id="A", file="src/a.py", line=10, category="injection",
                         agent="security", agent_confidence=85, severity="critical",
                         source_window=["a", "b", "c", "d", "e"])
        b = make_finding(id="B", file="src/a.py", line=11, category="adversarial",
                         agent="codex-adversarial", agent_confidence=85,
                         severity="critical",
                         source_window=["a", "b", "c", "d", "e"])
        c = make_finding(id="C", file="src/a.py", line=20, category="duplication",
                         agent="design", agent_confidence=85, severity="critical",
                         source_window=["a", "b", "c", "d", "e"])
        for perm in itertools.permutations([a, b, c]):
            with self.subTest(perm=[f["id"] for f in perm]):
                groups = score.cross_confirm_group(list(perm))
                # Exactly one group has 2+ attribution: the A<->B confirm.
                confirmed = [g for g in groups if len(g["attribution"]) >= 2]
                self.assertEqual(len(confirmed), 1)
                self.assertEqual(
                    sorted(confirmed[0]["attribution"]),
                    ["codex-adversarial", "security"],
                )
                # Through run(): A is cross-confirmed (85 +10 = 95), C emits alone.
                envelope = {
                    "command": "deep-review",
                    "all_mode": False,
                    "pass_number": 1,
                    "changed_line_ranges": {},
                    "carryforward": [],
                    "findings": list(perm),
                }
                result = score.run(envelope)
                ids = {g["id"]: g for g in result["findings"]}
                # A survives with the +10 cross-confirm (B absorbed into A's group).
                self.assertIn("A", ids)
                self.assertEqual(ids["A"]["orchestrator_score"], 95)
                self.assertEqual(len(ids["A"]["attribution"]), 2)
                # C is unrelated, emits alone with no +10.
                self.assertIn("C", ids)
                self.assertEqual(ids["C"]["orchestrator_score"], 85)
                self.assertLess(len(ids["C"]["attribution"]), 2)

    # --- W1 (a): multi-adversarial relay must NOT bridge ------------------ #
    def test_second_adversarial_does_not_relay_via_first_every_ordering(self):
        # native@10 (security), adv1@11 (1 away from native -> bridges),
        # adv2@13 (3 away from native, but only 2 away from adv1). adv2 must NOT
        # relay-bridge into the native via adv1 — proximity is measured against
        # NATIVE-origin members only, so |13-10|=3>2 means adv2 stands alone with
        # NO spurious +10, in EVERY input ordering.
        native = make_finding(id="N", file="src/a.py", line=10,
                              category="injection", agent="security",
                              agent_confidence=85, severity="critical",
                              source_window=["a", "b", "c", "d", "e"])
        adv1 = make_finding(id="A1", file="src/a.py", line=11,
                            category="adversarial", agent="codex-adversarial",
                            agent_confidence=85, severity="critical",
                            source_window=["a", "b", "c", "d", "e"])
        adv2 = make_finding(id="A2", file="src/a.py", line=13,
                            category="adversarial", agent="codex-adversarial",
                            agent_confidence=85, severity="critical",
                            source_window=["a", "b", "c", "d", "e"])
        for perm in itertools.permutations([native, adv1, adv2]):
            with self.subTest(perm=[f["id"] for f in perm]):
                groups = score.cross_confirm_group(list(perm))
                # Locate the group containing the native finding.
                native_group = next(
                    g for g in groups if any(m["id"] == "N" for m in g["members"])
                )
                # adv2 is NOT a member of the native's group (no relay).
                member_ids = {m["id"] for m in native_group["members"]}
                self.assertNotIn("A2", member_ids)
                # adv1 DID bridge (1 away) -> native group attribution is 2.
                self.assertIn("A1", member_ids)
                self.assertEqual(
                    sorted(native_group["attribution"]),
                    ["codex-adversarial", "security"],
                )
                # Through run(): native gets exactly ONE +10 (85+10=95). adv2
                # stands alone, NO +10 (85). Order-independent.
                envelope = {
                    "command": "deep-review",
                    "all_mode": False,
                    "pass_number": 1,
                    "changed_line_ranges": {},
                    "carryforward": [],
                    "findings": list(perm),
                }
                result = score.run(envelope)
                ids = {g["id"]: g for g in result["findings"]}
                self.assertIn("N", ids)
                self.assertEqual(ids["N"]["orchestrator_score"], 95)
                self.assertIn("A2", ids)
                self.assertEqual(ids["A2"]["orchestrator_score"], 85)
                self.assertLess(len(ids["A2"]["attribution"]), 2)

    # --- W1 (b): one domain across two disconnected components, deterministic #
    def test_single_domain_two_components_adversarial_deterministic(self):
        # security@10 and security@14 are the SAME domain but |10-14|=4>2, so
        # they are TWO disconnected native components. adv@12 is co-located with
        # BOTH (|12-10|=2 and |12-14|=2). Even though there is ONE domain, it is
        # split across two components, so WHICH one would get the +10 is
        # ambiguous -> DROP the bridge (consistent with the multi-domain
        # ambiguity drop). The SAME deterministic outcome must hold in EVERY
        # ordering: no group has 2+ attribution; both natives emit alone (85),
        # adv emits alone (85).
        s10 = make_finding(id="S10", file="src/a.py", line=10,
                           category="injection", agent="security",
                           agent_confidence=85, severity="critical",
                           source_window=["a", "b", "c", "d", "e"])
        s14 = make_finding(id="S14", file="src/a.py", line=14,
                           category="auth", agent="security",
                           agent_confidence=85, severity="critical",
                           source_window=["a", "b", "c", "d", "e"])
        adv = make_finding(id="ADV", file="src/a.py", line=12,
                           category="adversarial", agent="codex-adversarial",
                           agent_confidence=85, severity="critical",
                           source_window=["a", "b", "c", "d", "e"])
        for perm in itertools.permutations([s10, s14, adv]):
            with self.subTest(perm=[f["id"] for f in perm]):
                groups = score.cross_confirm_group(list(perm))
                # No cross-confirm anywhere (ambiguous => +10 dropped).
                for g in groups:
                    self.assertLess(len(g["attribution"]), 2)
                # Through run(): both natives + the adv all emit alone at 85,
                # deterministically, in every ordering.
                envelope = {
                    "command": "deep-review",
                    "all_mode": False,
                    "pass_number": 1,
                    "changed_line_ranges": {},
                    "carryforward": [],
                    "findings": list(perm),
                }
                result = score.run(envelope)
                ids = {g["id"]: g for g in result["findings"]}
                self.assertIn("S10", ids)
                self.assertIn("S14", ids)
                self.assertIn("ADV", ids)
                self.assertEqual(ids["S10"]["orchestrator_score"], 85)
                self.assertEqual(ids["S14"]["orchestrator_score"], 85)
                self.assertEqual(ids["ADV"]["orchestrator_score"], 85)
                self.assertLess(len(ids["S10"]["attribution"]), 2)
                self.assertLess(len(ids["S14"]["attribution"]), 2)
                self.assertLess(len(ids["ADV"]["attribution"]), 2)

    # --- Test 7: defensive — category=None through run() ------------------ #
    def test_none_category_flows_through_run_without_raising(self):
        f = make_finding(id="none-cat", category=None, agent_confidence=85,
                         severity="critical", line=10,
                         source_window=["a", "b", "c", "d", "e"])
        envelope = {
            "command": "deep-review",
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {"src/a.py": [[8, 14]]},
            "carryforward": [],
            "findings": [f],
        }
        result = score.run(envelope)  # must not raise
        self.assertTrue(result["scored_by_script"])
        ids = {g["id"]: g for g in result["findings"]}
        self.assertIn("none-cat", ids)


# --------------------------------------------------------------------------- #
# _categories_overlap (ROBUST-02) — the domain-overlap predicate in isolation
# --------------------------------------------------------------------------- #
class TestCategoriesOverlap(unittest.TestCase):
    def test_same_domain_overlaps(self):
        # Both map to "security".
        self.assertTrue(score._categories_overlap("injection", "auth"))

    def test_different_domain_does_not_overlap(self):
        # security vs impact.
        self.assertFalse(score._categories_overlap("injection", "perf"))

    def test_missing_or_non_str_is_non_overlap(self):
        # D-02: missing/None/non-str/unknown -> NON-overlap, never raises.
        for bad in (None, 5, ["x"], {"k": 1}, "unknown-cat"):
            with self.subTest(bad=bad):
                self.assertFalse(score._categories_overlap(bad, "injection"))
                self.assertFalse(score._categories_overlap("injection", bad))

    def test_adversarial_is_not_a_wildcard_domain(self):
        # `adversarial` is NOT given a domain in the map; it is handled by the
        # separate bridge, so _categories_overlap('adversarial', X) is False.
        self.assertFalse(score._categories_overlap("adversarial", "injection"))
        self.assertFalse(score._categories_overlap("adversarial", "adversarial"))

    def test_test_coverage_is_standalone(self):
        # test-sufficiency's only category (`test-coverage`) is deliberately NOT
        # in CATEGORY_DOMAIN: it stands on its own score and must NEVER
        # cross-confirm with (and thereby absorb) a co-located finding from
        # another agent. Regression lock for the v2.5 integration-check
        # observation — if a future edit added `test-coverage` to the domain
        # map, this fails loudly instead of silently shipping a spurious +10.
        self.assertIsNone(score._category_domain("test-coverage"))
        for other in ("null-access", "injection", "type-safety", "perf",
                      "test-coverage"):
            with self.subTest(other=other):
                self.assertFalse(
                    score._categories_overlap("test-coverage", other))

    def test_react_hooks_twin_cross_confirms_others_standalone(self):
        # framework-react cross-confirm policy (v2.5): ONLY the genuine
        # cross-agent twins are mapped — `hooks` (twin of language-typescript's
        # `react-hook`, both "style") and `perf` (twin of `perf`, both
        # "impact"). The non-twin React-idiom categories `rendering`,
        # `controlled-uncontrolled`, `a11y` are deliberately UNMAPPED so a
        # distinct React finding can never be folded into the broad "style"
        # bucket and silently absorb an unrelated co-located TS style finding.
        # Locks the corrected (tightened) behavior so a future re-broadening
        # regresses loudly.
        self.assertTrue(score._categories_overlap("hooks", "react-hook"))   # headline twin
        self.assertTrue(score._categories_overlap("perf", "perf"))          # impact twin
        for standalone in ("rendering", "controlled-uncontrolled", "a11y"):
            with self.subTest(standalone=standalone):
                self.assertIsNone(score._category_domain(standalone))
                # must NOT overlap an unrelated co-located TS "style" finding
                self.assertFalse(
                    score._categories_overlap(standalone, "type-safety"))

    def test_framework_express_categories_standalone(self):
        # framework-express no-twin policy (v2.7, D-05): ALL SIX Express
        # categories are deliberately UNMAPPED in CATEGORY_DOMAIN — none has a
        # genuine cross-agent twin this phase, so each resolves to None and
        # stands on its own honest score. Adding a twin would let an Express
        # finding spuriously confirm — and silently absorb — an unrelated
        # co-located finding from a native domain. This is the regression lock:
        # if a future edit maps any of the six to a domain, this fails loudly.
        # The first v2.7 twin lands in Phase 27 (electron ipc-validation ->
        # security), NOT here. (framework-express)
        express_categories = (
            "middleware-order", "async-errors", "error-disclosure",
            "security-headers", "input-validation", "request-lifecycle",
        )
        for c in express_categories:
            with self.subTest(category=c):
                # no twin: resolves to no domain
                self.assertIsNone(score._category_domain(c))
                # never spuriously confirms a native security finding
                self.assertFalse(score._categories_overlap(c, "injection"))
                # never spuriously confirms a native impact finding
                self.assertFalse(score._categories_overlap(c, "perf"))

    def test_framework_vue_categories_standalone(self):
        # framework-vue no-twin policy (v2.7, D-05): ALL FIVE Vue categories
        # are deliberately UNMAPPED in CATEGORY_DOMAIN — none has a genuine
        # cross-agent twin this phase, so each resolves to None and stands on
        # its own honest score. Adding a twin would let a Vue finding spuriously
        # confirm — and silently absorb — an unrelated co-located finding from a
        # native domain. This is the regression lock: if a future edit maps any
        # of the five to a domain, this fails loudly. The first v2.7 twin lands
        # in Phase 27 (electron ipc-validation -> security), NOT here.
        # (framework-vue)
        vue_categories = (
            "reactivity", "composition-api", "lifecycle-cleanup",
            "template", "props",
        )
        for c in vue_categories:
            with self.subTest(category=c):
                # no twin: resolves to no domain
                self.assertIsNone(score._category_domain(c))
                # never spuriously confirms a native security finding
                self.assertFalse(score._categories_overlap(c, "injection"))
                # never spuriously confirms a native impact finding
                self.assertFalse(score._categories_overlap(c, "perf"))

    def test_framework_angular_categories_standalone(self):
        # framework-angular no-twin policy (v2.7, D-06): ALL FIVE Angular
        # categories are deliberately UNMAPPED in CATEGORY_DOMAIN — none has a
        # genuine cross-agent twin this phase, so each resolves to None and
        # stands on its own honest score. Adding a twin would let an Angular
        # finding spuriously confirm — and silently absorb — an unrelated
        # co-located finding from a native domain. This is the regression lock:
        # if a future edit maps any of the five to a domain, this fails loudly.
        # The first v2.7 twin lands in Phase 27 (electron ipc-validation ->
        # security), NOT here. (framework-angular)
        #
        # `lifecycle` subtlety: the generic word `lifecycle` is NOT a
        # CATEGORY_DOMAIN key (only the unmapped `lifecycle-background` appears,
        # in a comment) — the assertIsNone line locks it resolves to None.
        angular_categories = (
            "rxjs-leaks", "change-detection", "di-scope",
            "lifecycle", "rxjs-composition",
        )
        for c in angular_categories:
            with self.subTest(category=c):
                # no twin: resolves to no domain
                self.assertIsNone(score._category_domain(c))
                # never spuriously confirms a native security finding
                self.assertFalse(score._categories_overlap(c, "injection"))
                # never spuriously confirms a native impact finding
                self.assertFalse(score._categories_overlap(c, "perf"))


# --------------------------------------------------------------------------- #
# GOLDEN sha256 stable_hash (MANDATORY — T-16-01)
# --------------------------------------------------------------------------- #
class TestStableHashGolden(unittest.TestCase):
    def test_golden_digest_frozen(self):
        # Frozen literal — any separator/encoding/field-order drift fails here.
        # Recipe: sha256((file + "\x00" + canonical_line_content + "\x00" + title))
        # Separator is NUL (M1): the old "\n" separator was forgeable (collision),
        # so the digest was re-pinned when the separator changed.
        self.assertEqual(
            score.stable_hash("a.py", "  x=1", "title"),
            GOLDEN_DIGEST,
        )

    def test_hash_is_deterministic(self):
        h1 = score.stable_hash("f.py", "code", "t")
        h2 = score.stable_hash("f.py", "code", "t")
        self.assertEqual(h1, h2)

    def test_field_order_matters(self):
        # Swapping file and title must change the digest (proves order is fixed).
        self.assertNotEqual(
            score.stable_hash("a.py", "  x=1", "title"),
            score.stable_hash("title", "  x=1", "a.py"),
        )


# --------------------------------------------------------------------------- #
# AST import-set assertion (finding #5 / T-16-03) — enforce the import ban
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "hashlib", "re", "sys"}
    FORBIDDEN_NAMES = {"subprocess", "os", "pathlib", "shutil", "glob",
                       "difflib", "eval", "exec", "compile", "__import__",
                       "open"}

    def _tree(self):
        with open(SCORE_PY, "r", encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_import_set_subset_of_allowed(self):
        tree = self._tree()
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        self.assertTrue(
            imported.issubset(self.ALLOWED),
            "score.py imports outside {json,hashlib,re,sys}: "
            + str(imported - self.ALLOWED),
        )

    def test_no_forbidden_module_imported(self):
        tree = self._tree()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    self.assertNotIn(top, self.FORBIDDEN_NAMES)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    self.assertNotIn(top, self.FORBIDDEN_NAMES)

    def test_no_forbidden_calls_or_attributes(self):
        # Walk Call/Name/Attribute nodes for os.*, subprocess, open(, eval(,
        # exec(, compile(, __import__. (AST ignores string/comment tokens.)
        tree = self._tree()
        banned_call_names = {"eval", "exec", "compile", "__import__", "open"}
        banned_attr_roots = {"os", "subprocess", "pathlib", "shutil", "glob"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Name):
                    self.assertNotIn(fn.id, banned_call_names,
                                     "forbidden call: " + fn.id)
            if isinstance(node, ast.Attribute):
                # Catch os.path / os.listdir / subprocess.run etc.
                val = node.value
                if isinstance(val, ast.Name):
                    self.assertNotIn(val.id, banned_attr_roots,
                                     "forbidden attribute access on: " + val.id)


# --------------------------------------------------------------------------- #
# MALFORMED-STDIN fail-closed (finding #1 / T-16-02)
# --------------------------------------------------------------------------- #
class TestFailClosed(unittest.TestCase):
    def test_invalid_json_stdin_exits_nonzero(self):
        # Pipe garbage to `python3 score.py`; the process MUST exit non-zero so
        # the orchestrator's fail-closed gate (16-02) can fail the review closed.
        proc = subprocess.run(
            [sys.executable, SCORE_PY],
            input=b"not json",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,  # Gap A: bound the child so a hang fails the test, not stalls CI
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_empty_stdin_exits_nonzero(self):
        proc = subprocess.run(
            [sys.executable, SCORE_PY],
            input=b"",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,  # Gap A: bound the child so a hang fails the test, not stalls CI
        )
        self.assertNotEqual(proc.returncode, 0)


# --------------------------------------------------------------------------- #
# run(envelope) end-to-end
# --------------------------------------------------------------------------- #
class TestRunEndToEnd(unittest.TestCase):
    def _envelope(self, **over):
        base = {
            "command": "review",
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {"src/a.py": [[8, 14]]},
            "carryforward": [],
            "findings": [
                make_finding(id="keep-1", agent_confidence=85, severity="critical",
                             line=10, source_window=["a", "b", "c", "d", "e"]),
            ],
        }
        base.update(over)
        return base

    def test_sentinel_stamped(self):
        result = score.run(self._envelope())
        self.assertTrue(result["scored_by_script"])

    def test_survivor_carries_scored_fields(self):
        result = score.run(self._envelope())
        self.assertEqual(len(result["findings"]), 1)
        g = result["findings"][0]
        # in_diff recomputed (line 10 in [8,14]) -> 85 + 20 = 105 -> clamp 100.
        self.assertEqual(g["orchestrator_score"], 100)
        self.assertEqual(g["band"], "critical")
        self.assertIn("stable_hash", g)
        self.assertIn("attribution", g)

    def test_input_fields_preserved_verbatim(self):
        result = score.run(self._envelope())
        g = result["findings"][0]
        for field in ("id", "file", "line", "title", "category", "severity",
                      "problem", "current_code", "why_it_matters"):
            self.assertIn(field, g)

    def test_in_diff_recomputed_overrides_agent_claim(self):
        # Agent self-reports in_diff True, but line 99 is NOT in [8,14]; the
        # script overrides and the +20 does not apply (hard rule #4).
        f = make_finding(id="ood", agent_confidence=85, severity="critical",
                         line=99, in_diff=True,
                         source_window=["a", "b", "c", "d", "e"])
        result = score.run(self._envelope(findings=[f]))
        # 85, no +20 -> 85 still passes /review (>=80). Score must be 85 not 105.
        self.assertEqual(result["findings"][0]["orchestrator_score"], 85)

    def test_fixed_since_last_excluded_from_findings(self):
        # A carryforward finding whose file:line is gone -> fixed-since-last,
        # excluded from reported findings, surfaced in fixed_since_last[].
        cf = make_finding(id="cf-gone", file="src/a.py", line=10,
                          title="old bug", current_code="  gone",
                          canonical_line_content=None)
        result = score.run(self._envelope(carryforward=[cf], findings=[]))
        self.assertNotIn("cf-gone", [g["id"] for g in result["findings"]])
        self.assertTrue(len(result["fixed_since_last"]) >= 1)

    def test_persisted_carryforward_gets_plus_15(self):
        # A carryforward finding whose canonical content still matches ->
        # persisted, +15, included.
        cf = make_finding(id="cf-keep", file="src/a.py", line=10,
                          title="still here", agent_confidence=60,
                          severity="critical", current_code="  return q",
                          canonical_line_content="return q",
                          source_window=["a", "b", "c", "d", "e"])
        # line 10 in [8,14] -> in_diff +20; +15 persisted; conf 60 = 95 -> critical.
        result = score.run(self._envelope(carryforward=[cf], findings=[]))
        survivors = {g["id"]: g for g in result["findings"]}
        self.assertIn("cf-keep", survivors)
        self.assertEqual(survivors["cf-keep"]["status"], "persisted")
        self.assertEqual(survivors["cf-keep"]["orchestrator_score"], 95)


# --------------------------------------------------------------------------- #
# C1 — float agent_confidence must NOT be silently zeroed (deep-review C1)
# --------------------------------------------------------------------------- #
class TestFloatConfidence(unittest.TestCase):
    def test_float_confidence_scores_same_as_int(self):
        # 85.0 (float, as JSON from LLM agents routinely carries) must score
        # identically to 85 (int) — not get coerced to 0 by an isinstance int check.
        f_float = make_finding(agent_confidence=85.0, severity="critical")
        f_int = make_finding(agent_confidence=85, severity="critical")
        self.assertEqual(score_of(f_float), score_of(f_int))
        self.assertEqual(score_of(f_float), 85)

    def test_fractional_float_truncated_to_int(self):
        # A fractional float is accepted (not zeroed); truncated via int().
        f = make_finding(agent_confidence=85.9, severity="critical")
        self.assertEqual(score_of(f), 85)

    def test_bool_confidence_rejected_to_zero(self):
        # bool is an int subclass; True must NOT count as confidence 1 — it is
        # rejected to 0 (then severity critical +0 -> 0).
        f_true = make_finding(agent_confidence=True, severity="critical")
        self.assertEqual(score_of(f_true), 0)
        f_false = make_finding(agent_confidence=False, severity="critical")
        self.assertEqual(score_of(f_false), 0)


# --------------------------------------------------------------------------- #
# W1 — stable_hash is None-safe; a null title must not halt the whole review
# --------------------------------------------------------------------------- #
class TestStableHashNoneSafe(unittest.TestCase):
    def test_none_arg_equals_empty_string_arg(self):
        # A None field hashes identically to "" for that field (no crash).
        self.assertEqual(
            score.stable_hash(None, "  x=1", "title"),
            score.stable_hash("", "  x=1", "title"),
        )
        self.assertEqual(
            score.stable_hash("a.py", None, "title"),
            score.stable_hash("a.py", "", "title"),
        )
        self.assertEqual(
            score.stable_hash("a.py", "  x=1", None),
            score.stable_hash("a.py", "  x=1", ""),
        )

    def test_all_none_does_not_raise(self):
        # Returns a valid hex digest rather than raising TypeError.
        h = score.stable_hash(None, None, None)
        self.assertEqual(len(h), 64)

    def test_null_title_finding_flows_through_run_without_raising(self):
        # A malformed-but-parseable finding with title=null must NOT crash run()
        # (which would propagate non-zero and trip the orchestrator fail-closed
        # halt on the entire review).
        f = make_finding(id="null-title", title=None, agent_confidence=85,
                         severity="critical", line=10,
                         source_window=["a", "b", "c", "d", "e"])
        envelope = {
            "command": "deep-review",
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {"src/a.py": [[8, 14]]},
            "carryforward": [],
            "findings": [f],
        }
        result = score.run(envelope)  # must not raise
        self.assertTrue(result["scored_by_script"])
        # It survived scoring and carries a stable_hash computed with title="".
        survivors = {g["id"]: g for g in result["findings"]}
        self.assertIn("null-title", survivors)
        self.assertIn("stable_hash", survivors["null-title"])

    def test_non_string_current_code_does_not_crash_first_line(self):
        # _first_line must coerce a non-string (a JSON number) to '' rather than
        # raising AttributeError — otherwise a single malformed-but-parseable
        # finding crashes run() and trips the fail-closed halt on the whole
        # review (completes W1 for the current_code sibling field).
        self.assertEqual(score._first_line(5), "")
        self.assertEqual(score._first_line({"x": 1}), "")
        self.assertEqual(score._first_line(None), "")
        self.assertEqual(score._first_line("a\nb"), "a")

    def test_numeric_current_code_finding_flows_through_run(self):
        f = make_finding(id="num-cc", title="real bug", agent_confidence=85,
                         severity="critical", line=10,
                         source_window=["a", "b", "c", "d", "e"])
        f["current_code"] = 12345  # non-string (schema drift / LLM quirk)
        envelope = {
            "command": "deep-review",
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {"src/a.py": [[8, 14]]},
            "carryforward": [],
            "findings": [f],
        }
        result = score.run(envelope)  # must not raise
        self.assertTrue(result["scored_by_script"])
        # Gap B (tightened): assert the OUTCOME, not merely "did not raise". A
        # non-string current_code is an already-safe shape (_first_line coerces it
        # to "" for the hash) — the finding is KEPT and scored, so it must survive
        # in result["findings"] (conf 85 + critical, line 10 in [8,14] -> 100).
        self.assertIn("num-cc", [g["id"] for g in result["findings"]])


# --------------------------------------------------------------------------- #
# M1 — NUL separator: new golden pinned + the newline collision is gone
# --------------------------------------------------------------------------- #
class TestStableHashSeparatorCollision(unittest.TestCase):
    def test_new_golden_digest_pinned(self):
        # Distinct intent from test_golden_digest_frozen: this class (M1) asserts
        # the NUL-separator re-pin specifically. Both reference the single
        # GOLDEN_DIGEST source-of-truth literal (Gap C de-dup).
        self.assertEqual(
            score.stable_hash("a.py", "  x=1", "title"),
            GOLDEN_DIGEST,
        )

    def test_newline_separator_collision_no_longer_occurs(self):
        # Under the old "\n" separator these two inputs collided:
        #   ('a.py','x','y\nz')  ==  ('a.py','x\ny','z')
        # With the NUL separator they must differ (NUL cannot appear in the fields).
        self.assertNotEqual(
            score.stable_hash("a.py", "x", "y\nz"),
            score.stable_hash("a.py", "x\ny", "z"),
        )


# --------------------------------------------------------------------------- #
# W2 — explicit line:null must not crash grouping or the diff/range checks
# --------------------------------------------------------------------------- #
class TestNullLineDefensive(unittest.TestCase):
    def test_null_line_finding_flows_through_run_without_raising(self):
        # A file-level finding legitimately carries line=null; run() must not
        # crash on abs(None - 0) or `1 <= None <= n`.
        f = make_finding(id="file-level", line=None, agent_confidence=85,
                         severity="critical",
                         source_window=["a", "b", "c", "d", "e"])
        envelope = {
            "command": "deep-review",
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": {"src/a.py": [[8, 14]]},
            "carryforward": [],
            "findings": [f],
        }
        result = score.run(envelope)  # must not raise
        self.assertTrue(result["scored_by_script"])
        # Gap B (tightened): assert the OUTCOME. A null line is not a usable diff
        # coordinate (no +20), but conf 85 + critical = 85 >= 70 (deep-review), so
        # the file-level finding is KEPT and must survive in result["findings"].
        self.assertIn("file-level", [g["id"] for g in result["findings"]])

    def test_two_null_line_findings_do_not_group_on_line(self):
        # Two null-line findings in the same file with OVERLAPPING category
        # domains (both security) must STILL NOT group — a null line is not a
        # usable ±2 coordinate, so line-gating alone prevents the grouping even
        # when the domains would otherwise overlap.
        a = make_finding(id="a", file="src/a.py", line=None, category="injection",
                         agent="bugs")
        b = make_finding(id="b", file="src/a.py", line=None, category="auth",
                         agent="security")
        groups = score.cross_confirm_group([a, b])
        self.assertEqual(len(groups), 2)

    def test_line_in_ranges_null_line_is_out_of_range(self):
        self.assertFalse(score._line_in_ranges(None, [[1, 100]]))

    def test_all_mode_null_line_not_in_reviewed_set(self):
        # In --all mode with a known file line total, a null-line finding fails
        # the 1<=line<=N bound (out of range) instead of raising.
        f = make_finding(id="al", file="src/a.py", line=None,
                         agent_confidence=85, severity="critical",
                         source_window=["a", "b", "c", "d", "e"])
        envelope = {
            "command": "deep-review",
            "all_mode": True,
            "pass_number": 1,
            "reviewed_union": ["src/a.py"],
            "file_line_totals": {"src/a.py": 50},
            "changed_line_ranges": {},
            "carryforward": [],
            "findings": [f],
        }
        result = score.run(envelope)  # must not raise
        self.assertNotIn("al", [g["id"] for g in result["findings"]])


# --------------------------------------------------------------------------- #
# SINGLE-WRITER REGRESSION-LOCK (ROBUST-01 D-10, Phase 17)
#
# score.py is the SINGLE writer of the scored fields
# (orchestrator_score/band/status/stable_hash/attribution). review.md:830 names
# it the single writer and forbids a by-hand hash. This lock FAILS if a future
# edit reintroduces a by-hand scored-field WRITE PATH into review.md/deep-review.md
# — whether as a fenced machine assignment or as UNFENCED prose (this orchestrator
# follows prose directives throughout the file).
#
# The guard scans the ENTIRE file text (NOT fenced-only). It is BOTH:
#   * SOUND — it must NOT false-positive on the legitimate, non-scored
#     SCOPE_HASH `shasum` (a state-file-path hash, review.md:392), nor on the
#     many legitimate scored-field MENTIONS / comparisons / reads / forbidding
#     prose ("band == medium", "consume the stable_hash", "do NOT recompute …").
#   * COMPLETE — it must CATCH a reintroduced writer, including an unfenced prose
#     directive ("compute stable_hash with sha256", "set band to critical") and a
#     hasher tied to a scored field.
#
# Tie requirement (the BLOCKER-3 round-2 fix): a hasher token is flagged ONLY
# when it co-occurs (same clause) with a scored-field token. A hasher with no
# scored-field reference (the SCOPE_HASH line references SCOPE_HASH/ALL_STATE_FILE,
# never `stable_hash`) is ALLOWED.
# --------------------------------------------------------------------------- #
# A scored-field token. `band`/`status` are common English words → word
# boundaries; the others are distinctive identifiers.
_SCORED_FIELD_RE = re.compile(
    r"(?:orchestrator_score|stable_hash|attribution|\bband\b|\bstatus\b)"
)
# Hasher tokens (the by-hand-hash surface ROBUST-01 forbids).
_HASHER_RE = re.compile(
    r"\b(?:sha256|sha-256|shasum|openssl\s+dgst|md5|hashlib)\b", re.I
)
# Imperative WRITE verbs (a by-hand synthesis directive). READ/compare verbs
# (consume/read/render/score/count) are deliberately EXCLUDED.
_WRITE_VERBS = r"set|compute|recompute|write|assign|synthesize|synthesise|derive"

# Negated / forbidding / without-clauses EXEMPT a clause: the file legitimately
# FORBIDS by-hand writes (review.md:676 "does NOT assign status", :830 "do NOT
# recompute the sha256 by hand", :672 "no longer a manual path"). A negated
# directive is the OPPOSITE of a reintroduced writer.
_NEG_RE = re.compile(
    r"\b(?:do not|do n't|don't|does not|doesn't|did not|didn't|"
    r"never|no longer|not\b|cannot|can't|must not|mustn't|"
    r"forbid|forbidden|forbids|without|no by-hand|"
    r"would create|would be|reintroduc)\b",
    re.I,
)
# Machine-assignment form: a scored field IMMEDIATELY followed by `=` then a
# COMPUTED value (a quote / shell substitution / hasher expr). Catches
#   band="critical" / orchestrator_score=$((conf+20)) / stable_hash="$H"
# but NOT band=critical (bare word — the :64 read filter), NOT band == medium
# (comparison), NOT medium_acknowledgments[stable_hash] = … (the `]` breaks the
# field-immediately-before-`=` requirement, so the write target is the dict, not
# the scored field).
_ASSIGN_RE = re.compile(
    r"(?:orchestrator_score|stable_hash|attribution|band|status)"
    r"\s*=\s*"
    r"(?:\"|'|\$\(|\$\{|[A-Za-z0-9_]*\s*(?:sha256|shasum|md5|hashlib))"
)
# Prose-directive form: a WRITE verb whose DIRECT OBJECT is a scored field
# (`<verb> [the/a/an] <field>`). The field must be the object adjacent to the
# verb, so "write medium_acknowledgments[stable_hash]" (object = the dict),
# "the row's band derives from" (no scored field AFTER the verb), and
# "computes the canonical line content" (object = canonical content) do NOT match.
_DIRECTIVE_RE = re.compile(
    r"\b(?:" + _WRITE_VERBS + r")\b"
    r"\s+(?:the\s+|a\s+|an\s+)?"
    r"(?:orchestrator_score|stable_hash|attribution|band|status)\b",
    re.I,
)


def _writer_clauses(text):
    """Split text into small clauses so negation/tie scoping is LOCAL.

    Break on newlines, sentence terminators, and semicolons — a forbidding
    clause must not exempt a sibling write clause, and a hasher must tie to a
    scored field in the SAME clause, not merely the same paragraph.
    """
    raw = re.split(r"[\n;.]|(?<=[!?])\s", text)
    return [c.strip() for c in raw if c.strip()]


def has_scored_field_write_path(text):
    """True iff `text` contains a by-hand scored-field WRITE PATH.

    (a) scored-field SYNTHESIS — an imperative write-verb directive OR a machine
        assignment INTO a scored field (any fencing), OR
    (b) a HASHER token TIED to a scored field (same-clause co-occurrence).
    Negated / forbidding / without-clauses are EXEMPT (they FORBID, not write).
    """
    for clause in _writer_clauses(text):
        if _NEG_RE.search(clause):
            continue
        if _DIRECTIVE_RE.search(clause) or _ASSIGN_RE.search(clause):
            return True
        if _HASHER_RE.search(clause) and _SCORED_FIELD_RE.search(clause):
            return True
    return False


class TestSingleWriterLock(unittest.TestCase):
    """ROBUST-01 D-10: lock score.py as the single writer of scored fields."""

    COMMANDS_DIR = os.path.join(os.path.dirname(SCORE_PY), "..", "commands")
    REVIEW_MD = os.path.join(COMMANDS_DIR, "review.md")
    DEEP_REVIEW_MD = os.path.join(COMMANDS_DIR, "deep-review.md")

    @classmethod
    def _read(cls, path):
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()

    # -- Test 1: the lock HOLDS today (soundness on the real files) -------- #
    def test_review_md_has_no_by_hand_scored_field_write(self):
        text = self._read(self.REVIEW_MD)
        # Whole-file scan (not fenced-only). The load-bearing no-false-positive
        # proof: must NOT trip on review.md:392 SCOPE_HASH `shasum`, nor on the
        # scored-field mentions/comparisons/reads/forbidding-prose.
        self.assertFalse(
            has_scored_field_write_path(text),
            "review.md tripped the single-writer lock — a by-hand scored-field "
            "write path was detected (or a false positive on SCOPE_HASH / a "
            "scored-field mention).",
        )

    def test_deep_review_md_has_no_by_hand_scored_field_write(self):
        text = self._read(self.DEEP_REVIEW_MD)
        self.assertFalse(
            has_scored_field_write_path(text),
            "deep-review.md tripped the single-writer lock — a by-hand "
            "scored-field write path was detected.",
        )

    def test_the_real_files_actually_exist_and_were_read(self):
        # Guard against the detector silently passing on an empty/missing read.
        self.assertTrue(os.path.isfile(self.REVIEW_MD), self.REVIEW_MD)
        self.assertTrue(os.path.isfile(self.DEEP_REVIEW_MD), self.DEEP_REVIEW_MD)
        self.assertGreater(len(self._read(self.REVIEW_MD)), 1000)
        self.assertGreater(len(self._read(self.DEEP_REVIEW_MD)), 1000)
        # Both files DO mention scored fields (so the soundness proof above is
        # non-vacuous — the detector saw scored-field tokens and still passed).
        self.assertRegex(self._read(self.REVIEW_MD), r"stable_hash")
        self.assertRegex(self._read(self.REVIEW_MD), r"orchestrator_score")
        # And review.md DOES contain the legitimate SCOPE_HASH `shasum` the
        # detector must NOT flag — proving the no-false-positive is meaningful.
        self.assertIn("SCOPE_HASH", self._read(self.REVIEW_MD))
        self.assertRegex(self._read(self.REVIEW_MD), r"\| *shasum")

    # -- Test 2: the lock CATCHES reintroduction (completeness) ------------ #
    def test_catches_unfenced_prose_writers(self):
        # The round-2 evasion hole: an unfenced prose directive the orchestrator
        # would follow. Each MUST be caught.
        for fixture in (
            "Compute stable_hash with sha256 over file+content+title.",
            "Then set band to critical for any auth finding.",
            "Recompute the orchestrator_score by hand as confidence + 20.",
            "Assign attribution to the security agent manually.",
        ):
            self.assertTrue(
                has_scored_field_write_path(fixture),
                "unfenced prose writer NOT caught: " + fixture,
            )

    def test_catches_fenced_machine_writers(self):
        for fixture in (
            'band="critical"',
            "orchestrator_score=$((conf + 20))",
            # Hasher TIED to stable_hash (same clause):
            'stable_hash=$(shasum -a 256 <<<"$x")',
        ):
            self.assertTrue(
                has_scored_field_write_path(fixture),
                "fenced machine writer NOT caught: " + fixture,
            )

    def test_catches_hasher_tied_to_scored_field(self):
        # A hasher token co-occurring with a scored-field token in ONE clause
        # (the tie is same-clause by design — that same-clause requirement is
        # exactly what keeps the SCOPE_HASH line, whose clause references no
        # scored field, exempt).
        for fixture in (
            "the finding's stable_hash is the sha256 of file+content",
            "hash stable_hash with shasum over the canonical content",
        ):
            self.assertTrue(
                has_scored_field_write_path(fixture),
                "hasher tied to a scored field NOT caught: " + fixture,
            )

    # -- Test 3: NEGATIVE fixtures (soundness at unit level) --------------- #
    def test_allows_real_scope_hash_shasum_line(self):
        # The EXACT SCOPE_HASH line from review.md:392 — a hasher with NO
        # scored-field reference → ALLOWED (the load-bearing soundness proof).
        scope_hash_line = (
            "SCOPE_HASH=$(printf '%s' \"${REPO}:${BRANCH}:${SCOPE_TOKEN}\" "
            "| shasum | cut -c1-12)"
        )
        self.assertFalse(
            has_scored_field_write_path(scope_hash_line),
            "FALSE POSITIVE on the legitimate SCOPE_HASH shasum line.",
        )

    def test_allows_scored_field_mentions_reads_and_comparisons(self):
        for fixture in (
            "band == medium",
            "findings with band ∈ {critical, warning}",
            "findings with band=critical, status=fixed-since-last across all passes",
            "consume the stable_hash field score.py returned",
            "the row's band derives from that highest score",
            "each finding keeps its own band/score",
        ):
            self.assertFalse(
                has_scored_field_write_path(fixture),
                "FALSE POSITIVE on a scored-field read/mention/comparison: "
                + fixture,
            )

    def test_allows_forbidding_prose(self):
        # The explicit single-writer FORBIDDING prose (review.md:676/830) — a
        # NEGATED directive is the OPPOSITE of a reintroduced writer.
        for fixture in (
            "do NOT recompute the sha256 by hand",
            "The orchestrator does NOT assign `status`/+15 by hand",
            "there is no longer a manual path that can produce a scored finding",
            "reintroducing a by-hand hash here would create a second writer",
        ):
            self.assertFalse(
                has_scored_field_write_path(fixture),
                "FALSE POSITIVE on forbidding prose: " + fixture,
            )

    def test_allows_medium_acknowledgments_keyed_by_stable_hash(self):
        # review.md:43 writes a DIFFERENT field (medium_acknowledgments) KEYED by
        # stable_hash — the scored field is read as a key, not written.
        self.assertFalse(
            has_scored_field_write_path(
                'write `medium_acknowledgments[stable_hash] = '
                '{decision: "dismiss"}` to state root'
            )
        )


# --------------------------------------------------------------------------- #
# ENUMERATED MALFORMED-SHAPE MATRIX (HARDEN-02 / T-20-07, T-20-08, D-03)
#
# Pins every dogfood-named malformed shape (T1-T19) PLUS the two adversarial-found
# holes (T20 list-with-non-str-elements, T21 non-finite confidence) as an EXPLICIT
# regression case asserting the post-Wave-1-hardening OUTCOME — never merely "did
# not raise". This is the readable proof that a single malformed agent finding can
# no longer hard-crash a review run (the C1-C6 crash inventory + the two holes).
#
# Disposition vocabulary (locked against the live score.py + 20-01-SUMMARY):
#   * REJECT (non-dict container, C1/C2)  -> routed to result["filtered"] with
#     reason "malformed: non-dict finding"; the finding is NOT in result["findings"].
#   * KEPT-and-degraded (odd-but-safe field) -> still scored; survives in
#     result["findings"] when its score clears threshold (no crash).
#   * Envelope present-but-non-list findings/carryforward (C4/C5/C6, D-02) ->
#     FAIL CLOSED (score.run raises; python3 score.py exits non-zero).
#   * Absent/None/empty envelope -> a VALID empty review (must NOT raise).
#
# CRITICAL alignment note (20-01-SUMMARY, orchestrator mid-execution correction):
# _valid_finding rejects ONLY a non-dict member. A dict that merely MISSES /
# null-values file/title/category is NOT a malformed-reject — score.py is
# null-safe for those fields, so such a finding flows through and SCORES. Hence
# T6/T7/T8 (missing file/title/category) and T9 (empty {} dict) are KEPT-shapes
# here, NOT rejects. (Two frozen tests already lock the survival of null-title /
# null-category findings.)
# --------------------------------------------------------------------------- #
class TestMalformedInputMatrix(unittest.TestCase):
    """T1-T21 malformed-shape pinning suite — locks the Wave-1 crash guards."""

    GOOD_RANGES = {"src/a.py": [[8, 14]]}

    def _good_sibling(self, **over):
        # A high-confidence in-diff critical finding that always clears the
        # deep-review threshold (conf 85 + in_diff 20 = 105 -> clamp 100) so its
        # presence in result["findings"] is the D-03 "no-good-sibling-drop" probe.
        # `id` defaults to "keep" but is overridable via `over`.
        defaults = dict(id="keep", file="src/a.py", line=10, severity="critical",
                        agent_confidence=85, category="bug", agent="bugs",
                        source_window=["a", "b", "c", "d", "e"])
        defaults.update(over)
        return make_finding(**defaults)

    def _run(self, findings, carryforward=None, command="deep-review"):
        envelope = {
            "command": command,
            "all_mode": False,
            "pass_number": 1,
            "changed_line_ranges": self.GOOD_RANGES,
            "carryforward": carryforward if carryforward is not None else [],
            "findings": findings,
        }
        return score.run(envelope)

    def _ids(self, result):
        return [g["id"] for g in result["findings"]]

    def _reasons(self, result):
        return [f.get("reason", "") for f in result["filtered"]]

    def _assert_sibling_survives(self, result):
        # D-03: a malformed neighbour must NEVER drop the good finding too.
        self.assertIn("keep", self._ids(result))

    # --- T1-T4 / T5: NON-DICT container -> REJECT to filtered (C1, C2) -------- #
    def test_t1_t4_non_dict_finding_rejected_to_filtered(self):
        # A bare str / None / list / int finding cannot be `.get`-ed (would crash
        # run() with AttributeError, C1). It must be SKIPPED and reported to
        # result["filtered"] with a "malformed" reason; the good sibling survives.
        for label, bad in (("str", "i am a string"), ("None", None),
                           ("list", [1, 2, 3]), ("int", 99)):
            with self.subTest(shape=label):
                result = self._run([bad, self._good_sibling()])
                self.assertNotIn(bad, result["findings"])  # the malformed entry is gone
                self.assertTrue(
                    any("malformed" in r for r in self._reasons(result)),
                    "expected a 'malformed' filtered reason for " + label,
                )
                self._assert_sibling_survives(result)

    def test_t5_non_dict_carryforward_rejected_good_ones_survive(self):
        # A non-dict carryforward entry would crash cf.get(...) BEFORE the working
        # set is even assembled (C2). It is routed to filtered; a good carryforward
        # AND a good finding both survive.
        for label, bad in (("str", "bad cf"), ("None", None), ("list", [1])):
            with self.subTest(shape=label):
                good_cf = make_finding(id="cf-keep", file="src/a.py", line=10,
                                       title="still here", agent_confidence=85,
                                       severity="critical",
                                       current_code="return q",
                                       canonical_line_content="return q",
                                       source_window=["a", "b", "c", "d", "e"])
                result = self._run([self._good_sibling()],
                                   carryforward=[bad, good_cf])
                ids = self._ids(result)
                self.assertIn("cf-keep", ids)   # good carryforward kept
                self.assertIn("keep", ids)      # good finding kept
                self.assertTrue(
                    any("malformed" in r for r in self._reasons(result)),
                    "expected a 'malformed' filtered reason for cf " + label,
                )

    # --- T6/T7/T8: missing required key -> KEPT (NOT a reject) ---------------- #
    def test_t6_t7_t8_missing_required_key_is_kept_not_rejected(self):
        # Per the orchestrator correction (20-01-SUMMARY): a dict missing
        # file/title/category is NULL-SAFE and flows through to scoring — it is
        # KEPT, NOT a malformed-reject. (Locks the two frozen null-field tests.)
        for key in ("file", "title", "category"):
            with self.subTest(missing=key):
                bad = self._good_sibling(id="missing-" + key)
                del bad[key]
                result = self._run([bad, self._good_sibling()])
                # The odd finding is KEPT (scored, survives) — not in filtered as malformed.
                self.assertIn("missing-" + key, self._ids(result))
                self.assertFalse(
                    any("malformed" in r for r in self._reasons(result)),
                    "missing " + key + " must NOT be a malformed-reject",
                )
                self._assert_sibling_survives(result)

    # --- T9: empty {} dict -> flows through (a dict is NOT a non-dict) -------- #
    def test_t9_empty_dict_finding_flows_through_not_malformed_rejected(self):
        # An empty {} IS a dict, so _valid_finding does NOT reject it. It flows
        # through and is dropped (if at all) by NORMAL scoring (sub-threshold),
        # NEVER by the malformed-container guard. The good sibling survives.
        result = self._run([{}, self._good_sibling()])
        self.assertFalse(
            any("malformed" in r for r in self._reasons(result)),
            "empty {} is a dict -> must NOT be a malformed-reject",
        )
        self._assert_sibling_survives(result)

    # --- T10-T13: KEPT-and-degraded odd fields (no crash, sibling survives) --- #
    def test_t10_odd_line_types_kept(self):
        # line as str / float / bool is not a usable diff coordinate, but the
        # finding is KEPT-and-degraded (conf 85 + critical >= 70 deep-review),
        # never a reject. No crash.
        for label, lv in (("str", "10"), ("float", 10.0), ("bool", True)):
            with self.subTest(line=label):
                result = self._run([self._good_sibling(id="oddline", line=lv),
                                    self._good_sibling()])
                self.assertIn("oddline", self._ids(result))
                self._assert_sibling_survives(result)

    def test_t11_source_window_non_list_int_kept_no_crash(self):
        # C3: source_window=99 (a truthy non-list) would crash
        # `for line in source_window` with TypeError before the guard. _safe_window
        # coerces it to [] -> silenced False; the finding is KEPT, no crash.
        result = self._run([self._good_sibling(id="sw99", source_window=99),
                            self._good_sibling()])
        self.assertIn("sw99", self._ids(result))
        self._assert_sibling_survives(result)
        self.assertFalse(score.silenced_nearby(score._safe_window(99)))

    def test_t12_source_window_str_or_dict_kept(self):
        # An already-safe odd window (str / dict) normalizes to "no window"
        # (silenced False); the finding is KEPT.
        for label, sw in (("str", "not a window"), ("dict", {"x": 1})):
            with self.subTest(source_window=label):
                result = self._run(
                    [self._good_sibling(id="swodd", source_window=sw),
                     self._good_sibling()])
                self.assertIn("swodd", self._ids(result))
                self._assert_sibling_survives(result)

    def test_t13_numeric_current_code_sibling_survives(self):
        # The single-finding KEPT case is locked in
        # test_numeric_current_code_finding_flows_through_run (tightened in Task 1);
        # this adds the 2-finding D-03 sibling-survival variant.
        bad = self._good_sibling(id="num-cc")
        bad["current_code"] = 12345  # non-string
        result = self._run([bad, self._good_sibling()])
        self.assertIn("num-cc", self._ids(result))
        self._assert_sibling_survives(result)

    # --- T20: GENUINE list with non-string elements -> KEPT (HOLE 1) --------- #
    def test_t20_source_window_list_with_non_str_elements_kept(self):
        # source_window=[1, 2, 3] is a genuine LIST (passes a container-only
        # guard) whose elements crash the `marker in line` scan with TypeError —
        # the element-level hole the three original guards missed. _safe_window
        # filters to string elements -> [] -> silenced False; the finding is
        # KEPT, no crash; the good sibling survives.
        result = self._run([self._good_sibling(id="sw123", source_window=[1, 2, 3]),
                            self._good_sibling()])
        self.assertIn("sw123", self._ids(result))
        self.assertFalse(score.silenced_nearby(score._safe_window([1, 2, 3])))
        self._assert_sibling_survives(result)

    # --- T21: non-finite agent_confidence -> KEPT/no-crash, scored as 0 ------- #
    def test_t21_non_finite_confidence_no_crash_scored_as_zero(self):
        # HOLE 2: json.load accepts bare NaN/Infinity/-Infinity as floats; they
        # pass the isinstance(int,float) check, then int(float('nan')) raises
        # ValueError / int(float('inf')) raises OverflowError. The import-free
        # bound coerces them to 0. Produced via float('nan')/float('inf') (NOT
        # Python literals) — exactly the T21 attack surface.
        #
        # With confidence coerced to 0, an in-diff critical finding scores
        # 0 + 20 = 20, which is BELOW the deep-review threshold of 70 — so the
        # non-finite finding is correctly SUB-THRESHOLD-FILTERED, NOT in
        # result["findings"]. "Kept" here means NO CRASH + scored exactly like a
        # confidence-0 finding. The good (high-confidence) sibling survives.
        for label, conf in (("NaN", float("nan")), ("Infinity", float("inf")),
                           ("-Infinity", float("-inf"))):
            with self.subTest(confidence=label):
                bad = self._good_sibling(id="nf", agent_confidence=conf)
                result = self._run([bad, self._good_sibling()])  # must not raise
                self.assertTrue(result["scored_by_script"])
                # Scored as if confidence were 0 -> 20 < 70 -> sub-threshold, not
                # in findings (matches compute_score with confidence=0).
                self.assertNotIn("nf", self._ids(result))
                self.assertEqual(
                    score.compute_score(bad, in_diff=True, silenced=False,
                                        cross_confirmed=False, persisted=False),
                    score.compute_score(self._good_sibling(agent_confidence=0),
                                        in_diff=True, silenced=False,
                                        cross_confirmed=False, persisted=False),
                )
                self._assert_sibling_survives(result)

    # --- T14-T17: ENVELOPE present-but-non-list -> FAIL CLOSED (raise) -------- #
    def test_t14_findings_dict_raises(self):
        with self.assertRaises((TypeError, ValueError)):
            self._run({"file": "a.py"})

    def test_t15_findings_truthy_non_list_raises(self):
        for bad in ("oops", 5, {"x": 1}):
            with self.subTest(findings=bad):
                with self.assertRaises((TypeError, ValueError)):
                    self._run(bad)

    def test_t16_findings_falsy_non_list_raises(self):
        # The MOST important D-02 case (C6): a FALSY non-list ({}/""/0) previously
        # got silently masked into a fake "0 findings clean review" by the `or []`
        # coercion. The guard now runs BEFORE that coercion, so it MUST raise.
        for bad in ({}, "", 0):
            with self.subTest(findings=bad):
                with self.assertRaises((TypeError, ValueError)):
                    self._run(bad)

    def test_t17_carryforward_non_list_raises(self):
        # Present-but-non-list carryforward fails closed too (truthy AND falsy).
        for bad in ({"x": 1}, "oops", {}, 0):
            with self.subTest(carryforward=bad):
                with self.assertRaises((TypeError, ValueError)):
                    self._run([self._good_sibling()], carryforward=bad)

    def test_t16_black_box_non_list_findings_exits_nonzero(self):
        # Black-box: the fail-closed raise must propagate through the __main__ shim
        # to a NON-ZERO exit so the orchestrator's fail-closed gate can fail the
        # review closed. timeout= bounds the child (Gap A consistency, T-20-05).
        proc = subprocess.run(
            [sys.executable, SCORE_PY],
            input=b'{"command": "deep-review", "findings": {}, "carryforward": []}',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        self.assertNotEqual(proc.returncode, 0)

    # --- T18/T19: absent/empty envelope -> VALID empty review (no raise) ------ #
    def test_t18_empty_envelope_is_valid_empty_review(self):
        result = score.run({})  # must NOT raise
        self.assertTrue(result["scored_by_script"])
        self.assertEqual(result["findings"], [])

    def test_t19_absent_or_none_findings_is_valid_empty_review(self):
        # findings absent entirely, and findings explicitly None, are BOTH a legal
        # empty review (only a PRESENT non-list fails closed).
        for envelope in ({"command": "deep-review", "carryforward": []},
                        {"command": "deep-review", "findings": None,
                         "carryforward": None}):
            with self.subTest(envelope=envelope):
                result = score.run(envelope)  # must NOT raise
                self.assertTrue(result["scored_by_script"])
                self.assertEqual(result["findings"], [])


if __name__ == "__main__":
    unittest.main()
