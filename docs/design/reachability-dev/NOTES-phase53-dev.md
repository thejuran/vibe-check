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

