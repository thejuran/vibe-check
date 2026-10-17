"""freeze_tally.py — the one entry point in front of every release tally.

Every subcommand builds the active manifest's prerequisites
(`freeze_policy.prerequisites_for`) and filters run records through
`freeze_policy.eligible`; there is no path that counts a run without both.

  list             one line per run dir: eligible, or INELIGIBLE with the reason
  b3-aggregate     score43 over a filtered view (ineligible runs become holes,
                   so score43 refuses); optional score43 `aggregate` args after --
  dev-tally        score43 dev-tally over eligible runs only
  harness-verdicts fix-harness run.json verdicts by slot, with eligibility
  gate             slot-based gate status: `GATE <name>: MET|UNMET` (exit 0|1)

There is no count option and no waiver option: a gate is MET only through
`freeze_policy.gate_status`. Runs roots are only read; filtered views are
symlink trees in a temporary directory. Holdout case content is never
opened — only run-record files (run.json, identity.json, fingerprint.txt)
and the engineering evidence files.

Usage error -> exit 2.
"""

import argparse
import json
import os
import sys
import tempfile

import freeze_policy
from freeze_common import FreezeError

REPO_DEFAULT = freeze_policy.REPO_DEFAULT
SERIES_REL = "docs/design/freeze-v2.12"
EVIDENCE_REL = freeze_policy.EVIDENCE_REL
PLUGIN_SCRIPTS_REL = os.path.join("plugins", "vibe-check", "scripts")


class UsageError(Exception):
    """Bad input: exit 2."""


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def _active_manifest_path(series_dir):
    best = None
    for name in (os.listdir(series_dir) if os.path.isdir(series_dir) else []):
        m = freeze_policy.MANIFEST_FILE_RE.match(name)
        if m and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), name)
    if best is None:
        raise UsageError("no freeze manifest under %s" % series_dir)
    return os.path.join(series_dir, best[1])


def _load_json(path, what):
    if path is None:
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        raise UsageError("%s unreadable or not JSON: %s" % (what, path))
    if not isinstance(data, dict):
        raise UsageError("%s is not a JSON object: %s" % (what, path))
    return data


def _context(args):
    """(manifest, prerequisites, lineage claim) for a subcommand."""
    series_dir = args.series_dir or os.path.join(args.repo, SERIES_REL)
    manifest_path = args.manifest or _active_manifest_path(series_dir)
    try:
        manifest = freeze_policy.load_manifest_file(manifest_path)
    except FreezeError as exc:
        raise UsageError(str(exc))
    evidence_dir = args.evidence_dir
    if evidence_dir is None:
        evidence_dir = args.runs_root if getattr(args, "gate", None) == "engineering" \
            else os.path.join(args.repo, EVIDENCE_REL)
    prerequisites = freeze_policy.prerequisites_for(manifest, args.repo,
                                                    evidence_dir, series_dir)
    lineage = _load_json(getattr(args, "lineage", None), "lineage")
    return manifest, prerequisites, lineage


def walk_records(runs_root):
    """read_record for every `<case>/run-*` directory under `runs_root`."""
    if not os.path.isdir(runs_root):
        raise UsageError("runs root is not a directory: %s" % runs_root)
    out = []
    for case in sorted(os.listdir(runs_root)):
        cdir = os.path.join(runs_root, case)
        if not os.path.isdir(cdir):
            continue
        for name in sorted(os.listdir(cdir)):
            rdir = os.path.join(cdir, name)
            if os.path.isdir(rdir) and name.startswith("run-"):
                out.append(freeze_policy.read_record(rdir))
    return out


def engineering_records(evidence_dir):
    return [freeze_policy.read_record(os.path.join(evidence_dir, name))
            for name in freeze_policy.ENGINEERING_RECORD_FILES
            if os.path.isfile(os.path.join(evidence_dir, name))]


