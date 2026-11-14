"""CI guard for the tests the offline suite leaves out or sees skip.

Left-out tests (owner ruling D-18). These five cannot pass on GitHub's Linux
machines without changing plugin files: three replay tests read private
session recordings, and two footprint tests assert the Mac `wc` behaviour.
They keep running on the owner's Mac at every release gate. Any other
Linux-only failure is not covered by this list and goes back to the owner.

Skipped tests (owner ruling D-20). Some tests skip themselves on the runner
through their own built-in conditions (a replay test that needs private
recordings absent from a linked worktree, a lane-archive test that needs a
sandbox temp root). The recorded tests keep running on the owner's Mac at
every release gate, where the baseline has 0 skips. Any skip not on the
recorded list stops work and goes back to the owner. Nothing here adds a
skip: this script only compares.

Subcommands (exit 0 clean, 1 violation, 2 usage or unusable input):

    python3 -I .github/scripts/left_out_guard.py check-list <list file>
    python3 -I .github/scripts/left_out_guard.py args <list file>
    python3 -I .github/scripts/left_out_guard.py check-log <suite log>
    python3 -I .github/scripts/left_out_guard.py check-skips <junit xml> <suite log>

check-list  the list file must hold exactly RECORDED_FIVE (any order, blank
            lines ignored, no duplicates, nothing else).
args        runs check-list, then prints one `--deselect=<id>` per id in
            RECORDED_FIVE order. The ids come from the constant, never from
            the file text.
check-log   the last pytest summary line must show exactly 5 deselected and
            no failed or error count, so an id that matches no real test is
            caught.
check-skips reads pytest's --junitxml result file, prints every observed skip
            as `OBSERVED-SKIP<TAB>id<TAB>reason`, and requires the set of
            (test id, reason) pairs to equal RECORDED_SKIPS and the log's
            skipped count to equal the result file's.

I/O: stdlib only, imports exactly {re, sys, xml}. Messages go to stderr in
caps ending `— STOPPING`; the exit code carries the verdict.
"""

import re
import sys
import xml.etree.ElementTree as ElementTree

RECORDED_FIVE = (
    "plugins/vibe-check/scripts/test_replay.py::TestPhase53SameLineRegressionCases::test_a2_pair_sits_on_adjacent_lines_of_one_statement",
    "plugins/vibe-check/scripts/test_replay.py::TestPhase53SameLineRegressionCases::test_off_line_credit_mutation_trips",
    "plugins/vibe-check/scripts/test_replay.py::TestPhase53SameLineRegressionCases::test_pre_same_line_scorer_gave_critical_100",
    "plugins/vibe-check/scripts/test_footprint.py::TestWordCountLocaleDrift::test_c_locale_wc_matches_the_recorded_number",
    "plugins/vibe-check/scripts/test_footprint.py::TestWordCountLocaleDrift::test_utf8_locale_wc_is_the_plans_figure_and_differs_by_two",
)

# The tests that skip themselves on the runner, as (test id, reason) pairs.
# None means not yet recorded: check-skips then always exits 1 after printing
# what it saw, so the runner's first run is a recording run, never a green
# run. The printed set is copied here (only if every entry passes
# skip_list_problems), and only a later run on that pinned commit can be
# called green. An empty tuple means "recorded: no skips expected".
RECORDED_SKIPS = None

# The only skip reasons a recorded entry may carry, one per approved file.
# Each is the exact string its test file passes to skipIf / skipTest.
APPROVED_SKIP_REASONS = (
    ("plugins/vibe-check/scripts/test_replay.py::",
     "Phase-40 transcripts are local-only (gitignored); "
     "a linked worktree has none to recover from"),
    ("plugins/vibe-check/scripts/test_lanearchive.py::",
     "no sandbox temp root on this machine"),
)

MAX_RESULT_BYTES = 50 * 1024 * 1024
PLUGIN_CLASSNAME_PREFIX = "plugins.vibe-check.scripts."
PLUGIN_PATH_PREFIX = "plugins/vibe-check/scripts/"

_SUMMARY_RE = re.compile(r"\d+ passed")
_DESELECT5_RE = re.compile(r"(?<!\d)5 deselected\b")
_FAILURE_RE = re.compile(r"\b(failed|errors?)\b")
_SKIPPED_RE = re.compile(r"(?<![\w-])(\d+) skipped\b")


