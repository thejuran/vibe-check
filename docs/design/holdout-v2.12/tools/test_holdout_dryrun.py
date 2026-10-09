"""Tests for holdout_dryrun — the dummy holdout and the end-to-end rehearsal.

Locked here:
  * `dryrun --populate` turns a freshly set-up folder into a six-case holdout
    that validate accepts (proofs re-executed) with a completed, agreeing
    blind cross-check; its synthetic text never appears in the repo source,
    so the owner's dry-run leakscan of this repo stays clean.
  * The whole pipeline runs on dummy data with an openssl shim:
    populate -> validate -> crosscheck -> seal -> encrypt -> rehash ->
    leakscan -> publish -> scrub, including
      - an inputs-changed refusal regenerated through crosscheck-reset into a
        fresh cross-check generation (xcheck-r2, cfg-xcheck-r2) whose sandbox
        denies generation 1 and whose sandbox probe targets it;
      - the writer barrier: encrypt refuses while a process sits in the
        folder;
      - a planted tuning-side leak: publish refuses, a clean re-scan alone
        does not help, a relabel of the leaked case under a fresh ID is
        refused by seal (`reuses material retired`), and only replace_case +
        re-seal + re-encrypt + a clean scan lets publish through;
      - planted logs and stray plaintext that scrub removes (they were
        archived, so decrypt brings them back), and the README's recovery
        command (`decrypt --archive archive/holdout-v2.12.tar.enc --dest <H>`
        then `retire --sync`).
  * The C3-as-C1 disagreement and the stale-workspace refusal, each cleared
    only through crosscheck-reset and a fresh generation.

Every folder is a temp dir; nothing here reads the owner's holdout. Synthetic
text is never printed by these tests.
"""

import ast
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

import holdout_fixture  # noqa: E402
import holdout_kit  # noqa: E402
import holdout_manifest  # noqa: E402
import holdout_seal  # noqa: E402
import holdout_validate  # noqa: E402
import holdout_archive  # noqa: E402

import holdout_dryrun  # noqa: E402

KitError = holdout_kit.KitError
KIT_PY = os.path.join(TOOLS_DIR, "holdout_kit.py")
DRYRUN_PY = os.path.join(TOOLS_DIR, "holdout_dryrun.py")
ID_ANY = re.compile(r"H-[0-9a-f]{8}")
REGEN_SLOT = "C1"
LEAK_SLOT = "C2"

SHIM_SRC = r'''#!@@EXE@@
"""Fake openssl for tests: a reversible XOR, never a passphrase."""
import os
import sys

args = sys.argv[1:]
for a in args:
    if a in ("-pass", "-k", "-kfile") or a.startswith("pass:"):
        sys.stderr.write("refused: passphrase on argv\n")
        sys.exit(3)
if not args or args[0] != "enc":
    sys.exit(2)
src = args[args.index("-in") + 1] if "-in" in args else None
dst = args[args.index("-out") + 1] if "-out" in args else None
data = open(src, "rb").read() if src else sys.stdin.buffer.read()
data = data.translate(bytes(i ^ 0x5A for i in range(256)))
if dst:
    with open(dst, "wb") as fh:
        fh.write(data)
else:
    sys.stdout.buffer.write(data)
'''


# ================================================================ helpers


def make_shim(directory):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "fake-openssl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(SHIM_SRC.replace("@@EXE@@", sys.executable))
    os.chmod(path, 0o755)
    return path


def plain_terminal():
    """os.environ as a plain Terminal with isolated git config (no
    CLAUDECODE, no global or system git config)."""
    return mock.patch.dict(os.environ, holdout_fixture.kit_env(), clear=True)


def quiet(fn, *args, **kwargs):
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


def kdir(folder, cid):
    return os.path.join(folder, "sealed", "keys", cid)


def cdir(folder, cid):
    return os.path.join(folder, "sealed", "cases", cid)


def ledger(folder, cid):
    return load(os.path.join(kdir(folder, cid), "xcheck-ledger.json"))


def registry(folder):
    return load(os.path.join(folder,
                             *holdout_seal.WORKSPACES_RELPATH.split("/")))


def packets(folder, ws):
    return sorted(n for n in os.listdir(os.path.join(folder, ws))
                  if holdout_kit.XID_RE.match(n))


