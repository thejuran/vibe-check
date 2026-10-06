"""score43.py — scorer-of-record worksheet helper for the post-change measurement.

Mechanical parts only; AXIS is a recorded hand judgement. This module scripts
everything in the scoring ladder that needs no judgement — the completeness
ledger, the per-run false-alarm verdict, the catch-arm candidate rows, the Codex
status per run, the exact-fraction aggregate, the failed-diff list and the
retune ordering gate — so the numbers of record are reproducible from committed
files. Whether a candidate row at the catch site names the mechanism (AXIS) is
NOT computed here: the owner's hand verdicts arrive as a CATCH|MISS map and are
the only way the catch arm enters the aggregate.

Evidence rules:

* Bands are read from the archived `state.json` (`passes[-1].findings[].band`),
  never recomputed (D-00a). A run fires iff any surviving row is critical or
  warning (D-08).
* Denominators come from the sealed pre-registration blob (`633f1dd`,
  `DENOM_CATCH_RUNS` / `DENOM_QUIET_RUNS`) and are checked against the diff set.
* The verdict is decided on the CORRECTED quiet cohort: `QUIET_EXCLUDED`
  (should-quiet-7, SUPERSESSIONS-v2.10.md #001 — it carries a real config-loss
  defect) is removed, giving 18 quiet runs against a bar of 8, AND catches
  15 of 15 (D-00a2). The sealed-literal figure over all 21 quiet runs (bar 9) is
  always computed and printed beside the verdict and never decides. The
  excluded diff is never in the failed-diff list and never retune-eligible; the
  completeness ledger still expects it.
* No aggregation over holes or extras: every expected diff must have exactly
  run-1..3 scoreable and no other run may exist.
* Archive content is parsed as JSON data only — never imported or executed.

Output rule: `fp` and `aggregate` output carries agent / file / line / band /
score / stable_hash only (rendered through `replay.finding_row`). Finding
titles appear ONLY in `catch-candidates` output, which exists so the owner can
make the AXIS call.

Imports exactly {argparse, json, os, re, subprocess, sys} plus the sibling
`replay`; every git call carries a 120-second timeout.

    python3 score43.py ledger --runs-root R [--expected-diffs PATH]
    python3 score43.py fp --state PATH
    python3 score43.py catch-candidates --state PATH --diff D [--manifest PATH]
    python3 score43.py codex-status --state PATH
    python3 score43.py aggregate --runs-root R --label first|retune|combined|retune-full
        [--profile phase43|phase49] --fp-bar 8 --sealed-fp-bar 9 --catch-bar 15
        --catch-verdicts PATH [--expected-diffs PATH]
        [--first-root R1 --retune-root R2 --failed-diffs PATH]
        [--denoms-blob SHA] --verdict-out PATH
    python3 score43.py aggregate --profile phase49 --fp-bar 3 --sealed-fp-bar 6 --catch-bar 15 ...
    python3 score43.py failed-diffs --runs-root R --out PATH [--catch-verdicts PATH]
    python3 score43.py retune-gate --repo DIR --s S --s2 S2 --failed-diffs PATH
        --last-first-commit SHA [--first-root R1 --retune-root R2] [--cohort failed|full]
    python3 score43.py headline-check [--profile phase43|phase49] --results PATH --verdict PATH

Profiles (`PROFILES`): each names its pinned bar triple, the headline H1 and
before-values the headline grammar is checked against, the aggregate labels it
allows and the label a `Retune: used` headline must bind to. `phase43` is the
default and is the Phase-43 behaviour unchanged. Under `phase49` a retune is
scored only as `retune-full`: all 12 diffs x run-1..3 on the retune root decide
the verdict alone, and the first pass is carried beside it as `untuned` (no
mixed-snapshot combine).

`--catch-verdicts` is a JSON object {"<catch diff>/run-<n>": "CATCH"|"MISS"} with
exactly one entry per expected catch run. `--expected-diffs` / `--failed-diffs`
are JSON lists of diff names. `retune-gate` without `--first-root` and
`--retune-root` is the PRE-RUN form: ancestry, allowlist and frozen-file checks
only, the ledger skipped.
In both forms a non-allowlisted S..S2 path is tolerated only when it is
runbook tooling (PRE_VERDICT_TOOLING) whose blob is unchanged from the
FAILED-DIFFS first commit to S2; each one is printed as a pre-verdict tooling
change.

Exit 0 clean / 1 gate failure / 2 usage error or unreadable input.
"""

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import replay  # noqa: E402  (sibling module: run-dir rule, site/band helpers, row projection)

# D-02 order.
DIFFS = (
    "triggarr-secret-in-logs", "triggarr-autoescape", "third-organic-should-catch",
    "should-quiet-1", "should-quiet-2", "should-quiet-3",
    "triggarr-session-rotation", "triggarr-settings-form-split",
    "should-quiet-4", "should-quiet-5", "should-quiet-6", "should-quiet-7",
)
CATCH_DIFFS = ("triggarr-secret-in-logs", "triggarr-autoescape",
               "third-organic-should-catch", "triggarr-session-rotation",
               "triggarr-settings-form-split")
ROLE = {d: ("catch" if d in CATCH_DIFFS else "quiet") for d in DIFFS}
# D-00a2 / SUPERSESSIONS-v2.10.md #001. A module constant, never a flag: no
# invocation can widen or shrink the exclusion.
QUIET_EXCLUDED = ("should-quiet-7",)
RUN_NUMBERS = (1, 2, 3)

# Named measurement profiles. Each pins its own bar triple (corrected cohort
# deciding bar, sealed-literal bar that never decides, catch bar), the headline
# grammar it is transcribed under, the aggregate labels it allows and the label
# a "Retune: used" headline must bind to.
PROFILES = {
    "phase43": {"fp_bar": 8, "sealed_fp_bar": 9, "catch_bar": 15,
                "h1": "# B3 v2.10 — Phase 43",
                "fp_before": 16, "sealed_before": 19, "catch_before": 15,
                "labels": ("first", "retune", "combined"),
                "retune_label": "combined"},
    "phase49": {"fp_bar": 3, "sealed_fp_bar": 6, "catch_bar": 15,
                "h1": "# B3 v2.11 — Phase 49",
                "fp_before": 3, "sealed_before": 6, "catch_before": 15,
                "labels": ("first", "retune-full"),
                "retune_label": "retune-full"},
}
DEFAULT_PROFILE = "phase43"

