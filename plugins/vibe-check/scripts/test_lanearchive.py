"""Tests for lanearchive.py — the per-run raw-lane / Codex archive extractor.

Every lock carries a demonstrated failure: decoys are recovered once their
filter is removed, planted private tokens make `extract` refuse and leave
nothing behind, and a joined run that cannot produce its Codex payload is an
extraction failure rather than a silent `codex-absent.txt`.
"""

import ast
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lanearchive  # noqa: E402  (sibling module under test)
import replay  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LANEARCHIVE_PY = os.path.join(HERE, "lanearchive.py")

BUGS_RETURN = {"agent": "bugs", "findings": [{"file": "a.py", "line": 3, "title": "t"}],
               "agent_notes": ["checked a.py"]}
SEC_RETURN = {"agent": "security", "findings": [], "agent_notes": ["nothing"]}
CODEX_OBJ = {"agent": "codex-adversarial", "findings": [{"file": "a.py", "line": 4}],
             "agent_notes": ["codex summary"]}
DECOY = {"agent": "impact", "findings": [{"file": "decoy.py", "line": 9}]}


def _assistant(tool_uses, usage=None, sidechain=False, agent_id=None):
    rec = {"type": "assistant", "isSidechain": sidechain,
           "message": {"content": tool_uses}}
    if usage is not None:
        rec["message"]["usage"] = usage
    if agent_id:
        rec["agentId"] = agent_id
    return rec


def _tool_use(tid, name, inp):
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def _result(tid, text):
    return {"type": "user", "isSidechain": False, "message": {"content": [
        {"type": "tool_result", "tool_use_id": tid,
         "content": [{"type": "text", "text": text}]}]}}


def _notification(tid, task_id, body):
    return ("<task-notification>\n<task-id>%s</task-id>\n<tool-use-id>%s</tool-use-id>\n"
            "<status>completed</status>\n<result>%s</result>\n</task-notification>"
            % (task_id, tid, body))


class _TmpDirCase(unittest.TestCase):
    def setUp(self):
        # Under the user's temp root, so the CODEX_DIR containment rule accepts it.
        self.tmp = tempfile.mkdtemp(prefix="test-lanearchive-")
        self.codex_dir = os.path.join(self.tmp, "codexdir")
        os.makedirs(self.codex_dir)
        with open(os.path.join(self.codex_dir, "payload.json"), "w") as fh:
            fh.write('{"result": {"verdict": "approve", "findings": []}}\n')
        with open(os.path.join(self.codex_dir, "rc"), "w") as fh:
            fh.write("0\n")
        self.out = os.path.join(self.tmp, "run-1")
        os.makedirs(self.out)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def records(self, bugs_return=None, codex_dir_line=True, extra=()):
        bugs_return = json.dumps(bugs_return or BUGS_RETURN)
        recs = [
            _assistant([_tool_use("tu_bugs", "Agent", {"subagent_type": "vibe-check:bugs",
                                                       "prompt": "review"})],
                       usage={"input_tokens": 10, "cache_read_input_tokens": 1000,
                              "cache_creation_input_tokens": 200}),
            _result("tu_bugs", "Async agent launched successfully.\nagentId: abugs1 (internal)"),
            _assistant([_tool_use("tu_sec", "Agent", {"subagent_type": "vibe-check:security"})],
                       usage={"input_tokens": 5, "cache_read_input_tokens": 3000}),
            _result("tu_sec", "Async agent launched successfully.\nagentId: asec22 (internal)"),
            # A Write whose payload is findings-shaped: never a channel.
            _assistant([_tool_use("tu_write", "Write", {"file_path": "/x",
                                                        "content": json.dumps(DECOY)})]),
            _result("tu_write", "File created successfully"),
            # The bugs return, as a task notification (queued copy + user copy).
            {"type": "queue-operation", "operation": "enqueue",
             "content": _notification("tu_bugs", "abugs1", "```json\n%s\n```" % bugs_return)},
            {"type": "user", "isSidechain": False,
             "message": {"content": _notification("tu_bugs", "abugs1",
                                                  "```json\n%s\n```" % bugs_return)}},
            # The security return, via a sidechain SubagentHandback.
            _assistant([_tool_use("tu_hb", "SubagentHandback",
                                  {"message": json.dumps(SEC_RETURN)})],
                       sidechain=True, agent_id="asec22",
                       usage={"input_tokens": 999999}),
            # Codex: the kickoff prints CODEX_DIR, the translator prints the object.
            _assistant([_tool_use("tu_kick", "Bash", {"command": "mktemp -d"})],
                       usage={"input_tokens": 1, "cache_read_input_tokens": 4000,
                              "cache_creation_input_tokens": 500}),
            _result("tu_kick", ("CODEX_DIR=%s\nSTARTED_AT=1790000000" % self.codex_dir)
                    if codex_dir_line else "STARTED_AT=1790000000"),
            _assistant([_tool_use("tu_tr", "Bash", {"command": "translate"})]),
            _result("tu_tr", json.dumps(CODEX_OBJ)),
        ]
        recs.extend(extra)
        return recs

    def write_transcript(self, records, name="transcript.jsonl", malformed=0):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec) + "\n")
            for _ in range(malformed):
                fh.write("not json\n")
        return path

    def write_state(self, status="joined", reason=None, name="state.json"):
        path = os.path.join(self.tmp, name)
        state = {"passes": [{"findings": [], "codex": {
            "status": status, "reason": reason,
            "verdict": "approve" if status == "joined" else None, "findings": 0}}]}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        return path

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = lanearchive.run(list(argv))
        return code, out.getvalue(), err.getvalue()

    def extract(self, transcript, state):
        return self.cli("extract", "--transcript", transcript, "--state", state,
                        "--out-dir", self.out)


