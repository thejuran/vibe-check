"""dedup.py — the `--all` cross-file dedup GROUPING rule as executable code.

Phase 40 (DIET-02, second tier, D-07). A BEHAVIOR-PRESERVING extraction of the
grouping key at `commands/review.md:948` and the collapse condition at `:949`.

THE GROUPING KEY (review.md:948), transcribed:

    Group the surviving individual findings by IDENTICAL `category` AND a
    substantially-similar `title`. Concrete title-similarity rule: lowercase
    both titles; strip file-specific tokens (paths, identifiers, quoted
    symbols, and line numbers); then group two findings together iff their
    normalized title-token sets have Jaccard overlap >= 0.7, OR one normalized
    title is a substring of the other after the strip.

The 0.7 bar is "deliberately conservative so two genuinely DISTINCT bugs that
merely share a `category` are NEVER merged into one displayed row" (:948). Do
not loosen it here; :948 records that the owner tunes it after real occurrence
counts, and a retune during extraction would be indistinguishable from a bug.

THE COLLAPSE CONDITION (review.md:949): a group DISPLAYS as one collapsed row
only when it spans 2+ DISTINCT files. The primary is "the highest-scored
occurrence". A group on a single file is still a group, but `collapsed` is
False so the prose renders its members as ordinary rows.

NOTHING IS MERGED OR RE-SCORED (review.md:947). The grouping is emphatically a
DISPLAY grouping: it "does NOT alter, merge, remove, collapse, or re-score any
canonical finding object", and `occurrence_count`/`occurrences` are RENDER-LOCAL
and are "NEVER added to the finding object or the Phase-4.5 pass entry". So this
module takes findings and returns REFERENCES to them (ids, files) — it never
returns, copies, or mutates a finding. A test asserts the input is unchanged.

WHAT THIS MODULE DOES NOT DO (D-08 keep-list). It groups; the prose renders —
do not extract the layout. It emits `occurrence_count` as a NUMBER and never the
`(+ N more occurrences)` phrase, no table rows, no band markup. A test asserts
it.

TWO RULES HERE ARE **NEW**, because the prose left them unspecified. Both are
ordering-only; neither changes which findings group together:

  1. Member order within a group is `(file, line, id)`. The prose specifies only
     the primary. An unspecified order would make the rendered occurrence list
     move run-to-run, and DIET-04's envelope leg measures byte-stability.
  2. Group order is: collapsed groups first, then uncollapsed; within each, by
     descending primary score, then by the group key. The prose orders band
     sections but never the groups inside them.

A THIRD point is a transcription AMBIGUITY, resolved to the most literal reading
and recorded rather than improved. `:948` defines similarity PAIRWISE ("group
two findings together iff..."), but Jaccard similarity is not transitive, so a
chain a~b~c with a!~c has no defined grouping. This module applies the literal
pairwise rule as SINGLE-LINKAGE over findings visited in a deterministic order
(sorted by `(file, line, id)`), joining a finding to the first existing group
whose SEED it matches. Seed-matching rather than any-member-matching keeps the
conservatism clause intact: a group can never grow by chaining through
progressively less similar members.

I/O: stdlib only, imports exactly {json, sys}. CLI:

    echo '{"findings": [...]}' | python3 dedup.py

JSON stdin -> JSON stdout. Unparseable stdin propagates so the process exits
NON-ZERO.
"""

import json
import sys

# review.md:948 — the Jaccard bar. Conservative by design; the owner tunes it,
# an extraction does not.
JACCARD_THRESHOLD = 0.7

# Characters that delimit tokens once quoting/punctuation is stripped. Kept as
# a set rather than a regex because `re` is outside this module's import set.
_SEPARATORS = set(" \t\n\r`'\"“”‘’()[]{}<>,;:!?*#=+")


def _strip_file_specific(token):
    """review.md:948 — strip paths, identifiers, quoted symbols, line numbers.

    A token is dropped when it looks file-specific rather than descriptive:
      * it contains a path separator or a file extension dot ("api/users.py")
      * it contains a digit (a line number, or "sha256")
      * it contains an underscore (a snake_case identifier, e.g. build_query)
      * it is mixedCase with an interior capital (a camelCase identifier)
    Quoting characters are removed before this test, which is what makes
    `` `build_query` `` a stripped identifier rather than a kept word.
    """
    if not token:
        return None
    if "/" in token or "\\" in token or "." in token:
        return None
    if any(ch.isdigit() for ch in token):
        return None
    if "_" in token:
        return None
    return token


