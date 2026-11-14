"""test_workflow_shape.py — text locks on the one CI workflow.

The repo has exactly one GitHub Actions workflow, `.github/workflows/offline-suite.yml`.
It only adds a check: no secrets, a read-only token, no live model call. Its safety
properties live in plain workflow text, so each one is locked here by a check function
that reads the text and returns a list of problems (empty when the property holds).

Every check is made of named clauses. Every clause has at least one mutant: a named,
deliberate break of the real text (or of a temp copy of a directory). Each mutant first
asserts that the break really happened (the needle is present, the mutant differs from
the original) and only then asserts that the check trips on that clause. A check that
cannot trip is worse than no check, so `TestEveryClauseHasAMutant` fails if any clause
is left without a mutant, and has its own break test.

Stdlib only, no YAML library: regex and line checks on the workflow text.
Imports exactly a subset of {os, re, shutil, sys, tempfile, unittest}.
"""

import os
import re
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
WORKFLOWS_DIR = os.path.join(REPO_ROOT, ".github", "workflows")
WORKFLOW = os.path.join(WORKFLOWS_DIR, "offline-suite.yml")
THIS_FILE = os.path.abspath(__file__)

ALLOWED_IMPORTS = {"os", "re", "shutil", "sys", "tempfile", "unittest"}

CHECKOUT_PIN = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_PYTHON_PIN = "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0"
KNOWN_PINS = {CHECKOUT_PIN, SETUP_PYTHON_PIN}

# The three suite directories, in the order the workflow passes them to pytest.
SUITE_DIRS = (
    "plugins/vibe-check/scripts",
    ".github/scripts",
    "docs/design/lean-v2.15/tools",
)

# Files pytest reads settings (addopts and friends) from. The repo has none of them.
CONFIG_FILES = (
    "pytest.ini",
    ".pytest.ini",
    "pytest.toml",
    ".pytest.toml",
    "pyproject.toml",
    "tox.ini",
    "setup.cfg",
)

STDLIB_RUN = "python3 -I .github/scripts/stdlib_only.py plugins/vibe-check"
LIST_GUARD = "left_out_guard.py check-list .github/ci-left-out-tests.txt"
ARGS_GUARD = "left_out_guard.py args .github/ci-left-out-tests.txt"
COUNT_GUARD = "left_out_guard.py check-log"
SKIP_GUARD = 'left_out_guard.py check-skips "$RUNNER_TEMP/suite.xml" "$RUNNER_TEMP/suite.log"'
JUNITXML = '--junitxml="$RUNNER_TEMP/suite.xml"'
TEE = '2>&1 | tee "$RUNNER_TEMP/suite.log"'
PIPESTATUS_LINE = 'test "${PIPESTATUS[0]}" -eq 0'
WORKTREE_ADD = 'git worktree add --detach "$RUNNER_TEMP/wt" HEAD'
WORKTREE_CD = 'cd "$RUNNER_TEMP/wt"'

STEP_START = "      - "


# --------------------------------------------------------------------------- helpers


def _clean(line):
    """A line with any YAML comment removed and trailing space stripped."""
    if line.lstrip().startswith("#"):
        return ""
    return re.sub(r"\s+#.*$", "", line).rstrip()


def _lines(text):
    return [c for c in (_clean(l) for l in text.splitlines()) if c.strip()]


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _children(lines, key, indent):
    """The lines nested under `key:` at the given indent, or None if the key is absent."""
    out = None
    for line in lines:
        ind = _indent(line)
        if out is None:
            if ind == indent and line.strip() == key + ":":
                out = []
            continue
        if ind <= indent:
            break
        out.append(line)
    return out


def split_steps(text):
    """(prefix, [step blocks]) — prefix runs through the `steps:` line."""
    lines = text.splitlines(keepends=True)
    prefix = []
    blocks = []
    in_steps = False
    for line in lines:
        if not in_steps:
            prefix.append(line)
            if re.match(r"^\s+steps:\s*$", line):
                in_steps = True
            continue
        if line.startswith(STEP_START) or not blocks:
            blocks.append([line])
        else:
            blocks[-1].append(line)
    return "".join(prefix), ["".join(b) for b in blocks]


def step_name(block):
    m = re.search(r"^\s*-?\s*name:\s*(.+?)\s*$", block, re.M)
    return _clean(m.group(1)) if m else None


def step_block(text, name):
    for block in split_steps(text)[1]:
        if step_name(block) == name:
            return block
    return None


