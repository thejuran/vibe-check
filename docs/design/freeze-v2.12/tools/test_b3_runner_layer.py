"""Prose locks over the committed B3 runner layer and the live-check runbook.

The B3 runner is shell plus a Markdown runbook, so its identity contract is
held by text locks rather than unit tests of behavior:

- every launch-bearing runbook block (preflight, launch, session, pre, post)
  calls `b3_identity_check`;
- the environment checked is the environment the session gets: `claude`
  starts only from the `session` block, by `exec`, after that block's own
  identity check (run in the process that becomes `claude`) agreed with
  `launch`; `launch` hands the pane the session block as an argv list and
  never types a launch line into a pane, so which tmux server hosts the
  pane cannot matter;
- the runner copy is built with `git archive`, never copied from the working
  tree (no rsync, cp -r, copytree, ditto);
- no line passes on a version string;
- the identity check has no override and fails closed;
- the settings file the check verifies is the file the session loads (one
  `"$RUNNER_SETTINGS"` / `"$RUNNER_PLUGIN"` token everywhere);
- materialization edits exactly one settings key (`statusLine.command`,
  `<RUNNER>` -> the runner dir).

Every lock is a pure `..._holds(text) -> bool` function with a test on the
real files and at least one mutant test showing the lock trips.
"""

import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
LAYER = os.path.join(REPO, "docs", "design", "b3-ground-truth", "b3-runner-v2.12")
COMMON = os.path.join(LAYER, "common.sh")
RUN_CASE = os.path.join(LAYER, "run_case.sh")
SETTINGS = os.path.join(LAYER, "settings-measured.json")
RUNBOOK = os.path.join(REPO, "docs", "design", "reachability-dev", "RUN-PHASE54-live.md")

LAUNCH_BEARING = ("preflight", "launch", "session", "pre", "post")
RUNBOOK_BLOCKS = ("common", "materialize", "identity", "park-memory", "preflight",
                  "fresh", "launch", "session", "pre", "post", "fail", "revert",
                  "restore-memory")
LAYER_FUNCTIONS = ("b3_identity_check", "b3_materialize_runner", "b3_stamp_run", "b3_block")
FREEZE_CALL = 'freeze_check.py" verify --runner b3'
SETTINGS_TOKEN = '"$RUNNER_SETTINGS"'
PLUGIN_TOKEN = '"$RUNNER_PLUGIN"'
ONLY_WRITE = 'd["statusLine"]["command"] = cmd.replace("<RUNNER>", runner)'
SESSION_CALL = 'b3_block "$2" session "$3"'
PANE_ARGV = '"${SESSION[@]}"'
EXPECT_COMPARE = ('test "$(identity_field manifest_id)" = "${EXPECT_MANIFEST_ID:-}"',
                  'test "$(identity_field candidate_sha)" = "${EXPECT_CANDIDATE_SHA:-}"')
_CLAUDE_START = re.compile(r"(?:^|[;&|(]|\bexec)\s*claude\b|\bclaude\s+--")

_ARG_VALUE = r"""("[^"]*"|'[^']*'|[^\s`)'"]+)"""


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def block(text, name):
    """Body of `# BLOCK: name` ... `# END: name`, or None."""
    lines = text.splitlines()
    try:
        start = lines.index("# BLOCK: " + name)
        end = lines.index("# END: " + name, start)
    except ValueError:
        return None
    return "\n".join(lines[start + 1:end])


def function_body(text, name):
    """Body of a top-level shell function `name() {` ... `}`, or None."""
    m = re.search(r"(?m)^" + re.escape(name) + r"\(\) \{\n(.*?)^\}$", text, re.S)
    return m.group(1) if m else None


def _code_lines(text):
    return [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]


# --------------------------------------------------------------------------- #
# Predicates
# --------------------------------------------------------------------------- #

def blocks_call_identity_holds(runbook_text):
    """Each launch-bearing block exists and calls b3_identity_check."""
    for name in LAUNCH_BEARING:
        body = block(runbook_text, name)
        if body is None:
            return False
        if not any(re.match(r"\s*b3_identity_check\s+\S", ln) for ln in _code_lines(body)):
            return False
    return True


