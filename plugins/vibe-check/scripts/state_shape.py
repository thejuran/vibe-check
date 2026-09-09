"""state_shape.py — the SHAPE leg of DIET-04 envelope byte-stability.

RESEARCH Q6 found the review state envelope was never actually deterministic:
across the 37 sealed Phase-38 runs the `codex` value takes 8 distinct shapes
(twice a bare string), the `timestamp` appears in two resolutions, and findings
carry an improvised long tail of extra keys. Byte equality was therefore
abandoned as a stability definition — and this module is what replaced it: a
DEFINED shape contract, executed rather than assumed.

Two schemas, two jobs. They are separate files and must stay separate:

  fixtures/archive-compat-schema.json  DESCRIPTIVE. Records what the 37 sealed
    states ACTUALLY contain, so they can be validated without touching a byte.
    Never tighten it to make a new state pass.
  fixtures/future-schema.json          PRESCRIPTIVE. The contract every state
    produced after Phase 40 must satisfy. Never loosen it to accommodate an
    archive.

Collapsing them would either reject sealed evidence or bless the drift the
contract exists to stop, so `--schema` is a REQUIRED enum with no default: the
caller must say which contract it is asserting.

Scope, stated honestly: this proves the ENVELOPE shape is stable. It does not
prove orchestration or rendered reports are unchanged. Those are the scorer leg
(test_score.py goldens), the script leg (the per-script goldens), and the trace
leg. This module owns one of four legs.

NO WRITE PATH. The archives are evidence that later phases re-measure against;
a validator able to write is a validator able to corrupt what it validates.
This module never opens a file for writing, never imports shutil/tempfile, and
a test asserts both by AST inspection.

Reasons are drawn from the module-level REASONS tuple and name the offending
KEY only. A reason NEVER contains a value from the state — no finding titles,
no file paths, no SHAs (T-40-15: state files carry content derived from
attacker-authored diffs).

I/O: stdlib only, imports exactly {json, os, re, sys}. CLI:

    python3 state_shape.py <state.json> --schema archive-compat|future [--all]

GATE semantics (D-13): exit 0 clean, 1 on any violation, 2 on unreadable input
or a usage error. One reason per line on stderr; callers branch on the EXIT
CODE. Contrast footprint.py, which is optional context and always exits 0.
"""

import json
import os
import re
import sys

SCHEMA_NAMES = ("archive-compat", "future")

# Every reason the checker can emit. Each is a fixed template taking at most a
# KEY name — never a value read out of the state (T-40-15).
REASONS = (
    "missing required root key: %s",
    "unknown root key: %s",
    "state is not an object",
    "passes is not a list",
    "pass entry is not an object",
    "missing required key in pass entry: %s",
    "unknown key in pass entry: %s",
    "forbidden key in pass entry: %s",
    "--all-only key present in diff-mode pass entry: %s",
    "timestamp does not match the pinned format",
    "timestamp is not a string",
    "codex record is not an object",
    "missing required key in codex record: %s",
    "unknown key in codex record: %s",
    "codex status is not in the pinned enum",
    "codex verdict is not in the pinned enum",
    "codex findings count is not an integer",
    "codex reason is not a slug or null",
    "findings is not a list",
    "finding is not an object",
    "missing required key in finding: %s",
    "unknown key in finding: %s",
)

_HERE = os.path.dirname(os.path.abspath(__file__))


def load_schema(name):
    """Load a schema by ENUM NAME (not a path) from fixtures/ next to this module.

    Schemas are DATA: no key set, regex, or codex shape is hard-coded here, so
    a future phase can diff the envelope contract as data. The name is checked
    against a fixed enum before it reaches the filesystem, so no caller can
    traverse out of fixtures/ or point the tool at an arbitrary file.
    """
    if name not in SCHEMA_NAMES:
        raise ValueError("unknown schema name (expected one of: %s)"
                         % ", ".join(SCHEMA_NAMES))
    path = os.path.join(_HERE, "fixtures", "%s-schema.json" % name)
    with open(path) as handle:
        return json.load(handle)


def _key_reasons(obj, required, optional, closed, missing_tpl, unknown_tpl,
                 extra_known=()):
    """Shared required/unknown key comparison. Returns fixed reason strings."""
    reasons = []
    for key in required:
        if key not in obj:
            reasons.append(missing_tpl % key)
    if closed:
        known = set(required) | set(optional) | set(extra_known)
        for key in obj:
            if key not in known:
                reasons.append(unknown_tpl % key)
    return reasons


def check_finding(finding, schema):
    """Validate one finding. -> list of fixed reason strings."""
    if not isinstance(finding, dict):
        return ["finding is not an object"]
    return _key_reasons(
        finding,
        schema.get("finding_required", []),
        schema.get("finding_optional", []),
        schema.get("finding_closed", False),
        "missing required key in finding: %s",
        "unknown key in finding: %s",
    )


