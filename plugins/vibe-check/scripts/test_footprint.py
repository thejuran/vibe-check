"""test_footprint.py — the DIET-01 per-mode-path footprint measurement.

Two properties are load-bearing.

**F11 — BEFORE numbers must not come from the mutable worktree.** The previous
version of this plan measured `commands/review.md` from the working file while
wave-1 plan 40-02 was concurrently editing that same file. Depending on
execution order the recorded BEFORE numbers were either right by luck or wrong
with no signal at all. The fix is the module constant `PRE_PHASE_REV`: every
BEFORE stat is read with `git show <rev>:<path>`. TestPinnedRev proves the
number is rev-sourced by computing it independently via subprocess AND by
asserting the pinned read disagrees with the worktree (40-02 has landed, so
they genuinely differ today).

**T-40-17 — MODE_PATHS must not silently drift out of coverage.** `MODE_PATHS`
is the ONE place a mode path's file list lives, and D-09 makes a skipped read
the new failure mode. Two static drift-locks: EXISTENCE (every listed path
exists) and COVERAGE (once `phases/` exists, every sub-file is named by at
least one mode path). These are the static twin of the D-09 skipped-read risk;
the dynamic twin is plan 40-13.

Contrast with state_shape.py, per the D-13 inversion: state_shape is a GATE
(non-zero exit on a violation) while footprint is OPTIONAL CONTEXT — a missing
file degrades into a `missing` list and `run` still exits 0. A footprint number
must never be able to block a batch.

`--measure` is NOT exercised here: it shells `claude -p`, costs money, and
needs network.
"""

import ast
import glob
import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import footprint  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
FOOTPRINT_PY = os.path.join(HERE, "footprint.py")
PLUGIN_ROOT = os.path.abspath(os.path.join(HERE, ".."))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

# Verified against `git show 7a386ed:<path> | wc -c` at planning time. Bytes
# are unambiguous; WORDS are not. The plan pinned 27148/12134, which is what
# BSD `wc -w` reports under en_US.UTF-8 -- it splits on a couple of multibyte
# symbols (U+2260, U+2298). `LC_ALL=C wc -w` and Python's split() both report
# 27146/12132. footprint.py records the locale-INDEPENDENT figure because plan
# 40-14 transcribes it; TestWordCountLocaleDrift locks the +2 relationship so
# the discrepancy stays visible instead of being rediscovered as a bug.
REVIEW_MD_BYTES_AT_PIN = 189625
REVIEW_MD_WORDS_AT_PIN = 27146
REVIEW_MD_WORDS_WC_UTF8 = 27148
DEEP_MD_BYTES_AT_PIN = 84534
DEEP_MD_WORDS_AT_PIN = 12132
DEEP_MD_WORDS_WC_UTF8 = 12134

EXPECTED_MODES = {"review-plain", "review-all", "deep-plain", "deep-all",
                  "finalize", "fix-loop"}


class TestModulePins(unittest.TestCase):

    def test_pre_phase_rev_is_the_pinned_constant(self):
        self.assertEqual(footprint.PRE_PHASE_REV, "7a386ed")

    def test_mode_paths_has_exactly_the_six_keys(self):
        self.assertEqual(set(footprint.MODE_PATHS), EXPECTED_MODES)

    def test_proxies_are_labelled_proxies(self):
        """D-10/D-01: a proxy is never presented as a measurement."""
        names = [n for n, _ in footprint.PROXIES]
        self.assertEqual(names, ["tokens@3.5", "tokens@2.7"])
        for _, divisor in footprint.PROXIES:
            self.assertIsInstance(divisor, float)

    def test_deep_paths_list_both_files(self):
        """deep-review.md:35 makes the deep path read review.md end-to-end."""
        for mode in ("deep-plain", "deep-all"):
            with self.subTest(mode=mode):
                self.assertIn("commands/deep-review.md", footprint.MODE_PATHS[mode])
                self.assertIn("commands/review.md", footprint.MODE_PATHS[mode])


class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "os", "subprocess", "sys"}

    def test_imports_are_exactly_the_allowed_set(self):
        with open(FOOTPRINT_PY) as fh:
            tree = ast.parse(fh.read())
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    found.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
        self.assertEqual(found, self.ALLOWED)

    def test_every_subprocess_run_has_an_explicit_timeout(self):
        with open(FOOTPRINT_PY) as fh:
            tree = ast.parse(fh.read())
        calls = 0
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "run"
                    and getattr(node.func.value, "id", None) == "subprocess"):
                calls += 1
                self.assertIn("timeout", [kw.arg for kw in node.keywords],
                              "every subprocess.run needs an explicit timeout")
        self.assertGreater(calls, 0, "expected at least one subprocess.run")


