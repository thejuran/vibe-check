"""holdout_autopilot.py — the owner's one-command run of the holdout.

`bin/holdout autopilot --repo <tuning repo>` runs the whole owner side from
one plain Terminal window, in this fixed order:

  preflight -> finder -> validate -> cross-check (one generation at a time)
  -> seal -> close-sessions -> encrypt -> leakscan -> publish -> scrub
  -> result

The finder and every cross-check generation run HEADLESS, through the kit's
own launchers (bin/finder, bin/crosscheck, bin/crosscheck-rN) with Claude
Code print-mode arguments appended. Each launcher keeps its own config dir,
temp root, settings, guard hook and sandbox. The autopilot adds two controls
on top (no unsandboxed retry, no permission prompt) and removes none: it
never passes a flag that skips settings or hooks, bypasses permissions or
disables session persistence (FORBIDDEN_ARGS, checked on every argv).

What the terminal shows: step names, counts, slot labels, opaque IDs and
fixed lines, then exactly one result line from the resume grammar
(holdout_manifest.RESUME_GRAMMAR). A session's JSON and stderr, and the
output of every kit function the autopilot calls, go to
<H>/tmp/owner/autopilot/ (never archived, removed by scrub). openssl still
asks the owner for the passphrase at the terminal.

Resume: <H>/AUTOPILOT.json records step status, session ids, generation
bookkeeping and slot labels; never a path under sealed/ and never a
session's reply. Every fresh session's id is allocated and journaled BEFORE
the launch (--session-id), so an interrupted session is continued with
--resume, never restarted. On-disk evidence (SEAL.json, the archive and its
recorded hash, the leak ledger, the published copy) beats the journal.

Authentication: credential variables are removed from the environment first,
so the only credential a session can use is the login keyed to its own
config dir. Preflight asks each launcher `auth status --json`; a missing
login stops with one instruction naming the launcher to run /login in.

The autopilot refuses in every Claude-spawned shell (isolated sessions
included): only the owner starts it.

I/O: stdlib only, imports exactly {contextlib, json, os, re, shutil, sys,
time, uuid} plus the kit modules. Every process goes through
holdout_kit.run_argv (argv list, timeout, never a shell).
"""

import contextlib
import json
import os
import re
import shutil
import sys
import time
import uuid

import holdout_kit
import holdout_validate
import holdout_manifest
import holdout_seal
import holdout_archive
import holdout_dryrun

KitError = holdout_kit.KitError

# ---------------------------------------------------------------- constants

# The launchers resolve this on PATH (`exec claude "$@"`); the autopilot
# itself only ever runs <H>/bin/*.
CLAUDE_BIN = "claude"
JOURNAL_RELPATH = "AUTOPILOT.json"
# Written as two literals so this module's text never spells the holdout
# folder's name.
JOURNAL_SCHEMA = "vibe-check-" "holdout-autopilot/1"
LOG_RELDIR = "tmp/owner/autopilot"

# Print mode uses an API key or token from the environment ahead of the
# login stored for a config dir. The autopilot is the top-level process of
# the run, so it removes them from its own environment before launching
# anything: every session then authenticates with its own config dir's login.
STRIPPED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_PROFILE",
                "ANTHROPIC_FEDERATION_RULE_ID", "ANTHROPIC_ORGANIZATION_ID")

DEFAULT_MAX_TURNS = 400
DEFAULT_BUDGET_USD = 40.0
DEFAULT_SESSION_TIMEOUT = 4 * 3600
AUTH_TIMEOUT = 60
MAX_FIX_ROUNDS = 3
MAX_INPUT_RESETS = 2
ALLOWED_TOOLS = "Bash,Read,Edit,Write,Glob,Grep"
SANDBOX_OVERRIDE = json.dumps({"sandbox": {"allowUnsandboxedCommands": False}},
                              separators=(",", ":"))


def print_args(max_turns=DEFAULT_MAX_TURNS, budget_usd=DEFAULT_BUDGET_USD):
    """The print-mode arguments every headless session gets (without the
    prompt and the session identity)."""
    return ["--output-format", "json",
            "--max-turns", str(int(max_turns)),
            "--max-budget-usd", "%.2f" % float(budget_usd),
            "--permission-mode", "dontAsk",
            "--permission-prompts", "none",
            "--allowedTools", ALLOWED_TOOLS,
            "--settings", SANDBOX_OVERRIDE]


PRINT_ARGS = print_args()

# Flags that would drop the launchers' settings or hooks, bypass permissions,
# run a session in the background or disable resume. Built from pieces so the
# names appear nowhere else in this module's text. --permission-mode is
# allowed exactly once, with the value dontAsk.
FORBIDDEN_ARGS = ("--" + "bare", "--safe-mode", "--restricted",
                  "--dangerously-skip-" + "permissions",
                  "--no-session-" + "persistence", "--bg", "--background",
                  "--permission-mode", "bypass" + "Permissions")

