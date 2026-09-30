# Phase 2c — Codex kickoff (facts → gate → launch)

> **Lazy-loaded.** Read from `commands/deep-review.md` when Phase 2c is entered: every deep review whose `$CONFIG_CODEX` is NOT `off`, after Phase 1d and before the Phase 2 fan-out turn. Under `off` the spine sets `CODEX_SKIPPED=1` and `CODEX_OFF=1`, announces the phase as skipped, and never reads this file — so `off` does no Codex plumbing at all: no probe, no gate, no smoke check, no launch, no collection.
> Announce on entry, after this Read: `✓ Phase 2c — Codex kickoff`.

**Who owns what.** `scripts/codex_gate.py` owns the decision — whether Codex runs, the reason slug when it does not, and the companion arguments when it does. Its nine reason slugs are its `SLUGS` constant; this file never re-types them. This file gathers the FACTS the gate needs with git and shell, launches Codex when the gate says run, and runs the launch-gated smoke check.

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
       timeout_binary "$TIMEOUT_OK" dirty "$DIRTY" phase_start_is_ancestor "$PHASE_START_OK" \
       head_is_upper "$HEAD_IS_UPPER" a_is_ancestor_of_b "$A_ANC_B" head_is_pr_head "$HEAD_IS_PR" \
       merge_base_matches_pr_base "$MB_OK" | python3 "$VC_ROOT/scripts/codex_gate.py"); then
     printf 'CODEX_DECISION=%s\n' "$CODEX_DECISION"      # {"action": "run"|"skip", "slug": ..., "codex_args": ...}
     printf 'CODEX_PLUGIN_ROOT=%s\nTIMEOUT_BIN=%s\n' "$CODEX_PLUGIN_ROOT" "$TIMEOUT_BIN"
   else
     echo "__CODEX_GATE_FAILED__"                        # the gate could not decide → do not launch
   fi
   ```
   Branch on the printed decision:
   - **`action: "skip"`** → set `CODEX_SKIPPED=1` and remember the `slug`. Print ONE skip-and-note line naming it (`⊘ Codex skipped: <slug> — native review continues`) and do nothing else in this phase: no disclosure line, no smoke check, no launch. Phase 3's Codex collection is a no-op. When the skip came from the missing watchdog (`timeout_binary` was false), add one hint: GNU coreutils provides `timeout`; on macOS `brew install coreutils` provides `gtimeout`.
   - **`__CODEX_GATE_FAILED__`** (the gate exited non-zero) → the same as a skip. Its slug is the one the gate returns for malformed input: `echo '{}' | python3 "$VC_ROOT/scripts/codex_gate.py"` prints it. Never launch on a gate failure.
   - **`action: "run"`** → continue with steps 2-4. `codex_args` is the companion's range arguments. It may contain the placeholder `<base-ref>`: replace it with THIS run's own resolved ref (`$PHASE_START` in GSD-range mode, `A` in range mode, the PR base ref in PR mode). `--base` is never derived from Codex output (D-08), and a working-tree decision carries no `--base` at all — passing `--base ""` would force branch mode and review the wrong range.

   Every skip degrades to a native-only review. A Codex limitation never blocks the native review and never runs a partial or different diff (SAFE-01).

2. **Disclosure line (CODEX-04) — print ONCE at kickoff, as text (not a tool call, not per poll):**
   `▶ Running Codex adversarial review in parallel (GPT-5-codex, ~1–3 min, deep-review only)…`

3. **Collection-mechanism smoke-check — LAUNCH-GATED (HIGH-B, SAFE-01/SAFE-02).** Runs ONLY on the `run` branch, immediately BEFORE the launch in step 4 — so it fires **iff Codex will actually launch**. The Codex pass is launched as a backgrounded shell and **collected** in Phase 3 by reading that shell's output; under the self-contained-watchdog design the launched shell **self-kills** the codex process at the cap, so `KillShell` is NOT on the critical path and the collection mechanism depends on exactly **one** built-in tool being callable: **`BashOutput`**. The smoke-check is **`BashOutput`-only** by design.

   **This is a REAL EXECUTION gate, not a prose claim. On the `run` branch the executor MUST actually run it once before trusting background collection:**
   - Launch a trivial command via `Bash(run_in_background: true)` that prints the fixed sentinel: `echo __SMOKE_OK__`. Capture the returned `shell_id`.
   - Read that backgrounded shell back with `BashOutput(shell_id)`.
   - **PASS** iff the `BashOutput` read is available AND the returned output contains the literal sentinel `__SMOKE_OK__` → proceed to the codex launch in step 4.
   - **FAIL CLOSED** otherwise. If `BashOutput` is not callable, or the read returns no output, that is a **structural blocker** that **blocks the LAUNCH** — surface the blocker and do NOT launch a Codex job whose output can never be collected (SAFE-02). Because the launch never happens, Phase 3 collect is a no-op and the review runs native-only; but on a genuine launch path a broken `BashOutput` is still fatal to the launch — the check keeps its full fail-closed force here.

   **Why launch-gated matters (HIGH-B):** every non-launching run (`off`, or any skip the gate decides) never reaches this step, so a native review that will not launch Codex is NEVER hard-blocked on missing `BashOutput` (it degrades to native-only per SAFE-01/SAFE-02). Record the smoke-check result (PASS/FAIL, and that `__SMOKE_OK__` was observed) in the run's evidence when it runs. `BashOutput`/`KillShell` are Claude Code **built-ins** and are **not** added to `allowed-tools` (only `Bash(node:*)` is). This probe edits no source — it runs `echo` and reads it back.

   > A live **authenticated** probe→launch→collect against real Codex is deferred to the efficacy phase (Phase 6, EFF-01). The `BashOutput` **callability** smoke-check above is NOT deferred — it is a structural gate run on a genuine launch path with a trivial `echo` (no Codex auth required).

4. **Background launch with a SELF-CONTAINED 300s watchdog (RESEARCH CORRECTION 2).** Only reached on the `run` branch after the smoke check passed. Record `started_at` (`date +%s`) at this kickoff. Make ONE `Bash(run_in_background: true)` call whose COMMAND wraps the codex invocation so the cap is enforced by the launched shell ITSELF, independent of when the orchestrator next polls. The single named constant is **`CODEX_TIMEOUT_SECONDS = 300`** (one named value, not scattered magic numbers). The cap is enforced with `timeout`/`gtimeout` (NOT a bare `sleep 300; kill <pid>`, which kills only the `node` wrapper and ORPHANS the spawned `codex`/GPT-5-codex child, so a hang INSIDE the child could outlive the cap). `timeout` propagates the kill to the spawned child tree — and signals the timeout via **exit code 124**, not a separately-echoed line, so there is no "payload printed then sentinel echoed" race. On the 124 exit the shell prints the stable **timeout sentinel** `__CODEX_TIMEOUT__`; on normal completion within the cap it prints the codex `--json` payload and exits 0. The payload is ALSO kept in `$CODEX_OUT`, so Phase 3 hands the file to `codex_translate.py` and never re-types Codex's bytes. Capture the returned shell id and the printed `CODEX_OUT` path for the Phase 3 collect step.
   ```bash
   # ONE run_in_background:true call. CODEX_TIMEOUT_SECONDS=300 (single named value).
   # Substitute CODEX_PLUGIN_ROOT and TIMEOUT_BIN as step 1 printed them, and the gate's codex_args
   # (with <base-ref> already replaced by this run's own ref) as the words after --json; the fixed
   # calibration literal CODEX_FOCUS is the final positional, after the gate's codex_args.
   CODEX_ACTION="<the decision's action>"
   CODEX_PLUGIN_ROOT="<printed in step 1>"; TIMEOUT_BIN="<printed in step 1>"
   # Fixed constant: never interpolate diff-derived, user- or Codex-derived text into it; passed as ONE array element.
   CODEX_FOCUS='Calibration rules for every finding, not a focus area: review the whole change as you normally would. (1) A change that tightens a control (adds or narrows an allowlist or denylist validator on an input, wraps output in an existing sanitizer or escaper, adds a bound or finite-only check to a numeric field, routes input through an existing clamping or parse helper) is safe on the axis it tightens unless you name a concrete bypass: a specific input value and the file:line path by which it defeats the case the new check is written to block. An input the pre-change code equally allowed is a pre-existing gap, not a defect of this change, only when it is a case the diff never addressed: report it at or below 0.45 confidence with severity low. An input the new check is written to block and demonstrably fails to block is a defect of this change at your honest confidence, even though the old code allowed it too. Rejecting inputs the old code accepted is the control working, not a regression, when the input lies outside what the input contract of the code supports (typed range, documented values, defaults); a concrete value the contract does support, traced through the new check to a specific failure at file:line, is a real regression whether or not that value occurs in the repository. Every other axis is reviewed normally. (2) A change that removes, reverts, loosens, disables or bypasses a control, or makes it depend on fragile or version-dependent configuration, is a real defect on a changed line when a path the control used to protect is left without it: report it at your honest confidence. A control moved rather than lost (the same check now enforced by shared middleware, a decorator, a schema or an upstream layer that every path to the old site still passes through) is not a removal: look for the replacement before reporting, and when you cannot tell whether one covers every path the old check guarded, report it at or below 0.45 confidence with severity low and say what would confirm it. (3) If a finding rests only on the changed code being in a sensitive area, with no defect shown on a changed line, set confidence at or below 0.45 and severity low (no demonstrated defect means no demonstrated consequence) and say what would demonstrate it. Still report it. At that confidence and severity the note stays below the Warning band even when corroborated and persisted. Off-hunk is not the same as unverified: repository context outside the change that you actually read counts as evidence, so an unchanged caller that demonstrably feeds attacker-controlled input into a changed sink is a defect on the changed line at your honest confidence.'
   ARGS=(adversarial-review --json <codex_args> "$CODEX_FOCUS")
   CODEX_OUT=$(mktemp)
   echo "CODEX_OUT=$CODEX_OUT"
   # The shell enforces the decision too, not just the reader: launch only on "run" with a watchdog.
   if [ "$CODEX_ACTION" = run ] && [ -n "$TIMEOUT_BIN" ]; then
     # -k 10 sends SIGKILL 10s after the initial SIGTERM in case the tree ignores TERM.
     "$TIMEOUT_BIN" -k 10 300 node "$CODEX_PLUGIN_ROOT/scripts/codex-companion.mjs" "${ARGS[@]}" > "$CODEX_OUT"
     rc=$?
     cat "$CODEX_OUT"
     # timeout signals the cap via exit 124 (NOT an echoed sentinel) → no completion-vs-echo race.
     if [ "$rc" = 124 ]; then echo __CODEX_TIMEOUT__; fi
   fi
   ```
   **The 300s ceiling is enforced by the background command's own watchdog, so a hung Codex self-terminates at `CODEX_TIMEOUT_SECONDS` even if the orchestrator does not poll for minutes** — the cap holds independent of poll timing; the orchestrator's later `BashOutput` read just observes the result-or-sentinel.

   **Calibration literal (Phase 42, AGENT-01/02).** The companion joins trailing positionals into its prompt's `User focus:` slot, so `CODEX_FOCUS` reaches Codex on every launch. It is written as calibration rules for every finding, not a topic, so Codex is not steered away from defects elsewhere in the change. Its `confidence ≤ 0.45` ceiling translates verbatim (`scripts/codex_translate.py`, ×100) to `agent_confidence ≤ 45`; because every capped note also carries `severity: low`, it scores at most 65 from a lone lane (below the Medium floor in `templates/scoring.md`) and at most 70 on any path at all (lone, Codex-corroborated, persisted from a previous pass, or both: 45 + 20 + 10 + 15 − 20), so a sensitive-area note never reaches the Warning band and never blocks finalize without an acknowledgment path (`scripts/test_agent_prompts.py` proves both against the real scorer). This literal is the ONLY runtime carrier of the rule for Codex — the contract `agents/codex-adversarial.md` documents it but is not read at runtime. Changing its wording is a measurement confound and must be pre-registered in `docs/efficacy/RESULTS-v2.10.md` before any B3 run.

**Two corrections baked in (do NOT revert them to older wording).** Probe with `setup --json` and gate on `.ready == true` — **NOT** `status --json` (which exits 0 even when Codex is uninstalled/logged-out and checks no auth, so it cannot gate). Background the launch with Claude Code `Bash(run_in_background: true)`, **NOT** the companion's `--background`/`--wait` (which `adversarial-review` ignores — it always foregrounds and prints no job-id).
