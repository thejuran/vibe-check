"""Prose pins for the fix-loop card in phases/review/50-fix-loop.md.

The fix loop asks the owner ONE card per pass (Apply all & rerun / Apply
selected… / Skip & rerun / Stop here…); Apply selected… and Stop here… each
open exactly one more. Step B dispatches exactly what `batch_card.py payload`
prints, so the fix agent only ever receives the selected record's own defect.

Every assertion is on an exact literal. The no-nudge, dispatch and header
checks each carry a mutant subtest proving the check would trip.
"""

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import batch_card  # noqa: E402  (title filler words)
import batch_parse  # noqa: E402  (sibling module: the card labels)
import fixstage  # noqa: E402  (the one exit table: render_case_arms)
from test_git_safety_prose import OPTIONAL_EXPANSION  # noqa: E402
from test_scope_args import (  # noqa: E402  (the real Phase 0 fence)
    REENTRY, RERUN_POINTER, SCOPE, SHELLS, carrier_flag, finalize_mode,
    normalizer_block, scope_args, read as read_scope)

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.normpath(os.path.join(HERE, ".."))
FIX_LOOP = os.path.join(PLUGIN_DIR, "phases", "review", "50-fix-loop.md")
FIX_MD = os.path.join(PLUGIN_DIR, "agents", "fix.md")

# sha256 of agents/fix.md after the D-08 commit-title paragraph (titles are
# sanitized into the allowlist, never refused over punctuation). Any further
# edit must re-pin deliberately.
FIX_MD_SHA256 = (
    "fe0f145cac8bcc4d6f4997ab0c08d9245ed57220841592b51ca961b498907707")

CARD_HEADING = "### The fix-loop card"
STEP_B_HEADING = "### Step B"
TERMINATION_HEADING = "### Loop termination guarantees"

PAUSED_REVIEW = ("Paused. Resume with `/vibe-check:review ${original_args}` "
                 "or close out later with `--finalize`.")
PAUSED_DEEP = ("Paused. Resume with `/vibe-check:deep-review "
               "${original_args}` or close out later with `--finalize`.")

ROWS_CALL = 'batch_card.py" rows --mode fix-loop'
SELECT_QUESTIONS_CALL = 'batch_card.py" select-questions --rows'
PAYLOAD_CALL = 'batch_card.py" payload --rows "$ROWSFILE" --answer "$ANSWERFILE"'
SELECT_CALL = 'batch_card.py" select --rows'

FIX_SENT_BINDING = "Bind `$FIX_SENT` = `$PAYLOADFILE`'s `sent` array"
FINDINGS_VERBATIM = "`$PAYLOADFILE`'s `findings` array, inserted verbatim"
OLD_PLACEHOLDER = "JSON array of selected findings"

CARD_HEADER = 'header "Pass {{$PASS_NUMBER}}"'
STOP_HEADER = 'header "Stop here"'
MAX_HEADER_CHARS = 12

# fix.md's **8** bullet carries this rider; the Step B exit-8 render clause
# must carry the same sentence (D-01.3b).
EXIT8_RIDER = ('if a `hook-changed:` line follows, add "your commit hook changed '
               'what went into that commit"')
# Exit 9: publication uncertain. Never "nothing committed", never retried.
EXIT9_RENDER = ('9 → `errored` "interrupted while publishing; commit <sha> may '
                'or may not be on your branch — check `git log` for it before '
                'you retry anything" (sha from the `publication-uncertain:` '
                'line; never `applied`; this fix is not retried automatically)')

STEP_B_NEEDLES = ("PRE_BLOBS", "POST_BLOBS", "PRE_CLEAN", "POST_CLEAN",
                  "files_touched", "record-fix-verdicts", "^[A-Za-z0-9._/-]+$",
                  "applied-uncommitted", "unverified", "check.label",
                  EXIT8_RIDER, EXIT9_RENDER)

COMMIT_INVOCATION = 'fixstage.py" commit'
EXIT9_NO_RETRY = "do NOT retry this fix"
FIX_MD_NO_REATTEMPT = "Do NOT re-attempt this finding automatically"
FENCE_SHA = "0123456789abcdef0123456789abcdef01234567"
FENCE_ATTEMPT = "0123456789abcdef0123456789abcdef"

# --- Step B verified flow: dispatch, blobs rule (iii), fallback, render ---- #

DISPATCH_START = "You are the fix agent."
DISPATCH_END = "PASS_NUMBER = {{$PASS_NUMBER}}"
OLD_PATHSPEC = "`--` pathspec on BOTH `git add` and `git commit`"
FALLBACK_START = "**Inline fallback (narrow, fully specified).**"
RENDER_START = "**Render results**"
RENDER_END = "The pass entry still carries"
UNDO_CONDITION = "**Undo when the fix is not proven.**"
FIXSTAGE = 'fixstage.py" '
FIXCHECK = 'fixcheck.py" '
FALLBACK_ORDER = (FIXSTAGE + "begin", FIXSTAGE + "snapshot", FIXSTAGE + "seal",
                  FIXCHECK + "after", FIXSTAGE + "undo", FIXSTAGE + "commit")
FRESH_ATTEMPT = "never use an attempt id from an earlier pass"
D13_LINE = ("applied, not committed — mixed with your unfinished edits; "
            "build/test re-run won't see it")
HEAD_SENTENCE = ("applied-but-uncommitted fixes do not move HEAD, which is why "
                 "their line says build/test re-run won't see them")
CHECK_LABELS = ("verified by `<command>`", "syntax check only",
                "problem re-checked; no automated check available")
_ATTEMPT_CALL = re.compile(
    r'(fixstage\.py" (?:snapshot|seal|undo|commit)|fixcheck\.py" (?:baseline|after))')
_DIRECT_GIT = re.compile(r"^\s*git (add|commit|stash|checkout|reset|restore)\b",
                         re.M)


def _flat(text):
    return " ".join(text.split())


def dispatch_prompt(step_b):
    start = step_b.index(DISPATCH_START)
    return step_b[start:step_b.index(DISPATCH_END, start)]


def fallback_section(step_b):
    start = step_b.index(FALLBACK_START)
    return step_b[start:step_b.index(RENDER_START, start)]


def render_section(step_b):
    start = step_b.index(RENDER_START)
    return step_b[start:step_b.index(RENDER_END, start)]


def render_line(render, status):
    """The render bullet for `status`, or "" when it is missing."""
    for line in render.split("\n"):
        if line.startswith("- `%s` →" % status):
            return line
    return ""


def case_arms(text, invocation):
    """{label: arm text} of the `case` following `invocation` ({} if absent)."""
    if invocation not in text:
        return {}
    start = text.index(invocation)
    end = text.find("esac", start)
    window = text[start:end if end >= 0 else len(text)]
    return {m.group(1): m.group(2) for m in
            re.finditer(r"^\s+(\d|\*)\) (.*)$", window, re.M)}


def render_problems(step_b):
    render = render_section(step_b)
    problems = []
    if D13_LINE not in render_line(render, "applied-uncommitted"):
        problems.append("no applied-uncommitted render line with the D-13 text")
    if "the finding stays open" not in render_line(render, "unverified"):
        problems.append("no unverified render line keeping the finding open")
    if HEAD_SENTENCE not in step_b:
        problems.append("HEAD-movement sentence missing")
    if "copied into your reply as message text" not in render:
        problems.append("render is not copied as message text")
    return problems


def blobs_rule_problems(step_b):
    rule = next((l for l in step_b.split("\n") if "(iii)" in l), "")
    problems = ["rule (iii) does not name `%s`" % s
                for s in ("applied", "applied-uncommitted", "unverified")
                if "`%s`" % s not in rule]
    if 'status == "applied"' in rule:
        problems.append("rule (iii) is back to applied only")
    return problems


def fallback_git_problems(step_b):
    fb = fallback_section(step_b)
    problems = [] if FIXSTAGE + "commit" in fb else ["no fixstage commit"]
    problems += ["direct git: " + m.group(0).strip()
                 for m in _DIRECT_GIT.finditer(fb)]
    return problems


def fallback_lifecycle_problems(step_b):
    fb = fallback_section(step_b)
    if any(s not in fb for s in FALLBACK_ORDER):
        return ["a lifecycle step is missing"]
    problems = []
    idx = [fb.index(s) for s in FALLBACK_ORDER]
    if idx != sorted(idx):
        problems.append("order must be begin < snapshot < seal < after < undo < commit")
    for line in fb.split("\n"):
        for m in _ATTEMPT_CALL.finditer(line):
            tail = re.split(r"&&|;", line[m.start():], maxsplit=1)[0]
            if "--attempt" not in tail:
                problems.append("%s lacks --attempt" % m.group(1))
    if FRESH_ATTEMPT not in fb:
        problems.append("fresh-attempt sentence missing")
    arms = case_arms(fb, FIXSTAGE + "commit")
    for label in ("0", "3", "4", "5", "6", "7", "8", "9", "*"):
        if label not in arms:
            problems.append("commit case lacks a %s) arm" % label)
    arm9 = arms.get("9", "")
    if not ("publication-uncertain" in arm9 and "record errored" in arm9
            and EXIT9_NO_RETRY in arm9
            and "NOTHING is committed" not in arm9):
        problems.append("9) arm must name publication-uncertain, record "
                        "errored, forbid a retry and not claim nothing was "
                        "committed")
    if "hook-changed" not in arms.get("5", ""):
        problems.append("5) arm must name hook-changed")
    if "moved-after-commit" not in arms.get("7", ""):
        problems.append("7) arm must name moved-after-commit")
    if not ("published-unverified" in arms.get("8", "")
            and "record errored" in arms.get("8", "")):
        problems.append("8) arm must name published-unverified and record errored")
    if "NOTHING is staged and NOTHING is committed" not in arms.get("*", ""):
        problems.append("*) arm must say nothing is staged or committed")
    return problems


def exit8_rider_problems(step_b):
    """The exit-8 render clause (from `8 → errored` to `9 → errored`) carries
    the hook-changed rider. Anchored: the rider's sentence also occurs in the
    `5)` echo arm, so a bare substring check could pass on the wrong clause."""
    start = step_b.find("8 → `errored`")
    end = step_b.find("9 → `errored`", start + 1) if start >= 0 else -1
    if start < 0 or end < 0:
        return ["no exit-8 render clause"]
    if EXIT8_RIDER not in step_b[start:end]:
        return ["exit-8 clause lacks the hook-changed rider"]
    return []


def exit9_render_problems(step_b):
    """The exit-9 render clause (from `9 → errored` to `anything else →`)."""
    start = step_b.find("9 → `errored`")
    end = step_b.find("anything else →", start + 1) if start >= 0 else -1
    if start < 0 or end < 0:
        return ["no exit-9 render clause"]
    clause = step_b[start:end]
    return ["exit-9 clause lacks %s" % token
            for token in ("publication-uncertain:", "git log",
                          "not retried automatically")
            if token not in clause]


def fix_md_exit9_problems(text):
    """agents/fix.md's commit case has a `9)` arm between `8)` and `*)`, and
    exactly one **9** bullet forbidding an automatic re-attempt."""
    problems = []
    arms = case_arms(text, COMMIT_INVOCATION)
    if "9" not in arms:
        problems.append("fix.md commit case lacks a 9) arm")
    else:
        arm = arms["9"]
        for token in ("publication-uncertain", "record errored", EXIT9_NO_RETRY):
            if token not in arm:
                problems.append("9) arm lacks %s" % token)
        if "NOTHING is committed" in arm:
            problems.append("9) arm claims nothing was committed")
        labels = list(arms)
        if not ("8" in labels and "*" in labels
                and labels.index("8") < labels.index("9") < labels.index("*")):
            problems.append("9) arm is not between 8) and *)")
    bullets = [l for l in text.split("\n") if l.strip().startswith("- **9** →")]
    if len(bullets) != 1:
        problems.append("fix.md needs exactly one **9** bullet")
    else:
        for token in ("errored", "publication-uncertain:", "git log",
                      FIX_MD_NO_REATTEMPT):
            if token not in bullets[0]:
                problems.append("**9** bullet lacks %s" % token)
    return problems


def exit9_parity_problems(fix_text, step_b):
    """Both consumers' `9)` arms are identical and forbid a retry."""
    fix_arm = case_arms(fix_text, COMMIT_INVOCATION).get("9")
    loop_arm = case_arms(step_b, COMMIT_INVOCATION).get("9")
    if fix_arm is None or loop_arm is None:
        return ["a 9) arm is missing (fix.md: %s, 50-fix-loop.md: %s)"
                % (fix_arm is not None, loop_arm is not None)]
    problems = []
    if fix_arm.strip() != loop_arm.strip():
        problems.append("9) arms differ between fix.md and 50-fix-loop.md")
    if EXIT9_NO_RETRY not in fix_arm or EXIT9_NO_RETRY not in loop_arm:
        problems.append("a 9) arm does not forbid a retry")
    return problems


# --- the exit table: every prose case block is locked to fixstage -------- #

# Every (file, subcommand) whose `case "$rc"` block copies fixstage's arms.
ARMS_CONSUMERS = ((FIX_MD, "begin"), (FIX_MD, "undo"), (FIX_MD, "commit"),
                  (FIX_LOOP, "begin"), (FIX_LOOP, "undo"),
                  (FIX_LOOP, "commit"), (FIX_LOOP, "preflight"))