class UnusableInput(Exception):
    pass


def _stop(message, details=()):
    for line in details:
        sys.stderr.write(line + "\n")
    sys.stderr.write(message + " — STOPPING\n")


def _read_text(path, what):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise UnusableInput("CANNOT READ %s %s (%s)" % (what, path, type(exc).__name__))


# ---------------------------------------------------------------- left-out list

def list_problems(text):
    """Return one line per difference between the list text and RECORDED_FIVE."""
    entries = [line.strip() for line in text.splitlines() if line.strip()]
    recorded = set(RECORDED_FIVE)
    problems = []
    seen = set()
    for entry in entries:
        if entry in seen:
            problems.append("duplicated %s" % entry)
        seen.add(entry)
        if entry not in recorded:
            problems.append("extra %s" % entry)
    for entry in RECORDED_FIVE:
        if entry not in seen:
            problems.append("missing %s" % entry)
    if len(entries) != len(RECORDED_FIVE) and not problems:
        problems.append("count %d, expected %d" % (len(entries), len(RECORDED_FIVE)))
    return problems


def _check_list(path):
    problems = list_problems(_read_text(path, "LEFT-OUT LIST"))
    if problems:
        _stop("LEFT-OUT LIST DIFFERS FROM THE RECORDED FIVE", problems)
        return 1
    return 0


def cmd_check_list(path):
    code = _check_list(path)
    if code == 0:
        sys.stdout.write("left-out list matches the recorded five\n")
    return code


def cmd_args(path):
    code = _check_list(path)
    if code != 0:
        return code
    for test_id in RECORDED_FIVE:
        sys.stdout.write("--deselect=%s\n" % test_id)
    return 0


# ---------------------------------------------------------------- suite log

def summary_line(text):
    """The last pytest summary line (the last line holding `<n> passed`), or None."""
    found = None
    for line in text.splitlines():
        if _SUMMARY_RE.search(line):
            found = line
    return found


def cmd_check_log(path):
    line = summary_line(_read_text(path, "SUITE LOG"))
    if line is None:
        _stop("DESELECT COUNT IS NOT 5", ["no pytest summary line in %s" % path])
        return 1
    if _FAILURE_RE.search(line):
        _stop("SUITE LOG SHOWS A FAILURE", ["summary: %s" % line.strip()])
        return 1
    if not _DESELECT5_RE.search(line):
        _stop("DESELECT COUNT IS NOT 5", ["summary: %s" % line.strip()])
        return 1
    sys.stdout.write("suite log: 5 deselected, no failure (%s)\n" % line.strip())
    return 0


# ---------------------------------------------------------------- skips

def _test_id(classname, name):
    if classname.startswith(PLUGIN_CLASSNAME_PREFIX):
        rest = classname[len(PLUGIN_CLASSNAME_PREFIX):]
        module, _, cls = rest.partition(".")
        if module and "." not in cls:
            path = PLUGIN_PATH_PREFIX + module + ".py"
            return "%s::%s::%s" % (path, cls, name) if cls else "%s::%s" % (path, name)
    return "%s::%s" % (classname, name)


def observed_skips(xml_path):
    """Sorted (test id, reason) pairs for every skipped testcase in the result file.

    Raises UnusableInput for a missing, oversized or unparseable file, or one
    with no testcase elements at all.
    """
    try:
        with open(xml_path, "rb") as fh:
            data = fh.read(MAX_RESULT_BYTES + 1)
    except OSError as exc:
        raise UnusableInput("CANNOT READ RESULT FILE %s (%s)" % (xml_path, type(exc).__name__))
    if len(data) > MAX_RESULT_BYTES:
        raise UnusableInput("RESULT FILE OVER %d BYTES: %s" % (MAX_RESULT_BYTES, xml_path))
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        raise UnusableInput("CANNOT PARSE RESULT FILE %s (%s)" % (xml_path, exc))
    cases = list(root.iter("testcase"))
    if not cases:
        raise UnusableInput("RESULT FILE HOLDS NO TEST CASES: %s" % xml_path)
    pairs = []
    for case in cases:
        skipped = case.find("skipped")
        if skipped is None:
            continue
        pairs.append((_test_id(case.get("classname", ""), case.get("name", "")),
                      skipped.get("message", "")))
    return sorted(pairs)


