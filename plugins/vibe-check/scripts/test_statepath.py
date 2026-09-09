"""test_statepath.py — the ONE `.turingmind/state/` filename rule, per mode.

The HARD CONTRACT at `review.md:12` states the governing rule and Phase 0.5
(`:405-428`) states the per-mode derivations. Phase 4.5 and Finalize both
consume the result, and `review.md:405` is explicit that "Finalize must NOT
re-derive a path" — which is precisely the drift this module removes: before it,
the rule was prose restated at `:12`, `:30`, `:406`, `:409` and `:1096`.

Fix-list FL-05 (finding R9) is the reason the signature looks the way it does.
The plan proposed `resolve(mode, phase_id, scope_label)`, which cannot reproduce
a single existing key: the default modes need the repo basename and the branch
slug, and `--all` needs a SHA-1 over `repo:branch:scope`. So `resolve` takes a
context carrying all of it and OWNS the hashing.

FL-05 also requires reproducing real existing keys byte-for-byte. Three were
harvested from the sealed run tree — `RUN-CHECKLIST-v2.10.md` records
`triggarr-.json`, `roonseek-.json` and `seedsyncarr-.json`, each with an EMPTY
branch slug because the harness pins every clone to a base SHA with
`git switch --detach` (`RUN-CHECKLIST-v2.10.md:288`), so `git branch
--show-current` returns empty. Those keys are the golden: a helper that cannot
reproduce them would silently orphan live state.

The "never abbreviate" rule (`review.md:406`) is ENFORCED here, not merely
documented. `:408` names `02.json` and `31.json` as the wrong forms, and the
prose spells out the cost: "a second invocation looking for
`02-real-data-path.json` won't find a state written as `02.json`, and
carry-forward silently restarts from pass 1."
"""

import ast
import hashlib
import json
import os
import subprocess
import sys
import unittest

# Make `import statepath` resolve when unittest discovery runs from the root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import statepath  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
STATEPATH_PY = os.path.join(HERE, "statepath.py")


class TestRealHarvestedKeys(unittest.TestCase):
    """FL-05 / R9 — reproduce real existing state-file keys byte-for-byte.

    Harvested from `docs/design/b3-ground-truth/RUN-CHECKLIST-v2.10.md`. Each
    was produced by a real run against a detached checkout, so the branch slug
    is empty and the key ends `<repo>-.json`. That trailing dash is not a typo:
    it is what the recorded derivation actually emits, and a "tidier" helper
    that dropped it would fail to find state written by every sealed run.
    """

    HARVESTED = (
        ("triggarr", ".turingmind/state/triggarr-.json"),
        ("roonseek", ".turingmind/state/roonseek-.json"),
        ("seedsyncarr", ".turingmind/state/seedsyncarr-.json"),
    )

    def test_reproduces_each_harvested_key(self):
        for repo, expected in self.HARVESTED:
            with self.subTest(repo=repo):
                path, reason = statepath.resolve(
                    "default", repo=repo, branch="")
                self.assertEqual(path, expected)
                self.assertEqual(reason, statepath.REASON_OK)

    def test_the_harvested_fixture_is_what_we_think_it_is(self):
        """Fixture integrity: these must be EMPTY-slug keys with a trailing
        dash, or they are not exercising the detached-HEAD case at all."""
        self.assertEqual(len(self.HARVESTED), 3)
        for repo, expected in self.HARVESTED:
            self.assertTrue(expected.endswith(repo + "-.json"), expected)
            self.assertNotIn("/", expected[len(".turingmind/state/"):])


