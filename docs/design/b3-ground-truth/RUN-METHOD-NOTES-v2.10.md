# B3 v2.10 run-method notes (working log — editable during runs; feeds the baseline report's Method/Limitations)

> Not a run artifact and not covered by the pre-registration immutability rule (that covers
> ANSWER-KEY-v2.10.md and PREREGISTRATION-v2.10.md only). Records protocol clarifications,
> gate deviations, and the per-session harness fingerprints, in the open, before scoring.

Corollary the fingerprint machinery depends on: BECAUSE this file is mutable, nothing
downstream may trust its live content — the 38-05 gates read fingerprint blocks from
committed blobs (`git show`), bound per run by commit sha (see the run-binding convention
below), never from the live file.

## Carried remedies from v2.9 (pre-applied)

Known friction classes from the v2.9 runs, seeded here so they are not rediscovered
mid-run:

- **N-01 (conversation isolation — MANDATORY in v2.10):** clearing state.json does NOT
  erase model memory. `/clear` (or a fresh conversation) is REQUIRED immediately before
  EVERY `/deep-review` run — run 2 and 3 of a diff, retries after a failed run, and
  resumed multi-day sessions included — so no run can remember a prior run's findings.
  In v2.10 this is built into every per-run checklist block as a typed `CLEARED`
  attestation archived per run as `clear.txt` (a run without it is unscoreable). The v2.9
  wording made this a notes-file practice; v2.10 makes it a gate, because a
  same-conversation replicate leaks prior findings while `len(passes)`, head_sha, and
  tree.diff all still pass — an invisible invalidation.

- **N-02/N-05 (old-base local-exclude remedy — persists):** the `.git/info/exclude`
  `turingmind` entries persist in triggarr/seedsyncarr/roonseek — verified 2026-07-27.
  Expect the same class (owner-local tool artifacts gitignored at current main but not at
  an old pinned base) in any newly pinned repo; the remedy is the same local-exclude
  mechanism, and no run is discarded when only the untracked-guard trips (8f1/8f2 passing
  proves the reviewed diff was unaffected).

- **N-03/N-04 (uv.lock mid-run rewrites — prevention now BUILT IN):** the
  `chflags uchg`/`nouchg` protection is built into the v2.10 checklist for
  triggarr/roonseek/dashboard; seedsyncarr has no uv.lock. The flag is HELD for the
  entire duration of a diff's runs — asserted present before every run and through
  FAILED-RUN RECOVERY and retries, cleared ONLY by the revert-once block (success or
  explicit abandonment), which asserts it cleared (N-04: recovery must never strip the
  protection before a retry).

## Harness fingerprints

Rationale: archived state.json pass keys are `agents_run, diff_range, findings, head_sha,
mode, pass_number, timestamp` ONLY — no model/harness metadata. Without a committed
fingerprint the "Claude 5 harness" claim is unsubstantiated. Each run session appends
exactly ONE fingerprint block beneath this section (checklist STEP 0.25, authored in
38-02, does it) and commits it — in a commit touching only this file — BEFORE any run it
governs is triggered.

### Per-session record format

Block header (SINGULAR, timestamped, timezone-bearing — this IS the unique session ID):
`## Harness fingerprint — ` followed by the output of `date '+%Y-%m-%dT%H:%M:%S%z'`, e.g.
`## Harness fingerprint — 2026-07-28T14:02:05-0400`. Second precision + timezone offset
make each session header unique; the 38-05 gate counts ONLY headers matching
`^## Harness fingerprint — [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}[+-][0-9]{4}$`
and HARD-FAILS on duplicate session IDs.

Field lines (bare `key: value` lines inside the block, in this order):

- `claude-code:` — the exact `claude --version` output. The command must SUCCEED — a
  session where `claude --version` fails cannot be fingerprinted; `unknown` is never
  recorded and never accepted.
- `model:` — typed by the owner from the session UI via a read prompt (acceptance rule
  below).
- `codex:` — the exact `codex --version` output; must contain a full x.y.z version.
- `cache-root:` — the resolved installed-cache root: the same `sort -V | tail -1`
  resolution the sealed review.md uses to pick the cache its helper scripts run from,
  re-derived by STEP 0.25 (38-02) and required to resolve to the `2.9.0` dir. The
  fingerprint thereby records which installed tree the session's runs resolved helpers
  from.

The documented append command (STEP 0.25 references this format; the `$(date …)` template
line sits inside the bash fence and falls outside the anchored gate pattern, so a
zero-fingerprint file can never satisfy the gate):

