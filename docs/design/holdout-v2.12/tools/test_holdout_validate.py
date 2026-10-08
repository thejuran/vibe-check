"""Tests for holdout_validate — the checks the owner runs after the finder
session, and that seal re-runs before sealing.

Locked here:
  * A complete, valid six-case holdout (holdout_fixture.make_valid_holdout:
    two tiny git repos, real base.tar exports, real diffs, executable proofs
    whose recorded results came from actually running them) passes every
    check.
  * One failing fixture per rule: each mutates exactly one thing in the valid
    tree and asserts the named check turns to PROBLEM with a plain fix hint.
  * Output never carries case content: key text, diff lines and repo paths
    beyond the basename stay out of stdout.

Mutants follow the gitsnap convention: first show the real component sees the
difference, then patch it out and show the case is no longer caught.

The valid holdout is built once per module (setUpModule) and copied into each
test's own temp dir; the copies keep pointing at the module's two source
repos, which nothing mutates.
"""

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

import holdout_fixture  # noqa: E402
import holdout_kit  # noqa: E402
import holdout_validate  # noqa: E402
from holdout_validate import Check  # noqa: E402

KIT_PY = os.path.join(TOOLS_DIR, "holdout_kit.py")
VALIDATE_PY = os.path.join(TOOLS_DIR, "holdout_validate.py")

_TEMPLATE = {}


def setUpModule():
    tmp = tempfile.TemporaryDirectory()
    folder, ids = holdout_fixture.make_valid_holdout(tmp.name)
    _TEMPLATE.update(tmp=tmp, root=os.path.realpath(tmp.name),
                     folder=folder, ids=ids)


def tearDownModule():
    _TEMPLATE["tmp"].cleanup()


def _clean_env():
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
    env.pop("CLAUDE_CONFIG_DIR", None)
    return mock.patch.dict(os.environ, env, clear=True)


def _imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module)
    return names


