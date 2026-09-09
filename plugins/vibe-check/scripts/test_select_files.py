"""test_select_files.py — parse, skip-rule and drift-lock tests for select_files.py.

Covers the two `--all` selection filters extracted from review.md Phase 0 mode 5:
the git-mode symlink filter (step c) and the skip-rules matcher (step d).

Two properties are load-bearing here:

* T-40-14 — a tracked symlink must never reach the `<files>` block, because
  reading one could follow a link outside the repo and disclose local files. The
  parse tests assert mode 120000 is dropped AND counted, and that a gitlink
  (160000) is dropped too rather than silently treated as a regular file.
* T-40-12 — the pattern table and templates/skip-rules.md must not drift apart.
  A stale copy silently under-reviews real source, which is the failure this
  tool exists to catch. TestSkipRulesDriftLock parses the template's bullet
  lists and asserts set equality with the code, so changing either side alone
  fails.

F9a (post-adversarial): the NUL separator is written `\\000` with THREE octal
digits. `\\0120000` reads as the single escape `\\012` (newline) plus a literal
`0000`, so a fixture written that way holds ONE record, not four, and would
pass while exercising none of the filtering. The fixture is therefore built by
joining explicit per-record byte strings, and its separator count is asserted
before use so a regression is caught rather than silently shrinking the fixture.
"""

import ast
import base64
import json
import os
import re
import subprocess
import sys
import unittest

# Make `import select_files` resolve when unittest discovery runs from the root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import select_files  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
SELECT_FILES_PY = os.path.join(HERE, "select_files.py")
SKIP_RULES_MD = os.path.join(
    os.path.dirname(HERE), "templates", "skip-rules.md"
)

NULL = b"\000"  # THREE octal digits — see the F9a note in the module docstring.
BLANK_SHA = b"0" * 40


def ls_files_record(mode, path):
    """One `git ls-files -s -z` record WITHOUT its trailing NUL separator.

    Real shape: `<mode> <sha> <stage>\\t<path>`.
    """
    return mode.encode() + b" " + BLANK_SHA + b" 0\t" + path.encode()


def ls_files_fixture(pairs):
    """NUL-DELIMITED `git ls-files -s -z` bytes built by explicit byte join.

    Deliberately NOT one long literal with embedded escapes: that is exactly
    how F9a collapsed four records into one. Joining per-record byte strings
    makes the separator count assertable by the caller.
    """
    records = [ls_files_record(mode, path) for mode, path in pairs]
    return NULL.join(records) + NULL


# --------------------------------------------------------------------------- #
# parse_ls_files — the mode filter (T-40-14)
# --------------------------------------------------------------------------- #
class TestParseLsFiles(unittest.TestCase):
    def _four_record_fixture(self):
        return ls_files_fixture([
            ("100644", "src/a.py"),
            ("120000", "link"),
            ("160000", "sub"),
            ("100755", "bin/run"),
        ])

    def test_fixture_really_holds_four_records(self):
        # F9a guard. If a future edit reintroduces a two-digit octal escape the
        # record count changes and this fails, instead of the fixture silently
        # shrinking to one record and making every test below vacuous.
        fixture = self._four_record_fixture()
        self.assertEqual(fixture.count(NULL), 4)

    def test_no_short_octal_escape_in_this_file(self):
        # The other half of the F9a guard: no `\0` or `\01` escape may appear
        # in a byte literal here. Only the three-digit `\000` form is allowed.
        with open(os.path.abspath(__file__), "r", encoding="utf-8") as fh:
            src = fh.read()
        # Strip the docstring's prose about the defect before scanning for it.
        body = src.split('"""', 2)[-1]
        self.assertIsNone(
            re.search(r"(?<!\\)\\0(?![0-7]{2})", body),
            "a short octal escape reintroduces F9a",
        )

    def test_only_regular_files_survive(self):
        result = select_files.parse_ls_files(self._four_record_fixture())
        self.assertEqual(result["regular"], ["src/a.py", "bin/run"])

    def test_symlink_is_dropped_and_counted(self):
        result = select_files.parse_ls_files(self._four_record_fixture())
        self.assertEqual(result["symlink_count"], 1)
        self.assertNotIn("link", result["regular"])

    def test_gitlink_is_dropped_and_counted_non_regular(self):
        result = select_files.parse_ls_files(self._four_record_fixture())
        self.assertEqual(result["non_regular_count"], 1)
        self.assertNotIn("sub", result["regular"])

    def test_empty_input(self):
        result = select_files.parse_ls_files(b"")
        self.assertEqual(result["regular"], [])
        self.assertEqual(result["symlink_count"], 0)
        self.assertEqual(result["non_regular_count"], 0)

    def test_path_containing_a_space_survives(self):
        # The tab before the path is the delimiter, which is why -z / -s is used
        # instead of parsing whitespace-separated columns.
        fixture = ls_files_fixture([("100644", "src/my file.py")])
        self.assertEqual(
            select_files.parse_ls_files(fixture)["regular"], ["src/my file.py"]
        )

    def test_unterminated_final_record_is_still_read(self):
        fixture = NULL.join([
            ls_files_record("100644", "src/a.py"),
            ls_files_record("100644", "src/b.py"),
        ])  # no trailing NUL
        self.assertEqual(
            select_files.parse_ls_files(fixture)["regular"],
            ["src/a.py", "src/b.py"],
        )


