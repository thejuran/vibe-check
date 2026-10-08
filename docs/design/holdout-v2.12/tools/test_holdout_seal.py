"""Tests for holdout_seal — the blind cross-check and the seal gate.

Locked here:
  * crosscheck-prepare writes packets that hold code and definitions only
    (base tree, change.diff, CASE-TYPES.md, CROSSCHECK-BRIEF.md) under fresh
    random XIDs; the ID -> XID mapping and the sha256 of every input live only
    in sealed/keys/<ID>/xcheck-ledger.json.
  * Workspaces are generations. A workspace that has seen a reveal is burned:
    the next prepare mints a new generation (own cwd, own config dir, own
    scratch root, own launcher, every earlier generation denied) and records
    it in sealed/keys/xcheck-workspaces.json.
  * crosscheck-reveal is all-or-nothing per workspace and freezes every blind
    hash, reveal token and revealed-file hash in the ledgers before any key is
    copied.
  * crosscheck-reset is the only regeneration path; it archives the round and
    never touches the sealed case.
  * seal refuses on every blocker (validation, retired content, binding,
    workspace freshness, blind shape, final binding, the AGREEMENT RULE, the
    PROOF EXITS RULE and the NON-RUNNABLE RULE), and each blocker is shown to
    be load-bearing by a mutant that patches it out.

The valid holdout (holdout_fixture.make_valid_holdout) is built once per
module and copied into each test's own temp dir. Every fixture is synthetic;
nothing here reads the owner's holdout or installs a hook.
"""

import ast
import contextlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

import holdout_fixture  # noqa: E402
import holdout_kit  # noqa: E402
import holdout_manifest  # noqa: E402
import holdout_validate  # noqa: E402

import holdout_seal  # noqa: E402

