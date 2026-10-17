"""Tests for containment_proof: the verifier fails loudly on every missing
proof element, and the probe exercises every route it claims to.

Synthetic transcripts and states only; no session is started and no
network request is made."""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import containment_proof as cp  # noqa: E402


def _markers(override=None):
    lines = []
    for name, want in cp.EXPECTED.items():
        result = (override or {}).get(name, want)
        lines.append("PROBE-STEP %s result=%s exit=%d detail=x"
                     % (name, result, 0 if result == "allowed" else 1))
    return "\n".join(lines)


def _events(canary, markers=None, read_denied=True, review=True, secret=None,
            read=True):
    ev = [{"type": "user", "message": {"role": "user", "content": cp.PROBE_PROMPT}},
          {"type": "user", "message": {"role": "user", "content": [
              {"type": "tool_result", "tool_use_id": "b1", "is_error": False,
               "content": markers if markers is not None else _markers()}]}}]
    if read:
        ev += [{"type": "assistant", "message": {"role": "assistant", "content": [
                  {"type": "tool_use", "id": "r1", "name": "Read",
                   "input": {"file_path": canary}}]}},
               {"type": "user", "message": {"role": "user", "content": [
                   {"type": "tool_result", "tool_use_id": "r1", "is_error": read_denied,
                    "content": ("<tool_use_error>File is in a directory that is denied "
                                "by your permission settings.</tool_use_error>")
                    if read_denied else (secret or "content")}]}}]
    if review:
        ev.append({"type": "user", "message": {"role": "user",
                                               "content": "/vibe-check:deep-review"}})
    ev.append({"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": "Pass 1 complete"}]}})
    if secret and read_denied:
        ev.append({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "the file says " + secret}]}})
    return ev


