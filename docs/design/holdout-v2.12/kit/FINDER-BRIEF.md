# Finder brief

This file is your whole instruction set. You have nothing else loaded and you need nothing
else. All paths below are relative to the holdout folder, which is the parent of the
`work/` directory you start in.

## Your role

You are building six independent evaluation cases from the owner's own repositories, one
for each slot C1, C2, C3, Q1, Q2 and Q3. Each case is a base tree, one diff, a sealed answer
key, an executable proof and a provenance record. Your output is judged mechanically by
rules you can read (`kit/VALIDITY-RULES.md`) and then by a second, independent session that
never sees your reasoning.

You never see or use any code-review tool, and you never ask one for an opinion. Everything
you produce stays in this folder. You may write only inside `sealed/` and `work/`.

## What you may read

- `kit/CASE-TYPES.md`: the six slot definitions, proof shapes, key formats and the
  causal-failure categories.
- `kit/VALIDITY-RULES.md`: rules R-01 to R-12 and the exact schemas.
- `kit/eligible-repos.json`: `{"repos": [<absolute path>, ...]}`, the only repositories you
  may use, in the order you must screen them.
- `kit/b3-exclusions.json`: names and hashes only. Its `repos` list names the repositories
  an earlier benchmark used. A case's `repo_in_b3` is true when the basename of its
  `source_repo` is in that list, and false otherwise. **C1 and Q2 must come from repos where
  `repo_in_b3` is false.** The hash lists let the validator reject a reused commit or patch;
  you do not need to do anything with them.
- `work/RETIRED-REVISIONS.json`, if it exists: revisions the owner retired after a
  contamination or a replacement, as `{"revisions": [{"repo_name": ..., "base_rev": ...,
  "feature_rev": ...}]}`. The owner's kit writes it; you only read it.
- The eligible repositories listed in `kit/eligible-repos.json`, read-only. Your session
  settings deny edits to them.

## What you must never do

- Never re-create a retired or replaced case from the same revision, the same diff or the
  same answer key under a new ID. The owner's seal compares content, not IDs, and refuses
  it.
- Never edit a source repository. Never run `git worktree`, `git checkout`, `git switch`,
  `git stash`, `git reset` or anything else that writes to a repository or its `.git`
  directory. Use exports (see Proof procedure).
- Do not run any code-review tool, reviewer agent or review command, and never ask one for
  a verdict, to find, choose, rank or check a candidate (R-09).
- Never read anything outside this folder and the eligible repositories.
- Never copy case text into a message to the owner. The owner sees only the final line in
  "When you are done".
- Never use a change you have already seen in another benchmark or test fixture.
- Never derive an ID from content. IDs come only from the random command in "What to
  write".
- Never write outside `sealed/` and `work/`.

## Search procedure

1. Before screening anything, load `work/RETIRED-REVISIONS.json` if it exists. A commit
   listed there (its `repo_name` together with its `feature_rev` or `base_rev`) is SKIPPED:
   it gets no ordinal and no rejection entry, it is not a candidate and it does not count
   toward the 25. When you are re-finding a slot after a replacement, the revision that slot
   used before is in that file and must not be taken again, even if it is the first valid
   commit in the fixed order.
2. Per slot, declare the budget and the screening order BEFORE looking. The budget is 25
   candidates. The order is: walk each eligible repository's
   `git log --no-merges --format=%H` newest-first, repositories in the order listed in
   `kit/eligible-repos.json` (for C1 and Q2, only repositories whose `repo_in_b3` is false).
   Write that order into `search.order_rule`.
3. A *candidate* is a commit whose subject or touched paths plausibly match the slot, not
   every commit you scroll past. Assign the next ordinal (1, 2, 3, ...) at the moment you
   decide to inspect it, before inspecting it.
4. Inspect it against the slot definition in `kit/CASE-TYPES.md` and rules R-01 to R-06. If
   it fails, record `{"ordinal": n, "rev": "<commit>", "reason": "<why>"}` in
   `search.rejections` and move on.
5. Take the first valid candidate and stop searching for that slot. Its commit is
   `feature_rev`, its parent is `base_rev`, and `search.screened` equals its ordinal.