class TestExtractLanes(_TmpDirCase):

    def test_every_dispatch_recovered_verbatim(self):
        t = self.write_transcript(self.records(), malformed=1)
        got = lanearchive.extract_lanes(t)
        self.assertEqual(got["dispatched"], 2)
        self.assertEqual(got["recovered"], 2)
        self.assertEqual(got["malformed"], 1)
        by_type = {l["subagent_type"]: l for l in got["lanes"]}
        bugs = by_type["vibe-check:bugs"]
        self.assertEqual(bugs["source_channel"], "task-result")
        self.assertEqual(bugs["raw_return_text"], "```json\n%s\n```" % json.dumps(BUGS_RETURN))
        self.assertEqual(bugs["parsed"], BUGS_RETURN)
        self.assertEqual(bugs["returns_seen"], 1)  # queued + user copy collapse
        sec = by_type["vibe-check:security"]
        self.assertEqual(sec["source_channel"], "handback")
        self.assertEqual(sec["tool_use_id"], "tu_sec")
        self.assertEqual(sec["parsed"], SEC_RETURN)

    def test_codex_line_is_its_own_lane(self):
        t = self.write_transcript(self.records())
        got = lanearchive.extract_lanes(t)
        codex = [l for l in got["lanes"] if l["source_channel"] == "codex-line"]
        self.assertEqual(len(codex), 1)
        self.assertEqual(codex[0]["subagent_type"], "codex-adversarial")
        self.assertEqual(codex[0]["raw_return_text"], json.dumps(CODEX_OBJ))
        self.assertEqual(got["codex_lines"], 1)

    def test_unreturned_dispatch_is_listed_unrecovered(self):
        recs = self.records() + [
            _assistant([_tool_use("tu_imp", "Agent", {"subagent_type": "vibe-check:impact"})])]
        got = lanearchive.extract_lanes(self.write_transcript(recs))
        self.assertEqual(got["dispatched"], 3)
        self.assertEqual(got["recovered"], 2)
        self.assertEqual(got["unrecovered"], [{"tool_use_id": "tu_imp",
                                               "subagent_type": "vibe-check:impact"}])

    def test_write_payload_is_not_recovered(self):
        got = lanearchive.extract_lanes(self.write_transcript(self.records()))
        self.assertNotIn("decoy.py", json.dumps(got))


