"""test_carry_writers.py — one writer per carry-forward state field family.

The review state file is written by several orchestrator phases (prose the
model follows) and by two scripts. Each field family has exactly ONE writer:

  | family                 | sole writer                                      |
  |------------------------|--------------------------------------------------|
  | passes (pass entries)  | phases/review/45-persist.md (+ 45-persist-all.md |
  |                        | adds keys to the SAME entry)                     |
  | scored finding fields  | scripts/score.py (TestSingleWriterLock,          |
  |                        | test_score.py — composed with, not duplicated)   |
  | snapshot / resolved /  | scripts/score.py; prose may only copy them       |
  | kept_open / obligation | unchanged                                        |
  | decisions              | phases/shared/90-finalize.md, through            |
  |                        | carry_state.py record-decisions                  |
  | fix_verdicts           | phases/review/50-fix-loop.md, through            |
  |                        | carry_state.py record-fix-verdicts               |
  | medium_acknowledgments | nobody (legacy, read-only; a fresh root creates  |
  |                        | it empty, which is not an entry write)           |
  | state archive (mv)     | phases/shared/90-finalize.md                     |

Two locks enforce the table:

* a prose detector over every orchestrator file (commands/*.md and
  phases/**/*.md): a family's WRITE form may appear only in its owner file;
* AST locks over carry_state.py (one function per family it writes) and
  score.py (the only producer of snapshot / kept_open / obligation / resolved).

Every lock is mutation-tested in memory: an injected second writer must trip
it, and a negated injection must not.
"""

import ast
import glob
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.normpath(os.path.join(HERE, ".."))
COMMANDS_DIR = os.path.join(PLUGIN_DIR, "commands")
PHASES_DIR = os.path.join(PLUGIN_DIR, "phases")
SCORE_PY = os.path.join(HERE, "score.py")
CARRY_STATE_PY = os.path.join(HERE, "carry_state.py")


# --------------------------------------------------------------------------- #
# Prose detector.
# --------------------------------------------------------------------------- #
# Negated / forbidding clauses are exempt: the corpus legitimately says who
# must NOT write a family. Same vocabulary as test_score.py's _NEG_RE.
_NEG_RE = re.compile(
    r"\b(?:do not|do n't|don't|does not|doesn't|did not|didn't|"
    r"never|no longer|not\b|cannot|can't|must not|mustn't|"
    r"forbid|forbidden|forbids|without|no by-hand|"
    r"would create|would be|reintroduc)\b",
    re.I,
)

_VERBS = (r"set|write|record|append|assign|create|add|update|migrate|rewrite|"
          r"reset")


def _writer_clauses(text):
    """Split text into small clauses so negation scoping is LOCAL.

    Breaks on newlines, semicolons, `!`/`?` + space, and a period that ends a
    sentence (followed by whitespace or the end). A period inside a token
    (`carry_state.py`, `state.passes`, `$STATE_FILE.tmp`) is NOT a break, so a
    helper invocation or a dotted field path stays in one clause.
    """
    raw = re.split(r"\n|;|\.(?=\s|$)|(?<=[!?])\s", text)
    return [c.strip() for c in raw if c.strip()]


def _subscript_write(name):
    # name[...] = value (not ==)
    return r"\b" + name + r"\s*\[[^\]\n]*\]\s*=(?!=)"


def _directive(name):
    # <write verb> [the|a|an|to|into|its ...] [`][root |state.][`]name
    return (r"\b(?:" + _VERBS + r")\b\s+(?:(?:the|a|an|to|into|its)\s+)*"
            r"`?(?:root\s+|state\.)?`?" + name + r"\b")


def _helper(subcommand):
    # carry_state.py record-<family> (bare or quoted path, any prefix)
    return r"carry_state\.py\"?\s+" + subcommand + r"\b"


# Exemption. Frozen against the real corpus — loosening it to make the corpus
# pass would hide a real second writer; fix the prose instead. The only clause
# shape the real corpus needs exempted is one that NAMES a family's owner
# ("written only by Finalize via carry_state.py record-decisions",
# "Finalize-written via ..."). Copy-through, read and create-empty clauses
# are not matched by any write form, so they need no exemption (and get none:
# an exemption that never fires only weakens the lock).
_OWNER_ATTRIBUTION_RE = re.compile(
    r"\bwritten\s+only\s+by\b|-written\s+via\b", re.I)


