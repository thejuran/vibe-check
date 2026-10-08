"""Tests for holdout_manifest — keyed hashes, the public seal manifest and the
checks that read it.

Locked here:
  * Per-case serialization is deterministic and content-sensitive; symlinks
    are refused.
  * The 256-bit HMAC key lives only at sealed/HMAC-KEY (0600); SEAL.json
    carries slots, keyed hashes and a SHA-256 commitment to the key, nothing
    else (public-shape checker, mutation-tested per injected leak).
  * The private inventory and rehash share ONE exclusion list, bound from
    holdout_kit.SEALED_PRIVATE (mutation-tested with a two-name list; an AST
    lock keeps the sentinel's name from being spelled out here).

Mutants follow the gitsnap convention: first show the real component sees the
difference, then patch it out and show the case is no longer caught.

`make_six_cases` is this file's own fixture: it writes a six-case tree with
placeholder content (the HMAC layer does not validate content) plus
sealed/SANDBOX-SENTINEL exactly as setup leaves the folder.
"""

import ast
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

import holdout_fixture  # noqa: E402
import holdout_kit  # noqa: E402
import holdout_manifest  # noqa: E402

KIT_PY = os.path.join(TOOLS_DIR, "holdout_kit.py")
MANIFEST_PY = os.path.join(TOOLS_DIR, "holdout_manifest.py")
REPO_NAME = "src-repo"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ID_ANY = re.compile(r"H-[0-9a-f]{8}")


# ================================================================ fixture


def _rev(*parts):
    return hashlib.sha1(("|".join(parts)).encode()).hexdigest()


def make_diff(path, removed, added, context=1, start=10):
    """A one-hunk git diff of `path` with `context` lines on each side."""
    pre = ["context before %d of %s" % (i, path) for i in range(context)]
    post = ["context after %d of %s" % (i, path) for i in range(context)]
    old_n = len(pre) + len(removed) + len(post)
    new_n = len(pre) + len(added) + len(post)
    lines = ["diff --git a/%s b/%s" % (path, path),
             "index 1111111..2222222 100644",
             "--- a/%s" % path, "+++ b/%s" % path,
             "@@ -%d,%d +%d,%d @@" % (start, old_n, start, new_n)]
    lines += [" " + ln for ln in pre]
    lines += ["-" + ln for ln in removed]
    lines += ["+" + ln for ln in added]
    lines += [" " + ln for ln in post]
    return "\n".join(lines) + "\n"


def default_diff(slot, context=1):
    return make_diff("src/%s.py" % slot.lower(),
                     ["value_%s = old_compute()" % slot.lower()],
                     ["value_%s = new_compute(%s)" % (slot.lower(),
                                                     slot.lower()),
                      "    return value_%s" % slot.lower()],
                     context=context)


def default_key(slot, tag="a"):
    if slot.startswith("C"):
        return {"slot": slot, "class": "catch",
                "defect": "defect %s %s" % (slot, tag),
                "location": {"file": "src/%s.py" % slot.lower(),
                             "line_start": 10, "line_end": 12},
                "causal_failure": "fails %s %s" % (slot, tag),
                "causal_failure_category": "missing-input-validation"}
    return {"slot": slot, "class": "quiet",
            "expected_quiet_rationale": "quiet %s %s" % (slot, tag),
            "supported_behavior": "holds %s %s" % (slot, tag),
            "exposure_check": "none %s %s" % (slot, tag)}


def default_provenance(slot, repo_name=REPO_NAME, tag="a", organic=True):
    prov = {"slot": slot, "kind": "organic" if organic else "constructed",
            "source_repo": "/Users/owner/%s" % repo_name,
            "repo_name": repo_name, "repo_in_b3": False,
            "selected_using_reviewer_output": False}
    if organic:
        prov["base_rev"] = _rev(repo_name, slot, tag, "base")
        prov["feature_rev"] = _rev(repo_name, slot, tag, "feature")
    else:
        prov["constructed_by"] = "owner"
    return prov


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(data, str):
        data = data.encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(data)


