# Finalize mode

> **Lazy-loaded.** Read from the command spine when `$ARGUMENTS` contains `--finalize`, after Phase 0 and Phase 0.5 (and the unconditional Phase 0.6) have run. Never read on a review pass.
> Shared: `/review` and `/deep-review` finalize through this one file.

**Who owns what.** `scripts/finalize_gate.py` decides which way finalize goes: write, route to the fix loop, enter the Medium acknowledgement loop, fall back, error, or refuse. This file computes the gate's inputs, renders every message, and writes REVIEW.md. The gate never produces REVIEW.md content and never prints a finding.

## Finalize mode

If `$ARGUMENTS` contains `--finalize`:
- Run Phase 0 and 0.5 to resolve scope and read state. Do NOT dispatch agents. Phase 0.5 binds `$STATE_FILE` to the mode-resolved state path (GSD `<$PHASE_ID>.json`, other-modes `<repo>-<branch>.json`, or `--all` `by-mode/all/<scope-hash>.json`) — Finalize consumes that one variable and never re-derives a path of its own.
- Compute current state from the state object parsed out of `$STATE_FILE`:
  - `outstanding_cw` = last pass's findings with band ∈ {critical, warning} AND status ≠ fixed-since-last
  - `unacknowledged_medium` = last pass's findings with band == medium AND no entry in state's `medium_acknowledgments`
- Compute the gate's inputs, then let `finalize_gate.py` pick the branch. Its input is exactly six keys, built with a JSON encoder (booleans as JSON `true`/`false`, counts as JSON integers):
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
  - List each: `{{file}}:{{line}} — {{title}}`
  - `outstanding-to-phase-5` → **Route into Phase 5 Step A** (**Read $VC_ROOT/phases/review/50-fix-loop.md** with the Read tool first) with the outstanding findings as the candidate set, so the user can apply fixes (auto / selected / by hand) and then choose at Step C whether to rerun or abandon. Do NOT write REVIEW.md or archive state — finalize stays blocked until a future invocation finds `outstanding_cw` empty.
  - `fallback` — Phase 5 is unavailable (e.g. `$TURINGMIND_NONINTERACTIVE` is set, or PR/range mode); fall back to the legacy behavior: tell user "Fix these, re-run with `--finalize`." and stop.
- `fallback` with `outstanding_cw` empty — the Medium acknowledgement loop needs an interactive Phase 5 too (its "Will fix" answer defers to Phase 5): list each unacknowledged Medium as `{{file}}:{{line}} — {{title}}`, tell the user "Acknowledge these interactively, or fix them, then re-run with `--finalize`." and stop. Do NOT write REVIEW.md or archive state.
- `medium-ack-loop` — `unacknowledged_medium` non-empty: enter acknowledgment loop. For each:
  - AskUserQuestion: "{{title}} at {{file}}:{{line}} — action?"
    - "Will fix" → defer to Phase 5: collect all "Will fix" Medium findings, then route into Phase 5 Step A (**Read $VC_ROOT/phases/review/50-fix-loop.md** with the Read tool first) with that set as the candidates. After Phase 5's Step C, the user picks rerun (loop continues) or abandon (state preserved, no REVIEW.md).
    - "Dismiss" → follow-up AskUserQuestion for reason, write `medium_acknowledgments[stable_hash] = {decision: "dismiss", reason: "<text>", at_pass: N}` to state root.
    - "Look again" → display `problem` + `current_code` + `fix_hint` (if present), then re-ask.
  - After loop:
    - Any "Will fix" → routed to Phase 5 above; finalize does NOT proceed this invocation.
    - All dismissed/acknowledged → `medium_acknowledgments` written to the state ROOT (`state.medium_acknowledgments`, the single canonical location — the same field the Dismiss write above targets); proceed to the write below.
- `write` (or the acknowledgement loop above ended with everything dismissed/acknowledged):
  - Write `.turingmind/REVIEW.md` per `templates/review-md-schema.md`.
  - Archive state: `mv "$STATE_FILE" "$STATE_FILE.archived-$(date +%Y-%m-%d)"` — using the Phase-0.5-resolved state path (`$STATE_FILE`), the same file Phase 4.5 wrote. The `by-mode/all/<scope-hash>.json` form makes each `--all` archived name unique, so archived snapshots never collide.
  - Print summary to user: path to `.turingmind/REVIEW.md` and reminder that it's gitignored — user must `cp` if they want it tracked.
- `refuse` — print "I'm uncertain about Finalize mode — finalize_gate.py refused its input" and stop. Do NOT write REVIEW.md or archive state.

### Writing REVIEW.md

Use Write to create `.turingmind/REVIEW.md` per `templates/review-md-schema.md`. Fill from state:

- `{{scope_label}}`: if GSD phase mode, "Phase {{$PHASE_ID}}"; else "<repo>/<branch>"
- `{{passes}}`: length of `state.passes`
- `{{deep_count}}` / `{{quick_count}}`: count passes by `mode`
- `{{commits}}`: `git rev-list --count $baseline..HEAD`
- `{{loc}}`: sum of additions+deletions across all passes
- Coverage table: aggregate `agents_run` and `findings` across passes
- "Critical issues resolved": findings with band=critical, status=fixed-since-last across all passes. Best-effort fix-commit lookup: `git log -L <line>,<line>:<file> | head -20` to find a commit that touched that line.
- "Medium findings — dismissed": from `state.medium_acknowledgments` (the state-ROOT field, the same location the Dismiss write targets and the `unacknowledged_medium` read consults, both above — NOT `state.passes[-1].medium_acknowledgments`, a per-pass path nothing writes; reading per-pass here would always find dismissals empty and silently drop them from REVIEW.md) with decision=dismiss

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