def no_worktree_copy_holds(common_text):
    """The runner copy comes from git objects: git archive present, no
    working-tree copy tool anywhere in the layer."""
    if re.search(r"\brsync\b|\bcopytree\b|\bditto\b", common_text):
        return False
    if re.search(r"\bcp\s+-[A-Za-z]*[rRa]", common_text):
        return False
    body = function_body(common_text, "b3_materialize_runner")
    if body is None or not re.search(r'git -C "\$REPO" archive "\$sha" plugins/vibe-check', body):
        return False
    return True


_VERSION_COMPARE = (
    re.compile(r"""(=|==|!=)\s*["']?v?\d+\.\d+\.\d+"""),            # x.y.z literal compared
    re.compile(r"--version"),                                         # CLI version output
    re.compile(r"plugin\.json.*\bversion\b|\bversion\b.*plugin\.json"),
)


def no_version_compare_holds(common_text, runbook_text):
    """No code line passes on a version string (the check compares content)."""
    for text in (common_text, runbook_text):
        for ln in _code_lines(text):
            if any(p.search(ln) for p in _VERSION_COMPARE):
                return False
    return True


def no_override_holds(common_text):
    """No skip/force/override switch exists in the layer."""
    if re.search(r"\b[A-Z0-9_]*(SKIP|FORCE|NO_CHECK|OVERRIDE|BYPASS)[A-Z0-9_]*\b", common_text):
        return False
    if re.search(r"--(force|skip|no-check|override|bypass)\b", common_text):
        return False
    return True


def identity_fails_closed_holds(common_text):
    """b3_identity_check runs the freeze check exactly once, never returns
    early, and exits 1 after printing the STOPPING line on a non-zero exit."""
    body = function_body(common_text, "b3_identity_check")
    if body is None or common_text.count(FREEZE_CALL) != 1 or FREEZE_CALL not in body:
        return False
    if re.search(r"(?m)^\s*[^#\n]*\breturn\b", body):
        return False
    stop = body.find('IDENTITY MISMATCH ($label) — STOPPING')
    if stop < 0 or not re.match(r'"\s*\n\s*exit 1\b', body[stop + len('IDENTITY MISMATCH ($label) — STOPPING'):]):
        return False
    return body.index(FREEZE_CALL) < stop


def same_settings_path_holds(common_text, runbook_text):
    """Every --settings / --plugin-dir value in the layer and the runbook is
    the one variable the check uses; the check and a claude launch line both
    carry it."""
    for text in (common_text, runbook_text):
        for flag, token in (("--settings", SETTINGS_TOKEN), ("--plugin-dir", PLUGIN_TOKEN)):
            for m in re.finditer(re.escape(flag) + r"\s+" + _ARG_VALUE, text):
                if m.group(1) != token:
                    return False
    body = function_body(common_text, "b3_identity_check") or ""
    if "--settings " + SETTINGS_TOKEN not in body or "--plugin-dir " + PLUGIN_TOKEN not in body:
        return False
    session = block(runbook_text, "session") or ""
    launch_lines = [ln for ln in _code_lines(session) if re.search(r"\bclaude\b.*--permission-mode", ln)]
    if not launch_lines:
        return False
    return all("--settings " + SETTINGS_TOKEN in ln and "--plugin-dir " + PLUGIN_TOKEN in ln
               for ln in launch_lines)


def single_substitution_holds(common_text):
    """Materialization writes exactly one settings key: statusLine.command,
    replacing the literal <RUNNER>."""
    body = function_body(common_text, "b3_materialize_runner")
    if body is None:
        return False
    writes = re.findall(r"(?m)^\s*d(?:\[[^\]\n]+\])+\s*=(?!=).*$", body)
    if [w.strip() for w in writes] != [ONLY_WRITE]:
        return False
    if re.search(r"\bd\.(update|setdefault|pop|clear)\(|\bdel d\b", body):
        return False
    return True


