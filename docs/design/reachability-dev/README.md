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

(filled when the batch is mined)

## Approval record

(pending owner approval of the batch)
