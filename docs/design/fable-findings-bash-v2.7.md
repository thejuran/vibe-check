# Independent bash/security audit — vibe-check inline shell (tag v2.7)

**Scope:** the security-critical and deterministic BASH embedded in the command/agent prose —
path containment, Codex output normalization, and `--all` chunk math — across
`commands/review.md`, `commands/deep-review.md`, `agents/fix.md`, `agents/codex-adversarial.md`.
The Python engine (`score.py`/`config.py`) is a separate file: `fable-findings-score-py-v2.7.md`.

**Checkout:** tag `v2.7` (HEAD `3501545`).

## Provenance (read this)
This pass was **authored by Opus 4.8, NOT Fable.** Fable 5's content-safety safeguards flagged
the security/bash prompt mid-session and hard-switched the model to Opus (the safeguards are
"intentionally broad right now and may flag safe and routine coding, cybersecurity... work").
So — unlike the score.py pass, which was genuine Fable — this is **not** an independent
cross-model data point; it's Opus reviewing vibe-check (same model family as the tool's own
dogfood). The findings are real regardless of author, but they carry no "a different model
caught what ours couldn't" weight. Recorded honestly per the review remit.

## Independent verification (Opus, 2026-07-01)
Every finding below was re-checked against the real bash extracted at tag `v2.7`
(`git show v2.7:…`), reading the cited lines and surrounding logic. **5 of 5 confirmed real,
0 overstated** — a cleaner hit rate than the score.py pass (which had one overstated finding).
Two are drift-between-copies findings (F2, F3): the containment logic genuinely diverges across
the ≥5 hand-copied sites — direct evidence for extracting the path-validation family into one
tested `guard.py` (see `prose-to-code-inventory.md` Family 1).

| # | Finding | Verdict | Severity |
|---|---------|---------|----------|
| B1 | state-key raw branch name breaks the "flat filename" disjointness proof | ✅ CONFIRMED | HIGH-correctness / Med-security |
| B2 | empty `$ROOT` → containment fails OPEN; bash copies diverge from the Python copy | ✅ CONFIRMED | Medium |
| B3 | deleted file (in diff set) → empty realpath → legit Codex finding downgraded | ✅ CONFIRMED | Medium |
| B4 | `grep -Eq` allowlist is line-anchored → multi-line `$NARROW` passes on a clean first line | ✅ CONFIRMED | Low |
| B5 | summary→agent_notes single-line reduction is ASCII-only vs the Unicode-aware title rule | ✅ CONFIRMED | Low |
| — | Family 2 chunk-packer (sort key, silent-drop, byte-bound one-liner) | ✅ clean — no defects | — |

---

## B1 — State-key embeds an unescaped branch name → the "structurally disjoint" reserved-path proof is false  [HIGH-correctness / Med-security]

`review.md:385` (bash) · `review.md:389` (the falsified claim)

**Confirmed.** The non-`--all` state path interpolates `$(git branch --show-current)` raw:
```
STATE_FILE=".turingmind/state/$(git rev-parse --show-toplevel | xargs basename)-$(git branch --show-current).json"
```
Git branch names legally contain `/` (`feat/…`, `fix/…`, `release/…`), so the resolved path
gains an embedded `/` — it is NOT "a FLAT filename directly under `.turingmind/state/`" as
`review.md:389` asserts. Two consequences:

1. **The reserved-path disjointness proof (Phase 0.5 (i), :389) is false.** It claims a
   subdirectory `by-mode/all/` "can NEVER equal a flat filename." Counter-example: repo named
   `by`, branch `mode/all/1234567890ab` (verified legal via `git check-ref-format`) → the flat
   key becomes `.turingmind/state/by-mode/all/1234567890ab.json` — byte-identical to the
   reserved `--all` key grammar. A plain `/review` then reads/writes inside the `by-mode/`
   subtree the next paragraph declares off-limits. The "structural property of the path grammar"
   the guard rests on does not hold once branch names carry slashes.