def write_case(folder, slot, case_id=None, diff=None, key=None,
               provenance=None, base=None):
    """Write one case (cases/<ID>/* and keys/<ID>/*); return its ID."""
    case_id = case_id or holdout_kit.new_case_id()
    sealed = os.path.join(folder, "sealed")
    cdir = os.path.join(sealed, "cases", case_id)
    kdir = os.path.join(sealed, "keys", case_id)
    _write(os.path.join(cdir, "case.json"),
           json.dumps({"id": case_id, "base": "base.tar",
                       "diff": "change.diff", "apply_with": "git apply"}))
    _write(os.path.join(cdir, "base.tar"),
           base if base is not None else b"base tree placeholder " + slot.encode())
    _write(os.path.join(cdir, "change.diff"),
           diff if diff is not None else default_diff(slot))
    _write(os.path.join(kdir, "key.json"),
           json.dumps(key if key is not None else default_key(slot),
                      sort_keys=True))
    _write(os.path.join(kdir, "provenance.json"),
           json.dumps(provenance if provenance is not None
                      else default_provenance(slot), sort_keys=True))
    _write(os.path.join(kdir, "proof", "run"),
           "#!/bin/sh\necho proof %s\n" % slot)
    _write(os.path.join(kdir, "proof-results.json"),
           json.dumps({"runnable": True, "base": {"exit": 0},
                       "changed": {"exit": 1}}))
    return case_id


def make_six_cases(folder):
    """Six placeholder cases + sealed/SANDBOX-SENTINEL; return {slot: ID}."""
    sealed = os.path.join(folder, "sealed")
    for sub in ("cases", "keys"):
        os.makedirs(os.path.join(sealed, sub), exist_ok=True)
    with open(os.path.join(sealed, holdout_kit.SENTINEL_NAME), "w",
              encoding="utf-8") as fh:
        fh.write(holdout_kit.SANDBOX_SENTINEL_TEXT)
    return {slot: write_case(folder, slot) for slot in holdout_kit.SLOTS}


def _clean_env():
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
    env.pop("CLAUDE_CONFIG_DIR", None)
    return mock.patch.dict(os.environ, env, clear=True)


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _strings(v)


def _imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module)
    return names


def _str_literals(tree):
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


