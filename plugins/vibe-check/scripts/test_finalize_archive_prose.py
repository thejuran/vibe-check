"""Prose pins for the Finalize archive moves (phases/shared/90-finalize.md).

Every archive move in the close-out — the review state file, a prior stamped
REVIEW.md and an unstamped REVIEW.md — goes through `review_archive.py`, which
never overwrites an existing archive. A prior stamped report is archived even
when it belongs to the same phase, so a same-day second close-out keeps both
reports.

Every lock is a pure `..._holds(text) -> bool` function. Each has a test on
the real file and at least one mutant test proving the lock would trip.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.normpath(os.path.join(HERE, ".."))
FINALIZE = os.path.join(PLUGIN_DIR, "phases", "shared", "90-finalize.md")

STATE_CALL = 'review_archive.py" state --state-file "$STATE_FILE"'
REVIEW_MD_CALL = 'review_archive.py" review-md --phase "$PRIOR_PHASE"'
UNSTAMPED_CALL = 'review_archive.py" unstamped'
BARE_STATE_MV = 'mv "$STATE_FILE"'
BARE_REVIEW_MV = "mv .turingmind/REVIEW.md"
DATED_ARCHIVE = "archived-$(date"
SAME_PHASE_SKIP = '"$PRIOR_PHASE" != "$PHASE_ID"'
BOTH_KEPT = "same-day second close-out keeps both reports"

OLD_STATE_LINE = 'mv "$STATE_FILE" "$STATE_FILE.archived-$(date +%Y-%m-%d)"'
OLD_UNSTAMPED_LINE = ('mv .turingmind/REVIEW.md '
                      '".turingmind/REVIEW-unstamped-$(date +%Y-%m-%d).md"')


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def state_archive_uses_helper_holds(text):
    return text.count(STATE_CALL) == 1 and BARE_STATE_MV not in text


def review_md_archives_use_helper_holds(text):
    return (text.count(REVIEW_MD_CALL) == 1
            and text.count(UNSTAMPED_CALL) == 1
            and BARE_REVIEW_MV not in text
            and DATED_ARCHIVE not in text)


ARCHIVE_CALL = 'python3 "$VC_ROOT/scripts/review_archive.py"'
# The calling line must branch on the helper's exit code: `if ! python3 …;
# then` or `if VAR=$(python3 …); then`.
CHECKED_LINE = re.compile(
    r'^\s*if (?:! |[A-Z_]+=\$\()python3 "\$VC_ROOT/scripts/review_archive\.py"'
    r'[^\n]*; then$')
STOP_NO_WRITE = "do NOT write REVIEW.md"
STOP_KEEPS_BOTH = "the earlier report and the live state are both kept"


def _fail_branch(lines, i):
    """The lines that run when the call on line i fails: the `if !` body, or
    the `else` body of an `if VAR=$(…)` call."""
    negated = " ! python3" in lines[i]
    depth = 0
    body = []
    in_else = False
    for line in lines[i + 1:]:
        stripped = line.strip()
        if stripped.startswith("if ") and stripped.endswith("; then"):
            depth += 1
        if stripped == "fi":
            if depth == 0:
                break
            depth -= 1
        if depth == 0 and stripped == "else":
            in_else = True
            continue
        if negated and not in_else:
            body.append(stripped)
        elif not negated and in_else:
            body.append(stripped)
    return body


def archive_calls_checked_holds(text):
    """Every review_archive.py call branches on its exit code and stops (exit
    1) on failure, and the prose says a failure writes nothing."""
    lines = text.split("\n")
    calls = [i for i, line in enumerate(lines) if ARCHIVE_CALL in line]
    if len(calls) != 3:
        return False
    for i in calls:
        if not CHECKED_LINE.match(lines[i]):
            return False
        branch = _fail_branch(lines, i)
        if "exit 1" not in branch or not any(b.startswith("echo ")
                                             for b in branch):
            return False
    return STOP_NO_WRITE in text and STOP_KEEPS_BOTH in text


def same_phase_is_archived_holds(text):
    return SAME_PHASE_SKIP not in text and BOTH_KEPT in text


class TestRealFile(unittest.TestCase):
    def setUp(self):
        self.text = _read(FINALIZE)

    def test_state_archive_uses_helper(self):
        self.assertTrue(state_archive_uses_helper_holds(self.text))

    def test_review_md_archives_use_helper(self):
        self.assertTrue(review_md_archives_use_helper_holds(self.text))

    def test_same_phase_is_archived(self):
        self.assertTrue(same_phase_is_archived_holds(self.text))

    def test_archive_calls_checked(self):
        self.assertTrue(archive_calls_checked_holds(self.text))


class TestMutants(unittest.TestCase):
    def setUp(self):
        self.text = _read(FINALIZE)

    def _mutant(self, old, new=""):
        mutant = self.text.replace(old, new)
        self.assertNotEqual(mutant, self.text)
        return mutant

    def test_restored_bare_state_mv_trips(self):
        mutant = self._mutant(
            'python3 "$VC_ROOT/scripts/' + STATE_CALL, OLD_STATE_LINE)
        self.assertFalse(state_archive_uses_helper_holds(mutant))

    def test_deleted_state_call_trips(self):
        self.assertFalse(state_archive_uses_helper_holds(
            self._mutant(STATE_CALL)))

    def test_restored_bare_unstamped_mv_trips(self):
        mutant = self._mutant(
            'python3 "$VC_ROOT/scripts/' + UNSTAMPED_CALL + " --dir .turingmind",
            OLD_UNSTAMPED_LINE)
        self.assertFalse(review_md_archives_use_helper_holds(mutant))

    def test_deleted_review_md_call_trips(self):
        self.assertFalse(review_md_archives_use_helper_holds(
            self._mutant(REVIEW_MD_CALL)))

    def test_bare_review_mv_added_trips(self):
        mutant = self._mutant(
            'python3 "$VC_ROOT/scripts/' + REVIEW_MD_CALL,
            'python3 "$VC_ROOT/scripts/' + REVIEW_MD_CALL + "\n    "
            + BARE_REVIEW_MV + ' ".turingmind/REVIEW-x.md"')
        self.assertFalse(review_md_archives_use_helper_holds(mutant))

    def test_reinserted_same_phase_condition_trips(self):
        mutant = self._mutant(
            'if [ -n "$PRIOR_PHASE" ]; then',
            'if [ -n "$PRIOR_PHASE" ] && [ ' + SAME_PHASE_SKIP + ' ]; then')
        self.assertFalse(same_phase_is_archived_holds(mutant))

    def test_deleted_both_kept_sentence_trips(self):
        self.assertFalse(same_phase_is_archived_holds(self._mutant(BOTH_KEPT)))

    def test_unchecked_archive_call_trips(self):
        """Dropping the exit check on any one call trips the lock."""
        lines = self.text.split("\n")
        calls = [i for i, line in enumerate(lines) if ARCHIVE_CALL in line]
        self.assertEqual(len(calls), 3)
        for i in calls:
            with self.subTest(line=lines[i].strip()[:60]):
                bare = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                call = lines[i][lines[i].index(ARCHIVE_CALL):]
                call = re.sub(r"\)?; then$", "", call)
                mutant = "\n".join(lines[:i] + [bare + call] + lines[i + 1:])
                self.assertNotEqual(mutant, self.text)
                self.assertFalse(archive_calls_checked_holds(mutant))

    def test_failure_branch_without_exit_trips(self):
        mutant = self.text.replace("    exit 1\n", "    :\n")
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(archive_calls_checked_holds(mutant))

    def test_stop_sentence_removed_trips(self):
        self.assertFalse(archive_calls_checked_holds(
            self._mutant(STOP_KEEPS_BOTH)))


def _archive_fence(text):
    fences = re.findall(r"````bash\n(.*?)\n````", text, re.S)
    hits = [f for f in fences if "PRIOR_PHASE=" in f]
    assert len(hits) == 1
    return hits[0]


class TestArchiveFenceRuns(unittest.TestCase):
    """Run the real prior-report fence with the real helpers. When the
    archive cannot be written the fence exits non-zero and the prior report
    is still in place, so the Write that follows never runs."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.tm = os.path.join(self.tmp, ".turingmind")
        os.mkdir(self.tm)
        self.report = os.path.join(self.tm, "REVIEW.md")
        self.fence = _archive_fence(_read(FINALIZE))

    def tearDown(self):
        os.chmod(self.tm, 0o755)
        shutil.rmtree(self.tmp)

    def _run(self):
        return subprocess.run(
            ["bash", "-c", self.fence], cwd=self.tmp,
            env=dict(os.environ, VC_ROOT=PLUGIN_DIR),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)

    def _write(self, body):
        with open(self.report, "w", encoding="utf-8") as fh:
            fh.write(body)

    def test_stamped_report_archived(self):
        self._write("# Review\nPhase 54-x\n**Final verdict:** \u2705 APPROVED\n"
                    "**State format:** 53\n")
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertFalse(os.path.exists(self.report))
        self.assertEqual(len(os.listdir(self.tm)), 1)

    def test_unarchivable_stamped_report_stops(self):
        if os.geteuid() == 0:
            self.skipTest("root ignores directory permissions")
        body = ("# Review\nPhase 54-x\n**Final verdict:** \u2705 APPROVED\n"
                "**State format:** 53\n")
        self._write(body)
        os.chmod(self.tm, 0o555)
        proc = self._run()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Finalize stopped", proc.stderr.decode())
        self.assertEqual(os.listdir(self.tm), ["REVIEW.md"])
        self.assertEqual(_read(self.report), body)

    def test_unarchivable_unstamped_report_stops(self):
        if os.geteuid() == 0:
            self.skipTest("root ignores directory permissions")
        self._write("old report, no stamp\n")
        os.chmod(self.tm, 0o555)
        proc = self._run()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Finalize stopped", proc.stderr.decode())
        self.assertNotIn("archived aside", proc.stdout.decode())
        self.assertEqual(_read(self.report), "old report, no stamp\n")


if __name__ == "__main__":
    unittest.main()
