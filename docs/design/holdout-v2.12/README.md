# v2.12 sealed holdout

The holdout is the one test of v2.12 that tuning never sees. This file explains what protects
it and what does not, and gives you, the owner, the exact commands to build it, seal it and
lock it away.

Every command below is one line. Run every one of them from a **new Terminal window that you
opened yourself** (not one started by Claude). Each kit command prints plain `OK: ...` or
`PROBLEM: ...` lines. When a line says PROBLEM, fix only what it names.

---

## 1. What this is

- **Six cases, sealed before tuning starts.** Three catch cases (C1 newly reachable exposure,
  C2 removed protection, C3 ordinary bug) and three quiet cases (Q1, Q2, Q3). They are found
  in your own repositories by an isolated finder session and checked by an isolated
  cross-check session. Both are sessions you launch and drive yourself, with their own
  configuration folders; this repo only supplies the kit (D-04, D-05).
- **Stored outside every git repo**, at `~/.vibe-check-holdout/v2.12/`. Once sealed, the
  folder holds one encrypted archive and no plaintext (D-07).
- **Only `SEAL.json` is committed** (`docs/design/holdout-v2.12/SEAL.json`). It holds opaque
  case IDs, slots and keyed hashes, nothing else.
- **The assistant never reads case content.** Not the cases, not the keys, not the finder's or
  cross-check's notes, not their screens.

**The one rule for every message from you to the assistant about the holdout:** the only
things that ever cross are opaque IDs, slot names, hashes, counts and the fixed status words
that `resume-check` accepts (section 7c). Nothing else, ever. No "C1 is the auth one", no repo
names, no "the proof was flaky".

---

## 2. Barrier, not proof