```bash
{ echo "## Harness fingerprint — $(date '+%Y-%m-%dT%H:%M:%S%z')";
  echo "claude-code: $(claude --version)";
  echo "model: <typed by the owner from the session UI — see the acceptance rule>";
  echo "codex: $(codex --version)";
  echo "cache-root: <the STEP 0.25-resolved installed-cache root — must be the 2.9.0 dir>"; } >> docs/design/b3-ground-truth/RUN-METHOD-NOTES-v2.10.md
```

### The model-value acceptance rule (verbatim, so the owner knows what to type)

The 38-05 scoring gate REJECTS any `model:` line containing `<`, `>`, or the words
"record", "TBD", or "placeholder", and ACCEPTS ONLY a value whose FULL text matches,
case-insensitively, the exact grammar
`^(claude[- ])?(fable|opus|sonnet|haiku)[- ]5(\.[0-9]+)?(-[0-9]{8})?$`.

- Accepted examples: "Fable 5", "Claude Fable 5", "Opus 5.1", "claude-fable-5",
  "claude-fable-5-20260115".
- REJECTED examples (listed so the owner is never surprised): "Claude Sonnet 4.5" (a
  4-generation model — the grammar requires the standalone generation number 5),
  "Claude Opus 4 (fallback from 5)" (an incidental 5 in prose — the full-line anchor
  rejects it), and any placeholder. A wrong-generation or decorated value cannot certify
  a session.
- The v2.9-era loose pattern shape (an unanchored `.*5` substring match) is FORBIDDEN —
  it substring-accepts both rejection examples above.

### The harness pin (convention only — values are NOT recorded at seed time)

A `## Harness pin` section is appended ONCE by plan 38-02, at WAIT-1-open time, BEFORE
any fingerprint and before any run. It contains three bare lines — `pin-claude-code:`
(the exact `claude --version` output; the command must succeed — `unknown` is never
pinned nor accepted), `pin-codex:` (the exact `codex --version` output, full x.y.z), and
`pin-model:` (lowercase family+generation, e.g. `fable 5`).

EVERY session fingerprint must tuple-match the pin: `claude-code:` and `codex:`
byte-equal their pin lines; the `model:` value, normalized to lowercase with `-` folded
to space, must carry the pinned family+generation — and all sessions' normalized model
values must be IDENTICAL to each other. STEP 0.25 asserts this at session start
(HARD-STOP on drift, before any run) and 38-05 re-asserts it per fingerprint from
committed blobs, so the 30–36-run baseline can never silently aggregate different models
or CLI harnesses.

The pin may be corrected ONLY while zero fingerprints and zero runs-v2.10 commits exist;
after that, harness drift makes the affected runs unscoreable — the owner reruns them
under the pinned harness or explicitly directs a recorded separate-cohort seal (never
silent aggregation). All `pin-*` field labels in this seed are backticked — no seed line
begins at column 0 with a bare pin-shaped line, so the anchored pin parses are
unsatisfiable until 38-02 records real values.

### The run-binding convention (commit-anchored AND PRE-RUN)

The notes file is mutable, and a binding created at archival time could adopt a
fingerprint appended AFTER the review ran — so the binding is created BEFORE the run is
triggered, from committed blobs, never at archival and never from the live file.

Every archived run dir carries a `session.txt` of exactly TWO lines:

- line 1 = the timestamp of the governing committed fingerprint header;
- line 2 = the 40-hex sha of the COMMIT that introduced that header;

both derived from COMMITTED blobs (`git show HEAD:<this file>` and `git log -S`) by the
per-run PRE-RUN sequence BEFORE the run is triggered.

The archival step VERIFIES the pre-run records exist (it never writes them) and asserts
that the clear.txt timestamp AND the fingerprint commit's committer time both strictly
precede the archived `state.passes[-1].timestamp` (UTC ISO `…Z` form, per the v2.9
archive) — an attestation or fingerprint created after the review ran cannot certify it.

38-05 gates scoring on COMPLETE run-to-fingerprint coverage: for every run, the named
commit must have introduced the block (present at that commit, absent at its parent),
touched only this file, be a strict ancestor of the run-capture commit, the block's
field lines at HEAD must byte-equal the field lines at that commit (a later edit to a
referenced block fails the gate), the tuple must match the pin, and the ordering rule
must hold. Never a mere count, never the live file.

### The run dir's fifth file: clear.txt (the N-01 attestation)

`clear.txt` = the N-01 conversation-isolation attestation (`<timestamp> CLEARED`),
written by the per-run PRE-RUN sequence AFTER the run's state-fresh assert and BEFORE
the run is triggered (a run attempted out of order STOPs before any attestation artifact
exists; the run dir is guarded no-clobber). With it the run dir holds five files:
state.json, tree.diff, tree.diff.sha256, session.txt, clear.txt.

### Known harness-shift component

