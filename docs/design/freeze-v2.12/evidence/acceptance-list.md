# v2.12 freeze: owner acceptance list (one decision)

- Candidate: `24c0c00038f2d15af4b55f178ea44e680c1f2c58` (from `evidence/CANDIDATE.json`).
- Source review: `evidence/deep-review-release.json`, outcome `blocked`. The full agent JSON is in `evidence/deep-review-release-raw/`.
- Reviewer build: the installed vibe-check cache, content fingerprint `f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3`. The version string 2.11.1 is context only.
- Ranges:
  - Pass 1 reviewed every commit no earlier review saw: `7115f40..24c0c00`, all lanes.
  - Pass 2 reviewed the whole milestone: `v2.11.1 (bbec704)..24c0c00`, architecture and impact lanes only, on the five D-08 areas.
- Totals: 42 findings. 0 critical, 3 warning and 6 medium were reported; 31 fell below the reporting threshold. Every reported finding is listed below. So is every below-threshold finding the coordinator named for a D-09 check. Each was judged by reading the site in the candidate.

## How to read this

The items fall into four groups:

- **A, gate-breaking.** These fall into a D-09 class: lost catch, silently dropped finding, erased decision, false harness completion, or invalid measurement evidence. Accepting them cannot make the gate pass. They must be fixed, which moves the candidate.
- **B, recommended fixes.** Cheap tooling fixes to ride along in the same single restart. Each prevents a Phase-55 stop or a later manifest reissue. None changes the measured plugin.
- **P1, a product call for you.** One plugin regression on unusual filesystems: fix it now or carry it to a patch.
- **C, accept or carry.** Risks proposed to ship with the freeze, disclosed in RESULTS limitations.

**Recommended single decision:** fix A1, A2 and B1–B7 in one batch (one new candidate, one restart). Carry P1 to a 2.12.1 patch with a CHANGELOG note. Accept C1–C6, the carried items K1–K11, the earlier items (a)–(f) and the judgment calls as written.

## A — Gate-breaking: must be fixed before freeze

**A1. The fix-harness completion check never checks that the review was actually closed.** Finding `c65ca7dc8013`, pass 2, architecture, medium, `docs/design/fix-harness/tools/harness_verdict.py:678`.

- What:
  - The workflow gate counts a run as COMPLETE when Finalize really closed the review. The plugin's own test for "closed" is the `**State format:** 53` stamp, checked by `finalize_gate.review_closed`. The plugin's finalize instructions tell every reader to use that test.
  - The harness checks only that `.turingmind/REVIEW.md` exists and is not empty. I read the site in the candidate, and no harness module calls `review_closed`.
- Impact: in Phase 55, a session that improvised its close-out could be counted COMPLETE. For example, it might write a report from memory, or one without the APPROVED stamp, while some other step archived the state. That is a false harness completion, which D-09 says blocks.
- Why it is not acceptable: the other checks (state archived, zero outstanding, decision conservation) lower the odds, but they do not test the close itself. D-09 treats the class as blocking regardless of severity.
- Recommendation: fix. Require `finalize_gate.review_closed(text)` on REVIEW.md, imported the same way the harness already imports `carry_state`, and add a test that fails without the stamp. Small change in fix-harness tools (classified engineering + workflow).
- What would reverse this: nothing. A finding in a gate-breaking class cannot be accepted.

**A2. Detection results could be inherited across a change in model routing.** Finding `p1:arch-005`, pass 1, architecture, below threshold, `docs/design/freeze-v2.12/tools/freeze_policy.py:185`.

- What:
  - The identity check stops B3 runs when the gateway or the process environment changes. The gateway carries the effective model routing (D-24). For example, `ANTHROPIC_DEFAULT_OPUS_MODEL` is part of the process environment.
  - The inheritance rule (`GATE_FIELDS`) for the B3 and holdout gates does not include either.
  - Read in the candidate: `inherit()` compares only `plugin.tree_sha256`, `models`, `codex` and the runner's `cli`, `user_level` and `launch_model`. A gateway update is not a repo path, so the changed-path check cannot catch it either.
- Impact:
  - After the freeze, suppose a gateway update forces a new manifest. The tooling would then declare the B3 and holdout results "inheritable" even though they were measured under different model routing.
  - D-17 forbids carrying results over unless configuration and models are unchanged. Counting those results would be invalid measurement evidence.
- Why it is not acceptable: it is latent, since it only fires on a post-freeze reissue. But the eligibility tool would then certify evidence the policy forbids. That is the "invalid measurement evidence" class.
- Recommendation: fix. Add `runners.<runner>.gateway` and a process-env field to the detection gates' fields, and move the shared environment baseline out of the fix-harness profile. Add a test that a gateway change blocks detection inheritance. Small change in freeze tools (classified engineering + detection + workflow).
- What would reverse this: nothing.

