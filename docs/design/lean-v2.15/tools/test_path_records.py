"""Tests for path_records.py: declared mode-path bytes and loaded-file traces.

The committed records are re-derived from `git show` at the pinned commit on
every run, so these tests hold on any clone with full history. Session logs
are synthetic, built in temp dirs; no real log is ever read here.
"""

import ast
import contextlib
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PATH_RECORDS_PY = os.path.join(HERE, "path_records.py")
BASELINE_DIR = os.path.join(HERE, "..", "baseline")
FOOTPRINT_JSON = os.path.join(BASELINE_DIR, "footprint-v2.14.1.json")
TRACES_JSON = os.path.join(BASELINE_DIR, "traces-v2.14.1.json")

if HERE not in sys.path:
    sys.path.insert(0, HERE)
import path_records  # noqa: E402

# Pinned 2.14.1 figures: 62-CONTEXT.md, re-verified in 62-RESEARCH.md with
# `footprint.py --rev v2.14.1 --json`.
BASELINE = "dd8e4ab42fd0e8bbdaa445df7db2d58621ab18a4"
PINNED = {
    "review-plain": (192057, 13),
    "deep-plain": (268997, 19),
    "finalize": (136114, 7),
}
ALL_MODES = {"review-plain", "review-all", "deep-plain", "deep-all", "finalize", "fix-loop"}


