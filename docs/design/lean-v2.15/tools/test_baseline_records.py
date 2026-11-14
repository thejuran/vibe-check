"""Tests for baseline_records: replay fingerprints, the manifest, verify_baseline.

Every lock here lands with a mutant that trips it, and every mutant first
asserts that the mutation really happened, so no guard is decorative. The
replay tests run a stand-in `replay.py` (written into a temp scripts
directory) so they do not depend on which recordings this checkout holds;
the committed records are checked against the real replay.py further down.
There is no skip anywhere in this file: where the private recordings are
absent the replay check compares against the second recorded fingerprint.
"""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import baseline_records  # noqa: E402  (sibling module under test)
import finalize_capture  # noqa: E402
import step_count  # noqa: E402

BASELINE_RECORDS_PY = os.path.join(HERE, "baseline_records.py")
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "plugins", "vibe-check", "scripts")
BASELINE_DIR = os.path.abspath(os.path.join(HERE, "..", "baseline"))

BASELINE_COMMIT = "dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4"
PLUGINS_TREE = "90e0697363ee5c09bb7942a963cf670e16717c4a"
FINALIZE_MD = "phases/shared/90-finalize.md"
FINALIZE_FENCES_AT_PIN = 18

REPLAY_WITH = "replay-baseline-v2.14.1.md"
REPLAY_WITHOUT = "replay-baseline-v2.14.1.no-private.md"

SAMPLE_REPORT = (
    "# Replay report — baseline fidelity\n"
    "\n"
    "- baseline: blob: b21f7f3d\n"
    "- manifest sha256: 7f5ac511\n"
    "- HEAD: e1881b3f32a6fccd96fc56dfbe73a2096915cb93\n"
    "- generated (UTC): 2026-11-14T05:45:35Z\n"
    "\n"
    "## Protected catches\n"
    "\n"
    "| run | status |\n"
    "|---|---|\n"
    "| runs/a/run-1 | REPRODUCED |\n"
)

# A stand-in replay.py: `census` prints the recording count from fake.json
# (or leaves the transcripts line out), `baseline --out` writes a fixed report
# whose HEAD and generated lines change on every call (a call counter), so
# two captures always differ in exactly those two lines.
FAKE_REPLAY = textwrap.dedent('''\
    import json, os, sys
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "fake.json")) as fh:
        cfg = json.load(fh)
    counter = os.path.join(here, "calls")
    n = int(open(counter).read()) + 1 if os.path.exists(counter) else 1
    with open(counter, "w") as fh:
        fh.write(str(n))
    if sys.argv[1] == "census":
        sys.stdout.write("runs: 18\\n")
        if cfg.get("transcripts") is not None:
            sys.stdout.write("transcripts: %d\\n" % cfg["transcripts"])
        sys.stdout.write("scoreable: 66\\n")
        sys.exit(0)
    if sys.argv[1] == "baseline":
        out = sys.argv[sys.argv.index("--out") + 1]
        with open(out, "w") as fh:
            fh.write("# Replay report — baseline fidelity\\n\\n")
            fh.write("- baseline: blob: b21f7f3d\\n")
            fh.write("- HEAD: %040d\\n" % n)
            fh.write("- generated (UTC): 2026-11-14T00:00:%02dZ\\n" % (n % 60))
            fh.write("\\n## Body\\n\\n%s\\n" % cfg.get("body", "transcripts seen"))
        sys.exit(0)
    sys.exit(2)
''')


