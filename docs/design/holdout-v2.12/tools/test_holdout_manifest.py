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
            if s in (mac, holdout_manifest.SEAL_SCHEMA):
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


class TestRegistryEntry(ManifestCase):
    """sealed/keys/xcheck-workspaces.json (the cross-check workspace
    registry) is not a case: build_seal skips it, the inventory lists it."""

    def _write_registry(self):
        path = self.p("keys", holdout_kit.XCHECK_REGISTRY)
        holdout_kit.write_json_atomic(path, {"generations": []})
        return path

    def test_build_seal_skips_registry(self):
        self._write_registry()
        seal = holdout_manifest.build_seal(self.folder)
        self.assertEqual(sorted(seal["cases"]), sorted(self.ids.values()))

    def test_registry_in_inventory_not_in_any_case(self):
        self._write_registry()
        seal = self.seal_build()
        inv = holdout_kit.load_json(self.p("INVENTORY.json"))
        self.assertIn("keys/" + holdout_kit.XCHECK_REGISTRY, inv["files"])
        for cid in seal["cases"]:
            self.assertNotIn(
                holdout_kit.XCHECK_REGISTRY.encode(),
                holdout_manifest.case_serialization(self.folder, cid))

    def test_registry_directory_is_not_skipped(self):
        os.makedirs(self.p("keys", holdout_kit.XCHECK_REGISTRY))
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.build_seal(self.folder)

    def test_other_stray_file_still_refused(self):
        with open(self.p("keys", "notes.json"), "w") as fh:
            fh.write("{}\n")
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.build_seal(self.folder)


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


# ================================================================ rehash


def _flip_byte(path):
    with open(path, "rb") as fh:
        data = bytearray(fh.read())
    data[0] ^= 0x01
    with open(path, "wb") as fh:
        fh.write(bytes(data))


class SealedCase(ManifestCase):
    """A six-case holdout after seal-build."""

    def setUp(self):
        super().setUp()
        self.seal = self.seal_build()
        self.seal_path = os.path.join(self.folder, "SEAL.json")

    def rehash(self):
        return holdout_manifest.rehash_folder(self.seal_path, self.sealed)


class TestRehash(SealedCase):

    def test_untouched_tree_is_clean(self):
        self.assertTrue(os.path.isfile(self.p(holdout_kit.SENTINEL_NAME)))
        r = self.rehash()
        self.assertTrue(r["ok"])
        self.assertTrue(r["commitment_ok"])
        self.assertEqual(r["cases"], {cid: True for cid in self.ids.values()})
        for key in ("mismatched", "missing", "extra", "missing_cases",
                    "extra_cases"):
            self.assertEqual(r[key], [], key)

    def test_cli_clean(self):
        with open(self.p("INVENTORY.json")) as fh:
            n = len(json.load(fh)["files"])
        proc = self.cli("--folder", self.folder, "rehash", "--seal",
                        self.seal_path, "--sealed", self.sealed)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(proc.stdout.strip(),
                         "OK: all 6 cases match the seal; key commitment "
                         "verified; %d files in inventory" % n)

    def test_sentinel_deleted_still_clean(self):
        os.remove(self.p(holdout_kit.SENTINEL_NAME))
        self.assertTrue(self.rehash()["ok"])

    def test_private_names_mutant_reports_sentinel(self):
        self.assertTrue(self.rehash()["ok"])
        with mock.patch.object(holdout_manifest, "_private_names",
                               ("HMAC-KEY", "INVENTORY.json")):
            r = self.rehash()
        self.assertFalse(r["ok"])
        self.assertEqual(r["extra"], [holdout_kit.SENTINEL_NAME])

    def test_byte_flip(self):
        cid = self.ids["C2"]
        self.assertTrue(self.rehash()["ok"])
        _flip_byte(self.p("keys", cid, "key.json"))
        r = self.rehash()
        self.assertFalse(r["ok"])
        self.assertFalse(r["cases"][cid])
        self.assertEqual(sum(1 for v in r["cases"].values() if not v), 1)
        self.assertEqual(r["mismatched"], ["keys/%s/key.json" % cid])
        proc = self.cli("--folder", self.folder, "rehash", "--seal",
                        self.seal_path, "--sealed", self.sealed)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: 1 case(s) differ from the seal", proc.stdout)

    def test_byte_flip_mutant_case_hmac(self):
        cid = self.ids["C2"]
        _flip_byte(self.p("keys", cid, "key.json"))
        self.assertFalse(self.rehash()["cases"][cid])
        stored = {k: v["hmac"] for k, v in self.seal["cases"].items()}
        with mock.patch.object(holdout_manifest, "case_hmac",
                               lambda key, folder, c: stored[c]):
            self.assertTrue(self.rehash()["cases"][cid])

    def test_missing_file(self):
        cid = self.ids["Q1"]
        self.assertTrue(self.rehash()["ok"])
        os.remove(self.p("keys", cid, "proof-results.json"))
        r = self.rehash()
        self.assertFalse(r["ok"])
        self.assertEqual(r["missing"], ["keys/%s/proof-results.json" % cid])
        self.assertFalse(r["cases"][cid])

    def test_extra_file(self):
        cid = self.ids["Q2"]
        self.assertTrue(self.rehash()["ok"])
        _write(self.p("keys", cid, "extra.txt"), "x")
        r = self.rehash()
        self.assertFalse(r["ok"])
        self.assertEqual(r["extra"], ["keys/%s/<file>" % cid])
        self.assertFalse(r["cases"][cid])

    def test_wrong_key(self):
        self.assertTrue(self.rehash()["ok"])
        _write(self.p("HMAC-KEY"), (b"\x05" * 32).hex() + "\n")
        r = self.rehash()
        self.assertFalse(r["ok"])
        self.assertFalse(r["commitment_ok"])
        self.assertFalse(any(r["cases"].values()))
        proc = self.cli("--folder", self.folder, "rehash", "--seal",
                        self.seal_path, "--sealed", self.sealed)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: the HMAC key does not match the committed key",
                      proc.stdout)

    def test_key_missing(self):
        os.remove(self.p("HMAC-KEY"))
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.rehash()
        self.assertIn("HMAC key missing", str(ctx.exception))
        proc = self.cli("--folder", self.folder, "rehash", "--seal",
                        self.seal_path, "--sealed", self.sealed)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: HMAC key missing", proc.stdout)

    def test_symlink_refused(self):
        cid = self.ids["C3"]
        link = self.p("cases", cid, "link")
        os.symlink(self.p("cases", cid, "change.diff"), link)
        self.assertTrue(os.path.islink(link))
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.rehash()
        self.assertIn("symlink refused", str(ctx.exception))
        proc = self.cli("--folder", self.folder, "rehash", "--seal",
                        self.seal_path, "--sealed", self.sealed)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: symlink refused", proc.stdout)

    def test_seal_id_not_in_folder(self):
        old = self.ids["C1"]
        seal = json.loads(json.dumps(self.seal))
        seal["cases"]["H-0000beef"] = seal["cases"].pop(old)
        holdout_kit.write_json_atomic(self.seal_path, seal)
        r = self.rehash()
        self.assertFalse(r["ok"])
        self.assertFalse(r["cases"]["H-0000beef"])
        self.assertEqual(r["missing_cases"], ["H-0000beef"])
        self.assertEqual(r["extra_cases"], [old])

    def test_case_dir_not_in_seal(self):
        new = write_case(self.folder, "C1", case_id="H-0000cafe")
        r = self.rehash()
        self.assertFalse(r["ok"])
        self.assertEqual(r["extra_cases"], [new])
        self.assertTrue(r["extra"])

    def test_seventh_case_in_seal_refused(self):
        seal = json.loads(json.dumps(self.seal))
        seal["cases"]["H-0000beef"] = {"slot": "C1", "hmac": "b" * 64}
        holdout_kit.write_json_atomic(self.seal_path, seal)
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.rehash()
        self.assertIn("public shape", str(ctx.exception))

    def test_archive_sha256_present_is_fine(self):
        seal = json.loads(json.dumps(self.seal))
        seal["archive_sha256"] = "d" * 64
        holdout_kit.write_json_atomic(self.seal_path, seal)
        self.assertTrue(self.rehash()["ok"])

    def test_inventory_missing(self):
        os.remove(self.p("INVENTORY.json"))
        with self.assertRaises(holdout_kit.KitError):
            self.rehash()

    def test_sealed_must_be_named_sealed(self):
        other = os.path.join(self.tmp, "copy")
        shutil.copytree(self.sealed, other)
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.rehash_folder(self.seal_path, other)

    def test_output_never_names_repo(self):
        cid = self.ids["Q3"]
        _write(self.p("keys", cid, REPO_NAME + "-notes.txt"), "x")
        _write(self.p(REPO_NAME + ".txt"), "x")
        proc = self.cli("--folder", self.folder, "rehash", "--seal",
                        self.seal_path, "--sealed", self.sealed)
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn(REPO_NAME, proc.stdout + proc.stderr)
        for ln in proc.stdout.splitlines():
            for tok in re.findall(r"[A-Za-z0-9_.<>-]+(?:/[A-Za-z0-9_.<>-]+)+",
                                  ln):
                for part in tok.split("/"):
                    self.assertTrue(
                        part in ("cases", "keys", "proof", "run", "<file>")
                        or part in holdout_kit.CASE_FILES
                        or part in holdout_kit.KEY_FILES
                        or ID_ANY.fullmatch(part), (part, ln))