FP_BAR = PROFILES["phase43"]["fp_bar"]                 # corrected cohort, deciding
SEALED_FP_BAR = PROFILES["phase43"]["sealed_fp_bar"]   # sealed literal, never deciding
CATCH_BAR = PROFILES["phase43"]["catch_bar"]
CORRECTED_QUIET_DENOM = 18

SEAL_COMMIT = "633f1dd"
PREREG_REL = "docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md"
_DENOM_RE = {k: re.compile(r"^%s: ([0-9]+)[ \t]*$" % k, re.MULTILINE)
             for k in ("DENOM_CATCH_RUNS", "DENOM_QUIET_RUNS")}

# D-05: the scorer is frozen across a retune; only prompt surfaces may change.
FROZEN_FILES = (
    "plugins/vibe-check/scripts/score.py",
    "plugins/vibe-check/scripts/config.py",
    "plugins/vibe-check/scripts/codex_translate.py",
    "plugins/vibe-check/scripts/codex_gate.py",
    "plugins/vibe-check/templates/scoring.md",
)
RETUNE_ALLOWLIST = (
    re.compile(r"^plugins/vibe-check/agents/[^/]+\.md$"),
    re.compile(r"^plugins/vibe-check/templates/codex-focus\.txt$"),
    re.compile(r"^plugins/vibe-check/scripts/test_agent_prompts\.py$"),
    re.compile(r"^plugins/vibe-check/docs/efficacy/RESULTS-v2\.10\.md$"),
)

# Runbook/scoring tooling the measured plugin never loads (no agent, command,
# phase or template references it; the runbook runs it from the repo, not the
# snapshot). A first-pass kit fix to one of these lands between S and the
# FAILED-DIFFS commit, so it shows up in S..S2 without being part of the
# retune. It is tolerated ONLY when its blob at S2 equals its blob at the
# FAILED-DIFFS first commit: the change predates the verdict and the retune
# did not touch it. Any other non-allowlisted path still fails.
PRE_VERDICT_TOOLING = (
    re.compile(r"^plugins/vibe-check/scripts/(?:test_)?(?:lanearchive|score43|batchsnap)\.py$"),
)

SNAPSHOT_NOTE = ("snapshot commit is bound per run by the fingerprint batch-sha line "
                 "and checked by the scoring ladder, not by this tool")

_CATCH_VALUES = ("CATCH", "MISS")


class ScoreError(ValueError):
    """A gate refusal (exit 1): holes, extras, a bad hand map, a failed check."""


def _key(diff, n):
    return "%s/run-%d" % (diff, n)


def _git(repo, *argv):
    return subprocess.run(["git", "-C", repo, *argv], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, timeout=120)


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _diff_list(obj, what):
    """A validated, D-02-ordered list of diff names from a JSON list."""
    if not isinstance(obj, list) or not obj:
        raise ScoreError("%s: must be a non-empty JSON list of diffs" % what)
    if any(not isinstance(d, str) or d not in DIFFS for d in obj):
        raise ScoreError("%s: names a diff outside the measured set" % what)
    if len(set(obj)) != len(obj):
        raise ScoreError("%s: repeats a diff" % what)
    return [d for d in DIFFS if d in obj]


# --------------------------------------------------------------------------- #
# Ledger
# --------------------------------------------------------------------------- #

def completeness_ledger(runs_root, expected_diffs=DIFFS):
    """Scoreable runs per expected diff; holes and extras; complete iff neither.

    A scoreable run is a `run-<N>` directory holding `state.json`. `run-N.failed-*`
    and `run-N.voided-*` siblings are listed as excluded. An extra is any
    scoreable run under a diff outside `expected_diffs`, or an N outside 1..3.
    """
    expected = _diff_list(list(expected_diffs), "expected diffs")
    per = {d: {"scoreable": [], "excluded": [], "holes": []} for d in expected}
    extras = []
    if os.path.isdir(runs_root):
        for diff in sorted(os.listdir(runs_root)):
            ddir = os.path.join(runs_root, diff)
            if not os.path.isdir(ddir):
                continue
            for name in sorted(os.listdir(ddir)):
                rdir = os.path.join(ddir, name)
                if not os.path.isdir(rdir) or not name.startswith("run-"):
                    continue
                if not replay.RUN_DIR_RE.match(name):
                    if diff in per:
                        per[diff]["excluded"].append(name)
                    continue
                if not os.path.isfile(os.path.join(rdir, "state.json")):
                    continue
                n = int(name[len("run-"):])
                if diff in per and n in RUN_NUMBERS:
                    per[diff]["scoreable"].append(n)
                else:
                    extras.append("%s/%s" % (diff, name))
    holes = []
    for d in expected:
        per[d]["scoreable"].sort()
        per[d]["holes"] = [n for n in RUN_NUMBERS if n not in per[d]["scoreable"]]
        holes += [_key(d, n) for n in per[d]["holes"]]
    return {"runs_root": runs_root, "expected": expected, "diffs": per,
            "holes": holes, "extras": sorted(extras),
            "complete": not holes and not extras}


def _require_complete(ledger):
    if ledger["holes"]:
        raise ScoreError("holes present: " + ", ".join(ledger["holes"]))
    if ledger["extras"]:
        raise ScoreError("extras present: " + ", ".join(ledger["extras"]))


def _load_states(ledger):
    out = {}
    for d in ledger["expected"]:
        for n in RUN_NUMBERS:
            out[_key(d, n)] = _read_json(os.path.join(
                ledger["runs_root"], d, "run-%d" % n, "state.json"))
    return out


# --------------------------------------------------------------------------- #
# Per-run verdicts
# --------------------------------------------------------------------------- #

