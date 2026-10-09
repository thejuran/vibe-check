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
    "reveal": (
        "crosscheck-reveal refused. In a new Terminal window run "
        "<H>/bin/holdout crosscheck-reveal --ready to read why, fix what it "
        "names (README 7b), then run bin/holdout autopilot again."),
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

    def __init__(self, kind, instruction=None, line=None, status="blocked"):
        Exception.__init__(self, kind)
        self.kind = kind
        self.instruction = instruction
        self.line = line or ("blocked %s" % kind)
        # "pending" for a resumable stop (a session failed or was lost): the
        # re-run continues the same step with the same session id.
        self.status = status


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
            "replaced_slots": [], "nonrunnable": 0, "prompted": False,
            "result_line": None}


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


def _identity_args(session_id, resume):
    if session_id is not None:
        return ["--session-id", session_id]
    return ["--resume", resume]


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
    ident = _identity_args(session_id, resume)
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
    """Stop for a failed session (its fixed line is already printed); the
    step stays pending so a re-run resumes the same session."""
    raise Stop("other", STOP_INSTRUCTIONS["session"], status="pending")


def _lost(res):
    """The CLI answered that it has no conversation under the id."""
    return res.is_error and res.not_found and not res.timed_out


def _lost_unrevealed(h, j, x):
    """An unrevealed generation's session was lost. That session has seen no
    key, so a fresh session in the same generation is still blind: forget
    the old id (kept in lost_session_ids) and start over from the probe."""
    x["lost_session_ids"] = list(x.get("lost_session_ids") or []) \
        + [x["session_id"]]
    x.update(session_id=None, probe_started=False, probe_ok=False,
             begun=False)
    journal_save(h, j)


def _probe(h, j, gen, opts, step="preflight"):
    """Generation `gen`'s first prompt: the sandbox probe, under the id that
    generation keeps for its whole judging round."""
    x = _xentry(j, gen)
    for attempt in range(2):
        if x["session_id"] is None:
            _allocate(h, j, x)
        if x["probe_started"]:
            res = _launch(h, j, "xcheck", PROBE_PROMPT, gen=gen,
                          resume=x["session_id"], **opts)
            if _lost(res) and attempt == 0:
                _lost_unrevealed(h, j, x)
                continue
        else:
            x["probe_started"] = True
            journal_save(h, j)
            res = _launch(h, j, "xcheck", PROBE_PROMPT, gen=gen,
                          session_id=x["session_id"], **opts)
        break
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


# ---------------------------------------------------------------- kit calls


def _quiet(h, log_name, fn, *args, **kwargs):
    """Run an in-process kit call with its stdout appended to
    <H>/tmp/owner/autopilot/<log_name>.log. Child processes it starts
    (openssl) keep the real terminal, so openssl still prompts there."""
    path = os.path.join(_log_dir(h), log_name + ".log")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as fh:
        with contextlib.redirect_stdout(fh):
            try:
                return fn(*args, **kwargs)
            finally:
                fh.flush()


def _log_lines(h, log_name, lines):
    """Append lines to a step log (never the terminal)."""
    def write():
        for line in lines:
            print(line)
    _quiet(h, log_name, write)


def _seal_exists(h):
    return os.path.lexists(os.path.join(h, holdout_manifest.SEAL_NAME))


def _sealed_present(h):
    """True while any plaintext case file exists (an interrupted scrub can
    leave empty case folders behind)."""
    cases = os.path.join(h, "sealed", "cases")
    if os.path.islink(cases) or not os.path.isdir(cases):
        return False
    try:
        return bool(holdout_kit.walk_regular(cases))
    except KitError:
        return True


def _slots_present(h):
    """{slot: ID} of the cases on disk; a case whose key names no slot is
    left out (validate reports it)."""
    out = {}
    try:
        ids = holdout_kit.case_ids(h)
    except KitError:
        return out
    for cid in ids:
        try:
            out.setdefault(holdout_validate.slot_of(h, cid), cid)
        except KitError:
            continue
    return out