class TestRehashSetupFolder(unittest.TestCase):
    """seal-build + rehash on a folder made by the real `setup`."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self._env = _clean_env()
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def test_setup_folder_rehashes_clean(self):
        folder = holdout_fixture.make_fake_holdout(self.tmp)
        sealed = os.path.join(folder, "sealed")
        self.assertTrue(os.path.isfile(os.path.join(
            sealed, holdout_kit.SENTINEL_NAME)))
        make_six_cases(folder)
        seal = holdout_manifest.build_seal(folder)
        holdout_manifest.write_inventory(folder)
        seal_path = os.path.join(folder, "SEAL.json")
        holdout_kit.write_json_atomic(seal_path, seal)
        r = holdout_manifest.rehash_folder(seal_path, sealed)
        self.assertEqual(r["extra"], [])
        self.assertTrue(r["ok"])
        with mock.patch.object(holdout_manifest, "_private_names",
                               ("HMAC-KEY", "INVENTORY.json")):
            r = holdout_manifest.rehash_folder(seal_path, sealed)
        self.assertEqual(r["extra"], [holdout_kit.SENTINEL_NAME])
        self.assertFalse(r["ok"])


# ================================================================ extract


class TestExtract(SealedCase):

    def test_cases_only(self):
        dest = os.path.join(self.tmp, "runner")
        n = holdout_manifest.extract_part(self.sealed, "cases", dest)
        self.assertTrue(os.path.isdir(os.path.join(dest, "cases")))
        self.assertFalse(os.path.exists(os.path.join(dest, "keys")))
        got = holdout_kit.walk_regular(dest)
        self.assertEqual(n, len(got))
        self.assertTrue(all(r.startswith("cases/") for r in got))
        self.assertEqual(got, [r for r in holdout_kit.walk_regular(self.sealed)
                               if r.startswith("cases/")])

    def test_keys_only(self):
        dest = os.path.join(self.tmp, "scorer")
        n = holdout_manifest.extract_part(self.sealed, "keys", dest)
        self.assertFalse(os.path.exists(os.path.join(dest, "cases")))
        got = holdout_kit.walk_regular(dest)
        self.assertEqual(n, len(got))
        self.assertTrue(all(r.startswith("keys/") for r in got))
        self.assertFalse(any(holdout_kit.SENTINEL_NAME in r for r in got))

    def test_both_refused(self):
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.extract_part(self.sealed, "both",
                                          os.path.join(self.tmp, "d"))

    def test_symlink_refused(self):
        cid = self.ids["C1"]
        os.symlink(self.p("cases", cid, "change.diff"),
                   self.p("cases", cid, "link"))
        dest = os.path.join(self.tmp, "d")
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.extract_part(self.sealed, "cases", dest)
        self.assertFalse(os.path.exists(os.path.join(dest, "cases")))

    def test_existing_dest_part_refused(self):
        dest = os.path.join(self.tmp, "d")
        os.makedirs(os.path.join(dest, "cases"))
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.extract_part(self.sealed, "cases", dest)

    def test_cli_extract(self):
        dest = os.path.join(self.tmp, "d")
        proc = self.cli("--folder", self.folder, "extract", "--part", "keys",
                        "--dest", dest)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("OK: extracted keys/"))
        self.assertTrue(os.path.isdir(os.path.join(dest, "keys")))
        self.assertFalse(os.path.exists(os.path.join(dest, "cases")))

    def test_cli_extract_both_is_usage_error(self):
        proc = self.cli("--folder", self.folder, "extract", "--part", "both",
                        "--dest", os.path.join(self.tmp, "d"))
        self.assertEqual(proc.returncode, 2)


# ================================================================ seal-order


class TestSealOrder(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self.repo = holdout_fixture.make_repo(self.tmp)
        holdout_fixture.write(self.repo, "README", "x\n")
        self.commit("init")
        self.env = mock.patch.dict(os.environ, holdout_fixture.helper_env(),
                                   clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self._tmp.cleanup()

    def commit(self, msg):
        holdout_fixture.git(self.repo, "add", "-A")
        holdout_fixture.git(self.repo, "commit", "-q", "-m", msg)
        return holdout_fixture.git(self.repo, "rev-parse",
                                   "HEAD").stdout.strip()

    def write_seal(self, text="{}\n"):
        holdout_fixture.write(self.repo, holdout_manifest.SEAL_RELPATH, text)

    def test_no_commit(self):
        self.assertEqual(holdout_manifest.seal_order_problems(self.repo),
                         ["SEAL.json has no commit"])

    def test_one_commit(self):
        self.write_seal()
        self.commit("seal")
        self.assertEqual(holdout_manifest.seal_order_problems(self.repo), [])

    def test_two_commits(self):
        self.write_seal()
        self.commit("seal")
        self.write_seal("{ }\n")
        self.commit("edit")
        self.assertEqual(holdout_manifest.seal_order_problems(self.repo),
                         ["SEAL.json has 2 commits; expected exactly 1"])

    def test_edit_on_other_branch_counts(self):
        self.write_seal()
        self.commit("seal")
        holdout_fixture.git(self.repo, "checkout", "-q", "-b", "side")
        self.write_seal("{\"x\": 1}\n")
        self.commit("side edit")
        holdout_fixture.git(self.repo, "checkout", "-q", "main")
        self.assertEqual(holdout_manifest.seal_order_problems(self.repo),
                         ["SEAL.json has 2 commits; expected exactly 1"])

    def test_before_descendant(self):
        self.write_seal()
        self.commit("seal")
        holdout_fixture.write(self.repo, "later.txt", "x\n")
        later = self.commit("53-01 tuning")
        self.assertEqual(holdout_manifest.seal_order_problems(
            self.repo, before=later), [])

    def test_before_not_descendant(self):
        base = holdout_fixture.git(self.repo, "rev-parse",
                                   "HEAD").stdout.strip()
        self.write_seal()
        self.commit("seal")
        holdout_fixture.git(self.repo, "checkout", "-q", "-b", "early", base)
        holdout_fixture.write(self.repo, "early.txt", "x\n")
        early = self.commit("53-01 tuning before the seal")
        self.assertEqual(holdout_manifest.seal_order_problems(
            self.repo, before=early),
            ["seal commit is not an ancestor of %s" % early])

    def test_before_unknown_rev(self):
        self.write_seal()
        self.commit("seal")
        problems = holdout_manifest.seal_order_problems(self.repo,
                                                        before="no-such-rev")
        self.assertEqual(len(problems), 1)
        self.assertIn("no-such-rev", problems[0])

    def test_not_a_repo(self):
        problems = holdout_manifest.seal_order_problems(
            os.path.join(self.tmp, "nothing"))
        self.assertEqual(len(problems), 1)

    def test_cli_works_under_claudecode(self):
        self.write_seal()
        self.commit("seal")
        env = holdout_fixture.helper_env()
        env["CLAUDECODE"] = "1"
        env.pop("CLAUDE_CONFIG_DIR", None)
        proc = subprocess.run([sys.executable, KIT_PY, "seal-order", "--repo",
                               self.repo], env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith(
            "OK: SEAL.json has exactly one commit"))

    def test_cli_problem(self):
        proc = subprocess.run([sys.executable, KIT_PY, "seal-order", "--repo",
                               self.repo], env=holdout_fixture.kit_env(),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=120)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout.strip(),
                         "PROBLEM: SEAL.json has no commit")


# ================================================================ leak ledger


def write_ledger(folder, scans):
    holdout_kit.write_json_atomic(
        os.path.join(folder, holdout_manifest.LEAKSCAN_RELPATH),
        {"schema": holdout_manifest.LEAKSCAN_SCHEMA, "scans": scans})


def scan_entry(folder, hits=0, ids=(), slots=(), at="2026-10-08T10:00:00Z",
               seal_sha=None):
    seal_path = os.path.join(folder, "SEAL.json")
    if seal_sha is None and os.path.isfile(seal_path):
        seal_sha = holdout_kit.sha256_file(seal_path)
    return {"at": at, "seal_sha256": seal_sha, "probes": 40, "hits": hits,
            "hit_case_ids": list(ids), "hit_slots": list(slots)}


NO_SCAN = "no leak scan recorded; run leakscan before publish"
FOUND = ("the last leak scan found holdout text on the tuning side; replace "
         "the slots it named, re-seal, and scan again")
PREDATES = "the last leak scan predates the current seal; run leakscan again"


def not_replaced(slot, cid, at):
    return ("case %s (%s) was named by a leak scan on %s and has not been "
            "replaced; deleting the matched files is cleanup, not a remedy: "
            "replace the slot through the finder and a fresh cross-check, "
            "then re-seal" % (slot, cid, at))


class TestLeakLedger(SealedCase):

    def problems(self):
        return holdout_manifest.leak_ledger_problems(self.folder, self.seal)

    def test_no_ledger(self):
        self.assertEqual(self.problems(), [NO_SCAN])

    def test_clean(self):
        write_ledger(self.folder, [scan_entry(self.folder)])
        self.assertEqual(self.problems(), [])

    def test_last_scan_hits(self):
        cid = self.ids["Q1"]
        write_ledger(self.folder, [scan_entry(self.folder, hits=2, ids=[cid],
                                              slots=["Q1"])])
        self.assertIn(FOUND, self.problems())

    def test_predates_current_seal(self):
        write_ledger(self.folder, [scan_entry(self.folder)])
        self.assertEqual(self.problems(), [])
        with open(self.p("keys", self.ids["C1"], "key.json"), "ab") as fh:
            fh.write(b" ")
        self.seal = self.seal_build()
        self.assertEqual(self.problems(), [PREDATES])

    def test_null_seal_sha(self):
        entry = scan_entry(self.folder)
        entry["seal_sha256"] = None
        write_ledger(self.folder, [entry])
        self.assertEqual(self.problems(), [PREDATES])

    def test_codex_case_clean_rescan_does_not_clear(self):
        cid = self.ids["C2"]
        at = "2026-10-08T09:00:00Z"
        write_ledger(self.folder, [
            scan_entry(self.folder, hits=1, ids=[cid], slots=["C2"], at=at),
            scan_entry(self.folder, at="2026-10-08T11:00:00Z")])
        self.assertEqual(self.problems(), [not_replaced("C2", cid, at)])

    def test_replaced_slot_clears(self):
        cid = self.ids["C2"]
        at = "2026-10-08T09:00:00Z"
        first = scan_entry(self.folder, hits=1, ids=[cid], slots=["C2"],
                           at=at)
        shutil.rmtree(self.p("cases", cid))
        shutil.rmtree(self.p("keys", cid))
        write_case(self.folder, "C2",
                   diff=default_diff("C2").replace("new_compute",
                                                   "fresh_compute"),
                   key=default_key("C2", tag="b"),
                   provenance=default_provenance("C2", tag="b"))
        self.seal = self.seal_build()
        self.assertNotIn(cid, self.seal["cases"])
        write_ledger(self.folder, [first, scan_entry(self.folder)])
        self.assertEqual(self.problems(), [])

    def test_malformed_ledger(self):
        path = os.path.join(self.folder, holdout_manifest.LEAKSCAN_RELPATH)
        for body in ([], {"schema": holdout_manifest.LEAKSCAN_SCHEMA},
                     {"schema": "other/1", "scans": [scan_entry(self.folder)]},
                     {"schema": holdout_manifest.LEAKSCAN_SCHEMA, "scans": []},
                     {"schema": holdout_manifest.LEAKSCAN_SCHEMA,
                      "scans": [{"hits": "0"}]}):
            with open(path, "w") as fh:
                json.dump(body, fh)
            self.assertEqual(self.problems(), [NO_SCAN], body)
        with open(path, "w") as fh:
            fh.write("not json")
        self.assertEqual(self.problems(), [NO_SCAN])


# ================================================================ publish


class TestPublish(SealedCase):

    def setUp(self):
        super().setUp()
        self.repo = holdout_fixture.make_repo(self.tmp)
        self.dest = os.path.join(self.repo,
                                 *holdout_manifest.SEAL_RELPATH.split("/"))

    def test_clean_ledger_publishes(self):
        write_ledger(self.folder, [scan_entry(self.folder)])
        dest = holdout_manifest.publish(self.folder, self.repo)
        self.assertEqual(dest, self.dest)
        with open(dest, "rb") as a, open(self.seal_path, "rb") as b:
            self.assertEqual(a.read(), b.read())
        status = holdout_fixture.git(self.repo, "status", "--porcelain",
                                     "-uall").stdout.split("\n")
        self.assertEqual([s for s in status if s],
                         ["?? " + holdout_manifest.SEAL_RELPATH])

    def test_cli_publish(self):
        write_ledger(self.folder, [scan_entry(self.folder)])
        proc = self.cli("--folder", self.folder, "publish", "--repo",
                        self.repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(),
                         "OK: SEAL.json published to %s. Commit it on its own."
                         % self.dest)

    def test_idempotent(self):
        write_ledger(self.folder, [scan_entry(self.folder)])
        holdout_manifest.publish(self.folder, self.repo)
        self.assertEqual(holdout_manifest.publish(self.folder, self.repo),
                         self.dest)

    def test_never_overwrites(self):
        write_ledger(self.folder, [scan_entry(self.folder)])
        holdout_fixture.write(self.repo, holdout_manifest.SEAL_RELPATH,
                              "{\"other\": true}\n")
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.publish(self.folder, self.repo)
        with open(self.dest) as fh:
            self.assertEqual(fh.read(), "{\"other\": true}\n")

    def test_shape_failure_refused(self):
        seal = json.loads(json.dumps(self.seal))
        seal["repo"] = REPO_NAME
        holdout_kit.write_json_atomic(self.seal_path, seal)
        write_ledger(self.folder, [scan_entry(self.folder)])
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.publish(self.folder, self.repo)
        self.assertFalse(os.path.exists(self.dest))

    def test_each_failing_ledger_refuses(self):
        cid = self.ids["C2"]
        at = "2026-10-08T09:00:00Z"
        stale = scan_entry(self.folder)
        stale["seal_sha256"] = "e" * 64
        cases = [
            (None, NO_SCAN),
            ([scan_entry(self.folder, hits=2, ids=[cid], slots=["C2"])],
             FOUND),
            ([stale], PREDATES),
            ([scan_entry(self.folder, hits=1, ids=[cid], slots=["C2"], at=at),
              scan_entry(self.folder)], not_replaced("C2", cid, at)),
        ]
        ledger = os.path.join(self.folder, holdout_manifest.LEAKSCAN_RELPATH)
        for scans, line in cases:
            if scans is None:
                if os.path.exists(ledger):
                    os.remove(ledger)
            else:
                write_ledger(self.folder, scans)
            proc = self.cli("--folder", self.folder, "publish", "--repo",
                            self.repo)
            self.assertEqual(proc.returncode, 1, line)
            self.assertEqual(proc.stderr.splitlines()[0], "holdout: " + line)
            self.assertFalse(os.path.exists(self.dest), line)

    def test_mutant_leak_gate(self):
        cid = self.ids["C2"]
        write_ledger(self.folder, [
            scan_entry(self.folder, hits=1, ids=[cid], slots=["C2"]),
            scan_entry(self.folder)])
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.publish(self.folder, self.repo)
        self.assertFalse(os.path.exists(self.dest))
        with mock.patch.object(holdout_manifest, "leak_ledger_problems",
                               return_value=[]):
            holdout_manifest.publish(self.folder, self.repo)
        self.assertTrue(os.path.isfile(self.dest))

    def test_refuses_under_claudecode(self):
        write_ledger(self.folder, [scan_entry(self.folder)])
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        proc = self.cli("--folder", self.folder, "publish", "--repo",
                        self.repo, env=env)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stderr, holdout_kit.REFUSE_MSG + "\n")
        self.assertFalse(os.path.exists(self.dest))

    def test_requires_folder(self):
        rc, _, err = self.run_inproc(["publish", "--repo", self.repo])
        self.assertEqual(rc, 1)
        self.assertIn("--folder", err)
        self.assertFalse(os.path.exists(self.dest))


# ================================================================ retirement


def relabel_case(folder, old_id):
    """Copy a case byte-for-byte to a fresh ID, delete the old one, re-run
    seal-build and append a clean leak scan against the new SEAL.json."""
    sealed = os.path.join(folder, "sealed")
    new_id = holdout_kit.new_case_id()
    for part in ("cases", "keys"):
        shutil.copytree(os.path.join(sealed, part, old_id),
                        os.path.join(sealed, part, new_id))
    case_json = os.path.join(sealed, "cases", new_id, "case.json")
    with open(case_json) as fh:
        data = json.load(fh)
    data["id"] = new_id
    with open(case_json, "w") as fh:
        json.dump(data, fh)
    for part in ("cases", "keys"):
        shutil.rmtree(os.path.join(sealed, part, old_id))
    seal = holdout_manifest.build_seal(folder)
    holdout_manifest.write_inventory(folder)
    holdout_kit.write_json_atomic(os.path.join(folder, "SEAL.json"), seal)
    ledger_path = os.path.join(folder, holdout_manifest.LEAKSCAN_RELPATH)
    scans = []
    if os.path.exists(ledger_path):
        with open(ledger_path) as fh:
            scans = json.load(fh)["scans"]
    write_ledger(folder, scans + [scan_entry(folder)])
    return new_id


def retired_line_prefix(slot, cid):
    return "case %s (%s) reuses material retired on " % (slot, cid)


class RetiredCase(SealedCase):

    def setUp(self):
        super().setUp()
        write_ledger(self.folder, [scan_entry(self.folder)])
        self.repo = holdout_fixture.make_repo(self.tmp)
        self.dest = os.path.join(self.repo,
                                 *holdout_manifest.SEAL_RELPATH.split("/"))
        self.retired_path = os.path.join(self.folder,
                                         holdout_manifest.RETIRED_RELPATH)

    def ledger_text(self):
        with open(self.retired_path) as fh:
            return fh.read()

    def ledger(self):
        with open(self.retired_path) as fh:
            return json.load(fh)

    def replace(self, slot, **kw):
        """Delete the slot's current case, write a new one, re-seal, and
        append a clean scan. Returns the new ID."""
        old = self.ids[slot]
        for part in ("cases", "keys"):
            shutil.rmtree(self.p(part, old))
        new = write_case(self.folder, slot, **kw)
        self.ids[slot] = new
        self.seal = self.seal_build()
        with open(os.path.join(self.folder,
                               holdout_manifest.LEAKSCAN_RELPATH)) as fh:
            scans = json.load(fh)["scans"]
        write_ledger(self.folder, scans + [scan_entry(self.folder)])
        return new

    def matched(self, problems):
        self.assertEqual(len(problems), 1, problems)
        m = re.search(r"\(([a-z,]+)\); a retired change", problems[0])
        self.assertTrue(m, problems[0])
        return m.group(1)


class TestLeakClearance(RetiredCase):
    """A clearance (owner rule 2026-10-09) is an append-only record a later
    kit command writes; it lets a leak-named, leakscan-retired case stay
    only for the seal it was cleared against. Owner retirements are never
    cleared."""

    def clear(self, slots, at="2026-10-09T12:00:00Z", seal_sha=None):
        cases = {self.ids[s]: {"slot": s, "cause": "origin-history",
                               "identity": holdout_manifest.case_identity(
                                   self.folder, self.ids[s])}
                 for s in slots}
        holdout_manifest.append_clearance(
            self.folder, cases, at=at,
            seal_sha256=seal_sha or holdout_kit.sha256_file(
                os.path.join(self.folder, "SEAL.json")))

    def named(self, slot, at="2026-10-09T10:00:00Z"):
        cid = self.ids[slot]
        write_ledger(self.folder, [
            scan_entry(self.folder, hits=1, ids=[cid], slots=[slot], at=at),
            scan_entry(self.folder, at="2026-10-09T11:00:00Z")])
        return cid

    def problems(self):
        return holdout_manifest.leak_ledger_problems(self.folder, self.seal)

    def test_named_case_needs_clearance(self):
        cid = self.named("C3")
        self.assertEqual(self.problems(),
                         [not_replaced("C3", cid, "2026-10-09T10:00:00Z")])
        self.clear(["C3"])
        self.assertEqual(self.problems(), [])

    def test_clearance_is_bound_to_the_seal(self):
        self.named("C3")
        self.clear(["C3"], seal_sha="0" * 64)
        self.assertEqual(len(self.problems()), 1)

    def test_clearance_before_the_naming_scan_does_not_count(self):
        self.named("C3", at="2026-10-09T13:00:00Z")
        self.clear(["C3"], at="2026-10-09T12:00:00Z")
        self.assertEqual(len(self.problems()), 1)

    def test_clears_only_its_cases(self):
        cid = self.named("Q1")
        self.clear(["C3"])
        self.assertEqual(self.problems(),
                         [not_replaced("Q1", cid, "2026-10-09T10:00:00Z")])

    def test_leakscan_retirement_is_cleared(self):
        holdout_manifest.retire_case(self.folder, self.ids["C3"], "leakscan")
        self.assertEqual(len(holdout_manifest.retired_problems(self.folder)),
                         1)
        self.clear(["C3"], at="2099-01-01T00:00:00Z")
        self.assertEqual(holdout_manifest.retired_problems(self.folder), [])

    def test_owner_retirement_is_never_cleared(self):
        holdout_manifest.retire_case(self.folder, self.ids["C3"], "owner")
        self.clear(["C3"], at="2099-01-01T00:00:00Z")
        self.assertEqual(len(holdout_manifest.retired_problems(self.folder)),
                         1)

    def test_clears_only_the_content_it_names(self):
        holdout_manifest.retire_case(self.folder, self.ids["Q1"], "leakscan")
        self.clear(["C3"], at="2099-01-01T00:00:00Z")
        self.assertEqual(len(holdout_manifest.retired_problems(self.folder)),
                         1)

    def test_an_edited_case_is_not_covered_by_the_old_seal(self):
        self.named("C3")
        self.clear(["C3"])
        with open(self.p("keys", self.ids["C3"], "key.json"), "ab") as fh:
            fh.write(b" ")
        self.seal = self.seal_build()
        self.assertIn(not_replaced("C3", self.ids["C3"],
                                   "2026-10-09T10:00:00Z"), self.problems())

    def test_append_only_and_malformed_refused(self):
        self.clear(["C3"])
        self.clear(["Q1"])
        path = os.path.join(self.folder,
                            holdout_manifest.LEAK_CLEARED_RELPATH)
        with open(path) as fh:
            self.assertEqual(len(json.load(fh)["clearances"]), 2)
        with open(path, "w") as fh:
            fh.write("{")
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.load_clearances(self.folder)

    def test_cleared_slots_for_seal(self):
        self.clear(["C3", "Q1"])
        self.assertEqual(holdout_manifest.cleared_slots(self.folder),
                         ["C3", "Q1"])


class TestRetired(RetiredCase):

    def test_fingerprint_is_id_independent(self):
        old = self.ids["C2"]
        new = "H-0000f00d"
        for part in ("cases", "keys"):
            shutil.copytree(self.p(part, old), self.p(part, new))
        a = holdout_manifest.case_fingerprint(self.folder, old)
        b = holdout_manifest.case_fingerprint(self.folder, new)
        self.assertEqual(a, b)
        for fp in (a, b):
            self.assertFalse(any(ID_ANY.search(s) for s in _strings(fp)))
            self.assertEqual(set(fp), {"source", "diff_sha256",
                                       "lines_sha256", "key_sha256"})
            self.assertEqual(set(fp["source"]),
                             {"repo_name", "base_rev", "feature_rev"})

    def test_lines_hash_ignores_context_and_whitespace(self):
        a = holdout_manifest._diff_lines_sha256(default_diff("C1", 1).encode())
        b = holdout_manifest._diff_lines_sha256(default_diff("C1", 3).encode())
        c = holdout_manifest._diff_lines_sha256(
            default_diff("C1", 1).replace("+    return value_c1",
                                          "+\t\treturn value_c1   ")
            .encode())
        self.assertEqual(a, b)
        self.assertEqual(a, c)
        d = holdout_manifest._diff_lines_sha256(
            default_diff("C2", 1).encode())
        self.assertNotEqual(a, d)

    def test_retire_writes_opaque_entry(self):
        cid = self.ids["C2"]
        ledger = holdout_manifest.retire_case(self.folder, cid, "leakscan")
        self.assertEqual(ledger["schema"], holdout_manifest.RETIRED_SCHEMA)
        self.assertEqual(len(ledger["retired"]), 1)
        entry = ledger["retired"][0]
        self.assertEqual(entry["slot"], "C2")
        self.assertEqual(entry["reason"], "leakscan")
        self.assertEqual(entry["source"]["repo_name"], REPO_NAME)
        text = self.ledger_text()
        self.assertIsNone(ID_ANY.search(text))
        with open(self.p("cases", cid, "change.diff")) as fh:
            for ln in fh:
                if ln.startswith(("+", "-")) and ln.strip("+- \n"):
                    self.assertNotIn(ln[1:].strip(), text)
        key = default_key("C2")
        self.assertNotIn(key["defect"], text)
        self.assertNotIn(key["causal_failure"], text)
        self.assertNotIn(self.tmp, text)
        self.assertNotIn("/Users", text)
        with open(os.path.join(self.folder,
                               holdout_manifest.RETIRED_REVISIONS_RELPATH)) as f:
            revs = json.load(f)
        self.assertEqual(revs["revisions"], [entry["source"]])

    def test_retire_twice_appends_once(self):
        cid = self.ids["C2"]
        holdout_manifest.retire_case(self.folder, cid, "leakscan")
        ledger = holdout_manifest.retire_case(self.folder, cid, "owner")
        self.assertEqual(len(ledger["retired"]), 1)
        self.assertEqual(len(self.ledger()["retired"]), 1)

    def test_retire_keeps_earlier_entries(self):
        holdout_manifest.retire_case(self.folder, self.ids["C1"], "owner")
        first = self.ledger()["retired"][0]
        holdout_manifest.retire_case(self.folder, self.ids["Q1"], "owner")
        entries = self.ledger()["retired"]
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0], first)

    def test_retire_deleted_case_refused(self):
        cid = self.ids["C2"]
        for part in ("cases", "keys"):
            shutil.rmtree(self.p(part, cid))
        with self.assertRaises(holdout_kit.KitError) as ctx:
            holdout_manifest.retire_case(self.folder, cid, "leakscan")
        self.assertIn("retire BEFORE deleting", str(ctx.exception))
        self.assertFalse(os.path.exists(self.retired_path))

    def test_retire_bad_reason(self):
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.retire_case(self.folder, self.ids["C2"], "other")

    def test_retire_from_content_folder(self):
        cid = self.ids["Q2"]
        verify = os.path.join(self.tmp, "verify")
        shutil.copytree(self.sealed, os.path.join(verify, "sealed"))
        live = holdout_manifest.case_fingerprint(self.folder, cid)
        for part in ("cases", "keys"):
            shutil.rmtree(self.p(part, cid))
        ledger = holdout_manifest.retire_case(self.folder, cid, "leakscan",
                                              content_folder=verify)
        entry = ledger["retired"][0]
        self.assertEqual(entry["slot"], "Q2")
        for k, v in live.items():
            self.assertEqual(entry[k], v)
        self.assertTrue(os.path.isfile(self.retired_path))
        self.assertFalse(os.path.exists(os.path.join(
            verify, holdout_manifest.RETIRED_RELPATH)))

    def test_relabel_caught(self):
        old = self.ids["C2"]
        holdout_manifest.retire_case(self.folder, old, "leakscan")
        at = self.ledger()["retired"][0]["at"]
        new = relabel_case(self.folder, old)
        self.assertNotEqual(new, old)
        with open(self.seal_path) as fh:
            seal = json.load(fh)
        self.assertNotIn(old, seal["cases"])
        self.assertEqual(
            holdout_manifest.leak_ledger_problems(self.folder, seal), [])
        problems = holdout_manifest.retired_problems(self.folder)
        self.assertEqual(problems, [
            "case C2 (%s) reuses material retired on %s (source,diff,lines,"
            "key); a retired change cannot return under a new ID: replace it "
            "with a different change (different revision AND different diff)"
            % (new, at)])
        proc = self.cli("--folder", self.folder, "publish", "--repo",
                        self.repo)
        self.assertEqual(proc.returncode, 1)
        self.assertTrue(proc.stderr.startswith(
            "holdout: " + retired_line_prefix("C2", new)), proc.stderr)
        self.assertFalse(os.path.exists(self.dest))

    def test_variant_more_context(self):
        holdout_manifest.retire_case(self.folder, self.ids["C1"], "leakscan")
        self.replace("C1", diff=default_diff("C1", context=3))
        self.assertEqual(self.matched(
            holdout_manifest.retired_problems(self.folder)),
            "source,lines,key")

    def test_variant_new_provenance_same_diff(self):
        holdout_manifest.retire_case(self.folder, self.ids["C1"], "owner")
        self.replace("C1", provenance=default_provenance(
            "C1", repo_name="other-repo", tag="z"))
        self.assertEqual(self.matched(
            holdout_manifest.retired_problems(self.folder)),
            "diff,lines,key")

    def test_variant_same_key_except_slot(self):
        holdout_manifest.retire_case(self.folder, self.ids["C1"], "owner")
        self.replace("C1", key=default_key("C1", tag="b"),
                     provenance=default_provenance("C1", tag="b"),
                     diff=make_diff("src/fresh.py", ["f = 1"], ["f = 2"]))
        self.assertEqual(holdout_manifest.retired_problems(self.folder), [])
        key = dict(default_key("C1"), slot="C2")
        self.replace("C2", key=key,
                     provenance=default_provenance("C2", repo_name="other-repo",
                                                   tag="z"),
                     diff=make_diff("src/other.py", ["a = 1"], ["a = 2"]))
        problems = holdout_manifest.retired_problems(self.folder)
        self.assertTrue(problems[0].startswith(
            retired_line_prefix("C2", self.ids["C2"])))
        self.assertEqual(self.matched(problems), "key")

    def test_genuinely_different_case_passes(self):
        holdout_manifest.retire_case(self.folder, self.ids["C1"], "leakscan")
        self.replace("C1", key=default_key("C1", tag="b"),
                     provenance=default_provenance("C1", tag="b"),
                     diff=make_diff("src/new.py", ["b = 1"], ["b = 3"]))
        self.assertEqual(holdout_manifest.retired_problems(self.folder), [])
        holdout_manifest.publish(self.folder, self.repo)
        self.assertTrue(os.path.isfile(self.dest))

    def test_shared_base_alone_never_matches(self):
        base = b"shared constructed base tree"
        self.replace("Q1", base=base, key=default_key("Q1", tag="c1"),
                     provenance=default_provenance("Q1", tag="c1",
                                                   organic=False),
                     diff=make_diff("src/q.py", ["q = 1"], ["q = 2"]))
        holdout_manifest.retire_case(self.folder, self.ids["Q1"], "owner")
        self.replace("Q1", base=base, key=default_key("Q1", tag="c2"),
                     provenance=default_provenance("Q1", tag="c2",
                                                   organic=False),
                     diff=make_diff("src/q.py", ["q = 1"], ["q = 5"]))
        self.assertEqual(holdout_manifest.retired_problems(self.folder), [])
        entry = self.ledger()["retired"][0]
        self.assertEqual(entry["source"]["feature_rev"], None)

    def test_m1_retired_gate_is_load_bearing(self):
        old = self.ids["C2"]
        holdout_manifest.retire_case(self.folder, old, "leakscan")
        relabel_case(self.folder, old)
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.publish(self.folder, self.repo)
        self.assertFalse(os.path.exists(self.dest))
        with mock.patch.object(holdout_manifest, "retired_problems",
                               return_value=[]):
            holdout_manifest.publish(self.folder, self.repo)
        self.assertTrue(os.path.isfile(self.dest))

    def test_m2_id_bound_fingerprint_reopens_the_hole(self):
        real = holdout_manifest.case_fingerprint

        def id_bound(folder, case_id):
            fp = real(folder, case_id)
            mix = lambda v: None if v is None else hashlib.sha256(
                (v + case_id).encode()).hexdigest()
            return {"source": {k: mix(v) for k, v in fp["source"].items()},
                    "diff_sha256": mix(fp["diff_sha256"]),
                    "lines_sha256": mix(fp["lines_sha256"]),
                    "key_sha256": mix(fp["key_sha256"])}

        # Mutant: an ID-bound fingerprint lets the relabeled case through.
        with mock.patch.object(holdout_manifest, "case_fingerprint",
                               id_bound):
            holdout_manifest.retire_case(self.folder, self.ids["Q1"],
                                         "leakscan")
            relabeled = relabel_case(self.folder, self.ids["Q1"])
            self.assertEqual(holdout_manifest.retired_problems(self.folder),
                             [])
        # Real: the same retire + relabel is caught.
        os.remove(self.retired_path)
        holdout_manifest.retire_case(self.folder, relabeled, "leakscan")
        again = relabel_case(self.folder, relabeled)
        problems = holdout_manifest.retired_problems(self.folder)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            retired_line_prefix("Q1", again)))

    def test_m3_absent_and_malformed(self):
        self.assertFalse(os.path.exists(self.retired_path))
        self.assertEqual(holdout_manifest.retired_problems(self.folder), [])
        with open(self.retired_path, "w") as fh:
            json.dump([], fh)
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.retired_problems(self.folder)
        with open(self.retired_path, "w") as fh:
            json.dump({"schema": holdout_manifest.RETIRED_SCHEMA,
                       "retired": [{"at": "x"}]}, fh)
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.retired_problems(self.folder)

    def test_empty_ledger_passes(self):
        holdout_kit.write_json_atomic(
            self.retired_path, {"schema": holdout_manifest.RETIRED_SCHEMA,
                                "retired": []})
        self.assertEqual(holdout_manifest.retired_problems(self.folder), [])

    def test_sync_recreates_skip_list(self):
        holdout_manifest.retire_case(self.folder, self.ids["C1"], "owner")
        holdout_manifest.retire_case(self.folder, self.ids["Q3"], "owner")
        path = os.path.join(self.folder,
                            holdout_manifest.RETIRED_REVISIONS_RELPATH)
        with open(path) as fh:
            before = json.load(fh)
        shutil.rmtree(os.path.join(self.folder, "work"))
        self.assertEqual(holdout_manifest.sync_retired_revisions(self.folder),
                         2)
        with open(path) as fh:
            self.assertEqual(json.load(fh), before)

    def test_sync_without_ledger_writes_empty(self):
        self.assertEqual(holdout_manifest.sync_retired_revisions(self.folder),
                         0)
        with open(os.path.join(
                self.folder, holdout_manifest.RETIRED_REVISIONS_RELPATH)) as f:
            self.assertEqual(json.load(f)["revisions"], [])

    def test_retired_not_in_seal_or_inventory(self):
        holdout_manifest.retire_case(self.folder, self.ids["C1"], "owner")
        self.seal_build()
        with open(self.p("INVENTORY.json")) as fh:
            self.assertNotIn("RETIRED", fh.read())
        with open(self.seal_path) as fh:
            self.assertNotIn("RETIRED", fh.read())


class TestCliRetire(RetiredCase):

    def test_retire_slot(self):
        cid = self.ids["C2"]
        proc = self.cli("--folder", self.folder, "retire", "--slot", "C2",
                        "--reason", "owner")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(),
                         "OK: retired C2 (%s): recorded in RETIRED.json; its "
                         "revision and content cannot be re-sealed under any "
                         "ID" % cid)
        led = self.ledger()
        self.assertEqual((len(led["retired"]), led["retired"][0]["slot"]),
                         (1, "C2"))
        self.assertEqual(led["retired"][0]["reason"], "owner")

    def test_retire_case(self):
        cid = self.ids["Q1"]
        proc = self.cli("--folder", self.folder, "retire", "--case", cid,
                        "--reason", "leakscan")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("OK: retired Q1 (%s)" % cid))
        self.assertEqual(self.ledger()["retired"][0]["reason"], "leakscan")

    def test_usage_errors(self):
        cid = self.ids["Q1"]
        for argv in (["retire", "--slot", "C2", "--case", cid, "--reason",
                      "owner"],
                     ["retire", "--reason", "owner"],
                     ["retire", "--slot", "C2"],
                     ["retire", "--sync", "--reason", "owner"],
                     ["retire", "--slot", "C9", "--reason", "owner"]):
            rc, _, _ = self.run_inproc(["--folder", self.folder] + argv)
            self.assertEqual(rc, 2, argv)
        self.assertFalse(os.path.exists(self.retired_path))

    def test_unknown_case(self):
        rc, _, err = self.run_inproc(["--folder", self.folder, "retire",
                                      "--case", "H-0000beef", "--reason",
                                      "owner"])
        self.assertEqual(rc, 1)
        self.assertIn("retire BEFORE deleting", err)

    def test_sync(self):
        holdout_manifest.retire_case(self.folder, self.ids["C1"], "owner")
        proc = self.cli("--folder", self.folder, "retire", "--sync")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(),
                         "OK: finder skip list rewritten (1 retired "
                         "revision(s))")

    def test_refuses_under_claudecode(self):
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        proc = self.cli("--folder", self.folder, "retire", "--slot", "C2",
                        "--reason", "owner", env=env)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stderr, holdout_kit.REFUSE_MSG + "\n")
        self.assertFalse(os.path.exists(self.retired_path))


# ================================================================ resume grammar

CONFORMING = [
    ("sealed", "sealed"),
    ("sealed non-runnable=1", "sealed"),
    ("sealed cleared=C1,C2,C3,Q1,Q2,Q3", "sealed"),
    ("sealed cleared=C3 non-runnable=1", "sealed"),
    ("replaced slots=C1 cleared=C3", "replaced"),
    ("leak-clear cleared=C1,C3 kept=none", "leak-clear"),
    ("leak-clear cleared=none kept=Q2", "leak-clear"),
    ("dry run ok prompted sandbox=ok", "dry-run-ok"),
    ("dry run ok", "dry-run-failed"),
    ("dry run ok prompted", "dry-run-failed"),
    ("dry run ok no-prompt", "dry-run-failed"),
    ("dry run ok no-prompt problems=5", "dry-run-failed"),
    ("dry run ok problems=3", "dry-run-failed"),
    ("dry run ok prompted problems=2,4", "dry-run-failed"),
    ("dry run ok prompted sandbox=ok problems=2,4", "dry-run-failed"),
    ("dry run ok no-prompt sandbox=ok", "dry-run-failed"),
    ("dry run ok sandbox=ok", "dry-run-failed"),
    ("replaced slots=C1,Q2", "replaced"),
    ("replaced slots=Q3 non-runnable=1", "replaced"),
    ("clean leakscan=0", "clean"),
    ("blocked disagreement", "blocked"),
    ("blocked sandbox", "blocked"),
    ("blocked no-prompt", "blocked"),
    ("  sealed  ", "sealed"),
    ("sealed\n", "sealed"),
    ("dry run ok prompted sandbox=ok\n", "dry-run-ok"),
    ("diagnosis C3 cause=judge-disagrees checks=type-other-slot,"
     "judge-type-false", "diagnosis"),
    ("diagnosis Q1 cause=agrees checks=none", "diagnosis"),
    ("denials gen=5 count=3 bash-home,read-holdout", "denials"),
    ("denials gen=12 count=0 none", "denials"),
    ("leakdiag C1=origin-history C2=none C3=exposed Q1=prior-elsewhere "
     "Q2=none Q3=none where=own-transcript,tuning-transcript", "leakdiag"),
    ("leakdiag C1=none C2=none C3=none Q1=none Q2=none Q3=none where=none",
     "leakdiag"),
    ("denials gen=2 count=0 unknown", "denials"),
    ("diagnosis C2 cause=checker-suspect checks=location-path-form",
     "diagnosis"),
]

NON_CONFORMING = [
    "sealed!", "Sealed", "sealed, C1 came from a repo I will not name",
    "sealed cleared=", "sealed cleared=C4", "leak-clear cleared=C1",
    "leak-clear cleared=C1 kept=the auth one",
    "sealed\nall good", "replaced", "replaced slots=C4", "blocked",
    "clean leakscan=1", "dry run ok, openssl prompted", "",
    "sealed non-runnable=7", "dry run ok prompted sandbox=OK",
    "dry run ok sandbox=ok prompted", "dry run ok prompted sandbox=ok\nfine",
    "dry run ok prompted sandbox=failed", "dry run ok prompted  sandbox=ok",
    "diagnosis C3 cause=judge-disagrees checks=sql-injection-in-login",
    "diagnosis C3 cause=judge-disagrees checks=none,type-other-slot",
    "diagnosis C3 cause=bad-key checks=none",
    "leakdiag C1=fine C2=none C3=none Q1=none Q2=none Q3=none where=none",
    "leakdiag C1=none where=none", "leakdiag C1=none C2=none C3=none Q1=none "
    "Q2=none Q3=none where=/Users/x",
    "denials gen=5 count=1 bash-/opt/thing", "denials gen=5 count=1 "
    "pytest-home", "denials gen=5 none", "denials gen=5 count=1 "
    "bash-home and more", "diagnosis C4 cause=agrees "
    "checks=none", "diagnosis C3 cause=agrees", "diagnosis C3 cause=agrees "
    "checks=none the handler in auth.py",
]

# The dry-run checkpoint (51-09 Task 1): only the clean success form may
# proceed; a reply that reports no openssl prompt, step problems, or omits
# the explicit sandbox-probe OK is a conforming but BLOCKING outcome.
DRY_RUN_TRANSITIONS = [
    ("dry run ok prompted sandbox=ok", "proceed"),
    ("dry run ok", "blocking"),
    ("dry run ok prompted", "blocking"),
    ("dry run ok no-prompt", "blocking"),
    ("dry run ok no-prompt problems=5", "blocking"),
    ("dry run ok problems=1", "blocking"),
    ("dry run ok prompted sandbox=ok problems=3", "blocking"),
    ("dry run ok no-prompt sandbox=ok", "blocking"),
    ("dry run ok sandbox=ok", "blocking"),
    ("blocked sandbox", "blocking"),
    ("blocked no-prompt", "blocking"),
    ("blocked other", "blocking"),
    ("sealed", "proceed"),
    ("replaced slots=C2", "proceed"),
    ("clean leakscan=0", "proceed"),
    ("dry run ok, it prompted", None),
]

# The permissive dry-run grammar from before the amendment, used as a mutant.
PERMISSIVE_DRY_RUN = (("dry-run-ok", re.compile(
    r"dry run ok(?: prompted| no-prompt)?"
    r"(?: problems=[0-9]+(?:,[0-9]+)*)?")),)


class TestResumeGrammar(unittest.TestCase):

    def test_conforming(self):
        for text, kind in CONFORMING:
            with self.subTest(text=text):
                self.assertEqual(holdout_manifest.resume_reply_kind(text),
                                 kind)

    def test_non_conforming(self):
        for text in NON_CONFORMING:
            with self.subTest(text=text):
                self.assertIsNone(holdout_manifest.resume_reply_kind(text))

    def test_never_raises(self):
        for value in (None, 5, b"sealed", ["sealed"]):
            self.assertIsNone(holdout_manifest.resume_reply_kind(value))

    def test_mutant_empty_grammar(self):
        with mock.patch.object(holdout_manifest, "RESUME_GRAMMAR", ()):
            for text, _ in CONFORMING:
                self.assertIsNone(holdout_manifest.resume_reply_kind(text))

    def test_kinds_partition(self):
        kinds = {k for k, _ in holdout_manifest.RESUME_GRAMMAR}
        self.assertEqual(kinds, {"dry-run-ok", "dry-run-failed", "sealed",
                                 "replaced", "clean", "blocked",
                                 "diagnosis", "denials", "leakdiag",
                                 "leak-clear"})
        self.assertEqual(holdout_manifest.RESUME_BLOCKING_KINDS,
                         frozenset({"dry-run-failed", "blocked",
                                    "diagnosis", "denials", "leakdiag",
                                    "leak-clear"}))
        self.assertTrue(holdout_manifest.RESUME_BLOCKING_KINDS <= kinds)
        order = [k for k, _ in holdout_manifest.RESUME_GRAMMAR]
        self.assertLess(order.index("dry-run-ok"),
                        order.index("dry-run-failed"))


class TestDiagnosisGrammar(unittest.TestCase):

    def test_every_vocabulary_word_conforms(self):
        for cause in holdout_manifest.DIAG_CAUSES:
            for check in holdout_manifest.DIAG_CHECKS:
                line = "diagnosis C3 cause=%s checks=%s" % (cause, check)
                self.assertEqual(holdout_manifest.resume_reply_kind(line),
                                 "diagnosis", line)

    def test_diagnosis_reply_blocks(self):
        self.assertEqual(holdout_manifest.resume_reply_outcome(
            "diagnosis C3 cause=agrees checks=none"), "blocking")

    def test_vocabulary_is_closed(self):
        for word in holdout_manifest.DIAG_CAUSES + holdout_manifest.DIAG_CHECKS:
            self.assertRegex(word, r"^[a-z]+(?:-[a-z]+)*$")


class TestDryRunTransitions(unittest.TestCase):

    def test_transitions(self):
        for text, outcome in DRY_RUN_TRANSITIONS:
            with self.subTest(text=text):
                self.assertEqual(
                    holdout_manifest.resume_reply_outcome(text), outcome)

    def test_only_clean_success_proceeds_at_dry_run(self):
        proceeding = [t for t, _ in CONFORMING
                      if holdout_manifest.resume_reply_kind(t) is not None
                      and holdout_manifest.resume_reply_kind(t).startswith(
                          "dry-run")
                      and holdout_manifest.resume_reply_outcome(t)
                      == "proceed"]
        self.assertEqual({t.strip() for t in proceeding},
                         {"dry run ok prompted sandbox=ok"})

    def test_mutant_permissive_grammar_lets_failures_through(self):
        self.assertEqual(holdout_manifest.resume_reply_outcome(
            "dry run ok no-prompt"), "blocking")
        with mock.patch.object(holdout_manifest, "RESUME_GRAMMAR",
                               PERMISSIVE_DRY_RUN):
            self.assertEqual(holdout_manifest.resume_reply_outcome(
                "dry run ok no-prompt"), "proceed")
            self.assertEqual(holdout_manifest.resume_reply_outcome(
                "dry run ok problems=5"), "proceed")

    def test_mutant_blocking_set_is_load_bearing(self):
        with mock.patch.object(holdout_manifest, "RESUME_BLOCKING_KINDS",
                               frozenset({"blocked"})):
            self.assertEqual(holdout_manifest.resume_reply_outcome(
                "dry run ok no-prompt problems=5"), "proceed")


class TestCliResumeCheck(ManifestCase):

    PROBLEM = ("PROBLEM: resume reply does not conform to the opaque grammar; "
               "treat it as a contamination incident and do not record its "
               "contents")

    def test_non_conforming_never_echoes(self):
        proc = self.cli("resume-check",
                        stdin="sealed, and C1 is from ZQX-SENTINEL-7731\n")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, self.PROBLEM + "\n")
        self.assertNotIn("ZQX", proc.stdout + proc.stderr)

    def test_conforming(self):
        proc = self.cli("resume-check", stdin="sealed\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "OK: resume reply conforms (sealed)\n")

    def test_dry_run_success(self):
        proc = self.cli("resume-check",
                        stdin="dry run ok prompted sandbox=ok\n")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout,
                         "OK: resume reply conforms (dry-run-ok)\n")

    def test_blocking_kinds_exit_3(self):
        for text, kind in (("dry run ok no-prompt", "dry-run-failed"),
                           ("dry run ok problems=2", "dry-run-failed"),
                           ("dry run ok prompted", "dry-run-failed"),
                           ("blocked sandbox", "blocked")):
            proc = self.cli("resume-check", stdin=text + "\n")
            self.assertEqual(proc.returncode, 3, text)
            self.assertEqual(proc.stdout.splitlines(), [
                "OK: resume reply conforms (%s)" % kind,
                "PROBLEM: this reply reports a blocking outcome (%s); stop "
                "and do not proceed" % kind])

    def test_works_under_claudecode(self):
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        proc = self.cli("resume-check", stdin="clean leakscan=0\n", env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "OK: resume reply conforms (clean)\n")

    def test_folder_accepted_and_ignored(self):
        proc = self.cli("--folder", os.path.join(self.tmp, "nowhere"),
                        "resume-check", stdin="sealed\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "nowhere")))

    def test_real_dispatcher_never_2(self):
        for text in ("sealed", "garbage", "blocked other", ""):
            rc, out, _ = self.run_inproc(["resume-check"], stdin=text)
            self.assertIn(rc, (0, 1, 3), text)

    def test_invalid_utf8_is_non_conforming(self):
        proc = subprocess.run([sys.executable, KIT_PY, "resume-check"],
                              cwd=self.tmp, env=holdout_fixture.kit_env(),
                              input=b"sealed \xff\xfe ZQX\n",
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=120)
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn(b"ZQX", proc.stdout + proc.stderr)


# ================================================================ CLI refusals


class TestCliManifest(SealedCase):

    def test_holdout_commands_refuse_under_claudecode(self):
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        repo = holdout_fixture.make_repo(self.tmp)
        for argv in (["seal-build"],
                     ["rehash", "--seal", self.seal_path, "--sealed",
                      self.sealed],
                     ["extract", "--part", "cases", "--dest",
                      os.path.join(self.tmp, "d")],
                     ["publish", "--repo", repo],
                     ["retire", "--sync"]):
            proc = self.cli("--folder", self.folder, *argv, env=env)
            self.assertEqual(proc.returncode, 1, argv)
            self.assertEqual(proc.stderr, holdout_kit.REFUSE_MSG + "\n", argv)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "d")))

    def test_isolated_session_config_inside_folder_allowed(self):
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        env["CLAUDE_CONFIG_DIR"] = os.path.join(self.folder, "cfg-finder")
        proc = self.cli("--folder", self.folder, "rehash", "--seal",
                        self.seal_path, "--sealed", self.sealed, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_folder_required_for_rehash(self):
        rc, _, err = self.run_inproc(["rehash", "--seal", self.seal_path,
                                      "--sealed", self.sealed])
        self.assertEqual(rc, 2)
        self.assertIn("--folder", err)

    def test_seal_order_ignores_folder(self):
        repo = holdout_fixture.make_repo(self.tmp)
        holdout_fixture.write(repo, "x", "x")
        holdout_fixture.git(repo, "add", "-A")
        holdout_fixture.git(repo, "commit", "-q", "-m", "init")
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        proc = self.cli("--folder", os.path.join(self.tmp, "nowhere"),
                        "seal-order", "--repo", repo, env=env)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout.strip(),
                         "PROBLEM: SEAL.json has no commit")

    def test_module_exports(self):
        for name in ("rehash_folder", "extract_part", "seal_order_problems",
                     "leak_ledger_problems", "case_fingerprint",
                     "retire_case", "sync_retired_revisions",
                     "retired_problems", "resume_reply_kind",
                     "resume_reply_outcome", "RESUME_GRAMMAR",
                     "RESUME_BLOCKING_KINDS", "publish", "LEAKSCAN_RELPATH",
                     "LEAKSCAN_SCHEMA", "RETIRED_RELPATH", "RETIRED_SCHEMA",
                     "RETIRED_REVISIONS_RELPATH"):
            self.assertTrue(hasattr(holdout_manifest, name), name)
        self.assertEqual(holdout_manifest.LEAKSCAN_RELPATH, "LEAKSCAN.json")
        self.assertEqual(holdout_manifest.RETIRED_RELPATH, "RETIRED.json")
        self.assertEqual(holdout_manifest.RETIRED_REVISIONS_RELPATH,
                         "work/RETIRED-REVISIONS.json")
        self.assertEqual(holdout_manifest.LEAKSCAN_SCHEMA,
                         "vibe-check-holdout-leakscan/1")
        self.assertEqual(holdout_manifest.RETIRED_SCHEMA,
                         "vibe-check-holdout-retired/1")

    def test_full_history_flags(self):
        with open(MANIFEST_PY) as fh:
            src = fh.read()
        for flag in ("--full-history", "--simplify-merges", "--topo-order",
                     "--branches", "--tags", "--remotes"):
            self.assertIn('"%s"' % flag, src)


if __name__ == "__main__":
    unittest.main()
