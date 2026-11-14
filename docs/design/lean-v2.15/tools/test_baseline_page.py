"""Locks that keep BASELINE-v2.14.1.md equal to the committed baseline records.

The page is the owner's plain-terms summary of the 2.14.1 baseline. Every
figure on it comes from a record under `docs/design/lean-v2.15/baseline/`.
`page_problems(page_text, baseline_dir)` re-reads those records and returns
one line per disagreement, each starting with the clause id that found it;
`[]` means the page agrees with the records.

Every clause has mutants: a named change to the real page text in memory,
or to an in-memory copy of a record. Each mutant first checks that the
mutation really happened, then checks that the clause it targets reports it
by name. A completeness test makes sure no clause is left without a mutant.

A missing page or record is a failure with a clear message, never a skip.
Standard library only.
"""

import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
KIT_DIR = os.path.join(REPO_ROOT, "docs", "design", "lean-v2.15")
PAGE = os.path.join(KIT_DIR, "BASELINE-v2.14.1.md")
README = os.path.join(KIT_DIR, "README.md")
BASELINE_DIR = os.path.join(KIT_DIR, "baseline")
TOOLS_DIR = HERE
THIS_FILE = os.path.abspath(__file__)

# --------------------------------------------------------------------------
# Page shape
# --------------------------------------------------------------------------

H_HOW = "## How to read this"
H_SUITE = "## Suite"
H_REPLAY = "## Archived replay"
H_SITUATIONS = "## Finalize situations"
H_BYTES = "## Instructions loaded (bytes)"
H_TRACES = "## Files actually loaded (traces)"
H_STEPS = "## Model-run mechanical steps"
H_COST = "## Cost visibility"
H_RECHECK = "## Checking this baseline later"

HEADINGS = (H_HOW, H_SUITE, H_REPLAY, H_SITUATIONS, H_BYTES, H_TRACES,
            H_STEPS, H_COST, H_RECHECK)

# Scopes that are not a whole `## ` section.
HEADLINE = "<headline>"
BYTES_MAIN = "<bytes: before the proxy sub-heading>"
BYTES_PROXY = "<bytes: the proxy sub-part>"

PROXY_SUB_RE = re.compile(r"^### .*proxy.*$", re.I | re.M)

# The three paths the page shows, in page order (keys of the footprint and
# traces records). Their plain names come from the footprint record's labels.
PAGE_PATHS = ("review-plain", "deep-plain", "finalize")

# Step-count parts, in page order, with the plain words the page uses as the
# start of each row's first cell.
STEP_PARTS = (
    ("bash_fences", "Commands in blocks"),
    ("inline_commands", "Commands written inline"),
    ("write_tool_writes", "Files written"),
    ("carried_paste_sites", "Values copied between commands"),
)
STEP_TOTAL_ROW = "Total model-run steps"

TALLY_KEYS = ("commands_run", "values_carried", "writes")

RECHECK_COMMAND = ("python3 docs/design/lean-v2.15/tools/baseline_records.py "
                   "verify --repo .")
RECHECK_OK_LINE = "baseline holds"

VERDICTS = ("**GO**", "**NO-GO**")
VERDICT_LEAD = "The cost note's recommendation, not the decision:"
SETTLED_WORDS_RE = re.compile(r"\b(decided|final|finally|settled|approved)\b",
                              re.I)
COST_PHRASES = (
    "recommendation, not the decision",
    "decision is the owner's",
    "`## Owner decision`",
    "may overrule",
    "accounting work stops",
)

LABEL_OBSERVED = "observed"
LABEL_DECLARED = "declared, not observed"

NUMBER_WORDS = ("zero", "one", "two", "three", "four", "five", "six",
                "seven", "eight", "nine", "ten", "eleven", "twelve")

# --------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------

SUITE_FILE = "suite-v2.14.1.json"
MANIFEST_FILE = "MANIFEST.json"
SITUATIONS_FILE = "finalize-situations-v2.14.1.json"
FOOTPRINT_FILE = "footprint-v2.14.1.json"
TRACES_FILE = "traces-v2.14.1.json"
STEPS_FILE = "steps-v2.14.1.json"

JSON_RECORDS = (("suite", SUITE_FILE), ("manifest", MANIFEST_FILE),
                ("situations", SITUATIONS_FILE), ("footprint", FOOTPRINT_FILE),
                ("traces", TRACES_FILE), ("steps", STEPS_FILE))


class RecordError(Exception):
    """A baseline record is missing or unreadable."""


def _read_text(path, what):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        raise RecordError("%s missing or unreadable: %s (%s)"
                          % (what, path, type(exc).__name__))


def load_records(baseline_dir):
    """Every record the page summarises, as one dict. Raises RecordError
    naming the file when one is missing or not valid JSON."""
    rec = {}
    for key, name in JSON_RECORDS:
        text = _read_text(os.path.join(baseline_dir, name), "baseline record")
        try:
            rec[key] = json.loads(text)
        except ValueError:
            raise RecordError("baseline record is not valid JSON: %s" % name)
    replay = {}
    files = rec["manifest"].get("facts", {}).get("replay_files", {})
    if not files:
        raise RecordError("MANIFEST.json facts hold no replay_files")
    for count, name in sorted(files.items()):
        side = _read_text(os.path.join(baseline_dir, name + ".sha256"),
                          "replay fingerprint")
        replay[count] = {"file": name, "fingerprint": side.strip()}
    rec["replay"] = replay
    rec["situations_sidecar"] = _read_text(
        os.path.join(baseline_dir, SITUATIONS_FILE + ".sha256"),
        "situations fingerprint").strip()
    return rec


def _copy(obj):
    return json.loads(json.dumps(obj))


def _replay_diff(rec):
    """(runs compared, runs differing) from the manifest, or None."""
    m = re.fullmatch(r"runs compared: (\d+), runs differing: (\d+)",
                     rec["manifest"]["facts"].get("replay_diff", ""))
    return (int(m.group(1)), int(m.group(2))) if m else None


def _path_label(rec, key):
    return rec["footprint"]["paths"][key]["label"]


def _out_of_list(rec):
    """[(path label, file, bytes, sessions that read it, sessions)] for every
    file an observed session read that the path's declared list leaves out."""
    out = []
    for key in PAGE_PATHS:
        entry = rec["traces"]["paths"][key]
        observed = entry.get("observed", [])
        found = {}
        for session in observed:
            seen = set()
            for read in session.get("reads", []):
                if read.get("in_declared") or read["path"] in seen:
                    continue
                seen.add(read["path"])
                slot = found.setdefault(read["path"],
                                        [read["bytes_at_baseline"], 0])
                slot[1] += 1
        for path in sorted(found):
            out.append((_path_label(rec, key), path, found[path][0],
                        found[path][1], len(observed)))
    return out


