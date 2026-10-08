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
        self.assertEqual(dec[:len(holdout_archive.ENC_ARGS) + 1],
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
                         ("archive", "tmp", "LEAKSCAN.json", "RETIRED.json"))

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
        self.assertNotIn("shell=True", self.text)
        self.assertNotIn("Popen", self.text)
        self.assertNotIn("subprocess", self.text)


if __name__ == "__main__":
    unittest.main()
