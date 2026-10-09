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
        self.assertIn("cross-check folder already exists for",
                      str(cm.exception))
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


# ================================================================ agreement

CATCH_EXITS = {"base": 0, "changed": 1}
QUIET_EXITS = {"base": 0, "changed": 0}


def agreeing_args(slot):
    """(key, blind, final, recorded_exits) that agree for `slot`."""
    if slot in holdout_kit.CATCH_SLOTS:
        key = {"slot": slot, "class": "catch", "defect": "d",
               "location": {"file": "src/a.py", "line_start": 10,
                            "line_end": 20},
               "causal_failure": "c", "causal_failure_category": "injection"}
        blind = {"verdict": "catch", "type_guess": slot,
                 "location": {"file": "src/a.py", "line_start": 10,
                              "line_end": 20},
                 "defect_category": "injection", "reasoning": "r"}
        exits, quiet_ok = dict(CATCH_EXITS), None
    else:
        key = {"slot": slot, "class": "quiet",
               "expected_quiet_rationale": "r", "supported_behavior": "b",
               "exposure_check": "e"}
        blind = {"verdict": "quiet", "type_guess": slot, "location": None,
                 "defect_category": None, "reasoning": "r"}
        exits = dict(QUIET_EXITS)
        quiet_ok = {"supported_behavior": True, "exposure_check": True}
    final = {"reveal_token": "0" * 16, "type_agrees": True,
             "defect_agrees": True, "causal_failure_agrees": True,
             "proof_agrees": True, "proof_rerun_exit": dict(exits),
             "quiet_confirmed": quiet_ok, "notes": "n"}
    return key, blind, final, dict(exits)


def ap(slot, key_edit=None, blind_edit=None, final_edit=None, **kw):
    key, blind, final, rec = agreeing_args(slot)
    for obj, edit in ((key, key_edit), (blind, blind_edit),
                      (final, final_edit)):
        if edit is not None:
            edit(obj)
    kw.setdefault("recorded_exits", rec)
    return holdout_seal.agreement_problems(slot, key, blind, final, **kw)


def _loc(start, end, file="src/a.py"):
    return lambda b: b.update(location={"file": file, "line_start": start,
                                        "line_end": end})


class TestAgreementRule(unittest.TestCase):

    def test_agreeing_every_slot(self):
        for slot in holdout_kit.SLOTS:
            self.assertEqual(ap(slot), [], slot)

    def test_c3_as_c1(self):
        self.assertEqual(ap("C1", blind_edit=lambda b: b.update(
            type_guess="C3")), ["type"])

    def test_different_defect_same_file(self):
        self.assertEqual(ap("C2", blind_edit=_loc(200, 210)),
                         ["defect location"])

    def test_overlap_at_upper_slack_edge(self):
        self.assertEqual(ap("C1", blind_edit=_loc(25, 30)), [])
        self.assertEqual(ap("C1", blind_edit=_loc(26, 30)),
                         ["defect location"])

    def test_overlap_at_lower_slack_edge(self):
        self.assertEqual(ap("C1", blind_edit=_loc(1, 5)), [])
        self.assertEqual(ap("C1", blind_edit=_loc(1, 4)),
                         ["defect location"])

    def test_different_file(self):
        self.assertEqual(ap("C1", blind_edit=_loc(10, 20, "src/b.py")),
                         ["defect location"])

    def test_category_mismatch(self):
        self.assertEqual(ap("C3", blind_edit=lambda b: b.update(
            defect_category="logic-error")), ["causal-failure category"])

    def test_other_never_agrees(self):
        self.assertEqual(ap("C1", key_edit=lambda k: k.update(
            causal_failure_category="other"),
            blind_edit=lambda b: b.update(defect_category="other")),
            ["category other"])

    def test_other_against_a_real_category(self):
        self.assertEqual(ap("C1", blind_edit=lambda b: b.update(
            defect_category="other")),
            ["causal-failure category", "category other"])

    def test_quiet_slot_with_catch_verdict(self):
        self.assertEqual(ap("Q2", blind_edit=lambda b: b.update(
            verdict="catch", type_guess="C1",
            location={"file": "x", "line_start": 1, "line_end": 2},
            defect_category="logic-error")), ["type"])

    def test_catch_slot_with_quiet_verdict(self):
        self.assertEqual(ap("C2", blind_edit=lambda b: b.update(
            verdict="quiet", type_guess="Q1", location=None,
            defect_category=None)), ["type"])

    def test_quiet_exposure_check_false(self):
        self.assertEqual(ap("Q1", final_edit=lambda f: f.update(
            quiet_confirmed={"supported_behavior": True,
                             "exposure_check": False})),
            ["quiet confirmation"])

    def test_quiet_confirmed_null(self):
        self.assertEqual(ap("Q3", final_edit=lambda f: f.update(
            quiet_confirmed=None)), ["quiet confirmation"])

    def test_each_flag_false_is_final_flags(self):
        for flag in ("type_agrees", "defect_agrees", "causal_failure_agrees",
                     "proof_agrees"):
            with self.subTest(flag=flag):
                self.assertIn("final flags", ap("C1", final_edit=lambda f:
                                                f.update({flag: False})))

    def test_truthy_non_bool_flag_is_final_flags(self):
        self.assertIn("final flags", ap("C2", final_edit=lambda f: f.update(
            type_agrees="yes")))

    def test_final_not_an_object(self):
        key, blind, _, rec = agreeing_args("C1")
        self.assertIn("final flags", holdout_seal.agreement_problems(
            "C1", key, blind, None, recorded_exits=rec))

    def test_defect_flag_cannot_override_location(self):
        self.assertEqual(ap("C1", blind_edit=_loc(200, 210),
                            final_edit=lambda f: f.update(
                                defect_agrees=True)),
                         ["defect location"])

    def test_type_flag_cannot_override_type(self):
        self.assertEqual(ap("C1", blind_edit=lambda b: b.update(
            type_guess="C2"), final_edit=lambda f: f.update(
            type_agrees=True)), ["type"])

    def test_malformed_blind_location_never_agrees(self):
        self.assertEqual(ap("C1", blind_edit=lambda b: b.update(
            location={"file": "src/a.py", "line_start": "10",
                      "line_end": 20})), ["defect location"])