# --------------------------------------------------------------------------
# Page reading helpers
# --------------------------------------------------------------------------

SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|?$")


def section_span(page, heading):
    """(start, end) offsets of the text under `heading` up to the next `## `
    line. heading None: from the top of the page to the first `## ` line.
    None when the heading is absent."""
    pos = 0
    start = 0 if heading is None else None
    for line in page.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if body.startswith("## "):
            if start is not None:
                return (start, pos)
            if body.rstrip() == heading:
                start = pos + len(line)
        pos += len(line)
    return (start, pos) if start is not None else None


def scope_span(page, scope):
    if scope == HEADLINE:
        return section_span(page, None)
    if scope in (BYTES_MAIN, BYTES_PROXY):
        span = section_span(page, H_BYTES)
        if span is None:
            return None
        s, e = span
        m = PROXY_SUB_RE.search(page, s, e)
        cut = m.start() if m else e
        return (s, cut) if scope == BYTES_MAIN else (cut, e)
    return section_span(page, scope)


def scope_text(page, scope):
    span = scope_span(page, scope)
    return page[span[0]:span[1]] if span else ""


def split_cells(line):
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [c.strip() for c in body.split("|")]


def table_rows(text):
    rows = []
    for line in text.splitlines():
        body = line.strip()
        if body.startswith("|") and not SEPARATOR_RE.match(body):
            rows.append(split_cells(body))
    return rows


def bare(cell):
    return cell.replace("*", "").replace("`", "").strip()


def cell_number(cell):
    """The cell as an int when it is only a number (commas allowed)."""
    text = bare(cell).replace(",", "")
    return int(text) if text.isdigit() else None


def find_rows(text, first, prefix=False):
    found = []
    for cells in table_rows(text):
        key = bare(cells[0])
        if key == first or (prefix and key.startswith(first)):
            found.append(cells)
    return found


def figure_re(n):
    alts = sorted({str(n), "{:,}".format(n)}, key=len, reverse=True)
    return re.compile(r"(?<![\d,.])(?:%s)(?!\d|[,.]\d)"
                      % "|".join(re.escape(a) for a in alts))


def phrase_figures(text, word):
    """Every number written directly before `word` (e.g. `3886 passed`)."""
    pattern = r"(?<![\d,.])(\d[\d,]*)\s+%s\b" % re.escape(word)
    return [int(m.group(1).replace(",", "")) for m in re.finditer(pattern, text)]


def _phrase_check(text, word, want, where):
    got = phrase_figures(text, word)
    if not got:
        return ["%s: no '<number> %s'" % (where, word)]
    wrong = sorted(set(g for g in got if g != want))
    if wrong:
        return ["%s: '<number> %s' reads %s, record says %d"
                % (where, word, ", ".join(str(w) for w in wrong), want)]
    return []


# --------------------------------------------------------------------------
# Clauses
# --------------------------------------------------------------------------

def clause_headings(page, rec):
    found = [l.rstrip() for l in page.splitlines() if l.startswith("## ")]
    probs = ["missing heading %r" % h for h in HEADINGS if h not in found]
    for h in HEADINGS:
        if found.count(h) > 1:
            probs.append("heading %r appears more than once" % h)
    order = [h for h in found if h in HEADINGS]
    if not probs and order != list(HEADINGS):
        probs.append("headings out of order: %s" % order)
    return probs


def clause_headline(page, rec):
    text = scope_text(page, HEADLINE)
    probs = []
    short = rec["manifest"]["baseline_commit"][:7]
    if short not in text:
        probs.append("headline lacks the commit %s" % short)
    suite = rec["suite"]
    probs += _phrase_check(text, "passed", suite["passed"], "headline")
    probs += _phrase_check(text, "failed", suite["failed"], "headline")
    diff = _replay_diff(rec)
    if diff is None:
        probs.append("manifest replay_diff is unreadable")
    else:
        probs += _phrase_check(text, "runs", diff[0], "headline")
        probs += _phrase_check(text, "differing", diff[1], "headline")
    count = len(rec["situations"]["situations"])
    word = NUMBER_WORDS[count] if count < len(NUMBER_WORDS) else str(count)
    if not re.search(r"\b%s Finalize situations\b" % word, text):
        probs.append("headline lacks '%s Finalize situations'" % word)
    return probs


def clause_commit(page, rec):
    probs = []
    commit = rec["manifest"]["baseline_commit"]
    others = [("suite", rec["suite"].get("baseline_commit")),
              ("situations", rec["situations"].get("baseline_commit")),
              ("footprint", rec["footprint"].get("baseline_commit")),
              ("traces", rec["traces"].get("baseline_commit")),
              ("steps", rec["steps"].get("rev"))]
    for name, value in others:
        if value != commit:
            probs.append("%s record is pinned to a different commit than the "
                         "manifest" % name)
    if commit not in scope_text(page, H_HOW):
        probs.append("'How to read this' lacks the full commit id %s" % commit)
    return probs


def clause_suite_count(page, rec):
    text = scope_text(page, H_SUITE)
    suite = rec["suite"]
    probs = []
    probs += _phrase_check(text, "passed", suite["passed"], "Suite")
    probs += _phrase_check(text, "failed", suite["failed"], "Suite")
    probs += _phrase_check(text, "skipped", suite["skipped"], "Suite")
    if suite["summary_line"] not in text:
        probs.append("Suite lacks the verbatim summary line")
    return probs


def clause_suite_env(page, rec):
    text = scope_text(page, H_SUITE)
    probs = []
    for key in ("runner", "python", "platform"):
        value = rec["suite"][key]
        if not re.search(r"(?<![\w.])%s(?![\w]|\.\d)" % re.escape(value), text):
            probs.append("Suite lacks the %s %r" % (key, value))
    return probs


def clause_plugins_tree(page, rec):
    tree = rec["suite"]["plugins_tree"]
    probs = []
    if tree != rec["manifest"].get("plugins_tree"):
        probs.append("suite and manifest disagree on the plugin tree id")
    if not re.search(r"(?<![0-9a-f])%s(?![0-9a-f])" % tree,
                     scope_text(page, H_SUITE)):
        probs.append("Suite lacks the plugin tree id %s" % tree)
    return probs


