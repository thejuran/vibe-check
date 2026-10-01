"""test_codex_collect.py — the DYNAMIC half of the Codex collection locks.

The STATIC locks (no harness read tool in the prose, the atomic rc write, the
bounded wait, the payload path, no cleanup) live in `test_agent_prompts.py` and
scan text. This module runs the REAL fenced blocks instead:

  * the Phase 2c step-4 launch block (the fence holding the ARGS line) from
    `phases/deep-review/2c-codex-kickoff.md`, and
  * the Phase 3 step-2 collect block (the fence holding the REMAIN line) from
    `phases/deep-review/30-codex-collect.md`.

Both are extracted from the files, never retyped. Rendering only substitutes
the `VAR="<placeholder>"` values, replaces `<codex_args>` with `--base main`,
shortens the watchdog `-k 10 300` to `-k 1 2` and the wait bound
`LAUNCHED_AT + 315` to `LAUNCHED_AT + 3`. Everything runs under a
TemporaryDirectory with a stub `codex-companion.mjs` whose behavior is chosen
by the STUB_MODE env var, and with CLAUDE_PLUGIN_ROOT / VIBE_CHECK_PLUGIN_ROOT
removed from the environment. The launch runs in the background (Popen) while
the collect block runs in the foreground, as in a real review.
"""

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

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
KICKOFF = os.path.join(PLUGIN_ROOT, "phases", "deep-review", "2c-codex-kickoff.md")
COLLECT = os.path.join(PLUGIN_ROOT, "phases", "deep-review", "30-codex-collect.md")

ARGS_LINE = 'ARGS=(adversarial-review --json <codex_args> "$CODEX_FOCUS")'
REMAIN_LINE = "REMAIN=$(( LAUNCHED_AT + 315 - $(date +%s) ))"
KICKOFF_TIMED_REMAIN = "REMAIN=$(( STARTED_AT + 315 - $(date +%s) ))"
RC_ATOMIC_LINE = ('''printf '%s\\n' "$rc" > "$CODEX_DIR/rc.tmp" && '''
                  '''mv "$CODEX_DIR/rc.tmp" "$CODEX_DIR/rc"''')

TIMEOUT_BIN = shutil.which("timeout") or shutil.which("gtimeout")
NODE_BIN = shutil.which("node")
CAP = 2          # rendered watchdog cap (seconds), replaces 300
WAIT_BOUND = 3   # rendered wait bound (seconds), replaces 315
MARGIN = 10      # wall-clock slack on top of the wait bound
LATE_LAUNCH = 5  # seconds the launch trails STARTED_AT in the late-launch case

STUB = """\
const mode = process.env.STUB_MODE || "ok";
if (mode === "ok") {
  process.stdout.write(JSON.stringify({result: {findings: []}}) + "\\n");
  process.exit(0);
} else if (mode === "slow") {
  // Finishes inside the cap, but later than the kickoff-timed wait would allow.
  setTimeout(() => {
    process.stdout.write(JSON.stringify({result: {findings: []}}) + "\\n");
    process.exit(0);
  }, 1500);
} else if (mode === "hang") {
  setTimeout(() => process.exit(0), 30000);
} else {
  process.stderr.write("stub failure\\n");
  process.exit(3);
}
"""


def skip_reason():
    """Why the dynamic tests cannot run here, naming the missing binary; None when they can."""
    if not TIMEOUT_BIN:
        return "neither timeout nor gtimeout is on PATH"
    if not NODE_BIN:
        return "node is not on PATH"
    return None