class TestProofExits(unittest.TestCase):

    def test_agreeing(self):
        self.assertEqual(ap("C1"), [])
        self.assertEqual(ap("Q1"), [])

    def test_catch_rerun_passes_on_both_trees(self):
        self.assertEqual(ap("C1", final_edit=lambda f: f.update(
            proof_rerun_exit={"base": 0, "changed": 0}, proof_agrees=True)),
            ["proof exits"])

    def test_equal_exits_wrong_pattern(self):
        both = {"base": 1, "changed": 1}
        self.assertEqual(ap("C2", final_edit=lambda f: f.update(
            proof_rerun_exit=dict(both)), recorded_exits=dict(both)),
            ["proof exits"])

    def test_different_nonzero_changed_exit(self):
        self.assertEqual(ap("C3", final_edit=lambda f: f.update(
            proof_rerun_exit={"base": 0, "changed": 2})), ["proof exits"])

    def test_quiet_rerun_fails_on_changed(self):
        self.assertEqual(ap("Q1", final_edit=lambda f: f.update(
            proof_rerun_exit={"base": 0, "changed": 1})), ["proof exits"])

    def test_quiet_both_zero(self):
        self.assertEqual(ap("Q2", final_edit=lambda f: f.update(
            proof_rerun_exit={"base": 0, "changed": 0})), [])

    def test_missing_recorded_exits_fail_closed(self):
        self.assertEqual(ap("C1", recorded_exits=None), ["proof exits"])

    def test_default_recorded_exits_fail_closed(self):
        key, blind, final, _ = agreeing_args("Q3")
        self.assertEqual(holdout_seal.agreement_problems("Q3", key, blind,
                                                         final),
                         ["proof exits"])

    def test_recorded_exits_strings_and_bools(self):
        for rec in ({"base": "0", "changed": 1},
                    {"base": False, "changed": True}):
            with self.subTest(rec=rec):
                self.assertEqual(ap("C1", recorded_exits=rec),
                                 ["proof exits"])

    def test_final_exit_bools_are_final_flags(self):
        self.assertEqual(ap("C1", final_edit=lambda f: f.update(
            proof_rerun_exit={"base": False, "changed": True})),
            ["final flags"])

    def test_runnable_rerun_null_is_final_flags(self):
        self.assertIn("final flags", ap("C2", final_edit=lambda f: f.update(
            proof_rerun_exit=None)))

    def test_proof_agrees_false_with_matching_exits(self):
        self.assertEqual(ap("C1", final_edit=lambda f: f.update(
            proof_agrees=False)), ["final flags"])

    def test_proof_agrees_cannot_cover_exits(self):
        self.assertEqual(ap("Q1", final_edit=lambda f: f.update(
            proof_agrees=True, proof_rerun_exit={"base": 1, "changed": 0})),
            ["proof exits"])

    def test_recorded_exits_helper(self):
        rec = holdout_seal._recorded_exits
        run = {"runnable": True, "base": {"exit": 0}, "changed": {"exit": 3}}
        self.assertEqual(rec(run), {"base": 0, "changed": 3})
        self.assertIsNone(rec({"runnable": False, "nonrunnable_reason": "x",
                               "manual_evidence": "y"}))
        self.assertIsNone(rec({"runnable": True, "base": {"exit": True},
                               "changed": {"exit": 1}}))
        self.assertIsNone(rec({"runnable": True, "base": {}}))
        self.assertIsNone(rec({"runnable": "yes", "base": {"exit": 0},
                               "changed": {"exit": 1}}))
        self.assertIsNone(rec(None))
        self.assertIsNone(rec([1, 2]))


class TestPureNonRunnable(unittest.TestCase):

    def _nr(self, slot="C2", **kw):
        kw.setdefault("runnable", False)
        kw.setdefault("recorded_exits", {"base": 0, "changed": 0})
        final_edit = kw.pop("final_edit", None)

        def edit(f):
            f.update(proof_rerun_exit=None, proof_agrees=True)
            if final_edit:
                final_edit(f)
        return ap(slot, final_edit=edit, **kw)

    def test_unresolved_blocks(self):
        self.assertEqual(self._nr(resolution_bound=False),
                         ["non-runnable proof"])

    def test_bound_resolution_passes(self):
        self.assertEqual(self._nr(resolution_bound=True), [])

    def test_invented_exits_block(self):
        self.assertEqual(self._nr(resolution_bound=True, final_edit=lambda f:
                                  f.update(proof_rerun_exit={"base": 0,
                                                             "changed": 1})),
                         ["non-runnable proof"])

    def test_resolution_does_not_override_disagreement(self):
        self.assertIn("final flags", self._nr(
            resolution_bound=True,
            final_edit=lambda f: f.update(proof_agrees=False)))

    def test_quiet_non_runnable_bound(self):
        self.assertEqual(self._nr("Q2", resolution_bound=True), [])

    def test_recorded_exits_ignored(self):
        self.assertEqual(self._nr(resolution_bound=True,
                                  recorded_exits=None), [])


# ================================================================ seal gate


class CompletedCase(SealCase):
    """A holdout whose six cases went through an agreeing cross-check."""

    COMPLETE = True

    def setUp(self):
        super().setUp()
        if self.COMPLETE:
            self.complete()

    def blockers(self, **kw):
        return holdout_seal.seal_blockers(self.folder, **kw)

    def seal(self):
        return quiet(holdout_seal.do_seal, self.folder)[0]

    def assertSeals(self):
        self.assertEqual(self.blockers(), [])
        self.seal()
        self.assertTrue(os.path.isfile(os.path.join(self.folder,
                                                    "SEAL.json")))

    def assertBlocked(self, expected=None, contains=None):
        got = self.blockers()
        if expected is not None:
            self.assertEqual(got, expected)
        if contains is not None:
            self.assertTrue(any(contains in b for b in got), got)
        with self.assertRaises(KitError):
            self.seal()
        self.assertFalse(os.path.exists(os.path.join(self.folder,
                                                     "SEAL.json")))
        return got

    def pkt(self, slot):
        return packet(self.folder, self.cid(slot))

    def edit_json(self, path, fn):
        obj = load(path)
        fn(obj)
        dump(path, obj)

    def refreeze_blind(self, slot):
        c = self.cid(slot)
        self.edit_json(ledger_path(self.folder, c), lambda d: d.update(
            blind_sha256=sha(os.path.join(self.pkt(slot), "blind.json"))))

    def append(self, path, data=b"x"):
        with open(path, "ab") as fh:
            fh.write(data)


class TestSealHappyPath(CompletedCase):

    def test_completed_fixture_has_no_blockers(self):
        self.assertEqual(self.blockers(), [])

    def test_do_seal_writes_everything(self):
        seal = self.seal()
        f = self.folder
        on_disk = load(os.path.join(f, "SEAL.json"))
        self.assertEqual(on_disk, seal)
        self.assertEqual(holdout_manifest.public_shape_problems(on_disk), [])
        self.assertEqual(sorted(on_disk["cases"]), sorted(self.ids.values()))
        self.assertTrue(os.path.isfile(os.path.join(f, "sealed",
                                                    "INVENTORY.json")))
        self.assertTrue(os.path.isfile(os.path.join(f, "sealed", "HMAC-KEY")))
        for c in self.ids.values():
            self.assertEqual(sha(os.path.join(kdir(f, c), "crosscheck.json")),
                             sha(os.path.join(packet(f, c), "final.json")))
        inv = load(os.path.join(f, "sealed", "INVENTORY.json"))["files"]
        self.assertIn("keys/" + holdout_kit.XCHECK_REGISTRY, inv)

    def test_seal_twice_refused(self):
        self.seal()
        with self.assertRaises(KitError) as cm:
            self.seal()
        self.assertIn("already sealed (SEAL.json exists); delete it "
                      "deliberately if you must re-seal", str(cm.exception))

    def test_no_partial_seal_when_build_fails(self):
        with mock.patch.object(holdout_manifest, "build_seal",
                               side_effect=KitError("boom")):
            with self.assertRaises(KitError):
                self.seal()
        self.assertFalse(os.path.exists(os.path.join(self.folder,
                                                     "SEAL.json")))

    def test_no_partial_seal_when_inventory_fails(self):
        with mock.patch.object(holdout_manifest, "write_inventory",
                               side_effect=KitError("boom")):
            with self.assertRaises(KitError):
                self.seal()
        self.assertFalse(os.path.exists(os.path.join(self.folder,
                                                     "SEAL.json")))

    def test_seal_prints_no_key_text(self):
        _, out = quiet(holdout_seal.do_seal, self.folder)
        for c in self.ids.values():
            key = key_of(self.folder, c)
            for field in ("defect", "causal_failure",
                          "expected_quiet_rationale"):
                if key.get(field):
                    self.assertNotIn(key[field], out)