def clause_replay_fingerprints(page, rec):
    text = scope_text(page, H_REPLAY)
    probs = []
    for count, info in sorted(rec["replay"].items()):
        rows = [c for c in table_rows(text)
                if any(bare(cell) == info["file"] for cell in c)]
        if len(rows) != 1:
            probs.append("Archived replay needs one row for %s, found %d"
                         % (info["file"], len(rows)))
            continue
        cells = rows[0]
        if not any(bare(cell) == info["fingerprint"] for cell in cells):
            probs.append("the %s row does not show its fingerprint %s"
                         % (info["file"], info["fingerprint"]))
        if not figure_re(int(count)).search(bare(cells[0])):
            probs.append("the %s row's condition does not say %s private "
                         "recordings" % (info["file"], count))
    return probs


def clause_replay_diff(page, rec):
    text = scope_text(page, H_REPLAY)
    facts = rec["manifest"]["facts"]
    probs = []
    if facts.get("replay_diff", "") not in text or not facts.get("replay_diff"):
        probs.append("Archived replay lacks the verbatim diff figures %r"
                     % facts.get("replay_diff"))
    if facts.get("replay_normalisation", "") not in text \
            or not facts.get("replay_normalisation"):
        probs.append("Archived replay lacks the verbatim removed-line rule")
    return probs


def clause_situations(page, rec):
    text = scope_text(page, H_SITUATIONS)
    sit = rec["situations"]
    probs = []
    if sit.get("sha256") != rec["situations_sidecar"]:
        probs.append("situations record and its .sha256 sidecar disagree")
    for sid in sit["situations"]:
        if "`%s`" % sid not in text:
            probs.append("Finalize situations lacks `%s`" % sid)
    if not re.search(r"(?<![0-9a-f])%s(?![0-9a-f])" % re.escape(sit["sha256"]),
                     text):
        probs.append("Finalize situations lacks the record fingerprint %s"
                     % sit["sha256"])
    return probs


def clause_situation_tallies(page, rec):
    text = scope_text(page, H_SITUATIONS)
    probs = []
    for sid, body in rec["situations"]["situations"].items():
        rows = find_rows(text, sid)
        if len(rows) != 1:
            probs.append("Finalize situations needs one table row for %s, "
                         "found %d" % (sid, len(rows)))
            continue
        cells = rows[0][-len(TALLY_KEYS):]
        for key, cell in zip(TALLY_KEYS, cells):
            if cell_number(cell) != body["tally"][key]:
                probs.append("%s %s reads %r, record says %d"
                             % (sid, key, bare(cell), body["tally"][key]))
    return probs


def _path_rows(text, rec, key):
    return [c for c in find_rows(text, _path_label(rec, key))
            if len(c) >= 3 and not bare(c[1]).endswith(".md")]


def clause_bytes(page, rec):
    text = scope_text(page, BYTES_MAIN)
    probs = []
    for key in PAGE_PATHS:
        want = rec["footprint"]["paths"][key]["total_bytes"]
        rows = _path_rows(text, rec, key)
        if len(rows) != 1:
            probs.append("byte table needs one row for %s, found %d"
                         % (_path_label(rec, key), len(rows)))
        elif cell_number(rows[0][1]) != want:
            probs.append("%s bytes read %r, record says %d"
                         % (_path_label(rec, key), bare(rows[0][1]), want))
    return probs


def clause_file_counts(page, rec):
    text = scope_text(page, BYTES_MAIN)
    probs = []
    for key in PAGE_PATHS:
        want = rec["footprint"]["paths"][key]["file_count"]
        rows = _path_rows(text, rec, key)
        if len(rows) != 1:
            probs.append("byte table needs one row for %s, found %d"
                         % (_path_label(rec, key), len(rows)))
        elif cell_number(rows[0][2]) != want:
            probs.append("%s files read %r, record says %d"
                         % (_path_label(rec, key), bare(rows[0][2]), want))
    return probs


def _proxy_keys(rec):
    return sorted(rec["footprint"]["proxies"]["modes"][PAGE_PATHS[0]])


def clause_proxy_figures(page, rec):
    text = scope_text(page, BYTES_PROXY)
    proxies = rec["footprint"]["proxies"]
    probs = []
    if not text:
        return ["no `### ` sub-heading containing 'proxy' in the bytes section"]
    if proxies["label"] not in text:
        probs.append("proxy sub-part lacks the record's label %r"
                     % proxies["label"])
    keys = _proxy_keys(rec)
    header = find_rows(text, "Path")
    ratios = [k.split("@", 1)[1] for k in keys]
    if len(header) != 1 or len(header[0]) < 1 + len(keys) or not all(
            r in header[0][i + 1] for i, r in enumerate(ratios)):
        probs.append("proxy table header must name the ratios %s in order"
                     % ", ".join(ratios))
    for key in PAGE_PATHS:
        rows = _path_rows(text, rec, key)
        if len(rows) != 1:
            probs.append("proxy table needs one row for %s, found %d"
                         % (_path_label(rec, key), len(rows)))
            continue
        for i, pkey in enumerate(keys):
            want = proxies["modes"][key][pkey]
            if len(rows[0]) <= i + 1 or cell_number(rows[0][i + 1]) != want:
                probs.append("%s %s reads %r, record says %d"
                             % (_path_label(rec, key), pkey,
                                bare(rows[0][i + 1]) if len(rows[0]) > i + 1
                                else "", want))
    return probs


def clause_proxies_apart(page, rec):
    probs = []
    for scope, name in ((BYTES_MAIN, "bytes section before the proxy part"),
                        (H_STEPS, "steps section")):
        for line in scope_text(page, scope).splitlines():
            if re.search(r"\btokens?\b", line, re.I) and "proxy" not in line.lower():
                probs.append("the %s mentions tokens outside a proxy-headed "
                             "line: %r" % (name, line.strip()[:80]))
    return probs


def clause_steps(page, rec):
    text = scope_text(page, H_STEPS)
    want = rec["steps"]["totals"]["model_run_steps"]
    rows = find_rows(text, STEP_TOTAL_ROW, prefix=True)
    if len(rows) != 1:
        return ["steps table needs one %r row, found %d"
                % (STEP_TOTAL_ROW, len(rows))]
    if cell_number(rows[0][1]) != want:
        return ["total model-run steps read %r, record says %d"
                % (bare(rows[0][1]), want)]
    return []


def clause_step_parts(page, rec):
    text = scope_text(page, H_STEPS)
    totals = rec["steps"]["totals"]
    probs = []
    if sum(totals[k] for k, _ in STEP_PARTS) != totals["model_run_steps"]:
        probs.append("steps record: the four parts do not add up to the total")
    for key, words in STEP_PARTS:
        rows = find_rows(text, words, prefix=True)
        if len(rows) != 1:
            probs.append("steps table needs one %r row, found %d"
                         % (words, len(rows)))
        elif cell_number(rows[0][1]) != totals[key]:
            probs.append("%s reads %r, record says %d"
                         % (words, bare(rows[0][1]), totals[key]))
    return probs