def _done(run, step, msg):
    _step(step, msg)
    mark(run.j, step, "done")
    journal_save(run.h, run.j)


def _skip(run, step, why):
    _done(run, step, "skipped (%s)" % why)


def _begin(run, step):
    mark(run.j, step, "pending")
    journal_save(run.h, run.j)


# ---------------------------------------------------------------- replace

RETIRED_LINE_RE = re.compile(r"^case (C[1-3]|Q[1-3]) \((H-[0-9a-f]{8})\) "
                             r"reuses material retired")


def _retired_present(h):
    """[(ID, slot)] of the current cases whose content matches RETIRED.json
    (holdout_manifest.retired_problems is the one matcher)."""
    if not _sealed_present(h):
        return []
    out = []
    for line in holdout_manifest.retired_problems(h):
        match = RETIRED_LINE_RE.match(line)
        if not match:
            raise KitError("a retired case could not be matched to a slot; "
                           "run bin/holdout seal in a Terminal to see it")
        out.append((match.group(2), match.group(1)))
    return out


def _record_replace_intent(run, present):
    """Journal what will be replaced BEFORE anything is deleted."""
    r = run.j["replace"]
    r["pending"] = [{"id": cid, "slot": slot} for cid, slot in present]
    r["removed"] = []
    r["seal_cleared"] = False
    r["prompt_sent"] = False
    run.j["replaced_slots"] = sorted(set(run.j["replaced_slots"])
                                     | {slot for _, slot in present})
    journal_save(run.h, run.j)


def _remove_case_trees(h, cid):
    for part in ("cases", "keys"):
        path = os.path.join(h, "sealed", part, cid)
        if os.path.islink(path):
            raise KitError("a retired case folder is a symbolic link; "
                           "remove it by hand and run this again")
        if os.path.isdir(path):
            shutil.rmtree(path)


def _finder_replace_slots(run):
    """The slots the finder must re-find: always from the journal's intent
    record, never from a disk scan after the deletion."""
    return sorted({e["slot"] for e in run.j["replace"]["pending"]})


def _replace_step(run):
    """Start or continue a replacement; True when one is in progress."""
    h, j = run.h, run.j
    r = j["replace"]
    if not _replacement_active(j, run.replace_retired):
        return False
    if not r["pending"]:
        present = _retired_present(h)
        if not present:
            if j["replaced_slots"] and j["finder"]["done"]:
                _step("replace", "nothing left to replace")
                return False
            raise KitError(NOTHING_TO_REPLACE_MSG)
        _record_replace_intent(run, present)
    for entry in r["pending"]:
        if entry["id"] in r["removed"]:
            continue
        _remove_case_trees(h, entry["id"])
        r["removed"].append(entry["id"])
        journal_save(h, j)
    if not r["seal_cleared"]:
        seal = os.path.join(h, holdout_manifest.SEAL_NAME)
        if os.path.lexists(seal):
            os.remove(seal)
        archive_dir = os.path.dirname(holdout_archive.archive_path(h))
        if os.path.isdir(archive_dir) and not os.path.islink(archive_dir):
            shutil.rmtree(archive_dir)
        r["seal_cleared"] = True
        journal_save(h, j)
    _step("replace", "removed %d retired case(s), slots %s"
          % (len(r["pending"]), ",".join(_finder_replace_slots(run))))
    j["finder"]["done"] = False
    _begin(run, "finder")
    return True


def _clear_replacement_if_done(run, present):
    pending = run.j["replace"]["pending"]
    if pending and all(present.get(e["slot"]) not in (None, e["id"])
                       for e in pending):
        run.j["replace"]["pending"] = []
        run.j["replace"]["prompt_sent"] = False
        journal_save(run.h, run.j)


# ---------------------------------------------------------------- finder


def _finder_after(run, res):
    if res.is_error:
        _session_failed(res)
    present = _slots_present(run.h)
    _clear_replacement_if_done(run, present)
    run.j["finder"]["done"] = True
    _done(run, "finder", "done (%d of 6 slots on disk)" % len(present))


