"""calibrate.py — B-REWEIGHT per-agent confidence offsets, derived from archives.

This derives the per-agent confidence offsets that score.py embeds as
`AGENT_CONFIDENCE_OFFSET`. The method was FIXED in
`docs/design/b3-ground-truth/CALIBRATION-v2.10.md` before any candidate scorer
was replayed (D-15). There is no search over `ALPHA` or `MIN_LABELED`: they are
module constants, pinned by test, and changing either is a new method that
needs its own recorded reason, not a tuning step.

What the numbers ARE: a base-rate correction. Each agent's labeled precision is
shrunk toward the pooled precision with prior strength `ALPHA`; an agent whose
shrunk precision sits below the pool gets a negative offset of that many
percentage points. What they are NOT:

* not a raise — offsets are lower-only (`min(0, ...)`); an agent above the pool
  is identity;
* not applied everywhere — score.py applies them only to lone-lane groups
  (no second opinion); corroboration restores the raw confidence;
* not a per-bucket curve — confidence does not separate TP from FP within an
  agent, so only a per-agent shift is supported by the data;
* not a precision estimate — the labels are a LOWER BOUND on precision. Only
  axis-qualifying findings on catch runs count as TP; every other real issue
  found on a catch run is unlabeled (Pitfall 4);
* not from every archive — inputs are the Claude-5-era archives only
  (`runs-v2.10/`, `runs-v2.10-phase40/`; D-04), with should-quiet-7 excluded
  (D-06). `counts` RAISES if either boundary is crossed; it is asserted, not
  described.

Arithmetic is exact (`fractions.Fraction`), so the rounding rule is exactly
Python 3's `round`: half-to-even. Agents with fewer than `MIN_LABELED`
labeled findings are identity (absent from the result); zero offsets are
omitted (absent means 0).

It reads only the committed catch manifest and archives (through replay.py,
the single archive walker); never live review state, never a reviewed
repository. It prints agent names, integers and fractions only — never a
finding title or problem text.

Imports exactly {argparse, fractions, json, os, sys} plus the sibling
`replay` module, and the sibling `score` module inside `--check` only.

    python3 calibrate.py counts
    python3 calibrate.py derive
    python3 calibrate.py --check

Exit 0 clean / 1 `--check` mismatch or score.py has no offsets / 2 usage error
or unreadable manifest.
"""

import argparse
import fractions
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import replay  # noqa: E402  (sibling module: the single archive walker)

# D-15: fixed before any candidate replay. Never searched.
ALPHA = 20
MIN_LABELED = 5

# D-04: only the Claude-5-era archives teach the calibration.
CALIBRATION_ARCHIVES = ("runs-v2.10", "runs-v2.10-phase40")
# A quiet-run survivor at one of these bands is a labeled false positive.
FIRING_BANDS = ("critical", "warning")
QUIET_SETS = ("headline", "phase40")
MALFORMED_AGENT = "<malformed>"


class CalibrationError(Exception):
    """A labeled input crosses the D-04/D-06 boundary or cannot be read."""


def _excluded_paths(manifest):
    out = set()
    for key, value in (manifest.get("excluded_runs") or {}).items():
        if key == "reason":
            continue
        if isinstance(value, list):
            out.update(v for v in value if isinstance(v, str))
    return out


def _check_boundary(path, archive, excluded):
    if archive not in CALIBRATION_ARCHIVES:
        raise CalibrationError("%s: archive %r is not a calibration archive (D-04)"
                               % (path, archive))
    if path in excluded:
        raise CalibrationError("%s: excluded run cannot be labeled (D-06)" % path)


def _bump(table, agent, key):
    row = table.setdefault(agent, {"tp": 0, "fp": 0, "n": 0})
    row[key] += 1
    row["n"] += 1