def _family(name, owners, subscript=None, directive=None, assign=None,
            helper=None, extra=None):
    """One field family: its owner files and its write forms.

    Each form is (compiled regex, exemptions that apply to it). Machine forms
    (subscript write, `name =`, `mv`, the append-to-passes form) are exempt
    only by negation; a prose directive or a helper invocation is also exempt
    when the clause names the family's owner.
    """
    forms = []
    if subscript:
        forms.append((re.compile(_subscript_write(subscript)), ()))
    if assign:
        forms.append((re.compile(r"\b" + assign + r"`?\s*=(?!=)"), ()))
    if directive:
        forms.append((re.compile(_directive(directive), re.I),
                      (_OWNER_ATTRIBUTION_RE,)))
    if helper:
        forms.append((re.compile(_helper(helper)), (_OWNER_ATTRIBUTION_RE,)))
    for pattern, exempt in extra or ():
        forms.append((re.compile(pattern, re.I), exempt))
    return {"name": name, "owners": tuple(owners), "forms": tuple(forms)}


FAMILIES = (
    _family("passes",
            ("phases/review/45-persist.md", "phases/review/45-persist-all.md"),
            subscript="passes", directive="passes",
            # "append the pass entry to its `passes` array"
            extra=((r"\bappend\b[^\n]*?\b(?:state\.)?passes\b", ()),)),
    _family("decisions", ("phases/shared/90-finalize.md",),
            subscript="decisions", directive="decisions",
            helper="record-decisions"),
    _family("fix_verdicts", ("phases/review/50-fix-loop.md",),
            subscript="fix_verdicts", directive="fix_verdicts",
            helper="record-fix-verdicts"),
    _family("medium_acknowledgments", (),
            subscript="medium_acknowledgments",
            directive="medium_acknowledgments"),
    _family("snapshot", (), subscript="snapshot", assign="snapshot",
            directive="snapshot"),
    _family("resolved", (), subscript="resolved", assign="resolved",
            directive="`resolved`"),
    _family("kept_open", (), subscript="kept_open", assign="kept_open",
            directive="kept_open"),
    _family("obligation", (), subscript="obligation", assign="obligation",
            directive="obligation"),
    _family("archive", ("phases/shared/90-finalize.md",),
            extra=((r"\bmv\s+\"?\$(?:ALL_)?STATE_FILE\"?\s", ()),)),
)
FAMILY_BY_NAME = {f["name"]: f for f in FAMILIES}


def family_write_clauses(text, family):
    """The clauses of `text` that WRITE `family` (negated clauses exempt)."""
    hits = []
    for clause in _writer_clauses(text):
        if _NEG_RE.search(clause):
            continue
        for pattern, exempt in family["forms"]:
            if pattern.search(clause) and not any(e.search(clause)
                                                  for e in exempt):
                hits.append(clause)
                break
    return hits


def corpus():
    """commands/*.md UNION phases/**/*.md — every orchestrator prose file."""
    return sorted(glob.glob(os.path.join(COMMANDS_DIR, "*.md"))) + sorted(
        glob.glob(os.path.join(PHASES_DIR, "**", "*.md"), recursive=True))


def rel(path):
    return os.path.relpath(path, PLUGIN_DIR)


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def offenders(family, texts):
    """{relpath: hits} for every non-owner file that writes `family`."""
    out = {}
    for path, text in texts.items():
        if path in family["owners"]:
            continue
        hits = family_write_clauses(text, family)
        if hits:
            out[path] = hits
    return out