v2.9 runs were on codex-cli 0.133.0; the current CLI is 0.153.4 (pin corrected from 0.145.0 on 2026-09-05, before any fingerprint or run — codex was upgraded after the original pin) — record this as an
explicit harness-shift component in the RESULTS-v2.10.md limitations (the harness =
model + CLI versions bundled; the re-measure cannot decompose model vs codex-cli within
the shift).

### Naming convention (load-bearing for the 38-05 harness-evidence gate)

The section header above is the PLURAL `## Harness fingerprints`; each appended
per-session block header is the SINGULAR timestamped form. The plural seed header and
the `$(date …)` template line inside the documented append command (which sits inside a
bash fence, starting with `{ echo`) both fall outside the anchored gate pattern, so a
zero-fingerprint file can never satisfy it.

## Seal verifier pin

verifier-commit: a407539115872137dc55d99aef439a9c5a4f16d9
verifier-sha256: 7be8ed39e9ad38a521caa17316fcea8894a7f25ab54b72af7b673a9bff75daaf

Every consumer of the seal check first asserts the live verifier file's sha256 equals
verifier-sha256 AND that exactly one commit ever touched the path, then executes the
check via `git show <verifier-commit>:<path> | python3 -` — the pinned blob, never the
working file.

## Harness pin

pin-claude-code: 2.1.261 (Claude Code)
pin-codex: codex-cli 0.153.4
pin-model: fable 5

Every session fingerprint must tuple-match these three lines; correction is legal ONLY
while zero fingerprints and zero runs-v2.10 commits exist.

## Harness fingerprint — 2026-09-05T18:04:05-0400
claude-code: 2.1.261 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
cache-root: /Users/julianamacbook/.claude/plugins/cache/thejuran/vibe-check/2.9.0

## Harness fingerprint — 2026-09-05T18:09:56-0400
claude-code: 2.1.261 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
cache-root: /Users/julianamacbook/.claude/plugins/cache/thejuran/vibe-check/2.9.0

## Per-run Codex outcome (D-13 — owner-reported one-liner + state.json agents_run check; ledger committed at diff boundaries)

- triggarr-secret-in-logs run 1 (2026-09-05, capture 48dd571): codex JOINED — owner: "Codex smoke check: PASS via the background-shell output file (the deprecated TaskOutput reader could not re-open the reaped task, so collection used the harness's documented output-file path)"; state.json: 1 finding attributed to codex-adversarial (agents_run lists the 8 native agents only — codex participation is visible via finding attribution, as in v2.9 scoring).
- HARNESS OBSERVATION (runs 1-2, 2026-09-05): the shipped deep-review collects the Codex result via the TaskOutput reader, which Claude Code 2.1.261 reports as deprecated and which fails to re-open a reaped background task ("Error: No task found with ID: <id>"); the command then falls back to the documented background-shell output-file path and Codex still joins. Not a run defect (state.json unaffected); record in RESULTS-v2.10 limitations as a harness-shift component and as Phase 40 (orchestration rewrite) input.

## v2.10 run-time deviations (recorded in the open, before scoring)

