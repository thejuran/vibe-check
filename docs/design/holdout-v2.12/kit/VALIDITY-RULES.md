# Holdout validity rules

A case is valid only when every rule below holds. Each rule is written so the kit's
validator, or the seal, can check it from the files alone. The decision each rule comes
from is in brackets. `<H>` is the holdout folder; `<ID>` is a case ID.

## Rules

R-01 [D-01a] Type match with concrete proof. The case meets its slot's definition in `CASE-TYPES.md` and carries a proof: an executable `proof/run` whose recorded exits fit the slot pattern (catch: base 0, changed non-zero; quiet: base 0, changed 0), or a labeled non-runnable proof (R-10). A quiet key carries a supported `expected_quiet_rationale`, `supported_behavior` and `exposure_check`.

R-02 [D-01b] Enough surrounding code. `base.tar` contains the complete tree at the base revision, not a fragment, so a judge can follow every call the diff touches. `change.diff` applies cleanly to it with `git apply`.

R-03 [D-01c] Unseen. The case is not a renamed or lightly edited version of any prior benchmark case and is absent from any development fixture. The kit's `b3-exclusions.json` hash check rejects a reused commit (`sha256` of `base_rev` or `feature_rev` in `commit_sha256`) or a reused patch (`sha256` of the diff bytes in `patch_sha256`).

R-04 [D-01d] Sealed fields present. Every case has `case.json`, `base.tar`, `change.diff`, `key.json`, `proof/run` (or a non-runnable record), `proof-results.json` and `provenance.json`, with every field in the Schemas section present and non-empty.

R-05 [D-13] Eligible repos only. `source_repo` is one of the repositories listed in `kit/eligible-repos.json`. `turingmind-code-review` and `thejuran-marketplace` are never eligible for any slot.

R-06 [D-02, D-13] C1 and Q2 outside the earlier benchmark. C1 and Q2 must come from repos whose basename is NOT in `kit/b3-exclusions.json["repos"]` (triggarr, seedsyncarr, roonseek, dashboard), so their `repo_in_b3` is false. C1 and Q2 must be distinct changes: different repo-or-revision, different diff, and a changed-line similarity under 0.5. The other four slots may come from any eligible repo.

R-07 [D-03] Budget. At most 25 candidates per type (`search.budget` is 25, `search.screened` <= 25). A candidate is counted when it is chosen for inspection, before inspecting it. The screening order is fixed before the search starts and written in `search.order_rule`. Every rejection is recorded in `search.rejections` with `ordinal`, `rev` and `reason`. The first valid candidate is taken. Organic: `len(rejections) == screened - 1` and the chosen `feature_rev` is ordinal `screened`. Constructed: `len(rejections) == screened`.

R-08 [D-01, D-03] Constructed fallback. A constructed case is allowed only after the budget for its type is exhausted with no valid candidate. It is written by the owner or by this isolated session, with no access to reviewer prompts or tuning results. It sets `kind: "constructed"` and `constructed_by` (`"owner"` or `"isolated-agent"`) and is still built inside a tree exported from an eligible repo.

R-09 [D-03] No reviewer in the loop. `selected_using_reviewer_output: false` must be literally present in every provenance.json. No code-review tool or reviewer agent is ever run to find, choose, rank or check candidates.

R-10 [D-06a, D-06] Executable proof. `proof/run` exits 0 on base and the slot-pattern exit on changed, and the results are recorded in `proof-results.json` with `output_sha256` of the combined output. The validator re-runs the proof on fresh exports and a mismatch blocks. A proof that cannot run carries `runnable: false` with `nonrunnable_reason` and `manual_evidence`; it is labeled, never silent. A non-runnable case never seals on the finder's word alone: the cross-check confirms the manual evidence (`proof_agrees` true, `proof_rerun_exit` null) AND the owner records the decision in `keys/<ID>/resolution.md` before the cross-check round that seals it, so the ledger binds its hash (the NON-RUNNABLE RULE in the Schemas section).

R-11 [D-06b] Independent cross-check. A second isolated session judges each case blind and writes a structured blind verdict (`verdict`, `type_guess`, `location`, `defect_category`). The seal compares it to the key with the AGREEMENT RULE (type match, file and line-overlap match, category match with `other` never agreeing, quiet confirmations, `reveal_token` binding) and any mismatch blocks sealing. The cross-check is bound to the exact bytes it judged (`base.tar`, `change.diff`, `key.json`, `proof/`, `proof-results.json` hashes in the ledger) and to the cross-check workspace generation that judged it (`generation` and `workspace` in the ledger; a round judged in a workspace that had already seen a revealed key is refused). Any later change to those bytes invalidates it until the owner regenerates it with `crosscheck-reset`.

R-12 [D-04] Everything stays inside this folder. Write only under `sealed/` and `work/`. Never copy case material anywhere else. Never paste case text into another tool.

## Schemas

