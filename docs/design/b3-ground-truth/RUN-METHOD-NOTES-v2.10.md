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