def _restart_finder(run):
    """Only under --restart-finder: a NEW session (id journaled first) told
    to finish the missing slots; finished cases stay as they are."""
    h, j = run.h, run.j
    f = j["finder"]
    if f["session_id"] is not None:
        f["lost_session_ids"].append(f["session_id"])
    f["restarts"] += 1
    f["resume_failed"] = False
    f["started_at"] = _now()
    _begin(run, "finder")
    sid = _allocate(h, j, f)
    _step("finder", "starting a fresh session (restart %d)" % f["restarts"])
    res = _launch(h, j, "finder", FINDER_RESTART_PROMPT, session_id=sid,
                  **run.opts)
    _finder_after(run, res)


def _lost_finder(run):
    """The CLI could not find the finder session by its id. Never a silent
    restart: stop, unless the owner passed --restart-finder."""
    if not run.restart_finder:
        raise Stop("other", STOP_INSTRUCTIONS["resume-lost"],
                   status="pending")
    _restart_finder(run)


def _resume_finder(run, prompt):
    """--resume the recorded finder session; returns the result, or handles
    a lost session."""
    h, j = run.h, run.j
    f = j["finder"]
    res = _launch(h, j, "finder", prompt, resume=f["session_id"], **run.opts)
    if _lost(res):
        f["resume_failed"] = True
        journal_save(h, j)
        _lost_finder(run)
        return None
    return res


def _step_finder(run):
    h, j = run.h, run.j
    f = j["finder"]
    replacing = _replace_step(run)
    pending = j["replace"]["pending"]
    if not replacing and _seal_exists(h):
        return _skip(run, "finder", "sealed")
    if f["done"] and not pending:
        return _skip(run, "finder", "done")
    if f["session_id"] is None and not pending \
            and len(_slots_present(h)) == len(holdout_kit.SLOTS):
        f["done"] = True
        return _done(run, "finder", "done (six cases on disk)")
    if run.restart_finder and f["resume_failed"]:
        return _restart_finder(run)
    if f["session_id"] is None:
        prompt = FINDER_BEGIN_PROMPT
        if pending:
            prompt = FINDER_REPLACE_PROMPT % ",".join(
                _finder_replace_slots(run))
            j["replace"]["prompt_sent"] = True
        f["started_at"] = _now()
        mark(j, "finder", "pending")
        sid = _allocate(h, j, f)
        _step("finder", "session started")
        res = _launch(h, j, "finder", prompt, session_id=sid, **run.opts)
        return _finder_after(run, res)
    if pending and not j["replace"]["prompt_sent"]:
        prompt = FINDER_REPLACE_PROMPT % ",".join(_finder_replace_slots(run))
        j["replace"]["prompt_sent"] = True
    else:
        prompt = FINDER_RESUME_PROMPT
    _begin(run, "finder")
    _step("finder", "resuming the recorded session")
    res = _resume_finder(run, prompt)
    if res is not None:
        _finder_after(run, res)


# ---------------------------------------------------------------- validate


def _step_validate(run):
    h, j = run.h, run.j
    if _seal_exists(h):
        return _skip(run, "validate", "sealed")
    _begin(run, "validate")
    f = j["finder"]
    while True:
        checks = _quiet(h, "validate", holdout_validate.validate_folder, h)
        names = []
        for c in checks:
            if c.name not in names:
                names.append(c.name)
        failed = [c for c in checks if not c.ok]
        if not failed:
            _step("validate", "OK (%d checks)" % len(names))
            break
        failed_names = {c.name for c in failed}
        _step("validate", "PROBLEM (%d of %d checks failed)"
              % (len(failed_names), len(names)))
        _log_lines(h, "validate", ["%s: %s" % (c.name, c.message)
                                   for c in failed])
        if run.mode != "real" or f["session_id"] is None \
                or f["fix_rounds"] >= MAX_FIX_ROUNDS:
            raise Stop("validation", STOP_INSTRUCTIONS["validation"]
                       % f["fix_rounds"])
        f["fix_rounds"] += 1
        journal_save(h, j)
        _step("validate", "fix round %d: resuming the finder"
              % f["fix_rounds"])
        prompt = FINDER_FIX_PROMPT + "\n".join(
            "%s: %s" % (c.name, c.message) for c in failed)
        res = _resume_finder(run, prompt)
        if res is not None and res.is_error:
            _session_failed(res)
    j["nonrunnable"] = _quiet(h, "validate",
                              holdout_validate.nonrunnable_count, h)
    _clear_replacement_if_done(run, _slots_present(h))
    _done(run, "validate", "non-runnable cases: %d" % j["nonrunnable"])