class TestSealBlockers(CompletedCase):

    def test_validation_failure_blocks(self):
        prov = os.path.join(kdir(self.folder, self.cid("Q2")),
                            "provenance.json")
        self.edit_json(prov, lambda p: p["search"].update(budget=24))
        got = self.assertBlocked()
        self.assertTrue(any(b.startswith("validation failed: ")
                            for b in got), got)

    def test_validate_runs_with_proofs(self):
        with mock.patch.object(holdout_validate, "validate_folder",
                               wraps=holdout_validate.validate_folder) as spy:
            self.blockers()
        self.assertEqual(spy.call_count, 1)
        args, kwargs = spy.call_args
        self.assertEqual(args, (self.folder,))
        self.assertFalse(kwargs.get("skip_proofs", False))

    def test_given_checks_are_used(self):
        bad = [holdout_validate.Check("proofs", False, "x")]
        with mock.patch.object(holdout_validate, "validate_folder") as spy:
            got = self.blockers(checks=bad)
        spy.assert_not_called()
        self.assertEqual(got, ["validation failed: proofs"])

    def test_case_without_ledger(self):
        os.remove(ledger_path(self.folder, self.cid("C1")))
        self.assertBlocked(["cross-check not prepared for C1"])

    def test_blind_edited_after_reveal(self):
        self.append(os.path.join(self.pkt("C1"), "blind.json"), b" ")
        self.assertBlocked(["C1: blind verdict changed after reveal"])

    def test_blind_missing_after_reveal(self):
        os.remove(os.path.join(self.pkt("Q3"), "blind.json"))
        self.assertBlocked(["Q3: blind verdict changed after reveal"])

    def test_blind_wrong_shape(self):
        self.edit_json(os.path.join(self.pkt("C2"), "blind.json"),
                       lambda b: b.update(defect_category="weird"))
        self.refreeze_blind("C2")
        self.assertBlocked(["C2: blind verdict has the wrong shape"])

    def test_token_mismatch(self):
        def flip(f):
            t = f["reveal_token"]
            f["reveal_token"] = ("1" if t[0] != "1" else "2") + t[1:]
        self.edit_json(os.path.join(self.pkt("Q2"), "final.json"), flip)
        self.assertBlocked(["Q2: final.json is not bound to this reveal "
                            "(reveal_token mismatch)"])

    def test_token_missing(self):
        self.edit_json(os.path.join(self.pkt("C3"), "final.json"),
                       lambda f: f.pop("reveal_token"))
        self.assertBlocked(["C3: final.json is not bound to this reveal "
                            "(reveal_token mismatch)"])

    def test_final_missing(self):
        os.remove(os.path.join(self.pkt("C2"), "final.json"))
        self.assertBlocked(["C2: final.json missing"])

    def test_final_unreadable(self):
        with open(os.path.join(self.pkt("C2"), "final.json"), "w") as fh:
            fh.write("{oops")
        self.assertBlocked(contains="C2: final.json")

    def test_every_case_reported(self):
        os.remove(os.path.join(self.pkt("C2"), "final.json"))
        self.append(os.path.join(self.pkt("Q1"), "blind.json"), b" ")
        got = self.assertBlocked()
        self.assertEqual(sorted(got), ["C2: final.json missing",
                                       "Q1: blind verdict changed after "
                                       "reveal"])


class TestSealNotRevealed(CompletedCase):

    COMPLETE = False

    def test_not_yet_revealed(self):
        self.prepare()
        self.blinds()
        got = self.assertBlocked()
        self.assertEqual(sorted(got), sorted("%s: not yet revealed" % s
                                             for s in self.ids))

    def test_nothing_prepared(self):
        got = self.assertBlocked()
        self.assertEqual(sorted(got), sorted("cross-check not prepared for %s"
                                             % s for s in self.ids))


class TestSealRetired(CompletedCase):

    def relabel(self, slot):
        """Retire `slot`, then re-file it byte-for-byte under a fresh ID
        (ledger and verdict included; case.json and the registry updated so
        every other check still holds)."""
        f = self.folder
        old = self.cid(slot)
        holdout_manifest.retire_case(f, old, "owner")
        new = holdout_kit.new_case_id()
        for part in ("cases", "keys"):
            shutil.copytree(os.path.join(f, "sealed", part, old),
                            os.path.join(f, "sealed", part, new))
            shutil.rmtree(os.path.join(f, "sealed", part, old))
        self.edit_json(os.path.join(cdir(f, new), "case.json"),
                       lambda d: d.update(id=new))

        def swap(reg):
            for g in reg["generations"]:
                g["cases"] = [new if c == old else c for c in g["cases"]]
        self.edit_json(registry_path(f), swap)
        self.ids[slot] = new
        return new

    def test_relabeled_retired_case_blocks(self):
        new = self.relabel("C2")
        self.assertEqual([c for c in holdout_validate.validate_folder(
            self.folder) if not c.ok], [])
        got = self.assertBlocked()
        self.assertEqual(got, holdout_manifest.retired_problems(self.folder))
        self.assertEqual(len(got), 1)
        self.assertTrue(got[0].startswith("case C2 (%s) reuses material "
                                          "retired on " % new), got)

    def test_retired_listed_before_crosscheck_blockers(self):
        self.relabel("Q1")
        os.remove(os.path.join(self.pkt("C3"), "final.json"))
        got = self.assertBlocked()
        self.assertIn("reuses material retired", got[0])
        self.assertEqual(got[1:], ["C3: final.json missing"])

    def test_mutant_retired_blocker(self):
        self.relabel("C2")
        with mock.patch.object(holdout_seal, "_blocker_retired",
                               return_value=None):
            self.assertSeals()