def clause_step_judgement(page, rec):
    total = rec["steps"]["totals"]["model_run_steps"]
    phrase = "%d instead of %d" % (total - 1, total)
    if phrase not in scope_text(page, H_STEPS):
        return ["steps section lacks the judgement-call figure %r" % phrase]
    return []


def clause_trace_labels(page, rec):
    text = scope_text(page, H_TRACES)
    probs = []
    for key in PAGE_PATHS:
        entry = rec["traces"]["paths"][key]
        label = _path_label(rec, key)
        if entry["label"] not in (LABEL_OBSERVED, LABEL_DECLARED):
            probs.append("traces record carries an unknown label for %s" % label)
        if entry["label"] == LABEL_DECLARED and not entry.get("gap"):
            probs.append("traces record: %s is declared-only but names no gap"
                         % label)
        rows = _path_rows(text, rec, key)
        if len(rows) != 1:
            probs.append("trace table needs one row for %s, found %d"
                         % (label, len(rows)))
            continue
        cells = rows[0]
        if bare(cells[1]) != entry["label"]:
            probs.append("%s is labelled %r on the page, record says %r"
                         % (label, bare(cells[1]), entry["label"]))
        if len(cells) < 4 or cell_number(cells[2]) != len(entry["observed"]):
            probs.append("%s recorded sessions read %r, record says %d"
                         % (label, bare(cells[2]) if len(cells) > 2 else "",
                            len(entry["observed"])))
        versions = sorted({o["version"] for o in entry["observed"]})
        for version in versions:
            if len(cells) < 4 or version not in cells[3]:
                probs.append("%s row lacks the session version %r"
                             % (label, version))
        if entry["label"] == LABEL_DECLARED and entry.get("gap") \
                and entry["gap"] not in text:
            probs.append("traces section lacks the recorded gap for %s" % label)
    return probs


def clause_trace_extras(page, rec):
    text = scope_text(page, H_TRACES)
    labels = {_path_label(rec, k) for k in PAGE_PATHS}
    rows = [c for c in table_rows(text)
            if bare(c[0]) in labels and len(c) >= 2 and bare(c[1]).endswith(".md")]
    expected = _out_of_list(rec)
    probs = []
    if len(rows) != len(expected):
        probs.append("traces section lists %d out-of-list files, records hold %d"
                     % (len(rows), len(expected)))
    for label, path, nbytes, read_by, sessions in expected:
        match = [c for c in rows if bare(c[0]) == label and bare(c[1]) == path]
        if len(match) != 1:
            probs.append("no single row for %s reading %s" % (label, path))
            continue
        cells = match[0]
        if len(cells) < 4 or cell_number(cells[2]) != nbytes:
            probs.append("%s %s bytes read %r, record says %d"
                         % (label, path, bare(cells[2]) if len(cells) > 2 else "",
                            nbytes))
        want = "%d of %d" % (read_by, sessions)
        if len(cells) < 4 or bare(cells[3]) != want:
            probs.append("%s %s sessions read %r, record says %r"
                         % (label, path, bare(cells[3]) if len(cells) > 3 else "",
                            want))
    return probs


def clause_limits(page, rec):
    probs = []
    situations = scope_text(page, H_SITUATIONS)
    for word in ("macOS", "Linux"):
        if word not in situations:
            probs.append("Finalize situations does not state the %s limit" % word)
    if "score.py" not in scope_text(page, H_REPLAY):
        probs.append("Archived replay does not state that score.py changes "
                     "are not caught by the fingerprint")
    return probs


def clause_no_price(page, rec):
    hits = re.findall(r"\$\s*\d", page)
    return ["the page holds a dollar amount (%d)" % len(hits)] if hits else []


def clause_verdict_labelled(page, rec):
    text = scope_text(page, H_COST)
    probs = ["Cost visibility lacks %r" % p for p in COST_PHRASES if p not in text]
    if not any(l.strip().startswith(VERDICT_LEAD) for l in text.splitlines()):
        probs.append("no line begins %r" % VERDICT_LEAD)
    return probs


def clause_verdict_quoted(page, rec):
    text = scope_text(page, H_COST)
    in_section = [text.count(v) for v in VERDICTS]
    on_page = [page.count(v) for v in VERDICTS]
    if sorted(in_section) != [0, 1]:
        return ["Cost visibility must hold exactly one of %s, holds %s"
                % (" and ".join(VERDICTS), in_section)]
    if on_page != in_section:
        return ["a bold verdict appears outside Cost visibility"]
    lead = [l for l in text.splitlines() if l.strip().startswith(VERDICT_LEAD)]
    if not any(v in l for l in lead for v in VERDICTS):
        return ["the verdict is not on the line that begins %r" % VERDICT_LEAD]
    return []


def clause_verdict_not_settled(page, rec):
    probs = []
    for line in page.splitlines():
        if any(v in line for v in VERDICTS) and SETTLED_WORDS_RE.search(line):
            probs.append("the verdict line calls it %r"
                         % SETTLED_WORDS_RE.search(line).group(0))
    return probs


def clause_recheck_command(page, rec):
    text = scope_text(page, H_RECHECK)
    probs = []
    if RECHECK_COMMAND not in text:
        probs.append("the re-check section lacks %r" % RECHECK_COMMAND)
    if RECHECK_OK_LINE not in text:
        probs.append("the re-check section does not name the %r line"
                     % RECHECK_OK_LINE)
    return probs


CLAUSE_FUNCS = (
    ("headings", clause_headings),
    ("headline", clause_headline),
    ("commit", clause_commit),
    ("suite-count", clause_suite_count),
    ("suite-env", clause_suite_env),
    ("plugins-tree", clause_plugins_tree),
    ("replay-fingerprints", clause_replay_fingerprints),
    ("replay-diff", clause_replay_diff),
    ("situations", clause_situations),
    ("situation-tallies", clause_situation_tallies),
    ("bytes", clause_bytes),
    ("file-counts", clause_file_counts),
    ("proxy-figures", clause_proxy_figures),
    ("proxies-apart", clause_proxies_apart),
    ("steps", clause_steps),
    ("step-parts", clause_step_parts),
    ("step-judgement", clause_step_judgement),
    ("trace-labels", clause_trace_labels),
    ("trace-extras", clause_trace_extras),
    ("limits", clause_limits),
    ("no-price", clause_no_price),
    ("verdict-labelled", clause_verdict_labelled),
    ("verdict-quoted", clause_verdict_quoted),
    ("verdict-not-settled", clause_verdict_not_settled),
    ("recheck-command", clause_recheck_command),
)
CLAUSES = tuple(cid for cid, _ in CLAUSE_FUNCS)