PROBE_PROMPT = "Run python3 sandbox-probe.py and reply with its exact output."
PROBE_OK_RE = re.compile(r"OK: sandbox denied (\d+)/(\d+) protected reads")
# README section 6 step 3, verbatim.
FINDER_CHECK_PROMPT = ("Read ../kit/FINDER-BRIEF.md and reply only with its "
                       "first heading. Then run: touch ../sealed/WRITE-CHECK "
                       "&& rm ../sealed/WRITE-CHECK && echo finder-write-ok")
FINDER_CHECK_MARKS = ("# Finder brief", "finder-write-ok")
FINDER_BEGIN_PROMPT = "Read ../kit/FINDER-BRIEF.md and begin."
FINDER_RESUME_PROMPT = (
    "Your previous turn was interrupted. Continue from what is already on "
    "disk: every slot whose sealed/cases/<ID>/provenance.json exists is "
    "finished and must not be changed; for the slot you were working on, "
    "continue its screening from the last ordinal you recorded in the fixed "
    "order, never re-screen a recorded candidate and never change a recorded "
    "selection; then finish the remaining slots exactly as the brief says "
    "and stop.")
FINDER_RESTART_PROMPT = (
    "Read ../kit/FINDER-BRIEF.md. Your previous session was lost. Every slot "
    "whose sealed/cases/<ID>/provenance.json exists is finished and must not "
    "be changed. For each remaining slot follow the brief's fixed screening "
    "order from ordinal 1 (the order rule is deterministic, so the same "
    "candidates come back in the same order), then stop.")
FINDER_REPLACE_PROMPT = (
    "Slots %s were withdrawn and retired. Re-find each of them as a "
    "DIFFERENT change within the same 25-candidate budget; "
    "work/RETIRED-REVISIONS.json lists revisions you must skip. Do not touch "
    "the other slots. Then stop.")
FINDER_FIX_PROMPT = ("bin/holdout validate reported problems. Fix only what "
                     "these lines name, then stop:\n")
XCHECK_BEGIN_PROMPT = "Read CROSSCHECK-BRIEF.md and begin."
XCHECK_BLIND_RETRY_PROMPT = ("Write blind.json for every packet in this "
                             "folder exactly as the brief says, then stop.")
XCHECK_CONTINUE_PROMPT = "The owner has revealed. Continue."
XCHECK_FINAL_RETRY_PROMPT = ("Write final.json for every revealed packet "
                             "exactly as the brief says, then stop.")
RESUME_CHECK_PROMPT_1 = "Reply with the single word ready."
RESUME_CHECK_PROMPT_2 = "Reply with the single word ready again."

# How the CLI says it has no conversation under a --resume id.
NOT_FOUND_RE = re.compile(r"no conversation found", re.I)

STEPS = ("preflight", "finder", "validate", "crosscheck", "seal",
         "close-sessions", "encrypt", "leakscan", "publish", "scrub",
         "result")
DRY_RUN_STEPS = ("preflight", "populate", "validate", "crosscheck", "seal",
                 "close-sessions", "encrypt", "rehash", "leakscan", "scrub",
                 "result")
STATUSES = ("pending", "done", "blocked")