# ---------------------------------------------------------------- crosscheck


def _generation_revealed(entry):
    return entry.get("revealed_at") is not None


def _ensure_login(run, gen):
    """A generation minted during the run has a fresh config dir: it needs
    its own login before its first prompt."""
    if gen < 2:
        return
    problem = _auth_problem(run.h, "cross-check",
                            holdout_kit.xcheck_names(gen)["launcher"])
    if problem:
        raise Precondition(problem)


def _prepare_missing(run):
    h = run.h
    need = [cid for cid in holdout_kit.case_ids(h)
            if not (holdout_seal._load_ledger(h, cid) or {}).get("xid")]
    if need:
        mapping = _quiet(h, "crosscheck", holdout_seal.prepare_crosscheck, h)
        _step("crosscheck", "prepared %d blind packet(s)" % len(mapping))


def _xcheck_failed(res):
    if res.is_error:
        _session_failed(res)


class _LostSession(Exception):
    """An unrevealed generation's --resume found no conversation."""


def _blind_call(run, gen, x, prompt):
    res = _launch(run.h, run.j, "xcheck", prompt, gen=gen,
                  resume=x["session_id"], **run.opts)
    if _lost(res):
        raise _LostSession()
    _xcheck_failed(res)


def _blind_round(run, gen, x, missing):
    """Probe (once per session), begin, and one retry for missing blind
    verdicts, all in a generation that has not been revealed."""
    h, j = run.h, run.j
    if x["session_id"] is None or not x["probe_ok"]:
        _ensure_login(run, gen)
    if x["session_id"] is None:
        _allocate(h, j, x)
    if not x["probe_ok"]:
        _probe(h, j, gen, run.opts, step="crosscheck")
    if not x["begun"]:
        x["begun"] = True
        journal_save(h, j)
        _blind_call(run, gen, x, XCHECK_BEGIN_PROMPT)
    tries = 0
    while missing("blind.json"):
        if tries >= 1:
            raise Stop("other", STOP_INSTRUCTIONS["session"],
                       status="pending")
        tries += 1
        _blind_call(run, gen, x, XCHECK_BLIND_RETRY_PROMPT)


def _judge_generation(run, entry, packets):
    h, j = run.h, run.j
    gen, ws = entry["gen"], entry["workspace"]
    x = _xentry(j, gen)

    def missing(name):
        return [led["xid"] for _, led in packets
                if not os.path.lexists(os.path.join(h, ws, led["xid"],
                                                    name))]

    if not _generation_revealed(entry):
        for attempt in range(2):
            try:
                _blind_round(run, gen, x, missing)
                break
            except _LostSession:
                if attempt:
                    raise Stop("other", STOP_INSTRUCTIONS["session"],
                               status="pending")
                _lost_unrevealed(h, j, x)
        _step("crosscheck", "generation %d blind verdicts written (%d)"
              % (gen, len(packets)))
        try:
            ids = _quiet(h, "crosscheck", holdout_seal.reveal_workspace, h,
                         gen)
        except KitError as exc:
            _log_lines(h, "crosscheck", [str(exc)])
            _step("crosscheck", "reveal refused (see the log inside the "
                                "holdout folder)")
            raise Stop("other", STOP_INSTRUCTIONS["reveal"])
        x["revealed"] = True
        journal_save(h, j)
        _step("crosscheck", "generation %d revealed (%d packet(s))"
              % (gen, len(ids)))
    need = missing("final.json")
    if need:
        burned = STOP_INSTRUCTIONS["burned"] % (gen, packets[0][0])
        if x["session_id"] is None:
            raise Stop("other", burned)
        for attempt in range(2):
            prompt = (XCHECK_FINAL_RETRY_PROMPT if x["continued"]
                      else XCHECK_CONTINUE_PROMPT)
            x["continued"] = True
            journal_save(h, j)
            res = _launch(h, j, "xcheck", prompt, gen=gen,
                          resume=x["session_id"], **run.opts)
            if _lost(res):
                raise Stop("other", burned)
            _xcheck_failed(res)
            if not missing("final.json"):
                break
        if missing("final.json"):
            raise Stop("other", STOP_INSTRUCTIONS["session"],
                       status="pending")
        _step("crosscheck", "generation %d final verdicts written (%d)"
              % (gen, len(packets)))
    x["final_done"] = True
    journal_save(h, j)


