"""chunks.py — the deterministic risk rank and chunk packer for `--all` reviews.

Phase 40 (DIET-02, Family 2). This is a BEHAVIOR-PRESERVING extraction of
review.md Phase 0.2 (risk-score, two-key sort, greedy pack) and the Phase-0.3
agents-per-chunk budget arithmetic. Every tier glob, budget number, and count
below is transcribed from the cited prose line; nothing is retuned here.

Pure-function boundary (keep-list D-08): the script does NO filesystem, git, or
shell-out I/O. Sizes and churn ARRIVE AS DATA — `wc -l`, `wc -c`, and the
one-pass `git log` churn table stay orchestrator-side glue, exactly as the
inventory's keep-list requires. Import set is EXACTLY {fnmatch, json, sys}
(the AST import-set test enforces this).

CHUNK-01 — the tier-first lock. Path tier is the PRIMARY sort key; churn is
ONLY a within-tier booster. This order inverted once (a high-churn README
floating above a low-churn crypto file and leading chunk #1), so the ordering
is pinned by a golden test and must not be reordered.

The path tie-break is NEW and deliberate: bash `sort` without `-s` left equal
(tier, churn) rows in byte order, which was not reproducible across locales. No
consumer depended on that tie order, so the explicit `path` third key replaces
it and is what makes the packed output golden-testable.

I/O: one JSON envelope on stdin -> one JSON envelope on stdout. The __main__
shim fails CLOSED — unparseable stdin propagates so the process exits non-zero.
`--budgets` prints the two budget constants and exits 0; that flag is the single
source the overflow prose reads, so the numbers are stated in one place only.
"""

import fnmatch
import json
import sys

# --------------------------------------------------------------------------- #
# Constants — transcribed verbatim from commands/review.md. Do NOT retune.
# --------------------------------------------------------------------------- #

# review.md:312 — per-chunk budget of 1800 lines (`wc -l` column) AND a
# secondary per-chunk cap of 200000 bytes (`wc -c` column). The byte cap exists
# because lines alone has a one-line-file blind spot: a minified or generated
# single-line blob counts as ~1 line but can be enormous in bytes.
LINE_BUDGET = 1800
BYTE_CAP = 200000

# review.md:270-282 — the path-tier `case` arms, in order. Lower tier number =
# higher audit risk. First matching arm wins, exactly like the shell `case`.
# The globs are UNANCHORED on purpose (`*auth*` matches anywhere in the path);
# this is a transcription, not a cleanup — narrowing them is a behavior change.
TIERS = (
    # tier 0 — highest audit risk: auth / crypto / secrets
    (0, ("*auth*", "*login*", "*session*", "*crypto*", "*secret*",
         "*password*", "*token*", "*.env*", "*credential*")),
    # tier 1 — api surface / input handling / db / config
    (1, ("*/api/*", "*input*", "*validat*", "*sanitiz*", "*db/*",
         "*query*", "*sql*", "*config*")),
    # tier 2 — other executable source
    (2, ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.mjs", "*.cjs",
         "*.go", "*.rs")),
)
DEFAULT_TIER = 3  # review.md:281 — docs / config / other (README lands here)

# review.md:351 — the agents/chunk RANGE. The `/review` FLOOR is triage + bugs
# + security (3), plus compliance when a dispatch-relevant CLAUDE.md/AGENTS.md
# is in scope (4). `/deep-review` raises the floor by adding architecture +
# impact + test-sufficiency. The MAX is the floor plus every applicable
# language-* (4) and framework-* (8) agent = floor + 12.
REVIEW_FLOOR = 3
DEEP_FLOOR_EXTRA = 3  # architecture + impact + test-sufficiency
MAX_OPTIONAL_AGENTS = 12  # language-* (4) + framework-* (8)


# --------------------------------------------------------------------------- #
# Risk math
# --------------------------------------------------------------------------- #
def tier_for(path):
    """Path-tier classification — the PRIMARY risk key (review.md:270-282).

    Mirrors the shell `case "$path" in ... esac`: arms are tried in order and
    the FIRST match wins, so a path matching both a tier-0 and a tier-1 glob
    lands in tier 0.
    """
    for tier, globs in TIERS:
        for glob in globs:
            if fnmatch.fnmatchcase(path, glob):
                return tier
    return DEFAULT_TIER


def _sort_key(row):
    """(tier ASC, churn DESC, path ASC) — CHUNK-01.

    Tier first is the locked ordering. Churn is negated so a higher commit
    count sorts earlier WITHIN a tier only. Path is the explicit tie-break.
    """
    return (tier_for(row["path"]), -row.get("churn", 0), row["path"])


def risk_order(rows):
    """Return `rows` in risk order, riskiest first. Does not mutate the input.

    review.md:286-291 — `sort -t$'\\t' -k1,1n -k2,2nr`: tier numeric ascending
    is the PRIMARY key, churn numeric descending is only the within-tier
    booster. review.md:293 states the anti-pattern explicitly: sorting churn
    before tier reintroduces the README-vs-crypto inversion.
    """
    return sorted(rows, key=_sort_key)