class ValidateCase(unittest.TestCase):
    """Base: a private copy of the valid holdout and editing helpers."""

    SKIP_PROOFS = True

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        env = _clean_env()
        env.start()
        self.addCleanup(env.stop)
        self.folder = os.path.join(self.tmp, "holdout")
        shutil.copytree(_TEMPLATE["folder"], self.folder, symlinks=True)
        self.ids = dict(_TEMPLATE["ids"])

    # ---- paths and edits

    def kdir(self, slot):
        return os.path.join(self.folder, "sealed", "keys", self.ids[slot])

    def cdir(self, slot):
        return os.path.join(self.folder, "sealed", "cases", self.ids[slot])

    def path(self, slot, name):
        if name in holdout_kit.CASE_FILES:
            return os.path.join(self.cdir(slot), name)
        return os.path.join(self.kdir(slot), name)

    def load(self, slot, name):
        with open(self.path(slot, name), encoding="utf-8") as fh:
            return json.load(fh)

    def save(self, slot, name, obj):
        with open(self.path(slot, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh)

    def edit(self, slot, name, fn):
        obj = self.load(slot, name)
        fn(obj)
        self.save(slot, name, obj)

    def read_bytes(self, slot, name):
        with open(self.path(slot, name), "rb") as fh:
            return fh.read()

    def write_bytes(self, slot, name, data):
        with open(self.path(slot, name), "wb") as fh:
            fh.write(data)

    def edit_exclusions(self, fn):
        path = os.path.join(self.folder, "kit", "b3-exclusions.json")
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
        fn(obj)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)

    # ---- running and asserting

    def checks(self):
        return holdout_validate.validate_folder(self.folder,
                                                skip_proofs=self.SKIP_PROOFS)

    def named(self, checks, name):
        found = [c for c in checks if c.name == name]
        self.assertTrue(found, "no check named %r" % name)
        return found

    def assertProblem(self, name, fragment=None, checks=None):
        checks = self.checks() if checks is None else checks
        bad = [c for c in self.named(checks, name) if not c.ok]
        self.assertTrue(bad, "%s did not report a problem" % name)
        if fragment is not None:
            self.assertTrue(any(fragment in c.message for c in bad),
                            [c.message for c in bad])
        for c in bad:
            self.assertIn("Fix:", c.message)
        return bad

    def assertCheckOk(self, name, checks=None):
        checks = self.checks() if checks is None else checks
        for c in self.named(checks, name):
            self.assertTrue(c.ok, c.message)

    def run_cli(self, *args, env=None):
        return subprocess.run(
            [sys.executable, KIT_PY, "--folder", self.folder, "validate",
             *args], cwd=self.tmp,
            env=env or holdout_fixture.kit_env(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=600)


# ================================================================ valid


class TestValidFixture(ValidateCase):

    def test_every_check_ok(self):
        checks = self.checks()
        self.assertGreaterEqual(len(checks), 11)
        for c in checks:
            self.assertTrue(c.ok, "%s: %s" % (c.name, c.message))
            self.assertFalse(c.warning, "%s: %s" % (c.name, c.message))

    def test_every_rule_has_a_check(self):
        names = {c.name for c in self.checks()}
        for name in ("slots", "opaque ids", "file allowlist",
                     "provenance fields", "budget", "search ledger",
                     "reviewer output", "repo_in_b3", "eligibility",
                     "C1/Q2 eligibility", "C1/Q2 distinct", "B3 reuse",
                     "key shape", "slot agreement", "proofs"):
            self.assertIn(name, names)

    def test_check_has_four_fields(self):
        c = Check("x", True, "m")
        self.assertEqual((c.name, c.ok, c.message, c.warning),
                         ("x", True, "m", False))
        self.assertTrue(Check("x", True, "m", warning=True).warning)

    def test_constructed_case_with_full_budget_is_valid(self):
        def fn(p):
            p["kind"] = "constructed"
            del p["base_rev"]
            del p["feature_rev"]
            p["constructed_by"] = "isolated-agent"
            p["search"]["screened"] = 25
            p["search"]["rejections"] = [
                {"ordinal": n, "rev": "%040x" % (100 + n), "reason": "r"}
                for n in range(1, 26)]
        self.edit("Q3", "provenance.json", fn)
        for c in self.checks():
            self.assertTrue(c.ok, "%s: %s" % (c.name, c.message))

    def test_missing_sealed_cases_raises(self):
        shutil.rmtree(os.path.join(self.folder, "sealed"))
        with self.assertRaises(holdout_kit.KitError):
            self.checks()


class TestSlotOf(ValidateCase):

    def test_slot_of_reads_key(self):
        for slot, cid in self.ids.items():
            self.assertEqual(holdout_validate.slot_of(self.folder, cid), slot)

    def test_slot_of_refuses_unreadable_or_bad(self):
        os.remove(self.path("C1", "key.json"))
        with self.assertRaises(holdout_kit.KitError):
            holdout_validate.slot_of(self.folder, self.ids["C1"])
        self.edit("C2", "key.json", lambda k: k.update(slot="C9"))
        with self.assertRaises(holdout_kit.KitError):
            holdout_validate.slot_of(self.folder, self.ids["C2"])


# ================================================================ structure


class TestSlots(ValidateCase):

    def test_a_five_cases(self):
        shutil.rmtree(self.cdir("Q3"))
        shutil.rmtree(self.kdir("Q3"))
        self.assertProblem("slots", "5")

    def test_a_case_without_key_dir(self):
        shutil.rmtree(self.cdir("Q3"))
        self.assertProblem("slots")

    def test_b_duplicate_slot(self):
        self.edit("Q3", "key.json", lambda k: k.update(slot="C1"))
        self.edit("Q3", "provenance.json", lambda p: p.update(slot="C1"))
        self.assertProblem("slots", "C1")

    def test_c_non_opaque_id(self):
        os.rename(self.cdir("C1"),
                  os.path.join(self.folder, "sealed", "cases", "C1-triggarr"))
        os.rename(self.kdir("C1"),
                  os.path.join(self.folder, "sealed", "keys", "C1-triggarr"))
        bad = self.assertProblem("opaque ids")
        for c in bad:
            self.assertNotIn("triggarr", c.message)


class TestAllowlist(ValidateCase):

    def test_d_extra_case_file(self):
        with open(os.path.join(self.cdir("C2"), "notes.txt"), "w") as fh:
            fh.write("finder notes\n")
        bad = self.assertProblem("file allowlist", "C2")
        for c in bad:
            self.assertNotIn("notes", c.message)

    def test_extra_key_file(self):
        with open(os.path.join(self.kdir("Q1"), "scratch.json"), "w") as fh:
            fh.write("{}\n")
        self.assertProblem("file allowlist", "Q1")

    def test_proof_dir_may_hold_helpers(self):
        with open(os.path.join(self.kdir("Q1"), "proof", "helper.py"),
                  "w") as fh:
            fh.write("print(1)\n")
        self.assertCheckOk("file allowlist")

    def test_missing_required_file(self):
        os.remove(self.path("C3", "change.diff"))
        self.assertProblem("file allowlist", "C3")
        os.remove(self.path("Q2", "provenance.json"))
        self.assertProblem("file allowlist", "Q2")

    def test_symlink_is_a_problem_not_a_crash(self):
        os.symlink("/etc/hosts", os.path.join(self.kdir("Q1"), "proof", "l"))
        self.assertProblem("file allowlist", "Q1")

    def test_case_json_must_match_layout(self):
        self.edit("C1", "case.json", lambda c: c.update(id="H-00000000"))
        self.assertProblem("file allowlist", "case.json")


class TestProvenance(ValidateCase):

    def test_e_budget_over_25(self):
        self.edit("C3", "provenance.json",
                  lambda p: p["search"].update(screened=26))
        self.assertProblem("budget", "C3")

    def test_budget_field_must_be_25(self):
        self.edit("C3", "provenance.json",
                  lambda p: p["search"].update(budget=30))
        self.assertProblem("budget", "25")

    def test_f_organic_rejection_arithmetic(self):
        self.edit("C2", "provenance.json",
                  lambda p: p["search"]["rejections"].pop())
        self.assertProblem("search ledger", "C2")

    def test_ordinals_must_be_one_to_n(self):
        def fn(p):
            p["search"]["rejections"][1]["ordinal"] = 1
        self.edit("C2", "provenance.json", fn)
        self.assertProblem("search ledger", "ordinal")

    def test_selected_rev_cannot_be_rejected(self):
        def fn(p):
            p["search"]["rejections"][1]["rev"] = p["feature_rev"]
        self.edit("Q1", "provenance.json", fn)
        self.assertProblem("search ledger", "Q1")

    def test_q_constructed_rejection_arithmetic(self):
        def fn(p):
            p["kind"] = "constructed"
            del p["base_rev"]
            del p["feature_rev"]
            p["constructed_by"] = "owner"
            p["search"]["screened"] = 25
            p["search"]["rejections"] = [
                {"ordinal": n, "rev": "%040x" % (100 + n), "reason": "r"}
                for n in range(1, 25)]
        self.edit("Q3", "provenance.json", fn)
        self.assertProblem("search ledger", "Q3")

    def test_constructed_needs_exhausted_budget(self):
        def fn(p):
            p["kind"] = "constructed"
            del p["base_rev"]
            del p["feature_rev"]
            p["constructed_by"] = "owner"
            p["search"]["rejections"].append(
                {"ordinal": 3, "rev": "%040x" % 99, "reason": "r"})
        self.edit("Q3", "provenance.json", fn)
        self.assertProblem("search ledger", "25")

    def test_g_reviewer_output_missing(self):
        self.edit("C1", "provenance.json",
                  lambda p: p.pop("selected_using_reviewer_output"))
        self.assertProblem("reviewer output", "C1")

    def test_g_reviewer_output_true(self):
        self.edit("C1", "provenance.json",
                  lambda p: p.update(selected_using_reviewer_output=True))
        self.assertProblem("reviewer output", "C1")

    def test_g_reviewer_output_falsy_not_false(self):
        self.edit("C1", "provenance.json",
                  lambda p: p.update(selected_using_reviewer_output=0))
        self.assertProblem("reviewer output")

    def test_h_repo_in_b3_mismatch(self):
        self.edit("C3", "provenance.json",
                  lambda p: p.update(repo_name="triggarr"))
        self.assertProblem("repo_in_b3", "mismatch")

    def test_i_c1_from_b3_repo(self):
        self.edit("C1", "provenance.json",
                  lambda p: p.update(repo_name="triggarr", repo_in_b3=True))
        self.assertProblem("C1/Q2 eligibility", "C1")
        self.assertCheckOk("repo_in_b3")

    def test_q2_from_b3_repo(self):
        self.edit("Q2", "provenance.json",
                  lambda p: p.update(repo_name="seedsyncarr",
                                     repo_in_b3=True))
        self.assertProblem("C1/Q2 eligibility", "Q2")

    def test_other_slots_may_come_from_b3_repo(self):
        self.edit("C3", "provenance.json",
                  lambda p: p.update(repo_name="triggarr", repo_in_b3=True))
        self.assertCheckOk("C1/Q2 eligibility")
        self.assertCheckOk("repo_in_b3")

    def test_r_tuning_repo_never_eligible(self):
        self.edit("Q1", "provenance.json",
                  lambda p: p.update(repo_name="turingmind-code-review"))
        self.assertProblem("eligibility", "Q1")

    def test_source_repo_must_be_listed_eligible(self):
        self.edit("Q1", "provenance.json",
                  lambda p: p.update(source_repo="/somewhere/alpha"))
        bad = self.assertProblem("eligibility", "Q1")
        for c in bad:
            self.assertNotIn("/somewhere", c.message)

    def test_kind_enum(self):
        self.edit("C1", "provenance.json", lambda p: p.update(kind="found"))
        self.assertProblem("provenance fields", "C1")

    def test_organic_revs_are_40_hex(self):
        self.edit("C1", "provenance.json", lambda p: p.update(base_rev="abc"))
        self.assertProblem("provenance fields", "base_rev")

    def test_constructed_by_enum(self):
        def fn(p):
            p["kind"] = "constructed"
            del p["base_rev"]
            del p["feature_rev"]
            p["constructed_by"] = "someone"
        self.edit("Q3", "provenance.json", fn)
        self.assertProblem("provenance fields", "constructed_by")

    def test_found_at_must_be_iso(self):
        self.edit("C1", "provenance.json",
                  lambda p: p.update(found_at="yesterday"))
        self.assertProblem("provenance fields", "found_at")

    def test_unknown_field_refused(self):
        self.edit("C1", "provenance.json", lambda p: p.update(notes="x"))
        self.assertProblem("provenance fields", "C1")

    def test_p_slot_agreement(self):
        self.edit("C2", "provenance.json", lambda p: p.update(slot="C3"))
        self.assertProblem("slot agreement", "C2")


class TestDistinct(ValidateCase):

    def _q2_from_c1_source(self):
        c1 = self.load("C1", "provenance.json")

        def fn(p):
            for k in ("source_repo", "repo_name", "base_rev", "feature_rev"):
                p[k] = c1[k]
        self.edit("Q2", "provenance.json", fn)

    def test_j_same_change(self):
        self._q2_from_c1_source()
        self.write_bytes("Q2", "change.diff",
                         self.read_bytes("C1", "change.diff"))
        bad = self.assertProblem("C1/Q2 distinct")
        msgs = " ".join(c.message for c in bad)
        self.assertIn("revision", msgs)
        self.assertIn("diff", msgs)

    def test_k_near_identical_diff(self):
        diff = self.read_bytes("C1", "change.diff")
        edited = diff.replace(b'+v_C1_1="value-C1-1-new"',
                              b'+v_C1_1="value-C1-1-newer"')
        self.assertNotEqual(diff, edited)
        self.write_bytes("Q2", "change.diff", edited)
        self.assertProblem("C1/Q2 distinct", "similar")

    def test_valid_pair_similarity_is_low(self):
        lines = holdout_validate._changed_lines
        ratio = holdout_validate._similarity(
            lines(self.read_bytes("C1", "change.diff")),
            lines(self.read_bytes("Q2", "change.diff")))
        self.assertLess(ratio, 0.5)

    def test_changed_lines_skip_headers(self):
        out = holdout_validate._changed_lines(
            b"--- a/x\n+++ b/x\n@@ -1 +1 @@\n-old\n+new\n ctx\n")
        self.assertEqual(out, ["old", "new"])


class TestB3Reuse(ValidateCase):

    def test_l_reused_commit(self):
        self.edit("C3", "provenance.json",
                  lambda p: p.update(base_rev=holdout_fixture.THROWAWAY_B3_REV))
        self.assertProblem("B3 reuse", "C3")

    def test_l_reused_feature_commit(self):
        self.edit("Q1", "provenance.json",
                  lambda p: p.update(
                      feature_rev=holdout_fixture.THROWAWAY_B3_REV))
        self.assertProblem("B3 reuse", "Q1")

    def test_m_reused_patch(self):
        digest = holdout_kit.sha256_bytes(self.read_bytes("Q3", "change.diff"))
        self.edit_exclusions(
            lambda e: e["patch_sha256"].append(digest))
        self.assertProblem("B3 reuse", "Q3")

    def test_missing_exclusions_is_a_problem(self):
        os.remove(os.path.join(self.folder, "kit", "b3-exclusions.json"))
        self.assertProblem("B3 reuse")
        self.assertProblem("repo_in_b3")


class TestKeyShape(ValidateCase):

    def test_n_catch_missing_causal_failure(self):
        self.edit("C2", "key.json", lambda k: k.pop("causal_failure"))
        self.assertProblem("key shape", "C2")

    def test_n_catch_empty_defect(self):
        self.edit("C2", "key.json", lambda k: k.update(defect="  "))
        self.assertProblem("key shape", "C2")

    def test_n2_category_missing(self):
        self.edit("C1", "key.json", lambda k: k.pop("causal_failure_category"))
        self.assertProblem("key shape", "C1")

    def test_n2_category_unknown_names_allowed_list(self):
        self.edit("C1", "key.json",
                  lambda k: k.update(causal_failure_category="sql-thing"))
        bad = self.assertProblem("key shape", "missing-input-validation")
        for c in bad:
            self.assertNotIn("sql-thing", c.message)

    def test_n3_category_other_warns(self):
        self.edit("C3", "key.json",
                  lambda k: k.update(causal_failure_category="other"))
        checks = self.checks()
        shape = self.named(checks, "key shape")
        self.assertTrue(all(c.ok for c in shape))
        warned = [c for c in shape if c.warning]
        self.assertTrue(warned)
        self.assertIn('C3: causal_failure_category is "other"; the '
                      'cross-check cannot agree mechanically and the seal '
                      'will block until resolved',
                      [c.message for c in warned])

    def test_o_quiet_empty_exposure_check(self):
        self.edit("Q1", "key.json", lambda k: k.update(exposure_check=""))
        self.assertProblem("key shape", "Q1")

    def test_class_must_match_slot(self):
        self.edit("Q2", "key.json", lambda k: k.update(**{"class": "catch"}))
        self.assertProblem("key shape", "Q2")

    def test_location_range(self):
        self.edit("C1", "key.json",
                  lambda k: k["location"].update(line_start=9, line_end=4))
        self.assertProblem("key shape", "C1")
        self.edit("C1", "key.json",
                  lambda k: k["location"].update(line_start=True, line_end=4))
        self.assertProblem("key shape", "C1")

    def test_unknown_key_field(self):
        self.edit("Q3", "key.json", lambda k: k.update(defect="x"))
        self.assertProblem("key shape", "Q3")


# ================================================================ mutants


class TestMutants(ValidateCase):

    def test_budget_is_load_bearing(self):
        self.edit("C3", "provenance.json",
                  lambda p: p["search"].update(screened=26))
        self.assertProblem("budget")
        with mock.patch.object(holdout_validate, "_check_budget",
                               return_value=Check("budget", True, "x")):
            self.assertCheckOk("budget")

    def test_similarity_is_load_bearing(self):
        diff = self.read_bytes("C1", "change.diff")
        self.write_bytes("Q2", "change.diff",
                         diff.replace(b'+v_C1_1="value-C1-1-new"',
                                      b'+v_C1_1="value-C1-1-newer"'))
        self.assertProblem("C1/Q2 distinct")
        with mock.patch.object(holdout_validate, "_similarity",
                               return_value=0.0):
            self.assertCheckOk("C1/Q2 distinct")

    def test_b3_hashes_are_load_bearing(self):
        self.edit("C3", "provenance.json",
                  lambda p: p.update(base_rev=holdout_fixture.THROWAWAY_B3_REV))
        digest = holdout_kit.sha256_bytes(self.read_bytes("Q3", "change.diff"))
        self.edit_exclusions(lambda e: e["patch_sha256"].append(digest))
        bad = self.assertProblem("B3 reuse")
        msgs = " ".join(c.message for c in bad)
        self.assertIn("C3", msgs)
        self.assertIn("Q3", msgs)
        with mock.patch.object(holdout_validate, "_b3_hashes",
                               return_value=(set(), set())):
            self.assertCheckOk("B3 reuse")


# ================================================================ output


class TestCliStructure(ValidateCase):

    def test_valid_skip_proofs_exit_0(self):
        proc = self.run_cli("--skip-proofs")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        ok = [l for l in proc.stdout.splitlines() if l.startswith("OK: ")]
        self.assertGreaterEqual(len(ok), 11)
        self.assertNotIn("PROBLEM:", proc.stdout)
        self.assertIn("OK: proofs: skipped (--skip-proofs)", proc.stdout)
        n = len({c.name for c in holdout_validate.validate_folder(
            self.folder, skip_proofs=True)})
        self.assertIn("OK: all %d checks passed" % n, proc.stdout)

    def test_removed_case_exit_1(self):
        shutil.rmtree(self.cdir("Q1"))
        proc = self.run_cli("--skip-proofs")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: slots: ", proc.stdout)

    def test_refuses_inside_claude_shell(self):
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        proc = self.run_cli("--skip-proofs", env=env)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stderr.strip(), holdout_kit.REFUSE_MSG)
        self.assertEqual(proc.stdout, "")

    def test_output_carries_no_case_content(self):
        self.edit("C1", "key.json",
                  lambda k: k.update(causal_failure_category="sql-thing",
                                     defect=""))
        self.edit("C3", "provenance.json",
                  lambda p: p["search"].update(screened=26))
        self.edit("Q1", "provenance.json",
                  lambda p: p.update(source_repo="/elsewhere/alpha"))
        diff = self.read_bytes("C1", "change.diff")
        self.write_bytes("Q2", "change.diff", diff)
        proc = self.run_cli("--skip-proofs")
        self.assertEqual(proc.returncode, 1)
        out = proc.stdout + proc.stderr
        self.assertIn("PROBLEM:", out)
        for secret in ("fixture defect text", "fixture causal text",
                       "fixture rationale", "fixture exposure",
                       "fixture rejection", 'value-C1-1-new', "sql-thing",
                       "/elsewhere", _TEMPLATE["root"], self.tmp,
                       "git log --no-merges"):
            self.assertNotIn(secret, out)