def problems_for(page_text, rec):
    out = []
    for cid, func in CLAUSE_FUNCS:
        out.extend("%s: %s" % (cid, p) for p in func(page_text, rec))
    return out


def page_problems(page_text, baseline_dir):
    """[] when the page agrees with the records in `baseline_dir`; otherwise
    one line per disagreement, each starting with its clause id."""
    return problems_for(page_text, load_records(baseline_dir))


# --------------------------------------------------------------------------
# README
# --------------------------------------------------------------------------

def kit_tools(tools_dir):
    return sorted(n for n in os.listdir(tools_dir)
                  if n.endswith(".py") and not n.startswith("test_"))


def readme_problems(readme_text, tools_dir):
    rows = table_rows(readme_text)
    listed = {bare(c[0]) for c in rows if c}
    return ["readme: tool %s has no row in the tool table" % name
            for name in kit_tools(tools_dir) if name not in listed]


# --------------------------------------------------------------------------
# Mutants
# --------------------------------------------------------------------------

class MutantError(Exception):
    """A mutant's needle was not found in the text it should change."""


def swap_in_scope(page, scope, old, new):
    span = scope_span(page, scope)
    if span is None or old not in page[span[0]:span[1]]:
        raise MutantError("%r not found in %s" % (old, scope))
    s, e = span
    return page[:s] + page[s:e].replace(old, new) + page[e:]


def swap_everywhere(page, old, new):
    if old not in page:
        raise MutantError("%r not on the page" % old)
    return page.replace(old, new)


def _bumped(cell_text):
    m = re.search(r"\d[\d,]*", cell_text)
    if not m:
        raise MutantError("no number in %r" % cell_text)
    raw = m.group(0)
    n = int(raw.replace(",", "")) + 1
    new = "{:,}".format(n) if "," in raw else str(n)
    return cell_text[:m.start()] + new + cell_text[m.end():]


def bump_row_cell(page, scope, first, col, prefix=False, pick=None):
    span = scope_span(page, scope)
    if span is None:
        raise MutantError("no %s" % scope)
    s, e = span
    pos = s
    for line in page[s:e].splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if body.strip().startswith("|") and not SEPARATOR_RE.match(body.strip()):
            cells = split_cells(body)
            key = bare(cells[0])
            if (key == first or (prefix and key.startswith(first))) and \
                    (pick is None or pick(cells)):
                cells[col] = _bumped(cells[col])
                new = "| " + " | ".join(cells) + " |" + line[len(body):]
                return page[:pos] + new + page[pos + len(line):]
        pos += len(line)
    raise MutantError("no row %r in %s" % (first, scope))


def set_row_cell(page, scope, first, col, value, pick=None):
    span = scope_span(page, scope)
    if span is None:
        raise MutantError("no %s" % scope)
    s, e = span
    pos = s
    for line in page[s:e].splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if body.strip().startswith("|") and not SEPARATOR_RE.match(body.strip()):
            cells = split_cells(body)
            if bare(cells[0]) == first and (pick is None or pick(cells)):
                if cells[col] == value:
                    raise MutantError("cell already %r" % value)
                cells[col] = value
                new = "| " + " | ".join(cells) + " |" + line[len(body):]
                return page[:pos] + new + page[pos + len(line):]
        pos += len(line)
    raise MutantError("no row %r in %s" % (first, scope))


def drop_line(page, needle):
    lines = page.splitlines(keepends=True)
    hit = [i for i, l in enumerate(lines) if needle in l]
    if not hit:
        raise MutantError("no line holds %r" % needle)
    del lines[hit[0]]
    return "".join(lines)


def bump_phrase(page, scope, word):
    span = scope_span(page, scope)
    if span is None:
        raise MutantError("no %s" % scope)
    s, e = span
    m = re.compile(r"(?<![\d,.])(\d[\d,]*)(\s+%s\b)" % re.escape(word)).search(
        page, s, e)
    if not m:
        raise MutantError("no '<number> %s' in %s" % (word, scope))
    return page[:m.start(1)] + _bumped(m.group(1)) + page[m.end(1):]


def flip_char(value):
    """`value` with its last character changed (hex-safe)."""
    last = value[-1]
    return value[:-1] + ("0" if last != "0" else "1")


def _not_md(cells):
    return not bare(cells[1]).endswith(".md")


def _the_verdict(page):
    held = [v for v in VERDICTS if v in page]
    if len(held) != 1:
        raise MutantError("the page holds %d bold verdicts" % len(held))
    return held[0]


