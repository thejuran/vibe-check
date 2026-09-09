"""test_state_shape.py — the shape leg of DIET-04 envelope byte-stability.

RESEARCH Q6 found the state envelope was never actually deterministic, so
"byte-stability" had to be DEFINED rather than assumed. The definition is two
schemas with different jobs, and the tests here exist to stop them collapsing
into one:

* `archive-compat` is DESCRIPTIVE. It records what the 37 sealed Phase-38
  states ACTUALLY contain so the tool can validate them without touching a
  byte. It is never tightened to make a new state pass.
* `future` is PRESCRIPTIVE. It is the contract every state produced after
  Phase 40 must satisfy. It is never loosened to accommodate an archive.

The regression lock is TestSchemasAreDistinct: if a later edit harmonizes the
two files, those tests fail.

Defects these tests lock (F13/F14/F11 from the adversarial review):

* F13 — a single schema with a `fixes_applied` escape hatch could not accept
  the real archives: the census found 19 distinct pass keys, 2 extra root keys,
  and 4 findings carrying neither `id` nor `title`. Twelve archive files
  conflicted with the old single schema. Hence two schemas.
* F13 (sealed evidence) — the archives are evidence Phase 43 re-measures
  against. `state_shape.py` is given NO write path (TestNoWritePath asserts it
  by AST) and `tearDownModule` asserts the whole module run changed not one
  archived byte, comparing BOTH index and worktree against HEAD.
* F14 — key presence alone would accept the very Codex-shape variability that
  was the reason byte equality was abandoned (8 archived shapes, twice a bare
  string). The future schema therefore pins the canonical codex record, an
  exact `Z` timestamp regex, and closed key sets.

Fix-list corrections applied here:

* FL-12 (index gap) — the archive integrity check compares the pinned baseline
  against BOTH the index and the worktree. Plain `git diff --quiet` compares
  worktree-vs-index only, so a STAGED modification whose worktree copy matches
  the index passes it. TestArchiveIntegrityCheck stages a real modification to
  a sealed path and asserts the check FAILS, then restores it.
* FL-14 (`reason` slug|null) — the future codex `reason` field is constrained
  to a slug or null; a free-text sentence or an empty string is a violation.
  Positive and negative tests below.

Honest statement of what this proves: the ENVELOPE shape is stable. It does
not prove orchestration or rendered reports are unchanged.
"""

import ast
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

# Make `import state_shape` resolve when unittest discovery runs from the root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import state_shape  # noqa: E402  (sibling module under test)

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_SHAPE_PY = os.path.join(HERE, "state_shape.py")
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ARCHIVE_REL = "docs/design/b3-ground-truth/runs-v2.10"
ARCHIVE_DIR = os.path.join(REPO_ROOT, ARCHIVE_REL)
ARCHIVE_GLOB = os.path.join(ARCHIVE_DIR, "*", "run-*", "state.json")

# The git TREE object of the sealed Phase-38 baseline. A tree hash is used
# rather than a commit because it is stable under rebase and cherry-pick.
ARCHIVE_TREE = "82c412b6e58b5d5a1dbddca0239f0f4b26833b4a"

# The census is the whole point: exactly 37 sealed states.
EXPECTED_STATE_COUNT = 37


def _git(*argv, **kw):
    return subprocess.run(["git", "-C", REPO_ROOT, *argv],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=30, **kw)


def archives_unmodified():
    """Is every sealed archive byte-identical to the pinned baseline?

    FL-12: `git diff --quiet -- <path>` compares the WORKTREE against the
    INDEX only, while the tree pin is taken against HEAD. A staged edit whose
    worktree copy matches the index passes that form. Comparing against HEAD
    covers staged and unstaged together; the tree-hash compare is the
    independent second leg (it reads the index, so a staged-only change moves
    it once `write-tree` runs -- but HEAD-vs-worktree already catches it).
    """
    worktree_and_index = _git("diff", "--quiet", "HEAD", "--", ARCHIVE_REL)
    staged_only = _git("diff", "--cached", "--quiet", "--", ARCHIVE_REL)
    return worktree_and_index.returncode == 0 and staged_only.returncode == 0