_CASE_BLOCK = re.compile(
    r'fixstage\.py" (\w+) [^\n]*; rc=\$\?\n([ ]*)case "\$rc" in\n(.*?)\n\2esac',
    re.S)
PREFLIGHT_INVOCATION = 'fixstage.py" preflight --root "$GREPO"'
BUILD_DISPATCH = "**Build the dispatch (deterministic).**"
SUBSET_BULLET = "- **Finalize routed a fix set here (D-10)**"
ORDINARY_BULLET = "- **Every other pass**"
SUBSET_NO_CARD = ("Finalize already printed its `echo_text` before reading "
                  "this file — do not print it again. Write "
                  "`{\"all\": true}` to `$ANSWERFILE` with the Write tool, and "
                  "go straight to **Step B** — ask NO AskUserQuestion: the "
                  "owner already chose these rows at Finalize (D-06).")
BUDGET_NO_CARD = "a Finalize-routed subset costs no card"
# Words that name the Finalize-routed case, and verbs that would show it a
# card. A sentence outside the subset bullet holding one of each is a
# second, contradicting rule (bug C, mutant C).
SUBSET_CASE_WORDS = ("Finalize routed", "Finalize-routed", "$SUBSETFILE")
SUBSET_CARD_VERBS = ("AskUserQuestion", "show the card", "Apply or Skip")
MUTANT_C = ("When Finalize routed a fix set, show the card below so the "
            "owner can Apply or Skip.")


def case_blocks(text):
    """[(sub, dedented case body)] for every fixstage `case "$rc"` block."""
    out = []
    for m in _CASE_BLOCK.finditer(text):
        indent = m.group(2)
        lines = [l[len(indent):] if l.startswith(indent) else l
                 for l in m.group(3).split("\n")]
        out.append((m.group(1), "\n".join(lines)))
    return out


def rendered_arms(sub):
    """{label: arm text} parsed from fixstage.render_case_arms(sub)."""
    return {m.group(1): m.group(2) for m in
            re.finditer(r"^\s+(\d|\*)\) (.*)$",
                        fixstage.render_case_arms(sub), re.M)}


def arms_parity_problems(text, sub):
    """Every `case "$rc"` block after `fixstage.py" <sub>` in `text` is
    byte-equal to fixstage.render_case_arms(sub) ([] = holds)."""
    blocks = [body for name, body in case_blocks(text) if name == sub]
    if not blocks:
        return ["no case block for fixstage %s" % sub]
    want = fixstage.render_case_arms(sub)
    problems = ["%s case block #%d differs from render_case_arms" % (sub, i + 1)
                for i, body in enumerate(blocks) if body != want]
    if case_arms(text, 'fixstage.py" %s' % sub) != rendered_arms(sub):
        problems.append("%s arms differ from the exit table" % sub)
    return problems


def record_mapping_problems(step_b):
    """The fallback's commit record mapping names every (code, verdict) of
    EXIT_TABLE["commit"], in table order."""
    lines = [l for l in step_b.split("\n")
             if l.strip().startswith("Exit 0 → `applied`")]
    if len(lines) != 1:
        return ["commit record mapping line missing or duplicated"]
    line = lines[0]
    problems, at = [], 0
    for code, _label, verdict, _arm in fixstage.EXIT_TABLE["commit"]:
        if code == 0:
            needle = "Exit 0 → `%s`" % verdict
        elif code == "*":
            needle = "anything else → `%s`" % verdict
        else:
            needle = "; %s → `%s`" % (code, verdict)
        found = line.find(needle, at)
        if found < 0:
            problems.append("record mapping lacks %s" % needle)
        else:
            at = found
    return problems


def _fence_around(text, at):
    open_at = text.rindex("```bash", 0, at)
    return text[open_at:text.index("```", at)]


def preflight_fence_problems(step_b):
    """The preflight fence runs before Build the dispatch and first in the
    inline fallback; its 1) arm pauses and never reruns ([] = holds)."""
    problems = []
    hits = [m.start() for m in re.finditer(re.escape(PREFLIGHT_INVOCATION),
                                           step_b)]
    if BUILD_DISPATCH not in step_b or FALLBACK_START not in step_b:
        return ["Build the dispatch or the inline fallback is missing"]
    build_at = step_b.index(BUILD_DISPATCH)
    if not any(h < build_at for h in hits):
        problems.append("no preflight fence before Build the dispatch")
    fb = fallback_section(step_b)
    fb_hits = [m.start() for m in re.finditer(re.escape(PREFLIGHT_INVOCATION),
                                              fb)]
    first_call = fb.find(FIXSTAGE + "begin")
    if not fb_hits or (first_call >= 0 and fb_hits[0] > first_call):
        problems.append("no preflight fence before the fallback's first call")
    for h in hits:
        fence = _fence_around(step_b, h)
        if OPTIONAL_EXPANSION.search(fence):
            problems.append("preflight fence uses an optional expansion")
        if "; rc=$?" not in fence or 'case "$rc" in' not in fence:
            problems.append("preflight fence does not branch with case")
        arm1 = case_arms(fence, 'fixstage.py" preflight').get("1", "")
        if "Paused." not in arm1:
            problems.append("preflight 1) arm does not pause")
        if "rerun" in arm1.lower():
            problems.append("preflight 1) arm mentions the Rerun")
    return problems


def subset_no_card_problems(card):
    """A Finalize-routed subset goes straight to Step B with no card."""
    problems = []
    if SUBSET_BULLET not in card or ORDINARY_BULLET not in card:
        return ["subset or ordinary bullet missing"]
    bullet = card[card.index(SUBSET_BULLET):card.index(ORDINARY_BULLET)]
    if SUBSET_NO_CARD not in bullet:
        problems.append("subset bullet does not go straight to Step B")
    if bullet.count("AskUserQuestion") != 1:
        problems.append("subset bullet mentions AskUserQuestion other than "
                        "to forbid it")
    if '{"all": true}' not in bullet:
        problems.append("subset bullet does not write the all answer")
    budget = [l for l in card.split("\n") if l.startswith("**Card budget.**")]
    if len(budget) != 1 or BUDGET_NO_CARD not in budget[0]:
        problems.append("card budget does not say the subset costs no card")
    # The bullet is the only rule for a Finalize-routed set: no sentence
    # anywhere else in the card section may tie that case to a card.
    rest = card.replace(bullet, "", 1)
    for sentence in re.split(r"\. |\n", rest):
        if (any(w in sentence for w in SUBSET_CASE_WORDS)
                and any(v in sentence for v in SUBSET_CARD_VERBS)):
            problems.append("off-bullet sentence asks a card for the "
                            "Finalize-routed set: " + sentence.strip()[:80])
    return problems


def arm_echo(arm, rc):
    """The text an `echo "..."` arm prints for exit `rc`."""
    m = re.match(r'echo "(.*)"( >&2)?$', arm)
    return m.group(1).replace("$rc", str(rc)) if m else None


def run_commit_fence(text, rc):
    """Execute the ```bash fence holding the fixstage commit call, with a
    fixstage stub that prints `publication-uncertain: <sha>` (the real
    fixstage's stdout line 1 on a failed recovery read) and exits `rc`.
    Returns stdout + stderr."""
    at = text.index(COMMIT_INVOCATION)
    open_at = text.rindex("```bash", 0, at)
    close_at = text.index("```", at)
    line_start = text.rfind("\n", 0, open_at) + 1
    indent = text[line_start:open_at]
    body = text[text.index("\n", open_at) + 1:close_at]
    lines = [l[len(indent):] if l.startswith(indent) else l.lstrip()
             for l in body.split("\n")]
    snippet = "\n".join(lines).replace("<A>", FENCE_ATTEMPT)
    tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(tmp, "scripts"))
        with open(os.path.join(tmp, "scripts", "fixstage.py"), "w") as fh:
            fh.write("import sys\nprint('publication-uncertain: %s')\n"
                     "sys.exit(%d)\n" % (FENCE_SHA, rc))
        repo = os.path.join(tmp, "repo")
        os.makedirs(repo)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=30)
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=tmp, VC_ROOT=tmp)
        proc = subprocess.run(["bash", "-c", snippet], cwd=repo, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=30)
        return proc.stdout + proc.stderr
    finally:
        shutil.rmtree(tmp)


def unavailable_problems(step_b):
    fb = fallback_section(step_b)
    problems = []
    if UNDO_CONDITION not in fb or FIXSTAGE + "undo" not in fb:
        return ["undo condition or undo call missing"]
    cond = fb[fb.index(UNDO_CONDITION):fb.index(FIXSTAGE + "undo")]
    if "`unavailable`" not in cond:
        problems.append("undo condition does not name `unavailable`")
    line = render_line(render_section(step_b), "unverified")
    if not ("`unavailable`" in line and '"could not run"' in line):
        problems.append("render does not map unavailable to could not run")
    return problems


def dispatch_problems(step_b):
    prompt = _flat(dispatch_prompt(step_b))
    problems = ["dispatch lacks " + n for n in ("`unverified`",
                                                 "`fixstage.py commit`")
                if n not in prompt]
    if OLD_PATHSPEC in prompt:
        problems.append("dispatch still asks for the git add pathspec commit")
    return problems


def label_problems(step_b):
    line = render_line(render_section(step_b), "applied")
    return ["applied render lacks " + l for l in CHECK_LABELS if l not in line]


SUBSET_ROWS_LINE = ('if ROWS_JSON=$(python3 "$VC_ROOT/scripts/batch_card.py" '
                    'rows --mode fix-loop --subset "<subset path>" '
                    '< "$STATE_FILE"); then')
PLAIN_ROWS_LINE = ('if ROWS_JSON=$(python3 "$VC_ROOT/scripts/batch_card.py" '
                   'rows --mode fix-loop < "$STATE_FILE"); then')
NO_SUBSET_REFUSAL = ("No fix set from Finalize — the fix loop will not fall "
                     "back to every open row; nothing was changed")
SUBSET_LITERAL_RULE = ("the literal path Finalize's subset step printed "
                       "after `SUBSETFILE=`")


def subset_fence_problems(card):
    """Why the rows fences could mis-route a Finalize fix set (empty = ok)."""
    problems = []
    rows_lines = [line.strip() for line in card.splitlines()
                  if ROWS_CALL in line]
    if any(":+" in line or "$SUBSETFILE" in line for line in rows_lines):
        problems.append("rows call builds --subset from a shell variable")
    for line, name in ((SUBSET_ROWS_LINE, "subset fence"),
                       (PLAIN_ROWS_LINE, "ordinary fence")):
        if rows_lines.count(line) != 1:
            problems.append(name + " missing or duplicated")
    for needle in (NO_SUBSET_REFUSAL, SUBSET_LITERAL_RULE,
                   "Never run the ordinary fence in its place"):
        if needle not in card:
            problems.append("missing: " + needle)
    return problems


def read_text():
    with open(FIX_LOOP, "r", encoding="utf-8") as fh:
        return fh.read()


def card_section(text):
    start = text.index(CARD_HEADING)
    return text[start:text.index(STEP_B_HEADING, start)]


def step_b_section(text):
    start = text.index(STEP_B_HEADING)
    return text[start:text.index(TERMINATION_HEADING, start)]


def nudge_count(text):
    """Occurrences of a preferred-default nudge anywhere in the file."""
    return text.count("(Recommended)") + text.count("Recommended")


def dispatch_pins_hold(text):
    """True when Step B dispatches exactly the payload output (D-10)."""
    step_b = step_b_section(text)
    card = card_section(text)
    return (FIX_SENT_BINDING in step_b
            and FINDINGS_VERBATIM in step_b
            and OLD_PLACEHOLDER not in text
            and "routed through" in card
            and "which is not being fixed" in card)


def header_value(literal):
    """The quoted header value with its {{placeholder}} parts removed."""
    value = literal.split('"', 2)[1]
    while "{{" in value:
        a = value.index("{{")
        value = value[:a] + value[value.index("}}", a) + 2:]
    return value.strip()


def headers_fit(card):
    for literal in (CARD_HEADER, STOP_HEADER):
        if card.count(literal) != 1:
            return False
        if len(header_value(literal)) > MAX_HEADER_CHARS:
            return False
    return True


LIST_IN_CARD = (
    "copy the `card_text` field of `$ROWSFILE` verbatim into the question",
    "never print it only from a shell command",
    "When `card_text_truncated` is true",
    "ALSO print the `list_text` field verbatim as message text",
)
FINALIZE_ECHO_RESIDUE = ("From your finalize answer:", "<echo_text>")


def question_line(card):
    """The fix-loop card's **Question:** line."""
    start = card.index("> **Question:** \"Pass {{$PASS_NUMBER}}")
    return card[start:card.index("\n", start)]


def list_in_card_problems(card):
    """[] when the numbered list is carried INSIDE the card's question."""
    problems = [n for n in LIST_IN_CARD if card.count(n) != 1]
    question = question_line(card)
    for needle in ("{{card_text}}", "listed below"):
        if needle not in question:
            problems.append("question lacks " + needle)
    # No card is shown on a Finalize-routed pass, so the card never carries
    # a "From your finalize answer:" block (I-10).
    for gone in FINALIZE_ECHO_RESIDUE:
        if gone in card:
            problems.append("finalize-answer residue in the card: " + gone)
    if "Message text above the card" in card:
        problems.append("list printed as message text above the card")
    return problems