class TestProseWriterLock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = {rel(p): read(p) for p in corpus()}

    def test_corpus_is_real(self):
        self.assertGreaterEqual(len(self.texts), 10, sorted(self.texts))
        for path, text in self.texts.items():
            self.assertGreater(len(text), 200, path)
        self.assertIn("commands/review.md", self.texts)
        self.assertIn("commands/deep-review.md", self.texts)
        for family in FAMILIES:
            for owner in family["owners"]:
                with self.subTest(family=family["name"], owner=owner):
                    self.assertIn(owner, self.texts)
        # The corpus does mention every family (the zero-hit results below are
        # not a vacuous scan of text that never names them).
        joined = "\n".join(self.texts.values())
        for name in ("passes", "decisions", "fix_verdicts",
                     "medium_acknowledgments", "snapshot", "resolved",
                     "kept_open", "obligation", '"$STATE_FILE"'):
            self.assertIn(name, joined)

    def test_each_family_written_only_by_its_owner(self):
        for family in FAMILIES:
            for path, text in sorted(self.texts.items()):
                with self.subTest(family=family["name"], path=path):
                    if path in family["owners"]:
                        continue
                    self.assertEqual(
                        family_write_clauses(text, family), [],
                        "%s writes %s, which only %s may write"
                        % (path, family["name"],
                           ", ".join(family["owners"]) or "score.py / nobody"))

    def test_owner_is_actually_detected(self):
        # Non-vacuity: each prose owner's real write is seen by the detector.
        for name in ("passes", "decisions", "fix_verdicts", "archive"):
            family = FAMILY_BY_NAME[name]
            for owner in family["owners"]:
                if name == "passes" and owner.endswith("45-persist-all.md"):
                    continue  # adds keys to the entry 45-persist.md appends
                with self.subTest(family=name, owner=owner):
                    self.assertGreaterEqual(
                        len(family_write_clauses(self.texts[owner], family)), 1)
        # score.py-produced families: no prose writer at all, and the scorer
        # really produces them.
        source = read(SCORE_PY)
        for name in ("snapshot", "resolved", "kept_open", "obligation",
                     "medium_acknowledgments"):
            family = FAMILY_BY_NAME[name]
            with self.subTest(family=name):
                self.assertEqual(family["owners"], ())
                self.assertEqual(offenders(family, self.texts), {})
        self.assertRegex(source, r'\w+\["snapshot"\]\s*=')
        self.assertRegex(source, r'out\["resolved"\]\s*=\s*resolved')
        self.assertRegex(source, r'\bresolved\.append\(')

    # One injected second writer per family, in a non-owner file. Each must be
    # reported, for exactly that file.
    INJECTIONS = (
        ("passes", "Append the pass entry to state.passes here as well."),
        ("passes", 'Then set state.passes[0] = {"pass_number": 1}.'),
        ("decisions", 'Then write decisions[stable_hash] = {"decision": "dismiss"}.'),
        ("decisions",
         'Run python3 "$VC_ROOT/scripts/carry_state.py" record-decisions here.'),
        ("fix_verdicts", 'Record fix_verdicts[stable_hash] = {"verdict": "obsolete"}.'),
        ("fix_verdicts",
         'Run python3 "$VC_ROOT/scripts/carry_state.py" record-fix-verdicts here.'),
        ("medium_acknowledgments",
         'Then write medium_acknowledgments[stable_hash] = {"decision": "dismiss"}.'),
        ("medium_acknowledgments", "Record the medium_acknowledgments entry."),
        ("snapshot", 'Set snapshot = {"at_pass": 1} on each row.'),
        ("resolved", "Then append each resolution: `resolved` = [] first."),
        ("kept_open", 'Set kept_open = "sub-threshold" on the row.'),
        ("obligation", 'Set obligation = {"stable_hash": "x"} on the member.'),
        ("archive", 'mv "$STATE_FILE" elsewhere.'),
    )
    TARGET = "phases/review/40-render.md"

    def test_mutation_second_writer_is_caught(self):
        self.assertTrue(set(name for name, _ in self.INJECTIONS)
                        >= set(FAMILY_BY_NAME))
        base = self.texts[self.TARGET]
        for name in FAMILY_BY_NAME:
            self.assertNotIn(self.TARGET, FAMILY_BY_NAME[name]["owners"])
        for name, clause in self.INJECTIONS:
            with self.subTest(family=name, injection=clause):
                family = FAMILY_BY_NAME[name]
                texts = dict(self.texts)
                texts[self.TARGET] = base + "\n" + clause + "\n"
                self.assertEqual(list(offenders(family, texts)), [self.TARGET])

    def test_negated_injection_is_not_reported(self):
        base = self.texts[self.TARGET]
        for name, clause in (
                ("decisions",
                 'Do not write decisions[stable_hash] = {"decision": "dismiss"}.'),
                ("passes", "Never append the pass entry to state.passes here."),
                ("medium_acknowledgments",
                 "Nothing may write medium_acknowledgments[h] = 1, never."),
                ("archive", 'Do not mv "$STATE_FILE" here.')):
            with self.subTest(family=name):
                family = FAMILY_BY_NAME[name]
                texts = dict(self.texts)
                texts[self.TARGET] = base + "\n" + clause + "\n"
                self.assertEqual(offenders(family, texts), {})

    # The exact set of real-corpus clauses the owner-attribution exemption
    # covers: (family, file, clause prefix). A new exempted clause anywhere
    # fails here, so the exemption cannot quietly grow.
    FROZEN_EXEMPTED = {
        ("decisions", "phases/review/05-state.md",
         "- The state root may also carry `decisions` (Finalize-written via"),
        ("decisions", "phases/review/45-persist.md",
         "The root may LATER gain `decisions` (written only by Finalize via"),
        ("fix_verdicts", "phases/review/45-persist.md",
         "The root may LATER gain `decisions` (written only by Finalize via"),
    }

    def test_exemptions_are_frozen(self):
        exempted = set()
        for family in FAMILIES:
            bare = dict(family, forms=tuple((p, ()) for p, _ in family["forms"]))
            for path, text in self.texts.items():
                if path in family["owners"]:
                    continue
                strict = set(family_write_clauses(text, family))
                for clause in family_write_clauses(text, bare):
                    if clause in strict:
                        continue
                    known = [p for f, q, p in self.FROZEN_EXEMPTED
                             if (f, q) == (family["name"], path)
                             and clause.startswith(p)]
                    exempted.add((family["name"], path,
                                  known[0] if known else clause))
        self.assertEqual(exempted, self.FROZEN_EXEMPTED)

    def test_owner_file_injection_is_not_a_second_writer(self):
        # The lock is about WHO writes: the owner file may grow another write.
        family = FAMILY_BY_NAME["decisions"]
        owner = family["owners"][0]
        texts = dict(self.texts)
        texts[owner] += '\nThen write decisions[h] = {"decision": "defer"}.\n'
        self.assertEqual(offenders(family, texts), {})

    def test_existing_scored_field_lock_untouched(self):
        # The scored-field lock lives in test_score.py; the two compose.
        import test_score
        self.assertTrue(callable(test_score.has_scored_field_write_path))
        self.assertTrue(hasattr(test_score, "TestSingleWriterLock"))
        for path, text in self.texts.items():
            with self.subTest(path=path):
                self.assertFalse(test_score.has_scored_field_write_path(text))