def select_eligible(runs_root, manifest, prerequisites, lineage=None, kinds=None):
    """(eligible records, [(run, reason)]) — every record judged by
    freeze_policy.eligible."""
    keep, refused = [], []
    for rec in walk_records(runs_root):
        if kinds is not None and rec["kind"] not in kinds:
            continue
        ok, reason = freeze_policy.eligible(rec, manifest, prerequisites, lineage)
        if ok:
            keep.append(rec)
        else:
            refused.append((rec["run"], reason))
    return keep, refused


def _filtered_view(view_root, records):
    """Symlink `<case>/<run>` -> the real run dir for each record."""
    for rec in records:
        case, run = rec["run"].split("/", 1)
        os.makedirs(os.path.join(view_root, case), exist_ok=True)
        os.symlink(rec["path"], os.path.join(view_root, case, run))


def _score43(repo):
    scripts = os.path.join(repo, PLUGIN_SCRIPTS_REL)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import score43
    return score43


def _slot_text(slot):
    return "/".join(str(p) for p in slot)


# --------------------------------------------------------------------------- #
# Subcommands
# --------------------------------------------------------------------------- #

def cmd_list(args):
    manifest, prereq, lineage = _context(args)
    for rec in walk_records(args.runs_root):
        ok, reason = freeze_policy.eligible(rec, manifest, prereq, lineage)
        print("%s eligible" % rec["run"] if ok else
              "%s INELIGIBLE: %s" % (rec["run"], reason))
    return 0


def cmd_b3_aggregate(args):
    manifest, prereq, lineage = _context(args)
    rest = list(args.score43_args or [])
    if rest[:1] == ["--"]:
        rest = rest[1:]
    if "--runs-root" in rest:
        raise UsageError("--runs-root is set by freeze_tally (the filtered view)")
    keep, refused = select_eligible(args.runs_root, manifest, prereq, lineage,
                                    kinds=("b3",))
    for run, reason in refused:
        print("ineligible: %s (%s)" % (run, reason))
    score43 = _score43(args.repo)
    with tempfile.TemporaryDirectory() as view:
        _filtered_view(view, keep)
        ledger = score43.completeness_ledger(view)
        try:
            score43._require_complete(ledger)
        except score43.ScoreError as exc:
            print("refused: %s" % exc)
            return 1
        if not rest:
            print("complete: %d eligible runs" % len(keep))
            return 0
        return score43.run(["aggregate", "--runs-root", view] + rest)


def cmd_dev_tally(args):
    manifest, prereq, lineage = _context(args)
    keep, refused = select_eligible(args.runs_root, manifest, prereq, lineage,
                                    kinds=("b3", "holdout-eval"))
    score43 = _score43(args.repo)
    want = (manifest.get("plugin") or {}).get("runtime_fingerprint")
    with tempfile.TemporaryDirectory() as view:
        _filtered_view(view, keep)
        rc = score43._cmd_dev_tally(view, require_fingerprint=want)
    for run, reason in refused:
        print("ineligible: %s (%s)" % (run, reason))
    return 1 if refused else rc


def cmd_harness_verdicts(args):
    manifest, prereq, lineage = _context(args)
    roster = _load_json(args.roster, "roster")
    try:
        slots = freeze_policy.GATE_SLOTS["workflow"](roster)
    except FreezeError as exc:
        raise UsageError(str(exc))
    by_slot, refused = {}, False
    for rec in walk_records(args.runs_root):
        if rec["kind"] != "fix-harness":
            continue
        ok, reason = freeze_policy.eligible(rec, manifest, prereq, lineage)
        slot = _slot_text(rec["slot"]) if rec["slot"] else "<no slot>"
        if ok:
            key = freeze_policy._slot_key("workflow", rec["slot"])
            if key not in slots:
                # Listed, never counted: only mandatory slots enter the total.
                print("extra: %s (not a mandatory slot)" % rec["run"])
                continue
            by_slot.setdefault(key, []).append(rec)
            print("%s %s %s eligible" % (slot, rec["run"], rec.get("verdict")))
        else:
            refused = True
            print("%s %s %s INELIGIBLE: %s" % (slot, rec["run"], rec.get("verdict"),
                                               reason))
    for key in sorted(by_slot, key=_slot_text):
        if len(by_slot[key]) > 1:
            refused = True
            print("duplicate slot: %s (%s)" % (_slot_text(key), ", ".join(
                sorted(r["run"] for r in by_slot[key]))))
    for slot in sorted(slots, key=_slot_text):
        if slot not in by_slot:
            refused = True
            print("missing slot: %s" % _slot_text(slot))
    if refused:
        print("refused: not totalling while a run is ineligible, duplicated or missing")
        return 1
    verdicts = [r.get("verdict") for rs in by_slot.values() for r in rs]
    print("COMPLETE: %d" % verdicts.count("COMPLETE"))
    print("other: %d" % (len(verdicts) - verdicts.count("COMPLETE")))
    return 0