def skip_list_problems(recorded):
    """Class rule on a recorded skip list; [] when it is acceptable.

    None (not yet recorded) and () are acceptable. Each entry must be a
    (test id, reason) pair under one of the APPROVED_SKIP_REASONS files,
    carrying exactly that file's reason, not one of RECORDED_FIVE, and not
    repeated.
    """
    if recorded is None:
        return []
    problems = []
    seen = set()
    for entry in recorded:
        if not (isinstance(entry, tuple) and len(entry) == 2
                and all(isinstance(x, str) for x in entry)):
            problems.append("not a (test id, reason) pair: %r" % (entry,))
            continue
        test_id, reason = entry
        if test_id in seen:
            problems.append("duplicated %s" % test_id)
        seen.add(test_id)
        if test_id in RECORDED_FIVE:
            problems.append("one of the five left-out tests: %s" % test_id)
        approved = [r for prefix, r in APPROVED_SKIP_REASONS if test_id.startswith(prefix)]
        if not approved:
            problems.append("not in an approved skip group: %s" % test_id)
        elif not reason:
            problems.append("empty reason: %s" % test_id)
        elif reason != approved[0]:
            problems.append("reason is not the approved one for its file: %s — %s"
                            % (test_id, reason))
    return problems


def _pair_key(pair):
    return pair


def skip_differences(observed, recorded):
    """(unexpected, missing) pairs, comparing on _pair_key."""
    obs = {_pair_key(p): p for p in observed}
    rec = {_pair_key(p): p for p in recorded}
    unexpected = sorted(obs[k] for k in obs if k not in rec)
    missing = sorted(rec[k] for k in rec if k not in obs)
    return unexpected, missing


def log_skip_count(text, path):
    line = summary_line(text)
    if line is None:
        raise UnusableInput("NO PYTEST SUMMARY LINE IN SUITE LOG %s" % path)
    m = _SKIPPED_RE.search(line)
    return int(m.group(1)) if m else 0


def cmd_check_skips(xml_path, log_path):
    observed = observed_skips(xml_path)
    logged = log_skip_count(_read_text(log_path, "SUITE LOG"), log_path)
    for test_id, reason in observed:
        sys.stdout.write("OBSERVED-SKIP\t%s\t%s\n" % (test_id, reason))
    sys.stdout.write("OBSERVED-SKIP-COUNT %d\n" % len(observed))
    recorded = RECORDED_SKIPS
    if recorded is None:
        _stop("SKIP LIST NOT YET RECORDED — THIS IS A RECORDING RUN, NOT A GREEN RUN")
        return 1
    rule = skip_list_problems(recorded)
    if rule:
        _stop("RECORDED SKIP LIST BREAKS THE APPROVED-GROUP RULE", rule)
        return 1
    if logged != len(observed):
        _stop("SKIP COUNT IN THE LOG AND THE RESULT FILE DISAGREE",
              ["log says %d skipped, result file has %d" % (logged, len(observed))])
        return 1
    unexpected, missing = skip_differences(observed, recorded)
    if unexpected or missing:
        details = (["unexpected %s — %s" % p for p in unexpected]
                   + ["missing %s — %s" % p for p in missing])
        _stop("SKIPPED SET DIFFERS FROM THE RECORDED LIST", details)
        return 1
    sys.stdout.write("skipped set matches the recorded %d\n" % len(recorded))
    return 0


# ---------------------------------------------------------------- CLI

COMMANDS = {
    "check-list": (cmd_check_list, 1),
    "args": (cmd_args, 1),
    "check-log": (cmd_check_log, 1),
    "check-skips": (cmd_check_skips, 2),
}

USAGE = ("usage: left_out_guard.py check-list <file> | args <file> | "
         "check-log <log> | check-skips <junit xml> <log>")


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if not args or args[0] not in COMMANDS:
        _stop(USAGE)
        return 2
    func, arity = COMMANDS[args[0]]
    if len(args) - 1 != arity:
        _stop(USAGE)
        return 2
    try:
        return func(*args[1:])
    except UnusableInput as exc:
        _stop(str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
