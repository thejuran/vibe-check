# Cost visibility note (BASE-01, backlog 999.12)

Analysis only: nothing was run against a model, no log was copied into the repo, and nothing is priced. Status: RECOMMENDATION, waiting on the owner's go or no-go at the phase's closing step (plan 62-09).

## Verdict

**NO-GO**

The recorded sessions do carry model names and token counts (input, output, cache-creation, cache-read) on every message, and those counts tie cleanly to a review run and, for plain review, to each reviewer lane. What cannot be trusted under the agreed rule is the cross-check: the records hold no run total of their own, so the lane figures can only be added up and compared with themselves; retries are not recorded at all, elapsed time includes the owner's waiting time, and deep review has no recorded 2.14.x session. Next: accounting work stops here (D-13), and this milestone uses the labelled byte and step counts in `docs/design/lean-v2.15/CRITERION.md` as its evidence; nothing is built for usage reporting in v2.15 either way (D-12).

**Why this verdict:** This NO-GO follows from the rule agreed in D-11 (a figure is trusted only if lane totals can be checked against a run total that was not made by adding up the same parts) and from the fact that the records hold no such run total. It is not a finding that the usage numbers look wrong: they are present in every sampled session and tie to runs and lanes. If figures labelled 'estimated' are good enough for your purpose, you can overrule this at the closing step. Of the fifteen deciding cells (five fields per run and per lane for plain review, five fields per run for Finalize), 0 came out `measured`, 15 `estimated` and 0 `missing`.

## What was looked at

The fixed sample, one pass, nothing else opened. These are recorded smoke-test sessions kept in their own throwaway project folders, counted as this project's records under D-19.

| Label | Kind | Version |
|---|---|---|
| smoke61/b1bb3036 | Finalize | 2.14.0 candidate `0d2be77` |
| smoke61/5caa5cec | plain review | 2.14.0 candidate `0d2be77` |
| smoke61/15a3be6d | plain review | 2.14.0 candidate `0d2be77` |
| smoke2141/b0294925 | plain review | 2.14.1 |
| smoke2141/6a70827e | plain review | 2.14.1 |
| (none) | deep review | no recorded 2.14.x session |

All five sample files were found on this machine. Each plain review has four reviewer lanes (`vibe-check:bugs`, `vibe-check:language-python`, `vibe-check:security`, `vibe-check:triage`), each named by its subagent's meta file; no subagent file was left without a lane. Finalize dispatches no reviewer lanes.

Repo archives (counted only, D-10):

| Archive | Transcript files | Files carrying any usage object | Files with a subagents folder beside them |
|---|---|---|---|
| `docs/design/b3-ground-truth` | 102 | 102 | 0 |
| `docs/design/freeze-v2.12` | 3 | 0 | 0 |

The b3 archives are older-version (v2.10/v2.11) main-session copies with no subagent files, so they cannot give per-lane usage for 2.14.x; the freeze-v2.12 harness transcripts carry no usage at all. Both count as present but not attributable, not as evidence. (The b3 transcripts are gitignored, so they were counted in the owner's primary checkout.)

This repo's own session folder was not sampled: research found no `/vibe-check:` review command recorded there (a research-time observation, not re-scanned, per D-13's one pass). Nothing was run and no log was copied; only field names, counts and token sums left the logs.

## Fields

Labels follow the rule fixed before the data was read: `measured` needs all three D-11 tests with test 3 checked against an independent run total; `estimated` means present and attributable but test 3 cannot be checked independently (or the figure includes something that is not the review); `missing` means absent in at least one sampled session of that kind or carried by no field.