class TestSealBinding(CompletedCase):

    def expect(self, slot, members):
        return [holdout_seal.INPUTS_CHANGED_MSG % (slot, members)]

    def test_change_diff(self):
        self.append(os.path.join(cdir(self.folder, self.cid("C1")),
                                 "change.diff"))
        self.assertBlocked(self.expect("C1", "change.diff"))

    def test_base_tar(self):
        tar_path = os.path.join(cdir(self.folder, self.cid("Q2")), "base.tar")
        tree = os.path.join(self.tmp, "retar")
        holdout_kit.safe_extract_tar(tar_path, tree)
        with open(os.path.join(tree, "EXTRA.txt"), "w") as fh:
            fh.write("extra\n")
        with tarfile.open(tar_path, "w") as tar:
            for rel in holdout_kit.walk_regular(tree):
                tar.add(os.path.join(tree, rel), arcname=rel)
        self.assertBlocked(self.expect("Q2", "base.tar"))

    def test_key_json(self):
        self.edit_json(os.path.join(kdir(self.folder, self.cid("C2")),
                                    "key.json"),
                       lambda k: k["location"].update(line_end=9))
        self.assertBlocked(self.expect("C2", "key.json"))

    def test_proof_results(self):
        self.edit_json(os.path.join(kdir(self.folder, self.cid("Q3")),
                                    "proof-results.json"),
                       lambda r: r["base"].update(
                           ran_at="2026-01-02T00:00:00Z"))
        self.assertBlocked(self.expect("Q3", "proof-results.json"))

    def test_proof_run(self):
        self.append(os.path.join(kdir(self.folder, self.cid("C3")), "proof",
                                 "run"), b"# reviewed\n")
        self.assertBlocked(self.expect("C3", "proof"))

    def test_proof_extra_file(self):
        with open(os.path.join(kdir(self.folder, self.cid("Q1")), "proof",
                               "extra.sh"), "w") as fh:
            fh.write("true\n")
        self.assertBlocked(self.expect("Q1", "proof"))

    def test_case_types(self):
        self.append(os.path.join(self.folder, "kit", "CASE-TYPES.md"),
                    b"\nedited\n")
        got = self.assertBlocked()
        self.assertEqual(sorted(got), sorted(
            holdout_seal.INPUTS_CHANGED_MSG % (s, "CASE-TYPES.md")
            for s in self.ids))

    def test_several_members_named_together(self):
        c = self.cid("C1")
        self.append(os.path.join(cdir(self.folder, c), "change.diff"))
        self.append(os.path.join(kdir(self.folder, c), "proof", "run"),
                    b"# x\n")
        self.edit_json(os.path.join(kdir(self.folder, c),
                                    "proof-results.json"),
                       lambda r: r["changed"].update(
                           ran_at="2026-01-03T00:00:00Z"))
        self.assertBlocked(self.expect(
            "C1", "change.diff, proof-results.json, proof"))

    def test_revalidating_does_not_clear(self):
        self.append(os.path.join(kdir(self.folder, self.cid("C3")), "proof",
                                 "run"), b"# reviewed\n")
        self.assertEqual([c for c in holdout_validate.validate_folder(
            self.folder) if not c.ok], [])
        self.assertBlocked(self.expect("C3", "proof"))

    def test_reset_and_fresh_round_clears(self):
        c = self.cid("C1")
        self.append(os.path.join(cdir(self.folder, c), "change.diff"))
        self.assertBlocked(self.expect("C1", "change.diff"))
        self.reset("C1", "inputs-changed")
        complete_case(self.folder, c)
        self.assertEqual(ledger(self.folder, c)["generation"], 2)
        self.assertSeals()

    def test_mutant_inputs_bound(self):
        self.edit_json(os.path.join(kdir(self.folder, self.cid("Q3")),
                                    "proof-results.json"),
                       lambda r: r["base"].update(
                           ran_at="2026-01-02T00:00:00Z"))
        with mock.patch.object(holdout_seal, "_blocker_inputs_bound",
                               return_value=None):
            self.assertSeals()


class TestSealWorkspaceFresh(CompletedCase):

    def setUp(self):
        super().setUp()
        self.reset("Q1", "owner")
        complete_case(self.folder, self.cid("Q1"))
        self.lp = ledger_path(self.folder, self.cid("Q1"))

    def test_honest_second_generation_seals(self):
        led = ledger(self.folder, self.cid("Q1"))
        self.assertEqual((led["generation"], led["workspace"]),
                         (2, "xcheck-r2"))
        self.assertSeals()

    def test_ledger_moved_to_burned_workspace(self):
        self.edit_json(self.lp, lambda d: d.update(generation=1,
                                                   workspace="xcheck"))
        self.assertBlocked([holdout_seal.STALE_WORKSPACE_MSG
                            % ("Q1", 2, "xcheck")])

    def test_packet_prepared_after_reveal(self):
        def early(reg):
            reg["generations"][1]["revealed_at"] = \
                "2000-01-01T00:00:00.000000Z"
        self.edit_json(registry_path(self.folder), early)
        self.assertBlocked(["Q1: packet prepared after its workspace was "
                            "revealed"])

    def test_generation_missing(self):
        self.edit_json(self.lp, lambda d: d.pop("generation"))
        self.assertBlocked(["Q1: cross-check round is not bound to a "
                            "registered workspace"])

    def test_workspace_not_in_registry(self):
        self.edit_json(self.lp, lambda d: d.update(workspace="xcheck-r7"))
        self.assertBlocked(["Q1: cross-check round is not bound to a "
                            "registered workspace"])

    def test_registry_revealed_at_cleared(self):
        def clear(reg):
            reg["generations"][1]["revealed_at"] = None
        self.edit_json(registry_path(self.folder), clear)
        self.assertBlocked(["Q1: cross-check round is not bound to a "
                            "registered workspace"])

    def test_registry_missing(self):
        os.remove(registry_path(self.folder))
        got = self.assertBlocked()
        self.assertEqual(sorted(got), sorted(
            "%s: cross-check round is not bound to a registered workspace"
            % s for s in self.ids))

    def test_current_generation_not_newer_than_archived_reveal(self):
        led = ledger(self.folder, self.cid("Q1"))
        fake = {"xid": "X-00000000", "generation": 2,
                "workspace": "xcheck-r2", "revealed_at": led["revealed_at"],
                "reset_reason": "owner"}
        self.edit_json(self.lp, lambda d: d["rounds"].append(fake))
        self.assertBlocked([holdout_seal.STALE_WORKSPACE_MSG
                            % ("Q1", led["round"], "xcheck-r2")])

    def test_case_not_registered_in_its_workspace(self):
        def drop(reg):
            reg["generations"][1]["cases"].remove(self.cid("Q1"))
        self.edit_json(registry_path(self.folder), drop)
        self.assertBlocked(["Q1: packet is not registered in workspace "
                            "xcheck-r2"])

    def _move_to_burned_workspace(self):
        old = self.pkt("Q1")
        os.rename(old, os.path.join(self.folder, "xcheck",
                                    os.path.basename(old)))
        self.edit_json(self.lp, lambda d: d.update(generation=1,
                                                   workspace="xcheck"))

    def test_stale_packet_really_in_burned_workspace(self):
        self._move_to_burned_workspace()
        self.assertBlocked([holdout_seal.STALE_WORKSPACE_MSG
                            % ("Q1", 2, "xcheck")])

    def test_mutant_workspace_fresh(self):
        self._move_to_burned_workspace()
        with mock.patch.object(holdout_seal, "_blocker_workspace_fresh",
                               return_value=None):
            self.assertSeals()


class TestSealAgreement(CompletedCase):

    COMPLETE = False

    def disagree(self, slot, parts, **kw):
        self.complete(**kw)
        return self.assertBlocked([holdout_seal.DISAGREE_MSG
                                   % (slot, parts)])

    @staticmethod
    def only(slot, **fields):
        def mutate(s, d):
            if s == slot:
                d.update(fields)
        return mutate

    def test_8a_c3_as_c1(self):
        self.disagree("C1", "type",
                      mutate_blind=self.only("C1", type_guess="C3"))

    def test_8b_different_defect_same_file(self):
        def far(s, d):
            if s == "C2":
                d["location"] = dict(d["location"], line_start=200,
                                     line_end=210)
        self.disagree("C2", "defect location", mutate_blind=far)

    def test_8c_different_file(self):
        def other_file(s, d):
            if s == "C1":
                d["location"] = dict(d["location"], file="mod_other.sh")
        self.disagree("C1", "defect location", mutate_blind=other_file)

    def test_8d_category(self):
        self.disagree("C3", "causal-failure category",
                      mutate_blind=self.only("C3",
                                             defect_category="injection"))

    def test_8e_key_and_blind_other(self):
        self.edit_json(os.path.join(kdir(self.folder, self.cid("C1")),
                                    "key.json"),
                       lambda k: k.update(causal_failure_category="other"))
        self.disagree("C1", "category other")

    def test_8f_catch_slot_judged_quiet(self):
        self.disagree("C1", "type", mutate_blind=self.only(
            "C1", verdict="quiet", type_guess="Q1", location=None,
            defect_category=None))

    def test_8g_quiet_slot_judged_catch(self):
        self.disagree("Q2", "type", mutate_blind=self.only(
            "Q2", verdict="catch", type_guess="C1",
            location={"file": "mod_q2.sh", "line_start": 3, "line_end": 5},
            defect_category="logic-error"))

    def test_8h_quiet_confirmation(self):
        self.disagree("Q1", "quiet confirmation", mutate_final=self.only(
            "Q1", quiet_confirmed={"supported_behavior": True,
                                   "exposure_check": False}))

    def test_8i_proof_agrees_false(self):
        self.disagree("C3", "final flags",
                      mutate_final=self.only("C3", proof_agrees=False))

    def test_8j_defect_agrees_false(self):
        self.disagree("C1", "final flags",
                      mutate_final=self.only("C1", defect_agrees=False))

    def test_8k_type_flag_cannot_override(self):
        self.disagree("C1", "type",
                      mutate_blind=self.only("C1", type_guess="C2"),
                      mutate_final=self.only("C1", type_agrees=True))

    def test_mutant_agreement(self):
        self.complete(mutate_blind=self.only("C1", type_guess="C3"))
        with mock.patch.object(holdout_seal, "agreement_problems",
                               return_value=[]):
            self.assertSeals()