class TestPinnedRev(unittest.TestCase):
    """F11 -- the number must not come from the mutable file."""

    def _git_show_bytes(self, rel):
        proc = subprocess.run(
            ["git", "-C", REPO_ROOT, "show",
             "%s:plugins/vibe-check/%s" % (footprint.PRE_PHASE_REV, rel)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def test_before_numbers_come_from_pinned_rev_not_worktree(self):
        stats = footprint.file_stats(PLUGIN_ROOT, "commands/review.md",
                                     rev=footprint.PRE_PHASE_REV)
        self.assertEqual(stats["bytes"], REVIEW_MD_BYTES_AT_PIN)
        self.assertEqual(stats["words"], REVIEW_MD_WORDS_AT_PIN)
        # Independently recomputed, so the assertion is not just echoing the
        # module's own arithmetic.
        self.assertEqual(stats["bytes"], len(self._git_show_bytes("commands/review.md")))

    def test_deep_review_pinned_numbers(self):
        stats = footprint.file_stats(PLUGIN_ROOT, "commands/deep-review.md",
                                     rev=footprint.PRE_PHASE_REV)
        self.assertEqual(stats["bytes"], DEEP_MD_BYTES_AT_PIN)
        self.assertEqual(stats["words"], DEEP_MD_WORDS_AT_PIN)

    def test_pinned_read_is_unaffected_by_the_working_file(self):
        """40-02 has already edited review.md, so the two must disagree.

        This is the exact failure F11 describes: had the BEFORE number been
        read from the worktree it would silently be the post-40-02 figure.
        """
        pinned = footprint.file_stats(PLUGIN_ROOT, "commands/review.md",
                                      rev=footprint.PRE_PHASE_REV)
        live = footprint.file_stats(PLUGIN_ROOT, "commands/review.md")
        self.assertEqual(pinned["bytes"], REVIEW_MD_BYTES_AT_PIN)
        self.assertNotEqual(
            pinned["bytes"], live["bytes"],
            "wave-1 plan 40-02 edits commands/review.md; if these are equal the "
            "test can no longer prove the BEFORE number is rev-sourced")

    def test_worktree_read_works_and_is_labelled_worktree(self):
        stats = footprint.path_stats(PLUGIN_ROOT, "review-plain")
        self.assertEqual(stats["rev"], "worktree")
        self.assertGreater(stats["bytes"], 0)

    def test_missing_at_rev_degrades_without_raising(self):
        """A file that did not exist at the pin lands in `missing`."""
        stats = footprint.file_stats(PLUGIN_ROOT, "phases/review/00-scope.md",
                                     rev=footprint.PRE_PHASE_REV)
        self.assertIsNone(stats["bytes"])


class TestWordCountLocaleDrift(unittest.TestCase):
    """The recorded word count must not move with the environment.

    Discovered while executing 40-05: the plan pinned 27148/12134 words, which
    is BSD `wc -w` under en_US.UTF-8. That `wc` splits `off≠config` (U+2260)
    into two words; `LC_ALL=C wc -w` does not. A footprint number that changes
    with $LC_ALL is a poor thing for plan 40-14 to transcribe, so footprint.py
    reports the locale-independent count and these tests keep the +2
    relationship documented and asserted rather than folkloric.
    """

    def _wc(self, rel, locale_env):
        env = dict(os.environ)
        env.update(locale_env)
        show = subprocess.run(
            ["git", "-C", REPO_ROOT, "show",
             "%s:plugins/vibe-check/%s" % (footprint.PRE_PHASE_REV, rel)],
            stdout=subprocess.PIPE, timeout=30)
        proc = subprocess.run(["wc", "-w"], input=show.stdout,
                              stdout=subprocess.PIPE, env=env, timeout=30)
        return int(proc.stdout.split()[0])

    def test_c_locale_wc_matches_the_recorded_number(self):
        for rel, want in (("commands/review.md", REVIEW_MD_WORDS_AT_PIN),
                          ("commands/deep-review.md", DEEP_MD_WORDS_AT_PIN)):
            with self.subTest(path=rel):
                self.assertEqual(self._wc(rel, {"LC_ALL": "C"}), want)
                self.assertEqual(
                    footprint.file_stats(PLUGIN_ROOT, rel,
                                         rev=footprint.PRE_PHASE_REV)["words"],
                    want)

    def test_utf8_locale_wc_is_the_plans_figure_and_differs_by_two(self):
        for rel, utf8, stable in (
                ("commands/review.md", REVIEW_MD_WORDS_WC_UTF8, REVIEW_MD_WORDS_AT_PIN),
                ("commands/deep-review.md", DEEP_MD_WORDS_WC_UTF8, DEEP_MD_WORDS_AT_PIN)):
            with self.subTest(path=rel):
                self.assertEqual(self._wc(rel, {"LC_ALL": "en_US.UTF-8"}), utf8)
                self.assertEqual(utf8 - stable, 2)


class TestPathStats(unittest.TestCase):

    def test_multi_file_sum_equals_sum_of_parts(self):
        rev = footprint.PRE_PHASE_REV
        combined = footprint.path_stats(PLUGIN_ROOT, "deep-plain", rev=rev)
        parts = [footprint.file_stats(PLUGIN_ROOT, rel, rev=rev)
                 for rel in footprint.MODE_PATHS["deep-plain"]]
        self.assertEqual(combined["bytes"], sum(p["bytes"] for p in parts))
        self.assertEqual(combined["words"], sum(p["words"] for p in parts))
        # No dedup: deep-plain legitimately lists two files today.
        self.assertEqual(combined["bytes"],
                         REVIEW_MD_BYTES_AT_PIN + DEEP_MD_BYTES_AT_PIN)

    def test_every_row_carries_its_rev(self):
        """A transcribed number must always be attributable (T-40-16c)."""
        for mode in footprint.MODE_PATHS:
            with self.subTest(mode=mode):
                stats = footprint.path_stats(PLUGIN_ROOT, mode,
                                             rev=footprint.PRE_PHASE_REV)
                self.assertEqual(stats["rev"], footprint.PRE_PHASE_REV)

    def test_missing_file_degrades_and_is_listed(self):
        """D-13 inversion: footprint DEGRADES where state_shape gates."""
        original = dict(footprint.MODE_PATHS)
        try:
            footprint.MODE_PATHS["review-plain"] = ["commands/review.md",
                                                    "commands/does-not-exist.md"]
            stats = footprint.path_stats(PLUGIN_ROOT, "review-plain")
            self.assertIn("commands/does-not-exist.md", stats["missing"])
            self.assertGreater(stats["bytes"], 0,
                               "stats for the files that DO exist are still returned")
        finally:
            footprint.MODE_PATHS.clear()
            footprint.MODE_PATHS.update(original)

    def test_unknown_mode_raises(self):
        with self.assertRaises(Exception):
            footprint.path_stats(PLUGIN_ROOT, "no-such-mode")


class TestDriftLocks(unittest.TestCase):
    """T-40-17 -- the static twin of the D-09 skipped-read risk."""

    def test_mode_paths_exist_in_the_worktree(self):
        missing = []
        for mode, rels in footprint.MODE_PATHS.items():
            for rel in rels:
                if not os.path.isfile(os.path.join(PLUGIN_ROOT, rel)):
                    missing.append("%s -> %s" % (mode, rel))
        self.assertEqual(missing, [],
                         "MODE_PATHS names files that do not exist: %s" % missing)

    def test_phases_covered(self):
        """Once phases/ exists, every sub-file must be read by some mode path."""
        phases_dir = os.path.join(PLUGIN_ROOT, "phases")
        found = sorted(glob.glob(os.path.join(phases_dir, "**", "*.md"),
                                 recursive=True))
        # phases/ exists from plan 40-08 on; an empty glob here is a path bug,
        # and skipping on it would turn this lock back into a no-op.
        self.assertGreater(len(found), 2, "phases/**/*.md glob found %r" % found)
        listed = set()
        for rels in footprint.MODE_PATHS.values():
            listed.update(rels)
        orphans = []
        for path in found:
            rel = os.path.relpath(path, PLUGIN_ROOT)
            if rel not in listed:
                orphans.append(rel)
        self.assertEqual(orphans, [],
                         "phase sub-files no mode path reads (a skipped read is "
                         "the D-09 failure mode): %s" % orphans)


class TestCli(unittest.TestCase):

    def _run(self, *argv):
        return subprocess.run([sys.executable, FOOTPRINT_PY, *argv],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=60)

    def test_json_reports_six_rows_with_pinned_bytes(self):
        proc = self._run("--root", PLUGIN_ROOT, "--rev", "7a386ed", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(set(data), EXPECTED_MODES)
        self.assertEqual(data["review-plain"]["bytes"], REVIEW_MD_BYTES_AT_PIN)
        self.assertEqual(data["deep-plain"]["bytes"],
                         REVIEW_MD_BYTES_AT_PIN + DEEP_MD_BYTES_AT_PIN)
        for row in data.values():
            self.assertEqual(row["rev"], "7a386ed")

    def test_worktree_run_is_labelled_worktree(self):
        proc = self._run("--root", PLUGIN_ROOT, "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        for row in data.values():
            self.assertEqual(row["rev"], "worktree")

    def test_table_header_labels_both_proxy_columns(self):
        """D-10: never print an unlabelled `tokens` column."""
        proc = self._run("--root", PLUGIN_ROOT, "--rev", "7a386ed")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.count("(proxy)"), 2)
        self.assertIn("7a386ed", proc.stdout)

    def test_exit_zero_even_with_missing_files(self):
        """Optional context never gates a batch (D-13)."""
        proc = self._run("--root", "/no/such/root", "--json")
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertTrue(any(row["missing"] for row in data.values()))


if __name__ == "__main__":
    unittest.main()