# Fixed instructions printed before a `blocked ...` line. "<H>" is rendered
# as the folder given on the command line; "%s" only ever takes an opaque
# ID, a slot label or a generation number.
STOP_INSTRUCTIONS = {
    "sandbox": (
        "The cross-check sandbox did not deny every protected read. Do not "
        "continue. README section 6 step 2 / section 7 step 5: fix the "
        "cross-check settings or the sandbox, then run bin/holdout autopilot "
        "again."),
    "finder-check": (
        "The finder session could not read the kit or write sealed/. Do not "
        "continue. README section 6 step 3: fix the finder settings, then "
        "run bin/holdout autopilot again."),
    "validation": (
        "validate still reports problems after %d fix rounds. In a new "
        "Terminal window run <H>/bin/holdout validate, fix only what it "
        "names (README 7b iv), then run bin/holdout autopilot again."),
    "disagreement": (
        "Case %s (%s): the independent check disagreed. Follow README 7b: "
        "either write sealed/keys/%s/resolution.md and run crosscheck-reset "
        "%s --reason resolved, or run retire --slot %s --reason owner. Then "
        "run bin/holdout autopilot again (after a retire: bin/holdout "
        "autopilot --replace-retired)."),
    "leakscan": (
        "Leak scan named slots %s. Follow README 7d steps 1-2 (close the "
        "named tuning session, delete the named matches as cleanup), then "
        "run bin/holdout autopilot --replace-retired."),
    "retired": (
        "A sealed case reuses retired material. Run bin/holdout autopilot "
        "--replace-retired to replace it through the finder."),
    "burned": (
        "Cross-check generation %d has already seen a revealed key and its "
        "session cannot be resumed. Run <H>/bin/holdout crosscheck-reset %s "
        "--reason owner for each case it holds, then bin/holdout autopilot "
        "again."),
    "inputs-reset": (
        "Case %s was regenerated twice after its inputs changed. Run "
        "<H>/bin/holdout seal in a new Terminal window to read why, fix it "
        "(README 7b ii), then run bin/holdout autopilot again."),
    "writers": (
        "Close what the line above names, wait a few seconds, then run "
        "bin/holdout autopilot again."),
    "residue": (
        "scrub found residue outside the folder. Delete what the lines above "
        "name, then run bin/holdout autopilot again."),
    "encrypt": (
        "encrypt failed; run <H>/bin/holdout encrypt in a Terminal to see "
        "why"),
    "seal-other": (
        "seal refused for a reason the autopilot does not classify. In a new "
        "Terminal window run <H>/bin/holdout seal to read it, fix what it "
        "names, then run bin/holdout autopilot again."),
    "leakscan-failed": (
        "leakscan could not finish. Run <H>/bin/holdout leakscan --repo "
        "<the tuning repo> in a Terminal to see why, then run bin/holdout "
        "autopilot again."),
    "publish": (
        "publish refused. Run <H>/bin/holdout publish --repo <the tuning "
        "repo> in a Terminal to see why, then run bin/holdout autopilot "
        "again."),
    "scrub": (
        "scrub did not finish. Run <H>/bin/holdout scrub in a Terminal to "
        "see why, then run bin/holdout autopilot again."),
    "rehash": (
        "rehash of the sealed folder did not match the seal. Run "
        "<H>/bin/holdout rehash in a Terminal to see why."),
    "session": (
        "A headless session failed or was interrupted. Run bin/holdout "
        "autopilot again: it resumes the same session. If it fails again, "
        "read the log inside the holdout folder (tmp/owner/autopilot)."),
    "journal-missing": (
        "PROBLEM: the run looks complete but the journal is missing; reply "
        "with the status line you recorded, or run leakscan --from-archive "
        "to re-establish it"),
    "resume-unverified": (
        "Claude Code could not resume a headless session by its id, so an "
        "interrupted run could not continue safely. Do not continue. Update "
        "Claude Code (claude update), then run bin/holdout autopilot again; "
        "if it repeats, run the manual steps in README section 6/7 instead."),
    "resume-lost": (
        "The finder session could not be resumed by its recorded id (see the "
        "log inside the holdout folder). Nothing was re-screened. In a new "
        "Terminal window run <H>/bin/finder --resume to see whether the "
        "session still exists; if it is gone, run bin/holdout autopilot "
        "--restart-finder: it keeps every finished case and starts a fresh "
        "finder session told to finish only the missing slots in the "
        "brief's fixed order."),
}

RUN_SESSION_ARGS_MSG = "run_session needs exactly one of session_id or resume"
ARGV_MSG = ("a headless session's arguments failed the isolation self-check; "
            "nothing was launched")
UNJOURNALED_MSG = ("a session id must be journaled before its session is "
                   "launched; nothing was launched")
JOURNAL_BAD_MSG = ("AUTOPILOT.json is malformed or is not this kit's "
                   "journal; repair it (or remove it deliberately) and run "
                   "this again")
JOURNAL_MODE_MSG = ("AUTOPILOT.json belongs to a %s run of this folder; use "
                    "a fresh folder for the other kind of run")
TTY_MSG = ("run the autopilot from a plain Terminal window: openssl must be "
           "able to prompt")
SETUP_MSG = ("the holdout folder is not set up; run setup first (README "
             "section 6 or 7, step 1)")
NO_CLAUDE_MSG = ("claude is not installed on PATH; install Claude Code, then "
                 "run bin/holdout autopilot again")
TOOL_MSG = "%s is missing (%s); the autopilot needs it"
SETTINGS_MSG = ("the %s settings failed their self-check; run setup again in "
                "a fresh folder")
AUTH_MSG = ("the %s session is not logged in. In a new Terminal window run "
            "%s, type /login, finish the browser login, type /exit, then run "
            "bin/holdout autopilot again.")
REPO_MSG = ("autopilot needs --repo PATH (the tuning repo) for leakscan and "
            "publish")
RESTART_MSG = ("nothing to restart: the finder session was not lost; run "
               "bin/holdout autopilot without --restart-finder")
NOTHING_TO_REPLACE_MSG = "nothing to replace: no retired case is still sealed"
RESULT_GRAMMAR_MSG = ("internal error: the result line does not conform to "
                      "the resume grammar; nothing was printed")
RESULT_UNPROVEN_MSG = ("internal error: a success line needs a scrub that "
                       "returned no residue in this run")
FAILED_LINE = "session %s: failed (see the log inside the holdout folder)"
MISMATCH_LINE = ("session %s: answered under a different session id (see the "
                 "log inside the holdout folder)")
TIMEOUT_LINE = ("session %s: timed out after %d s (see the log inside the "
                "holdout folder)")


def expected_probe_total(gen):
    """Protected reads generation `gen`'s sandbox probe must report denied:
    six base targets plus three per earlier generation."""
    return 6 + 3 * (gen - 1)


# ---------------------------------------------------------------- outcomes


class Stop(Exception):
    """The run stops: `instruction` (fixed text) is printed, then `line`
    (default `blocked <kind>`) as the last line."""

    def __init__(self, kind, instruction=None, line=None):
        Exception.__init__(self, kind)
        self.kind = kind
        self.instruction = instruction
        self.line = line or ("blocked %s" % kind)


