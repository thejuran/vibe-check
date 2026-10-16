# Targeted review standing in for missing semgrep bash coverage (candidate 24c0c00038f2)

**Status: this is a review, not a clean scan.** Semgrep 1.136.0's bash parser cannot parse
`run_case.sh` (whole file) and leaves 5 spans of `common.sh` unparsed. In every run, including
the pinned-ruleset runs with no time limit, the 3 bash rules in the pinned ruleset never reached
those lines. This document is a manual review of both files in full against each rule's actual
definition. Using it in place of scanner coverage **changes the security gate and requires the
owner's approval**. The parser limitation stays recorded in `security-gate.json` and
`semgrep-pinned-scan.json`.

- Candidate: `24c0c00038f2d15af4b55f178ea44e680c1f2c58`
- Files, read in full from the candidate's git objects:
  - `docs/design/b3-ground-truth/b3-runner-v2.12/run_case.sh`: 124 lines, sha256 `ff0a86bb883b641333a9821e212d955fa2a161f1ee6acafa539119faad8173f4`. Unchanged at HEAD.
  - `docs/design/b3-ground-truth/b3-runner-v2.12/common.sh`: 309 lines, sha256 `3f1b728f7f11410b1034ec965f8e319e8c973a0c6fc60984893f1d750d374c11`. Unchanged at HEAD.
- Rules: the 3 `languages: [bash]` rules in `semgrep-pinned-ruleset.json` (sha256 `19c843d4805089fac5361e6214c11f3aac61e8c3dd8514fde0b427a4ca0d6490`). Their definitions, metadata removed, are copied into `semgrep-pinned-scan.json` `bash_rules_in_pinned_ruleset`.
- What the scanner missed:
  - `run_case.sh`: all 124 lines.
  - `common.sh`: lines 29, 57, 188-213, 222 and 238. On the rest of the file, `curl-pipe-bash` and `curl-eval` ran. `ifs-tampering` was skipped by semgrep's prefilter because the file has no `IFS` token.
- Method:
  1. Restate each rule's pattern semantics.
  2. List every construct in both files that belongs to the class of risk the rule targets, not only the rule's literal form. That covers downloads, interpreters fed with dynamic text, eval/source/`bash -c`, command substitution that ends up executed, keystroke injection, and IFS changes.
  3. Judge each construct line by line.

## Rule 1: `bash.curl.security.curl-pipe-bash.curl-pipe-bash` (WARNING, CWE-95, confidence LOW)

**What it detects.** It matches any of these patterns: `curl ... | ... bash ...`, `curl ... | ... /bin/bash ...`, `... bash <(curl ...)`, `... /bin/bash <(curl ...)`, `... bash -c "$(curl ...)"` and `... /bin/bash -c "$(curl ...)"`. In other words: content fetched from the network by `curl` and run by bash, whether through a pipe, process substitution, or command substitution into `-c`.

**The broader class reviewed.** Any network fetch (`curl`, `wget`, `fetch`, `nc`, `/dev/tcp`) whose output reaches any shell or interpreter (`bash`, `sh`, `zsh`, `python3`, `source`). Also any interpreter fed text that is not static.

**Network fetches:** none in either file. Neither contains `curl`, `wget`, `fetch`, `nc`, `/dev/tcp` or `/dev/udp`, and no URL appears anywhere in either file.

**Every place an interpreter is fed text, judged:**

