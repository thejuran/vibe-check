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


if __name__ == "__main__":
    unittest.main()