class Precondition(KitError):
    """An owner-fixable precondition (TTY, tools, setup, a login): one
    PROBLEM line, exit 1, no result line."""


class SessionResult:
    """What one headless session call returned. `text` (the reply) is kept
    for the parser only; it is never printed."""

    __slots__ = ("session_id", "text", "is_error", "exit_code", "log_path",
                 "not_found", "timed_out")

    def __init__(self, session_id, text, is_error, exit_code, log_path,
                 not_found=False, timed_out=False):
        self.session_id = session_id
        self.text = text
        self.is_error = is_error
        self.exit_code = exit_code
        self.log_path = log_path
        self.not_found = not_found
        self.timed_out = timed_out


# ---------------------------------------------------------------- helpers


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _render(text, h):
    return text.replace("<H>", h)


def _step(name, msg):
    print("step %s: %s" % (name, msg))
    sys.stdout.flush()


def strip_credentials():
    """Remove every STRIPPED_ENV name from this process's environment."""
    for name in STRIPPED_ENV:
        os.environ.pop(name, None)


def new_session_id():
    return str(uuid.uuid4())


def check_argv(argv):
    """KitError unless a session argv carries no forbidden flag, exactly one
    `--permission-mode dontAsk` and exactly one session identity. The prompt
    (the value after -p) is text and is not inspected."""
    args = list(argv)
    rest = args[3:] if len(args) >= 3 and args[1] == "-p" else args[1:]
    modes = [rest[i + 1] if i + 1 < len(rest) else None
             for i, a in enumerate(rest) if a == "--permission-mode"]
    if modes != ["dontAsk"]:
        raise KitError(ARGV_MSG)
    for a in rest:
        if a in FORBIDDEN_ARGS and a != "--permission-mode":
            raise KitError(ARGV_MSG)
    if sum(1 for a in rest if a in ("--session-id", "--resume")) != 1:
        raise KitError(ARGV_MSG)


# ---------------------------------------------------------------- journal


def _fresh_journal():
    return {"schema": JOURNAL_SCHEMA, "mode": None, "started_at": None,
            "preflight": {"resume_session_id": None, "resume_ok": False,
                          "check_session_id": None},
            "steps": {},
            "finder": {"session_id": None, "lost_session_ids": [],
                       "restarts": 0, "fix_rounds": 0, "check_ok": False,
                       "done": False, "resume_failed": False},
            "xcheck": {},
            "replace": {"pending": [], "removed": [], "seal_cleared": False,
                        "prompt_sent": False},
            "input_resets": {},
            "replaced_slots": [], "nonrunnable": 0, "result_line": None}


def journal_path(folder):
    return os.path.join(folder, JOURNAL_RELPATH)


def journal_load(folder):
    """The journal, or a fresh one when AUTOPILOT.json is absent. A symlink,
    unreadable JSON or another schema is a KitError."""
    path = journal_path(folder)
    if not os.path.lexists(path):
        return _fresh_journal()
    if os.path.islink(path):
        raise KitError(JOURNAL_BAD_MSG)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        raise KitError(JOURNAL_BAD_MSG)
    if not isinstance(data, dict) or data.get("schema") != JOURNAL_SCHEMA:
        raise KitError(JOURNAL_BAD_MSG)
    for key, value in _fresh_journal().items():
        if key not in data:
            data[key] = value
        elif isinstance(value, dict) and isinstance(data[key], dict):
            for sub, default in value.items():
                data[key].setdefault(sub, default)
        elif type(value) is not type(data[key]) and value is not None:
            raise KitError(JOURNAL_BAD_MSG)
    return data


def journal_save(folder, j):
    holdout_kit.write_json_atomic(journal_path(folder), j)


def mark(j, step, status, **fields):
    if status not in STATUSES:
        raise KitError("unknown step status %s" % status)
    entry = j["steps"].setdefault(step, {})
    entry["status"] = status
    entry["at"] = _now()
    entry.update(fields)


def _status(j, step):
    return (j["steps"].get(step) or {}).get("status")


def _xentry(j, gen):
    entry = j["xcheck"].setdefault(str(gen), {})
    for key, default in (("session_id", None), ("probe_started", False),
                         ("probe_ok", False), ("begun", False),
                         ("revealed", False), ("continued", False),
                         ("final_done", False)):
        entry.setdefault(key, default)
    return entry


def _journaled_ids(j):
    ids = {j["preflight"].get("resume_session_id"),
           j["preflight"].get("check_session_id"),
           j["finder"].get("session_id")}
    for entry in j["xcheck"].values():
        if isinstance(entry, dict):
            ids.add(entry.get("session_id"))
    ids.discard(None)
    return ids


def _allocate(folder, j, holder, key="session_id"):
    """A fresh session id, written into `holder[key]` and saved to disk
    before anything is launched under it."""
    sid = new_session_id()
    holder[key] = sid
    journal_save(folder, j)
    return sid