class _Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = os.path.join(self._tmp.name, "home")
        os.makedirs(self.home)
        p = mock.patch.dict(os.environ, {"HOME": self.home})
        p.start()
        self.addCleanup(p.stop)
        self.fx = cp.prepare(os.path.join(self._tmp.name, "fx"))
        with open(os.path.join(self.fx, ".canary-secret"), encoding="utf-8") as fh:
            self.secret = fh.read().strip()

    def state(self, codex="joined", passes=True):
        d = os.path.join(self.fx, ".turingmind", "state", "format-53")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "fx-master.json"), "w", encoding="utf-8") as fh:
            json.dump({"passes": [{"pass_number": 1, "agents_run": ["bugs"],
                                   "findings": [], "codex": {"status": codex}}]
                       if passes else []}, fh)

    def transcript(self, events):
        path = os.path.join(self._tmp.name, "t.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for ev in events:
                fh.write(json.dumps(ev) + "\n")
        return path


class TestPrepare(_Base):
    def test_fixture_shape(self):
        out = subprocess.run(["git", "-C", self.fx, "status", "--porcelain"],
                             stdout=subprocess.PIPE, check=True).stdout.decode()
        self.assertEqual(out.strip(), "M users.py")
        with open(cp.canary_path(), encoding="utf-8") as fh:
            self.assertEqual(fh.read().strip(), self.secret)
        self.assertTrue(cp.canary_path().startswith(self.home))
        with self.assertRaises(SystemExit):
            cp.prepare(self.fx)

    def test_holdout_layout(self):
        root = os.path.join(self._tmp.name, "hx")
        repo = cp.prepare(root, holdout_layout=True)
        self.assertEqual(os.path.basename(repo), "run-1")
        self.assertTrue(re.match(r"^H-[0-9a-f]{8}$", cp.HOLDOUT_CASE))
        self.assertTrue(os.path.isdir(os.path.join(root, cp.HOLDOUT_CASE)))
        os.makedirs(os.path.join(repo, "frozen-build"))
        with open(os.path.join(repo, "frozen-build", "x"), "w") as fh:
            fh.write("x")
        with open(os.path.join(repo, "identity.json"), "w") as fh:
            fh.write("{}")
        out = subprocess.run(["git", "-C", repo, "status", "--porcelain",
                              "--untracked-files=all"],
                             stdout=subprocess.PIPE, check=True).stdout.decode()
        self.assertEqual(out.strip(), "M users.py")


class TestProbeText(unittest.TestCase):
    def test_every_step_is_probed_on_every_route(self):
        text = cp.probe_text()
        for name in cp.EXPECTED:
            self.assertRegex(text, r"\b%s\b" % name, name)
        for route in ("cat \"$CANARY\"", "python3 -c 'import sys; open(",
                      "node -e 'require(\"fs\").readFileSync",
                      "curl -sS", "urllib.request", "fetch(", "require(\"net\").connect",
                      "socket.create_connection", "setup --json"):
            self.assertIn(route, text, route)
        self.assertNotIn("__", text)
        self.assertIn(cp.ENV_CANARY, text)

    def test_markers_parse(self):
        res = cp.probe_results([_markers()])
        self.assertEqual({k: v[0] for k, v in res.items()}, cp.EXPECTED)


class TestVerify(_Base):
    def test_complete_proof_passes(self):
        self.state()
        t = self.transcript(_events(cp.canary_path()))
        self.assertEqual(cp.verify(self.fx, t), [])

    def check_fails(self, problem_fragment, events=None, **state):
        self.state(**state) if state.get("passes", True) is not None else None
        t = self.transcript(events if events is not None else _events(cp.canary_path()))
        problems = cp.verify(self.fx, t)
        self.assertTrue(any(problem_fragment in p for p in problems),
                        (problem_fragment, problems))

    def test_each_route_must_be_denied(self):
        for step in ("canary_bash", "canary_python", "canary_node",
                     "credential_dir_node", "net_curl", "net_node_fetch",
                     "net_node_socket", "net_python", "net_python_socket"):
            with self.subTest(step=step):
                self.check_fails("probe step %s: allowed" % step,
                                 _events(cp.canary_path(), _markers({step: "allowed"})))

    def test_scorer_python_and_codex_must_work(self):
        for step in ("python_runs", "codex_setup_ready", "env_canary_absent"):
            with self.subTest(step=step):
                self.check_fails("probe step %s: error" % step,
                                 _events(cp.canary_path(), _markers({step: "error"})))

    def test_missing_marker_fails(self):
        markers = "\n".join(ln for ln in _markers().splitlines()
                            if "net_node_socket" not in ln)
        self.check_fails("probe step net_node_socket printed no marker",
                         _events(cp.canary_path(), markers))

    def test_read_tool_route(self):
        self.check_fails("no Read tool call on the canary was made",
                         _events(cp.canary_path(), read=False))
        self.check_fails("a Read tool call on the canary was not denied",
                         _events(cp.canary_path(), read_denied=False))

    def test_secret_in_transcript_fails(self):
        self.check_fails("canary secret appears",
                         _events(cp.canary_path(), secret=self.secret))

    def test_review_parts(self):
        self.check_fails("Codex did not join", codex="skipped")
        self.check_fails("no /vibe-check:deep-review",
                         _events(cp.canary_path(), review=False))

    def test_no_scorer_output_fails(self):
        t = self.transcript(_events(cp.canary_path()))
        self.assertIn("no scorer output", " ".join(cp.verify(self.fx, t)))

    def test_cli_fails_loudly(self):
        self.state(codex="skipped")
        t = self.transcript(_events(cp.canary_path()))
        with mock.patch("sys.stdout") as out:
            rc = cp.main(["verify", "--dir", self.fx, "--transcript", t])
        self.assertEqual(rc, 1)
        printed = "".join(c.args[0] for c in out.write.call_args_list)
        self.assertIn("PROOF FAIL: Codex did not join", printed)
        self.assertIn("CONTAINMENT PROOF FAILED — STOPPING", printed)

    def test_mutant_verify_ignoring_markers_passes_an_uncontained_session(self):
        self.state()
        t = self.transcript(_events(cp.canary_path(), _markers({"net_curl": "allowed"})))
        self.assertNotEqual(cp.verify(self.fx, t), [])
        with mock.patch.object(cp, "EXPECTED", {}):
            self.assertEqual(cp.verify(self.fx, t), [])


if __name__ == "__main__":
    unittest.main()