class TestDecoyFilters(_TmpDirCase):
    """Each decoy filter is proven live: removing it recovers the decoy."""

    def _template_notification_records(self):
        # An impact dispatch whose real return never arrived, and a Read of a
        # template that shows a notification for it inside a tool_result.
        return self.records(extra=[
            _assistant([_tool_use("tu_imp", "Agent", {"subagent_type": "vibe-check:impact"})]),
            _assistant([_tool_use("tu_read", "Read", {"file_path": "/tpl.md"})]),
            _result("tu_read", "<example>\n%s\n</example>"
                    % _notification("tu_imp", "aimp", json.dumps(DECOY))),
        ])

    def test_template_notification_in_tool_result_is_not_a_return(self):
        got = lanearchive.extract_lanes(self.write_transcript(
            self._template_notification_records()))
        self.assertEqual([u["tool_use_id"] for u in got["unrecovered"]], ["tu_imp"])
        self.assertNotIn("decoy.py", json.dumps(got["lanes"]))

    def test_template_filter_mutation_recovers_the_decoy(self):
        t = self.write_transcript(self._template_notification_records())
        real = lanearchive._notification_strings
        try:
            lanearchive._notification_strings = lambda rec: list(replay._strings(rec))
            got = lanearchive.extract_lanes(t)
        finally:
            lanearchive._notification_strings = real
        self.assertIn("decoy.py", json.dumps(got["lanes"]))

    def _read_codex_records(self):
        return self.records(extra=[
            _assistant([_tool_use("tu_read2", "Read", {"file_path": "/agents/codex.md"})]),
            _result("tu_read2", json.dumps({"agent": "codex-adversarial",
                                            "findings": [{"file": "decoy.py", "line": 1}]})),
        ])

    def test_codex_object_in_non_bash_result_is_not_a_lane(self):
        got = lanearchive.extract_lanes(self.write_transcript(self._read_codex_records()))
        self.assertEqual(got["codex_lines"], 1)
        self.assertNotIn("decoy.py", json.dumps(got["lanes"]))

    def test_codex_tool_filter_mutation_recovers_the_decoy(self):
        t = self.write_transcript(self._read_codex_records())
        real = lanearchive.CODEX_LINE_TOOLS
        try:
            lanearchive.CODEX_LINE_TOOLS = ("Bash", "Read")
            got = lanearchive.extract_lanes(t)
        finally:
            lanearchive.CODEX_LINE_TOOLS = real
        self.assertEqual(got["codex_lines"], 2)
        self.assertIn("decoy.py", json.dumps(got["lanes"]))


class TestLocateAndContext(_TmpDirCase):

    def test_locates_printed_codex_dir(self):
        t = self.write_transcript(self.records())
        self.assertEqual(lanearchive.locate_codex_dir(t), os.path.realpath(self.codex_dir))

    def test_legacy_codex_out_gives_its_directory(self):
        recs = self.records(codex_dir_line=False) + [
            _assistant([_tool_use("tu_old", "Bash", {"command": "x"})]),
            _result("tu_old", "CODEX_OUT=%s/payload.json" % self.codex_dir)]
        t = self.write_transcript(recs)
        self.assertEqual(lanearchive.locate_codex_dir(t), os.path.realpath(self.codex_dir))

    def test_no_line_is_none(self):
        t = self.write_transcript(self.records(codex_dir_line=False))
        self.assertIsNone(lanearchive.locate_codex_dir(t))

    def test_path_outside_temp_root_is_refused(self):
        recs = self.records(codex_dir_line=False) + [
            _assistant([_tool_use("tu_bad", "Bash", {"command": "x"})]),
            _result("tu_bad", "CODEX_DIR=/etc/passwd")]
        t = self.write_transcript(recs)
        with self.assertRaises(ValueError):
            lanearchive.locate_codex_dir(t)
        state = self.write_state("joined")
        code, _out, err = self.extract(t, state)
        self.assertEqual(code, 2)
        self.assertEqual(err.strip(), "unreadable input: ValueError")
        self.assertEqual(os.listdir(self.out), [])

    def test_codex_dir_line_in_a_read_result_is_ignored(self):
        recs = self.records(codex_dir_line=False) + [
            _assistant([_tool_use("tu_r", "Read", {"file_path": "/k.md"})]),
            _result("tu_r", "CODEX_DIR=%s" % self.codex_dir)]
        self.assertIsNone(lanearchive.locate_codex_dir(self.write_transcript(recs)))

    def test_peak_context_is_main_session_max(self):
        t = self.write_transcript(self.records())
        # main: 1210, 3005, 4501; the sidechain 999999 is not the session's context.
        self.assertEqual(lanearchive.peak_context(t), 4501)

    def test_peak_context_zero_without_usage(self):
        t = self.write_transcript([_assistant([])])
        self.assertEqual(lanearchive.peak_context(t), 0)


