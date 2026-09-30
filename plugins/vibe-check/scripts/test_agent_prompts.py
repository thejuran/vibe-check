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


def section(text, heading):
    """Slice from `## <heading>` to the next `## ` heading (or EOF); None if absent."""
    m = re.search(r"(?m)^## " + re.escape(heading) + r"[ \t]*$", text)
    if m is None:
        return None
    end = text.find("\n## ", m.end())
    return text[m.start():] if end == -1 else text[m.start():end]


# Phrases the retired Claude<->Claude cross-confirm model used. The last entry
# is a STEM: plain case-insensitive substring matching catches both
# "independently confirmed" and "independently confirms", while the replacement
# wording "Codex independently flags ..." never matches. Keep it last so the
# ordered expectations stay stable.
FORBIDDEN_PHRASES = (
    "CATEGORY_DOMAIN",
    "category-domain",
    "shares its domain",
    "actually cross-confirm today",
    "same-domain",
    "domain overlap",
    "independently confirm",
)


def forbidden_hits(text, phrases=FORBIDDEN_PHRASES):
    """Phrases present in `text` (case-insensitive, whitespace-normalized), in phrase order."""
    hay = norm(text).lower()
    return [p for p in phrases if norm(p).lower() in hay]


def missing_clauses(section_text, clauses):
    """Clauses absent from `section_text` after whitespace normalization (case-sensitive)."""
    hay = norm(section_text or "")
    return [c for c in clauses if norm(c) not in hay]


def focus_literal(kickoff_text):
    """Contents of the first CODEX_FOCUS='...' single-quoted literal, or None."""
    m = re.search(r"CODEX_FOCUS='([^']*)'", kickoff_text, re.DOTALL)
    return None if m is None else m.group(1)


_CAP = re.compile(
    r"agent_confidence\s*(?:≤|<=)\s*(\d+)|confidence at or below 0\.(\d\d)")


def caps_in(text):
    """Every confidence ceiling stated in `text`, as integer percent, in document order."""
    return [int(m.group(1) or m.group(2)) for m in _CAP.finditer(norm(text))]


def _int(token):
    return int(token.replace("−", "-"))


def scoring_constants(text):
    """Parse the band floors, bonuses, severity weights and offsets from scoring.md.

    Raises ValueError naming the first piece that cannot be parsed, so a
    reshaped template trips the cap proof instead of silently passing it.
    """
    def one(name, pattern):
        m = re.search(pattern, text, re.MULTILINE)
        if m is None:
            raise ValueError(f"scoring.md: cannot parse {name}")
        return _int(m.group(1))

    consts = {
        "medium_floor": one("medium_floor", r"\|\s*Medium\s*\|\s*(\d+)\s*[–-]\s*\d+"),
        "warning_floor": one("warning_floor", r"\|\s*Warning\s*\|\s*(\d+)"),
        "in_diff_bonus": one("in_diff_bonus", r"\+\s*(\d+)\s+if in_diff"),
        "corroborated_bonus": one("corroborated_bonus", r"\+\s*(\d+)\s+if corroborated"),
        "persisted_bonus": one("persisted_bonus", r"\+\s*(\d+)\s+if persisted"),
    }

    weights = {sev: _int(w) for sev, w in re.findall(
        r'severity == "(critical|high|medium|low)"\s*→\s*([+−-]?\d+)', text)}
    for sev in ("critical", "high", "medium", "low"):
        if sev not in weights:
            raise ValueError(f"scoring.md: cannot parse severity_weights[{sev}]")
    consts["severity_weights"] = weights

    m = re.search(r"^\s*-\s*Current offsets:\s*\n((?:[ \t]+-\s*\w+:\s*-?\d+[ \t]*\n?)+)",
                  text, re.MULTILINE)
    if m is None:
        raise ValueError("scoring.md: cannot parse offsets")
    consts["offsets"] = {name: int(v) for name, v in
                         re.findall(r"^\s*-\s*(\w+):\s*(-?\d+)", m.group(1), re.MULTILINE)}
    return consts


def lone_lane_max(cap, offset=0, in_diff_bonus=20, severity_weight=0):
    """Highest score a lone-lane finding at `cap` can reach (no second opinion)."""
    return cap + offset + in_diff_bonus + severity_weight


def cap_is_nonblocking(cap, consts, offset=0):
    """A lone lane at `cap`, in the diff, at critical severity stays below Medium.

    Critical is the worst severity (weight 0), so this is the worst case FROM A
    LONE LANE only; `cap_never_warns` covers the carried-member path.
    """
    return lone_lane_max(cap, offset, consts["in_diff_bonus"], 0) < consts["medium_floor"]


def max_path_score(cap, consts, severity):
    """Worst reachable score: in the diff, Codex-corroborated AND persisted.

    A capped note carried as a member of a surviving row is re-scored next pass
    with the persisted bonus, plus the corroborated bonus if Codex joins again
    beside a Claude lane. No lone-lane offset: it is 0 on every second-opinion
    path.
    """
    return (cap + consts["in_diff_bonus"] + consts["corroborated_bonus"]
            + consts["persisted_bonus"] + consts["severity_weights"][severity])


def cap_never_warns(cap, consts, severity):
    """The worst reachable path at `cap` / `severity` stays below the Warning floor."""
    return max_path_score(cap, consts, severity) < consts["warning_floor"]


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