def _last_pass(state):
    passes = state.get("passes") if isinstance(state, dict) else None
    if not isinstance(passes, list) or not passes or not isinstance(passes[-1], dict):
        raise ValueError("state has no passes")
    return passes[-1]


def _findings(state):
    return [f for f in _last_pass(state).get("findings") or [] if isinstance(f, dict)]


def fp_verdict(state):
    """D-08: a run is one false alarm iff any surviving row is critical/warning.
    Bands are read from the state, never recomputed."""
    findings = _findings(state)
    rows = [{"agent": f.get("agent"), "file": f.get("file"), "line": f.get("line"),
             "band": f.get("band"), "score": f.get("orchestrator_score"),
             "stable_hash": f.get("stable_hash")}
            for f in findings if f.get("band") in ("critical", "warning")]
    return {"fired": replay.fires({"findings": findings}), "count": len(rows), "rows": rows}


def catch_candidates(state, entry):
    """Rows at the catch SITE with BAND >= floor, with their own and their
    members' titles, for the owner's hand AXIS call. This is the ONLY function
    in this module that emits titles; the AXIS column is left blank."""
    floor = replay.rank(entry.get("floor"))
    out = []
    for f in replay.rows_at_site({"findings": _findings(state)}, entry.get("site")):
        if replay.rank(f.get("band")) < floor:
            continue
        members = f.get("members") if isinstance(f.get("members"), list) else []
        out.append({"agent": f.get("agent"), "file": f.get("file"), "line": f.get("line"),
                    "band": f.get("band"), "score": f.get("orchestrator_score"),
                    "stable_hash": f.get("stable_hash"),
                    "survivor_title": f.get("title"),
                    "member_titles": [[m.get("agent"), m.get("title")]
                                      for m in members if isinstance(m, dict)],
                    "axis": ""})
    return out


def codex_status(state):
    """passes[-1].codex status/reason; dropout iff status != joined. The count of
    surviving codex-agent rows is reported as a cross-check only."""
    codex = _last_pass(state).get("codex")
    codex = codex if isinstance(codex, dict) else {}
    status, reason = codex.get("status"), codex.get("reason")
    return {"status": status, "reason": reason,
            "codex_findings": sum(1 for f in _findings(state)
                                  if f.get("agent") == replay.CODEX_AGENT),
            "dropout": status != "joined"}


def _site_entry(diff, manifest_path=None):
    manifest = replay.load_manifest(path=manifest_path)
    entries = {(json.dumps(e.get("site"), sort_keys=True), e.get("floor"))
               for e in (manifest.get("catch_runs") or {}).values()
               if isinstance(e, dict) and e.get("diff") == diff}
    if len(entries) != 1:
        raise ScoreError("catch-candidates: manifest has %d site entries for the diff"
                         % len(entries))
    site, floor = entries.pop()
    return {"site": json.loads(site), "floor": floor}


# --------------------------------------------------------------------------- #
# Hand map, denominators, aggregate
# --------------------------------------------------------------------------- #

def _expected_catch_runs(expected):
    return [_key(d, n) for d in expected if ROLE[d] == "catch" for n in RUN_NUMBERS]


def check_catch_verdicts(verdicts, expected):
    """The hand AXIS map must carry exactly one CATCH|MISS per expected catch run."""
    if not isinstance(verdicts, dict):
        raise ScoreError("catch-verdicts: not a JSON object")
    want = _expected_catch_runs(expected)
    unknown = sorted(k for k in verdicts if k not in want)
    if unknown:
        raise ScoreError("catch-verdicts: unknown run key %s" % ", ".join(unknown))
    missing = [k for k in want if k not in verdicts]
    if missing:
        raise ScoreError("catch-verdicts: %d entries, %d expected (missing %s)"
                         % (len(verdicts), len(want), ", ".join(missing)))
    bad = sorted(k for k, v in verdicts.items() if v not in _CATCH_VALUES)
    if bad:
        raise ScoreError("catch-verdicts: value is not CATCH or MISS for %s" % ", ".join(bad))
    return dict(verdicts)


def parse_denoms(text):
    out = {}
    for k, rx in _DENOM_RE.items():
        found = rx.findall(text)
        if len(found) != 1:
            raise ScoreError("sealed denominators: %s appears %d times" % (k, len(found)))
        out[k] = int(found[0])
    return out


def check_denoms(denoms):
    n_catch = sum(1 for d in DIFFS if ROLE[d] == "catch")
    n_quiet = len(DIFFS) - n_catch
    if denoms.get("DENOM_CATCH_RUNS") != 3 * n_catch:
        raise ScoreError("sealed DENOM_CATCH_RUNS != 3 x %d catch diffs" % n_catch)
    if denoms.get("DENOM_QUIET_RUNS") != 3 * n_quiet:
        raise ScoreError("sealed DENOM_QUIET_RUNS != 3 x %d quiet diffs" % n_quiet)
    corrected = denoms["DENOM_QUIET_RUNS"] - 3 * len(QUIET_EXCLUDED)
    if corrected != CORRECTED_QUIET_DENOM:
        raise ScoreError("corrected quiet denominator %d != %d"
                         % (corrected, CORRECTED_QUIET_DENOM))
    return denoms


def load_denoms(blob=SEAL_COMMIT, repo=replay.REPO_ROOT):
    """Denominators from the sealed pre-registration (`<commit>` or `<rev>:<path>`)."""
    spec = blob if ":" in blob else "%s:%s" % (blob, PREREG_REL)
    proc = _git(repo, "show", spec)
    if proc.returncode != 0:
        raise ScoreError("sealed denominators: git show failed for the seal blob")
    return check_denoms(parse_denoms(proc.stdout))


def _per_diff(expected, fp, catch, codex):
    out = {}
    for d in expected:
        keys = [_key(d, n) for n in RUN_NUMBERS]
        row = {"role": ROLE[d],
               "dropouts": sum(1 for k in keys if codex[k]["dropout"]),
               "codex": [codex[k]["status"] for k in keys]}
        if ROLE[d] == "quiet":
            row["fired"] = [fp[k]["fired"] for k in keys]
            row["fired_count"] = "%d/3" % sum(row["fired"])
        else:
            row["catch"] = [catch[k] for k in keys]
            row["catch_count"] = "%d/3" % sum(1 for v in row["catch"] if v == "CATCH")
        out[d] = row
    return out