class TestDefaultModes(unittest.TestCase):
    """review.md:409 — `.turingmind/state/<repo>-<branch-slug>.json`."""

    def test_the_three_default_modes_share_one_derivation(self):
        """":409 — Other modes (no args / PR / range)". One rule, not three."""
        paths = set()
        for mode in ("default", "pr", "range"):
            with self.subTest(mode=mode):
                path, reason = statepath.resolve(
                    mode, repo="myrepo", branch="main")
                self.assertEqual(reason, statepath.REASON_OK)
                paths.add(path)
        self.assertEqual(paths, {".turingmind/state/myrepo-main.json"})

    def test_branch_slug_replaces_every_slash(self):
        """:409 — "the current branch with every `/` replaced by `-`". The slug
        step is MANDATORY; a raw name would produce a SLASHED path that ENOENTs
        on write."""
        path, _ = statepath.resolve("default", repo="r", branch="feat/v2.9")
        self.assertEqual(path, ".turingmind/state/r-feat-v2.9.json")

    def test_multi_segment_branch_is_fully_slugged(self):
        path, _ = statepath.resolve(
            "default", repo="r", branch="release/1.2/hotfix")
        self.assertEqual(path, ".turingmind/state/r-release-1.2-hotfix.json")
        self.assertNotIn("/", path[len(".turingmind/state/"):])

    def test_result_is_a_flat_filename_under_state(self):
        for branch in ("main", "feat/x", "a/b/c/d", ""):
            with self.subTest(branch=branch):
                path, _ = statepath.resolve("default", repo="r", branch=branch)
                tail = path[len(statepath.STATE_DIR) + 1:]
                self.assertNotIn("/", tail)

    def test_missing_repo_refuses(self):
        path, reason = statepath.resolve("default", repo=None, branch="main")
        self.assertIsNone(path)
        self.assertIn(reason, statepath.REASONS)

    def test_branch_is_required_but_may_be_empty(self):
        """Empty is a real value (detached HEAD); absent is a caller bug."""
        self.assertIsNotNone(
            statepath.resolve("default", repo="r", branch="")[0])
        self.assertIsNone(
            statepath.resolve("default", repo="r", branch=None)[0])


class TestGsdMode(unittest.TestCase):
    """review.md:406 — `.turingmind/state/<$PHASE_ID>.json`, full name."""

    def test_full_phase_directory_name_resolves(self):
        path, reason = statepath.resolve("gsd", phase_id="02-real-data-path")
        self.assertEqual(path, ".turingmind/state/02-real-data-path.json")
        self.assertEqual(reason, statepath.REASON_OK)

    def test_the_prose_worked_examples_resolve(self):
        """:407 — the two ✓ Correct examples, transcribed."""
        for phase_id, expected in (
            ("02-real-data-path", ".turingmind/state/02-real-data-path.json"),
            ("31-cache-invalidation-renderer-config-epoch-and-awaited-purge-a",
             ".turingmind/state/31-cache-invalidation-renderer-config-epoch-"
             "and-awaited-purge-a.json"),
        ):
            with self.subTest(phase_id=phase_id):
                self.assertEqual(
                    statepath.resolve("gsd", phase_id=phase_id)[0], expected)

    def test_abbreviated_phase_id_is_refused(self):
        """The HARD CONTRACT (:12) says never abbreviate; :408 names `02.json`
        and `31.json` as the WRONG forms.

        Before this module that rule was prose restated in two phases and could
        drift. Abbreviating means a second invocation looking for
        `02-real-data-path.json` won't find state written as `02.json`, and
        carry-forward silently restarts from pass 1 (:406).
        """
        for abbreviated in ("02", "31", "7", "40"):
            with self.subTest(phase_id=abbreviated):
                path, reason = statepath.resolve("gsd", phase_id=abbreviated)
                self.assertIsNone(path, "an abbreviated phase id must refuse")
                self.assertEqual(reason, statepath.REASON_ABBREVIATED)

    def test_bare_prefix_with_trailing_dash_is_refused(self):
        """`02-` is a prefix that has a separator but no name."""
        self.assertIsNone(statepath.resolve("gsd", phase_id="02-")[0])

    def test_missing_phase_id_refuses(self):
        path, reason = statepath.resolve("gsd", phase_id=None)
        self.assertIsNone(path)
        self.assertIn(reason, statepath.REASONS)


