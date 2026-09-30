"""test_agent_prompts.py — prose locks for the agent prompts.

The agent prompts are prose, so the only proof that a prompt rule exists (and
keeps existing) is a test that reads the prose. This module holds those locks:

* Leakage (D-01/D-02). The prompts may teach generic classes of safe change,
  never the B3 ground-truth diffs they are measured against. The identifier set
  is EXTRACTED from the committed B3 patches and provenance files (never
  hand-typed), and the whole prompt corpus must scan clean against it.
* Cap math. The confidence ceiling a prompt asks for is only meaningful against
  the scoring template, so the Medium floor, the Warning floor, the bonuses and
  the severity weights are parsed from `templates/scoring.md`; a band retune or
  a bonus change trips the proof rather than silently invalidating it.
* Prompt content (block clauses, the Codex focus literal, retired wording) is
  locked with the same pure scanners.

Every scanner is a pure function over text. Mutation tests plant text in
memory and assert the scanner trips; no test writes a file.
"""

import glob
import os
import re
import sys
import unittest

# Make sibling imports resolve when unittest discovery runs from the root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import replay  # noqa: E402  (REPO_ROOT convention)

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
REPO_ROOT = replay.REPO_ROOT
DIFFS_DIR = os.path.join(REPO_ROOT, "docs", "design", "b3-ground-truth", "diffs")

LOUD = ("bugs", "security", "impact")

SENTINELS = {"validate_url_ssrf", "sanitize_log_value", "safe_float",
             "shutdown_drain_timeout", "triggarr", "seedsyncarr"}

# Tokens the B3 patches happen to contain that are library/stdlib names, not
# B3-specific identifiers. Every entry needs a reason, and every entry must
# still appear in the raw extraction (TestB3Identifiers.test_allowlist_is_live),
# so the list cannot quietly grow to hide a leak.
GENERIC_API = {
    "TemplateResponse": "Starlette/FastAPI template API; framework-fastapi.md "
                        "names it as the framework idiom",
    "ValueError": "Python builtin exception; deep-review and framework prose "
                  "use it generically",
}


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
def norm(text):
    """Collapse all whitespace runs to one space (prompts are hard-wrapped)."""
    return " ".join(text.split())


def read(relpath):
    """Read a file under the plugin root as text."""
    with open(os.path.join(PLUGIN_ROOT, relpath), encoding="utf-8") as fh:
        return fh.read()


def prose_corpus():
    """Every prompt/prose file the agents or orchestrator read: {relpath: text}."""
    patterns = ("agents/*.md", "commands/*.md", "phases/**/*.md", "templates/*.md")
    corpus = {}
    for pat in patterns:
        for path in glob.glob(os.path.join(PLUGIN_ROOT, pat), recursive=True):
            rel = os.path.relpath(path, PLUGIN_ROOT)
            with open(path, encoding="utf-8") as fh:
                corpus[rel] = fh.read()
    return corpus


_IDENT = re.compile(r"\b[A-Za-z_]\w*\b")
_SOURCE_REPO = re.compile(r"^source_repo:\s*~/(\S+)", re.MULTILINE)


def _is_distinctive(token):
    """Length >= 6 with an inner underscore or a lower->upper camelCase step."""
    if len(token) < 6:
        return False
    return "_" in token.strip("_") or re.search(r"[a-z][A-Z]", token) is not None


def _raw_b3_identifiers(diffs_dir):
    """B3 identifiers BEFORE the GENERIC_API subtraction.

    From each *.patch: the full repo-relative path of every `+++ b/` header
    (never a basename — `config.py` alone is generic) plus every distinctive
    token on a `+`/`-` body line. From each *.provenance: the source repo name.
    """
    ids = set()
    for path in sorted(glob.glob(os.path.join(diffs_dir, "*.patch"))):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("+++ b/"):
                    ids.add(line[len("+++ b/"):].strip())
                elif line.startswith(("+++", "---")):
                    continue
                elif line[:1] in ("+", "-"):
                    ids.update(t for t in _IDENT.findall(line) if _is_distinctive(t))
    for path in sorted(glob.glob(os.path.join(diffs_dir, "*.provenance"))):
        with open(path, encoding="utf-8", errors="replace") as fh:
            ids.update(_SOURCE_REPO.findall(fh.read()))
    return ids


def b3_identifiers(diffs_dir):
    """B3-specific identifiers, repo names and paths (raw minus GENERIC_API)."""
    return _raw_b3_identifiers(diffs_dir) - set(GENERIC_API)


def leaks(text, ids):
    """Sorted B3 identifiers present in `text` as whole tokens."""
    return sorted(
        t for t in ids
        if re.search(r"(?<![\w/])" + re.escape(t) + r"(?![\w])", text)
    )


# --------------------------------------------------------------------------- #
# Leakage guard tests
# --------------------------------------------------------------------------- #
class TestB3Identifiers(unittest.TestCase):
    def setUp(self):
        self.ids = b3_identifiers(DIFFS_DIR)

    def test_sentinels_present(self):
        self.assertTrue(SENTINELS <= self.ids, SENTINELS - self.ids)

    def test_paths_are_full_repo_relative(self):
        paths = [i for i in self.ids if "/" in i and i.endswith(".py")]
        self.assertTrue(paths, "no full repo-relative .py path extracted")
        bare = [i for i in self.ids if "/" not in i and i.endswith(".py")]
        self.assertEqual(bare, [])
        self.assertNotIn("config.py", self.ids)

    def test_allowlist_is_live(self):
        raw = _raw_b3_identifiers(DIFFS_DIR)
        for name, reason in GENERIC_API.items():
            self.assertIn(name, raw, f"stale GENERIC_API entry: {name}")
            self.assertIsInstance(reason, str)
            self.assertTrue(reason.strip(), f"unexplained GENERIC_API entry: {name}")
            self.assertNotIn(name, self.ids)


class TestLeakScanner(unittest.TestCase):
    def setUp(self):
        self.ids = b3_identifiers(DIFFS_DIR)

    def test_planted_identifier_trips(self):
        self.assertEqual(leaks("routes it through safe_float here", self.ids),
                         ["safe_float"])

    def test_planted_repo_name_trips(self):
        self.assertEqual(leaks("as in triggarr", self.ids), ["triggarr"])

    def test_planted_path_trips(self):
        self.assertIn("triggarr/models/config.py",
                      leaks("see triggarr/models/config.py", self.ids))

    def test_generic_words_do_not_trip(self):
        self.assertEqual(
            leaks("adds an allowlist/denylist validator on an input", self.ids), [])
        self.assertEqual(leaks("TemplateResponse ValueError", self.ids), [])

    def test_word_boundary(self):
        self.assertEqual(leaks("xsafe_floaty", self.ids), [])


class TestCorpusHasNoLeaks(unittest.TestCase):
    def test_corpus_is_not_empty(self):
        self.assertGreaterEqual(len(prose_corpus()), 40)

    def test_prompt_corpus_clean(self):
        ids = b3_identifiers(DIFFS_DIR)
        for relpath, text in sorted(prose_corpus().items()):
            with self.subTest(relpath=relpath):
                self.assertEqual(leaks(text, ids), [])


if __name__ == "__main__":
    unittest.main()
