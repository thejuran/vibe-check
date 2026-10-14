"""test_finalize_gate.py — the Finalize-mode gate as an executable decision.

Transcribed from `review.md:29-48` (Finalize mode), whose branch order is:

  :31  no state file                      -> error, "Run `/review` first."
  :35  outstanding_cw non-empty           -> the finalize card (fix rows -> fix-loop card)
  :39    ...unless Phase 5 is unavailable -> the legacy fallback
  :40  unacknowledged_medium non-empty    -> the same finalize card (medium rows)
  :46    ...any row marked fix            -> Phase 5; finalize does not proceed
  :47    ...all dismissed                 -> proceed
  :48  otherwise                          -> write .turingmind/REVIEW.md

Fix-list FL-07 (finding R11) is why the vocabulary is six values and not three.
The plan proposed `write` / `fallback` / `refuse`, which cannot represent either
interactive route: `:38` routes outstanding Critical/Warning findings into the
finalize card (explicitly "Do NOT write REVIEW.md ... finalize stays blocked"),
and `:40-47` is the medium branch of the finalize card that ends in either a
Phase-5 route or a proceed. Collapsing those into `fallback` would misclassify
live behavior: the fallback at `:39` is the NON-interactive path, and it tells the user to re-run,
whereas the Phase-5 route keeps going in the same invocation.

The precedence between `:35` and `:40` is the regression lock. `outstanding_cw`
is evaluated BEFORE `unacknowledged_medium`, so a state carrying both must route
on the Critical/Warning branch. Under a swapped order the same input would enter
the medium branch of the finalize card — asking the user to adjudicate Mediums
while Criticals sit unfixed, and (worse) reaching `:48` and writing REVIEW.md for a
review that `:38` says must stay blocked. That is the elevation-of-privilege
shape T-40-44 names.
"""

import ast
import json
import os
import subprocess
import sys
import unittest

# Make `import finalize_gate` resolve when unittest discovery runs from root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import finalize_gate  # noqa: E402  (sibling module under test)
import replay  # noqa: E402  (sibling — reads the shipped v2.11.1 schema blob)

HERE = os.path.dirname(os.path.abspath(__file__))
FINALIZE_GATE_PY = os.path.join(HERE, "finalize_gate.py")


CLEAN = {
    "state_file_present": True,
    "outstanding_cw": 0,
    "unacknowledged_medium": 0,
    "undecided_nv": 0,
    "noninteractive": False,
    "pr_mode": False,
    "range_mode": False,
}


def flags(**overrides):
    out = dict(CLEAN)
    out.update(overrides)
    return out


class TestActions(unittest.TestCase):
    def test_action_vocabulary_is_the_six_transcribed_outcomes(self):
        """FL-07 — three values cannot represent :38 or :40-47."""
        self.assertEqual(finalize_gate.ACTIONS, (
            "write",
            "outstanding-to-phase-5",
            "medium-ack-loop",
            "fallback",
            "error",
            "refuse",
        ))

    def test_every_action_is_reachable(self):
        """A vocabulary with an unreachable member is an invented outcome.

        FL-07 says an added outcome that turns out to be a sub-state of an
        existing one must be called out rather than silently kept; this proves
        each of the six is a distinct, reachable route.
        """
        reached = {
            finalize_gate.decide(flags())["action"],
            finalize_gate.decide(flags(outstanding_cw=2))["action"],
            finalize_gate.decide(flags(unacknowledged_medium=1))["action"],
            finalize_gate.decide(
                flags(outstanding_cw=2, noninteractive=True))["action"],
            finalize_gate.decide(flags(state_file_present=False))["action"],
            finalize_gate.decide("not a mapping")["action"],
        }
        self.assertEqual(reached, set(finalize_gate.ACTIONS))


