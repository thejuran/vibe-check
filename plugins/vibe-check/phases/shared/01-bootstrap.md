# Bootstrap — trusted helper resolution

> **Read FIRST, before any phase, by both `/review` and `/deep-review`, and only AFTER the spine has
> run its seat line.** This file binds the helper paths every later phase uses. Nothing else reads it;
> nothing else may re-resolve them.

**Resolve `$GUARD_PY` ONCE (unconditional — Fable A7/B2).** Path containment is no longer an inline `case "$REAL/" in "$ROOT/"*` transcription — the ≥5 hand-copied snippets had ALREADY drifted (four failed OPEN on an empty `$ROOT`; the deep-review/fix copies silently downgraded findings about deleted files). Every containment decision now calls the ONE tested `scripts/guard.py` (fail-closed: empty root/path, non-dir root, and any escape all refuse; missing-path TOLERANT: a deleted-but-in-diff file is judged lexically; relative `--path` values resolve against `--root`). Bind it here with the SAME TRUST-01 resolver that binds `$SCORE_PY`/`$CONFIG_PY` (guard.py sits in the same `scripts/` dir):

`$VC_ROOT`, `$GUARD_PY`, `$CONFIG_PY`, `$SCORE_PY` are bound HERE, once, and carried forward like `$CONFIG_*` — later phases substitute the resolved absolute paths and never re-resolve. The spine's seat line is the only place the load-time token is spelled on this path; the resolver body reads the value the seat exported. The owner's dev override is the env var `VIBE_CHECK_PLUGIN_ROOT` (exported by the owner; the recommended dev workflow is `claude --plugin-dir <repo>/plugins/vibe-check`, which makes arm (1) the working tree).

Run the block below in the SAME Bash call as the spine's seat line, seat first. If the two end up in
separate Bash calls, re-emit the seat line at the top of the call that runs this block — each Bash call
may be a fresh shell, and an unset seat value makes every consumer take its terminal arm.

```bash
# TRUST-01 resolver — the trusted plugin root arrives from the SEAT line above (a loader substitution the
# reviewed repo cannot reach). Arm (2) is an env var the OWNER exports (`VIBE_CHECK_PLUGIN_ROOT`) — never
# read from the reviewed repo. There is NO repo-relative arm and NO cache-glob/marketplace arm. If BOTH arms
# are empty every consumer takes its terminal arm.
VC_ROOT="${VIBE_CHECK_PLUGIN_ROOT_SUBST:-}"
[ -z "$VC_ROOT" ] && VC_ROOT="${VIBE_CHECK_PLUGIN_ROOT:-}"
# (3) terminal arm is PER CONSUMER (D-13): guard/score FAIL CLOSED on empty; config DEGRADES to defaults.
GUARD_PY="";  [ -n "$VC_ROOT" ] && [ -f "$VC_ROOT/scripts/guard.py" ]  && GUARD_PY="$VC_ROOT/scripts/guard.py"
CONFIG_PY=""; [ -n "$VC_ROOT" ] && [ -f "$VC_ROOT/scripts/config.py" ] && CONFIG_PY="$VC_ROOT/scripts/config.py"
SCORE_PY="";  [ -n "$VC_ROOT" ] && [ -f "$VC_ROOT/scripts/score.py" ]  && SCORE_PY="$VC_ROOT/scripts/score.py"
# /TRUST-01 resolver
# Terminal arm: $GUARD_PY EMPTY. Every consumer FAILS CLOSED on that (treats the
# path as NOT contained / refuses) — a security guard degrades to refusal, never
# to pass-through. (Contrast: $CONFIG_PY degrades to defaults; $SCORE_PY halts.)
# Print what was bound, so every later phase can substitute the RESOLVED absolute paths.
printf 'VC_ROOT=%s\nGUARD_PY=%s\nCONFIG_PY=%s\nSCORE_PY=%s\n' "$VC_ROOT" "$GUARD_PY" "$CONFIG_PY" "$SCORE_PY"
```

Callers branch on guard.py's EXIT CODE (0 = every `--path` contained; non-zero = refuse), never by parsing its stdout. Do NOT re-inline the `case` compare anywhere in the phase files, the command spines, or the agents — that is how the copies drifted apart in the first place.

Carry these forward for the whole invocation: `$VC_ROOT`, `$GUARD_PY`, `$CONFIG_PY`, `$SCORE_PY`.
Later phases substitute the RESOLVED ABSOLUTE PATHS into their own Bash calls and never re-resolve.

**Why arm (1) is an env var and not the load-time token.** The bytes of this file arrive through
`Read` and are NOT loader-processed — the token would survive here as dead literal text. The spine
that read this file IS loader-processed, so the spine performs the substitution once, on its seat
line, and exports the value. This file consumes that value. If you are ever tempted to "restore" the
token here, that change would silently unbind every helper path.

**Reading later phase files.** Every later read instruction is written against `$VC_ROOT` — for
example **Read $VC_ROOT/phases/review/06-config.md**. Substitute the resolved value printed above;
never carry the raw plugin-root token into a Read path, and load every phase file with the Read tool,
never with a Bash `cat`. (This file lives under `phases/`, where the token count must be zero — so this
warning names the token rather than spelling it.)