class TestAllMode(unittest.TestCase):
    """review.md:418-425 — `by-mode/all/<scope-hash>.json`, 12-hex SHA-1."""

    def test_whole_tree_key_matches_the_bash_derivation(self):
        """:423 — `printf '%s' "repo:branch:scope" | shasum | cut -c1-12`.

        Recomputed here with hashlib.sha1 independently of the module. `shasum`
        with no algorithm flag is SHA-1, which is what makes these agree.
        """
        expected_hash = hashlib.sha1(
            b"triggarr:main:whole-tree").hexdigest()[:12]
        path, reason = statepath.resolve(
            "all", repo="triggarr", branch="main", narrow="")
        self.assertEqual(
            path, ".turingmind/state/by-mode/all/%s.json" % expected_hash)
        self.assertEqual(reason, statepath.REASON_OK)

    def test_scope_token_is_the_literal_whole_tree_only_when_narrow_empty(self):
        """:422 — "the literal token 'whole-tree' ONLY when $NARROW is empty"."""
        narrowed = hashlib.sha1(b"r:main:src/api").hexdigest()[:12]
        path, _ = statepath.resolve("all", repo="r", branch="main",
                                    narrow="src/api")
        self.assertEqual(
            path, ".turingmind/state/by-mode/all/%s.json" % narrowed)

    def test_hash_includes_repo_and_branch_so_repos_never_collide(self):
        """:428 — "a whole-tree `--all` in repo A and in repo B yield DIFFERENT
        keys even in a shared `.turingmind/`"."""
        a, _ = statepath.resolve("all", repo="alpha", branch="main", narrow="")
        b, _ = statepath.resolve("all", repo="beta", branch="main", narrow="")
        self.assertNotEqual(a, b)
        c, _ = statepath.resolve("all", repo="alpha", branch="dev", narrow="")
        self.assertNotEqual(a, c)

    def test_key_is_always_twelve_hex(self):
        """:424 — "always by-mode/all/<12hex>.json"; never a bare
        'whole-tree' filename."""
        path, _ = statepath.resolve("all", repo="r", branch="b", narrow="")
        stem = path.split("/")[-1][: -len(".json")]
        self.assertEqual(len(stem), 12)
        self.assertTrue(all(c in "0123456789abcdef" for c in stem), stem)
        self.assertNotIn("whole-tree", path)

    def test_all_mode_never_needs_a_branch_slug(self):
        """:414 — "The `--all` branch below needs NO slug: its `$BRANCH` feeds
        `shasum`, and a 12-hex digest never carries a slash."

        So a slashed branch must hash RAW — slugging it first would produce a
        different key than the recorded bash.
        """
        raw = hashlib.sha1(b"r:feat/x:whole-tree").hexdigest()[:12]
        path, _ = statepath.resolve("all", repo="r", branch="feat/x", narrow="")
        self.assertEqual(
            path, ".turingmind/state/by-mode/all/%s.json" % raw)


class TestNamespaceDisjointness(unittest.TestCase):
    """review.md:428 — the reserved-path guard, as a structural property.

    ":418 — a repo named `all` on branch `whole-tree` produces the default key
    `all-whole-tree.json`, byte-identical to a whole-tree `--all` key" under the
    OLD flat grammar. The subdirectory is what makes that impossible.
    """

    def test_default_never_resolves_into_by_mode(self):
        for repo, branch in (("by", "mode-all-abc"), ("all", "whole-tree"),
                             ("by-mode", "all")):
            with self.subTest(repo=repo, branch=branch):
                path, _ = statepath.resolve("default", repo=repo, branch=branch)
                self.assertIsNotNone(path)
                self.assertNotIn("by-mode/", path)

    def test_all_never_resolves_to_a_flat_key(self):
        path, _ = statepath.resolve("all", repo="r", branch="b", narrow="")
        self.assertTrue(path.startswith(".turingmind/state/by-mode/all/"))

    def test_the_collision_counter_example_no_longer_collides(self):
        """The exact :418 counter-example, executed."""
        flat, _ = statepath.resolve("default", repo="all", branch="whole-tree")
        scoped, _ = statepath.resolve("all", repo="all", branch="whole-tree",
                                      narrow="")
        self.assertNotEqual(flat, scoped)


