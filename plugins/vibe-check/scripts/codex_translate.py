"""codex_translate.py — the ONE executable owner of Family 3: Codex output
sanitization and translation into the vibe-check finding shape.

Phase 40 (DIET-02, Family 3). This is a BEHAVIOR-PRESERVING extraction of the
translation step that lived as prose in TWO places at once:
`agents/codex-adversarial.md` (the contract: the `agent_notes` carry at :32, the
per-finding field map at :46-60, the title-sanitization rule at :110-122) and
`commands/deep-review.md` (the restatement at :317-321 and the path two-check at
:323-346). A restated rule is a rule that drifts; the codepoint list and the
field map are now stated once, here, and tested.

Two OPPOSITE postures live in this module, and the difference is deliberate:

  * `title` is COSMETIC, not a security boundary — so it gets sanitize-and-KEEP
    (codex-adversarial.md:110-122). The finding is NEVER dropped over its title;
    only the spoofing/injection codepoints are removed. Dropping findings over
    title characters would let a crafted title suppress a real defect.
  * `file` IS a security boundary — it drives the fix agent's reads and edits
    (deep-review.md:323-346). Any validation failure DROPS the finding and
    appends a FIXED note. The note never echoes the rejected path: echoing it
    would re-smuggle the unvalidated bytes into `agent_notes`, which is rendered.

The ONE codepoint list (do not restate it anywhere else):
  - line boundaries: `\\n`, `\\r`, U+2028 LINE SEPARATOR, U+2029 PARAGRAPH
    SEPARATOR  -> single-line reduction (keep the first segment)
  - deleted outright: backtick (and thus code fences), ASCII controls
    U+0000-U+001F and U+007F, bidi controls U+202A-U+202E and U+2066-U+2069,
    zero-width / BOM U+200B-U+200D and U+FEFF
  - KEPT: `=` (CRITICAL, codex-adversarial.md:122 — `shell=True` /
    `verify=False` titles must stay committable by the fix agent), spaces,
    quotes, parentheses, commas, and every other printable character including
    ordinary non-ASCII letters.

The display class here is deliberately WIDER than the commit-construction
allowlist (`fixcommit.TITLE_ALLOWED`, `[A-Za-z0-9 ._:/()#=,-]`), which
additionally rejects `"` and `'` (a comma is admitted there by owner decision
D-16). That is not a disagreement to reconcile: a commit subject is constructed,
and a quote is not demonstrably safe at a construction site. Do NOT re-widen the
commit allowlist to admit quotes or apostrophes. `test_codex_translate.TestAllowlistRelationship`
pins the relationship in the one direction that must hold: every character the
commit class permits survives this sanitizer unchanged.

`why_it_matters` is PINNED to the body verbatim. The contract row
(codex-adversarial.md:60) allows "the impact clause of `body`, or restate
concisely from `recommendation`" — a judgement an LLM makes and a script cannot.
Rather than paraphrase, this module carries the body, which is always a truthful
superset of its own impact clause. Deterministic beats lossy.

Purity (keep-list D-08, mirroring score.py / chunks.py / select_files.py): the
pure functions do NO git, filesystem or shell I/O. The diff file set and the
repo root arrive as DATA from the orchestrator's bash. The single exception is
the containment leg, which delegates to the ONE tested `guard.py` (its
`os.path.realpath` is the only I/O in the whole import graph) rather than
re-inlining the `case "$REAL/" in "$ROOT/"*` compare that drifted across five
call sites (Fable A7/B2, A10/B3). Import set is EXACTLY {json, re, sys, guard};
the AST import-set test enforces it.

I/O: JSON envelope on stdin -> JSON envelope on stdout. The __main__ shim fails
CLOSED — unparseable stdin propagates so the process exits non-zero and the
orchestrator skips Codex rather than joining an object it could not derive.
"""

import json
import re
import sys

import guard

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
NOTE_CAP = 300  # codex-adversarial.md:32 — the summary -> agent_notes cap.

AGENT_NAME = "codex-adversarial"  # top-level, NEVER a per-finding key.

# deep-review.md:346 (f) — FIXED string. Never interpolate the rejected path.
DOWNGRADE_NOTE = "codex finding downgraded: file path failed validation"

# Line/paragraph boundaries for the single-line reduction. U+2028/U+2029 are
# included because renderers and string libraries that treat them as breaks
# would otherwise let a second line survive an ASCII-only truncation
# (codex-adversarial.md:114).
_LINE_BOUNDARIES = re.compile("[\n\r  ]")

# Codepoints deleted outright (codex-adversarial.md:118):
#   `           backtick, and therefore code fences (```)
#   \x00-\x1F   ASCII controls
#   \x7F        DEL
#   ​-‍, ﻿   zero-width / BOM
#   ‪-‮           bidi embedding/override controls
#   ⁦-⁩           bidi isolate controls
#                 separators (also handled above; deleted here so a
#                           non-leading occurrence cannot survive)
_STRIP_CHARS = re.compile(
    "[`\x00-\x1f\x7f​-‍﻿‪-‮⁦-⁩  ]"
)

# deep-review.md:334 (c) — the regex pre-filter. NOT sufficient alone: every
# character in `../../.git/hooks/pre-commit` is in this class, so the explicit
# `..` reject in _structurally_rejected must run too.
_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


# --------------------------------------------------------------------------- #
# Sanitization
# --------------------------------------------------------------------------- #
def sanitize_title(value):
    """Sanitize-and-KEEP a Codex title (codex-adversarial.md:110-122).

    Strips a trailing period, reduces to the first line, deletes the
    spoofing/injection codepoints, and strips surrounding whitespace. Never
    raises and never signals rejection: a non-string degrades to "" because the
    caller must KEEP the finding regardless of its title.
    """
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if text.endswith("."):
        text = text[:-1]
    text = _LINE_BOUNDARIES.split(text, 1)[0]
    text = _STRIP_CHARS.sub("", text)
    return text.strip()