def aggregate(ledger, fp_verdicts, catch_verdicts, denoms, fp_bar=FP_BAR,
              sealed_fp_bar=SEALED_FP_BAR, catch_bar=CATCH_BAR, label="first",
              codex=None, untuned=None):
    """Exact-fraction aggregate. `first`/`combined`/`retune-full` decide
    PASS|MISS on the corrected cohort and carry the sealed literal beside it;
    `retune` is the per-diff subset record with no headline and no verdict.
    `combined` and `retune-full` also carry the untuned first-pass triple."""
    _require_complete(ledger)
    check_denoms(denoms)
    expected = ledger["expected"]
    catch = check_catch_verdicts(catch_verdicts, expected)
    codex = codex or {k: {"status": None, "dropout": True} for k in fp_verdicts}
    per_diff = _per_diff(expected, fp_verdicts, catch, codex)
    dropouts = {d: per_diff[d]["dropouts"] for d in expected}
    if label == "retune":
        if any(d in QUIET_EXCLUDED for d in expected):
            raise ScoreError("retune: an excluded diff is never retune-eligible")
        return {"label": "retune", "expected_diffs": expected, "runs": 3 * len(expected),
                "per_diff": per_diff, "dropouts": dropouts,
                "snapshot_commit_note": SNAPSHOT_NOTE}
    if label not in ("first", "combined", "retune-full"):
        raise ScoreError("unknown label")
    if list(expected) != list(DIFFS):
        raise ScoreError("%s: the headline needs all %d diffs" % (label, len(DIFFS)))
    quiet = [d for d in DIFFS if ROLE[d] == "quiet"]
    counted = [d for d in quiet if d not in QUIET_EXCLUDED]

    def fired(diffs):
        return sum(1 for d in diffs for n in RUN_NUMBERS if fp_verdicts[_key(d, n)]["fired"])

    corrected, sealed = fired(counted), fired(quiet)
    hit = sum(1 for v in catch.values() if v == "CATCH")
    quiet_denom = denoms["DENOM_QUIET_RUNS"] - 3 * len(QUIET_EXCLUDED)
    verdict = "PASS" if corrected <= fp_bar and hit >= catch_bar else "MISS"
    out = {
        "label": label,
        "verdict": verdict,
        "quiet_fired": corrected,
        "quiet_denominator": quiet_denom,
        "quiet_fraction": "%d/%d" % (corrected, quiet_denom),
        "quiet_excluded": list(QUIET_EXCLUDED),
        "excluded_runs": {d: [fp_verdicts[_key(d, n)]["fired"] for n in RUN_NUMBERS]
                          for d in QUIET_EXCLUDED},
        "sealed_literal": {
            "quiet_fired": sealed,
            "quiet_denominator": denoms["DENOM_QUIET_RUNS"],
            "fp_bar": sealed_fp_bar,
            "would_be": "PASS" if sealed <= sealed_fp_bar and hit >= catch_bar else "MISS",
        },
        "catch_hit": hit,
        "catch_denominator": denoms["DENOM_CATCH_RUNS"],
        "catch_fraction": "%d/%d" % (hit, denoms["DENOM_CATCH_RUNS"]),
        "fp_bar": fp_bar,
        "catch_bar": catch_bar,
        "per_diff": per_diff,
        "dropouts": dropouts,
        "snapshot_commit_note": SNAPSHOT_NOTE,
    }
    if label in ("combined", "retune-full"):
        if not isinstance(untuned, dict):
            raise ScoreError("%s: the untuned first-pass triple is required" % label)
        out["untuned"] = {"quiet_fired": untuned["quiet_fired"],
                          "sealed_quiet_fired": untuned["sealed_quiet_fired"],
                          "catch_hit": untuned["catch_hit"]}
    return out


def _headline_lines(result):
    lines = ["%s: %s — quiet fired %s (corrected cohort, bar <= %d; excluded: %s); "
             "catch %s (bar %d)" % (result["label"], result["verdict"],
                                    result["quiet_fraction"], result["fp_bar"],
                                    ", ".join(result["quiet_excluded"]),
                                    result["catch_fraction"], result["catch_bar"]),
             "sealed literal (never deciding): %d/%d vs <= %d/%d -> would be %s" % (
                 result["sealed_literal"]["quiet_fired"],
                 result["sealed_literal"]["quiet_denominator"],
                 result["sealed_literal"]["fp_bar"],
                 result["sealed_literal"]["quiet_denominator"],
                 result["sealed_literal"]["would_be"])]
    for d, flags in result["excluded_runs"].items():
        lines.append("%s (descriptive, excluded per #001): fired %d/3" % (d, sum(flags)))
    if "untuned" in result:
        u = result["untuned"]
        lines.append("untuned first pass: %d/%d, %d/%d, %d/%d" % (
            u["quiet_fired"], result["quiet_denominator"], u["sealed_quiet_fired"],
            result["sealed_literal"]["quiet_denominator"], u["catch_hit"],
            result["catch_denominator"]))
    return lines


# --------------------------------------------------------------------------- #
# Failed diffs and the retune gate
# --------------------------------------------------------------------------- #

def failed_diffs(per_run_verdicts):
    """D-06: diffs with >= 1 failed run, sorted, MINUS QUIET_EXCLUDED (D-00a2).
    `per_run_verdicts` maps "<diff>/run-<n>" to True when that run failed."""
    failed = {k.rsplit("/", 1)[0] for k, bad in per_run_verdicts.items() if bad}
    return sorted(d for d in failed if d not in QUIET_EXCLUDED)


def _per_run_failures(fp, catch):
    out = {}
    for k, v in fp.items():
        diff = k.rsplit("/", 1)[0]
        out[k] = v["fired"] if ROLE[diff] == "quiet" else catch.get(k) != "CATCH"
    return out