KitError = holdout_kit.KitError
KIT_PY = os.path.join(TOOLS_DIR, "holdout_kit.py")
SEAL_PY = os.path.join(TOOLS_DIR, "holdout_seal.py")
HEX16 = re.compile(r"^[0-9a-f]{16}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

_TEMPLATE = {}


def setUpModule():
    tmp = tempfile.TemporaryDirectory()
    folder, ids = holdout_fixture.make_valid_holdout(tmp.name)
    _TEMPLATE.update(tmp=tmp, folder=folder, ids=ids)


def tearDownModule():
    _TEMPLATE["tmp"].cleanup()


# ================================================================ helpers


def quiet(fn, *args, **kwargs):
    """Call fn with stdout captured; return (result, stdout text)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn(*args, **kwargs)
    return result, buf.getvalue()


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dump(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")


def sha(path):
    return holdout_kit.sha256_file(path)


def kdir(folder, cid):
    return os.path.join(folder, "sealed", "keys", cid)


def cdir(folder, cid):
    return os.path.join(folder, "sealed", "cases", cid)


def ledger_path(folder, cid):
    return os.path.join(kdir(folder, cid), "xcheck-ledger.json")


def ledger(folder, cid):
    return load(ledger_path(folder, cid))


def registry_path(folder):
    return os.path.join(folder, *holdout_seal.WORKSPACES_RELPATH.split("/"))


def registry(folder):
    return load(registry_path(folder))


def packet(folder, cid):
    led = ledger(folder, cid)
    return os.path.join(folder, led["workspace"], led["xid"])


def key_of(folder, cid):
    return load(os.path.join(kdir(folder, cid), "key.json"))


def xids_in(folder, ws="xcheck"):
    return sorted(n for n in os.listdir(os.path.join(folder, ws))
                  if holdout_kit.XID_RE.match(n))


def agreeing_blind(key):
    slot = key["slot"]
    if slot in holdout_kit.CATCH_SLOTS:
        return {"verdict": "catch", "type_guess": slot,
                "location": dict(key["location"]),
                "defect_category": key["causal_failure_category"],
                "reasoning": "fixture reasoning"}
    return {"verdict": "quiet", "type_guess": slot, "location": None,
            "defect_category": None, "reasoning": "fixture reasoning"}


def write_blind(folder, cid, mutate=None):
    key = key_of(folder, cid)
    blind = agreeing_blind(key)
    if mutate is not None:
        mutate(key["slot"], blind)
    dump(os.path.join(packet(folder, cid), "blind.json"), blind)
    return blind


def agreeing_final(folder, cid):
    rev = os.path.join(packet(folder, cid), "revealed")
    with open(os.path.join(rev, "REVEAL-TOKEN"), encoding="utf-8") as fh:
        token = fh.read().strip()
    key = load(os.path.join(rev, "key.json"))
    pr = load(os.path.join(rev, "proof-results.json"))
    exits = None
    if pr.get("runnable") is True:
        exits = {"base": pr["base"]["exit"], "changed": pr["changed"]["exit"]}
    quiet_ok = None
    if key["slot"] in holdout_kit.QUIET_SLOTS:
        quiet_ok = {"supported_behavior": True, "exposure_check": True}
    return {"reveal_token": token, "type_agrees": True,
            "defect_agrees": True, "causal_failure_agrees": True,
            "proof_agrees": True, "proof_rerun_exit": exits,
            "quiet_confirmed": quiet_ok, "notes": "fixture notes"}


def write_final(folder, cid, mutate=None):
    final = agreeing_final(folder, cid)
    if mutate is not None:
        mutate(key_of(folder, cid)["slot"], final)
    dump(os.path.join(packet(folder, cid), "final.json"), final)
    return final


def live(folder, cid):
    path = ledger_path(folder, cid)
    if not os.path.exists(path):
        return False
    return bool(load(path).get("xid"))


def reveal_all(folder):
    """Reveal every unrevealed generation that holds a live packet."""
    out = []
    for g in registry(folder)["generations"]:
        if g["revealed_at"] is not None:
            continue
        packets = [c for c in g["cases"] if live(folder, c)
                   and ledger(folder, c).get("generation") == g["gen"]]
        if packets:
            got, _ = quiet(holdout_seal.reveal_workspace, folder, g["gen"])
            out.extend(got)
    return out


def complete_crosscheck(folder, ids, mutate_blind=None, mutate_final=None):
    """Prepare every case without a live packet, write an agreeing blind.json
    for every unrevealed packet, reveal, then write an agreeing final.json
    wherever one is missing. Each case is completed in the workspace its
    ledger names. The callbacks get (slot, dict) and may mutate the dict."""
    cids = list(ids.values())
    if any(not live(folder, c) for c in cids):
        quiet(holdout_seal.prepare_crosscheck, folder)
    for c in cids:
        if not ledger(folder, c).get("blind_sha256"):
            if not os.path.exists(os.path.join(packet(folder, c),
                                               "blind.json")):
                write_blind(folder, c, mutate_blind)
    reveal_all(folder)
    for c in cids:
        if not os.path.exists(os.path.join(packet(folder, c), "final.json")):
            write_final(folder, c, mutate_final)


def complete_case(folder, cid, mutate_blind=None, mutate_final=None):
    """prepare --case, blind, reveal and final for one case."""
    quiet(holdout_seal.prepare_crosscheck, folder, case_id=cid)
    write_blind(folder, cid, mutate_blind)
    reveal_all(folder)
    write_final(folder, cid, mutate_final)


def file_hashes(root):
    return {rel: sha(os.path.join(root, rel))
            for rel in holdout_kit.walk_regular(root)}


class SealCase(unittest.TestCase):
    """Base: a private copy of the valid holdout and a plain-Terminal env."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = os.path.realpath(self._tmp.name)
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("CLAUDECODE", None)
        os.environ.pop("CLAUDE_CONFIG_DIR", None)
        self.folder = os.path.join(self.tmp, "holdout")
        shutil.copytree(_TEMPLATE["folder"], self.folder, symlinks=True)
        self.ids = dict(_TEMPLATE["ids"])

    def cid(self, slot):
        return self.ids[slot]

    def prepare(self, case_id=None):
        return quiet(holdout_seal.prepare_crosscheck, self.folder,
                     case_id=case_id)

    def blinds(self, mutate=None, skip=()):
        for slot, c in self.ids.items():
            if slot not in skip:
                write_blind(self.folder, c, mutate)

    def complete(self, **kw):
        complete_crosscheck(self.folder, self.ids, **kw)

    def reset(self, slot, reason="owner"):
        return quiet(holdout_seal.reset_crosscheck, self.folder,
                     self.cid(slot), reason)[0]

    def cli(self, *args, env=None):
        return subprocess.run(
            [sys.executable, KIT_PY, "--folder", self.folder] + list(args),
            env=env if env is not None else holdout_fixture.kit_env(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            timeout=300)


# ================================================================ prepare


class TestPrepare(SealCase):

    def test_six_packets_with_random_xids(self):
        mapping, _ = self.prepare()
        self.assertEqual(sorted(mapping), sorted(self.ids.values()))
        self.assertEqual(sorted(mapping.values()), xids_in(self.folder))
        for xid in mapping.values():
            self.assertRegex(xid, holdout_kit.XID_RE)
        for cid, xid in mapping.items():
            self.assertNotEqual(xid[2:], cid[2:])

    def test_packet_contents(self):
        mapping, _ = self.prepare()
        kit = os.path.join(self.folder, "kit")
        for cid, xid in mapping.items():
            p = os.path.join(self.folder, "xcheck", xid)
            self.assertEqual(sorted(os.listdir(p)),
                             ["CASE-TYPES.md", "CROSSCHECK-BRIEF.md", "base",
                              "change.diff"])
            self.assertEqual(sha(os.path.join(p, "change.diff")),
                             sha(os.path.join(cdir(self.folder, cid),
                                              "change.diff")))
            for doc in ("CASE-TYPES.md", "CROSSCHECK-BRIEF.md"):
                self.assertEqual(sha(os.path.join(p, doc)),
                                 sha(os.path.join(kit, doc)))
            with tarfile.open(os.path.join(cdir(self.folder, cid),
                                           "base.tar")) as tar:
                members = sorted(m.name for m in tar.getmembers()
                                 if m.isfile())
            self.assertEqual(holdout_kit.walk_regular(os.path.join(p, "base")),
                             members)

    def test_no_verdict_material_in_any_packet(self):
        self.prepare()
        forbidden = {"key.json", "provenance.json", "proof", "run",
                     "proof-results.json", "FINDER-BRIEF.md",
                     "xcheck-ledger.json", "crosscheck.json",
                     "resolution.md", holdout_kit.XCHECK_REGISTRY}
        defects = [key_of(self.folder, c).get("defect")
                   for c in self.ids.values()]
        defects = [d for d in defects if d]
        root = os.path.join(self.folder, "xcheck")
        for dirpath, dirnames, filenames in os.walk(root):
            for name in dirnames + filenames:
                self.assertNotIn(name, forbidden)
                self.assertNotIn(name, holdout_kit.SLOTS)
            for name in filenames:
                with open(os.path.join(dirpath, name), "rb") as fh:
                    data = fh.read()
                for d in defects:
                    self.assertNotIn(d.encode(), data)
                for c in self.ids.values():
                    self.assertNotIn(c.encode(), data)

    def test_xids_differ_across_two_copies(self):
        first, _ = self.prepare()
        other = os.path.join(self.tmp, "other")
        shutil.copytree(_TEMPLATE["folder"], other, symlinks=True)
        second, _ = quiet(holdout_seal.prepare_crosscheck, other)
        self.assertFalse(set(first.values()) & set(second.values()))

    def test_ledger_binds_inputs(self):
        mapping, _ = self.prepare()
        for cid, xid in mapping.items():
            led = ledger(self.folder, cid)
            self.assertEqual(led["xid"], xid)
            self.assertEqual(led["round"], 1)
            self.assertEqual(led["generation"], 1)
            self.assertEqual(led["workspace"], "xcheck")
            self.assertTrue(led["prepared_at"])
            self.assertEqual(led["rounds"], [])
            self.assertEqual(led["inputs"], {
                "base.tar": sha(os.path.join(cdir(self.folder, cid),
                                             "base.tar")),
                "change.diff": sha(os.path.join(cdir(self.folder, cid),
                                                "change.diff")),
                "CASE-TYPES.md": sha(os.path.join(self.folder, "kit",
                                                  "CASE-TYPES.md"))})

    def test_mapping_lives_only_in_the_ledgers(self):
        self.prepare()
        for name in os.listdir(os.path.join(self.folder, "xcheck")):
            self.assertFalse(name.endswith(".json"), name)

    def test_second_prepare_refused(self):
        self.prepare()
        with self.assertRaises(KitError) as cm:
            self.prepare()
        self.assertIn("cross-check folder already exists for", str(cm.exception))
        self.assertIn("run crosscheck-reset first", str(cm.exception))

    def test_prepare_case_with_live_packet_refused(self):
        self.prepare()
        with self.assertRaises(KitError) as cm:
            self.prepare(self.cid("C2"))
        self.assertIn("already exists for C2", str(cm.exception))

    def test_prepare_case_after_reset_gets_new_xid_round_two(self):
        mapping, _ = self.prepare()
        old = mapping[self.cid("C1")]
        self.reset("C1")
        again, _ = self.prepare(self.cid("C1"))
        self.assertEqual(list(again), [self.cid("C1")])
        self.assertNotEqual(again[self.cid("C1")], old)
        self.assertEqual(ledger(self.folder, self.cid("C1"))["round"], 2)
        for slot in ("C2", "C3", "Q1"):
            self.assertEqual(ledger(self.folder, self.cid(slot))["xid"],
                             mapping[self.cid(slot)])

    def test_prepare_after_seal_refused(self):
        dump(os.path.join(self.folder, "SEAL.json"), {})
        with self.assertRaises(KitError) as cm:
            self.prepare()
        self.assertIn("already sealed", str(cm.exception))
        self.assertFalse(os.path.exists(registry_path(self.folder)))

    def test_prepare_unknown_case_refused(self):
        with self.assertRaises(KitError):
            self.prepare("H-00000000")

    def test_failed_extract_leaves_no_packet_and_no_ledger(self):
        with mock.patch.object(holdout_kit, "safe_extract_tar",
                               side_effect=KitError("boom")):
            with self.assertRaises(KitError):
                self.prepare()
        self.assertEqual(xids_in(self.folder), [])
        for c in self.ids.values():
            self.assertFalse(os.path.exists(ledger_path(self.folder, c)))


# ================================================================ workspaces


class TestWorkspaces(SealCase):

    def _deny(self, ws):
        return load(os.path.join(self.folder, ws, ".claude", "settings.json"))

    def test_first_prepare_registers_generation_one(self):
        self.prepare()
        reg = registry(self.folder)
        self.assertEqual(len(reg["generations"]), 1)
        g = reg["generations"][0]
        self.assertEqual(g["gen"], 1)
        self.assertEqual(g["workspace"], "xcheck")
        self.assertEqual(g["config_dir"], "cfg-xcheck")
        self.assertEqual(g["tmp_dir"], "tmp/crosscheck/xcheck")
        self.assertEqual(g["launcher"], "bin/crosscheck")
        self.assertEqual(sorted(g["cases"]), sorted(self.ids.values()))
        self.assertIsNone(g["revealed_at"])
        self.assertTrue(g["created_at"])

    def test_reset_before_reveal_stays_in_generation_one(self):
        self.prepare()
        self.reset("C2")
        _, out = self.prepare(self.cid("C2"))
        self.assertFalse(os.path.exists(os.path.join(self.folder,
                                                     "xcheck-r2")))
        led = ledger(self.folder, self.cid("C2"))
        self.assertEqual((led["generation"], led["workspace"]), (1, "xcheck"))
        self.assertNotIn("fresh cross-check workspace", out)
        self.assertEqual(len(registry(self.folder)["generations"]), 1)
        self.assertEqual(registry(self.folder)["generations"][0]["cases"]
                         .count(self.cid("C2")), 1)

    def test_reset_after_reveal_mints_generation_two(self):
        self.complete()
        self.reset("Q1")
        mapping, out = self.prepare(self.cid("Q1"))
        f = self.folder
        self.assertEqual(xids_in(f, "xcheck-r2"), [mapping[self.cid("Q1")]])
        self.assertEqual(os.listdir(os.path.join(f, "cfg-xcheck-r2")), [])
        tmp_root = os.path.join(f, "tmp", "crosscheck", "xcheck-r2")
        self.assertEqual(os.listdir(tmp_root), ["SANDBOX-SENTINEL"])
        launcher = os.path.join(f, "bin", "crosscheck-r2")
        self.assertEqual(stat.S_IMODE(os.stat(launcher).st_mode), 0o700)
        with open(launcher, encoding="utf-8") as fh:
            self.assertIn('TMPDIR="$H/tmp/crosscheck/xcheck-r2"', fh.read())
        gens = registry(f)["generations"]
        self.assertEqual([g["gen"] for g in gens], [1, 2])
        self.assertIsNotNone(gens[0]["revealed_at"])
        self.assertEqual(gens[1]["cases"], [self.cid("Q1")])
        self.assertIsNone(gens[1]["revealed_at"])
        self.assertEqual(gens[1]["tmp_dir"], "tmp/crosscheck/xcheck-r2")
        self.assertEqual(gens[1]["workspace"], "xcheck-r2")
        self.assertEqual(gens[1]["launcher"], "bin/crosscheck-r2")
        led = ledger(f, self.cid("Q1"))
        self.assertEqual((led["generation"], led["workspace"]),
                         (2, "xcheck-r2"))
        self.assertIn("fresh cross-check workspace xcheck-r2", out)

    def test_generation_two_denies_generation_one(self):
        self.complete()
        self.reset("Q1")
        self.prepare(self.cid("Q1"))
        s = self._deny("xcheck-r2")
        f = self.folder
        deny = s["permissions"]["deny"]
        for rel in ("xcheck", "cfg-xcheck", "tmp/crosscheck/xcheck"):
            self.assertIn("Read(%s/%s/**)" % (f, rel), deny)
        args = holdout_kit._guard_hooks(s)[0][1]
        pairs = [args[i + 1] for i in range(len(args) - 1)
                 if args[i] == "--protect"]
        for rel in ("xcheck", "cfg-xcheck", "tmp/crosscheck/xcheck"):
            self.assertIn("%s/%s" % (f, rel), pairs)
        self.assertEqual(holdout_kit.xcheck_settings_problems(
            s, f, prior=[holdout_kit.xcheck_names(1)]), [])

    def test_generation_one_settings_untouched(self):
        path = os.path.join(self.folder, "xcheck", ".claude", "settings.json")
        before = sha(path)
        self.complete()
        self.reset("C3")
        self.prepare(self.cid("C3"))
        self.assertEqual(sha(path), before)

    def test_two_post_reveal_resets_share_generation_two(self):
        self.complete()
        self.reset("C1")
        self.reset("Q2")
        _, out1 = self.prepare(self.cid("C1"))
        _, out2 = self.prepare(self.cid("Q2"))
        self.assertIn("fresh cross-check workspace xcheck-r2", out1)
        self.assertNotIn("fresh cross-check workspace", out2)
        self.assertEqual(len(xids_in(self.folder, "xcheck-r2")), 2)
        gens = registry(self.folder)["generations"]
        self.assertEqual(len(gens), 2)
        self.assertEqual(sorted(gens[1]["cases"]),
                         sorted([self.cid("C1"), self.cid("Q2")]))

    def test_third_cycle_mints_generation_three(self):
        self.complete()
        self.reset("C1")
        complete_case(self.folder, self.cid("C1"))
        self.assertIsNotNone(registry(self.folder)["generations"][1]
                             ["revealed_at"])
        self.reset("C1")
        _, out = self.prepare(self.cid("C1"))
        self.assertIn("fresh cross-check workspace xcheck-r3", out)
        self.assertIn("bin/crosscheck-r3", out)
        s = self._deny("xcheck-r3")
        deny = s["permissions"]["deny"]
        for rel in ("xcheck", "cfg-xcheck", "xcheck-r2", "cfg-xcheck-r2"):
            self.assertIn("Read(%s/%s/**)" % (self.folder, rel), deny)
        self.assertEqual(ledger(self.folder, self.cid("C1"))["generation"], 3)

    def test_minting_stdout_names_launcher_and_no_verdict(self):
        self.complete()
        self.reset("C2")
        _, out = self.prepare(self.cid("C2"))
        self.assertIn("OK: fresh cross-check workspace xcheck-r2", out)
        self.assertIn("bin/crosscheck-r2", out)
        self.assertIn("Read CROSSCHECK-BRIEF.md and begin.", out)
        self.assertNotIn(key_of(self.folder, self.cid("C2"))["defect"], out)
        self.assertNotIn("C2", out)
        self.assertNotIn(self.cid("C2"), out)

    def test_unregistered_workspace_refused(self):
        self.complete()
        self.reset("C2")
        os.makedirs(os.path.join(self.folder, "xcheck-r2"))
        with self.assertRaises(KitError) as cm:
            self.prepare(self.cid("C2"))
        self.assertIn("unregistered cross-check workspace xcheck-r2; remove "
                      "it deliberately", str(cm.exception))
        self.assertEqual(len(registry(self.folder)["generations"]), 1)


# ================================================================ reveal


class TestReveal(SealCase):

    def setUp(self):
        super().setUp()
        self.mapping, _ = self.prepare()

    def xid(self, slot):
        return self.mapping[self.cid(slot)]

    def blind_path(self, slot):
        return os.path.join(packet(self.folder, self.cid(slot)), "blind.json")

    def assert_nothing_revealed(self):
        for c in self.ids.values():
            self.assertNotIn("blind_sha256", ledger(self.folder, c))
            self.assertFalse(os.path.exists(os.path.join(
                packet(self.folder, c), "revealed")))
        self.assertIsNone(registry(self.folder)["generations"][0]
                          ["revealed_at"])

    def test_all_or_nothing_refuses_with_one_missing(self):
        self.blinds(skip=("Q3",))
        with self.assertRaises(KitError) as cm:
            quiet(holdout_seal.reveal, self.folder, self.xid("C1"))
        msg = str(cm.exception)
        self.assertIn("workspace xcheck has packets without blind.json (1)",
                      msg)
        self.assertIn("all-or-nothing", msg)
        self.assert_nothing_revealed()

    def test_own_blind_missing_named(self):
        self.blinds(skip=("C2",))
        with self.assertRaises(KitError) as cm:
            quiet(holdout_seal.reveal, self.folder, self.xid("C2"))
        self.assertIn("blind.json is missing for %s" % self.xid("C2"),
                      str(cm.exception))
        self.assert_nothing_revealed()

    def test_reveal_one_xid_reveals_whole_workspace(self):
        self.blinds()
        cid, _ = quiet(holdout_seal.reveal, self.folder, self.xid("C1"))
        self.assertEqual(cid, self.cid("C1"))
        for c in self.ids.values():
            self.assertTrue(os.path.isdir(os.path.join(packet(self.folder, c),
                                                       "revealed")))
            self.assertIn("blind_sha256", ledger(self.folder, c))
        self.assertIsNotNone(registry(self.folder)["generations"][0]
                             ["revealed_at"])

    def test_ledger_freezes_hashes_from_current_files(self):
        self.blinds()
        quiet(holdout_seal.reveal, self.folder, self.xid("Q1"))
        for slot, c in self.ids.items():
            led = ledger(self.folder, c)
            self.assertEqual(led["blind_sha256"], sha(self.blind_path(slot)))
            self.assertRegex(led["reveal_token"], HEX16)
            self.assertTrue(led["revealed_at"])
            k = kdir(self.folder, c)
            self.assertEqual(led["revealed"], {
                "key.json": sha(os.path.join(k, "key.json")),
                "proof-results.json": sha(os.path.join(k,
                                                       "proof-results.json")),
                "proof": holdout_seal._proof_aggregate_sha256(
                    os.path.join(k, "proof"))})
            self.assertNotIn("resolution_sha256", led)
        tokens = {ledger(self.folder, c)["reveal_token"]
                  for c in self.ids.values()}
        self.assertEqual(len(tokens), 6)

    def test_revealed_files(self):
        self.blinds()
        quiet(holdout_seal.reveal, self.folder, self.xid("C3"))
        for c in self.ids.values():
            rev = os.path.join(packet(self.folder, c), "revealed")
            self.assertEqual(sorted(os.listdir(rev)),
                             ["REVEAL-TOKEN", "key.json", "proof",
                              "proof-results.json"])
            k = kdir(self.folder, c)
            self.assertEqual(sha(os.path.join(rev, "key.json")),
                             sha(os.path.join(k, "key.json")))
            self.assertEqual(sha(os.path.join(rev, "proof", "run")),
                             sha(os.path.join(k, "proof", "run")))
            with open(os.path.join(rev, "REVEAL-TOKEN"), encoding="utf-8") \
                    as fh:
                self.assertEqual(fh.read(),
                                 ledger(self.folder, c)["reveal_token"])

    def test_resolution_copied_and_bound_when_present(self):
        res = os.path.join(kdir(self.folder, self.cid("C2")), "resolution.md")
        with open(res, "w", encoding="utf-8") as fh:
            fh.write("owner evidence\n")
        self.blinds()
        quiet(holdout_seal.reveal, self.folder, self.xid("C2"))
        led = ledger(self.folder, self.cid("C2"))
        self.assertEqual(led["resolution_sha256"], sha(res))
        self.assertTrue(os.path.isfile(os.path.join(
            packet(self.folder, self.cid("C2")), "revealed", "resolution.md")))

    def test_invalid_json_refused(self):
        self.blinds()
        with open(self.blind_path("C1"), "w") as fh:
            fh.write("{not json")
        with self.assertRaises(KitError):
            quiet(holdout_seal.reveal, self.folder, self.xid("C1"))
        self.assert_nothing_revealed()

    def _bad_shape(self, slot, mutate):
        self.blinds()
        blind = load(self.blind_path(slot))
        mutate(blind)
        dump(self.blind_path(slot), blind)
        with self.assertRaises(KitError) as cm:
            quiet(holdout_seal.reveal, self.folder, self.xid("Q1"))
        self.assertIn("blind.json has the wrong shape", str(cm.exception))
        self.assert_nothing_revealed()

    def test_shape_missing_verdict(self):
        self._bad_shape("C1", lambda b: b.pop("verdict"))

    def test_shape_catch_null_category(self):
        self._bad_shape("C1", lambda b: b.update(defect_category=None))

    def test_shape_catch_unknown_category(self):
        self._bad_shape("C2", lambda b: b.update(defect_category="weird"))

    def test_shape_catch_null_location(self):
        self._bad_shape("C3", lambda b: b.update(location=None))

    def test_shape_quiet_with_location(self):
        self._bad_shape("Q2", lambda b: b.update(
            location={"file": "a", "line_start": 1, "line_end": 2}))

    def test_shape_quiet_with_category(self):
        self._bad_shape("Q3", lambda b: b.update(defect_category="other"))

    def test_shape_type_guess_not_a_slot(self):
        self._bad_shape("C1", lambda b: b.update(type_guess="C4"))

    def test_shape_verdict_and_type_class_disagree(self):
        self._bad_shape("C1", lambda b: b.update(type_guess="Q1"))

    def test_order_every_ledger_written_before_any_copy(self):
        self.blinds()
        with mock.patch.object(holdout_seal.shutil, "copy2",
                               side_effect=OSError("disk")):
            with self.assertRaises((KitError, OSError)):
                quiet(holdout_seal.reveal, self.folder, self.xid("C1"))
        for slot, c in self.ids.items():
            led = ledger(self.folder, c)
            self.assertEqual(led["blind_sha256"], sha(self.blind_path(slot)))
            self.assertRegex(led["reveal_token"], HEX16)
            rev = os.path.join(packet(self.folder, c), "revealed")
            if os.path.exists(rev):
                self.assertNotIn("REVEAL-TOKEN", os.listdir(rev))
        self.assertIsNotNone(registry(self.folder)["generations"][0]
                             ["revealed_at"])

    def test_second_reveal_refused(self):
        self.blinds()
        quiet(holdout_seal.reveal, self.folder, self.xid("C1"))
        with self.assertRaises(KitError) as cm:
            quiet(holdout_seal.reveal, self.folder, self.xid("C2"))
        self.assertIn("already revealed", str(cm.exception))

    def test_inputs_changed_refused(self):
        self.blinds()
        with open(os.path.join(cdir(self.folder, self.cid("C3")),
                               "change.diff"), "ab") as fh:
            fh.write(b"x")
        with self.assertRaises(KitError) as cm:
            quiet(holdout_seal.reveal, self.folder, self.xid("C1"))
        self.assertIn("sealed inputs changed since crosscheck-prepare "
                      "(change.diff)", str(cm.exception))
        self.assert_nothing_revealed()

    def test_unknown_xid_refused(self):
        self.blinds()
        with self.assertRaises(KitError):
            quiet(holdout_seal.reveal, self.folder, "X-00000000")
        self.assert_nothing_revealed()

    def test_reveal_after_seal_refused(self):
        self.blinds()
        dump(os.path.join(self.folder, "SEAL.json"), {})
        with self.assertRaises(KitError) as cm:
            quiet(holdout_seal.reveal, self.folder, self.xid("C1"))
        self.assertIn("already sealed", str(cm.exception))


class TestProofAggregate(SealCase):

    def setUp(self):
        super().setUp()
        self.proof = os.path.join(kdir(self.folder, self.cid("C1")), "proof")

    def test_deterministic(self):
        self.assertEqual(holdout_seal._proof_aggregate_sha256(self.proof),
                         holdout_seal._proof_aggregate_sha256(self.proof))
        self.assertRegex(holdout_seal._proof_aggregate_sha256(self.proof),
                         HEX64)

    def test_changes_on_one_byte(self):
        before = holdout_seal._proof_aggregate_sha256(self.proof)
        with open(os.path.join(self.proof, "run"), "ab") as fh:
            fh.write(b"#")
        self.assertNotEqual(holdout_seal._proof_aggregate_sha256(self.proof),
                            before)

    def test_changes_on_add_and_remove(self):
        before = holdout_seal._proof_aggregate_sha256(self.proof)
        extra = os.path.join(self.proof, "extra.sh")
        with open(extra, "w") as fh:
            fh.write("true\n")
        added = holdout_seal._proof_aggregate_sha256(self.proof)
        self.assertNotEqual(added, before)
        os.remove(extra)
        self.assertEqual(holdout_seal._proof_aggregate_sha256(self.proof),
                         before)
        os.rename(os.path.join(self.proof, "run"),
                  os.path.join(self.proof, "run2"))
        self.assertNotEqual(holdout_seal._proof_aggregate_sha256(self.proof),
                            before)

    def test_symlink_refused(self):
        os.symlink("/etc/hosts", os.path.join(self.proof, "link"))
        with self.assertRaises(KitError):
            holdout_seal._proof_aggregate_sha256(self.proof)


# ================================================================ reset


class TestReset(SealCase):

    def test_reset_archives_the_round_and_removes_the_packet(self):
        self.complete()
        c = self.cid("C2")
        old = ledger(self.folder, c)
        p = packet(self.folder, c)
        blind_sha = sha(os.path.join(p, "blind.json"))
        final_sha = sha(os.path.join(p, "final.json"))
        xid = self.reset("C2", "inputs-changed")
        self.assertEqual(xid, old["xid"])
        self.assertFalse(os.path.exists(p))
        for keep in ("xcheck", "cfg-xcheck"):
            self.assertTrue(os.path.isdir(os.path.join(self.folder, keep)))
        self.assertIn(c, registry(self.folder)["generations"][0]["cases"])
        led = ledger(self.folder, c)
        for field in ("xid", "generation", "workspace", "prepared_at",
                      "blind_sha256", "revealed_at", "reveal_token",
                      "revealed", "inputs"):
            self.assertNotIn(field, led)
        self.assertEqual(len(led["rounds"]), 1)
        r = led["rounds"][0]
        for field in ("xid", "generation", "workspace", "prepared_at",
                      "blind_sha256", "revealed_at", "reveal_token",
                      "revealed", "inputs"):
            self.assertEqual(r[field], old[field], field)
        self.assertEqual(r["reset_reason"], "inputs-changed")
        self.assertTrue(r["reset_at"])
        self.assertEqual(r["blind_sha256_at_reset"], blind_sha)
        self.assertEqual(r["final_sha256_at_reset"], final_sha)

    def test_reset_unrevealed_records_null_hashes(self):
        self.prepare()
        self.reset("Q2")
        r = ledger(self.folder, self.cid("Q2"))["rounds"][0]
        self.assertIsNone(r["blind_sha256_at_reset"])
        self.assertIsNone(r["final_sha256_at_reset"])

    def test_reset_never_touches_the_sealed_case(self):
        c = self.cid("C1")
        with open(os.path.join(kdir(self.folder, c), "resolution.md"),
                  "w") as fh:
            fh.write("owner evidence\n")
        self.complete()
        keep = os.path.join(kdir(self.folder, c))
        before_cases = file_hashes(cdir(self.folder, c))
        before_keys = {r: h for r, h in file_hashes(keep).items()
                       if r not in ("xcheck-ledger.json", "crosscheck.json")}
        self.reset("C1", "resolved")
        self.assertEqual(file_hashes(cdir(self.folder, c)), before_cases)
        after = {r: h for r, h in file_hashes(keep).items()
                 if r not in ("xcheck-ledger.json", "crosscheck.json")}
        self.assertEqual(after, before_keys)

    def test_reset_removes_crosscheck_json(self):
        self.complete()
        c = self.cid("Q1")
        shutil.copy(os.path.join(packet(self.folder, c), "final.json"),
                    os.path.join(kdir(self.folder, c), "crosscheck.json"))
        self.reset("Q1")
        self.assertFalse(os.path.exists(os.path.join(kdir(self.folder, c),
                                                     "crosscheck.json")))

    def test_bad_reason_refused(self):
        self.prepare()
        with self.assertRaises(KitError):
            self.reset("C1", "because")
        self.assertIn("xid", ledger(self.folder, self.cid("C1")))

    def test_reset_after_seal_refused(self):
        self.prepare()
        dump(os.path.join(self.folder, "SEAL.json"), {})
        with self.assertRaises(KitError) as cm:
            self.reset("C1")
        self.assertIn("already sealed", str(cm.exception))

    def test_reset_without_ledger_refused(self):
        with self.assertRaises(KitError) as cm:
            self.reset("C3")
        self.assertIn("cross-check not prepared for C3", str(cm.exception))

    def test_reset_twice_refused(self):
        self.prepare()
        self.reset("C3")
        with self.assertRaises(KitError) as cm:
            self.reset("C3")
        self.assertIn("cross-check not prepared for C3", str(cm.exception))


# ================================================================ CLI


class TestCliCrosscheck(SealCase):

    def test_cli_prepare(self):
        proc = self.cli("crosscheck-prepare")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = [ln for ln in proc.stdout.splitlines()
                 if ln.startswith("OK: prepared X-")]
        self.assertEqual(len(lines), 6)
        for ln in lines:
            self.assertTrue(ln.endswith(" in xcheck"), ln)
        self.assertEqual(len(xids_in(self.folder)), 6)

    def test_cli_reveal_ready(self):
        self.prepare()
        self.blinds()
        proc = self.cli("crosscheck-reveal", "--ready")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = [ln for ln in proc.stdout.splitlines()
                 if re.match(r"^OK: revealed X-[0-9a-f]{8}$", ln)]
        self.assertEqual(len(lines), 6)
        for c in self.ids.values():
            self.assertEqual(sorted(os.listdir(os.path.join(
                packet(self.folder, c), "revealed"))),
                ["REVEAL-TOKEN", "key.json", "proof", "proof-results.json"])
        for c in self.ids.values():
            self.assertNotIn(key_of(self.folder, c).get("defect", "@@"),
                             proc.stdout)

    def test_cli_reveal_ready_nothing(self):
        self.complete()
        proc = self.cli("crosscheck-reveal", "--ready")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("OK: nothing to reveal", proc.stdout)

    def test_cli_reveal_ready_skips_incomplete_workspace(self):
        self.prepare()
        self.blinds(skip=("C1", "Q2"))
        proc = self.cli("crosscheck-reveal", "--ready")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: workspace xcheck has packets without "
                      "blind.json (2); nothing revealed there", proc.stdout)
        for c in self.ids.values():
            self.assertNotIn("blind_sha256", ledger(self.folder, c))

    def test_cli_reveal_inputs_changed(self):
        self.prepare()
        self.blinds()
        with open(os.path.join(cdir(self.folder, self.cid("Q3")),
                               "change.diff"), "ab") as fh:
            fh.write(b"x")
        proc = self.cli("crosscheck-reveal", "--ready")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: ", proc.stdout)
        self.assertIn("sealed inputs changed since crosscheck-prepare",
                      proc.stdout)

    def test_cli_reveal_xid(self):
        mapping, _ = self.prepare()
        self.blinds()
        proc = self.cli("crosscheck-reveal", mapping[self.cid("C1")])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.count("OK: revealed X-"), 6)

    def test_cli_reveal_needs_xid_or_ready(self):
        proc = self.cli("crosscheck-reveal")
        self.assertEqual(proc.returncode, 2)

    def test_cli_reset_then_prepare_case(self):
        self.prepare()
        c = self.cid("C2")
        proc = self.cli("crosscheck-reset", c, "--reason", "inputs-changed")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("OK: cross-check reset for C2 (round 1 archived). "
                      "Next: bin/holdout crosscheck-prepare --case %s" % c,
                      proc.stdout)
        self.assertEqual(len(xids_in(self.folder)), 5)
        proc = self.cli("crosscheck-prepare", "--case", c)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(proc.stdout, r"OK: prepared X-[0-9a-f]{8} in xcheck")
        self.assertNotIn("fresh cross-check workspace", proc.stdout)
        self.assertEqual(len(xids_in(self.folder)), 6)

    def test_cli_prepare_case_mints_generation(self):
        self.complete()
        c = self.cid("Q2")
        self.assertEqual(self.cli("crosscheck-reset", c, "--reason",
                                  "owner").returncode, 0)
        proc = self.cli("crosscheck-prepare", "--case", c)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("fresh cross-check workspace xcheck-r2", proc.stdout)
        self.assertIn("bin/crosscheck-r2", proc.stdout)
        self.assertRegex(proc.stdout,
                         r"OK: prepared X-[0-9a-f]{8} in xcheck-r2")
        gens = registry(self.folder)["generations"]
        self.assertEqual([(g["gen"], g["workspace"],
                           g["revealed_at"] is not None, len(g["cases"]))
                          for g in gens],
                         [(1, "xcheck", True, 6), (2, "xcheck-r2", False, 1)])

    def test_cli_reset_bad_reason_is_usage_error(self):
        self.prepare()
        proc = self.cli("crosscheck-reset", self.cid("C1"), "--reason", "x")
        self.assertEqual(proc.returncode, 2)

    def test_cli_refuses_under_claudecode(self):
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        for args in (("crosscheck-prepare",),
                     ("crosscheck-reveal", "--ready"),
                     ("crosscheck-reset", self.cid("C1"), "--reason",
                      "owner"),
                     ("seal",)):
            proc = self.cli(*args, env=env)
            self.assertEqual(proc.returncode, 1, args)
            self.assertIn(holdout_kit.REFUSE_MSG, proc.stderr)
        self.assertFalse(os.path.exists(registry_path(self.folder)))


