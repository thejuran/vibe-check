# Cross-check brief

This file is your whole instruction set. You have nothing else loaded and you need nothing
else. You start in your cross-check workspace (`xcheck/`, or `xcheck-rN/` in a later
round). Below, `xcheck/<XID>/` means a packet folder inside your workspace.

## Your role

You are an independent judge. For each packet you receive:

- `xcheck/<XID>/base/`: the complete base tree of a change;
- `xcheck/<XID>/change.diff`: the change, a unified diff that applies to that tree;
- `CASE-TYPES.md`: the six case types and the causal-failure categories.

Nobody has told you the expected verdict, and nothing in the packet says which type the
case was built for. Your job is to decide for yourself, write that judgment down, and only
then compare it with the answer the owner reveals.

## Before reveal

For each packet:

1. Read the diff against the base tree. Apply it mentally, or in a copy under
   `xcheck/<XID>/changed/` (never anywhere else): copy `base/` to `changed/` and run
   `git apply ../change.diff` inside `changed/`.
2. Decide the verdict: `catch` (the change introduces a defect a careful reviewer should
   report) or `quiet` (it does not, and a careful reviewer should stay quiet).
3. Decide `type_guess`: the single best-matching type from `CASE-TYPES.md`, one of `C1`,
   `C2`, `C3`, `Q1`, `Q2`, `Q3`. A catch verdict takes a C type; a quiet verdict takes a Q
   type.
4. For a catch verdict, give the defect `location`: the file and the line range in the
   changed tree, as narrow as you can defend. Then pick the `defect_category`: the single
   best category from this list (definitions in `CASE-TYPES.md`):
   `missing-input-validation`, `missing-authz-check`, `injection`, `path-traversal`,
   `unsafe-deserialization`, `resource-exhaustion`, `race-condition`, `error-handling`,
   `crypto-misuse`, `info-disclosure`, `logic-error`, `other`.
   `other` never counts as agreement and blocks the case until the owner resolves it with
   evidence, so use it only when nothing else fits.
5. Write `xcheck/<XID>/blind.json`. A quiet verdict sets `location` and `defect_category` to
   `null`. A catch verdict sets both.

```json
{"verdict": "catch", "type_guess": "C3", "location": {"file": "src/app.py", "line_start": 41, "line_end": 44}, "defect_category": "logic-error", "reasoning": "why"}
```

```json
{"verdict": "quiet", "type_guess": "Q2", "location": null, "defect_category": null, "reasoning": "why"}
```

When every packet has a `blind.json`, tell the owner "Blind verdict written for <XID>" for
each one, and WAIT. Do not look for a `revealed/` folder before the owner says it exists.

## After reveal

When the owner says the packets are revealed, each packet has a `revealed/` folder. Read,
for each packet:

- `revealed/REVEAL-TOKEN`: a 16-hex token for this reveal round;
- `revealed/key.json`: the answer key (slot, and for catch: `defect`, `location`,
  `causal_failure`, `causal_failure_category`; for quiet: `expected_quiet_rationale`,
  `supported_behavior`, `exposure_check`);
- `revealed/proof/`: the proof, with `proof/run` as the entry point;
- `revealed/proof-results.json`: the recorded proof runs.

If the proof is runnable, re-run `proof/run` yourself, with the current directory at the
root of each tree: once in a fresh export of `base/` and once in your changed tree. Note
the two exit codes.

Then write `xcheck/<XID>/final.json`:

- `reveal_token`: copied exactly from `revealed/REVEAL-TOKEN`.
- `type_agrees`: your `type_guess` equals the key's slot.
- `defect_agrees` (catch): the key's defect is the same defect you found, in the same file
  with overlapping lines, not merely some defect in the same file.
- `causal_failure_agrees` (catch): the key's `causal_failure_category` equals your
  `defect_category`, and its `causal_failure` prose describes the failure you identified.
- `proof_agrees`: your re-run exits match the recorded ones and fit the slot pattern
  (catch: base 0, changed non-zero; quiet: both 0).
- `proof_rerun_exit`: an object with the base and changed exits you actually saw.
- `quiet_confirmed` (quiet only, otherwise `null`): you independently confirmed the
  `supported_behavior` and that the `exposure_check` holds. Passing tests alone cannot prove
  that no defect exists, so confirm both from the code.
- `notes`: what you checked and anything you disagree with.

```json
{"reveal_token": "<16 hex>", "type_agrees": true, "defect_agrees": true, "causal_failure_agrees": true, "proof_agrees": true,
 "proof_rerun_exit": {"base": 0, "changed": 1}, "quiet_confirmed": null, "notes": "what was checked"}
```

```json
{"reveal_token": "<16 hex>", "type_agrees": true, "defect_agrees": false, "causal_failure_agrees": false, "proof_agrees": true,
 "proof_rerun_exit": {"base": 0, "changed": 0}, "quiet_confirmed": {"supported_behavior": true, "exposure_check": true}, "notes": "what was checked"}
```

The owner's seal recomputes type, location and category agreement from your `blind.json`
by itself, and compares your `proof_rerun_exit` with the recorded exits and the slot
pattern by itself. A flag you set to true cannot override a mechanical mismatch, and
`proof_agrees` cannot cover exits that do not match. Report the exits you actually saw,
even when they contradict the recorded ones: a mismatch is information the owner needs.

### Non-runnable proofs

If `revealed/proof-results.json` has `runnable` set to false, there is nothing to re-run.
Read its `nonrunnable_reason` and `manual_evidence`, and check against the code whether that
evidence really establishes the slot's pattern (catch: the defect is reachable as
described; quiet: the expected behavior holds and nothing new is exposed). Set
`proof_agrees` to true only if it does, and say why in `notes`. Set `proof_rerun_exit` to
`null`; never invent exits.

A non-runnable case does not seal on your say-so: the owner decides whether it seals, by
recording a decision with evidence in a file you cannot see, and the kit blocks the case
until that file is bound to the round. If `revealed/resolution.md` is present, it is the
owner's evidence: read it only after your `blind.json` is written, and say in `notes`
whether it matches what you found.

## If the owner resets a case

Once a reveal has happened in this workspace you have seen answer keys, so you are
never asked to judge a reset or replaced case. The owner launches a different cross-check
session in a fresh workspace with its own configuration directory, which cannot read this
workspace, and that other session judges the new packet without any key in view.

If a packet disappears from your workspace, do not look for it, do not ask about it and do
not write any verdict for it. Finish any `final.json` still pending for the packets you
judged before reveal, then stop when the owner says so.

Before any reveal (no key seen yet), the owner may still add or re-prepare a packet in this
workspace; judge it as in "Before reveal".

## What you must never do

- Never edit `blind.json` after writing it. The owner freezes its hash before reveal, and
  any change is detected.
- Never read `sealed/`, `work/`, `cfg-finder/`, the finder's or the owner's scratch
  (`tmp/finder`, `tmp/owner`), or any earlier cross-check workspace, configuration
  directory or scratch root. All of them are denied. Your own scratch is the
  `tmp/crosscheck/<your workspace>` directory set as `TMPDIR` when this session started.
- Never write outside your packet folders.
- Never run any code-review tool or reviewer agent, or ask one for a verdict.
- Never discuss the case content with anyone but the owner, inside this session.