def move_step(text, name, anchor, where):
    """Move the step called `name` to just after (or before) the step called `anchor`."""
    prefix, blocks = split_steps(text)
    moving = [b for b in blocks if step_name(b) == name]
    if len(moving) != 1:
        return text
    rest = [b for b in blocks if step_name(b) != name]
    names = [step_name(b) for b in rest]
    if anchor not in names:
        return text
    i = names.index(anchor)
    if where == "after":
        i += 1
    rest.insert(i, moving[0])
    return prefix + "".join(rest)


def pytest_lines(text):
    joined = text.replace("\\\n", " ")
    return [l for l in joined.splitlines() if re.match(r"^\s*pytest\s", l)]


def pytest_option_text(text):
    """Every place a pytest option can come from in the workflow: the pytest command
    line(s) and any line that sets PYTEST_ADDOPTS."""
    joined = text.replace("\\\n", " ")
    keep = [
        l
        for l in joined.splitlines()
        if re.match(r"^\s*pytest\s", l) or "PYTEST_ADDOPTS" in l
    ]
    return "\n".join(keep)


def _all_positions(text, needle):
    out = []
    i = text.find(needle)
    while i >= 0:
        out.append(i)
        i = text.find(needle, i + 1)
    return out


# --------------------------------------------------------------------------- checks


def one_workflow_holds(workflows_dir):
    entries = sorted(os.listdir(workflows_dir)) if os.path.isdir(workflows_dir) else []
    problems = []
    if len(entries) != 1:
        problems.append(f"single-file: workflows directory holds {entries!r}")
    if entries != ["offline-suite.yml"]:
        problems.append(f"named-offline-suite: expected ['offline-suite.yml'], found {entries!r}")
    return problems


def push_trigger_holds(text):
    on = _children(_lines(text), "on", 0) or []
    push = _children(on, "push", 2)
    problems = []
    if push is None:
        problems.append("push-present: no push trigger under on:")
    body = [l.strip() for l in push or []]
    if body != ["branches: ['**']"]:
        problems.append(f"push-all-branches: push filters are {body!r}, expected only branches: ['**']")
    return problems


def pr_trigger_holds(text):
    on = _children(_lines(text), "on", 0) or []
    pr = _children(on, "pull_request", 2)
    problems = []
    if pr is None:
        problems.append("pr-present: no pull_request trigger under on:")
    body = [l.strip() for l in pr or []]
    if body != ["branches: [main]"]:
        problems.append(f"pr-targets-main: pull_request filters are {body!r}, expected only branches: [main]")
    if "pull_request_target" in text:
        problems.append("no-pr-target: pull_request_target appears in the workflow")
    return problems


def permissions_hold(text):
    perms = _children(_lines(text), "permissions", 0)
    entries = [l.strip() for l in perms or []]
    problems = []
    if "contents: read" not in entries:
        problems.append(f"contents-read: top-level permissions are {entries!r}, expected contents: read")
    others = [e for e in entries if e != "contents: read"]
    if others:
        problems.append(f"nothing-else: extra permission entries {others!r}")
    count = len(re.findall(r"^\s*permissions\s*:", text, re.M))
    if count != 1:
        problems.append(f"nothing-else: permissions set {count} times, expected once at the top")
    return problems


def no_secrets_holds(text):
    problems = []
    if re.search(r"\bsecrets\s*[.\[]", text):
        problems.append("no-secrets: the workflow reads a secret")
    if re.search(r"\$\{\{[^}]*github\.(event|head_ref)", text):
        problems.append("no-event-fields: the workflow expands an event field")
    if re.search(r"anthropic", text, re.I):
        problems.append("no-anthropic: the workflow names ANTHROPIC")
    if re.search(r"openai", text, re.I):
        problems.append("no-openai: the workflow names OPENAI")
    if re.search(r"api_key", text, re.I):
        problems.append("no-api-key: the workflow names API_KEY")
    return problems


def actions_pinned_hold(text):
    uses = re.findall(r"^\s*(?:-\s+)?uses:\s*(\S+)", text, re.M)
    problems = []
    if not uses:
        problems.append("forty-hex: no uses: lines")
    for u in uses:
        if not re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", u):
            problems.append(f"forty-hex: {u} is not pinned to a 40-hex commit id")
    if set(uses) != KNOWN_PINS or len(uses) != len(KNOWN_PINS):
        problems.append(f"known-ids: uses values {uses!r} differ from the two pinned ids")
    return problems