def _judge_all(run):
    _prepare_missing(run)
    reg = _registry(run.h)
    for entry in (reg or {}).get("generations", []):
        packets = holdout_seal._live_packets(run.h, entry)
        if packets:
            _judge_generation(run, entry, packets)


def _dry_regenerate(run):
    """Dry run only: send case C1 through a fresh generation so one real
    headless judging round runs on dummy data."""
    h = run.h
    reg = _registry(h)
    gens = (reg or {}).get("generations", [])
    if len(gens) != 1 or not _generation_revealed(gens[0]):
        return
    cid = _slots_present(h).get("C1")
    if cid is None:
        raise KitError("the dummy holdout has no C1 case")
    _quiet(h, "crosscheck", holdout_seal.reset_crosscheck, h, cid, "owner")
    _quiet(h, "crosscheck", holdout_seal.prepare_crosscheck, h, cid)
    _step("crosscheck", "case %s sent to a fresh generation" % cid)


def _step_crosscheck(run):
    if _seal_exists(run.h):
        return _skip(run, "crosscheck", "sealed")
    _begin(run, "crosscheck")
    if run.mode == "dry-run":
        _dry_regenerate(run)
    _judge_all(run)
    _done(run, "crosscheck", "every case has a final verdict")


# ---------------------------------------------------------------- seal

STALE_RE = re.compile(r"workspace xcheck(?:-r([0-9]+))?, which had already")


def _classify_blocker(line):
    """(kind, slot) of a seal blocker line. The line itself is only ever
    logged."""
    slot = None
    match = re.match(r"^Case (C[1-3]|Q[1-3]):", line)
    if match:
        slot = match.group(1)
    if "the independent check disagreed" in line:
        return "disagreement", slot
    if "sealed inputs changed after the cross-check" in line:
        return "inputs-changed", slot
    if line.startswith("validation failed"):
        return "validation", None
    if "had already seen a revealed key" in line:
        return "burned", slot
    if "reuses material retired" in line:
        return "retired", None
    return "other", None