def _normalize(title):
    """Lowercase, strip file-specific tokens, return the token SET (:948)."""
    cleaned = []
    for ch in title:
        cleaned.append(" " if ch in _SEPARATORS else ch)
    tokens = set()
    for raw in "".join(cleaned).split():
        # Detect camelCase BEFORE folding case, then fold (:948 lowercases).
        interior_capital = any(c.isupper() for c in raw[1:]) and not raw.isupper()
        kept = _strip_file_specific(raw)
        if kept is None or interior_capital:
            continue
        tokens.add(kept.lower())
    return tokens


def _similar(a_tokens, b_tokens):
    """:948 — Jaccard >= 0.7 OR one normalized title a substring of the other.

    With titles reduced to token SETS, "one is a substring of the other" is
    read as the set-containment it becomes after normalization: every token of
    the shorter title appears in the longer one.
    """
    if not a_tokens or not b_tokens:
        return a_tokens == b_tokens
    if a_tokens <= b_tokens or b_tokens <= a_tokens:
        return True
    union = len(a_tokens | b_tokens)
    if union == 0:
        return True
    return (len(a_tokens & b_tokens) / union) >= JACCARD_THRESHOLD


def _usable(finding):
    """A finding must carry the fields :948 requires: category AND title."""
    if not isinstance(finding, dict):
        return False
    return (isinstance(finding.get("category"), str)
            and isinstance(finding.get("title"), str)
            and isinstance(finding.get("id"), str))


def _sort_key(finding):
    """The NEW member order: (file, line, id). See the docstring."""
    line = finding.get("line")
    if not isinstance(line, int) or isinstance(line, bool):
        line = -1
    return (str(finding.get("file", "")), line, finding["id"])


def _score(finding):
    score = finding.get("orchestrator_score")
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        return -1
    return score


def group(findings):
    """Cross-file groups over the surviving individual findings (:948-:949).

    Returns a list of `{"key", "members", "files", "primary",
    "occurrence_count", "collapsed"}` dicts in a deterministic total order.
    Never returns a rendered row (D-08); never mutates `findings` (:947).
    """
    if not isinstance(findings, list):
        return []

    usable = sorted((f for f in findings if _usable(f)), key=_sort_key)

    # Single-linkage against each group's SEED, in a deterministic visit order.
    groups = []
    for finding in usable:
        tokens = _normalize(finding["title"])
        placed = False
        for g in groups:
            if g["category"] != finding["category"]:
                continue
            if _similar(g["seed_tokens"], tokens):
                g["members"].append(finding)
                placed = True
                break
        if not placed:
            groups.append({
                "category": finding["category"],
                "seed_tokens": tokens,
                "members": [finding],
            })

    out = []
    for g in groups:
        members = sorted(g["members"], key=_sort_key)
        files = sorted({str(m.get("file", "")) for m in members})
        # :949 — the primary is the highest-scored occurrence. Ties resolve by
        # the same (file, line, id) order, so the pick is deterministic.
        primary = sorted(members, key=lambda m: (-_score(m),) + _sort_key(m))[0]
        out.append({
            "key": g["category"] + "::" + "|".join(sorted(g["seed_tokens"])),
            "members": [m["id"] for m in members],
            "files": files,
            "primary": primary["id"],
            "occurrence_count": len(members),
            # :949 — collapse applies to groups spanning 2+ DISTINCT files.
            "collapsed": len(files) >= 2,
            "_order": (0 if len(files) >= 2 else 1, -_score(primary)),
        })

    out.sort(key=lambda g: g["_order"] + (g["key"],))
    for g in out:
        del g["_order"]
    return out


def run(envelope):
    """{"findings": [...]} -> the groups. Fails closed."""
    if not isinstance(envelope, dict):
        return []
    return group(envelope.get("findings"))


# --------------------------------------------------------------------------- #
# stdin/stdout shim — the ONLY process I/O. Fails CLOSED on bad input.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Do NOT wrap json.load in a swallowing try/except: an unparseable stdin
    # must propagate so the process exits NON-ZERO.
    json.dump(run(json.load(sys.stdin)), sys.stdout, allow_nan=False)
