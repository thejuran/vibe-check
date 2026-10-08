# Phase 0 — Resolve scope

> **Lazy-loaded.** Read from the command spine (`commands/review.md` or `commands/deep-review.md`) when Phase 0 is entered (every invocation, first, right after the spine head).
> Announce on entry, after this Read: `✓ Phase 0 — Resolve scope`.

**Neither the TRUST-01 resolver nor its seat lives here.** The seat line runs at the head of the command spine and the resolver body lives in `phases/shared/01-bootstrap.md`; both are reached before any phase, so `$VC_ROOT`, `$GUARD_PY`, `$CONFIG_PY` and `$SCORE_PY` are already bound when this file runs. Do not move either back into this file.

Parse `$ARGUMENTS`:

**Pre-mode universal-flag normalizer (`$SCOPE_ARGS`, runs FIRST — LEGIBLE-02, D-10, HIGH-A/HIGH-C).** BEFORE any mode detection (before the branch-flip guard below and before modes 1-5), derive `$SCOPE_ARGS` = `$ARGUMENTS` with the UNIVERSAL value-carrying flag tokens stripped out. `--codex` and `--min-confidence` are UNIVERSAL flags (they apply in ALL 5 modes and are parsed unconditionally at Phase 0.6), NOT positional scope args — but the mode detectors below classify/validate/derive the scope from the argument string, so an un-stripped universal flag poisons them (a `--codex off` tail contains a space and `-`, which the GSD-mode sandbox `^[A-Za-z0-9._-]+$` rejects; a flag-only call has a non-empty `$ARGUMENTS` so it would fall through the diff detectors into GSD/PR/range validation on the leftover flag; and a universal flag after `--all` gets mis-read as the mode-5 `$NARROW` path). So strip BOTH `--codex <val>` / `--codex=<val>` AND `--min-confidence <val>` / `--min-confidence=<val>` token pairs (the flag AND its value token, in both the space form and the `=` form — mirroring the Phase-0.6 parse grammar). Also strip the value-less `--finalize` token (whole token only, so a path or phase id containing that text is not rewritten): it is a spine-level mode flag the spines read from `$ARGUMENTS`, not a scope arg, and left in `$SCOPE_ARGS` it poisons the GSD sandbox ("Invalid phase id") or becomes a phase lookup ("Phase not found"). Then trim leading/trailing whitespace so a flag-only invocation yields `$SCOPE_ARGS=""` (a clean empty string, NOT `" "`). Strip ONLY these two universal flags plus `--finalize` — do NOT strip `--all`/`--full`/`--fix`/`--include-docs` (those are `$ALL_MODE` step-a tokens the mode-5 parse owns, and the branch-flip guard still needs to SEE `--all`; mode-5 step-a's skip-list still needs to SEE `--full`/`--fix`/`--include-docs` in `$SCOPE_ARGS` so its "first non-flag token" logic stays byte-stable). This normalizer COPIES-and-strips into `$SCOPE_ARGS`; it does NOT consume the tokens out of `$ARGUMENTS`, so `--codex`/`--min-confidence` still reach Phase 0.6 (which parses `$ARGUMENTS`) in EVERY mode — including the default diff and `--all` — and `--finalize` still reaches the command spine's finalize trigger.

```bash
# Strip the universal value-carrying flags (--codex / --min-confidence and their value token,
# both `--flag val` and `--flag=val` forms) out of $ARGUMENTS into $SCOPE_ARGS, then trim,
# so a flag-only invocation yields an EMPTY $SCOPE_ARGS. Also strip the value-less --finalize
# token, whole token only (a spine-level mode flag; $ARGUMENTS keeps it for the finalize trigger):
# after the squeeze every token is single-space delimited, so padding the ends gives whole-token
# matching. Leaves --all/--full/--fix/--include-docs intact.
SCOPE_ARGS=$(printf '%s' "$ARGUMENTS" \
  | sed -E 's/--codex[[:space:]]+[^[:space:]]+//g; s/--codex=[^[:space:]]+//g; s/--min-confidence[[:space:]]+[^[:space:]]+//g; s/--min-confidence=[^[:space:]]+//g' \
  | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/[[:space:]]+/ /g; s/^/ /; s/$/ /; s/ --finalize( --finalize)* / /g; s/^ //; s/ $//')
```

ALL SIX downstream scope-parsing sites classify/validate/derive scope from `$SCOPE_ARGS`, never raw `$ARGUMENTS`: (a) the branch-flip guard's bare-`all` alias rewrite and `--all`-contains test, (b) mode-1 default-diff selection (the "no positional scope arg" test is `$SCOPE_ARGS` EMPTY), (c) PR mode, (d) range mode, (e) the GSD-mode sandbox validator, (f) mode-5 step-a's `$NARROW` first-non-flag-token derivation. For any invocation carrying NO universal flag and no `--finalize` token, `$SCOPE_ARGS == $ARGUMENTS` and mode resolution is byte-identical to before.

**Branch-flip guard (`--all`, evaluated FIRST):** FIRST, normalize a bare `all` alias: if the FIRST token of `$SCOPE_ARGS` is exactly `all` (no dashes), treat it as `--all` for the remainder of Phase 0 — silently, with NO interactive disambiguation question or essay (LEGIBLE-01). Then, if `$SCOPE_ARGS` contains the `--all` token anywhere (now including a normalized leading `all`), go DIRECTLY to **mode 5** below and SKIP modes 1-4 entirely. `--all` is a branch-flip flag — it WINS over all four diff detectors (no-args / PR number / `..` range / GSD phase). In particular, a bare number after `--all` (e.g. `--all 42`) is a PATH, never a PR ref — the guard firing first prevents PR mode from matching; and because a lone leading `all` is normalized to `--all`, a number that FOLLOWS it (e.g. `all 42`) likewise remains a PATH token for mode-5 step a, never a PR ref — identical to `--all 42`. Scope the bare-`all` normalization to the FIRST token only, so a non-leading `all` (e.g. the second token in `--all all`, a legitimate narrow path component) is NOT rewritten. Modes 1-4 are reached ONLY when neither `--all` nor a leading bare `all` is present (no regression: a non-`--all`, non-`all` invocation resolves a diff exactly as before). **Composition with the universal-flag normalizer (the ONE new sentence the post-Fable rebase adds):** the normalizer runs FIRST and strips ONLY `--codex <val>` / `--min-confidence <val>` and the value-less `--finalize` (never `--all` or a bare leading `all`), so the bare-`all` alias rewrite operates on `$SCOPE_ARGS`'s first token and the `--all`-contains test reads `$SCOPE_ARGS` — the two are byte-identical in their first token unless that token is a universal flag (a flag-only call, which has no `all` alias to rewrite anyway). Thus `all --codex off` → `$SCOPE_ARGS="all"` → alias-rewrite → `--all` → mode 5 with `$NARROW` EMPTY (whole tree), with `--codex off` still reaching Phase 0.6 from `$ARGUMENTS`.

**One-line mode conclusion (LEGIBLE-02):** after resolving the mode/scope above, print EXACTLY ONE conclusion line `Mode: <resolved mode + scope>` and proceed — do NOT narrate the resolution reasoning, and do NOT ask a disambiguation question for an unambiguous alias (the bare-`all` normalization already resolves silently, so this line is the only resolution output the user sees). Example forms (exact wording is discretion within this behavioral bar): `Mode: --all (whole-tree, docs excluded)` / `Mode: --all --include-docs (whole-tree)` / `Mode: --all src/api (narrowed)` / `Mode: diff (uncommitted changes)` / `Mode: PR #42` / `Mode: range a..b` / `Mode: GSD phase 02-foo`. This is PROSE-tightening of the orchestrator's self-narration ONLY — it does NOT change WHICH mode is chosen; the five modes' selection logic below is byte-stable.

1. **No positional scope arg (default diff)** — selected when `$SCOPE_ARGS` is EMPTY (the branch-flip guard did not fire and neither PR/range/GSD matched `$SCOPE_ARGS`): review all uncommitted changes. This tests `$SCOPE_ARGS` being empty, NOT raw `$ARGUMENTS` — a flag-only invocation like `/review --min-confidence 75`, `/deep-review --codex off` or `/review --finalize` (the Close-out re-entry from a default-diff pass) has a non-empty `$ARGUMENTS` but an EMPTY `$SCOPE_ARGS`, so it MUST resolve the DEFAULT diff mode here (never fall through to PR/range/GSD validation on the leftover flag), while the flag token still reaches Phase 0.6 in `$ARGUMENTS` (HIGH-A). Assemble diff via:
   ```bash
   git diff HEAD
   git diff --staged
   git status --short
   ```
   If empty and `$ARGUMENTS` does NOT contain the `--finalize` token: print "No changes to review." and stop. On a `--finalize` run (whole token in `$ARGUMENTS`, e.g. Close out after a fix loop that committed every fix), an empty diff is expected: do NOT stop — continue to Phase 0.5, because Finalize reads `$STATE_FILE`, not the diff.

2. **PR mode** — `$SCOPE_ARGS` matches `^[0-9]+$` or contains `/pull/`:
   ```bash
   gh pr diff <ref> --patch
   gh pr view <ref> --json title,body,author,headRefName
   ```
   Stateless. No intent context.

3. **Range mode** — `$SCOPE_ARGS` matches `<ref>..<ref>`:
   ```bash
   git diff <range>
   ```
   Stateless.

4. **GSD phase mode** — `$SCOPE_ARGS` is a phase identifier (a phase directory name like `02-code-review` or just `02`).

   **⚠ GSD projects use TWO phase-dir layouts — resolve across both, never assume the flat one.** Phases live either flat under `.planning/phases/<N>-<slug>/` or **milestone-nested** under `.planning/milestones/<milestone>-phases/<N>-<slug>/` (common once a project has shipped milestones; some projects have NO `.planning/phases/` dir at all). Resolving only the flat layout makes this mode fail with "phase not found" on milestone-nested projects even though the phase plainly exists.

   **Validate first (sandbox guard).** Before any path lookup, reject `$SCOPE_ARGS` if it does not match `^[A-Za-z0-9._-]+$` — no slashes, no `..`, no spaces, no shell metacharacters. On reject, error: "Invalid phase id — must match `[A-Za-z0-9._-]+` (no slashes, no `..`)." and stop. This prevents `../../etc/passwd`-style escapes from the `.planning/` namespace, which would otherwise be propagated into shell commands, state file paths, and intent-doc reads. (The `<arg>` used in the resolution below is `$SCOPE_ARGS`, now flag-free — a `/deep-review 33 --codex off` invocation reaches here as `$SCOPE_ARGS="33"`, so the `--codex off` tail no longer trips this sandbox; the flag still reaches Phase 0.6 from `$ARGUMENTS`. Likewise `49-foo --finalize` (Close out from a GSD pass) reaches here as `$SCOPE_ARGS="49-foo"`.)

   Then resolve across both layouts — exact name first, then unique `<arg>-` prefix (e.g. `02` → `02-code-review`). The literal dash in `<arg>-*` keeps phase `1` from matching `10-foo`/`11-bar`; `-maxdepth 2` keeps find from descending into nested artifact trees:
   ```bash
   PHASE_DIR=$(find .planning/phases .planning/milestones -maxdepth 2 -type d \
                 -name "<arg>" 2>/dev/null | head -1)
   if [ -z "$PHASE_DIR" ]; then
     MATCHES=$(find .planning/phases .planning/milestones -maxdepth 2 -type d \
                 -name "<arg>-*" 2>/dev/null)
     [ "$(printf '%s\n' "$MATCHES" | grep -c .)" = "1" ] && PHASE_DIR="$MATCHES"
   fi
   ```
   - Unique match → `$PHASE_DIR` is set; continue.
   - Zero matches → error: "Phase '<arg>' not found under .planning/phases/ or .planning/milestones/. Available: <list dirs from both roots>".
   - Multiple matches → error listing them and stop — do not guess between an archived and an active copy of the same phase number.

   **After resolution, verify containment.** Confirm the resolved phase dir is a descendant of `.planning/` (the common root of both layouts) via the ONE tested guard (Fable A7/B2 — the old inline `case "$PHASE_REAL/" in "$PLANNING_ROOT/"*` copy failed OPEN when `cd .planning` failed and left `$PLANNING_ROOT` empty). `$PHASE_DIR` is CWD-relative (`find` output), so absolutize it with `$PWD` — guard.py resolves a RELATIVE `--path` against `--root`, which would double the `.planning/` prefix here:
   ```bash
   [ -n "$GUARD_PY" ] && python3 "$GUARD_PY" --root "$PWD/.planning" --path "$PWD/$PHASE_DIR" \
     || { echo "Phase resolution escaped .planning/ — refusing."; exit 1; }
   ```
   (Fail closed both ways: an empty `$GUARD_PY` short-circuits `&&` to the refusal arm, and a non-zero guard exit refuses.)

   Compute phase commit range (`$PHASE_DIR` is the path resolved above):
   ```bash
   PHASE_START=$(git log --reverse --format=%H -- "$PHASE_DIR" | head -1)
   if [ -z "$PHASE_START" ]; then
     echo "ℹ Phase dir '$PHASE_DIR' has no commit history yet — using staged + unstaged diff only for this pass."
     # Skip the $PHASE_START..HEAD portion below; fall back to staged + unstaged only.
     PHASE_RANGE=""
   else
     PHASE_RANGE="$PHASE_START..HEAD"
   fi
   ```
   Diff = `$PHASE_RANGE` (if non-empty) + staged + unstaged.

   Set `$PHASE_ID = $(basename "$PHASE_DIR")` for state and intent context — the directory *name*, layout-independent, so state files are identical whether the phase lives flat or milestone-nested. `$PHASE_DIR` (the full resolved path) is reused by Phase 1 (triage prompt) and Phase 1.5 (intent docs) — those phases must NOT re-derive it from `.planning/phases/`.

5. **`--all` mode** — reached only via the branch-flip guard above (the `--all` token is present in `$ARGUMENTS`). Whole-codebase selection over tracked files instead of a diff.

   When the branch-flip guard routes here, **Read $VC_ROOT/phases/review/00-scope-all.md** with the Read tool before continuing (and before announcing Phase 0) — it resolves the `--all` scope (narrow parse, containment guard, tracked-file selection, skip rules, and the `$ALL_MODE`/`$REVIEW_SET` bindings). `$ALL_MODE` is not bound yet at this point: that file binds it, so the `--all` token is the trigger here, not the variable. On a plain diff review, do not read it.
