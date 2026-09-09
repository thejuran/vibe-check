"""test_chunks.py — golden, purity and fail-closed tests for chunks.py.

Family 2 of the prose-to-code extraction: the path-tier risk rank, the two-key
risk sort, the greedy chunk packer, and the agents-per-chunk budget counts that
review.md Phase 0.2 / 0.3 previously stated only as prose.

The load-bearing property under test is CHUNK-01: path tier is the PRIMARY sort
key and churn is only a within-tier booster. That order inverted once already
(a high-churn README floating above a low-churn crypto file), so
TestTierOrderLocked pins it with an explicit high-churn-doc vs low-churn-crypto
pair rather than trusting the implementation to stay correct.
"""

import ast
import json
import os
import re
import subprocess
import sys
import unittest

# Make `import chunks` resolve when unittest discovery runs from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chunks  # noqa: E402  (sibling module under test)

CHUNKS_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chunks.py")

# GOLDEN packed output for the seven-file fixture below — an INDEPENDENTLY
# hard-coded literal. It was computed by hand-walking review.md's 0.2b greedy
# recipe (seed → same-directory fill → spill), NOT by calling chunks.pack(),
# which would make the freeze tautological. If a packer change moves a single
# file between chunks, this literal fails and the change has to be argued for.
GOLDEN_PACK = (
    '{"chunks":[{"bytes":49800,"files":['
    '{"bytes":6200,"lines":180,"path":"README.md"},'
    '{"bytes":12000,"lines":400,"path":"src/api/handler.py"},'
    '{"bytes":11000,"lines":350,"path":"src/api/router.py"},'
    '{"bytes":9000,"lines":300,"path":"src/auth/login.py"},'
    '{"bytes":8000,"lines":250,"path":"src/auth/session.py"},'
    '{"bytes":3600,"lines":120,"path":"src/util/helper.py"}],'
    '"lines":1600,"seed":"src/auth/session.py","tier":0},'
    '{"bytes":60000,"files":[{"bytes":60000,"lines":1900,'
    '"path":"src/util/big.js"}],"lines":1900,'
    '"seed":"src/util/big.js","tier":2}],'
    '"counts":{"chunk_total":2,"dispatch_max":30,"dispatch_min":6,'
    '"floor":3,"max":15}}'
)


# --------------------------------------------------------------------------- #
# Test fixtures / helpers
# --------------------------------------------------------------------------- #
def make_row(path, lines, bytes_, churn):
    """One `$REVIEW_SET` row as it arrives from the orchestrator's wc/git glue.

    Sizes and churn are DATA (keep-list D-08) — the module never measures them.
    """
    return {"path": path, "lines": lines, "bytes": bytes_, "churn": churn}


# The seven-file golden fixture: mixed tiers, three directories, and one file
# (src/util/big.js at 1900 lines) that exceeds the line budget on its own.
GOLDEN_ROWS = [
    make_row("src/auth/login.py", 300, 9000, 4),      # tier 0
    make_row("src/auth/session.py", 250, 8000, 11),   # tier 0
    make_row("src/api/handler.py", 400, 12000, 2),    # tier 1
    make_row("src/api/router.py", 350, 11000, 7),     # tier 1
    make_row("src/util/big.js", 1900, 60000, 1),      # tier 2, over line budget
    make_row("src/util/helper.py", 120, 3600, 3),     # tier 2
    make_row("README.md", 180, 6200, 99),             # tier 3, highest churn
]


def _paths(rows):
    return [r["path"] for r in rows]


