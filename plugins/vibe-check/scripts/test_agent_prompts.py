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
  A two-pass run of the real scorer confirms that a capped note at severity
  low never reaches Warning, even when carried forward and corroborated.
* Safe-change recognition block. bugs, security and impact each carry the same
  block (identical after whitespace normalization) with all eighteen clauses;
  every cap it states is at most 45 and non-blocking for the lane's offset;
  every sentence stating the 45 cap also says `severity: low`; it never
  requires a repository occurrence ("in-repo").
* Location-keyed ceilings. No loud lane caps confidence on WHERE evidence sits
  (off-hunk / in-hunk) instead of whether it was verified; the security, bugs
  and impact anchors key on unverified or unread evidence.
* Codex focus literal. The text lives in templates/codex-focus.txt; the kickoff
  reads it with cat (skipping the launch on an empty read, never retyping it)
  and passes "$CODEX_FOCUS" on the exact ARGS line; the text carries every calibration token, states the exemption
  after the pre-existing-gap cap, has no shell metacharacters, and its 0.45
  ceilings are non-blocking at severity low. The contract documents it.
* Codex collection is file-owned. No prose file names a harness read tool
  (BashOutput, KillShell, shell_id); the private collection directory is
  created exactly once on the run branch, before the launch; the launch writes
  its exit status to rc LAST via temp file + rename (and the focus backstop
  writes its marker the same way); Phase 3 waits for rc under $TIMEOUT_BIN with
  the Bash tool timeout stated, maps rc through a strict case with no eval,
  reads the payload from the directory, and nothing removes the directory.
* Retired +10 prose. No file in agents/ or phases/deep-review/ describes a
  Claude-to-Claude, category-domain or multi-agent bonus; the places that name
  the +10 also name the joined condition.

Every scanner is a pure function over text. Each lock has a mutation test that
plants the regression in memory and asserts the scanner trips; no test writes a
file. A lock with no tripping mutation is decorative and does not count.
"""

import copy
import glob
import json
import os
import re
import sys
import unittest

# Make sibling imports resolve when unittest discovery runs from the root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import codex_gate  # noqa: E402  (the focus-unreadable slug and fact)
import replay  # noqa: E402  (REPO_ROOT convention)
import score  # noqa: E402  (read-only: driven, never edited)

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
    patterns = ("agents/*.md", "commands/*.md", "phases/**/*.md", "templates/*.md",
                "templates/*.txt")
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
    # The retired "N agents agree -> +10" wording (framework-fastapi.md's
    # severity calibration, framework-skill.md's score formula). Only a Codex
    # member beside a Claude lane while joined earns the bonus now.
    "cross-confirmed by",
    "if cross-confirmed",
    "when cross-confirmed",
    "(cross-confirmed)",
    "2+ agents",
    "2+ lanes",
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


def focus_text(file_text):
    """What `CODEX_FOCUS=$(cat <file>)` holds: the file with trailing newlines stripped."""
    return file_text.rstrip("\n")


_CAP = re.compile(
    r"agent_confidence\s*(?:≤|<=)\s*(\d+)|confidence at or below 0\.(\d\d)"
    r"|at or below 0\.(\d\d) confidence")


def caps_in(text):
    """Every confidence ceiling stated in `text`, as integer percent, in document order.

    Reads the Claude-lane form (`agent_confidence ≤ N`) and both Codex word
    orders ("confidence at or below 0.NN", "at or below 0.NN confidence").
    """
    return [int(m.group(1) or m.group(2) or m.group(3)) for m in _CAP.finditer(norm(text))]


def uncapped_moved_span(text, first_uncapped, capped_branch):
    """The LIVE text from the start of the moved-control not-found branch up to
    the start of the capped branch (whitespace-normalized): branches 1 and 2
    plus anything planted between them. Raises ValueError if either anchor is
    missing, so a reshaped carrier trips instead of silently passing."""
    hay = norm(text)
    start = hay.index(norm(first_uncapped))
    end = hay.index(norm(capped_branch), start)
    return hay[start:end]


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


# --------------------------------------------------------------------------- #
# Codex kickoff focus literal
# --------------------------------------------------------------------------- #
# Tokens the fixed CODEX_FOCUS literal must carry: the calibration framing, the
# safe-change rule, the 0.45 / severity-low ceiling, the loosening-is-a-defect
# rule, the pre-existing-gap cap and its exemption, and the two exceptions the
# loud lanes also carry (no repository-occurrence requirement; off-hunk is not
# unverified), and the three-branch moved-control rule keyed on what the
# reviewer FOUND: [16] a same-purpose replacement guards the same property;
# [17] none found — even when a comment asserts a move, or when the only code
# found guards a different property — leaves the removal rule uncapped; [19] a
# same-purpose replacement with a traced bypassing path is a demonstrated loss,
# uncapped; [20] a same-purpose replacement with unverified coverage leaves the
# capped note.
FOCUS_TOKENS = (
    "not a focus area",
    "tightens a control",
    "0.45",
    "removes, reverts, loosens, disables or bypasses",
    "pre-existing gap",
    "Every other axis is reviewed normally",
    "file:line",
    "Still report it",
    "input contract",
    "whether or not that value occurs in the repository",
    "Off-hunk is not the same as unverified",
    "a case the diff never addressed",
    "demonstrably fails to block",
    "severity low",
    "moved rather than lost",
    "judged by what you found, not by what the change claims",
    "A same-purpose replacement is code at file:line (shared middleware, a decorator, a "
    "schema or an upstream layer) that guards the same property as the removed check",
    "When you found and read no same-purpose replacement, including when only a comment, "
    "docstring or commit message asserts a move, or when the only code you found guards a "
    "different property (logging or rate-limiting middleware for a removed auth check), the "
    "removal rule applies at your honest confidence and the cap does not apply",
    "A move claim in the change text is never evidence of a replacement",
    "When you found and read a same-purpose replacement and can trace a formerly protected "
    "path that bypasses it, that is a demonstrated protection loss: report it at your honest "
    "confidence with no cap, because demonstrated loss always takes precedence over the cap",
    "When you found and read a same-purpose replacement whose coverage of every formerly "
    "protected path remains unverified, report the removal at or below 0.45 confidence with "
    "severity low and say to confirm that file:line covers every path the old check guarded",
)

# The exact ceilings the literal states, in order (pre-existing gap, moved-control
# capped note, sensitive-area note), and the exact count of "0.45". Pinning both
# means any added cap — however worded — trips, including a re-cap of the
# not-found or demonstrated-loss branch.
FOCUS_EXPECTED_CAPS = [45, 45, 45]
FOCUS_045_COUNT = 3

# The literal is single-quoted in bash: a quote would end it, `$` or a backtick
# would invite interpolation if it were ever re-quoted. "in-repo" would bring
# back the repository-occurrence requirement. "not a removal" would bring back
# the moved-control exemption that drops a claimed move without a trace.
# "not named, not read" / "the same note applies" would bring back the cap on a
# move no replacement was found for (a real removal filtered out of the report).
FOCUS_FORBIDDEN = ("$", "`", "'", "in-repo", "not a removal", "not named, not read",
                   "the same note applies")


def missing_focus_tokens(literal):
    """FOCUS_TOKENS absent from `literal`, in token order."""
    return [t for t in FOCUS_TOKENS if t not in (literal or "")]


# Tokens the literal must state at least twice: the ceiling appears once for the
# pre-existing gap and once for the sensitive-area note.
FOCUS_REPEATED = ("0.45", "severity low")


def focus_repeat_shortfalls(literal):
    """FOCUS_REPEATED tokens that occur fewer than twice in `literal`."""
    return [t for t in FOCUS_REPEATED if (literal or "").count(t) < 2]


def focus_forbidden_hits(literal):
    """FOCUS_FORBIDDEN substrings present in `literal`."""
    return [t for t in FOCUS_FORBIDDEN if t in (literal or "")]


FOCUS_FILE = "templates/codex-focus.txt"
FOCUS_READ_LINE = 'CODEX_FOCUS=$(cat "$VC_ROOT/templates/codex-focus.txt" 2>/dev/null)'
FOCUS_GUARD_LINE = ('if [ -z "$CODEX_FOCUS" ]; then echo __CODEX_FOCUS_MISSING__; '
                    'CODEX_ACTION=skip; fi')


def kickoff_reads_focus_file(kickoff_text):
    """The launch reads the focus text from FOCUS_FILE, skips on an empty read,
    and no inline CODEX_FOCUS='...' literal remains to be retyped."""
    lines = [ln.strip() for ln in kickoff_text.splitlines()]
    if FOCUS_READ_LINE not in lines or FOCUS_GUARD_LINE not in lines:
        return False
    if "CODEX_FOCUS='" in kickoff_text:
        return False
    read_at, guard_at = lines.index(FOCUS_READ_LINE), lines.index(FOCUS_GUARD_LINE)
    args = [i for i, ln in enumerate(lines)
            if ln == 'ARGS=(adversarial-review --json <codex_args> "$CODEX_FOCUS")']
    return bool(args) and read_at < guard_at < args[0]


FOCUS_FACT_LINE = ('FOCUS_OK=false; if [ -n "$(cat "$VC_ROOT/templates/codex-focus.txt" '
                   '2>/dev/null)" ]; then FOCUS_OK=true; fi')
FOCUS_FACT_ARG = 'focus_readable "$FOCUS_OK"'
FOCUS_SLUG = "focus-unreadable"
RUN_BRANCH_LINE = 'if [ "$CODEX_ACTION" = run ] && [ -n "$TIMEOUT_BIN" ]; then'
MKTEMP_LINE = "CODEX_DIR=$(mktemp -d)"
OLD_MKTEMP_LINE = "CODEX_OUT=$(mktemp)"
RUN_DECISION_TOKEN = '`action: "run"`'
ARGS_LINE_TEXT = 'ARGS=(adversarial-review --json <codex_args> "$CODEX_FOCUS")'
DISCLOSURE_HEAD = "2. **Disclosure line"


def kickoff_gates_focus(kickoff_text):
    """Readability of the focus file is a step-1 gate fact decided BEFORE the
    disclosure line, the skip is labeled with the gate's slug, and the private
    collection directory is created exactly once, after the run-branch decision
    text and before the launch's ARGS line (a skip leaves no temp directory)."""
    lines = [ln.strip() for ln in kickoff_text.splitlines()]
    if FOCUS_FACT_LINE not in lines or FOCUS_FACT_ARG not in kickoff_text:
        return False
    if FOCUS_SLUG not in kickoff_text:
        return False
    disclosure = [i for i, ln in enumerate(lines) if ln.startswith(DISCLOSURE_HEAD)]
    if not disclosure or lines.index(FOCUS_FACT_LINE) > disclosure[0]:
        return False
    mktemps = [i for i, ln in enumerate(lines) if ln == MKTEMP_LINE]
    if len(mktemps) != 1 or RUN_BRANCH_LINE not in lines or ARGS_LINE_TEXT not in lines:
        return False
    if OLD_MKTEMP_LINE in lines:
        return False
    decision = [i for i, ln in enumerate(lines) if RUN_DECISION_TOKEN in ln]
    if not decision:
        return False
    return decision[0] < mktemps[0] < lines.index(ARGS_LINE_TEXT)