# ================================================================ module shape


def _imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module)
    return names


class TestModuleShape(unittest.TestCase):

    def _tree(self):
        with open(SEAL_PY, encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_import_set_is_exact(self):
        self.assertEqual(_imports(self._tree()),
                         {"json", "os", "secrets", "shutil", "sys", "time",
                          "holdout_kit", "holdout_validate",
                          "holdout_manifest"})

    def test_no_subprocess(self):
        tree = self._tree()
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        self.assertNotIn("subprocess", names)
        self.assertNotIn("subprocess", _imports(tree))

    def test_commands_registered(self):
        for name in ("crosscheck-prepare", "crosscheck-reveal",
                     "crosscheck-reset", "seal"):
            self.assertEqual(holdout_kit.COMMANDS[name], "holdout_seal")

    def test_exports(self):
        for name in ("prepare_crosscheck", "reveal", "reveal_workspace",
                     "reset_crosscheck", "seal_blockers", "agreement_problems",
                     "do_seal", "add_parser", "cmd", "DISAGREE_MSG",
                     "INPUTS_CHANGED_MSG", "STALE_WORKSPACE_MSG",
                     "LINE_SLACK", "WORKSPACES_RELPATH"):
            self.assertTrue(hasattr(holdout_seal, name), name)
        self.assertEqual(holdout_seal.LINE_SLACK, 5)
        self.assertEqual(holdout_seal.WORKSPACES_RELPATH,
                         "sealed/keys/xcheck-workspaces.json")


if __name__ == "__main__":
    unittest.main()
