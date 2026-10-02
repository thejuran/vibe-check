# Finalize mode

> **Lazy-loaded.** Read from the command spine when `$ARGUMENTS` contains `--finalize`, after Phase 0 and Phase 0.5 (and the unconditional Phase 0.6) have run. Never read on a review pass.
> Shared: `/review` and `/deep-review` finalize through this one file.

**Who owns what.** `scripts/finalize_gate.py` decides which way finalize goes: write, route to the fix loop, enter the Medium acknowledgement loop, fall back, error, or refuse. This file computes the gate's inputs, renders every message, and writes REVIEW.md. The gate never produces REVIEW.md content and never prints a finding.

## Finalize mode

If `$ARGUMENTS` contains `--finalize`:
- Run Phase 0 and 0.5 to resolve scope and read state. Do NOT dispatch agents. Phase 0.5 binds `$STATE_FILE` to the mode-resolved state path (GSD `<$PHASE_ID>.json`, other-modes `<repo>-<branch>.json`, or `--all` `by-mode/all/<scope-hash>.json`) — Finalize consumes that one variable and never re-derives a path of its own.
- Read the two gate counts from `carry_state.py` — never by hand. When there is no state file both counts are `0` and the helper is not run. Otherwise:
  1. **HEAD fingerprints.** For every entry of root `fix_verdicts` whose `at_pass == state.passes[-1].pass_number`, find its finding in `state.passes[-1].findings` by `stable_hash` and, for that finding's `<file>`, run `git rev-parse "HEAD:<file>"`, `git diff --quiet HEAD -- <file>` and `git diff --cached --quiet -- <file>`. Serialize `{"<file>": "<blob>"}` to `$BLOBFILE` with the Write tool, including a file ONLY when all three exit 0. A file whose rev-parse fails, or whose working tree or index differs from HEAD, is OMITTED: the fix agent judged working-tree content, so HEAD's blob is evidence only while HEAD, index and working tree are identical. Omission is how this file tells the helper "unbound" — the helper fails closed for an absent file and never runs git itself. With no last-pass fix verdicts `$BLOBFILE` holds `{}` and is still passed. The helper honours a fix-obsolete verdict ONLY while HEAD's blob equals the verdict's recorded `verified_blob`, so any edit after the verdict re-opens the finding.
  2. **Counts.**
     ```bash
     if COUNTS_JSON=$(python3 "$VC_ROOT/scripts/carry_state.py" finalize-counts --head-blobs "$BLOBFILE" < "$STATE_FILE"); then
       printf '%s\n' "$COUNTS_JSON"   # {"outstanding_cw", "unacknowledged_medium", "outstanding_cw_hashes", "unacknowledged_medium_hashes", "verified_obsolete_hashes"}
     else
       echo "I'm uncertain about Finalize mode — carry_state.py failed; nothing was written or archived." >&2
       exit 1
     fi
     ```
     `outstanding_cw` and `unacknowledged_medium` are read from `$COUNTS_JSON`; keep `$COUNTS_JSON` for the REVIEW.md fill below.
  What the helper counts (so nobody re-derives it by hand):
  - **Open** = the last pass's findings whose status is one of {new, persisted, needs-recheck}, PLUS every `members[].obligation` record those rows carry — a once-raised finding folded into a neighbour's row is its own obligation, deduplicated by its own `stable_hash`; a decision or fix-obsolete verdict on the LEAD row closes nothing for it.
  - **Closed** = has an entry in root `decisions`, OR in legacy root `medium_acknowledgments`, OR a `fix_verdicts` entry from the last pass whose `verified_blob` equals HEAD's blob for that file (per record, never inherited from a lead).
  - `outstanding_cw` = open, not closed, band critical or warning; `unacknowledged_medium` = the same for medium. Lows never block.
  An unresolved finding is counted on EVERY later pass with no expiry — a row the scorer marked `kept_open` (dropped by this pass's confidence/threshold filters) is as open as any other. The only exits are a verified resolution (`resolved[]` from score.py, or a last-pass fix-obsolete verdict whose code is unchanged) or an owner decision.
- Compute the gate's inputs, then let `finalize_gate.py` pick the branch. Its input is ONE JSON object whose only key is `flags`, and `flags` holds exactly the six keys below, built with a JSON encoder (booleans as JSON `true`/`false`, counts as JSON integers): `{"flags": {"state_file_present": true, "outstanding_cw": 0, "unacknowledged_medium": 0, "noninteractive": false, "pr_mode": false, "range_mode": false}}`. Passing the six keys bare, without the `flags` wrapper, is malformed input and the gate refuses it.
  - `state_file_present` — `[ -f "$STATE_FILE" ]`
  - `outstanding_cw`, `unacknowledged_medium` — the two counts above (`0` when there is no state file)
  - `noninteractive` — `$TURINGMIND_NONINTERACTIVE` is set to a truthy value
  - `pr_mode`, `range_mode` — Phase 0 resolved PR mode / range mode
  ```bash
  if FINALIZE_GATE_JSON=$(printf '%s' "$FINALIZE_GATE_INPUT_JSON" | python3 "$VC_ROOT/scripts/finalize_gate.py"); then
    printf '%s\n' "$FINALIZE_GATE_JSON"       # {"action": ..., "reason": ...}
  else
    echo "I'm uncertain about Finalize mode — finalize_gate.py failed; nothing was written or archived." >&2
    exit 1
  fi
  ```
  Branch on `action`. A non-zero exit is the halt above; any other `action` value, or stdout that does not parse, is treated as `refuse`.
- `error` — the state file is absent: error "No prior review passes. Run `/review` first."
- `outstanding-to-phase-5` / `fallback` with `outstanding_cw` non-empty:
  - Print: "Cannot finalize — {{N}} Critical/Warning findings remain:"
  - List each obligation whose hash is in `outstanding_cw_hashes` as `{{file}}:{{line}} — {{title}}`. **Join rule** (also used by the Medium loop for `unacknowledged_medium_hashes`): match the hash to a row of `state.passes[-1].findings` by `stable_hash`; when no row matches, match it to the `members[]` entry whose `obligation.stable_hash` equals it and render that member's file/line/title/agent, with the band read from `obligation.band`, and the suffix `(absorbed into "{{lead title}}" — decided on its own)`.
  - `outstanding-to-phase-5` → first ask, per listed obligation, one AskUserQuestion (4 options, neutral): "{{title}} at {{file}}:{{line}} ({{band}}) — action?"
    - **Will fix** → collect it into the Step A candidate set. For an absorbed obligation this collects its LEAD row — the site is the lead's; after the fix the next pass re-scores it, so the member resolves, is re-absorbed, or re-emerges as its own kept-open row.
    - **Dismiss** → follow-up AskUserQuestion for a reason.
    - **Defer** → follow-up AskUserQuestion for a reason. A deferred finding does not block REVIEW.md and is listed there.
    - **Look again** → display `problem` + `current_code` + `fix_hint` (if present), then re-ask.
    A reason must be non-empty; an empty answer re-asks.
  - After that loop:
    - Any Dismiss/Defer → record them (see "Recording decisions" below), then RE-RUN the counts step and the gate above. The gate decides again — this file never jumps to `write` on its own.
    - Any Will fix → **Route into Phase 5 Step A** (**Read $VC_ROOT/phases/review/50-fix-loop.md** with the Read tool first) with that set as the candidate set, so the user can apply fixes (auto / selected / by hand) and then choose at Step C whether to rerun or abandon. Do NOT write REVIEW.md or archive state — finalize stays blocked until a future invocation's gate returns `write`.
    - Everything decided and the re-run gate returns `write` → proceed to the write below.
    (A later version collapses these per-finding asks into one card; this loop is the minimal shape.)
  - `fallback` — Phase 5 is unavailable (e.g. `$TURINGMIND_NONINTERACTIVE` is set, or PR/range mode); fall back to the legacy behavior: tell user "Fix these, re-run with `--finalize`." and stop. No asks, no writes.
- `fallback` with `outstanding_cw` empty — the Medium acknowledgement loop needs an interactive Phase 5 too (its "Will fix" answer defers to Phase 5): list each unacknowledged Medium as `{{file}}:{{line}} — {{title}}` (join rule above), tell the user "Acknowledge these interactively, or fix them, then re-run with `--finalize`." and stop. Do NOT write REVIEW.md or archive state.
- `medium-ack-loop` — `unacknowledged_medium` non-empty: enter acknowledgment loop over the obligations whose hash is in `unacknowledged_medium_hashes` (join rule above). For each:
  - AskUserQuestion: "{{title}} at {{file}}:{{line}} — action?"
    - "Will fix" → defer to Phase 5: collect all "Will fix" Medium findings (an absorbed obligation collects its LEAD row), then route into Phase 5 Step A (**Read $VC_ROOT/phases/review/50-fix-loop.md** with the Read tool first) with that set as the candidates. After Phase 5's Step C, the user picks rerun (loop continues) or abandon (state preserved, no REVIEW.md).
    - "Dismiss" → follow-up AskUserQuestion for a reason (non-empty; an empty answer re-asks).
    - "Defer" → follow-up AskUserQuestion for a reason (non-empty; an empty answer re-asks). A deferred finding does not block REVIEW.md and is listed there.
    - "Look again" → display `problem` + `current_code` + `fix_hint` (if present), then re-ask.
  - After loop:
    - Any Dismiss/Defer → record them (see "Recording decisions" below).
    - Any "Will fix" → routed to Phase 5 above; finalize does NOT proceed this invocation.
    - Otherwise RE-RUN the counts step and the gate above; proceed to the write below only when the gate returns `write`.
  - `medium_acknowledgments` is a legacy, READ-only family: the helper still counts its entries as decisions, so an old medium-only state finalizes exactly as before. Nothing writes, migrates or rewrites it.
- `write` (only on the gate's `write`, including a re-run after decisions were recorded):
  - Write `.turingmind/REVIEW.md` per `templates/review-md-schema.md`.
  - Archive state: `mv "$STATE_FILE" "$STATE_FILE.archived-$(date +%Y-%m-%d)"` — using the Phase-0.5-resolved state path (`$STATE_FILE`), the same file Phase 4.5 wrote. The `by-mode/all/<scope-hash>.json` form makes each `--all` archived name unique, so archived snapshots never collide.
  - Print summary to user: path to `.turingmind/REVIEW.md` and reminder that it's gitignored — user must `cp` if they want it tracked.
- `refuse` — print "I'm uncertain about Finalize mode — finalize_gate.py refused its input" and stop. Do NOT write REVIEW.md or archive state.

### Recording decisions (the ONE write Finalize makes before REVIEW.md)

Serialize `{"at_pass": <passes[-1].pass_number>, "decisions": [{"stable_hash": "<full hash>", "decision": "dismiss"|"defer", "reason": "<owner text verbatim>"}]}` to a temp file with the Write tool (`$DECFILE`). The owner's reason is free text and NEVER goes on a command line — the same rule as `fixcommit.py`'s `--finding-json`. Then run under bash:
```bash
if python3 "$VC_ROOT/scripts/carry_state.py" record-decisions --decisions-file "$DECFILE" < "$STATE_FILE" > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"; then
  :
else
  rm -f "$STATE_FILE.tmp"
  echo "carry_state.py refused the decisions — state left unchanged; finalize stays blocked" >&2
  exit 1
fi
```
On a refusal: stop. Do NOT write REVIEW.md and do NOT edit the state by hand.

What the helper writes: root `decisions[<hash>] = {decision, reason, at_pass, band}` and nothing else, one record per finding — a later decision for the same hash replaces it. The band is read by the helper from the record: a row's own band, or an absorbed obligation's `obligation.band` (the helper accepts a member obligation's own hash). `fallback` (non-interactive / PR / range) never reaches this step: no asks, no writes.

### Writing REVIEW.md

Use Write to create `.turingmind/REVIEW.md` per `templates/review-md-schema.md`. Fill from state:

- `{{scope_label}}`: if GSD phase mode, "Phase {{$PHASE_ID}}"; else "<repo>/<branch>"
- `{{passes}}`: length of `state.passes`
- `{{deep_count}}` / `{{quick_count}}`: count passes by `mode`
- `{{commits}}`: `git rev-list --count $baseline..HEAD`
- `{{loc}}`: sum of additions+deletions across all passes
- Coverage table: aggregate `agents_run` and `findings` across passes
- "Critical issues resolved": `fixed_since_last` entries with band critical across all passes — nothing else. Best-effort fix-commit lookup: `git log -L <line>,<line>:<file> | head -20` to find a commit that touched that line.
- "Resolved by verification": the union of `passes[].resolved[]` across all passes, each rendered with its `resolution` object (source, agents, head_sha, at_pass, reason), PLUS the no-rerun fix-obsolete closures — every hash in `$COUNTS_JSON`'s `verified_obsolete_hashes` (the last-pass `fix_verdicts` entries whose fingerprint still matched HEAD; the helper already judged validity, this file never re-derives it), joined to its finding in `state.passes[-1].findings` by `stable_hash` and rendered with source `fix-obsolete`, agents `["fix"]`, HEAD = the verdict's `head_sha`, pass = the verdict's `at_pass`, reason = the verdict's `reason`. Deduplicate by `stable_hash` against the `resolved[]` entries (a verdict that also produced a `resolved[]` entry on a rerun is listed once). Use the `$COUNTS_JSON` from the gate step; the decisions step changes nothing about fix verdicts, so the helper is not re-run for this read.
- "Medium findings — dismissed" (Findings dismissed, any band): root `decisions` entries with decision == dismiss ∪ legacy root `medium_acknowledgments` entries with decision == dismiss. Both are state-ROOT fields — NOT `state.passes[-1].medium_acknowledgments` or `state.passes[-1].decisions`, per-pass paths nothing writes; reading per-pass here would always find dismissals empty and silently drop them from REVIEW.md.
- "Findings deferred": root `decisions` entries with decision == defer (ROOT-only, as above).
- For both the dismissed and deferred entries, join each decision's hash to `state.passes[-1].findings` by `stable_hash`; when no row matches, join it to the `members[]` entry whose `obligation.stable_hash` equals it (file/line/title/agent from the member, band from the decision record). An absorbed obligation's decision is listed under its own identity.

Filling REVIEW.md is READ-only over state: Finalize's only state write is the `record-decisions` step above; the archive `mv` follows the write as today.

If a prior `.turingmind/REVIEW.md` exists for a DIFFERENT phase, archive it first:
````bash
PRIOR_PHASE=$(grep -oE 'Phase [^ ]+' .turingmind/REVIEW.md | head -1 | cut -d' ' -f2)
# Defense in depth: REVIEW.md is parsed input — don't trust it. Same allowlist as Phase 0.
if [[ ! "$PRIOR_PHASE" =~ ^[A-Za-z0-9._-]+$ ]]; then
  PRIOR_PHASE="unknown"
fi
if [ -n "$PRIOR_PHASE" ] && [ "$PRIOR_PHASE" != "$PHASE_ID" ]; then
  mv .turingmind/REVIEW.md ".turingmind/REVIEW-${PRIOR_PHASE}-$(date +%Y-%m-%d).md"
fi
````