# --------------------------------------------------------------------------- #
# apply_skip_rules — the denylist groups and the allowlist override
# --------------------------------------------------------------------------- #
class TestApplySkipRules(unittest.TestCase):
    def test_denylisted_paths_are_dropped(self):
        cases = [
            "node_modules/x.js",     # vendored directory
            "dist/app.min.js",       # vendored dir + generated
            "yarn.lock",             # lockfile
            "img/logo.png",          # binary
            "docs/guide.md",         # docs segment
            "README.md",             # top-level README
            "src/.planning/p.md",    # nested .planning segment
        ]
        for path in cases:
            with self.subTest(path=path):
                kept, _ = select_files.apply_skip_rules([path])
                self.assertEqual(kept, [])

    def test_nested_readme_is_kept(self):
        # skip-rules.md is explicit: "top-level" means the repo root ONLY, so a
        # nested README is source-adjacent documentation and stays.
        kept, _ = select_files.apply_skip_rules(["src/api/README.md"])
        self.assertEqual(kept, ["src/api/README.md"])

    def test_allowlist_segment_wins_over_the_docs_denylist(self):
        # vibe-check's own agents/commands/templates/skills are instructional
        # .md that IS the program; a docs pattern must never drop them.
        kept, _ = select_files.apply_skip_rules(
            ["plugins/vibe-check/agents/bugs.md"]
        )
        self.assertEqual(kept, ["plugins/vibe-check/agents/bugs.md"])

    def test_plugin_docs_dir_is_still_dropped(self):
        kept, _ = select_files.apply_skip_rules(["plugins/vibe-check/docs/x.md"])
        self.assertEqual(kept, [])

    def test_all_four_allowlist_segments_win(self):
        for segment in select_files.ALLOWLIST_SEGMENTS:
            path = "plugins/vibe-check/%s/thing.md" % segment
            with self.subTest(segment=segment):
                kept, _ = select_files.apply_skip_rules([path])
                self.assertEqual(kept, [path])

    def test_ordinary_source_is_kept(self):
        paths = ["src/a.py", "lib/b.ts", "bin/run"]
        kept, skipped = select_files.apply_skip_rules(paths)
        self.assertEqual(kept, paths)
        self.assertEqual(skipped, 0)

    def test_skipped_count_is_the_difference(self):
        paths = ["src/a.py", "yarn.lock", "docs/guide.md", "lib/b.ts"]
        kept, skipped = select_files.apply_skip_rules(paths)
        self.assertEqual(kept, ["src/a.py", "lib/b.ts"])
        self.assertEqual(skipped, 2)

    def test_include_docs_drops_only_the_docs_group(self):
        paths = ["docs/guide.md", "README.md", "yarn.lock", "src/a.py"]
        kept, skipped = select_files.apply_skip_rules(paths, include_docs=True)
        self.assertEqual(kept, ["docs/guide.md", "README.md", "src/a.py"])
        self.assertEqual(skipped, 1)  # the lockfile still goes


