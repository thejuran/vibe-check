"""Path -> rerun-category classification for post-freeze changes.

PATH-MAP.json (schema `freeze-path-map/1`) lists glob rules, each naming the
categories a change to a matching path requires. The invariants:

  * a path's categories are the UNION over every matching rule;
  * an unmapped path requires every rerun category;
  * PATH-MAP.json itself requires every rerun category, whatever its rules
    say, so a map edit can never lower its own checks;
  * `reporting` is never implied by the fallback: it is the "no rerun,
    identity check still passes" category and only an explicit rule gives it.

Stdlib only (import lock: fnmatch, json, os, re + freeze_common).
"""

import json
import os

import freeze_common
from freeze_common import FreezeError

SCHEMA = "freeze-path-map/1"
CATEGORIES = ("engineering", "detection", "workflow", "reporting")
ALL_CATEGORIES = frozenset(CATEGORIES)
RERUN_CATEGORIES = ("engineering", "detection", "workflow")
MAP_SELF_PATH = "docs/design/freeze-v2.12/PATH-MAP.json"
DEFAULT_MAP = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "PATH-MAP.json")

REQUIRED_CHECKS = {
    "engineering": ("tests", "security-scan", "deep-review"),
    "detection": tuple("b3-run-%d" % i for i in range(1, 4))
                 + tuple("holdout-run-%d" % i for i in range(1, 4)),
    "workflow": tuple("preservation-run-%d" % i for i in range(1, 17))
                + tuple("clean-tree-run-%d" % i for i in range(1, 3)),
}

_TOP_KEYS = {"schema", "categories", "rules", "unmapped"}
_RULE_KEYS = {"glob", "cats"}


def _cats_ok(cats):
    return (isinstance(cats, list) and bool(cats)
            and all(isinstance(c, str) and c in ALL_CATEGORIES for c in cats))


def load_path_map(path=DEFAULT_MAP):
    """Read and validate a path map; return it with compiled rule regexes
    under `_compiled`. Any shape problem raises FreezeError."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        raise FreezeError("path map unreadable or not JSON: %s" % path)
    return validate_path_map(data)


def validate_path_map(data):
    if not isinstance(data, dict) or set(data) != _TOP_KEYS:
        raise FreezeError("path map: top-level keys must be exactly %s"
                          % sorted(_TOP_KEYS))
    if data["schema"] != SCHEMA:
        raise FreezeError("path map: schema must be %s" % SCHEMA)
    cats = data["categories"]
    if not isinstance(cats, dict) or set(cats) != ALL_CATEGORIES:
        raise FreezeError("path map: categories must be exactly %s"
                          % sorted(ALL_CATEGORIES))
    unmapped = data["unmapped"]
    if not _cats_ok(unmapped) or not set(RERUN_CATEGORIES) <= set(unmapped):
        raise FreezeError("path map: unmapped must name every rerun category")
    rules = data["rules"]
    if not isinstance(rules, list) or not rules:
        raise FreezeError("path map: rules must be a non-empty list")
    compiled = []
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict) or set(rule) != _RULE_KEYS:
            raise FreezeError("path map: rule %d must have exactly glob + cats" % i)
        if not isinstance(rule["glob"], str) or not rule["glob"]:
            raise FreezeError("path map: rule %d glob must be a non-empty string" % i)
        if not _cats_ok(rule["cats"]):
            raise FreezeError("path map: rule %d cats must be a non-empty "
                              "subset of the categories" % i)
        compiled.append((freeze_common.glob_to_regex(rule["glob"]),
                         frozenset(rule["cats"])))
    out = dict(data)
    out["_compiled"] = compiled
    return out


def classify(paths, path_map):
    """{path: set(categories)} — union over every matching rule; unmapped
    paths get the map's fallback; the map file always gets every rerun
    category."""
    compiled = path_map.get("_compiled")
    if compiled is None:
        compiled = validate_path_map(path_map)["_compiled"]
    fallback = set(path_map["unmapped"])
    result = {}
    for path in paths:
        cats = set()
        matched = False
        for regex, rule_cats in compiled:
            if regex.match(path):
                matched = True
                cats |= rule_cats
        if not matched:
            cats = set(fallback)
        if path == MAP_SELF_PATH:
            cats |= set(RERUN_CATEGORIES)
        result[path] = cats
    return result


def required(cats):
    """{rerun category: check ids} for the rerun categories in `cats`;
    `reporting` requires no rerun."""
    return {c: REQUIRED_CHECKS[c] for c in RERUN_CATEGORIES if c in set(cats)}


# --------------------------------------------------------------------------- #
# eligibility / inheritance / gate status
# --------------------------------------------------------------------------- #