2. **Live divergence + carry-forward restart.** The on-disk state file uses a dash
   (`…feat-framework-skill-reviewer.json`) but the documented bash produces a slash
   (`…feat/framework-skill-reviewer.json`) — and **no prose documents any slash-sanitization**
   (grep confirms). A model transcribing the block literally resolves the slashed path;
   `[ -f "$STATE_FILE" ]` then misses the dash-named file → carry-forward silently restarts
   from pass 1 (the exact failure the GSD-mode abbreviation warning at :382 guards against,
   reintroduced here). `mkdir -p .turingmind/state` (Phase 0.7) does not create the `…feat/`
   subdir either, so a literal write ENOENTs.

**Live trigger:** any slashed branch. The current dev branch `feat/framework-skill-reviewer`
triggers it in this very repo. The inventory's second-tier row "state-file path resolution —
'comment must match code' invariant is a drift smell" names exactly this block; it is a latent
bug, not merely an extraction candidate.

## B2 — Empty `$ROOT` makes the trailing-slash containment check fail OPEN; bash copies diverge from the empty-ROOT-safe Python copy  [Medium]

`fix.md:28`, `deep-review.md:~322`, `codex-adversarial.md:106`, `review.md:134` (bash) vs
`review.md:185-193` (Python)

**Confirmed.** The shared bash containment shape is `case "$REAL/" in "$ROOT/"*) CONTAINED=1`.
If `$ROOT` (or `$PLANNING_ROOT`) is empty, the pattern `"$ROOT/"*` becomes `/*`, which matches
any absolute `$REAL` (`/etc/passwd`, `/tmp/anything`) → `CONTAINED=1`. The check the doc
repeatedly calls "what actually stops traversal" silently passes an out-of-repo path.

**Divergence (live copy-disagreement):** the mode-5 narrow copy at `review.md:185-193` uses
Python `os.path.realpath` rooted at `ROOT`; on empty `ROOT`, `os.path.realpath("")` returns the
cwd (a real absolute dir), so containment degrades to "must be under cwd" — it never accepts an
arbitrary absolute path. The four `case` bash copies have no such floor. **Five hand-copied
sites, and they do not agree on the empty-`ROOT` input: one fails safe, four fail open.** Because
`fix.md`'s copy guards the path that reaches `git add`/`git commit`, this is the top-severity
failure class (containment miss on the auto-committing path); Medium rather than Critical only
because `$ROOT` is normally non-empty inside a git repo — but the doc presents the guard as
airtight, and it isn't.

## B3 — Codex path-check assumes diff-set membership ⇒ file exists on disk; a valid finding about a DELETED file is silently downgraded  [Medium]

`deep-review.md:325-327` (and the same assumption in `fix.md:28`) vs `review.md:185-193`

**Confirmed.** The comment justifies skipping missing-path tolerance: *"(a) requires CODEX_FILE
∈ the reviewed diff set, so it names a real tracked file → resolve the existing path."* Then:
```
REAL=$(cd "$ROOT" && realpath "$CODEX_FILE" 2>/dev/null) || REAL=""   # empty → downgrade
```
A file **deleted** in the reviewed range IS a member of the diff set (deletions appear in
`git diff --name-only`), so it passes membership check (a) — but BSD `realpath` returns empty
for a non-existent path → `REAL=""` → `CONTAINED=0` → the finding is downgraded/withheld even
though it is a legitimate, in-scope Codex finding about removed code.

**Divergence:** `review.md`'s mode-5 stage deliberately uses missing-path-tolerant Python
`os.path.realpath` *precisely because* "BSD realpath exits non-zero and prints nothing for a
non-existent path." The deep-review Codex copy and the fix.md copy do not adopt that tolerance.
Two copies of "resolve then contain" disagree on non-existent-but-legal paths: review.md
tolerates them, deep-review.md/fix.md reject them. (For fix.md the effect is milder — a fix
targeting a deleted file is usually genuinely obsolete — but the recorded reason would be a
spurious containment failure, not obsolescence.)