# --------------------------------------------------------------------------- #
# The greedy packer — "risk seeds, directory fills" (review.md:305-311)
# --------------------------------------------------------------------------- #
def _dirname(path):
    """Directory part of a repo-relative path; "" for a top-level file."""
    head, sep, _tail = path.rpartition("/")
    return head if sep else ""


def _as_file(row):
    return {"path": row["path"], "lines": row["lines"], "bytes": row["bytes"]}


def pack(rows, line_budget=LINE_BUDGET, byte_cap=BYTE_CAP):
    """Walk the risk-ordered list into budget-fitting chunks.

    `rows` is consumed in the order given — callers pass `risk_order(rows)`.
    A file FITS a chunk only if BOTH bounds hold after adding it.

    Per review.md:305-311: seed with the riskiest unplaced file, fill from
    same-directory neighbours first (best agent context), then spill to the
    next-riskiest unplaced files in any directory. Chunks emerge in descending
    seed-risk order because we always seed from the riskiest remaining file.

    Edge A (review.md:313): a seed exceeding EITHER bound becomes its own
    single-file chunk — nothing fits alongside it, so both loops add nothing.
    That is what catches a giant one-line file, whose bytes blow the cap while
    its line count never trips the line bound.

    Edge B (review.md:315): an empty input yields no chunks.
    """
    unplaced = list(rows)
    chunks = []
    while unplaced:
        seed = unplaced.pop(0)
        placed = [seed]
        total_lines = seed["lines"]
        total_bytes = seed["bytes"]
        seed_dir = _dirname(seed["path"])

        # FILL from same-directory neighbours FIRST, in risk order.
        remaining = []
        for row in unplaced:
            if (_dirname(row["path"]) == seed_dir
                    and total_lines + row["lines"] <= line_budget
                    and total_bytes + row["bytes"] <= byte_cap):
                placed.append(row)
                total_lines += row["lines"]
                total_bytes += row["bytes"]
            else:
                remaining.append(row)
        unplaced = remaining

        # THEN SPILL to the next-riskiest unplaced files, any directory.
        remaining = []
        for row in unplaced:
            if (total_lines + row["lines"] <= line_budget
                    and total_bytes + row["bytes"] <= byte_cap):
                placed.append(row)
                total_lines += row["lines"]
                total_bytes += row["bytes"]
            else:
                remaining.append(row)
        unplaced = remaining

        chunks.append({
            "seed": seed["path"],
            "tier": tier_for(seed["path"]),
            # Lexicographic WITHIN the chunk — D-07/D-08 position stability:
            # Phase 2 builds each chunk's <files> block from this order, and a
            # stable order is what keeps the block byte-identical across the
            # chunk's agents so the prompt cache actually hits.
            "files": sorted((_as_file(r) for r in placed),
                            key=lambda f: f["path"]),
            "lines": total_lines,
            "bytes": total_bytes,
        })
    return chunks


# --------------------------------------------------------------------------- #
# Budget counts (review.md:349-351)
# --------------------------------------------------------------------------- #
def budget_counts(mode, compliance, chunk_total):
    """Agents-per-chunk floor/max and the dispatch range for `chunk_total`.

    review.md:351 — `/review` floor = triage + bugs + security = 3, or 4 with
    compliance; max = floor + 12 (the language-* and framework-* fleet), i.e.
    15 or 16. `/deep-review` adds architecture + impact + test-sufficiency to
    the floor, giving 6/7 and 18/19.

    The compliance term follows the prose's conservative-include rule: the
    caller passes True whenever a dispatch-relevant CLAUDE.md/AGENTS.md exists
    anywhere in the selected scope, so the upper bound is never understated.
    """
    floor = REVIEW_FLOOR
    if mode == "deep":
        floor += DEEP_FLOOR_EXTRA
    if compliance:
        floor += 1
    maximum = floor + MAX_OPTIONAL_AGENTS
    return {
        "floor": floor,
        "max": maximum,
        "dispatch_min": chunk_total * floor,
        "dispatch_max": chunk_total * maximum,
        "chunk_total": chunk_total,
    }


# --------------------------------------------------------------------------- #
# Envelope
# --------------------------------------------------------------------------- #
def run(envelope):
    """{"files":[{path,lines,bytes,churn}], "mode", "compliance"} -> plan."""
    rows = envelope.get("files") or []
    packed = pack(risk_order(rows))
    counts = budget_counts(
        envelope.get("mode", "review"),
        bool(envelope.get("compliance", False)),
        len(packed),
    )
    return {"chunks": packed, "counts": counts}


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY I/O. Fails CLOSED on bad input.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    if "--budgets" in sys.argv[1:]:
        # The single source the overflow prose reads, so the two numbers are
        # never re-typed into a second place where they can drift.
        sys.stdout.write(
            "LINE_BUDGET=%d BYTE_CAP=%d\n" % (LINE_BUDGET, BYTE_CAP)
        )
        sys.exit(0)
    # Do NOT wrap json.load in a swallowing try/except: an unparseable stdin
    # must propagate so the process exits NON-ZERO and the orchestrator can
    # fail the review closed instead of dispatching an unplanned chunk set.
    _envelope = json.load(sys.stdin)
    json.dump(run(_envelope), sys.stdout, allow_nan=False)
