---
name: Skip Rules
---

# Skip Rules

Applied by the orchestrator during `--all` whole-tree selection, after `git ls-files`
and before the `<files>` block is built.

## Single source of truth

This file is the **canonical, single source of truth** for the skip patterns the `--all`
whole-codebase mode applies. `commands/review.md` references this list DIRECTLY from its Phase-0
mode-5 `--all` selection step (via the plugin's prose-pointer convention — e.g. "apply the skip
rules in `templates/skip-rules.md`"). `commands/deep-review.md` references it INDIRECTLY, by
INHERITANCE: `/deep-review` executes `review.md`'s Phase 0 verbatim (it has no separate `--all`
selection step of its own), so the same pointer applies through that delegation. **Do NOT
duplicate this list inline** in either command. A skip-rule change lands here, once, and both
commands inherit it — so the two files cannot silently drift apart (the exact cross-file drift
bug this review tool exists to catch).

## Relationship to triage

The baseline floor is the inline `files_to_skip` pattern set in `agents/triage.md` (line 29).
This snippet **supersedes and extends** that baseline for `--all` selection: every pattern triage
already skips is skipped here too, plus the additional vendored/binary patterns below.

`agents/triage.md` itself is left **untouched** in Phase 7 — it is named here only as the baseline
floor. Consolidating triage's inline list into this snippet (so triage points here rather than
carrying its own copy) is an explicit later-cleanup discretion item, not Phase 7 work.

## Skip patterns

A tracked file is excluded from the `--all` reviewed set if it matches any DENYLIST pattern below
**UNLESS** it also matches the allowlist override at the bottom of this file — the allowlist WINS
(see "Keep these (allowlist override — wins over the denylist)"). There are now **five denylist
groups** (vendored, generated/minified, lockfiles, binary/image, docs/planning) plus **one
allowlist override**. The exact extension set within each denylist category is non-exhaustive and
may grow.

### Vendored / dependency directories

Skip any file under these directories:

- `node_modules/`
- `vendor/`
- `.venv/`
- `dist/`
- `build/`
- `.next/`
- `__pycache__/`
- `target/`

### Generated / minified output

- `*.min.js`
- `*.min.css`
- `*.map`
- `*.snap`
- (plus everything under the `dist/`, `build/`, `.next/`, `target/` dirs above)

### Lockfiles

- `*.lock`
- `*-lock.json`
- `*.lockb`
- `package-lock.json`
- `pnpm-lock.yaml`
- `yarn.lock`
- `Cargo.lock`
- `go.sum`
- `poetry.lock`

### Binary / image / font / archive

- `*.bin`
- `*.png`
- `*.jpg`
- `*.jpeg`
- `*.gif`
- `*.ico`
- `*.pdf`
- `*.woff`
- `*.woff2`
- `*.ttf`
- `*.zip`
- `*.gz`
- `*.tar`
- `*.so`
- `*.dylib`
- `*.exe`
- `*.wasm`

### Docs / planning / non-source

Skip files in these non-source locations. This is the **conservative spec list — D-03**; do NOT
broaden it (no blanket markdown rule, no contributor/license/CI/example files). A false exclusion
(silently not reviewing real source) is worse than a false inclusion, so the list stays minimal
and the `--include-docs` escape-hatch is the safety valve.

Match on the **path segment** (any directory of that name anywhere in the path), NOT a repo-root
anchor — tracked paths are repo-relative (e.g. `plugins/vibe-check/docs/architecture.md`), so a
root-only `docs/` rule would miss the nested plugin docs:

- any file under a `.planning/` directory (a `*/.planning/*` or root `.planning/` segment)
- any file under a `docs/` directory (a `*/docs/*` or root `docs/` segment)
- any file under a `specs/` directory (a `*/specs/*` or root `specs/` segment)
- top-level `README*` (e.g. `README.md`, `README.rst`)
- top-level `CHANGELOG*`

These are excluded by DEFAULT. The `--include-docs` flag (review.md mode-5 step a) re-includes
them, restoring prior whole-tree behavior. The allowlist override below still applies in both
cases (it only ever KEEPS files, so it is harmless under `--include-docs`).

## Keep these (allowlist override — wins over the denylist)

This section is evaluated **AFTER** all the denylist categories above and **takes precedence over
them**. A tracked `.md` file whose path contains any of the directory segments below is KEPT in
the reviewed set **even if a denylist pattern (e.g. the docs/planning category) would otherwise
drop it**:

- a `/agents/` segment anywhere in the path
- a `/commands/` segment anywhere in the path
- a `/templates/` segment anywhere in the path
- a `/skills/` segment anywhere in the path

Match on the **path segment** (`*/agents/*`, `*/commands/*`, `*/templates/*`, `*/skills/*`), NOT a
repo-root anchor — tracked paths are repo-relative (e.g.
`plugins/vibe-check/agents/architecture.md`), so the rule must match the segment anywhere in the
path, not a root-level `agents/`. This is what protects vibe-check's OWN source: its
`agents/`, `commands/`, `templates/`, and `skills/` are all instructional `.md` that *is* the
program, and a docs/planning denylist pattern must never silently drop them. (The `/skills/` arm
is forward-looking — no `skills/` directory exists yet — but is kept per D-04 so future skill
`.md` is protected the moment it lands.)

**Allowlist WINS:** if a file matches BOTH a denylist pattern and an allowlist segment, it is
KEPT. The allowlist is applied last and overrides the denylist — never the other way around.

## Notes

- This is a **static pattern list only** — it carries no chunking, file-count cap, `git ls-files`
  invocation, or any other selection logic. The selection mechanism (how the list is gathered,
  narrowed, and applied) lives in the `--all` mode block of `commands/review.md`.
- The list is grouped under the four category headings deliberately, so a human can read and audit
  it at a glance — that readability is why a markdown denylist was chosen over opaque git
  `:(exclude)` pathspec magic.