6. If 25 candidates are rejected, construct the case (R-08): build it inside an export of an
   eligible repository (for C1 and Q2, a repository with `repo_in_b3` false), set
   `"kind": "constructed"` and `"constructed_by": "isolated-agent"`, and keep all 25
   rejections (`screened` is 25).
7. Record `screened` and the whole `rejections` list in provenance.json.

## Proof procedure

Work on exports, never on the live repository. Export with `git archive`. The commands
below run from the holdout folder (the parent of `work/`); `<repo>` is the absolute path
from `kit/eligible-repos.json`.

```sh
mkdir -p work/<ID>/base work/<ID>/changed
git -C <repo> archive --format=tar <base_rev> -o sealed/cases/<ID>/base.tar
tar -xf sealed/cases/<ID>/base.tar -C work/<ID>/base
tar -xf sealed/cases/<ID>/base.tar -C work/<ID>/changed
git -C <repo> diff <base_rev> <feature_rev> > sealed/cases/<ID>/change.diff
git -C work/<ID>/changed apply ../../../sealed/cases/<ID>/change.diff
```

(`git apply` with explicit paths is fine too; it must apply cleanly to the extracted base
tree.)

Then write `sealed/keys/<ID>/proof/run`: an executable file in any language, run with the
current directory at the root of a tree, that exits 0 when the safe or expected behavior
holds. Run it in `work/<ID>/base` and in `work/<ID>/changed`. For each run, record the exit
code, the `sha256` of the combined stdout and stderr, and an ISO-8601 timestamp in
`sealed/keys/<ID>/proof-results.json`.

- Catch slots (C1, C2, C3): base exits 0, changed exits non-zero.
- Quiet slots (Q1, Q2, Q3): base exits 0, changed exits 0, and the key's `exposure_check`
  names the supported behavior and why the change opens no new exposure.
- C2: the proof must call the code path that lost its protection and show the behavioral
  loss. A proof that only greps, diffs or tests for a file does not count.
- If a proof cannot run (it needs the network, docker, secrets or hardware), write
  `"runnable": false` with `nonrunnable_reason` and `manual_evidence` instead. Such a case is
  labeled and never seals on your word alone; the owner decides it with evidence.

Your shell runs in a sandbox and may prompt the owner before an unsandboxed command. Prefer
proofs that need no network.

## What to write

Mint each case ID with this command, once per case, and never any other way:

```sh
python3 -c 'import secrets;print("H-"+secrets.token_hex(4))'
```

Layout and fields, verbatim from `kit/VALIDITY-RULES.md`:

```text
Layout the finder writes (all under <H>/sealed/; <ID> = "H-" + 8 hex from `python3 -c 'import secrets;print("H-"+secrets.token_hex(4))'`):
  sealed/cases/<ID>/case.json        {"id": "<ID>", "base": "base.tar", "diff": "change.diff", "apply_with": "git apply"}
  sealed/cases/<ID>/base.tar         tar of the base tree (organic: `git -C <repo> archive --format=tar <base_rev> -o base.tar`; constructed: tar of the hand-built tree, relative paths, no symlinks)
  sealed/cases/<ID>/change.diff      unified diff that `git apply` applies cleanly to the extracted base tree
  sealed/keys/<ID>/key.json          catch: {"slot": "C1"|"C2"|"C3", "class": "catch", "defect": str, "location": {"file": str, "line_start": int, "line_end": int}, "causal_failure": str, "causal_failure_category": <one of CAUSAL_CATEGORIES>}
                                     quiet: {"slot": "Q1"|"Q2"|"Q3", "class": "quiet", "expected_quiet_rationale": str, "supported_behavior": str, "exposure_check": str}
  CAUSAL_CATEGORIES (fixed vocabulary; the tuple constant lives in holdout_validate.py and is reproduced verbatim in CASE-TYPES.md):
                                     ("missing-input-validation", "missing-authz-check", "injection", "path-traversal", "unsafe-deserialization",
                                      "resource-exhaustion", "race-condition", "error-handling", "crypto-misuse", "info-disclosure", "logic-error", "other")
                                     "other" is allowed in a key (with causal_failure prose) but NEVER counts as agreement: if either side says "other" the seal blocks and the owner resolves by evidence (resolution.md) or replaces the case.
  sealed/keys/<ID>/provenance.json   {"slot": str, "kind": "organic"|"constructed", "source_repo": "<absolute path>", "repo_name": "<basename>", "repo_in_b3": bool,
                                      "base_rev": "<40 hex>" (organic), "feature_rev": "<40 hex>" (organic), "constructed_by": "owner"|"isolated-agent" (constructed),
                                      "search": {"budget": 25, "order_rule": str, "screened": int, "rejections": [{"ordinal": int, "rev": str, "reason": str}, ...]},
                                      "selected_using_reviewer_output": false, "found_at": "<ISO-8601>"}
                                     rules: screened <= 25; organic: len(rejections) == screened - 1 and the chosen feature_rev is ordinal == screened; constructed: len(rejections) == screened (every candidate rejected)
  sealed/keys/<ID>/proof/run         executable; cwd = tree root; exit 0 = the safe/expected behavior holds. Catch: base->0, changed->non-zero. Quiet: base->0, changed->0.
  sealed/keys/<ID>/proof-results.json runnable: {"runnable": true, "base": {"exit": int, "output_sha256": str, "ran_at": str}, "changed": {"exit": int, "output_sha256": str, "ran_at": str}}
                                      non-runnable: {"runnable": false, "nonrunnable_reason": str, "manual_evidence": str}
```