class TestPhase45AndFinalizeAgree(unittest.TestCase):
    """review.md:405 — ONE canonical handle; ":30" Finalize never re-derives.

    Asserting agreement by construction is the point: the two call sites used
    to be two prose restatements that could drift apart.
    """

    def test_same_context_yields_same_path_for_every_mode(self):
        contexts = (
            ("gsd", {"phase_id": "40-prose-diet-restructure-for-opus-5"}),
            ("default", {"repo": "triggarr", "branch": ""}),
            ("pr", {"repo": "r", "branch": "feat/x"}),
            ("range", {"repo": "r", "branch": "main"}),
            ("all", {"repo": "r", "branch": "main", "narrow": ""}),
        )
        for mode, kwargs in contexts:
            with self.subTest(mode=mode):
                persist = statepath.resolve(mode, **kwargs)
                finalize = statepath.resolve(mode, **kwargs)
                self.assertEqual(persist, finalize)
                self.assertIsNotNone(persist[0])


class TestUnsafeComponentsRefused(unittest.TestCase):
    """T-40-41 — a phase id (or repo/branch) becomes a FILENAME component."""

    UNSAFE = ("a/b", "..", "../escape", "a\x00b", "-leading-dash",
              "a\nb", ".", "")

    def test_unsafe_phase_id_refused(self):
        for bad in self.UNSAFE:
            with self.subTest(phase_id=bad):
                path, reason = statepath.resolve("gsd", phase_id=bad)
                self.assertIsNone(path)
                self.assertIn(reason, statepath.REASONS)

    def test_unsafe_repo_refused(self):
        for bad in ("a/b", "..", "a\x00b", ""):
            with self.subTest(repo=bad):
                self.assertIsNone(
                    statepath.resolve("default", repo=bad, branch="main")[0])

    def test_branch_traversal_refused_even_after_slugging(self):
        """`..` survives slugging (no slash to replace), so it must be caught
        on its own."""
        self.assertIsNone(
            statepath.resolve("default", repo="r", branch="..")[0])

    def test_reasons_never_echo_the_offending_value(self):
        """The value can originate from a directory name in the REVIEWED repo.

        A reason that echoed it would put attacker-influenced text into an
        operator-facing message.
        """
        secret = "40-SENTINELVALUE-not-a-real-phase/../etc"
        _, reason = statepath.resolve("gsd", phase_id=secret)
        self.assertNotIn("SENTINEL", reason)
        for fragment in ("etc", ".."):
            self.assertNotIn(fragment, reason)

    def test_the_echo_guard_is_not_vacuous(self):
        """Prove the sentinel would be detected if a reason DID echo it."""
        self.assertIn("SENTINEL", "phase id 40-SENTINELVALUE is invalid")

    def test_every_reason_is_from_the_fixed_tuple(self):
        cases = (
            ("gsd", {"phase_id": "02"}),
            ("gsd", {"phase_id": "a/b"}),
            ("gsd", {"phase_id": None}),
            ("default", {"repo": None, "branch": "m"}),
            ("bogus", {}),
        )
        for mode, kwargs in cases:
            with self.subTest(mode=mode, kwargs=kwargs):
                _, reason = statepath.resolve(mode, **kwargs)
                self.assertIn(reason, statepath.REASONS)


class TestFailClosed(unittest.TestCase):
    def test_unknown_mode_refuses(self):
        path, reason = statepath.resolve("teleport", repo="r", branch="m")
        self.assertIsNone(path)
        self.assertEqual(reason, statepath.REASON_UNKNOWN_MODE)

    def test_non_string_mode_refuses(self):
        for bad in (None, 7, ["gsd"], True):
            with self.subTest(bad=bad):
                self.assertIsNone(statepath.resolve(bad, repo="r")[0])

    def test_non_string_components_refuse(self):
        self.assertIsNone(statepath.resolve("gsd", phase_id=40)[0])
        self.assertIsNone(
            statepath.resolve("default", repo=7, branch="m")[0])

    def test_run_rejects_non_dict_envelope(self):
        out = statepath.run("nope")
        self.assertIsNone(out["path"])
        self.assertIn(out["reason"], statepath.REASONS)

    def test_run_returns_the_resolved_path(self):
        out = statepath.run({"mode": "default", "repo": "triggarr",
                             "branch": ""})
        self.assertEqual(out["path"], ".turingmind/state/triggarr-.json")


