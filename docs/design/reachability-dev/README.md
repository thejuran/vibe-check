# Reachability development cases

## Purpose

These cases are **development rehearsal, not release evidence**. They exist so
prompt changes to the reachability rule can be exercised against real changes of
both shapes before any release measurement:

- **new exposure** (`reach-new-N`) — a real past commit that makes attacker- or
  configuration-controlled input reach an existing, unchanged helper with a real
  weakness for the first time. Expected verdict: a finding (critical/warning) at
  the helper or the new call site, with the causal failure named.
- **demonstrated unchanged** (`reach-unchanged-N`) — a real past commit that
  reuses, refactors or extends an already-reachable helper where every input
  reaching it already reached it before the commit. Expected verdict: quiet (at
  most a pre-existing capped note; a rendered Needs-verification item counts as
  an alarm).

Release measurement uses the B3 ground truth and the sealed holdout, never this
directory. This directory lives outside `docs/design/b3-ground-truth/diffs/`, so
the B3 scorer and replay censuses never see it.

## Provenance rule

- Every case is a REAL historical commit. Nothing here is authored, edited or
  synthesized: each `<id>.patch` is byte-identical to `git diff <base_sha>
  <feature_sha> -- <touched_paths>` in the named source repo.
- Source repos are limited to the B3 source repos (`~/triggarr`,
  `~/seedsyncarr`, `~/roonseek`) or a development repo the owner has approved in
  writing (the approval text is quoted here when that happens).
- A commit that is already a B3 case (its `feature_sha` appears in a
  `docs/design/b3-ground-truth/diffs/*.provenance`) is excluded.
- The sealed holdout is never opened, listed or used to decide exclusions.
  Exclusion is decided only by the B3 provenance rule above.

## Case files

Each case is a triple under `cases/`:

| File | Content |
|------|---------|
| `<id>.patch` | the forward diff `git diff <base_sha> <feature_sha> -- <touched_paths>`; applies cleanly at `base_sha` |
| `<id>.provenance` | `diff_id`, `role`, `source_repo`, `feature_sha`, `base_sha` (= `feature_sha^`), `commit_subject`, `touched_paths`, full-worktree proof (`EXPECTED_TREE_DIFF_SHA256`), PURE-M name-status, literal-secret scan |
| `<id>.expected.md` | expected verdict and the concrete reachability evidence (input, file:line path at `feature_sha`, why it is or is not newly reachable relative to `base_sha`); new-exposure cases also carry the keyed defect (defect, location, causal failure) |

## Leak scanning

This directory is a second identifier source for the prompt leak scanner
(`plugins/vibe-check/scripts/test_agent_prompts.py`, `DEV_CASES_DIR`): paths,
distinctive tokens and the source repo name extracted from these cases must
never appear in agent prompts or templates, exactly like the B3 cases.

## Case index

Mined 2026-10-14 from the B3 source repos only (no other development repo has
been approved).

| id | shape | repo | feature_sha | base_sha | commit_subject | expected |
|----|-------|------|-------------|----------|----------------|----------|
| reach-new-1 | new exposure | ~/triggarr | 050c9c968e48f7e80b2ad3c74ecf9565a804bcfc | 345eaaad08d592376897c3d9a5c33ca173fdbbf8 | feat(72-02): implement reset_request_page, reset_request_post, _write_reset_token_file | finding: the reset token reaches the in-app log viewer |
| reach-new-2 | new exposure | ~/seedsyncarr | 093cd18948f39d4c3a9a5e746e20abd84888aafd | a6a0c6db7380ca0bf2af0805f6f74f44be947431 | feat(62-02): use innerHTML for notification bell text binding | finding: server- and remote-influenced notification text is rendered as HTML |
| reach-unchanged-1 | unchanged | ~/roonseek | 79031dc5a4a718829e2aeb1298c28e85c30eeb2d | 754b2f1c4891b3438be5b2208fc6b0b3eb8235bc | refactor(29-followup): split filter-overrides handler into POST/PUT | quiet |
| reach-unchanged-2 | unchanged | ~/seedsyncarr | 43ee518610e1a0727534ef6d933ad8ecdc620a57 | b853a18ddfb157d3c1d8541bd700a3f24a47cd7a | feat(108-02): extract _dispatch_command helper; thin five single-action handlers | quiet |

### Real-commit lock (outputs recorded 2026-10-14)

For every case: `git -C <repo> cat-file -t <feature_sha>` printed `commit`;
`git -C <repo> rev-parse <feature_sha>^` printed exactly `base_sha`; and
`git -C <repo> diff <base_sha> <feature_sha> -- <touched_paths> | cmp - cases/<id>.patch`
exited 0 (byte-identical).

| id | cat-file -t | rev-parse feature^ | diff vs patch |
|----|-------------|--------------------|---------------|
| reach-new-1 | commit | 345eaaad08d592376897c3d9a5c33ca173fdbbf8 | identical |
| reach-new-2 | commit | a6a0c6db7380ca0bf2af0805f6f74f44be947431 | identical |
| reach-unchanged-1 | commit | 754b2f1c4891b3438be5b2208fc6b0b3eb8235bc | identical |
| reach-unchanged-2 | commit | b853a18ddfb157d3c1d8541bd700a3f24a47cd7a | identical |

Each patch is the whole commit (every file the commit touches is a product file
with status M). Each one passes `git apply --check` on a detached worktree at
`base_sha`. No `feature_sha` or `base_sha` here appears in any B3 provenance file.

## Approval record

(pending owner approval of the batch)