class TestSealProofExits(CompletedCase):

    COMPLETE = False

    def test_8l_catch_rerun_passed_on_both_trees(self):
        self.complete(mutate_final=TestSealAgreement.only(
            "C2", proof_rerun_exit={"base": 0, "changed": 0},
            proof_agrees=True))
        self.assertBlocked([holdout_seal.DISAGREE_MSG % ("C2", "proof exits")])

    def test_8m_quiet_rerun_failed_on_changed(self):
        self.complete(mutate_final=TestSealAgreement.only(
            "Q1", proof_rerun_exit={"base": 0, "changed": 1}))
        self.assertBlocked([holdout_seal.DISAGREE_MSG % ("Q1", "proof exits")])

    def test_8n_rerun_differs_from_record(self):
        self.complete(mutate_final=TestSealAgreement.only(
            "C3", proof_rerun_exit={"base": 0, "changed": 2}))
        self.assertBlocked([holdout_seal.DISAGREE_MSG % ("C3", "proof exits")])

    def test_8o_recorded_exits_wrong_is_a_validation_failure(self):
        path = os.path.join(kdir(self.folder, self.cid("C1")),
                            "proof-results.json")
        self.edit_json(path, lambda r: (r["base"].update(exit=1),
                                        r["changed"].update(exit=1)))
        self.complete()
        got = self.assertBlocked()
        self.assertIn("validation failed: proofs", got)

    def test_8p_wiring_passes_recorded_exits(self):
        self.complete()
        with mock.patch.object(holdout_seal, "agreement_problems",
                               wraps=holdout_seal.agreement_problems) as spy:
            self.assertEqual(self.blockers(), [])
        self.assertEqual(spy.call_count, 6)
        seen = {}
        for call in spy.call_args_list:
            slot = call.args[0]
            seen[slot] = call.kwargs
        for slot, c in self.ids.items():
            pr = load(os.path.join(kdir(self.folder, c),
                                   "proof-results.json"))
            self.assertEqual(seen[slot]["recorded_exits"],
                             {"base": pr["base"]["exit"],
                              "changed": pr["changed"]["exit"]})
            self.assertIs(seen[slot]["runnable"], True)
            self.assertIs(seen[slot]["resolution_bound"], False)

    def test_8q_mutants(self):
        self.complete(mutate_final=TestSealAgreement.only(
            "C2", proof_rerun_exit={"base": 0, "changed": 0}))
        # Recorded exits forged to equal the rerun: equality now holds for
        # C2, and the slot pattern alone still blocks it.
        with mock.patch.object(holdout_seal, "_recorded_exits",
                               return_value={"base": 0, "changed": 0}):
            self.assertIn(holdout_seal.DISAGREE_MSG % ("C2", "proof exits"),
                          self.blockers())
        with mock.patch.object(holdout_seal, "agreement_problems",
                               return_value=[]):
            self.assertSeals()


class TestNonRunnable(CompletedCase):
    """C2's proof recorded as non-runnable before the cross-check."""

    COMPLETE = False

    def setUp(self):
        super().setUp()
        self.c = self.cid("C2")
        dump(os.path.join(kdir(self.folder, self.c), "proof-results.json"),
             {"runnable": False, "nonrunnable_reason": "needs a live service",
              "manual_evidence": "fixture manual evidence"})
        self.res = os.path.join(kdir(self.folder, self.c), "resolution.md")

    def resolve(self):
        with open(self.res, "w", encoding="utf-8") as fh:
            fh.write("owner decision with evidence\n")
        self.reset("C2", "resolved")
        complete_case(self.folder, self.c)

    def test_validate_still_passes(self):
        self.assertEqual([c for c in holdout_validate.validate_folder(
            self.folder) if not c.ok], [])

    def test_blocked_without_resolution(self):
        self.complete()
        self.assertIsNone(agreeing_final(self.folder, self.c)
                          ["proof_rerun_exit"])
        self.assertBlocked([holdout_seal.DISAGREE_MSG
                            % ("C2", "non-runnable proof")])

    def test_runnable_flag_wiring(self):
        self.complete()
        with mock.patch.object(holdout_seal, "agreement_problems",
                               wraps=holdout_seal.agreement_problems) as spy:
            self.blockers()
        flags = {call.args[0]: call.kwargs for call in spy.call_args_list}
        self.assertIs(flags["C2"]["runnable"], False)
        self.assertIsNone(flags["C2"]["recorded_exits"])
        self.assertEqual(sorted(s for s, kw in flags.items()
                                if kw["runnable"] is True),
                         ["C1", "C3", "Q1", "Q2", "Q3"])

    def test_owner_resolution_path_seals(self):
        self.complete()
        self.resolve()
        led = ledger(self.folder, self.c)
        self.assertEqual(led["resolution_sha256"], sha(self.res))
        self.assertEqual(led["generation"], 2)
        self.assertTrue(os.path.isfile(os.path.join(
            packet(self.folder, self.c), "revealed", "resolution.md")))
        self.assertSeals()

    def test_resolution_written_after_reveal_is_not_bound(self):
        self.complete()
        with open(self.res, "w", encoding="utf-8") as fh:
            fh.write("late decision\n")
        self.assertBlocked([holdout_seal.DISAGREE_MSG
                            % ("C2", "non-runnable proof")])

    def test_resolution_edited_after_reveal_is_not_bound(self):
        self.complete()
        self.resolve()
        with open(self.res, "a", encoding="utf-8") as fh:
            fh.write("edited afterwards\n")
        self.assertBlocked([holdout_seal.DISAGREE_MSG
                            % ("C2", "non-runnable proof")])

    def test_invented_exits_block(self):
        self.complete()
        self.resolve()
        self.edit_json(os.path.join(packet(self.folder, self.c),
                                    "final.json"),
                       lambda f: f.update(proof_rerun_exit={"base": 0,
                                                            "changed": 1}))
        self.assertBlocked([holdout_seal.DISAGREE_MSG
                            % ("C2", "non-runnable proof")])

    def test_mutant_non_runnable_clause(self):
        self.complete()
        with mock.patch.object(holdout_seal, "agreement_problems",
                               return_value=[]):
            self.assertSeals()