| File:line | Construct | Source of the text | Finding |
|---|---|---|---|
| common.sh:64-65, 70 | `script=$(awk … "$book")` then `bash -c "$script" "b3:$name" "$@"` | A named block of a runbook in the repo. Lines 58-63 refuse to run unless the runbook exists, is tracked (`git ls-files --error-unmatch`) and has no uncommitted changes (`git diff --quiet HEAD`). Line 59 checks the block name against `^[a-z0-9-]+$`. Lines 66-67 require the common block and the named block's END marker. | Same shape as the rule's `bash -c "$(…)"`, but the source is committed local text, not the network. This is the runner's intended mechanism ("blocks run from committed text only"). Caller arguments go in as positional `$@`, never spliced into the script. **No finding.** |
| common.sh:106-119 | `python3 - … <<'PY' … PY` | Quoted heredoc, so the script is static with no expansion. Paths are passed as argv. | Static script. **No finding.** |
| common.sh:172-181 | `python3 - "$DEFAULT_REG" <<'PY'` | Quoted heredoc, static. Reads the registry JSON file. | **No finding.** |
| common.sh:198 | `python3 -c '…' "$RUNNER_SETTINGS"` | Single-quoted literal. The path is passed as argv. | **No finding.** |
| common.sh:212, 255 | `python3 -c '…import score43…' "$SCRIPTS" ["$CASE"]` | Single-quoted literal. The values are argv. `$CASE` was checked against `^[a-z0-9-]+$` at line 208 and against the allowlist at lines 213-219. | **No finding.** |
| common.sh:134-136 | `python3 "$FREEZE_TOOLS/freeze_check.py" verify …` | A repo script with fixed flags. Values are argv. `${MANIFEST:+--manifest "$MANIFEST"}` adds one quoted argument. | **No finding.** |
| common.sh:162 | `python3 "$SCORE43" fingerprint --root "$RUNNER_PLUGIN"` | A repo script with argv. | **No finding.** |
| common.sh:99 | `git archive "$sha" plugins/vibe-check \| tar -x …` | `$sha` is checked against hex at line 92 and resolved with `rev-parse --verify` at line 93. The pipe feeds `tar`, not a shell. | Not an interpreter. **No finding.** (Tar extraction of our own `git archive` output goes into the runner directory.) |
| run_case.sh:19 | `source "$HERE/common.sh"` | The file next to the script. `HERE` is `cd "$(dirname "$0")" && pwd` (line 16). This is the committed layer the freeze manifest hashes. | Local, committed, identity-checked. **No finding.** |
| run_case.sh:25 | `exec > >(tee -a "$LOG") 2>&1` | Process substitution into `tee` for logging. | Not an interpreter, and no remote input. **No finding.** |

**Rule 1 result: no finding in either file, including the lines the scanner could not parse.**

## Rule 2: `bash.curl.security.curl-eval.curl-eval` (WARNING, CWE-95, confidence MEDIUM)

**What it detects.** This is a taint rule:
- sources: `$(curl ...)` and `` `curl ...` ``
- sink: `eval ...`

It fires when command-substitution output from `curl` flows, directly or through variables, into `eval`.

**The broader class reviewed.** Any `eval`. Any run-a-string sink (`bash -c`, `sh -c`, `source`/`.`, `exec` with a computed command, an unquoted `$var` used as the command word). Any command-substitution output that is later executed, whatever its origin, and whether it comes from files, the environment, or the tmux pane.

**`eval`:** none in either file.

**Run-a-string sinks and the data that reaches them:**

| File:line | Sink | Where the data comes from | Finding |
|---|---|---|---|
| common.sh:70 | `bash -c "$script"` | Committed runbook text, as described under Rule 1. No command substitution of external data. | **No finding.** |
| run_case.sh:19 | `source "$HERE/common.sh"` | A fixed relative file. | **No finding.** |
| common.sh:43 | `env_get` | Reads `KEY=VALUE` lines from `$ENV` with `sed` and prints the value. The comment states the file is "never sourced", and nothing sources or evals it. Values are used as data: `want` at line 145 is compared with `test`, and `PD` at run_case.sh:120 is used as a path. | **No finding.** |
| run_case.sh:27, 32, 47, 66, 70, 77, 98 | `$(pane)`, i.e. `tmux capture-pane` output | Screen text from the measured session, possibly influenced by the model. It is only ever grepped, compared (`test "$P" = "$P2"`) or printed (`die`). It never reaches a sink. | **No finding.** |
| run_case.sh:30-38 | `pick`: `tmux send-keys -t "$S" "$n"` | `n` is extracted from pane text by the sed capture group `([0-9]+)`, so it is digits only, and only when the label matches exactly once (lines 35-36). Typing digits into the TUI is the intended keystroke. | Keystroke injection is limited to a digit string. **No finding.** |
| run_case.sh:57, 60, 108 | `tmux send-keys` with literals `'/clear'`, `'/vibe-check:deep-review'`, `C-u`, `'/exit'`, `Down`, `Enter` | Static. | **No finding.** |
| run_case.sh:106 | `NVW=$(grep -oE '[0-9]+ weak …' "$REPO/$RD/…/transcript.jsonl" … \| awk '{print $1}')` | Only digits are extracted from the transcript, and the value is only echoed (line 107). | **No finding.** |
| run_case.sh:112-115 | `CP=$(sed -n 's/^source_repo: ~\///p' "$REPO/docs/design/"*/{diffs,cases}/"$CASE.provenance" …)` then `rm "$H/.planning/HANDOFF.json"` | `CP` comes from committed provenance files and is used as a path component. The `rm` targets one fixed file name, only if it exists and git does not track it. Nothing is executed. | Path use only. **No finding.** (The value is not validated here. It comes from provenance files that `sidecar` checks against the seal elsewhere, but this function does not call `sidecar`.) |
| run_case.sh:118-122 | `M="$(proj_dir …)/memory"`, `PD=$(sed … park.env)`, `mv "$M" "$PD/…"` | Data used only as paths, quoted. | **No finding.** |
| common.sh:209-212, 248-251, 259-267 | Command substitution of `git show` / `python3` output into variables | Committed blobs and repo code. The values are compared or validated against strict regexes at lines 268-278 before use as paths. None is executed. | **No finding.** |