| Field | Per run | Per lane | In every session? | Tied to run and lane? | Consistent? | Notes |
|---|---|---|---|---|---|---|
| model (plain review) | estimated | estimated | yes: 75 of 75, 55 of 55, 77 of 77, 51 of 51 messages | yes: run by session file, lane by meta file | cannot be checked: no independent run total | main session `claude-opus-5-5`; bugs, language-python and security `claude-sonnet-5`; triage `claude-haiku-5-5` |
| model (Finalize) | estimated | not applicable | yes: 19 of 19 | yes: run by session file | cannot be checked: no independent run total | `claude-opus-5-5`; no lanes |
| input tokens (plain review) | estimated | estimated | yes: same counts as model | yes | cannot be checked: no independent run total | |
| input tokens (Finalize) | estimated | not applicable | yes: 19 of 19 | yes | cannot be checked: no independent run total | |
| output tokens (plain review) | estimated | estimated | yes: same counts as model | yes | cannot be checked: no independent run total | |
| output tokens (Finalize) | estimated | not applicable | yes: 19 of 19 | yes | cannot be checked: no independent run total | |
| cache-creation tokens (plain review) | estimated | estimated | yes: same counts as model | yes | cannot be checked: no independent run total | the `cache_creation` sub-object's meaning is unverified and was not used |
| cache-creation tokens (Finalize) | estimated | not applicable | yes: 19 of 19 | yes | cannot be checked: no independent run total | |
| cache-read tokens (plain review) | estimated | estimated | yes: same counts as model | yes | cannot be checked: no independent run total | |
| cache-read tokens (Finalize) | estimated | not applicable | yes: 19 of 19 | yes | cannot be checked: no independent run total | |
| retries (plain review and Finalize) | missing | missing | no field holds it | no | no | no key name containing "retry" in any sampled record |
| elapsed time (plain review) | estimated | estimated | yes: first and last timestamps in every file | yes | cannot be checked: no independent duration | run figure includes the owner's waiting time; in two sessions each lane ran twice, so its figure spans both runs and the gap between them |
| elapsed time (Finalize) | estimated | not applicable | yes | yes | cannot be checked | includes the owner's waiting time |
| every field (deep review) | missing | missing | no recorded 2.14.x session | no | no | declared, not observed |

The fifteen deciding cells are the five fields model, input, output, cache-creation and cache-read: per run and per lane for plain review (ten) and per run for Finalize (five). Retries and elapsed time are reported but are outside the verdict rule; Finalize's per-lane cells are `not applicable` and count neither way.

## What is missing

- **Retries.** No retry field was seen: no key name containing "retry" appears in any record of the five sessions or their subagent files.
- **An independent run total.** The reader's `run_total_source` showed `none found` for all five sessions. The run figure exists only as the sum of the main session and its lanes, so lane totals cannot be checked against anything independent (D-11 test 3).
- **Deep review.** No recorded 2.14.x deep-review session exists; every field for that kind is `missing`.
- **Elapsed time as a performance figure.** The only figure available is first-to-last timestamp, which includes the owner's waiting time. Lane figures span the lane's own records but, where a lane ran twice in one review, also the gap between its two runs.
- **Older archives.** The b3 and freeze-v2.12 archives cannot stand in: the first has no lane files and is an older version, the second has no usage at all.

## Smallest useful report

One row per recorded review run (session label, kind, plugin version) and, for plain review, one row per reviewer lane beneath it, with columns: model (`estimated`), input tokens, output tokens, cache-creation tokens and cache-read tokens (each `estimated`, summed once per message id), and elapsed time (`estimated`, marked as including the owner's waiting time). Retries are left out as `missing` rather than shown as zero, and the run row is marked "sum of parts". The single missing piece that would turn this into a GO is a run-level usage total recorded by Claude Code itself (for example token totals on each lane's dispatch result), so lane sums could be checked against a figure that was not made by adding them up.

## Numbers

Token counts from the reader, deduplicated by message id. These are token counts from subscription sessions, not a bill; nothing is priced.