def _step_seal(run):
    h, j = run.h, run.j
    if _seal_exists(h):
        return _skip(run, "seal", "SEAL.json exists")
    _begin(run, "seal")
    revalidated = False
    while True:
        blockers = _quiet(h, "seal", holdout_seal.seal_blockers, h)
        if not blockers:
            seal = _quiet(h, "seal", holdout_seal.do_seal, h)
            return _done(run, "seal", "sealed %d cases" % len(seal["cases"]))
        _log_lines(h, "seal", blockers)
        kind, slot = _classify_blocker(blockers[0])
        ids = _slots_present(h)
        cid = ids.get(slot) if slot else None
        if kind == "disagreement" and cid:
            raise Stop("disagreement", STOP_INSTRUCTIONS["disagreement"]
                       % (cid, slot, cid, cid, slot))
        if kind == "inputs-changed" and cid:
            n = j["input_resets"].get(cid, 0)
            if n >= MAX_INPUT_RESETS:
                raise Stop("other", STOP_INSTRUCTIONS["inputs-reset"] % cid)
            j["input_resets"][cid] = n + 1
            journal_save(h, j)
            _quiet(h, "seal", holdout_seal.reset_crosscheck, h, cid,
                   "inputs-changed")
            _quiet(h, "seal", holdout_seal.prepare_crosscheck, h, cid)
            _step("seal", "case %s changed after its cross-check: judging it "
                          "again in a fresh generation" % cid)
            _judge_all(run)
            continue
        if kind == "validation" and not revalidated:
            revalidated = True
            j["steps"].pop("validate", None)
            _step_validate(run)
            _begin(run, "seal")
            continue
        if kind == "validation":
            raise Stop("validation", STOP_INSTRUCTIONS["validation"]
                       % j["finder"]["fix_rounds"])
        if kind == "burned" and cid:
            match = STALE_RE.search(blockers[0])
            gen = int(match.group(1)) if match and match.group(1) else 1
            raise Stop("other", STOP_INSTRUCTIONS["burned"] % (gen, cid))
        if kind == "retired":
            raise Stop("other", STOP_INSTRUCTIONS["retired"])
        _step("seal", "refused (see the log inside the holdout folder)")
        raise Stop("other", STOP_INSTRUCTIONS["seal-other"])


# ---------------------------------------------------------------- archive


def _step_close(run):
    if run.journal_missing:
        return _skip(run, "close-sessions", "journal missing")
    if _archive_verified(run.h):
        return _skip(run, "close-sessions", "archive verified")
    _begin(run, "close-sessions")
    _step("close-sessions", "no session running")
    try:
        _quiet(run.h, "close-sessions", holdout_archive.require_no_writers,
               run.h)
    except KitError as exc:
        holdout_kit.print_problem(str(exc))
        raise Stop("other", STOP_INSTRUCTIONS["writers"])
    _done(run, "close-sessions", "no other process holds the folder")


def _encrypt_evidence(run):
    return _archive_verified(run.h)


def _step_encrypt(run):
    if run.journal_missing:
        return _skip(run, "encrypt", "journal missing")
    if _encrypt_evidence(run):
        return _skip(run, "encrypt", "archive verified")
    _begin(run, "encrypt")
    _step("encrypt", "openssl will ask for the passphrase (twice, then once "
                     "to verify)")
    try:
        _quiet(run.h, "encrypt", holdout_archive.encrypt, run.h)
    except KitError as exc:
        _log_lines(run.h, "encrypt", [str(exc)])
        if run.mode == "dry-run":
            raise Stop("dry-run-failed", STOP_INSTRUCTIONS["encrypt"],
                       line="dry run ok no-prompt")
        raise Stop("other", STOP_INSTRUCTIONS["encrypt"])
    run.j["prompted"] = True
    _done(run, "encrypt", "archive written and verified")


def _step_rehash(run):
    h = run.h
    if not _sealed_present(h):
        return _skip(run, "rehash", "plaintext already removed")
    result = _quiet(h, "rehash", holdout_manifest.rehash_folder,
                    os.path.join(h, holdout_manifest.SEAL_NAME),
                    os.path.join(h, "sealed"))
    if not result.get("ok"):
        raise Stop("other", STOP_INSTRUCTIONS["rehash"])
    _done(run, "rehash", "all %d cases match the seal" % len(result["cases"]))


def _leak_hits(result):
    return result["hits"]


def _unreplaced_slots(h):
    """Slots of every case some leak scan named that is still in the seal."""
    seal = _load_seal_or_none(h) or {}
    cases = seal.get("cases") if isinstance(seal.get("cases"), dict) else {}
    path = os.path.join(h, holdout_manifest.LEAKSCAN_RELPATH)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            ledger = json.load(fh)
        scans = ledger["scans"]
        named = {cid for scan in scans for cid in scan["hit_case_ids"]}
    except (OSError, ValueError, KeyError, TypeError):
        return []
    return sorted({cases[cid].get("slot") for cid in named
                   if cid in cases and isinstance(cases[cid], dict)}
                  - {None})


