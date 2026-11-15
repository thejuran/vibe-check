"""Inline Python in the instruction files never imports from the reviewed repo.

The instruction files run their shell blocks with the reviewed repository as
the working directory. `python3 -c '...'` (and `-m`, or a script read from
stdin) puts that directory first on the module search path, so a file named
`json.py` at the reviewed repo's root would run in place of the standard
library. Every inline invocation therefore carries `-I` (isolated mode: no
current directory, no user site folder, no `PYTHON*` variables). The helper
scripts are run as `python3 "$VC_ROOT/scripts/x.py"`, which puts the script's
own folder first, not the working directory; one case below pins that too.

The behavioural cases take the real program text from the live files and run
it in a temporary directory that holds a planted `json.py`. The planted module
only creates a marker file inside that temporary directory.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_cross_call_vars import PLUGIN_ROOT, bash_fences, read_rel  # noqa: E402

BASH = "/bin/bash"
MARKER = "PLANTED_RAN"
PLANTED = ("import os\nopen(os.path.join(os.path.dirname(os.path.abspath("
           "__file__)), %r), 'w').close()\n" % MARKER)

# A command word `python`, `python3` or `python3.N`, its leading options, and
# what makes it inline: `-c`, `-m`, or `-` (a script on stdin).
_PY = re.compile(
    r"(?<![\w.$-])(python(?:3(?:\.\d+)?)?)((?:[ \t]+-[A-Za-z]+)*?)"
    r"[ \t]+(-c\b|-m\b|-(?=[ \t]|$))", re.M)

FINALIZE_REL = "phases/shared/90-finalize.md"
FIX_LOOP_REL = "phases/review/50-fix-loop.md"

# Today's inline invocations by file. A change is fine, but it must be seen.
EXPECTED_COUNTS = {
    "phases/deep-review/01d-coverage.md": 1,
    "phases/deep-review/2c-codex-kickoff.md": 2,
    "phases/deep-review/30-codex-collect.md": 1,
    "phases/review/05-state-all.md": 2,
    "phases/review/50-fix-loop.md": 3,
    FINALIZE_REL: 3,
}


def instruction_files():
    """Every shipped non-Python file under the plugin root, by relative path.
    `scripts/` holds the helpers and their tests, not instructions."""
    found = []
    for dirpath, dirnames, filenames in os.walk(PLUGIN_ROOT):
        rel_dir = os.path.relpath(dirpath, PLUGIN_ROOT).replace(os.sep, "/")
        if rel_dir == "scripts" or rel_dir.startswith("scripts/"):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
        for name in filenames:
            if name.endswith((".md", ".json", ".txt", ".sh", ".toml", ".yml",
                              ".yaml")):
                rel = os.path.join(rel_dir, name) if rel_dir != "." else name
                found.append(rel.replace(os.sep, "/"))
    return sorted(found)


def inline_invocations(text):
    """[(options text, kind)] for every inline Python invocation in `text`."""
    return [(m.group(2), m.group(3)) for m in _PY.finditer(text)]


def missing_isolation(texts):
    """[(path, invocation)] for each inline invocation without `-I`."""
    bad = []
    for rel, text in sorted(texts.items()):
        for opts, kind in inline_invocations(text):
            if "-I" not in opts.split():
                bad.append((rel, ("python3%s %s" % (opts, kind)).strip()))
    return bad


def all_texts():
    texts = {}
    for rel in instruction_files():
        with open(os.path.join(PLUGIN_ROOT, rel), encoding="utf-8") as fh:
            texts[rel] = fh.read()
    return texts


_PROGRAM = re.compile(r"python3((?:[ \t]+-[A-Za-z]+)*)[ \t]+-c[ \t]+'([^']*)'")


def programs(relpath):
    """[(options, program text)] of each `python3 ... -c '<program>'` in the
    Bash fences of `relpath`, each fence dedented as the model runs it."""
    found = []
    for _, body in bash_fences(read_rel(relpath)):
        for m in _PROGRAM.finditer(textwrap.dedent(body)):
            found.append((m.group(1).split(), m.group(2)))
    return found


class Planted(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        with open(os.path.join(self.tmp, "json.py"), "w") as fh:
            fh.write(PLANTED)

    def marker(self):
        return os.path.exists(os.path.join(self.tmp, MARKER))

    def run_inline(self, options, program, stdin, args=()):
        """Run `python3 <options> -c <program> <args>` under /bin/bash in the
        planted directory, the way a fence runs it."""
        argv = ["python3"] + list(options) + ["-c", program] + list(args)
        script = " ".join(_sh_quote(a) for a in argv)
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        proc = subprocess.run([BASH, "-c", script], input=stdin, cwd=self.tmp,
                              env=env, capture_output=True, text=True,
                              timeout=30)
        return proc.returncode, proc.stdout, proc.stderr

    def reset(self):
        path = os.path.join(self.tmp, MARKER)
        if os.path.exists(path):
            os.remove(path)


def _sh_quote(word):
    return "'" + word.replace("'", "'\\''") + "'"


class TestEveryInlineInvocationIsIsolated(unittest.TestCase):
    def test_the_scan_sees_the_known_invocations(self):
        texts = all_texts()
        self.assertIn("commands/review.md", texts)
        self.assertIn("hooks/hooks.json", texts)
        counts = {rel: len(inline_invocations(t)) for rel, t in texts.items()
                  if inline_invocations(t)}
        self.assertEqual(counts, EXPECTED_COUNTS)

    def test_every_inline_invocation_carries_dash_capital_i(self):
        self.assertEqual(missing_isolation(all_texts()), [])

    def test_the_scan_catches_each_form(self):
        cases = {
            "python3 -c 'import json'": 1,
            "x=$(python3 -c '\nimport json')": 1,
            "printf x | python3 -c 'pass'": 1,
            "python -c 'pass'": 1,
            "python3.9 -c 'pass'": 1,
            "python3 -m json.tool": 1,
            "python3 - <<'PY'\nprint(1)\nPY": 1,
            "python3 -u -c 'pass'": 1,
            'python3 "$VC_ROOT/scripts/score.py"': 0,
            "`python3` on the trusted scripts": 0,
            "a /usr/bin/python3x -c": 0,
            "/usr/bin/python3 -c 'pass'": 1,
        }
        for text, want in cases.items():
            with self.subTest(text):
                self.assertEqual(len(missing_isolation({"f": text})), want)
        self.assertEqual(missing_isolation({"f": "python3 -I -c 'pass'"}), [])
        self.assertEqual(missing_isolation({"f": "python3 -u -I -c 'x'"}), [])

    def test_each_finalize_and_fix_loop_program_is_found(self):
        for rel in (FINALIZE_REL, FIX_LOOP_REL):
            with self.subTest(rel):
                self.assertEqual(len(programs(rel)), 3)


# Inputs for the Finalize / fix-loop one-liners, by what each reads.
PARSE = {"payload": {"decisions": [1, 2]}, "fix_targets": ["a.ts:3"],
         "grammar": "fix all"}


def expected_output(program):
    if '["payload"]' in program:
        return json.dumps(PARSE["payload"])
    if '["fix_targets"]' in program:
        return json.dumps(PARSE["fix_targets"])
    if '["grammar"]' in program:
        return json.dumps({"q1": PARSE["grammar"], "q2": None})
    raise AssertionError("unknown program %r" % program)


class TestPlantedModuleDoesNotRun(Planted):
    """The real one-liners, run in a folder holding a planted `json.py`."""

    def test_finalize_and_fix_loop_commands(self):
        for rel in (FINALIZE_REL, FIX_LOOP_REL):
            for options, program in programs(rel):
                with self.subTest(rel=rel, program=program):
                    self.reset()
                    rc, out, err = self.run_inline(options, program,
                                                   json.dumps(PARSE))
                    self.assertFalse(self.marker(), "planted json.py ran")
                    self.assertEqual(rc, 0, err)
                    self.assertEqual(out, expected_output(program))

    def test_without_dash_capital_i_the_planted_module_runs(self):
        # The mutant: the same command with `-I` taken out.
        for rel in (FINALIZE_REL, FIX_LOOP_REL):
            for options, program in programs(rel):
                with self.subTest(rel=rel, program=program):
                    self.reset()
                    bare = [o for o in options if o != "-I"]
                    self.run_inline(bare, program, json.dumps(PARSE))
                    self.assertTrue(self.marker(), "the mutant was not caught")

    def test_every_other_program_in_the_fences(self):
        # Programs that read argv: given empty input and placeholder
        # arguments they may fail, but must never import the planted module.
        rels = [r for r in EXPECTED_COUNTS
                if r not in (FINALIZE_REL, FIX_LOOP_REL)]
        seen = 0
        for rel in rels:
            for options, program in programs(rel):
                seen += 1
                with self.subTest(rel=rel):
                    self.reset()
                    self.run_inline(options, program, "{}",
                                    ["a", "b", "--", "c", "d"])
                    self.assertFalse(self.marker(), "planted json.py ran")
                    self.reset()
                    self.run_inline([o for o in options if o != "-I"],
                                    program, "{}", ["a", "b", "--", "c", "d"])
                    self.assertTrue(self.marker(), "the mutant was not caught")
        self.assertEqual(seen, 6)

    def test_a_shipped_script_puts_its_own_folder_first_not_the_cwd(self):
        # `python3 "$VC_ROOT/scripts/x.py"` is not affected: the planted
        # json.py in the working directory is not imported.
        script = os.path.join(PLUGIN_ROOT, "scripts", "statepath.py")
        proc = subprocess.run(
            [BASH, "-c", "python3 %s" % _sh_quote(script)],
            input=json.dumps({"mode": "all", "repo": "r", "branch": "b",
                              "narrow": ""}),
            cwd=self.tmp, env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
            capture_output=True, text=True, timeout=30)
        self.assertFalse(self.marker(), "planted json.py ran")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("by-mode/all/", json.loads(proc.stdout)["current_path"])


if __name__ == "__main__":
    unittest.main()
