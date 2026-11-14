"""test_usage_fields.py — the usage-field reader, proven able to FAIL.

Every fixture here is synthetic and built in a temp directory; no real session
log is ever read or committed by these tests.

What these tests lock:

* Usage is summed once per message id. A message logged once per content block
  must not be counted once per block (the dedupe mutant doubles the sums).
* Lanes come only from a subagent's meta file. A subagent file without a
  readable meta file is reported as unattributed, never guessed into a lane
  (the lane mutant deletes a meta file and watches the lane move).
* Nothing but field names, counts, sums, model names and pattern-checked lane
  names leaves the logs (a sentinel placed in four positions never appears).
* Nothing is priced: `price_problems` rejects a dollar sign and any key or
  table heading naming cost, price or usd, and four planted mutants show it
  trips; a patched-off check is shown to miss them.
"""

import ast
import contextlib
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
sys.path.insert(0, HERE)
import usage_fields  # noqa: E402

USAGE_FIELDS_PY = os.path.join(HERE, "usage_fields.py")
SENTINEL = "SENTINEL-4be19d"
TOKEN_FIELDS = ("input_tokens", "output_tokens",
                "cache_creation_input_tokens", "cache_read_input_tokens")
_IDS = [0]


def _usage(i, o, cw=0, cr=0, **extra):
    u = {"input_tokens": i, "output_tokens": o,
         "cache_creation_input_tokens": cw, "cache_read_input_tokens": cr}
    u.update(extra)
    return u