def _step_leakscan(run):
    h, j = run.h, run.j
    if run.journal_missing:
        return _skip(run, "leakscan", "journal missing")
    seal = _load_seal_or_none(h)
    if seal is not None and not holdout_manifest.leak_ledger_problems(h,
                                                                      seal):
        return _skip(run, "leakscan", "recorded for this seal")
    _begin(run, "leakscan")
    from_archive = not _sealed_present(h)
    if from_archive:
        _step("leakscan", "openssl will ask for the passphrase (to read the "
                          "archive)")
    try:
        result = _quiet(h, "leakscan", holdout_archive.leakscan, h,
                        repo=run.repo, from_archive=from_archive)
    except KitError as exc:
        _log_lines(h, "leakscan", [str(exc)])
        raise Stop("other", STOP_INSTRUCTIONS["leakscan-failed"])
    hits = _leak_hits(result)
    _step("leakscan", "%d match(es) across %d probes"
          % (len(hits), result["probes"]))
    if hits:
        slots = sorted(set(result["hit_slots"]))
        j["replaced_slots"] = sorted(set(j["replaced_slots"]) | set(slots))
        journal_save(h, j)
        raise Stop("leakscan", STOP_INSTRUCTIONS["leakscan"]
                   % ",".join(slots))
    unreplaced = _unreplaced_slots(h)
    if unreplaced:
        raise Stop("leakscan", STOP_INSTRUCTIONS["leakscan"]
                   % ",".join(unreplaced))
    _done(run, "leakscan", "clean")


def _published(run):
    dest = os.path.join(run.repo or "",
                        *holdout_manifest.SEAL_RELPATH.split("/"))
    src = os.path.join(run.h, holdout_manifest.SEAL_NAME)
    if not run.repo or os.path.islink(dest) or not os.path.isfile(dest) \
            or not os.path.isfile(src):
        return False
    with open(dest, "rb") as a, open(src, "rb") as b:
        return a.read() == b.read()


def _step_publish(run):
    h = run.h
    if run.journal_missing:
        return _skip(run, "publish", "journal missing")
    if _published(run):
        return _skip(run, "publish", "already published")
    _begin(run, "publish")
    try:
        _quiet(h, "publish", holdout_manifest.publish, h, run.repo)
    except KitError as exc:
        msg = str(exc)
        _log_lines(h, "publish", [msg])
        if "has not been replaced" in msg or "leak" in msg \
                or "reuses material retired" in msg:
            slots = _unreplaced_slots(h) or run.j["replaced_slots"]
            raise Stop("leakscan", STOP_INSTRUCTIONS["leakscan"]
                       % (",".join(slots) or "named in LEAKSCAN.json"))
        raise Stop("other", STOP_INSTRUCTIONS["publish"])
    _done(run, "publish", "SEAL.json published")


def _scrub_residue(residue):
    return list(residue)


def _step_scrub(run):
    """Never skipped: every run that gets here calls holdout_archive.scrub,
    which re-verifies the archive, removes whatever non-survivor remains,
    re-walks the survivors and checks the residue outside the folder. An
    absent sealed/ proves only that a deletion ran, not that it finished."""
    h = run.h
    _begin(run, "scrub")
    try:
        raw = _quiet(h, "scrub", holdout_archive.scrub, h)
    except KitError as exc:
        if "still in use" in str(exc):
            holdout_kit.print_problem(str(exc))
            raise Stop("other", STOP_INSTRUCTIONS["writers"])
        _step("scrub", "refused (see the log inside the holdout folder)")
        raise Stop("other", STOP_INSTRUCTIONS["scrub"])
    residue = _scrub_residue(raw)
    if residue:
        for path in residue:
            holdout_kit.print_problem("residue: %s — delete it by hand"
                                      % path)
        raise Stop("residue", STOP_INSTRUCTIONS["residue"])
    run.scrub_result = raw
    _done(run, "scrub", "plaintext removed")


# ---------------------------------------------------------------- result