def checkout_holds(text):
    blocks = [
        b
        for b in split_steps(text)[1]
        if re.search(r"^\s*-?\s*uses:\s*actions/checkout@", b, re.M)
    ]
    body = "\n".join(_lines(blocks[0])) if len(blocks) == 1 else ""
    problems = []
    if not re.search(r"^\s*fetch-depth:\s*0\s*$", body, re.M):
        problems.append("fetch-depth-0: the checkout step lacks fetch-depth: 0")
    if not re.search(r"^\s*persist-credentials:\s*false\s*$", body, re.M):
        problems.append("no-persisted-credentials: the checkout step lacks persist-credentials: false")
    return problems


def runner_holds(text):
    runs = re.findall(r"^\s*runs-on:\s*(.+?)\s*$", "\n".join(_lines(text)), re.M)
    problems = []
    if runs != ["ubuntu-24.04"]:
        problems.append(f"ubuntu-24-04: runs-on values are {runs!r}, expected ['ubuntu-24.04']")
    if "macos" in text.lower():
        problems.append("no-macos: the workflow names macos")
    if "continue-on-error" in text:
        problems.append("no-continue-on-error: a step may fail softly")
    if re.search(r"\|\|\s*(true|:|exit\s+0)(\s|$)", text, re.M):
        problems.append("no-or-true: a command's failure is swallowed")
    return problems


def tools_pinned_hold(text):
    pip_lines = [l for l in _lines(text) if re.search(r"\bpip\s+install\b", l)]
    problems = []
    tokens = []
    for l in pip_lines:
        after = re.split(r"\bpip\s+install\b", l, maxsplit=1)[1]
        tokens += [t for t in after.split() if not t.startswith("-")]
    if "pytest==9.0.3" not in tokens:
        problems.append(f"pytest-pinned: pip installs {tokens!r}, expected pytest==9.0.3")
    loose = [t for t in tokens if "==" not in t]
    if loose:
        problems.append(f"pytest-pinned: unpinned pip packages {loose!r}")
    if not re.search(r"apt-get install\b[^\n]*\bzsh\b", text):
        problems.append("zsh-installed: no apt-get install line names zsh")
    return problems


def stdlib_step_holds(text):
    block = step_block(text, "Stdlib-only check")
    problems = []
    if block is None:
        problems.append("step-named: no step named 'Stdlib-only check'")
    where = block if block is not None else text
    runs = [l.strip() for l in _lines(where) if re.match(r"^\s*run:", l)]
    if "run: " + STDLIB_RUN not in runs:
        problems.append(f"run-line: no run line '{STDLIB_RUN}'")
    return problems


def left_out_guard_holds(text):
    opts = pytest_option_text(text)
    problems = []
    if LIST_GUARD not in text:
        problems.append("check-list-present: the list guard is missing")
    if ARGS_GUARD not in text:
        problems.append("args-present: the deselects are not built from the guarded list")
    if COUNT_GUARD not in text:
        problems.append("check-log-present: the deselect-count guard is missing")
    if re.search(r"--deselect[ =]", text):
        problems.append("no-literal-deselect: a literal deselect appears in the workflow")
    if re.search(r"--ignore(-glob)?\b", text):
        problems.append("no-ignore: an ignore option appears in the workflow")
    if re.search(r"(^|\s)-k(?![\w-])", opts, re.M):
        problems.append("no-k: a -k selection reaches pytest")
    if re.search(r"(^|\s)(-x(?![\w-])|--exitfirst|--maxfail)", opts, re.M):
        problems.append("no-x: pytest may stop at the first failure")
    if re.search(r"(^|\s)-m(?![\w-])", opts, re.M):
        problems.append("no-marker-select: a -m marker selection reaches pytest")
    disabled = re.findall(r"-p\s*no:(\S+)", opts)
    if disabled != ["cacheprovider"]:
        problems.append(f"only-cacheprovider-disabled: disabled plugins are {disabled!r}")
    return problems


def skip_guard_holds(text):
    problems = []
    if SKIP_GUARD not in text:
        problems.append("check-skips-present: the skip guard command is missing")
    lines = pytest_lines(text)
    if not lines or JUNITXML not in lines[0]:
        problems.append("junitxml-present: the pytest line does not write the junit result file")
    if step_block(text, "Skip guard") is None:
        problems.append("skip-step-named: no step named 'Skip guard'")
    return problems