The tuning side is kept away from the holdout by a PreToolUse hook (`tools/holdout_guard.py`,
installed in this repo's local settings and in your user-level settings) plus permission deny
rules. They stop Claude tool calls (every tool, every subagent, every MCP tool) that reach the
holdout folder. **They are a barrier, not proof: defense in depth, not a complete filesystem
boundary.**

Residuals (what the hook does not stop):

- **Deliberate obfuscation**: a command that builds the path at run time (variable
  concatenation, command substitution, a string assembled inside a Python or Node script).
- **Traversal beyond the listed recursive readers**: `find ~`-style walks are caught only for
  the readers the hook knows (find, grep -r, rg, du, tar, rsync, cp -r, ls -R, zip -r, tree,
  fd, Grep, Glob), and a Grep or Glob with no path run from your home folder is not caught.
- **dotglob**: a bare `~/*` is not treated as reaching a dot-folder, which is wrong when the
  shell has dotglob switched on.
- **Codex and every other non-Claude process.** The hook is a Claude Code hook; Codex, editors
  and scripts you run yourself never pass through it.
- **Sessions launched without the user-level copy** (another config folder, another machine,
  or a settings file that lost the entry).
- **Fail-open**: if `python3` is missing, the script path is wrong, or the hook times out,
  Claude Code lets the call through. `check-install` (section 9) detects all three, and it
  runs at every session start.
- **leakscan's reach**: leakscan matches raw and JSON-decoded text line-by-line, so it cannot
  see holdout content that was re-wrapped across lines, re-encoded another way, or
  paraphrased. That is why any described case is replaced even when the scan is clean
  (section 7c).

What actually covers these residuals: **after `scrub`, no plaintext exists on disk.** The
archive is encrypted with a passphrase only you hold, typed at openssl's own prompt. It is
never in a file, an environment variable, a command line or any session.

`RESULTS-v2.12.md` must repeat this wording: the hook and encryption are a barrier, not proof,
with the residuals above (HOLD-04).

---

## 3. What is public and what is private

**Public (`SEAL.json`, committed once, before tuning):**

| Field | Meaning |
|-------|---------|
| `schema`, `milestone`, `status` | fixed values |
| `mac` | a fixed description of how each case hash is built |
| `key_commitment_sha256` | SHA-256 of the private HMAC key |
| `cases` | `{ "<opaque ID>": { "slot": "C1".."Q3", "hmac": "<64 hex>" } }` |
| `archive_sha256` | SHA-256 of the encrypted archive |

**Why HMAC and not plain SHA-256 (D-12):** commit IDs and diffs from your repos are
enumerable. Anyone with the repos could hash every commit and diff and match a plain SHA-256.
Each case hash is therefore HMAC-SHA256 under a fresh, private 256-bit key, over a
deterministic listing of every file in the case and its answer key. The key is not derived from
your passphrase.

**Private (inside the encrypted archive only):** the cases, the answer keys, the proofs and
their recorded results, the provenance and search records, the cross-check verdicts, the HMAC
key and the per-file inventory. Phase 55 decrypts privately and checks both the per-case
HMACs and the key commitment (`rehash`).

---

## 4. Considered and declined

- **An OS sandbox in this (tuning) repo** (`sandbox.filesystem.denyRead` on the holdout).
  Declined: once scrub has run there is no plaintext to protect, and a tuning-side sandbox
  would break normal development commands.
- **Other encryption tools.** `hdiutil` encrypted disk images (mountable plaintext that tuning
  sessions could read while mounted), `gpg` symmetric mode (its agent may cache the
  passphrase), `zip -e` (weak legacy encryption). The kit uses `/usr/bin/openssl enc
  -aes-256-cbc -pbkdf2 -iter 600000`, which ships with macOS.
- **`rm -P` secure delete.** It has no effect on modern macOS file systems. FileVault is the
  at-rest baseline for anything deleted.

---

## 5. Before you start (once)

1. **Logins.** The finder and the cross-check each run with their own configuration folder,
   so the first launch of each asks you to log in: type `/login` once in the finder session
   and once in the cross-check session. A later cross-check generation (`bin/crosscheck-r2`,
   `-r3`, ...) has its own configuration folder too and asks again.
2. **Passphrase.** Pick the archive passphrase now and store it in your password manager.
   Never type it into a Claude session, a file or a command line.
3. **Pick the eligible repos.** These are the git repos found under your home folder, minus the
   four exposed during B3 development (triggarr, seedsyncarr, roonseek, dashboard) and the two
   tuning repos (turingmind-code-review, thejuran-marketplace), which can never be used:

   bridgarr, DVC, efficacy-fixture, Fellow-Call-Schedule, gsd-for-pos, gsdboard, iPlayarr,
   iviewarr, NephSched, phi-compli, seedsync, shannon, sonoscrub, VisualSchedules, VolvLog,
   ytfortv

   Two notes: `efficacy-fixture` was built to test vibe-check, so it is a poor source; and
   `seedsync` may share history with seedsyncarr, so keep it out of C1 and Q2. **C1 and Q2
   must come from repos that are not triggarr, seedsyncarr, roonseek or dashboard (D-13).**
   You may still pass the B3 repos to `setup` for the other four slots; setup marks them as
   previously exposed.

---

## 6. Dry run first (dummy data)

Preferred: run the autopilot (section 7e) after step 1; the steps below are the manual fallback and the reference the autopilot's stop messages point to.

This rehearses the whole pipeline on six fake cases before any real case exists (D-15). It
checks three things only a real Terminal can show: the cross-check sandbox really blocks
reads, the finder can read the kit and write `sealed/`, and openssl really prompts for the
passphrase.

1. `python3 ~/turingmind-code-review/docs/design/holdout-v2.12/tools/holdout_kit.py --folder ~/.vibe-check-holdout/dryrun setup --repo ~/bridgarr`
   (any eligible repo works; nothing is read from it in the dry run). Expect the last line
   `OK: holdout folder ready at ...`.
2. **Cross-check sandbox check.** `~/.vibe-check-holdout/dryrun/bin/crosscheck` (first time:
   `/login`), then type exactly:
   `Run python3 sandbox-probe.py and reply with its exact output.`
   Expect `OK: sandbox denied 8/8 protected reads and writes` (sealed/, work/, cfg-finder/,
   the finder brief, the finder and owner scratch roots, and a read of and a write into
   Claude Code's shared temp directory `/tmp/claude-<uid>`). Anything else (a PROBLEM line, a permission
   prompt asking to run without the sandbox, or output that quotes a sentinel) means stop,
   decline any such prompt, and report `blocked sandbox`. Then `/exit`.
3. **Finder check.** `~/.vibe-check-holdout/dryrun/bin/finder` (first time: `/login`), then
   type exactly:
   `Read ../kit/FINDER-BRIEF.md and reply only with its first heading. Then run: touch ../sealed/WRITE-CHECK && rm ../sealed/WRITE-CHECK && echo finder-write-ok`
   Expect the heading `# Finder brief` and the line `finder-write-ok`. If the Read is refused,
   the command fails, or Claude asks to run it without the sandbox, decline and report
   `blocked sandbox`. Then `/exit`.
   Setup writes the finder's settings as two files: `work/.claude/settings.json` (the denies
   and the sandbox, including the write ban on `kit/` and the repos) and
   `cfg-finder/settings.json` (the directories the finder may use: the repos, `sealed/` and
   `kit/`). The second file must stay in `cfg-finder/`: Claude Code ignores those directories
   when a workspace's own settings name them, so the Read and the write above would both be
   refused. "Fix the finder settings" means run setup again in a fresh folder; do not edit
   either file by hand.
4. `~/.vibe-check-holdout/dryrun/bin/holdout dryrun --populate`
   Expect `OK: dummy holdout populated with 6 synthetic cases. ...`. It also writes
   `DRY-RUN.json` at the top of the folder: from now on the real `seal`, `seal-build`,
   `rehash` and `publish` refuse this folder, and only the `--dry-run` forms below work.
5. `~/.vibe-check-holdout/dryrun/bin/holdout validate`
   Expect `OK: all 16 checks passed`, `Warnings: 0`, `Non-runnable cases: 0`.
6. `~/.vibe-check-holdout/dryrun/bin/holdout seal --dry-run`
   Expect `OK: sealed 6 cases. Next: bin/holdout encrypt`. The SEAL.json it writes says
   `"status": "dry-run"`, which publish and the Phase-55 rehash always refuse.
7. Make sure both dry-run sessions are closed (`/exit`, window closed), then
   `~/.vibe-check-holdout/dryrun/bin/holdout encrypt`
   Type a throwaway passphrase (not the real one): openssl asks twice, then once more to
   verify. Expect `OK: archive written`, `OK: archive decrypts and re-hashes clean (6 cases)`,
   `OK: archive_sha256 recorded in SEAL.json`. **If openssl does not prompt** (it fails, hangs,
   or finishes without asking), stop and report it with the reply form
   `dry run ok no-prompt` (A2).
8. `~/.vibe-check-holdout/dryrun/bin/holdout rehash --dry-run --seal ~/.vibe-check-holdout/dryrun/SEAL.json --sealed ~/.vibe-check-holdout/dryrun/sealed`
   Expect `OK: all 6 cases match the seal; key commitment verified; N files in inventory`.