# --------------------------------------------------------------------------- #
# AST locks.
# --------------------------------------------------------------------------- #
def subscript_writes(source, include_setdefault=False):
    """[(innermost enclosing function or '<module>', key)] for every
    `x["key"] = ...` / `x["key"] += ...` target (any depth of the chain), plus
    `.setdefault("key", ...)` calls when asked. Other calls are not writes."""
    tree = ast.parse(source)
    found = []

    def keys_of(node):
        out = []
        while isinstance(node, (ast.Subscript, ast.Attribute)):
            if (isinstance(node, ast.Subscript)
                    and isinstance(node.slice, ast.Constant)
                    and isinstance(node.slice.value, str)):
                out.append(node.slice.value)
            node = node.value
        return out

    def visit(node, fn):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn = node.name
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        for t in targets:
            if isinstance(t, ast.Subscript):
                for k in keys_of(t):
                    found.append((fn, k))
        if (include_setdefault and isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "setdefault" and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            found.append((fn, node.args[0].value))
        for child in ast.iter_child_nodes(node):
            visit(child, fn)

    visit(tree, "<module>")
    return found


def functions_writing(source, key, include_setdefault=False):
    return sorted({fn for fn, k in subscript_writes(source, include_setdefault)
                   if k == key})


def inject_into(source, func_name, line):
    """`source` with `line` inserted as the first statement of `func_name`
    (whose `def` must fit on one line)."""
    anchor = "def %s(" % func_name
    assert source.count(anchor) == 1, func_name
    head, tail = source.split(anchor, 1)
    sig, body = tail.split("\n", 1)
    assert sig.rstrip().endswith(":"), func_name
    return head + anchor + sig + "\n    " + line + "\n" + body


CARRY_OWNERS = {"decisions": ["record_decisions"],
                "fix_verdicts": ["record_fix_verdicts"],
                "passes": [], "medium_acknowledgments": []}


def carry_state_violations(source):
    bad = []
    for key, owners in CARRY_OWNERS.items():
        got = functions_writing(source, key, include_setdefault=True)
        if got != owners:
            bad.append((key, got))
    for key in ("snapshot", "resolved", "kept_open", "obligation"):
        got = functions_writing(source, key, include_setdefault=True)
        if got:
            bad.append((key, got))
    return bad


class TestCarryStateAstLock(unittest.TestCase):
    def setUp(self):
        self.source = read(CARRY_STATE_PY)

    def test_helper_ast_single_function_per_family(self):
        self.assertEqual(carry_state_violations(self.source), [])
        # Non-vacuity: both owners really write their family.
        self.assertEqual(functions_writing(self.source, "decisions"),
                         ["record_decisions"])
        self.assertEqual(functions_writing(self.source, "fix_verdicts"),
                         ["record_fix_verdicts"])

    def test_helper_ast_lock_trips_under_mutation(self):
        for func, line in (
                ("pending", 'state["passes"] = []'),
                ("finalize_counts", 'state["medium_acknowledgments"]["h"] = 1'),
                ("record_fix_verdicts", 'state["decisions"] = {}'),
                ("record_decisions", 'state.setdefault("fix_verdicts", {})'),
                ("record_decisions", 'state["snapshot"] = {}'),
                ("open_findings", 'state["passes"][0]["findings"] += []')):
            with self.subTest(func=func, line=line):
                mutated = inject_into(self.source, func, line)
                self.assertNotEqual(carry_state_violations(mutated), [])


# score.py: allowlist bound + per-function non-vacuity bound for each key.
SCORE_PRODUCERS = {
    "snapshot": ("run", "_kept_open_rows"),
    "kept_open": ("_kept_open_rows",),
    "obligation": ("run", "_expand_members", "_kept_open_rows"),
    "resolved": ("run",),
}


def score_allowlist_violations(source):
    """[(key, function)] for a producer-key assignment outside its allowlist."""
    bad = []
    for key, allowed in SCORE_PRODUCERS.items():
        for fn in functions_writing(source, key):
            if fn not in allowed:
                bad.append((key, fn))
    return bad


def score_missing_producers(source):
    """[(key, function)] for an allowlisted function that no longer assigns."""
    missing = []
    for key, allowed in SCORE_PRODUCERS.items():
        have = functions_writing(source, key)
        for fn in allowed:
            if fn not in have:
                missing.append((key, fn))
    return missing


class TestScoreSoleProducer(unittest.TestCase):
    def setUp(self):
        self.source = read(SCORE_PY)

    def test_score_is_sole_producer_of_snapshot_and_resolved(self):
        self.assertEqual(score_allowlist_violations(self.source), [])
        self.assertEqual(score_missing_producers(self.source), [])
        # _snapshot_for only RETURNS a snapshot dict; it is on neither list.
        tree = ast.parse(self.source)
        names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        self.assertIn("_snapshot_for", names)
        self.assertNotIn("_snapshot_for", functions_writing(self.source, "snapshot"))
        for allowed in SCORE_PRODUCERS.values():
            self.assertNotIn("_snapshot_for", allowed)
        # `rep.pop("kept_open", None)` is a call, not an assignment.
        self.assertIn('pop("kept_open", None)', self.source)
        # carry_state.py never assigns any of these keys.
        carry = read(CARRY_STATE_PY)
        for key in SCORE_PRODUCERS:
            with self.subTest(key=key):
                self.assertEqual(functions_writing(carry, key, True), [])

    def test_allowlist_bound_trips_outside_the_allowlist(self):
        for func, line in (("band_for", 'x = {}; x["snapshot"] = {}'),
                           ("_snapshot_for", 'row["snapshot"] = {}'),
                           ("_member_ref", 'm["obligation"] = None'),
                           ("carry_forward_status", 'finding["kept_open"] = "x"')):
            with self.subTest(func=func):
                mutated = inject_into(self.source, func, line)
                self.assertIn(func, [fn for _, fn in
                                     score_allowlist_violations(mutated)])

    def test_non_vacuity_bound_trips_on_keyword_form(self):
        # A `dict(rec, obligation=...)` keyword form is invisible to the
        # allowlist bound; the per-function non-vacuity bound catches it.
        old = 'rec["obligation"] = raw["obligation"]'
        self.assertEqual(self.source.count(old), 1)
        mutated = self.source.replace(
            old, 'rec = dict(rec, obligation=raw["obligation"])')
        self.assertEqual(score_allowlist_violations(mutated), [])
        self.assertEqual(score_missing_producers(mutated),
                         [("obligation", "_expand_members")])


if __name__ == "__main__":
    unittest.main()