def _score_root(runs_root, expected, catch_path):
    ledger = completeness_ledger(runs_root, expected)
    _require_complete(ledger)
    states = _load_states(ledger)
    fp = {k: fp_verdict(s) for k, s in states.items()}
    codex = {k: codex_status(s) for k, s in states.items()}
    catch = check_catch_verdicts(_read_json(catch_path), ledger["expected"])
    return ledger, fp, codex, catch


def _rel_in_repo(repo, path):
    rel = os.path.relpath(os.path.realpath(path), os.path.realpath(repo))
    if rel.startswith(".."):
        raise ScoreError("retune-gate: FAILED-DIFFS is outside the repository")
    return rel.replace(os.sep, "/")


def _resolve(repo, rev, failures, what):
    proc = _git(repo, "rev-parse", "--verify", "--quiet", "%s^{commit}" % rev)
    if proc.returncode != 0:
        failures.append("%s does not resolve to a commit" % what)
        return None
    return proc.stdout.strip()


def _ancestor(repo, a, b):
    return _git(repo, "merge-base", "--is-ancestor", a, b).returncode == 0


def retune_gate(repo, s, s2, failed_diffs_path, first_root, retune_root,
                last_first_commit, notes=None, cohort="failed"):
    """Every D-05..D-07 ordering/scope check; returns the list of failures.

    `retune_root=None` is the PRE-RUN form: identical ancestry, allowlist and
    frozen-file checks, the ledger skipped. An empty checked set never passes.
    `cohort` picks the retune ledger's expected set in the full form: "failed"
    (the committed FAILED-DIFFS) or "full" (all diffs, the full-cohort retune).
    """
    failures = []
    if cohort not in ("failed", "full"):
        raise ScoreError("retune-gate: unknown cohort")
    s_sha = _resolve(repo, s, failures, "S")
    s2_sha = _resolve(repo, s2, failures, "S2")
    last_sha = _resolve(repo, last_first_commit, failures, "last first-pass commit")
    rel = _rel_in_repo(repo, failed_diffs_path)
    log = _git(repo, "log", "--format=%H", "--reverse", "--", rel)
    commits = log.stdout.split() if log.returncode == 0 else []
    if not commits:
        failures.append("FAILED-DIFFS is not committed")
        return failures
    if len(commits) > 1:
        failures.append("FAILED-DIFFS was rewritten after its first commit")
    f_sha = commits[0]
    committed = _git(repo, "show", "%s:%s" % (f_sha, rel))
    failed = None
    try:
        failed = _diff_list(json.loads(committed.stdout), "FAILED-DIFFS")
        if any(d in QUIET_EXCLUDED for d in failed):
            failures.append("FAILED-DIFFS names an excluded diff")
    except (ValueError, ScoreError):
        failures.append("FAILED-DIFFS (first commit) is not a valid non-empty diff list")
    if None in (s_sha, s2_sha, last_sha):
        return failures
    if s_sha == s2_sha:
        failures.append("S2 equals S (no retune commit)")
    if not _ancestor(repo, last_sha, f_sha):
        failures.append("ordering: last first-pass commit is not an ancestor of FAILED-DIFFS")
    if f_sha == s2_sha or not _ancestor(repo, f_sha, s2_sha):
        failures.append("ordering: FAILED-DIFFS does not strictly precede S2")
    if not _ancestor(repo, s_sha, s2_sha):
        failures.append("ordering: S is not an ancestor of S2")
    names = _git(repo, "diff", "--name-only", s_sha, s2_sha, "--", "plugins/vibe-check")
    changed = names.stdout.split("\n") if names.returncode == 0 else []
    changed = [p for p in changed if p]
    if not changed:
        failures.append("allowlist: S..S2 changes nothing under plugins/vibe-check")
    for p in changed:
        if any(rx.match(p) for rx in RETUNE_ALLOWLIST):
            continue
        if any(rx.match(p) for rx in PRE_VERDICT_TOOLING):
            a = _git(repo, "rev-parse", "--verify", "--quiet", "%s:%s" % (f_sha, p))
            b = _git(repo, "rev-parse", "--verify", "--quiet", "%s:%s" % (s2_sha, p))
            if a.returncode == 0 and b.returncode == 0 and a.stdout == b.stdout:
                if notes is not None:
                    notes.append("pre-verdict tooling change (not part of R): %s" % p)
                continue
        failures.append("allowlist: %s is outside the retune allowlist" % p)
    for p in FROZEN_FILES:
        a = _git(repo, "rev-parse", "--verify", "--quiet", "%s:%s" % (s_sha, p))
        b = _git(repo, "rev-parse", "--verify", "--quiet", "%s:%s" % (s2_sha, p))
        if a.returncode != 0 or b.returncode != 0 or a.stdout != b.stdout:
            failures.append("frozen: %s differs between S and S2" % p)
    if retune_root is None or failed is None:
        return failures
    ledger = completeness_ledger(retune_root, list(DIFFS) if cohort == "full" else failed)
    failures += ["ledger hole: " + h for h in ledger["holes"]]
    failures += ["ledger extra: " + e for e in ledger["extras"]]
    try:
        _l, fp, _c, catch = _score_root(first_root, DIFFS,
                                        os.path.join(first_root, "CATCH-VERDICTS.json"))
        if failed_diffs(_per_run_failures(fp, catch)) != sorted(failed):
            failures.append("FAILED-DIFFS differs from the first-pass verdicts")
    except (OSError, ValueError) as exc:
        failures.append("first-pass root unscoreable: %s" % (
            exc if isinstance(exc, ScoreError) else type(exc).__name__))
    return failures


# --------------------------------------------------------------------------- #
# Headline check
# --------------------------------------------------------------------------- #

_PHASE43_H1 = PROFILES["phase43"]["h1"]