# --------------------------------------------------------------------------- #
# T-40-12 — the code table and the template cannot drift apart
# --------------------------------------------------------------------------- #
class TestSkipRulesDriftLock(unittest.TestCase):
    """Parse templates/skip-rules.md and assert set equality with the code.

    Only the template's BULLET lines are parsed, never its prose — a wording
    change must not fail this test, but adding or removing a pattern must.
    """

    HEADINGS = {
        "### Vendored / dependency directories": "vendored",
        "### Generated / minified output": "generated",
        "### Lockfiles": "lockfiles",
        "### Binary / image / font / archive": "binary",
    }

    def _template_lines(self):
        with open(SKIP_RULES_MD, "r", encoding="utf-8") as fh:
            return fh.read().splitlines()

    def _parse_template_groups(self):
        """-> {group: {pattern, ...}} for the four backticked-bullet groups."""
        groups = {name: set() for name in self.HEADINGS.values()}
        current = None
        for line in self._template_lines():
            stripped = line.strip()
            if stripped.startswith("#"):
                current = self.HEADINGS.get(stripped)
                continue
            if current is None or not stripped.startswith("- "):
                continue
            match = re.match(r"^- `([^`]+)`", stripped)
            if match:
                groups[current].add(match.group(1))
        return groups

    def _parse_template_allowlist(self):
        """-> {segment, ...} from the allowlist override section's bullets."""
        segments = set()
        in_section = False
        for line in self._template_lines():
            stripped = line.strip()
            if stripped.startswith("## "):
                in_section = stripped.startswith("## Keep these")
                continue
            if not in_section or not stripped.startswith("- "):
                continue
            match = re.search(r"`/([A-Za-z0-9_.-]+)/`", stripped)
            if match:
                segments.add(match.group(1))
        return segments

    def test_template_parse_is_not_vacuous(self):
        # If the heading text changes and the parser silently matches nothing,
        # every set-equality assertion below would trivially pass. Pin non-empty.
        groups = self._parse_template_groups()
        for name, patterns in groups.items():
            with self.subTest(group=name):
                self.assertTrue(patterns, "no bullets parsed for " + name)
        self.assertTrue(self._parse_template_allowlist())

    def test_denylist_groups_match_the_template(self):
        template = self._parse_template_groups()
        for name, patterns in template.items():
            with self.subTest(group=name):
                self.assertEqual(
                    set(select_files.SKIP_GROUPS[name]),
                    patterns,
                    "SKIP_GROUPS[%r] and templates/skip-rules.md disagree" % name,
                )

    def test_allowlist_segments_match_the_template(self):
        self.assertEqual(
            set(select_files.ALLOWLIST_SEGMENTS),
            self._parse_template_allowlist(),
        )

    def test_docs_group_rules_match_the_template(self):
        # The docs group is stated as prose bullets rather than backticked
        # patterns, so it is pinned by its three directory segments and the two
        # top-level stems rather than by bullet scraping.
        self.assertEqual(
            set(select_files.SKIP_GROUPS["docs_segments"]),
            {".planning", "docs", "specs"},
        )
        self.assertEqual(
            set(select_files.SKIP_GROUPS["docs_toplevel"]),
            {"README*", "CHANGELOG*"},
        )
        text = "\n".join(self._template_lines())
        for segment in (".planning/", "docs/", "specs/"):
            with self.subTest(segment=segment):
                self.assertIn(segment, text)
        for stem in ("README*", "CHANGELOG*"):
            with self.subTest(stem=stem):
                self.assertIn(stem, text)

    def test_five_denylist_groups_exist(self):
        # skip-rules.md states there are five denylist groups; docs is split
        # into its segment and top-level halves, hence six keys.
        self.assertEqual(
            set(select_files.SKIP_GROUPS),
            {"vendored", "generated", "lockfiles", "binary",
             "docs_segments", "docs_toplevel"},
        )


