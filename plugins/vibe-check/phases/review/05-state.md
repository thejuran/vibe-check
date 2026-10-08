# Phase 0.5 — Multi-pass state check

> **Lazy-loaded.** Read from the command spine (`commands/review.md` or `commands/deep-review.md`) when Phase 0.5 is entered (every mode, after Phase 0).
> Announce on entry, after this Read: `✓ Phase 0.5 — Multi-pass state check`.

State file path. Bind the resolved path to ONE canonical variable, `$STATE_FILE`, so every downstream consumer (Phase 4.5 persist, Finalize read/archive) reads the SAME handle regardless of mode — Finalize must NOT re-derive a path:
- GSD phase mode: `.turingmind/state/<$PHASE_ID>.json` where `$PHASE_ID` is the **full resolved directory name** from Phase 0 (e.g. `02-real-data-path`, NOT `02`). Use the resolved name verbatim — do NOT abbreviate to the prefix the user typed. Abbreviating means a second invocation looking for `02-real-data-path.json` won't find a state written as `02.json`, and carry-forward silently restarts from pass 1. Bind: `STATE_FILE=".turingmind/state/${PHASE_ID}.json"`.
  - ✓ Correct: `.turingmind/state/02-real-data-path.json`, `.turingmind/state/31-cache-invalidation-renderer-config-epoch-and-awaited-purge-a.json`
  - 🚫 Wrong: `.turingmind/state/02.json`, `.turingmind/state/31.json`
- Other modes (no args / PR / range): `.turingmind/state/<repo>-<branch-slug>.json`, where `<branch-slug>` is the current branch with every `/` replaced by `-`. **The slug step is MANDATORY (Fable A9/B1):** branch names legally contain `/` (`feat/x`, `release/1.2`), and interpolating the raw name (the old form) produced a SLASHED path — not "a FLAT filename directly under `.turingmind/state/`" — which (a) broke the flat-vs-`by-mode/` disjointness guarantee below (counter-example: repo `by`, branch `mode/all/<12hex>` collided byte-for-byte with the reserved `--all` key grammar), (b) ENOENT'd on write since Phase 0.7 only creates `.turingmind/state/` itself, and (c) diverged from the dash-named files actually on disk, silently restarting carry-forward from pass 1. Bind:
  ```bash
  BRANCH_SLUG=$(git branch --show-current | tr '/' '-')
  STATE_FILE=".turingmind/state/$(git rev-parse --show-toplevel | xargs basename)-${BRANCH_SLUG}.json"
  ```

If `$ALL_MODE` is set, **Read $VC_ROOT/phases/review/05-state-all.md** with the Read tool before continuing — in `--all` mode it REPLACES the state-key resolution above with the reserved-subdirectory key and forces a fresh snapshot. On a plain diff review, do not read it.