def tearDownModule():
    """F13 — the sealed evidence must be byte-unchanged by this whole module.

    Implemented as tearDownModule rather than a single test so it covers every
    test in the file, not just the census one.
    """
    if not archives_unmodified():
        raise AssertionError(
            "SEALED ARCHIVES MODIFIED by the test run: "
            "`git diff HEAD -- %s` is non-empty. The archives are evidence "
            "Phase 43 re-measures against; nothing in this suite may write to "
            "them." % ARCHIVE_REL)


# --------------------------------------------------------------------------
# Fixture builders. Overrides may delete a key by passing state_shape-free
# sentinel `DROP`.
# --------------------------------------------------------------------------

DROP = object()


def _apply(base, overrides):
    out = dict(base)
    for k, v in overrides.items():
        if v is DROP:
            out.pop(k, None)
        else:
            out[k] = v
    return out


def make_finding(**overrides):
    """A finding satisfying BOTH schemas' required sets (their union)."""
    base = {
        "id": "F-001",
        "file": "src/app.py",
        "line": 12,
        "title": "a title",
        "category": "security",
        "severity": "high",
        "agent": "security",
        "agent_confidence": 80,
        "problem": "a problem",
        "source_window": "a window",
        "orchestrator_score": 71,
        "band": "critical",
        "attribution": ["security"],
        "status": "new",
        "stable_hash": "abc123",
    }
    return _apply(base, overrides)


def make_codex(**overrides):
    """The canonical future-schema codex record."""
    base = {"status": "joined", "reason": None, "verdict": "approve", "findings": 2}
    return _apply(base, overrides)


def make_pass(**overrides):
    """A pass entry satisfying BOTH schemas' required sets (their union)."""
    base = {
        "pass_number": 1,
        "head_sha": "deadbeef",
        "timestamp": "2026-09-08T12:00:00Z",
        "mode": "review",
        "diff_range": "a..b",
        "agents_run": ["security"],
        "findings": [make_finding()],
        "filtered": [],
        "codex": make_codex(),
    }
    return _apply(base, overrides)


def make_state(**overrides):
    base = {"medium_acknowledgments": [], "passes": [make_pass()]}
    return _apply(base, overrides)


ARCHIVE = state_shape.load_schema("archive-compat")
FUTURE = state_shape.load_schema("future")


class TestSchemaFixtures(unittest.TestCase):
    """The schemas are DATA, not code -- a future phase diffs them as data."""

    def test_both_schemas_parse_and_carry_purpose(self):
        for name in ("archive-compat", "future"):
            with self.subTest(schema=name):
                s = state_shape.load_schema(name)
                self.assertIsInstance(s, dict)
                self.assertTrue(s.get("_purpose", "").strip(),
                                "%s schema needs a non-empty _purpose -- it is what "
                                "stops a later reader harmonizing the two" % name)

    def test_unknown_schema_name_raises(self):
        with self.assertRaises(Exception):
            state_shape.load_schema("no-such-schema")

    def test_schema_name_cannot_traverse(self):
        """`--schema` is an enum, not a filename (FL-11's A4 note)."""
        for bad in ("../secrets", "future-schema.json", "/etc/passwd"):
            with self.subTest(name=bad):
                with self.assertRaises(Exception):
                    state_shape.load_schema(bad)