class ManifestCase(unittest.TestCase):
    """Base: a realpath temp dir with a six-case holdout and a clean env."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self._env = _clean_env()
        self._env.start()
        self.folder = os.path.join(self.tmp, "holdout")
        self.ids = make_six_cases(self.folder)
        self.sealed = os.path.join(self.folder, "sealed")

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def p(self, *parts):
        return os.path.join(self.sealed, *parts)

    def seal_build(self):
        """Build and write SEAL.json + INVENTORY.json like `seal-build`."""
        seal = holdout_manifest.build_seal(self.folder)
        holdout_manifest.write_inventory(self.folder)
        holdout_kit.write_json_atomic(
            os.path.join(self.folder, "SEAL.json"), seal)
        return seal

    def cli(self, *args, env=None, stdin=None):
        return subprocess.run(
            [sys.executable, KIT_PY, *args], cwd=self.tmp,
            env=env if env is not None else holdout_fixture.kit_env(),
            input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=120)

    def run_inproc(self, argv, stdin=None):
        out, err = io.StringIO(), io.StringIO()
        patches = [mock.patch.object(sys, "stdout", out),
                   mock.patch.object(sys, "stderr", err)]
        if stdin is not None:
            patches.append(mock.patch.object(sys, "stdin", io.StringIO(stdin)))
        for p in patches:
            p.start()
        try:
            rc = holdout_kit.run(argv)
        finally:
            for p in reversed(patches):
                p.stop()
        return rc, out.getvalue(), err.getvalue()


# ================================================================ serialization


class TestSerialization(ManifestCase):

    def test_deterministic(self):
        cid = self.ids["C1"]
        a = holdout_manifest.case_serialization(self.folder, cid)
        b = holdout_manifest.case_serialization(self.folder, cid)
        self.assertEqual(a, b)
        self.assertIsInstance(a, bytes)

    def test_line_format_and_bytewise_sort(self):
        cid = self.ids["Q2"]
        data = holdout_manifest.case_serialization(self.folder, cid)
        lines = data.split(b"\n")
        self.assertEqual(lines[-1], b"")
        lines = lines[:-1]
        self.assertEqual(lines, sorted(lines))
        rels = [ln.split(b"\0")[0].decode() for ln in lines]
        self.assertEqual(rels[0], min(rels))
        self.assertIn("cases/%s/change.diff" % cid, rels)
        self.assertIn("keys/%s/proof/run" % cid, rels)
        for ln in lines:
            rel, digest = ln.split(b"\0")
            parts = rel.decode().split("/")
            self.assertIn(parts[0], ("cases", "keys"))
            with open(self.p(*parts), "rb") as fh:
                self.assertEqual(digest.decode(),
                                 hashlib.sha256(fh.read()).hexdigest())

    def test_one_byte_change_changes_serialization(self):
        cid = self.ids["C2"]
        before = holdout_manifest.case_serialization(self.folder, cid)
        path = self.p("keys", cid, "key.json")
        with open(path, "rb") as fh:
            old = fh.read()
        with open(path, "ab") as fh:
            fh.write(b" ")
        with open(path, "rb") as fh:
            self.assertNotEqual(fh.read(), old)
        self.assertNotEqual(
            holdout_manifest.case_serialization(self.folder, cid), before)

    def test_added_file_changes_serialization(self):
        cid = self.ids["C2"]
        before = holdout_manifest.case_serialization(self.folder, cid)
        extra = self.p("keys", cid, "extra.txt")
        _write(extra, "x")
        self.assertTrue(os.path.isfile(extra))
        self.assertNotEqual(
            holdout_manifest.case_serialization(self.folder, cid), before)

    def test_removed_file_changes_serialization(self):
        cid = self.ids["C2"]
        before = holdout_manifest.case_serialization(self.folder, cid)
        path = self.p("keys", cid, "proof-results.json")
        os.remove(path)
        self.assertFalse(os.path.exists(path))
        self.assertNotEqual(
            holdout_manifest.case_serialization(self.folder, cid), before)

    def test_symlink_refused(self):
        cid = self.ids["C3"]
        link = self.p("keys", cid, "proof-link")
        os.symlink(self.p("keys", cid, "proof"), link)
        self.assertTrue(os.path.islink(link))
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.case_serialization(self.folder, cid)

    def test_symlinked_proof_dir_refused(self):
        cid = self.ids["C3"]
        proof = self.p("keys", cid, "proof")
        shutil.move(proof, os.path.join(self.tmp, "elsewhere"))
        os.symlink(os.path.join(self.tmp, "elsewhere"), proof)
        self.assertTrue(os.path.islink(proof))
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.case_serialization(self.folder, cid)

    def test_missing_case_dir_refused(self):
        cid = self.ids["Q1"]
        shutil.rmtree(self.p("keys", cid))
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.case_serialization(self.folder, cid)

    def test_serialization_carries_no_other_case(self):
        cid = self.ids["C1"]
        data = holdout_manifest.case_serialization(self.folder, cid)
        for other in self.ids.values():
            if other != cid:
                self.assertNotIn(other.encode(), data)


# ================================================================ key


class TestKey(ManifestCase):

    def test_creates_key_0600(self):
        path = self.p("HMAC-KEY")
        self.assertFalse(os.path.exists(path))
        key = holdout_manifest.load_or_create_key(self.folder)
        self.assertEqual(len(key), 32)
        with open(path, encoding="ascii") as fh:
            text = fh.read().strip()
        self.assertTrue(HEX64.match(text))
        self.assertEqual(bytes.fromhex(text), key)
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)

    def test_second_call_returns_same_key(self):
        a = holdout_manifest.load_or_create_key(self.folder)
        b = holdout_manifest.load_or_create_key(self.folder)
        self.assertEqual(a, b)
        leftovers = [n for n in os.listdir(self.sealed) if n.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def test_malformed_key_refused(self):
        _write(self.p("HMAC-KEY"), "ab" * 31 + "\n")
        with self.assertRaises(holdout_kit.KitError) as ctx:
            holdout_manifest.load_or_create_key(self.folder)
        self.assertIn("HMAC key file is malformed", str(ctx.exception))

    def test_symlinked_key_refused(self):
        target = os.path.join(self.tmp, "key-elsewhere")
        _write(target, "ab" * 32 + "\n")
        os.symlink(target, self.p("HMAC-KEY"))
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.load_or_create_key(self.folder)

    def test_different_keys_different_hmac(self):
        cid = self.ids["C1"]
        k1, k2 = b"\x01" * 32, b"\x02" * 32
        self.assertNotEqual(holdout_manifest.case_hmac(k1, self.folder, cid),
                            holdout_manifest.case_hmac(k2, self.folder, cid))
        self.assertEqual(holdout_manifest.case_hmac(k1, self.folder, cid),
                         holdout_manifest.case_hmac(k1, self.folder, cid))

    def test_hmac_is_hmac_sha256_of_serialization(self):
        import hmac as _hmac
        cid = self.ids["Q3"]
        key = b"\x07" * 32
        expect = _hmac.new(key, holdout_manifest.case_serialization(
            self.folder, cid), hashlib.sha256).hexdigest()
        self.assertEqual(holdout_manifest.case_hmac(key, self.folder, cid),
                         expect)


# ================================================================ build_seal


class TestBuildSeal(ManifestCase):

    def test_shape_and_slots(self):
        seal = holdout_manifest.build_seal(self.folder)
        self.assertEqual(holdout_manifest.public_shape_problems(seal), [])
        self.assertEqual(len(seal["cases"]), 6)
        self.assertEqual(sorted(v["slot"] for v in seal["cases"].values()),
                         sorted(holdout_kit.SLOTS))
        self.assertEqual(set(seal), holdout_manifest.PUBLIC_KEYS
                         - {"archive_sha256"})
        self.assertEqual(seal["schema"], holdout_manifest.SEAL_SCHEMA)
        self.assertEqual(seal["status"], "sealed")
        self.assertEqual(seal["milestone"], "v2.12")
        for cid, entry in seal["cases"].items():
            self.assertEqual(set(entry), holdout_manifest.CASE_KEYS)
            self.assertEqual(self.ids[entry["slot"]], cid)

    def test_key_commitment(self):
        seal = holdout_manifest.build_seal(self.folder)
        key = holdout_manifest.load_or_create_key(self.folder)
        self.assertEqual(seal["key_commitment_sha256"],
                         hashlib.sha256(key).hexdigest())

    def test_case_hmac_matches(self):
        seal = holdout_manifest.build_seal(self.folder)
        key = holdout_manifest.load_or_create_key(self.folder)
        for cid, entry in seal["cases"].items():
            self.assertEqual(entry["hmac"],
                             holdout_manifest.case_hmac(key, self.folder, cid))

    def test_no_identifying_strings(self):
        seal = holdout_manifest.build_seal(self.folder)
        mac = seal["mac"]
        self.assertEqual(mac, holdout_manifest.MAC_DESCRIPTION)
        for s in _strings(seal):
            if s == mac:
                continue
            self.assertNotIn(REPO_NAME, s)
            self.assertNotIn("/", s)
            self.assertIsNone(re.fullmatch(r"[0-9a-f]{40}", s), s)
            self.assertIsNone(re.search(r"\d{4}-\d{2}-\d{2}", s), s)
            self.assertNotIn(".json", s)
            self.assertNotIn(".diff", s)
        self.assertNotIn(REPO_NAME, json.dumps(seal))

    def test_deterministic_across_builds(self):
        a = holdout_manifest.build_seal(self.folder)
        b = holdout_manifest.build_seal(self.folder)
        self.assertEqual(a, b)

    def test_missing_slot_refused(self):
        shutil.rmtree(self.p("cases", self.ids["Q3"]))
        shutil.rmtree(self.p("keys", self.ids["Q3"]))
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.build_seal(self.folder)

    def test_duplicate_slot_refused(self):
        cid = self.ids["Q3"]
        _write(self.p("keys", cid, "key.json"),
               json.dumps(default_key("Q2")))
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.build_seal(self.folder)

    def test_orphan_key_dir_refused(self):
        os.makedirs(self.p("keys", "H-0000aaaa"))
        _write(self.p("keys", "H-0000aaaa", "key.json"), "{}")
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.build_seal(self.folder)

    def test_build_seal_carries_no_inventory(self):
        seal = holdout_manifest.build_seal(self.folder)
        inv = holdout_manifest.write_inventory(self.folder)
        dumped = json.dumps(seal)
        for rel in inv["files"]:
            self.assertNotIn(rel, dumped)
        self.assertNotIn("inventory", dumped.lower())


# ================================================================ inventory


class TestInventory(ManifestCase):

    def test_inventory_lists_every_content_file(self):
        holdout_manifest.load_or_create_key(self.folder)
        inv = holdout_manifest.write_inventory(self.folder)
        with open(self.p("INVENTORY.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), inv)
        content = [r for r in holdout_kit.walk_regular(self.sealed)
                   if r.startswith(("cases/", "keys/"))]
        self.assertEqual(sorted(inv["files"]), sorted(content))
        for rel, digest in inv["files"].items():
            self.assertEqual(digest, holdout_kit.sha256_file(
                self.p(*rel.split("/"))))

    def test_inventory_includes_stray_top_level_file(self):
        _write(self.p("stray.txt"), "x")
        inv = holdout_manifest.write_inventory(self.folder)
        self.assertIn("stray.txt", inv["files"])


class TestSealedPrivate(ManifestCase):

    def test_private_names_bound_from_kit(self):
        self.assertEqual(holdout_manifest._private_names,
                         holdout_kit.SEALED_PRIVATE)
        self.assertIs(holdout_manifest._private_names,
                      holdout_kit.SEALED_PRIVATE)

    def test_sentinel_excluded(self):
        self.assertTrue(os.path.isfile(self.p(holdout_kit.SENTINEL_NAME)))
        self.seal_build()
        with open(self.p("INVENTORY.json"), encoding="utf-8") as fh:
            files = json.load(fh)["files"]
        for name in holdout_kit.SEALED_PRIVATE:
            self.assertNotIn(name, files)
        for cid in self.ids.values():
            self.assertIn("cases/%s/change.diff" % cid, files)
            self.assertIn("keys/%s/key.json" % cid, files)
            data = holdout_manifest.case_serialization(self.folder, cid)
            self.assertNotIn(holdout_kit.SENTINEL_NAME.encode(), data)

    def test_mutant_two_name_list_inventories_sentinel(self):
        self.assertTrue(os.path.isfile(self.p(holdout_kit.SENTINEL_NAME)))
        with mock.patch.object(holdout_manifest, "_private_names",
                               ("HMAC-KEY", "INVENTORY.json")):
            inv = holdout_manifest.write_inventory(self.folder)
        self.assertIn(holdout_kit.SENTINEL_NAME, inv["files"])

    def test_no_sentinel_literal_in_module(self):
        with open(MANIFEST_PY, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        self.assertNotIn("SANDBOX-SENTINEL", _str_literals(tree))
        self.assertTrue(any("SEALED_PRIVATE" in getattr(n, "attr", "")
                            for n in ast.walk(tree)))

    def test_literal_lock_can_trip(self):
        tree = ast.parse("x = ('HMAC-KEY', 'SANDBOX-SENTINEL')\n")
        self.assertIn("SANDBOX-SENTINEL", _str_literals(tree))


# ================================================================ public shape


class TestPublicShape(ManifestCase):

    def setUp(self):
        super().setUp()
        self.good = holdout_manifest.build_seal(self.folder)
        self.assertEqual(holdout_manifest.public_shape_problems(self.good), [])

    def bad(self):
        return json.loads(json.dumps(self.good))

    def assertProblem(self, seal, fragment):
        problems = holdout_manifest.public_shape_problems(seal)
        self.assertTrue(any(fragment in p for p in problems),
                        (fragment, problems))

    def test_archive_sha256_allowed(self):
        seal = self.bad()
        seal["archive_sha256"] = "a" * 64
        self.assertEqual(holdout_manifest.public_shape_problems(seal), [])

    def test_archive_sha256_format(self):
        seal = self.bad()
        seal["archive_sha256"] = "a" * 63
        self.assertProblem(seal, "hash format")

    def test_extra_top_level_key(self):
        seal = self.bad()
        seal["repo"] = REPO_NAME
        self.assertProblem(seal, "unexpected key: repo")

    def test_missing_top_level_key(self):
        seal = self.bad()
        del seal["key_commitment_sha256"]
        self.assertProblem(seal, "missing key")

    def test_case_extra_key(self):
        seal = self.bad()
        cid = self.ids["C1"]
        seal["cases"][cid]["repo_name"] = REPO_NAME
        self.assertProblem(seal, "case %s: unexpected key" % cid)

    def test_non_opaque_id(self):
        seal = self.bad()
        cid = self.ids["C1"]
        seal["cases"]["C1-triggarr"] = seal["cases"].pop(cid)
        self.assertProblem(seal, "opaque id")
        problems = holdout_manifest.public_shape_problems(seal)
        self.assertFalse(any("triggarr" in p for p in problems))

    def test_duplicate_slot(self):
        seal = self.bad()
        seal["cases"][self.ids["C2"]]["slot"] = "C1"
        self.assertProblem(seal, "slots")

    def test_seventh_case(self):
        seal = self.bad()
        seal["cases"]["H-0000beef"] = {"slot": "C1", "hmac": "b" * 64}
        self.assertProblem(seal, "slots")

    def test_hmac_length(self):
        seal = self.bad()
        seal["cases"][self.ids["Q1"]]["hmac"] = "c" * 63
        self.assertProblem(seal, "hash format")

    def test_uppercase_hash(self):
        seal = self.bad()
        seal["key_commitment_sha256"] = "C" * 64
        self.assertProblem(seal, "hash format")

    def test_mac_description(self):
        seal = self.bad()
        seal["mac"] = "2026-10-08"
        self.assertProblem(seal, "mac description")

    def test_too_large(self):
        seal = self.bad()
        seal["padding"] = "x" * 20000
        self.assertProblem(seal, "too large")

    def test_status(self):
        seal = self.bad()
        seal["status"] = "draft"
        self.assertProblem(seal, "status")

    def test_schema_and_milestone(self):
        seal = self.bad()
        seal["schema"] = "other/1"
        seal["milestone"] = "v2.11"
        self.assertProblem(seal, "schema")
        self.assertProblem(seal, "milestone")

    def test_case_value_not_object(self):
        seal = self.bad()
        seal["cases"][self.ids["Q2"]] = "Q2"
        self.assertProblem(seal, "case %s" % self.ids["Q2"])

    def test_not_an_object(self):
        self.assertTrue(holdout_manifest.public_shape_problems([]))


# ================================================================ CLI seal-build


class TestCliSealBuild(ManifestCase):

    def test_seal_build_cli(self):
        proc = self.cli("--folder", self.folder, "seal-build")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(),
                         "OK: seal manifest built: 6 cases, key commitment "
                         "recorded")
        with open(os.path.join(self.folder, "SEAL.json")) as fh:
            seal = json.load(fh)
        self.assertNotIn("archive_sha256", seal)
        self.assertEqual(holdout_manifest.public_shape_problems(seal), [])
        self.assertTrue(os.path.isfile(self.p("INVENTORY.json")))
        self.assertEqual(stat.S_IMODE(os.stat(self.p("HMAC-KEY")).st_mode),
                         0o600)

    def test_seal_build_refuses_under_claudecode(self):
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        proc = self.cli("--folder", self.folder, "seal-build", env=env)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stderr, holdout_kit.REFUSE_MSG + "\n")
        self.assertFalse(os.path.exists(os.path.join(self.folder,
                                                     "SEAL.json")))

    def test_seal_build_requires_folder(self):
        rc, _, err = self.run_inproc(["seal-build"])
        self.assertEqual(rc, 2)
        self.assertIn("--folder", err)


# ================================================================ module shape


class TestModuleShape(unittest.TestCase):

    def _tree(self):
        with open(MANIFEST_PY, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_import_set_is_exact(self):
        self.assertEqual(_imports(self._tree()),
                         {"hashlib", "hmac", "json", "os", "re", "secrets",
                          "shutil", "stat", "sys", "time", "holdout_kit"})

    def test_no_subprocess(self):
        tree = self._tree()
        self.assertNotIn("subprocess", _imports(tree))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        self.assertNotIn("subprocess", names)

    def test_import_lock_can_trip(self):
        tree = ast.parse("import subprocess\nfrom os import path\n")
        self.assertEqual(_imports(tree), {"subprocess", "os"})

    def test_no_argparse_default_names_holdout(self):
        for s in _str_literals(self._tree()):
            self.assertNotIn(".vibe-check-holdout", s)

    def test_token_bytes_32_once(self):
        with open(MANIFEST_PY, encoding="utf-8") as fh:
            self.assertEqual(fh.read().count("token_bytes(32)"), 1)

    def test_commands_registered(self):
        for name in ("seal-build", "rehash", "extract", "seal-order",
                     "publish", "retire", "resume-check"):
            self.assertEqual(holdout_kit.COMMANDS[name], "holdout_manifest")

    def test_exports(self):
        for name in ("case_serialization", "case_hmac", "build_seal",
                     "write_inventory", "load_or_create_key",
                     "public_shape_problems", "add_parser", "cmd",
                     "SEAL_SCHEMA", "PUBLIC_KEYS", "CASE_KEYS",
                     "MAC_DESCRIPTION", "SEAL_RELPATH"):
            self.assertTrue(hasattr(holdout_manifest, name), name)


if __name__ == "__main__":
    unittest.main()
