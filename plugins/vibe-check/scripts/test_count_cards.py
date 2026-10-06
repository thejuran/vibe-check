"""Tests for count_cards.py — the REL-02 fix-loop card counter.

Every lock carries a demonstrated failure: the sidechain filter, the id dedupe,
the tool-name filter and the sha binding are each proven live by a mutant that
flips the outcome when the real code is patched away.
"""

import ast
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import count_cards  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
COUNT_CARDS_PY = os.path.join(HERE, "count_cards.py")


def ask(block_id, question="Pick one", sidechain=False, name="AskUserQuestion"):
    rec = {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": block_id, "name": name,
         "input": {"questions": [{"question": question}]}}]}}
    if sidechain:
        rec["isSidechain"] = True
    return rec


def answer(block_id, label="Abandon"):
    return {"type": "user", "toolUseResult": {"answers": {"q": label}},
            "message": {"content": [{"type": "tool_result", "tool_use_id": block_id,
                                     "content": "answered"}]}}


def write_lines(path, records, raw=()):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
        for line in raw:
            fh.write(line + "\n")
    return path


def seal(path):
    with open(path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    with open(path + ".sha256", "w") as fh:
        fh.write(digest + "  transcript.jsonl\n")


class _Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test-count-cards-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def p(self, *parts):
        return os.path.join(self.tmp, *parts)

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = count_cards.run(list(argv))
        return code, out.getvalue(), err.getvalue()

    def fixture(self, name, records, raw=()):
        return write_lines(self.p(name), records, raw)

    def run_dir(self, root, diff, n, records):
        path = write_lines(os.path.join(root, diff, "run-%d" % n, "transcript.jsonl"), records)
        seal(path)
        return path


class TestCount(_Case):

    def test_streamed_split_duplicate_id_counts_once(self):
        path = self.fixture("t.jsonl", [ask("toolu_1"), ask("toolu_1"), ask("toolu_2")])
        self.assertEqual(count_cards.count_cards(path), (2, 0))

    def test_sidechain_not_counted(self):
        path = self.fixture("t.jsonl", [ask("toolu_1"), ask("toolu_9", sidechain=True)])
        self.assertEqual(count_cards.count_cards(path), (1, 0))

    def test_other_tool_not_counted(self):
        path = self.fixture("t.jsonl", [ask("toolu_1"), ask("toolu_2", name="Bash")])
        self.assertEqual(count_cards.count_cards(path), (1, 0))

    def test_user_answer_record_not_counted(self):
        path = self.fixture("t.jsonl", [ask("toolu_1"), answer("toolu_1")])
        self.assertEqual(count_cards.count_cards(path), (1, 0))

    def test_malformed_line_counted_never_raised(self):
        path = self.fixture("t.jsonl", [ask("toolu_1")], raw=("{not json", "", "[1, 2]"))
        self.assertEqual(count_cards.count_cards(path), (1, 2))

    def test_non_assistant_record_with_tool_use_not_counted(self):
        rec = ask("toolu_5")
        rec["type"] = "user"
        path = self.fixture("t.jsonl", [ask("toolu_1"), rec])
        self.assertEqual(count_cards.count_cards(path), (1, 0))

    def test_cli_count_prints_two_lines(self):
        path = self.fixture("t.jsonl", [ask("toolu_1"), ask("toolu_2")], raw=("bad",))
        code, out, _e = self.cli("count", "--transcript", path)
        self.assertEqual(code, 0)
        self.assertEqual(out, "cards: 2\nmalformed: 1\n")

    def test_cli_count_unreadable_is_exit_2_class_name_only(self):
        code, out, err = self.cli("count", "--transcript", self.p("missing.jsonl"))
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("FileNotFoundError", err)
        self.assertNotIn(self.tmp, err)

    def test_usage_error_is_exit_2(self):
        self.assertEqual(self.cli()[0], 2)
        self.assertEqual(self.cli("count")[0], 2)

    def test_output_never_carries_transcript_text(self):
        path = self.fixture("t.jsonl", [ask("toolu_1", question="SECRET-CANARY"),
                                        answer("toolu_1", label="SECRET-CANARY")],
                            raw=("SECRET-CANARY not json",))
        code, out, err = self.cli("count", "--transcript", path)
        self.assertEqual(code, 0)
        self.assertNotIn("SECRET-CANARY", out + err)
        root = self.p("runs")
        self.run_dir(root, "d1", 1, [ask("toolu_1", question="SECRET-CANARY")])
        code, out, err = self.cli("tally", "--runs-root", root)
        self.assertEqual(code, 0, err)
        self.assertNotIn("SECRET-CANARY", out + err)


class TestTally(_Case):

    def build(self):
        root = self.p("runs")
        self.run_dir(root, "d1", 1, [ask("a"), ask("a"), ask("b")])   # 2 cards
        self.run_dir(root, "d1", 2, [])                                # 0 cards
        self.run_dir(root, "d2", 1, [ask("c"), ask("d", sidechain=True)])  # 1 card
        # Voided / failed siblings and stray files are ignored.
        write_lines(os.path.join(root, "d1", "run-3.voided-1790000000", "transcript.jsonl"),
                    [ask("x"), ask("y")])
        write_lines(os.path.join(root, "d1", "run-4", "transcript.jsonl"), [ask("z")])
        with open(os.path.join(root, "CATCH-VERDICTS.json"), "w") as fh:
            fh.write("{}\n")
        return root

    def test_tally_lines(self):
        code, out, err = self.cli("tally", "--runs-root", self.build())
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), [
            "d1 run-1 cards=2", "d1 run-2 cards=0", "d2 run-1 cards=1",
            "firings: 3", "fix-loop firings: 2", "cards: 3",
            "cards per fix-loop firing: 3/2 (1.50)", "cards per firing: 3/3 (1.00)",
            "malformed lines: 0"])

    def test_tally_no_fix_loop_firing(self):
        root = self.p("runs")
        self.run_dir(root, "d1", 1, [])
        code, out, _e = self.cli("tally", "--runs-root", root)
        self.assertEqual(code, 0)
        self.assertIn("cards per fix-loop firing: unavailable", out)

    def test_tally_missing_transcript_exit_1(self):
        root = self.build()
        os.remove(os.path.join(root, "d1", "run-2", "transcript.jsonl"))
        code, _o, err = self.cli("tally", "--runs-root", root)
        self.assertEqual(code, 1)
        self.assertIn("transcript missing or sha mismatch: d1/run-2", err)

    def test_tally_missing_sha_file_exit_1(self):
        root = self.build()
        os.remove(os.path.join(root, "d2", "run-1", "transcript.jsonl.sha256"))
        code, _o, err = self.cli("tally", "--runs-root", root)
        self.assertEqual(code, 1)
        self.assertIn("transcript missing or sha mismatch: d2/run-1", err)

    def tamper(self, root):
        path = os.path.join(root, "d1", "run-1", "transcript.jsonl")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ask("planted")) + "\n")

    def test_tally_tampered_transcript_exit_1(self):
        root = self.build()
        self.tamper(root)
        code, _o, err = self.cli("tally", "--runs-root", root)
        self.assertEqual(code, 1)
        self.assertIn("transcript missing or sha mismatch: d1/run-1", err)

    def test_tally_unreadable_root_exit_2(self):
        code, _o, err = self.cli("tally", "--runs-root", self.p("nope"))
        self.assertEqual(code, 2)
        self.assertNotIn(self.tmp, err)