def check_codex(codex, shape):
    """Validate the `codex` record against the schema's canonical shape.

    `shape` is None for the historical schema — the archives are genuinely
    nondeterministic here (8 shapes, twice a bare string) and the descriptive
    schema records that truth rather than pretending otherwise.
    """
    if shape is None:
        return []
    if not isinstance(codex, dict):
        return ["codex record is not an object"]
    reasons = _key_reasons(
        codex,
        shape.get("required", []),
        [],
        shape.get("closed", False),
        "missing required key in codex record: %s",
        "unknown key in codex record: %s",
    )
    if "status" in codex and "status_enum" in shape:
        if codex["status"] not in shape["status_enum"]:
            reasons.append("codex status is not in the pinned enum")
    if "verdict" in codex and "verdict_enum" in shape:
        if codex["verdict"] not in shape["verdict_enum"]:
            reasons.append("codex verdict is not in the pinned enum")
    if "findings" in codex and shape.get("findings_type") == "int":
        value = codex["findings"]
        # bool is a subclass of int; a flag is not a count.
        if not isinstance(value, int) or isinstance(value, bool):
            reasons.append("codex findings count is not an integer")
    if "reason" in codex and "reason_regex" in shape:
        # FL-14: the field's real domain is a slug or null. An empty string or
        # a free-text sentence is drift.
        value = codex["reason"]
        if value is None:
            if not shape.get("reason_nullable", False):
                reasons.append("codex reason is not a slug or null")
        elif not isinstance(value, str) or not re.match(shape["reason_regex"], value):
            reasons.append("codex reason is not a slug or null")
    return reasons


def check_pass_entry(entry, schema, all_mode=False):
    """Validate one pass entry (and, recursively, its findings)."""
    if not isinstance(entry, dict):
        return ["pass entry is not an object"]

    all_only = schema.get("pass_all_only", [])
    reasons = _key_reasons(
        entry,
        schema.get("pass_required", []),
        schema.get("pass_optional", []),
        schema.get("pass_closed", True),
        "missing required key in pass entry: %s",
        "unknown key in pass entry: %s",
        # The --all-only keys are known-but-conditional: their presence is
        # judged by the diff-mode rule below, not by the unknown-key rule.
        extra_known=list(all_only) + list(schema.get("pass_forbidden", [])),
    )

    for key in schema.get("pass_forbidden", []):
        if key in entry:
            reasons.append("forbidden key in pass entry: %s" % key)

    # Diff-mode purity: the diff-mode pass-entry shape is byte-unchanged, so
    # the three --all-only keys must be omitted ENTIRELY outside --all.
    if not all_mode:
        for key in all_only:
            if key in entry:
                reasons.append(
                    "--all-only key present in diff-mode pass entry: %s" % key)

    timestamp_regex = schema.get("timestamp_regex")
    if timestamp_regex and "timestamp" in entry:
        value = entry["timestamp"]
        if not isinstance(value, str):
            reasons.append("timestamp is not a string")
        elif not re.match(timestamp_regex, value):
            reasons.append("timestamp does not match the pinned format")

    if "codex" in entry:
        reasons.extend(check_codex(entry["codex"], schema.get("codex_shape")))

    if "findings" in entry:
        findings = entry["findings"]
        if not isinstance(findings, list):
            reasons.append("findings is not a list")
        else:
            for finding in findings:
                reasons.extend(check_finding(finding, schema))

    return reasons


def check_state(state, schema, all_mode=False):
    """Validate a whole state file: root keys plus every pass entry."""
    if not isinstance(state, dict):
        return ["state is not an object"]

    reasons = _key_reasons(
        state,
        schema.get("root_required", []),
        schema.get("root_optional", []),
        schema.get("root_closed", False),
        "missing required root key: %s",
        "unknown root key: %s",
    )

    if "passes" in state:
        passes = state["passes"]
        if not isinstance(passes, list):
            reasons.append("passes is not a list")
        else:
            for entry in passes:
                reasons.extend(check_pass_entry(entry, schema, all_mode=all_mode))

    return reasons


USAGE = ("usage: state_shape.py <state.json> --schema archive-compat|future [--all]\n"
         "  --schema is REQUIRED and takes one of those two names (not a filename):\n"
         "  the caller must say which contract it is asserting.\n")


def _parse(argv):
    """Hand-rolled argv parse (argparse is outside this module's import set).

    Returns (path, schema_name, all_mode) or raises ValueError on a usage error.
    """
    path = None
    schema_name = None
    all_mode = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--schema":
            if index + 1 >= len(argv):
                raise ValueError("--schema requires a value")
            schema_name = argv[index + 1]
            index += 2
            continue
        if arg == "--all":
            all_mode = True
            index += 1
            continue
        if arg.startswith("-"):
            raise ValueError("unknown option")
        if path is not None:
            raise ValueError("exactly one state file is expected")
        path = arg
        index += 1
    if path is None:
        raise ValueError("a state file path is required")
    if schema_name is None:
        raise ValueError("--schema is required (no default)")
    if schema_name not in SCHEMA_NAMES:
        raise ValueError("--schema must be one of: %s" % ", ".join(SCHEMA_NAMES))
    return path, schema_name, all_mode


def run(argv):
    """CLI shim. 0 clean / 1 violation / 2 unreadable input or usage error."""
    try:
        path, schema_name, all_mode = _parse(argv)
    except ValueError as exc:
        sys.stderr.write("%s\n%s" % (exc, USAGE))
        return 2

    try:
        schema = load_schema(schema_name)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write("schema could not be loaded: %s\n" % exc)
        return 2

    try:
        with open(path) as handle:
            state = json.load(handle)
    except (OSError, ValueError):
        # Never echo the payload: an unreadable state file may itself carry
        # reviewed-repo content in its parse-error context.
        sys.stderr.write("state file could not be read or parsed as JSON\n")
        return 2

    reasons = check_state(state, schema, all_mode=all_mode)
    for reason in reasons:
        sys.stderr.write(reason + "\n")
    return 1 if reasons else 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