- **N-06 (state-key deviation, triggarr-secret-in-logs run 2, 2026-09-05 — owner decision: ACCEPT with deviation recorded):**
  the fresh block detached `~/triggarr` at base f4366a2 (reflog 18:02:22) and run 1 wrote the
  expected detached key `triggarr-.json`. At 20:45:59 (reflog: "checkout: moving from f4366a2… to
  main"; no hook — origin in the owner's session/terminal, not identified) the clone was switched
  onto branch `main` (same commit). Run 2 (pass ts 2026-09-06T01:03:08Z) therefore wrote its state
  to `triggarr-main.json`; that file did not pre-exist (pass_number 1). The reviewed tree, HEAD and
  diff scope (HEAD..working-tree) were identical to run 1 — only the state filename differed.
  Remedy: the post-run block (checklist lines 472-519, original bytes sha256
  da8acaae4737ae14591eaa8d64f81c9be34d69ab0472f527bc96e6de962b494b) was executed with EXACTLY ONE
  substitution — line 4 `STATE_FILE=$STATE_DIR/triggarr-.json` → `triggarr-main.json` (modified
  bytes sha256 a4045873e149a74b45193104dc70294bb281f7c7bc822eef5c6337e6eff87e60); every assert
  (pre-run ordering, len(passes)==1, head==base, full-worktree sha, touched-path set, no strays,
  commit scope, sealed v2.9 tree) passed unchanged; capture commit 7072418. Step 8h removed
  `triggarr-main.json`, so no carry-forward channel remains. The clone was re-detached at f4366a2
  before run 3 (expected key `triggarr-.json` restored). Watch-for: any branch switch in a source
  clone mid-diff changes the state key — check `git branch --show-current` is EMPTY before every run.
- triggarr-secret-in-logs run 2 (2026-09-05, capture 7072418, N-06 deviation): codex JOINED — codex-adversarial finding conf 99 (reproduced Basic-Auth credential leak on a 502); Codex result again collected via the output-file fallback after the deprecated TaskOutput reader failed ("No task found with ID").
- triggarr-secret-in-logs run 3 (2026-09-05, capture cf9ecf0): codex JOINED — codex-adversarial listed in agents-dispatched.txt and 1 medium finding attributed ("Validation error formatting can bypass secret redaction"); the owner saw no quoted Codex note in the transcript because the finding rendered at medium tier. Diff 1 complete: 3/3 runs captured (48dd571, 7072418, cf9ecf0), clone restored main@f4366a2.
- OBSERVATION (limitations input): run 3 architecture finding titled the diff "a byte-for-byte revert of security fix d47b4c2" — the agents can see that a REVERSED planted diff undoes a commit present in history. Kit-design artifact of reversed should-catch diffs (not new to v2.10); note in RESULTS-v2.10 limitations.
- triggarr-autoescape run 1 (2026-09-05, capture 8655240): codex JOINED — codex-adversarial dispatched; 1 high finding attributed ("Unsupported autoescape argument prevents startup"); owner saw no Codex line in the transcript.
- triggarr-autoescape run 2 (2026-09-05, capture 5aa6dbe): codex JOINED — codex-adversarial dispatched; 1 high finding attributed ("Preserve the supported Jinja2 environment initialization").
- triggarr-autoescape run 3 (2026-09-05, capture bccf302): codex JOINED — codex-adversarial dispatched; 1 high finding attributed. Diff 2 complete: 3/3 runs captured (8655240, 5aa6dbe, bccf302), clone restored main@f4366a2.

## Harness fingerprint — 2026-09-05T22:17:54-0400
claude-code: 2.1.261 (Claude Code)
model: Fable 5.1
codex: codex-cli 0.153.4
cache-root: /Users/julianamacbook/.claude/plugins/cache/thejuran/vibe-check/2.9.0
- third-organic-should-catch run 1 (2026-09-05, capture f0896a1, seedsyncarr session fingerprint 93b42fa): codex JOINED (agents-dispatched: "joined, working-tree scope, smoke-check PASS"); 1 medium finding attributed ("Restore the 100% cap for extracted files").

- **N-07 (state-key deviation #2 — TOOL-SIDE, third-organic-should-catch run 2, 2026-09-05 — accepted under the N-06 policy):**
  the clone stayed detached at 3db8b48 (reflog: no checkout after 22:16:27), yet the shipped
  command wrote run 2's state to `seedsyncarr-HEAD.json` (run 1 had written `seedsyncarr-.json`).
  review.md Phase 0.5 binds `BRANCH_SLUG=$(git branch --show-current | tr '/' '-')` (empty when
  detached); the orchestrating model evidently derived the slug via an `--abbrev-ref HEAD`-style
  call this pass. This is nondeterminism of the MEASURED tool's prose orchestration on a detached
  checkout (Phase 40 orchestration-rewrite input; RESULTS-v2.10 limitations). The file was fresh
  (pass_number 1, single pass, head==base, ts 02:46:14Z after clear.txt 22:34:34-0400); tree,
  HEAD and diff scope identical to run 1. Remedy identical in form to N-06: post-run block
  (checklist lines 1460-1507, original bytes sha256 fe6b2820d7356771c70a4ac1e16d5064b9fa61b77d0418beaefc15a433b52526) executed with EXACTLY ONE substitution —
  line 4 STATE_FILE `seedsyncarr-.json` → `seedsyncarr-HEAD.json` (modified bytes sha256 43a81b02686553a2879e27bebfdd63a42bf625a6287b08f2fd98a859416571ed);
  every assert passed unchanged; capture commit 68937bf; step 8h removed the file (no carry-forward).
  STANDING RULE from here (assistant-applied, recorded per occurrence): before each post-run,
  identify the ONE state JSON modified after that run's clear.txt; if its name differs from the
  checklist's STATE_FILE, capture it via the same one-line substitution and log the run here;
  before each pre-run, assert NO state JSON is newer than the previous run's capture. Protective:
  the owner's pre-existing `seedsyncarr-main.json` (15:51 today, real state) is parked as
  `seedsyncarr-main.json.b3-n07-parked` for the rest of this diff so a "main"-resolving pass can
  never append to it; restored verbatim at this diff's revert step.
- third-organic-should-catch run 2 (2026-09-05, capture 68937bf, N-07 deviation): codex JOINED (agents-dispatched "(joined)"); 1 medium finding attributed ("Removing the clamp breaks completed-file progress").