def _assert_journaled(folder, sid):
    if sid is None or sid not in _journaled_ids(journal_load(folder)):
        raise KitError(UNJOURNALED_MSG)


# ---------------------------------------------------------------- sessions

_SEQ = [0]


def _log_dir(h):
    owner = os.path.join(h, "tmp", "owner")
    if os.path.islink(owner):
        raise KitError("tmp/owner is a symbolic link; remove it and run this "
                       "again")
    path = os.path.join(h, *LOG_RELDIR.split("/"))
    if os.path.islink(path):
        raise KitError("tmp/owner/autopilot is a symbolic link; remove it "
                       "and run this again")
    os.makedirs(path, mode=0o700, exist_ok=True)
    os.chmod(path, 0o700)
    return path


def _write_log(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data or b"")
    os.chmod(path, 0o600)


def _log_base(h, label):
    _SEQ[0] += 1
    return os.path.join(_log_dir(h), "%s-%s-%03d" % (
        label, time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()), _SEQ[0]))


def _launcher(h, role, gen):
    if role == "finder":
        return "finder", os.path.join(h, "bin", "finder")
    if role == "xcheck":
        if gen is None:
            raise KitError("a cross-check session needs its generation")
        rel = holdout_kit.xcheck_names(gen)["launcher"]
        return os.path.basename(rel), os.path.join(h, *rel.split("/"))
    raise KitError("unknown session role")


def _last_json(data):
    text = (data or b"").decode("utf-8", "replace")
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if isinstance(obj, dict):
                return obj
    try:
        obj = json.loads(text)
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def _ids_match(got, expected):
    return isinstance(got, str) and got == expected


def _is_timeout(exc):
    return str(exc).endswith("(TimeoutExpired)")


def run_session(folder, role, prompt, gen=None, session_id=None, resume=None,
                max_turns=DEFAULT_MAX_TURNS, budget_usd=DEFAULT_BUDGET_USD,
                timeout=DEFAULT_SESSION_TIMEOUT):
    """Run one headless prompt through the role's launcher.

    Exactly one of `session_id` (a fresh session under that id) or `resume`
    (continue that session) must be given. The reply is logged under
    <H>/tmp/owner/autopilot/ and parsed; only a fixed line is ever printed.
    A timeout is a failed, resumable result (the id is kept)."""
    if (session_id is None) == (resume is None):
        raise KitError(RUN_SESSION_ARGS_MSG)
    strip_credentials()
    h = os.path.realpath(folder)
    label, launcher = _launcher(h, role, gen)
    expected = session_id if session_id is not None else resume
    ident = (["--session-id", session_id] if session_id is not None
             else ["--resume", resume])
    argv = [launcher, "-p", prompt] + print_args(max_turns, budget_usd) \
        + ident
    check_argv(argv)
    base = _log_base(h, label)
    try:
        proc = holdout_kit.run_argv(argv, cwd="/", timeout=timeout,
                                    stdin_bytes=b"")
    except KitError as exc:
        if not _is_timeout(exc):
            raise
        _write_log(base + ".json", b"")
        _write_log(base + ".err", b"timed out\n")
        print(TIMEOUT_LINE % (label, max(1, int(timeout))))
        sys.stdout.flush()
        return SessionResult(expected, "", True, None, base + ".json",
                             timed_out=True)
    _write_log(base + ".json", proc.stdout)
    _write_log(base + ".err", proc.stderr)
    reply = _last_json(proc.stdout)
    text = reply.get("result") if isinstance(reply, dict) else None
    text = text if isinstance(text, str) else ""
    raw = ((proc.stdout or b"") + b"\n" + (proc.stderr or b"")).decode(
        "utf-8", "replace")
    not_found = resume is not None and bool(NOT_FOUND_RE.search(raw))
    is_error = (proc.returncode != 0 or reply is None
                or reply.get("is_error") is not False)
    if not is_error and not _ids_match(reply.get("session_id"), expected):
        print(MISMATCH_LINE % label)
        sys.stdout.flush()
        return SessionResult(expected, text, True, proc.returncode,
                             base + ".json")
    if is_error:
        print(FAILED_LINE % label)
        sys.stdout.flush()
    return SessionResult(expected, text, is_error, proc.returncode,
                         base + ".json", not_found=not_found)


def _launch(h, j, role, prompt, gen=None, session_id=None, resume=None,
            **opts):
    """run_session, after checking the id is already in the on-disk
    journal."""
    _assert_journaled(h, session_id if session_id is not None else resume)
    return run_session(h, role, prompt, gen=gen, session_id=session_id,
                       resume=resume, **opts)


# ---------------------------------------------------------------- preflight

FULL_LAYOUT = ("bin/finder", "bin/holdout", "kit", "work", "sealed",
               "xcheck/.claude/settings.json")
POST_ENCRYPT_LAYOUT = ("bin/holdout", "kit/" + holdout_kit.KIT_INVENTORY)


def _tty_ok():
    return os.isatty(0) and os.isatty(1)


