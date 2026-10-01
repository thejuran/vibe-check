# Phase 2c — Codex kickoff (facts → gate → launch)

> **Lazy-loaded.** Read from `commands/deep-review.md` when Phase 2c is entered: every deep review whose `$CONFIG_CODEX` is NOT `off`, after Phase 1d and before the Phase 2 fan-out turn. Under `off` the spine sets `CODEX_SKIPPED=1` and `CODEX_OFF=1`, announces the phase as skipped, and never reads this file — so `off` does no Codex plumbing at all: no probe, no gate, no collection directory, no launch, no collection.
> Announce on entry, after this Read: `✓ Phase 2c — Codex kickoff`.

**Who owns what.** `scripts/codex_gate.py` owns the decision — whether Codex runs, the reason slug when it does not, and the companion arguments when it does. Its ten reason slugs are its `SLUGS` constant; this file never re-types them. This file gathers the FACTS the gate needs with git and shell, creates the private collection directory when the gate says run, then launches Codex.

**Run this as its OWN turn(s) BEFORE the Phase 2 native fan-out turn. It is text + Bash only — it never adds a tool call to the pure-Task Phase 2 turn.** Phase 2's **MANDATORY DISPATCH SHAPE** (`$VC_ROOT/phases/review/20-dispatch.md`: one assistant turn = exactly N parallel `Task` calls, zero other tool calls) forbids any non-Task tool call in that turn, so the probe/launch Bash MUST live in a prior turn. Codex is a separate orchestrator-run step launched here and **collected at Phase 3** — never one of the parallel `Task` calls.

In order:

0. **`on` marker.** If `$CONFIG_CODEX == on`, set `CODEX_ON=1`. That marker is the ONLY `on`-specific behavior: Phase 3 reads it to render a skip outcome line in the PROMINENT style. `on` takes the SAME decision as `auto` (run iff available AND representable) — it NEVER forces a launch onto a skip the gate decides (D-09/Pitfall 3). `auto` (the default) is unchanged.