def _page_mutants():
    """[(clause, name, fn(page, rec) -> mutated page)]"""
    m = []

    def add(clause, name, fn):
        m.append((clause, name, fn))

    add("headings", "heading renamed",
        lambda p, r: swap_everywhere(p, "\n## Suite\n", "\n## Test suite\n"))
    add("headings", "two headings swapped",
        lambda p, r: swap_everywhere(
            swap_everywhere(swap_everywhere(p, "\n## Suite\n", "\n## @@\n"),
                            "\n## Archived replay\n", "\n## Suite\n"),
            "\n## @@\n", "\n## Archived replay\n"))

    add("headline", "passed figure plus one",
        lambda p, r: bump_phrase(p, HEADLINE, "passed"))
    add("headline", "failed figure plus one",
        lambda p, r: bump_phrase(p, HEADLINE, "failed"))
    add("headline", "replay runs plus one",
        lambda p, r: bump_phrase(p, HEADLINE, "runs"))
    add("headline", "replay differing plus one",
        lambda p, r: bump_phrase(p, HEADLINE, "differing"))
    add("headline", "situation count word changed",
        lambda p, r: swap_in_scope(p, HEADLINE, "five Finalize situations",
                                   "four Finalize situations"))
    add("headline", "short commit changed",
        lambda p, r: swap_in_scope(p, HEADLINE,
                                   r["manifest"]["baseline_commit"][:7],
                                   flip_char(r["manifest"]["baseline_commit"][:7])))

    add("commit", "full commit changed",
        lambda p, r: swap_in_scope(p, H_HOW, r["manifest"]["baseline_commit"],
                                   flip_char(r["manifest"]["baseline_commit"])))

    add("suite-count", "passed figure plus one",
        lambda p, r: bump_phrase(p, H_SUITE, "passed"))
    add("suite-count", "failed figure plus one",
        lambda p, r: bump_phrase(p, H_SUITE, "failed"))
    add("suite-count", "skipped figure plus one",
        lambda p, r: bump_phrase(p, H_SUITE, "skipped"))
    add("suite-count", "subtests figure in the summary line plus one",
        lambda p, r: swap_in_scope(p, H_SUITE, "%d subtests" % r["suite"]["subtests_passed"],
                                   "%d subtests" % (r["suite"]["subtests_passed"] + 1)))

    for key in ("runner", "python", "platform"):
        add("suite-env", "%s changed" % key,
            lambda p, r, key=key: swap_in_scope(p, H_SUITE, r["suite"][key],
                                                r["suite"][key] + "9"))

    add("plugins-tree", "tree id changed by one character",
        lambda p, r: swap_in_scope(p, H_SUITE, r["suite"]["plugins_tree"],
                                   flip_char(r["suite"]["plugins_tree"])))

    for count in ("0", "12"):
        add("replay-fingerprints", "fingerprint for %s recordings changed" % count,
            lambda p, r, c=count: swap_in_scope(
                p, H_REPLAY, r["replay"][c]["fingerprint"],
                flip_char(r["replay"][c]["fingerprint"])))
    add("replay-fingerprints", "the two fingerprints swapped",
        lambda p, r: swap_in_scope(
            swap_in_scope(swap_in_scope(p, H_REPLAY, r["replay"]["0"]["fingerprint"], "@@"),
                          H_REPLAY, r["replay"]["12"]["fingerprint"],
                          r["replay"]["0"]["fingerprint"]),
            H_REPLAY, "@@", r["replay"]["12"]["fingerprint"]))
    add("replay-fingerprints", "recording count in the condition changed",
        lambda p, r: bump_row_cell(
            p, H_REPLAY, "12 private recordings present", 0, prefix=True))

    add("replay-diff", "runs compared plus one",
        lambda p, r: swap_in_scope(p, H_REPLAY,
                                   "runs compared: %d" % _replay_diff(r)[0],
                                   "runs compared: %d" % (_replay_diff(r)[0] + 1)))
    add("replay-diff", "removed-line rule changed",
        lambda p, r: swap_in_scope(p, H_REPLAY, "generated( \\(UTC\\))?",
                                   "generated"))

    add("situations", "one situation id removed",
        lambda p, r: swap_in_scope(p, H_SITUATIONS, "`one-rebuild`", "`one-retry`"))
    add("situations", "record fingerprint changed",
        lambda p, r: swap_in_scope(p, H_SITUATIONS, r["situations"]["sha256"],
                                   flip_char(r["situations"]["sha256"])))

    for sid in ("clean-close", "card-first", "one-rebuild", "refused-close",
                "fresh-shell-restart"):
        for i, key in enumerate(TALLY_KEYS):
            add("situation-tallies", "%s %s plus one" % (sid, key),
                lambda p, r, sid=sid, col=i - len(TALLY_KEYS): bump_row_cell(
                    p, H_SITUATIONS, sid, col))

    for key in PAGE_PATHS:
        add("bytes", "%s bytes plus one" % key,
            lambda p, r, key=key: bump_row_cell(p, BYTES_MAIN, _path_label(r, key),
                                                1, pick=_not_md))
        add("file-counts", "%s files plus one" % key,
            lambda p, r, key=key: bump_row_cell(p, BYTES_MAIN, _path_label(r, key),
                                                2, pick=_not_md))
        for i in (1, 2):
            add("proxy-figures", "%s proxy column %d plus one" % (key, i),
                lambda p, r, key=key, i=i: bump_row_cell(
                    p, BYTES_PROXY, _path_label(r, key), i, pick=_not_md))
    add("proxy-figures", "proxy label removed",
        lambda p, r: swap_in_scope(p, BYTES_PROXY, r["footprint"]["proxies"]["label"],
                                   "proxy"))
    add("proxy-figures", "ratio columns swapped in the header",
        lambda p, r: swap_in_scope(swap_in_scope(swap_in_scope(
            p, BYTES_PROXY, "2.7", "@@"), BYTES_PROXY, "3.5", "2.7"),
            BYTES_PROXY, "@@", "3.5"))

    add("proxies-apart", "tokens added to the byte table heading row",
        lambda p, r: swap_in_scope(p, BYTES_MAIN, "| Bytes |", "| Bytes (tokens) |"))
    add("proxies-apart", "tokens added to the steps section",
        lambda p, r: swap_in_scope(p, H_STEPS, "| Step kind |",
                                   "| Step kind (tokens) |"))

    add("steps", "total plus one",
        lambda p, r: bump_row_cell(p, H_STEPS, STEP_TOTAL_ROW, 1, prefix=True))
    for key, words in STEP_PARTS:
        add("step-parts", "%s plus one" % key,
            lambda p, r, words=words: bump_row_cell(p, H_STEPS, words, 1,
                                                    prefix=True))
    add("step-judgement", "judgement figure changed",
        lambda p, r: swap_in_scope(
            p, H_STEPS,
            "%d instead of" % (r["steps"]["totals"]["model_run_steps"] - 1),
            "%d instead of" % (r["steps"]["totals"]["model_run_steps"] - 2)))

    add("trace-labels", "declared, not observed relabelled observed",
        lambda p, r: swap_in_scope(p, H_TRACES, LABEL_DECLARED, LABEL_OBSERVED))
    add("trace-labels", "plain review session count plus one",
        lambda p, r: bump_row_cell(p, H_TRACES, _path_label(r, "review-plain"), 2,
                                   pick=_not_md))
    add("trace-labels", "Finalize session version changed",
        lambda p, r: set_row_cell(p, H_TRACES, _path_label(r, "finalize"), 3,
                                  "2.14.1 (smoke session)", pick=_not_md))
    add("trace-labels", "deep review gap removed",
        lambda p, r: swap_in_scope(p, H_TRACES,
                                   r["traces"]["paths"]["deep-plain"]["gap"], "-"))

    for label, path in (("plain review", "phases/review/50-fix-loop.md"),
                        ("Finalize", "templates/review-md-schema.md")):
        add("trace-extras", "%s bytes plus one" % path,
            lambda p, r, label=label, path=path: bump_row_cell(
                p, H_TRACES, label, 2, pick=lambda c, path=path: bare(c[1]) == path))
        add("trace-extras", "%s session count changed" % path,
            lambda p, r, label=label, path=path: bump_row_cell(
                p, H_TRACES, label, 3, pick=lambda c, path=path: bare(c[1]) == path))
    add("trace-extras", "one out-of-list row removed",
        lambda p, r: drop_line(p, "`templates/output-format.md`"))

    add("limits", "macOS-only note removed",
        lambda p, r: swap_in_scope(p, H_SITUATIONS, "macOS", "one machine"))
    add("limits", "score.py note removed",
        lambda p, r: swap_in_scope(p, H_REPLAY, "score.py", "the scorer"))

    add("no-price", "a dollar amount added",
        lambda p, r: swap_in_scope(p, H_COST, VERDICT_LEAD,
                                   "At about $5 a run. " + VERDICT_LEAD))

    for phrase in COST_PHRASES:
        add("verdict-labelled", "%r removed" % phrase,
            lambda p, r, phrase=phrase: swap_in_scope(p, H_COST, phrase, "-"))

    add("verdict-quoted", "verdict removed",
        lambda p, r: swap_in_scope(p, H_COST, _the_verdict(p),
                                   _the_verdict(p).strip("*")))
    add("verdict-quoted", "both verdicts present",
        lambda p, r: swap_in_scope(p, H_COST, _the_verdict(p),
                                   "**GO** / **NO-GO**"))
    add("verdict-quoted", "verdict repeated outside Cost visibility",
        lambda p, r: swap_in_scope(p, H_RECHECK, RECHECK_OK_LINE,
                                   RECHECK_OK_LINE + " " + _the_verdict(p)))

    add("verdict-not-settled", "verdict called settled",
        lambda p, r: swap_in_scope(p, H_COST, _the_verdict(p),
                                   _the_verdict(p) + " (settled)"))

    add("recheck-command", "command changed",
        lambda p, r: swap_in_scope(p, H_RECHECK, "baseline_records.py verify",
                                   "baseline_records.py check"))
    add("recheck-command", "success line removed",
        lambda p, r: swap_in_scope(p, H_RECHECK, RECHECK_OK_LINE, "ok"))
    return m