**Rule 2 result: no `eval` and no flow from external or network data into any execution sink. No finding.**

## Rule 3: `bash.lang.security.ifs-tampering.ifs-tampering` (WARNING, CWE-20, confidence LOW)

**What it detects.** The pattern is `IFS=...`, meaning any assignment to the shell's field-separator variable, global or command-prefix. The rule's message recommends `cut`/`awk` for splitting, or a local `IFS=... read`.

**The broader class reviewed.** Any assignment, export, `local` or `unset` of IFS. Any `read` with field splitting. Any `set --` re-splitting.

| File | IFS assignments | `read` | Splitting mechanism actually used |
|---|---|---|---|
| run_case.sh | none | none | `awk -F'\|'` (line 34, as the rule recommends) and `grep`/`sed`. `for i in $(seq 1 12)` / `$(seq 1 20)` / `$(seq 1 120)` rely on default IFS for integer lists. |
| common.sh | none | none | `tr ' ' '\n'` (line 154), `sed`, `awk`, `grep`. `CLONES` (line 37) is a space-separated default; it is never word-split anywhere in this file. |

Line by line: neither file contains `IFS` at all, in an assignment, an export, a `local` or anywhere else. Neither uses `read` or `set --`.

**Rule 3 result: no finding.**

## Unparsed spans of common.sh, reviewed individually

| Lines | Content | Rules 1-3 constructs |
|---|---|---|
| 29 | `case "$MANIFEST" in '' \| /*) ;; *) MANIFEST=$REPO/$MANIFEST ;; esac` | none |
| 57 | `case "$book" in /*) ;; *) book=$REPO/$book ;; esac` | none |
| 188-213 | the end of `isolation_check_owner` (case on cache path, `grep -qF` of the owner config), `isolation_check` (`python3 -c` literal at line 198, see Rule 1), and the start of `check_case` (CASE regex, `git show … \| grep`, `python3 -c` literal at line 212) | only the static `python3 -c` literals, already judged: no finding |
| 222 | `case "${RUN:-}" in [1-9]) ;; …` | none |
| 238 | `case "$CASE" in reach-new-*) ROLE=catch ;; *) ROLE=quiet ;; esac` | none |

The parser stops at `case` patterns. Bash itself accepts the file (`bash -n` clean for run_case.sh). This is a gap in semgrep's grammar, not a defect in the scripts.

## Conclusion for the owner's decision

- Against the actual definitions of the 3 bash rules, a full manual review of both files finds **no instance** of any rule, and nothing else in the class of risk they target. There are no network fetches, no `eval`, no IFS changes, and no flow from external or session-controlled data into an execution sink.
- Coverage is still missing, and that is stated plainly here: the scanner did not check these lines and no clean scan exists for them. The gap is limited to 3 rules × `run_case.sh` (whole file) and 3 rules × 5 spans of `common.sh`. Generic-language rules do not depend on the bash parser.
- Accepting this review in place of scanner coverage is a gate change, and it is the owner's call.
- Scope: candidate 24c0c00 only. Any change to either file needs a fresh review or a parsable form.