class TestResolutionPath(CompletedCase):

    COMPLETE = False

    def setUp(self):
        super().setUp()
        self.c = self.cid("C3")
        self.complete(mutate_blind=TestSealAgreement.only(
            "C3", defect_category="injection"))
        self.assertBlocked([holdout_seal.DISAGREE_MSG
                            % ("C3", "causal-failure category")])
        self.old_xid = ledger(self.folder, self.c)["xid"]
        self.old_token = ledger(self.folder, self.c)["reveal_token"]
        self.res = os.path.join(kdir(self.folder, self.c), "resolution.md")

    def write_resolution(self):
        with open(self.res, "w", encoding="utf-8") as fh:
            fh.write("owner evidence: the key category is right\n")

    def test_resolution_without_reset_never_auto_passes(self):
        self.write_resolution()
        self.assertBlocked([holdout_seal.DISAGREE_MSG
                            % ("C3", "causal-failure category")])

    def test_resolved_round_in_next_generation_seals(self):
        self.write_resolution()
        self.reset("C3", "resolved")
        mapping, _ = self.prepare(self.c)
        new_xid = mapping[self.c]
        self.assertNotEqual(new_xid, self.old_xid)
        self.assertFalse(os.path.exists(os.path.join(self.folder, "xcheck",
                                                     self.old_xid)))
        self.assertNotIn(new_xid, xids_in(self.folder, "xcheck"))
        self.assertEqual(xids_in(self.folder, "xcheck-r2"), [new_xid])
        deny = load(os.path.join(self.folder, "xcheck-r2", ".claude",
                                 "settings.json"))["permissions"]["deny"]
        self.assertIn("Read(%s/xcheck/**)" % self.folder, deny)
        write_blind(self.folder, self.c)
        reveal_all(self.folder)
        led = ledger(self.folder, self.c)
        self.assertEqual(led["resolution_sha256"], sha(self.res))
        self.assertTrue(os.path.isfile(os.path.join(
            packet(self.folder, self.c), "revealed", "resolution.md")))
        write_final(self.folder, self.c)
        self.assertSeals()
        led = ledger(self.folder, self.c)
        self.assertEqual(len(led["rounds"]), 1)
        self.assertEqual(led["rounds"][0]["reset_reason"], "resolved")
        self.assertEqual(led["rounds"][0]["generation"], 1)
        self.assertEqual(led["generation"], 2)

    def test_stale_final_with_old_token_blocks(self):
        self.write_resolution()
        self.reset("C3", "resolved")
        complete_case(self.folder, self.c,
                      mutate_final=lambda s, f: f.update(
                          reveal_token=self.old_token))
        self.assertBlocked(["C3: final.json is not bound to this reveal "
                            "(reveal_token mismatch)"])


class TestSealMutants(CompletedCase):
    """Each remaining blocker patched out: its own message disappears (and,
    where nothing downstream also catches the fault, the holdout seals)."""

    def test_mutant_validate(self):
        prov = os.path.join(kdir(self.folder, self.cid("Q2")),
                            "provenance.json")
        self.edit_json(prov, lambda p: p["search"].update(budget=24))
        with mock.patch.object(holdout_seal, "_blocker_validate",
                               return_value=None):
            self.assertSeals()

    def test_mutant_prepared(self):
        os.remove(ledger_path(self.folder, self.cid("C1")))
        with mock.patch.object(holdout_seal, "_blocker_prepared",
                               return_value=None):
            got = self.blockers()
        self.assertNotIn("cross-check not prepared for C1", got)
        self.assertTrue(any(b.startswith("C1: ") for b in got), got)

    def test_mutant_revealed(self):
        led = ledger(self.folder, self.cid("Q3"))
        led.pop("blind_sha256")
        dump(ledger_path(self.folder, self.cid("Q3")), led)
        self.assertEqual(self.blockers(), ["Q3: not yet revealed"])
        with mock.patch.object(holdout_seal, "_blocker_revealed",
                               return_value=None):
            got = self.blockers()
        self.assertNotIn("Q3: not yet revealed", got)
        self.assertTrue(got)

    def test_mutant_blind_intact(self):
        self.append(os.path.join(self.pkt("C1"), "blind.json"), b" ")
        with mock.patch.object(holdout_seal, "_blocker_blind_intact",
                               return_value=None):
            self.assertSeals()

    def test_mutant_blind_shape(self):
        self.edit_json(os.path.join(self.pkt("C2"), "blind.json"),
                       lambda b: b.update(reasoning=""))
        self.refreeze_blind("C2")
        self.assertEqual(self.blockers(),
                         ["C2: blind verdict has the wrong shape"])
        with mock.patch.object(holdout_seal, "_blocker_blind_shape",
                               return_value=None):
            self.assertSeals()

    def test_mutant_final_present(self):
        os.remove(os.path.join(self.pkt("C2"), "final.json"))
        with mock.patch.object(holdout_seal, "_blocker_final_present",
                               return_value=None):
            got = self.blockers()
        self.assertNotIn("C2: final.json missing", got)
        self.assertTrue(got)

    def test_mutant_final_bound(self):
        self.edit_json(os.path.join(self.pkt("Q2"), "final.json"),
                       lambda f: f.update(reveal_token="f" * 16))
        with mock.patch.object(holdout_seal, "_blocker_final_bound",
                               return_value=None):
            self.assertSeals()


# ================================================================ CLI seal


class TestCliSeal(CompletedCase):

    def run_seal(self):
        return self.cli("seal")

    def test_cli_seal(self):
        proc = self.run_seal()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("OK: sealed 6 cases. Next: bin/holdout encrypt",
                      proc.stdout)
        seal = load(os.path.join(self.folder, "SEAL.json"))
        self.assertEqual(holdout_manifest.public_shape_problems(seal), [])
        for c in self.ids.values():
            self.assertNotIn(key_of(self.folder, c).get("defect", "@@"),
                             proc.stdout)
        again = self.run_seal()
        self.assertEqual(again.returncode, 1)
        self.assertIn("already sealed (SEAL.json exists)", again.stderr)

    def test_cli_blind_changed(self):
        self.append(os.path.join(self.pkt("C1"), "blind.json"), b" ")
        proc = self.run_seal()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: C1: blind verdict changed after reveal",
                      proc.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.folder,
                                                     "SEAL.json")))

    def test_cli_inputs_changed_then_redo(self):
        c = self.cid("Q3")
        self.append(os.path.join(cdir(self.folder, c), "change.diff"))
        proc = self.run_seal()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("sealed inputs changed after the cross-check "
                      "(change.diff)", proc.stdout)
        self.assertEqual(self.cli("crosscheck-reset", c, "--reason",
                                  "inputs-changed").returncode, 0)
        self.assertEqual(self.cli("crosscheck-prepare", "--case",
                                  c).returncode, 0)
        write_blind(self.folder, c)
        self.assertEqual(self.cli("crosscheck-reveal", "--ready").returncode,
                         0)
        write_final(self.folder, c)
        proc = self.run_seal()
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_cli_type_disagreement(self):
        self.edit_json(os.path.join(self.pkt("C1"), "blind.json"),
                       lambda b: b.update(type_guess="C3"))
        self.refreeze_blind("C1")
        proc = self.run_seal()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: Case C1: the independent check disagreed "
                      "(type)", proc.stdout)

    def test_cli_proof_exits_then_restore(self):
        path = os.path.join(self.pkt("C2"), "final.json")
        self.edit_json(path, lambda f: f.update(
            proof_rerun_exit={"base": 0, "changed": 0}))
        proc = self.run_seal()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: Case C2: the independent check disagreed "
                      "(proof exits)", proc.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.folder,
                                                     "SEAL.json")))
        self.edit_json(path, lambda f: f.update(
            proof_rerun_exit={"base": 0, "changed": 1}))
        self.assertEqual(self.run_seal().returncode, 0)

    def test_cli_stale_workspace_then_restore(self):
        c = self.cid("C3")
        self.reset("C3", "owner")
        complete_case(self.folder, c)
        lp = ledger_path(self.folder, c)
        honest = load(lp)
        self.edit_json(lp, lambda d: d.update(generation=1,
                                              workspace="xcheck"))
        proc = self.run_seal()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: Case C3: round 2 was judged in cross-check "
                      "workspace xcheck, which had already seen a revealed "
                      "key.", proc.stdout)
        dump(lp, honest)
        self.assertEqual(self.run_seal().returncode, 0)


