# Phase 0.5 — `--all` state key (reserved subdirectory + fresh snapshot)

> **Lazy-loaded.** Read from `phases/review/05-state.md` when `$ALL_MODE` is set (bound by `00-scope-all.md`). A plain diff review never reads it.
> Part of Phase 0.5 — no announcement of its own. In `--all` mode, Read this file before Phase 0.5's `✓ Phase 0.5 — Multi-pass state check` line.

**Who owns what.** `scripts/statepath.py` is the ONE state-filename rule: it computes the `--all` key (and refuses an unsafe or missing component). This file calls it and binds `$STATE_FILE`; it never recomputes the key by hand.

(The `--all` branch needs NO slug: its `$BRANCH` feeds `shasum`, and a 12-hex digest never carries a slash.)

**`--all` mode (`$ALL_MODE` set) — reserved-subdirectory fresh-snapshot branch (additive; the two key lines in `05-state.md` are byte-untouched).** When `$ALL_MODE` is set, do BOTH of the following INSTEAD of the default state-key resolution and INSTEAD of Phase 0.5 steps 2-5:

  (i) **Structurally separate state key.** `--all` state lives under a RESERVED SUBDIRECTORY: `.turingmind/state/by-mode/all/<scope-hash>.json`. WHY a subdirectory and not a filename prefix: the default "other modes" key is a FLAT filename `<repo>-<branch>.json` directly under `.turingmind/state/`, so ANY flat all-mode filename — even `all-<hash>.json` — shares that grammar and CAN collide (a repo named `all` on branch `whole-tree` produces the default key `all-whole-tree.json`, byte-identical to a whole-tree `--all` key; git accepts both `whole-tree` and 12-hex branch names). A filename prefix is NOT a namespace. A subdirectory `by-mode/all/` can NEVER equal a flat filename no matter the repo/branch name, so the two namespaces are STRUCTURALLY disjoint. Define `<scope-hash>` so it (a) is a single deterministic value the code actually produces — comment and code must AGREE — and (b) includes repo+branch context so two repos sharing a `.turingmind/` (e.g. a mounted/NAS-shared state dir) do NOT collide on an identical `whole-tree` key. The scope-hash is ALWAYS a 12-hex digest of `<repo>:<branch>:<narrow-or-whole-tree-token>` — there is no verbatim-`whole-tree` filename. `statepath.py` computes it as `SCOPE_HASH` = `printf '%s' "${REPO}:${BRANCH}:${SCOPE_TOKEN}" | shasum | cut -c1-12` (SHA-1), where `SCOPE_TOKEN` is `$NARROW`, or the literal token `whole-tree` ONLY when `$NARROW` is empty; do not recompute it by hand:
  ```bash
  REPO=$(basename "$(git rev-parse --show-toplevel)")
  BRANCH=$(git branch --show-current)                    # hashed RAW — no slug (see the note above)
  # Serialize the components with a JSON encoder from argv (never string-built): a branch name may carry a quote.
  if ALL_STATE_FILE=$(set -o pipefail
       python3 -c 'import json,sys; print(json.dumps({"mode":"all","repo":sys.argv[1],"branch":sys.argv[2],"narrow":sys.argv[3]}))' \
         "$REPO" "$BRANCH" "${NARROW:-}" \
       | python3 "$VC_ROOT/scripts/statepath.py" \
       | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r["path"]) if r["path"] else sys.exit("statepath.py refused: " + r["reason"])'); then
    STATE_FILE="$ALL_STATE_FILE"      # the single canonical handle Finalize consumes (alias of the --all key)
    mkdir -p .turingmind/state/by-mode/all
  else
    echo "--all state key could not be resolved — review HALTED." >&2
    exit 1
  fi
  ```
  The resolved path is always `.turingmind/state/by-mode/all/<12hex>.json`. `statepath.py`'s refusal reasons are fixed strings and never echo the offending value.
  (Hashing repo+branch+scope means a whole-tree `--all` in repo A and in repo B yield DIFFERENT keys even in a shared `.turingmind/`, and `statepath.py` produces one deterministic key, read and written the same way within a run.) **Reserved-path guard (state in prose, enforced structurally):** default-mode state resolution (the GSD-mode and "other modes" branches in `05-state.md`) MUST NOT read or write anything under `.turingmind/state/by-mode/` — that subtree is reserved for mode-scoped state — and conversely the `--all` branch MUST NOT read or write a flat `.turingmind/state/<repo>-<branch>.json` file. Because the default branches build a FLAT filename and the `--all` branch builds a `by-mode/all/` path, a plain `/review` can NEVER resolve INTO the `by-mode/all/` subtree (and `--all` can never resolve out of it). The disjointness is a structural property of the path grammar, restated here as the guard.

  (ii) **Carry-forward bypass (fresh snapshot).** FORCE pass-1 / fresh-snapshot behavior UNCONDITIONALLY: `$PASS_NUMBER = 1`, `$LAST_REVIEWED_SHA = null`, `$CARRYFORWARD = []`, and SKIP Phase 0.5 steps 2-5 (parse / incremental-narrow / carry-forward) EVEN IF a `by-mode/all/<scope-hash>.json` file already exists from a prior run. This realizes design-spec §4 ("each `--all` run is a fresh snapshot — no carry-forward, no diff against a previous snapshot") and D-09's fresh-snapshot posture. The run still PROCEEDS to write its state file at `$ALL_STATE_FILE` in Phase 4.5 (so a same-run `--fix`/`--finalize` works), but it never diffs against a previous snapshot.

  **Net guarantee:** a plain `/review` run BEFORE and AFTER an `--all` run uses the SAME flat `<repo>-<branch>.json` file and the SAME carry-forward behavior it had before this feature — no cross-contamination in EITHER direction, and structurally impossible (not merely conventionally avoided) because the namespaces are a flat filename vs. a reserved subdirectory.