class TestBranchOrder(unittest.TestCase):
    def test_no_state_file_errors_first(self):
        """:31 — evaluated before any finding is inspected."""
        got = finalize_gate.decide(
            flags(state_file_present=False, outstanding_cw=5,
                  unacknowledged_medium=5))
        self.assertEqual(got["action"], "error")

    def test_outstanding_cw_precedes_medium_REGRESSION_LOCK(self):
        """:35 is evaluated BEFORE :40. This is the swapped-order lock.

        Under a swapped precedence this same input would return
        `medium-ack-loop`, adjudicating Mediums while Criticals sit unfixed.
        """
        got = finalize_gate.decide(
            flags(outstanding_cw=3, unacknowledged_medium=4))
        self.assertEqual(got["action"], "outstanding-to-phase-5")
        self.assertNotEqual(got["action"], "medium-ack-loop")

    def test_the_lock_input_would_resolve_differently_under_a_swap(self):
        """Fixture integrity for the lock: the input must genuinely satisfy
        BOTH conditions, or the test proves nothing about ordering."""
        payload = flags(outstanding_cw=3, unacknowledged_medium=4)
        self.assertGreater(payload["outstanding_cw"], 0)
        self.assertGreater(payload["unacknowledged_medium"], 0)

    def test_medium_only_enters_the_ack_loop(self):
        """:40 — reached only once outstanding_cw is empty."""
        got = finalize_gate.decide(flags(unacknowledged_medium=2))
        self.assertEqual(got["action"], "medium-ack-loop")

    def test_clean_state_writes(self):
        """:48 — the only route that writes REVIEW.md."""
        got = finalize_gate.decide(flags())
        self.assertEqual(got["action"], "write")


class TestPhase5Availability(unittest.TestCase):
    """:39 — the fallback fires only when Phase 5 is UNAVAILABLE."""

    def test_noninteractive_with_outstanding_cw_falls_back(self):
        got = finalize_gate.decide(
            flags(outstanding_cw=1, noninteractive=True))
        self.assertEqual(got["action"], "fallback")

    def test_pr_mode_with_outstanding_cw_falls_back(self):
        got = finalize_gate.decide(flags(outstanding_cw=1, pr_mode=True))
        self.assertEqual(got["action"], "fallback")

    def test_range_mode_with_outstanding_cw_falls_back(self):
        got = finalize_gate.decide(flags(outstanding_cw=1, range_mode=True))
        self.assertEqual(got["action"], "fallback")

    def test_interactive_with_outstanding_cw_routes_to_phase_5(self):
        got = finalize_gate.decide(flags(outstanding_cw=1))
        self.assertEqual(got["action"], "outstanding-to-phase-5")

    def test_medium_loop_also_needs_phase_5(self):
        """The finalize card's fix choice defers to Phase 5, so the medium branch
        is interactive by construction — a non-interactive run cannot ask the
        question."""
        got = finalize_gate.decide(
            flags(unacknowledged_medium=1, noninteractive=True))
        self.assertEqual(got["action"], "fallback")

    def test_clean_pr_and_range_still_write(self):
        """FL-07: "Clean PR/range finalization reaches Write."

        Phase-5 availability gates the FIX routes, not finalization itself —
        with nothing outstanding there is nothing to fix.
        """
        for mode in ("pr_mode", "range_mode", "noninteractive"):
            with self.subTest(mode=mode):
                got = finalize_gate.decide(flags(**{mode: True}))
                self.assertEqual(got["action"], "write")


class TestFailClosed(unittest.TestCase):
    def test_missing_flag_refuses(self):
        for key in CLEAN:
            with self.subTest(missing=key):
                partial = flags()
                del partial[key]
                got = finalize_gate.decide(partial)
                self.assertEqual(got["action"], "refuse")

    def test_unknown_flag_refuses(self):
        got = finalize_gate.decide(flags(surprise=True))
        self.assertEqual(got["action"], "refuse")

    def test_non_bool_bool_flag_refuses(self):
        """`1`, `"true"` and `"false"` are all truthy in Python, so a bash site
        that emitted a string would otherwise silently decide `write`."""
        for bad in (1, 0, "true", "false", None, []):
            with self.subTest(bad=bad):
                got = finalize_gate.decide(flags(noninteractive=bad))
                self.assertEqual(got["action"], "refuse")

    def test_non_int_count_refuses(self):
        for bad in ("3", None, True, 1.5, [1]):
            with self.subTest(bad=bad):
                got = finalize_gate.decide(flags(outstanding_cw=bad))
                self.assertEqual(got["action"], "refuse")

    def test_negative_count_refuses(self):
        self.assertEqual(
            finalize_gate.decide(flags(outstanding_cw=-1))["action"], "refuse")

    def test_non_mapping_refuses(self):
        for bad in (None, "flags", 7, ["a"]):
            with self.subTest(bad=bad):
                self.assertEqual(
                    finalize_gate.decide(bad)["action"], "refuse")

    def test_run_rejects_non_dict_envelope(self):
        self.assertEqual(finalize_gate.run("nope")["action"], "refuse")

    def test_run_reads_the_flags_key(self):
        self.assertEqual(
            finalize_gate.run({"flags": flags()})["action"], "write")