HARNESS_READ_TOOLS = ("BashOutput", "KillShell", "shell_id")


def harness_read_tool_hits(corpus):
    """(relpath, token) for every harness read-tool name in the prose corpus."""
    return sorted((rel, tok) for rel, text in corpus.items()
                  for tok in HARNESS_READ_TOOLS if tok in text)


RC_ATOMIC_LINE = ('''printf '%s\\n' "$rc" > "$CODEX_DIR/rc.tmp" && '''
                  '''mv "$CODEX_DIR/rc.tmp" "$CODEX_DIR/rc"''')
FOCUS_MARKER_LINE = ('''if [ "$CODEX_ACTION" = skip ] && [ -n "$CODEX_DIR" ]; then '''
                     '''printf 'focus-missing\\n' > "$CODEX_DIR/rc.tmp" && '''
                     '''mv "$CODEX_DIR/rc.tmp" "$CODEX_DIR/rc"; fi''')


def kickoff_rc_is_atomic(kickoff_text):
    """Inside the run branch, rc is written by temp file + rename after rc=$?,
    and the focus backstop marker is written the same way right after the guard.
    No line writes rc directly."""
    lines = [ln.strip() for ln in kickoff_text.splitlines()]
    if RUN_BRANCH_LINE not in lines or FOCUS_GUARD_LINE not in lines:
        return False
    if any('> "$CODEX_DIR/rc"' in ln for ln in lines):
        return False
    start = lines.index(RUN_BRANCH_LINE)
    end = next((i for i in range(start + 1, len(lines)) if lines[i] == "fi"), None)
    if end is None:
        return False
    branch = lines[start:end]
    if branch.count("rc=$?") != 1 or branch.count(RC_ATOMIC_LINE) != 1:
        return False
    if branch.index("rc=$?") > branch.index(RC_ATOMIC_LINE):
        return False
    guard = lines.index(FOCUS_GUARD_LINE)
    return guard + 1 < len(lines) and lines[guard + 1] == FOCUS_MARKER_LINE


LAUNCHED_AT_LINE = ('date +%s > "$CODEX_DIR/launched_at.tmp" && '
                    'mv "$CODEX_DIR/launched_at.tmp" "$CODEX_DIR/launched_at"')
WATCHDOG_TOKEN = '"$TIMEOUT_BIN" -k 10 300 node'


def kickoff_records_launch_time(kickoff_text):
    """Inside the run branch, the launch time is written once (temp file +
    rename) BEFORE the watchdog line, so Phase 3 times its wait from the launch."""
    lines = [ln.strip() for ln in kickoff_text.splitlines()]
    if RUN_BRANCH_LINE not in lines:
        return False
    start = lines.index(RUN_BRANCH_LINE)
    end = next((i for i in range(start + 1, len(lines)) if lines[i] == "fi"), None)
    if end is None:
        return False
    branch = lines[start:end]
    if branch.count(LAUNCHED_AT_LINE) != 1:
        return False
    watchdog = [i for i, ln in enumerate(branch) if ln.startswith(WATCHDOG_TOKEN)]
    return len(watchdog) == 1 and branch.index(LAUNCHED_AT_LINE) < watchdog[0]


COLLECT = "phases/deep-review/30-codex-collect.md"
LAUNCHED_READ_LINE = 'LAUNCHED_AT=$(cat "$CODEX_DIR/launched_at" 2>/dev/null || true)'
LAUNCHED_CHECK_LINE = '''case "$LAUNCHED_AT" in ''|*[!0-9]*) LAUNCHED_AT="$STARTED_AT" ;; esac'''
REMAIN_LINE = "REMAIN=$(( LAUNCHED_AT + 315 - $(date +%s) ))"
WAIT_LINE = ('''if [ "$REMAIN" -gt 0 ]; then "$TIMEOUT_BIN" "$REMAIN" sh -c '''
             '''\'until [ -e "$1" ]; do sleep 2; done\' _ "$CODEX_DIR/rc"; fi''')
RC_READ_LINE = 'RC=$(cat "$CODEX_DIR/rc" 2>/dev/null || true)'
BASH_TIMEOUT = "timeout: 330000"
CASE_ARMS = ("0) CODEX_COLLECT=join ;;", "124) CODEX_COLLECT=timeout ;;",
             "focus-missing) CODEX_COLLECT=focus-unreadable ;;", "*) CODEX_COLLECT=timeout ;;")
PAYLOAD_LINE = 'CODEX_OUT="$CODEX_DIR/payload.json"'
CLEANUP_TOKEN = 'rm -rf "$CODEX_DIR"'


def fenced_block_with(text, needle):
    """The body of the first ``` fenced block whose stripped lines include
    `needle`, as stripped lines; None when no block holds it."""
    block, inside = [], False
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("```"):
            if inside:
                if needle in block:
                    return block
                block = []
            inside = not inside
            continue
        if inside:
            block.append(s)
    return None


def collect_wait_is_bounded(collect_text):
    """Phase 3 waits for rc under $TIMEOUT_BIN within LAUNCHED_AT + 315 (the
    launch time read from $CODEX_DIR/launched_at, digits-only, else STARTED_AT),
    states the Bash tool timeout, maps rc through a strict case with all four
    arms and no eval anywhere in the wait block."""
    if BASH_TIMEOUT not in collect_text:
        return False
    block = fenced_block_with(collect_text, REMAIN_LINE)
    if block is None:
        return False
    if WAIT_LINE not in block or RC_READ_LINE not in block or 'case "$RC" in' not in block:
        return False
    if LAUNCHED_READ_LINE not in block or LAUNCHED_CHECK_LINE not in block:
        return False
    if any(re.search(r"\beval\b", ln) for ln in block):
        return False
    order = [block.index(x) for x in (LAUNCHED_READ_LINE, LAUNCHED_CHECK_LINE, REMAIN_LINE,
                                      WAIT_LINE, RC_READ_LINE, 'case "$RC" in')]
    if order != sorted(order):
        return False
    case_at = block.index('case "$RC" in')
    esac = next((i for i in range(case_at, len(block)) if block[i] == "esac"), None)
    if esac is None:
        return False
    return list(block[case_at + 1:esac]) == list(CASE_ARMS)


def collect_out_is_payload_in_dir(kickoff_text, collect_text):
    """Both the launch and the translate step name the payload inside CODEX_DIR."""
    return all(PAYLOAD_LINE in [ln.strip() for ln in text.splitlines()]
               for text in (kickoff_text, collect_text))


def no_collection_cleanup(*texts):
    """Nothing removes the collection directory (the runbook copies it later)."""
    return all(CLEANUP_TOKEN not in text for text in texts)


def args_line_ok(kickoff_text):
    """The launch passes "$CODEX_FOCUS" as its last argument and no bare launch remains."""
    lines = [ln.strip() for ln in kickoff_text.splitlines()]
    return ('ARGS=(adversarial-review --json <codex_args> "$CODEX_FOCUS")' in lines
            and "ARGS=(adversarial-review --json <codex_args>)" not in kickoff_text)


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
# Safe-change recognition block (bugs, security, impact)
# --------------------------------------------------------------------------- #
# The twenty-one clauses of the shared block, verbatim after whitespace
# normalization (case-sensitive). Index order is relied on by the tests:
# [10] is the loosening-is-a-defect clause, [11] the sensitive-area cap
# sentence, [12] the no-repository-occurrence clause, and the three-branch
# moved-control rule: [17] defines a same-purpose replacement (guards the same
# property as the removed check); [18] branch 1, none found and read — even when
# a comment asserts a move, or when the only code found guards a different
# property — leaves the removal rule at honest confidence, uncapped; [19]
# branch 2, a traced path bypassing a same-purpose replacement is a demonstrated
# loss, uncapped; [20] branch 3, a same-purpose replacement with unverified
# coverage leaves the capped note.
SAFE_CHANGE_CLAUSES = (
    "A diff that TIGHTENS a control — it reduces what can get through — is presumptively "
    "safe on the axis it tightens.",
    "adds an allowlist/denylist validator on an input",
    "wraps output in an existing sanitizer/escaper",
    "adds a bound or finite-only check to a numeric field",
    "routes an input through an existing clamping/parse helper",
    "unless you name a concrete bypass: a specific input value AND the path by which it "
    "defeats the case the new check is written to block, cited at `file:line`.",
    "\"Could be bypassed\", \"may be incomplete\", \"not exhaustive\" or \"sensitive area\" "
    "do not lift the cap.",
    "A bypass input the pre-change code equally allowed — a case the diff never addressed — "
    "is a pre-existing gap, not a defect of this diff: report it under the cap.",
    "Rejecting an input the old code accepted is the control working, not a regression",
    "Review the same diff normally on every other axis",
    "a diff that removes, reverts, loosens, disables or bypasses a control, or makes it depend "
    "on fragile or version-dependent configuration, IS a demonstrated defect on a changed "
    "line when a path the control used to protect is left without it. Report it at your "
    "honest confidence; no cap applies.",
    "cap `agent_confidence ≤ 45`, set `severity: low` and add `pending: <what would "
    "demonstrate it>`. Still report it — the cap is a downgrade, never a drop.",
    "report that at your honest confidence whether or not that value occurs in this repository",
    "Off-hunk is not the same as unverified: repository context outside the diff that you "
    "have actually read counts as evidence",
    "a note with no demonstrated defect has no demonstrated consequence, so it is `low` until "
    "a defect is shown",
    "At `agent_confidence ≤ 45` and `severity: low` the note never reaches the Warning band, "
    "even if Codex independently flags the same site while joined and it persists across passes",
    "report at most a non-blocking note (`agent_confidence ≤ 45`, `severity: low`, plus "
    "`pending: <what would demonstrate a bypass>`)",
    "A control moved rather than lost is judged by what you found, not by what the diff "
    "claims. A same-purpose replacement is code at `file:line` — shared middleware, a "
    "decorator, a schema or an upstream layer — that guards the same property as the removed "
    "check.",
    "When you found and read no same-purpose replacement — including when only a comment, "
    "docstring or commit message asserts a move, or when the only code you found guards a "
    "different property (logging or rate-limiting middleware for a removed auth check) — the "
    "removal rule above applies at your honest confidence and the cap does not apply. A move "
    "claim in the diff text is never evidence of a replacement.",
    "When you found and read a same-purpose replacement and can trace a formerly protected "
    "path that bypasses it, that is a demonstrated protection loss: report it at your honest "
    "confidence; no cap applies, because demonstrated loss always takes precedence over the "
    "cap.",
    "When you found and read a same-purpose replacement whose coverage of every formerly "
    "protected path remains unverified, report the removal as a capped note "
    "(`agent_confidence ≤ 45`, `severity: low`) with `pending: confirm <file:line> covers "
    "every path the old check guarded`.",
)

# The exact ceilings the block states, in order: the tightened-axis note, the
# moved-control capped note (branch 3 only), the sensitive-area cap and its
# Warning-band sentence. Pinning the list means any added cap — however worded,
# including a re-cap of branch 1 or branch 2 — trips.
BLOCK_EXPECTED_CAPS = [45, 45, 45, 45]