class TestPrivacyScan(unittest.TestCase):

    def test_clean_and_allowed(self):
        self.assertEqual(lanearchive.privacy_scan("Co-Authored-By: x <noreply@anthropic.com>"), [])

    def test_each_class(self):
        cases = {
            "email": "contact leak.fixture@corp-mail.io",
            "nas-host": "run on maguffynas",
            "token": "key sk-ant-abc123",
            "private-instructions": "a NOPASSWD rule",
        }
        for cls, text in cases.items():
            with self.subTest(cls=cls):
                self.assertEqual(lanearchive.privacy_scan(text), [cls])
        for tok in ("ghp_abc", "github_pat_abc", "AKIAABCDEFGHIJKL", "Bearer abcdefghijklmnopq",
                    "sk-abcdefghijklmnop"):
            with self.subTest(tok=tok):
                self.assertEqual(lanearchive.privacy_scan(tok), ["token"])


class TestReservedEmailDomains(unittest.TestCase):

    CITED = ("password@example.com", "Pr0xyPass@radarr.example", "pass@radarr.internal",
             "pass@radarr.local", "pass@radarr.test")
    REFUSED = ("jane.doe@gmail.com", "x@corp-mail.io", "user@radarr.local.evil.com",
               "user@example.com.attacker.net")

    def test_reserved_domain_tokens_pass(self):
        for tok in self.CITED + ("u@Sub.EXAMPLE.org", "u@host.INVALID", "u@box.localhost"):
            with self.subTest(tok=tok):
                text = 'leaks "https://user:%s:7878/api" to the log' % tok
                self.assertEqual(lanearchive.privacy_scan(text), [])

    def test_routable_domain_tokens_refused_kind_only(self):
        for tok in self.REFUSED:
            with self.subTest(tok=tok):
                self.assertEqual(lanearchive.privacy_scan("see %s here" % tok), ["email"])

    def test_private_use_names_pass(self):
        for text in ("a config such as http://user:pass@radarr.lan is accepted",
                     "mail a@nas.home", "mail b@x.home.arpa", "mail c@y.corp",
                     "mail d@box.private", "mail e@wiki.intranet"):
            with self.subTest(text=text):
                self.assertEqual(lanearchive.privacy_scan(text), [])

    def test_private_use_name_only_as_final_label(self):
        for tok in ("x@radarr.lan.evil.com", "jane@gmail.com", "y@home.arpa.evil.com",
                    "z@corp.example-mail.io"):
            with self.subTest(tok=tok):
                self.assertEqual(lanearchive.privacy_scan("see %s here" % tok), ["email"])

    def test_reserved_domain_does_not_exempt_other_classes(self):
        self.assertEqual(lanearchive.privacy_scan("pass@maguffynas.local"), ["nas-host"])
        self.assertEqual(lanearchive.privacy_scan("sk-ant-abc@radarr.test"), ["token"])

    def test_scan_cli_refusal_prints_kind_only(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "report.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("ok pass@radarr.local\nbad jane.doe@gmail.com\n")
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                rc = lanearchive.run(["scan", path])
            self.assertEqual(rc, 1)
            self.assertEqual(err.getvalue().strip(), "privacy scan refused: email")
            self.assertNotIn("gmail", err.getvalue())


class TestExtractCli(_TmpDirCase):

    def test_joined_run_writes_payload_and_rc(self):
        t = self.write_transcript(self.records())
        code, _out, err = self.extract(t, self.write_state("joined"))
        self.assertEqual(code, 0, err)
        self.assertEqual(sorted(os.listdir(self.out)),
                         ["codex-payload.json", "codex-rc.txt", "context.txt", "lanes.json"])
        with open(os.path.join(self.out, "codex-rc.txt")) as fh:
            self.assertEqual(fh.read(), "0\n")
        with open(os.path.join(self.out, "context.txt")) as fh:
            self.assertEqual(fh.read(), "4501\n")
        with open(os.path.join(self.out, "lanes.json")) as fh:
            self.assertEqual(json.load(fh)["recovered"], 2)

    def test_skipped_run_without_dir_line_writes_absent(self):
        t = self.write_transcript(self.records(codex_dir_line=False))
        code, _out, err = self.extract(t, self.write_state("skipped", "timeout"))
        self.assertEqual(code, 0, err)
        self.assertEqual(sorted(os.listdir(self.out)),
                         ["codex-absent.txt", "context.txt", "lanes.json"])
        with open(os.path.join(self.out, "codex-absent.txt")) as fh:
            self.assertEqual(fh.read(), "codex.status=skipped reason=timeout\n")

    def test_off_run_writes_absent(self):
        t = self.write_transcript(self.records(codex_dir_line=False))
        code, _out, _err = self.extract(t, self.write_state("off"))
        self.assertEqual(code, 0)
        with open(os.path.join(self.out, "codex-absent.txt")) as fh:
            self.assertEqual(fh.read(), "codex.status=off reason=null\n")

    def test_joined_run_without_dir_line_is_extraction_failure(self):
        """A joined run whose CODEX_DIR line is gone never degrades to absent."""
        t = self.write_transcript(self.records(codex_dir_line=False))
        code, _out, err = self.extract(t, self.write_state("joined"))
        self.assertEqual(code, 1)
        self.assertEqual(err.strip(),
                         "codex extraction failed: joined run printed no CODEX_DIR line")
        self.assertEqual(os.listdir(self.out), [])

    def test_joined_cross_check_mutation(self):
        """Mutation proof: a disposition that ignores the state status (absent
        whenever no dir is printed) passes the joined-without-line fixture —
        so the joined-without-line test above is what the cross-check guards."""
        t = self.write_transcript(self.records(codex_dir_line=False))
        state = self.write_state("joined")
        real = lanearchive._codex_disposition
        try:
            def lenient(transcript, state_path):
                if lanearchive.locate_codex_dir(transcript) is None:
                    return "absent", "codex.status=joined reason=null\n", None
                return real(transcript, state_path)
            lanearchive._codex_disposition = lenient
            code, _out, _err = self.extract(t, state)
        finally:
            lanearchive._codex_disposition = real
        self.assertEqual(code, 0)
        self.assertIn("codex-absent.txt", os.listdir(self.out))

    def test_joined_run_with_missing_payload_fails(self):
        os.remove(os.path.join(self.codex_dir, "payload.json"))
        t = self.write_transcript(self.records())
        code, _out, err = self.extract(t, self.write_state("joined"))
        self.assertEqual(code, 1)
        self.assertEqual(err.strip(), "codex extraction failed: joined run has no payload.json")
        self.assertEqual(os.listdir(self.out), [])

    def test_joined_run_with_nonzero_rc_fails(self):
        with open(os.path.join(self.codex_dir, "rc"), "w") as fh:
            fh.write("124\n")
        t = self.write_transcript(self.records())
        code, _out, err = self.extract(t, self.write_state("joined"))
        self.assertEqual(code, 1)
        self.assertIn("rc is not 0", err)
        self.assertEqual(os.listdir(self.out), [])

    def test_unknown_status_fails(self):
        t = self.write_transcript(self.records())
        code, _out, err = self.extract(t, self.write_state("maybe"))
        self.assertEqual(code, 1)
        self.assertIn("unknown codex status", err)

    def test_existing_output_is_refused_and_preserved(self):
        with open(os.path.join(self.out, "lanes.json"), "w") as fh:
            fh.write("prior evidence\n")
        t = self.write_transcript(self.records())
        code, _out, err = self.extract(t, self.write_state("joined"))
        self.assertEqual(code, 1)
        self.assertIn("already written: lanes.json", err)
        with open(os.path.join(self.out, "lanes.json")) as fh:
            self.assertEqual(fh.read(), "prior evidence\n")

    def test_planted_private_tokens_refuse_and_leave_nothing(self):
        cases = {
            "email": "leak.fixture@corp-mail.io",
            "token": "sk-ant-abcdefghijklmnop",
            "nas-host": "maguffynas",
        }
        cases_extra = {"token-ghp": "ghp_abcdefghijklmnop"}
        for cls, planted in list(cases.items()) + list(cases_extra.items()):
            with self.subTest(cls=cls):
                for n in os.listdir(self.out):
                    os.remove(os.path.join(self.out, n))
                ret = dict(BUGS_RETURN, agent_notes=["saw %s here" % planted])
                t = self.write_transcript(self.records(bugs_return=ret))
                code, out, err = self.extract(t, self.write_state("joined"))
                self.assertEqual(code, 1)
                self.assertEqual(err.strip(), "privacy scan refused: %s" % cls.split("-ghp")[0])
                self.assertNotIn(planted, err + out)
                self.assertEqual(os.listdir(self.out), [])

    def test_private_token_in_codex_payload_refuses(self):
        with open(os.path.join(self.codex_dir, "payload.json"), "w") as fh:
            fh.write('{"note": "Bearer abcdefghijklmnopqrstu"}\n')
        t = self.write_transcript(self.records())
        code, _out, err = self.extract(t, self.write_state("joined"))
        self.assertEqual(code, 1)
        self.assertEqual(err.strip(), "privacy scan refused: token")
        self.assertEqual(os.listdir(self.out), [])

    def test_scan_cli_exit_codes(self):
        clean = os.path.join(self.tmp, "clean.txt")
        dirty = os.path.join(self.tmp, "dirty.txt")
        with open(clean, "w") as fh:
            fh.write("nothing here\n")
        with open(dirty, "w") as fh:
            fh.write("ssh nas then sudo\n")
        self.assertEqual(self.cli("scan", clean)[0], 0)
        code, _out, err = self.cli("scan", clean, dirty)
        self.assertEqual(code, 1)
        self.assertEqual(err.strip(), "privacy scan refused: nas-host")
        self.assertEqual(self.cli("scan", os.path.join(self.tmp, "missing.txt"))[0], 2)

    def test_usage_errors_exit_two(self):
        self.assertEqual(self.cli()[0], 2)
        self.assertEqual(self.cli("extract", "--transcript", "x")[0], 2)
        self.assertEqual(self.cli("--help")[0], 0)


class TestImportSet(unittest.TestCase):

    ALLOWED = {"argparse", "json", "os", "re", "shutil", "sys", "tempfile", "replay"}

    def test_imports_are_exactly_the_allowed_set(self):
        with open(LANEARCHIVE_PY, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    found.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        self.assertEqual(found, self.ALLOWED)

    def test_no_subprocess_or_exec(self):
        with open(LANEARCHIVE_PY, encoding="utf-8") as fh:
            text = fh.read()
        for token in ("subprocess", "exec(", "eval(", "importlib"):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