class TestReasons(unittest.TestCase):
    def test_every_reason_is_from_the_fixed_tuple(self):
        cases = (flags(), flags(outstanding_cw=1),
                 flags(outstanding_cw=1, noninteractive=True),
                 flags(unacknowledged_medium=1),
                 flags(state_file_present=False), "bad")
        for case in cases:
            with self.subTest(case=case):
                self.assertIn(finalize_gate.decide(case)["reason"],
                              finalize_gate.REASONS)

    def test_reasons_never_carry_a_finding_count_or_title(self):
        """Reasons are FIXED strings. A count belongs to the render, and a
        title would be attacker-influenced text (findings come from agents
        reading the reviewed diff)."""
        got = finalize_gate.decide(flags(outstanding_cw=7))
        self.assertNotIn("7", got["reason"])

    def test_the_count_guard_is_not_vacuous(self):
        self.assertIn("7", "7 Critical/Warning findings remain")


class TestNoRendering(unittest.TestCase):
    """D-08 — the finalize DECISION is executable, REVIEW.md stays prose."""

    def test_decide_returns_only_action_and_reason(self):
        got = finalize_gate.decide(flags())
        self.assertEqual(set(got), {"action", "reason"})

    def test_no_review_md_content_is_emitted(self):
        blob = json.dumps([finalize_gate.decide(f) for f in (
            flags(), flags(outstanding_cw=1), flags(unacknowledged_medium=1),
            flags(state_file_present=False))])
        for fragment in ("REVIEW.md", "##", "|", "{{"):
            self.assertNotIn(fragment, blob)

    def test_the_rendering_guard_is_not_vacuous(self):
        self.assertIn("REVIEW.md", json.dumps({"x": "wrote REVIEW.md"}))


class TestNoInventedActions(unittest.TestCase):
    """Every action literal must come from ACTIONS, never a bare string."""

    def test_no_action_literal_outside_the_tuple(self):
        with open(FINALIZE_GATE_PY, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        exempt = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
                if "ACTIONS" in names:
                    for sub in ast.walk(node.value):
                        if isinstance(sub, ast.Constant) and isinstance(
                                sub.value, str):
                            exempt.add(id(sub))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) in exempt:
                    continue
                if node.value in finalize_gate.ACTIONS:
                    offenders.append(node.value)
        self.assertEqual(offenders, [],
                         "action literals outside ACTIONS: " + str(offenders))


class TestCLI(unittest.TestCase):
    def _run(self, payload):
        return subprocess.run(
            [sys.executable, FINALIZE_GATE_PY],
            input=payload,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )

    def test_clean_state_writes_through_the_shim(self):
        proc = self._run(json.dumps({"flags": flags()}).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout.decode())["action"], "write")

    def test_bad_flags_refuse_through_the_shim(self):
        proc = self._run(json.dumps({"flags": {"bogus": 1}}).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout.decode())["action"], "refuse")

    def test_invalid_json_exits_nonzero(self):
        self.assertNotEqual(self._run(b"not json").returncode, 0)

    def test_empty_stdin_exits_nonzero(self):
        self.assertNotEqual(self._run(b"").returncode, 0)