9. `~/.vibe-check-holdout/dryrun/bin/holdout leakscan --repo ~/turingmind-code-review`
   Expect `OK: leak scan: 0 matches across N probes (raw + JSON-decoded)`. (The fake text is
   random per dry run, so any match is a real problem: report `blocked leakscan`.)
10. **Do not run `publish` in the dry run.** It would put the dummy SEAL.json into the repo.
11. `~/.vibe-check-holdout/dryrun/bin/holdout scrub --yes`
    Expect `OK: plaintext removed (...)`. A `residue:` line names something outside the folder
    to delete by hand.
12. `rm -r ~/.vibe-check-holdout/dryrun`

Reply to the assistant with exactly `dry run ok prompted sandbox=ok` only if every step above
passed (openssl prompted, the probe printed its OK line, the finder check passed). That is the
only reply that lets the run proceed. Every other form (`dry run ok`, `dry run ok prompted`,
`dry run ok no-prompt`, `... problems=N`) is recorded as a failed dry run and stops it, and
`blocked sandbox`, `blocked leakscan` or `blocked other` say what failed.

---

## 7. The real run

Preferred: run the autopilot (section 7e) after step 1; the steps below are the manual fallback and the reference the autopilot's stop messages point to.

Rules for the whole run:

- Open a **new Terminal window** (not one started by Claude) for every command and session.
- **Never run Codex or any tuning session in this repo between `setup` and `scrub`.** While
  plaintext exists, the residuals in section 2 are open.
- **Before `encrypt`, close every isolated session** (finder and cross-check), and start none
  until `scrub` has finished.
- If a step prints PROBLEM, fix only what it names.

The run sheet:

1. `python3 ~/turingmind-code-review/docs/design/holdout-v2.12/tools/holdout_kit.py --folder ~/.vibe-check-holdout/v2.12 setup --repo ~/<repo1> --repo ~/<repo2> ...`
   (one `--repo` per eligible repo you picked in section 5).
2. `~/.vibe-check-holdout/v2.12/bin/finder`, then in the session type
   `Read ../kit/FINDER-BRIEF.md and begin.` (the finder starts in the `work/` folder, so the
   kit is one level up). Answer its questions only inside that session.
3. When the finder says it is done: `~/.vibe-check-holdout/v2.12/bin/holdout validate`
4. `~/.vibe-check-holdout/v2.12/bin/holdout crosscheck-prepare`
5. `~/.vibe-check-holdout/v2.12/bin/crosscheck`, then **before anything else** type
   `Run python3 sandbox-probe.py and reply with its exact output.`
   Require `OK: sandbox denied N/N protected reads and writes`. The script names no protected path on its
   command line, so this proves the OS sandbox, not the hook, is what stops a script from
   opening `sealed/`. A PROBLEM line means close the session and reply `blocked sandbox`.
   Only then type `Read CROSSCHECK-BRIEF.md and begin.`
6. When the cross-check session says the blind verdicts are written, in a second plain
   Terminal window: `~/.vibe-check-holdout/v2.12/bin/holdout crosscheck-reveal --ready`
7. Back in the cross-check session type `The owner has revealed. Continue.` and let it write
   its final verdicts.
8. `~/.vibe-check-holdout/v2.12/bin/holdout seal` (if it refuses, see 7b).
9. **Close the sessions:** `/exit` in the finder session and in every cross-check session,
   close their windows, and wait a few seconds. `encrypt` and `scrub` refuse while any process
   still has the holdout open (as its working directory, an open file, or on its command
   line), and they refuse outright if that check cannot run. On
   `holdout folder is still in use by N process(es)`, close what it names and re-run.
10. `~/.vibe-check-holdout/v2.12/bin/holdout encrypt` (the real passphrase: openssl asks twice,
    then once more to verify).
11. `~/.vibe-check-holdout/v2.12/bin/holdout leakscan --repo ~/turingmind-code-review`
    (after encrypt, because encrypt rewrites SEAL.json and publish wants a scan of the final
    seal). Any match: section 7d.
12. `~/.vibe-check-holdout/v2.12/bin/holdout publish --repo ~/turingmind-code-review`
13. `~/.vibe-check-holdout/v2.12/bin/holdout scrub --yes` (it walks the folder twice a couple of
    seconds apart; both walks must be clean).
14. Reply to the assistant with exactly `sealed` (or `sealed non-runnable=N` when validate
    reported N non-runnable cases).

### 7b. When seal refuses a case

`seal` checks every case, and each refusal has exactly one way forward.

**(i) `the independent check disagreed (<part>)`.** The cross-check session's blind verdict
does not match the key: on type (for example it saw an ordinary C3 bug where the key claims a
C1 newly reachable exposure), defect location, causal-failure category (or either side said
`other`), quiet confirmation, its own final flags, or `proof exits` (its re-run of the proof
gave exits that differ from the recorded ones or do not fit the slot pattern, for example a
catch proof that passes on both trees: the proof or the key is wrong, and `proof_agrees: true`
does not cover it).

