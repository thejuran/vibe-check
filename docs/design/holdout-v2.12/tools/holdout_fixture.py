"""holdout_fixture.py — temp-repo and fake-holdout helpers for the holdout kit tests.

Test support only. The module is deliberately not named `test_*` so pytest does
not collect it; test modules import it as a sibling.

The four git helpers are verbatim copies of plugins/vibe-check/scripts/
gitfixture.py. They are copied, not imported: the holdout tools never import
from the shipped plugin.

Isolation: a temp repo must never inherit the developer's global or system git
config (a global `commit.gpgsign=true`, a global hooks path or an `init` template
would leak into the tests). `helper_env()` points GIT_CONFIG_GLOBAL at the null
device and sets GIT_CONFIG_NOSYSTEM, and every test that runs a production
script as a subprocess passes that env.

`git()` also passes `-c user.*` and `-c commit.gpgsign=false` on the test side
only. `make_repo` writes the same three keys into the repo's LOCAL config.

`kit_env()` additionally removes CLAUDECODE and CLAUDE_CONFIG_DIR: the shell
that runs these tests may itself be Claude-spawned, and every kit command
refuses to run there. One explicit test per refusal path puts CLAUDECODE back.
"""

import os
import subprocess
import sys


def helper_env():
    """A copy of os.environ with global and system git config switched off."""
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


def git(repo, *args, check=True):
    """Run git in `repo` (isolated config); raise on failure unless check=False.

    Returns the CompletedProcess with stdout/stderr as text.
    """
    proc = subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "-c", "commit.gpgsign=false", *args],
        cwd=repo, env=helper_env(), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, timeout=120)
    if check and proc.returncode != 0:
        raise AssertionError("git %s failed in %s:\n%s%s"
                             % (args[0] if args else "", repo,
                                proc.stdout, proc.stderr))
    return proc


def make_repo(tmp):
    """Init `<tmp>/repo` on branch main with local identity; return its realpath."""
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "t")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "commit.gpgsign", "false")
    return os.path.realpath(repo)


def write(repo, rel, data):
    """Write text or bytes to `<repo>/<rel>`, creating parent directories."""
    path = os.path.join(repo, rel)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if isinstance(data, str):
        data = data.encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(data)
    return path


TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
KIT_PY = os.path.join(TOOLS_DIR, "holdout_kit.py")


def kit_env():
    """helper_env() without CLAUDECODE / CLAUDE_CONFIG_DIR (a plain Terminal)."""
    env = helper_env()
    env.pop("CLAUDECODE", None)
    env.pop("CLAUDE_CONFIG_DIR", None)
    return env


def make_source_repo(tmp, name="src-repo"):
    """A git repo at `<tmp>/<name>` with one committed file; return its realpath."""
    repo = os.path.join(tmp, name)
    os.makedirs(repo)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "t")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "commit.gpgsign", "false")
    write(repo, "app.py", "print('hello')\n")
    git(repo, "add", "--", "app.py")
    git(repo, "commit", "-q", "-m", "init")
    return os.path.realpath(repo)


def make_fake_holdout(tmp):
    """Run the real `setup` CLI into `<tmp>/holdout`; return the folder realpath.

    Uses `<tmp>/src-repo` as the only eligible repo and always passes
    --skip-system-exclusions (tests never touch Time Machine).
    """
    repo = make_source_repo(tmp)
    folder = os.path.join(os.path.realpath(tmp), "holdout")
    proc = subprocess.run(
        [sys.executable, KIT_PY, "--folder", folder, "setup",
         "--repo", repo, "--skip-system-exclusions"],
        cwd=tmp, env=kit_env(), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, timeout=120)
    if proc.returncode != 0:
        raise AssertionError("holdout setup failed:\n%s%s"
                             % (proc.stdout, proc.stderr))
    return os.path.realpath(folder)