def _record_mutants():
    """[(clause, name, fn(rec) -> None, mutating a copy in place)]"""
    m = []

    def add(clause, name, fn):
        m.append((clause, name, fn))

    def inc(d, k):
        d[k] += 1

    add("headline", "suite passed plus one", lambda r: inc(r["suite"], "passed"))
    add("suite-count", "suite passed plus one", lambda r: inc(r["suite"], "passed"))
    add("suite-count", "suite failed plus one", lambda r: inc(r["suite"], "failed"))
    add("suite-count", "suite skipped plus one", lambda r: inc(r["suite"], "skipped"))
    add("suite-count", "summary line changed",
        lambda r: r["suite"].__setitem__("summary_line",
                                         r["suite"]["summary_line"] + " "))
    add("suite-env", "python changed",
        lambda r: r["suite"].__setitem__("python", "3.12.13"))
    add("plugins-tree", "tree id changed",
        lambda r: r["suite"].__setitem__("plugins_tree",
                                         flip_char(r["suite"]["plugins_tree"])))
    add("commit", "steps record pinned elsewhere",
        lambda r: r["steps"].__setitem__("rev", flip_char(r["steps"]["rev"])))
    add("headline", "replay runs compared changed",
        lambda r: r["manifest"]["facts"].__setitem__(
            "replay_diff", "runs compared: 171, runs differing: 0"))
    add("replay-diff", "replay runs compared changed",
        lambda r: r["manifest"]["facts"].__setitem__(
            "replay_diff", "runs compared: 171, runs differing: 0"))
    add("replay-diff", "removed-line rule changed",
        lambda r: r["manifest"]["facts"].__setitem__(
            "replay_normalisation", r["manifest"]["facts"]["replay_normalisation"] + "."))
    for count in ("0", "12"):
        add("replay-fingerprints", "fingerprint for %s recordings changed" % count,
            lambda r, c=count: r["replay"][c].__setitem__(
                "fingerprint", flip_char(r["replay"][c]["fingerprint"])))
    add("situations", "record fingerprint changed",
        lambda r: r["situations"].__setitem__(
            "sha256", flip_char(r["situations"]["sha256"])))
    add("situations", "sidecar fingerprint changed",
        lambda r: r.__setitem__("situations_sidecar",
                                flip_char(r["situations_sidecar"])))
    for sid in ("clean-close", "card-first", "one-rebuild", "refused-close",
                "fresh-shell-restart"):
        for key in TALLY_KEYS:
            add("situation-tallies", "%s %s plus one" % (sid, key),
                lambda r, sid=sid, key=key: inc(
                    r["situations"]["situations"][sid]["tally"], key))
    for key in PAGE_PATHS:
        add("bytes", "%s bytes plus one" % key,
            lambda r, key=key: inc(r["footprint"]["paths"][key], "total_bytes"))
        add("file-counts", "%s files plus one" % key,
            lambda r, key=key: inc(r["footprint"]["paths"][key], "file_count"))
        for pkey in ("tokens@2.7", "tokens@3.5"):
            add("proxy-figures", "%s %s plus one" % (key, pkey),
                lambda r, key=key, pkey=pkey: inc(
                    r["footprint"]["proxies"]["modes"][key], pkey))
    add("steps", "total plus one",
        lambda r: inc(r["steps"]["totals"], "model_run_steps"))
    add("step-judgement", "total plus one",
        lambda r: inc(r["steps"]["totals"], "model_run_steps"))
    for key, _words in STEP_PARTS:
        add("step-parts", "%s plus one" % key,
            lambda r, key=key: inc(r["steps"]["totals"], key))
    add("trace-labels", "deep review relabelled observed",
        lambda r: r["traces"]["paths"]["deep-plain"].__setitem__("label",
                                                                 LABEL_OBSERVED))
    add("trace-labels", "one plain review session dropped",
        lambda r: r["traces"]["paths"]["review-plain"]["observed"].pop())
    add("trace-labels", "deep review gap changed",
        lambda r: r["traces"]["paths"]["deep-plain"].__setitem__(
            "gap", r["traces"]["paths"]["deep-plain"]["gap"] + "."))
    add("trace-extras", "out-of-list file bytes changed",
        lambda r: [rd.__setitem__("bytes_at_baseline", rd["bytes_at_baseline"] + 1)
                   for rd in r["traces"]["paths"]["finalize"]["observed"][0]["reads"]
                   if not rd["in_declared"]])
    add("trace-extras", "a declared file marked out-of-list",
        lambda r: r["traces"]["paths"]["finalize"]["observed"][0]["reads"][0]
        .__setitem__("in_declared", False))
    return m


PAGE_MUTANTS = _page_mutants()
RECORD_MUTANTS = _record_mutants()


def uncovered_clauses(page_mutants):
    """Clauses with no page mutant in `page_mutants`."""
    covered = {c for c, _n, _f in page_mutants}
    return [c for c in CLAUSES if c not in covered]


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

def _read_page():
    if not os.path.isfile(PAGE):
        raise AssertionError("baseline page missing: %s — write "
                             "BASELINE-v2.14.1.md from the committed records"
                             % os.path.relpath(PAGE, REPO_ROOT))
    with open(PAGE, encoding="utf-8") as fh:
        return fh.read()


