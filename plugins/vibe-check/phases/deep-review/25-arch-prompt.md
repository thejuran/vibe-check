# Phase 2.5 — Architecture prompt enhancement

> **Lazy-loaded.** Read from `commands/deep-review.md` in the pre-dispatch turn of Phase 2 (every deep review), so the architecture prompt below is composed before the fan-out turn. That turn carries only `Task` calls, so this file is never read inside it.
> Announce after `✓ Phase 2`, as text in the dispatch turn: `✓ Phase 2.5 — Architecture prompt enhancement`.

Architecture prompt includes `<intent-context>` AND the related-files block:

```
You are the architecture agent. Reason deeply about cross-file implications, intent alignment, pattern consistency.

{{intent-context}}

<diff>
{{git_diff}}
</diff>

<related-files>
{{from Phase 1c}}
</related-files>
```

**`--all` mode (`$ALL_MODE` set) — `<files>` swap (REVIEW-01, D-07/D-08).** When `$ALL_MODE` is set (bound by Phase 0 mode 5, `$VC_ROOT/phases/review/00-scope-all.md`), swap this deep-only architecture prompt's `<diff>` block for a `<files>` block in the EXACT same position (after `{{intent-context}}`, before `<related-files>`) — identically to the base/intent template swap in `$VC_ROOT/phases/review/20-dispatch-all.md`. Reuse that `$ALL_MODE` flag and its `<files>` block format/`$FILES_BLOCK` string verbatim; do NOT redefine the `<files>` format here. NOTE the placeholder: the diff-mode block above uses `{{git_diff}}`, but the `--all` block's content is `$FILES_BLOCK` (the same string `20-dispatch-all.md` binds to `{{git_diff_output}}` in mode 5) — substitute `$FILES_BLOCK` here, NOT a diff token, so the architecture agent receives the byte-identical position-stable block the other agents get (D-08). **PER-CHUNK SCOPING (Site C loop):** in `--all` the per-chunk dispatch loop runs once per chunk, so the `$FILES_BLOCK` this architecture prompt binds is the CURRENT CHUNK's `$FILES_BLOCK_i` (the block `20-dispatch-all.md` Site C builds per chunk) — the deep architecture agent is part of chunk `i`'s ONE pure-Task fan-out turn, position-stable with that chunk's other agents (D-08). So in `--all` this prompt reads (`$FILES_BLOCK` = `$FILES_BLOCK_i` for the current chunk):

```
You are the architecture agent. Reason deeply about cross-file implications, intent alignment, pattern consistency.

{{intent-context}}

<files>
$FILES_BLOCK
</files>

<related-files>
{{from Phase 1c}}
</related-files>
```

The impact agent's `<related-files>` block (Phase 1c, `01c-related-files.md`) is diff-oriented; in `--all` it stays AS-IS / is best-effort (its deeper `--all` behavior is a later phase — NOT Phase 7).
