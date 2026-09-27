# Phase 0, mode 5 — `--all` scope selection

> **Lazy-loaded.** Read from `phases/review/00-scope.md` when Phase 0 resolves to mode 5 — the branch-flip guard found `--all` (or a leading bare `all`) in `$SCOPE_ARGS`. This file is what binds `$ALL_MODE`; a plain diff review never reads it.
> Part of Phase 0 — no announcement of its own. In `--all` mode, Read this file before Phase 0's `✓ Phase 0 — Resolve scope` line.

**Who owns what.** `scripts/select_files.py` owns the regular-files-only git-mode filter and the skip-rule matcher (step c/d). The orchestrator owns the narrow parse, the containment guard, and the `git ls-files` call that feeds the script, and this file binds the variables later phases read.

5. **`--all` mode** — Resolve scope as follows:

   a. **Narrow parse (`$NARROW`).** The first non-flag token after `--all` **in `$SCOPE_ARGS`** (if any) is `$NARROW` — the path OR glob to narrow to (e.g. `--all src/api`, `--all '*.md'`, `--all 'src/**/*.ts'`). Derive `$NARROW` from `$SCOPE_ARGS`, NOT raw `$ARGUMENTS` (HIGH-C): the pre-mode normalizer has ALREADY stripped the universal `--codex <val>` / `--min-confidence <val>` pairs (but LEFT `--all`/`--full`/`--fix`/`--include-docs` in `$SCOPE_ARGS`), so the "first non-flag token after `--all`, skipping `--full`/`--fix`/`--include-docs`" logic below runs unchanged — only its INPUT changes from `$ARGUMENTS` to `$SCOPE_ARGS`. Because the universal pair is already gone from `$SCOPE_ARGS`, `--all --codex off` yields `$SCOPE_ARGS="--all"` → `$NARROW` EMPTY → whole tree (NOT the bogus `$NARROW="off"`); `--all --min-confidence 75` yields `$NARROW` EMPTY → whole tree (NOT `$NARROW="75"`); `--all src --codex off` yields `$SCOPE_ARGS="--all src"` → `$NARROW="src"`. In every case `--codex`/`--min-confidence` STILL reach config.py because Phase 0.6 parses them from `$ARGUMENTS`. `--full`, `--fix`, and `--include-docs` are recognized as independent composable flags and are NOT the narrow token (their `--all`-specific semantics land in later phases; Phase 7 just must not misparse them as the path). **Bind `--full` to a variable here** (mirroring the `$ALL_MODE=1` flag binding in step e below — the Phase-4 listing bar tests it at render time, so it MUST be a defined boolean, not a re-scan of `$ARGUMENTS`): set `$FULL=1` iff the `--full` token ∈ `$ARGUMENTS`, else `$FULL=0`. This binding is `$ALL_MODE`-only and adds NOTHING to the four diff handlers (Phase 0 modes 1-4). **Bind `--fix` to a variable here** (mirroring the `$FULL` binding above — the Phase-5 skip predicate tests it at fix-decision time, so it MUST be a defined boolean, not a re-scan of `$ARGUMENTS`): set `$FIX=1` iff the `--fix` token ∈ `$ARGUMENTS`, else `$FIX=0`. This binding is `$ALL_MODE`-only and adds NOTHING to the four diff handlers (Phase 0 modes 1-4). **Bind `--include-docs` to a variable here** (mirroring the `$FULL`/`$FIX` bindings above — the step-d skip-rule branch tests it at selection time, so it MUST be a defined boolean, not a re-scan of `$ARGUMENTS`): set `$INCLUDE_DOCS=1` iff the `--include-docs` token ∈ `$ARGUMENTS`, else `$INCLUDE_DOCS=0`. This binding is `$ALL_MODE`-only and adds NOTHING to the four diff handlers (Phase 0 modes 1-4). **`--include-docs` is the escape-hatch that restores prior whole-tree behavior** — it re-includes the doc/planning files (`.planning/`, `docs/`, `specs/`, top-level `README*`/`CHANGELOG*`) the default `--all` now excludes, so the default `--all` reviews source not docs and `--all --include-docs` reverts to the whole tree (SELECT-03). It is documented HERE because mode-5 step a is where `--all`'s flags are documented (the README carries no `--all` docs). If there is no non-flag token, `$NARROW` is EMPTY → review the whole tree. A `$NARROW` MAY legitimately contain `*` — a glob like `*.md` or `src/**/*.ts` is contractual input, so the guard below validates-and-passes a glob; it never silently drops a glob's matches.

   b. **Hardened containment guard for `$NARROW`** (skip this entire sub-step when `$NARROW` is empty — the whole-tree case has no user path to validate). This is a three-stage validate-then-contain guard modeled on the most-hardened in-repo example (the `deep-review.md` Codex path two-check, steps (b)→(d)). All three stages run, in order:

      (i) **Explicit `case` pre-reject (REQUIRED — the regex in (ii) does NOT cover `..`).** Reject `$NARROW` outright (clear error + stop) on ANY of: a leading `/` (absolute), a leading `-` (option-like), any `..` path segment (traversal), a leading `:` or ANY occurrence of a Git PATHSPEC-MAGIC token (`:`, `:(`, `:!`, `:^`) anywhere in the value, spaces, or shell metacharacters (`;` `|` `&` `$` backtick, plus `(` `)` `!` `^`):
      ```bash
      case "$NARROW" in
        /* | -* | *..* ) echo "Invalid --all path/glob (absolute, option-like, or '..' traversal) — refusing."; exit 1 ;;
        :* | *:\(* | *:!* | *:^* ) echo "Invalid --all path/glob (Git pathspec magic is not allowed) — refusing."; exit 1 ;;
        *' '* | *';'* | *'|'* | *'&'* | *'$'* | *'`'* | *'('* | *')'* | *'!'* | *'^'* ) echo "Invalid --all path/glob (shell metacharacter) — refusing."; exit 1 ;;
        *) : ;;   # OK so far: relative, no traversal, no pathspec magic, no metachar — continue to (ii)
      esac
      ```
      The leading-`:` and the `:(` / `:!` / `:^` arms are what FAIL CLOSED on Git pathspec-magic input: `--all ':(top)*'` (selects the whole repo) and `--all ':!plugins/**'` (excludes a subtree) PASS a guard that only checks `..`/absolute/metachar, silently broadening or narrowing the audit. They are now REJECTED, not expanded. NOTE: `*` is NOT in any reject arm — a glob is legal input; only the pathspec-magic chars (`:` `(` `)` `!` `^`) and the other shell metachars are rejected.

      (ii) **Regex allowlist pre-filter.** Additionally require `$NARROW` to match the EXACT allowlist `^[A-Za-z0-9._*/-]+$` — letters, digits, dot, underscore, **star** (so globs pass), slash, hyphen ONLY. Every character outside that class — including every pathspec-magic char (`:` `(` `)` `!` `^`) and every shell metachar — is rejected. The `*` IS in the allowlist on purpose (globs must narrow); the pathspec-magic chars are NOT, so an allowlisted value can NEVER carry its own pathspec magic — that invariant is what makes the orchestrator-supplied `:(literal)` / `:(glob)` prefix in (d) safe. As in the `deep-review.md` model, this regex is NOT sufficient alone — it does NOT stop `..` (every char of `a/../b` is in the class) — so the explicit (i) reject is REQUIRED and runs first.
      ```bash
      printf '%s' "$NARROW" | grep -Eq '^[A-Za-z0-9._*/-]+$' || { echo "Invalid --all path/glob (allowed: letters digits . _ * / -) — refusing."; exit 1; }
      ```

      (iii) **realpath-contain the LITERAL PREFIX of `$NARROW`** under `$(git rev-parse --show-toplevel)`. For a plain path the literal prefix is the whole value; for a glob it is the portion BEFORE the first `*` (e.g. for `src/**/*.ts` the literal prefix is `src/`; for a bare `*.md` the literal prefix is empty → resolves to the repo root, which IS contained). Mirror the GSD-mode containment (mode 4 in `00-scope.md`) / `deep-review.md` (d): set `CONTAINED` in each `case` arm, then act on the flag — a non-empty literal prefix that resolves OUTSIDE the toplevel is NOT contained → refuse.

      **Resolve WITHOUT requiring the prefix to exist on disk.** A legal in-repo glob can name a directory that is tracked-but-not-checked-out, or simply not materialized — BSD `realpath` (the macOS default, and macOS is this project's primary host) exits non-zero and prints nothing for a non-existent path, so a bare `realpath "$LITERAL_PREFIX"` would falsely refuse a legal scope like `src/**/*.ts`. The actual traversal guard is stage (i)'s explicit `..`/leading-`/` reject (already run); this stage only needs a missing-path-TOLERANT containment check — which is exactly `guard.py`'s contract (Fable A7/B2: this used to be an inline Python heredoc, the ONE copy of the ≥5 that failed safe; it is now the same tested source every other site calls). A relative `--path` resolves against `--root`, matching what the heredoc did. Do NOT gate containment on the path existing, and do NOT re-inline the check.
      ```bash
      ROOT=$(git rev-parse --show-toplevel)
      LITERAL_PREFIX="${NARROW%%\**}"          # everything before the first '*' ('' for a bare glob like *.md)
      if [ -z "$LITERAL_PREFIX" ]; then
        CONTAINED=1                            # empty prefix → repo root → contained
      elif [ -n "$GUARD_PY" ] && python3 "$GUARD_PY" --root "$ROOT" --path "$LITERAL_PREFIX"; then
        CONTAINED=1                            # guard.py exit 0 — contained (missing-path tolerant)
      else
        CONTAINED=0                            # escaped repo, OR $GUARD_PY unresolved (fail closed)
      fi
      [ "$CONTAINED" = 1 ] || { echo "--all narrow scope escaped the repo root — refusing."; exit 1; }
      ```

      **Then drive git with an ORCHESTRATOR-OWNED pathspec-magic prefix chosen by SCOPE SHAPE** (this is what fixes both the magic-injection vector AND keeps globs working — the orchestrator OWNS the `:(literal)`/`:(glob)` prefix; it is a fixed string the orchestrator selects by detecting `*`, and the user input can never supply its own magic because (i)+(ii) reject any `:`/`(`/`)`/`!`/`^`):
      - If `$NARROW` contains NO `*` (a plain path): use `:(literal)` — `git ls-files -s -z -- ":(literal)$NARROW"` — exact-path, wildcard-free, magic-free.
      - If `$NARROW` contains `*` (a glob): use `:(glob)` — `git ls-files -s -z -- ":(glob)$NARROW"` — so `*` / `**` perform standard glob matching. (LIVE-VERIFIED in this repo: `:(glob)*.md` and `:(glob)plugins/**/*.md` select correctly, whereas `:(literal)*.md` returns NOTHING — forcing `:(literal)` on a glob would silently under-select, so the prefix MUST be split by shape.)

      The `--` terminates option parsing; `$NARROW` is always double-quoted inside the pathspec and is NEVER interpolated into a command line. Net invariant: user-supplied pathspec magic stays REJECTED (fail closed), but a normal glob like `*.md` / `src/**/*.ts` narrows correctly.

   c. **Selection + regular-files-only filter (the candidate tracked set) — `scripts/select_files.py`.** List the candidate set with `git ls-files -s -z` — the `-s`/`--stage` form prints the git mode bits, and `-z` is NUL-delimited for robustness to odd filenames — and pipe the raw bytes into `select_files.py --raw`, which applies the mode filter AND the step-d skip rules in one pass and reports what each dropped. The pathspec is chosen by scope shape (step b):
      - whole tree (empty `$NARROW`): `git ls-files -s -z`
      - plain-path `$NARROW`: `git ls-files -s -z -- ":(literal)$NARROW"`
      - glob `$NARROW`: `git ls-files -s -z -- ":(glob)$NARROW"`

      ```bash
      PATHSPEC=()                                        # whole tree: no pathspec
      case "$NARROW" in
        '')   : ;;
        *\**) PATHSPEC=(-- ":(glob)$NARROW") ;;          # a glob — `*`/`**` must match
        *)    PATHSPEC=(-- ":(literal)$NARROW") ;;       # a plain path — exact, wildcard-free
      esac
      SELECT_ARGS=(--raw)
      [ "$INCLUDE_DOCS" = 1 ] && SELECT_ARGS+=(--include-docs)   # step d's docs/planning escape hatch
      if SELECTION=$(set -o pipefail; git ls-files -s -z "${PATHSPEC[@]}" \
                     | python3 "$VC_ROOT/scripts/select_files.py" "${SELECT_ARGS[@]}"); then
        printf '%s\n' "$SELECTION"
      else
        echo "--all selection failed (git ls-files or select_files.py exited non-zero) — review HALTED." >&2
        exit 1
      fi
      ```

      The script prints one JSON object: `review_set` (the surviving paths, lexicographic), `symlink_count`, `non_regular_count`, `skipped_count`. A non-zero exit, or stdout that does not parse as that object, is the halt above — never review a set the script could not derive.

      **The mode filter is a security control.** `select_files.py` keeps ONLY entries whose mode is `100644` (regular file) or `100755` (executable) and **DROPS entries whose mode is `120000` (symlink)** (and any other non-regular mode, e.g. a `160000` gitlink). This filter runs BEFORE any file-content read, so a tracked symlink can NEVER contribute its target's contents to the `<files>` block — `git ls-files` includes tracked symlinks, and reading one could follow a link OUTSIDE the repo and disclose local files. Dropped symlinks are noted as skipped/non-regular in the Phase-4 coverage note (their link text is not read in Phase 7 either). `Bash(git:*)` already permits `git ls-files -s` — no allowed-tool change.

      **Selection-time skip count — symlink bucket (`$SELECTION_SKIPPED_SYMLINK`)** = `symlink_count + non_regular_count` from the script — the entries the mode filter dropped, counted where the drop happens (this is NOT a second `git ls-files` pass). This bucket capture is `$ALL_MODE`-only (it lives inside this mode-5 `--all` branch) and adds NOTHING to the four diff handlers (Phase 0 modes 1-4). It is RECOMPUTED on a Phase-0.3 Narrow re-entry, because the narrowed scope has its own symlink drops.

   d. **Skip rules.** `select_files.py` (step c) applies the skip rules in `templates/skip-rules.md` — that template is the human-readable source of truth both `commands/review.md` and `commands/deep-review.md` reference, and a drift-lock test binds the script's table to it. Do not duplicate the list inline and do not re-match patterns by hand. It supersedes/extends triage's inline `files_to_skip` baseline. **Branch on `$INCLUDE_DOCS` (bound at step a):** `--include-docs` is passed to the script iff `$INCLUDE_DOCS=1`, and then ONLY the "Docs / planning / non-source" denylist category from `templates/skip-rules.md` is skipped — all OTHER denylist categories (vendored, generated/minified, lockfiles, binary/image) AND the allowlist override still apply; when `$INCLUDE_DOCS=0` (the default), the full `templates/skip-rules.md` INCLUDING the docs/planning category applies. The allowlist override applies in BOTH cases (it only ever KEEPS files, so it is harmless under `--include-docs`). This branch is `$ALL_MODE`-only and adds NOTHING to the four diff handlers (Phase 0 modes 1-4).

      **Selection-time skip count — skip-rule bucket (`$SELECTION_SKIPPED_RULE`)** = `skipped_count` from the script — the number of regular files excluded by the skip rules, counted where the exclusion happens (no second pass). The doc/planning drops are SKIP-RULE exclusions, so they already flow through this SAME `$SELECTION_SKIPPED_RULE` count — do NOT add a separate variable for them (D-02). When doc/planning files were among the drops, the Phase-0.3 render line (`03-estimate-gate.md`) names "docs/planning" as one of the reasons. This is `$ALL_MODE`-only (it lives inside this mode-5 `--all` branch), touches NONE of the four diff handlers, and is RECOMPUTED on a Phase-0.3 Narrow re-entry.

   e. **Set downstream variables.** After the symlink filter and skip rules, the surviving regular files are the reviewed set:
      - `$REVIEW_SET` = the surviving regular files — the script's `review_set` (the candidate set; later phases use it). NB: the `in_reviewed_set` finding-validity filter is NOT built here — it lives in Phase 3 step 2 and gates on the POST-triage dispatched union `$REVIEWED_UNION` (the per-chunk `$CHUNK_REVIEW_FILES_i` union, = the Phase-4 `{{R}}` set), NOT on this pre-triage `$REVIEW_SET`.
      - **Selection-time skipped count (`$SELECTION_SKIPPED_COUNT`) — SEPARATE pre-selection metadata, NOT the Phase-4 `{{S}}` set.** Set `$SELECTION_SKIPPED_COUNT = $SELECTION_SKIPPED_SYMLINK + $SELECTION_SKIPPED_RULE` — the SELECTION-TIME skip set (dropped symlinks from step c + skip-rule exclusions from step d), captured BEFORE `$REVIEW_SET` is built. Because these entries are removed BEFORE `$REVIEW_SET` exists, they are OUTSIDE the `{{T}} = $REVIEW_SET` denominator the Phase-4 coverage note uses, and they are therefore NOT the Phase-4 coverage `{{S}}` set (which is `{{S}} = {{T}} − {{R}}`, the files selected-but-not-dispatched, computed INSIDE `{{T}}`). `$SELECTION_SKIPPED_COUNT` and `{{S}}` are DISTINCT quantities measuring different things — pre-selection exclusions vs. selected-but-not-dispatched files — and MUST NOT be conflated, claimed equal, or folded into one another. This variable is CONSUMED by the Phase-0.3 estimate gate (the gate READS it and does NOT recompute the drops — D-04 "no new measurement in the gate"), and it is RECOMPUTED on a Phase-0.3 Narrow re-entry (the new scope has its own drops). FORWARD NOTE: the Phase-4 coverage note (`{{T}}`/`{{S}}`/`{{R}}`) is INTENTIONALLY left untouched here — its denominator precision (symlink/skip-rule reconciliation) is the deferred Phase-10 P10-C concern, not Phase 9's. This `$SELECTION_SKIPPED_COUNT` capture is `$ALL_MODE`-only and adds NOTHING to the four diff handlers (Phase 0 modes 1-4).
      - **Empty-set guard (early exit).** If `$REVIEW_SET` is EMPTY after selection + symlink filter + skip rules — a glob that matched nothing (e.g. `--all '*.nonexistent'`), a narrow path containing only symlinks/skipped files, or an all-skipped tree — print `No files matched the --all scope (the path/glob matched nothing, or every match was filtered as a symlink/skipped file).` and STOP, BEFORE the Phase-2 fan-out. Do NOT dispatch agents over an empty `<files>` block (wasted fan-out + a misleading "reviewed 0 files" report); this mirrors the four diff modes bottoming out on "no changes".
      - `$ALL_MODE=1` — the flag that gates the Phase-0.5 fresh-snapshot branch, the Phase-2 `<diff>`→`<files>` block swap, and the Phase-4 coverage note.
      - The existing Phase-2 bindings are REUSED via a conditional (not a rewrite): `{{filtered_file_list}}` ← `$REVIEW_SET` rendered as a name list, and `{{git_diff_output}}` ← the `<files>` block string (`$FILES_BLOCK`, built in Phase 2).
      - Leave `$PHASE_ID` / `$PHASE_DIR` UNSET — `--all` has no single-phase intent doc, so this correctly skips Phase 1.5 intent loading.