# Substrings the block must never carry: a repository-occurrence requirement
# ("a concrete in-repo value") would let a traced break of contract-supported
# configuration be dismissed for lack of a fixture. "not a removal" would
# reopen the moved-control exemption that drops a claimed move without a trace.
# The last three would re-cap a move no replacement was found for (a real
# removal filtered out of the report on the strength of a comment).
BLOCK_FORBIDDEN = ("in-repo", "not a removal", "not named, not read",
                   "the same capped note applies", "confirm no replacement covers")

_CAP45 = re.compile(r"agent_confidence\s*(?:≤|<=)\s*45")


def block_forbidden_hits(text):
    """BLOCK_FORBIDDEN substrings present in `text` (whitespace-normalized)."""
    hay = norm(text)
    return [p for p in BLOCK_FORBIDDEN if p in hay]


def caps_without_low_severity(text):
    """Sentences stating the 45 cap without `severity: low` (split on '. ')."""
    return [s for s in norm(text).split(". ")
            if _CAP45.search(s) and "severity: low" not in s]


# --------------------------------------------------------------------------- #
# Location-keyed ceilings
# --------------------------------------------------------------------------- #
# Fragments of ceilings keyed on WHERE evidence sits rather than whether it was
# verified: the nine bugs.md fragments retired in favour of "remains
# unverified", plus the security-anchor fragment. Case-insensitive.
LOCATION_CAP_PHRASES = (
    "visible in the diff/hunk",
    "on invisible context",
    "off-hunk-context finding",
    "could live off-hunk",
    "off-hunk callee",
    "evidence required in-hunk",
    "acquire-to-release scope is in-hunk",
    "not visible in-hunk, reduce",
    "the needed context is off-hunk",
    "leg is off-hunk",
)

# A sentence that names a cap and a location is legal only when it also says the
# cap is about unverified (or unread) evidence.
EVIDENCE_QUALIFIERS = (
    "unverified",
    "actually read",
    "you have read",
    "you have not read",
    "you read",
    "not confirmed",
    "not the same as unverified",
    "read evidence",
)

_ANY_CAP = re.compile(r"(?:≤|<=)\s*\d+")