class TestSingleRead(_Case):
    """The bytes that are hashed are the bytes that are counted: a transcript
    swapped between the sha check and the count can never be tallied."""

    def test_swap_between_hash_and_count_is_not_counted(self):
        root = self.p("runs")
        path = self.run_dir(root, "d1", 1, [ask("a")])           # sealed: 1 card
        swapped = write_lines(self.p("swapped.jsonl"), [ask("a"), ask("b")])  # 2 cards
        real_open = open
        opens = []

        def fake_open(file, *args, **kwargs):
            if os.path.realpath(str(file)) == os.path.realpath(path):
                opens.append(file)
                if len(opens) > 1:  # every read after the first sees the swap
                    return real_open(swapped, *args, **kwargs)
            return real_open(file, *args, **kwargs)
        with mock.patch.object(count_cards, "open", fake_open, create=True):
            code, out, err = self.cli("tally", "--runs-root", root)
        self.assertEqual(code, 0, err)
        self.assertIn("d1 run-1 cards=1", out.splitlines())
        self.assertEqual(len(opens), 1, "the transcript was read more than once")

    def test_swapped_bytes_fail_the_sha(self):
        root = self.p("runs")
        path = self.run_dir(root, "d1", 1, [ask("a")])
        swapped = write_lines(self.p("swapped.jsonl"), [ask("a"), ask("b")])
        real_open = open

        def fake_open(file, *args, **kwargs):
            if os.path.realpath(str(file)) == os.path.realpath(path):
                return real_open(swapped, *args, **kwargs)
            return real_open(file, *args, **kwargs)
        with mock.patch.object(count_cards, "open", fake_open, create=True):
            code, _o, err = self.cli("tally", "--runs-root", root)
        self.assertEqual(code, 1)
        self.assertIn("transcript missing or sha mismatch: d1/run-1", err)