def _retired_empty(h):
    try:
        return holdout_manifest.load_retired(h)["retired"] == []
    except KitError:
        return False


def _proven_complete(run):
    """Without a journal the status word is never guessed: `sealed` only
    when the repo holds this exact SEAL.json and nothing was ever retired
    (so no replacement can be hidden)."""
    return _published(run) and _retired_empty(run.h)


def _result_step(run):
    h, j = run.h, run.j
    if run.journal_missing:
        if not _proven_complete(run):
            print(STOP_INSTRUCTIONS["journal-missing"])
            sys.stdout.flush()
            return 1
        line = "sealed"
    elif run.mode == "dry-run":
        line = ("dry run ok prompted sandbox=ok" if j.get("prompted")
                else "dry run ok no-prompt")
    else:
        slots = sorted(set(j["replaced_slots"]))
        line = ("replaced slots=" + ",".join(slots)) if slots else "sealed"
        if j["nonrunnable"]:
            line += " non-runnable=%d" % j["nonrunnable"]
    mark(j, "result", "done")
    return result_line(h, j, line, run.scrub_result)


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
    if restart_finder and not j["finder"]["resume_failed"]:
        raise KitError(RESTART_MSG)
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


def _step_populate(run):
    h = run.h
    if _seal_exists(h) or holdout_kit.case_ids(h):
        return _skip(run, "populate", "cases exist")
    _quiet(h, "populate", holdout_dryrun.populate, h)
    _done(run, "populate", "6 synthetic cases written")


def _real_handlers():
    """Step name -> handler function name (looked up at call time)."""
    return {"preflight": "_step_preflight", "finder": "_step_finder",
            "validate": "_step_validate", "crosscheck": "_step_crosscheck",
            "seal": "_step_seal", "close-sessions": "_step_close",
            "encrypt": "_step_encrypt", "leakscan": "_step_leakscan",
            "publish": "_step_publish", "scrub": "_step_scrub"}


def _dry_handlers():
    """The dry run's steps: the real ones minus the finder, plus populate
    and rehash. Nothing here copies SEAL.json into the tuning repo."""
    return {"preflight": "_step_preflight", "populate": "_step_populate",
            "validate": "_step_validate", "crosscheck": "_step_crosscheck",
            "seal": "_step_seal", "close-sessions": "_step_close",
            "encrypt": "_step_encrypt", "rehash": "_step_rehash",
            "leakscan": "_step_leakscan", "scrub": "_step_scrub"}


def _drive(run, steps, handlers):
    module = sys.modules[__name__]
    current = None
    try:
        for step in steps:
            current = step
            if step == "result":
                return _result_step(run)
            getattr(module, handlers[step])(run)
    except Stop as stop:
        if stop.instruction:
            print(_render(stop.instruction, run.h))
        mark(run.j, current, stop.status)
        journal_save(run.h, run.j)
        return result_line(run.h, run.j, stop.line)
    raise KitError("the step list has no result step")


def autopilot(folder, repo, replace_retired=False, restart_finder=False,
              max_turns=DEFAULT_MAX_TURNS, budget_usd=DEFAULT_BUDGET_USD,
              session_timeout=DEFAULT_SESSION_TIMEOUT):
    """The real run; returns the exit code (0 proceed, 3 blocking)."""
    run = _start(folder, "real", repo, replace_retired, restart_finder,
                 max_turns, budget_usd, session_timeout)
    return _drive(run, STEPS, _real_handlers())


def dry_run(folder, repo=None, max_turns=DEFAULT_MAX_TURNS,
            budget_usd=DEFAULT_BUDGET_USD,
            session_timeout=DEFAULT_SESSION_TIMEOUT):
    """The same flow on dummy data (six synthetic cases, one real headless
    judging round in a fresh generation); SEAL.json never leaves the
    folder."""
    run = _start(folder, "dry-run", repo, False, False, max_turns,
                 budget_usd, session_timeout)
    return _drive(run, DRY_RUN_STEPS, _dry_handlers())


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