def _load_seal_or_none(h):
    path = os.path.join(h, holdout_manifest.SEAL_NAME)
    if os.path.islink(path) or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _archive_verified(h):
    """SEAL.json records archive_sha256 and the archive has exactly that
    hash."""
    seal = _load_seal_or_none(h)
    recorded = seal.get("archive_sha256") if seal else None
    archive = holdout_archive.archive_path(h)
    if not isinstance(recorded, str) or os.path.islink(archive) \
            or not os.path.isfile(archive):
        return False
    return holdout_kit.sha256_file(archive) == recorded


def _replacement_active(j, replace_retired):
    return bool(replace_retired or j["replace"]["pending"])


def _phase(folder, j=None, replace_retired=False):
    """"post-encrypt" once the archive is verified (nothing after encrypt
    launches a session, and scrub may already have removed the workspaces);
    "full" otherwise, and always for a replacement, which deletes the seal
    and the archive first."""
    h = os.path.realpath(folder)
    if replace_retired or (j is not None and _replacement_active(j, False)):
        return "full"
    return "post-encrypt" if _archive_verified(h) else "full"


def _registry(h):
    return holdout_seal._load_registry(h)


def _check_layout(h, phase):
    layout = POST_ENCRYPT_LAYOUT if phase == "post-encrypt" else FULL_LAYOUT
    for rel in layout:
        if not os.path.exists(os.path.join(h, *rel.split("/"))):
            raise Precondition(SETUP_MSG)


def _check_settings(h, reg):
    try:
        settings = holdout_kit.load_json(
            os.path.join(h, "work", ".claude", "settings.json"),
            what="the finder settings")
    except KitError:
        raise Precondition(SETTINGS_MSG % "finder")
    if holdout_kit.finder_settings_problems(settings, h):
        raise Precondition(SETTINGS_MSG % "finder")
    gens = [g["gen"] for g in reg["generations"]] if reg else [1]
    for gen in gens:
        names = holdout_kit.xcheck_names(gen)
        try:
            settings = holdout_kit.load_json(
                os.path.join(h, names["workspace"], ".claude",
                             "settings.json"),
                what="the cross-check settings")
        except KitError:
            raise Precondition(SETTINGS_MSG % "cross-check")
        prior = [holdout_kit.xcheck_names(k) for k in range(1, gen)]
        if holdout_kit.xcheck_settings_problems(settings, h, prior=prior):
            raise Precondition(SETTINGS_MSG % "cross-check")


def _check_tools():
    for name, path in (("openssl", holdout_archive.OPENSSL_BIN),
                       ("tar", holdout_archive.TAR_BIN),
                       ("lsof", holdout_archive.LSOF_BIN),
                       ("pgrep", holdout_archive.PGREP_BIN)):
        if not (os.path.isfile(path) and os.access(path, os.X_OK)):
            raise Precondition(TOOL_MSG % (name, path))


def _check_claude(h):
    try:
        proc = holdout_kit.run_argv([os.path.join(h, "bin", "finder"),
                                     "--version"], cwd="/", timeout=60,
                                    stdin_bytes=b"")
    except KitError:
        raise Precondition(NO_CLAUDE_MSG)
    if proc.returncode != 0:
        raise Precondition(NO_CLAUDE_MSG)


def _auth_targets(reg):
    """(role word, launcher relpath): the finder, generation 1 and every
    later generation that has not been revealed."""
    targets = [("finder", "bin/finder"), ("cross-check", "bin/crosscheck")]
    for g in (reg or {}).get("generations", []):
        if g["gen"] >= 2 and g.get("revealed_at") is None:
            targets.append(("cross-check",
                            holdout_kit.xcheck_names(g["gen"])["launcher"]))
    return targets


def _auth_problem(h, role, rel):
    """None when the launcher's config dir is logged in; else the fixed
    instruction naming that launcher."""
    launcher = os.path.join(h, *rel.split("/"))
    try:
        proc = holdout_kit.run_argv([launcher, "auth", "status", "--json"],
                                    cwd="/", timeout=AUTH_TIMEOUT,
                                    stdin_bytes=b"")
    except KitError:
        proc = None
    status = _last_json(proc.stdout) if proc is not None else None
    if isinstance(status, dict) and status.get("loggedIn") is True:
        return None
    return AUTH_MSG % (role, launcher)


def _probe_generation(reg):
    """The generation the next judging prompt goes to: generation 1 before
    any registry exists, the newest one while it is unrevealed, else None."""
    if not reg or not reg.get("generations"):
        return 1
    newest = reg["generations"][-1]
    return newest["gen"] if newest.get("revealed_at") is None else None


def _session_failed(res):
    """Stop for a failed session (its fixed line is already printed)."""
    raise Stop("other", STOP_INSTRUCTIONS["session"])