# ================================================================ shape


class TestModuleShape(unittest.TestCase):

    def _tree(self):
        with open(VALIDATE_PY, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_import_set_is_exact(self):
        self.assertEqual(_imports(self._tree()),
                         {"difflib", "os", "time", "holdout_kit"})

    def test_no_subprocess(self):
        tree = self._tree()
        self.assertNotIn("subprocess", _imports(tree))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        self.assertNotIn("subprocess", names)

    def test_every_run_argv_has_timeout(self):
        calls = [n for n in ast.walk(self._tree()) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "run_argv"]
        for call in calls:
            self.assertIn("timeout", {k.arg for k in call.keywords})

    def test_no_string_names_the_holdout(self):
        for n in ast.walk(self._tree()):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                self.assertNotIn(".vibe-check-holdout", n.value)

    def test_import_lock_can_trip(self):
        tree = ast.parse("import subprocess\nfrom os import path\n")
        self.assertEqual(_imports(tree), {"subprocess", "os"})

    def test_categories_verbatim(self):
        self.assertEqual(holdout_validate.CAUSAL_CATEGORIES, (
            "missing-input-validation", "missing-authz-check", "injection",
            "path-traversal", "unsafe-deserialization", "resource-exhaustion",
            "race-condition", "error-handling", "crypto-misuse",
            "info-disclosure", "logic-error", "other"))

    def test_required_field_tuples(self):
        self.assertIn("causal_failure_category",
                      holdout_validate.CATCH_KEY_KEYS)
        self.assertIn("exposure_check", holdout_validate.QUIET_KEY_KEYS)
        self.assertIn("selected_using_reviewer_output",
                      holdout_validate.PROVENANCE_KEYS)
        self.assertIn("runnable", holdout_validate.PROOF_RESULT_KEYS)


if __name__ == "__main__":
    unittest.main()