**Diagnose first.** Before retiring or resetting anything, run `bin/holdout diagnose --slot <S>`
(the holdout folder's `bin/`) in a new Terminal window. It reads only, prints an `action <S>:`
line for you and, last, one line in fixed words: `diagnosis <S> cause=<cause> checks=<checks>`.
It never prints a file, line, category, prose or case ID, so that line (and only that line) may
be sent to the tuning session. The cause sorts the failure:

| cause | meaning | way forward |
|---|---|---|
| `key-unsealable` | the key says `other`, or the recorded proof exits are missing or do not fit the slot | case/key problem: retire and replace |
| `judge-disagrees` | the judge, having read the key, still disagrees | case/key problem: resolve with evidence or replace; before a second replacement of the same slot, send the diagnosis line |
| `checker-suspect` | the judge accepted the key's defect but the mechanical location check did not | do not retire, reset or replace; send the diagnosis line |
| `proof-mismatch` | the judge's proof re-run did not reproduce the recorded exits | do not retire, reset or replace; send the diagnosis line |
| `incomplete` | the round is not finished | run the autopilot again |

The agreement rule itself never changes because of a diagnosis: a suspect is fixed in the
tuning repo, then `refresh-kit` and the autopilot re-check the same, untouched verdicts.

**Re-judge (`proof-mismatch` with only `proof-rerun-missing`).** The judge agreed on type,
defect and category but its sandbox could not run the proof, so it recorded no exits. Once the
cause is fixed in the kit, `refresh-kit`, then `bin/holdout autopilot --repo
~/turingmind-code-review --rejudge <S>` archives that round and judges the case again, blind, in
a fresh generation. It refuses every other diagnosis, so it can never answer a disagreement.
Role sessions keep the owner Terminal's PATH (the launchers save it as `HOLDOUT_ROLE_PATH`, and
`bin/role-env.sh` restores it in every Bash command): proofs run with the PATH their recorded
exits came from.
Otherwise, two ways forward:

- **Resolve with evidence.** Write `sealed/keys/<ID>/resolution.md` (what the evidence is; no
  new verdict), then `~/.vibe-check-holdout/v2.12/bin/holdout crosscheck-reset <ID> --reason resolved`,
  then `~/.vibe-check-holdout/v2.12/bin/holdout crosscheck-prepare --case <ID>`. Because the
  first cross-check session has already seen keys, this prints
  `fresh cross-check workspace xcheck-r2` and names a NEW launcher (`bin/crosscheck-r2`, then
  `-r3`, ...). Close the old cross-check session, open a new Terminal window and run that
  launcher (`/login` if asked; the new session has its own configuration folder and cannot
  read the old workspace, which is the point). Run the probe first
  (`Run python3 sandbox-probe.py and reply with its exact output.`): its targets now include
  every earlier workspace, configuration folder and scratch root, so N grows by three per
  earlier generation (9 for `-r2`, 12 for `-r3`). Then type `Read CROSSCHECK-BRIEF.md and begin.`
  and say nothing about the previous round or why the case is back. When it says the blind
  verdict is written, reveal with `crosscheck-reveal --ready` in the second window, let it
  write its final verdict, and run `seal` again.
- **Replace the case.** First `~/.vibe-check-holdout/v2.12/bin/holdout retire --slot <S> --reason owner`
  (so the withdrawn change can never come back under a new name). Then tell the finder session
  to delete that slot and re-find it as a different change within the same 25-candidate
  budget, and repeat from `validate`. The replacement's cross-check also lands in a fresh
  workspace.

Never ask a cross-check session that has seen a reveal to judge anything again. The seal
refuses a round judged in a workspace that had already seen a key.

**(ii) `sealed inputs changed after the cross-check (<members>)`.** A case or its proof was
corrected after its packet was prepared. The old verdict is about different bytes and is never
reused: `bin/holdout crosscheck-reset <ID> --reason inputs-changed`, then the
prepare/judge/reveal/final steps for that case (a fresh workspace, as above), then `seal`.

**(iii) `final.json is not bound to this reveal` or `blind verdict changed after reveal`.** A
verdict file was edited or copied from an older round. Reset and redo that case.

**(iv) `validation failed`.** Fix only what `validate` names, then `seal`. If the fix changes a
case or a proof, (ii) follows and that case's cross-check is redone.

**(v) `round N was judged in cross-check workspace <ws>, which had already seen a revealed key`.**
A reset case was judged by the old session, or its packet was slipped into a revealed
workspace. `bin/holdout crosscheck-reset <ID> --reason owner`, then
`bin/holdout crosscheck-prepare --case <ID>` (it mints the next workspace) and a new session.

Re-running `validate` or the proof never clears (i), (ii), (iii) or (v). Editing `blind.json`,
`final.json`, the ledger or the workspace registry by hand is always detected. Every refusal
ends in a fresh blind verdict, by a session that has never seen a key, on the exact bytes that
will be sealed (D-06).

### 7c. If a checkpoint reply carried case details

The assistant checks every checkpoint reply with
`python3 docs/design/holdout-v2.12/tools/holdout_kit.py resume-check` (reply on stdin). These
are the only accepted replies, exactly as written:

| Reply | Meaning |
|-------|---------|
| `dry run ok prompted sandbox=ok` | dry run passed (the only passing dry-run reply) |
| `dry run ok`, `dry run ok prompted`, `dry run ok no-prompt`, `dry run ok no-prompt problems=5` | dry run failed; the run stops |
| `sealed`, `sealed non-runnable=1` | the holdout is sealed, encrypted, published and scrubbed |
| `replaced slots=C1,Q2` (optionally `non-runnable=1`) | those slots were replaced and the holdout re-sealed |
| `clean leakscan=0` | an incident check found nothing and nothing was described |
| `blocked disagreement`, `blocked validation`, `blocked leakscan`, `blocked residue`, `blocked no-prompt`, `blocked sandbox`, `blocked other` | stopped; the word says where |