def make_fake_scripts(root, transcripts=0, body="transcripts seen"):
    scripts = os.path.join(root, "scripts")
    os.makedirs(scripts, exist_ok=True)
    with open(os.path.join(scripts, "replay.py"), "w", encoding="utf-8") as fh:
        fh.write(FAKE_REPLAY)
    with open(os.path.join(scripts, "fake.json"), "w", encoding="utf-8") as fh:
        json.dump({"transcripts": transcripts, "body": body}, fh)
    return scripts


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def git_show(rel):
    proc = subprocess.run(
        ["git", "-C", REPO_ROOT, "show", "%s:plugins/vibe-check/%s" % (BASELINE_COMMIT, rel)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    return proc.stdout.decode("utf-8")


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="baseline-records-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)


# --------------------------------------------------------------------------- #
# Replay normalisation and fingerprints
# --------------------------------------------------------------------------- #
class TestNormalise(unittest.TestCase):
    def test_drops_exactly_the_four_volatile_line_shapes(self):
        text = (SAMPLE_REPORT
                + "- head: abc\n- generated: 2026-01-01T00:00:00Z\n- heads: kept\n"
                + "-  HEAD: kept (two spaces)\nnot - HEAD: kept\n")
        out = baseline_records.normalise_replay(text.encode("utf-8")).decode("utf-8")
        self.assertNotIn("- HEAD: e1881b3", out)
        self.assertNotIn("- generated (UTC):", out)
        self.assertNotIn("- head: abc", out)
        self.assertNotIn("- generated: 2026", out)
        for kept in ("- heads: kept", "-  HEAD: kept (two spaces)", "not - HEAD: kept",
                     "- baseline: blob: b21f7f3d", "- manifest sha256: 7f5ac511",
                     "| runs/a/run-1 | REPRODUCED |"):
            self.assertIn(kept, out)
        removed = len(text.splitlines()) - len(out.splitlines())
        self.assertEqual(removed, 4)

    def test_reports_differing_only_in_volatile_lines_share_a_fingerprint(self):
        other = (SAMPLE_REPORT.replace("e1881b3f32a6", "0000000000ff")
                 .replace("05:45:35Z", "23:59:59Z"))
        self.assertNotEqual(other, SAMPLE_REPORT)
        self.assertEqual(baseline_records.replay_fingerprint(SAMPLE_REPORT.encode()),
                         baseline_records.replay_fingerprint(other.encode()))

    def test_one_other_character_changes_the_fingerprint(self):
        other = SAMPLE_REPORT.replace("REPRODUCED", "REPRODUCEd")
        self.assertNotEqual(other, SAMPLE_REPORT)
        self.assertNotEqual(baseline_records.replay_fingerprint(SAMPLE_REPORT.encode()),
                            baseline_records.replay_fingerprint(other.encode()))

    def test_fingerprint_is_sha256_of_the_kept_bytes(self):
        import hashlib
        kept = baseline_records.normalise_replay(SAMPLE_REPORT.encode())
        self.assertEqual(baseline_records.replay_fingerprint(SAMPLE_REPORT.encode()),
                         hashlib.sha256(kept).hexdigest())

    def test_rule_text_names_the_pattern(self):
        self.assertIn(baseline_records.REPLAY_VOLATILE_RE.pattern.decode("ascii"),
                      baseline_records.REPLAY_RULE)


class TestRecordingCount(TempDirCase):
    def test_reads_the_transcripts_line(self):
        for n in (0, 12):
            scripts = make_fake_scripts(os.path.join(self.tmp, str(n)), transcripts=n)
            self.assertEqual(baseline_records.recording_count(scripts), n)

    def test_output_without_the_line_is_a_usage_error(self):
        scripts = make_fake_scripts(self.tmp, transcripts=None)
        with self.assertRaises(baseline_records.UsageError):
            baseline_records.recording_count(scripts)

    def test_real_census_in_this_checkout_gives_an_expected_count(self):
        n = baseline_records.recording_count(SCRIPTS_DIR)
        self.assertIn(n, baseline_records.REPLAY_FILES)


class TestExpectedReplayFile(unittest.TestCase):
    def test_known_counts(self):
        self.assertEqual(baseline_records.expected_replay_file(12), REPLAY_WITH)
        self.assertEqual(baseline_records.expected_replay_file(0), REPLAY_WITHOUT)

    def test_unexpected_count_stops_by_name(self):
        with self.assertRaises(baseline_records.UsageError) as cm:
            baseline_records.expected_replay_file(3)
        self.assertIn("UNEXPECTED RECORDING COUNT 3 — STOPPING", str(cm.exception))


class TestCaptureReplay(TempDirCase):
    def test_writes_the_report_and_returns_count_fingerprint_rule(self):
        scripts = make_fake_scripts(self.tmp, transcripts=12)
        out = os.path.join(self.tmp, "r.md")
        got = baseline_records.capture_replay(scripts, out)
        with open(out, "rb") as fh:
            data = fh.read()
        self.assertEqual(got, {"transcripts": 12,
                               "sha256": baseline_records.replay_fingerprint(data),
                               "rule": baseline_records.REPLAY_RULE})

    def test_two_captures_differ_in_bytes_but_share_a_fingerprint(self):
        scripts = make_fake_scripts(self.tmp, transcripts=0)
        a = os.path.join(self.tmp, "a.md")
        b = os.path.join(self.tmp, "b.md")
        fa = baseline_records.capture_replay(scripts, a)["sha256"]
        fb = baseline_records.capture_replay(scripts, b)["sha256"]
        self.assertNotEqual(read(a), read(b))
        self.assertEqual(fa, fb)


def seed_replay_dir(case, transcripts):
    """A baseline dir holding both replay reports (+ .sha256) from the stand-in."""
    base = os.path.join(case.tmp, "baseline")
    os.makedirs(base)
    for count, name in baseline_records.REPLAY_FILES.items():
        scripts = make_fake_scripts(os.path.join(case.tmp, "seed-%d" % count),
                                    transcripts=count, body="count %d" % count)
        got = baseline_records.capture_replay(scripts, os.path.join(base, name))
        write(os.path.join(base, name + ".sha256"), got["sha256"] + "\n")
    live = make_fake_scripts(os.path.join(case.tmp, "live"), transcripts=transcripts,
                             body="count %d" % transcripts)
    return base, live


class TestVerifyReplay(TempDirCase):
    def test_clean_in_both_conditions(self):
        for n in (12, 0):
            sub = os.path.join(self.tmp, "c%d" % n)
            os.makedirs(sub)
            case = mock.Mock(tmp=sub)
            base, live = seed_replay_dir(case, n)
            self.assertEqual(baseline_records.verify_replay(REPO_ROOT, base, live), [])

    def test_unexpected_count_fails_by_name(self):
        base, _ = seed_replay_dir(self, 0)
        live = make_fake_scripts(os.path.join(self.tmp, "three"), transcripts=3)
        problems = baseline_records.verify_replay(REPO_ROOT, base, live)
        self.assertTrue(any("UNEXPECTED RECORDING COUNT 3 — STOPPING" in p for p in problems),
                        problems)

    def test_mutant_report_body_character_changed(self):
        base, live = seed_replay_dir(self, 0)
        path = os.path.join(base, REPLAY_WITH)
        text = read(path)
        mutated = text.replace("count 12", "count 13")
        self.assertNotEqual(mutated, text)
        write(path, mutated)
        problems = baseline_records.verify_replay(REPO_ROOT, base, live)
        self.assertTrue(problems)
        self.assertTrue(all(p.startswith(REPLAY_WITH + ":") for p in problems), problems)

    def test_mutant_sha256_text_changed(self):
        base, live = seed_replay_dir(self, 0)
        path = os.path.join(base, REPLAY_WITHOUT + ".sha256")
        text = read(path)
        mutated = ("0" if text[0] != "0" else "1") + text[1:]
        self.assertNotEqual(mutated, text)
        write(path, mutated)
        problems = baseline_records.verify_replay(REPO_ROOT, base, live)
        self.assertTrue(any(p.startswith(REPLAY_WITHOUT + ":") for p in problems), problems)

    def test_mutant_re_derived_body_differs(self):
        base, _ = seed_replay_dir(self, 12)
        live = make_fake_scripts(os.path.join(self.tmp, "drift"), transcripts=12,
                                 body="count 12 but scored differently")
        problems = baseline_records.verify_replay(REPO_ROOT, base, live)
        self.assertTrue(any(p.startswith(REPLAY_WITH + ":") and "re-derived" in p
                            for p in problems), problems)

    def test_mutant_normaliser_keeps_the_generated_line(self):
        base, live = seed_replay_dir(self, 0)
        self.assertEqual(baseline_records.verify_replay(REPO_ROOT, base, live), [])
        weak = re.compile(rb"^- (HEAD|head): ")
        self.assertNotEqual(weak.pattern, baseline_records.REPLAY_VOLATILE_RE.pattern)
        with mock.patch.object(baseline_records, "REPLAY_VOLATILE_RE", weak):
            problems = baseline_records.verify_replay(REPO_ROOT, base, live)
        self.assertTrue(any(p.startswith(REPLAY_WITHOUT + ":") and "re-derived" in p
                            for p in problems), problems)

    def test_missing_sidecar_is_named(self):
        base, live = seed_replay_dir(self, 0)
        os.remove(os.path.join(base, REPLAY_WITH + ".sha256"))
        problems = baseline_records.verify_replay(REPO_ROOT, base, live)
        self.assertTrue(any(p.startswith(REPLAY_WITH + ":") for p in problems), problems)

    def test_temp_report_is_removed(self):
        base, live = seed_replay_dir(self, 0)
        made = []
        real = tempfile.mkdtemp

        def spy(*a, **k):
            d = real(*a, **k)
            made.append(d)
            return d
        with mock.patch.object(baseline_records.tempfile, "mkdtemp", spy):
            baseline_records.verify_replay(REPO_ROOT, base, live)
        self.assertTrue(made)
        self.assertFalse(any(os.path.exists(d) for d in made))


# --------------------------------------------------------------------------- #
# Manifest
# --------------------------------------------------------------------------- #
class TestManifest(TempDirCase):
    def _seed(self):
        base = os.path.join(self.tmp, "baseline")
        os.makedirs(base)
        for name, body in (("a.json", "{}\n"), ("b.md", "# b\n"), ("b.md.sha256", "x\n")):
            write(os.path.join(base, name), body)
        manifest = baseline_records.build_manifest(base, {"note": "facts"})
        baseline_records.write_manifest(base, manifest)
        return base

    def test_build_covers_every_file_but_itself(self):
        base = self._seed()
        manifest = json.loads(read(os.path.join(base, "MANIFEST.json")))
        self.assertEqual(sorted(manifest["files"]), ["a.json", "b.md", "b.md.sha256"])
        self.assertEqual(manifest["schema"], 1)
        self.assertEqual(manifest["baseline_commit"], BASELINE_COMMIT)
        self.assertEqual(manifest["plugins_tree"], PLUGINS_TREE)
        self.assertEqual(manifest["facts"], {"note": "facts"})
        self.assertEqual(set(manifest), {"schema", "baseline_commit", "plugins_tree",
                                         "facts", "files"})

    def test_untouched_copy_is_clean(self):
        self.assertEqual(baseline_records.verify_manifest(self._seed()), [])

    def test_mutant_one_byte_changed(self):
        base = self._seed()
        path = os.path.join(base, "a.json")
        write(path, "{ }\n")
        problems = baseline_records.verify_manifest(base)
        self.assertTrue(problems and all("a.json" in p for p in problems), problems)

    def test_mutant_record_deleted(self):
        base = self._seed()
        os.remove(os.path.join(base, "b.md"))
        problems = baseline_records.verify_manifest(base)
        self.assertTrue(any("b.md:" in p and "absent" in p for p in problems), problems)

    def test_mutant_extra_file_added(self):
        base = self._seed()
        write(os.path.join(base, "c.json"), "{}\n")
        problems = baseline_records.verify_manifest(base)
        self.assertTrue(any("c.json" in p and "not listed" in p for p in problems), problems)

    def test_mutant_hash_edited_in_manifest(self):
        base = self._seed()
        mpath = os.path.join(base, "MANIFEST.json")
        manifest = json.loads(read(mpath))
        old = manifest["files"]["b.md.sha256"]
        manifest["files"]["b.md.sha256"] = "0" * 64
        self.assertNotEqual(old, "0" * 64)
        write(mpath, json.dumps(manifest))
        problems = baseline_records.verify_manifest(base)
        self.assertTrue(problems and all("b.md.sha256" in p for p in problems), problems)

    def test_missing_manifest_is_named(self):
        base = self._seed()
        os.remove(os.path.join(base, "MANIFEST.json"))
        problems = baseline_records.verify_manifest(base)
        self.assertTrue(any("MANIFEST.json" in p for p in problems), problems)


# --------------------------------------------------------------------------- #
# Suite record
# --------------------------------------------------------------------------- #
LINE = "3886 passed, 5060 subtests passed in 205.20s (0:03:25)"


class TestSuiteRecord(unittest.TestCase):
    def test_parse_summary_line(self):
        got = baseline_records.parse_summary_line(LINE)
        self.assertEqual(got, {"passed": 3886, "failed": 0, "skipped": 0, "errors": 0,
                               "subtests_passed": 5060})
        got = baseline_records.parse_summary_line(
            "== 2 failed, 10 passed, 3 skipped, 1 error in 1.00s ==")
        self.assertEqual(got, {"passed": 10, "failed": 2, "skipped": 3, "errors": 1,
                               "subtests_passed": 0})

    def test_line_without_passed_is_a_usage_error(self):
        with self.assertRaises(baseline_records.UsageError):
            baseline_records.parse_summary_line("no tests ran in 0.01s")

    def _good(self):
        rec = {"summary_line": LINE, "baseline_commit": BASELINE_COMMIT,
               "plugins_tree": PLUGINS_TREE, "seconds": 205}
        rec.update(baseline_records.parse_summary_line(LINE))
        return rec

    def test_good_record_is_clean(self):
        self.assertEqual(baseline_records.verify_suite_record(REPO_ROOT, self._good()), [])

    def test_mutant_plugins_tree_altered(self):
        rec = self._good()
        rec["plugins_tree"] = "f" * 40
        self.assertNotEqual(rec["plugins_tree"], PLUGINS_TREE)
        problems = baseline_records.verify_suite_record(REPO_ROOT, rec)
        self.assertTrue(any("plugins_tree" in p for p in problems), problems)

    def test_mutant_failed_nonzero(self):
        # summary line and counts agree, so only the failed-is-zero rule can trip
        rec = self._good()
        rec["summary_line"] = "1 failed, " + LINE
        rec.update(baseline_records.parse_summary_line(rec["summary_line"]))
        self.assertEqual(rec["failed"], 1)
        problems = baseline_records.verify_suite_record(REPO_ROOT, rec)
        self.assertEqual(problems, ["failed is 1, not 0"])

    def test_mutant_passed_not_positive(self):
        for bad in (0, -1, "3886", True):
            rec = self._good()
            rec["passed"] = bad
            problems = baseline_records.verify_suite_record(REPO_ROOT, rec)
            self.assertTrue(any(p.startswith("passed is ") for p in problems), (bad, problems))

    def test_mutant_counts_disagree_with_the_summary_line(self):
        rec = self._good()
        rec["subtests_passed"] = 5061
        problems = baseline_records.verify_suite_record(REPO_ROOT, rec)
        self.assertTrue(any("summary_line" in p for p in problems), problems)


# --------------------------------------------------------------------------- #
# verify_baseline wiring, decoupling, fence agreement
# --------------------------------------------------------------------------- #
class TestStepsDecoupling(TempDirCase):
    def test_steps_check_ignores_a_changed_mode_path_list(self):
        base = os.path.join(self.tmp, "baseline")
        os.makedirs(base)
        shutil.copy(os.path.join(BASELINE_DIR, "steps-v2.14.1.json"), base)
        before = baseline_records.check_steps(REPO_ROOT, base)
        if SCRIPTS_DIR not in sys.path:
            sys.path.insert(0, SCRIPTS_DIR)
        import footprint
        original = list(footprint.MODE_PATHS["finalize"])
        patched = original[:-1]
        with mock.patch.dict(footprint.MODE_PATHS, {"finalize": patched}):
            self.assertNotEqual(list(footprint.MODE_PATHS["finalize"]), original)
            # the patch is live: the live-list counter sees the shorter list
            live = step_count.count_path(REPO_ROOT, rev=BASELINE_COMMIT)
            self.assertEqual(len(live["files"]), len(original) - 1)
            during = baseline_records.check_steps(REPO_ROOT, base)
        self.assertEqual(before, [])
        self.assertEqual(during, before)


class TestFenceAgreement(unittest.TestCase):
    def test_both_tools_count_the_same_bash_blocks(self):
        counted = step_count.count_files(REPO_ROOT, BASELINE_COMMIT, [FINALIZE_MD])
        static = counted["files"][0]["bash_fences"]
        walked = len(finalize_capture.extract_fences(git_show(FINALIZE_MD)))
        self.assertEqual(static, walked)
        self.assertEqual(static, FINALIZE_FENCES_AT_PIN)


class TestFenceAgreementMutant(unittest.TestCase):
    def _run_agreement(self):
        result = unittest.TestResult()
        TestFenceAgreement("test_both_tools_count_the_same_bash_blocks").run(result)
        return result

    def test_unpatched_agreement_passes(self):
        result = self._run_agreement()
        self.assertEqual((result.failures, result.errors), ([], []))

    def test_column_zero_capture_pattern_breaks_agreement(self):
        col0 = re.compile(r"^```bash\n(.*?)\n```", re.S | re.M)
        self.assertNotEqual(col0.pattern, finalize_capture.FENCE_RE.pattern)
        with mock.patch.object(finalize_capture, "FENCE_RE", col0):
            self.assertLess(len(finalize_capture.extract_fences(git_show(FINALIZE_MD))),
                            FINALIZE_FENCES_AT_PIN)
            result = self._run_agreement()
        self.assertEqual(len(result.failures), 1, result.errors)

    def test_column_zero_count_pattern_breaks_agreement(self):
        col0 = re.compile(r"^```bash$")
        self.assertNotEqual(col0.pattern, step_count.FENCE_OPEN.pattern)
        with mock.patch.object(step_count, "FENCE_OPEN", col0):
            result = self._run_agreement()
        self.assertEqual(len(result.failures), 1, result.errors)


def seed_full_baseline(tmp):
    """A temp baseline dir: copies of the four earlier records, stand-in replay
    reports and a suite record, plus a manifest over them. Returns
    (baseline_dir, live_scripts_dir)."""
    base = os.path.join(tmp, "baseline")
    os.makedirs(base)
    for name in ("steps-v2.14.1.json", "footprint-v2.14.1.json", "traces-v2.14.1.json",
                 "finalize-situations-v2.14.1.json", "finalize-situations-v2.14.1.json.sha256"):
        shutil.copy(os.path.join(BASELINE_DIR, name), base)
    for count, name in baseline_records.REPLAY_FILES.items():
        scripts = make_fake_scripts(os.path.join(tmp, "seed-%d" % count),
                                    transcripts=count, body="count %d" % count)
        got = baseline_records.capture_replay(scripts, os.path.join(base, name))
        write(os.path.join(base, name + ".sha256"), got["sha256"] + "\n")
    rec = {"summary_line": LINE, "baseline_commit": BASELINE_COMMIT,
           "plugins_tree": PLUGINS_TREE, "seconds": 205}
    rec.update(baseline_records.parse_summary_line(LINE))
    write(os.path.join(base, baseline_records.SUITE_FILE), json.dumps(rec, indent=2) + "\n")
    baseline_records.write_manifest(base, baseline_records.build_manifest(base, {}))
    live = make_fake_scripts(os.path.join(tmp, "live"), transcripts=0, body="count 0")
    return base, live


class TestVerifyBaseline(TempDirCase):
    def test_clean_seeded_baseline(self):
        base, live = seed_full_baseline(self.tmp)
        self.assertEqual(baseline_records.verify_baseline(REPO_ROOT, base, live), [])

    def test_each_record_problem_is_prefixed_with_its_file(self):
        base, live = seed_full_baseline(self.tmp)
        path = os.path.join(base, "steps-v2.14.1.json")
        rec = json.loads(read(path))
        rec["totals"]["model_run_steps"] += 1
        write(path, json.dumps(rec))
        problems = baseline_records.verify_baseline(REPO_ROOT, base, live)
        self.assertTrue(any(p.startswith("steps-v2.14.1.json: total differs") for p in problems),
                        problems)
        self.assertTrue(any(p.startswith("MANIFEST.json: steps-v2.14.1.json") for p in problems),
                        problems)

    def test_mutant_manifest_check_switched_off_misses_a_tampered_record(self):
        base, live = seed_full_baseline(self.tmp)
        path = os.path.join(base, REPLAY_WITH + ".sha256")
        # Tamper a file only the manifest guards byte for byte: a trailing
        # space the replay check's .strip() forgives.
        text = read(path)
        write(path, text.rstrip("\n") + " \n")
        self.assertNotEqual(read(path), text)
        problems = baseline_records.verify_baseline(REPO_ROOT, base, live)
        self.assertTrue(any(REPLAY_WITH + ".sha256" in p for p in problems), problems)
        with mock.patch.object(baseline_records, "verify_manifest", lambda d: []):
            self.assertEqual(baseline_records.verify_baseline(REPO_ROOT, base, live), [])

    def test_mutant_suite_record_tree_altered_is_named(self):
        base, live = seed_full_baseline(self.tmp)
        path = os.path.join(base, baseline_records.SUITE_FILE)
        rec = json.loads(read(path))
        rec["plugins_tree"] = "e" * 40
        write(path, json.dumps(rec))
        baseline_records.write_manifest(base, baseline_records.build_manifest(base, {}))
        problems = baseline_records.verify_baseline(REPO_ROOT, base, live)
        self.assertTrue(problems)
        self.assertTrue(all(p.startswith(baseline_records.SUITE_FILE + ":") for p in problems),
                        problems)


class TestCli(TempDirCase):
    def _run(self, *args):
        return subprocess.run([sys.executable, BASELINE_RECORDS_PY] + list(args),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                              timeout=300)

    def test_verify_exit_0_on_clean_and_1_with_banner_on_difference(self):
        base, live = seed_full_baseline(self.tmp)
        ok = self._run("verify", "--repo", REPO_ROOT, "--baseline-dir", base,
                       "--scripts-dir", live)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        write(os.path.join(base, "extra.txt"), "x\n")
        bad = self._run("verify", "--repo", REPO_ROOT, "--baseline-dir", base,
                        "--scripts-dir", live)
        self.assertEqual(bad.returncode, 1)
        self.assertIn("BASELINE DIFFERS — STOPPING", bad.stdout)
        self.assertIn("extra.txt", bad.stdout)

    def test_usage_error_exits_2(self):
        self.assertEqual(self._run("verify").returncode, 2)
        self.assertEqual(self._run("no-such-command").returncode, 2)

    def test_unexpected_recording_count_exits_nonzero_by_name(self):
        base, _ = seed_full_baseline(self.tmp)
        live = make_fake_scripts(os.path.join(self.tmp, "seven"), transcripts=7)
        p = self._run("verify", "--repo", REPO_ROOT, "--baseline-dir", base,
                      "--scripts-dir", live)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("UNEXPECTED RECORDING COUNT 7 — STOPPING", p.stdout + p.stderr)

    def test_capture_replay_cli(self):
        scripts = make_fake_scripts(self.tmp, transcripts=12)
        out = os.path.join(self.tmp, "r.md")
        p = self._run("capture-replay", "--scripts-dir", scripts, "--out", out)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("transcripts: 12", p.stdout)
        self.assertEqual(read(out + ".sha256").strip(),
                         baseline_records.replay_fingerprint(open(out, "rb").read()))

    def test_suite_record_cli(self):
        out = os.path.join(self.tmp, "suite.json")
        p = self._run("suite-record", "--repo", REPO_ROOT, "--summary-line", LINE,
                      "--seconds", "205", "--captured", "2026-11-14", "--out", out)
        self.assertEqual(p.returncode, 0, p.stderr)
        rec = json.loads(read(out))
        self.assertEqual(rec["passed"], 3886)
        self.assertEqual(rec["subtests_passed"], 5060)
        self.assertEqual(rec["plugins_tree"], PLUGINS_TREE)
        self.assertEqual(rec["summary_line"], LINE)
        self.assertTrue(rec["runner"].startswith("pytest "))
        for key in ("python", "platform", "captured", "seconds", "baseline_commit"):
            self.assertIn(key, rec)
        self.assertNotIn(os.uname().nodename, json.dumps(rec))
        self.assertEqual(baseline_records.verify_suite_record(REPO_ROOT, rec), [])


class TestImportSet(unittest.TestCase):
    def _tree(self):
        with open(BASELINE_RECORDS_PY, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_module_level_imports(self):
        names = set()
        for node in self._tree().body:
            if isinstance(node, ast.Import):
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module)
        allowed = {"argparse", "hashlib", "json", "os", "platform", "re", "shutil",
                   "subprocess", "sys", "tempfile",
                   "step_count", "finalize_capture", "path_records"}
        self.assertTrue(names <= allowed, names)
        self.assertNotIn("replay", names)

    def test_every_subprocess_run_has_an_explicit_timeout(self):
        calls = 0
        for node in ast.walk(self._tree()):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "run"
                    and getattr(node.func.value, "id", None) == "subprocess"):
                calls += 1
                self.assertIn("timeout", [kw.arg for kw in node.keywords],
                              "every subprocess.run needs an explicit timeout")
        self.assertGreater(calls, 0, "expected at least one subprocess.run")

    def test_no_live_mode_path_list(self):
        text = read(BASELINE_RECORDS_PY)
        self.assertNotIn("MODE_PATHS", text)
        self.assertNotIn("count_path", text)
        self.assertIn("verify_steps", text)


if __name__ == "__main__":
    unittest.main()