## B4 — `grep -Eq '^…$'` allowlist is line-anchored → a multi-line `$NARROW` passes if only its first line is clean  [Low]

`review.md:174` (stage ii) + `review.md:163-168` (stage i)

**Confirmed.** `printf '%s' "$NARROW" | grep -Eq '^[A-Za-z0-9._*/-]+$'` matches when ANY line
satisfies the anchored pattern. For `$NARROW = $'docs\n/etc/cron.d'`, line 1 (`docs`) passes, so
the whole value passes. The stage-(i) `case` `/*` arm anchors to the whole value's start, so a
leading `/` on line 2 is not caught either (traversal specifically is still covered — the `*..*`
arm matches across the newline — but the absolute-path reject is bypassed). Only stage-(iii)'s
literal-prefix realpath then stands between this and selection, operating on the mangled
multi-line prefix. Low likelihood (a slash-command token rarely contains a raw newline) but the
allowlist is presented as exhaustive and the line-anchoring defeats that. **review.md-only:** the
deep-review.md Codex path checks use `case` (whole-string), not `grep`, so they don't share the
hole — a small copy-shape difference that happens to matter.

## B5 — summary→agent_notes single-line reduction is ASCII-newline-only, while the title reduction is Unicode-line-aware  [Low]

`codex-adversarial.md:32` (summary rule) vs `codex-adversarial.md:116` (title rule)

**Confirmed — internal inconsistency, not copy drift.** The title single-line step explicitly
splits on `\n`, `\r`, U+2028, U+2029, with its own rationale: *"Checking only ASCII \n/\r would
let a U+2028-delimited second line survive."* The summary→agent_notes reduction says only
"truncate at the first newline" — ASCII only. So a Codex `summary` containing U+2028 as a line
separator survives the "single-line" reduction; in a renderer that treats U+2028 as a break, the
agent_note displays as multiple lines — the exact report-spoofing surface the cap is meant to
defend against. Both files state the summary rule identically (no copy drift); the rule is simply
weaker than its own sibling against the doc's stated threat model. Low because `agent_notes` is
contractually display-only. (The Family-3 title character lists — bidi U+202A–U+202E/U+2066–U+2069,
zero-width U+200B–U+200D/U+FEFF, U+2028/U+2029, backticks, control chars — DO match exactly
between `codex-adversarial.md:117` and `deep-review.md:306/313`; that duplication is in sync.)

---

## What checked out clean (Family 2 — chunk math)

- **Sort key** (`review.md:267`): `sort -t$'\t' -k1,1n -k2,2nr` is tier-ASC-primary,
  churn-DESC-secondary — matches the CHUNK-01 requirement exactly (a tier-0 auth file sorts above
  a high-churn tier-3 README). Not transcribed wrong.
- **Silent-drop / partial-note:** the greedy walk seeds from every unplaced file; edge-case A
  (`review.md:289`) routes a single file over either bound into its own chunk; the reviewed-partial
  note fires on line OR byte overflow of the dispatched per-chunk totals — so a giant one-line file
  (≈1 line, huge bytes) is caught by the byte arm and cannot be reported "fully reviewed" without a
  note. No traced input drops a file from all chunks or suppresses the partial note.

---

## Bottom line

The Python scoring math is solid; the **bash trust boundaries are where the defects cluster** —
and B2/B3 prove the hand-copied containment logic has already drifted out of sync across files.
The single highest-leverage fix is extracting the path-validation family (containment + regex
allowlist + `..`/pathspec-magic reject + missing-path tolerance) into one tested `guard.py`
(`prose-to-code-inventory.md` Family 1): every one of B1–B3 exists *because* the logic is
transcribed/copied rather than executed from one tested source.