Anything else, including a friendly extra word, is treated as a contamination incident,
because the reply already sits in the tuning session's transcript and cannot be unsaid.

1. The assistant stops and records only `incident: non-conforming checkpoint reply` (never the
   text). It does not commit SEAL.json and does not mark HOLD-01..04 done.
2. End that Claude session (`/clear` is not enough: close it) and delete its transcript under
   `~/.claude/projects/-Users-julianamacbook-turingmind-code-review/`.
3. In a new Terminal window:
   `~/.vibe-check-holdout/v2.12/bin/holdout leakscan --from-archive --repo ~/turingmind-code-review`
   It decrypts the archive into `tmp/owner/`, scans the tuning side including `~/.claude`, and
   prints the slots whose text leaked. If it retired anything (it prints `retired <slot>`
   lines), run `~/.vibe-check-holdout/v2.12/bin/holdout scrub --yes` again afterwards: the
   retirement rewrites the finder's skip list inside the folder.
4. Replace every slot leakscan names, plus every slot you described in any way, even
   paraphrased. Leakscan has already retired the named cases by content into `RETIRED.json`.
   - `~/.vibe-check-holdout/v2.12/bin/holdout decrypt --archive archive/holdout-v2.12.tar.enc --dest ~/.vibe-check-holdout/v2.12`
   - for each described slot leakscan did not name:
     `~/.vibe-check-holdout/v2.12/bin/holdout retire --slot <S> --reason owner`
   - `~/.vibe-check-holdout/v2.12/bin/holdout retire --sync` (the decrypt restored an older
     finder skip list; this rewrites `work/RETIRED-REVISIONS.json` from `RETIRED.json`)
   - delete `SEAL.json` in the holdout folder, the published
     `docs/design/holdout-v2.12/SEAL.json` in the repo (it is not committed yet; if it were,
     stop and bring it to the orchestrator) and the holdout's `archive/`, deliberately
   - have the finder session re-find those slots as DIFFERENT changes within the same 25
     budget (the same commit, diff or key under a new ID is refused by `seal` and `publish`
     with `reuses material retired`)
   - then `validate`, `crosscheck-prepare` (fresh workspace), the new cross-check session,
     reveal, `seal`, close the sessions, `encrypt`, `leakscan`, `publish`, `scrub --yes`.
5. Start a clean tuning session and reply exactly `replaced slots=<the slots>`. If leakscan
   reported 0 and you described nothing, reply exactly `clean leakscan=0` in the clean session
   instead.

The assistant continues to the seal commit only after a conforming `sealed`,
`replaced slots=...` or `clean leakscan=0` reply in a session that has no incident.

### 7d. If leakscan reports matches

A match means holdout text already sits on the tuning side (a transcript, Codex history, shell
history, the repo tree or its git history) and may already have shaped a tuning agent.
Deleting the match removes the evidence, not the influence. So: never delete-and-rerun.

`publish` refuses mechanically. Every scan is appended to `LEAKSCAN.json`, a ledger in the
holdout folder that scrub keeps. Right after a scan with matches, publish says the last scan
found holdout text; after a clean re-scan with the same case still sealed it says the case
`has not been replaced` (deleting the matched files is cleanup, not a remedy). It accepts only
when every slot any scan named has been REPLACED (a new ID from the finder) and the holdout is
re-sealed.

Replacement means a DIFFERENT change. The scan retires every named case by content (source
revision, diff, changed lines, key) into `RETIRED.json`, which is never archived and never
scrubbed, and rewrites the finder's skip list `work/RETIRED-REVISIONS.json`. The same revision
or diff re-found under a new ID is refused by `seal` and `publish` with
`reuses material retired`; without that, the finder's fixed screening order would pick the
same commit again.

Procedure:

1. Close any tuning session whose transcript was named. Delete the named files or entries, as
   cleanup only.
2. Delete `SEAL.json` in the holdout folder and the holdout's `archive/`, deliberately.
3. Have the finder session delete each named slot's case and re-find it within the same 25
   budget.
4. `bin/holdout validate`, then `bin/holdout crosscheck-prepare --case <new ID>` (fresh
   workspace; run the probe first in the new session), reveal, `bin/holdout seal`.
5. Close every isolated session, then `bin/holdout encrypt`,
   `bin/holdout leakscan --repo ~/turingmind-code-review` (expect 0),
   `bin/holdout publish --repo ~/turingmind-code-review`, `bin/holdout scrub --yes`.
6. Reply exactly `replaced slots=<slots>` (not `sealed`).

If a match is in the current tuning session's own transcript, it is also a 7c incident: end
that session first and continue in a clean one.

**Dry run only: re-scan clean, then finish without replacement (owner decision, 51-09).** The
dry run's cases are dummy material, so a match there proves the scan works rather than
contaminating anything. The hit is still recorded exactly as above (`LEAKSCAN.json` keeps it,
the named cases stay retired in `RETIRED.json`). Do step 1 (close the named session, delete
the named copy), then run the dry-run autopilot again with plain `--dry-run`. It always scans
afresh after a scan with matches; if that fresh scan, against the same dry-run seal, is clean,
it writes `LEAK-WAIVER.json` (each named dummy case kept under its ID, marked
`"leak": "waived (dry-run)"`, bound to the folder, the seal bytes and the clean scan) and
finishes without any replacement or new cross-check generation. If the scan still matches, it
stops again. `LEAK-WAIVER.json` is a dry-run marker like `DRY-RUN.json`: the real `seal`,
`seal-build`, `publish`, `rehash` and the real autopilot refuse any folder holding it, and the
real leak gate never reads it. In the real run nothing here applies: a clean re-scan still
requires the replacement above.