class LockCase(unittest.TestCase):
    def assert_holds(self, check, *texts):
        self.assertEqual(check(*texts), [])

    def assert_trips(self, check, clause, *texts):
        problems = check(*texts)
        self.assertNotEqual(problems, [])
        self.assertTrue(any(p.startswith(clause + ":") for p in problems),
                        "%s not reported by name: %s" % (clause, problems))


class TestPageMatchesRecords(LockCase):
    def setUp(self):
        self.page = _read_page()
        self.rec = load_records(BASELINE_DIR)

    def test_page_holds(self):
        self.assert_holds(page_problems, self.page, BASELINE_DIR)

    def test_every_problem_names_a_clause(self):
        mutant = "\n".join(l for l in self.page.splitlines()
                           if not l.startswith("|"))
        problems = problems_for(mutant, self.rec)
        self.assertNotEqual(problems, [])
        for line in problems:
            self.assertIn(line.split(":", 1)[0], CLAUSES, line)

    def _run_page_mutants(self, clause):
        mutants = [x for x in PAGE_MUTANTS if x[0] == clause]
        self.assertTrue(mutants, "no page mutant for %s" % clause)
        for _c, name, fn in mutants:
            with self.subTest(clause=clause, mutant=name):
                mutant = fn(self.page, self.rec)
                self.assertNotEqual(mutant, self.page, "mutation did not happen")
                self.assert_trips(problems_for, clause, mutant, self.rec)

    def _run_record_mutants(self, clause):
        for _c, name, fn in [x for x in RECORD_MUTANTS if x[0] == clause]:
            with self.subTest(clause=clause, record_mutant=name):
                rec = _copy(self.rec)
                fn(rec)
                self.assertNotEqual(json.dumps(rec, sort_keys=True),
                                    json.dumps(self.rec, sort_keys=True),
                                    "record mutation did not happen")
                self.assert_trips(problems_for, clause, self.page, rec)

    def _clause(self, clause):
        self._run_page_mutants(clause)
        self._run_record_mutants(clause)

    def test_headings(self):
        self._clause("headings")

    def test_headline(self):
        self._clause("headline")

    def test_commit(self):
        self._clause("commit")

    def test_suite_count(self):
        self._clause("suite-count")

    def test_suite_env(self):
        self._clause("suite-env")

    def test_plugins_tree(self):
        self._clause("plugins-tree")

    def test_replay_fingerprints(self):
        self._clause("replay-fingerprints")

    def test_replay_diff(self):
        self._clause("replay-diff")

    def test_situations(self):
        self._clause("situations")

    def test_situation_tallies(self):
        self._clause("situation-tallies")

    def test_bytes(self):
        self._clause("bytes")

    def test_file_counts(self):
        self._clause("file-counts")

    def test_proxy_figures(self):
        self._clause("proxy-figures")

    def test_proxies_apart(self):
        self._clause("proxies-apart")

    def test_steps(self):
        self._clause("steps")

    def test_step_parts(self):
        self._clause("step-parts")

    def test_step_judgement(self):
        self._clause("step-judgement")

    def test_trace_labels(self):
        self._clause("trace-labels")

    def test_trace_extras(self):
        self._clause("trace-extras")

    def test_limits(self):
        self._clause("limits")

    def test_no_price(self):
        self.assertNotIn("$5", self.page)
        mutant = PAGE_MUTANTS[[x[1] for x in PAGE_MUTANTS].index(
            "a dollar amount added")][2](self.page, self.rec)
        self.assertIn("$5", mutant)
        self._clause("no-price")

    def test_verdict_labelled(self):
        self._clause("verdict-labelled")

    def test_verdict_quoted(self):
        self._clause("verdict-quoted")

    def test_verdict_not_settled(self):
        self._clause("verdict-not-settled")

    def test_recheck_command(self):
        self._clause("recheck-command")


class TestCompleteness(unittest.TestCase):
    def test_clause_ids_unique(self):
        self.assertEqual(len(CLAUSES), len(set(CLAUSES)))

    def test_every_clause_has_a_test_method(self):
        names = set(dir(TestPageMatchesRecords))
        for clause in CLAUSES:
            self.assertIn("test_" + clause.replace("-", "_"), names, clause)

    def test_every_clause_has_a_page_mutant(self):
        self.assertEqual(uncovered_clauses(PAGE_MUTANTS), [])

    def test_every_mutant_names_a_known_clause(self):
        for clause, name, _f in PAGE_MUTANTS + RECORD_MUTANTS:
            self.assertIn(clause, CLAUSES, name)

    def test_break_dropping_a_clause_mutants_is_reported(self):
        for clause in CLAUSES:
            with self.subTest(clause=clause):
                table = [x for x in PAGE_MUTANTS if x[0] != clause]
                self.assertLess(len(table), len(PAGE_MUTANTS))
                self.assertEqual(uncovered_clauses(table), [clause])


class TestMissingInputs(unittest.TestCase):
    def test_missing_record_dir_raises_with_its_name(self):
        missing = os.path.join(BASELINE_DIR, "no-such-folder")
        with self.assertRaises(RecordError) as ctx:
            page_problems("", missing)
        self.assertIn(SUITE_FILE, str(ctx.exception))


class TestReadme(LockCase):
    def setUp(self):
        if not os.path.isfile(README):
            raise AssertionError("kit README missing: %s"
                                 % os.path.relpath(README, REPO_ROOT))
        with open(README, encoding="utf-8") as fh:
            self.text = fh.read()

    def test_every_tool_is_listed(self):
        self.assertGreater(len(kit_tools(TOOLS_DIR)), 0)
        self.assert_holds(readme_problems, self.text, TOOLS_DIR)

    def test_mutant_tool_row_removed(self):
        for name in kit_tools(TOOLS_DIR):
            with self.subTest(tool=name):
                row = "| `%s` |" % name
                self.assertIn(row, self.text)
                mutant = drop_line(self.text, row)
                self.assertNotEqual(mutant, self.text)
                problems = readme_problems(mutant, TOOLS_DIR)
                self.assertEqual(problems,
                                 ["readme: tool %s has no row in the tool table"
                                  % name])


class TestImportSet(unittest.TestCase):
    def _source(self):
        with open(THIS_FILE, encoding="utf-8") as fh:
            return fh.read()

    def test_module_level_imports(self):
        names = set(re.findall(r"^(?:import|from)\s+([\w.]+)", self._source(),
                               re.M))
        self.assertTrue(names <= {"json", "os", "re", "sys", "unittest"}, names)

    def test_reads_nothing_under_the_phase_records_folder(self):
        folder = "".join([".", "planning"])
        self.assertNotIn(folder, self._source())


if __name__ == "__main__":
    unittest.main()