# --------------------------------------------------------------------------- #
# run(envelope) and the CLI
# --------------------------------------------------------------------------- #
class TestRunEnvelope(unittest.TestCase):
    def _envelope(self, pairs, include_docs=False):
        raw = ls_files_fixture(pairs)
        return {
            "ls_files_z": base64.b64encode(raw).decode(),
            "include_docs": include_docs,
        }

    def test_end_to_end_counts(self):
        result = select_files.run(self._envelope([
            ("100644", "src/a.py"),
            ("120000", "link"),
            ("160000", "sub"),
            ("100644", "yarn.lock"),
            ("100644", "docs/guide.md"),
        ]))
        self.assertEqual(result["review_set"], ["src/a.py"])
        self.assertEqual(result["symlink_count"], 1)
        self.assertEqual(result["non_regular_count"], 1)
        self.assertEqual(result["skipped_count"], 2)

    def test_review_set_is_sorted(self):
        result = select_files.run(self._envelope([
            ("100644", "src/z.py"),
            ("100644", "src/a.py"),
            ("100644", "src/m.py"),
        ]))
        self.assertEqual(
            result["review_set"], ["src/a.py", "src/m.py", "src/z.py"]
        )

    def test_include_docs_flows_through(self):
        result = select_files.run(self._envelope(
            [("100644", "docs/guide.md")], include_docs=True
        ))
        self.assertEqual(result["review_set"], ["docs/guide.md"])


class TestCLI(unittest.TestCase):
    def _run(self, args, payload):
        return subprocess.run(
            [sys.executable, SELECT_FILES_PY] + args,
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

    def test_raw_mode_reads_nul_delimited_stdin(self):
        raw = ls_files_fixture([
            ("100644", "src/a.py"),
            ("120000", "link"),
        ])
        self.assertEqual(raw.count(NULL), 2)  # F9a guard on this fixture too
        proc = self._run(["--raw"], raw)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        result = json.loads(proc.stdout.decode())
        self.assertEqual(result["review_set"], ["src/a.py"])
        self.assertEqual(result["symlink_count"], 1)

    def test_raw_include_docs_is_honored(self):
        raw = ls_files_fixture([("100644", "docs/guide.md")])
        proc = self._run(["--raw", "--include-docs"], raw)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(
            json.loads(proc.stdout.decode())["review_set"], ["docs/guide.md"]
        )

    def test_json_envelope_mode(self):
        raw = ls_files_fixture([("100644", "src/a.py")])
        payload = json.dumps({
            "ls_files_z": base64.b64encode(raw).decode(),
            "include_docs": False,
        }).encode()
        proc = self._run([], payload)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(
            json.loads(proc.stdout.decode())["review_set"], ["src/a.py"]
        )

    def test_invalid_json_envelope_exits_nonzero(self):
        self.assertNotEqual(self._run([], b"x").returncode, 0)

    def test_empty_stdin_envelope_exits_nonzero(self):
        self.assertNotEqual(self._run([], b"").returncode, 0)


# --------------------------------------------------------------------------- #
# Purity — the import set is EXACTLY {base64, fnmatch, json, sys}
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    ALLOWED = {"base64", "fnmatch", "json", "sys"}
    FORBIDDEN_NAMES = {"subprocess", "os", "pathlib", "shutil", "glob",
                       "eval", "exec", "compile", "__import__", "open"}

    def _tree(self):
        with open(SELECT_FILES_PY, "r", encoding="utf-8") as fh:
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
            "select_files.py imports outside the allowed set: "
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


if __name__ == "__main__":
    unittest.main()