def no_config_file_holds(repo_root):
    problems = []
    for name in CONFIG_FILES:
        if os.path.lexists(os.path.join(repo_root, name)):
            problems.append(f"no-root-config: {name} at the repo root")
    places = {""}
    for d in SUITE_DIRS:
        parts = d.split("/")
        for i in range(1, len(parts)):
            places.add("/".join(parts[:i]))
    for rel in sorted(places):
        here = os.path.join(repo_root, *rel.split("/")) if rel else repo_root
        if os.path.lexists(os.path.join(here, "conftest.py")):
            problems.append(f"no-conftest: {rel + '/' if rel else ''}conftest.py")
    for d in SUITE_DIRS:
        top = os.path.join(repo_root, *d.split("/"))
        if not os.path.isdir(top):
            continue
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames.sort()
            if "conftest.py" in filenames:
                rel = os.path.relpath(os.path.join(dirpath, "conftest.py"), repo_root)
                problems.append(f"no-conftest: {rel.replace(os.sep, '/')}")
    return problems


def step_order_holds(text):
    prefix_len = len(split_steps(text)[0])
    m = re.search(r"^\s*pytest\s", text[prefix_len:], re.M)
    suite = prefix_len + m.start() if m else -1
    problems = []
    if suite < 0:
        return [
            "stdlib-before-suite: no pytest line",
            "list-guard-before-suite: no pytest line",
            "count-guard-after-suite: no pytest line",
            "skip-guard-after-suite: no pytest line",
        ]
    stdlib = _all_positions(text, STDLIB_RUN)
    if not stdlib or max(stdlib) > suite:
        problems.append("stdlib-before-suite: the stdlib check does not run before the suite")
    listed = _all_positions(text, LIST_GUARD)
    if not listed or max(listed) > suite:
        problems.append("list-guard-before-suite: the list guard does not run before the suite")
    count = _all_positions(text, COUNT_GUARD)
    if not count or min(count) < suite:
        problems.append("count-guard-after-suite: the count guard does not run after the suite")
    skips = _all_positions(text, SKIP_GUARD)
    if not skips or min(skips) < suite:
        problems.append("skip-guard-after-suite: the skip guard does not run after the suite")
    return problems


def suite_command_holds(text):
    lines = pytest_lines(text)
    problems = []
    pl = lines[0] if len(lines) == 1 else ""
    if len(lines) != 1:
        problems.append(f"quiet-no-cache: expected one pytest line, found {len(lines)}")
    elif not re.match(r"^\s*pytest -q -p no:cacheprovider\s", pl):
        problems.append("quiet-no-cache: the pytest line does not start with pytest -q -p no:cacheprovider")
    if " ".join(SUITE_DIRS) not in pl:
        problems.append("dirs-in-order: the three suite directories are not passed in the pinned order")
    if not re.search(r"\s-rs(\s|$)", pl):
        problems.append("rs-present: skip reasons are not printed (-rs)")
    add = text.find(WORKTREE_ADD)
    cd = text.find(WORKTREE_CD)
    at = text.find(pl) if pl else -1
    if add < 0 or cd < 0 or not (add < cd < at):
        problems.append("worktree-add: the suite does not run from a detached linked worktree")
    if TEE not in pl:
        problems.append("tee-present: the suite output is not piped through tee into the log")
    after = ""
    if pl:
        rest = text.replace("\\\n", " ").splitlines()
        idx = rest.index(pl)
        following = [l.strip() for l in rest[idx + 1:] if l.strip()]
        after = following[0] if following else ""
    if after != PIPESTATUS_LINE:
        problems.append(f"pipestatus: the line after pytest is {after!r}, expected {PIPESTATUS_LINE!r}")
    return problems


# --------------------------------------------------------------------------- tables

CLAUSES = {
    "one_workflow_holds": ("single-file", "named-offline-suite"),
    "push_trigger_holds": ("push-present", "push-all-branches"),
    "pr_trigger_holds": ("pr-present", "pr-targets-main", "no-pr-target"),
    "permissions_hold": ("contents-read", "nothing-else"),
    "no_secrets_holds": ("no-secrets", "no-event-fields", "no-anthropic", "no-openai", "no-api-key"),
    "actions_pinned_hold": ("forty-hex", "known-ids"),
    "checkout_holds": ("fetch-depth-0", "no-persisted-credentials"),
    "runner_holds": ("ubuntu-24-04", "no-macos", "no-continue-on-error", "no-or-true"),
    "tools_pinned_hold": ("pytest-pinned", "zsh-installed"),
    "stdlib_step_holds": ("step-named", "run-line"),
    "left_out_guard_holds": (
        "check-list-present",
        "args-present",
        "check-log-present",
        "no-literal-deselect",
        "no-ignore",
        "no-k",
        "no-x",
        "no-marker-select",
        "only-cacheprovider-disabled",
    ),
    "skip_guard_holds": ("check-skips-present", "junitxml-present", "skip-step-named"),
    "no_config_file_holds": ("no-root-config", "no-conftest"),
    "step_order_holds": (
        "stdlib-before-suite",
        "list-guard-before-suite",
        "count-guard-after-suite",
        "skip-guard-after-suite",
    ),
    "suite_command_holds": (
        "quiet-no-cache",
        "dirs-in-order",
        "rs-present",
        "worktree-add",
        "tee-present",
        "pipestatus",
    ),
}