def _probe(h, j, gen, opts, step="preflight"):
    """Generation `gen`'s first prompt: the sandbox probe, under the id that
    generation keeps for its whole judging round."""
    x = _xentry(j, gen)
    if x["session_id"] is None:
        _allocate(h, j, x)
    if x["probe_started"]:
        res = _launch(h, j, "xcheck", PROBE_PROMPT, gen=gen,
                      resume=x["session_id"], **opts)
    else:
        x["probe_started"] = True
        journal_save(h, j)
        res = _launch(h, j, "xcheck", PROBE_PROMPT, gen=gen,
                      session_id=x["session_id"], **opts)
    if res.is_error:
        _session_failed(res)
    match = PROBE_OK_RE.search(res.text)
    want = expected_probe_total(gen)
    if not match or int(match.group(1)) != want \
            or int(match.group(2)) != want:
        raise Stop("sandbox", STOP_INSTRUCTIONS["sandbox"])
    x["probe_ok"] = True
    journal_save(h, j)
    if step == "preflight":
        _step(step, "sandbox probe ok (%d/%d)" % (want, want))
    else:
        _step(step, "generation %d probe ok (%d/%d)" % (gen, want, want))


def resume_check(folder, j=None, **opts):
    """Prove resume-by-id on this CLI: a fresh session under an allocated id,
    then a --resume of that id; both must answer under it."""
    h = os.path.realpath(folder)
    if j is None:
        j = journal_load(h)
    pre = j["preflight"]
    pre["resume_ok"] = False
    sid = _allocate(h, j, pre, "resume_session_id")
    first = _launch(h, j, "finder", RESUME_CHECK_PROMPT_1, session_id=sid,
                    **opts)
    if first.is_error or first.session_id != sid:
        raise Stop("other", STOP_INSTRUCTIONS["resume-unverified"])
    second = _launch(h, j, "finder", RESUME_CHECK_PROMPT_2, resume=sid,
                     **opts)
    if second.is_error or second.session_id != sid:
        raise Stop("other", STOP_INSTRUCTIONS["resume-unverified"])
    pre["resume_ok"] = True
    journal_save(h, j)
    _step("preflight", "resume by session id ok")
    return j


def _finder_check(h, j, opts):
    sid = _allocate(h, j, j["preflight"], "check_session_id")
    res = _launch(h, j, "finder", FINDER_CHECK_PROMPT, session_id=sid, **opts)
    if res.is_error:
        _session_failed(res)
    if not all(m in res.text for m in FINDER_CHECK_MARKS):
        raise Stop("sandbox", STOP_INSTRUCTIONS["finder-check"])
    j["finder"]["check_ok"] = True
    journal_save(h, j)
    _step("preflight", "finder check ok")


def preflight(folder, mode, j=None, replace_retired=False,
              max_turns=DEFAULT_MAX_TURNS, budget_usd=DEFAULT_BUDGET_USD,
              session_timeout=DEFAULT_SESSION_TIMEOUT):
    """Every precondition, before any case-finding. Raises Precondition for
    an owner-fixable gap (one PROBLEM line, exit 1) and Stop for a sandbox or
    resume failure. Returns the journal."""
    strip_credentials()
    holdout_kit.refuse_if_claude_spawned(None)
    h = os.path.realpath(folder)
    if not os.path.isdir(h):
        raise Precondition(SETUP_MSG)
    if j is None:
        j = journal_load(h)
    if not _tty_ok():
        raise Precondition(TTY_MSG)
    phase = _phase(h, j, replace_retired)
    _check_layout(h, phase)
    reg = None
    if phase == "full":
        reg = _registry(h)
        _check_settings(h, reg)
    _check_tools()
    if phase == "post-encrypt":
        journal_save(h, j)
        _step("preflight", "ok (archive verified: no session needed)")
        return j
    _check_claude(h)
    targets = _auth_targets(reg)
    for role, rel in targets:
        problem = _auth_problem(h, role, rel)
        if problem:
            raise Precondition(problem)
    _step("preflight", "logins ok (%d)" % len(targets))
    opts = {"max_turns": max_turns, "budget_usd": budget_usd,
            "timeout": session_timeout}
    gen = _probe_generation(reg)
    if gen is not None and (mode == "dry-run"
                            or not _xentry(j, gen)["probe_ok"]):
        _probe(h, j, gen, opts)
    if mode == "dry-run" or not j["preflight"]["resume_ok"]:
        resume_check(h, j, **opts)
    if mode == "dry-run" or not j["finder"]["check_ok"]:
        _finder_check(h, j, opts)
    journal_save(h, j)
    _step("preflight", "ok")
    return j


# ---------------------------------------------------------------- result


def result_line(folder, j, line, scrub_result=None):
    """Print the last line. It must fullmatch the resume grammar, and a
    success line needs the residue list a scrub call returned in this run
    to be []. Returns the exit code (0 proceed, 3 blocking)."""
    kind = holdout_manifest.resume_reply_kind(line)
    if kind is None or line != line.strip():
        raise KitError(RESULT_GRAMMAR_MSG)
    blocking = kind in holdout_manifest.RESUME_BLOCKING_KINDS
    if not blocking and scrub_result != []:
        raise KitError(RESULT_UNPROVEN_MSG)
    j["result_line"] = line
    journal_save(folder, j)
    print(line)
    sys.stdout.flush()
    return 3 if blocking else 0


# ---------------------------------------------------------------- driver


