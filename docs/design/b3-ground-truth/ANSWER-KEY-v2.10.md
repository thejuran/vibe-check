# B3 v2.10 Answer Key — per-diff SITE + AXIS + BAND for the NEW diffs (pre-registered)

**Authored:** 2026-09-05, BEFORE any new-diff run (sealed by seal-2 strictly before the
first `runs-v2.10/<new-diff-id>/` commit). Covers ONLY the six diffs added by plan 38-03.
The six carried-over v2.9 diffs get NO rows here — they score against the sealed v2.9
blob (two-seal independence; see the manifest's carried-over key reference). Scoring
input: `state.passes[-1].findings[]` from the archived per-run
`runs-v2.10/<diff-id>/run-<n>/state.json` (D-06 — never the chat transcript).

## Pre-registration

The pre-registration proof (this file's committing-commit hash + the SHA-256 of its
committed blob) is recorded in the SEPARATE manifest
`docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md`, appended there by seal-2 — the
manifest's single permitted follow-up commit — so this key blob never contains its own
hash. The scoring wave (38-05) recomputes
`git show <the manifest's recorded key commit>:docs/design/b3-ground-truth/ANSWER-KEY-v2.10.md | shasum -a 256`,
compares it to the manifest's recorded digest, and EXITS NON-ZERO on mismatch; it parses
the SCORED rows FROM that committed blob (never this live file); it requires
`git merge-base --is-ancestor <the recorded key commit> HEAD` to exit 0 and that every
commit touching `docs/design/b3-ground-truth/runs-v2.10/<new-diff-id>/` descends from
seal-2. This key file therefore carries NO output-dependent and NO
self-referential-hash placeholders — the two proof values live only in the manifest,
filled from git BEFORE any new-diff run.

## Preamble rules (by reference — sealed in the v2.9 blob, not re-authored)

Scoring semantics for the rows below are EXACTLY the v2.9 rules sealed in the blob at
`git show ef0ab67cb45957167c99eff468077348432e1474:docs/design/b3-ground-truth/ANSWER-KEY-b3.md`:
the three-gate catch rule (SITE + AXIS + BAND as INDEPENDENT gates, D-07 —
right-site-wrong-axis or right-axis-below-band = detected-below-threshold = a MISS in
the headline number), the D-08 FP rule (any critical/warning finding on a should-quiet
run is an FP; medium/low = noise-notes, not FPs), the D-09 no-rounding aggregation rule
(exact fractions), the A8 fold (exemptions are content-justified, never name-justified),
the A16 rule (a should-quiet diff is safe ON a specific named axis, never "globally
safe"), the head check (every scoreable run has `len(passes) == 1` and
`passes[-1].head_sha` equal to the row's base_sha), and the D-13 method note (runs
measure the shipped default, codex=auto). None of that sealed rule text is re-authored
here. A8 applicability was re-checked at key-authoring time for the six new picks: NO
new diff carries a `/health`-style or name-suggestive route, so A8 applies as the
standing preamble rule with no per-row exemption statement required.

## Should-catch rows (2 new diffs × N=3 runs)

Line ranges are post-image (the patched tree at the row's base_sha). base_sha is BOTH the
tree the SITE line numbers are keyed to AND the exact `head_sha` scoring must find in the
run state.

| diff-id | SITE (file : planted-hunk lines) | AXIS (mechanism the finding MUST name) | expected band (floor) | base_sha |
|---|---|---|---|---|
| triggarr-session-rotation | `triggarr/web/routes.py` : 1445-1451 (bug line 1448, the hash-only `model_copy` that drops the `session_secret` rotation) AND/OR 1459-1469 (bug line 1462, the direct `return` that drops the fresh-cookie re-issue) — either hunk satisfies SITE | **Stale-session survival — password change no longer evicts existing sessions**: the `session_secret` rotation is gone from the atomic config write, so every cookie signed with the old (unchanged) secret stays valid for the full 30-day COOKIE_MAX_AGE — a stolen or compromised session SURVIVES the password change, defeating the most common reason users change a password. The finding must name the session-eviction/invalidation consequence (old sessions remain valid / compromised session survives). NOT "dead code or comment cleanup", NOT "logging removed", NOT a response-refactor or cookie-attribute nit — a finding at routes.py:1448 calling it refactor cleanup is right-site-wrong-axis = detected-below-threshold = a MISS. | warning (security) | f4366a261fcf9bab01b48ad89279aac973a7d9b1 |
| triggarr-settings-form-split | `triggarr/templates/settings.html` : 15-28 (bug lines 15+20, the new submit-button-less General `<form>` and the first input stripped of `form="settings-form"`) AND/OR 33-81 (every remaining General input stripped of the association attribute) AND/OR 87-93 (bug line 90, the `</form>` closing the button-less General form) AND/OR 131-137 (bug line 134, the instances `<form>` losing `id="settings-form"`) — any hunk satisfies SITE | **Silent data loss on save — General settings fields are no longer submitted**: the General section sits in its own `<form>` with NO submit button while the "Save Settings" button submits only the instances form, so every General field (log_level, counts, skip_unreleased, …) is ABSENT from the POST and silently reset to its form-default on each save. The finding must name the broken form association / fields-not-submitted / values-lost-on-save consequence. NOT "HTML restructuring", NOT "duplicate form action", NOT a styling or accessibility nit — right-site-wrong-axis = detected-below-threshold = a MISS. | warning (correctness/data-loss — silently losing saved settings is an action-bar defect, not a display nit) | 542d5ddb685c992f94cc18e9c780a176067ddaa7 |

## Should-quiet rows (4 new diffs × N=3 runs)

Each is a shipped, organic, pure-M FEATURE commit whose selected lines no later commit
rewrote (line-level, subject-agnostic evidence in the `.provenance` sidecars). Per A16,
each is named safe ON a specific axis — not "globally safe". Per D-08, only a
critical/warning finding on these diffs is an FP; medium/low = noise-notes.

| diff-id | SITE (file : feature-hunk lines) | Safe ON axis (A16) | FP rule | base_sha |
|---|---|---|---|---|
| should-quiet-4 | `triggarr/models/config.py` : 88-115 | SSRF / input-validation: the diff ADDS `validate_url_ssrf`, TIGHTENING the guard (blocks cloud-metadata IPs/hosts + link-local/unspecified/multicast literals); loopback + localhost deliberately permitted and documented (same-host *arr); defined AFTER `reject_apikey_in_url` so the pydantic-v2 definition-order guarantee keeps the apikey= rejection firing first — no leak, no injection, no resource issue | any critical/warning = FP | 14eecb580499ec2ab4e8d469c768479509a9695a |
| should-quiet-5 | `src/python/model/model.py` : 3-9, 78-84, 94-100, 109-115 | log-sanitization / secret-handling: imports `sanitize_log_value` and wraps the file-name interpolation in the add_file/remove_file/update_file debug logs — strictly REDUCES what reaches the logs; dict keys, lookups, deletions, and listener notifications stay raw by design; no behavior change outside log formatting | any critical/warning = FP | 70354771a331f7def6c8116556f58d865f644cd9 |
| should-quiet-6 | `triggarr/models/config.py` : 132-142 | input-validation / config bounds: new `shutdown_drain_timeout` declared `Field(default=60.0, ge=1.0, allow_inf_nan=False)` — rejects zero/negative AND inf/nan (ge=1.0 alone accepts +inf in pydantic v2), bounds-guarded tighter than the surrounding fields; the absent model-level upper bound is a documented deliberate decision (the form clamp is the UI ceiling, the env override is the shutdown-time escape hatch) | any critical/warning = FP | 9bfd4a63dcac983a544a651d53d76612d08a4933 |
| should-quiet-7 | `triggarr/web/routes.py` : 60-66, 443-449, 547-553 | settings input-parse path: the POSTed value flows ONLY through the bounded `safe_float(form.get("shutdown_drain_timeout"), 60.0, 1.0, 3600.0)` (default-clamped, floor 1.0, ceiling 3600.0), mirroring the existing `safe_int` parses beside it; the GET change is a render-context entry — no raw interpolation, no injection surface, no resource issue | any critical/warning = FP | ce567d331b4c10aeeafd24975b75719906f471d6 |

## Owner confirmation (carried v2.9 D-02)

owner_confirmed: true — the owner confirmed ALL SIX picks live on 2026-09-05 (plan 38-03
Task 2 checkpoint, via AskUserQuestion; selected "confirm-all (Recommended)" from the
options [confirm-all / Swap #2 for roonseek a77a2d9 / Drop #6 (land at 11)]).

One-line-each pick summary as confirmed:

- triggarr-session-rotation — triggarr `0866332` "fix(auth): rotate session secret on
  password change to evict other sessions" REVERSED (−27/+2, `routes.py`), base_sha
  `f4366a2...` (the clone HEAD at build; apply-check exit 0)
- triggarr-settings-form-split — triggarr `542d5dd` "fix(walkthrough): General settings
  fields lived in a separate form from the Save button, so saving never submitted them"
  REVERSED (+12/−18, `settings.html`), base_sha `542d5dd...` (= the fix itself — the
  patch fails at current triggarr HEAD; the pinned-base autoescape precedent)
- should-quiet-4 — triggarr `9be610a` "feat(71-02): add validate_url_ssrf
  field_validator to InstanceConfig" (+22, `config.py`), base_sha `14eecb5...` (= 9be610a^)
- should-quiet-5 — seedsyncarr `f64a874` "feat(101-05): add sanitize_log_value import
  and wrap add/remove/update debug logs in model/model.py" (+4/−4, `model.py`), base_sha
  `7035477...` (= f64a874^)
- should-quiet-6 — triggarr `3d042c8` "feat(75-01): add finite-only
  shutdown_drain_timeout GeneralConfig field" (+5, `config.py`), base_sha `9bfd4a6...`
  (= 3d042c8^)
- should-quiet-7 — triggarr `05cfd1b` "feat(75-02): parse and render
  shutdown_drain_timeout in settings handler" (+3/−1, `routes.py`), base_sha
  `ce567d3...` (= 05cfd1b^)

## Kit integrity digests (computed from the COMMITTED 38-03 kit blobs)

Kit commit KC = `ccf887cb66962739d0c094652ed35321d0e8c7a8` (resolved by pathspec log at
key-authoring time; all 12 files below resolve to the same KC). Each digest below is
`git show KC:docs/design/b3-ground-truth/diffs/<file> | shasum -a 256` — computed from
the committed blob, NEVER from a live working file. Because seal-2 digest-binds THIS key
blob, these lines transitively SEAL the new kits' bytes: the part-B checklist generation
(38-04), the scoring ladder (38-05), and the phase exit gate (38-06) all verify kit
bytes against them (the exit gate's A-only status filter alone cannot see a
post-addition rewrite of a NEW kit file — these digests can).

sha256(diffs/triggarr-session-rotation.patch) = 31bad85408ca909aca531e6a55bdbe5033db4a3760074c5dc4a3f68ad7d09b23
sha256(diffs/triggarr-session-rotation.provenance) = ccc51cee5407ef5e2d8c73347089a4be9b4ecc88febb062ce17ef7de20c6575c
sha256(diffs/triggarr-settings-form-split.patch) = 40ae123ce9910d937b8afdf51dcd98de048eec6b86bbdb4be1c0661fbc88cd91
sha256(diffs/triggarr-settings-form-split.provenance) = ad9f3911541ebb9ce10ae2461839b6674d8fc552c33c6145f1d18cc1ea3684fa
sha256(diffs/should-quiet-4.patch) = 81a3b81463c354bcc3e88215c2d2d296f0e6c56bd895ce7fa76af2f89ce3ea69
sha256(diffs/should-quiet-4.provenance) = f3d04ac4a106f8651f7e1e51531f9a0934e0553a32508c8e5c98a758b098edb5
sha256(diffs/should-quiet-5.patch) = b980f980f873cc28982b17901a86382d565261663792e90243edc8db7afc1035
sha256(diffs/should-quiet-5.provenance) = d22bd39a5a9e68326d133819ae9504c85d709a799afb6b47027c944ce9496903
sha256(diffs/should-quiet-6.patch) = b68b2db029f8c09a489e645efff113525ead24dd5cb4d25c596a1d27c7f9df07
sha256(diffs/should-quiet-6.provenance) = b713955e0db8ed529ef8d1b6ca0fb5ceb82d35de41ffdbd1e5d947b2e3d79bc2
sha256(diffs/should-quiet-7.patch) = d747d8d0dacc7752ae5e41b44810265ba9b88245f41d10ea3f478422f5761663
sha256(diffs/should-quiet-7.provenance) = 4a0417456f293be15456f7769b37bc16b4c888683a829a333fc57bc02868218b

## Per-role denominators (FULL grown set — carried 6 + new 6)

- Headline **catch-rate** denominator = total should-catch runs: 5 should-catch diffs
  (3 carried + 2 new) × 3 runs = **15 runs**.
- Headline **FP-rate** denominator = total should-quiet runs: 7 should-quiet diffs
  (3 carried + 4 new) × 3 runs = **21 runs**.
- Full-set total = **36 runs**.

These same three numbers are recorded as the three literal denominator lines appended to
the manifest at seal-2 (the two statements must agree; scoring uses exactly these — no
aggregation over holes, per the sealed denominator rule).

## Scoring output states (by reference)

Per should-catch run: **catch** / **detected-below-threshold** / **miss** /
**unscoreable**; per should-quiet run: **FP** / **noise-note** / **clean** /
**unscoreable** — exactly as defined in the sealed v2.9 blob's "Scoring output states"
section (same D-06 rule: repeat, never guess).
