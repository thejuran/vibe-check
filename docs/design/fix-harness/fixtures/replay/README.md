# Captured card payloads

Real `AskUserQuestion` inputs, copied verbatim from the transcripts of live
harness sessions. Nothing is stripped: every payload comes from the synthetic
case `py-clamp-01`, so it is safe to track. These files define the card shape
the harness must handle. `tools/test_harness_cards.py` (`TestCapturedCards`)
checks that each one classifies as its file name says and is answered from
the seeded identity alone. When the plugin changes a card, capture the new
payload here, and update `harness_cards` if the test fails.

| File | Card kind | Provenance |
|------|-----------|------------|
| `fix-loop-card.json` | fix-loop (single question, four options) | smoke run P-D (`run --case py-clamp-01 --mode default --kind preservation`), 2026-10-10, plugin snapshot of `plugins/vibe-check` at c2d69af (version string 2.11.1), Claude Code 2.1.294 via claude-agent-sdk 0.2.165, model claude-opus-5-5[1m]. First card of the run (review pass 2, one finding). The harness answered `Apply all & rerun`. |

How the captured shape compares with the hand-written fixtures in
`test_harness_cards.py`: header `Pass N`, the question sentence
`Pass N — <n> finding(s) listed below. How do you want to proceed?`, the row
line `#n file:line — title (band)`, the option labels in
`batch_parse.FIX_LOOP_OPTIONS` order, and `multiSelect: false` all match.
The real options also carry `description` text, which the classifier
ignores.

Replay message files for `fixharness.py replay` are JSON lines, one per
item: `{"card": <AskUserQuestion input>}`, `{"tool": "<name>", "input": {…}}`
or `{"turn_end": "<text>"}`.