def cmd_gate(args):
    manifest, prereq, lineage = _context(args)
    roster = _load_json(args.roster, "roster")
    verdicts = _load_json(args.verdicts, "verdicts")
    if args.gate == "engineering":
        records = engineering_records(args.runs_root)
    else:
        records = walk_records(args.runs_root)
    res = freeze_policy.gate_status(args.gate, records, manifest, prereq,
                                    lineage=lineage, roster=roster, verdicts=verdicts)
    print("GATE %s: %s" % (args.gate, res["status"]))
    for problem in res["prerequisites"]:
        print("prerequisite: %s" % problem)
    for slot in res["missing"]:
        print("missing slot: %s" % _slot_text(slot))
    for dup in res["duplicates"]:
        print("duplicate slot: %s (%s)" % (_slot_text(dup["slot"]), ", ".join(dup["runs"])))
    for extra in res["extras"]:
        print("extra: %s (%s)" % (extra["run"], extra["reason"]))
    for inel in res["ineligible"]:
        print("ineligible: %s (%s)" % (inel["run"], inel["reason"]))
    for reason in res["rule"]["reasons"]:
        print("rule: %s" % reason)
    return 0 if res["status"] == "MET" else 1


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _common(p):
    p.add_argument("--runs-root", required=True)
    # Optional everywhere: absent -> the highest-N FREEZE-MANIFEST-<N>.json in
    # the series dir (the active manifest).
    p.add_argument("--manifest", default=None)
    p.add_argument("--repo", default=REPO_DEFAULT)
    p.add_argument("--evidence-dir", default=None)
    p.add_argument("--series-dir", default=None)
    p.add_argument("--lineage", default=None)


def build_parser():
    parser = argparse.ArgumentParser(prog="freeze_tally.py",
                                     description="Eligibility-filtered release tallies.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    _common(sub.add_parser("list"))
    p = sub.add_parser("b3-aggregate")
    _common(p)
    p.add_argument("score43_args", nargs=argparse.REMAINDER)
    _common(sub.add_parser("dev-tally"))
    p = sub.add_parser("harness-verdicts")
    _common(p)
    # Required: without the roster there is no slot set to check completeness
    # against, so a total could not tell a full set from a partial one.
    p.add_argument("--roster", required=True)
    p = sub.add_parser("gate")
    _common(p)
    p.add_argument("--gate", required=True, choices=freeze_policy.GATES)
    p.add_argument("--roster", default=None)
    p.add_argument("--verdicts", default=None)
    return parser


COMMANDS = {"list": cmd_list, "b3-aggregate": cmd_b3_aggregate,
            "dev-tally": cmd_dev_tally, "harness-verdicts": cmd_harness_verdicts,
            "gate": cmd_gate}


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        return COMMANDS[args.cmd](args)
    except ValueError as exc:
        # score43 refusals (ScoreError is a ValueError) and unreadable run state.
        sys.stderr.write("freeze_tally.py: score43 refused: %s\n" % exc)
        return 1
    except UsageError as exc:
        sys.stderr.write("freeze_tally.py: %s\n" % exc)
        return 2
    except FreezeError as exc:
        sys.stderr.write("freeze_tally.py: %s\n" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