class TestMutants(_Case):
    """Each mutant asserts the patched callable differs from the real one and
    that the outcome flips — so the real code's behaviour is proven live."""

    def test_mutant_sidechain_filter(self):
        path = self.fixture("t.jsonl", [ask("toolu_1"), ask("toolu_9", sidechain=True)])
        real = count_cards.count_cards(path)[0]
        always = lambda rec: True  # noqa: E731
        self.assertIsNot(always, count_cards._is_main)
        with mock.patch.object(count_cards, "_is_main", always):
            self.assertGreater(count_cards.count_cards(path)[0], real)

    def test_mutant_dedupe_key(self):
        path = self.fixture("t.jsonl", [ask("toolu_1"), ask("toolu_1")])
        self.assertEqual(count_cards.count_cards(path)[0], 1)
        counter = iter(range(10 ** 6))
        per_block = lambda block: next(counter)  # noqa: E731
        self.assertIsNot(per_block, count_cards._dedupe_key)
        with mock.patch.object(count_cards, "_dedupe_key", per_block):
            self.assertEqual(count_cards.count_cards(path)[0], 2)

    def test_mutant_card_tool_name(self):
        path = self.fixture("t.jsonl", [ask("toolu_1"), ask("toolu_2"),
                                        ask("toolu_3", name="Bash")])
        real = count_cards.count_cards(path)[0]
        self.assertNotEqual(count_cards.CARD_TOOL, "Bash")
        with mock.patch.object(count_cards, "CARD_TOOL", "Bash"):
            self.assertNotEqual(count_cards.count_cards(path)[0], real)

    def test_mutant_sha_check(self):
        root = self.p("runs")
        path = self.run_dir(root, "d1", 1, [ask("a")])
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ask("planted")) + "\n")
        self.assertEqual(self.cli("tally", "--runs-root", root)[0], 1)
        always_ok = lambda *a, **k: True  # noqa: E731
        self.assertIsNot(always_ok, count_cards._sha_ok)
        with mock.patch.object(count_cards, "_sha_ok", always_ok):
            self.assertEqual(self.cli("tally", "--runs-root", root)[0], 0)


class TestModuleShape(unittest.TestCase):

    def setUp(self):
        with open(COUNT_CARDS_PY, encoding="utf-8") as fh:
            self.src = fh.read()
        self.tree = ast.parse(self.src)

    def test_import_set_is_exact(self):
        names = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module)
        self.assertEqual(names, {"argparse", "hashlib", "json", "os", "re", "sys"})

    def test_docstring_states_the_method(self):
        doc = ast.get_docstring(self.tree)
        for needle in ("AskUserQuestion", "deduplicated by", "grep -c", "sha"):
            self.assertIn(needle, doc)


if __name__ == "__main__":
    unittest.main()
