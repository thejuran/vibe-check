# Live check — two same-day close-outs keep both reports and both state archives

Requirement: R2 (no-clobber Finalize archive routing, 54-02), live check per D-27 / D-07. Run by the 54-10 re-run on candidate `24c0c00038f2d15af4b55f178ea44e680c1f2c58` (from `evidence/CANDIDATE.json`).

This replaces the record for the superseded candidate `302df48e1097…`, which is kept unchanged in `evidence/superseded-302df48e1097/live-finalize-archive.md`. The candidate's `90-finalize.md`, `review_archive.py` and `finalize_gate.py` are unchanged from 302df48 (`git diff 302df48 24c0c00 -- plugins/` is empty). Every archive name and every sha256 below matches the superseded run.

## Result

PASS. Nothing was overwritten.

| pass | REVIEW.md archive | state archive |
|---|---|---|
| close-out 1 | `.turingmind/REVIEW-54-2026-10-15.md` (sha256 9e0b5ebb…, unchanged after close-out 2) | `.turingmind/state/format-53/54.json.archived-2026-10-15` (sha256 e82f5bf2…, unchanged after close-out 2) |
| close-out 2 (same day) | `.turingmind/REVIEW-54-2026-10-15-2.md` (sha256 b15d26ce… = the REVIEW.md close-out 1 wrote) | `.turingmind/state/format-53/54.json.archived-2026-10-15-2` (sha256 9f9e3684…) |
| unstamped pass 1 | `.turingmind/REVIEW-unstamped-2026-10-15.md` (sha256 4656382a…, unchanged after pass 2) | — |
| unstamped pass 2 (same day) | `.turingmind/REVIEW-unstamped-2026-10-15-2.md` (sha256 e62b06e4…) | — |

Both close-out REVIEW.md reports survive: the earlier same-phase report is in `REVIEW-54-2026-10-15.md`, close-out 1's report is in `REVIEW-54-2026-10-15-2.md` (byte-identical to the REVIEW.md close-out 1 left behind), and close-out 2's report is the live `REVIEW.md`. Both state archives survive with their own bytes.

## Method