class TestCliSealNonRunnable(CompletedCase):

    COMPLETE = False

    def test_cli_non_runnable_then_resolution(self):
        c = self.cid("C1")
        dump(os.path.join(kdir(self.folder, c), "proof-results.json"),
             {"runnable": False, "nonrunnable_reason": "needs hardware",
              "manual_evidence": "fixture manual evidence"})
        self.complete()
        proc = self.cli("seal")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROBLEM: Case C1: the independent check disagreed "
                      "(non-runnable proof)", proc.stdout)
        with open(os.path.join(kdir(self.folder, c), "resolution.md"),
                  "w") as fh:
            fh.write("owner evidence\n")
        self.assertEqual(self.cli("crosscheck-reset", c, "--reason",
                                  "resolved").returncode, 0)
        self.assertEqual(self.cli("crosscheck-prepare", "--case",
                                  c).returncode, 0)
        write_blind(self.folder, c)
        reveal_all(self.folder)
        write_final(self.folder, c)
        proc = self.cli("seal")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("resolution_sha256", ledger(self.folder, c))


# ================================================================ module shape


# ================================================================ diagnose


def dg(slot, key_edit=None, blind_edit=None, final_edit=None, **kw):
    key, blind, final, rec = agreeing_args(slot)
    for obj, edit in ((key, key_edit), (blind, blind_edit),
                      (final, final_edit)):
        if edit is not None:
            edit(obj)
    kw.setdefault("recorded_exits", rec)
    return holdout_seal.diagnose_parts(slot, key, blind, final, **kw)


def _flags(**flags):
    return lambda f: f.update(flags)


class TestDiagnoseParts(unittest.TestCase):
    """The diagnosis names WHY the agreement rule failed, in a closed
    vocabulary, and sorts it into a case/key problem or a checker suspect.
    It never changes what agrees."""

    def test_agreeing_every_slot(self):
        for slot in holdout_kit.SLOTS:
            self.assertEqual(dg(slot), ("agrees", []), slot)

    def test_c3_judged_other_catch_slot(self):
        self.assertEqual(
            dg("C3", blind_edit=lambda b: b.update(type_guess="C1"),
               final_edit=_flags(type_agrees=False)),
            ("judge-disagrees", ["type-other-slot", "judge-type-false"]))

    def test_c3_judged_quiet(self):
        cause, checks = dg("C3", blind_edit=lambda b: b.update(
            verdict="quiet", type_guess="Q1", location=None,
            defect_category=None), final_edit=_flags(type_agrees=False,
                                                     defect_agrees=False))
        self.assertEqual(cause, "judge-disagrees")
        self.assertIn("type-judged-quiet", checks)

    def test_quiet_judged_catch(self):
        cause, checks = dg("Q2", blind_edit=lambda b: b.update(
            verdict="catch", type_guess="C1",
            location={"file": "a", "line_start": 1, "line_end": 2},
            defect_category="logic-error"))
        self.assertEqual(cause, "judge-disagrees")
        self.assertIn("type-judged-catch", checks)

    def test_type_flag_contradicting_the_blind_is_still_the_judge(self):
        cause, checks = dg("C3", blind_edit=lambda b: b.update(
            type_guess="C2"))
        self.assertEqual(cause, "judge-disagrees")
        self.assertIn("judge-flag-contradicts", checks)

    def test_key_other_is_unsealable(self):
        cause, checks = dg("C3", key_edit=lambda k: k.update(
            causal_failure_category="other"), blind_edit=lambda b: b.update(
            defect_category="other"))
        self.assertEqual(cause, "key-unsealable")
        self.assertIn("category-key-other", checks)

    def test_judge_other(self):
        cause, checks = dg("C3", blind_edit=lambda b: b.update(
            defect_category="other"), final_edit=_flags(
            causal_failure_agrees=False))
        self.assertEqual(cause, "judge-disagrees")
        self.assertIn("category-judge-other", checks)

    def test_recorded_pattern_wrong_is_unsealable(self):
        cause, checks = dg("C3", recorded_exits={"base": 1, "changed": 1},
                           final_edit=lambda f: f.update(
                               proof_rerun_exit={"base": 1, "changed": 1}))
        self.assertEqual(cause, "key-unsealable")
        self.assertIn("proof-recorded-bad", checks)

    def test_recorded_missing_is_unsealable(self):
        cause, checks = dg("C3", recorded_exits=None)
        self.assertEqual(cause, "key-unsealable")
        self.assertIn("proof-recorded-bad", checks)

    def test_category_differs_judge_says_no(self):
        self.assertEqual(
            dg("C3", blind_edit=lambda b: b.update(
                defect_category="logic-error"),
               final_edit=_flags(causal_failure_agrees=False)),
            ("judge-disagrees", ["category-differs", "judge-category-false"]))

    def test_category_differs_judge_says_yes(self):
        cause, checks = dg("C3", blind_edit=lambda b: b.update(
            defect_category="logic-error"))
        self.assertEqual(cause, "judge-disagrees")
        self.assertEqual(checks, ["category-differs",
                                  "judge-flag-contradicts"])

    def test_location_path_form_is_checker_suspect(self):
        for form in ("changed/src/a.py", "/x/xcheck/X-1/changed/src/a.py",
                     "base/src/a.py"):
            cause, checks = dg("C3", blind_edit=_loc(10, 20, form))
            self.assertEqual(cause, "checker-suspect", form)
            self.assertIn("location-path-form", checks, form)

    def test_judge_disagreement_outranks_checker_suspect(self):
        # Fixing the checker would not seal a case the judge rejects.
        cause, checks = dg("C3", blind_edit=lambda b: b.update(
            type_guess="C1", location={"file": "changed/src/a.py",
                                       "line_start": 10, "line_end": 20}),
            final_edit=_flags(type_agrees=False))
        self.assertEqual(cause, "judge-disagrees")
        self.assertIn("location-path-form", checks)

    def test_location_suffix_of_a_different_name_is_not_path_form(self):
        cause, checks = dg("C3", blind_edit=_loc(10, 20, "src/xa.py"),
                           final_edit=_flags(defect_agrees=False))
        self.assertEqual(cause, "judge-disagrees")
        self.assertIn("location-file-differs", checks)

    def test_location_apart_judge_says_same_defect(self):
        cause, checks = dg("C3", blind_edit=_loc(200, 210))
        self.assertEqual(cause, "checker-suspect")
        self.assertIn("location-lines-apart", checks)

    def test_location_apart_judge_says_different_defect(self):
        cause, checks = dg("C3", blind_edit=_loc(200, 210),
                           final_edit=_flags(defect_agrees=False))
        self.assertEqual(cause, "judge-disagrees")
        self.assertEqual(checks, ["location-lines-apart",
                                  "judge-defect-false"])

    def test_rerun_base_failed(self):
        cause, checks = dg("C3", final_edit=lambda f: f.update(
            proof_agrees=False, proof_rerun_exit={"base": 1, "changed": 1}))
        self.assertEqual(cause, "proof-mismatch")
        self.assertIn("proof-rerun-base-failed", checks)
        self.assertIn("proof-rerun-differs", checks)

    def test_rerun_changed_passed(self):
        cause, checks = dg("C3", final_edit=lambda f: f.update(
            proof_agrees=False, proof_rerun_exit={"base": 0, "changed": 0}))
        self.assertEqual(cause, "proof-mismatch")
        self.assertIn("proof-rerun-changed-passed", checks)

    def test_rerun_missing(self):
        cause, checks = dg("C3", final_edit=lambda f: f.update(
            proof_rerun_exit=None))
        self.assertEqual(cause, "judge-disagrees")
        self.assertIn("final-malformed", checks)

    def test_quiet_unconfirmed(self):
        cause, checks = dg("Q1", final_edit=lambda f: f.update(
            quiet_confirmed={"supported_behavior": True,
                             "exposure_check": False}))
        self.assertEqual(cause, "judge-disagrees")
        self.assertIn("quiet-unconfirmed", checks)

    def test_non_runnable_unresolved(self):
        cause, checks = dg("C3", runnable=False, final_edit=lambda f: f.update(
            proof_rerun_exit=None))
        self.assertEqual(cause, "judge-disagrees")
        self.assertIn("nonrunnable-unresolved", checks)

    def test_judge_proof_flag_false_alone(self):
        self.assertEqual(dg("C3", final_edit=_flags(proof_agrees=False)),
                         ("judge-disagrees", ["judge-proof-false"]))

    def test_vocabulary_closed_and_consistent_with_rule(self):
        edits = [
            dict(blind_edit=lambda b: b.update(type_guess="C1")),
            dict(blind_edit=_loc(200, 210)),
            dict(blind_edit=_loc(10, 20, "changed/src/a.py")),
            dict(blind_edit=lambda b: b.update(defect_category="other")),
            dict(key_edit=lambda k: k.update(causal_failure_category="other")),
            dict(final_edit=_flags(defect_agrees=False)),
            dict(final_edit=lambda f: f.update(
                proof_rerun_exit={"base": 0, "changed": 0})),
            dict(recorded_exits={"base": 0, "changed": 0}),
            dict(final_edit=lambda f: f.clear()),
            dict(blind_edit=lambda b: b.clear()),
            dict(key_edit=lambda k: k.clear()),
            dict(),
        ]
        for slot in holdout_kit.SLOTS:
            for kw in edits:
                cause, checks = dg(slot, **kw)
                rule = ap(slot, **kw)
                self.assertIn(cause, holdout_manifest.DIAG_CAUSES)
                for c in checks:
                    self.assertIn(c, holdout_manifest.DIAG_CHECKS)
                self.assertEqual(cause == "agrees", rule == [], (slot, kw))
                if rule:
                    self.assertTrue(checks, (slot, kw))

    def test_mutant_rule_drives_agrees(self):
        with mock.patch.object(holdout_seal, "agreement_problems",
                               return_value=[]):
            self.assertEqual(dg("C3", blind_edit=lambda b: b.update(
                type_guess="C1"))[0], "agrees")