class TestUndecidedNeedsVerification(unittest.TestCase):
    """Phase 53 R10: APPROVED is never written while a Needs-verification item
    is undecided. The seventh flag is part of the closed set."""

    def test_six_key_pre53_flags_refuse(self):
        six = {k: v for k, v in flags().items() if k != "undecided_nv"}
        self.assertEqual(len(six), 6)
        got = finalize_gate.decide(six)
        self.assertEqual(got, {"action": "refuse",
                               "reason": finalize_gate.REASON_MALFORMED})

    def test_flag_set_is_seven_keys(self):
        self.assertEqual(finalize_gate._COUNT_FLAGS,
                         ("outstanding_cw", "unacknowledged_medium",
                          "undecided_nv"))
        self.assertEqual(len(finalize_gate.FLAGS), 7)
        self.assertEqual(set(CLEAN), set(finalize_gate.FLAGS))

    def test_bool_or_bad_count_refuses(self):
        for bad in (True, False, "1", None, -1, 1.0):
            with self.subTest(bad=bad):
                got = finalize_gate.decide(flags(undecided_nv=bad))
                self.assertEqual(got["reason"], finalize_gate.REASON_MALFORMED)

    def test_undecided_nv_routes_to_the_card(self):
        got = finalize_gate.decide(flags(undecided_nv=2))
        self.assertEqual(got, {"action": "outstanding-to-phase-5",
                               "reason": finalize_gate.REASON_UNDECIDED_NV})

    def test_undecided_nv_without_phase5_falls_back(self):
        for mode in ("noninteractive", "pr_mode", "range_mode"):
            with self.subTest(mode=mode):
                got = finalize_gate.decide(flags(undecided_nv=2, **{mode: True}))
                self.assertEqual(got, {
                    "action": "fallback",
                    "reason": finalize_gate.REASON_PHASE5_UNAVAILABLE})

    def test_cw_precedes_nv(self):
        got = finalize_gate.decide(flags(outstanding_cw=1, undecided_nv=1))
        self.assertEqual(got["reason"], finalize_gate.REASON_OUTSTANDING_CW)

    def test_nv_precedes_medium(self):
        got = finalize_gate.decide(flags(undecided_nv=1, unacknowledged_medium=3))
        self.assertEqual(got["reason"], finalize_gate.REASON_UNDECIDED_NV)
        self.assertNotEqual(got["action"], "medium-ack-loop")

    def test_never_writes_while_nv_undecided(self):
        for extra in ({}, {"noninteractive": True}, {"pr_mode": True},
                      {"range_mode": True}, {"unacknowledged_medium": 1}):
            with self.subTest(**extra):
                got = finalize_gate.decide(flags(undecided_nv=1, **extra))
                self.assertNotEqual(got["action"], "write")

    def test_all_zero_writes(self):
        self.assertEqual(finalize_gate.decide(flags()),
                         {"action": "write",
                          "reason": finalize_gate.REASON_CLEAN})

    def test_vocabulary_unchanged(self):
        self.assertEqual(len(finalize_gate.ACTIONS), 6)
        self.assertIn(finalize_gate.REASON_UNDECIDED_NV, finalize_gate.REASONS)
        self.assertEqual(len(set(finalize_gate.REASONS)),
                         len(finalize_gate.REASONS))


# The shipped v2.11.1 REVIEW.md schema (verified against `git ls-tree v2.11.1`):
# its header has NO state-format stamp — exactly what every 2.11.x finalize
# writes.
V2111_REVIEW_SCHEMA_BLOB = "7469242c48ab7fb88f91af2dc9d2abcbf4441091"
_PLACEHOLDER = "{{"


def old_style_review_md():
    """A REVIEW.md rendered from the v2.11.1 schema template: the fenced
    template body with every {{placeholder}} filled."""
    text = replay._git("cat-file", "-p", V2111_REVIEW_SCHEMA_BLOB).decode("utf-8")
    body = text.split("````markdown\n", 1)[1].split("\n````", 1)[0]
    out = []
    i = 0
    while True:
        j = body.find(_PLACEHOLDER, i)
        if j < 0:
            out.append(body[i:])
            break
        k = body.find("}}", j)
        out.append(body[i:j] + "x")
        i = k + 2
    return "".join(out)


def stamped(text):
    return text.replace(finalize_gate.APPROVED_LINE + "\n",
                        finalize_gate.APPROVED_LINE + "\n"
                        + finalize_gate.REVIEW_FORMAT_STAMP + "\n", 1)