class TestSchemasAreDistinct(unittest.TestCase):
    """F13 regression lock: if an edit collapses the two schemas, these fail."""

    def test_schemas_differ_in_the_load_bearing_fields(self):
        for field in ("pass_forbidden", "codex_shape", "timestamp_regex", "finding_required"):
            with self.subTest(field=field):
                self.assertNotEqual(ARCHIVE.get(field), FUTURE.get(field),
                                    "%s must differ between the descriptive and "
                                    "prescriptive schemas" % field)

    def test_archive_permits_what_future_forbids(self):
        entry = make_pass(fixes_applied=["x"], scored_by_script=True)
        self.assertEqual(state_shape.check_pass_entry(entry, ARCHIVE), [])
        reasons = state_shape.check_pass_entry(entry, FUTURE)
        self.assertIn("forbidden key in pass entry: fixes_applied", reasons)
        self.assertIn("unknown key in pass entry: scored_by_script", reasons)

    def test_finding_without_id_splits_the_schemas(self):
        """4 archived findings carry neither id nor title -- sealed evidence."""
        f = make_finding(id=DROP, title=DROP)
        self.assertEqual(state_shape.check_finding(f, ARCHIVE), [])
        reasons = state_shape.check_finding(f, FUTURE)
        self.assertIn("missing required key in finding: id", reasons)
        self.assertIn("missing required key in finding: title", reasons)

    def test_archive_stray_keys_are_future_violations(self):
        """The improvised strays are the drift the future schema exists to stop."""
        for stray in ("_normalized_fields", "_orchestrator_note", "fix", "confidence", "pending"):
            with self.subTest(stray=stray):
                f = make_finding(**{stray: "x"})
                self.assertEqual(state_shape.check_finding(f, ARCHIVE), [])
                self.assertIn("unknown key in finding: %s" % stray,
                              state_shape.check_finding(f, FUTURE))


class TestCensusAll37(unittest.TestCase):
    """F13 -- every sealed state validates clean under archive-compat."""

    def test_census_all_37_states_validate_untouched(self):
        files = sorted(glob.glob(ARCHIVE_GLOB))
        self.assertNotEqual(len(files), 0,
                            "found 0 archived states at %s -- the census is the "
                            "whole point of this test" % ARCHIVE_GLOB)
        self.assertEqual(len(files), EXPECTED_STATE_COUNT,
                         "expected %d sealed states, found %d -- the archive "
                         "changed, and that is itself the signal"
                         % (EXPECTED_STATE_COUNT, len(files)))
        failures = []
        for path in files:
            with open(path) as fh:
                state = json.load(fh)
            reasons = state_shape.check_state(state, ARCHIVE)
            if reasons:
                failures.append("%s:\n    %s"
                                % (os.path.relpath(path, REPO_ROOT),
                                   "\n    ".join(reasons)))
        # Report EVERY failing file, not just the first, so a mismatch is
        # diagnosable in one run.
        self.assertEqual(failures, [],
                         "archived states failed archive-compat (the SCHEMA is "
                         "wrong, not the archive):\n" + "\n".join(failures))

    def test_census_counts_are_what_the_schema_was_built_from(self):
        """Assert the fixture census is real, not assumed (vacuous-fixture guard)."""
        files = sorted(glob.glob(ARCHIVE_GLOB))
        passes = 0
        findings = 0
        no_id_no_title = 0
        for path in files:
            with open(path) as fh:
                state = json.load(fh)
            for entry in state.get("passes", []):
                passes += 1
                for f in entry.get("findings", []):
                    findings += 1
                    if "id" not in f and "title" not in f:
                        no_id_no_title += 1
        self.assertEqual(passes, 37)
        self.assertEqual(findings, 214)
        self.assertEqual(no_id_no_title, 4,
                         "the 4 id-less findings are why archive-compat cannot "
                         "require `id`; if this count moved, re-derive the census")


class TestArchiveIntegrityCheck(unittest.TestCase):
    """FL-12 -- the integrity check must catch a STAGED-only modification."""

    def test_check_passes_on_clean_archives(self):
        self.assertTrue(archives_unmodified(),
                        "archives must be clean before this test runs")

    def test_pinned_tree_hash_matches(self):
        proc = _git("rev-parse", "HEAD:%s" % ARCHIVE_REL)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), ARCHIVE_TREE,
                         "the sealed archive tree moved")

    def test_staged_only_modification_is_caught(self):
        """The defect FL-12 names: plain `git diff --quiet` would PASS this.

        Stage a real modification to a sealed path, assert the check fails,
        then restore both index and worktree. This proves the guard actually
        trips on the defect it targets rather than being vacuously green.
        """
        victim = sorted(glob.glob(ARCHIVE_GLOB))[0]
        rel = os.path.relpath(victim, REPO_ROOT)
        with open(victim, "rb") as fh:
            original = fh.read()
        try:
            with open(victim, "ab") as fh:
                fh.write(b"\n")
            add = _git("add", "--", rel)
            self.assertEqual(add.returncode, 0, add.stderr)
            # Worktree now MATCHES the index -- this is precisely the state
            # that defeats a bare `git diff --quiet`.
            bare_form = _git("diff", "--quiet", "--", ARCHIVE_REL)
            self.assertEqual(bare_form.returncode, 0,
                             "sanity: the defective bare form should pass here, "
                             "which is why FL-12 exists")
            self.assertFalse(archives_unmodified(),
                             "FL-12: the integrity check must catch a staged-only "
                             "modification to sealed evidence")
        finally:
            with open(victim, "wb") as fh:
                fh.write(original)
            _git("add", "--", rel)
            # Fully unstage so the tree returns to pristine HEAD state.
            _git("restore", "--staged", "--", rel)
            with open(victim, "wb") as fh:
                fh.write(original)
        self.assertTrue(archives_unmodified(), "restore failed to clean up")