## 7e. Autopilot: the one-command run

The autopilot runs everything in sections 6 and 7 after `setup` from one command in a plain
Terminal window (not one started by Claude: it refuses there, like every kit command). You do
not drive any session by hand and you paste nothing but its last line.

**The two commands.**

- Dry run, after section 6 step 1 (`setup` into the dryrun folder):
  `~/.vibe-check-holdout/dryrun/bin/holdout autopilot --dry-run`
  Reply `dry run ok prompted sandbox=ok` only when that is the line it printed last. Then
  `rm -r ~/.vibe-check-holdout/dryrun` as before (section 6 step 12).
- Real run, after section 7 step 1 (`setup` into the v2.12 folder):
  `~/.vibe-check-holdout/v2.12/bin/holdout autopilot --repo ~/turingmind-code-review`
  Reply with exactly the last line it printed (`sealed`, `sealed non-runnable=N`,
  `replaced slots=...`, or a `blocked ...` line).

**What it does.** In order: preflight, the finder, `validate`, the cross-check (one generation
at a time: sandbox probe, blind verdicts, reveal, final verdicts), `seal`, close-sessions (the
writer check), `encrypt`, `leakscan`, `publish`, `scrub`. The finder and every cross-check
session run headless in Claude Code's print mode, through the same launchers
(`bin/finder`, `bin/crosscheck`, `bin/crosscheck-rN`), so they keep the same config folders,
scratch roots, settings, guard hook and sandbox as when you open them yourself. Every reset
after a reveal is judged by a fresh generation, as in 7b. The dry run does the same on the six
fake cases and also judges one of them headless in a fresh generation (`bin/crosscheck-r2`), so
expect one short real session there; it never runs `publish`.

**The dry run's pass rule (owner decision, 51-09).** The dry run proves the machinery works;
agreement on real cases belongs to the real run. The headless judging session still has to run
in full (sandbox probe, blind verdict, reveal, final verdict) and write a well-formed
`blind.json` and `final.json`; if it does not, the run stops with `blocked other`. Whether that
judge agreed with the fake case's label is recorded, never required: the terminal shows
`step crosscheck: real judge verdict recorded (agreed)` or `(disagreed)`, and the judge's files
are kept exactly as written (their hashes stay bound in the ledger). A disagreement is sealed
on an explicitly marked `SYNTHETIC-AGREEMENT.json` (`"mode": "dry-run"`, the case IDs it
covers, bound to the judge's exact verdict files), which only `seal --dry-run` in a folder
carrying `DRY-RUN.json` accepts. The dry-run SEAL.json says `"status": "dry-run"` and, per
judged case, `judge_outcome` (and `"agreement": "synthetic"` where it disagreed). The real
`seal`, `seal-build`, `publish`, `rehash` (Phase 55) and the real autopilot refuse any folder
or seal carrying either marker or a dry-run status. A dry-run disagreement never stops at
`blocked disagreement`, never asks for `retire` or `--replace-retired` and never opens another
generation.

**Preflight** (before any case-finding): the Terminal is a real terminal (openssl must be able
to prompt), `claude` is on PATH, `/usr/bin/openssl`, `/usr/bin/tar`, `/usr/sbin/lsof` and
`/usr/bin/pgrep` exist, the finder and cross-check settings pass their self-checks, the role
launchers and `bin/role-env.sh` are current (otherwise it names `refresh-kit`), each role is
logged in (`auth status` through its own launcher), the cross-check sandbox probe reports N/N,
the finder can read the kit and write `sealed/`, and a headless session can be resumed by its
id. It removes `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`,
`ANTHROPIC_PROFILE`, `ANTHROPIC_FEDERATION_RULE_ID` and `ANTHROPIC_ORGANIZATION_ID` from its own
environment first, so each session uses only the login of its own config folder; it never
writes a credential anywhere.

**Role sessions keep their temp files in the folder (51-09).** Claude Code gives a sandboxed
command `$TMPDIR=<CLAUDE_CODE_TMPDIR>/claude-<uid>` only while that path is at most 44 bytes;
every role's temp root under the holdout folder is longer, so Claude Code falls back to the
shared `/tmp/claude-<uid>`, which the sandbox lets commands write by default and which holds
every other Claude session's scratch, the tuning side's included. In the 51-09 dry run the
cross-check judge re-ran a proof in "a fresh export" there, and the leak scan found dummy case
code in `/tmp/claude-<uid>/base-export/`. Now every role's settings (the finder and each
generation) deny `/tmp/claude-<uid>` and `/tmp/claude` in every control: sandbox read and
write, permission `Read`/`Edit` (the file tools are not sandboxed; both the `/tmp` and the
`/private/tmp` spelling), and the guard hook; each self-check fails if any entry is missing.
Each launcher sets `CLAUDE_ENV_FILE=<H>/bin/role-env.sh`, which Claude Code runs inside every
Bash command after its own `TMPDIR` export and which points `$TMPDIR` (and zsh's here-document
prefix) back at the role's own temp root, so temp files, here-documents and Python's
`tempfile` keep working there. The cross-check probe tries to read and to write the shared
directory; both must be denied. One visible side effect: Claude Code writes its
working-directory tracking file into the shared directory after each command, so in every role
session a command that succeeds ends with `operation not permitted: /tmp/claude-<uid>/cwd-...`
and reports exit code 1, and a `cd` does not carry over to the next call. A failing command
keeps its own exit code and has no such line. The briefs say so, and tell each session to keep
scratch and proof copies in its own folders.