def _deciding_re(prof):
    n = lambda k: re.escape(str(prof[k]))  # noqa: E731
    return re.compile(
        r"^\*\*(PASS|MISS)\*\* — false alarms " + n("fp_before") + r"→([0-9]+) of 18 "
        r"\(corrected cohort, bar ≤ " + n("fp_bar") + r"; "
        r"should-quiet-7 excluded per SUPERSESSIONS-v2\.10\.md #001\); "
        r"catches " + n("catch_before") + r"→([0-9]+) of 15 \(bar " + n("catch_bar") + r"\)",
        re.MULTILINE)


def _sealed_re(prof):
    return re.compile(r"^Sealed literal \(never deciding\): false alarms "
                      + re.escape(str(prof["sealed_before"])) + r"→([0-9]+) of 21",
                      re.MULTILINE)


_DECIDING_RE = _deciding_re(PROFILES["phase43"])
_SEALED_RE = _sealed_re(PROFILES["phase43"])
_RETUNE_RE = re.compile(r"^Retune: (not used|used)\b", re.MULTILINE)
_UNTUNED_RE = re.compile(r"untuned first pass: ([0-9]+)/18, ([0-9]+)/21, ([0-9]+)/15")


def _headline_block(text, h1=_PHASE43_H1):
    starts = [m.start() for m in re.finditer(r"^%s" % re.escape(h1), text, re.MULTILINE)]
    if not starts:
        return None
    section = text[starts[-1]:]
    m = re.search(r"^## Headline[ \t]*$", section, re.MULTILINE)
    if not m:
        return None
    rest = section[m.end():]
    nxt = re.search(r"^#{1,2} ", rest, re.MULTILINE)
    return rest[:nxt.start()] if nxt else rest


def headline_check(results_path, verdict_path, profile=DEFAULT_PROFILE):
    """Field names whose headline transcription disagrees with the artifact ([] = match)."""
    prof = PROFILES[profile]
    with open(results_path, encoding="utf-8") as fh:
        text = fh.read()
    art = _read_json(verdict_path)
    if not isinstance(art, dict):
        raise ValueError("verdict artifact is not an object")
    block = _headline_block(text, prof["h1"])
    if block is None:
        return ["headline-block"]
    bad = []
    if (art.get("fp_bar"), art.get("catch_bar"),
            (art.get("sealed_literal") or {}).get("fp_bar")) != (
                prof["fp_bar"], prof["catch_bar"], prof["sealed_fp_bar"]):
        bad.append("bars")
    dec = _deciding_re(prof).findall(block)
    sealed = _sealed_re(prof).findall(block)
    retune = _RETUNE_RE.findall(block)
    if len(dec) != 1:
        bad.append("deciding-line")
    else:
        v, x, y = dec[0]
        if v != art.get("verdict"):
            bad.append("verdict")
        if int(x) != art.get("quiet_fired"):
            bad.append("quiet_fired")
        if int(y) != art.get("catch_hit"):
            bad.append("catch_hit")
    if len(sealed) != 1:
        bad.append("sealed-line")
    elif int(sealed[0]) != (art.get("sealed_literal") or {}).get("quiet_fired"):
        bad.append("sealed_literal.quiet_fired")
    if len(retune) != 1:
        bad.append("retune-line")
        return bad
    if retune[0] == "not used":
        if art.get("label") != "first":
            bad.append("label")
    else:
        if art.get("label") != prof["retune_label"]:
            bad.append("label")
        trip = _UNTUNED_RE.findall(block)
        u = art.get("untuned") if isinstance(art.get("untuned"), dict) else {}
        if len(trip) != 1:
            bad.append("untuned-line")
        elif tuple(int(t) for t in trip[0]) != (u.get("quiet_fired"),
                                                 u.get("sealed_quiet_fired"),
                                                 u.get("catch_hit")):
            bad.append("untuned")
    return bad


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _render_rows(rows):
    out = ["| agent | file | line | band | score | stable_hash |", "|---|---|---|---|---|---|"]
    for r in rows:
        out.append(replay.finding_row({"agent": r["agent"], "file": r["file"],
                                        "line": r["line"], "band": r["band"],
                                        "orchestrator_score": r["score"],
                                        "stable_hash": r["stable_hash"]}))
    return out


def _emit(lines):
    text = "\n".join(lines)
    if '"title"' in text or "<result>" in text:
        raise ScoreError("output refused: forbidden token in output text")
    print(text)


def _cmd_ledger(runs_root, expected_path):
    expected = _diff_list(_read_json(expected_path), "expected diffs") if expected_path else DIFFS
    ledger = completeness_ledger(runs_root, expected)
    for d in ledger["expected"]:
        e = ledger["diffs"][d]
        print("%s: scoreable %s%s" % (d, e["scoreable"],
                                      " excluded %s" % e["excluded"] if e["excluded"] else ""))
    if not ledger["complete"]:
        if ledger["holes"]:
            print("holes: " + ", ".join(ledger["holes"]), file=sys.stderr)
        if ledger["extras"]:
            print("extras: " + ", ".join(ledger["extras"]), file=sys.stderr)
        return 1
    print("ledger complete: %d diffs x 3, no holes, no extras" % len(ledger["expected"]))
    return 0