class TestDiagnoseFolder(CompletedCase):

    COMPLETE = False

    def snapshot(self):
        return file_hashes(self.folder)

    def test_all_agree(self):
        self.complete()
        self.assertEqual(holdout_seal.diagnose(self.folder), [])
        self.assertEqual(holdout_seal.diagnose(self.folder, slot="C3"),
                         [("C3", "agrees", [])])

    def test_c3_disagreement_line_is_opaque(self):
        def c1(s, d):
            if s == "C3":
                d["type_guess"] = "C1"
        self.complete(mutate_blind=c1)
        self.refreeze_blind("C3")
        got = holdout_seal.diagnose(self.folder)
        self.assertEqual(len(got), 1)
        slot, cause, checks = got[0]
        line = holdout_seal.diagnosis_line(slot, cause, checks)
        self.assertEqual(holdout_manifest.resume_reply_kind(line),
                         "diagnosis")
        key = key_of(self.folder, self.cid("C3"))
        for secret in (key["defect"], key["location"]["file"],
                       key["causal_failure"], self.cid("C3")):
            self.assertNotIn(secret, line)

    def test_incomplete_round(self):
        self.prepare()
        self.assertEqual(holdout_seal.diagnose(self.folder, slot="C3"),
                         [("C3", "incomplete", ["round-incomplete"])])

    def test_read_only(self):
        self.complete(mutate_blind=lambda s, d: d.update(type_guess="C1")
                      if s == "C3" else None)
        before = self.snapshot()
        holdout_seal.diagnose(self.folder)
        self.assertEqual(self.snapshot(), before)

    def test_cli(self):
        self.complete(mutate_blind=lambda s, d: d.update(type_guess="C1")
                      if s == "C3" else None)
        before = self.snapshot()
        proc = self.cli("diagnose", "--slot", "C3")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        last = proc.stdout.strip().splitlines()[-1]
        self.assertTrue(last.startswith("diagnosis C3 cause=judge-disagrees "
                                        "checks=type-other-slot"), last)
        self.assertEqual(holdout_manifest.resume_reply_kind(last),
                         "diagnosis")
        self.assertIn("action C3:", proc.stdout)
        key = key_of(self.folder, self.cid("C3"))
        self.assertNotIn(key["defect"], proc.stdout + proc.stderr)
        self.assertNotIn(self.cid("C3"), proc.stdout + proc.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_cli_all_agree(self):
        self.complete()
        proc = self.cli("diagnose")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(proc.stdout.strip().splitlines()[-1],
                         "diagnosis all cause=agrees checks=none")

    def test_cli_refuses_inside_claude(self):
        self.complete()
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        proc = self.cli("diagnose", env=env)
        self.assertNotEqual(proc.returncode, 0)
        self.assertNotIn("diagnosis", proc.stdout)


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
                     "crosscheck-reset", "seal", "diagnose"):
            self.assertEqual(holdout_kit.COMMANDS[name], "holdout_seal")

    def test_exports(self):
        for name in ("prepare_crosscheck", "reveal", "reveal_workspace",
                     "reset_crosscheck", "add_parser", "cmd", "DISAGREE_MSG",
                     "INPUTS_CHANGED_MSG", "STALE_WORKSPACE_MSG",
                     "LINE_SLACK", "WORKSPACES_RELPATH"):
            self.assertTrue(hasattr(holdout_seal, name), name)
        self.assertEqual(holdout_seal.LINE_SLACK, 5)

    def test_seal_exports(self):
        for name in ("seal_blockers", "agreement_problems", "do_seal",
                     "_recorded_exits", "_blocker_validate",
                     "_blocker_retired", "_blocker_prepared",
                     "_blocker_revealed", "_blocker_blind_intact",
                     "_blocker_blind_shape", "_blocker_inputs_bound",
                     "_blocker_workspace_fresh", "_blocker_final_present",
                     "_blocker_final_bound", "_blocker_agreement"):
            self.assertTrue(hasattr(holdout_seal, name), name)
        self.assertEqual(holdout_seal.WORKSPACES_RELPATH,
                         "sealed/keys/xcheck-workspaces.json")


if __name__ == "__main__":
    unittest.main()