def cap_note(value):
    """Reduce a Codex `summary` to ONE line of at most NOTE_CAP characters.

    codex-adversarial.md:32 — the cap is MANDATORY, not optional: a multi-line
    summary is a report-spoofing surface. It is necessary but NOT sufficient, so
    the value stays inert display data downstream (deep-review.md:321).
    """
    if not isinstance(value, str):
        return ""
    return _LINE_BOUNDARIES.split(value, 1)[0][:NOTE_CAP]


# --------------------------------------------------------------------------- #
# Path two-check — deep-review.md:323-346
# --------------------------------------------------------------------------- #
def _structurally_rejected(path):
    """(b) Explicit pre-containment rejects the (c) regex does NOT cover."""
    if path.startswith("/"):        # absolute
        return True
    if path.startswith("-"):        # option-like
        return True
    return ".." in path.split("/")  # ANY dot-dot SEGMENT


def path_ok(path, diff_files, root=None):
    """Apply the full path two-check. -> bool (no reason string is returned).

    Deliberately returns only a boolean: the downgrade note is a FIXED string,
    so a per-failure reason would be an unused channel that invites someone to
    start interpolating the path into it later. Order follows
    deep-review.md:329-341 — (b) structural, (c) regex, (a) diff-set membership,
    (d) containment. (d) is skipped only when no root is supplied; every other
    leg always runs.
    """
    if not isinstance(path, str) or not path:
        return False
    if _structurally_rejected(path):
        return False
    if not _PATH_RE.match(path):
        return False
    if path not in diff_files:
        return False
    if root is not None:
        # The ONE tested containment check. An empty/unresolvable root refuses
        # inside guard.contained (fail closed), which is why the empty-$ROOT
        # fail-open cannot come back here.
        is_in, _reason = guard.contained(root, path)
        if not is_in:
            return False
    return True


# --------------------------------------------------------------------------- #
# Translation — codex-adversarial.md:46-60, deep-review.md:317
# --------------------------------------------------------------------------- #
def translate_finding(idx, finding):
    """Map ONE Codex finding into the pre-backfill vibe-check finding shape.

    `idx` is 1-based. `current_code` / `in_diff` / `silenced_marker_nearby` are
    deliberately ABSENT: review.md Phase 3 step 0/2 backfills them for every
    agent once the object joins the response set (deep-review.md:317). Emitting
    them here would let a Codex-supplied value reach a consumer before the
    orchestrator's schema hard-rule-#4 override runs.
    """
    confidence = finding.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        confidence = 0
    recommendation = finding.get("recommendation")
    if not isinstance(recommendation, str) or not recommendation:
        recommendation = None
    return {
        "id": "codex-%03d" % idx,
        "file": finding.get("file"),
        "line": finding.get("line_start"),
        "title": sanitize_title(finding.get("title")),
        "category": "adversarial",
        "cwe": None,
        "severity": finding.get("severity"),
        # Verbatim: no Codex-specific floor and no severity penalty
        # (codex-adversarial.md:58) — a score adjustment would be a scoring
        # change, which this milestone forbids.
        "agent_confidence": int(round(confidence * 100)),
        "problem": finding.get("body"),
        # PINNED to the body — see the module docstring. Not a paraphrase.
        "why_it_matters": finding.get("body"),
        "fix_hint": recommendation,
        "intent_doc_match": None,
    }


def translate(result, diff_files, root=None):
    """Translate a Codex `payload.result` into ONE synthetic agent-response.

    Returns the pre-backfill top-level object from the contract's worked example
    (codex-adversarial.md:135): `agent` and `agent_notes` are siblings of
    `findings`, and no object inside `findings[]` carries an `agent` key.

    `verdict == "approve"` emits ZERO findings — a zero-finding agent is valid
    and still joins the set (deep-review.md:316). Any other verdict translates
    every finding that survives the path two-check; a finding that fails is
    DROPPED (the contract's permitted variant of downgrade) with one fixed note
    appended per drop. `next_steps` is dropped entirely.
    """
    result = result if isinstance(result, dict) else {}
    diff_set = set(diff_files or ())
    notes = []
    summary = cap_note(result.get("summary"))
    if summary:
        notes.append(summary)

    findings = []
    if result.get("verdict") != "approve":
        raw = result.get("findings")
        for finding in raw if isinstance(raw, list) else []:
            if not isinstance(finding, dict):
                notes.append(DOWNGRADE_NOTE)
                continue
            if not path_ok(finding.get("file"), diff_set, root):
                # Fixed note ONLY. Never echo the rejected path.
                notes.append(DOWNGRADE_NOTE)
                continue
            findings.append(translate_finding(len(findings) + 1, finding))

    return {"agent": AGENT_NAME, "findings": findings, "agent_notes": notes}


# --------------------------------------------------------------------------- #
# Envelope
# --------------------------------------------------------------------------- #
def run(envelope):
    """{"result": {...}, "diff_files": [...], "root": "<abs>"} -> translated."""
    return translate(
        envelope.get("result"),
        envelope.get("diff_files") or [],
        envelope.get("root"),
    )


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY process I/O. Fails CLOSED on bad input.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Do NOT wrap json.load in a swallowing try/except: an unparseable stdin
    # must propagate so the process exits NON-ZERO and the orchestrator skips
    # Codex rather than joining an object it could not derive.
    json.dump(run(json.load(sys.stdin)), sys.stdout, allow_nan=False)
