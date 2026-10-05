"""gitfixture.py — shared temp-repo helper for tests that drive real git.

Test support only. The module is deliberately not named `test_*` so pytest does
not collect it; test modules import it as a sibling.

Isolation: a temp repo must never inherit the developer's global or system git
config (a global `commit.gpgsign=true`, a global hooks path or an `init` template
would leak into the tests). `helper_env()` points GIT_CONFIG_GLOBAL at the null
device and sets GIT_CONFIG_NOSYSTEM, and every test that runs a production
script as a subprocess passes that env.

`git()` also passes `-c user.*` and `-c commit.gpgsign=false` on the test side
only. Production code must never set gpgsign: the fix agent's commits respect
the owner's signing config. `make_repo` writes the same three keys into the
repo's LOCAL config so the production scripts' own git calls (which get no `-c`
flags) can still commit inside the fixture.
"""

import os
import subprocess


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