Examples with placeholder values (field names exact):

```json
{"id": "H-0123abcd", "base": "base.tar", "diff": "change.diff", "apply_with": "git apply"}
```

```json
{"slot": "C2", "class": "catch", "defect": "what is wrong", "location": {"file": "src/app.py", "line_start": 40, "line_end": 52}, "causal_failure": "how it fails", "causal_failure_category": "missing-input-validation"}
```

```json
{"slot": "Q1", "class": "quiet", "expected_quiet_rationale": "why a reviewer should stay quiet", "supported_behavior": "the behavior that still holds", "exposure_check": "why nothing new is exposed"}
```

```json
{"slot": "C1", "kind": "organic", "source_repo": "/Users/owner/some-repo", "repo_name": "some-repo", "repo_in_b3": false,
 "base_rev": "<40 hex>", "feature_rev": "<40 hex>",
 "search": {"budget": 25, "order_rule": "git log --no-merges newest-first, repos in eligible-repos.json order", "screened": 3,
            "rejections": [{"ordinal": 1, "rev": "<40 hex>", "reason": "does not match the slot"}, {"ordinal": 2, "rev": "<40 hex>", "reason": "proof cannot separate the trees"}]},
 "selected_using_reviewer_output": false, "found_at": "2026-01-01T00:00:00Z"}
```

A constructed case drops `base_rev` and `feature_rev`, sets `"kind": "constructed"` and
`"constructed_by"`, and lists every screened candidate as a rejection.

```json
{"runnable": true, "base": {"exit": 0, "output_sha256": "<64 hex>", "ran_at": "2026-01-01T00:00:00Z"}, "changed": {"exit": 1, "output_sha256": "<64 hex>", "ran_at": "2026-01-01T00:00:00Z"}}
```

```json
{"runnable": false, "nonrunnable_reason": "why it cannot run here", "manual_evidence": "what in the code establishes the slot pattern"}
```

Rules that are easy to miss:

- `selected_using_reviewer_output` must be literally `false` in every provenance.json.
- Every catch key sets `causal_failure_category` to exactly one category from
  `kit/CASE-TYPES.md`. `other` is allowed but the independent check can never agree with
  it, so the owner will have to resolve that case with evidence or replace it.
- `location` points at the lines in the changed tree where the defect is, as narrow as you
  can defend.
- Exactly six cases, one per slot. C1 and Q2 must be different changes from each other.
- Do not write `xcheck-ledger.json`, `crosscheck.json` or `resolution.md`; the owner's kit
  writes those.

## When you are done

Tell the owner exactly: "Six cases written. Run bin/holdout validate." Say nothing else
about the cases, then stop.

If the owner reports that validate printed a PROBLEM line, fix only what that line names,
then tell the owner the same sentence again.