# --------------------------------------------------------------------------- #
# CHUNK-01 — tier-first ordering is LOCKED
# --------------------------------------------------------------------------- #
class TestTierOrderLocked(unittest.TestCase):
    def test_high_churn_readme_sorts_after_low_churn_crypto(self):
        # The exact CHUNK-01 inversion: a README with far more commits than any
        # source file must still rank BELOW a barely-touched crypto file,
        # because tier is the primary key and churn only breaks within-tier ties.
        rows = [
            make_row("README.md", 180, 6200, 99),
            make_row("src/crypto/keys.py", 90, 3000, 1),
        ]
        ordered = _paths(chunks.risk_order(rows))
        self.assertEqual(ordered, ["src/crypto/keys.py", "README.md"])

    def test_tier_globs_match_anywhere_in_path(self):
        # Transcribed, not "fixed": review.md:270-282 uses unanchored `*auth*`
        # arms, so a docs path containing "auth" IS tier 0. Faithful transcription
        # is the contract; changing it is a behavior change, not a cleanup.
        self.assertEqual(chunks.tier_for("docs/auth-notes.md"), 0)

    def test_tier_assignments(self):
        cases = [
            ("src/auth/login.py", 0),
            ("app/secret_store.go", 0),
            (".env.production", 0),
            ("src/api/handler.py", 1),
            ("lib/validation.rb", 1),
            ("src/util/helper.py", 2),
            ("web/app.tsx", 2),
            ("README.md", 3),
            ("notes.txt", 3),
        ]
        for path, expected in cases:
            with self.subTest(path=path):
                self.assertEqual(chunks.tier_for(path), expected)

    def test_first_matching_arm_wins(self):
        # A path matching both a tier-0 and a tier-1 glob takes tier 0 — the
        # `case` semantics of the prose, where the first arm that matches wins.
        self.assertEqual(chunks.tier_for("src/api/auth.py"), 0)


# --------------------------------------------------------------------------- #
# The two-key sort
# --------------------------------------------------------------------------- #
class TestSortKey(unittest.TestCase):
    def test_equal_tier_orders_by_churn_desc(self):
        rows = [
            make_row("src/util/a.py", 10, 100, 1),
            make_row("src/util/b.py", 10, 100, 9),
            make_row("src/util/c.py", 10, 100, 5),
        ]
        self.assertEqual(
            _paths(chunks.risk_order(rows)),
            ["src/util/b.py", "src/util/c.py", "src/util/a.py"],
        )

    def test_equal_tier_and_churn_orders_by_path_asc(self):
        # The explicit path tie-break is NEW (bash `sort` without -s left ties
        # in byte order). No consumer depends on the old tie order; making it
        # explicit is what makes the golden reproducible.
        rows = [
            make_row("src/util/z.py", 10, 100, 4),
            make_row("src/util/a.py", 10, 100, 4),
            make_row("src/util/m.py", 10, 100, 4),
        ]
        self.assertEqual(
            _paths(chunks.risk_order(rows)),
            ["src/util/a.py", "src/util/m.py", "src/util/z.py"],
        )

    def test_risk_order_does_not_mutate_input(self):
        rows = list(GOLDEN_ROWS)
        before = _paths(rows)
        chunks.risk_order(rows)
        self.assertEqual(_paths(rows), before)


# --------------------------------------------------------------------------- #
# The greedy packer
# --------------------------------------------------------------------------- #
class TestPackGolden(unittest.TestCase):
    def test_pack_matches_golden_literal(self):
        result = chunks.run({
            "files": GOLDEN_ROWS,
            "mode": "review",
            "compliance": False,
        })
        actual = json.dumps(result, sort_keys=True, separators=(",", ":"))
        self.assertEqual(actual, GOLDEN_PACK)

    def test_golden_literal_is_not_computed_from_the_module(self):
        # Guard the guard: the golden must stay a literal. If a future edit
        # replaces it with a json.dumps(chunks...) call the freeze proves nothing.
        with open(os.path.abspath(__file__), "r", encoding="utf-8") as fh:
            src = fh.read()
        head = src.split("GOLDEN_ROWS", 1)[0]
        self.assertNotIn("chunks.", head)