class TestModeSet(unittest.TestCase):
    def test_modes_transcribed_from_phase_05(self):
        self.assertEqual(statepath.MODES,
                         ("gsd", "default", "pr", "range", "all"))

    def test_state_dir_is_the_hard_contract_value(self):
        self.assertEqual(statepath.STATE_DIR, ".turingmind/state")


class TestNoFilesystemAccess(unittest.TestCase):
    """It computes a path; it does not check or create one."""

    def _tree(self):
        with open(STATEPATH_PY, "r", encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def _imported(self):
        imported = set()
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        return imported

    def test_os_is_not_imported_at_all(self):
        self.assertNotIn("os", self._imported())

    def test_no_filesystem_module_imported(self):
        for name in ("os", "pathlib", "shutil", "glob", "tempfile",
                     "subprocess"):
            self.assertNotIn(name, self._imported())

    def test_no_open_or_dynamic_exec(self):
        banned = {"open", "eval", "exec", "compile", "__import__"}
        for node in ast.walk(self._tree()):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, banned)

    def test_the_import_checker_actually_sees_imports(self):
        """Fixture integrity — a walk that found nothing would pass
        vacuously."""
        self.assertEqual(self._imported(), {"hashlib", "json", "re", "sys"})


class TestCLI(unittest.TestCase):
    def _run(self, payload):
        return subprocess.run(
            [sys.executable, STATEPATH_PY],
            input=payload,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )

    def test_harvested_key_round_trips_through_the_shim(self):
        payload = json.dumps({"mode": "default", "repo": "triggarr",
                              "branch": ""}).encode()
        proc = self._run(payload)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertEqual(json.loads(proc.stdout.decode())["path"],
                         ".turingmind/state/triggarr-.json")

    def test_abbreviated_phase_id_refuses_through_the_shim(self):
        payload = json.dumps({"mode": "gsd", "phase_id": "40"}).encode()
        proc = self._run(payload)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertIsNone(json.loads(proc.stdout.decode())["path"])

    def test_invalid_json_exits_nonzero(self):
        self.assertNotEqual(self._run(b"not json").returncode, 0)

    def test_empty_stdin_exits_nonzero(self):
        self.assertNotEqual(self._run(b"").returncode, 0)


class TestCitations(unittest.TestCase):
    def _source(self):
        with open(STATEPATH_PY, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_cites_the_hard_contract_and_phase_05(self):
        src = self._source()
        for citation in ("review.md:12", "review.md:406", "review.md:409",
                         "review.md:423"):
            self.assertIn(citation, src)

    def test_states_the_never_abbreviate_rule(self):
        self.assertIn("never abbreviate", self._source().lower())


class TestImportSet(unittest.TestCase):
    """{json, re, sys} PLUS hashlib.

    The plan specified {json, re, sys}. FL-05 then required the `--all` key to
    be a real SHA-1 over `repo:branch:scope` (review.md:423), which is not
    computable in that set — so `hashlib` is a deliberate, documented addition,
    not drift. `os` remains forbidden.
    """

    ALLOWED = {"hashlib", "json", "re", "sys"}
    FORBIDDEN_NAMES = {"subprocess", "os", "pathlib", "shutil", "glob",
                       "eval", "exec", "compile", "__import__", "open"}

    def _imported(self):
        with open(STATEPATH_PY, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        return imported

    def test_import_set_subset_of_allowed(self):
        imported = self._imported()
        self.assertTrue(
            imported.issubset(self.ALLOWED),
            "statepath.py imports outside the allowed set: "
            + str(imported - self.ALLOWED))

    def test_no_forbidden_module_imported(self):
        for name in self._imported():
            self.assertNotIn(name, self.FORBIDDEN_NAMES)


if __name__ == "__main__":
    unittest.main()