_PLANT_CONFIG = "addopts = --ignore=plugins/vibe-check/scripts/test_score.py\n"
_PLANT_CONFTEST = 'collect_ignore = ["test_score.py"]\n'
_TEE_END = 'tee "$RUNNER_TEMP/suite.log"\n'


def _env_on_stdlib_step(line):
    return (
        "replace",
        "      - name: Stdlib-only check\n",
        "      - name: Stdlib-only check\n        env:\n          " + line + "\n",
    )


# (check, clause, label, kind, a, b)
#   replace: a = needle, b = replacement (first occurrence only)
#   move:    a = step name, b = (anchor step name, "after" | "before")
#   dir:     a = "add" | "rename", b = file name, on a temp copy of .github/workflows
#   tree:    a = relative path planted in a temp skeleton, b = file content
MUTANTS = [
    ("one_workflow_holds", "single-file", "a second file extra.yml added", "dir", "add", "extra.yml"),
    ("one_workflow_holds", "named-offline-suite", "the file renamed ci.yml", "dir", "rename", "ci.yml"),
    ("push_trigger_holds", "push-present", "push replaced by workflow_dispatch",
     "replace", "  push:\n", "  workflow_dispatch:\n"),
    ("push_trigger_holds", "push-all-branches", "push narrowed to main",
     "replace", "    branches: ['**']\n", "    branches: [main]\n"),
    ("pr_trigger_holds", "pr-present", "the pull_request block removed",
     "replace", "  pull_request:\n    branches: [main]\n", ""),
    ("pr_trigger_holds", "pr-targets-main", "pull_request retargeted to release",
     "replace", "  pull_request:\n    branches: [main]\n", "  pull_request:\n    branches: [release]\n"),
    ("pr_trigger_holds", "no-pr-target", "trigger renamed pull_request_target",
     "replace", "  pull_request:\n", "  pull_request_target:\n"),
    ("permissions_hold", "contents-read", "contents: write",
     "replace", "  contents: read\n", "  contents: write\n"),
    ("permissions_hold", "nothing-else", "pull-requests: write added",
     "replace", "  contents: read\n", "  contents: read\n  pull-requests: write\n"),
    ("no_secrets_holds", "no-secrets", "a secret added to a run line",
     "replace", "sudo apt-get update -q\n", "sudo apt-get update -q ${{ secrets.TOKEN }}\n"),
    ("no_secrets_holds", "no-event-fields", "a PR title added to a run line",
     "replace", "sudo apt-get update -q\n", "sudo apt-get update -q ${{ github.event.pull_request.title }}\n"),
    ("no_secrets_holds", "no-anthropic", "an ANTHROPIC env line added",
     *_env_on_stdlib_step("ANTHROPIC_MODEL: x")),
    ("no_secrets_holds", "no-openai", "an OPENAI env line added",
     *_env_on_stdlib_step("OPENAI_BASE_URL: x")),
    ("no_secrets_holds", "no-api-key", "an API_KEY env line added",
     *_env_on_stdlib_step("SERVICE_API_KEY: x")),
    ("actions_pinned_hold", "forty-hex", "checkout pin replaced by @v7",
     "replace", "@3d3c42e5aac5ba805825da76410c181273ba90b1", "@v7"),
    ("actions_pinned_hold", "known-ids", "checkout pin replaced by forty zeros",
     "replace", "@3d3c42e5aac5ba805825da76410c181273ba90b1", "@" + "0" * 40),
    ("checkout_holds", "fetch-depth-0", "fetch-depth: 1",
     "replace", "fetch-depth: 0\n", "fetch-depth: 1\n"),
    ("checkout_holds", "no-persisted-credentials", "persist-credentials: true",
     "replace", "persist-credentials: false\n", "persist-credentials: true\n"),
    ("runner_holds", "ubuntu-24-04", "ubuntu-latest",
     "replace", "runs-on: ubuntu-24.04\n", "runs-on: ubuntu-latest\n"),
    ("runner_holds", "no-macos", "macos-latest",
     "replace", "runs-on: ubuntu-24.04\n", "runs-on: macos-latest\n"),
    ("runner_holds", "no-continue-on-error", "continue-on-error on the suite step",
     "replace", "      - name: Offline suite\n", "      - name: Offline suite\n        continue-on-error: true\n"),
    ("runner_holds", "no-or-true", "|| true after the pytest pipe",
     "replace", _TEE_END, 'tee "$RUNNER_TEMP/suite.log" || true\n'),
    ("tools_pinned_hold", "pytest-pinned", "pytest version removed",
     "replace", "pytest==9.0.3", "pytest"),
    ("tools_pinned_hold", "zsh-installed", "zsh removed from apt-get install",
     "replace", "apt-get install -y -q zsh", "apt-get install -y -q"),
    ("stdlib_step_holds", "step-named", "step renamed",
     "replace", "name: Stdlib-only check\n", "name: Stdlib check\n"),
    ("stdlib_step_holds", "run-line", "run line deleted",
     "replace", "        run: " + STDLIB_RUN + "\n", ""),
    ("left_out_guard_holds", "check-list-present", "list guard removed",
     "replace", "        run: python3 -I .github/scripts/" + LIST_GUARD + "\n", ""),
    ("left_out_guard_holds", "args-present", "args line removed",
     "replace", '          left_out="$(python3 -I .github/scripts/' + ARGS_GUARD + ')"\n', ""),
    ("left_out_guard_holds", "check-log-present", "count guard removed",
     "replace", '        run: python3 -I .github/scripts/' + COUNT_GUARD + ' "$RUNNER_TEMP/suite.log"\n', ""),
    ("left_out_guard_holds", "no-literal-deselect", "literal deselect added",
     "replace", " -rs ", " --deselect plugins/vibe-check/scripts/test_score.py -rs "),
    ("left_out_guard_holds", "no-ignore", "--ignore added",
     "replace", " -rs ", " --ignore=plugins/vibe-check/scripts/test_score.py -rs "),
    ("left_out_guard_holds", "no-k", "-k added",
     "replace", " -rs ", ' -k "not replay" -rs '),
    ("left_out_guard_holds", "no-x", "-x added",
     "replace", " -rs ", " -x -rs "),
    ("left_out_guard_holds", "no-marker-select", "-m added",
     "replace", " -rs ", ' -m "not slow" -rs '),
    ("left_out_guard_holds", "only-cacheprovider-disabled", "-p no:unittest added",
     "replace", " -rs ", " -p no:unittest -rs "),
    ("skip_guard_holds", "check-skips-present", "skip guard line removed",
     "replace", "        run: python3 -I .github/scripts/" + SKIP_GUARD + "\n", ""),
    ("skip_guard_holds", "junitxml-present", "junitxml removed",
     "replace", " " + JUNITXML, ""),
    ("skip_guard_holds", "skip-step-named", "skip step renamed",
     "replace", "name: Skip guard\n", "name: Skips\n"),
] + [
    ("no_config_file_holds", "no-root-config", f"{name} planted at the root", "tree", name, _PLANT_CONFIG)
    for name in CONFIG_FILES
] + [
    ("no_config_file_holds", "no-conftest", "conftest.py at the root",
     "tree", "conftest.py", _PLANT_CONFTEST),
    ("no_config_file_holds", "no-conftest", "conftest.py in a suite directory",
     "tree", "plugins/vibe-check/scripts/conftest.py", _PLANT_CONFTEST),
    ("no_config_file_holds", "no-conftest", "conftest.py in an in-between directory",
     "tree", "plugins/conftest.py", _PLANT_CONFTEST),
    ("no_config_file_holds", "no-conftest", "conftest.py below a suite directory",
     "tree", "plugins/vibe-check/scripts/fixtures/conftest.py", _PLANT_CONFTEST),
    ("step_order_holds", "stdlib-before-suite", "stdlib step moved after the suite",
     "move", "Stdlib-only check", ("Offline suite", "after")),
    ("step_order_holds", "list-guard-before-suite", "list guard moved after the suite",
     "move", "Left-out list guard", ("Offline suite", "after")),
    ("step_order_holds", "count-guard-after-suite", "count guard moved before the suite",
     "move", "Left-out count guard", ("Offline suite", "before")),
    ("step_order_holds", "skip-guard-after-suite", "skip guard moved before the suite",
     "move", "Skip guard", ("Offline suite", "before")),
    ("suite_command_holds", "quiet-no-cache", "-q removed",
     "replace", "pytest -q -p no:cacheprovider", "pytest -p no:cacheprovider"),
    ("suite_command_holds", "dirs-in-order", "first two directories swapped",
     "replace", "plugins/vibe-check/scripts .github/scripts", ".github/scripts plugins/vibe-check/scripts"),
    ("suite_command_holds", "dirs-in-order", "third directory removed",
     "replace", " docs/design/lean-v2.15/tools", ""),
    ("suite_command_holds", "rs-present", "-rs removed",
     "replace", " -rs ", " "),
    ("suite_command_holds", "worktree-add", "worktree add line removed",
     "replace", "          " + WORKTREE_ADD + "\n", ""),
    ("suite_command_holds", "tee-present", "tee pipe replaced by > /dev/null",
     "replace", ' | tee "$RUNNER_TEMP/suite.log"', " > /dev/null"),
    ("suite_command_holds", "pipestatus", "PIPESTATUS line removed",
     "replace", "          " + PIPESTATUS_LINE + "\n", ""),
]


