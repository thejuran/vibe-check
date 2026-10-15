# Phase-53 development run notes

**Label: development rehearsal — not release evidence (D-09).** Every number in this file comes
from development runs of the Phase-53 candidate. Release measurement is Phase 55 (the frozen
candidate through B3 x3 and the sealed holdout x3). `docs/efficacy/RESULTS-v2.10.md` stays the
historical record and is not edited by these runs. Nothing under `runs-phase53-dev/` is read by
`score43.py aggregate`, `ledger` or the replay censuses.

Runbook: `docs/design/reachability-dev/RUN-PHASE53-dev.md` (`p53` blocks). Transcripts stay local
(gitignored); only `transcript.jsonl.sha256` is committed.

## Harness pins

pin-claude-code: 2.1.281 (Claude Code)
pin-codex: codex-cli 0.153.4
pin-model: claude-fable-5-1[1m]

The pins equal the Phase-49 harness (`RUN-METHOD-NOTES-phase49.md`: claude-code 2.1.281, codex-cli
0.153.4, model fable 5.1 launched as `claude-fable-5-1[1m]`, codex-companion 1.0.4, 1M window),
so these rehearsal numbers sit on the same harness as the last measured B3 numbers. Each value
was checked live on 2026-10-14 (`claude --version`, `codex --version`, a one-line `claude -p`
probe on the pinned model id).

## Suites on the candidate (before any run)

At `0a924dea15e70f086543b14f6c53e30f50a5e638`:

- `cd plugins/vibe-check/scripts && pytest -q` — 2786 passed, 3798 subtests passed
- `pytest -q docs/design/fix-harness/tools` — 396 passed, 213 subtests passed

## Pre-registration

### Entry 1 — 2026-10-14T23:48:56Z (before the first targeted run)

Recorded and committed before any Phase-53 development run. Never edited afterwards: any later
instruction change gets a NEW dated entry below, committed before the rerun.

**Candidate.** commit `0a924dea15e70f086543b14f6c53e30f50a5e638` (branch `feat/v2.12`);
candidate tree fingerprint over the runtime roots (`score43.py fingerprint --root
plugins/vibe-check`): `5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26`;
`plugins/vibe-check` clean.

**Model / settings.** Each measured session is a separate `claude` process in tmux, launched as
`claude --permission-mode manual --model 'claude-fable-5-1[1m]' --allowedTools
"Bash,Read,Write,Edit,Grep,Glob,Task,Agent"` in the case clone, with no `--plugin-dir` (the
installed `vibe-check@thejuran` cache runs, made content-identical to the candidate by
`resync-cache`). Codex: codex-cli 0.153.4 via the codex plugin 1.0.4, at the plugin's own
configured model and effort (unchanged by this phase). No `.vibe-check.toml` in any clone (default
config). Clone auto-memory parked for the whole window. Driver keystrokes: launch line, `/clear`,
`/vibe-check:deep-review`, `Stop here…` then `Abandon` (by label), `/exit`. One run per case.

**Exact instruction diff.** `git diff 230332e 0a924de -- plugins/vibe-check/agents
plugins/vibe-check/templates/codex-focus.txt plugins/vibe-check/templates/false-positive-rules.md`
(sha256 of the diff text
`e0f32ffb10adef3b05c0483f0328c899fc05edc61b52a7f5833df3606367593b`), reproduced in full at the end
of this entry. The rest of the candidate's change under `plugins/vibe-check/` since 230332e
(scorer D-05/D-06, the Needs-verification route, render, card and finalize wiring, state
location) is listed by `--stat` after the diff; it is not instruction text to the lanes.

**Cases (stage `targeted`).** Run order follows clone availability: `~/triggarr` currently holds uncommitted owner work (not touched by these runs), so the `~/seedsyncarr` and `~/roonseek` cases run first and the `~/triggarr` cases run once that clone is clean. Order does not change any expectation below.

1. `reach-new-1`, `reach-new-2`, `reach-unchanged-1`, `reach-unchanged-2` — the four approved
   development cases (README approval record, 917bde2).
2. `should-quiet-4` (legacy-value rejection, QUIET-03), `should-quiet-6` (declared but not yet
   consumed value, QUIET-02), `should-quiet-7` (staged value reaching a bounded parse, QUIET-02).
3. Reused-helper B3 catch cases — the catch cases whose keyed failure is completed by unchanged
   code the change newly feeds or relies on, so the replaced "unchanged helper = pre-existing"
   cap and the new three-outcome rule both bear on them:
   - `triggarr-secret-in-logs` — the changed log calls feed an unchanged exception text (httpx
     error URL / pydantic payload echo) into the unchanged logging sink;
   - `triggarr-session-rotation` — the change stops rotating the secret; the unchanged signed-
     cookie verifier is what keeps old sessions valid;
   - `triggarr-autoescape` — the change relies on unchanged library behaviour
     (`Jinja2Templates(..., autoescape=True)` no-ops the option).
   Not targeted (keyed failure entirely inside changed lines): `third-organic-should-catch`,
   `triggarr-settings-form-split`. They run in the final sweep.

**Stage `final`.** Every id in `score43.DIFFS` (12) plus the four development cases, once each,
on one recorded `FINAL_FP`, after the replay guard (26/26) and the allowance-gated complete-output
diff pass on that same candidate.

**Expected effects per case** (what the Phase-53 instruction change is expected to do; the
comparison point is the Phase-49 measurement of 2.11, `SCORING-v2.11-phase49.md`).