def _block_names(text):
    return re.findall(r"(?m)^# BLOCK: ([a-z0-9-]+)$", text)


def session_self_check_holds(runbook_text, run_case_text):
    """The identity check that vouches for a run executes in the process
    that becomes `claude`.

    - `session` runs b3_identity_check, then compares the verified
      manifest_id and candidate_sha with the values `launch` handed it, and
      only after both starts claude, by `exec` (the one claude start in the
      runbook);
    - no other block starts claude, and nothing types a launch line into a
      pane (`tmux send-keys` with claude or a LAUNCH variable);
    - `launch` starts the pane with the session block as an argv list
      (`tmux new-session ... "${SESSION[@]}"`) whose command runs
      `b3_block "$2" session "$3"`."""
    session = block(runbook_text, "session")
    launch = block(runbook_text, "launch")
    if session is None or launch is None:
        return False
    for name in _block_names(runbook_text):
        if name == "session":
            continue
        for ln in _code_lines(block(runbook_text, name) or ""):
            if _CLAUDE_START.search(ln):
                return False
    for text in (runbook_text, run_case_text):
        for ln in _code_lines(text):
            if "send-keys" in ln and re.search(r"\bclaude\b|LAUNCH", ln):
                return False
    lines = _code_lines(session)
    starts = [i for i, ln in enumerate(lines) if _CLAUDE_START.search(ln)]
    if len(starts) != 1 or not re.match(r"\s*exec claude\s", lines[starts[0]]):
        return False
    checks = [i for i, ln in enumerate(lines) if re.match(r"\s*b3_identity_check\s+\S", ln)]
    if not checks or checks[0] > starts[0]:
        return False
    for needle in EXPECT_COMPARE:
        at = [i for i, ln in enumerate(lines) if needle in ln]
        if not at or not checks[0] < at[0] < starts[0]:
            return False
    launch_lines = _code_lines(launch)
    panes = [ln for ln in launch_lines if re.search(r"\btmux\s+new-session\b", ln)]
    if not panes or not all(ln.rstrip().endswith(PANE_ARGV) for ln in panes):
        return False
    return SESSION_CALL in launch


# --------------------------------------------------------------------------- #
# Real files
# --------------------------------------------------------------------------- #

class TestRealFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.common = _read(COMMON)
        cls.runbook = _read(RUNBOOK)

    def test_blocks_call_identity(self):
        self.assertTrue(blocks_call_identity_holds(self.runbook))

    def test_no_worktree_copy(self):
        self.assertTrue(no_worktree_copy_holds(self.common))

    def test_no_version_compare(self):
        self.assertTrue(no_version_compare_holds(self.common, self.runbook))
        self.assertTrue(no_version_compare_holds(_read(RUN_CASE), ""))

    def test_no_override(self):
        self.assertTrue(no_override_holds(self.common))
        self.assertTrue(no_override_holds(_read(RUN_CASE)))

    def test_identity_fails_closed(self):
        self.assertTrue(identity_fails_closed_holds(self.common))

    def test_same_settings_path(self):
        self.assertTrue(same_settings_path_holds(self.common, self.runbook))

    def test_single_substitution(self):
        self.assertTrue(single_substitution_holds(self.common))

    def test_session_self_check(self):
        self.assertTrue(session_self_check_holds(self.runbook, _read(RUN_CASE)))

    def test_b3_block_names_its_runbook(self):
        body = function_body(self.common, "b3_block")
        self.assertIn('B3_RUNBOOK=$book bash -c "$script"', body)
        self.assertIn('test -n "${B3_RUNBOOK:-}"', block(self.runbook, "launch"))

    def test_layer_functions_defined(self):
        for name in LAYER_FUNCTIONS:
            self.assertIsNotNone(function_body(self.common, name), name)

    def test_runbook_blocks_present(self):
        for name in RUNBOOK_BLOCKS:
            self.assertIsNotNone(block(self.runbook, name), name)
        for gone in ("resync-cache", "restore-cache", "fingerprint"):
            self.assertIsNone(block(self.runbook, gone), gone)
        self.assertNotIn("cache_unchanged", self.runbook)

    def test_common_block_sources_the_layer(self):
        self.assertIn('source "$REPO/docs/design/b3-ground-truth/b3-runner-v2.12/common.sh"',
                      block(self.runbook, "common"))

    def test_pre_stamps_and_post_compares(self):
        pre = block(self.runbook, "pre")
        self.assertIn('b3_stamp_run "$RUN_DIR"', pre)
        self.assertLess(pre.index("b3_identity_check"), pre.index("b3_stamp_run"))
        post = block(self.runbook, "post")
        self.assertIn("RUN STAMP DOES NOT MATCH THE ACTIVE MANIFEST — p54 fail — STOPPING", post)
        self.assertLess(post.index("b3_identity_check"), post.index("RUN STAMP DOES NOT MATCH"))
        self.assertLess(post.index("RUN STAMP DOES NOT MATCH"), post.index('>> "$REPO/$NOTES"'))

    def test_run_case_routes_every_block_through_b3_block(self):
        text = _read(RUN_CASE)
        self.assertNotIn("p53 ", text)
        for name in ("preflight", "fresh", "launch", "pre", "post", "revert"):
            self.assertRegex(text, r'b3_block "\$RUNBOOK" %s\b' % re.escape(name))
        self.assertNotRegex(text, r"(?m)^[^#]*\bclaude\s+--")

    def test_settings_template_pins(self):
        d = json.loads(_read(SETTINGS))
        self.assertIs(d["enabledPlugins"]["vibe-check@thejuran"], False)
        self.assertEqual(d["env"], {"DISABLE_AUTOUPDATER": "1", "DISABLE_UPDATES": "1"})
        self.assertEqual(d["statusLine"]["command"], "bash <RUNNER>/statusline-capture.sh")


# --------------------------------------------------------------------------- #
# Mutants
# --------------------------------------------------------------------------- #

def _drop_identity_from(runbook_text, name):
    body = block(runbook_text, name)
    assert body is not None and "b3_identity_check" in body, name
    mutated = "\n".join(ln for ln in body.splitlines() if "b3_identity_check" not in ln)
    return runbook_text.replace(body, mutated, 1)


def _insert_into_function(common_text, name, line):
    head = name + "() {\n"
    assert common_text.count(head) == 1, name
    return common_text.replace(head, head + line + "\n", 1)


