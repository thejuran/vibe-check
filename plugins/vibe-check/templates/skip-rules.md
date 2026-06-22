---
name: Skip Rules
---

# Skip Rules

Applied by the orchestrator during `--all` whole-tree selection, after `git ls-files`
and before the `<files>` block is built.

## Single source of truth

This file is the **canonical, single source of truth** for the skip patterns the `--all`
whole-codebase mode applies. Both `commands/review.md` and `commands/deep-review.md` reference
this list from their `--all` selection step (via the plugin's prose-pointer convention — e.g.
"apply the skip rules in `templates/skip-rules.md`"). **Do NOT duplicate this list inline** in
either command. A skip-rule change lands here, once, and both commands inherit it — so the two
files cannot silently drift apart (the exact cross-file drift bug this review tool exists to catch).

## Relationship to triage

The baseline floor is the inline `files_to_skip` pattern set in `agents/triage.md` (line 29).
This snippet **supersedes and extends** that baseline for `--all` selection: every pattern triage
already skips is skipped here too, plus the additional vendored/binary patterns below.

`agents/triage.md` itself is left **untouched** in Phase 7 — it is named here only as the baseline
floor. Consolidating triage's inline list into this snippet (so triage points here rather than
carrying its own copy) is an explicit later-cleanup discretion item, not Phase 7 work.

## Skip patterns

A tracked file is excluded from the `--all` reviewed set if it matches any pattern below. The
four categories are the locked exclusions (vendored, generated/minified, lockfiles, binary/image);
the exact extension set within each is non-exhaustive and may grow.

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

## Notes

- This is a **static pattern list only** — it carries no chunking, file-count cap, `git ls-files`
  invocation, or any other selection logic. The selection mechanism (how the list is gathered,
  narrowed, and applied) lives in the `--all` mode block of `commands/review.md`.
- The list is grouped under the four category headings deliberately, so a human can read and audit
  it at a glance — that readability is why a markdown denylist was chosen over opaque git
  `:(exclude)` pathspec magic.