def strip_fences(text):
    """Remove every ``` fenced block (example JSON is not instruction prose)."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def location_cap_hits(text):
    """Location-keyed ceilings in `text`, fences stripped.

    Returns every LOCATION_CAP_PHRASES hit, then every '. '-delimited sentence
    that names a cap (`≤ N` / `<= N`) and 'off-hunk' or 'in-hunk' but none of
    EVIDENCE_QUALIFIERS. A sentence already reported through a phrase hit is not
    reported twice.
    """
    hay = norm(strip_fences(text))
    low = hay.lower()
    hits = [p for p in LOCATION_CAP_PHRASES if p.lower() in low]
    for sentence in hay.split(". "):
        s = sentence.lower()
        if not _ANY_CAP.search(sentence):
            continue
        if "off-hunk" not in s and "in-hunk" not in s:
            continue
        if any(q in s for q in EVIDENCE_QUALIFIERS):
            continue
        if any(p.lower() in s for p in LOCATION_CAP_PHRASES):
            continue
        hits.append(sentence)
    return hits


# --------------------------------------------------------------------------- #
# Scorer fixtures (pure) for the two-pass proof
# --------------------------------------------------------------------------- #
_WINDOW = ["a", "b", "c", "d", "e"]


def _finding(**over):
    """A finding with the agent-output-schema key set and a source window."""
    f = {
        "id": "x-001",
        "file": "src/a.py",
        "line": 10,
        "title": "some finding",
        "category": "ssrf",
        "cwe": None,
        "severity": "critical",
        "agent_confidence": 100,
        "in_diff": False,
        "intent_doc_match": None,
        "problem": "p",
        "current_code": "  x = 1",
        "fix_hint": None,
        "why_it_matters": "w",
        "silenced_marker_nearby": False,
        "agent": "security",
        "source_window": list(_WINDOW),
    }
    f.update(over)
    return f


def _cdx_note(sev, **over):
    """A capped Codex note (agent_confidence 45) one line below the real defect."""
    base = dict(id="cdx", line=11, agent="codex-adversarial", category="adversarial",
                agent_confidence=45, severity=sev, title="codex note",
                current_code="return r")
    base.update(over)
    return _finding(**base)


def _sec_note(sev, **over):
    """A capped security-lane note (agent_confidence 45) two lines below."""
    base = dict(id="sec", line=12, agent="security", agent_confidence=45,
                severity=sev, title="security note", current_code="return s")
    base.update(over)
    return _finding(**base)


def _envelope(findings, carryforward, codex_status, pass_number):
    return {
        "command": "deep-review",
        "all_mode": False,
        "pass_number": pass_number,
        "changed_line_ranges": {"src/a.py": [[8, 14]]},
        "carryforward": carryforward,
        "findings": findings,
        "codex": {"status": codex_status},
    }


def _carry(result, fixed_ids):
    """Build the next pass's carryforward from a scored result.

    Mirrors the orchestrator's HEAD read (30-collect-score.md step 0): each row
    and each of its members gets `canonical_line_content` = its own
    `current_code` (line unchanged) and the source window; a row whose id is in
    `fixed_ids` had its line removed, so it and its own member record (same
    agent, line and title) read as gone (None).
    """
    carried = []
    for row in copy.deepcopy(result["findings"]):
        fixed = row.get("id") in fixed_ids
        row["canonical_line_content"] = None if fixed else row.get("current_code")
        row["canonical_window"] = list(_WINDOW)
        for m in row.get("members", []):
            own = (m.get("agent"), m.get("line"), m.get("title")) == (
                row.get("agent"), row.get("line"), row.get("title"))
            m["canonical_line_content"] = None if (fixed and own) else m.get("current_code")
            m["canonical_window"] = list(_WINDOW)
        carried.append(row)
    return carried


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
                "confidence at or below 0.45 … report it at or below 0.35 confidence")
        self.assertEqual(caps_in(text), [45, 40, 45, 35])

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


class TestFocusText(unittest.TestCase):
    def test_strips_trailing_newlines_like_command_substitution(self):
        self.assertEqual(focus_text("hello world\n"), "hello world")
        self.assertEqual(focus_text("wrapped\nliteral\n\n"), "wrapped\nliteral")
        self.assertEqual(focus_text("do not skip what isn't shown\n"),
                         "do not skip what isn't shown")


# --------------------------------------------------------------------------- #
# Two-pass ceiling proof against the real scorer
# --------------------------------------------------------------------------- #
class TestTwoPassCeiling(unittest.TestCase):
    """A capped note rides along as a member of a real finding's row, the real
    finding is fixed, and the note is re-scored next pass as persisted (and, in
    arm B, Codex-corroborated again). Only severity low stays below Warning.

    The arithmetic helpers supply the EXPECTED numbers; score.run() supplies the
    ACTUAL ones.
    """

    def setUp(self):
        self.c = scoring_constants(read("templates/scoring.md"))

    def _pass1(self, sev):
        return score.run(_envelope(
            [_finding(id="real", line=10, agent_confidence=85, severity="critical",
                      title="real defect", current_code="return q"),
             _cdx_note(sev), _sec_note(sev)],
            [], "joined", 1))

    def _pass2(self, sev):
        p1 = self._pass1(sev)
        self.assertEqual(len(p1["findings"]), 1)
        self.assertEqual(p1["findings"][0]["id"], "real")
        self.assertEqual(len(p1["findings"][0]["members"]), 3)
        carried = _carry(p1, {"real"})
        arm_a = score.run(_envelope([], carried, "off", 2))
        arm_b = score.run(_envelope(
            [_cdx_note(sev, id="cdx2")], _carry(p1, {"real"}), "joined", 2))
        return arm_a, arm_b

    def test_capped_low_notes_never_reach_warning_after_carry_forward(self):
        arm_a, arm_b = self._pass2("low")
        for arm in (arm_a, arm_b):
            for row in arm["findings"]:
                self.assertLess(row["orchestrator_score"], self.c["warning_floor"])
                self.assertNotIn(row["band"], ("warning", "critical"))
        # Non-vacuity: arm B really carries the notes to the Medium floor.
        self.assertEqual(len(arm_b["findings"]), 1)
        row = arm_b["findings"][0]
        self.assertEqual(row["status"], "persisted")
        self.assertEqual(row["orchestrator_score"], max_path_score(45, self.c, "low"))
        self.assertEqual(row["orchestrator_score"], 70)
        self.assertEqual(row["band"], "medium")
        self.assertEqual(sorted(row["attribution"]), ["codex-adversarial", "security"])
        # Arm A: persisted but uncorroborated -> 60, dropped as sub-threshold.
        self.assertEqual(arm_a["findings"], [])
        self.assertTrue(any("sub-threshold" in str(f.get("reason", ""))
                            for f in arm_a["filtered"]), arm_a["filtered"])

    def test_higher_severity_variants_do_reach_warning(self):
        for sev in ("critical", "high", "medium"):
            with self.subTest(severity=sev):
                arm_a, arm_b = self._pass2(sev)
                self.assertEqual(len(arm_b["findings"]), 1)
                row = arm_b["findings"][0]
                self.assertEqual(row["status"], "persisted")
                self.assertEqual(row["band"], "warning")
                self.assertEqual(row["orchestrator_score"],
                                 max_path_score(45, self.c, sev))
                if sev == "critical":
                    self.assertEqual(len(arm_a["findings"]), 1)
                    self.assertEqual(arm_a["findings"][0]["orchestrator_score"], 80)
                    self.assertEqual(arm_a["findings"][0]["band"], "warning")

    def test_pass_one_corroborated_low_pair_is_filtered(self):
        result = score.run(_envelope([_cdx_note("low"), _sec_note("low")],
                                     [], "joined", 1))
        self.assertEqual(result["findings"], [])
        self.assertTrue(result["filtered"])

    def test_scorer_constants_match_the_template(self):
        self.assertEqual(score.SEVERITY_WEIGHT, self.c["severity_weights"])


# --------------------------------------------------------------------------- #
# Loud-lane Safe-change recognition block
# --------------------------------------------------------------------------- #
def _lane(lane):
    return read(f"agents/{lane}.md")


def _block(lane):
    return section(_lane(lane), "Safe-change recognition")


def _offset_for(lane, consts):
    return consts["offsets"].get(lane, 0)


class TestLoudLaneBlock(unittest.TestCase):
    def setUp(self):
        self.c = scoring_constants(read("templates/scoring.md"))

    def test_block_present_before_coverage(self):
        for lane in LOUD:
            with self.subTest(lane=lane):
                text = _lane(lane)
                self.assertIsNotNone(section(text, "Safe-change recognition"))
                self.assertLess(text.index("## Safe-change recognition"),
                                text.index("## Coverage, not filtering"))

    def test_all_clauses_present(self):
        self.assertEqual(len(SAFE_CHANGE_CLAUSES), 21)
        for lane in LOUD:
            with self.subTest(lane=lane):
                self.assertEqual(missing_clauses(_block(lane), SAFE_CHANGE_CLAUSES), [])

    def test_copies_identical(self):
        b, s, i = (norm(_block(lane)) for lane in LOUD)
        self.assertEqual(b, s, "bugs and security blocks drifted apart")
        self.assertEqual(b, i, "bugs and impact blocks drifted apart")

    def test_exact_caps_pinned(self):
        # Exactly the expected ceilings: an added cap anywhere in the block,
        # however worded, changes this list.
        for lane in LOUD:
            with self.subTest(lane=lane):
                self.assertEqual(caps_in(_block(lane)), BLOCK_EXPECTED_CAPS)

    def test_three_moved_control_branches_present(self):
        # Branch 1 (none found / different property, uncapped), branch 2
        # (demonstrated loss, uncapped) and branch 3 (unverified coverage,
        # capped), in that order after the same-purpose definition.
        definition, b1, b2, b3 = SAFE_CHANGE_CLAUSES[17:21]
        self.assertIn("guards the same property as the removed check", definition)
        self.assertIn("only a comment, docstring or commit message asserts a move", b1)
        self.assertIn("the only code you found guards a different property", b1)
        self.assertIn("the cap does not apply", b1)
        self.assertIn("demonstrated protection loss", b2)
        self.assertIn("no cap applies, because demonstrated loss always takes precedence "
                      "over the cap", b2)
        self.assertIn("remains unverified", b3)
        self.assertEqual(caps_in(b3), [45])
        for lane in LOUD:
            with self.subTest(lane=lane):
                blk = norm(_block(lane))
                at = [blk.index(norm(c)) for c in (definition, b1, b2, b3)]
                self.assertEqual(at, sorted(at))

    def test_caps_never_exceed_ceiling(self):
        for lane in LOUD:
            with self.subTest(lane=lane):
                caps = caps_in(_block(lane))
                self.assertGreaterEqual(len(caps), 2)
                self.assertLessEqual(max(caps), 45)
                for cap in caps:
                    self.assertIs(
                        cap_is_nonblocking(cap, self.c, _offset_for(lane, self.c)), True)

    def test_downgrade_never_drop(self):
        for lane in LOUD:
            with self.subTest(lane=lane):
                self.assertIn("Still report it", norm(_block(lane)))
                cov = section(_lane(lane), "Coverage, not filtering")
                self.assertIsNotNone(cov)
                self.assertIn("Report every issue you find", norm(cov))

    def test_capped_notes_carry_low_severity(self):
        # The prose requirement exists because of the template arithmetic:
        # a capped note at low never warns on any path, at critical it does.
        self.assertIs(cap_never_warns(45, self.c, "low"), True)
        self.assertIs(cap_never_warns(45, self.c, "critical"), False)
        for lane in LOUD:
            with self.subTest(lane=lane):
                blk = _block(lane)
                self.assertEqual(caps_without_low_severity(blk), [])
                self.assertGreaterEqual(norm(blk).count("severity: low"), 3)

    def test_no_repository_occurrence_requirement(self):
        c13 = SAFE_CHANGE_CLAUSES[12]
        self.assertIn("whether or not that value occurs", c13)
        for lane in LOUD:
            with self.subTest(lane=lane):
                blk = norm(_block(lane))
                self.assertEqual(block_forbidden_hits(blk), [])
                self.assertIn(norm(c13), blk)

    def test_removal_requires_protection_loss(self):
        # Moving a validator into shared middleware is a refactor, not a removal:
        # the removal rule applies only when a protected path is left unprotected.
        c11, moved = SAFE_CHANGE_CLAUSES[10], SAFE_CHANGE_CLAUSES[17]
        self.assertIn("when a path the control used to protect is left without it", c11)
        self.assertIn("shared middleware", moved)
        for lane in LOUD:
            with self.subTest(lane=lane):
                blk = norm(_block(lane))
                self.assertGreater(blk.index(norm(moved)), blk.index(norm(c11)))
        self.assertIn("leaving a path it used to guard without it", _security_anchors())
        self.assertIn("moved into shared middleware", _security_anchors())


class TestLoudLaneBlockMutation(unittest.TestCase):
    """Planted changes to an in-memory copy of the real block must trip each lock."""

    def setUp(self):
        self.c = scoring_constants(read("templates/scoring.md"))
        self.bugs = norm(_block("bugs"))

    def test_dropped_clause_is_reported(self):
        c11 = SAFE_CHANGE_CLAUSES[10]
        planted = self.bugs.replace(norm(c11), "")
        self.assertNotEqual(planted, self.bugs)
        self.assertEqual(missing_clauses(planted, SAFE_CHANGE_CLAUSES), [c11])

    def test_raised_cap_is_caught(self):
        planted = self.bugs.replace("≤ 45", "≤ 55")
        self.assertEqual(max(caps_in(planted)), 55)
        self.assertIs(cap_is_nonblocking(55, self.c, -2), False)

    def test_dropped_severity_is_caught(self):
        planted = self.bugs.replace(", set `severity: low`", "")
        self.assertNotEqual(planted, self.bugs)
        hits = caps_without_low_severity(planted)
        self.assertEqual(len(hits), 1, hits)
        self.assertIn("what would demonstrate it", hits[0])
        self.assertEqual(missing_clauses(planted, SAFE_CHANGE_CLAUSES),
                         [SAFE_CHANGE_CLAUSES[11]])
        self.assertEqual(
            caps_without_low_severity("cap `agent_confidence ≤ 45` and add pending. Other text."),
            ["cap `agent_confidence ≤ 45` and add pending"])

    def test_unconditional_removal_rule_is_caught(self):
        c11, moved = SAFE_CHANGE_CLAUSES[10], SAFE_CHANGE_CLAUSES[17]
        planted = self.bugs.replace(
            " when a path the control used to protect is left without it", "")
        self.assertNotEqual(planted, self.bugs)
        self.assertEqual(missing_clauses(planted, SAFE_CHANGE_CLAUSES), [c11])
        dropped = self.bugs.replace(norm(moved), "")
        self.assertEqual(missing_clauses(dropped, SAFE_CHANGE_CLAUSES), [moved])

    def test_unnamed_replacement_exemption_is_caught(self):
        # A found-and-read replacement leaves a capped note, never a full drop.
        found, not_found = SAFE_CHANGE_CLAUSES[20], SAFE_CHANGE_CLAUSES[18]
        planted = self.bugs.replace(
            "report the removal as a capped note",
            "the removal is not a removal and needs no note")
        self.assertNotEqual(planted, self.bugs)
        self.assertEqual(missing_clauses(planted, SAFE_CHANGE_CLAUSES), [found])
        self.assertEqual(block_forbidden_hits(planted), ["not a removal"])
        silenced = self.bugs.replace(norm(not_found), "Such a move is not reported.")
        self.assertNotEqual(silenced, self.bugs)
        self.assertEqual(missing_clauses(silenced, SAFE_CHANGE_CLAUSES), [not_found])

    def test_not_found_move_stays_uncapped(self):
        # The not-found clause keeps a comment-asserted move at honest
        # confidence: it carries the comment case, says the cap does not apply,
        # and states no ceiling of its own.
        not_found = SAFE_CHANGE_CLAUSES[18]
        self.assertIn("only a comment, docstring or commit message asserts a move", not_found)
        self.assertIn("at your honest confidence and the cap does not apply", not_found)
        self.assertIn("never evidence of a replacement", not_found)
        for lane in LOUD:
            with self.subTest(lane=lane):
                blk = _block(lane)
                self.assertEqual(block_forbidden_hits(blk), [])
                # Against the LIVE block: branches 1 and 2, and anything
                # inserted between them and branch 3, state no ceiling.
                self.assertEqual(caps_in(uncapped_moved_span(
                    blk, not_found, SAFE_CHANGE_CLAUSES[20])), [])

    def test_cap_inserted_into_uncapped_branches_trips(self):
        # A cap planted inside the live uncapped span, beside intact clauses,
        # trips the live-span check and the pinned list.
        b1, b3 = SAFE_CHANGE_CLAUSES[18], SAFE_CHANGE_CLAUSES[20]
        anchor = "never evidence of a replacement."
        planted = self.bugs.replace(
            anchor, anchor + " Hold such a claimed move at agent_confidence <= 45.", 1)
        self.assertNotEqual(planted, self.bugs)
        self.assertEqual(missing_clauses(planted, SAFE_CHANGE_CLAUSES), [])
        self.assertEqual(block_forbidden_hits(planted), [])
        self.assertEqual(caps_in(uncapped_moved_span(planted, b1, b3)), [45])
        self.assertNotEqual(caps_in(planted), BLOCK_EXPECTED_CAPS)

    def test_recapped_not_found_case_trips(self):
        # (i) Re-adding a cap for the not-found case trips a lock, whether the
        # not-found clause is rewritten or a cap is appended beside it intact.
        not_found = SAFE_CHANGE_CLAUSES[18]
        rewritten = self.bugs.replace("and the cap does not apply",
                                      "under the same capped note (`agent_confidence ≤ 45`, "
                                      "`severity: low`)")
        self.assertNotEqual(rewritten, self.bugs)
        self.assertEqual(missing_clauses(rewritten, SAFE_CHANGE_CLAUSES), [not_found])
        appended = (self.bugs + " A claimed move is never a silent drop: when the replacement "
                    "is not named, not read, or its coverage of every path is uncertain, the "
                    "same capped note applies (`agent_confidence ≤ 45`, `severity: low`) with "
                    "`pending: confirm no replacement covers <path>`.")
        self.assertEqual(missing_clauses(appended, SAFE_CHANGE_CLAUSES), [])
        self.assertEqual(block_forbidden_hits(appended),
                         ["not named, not read", "the same capped note applies",
                          "confirm no replacement covers"])
        # A reworded appended re-cap avoids every forbidden phrase; the pinned
        # cap list is what catches it.
        reworded = (self.bugs + " Where only a comment claims the move, keep the removal at "
                    "`agent_confidence ≤ 45`, `severity: low`.")
        self.assertEqual(missing_clauses(reworded, SAFE_CHANGE_CLAUSES), [])
        self.assertEqual(block_forbidden_hits(reworded), [])
        self.assertEqual(caps_without_low_severity(reworded), [])
        self.assertNotEqual(caps_in(reworded), BLOCK_EXPECTED_CAPS)

    def test_comment_asserted_move_capped_trips(self):
        # (ii) Dropping the comment-asserted case from the uncapped branch, or
        # letting a comment count as a replacement, trips the clause lock.
        not_found = SAFE_CHANGE_CLAUSES[18]
        no_comment = self.bugs.replace(
            "including when only a comment, docstring or commit message asserts a move, or ", "")
        self.assertNotEqual(no_comment, self.bugs)
        self.assertEqual(missing_clauses(no_comment, SAFE_CHANGE_CLAUSES), [not_found])
        trusted = self.bugs.replace("is never evidence of a replacement",
                                    "counts as a named replacement")
        self.assertNotEqual(trusted, self.bugs)
        self.assertEqual(missing_clauses(trusted, SAFE_CHANGE_CLAUSES), [not_found])

    def test_dropped_same_property_condition_trips(self):
        # Letting different-property code (logging, rate limiting) count as a
        # replacement, from either the definition or branch 1, trips a clause.
        definition, b1 = SAFE_CHANGE_CLAUSES[17], SAFE_CHANGE_CLAUSES[18]
        no_cond = self.bugs.replace(
            ", or when the only code you found guards a different property (logging or "
            "rate-limiting middleware for a removed auth check)", "")
        self.assertNotEqual(no_cond, self.bugs)
        self.assertEqual(missing_clauses(no_cond, SAFE_CHANGE_CLAUSES), [b1])
        no_def = self.bugs.replace(" that guards the same property as the removed check", "")
        self.assertNotEqual(no_def, self.bugs)
        self.assertEqual(missing_clauses(no_def, SAFE_CHANGE_CLAUSES), [definition])

    def test_dropped_demonstrated_loss_branch_trips(self):
        # Removing branch 2 lets the cap swallow a traced bypass; recapping it
        # also changes the pinned cap list.
        b2 = SAFE_CHANGE_CLAUSES[19]
        dropped = self.bugs.replace(norm(b2), "")
        self.assertNotEqual(dropped, self.bugs)
        self.assertEqual(missing_clauses(dropped, SAFE_CHANGE_CLAUSES), [b2])
        recapped = self.bugs.replace(
            "no cap applies, because demonstrated loss always takes precedence over the cap",
            "keep it under the same cap (`agent_confidence ≤ 45`, `severity: low`)")
        self.assertNotEqual(recapped, self.bugs)
        self.assertEqual(missing_clauses(recapped, SAFE_CHANGE_CLAUSES), [b2])
        self.assertNotEqual(caps_in(recapped), BLOCK_EXPECTED_CAPS)

    def test_added_cap_trips_pinned_list(self):
        # Any extra cap appended beside intact clauses changes the pinned list.
        self.assertEqual(caps_in(self.bugs), BLOCK_EXPECTED_CAPS)
        planted = (self.bugs + " A move you could not fully trace is reported with "
                   "agent_confidence <= 40.")
        self.assertEqual(missing_clauses(planted, SAFE_CHANGE_CLAUSES), [])
        self.assertEqual(block_forbidden_hits(planted), [])
        self.assertNotEqual(caps_in(planted), BLOCK_EXPECTED_CAPS)

    def test_drifted_copy_is_caught(self):
        drifted = norm(_block("security")) + " extra"
        self.assertNotEqual(self.bugs, drifted)

    def test_planted_repo_occurrence_trips(self):
        planted = self.bugs + " unless you cite a concrete in-repo value"
        self.assertEqual(block_forbidden_hits(planted), ["in-repo"])

    def test_planted_full_drop_exemption_trips(self):
        # An exemption appended beside the intact clauses would pass the
        # presence lock; the forbidden phrase is what catches it.
        planted = (self.bugs + " A control moved to middleware you have read is not a "
                   "removal and needs no finding.")
        self.assertEqual(missing_clauses(planted, SAFE_CHANGE_CLAUSES), [])
        self.assertEqual(block_forbidden_hits(planted), ["not a removal"])


# --------------------------------------------------------------------------- #
# security.md confidence anchors and capped example
# --------------------------------------------------------------------------- #
def _security_anchors():
    return norm(section(_lane("security"), "Confidence anchors") or "")


# The anchors only point at the moved-control rule; restating its conditions
# there lets a weaker shorthand (e.g. "name + read" without the capped note)
# drift from the Safe-change recognition block.
ANCHOR_MOVED_RESTATEMENTS = ("not a removal", "only when", "name that replacement",
                             "have read it", "covers every path", "never dropped")


def anchor_moved_restatements(anchors_text):
    """ANCHOR_MOVED_RESTATEMENTS substrings present in `anchors_text`."""
    hay = norm(anchors_text)
    return [p for p in ANCHOR_MOVED_RESTATEMENTS if p in hay]


class TestSecurityAnchors(unittest.TestCase):
    def test_anchor_scale_present(self):
        a = _security_anchors()
        for token in ("90+", "60–75", "≤ 45", "severity: low", "pending:",
                      "weakens, removes or reverts"):
            with self.subTest(token=token):
                self.assertIn(token, a)

    def test_top_anchor_keys_on_view_not_location(self):
        # The 90+ anchor says "in view", which includes context actually read;
        # a bare "both in-hunk" would key the top anchor on location.
        a = _security_anchors()
        self.assertIn("source and sink are both in view (in-hunk, or in repository "
                      "context you actually read)", a)
        self.assertNotIn("both in-hunk", a)

    def test_example_has_capped_finding(self):
        m = re.search(r"```json\n(.*?)\n```", _lane("security"), re.S)
        self.assertIsNotNone(m)
        example = json.loads(m.group(1))
        capped = [f for f in example["findings"]
                  if f["agent_confidence"] <= 45 and f["severity"] == "low"
                  and "pending:" in f["problem"]]
        self.assertEqual(len(capped), 1, example["findings"])

    def test_offhunk_verified_context_is_not_capped(self):
        a = _security_anchors()
        self.assertIn("Off-hunk is not the same as unverified", a)
        self.assertIn("repository context", a)
        self.assertNotIn("leg is off-hunk", a)

    def test_anchors_point_to_moved_rule_without_restating_it(self):
        a = _security_anchors()
        self.assertIn("follows the moved-control rule in Safe-change recognition below", a)
        self.assertEqual(anchor_moved_restatements(a), [])


class TestSecurityAnchorsMutation(unittest.TestCase):
    def test_planted_offhunk_cap_trips(self):
        a = _security_anchors()
        planted = a.replace("remains unverified", "is off-hunk")
        self.assertIn("a needed leg is off-hunk", planted)
        self.assertIn("leg is off-hunk", planted)
        m = re.search(r"Off-hunk is not the same as unverified[^.]*\.", a)
        self.assertIsNotNone(m)
        self.assertNotIn("Off-hunk is not the same as unverified", a.replace(m.group(0), ""))

    def test_planted_moved_shorthand_trips(self):
        a = _security_anchors()
        planted = a.replace(
            "follows the moved-control rule in Safe-change recognition below.",
            "is not a removal only when you name that replacement at `file:line` and have "
            "read it; see Safe-change recognition below.")
        self.assertNotEqual(planted, a)
        self.assertEqual(anchor_moved_restatements(planted),
                         ["not a removal", "only when", "name that replacement", "have read it"])


# --------------------------------------------------------------------------- #
# No loud lane keys a ceiling on location
# --------------------------------------------------------------------------- #
class TestLocationCapReconciled(unittest.TestCase):
    def test_no_location_keyed_cap(self):
        found = {lane: location_cap_hits(_lane(lane)) for lane in LOUD}
        for lane in LOUD:
            with self.subTest(lane=lane):
                self.assertEqual(found[lane], [], f"{lane}: {found[lane]}")

    def test_bugs_anchors_and_checks_key_on_verification(self):
        bugs = _lane("bugs")
        a = norm(section(bugs, "Confidence anchors"))
        self.assertIn("Off-hunk is not the same as unverified", a)
        self.assertIn("the needed context remains unverified", a)
        self.assertNotIn("in-hunk (guard", a)
        c = norm(section(bugs, "Checks"))
        for s in ("in view — in the diff/hunk, or in repository context you actually read",
                  "when a release site remains unverified",
                  "When the guard's absence is unverified"):
            with self.subTest(sentence=s):
                self.assertIn(s, c)

    def test_impact_anchors_key_on_evidence(self):
        o = norm(section(_lane("impact"), "Output"))
        self.assertIn("you READ the importers/callers you are citing", o)
        self.assertIn("no measured or read evidence", o)

    def test_strip_fences_removes_example(self):
        stripped = strip_fences(_lane("bugs"))
        self.assertNotIn("\"agent_confidence\":", stripped)
        self.assertIn("## Confidence anchors", stripped)
        self.assertIn("\"agent_confidence\":", _lane("bugs"))  # non-vacuity


class TestLocationCapMutation(unittest.TestCase):
    def test_planted_retired_fragment_trips(self):
        self.assertEqual(
            location_cap_hits(_lane("bugs")
                              + "\nflag only when the whole acquire-to-release scope is in-hunk."),
            ["acquire-to-release scope is in-hunk"])
        self.assertEqual(
            location_cap_hits(_lane("impact")
                              + "\n**≤ 40** — the needed context is off-hunk; emit with the pending note."),
            ["the needed context is off-hunk"])

    def test_planted_generic_location_cap_trips(self):
        hits = location_cap_hits(
            _lane("security") + "\nWhen the sink is off-hunk, cap at agent_confidence ≤ 40.")
        self.assertEqual(len(hits), 1, hits)
        self.assertIn("When the sink is off-hunk, cap at agent_confidence ≤ 40", hits[0])
        self.assertNotIn(hits[0], LOCATION_CAP_PHRASES)

    def test_qualified_sentence_does_not_trip(self):
        self.assertEqual(location_cap_hits(
            "When a release site remains unverified, `agent_confidence ≤ 40` plus "
            "`pending: confirm no cleanup off-hunk`."), [])

    def test_fenced_text_is_ignored(self):
        self.assertEqual(location_cap_hits(
            "```json\n\"problem\": \"the needed context is off-hunk\"\n```"), [])
        self.assertEqual(location_cap_hits("\"problem\": \"the needed context is off-hunk\""),
                         ["the needed context is off-hunk"])


# --------------------------------------------------------------------------- #
# Codex kickoff focus literal
# --------------------------------------------------------------------------- #
KICKOFF = "phases/deep-review/2c-codex-kickoff.md"
ARGS_LINE = 'ARGS=(adversarial-review --json <codex_args> "$CODEX_FOCUS")'
OLD_ARGS_LINE = "ARGS=(adversarial-review --json <codex_args>)"


def _kickoff():
    return read(KICKOFF)


def _literal():
    return focus_text(read(FOCUS_FILE))


class TestKickoffCarriesFocus(unittest.TestCase):
    def setUp(self):
        self.c = scoring_constants(read("templates/scoring.md"))

    def test_args_line_exact(self):
        self.assertIs(args_line_ok(_kickoff()), True)

    def test_kickoff_reads_focus_from_file(self):
        self.assertIs(kickoff_reads_focus_file(_kickoff()), True)
        # Echoed by the guard line AND handled as a skip in the prose after the block.
        self.assertGreaterEqual(_kickoff().count("__CODEX_FOCUS_MISSING__"), 2)

    def test_focus_readability_is_a_gate_fact(self):
        self.assertIs(kickoff_gates_focus(_kickoff()), True)
        self.assertIn(FOCUS_SLUG, codex_gate.SLUGS)
        self.assertIn("focus_readable", codex_gate.REQUIRED_FACTS)
        # Phase 3 handles the backstop sentinel and names the slug.
        collect = read("phases/deep-review/30-codex-collect.md")
        self.assertIn("__CODEX_FOCUS_MISSING__", collect)
        self.assertIn(FOCUS_SLUG, collect)

    def test_literal_tokens(self):
        lit = _literal()
        # _literal() always returns a str (a missing file raises in read()), so
        # the live check is non-emptiness, not None-ness.
        self.assertTrue(lit.strip())
        self.assertEqual(len(FOCUS_TOKENS), 21)
        self.assertEqual(missing_focus_tokens(lit), [])
        self.assertEqual(focus_repeat_shortfalls(lit), [])

    def test_literal_exact_caps_pinned(self):
        # Every ceiling, in both Codex word orders, and the exact count of 0.45.
        lit = _literal()
        self.assertEqual(caps_in(lit), FOCUS_EXPECTED_CAPS)
        self.assertEqual(lit.count("0.45"), FOCUS_045_COUNT)

    def test_literal_three_moved_control_branches(self):
        lit = _literal()
        definition, b1, b2, b3 = (FOCUS_TOKENS[16], FOCUS_TOKENS[17], FOCUS_TOKENS[19],
                                  FOCUS_TOKENS[20])
        self.assertIn("guards the same property as the removed check", definition)
        self.assertIn("the only code you found guards a different property", b1)
        self.assertIn("the cap does not apply", b1)
        self.assertIn("demonstrated protection loss", b2)
        self.assertIn("with no cap, because demonstrated loss always takes precedence", b2)
        self.assertEqual(caps_in(b3), [45])
        at = [lit.index(t) for t in (definition, b1, b2, b3)]
        self.assertEqual(at, sorted(at))

    def test_literal_exempts_demonstrated_failure_of_the_new_control(self):
        lit = _literal()
        self.assertIn("a case the diff never addressed", lit)
        self.assertIn("demonstrably fails to block", lit)
        self.assertGreater(lit.index("demonstrably fails to block"),
                           lit.index("pre-existing gap"))

    def test_literal_removal_requires_protection_loss(self):
        lit = _literal()
        self.assertIn("is a real defect on a changed line when a path the control used to "
                      "protect is left without it", lit)
        self.assertGreater(lit.index("moved rather than lost"),
                           lit.index("removes, reverts, loosens, disables or bypasses"))
        self.assertIn("shared middleware", lit)

    def test_literal_has_no_shell_metacharacters(self):
        lit = _literal()
        for ch in ("$", "`", "'"):
            with self.subTest(ch=ch):
                self.assertNotIn(ch, lit)
        self.assertNotIn("CODEX_FOCUS='", _kickoff())

    def test_literal_has_no_repository_occurrence_requirement(self):
        lit = _literal()
        self.assertEqual(focus_forbidden_hits(lit), [])
        self.assertIn("Off-hunk is not the same as unverified", lit)

    def test_literal_caps_are_nonblocking(self):
        lit = _literal()
        # Codex states its ceiling in its own unit (0.45); codex_translate.py x100.
        caps = [int(d) for d in re.findall(r"\b0\.(\d\d)\b", lit)]
        self.assertGreaterEqual(len(caps), 2)
        self.assertTrue(caps_in(lit))
        for cap in caps + caps_in(lit):
            with self.subTest(cap=cap):
                self.assertIs(cap_is_nonblocking(cap, self.c, 0), True)
                self.assertIs(cap_never_warns(cap, self.c, "low"), True)


class TestCodexCollectionFileOwned(unittest.TestCase):
    def test_no_harness_read_tool_anywhere(self):
        corpus = prose_corpus()
        self.assertIn(KICKOFF, corpus)
        self.assertIn(COLLECT, corpus)
        self.assertEqual(harness_read_tool_hits(corpus), [])

    def test_kickoff_gates_focus_with_collection_dir(self):
        self.assertIs(kickoff_gates_focus(_kickoff()), True)

    def test_launch_writes_rc_atomically(self):
        self.assertIs(kickoff_rc_is_atomic(_kickoff()), True)

    def test_collect_waits_under_timeout_bin(self):
        self.assertIs(collect_wait_is_bounded(read(COLLECT)), True)

    def test_launch_records_launch_time(self):
        self.assertIs(kickoff_records_launch_time(_kickoff()), True)

    def test_collect_out_is_payload_in_dir(self):
        self.assertIs(collect_out_is_payload_in_dir(_kickoff(), read(COLLECT)), True)

    def test_no_cleanup_before_runbook_capture(self):
        self.assertIs(no_collection_cleanup(_kickoff(), read(COLLECT)), True)


class TestKickoffMutation(unittest.TestCase):
    def test_planted_interpolation_trips(self):
        self.assertIn("$", focus_forbidden_hits(focus_text("rules $DIFF here\n")))

    def test_planted_apostrophe_in_real_literal_trips(self):
        real = _literal()
        planted = focus_text(real[:-1] + " it isn't a defect.\n")
        self.assertNotEqual(planted, real)
        self.assertEqual(focus_forbidden_hits(real), [])
        self.assertIn("'", focus_forbidden_hits(planted))

    def test_reinlined_or_unguarded_focus_trips(self):
        k = _kickoff()
        inlined = k.replace(FOCUS_READ_LINE, "CODEX_FOCUS='" + _literal() + "'")
        self.assertNotEqual(inlined, k)
        self.assertIs(kickoff_reads_focus_file(inlined), False)
        unguarded = k.replace(FOCUS_GUARD_LINE, "")
        self.assertNotEqual(unguarded, k)
        self.assertIs(kickoff_reads_focus_file(unguarded), False)
        planted_literal = k + "\nCODEX_FOCUS='stale copy'\n"
        self.assertIs(kickoff_reads_focus_file(planted_literal), False)

    def test_unnamed_replacement_in_literal_trips(self):
        lit = _literal()
        planted = lit.replace(
            "When you found and read a same-purpose replacement whose coverage",
            "A move is not a removal when you name a replacement whose coverage")
        self.assertNotEqual(planted, lit)
        self.assertEqual(missing_focus_tokens(planted), [FOCUS_TOKENS[20]])
        self.assertEqual(focus_forbidden_hits(planted), ["not a removal"])
        appended = lit + " A control moved to middleware is not a removal and needs no finding."
        self.assertEqual(missing_focus_tokens(appended), [])
        self.assertEqual(focus_forbidden_hits(appended), ["not a removal"])

    def test_recapped_not_found_case_in_literal_trips(self):
        # (i) A cap re-added for the not-found case trips a lock.
        lit = _literal()
        not_found = FOCUS_TOKENS[17]
        rewritten = lit.replace("and the cap does not apply",
                                "at or below 0.45 confidence with severity low")
        self.assertNotEqual(rewritten, lit)
        self.assertEqual(missing_focus_tokens(rewritten), [not_found])
        appended = (lit + " A claimed move is never a silent drop: when the replacement is not "
                    "named, not read, or its coverage of every path is uncertain, the same note "
                    "applies at or below 0.45 confidence with severity low.")
        self.assertEqual(missing_focus_tokens(appended), [])
        self.assertEqual(focus_forbidden_hits(appended),
                         ["not named, not read", "the same note applies"])
        # A reworded appended re-cap in the Codex word order avoids every
        # forbidden phrase; the pinned cap list and 0.45 count catch it.
        reworded = (lit + " Where only a comment claims the move, keep it at or below 0.45 "
                    "confidence with severity low.")
        self.assertEqual(missing_focus_tokens(reworded), [])
        self.assertEqual(focus_forbidden_hits(reworded), [])
        self.assertNotEqual(caps_in(reworded), FOCUS_EXPECTED_CAPS)
        self.assertNotEqual(reworded.count("0.45"), FOCUS_045_COUNT)

    def test_comment_asserted_move_in_literal_stays_uncapped(self):
        # (ii) The comment-asserted case sits in the uncapped branch; dropping
        # it or trusting the claim trips a token.
        lit = _literal()
        not_found, claim = FOCUS_TOKENS[17], FOCUS_TOKENS[18]
        self.assertIn("comment, docstring or commit message asserts a move", not_found)
        self.assertIn("the cap does not apply", not_found)
        # Against the LIVE literal: branches 1 and 2, and anything inserted
        # between them and branch 3, state no ceiling.
        self.assertEqual(caps_in(uncapped_moved_span(lit, not_found, FOCUS_TOKENS[20])), [])
        anchor = "never evidence of a replacement."
        planted = lit.replace(
            anchor, anchor + " Hold such a claimed move at or below 0.45 confidence.", 1)
        self.assertNotEqual(planted, lit)
        self.assertEqual(missing_focus_tokens(planted), [])
        self.assertEqual(focus_forbidden_hits(planted), [])
        self.assertEqual(caps_in(uncapped_moved_span(planted, not_found, FOCUS_TOKENS[20])),
                         [45])
        no_comment = lit.replace(
            ", including when only a comment, docstring or commit message asserts a move,", ",")
        self.assertNotEqual(no_comment, lit)
        self.assertEqual(missing_focus_tokens(no_comment), [not_found])
        trusted = lit.replace("is never evidence of a replacement", "counts as a replacement")
        self.assertNotEqual(trusted, lit)
        self.assertEqual(missing_focus_tokens(trusted), [claim])

    def test_literal_dropped_branch_or_condition_trips(self):
        lit = _literal()
        definition, b1, b2 = FOCUS_TOKENS[16], FOCUS_TOKENS[17], FOCUS_TOKENS[19]
        no_cond = lit.replace(
            ", or when the only code you found guards a different property (logging or "
            "rate-limiting middleware for a removed auth check)", "")
        self.assertNotEqual(no_cond, lit)
        self.assertEqual(missing_focus_tokens(no_cond), [b1])
        no_def = lit.replace(" that guards the same property as the removed check", "")
        self.assertNotEqual(no_def, lit)
        self.assertEqual(missing_focus_tokens(no_def), [definition])
        dropped = lit.replace(b2 + ". ", "")
        self.assertNotEqual(dropped, lit)
        self.assertEqual(missing_focus_tokens(dropped), [b2])

    def test_literal_added_cap_trips_pinned_counts(self):
        lit = _literal()
        planted = lit + " A move you could not fully trace stays at or below 0.45 confidence."
        self.assertEqual(missing_focus_tokens(planted), [])
        self.assertEqual(focus_forbidden_hits(planted), [])
        self.assertNotEqual(caps_in(planted), FOCUS_EXPECTED_CAPS)
        self.assertNotEqual(planted.count("0.45"), FOCUS_045_COUNT)

    def test_focus_gate_regressions_trip(self):
        k = _kickoff()
        no_fact = k.replace(FOCUS_FACT_LINE, "")
        self.assertNotEqual(no_fact, k)
        self.assertIs(kickoff_gates_focus(no_fact), False)
        no_arg = k.replace(FOCUS_FACT_ARG + " ", "")
        self.assertNotEqual(no_arg, k)
        self.assertIs(kickoff_gates_focus(no_arg), False)
        free_text = k.replace(FOCUS_SLUG, "calibration text unreadable")
        self.assertNotEqual(free_text, k)
        self.assertIs(kickoff_gates_focus(free_text), False)
        # The readability check moved back after the disclosure line.
        late = k.replace(FOCUS_FACT_LINE, "").replace(
            RUN_BRANCH_LINE, FOCUS_FACT_LINE + "\n" + RUN_BRANCH_LINE)
        self.assertIs(kickoff_gates_focus(late), False)
        # The temp file created ahead of the run branch again (orphaned on a skip).
        hoisted = k.replace(MKTEMP_LINE, "").replace(
            RUN_BRANCH_LINE, MKTEMP_LINE + "\n" + RUN_BRANCH_LINE)
        self.assertNotEqual(hoisted, k)
        self.assertIs(kickoff_gates_focus(hoisted), False)

    def test_harness_read_tool_planted_trips(self):
        corpus = prose_corpus()
        planted = dict(corpus)
        planted[KICKOFF] = corpus[KICKOFF] + "\nRead the shell with BashOutput(id).\n"
        self.assertNotEqual(planted[KICKOFF], corpus[KICKOFF])
        self.assertEqual(harness_read_tool_hits(planted), [(KICKOFF, "BashOutput")])
        planted[COLLECT] = corpus[COLLECT] + "\nCapture the shell_id.\n"
        self.assertIn((COLLECT, "shell_id"), harness_read_tool_hits(planted))

    def test_collection_dir_regressions_trip(self):
        k = _kickoff()
        lines = k.splitlines()
        decision = next(i for i, ln in enumerate(lines) if RUN_DECISION_TOKEN in ln)
        # Created above the run-branch decision text (a skip would leave it behind).
        stripped = [ln for ln in lines if ln.strip() != MKTEMP_LINE]
        early = "\n".join(stripped[:decision] + [MKTEMP_LINE] + stripped[decision:])
        self.assertNotEqual(early, k)
        self.assertIs(kickoff_gates_focus(early), False)
        # Created twice.
        duplicated = k + "\n" + MKTEMP_LINE + "\n"
        self.assertIs(kickoff_gates_focus(duplicated), False)
        # The old bare temp file restored in place of the directory.
        old = k.replace(MKTEMP_LINE, OLD_MKTEMP_LINE)
        self.assertNotEqual(old, k)
        self.assertIs(kickoff_gates_focus(old), False)
        # The old temp file alongside the directory.
        both = k.replace(PAYLOAD_LINE, OLD_MKTEMP_LINE)
        self.assertNotEqual(both, k)
        self.assertIs(kickoff_gates_focus(both), False)

    def test_rc_atomic_regressions_trip(self):
        k = _kickoff()
        no_mv = k.replace(RC_ATOMIC_LINE, '''printf '%s\\n' "$rc" > "$CODEX_DIR/rc.tmp"''')
        self.assertNotEqual(no_mv, k)
        self.assertIs(kickoff_rc_is_atomic(no_mv), False)
        direct = k.replace(RC_ATOMIC_LINE, '''printf '%s\\n' "$rc" > "$CODEX_DIR/rc"''')
        self.assertNotEqual(direct, k)
        self.assertIs(kickoff_rc_is_atomic(direct), False)
        no_marker = k.replace(FOCUS_MARKER_LINE, "")
        self.assertNotEqual(no_marker, k)
        self.assertIs(kickoff_rc_is_atomic(no_marker), False)
        # rc written before the launch's exit status exists.
        early = k.replace(RC_ATOMIC_LINE + "\n", "").replace(
            "rc=$?", RC_ATOMIC_LINE + "\n     rc=$?")
        self.assertNotEqual(early, k)
        self.assertIs(kickoff_rc_is_atomic(early), False)

    def test_collect_wait_regressions_trip(self):
        c = read(COLLECT)
        unwrapped = c.replace('"$TIMEOUT_BIN" "$REMAIN" sh -c', "sh -c")
        self.assertNotEqual(unwrapped, c)
        self.assertIs(collect_wait_is_bounded(unwrapped), False)
        no_bash_timeout = c.replace(BASH_TIMEOUT, "timeout: 120000")
        self.assertNotEqual(no_bash_timeout, c)
        self.assertIs(collect_wait_is_bounded(no_bash_timeout), False)
        case_at = c.index('case "$RC" in')
        esac_end = c.index("esac", case_at) + len("esac")
        evaled = c[:case_at] + 'eval "CODEX_COLLECT=$RC"' + c[esac_end:]
        self.assertNotEqual(evaled, c)
        self.assertIs(collect_wait_is_bounded(evaled), False)
        # A lenient mapping: every non-zero rc treated as a join.
        lenient = c.replace(CASE_ARMS[3], "*) CODEX_COLLECT=join ;;")
        self.assertNotEqual(lenient, c)
        self.assertIs(collect_wait_is_bounded(lenient), False)
        # The wait timed from the kickoff again instead of the recorded launch.
        from_kickoff = c.replace(REMAIN_LINE, "REMAIN=$(( STARTED_AT + 315 - $(date +%s) ))")
        self.assertNotEqual(from_kickoff, c)
        self.assertIs(collect_wait_is_bounded(from_kickoff), False)
        # The launch time used unvalidated (arithmetic would evaluate file content).
        unchecked = c.replace(LAUNCHED_CHECK_LINE, "")
        self.assertNotEqual(unchecked, c)
        self.assertIs(collect_wait_is_bounded(unchecked), False)
        # The launch time read after REMAIN is computed.
        late = c.replace(LAUNCHED_READ_LINE + "\n", "").replace(
            REMAIN_LINE, REMAIN_LINE + "\n   " + LAUNCHED_READ_LINE)
        self.assertNotEqual(late, c)
        self.assertIs(collect_wait_is_bounded(late), False)

    def test_launch_time_regressions_trip(self):
        k = _kickoff()
        dropped = k.replace(LAUNCHED_AT_LINE, "")
        self.assertNotEqual(dropped, k)
        self.assertIs(kickoff_records_launch_time(dropped), False)
        # Recorded after the watchdog returns: that is the END time, not the launch.
        after = k.replace(LAUNCHED_AT_LINE + "\n", "").replace(
            "rc=$?", "rc=$?\n     " + LAUNCHED_AT_LINE)
        self.assertNotEqual(after, k)
        self.assertIs(kickoff_records_launch_time(after), False)
        # Recorded outside the run branch (a skip would leave a launch time behind).
        outside = k.replace(LAUNCHED_AT_LINE + "\n", "").replace(
            RUN_BRANCH_LINE, LAUNCHED_AT_LINE + "\n   " + RUN_BRANCH_LINE)
        self.assertNotEqual(outside, k)
        self.assertIs(kickoff_records_launch_time(outside), False)

    def test_collect_payload_regression_trips(self):
        c = read(COLLECT)
        reverted = c.replace(PAYLOAD_LINE, 'CODEX_OUT="<printed at kickoff>"')
        self.assertNotEqual(reverted, c)
        self.assertIs(collect_out_is_payload_in_dir(_kickoff(), reverted), False)

    def test_planted_cleanup_trips(self):
        c = read(COLLECT)
        planted = c + "\n" + CLEANUP_TOKEN + "\n"
        self.assertIs(no_collection_cleanup(_kickoff(), planted), False)
        self.assertIs(no_collection_cleanup(_kickoff() + CLEANUP_TOKEN, c), False)

    def test_missing_args_arg_trips(self):
        text = _kickoff().replace(ARGS_LINE, OLD_ARGS_LINE)
        self.assertNotEqual(text, _kickoff())
        self.assertIs(args_line_ok(text), False)
        self.assertIs(args_line_ok(_kickoff() + "\n" + OLD_ARGS_LINE), False)

    def test_planted_repo_occurrence_in_literal_trips(self):
        lit = focus_text("unless you cite a concrete in-repo value\n")
        self.assertIn("in-repo", lit)
        self.assertEqual(focus_forbidden_hits(lit), ["in-repo"])

    def test_missing_exemption_or_severity_trips(self):
        lit = _literal()
        m = re.search(r"[^.]*demonstrably fails to block[^.]*\.", lit)
        self.assertIsNotNone(m)
        dropped = lit.replace(m.group(0), "")
        self.assertEqual(missing_focus_tokens(dropped), ["demonstrably fails to block"])
        medium = lit.replace("severity low", "severity medium")
        self.assertNotEqual(medium, lit)
        # The moved-control capped-note token (branch 3) carries its own severity.
        self.assertEqual(missing_focus_tokens(medium), ["severity low", FOCUS_TOKENS[20]])
        self.assertEqual(focus_repeat_shortfalls(medium), ["severity low"])
        # Raising all but one capped note leaves the token present but short
        # (and the branch-3 token, raised along the way, missing).
        one_left = lit.replace("severity low", "severity medium",
                               lit.count("severity low") - 1)
        self.assertEqual(missing_focus_tokens(one_left), [FOCUS_TOKENS[20]])
        self.assertEqual(focus_repeat_shortfalls(one_left), ["severity low"])


# --------------------------------------------------------------------------- #
# Contract documents the focus-text mechanism
# --------------------------------------------------------------------------- #
class TestContractDocumentsFocus(unittest.TestCase):
    def test_section_and_mechanism(self):
        text = read("agents/codex-adversarial.md")
        sec = section(text,
                      "Calibration reaches Codex through the kickoff focus text (Phase 42)")
        self.assertIsNotNone(sec)
        for token in ("CODEX_FOCUS", "2c-codex-kickoff.md", "codex_translate.py", "0.45",
                      "severity low"):
            with self.subTest(token=token):
                self.assertIn(token, norm(sec))


# --------------------------------------------------------------------------- #
# Retired +10 prose stays retired (R6)
# --------------------------------------------------------------------------- #
def _stale_prose_corpus():
    return {rel: text for rel, text in prose_corpus().items()
            if rel.startswith(("agents/", "phases/deep-review/"))}


def _paragraphs_with(text, *needles):
    return [p for p in (norm(x) for x in re.split(r"\n\s*\n", text))
            if all(n in p for n in needles)]


class TestNoRetiredPlusTenProse(unittest.TestCase):
    def test_agents_and_deep_review_clean(self):
        corpus = _stale_prose_corpus()
        self.assertGreaterEqual(len(corpus), 20)
        self.assertIn("agents/framework-fastapi.md", corpus)
        self.assertIn("phases/deep-review/30-codex-collect.md", corpus)
        hits = {rel: forbidden_hits(text) for rel, text in sorted(corpus.items())}
        hits = {rel: h for rel, h in hits.items() if h}
        self.assertEqual(hits, {}, f"retired +10 prose: {hits}")

    def test_stem_is_in_forbidden_set(self):
        self.assertIn("independently confirm", FORBIDDEN_PHRASES)
        for stem in ("cross-confirmed by", "2+ agents"):
            with self.subTest(stem=stem):
                self.assertIn(stem, FORBIDDEN_PHRASES)

    def test_joined_named_beside_plus_ten(self):
        for rel in ("agents/codex-adversarial.md", "phases/deep-review/30-codex-collect.md",
                    "agents/index.md"):
            with self.subTest(rel=rel):
                self.assertTrue(_paragraphs_with(read(rel), "+10", "joined"), rel)


class TestStaleProseMutation(unittest.TestCase):
    def test_planted_phrase_in_agent_text_trips(self):
        self.assertEqual(
            forbidden_hits(read("agents/bugs.md") + "\nshares its domain in CATEGORY_DOMAIN"),
            ["CATEGORY_DOMAIN", "shares its domain"])

    def test_planted_retired_confirm_trips(self):
        self.assertEqual(
            forbidden_hits(read("agents/language-go.md")
                           + "\nto a Filtered-summary count unless independently confirmed."),
            ["independently confirm"])
        self.assertEqual(
            forbidden_hits(read("agents/impact.md")
                           + "\nunless another agent independently confirms the site"),
            ["independently confirm"])

    def test_planted_multi_agent_bonus_trips(self):
        # The retired wording removed from framework-fastapi.md and
        # framework-skill.md; each must trip on its own against the real file.
        fastapi = read("agents/framework-fastapi.md")
        self.assertEqual(forbidden_hits(fastapi), [])
        cases = (
            ("plus +10 if cross-confirmed by 2+ agents, plus +15 if persisted",
             ["cross-confirmed by", "if cross-confirmed", "2+ agents"]),
            ("still reaches 75 (Medium band) when cross-confirmed (+10)",
             ["when cross-confirmed"]),
            ("+ severity weight + 10 (cross-confirmed) + 15 (persisted)",
             ["(cross-confirmed)"]),
            ("the +10 fires when 2+\nlanes flag it", ["2+ lanes"]),
        )
        for planted, expected in cases:
            with self.subTest(planted=planted):
                self.assertEqual(forbidden_hits(fastapi + "\n" + planted), expected)
        # The live joined-rule wording and the collect-line count are not hits.
        self.assertEqual(forbidden_hits("({M} cross-confirmed)"), [])
        self.assertEqual(forbidden_hits("the +10 cross-confirm fires only when a "
                                        "codex-adversarial member"), [])



# --------------------------------------------------------------------------- #
# Retune clauses (the single post-measurement prompt retune)
# --------------------------------------------------------------------------- #
# Two rules added after the full measurement, each an abstract class:
# [0] a bypass that lives in the unchanged logic of an existing validator or
#     helper the diff only calls is a pre-existing gap (capped), and the cap
#     lifts only when the diff's own changed lines let the input through;
# [1] replacing an unconditional protection with one that holds only through a
#     default, a deprecated path or the installed version is a loss of the
#     guarantee even when it still holds today: honest confidence, not the
#     sensitive-area cap, and the title names the attack the control prevents.
RETUNE_BLOCK_CLAUSES = (
    "When the new check calls an existing validator or helper and the bypass lies in that "
    "helper's unchanged logic, it is likewise a pre-existing gap: every existing caller of the "
    "helper already has it, and the diff only extends the helper to one more input. Report it "
    "under the cap and name the bypass input in the `pending:` note; it lifts the cap only when "
    "the diff's own changed lines let the input through.",
    "Replacing a protection that held unconditionally with one that holds only through a "
    "library default, a deprecated path or the currently installed dependency version is a loss "
    "of that guarantee on the changed line even when you verify it still holds today: report it "
    "at your honest confidence, not under the sensitive-area cap, and name in the title the "
    "attack the control prevents once the protection lapses (for example injection, script "
    "execution or data exposure), not only the revert, deprecation or startup symptom.",
)

RETUNE_FOCUS_TOKENS = (
    "When the failure lies in the unchanged logic of an existing validator or helper that the "
    "change only calls, it is a pre-existing gap instead: every existing caller of that helper "
    "already has it, so report it under the pre-existing-gap ceiling above and name the bypass "
    "input; it is a defect of this change only when the lines the change itself adds or edits "
    "let the input through.",
    "Replacing a protection that held unconditionally with one that holds only through a library "
    "default, a deprecated path or the currently installed dependency version is such a loss even "
    "when you verify it still holds today: report it at your honest confidence, not under the "
    "sensitive-area ceiling, and name in the title the attack the control prevents once the "
    "protection lapses (for example injection, script execution or data exposure), not only the "
    "revert, deprecation or startup symptom.",
)


def _ordered(hay, before, item, after):
    """True when `item` sits strictly between `before` and `after` in `hay`."""
    try:
        return hay.index(before) < hay.index(item) < hay.index(after)
    except ValueError:
        return False


def retune_block_problems(block_text):
    """Problems with the retune clauses in a loud-lane block: missing clauses,
    then each clause outside its slot (helper clause between the pre-existing
    gap rule and the input-contract rule; guarantee clause between the
    removal rule and the moved-control definition)."""
    hay = norm(block_text or "")
    problems = missing_clauses(block_text, RETUNE_BLOCK_CLAUSES)
    if problems:
        return problems
    helper, guarantee = (norm(c) for c in RETUNE_BLOCK_CLAUSES)
    if not _ordered(hay, norm(SAFE_CHANGE_CLAUSES[7]), helper, norm(SAFE_CHANGE_CLAUSES[8])):
        problems.append("helper clause out of slot")
    if not _ordered(hay, norm(SAFE_CHANGE_CLAUSES[10]), guarantee,
                    norm(SAFE_CHANGE_CLAUSES[17])):
        problems.append("guarantee clause out of slot")
    return problems


def retune_focus_problems(literal):
    """Problems with the retune tokens in the Codex literal (same shape)."""
    lit = literal or ""
    problems = [t for t in RETUNE_FOCUS_TOKENS if t not in lit]
    if problems:
        return problems
    helper, guarantee = RETUNE_FOCUS_TOKENS
    if not _ordered(lit, "demonstrably fails to block", helper, "input contract"):
        problems.append("helper clause out of slot")
    if not _ordered(lit, "removes, reverts, loosens, disables or bypasses", guarantee,
                    "moved rather than lost"):
        problems.append("guarantee clause out of slot")
    return problems


class TestRetuneClauses(unittest.TestCase):
    def test_block_clauses_present_and_slotted(self):
        for lane in LOUD:
            with self.subTest(lane=lane):
                self.assertEqual(retune_block_problems(_block(lane)), [])

    def test_focus_tokens_present_and_slotted(self):
        self.assertEqual(retune_focus_problems(_literal()), [])

    def test_no_new_ceiling(self):
        # Neither clause states a number: the pinned cap lists stay the only caps.
        for clause in RETUNE_BLOCK_CLAUSES + RETUNE_FOCUS_TOKENS:
            self.assertEqual(caps_in(clause), [])
            self.assertNotIn("0.45", clause)

    def test_guarantee_clause_is_uncapped_and_names_the_attack(self):
        for clause in (RETUNE_BLOCK_CLAUSES[1], RETUNE_FOCUS_TOKENS[1]):
            self.assertIn("even when you verify it still holds today", clause)
            self.assertIn("at your honest confidence, not under the sensitive-area", clause)
            self.assertIn("name in the title the attack the control prevents", clause)

    def test_helper_clause_keeps_the_changed_line_exemption(self):
        self.assertIn("lifts the cap only when the diff's own changed lines let the input "
                      "through", RETUNE_BLOCK_CLAUSES[0])
        self.assertIn("only when the lines the change itself adds or edits let the input "
                      "through", RETUNE_FOCUS_TOKENS[0])

    def test_focus_tokens_obey_literal_quoting(self):
        for tok in RETUNE_FOCUS_TOKENS:
            self.assertEqual(focus_forbidden_hits(tok), [])


class TestRetuneClausesMutation(unittest.TestCase):
    """Planted changes to in-memory copies of the real carriers must trip."""

    def _blk(self):
        return norm(_block("security"))

    def test_dropped_guarantee_clause_trips(self):
        planted = self._blk().replace(norm(RETUNE_BLOCK_CLAUSES[1]), "")
        self.assertEqual(retune_block_problems(planted), [RETUNE_BLOCK_CLAUSES[1]])

    def test_recapped_guarantee_clause_trips(self):
        planted = self._blk().replace("not under the sensitive-area cap",
                                      "under the sensitive-area cap")
        self.assertNotEqual(retune_block_problems(planted), [])

    def test_dropped_verify_today_phrase_trips(self):
        planted = self._blk().replace(" even when you verify it still holds today", "")
        self.assertNotEqual(retune_block_problems(planted), [])

    def test_dropped_helper_clause_trips(self):
        planted = self._blk().replace(norm(RETUNE_BLOCK_CLAUSES[0]), "")
        self.assertEqual(retune_block_problems(planted), [RETUNE_BLOCK_CLAUSES[0]])

    def test_helper_clause_widened_to_never_lift_trips(self):
        planted = self._blk().replace(
            "it lifts the cap only when the diff's own changed lines let the input through",
            "it never lifts the cap")
        self.assertNotEqual(retune_block_problems(planted), [])

    def test_misplaced_guarantee_clause_trips(self):
        g = norm(RETUNE_BLOCK_CLAUSES[1])
        planted = self._blk().replace(g, "")
        planted = planted.replace(norm(SAFE_CHANGE_CLAUSES[7]), norm(SAFE_CHANGE_CLAUSES[7]) + " " + g)
        self.assertEqual(retune_block_problems(planted), ["guarantee clause out of slot"])

    def test_focus_dropped_or_misplaced_trips(self):
        lit = _literal()
        helper, guarantee = RETUNE_FOCUS_TOKENS
        self.assertEqual(retune_focus_problems(lit.replace(guarantee, "")), [guarantee])
        self.assertEqual(retune_focus_problems(lit.replace(helper, "")), [helper])
        moved = lit.replace(" " + helper, "")
        moved = moved.replace("pre-existing gap", helper + " pre-existing gap", 1)
        self.assertEqual(retune_focus_problems(moved), ["helper clause out of slot"])
        recapped = lit.replace("not under the sensitive-area ceiling", "under the sensitive-area ceiling")
        self.assertNotEqual(retune_focus_problems(recapped), [])


# --------------------------------------------------------------------------- #
# Fix agent: the description tells the truth about the model pin (W2, D-12)
# --------------------------------------------------------------------------- #
TIER_WORDS = ("opus", "fable", "sonnet", "haiku")
FIX_MD_REL = os.path.join("agents", "fix.md")


def _frontmatter(text):
    """Line-based `key: value` pairs of the leading `---` block (no YAML lib)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    out = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        key, sep, value = line.partition(":")
        if sep and key.strip() and not key.startswith(" "):
            out[key.strip()] = value.strip()
    return {}