class Builder:
    """Builds Claude Code session records: assistant messages logged once per
    content block (same message id, same usage), user tool results."""

    def __init__(self, start="2026-10-28T12:00:00.000Z"):
        self.records = []
        self.ts = start

    @staticmethod
    def _id(prefix):
        _IDS[0] += 1
        return "%s_%05d" % (prefix, _IDS[0])

    def message(self, usage, blocks=2, model="claude-opus-5-5", mid=None,
                ts=None, text="hello", tool_path=None, usage_per_block=None):
        mid = mid or self._id("msg")
        for n in range(blocks):
            u = usage_per_block[n] if usage_per_block else usage
            if n == 0 and tool_path is None:
                content = [{"type": "text", "text": text}]
            else:
                content = [{"type": "tool_use", "id": self._id("toolu"), "name": "Read",
                            "input": {"file_path": tool_path or "/fixture/a.py"}}]
            msg = {"id": mid, "role": "assistant", "content": content, "usage": dict(u)}
            if model is not None:
                msg["model"] = model
            self.records.append({"type": "assistant", "timestamp": ts or self.ts,
                                 "requestId": "req_" + mid, "cwd": "/fixture",
                                 "message": msg})
        return mid

    def tool_result(self, content, ts=None):
        self.records.append({"type": "user", "timestamp": ts or self.ts, "cwd": "/fixture",
                             "message": {"role": "user", "content": [
                                 {"type": "tool_result", "tool_use_id": "toolu_x",
                                  "content": content}]}})

    def raw(self, rec):
        self.records.append(rec)


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def session(self, builder, sid="sess-a", raw_lines=()):
        path = os.path.join(self.tmp, sid + ".jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for r in builder.records:
                fh.write(json.dumps(r) + "\n")
            for line in raw_lines:
                fh.write(line + "\n")
        return path

    def subagent(self, session_path, stem, builder, agent_type=None, meta_raw=None,
                 meta=True):
        base = session_path[:-len(".jsonl")]
        sub = os.path.join(base, "subagents")
        os.makedirs(sub, exist_ok=True)
        with open(os.path.join(sub, stem + ".jsonl"), "w", encoding="utf-8") as fh:
            for r in builder.records:
                fh.write(json.dumps(r) + "\n")
        meta_path = os.path.join(sub, stem + ".meta.json")
        if meta:
            with open(meta_path, "w", encoding="utf-8") as fh:
                if meta_raw is not None:
                    fh.write(meta_raw)
                else:
                    json.dump({"agentType": agent_type, "toolUseId": "toolu_p"}, fh)
        return meta_path

    def cli(self, *argv):
        return subprocess.run([sys.executable, "-I", USAGE_FIELDS_PY, *argv],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=60)

    def call_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = usage_fields.main(argv)
        return code, out.getvalue(), err.getvalue()


def three_messages_six_records():
    b = Builder()
    usages = [_usage(10, 100, 1000, 5000), _usage(20, 200, 2000, 6000),
              _usage(30, 300, 3000, 7000)]
    for u in usages:
        b.message(u, blocks=2)
    return b, usages


class TestDedupe(Case):
    def test_three_messages_six_records(self):
        b, usages = three_messages_six_records()
        s = usage_fields.summarise_session(self.session(b))
        self.assertEqual(s["records"], 6)
        self.assertEqual(s["unique_messages"], 3)
        self.assertEqual(s["duplicates_dropped"], 3)
        for f in TOKEN_FIELDS:
            self.assertEqual(s["tokens"][f], sum(u[f] for u in usages), f)

    def test_request_id_fallback(self):
        b = Builder()
        b.message(_usage(1, 2), blocks=2)
        for r in b.records:
            del r["message"]["id"]
        s = usage_fields.summarise_session(self.session(b))
        self.assertEqual(s["unique_messages"], 1)
        self.assertEqual(s["tokens"]["output_tokens"], 2)

    def test_duplicate_usage_conflicts(self):
        b, _ = three_messages_six_records()
        s = usage_fields.summarise_session(self.session(b))
        self.assertEqual(s["duplicate_usage_conflicts"], 0)
        b2 = Builder()
        b2.message(None, blocks=2, usage_per_block=[_usage(1, 5), _usage(1, 9)])
        s2 = usage_fields.summarise_session(self.session(b2, sid="sess-b"))
        self.assertEqual(s2["duplicate_usage_conflicts"], 1)


class TestFields(Case):
    def test_presence(self):
        b = Builder()
        b.message(_usage(1, 2, 3, 4), blocks=1)
        b.message(_usage(1, 2, 3, 4), blocks=1, model=None)
        b.message({"input_tokens": 1, "output_tokens": 2}, blocks=1)
        s = usage_fields.summarise_session(self.session(b))
        self.assertEqual(s["fields"]["model"], {"present": 2, "of": 3})
        self.assertEqual(s["fields"]["input_tokens"], {"present": 3, "of": 3})
        self.assertEqual(s["fields"]["cache_read_input_tokens"], {"present": 2, "of": 3})
        self.assertEqual(s["models"], ["claude-opus-5-5"])

    def test_usage_key_names_withhold_price_like(self):
        b = Builder()
        b.message(_usage(1, 2, service_tier="standard", cost_usd=1, priceEstimate=2),
                  blocks=1)
        s = usage_fields.summarise_session(self.session(b))
        self.assertEqual(s["usage_key_names"],
                         sorted(list(TOKEN_FIELDS) + ["service_tier"]))
        self.assertEqual(s["charge_like_keys_withheld"], 2)
        for n in s["usage_key_names"]:
            self.assertNotRegex(n.lower(), "cost|price|usd")

    def test_retry_key_names(self):
        b, _ = three_messages_six_records()
        s = usage_fields.summarise_session(self.session(b))
        self.assertEqual(s["retry_key_names"], [])
        b.raw({"type": "system", "timestamp": b.ts, "retryCount": 2})
        s2 = usage_fields.summarise_session(self.session(b, sid="sess-r"))
        self.assertEqual(s2["retry_key_names"], ["retryCount"])

    def test_wall_clock(self):
        b = Builder()
        b.message(_usage(1, 1), blocks=1, ts="2026-10-28T12:00:00.000Z")
        b.message(_usage(1, 1), blocks=1, ts="2026-10-28T12:01:30.500Z")
        s = usage_fields.summarise_session(self.session(b))
        self.assertAlmostEqual(s["wall_clock_seconds"], 90.5)
        self.assertEqual(s["wall_clock_label"],
                         "includes the owner's waiting time — not a performance measure")

    def test_wall_clock_crosses_midnight_and_offset(self):
        b = Builder()
        b.message(_usage(1, 1), blocks=1, ts="2026-12-31T23:59:00Z")
        b.message(_usage(1, 1), blocks=1, ts="2027-01-01T01:01:00+01:00")
        s = usage_fields.summarise_session(self.session(b))
        self.assertAlmostEqual(s["wall_clock_seconds"], 120.0)

    def test_malformed_lines_counted(self):
        b, _ = three_messages_six_records()
        s = usage_fields.summarise_session(self.session(b, raw_lines=("{not json", "[1,")))
        self.assertEqual(s["malformed_lines"], 2)
        self.assertEqual(s["records"], 6)

    def test_run_total_source(self):
        b, _ = three_messages_six_records()
        s = usage_fields.summarise_session(self.session(b))
        self.assertEqual(s["run_total_source"], "none found")
        b.raw({"type": "user", "timestamp": b.ts,
               "toolUseResult": {"totalTokens": 999, "status": "completed"}})
        s2 = usage_fields.summarise_session(self.session(b, sid="sess-t"))
        self.assertNotEqual(s2["run_total_source"], "none found")
        self.assertIn("totalTokens", s2["run_total_source"])


class TestLanes(Case):
    def _two_lanes(self):
        main = Builder()
        main.message(_usage(5, 50), blocks=2)
        path = self.session(main)
        sec = Builder()
        sec.message(_usage(100, 10, 7, 70), blocks=3)
        sec.message(_usage(200, 20, 8, 80), blocks=1)
        bugs = Builder()
        bugs.message(_usage(1000, 1, 9, 90), blocks=2)
        m1 = self.subagent(path, "agent-a1", sec, "vibe-check:security")
        m2 = self.subagent(path, "agent-b2", bugs, "vibe-check:bugs")
        return path, m1, m2

    def test_lanes_from_meta(self):
        path, _, _ = self._two_lanes()
        s = usage_fields.summarise_session(path)
        self.assertEqual(sorted(s["lanes"]), ["vibe-check:bugs", "vibe-check:security"])
        sec = s["lanes"]["vibe-check:security"]
        self.assertEqual(sec["unique_messages"], 2)
        self.assertEqual(sec["records"], 4)
        self.assertEqual(sec["tokens"]["input_tokens"], 300)
        self.assertEqual(sec["tokens"]["cache_read_input_tokens"], 150)
        self.assertEqual(s["lanes"]["vibe-check:bugs"]["tokens"]["input_tokens"], 1000)
        self.assertEqual(s["lanes_unattributed"]["files"], 0)
        # main alone at the top level; the run row is main plus every lane.
        self.assertEqual(s["tokens"]["input_tokens"], 5)
        self.assertEqual(s["run"]["tokens"]["input_tokens"], 1305)
        self.assertEqual(s["run"]["source"], "sum of parts")

    def test_lane_mutant_meta_removed(self):
        path, m1, _ = self._two_lanes()
        self.assertIn("vibe-check:security", usage_fields.summarise_session(path)["lanes"])
        os.remove(m1)
        self.assertFalse(os.path.exists(m1))
        s = usage_fields.summarise_session(path)
        self.assertNotIn("vibe-check:security", s["lanes"])
        self.assertEqual(s["lanes_unattributed"]["files"], 1)
        self.assertEqual(s["lanes_unattributed"]["tokens"]["input_tokens"], 300)

    def test_unreadable_meta_unattributed(self):
        main = Builder()
        main.message(_usage(1, 1))
        path = self.session(main)
        lane = Builder()
        lane.message(_usage(4, 4))
        self.subagent(path, "agent-x", lane, meta_raw="{broken")
        lane2 = Builder()
        lane2.message(_usage(6, 6))
        self.subagent(path, "agent-y", lane2, meta_raw=json.dumps({"agentType": 7}))
        s = usage_fields.summarise_session(path)
        self.assertEqual(s["lanes"], {})
        self.assertEqual(s["lanes_unattributed"]["files"], 2)
        self.assertEqual(s["lanes_unattributed"]["tokens"]["input_tokens"], 10)

    def test_unsafe_agent_type_is_other(self):
        main = Builder()
        main.message(_usage(1, 1))
        path = self.session(main)
        lane = Builder()
        lane.message(_usage(3, 3))
        self.subagent(path, "agent-z", lane, "bad lane/" + SENTINEL + " x")
        s = usage_fields.summarise_session(path)
        self.assertEqual(list(s["lanes"]), ["other"])
        self.assertNotIn(SENTINEL, json.dumps(s))


class TestCensus(Case):
    def test_census(self):
        def put(rel, records):
            p = os.path.join(self.tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as fh:
                for r in records:
                    fh.write(json.dumps(r) + "\n")
            return p
        put("a/transcript.jsonl", [{"type": "assistant",
                                    "message": {"id": "m", "usage": _usage(1, 1)}}])
        put("b/transcript.jsonl", [{"type": "assistant", "message": {"id": "m"}}])
        p = put("c/d/transcript.jsonl", [{"type": "user"}])
        os.makedirs(os.path.join(os.path.dirname(p), "subagents"))
        put("c/other.jsonl", [{"usage": {}}])
        self.assertEqual(usage_fields.census_archives(self.tmp),
                         {"files": 3, "with_usage": 1, "with_subagents": 1})


class TestNeverEcho(Case):
    def test_sentinel_never_printed(self):
        b = Builder()
        b.message(_usage(1, 2), blocks=1, text="secret " + SENTINEL)
        b.message(_usage(1, 2), blocks=1, tool_path="/%s/private/file.py" % SENTINEL)
        b.tool_result("result " + SENTINEL)
        b.raw({"type": "user", "timestamp": b.ts, "cwd": "/home/" + SENTINEL,
               "message": {"role": "user", "content": "hi"}})
        path = self.session(b, sid="sess-" + SENTINEL)
        found = 0
        for r in b.records:
            found += json.dumps(r).count(SENTINEL)
        self.assertEqual(found, 4, "fixture must hold the sentinel in four places")
        for extra in ((), ("--json",)):
            p = self.cli("--session", "s1=plain=" + path, *extra)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertNotIn(SENTINEL, p.stdout + p.stderr)
            self.assertIn("s1", p.stdout)


def all_fixture_outputs(case):
    """Printed and --json output of the reader on every fixture shape here."""
    b, _ = three_messages_six_records()
    p1 = case.session(b, sid="f1")
    main = Builder()
    main.message(_usage(5, 50))
    p2 = case.session(main, sid="f2")
    lane = Builder()
    lane.message(_usage(7, 70, cost_usd=3))
    case.subagent(p2, "agent-q", lane, "vibe-check:security")
    lane2 = Builder()
    lane2.message(_usage(1, 1))
    case.subagent(p2, "agent-r", lane2, meta=False)
    outs = []
    for extra in ((), ("--json",)):
        code, out, err = case.call_main(["--session", "a=plain=" + p1,
                                         "--session", "b=finalize=" + p2,
                                         "--archive-root", case.tmp, *extra])
        case.assertEqual(code, 0, err)
        outs.append(out)
    return outs


class TestNoPrice(Case):
    def test_reader_output_clean(self):
        text, js = all_fixture_outputs(self)
        self.assertEqual(usage_fields.price_problems(text), [])
        self.assertEqual(usage_fields.price_problems(js), [])
        json.loads(js)

    def test_mutant_dollar_on_table(self):
        text, _ = all_fixture_outputs(self)
        planted = text + "$5\n"
        self.assertIn("$5", planted)
        self.assertNotEqual(planted, text)
        self.assertTrue(usage_fields.price_problems(planted))

    def test_mutant_cost_usd_key(self):
        _, js = all_fixture_outputs(self)
        data = json.loads(js)
        data["cost_usd"] = 1
        planted = json.dumps(data, indent=2)
        self.assertIn('"cost_usd"', planted)
        self.assertNotEqual(planted, js)
        self.assertTrue(usage_fields.price_problems(planted))

    def test_mutant_price_estimate_key(self):
        _, js = all_fixture_outputs(self)
        data = json.loads(js)
        data["sessions"][0]["priceEstimate"] = 1
        planted = json.dumps(data, indent=2)
        self.assertIn('"priceEstimate"', planted)
        self.assertNotEqual(planted, js)
        self.assertTrue(usage_fields.price_problems(planted))

    def test_mutant_note_dollar_figure(self):
        clean = "# Cost visibility note\n\nA review used many tokens.\n"
        planted = clean + "That is about $12 a run.\n"
        self.assertIn("$12", planted)
        self.assertEqual(usage_fields.price_problems(clean), [])
        self.assertTrue(usage_fields.price_problems(planted))

    def test_title_and_phrase_do_not_trip(self):
        text = ("# Cost visibility note\n\n## Verdict\n\nThis is about cost visibility.\n\n"
                "| Field | Per run |\n|---|---|\n| model | measured, no price here |\n")
        self.assertEqual(usage_fields.price_problems(text), [])

    def test_table_heading_trips(self):
        for head in ("Cost", "unit PRICE", "USD"):
            text = "| Field | %s |\n|---|---|\n| model | 1 |\n" % head
            self.assertTrue(usage_fields.price_problems(text), head)

    def test_reader_refuses_to_print_a_price(self):
        b, _ = three_messages_six_records()
        p = self.session(b)
        real = usage_fields.render
        with mock.patch.object(usage_fields, "render", lambda s, a: real(s, a) + "$5\n"):
            code, out, err = self.call_main(["--session", "a=plain=" + p])
        self.assertEqual(code, 1)
        self.assertIn("OUTPUT HOLDS A PRICE — STOPPING", err)
        self.assertNotIn("$5", out)


class TestCheckNote(Case):
    def _note(self, text):
        p = os.path.join(self.tmp, "note.md")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def test_clean_and_planted(self):
        clean = "# Cost visibility note\n\n## Verdict\n\n**NO-GO**\n"
        self.assertEqual(self.cli("check-note", self._note(clean)).returncode, 0)
        p = self.cli("check-note", self._note(clean + "Usage cost: $5\n"))
        self.assertEqual(p.returncode, 1)
        self.assertIn("line 6", p.stdout + p.stderr)

    def test_private_paths_and_ids(self):
        for bad in ("see /Users/someone/x", "under ~/.claude/projects/x",
                    "id b1bb3036-026b-4ad4-9857-5d8c05e716b8"):
            p = self.cli("check-note", self._note("ok\n" + bad + "\n"))
            self.assertEqual(p.returncode, 1, bad)
        self.assertEqual(self.cli("check-note", self._note("id b1bb3036 only\n")).returncode, 0)

    def test_missing_file(self):
        self.assertEqual(self.cli("check-note", os.path.join(self.tmp, "nope.md")).returncode, 2)


class TestCli(Case):
    def test_missing_session_names_label_not_path(self):
        missing = os.path.join(self.tmp, "hidden-dir-" + SENTINEL, "x.jsonl")
        p = self.cli("--session", "smoke/abc=plain=" + missing)
        self.assertEqual(p.returncode, 2)
        self.assertIn("smoke/abc", p.stderr)
        self.assertNotIn(SENTINEL, p.stdout + p.stderr)

    def test_bad_session_argument(self):
        self.assertEqual(self.cli("--session", "no-equals").returncode, 2)

    def test_runs_isolated(self):
        b, _ = three_messages_six_records()
        p = self.cli("--session", "a=plain=" + self.session(b), "--json")
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data["sessions"][0]["label"], "a")
        self.assertEqual(data["sessions"][0]["summary"]["unique_messages"], 3)


class TestImportSet(unittest.TestCase):
    def test_module_level_imports(self):
        with open(USAGE_FIELDS_PY, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                names.add((node.module or "").split(".")[0])
        self.assertTrue(names <= {"argparse", "json", "os", "re", "sys"}, names)


class TestMutants(unittest.TestCase):
    def _passes(self, cls, name):
        result = unittest.TestResult()
        cls(name).run(result)
        return result.wasSuccessful()

    def test_mutant_dedupe_off(self):
        name = "test_three_messages_six_records"
        self.assertTrue(self._passes(TestDedupe, name))
        with mock.patch.object(usage_fields, "_unique_by_message",
                               lambda entries: (list(entries), 0)):
            self.assertFalse(self._passes(TestDedupe, name))
            tmp = tempfile.mkdtemp()
            self.addCleanup(shutil.rmtree, tmp, True)
            b, usages = three_messages_six_records()
            path = os.path.join(tmp, "s.jsonl")
            with open(path, "w", encoding="utf-8") as fh:
                for r in b.records:
                    fh.write(json.dumps(r) + "\n")
            s = usage_fields.summarise_session(path)
            self.assertEqual(s["tokens"]["output_tokens"],
                             2 * sum(u["output_tokens"] for u in usages))

    def test_mutant_price_check_off(self):
        names = ("test_mutant_dollar_on_table", "test_mutant_cost_usd_key",
                 "test_mutant_price_estimate_key", "test_mutant_note_dollar_figure",
                 "test_reader_refuses_to_print_a_price")
        for n in names:
            self.assertTrue(self._passes(TestNoPrice, n), n)
        with mock.patch.object(usage_fields, "price_problems", lambda text: []):
            for n in names:
                self.assertFalse(self._passes(TestNoPrice, n), n)

    def test_mutant_echo(self):
        name = "test_unsafe_agent_type_is_other"
        self.assertTrue(self._passes(TestLanes, name))
        with mock.patch.object(usage_fields, "_safe", lambda v, pattern: v):
            self.assertFalse(self._passes(TestLanes, name))


if __name__ == "__main__":
    unittest.main()