class TestReviewClosed(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(finalize_gate.REVIEW_FORMAT_STAMP, "**State format:** 53")
        self.assertEqual(finalize_gate.APPROVED_LINE,
                         "**Final verdict:** \u2705 APPROVED")

    def test_fixture_is_the_shipped_render(self):
        old = old_style_review_md()
        self.assertNotIn(_PLACEHOLDER, old)
        self.assertIn(finalize_gate.APPROVED_LINE, old.split("\n"))
        self.assertNotIn("State format", old)
        self.assertNotEqual(stamped(old), old)

    def test_stamped_approved_is_closed(self):
        self.assertTrue(finalize_gate.review_closed(stamped(old_style_review_md())))

    def test_old_style_review_md_is_not_a_phase53_close(self):
        self.assertFalse(finalize_gate.review_closed(old_style_review_md()))

    def test_review_stamp_requirement_is_load_bearing_mutation(self):
        old = old_style_review_md()
        original = finalize_gate.REVIEW_FORMAT_STAMP
        try:
            finalize_gate.REVIEW_FORMAT_STAMP = ""
            self.assertTrue(finalize_gate.review_closed(old))
        finally:
            finalize_gate.REVIEW_FORMAT_STAMP = original
        self.assertFalse(finalize_gate.review_closed(old))

    def test_stamp_without_approved_is_not_closed(self):
        text = stamped(old_style_review_md()).replace(
            finalize_gate.APPROVED_LINE, "**Final verdict:** \u274c BLOCKED")
        self.assertIn(finalize_gate.REVIEW_FORMAT_STAMP, text)
        self.assertFalse(finalize_gate.review_closed(text))

    def test_stamp_is_whole_line(self):
        base = old_style_review_md()
        for bad in ("**State format:** 52", "**State format:** 53x",
                    "    **State format:** 53", "> **State format:** 53",
                    "x **State format:** 53",
                    "`**State format:** 53`"):
            with self.subTest(bad=bad):
                text = base.replace(finalize_gate.APPROVED_LINE + "\n",
                                    finalize_gate.APPROVED_LINE + "\n" + bad + "\n", 1)
                self.assertIn(bad, text)
                self.assertFalse(finalize_gate.review_closed(text))

    def test_trailing_whitespace_tolerated(self):
        text = (finalize_gate.APPROVED_LINE + "  \r\n"
                + finalize_gate.REVIEW_FORMAT_STAMP + " \n")
        self.assertTrue(finalize_gate.review_closed(text))

    def test_non_str_and_empty(self):
        for bad in (None, b"x", 5, [], ""):
            with self.subTest(bad=bad):
                self.assertFalse(finalize_gate.review_closed(bad))


class TestReviewClosedCLI(unittest.TestCase):
    def _run(self, argv, payload):
        return subprocess.run(
            [sys.executable, FINALIZE_GATE_PY] + argv, input=payload,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

    def test_stamped_exits_zero(self):
        proc = self._run(["review-closed"],
                         stamped(old_style_review_md()).encode("utf-8"))
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout.decode()), {"closed": True})

    def test_unstamped_exits_one(self):
        proc = self._run(["review-closed"], old_style_review_md().encode("utf-8"))
        self.assertEqual(proc.returncode, 1, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout.decode()), {"closed": False})

    def test_empty_stdin_exits_one(self):
        proc = self._run(["review-closed"], b"")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(json.loads(proc.stdout.decode()), {"closed": False})

    def test_unknown_argv_exits_two_silently(self):
        for argv in (["bogus"], ["review-closed", "extra"], ["--flags"]):
            with self.subTest(argv=argv):
                proc = self._run(argv, b"{}")
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")

    def test_no_argv_flags_path_unchanged(self):
        proc = self._run([], json.dumps({"flags": flags(undecided_nv=1)}).encode())
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout.decode()),
                         {"action": "outstanding-to-phase-5",
                          "reason": finalize_gate.REASON_UNDECIDED_NV})


class TestCitations(unittest.TestCase):
    def _source(self):
        with open(FINALIZE_GATE_PY, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_cites_the_finalize_branches(self):
        src = self._source()
        for citation in ("review.md:31", "review.md:35", "review.md:39",
                         "review.md:40", "review.md:48"):
            self.assertIn(citation, src)

    def test_states_the_d08_boundary(self):
        src = " ".join(self._source().lower().split())
        self.assertIn("returns a decision", src)


class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "sys"}
    FORBIDDEN_NAMES = {"subprocess", "os", "pathlib", "shutil", "glob", "re",
                       "eval", "exec", "compile", "__import__", "open"}

    def _tree(self):
        with open(FINALIZE_GATE_PY, "r", encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def _imported(self):
        imported = set()
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        return imported

    def test_import_set_subset_of_allowed(self):
        imported = self._imported()
        self.assertTrue(
            imported.issubset(self.ALLOWED),
            "finalize_gate.py imports outside the allowed set: "
            + str(imported - self.ALLOWED))

    def test_no_forbidden_module_imported(self):
        for name in self._imported():
            self.assertNotIn(name, self.FORBIDDEN_NAMES)

    def test_no_forbidden_calls(self):
        banned = {"eval", "exec", "compile", "__import__", "open"}
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, banned)

    def test_the_import_checker_actually_sees_imports(self):
        self.assertEqual(self._imported(), self.ALLOWED)


if __name__ == "__main__":
    unittest.main()