def check_functions():
    """Every module-level check function: names ending in _holds or _hold."""
    return {
        name: fn
        for name, fn in globals().items()
        if callable(fn) and re.search(r"_holds?$", name)
    }


def clauses_without_mutant(clauses, mutants):
    have = {}
    for m in mutants:
        have.setdefault(m[0], set()).add(m[1])
    return [
        f"{check}: {clause}"
        for check, ids in clauses.items()
        for clause in ids
        if clause not in have.get(check, set())
    ]


def mutants_on_unknown_clauses(clauses, mutants):
    return [f"{m[0]}: {m[1]}" for m in mutants if m[1] not in clauses.get(m[0], ())]


def checks_missing_from_clauses(clauses):
    return sorted(set(check_functions()) - set(clauses))


def found_imports(source):
    found = set()
    for line in source.splitlines():
        m = re.match(r"^\s*(?:import|from)\s+([A-Za-z_][\w]*)", line)
        if m:
            found.add(m.group(1))
    return found


# --------------------------------------------------------------------------- tests


class LockCase(unittest.TestCase):
    def assert_holds(self, check, *texts):
        self.assertEqual(check(*texts), [])

    def assert_trips(self, check, *mutant_texts):
        self.assertNotEqual(check(*mutant_texts), [])

    def assert_names_clause(self, check_name, clause, problems, must_mention=None):
        self.assertTrue(
            any(p.startswith(clause + ":") and (must_mention is None or must_mention in p) for p in problems),
            f"{check_name} did not name {clause!r}: {problems!r}",
        )
        prefixes = {p.split(":", 1)[0] for p in problems}
        self.assertLessEqual(prefixes, set(CLAUSES[check_name]), problems)