| Session | Kind | Scope | Messages | Input tokens | Output tokens | Cache-creation tokens | Cache-read tokens | Models |
|---|---|---|---|---|---|---|---|---|
| smoke61/b1bb3036 | finalize | main session | 19 | 38 | 9,574 | 105,309 | 1,997,183 | claude-opus-5-5 |
| smoke61/b1bb3036 | finalize | run (sum of parts) | 19 | 38 | 9,574 | 105,309 | 1,997,183 | claude-opus-5-5 |
| smoke61/5caa5cec | plain | main session | 56 | 128 | 33,242 | 224,401 | 8,621,976 | claude-opus-5-5 |
| smoke61/5caa5cec | plain | lane vibe-check:bugs | 4 | 8 | 10,526 | 96,212 | 135,247 | claude-sonnet-5 |
| smoke61/5caa5cec | plain | lane vibe-check:language-python | 5 | 10 | 8,240 | 53,300 | 227,781 | claude-sonnet-5 |
| smoke61/5caa5cec | plain | lane vibe-check:security | 6 | 12 | 5,694 | 75,351 | 278,833 | claude-sonnet-5 |
| smoke61/5caa5cec | plain | lane vibe-check:triage | 4 | 8 | 1,221 | 65,414 | 129,441 | claude-haiku-5-5 |
| smoke61/5caa5cec | plain | run (sum of parts) | 75 | 166 | 58,923 | 514,678 | 9,393,278 | claude-haiku-5-5, claude-opus-5-5, claude-sonnet-5 |
| smoke61/15a3be6d | plain | main session | 45 | 98 | 28,571 | 182,895 | 6,600,231 | claude-opus-5-5 |
| smoke61/15a3be6d | plain | lane vibe-check:bugs | 2 | 4 | 6,264 | 65,087 | 52,307 | claude-sonnet-5 |
| smoke61/15a3be6d | plain | lane vibe-check:language-python | 3 | 6 | 4,792 | 39,221 | 131,569 | claude-sonnet-5 |
| smoke61/15a3be6d | plain | lane vibe-check:security | 3 | 6 | 1,762 | 39,948 | 136,341 | claude-sonnet-5 |
| smoke61/15a3be6d | plain | lane vibe-check:triage | 2 | 4 | 811 | 54,377 | 43,144 | claude-haiku-5-5 |
| smoke61/15a3be6d | plain | run (sum of parts) | 55 | 118 | 42,200 | 381,528 | 6,963,592 | claude-haiku-5-5, claude-opus-5-5, claude-sonnet-5 |
| smoke2141/b0294925 | plain | main session | 57 | 130 | 34,356 | 228,229 | 8,666,668 | claude-opus-5-5 |
| smoke2141/b0294925 | plain | lane vibe-check:bugs | 6 | 12 | 6,307 | 101,375 | 262,420 | claude-sonnet-5 |
| smoke2141/b0294925 | plain | lane vibe-check:language-python | 5 | 10 | 8,980 | 55,843 | 224,155 | claude-sonnet-5 |
| smoke2141/b0294925 | plain | lane vibe-check:security | 5 | 10 | 5,694 | 73,253 | 216,154 | claude-sonnet-5 |
| smoke2141/b0294925 | plain | lane vibe-check:triage | 4 | 8 | 1,414 | 65,346 | 129,444 | claude-haiku-5-5 |
| smoke2141/b0294925 | plain | run (sum of parts) | 77 | 170 | 56,751 | 524,046 | 9,498,841 | claude-haiku-5-5, claude-opus-5-5, claude-sonnet-5 |
| smoke2141/6a70827e | plain | main session | 41 | 90 | 21,795 | 172,837 | 5,794,472 | claude-opus-5-5 |
| smoke2141/6a70827e | plain | lane vibe-check:bugs | 2 | 4 | 6,407 | 66,770 | 52,144 | claude-sonnet-5 |
| smoke2141/6a70827e | plain | lane vibe-check:language-python | 4 | 8 | 3,296 | 38,200 | 190,727 | claude-sonnet-5 |
| smoke2141/6a70827e | plain | lane vibe-check:security | 2 | 4 | 2,946 | 38,568 | 74,581 | claude-sonnet-5 |
| smoke2141/6a70827e | plain | lane vibe-check:triage | 2 | 4 | 1,044 | 54,334 | 43,150 | claude-haiku-5-5 |
| smoke2141/6a70827e | plain | run (sum of parts) | 51 | 110 | 35,488 | 370,709 | 6,155,074 | claude-haiku-5-5, claude-opus-5-5, claude-sonnet-5 |

Elapsed time per run, first to last record, including the owner's waiting time: smoke61/b1bb3036 110 s, smoke61/5caa5cec 525 s, smoke61/15a3be6d 359 s, smoke2141/b0294925 549 s, smoke2141/6a70827e 275 s (rounded from the reader's figures).

## How this was produced

- **Reader:** `docs/design/lean-v2.15/tools/usage_fields.py` (stdlib only, read-only, tests in `test_usage_fields.py` beside it).
- **Command shape:** `python3 -I docs/design/lean-v2.15/tools/usage_fields.py --session smoke61/b1bb3036=finalize=<session file> --session smoke61/5caa5cec=plain=<session file> --session smoke61/15a3be6d=plain=<session file> --session smoke2141/b0294925=plain=<session file> --session smoke2141/6a70827e=plain=<session file> --json`, output kept in the session scratchpad, and once more with `--archive-root <checkout>/docs/design/b3-ground-truth --archive-root <checkout>/docs/design/freeze-v2.12 --json` for the archive counts.
- **Dedupe rule:** usage is counted once per message id (`message.id`, falling back to `requestId`), because Claude Code logs one record per content block of each message. Across the five runs, 264 duplicate records were dropped, 0 message ids had duplicates that disagreed, 0 lines were malformed and 0 message ids appeared in more than one file.
- **Lanes:** taken only from each subagent file's meta file `agentType`; 0 subagent files were unattributed.
- **No price:** the reader refuses to print output holding a dollar sign or a cost, price or usd key or table heading; this note was checked with the reader's `check-note` mode before commit.
- **Date:** 2026-11-14.