1. If state file absent: pass 1, `$LAST_REVIEWED_SHA = null`. **Run Phase 0.6 (Resolve config) FIRST** (it is unconditional — the `$CONFIG_*` vars MUST be bound before any consumer), THEN proceed to Phase 0.7 (first-run setup will create `.turingmind/state/` if needed), then to Phase 1. Skip the rest of Phase 0.5.

   If state file present: skip Phase 0.7 (already initialized) and continue with step 2 below.

   **Phase 0.6 invariant (applies to EVERY Phase 0.5 exit).** Phase 0.6 (Resolve config) is unconditional and MUST run before ANY Phase 0.5 exit reaches Phase 0.7, Phase 1, or Phase 3 — so `$CONFIG_THRESHOLDS`/`$CONFIG_DISABLED`/`$CONFIG_TOP_MODEL`/`$CONFIG_MIN_CONFIDENCE`/`$CONFIG_IDIOM_FLOOR`/`$CONFIG_CODEX`/`$CONFIG_WARNINGS` are ALWAYS bound before any consumer (the Phase-2 Selection table, the Phase-3 score.py envelope, the Phase-4 config-health line, and `/deep-review`'s Phase-2c dispatch). This holds for the early-exit paths below (step 1's absent-state jump and step 5's carry-forward-only jump), NOT only the normal straight-through flow.

2. If present: parse it.
   - `$PASS_NUMBER = state.passes[-1].pass_number + 1`
   - `$LAST_REVIEWED_SHA = state.passes[-1].head_sha`
   - `$CARRYFORWARD = state.passes[-1].findings` filtered to status in `["new", "persisted", "needs-recheck"]`. **Do NOT add `"audit"` to this allowlist (impact-01):** the synthetic bare-`// vibe-ignore` "suppression" finding `score.py` emits carries `status: "audit"` precisely so it is EXCLUDED here — it is REGENERATED fresh each pass from the live window scan, so carrying it forward would double-count it and (with its empty `current_code`) mis-classify it as `needs-recheck`/`fixed-since-last`. Its absence from this allowlist is what makes it regenerated-not-carried; it still renders (the Suppression audit section selects by `category == "suppression"`, not status) and still passes the Phase 3/4 structural gates (which key on band/orchestrator_score/stable_hash, not status).
     A carried row carrying `kept_open` (score.py re-emitted it after this pass's filters dropped it) is carried like any persisted/needs-recheck row — its status is one of those, so the allowlist above does not change.
   - `$FIX_VERDICTS_PREV` = the entries of the root `fix_verdicts` object (absent ⇒ none) whose `at_pass == state.passes[-1].pass_number`, each as `{stable_hash: <its key>, at_pass, head_sha, verified_blob, reason, head_blob}`. `head_blob` is read NOW for the finding's `file` (joined from `state.passes[-1].findings` by `stable_hash`) as the output of `git rev-parse "HEAD:<file>"`, and is `null` when ANY of these holds:
     - `<file>` fails path validation, checked BEFORE any git call on it (the finding's `file` comes from the reviewed diff and may be attacker-authored): it must match `^[A-Za-z0-9._/-]+$` (the PATH_RE pre-filter `agents/fix.md` step 0 uses) AND `python3 "$GUARD_PY" --root "$(git rev-parse --show-toplevel)" --path "<file>"` must exit 0 (`$GUARD_PY` from `$VC_ROOT/phases/shared/01-bootstrap.md`; branch on the EXIT CODE; an unresolved/empty `$GUARD_PY` refuses). A rejected path is never passed to git — none of the three commands below runs for it;
     - the rev-parse exits non-zero (file deleted or renamed);
     - `git diff --quiet HEAD -- <file>` exits non-zero (unstaged edits);
     - `git diff --cached --quiet -- <file>` exits non-zero (staged edits).

     The two cleanliness checks are load-bearing (codex rewrite-3 high): the fix agent Reads the WORKING TREE and this very phase reviews staged + unstaged changes (step 3), so a HEAD blob only describes what the agent judged while the file is byte-identical across HEAD, index and working tree. A dirty file is reported as `null`, score.py rejects the verdict as changed evidence and the finding stays open for an ordinary recheck. The prose collects these facts; neither the helper nor the scorer runs git. `head_blob` is the current fingerprint of the code the fix agent judged: score.py accepts the verdict only while it equals `verified_blob` (an intervening edit — committed or not — re-opens the finding, codex high). Older `fix_verdicts` entries (`at_pass` below the last pass) are ignored — never resurrected. Phase 3 forwards `$FIX_VERDICTS_PREV` into the score.py envelope.
   - The state root may also carry `decisions` (Finalize-written via `carry_state.py record-decisions`). Phase 0.5 reads it for nothing here: an owner decision never removes a finding from `$CARRYFORWARD` (D-02: no expiry; closure is a Finalize-gate concept).

3. Narrow diff to incremental: `$LAST_REVIEWED_SHA..HEAD` + staged + unstaged.

4. If incremental diff empty AND `$CARRYFORWARD` empty AND `$ARGUMENTS` does NOT contain the `--finalize` token: print "No new changes since pass {{$PASS_NUMBER - 1}}." and stop. A `--finalize` run never stops here: it continues to Phase 0.6 and Finalize (the spine's finalize flow), which reads `$STATE_FILE`, not the diff.

5. If incremental diff empty but `$CARRYFORWARD` non-empty: **run Phase 0.6 (Resolve config) FIRST** — so `$CONFIG_THRESHOLDS`/`$CONFIG_DISABLED`/`$CONFIG_TOP_MODEL`/`$CONFIG_MIN_CONFIDENCE`/`$CONFIG_IDIOM_FLOOR`/`$CONFIG_CODEX`/`$CONFIG_WARNINGS` are bound before Phase 3 sources `$CONFIG_THRESHOLDS` / `$CONFIG_MIN_CONFIDENCE` / `$CONFIG_IDIOM_FLOOR` into the score.py envelope and Phase 4 renders `$CONFIG_WARNINGS` — THEN skip agent dispatch and proceed directly to Phase 3 carry-forward check. (Without this, a repo WITH a valid `.vibe-check.toml` would silently drop its config on this carry-forward-only path, violating "reads config ONCE per run on EVERY mode".)