class _Run:
    """One autopilot invocation: folder, journal, options and what this run
    has proven so far."""

    def __init__(self, h, j, mode, repo, opts, replace_retired=False,
                 restart_finder=False, journal_missing=False):
        self.h = h
        self.j = j
        self.mode = mode
        self.repo = repo
        self.opts = opts
        self.replace_retired = replace_retired
        self.restart_finder = restart_finder
        self.journal_missing = journal_missing
        self.scrub_result = None


def _start(folder, mode, repo, replace_retired, restart_finder, max_turns,
           budget_usd, session_timeout):
    strip_credentials()
    holdout_kit.refuse_if_claude_spawned(None)
    h = os.path.realpath(folder)
    if not os.path.isdir(h):
        raise Precondition(SETUP_MSG)
    missing = not os.path.lexists(journal_path(h))
    j = journal_load(h)
    if j["mode"] not in (None, mode):
        raise KitError(JOURNAL_MODE_MSG % j["mode"])
    j["mode"] = mode
    j["started_at"] = j["started_at"] or _now()
    opts = {"max_turns": max_turns, "budget_usd": budget_usd,
            "timeout": session_timeout}
    return _Run(h, j, mode, repo, opts, replace_retired=replace_retired,
                restart_finder=restart_finder,
                journal_missing=missing and _archive_verified(h))


def _step_preflight(run):
    preflight(run.h, run.mode, run.j, replace_retired=run.replace_retired,
              max_turns=run.opts["max_turns"],
              budget_usd=run.opts["budget_usd"],
              session_timeout=run.opts["timeout"])
    mark(run.j, "preflight", "done")
    journal_save(run.h, run.j)


def _not_installed(run):
    raise KitError("the autopilot pipeline is not installed in this kit copy")


_HANDLERS = {"preflight": _step_preflight}


def _drive(run, steps):
    current = None
    try:
        for step in steps:
            current = step
            if step == "result":
                return _result_step(run)
            _HANDLERS.get(step, _not_installed)(run)
    except Stop as stop:
        if stop.instruction:
            print(_render(stop.instruction, run.h))
        mark(run.j, current, "blocked")
        journal_save(run.h, run.j)
        return result_line(run.h, run.j, stop.line)
    return None


def _result_step(run):
    raise KitError("the autopilot pipeline is not installed in this kit copy")


def autopilot(folder, repo, replace_retired=False, restart_finder=False,
              max_turns=DEFAULT_MAX_TURNS, budget_usd=DEFAULT_BUDGET_USD,
              session_timeout=DEFAULT_SESSION_TIMEOUT):
    """The real run; returns the exit code (0 proceed, 3 blocking)."""
    run = _start(folder, "real", repo, replace_retired, restart_finder,
                 max_turns, budget_usd, session_timeout)
    return _drive(run, STEPS)


def dry_run(folder, repo=None, max_turns=DEFAULT_MAX_TURNS,
            budget_usd=DEFAULT_BUDGET_USD,
            session_timeout=DEFAULT_SESSION_TIMEOUT):
    """The same flow on dummy data; never publishes."""
    run = _start(folder, "dry-run", repo, False, False, max_turns,
                 budget_usd, session_timeout)
    return _drive(run, DRY_RUN_STEPS)


# ---------------------------------------------------------------- CLI


def add_parser(sub, name):
    if name != "autopilot":
        raise KitError("unknown autopilot command")
    p = sub.add_parser(
        name, help="run the whole owner side in one command: headless "
                   "finder and cross-check, seal, encrypt, leakscan, "
                   "publish, scrub")
    p.add_argument("--dry-run", action="store_true",
                   help="rehearse on dummy data (never publishes)")
    p.add_argument("--repo", metavar="PATH",
                   help="the tuning repo (leakscan and publish); required "
                        "unless --dry-run")
    p.add_argument("--replace-retired", action="store_true",
                   help="replace every retired case that is still sealed "
                        "(after a leak hit or a retire)")
    p.add_argument("--restart-finder", action="store_true",
                   help="start a fresh finder session after its recorded "
                        "session was lost (finished cases are kept)")
    p.add_argument("--budget-usd", type=float, default=DEFAULT_BUDGET_USD,
                   metavar="USD", help="spend cap per headless prompt")
    p.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS,
                   metavar="N", help="turn cap per headless prompt")
    p.add_argument("--session-timeout", type=float,
                   default=DEFAULT_SESSION_TIMEOUT, metavar="SECONDS",
                   help="wall-clock cap per headless prompt")


def cmd(args):
    strip_credentials()
    holdout_kit.refuse_if_claude_spawned(None)
    opts = {"max_turns": args.max_turns, "budget_usd": args.budget_usd,
            "session_timeout": args.session_timeout}
    try:
        if args.dry_run:
            return dry_run(args.folder, repo=args.repo, **opts)
        if not args.repo:
            raise KitError(REPO_MSG)
        return autopilot(args.folder, args.repo,
                         replace_retired=args.replace_retired,
                         restart_finder=args.restart_finder, **opts)
    except Precondition as exc:
        holdout_kit.print_problem(str(exc))
        return 1
