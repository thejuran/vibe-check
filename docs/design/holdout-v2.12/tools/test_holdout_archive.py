"""Tests for holdout_archive — encrypt, verify, decrypt, leak scan, scrub.

Locked here:
  * encrypt stages a tar of everything in the folder except archive/, tmp/
    and the two process ledgers under tmp/owner, runs openssl with ENC_ARGS
    verbatim and no passphrase argument, decrypts the result into
    tmp/owner/verify, re-hashes it against SEAL.json and only then records
    archive_sha256. Any failure after the archive was written deletes it.
  * No passphrase ever reaches argv, the environment or a file: a fake
    openssl shim refuses every passphrase option, and an AST lock keeps the
    option names, getpass and input() out of the module.
  * encrypt and scrub refuse while any process outside the kit's own process
    tree holds the folder (cwd, open file, or argv naming it), and refuse
    when lsof or pgrep cannot run.

The real /usr/bin/openssl is never run here: it prompts on the terminal, and
the owner's dry run exercises it. Every fixture lives in a temp dir and every
passphrase-shaped value is absent by construction.
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
import tempfile
import time
import unittest
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)

import holdout_fixture  # noqa: E402
import holdout_kit  # noqa: E402
import holdout_manifest  # noqa: E402
import test_holdout_manifest as tm  # noqa: E402

import holdout_archive  # noqa: E402

ARCHIVE_PY = os.path.join(TOOLS_DIR, "holdout_archive.py")
KIT_PY = os.path.join(TOOLS_DIR, "holdout_kit.py")
ARCHIVE_REL = "archive/holdout-v2.12.tar.enc"
ID_ANY = re.compile(r"H-[0-9a-f]{8}")


# ================================================================ fixture
#
# Six cases written with tm.make_six_cases (51-05's helper), then each case's
# change.diff and key.json are replaced with distinctive content so the leak
# scan has probes: one diff line per catch slot carries a double quote, a
# backslash or a non-ASCII character, and C1's key carries a value that
# spans two lines. Every diff also has one short added line (< 30 chars)
# that must never become a probe.

SHORT_LINE = "return x"
QUOTE_LINE = 'message_c1 = "settlement window closed for account"'
BACKSLASH_LINE = 'pattern_c2 = re.compile(r"\\d{4}-\\d{2}-\\d{2}T\\d{2}")'
ACCENT_LINE = "label_c3 = 'résumé upload threshold exceeded now'"
MULTILINE_DEFECT = ("the settlement window check compares\n"
                    "local time against the UTC deadline")
GIT_DEFECT = "defect C2: the retry loop never resets its backoff counter"
SPECIAL_DIFF = {"C1": QUOTE_LINE, "C2": BACKSLASH_LINE, "C3": ACCENT_LINE}


def legacy_line(slot):
    s = slot.lower()
    return "legacy_total_%s = sum(row.amount for row in rows_%s)" % (s, s)


def normalized_line(slot):
    s = slot.lower()
    return ("normalized_total_%s = Decimal(sum(r.amount for r in rows_%s))"
            % (s, s))


def key_detail(slot):
    return "the %s settlement routine drops the final partial batch" % slot


def case_diff(slot):
    added = [normalized_line(slot)]
    if slot in SPECIAL_DIFF:
        added.append(SPECIAL_DIFF[slot])
    added.append(SHORT_LINE)
    return tm.make_diff("src/%s_ledger.py" % slot.lower(),
                        [legacy_line(slot)], added)


def case_key(slot):
    key = tm.default_key(slot)
    key["detail"] = key_detail(slot)
    if slot == "C1":
        key["defect"] = MULTILINE_DEFECT
    if slot == "C2":
        key["defect"] = GIT_DEFECT
    return key


def all_probes():
    out = {}
    for slot in holdout_kit.SLOTS:
        for p in (legacy_line(slot), normalized_line(slot), key_detail(slot)):
            out[p] = slot
        if slot in SPECIAL_DIFF:
            out[SPECIAL_DIFF[slot]] = slot
    out[MULTILINE_DEFECT] = "C1"
    out[GIT_DEFECT] = "C2"
    return out


def write_cases(folder):
    """make_six_cases + distinctive diff/key per case; return {slot: ID}."""
    ids = tm.make_six_cases(folder)
    sealed = os.path.join(folder, "sealed")
    for slot, cid in ids.items():
        with open(os.path.join(sealed, "cases", cid, "change.diff"), "w",
                  encoding="utf-8") as fh:
            fh.write(case_diff(slot))
        with open(os.path.join(sealed, "keys", cid, "key.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(case_key(slot), fh, sort_keys=True)
    return ids


def seal_build(folder):
    seal = holdout_manifest.build_seal(folder)
    holdout_manifest.write_inventory(folder)
    holdout_kit.write_json_atomic(os.path.join(folder, "SEAL.json"), seal)
    return seal


def plant(folder, rel, data="x\n"):
    path = os.path.join(folder, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data.encode("utf-8") if isinstance(data, str) else data)
    return path


# Plaintext a finished holdout carries besides sealed/: logs, finder scratch,
# later cross-check generations, a stray file and per-role scratch.
EXTRA_FILES = {
    "logs/finder.log": "finder log\n" + legacy_line("Q1") + "\n",
    "work/scratch.txt": "scratch\n",
    "xcheck-r2/X-aaaaaaaa/blind.json": '{"verdict": "x"}\n',
    "cfg-xcheck-r2/x": "x\n",
    "notes.txt": "owner notes\n",
    "tmp/junk": "junk\n",
    "tmp/finder/scratch.txt": "scratch\n",
    "tmp/crosscheck/xcheck-r2/blind-scratch.txt": "blind\n",
}

SHIM_SRC = r'''#!@@EXE@@
"""Fake openssl for tests: a reversible XOR, never a passphrase."""
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "argv.jsonl"), "a") as fh:
    fh.write(json.dumps(sys.argv) + "\n")
args = sys.argv[1:]
for a in args:
    if a in ("-pass", "-k", "-kfile") or a.startswith("pass:"):
        sys.stderr.write("refused: passphrase on argv\n")
        sys.exit(3)
code = os.environ.get("FAKE_OPENSSL_FAIL")
if code:
    sys.exit(int(code))
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


def make_shim(directory):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "fake-openssl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(SHIM_SRC.replace("@@EXE@@", sys.executable))
    os.chmod(path, 0o755)
    return path


def shim_calls(shim):
    log = os.path.join(os.path.dirname(shim), "argv.jsonl")
    if not os.path.exists(log):
        return []
    with open(log, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _clean_env():
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
    env.pop("CLAUDE_CONFIG_DIR", None)
    env.pop("FAKE_OPENSSL_FAIL", None)
    return mock.patch.dict(os.environ, env, clear=True)


_TEMPLATES = {}
_MODULE_TMP = None


def setUpModule():
    global _MODULE_TMP
    _MODULE_TMP = tempfile.TemporaryDirectory()


def tearDownModule():
    if _MODULE_TMP is not None:
        _MODULE_TMP.cleanup()


def _template(kind):
    """A cached fixture folder: 'sealed' (setup + six sealed cases + extra
    plaintext files) or 'encrypted' (the same, encrypted with the shim)."""
    if kind in _TEMPLATES:
        return _TEMPLATES[kind]
    base = os.path.realpath(os.path.join(_MODULE_TMP.name, kind))
    os.makedirs(base)
    with _clean_env():
        folder = holdout_fixture.make_fake_holdout(base)
        ids = write_cases(folder)
        seal_build(folder)
        for rel, data in EXTRA_FILES.items():
            plant(folder, rel, data)
        if kind == "encrypted":
            shim = make_shim(os.path.join(base, "shim"))
            with contextlib.redirect_stdout(io.StringIO()):
                holdout_archive.encrypt(folder, openssl=shim)
    _TEMPLATES[kind] = (folder, ids)
    return _TEMPLATES[kind]


class ArchiveCase(unittest.TestCase):
    """Base: a fresh copy of a template holdout plus a fresh shim."""

    template = "sealed"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = os.path.realpath(self._tmp.name)
        self._env = _clean_env()
        self._env.start()
        src, self.ids = _template(self.template)
        self.folder = os.path.join(self.tmp, "holdout")
        shutil.copytree(src, self.folder, symlinks=True)
        self.shim = make_shim(os.path.join(self.tmp, "shim"))
        self.archive = os.path.join(self.folder, *ARCHIVE_REL.split("/"))
        self.slot_of = {cid: slot for slot, cid in self.ids.items()}
        self._procs = []

    def tearDown(self):
        for proc in self._procs:
            if proc.poll() is None:
                proc.terminate()
            proc.wait(timeout=10)
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                if stream is not None:
                    stream.close()
        self._env.stop()
        self._tmp.cleanup()

    def p(self, rel):
        return os.path.join(self.folder, *rel.split("/"))

    def seal(self):
        with open(self.p("SEAL.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def quiet(self, fn, *args, **kwargs):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = fn(*args, **kwargs)
        return result, out.getvalue()

    def encrypt(self):
        return self.quiet(holdout_archive.encrypt, self.folder,
                          openssl=self.shim)

    def spawn(self, argv, cwd=None, stdin=None, stdout=None):
        proc = subprocess.Popen(argv, cwd=cwd or self.tmp, stdin=stdin,
                                stdout=stdout, stderr=subprocess.DEVNULL)
        self._procs.append(proc)
        return proc

    def stop(self, proc):
        proc.terminate()
        proc.wait(timeout=10)

    def run_inproc(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdout", out), \
                mock.patch.object(sys, "stderr", err):
            rc = holdout_kit.run(argv)
        return rc, out.getvalue(), err.getvalue()


# ================================================================ encrypt


class TestEncrypt(ArchiveCase):

    def test_writes_archive_and_records_hash(self):
        tmp_before = sorted(os.listdir(self.p("tmp")))
        path, out = self.encrypt()
        self.assertEqual(path, self.archive)
        self.assertTrue(os.path.isfile(self.archive))
        self.assertEqual(self.seal()["archive_sha256"],
                         holdout_kit.sha256_file(self.archive))
        self.assertEqual(holdout_manifest.public_shape_problems(self.seal()),
                         [])
        self.assertFalse(os.path.exists(self.p("tmp/owner/verify")))
        self.assertFalse(os.path.exists(self.p("tmp/owner/stage.tar")))
        self.assertEqual(sorted(os.listdir(self.p("tmp/owner"))),
                         ["SANDBOX-SENTINEL"])
        self.assertEqual(sorted(os.listdir(self.p("tmp"))), tmp_before)
        self.assertIn("OK: archive written", out)
        self.assertIn("OK: archive decrypts and re-hashes clean (6 cases)",
                      out)
        self.assertIn("OK: archive_sha256 recorded in SEAL.json", out)
        self.assertIn("Verifying: openssl will ask for the passphrase once "
                      "more", out)

    def test_openssl_argv_is_enc_args_verbatim(self):
        self.encrypt()
        calls = shim_calls(self.shim)
        self.assertEqual(len(calls), 2)
        enc, dec = calls
        stage = self.p("tmp/owner/stage.tar")
        self.assertEqual(enc, [self.shim, *holdout_archive.ENC_ARGS,
                               "-in", stage, "-out", self.archive])
        self.assertEqual(dec[:len(holdout_archive.ENC_ARGS) + 2],
                         [self.shim, "enc", "-d",
                          *holdout_archive.ENC_ARGS[1:]])
        self.assertEqual(dec[-4:-2], ["-in", self.archive])
        for call in calls:
            for bad in ("-pass", "-k", "-kfile"):
                self.assertNotIn(bad, call)

    def test_enc_args_constant(self):
        self.assertEqual(holdout_archive.ENC_ARGS,
                         ["enc", "-aes-256-cbc", "-md", "sha256", "-pbkdf2",
                          "-iter", "600000", "-salt"])
        self.assertEqual(holdout_archive.OPENSSL_BIN, "/usr/bin/openssl")
        self.assertEqual(holdout_archive.TAR_BIN, "/usr/bin/tar")

    def test_archive_members_and_exclusions(self):
        plant(self.folder, "LEAKSCAN.json", '{"schema": "x"}\n')
        plant(self.folder, "RETIRED.json", '{"schema": "y"}\n')
        self.encrypt()
        dest = os.path.join(self.tmp, "out")
        self.quiet(holdout_archive.decrypt_to, self.archive, dest,
                   openssl=self.shim)
        for name in ("sealed", "xcheck", "xcheck-r2", "cfg-xcheck-r2",
                     "cfg-finder", "kit", "work"):
            self.assertTrue(os.path.isdir(os.path.join(dest, name)), name)
        for rel in ("logs/finder.log", "work/scratch.txt", "notes.txt",
                    "bin/holdout", "SEAL.json", ".metadata_never_index",
                    "xcheck-r2/X-aaaaaaaa/blind.json"):
            self.assertTrue(os.path.isfile(os.path.join(dest, rel)), rel)
        for name in ("tmp", "archive", "LEAKSCAN.json", "RETIRED.json"):
            self.assertFalse(os.path.lexists(os.path.join(dest, name)), name)
        # The archived SEAL.json predates the archive hash.
        with open(os.path.join(dest, "SEAL.json"), encoding="utf-8") as fh:
            self.assertNotIn("archive_sha256", json.load(fh))

    def test_archive_members_listing(self):
        names = holdout_archive.archive_members(self.folder)
        self.assertEqual(names, sorted(names))
        for excluded in holdout_archive.ARCHIVE_EXCLUDES:
            self.assertNotIn(excluded, names)
        for name in ("sealed", "logs", "notes.txt", "kit", "bin",
                     "SEAL.json", ".metadata_never_index"):
            self.assertIn(name, names)
        self.assertEqual(holdout_archive.ARCHIVE_EXCLUDES,
                         ("archive", "tmp", "LEAKSCAN.json", "RETIRED.json",
                          "AUTOPILOT.json"))

    def test_archive_members_refuses_top_level_symlink(self):
        os.symlink(self.p("notes.txt"), self.p("link.txt"))
        with self.assertRaises(holdout_kit.KitError):
            holdout_archive.archive_members(self.folder)

    def test_encrypt_refuses_nested_symlink(self):
        os.symlink(self.p("notes.txt"), self.p("logs/link.txt"))
        with self.assertRaises(holdout_kit.KitError):
            self.encrypt()
        self.assertFalse(os.path.exists(self.archive))

    def test_verify_failure_deletes_archive(self):
        fake = {"ok": False, "cases": {}}
        with mock.patch.object(holdout_manifest, "rehash_folder",
                               return_value=fake):
            with self.assertRaises(holdout_kit.KitError) as ctx:
                self.encrypt()
        self.assertEqual(str(ctx.exception),
                         "archive verification failed; the archive was "
                         "deleted")
        self.assertFalse(os.path.exists(self.archive))
        self.assertNotIn("archive_sha256", self.seal())
        self.assertFalse(os.path.exists(self.p("tmp/owner/verify")))
        self.assertFalse(os.path.exists(self.p("tmp/owner/stage.tar")))

    def test_openssl_failure_leaves_no_archive(self):
        with mock.patch.dict(os.environ, {"FAKE_OPENSSL_FAIL": "5"}):
            with self.assertRaises(holdout_kit.KitError) as ctx:
                self.encrypt()
        self.assertEqual(str(ctx.exception), "openssl could not encrypt "
                                             "(exit 5)")
        self.assertFalse(os.path.exists(self.archive))
        self.assertFalse(os.path.exists(self.p("tmp/owner/stage.tar")))
        self.assertNotIn("archive_sha256", self.seal())

    def test_refuses_without_seal(self):
        os.remove(self.p("SEAL.json"))
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.encrypt()
        self.assertIn("seal first", str(ctx.exception))
        self.assertEqual(shim_calls(self.shim), [])

    def test_refuses_when_already_encrypted(self):
        self.encrypt()
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.encrypt()
        self.assertIn("already encrypted; delete archive/ deliberately to "
                      "redo", str(ctx.exception))

    def test_stale_hash_without_archive_is_cleared(self):
        # A crash after SEAL.json recorded archive_sha256 but before encrypt
        # finished leaves a hash whose archive the finally block deleted.
        seal = self.seal()
        seal["archive_sha256"] = "0" * 64
        holdout_kit.write_json_atomic(self.p("SEAL.json"), seal)
        self.assertFalse(os.path.exists(self.archive))
        self.encrypt()
        self.assertTrue(os.path.isfile(self.archive))
        self.assertEqual(self.seal()["archive_sha256"],
                         holdout_kit.sha256_file(self.archive))
        # The archived SEAL.json carries no stale hash either.
        dest = os.path.join(self.tmp, "out")
        self.quiet(holdout_archive.decrypt_to, self.archive, dest,
                   openssl=self.shim)
        with open(os.path.join(dest, "SEAL.json"), encoding="utf-8") as fh:
            self.assertNotIn("archive_sha256", json.load(fh))

    def test_crash_after_hash_recorded_keeps_archive(self):
        # Once SEAL.json names the archive, the archive is kept: an error in
        # the last progress line must not delete it behind the hash.
        real = holdout_kit.print_ok

        def boom(msg):
            if "archive_sha256 recorded" in msg:
                raise RuntimeError("synthetic crash")
            real(msg)

        with mock.patch.object(holdout_archive.holdout_kit, "print_ok",
                               side_effect=boom):
            with self.assertRaises(RuntimeError):
                self.encrypt()
        self.assertTrue(os.path.isfile(self.archive))
        self.assertEqual(self.seal()["archive_sha256"],
                         holdout_kit.sha256_file(self.archive))

    def test_crash_between_hash_write_and_ok_recovers(self):
        # The one remaining window: SEAL.json is written, ok is not yet set,
        # so finally deletes the archive. The stale-hash rule lets the next
        # encrypt redo it instead of refusing with "already encrypted".
        real_write = holdout_kit.write_json_atomic

        def write_then_crash(path, obj):
            real_write(path, obj)
            if "archive_sha256" in obj:
                raise RuntimeError("synthetic crash")

        with mock.patch.object(holdout_archive.holdout_kit,
                               "write_json_atomic",
                               side_effect=write_then_crash):
            with self.assertRaises(RuntimeError):
                self.encrypt()
        self.assertFalse(os.path.exists(self.archive))
        self.assertIn("archive_sha256", self.seal())
        self.encrypt()
        self.assertEqual(self.seal()["archive_sha256"],
                         holdout_kit.sha256_file(self.archive))

    def test_refuses_existing_archive_file(self):
        plant(self.folder, ARCHIVE_REL, b"old")
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.encrypt()
        self.assertIn("already encrypted", str(ctx.exception))
        with open(self.archive, "rb") as fh:
            self.assertEqual(fh.read(), b"old")

    def test_refuses_under_claudecode(self):
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1"}):
            with self.assertRaises(holdout_kit.KitError) as ctx:
                self.encrypt()
        self.assertEqual(str(ctx.exception), holdout_kit.REFUSE_MSG)
        self.assertEqual(shim_calls(self.shim), [])


# ================================================================ decrypt


class TestDecrypt(ArchiveCase):

    template = "encrypted"

    def test_round_trip_rehashes_clean(self):
        dest = os.path.join(self.tmp, "out")
        self.quiet(holdout_archive.decrypt_to, self.archive, dest,
                   openssl=self.shim)
        result = holdout_manifest.rehash_folder(
            self.p("SEAL.json"), os.path.join(dest, "sealed"))
        self.assertTrue(result["ok"])
        self.assertFalse(os.path.exists(os.path.join(
            self.tmp, "decrypt-stage.tar")))

    def test_corrupted_archive_fails(self):
        with open(self.archive, "r+b") as fh:
            first = fh.read(1)
            fh.seek(0)
            fh.write(bytes([first[0] ^ 0xFF]))
        dest = os.path.join(self.tmp, "out")
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.quiet(holdout_archive.decrypt_to, self.archive, dest,
                       openssl=self.shim)
        self.assertEqual(str(ctx.exception), "archive did not decrypt or "
                                             "extract")
        self.assertFalse(os.path.exists(dest))
        self.assertFalse(os.path.exists(os.path.join(
            self.tmp, "decrypt-stage.tar")))

    def test_openssl_failure(self):
        dest = os.path.join(self.tmp, "out")
        with mock.patch.dict(os.environ, {"FAKE_OPENSSL_FAIL": "1"}):
            with self.assertRaises(holdout_kit.KitError) as ctx:
                self.quiet(holdout_archive.decrypt_to, self.archive, dest,
                           openssl=self.shim)
        self.assertEqual(str(ctx.exception), "archive did not decrypt or "
                                             "extract")
        self.assertFalse(os.path.exists(dest))

    def test_decrypt_into_existing_folder_keeps_ledgers(self):
        # The documented recovery decrypts back into the holdout folder.
        plant(self.folder, "LEAKSCAN.json", "ledger\n")
        os.remove(self.p("notes.txt"))
        self.quiet(holdout_archive.decrypt_to, self.archive, self.folder,
                   openssl=self.shim,
                   stage_dir=self.p("tmp/owner"))
        self.assertTrue(os.path.isfile(self.p("notes.txt")))
        with open(self.p("LEAKSCAN.json"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "ledger\n")
        self.assertFalse(os.path.exists(self.p("tmp/owner/"
                                               "decrypt-stage.tar")))

    def test_unsafe_member_refused(self):
        # A hand-built archive whose tar holds a `..` member.
        evil = os.path.join(self.tmp, "evil")
        os.makedirs(os.path.join(evil, "a"))
        plant(evil, "a/f", "x")
        stage = os.path.join(self.tmp, "evil.tar")
        subprocess.run(["/usr/bin/tar", "-C", os.path.join(evil, "a"), "-cf",
                        stage, "-s", ",^f$,../escape,", "f"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        archive = os.path.join(self.tmp, "evil.enc")
        subprocess.run([self.shim, "enc", "-in", stage, "-out", archive],
                       check=True)
        dest = os.path.join(self.tmp, "deep", "out")
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.quiet(holdout_archive.decrypt_to, archive, dest,
                       openssl=self.shim)
        self.assertIn("unsafe path", str(ctx.exception))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "deep",
                                                     "escape")))
        self.assertFalse(os.path.exists(dest))

    def test_cli_decrypt_requires_args(self):
        rc, out, err = self.run_inproc(["--folder", self.folder, "decrypt"])
        self.assertEqual(rc, 2)


# ================================================================ writers


class TestActiveWriters(ArchiveCase):

    def sleeper_in_work(self):
        return self.spawn(["sleep", "30"], cwd=self.p("work"))

    def test_idle_folder(self):
        self.assertEqual(holdout_archive.active_writers(self.folder), [])

    def test_cwd_holder_reported(self):
        proc = self.sleeper_in_work()
        writers = holdout_archive.active_writers(self.folder)
        self.assertEqual(writers, [(proc.pid, "sleep")])
        self.stop(proc)
        self.assertEqual(holdout_archive.active_writers(self.folder), [])

    def test_argv_holder_reported(self):
        proc = self.spawn([sys.executable, "-c", "import time; "
                           "time.sleep(30)", self.p("xcheck")])
        pids = [pid for pid, _ in holdout_archive.active_writers(self.folder)]
        self.assertEqual(pids, [proc.pid])
        self.stop(proc)
        self.assertEqual(holdout_archive.active_writers(self.folder), [])

    def test_open_file_holder_reported(self):
        target = plant(self.folder, "cfg-finder/history.jsonl", "{}\n")
        proc = self.spawn(
            [sys.executable, "-c",
             "import sys,time; f=open(sys.stdin.readline().strip()); "
             "print('ready', flush=True); time.sleep(30)"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.stdin.write((target + "\n").encode())
        proc.stdin.flush()
        self.assertEqual(proc.stdout.readline().strip(), b"ready")
        pids = [pid for pid, _ in holdout_archive.active_writers(self.folder)]
        self.assertEqual(pids, [proc.pid])
        self.stop(proc)
        self.assertEqual(holdout_archive.active_writers(self.folder), [])

    def test_own_process_tree_excluded(self):
        here = os.getcwd()
        os.chdir(self.p("work"))
        try:
            self.assertEqual(holdout_archive.active_writers(self.folder), [])
        finally:
            os.chdir(here)
        own = holdout_archive._own_pids()
        self.assertIn(os.getpid(), own)
        self.assertIn(os.getppid(), own)

    def test_tuples_never_carry_a_path(self):
        proc = self.spawn([sys.executable, "-c", "import time; "
                           "time.sleep(30)", self.p("xcheck")])
        for pid, comm in holdout_archive.active_writers(self.folder):
            self.assertNotIn("/", comm)
        self.stop(proc)

    def test_encrypt_refuses_while_held(self):
        self.sleeper_in_work()
        before = self.seal()
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.encrypt()
        msg = str(ctx.exception)
        self.assertIn("holdout folder is still in use by 1 process(es)", msg)
        self.assertIn("sleep", msg)
        self.assertFalse(os.path.exists(self.p("tmp/owner/stage.tar")))
        self.assertFalse(os.path.exists(self.archive))
        self.assertEqual(self.seal(), before)
        self.assertEqual(shim_calls(self.shim), [])

    def test_mutant_barrier_is_load_bearing(self):
        self.sleeper_in_work()
        with mock.patch.object(holdout_archive, "active_writers",
                               return_value=[]):
            self.encrypt()
        self.assertTrue(os.path.isfile(self.archive))

    def test_lsof_unavailable_fails_closed(self):
        with mock.patch.object(holdout_archive, "LSOF_BIN",
                               "/nonexistent/lsof"):
            with self.assertRaises(holdout_kit.KitError) as ctx:
                holdout_archive.active_writers(self.folder)
            self.assertEqual(str(ctx.exception),
                             "cannot check for active writers (lsof "
                             "unavailable); refusing to continue")
            with self.assertRaises(holdout_kit.KitError):
                self.encrypt()
        self.assertFalse(os.path.exists(self.archive))

    def test_pgrep_unavailable_fails_closed(self):
        with mock.patch.object(holdout_archive, "PGREP_BIN",
                               "/nonexistent/pgrep"):
            with self.assertRaises(holdout_kit.KitError) as ctx:
                holdout_archive.active_writers(self.folder)
            self.assertEqual(str(ctx.exception),
                             "cannot check for active writers (pgrep "
                             "unavailable); refusing to continue")
            with self.assertRaises(holdout_kit.KitError):
                self.encrypt()
        self.assertFalse(os.path.exists(self.archive))

    def test_lsof_error_exit_fails_closed(self):
        real = holdout_kit.run_argv

        def fake(argv, **kw):
            if argv[0] == holdout_archive.LSOF_BIN:
                return subprocess.CompletedProcess(argv, 2, b"", b"err")
            return real(argv, **kw)

        with mock.patch.object(holdout_kit, "run_argv", side_effect=fake):
            with self.assertRaises(holdout_kit.KitError) as ctx:
                holdout_archive.active_writers(self.folder)
        self.assertIn("lsof unavailable", str(ctx.exception))

    def test_require_no_writers_message(self):
        with mock.patch.object(holdout_archive, "active_writers",
                               return_value=[(11, "claude"), (12, "zsh")]):
            with self.assertRaises(holdout_kit.KitError) as ctx:
                holdout_archive.require_no_writers(self.folder)
        self.assertEqual(
            str(ctx.exception),
            "holdout folder is still in use by 2 process(es): 11 claude, "
            "12 zsh; close every finder and cross-check session (/exit, then "
            "close the window), wait a few seconds, and run this again")


# ================================================================ decode


class TestDecodedStrings(unittest.TestCase):

    def test_escaped_quote(self):
        self.assertIn('x"y', holdout_archive.decoded_strings('{"a":"x\\"y"}'))

    def test_unicode_escape(self):
        self.assertIn("é", holdout_archive.decoded_strings('"\\u00e9"'))

    def test_surrogate_pair(self):
        self.assertIn("\U0001F600",
                      holdout_archive.decoded_strings('"\\ud83d\\ude00"'))

    def test_broken_literal(self):
        self.assertEqual(holdout_archive.decoded_strings('"abc'), [])

    def test_depth(self):
        text = json.dumps({"o": json.dumps({"i": "deep"})})
        self.assertIn("deep", holdout_archive.decoded_strings(text, depth=2))
        self.assertNotIn("deep",
                         holdout_archive.decoded_strings(text, depth=1))
        self.assertIn("deep", holdout_archive.decoded_strings(text))
        self.assertEqual(holdout_archive.DECODE_DEPTH, 3)

    def test_no_surrounding_quotes(self):
        out = holdout_archive.decoded_strings('{"key": "value"}')
        self.assertEqual(sorted(out), ["key", "value"])

    def test_newline_and_backslash(self):
        out = holdout_archive.decoded_strings(json.dumps("a\\b\nc"))
        self.assertIn("a\\b\nc", out)


# ================================================================ leakscan


class LeakCase(ArchiveCase):

    def setUp(self):
        super().setUp()
        self.root_a = os.path.join(self.tmp, "rootA")
        self.root_b = os.path.join(self.tmp, "rootB")
        os.makedirs(self.root_a)
        os.makedirs(self.root_b)

    def scan(self, roots=None, **kwargs):
        return self.quiet(holdout_archive.leakscan, self.folder,
                          scan_roots=roots or [self.root_a], **kwargs)

    def ledger(self):
        with open(self.p("LEAKSCAN.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def ledger_text(self):
        with open(self.p("LEAKSCAN.json"), encoding="utf-8") as fh:
            return fh.read()

    def assert_no_probe_text(self, text):
        for probe in all_probes():
            self.assertFalse(probe in text, "probe text in output")
            self.assertFalse(json.dumps(probe)[1:-1] in text,
                             "escaped probe text in output")


class TestLeakscan(LeakCase):

    def test_probe_generation(self):
        probes = holdout_archive._probes(self.folder)
        texts = {p for p, _, _ in probes}
        self.assertEqual(texts, set(all_probes()))
        for probe, slot, cid in probes:
            self.assertEqual(self.slot_of[cid], slot)
            self.assertEqual(all_probes()[probe], slot)
        self.assertNotIn(SHORT_LINE, texts)
        with open(self.p("sealed/cases/%s/change.diff" % self.ids["C1"]),
                  encoding="utf-8") as fh:
            self.assertIn("+" + SHORT_LINE + "\n", fh.read())
        for special in (QUOTE_LINE, BACKSLASH_LINE, ACCENT_LINE,
                        MULTILINE_DEFECT):
            self.assertGreaterEqual(len(special), 30)
        self.assertIn('"', QUOTE_LINE)
        self.assertIn("\\", BACKSLASH_LINE)
        self.assertIn("é", ACCENT_LINE)
        self.assertIn("\n", MULTILINE_DEFECT)

    def test_clean_roots(self):
        plant(self.root_a, "a.txt", "nothing here\n")
        result, out = self.scan()
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["probes"], len(all_probes()))
        self.assertIn("OK: leak scan: 0 matches across %d probes (raw + "
                      "JSON-decoded)" % len(all_probes()), out)

    def test_single_hit(self):
        path = plant(self.root_a, "sub/leak.txt",
                     "before\n" + legacy_line("C2") + "\nafter\n")
        result, out = self.scan()
        self.assertEqual(result["hits"], [{
            "location": path, "count": 1, "decoded": False, "slots": ["C2"],
            "case_ids": [self.ids["C2"]]}])
        self.assertEqual(result["hit_slots"], ["C2"])
        self.assertEqual(result["hit_case_ids"], [self.ids["C2"]])
        self.assertIn("PROBLEM: leak scan: 1 location(s) contain holdout "
                      "text:", out)
        self.assertIn("  %s: 1 (slots: C2)\n" % path, out)
        self.assertIn("PROBLEM: slots to replace: C2\n", out)
        self.assertIn("PROBLEM: publish will refuse until these slots are "
                      "replaced through the finder and a fresh cross-check "
                      "and the holdout is re-sealed; deleting the matched "
                      "files is cleanup, not a remedy", out)
        self.assert_no_probe_text(out)

    def test_two_cases_in_one_file(self):
        plant(self.root_a, "two.txt",
              legacy_line("Q1") + "\n" + key_detail("C3") + "\n")
        result, out = self.scan()
        self.assertEqual(len(result["hits"]), 1)
        self.assertEqual(result["hits"][0]["slots"], ["C3", "Q1"])
        self.assertEqual(result["hits"][0]["count"], 2)
        self.assertIn("PROBLEM: slots to replace: C3, Q1", out)

    def test_git_log_hit(self):
        repo = holdout_fixture.make_repo(self.tmp)
        holdout_fixture.write(repo, "readme.txt", "hello\n")
        holdout_fixture.git(repo, "add", "readme.txt")
        holdout_fixture.git(repo, "commit", "-q", "-m", GIT_DEFECT)
        result, out = self.scan(repo=repo)
        self.assertEqual([h["location"] for h in result["hits"]],
                         ["git log -p --all"])
        self.assertEqual(result["hits"][0]["slots"], ["C2"])
        self.assertIn("  git log -p --all: 1 (slots: C2)", out)

    def test_repo_tree_hit(self):
        repo = holdout_fixture.make_repo(self.tmp)
        path = holdout_fixture.write(repo, "src/x.py",
                                     normalized_line("Q3") + "\n")
        result, _ = self.scan(repo=repo)
        self.assertEqual([h["location"] for h in result["hits"]], [path])

    def test_holdout_cfg_dirs_are_not_hits(self):
        plant(self.folder, "cfg-finder/history.jsonl",
              json.dumps({"display": legacy_line("C1")}) + "\n")
        plant(self.folder, "cfg-xcheck/t.jsonl", legacy_line("C2") + "\n")
        result, _ = self.scan(roots=[self.p("cfg-finder"), self.folder,
                                     self.root_a])
        self.assertEqual(result["hits"], [])

    def test_escaped_transcripts(self):
        files = self._escaped_files()
        result, out = self.scan()
        by_loc = {h["location"]: h for h in result["hits"]}
        for path, probe, kind in files:
            self.assertIn(path, by_loc, kind)
            self.assertTrue(by_loc[path]["decoded"], kind)
            self.assertIn("  %s: " % path, out)
        self.assertIn("(JSON-decoded)", out)
        self.assert_no_probe_text(out)

    def _escaped_files(self):
        files = []
        specials = [(QUOTE_LINE, "q"), (BACKSLASH_LINE, "b"),
                    (ACCENT_LINE, "u"), (MULTILINE_DEFECT, "n")]
        for probe, tag in specials:
            variants = {
                "history.jsonl": json.dumps({"display": probe,
                                             "project": "/x"}) + "\n",
                "session.jsonl": json.dumps(
                    {"type": "tool_result",
                     "content": [{"text": "prefix\n" + probe +
                                  "\nsuffix"}]}) + "\n",
                "nested.jsonl": json.dumps(
                    {"content": json.dumps({"text": probe})}) + "\n",
                "uescape.json": json.dumps(probe, ensure_ascii=True),
            }
            for name, text in variants.items():
                self.assertFalse(probe in text, (tag, name))
                path = plant(self.root_a, "%s/%s" % (tag, name), text)
                files.append((path, probe, name))
        return files

    def test_raw_and_decoded_count_two(self):
        probe = legacy_line("Q2")
        path = plant(self.root_a, "both.txt",
                     json.dumps({"x": probe}) + "\n" + probe + "\n")
        result, out = self.scan()
        self.assertEqual(result["hits"][0]["location"], path)
        self.assertEqual(result["hits"][0]["count"], 2)
        self.assertFalse(result["hits"][0]["decoded"])
        self.assertNotIn("(JSON-decoded)", out)

    def test_mutant_decoded_pass_is_load_bearing(self):
        files = self._escaped_files()
        with mock.patch.object(holdout_archive, "decoded_strings",
                               return_value=[]):
            result, _ = self.scan()
        self.assertEqual(result["hits"], [])
        result, _ = self.scan()
        self.assertEqual(len(result["hits"]), len(files))

    def test_mutant_depth_one_drops_nested(self):
        files = self._escaped_files()
        with mock.patch.object(holdout_archive, "DECODE_DEPTH", 1):
            result, _ = self.scan()
        found = {h["location"] for h in result["hits"]}
        for path, _, kind in files:
            if kind == "nested.jsonl":
                self.assertNotIn(path, found)
            else:
                self.assertIn(path, found)

    def test_default_scan_roots(self):
        roots = holdout_archive.default_scan_roots(home="/fake/home")
        self.assertEqual(roots, [
            "/fake/home/.claude", "/fake/home/.claude/history.jsonl",
            "/private/tmp/claude-%d" % os.getuid(), "/fake/home/.codex",
            "/fake/home/.zsh_history"])

    def test_missing_sealed_needs_archive(self):
        shutil.rmtree(self.p("sealed"))
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.scan()
        self.assertEqual(str(ctx.exception), "no sealed/ to build probes "
                                             "from; use --from-archive")

    def test_missing_root_is_skipped(self):
        result, _ = self.scan(roots=[os.path.join(self.tmp, "nope"),
                                     self.root_a])
        self.assertEqual(result["hits"], [])

    def test_symlinks_are_not_followed(self):
        outside = plant(self.tmp, "outside/leak.txt", legacy_line("C1"))
        os.symlink(os.path.dirname(outside), os.path.join(self.root_a, "l"))
        result, _ = self.scan()
        self.assertEqual(result["hits"], [])


class TestLeakLedger(LeakCase):

    def test_clean_scan_entry(self):
        self.scan()
        led = self.ledger()
        self.assertEqual(led["schema"], holdout_manifest.LEAKSCAN_SCHEMA)
        self.assertEqual(len(led["scans"]), 1)
        entry = led["scans"][0]
        self.assertEqual(set(entry), {"at", "seal_sha256", "probes", "hits",
                                      "hit_case_ids", "hit_slots"})
        self.assertEqual((entry["hits"], entry["hit_case_ids"],
                          entry["hit_slots"], entry["probes"]),
                         (0, [], [], len(all_probes())))
        self.assertEqual(entry["seal_sha256"],
                         holdout_kit.sha256_file(self.p("SEAL.json")))
        self.assertRegex(entry["at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_hit_scan_appends(self):
        self.scan()
        first = self.ledger()["scans"][0]
        plant(self.root_b, "leak.txt", key_detail("Q2") + "\n")
        self.scan(roots=[self.root_b])
        led = self.ledger()
        self.assertEqual(len(led["scans"]), 2)
        self.assertEqual(led["scans"][0], first)
        self.assertEqual(led["scans"][1]["hit_case_ids"], [self.ids["Q2"]])
        self.assertEqual(led["scans"][1]["hit_slots"], ["Q2"])
        self.assertEqual(led["scans"][1]["hits"], 1)
        text = self.ledger_text()
        self.assertNotIn(self.root_b, text)
        self.assertNotIn("leak.txt", text)
        self.assert_no_probe_text(text)

    def test_unsealed_fixture_records_none(self):
        os.remove(self.p("SEAL.json"))
        self.scan()
        self.assertIsNone(self.ledger()["scans"][0]["seal_sha256"])

    def test_malformed_ledger_refused_and_kept(self):
        plant(self.folder, "LEAKSCAN.json", "not json")
        with self.assertRaises(holdout_kit.KitError):
            self.scan()
        with open(self.p("LEAKSCAN.json"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "not json")

    def test_mutant_record_is_called(self):
        plant(self.root_a, "leak.txt", legacy_line("C1") + "\n")
        with mock.patch.object(holdout_archive, "record_leakscan"):
            self.scan()
        self.assertFalse(os.path.exists(self.p("LEAKSCAN.json")))
        self.scan()
        self.assertTrue(os.path.exists(self.p("LEAKSCAN.json")))

    def test_publish_gate_reads_ledger(self):
        plant(self.root_a, "leak.txt", legacy_line("C1") + "\n")
        self.scan()
        problems = holdout_manifest.leak_ledger_problems(self.folder,
                                                         self.seal())
        self.assertTrue(any(self.ids["C1"] in p for p in problems))


class TestLeakRetire(LeakCase):

    def retired(self):
        with open(self.p("RETIRED.json"), encoding="utf-8") as fh:
            return fh.read()

    def test_hit_retires_case(self):
        plant(self.root_a, "leak.txt", normalized_line("C3") + "\n")
        _, out = self.scan()
        led = json.loads(self.retired())
        self.assertEqual(led["schema"], holdout_manifest.RETIRED_SCHEMA)
        self.assertEqual(len(led["retired"]), 1)
        self.assertEqual(led["retired"][0]["slot"], "C3")
        self.assertEqual(led["retired"][0]["reason"], "leakscan")
        problems = holdout_manifest.retired_problems(self.folder)
        self.assertTrue(any(self.ids["C3"] in p for p in problems))
        self.assertIn("PROBLEM: retired C3 (%s): its revision and content "
                      "cannot be re-sealed under any ID" % self.ids["C3"],
                      out)
        text = self.retired()
        self.assertIsNone(ID_ANY.search(text))
        self.assertNotIn(self.root_a, text)
        self.assert_no_probe_text(text)

    def test_clean_scan_creates_nothing(self):
        self.scan()
        self.assertFalse(os.path.exists(self.p("RETIRED.json")))

    def test_second_hit_appends_nothing(self):
        plant(self.root_a, "leak.txt", normalized_line("C3") + "\n")
        self.scan()
        before = json.loads(self.retired())
        self.scan()
        self.assertEqual(json.loads(self.retired()), before)

    def test_mutant_retire_is_called(self):
        plant(self.root_a, "leak.txt", normalized_line("C3") + "\n")
        with mock.patch.object(holdout_manifest, "retire_case"):
            self.scan()
        self.assertFalse(os.path.exists(self.p("RETIRED.json")))


# ================================================================ scrub

FIXED = ("SEAL.json", ".metadata_never_index", ARCHIVE_REL, "bin/holdout",
         "kit/KIT-INVENTORY.json", "LEAKSCAN.json", "RETIRED.json",
         "AUTOPILOT.json")

SCRUB_PLANTS = {
    "xcheck/X-1/blind.json": "{}\n",
    "xcheck-r2/X-2/revealed/key.json": json.dumps({"d": key_detail("C1")}),
    "cfg-xcheck/transcript.jsonl": json.dumps({"t": legacy_line("C2")}),
    "cfg-xcheck-r2/transcript.jsonl": "{}\n",
    "cfg-finder/history.jsonl": json.dumps({"display": legacy_line("Q3")}),
    "kit/notes.md": "notes\n",
    "bin/crosscheck-r2": "#!/bin/sh\n",
    "tmp/owner/verify/sealed/x": legacy_line("Q1"),
    "tmp/crosscheck/xcheck-r2/SANDBOX-SENTINEL": "s\n",
}


class ScrubCase(LeakCase):

    template = "encrypted"

    def setUp(self):
        super().setUp()
        self.home = os.path.join(self.tmp, "home")
        self.ctmp = os.path.join(self.tmp, "ctmp")
        self.bases = {"home": self.home, "tmp": self.ctmp}

    def scrub(self):
        return self.quiet(holdout_archive.scrub, self.folder,
                          residue_bases=self.bases)

    def plant_all(self):
        for rel, data in SCRUB_PLANTS.items():
            plant(self.folder, rel, data)
        with open(self.p("kit/tools/holdout_kit.py"), "ab") as fh:
            fh.write(b"#")
        plant(self.folder, "LEAKSCAN.json", '{"schema": "kept"}\n')
        plant(self.folder, "RETIRED.json", '{"schema": "kept too"}\n')

    def expected_survivors(self, modified=("kit/tools/holdout_kit.py",)):
        allow = holdout_archive.survivor_allowlist(self.folder)
        return sorted(rel for rel in allow
                      if os.path.isfile(self.p(rel)) and rel not in modified)


class TestScrub(ScrubCase):

    def test_constants(self):
        self.assertEqual(holdout_archive.SCRUB_FIXED_SURVIVORS, FIXED)
        for rel in holdout_archive.SCRUB_FIXED_SURVIVORS:
            self.assertFalse(rel.startswith("tmp/"))
            self.assertFalse(rel.startswith("work/"))
        self.assertEqual(holdout_archive.SCRUB_SETTLE_SECONDS, 2.0)

    def test_full_scrub(self):
        self.plant_all()
        expected = self.expected_survivors()
        with mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS", 0.0):
            residue, out = self.scrub()
        self.assertEqual(residue, [])
        survivors = holdout_kit.walk_regular(self.folder)
        self.assertEqual(survivors, expected)
        self.assertFalse(any(r.startswith("tmp/") for r in survivors))
        self.assertFalse(os.path.exists(self.p("tmp")))
        self.assertFalse(os.path.exists(self.p("kit/tools/holdout_kit.py")))
        self.assertTrue(os.path.exists(self.p("kit/tools/holdout_manifest.py")))
        for rel in ("logs", "work", "sealed", "xcheck", "xcheck-r2",
                    "cfg-xcheck", "cfg-xcheck-r2", "cfg-finder", "notes.txt",
                    "bin/finder", "bin/crosscheck", "bin/crosscheck-r2",
                    "kit/notes.md", "kit/eligible-repos.json"):
            self.assertFalse(os.path.lexists(self.p(rel)), rel)
        for rel in survivors:
            with open(self.p(rel), "rb") as fh:
                data = fh.read().decode("utf-8", "replace")
            self.assert_no_probe_text(data)
        self.assertRegex(out, r"OK: plaintext removed \(\d+ file\(s\) under "
                              r"[^)]*\); survivors: SEAL.json, the archive, "
                              r"bin/holdout and the unmodified kit")
        self.assertIn("logs", out)
        self.assertNotIn("finder.log", out)
        self.assertNotIn("X-1", out)
        self.assertNotIn("blind.json", out)

    def test_ledgers_survive_byte_identical(self):
        self.plant_all()
        with mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS", 0.0):
            self.scrub()
        with open(self.p("LEAKSCAN.json"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), '{"schema": "kept"}\n')
        with open(self.p("RETIRED.json"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), '{"schema": "kept too"}\n')

    def test_refuses_before_encrypt(self):
        src, _ = _template("sealed")
        shutil.rmtree(self.folder)
        shutil.copytree(src, self.folder, symlinks=True)
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.scrub()
        self.assertEqual(str(ctx.exception), "archive missing or not "
                                             "verified; run encrypt first")
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))

    def test_refuses_without_recorded_hash(self):
        seal = self.seal()
        del seal["archive_sha256"]
        holdout_kit.write_json_atomic(self.p("SEAL.json"), seal)
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.scrub()
        self.assertIn("archive missing or not verified", str(ctx.exception))
        self.assertTrue(os.path.exists(self.p("sealed")))

    def test_refuses_tampered_archive_and_mutant(self):
        with open(self.archive, "ab") as fh:
            fh.write(b"x")
        with self.assertRaises(holdout_kit.KitError):
            self.scrub()
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))
        recorded = self.seal()["archive_sha256"]
        real = holdout_kit.sha256_file

        def lying(path):
            if os.path.abspath(path) == self.archive:
                return recorded
            return real(path)

        with mock.patch.object(holdout_kit, "sha256_file",
                               side_effect=lying), \
                mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS",
                                  0.0):
            self.scrub()
        self.assertFalse(os.path.exists(self.p("logs/finder.log")))

    def test_missing_inventory_deletes_nothing(self):
        os.remove(self.p("kit/KIT-INVENTORY.json"))
        with self.assertRaises(holdout_kit.KitError):
            holdout_archive.survivor_allowlist(self.folder)
        with self.assertRaises(holdout_kit.KitError):
            self.scrub()
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))

    def test_malformed_inventory_deletes_nothing(self):
        plant(self.folder, "kit/KIT-INVENTORY.json",
              json.dumps({"files": {"../x": "0" * 64}}))
        with self.assertRaises(holdout_kit.KitError):
            self.scrub()
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))

    def test_symlink_refused_before_delete(self):
        os.symlink("/etc", self.p("work/link"))
        with self.assertRaises(holdout_kit.KitError):
            self.scrub()
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))

    def test_mutant_old_fixed_list(self):
        self.plant_all()

        def old_list(folder, allowlist):
            n = 0
            for name in ("sealed", "work", "xcheck", "cfg-finder",
                         "cfg-xcheck", "tmp"):
                path = os.path.join(folder, name)
                if os.path.isdir(path):
                    n += len(holdout_kit.walk_regular(path))
                    shutil.rmtree(path)
            return n, ["sealed"]

        with mock.patch.object(holdout_archive, "_remove_non_survivors",
                               side_effect=old_list), \
                mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS",
                                  0.0):
            with self.assertRaises(holdout_kit.KitError) as ctx:
                self.scrub()
        msg = str(ctx.exception)
        self.assertTrue(msg.startswith("scrub incomplete: "), msg)
        for name in ("logs", "notes.txt", "kit", "bin"):
            self.assertIn(name, msg)

    def test_mutant_allowlist_decides(self):
        real_walk = holdout_kit.walk_regular(self.folder)
        everything = {rel: None for rel in real_walk}
        with mock.patch.object(holdout_archive, "survivor_allowlist",
                               return_value=everything), \
                mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS",
                                  0.0):
            self.scrub()
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))
        src, _ = _template("encrypted")
        shutil.rmtree(self.folder)
        shutil.copytree(src, self.folder, symlinks=True)
        with mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS", 0.0):
            self.scrub()
        self.assertFalse(os.path.exists(self.p("logs/finder.log")))

    def test_residue_reported_not_deleted(self):
        proj = os.path.join(self.home, ".claude", "projects",
                            "-Users-x--vibe-check-holdout-work")
        os.makedirs(proj)
        plant(proj, "s.jsonl", "{}\n")
        hist = plant(self.home, ".claude/history.jsonl",
                     json.dumps({"display": "a", "project": self.folder})
                     + "\n" + json.dumps({"display": "b", "project": "/o"})
                     + "\n")
        tmpres = os.path.join(self.ctmp, "-vibe-check-holdout-xcheck")
        os.makedirs(tmpres)
        os.makedirs(os.path.join(self.home, ".claude", "paste-cache"))
        with mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS", 0.0):
            residue, out = self.scrub()
        self.assertEqual(sorted(residue), sorted([
            proj, hist, tmpres,
            os.path.join(self.home, ".claude", "paste-cache")]))
        for path in residue:
            self.assertTrue(os.path.exists(path))
        self.assertIn("PROBLEM: residue: %s — delete it by hand" % proj, out)
        self.assertIn("PROBLEM: residue: %s (1 line(s) name the holdout) — "
                      "delete those lines by hand" % hist, out)

    def test_rehash_fails_after_scrub(self):
        with mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS", 0.0):
            self.scrub()
        with self.assertRaises(holdout_kit.KitError):
            holdout_manifest.rehash_folder(self.p("SEAL.json"),
                                           self.p("sealed"))

    def test_archive_never_holds_ledgers(self):
        dest = os.path.join(self.tmp, "out")
        self.quiet(holdout_archive.decrypt_to, self.archive, dest,
                   openssl=self.shim)
        self.assertFalse(os.path.exists(os.path.join(dest, "LEAKSCAN.json")))
        self.assertFalse(os.path.exists(os.path.join(dest, "RETIRED.json")))

    def test_writer_blocks_scrub(self):
        self.spawn(["sleep", "30"], cwd=self.p("work"))
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.scrub()
        self.assertIn("holdout folder is still in use by 1 process(es)",
                      str(ctx.exception))
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))

    def test_lsof_unavailable_blocks_scrub(self):
        with mock.patch.object(holdout_archive, "LSOF_BIN",
                               "/nonexistent/lsof"):
            with self.assertRaises(holdout_kit.KitError):
                self.scrub()
        with mock.patch.object(holdout_archive, "PGREP_BIN",
                               "/nonexistent/pgrep"):
            with self.assertRaises(holdout_kit.KitError):
                self.scrub()
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))


class TestScrubSettle(ScrubCase):

    LATE = "cfg-xcheck/late.jsonl"

    def start_late_writer(self):
        self.marker = os.path.join(self.tmp, "go")
        script = ("import os, sys, time\n"
                  "marker, target = sys.argv[1], sys.argv[2]\n"
                  "while not os.path.exists(marker):\n"
                  "    time.sleep(0.05)\n"
                  "os.makedirs(os.path.dirname(target), exist_ok=True)\n"
                  "open(target, 'w').write('late\\n')\n")
        return self.spawn([sys.executable, "-c", script, self.marker,
                           self.p(self.LATE)])

    def wrapped_rewalk(self, stale=False):
        real = holdout_archive._rewalk_survivors
        calls = []

        def wrapper(folder):
            if calls and stale:
                return calls[0]
            result = real(folder)
            if not calls:
                with open(self.marker, "w") as fh:
                    fh.write("go")
            calls.append(result)
            return result
        return wrapper

    def test_late_write_fails_scrub(self):
        self.start_late_writer()
        with mock.patch.object(holdout_archive, "active_writers",
                               return_value=[]), \
                mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS",
                                  1.0), \
                mock.patch.object(holdout_archive, "_rewalk_survivors",
                                  side_effect=self.wrapped_rewalk()):
            with self.assertRaises(holdout_kit.KitError) as ctx:
                _, out = self.scrub()
        self.assertEqual(str(ctx.exception), "scrub incomplete: 1 unexpected "
                                             "file(s) remain under "
                                             "cfg-xcheck")

    def test_early_write_is_deleted(self):
        proc = self.start_late_writer()
        with open(self.marker, "w") as fh:
            fh.write("go")
        proc.wait(timeout=10)
        self.assertTrue(os.path.exists(self.p(self.LATE)))
        with mock.patch.object(holdout_archive, "active_writers",
                               return_value=[]), \
                mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS",
                                  1.0):
            _, out = self.scrub()
        self.assertFalse(os.path.exists(self.p(self.LATE)))
        self.assertIn("OK: plaintext removed", out)

    def test_mutant_second_walk_is_load_bearing(self):
        self.start_late_writer()
        with mock.patch.object(holdout_archive, "active_writers",
                               return_value=[]), \
                mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS",
                                  1.0), \
                mock.patch.object(holdout_archive, "_rewalk_survivors",
                                  side_effect=self.wrapped_rewalk(
                                      stale=True)):
            _, out = self.scrub()
        self.assertIn("OK: plaintext removed", out)
        self.assertTrue(os.path.exists(self.p(self.LATE)))


class TestLeakscanArchive(ScrubCase):

    def scrubbed(self):
        with mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS", 0.0):
            self.scrub()
        self.assertFalse(os.path.exists(self.p("sealed")))

    def test_from_archive_matches_live_scan(self):
        plant(self.root_a, "leak.txt", key_detail("Q1") + "\n")
        live, _ = self.scan()
        live_entry = json.loads(open(self.p("RETIRED.json")).read())
        os.remove(self.p("RETIRED.json"))
        os.remove(self.p("LEAKSCAN.json"))
        self.scrubbed()
        plant(self.folder, "LEAKSCAN.json", json.dumps(
            {"schema": holdout_manifest.LEAKSCAN_SCHEMA, "scans": []}))
        arch, out = self.scan(from_archive=True, openssl=self.shim)
        strip = lambda r: [(h["location"], h["count"], h["slots"])
                           for h in r["hits"]]
        self.assertEqual(strip(arch), strip(live))
        self.assertEqual(arch["probes"], live["probes"])
        self.assertFalse(os.path.exists(self.p("tmp/owner/verify")))
        self.assertFalse(os.path.exists(self.p("tmp/verify")))
        self.assertEqual(len(json.load(open(self.p("LEAKSCAN.json")))
                             ["scans"]), 1)
        archived = json.loads(open(self.p("RETIRED.json")).read())
        drop_at = lambda e: {k: v for k, v in e.items() if k != "at"}
        self.assertEqual([drop_at(e) for e in archived["retired"]],
                         [drop_at(e) for e in live_entry["retired"]])
        self.assertIn("PROBLEM: retired Q1 (%s)" % self.ids["Q1"], out)

    def test_from_archive_ledger_appends_after_scrub(self):
        self.scan()
        self.scrubbed()
        self.scan(from_archive=True, openssl=self.shim)
        self.assertEqual(len(self.ledger()["scans"]), 2)

    def test_verify_copy_removed_on_error(self):
        self.scrubbed()
        with mock.patch.object(holdout_archive, "_scan_file",
                               side_effect=RuntimeError("boom")):
            plant(self.root_a, "a.txt", "x\n")
            with self.assertRaises(RuntimeError):
                self.scan(from_archive=True, openssl=self.shim)
        self.assertFalse(os.path.exists(self.p("tmp/owner/verify")))

    def test_scrubbed_without_archive_flag(self):
        self.scrubbed()
        with self.assertRaises(holdout_kit.KitError) as ctx:
            self.scan()
        self.assertEqual(str(ctx.exception), "no sealed/ to build probes "
                                             "from; use --from-archive")


# ================================================================ CLI


class TestCliArchive(ScrubCase):

    def cli(self, *args):
        with mock.patch.object(holdout_archive, "_default_residue_bases",
                               return_value=self.bases), \
                mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS",
                                  0.0):
            return self.run_inproc(["--folder", self.folder, *args])

    def test_refuses_under_claudecode(self):
        env = {"CLAUDECODE": "1",
               "CLAUDE_CONFIG_DIR": self.p("cfg-finder")}
        for argv in (["encrypt"], ["scrub", "--yes"],
                     ["leakscan", "--scan-root", self.root_a],
                     ["decrypt", "--archive", ARCHIVE_REL, "--dest",
                      os.path.join(self.tmp, "out")]):
            with mock.patch.dict(os.environ, env):
                rc, out, err = self.cli(*argv)
            self.assertEqual(rc, 1, argv)
            self.assertEqual(err, holdout_kit.REFUSE_MSG + "\n", argv)
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "out")))
        self.assertFalse(os.path.exists(self.p("LEAKSCAN.json")))

    def test_scrub_without_yes_prints_plan(self):
        rc, out, err = self.cli("scrub")
        self.assertEqual(rc, 0, err)
        self.assertIn("Re-run with --yes to remove the plaintext.", out)
        self.assertIn("logs", out)
        self.assertNotIn("finder.log", out)
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))

    def test_scrub_yes(self):
        rc, out, err = self.cli("scrub", "--yes")
        self.assertEqual(rc, 0, err)
        self.assertEqual(sorted(os.listdir(self.folder)),
                         [".metadata_never_index", "SEAL.json", "archive",
                          "bin", "kit"])
        self.assertEqual(os.listdir(self.p("bin")), ["holdout"])

    def test_scrub_before_encrypt(self):
        src, _ = _template("sealed")
        shutil.rmtree(self.folder)
        shutil.copytree(src, self.folder, symlinks=True)
        rc, out, err = self.cli("scrub", "--yes")
        self.assertEqual(rc, 1)
        self.assertIn("PROBLEM: archive missing or not verified; run encrypt "
                      "first", out)
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))

    def test_scrub_incomplete_exit(self):
        with mock.patch.object(holdout_archive, "_remove_non_survivors",
                               return_value=(0, [])):
            rc, out, err = self.cli("scrub", "--yes")
        self.assertEqual(rc, 1)
        self.assertTrue(err.startswith("holdout: scrub incomplete: "), err)
        self.assertNotIn("OK: plaintext removed", out)

    def test_scrub_writer_cli(self):
        self.spawn(["sleep", "30"], cwd=self.p("work"))
        rc, out, err = self.cli("scrub", "--yes")
        self.assertEqual(rc, 1)
        self.assertTrue(err.startswith("holdout: holdout folder is still in "
                                       "use by 1 process(es)"), err)
        self.assertTrue(os.path.exists(self.p("logs/finder.log")))

    def test_leakscan_cli_decoded_hit(self):
        plant(self.root_b, "t.jsonl", json.dumps({"text": QUOTE_LINE}))
        rc, out, err = self.cli("leakscan", "--scan-root", self.root_b)
        self.assertEqual(rc, 1, err)
        self.assertIn("PROBLEM: leak scan: 1 location(s) contain holdout "
                      "text:", out)
        self.assertRegex(out, r"\(slots: C1\) \(JSON-decoded\)\n")
        self.assertNotIn(QUOTE_LINE, out)
        self.assertIn("OK: tuning repo not scanned (pass --repo)", out)

    def test_leakscan_cli_clean(self):
        rc, out, err = self.cli("leakscan", "--scan-root", self.root_a)
        self.assertEqual(rc, 0, err)
        m = re.search(r"OK: leak scan: 0 matches across (\d+) probes \(raw "
                      r"\+ JSON-decoded\)", out)
        self.assertIsNotNone(m)
        self.assertGreaterEqual(int(m.group(1)), 6)

    def test_cli_encrypt_scrub_decrypt_rehash(self):
        # Drives the documented recovery through holdout_kit.run: encrypt,
        # scrub, decrypt back into the folder, rehash. Works on a sealed
        # (unencrypted) copy so encrypt runs through the CLI too.
        src, _ = _template("sealed")
        shutil.rmtree(self.folder)
        shutil.copytree(src, self.folder, symlinks=True)
        with mock.patch.object(holdout_archive, "OPENSSL_BIN", self.shim), \
                mock.patch.object(holdout_archive, "_default_residue_bases",
                                  return_value=self.bases), \
                mock.patch.object(holdout_archive, "SCRUB_SETTLE_SECONDS",
                                  0.0):
            rc, out, err = self.run_inproc(["--folder", self.folder,
                                            "encrypt"])
            self.assertEqual(rc, 0, err)
            self.assertIn("OK: archive_sha256 recorded in SEAL.json", out)
            rc, out, err = self.run_inproc(["--folder", self.folder, "scrub",
                                            "--yes"])
            self.assertEqual(rc, 0, err)
            self.assertFalse(os.path.exists(self.p("sealed")))
            rc, out, err = self.run_inproc(
                ["--folder", self.folder, "decrypt", "--archive", ARCHIVE_REL,
                 "--dest", self.folder])
            self.assertEqual(rc, 0, err)
            self.assertIn("OK: decrypted", out)
        rc, out, err = self.run_inproc(
            ["--folder", self.folder, "rehash", "--seal", self.p("SEAL.json"),
             "--sealed", self.p("sealed")])
        self.assertEqual(rc, 0, out + err)
        self.assertIn("OK: all 6 cases match the seal", out)
        self.assertTrue(os.path.isfile(self.p("logs/finder.log")))


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
        with open(ARCHIVE_PY, encoding="utf-8") as fh:
            self.text = fh.read()
        self.tree = ast.parse(self.text)

    def test_import_set(self):
        self.assertEqual(_imports(self.tree),
                         {"json", "os", "re", "shutil", "stat", "sys", "time",
                          "holdout_kit", "holdout_manifest"})

    def test_no_passphrase_option_literals(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for bad in ("-pass", "-k", "-kfile", "pass:"):
                    self.assertFalse(node.value.startswith(bad), node.value)
        self.assertNotIn('"-pass"', self.text)
        self.assertNotIn('"-k"', self.text)
        self.assertNotIn('"-kfile"', self.text)
        self.assertNotIn("pass:", self.text)

    def test_no_prompt_in_python(self):
        self.assertNotIn("getpass", self.text)
        self.assertNotIn("input(", self.text)
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, ("input", "getpass"))

    def test_environment_access_is_narrow(self):
        allowed = {"CLAUDECODE", "CLAUDE_CONFIG_DIR", "HOME", "UID"}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Attribute) and node.attr in (
                    "environ", "getenv", "putenv", "environb"):
                self.fail("module touches os.%s directly" % node.attr)
        for name in allowed:
            self.assertNotIn("os.environ[%r]" % name, self.text)

    def test_iteration_count_appears_once(self):
        self.assertEqual(self.text.count('"600000"'), 1)

    def test_no_shell_and_no_popen(self):
        self.assertFalse("shell=True" in self.text)
        self.assertFalse("Popen" in self.text)
        self.assertFalse("import subprocess" in self.text)
        self.assertFalse("subprocess." in self.text)


if __name__ == "__main__":
    unittest.main()
