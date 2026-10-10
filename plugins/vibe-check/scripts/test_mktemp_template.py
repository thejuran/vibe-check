"""Every mktemp in the plugin's shell fences names an explicit $TMPDIR template.

macOS mktemp called without a template ignores $TMPDIR and creates its file in
the per-user /var/folders/.../T directory. Under Claude Code's sandbox only
$TMPDIR is writable, so a bare `mktemp` / `mktemp -d` fails with "Operation not
permitted" and the fence breaks. Every call must therefore pass a template
rooted at "${TMPDIR:-/tmp}".
"""
import os
import re
import unittest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCANNED_DIRS = ("phases", "commands", "agents", "templates", "hooks", "docs")
TEMPLATE_PREFIX = '"${TMPDIR:-/tmp}/'
MKTEMP_CALL = re.compile(r"\$\(\s*mktemp\b([^)]*)\)")


def mktemp_problems(text):
    """Return each `$(mktemp …)` call whose arguments do not start with an
    explicit template rooted at ${TMPDIR:-/tmp} (an optional -d first)."""
    bad = []
    for m in MKTEMP_CALL.finditer(text):
        args = m.group(1).strip()
        if args.startswith("-d"):
            args = args[2:].strip()
        if not (args.startswith(TEMPLATE_PREFIX) and "XXXXXX" in args):
            bad.append(m.group(0))
    return bad


def plugin_text_files():
    for sub in SCANNED_DIRS:
        base = os.path.join(PLUGIN_ROOT, sub)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in filenames:
                if name.endswith((".md", ".sh", ".txt")):
                    yield os.path.join(dirpath, name)


class TestMktempTemplate(unittest.TestCase):
    def test_every_plugin_mktemp_has_tmpdir_template(self):
        seen = 0
        for path in plugin_text_files():
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            seen += len(MKTEMP_CALL.findall(text))
            with self.subTest(file=os.path.relpath(path, PLUGIN_ROOT)):
                self.assertEqual(mktemp_problems(text), [])
        # the fences that need temp files exist (guards a scan that finds nothing)
        self.assertGreaterEqual(seen, 10)

    def test_bare_mktemp_is_flagged(self):
        self.assertEqual(mktemp_problems("ROWSFILE=$(mktemp)"), ["$(mktemp)"])
        self.assertEqual(mktemp_problems("D=$(mktemp -d)"), ["$(mktemp -d)"])

    def test_template_outside_tmpdir_is_flagged(self):
        self.assertEqual(len(mktemp_problems('F=$(mktemp "/var/tmp/x.XXXXXX")')), 1)
        self.assertEqual(len(mktemp_problems('F=$(mktemp -t vc)')), 1)

    def test_tmpdir_templates_pass(self):
        self.assertEqual(mktemp_problems('F=$(mktemp "${TMPDIR:-/tmp}/vc.XXXXXX")'), [])
        self.assertEqual(
            mktemp_problems('D=$(mktemp -d "${TMPDIR:-/tmp}/vc-codex.XXXXXX")'), [])


if __name__ == "__main__":
    unittest.main()
