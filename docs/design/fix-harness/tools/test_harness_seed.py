"""Tests for harness_seed: the answer-key record becomes a pass-1 state the
plugin itself scored and shape-checked, and no key material enters the copy.

Run with bare `pytest -q` from this directory.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness_fixture as hf  # noqa: E402
import harness_seed as hs  # noqa: E402

CASE = "py-clamp-01"
KEY_PATH = hf.KEYS_DIR / ("%s.json" % CASE)


def _key():
    with open(KEY_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _git(repo, *args):
    proc = subprocess.run(["git", *args], cwd=repo, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, timeout=60)
    if proc.returncode != 0:
        raise AssertionError("git %s failed: %s" % (args, proc.stderr))
    return proc.stdout


def _listing(root):
    """Every path under root outside .git/ (files and directories)."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        for name in dirnames + filenames:
            out.append(os.path.relpath(os.path.join(dirpath, name), root))
    return sorted(out)


def _plugin(script, *args, stdin=None):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(hf.PLUGIN_SCRIPTS_DIR / script), *args],
        input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=60, env=env)


class _CopyCase(unittest.TestCase):
    MODE = "default"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.copy = hf.build_copy(hf.load_recipe(CASE), self.MODE,
                                  self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class TestKeyToFinding(unittest.TestCase):
    def setUp(self):
        self.source = (hf.FIXTURES_DIR / CASE / "defect" / "src"
                       / "clamp.py").read_bytes()

    def test_whitelisted_fields_only(self):
        f = hs.key_to_finding(_key(), self.source)
        for banned in ("defect_check", "expected_commit_files", "axis",
                       "case_id"):
            self.assertNotIn(banned, f)
        k = _key()
        for field in ("file", "line", "title", "problem", "current_code",
                      "fix_hint", "agent"):
            self.assertEqual(f[field], k[field])
        self.assertNotIn("defect_check", json.dumps(f))

    def test_raw_facts_read_from_the_source(self):
        f = hs.key_to_finding(_key(), self.source)
        lines = self.source.decode("utf-8").splitlines()
        self.assertEqual(f["source_window"], lines[10:15])
        self.assertEqual(f["canonical_line_content"],
                         "    if value > hi - 1:")

    def test_line_outside_the_file_is_refused(self):
        k = _key()
        k["line"] = 999
        with self.assertRaises(hs.SeedError):
            hs.key_to_finding(k, self.source)

    def test_missing_field_is_refused_without_echoing_the_title(self):
        k = _key()
        del k["problem"]
        with self.assertRaises(hs.SeedError) as ctx:
            hs.key_to_finding(k, self.source)
        self.assertNotIn(k["title"], str(ctx.exception))

    def test_band_below_warning_is_refused(self):
        k = _key()
        k["band"] = "medium"
        with self.assertRaises(hs.SeedError):
            hs.key_to_finding(k, self.source)


class _SeedTests:
    """Shared assertions run in both layouts."""

    def _seed(self):
        before_status = _git(self.copy.root, "status", "--porcelain")
        before = _listing(self.copy.root)
        path = hs.seed_state(self.copy, _key(), self.MODE)
        return path, before, before_status

    def test_state_lands_at_the_mode_correct_path(self):
        path, _, _ = self._seed()
        self.assertEqual(os.path.realpath(path),
                         os.path.realpath(os.path.join(self.copy.root,
                                                       self.EXPECTED_REL)))
        self.assertTrue(os.path.isfile(path))

    def test_state_is_plugin_shaped_pass_one(self):
        path, _, _ = self._seed()
        with open(path, "r", encoding="utf-8") as fh:
            state = json.load(fh)
        self.assertEqual(state["medium_acknowledgments"], {})
        self.assertEqual(len(state["passes"]), 1)
        p = state["passes"][0]
        self.assertEqual(p["pass_number"], 1)
        self.assertEqual(p["head_sha"], self.copy.head_sha)
        self.assertEqual(len(p["findings"]), 1)
        f = p["findings"][0]
        self.assertIn(f["band"], ("critical", "warning"))
        self.assertEqual((f["file"], f["title"]),
                         (_key()["file"], _key()["title"]))
        # score.py wrote the scored fields, not the harness.
        for field in ("orchestrator_score", "stable_hash", "attribution",
                      "status", "snapshot"):
            self.assertIn(field, f)
        self.assertEqual(path.stable_hash, f["stable_hash"])
        self.assertEqual(path.seeded_identity,
                         (_key()["file"], _key()["title"]))
        rc = _plugin("state_shape.py", str(path), "--schema", "future")
        self.assertEqual(rc.returncode, 0, rc.stdout + rc.stderr)

    def test_batch_card_lists_exactly_the_seeded_row(self):
        path, _, _ = self._seed()
        with open(path, "r", encoding="utf-8") as fh:
            rc = _plugin("batch_card.py", "rows", "--mode", "fix-loop",
                         stdin=fh.read())
        self.assertEqual(rc.returncode, 0, rc.stderr)
        doc = json.loads(rc.stdout)
        self.assertEqual(len(doc["rows"]), 1)
        row = doc["rows"][0]
        k = _key()
        self.assertEqual((row["file"], row["line"], row["title"]),
                         (k["file"], k["line"], k["title"]))
        self.assertIn("#1 %s:%d" % (k["file"], k["line"]), doc["card_text"])

    def test_seeder_writes_only_the_state_file(self):
        path, before, before_status = self._seed()
        after = _listing(self.copy.root)
        rel = os.path.relpath(path, self.copy.root)
        added = sorted(set(after) - set(before))
        expected = sorted({".turingmind", ".turingmind/state", rel}
                          - set(before))
        self.assertEqual(added, expected)
        self.assertEqual(sorted(set(before) - set(after)), [])
        self.assertEqual(_git(self.copy.root, "status", "--porcelain"),
                         before_status)
        self.assertEqual(_git(self.copy.root, "rev-parse", "HEAD").strip(),
                         self.copy.head_sha)

    def test_copy_is_key_free_after_seeding(self):
        self.assertTrue(hs.copy_is_key_free(self.copy.root))
        self._seed()
        self.assertTrue(hs.copy_is_key_free(self.copy.root))

    def test_mutant_key_written_into_the_copy_is_caught(self):
        self._seed()
        planted = Path(self.copy.root, ".turingmind", "key.json")
        planted.write_bytes(KEY_PATH.read_bytes())
        self.assertFalse(hs.copy_is_key_free(self.copy.root))

    def test_mutant_each_needle_alone_flips_the_lock(self):
        self._seed()
        planted = Path(self.copy.root, ".turingmind", "note.txt")
        for needle in ("defect_check", "expected_commit_files", '"axis"',
                       str(KEY_PATH)):
            planted.write_text("x %s y\n" % needle, encoding="utf-8")
            self.assertFalse(hs.copy_is_key_free(self.copy.root), needle)
        planted.unlink()
        self.assertTrue(hs.copy_is_key_free(self.copy.root))


class TestSeedDefault(_SeedTests, _CopyCase):
    MODE = "default"
    EXPECTED_REL = ".turingmind/state/repo-main.json"


class TestSeedGsd(_SeedTests, _CopyCase):
    MODE = "gsd"
    EXPECTED_REL = ".turingmind/state/52-harness-case.json"


class TestSeedRefusals(_CopyCase):
    def test_existing_state_is_never_overwritten(self):
        hs.seed_state(self.copy, _key(), "default")
        with self.assertRaises(hs.SeedError):
            hs.seed_state(self.copy, _key(), "default")

    def test_unknown_mode_is_refused(self):
        with self.assertRaises(ValueError):
            hs.seed_state(self.copy, _key(), "pr")

    def test_finding_that_does_not_survive_scoring_is_refused(self):
        k = _key()
        k["current_code"] = "    if value > hi - 1:  # noqa"
        src = Path(self.copy.root, k["file"])
        data = src.read_bytes().replace(b"    if value > hi - 1:\n",
                                        b"    if value > hi - 1:  # noqa\n")
        src.write_bytes(data)
        _git(self.copy.root, "commit", "-qam", "silence")
        info = self.copy._replace(
            head_sha=_git(self.copy.root, "rev-parse", "HEAD").strip())
        with self.assertRaises(hs.SeedError):
            hs.seed_state(info, k, "default")
        self.assertFalse(Path(self.copy.root, ".turingmind",
                              "state", "repo-main.json").exists())


class TestSeedGates(_CopyCase):
    """The two plugin gates are load-bearing: a fake plugin reply that a real
    run cannot produce proves each refusal branch is wired."""

    def _patched(self, rewrite):
        real = hs._plugin

        def fake(script, *args, stdin=None):
            proc = real(script, *args, stdin=stdin)
            return rewrite(Path(script).name, proc)
        return mock.patch.object(hs, "_plugin", side_effect=fake)

    def _state(self):
        return Path(self.copy.root, ".turingmind", "state", "repo-main.json")

    def test_survivor_below_warning_is_refused(self):
        def demote(name, proc):
            if name != "score.py":
                return proc
            out = json.loads(proc.stdout)
            out["findings"][0]["band"] = "medium"
            return proc.__class__(proc.args, 0, json.dumps(out), "")
        with self._patched(demote):
            with self.assertRaises(hs.SeedError):
                hs.seed_state(self.copy, _key(), "default")
        self.assertFalse(self._state().exists())

    def test_shape_rejection_is_refused_and_leaves_no_state(self):
        def reject(name, proc):
            if name != "state_shape.py":
                return proc
            return proc.__class__(proc.args, 1, "", "bad shape\n")
        with self._patched(reject):
            with self.assertRaises(hs.SeedError):
                hs.seed_state(self.copy, _key(), "default")
        self.assertFalse(self._state().exists())

    def test_score_is_given_the_defect_hunk_as_changed_lines(self):
        seen = {}
        real = hs._plugin

        def spy(script, *args, stdin=None):
            if Path(script).name == "score.py":
                seen.update(json.loads(stdin))
            return real(script, *args, stdin=stdin)
        with mock.patch.object(hs, "_plugin", side_effect=spy):
            hs.seed_state(self.copy, _key(), "default")
        recipe = hf.load_recipe(CASE)
        self.assertEqual(seen["changed_line_ranges"],
                         {_key()["file"]: [recipe["hunk_lines"]]})
        self.assertEqual(seen["codex"], {"status": "off"})
        self.assertEqual(seen["command"], "review")


class TestNoShell(unittest.TestCase):
    def test_no_shell_true_in_the_tools(self):
        here = Path(__file__).resolve().parent
        needle = "shell" + "=True"
        for py in here.glob("*.py"):
            if py.name.startswith("test_"):
                continue
            self.assertNotIn(needle, py.read_text(encoding="utf-8"),
                             py.name)


if __name__ == "__main__":
    unittest.main()