def probe_targets(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "TARGETS"
                for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("no TARGETS in %s" % path)


def slot_ids(folder):
    return {holdout_validate.slot_of(folder, c): c
            for c in holdout_kit.case_ids(folder)}


def setup_folder(tmp):
    """The real setup CLI into <tmp>/holdout with one seed repo."""
    seed = holdout_fixture.make_source_repo(tmp, "seed-repo")
    folder = os.path.join(tmp, "holdout")
    proc = subprocess.run(
        [sys.executable, KIT_PY, "--folder", folder, "setup", "--repo", seed,
         "--skip-system-exclusions"], cwd=tmp, env=holdout_fixture.kit_env(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
    if proc.returncode != 0:
        raise AssertionError("setup failed:\n%s%s"
                             % (proc.stdout, proc.stderr))
    return os.path.realpath(folder)


def populated(tmp, mark_dry_run=False):
    """A populated dummy folder. Unmarked by default: these tests rehearse
    the REAL seal/publish/rehash machinery on dummy data, which refuses a
    folder carrying the dry-run marker (TestDryRunMarker covers that)."""
    folder = setup_folder(tmp)
    with plain_terminal():
        ids, _ = quiet(holdout_dryrun.populate, folder,
                       mark_dry_run=mark_dry_run)
    return folder, ids


def relabel(folder, old):
    """Test-only: copy a case and its keys byte-for-byte to a fresh ID (the
    ledger and crosscheck.json included; the live packet stays in place),
    rewrite case.json's id and the registry's case list so every
    cross-check binding still holds, and delete the old folders."""
    taken = set(holdout_kit.case_ids(folder))
    new = holdout_kit.new_case_id()
    while new in taken:
        new = holdout_kit.new_case_id()
    for part in (cdir, kdir):
        shutil.copytree(part(folder, old), part(folder, new), symlinks=True)
    case_json = os.path.join(cdir(folder, new), "case.json")
    data = load(case_json)
    data["id"] = new
    dump(case_json, data)
    reg_path = os.path.join(folder,
                            *holdout_seal.WORKSPACES_RELPATH.split("/"))
    reg = load(reg_path)
    for g in reg["generations"]:
        g["cases"] = [new if c == old else c for c in g["cases"]]
    dump(reg_path, reg)
    for part in (cdir, kdir):
        shutil.rmtree(part(folder, old))
    return new


def diff_probe_with_escapes(folder, cid):
    """The added diff line of a case that holds a double quote and a
    backslash, stripped the way leakscan builds probes."""
    with open(os.path.join(cdir(folder, cid), "change.diff"),
              encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            if line.startswith("+") and not line.startswith("+++") \
                    and '"' in line and "\\" in line:
                return line[1:].strip()
    raise AssertionError("no escaped added line")


def all_probes(folder):
    return {p for p, _, _ in holdout_archive._probes(folder)}


class DryrunCase(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = os.path.realpath(self._tmp.name)

    def cli(self, folder, *args, stdin=None):
        argv = [sys.executable, KIT_PY]
        if folder is not None:
            argv += ["--folder", folder]
        return subprocess.run(argv + list(args), cwd=self.tmp,
                              env=holdout_fixture.kit_env(), input=stdin,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=600)

    def ok(self, proc, msg=""):
        self.assertEqual(proc.returncode, 0,
                         "%s\n%s%s" % (msg, proc.stdout, proc.stderr))
        return proc

    def refused(self, proc, msg=""):
        self.assertEqual(proc.returncode, 1,
                         "%s\n%s%s" % (msg, proc.stdout, proc.stderr))
        return proc

    def git_repo(self, name):
        repo = os.path.join(self.tmp, name)
        os.makedirs(repo)
        proc = holdout_kit.run_argv(["git", "init", "-q", repo])
        self.assertEqual(proc.returncode, 0)
        return repo

    def scan_root(self, name, files=None):
        root = os.path.join(self.tmp, name)
        os.makedirs(root)
        for rel, text in (files or {}).items():
            with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                fh.write(text)
        return root


# ================================================================ populate


class TestPopulate(DryrunCase):

    @classmethod
    def setUpClass(cls):
        cls._ctmp = tempfile.TemporaryDirectory()
        cls.folder, cls.ids = populated(os.path.realpath(cls._ctmp.name))

    @classmethod
    def tearDownClass(cls):
        cls._ctmp.cleanup()

    def test_validate_all_ok(self):
        with plain_terminal():
            checks = holdout_validate.validate_folder(self.folder)
        self.assertTrue(checks)
        self.assertEqual([c.name for c in checks if not c.ok], [])
        self.assertEqual([c.name for c in checks if c.warning], [])
        self.ok(self.cli(self.folder, "validate"))

    def test_six_slots_and_cross_check_complete(self):
        self.assertEqual(sorted(self.ids), list(holdout_kit.SLOTS))
        self.assertEqual(len(packets(self.folder, "xcheck")), 6)
        for slot, cid in self.ids.items():
            led = ledger(self.folder, cid)
            self.assertEqual(led["generation"], 1, slot)
            self.assertRegex(led["blind_sha256"], r"^[0-9a-f]{64}$")
            packet = os.path.join(self.folder, "xcheck", led["xid"])
            for name in ("blind.json", "final.json", "revealed/REVEAL-TOKEN"):
                self.assertTrue(os.path.isfile(os.path.join(packet, name)),
                                name)
            final = load(os.path.join(packet, "final.json"))
            with open(os.path.join(packet, "revealed", "REVEAL-TOKEN")) as fh:
                self.assertEqual(final["reveal_token"], fh.read().strip())
            blind = load(os.path.join(packet, "blind.json"))
            self.assertEqual(blind["type_guess"], slot)
        reg = registry(self.folder)
        self.assertEqual(len(reg["generations"]), 1)
        self.assertIsNotNone(reg["generations"][0]["revealed_at"])

    def test_seal_blockers_empty(self):
        with plain_terminal():
            self.assertEqual(holdout_seal.seal_blockers(self.folder), [])

    def test_provenance_and_keys_are_synthetic(self):
        eligible = load(os.path.join(self.folder, "kit",
                                     "eligible-repos.json"))["repos"]
        for slot, cid in self.ids.items():
            prov = load(os.path.join(kdir(self.folder, cid),
                                     "provenance.json"))
            self.assertEqual(prov["kind"], "organic")
            self.assertEqual(prov["repo_name"],
                             holdout_dryrun.LAYOUT[slot][0])
            self.assertEqual(os.path.basename(prov["source_repo"]),
                             prov["repo_name"])
            self.assertIn(prov["source_repo"], eligible)
            self.assertIs(prov["repo_in_b3"], False)
            self.assertTrue(prov["source_repo"].startswith(
                os.path.join(self.folder, holdout_dryrun.REPOS_DIRNAME)))
            key = load(os.path.join(kdir(self.folder, cid), "key.json"))
            texts = [v for k, v in key.items() if isinstance(v, str)
                     and k not in ("slot", "class",
                                   "causal_failure_category")]
            self.assertTrue(texts)
            for text in texts:
                self.assertIn("DRY RUN: synthetic", text)
            if slot in holdout_kit.CATCH_SLOTS:
                self.assertIn(key["causal_failure_category"],
                              holdout_validate.CAUSAL_CATEGORIES)
                self.assertNotEqual(key["causal_failure_category"], "other")
                loc = key["location"]
                self.assertLess(loc["line_start"], loc["line_end"])

    def test_every_diff_has_an_escaped_added_line(self):
        for cid in self.ids.values():
            probe = diff_probe_with_escapes(self.folder, cid)
            self.assertGreaterEqual(len(probe), holdout_archive.PROBE_MIN_LEN)

    def test_no_probe_in_repo_source(self):
        """The owner's dry-run leakscan scans this repo: no synthetic probe
        may appear verbatim in any kit source or test."""
        probes = all_probes(self.folder)
        self.assertGreater(len(probes), 30)
        for name in os.listdir(TOOLS_DIR):
            if name.endswith(".py"):
                with open(os.path.join(TOOLS_DIR, name), encoding="utf-8") \
                        as fh:
                    text = fh.read()
                self.assertEqual(sum(1 for p in probes if p in text), 0, name)

    def test_probes_are_fresh_per_populate(self):
        other_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(other_tmp.cleanup)
        other, _ = populated(os.path.realpath(other_tmp.name))
        self.assertEqual(all_probes(self.folder) & all_probes(other), set())

    def test_populate_refuses_a_folder_with_cases(self):
        with plain_terminal():
            with self.assertRaises(KitError) as cm:
                holdout_dryrun.populate(self.folder)
        self.assertIn("folder already has cases", str(cm.exception))

    def test_replace_refuses_when_sealed(self):
        seal = os.path.join(self.folder, "SEAL.json")
        with open(seal, "w") as fh:
            fh.write("{}")
        self.addCleanup(os.remove, seal)
        with plain_terminal():
            with self.assertRaises(KitError) as cm:
                holdout_dryrun.replace_case(self.folder, "C2")
        self.assertIn("delete SEAL.json and archive/ deliberately",
                      str(cm.exception))


class TestPopulateCli(DryrunCase):

    def test_cli_populate(self):
        folder = setup_folder(self.tmp)
        proc = self.ok(self.cli(folder, "dryrun", "--populate"))
        self.assertIn("OK: " + holdout_dryrun.POPULATED_MSG, proc.stdout)
        self.assertEqual(len(holdout_kit.case_ids(folder)), 6)
        again = self.refused(self.cli(folder, "dryrun", "--populate"))
        self.assertIn("folder already has cases", again.stderr)
        self.assertTrue(holdout_kit.dry_run_marker_ok(folder))

    def test_manual_dry_run_is_marked_end_to_end(self):
        # README section 6: the populated folder is a dry run. Real seal,
        # seal-build, rehash and publish refuse it; the --dry-run forms work
        # and write a seal that can never pass for the real one.
        folder = setup_folder(self.tmp)
        self.ok(self.cli(folder, "dryrun", "--populate"))
        self.ok(self.cli(folder, "validate"))
        refused = self.refused(self.cli(folder, "seal"))
        self.assertIn(holdout_kit.DRY_RUN_REFUSED_MSG, refused.stdout)
        self.refused(self.cli(folder, "seal-build"))
        self.assertFalse(os.path.exists(os.path.join(folder, "SEAL.json")))
        self.ok(self.cli(folder, "seal", "--dry-run"))
        seal = load(os.path.join(folder, "SEAL.json"))
        self.assertEqual(seal["status"], "dry-run")
        self.assertTrue(holdout_manifest.public_shape_problems(seal))
        # No real judge ran here, so nothing is synthetic.
        self.assertFalse(any("agreement" in e for e in seal["cases"].values()))
        seal_path = os.path.join(folder, "SEAL.json")
        sealed = os.path.join(folder, "sealed")
        proc = self.refused(self.cli(folder, "rehash", "--seal", seal_path,
                                     "--sealed", sealed))
        self.assertIn(holdout_kit.DRY_RUN_REFUSED_MSG, proc.stdout)
        self.ok(self.cli(folder, "rehash", "--dry-run", "--seal", seal_path,
                         "--sealed", sealed))
        repo = self.git_repo("tuning")
        proc = self.refused(self.cli(folder, "publish", "--repo", repo))
        self.assertIn(holdout_kit.DRY_RUN_REFUSED_MSG, proc.stderr)
        self.assertFalse(os.path.exists(os.path.join(
            repo, *holdout_manifest.SEAL_RELPATH.split("/"))))

    def test_cli_refuses_under_claudecode(self):
        folder = setup_folder(self.tmp)
        env = holdout_fixture.kit_env()
        env["CLAUDECODE"] = "1"
        proc = subprocess.run(
            [sys.executable, KIT_PY, "--folder", folder, "dryrun",
             "--populate"], cwd=self.tmp, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=120)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stderr, holdout_kit.REFUSE_MSG + "\n")
        self.assertEqual(holdout_kit.case_ids(folder), [])

    def test_cli_requires_populate_flag(self):
        folder = setup_folder(self.tmp)
        self.assertEqual(self.cli(folder, "dryrun").returncode, 2)

    def test_populate_needs_setup(self):
        with plain_terminal():
            with self.assertRaises(KitError) as cm:
                holdout_dryrun.populate(os.path.join(self.tmp, "nothing"))
        self.assertIn("run setup first", str(cm.exception))


# ================================================================ pipeline


class TestPipeline(DryrunCase):

    def regenerate_inputs_changed(self, F, ids):
        """Touch one proof after the cross-check; seal must refuse and the
        case must be regenerated in a fresh generation."""
        cid = ids[REGEN_SLOT]
        run = os.path.join(kdir(F, cid), "proof", "run")
        with open(run, "a", encoding="utf-8") as fh:
            fh.write("# trailing comment added after the cross-check\n")
        time.sleep(1.1)  # a later ran_at, so proof-results.json changes too
        with plain_terminal():
            holdout_dryrun.record_proof_results(F, cid)
        self.ok(self.cli(F, "validate"))
        proc = self.refused(self.cli(F, "seal"))
        self.assertIn(holdout_seal.INPUTS_CHANGED_MSG
                      % (REGEN_SLOT, "proof-results.json, proof"),
                      proc.stdout)
        self.assertFalse(os.path.exists(os.path.join(F, "SEAL.json")))
        self.ok(self.cli(F, "crosscheck-reset", cid, "--reason",
                         "inputs-changed"))
        proc = self.ok(self.cli(F, "crosscheck-prepare", "--case", cid))
        self.assertIn("fresh cross-check workspace xcheck-r2", proc.stdout)
        self.assertIn("bin/crosscheck-r2", proc.stdout)

        # Generation 2: its own workspace, empty config dir, scratch root
        # and launcher, every generation-1 path denied.
        self.assertEqual(len(packets(F, "xcheck-r2")), 1)
        self.assertEqual(os.listdir(os.path.join(F, "cfg-xcheck-r2")), [])
        self.assertTrue(os.path.isfile(os.path.join(F, "bin",
                                                    "crosscheck-r2")))
        settings = load(os.path.join(F, "xcheck-r2", ".claude",
                                     "settings.json"))
        deny = settings["permissions"]["deny"]
        self.assertIn("Read(%s/xcheck/**)" % F, deny)
        self.assertIn("Read(%s/cfg-xcheck/**)" % F, deny)
        self.assertEqual(holdout_kit.xcheck_settings_problems(
            settings, F, prior=[holdout_kit.xcheck_names(1)]), [])
        deny_read = settings["sandbox"]["filesystem"]["denyRead"]
        for rel in ("sealed", "tmp/finder", "tmp/owner", "xcheck",
                    "cfg-xcheck", "tmp/crosscheck/xcheck"):
            self.assertIn(os.path.join(F, rel), deny_read)
        self.assertNotIn(os.path.join(F, "tmp/crosscheck/xcheck-r2"),
                         deny_read)
        self.assertTrue(os.path.isfile(os.path.join(
            F, "tmp", "crosscheck", "xcheck-r2", "SANDBOX-SENTINEL")))
        targets = probe_targets(os.path.join(F, "xcheck-r2",
                                             "sandbox-probe.py"))
        for rel in ("sealed/SANDBOX-SENTINEL", "tmp/finder/SANDBOX-SENTINEL",
                    "tmp/owner/SANDBOX-SENTINEL",
                    "xcheck/.claude/settings.json",
                    "tmp/crosscheck/xcheck/SANDBOX-SENTINEL", "cfg-xcheck"):
            self.assertIn(os.path.join(F, rel), targets)
        gens = registry(F)["generations"]
        self.assertEqual([(g["workspace"], g["revealed_at"] is not None)
                          for g in gens],
                         [("xcheck", True), ("xcheck-r2", False)])

        with plain_terminal():
            holdout_dryrun.complete_case_crosscheck(F, cid)
        self.assertEqual(ledger(F, cid)["generation"], 2)
        self.assertEqual(ledger(F, cid)["workspace"], "xcheck-r2")

    def test_dummy_pipeline(self):
        F, ids = populated(self.tmp)
        shim = make_shim(os.path.join(self.tmp, "shim"))
        publish_repo = self.git_repo("tuning-repo")
        published = os.path.join(publish_repo,
                                 *holdout_manifest.SEAL_RELPATH.split("/"))
        self.ok(self.cli(F, "validate"))

        # --- regeneration cycle (inputs changed -> fresh generation)
        self.regenerate_inputs_changed(F, ids)
        self.ok(self.cli(F, "seal"))
        seal_path = os.path.join(F, "SEAL.json")
        self.assertEqual(holdout_manifest.public_shape_problems(
            load(seal_path)), [])
        rounds = ledger(F, ids[REGEN_SLOT])["rounds"]
        self.assertEqual(len(rounds), 1)
        self.assertEqual(rounds[0]["generation"], 1)

        # --- plaintext that must not survive scrub, and a modified kit copy
        probes_v0 = sorted(all_probes(F))
        os.makedirs(os.path.join(F, "logs"))
        with open(os.path.join(F, "logs", "finder.log"), "w") as fh:
            fh.write("finder log\n%s\n" % probes_v0[0])
        with open(os.path.join(F, "stray-notes.txt"), "w") as fh:
            fh.write("notes\n%s\n" % probes_v0[-1])
        with open(os.path.join(F, "kit", "tools", "holdout_kit.py"),
                  "a") as fh:
            fh.write("#")

        # --- writer barrier
        archive = os.path.join(F, *holdout_archive.ARCHIVE_RELPATH.split("/"))
        holder = subprocess.Popen(["sleep", "30"],
                                  cwd=os.path.join(F, "xcheck"))
        try:
            with plain_terminal():
                with self.assertRaises(KitError) as cm:
                    quiet(holdout_archive.encrypt, F, openssl=shim)
            self.assertIn("still in use", str(cm.exception))
            self.assertFalse(os.path.exists(archive))
        finally:
            holder.terminate()
            holder.wait()

        with plain_terminal():
            quiet(holdout_archive.encrypt, F, openssl=shim)
        self.assertTrue(os.path.isfile(archive))
        self.ok(self.cli(F, "rehash", "--seal", seal_path, "--sealed",
                         os.path.join(F, "sealed")))

        # --- a planted tuning-side leak, JSON-escaped (decoded pass only)
        leaked = ids[LEAK_SLOT]
        probe = diff_probe_with_escapes(F, leaked)
        hit_root = self.scan_root("leak-root", {
            "transcript.jsonl": json.dumps({"message": probe}) + "\n"})
        self.assertNotIn(probe, open(os.path.join(
            hit_root, "transcript.jsonl"), encoding="utf-8").read())
        proc = self.refused(self.cli(F, "leakscan", "--scan-root", hit_root))
        self.assertIn("(slots: %s) (JSON-decoded)" % LEAK_SLOT, proc.stdout)
        self.assertIn("slots to replace: %s" % LEAK_SLOT, proc.stdout)
        self.assertIn("cleanup, not a remedy", proc.stdout)
        self.assertNotIn(probe, proc.stdout)

        # --- the remedy is replacement: publish refuses, a clean re-scan
        # alone does not help
        proc = self.refused(self.cli(F, "publish", "--repo", publish_repo))
        self.assertIn("found holdout text", proc.stderr)
        self.assertFalse(os.path.exists(published))
        empty = self.scan_root("empty-root")
        self.ok(self.cli(F, "leakscan", "--scan-root", empty))
        proc = self.refused(self.cli(F, "publish", "--repo", publish_repo))
        self.assertIn("has not been replaced", proc.stderr)
        self.assertIn("case %s (%s)" % (LEAK_SLOT, leaked), proc.stderr)
        self.assertFalse(os.path.exists(published))
        scans = load(os.path.join(F, "LEAKSCAN.json"))["scans"]
        self.assertEqual(len(scans), 2)
        self.assertEqual(scans[0]["hit_case_ids"], [leaked])
        self.assertEqual(scans[1]["hits"], 0)
        with open(os.path.join(F, "RETIRED.json"), encoding="utf-8") as fh:
            retired_text = fh.read()
        retired = json.loads(retired_text)["retired"]
        self.assertEqual([e["slot"] for e in retired], [LEAK_SLOT])
        self.assertIsNone(ID_ANY.search(retired_text))

        # --- relabel attempt: the same change under a fresh ID
        os.remove(seal_path)
        shutil.rmtree(os.path.join(F, "archive"))
        relabeled = relabel(F, leaked)
        self.ok(self.cli(F, "validate"))
        proc = self.refused(self.cli(F, "seal"))
        self.assertIn("reuses material retired", proc.stdout)
        self.assertTrue("(source" in proc.stdout or "(diff" in proc.stdout)
        self.assertIn(relabeled, proc.stdout)
        self.assertFalse(os.path.exists(seal_path))

        # --- the remedy proper: replace the slot with a different change
        with plain_terminal():
            (old, new), _ = quiet(holdout_dryrun.replace_case, F, LEAK_SLOT)
        self.assertEqual(old, relabeled)
        self.assertNotEqual(new, old)
        self.assertEqual(len(load(os.path.join(F, "RETIRED.json"))
                             ["retired"]), 1)
        self.assertEqual(ledger(F, new)["generation"], 3)
        self.assertEqual(ledger(F, new)["workspace"], "xcheck-r3")
        self.assertIn(os.path.join(F, "xcheck-r2", ".claude",
                                   "settings.json"),
                      probe_targets(os.path.join(F, "xcheck-r3",
                                                 "sandbox-probe.py")))
        self.assertFalse(os.path.exists(cdir(F, old)))
        self.ok(self.cli(F, "validate"))
        self.ok(self.cli(F, "seal"))
        seal = load(seal_path)
        self.assertIn(new, seal["cases"])
        self.assertNotIn(old, seal["cases"])
        self.assertNotIn(leaked, seal["cases"])
        with plain_terminal():
            quiet(holdout_archive.encrypt, F, openssl=shim)
        self.ok(self.cli(F, "leakscan", "--scan-root", empty))
        scans = load(os.path.join(F, "LEAKSCAN.json"))["scans"]
        self.assertEqual(len(scans), 3)
        self.assertEqual(scans[2]["seal_sha256"],
                         holdout_kit.sha256_file(seal_path))
        self.ok(self.cli(F, "publish", "--repo", publish_repo))
        with open(published, "rb") as a, open(seal_path, "rb") as b:
            self.assertEqual(a.read(), b.read())

        # --- scrub: only the survivor allowlist remains
        probes = set(probes_v0) | all_probes(F)
        allow = holdout_archive.survivor_allowlist(F)
        expected = sorted(rel for rel in allow
                          if os.path.isfile(os.path.join(F, rel))
                          and rel != "kit/tools/holdout_kit.py")
        self.assertIn("LEAKSCAN.json", expected)
        self.assertIn("RETIRED.json", expected)
        self.ok(self.cli(F, "scrub", "--yes"))
        self.assertEqual(holdout_kit.walk_regular(F), expected)
        for rel in ("logs/finder.log", "stray-notes.txt", "xcheck",
                    "xcheck-r2", "xcheck-r3", "cfg-xcheck", "cfg-xcheck-r2",
                    "cfg-finder", "work", "sealed", "dryrun-repos",
                    "bin/finder", "bin/crosscheck", "bin/crosscheck-r2",
                    "kit/tools/holdout_kit.py"):
            self.assertFalse(os.path.exists(os.path.join(F, rel)), rel)
        self.assertEqual(len(load(os.path.join(F, "LEAKSCAN.json"))
                             ["scans"]), 3)
        self.assertEqual(len(load(os.path.join(F, "RETIRED.json"))
                             ["retired"]), 1)
        for rel in expected:
            with open(os.path.join(F, rel), "rb") as fh:
                data = fh.read().decode("utf-8", "replace")
            self.assertEqual(sum(1 for p in probes if p in data), 0, rel)

        # --- nothing was lost: the archive restores the planted plaintext
        restore = os.path.join(self.tmp, "restore")
        with plain_terminal():
            holdout_archive.decrypt_to(archive, restore, openssl=shim)
        self.ok(self.cli(F, "rehash", "--seal", seal_path, "--sealed",
                         os.path.join(restore, "sealed")))
        for rel in ("logs/finder.log", "stray-notes.txt"):
            self.assertTrue(os.path.isfile(os.path.join(restore, rel)), rel)
        for rel in ("LEAKSCAN.json", "RETIRED.json"):
            self.assertFalse(os.path.exists(os.path.join(restore, rel)), rel)

        # --- the README recovery form: decrypt back into the holdout folder,
        # rehash, then rewrite the finder skip list from RETIRED.json
        out = io.StringIO()
        with plain_terminal(), \
                mock.patch.object(holdout_archive, "OPENSSL_BIN", shim), \
                contextlib.redirect_stdout(out):
            rc = holdout_kit.run(["--folder", F, "decrypt", "--archive",
                                  "archive/holdout-v2.12.tar.enc", "--dest",
                                  F])
        self.assertEqual(rc, 0, out.getvalue())
        self.assertIn("OK: decrypted into %s" % F, out.getvalue())
        self.ok(self.cli(F, "rehash", "--seal", seal_path, "--sealed",
                         os.path.join(F, "sealed")))
        self.ok(self.cli(F, "retire", "--sync"))
        self.assertTrue(os.path.isfile(os.path.join(
            F, *holdout_manifest.RETIRED_REVISIONS_RELPATH.split("/"))))
        self.assertEqual(len(load(os.path.join(F, "LEAKSCAN.json"))
                             ["scans"]), 3)

    def c3_as_c1_cycle(self, F, ids):
        cid = ids["C1"]
        led = ledger(F, cid)
        blind_path = os.path.join(F, led["workspace"], led["xid"],
                                  "blind.json")
        blind = load(blind_path)
        blind["type_guess"] = "C3"
        dump(blind_path, blind)
        led["blind_sha256"] = holdout_kit.sha256_file(blind_path)
        dump(os.path.join(kdir(F, cid), "xcheck-ledger.json"), led)
        proc = self.refused(self.cli(F, "seal"))
        self.assertIn("Case C1: the independent check disagreed (type)",
                      proc.stdout)
        self.assertFalse(os.path.exists(os.path.join(F, "SEAL.json")))
        self.ok(self.cli(F, "crosscheck-reset", cid, "--reason", "resolved"))
        proc = self.ok(self.cli(F, "crosscheck-prepare", "--case", cid))
        self.assertIn("fresh cross-check workspace xcheck-r2", proc.stdout)
        with plain_terminal():
            holdout_dryrun.complete_case_crosscheck(F, cid)
        self.assertEqual(ledger(F, cid)["generation"], 2)
        return cid

    def test_c3_as_c1_blocks(self):
        F, ids = populated(self.tmp)
        self.c3_as_c1_cycle(F, ids)
        self.ok(self.cli(F, "seal"))
        self.assertEqual(ledger(F, ids["C1"])["generation"], 2)

    def test_stale_workspace_blocks(self):
        F, ids = populated(self.tmp)
        cid = self.c3_as_c1_cycle(F, ids)
        path = os.path.join(kdir(F, cid), "xcheck-ledger.json")
        good = load(path)
        stale = dict(good, generation=1, workspace="xcheck")
        dump(path, stale)
        proc = self.refused(self.cli(F, "seal"))
        self.assertIn("Case C1: round 2 was judged in cross-check workspace "
                      "xcheck", proc.stdout)
        self.assertFalse(os.path.exists(os.path.join(F, "SEAL.json")))
        dump(path, good)
        self.ok(self.cli(F, "seal"))


# ================================================================ grammar


class TestResumeGrammarSmoke(unittest.TestCase):

    def test_sealed_reply(self):
        self.assertEqual(holdout_manifest.resume_reply_kind("sealed"),
                         "sealed")

    def test_reply_with_case_detail_is_non_conforming(self):
        self.assertIsNone(holdout_manifest.resume_reply_kind(
            "sealed, C1 is from ZQX"))

    def test_only_one_passing_dry_run_reply(self):
        self.assertEqual(holdout_manifest.resume_reply_outcome(
            "dry run ok prompted sandbox=ok"), "proceed")
        for reply in ("dry run ok", "dry run ok prompted",
                      "dry run ok no-prompt problems=5"):
            self.assertEqual(holdout_manifest.resume_reply_outcome(reply),
                             "blocking", reply)


# ================================================================ shape


def _imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module)
    return names


class TestModuleShape(unittest.TestCase):

    def setUp(self):
        with open(DRYRUN_PY, encoding="utf-8") as fh:
            self.text = fh.read()
        self.tree = ast.parse(self.text)

    def test_import_set(self):
        self.assertEqual(_imports(self.tree),
                         {"os", "shutil", "sys", "time", "holdout_kit",
                          "holdout_manifest", "holdout_seal",
                          "holdout_validate"})

    def test_no_test_helpers_imported(self):
        self.assertNotIn("holdout_fixture", self.text)
        self.assertNotIn("import subprocess", self.text)

    def test_exports(self):
        for name in ("populate", "replace_case", "complete_case_crosscheck",
                     "add_parser", "cmd"):
            self.assertTrue(callable(getattr(holdout_dryrun, name)), name)

    def test_registered_command(self):
        self.assertEqual(holdout_kit.COMMANDS["dryrun"], "holdout_dryrun")

    def test_folder_is_never_defaulted(self):
        self.assertNotIn("vibe-check-holdout", self.text)


if __name__ == "__main__":
    unittest.main()
