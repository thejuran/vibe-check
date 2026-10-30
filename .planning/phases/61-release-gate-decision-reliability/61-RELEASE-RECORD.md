# Phase 61 release record — vibe-check 2.14.0

This record proves the 2.14.0 release candidate against the scope Phases 59 and 60 delivered (decision continuity, exact-change ranges, reliable Close out). It adds no feature. Every gate below was re-run on the exact commit that will ship; results from earlier sessions are not carried forward.

**Code under consideration:** candidate `0d2be77` (0d2be7790577ea6d89e7eb563008e9ba8c5d7c6d), plugin.json 2.14.0; gates ran on a checkout whose tree equals C outside .planning (D-12).

Precondition (checked before any gate, 2026-10-30): `git diff --quiet 0d2be77 HEAD -- . ':(exclude).planning'` exit 0 and `git status --porcelain -- plugins README.md` empty. Working HEAD was `9b8b909` (commits after C touch only `.planning/`), which is why the replay reports below print `head: 9b8b909…`.

## Gate results

| # | Gate | Requirement | Command | Result | Verdict |
|---|------|-------------|---------|--------|---------|
| G1 | Full offline suite | GATE-01 | `pytest -q -p no:cacheprovider` | `3821 passed, 5039 subtests passed in 177.81s (0:02:57)` — equals README count in C ("3,821 passing at release") | PASS |
| G2 | Targeted real-chain regressions | GATE-01 | 61-RESEARCH G2 selector (10 node ids) | `193 passed, 200 subtests passed in 13.20s` | PASS |
| G3 | Mode/recovery integration | GATE-01, D-11 | 61-RESEARCH G3 selector (13 node ids) | `520 passed, 1062 subtests passed in 7.73s` | PASS |
| G4 | Replay tests | GATE-02 | `pytest -q -p no:cacheprovider test_replay.py` | `64 passed, 10 subtests passed in 10.06s` | PASS |
| G5a | Replay complete-output diff vs released 2.13 scorer | GATE-02 | `python3 replay.py diff --base rev:v2.13 --scorer path:$PWD/score.py --out <scratch>` (no `--allow`) | exit 0; `runs compared: 170`, `runs differing: 0`, `runs with unallowed differences: 0`; `## Differences — none` | PASS |
| G5b | Replay catch guardrail | GATE-02 | `python3 replay.py candidate --name gate61 --scorer path:$PWD/score.py --out <scratch>` | exit 0; `kept 25 / protected 26`, `REGRESSED 0`, `UNEVALUABLE 0`, `AMENDED 1` | PASS |
| G5c | Replay manifest integrity | GATE-02 | `python3 replay.py check-manifest` | exit 0, no output | PASS |
| G9 | Frozen replay machinery | GATE-02 | `git diff --stat v2.13 0d2be77 -- plugins/vibe-check/scripts/replay.py plugins/vibe-check/scripts/test_replay.py` | empty output (unchanged since v2.13) | PASS |

## Raw output

```
All runs are from plugins/vibe-check/scripts at candidate 0d2be77.
G1  3821 passed, 5039 subtests passed in 177.81s (0:02:57)
G4  64 passed, 10 subtests passed in 10.06s
G5a - base: rev:v2.13 (sha256 3504d2da79e9ebab26bfedd01c7614c9b7cc06ade99c12b7e24e90003edd22fb)
    - candidate: path:.../plugins/vibe-check/scripts/score.py (sha256 a4a02a246ff696f3301c48145d31c6edf119bd396a7dc8f14013b372f50b71ee)
    - roots: all (7 roots)
    - allowances: none
    - runs compared: 170
    - runs differing: 0
    - runs differing (allowed): 0
    - runs with unallowed differences: 0
    ## Differences
    - none
G5b kept 25 / protected 26
    REGRESSED 0
    UNEVALUABLE 0
    AMENDED 1
```

- 0 failed in every pytest run (G1–G4).
- Replay differences: none (expected-difference list: empty; no --allow used).
- GOLDEN_DIGEST unchanged (TestGolden passes inside G1).
- G5b's one AMENDED run (`runs/triggarr-secret-in-logs/run-2`, amendment 008) is the manifest's standing amendment, not a new difference.
- Full logs stayed in the session scratchpad; nothing was written into the repo (`git status --porcelain -- plugins` empty after the runs).