## B — Recommended fixes in the same batch (tooling only, no plugin change)

**B1. The documented release-gate command does not run, and one total ignores missing runs.** Findings `f4fa1bdac08b` (warning, `freeze_tally.py:268`) and `p1:bugs-003` (`freeze_tally.py:220`).

- What:
  - `freeze_tally.py gate --gate engineering --runs-root evidence/` is the command the README documents. It exits with a usage error because `--manifest` is required, and the "use the active manifest" fallback is unreachable.
  - `harness-verdicts` without `--roster` prints a COMPLETE total without checking that every slot is filled.
- Impact:
  - In 54-14 and Phase 55 the documented commands fail. That fails closed, but someone would have to work around it under time pressure.
  - The total is a report, not the verdict. The `gate` command requires the roster, so neither problem is gate-breaking.
- Recommendation: make `--manifest` optional, as the code already intended, and require `--roster` for `harness-verdicts`.

**B2. As built, every Phase-55 holdout launch would stop.** Finding `p1:arch-006`, `holdout_eval_launch.py:80`.

- What:
  - The launcher adds `DISABLE_UPDATES=1` to the session environment. It then checks that environment against the manifest's baseline, which was copied from the generating shell, where that variable was not set.
  - I confirmed this by simulation against the draft manifest. The check prints `setting differs: env.DISABLE_UPDATES (manifest null live 1)`, so the launch stops with an identity mismatch.
- Impact: no holdout measurement could start in Phase 55. Fixing that after the freeze means a new manifest and reruns.
- Recommendation: pin the update switches through the materialized settings, as B3 and the harness do, or give holdout-eval its own baseline. Add a test that drives the real `verify` instead of a mock.

**B3. The B3 runner script hard-codes Phase-54 paths.** Findings `f34de23053ad` (medium, `run_case.sh:120`) and `p1:imp-003` (absorbed).

- What: after each run, `run_case.sh` reads the memory-park record from a fixed Phase-54 file name and reads the weak-note count from `runs-phase54-live/`.
- Impact:
  - In a Phase-55 window the memory move fails: its target becomes the filesystem root, and the weak-note count prints 0. The next block's memory check moves a leftover memory folder aside or stops, so no confounded session runs. That is fail-safe, not gate-breaking.
  - Fixing the script after the freeze requires a new manifest, with all runner categories rerun.
- Recommendation: use the runbook's `MEMPARK_ENV` and run-archive variables, and stop when the park directory is empty.
- Cost note: this edits `run_case.sh`, so the owner-approved manual substitution for semgrep's shell-parser gap must be renewed for that file (124 lines) in the restarted 54-12.

**B4. A holdout launch that fails to start still leaves an eligibility record.** Finding `p1:bugs-008`, `holdout_eval_launch.py:299`.