def git_bytes(rel):
    proc = subprocess.run(
        ["git", "-C", REPO, "show", "%s:plugins/vibe-check/%s" % (BASELINE, rel)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    return proc.stdout


def load_footprint():
    with open(FOOTPRINT_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def run_quiet(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = path_records.run(argv)
    return code, out.getvalue(), err.getvalue()


class TestFootprintRecord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = path_records.footprint_record(REPO, BASELINE)

    def test_constants(self):
        self.assertEqual(path_records.BASELINE_COMMIT, BASELINE)
        self.assertEqual(path_records.SCHEMA, 1)
        self.assertEqual(path_records.REQUIRED, {
            "review-plain": "plain review", "deep-plain": "deep review",
            "finalize": "Finalize"})

    def test_shape(self):
        rec = self.rec
        self.assertEqual(rec["schema"], 1)
        self.assertEqual(rec["baseline_commit"], BASELINE)
        self.assertTrue(rec["source"])
        self.assertEqual(set(rec["paths"]), ALL_MODES)
        for mode, entry in rec["paths"].items():
            self.assertEqual(entry["file_count"], len(entry["files"]), mode)
            self.assertEqual(entry["total_bytes"], sum(f["bytes"] for f in entry["files"]))
            self.assertEqual(entry["total_words"], sum(f["words"] for f in entry["files"]))
            for row in entry["files"]:
                self.assertEqual(set(row) >= {"path", "bytes", "words"}, True)
        for mode, label in path_records.REQUIRED.items():
            self.assertEqual(rec["paths"][mode]["label"], label)

    def test_pinned_totals(self):
        for mode, (total, count) in PINNED.items():
            entry = self.rec["paths"][mode]
            self.assertEqual((entry["total_bytes"], entry["file_count"]), (total, count), mode)

    def test_proxies_held_apart(self):
        self.assertNotIn("token", json.dumps(self.rec["paths"]))
        self.assertIn("PROXY", self.rec["proxies"]["label"])
        self.assertEqual(self.rec["proxies"]["label"],
                         "PROXY — derived from bytes, not measured, not a bill")
        self.assertIn("tokens@3.5", json.dumps(self.rec["proxies"]))

    def test_no_price(self):
        self.assertNotIn("$", json.dumps(self.rec))

    def test_verify_fresh_record(self):
        self.assertEqual(path_records.verify_footprint(REPO, self.rec), [])


class TestCommittedFootprint(unittest.TestCase):
    def test_committed_record_verifies(self):
        self.assertEqual(path_records.verify_footprint(REPO, load_footprint()), [])

    def test_committed_record_equals_fresh_capture(self):
        self.assertEqual(load_footprint(), path_records.footprint_record(REPO, BASELINE))

    def test_committed_pinned_totals(self):
        paths = load_footprint()["paths"]
        for mode, (total, count) in PINNED.items():
            self.assertEqual((paths[mode]["total_bytes"], paths[mode]["file_count"]),
                             (total, count), mode)

    def test_independent_finalize_recount(self):
        # Recounted from git without calling the module under test.
        files = load_footprint()["paths"]["finalize"]["files"]
        total = sum(len(git_bytes(f["path"])) for f in files)
        self.assertEqual(total, PINNED["finalize"][0])
        self.assertEqual(total, load_footprint()["paths"]["finalize"]["total_bytes"])

    def test_committed_file_format(self):
        with open(FOOTPRINT_JSON, encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.endswith("}\n"))
        self.assertEqual(text, json.dumps(json.loads(text), indent=2, sort_keys=True,
                                          ensure_ascii=False) + "\n")


class TestFootprintTamper(unittest.TestCase):
    def setUp(self):
        self.rec = load_footprint()

    def test_byte_changed_by_one_named(self):
        m = copy.deepcopy(self.rec)
        row = m["paths"]["finalize"]["files"][3]
        row["bytes"] += 1
        self.assertNotEqual(m, self.rec)
        problems = path_records.verify_footprint(REPO, m)
        self.assertTrue(any("finalize" in p and row["path"] in p for p in problems), problems)

    def test_file_removed_named(self):
        m = copy.deepcopy(self.rec)
        gone = m["paths"]["deep-plain"]["files"].pop(5)
        self.assertNotEqual(m, self.rec)
        problems = path_records.verify_footprint(REPO, m)
        self.assertTrue(any("deep-plain" in p and gone["path"] in p for p in problems), problems)

    def test_total_bytes_changed_named(self):
        m = copy.deepcopy(self.rec)
        m["paths"]["review-plain"]["total_bytes"] -= 7
        self.assertNotEqual(m, self.rec)
        problems = path_records.verify_footprint(REPO, m)
        self.assertTrue(any("review-plain" in p and "total_bytes" in p for p in problems),
                        problems)


class TestFootprintCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.out = os.path.join(self.tmp, "fp.json")

    def test_capture_writes_record(self):
        code, _, _ = run_quiet(["footprint", "--repo", REPO, "--out", self.out])
        self.assertEqual(code, 0)
        with open(self.out, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), load_footprint())

    def test_capture_guard_refuses_on_disagreement(self):
        fp = path_records.load_plugin_module(REPO, "footprint")
        real = fp.path_stats

        def plus_one(root, mode, rev=None):
            stats = real(root, mode, rev=rev)
            if mode == "finalize":
                stats["files"][0] = dict(stats["files"][0], bytes=stats["files"][0]["bytes"] + 1)
                stats["bytes"] += 1
            return stats

        with mock.patch.object(fp, "path_stats", plus_one):
            code, _, err = run_quiet(["footprint", "--repo", REPO, "--out", self.out])
        self.assertEqual(code, 1)
        self.assertIn("FOOTPRINT RECOUNT DISAGREES WITH footprint.py — STOPPING", err)
        self.assertFalse(os.path.exists(self.out))

    def test_unknown_commit_exit_2(self):
        code, _, _ = run_quiet(["footprint", "--repo", REPO, "--out", self.out,
                                "--commit", "0" * 40])
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(self.out))

    def test_unknown_commit_subprocess_exit_2(self):
        proc = subprocess.run(
            [sys.executable, PATH_RECORDS_PY, "footprint", "--repo", REPO, "--out", self.out,
             "--commit", "deadbeefnotacommit"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        self.assertEqual(proc.returncode, 2)


# --------------------------------------------------------------------------- #
# Loaded-file traces
# --------------------------------------------------------------------------- #

FAKE_ROOT = "/fixture/cache/vibe-check/2.14.1"
SESSION_STEM = "abcdef12-3456-7890-abcd-ef1234567890"
SMOKE_LABEL = "2.14.1 (smoke session)"
SENTINEL = "SENTINEL-c41e7b"
_IDS = [0]


def load_traces():
    with open(TRACES_JSON, encoding="utf-8") as fh:
        return json.load(fh)


class Builder:
    """Synthetic session records: assistant tool_use/text, user tool_result/text."""

    def __init__(self, root=FAKE_ROOT):
        self.root = root
        self.records = []

    @staticmethod
    def _id():
        _IDS[0] += 1
        return "toolu_%05d" % _IDS[0]

    def tool(self, name, inp, ok=True, parent=None, content="done"):
        tid = self._id()
        self.records.append({"type": "assistant", "parent_tool_use_id": parent,
                             "message": {"role": "assistant", "content": [
                                 {"type": "tool_use", "id": tid, "name": name,
                                  "input": inp}]}})
        res = {"type": "tool_result", "tool_use_id": tid, "content": content}
        if not ok:
            res["is_error"] = True
            res["content"] = "File does not exist."
        self.records.append({"type": "user", "parent_tool_use_id": parent,
                             "message": {"role": "user", "content": [res]}})
        return tid

    def read(self, rel, ok=True, parent=None, content="file body", absolute=None):
        path = absolute or os.path.join(self.root, rel)
        return self.tool("Read", {"file_path": path}, ok=ok, parent=parent, content=content)

    def user_says(self, text):
        self.records.append({"type": "user", "message": {"role": "user", "content": [
            {"type": "text", "text": text}]}})

    def say(self, text):
        self.records.append({"type": "assistant", "message": {"role": "assistant",
                                                              "content": [{"type": "text",
                                                                           "text": text}]}})


def finalize_builder(sentinel=None):
    b = Builder()
    b.user_says("please finalize %s" % (sentinel or "now"))
    b.read("phases/shared/00-contract.md",
           content="contract " + (sentinel or "body"))
    b.tool("Bash", {"command": "git status"})
    b.read("phases/review/00-scope.md", ok=False)
    b.read("x", absolute="/fixture/repo/src/app.py")
    b.read("phases/shared/90-finalize.md")
    b.read("x", absolute="/fixture/%s/notes.md" % (sentinel or "repo"))
    b.read("templates/review-md-schema.md")
    b.say("done")
    return b


EXPECTED_READS = ["phases/shared/00-contract.md", "phases/shared/90-finalize.md",
                  "templates/review-md-schema.md"]


class TraceCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def write_session(self, records, stem=SESSION_STEM, subagent_records=None):
        path = os.path.join(self.tmp, stem + ".jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")
        if subagent_records is not None:
            sub = os.path.join(self.tmp, stem, "subagents")
            os.makedirs(sub)
            with open(os.path.join(sub, "agent-1.meta.json"), "w") as fh:
                json.dump({"toolUseId": "toolu_parent"}, fh)
            with open(os.path.join(sub, "agent-1.jsonl"), "w") as fh:
                for r in subagent_records:
                    fh.write(json.dumps(r) + "\n")
        return path

    def cli(self, *argv):
        return subprocess.run([sys.executable, PATH_RECORDS_PY, *argv],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                              timeout=120)


class TestPluginRelative(unittest.TestCase):
    def test_versioned_cache_path(self):
        self.assertEqual(path_records.plugin_relative(
            "/any/root/vibe-check/2.14.1/phases/shared/90-finalize.md"),
            "phases/shared/90-finalize.md")

    def test_unversioned_path(self):
        self.assertEqual(path_records.plugin_relative(
            "/snap/plugins/vibe-check/templates/review-md-schema.md"),
            "templates/review-md-schema.md")

    def test_non_plugin_paths(self):
        for p in ["/home/u/repo/src/app.py", "/x/vibe-check/notes/a.md",
                  "/x/other/phases/shared/a.md", "relative/phases/a.md",
                  "/x/vibe-check/2.14.1/extra/phases/a.md"]:
            self.assertIsNone(path_records.plugin_relative(p), p)

    def test_all_plugin_dirs(self):
        for d in ("commands", "phases", "templates", "agents", "scripts"):
            self.assertEqual(path_records.plugin_relative("/r/vibe-check/%s/f.md" % d),
                             "%s/f.md" % d)

    def test_dot_dot_refused(self):
        self.assertIsNone(path_records.plugin_relative("/r/vibe-check/phases/../../etc/x"))


class TestObservedTrace(TraceCase):
    def check_synthetic(self):
        sub = Builder()
        sub.read("phases/review/10-triage.md", parent="toolu_parent")
        path = self.write_session(finalize_builder().records,
                                  subagent_records=sub.records)
        obs = path_records.observed_trace(path, "finalize", SMOKE_LABEL, REPO, BASELINE)
        self.assertEqual(obs["label"], "observed")
        self.assertEqual(obs["kind"], "finalize")
        self.assertEqual(obs["version"], SMOKE_LABEL)
        self.assertIs(obs["smoke_session"], True)
        self.assertEqual(obs["session"], SESSION_STEM[:8])
        self.assertRegex(obs["session_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual([r["path"] for r in obs["reads"]], EXPECTED_READS)
        self.assertEqual(obs["non_plugin_reads"], 2)
        self.assertEqual(obs["tool_calls"], {"Read": 6, "Bash": 1})
        by_path = {r["path"]: r for r in obs["reads"]}
        self.assertEqual(by_path["templates/review-md-schema.md"]["bytes_at_baseline"],
                         len(git_bytes("templates/review-md-schema.md")))
        self.assertIs(by_path["phases/shared/90-finalize.md"]["in_declared"], True)
        self.assertIs(by_path["templates/review-md-schema.md"]["in_declared"], False)
        return obs

    def test_synthetic_session(self):
        self.check_synthetic()

    def test_sha_matches_file(self):
        import hashlib
        path = self.write_session(finalize_builder().records)
        obs = path_records.observed_trace(path, "finalize", SMOKE_LABEL, REPO, BASELINE)
        with open(path, "rb") as fh:
            self.assertEqual(obs["session_sha256"], hashlib.sha256(fh.read()).hexdigest())

    def test_not_smoke_label(self):
        path = self.write_session(finalize_builder().records)
        obs = path_records.observed_trace(path, "finalize", "2.14.1", REPO, BASELINE)
        self.assertIs(obs["smoke_session"], False)

    def test_absent_at_baseline(self):
        b = Builder()
        b.read("phases/shared/99-not-there.md")
        path = self.write_session(b.records)
        obs = path_records.observed_trace(path, "finalize", SMOKE_LABEL, REPO, BASELINE)
        self.assertEqual(obs["reads"], [{"path": "phases/shared/99-not-there.md",
                                         "bytes_at_baseline": None, "at_baseline": "absent",
                                         "in_declared": False}])

    def test_never_echo(self):
        path = self.write_session(finalize_builder(SENTINEL).records)
        with open(path, encoding="utf-8") as fh:
            self.assertIn(SENTINEL, fh.read())
        out = os.path.join(self.tmp, "traces.json")
        proc = self.cli("traces", "--repo", REPO, "--out", out,
                        "--session", "finalize=%s=%s" % (SMOKE_LABEL, path))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        with open(out, encoding="utf-8") as fh:
            written = fh.read()
        self.assertIn("observed", written)
        self.assertNotIn(SENTINEL, proc.stdout + proc.stderr + written)
        self.assertNotIn(self.tmp, proc.stdout + proc.stderr + written)


class TestTracesRecord(TraceCase):
    def test_no_session_is_declared_not_observed(self):
        rec = path_records.traces_record(REPO, BASELINE, [])
        declared = [f["path"] for f in load_footprint()["paths"]["deep-plain"]["files"]]
        self.assertEqual(rec["paths"]["deep-plain"], {
            "label": "declared, not observed",
            "gap": "no recorded 2.14.x session for this path; nothing was run to fill it (D-09)",
            "declared": declared, "observed": []})
        self.assertEqual(set(rec["paths"]), set(path_records.REQUIRED))

    def test_missing_session_named_in_gap(self):
        gone = os.path.join(self.tmp, "deadbeef-0000-0000-0000-000000000000.jsonl")
        rec = path_records.traces_record(REPO, BASELINE, [("finalize", SMOKE_LABEL, gone)])
        entry = rec["paths"]["finalize"]
        self.assertEqual(entry["label"], "declared, not observed")
        self.assertIn("deadbeef", entry["gap"])
        self.assertNotIn(self.tmp, json.dumps(rec))

    def test_synthetic_record_verifies(self):
        path = self.write_session(finalize_builder().records)
        rec = path_records.traces_record(REPO, BASELINE, [("finalize", SMOKE_LABEL, path)])
        self.assertEqual(path_records.verify_traces_record(REPO, rec), [])
        self.assertEqual(rec["paths"]["finalize"]["label"], "observed")

    def test_notes_name_command_expansion(self):
        rec = path_records.traces_record(REPO, BASELINE, [])
        self.assertTrue(any("commands/review.md" in n and "expansion" in n
                            for n in rec["notes"]))

    def test_traces_refuses_private_content(self):
        path = self.write_session(finalize_builder().records)
        out = os.path.join(self.tmp, "t.json")
        with mock.patch.object(path_records, "plugin_relative",
                               lambda p: "/Users/x/notes/secret.md"):
            code, _, err = run_quiet(["traces", "--repo", REPO, "--out", out,
                                      "--session", "finalize=%s=%s" % (SMOKE_LABEL, path)])
        self.assertEqual(code, 1)
        self.assertIn("TRACES RECORD HOLDS PRIVATE CONTENT — STOPPING", err)
        self.assertNotIn("/Users/x", err)
        self.assertFalse(os.path.exists(out))

    def test_bad_session_argument_exit_2(self):
        code, _, _ = run_quiet(["traces", "--repo", REPO, "--out",
                                os.path.join(self.tmp, "t.json"), "--session", "nokind"])
        self.assertEqual(code, 2)
        code, _, _ = run_quiet(["traces", "--repo", REPO, "--out",
                                os.path.join(self.tmp, "t.json"), "--session",
                                "fix-loop=v=/x.jsonl"])
        self.assertEqual(code, 2)


class TestVerifyTraces(TraceCase):
    def test_missing_session_exit_2(self):
        gone = os.path.join(self.tmp, "nope.jsonl")
        code, out, err = run_quiet(["verify-traces", "--traces", TRACES_JSON,
                                    "--session", "finalize=%s=%s" % (SMOKE_LABEL, gone)])
        self.assertEqual(code, 2)
        self.assertIn("SESSION FILES NOT ON THIS MACHINE — RE-EXTRACTION NOT RUN", err)

    def test_reextraction_matches_then_detects_change(self):
        path = self.write_session(finalize_builder().records)
        rec_path = os.path.join(self.tmp, "t.json")
        arg = "finalize=%s=%s" % (SMOKE_LABEL, path)
        self.assertEqual(run_quiet(["traces", "--repo", REPO, "--out", rec_path,
                                    "--session", arg])[0], 0)
        self.assertEqual(run_quiet(["verify-traces", "--repo", REPO, "--traces", rec_path,
                                    "--session", arg])[0], 0)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\n")
        code, _, err = run_quiet(["verify-traces", "--repo", REPO, "--traces", rec_path,
                                  "--session", arg])
        self.assertEqual(code, 1)
        self.assertIn(SESSION_STEM[:8], err)

    def test_verify_cli_on_committed(self):
        proc = self.cli("verify", "--repo", REPO, "--footprint", FOOTPRINT_JSON,
                        "--traces", TRACES_JSON)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_verify_cli_planted_path_exit_1(self):
        m = load_traces()
        m["paths"]["deep-plain"]["gap"] = "see /Users/x/notes/secret.md"
        planted = os.path.join(self.tmp, "planted.json")
        with open(planted, "w", encoding="utf-8") as fh:
            json.dump(m, fh)
        proc = self.cli("verify", "--repo", REPO, "--footprint", FOOTPRINT_JSON,
                        "--traces", planted)
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn("/Users/x", proc.stdout + proc.stderr)


class TestCommittedTraces(unittest.TestCase):
    def setUp(self):
        self.rec = load_traces()

    def test_committed_traces_verify(self):
        self.assertEqual(path_records.verify_traces_record(REPO, self.rec), [])

    def test_required_paths_and_labels(self):
        paths = self.rec["paths"]
        self.assertEqual(set(paths), {"review-plain", "deep-plain", "finalize"})
        self.assertEqual(paths["deep-plain"]["label"], "declared, not observed")
        self.assertTrue(paths["deep-plain"]["gap"])
        self.assertEqual(paths["deep-plain"]["observed"], [])
        for mode in ("finalize", "review-plain"):
            obs = [o for o in paths[mode]["observed"] if o["label"] == "observed"]
            self.assertTrue(obs, mode)
            for o in obs:
                self.assertTrue(o["version"])
                self.assertIs(o["smoke_session"], True)
                self.assertEqual(len(o["session"]), 8)
                self.assertRegex(o["session_sha256"], r"^[0-9a-f]{64}$")

    def test_declared_matches_footprint(self):
        fp = load_footprint()
        for mode, entry in self.rec["paths"].items():
            self.assertEqual(entry["declared"], [f["path"] for f in fp["paths"][mode]["files"]])

    def test_committed_traces_hold_no_private_path(self):
        self.assertEqual(path_records.private_content_problems(self.rec), [])
        text = json.dumps(self.rec)
        for marker in ("/Users/", "/private/", "/home/", ".claude/projects"):
            self.assertNotIn(marker, text)

    def test_committed_traces_hold_no_long_string(self):
        self.assertEqual(path_records.private_content_problems(self.rec), [])
        self.assertEqual(path_records.private_content_problems(load_footprint()), [])

    def test_committed_file_format(self):
        with open(TRACES_JSON, encoding="utf-8") as fh:
            text = fh.read()
        self.assertEqual(text, json.dumps(json.loads(text), indent=2, sort_keys=True,
                                          ensure_ascii=False) + "\n")


def plant_private_path(rec):
    m = copy.deepcopy(rec)
    m["paths"]["finalize"]["observed"][0]["reads"][0]["path"] = "/Users/x/notes/secret.md"
    return m


def plant_long_gap(rec, n):
    m = copy.deepcopy(rec)
    m["paths"]["deep-plain"]["gap"] = "g" * n
    return m


def plant_full_session(rec):
    m = copy.deepcopy(rec)
    m["paths"]["finalize"]["observed"][0]["session"] = "abcdef12-3456-7890-abcd-ef1234567890"
    return m


class TestPrivateContentLock(unittest.TestCase):
    def setUp(self):
        self.rec = load_traces()

    def test_planted_private_path_reported(self):
        m = plant_private_path(self.rec)
        self.assertNotEqual(m, self.rec)
        self.assertIn("/Users/x/notes/secret.md", json.dumps(m))
        problems = path_records.private_content_problems(m)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("paths.finalize.observed[0].reads[0].path", problems[0])
        self.assertNotIn("/Users/", problems[0])

    def test_each_private_marker_reported(self):
        for marker in ("/Users/", "/private/", "/home/", ".claude/projects"):
            m = copy.deepcopy(self.rec)
            m["paths"]["deep-plain"]["gap"] = "x %s y" % marker
            self.assertEqual(len(path_records.private_content_problems(m)), 1, marker)

    def test_private_key_reported(self):
        m = copy.deepcopy(self.rec)
        m["paths"]["finalize"]["/home/u"] = 1
        self.assertEqual(len(path_records.private_content_problems(m)), 1)

    def test_planted_201_char_string_reported(self):
        m = plant_long_gap(self.rec, 201)
        self.assertNotEqual(m, self.rec)
        self.assertEqual(len(m["paths"]["deep-plain"]["gap"]), 201)
        problems = path_records.private_content_problems(m)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("paths.deep-plain.gap", problems[0])
        self.assertNotIn("g" * 20, problems[0])

    def test_200_char_string_not_reported(self):
        m = plant_long_gap(self.rec, 200)
        self.assertEqual(len(m["paths"]["deep-plain"]["gap"]), 200)
        self.assertEqual(path_records.private_content_problems(m), [])

    def test_planted_full_session_id_reported(self):
        m = plant_full_session(self.rec)
        self.assertNotEqual(m, self.rec)
        self.assertEqual(len(m["paths"]["finalize"]["observed"][0]["session"]), 36)
        problems = path_records.private_content_problems(m)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("session", problems[0])

    def test_verify_includes_private_lines(self):
        problems = path_records.verify_traces_record(REPO, plant_long_gap(self.rec, 201))
        self.assertTrue(any("paths.deep-plain.gap" in p for p in problems), problems)


class TestTracesTamper(unittest.TestCase):
    def setUp(self):
        self.rec = load_traces()

    def problems(self, m):
        self.assertNotEqual(m, self.rec)
        return path_records.verify_traces_record(REPO, m)

    def test_observed_relabelled(self):
        m = copy.deepcopy(self.rec)
        m["paths"]["finalize"]["observed"][0]["label"] = "declared, not observed"
        self.assertTrue(any("finalize" in p and "label" in p for p in self.problems(m)))

    def test_made_up_observed_entry(self):
        m = copy.deepcopy(self.rec)
        fake = copy.deepcopy(m["paths"]["finalize"]["observed"][0])
        del fake["session_sha256"]
        m["paths"]["deep-plain"]["observed"].append(fake)
        problems = self.problems(m)
        self.assertTrue(any("deep-plain" in p and "session_sha256" in p for p in problems),
                        problems)

    def test_bytes_at_baseline_changed(self):
        m = copy.deepcopy(self.rec)
        row = m["paths"]["review-plain"]["observed"][0]["reads"][0]
        row["bytes_at_baseline"] += 1
        self.assertTrue(any("review-plain" in p and row["path"] in p
                            for p in self.problems(m)))

    def test_observed_merged_into_declared(self):
        m = copy.deepcopy(self.rec)
        entry = m["paths"]["finalize"]
        for r in entry["observed"][0]["reads"]:
            if r["path"] not in entry["declared"]:
                entry["declared"].append(r["path"])
        self.assertTrue(any("finalize" in p and "declared" in p for p in self.problems(m)))

    def test_gap_emptied(self):
        m = copy.deepcopy(self.rec)
        m["paths"]["deep-plain"]["gap"] = ""
        self.assertTrue(any("deep-plain" in p and "gap" in p for p in self.problems(m)))


class TestMutants(TraceCase):
    def test_read_filter_off_trips_synthetic_test(self):
        tc = path_records.load_plugin_module(REPO, "tracecheck")

        def all_attempts(evts, main_only=False):
            return [(i, p) for i, p, parent in tc.read_attempts(evts)
                    if not (main_only and parent)]

        with mock.patch.object(tc, "successful_reads", all_attempts):
            with self.assertRaises(AssertionError):
                TestObservedTrace.check_synthetic(self)

    def test_lock_off_misses_both_plants(self):
        rec = load_traces()
        planted = [plant_private_path(rec), plant_long_gap(rec, 201)]
        for m in planted:
            self.assertTrue(any("paths." in p for p in
                                path_records.verify_traces_record(REPO, m)))
        with mock.patch.object(path_records, "private_content_problems", lambda r: []):
            self.assertEqual(path_records.verify_traces_record(REPO, planted[1]), [])
            # The planted path also breaks the git byte check, so only the lock's
            # own location line disappears.
            self.assertFalse(any("paths.finalize.observed[0].reads[0].path" in p for p in
                                 path_records.verify_traces_record(REPO, planted[0])))
            self.assertEqual(path_records.private_content_problems(planted[0]), [])
            self.assertEqual(path_records.private_content_problems(planted[1]), [])



class TestImportSet(unittest.TestCase):
    ALLOWED = {"argparse", "hashlib", "json", "os", "subprocess", "sys",
               "footprint", "tracecheck"}

    def test_path_records_imports(self):
        with open(PATH_RECORDS_PY, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        self.assertTrue(names <= self.ALLOWED, names - self.ALLOWED)


if __name__ == "__main__":
    unittest.main()