DECISIONS_CALL = 'record-decisions --decisions-file "$DECFILE"'


def decisions_fence(text):
    """The bash fence holding the fix loop's one record-decisions call."""
    at = text.index(DECISIONS_CALL)
    start = text.rindex("```bash", 0, at)
    return text[start:text.index("```", at)]


def decisions_writer_problems(text):
    """[] when the fix loop writes `decisions` exactly once, atomically."""
    problems = []
    if text.count(DECISIONS_CALL) != 1:
        problems.append("expected exactly one %s, found %d"
                        % (DECISIONS_CALL, text.count(DECISIONS_CALL)))
    if text.count("record-decisions") != text.count(DECISIONS_CALL):
        problems.append("a record-decisions call outside the pinned one")
    if problems:
        return problems
    fence = decisions_fence(text)
    for needle in ('< "$STATE_FILE" > "$STATE_FILE.tmp"',
                   '&& mv "$STATE_FILE.tmp" "$STATE_FILE"',
                   'rm -f "$STATE_FILE.tmp"'):
        if needle not in fence:
            problems.append("decisions fence lacks " + needle)
    return problems


NV_DECIDED_LINE = (
    "Needs-verification rows are decided only by number: type in Other "
    "`fix N` to confirm (the fix agent takes it), or `dismiss N -- reason` / "
    "`defer N -- reason`; `Apply all & rerun` leaves them untouched.")
NV_APPLY_ALL_NOTE = ("(Needs-verification rows are not applied — confirm "
                     "them by number.)")
NV_TYPED_BRANCH = "**Typed answer via Other**"
# Apply all's scope is rendered by the helper (58-01 `bulk_fix_text`), which
# names the Needs-verification rows it leaves out by number (D-10..D-12).
BULK_FIX_SLOT = "{{bulk_fix_text}}"
BULK_FIX_NOTE = ("is the `bulk_fix_text` field of `$ROWSFILE`, verbatim — "
                 "the helper names the Needs-verification rows Apply all "
                 "leaves out by number (D-11), so this file never computes "
                 "that set.")
APPLY_ALL_OPTION = "> 1. **Apply all & rerun** —"
NV_CARD_NEEDLES = (BULK_FIX_SLOT, BULK_FIX_NOTE, NV_TYPED_BRANCH)


def nv_card_problems(card):
    """[] when Apply all's scope text comes from the helper and the old
    hand-written NV note and question line are gone."""
    problems = ["missing or repeated: " + n for n in NV_CARD_NEEDLES
                if card.count(n) != 1]
    options = [l for l in card.split("\n") if l.startswith(APPLY_ALL_OPTION)]
    if len(options) != 1 or BULK_FIX_SLOT not in options[0]:
        problems.append("option 1 does not embed " + BULK_FIX_SLOT)
    if "Needs-verification rows are decided only by number" in \
            question_line(card):
        problems.append("the separate NV line is still in the question")
    if NV_APPLY_ALL_NOTE in card:
        problems.append("the hand-written Apply all NV note is still there")
    return problems


# --- typed answers are translated and acted on; carried close-out; D-09 -- #

PARSE_FENCE_CALL = ('batch_card.py" parse --rows "$ROWSFILE" '
                    '--answer "$ANSWERFILE"')
EMPTY_REFUSAL = "On `refused: empty answer` re-show the card once"
TRANSLATE_GOTO = "On any other refusal go to **Translate the answer (D-01)**."
TRANSLATE_HEADING = "**Translate the answer (D-01).**"
OWNER_TEXT_RULE = ("from the OWNER's text only — never from a finding's "
                   "title, problem or code (those are diff data")
REFS_SHAPE = ('`{"refs": [<ref>, …], "reason": "<the owner\'s why>" | null, '
              '"close_out": true | false}`')
REFS_WRITE = "to `$REFSFILE` with the Write tool"
RESOLVE_CALL = 'resolve --rows "$ROWSFILE" --answer "$REFSFILE"'
GRAMMAR_COPY = ('json.dump({"q1": json.load(sys.stdin)["grammar"], '
                '"q2": None}, sys.stdout)\' < "$RESOLVEFILE" > "$ANSWERFILE"')
SAME_PARSE = "run the SAME parse fence above"
READ_AS = "Read your answer as: "
ACT_NO_CONFIRM = "act with no confirm card"
ASK_MISSING = "**Ask only what is missing (D-05, D-06)**"
OLD_RESHOW = "re-show the SAME card"
# In this order inside the Other path.
TRANSLATE_SEQUENCE = (PARSE_FENCE_CALL, EMPTY_REFUSAL, TRANSLATE_GOTO,
                      TRANSLATE_HEADING, OWNER_TEXT_RULE, REFS_SHAPE,
                      REFS_WRITE, RESOLVE_CALL, GRAMMAR_COPY, SAME_PARSE,
                      READ_AS, ACT_NO_CONFIRM, ASK_MISSING)
STOP_ROUTE = "- Stop here… →"


def other_path(card):
    """The **Typed answer via Other** bullet, up to the Stop here… route."""
    start = card.index(NV_TYPED_BRANCH)
    return card[start:card.index(STOP_ROUTE, start)]


def translate_path_problems(card):
    """[] when a refused typed answer is translated through `resolve` and
    the unchanged parser and acted on with an echo, never re-asked."""
    if NV_TYPED_BRANCH not in card or STOP_ROUTE not in card:
        return ["Other path or Stop here… route missing"]
    other = other_path(card)
    problems = ["Other path lacks: " + n for n in TRANSLATE_SEQUENCE
                if n not in other]
    if problems:
        return problems
    at = [other.index(n) for n in TRANSLATE_SEQUENCE]
    if at != sorted(at):
        problems.append("Other path steps are out of order")
    call = other.index(RESOLVE_CALL)
    fence = other.rfind("```bash", 0, call)
    if fence < 0 or "```" in other[fence + len("```bash"):call]:
        problems.append("resolve call is not inside a bash fence")
    if OLD_RESHOW in card:
        problems.append("a refusal still re-shows the SAME card")
    return problems


CLOSE_OUT_CARRY = "**Close out carried from the previous pass (D-17).**"
CARRY_LINE = "CLOSE_OUT_AFTER_RERUN=1"
CARRY_NEEDLES = (CARRY_LINE, "do not render the card",
                 "even when the rerun reported new findings",
                 "${original_args} --finalize", "drops it")
# The tmp files do not survive the Rerun, so the carry never reads them.
CARRY_FORBIDDEN = ("$RESOLVEFILE", "close_out")
BIND_ROWS = "**Bind the rows.**"


def close_out_carry_problems(text):
    """[] when the fix loop reads a carried close-out from Phase 0's printed
    line, before any fence, and goes to Close out without the card."""
    card = card_section(text)
    if CLOSE_OUT_CARRY not in card:
        return ["no carried close-out paragraph"]
    start = card.index(CLOSE_OUT_CARRY)
    para = card[start:card.index("\n\n", start)]
    problems = ["carry paragraph lacks: " + n for n in CARRY_NEEDLES
                if n not in para]
    problems += ["carry paragraph reads a tmp-file token: " + n
                 for n in CARRY_FORBIDDEN if n in para]
    if BIND_ROWS not in card or start > card.index(BIND_ROWS) \
            or start > card.index("```bash"):
        problems.append("carry paragraph is not before the rows fences")
    if text.count(CARRY_LINE) != 1:
        problems.append("%s x%d" % (CARRY_LINE, text.count(CARRY_LINE)))
    return problems


BOTTOM_LINE_SLOT = ('{{\\n\\nBottom line suggests: <grammar> — type '
                    '"bottom line" in Other to take it}}')
BOTTOM_LINE_HEAD = "**Bottom line as a choice (D-09).**"
BOTTOM_LINE_QUESTION_NOTE = ("The `Bottom line suggests:` line appears ONLY "
                             "when the suggestion fence below printed a "
                             "`SUGGESTFILE=` path created on this pass")
BOTTOM_LINE_NEEDLES = ("this pass's Bottom line in THIS session",
                       'suggest --rows "$ROWSFILE" --answer "$SUGGESTFILE"',
                       'rm -f "$SUGGESTFILE"',
                       "never print a guessed one",
                       "the 4 options and the neutral menu stay")


def bottom_line_problems(card):
    """[] when the card offers the Bottom line's verdict only as a parser-
    accepted grammar line, with no nudge on any option (D-09, LEGIBLE-03)."""
    problems = []
    question = question_line(card)
    if BOTTOM_LINE_SLOT not in question:
        problems.append("question lacks the Bottom line slot")
    if BOTTOM_LINE_QUESTION_NOTE not in card:
        problems.append("question note lacks the ONLY-when rule")
    if BOTTOM_LINE_HEAD not in card:
        return problems + ["no Bottom line paragraph"]
    start = card.index(BOTTOM_LINE_HEAD)
    end = card.find("\n\n**", start)
    para = card[start:end if end >= 0 else len(card)]
    problems += ["Bottom line paragraph lacks: " + n
                 for n in BOTTOM_LINE_NEEDLES if n not in para]
    if nudge_count(card):
        problems.append("a nudge in the card")
    return problems


OLD_HOLD = ("A recorded dismiss or defer holds until its own line is edited "
            "or its band changes (D-12); unrelated edits elsewhere never "
            "re-ask it.")
HOLD_NEEDLES = ("A recorded dismiss or defer holds while its evidence is "
                "unchanged",
                "a line shift alone never re-asks it",
                "code next to it changed",
                "a new concern from another lane joined it",
                "its severity rose because a new lane now reports it",
                "a severity drop keeps the decision",
                "(Phase 57 D-01, D-02, D-05, D-06, D-08)")


def decision_hold_problems(card):
    """[] when the hold sentence says what Phase 57's stale check does."""
    problems = []
    if card.count(HOLD_NEEDLES[0]) != 1:
        problems.append("hold sentence missing or repeated")
        sentence = ""
    else:
        start = card.index(HOLD_NEEDLES[0])
        sentence = card[start:card.index("\n", start)]
    problems += ["hold sentence lacks: " + n for n in HOLD_NEEDLES[1:]
                 if n not in sentence]
    if "holds until its own line is edited" in card:
        problems.append("the pre-Phase-57 hold sentence is back")
    return problems


BUDGET_NEEDLES = (
    "A pass costs one card", BUDGET_NO_CARD,
    "a carried close-out (D-17) costs none",
    "a plain-English answer that needs one detail costs at most one "
    "follow-up card per gap (D-06)",
    "a second unclear reply shows the full card once (D-08)",
    "`look N` re-shows the card at the owner's request")


def budget_problems(text):
    """[] when the one budget line enumerates every card the loop can show."""
    lines = [l for l in text.split("\n") if l.startswith("**Card budget.**")]
    if len(lines) != 1:
        return ["expected one Card budget line, found %d" % len(lines)]
    problems = ["budget lacks: " + n for n in BUDGET_NEEDLES
                if n not in lines[0]]
    if "an unparseable answer" in lines[0]:
        problems.append("budget still re-shows on an unparseable answer")
    return problems