The block below is the single source of truth for file layout and field names. It is
reproduced exactly; the per-file JSON examples after it use the same names.

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
Written by the kit, not the finder:
  sealed/keys/<ID>/xcheck-ledger.json {"xid": "X-xxxxxxxx", "round": int, "generation": int, "workspace": str, "prepared_at": str,    # generation = cross-check workspace generation (1 = "xcheck", N>=2 = "xcheck-rN"); workspace = that directory name; both written by crosscheck-prepare and required by seal
                                       "inputs": {"base.tar": <sha256>, "change.diff": <sha256>, "CASE-TYPES.md": <sha256>},        # written by crosscheck-prepare
                                       "blind_sha256": str, "revealed_at": str, "reveal_token": <16 hex from secrets.token_hex(8)>,    # written by crosscheck-reveal, BEFORE revealed/ is populated
                                       "revealed": {"key.json": <sha256>, "proof-results.json": <sha256>, "proof": <sha256 over sorted "relpath\0sha256\n" lines of proof/**>},
                                       "resolution_sha256": str (only when resolution.md exists at reveal time),
                                       "rounds": [ {a previous round's fields (incl. generation, workspace) plus "reset_reason": str}, ... ]}   # appended by crosscheck-reset; never deleted
  sealed/keys/<ID>/crosscheck.json    copy of xcheck/<XID>/final.json (made by seal)
  sealed/keys/<ID>/resolution.md      optional; only when a disagreement was resolved with evidence
Cross-check session writes (under <H>/xcheck/<XID>/):
  blind.json  {"verdict": "catch"|"quiet", "type_guess": "C1".."Q3", "location": {"file": str, "line_start": int, "line_end": int} | null,
               "defect_category": <one of CAUSAL_CATEGORIES> | null, "reasoning": str}
              rules: verdict == "catch" requires location and defect_category non-null; verdict == "quiet" requires both null
  final.json  (after reveal) {"reveal_token": str (copied verbatim from xcheck/<XID>/revealed/REVEAL-TOKEN), "type_agrees": bool, "defect_agrees": bool, "causal_failure_agrees": bool,
               "proof_agrees": bool, "proof_rerun_exit": {"base": int, "changed": int} | null,
               "quiet_confirmed": {"supported_behavior": bool, "exposure_check": bool} | null (required non-null for quiet slots), "notes": str}
              rules: proof_rerun_exit is an object when revealed/proof-results.json has runnable == true (the session re-ran proof/run) and null when runnable == false (there is nothing to run); a non-null value for a non-runnable case, or null for a runnable one, is a shape failure.
              proof_agrees for a NON-RUNNABLE case means: the session read revealed/proof-results.json's nonrunnable_reason and manual_evidence and independently confirmed, from the code, that the manual evidence establishes the slot pattern (catch: the defect is reachable as described; quiet: the expected behavior holds). It is a judgment, so it never seals on its own (see NON-RUNNABLE RULE).
Kit writes into the packet at reveal (not by the session):
  xcheck/<XID>/revealed/REVEAL-TOKEN  the 16-hex reveal_token; final.json must echo it, which binds final.json to this reveal round

AGREEMENT RULE (mechanical; computed by `seal` from blind.json vs key.json, independent of what final.json claims; final.json flags are required IN ADDITION):
  type:            blind.verdict class == slot class AND blind.type_guess == key.slot
  defect (catch):  blind.location.file == key.location.file AND the line ranges overlap after widening the key range by 5 lines on each side
                   (max(b.line_start, k.line_start-5) <= min(b.line_end, k.line_end+5))
  causal (catch):  blind.defect_category == key.causal_failure_category AND neither equals "other"
  quiet:           type rule above AND final.quiet_confirmed.supported_behavior == true AND final.quiet_confirmed.exposure_check == true
  final flags:     type_agrees, defect_agrees (catch), causal_failure_agrees (catch), proof_agrees all true; reveal_token == ledger.reveal_token
  PROOF EXITS RULE (runnable cases; D-06a + D-06): final.proof_rerun_exit == {base, changed} recorded in sealed/keys/<ID>/proof-results.json (int equality on both), AND both pairs fit the slot pattern (catch: base == 0 and changed != 0; quiet: base == 0 and changed == 0); the seal reads the recorded exits from proof-results.json itself, so proof_agrees == true can never stand in for them: a catch rerun that passes on both trees, or exits that differ from the recorded run, is part "proof exits" and blocks (resolve with evidence by fixing the proof or the key, then crosscheck-reset + a fresh round, or replace the case).
  NON-RUNNABLE RULE (R-10 runnable:false cases; D-06a + D-06): proof-results.json runnable == false requires final.proof_rerun_exit == null (and runnable == true requires it non-null); a non-runnable case is BLOCKED by seal with part "non-runnable proof" UNLESS ALL hold: (a) final.proof_agrees == true (the cross-check confirmed the manual evidence), (b) sealed/keys/<ID>/resolution.md exists and carries the owner's decision with evidence, and (c) it is BOUND: ledger.resolution_sha256 == sha256(resolution.md) (so it was present at reveal, i.e. the owner wrote it, ran crosscheck-reset --reason resolved, and a fresh session judged the packet). A resolution.md added after reveal (unbound) does not count. The seal never reads the prose; the bound hash is the whole mechanical test. There is no auto-pass for a non-runnable case.
  Any failed part -> seal prints DISAGREE_MSG for that slot and refuses. There is no "close enough" branch: ambiguity is a block the owner resolves with evidence or by replacement (D-06).
```

### Per-file examples

Each example uses placeholder values; the field names are exact.

#### case.json

```json
{"id": "H-0123abcd", "base": "base.tar", "diff": "change.diff", "apply_with": "git apply"}
```

#### key.json (catch)

```json
{"slot": "C2", "class": "catch", "defect": "what is wrong", "location": {"file": "src/app.py", "line_start": 40, "line_end": 52}, "causal_failure": "how it fails", "causal_failure_category": "missing-input-validation"}
```

#### key.json (quiet)

```json
{"slot": "Q1", "class": "quiet", "expected_quiet_rationale": "why a reviewer should stay quiet", "supported_behavior": "the behavior that still holds", "exposure_check": "why nothing new is exposed"}
```

#### provenance.json

```json
{"slot": "C1", "kind": "organic", "source_repo": "/Users/owner/some-repo", "repo_name": "some-repo", "repo_in_b3": false,
 "base_rev": "<40 hex>", "feature_rev": "<40 hex>",
 "search": {"budget": 25, "order_rule": "git log --no-merges newest-first, repos in eligible-repos.json order", "screened": 3,
            "rejections": [{"ordinal": 1, "rev": "<40 hex>", "reason": "does not match the slot"}, {"ordinal": 2, "rev": "<40 hex>", "reason": "proof cannot separate the trees"}]},
 "selected_using_reviewer_output": false, "found_at": "2026-01-01T00:00:00Z"}
```

`base_rev` and `feature_rev` are required for organic cases. A constructed case replaces them
with `constructed_by`, and every screened candidate is a rejection:

```json
{"slot": "Q3", "kind": "constructed", "source_repo": "/Users/owner/some-repo", "repo_name": "some-repo", "repo_in_b3": true,
 "constructed_by": "isolated-agent",
 "search": {"budget": 25, "order_rule": "git log --no-merges newest-first, repos in eligible-repos.json order", "screened": 25,
            "rejections": [{"ordinal": 1, "rev": "<40 hex>", "reason": "does not match the slot"}, "... one entry per ordinal up to 25 ..."]},
 "selected_using_reviewer_output": false, "found_at": "2026-01-01T00:00:00Z"}
```

#### proof-results.json (runnable)

```json
{"runnable": true, "base": {"exit": 0, "output_sha256": "<64 hex>", "ran_at": "2026-01-01T00:00:00Z"}, "changed": {"exit": 1, "output_sha256": "<64 hex>", "ran_at": "2026-01-01T00:00:00Z"}}
```

#### proof-results.json (non-runnable)

```json
{"runnable": false, "nonrunnable_reason": "why it cannot run here", "manual_evidence": "what in the code establishes the slot pattern"}
```

#### xcheck-ledger.json (written by the kit, never by a session)

```json
{"xid": "X-89abcdef", "round": 1,
 "generation": 1,
 "workspace": "xcheck",
 "prepared_at": "2026-01-01T00:00:00Z",
 "inputs": {"base.tar": "<64 hex>", "change.diff": "<64 hex>", "CASE-TYPES.md": "<64 hex>"},
 "blind_sha256": "<64 hex>", "revealed_at": "2026-01-01T00:00:00Z", "reveal_token": "<16 hex>",
 "revealed": {"key.json": "<64 hex>", "proof-results.json": "<64 hex>", "proof": "<64 hex>"},
 "rounds": []}
```

`resolution_sha256` is added only when `resolution.md` existed at reveal time.

#### blind.json (cross-check session)

```json
{"verdict": "catch", "type_guess": "C3", "location": {"file": "src/app.py", "line_start": 41, "line_end": 44}, "defect_category": "logic-error", "reasoning": "why"}
```

#### final.json (cross-check session, after reveal)

```json
{"reveal_token": "<16 hex>", "type_agrees": true, "defect_agrees": true, "causal_failure_agrees": true, "proof_agrees": true,
 "proof_rerun_exit": {"base": 0, "changed": 1}, "quiet_confirmed": null, "notes": "what was checked"}
```

## Reporting line

Per case, the finder reports the repo basename (`repo_name`), the provenance kind (`kind`)
and whether the repo was in the earlier benchmark (`repo_in_b3`), inside provenance.json
only. These details never leave the holdout folder.

The owner-facing description of the holdout result is: a small cross-repository smoke
check, not generalization evidence.