1. **Gather the facts and ask the gate (one Bash call).** The rule the gate implements: run Codex ONLY when its representable review range provably EQUALS the Phase-0-resolved diff for the active mode, else skip and run native-only. A wrong skip costs a second opinion; a wrong run silently misses defects Codex never saw, because the Phase-3 `in_diff` clip can drop extra findings but cannot recover unreviewed ones. `codex_gate.py` fails closed on anything it cannot decide — an unknown mode, a missing fact, or a fact that is not a JSON boolean — so every fact below is exactly `true` or `false`. Substitute the values Phase 0 resolved and the `$VC_ROOT` the bootstrap printed:
   ```bash
   # Mode, from Phase 0's resolution: all (--all) | default (no args) | gsd-empty-range | gsd-range | pr | range.
   CODEX_MODE="<mode>"
   PHASE_START="<gsd-range only: the phase's start ref>"
   RANGE_A="<range only: A of A..B>"; RANGE_B="<range only: B of A..B>"
   PR_HEAD_SHA="<pr only: headRefOid from gh pr view <ref> --json headRefOid,baseRefName,baseRefOid>"
   PR_BASE_REF="<pr only: the local ref for baseRefName>"; PR_DIFF_BASE="<pr only: baseRefOid>"

   # Companion path: newest versioned cache dir (.../codex/<version>), sort -V, marketplace fallback.
   # `find`, not a `*/` glob: zsh aborts the command on a glob that matches nothing.
   CODEX_PLUGIN_ROOT=$(find "$HOME/.claude/plugins/cache/openai-codex/codex" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort -V | tail -1)
   if [ -z "$CODEX_PLUGIN_ROOT" ] || [ ! -f "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" ]; then
     CODEX_PLUGIN_ROOT="$HOME/.claude/plugins/marketplaces/openai-codex/plugins/codex"
   fi
   INSTALLED=false; AUTHENTICATED=false; AVAILABLE=false
   if [ -f "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" ]; then INSTALLED=true; fi

   # Probe with `setup --json` ONLY when the companion exists — never run node against a path proven absent.
   # installed=false when the probe reports .codex.available == false; authenticated=false when it reports
   # .auth.loggedIn == false; available=true only on exit 0 AND parseable JSON AND .ready == true.
   if [ "$INSTALLED" = true ]; then
     if PROBE=$(node "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" setup --json 2>/dev/null); then PROBE_RC=0; else PROBE_RC=$?; fi
     PROBE_FACTS=$(printf '%s' "$PROBE" | python3 -c '
   import json, sys
   rc = int(sys.argv[1])
   try:
       p = json.load(sys.stdin)
   except ValueError:
       p = None
   if not isinstance(p, dict):
       print("true true false"); sys.exit(0)
   codex = p.get("codex") if isinstance(p.get("codex"), dict) else {}
   auth = p.get("auth") if isinstance(p.get("auth"), dict) else {}
   print("false" if codex.get("available") is False else "true",
         "false" if auth.get("loggedIn") is False else "true",
         "true" if rc == 0 and p.get("ready") is True else "false")' "$PROBE_RC")
     read -r INSTALLED AUTHENTICATED AVAILABLE <<< "$PROBE_FACTS"
   fi

   # The watchdog needs timeout/gtimeout; without one the 300s cap is inexpressible.
   TIMEOUT_BIN=$(command -v timeout || command -v gtimeout)
   TIMEOUT_OK=false; if [ -n "$TIMEOUT_BIN" ]; then TIMEOUT_OK=true; fi

   # Codex never launches without its calibration text; decided here, before the disclosure and the launch.
   FOCUS_OK=false; if [ -n "$(cat "$VC_ROOT/templates/codex-focus.txt" 2>/dev/null)" ]; then FOCUS_OK=true; fi

   # Range facts. Only the active mode's facts are consulted; the rest stay false.
   DIRTY=false; PHASE_START_OK=false; HEAD_IS_UPPER=false; A_ANC_B=false; HEAD_IS_PR=false; MB_OK=false
   if [ -n "$(git status --porcelain --untracked-files=no)" ]; then DIRTY=true; fi   # staged or unstaged changes
   HEAD_SHA=$(git rev-parse HEAD)
   case "$CODEX_MODE" in
     gsd-range)
       if git merge-base --is-ancestor "$PHASE_START" HEAD 2>/dev/null; then PHASE_START_OK=true; fi ;;
     range)
       B_SHA=$(git rev-parse --verify --quiet "$RANGE_B^{commit}")
       if [ -n "$B_SHA" ] && [ "$HEAD_SHA" = "$B_SHA" ]; then HEAD_IS_UPPER=true; fi
       if git merge-base --is-ancestor "$RANGE_A" "$RANGE_B" 2>/dev/null; then A_ANC_B=true; fi ;;
     pr)
       if [ -n "$PR_HEAD_SHA" ] && [ "$HEAD_SHA" = "$PR_HEAD_SHA" ]; then HEAD_IS_PR=true; fi
       MB=$(git merge-base HEAD "$PR_BASE_REF" 2>/dev/null)
       if [ -n "$MB" ] && [ "$MB" = "$PR_DIFF_BASE" ]; then MB_OK=true; fi ;;
   esac

   # Envelope built with a JSON encoder from argv, never string-spliced. A value other than
   # true/false passes through as a string, and the gate refuses it (fail closed).
   if CODEX_DECISION=$(python3 -c '
   import json, sys
   a = sys.argv[1:]
   b = {"true": True, "false": False}
   print(json.dumps({"mode": a[0], "facts": {k: b.get(v, v) for k, v in zip(a[1::2], a[2::2])}}))' \
       "$CODEX_MODE" installed "$INSTALLED" authenticated "$AUTHENTICATED" available "$AVAILABLE" \
       timeout_binary "$TIMEOUT_OK" focus_readable "$FOCUS_OK" dirty "$DIRTY" phase_start_is_ancestor "$PHASE_START_OK" \
       head_is_upper "$HEAD_IS_UPPER" a_is_ancestor_of_b "$A_ANC_B" head_is_pr_head "$HEAD_IS_PR" \
       merge_base_matches_pr_base "$MB_OK" | python3 "$VC_ROOT/scripts/codex_gate.py"); then
     printf 'CODEX_DECISION=%s\n' "$CODEX_DECISION"      # {"action": "run"|"skip", "slug": ..., "codex_args": ...}
     printf 'CODEX_PLUGIN_ROOT=%s\nTIMEOUT_BIN=%s\n' "$CODEX_PLUGIN_ROOT" "$TIMEOUT_BIN"
   else
     echo "__CODEX_GATE_FAILED__"                        # the gate could not decide → do not launch
   fi
   ```
   Branch on the printed decision:
   - **`action: "skip"`** → set `CODEX_SKIPPED=1` and remember the `slug`. Print ONE skip-and-note line naming it (`⊘ Codex skipped: <slug> — native review continues`) and do nothing else in this phase: no disclosure line, no collection directory, no launch. Phase 3's Codex collection is a no-op. When the skip came from the missing watchdog (`timeout_binary` was false), add one hint: GNU coreutils provides `timeout`; on macOS `brew install coreutils` provides `gtimeout`. When the slug is `focus-unreadable`, `templates/codex-focus.txt` could not be read (or was empty) — Codex never launches without its calibration text.
   - **`__CODEX_GATE_FAILED__`** (the gate exited non-zero) → the same as a skip. Its slug is the one the gate returns for malformed input: `echo '{}' | python3 "$VC_ROOT/scripts/codex_gate.py"` prints it. Never launch on a gate failure.
   - **`action: "run"`** → continue with steps 2-4. `codex_args` is the companion's range arguments. It may contain the placeholder `<base-ref>`: replace it with THIS run's own resolved ref (`$PHASE_START` in GSD-range mode, `A` in range mode, the PR base ref in PR mode). `--base` is never derived from Codex output (D-08), and a working-tree decision carries no `--base` at all — passing `--base ""` would force branch mode and review the wrong range.

   Every skip degrades to a native-only review. A Codex limitation never blocks the native review and never runs a partial or different diff (SAFE-01).