- What: `identity.json` (the run's eligibility stamp) is written before the session process starts. If the start fails, for example because `claude` is not on PATH, the run folder looks like a stamped run with no output.
- Impact:
  - The failure is loud (a traceback), and a run with no transcript cannot be graded, so the gate reads UNMET rather than passing.
  - But a hand-graded empty run could become a mis-scored slot, so this is a path to invalid evidence that depends on the operator. Not gate-breaking as built.
- Recommendation: check that the session binary resolves before writing the stamp, and mark the folder `.failed` if the launch raises.

**B5. The change map under-reports which reruns some files need.** Finding `p2:arch-005`, `PATH-MAP.json:269`.

- What: `score.py` drives fix-harness state but is not mapped to workflow. `gitguard.py` and `gitsnap.py` run during every review but are not mapped to detection.
- Impact: post-freeze rerun planning would list too few checks. Results cannot actually be inherited wrongly, because any plugin file change already blocks inheritance through the plugin tree hash. So the gates are safe; the planning output is not.
- Recommendation: add the categories. That is an addition, not a reduction, so no separate approval is needed beyond this list.

**B6. One identity-check class can pass silently.** Findings `p1:bugs-009` and `p1:sec-006`, `freeze_check.py:467-472`.

- What: for holdout-eval, the `.vibe-check.toml` check passes when no clone folder is given. The production launcher always gives one, so this is unreachable today.
- Impact: a future caller could get a false IDENTITY OK on that one class.
- Recommendation: report a problem instead, as the B3 branch already does. One-line change.

**B7. An engineering record's guard line is checked only by its prefix.** Finding `p1:bugs-004`, `freeze_policy.py:265`.

- What: the policy checks that `candidate_guard` begins with `CANDIDATE OK`, but not that the guard names the record's own candidate.
- Impact:
  - Records are already bound by `candidate_sha` equality.
  - The current `test-gate.json` and `security-gate.json` guard lines both name `24c0c000…` (checked).
  - Only a copied or fabricated line would slip through. Not gate-breaking.
- Recommendation: compare the candidate named in the guard line with `candidate_sha`. One-line change.

## P1 — Owner product call: finalize archiving on filesystems without hard links

Findings `p1:imp-001`, `p1:bugs-006`, `p1:bugs-007`, `p1:imp-002` (absorbed) and `p2:impact-1`. Sites: `plugins/vibe-check/scripts/review_archive.py:61-67` and `plugins/vibe-check/phases/shared/90-finalize.md:60,215-227`.

- What:
  - The new no-overwrite archive step moves files with a hard link followed by delete. Some filesystems do not support hard links: exFAT/FAT USB drives, SMB network shares and many FUSE mounts.
  - On those, the step fails, and the finalize instructions do not check the failure. So the closed review's state stays live, and the earlier REVIEW.md is overwritten. 2.11.1's plain move handled both cases.
- Impact:
  - Users with the repo on such a filesystem lose earlier reports. Their next review also continues a review that was already closed.
  - It cannot affect the release gates: every runner and the 54-10 live archive check run on the local APFS disk, where hard links work.
- Options:
  - Fix now. A fallback move plus exit-code checks in the finalize instructions. This changes the measured plugin (a new plugin fingerprint, and replay must still show no differences). It adds no restart steps beyond the full restart A already forces, but it puts more change into the build being frozen.
  - Carry to 2.12.1 with a CHANGELOG known-issue note (reporting-only, no candidate move).
- Recommendation: carry to 2.12.1. The issue is rare, its effects are visible to the user, and the freeze is cleanest if the plugin build stays the one the live checks exercised.

## Restart cost (plain terms)

Fixing A (and B) changes freeze, holdout, B3-runner and fix-harness tooling. That classifies as engineering + detection + workflow, which is the same breadth as the last restart (`302df48` to `24c0c00`):

1. One scoped fix commit for the whole batch, then a new candidate.
2. 54-10: replay guard and replay comparison (the scorer is unchanged, so no differences are expected), live finalize-archive check, the two harness clean-tree runs, and a new draft manifest. About 25 minutes last time.
3. 54-11: the 16 live B3 cases once each, the R4 before/after table, and your sign-off. The longest step.
4. 54-12: the four test suites (about 12 minutes), the security scan with triage of new or changed occurrences only, and renewed manual coverage for `run_case.sh` if B3 is included.
5. 54-13: a deep review of the fix commit only, plus a short list of any new items. Then the milestone audit, then 54-14.

Batching everything above into one commit keeps this to one restart. Fixing A alone costs the same restart. B6 and B7 are the only B items whose deferral would not later force a manifest reissue or stop a run.

## Deep-review acceptances

These reported warning/medium findings are proposed for acceptance (C). None is in a D-09 class.

**C1. `0072a6820b1a`** (warning, architecture, `holdout_eval_launch.py:154`). The holdout launcher calls the freeze kit's private git helpers (`_ls_tree`, `_cat_blobs`).

- Impact: maintenance only. A future change to those helpers could break the launcher. Both kits are pinned by the freeze, and the suites pass on the candidate.
- Rationale: behavior is correct today.
- Reversal trigger: any change to `freeze_common` internals. Fix them together at the next tooling change.

**C2. `88df8011d309`** (warning, architecture, `freeze_tally.py:174`). `freeze_tally` calls score43's private `_require_complete` and `_cmd_dev_tally`.

- Impact: the same maintenance coupling. score43 is pinned in the manifest.
- Reversal trigger: any score43 change. Expose public entry points then.

**C3. `5dc57bdc7f7e`** (medium, security, `holdout_eval_launch.py:90`). The holdout measurement session inherits the owner's environment (only auth keys are stripped), runs in `dontAsk` mode, and has no OS sandbox.

- Impact: a hostile instruction inside a case could reach tools the owner's frozen allow-list pre-approves, with the shell's other credentials available.
- Rationale:
  - The cases are owner-commissioned and sealed.
  - `dontAsk` refuses any tool that is not pre-approved, per Claude Code's permission-mode rules. The agent's reading that it auto-approves appears mistaken.
  - The measurement must match how the plugin runs for real. Adding a sandbox changes the environment being measured, so it would need a new baseline.
- Reversal trigger: cases from untrusted authors, or a decision to sandbox both B3 and holdout for the next milestone.

**C4. `6f4ce129479b`** (medium, security, `RUN-PHASE54-live.md:383`). The B3 measured session pre-approves Bash, Write and Edit through `--allowedTools`, inherits the tmux shell's environment, and has no sandbox.

- Impact and rationale: the same as C3. The posture equals the Phase-53 dev runner that the replay and live results are compared against, and the clones are the owner's own repos.
- Reversal trigger: the same as C3.

**C5. `eeb8d761b34d`** (medium, architecture, `harness_sandbox.py:305`). Three separate copies of "build the plugin from the candidate commit": B3 uses `git archive`, while the harness and holdout copy file by file. They treat symlinks differently.

- Impact: the copies could produce different builds if the plugin ever gained symlinks or export attributes.
- Rationale: checked at the candidate. The plugin is 154 regular files with no symlinks, and no `.gitattributes` is tracked, so all three produce the same build today.
- Reversal trigger: a symlink or `.gitattributes` appears. The plugin tree hash would change, which forces a new manifest anyway.

**C6. `348b88e40a9a`** (medium, architecture, `harness_verdict.py:150`). The format-53 state location is written out in three places instead of being imported from `statepath.FORMAT_SUBDIR`.

- Impact: a future location change could be missed in one copy.
- Rationale: maintenance only. The suites pin the current value.
- Reversal trigger: any change to the state location.

## Carried

These are below the reporting threshold. Each was judged against D-09 by reading the site, and none is gate-breaking. They are carried for information or to the backlog.

- **K1. `p2:arch-002`** — `batch_card.py:669`, Needs-verification (NV) rows on the "Apply selected…" card.
  - Picking "Apply selected…" on a card whose only row is NV sends nothing, while ticking an NV row on a 2–16-row card sends it to the fix agent without a typed `fix N`.
  - D-09 check: not a silently dropped finding or an erased decision. An unsent NV row stays open and keeps finalize blocked. A sent row records no decision, so it stays open until it is rechecked. No record is lost.
  - Carry: pick one rule in a later release.
- **K2. `p2:impact-2`** — `90-finalize.md:105`. The "Fix all — every row, any band" label leaves NV rows out.
  - D-09 check: fail-safe; finalize stays blocked. Wording fix later.
- **K3. `p2:impact-3` + `p2:arch-004`** — `20-dispatch.md:93` and `score.py:1182`. A Codex-raised NV item that the owner confirmed and fixed can only be closed by dismiss or defer, and REVIEW.md then lists it as dismissed rather than resolved.
  - D-09 check: the item is never dropped or hidden. The owner's later dismiss or defer is recorded with its reason. The cost is owner burden and a misleading label.
  - Carry: backlog. Record a confirm decision on `fix N`, or close on an `applied` fix verdict.
- **K4. `p2:arch-003` + `p2:impact-4`** — `05-state.md:27-32`. Downgrading to 2.11.1 without the manual rollback steps reopens the pre-migration state, and a 2.11 finalize can overwrite the stamped REVIEW.md.
  - D-09 check: this happens only on a downgrade, outside every release gate.
  - Mitigation: put the rollback steps in CHANGELOG / release notes (reporting-only, no candidate move). Backlog: rename the old state file after migration.
- **K5. `p1:imp-004`** — `score.py:1815`. A placeholder-only NV record with a symbol but no line becomes a normal finding with no line.
  - D-09 check: this promotes a record and never drops one, and the 170-run replay showed 0 differences. Carry.
- **K6. `p1:bugs-001`** — `holdout_autopilot.py:636`. Run from a folder copy, the autopilot hashes the repo's kit, not the code that is running.
  - Used only for sealing and retunes, and no retune is planned. Carry.
- **K7. `p1:bugs-010`** — `freeze_policy.py:801`. The retune proof accepts an empty list of retired cases.
  - Retunes only. Carry, and require a non-empty list before any retune.
- **K8. `p1:bugs-011`** — `freeze_manifest.py:892`. A malformed `enabledPlugins` makes manifest generation crash with a traceback.
  - Fails closed. Carry.
- **K9. `p1:sec-003`, `p1:sec-004`, `p1:sec-005`** — defense-in-depth items:
  - the harness settings check does not verify the network policy;
  - the harness session inherits the parent environment, which the Seatbelt network block mitigates;
  - the secret-value scan uses a list of known patterns rather than an allow-list, behind the closed manifest schema.
  - All predate this delta or are secondary layers. Carry.
- **K10. `p1:arch-003`, `p1:arch-007`, `p1:arch-008`, `p1:arch-009`, `p1:script-001`** — maintenance items: private-name coupling, an import that works only as a side effect, the update-pin constant defined four times, the covered-path list kept in three places, and an uncommented retry-limit constant. Carry.
- **K11. `p2:arch-006`** — README's inheritance claim. **False positive, verified.**
  - `freeze_policy._reporting_only_difference` lets the plugin tree hash differ in reporting-only files, and `plugins/vibe-check/README.md` is `reporting` in PATH-MAP. So the README's statement that every gate inherits across a README-only manifest holds. No action.

## Carried items from earlier plans

**(a) Placeholder normalization also ignores surrounding periods.** From 54-01, `score.py:951`.

- What: `N/A.` counts as a placeholder. Your D-28 wording said "whitespace and case" only.
- Impact: a field that is exactly a placeholder plus a period is treated as blank. Substantive text is never stripped, because matching is whole-field only.
- Recommendation: keep, and ratify it as a recorded deviation from the D-28 wording. Narrowing it is a plugin code change, which would move the candidate.

**(b) A retune forces every rerun set.** This is because `SEAL.json` is not mapped in PATH-MAP, and unmapped files trigger every set (D-16's safe default).

- Impact: extra reruns only, and only on a retune. No retune is planned.
- Recommendation: keep. Narrowing would reduce the map, which needs your approval.

**(c) Nine holdout-v2.12 files are unmapped and not content-hashed** (`kit/` plus two top-level files). The sealed-content barrier blocked the sweep.

- Impact: the runners' identity check does not hash them. Candidate-guard still stops on any edit before the freeze, and an unmapped change triggers every gate set.
- Recommendation: accept. The barrier exists by design.

**(d) `plugins/vibe-check/README.md` stays covered** (inside the hashed plugin root).

- Impact: a README edit needs a new manifest. Inheritance still stands, as verified in K11, so no reruns are needed.
- Recommendation: keep.

**(e) The Codex config is hashed as a whole file.**

- Impact: a cosmetic edit stops runs. These are false stops only, never a missed change.
- Recommendation: accept.

**(f) Hooks are hashed as a whole.**

- Impact: a hooks stop does not name the key that changed, which costs diagnosis time only.
- Recommendation: accept.

## Security triage acceptances

You already approved these in 54-12 (`security-gate.json` `owner_decisions`). They are restated here so the freeze has one record:

- The gitleaks `generic-api-key` hit at `docs/design/holdout-v2.12/SEAL.json:29` is a **false positive**: it is the public SHA-256 commitment to the holdout key, not the key. The exception is narrow, covering this finding id on `24c0c00` only.
- **48 semgrep advisory findings: accepted.** Each has its own location and reason (bidi strip set, mutation-test exec, chmod hardening, sha1 for git identity, `tarfile` with `filter="data"`, fixed import table, fixed globals). Scoped to `24c0c00`. New or changed occurrences need fresh triage.
- **Gate change approved:** documented manual review substitutes for three bash rules on `run_case.sh` (all lines) and `common.sh` (lines 29, 57, 188-213, 222 and 238), with ruleset `19c843d4…`. The gate reads "PASS — documented manual substitution for shell-parser gaps".
- On a new candidate, B3 changes `run_case.sh`, so that substitution must be renewed for that file.

## Judgment calls

**J1. How much of the session environment the identity check freezes.** Model aliases, effort, hooks and their scripts, enabled plugins with their content hashes, and the CLAUDE.md hash all stop a run; cosmetic keys never do.

- Too broad means false stops on harmless edits, and (e) and (f) are examples. Too narrow means a behavior change slips through.
- Recommendation: keep the current breadth. A2 closes the one narrow-side gap found, for inheritance.

**J2. `plugins/vibe-check/README.md` is covered.** Same as (d). Recommendation: keep.

**J3. Non-protected lost catches in 54-11.** There were none. 54-11 recorded "No lost catch" across the 16 live cases on `24c0c00`, and no case was rerun. Nothing to accept.

## Owner decision

Candidate: `24c0c00038f2d15af4b55f178ea44e680c1f2c58`. Relayed by the coordinator on 2026-10-16. Verbatim:

> "Fix A1–A2, B1–B7 and P1 together before the restart. P1 is a known data-loss regression; carrying it because measurement uses a local disk would be the wrong trade-off.For P1, require a no-overwrite fallback when hard links aren’t supported. If archiving still fails, stop visibly and preserve both the report and live state.I would not blanket-approve the remaining list from this truncated summary:- Maintenance duplication in C can be accepted if the recorded impact is only maintenance.- C3/C4 need their actual isolation and permission evidence; “these are our own cases” doesn’t establish containment.- The downgrade item needs reconciliation with the separate-state protection we explicitly chose. Documentation alone was previously rejected.- “Codex NV items never close” needs clarification: unresolved evidence may legitimately block, but a verified-resolved item that cannot close is the workflow defect we set out to eliminate.- The trailing-period placeholder match needs its exact behavior and regression evidence before ratifying that deviation.Keep the proposed single batched restart. Previously accepted findings need reopening only where the fixes invalidate their rationale; renew the shell-review substitution for changed shell code.Ask for one concise supplemental acceptance table covering only those unresolved points, rather than another round of individual cards."

What this decides:

- **To fix, in one batch before the restart:** A1, A2, B1–B7 and P1. For P1: a no-overwrite fallback where hard links are unsupported; if archiving still fails, stop visibly and keep both the report and the live state.
- **Not approved yet:** C3, C4, K3, K4, carried item (a), and the maintenance items C1, C2, C5 and C6 (pending confirmation that their impact is maintenance-only). These go to `## Supplemental acceptance table`.
- **Earlier acceptances:** reopened only where a fix invalidates the rationale. The shell-review substitution is renewed for any changed shell code.

## Supplemental acceptance table

Candidate `24c0c00038f2d15af4b55f178ea44e680c1f2c58`, written 2026-10-16. This covers only the points the owner left open.

How the evidence was gathered:

- Code was read at the candidate (`git show 24c0c00:<path>`). The covered files in the working tree are byte-identical to it (candidate-guard OK).
- Reproductions ran in the scratchpad. No holdout folder or sealed content was opened.

| # | Item | Hard evidence | Impact in plain terms | Recommendation |
|---|---|---|---|---|
| S1 | C1: holdout launcher uses freeze-kit private helpers | `holdout_eval_launch.py:154` calls `freeze_common._ls_tree`/`_cat_blobs`. Output matches the other two build paths (S3). Every launch is checked by `verify` (`plugin_files`) | Maintenance only. No behavior difference today | **Accept.** Residual: a future helper change can break the launcher. Any break fails closed at the identity check |
| S2 | C2: freeze_tally calls score43 private functions | `freeze_tally.py:174-193` calls `score43._require_complete`/`_cmd_dev_tally`. score43's public `run(['dev-tally',…])` calls the same `_cmd_dev_tally(runs_root, require_fingerprint)` (`score43.py:1313`). Only error formatting differs, and both exit non-zero (`freeze_tally.main` catches ValueError, which ScoreError is) | Maintenance only. Same computation, same refusals | **Accept** (as S1) |
| S3 | C5: three copies of the plugin-build step | Reproduced: `git archive … \| tar` (B3 path), `harness_sandbox.snapshot_plugin_from_commit` and `holdout_eval_launch.materialize_plugin_from_candidate`, all on `24c0c00`. `diff -r` showed all three identical (154 files). The tree has only `100644` entries, no symlinks and no tracked `.gitattributes` | Maintenance only today. They would differ only if a symlink or export attribute were added, and that changes the plugin tree hash, which forces a new manifest | **Accept.** Residual as stated |
| S4 | C6: format-53 location written out in three places | `harness_verdict.py:150` `FORMAT_SUBDIR = "format-53"` equals `statepath.py:95`. The other mentions (`harness_seed.py:18,207`) are docstrings | Maintenance only | **Accept** |
| S5 | C3: holdout measured session containment | Launch argv (`holdout_eval_launch.py:85-91`): `claude --plugin-dir … --settings settings-measured.json --model … --add-dir <case> --permission-mode dontAsk --session-id …`, with no `--allowedTools`. `settings-measured.json` has only `enabledPlugins`, `env` (two update pins) and `statusLine`: no `permissions`, no `sandbox`. Owner `~/.claude/settings.json` (loaded): allow `Bash(ssh nas:*)`, deny 4 holdout-read rules, no `sandbox`. The `/deep-review` command's `allowed-tools` frontmatter adds `Bash(git:*)`, `Bash(gh pr diff:*)`, `Bash(gh pr view:*)`, `Bash(node:*)`, `Read`, `Write`, `Edit`, `Grep`, `Glob`, `Task`, `AskUserQuestion`. Env (`session_environment`, `:185-192`): the full parent env minus 6 auth names (`holdout_autopilot.py:110-112`), plus pins. CLI 2.1.281 text: "'dontAsk' - Don't prompt for permissions, deny if not pre-approved". Review subagents are confined by the plugin's `gitguard` hook to read-only words; tested: `curl`, `env`, `printenv`, `python3`, `node` and `nc` are refused, but `cat ~/.ssh/id_rsa` is allowed. Main session and fix agent are unguarded | A prompt-injected **main session** could run `node -e …` (arbitrary code, network, `process.env`) and `ssh nas …`, and could Read files outside the deny list. Subagents cannot reach the network or interpreters but can read files. No OS sandbox. WebFetch is denied (not pre-approved) | **Fix in this batch, together with N1:** (1) give the session an env **allowlist** (the manifest `ENV_ALLOWLIST` keys plus PATH, HOME, USER, SHELL, TERM, LANG, TMPDIR), not the denylist; (2) add permission `deny` Read rules for credential paths (`~/.ssh`, `~/.aws`, `~/.config/gh`, `~/.codex/auth.json`, `~/.netrc`) to the runner settings; (3) add a Bash sandbox with network limited to the Codex endpoint. The fix harness already runs the plugin under a Seatbelt sandbox with network blocked, and its runs complete. Residual after the fix: an injected session can still read clone and repo files and reach the Codex endpoint |
| S6 | C4: B3 measured session containment | `RUN-PHASE54-live.md:383`: `exec claude --permission-mode manual --plugin-dir … --settings … --model … --allowedTools "Bash,Read,Write,Edit,Grep,Glob,Task,Agent"`. `manual` is in the CLI's mode list. `--allowedTools` pre-approves the named tools, so unrestricted Bash runs without a prompt. Env: `launch` (`:343-346`) uses `env VAR=… bash -c` without `-i`, so the tmux server's whole environment is inherited and nothing is stripped. Settings and sandbox are as in S5 (none). Same `gitguard` confinement of subagents. Any other permission prompt kills the run (`run_case.sh` dies on an unexpected card) | A prompt-injected **main session or fix agent** can run any shell command: network (curl), env, secrets readable by the owner. Subagents are as in S5 | **Fix in this batch** with the same three controls as S5, applied in `common.sh launch` (`env -i` plus allowlist) and `settings-measured.json` (shared by both runners). This edits shell code, so the shell-review substitution is renewed. Residual as in S5. Note: this changes the measured environment, but the restart reruns every live check on it anyway |
| S7 | **N1 (new, found while gathering S5): as built, holdout-eval sessions cannot run the plugin's scorer** | Reproduced in a scratch repo with CLI 2.1.281, `-p --permission-mode dontAsk`: `python3 -c 'print(42)'` was **denied** ("Permission to use Bash has been denied because Claude Code is running in don't ask mode"), while `git status --short` ran. Every `/deep-review` phase runs `python3 "$VC_ROOT/scripts/…"` (bootstrap, score.py), and nothing in S5's grant list pre-approves `python3`. The launcher's tests mock the session (D-25 synthetic), so no test would catch this | Every Phase-55 holdout review would be refused its scorer and halt, or improvise. A halted catch case reads as a miss; a halted quiet case reads as quiet. That is **invalid measurement evidence** (D-09 class). B3 is unaffected: it pre-approves `Bash` | **Fix in this batch (gate-breaking):** give holdout-eval the same pre-approved tool set as B3 (`--allowedTools` in `LAUNCH_ARGV`, with `check_argv` updated). Add a live synthetic launch check (a non-holdout fixture diff) proving the scorer runs under the launcher |
| S8 | K4: downgrade to 2.11.1 reopens the old state | What the chosen protection does (`05-state.md` "Why `format-53/`"): 2.12 state lives under `format-53/`, which 2.11.x's resolver can never build, so an older plugin cannot rescore an undecided NV item away or approve over the 2.12 file. What it does not cover (`05-state.md`, forward migration): the migration **copies** `<key>.json` and leaves it "NEVER deleted, moved or modified". After a 2.12 close-out (format-53 archived) or a block on undecided NV items, the old file is still a live 2.11 state at the pre-upgrade pass. 2.11.1 resumes it with no 2.12 decisions, can write an unstamped APPROVED, and (same-phase or default mode) overwrites the stamped REVIEW.md | A plain reinstall of 2.11.1 resurrects a review 2.12 closed or blocked, without the owner's 2.12 decisions. Documentation alone was rejected | **Fix in this batch:** after a successful forward copy, move the old file out of 2.11.1's reach under a no-overwrite archive name (`<key>.json.migrated-format-53`), using `review_archive` with the P1 fallback. If that move fails, stop visibly and keep both files. Update `_rollback.phase53_nv_downgrade` and the migration tests. Covers both the closed and the blocked case. Residual: a 2.11.1 install then starts a fresh pass 1 (a full re-review), and an old-version finalize can still overwrite REVIEW.md by its own rules |
| S9 | K3: Codex-raised NV items cannot close after a verified fix | (i) **Legitimate blocking:** `score._nv_carry_status` (`score.py:1085-1104`) returns `persisted` only when the stored snippet is found unchanged, otherwise `needs-recheck`, never "fixed". An item whose evidence is unchanged or unproven stays open by design. (ii) **Verified-resolved but cannot close: this happens.** Closure needs a `resolved` recheck from the raising lane, an `obsolete` fix verdict, or an owner decision. `20-dispatch.md` step 3: "A record whose agent is not dispatched this pass (a gated lane, `codex-adversarial`, a disabled agent) gets NO hint … the record simply stays carried". `carry_state.record_fix_verdicts` (`:609-648`) records only `obsolete`. `batch_parse` turns `fix N` into a fix target, not a decision. So after the owner types `fix N` and the fix agent commits (`applied`), the item can close only by dismiss or defer. Affected: **every Codex-raised NV item**, and NV items from a lane not dispatched on the next pass (e.g. architecture/impact items followed by a `/review` pass; gated language/framework lanes). Claude lanes that are re-dispatched can close through `resolved`. A verified-`obsolete` fix closes on every lane | The owner confirms and fixes, then must dismiss the same item to finalize, and REVIEW.md lists it as dismissed, not resolved. That is the workflow defect the owner set out to remove | **Fix in this batch (minimal):** record an `applied` fix verdict for an NV row that was an owner-named fix target with a commit sha that exists. Close it exactly as `obsolete` closes (same HEAD-fingerprint check that the fixed file changed since the verdict), and render it under "Resolved by verification" with source `confirmed-fix` and the commit. Legitimate blocking (i) is untouched |
| S10 | K1 part: "Apply selected…" with one NV row sends nothing | `batch_card.py:599-606`: one row means mode `none` and the caller writes `{"all": true}`. `select()` (`:669-671`) drops NV rows from `all` unless `subset`, so the owner's pick of the only row is silently not applied. On 2–16 rows, ticking an NV label sends it (an explicit, numbered choice) | The owner picks a row and nothing happens, with no message. The row stays open (no record is lost), but it costs a round and conflicts with the multi-row behavior | **Fix in this batch:** the one-row path passes that row's label, so an explicit pick is honored the same way on every card size. Bulk `all` still skips NV rows |
| S11 | Item (a): placeholder rule wider than D-28 | Code (`score.py:948-952`, commit `823f40d`): `text.lower().strip().strip(".").strip() in {"n/a","none","-"}`, applied to `_nv_field` = **first line** with whitespace collapsed. Reproduced, matched (blank): `N/A`, `n/a`, ` NONE `, `-`, `N/A.`, `none.`, `-.`, `n/a..`, `...none`, `.-.`, and `None\n<real text>` (first line only). Not matched (kept): `none of the callers.`, `na`, `null`, `—`, `n.a.`, `N / A`, `n/a,`, `'none'`. Tests pass: `test_placeholder_values_score_as_normal_finding` (includes `n/a.`), `test_partial_placeholder_is_not_promoted`, `test_substantive_text_is_not_a_placeholder`, `test_placeholder_set_is_exactly_locked`, `test_blank_dict_bcd15ef_rule`, `test_genuine_nv_still_takes_nv_route`, `test_carried_unaffected`, `test_mutant_empty_placeholder_set` (9 passed). **Narrowing test:** with the exact D-28 rule patched in, `test_placeholder_values_score_as_normal_finding` **fails** (0 findings instead of 1). A proven finding whose fields are `n/a.` gets dropped as `nv-not-admitted` | The periods rule prevents a lost catch: narrowing to D-28's exact wording would re-open the "placeholder values still drop" defect for the commonest LLM spelling (`N/A.`). The other widening, first-line-only, is the older `_nv_field` rule (53-07). It can only turn an NV row into a normal finding, never drop it | **Ratify** the periods rule as a recorded deviation from D-28, with the above as evidence. Residual: any number of leading or trailing periods is ignored, and a field whose first line is a placeholder counts as blank even if later lines carry text (promoted to normal scoring, not dropped). Optional same-batch hardening: evaluate the whole field rather than the first line (a plugin change already in this batch's scope) |

**Effect on the single batched restart:**

- The batch grows by S5/S6 (containment), S7 (N1, gate-breaking), S8, S9 and S10. All are tooling, runner-settings or plugin changes inside the same engineering + detection + workflow restart. No extra restart steps.
- Shell changes (`common.sh`, `run_case.sh`) need the renewed shell-review substitution.
- Previously accepted items whose rationale these fixes change: C3 and C4 are superseded by S5/S6. K3 and K4 move from carried to fixed. K1 is partly fixed (single-row path).
- The rest of the earlier list stands as written.