- Scratch git repos under the session scratchpad (`54-10r/arch-stamped`, `54-10r/arch-unstamped`). Not a real project and not the holdout.
- `VC_ROOT` is a `git archive 24c0c00038f2…  plugins/vibe-check` export of the candidate, not the working tree.
- The fences were extracted from the candidate's `90-finalize.md` (blob 91d02b45ee60024c1d384bb6e2db6b758e80edfb):
  - prior-REVIEW.md fence (the four-backtick bash block): `awk '/^````bash$/{f=1;next} /^````$/{f=0} f' "$FIN"`
  - state-archive command (the `write` branch's "Archive state" code span): `sed -n 's/.*Archive state: `\(python3 "\$VC_ROOT\/scripts\/review_archive.py" state --state-file "\$STATE_FILE"\)`.*/\1/p' "$FIN"`
- Each was run with `bash -s`, with `VC_ROOT` set and, for the state fence, `STATE_FILE=.turingmind/state/format-53/54.json` (the GSD-mode format-53 path Phase 0.5 binds for `PHASE_ID=54`).
- One close-out = the steady-state `write` branch order: prior-REVIEW.md fence, then write a stamped REVIEW.md (`**Final verdict:** ✅ APPROVED` followed by `**State format:** 53`), then the state-archive fence. Before close-out 1 a stamped Phase 54 REVIEW.md from an earlier close-out exists. Between the close-outs the state file is recreated (the same fixture plus one trailing newline, so the two state archives have distinct bytes).
- State JSON: copied from the fixture `scripts/fixtures/phase45-loop-state.json` in the candidate export (the first run copied it from the working tree; same bytes) (sha256 e82f5bf2…). The fix-harness fixtures hold no state JSON; their state is produced at run time by `harness_seed.seed_state`. Only the archive move is under test here, so the state's content does not matter.
- Unstamped variant: a REVIEW.md without the `**State format:** 53` line (`review-closed` exit 1), run through the prior-REVIEW.md fence twice on the same day.

## Script

```bash
#!/bin/bash
set -euo pipefail
REPO=/Users/julianamacbook/turingmind-code-review
SP=/private/tmp/claude-501/-Users-julianamacbook-turingmind-code-review/4224a579-78b3-4810-a82f-789b2e360499/scratchpad/54-10r
C=$(python3 -c "import json;print(json.load(open('$REPO/docs/design/freeze-v2.12/evidence/CANDIDATE.json'))['candidate_sha'])")
rm -rf "$SP/cand" "$SP/arch-stamped" "$SP/arch-unstamped"
mkdir -p "$SP/cand"
# Candidate plugin root exported from the candidate commit (not the working tree)
git -C "$REPO" archive "$C" plugins/vibe-check | tar -x -C "$SP/cand"
VC_ROOT="$SP/cand/plugins/vibe-check"
FIN="$VC_ROOT/phases/shared/90-finalize.md"
echo "candidate=$C"
echo "VC_ROOT=$VC_ROOT"
echo "90-finalize.md blob at candidate: $(git -C "$REPO" rev-parse "$C:plugins/vibe-check/phases/shared/90-finalize.md")"
echo "exported 90-finalize.md sha256: $(shasum -a 256 "$FIN" | cut -d' ' -f1)"
# Fence A: the prior-REVIEW.md archive fence (four-backtick bash block)
awk '/^````bash$/{f=1;next} /^````$/{f=0} f' "$FIN" > "$SP/fence-review.sh"
# Fence B: the state-archive command from the `write` branch
sed -n 's/.*Archive state: `\(python3 "\$VC_ROOT\/scripts\/review_archive.py" state --state-file "\$STATE_FILE"\)`.*/\1/p' "$FIN" > "$SP/fence-state.sh"
echo "--- extracted fence-review.sh ---"; cat "$SP/fence-review.sh"
echo "--- extracted fence-state.sh ---"; cat "$SP/fence-state.sh"
test -s "$SP/fence-review.sh"; test "$(wc -l < "$SP/fence-state.sh")" -eq 1

STATE_SRC="$VC_ROOT/scripts/fixtures/phase45-loop-state.json"
PHASE_ID=54
DATE=$(date +%Y-%m-%d)
echo "date=$DATE  PHASE_ID=$PHASE_ID  state fixture=$(basename "$STATE_SRC")"

review_md() { # $1 = close-out label; $2 = stamped|unstamped
  printf '# Code Review — Phase %s\n\n**Final verdict:** ✅ APPROVED\n' "$PHASE_ID"
  [ "$2" = stamped ] && printf '**State format:** 53\n'
  printf '\nClose-out marker: %s\n' "$1"
}

closeout() { # one Finalize `write` close-out in steady state
  local label=$1
  echo ">>> close-out $label: prior-REVIEW.md fence"
  ( cd "$W" && VC_ROOT="$VC_ROOT" bash -s < "$SP/fence-review.sh" )
  echo ">>> close-out $label: write stamped REVIEW.md (template write)"
  review_md "$label" stamped > "$W/.turingmind/REVIEW.md"
  echo ">>> close-out $label: state archive fence"
  ( cd "$W" && VC_ROOT="$VC_ROOT" STATE_FILE=".turingmind/state/format-53/$PHASE_ID.json" bash -s <<<"$(cat "$SP/fence-state.sh")" )
}

listing() {
  echo "\$ ls -la .turingmind .turingmind/state/format-53"
  ( cd "$W" && ls -la .turingmind .turingmind/state/format-53 | sed 's/^\([^ ]*\) *[0-9]* *[^ ]* *[^ ]* */\1 /' )
  echo "\$ sha256"
  ( cd "$W" && shasum -a 256 .turingmind/REVIEW*.md .turingmind/state/format-53/* )
}

echo; echo "===== STAMPED: two same-day close-outs ====="
W="$SP/arch-stamped"; mkdir -p "$W/.turingmind/state/format-53"; git -C "$W" init -q
python3 -c "import finalize_gate" 2>/dev/null || true
# a stamped REVIEW.md from an earlier same-phase close-out (Phase 54) exists before the first close-out
printf '# Code Review — Phase 54\n\n**Final verdict:** ✅ APPROVED\n**State format:** 53\n\nClose-out marker: 0 (earlier same-phase close-out)\n' > "$W/.turingmind/REVIEW.md"
cp "$STATE_SRC" "$W/.turingmind/state/format-53/$PHASE_ID.json"
echo "seed review-closed exit: $(cd "$W" && python3 "$VC_ROOT/scripts/finalize_gate.py" review-closed < .turingmind/REVIEW.md >/dev/null; echo $?)"
closeout 1
echo "--- after close-out 1 ---"; listing
# recreate state for the second close-out (same day)
cp "$STATE_SRC" "$W/.turingmind/state/format-53/$PHASE_ID.json"
printf '\n' >> "$W/.turingmind/state/format-53/$PHASE_ID.json"   # distinct bytes for the second state
closeout 2
echo "--- after close-out 2 ---"; listing

echo; echo "===== UNSTAMPED: two same-day passes with an unstamped REVIEW.md ====="
W="$SP/arch-unstamped"; mkdir -p "$W/.turingmind"; git -C "$W" init -q
for n in 1 2; do
  review_md "unstamped-$n" unstamped > "$W/.turingmind/REVIEW.md"
  echo "unstamped-$n review-closed exit: $(cd "$W" && python3 "$VC_ROOT/scripts/finalize_gate.py" review-closed < .turingmind/REVIEW.md >/dev/null; echo $?)"
  echo ">>> pass $n: prior-REVIEW.md fence"
  ( cd "$W" && VC_ROOT="$VC_ROOT" bash -s < "$SP/fence-review.sh" )
  echo "--- after pass $n ---"
  ( cd "$W" && ls -la .turingmind | sed 's/^\([^ ]*\) *[0-9]* *[^ ]* *[^ ]* */\1 /' && shasum -a 256 .turingmind/REVIEW*.md )
done
```

## Transcript

```
candidate=24c0c00038f2d15af4b55f178ea44e680c1f2c58
VC_ROOT=/private/tmp/claude-501/-Users-julianamacbook-turingmind-code-review/4224a579-78b3-4810-a82f-789b2e360499/scratchpad/54-10r/cand/plugins/vibe-check
90-finalize.md blob at candidate: 91d02b45ee60024c1d384bb6e2db6b758e80edfb
exported 90-finalize.md sha256: 7fe94ac5af7c7ad7d8f7d6f6ff343de2be04d6c4f135788cfd2458d0b32f660f
--- extracted fence-review.sh ---
if [ -f .turingmind/REVIEW.md ] && ! python3 "$VC_ROOT/scripts/finalize_gate.py" review-closed < .turingmind/REVIEW.md > /dev/null; then
  python3 "$VC_ROOT/scripts/review_archive.py" unstamped --dir .turingmind
  echo "An earlier REVIEW.md was written by a plugin version that does not read this review's state; archived aside as REVIEW-unstamped-<date>.md — it did not close this review."
fi
if [ -f .turingmind/REVIEW.md ]; then
  PRIOR_PHASE=$(grep -oE 'Phase [^ ]+' .turingmind/REVIEW.md | head -1 | cut -d' ' -f2)
  # Defense in depth: REVIEW.md is parsed input — don't trust it. Same allowlist as Phase 0.
  if [[ ! "$PRIOR_PHASE" =~ ^[A-Za-z0-9._-]+$ ]]; then
    PRIOR_PHASE="unknown"
  fi
  if [ -n "$PRIOR_PHASE" ]; then
    python3 "$VC_ROOT/scripts/review_archive.py" review-md --phase "$PRIOR_PHASE" --dir .turingmind
  fi
fi
--- extracted fence-state.sh ---
python3 "$VC_ROOT/scripts/review_archive.py" state --state-file "$STATE_FILE"
date=2026-10-15  PHASE_ID=54  state fixture=phase45-loop-state.json

===== STAMPED: two same-day close-outs =====
seed review-closed exit: 0
>>> close-out 1: prior-REVIEW.md fence
.turingmind/REVIEW-54-2026-10-15.md
>>> close-out 1: write stamped REVIEW.md (template write)
>>> close-out 1: state archive fence
.turingmind/state/format-53/54.json.archived-2026-10-15
--- after close-out 1 ---
$ ls -la .turingmind .turingmind/state/format-53
.turingmind: 
total 
drwxr-xr-x@ 160 Oct 15 18:32 .
drwxr-xr-x@ 128 Oct 15 18:32 ..
-rw-r--r--@ 133 Oct 15 18:32 REVIEW-54-2026-10-15.md
-rw-r--r--@ 102 Oct 15 18:32 REVIEW.md
drwxr-xr-x@ 96 Oct 15 18:32 state
 
.turingmind/state/format-53: 
total 
drwxr-xr-x@ 96 Oct 15 18:32 .
drwxr-xr-x@ 96 Oct 15 18:32 ..
-rw-r--r--@ 98066 Oct 15 18:32 54.json.archived-2026-10-15
$ sha256
9e0b5ebbbf5b4fddf65061df37ef78775edeb087758d3c9f1be11eec393c873b  .turingmind/REVIEW-54-2026-10-15.md
b15d26ce59ac00b2755d5a850a6a371b2bc38ca34b665002877a2dc703a8bd26  .turingmind/REVIEW.md
e82f5bf2fa25322cc04873062d3ee0df1c16994c6cc9b9915512ea6ab63bcd30  .turingmind/state/format-53/54.json.archived-2026-10-15
>>> close-out 2: prior-REVIEW.md fence
.turingmind/REVIEW-54-2026-10-15-2.md
>>> close-out 2: write stamped REVIEW.md (template write)
>>> close-out 2: state archive fence
.turingmind/state/format-53/54.json.archived-2026-10-15-2
--- after close-out 2 ---
$ ls -la .turingmind .turingmind/state/format-53
.turingmind: 
total 
drwxr-xr-x@ 192 Oct 15 18:32 .
drwxr-xr-x@ 128 Oct 15 18:32 ..
-rw-r--r--@ 102 Oct 15 18:32 REVIEW-54-2026-10-15-2.md
-rw-r--r--@ 133 Oct 15 18:32 REVIEW-54-2026-10-15.md
-rw-r--r--@ 102 Oct 15 18:32 REVIEW.md
drwxr-xr-x@ 96 Oct 15 18:32 state
 
.turingmind/state/format-53: 
total 
drwxr-xr-x@ 128 Oct 15 18:32 .
drwxr-xr-x@ 96 Oct 15 18:32 ..
-rw-r--r--@ 98066 Oct 15 18:32 54.json.archived-2026-10-15
-rw-r--r--@ 98067 Oct 15 18:32 54.json.archived-2026-10-15-2
$ sha256
b15d26ce59ac00b2755d5a850a6a371b2bc38ca34b665002877a2dc703a8bd26  .turingmind/REVIEW-54-2026-10-15-2.md
9e0b5ebbbf5b4fddf65061df37ef78775edeb087758d3c9f1be11eec393c873b  .turingmind/REVIEW-54-2026-10-15.md
568f023a6a08776f6752a6934659bb7cfdcbde55c56e4d76f62ecefdbd6780c5  .turingmind/REVIEW.md
e82f5bf2fa25322cc04873062d3ee0df1c16994c6cc9b9915512ea6ab63bcd30  .turingmind/state/format-53/54.json.archived-2026-10-15
9f9e36847f2aff88b7951761bd23eb367a81a54979778b347ec2e8098a40bad1  .turingmind/state/format-53/54.json.archived-2026-10-15-2

===== UNSTAMPED: two same-day passes with an unstamped REVIEW.md =====
unstamped-1 review-closed exit: 1
>>> pass 1: prior-REVIEW.md fence
.turingmind/REVIEW-unstamped-2026-10-15.md
An earlier REVIEW.md was written by a plugin version that does not read this review's state; archived aside as REVIEW-unstamped-<date>.md — it did not close this review.
--- after pass 1 ---
total 
drwxr-xr-x@ 96 Oct 15 18:32 .
drwxr-xr-x@ 128 Oct 15 18:32 ..
-rw-r--r--@ 91 Oct 15 18:32 REVIEW-unstamped-2026-10-15.md
4656382aa9c8242b7aba0b1a9ea4043df08a3dcb26414aa6aa2a6c2029b45462  .turingmind/REVIEW-unstamped-2026-10-15.md
unstamped-2 review-closed exit: 1
>>> pass 2: prior-REVIEW.md fence
.turingmind/REVIEW-unstamped-2026-10-15-2.md
An earlier REVIEW.md was written by a plugin version that does not read this review's state; archived aside as REVIEW-unstamped-<date>.md — it did not close this review.
--- after pass 2 ---
total 
drwxr-xr-x@ 128 Oct 15 18:32 .
drwxr-xr-x@ 128 Oct 15 18:32 ..
-rw-r--r--@ 91 Oct 15 18:32 REVIEW-unstamped-2026-10-15-2.md
-rw-r--r--@ 91 Oct 15 18:32 REVIEW-unstamped-2026-10-15.md
e62b06e465035c963c62296aaf4dd00cde4180b8aeea146bc1c84236ebda1707  .turingmind/REVIEW-unstamped-2026-10-15-2.md
4656382aa9c8242b7aba0b1a9ea4043df08a3dcb26414aa6aa2a6c2029b45462  .turingmind/REVIEW-unstamped-2026-10-15.md
```