2. **Disclosure line (CODEX-04) — print ONCE at kickoff, as text (not a tool call, not per poll):**
   `▶ Running Codex adversarial review in parallel (GPT-5-codex, ~1–3 min, deep-review only)…`

3. **Private collection directory — run branch only, its OWN foreground Bash turn (SAFE-02).** Runs ONLY on the `run` branch, after the disclosure line and BEFORE the launch in step 4. The collection mechanism depends on no harness tool: the plugin owns a private directory, the step-4 launch writes Codex's payload and then its exit status into it, and Phase 3 reads those files with plain Bash. Writing a sentinel into the directory and reading it back is the real-execution check, so a Codex job is never launched whose output could not be collected.
   ```bash
   CODEX_DIR=$(mktemp -d)
   if [ -n "$CODEX_DIR" ] && [ -d "$CODEX_DIR" ] && printf '%s\n' __COLLECT_OK__ > "$CODEX_DIR/probe" && [ "$(cat "$CODEX_DIR/probe")" = __COLLECT_OK__ ]; then
     printf 'CODEX_DIR=%s\nSTARTED_AT=%s\n' "$CODEX_DIR" "$(date +%s)"
   else
     echo __CODEX_COLLECT_UNAVAILABLE__   # the directory could not be created or read back → do not launch
   fi
   ```
   Branch on the printed result:
   - **`CODEX_DIR=…` and `STARTED_AT=…`** → remember both values and continue to step 4. `STARTED_AT` is the kickoff time Phase 3's bounded wait counts from.
   - **`__CODEX_COLLECT_UNAVAILABLE__`** → collection unavailable: set `CODEX_SKIPPED=1` with the gate's existing `unavailable` slug, print `⊘ Codex skipped: unavailable — native review continues`, and do NOT launch. Phase 3's Codex collection is a no-op.

   A skip decided in step 1 never reaches this step, so a skip leaves no temp directory behind. The directory is not removed when the review ends (a measurement run copies the payload afterwards); `mktemp -d` creates it under `$TMPDIR` with a unique name and owner-only permissions.