class TestWorkflowText(LockCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isfile(WORKFLOW):
            raise AssertionError(f"the CI workflow file is missing: {WORKFLOW}")
        with open(WORKFLOW, encoding="utf-8") as fh:
            cls.text = fh.read()

    def _run(self, check_name):
        check = check_functions()[check_name]
        self.assert_holds(check, self.text)
        entries = [m for m in MUTANTS if m[0] == check_name]
        self.assertTrue(entries, f"no mutants for {check_name}")
        for _, clause, label, kind, a, b in entries:
            with self.subTest(clause=clause, mutant=label):
                if kind == "replace":
                    self.assertIn(a, self.text)
                    mutant = self.text.replace(a, b, 1)
                elif kind == "move":
                    block = step_block(self.text, a)
                    self.assertIsNotNone(block, f"no step named {a!r}")
                    self.assertIn(block, self.text)
                    mutant = move_step(self.text, a, *b)
                else:
                    self.fail(f"unexpected mutant kind {kind!r} for a text check")
                self.assertNotEqual(mutant, self.text)
                self.assert_trips(check, mutant)
                self.assert_names_clause(check_name, clause, check(mutant))

    def test_push_trigger(self):
        self._run("push_trigger_holds")

    def test_pr_trigger(self):
        self._run("pr_trigger_holds")

    def test_permissions(self):
        self._run("permissions_hold")

    def test_no_secrets(self):
        self._run("no_secrets_holds")

    def test_actions_pinned(self):
        self._run("actions_pinned_hold")

    def test_checkout(self):
        self._run("checkout_holds")

    def test_runner(self):
        self._run("runner_holds")

    def test_tools_pinned(self):
        self._run("tools_pinned_hold")

    def test_stdlib_step(self):
        self._run("stdlib_step_holds")

    def test_left_out_guard(self):
        self._run("left_out_guard_holds")

    def test_skip_guard(self):
        self._run("skip_guard_holds")

    def test_step_order(self):
        self._run("step_order_holds")

    def test_suite_command(self):
        self._run("suite_command_holds")


class TestOneWorkflow(LockCase):
    def test_one_workflow(self):
        self.assert_holds(one_workflow_holds, WORKFLOWS_DIR)
        real = sorted(os.listdir(WORKFLOWS_DIR))
        entries = [m for m in MUTANTS if m[0] == "one_workflow_holds"]
        self.assertTrue(entries)
        for _, clause, label, kind, a, b in entries:
            with self.subTest(clause=clause, mutant=label):
                self.assertEqual(kind, "dir")
                tmp = tempfile.mkdtemp()
                self.addCleanup(shutil.rmtree, tmp)
                copy = os.path.join(tmp, "workflows")
                shutil.copytree(WORKFLOWS_DIR, copy)
                if a == "add":
                    with open(os.path.join(copy, b), "w", encoding="utf-8") as fh:
                        fh.write("name: extra\n")
                    self.assertEqual(len(os.listdir(copy)), 2)
                else:
                    os.rename(os.path.join(copy, "offline-suite.yml"), os.path.join(copy, b))
                self.assertNotEqual(sorted(os.listdir(copy)), real)
                self.assert_trips(one_workflow_holds, copy)
                self.assert_names_clause("one_workflow_holds", clause, one_workflow_holds(copy))
        self.assertEqual(sorted(os.listdir(WORKFLOWS_DIR)), real)


class TestNoConfigFile(LockCase):
    def test_no_config_file(self):
        self.assert_holds(no_config_file_holds, REPO_ROOT)
        entries = [m for m in MUTANTS if m[0] == "no_config_file_holds"]
        self.assertEqual(len(entries), len(CONFIG_FILES) + 4)
        for _, clause, label, kind, rel, content in entries:
            with self.subTest(clause=clause, mutant=label):
                self.assertEqual(kind, "tree")
                tmp = tempfile.mkdtemp()
                self.addCleanup(shutil.rmtree, tmp)
                for d in SUITE_DIRS:
                    os.makedirs(os.path.join(tmp, *d.split("/")))
                self.assert_holds(no_config_file_holds, tmp)
                planted = os.path.join(tmp, *rel.split("/"))
                os.makedirs(os.path.dirname(planted), exist_ok=True)
                with open(planted, "w", encoding="utf-8") as fh:
                    fh.write(content)
                self.assertTrue(os.path.isfile(planted))
                self.assertFalse(os.path.lexists(os.path.join(REPO_ROOT, *rel.split("/"))))
                self.assert_trips(no_config_file_holds, tmp)
                self.assert_names_clause(
                    "no_config_file_holds", clause, no_config_file_holds(tmp), must_mention=rel
                )


class TestEveryClauseHasAMutant(unittest.TestCase):
    def test_every_clause_has_a_mutant(self):
        self.assertEqual(clauses_without_mutant(CLAUSES, MUTANTS), [])

    def test_every_mutant_names_a_known_clause(self):
        self.assertEqual(mutants_on_unknown_clauses(CLAUSES, MUTANTS), [])

    def test_every_check_function_is_listed(self):
        self.assertEqual(checks_missing_from_clauses(CLAUSES), [])
        self.assertGreaterEqual(len(check_functions()), 15)

    def test_break_a_mutant_removed_is_named(self):
        target = ("permissions_hold", "nothing-else")
        matching = [m for m in MUTANTS if (m[0], m[1]) == target]
        self.assertEqual(len(matching), 1)
        broken = [m for m in MUTANTS if (m[0], m[1]) != target]
        self.assertNotEqual(len(broken), len(MUTANTS))
        self.assertEqual(clauses_without_mutant(CLAUSES, broken), ["permissions_hold: nothing-else"])

    def test_break_a_check_left_out_of_clauses_is_named(self):
        broken = {k: v for k, v in CLAUSES.items() if k != "runner_holds"}
        self.assertNotEqual(len(broken), len(CLAUSES))
        self.assertEqual(checks_missing_from_clauses(broken), ["runner_holds"])


class TestImportSet(unittest.TestCase):
    def test_imports_are_stdlib_subset(self):
        with open(THIS_FILE, encoding="utf-8") as fh:
            source = fh.read()
        found = found_imports(source)
        self.assertLessEqual(found, ALLOWED_IMPORTS)
        self.assertIn("unittest", found)
        with self.subTest("mutant: a YAML import added"):
            mutant = source + "\nimport yaml\n"
            self.assertNotEqual(mutant, source)
            self.assertFalse(found_imports(mutant) <= ALLOWED_IMPORTS)


if __name__ == "__main__":
    unittest.main()