class TestFixLoopCard(unittest.TestCase):

    def setUp(self):
        self.text = read_text()
        self.card = card_section(self.text)

    # (a) labels
    def test_every_label_appears_in_the_prose(self):
        for label in batch_parse.FIX_LOOP_OPTIONS + batch_parse.STOP_OPTIONS:
            with self.subTest(label=label):
                self.assertIn(label, self.text)

    def test_each_card_option_is_bold_exactly_once_in_the_card(self):
        for label in batch_parse.FIX_LOOP_OPTIONS:
            with self.subTest(label=label):
                self.assertEqual(self.card.count("**%s**" % label), 1)

    # (b) one card, same-turn rule, pending rows in the message text
    def test_one_card_and_same_turn_rule(self):
        self.assertIn("ONE card", self.card)
        self.assertIn("THIS assistant turn", self.card)
        self.assertIn(
            "unchanged since pass {{pending_since}}, decision pending",
            self.card)

    # (c) no nudge anywhere, lock proven load-bearing
    def test_no_recommended_nudge_anywhere(self):
        self.assertEqual(self.text.count("(Recommended)"), 0)
        self.assertEqual(self.text.count("Recommended"), 0)
        self.assertEqual(nudge_count(self.text), 0)

    def test_no_nudge_lock_trips_on_mutant(self):
        mutant = self.text.replace("**Apply all & rerun**",
                                   "**Apply all & rerun (Recommended)**", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertGreater(nudge_count(mutant), 0)

    # (d) section shape
    def test_old_menus_gone_and_step_b_kept(self):
        self.assertNotIn("### Step A", self.text)
        self.assertNotIn("### Step C", self.text)
        self.assertEqual(self.text.count("### Step B"), 1)
        self.assertEqual(self.text.count(CARD_HEADING), 1)

    # (e) Step B needles
    def test_step_b_needles_present(self):
        step_b = step_b_section(self.text)
        for needle in STEP_B_NEEDLES:
            with self.subTest(needle=needle):
                self.assertIn(needle, step_b)

    # (f) Paused. lines
    def test_paused_lines_exactly_once(self):
        self.assertEqual(self.text.count(PAUSED_REVIEW), 1)
        self.assertEqual(self.text.count(PAUSED_DEEP), 1)

    # (g) helper calls; payload is the one dispatch source
    def test_helper_calls(self):
        # Two rows fences: the Finalize-routed subset one and the ordinary one.
        self.assertEqual(self.text.count(ROWS_CALL), 2)
        self.assertEqual(self.text.count(SELECT_QUESTIONS_CALL), 1)
        self.assertEqual(self.text.count(PAYLOAD_CALL), 1)
        self.assertNotIn(SELECT_CALL, self.text)

    # (g2) payload dispatch pins (Codex CRITICAL 2), with mutants
    def test_dispatch_is_the_payload_output(self):
        self.assertTrue(dispatch_pins_hold(self.text))

    def test_dispatch_pins_trip_on_old_placeholder(self):
        mutant = self.text.replace(FINDINGS_VERBATIM, OLD_PLACEHOLDER, 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(dispatch_pins_hold(mutant))

    def test_dispatch_pins_trip_on_every_row_binding(self):
        mutant = self.text.replace(
            FIX_SENT_BINDING, "Bind `$FIX_SENT` = every row's `stable_hash`", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(dispatch_pins_hold(mutant))

    # (g3) agents/fix.md changes only with a deliberate re-pin
    def test_fix_md_unchanged(self):
        with open(FIX_MD, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(digest, FIX_MD_SHA256)

    # (h) banned literal: no silent fall-through
    def test_no_fall_through(self):
        self.assertNotIn("|| { :", self.text)

    # (h2) the fix loop is the second permitted decisions writer: exactly one
    # record-decisions call, in the .tmp + mv + rm -f shape, with a mutant
    def test_single_decisions_writer_pinned(self):
        self.assertEqual(decisions_writer_problems(self.text), [])

    def test_single_decisions_writer_mutants_trip(self):
        with self.subTest("mutant: a second record-decisions call"):
            mutant = self.text + "\n" + DECISIONS_CALL + " again\n"
            self.assertNotEqual(mutant, self.text)
            self.assertNotEqual(decisions_writer_problems(mutant), [])
        with self.subTest("mutant: the call is gone"):
            mutant = self.text.replace(DECISIONS_CALL, "record-decisions", 1)
            self.assertNotEqual(mutant, self.text)
            self.assertNotEqual(decisions_writer_problems(mutant), [])
        with self.subTest("mutant: no rm -f on refusal"):
            fence = decisions_fence(self.text)
            mutant = self.text.replace(
                fence, fence.replace('rm -f "$STATE_FILE.tmp"', ":"), 1)
            self.assertNotEqual(mutant, self.text)
            self.assertNotEqual(decisions_writer_problems(mutant), [])
        with self.subTest("mutant: written in place, no .tmp + mv"):
            fence = decisions_fence(self.text)
            mutant = self.text.replace(fence, fence.replace(
                '> "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"',
                '> "$STATE_FILE"'), 1)
            self.assertNotEqual(mutant, self.text)
            self.assertNotEqual(decisions_writer_problems(mutant), [])

    # (h3) the card tells the owner how Needs-verification rows are decided
    def test_nv_card_lines(self):
        self.assertEqual(nv_card_problems(self.card), [])

    def test_nv_card_mutants_trip(self):
        for needle in NV_CARD_NEEDLES:
            with self.subTest(deleted=needle):
                mutant = self.card.replace(needle, "", 1)
                self.assertNotEqual(mutant, self.card)
                self.assertNotEqual(nv_card_problems(mutant), [])
        with self.subTest("mutant: option 1 back to the hand-written note"):
            mutant = self.card.replace(
                BULK_FIX_SLOT, "every listed row " + NV_APPLY_ALL_NOTE, 1)
            self.assertNotEqual(mutant, self.card)
            self.assertNotEqual(nv_card_problems(mutant), [])
        with self.subTest("mutant: the separate NV line back in the question"):
            question = question_line(self.card)
            mutant = self.card.replace(
                question, question.replace(
                    "{{card_text}}", "{{card_text}}{{\\n\\n" +
                    NV_DECIDED_LINE + "}}", 1), 1)
            self.assertNotEqual(mutant, self.card)
            self.assertNotEqual(nv_card_problems(mutant), [])

    # (i) card budget
    def test_card_budget_sentence(self):
        self.assertEqual(self.text.count("A pass costs one card"), 1)

    # (j) card headers, with a length mutant
    def test_card_headers_pinned_and_short(self):
        self.assertEqual(self.card.count(CARD_HEADER), 1)
        self.assertEqual(self.card.count(STOP_HEADER), 1)
        self.assertTrue(headers_fit(self.card))

    def test_header_length_check_trips_on_mutant(self):
        mutant = self.card.replace(STOP_HEADER,
                                   'header "Stop here and choose"', 1)
        self.assertNotEqual(mutant, self.card)
        self.assertFalse(headers_fit(mutant))
        self.assertGreater(len(header_value('header "Stop here and choose"')),
                           MAX_HEADER_CHARS)

    # (k) stale rows render in the card
    def test_stale_suffix_in_card(self):
        self.assertEqual(
            self.card.count("code changed since your decision on pass"), 1)
        self.assertIn('stale.via == "same_hash"', self.card)
        self.assertIn('stale.via == "successor"', self.card)

    # Typed mode (more than 16 rows) is a single-select with two exclusive
    # buttons; the typed list arrives through Other.
    def test_typed_mode_buttons(self):
        self.assertIn('"All listed"', self.card)
        self.assertIn('"None — skip & rerun"', self.card)
        self.assertIn("arrive through \"Other\"", self.card)

    # A Finalize-routed subset is consumed once: cleared before every rerun.
    def test_subset_cleared_before_rerun(self):
        rerun = self.card[self.card.index("**The Rerun.**"):]
        clear = 'rm -f "$SUBSETFILE"; unset SUBSETFILE'
        self.assertIn(clear, rerun)
        self.assertLess(rerun.index(clear), rerun.index("loop back to Phase 0"))

    # The rows call never builds --subset from an optional-flag expansion:
    # zsh does not word-split `${SUBSETFILE:+--subset "$SUBSETFILE"}` (one
    # argv word, refused by batch_card.parse_argv), and a variable bound in
    # Finalize's fence does not survive into this Bash call.
    def test_subset_flag_is_never_an_optional_expansion(self):
        self.assertEqual(subset_fence_problems(self.card), [])
        with self.subTest("mutant: the old :+ expansion"):
            mutant = self.card.replace(
                SUBSET_ROWS_LINE,
                SUBSET_ROWS_LINE.replace(
                    '--subset "<subset path>"',
                    '${SUBSETFILE:+--subset "$SUBSETFILE"}'), 1)
            self.assertNotEqual(subset_fence_problems(mutant), [])
        with self.subTest("mutant: subset fence uses the variable"):
            mutant = self.card.replace('"<subset path>"', '"$SUBSETFILE"', 1)
            self.assertNotEqual(subset_fence_problems(mutant), [])
        with self.subTest("mutant: ordinary fence dropped"):
            mutant = self.card.replace(PLAIN_ROWS_LINE, "", 1)
            self.assertNotEqual(subset_fence_problems(mutant), [])
        with self.subTest("mutant: no refusal when the path is missing"):
            mutant = self.card.replace(NO_SUBSET_REFUSAL, "", 1)
            self.assertNotEqual(subset_fence_problems(mutant), [])


    # (l) the numbered list is carried IN the card (D1: text inside a Bash
    # call's output is collapsed by the terminal and never seen)
    def test_list_lives_in_the_card_question(self):
        self.assertEqual(list_in_card_problems(self.card), [])
        for gone in FINALIZE_ECHO_RESIDUE:
            with self.subTest(absent_from_file=gone):
                self.assertNotIn(gone, self.text)

    def test_list_in_card_trips_on_mutants(self):
        question = question_line(self.card)
        with self.subTest("mutant: card_text dropped from the question"):
            mutant = self.card.replace(
                question, question.replace("{{card_text}}", ""), 1)
            self.assertNotEqual(list_in_card_problems(mutant), [])
        with self.subTest("mutant: finalize echo block re-inserted (I-10)"):
            mutant = self.card.replace(
                question, question.replace(
                    "{{card_text}}",
                    "{{card_text}}{{\\n\\nFrom your finalize answer:"
                    "\\n<echo_text>}}", 1), 1)
            self.assertNotEqual(mutant, self.card)
            self.assertNotEqual(list_in_card_problems(mutant), [])
        with self.subTest("mutant: back to a list printed above the card"):
            mutant = self.card + "\n**Message text above the card.** Print"
            self.assertNotEqual(list_in_card_problems(mutant), [])
        with self.subTest("mutant: verbatim-copy rule removed"):
            mutant = self.card.replace(LIST_IN_CARD[0], "render the list", 1)
            self.assertNotEqual(list_in_card_problems(mutant), [])


class TestStepBVerifiedFlow(unittest.TestCase):
    """Step B dispatches, falls back to and renders the verified fix flow."""

    def setUp(self):
        self.step_b = step_b_section(read_text())

    def mutate(self, old, new):
        self.assertIn(old, self.step_b)
        mutant = self.step_b.replace(old, new, 1)
        self.assertNotEqual(mutant, self.step_b)
        return mutant

    def line_with(self, needle, text=None):
        return next(l for l in (text or self.step_b).split("\n") if needle in l)

    # (a) render lists the new statuses
    def test_render_lists_new_statuses(self):
        self.assertEqual(render_problems(self.step_b), [])

    def test_render_mutant_trips(self):
        line = render_line(render_section(self.step_b), "applied-uncommitted")
        self.assertNotEqual(render_problems(self.mutate(line + "\n", "")), [])

    # (k) exit 8 carries fix.md's hook-changed rider
    def test_exit8_render_has_hook_changed_rider(self):
        self.assertEqual(exit8_rider_problems(self.step_b), [])

    def test_exit8_rider_matches_fix_md(self):
        with open(FIX_MD, encoding="utf-8") as fh:
            fix_text = fh.read()
        phrase = 'add "your commit hook changed what went into that commit"'
        self.assertIn(phrase, self.line_with("**8**", fix_text))
        start = self.step_b.index("8 → `errored`")
        end = self.step_b.index("9 → `errored`", start)
        self.assertIn(phrase, self.step_b[start:end])

    def test_exit8_rider_mutant_trips(self):
        mutant = self.mutate(EXIT8_RIDER, "")
        self.assertNotEqual(exit8_rider_problems(mutant), [])

    # (l) exit 9: publication uncertain
    def test_exit9_render_clause(self):
        self.assertEqual(exit9_render_problems(self.step_b), [])

    def test_exit9_render_mutant_trips(self):
        mutant = self.mutate(EXIT9_RENDER, "")
        self.assertNotEqual(exit9_render_problems(mutant), [])

    def test_exit9_arm_mutant_trips(self):
        lines = self.step_b.split("\n")
        hits = [l for l in lines
                if l.strip().startswith('9) echo "publication-uncertain')]
        self.assertEqual(len(hits), 1)
        mutant = self.mutate(hits[0] + "\n", "")
        self.assertIn("commit case lacks a 9) arm",
                      fallback_lifecycle_problems(mutant))
        self.assertEqual(fallback_lifecycle_problems(self.step_b), [])

    # (b) blobs rule (iii) excludes every touching status
    def test_blobs_rule_excludes_touched(self):
        self.assertEqual(blobs_rule_problems(self.step_b), [])

    def test_blobs_rule_mutant_trips(self):
        rule = self.line_with("(iii)")
        old = ("   - (iii) does not appear in `files_touched` of any result "
               'with `status == "applied"` (belt-and-braces).')
        self.assertNotEqual(blobs_rule_problems(self.mutate(rule, old)), [])

    # (c) the inline fallback commits only through fixstage
    def test_fallback_uses_fixstage(self):
        self.assertEqual(fallback_git_problems(self.step_b), [])

    def test_fallback_git_mutant_trips(self):
        commit = self.line_with(FIXSTAGE + "commit", fallback_section(self.step_b))
        mutant = self.mutate(
            commit, "  git add -- <validated finding file set>\n" + commit)
        self.assertNotEqual(fallback_git_problems(mutant), [])

    # (c2) begin < snapshot < seal < after < undo < commit, all attempt-scoped
    def test_fallback_attempt_lifecycle(self):
        self.assertEqual(fallback_lifecycle_problems(self.step_b), [])

    def test_fallback_lifecycle_mutants_trip(self):
        fb = fallback_section(self.step_b)
        seal = self.line_with(FIXSTAGE + "seal", fb)
        after = self.line_with(FIXCHECK + "after", fb)
        commit = self.line_with(FIXSTAGE + "commit", fb)
        arm5 = self.line_with("5) echo \"hook-changed", fb)
        arm7 = self.line_with("7) echo \"moved-after-commit", fb)
        arm8 = self.line_with("8) echo \"published-unverified", fb)
        moved =self.step_b.replace(seal, "  : # sealed later", 1).replace(
            after, after + "\n" + seal, 1)
        mutants = {
            "seal after the after-check": moved,
            "commit drops --attempt": self.mutate(
                commit, commit.replace(" --attempt <A>", "")),
            "after drops --attempt": self.mutate(
                after, after.replace(" --attempt <A>", "")),
            "5) arm deleted": self.mutate(arm5 + "\n", ""),
            "7) arm deleted": self.mutate(arm7 + "\n", ""),
            "8) arm deleted": self.mutate(arm8 + "\n", ""),
            "8) arm says applied": self.mutate(
                arm8, arm8.replace("record errored", "record applied")),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(mutant, self.step_b)
                self.assertNotEqual(fallback_lifecycle_problems(mutant), [])

    # (c3) an after-check that could not run is never a pass
    def test_fallback_unavailable_is_unverified(self):
        self.assertEqual(unavailable_problems(self.step_b), [])

    def test_unavailable_mutants_trip(self):
        fb = fallback_section(self.step_b)
        cond = self.line_with(UNDO_CONDITION, fb)
        render = render_line(render_section(self.step_b), "unverified")
        mutants = {
            "unavailable dropped from undo": self.mutate(
                cond, cond.replace(" AND `unavailable`", "")),
            "could-not-run render dropped": self.mutate(
                render, render.replace('"could not run"', '"passed"')),
        }
        for name, mutant in mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(unavailable_problems(mutant), [])

    # (d) the dispatch prompt names the verified flow
    def test_dispatch_prompt_names_verified_flow(self):
        self.assertEqual(dispatch_problems(self.step_b), [])

    def test_dispatch_prompt_mutant_trips(self):
        prompt = dispatch_prompt(self.step_b)
        mutant = self.mutate(prompt, prompt + "Commit the finding's validated "
                             "file set as the " + OLD_PATHSPEC + ".\n")
        self.assertNotEqual(dispatch_problems(mutant), [])

    # (e) the three check labels render on applied fixes
    def test_labels_present(self):
        self.assertEqual(label_problems(self.step_b), [])

    def test_label_mutants_trip(self):
        line = render_line(render_section(self.step_b), "applied")
        for label in CHECK_LABELS:
            with self.subTest(label=label):
                mutant = self.mutate(line, line.replace(label, "checked", 1))
                self.assertNotEqual(label_problems(mutant), [])


class TestExitTableLocks(unittest.TestCase):
    """Every prose copy of fixstage's exit table is locked byte-for-byte to
    render_case_arms; the preflight fence and the no-card subset path are
    locked; each lock has a mutant that trips it."""

    def setUp(self):
        self.texts = {}
        for path in (FIX_MD, FIX_LOOP):
            with open(path, encoding="utf-8") as fh:
                self.texts[path] = fh.read()
        self.step_b = step_b_section(self.texts[FIX_LOOP])
        self.card = card_section(self.texts[FIX_LOOP])

    def test_fix_md_pin(self):
        with open(FIX_MD, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(),
                             FIX_MD_SHA256)

    def test_arms_parity_every_consumer(self):
        for path, sub in ARMS_CONSUMERS:
            with self.subTest(file=os.path.basename(path), sub=sub):
                self.assertEqual(arms_parity_problems(self.texts[path], sub),
                                 [])

    def test_every_case_block_is_a_known_consumer(self):
        for path, text in self.texts.items():
            for sub, _body in case_blocks(text):
                self.assertIn((path, sub), ARMS_CONSUMERS)
        self.assertEqual(
            sum(1 for _ in case_blocks(self.texts[FIX_LOOP])
                if _[0] == "preflight"), 2)

    def test_record_mapping_names_every_commit_verdict(self):
        self.assertEqual(record_mapping_problems(self.step_b), [])

    def test_preflight_fence(self):
        self.assertEqual(preflight_fence_problems(self.step_b), [])

    def test_subset_no_card(self):
        self.assertEqual(subset_no_card_problems(self.card), [])
        self.assertEqual(nudge_count(self.texts[FIX_LOOP]), 0)

    def test_commit_fence_runs_every_table_arm(self):
        for path in (FIX_MD, FIX_LOOP):
            text = self.texts[path] if path == FIX_MD else self.step_b
            for code, _label, _verdict, arm in fixstage.EXIT_TABLE["commit"]:
                rc = 1 if code == "*" else code
                with self.subTest(file=os.path.basename(path), rc=rc):
                    want = arm_echo(arm, rc)
                    self.assertIsNotNone(want)
                    self.assertIn(want, run_commit_fence(text, rc))

    # ------------------------------------------------------------ mutants

    def test_mutant_arm9_deleted_from_fix_loop(self):
        text = self.texts[FIX_LOOP]
        line = [l for l in text.split("\n")
                if l.strip().startswith('9) echo "publication-uncertain')]
        self.assertEqual(len(line), 1)
        mutant = text.replace(line[0] + "\n", "", 1)
        self.assertNotEqual(mutant, text)
        self.assertNotEqual(arms_parity_problems(mutant, "commit"), [])

    def test_mutant_fix_md_arm6_word_changed(self):
        text = self.texts[FIX_MD]
        old = "HEAD moved during the commit; nothing was published"
        self.assertEqual(text.count(old), 1)
        mutant = text.replace(old, "HEAD moved during the commit; nothing "
                                   "got published")
        self.assertNotEqual(mutant, text)
        self.assertNotEqual(arms_parity_problems(mutant, "commit"), [])

    def test_mutant_preflight_fence_removed(self):
        for which in ("step-b", "fallback"):
            with self.subTest(which=which):
                hits = [m.start() for m in re.finditer(
                    re.escape(PREFLIGHT_INVOCATION), self.step_b)]
                self.assertEqual(len(hits), 2)
                at = hits[0] if which == "step-b" else hits[1]
                fence = _fence_around(self.step_b, at)
                mutant = self.step_b.replace(fence, "```bash\n:\n", 1)
                self.assertNotEqual(mutant, self.step_b)
                self.assertNotEqual(preflight_fence_problems(mutant), [])

    def test_mutant_preflight_arm1_reruns(self):
        arm = rendered_arms("preflight")["1"]
        self.assertIn(arm, self.step_b)
        mutant = self.step_b.replace(
            arm, arm.replace("end Phase 5 for this pass", "go to the Rerun"))
        self.assertNotEqual(mutant, self.step_b)
        self.assertNotEqual(preflight_fence_problems(mutant), [])

    def test_mutant_subset_asks_again(self):
        mutant = self.card.replace(
            SUBSET_NO_CARD, SUBSET_NO_CARD + " Then call AskUserQuestion to "
            "confirm the rows.", 1)
        self.assertNotEqual(mutant, self.card)
        self.assertNotEqual(subset_no_card_problems(mutant), [])

    def test_mutant_card_budget_reverted(self):
        mutant = self.card.replace("; " + BUDGET_NO_CARD, "", 1)
        self.assertNotEqual(mutant, self.card)
        self.assertNotEqual(subset_no_card_problems(mutant), [])

    def test_mutant_record_mapping_drops_a_verdict(self):
        old = "3 → `applied-uncommitted`"
        self.assertEqual(self.step_b.count(old), 1)
        mutant = self.step_b.replace(old, "3 → `errored`")
        self.assertNotEqual(record_mapping_problems(mutant), [])

    def test_mutant_table_arm_changed_breaks_prose(self):
        # A table edit without re-copying the prose trips the lock too.
        rows = fixstage.EXIT_TABLE["undo"]
        changed = ((rows[0][0], rows[0][1], rows[0][2],
                    rows[0][3].replace("undone", "reverted")),) + rows[1:]
        with unittest.mock.patch.dict(fixstage.EXIT_TABLE, {"undo": changed}):
            self.assertNotEqual(
                arms_parity_problems(self.texts[FIX_LOOP], "undo"), [])
        self.assertEqual(arms_parity_problems(self.texts[FIX_LOOP], "undo"),
                         [])


class TestExit9BothConsumers(unittest.TestCase):
    """Exit 9 (publication uncertain) reaches agents/fix.md, the primary apply
    path, and 50-fix-loop.md's fallback alike: never `NOTHING is committed`,
    never retried automatically."""

    def setUp(self):
        with open(FIX_MD, encoding="utf-8") as fh:
            self.fix_text = fh.read()
        self.step_b = step_b_section(read_text())

    def drop_line(self, text, prefix):
        hits = [l for l in text.split("\n") if l.strip().startswith(prefix)]
        self.assertEqual(len(hits), 1, prefix)
        self.assertEqual(text.count(hits[0] + "\n"), 1)
        mutant = text.replace(hits[0] + "\n", "", 1)
        self.assertNotEqual(mutant, text)
        return mutant

    def test_fix_md_exit9_arm_and_bullet(self):
        self.assertEqual(fix_md_exit9_problems(self.fix_text), [])

    def test_fix_md_exit9_arm_mutant_trips(self):
        mutant = self.drop_line(self.fix_text, '9) echo "publication-uncertain')
        self.assertIn("fix.md commit case lacks a 9) arm",
                      fix_md_exit9_problems(mutant))
        self.assertIn("NOTHING is committed", run_commit_fence(mutant, 9))

    def test_fix_md_exit9_bullet_mutant_trips(self):
        mutant = self.drop_line(self.fix_text, "- **9** →")
        self.assertNotEqual(fix_md_exit9_problems(mutant), [])
        self.assertEqual(self.fix_text.count(FIX_MD_NO_REATTEMPT), 1)
        start = self.fix_text.index(FIX_MD_NO_REATTEMPT)
        end = self.fix_text.index("reconcile. ", start) + len("reconcile. ")
        sentence_gone = self.fix_text[:start] + self.fix_text[end:]
        self.assertNotEqual(sentence_gone, self.fix_text)
        self.assertNotEqual(fix_md_exit9_problems(sentence_gone), [])

    def test_exit9_parity(self):
        self.assertEqual(exit9_parity_problems(self.fix_text, self.step_b), [])

    def test_exit9_parity_mutant_trips(self):
        self.assertEqual(self.fix_text.count(EXIT9_NO_RETRY), 1)
        mutant = self.fix_text.replace(EXIT9_NO_RETRY, "retry later")
        self.assertNotEqual(mutant, self.fix_text)
        self.assertNotEqual(exit9_parity_problems(mutant, self.step_b), [])

    def assert_rc9_handled(self, text):
        out = run_commit_fence(text, 9)
        self.assertIn(FENCE_SHA, out)
        self.assertIn("publication-uncertain", out)
        self.assertNotIn("NOTHING is committed", out)

    def test_fix_md_commit_fence_rc9(self):
        self.assert_rc9_handled(self.fix_text)

    def test_fix_loop_commit_fence_rc9(self):
        self.assert_rc9_handled(self.step_b)

    def test_commit_fence_rc9_mutants_trip(self):
        for name, text in (("fix.md", self.fix_text),
                           ("50-fix-loop.md", self.step_b)):
            with self.subTest(file=name):
                mutant = self.drop_line(text, '9) echo "publication-uncertain')
                self.assertIn("NOTHING is committed",
                              run_commit_fence(mutant, 9))

    def test_commit_fence_rc8_sanity(self):
        # The harness really reaches the case: rc 8 selects the 8) arm.
        self.assertIn("published-unverified",
                      run_commit_fence(self.fix_text, 8))


class TestPhase58Prose(unittest.TestCase):
    """A clear typed answer is translated and acted on (ANSR-01), a carried
    close-out is read from Phase 0's printed line (D-17), the Bottom line is
    offered as grammar (D-09), Apply all's scope comes from the helper
    (RECV-01), stale residue is gone (D-14). Each check has a mutant."""

    def setUp(self):
        self.text = read_text()
        self.card = card_section(self.text)

    def swap(self, old, new, text=None):
        text = self.card if text is None else text
        self.assertIn(old, text)
        mutant = text.replace(old, new, 1)
        self.assertNotEqual(mutant, text)
        return mutant

    # translated Other path (D-01..D-04, I-13)
    def test_translate_path_holds(self):
        self.assertEqual(translate_path_problems(self.card), [])

    def test_mutant_translate_reshows_same_card(self):
        mutant = self.swap(TRANSLATE_GOTO, "On any other refusal "
                           + OLD_RESHOW + " once.")
        self.assertNotEqual(translate_path_problems(mutant), [])

    def test_mutant_translate_reads_titles(self):
        mutant = self.swap(OWNER_TEXT_RULE,
                           "from the owner's text and the finding titles")
        self.assertNotEqual(translate_path_problems(mutant), [])

    def test_mutant_translate_skips_parse(self):
        mutant = self.swap(SAME_PARSE, "use the grammar as parsed")
        self.assertNotEqual(translate_path_problems(mutant), [])

    # carried close-out (D-17)
    def test_close_out_carry_holds(self):
        self.assertEqual(close_out_carry_problems(self.text), [])

    def test_mutant_close_out_carry_new_findings_show_card(self):
        mutant = self.swap("even when the rerun reported new findings",
                           "unless the rerun reported new findings",
                           self.text)
        self.assertNotEqual(close_out_carry_problems(mutant), [])

    def test_mutant_close_out_carry_reads_tmp_file(self):
        mutant = self.swap(CARRY_LINE, "`close_out` true in `$RESOLVEFILE`",
                           self.text)
        self.assertNotEqual(close_out_carry_problems(mutant), [])

    # Bottom line as a choice (D-09)
    def test_bottom_line_holds(self):
        self.assertEqual(bottom_line_problems(self.card), [])
        self.assertEqual(nudge_count(self.text), 0)

    def test_mutant_bottom_line_guessed(self):
        mutant = self.swap("never print a guessed one",
                           "print your best guess")
        self.assertNotEqual(bottom_line_problems(mutant), [])

    def test_mutant_bottom_line_recommended(self):
        slot = BOTTOM_LINE_SLOT
        mutant = self.swap(slot, slot.replace(
            "to take it}}", "to take it (Recommended)}}"))
        self.assertGreater(nudge_count(mutant), 0)
        self.assertNotEqual(bottom_line_problems(mutant), [])

    # Apply all names the excluded NV rows from the helper (D-10..D-12)
    def test_nv_bulk_fix_holds(self):
        self.assertEqual(nv_card_problems(self.card), [])
        self.assertEqual(self.text.count(BULK_FIX_SLOT), 1)

    def test_mutant_nv_hand_written_note(self):
        mutant = self.swap(BULK_FIX_SLOT, "every listed row. "
                           + NV_APPLY_ALL_NOTE)
        self.assertNotEqual(nv_card_problems(mutant), [])

    # residue (I-10)
    def test_residue_holds(self):
        self.assertEqual(list_in_card_problems(self.card), [])

    def test_mutant_residue_finalize_echo(self):
        question = question_line(self.card)
        mutant = self.swap(question, question.replace(
            "{{card_text}}", "{{card_text}}{{\\n\\nFrom your finalize "
            "answer:\\n<echo_text>}}", 1))
        self.assertNotEqual(list_in_card_problems(mutant), [])

    # decision hold matches Phase 57 (I-12)
    def test_decision_hold_holds(self):
        self.assertEqual(decision_hold_problems(self.card), [])

    def test_mutant_decision_hold_restored(self):
        start = self.card.index(HOLD_NEEDLES[0])
        end = self.card.index(HOLD_NEEDLES[-1], start) + len(HOLD_NEEDLES[-1])
        if self.card[end:end + 1] == ".":
            end += 1
        mutant = self.swap(self.card[start:end], OLD_HOLD)
        self.assertNotEqual(decision_hold_problems(mutant), [])

    # card budget (D-14, Pitfall 4)
    def test_budget_holds(self):
        self.assertEqual(budget_problems(self.text), [])
        self.assertEqual(self.text.count("A pass costs one card"), 1)

    def test_mutant_budget_unparseable_reshows(self):
        mutant = self.swap(
            "at the owner's request.", "at the owner's request (an "
            "unparseable answer … re-shows the same card once).", self.text)
        self.assertNotEqual(budget_problems(mutant), [])

    # bug C (ANSR-03): the subset bullet is the only rule
    def test_mutant_subset_a_no_ask_clause_deleted(self):
        clause = (" — ask NO AskUserQuestion: the owner already chose these "
                  "rows at Finalize (D-06)")
        mutant = self.swap(clause, "")
        self.assertNotEqual(subset_no_card_problems(mutant), [])

    def test_mutant_subset_b_asks_apply_skip(self):
        clause = (" — ask NO AskUserQuestion: the owner already chose these "
                  "rows at Finalize (D-06)")
        mutant = self.swap(clause, " then ask one AskUserQuestion (Apply / "
                           "Skip) before Step B")
        self.assertNotEqual(subset_no_card_problems(mutant), [])

    def test_mutant_subset_off_bullet_instruction(self):
        mutant = self.swap("**Same-turn rule",
                           MUTANT_C + "\n\n**Same-turn rule")
        self.assertNotEqual(subset_no_card_problems(mutant), [])


# --- Phase 58 routing: ask only the gap, stale re-map, close-out carrier ---

ASK_HEADING = "**Ask only what is missing (D-05, D-06).**"
ASK_NEEDLES = ("Hold the whole answer and record nothing",
               "never half-apply",
               "ONE short AskUserQuestion",
               "only the unclear piece",
               "`#n file:line`",
               "re-run the resolve fence",
               "the whole answer together",
               "one follow-up per gap",
               "show the full card once",
               "could not be matched",
               "then stop asking")
FOLLOWUP_HEADERS = ('header "Which row"', 'header "Which rows"',
                    'header "Reason"', 'header "How many"')
STALE_HEADING = "**Stale card (D-07).**"
RESOLVE_PRIOR_CALL = ('resolve --rows "$ROWSFILE" --answer "$REFSFILE" '
                      '--prior-rows "$PRIORROWSFILE"')
STALE_NEEDLES = ("`prior_number`", "by finding identity",
                 "shows the new numbers",
                 " (your numbers re-mapped to the current card)",
                 "is asked about alone")
STEP2_START = "2. `fix_targets` non-empty"
STEP3_START = "3. `fix_targets` empty"
STEP2_NEEDLES = ("then the Rerun", "`close_out`", "**Close out**",
                 "`--close-out-after-rerun`", "Step B committed nothing",
                 "`close_out` is true", "go to **Close out** directly")
STEP3_NEEDLE = "**Close out** directly when `close_out` is true"
RERUN_HEADING = "**The Rerun.**"
MARKER_REENTRY = '$ARGUMENTS = "${original_args} --close-out-after-rerun"'
PLAIN_REENTRY = '$ARGUMENTS = "${original_args}"'
MARKER_GUARD = "when the answer that started this Rerun carried close out"
RERUN_NEEDLES = (PLAIN_REENTRY, MARKER_GUARD, "`close_out` true",
                 MARKER_REENTRY, "never carried into a second Rerun")
SUBSET_CLEAR = 'rm -f "$SUBSETFILE"; unset SUBSETFILE'
OLD_SAME_ARGS = "with the SAME `$ARGUMENTS`"
ORIGINAL_ARGS_DEF = ("`${original_args}` is this pass's `$ARGUMENTS` minus "
                     "every whole-token `--finalize` and "
                     "`--close-out-after-rerun`")
CLOSE_OUT_BULLET = "> 1. **Close out** —"
TYPED_BOTTOM_LINE_NEEDLES = ('"bottom line"', '"do what it says"',
                             "printed on the card currently shown",
                             'cp "$SUGGESTFILE" "$ANSWERFILE"',
                             "same gate, same bulk rules; D-09",
                             "any other plain-English answer")
_MARKER_REENTRY_RE = re.compile(
    r'\$ARGUMENTS = "(\$\{original_args\} --close-out[^"]*)"')
_CLOSE_OUT_REENTRY_RE = re.compile(
    r'\$ARGUMENTS = "(\$\{original_args\} --finalize[^"]*)"')
_PRIOR_RUN_ON = ("49-foo --close-out-after-rerun --finalize")
# The Rerun's own re-entry with the marker on: the $ARGUMENTS of the pass
# whose card then answers Close out.
_PRIOR_RERUN = "49-foo --close-out-after-rerun"
MARKER_STRIP_CLAUSE = ("s/ --close-out-after-rerun"
                       "( --close-out-after-rerun)* / /g")


def ask_paragraph(card):
    """The **Ask only what is missing** paragraph, up to the next bold
    paragraph inside the Other bullet or the Stop here… route."""
    start = card.index(ASK_HEADING)
    ends = [e for e in (card.find("\n\n  **", start + 1),
                        card.find(STOP_ROUTE, start)) if e >= 0]
    return card[start:min(ends) if ends else len(card)]


def followup_problems(card):
    """[] when an unclear piece holds the whole answer, asks one small
    question about only that piece, and falls back to the full card once."""
    if NV_TYPED_BRANCH not in card or STOP_ROUTE not in card:
        return ["Other path or Stop here… route missing"]
    if ASK_HEADING not in other_path(card):
        return ["no Ask only what is missing paragraph in the Other path"]
    para = ask_paragraph(card)
    problems = ["follow-up lacks: " + n for n in ASK_NEEDLES if n not in para]
    problems += ["follow-up lacks reason choice: " + lab
                 for lab in batch_parse.FINALIZE_Q2
                 if "`%s`" % lab not in para]
    for literal in FOLLOWUP_HEADERS:
        if literal not in para:
            problems.append("follow-up lacks " + literal)
        elif len(header_value(literal)) > MAX_HEADER_CHARS:
            problems.append("header too long: " + literal)
    if para.count("never half-apply") != 1 or \
            card.count("never half-apply") != 1:
        problems.append("never half-apply is not stated exactly once")
    return problems


def stale_card_problems(card):
    """[] when numbers from an older card are re-mapped by identity through
    the `--prior-rows` twin fence and the echo shows the new numbers."""
    if TRANSLATE_HEADING not in card or STALE_HEADING not in card:
        return ["no Stale card paragraph"]
    other = other_path(card)
    if STALE_HEADING not in other:
        return ["Stale card paragraph is outside the Other path"]
    start = other.index(STALE_HEADING)
    if start < other.index(TRANSLATE_HEADING):
        return ["Stale card paragraph precedes Translate the answer"]
    # the paragraph runs through its fence and the sentence after it
    end = other.find("\n\n  ", other.find("```\n", other.find(
        "```bash", start) + 1) + 1)
    para = other[start:end if end >= 0 else len(other)]
    problems = ["stale paragraph lacks: " + n for n in STALE_NEEDLES
                if n not in para]
    if RESOLVE_PRIOR_CALL not in para:
        return problems + ["stale paragraph lacks the --prior-rows twin"]
    call = para.index(RESOLVE_PRIOR_CALL)
    fence = para.rfind("```bash", 0, call)
    if fence < 0 or "```" in para[fence + len("```bash"):call]:
        problems.append("--prior-rows call is not inside a bash fence")
    return problems


def close_out_routing_problems(card):
    """[] when steps 2 and 3 route a translated close-out (D-17): via the
    Rerun's marker after a commit, else straight to Close out."""
    other = other_path(card)
    if STEP2_START not in other or STEP3_START not in other:
        return ["steps 2/3 missing"]
    a = other.index(STEP2_START)
    b = other.index(STEP3_START, a)
    step2 = other[a:b]
    step3 = other[b:other.index("\n", b)]
    problems = ["step 2 lacks: " + n for n in STEP2_NEEDLES
                if n not in step2]
    if STEP3_NEEDLE not in step3:
        problems.append("step 3 lacks: " + STEP3_NEEDLE)
    return problems


def rerun_paragraph(card):
    start = card.index(RERUN_HEADING)
    return card[start:card.index("\n\n", start)]


def rerun_marker_problems(card):
    """[] when the Rerun appends the close-out marker only for an answer
    that carried close out, and every other Rerun re-enters plain."""
    if RERUN_HEADING not in card:
        return ["no Rerun paragraph"]
    para = rerun_paragraph(card)
    problems = ["Rerun lacks: " + n for n in RERUN_NEEDLES if n not in para]
    if RERUN_POINTER not in para:
        problems.append("Rerun lacks the empty-diff pointer")
    if SUBSET_CLEAR not in para or "loop back to Phase 0" not in para or \
            para.index(SUBSET_CLEAR) > para.index("loop back to Phase 0"):
        problems.append("subset is not cleared before looping back")
    if MARKER_GUARD in para and MARKER_REENTRY in para and \
            para.index(MARKER_GUARD) > para.index(MARKER_REENTRY):
        problems.append("marker re-entry is not guarded by close out")
    if OLD_SAME_ARGS in para:
        problems.append("Rerun still re-enters with the SAME $ARGUMENTS")
    if card.count("${original_args} --close-out-after-rerun") != 1:
        problems.append("marker re-entry appears %d times" % card.count(
            "${original_args} --close-out-after-rerun"))
    return problems


def close_out_bullet(card):
    start = card.index(CLOSE_OUT_BULLET)
    return card[start:card.index("\n", start)]


def original_args_problems(card):
    """[] when `${original_args}` is defined once, in Close out, as
    stripping both --finalize and the close-out marker."""
    problems = []
    if card.count(ORIGINAL_ARGS_DEF) != 1:
        problems.append("definition x%d" % card.count(ORIGINAL_ARGS_DEF))
    if CLOSE_OUT_BULLET not in card or RERUN_HEADING not in card:
        return problems + ["Close out bullet or Rerun missing"]
    bullet = close_out_bullet(card)
    if REENTRY not in bullet:
        problems.append("Close out lacks " + REENTRY)
    if ORIGINAL_ARGS_DEF not in bullet:
        problems.append("definition is not in the Close out bullet")
    if "${original_args}" not in rerun_paragraph(card):
        problems.append("Rerun does not use ${original_args}")
    return problems


def typed_opening(card):
    """The Typed-answer bullet up to its parse fence."""
    start = card.index(NV_TYPED_BRANCH)
    return card[start:card.index("```bash", start)]


def typed_bottom_line_problems(card):
    """[] when typing "bottom line" copies the parser-checked suggestion
    file-to-file into the answer and runs the same parse fence (D-09)."""
    if NV_TYPED_BRANCH not in card:
        return ["no Typed answer bullet"]
    opening = typed_opening(card)
    return ["typed opening lacks: " + n for n in TYPED_BOTTOM_LINE_NEEDLES
            if n not in opening]


def marker_reentry(card):
    """The Rerun's marker re-entry string, read from the prose (or None)."""
    if RERUN_HEADING not in card:
        return None
    hits = _MARKER_REENTRY_RE.findall(rerun_paragraph(card))
    return hits[0] if len(hits) == 1 else None


def close_out_reentry(card):
    if CLOSE_OUT_BULLET not in card:
        return None
    hits = _CLOSE_OUT_REENTRY_RE.findall(close_out_bullet(card))
    return hits[0] if len(hits) == 1 else None


class TestPhase58Routing(unittest.TestCase):
    """Ask only the gap, once (D-05, D-06, D-08); stale cards re-map by
    identity (D-07); close out rides the Rerun as a one-shot marker (D-17);
    typed "bottom line" takes the suggestion (D-09). Each has a mutant."""

    def setUp(self):
        self.text = read_text()
        self.card = card_section(self.text)

    def swap(self, old, new, text=None):
        text = self.card if text is None else text
        self.assertIn(old, text)
        mutant = text.replace(old, new, 1)
        self.assertNotEqual(mutant, text)
        return mutant

    def test_followup_holds(self):
        self.assertEqual(followup_problems(self.card), [])

    def test_mutant_followup_records_partial(self):
        mutant = self.swap("Hold the whole answer and record nothing",
                           "Record the parts that resolved")
        self.assertNotEqual(followup_problems(mutant), [])

    def test_stale_card_holds(self):
        self.assertEqual(stale_card_problems(self.card), [])
        self.assertEqual(self.text.count(RESOLVE_CALL), 2)

    def test_mutant_stale_without_prior_rows(self):
        mutant = self.swap(' --prior-rows "$PRIORROWSFILE"', "")
        self.assertNotEqual(stale_card_problems(mutant), [])

    def test_close_out_routing_holds(self):
        self.assertEqual(close_out_routing_problems(self.card), [])

    def test_mutant_close_out_routing_step3_reruns(self):
        mutant = self.swap(", or " + STEP3_NEEDLE, "")
        self.assertNotEqual(close_out_routing_problems(mutant), [])

    def test_rerun_marker_holds(self):
        self.assertEqual(rerun_marker_problems(self.card), [])

    def test_mutant_marker_not_appended(self):
        para = rerun_paragraph(self.card)
        a = para.index(" — or, " + MARKER_GUARD)
        b = para.index(MARKER_REENTRY) + len(MARKER_REENTRY)
        mutant = self.swap(para[a:b], "")
        self.assertNotEqual(rerun_marker_problems(mutant), [])
        self.assertIsNone(marker_reentry(mutant))

    def test_original_args_holds(self):
        self.assertEqual(original_args_problems(self.card), [])

    def test_mutant_marker_carried(self):
        mutant = self.swap(ORIGINAL_ARGS_DEF, ORIGINAL_ARGS_DEF.replace(
            " and `--close-out-after-rerun`", ""))
        self.assertNotEqual(original_args_problems(mutant), [])

    def test_typed_bottom_line_holds(self):
        self.assertEqual(typed_bottom_line_problems(self.card), [])

    def test_mutant_typed_bottom_line_no_copy(self):
        mutant = self.swap('cp "$SUGGESTFILE" "$ANSWERFILE"',
                           "write the suggestion to `$ANSWERFILE`")
        self.assertNotEqual(typed_bottom_line_problems(mutant), [])


class TestCarrierRoundTrip(unittest.TestCase):
    """The exact re-entry strings the fix-loop prose carries, run through
    the REAL 00-scope.md normalizer fence: the Rerun's marker is read back
    once, and Close out's re-entry drops it."""

    @classmethod
    def setUpClass(cls):
        cls.card = card_section(read_text())
        cls.block = normalizer_block(read_scope(SCOPE))

    def test_rerun_marker_is_read_back(self):
        carried = marker_reentry(self.card)
        self.assertIsNotNone(carried, "no marker re-entry found")
        args = carried.replace("${original_args}", "49-foo")
        for shell in SHELLS:
            with self.subTest(shell=shell):
                self.assertEqual(carrier_flag(self.block, args, shell), "1")
                self.assertEqual(finalize_mode(self.block, args, shell), "0")
                self.assertEqual(scope_args(self.block, args, shell),
                                 "49-foo")

    def test_close_out_drops_the_marker(self):
        # The pass that reaches Close out was entered by the Rerun with the
        # marker on. ${original_args} is that pass's $ARGUMENTS minus the
        # whole-token flags, i.e. what the real normalizer derives, so build
        # it through the fence rather than typing the clean value in.
        reentry = close_out_reentry(self.card)
        self.assertIsNotNone(reentry, "no Close out re-entry found")
        self.assertEqual(reentry, REENTRY)
        for shell in SHELLS:
            with self.subTest(shell=shell):
                original_args = scope_args(self.block, _PRIOR_RERUN, shell)
                self.assertEqual(original_args, "49-foo")
                args = reentry.replace("${original_args}", original_args)
                self.assertEqual(carrier_flag(self.block, args, shell), "0")
                self.assertEqual(finalize_mode(self.block, args, shell), "1")
                self.assertEqual(scope_args(self.block, args, shell),
                                 "49-foo")

    def test_mutant_strip_removed_marker_would_carry(self):
        # Without the normalizer's marker strip, ${original_args} keeps the
        # marker and Close out's re-entry would carry it into Finalize.
        clause = MARKER_STRIP_CLAUSE + "; "
        self.assertIn(clause, self.block)
        mutated = self.block.replace(clause, "")
        self.assertNotEqual(mutated, self.block)
        reentry = close_out_reentry(self.card)
        self.assertIsNotNone(reentry, "no Close out re-entry found")
        for shell in SHELLS:
            with self.subTest(shell=shell):
                original_args = scope_args(mutated, _PRIOR_RERUN, shell)
                self.assertIn("--close-out-after-rerun", original_args)
                args = reentry.replace("${original_args}", original_args)
                self.assertNotEqual(carrier_flag(mutated, args, shell), "0")

    def test_non_stripping_original_args_would_carry(self):
        # What Close out would send if ${original_args} kept the marker:
        # the definition sentence is what keeps this from happening.
        for shell in SHELLS:
            with self.subTest(shell=shell):
                self.assertEqual(
                    carrier_flag(self.block, _PRIOR_RUN_ON, shell), "1")


# --- Temp-file lifecycle in the fix-loop spine (WR-01, WR-02, WR-05, WR-06,
# IN-05): every temp path is printed and reused as a literal, the answer
# files are cleared at every exit, a close-out is read only from this step's
# resolve output, the stale re-map has a reachable source, and Finalize's
# echo is printed once. ---

MKTEMP_RE = re.compile(r"^\s*(?:if )?([A-Z_]+FILE)=\$\(mktemp", re.M)
PATH_CONVENTION = ("a path printed after `NAME=` is reused in a later fence "
                   "only as that literal, substituted for `\"$NAME\"`")
ANSWER_FILES_CLEAR = 'rm -f "$SUGGESTFILE" "$REFSFILE" "$RESOLVEFILE"'
SUGGEST_OLD = "`$SUGGESTFILE` exists for this pass"
SUGGEST_SHOWN = "printed on the card currently shown"
SUGGEST_THIS_PASS = "created on this pass"
CARRY_OLD = "none of which survive it"
CARRY_NEW = "the Rerun removes the answer files it consumed"
CLOSE_OUT_SOURCE = ("came from the `ok` true branch of **Translate the "
                    "answer** and the resolve output printed in this step "
                    "had `close_out` true")
NEVER_STALE = ("a `close_out` found in a file written for an earlier answer "
               "is never read")
RERUN_OLD_SOURCE = "`close_out` true in `$RESOLVEFILE`"
STEP2_OLD = "was true in `$RESOLVEFILE`"
STEP2_NEW = "the resolve output acted on in this step had `close_out` true"
STALE_SOURCE_NEEDLES = (
    "the literal path the previous pass's rows fence printed after "
    "`ROWSFILE=`",
    "the Rerun keeps that file",
    "substituted for `\"$PRIORROWSFILE\"`",
    "no longer available")
STALE_SOURCE_OLD = "that pass's `$ROWSFILE` path, used as is"
KEEP_ROWS = "keep this pass's `$ROWSFILE`"
SINGLE_ECHO = ("Finalize already printed its `echo_text` before reading this "
               "file — do not print it again")
ECHO_OLD = "Then print Finalize's `echo_text`"
FULL_CARD_ONCE = "show the full card once"


def bash_fences(text):
    """Bodies of every ```bash fence in `text`."""
    return re.findall(r"```bash\n(.*?)```", text, re.S)


def printed_paths_problems(text):
    """[] when every `NAME=$(mktemp …)` in the file prints its path in the
    same fence, and the card says once that a printed path is reused only
    as that literal (WR-06, WR-05)."""
    problems = []
    for body in bash_fences(text):
        for name in MKTEMP_RE.findall(body):
            printf = "printf '%s=%%s\\n' \"$%s\"" % (name, name)
            if printf not in body:
                problems.append("unprinted temp path: " + name)
    count = card_section(text).count(PATH_CONVENTION)
    if count != 1:
        problems.append("path convention sentence appears %d times" % count)
    return problems


def _cleared_before(chunk, anchor, where):
    i, j = chunk.find(ANSWER_FILES_CLEAR), chunk.find(anchor)
    if j < 0:
        return ["%s: anchor %r missing" % (where, anchor)]
    if i < 0 or i > j:
        return ["%s: answer files not cleared before %r" % (where, anchor)]
    return []


def answer_files_problems(card):
    """[] when the suggestion/refs/resolve files are removed at the Rerun,
    at Close out and at the D-08 fallback, and a Bottom line suggestion
    counts only when printed on the card currently shown (WR-01, WR-02)."""
    problems = []
    if RERUN_HEADING not in card or CLOSE_OUT_BULLET not in card or \
            ASK_HEADING not in card or CLOSE_OUT_CARRY not in card:
        return ["Rerun, Close out, Ask or carry paragraph missing"]
    problems += _cleared_before(rerun_paragraph(card), "loop back to Phase 0",
                                "Rerun")
    if ANSWER_FILES_CLEAR not in close_out_bullet(card):
        problems.append("Close out: answer files not cleared")
    problems += _cleared_before(ask_paragraph(card), FULL_CARD_ONCE,
                                "D-08 fallback")
    if SUGGEST_OLD in card:
        problems.append("suggestion still read from a file that may be stale")
    if SUGGEST_SHOWN not in typed_opening(card):
        problems.append("typed bottom line not tied to the card shown")
    if SUGGEST_THIS_PASS not in question_line(card):
        problems.append("question note not tied to this pass's suggestion")
    start = card.index(CLOSE_OUT_CARRY)
    carry = card[start:card.index("\n\n", start)]
    if CARRY_OLD in carry:
        problems.append("carry paragraph still says the files do not survive")
    if CARRY_NEW not in carry:
        problems.append("carry paragraph lacks: " + CARRY_NEW)
    return problems


def close_out_source_problems(card):
    """[] when the Rerun's close-out marker and step 2's close-out route are
    bound to the resolve output acted on in THIS step, never to a file left
    by an earlier answer (WR-01)."""
    problems = []
    if RERUN_HEADING not in card:
        return ["no Rerun paragraph"]
    para = rerun_paragraph(card)
    for needle in (CLOSE_OUT_SOURCE, NEVER_STALE):
        if needle not in para:
            problems.append("Rerun lacks: " + needle)
    if RERUN_OLD_SOURCE in para:
        problems.append("Rerun still reads close_out from $RESOLVEFILE")
    other = other_path(card)
    if STEP2_START not in other or STEP3_START not in other:
        return problems + ["steps 2/3 missing"]
    step2 = other[other.index(STEP2_START):other.index(STEP3_START)]
    if STEP2_OLD in step2:
        problems.append("step 2 still reads close_out from $RESOLVEFILE")
    if STEP2_NEW not in step2:
        problems.append("step 2 lacks: " + STEP2_NEW)
    return problems


def stale_source_problems(card):
    """[] when a stale card's prior rows come from the literal path the
    previous pass printed after `ROWSFILE=`, which the Rerun keeps, with a
    fallback when no such path exists (WR-05)."""
    if STALE_HEADING not in card or RERUN_HEADING not in card:
        return ["no Stale card paragraph or Rerun"]
    start = card.index(STALE_HEADING)
    para = card[start:card.index("```bash", start)]
    problems = ["stale source lacks: " + n for n in STALE_SOURCE_NEEDLES
                if n not in para]
    if STALE_SOURCE_OLD in para:
        problems.append("stale source still names " + STALE_SOURCE_OLD)
    if KEEP_ROWS not in rerun_paragraph(card):
        problems.append("Rerun lacks: " + KEEP_ROWS)
    return problems


def single_echo_problems(card):
    """[] when a Finalize-routed subset does not print Finalize's
    `echo_text` a second time (IN-05)."""
    if SUBSET_BULLET not in card or ORDINARY_BULLET not in card:
        return ["subset or ordinary bullet missing"]
    bullet = card[card.index(SUBSET_BULLET):card.index(ORDINARY_BULLET)]
    problems = []
    if SINGLE_ECHO not in bullet:
        problems.append("subset bullet lacks: " + SINGLE_ECHO)
    if ECHO_OLD in card:
        problems.append("card still prints Finalize's echo_text again")
    return problems


class TestGapRoundFixLoop(unittest.TestCase):
    """The fix-loop spine's temp files: printed paths, answer-file
    lifecycle, close-out source, stale source, single echo. Each lock has
    mutants that restore the reviewed defect."""

    def setUp(self):
        self.text = read_text()
        self.card = card_section(self.text)

    def swap(self, old, new, text=None):
        text = self.card if text is None else text
        self.assertIn(old, text)
        mutant = text.replace(old, new, 1)
        self.assertNotEqual(mutant, text)
        return mutant

    def test_printed_paths_holds(self):
        self.assertEqual(printed_paths_problems(self.text), [])

    def test_mutant_printed_paths(self):
        for name in ("ROWSFILE", "ANSWERFILE", "PARSEFILE", "DECFILE",
                     "SUBSETFILE", "SUGGESTFILE", "REFSFILE", "RESOLVEFILE",
                     "PAYLOADFILE"):
            with self.subTest(drop=name):
                line = "printf '%s=%%s\\n' \"$%s\"\n" % (name, name)
                self.assertIn(line, self.text)
                at = self.text.index(line)
                bol = self.text.rindex("\n", 0, at) + 1
                mutant = self.text[:bol] + self.text[at + len(line):]
                self.assertNotEqual(printed_paths_problems(mutant), [])
        with self.subTest(drop="convention"):
            mutant = self.swap(PATH_CONVENTION, "a path is reused",
                               self.text)
            self.assertNotEqual(printed_paths_problems(mutant), [])

    def test_answer_files_holds(self):
        self.assertEqual(answer_files_problems(self.card), [])

    def test_mutant_answer_files(self):
        rerun = rerun_paragraph(self.card)
        ask = ask_paragraph(self.card)
        bullet = close_out_bullet(self.card)
        cases = {
            "rerun keeps files": (rerun, rerun.replace(
                ANSWER_FILES_CLEAR, ":", 1)),
            "close out keeps files": (bullet, bullet.replace(
                ANSWER_FILES_CLEAR, ":", 1)),
            "fallback keeps files": (ask, ask.replace(
                ANSWER_FILES_CLEAR, ":", 1)),
            "carry: none survive": (CARRY_NEW, CARRY_OLD),
            "typed: file exists": (SUGGEST_SHOWN, SUGGEST_OLD),
            "question: file exists": (
                "the suggestion fence below printed a `SUGGESTFILE=` path "
                "created on this pass", SUGGEST_OLD),
        }
        for label, (old, new) in cases.items():
            with self.subTest(label):
                mutant = self.swap(old, new)
                self.assertNotEqual(answer_files_problems(mutant), [])

    def test_close_out_source_holds(self):
        self.assertEqual(close_out_source_problems(self.card), [])

    def test_mutant_close_out_source(self):
        for label, (old, new) in {
                "rerun source": (CLOSE_OUT_SOURCE,
                                 "had `close_out` true in `$RESOLVEFILE`"),
                "never stale dropped": (NEVER_STALE, "it is read"),
                "step 2 reads the file": (STEP2_NEW,
                                          "`close_out` " + STEP2_OLD),
        }.items():
            with self.subTest(label):
                mutant = self.swap(old, new)
                self.assertNotEqual(close_out_source_problems(mutant), [])

    def test_stale_source_holds(self):
        self.assertEqual(stale_source_problems(self.card), [])

    def test_mutant_stale_source(self):
        for label, (old, new) in {
                "used as is": (STALE_SOURCE_NEEDLES[0], STALE_SOURCE_OLD),
                "no fallback": (STALE_SOURCE_NEEDLES[3], "gone"),
                "rerun deletes rows": (KEEP_ROWS, "remove `$ROWSFILE`"),
        }.items():
            with self.subTest(label):
                mutant = self.swap(old, new)
                self.assertNotEqual(stale_source_problems(mutant), [])

    def test_single_echo_holds(self):
        self.assertEqual(single_echo_problems(self.card), [])

    def test_mutant_single_echo(self):
        mutant = self.swap(SINGLE_ECHO + ". Write ",
                           "Then print Finalize's `echo_text` as message "
                           "text, write ")
        self.assertNotEqual(single_echo_problems(mutant), [])


# --- Translate / Ask / Bottom line against the helper's own rules ---------

TITLE_TEXT_NEW = '"text": "<the owner\'s words for that row, verbatim>"'
TITLE_TEXT_OLD = '"text": "<the owner\'s words>"}'
TITLE_RULE_NEEDLES = (TITLE_TEXT_NEW, "do not trim or clean them",
                      "whole words only", "ignoring filler",
                      "`port` never matches `import`",
                      "the Browse recovery issue")
_FILLER_LIST = re.compile(r"ignoring filler \(([^)]*)\)")

PARSE_REFUSAL_BULLET = ("every ref is `one` or `bulk`, `needs_reason` is "
                        "false and `parse_reason` is set")
PARSE_REFUSAL_AFTER = ("no piece to narrow", "full-card fallback",
                       "combined two bulk groups", "could not be checked")
BLOCKED_BULLET = "- A `blocked` ref is never asked about"

COUNT_NEEDED_HEAD = 'A `count_needed` ref → header "How many"'
COUNT_NEEDED_NEEDLES = (COUNT_NEEDED_HEAD,
                        "critical, warning or Needs-verification rows",
                        "dismissed or deferred only when you state how many "
                        "(D-18)",
                        "`candidates`", "`#n file:line`", "through Other",
                        '`"count": C`', "`number` refs")
COMPLETED_REFS = "Then write the completed refs"

SUGGEST_CALL = ('batch_card.py" suggest --rows "$ROWSFILE" --answer '
                '"$SUGGESTFILE" > "$SUGGESTFILE.tmp" && mv '
                '"$SUGGESTFILE.tmp" "$SUGGESTFILE"')
SUGGEST_ELSE = 'rm -f "$SUGGESTFILE" "$SUGGESTFILE.tmp"'
SUGGEST_SHOW = 'cat "$SUGGESTFILE"'
SUGGEST_SCOPE = ("`fix` for any row but `dismiss`/`defer` for MEDIUM rows "
                 "only (D-19)")
SUGGEST_OWN_WORDS = "still needs your own words"
PARSE_DRY_RUN = 'parse --rows "$ROWSFILE" --answer "$SUGGESTFILE"'


def translate_paragraph(card):
    """The **Translate the answer** paragraph, up to its first fence."""
    other = other_path(card)
    start = other.index(TRANSLATE_HEADING)
    return other[start:other.index("```bash", start)]


def title_rule_problems(card):
    """[] when Translate passes the owner's title words verbatim and states
    the helper's rule: whole words, filler ignored (WR-03)."""
    if TRANSLATE_HEADING not in card:
        return ["no Translate paragraph"]
    para = translate_paragraph(card)
    problems = ["Translate lacks: " + n for n in TITLE_RULE_NEEDLES
                if n not in para]
    if TITLE_TEXT_OLD in card:
        problems.append("the unqualified title text form is still present")
    m = _FILLER_LIST.search(para)
    if not m:
        problems.append("Translate lists no filler words")
    else:
        problems += ["filler word the helper does not ignore: " + w
                     for w in (w.strip() for w in m.group(1).split("/"))
                     if w not in batch_card._TITLE_FILLER]
    return problems


def ask_bullet(para, needle):
    """The whole line of `para` that holds `needle`."""
    at = para.index(needle)
    bol = para.rindex("\n", 0, at) + 1
    eol = para.find("\n", at)
    return para[bol:eol if eol >= 0 else len(para)]


def parse_refusal_branch_problems(card):
    """[] when an `ok` false result with every ref clear (the parser refused
    the built grammar) goes straight to the full-card fallback (WR-04)."""
    para = ask_paragraph(card)
    if PARSE_REFUSAL_BULLET not in para:
        return ["Ask paragraph lacks the parser-refusal bullet"]
    bullet = ask_bullet(para, PARSE_REFUSAL_BULLET)
    problems = []
    if not bullet.lstrip().startswith("- "):
        problems.append("the parser-refusal branch is not its own bullet")
    tail = bullet[bullet.index(PARSE_REFUSAL_BULLET):]
    problems += ["parser-refusal bullet lacks: " + n
                 for n in PARSE_REFUSAL_AFTER if n not in tail]
    if batch_parse.REASON_REST_TWICE.strip() not in bullet:
        problems.append("parser-refusal bullet does not name the "
                        "rest-twice refusal")
    if BLOCKED_BULLET not in para or \
            para.index(PARSE_REFUSAL_BULLET) > para.index(BLOCKED_BULLET):
        problems.append("parser-refusal bullet is not before the blocked "
                        "bullet")
    return problems


def count_needed_problems(card):
    """[] when an uncounted serious group is asked only its count (D-18)."""
    para = ask_paragraph(card)
    if COUNT_NEEDED_HEAD not in para:
        return ["Ask paragraph lacks the count_needed bullet"]
    bullet = ask_bullet(para, COUNT_NEEDED_HEAD)
    problems = ["count_needed bullet lacks: " + n
                for n in COUNT_NEEDED_NEEDLES if n not in bullet]
    if len(header_value('header "How many"')) > MAX_HEADER_CHARS:
        problems.append("How many header is too long")
    if COMPLETED_REFS not in para:
        return problems + ["no completed-refs sentence"]
    at = para.index(COMPLETED_REFS)
    sentence = para[at:para.index("re-run the resolve fence", at)]
    if "`count_needed`" not in sentence:
        problems.append("completed-refs sentence does not say how a "
                        "count_needed ref is completed")
    return problems


def bottom_line_paragraph(card):
    start = card.index(BOTTOM_LINE_HEAD)
    end = card.find("\n\n**", start)
    return card[start:end if end >= 0 else len(card)]


def suggest_fence_problems(card):
    """[] when the D-09 line comes from `batch_card.py suggest`, which keeps
    dismiss/defer for medium rows only (D-19), and no parse dry-run is left."""
    if BOTTOM_LINE_HEAD not in card:
        return ["no Bottom line paragraph"]
    para = bottom_line_paragraph(card)
    problems = []
    if card.count(SUGGEST_CALL) != 1 or SUGGEST_CALL not in para:
        problems.append("the D-09 paragraph lacks the suggest call once")
    else:
        call = para.index(SUGGEST_CALL)
        fence = para.rfind("```bash", 0, call)
        close = para.find("```", call)
        if fence < 0 or "```" in para[fence + len("```bash"):call] \
                or close < 0:
            problems.append("suggest call is not inside a bash fence")
        else:
            body = para[fence:close]
            if SUGGEST_SHOW not in body[:body.find("else")]:
                problems.append("suggest fence does not print the result")
            if "else" not in body or SUGGEST_ELSE not in \
                    body[body.index("else"):]:
                problems.append("suggest fence's else arm keeps a file")
    problems += ["Bottom line paragraph lacks: " + n
                 for n in (SUGGEST_SCOPE, SUGGEST_OWN_WORDS) if n not in para]
    if PARSE_DRY_RUN in card:
        problems.append("the parse dry-run of the suggestion is still there")
    return problems


class TestGapRoundTranslate(unittest.TestCase):
    """Translate, Ask and the Bottom line match the helper after the gap
    round: verbatim title words, the parser-refusal branch, the How many
    question, the suggest fence. Each lock has a mutant restoring the gap."""

    def setUp(self):
        self.card = card_section(read_text())

    def swap(self, old, new):
        self.assertIn(old, self.card)
        mutant = self.card.replace(old, new, 1)
        self.assertNotEqual(mutant, self.card)
        return mutant

    def drop_line(self, needle):
        self.assertIn(needle, self.card)
        line = ask_bullet(self.card, needle)
        return self.swap(line + "\n", "")

    def test_title_rule_holds(self):
        self.assertEqual(title_rule_problems(self.card), [])

    def test_mutant_title_rule(self):
        cases = {
            "old text form": (TITLE_TEXT_NEW + "}", TITLE_TEXT_OLD),
            "rule dropped": ("whole words only", "words"),
            "filler the helper keeps": ("filler (the / a", "filler (the / of"),
        }
        for label, (old, new) in cases.items():
            with self.subTest(label):
                self.assertNotEqual(
                    title_rule_problems(self.swap(old, new)), [])

    def test_parse_refusal_branch_holds(self):
        self.assertEqual(parse_refusal_branch_problems(self.card), [])

    def test_mutant_parse_refusal_branch(self):
        mutant = self.drop_line(PARSE_REFUSAL_BULLET)
        self.assertNotEqual(parse_refusal_branch_problems(mutant), [])

    def test_count_needed_holds(self):
        self.assertEqual(count_needed_problems(self.card), [])
        self.assertEqual(followup_problems(self.card), [])

    def test_mutant_count_needed(self):
        mutant = self.drop_line(COUNT_NEEDED_HEAD)
        self.assertNotEqual(count_needed_problems(mutant), [])
        self.assertNotEqual(followup_problems(mutant), [])

    def test_suggest_fence_holds(self):
        self.assertEqual(suggest_fence_problems(self.card), [])
        self.assertEqual(bottom_line_problems(self.card), [])

    def test_mutant_suggest_fence(self):
        cases = {
            "parse dry-run restored": (
                SUGGEST_CALL, 'batch_card.py" parse --rows "$ROWSFILE" '
                '--answer "$SUGGESTFILE" > /dev/null'),
            "else keeps the tmp file": (SUGGEST_ELSE, 'rm -f "$SUGGESTFILE"'),
            "scope sentence dropped": (SUGGEST_SCOPE, "any verb"),
        }
        for label, (old, new) in cases.items():
            with self.subTest(label):
                self.assertNotEqual(
                    suggest_fence_problems(self.swap(old, new)), [])
        mutant = self.swap(SUGGEST_CALL, 'batch_card.py" parse --rows '
                           '"$ROWSFILE" --answer "$SUGGESTFILE" > /dev/null')
        self.assertNotEqual(bottom_line_problems(mutant), [])


if __name__ == "__main__":
    unittest.main()