class TestMutants(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.common = _read(COMMON)
        cls.runbook = _read(RUNBOOK)

    def setUp(self):
        # Pristine first: a mutant test on files that already fail proves nothing.
        self.assertTrue(blocks_call_identity_holds(self.runbook))
        self.assertTrue(no_worktree_copy_holds(self.common))
        self.assertTrue(no_version_compare_holds(self.common, self.runbook))
        self.assertTrue(no_override_holds(self.common))
        self.assertTrue(identity_fails_closed_holds(self.common))
        self.assertTrue(same_settings_path_holds(self.common, self.runbook))
        self.assertTrue(single_substitution_holds(self.common))
        self.assertTrue(session_self_check_holds(self.runbook, _read(RUN_CASE)))

    def _assert_dropping_trips(self, name):
        mutant = _drop_identity_from(self.runbook, name)
        self.assertNotEqual(mutant, self.runbook)
        self.assertFalse(blocks_call_identity_holds(mutant))

    def test_mutant_identity_removed_from_preflight(self):
        self._assert_dropping_trips("preflight")

    def test_mutant_identity_removed_from_launch(self):
        self._assert_dropping_trips("launch")

    def test_mutant_identity_removed_from_pre(self):
        self._assert_dropping_trips("pre")

    def test_mutant_identity_removed_from_post(self):
        self._assert_dropping_trips("post")

    def test_mutant_identity_removed_from_session(self):
        self._assert_dropping_trips("session")
        mutant = _drop_identity_from(self.runbook, "session")
        self.assertFalse(session_self_check_holds(mutant, _read(RUN_CASE)))

    def _session_holds(self, runbook=None, run_case=None):
        return session_self_check_holds(runbook if runbook is not None else self.runbook,
                                        run_case if run_case is not None else _read(RUN_CASE))

    def _replace_in_block(self, name, old, new):
        body = block(self.runbook, name)
        self.assertIn(old, body)
        return self.runbook.replace(body, body.replace(old, new, 1), 1)

    def test_mutant_launch_types_claude_into_existing_server(self):
        # the pre-fix shape: the check ran in the block shell, the pane (env from
        # whichever shell started the tmux server) got the launch line typed in
        body = block(self.runbook, "launch")
        pane = [ln for ln in body.splitlines() if "tmux new-session" in ln][0]
        old_shape = ('  LAUNCH_LINE=$(printf \'%q \' claude --permission-mode manual '
                     '--plugin-dir "$RUNNER_PLUGIN" --settings "$RUNNER_SETTINGS" --model "$MODEL")\n'
                     '  tmux new-session -d -s "p54-$CASE" -c "$CLONE"\n'
                     '  tmux send-keys -t "p54-$CASE" "$LAUNCH_LINE" Enter')
        mutant = self.runbook.replace(body, body.replace(pane, old_shape, 1), 1)
        self.assertNotEqual(mutant, self.runbook)
        self.assertFalse(self._session_holds(mutant))

    def test_mutant_pane_without_session_argv(self):
        # a plain shell in the pane (default/existing server env), session block never run there
        mutant = self._replace_in_block(
            "launch", 'tmux new-session -d -s "p54-$CASE" -c "$CLONE" "${SESSION[@]}"',
            'tmux new-session -d -s "p54-$CASE" -c "$CLONE"')
        self.assertFalse(self._session_holds(mutant))

    def test_mutant_run_case_types_launch_line(self):
        mutant = _read(RUN_CASE).replace(
            'sleep 8\n', 'tmux send-keys -t "$S" "$LAUNCH_LINE" Enter\nsleep 8\n', 1)
        self.assertNotEqual(mutant, _read(RUN_CASE))
        self.assertFalse(self._session_holds(run_case=mutant))

    def test_mutant_exec_before_session_check(self):
        body = block(self.runbook, "session")
        lines = body.splitlines()
        exec_ln = [ln for ln in lines if ln.startswith("exec claude")][0]
        lines.remove(exec_ln)
        lines.insert(lines.index("b3_identity_check 'session'"), exec_ln)
        mutant = self.runbook.replace(body, "\n".join(lines), 1)
        self.assertFalse(self._session_holds(mutant))

    def test_mutant_session_skips_launch_identity_compare(self):
        body = block(self.runbook, "session")
        mutant = self.runbook.replace(
            body, "\n".join(ln for ln in body.splitlines() if "EXPECT_MANIFEST_ID" not in ln), 1)
        self.assertNotEqual(mutant, self.runbook)
        self.assertFalse(self._session_holds(mutant))

    def test_mutant_claude_without_exec(self):
        mutant = self._replace_in_block("session", "exec claude ", "claude ")
        self.assertFalse(self._session_holds(mutant))

    def test_mutant_claude_started_in_launch(self):
        mutant = self._replace_in_block(
            "launch", "echo 'BLOCK OK'",
            'cd "$CLONE" && claude --permission-mode manual --plugin-dir "$RUNNER_PLUGIN" '
            '--settings "$RUNNER_SETTINGS" --model "$MODEL"\necho \'BLOCK OK\'')
        self.assertFalse(self._session_holds(mutant))

    def test_mutant_identity_commented_out(self):
        body = block(self.runbook, "launch")
        mutant = self.runbook.replace(body, body.replace("b3_identity_check", "# b3_identity_check"), 1)
        self.assertFalse(blocks_call_identity_holds(mutant))

    def test_mutant_rsync_copy(self):
        mutant = _insert_into_function(
            self.common, "b3_materialize_runner",
            '  rsync -a --delete "$PLUGIN_ROOT/" "$RUNNER_PLUGIN/"')
        self.assertFalse(no_worktree_copy_holds(mutant))

    def test_mutant_cp_recursive_copy(self):
        mutant = _insert_into_function(
            self.common, "b3_materialize_runner", '  cp -R "$PLUGIN_ROOT" "$RUNNER/plugin/"')
        self.assertFalse(no_worktree_copy_holds(mutant))

    def test_mutant_archive_removed(self):
        mutant = self.common.replace('git -C "$REPO" archive "$sha" plugins/vibe-check',
                                     'tar -c -C "$REPO" plugins/vibe-check', 1)
        self.assertNotEqual(mutant, self.common)
        self.assertFalse(no_worktree_copy_holds(mutant))

    def test_mutant_version_string_pass(self):
        mutant = _insert_into_function(self.common, "b3_identity_check",
                                       '  test "$v" = "2.12.0" && return 0')
        self.assertFalse(no_version_compare_holds(mutant, self.runbook))

    def test_mutant_cli_version_compare_in_runbook(self):
        body = block(self.runbook, "preflight")
        mutant = self.runbook.replace(
            body, body + '\ntest "$(claude --version)" = "$(pin pin-claude-code)" || exit 1', 1)
        self.assertFalse(no_version_compare_holds(self.common, mutant))

    def test_mutant_override_variable(self):
        mutant = _insert_into_function(self.common, "b3_identity_check",
                                       '  test "${B3_SKIP_IDENTITY:-0}" = 1 && return 0')
        self.assertFalse(no_override_holds(mutant))
        self.assertFalse(identity_fails_closed_holds(mutant))

    def test_mutant_identity_early_return(self):
        mutant = _insert_into_function(self.common, "b3_identity_check",
                                       '  test -n "${IDENTITY_LINE:-}" && return 0')
        self.assertFalse(identity_fails_closed_holds(mutant))

    def test_mutant_mismatch_does_not_exit(self):
        mutant = self.common.replace('echo "IDENTITY MISMATCH ($label) — STOPPING"\n    exit 1',
                                     'echo "IDENTITY MISMATCH ($label) — STOPPING"\n    true', 1)
        self.assertNotEqual(mutant, self.common)
        self.assertFalse(identity_fails_closed_holds(mutant))

    def test_mutant_launch_settings_other_path(self):
        body = block(self.runbook, "session")
        mutant = self.runbook.replace(
            body, body.replace('--settings "$RUNNER_SETTINGS"', '--settings "$HOME/.b3/other.json"'), 1)
        self.assertNotEqual(mutant, self.runbook)
        self.assertFalse(same_settings_path_holds(self.common, mutant))

    def test_mutant_check_settings_other_path(self):
        body = function_body(self.common, "b3_identity_check")
        mutant = self.common.replace(
            body, body.replace('--settings "$RUNNER_SETTINGS"', '--settings "$RUNNER/checked.json"'), 1)
        self.assertNotEqual(mutant, self.common)
        self.assertFalse(same_settings_path_holds(mutant, self.runbook))

    def test_mutant_launch_plugin_dir_other_path(self):
        body = block(self.runbook, "session")
        mutant = self.runbook.replace(
            body, body.replace('--plugin-dir "$RUNNER_PLUGIN"', '--plugin-dir "$PLUGIN_ROOT"'), 1)
        self.assertNotEqual(mutant, self.runbook)
        self.assertFalse(same_settings_path_holds(self.common, mutant))

    def test_mutant_second_settings_key_write(self):
        mutant = self.common.replace(
            ONLY_WRITE + "\n", ONLY_WRITE + '\nd["env"]["EXTRA"] = "1"\n', 1)
        self.assertNotEqual(mutant, self.common)
        self.assertFalse(single_substitution_holds(mutant))

    def test_mutant_settings_update_call(self):
        mutant = self.common.replace(
            ONLY_WRITE + "\n", ONLY_WRITE + '\nd.update({"model": "other"})\n', 1)
        self.assertNotEqual(mutant, self.common)
        self.assertFalse(single_substitution_holds(mutant))


if __name__ == "__main__":
    unittest.main()