4. **Background launch with a SELF-CONTAINED 300s watchdog (RESEARCH CORRECTION 2).** Only reached on the `run` branch after step 3 printed `CODEX_DIR` and `STARTED_AT`. Make ONE `Bash(run_in_background: true)` call whose COMMAND wraps the codex invocation so the cap is enforced by the launched shell ITSELF, independent of when Phase 3 starts waiting. The single named constant is **`CODEX_TIMEOUT_SECONDS = 300`** (one named value, not scattered magic numbers). The cap is enforced with `timeout`/`gtimeout` (NOT a bare `sleep 300; kill <pid>`, which kills only the `node` wrapper and ORPHANS the spawned `codex`/GPT-5-codex child, so a hang INSIDE the child could outlive the cap). `timeout` propagates the kill to the spawned child tree and signals the cap with **exit code 124**, which the launch records as the rc value `124` — not a separately-echoed line, so there is no "payload printed then sentinel echoed" race. The payload goes to `$CODEX_DIR/payload.json` (`$CODEX_OUT`), Codex's stderr to `$CODEX_DIR/stderr` (never echoed into the session), and the exit status LAST, to `$CODEX_DIR/rc` by temp file + rename, so `rc` existing means the payload is complete. No background-task handle is captured and the orchestrator never reads the background shell's output: Phase 3 reads `rc`, then hands `payload.json` to `codex_translate.py`, so Codex's bytes are never re-typed.
   ```bash
   # ONE run_in_background:true call. CODEX_TIMEOUT_SECONDS=300 (single named value).
   # Substitute CODEX_PLUGIN_ROOT and TIMEOUT_BIN as step 1 printed them, and the gate's codex_args
   # (with <base-ref> already replaced by this run's own ref) as the words after --json; the fixed
   # calibration text CODEX_FOCUS is the final positional, after the gate's codex_args.
   CODEX_ACTION="<the decision's action>"
   CODEX_PLUGIN_ROOT="<printed in step 1>"; TIMEOUT_BIN="<printed in step 1>"
   VC_ROOT="<printed by the bootstrap>"
   CODEX_DIR="<printed in step 3>"; STARTED_AT="<printed in step 3>"
   # Fixed text read byte-for-byte from the plugin's own file, never retyped here; never interpolate
   # diff-derived, user- or Codex-derived text into it; passed as ONE array element.
   # Step 1's focus_readable fact already decided readability; this empty-read guard is only a backstop.
   CODEX_FOCUS=$(cat "$VC_ROOT/templates/codex-focus.txt" 2>/dev/null)
   if [ -z "$CODEX_FOCUS" ]; then echo __CODEX_FOCUS_MISSING__; CODEX_ACTION=skip; fi
   if [ "$CODEX_ACTION" = skip ] && [ -n "$CODEX_DIR" ]; then printf 'focus-missing\n' > "$CODEX_DIR/rc.tmp" && mv "$CODEX_DIR/rc.tmp" "$CODEX_DIR/rc"; fi
   ARGS=(adversarial-review --json <codex_args> "$CODEX_FOCUS")
   # The shell enforces the decision too, not just the reader: launch only on "run" with a watchdog.
   if [ "$CODEX_ACTION" = run ] && [ -n "$TIMEOUT_BIN" ]; then
     # The payload lives in the private collection directory step 3 created.
     CODEX_OUT="$CODEX_DIR/payload.json"
     echo "CODEX_OUT=$CODEX_OUT"
     # -k 10 sends SIGKILL 10s after the initial SIGTERM in case the tree ignores TERM.
     "$TIMEOUT_BIN" -k 10 300 node "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" "${ARGS[@]}" > "$CODEX_OUT" 2> "$CODEX_DIR/stderr"
     rc=$?
     # Written last and renamed atomically: Phase 3 never reads a half-written rc. 124 = the cap.
     printf '%s\n' "$rc" > "$CODEX_DIR/rc.tmp" && mv "$CODEX_DIR/rc.tmp" "$CODEX_DIR/rc"
   fi
   ```
   Readability of the calibration file is decided in step 1 (the `focus_readable` fact → the gate's `focus-unreadable` slug), so a missing file is normally a labeled skip before the disclosure line and the launch. The `__CODEX_FOCUS_MISSING__` guard above is only a backstop for a file that vanished between step 1 and this launch: nothing launched and no `payload.json` was created. The line after the guard writes the marker `focus-missing` to `$CODEX_DIR/rc` (temp file + rename), so the marker reaches Phase 3 through the rc FILE and Phase 3's collection step 2 maps it to the `focus-unreadable` slug (`⊘ Codex skipped: focus-unreadable`), native-only. Never launch Codex without its calibration text.

   **The 300s ceiling is enforced by the background command's own watchdog, so a hung Codex self-terminates at `CODEX_TIMEOUT_SECONDS` even if the orchestrator does not look for minutes** — the cap holds independent of when Phase 3 starts waiting; the orchestrator's later read of `$CODEX_DIR/rc` just observes the result.

   **Calibration literal (Phase 42, AGENT-01/02).** The text lives in `templates/codex-focus.txt` and the launch reads it with `cat`, so it reaches Codex byte-for-byte rather than retyped. The companion joins trailing positionals into its prompt's `User focus:` slot, so `CODEX_FOCUS` reaches Codex on every launch. It is written as calibration rules for every finding, not a topic, so Codex is not steered away from defects elsewhere in the change. Its `confidence ≤ 0.45` ceiling translates verbatim (`scripts/codex_translate.py`, ×100) to `agent_confidence ≤ 45`; because every capped note also carries `severity: low`, it scores at most 65 from a lone lane (below the Medium floor in `templates/scoring.md`) and at most 70 on any path at all (lone, Codex-corroborated, persisted from a previous pass, or both: 45 + 20 + 10 + 15 − 20), so a sensitive-area note never reaches the Warning band and never blocks finalize without an acknowledgment path (`scripts/test_agent_prompts.py` proves both against the real scorer). This literal is the ONLY runtime carrier of the rule for Codex — the contract `agents/codex-adversarial.md` documents it but is not read at runtime. Changing its wording is a measurement confound and must be pre-registered in `docs/efficacy/RESULTS-v2.10.md` before any B3 run.

**Two corrections baked in (do NOT revert them to older wording).** Probe with `setup --json` and gate on `.ready == true` — **NOT** `status --json` (which exits 0 even when Codex is uninstalled/logged-out and checks no auth, so it cannot gate). Background the launch with Claude Code `Bash(run_in_background: true)`, **NOT** the companion's `--background`/`--wait` (which `adversarial-review` ignores — it always foregrounds and prints no job-id).