# --------------------------------------------------------------------------- #
# Scoring constants and cap math
# --------------------------------------------------------------------------- #
class TestScoringConstants(unittest.TestCase):
    def setUp(self):
        self.text = read("templates/scoring.md")

    def _without(self, needle):
        lines = [ln for ln in self.text.splitlines() if needle not in ln]
        self.assertLess(len(lines), len(self.text.splitlines()), needle)
        return "\n".join(lines)

    def test_parses_live_template(self):
        self.assertEqual(scoring_constants(self.text), {
            "medium_floor": 70,
            "warning_floor": 80,
            "in_diff_bonus": 20,
            "corroborated_bonus": 10,
            "persisted_bonus": 15,
            "severity_weights": {"critical": 0, "high": -3, "medium": -8, "low": -20},
            "offsets": {"architecture": -6, "bugs": -2, "impact": -12},
        })

    def test_missing_persisted_row_raises(self):
        with self.assertRaisesRegex(ValueError, "persisted_bonus"):
            scoring_constants(self._without("if persisted"))

    def test_missing_medium_row_raises(self):
        with self.assertRaises(ValueError):
            scoring_constants(self._without("| Medium |"))

    def test_offsets_never_positive(self):
        offsets = scoring_constants(self.text)["offsets"]
        self.assertTrue(offsets)
        self.assertTrue(all(v <= 0 for v in offsets.values()), offsets)


class TestCapMath(unittest.TestCase):
    def setUp(self):
        self.c = scoring_constants(read("templates/scoring.md"))

    def test_45_is_nonblocking_for_every_loud_lane(self):
        for offset in (0, self.c["offsets"]["bugs"], self.c["offsets"]["impact"]):
            with self.subTest(offset=offset):
                self.assertIs(cap_is_nonblocking(45, self.c, offset), True)
        self.assertEqual(lone_lane_max(45, 0, 20, 0), 65)

    def test_55_is_blocking(self):
        self.assertIs(cap_is_nonblocking(55, self.c), False)

    def test_49_is_the_arithmetic_maximum(self):
        self.assertIs(cap_is_nonblocking(49, self.c), True)
        self.assertIs(cap_is_nonblocking(50, self.c), False)

    def test_low_is_the_only_severity_that_never_warns(self):
        self.assertEqual(max_path_score(45, self.c, "low"), 70)
        self.assertIs(cap_never_warns(45, self.c, "low"), True)
        for sev, score in (("critical", 90), ("high", 87), ("medium", 82)):
            with self.subTest(severity=sev):
                self.assertEqual(max_path_score(45, self.c, sev), score)
                self.assertIs(cap_never_warns(45, self.c, sev), False)

    def test_all_paths_proof_can_fail(self):
        self.assertIs(cap_never_warns(54, self.c, "low"), True)
        self.assertIs(cap_never_warns(55, self.c, "low"), False)


# --------------------------------------------------------------------------- #
# Text scanners
# --------------------------------------------------------------------------- #
class TestSectionSlicer(unittest.TestCase):
    def test_slices_between_headings(self):
        text = "## A\nfoo\n## B\nbar"
        self.assertEqual(norm(section(text, "A")), "## A foo")
        self.assertEqual(norm(section(text, "B")), "## B bar")
        self.assertIsNone(section(text, "Missing"))


class TestCapsIn(unittest.TestCase):
    def test_reads_unicode_and_ascii_and_codex_units(self):
        text = ("agent_confidence ≤ 45 … agent_confidence <= 40 … "
                "confidence at or below 0.45")
        self.assertEqual(caps_in(text), [45, 40, 45])

    def test_planted_55_is_read(self):
        self.assertEqual(caps_in("keep agent_confidence ≤ 55 here"), [55])


class TestForbiddenScanner(unittest.TestCase):
    def test_planted_phrase_trips(self):
        self.assertEqual(forbidden_hits("shares its domain in CATEGORY_DOMAIN"),
                         ["CATEGORY_DOMAIN", "shares its domain"])
        self.assertEqual(forbidden_hits("grouped by site only"), [])

    def test_wrapped_phrase_trips(self):
        self.assertEqual(forbidden_hits("actually cross-confirm\ntoday"),
                         ["actually cross-confirm today"])

    def test_retired_confirm_stem_trips(self):
        self.assertEqual(FORBIDDEN_PHRASES[-1], "independently confirm")
        self.assertEqual(
            forbidden_hits("to a Filtered-summary count unless it is independently confirmed."),
            ["independently confirm"])
        self.assertEqual(
            forbidden_hits("unless another agent independently\nconfirms the site"),
            ["independently confirm"])
        self.assertEqual(
            forbidden_hits("unless Codex independently flags the same site while joined"), [])
        self.assertEqual(forbidden_hits("independent confirmation"), [])


class TestMissingClauses(unittest.TestCase):
    def test_reports_absent_clause(self):
        self.assertEqual(missing_clauses("## X\nalpha beta", ("alpha beta", "gamma")),
                         ["gamma"])
        self.assertEqual(missing_clauses("## X\nalpha\nbeta", ("alpha beta",)), [])


class TestFocusLiteral(unittest.TestCase):
    def test_extracts_single_quoted_literal(self):
        self.assertEqual(focus_literal("x\nCODEX_FOCUS='hello world'\nARGS=(...)"),
                         "hello world")
        self.assertEqual(focus_literal("CODEX_FOCUS='wrapped\nliteral'"),
                         "wrapped\nliteral")
        self.assertIsNone(focus_literal("no literal here"))


if __name__ == "__main__":
    unittest.main()