def counts(manifest, runs):
    """{agent: {"tp", "fp", "n"}} over the labeled Claude-5-era runs, sorted by agent.

    TP: a `survivors_at_site` entry with `axis: true` on a catch run marked
    `calibration: true`. FP: a last-pass survivor at a FIRING_BANDS band on a
    quiet run in `quiet_runs.headline` or `quiet_runs.phase40`. The archived
    band is the label (the adjudicated ground truth), never a replay.
    """
    by_path = {r["rel_path"]: r for r in runs}
    excluded = _excluded_paths(manifest)
    table = {}

    for path, entry in sorted((manifest.get("catch_runs") or {}).items()):
        if not isinstance(entry, dict) or entry.get("calibration") is not True:
            continue
        run = by_path.get(path)
        archive = run["archive"] if run else entry.get("archive")
        _check_boundary(path, archive, excluded)
        if entry.get("archive") != archive:
            raise CalibrationError("%s: manifest archive disagrees with the walk" % path)
        for s in entry.get("survivors_at_site") or []:
            if not isinstance(s, dict) or s.get("axis") is not True:
                continue
            agent = s.get("agent")
            _bump(table, agent if isinstance(agent, str) else MALFORMED_AGENT, "tp")

    quiet = manifest.get("quiet_runs") or {}
    for key in QUIET_SETS:
        for path in quiet.get(key) or []:
            run = by_path.get(path)
            if run is None:
                raise CalibrationError("%s: quiet run not found in the archives" % path)
            _check_boundary(path, run["archive"], excluded)
            passes = (run.get("state") or {}).get("passes") or []
            if not passes or not isinstance(passes[-1], dict):
                raise CalibrationError("%s: no last pass" % path)
            for f in passes[-1].get("findings") or []:
                if not isinstance(f, dict) or f.get("band") not in FIRING_BANDS:
                    continue
                agent = f.get("agent")
                _bump(table, agent if isinstance(agent, str) else MALFORMED_AGENT, "fp")

    return {a: table[a] for a in sorted(table)}


def pooled_precision(table):
    """(ΣTP, Σ(TP+FP)) over every labeled agent, as exact ints."""
    num = sum(row["tp"] for row in table.values())
    den = sum(row["tp"] + row["fp"] for row in table.values())
    return num, den


def offsets_from_table(table):
    """The D-15 offsets for a counts table: only negative entries, int values."""
    num, den = pooled_precision(table)
    if den == 0:
        return {}
    p_pool = fractions.Fraction(num, den)
    out = {}
    for agent in sorted(table):
        row = table[agent]
        n = row["tp"] + row["fp"]
        if n < MIN_LABELED:
            continue
        p_hat = (row["tp"] + ALPHA * p_pool) / (n + ALPHA)
        off = min(0, int(round(100 * (p_hat - p_pool))))
        if off < 0:
            out[agent] = off
    return out


def derive(manifest, runs):
    """agent -> negative int offset over the committed calibration archives."""
    return offsets_from_table(counts(manifest, runs))


def _counts_text(table):
    lines = ["| agent | TP | FP | n | labeled? |", "|---|---|---|---|---|"]
    for agent, row in table.items():
        labeled = "yes" if row["n"] >= MIN_LABELED else "no (identity)"
        lines.append("| %s | %d | %d | %d | %s |" % (agent, row["tp"], row["fp"],
                                                     row["n"], labeled))
    num, den = pooled_precision(table)
    lines.append("")
    lines.append("pooled precision = ΣTP/Σ(TP+FP) = %d/%d" % (num, den))
    lines.append("ALPHA=%d MIN_LABELED=%d" % (ALPHA, MIN_LABELED))
    return "\n".join(lines) + "\n"


def _derive_text(offsets):
    return json.dumps(offsets, sort_keys=True) + "\n"


def _check(offsets):
    import score  # noqa: E402  (sibling module; only --check reads it)
    embedded = getattr(score, "AGENT_CONFIDENCE_OFFSET", None)
    if embedded is None:
        sys.stdout.write("score.py has no AGENT_CONFIDENCE_OFFSET\n")
        return 1
    if embedded != offsets:
        sys.stdout.write("MISMATCH score.py=%s derived=%s\n"
                         % (json.dumps(embedded, sort_keys=True),
                            json.dumps(offsets, sort_keys=True)))
        return 1
    sys.stdout.write("OK score.py AGENT_CONFIDENCE_OFFSET equals the derivation\n")
    return 0


def run(argv):
    parser = argparse.ArgumentParser(
        prog="calibrate.py", description="B-REWEIGHT derivation (see module docstring).")
    parser.add_argument("cmd", nargs="?", choices=("counts", "derive"))
    parser.add_argument("--check", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2  # usage error -> fail closed, never exit 0
    if bool(args.cmd) == bool(args.check):
        parser.print_usage(sys.stderr)
        return 2

    try:
        manifest = replay.load_manifest()
        runs = replay.iter_runs()
        table = counts(manifest, runs)
    except (OSError, ValueError, replay.ReplayError, CalibrationError) as exc:
        sys.stderr.write("calibrate.py: %s\n" % exc)
        return 2

    if args.cmd == "counts":
        sys.stdout.write(_counts_text(table))
        return 0
    offsets = offsets_from_table(table)
    if args.cmd == "derive":
        sys.stdout.write(_derive_text(offsets))
        return 0
    return _check(offsets)


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