**Logins.** The first time, a role is not logged in: the autopilot stops with one line naming
the launcher, for example `run ~/.vibe-check-holdout/v2.12/bin/crosscheck, type /login, ...`.
Do exactly that (`/login`, finish in the browser, `/exit`) and run the same autopilot command
again. A fresh generation (`bin/crosscheck-r2`, ...) has its own config folder, so it asks for
its own login the first time the autopilot reaches it; the dry run asks for one for
`bin/crosscheck-r2`.

**Flags it passes, and never passes.** Each headless prompt runs as
`<launcher> -p <prompt> --output-format json --max-turns 400 --max-budget-usd 40.00
--permission-mode dontAsk --permission-prompts none --allowedTools Bash,Read,Edit,Write,Glob,Grep
--settings '{"sandbox":{"allowUnsandboxedCommands":false}}'` plus either `--session-id <id>`
(a new session) or `--resume <id>` (continuing one). The last two controls are added on top of
the sandbox: no unsandboxed retry can be offered, and nothing can be approved by prompt. It never
passes a flag that skips settings or hooks, bypasses permissions, runs in the background or
turns off session persistence. `--max-turns`, `--budget-usd` and `--session-timeout` change the
caps.

**What the terminal shows.** Step names, counts, slot labels, opaque IDs and fixed lines, then
one result line. Every session's output and every kit command's output go to
`tmp/owner/autopilot/` inside the holdout folder, which is never archived and which scrub
removes. openssl still asks you for the passphrase at the terminal: twice, then once more to
verify (the autopilot prints a line just before).

**When it stops.** Only for these, each with a fixed instruction and the command that continues:

| Last line | What happened | What to do |
|-----------|---------------|------------|
| `blocked disagreement` | real run only (a dry run records the judge's outcome instead): the independent check disagreed on a case (named by ID and slot) | README 7b (i): run `bin/holdout diagnose --slot <S>` first and follow its action; then, when it is a case/key problem, resolve with evidence and `crosscheck-reset <ID> --reason resolved`, then `bin/holdout autopilot` again; or `retire --slot <S> --reason owner`, then `bin/holdout autopilot --replace-retired`. It never resolves a disagreement itself. |
| `blocked validation` | `validate` still failed after three fix rounds with the finder | README 7b (iv), then `bin/holdout autopilot` again |
| `blocked sandbox` | the sandbox probe or the finder check failed (for the finder check, the line above it says whether the kit read, the `sealed/` write, or both failed) | README 6 step 2/3, then `bin/holdout autopilot` again |
| `blocked leakscan` | the leak scan named slots | README 7d steps 1-2 (cleanup only), then `bin/holdout autopilot --replace-retired`. In a dry run: close the named session, delete the named copy, then `bin/holdout autopilot --dry-run` (7d, dry run only): a clean fresh scan finishes without replacement |
| `blocked residue` | scrub found plaintext residue outside the folder | delete what it names, then `bin/holdout autopilot` again |
| `blocked other` | a session failed or timed out, a process still holds the folder, encrypt failed, or seal refused for another reason | follow the line printed just above it, then `bin/holdout autopilot` again |

**Resume.** After any interruption (a closed window, a crash, a timeout) run the same command
again. It continues from `AUTOPILOT.json` (inside the holdout folder; never archived, kept by
scrub) plus what is on disk, and the evidence on disk wins when the two disagree. It resumes each
headless session by the id it recorded before launching it; the finder is told to continue from
the cases and search records it already wrote and never to re-screen. It never asks a
cross-check session that has seen a revealed key to judge again (it stops and names
`crosscheck-reset` instead). A replacement it had started (it records which cases it will delete
before deleting any) is finished by a plain re-run. Scrub's survivor and residue checks run
again on every run before it prints `sealed`. If the finder's session cannot be resumed at all,
it stops and names `bin/holdout autopilot --restart-finder`, the only way to start a fresh
finder session; that keeps every finished case and tells the new session to finish only the
missing slots in the brief's fixed order.

**A dryrun folder from the old retire/replace loop.** A folder an earlier kit left stopped at
`blocked disagreement`, perhaps with extra generations or a case you retired with
`retire --slot <S> --reason owner`, needs no more retirements, replacements or logins: run
`refresh-kit` on it (below; it adds `DRY-RUN.json` only when it can prove the folder is a dry
run), then the plain dry-run command once. It keeps the latest well-formed verdict of each
judged case, seals a case you retired as itself as it stands (the dry-run seal marks it
`"retired_material": "waived"`), and finishes with `dry run ok prompted sandbox=ok`. Without
`refresh-kit` the dry run stops before sealing with one line naming it.

**Dry-run recovery (a leak-retired dummy case).** In a dry run every command a stop message
names carries `--dry-run` (for example `bin/holdout autopilot --dry-run --replace-retired`), and
the same flags work. When the leak scan named a dummy case, the default is 7d's dry-run rule:
remove the leaked copy and run plain `--dry-run`; a clean fresh scan finishes the dry run with
the named cases kept and marked `leak: waived (dry-run)` in `LEAK-WAIVER.json`, with no
replacement and no new generation or login. Replacing the dummy case instead is still possible
with `--dry-run --replace-retired`, and is required when a new case reuses retired material.
With that flag the autopilot records which cases it will delete before deleting any,
removes each retired case (and `SEAL.json` and the archive, if they exist), writes different
dummy material for that slot under a new ID (new commits in the dry-run repo, a new module
variant and a fresh random tag, so the revisions, the diff, the changed lines and the key all
differ from what was retired; it refuses and starts again if any of them still matched), and
judges the new case blind in a fresh cross-check generation (`bin/crosscheck-r3` after the
dry run's `-r2`). Every other case, the journal, earlier generations and every login are left
as they are. A fresh generation has its own config folder, so the first time it stops with
the usual login line for it: `/login` there, then run
`~/.vibe-check-holdout/dryrun/bin/holdout autopilot --dry-run` again. A finished dry-run
replacement ends with `dry run ok prompted sandbox=ok` like any dry run (openssl prompts
again, because the seal and the archive are rebuilt). An interrupted replacement is finished
by a plain `--dry-run` re-run.

**Bringing an existing folder's kit up to date (`refresh-kit`).** `bin/holdout` runs the kit
copy inside the folder (`kit/tools/`), so a fix in the repo does not reach a folder that was
set up before it. In a plain Terminal window run, from the repo's tools (never the folder's
copy, which refuses):
`python3 ~/turingmind-code-review/docs/design/holdout-v2.12/tools/holdout_kit.py --folder <the holdout folder> refresh-kit`
It re-copies the kit docs, templates and tools whose bytes differ, rewrites
`kit/KIT-INVENTORY.json` (scrub's keep list) when it changed, rewrites `bin/holdout`,
`bin/finder`, each existing `bin/crosscheck*` and `bin/role-env.sh` only when setup's text for
it changed, the finder settings only where setup's output changed (in `cfg-finder/` it touches
only the `settings.json` grant, never the login), and in each existing cross-check workspace
only `.claude/settings.json` and `sandbox-probe.py`, regenerated by the same code that mints a
generation. Every settings file is self-checked right after it is written; a failure restores
the previous file and prints a PROBLEM line. It then confirms that nothing else changed:
`sealed/`, `work/`, every login and config folder, the packets and verdicts in each workspace,
`archive/`, `AUTOPILOT.json`, `LEAKSCAN.json`, `RETIRED.json`, `LEAK-WAIVER.json` and the
dry-run repos keep their exact files. The one file it may add is
`DRY-RUN.json`, and only when it can prove mechanically that the folder is a dry run: the
autopilot journal says `dry-run`, both dry-run repos exist and are listed as eligible, and every
case comes from them with the dry run's synthetic key text. It never adds it to the real
folder (whose journal says `real`, or which has none yet); it prints `OK: dry-run marker added`,
`OK: dry-run marker present` or `OK: dry-run marker: not added (...)`. It prints `OK:` lines
only when all of that holds; running it twice changes nothing the second time. Close every
session of that folder first.

---

## 8. After the real run (tuning side)

The assistant:

1. commits `docs/design/holdout-v2.12/SEAL.json` as its own commit
   (`chore(51): seal holdout v2.12 manifest`);
2. runs `python3 docs/design/holdout-v2.12/tools/holdout_kit.py seal-order --repo .` (expects
   `OK: SEAL.json has exactly one commit`) and the public-shape test.

The seal commit must come before the first Phase 53 commit (D-08); `seal-order --before
<first 53- commit>` proves it later.

---

## 9. Checking the barrier is live

- `python3 docs/design/holdout-v2.12/tools/holdout_guard.py check-install` prints
  `OK: holdout guard installed and live (2 settings file(s))`. It reads both settings files
  and sends a live probe through the hook.
- In any normal session, ask Claude to list the holdout folder and expect the line
  `Blocked: this tool call reaches the sealed holdout folder (v2.12 barrier).`
- This check runs at every session start (a SessionStart entry) and is the first step of every
  Phase 52 and Phase 53 plan.
- Worktrees and disposable copies (the Phase 52 harness) are not covered by this repo's local
  settings; the user-level copy covers them (D-14).

---

## 10. Phase 55 (built there, decided here)

- Every holdout run happens in a **separate, isolated evaluation session that the owner
  launches** from a plain Terminal, in a disposable copy with the frozen build installed. The
  assistant **never drives** it, never reads its screen and never uses tmux for it.
  Assistant-driven tmux execution is for the B3 runs only.
- That session runs the holdout detection runs (6 cases x 3) **and** the holdout accepted-fix
  runs (the 3 catch cases x 2 modes: preservation, and seeded from the answer keys).
- Only the per-slot verdict table plus result hashes (and completion and timing for the
  accepted-fix runs) return to the tuning session. No findings text, file names or code.
- Execution is separated from scoring: review runs get only the cases
  (`extract --part cases`), and scoring gets the keys (`extract --part keys`) only after the
  review outputs are saved.
- A verdict that steers tuning retires that slot; it needs a fresh replacement before the
  retune.
- Before any run: `decrypt`, then `rehash`, then `seal-order --before <first 53- commit>`.

STATE.md's v2.12 sequencing note says the same, and Phase 55's plans must repeat it.

---

## 11. Cleanup after v2.12 (explicit step, not now)

The hook stays active for all of v2.12 and is never removed to run the holdout (D-11). After
v2.12 closes:

- `python3 docs/design/holdout-v2.12/tools/holdout_guard.py uninstall --user`
- `python3 docs/design/holdout-v2.12/tools/holdout_guard.py uninstall --repo .`