class TestNoWritePath(unittest.TestCase):
    """F13 -- a validator that can write is a validator that can corrupt."""

    def setUp(self):
        with open(STATE_SHAPE_PY) as fh:
            self.tree = ast.parse(fh.read())

    def test_no_open_call_in_write_mode(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "open":
                modes = [a.value for a in node.args[1:]
                         if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                modes += [kw.value.value for kw in node.keywords
                          if kw.arg == "mode" and isinstance(kw.value, ast.Constant)]
                for mode in modes:
                    self.assertFalse(any(c in mode for c in "wax"),
                                     "state_shape.py opened a file in mode %r" % mode)

    def test_no_write_capable_imports(self):
        """AST, not a substring scan: the docstring legitimately says `shutil`."""
        imported = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    imported.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported.add(node.module.split(".")[0])
        for banned in ("shutil", "tempfile", "pathlib", "subprocess"):
            self.assertNotIn(banned, imported,
                             "state_shape.py must have no write path: imports %r" % banned)

    def test_no_mutating_os_calls(self):
        """`os` is imported for path joins only -- no filesystem mutation."""
        banned = {"remove", "rename", "unlink", "rmdir", "makedirs", "mkdir",
                  "replace", "chmod", "truncate", "symlink", "link"}
        for node in ast.walk(self.tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and getattr(node.func.value, "id", None) == "os"):
                self.assertNotIn(node.func.attr, banned,
                                 "state_shape.py must not call os.%s" % node.func.attr)

    def test_only_stderr_and_stdout_are_written(self):
        """A `.write` is allowed ONLY on a std stream, never on a file handle.

        The module reports reasons on stderr, so a blanket ban on `.write`
        would be wrong; the property that matters is that no FILE object is
        ever written to.
        """
        for node in ast.walk(self.tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("write", "writelines", "truncate")):
                target = node.func.value
                # Must be sys.stdout / sys.stderr
                ok = (isinstance(target, ast.Attribute)
                      and target.attr in ("stdout", "stderr")
                      and getattr(target.value, "id", None) == "sys")
                self.assertTrue(ok, "state_shape.py writes to something that is "
                                    "not sys.stdout/sys.stderr")


class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "os", "re", "sys"}

    def test_imports_are_exactly_the_allowed_set(self):
        with open(STATE_SHAPE_PY) as fh:
            tree = ast.parse(fh.read())
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    found.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
        self.assertEqual(found, self.ALLOWED)


class TestPassRequiredKeys(unittest.TestCase):

    def test_missing_required_pass_key_named_exactly_once(self):
        for schema, name in ((ARCHIVE, "archive-compat"), (FUTURE, "future")):
            for key in schema["pass_required"]:
                with self.subTest(schema=name, key=key):
                    entry = make_pass(**{key: DROP})
                    reasons = state_shape.check_pass_entry(entry, schema)
                    want = "missing required key in pass entry: %s" % key
                    self.assertEqual([r for r in reasons if r == want], [want])

    def test_complete_entry_is_clean_under_both(self):
        for schema, name in ((ARCHIVE, "archive-compat"), (FUTURE, "future")):
            with self.subTest(schema=name):
                self.assertEqual(state_shape.check_pass_entry(make_pass(), schema), [])

    def test_missing_required_finding_key_named(self):
        for key in FUTURE["finding_required"]:
            with self.subTest(key=key):
                f = make_finding(**{key: DROP})
                self.assertIn("missing required key in finding: %s" % key,
                              state_shape.check_finding(f, FUTURE))


class TestClosedRoot(unittest.TestCase):
    """Drift-lock: catches a future phase quietly adding a root field."""

    def test_unknown_root_key_rejected_under_both(self):
        for schema, name in ((ARCHIVE, "archive-compat"), (FUTURE, "future")):
            with self.subTest(schema=name):
                state = make_state(latency_ms=12)
                self.assertIn("unknown root key: latency_ms",
                              state_shape.check_state(state, schema))

    def test_observed_root_keys_split_the_schemas(self):
        """phase_id/scope_label were OBSERVED, so archive-compat allows them."""
        state = make_state(phase_id="p", scope_label="s")
        self.assertEqual(state_shape.check_state(state, ARCHIVE), [])
        reasons = state_shape.check_state(state, FUTURE)
        self.assertIn("unknown root key: phase_id", reasons)
        self.assertIn("unknown root key: scope_label", reasons)

    def test_missing_required_root_key(self):
        self.assertIn("missing required root key: passes",
                      state_shape.check_state({"medium_acknowledgments": []}, FUTURE))
        self.assertIn("missing required root key: medium_acknowledgments",
                      state_shape.check_state({"passes": []}, FUTURE))
        # archive-compat only requires `passes` -- 4 archived states omit
        # medium_acknowledgments.
        self.assertEqual(state_shape.check_state({"passes": []}, ARCHIVE), [])


class TestCodexCanonicalShape(unittest.TestCase):
    """F14 -- key presence alone would accept the variability that killed byte equality.

    The 8 codex shapes actually present in the archives are built as fixtures
    below. Under `archive-compat` (codex_shape null) every one is accepted.
    Under `future` only the canonical record survives -- the honest statement
    of what the new contract changes:

      ACCEPTED by future:  none of the 8 archived shapes as-is.
      REJECTED by future:  all 8. Specifically:
        {joined, findings, cross_confirmed}          x7  -- no status/reason/verdict, strays
        {joined, findings, verdict}                  x5  -- no status/reason, stray `joined`
        {joined, findings, verdict, cross_confirmed} x4  -- same plus stray
        {status, findings, cross_confirmed}          x3  -- no reason/verdict, stray
        <bare string>                                x2  -- not an object at all
        {status, findings, verdict, cross_confirmed} x1  -- no reason, stray
        {status, findings, verdict}                  x1  -- no reason
        {status, findings, scope, smoke_check, cross_confirmed} x1 -- no reason/verdict, 3 strays

    Every archived codex record would fail the future contract. That is the
    point: the field was never canonical, and Phase 40 makes it so.
    """

    ARCHIVED_SHAPES = (
        {"joined": True, "findings": 2, "cross_confirmed": 1},
        {"joined": True, "findings": 0, "verdict": "approve"},
        {"joined": True, "findings": 1, "verdict": "approve", "cross_confirmed": 0},
        {"status": "skipped", "findings": 0, "cross_confirmed": 0},
        "codex skipped: not installed",
        {"status": "joined", "findings": 3, "verdict": "needs-attention", "cross_confirmed": 1},
        {"status": "joined", "findings": 1, "verdict": "approve"},
        {"status": "skipped", "findings": 0, "scope": "x", "smoke_check": True,
         "cross_confirmed": 0},
    )

    def test_all_archived_shapes_accepted_by_archive_compat(self):
        for i, shape in enumerate(self.ARCHIVED_SHAPES):
            with self.subTest(shape=i):
                entry = make_pass(codex=shape)
                self.assertEqual(state_shape.check_pass_entry(entry, ARCHIVE), [])

    def test_every_archived_shape_rejected_by_future(self):
        for i, shape in enumerate(self.ARCHIVED_SHAPES):
            with self.subTest(shape=i):
                entry = make_pass(codex=shape)
                self.assertNotEqual(state_shape.check_pass_entry(entry, FUTURE), [],
                                    "archived codex shape %d must not satisfy the "
                                    "canonical contract" % i)

    def test_bare_string_codex_rejected(self):
        entry = make_pass(codex="codex skipped")
        self.assertIn("codex record is not an object",
                      state_shape.check_pass_entry(entry, FUTURE))

    def test_canonical_record_accepted(self):
        self.assertEqual(state_shape.check_pass_entry(make_pass(), FUTURE), [])

    def test_missing_verdict_rejected(self):
        entry = make_pass(codex=make_codex(verdict=DROP))
        self.assertIn("missing required key in codex record: verdict",
                      state_shape.check_pass_entry(entry, FUTURE))

    def test_extra_codex_key_rejected(self):
        entry = make_pass(codex=make_codex(cross_confirmed=1))
        self.assertIn("unknown key in codex record: cross_confirmed",
                      state_shape.check_pass_entry(entry, FUTURE))

    def test_status_enum(self):
        for good in ("joined", "skipped", "off"):
            with self.subTest(status=good):
                entry = make_pass(codex=make_codex(status=good))
                self.assertEqual(state_shape.check_pass_entry(entry, FUTURE), [])
        entry = make_pass(codex=make_codex(status="weird"))
        self.assertIn("codex status is not in the pinned enum",
                      state_shape.check_pass_entry(entry, FUTURE))

    def test_verdict_enum_including_null(self):
        for good in ("approve", "needs-attention", None):
            with self.subTest(verdict=good):
                entry = make_pass(codex=make_codex(verdict=good))
                self.assertEqual(state_shape.check_pass_entry(entry, FUTURE), [])
        entry = make_pass(codex=make_codex(verdict="lgtm"))
        self.assertIn("codex verdict is not in the pinned enum",
                      state_shape.check_pass_entry(entry, FUTURE))

    def test_findings_must_be_int(self):
        for bad in ("2", 2.5, None, [2]):
            with self.subTest(findings=bad):
                entry = make_pass(codex=make_codex(findings=bad))
                self.assertIn("codex findings count is not an integer",
                              state_shape.check_pass_entry(entry, FUTURE))
        # bool is not an acceptable int here either
        entry = make_pass(codex=make_codex(findings=True))
        self.assertIn("codex findings count is not an integer",
                      state_shape.check_pass_entry(entry, FUTURE))


class TestCodexReasonSlug(unittest.TestCase):
    """FL-14 -- `reason` is a slug or null, never free text."""

    def test_valid_slugs_and_null_accepted(self):
        for good in (None, "not-installed", "off", "diff-not-representable", "a1", "x-9-y"):
            with self.subTest(reason=good):
                entry = make_pass(codex=make_codex(reason=good))
                self.assertEqual(state_shape.check_pass_entry(entry, FUTURE), [])

    def test_free_text_and_empty_rejected(self):
        for bad in ("", "Codex was skipped because it is not installed.",
                    "Not-Installed", "not_installed", "-lead", "trail-",
                    "double--hyphen", " spaced ", 7):
            with self.subTest(reason=bad):
                entry = make_pass(codex=make_codex(reason=bad))
                self.assertIn("codex reason is not a slug or null",
                              state_shape.check_pass_entry(entry, FUTURE))


class TestTimestampRegex(unittest.TestCase):
    """F14 -- the archives carry two timestamp forms; the future carries one."""

    GOOD = "2026-09-08T12:00:00Z"
    BAD = ("2026-09-08T12:00:00+00:00", "2026-09-08T12:00:00.123456Z",
           "2026-09-08 12:00:00Z", "2026-09-08T12:00:00")

    def test_canonical_timestamp_passes_future(self):
        entry = make_pass(timestamp=self.GOOD)
        self.assertEqual(state_shape.check_pass_entry(entry, FUTURE), [])

    def test_noncanonical_timestamps_rejected_by_future(self):
        for bad in self.BAD:
            with self.subTest(timestamp=bad):
                entry = make_pass(timestamp=bad)
                self.assertIn("timestamp does not match the pinned format",
                              state_shape.check_pass_entry(entry, FUTURE))

    def test_archive_compat_accepts_all_forms(self):
        """regex null -- the archives contain both forms (35 Z, 2 offset)."""
        for ts in (self.GOOD,) + self.BAD:
            with self.subTest(timestamp=ts):
                entry = make_pass(timestamp=ts)
                self.assertEqual(state_shape.check_pass_entry(entry, ARCHIVE), [])

    def test_both_archived_timestamp_forms_are_real(self):
        """Vacuous-fixture guard: the two forms exist in the sealed data."""
        seen_z = seen_offset = False
        for path in sorted(glob.glob(ARCHIVE_GLOB)):
            with open(path) as fh:
                state = json.load(fh)
            for entry in state.get("passes", []):
                ts = entry.get("timestamp", "")
                if re.match(FUTURE["timestamp_regex"], ts):
                    seen_z = True
                else:
                    seen_offset = True
        self.assertTrue(seen_z, "no second-resolution Z timestamp in the archives")
        self.assertTrue(seen_offset, "no non-canonical timestamp in the archives")


class TestAllOnlyKeys(unittest.TestCase):
    """Diff-mode purity: the three --all-only keys must be absent in diff mode."""

    def test_all_only_key_in_diff_mode_rejected(self):
        for schema, name in ((ARCHIVE, "archive-compat"), (FUTURE, "future")):
            for key in ("cap_applied", "chunk_total", "capped_chunks"):
                with self.subTest(schema=name, key=key):
                    entry = make_pass(**{key: 1})
                    self.assertIn(
                        "--all-only key present in diff-mode pass entry: %s" % key,
                        state_shape.check_pass_entry(entry, schema, all_mode=False))

    def test_all_only_key_accepted_with_all_mode(self):
        for schema, name in ((ARCHIVE, "archive-compat"), (FUTURE, "future")):
            for key in ("cap_applied", "chunk_total", "capped_chunks"):
                with self.subTest(schema=name, key=key):
                    entry = make_pass(**{key: 1})
                    self.assertEqual(
                        state_shape.check_pass_entry(entry, schema, all_mode=True), [])


class TestNeverEcho(unittest.TestCase):
    """T-40-15 -- reasons name KEYS only, never a value from the state."""

    SENTINEL_TITLE = "SENTINEL-LEAK-TITLE"
    SENTINEL_PATH = "../../etc/passwd"

    def _broken_state(self):
        f = make_finding(title=self.SENTINEL_TITLE, file=self.SENTINEL_PATH,
                         id=DROP, leaked_stray=self.SENTINEL_TITLE)
        return make_state(passes=[make_pass(findings=[f], fixes_applied=[self.SENTINEL_PATH],
                                            timestamp="not-a-timestamp")])

    def test_reasons_never_contain_state_values(self):
        reasons = state_shape.check_state(self._broken_state(), FUTURE)
        self.assertNotEqual(reasons, [], "the fixture must actually be broken")
        blob = "\n".join(reasons)
        self.assertNotIn(self.SENTINEL_TITLE, blob)
        self.assertNotIn(self.SENTINEL_PATH, blob)
        self.assertNotIn("etc/passwd", blob)

    def test_cli_never_echoes_state_values(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(self._broken_state(), fh)
            path = fh.name
        try:
            proc = subprocess.run([sys.executable, STATE_SHAPE_PY, path,
                                   "--schema", "future"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, timeout=30)
            self.assertEqual(proc.returncode, 1)
            combined = proc.stdout + proc.stderr
            self.assertNotIn(self.SENTINEL_TITLE, combined)
            self.assertNotIn("etc/passwd", combined)
        finally:
            os.unlink(path)

    def test_every_reason_is_drawn_from_the_reasons_tuple(self):
        """Reasons are formatted from a module-level REASONS tuple."""
        self.assertTrue(hasattr(state_shape, "REASONS"))
        self.assertIsInstance(state_shape.REASONS, tuple)
        templates = [t.split("%s")[0] for t in state_shape.REASONS]
        for reason in state_shape.check_state(self._broken_state(), FUTURE):
            self.assertTrue(any(reason.startswith(t) for t in templates),
                            "reason %r is not drawn from REASONS" % reason)


class TestCli(unittest.TestCase):
    """The batch checks branch on the exit code -- lock it. GATE semantics (D-13)."""

    def _run(self, *argv):
        return subprocess.run([sys.executable, STATE_SHAPE_PY, *argv],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=30)

    def _tmp_state(self, obj):
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        if isinstance(obj, str):
            fh.write(obj)
        else:
            json.dump(obj, fh)
        fh.close()
        self.addCleanup(os.unlink, fh.name)
        return fh.name

    def test_clean_state_exits_zero_with_empty_stderr(self):
        proc = self._run(self._tmp_state(make_state()), "--schema", "future")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr.strip(), "")

    def test_violation_exits_one(self):
        proc = self._run(self._tmp_state(make_state(passes=[make_pass(fixes_applied=[])])),
                         "--schema", "future")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("forbidden key in pass entry: fixes_applied", proc.stderr)

    def test_missing_schema_flag_exits_two(self):
        """No default: a new state can never be silently checked as historical."""
        proc = self._run(self._tmp_state(make_state()))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--schema", proc.stderr)

    def test_schema_must_be_the_enum_not_a_filename(self):
        proc = self._run(self._tmp_state(make_state()),
                         "--schema", "future-schema.json")
        self.assertEqual(proc.returncode, 2)

    def test_nonexistent_path_exits_two(self):
        proc = self._run("/no/such/state.json", "--schema", "future")
        self.assertEqual(proc.returncode, 2)

    def test_invalid_json_exits_two(self):
        proc = self._run(self._tmp_state("{not json"), "--schema", "future")
        self.assertEqual(proc.returncode, 2)

    def test_archived_state_passes_archive_compat_via_cli(self):
        victim = sorted(glob.glob(ARCHIVE_GLOB))[0]
        proc = self._run(victim, "--schema", "archive-compat")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr.strip(), "")

    def test_archived_state_with_fixes_applied_fails_future_via_cli(self):
        """Acceptance criterion: the named archive/future split, end to end."""
        hit = None
        for path in sorted(glob.glob(ARCHIVE_GLOB)):
            with open(path) as fh:
                state = json.load(fh)
            if any("fixes_applied" in p for p in state.get("passes", [])):
                hit = path
                break
        self.assertIsNotNone(hit, "26 archived passes carry fixes_applied")
        proc = self._run(hit, "--schema", "future")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("forbidden key in pass entry: fixes_applied", proc.stderr)

    def test_all_flag_accepted(self):
        entry = make_pass(cap_applied=None, chunk_total=3, capped_chunks=[])
        proc = self._run(self._tmp_state(make_state(passes=[entry])),
                         "--schema", "future", "--all")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_reasons_go_to_stderr_one_per_line(self):
        entry = make_pass(fixes_applied=[], scored_by_script=True)
        proc = self._run(self._tmp_state(make_state(passes=[entry])),
                         "--schema", "future")
        self.assertEqual(proc.returncode, 1)
        lines = [ln for ln in proc.stderr.strip().split("\n") if ln]
        self.assertGreaterEqual(len(lines), 2)


class TestMalformedInput(unittest.TestCase):
    """Fail closed on shapes that are not the expected containers."""

    def test_non_object_state(self):
        for bad in ([], "x", 3, None):
            with self.subTest(state=bad):
                self.assertNotEqual(state_shape.check_state(bad, FUTURE), [])

    def test_passes_not_a_list(self):
        self.assertIn("passes is not a list",
                      state_shape.check_state({"medium_acknowledgments": [],
                                               "passes": {}}, FUTURE))

    def test_pass_entry_not_an_object(self):
        self.assertNotEqual(
            state_shape.check_state(make_state(passes=["x"]), FUTURE), [])

    def test_findings_not_a_list(self):
        self.assertIn("findings is not a list",
                      state_shape.check_pass_entry(make_pass(findings={}), FUTURE))

    def test_finding_not_an_object(self):
        self.assertNotEqual(
            state_shape.check_pass_entry(make_pass(findings=["x"]), FUTURE), [])


if __name__ == "__main__":
    unittest.main()