| case | role | Phase-49 (2.11) | expected on this candidate | why |
|---|---|---|---|---|
| reach-new-1 | catch (dev) | not run | catch: a warning (or NV) row at `routes.py` naming the reset token reaching the log buffer / log viewer | three-outcome rule: a new credential sent into an unchanged sink is demonstrated new exposure → normal band, not the pre-existing cap |
| reach-new-2 | catch (dev) | not run | catch: a warning row at the bell template binding naming influenced notification text parsed as HTML | the guard removal is in the changed line; the unchanged text sources are newly reached |
| reach-unchanged-1 | quiet (dev) | not run | quiet: 0 alarms, 0 NV | the weaknesses (a)-(c) were reachable before the commit; demonstrated unchanged → pre-existing cap at most |
| reach-unchanged-2 | quiet (dev) | not run | quiet: 0 alarms, 0 NV | as above; the refactor moves shared handler code without new inputs |
| should-quiet-4 | quiet | 1/3 fired | quiet | QUIET-03: a stricter validator rejecting a legacy value needs evidence the value exists before it is flagged |
| should-quiet-6 | quiet | 3/3 fired (codex critical at config.py:135/139) | quiet, or at worst an NV item (which still counts as fired) | QUIET-02: a declared-but-unconsumed value is not flagged without evidence of a consumer that breaks |
| should-quiet-7 | quiet (excluded from release verdict, SUPERSESSIONS #001) | 3/3 fired | quiet, or at worst an NV item | QUIET-02 / D-11 staged values: the bounded parse is positive evidence of harmlessness |
| triggarr-secret-in-logs | catch | 3/3 | catch kept (alarm or NV row naming the key reaching logs) | rule must not cap a newly fed unchanged sink |
| triggarr-session-rotation | catch | 3/3 | catch kept | as above |
| triggarr-autoescape | catch | 3/3 | catch kept | as above |
| third-organic-should-catch, triggarr-settings-form-split | catch | 3/3 | catch kept (final sweep) | defect inside changed lines; unaffected |
| should-quiet-1, -2, -3, -5 | quiet | 0, 0, 1, 0 of 3 | quiet (final sweep) | unchanged or better |

**Pass / fail criteria** (development rehearsal; R13).

- A quiet-shaped case (B3 quiet role, `reach-unchanged-*`) PASSES iff `dev-burden` reports
  `fired: False` (alarms == 0 AND Needs-verification items == 0). An NV item on a quiet case is a
  fail exactly like an alarm.
- A catch case PASSES iff a row listed by `catch-candidates` (B3) or `dev-catch-candidates`
  (`reach-new-*`) — alarm or NV row alike — names the keyed defect's location AND causal failure
  (hand AXIS call recorded under the run). An NV mention of the area without the causal failure
  earns nothing.
- Owner questions (cards per run) are reported separately and are not part of pass/fail.
- Stage `targeted` outcome: a quiet fail or a lost catch is recorded with its lane source; a
  plugin defect (crash, card misfire, refusal) is fixed in a scoped `fix(53-14)` commit and the
  case reruns; a rule rewording, if any, is generic only, follows the leak scanner + locks, and
  gets a new pre-registration entry here before the rerun. No prompt is edited to pass a case.
- Stage `final` outcome (for the owner's sign-off): the replay guard 26/26, the diff with zero
  unallowed differences, the tally with `stale: 0`, `missing: 0` on `FINAL_FP`, every B3 catch
  kept or its loss investigated under `## Lost catch investigation`.

**Instruction diff (230332e → 0a924de).**

```diff
diff --git a/plugins/vibe-check/agents/bugs.md b/plugins/vibe-check/agents/bugs.md
index 1d0ce68..816c7a8 100644
--- a/plugins/vibe-check/agents/bugs.md
+++ b/plugins/vibe-check/agents/bugs.md
@@ -111,11 +111,17 @@ value AND the path by which it defeats the case the new check is written to bloc
 `file:line`. "Could be bypassed", "may be incomplete", "not exhaustive" or "sensitive area" do not
 lift the cap. A bypass input the pre-change code equally allowed — a case the diff never addressed
 — is a pre-existing gap, not a defect of this diff: report it under the cap.
-When the new check calls an existing validator or helper and the bypass lies in that helper's
-unchanged logic, it is likewise a pre-existing gap: every existing caller of the helper already has
-it, and the diff only extends the helper to one more input. Report it under the cap and name the
-bypass input in the `pending:` note; it lifts the cap only when the diff's own changed lines let the
-input through.
+
+For a flaw in unchanged code that this diff touches or calls — a helper it now calls, a validator it
+extends, a default it now reaches — first read the callers, guards, defaults and the contract its
+inputs are held to, then land on exactly one outcome: (1) new exposure demonstrated — a new caller,
+a new input or a removed check lets a traced input reach the flaw, cited at `file:line` — report a
+finding at your honest confidence; (2) unchanged exposure demonstrated — the same inputs reached the
+flaw before this diff, cited at `file:line` — report it under the cap as pre-existing; (3) neither
+established — report an unresolved assessment: a finding carrying `needs_verification` whose
+`trigger` names the concrete input or value, `path` names how it reaches the changed code
+(`file:line` or a symbol) and `consequence` names the concrete failure. A new caller is evidence to
+investigate, never a verdict on its own.
 
 Rejecting an input the old code accepted is the control working, not a regression, when that
 input lies outside what the code's own input contract supports (its typed range, its documented
@@ -127,6 +133,22 @@ supported, or a failure asserted without tracing it, does not lift the cap. Revi
 normally on every other axis: a new validator that dereferences `None`, mis-parses a valid value or
 crashes on a wrong type is still a defect on that other axis at your honest confidence.
 
+When a stricter check rejects a value the old code accepted and the contract cannot be established
+either way — no documented configuration, public API or persisted data shows whether the rejected
+value is supported — report an unresolved assessment with `needs_verification` that names the
+concrete rejected value (`trigger`), the input path it arrives on (`path`) and the breakage
+(`consequence`). Old acceptance alone does not prove the value is supported; missing documentation
+alone does not prove it is unsupported; a bare "might break compatibility" with no named value, path
+and failure does not qualify and stays under the cap.
+
+A value, field or option added in one step of a staged change whose consumer is not in the diff is
+not a defect by itself and is not harmless by itself. Suppress it only on requirement-based evidence
+that the change's supported behavior does not need it yet — a working optional default, or a
+feature not exposed on any path this diff activates — cited at `file:line`. Report a finding when
+evidence shows current behavior requires it and it is not wired. Report an unresolved assessment
+with `needs_verification` when neither can be established. A comment, a plan, a roadmap entry or a
+commit message promising future wiring is never evidence of harmlessness.
+
 The opposite direction is a defect: a diff that removes, reverts, loosens, disables or bypasses a
 control, or makes it depend on fragile or version-dependent configuration, IS a demonstrated
 defect on a changed line when a path the control used to protect is left without it. Report it at
@@ -147,9 +169,10 @@ text is never evidence of a replacement. When you found and read a same-purpose
 can trace a formerly protected path that bypasses it, that is a demonstrated protection loss:
 report it at your honest confidence; no cap applies, because demonstrated loss always takes
 precedence over the cap. When you found and read a same-purpose replacement whose coverage of
-every formerly protected path remains unverified, report the removal as a capped note
-(`agent_confidence ≤ 45`, `severity: low`) with
-`pending: confirm <file:line> covers every path the old check guarded`.
+every formerly protected path remains unverified, report an unresolved assessment with
+`needs_verification`: `path` names the formerly protected path you could not confirm, `trigger`
+names the input that would take it, `consequence` names what the removed check prevented, and the
+problem text cites the replacement at `file:line`; it is never a capped note.
 
 **Sensitive area, no demonstrated defect:** when a finding's only basis is that changed code
 touches a sensitive area (auth, secrets, SSRF, injection, logging, validation, serialization) and
@@ -159,12 +182,17 @@ drop. Severity is how bad the finding is if real, and a note with no demonstrate
 demonstrated consequence, so it is `low` until a defect is shown — then raise confidence and
 severity together. At `agent_confidence ≤ 45` and `severity: low` the note never reaches the
 Warning band, even if Codex independently flags the same site while joined and it persists across
-passes (`templates/scoring.md`: at most 45 + 20 + 10 + 15 − 20 = 70, the Medium floor,
-acknowledgeable). Off-hunk is not the same as unverified: repository
+passes (`templates/scoring.md`: a note that does not qualify earns no +10, so at most
+45 + 20 + 15 − 20 = 60, below the Medium floor). Off-hunk is not the same as unverified: repository
 context outside the diff that you have actually read counts as evidence, so an unchanged caller
 that demonstrably feeds attacker-controlled input into a changed sink establishes a defect on the
 changed line — report it at your honest confidence, not under the cap.
 
+`needs_verification` is the exception, not a softer finding: every rendered unresolved item is
+counted as an alarm and must be decided by the owner, so emit it only with a concrete `trigger`,
+`path` and `consequence` tied to this diff; a note with no concrete failure stays under the
+sensitive-area cap.
+
 ## Coverage, not filtering
 
 Report every issue you find, including ones you are uncertain about or consider low-severity. Do not self-filter for importance or confidence — the orchestrator scores every finding (`templates/scoring.md`) and filters downstream; your honest `agent_confidence` and `severity` are what make that filter work. A surfaced finding that gets filtered out costs nothing; a silently dropped real issue is unrecoverable. (Pure style/naming preferences remain out of scope — report defects, not taste.)
diff --git a/plugins/vibe-check/agents/codex-adversarial.md b/plugins/vibe-check/agents/codex-adversarial.md
index 35b1d0d..ee74b63 100644
--- a/plugins/vibe-check/agents/codex-adversarial.md
+++ b/plugins/vibe-check/agents/codex-adversarial.md
@@ -76,9 +76,9 @@ Translation is deterministic Python (`scripts/codex_translate.py`), and this con
 
 - Codex's `confidence ≤ 0.45` maps verbatim to `agent_confidence ≤ 45`, and the literal's "severity low" maps verbatim to `severity: "low"` (−20). A lone Codex sensitive-area note therefore scores ≤ 45, below the Medium floor.
 - The "Verbatim; no floor, no penalty" row above stays true: no Codex-specific scoring adjustment exists. The ceiling is Codex's own calibration, carried by the literal.
-- A Codex note at ≤ 45 co-located with a Claude-lane finding while Codex is joined still earns the +10, but at severity low that pair scores 55 (filtered). The worst reachable path — the note carried as a member of a surviving row, then persisted (+15) and re-corroborated (+10) on the next pass — tops out at 70 (the Medium floor, acknowledgeable), never the Warning band. That is why the literal fixes the severity and not only the confidence; `scripts/test_agent_prompts.py` drives the real scorer over two passes to prove it. Whether the bound should hold per member or per group is backlog 999.19.
+- A ≤ 45 / low note never qualifies as a second opinion: alone it scores 45 + 20 − 20 = 45, below every per-command cutoff, so it earns no +10 and releases no lone-lane cap — for itself or for any finding beside it, even while Codex is joined (`templates/scoring.md` D-05). The worst reachable path — the note carried as a member of a surviving row, then persisted (+15) on the next pass — is 45 + 20 + 15 − 20 = 60, below the Medium floor. That is why the literal fixes the severity and not only the confidence; `scripts/test_agent_prompts.py` drives the real scorer over two passes to prove it. The per-member question is decided (Phase 53, D-05): each member of a corroborating pair must qualify on its own, on the same line, and only those two members earn the credit.
 
-**Cross-confirm (enforced in `/deep-review` Phase 3 dedup, `scripts/score.py`):** findings are grouped by site — the same file within ±2 lines, any category (`templates/scoring.md`, H-LANE). Every lane at one site is one surviving row that lists every member. The +10 second-opinion bonus fires only when a `codex-adversarial` member and a Claude-lane member sit at the same site and Codex joined this pass (the envelope's orchestrator-set `codex.status == "joined"`); agreement between two Claude lanes earns nothing (Phase 41 D-01). Codex's literal `category: "adversarial"` no longer affects grouping or the bonus. What matters is **location accuracy** (the `line`), not title phrasing — a shared title substring fires nothing.
+**Cross-confirm (enforced in `/deep-review` Phase 3 dedup, `scripts/score.py`):** findings are grouped by site — the same file within ±2 lines, any category (`templates/scoring.md`, H-LANE). Every lane at one site is one surviving row that lists every member. The +10 second-opinion bonus fires only when a `codex-adversarial` member and a Claude-lane member each clear the cutoff on their own score, sit on the same line, and Codex joined this pass (the envelope's orchestrator-set `codex.status == "joined"`); only those two members earn it (D-05); agreement between two Claude lanes earns nothing (Phase 41 D-01). Codex's literal `category: "adversarial"` no longer affects grouping or the bonus. What matters is **location accuracy** (the `line`), not title phrasing — a shared title substring fires nothing.
 
 ## Untrusted-data posture
 
diff --git a/plugins/vibe-check/agents/impact.md b/plugins/vibe-check/agents/impact.md
index ad7c84a..dc23972 100644
--- a/plugins/vibe-check/agents/impact.md
+++ b/plugins/vibe-check/agents/impact.md
@@ -28,11 +28,17 @@ value AND the path by which it defeats the case the new check is written to bloc
 `file:line`. "Could be bypassed", "may be incomplete", "not exhaustive" or "sensitive area" do not
 lift the cap. A bypass input the pre-change code equally allowed — a case the diff never addressed
 — is a pre-existing gap, not a defect of this diff: report it under the cap.
-When the new check calls an existing validator or helper and the bypass lies in that helper's
-unchanged logic, it is likewise a pre-existing gap: every existing caller of the helper already has
-it, and the diff only extends the helper to one more input. Report it under the cap and name the
-bypass input in the `pending:` note; it lifts the cap only when the diff's own changed lines let the
-input through.
+
+For a flaw in unchanged code that this diff touches or calls — a helper it now calls, a validator it
+extends, a default it now reaches — first read the callers, guards, defaults and the contract its
+inputs are held to, then land on exactly one outcome: (1) new exposure demonstrated — a new caller,
+a new input or a removed check lets a traced input reach the flaw, cited at `file:line` — report a
+finding at your honest confidence; (2) unchanged exposure demonstrated — the same inputs reached the
+flaw before this diff, cited at `file:line` — report it under the cap as pre-existing; (3) neither
+established — report an unresolved assessment: a finding carrying `needs_verification` whose
+`trigger` names the concrete input or value, `path` names how it reaches the changed code
+(`file:line` or a symbol) and `consequence` names the concrete failure. A new caller is evidence to
+investigate, never a verdict on its own.
 
 Rejecting an input the old code accepted is the control working, not a regression, when that
 input lies outside what the code's own input contract supports (its typed range, its documented
@@ -44,6 +50,22 @@ supported, or a failure asserted without tracing it, does not lift the cap. Revi
 normally on every other axis: a new validator that dereferences `None`, mis-parses a valid value or
 crashes on a wrong type is still a defect on that other axis at your honest confidence.
 
+When a stricter check rejects a value the old code accepted and the contract cannot be established
+either way — no documented configuration, public API or persisted data shows whether the rejected
+value is supported — report an unresolved assessment with `needs_verification` that names the
+concrete rejected value (`trigger`), the input path it arrives on (`path`) and the breakage
+(`consequence`). Old acceptance alone does not prove the value is supported; missing documentation
+alone does not prove it is unsupported; a bare "might break compatibility" with no named value, path
+and failure does not qualify and stays under the cap.
+
+A value, field or option added in one step of a staged change whose consumer is not in the diff is
+not a defect by itself and is not harmless by itself. Suppress it only on requirement-based evidence
+that the change's supported behavior does not need it yet — a working optional default, or a
+feature not exposed on any path this diff activates — cited at `file:line`. Report a finding when
+evidence shows current behavior requires it and it is not wired. Report an unresolved assessment
+with `needs_verification` when neither can be established. A comment, a plan, a roadmap entry or a
+commit message promising future wiring is never evidence of harmlessness.
+
 The opposite direction is a defect: a diff that removes, reverts, loosens, disables or bypasses a
 control, or makes it depend on fragile or version-dependent configuration, IS a demonstrated
 defect on a changed line when a path the control used to protect is left without it. Report it at
@@ -64,9 +86,10 @@ text is never evidence of a replacement. When you found and read a same-purpose
 can trace a formerly protected path that bypasses it, that is a demonstrated protection loss:
 report it at your honest confidence; no cap applies, because demonstrated loss always takes
 precedence over the cap. When you found and read a same-purpose replacement whose coverage of
-every formerly protected path remains unverified, report the removal as a capped note
-(`agent_confidence ≤ 45`, `severity: low`) with
-`pending: confirm <file:line> covers every path the old check guarded`.
+every formerly protected path remains unverified, report an unresolved assessment with
+`needs_verification`: `path` names the formerly protected path you could not confirm, `trigger`
+names the input that would take it, `consequence` names what the removed check prevented, and the
+problem text cites the replacement at `file:line`; it is never a capped note.
 
 **Sensitive area, no demonstrated defect:** when a finding's only basis is that changed code
 touches a sensitive area (auth, secrets, SSRF, injection, logging, validation, serialization) and
@@ -76,12 +99,17 @@ drop. Severity is how bad the finding is if real, and a note with no demonstrate
 demonstrated consequence, so it is `low` until a defect is shown — then raise confidence and
 severity together. At `agent_confidence ≤ 45` and `severity: low` the note never reaches the
 Warning band, even if Codex independently flags the same site while joined and it persists across
-passes (`templates/scoring.md`: at most 45 + 20 + 10 + 15 − 20 = 70, the Medium floor,
-acknowledgeable). Off-hunk is not the same as unverified: repository
+passes (`templates/scoring.md`: a note that does not qualify earns no +10, so at most
+45 + 20 + 15 − 20 = 60, below the Medium floor). Off-hunk is not the same as unverified: repository
 context outside the diff that you have actually read counts as evidence, so an unchanged caller
 that demonstrably feeds attacker-controlled input into a changed sink establishes a defect on the
 changed line — report it at your honest confidence, not under the cap.
 
+`needs_verification` is the exception, not a softer finding: every rendered unresolved item is
+counted as an alarm and must be decided by the owner, so emit it only with a concrete `trigger`,
+`path` and `consequence` tied to this diff; a note with no concrete failure stays under the
+sensitive-area cap.
+
 ## Coverage, not filtering
 
 Report every issue you find, including ones you are uncertain about or consider low-severity. Do not self-filter for importance or confidence — the orchestrator scores every finding (`templates/scoring.md`) and filters downstream; your honest `agent_confidence` and `severity` are what make that filter work. A surfaced finding that gets filtered out costs nothing; a silently dropped real issue is unrecoverable. (Pure style/naming preferences remain out of scope — report defects, not taste.)
diff --git a/plugins/vibe-check/agents/security.md b/plugins/vibe-check/agents/security.md
index 3f60482..7959746 100644
--- a/plugins/vibe-check/agents/security.md
+++ b/plugins/vibe-check/agents/security.md
@@ -78,11 +78,17 @@ value AND the path by which it defeats the case the new check is written to bloc
 `file:line`. "Could be bypassed", "may be incomplete", "not exhaustive" or "sensitive area" do not
 lift the cap. A bypass input the pre-change code equally allowed — a case the diff never addressed
 — is a pre-existing gap, not a defect of this diff: report it under the cap.
-When the new check calls an existing validator or helper and the bypass lies in that helper's
-unchanged logic, it is likewise a pre-existing gap: every existing caller of the helper already has
-it, and the diff only extends the helper to one more input. Report it under the cap and name the
-bypass input in the `pending:` note; it lifts the cap only when the diff's own changed lines let the
-input through.
+
+For a flaw in unchanged code that this diff touches or calls — a helper it now calls, a validator it
+extends, a default it now reaches — first read the callers, guards, defaults and the contract its
+inputs are held to, then land on exactly one outcome: (1) new exposure demonstrated — a new caller,
+a new input or a removed check lets a traced input reach the flaw, cited at `file:line` — report a
+finding at your honest confidence; (2) unchanged exposure demonstrated — the same inputs reached the
+flaw before this diff, cited at `file:line` — report it under the cap as pre-existing; (3) neither
+established — report an unresolved assessment: a finding carrying `needs_verification` whose
+`trigger` names the concrete input or value, `path` names how it reaches the changed code
+(`file:line` or a symbol) and `consequence` names the concrete failure. A new caller is evidence to
+investigate, never a verdict on its own.
 
 Rejecting an input the old code accepted is the control working, not a regression, when that
 input lies outside what the code's own input contract supports (its typed range, its documented
@@ -94,6 +100,22 @@ supported, or a failure asserted without tracing it, does not lift the cap. Revi
 normally on every other axis: a new validator that dereferences `None`, mis-parses a valid value or
 crashes on a wrong type is still a defect on that other axis at your honest confidence.
 
+When a stricter check rejects a value the old code accepted and the contract cannot be established
+either way — no documented configuration, public API or persisted data shows whether the rejected
+value is supported — report an unresolved assessment with `needs_verification` that names the
+concrete rejected value (`trigger`), the input path it arrives on (`path`) and the breakage
+(`consequence`). Old acceptance alone does not prove the value is supported; missing documentation
+alone does not prove it is unsupported; a bare "might break compatibility" with no named value, path
+and failure does not qualify and stays under the cap.
+
+A value, field or option added in one step of a staged change whose consumer is not in the diff is
+not a defect by itself and is not harmless by itself. Suppress it only on requirement-based evidence
+that the change's supported behavior does not need it yet — a working optional default, or a
+feature not exposed on any path this diff activates — cited at `file:line`. Report a finding when
+evidence shows current behavior requires it and it is not wired. Report an unresolved assessment
+with `needs_verification` when neither can be established. A comment, a plan, a roadmap entry or a
+commit message promising future wiring is never evidence of harmlessness.
+
 The opposite direction is a defect: a diff that removes, reverts, loosens, disables or bypasses a
 control, or makes it depend on fragile or version-dependent configuration, IS a demonstrated
 defect on a changed line when a path the control used to protect is left without it. Report it at
@@ -114,9 +136,10 @@ text is never evidence of a replacement. When you found and read a same-purpose
 can trace a formerly protected path that bypasses it, that is a demonstrated protection loss:
 report it at your honest confidence; no cap applies, because demonstrated loss always takes
 precedence over the cap. When you found and read a same-purpose replacement whose coverage of
-every formerly protected path remains unverified, report the removal as a capped note
-(`agent_confidence ≤ 45`, `severity: low`) with
-`pending: confirm <file:line> covers every path the old check guarded`.
+every formerly protected path remains unverified, report an unresolved assessment with
+`needs_verification`: `path` names the formerly protected path you could not confirm, `trigger`
+names the input that would take it, `consequence` names what the removed check prevented, and the
+problem text cites the replacement at `file:line`; it is never a capped note.
 
 **Sensitive area, no demonstrated defect:** when a finding's only basis is that changed code
 touches a sensitive area (auth, secrets, SSRF, injection, logging, validation, serialization) and
@@ -126,12 +149,17 @@ drop. Severity is how bad the finding is if real, and a note with no demonstrate
 demonstrated consequence, so it is `low` until a defect is shown — then raise confidence and
 severity together. At `agent_confidence ≤ 45` and `severity: low` the note never reaches the
 Warning band, even if Codex independently flags the same site while joined and it persists across
-passes (`templates/scoring.md`: at most 45 + 20 + 10 + 15 − 20 = 70, the Medium floor,
-acknowledgeable). Off-hunk is not the same as unverified: repository
+passes (`templates/scoring.md`: a note that does not qualify earns no +10, so at most
+45 + 20 + 15 − 20 = 60, below the Medium floor). Off-hunk is not the same as unverified: repository
 context outside the diff that you have actually read counts as evidence, so an unchanged caller
 that demonstrably feeds attacker-controlled input into a changed sink establishes a defect on the
 changed line — report it at your honest confidence, not under the cap.
 
+`needs_verification` is the exception, not a softer finding: every rendered unresolved item is
+counted as an alarm and must be decided by the owner, so emit it only with a concrete `trigger`,
+`path` and `consequence` tied to this diff; a note with no concrete failure stays under the
+sensitive-area cap.
+
 ## Coverage, not filtering
 
 Report every issue you find, including ones you are uncertain about or consider low-severity. Do not self-filter for importance or confidence — the orchestrator scores every finding (`templates/scoring.md`) and filters downstream; your honest `agent_confidence` and `severity` are what make that filter work. A surfaced finding that gets filtered out costs nothing; a silently dropped real issue is unrecoverable. (Pure style/naming preferences remain out of scope — report defects, not taste.)
diff --git a/plugins/vibe-check/templates/codex-focus.txt b/plugins/vibe-check/templates/codex-focus.txt
index beb46ba..072f107 100644
--- a/plugins/vibe-check/templates/codex-focus.txt
+++ b/plugins/vibe-check/templates/codex-focus.txt
@@ -1 +1 @@
-Calibration rules for every finding, not a focus area: review the whole change as you normally would. (1) A change that tightens a control (adds or narrows an allowlist or denylist validator on an input, wraps output in an existing sanitizer or escaper, adds a bound or finite-only check to a numeric field, routes input through an existing clamping or parse helper) is safe on the axis it tightens unless you name a concrete bypass: a specific input value and the file:line path by which it defeats the case the new check is written to block. An input the pre-change code equally allowed is a pre-existing gap, not a defect of this change, only when it is a case the diff never addressed: report it at or below 0.45 confidence with severity low. An input the new check is written to block and demonstrably fails to block is a defect of this change at your honest confidence, even though the old code allowed it too. When the failure lies in the unchanged logic of an existing validator or helper that the change only calls, it is a pre-existing gap instead: every existing caller of that helper already has it, so report it under the pre-existing-gap ceiling above and name the bypass input; it is a defect of this change only when the lines the change itself adds or edits let the input through. Rejecting inputs the old code accepted is the control working, not a regression, when the input lies outside what the input contract of the code supports (typed range, documented values, defaults); a concrete value the contract does support, traced through the new check to a specific failure at file:line, is a real regression whether or not that value occurs in the repository. Every other axis is reviewed normally. (2) A change that removes, reverts, loosens, disables or bypasses a control, or makes it depend on fragile or version-dependent configuration, is a real defect on a changed line when a path the control used to protect is left without it: report it at your honest confidence. Replacing a protection that held unconditionally with one that holds only through a library default, a deprecated path or the currently installed dependency version is such a loss even when you verify it still holds today: report it at your honest confidence, not under the sensitive-area ceiling, and name in the title the attack the control prevents once the protection lapses (for example injection, script execution or data exposure), not only the revert, deprecation or startup symptom. A control moved rather than lost is judged by what you found, not by what the change claims. A same-purpose replacement is code at file:line (shared middleware, a decorator, a schema or an upstream layer) that guards the same property as the removed check. When you found and read no same-purpose replacement, including when only a comment, docstring or commit message asserts a move, or when the only code you found guards a different property (logging or rate-limiting middleware for a removed auth check), the removal rule applies at your honest confidence and the cap does not apply. A move claim in the change text is never evidence of a replacement. When you found and read a same-purpose replacement and can trace a formerly protected path that bypasses it, that is a demonstrated protection loss: report it at your honest confidence with no cap, because demonstrated loss always takes precedence over the cap. When you found and read a same-purpose replacement whose coverage of every formerly protected path remains unverified, report the removal at or below 0.45 confidence with severity low and say to confirm that file:line covers every path the old check guarded. (3) If a finding rests only on the changed code being in a sensitive area, with no defect shown on a changed line, set confidence at or below 0.45 and severity low (no demonstrated defect means no demonstrated consequence) and say what would demonstrate it. Still report it. At that confidence and severity the note stays below the Warning band even when corroborated and persisted. Off-hunk is not the same as unverified: repository context outside the change that you actually read counts as evidence, so an unchanged caller that demonstrably feeds attacker-controlled input into a changed sink is a defect on the changed line at your honest confidence.
+Calibration rules for every finding, not a focus area: review the whole change as you normally would. (1) A change that tightens a control (adds or narrows an allowlist or denylist validator on an input, wraps output in an existing sanitizer or escaper, adds a bound or finite-only check to a numeric field, routes input through an existing clamping or parse helper) is safe on the axis it tightens unless you name a concrete bypass: a specific input value and the file:line path by which it defeats the case the new check is written to block. An input the pre-change code equally allowed is a pre-existing gap, not a defect of this change, only when it is a case the diff never addressed: report it at or below 0.45 confidence with severity low. An input the new check is written to block and demonstrably fails to block is a defect of this change at your honest confidence, even though the old code allowed it too. For a flaw in unchanged code that the change touches or calls, first read the callers, guards, defaults and the contract the inputs are held to, then land on exactly one outcome: new exposure demonstrated (a new caller, new input or removed check lets a traced input reach the flaw at file:line) is a finding at your honest confidence; unchanged exposure demonstrated (the same inputs reached it before the change, at file:line) is a pre-existing gap under the ceiling above; neither established is an unresolved assessment, reported by starting the body with exactly NEEDS VERIFICATION | Trigger: <the concrete input or value> | Path: <the file:line or symbol by which it reaches the changed code> | Consequence: <the concrete failure>, with your own text in place of each bracketed description. A new caller is evidence to investigate, never a verdict on its own. Rejecting inputs the old code accepted is the control working, not a regression, when the input lies outside what the input contract of the code supports (typed range, documented values, defaults); a concrete value the contract does support, traced through the new check to a specific failure at file:line, is a real regression whether or not that value occurs in the repository. When a stricter check rejects a value the old code accepted and no documented configuration, public API or persisted data shows whether that value is supported, report an unresolved assessment with the same marker, naming the concrete rejected value as Trigger, the input path it arrives on as Path and the breakage as Consequence. Old acceptance alone does not prove the value is supported; missing documentation alone does not prove it is unsupported; a bare "might break compatibility" with no named value, path and failure does not qualify. Every other axis is reviewed normally. A value, field or option added in one step of a staged change whose consumer is not in the change is neither a defect nor harmless by itself: suppress it only on evidence at file:line that the supported behavior does not need it yet (a working optional default, or a feature not exposed on any path the change activates); it is a finding when evidence shows current behavior requires it and it is not wired; otherwise it is an unresolved assessment with the same marker. A comment, plan, roadmap entry or commit message promising future wiring is never evidence of harmlessness. (2) A change that removes, reverts, loosens, disables or bypasses a control, or makes it depend on fragile or version-dependent configuration, is a real defect on a changed line when a path the control used to protect is left without it: report it at your honest confidence. Replacing a protection that held unconditionally with one that holds only through a library default, a deprecated path or the currently installed dependency version is such a loss even when you verify it still holds today: report it at your honest confidence, not under the sensitive-area ceiling, and name in the title the attack the control prevents once the protection lapses (for example injection, script execution or data exposure), not only the revert, deprecation or startup symptom. A control moved rather than lost is judged by what you found, not by what the change claims. A same-purpose replacement is code at file:line (shared middleware, a decorator, a schema or an upstream layer) that guards the same property as the removed check. When you found and read no same-purpose replacement, including when only a comment, docstring or commit message asserts a move, or when the only code you found guards a different property (logging or rate-limiting middleware for a removed auth check), the removal rule applies at your honest confidence and the cap does not apply. A move claim in the change text is never evidence of a replacement. When you found and read a same-purpose replacement and can trace a formerly protected path that bypasses it, that is a demonstrated protection loss: report it at your honest confidence with no cap, because demonstrated loss always takes precedence over the cap. When you found and read a same-purpose replacement whose coverage of every formerly protected path remains unverified, report an unresolved assessment with the same marker: Path names the formerly protected path you could not confirm, Trigger the input that would take it, Consequence what the removed check prevented, and the body cites the replacement at file:line; it is never a capped note. (3) If a finding rests only on the changed code being in a sensitive area, with no defect shown on a changed line, set confidence at or below 0.45 and severity low (no demonstrated defect means no demonstrated consequence) and say what would demonstrate it. Still report it. At that confidence and severity the note stays below the Warning band even when corroborated and persisted. Off-hunk is not the same as unverified: repository context outside the change that you actually read counts as evidence, so an unchanged caller that demonstrably feeds attacker-controlled input into a changed sink is a defect on the changed line at your honest confidence. The unresolved assessment is the exception, not a softer finding: every one is counted as an alarm and must be decided by the owner, so use the marker only with a concrete trigger, path and consequence tied to this change; a note with no concrete failure stays at the sensitive-area ceiling.
diff --git a/plugins/vibe-check/templates/false-positive-rules.md b/plugins/vibe-check/templates/false-positive-rules.md
index dade959..a939b0b 100644
--- a/plugins/vibe-check/templates/false-positive-rules.md
+++ b/plugins/vibe-check/templates/false-positive-rules.md
@@ -8,9 +8,9 @@ Use these rules to filter out issues that should not be reported.
 
 ### Always Filter Out
 
-1. **Pre-existing Issues**
-   - Issue exists in lines not modified by this diff
-   - Use `git blame` to verify if uncertain
+1. **Pre-existing issues the diff does not touch or call**
+   - Issue exists in lines this diff neither modifies, touches nor calls — `git blame` to verify
+   - For unchanged code this diff touches or calls (a helper it now calls, a validator it extends), never filter on 'unchanged' alone: apply the three-outcome rule in your Safe-change recognition block — finding on demonstrated new exposure, pre-existing note on demonstrated unchanged exposure, `needs_verification` when neither is established.
 
 2. **Linter/Compiler Territory**
    - Syntax errors
```

**Other candidate changes under plugins/vibe-check (stat only).**

```text
 plugins/vibe-check/agents/bugs.md                  |   48 +-
 plugins/vibe-check/agents/codex-adversarial.md     |    4 +-
 plugins/vibe-check/agents/impact.md                |   48 +-
 plugins/vibe-check/agents/security.md              |   48 +-
 plugins/vibe-check/phases/review/05-state-all.md   |   10 +-
 plugins/vibe-check/phases/review/05-state.md       |   30 +-
 plugins/vibe-check/phases/review/20-dispatch.md    |    5 +
 .../vibe-check/phases/review/30-collect-score.md   |   16 +-
 plugins/vibe-check/phases/review/40-render-all.md  |    2 +-
 plugins/vibe-check/phases/review/40-render.md      |    6 +
 plugins/vibe-check/phases/review/45-persist-all.md |    2 +-
 plugins/vibe-check/phases/review/45-persist.md     |    4 +-
 plugins/vibe-check/phases/review/50-fix-loop.md    |   54 +-
 plugins/vibe-check/phases/shared/00-contract.md    |    2 +-
 plugins/vibe-check/phases/shared/90-finalize.md    |   51 +-
 plugins/vibe-check/scripts/batch_card.py           |   46 +-
 plugins/vibe-check/scripts/batch_parse.py          |   26 +-
 plugins/vibe-check/scripts/carry_state.py          |  121 +-
 plugins/vibe-check/scripts/codex_translate.py      |   64 +-
 plugins/vibe-check/scripts/finalize_gate.py        |   70 +-
 .../vibe-check/scripts/fixtures/future-schema.json |   10 +-
 plugins/vibe-check/scripts/replay.py               |  242 +++-
 plugins/vibe-check/scripts/score.py                |  392 +++++-
 plugins/vibe-check/scripts/score43.py              |  307 ++++-
 plugins/vibe-check/scripts/statepath.py            |   50 +-
 plugins/vibe-check/scripts/test_agent_prompts.py   |  612 ++++++++--
 plugins/vibe-check/scripts/test_batch_card.py      |  182 ++-
 plugins/vibe-check/scripts/test_batch_parse.py     |   79 ++
 plugins/vibe-check/scripts/test_carry_state.py     |  308 ++++-
 plugins/vibe-check/scripts/test_carry_writers.py   |   32 +-
 plugins/vibe-check/scripts/test_codex_translate.py |  152 +++
 plugins/vibe-check/scripts/test_finalize_card.py   |  164 +++
 plugins/vibe-check/scripts/test_finalize_gate.py   |  193 +++
 plugins/vibe-check/scripts/test_fix_loop_card.py   |   98 +-
 plugins/vibe-check/scripts/test_nv_render.py       |  292 +++++
 plugins/vibe-check/scripts/test_pause_batching.py  |    1 +
 plugins/vibe-check/scripts/test_replay.py          |  359 ++++++
 plugins/vibe-check/scripts/test_score.py           | 1285 +++++++++++++++++++-
 plugins/vibe-check/scripts/test_score43.py         |  307 ++++-
 plugins/vibe-check/scripts/test_state_shape.py     |   21 +
 plugins/vibe-check/scripts/test_statepath.py       |  231 ++++
 .../vibe-check/templates/agent-output-schema.md    |   18 +-
 plugins/vibe-check/templates/codex-focus.txt       |    2 +-
 .../vibe-check/templates/false-positive-rules.md   |    6 +-
 plugins/vibe-check/templates/output-format.md      |   22 +-
 plugins/vibe-check/templates/review-md-schema.md   |    4 +-
 plugins/vibe-check/templates/scoring.md            |   32 +-
 47 files changed, 5759 insertions(+), 299 deletions(-)
```

### Entry 2 — 2026-10-15T00:12:09Z (before the targeted restart)

Committed before any run after the interrupted attempt. Entry 1 stands unchanged. This entry
changes WHERE and HOW the measured sessions run; the candidate, the instructions to the lanes,
the case list, the expected effects and the pass/fail criteria of entry 1 are unchanged.

**Owner instruction (verbatim, 2026-10-14, at the setup checkpoint).**

> Use separate disposable clones for all rehearsal runs. Record the location change before
> restarting, and keep the interrupted attempt marked invalid.
>
> Also isolate the runner's Claude configuration and plugin installation/cache so other sessions
> keep using released 2.11.1. Verify that isolation before running; don't assume a separate repo
> folder isolates the plugin.
>
> Check the effective context-window setting before counting the first result. Record any
> confirmed difference from the pinned setup.
>
> You may drop the leftover test stash only after verifying its identity and contents against the
> test fixture. Use its recorded object ID to locate it again immediately before deletion—don't
> assume it is still stash@{0}. If it contains anything else, leave it untouched.
>
> Once those checks pass, resume automatically. No further approval is needed for routine setup
> corrections within this scope.
>
> The isolated plugin setup needs investigation, but a shared cache shouldn't automatically
> become a requirement that you stop using vibe-check for seven hours.

Stash answer (verbatim): "Yes, drop it, after verifying it matches the notification-bell test
patch. Locate it by its recorded object ID before deletion; don't assume it's still stash@{0}.
Leave every other stash untouched."

**Interrupted attempt — INVALID.** `targeted-reach-new-2-run-1` (kept at
`runs-phase53-dev/attempts/targeted-reach-new-2-run-1-1792022519/`) is invalid: a separate owner
session changed the clone mid-run. It is kept for the record, never scored or counted. The
targeted stage restarts from its first case; `reach-new-2` takes run number 2 so the slot history
stays unambiguous.

**Leftover stash.** In `~/seedsyncarr`, stash object `282e57031302e3a7f7fd362b7e85c19a28b13176`
("detached-a6a0c6d notification-bell edit …"): parents = `a6a0c6d…` (the `reach-new-2` base_sha)
and an index commit with no staged change; no untracked-files part; `git stash show -p` is
byte-identical to `cases/reach-new-2.patch` (both sha256
`11414a59b3ec753fb6a1f66485e920731f09856b53af82dfe4331427c050ae3a`, the case's
`EXPECTED_TREE_DIFF_SHA256`). Re-located by object ID immediately before deletion (it resolved to
`stash@{0}`), oid re-confirmed, dropped. The one other stash (`e1963da…`, a dependabot WIP) was
left untouched. Nothing else in the owner's repos was touched.

**Location change — disposable clones.** Every case now runs in
`~/.b3/phase53-clones/{triggarr,seedsyncarr,roonseek}`, cloned (`--no-hardlinks`) from the
owner's local repos on 2026-10-14, checked out on `main`, origin fetch URL = the GitHub remote,
push URL disabled, `.turingmind/` in `.git/info/exclude`. Every case's `base_sha` and
`feature_sha` resolves in its clone and every case patch applies at its base (16/16 checked). The
owner's ignored `.claude/settings.local.json` (project permission allowlists) was copied into each
clone, so permission handling matches the owner's repos; the owner's other ignored local files
(`.mcp.json`, `.playwright-mcp/`, `.aidesigner/`, `.turingmind/` review state) are NOT in the
clones. No block runs checkout/switch/stash/revert against `~/triggarr`, `~/seedsyncarr` or
`~/roonseek` (runbook commit `45401bb`, `fix(53-14): run rehearsal in disposable clones`).

**Isolated runner — method.** A separate `CLAUDE_CONFIG_DIR` was tried first and rejected: a new
config dir starts logged out (`claude -p` → "Not logged in · Please run /login"), and copying the
owner's OAuth credentials into it would let the runner rotate the shared refresh token and log the
owner's own sessions out. Instead the measured sessions keep the owner's login and settings but
load the candidate from a private copy:

- runner copy `~/.b3/phase53-runner/plugin/vibe-check` (rsync of `plugins/vibe-check`, parity by
  `score43.py fingerprint`), passed with `--plugin-dir`;
- `--settings ~/.b3/phase53-runner/settings-measured.json` = `enabledPlugins:
  {"vibe-check@thejuran": false}` (the installed release is not loaded in that session) plus a
  status-line wrapper that logs Claude Code's own status-line payload locally (model id and
  context-window fields) before rendering the owner's normal status line;
- launch line: `claude --permission-mode manual --plugin-dir '<runner copy>' --settings
  '<runner settings>' --model 'claude-fable-5-1[1m]' --allowedTools
  "Bash,Read,Write,Edit,Grep,Glob,Task,Agent"` in the disposable clone.

The owner's `~/.claude` is never written: no resync into the installed cache, no registry edit, no
relaunch of the owner's sessions. Everything else the measured session sees is the owner's normal
setup, as in Phase 49 and entry 1: the same login, `~/.claude/settings.json` (env incl. the local
model gateway, permissions incl. the holdout denies, both holdout-guard hooks, the other enabled
plugins), the user-level `CLAUDE.md`. The codex lane runs the owner's installed codex plugin 1.0.4
(vibe-check finds its companion at the fixed path `~/.claude/plugins/cache/openai-codex/codex`),
read only; its per-project state is keyed by the clone path, so it cannot collide with the owner's
sessions. Clone auto-memory is parked for the window (the clone paths are new; there is none);
the owner's auto-memory for the real repos is not touched by any block.

**Isolation — verification (before any run).**

- (a) Owner default unchanged — sha256 before building the runner and after the runbook dry run:
  `installed_plugins.json` `6a9cd0aa29ceaefa2146f88a7e9b87588b32b05b6dae4ed13f36c2a6f13fc155`,
  `known_marketplaces.json` `eafbfd5e245d7bbfabb7fb1a6ef00bdf76b22e94d2639daad3b3a3f61fe5e827`,
  `settings.json` `3297ded3de0ea9ce88176642de1cb4fe9a320778a004e9506f1ad0c298942c2a` (all `OK` on
  re-check); the registered `vibe-check@thejuran` cache (`…/thejuran/vibe-check/2.11.1`) has
  fingerprint `f2cf0373f20adbd7ea0818a1a37a9e40f06f759940726e62dffdded4baea34d3`, equal to the
  fingerprint of the `v2.11.1` tag's `plugins/vibe-check` tree (the released build).
- (b) A session WITH the runner flags (`claude -p … --output-format stream-json --verbose`) lists
  in its init metadata exactly one vibe-check plugin: `path
  /Users/julianamacbook/.b3/phase53-runner/plugin/vibe-check`, `source vibe-check@inline`; the
  runner copy's fingerprint `5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26`
  equals the candidate tree's.
- (c) A session WITHOUT the flags lists exactly one vibe-check plugin: `path
  /Users/julianamacbook/.claude/plugins/cache/thejuran/vibe-check/2.11.1`, `source
  vibe-check@thejuran` — the released build.
- Guard: the runbook's `isolation_check` refuses when the owner's registry or settings reference
  the runner, or the runner settings stop disabling the installed plugin (both mutations tripped,
  the unmodified check passed); `post` voids a run whose transcript names the installed release
  cache path.

**Context window.** Both probe sessions in (b) and (c) report `contextWindow: 1000000` for
`claude-fable-5-1[1m]` (`modelUsage` in the result metadata) — the pinned 1M window. The "200k" in
the interrupted attempt's status line was the owner status-line script's fallback label (it shows
200k when the payload carries no window and the display name lacks "1M"), not a window: that
session reached 197,343 context tokens with no auto-compaction. No confirmed difference from the
pinned setup so far; the first measured run is checked again from the status-line payload log
before it is counted, and the result is recorded under that run.

**Differences from entry 1 (all setup, none in the candidate or the instructions).**

1. Location: disposable clones instead of the owner's working repos (above).
2. Plugin load: `--plugin-dir` runner copy with the installed plugin disabled for the session
   (the Phase-49 load path), instead of the resynced installed cache. The fingerprint now covers
   the runner copy.
3. Status line: the measured sessions render the owner's status line through a capture wrapper.
4. Missing in the clones vs the owner's repos: the ignored `.mcp.json` / MCP state and the repos'
   old `.turingmind/` review state (the runbook parks review state before every run anyway).

**Order.** All three clones are available, so the targeted stage runs in entry 1's list order:
`reach-new-1`, `reach-new-2` (run 2), `reach-unchanged-1`, `reach-unchanged-2`, `should-quiet-4`,
`should-quiet-6`, `should-quiet-7`, `triggarr-secret-in-logs`, `triggarr-session-rotation`,
`triggarr-autoescape`.

**Candidate.** Unchanged: `plugins/vibe-check` identical to `0a924de` (fingerprint
`5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26`); repo HEAD at this entry
`45401bb` (runbook change only).

### Entry 3 — 2026-10-15T02:11:10Z (before the final sweep)

Committed before any `final` run. Entries 1-2 stand. Setup only; the candidate and the
instructions are unchanged, so entry 1's expectations and pass/fail criteria apply unchanged.

**Environment folders in the disposable clones.** The owner's working repos carry ignored
environment folders that the fresh clones lacked: `~/triggarr/.venv` (Python 3.11),
`~/roonseek/.venv` (Python 3.13), `~/seedsyncarr/src/angular/node_modules`. During the targeted
stage a measured session (`triggarr-session-rotation`) ran `uv run pytest`, which built a `.venv`
in the triggarr clone (born 2026-10-15T01:48:40Z), and the next review (`triggarr-autoescape`) read
installed Starlette from it. So within the targeted stage: `reach-new-1`, `should-quiet-4/6/7`,
`triggarr-secret-in-logs` and the start of `triggarr-session-rotation` ran without a triggarr
`.venv`; `triggarr-autoescape` ran with one; the roonseek and seedsyncarr runs had no
environment folder. Recorded as a targeted-stage setup difference against Phase 49 (whose reviews
ran in the owner's repos with these folders present).

For the final sweep every clone carries the environment folder its owner repo has, built before
the first final run: triggarr and roonseek `.venv` rebuilt from the clone's committed `uv.lock` at
`main` (`uv sync --frozen --all-extras --all-groups`, same Python minor as the owner's); the
triggarr package set equals the owner's exactly; roonseek lacks one package the owner installed
outside the lock (`musicbrainzngs`), left uninstalled; seedsyncarr `src/angular/node_modules` is a
copy-on-write copy of the owner's (same top-level package list). All three are gitignored in the
clones (status clean). A measured session may still change them (e.g. `uv run` at an older base
re-syncing `.venv`), as it could in the owner's repos.

**Other setup changes since entry 2** (all runbook/clone, none in the candidate): `post` no
longer rescans `tree.diff` (byte-identical to the committed case patch; the email rule misread an added
decorator line, the diff's plus sign followed by `@router.get`) — `e239760`; `.planning/HANDOFF.json` (written by the owner's bm plugin on tool
use) is in each clone's local exclude and removed after each run; an empty clone auto-memory dir
a session creates is moved to the park dir as evidence after each run.

**Final sweep.** No change to `plugins/vibe-check/` since entry 1 (fingerprint
`5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26`, repo HEAD at this entry
`2863299`). `FINAL_FP` is recorded by `STAGE=final p53 fingerprint` on the runner copy, then the
replay guard (26/26 required) and the allowance-gated complete-output diff run on that candidate,
then every `score43.DIFFS` id (12) and the four approved development cases run once, in this
order: `reach-new-1`, `reach-new-2`, `reach-unchanged-1`, `reach-unchanged-2`, then
`score43.DIFFS` order (`triggarr-secret-in-logs`, `triggarr-autoescape`,
`third-organic-should-catch`, `should-quiet-1`, `should-quiet-2`, `should-quiet-3`,
`triggarr-session-rotation`, `triggarr-settings-form-split`, `should-quiet-4`, `should-quiet-5`,
`should-quiet-6`, `should-quiet-7`).

## nv_dropped_weak scope

Current rule (`templates/scoring.md` R5, `score.py`): when a grouped row's lead qualifies on its
own, every co-located member from another lane that does not qualify stays listed in the row's
members, never raises the band, and is counted in the published `nv_dropped_weak` number —
whether or not that lane marked it unresolved. The value observed on each run is listed below as
runs complete (Task 3 sign-off item 7 reads it).

| stage/case/run | nv_dropped_weak |
|---|---|
| targeted/reach-new-1/run-1 | 1 |
| targeted/reach-new-2/run-2 | 1 |
| targeted/reach-unchanged-1/run-1 | 0 |
| targeted/reach-unchanged-2/run-1 | 0 |
| targeted/should-quiet-4/run-1 | 3 |
| targeted/should-quiet-6/run-1 | 2 |
| targeted/should-quiet-7/run-1 | 2 |
| targeted/triggarr-secret-in-logs/run-1 | 3 |
| targeted/triggarr-session-rotation/run-1 | 0 |
| targeted/triggarr-autoescape/run-1 | 1 |
| final/reach-new-1/run-1 | 1 |
| final/reach-new-2/run-1 | 0 |
| final/reach-unchanged-1/run-1 | 0 |
| final/reach-unchanged-2/run-1 | 0 |
| final/triggarr-secret-in-logs/run-1 | 3 |
| final/triggarr-autoescape/run-1 | 0 |
| final/third-organic-should-catch/run-1 | 0 |
| final/should-quiet-1/run-1 | 3 |
| final/should-quiet-2/run-1 | 0 |
| final/should-quiet-3/run-1 | 0 |
| final/triggarr-session-rotation/run-1 | 2 |
| final/triggarr-settings-form-split/run-1 | 0 |
| final/should-quiet-4/run-1 | 3 |
| final/should-quiet-5/run-1 | 0 |
| final/should-quiet-6/run-1 | 0 |

## Cache

resync-cache (2026-10-14, stage targeted): installed cache
`~/.claude/plugins/cache/thejuran/vibe-check/2.11.1` (resolved from `installed_plugins.json`; the
directory name is the registry's, a version string is never compared) backed up to
`~/.b3/vibe-check-cache-bak-pre-phase53-dev`, then rsynced from `plugins/vibe-check/`.
Content parity over the runtime roots (sha256, `score43.py fingerprint`):

- cache `5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26`
- tree  `5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26`

Relaunch: every measured session is a NEW `claude` process started in tmux after the resync, so it
loads the resynced cache at start; the driving session is not a measured session.
`p53 fingerprint` (stage targeted) recorded `CACHE_FP` =
`5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26`; `preflight` OK.

## Targeted-stage fingerprints

- `5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26` — candidate `0a924de` (plugin tree unchanged at `a845fe1`)

## Targeted-stage tally (development rehearsal — not release evidence)

`score43.py dev-tally --runs-root docs/design/reachability-dev/runs-phase53-dev/targeted` (exit 0),
all ten runs on fingerprint `5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26`:

```text
reach-new-1 run-1 alarms=5 nv=1 fired=yes cards=2
reach-new-2 run-2 alarms=1 nv=0 fired=yes cards=2
reach-unchanged-1 run-1 alarms=2 nv=0 fired=yes cards=2
reach-unchanged-2 run-1 alarms=0 nv=0 fired=no cards=0
should-quiet-4 run-1 alarms=1 nv=1 fired=yes cards=2
should-quiet-6 run-1 alarms=1 nv=1 fired=yes cards=2
should-quiet-7 run-1 alarms=1 nv=0 fired=yes cards=2
triggarr-autoescape run-1 alarms=1 nv=0 fired=yes cards=2
triggarr-secret-in-logs run-1 alarms=2 nv=1 fired=yes cards=2
triggarr-session-rotation run-1 alarms=1 nv=0 fired=yes cards=2
runs: 10 · fired runs: 9 · alarms: 15 · needs-verification items: 4 · owner questions: 18
```

Against entry 1: catches 5/5 kept (`reach-new-1`, `reach-new-2`, `triggarr-secret-in-logs`,
`triggarr-session-rotation`, `triggarr-autoescape`; every credit from an alarm row, none from an
NV row). Quiet-shaped: 1/5 quiet (`reach-unchanged-2`); `reach-unchanged-1` fired on a real new
defect outside its key (deleted helper still imported by the tests); `should-quiet-4` (codex
bypass alarm + legacy-value NV), `should-quiet-6` (codex critical + staged-value NV),
`should-quiet-7` (bugs critical, settings save resets a configured value) fired as in Phase 49.
Cards: 2 per run that showed the fix-loop card (the measurement keystrokes), 0 for the clean run.

**Decision: no rule rewording in this stage.** Each quiet fail is one run and traces to a named
rule branch where the case key and the rule as written disagree (codex rule 1 on an input the new
check is written to block, the staged-value "current behavior requires it" branch, the
legacy-value NV branch), and one is a true positive. A generic rewording on that evidence would be
a scope decision, not a defect fix, so the candidate goes to the final sweep unchanged and the
disagreements go to the owner at sign-off. No plugin defect (crash, card misfire, refusal) was
found; the two harness problems found (`post` rescanning the sha-verified case diff; another
plugin's `.planning/HANDOFF.json` in the clone) were fixed in the runbook/clone setup, not the
candidate.

## Final candidate

FINAL_FP: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26
repo_head: ebcd3e4fded8f7793abcca005191ea2c182933f1
recorded (UTC): 2026-10-15T02:11:44Z (`STAGE=final p53 fingerprint` on the runner copy;
`plugins/vibe-check` clean; runner copy == candidate tree; the owner's installed cache untouched at
`f2cf0373…` = the v2.11.1 release)

Replay checks on this candidate (scorer `rev:HEAD`, sha256 `525c5e83…`):

- guardrail `replay.py candidate --name phase53-final` — exit 0; protected catch runs 26: kept 25,
  AMENDED 1 (`runs/triggarr-secret-in-logs/run-2`, baseline basis axis-false, the ledger amendment
  already in force — identical to the 53-07 guardrail), REGRESSED 0, UNEVALUABLE 0 → all 26
  accounted for (`REPLAY-REPORT-phase53-final-guardrail.md`).
- complete-output diff vs `blob:5ca2ddd…` with `ALLOWANCES-phase53-nv.json` — exit 0; runs compared
  154, differing 65, all allowed; **runs with unallowed differences: 0**; allowances unused 0; no
  new allowance added (`REPLAY-REPORT-phase53-final-diff.md`).

## Runs

### targeted/reach-new-2/run-1 — FAILED ATTEMPT (development rehearsal — not release evidence)

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26 (cache resynced; session launched 2026-10-14 19:51 -0400)

Not scored, not counted. While the review agents ran, a separate owner Claude Code session working
in the same `~/seedsyncarr` clone (a julian-orchestrator milestone run, phase 119) stashed the
applied case patch (`stash@{0}`: "detached-a6a0c6d notification-bell edit (stashed 2026-10-14
during v1.7.5 orchestration)"), switched the clone from the detached base to `main` and committed
`2b1ff53` there (19:57). The candidate's Phase 3 git-safety gate detected the change (HEAD moved,
branch switched, stash list grew) and halted the pass before scoring or persisting — the gate
behaved as designed; no plugin defect. No state file was written. The attempt is kept at
`runs-phase53-dev/attempts/targeted-reach-new-2-run-1-1792022519/` (`reason.txt`).

Cleanup without touching the owner's git state: the 16 parked state files were moved back into
`~/seedsyncarr/.turingmind/state/`, the sentinel removed; `revert` was NOT run (its
`git checkout -- .` / branch restore would act on the owner's live clone). `restore-memory` and
`restore-cache` were run so the owner's live sessions see the released 2.11.1 build and their own
auto-memory while the window is paused (an empty `seedsyncarr` memory dir created during the
window is kept as evidence in the park dir). The stash entry holding the case patch is left for
the owner (it is measurement material, safe to drop).

Observation (harness, unresolved): the measured session's status line showed a 200k window
(`0/200k` at start, `197.3k/200k` at the halt) although it was launched with
`--model 'claude-fable-5-1[1m]'`; Phase 49 pinned a 1M window.

Runs paused at this point: `~/seedsyncarr` is in live use by an owner session and `~/triggarr`
holds uncommitted owner work on branch `search-correctness`; only `~/roonseek` is idle.

### targeted/reach-new-1/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 5
needs-verification items: 1
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 1580 | warning | 94 | dcd1153127eb |
| security | triggarr/web/routes.py | 1689 | critical | 100 | 64d6c7dbf247 |
| compliance | triggarr/web/routes.py | 1573 | critical | 100 | 3f7d999d3032 |
| language-python | triggarr/web/routes.py | 1577 | warning | 91 | d8d189dacccf |
| codex-adversarial | triggarr/web/routes.py | 1617 | warning | 94 | 35778acbe810 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| language-python | triggarr/web/routes.py | 1573 | needs-verification | 0 | 0e36cfd6f116 |

keyed defect: triggarr/web/routes.py:1689-1692 (reset_request_post) logs the newly minted password-reset token at WARNING into the unchanged logging path: the buffer sink (triggarr/logging.py:72-84) copies it into log_buffer unredacted because the token is not in the collect_secrets redaction list, and the unchanged in-app log viewer (routes.py:1079-1094) and dashboard render that buffer, so anyone who can read the log viewer can read a live reset token and complete a password reset.
label: development rehearsal - not release evidence
| agent | file | line | band | score | stable_hash | nv | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|---|
| security | triggarr/web/routes.py | 1689 | critical | 100 | 64d6c7dbf247 | no | Password reset token logged in cleartext and surfaced in the authenticated web UI log viewer | security: Password reset token logged in cleartext and surfaced in the authenticated web UI log viewer; codex-adversarial: Reset tokens enter the web-visible log buffer; compliance: Reset token value deliberately written to logs |  |
candidates at site: 1 (alarms 1, needs-verification 0)

AXIS: credit — row 64d6c7dbf247 (alarm, critical 100) — names routes.py:1689 (the new reset-token log call) and the causal failure: the token is logged in cleartext into the log buffer and surfaced in the authenticated web UI log viewer (members codex-adversarial "Reset tokens enter the web-visible log buffer", compliance). Location AND causal failure match the keyed defect.

Setup checks (first run after entry 2): effective context window confirmed from Claude Code's own status-line payload for this session — `model.id claude-fable-5-1[1m]`, `context_window.context_window_size 1000000` — the pinned 1M window (the status line's "200k" label is its fallback, see entry 2); effort shown `medium`, the same as every Phase-49 measured session (their transcripts record `"effort":"medium"`), so no confirmed difference from the pinned setup. Before `/clear`, Claude Code showed its one-time folder-trust prompt for the new clone path; it was accepted ("Yes, I trust this folder") as a setup step — expected once per disposable clone. Session: 15m29s to the fix-loop card; `Stop here…` -> `Abandon` by label. Owner questions: the fix-loop card and the stop card (2, measurement keystrokes). Not scored but recorded: other alarms are off the keyed defect (mkstemp fd leak x2, reset flow unfinished, routes.py:1617).


### targeted/reach-new-2/run-2 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | src/angular/src/app/pages/main/notification-bell.component.html | 28 | critical | 100 | 5d4874b914f1 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

keyed defect: src/angular/src/app/pages/main/notification-bell.component.html:28 now binds unchanged server- and remote-influenced notification text with [innerHTML] instead of {{ notif.text }} interpolation, so markup in those strings is parsed as HTML in every open UI (HTML injection): Angular's sanitizer keeps links, images and formatting, so injected markup can render attacker-controlled links or images in a trusted UI element.
label: development rehearsal - not release evidence
| agent | file | line | band | score | stable_hash | nv | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|---|
| security | src/angular/src/app/pages/main/notification-bell.component.html | 28 | critical | 100 | 5d4874b914f1 | no | Auto-escaped interpolation replaced with raw [innerHTML] binding on notification text | security: Auto-escaped interpolation replaced with raw [innerHTML] binding on notification text; codex-adversarial: HTML injection enables phishing through remote scan errors; bugs: Notification text is now parsed as HTML, so server and remote error strings can inject markup and lose text; impact: HTML injection: server and remote-scan error text is now parsed as HTML, and script blocking depends only on Angular's sanitizer; architecture: Notification.text silently changes from plain text to HTML for every producer, including ones that pass through server-supplied strings; impact: Error text containing angle brackets is silently dropped or mangled for users |  |
candidates at site: 1 (alarms 1, needs-verification 0)

AXIS: credit — row 5d4874b914f1 (alarm, critical 100) — names notification-bell.component.html:28 and the causal failure: escaped interpolation replaced by [innerHTML] so server- and remote-influenced notification text is parsed as HTML (members codex-adversarial "HTML injection enables phishing through remote scan errors", bugs, impact). Location AND causal failure match the keyed defect (scored on HTML injection only, per the README condition).

Run notes: 8m30s to finish; fix-loop card after 495s; `Stop here…` -> `Abandon` by label; one-time folder-trust prompt accepted for the new seedsyncarr clone path. Harness note: after the review persisted its state, the owner's enabled bm plugin wrote an untracked `.planning/HANDOFF.json` (PostToolUse hook, `source: auto-postool`) into the clone; the case base predates the repo's own `**/HANDOFF.json` ignore rule, so `post` refused on the untracked file. The review's scope was tracked changes only (its one finding sits in the case file) and the file was born after the state was persisted, so the review is unaffected. Setup correction: `.planning/HANDOFF.json` added to each disposable clone's local exclude and removed after each run; the partial archive was cleared and `post` rerun on the same run (state file untouched).


### targeted/reach-unchanged-1/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 2
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | src/roonseek/web/_filter_overrides.py | 73 | critical | 100 | 22e86523916a |
| language-python | tests/test_filter_overrides.py | 13 | warning | 89 | 353203614f96 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

Result vs entry 1: pre-registered "quiet: 0 alarms, 0 NV" -> FIRED (2 alarms, 0 NV); a fail under the pre-registered rule. Both alarm rows are one defect, and it is real and new in this commit, outside the case key: the commit deletes `parse_optional_int` from `src/roonseek/web/_filter_overrides.py` while `tests/test_filter_overrides.py:13` (unchanged) still imports it, so pytest cannot collect that module (ImportError) and every test in it stops running. Checked in the clone: at base 754b2f1 the helper is defined and imported by the test; at feature 79031dc it is defined nowhere under `src/` and the test still imports it (the repo fixed the tests in a later commit). Rows: 22e86523916a (impact, critical 100; members codex-adversarial, bugs) and 353203614f96 (language-python, warning 89; member architecture). None of the keyed already-reachable weaknesses (a)-(c) was raised as an alarm or NV item, which is the behaviour the case was built to test. Not a plugin defect, so no change made; the case key (owner-approved) does not cover this break; raised for the owner at sign-off. Run: 13m32s; fix-loop card after 796s; `Stop here…` -> `Abandon` by label; folder-trust prompt accepted once for the roonseek clone; the bm plugin's `.planning/HANDOFF.json` removed after the run.


### targeted/reach-unchanged-2/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 0
needs-verification items: 0
fired: no
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

Result vs entry 1: pre-registered "quiet: 0 alarms, 0 NV" -> quiet (0 alarms, 0 NV) — PASS. The review rendered "No issues to fix" (two advisory notes filtered below threshold: a duplicated guarded-actions flag, and QUEUE/STOP unguarded as before), so no fix-loop card appeared and no keystroke was sent after `/vibe-check:deep-review`. Run: 8m04s. The bm plugin's `.planning/HANDOFF.json` removed after the run.


### targeted/should-quiet-4/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 1
needs-verification items: 1
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 108 | warning | 94 | 987137d5869a |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | needs-verification | 0 | 9ed3915425d3 |

Result vs entry 1: pre-registered "quiet" (QUIET-03: a stricter validator rejecting a legacy value needs evidence the value exists) -> FIRED (1 alarm, 1 NV); a fail under the pre-registered rule (Phase 49: 1/3 fired). Sources: (1) alarm 987137d5869a, codex-adversarial warning 94 at models/config.py:108, "Alternate numeric hosts bypass metadata SSRF protection" — a decimal host (`http://2852039166` -> 169.254.169.254) passes the new metadata block because the shared, unchanged `web/validation.py:150-171` helper misses it; the Claude-lane members at the row (bugs, impact) call it a pre-existing gap in the shared helper. Codex's own instruction (codex-focus rule 1) treats an input the new check is written to block and fails to block as a defect of the change, so this alarm follows the rule as written; whether the case key or that rule should decide is for the owner. (2) NV 9ed3915425d3, bugs lane, at models/config.py:108 — the QUIET-03 legacy-value shape exactly: trigger a disabled instance with a scheme-less URL (`192.168.1.10:7878`) that loaded before, path ensure_config -> load_settings -> Settings(**data) -> validate_url_ssrf, consequence an uncaught ValidationError at startup. This is the new rule's "contract cannot be established -> NV" outcome firing on a quiet case; under R13 it counts as fired. Run: 8m34s; fix-loop card after 496s; `Stop here…` -> `Abandon` by label.


### targeted/should-quiet-6/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 1
needs-verification items: 1
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | c93be6bfe251 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 139 | needs-verification | 0 | b6a6ad20d4b5 |

Result vs entry 1: pre-registered "quiet, or at worst an NV item (which still counts as fired)" -> FIRED (1 alarm, 1 NV); a fail, and worse than the "at worst" bound because the alarm is a critical (Phase 49: 3/3 fired, codex critical at config.py:135/139 — the same shape). Sources: (1) alarm c93be6bfe251, codex-adversarial critical 100 at models/config.py:139, "Wire the new timeout setting into the shutdown drain" — argues the field is already exposed (accepted by tests, serialized at routes.py:227) while scheduler.py:70-81/634 still uses the env/hard-coded 60s, i.e. it reads the staged-value rule's "evidence shows current behavior requires it" branch; members bugs (x2) and impact (impact: "no consumer yet"). (2) NV b6a6ad20d4b5, bugs lane: "New config field is never read" with trigger `shutdown_drain_timeout = 300`, consequence the configured value is ignored. The NV text itself states "the default (60.0) matches the env default, so behavior does not change unless someone sets the field" — the "working optional default" evidence the staged-value rule names as grounds to suppress — and it carries a `pending: confirm the scheduler refactor lands in this phase's next plan` note (a plan promise, which the rule says is never evidence). So the Claude lane landed on the NV outcome while citing the suppression evidence. Run: 7m20s; fix-loop card after 421s; `Stop here…` -> `Abandon` by label.


### targeted/should-quiet-7/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | critical | 100 | 2cc6c506b800 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

Result vs entry 1: pre-registered "quiet, or at worst an NV item" (case excluded from the release verdict, SUPERSESSIONS #001) -> FIRED (1 alarm, 0 NV); a fail (Phase 49: 3/3 fired). Source: alarm 2cc6c506b800, bugs critical 100 at web/routes.py:550, "Every settings save overwrites shutdown_drain_timeout with 60.0 because the settings form has no input for it" — a traced data-loss claim on the changed parse line (form field absent -> `safe_float` default 60.0 -> TOML rewritten), so the lane treated it as demonstrated, not as a staged value; members codex-adversarial ("Apply the saved timeout to the shutdown drain"), bugs x2 (3600 cap vs model bound; no runtime effect), impact (same overwrite). The bounded parse the key cites as harmless is the very line the alarm says resets a configured value. Run: 8m04s; fix-loop card after 465s; `Stop here…` -> `Abandon` by label.


### targeted/triggarr-secret-in-logs/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 2
needs-verification items: 1
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| compliance | triggarr/clients/base.py | 235 | warning | 94 | a535863e0066 |
| codex-adversarial | triggarr/clients/base.py | 252 | critical | 100 | 96232a0aaee9 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| compliance | triggarr/clients/base.py | 254 | needs-verification | 0 | d5a20c80027d |

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| compliance | triggarr/clients/base.py | 235 | warning | 94 | a535863e0066 | validate_connection logs raw httpx exception instead of a sanitized summary | compliance: validate_connection logs raw httpx exception instead of a sanitized summary; security: Revert of security fix reintroduces API-key leak risk via raw httpx exception logging; architecture: validate_connection now logs raw HTTPStatusError, bypassing the repo's established exception-sanitization pattern; bugs: Logging the raw HTTPStatusError can leak URL credentials into logs (sanitization removed); impact: Credential exposure in logs: raw HTTPStatusError text (full request URL) now logged, bypassing the _sanitize_exc convention |  |
| codex-adversarial | triggarr/clients/base.py | 252 | critical | 100 | 96232a0aaee9 | Raw validation errors disclose sensitive response contents | codex-adversarial: Raw validation errors disclose sensitive response contents; security: Revert of security fix reintroduces verbose response-payload exposure via raw pydantic ValidationError logging; architecture: validate_connection now logs raw pydantic.ValidationError instead of the established error-count summary; bugs: Logging the raw pydantic ValidationError puts untrusted response content into logs (sanitization removed); impact: Upstream data exposure in logs: raw pydantic ValidationError text (input_value excerpts of the *arr response) now logged instead of error count |  |
candidates at site with band >= floor: 2

AXIS: credit — row a535863e0066 (alarm, warning 94) at clients/base.py:235 (keyed hunk 230-238, bug line 235) — members name the keyed mechanism, not log formatting: security "reintroduces API-key leak risk via raw httpx exception logging", bugs "Logging the raw HTTPStatusError can leak URL credentials into logs", impact "raw HTTPStatusError text (full request URL) now logged". Row 96232a0aaee9 (alarm, critical 100) at base.py:252 (second keyed hunk) also names the pydantic payload echo into logs. Location AND causal failure match.

Result vs entry 1: pre-registered "catch kept" -> catch kept (Phase 49: 3/3). Additionally 1 NV at base.py:254 (compliance). Run: 11m18s; fix-loop card after 661s; `Stop here…` -> `Abandon` by label.


### targeted/triggarr-session-rotation/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/web/routes.py | 1567 | critical | 100 | 074ca54aca0e |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| architecture | triggarr/web/routes.py | 1567 | critical | 100 | 074ca54aca0e | change_password no longer follows the session-rotation pattern that reset_confirm_post copies | architecture: change_password no longer follows the session-rotation pattern that reset_confirm_post copies; codex-adversarial: Stolen session cookies retain access after password changes; bugs: Password change no longer rotates session_secret, so a hijacked session cookie stays valid after the password is changed; impact: Changing the password no longer logs out other sessions: a stolen session cookie stays valid for up to 30 days; security: Password-change endpoint no longer rotates session_secret, so stolen/compromised sessions survive a password change; architecture: Diff contradicts the tests that encode the rotation behavior |  |
candidates at site with band >= floor: 1

AXIS: credit — row 074ca54aca0e (alarm, critical 100), listed at the keyed site by `catch-candidates` (routes.py:1567 at the case's coordinates) — members name the keyed consequence: security "no longer rotates session_secret, so stolen/compromised sessions survive a password change", impact "a stolen session cookie stays valid for up to 30 days", codex-adversarial "Stolen session cookies retain access after password changes". Location AND causal failure (session eviction lost) match; the survivor title alone is architectural, the members carry the mechanism.

Result vs entry 1: pre-registered "catch kept" -> catch kept (Phase 49: 3/3). Run: 11m18s; fix-loop card after 661s; `Stop here…` -> `Abandon` by label.


### targeted/triggarr-autoescape/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/web/routes.py | 45 | critical | 100 | 31e9e61f6da3 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| impact | triggarr/web/routes.py | 45 | critical | 100 | 31e9e61f6da3 | Reverting to Jinja2Templates(directory=..., autoescape=True) raises a TypeError at import on Starlette 1.x, so the app and container fail to start, and the XSS autoescape guarantee now rests on the installed Starlette version | impact: Reverting to Jinja2Templates(directory=..., autoescape=True) raises a TypeError at import on Starlette 1.x, so the app and container fail to start, and the XSS autoescape guarantee now rests on the installed Starlette version; bugs: Jinja2Templates(autoescape=True) raises TypeError at import: the installed Starlette no longer accepts **env_options, so the app fails to start; architecture: Reverts the supported env= Jinja2Templates form for a removed kwargs passthrough, undoing commit e11187e; compliance: Reverts the project's own fix for broken Jinja2 autoescape config; codex-adversarial: Keep XSS protection independent of deprecated environment options; framework-fastapi: Jinja2Templates(autoescape=True) kwarg is unsupported by the installed Starlette and will raise TypeError at import time; bugs: Revert makes HTML autoescaping (protection against script injection / XSS) depend on the Starlette version; security: Autoescape control reverted to a deprecated starlette code path |  |
candidates at site with band >= floor: 1

AXIS: credit — row 31e9e61f6da3 (alarm, critical 100) at routes.py:45 (keyed bug line) — survivor title names "the XSS autoescape guarantee now rests on the installed Starlette version"; members codex-adversarial "Keep XSS protection independent of deprecated environment options", bugs "Revert makes HTML autoescaping (protection against script injection / XSS) depend on the Starlette version". The escaping/XSS consequence is named at the keyed line, as the key requires. Divergence recorded: the lead mechanism is a TypeError at import on the installed Starlette 1.3.1 (it read `.venv/.../starlette/templating.py`), where the key says autoescape silently no-ops; both are the version-dependent loss the key describes.

Result vs entry 1: pre-registered "catch kept" -> catch kept (Phase 49: 3/3). Run: 10m32s; fix-loop card after 617s; `Stop here…` -> `Abandon` by label. Environment note: this review read the triggarr clone's `.venv`, which did not exist when the clone was made — the previous measured session (`triggarr-session-rotation`) built it by running `uv run pytest` (born 2026-10-15T01:48:40Z). See pre-registration entry 3.


### final/reach-new-1/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 4
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 1581 | warning | 94 | bad49ddb5ff5 |
| security | triggarr/web/routes.py | 1689 | critical | 100 | 453bc76570c9 |
| impact | triggarr/web/routes.py | 1578 | warning | 80 | ef5e6138d458 |
| language-python | triggarr/web/routes.py | 1573 | critical | 100 | 7e83d5f23a4a |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

keyed defect: triggarr/web/routes.py:1689-1692 (reset_request_post) logs the newly minted password-reset token at WARNING into the unchanged logging path: the buffer sink (triggarr/logging.py:72-84) copies it into log_buffer unredacted because the token is not in the collect_secrets redaction list, and the unchanged in-app log viewer (routes.py:1079-1094) and dashboard render that buffer, so anyone who can read the log viewer can read a live reset token and complete a password reset.
label: development rehearsal - not release evidence
| agent | file | line | band | score | stable_hash | nv | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|---|
| security | triggarr/web/routes.py | 1689 | critical | 100 | 453bc76570c9 | no | Password-reset token logged in cleartext, bypassing the app's own secret-redaction sink | security: Password-reset token logged in cleartext, bypassing the app's own secret-redaction sink; codex-adversarial: Reset tokens leak through the web log viewer; compliance: Reset token value is logged in cleartext via logger.warning; impact: Reset token also lands unredacted in the in-app log buffer shown in the web UI, not only in docker logs |  |
candidates at site: 1 (alarms 1, needs-verification 0)

AXIS: credit — row 453bc76570c9 (alarm, critical 100) at routes.py:1689 — names the reset token logged in cleartext past the app's redaction sink; members codex-adversarial "Reset tokens leak through the web log viewer", impact "lands unredacted in the in-app log buffer shown in the web UI". Location AND causal failure match.

vs entry 1: "catch" -> catch kept. Other alarms are off the keyed defect (mkstemp fd/permission rows at 1573-1581). Run 18m20s; fix-loop card after 1082s; `Stop here…` -> `Abandon` by label.


### final/reach-new-2/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | src/angular/src/app/pages/main/notification-bell.component.html | 28 | critical | 100 | 3f078fc6d4f6 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

keyed defect: src/angular/src/app/pages/main/notification-bell.component.html:28 now binds unchanged server- and remote-influenced notification text with [innerHTML] instead of {{ notif.text }} interpolation, so markup in those strings is parsed as HTML in every open UI (HTML injection): Angular's sanitizer keeps links, images and formatting, so injected markup can render attacker-controlled links or images in a trusted UI element.
label: development rehearsal - not release evidence
| agent | file | line | band | score | stable_hash | nv | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|---|
| impact | src/angular/src/app/pages/main/notification-bell.component.html | 28 | critical | 100 | 3f078fc6d4f6 | no | Notification text switched from escaped interpolation to [innerHTML], allowing HTML injection from server and remote error strings | impact: Notification text switched from escaped interpolation to [innerHTML], allowing HTML injection from server and remote error strings; bugs: Plain-text notification messages now parsed as HTML, so text containing < or & gets garbled or dropped; codex-adversarial: Remote error output can inject phishing links into notifications; security: Interpolation replaced with [innerHTML] binding enables HTML/script injection via remote-influenced notification text; architecture: Notification.text silently changes from a plain-text contract to an HTML contract for every producer; impact: Plain-text error messages containing < or & are now mangled or silently dropped; bugs: Removing output escaping opens HTML/markup injection from remote-server error text into the notification bell |  |
candidates at site: 1 (alarms 1, needs-verification 0)

AXIS: credit — row 3f078fc6d4f6 (alarm, critical 100) at notification-bell.component.html:28 — "Notification text switched from escaped interpolation to [innerHTML], allowing HTML injection from server and remote error strings". Location AND causal failure (HTML injection) match; scored on HTML injection only.

vs entry 1: "catch" -> catch kept. Run 8m13s; fix-loop card after 481s; `Stop here…` -> `Abandon` by label.


### final/reach-unchanged-1/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 2
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | src/roonseek/web/_filter_overrides.py | 73 | critical | 100 | 2dab2c1b1e61 |
| architecture | tests/test_filter_overrides.py | 13 | warning | 83 | fe03e1c9ca8c |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs entry 1: "quiet" -> FIRED (2 alarms, 0 NV), same as the targeted run: both rows (2dab2c1b1e61 bugs critical at _filter_overrides.py:73; fe03e1c9ca8c architecture warning at tests/test_filter_overrides.py:13) are the one real new defect outside the case key — `parse_optional_int` deleted while `tests/test_filter_overrides.py:13` still imports it (verified at feature 79031dc; see the targeted run). None of the keyed already-reachable weaknesses (a)-(c) raised. Run: fix-loop card after 767s; `Stop here…` -> `Abandon` by label.


### final/reach-unchanged-2/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 0
needs-verification items: 0
fired: no
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs entry 1: "quiet" -> quiet (0 alarms, 0 NV) — PASS. Clean review (6m47s, no fix-loop card, no keystroke after `/vibe-check:deep-review`). The driver stopped at the clean finish (its clean-finish detector missed this wording); `post`, `/exit` and `revert` were then run by hand on the same run — no keystroke was sent to the review.


### final/triggarr-secret-in-logs/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 2
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 62cb389298ca |
| architecture | triggarr/clients/base.py | 252 | warning | 91 | 021700bd8847 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 62cb389298ca | HTTP error logging exposes proxy credentials | codex-adversarial: HTTP error logging exposes proxy credentials; impact: Credential exposure in logs and the web UI log viewer: raw HTTPStatusError text puts the full request URL, including userinfo passwords and ?token= values, into the log output; security: Revert of named security fix reintroduces raw exception logging (CWE-532); architecture: validate_connection now logs the raw HTTPStatusError, bypassing the codebase's established exception-sanitization pattern; bugs: Reverts key-leak fix: raw HTTPStatusError string (full request URL) logged, bypassing _sanitize_exc data-exposure control; compliance: Raw exception logged instead of extracted field, diverging from sibling handler's convention |  |
| architecture | triggarr/clients/base.py | 252 | warning | 91 | 021700bd8847 | validate_connection now logs the full pydantic ValidationError instead of the established error-count summary | architecture: validate_connection now logs the full pydantic ValidationError instead of the established error-count summary; bugs: Reverts sanitization: raw pydantic ValidationError (including response input values) logged; impact: Data exposure: raw pydantic ValidationError text writes the *arr status response payload (input_value) to logs and the web UI; compliance: Raw pydantic.ValidationError logged instead of extracted count, diverging from prior local convention |  |
candidates at site with band >= floor: 2

AXIS: credit — row 62cb389298ca (alarm, critical 100) at clients/base.py:233 (keyed bug line) — "HTTP error logging exposes proxy credentials"; members bugs "Reverts key-leak fix: raw HTTPStatusError string (full request URL) logged", impact "raw HTTPStatusError text puts the full request URL ... into logs and the web UI log viewer". Row 021700bd8847 (warning) at base.py:252 names the payload echo (bugs/impact members). Location AND causal failure (secret in the exception URL leaked into logs) match.

vs entry 1: "catch kept" -> catch kept. Run 9m17s; fix-loop card after 541s; `Stop here…` -> `Abandon` by label.


### final/triggarr-autoescape/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| compliance | triggarr/web/routes.py | 45 | critical | 100 | 02babc676ff2 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| compliance | triggarr/web/routes.py | 45 | critical | 100 | 02babc676ff2 | Diff reverts the exact fix for Jinja2 autoescape not applying | compliance: Diff reverts the exact fix for Jinja2 autoescape not applying; architecture: Diff reverts the supported Jinja2Templates env= API back to a kwarg the locked Starlette no longer accepts; framework-fastapi: Jinja2Templates called with unsupported `autoescape` kwarg, crashes app at import; bugs: Jinja2Templates(autoescape=True) raises TypeError on the installed Starlette, so the app fails at import; impact: Reverting to Jinja2Templates(directory=..., autoescape=True) raises TypeError at import, so the app cannot start (complete outage). It also hands the XSS autoescape guarantee to a removed, version-dependent library path; security: Diff reverts the prior autoescape fix, crashing the app and dropping the forced-autoescape guarantee; codex-adversarial: Template initialization crashes application startup |  |
candidates at site with band >= floor: 1

AXIS: credit — row 02babc676ff2 (alarm, critical 100) at routes.py:45 (keyed bug line) — survivor "Diff reverts the exact fix for Jinja2 autoescape not applying"; members impact "hands the XSS autoescape guarantee to a removed, version-dependent library path", security "dropping the forced-autoescape guarantee". The escaping/XSS consequence is named at the keyed line. As in the targeted run, the lead mechanism is a TypeError at import on the installed Starlette (the key describes a silent no-op); both are the version-dependent loss of autoescape.

vs entry 1: "catch kept" -> catch kept. Run 10m47s; fix-loop card after 602s; `Stop here…` -> `Abandon` by label. The triggarr clone had its provisioned `.venv` (entry 3).


### final/third-organic-should-catch/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 1
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | src/angular/src/app/services/files/view-file.service.ts | 308 | critical | 100 | 2cc1dbe9a612 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| codex-adversarial | src/angular/src/app/services/files/view-file.service.ts | 308 | critical | 100 | 2cc1dbe9a612 | Completed extracted files show over 100% and lose completion indicators | codex-adversarial: Completed extracted files show over 100% and lose completion indicators; bugs: Removed clamp lets percentDownloaded exceed 100 for extracted files (shows e.g. '199%', loses Done/success state); language-typescript: Removed clamp reintroduces documented >100% progress bug; impact: Removing the percentDownloaded clamp brings back >100% progress (e.g. '199%') and breaks the '=== 100' checks for extracted files; architecture: Removing the clamp breaks the 0-100 contract for percentDownloaded and leaves view code to handle out-of-range values |  |
candidates at site with band >= floor: 1

AXIS: credit — row 2cc1dbe9a612 (alarm, critical 100) at view-file.service.ts:308 (keyed bug lines 307-309) — "Completed extracted files show over 100% and lose completion indicators"; members bugs "Removed clamp lets percentDownloaded exceed 100 ... loses Done/success state", impact "breaks the three-equals 100 checks". Names the missing clamp / out-of-range value. Location AND causal failure match.

vs entry 1: "catch kept" -> catch kept. Run 8m01s; fix-loop card after 466s; `Stop here…` -> `Abandon` by label. The seedsyncarr clone had its provisioned `node_modules` (entry 3).


### final/should-quiet-1/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 0
needs-verification items: 0
fired: no
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs entry 1: "quiet" -> quiet (0 alarms, 0 NV) — PASS (Phase 49: 0/3 fired). The fix-loop card still appeared (rows below the Warning band are listed for fixing); `Stop here…` -> `Abandon` by label. Run 9m09s; card after 527s.


### final/should-quiet-2/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 0
needs-verification items: 0
fired: no
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs entry 1: "quiet" -> quiet (0 alarms, 0 NV) — PASS (Phase 49: 0/3 fired). Fix-loop card shown for sub-Warning rows; `Stop here…` -> `Abandon` by label. Run 5m48s; card after 330s.


### final/should-quiet-3/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 0
needs-verification items: 0
fired: no
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs entry 1: "quiet" -> quiet (0 alarms, 0 NV) — PASS (Phase 49: 1/3 fired). Clean review: no fix-loop card, no keystroke after `/vibe-check:deep-review`. Run 6m20s. The roonseek clone had its provisioned `.venv` (entry 3).


### final/triggarr-session-rotation/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 2
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 1567 | critical | 100 | 312fd3c4c345 |
| bugs | triggarr/web/routes.py | 1581 | warning | 90 | 494fa8e8b5c1 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 1567 | critical | 100 | 312fd3c4c345 | Stolen sessions retain authenticated access after password changes | codex-adversarial: Stolen sessions retain authenticated access after password changes; security: Password change no longer invalidates other active sessions (session_secret rotation removed); impact: Password change no longer rotates session_secret, so a stolen session cookie stays valid after the password is changed; compliance: change_password reverts the session-secret-rotation security fix, breaking its documented mirror with reset_confirm_post; bugs: Password change no longer rotates session_secret, so sessions stolen before the change stay valid for 30 days; architecture: change_password no longer follows the credential-change pattern that reset_confirm_post documents as its mirror; architecture: Diff contradicts tested contract in test_auth_routes and test_auth_integration |  |
| bugs | triggarr/web/routes.py | 1581 | warning | 90 | 494fa8e8b5c1 | Existing tests that assert rotation, cookie re-issue and other-device eviction will now fail | bugs: Existing tests that assert rotation, cookie re-issue and other-device eviction will now fail; impact: Existing tests that assert rotation, cookie re-issue and eviction will fail, which blocks the test gate; impact: The audit log line for session invalidation on password change is removed |  |
candidates at site with band >= floor: 2

AXIS: credit — row 312fd3c4c345 (alarm, critical 100), listed at the keyed site by `catch-candidates` (routes.py:1567) — "Stolen sessions retain authenticated access after password changes"; members security "no longer invalidates other active sessions", bugs "sessions stolen before the change stay valid for 30 days". Location AND causal failure (session eviction lost) match.

vs entry 1: "catch kept" -> catch kept. Second alarm 494fa8e8b5c1 (bugs warning at routes.py:1581): existing tests asserting rotation will fail — also at the keyed site, a consequence of the same change. Run 9m32s; fix-loop card after 556s; `Stop here…` -> `Abandon` by label.


### final/triggarr-settings-form-split/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 2
needs-verification items: 0
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/templates/settings.html | 18 | critical | 100 | 6b98d7648011 |
| bugs | triggarr/templates/settings.html | 134 | warning | 94 | 69b8cb779a87 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |
|---|---|---|---|---|---|---|---|---|
| architecture | triggarr/templates/settings.html | 18 | critical | 100 | 6b98d7648011 | Diff reverts commit 542d5dd, splitting the single save_settings contract back into two forms so Save drops every General field | architecture: Diff reverts commit 542d5dd, splitting the single save_settings contract back into two forms so Save drops every General field; security: Diff reverts a tested fix: General settings silently reset to hardcoded defaults on every instance save; bugs: General settings form has no submit button, so edits to General fields can never be saved; codex-adversarial: Keep General controls associated with the Save Settings form; impact: Reverts the 542d5dd fix: every 'Save Settings' click silently resets all General settings to their defaults |  |
| bugs | triggarr/templates/settings.html | 134 | warning | 94 | 69b8cb779a87 | Save Settings now posts without General fields, so the handler resets every General setting to its default | bugs: Save Settings now posts without General fields, so the handler resets every General setting to its default |  |
candidates at site with band >= floor: 2

AXIS: credit — row 6b98d7648011 (alarm, critical 100) at settings.html:18 (keyed hunk 15-28) — "splitting the single save_settings contract back into two forms so Save drops every General field"; members impact "every Save Settings click silently resets all General settings to their defaults", bugs "General settings form has no submit button". Row 69b8cb779a87 (warning) at settings.html:134 (keyed hunk 131-137) names the same fields-not-submitted reset. Location AND causal failure (broken form association, silent data loss on save) match.

vs entry 1: "catch kept" -> catch kept. Run 13m04s; fix-loop card after 752s; `Stop here…` -> `Abandon` by label.


### final/should-quiet-4/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 1
needs-verification items: 2
fired: yes
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 108 | warning | 94 | 37b2056f0936 |
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/models/config.py | 108 | needs-verification | 0 | b04b099a1960 |
| impact | triggarr/models/config.py | 91 | needs-verification | 0 | 5ded17410c7d |

vs entry 1: "quiet" (QUIET-03) -> FIRED (1 alarm, 2 NV); a fail (Phase 49: 1/3 fired; targeted run: 1 alarm + 1 NV, same shape). Sources: alarm 37b2056f0936, codex-adversarial warning at models/config.py:108 — "Numeric IPv4 notation bypasses the metadata SSRF block" (the bypass sits in the unchanged shared helper; an impact member calls it pre-existing; codex rule 1 treats an input the new check is written to block as a defect of the change). NV b04b099a1960 (bugs) — legacy scheme-less URL in a disabled instance now aborts startup; NV 5ded17410c7d (impact, config.py:91) — `http://0.0.0.0:7878` / `http://[::]:7878` hand-edited URLs now rejected. Both NV items are the new legacy-value rule's "contract cannot be established -> NV" outcome. Run 8m06s; fix-loop card after 466s; `Stop here…` -> `Abandon` by label.


### final/should-quiet-5/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 0
needs-verification items: 0
fired: no
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs entry 1: "quiet" -> quiet (0 alarms, 0 NV) — PASS (Phase 49: 0/3 fired). Clean review: no fix-loop card, no keystroke after `/vibe-check:deep-review`. Run 6m16s.


### final/should-quiet-6/run-1 — development rehearsal — not release evidence

fingerprint: 5bee4c114038e737da9553262b1702c656f2ab14f9bf1d78f7dd22406b85ec26

alarms: 0
needs-verification items: 0
fired: no
alarm rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
needs-verification rows:
| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|

vs entry 1: "quiet, or at worst an NV item" -> quiet (0 alarms, 0 NV) — PASS (Phase 49: 3/3 fired). Same fingerprint as the targeted run, which fired (codex critical + bugs NV): run-to-run variance on one build, so one run is weak evidence either way. Clean review: no fix-loop card, no keystroke after `/vibe-check:deep-review`. Run 5m59s.