def fix_md_model_truth_holds(text):
    """True only when the description names the pinned tier and no other.

    The description is what the orchestrator and the owner read; the `model:`
    line is what actually runs. A description that names a different tier, or
    an environment variable that does not affect this agent, is a false claim.
    """
    fm = _frontmatter(text)
    model = fm.get("model", "")
    desc = fm.get("description", "")
    if not desc or model not in TIER_WORDS:
        return False
    if "VIBE_CHECK_TOP_MODEL" in desc:
        return False
    low = desc.lower()
    if not re.search(r"\b%s\b" % re.escape(model), low):
        return False
    for other in TIER_WORDS:
        if other != model and re.search(r"\b%s\b" % other, low):
            return False
    return True


class TestFixMdModelTruth(unittest.TestCase):
    """agents/fix.md's description matches its `model:` pin (FIX-04)."""

    def setUp(self):
        self.text = read(FIX_MD_REL)

    def test_description_matches_the_pin(self):
        self.assertTrue(fix_md_model_truth_holds(self.text))

    def test_mutant_model_changed_trips(self):
        mutant = self.text.replace("\nmodel: opus\n", "\nmodel: sonnet\n", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(fix_md_model_truth_holds(mutant))

    def test_mutant_env_override_claim_trips(self):
        fm_end = self.text.index("\nmodel: ")
        mutant = (self.text[:fm_end]
                  + " (or Fable via $VIBE_CHECK_TOP_MODEL)"
                  + self.text[fm_end:])
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(fix_md_model_truth_holds(mutant))

    def test_mutant_description_removed_trips(self):
        lines = self.text.split("\n")
        mutant = "\n".join(l for l in lines if not l.startswith("description:"))
        self.assertNotEqual(mutant, self.text)
        self.assertFalse(fix_md_model_truth_holds(mutant))


if __name__ == "__main__":
    unittest.main()