def _cmd_fp(state_path):
    v = fp_verdict(_read_json(state_path))
    _emit(["fired: %s (%d critical/warning rows)" % (v["fired"], v["count"])]
          + _render_rows(v["rows"]))
    return 0


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def _cmd_catch_candidates(state_path, diff, manifest_path):
    if ROLE.get(diff) != "catch":
        raise ScoreError("catch-candidates: not a catch diff")
    rows = catch_candidates(_read_json(state_path), _site_entry(diff, manifest_path))
    print("| agent | file | line | band | score | stable_hash | survivor title | member titles | AXIS |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        members = "; ".join("%s: %s" % (agent, t) for agent, t in r["member_titles"])
        h = r["stable_hash"]
        print("| %s |" % " | ".join(_cell(v) for v in (
            r["agent"], r["file"], r["line"], r["band"], r["score"],
            h[:12] if isinstance(h, str) else h, r["survivor_title"], members, "")))
    print("candidates at site with band >= floor: %d" % len(rows))
    return 0


def _cmd_codex_status(state_path):
    c = codex_status(_read_json(state_path))
    print("codex.status=%s reason=%s codex_findings=%d dropout=%s" % (
        c["status"], c["reason"] if c["reason"] is not None else "null",
        c["codex_findings"], "yes" if c["dropout"] else "no"))
    return 0


def _write_verdict(path, result):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _untuned_from_first(first_root, denoms, label, require_recorded=False):
    """The untuned first-pass triple recomputed from the first-pass runs, and
    cross-checked against <first_root>/VERDICT.json (label "first")."""
    first = completeness_ledger(first_root, DIFFS)
    _require_complete(first)
    f_states = _load_states(first)
    u_fp = {k: fp_verdict(s) for k, s in f_states.items()}
    u_codex = {k: codex_status(s) for k, s in f_states.items()}
    first_catch = os.path.join(first_root, "CATCH-VERDICTS.json")
    u_res = aggregate(first, u_fp, _read_json(first_catch), denoms, label="first",
                      codex=u_codex)
    untuned = {"quiet_fired": u_res["quiet_fired"],
               "sealed_quiet_fired": u_res["sealed_literal"]["quiet_fired"],
               "catch_hit": u_res["catch_hit"]}
    recorded = os.path.join(first_root, "VERDICT.json")
    if os.path.exists(recorded):
        rec = _read_json(recorded)
        if not isinstance(rec, dict) or (
                rec.get("label"), rec.get("quiet_fired"),
                (rec.get("sealed_literal") or {}).get("quiet_fired"),
                rec.get("catch_hit")) != ("first", untuned["quiet_fired"],
                                          untuned["sealed_quiet_fired"],
                                          untuned["catch_hit"]):
            raise ScoreError("%s: first-pass VERDICT.json disagrees with the "
                             "first-pass runs" % label)
    elif require_recorded:
        raise ScoreError("%s: the first-pass VERDICT.json is missing" % label)
    return first, f_states, untuned


def _cmd_aggregate(args):
    prof = PROFILES[args.profile]
    if args.label not in prof["labels"]:
        raise ScoreError("label %s is not allowed under profile %s" % (args.label, args.profile))
    bars = (prof["fp_bar"], prof["sealed_fp_bar"], prof["catch_bar"])
    if (args.fp_bar, args.sealed_fp_bar, args.catch_bar) != bars:
        raise ScoreError("bars must be --fp-bar %d --sealed-fp-bar %d --catch-bar %d" % bars)
    bar_kw = {"fp_bar": bars[0], "sealed_fp_bar": bars[1], "catch_bar": bars[2]}
    denoms = load_denoms(args.denoms_blob or SEAL_COMMIT)
    catch_map = _read_json(args.catch_verdicts)
    combined_flags = (args.first_root, args.retune_root, args.failed_diffs)
    if args.label == "retune-full":
        if args.retune_root is not None or args.failed_diffs is not None:
            raise ScoreError("retune-full refuses --retune-root/--failed-diffs "
                             "(the retune root is --runs-root; every diff is re-run)")
        if not args.runs_root:
            raise ScoreError("retune-full needs --runs-root (the full-cohort retune root)")
        if not args.first_root:
            raise ScoreError("retune-full needs --first-root (the first-pass root)")
        if args.expected_diffs and _diff_list(_read_json(args.expected_diffs),
                                              "expected diffs") != list(DIFFS):
            raise ScoreError("retune-full: the expected set is all %d diffs" % len(DIFFS))
        ledger = completeness_ledger(args.runs_root, DIFFS)
        _require_complete(ledger)
        _f, _fs, untuned = _untuned_from_first(args.first_root, denoms, "retune-full",
                                               require_recorded=True)
        states = _load_states(ledger)
        fp = {k: fp_verdict(s) for k, s in states.items()}
        codex = {k: codex_status(s) for k, s in states.items()}
        result = aggregate(ledger, fp, catch_map, denoms, label="retune-full", codex=codex,
                           untuned=untuned, **bar_kw)
    elif args.label == "combined":
        if None in combined_flags:
            raise ScoreError("combined needs --first-root, --retune-root and --failed-diffs")
        failed = _diff_list(_read_json(args.failed_diffs), "failed diffs")
        if any(d in QUIET_EXCLUDED for d in failed):
            raise ScoreError("combined: an excluded diff is never retune-eligible")
        first = completeness_ledger(args.first_root, DIFFS)
        _require_complete(first)
        retune = completeness_ledger(args.retune_root, failed)
        _require_complete(retune)
        _f, f_states, untuned = _untuned_from_first(args.first_root, denoms, "combined")
        r_states = _load_states(retune)
        merged = dict(f_states)
        merged.update(r_states)  # D-07: the retuned diffs' runs replace their originals
        fp = {k: fp_verdict(s) for k, s in merged.items()}
        codex = {k: codex_status(s) for k, s in merged.items()}
        ledger = {"expected": list(DIFFS), "holes": [], "extras": []}
        result = aggregate(ledger, fp, catch_map, denoms, label="combined", codex=codex,
                           untuned=untuned, **bar_kw)
    else:
        if any(x is not None for x in combined_flags):
            raise ScoreError("--first-root/--retune-root/--failed-diffs are for combined only")
        if not args.runs_root:
            raise ScoreError("%s needs --runs-root" % args.label)
        if args.label == "retune":
            if not args.expected_diffs:
                raise ScoreError("retune needs --expected-diffs (the committed FAILED-DIFFS)")
            expected = _diff_list(_read_json(args.expected_diffs), "expected diffs")
        else:
            expected = list(DIFFS)
            if args.expected_diffs and _diff_list(_read_json(args.expected_diffs),
                                                  "expected diffs") != expected:
                raise ScoreError("first: the expected set is all %d diffs" % len(DIFFS))
        ledger = completeness_ledger(args.runs_root, expected)
        _require_complete(ledger)
        states = _load_states(ledger)
        fp = {k: fp_verdict(s) for k, s in states.items()}
        codex = {k: codex_status(s) for k, s in states.items()}
        result = aggregate(ledger, fp, catch_map, denoms, label=args.label, codex=codex,
                           **bar_kw)
    lines = []
    if result["label"] == "retune":
        for d, row in result["per_diff"].items():
            lines.append("%s (%s): %s, dropouts %d" % (
                d, row["role"], row.get("fired_count") or row.get("catch_count"),
                row["dropouts"]))
        lines.append("retune subset: %d runs over %d diffs (no headline; see combined)"
                     % (result["runs"], len(result["expected_diffs"])))
    else:
        lines += _headline_lines(result)
        lines.append("dropouts: " + ", ".join("%s %d" % (d, n)
                                              for d, n in result["dropouts"].items()))
        for k in sorted(fp):
            if ROLE[k.rsplit("/", 1)[0]] == "quiet" and fp[k]["fired"]:
                lines += ["", "fired: " + k] + _render_rows(fp[k]["rows"])
    _emit(lines)
    _write_verdict(args.verdict_out, result)
    return 0


def _cmd_failed_diffs(runs_root, out_path, catch_path):
    if os.path.lexists(out_path):
        raise ScoreError("ALREADY WRITTEN: refusing to overwrite FAILED-DIFFS")
    _l, fp, _c, catch = _score_root(runs_root, DIFFS, catch_path
                                    or os.path.join(runs_root, "CATCH-VERDICTS.json"))
    per_run = _per_run_failures(fp, catch)
    failed = failed_diffs(per_run)
    for d in QUIET_EXCLUDED:
        if any(per_run[_key(d, n)] for n in RUN_NUMBERS):
            print("excluded from retune eligibility: %s" % d)
    if not failed:
        raise ScoreError("no failed diffs: nothing to retune, FAILED-DIFFS not written")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(failed, fh)
        fh.write("\n")
    print("failed diffs: " + ", ".join(failed))
    return 0


def _cmd_retune_gate(args):
    notes = []
    failures = retune_gate(args.repo, args.s, args.s2, args.failed_diffs, args.first_root,
                           args.retune_root, args.last_first_commit, notes=notes,
                           cohort=args.cohort)
    for n in notes:
        print("retune-gate: " + n)
    for f in failures:
        print("retune-gate FAIL: " + f, file=sys.stderr)
    if failures:
        return 1
    if args.retune_root is None:
        print("retune-gate: pre-run form (ledger skipped)")
    print("retune-gate: PASS")
    return 0


def _cmd_headline_check(results_path, verdict_path, profile=DEFAULT_PROFILE):
    bad = headline_check(results_path, verdict_path, profile)
    if bad:
        print("headline-check mismatch: " + ", ".join(bad), file=sys.stderr)
        return 1
    print("headline-check: match")
    return 0


def _parser():
    parser = argparse.ArgumentParser(
        prog="score43.py", description="Phase-43 scorer-of-record worksheet helper "
                                       "(see module docstring).")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("ledger")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--expected-diffs", default=None)
    p = sub.add_parser("fp")
    p.add_argument("--state", required=True)
    p = sub.add_parser("catch-candidates")
    p.add_argument("--state", required=True)
    p.add_argument("--diff", required=True)
    p.add_argument("--manifest", default=None)
    p = sub.add_parser("codex-status")
    p.add_argument("--state", required=True)
    p = sub.add_parser("aggregate")
    p.add_argument("--runs-root", default=None)
    p.add_argument("--label", required=True,
                   choices=("first", "retune", "combined", "retune-full"))
    p.add_argument("--profile", choices=tuple(PROFILES), default=DEFAULT_PROFILE)
    p.add_argument("--fp-bar", type=int, required=True)
    p.add_argument("--sealed-fp-bar", type=int, required=True)
    p.add_argument("--catch-bar", type=int, required=True)
    p.add_argument("--catch-verdicts", required=True)
    p.add_argument("--expected-diffs", default=None)
    p.add_argument("--first-root", default=None)
    p.add_argument("--retune-root", default=None)
    p.add_argument("--failed-diffs", default=None)
    p.add_argument("--denoms-blob", default=None)
    p.add_argument("--verdict-out", required=True)
    p = sub.add_parser("failed-diffs")
    p.add_argument("--runs-root", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--catch-verdicts", default=None)
    p = sub.add_parser("retune-gate")
    p.add_argument("--repo", required=True)
    p.add_argument("--s", required=True)
    p.add_argument("--s2", required=True)
    p.add_argument("--failed-diffs", required=True)
    p.add_argument("--last-first-commit", required=True)
    p.add_argument("--first-root", default=None)
    p.add_argument("--retune-root", default=None)
    p.add_argument("--cohort", choices=("failed", "full"), default="failed")
    p = sub.add_parser("headline-check")
    p.add_argument("--profile", choices=tuple(PROFILES), default=DEFAULT_PROFILE)
    p.add_argument("--results", required=True)
    p.add_argument("--verdict", required=True)
    return parser


def run(argv):
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2  # --help exits 0; a usage error never does
    if not args.cmd:
        parser.print_usage(sys.stderr)
        return 2
    if args.cmd == "retune-gate" and (args.first_root is None) != (args.retune_root is None):
        sys.stderr.write("score43.py retune-gate: --first-root and --retune-root go together\n")
        return 2
    try:
        if args.cmd == "ledger":
            return _cmd_ledger(args.runs_root, args.expected_diffs)
        if args.cmd == "fp":
            return _cmd_fp(args.state)
        if args.cmd == "catch-candidates":
            return _cmd_catch_candidates(args.state, args.diff, args.manifest)
        if args.cmd == "codex-status":
            return _cmd_codex_status(args.state)
        if args.cmd == "aggregate":
            return _cmd_aggregate(args)
        if args.cmd == "failed-diffs":
            return _cmd_failed_diffs(args.runs_root, args.out, args.catch_verdicts)
        if args.cmd == "retune-gate":
            return _cmd_retune_gate(args)
        if args.cmd == "headline-check":
            return _cmd_headline_check(args.results, args.verdict, args.profile)
    except ScoreError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    except replay.ReplayError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    except (OSError, ValueError) as exc:
        sys.stderr.write("unreadable input: %s\n" % type(exc).__name__)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