class TestEdgeCaseA(unittest.TestCase):
    def test_single_file_over_byte_cap_is_its_own_chunk(self):
        # The giant ONE-LINE file: ~1 line so the line bound never fires, but
        # its bytes blow the cap, so the byte bound forces it alone (W3).
        rows = [
            make_row("dist/bundle.js", 1, 300000, 1),
            make_row("src/util/a.py", 10, 100, 1),
        ]
        packed = chunks.pack(chunks.risk_order(rows))
        big = [c for c in packed if c["seed"] == "dist/bundle.js"]
        self.assertEqual(len(big), 1)
        self.assertEqual(_paths(big[0]["files"]), ["dist/bundle.js"])

    def test_single_file_over_line_budget_is_its_own_chunk(self):
        rows = [
            make_row("src/util/big.py", 5000, 100, 1),
            make_row("src/util/a.py", 10, 100, 1),
        ]
        packed = chunks.pack(chunks.risk_order(rows))
        big = [c for c in packed if c["seed"] == "src/util/big.py"]
        self.assertEqual(len(big), 1)
        self.assertEqual(_paths(big[0]["files"]), ["src/util/big.py"])


class TestEdgeCaseB(unittest.TestCase):
    def test_empty_input_packs_to_nothing(self):
        self.assertEqual(chunks.pack([]), [])

    def test_empty_envelope_run(self):
        result = chunks.run({"files": [], "mode": "review", "compliance": False})
        self.assertEqual(result["chunks"], [])
        self.assertEqual(result["counts"]["chunk_total"], 0)
        self.assertEqual(result["counts"]["dispatch_min"], 0)
        self.assertEqual(result["counts"]["dispatch_max"], 0)


class TestSameDirFill(unittest.TestCase):
    def test_same_directory_neighbour_beats_a_riskier_other_dir_file(self):
        # Seed src/api/a.py (tier 1). src/auth/x.py is RISKIER (tier 0) but
        # lives elsewhere; the same-directory neighbour fills first so the
        # reviewing agent sees the module together (D-02).
        rows = [
            make_row("src/api/a.py", 100, 1000, 50),
            make_row("src/api/b.py", 100, 1000, 1),
            make_row("src/auth/x.py", 1700, 1000, 1),
        ]
        # Force the api file to seed by making it the only tier-1-or-better
        # entry ahead of auth: risk_order puts auth first, so pack the list
        # explicitly in the order we want to exercise.
        ordered = [rows[0], rows[1], rows[2]]
        packed = chunks.pack(ordered)
        self.assertEqual(
            _paths(packed[0]["files"]), ["src/api/a.py", "src/api/b.py"]
        )
        self.assertEqual(packed[0]["seed"], "src/api/a.py")

    def test_files_within_a_chunk_are_lexicographic(self):
        rows = [
            make_row("src/api/z.py", 10, 100, 9),
            make_row("src/api/a.py", 10, 100, 1),
            make_row("src/api/m.py", 10, 100, 5),
        ]
        packed = chunks.pack(chunks.risk_order(rows))
        self.assertEqual(
            _paths(packed[0]["files"]),
            ["src/api/a.py", "src/api/m.py", "src/api/z.py"],
        )

    def test_chunk_totals_are_sums_of_the_per_file_columns(self):
        packed = chunks.pack(chunks.risk_order(GOLDEN_ROWS))
        for i, chunk in enumerate(packed):
            with self.subTest(chunk=i):
                self.assertEqual(
                    chunk["lines"], sum(f["lines"] for f in chunk["files"])
                )
                self.assertEqual(
                    chunk["bytes"], sum(f["bytes"] for f in chunk["files"])
                )

    def test_every_input_file_lands_in_exactly_one_chunk(self):
        packed = chunks.pack(chunks.risk_order(GOLDEN_ROWS))
        placed = [f["path"] for c in packed for f in c["files"]]
        self.assertEqual(sorted(placed), sorted(_paths(GOLDEN_ROWS)))
        self.assertEqual(len(placed), len(set(placed)))