def fenced_block_with(path, needle):
    """Raw text of the first ``` fenced block in `path` holding a line whose
    stripped form equals `needle`, dedented by the fence's own indent."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    block, inside, indent = [], False, ""
    for ln in lines:
        if ln.strip().startswith("```"):
            if inside:
                if any(b.strip() == needle for b in block):
                    return "\n".join(b[len(indent):] if b.startswith(indent) else b
                                     for b in block) + "\n"
                block = []
            else:
                indent = ln[:len(ln) - len(ln.lstrip())]
            inside = not inside
            continue
        if inside:
            block.append(ln)
    raise AssertionError("no fenced block in %s holds %r" % (path, needle))


_PLACEHOLDER = re.compile(r'\b([A-Z_]+)="<[^>"]*>"')


def render(block, values, replacements):
    """Substitute every VAR="<...>" placeholder from `values` (each must be
    used, none may be left over) and apply the literal `replacements`, each of
    which must match exactly once."""
    used = set()

    def sub(m):
        name = m.group(1)
        if name not in values:
            raise AssertionError("unexpected placeholder %s" % name)
        value = str(values[name])
        if any(ch in value for ch in '"$`\\'):
            raise AssertionError("unsafe test value for %s" % name)
        used.add(name)
        return '%s="%s"' % (name, value)

    out = _PLACEHOLDER.sub(sub, block)
    if used != set(values):
        raise AssertionError("placeholders not found: %s" % sorted(set(values) - used))
    for old, new in replacements:
        if out.count(old) != 1:
            raise AssertionError("%r occurs %d times" % (old, out.count(old)))
        out = out.replace(old, new)
    if '"<' in out:
        raise AssertionError("an unrendered placeholder remains")
    return out


@unittest.skipIf(skip_reason() is not None, skip_reason() or "")
class TestCodexCollectExecutable(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = self._tmp.name
        self.vc_root = os.path.join(base, "vc")
        os.makedirs(os.path.join(self.vc_root, "templates"))
        self.focus = os.path.join(self.vc_root, "templates", "codex-focus.txt")
        with open(self.focus, "w", encoding="utf-8") as fh:
            fh.write("Calibration rules for the stub.\n")
        self.companion_root = os.path.join(base, "codex")
        os.makedirs(os.path.join(self.companion_root, "scripts"))
        stub = os.path.join(self.companion_root, "scripts", "codex-companion.mjs")
        with open(stub, "w", encoding="utf-8") as fh:
            fh.write(STUB)
        os.chmod(stub, stat.S_IRWXU)
        self.codex_dir = tempfile.mkdtemp(dir=base)
        self.launch_block = fenced_block_with(KICKOFF, ARGS_LINE)
        self.collect_block = fenced_block_with(COLLECT, REMAIN_LINE)

    def tearDown(self):
        self._tmp.cleanup()

    def _env(self, mode):
        env = {k: v for k, v in os.environ.items()
               if k not in ("CLAUDE_PLUGIN_ROOT", "VIBE_CHECK_PLUGIN_ROOT")}
        env["STUB_MODE"] = mode
        return env

    def _launch(self, started_at, drop_mv=False):
        text = render(self.launch_block, {
            "CODEX_ACTION": "run",
            "CODEX_PLUGIN_ROOT": self.companion_root,
            "TIMEOUT_BIN": TIMEOUT_BIN,
            "VC_ROOT": self.vc_root,
            "CODEX_DIR": self.codex_dir,
            "STARTED_AT": started_at,
        }, [("<codex_args>", "--base main"), ("-k 10 300", "-k 1 %d" % CAP)])
        if drop_mv:
            assert text.count(RC_ATOMIC_LINE) == 1
            text = text.replace(RC_ATOMIC_LINE, '''printf '%s\\n' "$rc" > "$CODEX_DIR/rc.tmp"''')
        return text

    def _collect(self, started_at, kickoff_timed=False):
        block = self.collect_block
        if kickoff_timed:  # the pre-fix wait, timed from STARTED_AT (control only)
            assert block.count(REMAIN_LINE) == 1
            block = block.replace(REMAIN_LINE, KICKOFF_TIMED_REMAIN)
            bound = ("STARTED_AT + 315", "STARTED_AT + %d" % WAIT_BOUND)
        else:
            bound = ("LAUNCHED_AT + 315", "LAUNCHED_AT + %d" % WAIT_BOUND)
        return render(block, {
            "CODEX_DIR": self.codex_dir,
            "STARTED_AT": started_at,
            "TIMEOUT_BIN": TIMEOUT_BIN,
        }, [bound])

    def _collect_run(self, started_at, mode, kickoff_timed=False):
        """Run the rendered collect block in the foreground. If it outlives its
        30 s guard, create rc so an orphaned `until [ -e rc ]` loop exits too."""
        try:
            return subprocess.run(["bash", "-c", self._collect(started_at, kickoff_timed)],
                                  env=self._env(mode), capture_output=True, text=True,
                                  timeout=30)
        except subprocess.TimeoutExpired:
            with open(os.path.join(self.codex_dir, "rc"), "w", encoding="utf-8") as fh:
                fh.write("unblock\n")
            time.sleep(3)
            raise

    def _run(self, mode, drop_mv=False, launch_delay=0, kickoff_timed=False):
        """Launch in the background, collect in the foreground; return
        (collect stdout, rc file content or None, elapsed seconds).
        `launch_delay` > 0 dates STARTED_AT that many seconds before the launch
        and starts collecting only once the launch has recorded launched_at."""
        t0 = time.monotonic()
        started_at = int(time.time()) - launch_delay
        proc = subprocess.Popen(["bash", "-c", self._launch(started_at, drop_mv)],
                                env=self._env(mode), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        try:
            if launch_delay:
                marker = os.path.join(self.codex_dir, "launched_at")
                deadline = time.monotonic() + 10
                while not os.path.exists(marker) and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(os.path.exists(marker), "launch never recorded launched_at")
            res = self._collect_run(started_at, mode, kickoff_timed)
            elapsed = time.monotonic() - t0
        finally:
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=30)
        self.assertEqual(res.returncode, 0, res.stderr)
        rc_path = os.path.join(self.codex_dir, "rc")
        rc = None
        if os.path.exists(rc_path):
            with open(rc_path, encoding="utf-8") as fh:
                rc = fh.read().strip()
        return res.stdout, rc, elapsed

    def test_render_touches_only_the_placeholders(self):
        rendered = self._launch(0).splitlines()
        original = self.launch_block.splitlines()
        self.assertEqual(len(rendered), len(original))
        changed = [o.strip() for o, r in zip(original, rendered) if o != r]
        self.assertEqual([c.split("=")[0].split(" ")[0] for c in changed],
                         ["CODEX_ACTION", "CODEX_PLUGIN_ROOT", "VC_ROOT", "CODEX_DIR", "ARGS",
                          '"$TIMEOUT_BIN"'], changed)

    def test_joined(self):
        out, rc, _ = self._run("ok")
        self.assertIn("CODEX_COLLECT=join", out)
        self.assertEqual(rc, "0")
        with open(os.path.join(self.codex_dir, "payload.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), {"result": {"findings": []}})

    def test_late_launch_finishing_near_the_cap_joins(self):
        # The launch trails STARTED_AT by LATE_LAUNCH s and the companion exits 0
        # inside the cap: the wait is timed from launched_at, so it joins.
        out, rc, _ = self._run("slow", launch_delay=LATE_LAUNCH)
        self.assertEqual(rc, "0")
        self.assertIn("CODEX_COLLECT=join", out)

    def test_kickoff_timed_wait_would_drop_the_late_launch(self):
        # Control: the same run with the wait timed from STARTED_AT gives up
        # before rc exists, so the join above is not vacuous.
        out, _rc, _ = self._run("slow", launch_delay=LATE_LAUNCH, kickoff_timed=True)
        self.assertIn("CODEX_COLLECT=timeout", out)

    def test_hang_hits_the_cap_without_hanging_collect(self):
        out, rc, elapsed = self._run("hang")
        self.assertEqual(rc, "124")
        self.assertIn("CODEX_COLLECT=timeout", out)
        self.assertLess(elapsed, WAIT_BOUND + MARGIN)

    def test_abnormal_exit_is_a_timeout_skip(self):
        out, rc, _ = self._run("fail")
        self.assertEqual(rc, "3")
        self.assertIn("CODEX_COLLECT=timeout", out)
        with open(os.path.join(self.codex_dir, "stderr"), encoding="utf-8") as fh:
            self.assertIn("stub failure", fh.read())

    def test_focus_backstop_reaches_collect_through_rc(self):
        with open(self.focus, "w", encoding="utf-8"):
            pass  # an empty calibration file: the guard trips
        out, rc, _ = self._run("ok")
        self.assertEqual(rc, "focus-missing")
        self.assertIn("CODEX_COLLECT=focus-unreadable", out)
        self.assertFalse(os.path.exists(os.path.join(self.codex_dir, "payload.json")))

    def test_wait_is_bounded_when_rc_never_appears(self):
        # Nothing was launched: collect alone must give up at the wait bound.
        t0 = time.monotonic()
        res = self._collect_run(int(time.time()), "ok")
        elapsed = time.monotonic() - t0
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("CODEX_COLLECT=timeout", res.stdout)
        self.assertGreaterEqual(elapsed, WAIT_BOUND - 1.5)
        self.assertLess(elapsed, WAIT_BOUND + MARGIN)

    def test_rc_file_is_the_only_completion_signal(self):
        # Without the rename, a successful run never signals completion.
        out, rc, elapsed = self._run("ok", drop_mv=True)
        self.assertIsNone(rc)
        self.assertIn("CODEX_COLLECT=timeout", out)
        self.assertLess(elapsed, WAIT_BOUND + MARGIN)


class TestModuleHygiene(unittest.TestCase):
    ALLOWED = {"json", "os", "re", "shutil", "stat", "subprocess", "sys", "tempfile",
               "time", "unittest"}

    def _source(self):
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            return fh.read()

    def test_imports_are_exactly_the_allowed_set(self):
        found = set(re.findall(r"^import (\w+)", self._source(), re.MULTILINE))
        found |= set(re.findall(r"^from (\w+)", self._source(), re.MULTILINE))
        self.assertEqual(found, self.ALLOWED)

    def test_every_subprocess_run_carries_timeout(self):
        src = self._source()
        calls = 0
        # Code calls only: the call opens a statement (optionally an assignment or return).
        for m in re.finditer(r"^[ \t]*(?:\w+ = |return )?subprocess\.run\(", src, re.MULTILINE):
            depth, i = 1, m.end()
            while depth:
                depth += {"(": 1, ")": -1}.get(src[i], 0)
                i += 1
            calls += 1
            self.assertIn("timeout=", src[m.end():i],
                          "subprocess.run without timeout: %r" % src[m.start():i][:80])
        self.assertGreater(calls, 0, "found no subprocess.run calls -- test is vacuous")

    def test_skip_reason_names_the_binary(self):
        reason = skip_reason()
        if TIMEOUT_BIN and NODE_BIN:
            self.assertIsNone(reason)
        elif not TIMEOUT_BIN:
            self.assertIn("timeout", reason)
            self.assertIn("gtimeout", reason)
        else:
            self.assertIn("node", reason)


if __name__ == "__main__":
    sys.exit(unittest.main())