# --------------------------------------------------------------------------- #
# Budget counts (review.md:349-351)
# --------------------------------------------------------------------------- #
class TestBudgetCounts(unittest.TestCase):
    def test_floor_and_max_per_mode(self):
        cases = [
            ("review", False, 3, 15),
            ("review", True, 4, 16),
            ("deep", False, 6, 18),
            ("deep", True, 7, 19),
        ]
        for mode, compliance, floor, mx in cases:
            with self.subTest(mode=mode, compliance=compliance):
                counts = chunks.budget_counts(mode, compliance, 0)
                self.assertEqual(counts["floor"], floor)
                self.assertEqual(counts["max"], mx)

    def test_dispatch_ranges_are_chunk_total_times_floor_and_max(self):
        counts = chunks.budget_counts("review", False, 7)
        self.assertEqual(counts["chunk_total"], 7)
        self.assertEqual(counts["dispatch_min"], 21)
        self.assertEqual(counts["dispatch_max"], 105)

    def test_max_is_always_floor_plus_twelve(self):
        for mode in ("review", "deep"):
            for compliance in (False, True):
                with self.subTest(mode=mode, compliance=compliance):
                    counts = chunks.budget_counts(mode, compliance, 1)
                    self.assertEqual(counts["max"], counts["floor"] + 12)


class TestBudgetsFlag(unittest.TestCase):
    def test_budgets_flag_prints_the_single_source_of_truth(self):
        proc = subprocess.run(
            [sys.executable, CHUNKS_PY, "--budgets"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(
            proc.stdout.decode().strip(), "LINE_BUDGET=1800 BYTE_CAP=200000"
        )

    def test_constants_match_the_prose(self):
        self.assertEqual(chunks.LINE_BUDGET, 1800)
        self.assertEqual(chunks.BYTE_CAP, 200000)


# --------------------------------------------------------------------------- #
# Purity — the import set is EXACTLY {fnmatch, json, sys}
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    ALLOWED = {"fnmatch", "json", "sys"}
    FORBIDDEN_NAMES = {"subprocess", "os", "pathlib", "shutil", "glob",
                       "eval", "exec", "compile", "__import__", "open"}

    def _tree(self):
        with open(CHUNKS_PY, "r", encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_import_set_subset_of_allowed(self):
        imported = set()
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        self.assertTrue(
            imported.issubset(self.ALLOWED),
            "chunks.py imports outside {fnmatch,json,sys}: "
            + str(imported - self.ALLOWED),
        )

    def test_no_forbidden_module_imported(self):
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn(
                        alias.name.split(".")[0], self.FORBIDDEN_NAMES
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn(
                        node.module.split(".")[0], self.FORBIDDEN_NAMES
                    )

    def test_no_forbidden_calls_or_attributes(self):
        banned_call_names = {"eval", "exec", "compile", "__import__", "open"}
        banned_attr_roots = {"os", "subprocess", "pathlib", "shutil", "glob"}
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, banned_call_names,
                                 "forbidden call: " + node.func.id)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                self.assertNotIn(node.value.id, banned_attr_roots,
                                 "forbidden attribute access on: "
                                 + node.value.id)


# --------------------------------------------------------------------------- #
# MALFORMED-STDIN fail-closed
# --------------------------------------------------------------------------- #
class TestFailClosed(unittest.TestCase):
    def _run(self, payload):
        return subprocess.run(
            [sys.executable, CHUNKS_PY],
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

    def test_invalid_json_stdin_exits_nonzero(self):
        self.assertNotEqual(self._run(b"not json").returncode, 0)

    def test_empty_stdin_exits_nonzero(self):
        self.assertNotEqual(self._run(b"").returncode, 0)

    def test_valid_envelope_round_trips_through_stdin(self):
        payload = json.dumps({
            "files": GOLDEN_ROWS, "mode": "review", "compliance": False,
        }).encode()
        proc = self._run(payload)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        result = json.loads(proc.stdout.decode())
        self.assertEqual(
            json.dumps(result, sort_keys=True, separators=(",", ":")),
            GOLDEN_PACK,
        )

    def test_no_octal_escape_shorter_than_three_digits(self):
        # Mirrors the select_files guard (F9a): a `\0` or `\01` escape inside a
        # byte fixture silently collapses records. Nothing here needs one.
        with open(os.path.abspath(__file__), "r", encoding="utf-8") as fh:
            src = fh.read()
        self.assertIsNone(re.search(r"\\\\0(?![0-7]{2})", src))


if __name__ == "__main__":
    unittest.main()
