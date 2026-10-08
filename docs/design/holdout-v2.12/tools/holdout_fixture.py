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

import hashlib
import io
import json
import os
import secrets
import shutil
import subprocess
import sys
import tarfile


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


# ---------------------------------------------------------------- valid holdout

# A 40-hex revision whose SHA-256 make_valid_holdout adds to the folder's
# kit/b3-exclusions.json commit_sha256 list, so tests can plant an
# "earlier-benchmark commit" without touching the real exclusions.
THROWAWAY_B3_REV = "0123456789abcdef0123456789abcdef01234567"

# Slot -> (repo basename, causal_failure_category or None for quiet).
# C1 and Q2 come from different repos, neither of them in the B3 list.
VALID_LAYOUT = {
    "C1": ("alpha", "missing-input-validation"),
    "C2": ("alpha", "missing-authz-check"),
    "C3": ("beta", "logic-error"),
    "Q1": ("alpha", None),
    "Q2": ("beta", None),
    "Q3": ("beta", None),
}

# Every proof runs the slot's module and checks what it prints, so no proof
# is a text-only grep. Exit 0 means the module still prints "safe".
PROOF_TEMPLATE = """#!/bin/sh
out=$(sh ./%s)
[ "$out" = "safe" ]
"""

# The number of value lines each module carries; every feature commit rewrites
# all of them, so each diff has many changed lines.
_VALUE_LINES = 11


def module_name(slot):
    return "mod_%s.sh" % slot.lower()


def _module_text(slot, version, verdict):
    lines = ["#!/bin/sh", "# module %s" % slot]
    for i in range(1, _VALUE_LINES + 1):
        lines.append('v_%s_%d="value-%s-%d-%s"' % (slot, i, slot, i, version))
    lines.append("echo %s" % verdict)
    return "\n".join(lines) + "\n"


def _head(repo):
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def _export_rev(repo, rev, dest):
    """Extract `git archive <rev>` into `dest` with tarfile (independent of
    the code under test)."""
    data = subprocess.run(["git", "archive", "--format=tar", rev], cwd=repo,
                          env=helper_env(), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=120, check=True
                          ).stdout
    os.makedirs(dest)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall(dest, filter="data")
    return data


def _run_proof_script(script, tree):
    proc = subprocess.run([script], cwd=tree, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=120)
    return proc.returncode, proc.stdout + proc.stderr


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _new_id(taken):
    while True:
        cid = "H-" + secrets.token_hex(4)
        if cid not in taken:
            return cid


def make_valid_holdout(tmp):
    """Build a complete, valid six-case holdout under `<tmp>`.

    Creates `<tmp>/repos/alpha` and `<tmp>/repos/beta` (basenames not in the
    B3 list), runs the real `setup` CLI into `<tmp>/holdout`, then writes the
    six cases exactly as the finder would: case.json, base.tar (git archive of
    the base commit), change.diff (git diff base..feature), key.json,
    provenance.json (organic, screened 3, two rejections), an executable
    proof/run and proof-results.json filled in by actually running the proof.

    Also appends sha256(THROWAWAY_B3_REV) to `<folder>/kit/b3-exclusions.json`
    commit_sha256. Returns (folder, ids_by_slot).
    """
    tmp = os.path.realpath(tmp)
    repos = {}
    for name in ("alpha", "beta"):
        repo = os.path.join(tmp, "repos", name)
        os.makedirs(repo)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.name", "t")
        git(repo, "config", "user.email", "t@t")
        git(repo, "config", "commit.gpgsign", "false")
        write(repo, "README.txt", "%s fixture repo\n" % name)
        for slot, (rname, _) in VALID_LAYOUT.items():
            if rname == name:
                write(repo, module_name(slot), _module_text(slot, "old",
                                                            "safe"))
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "initial")
        repos[name] = os.path.realpath(repo)

    folder = os.path.join(tmp, "holdout")
    argv = [sys.executable, KIT_PY, "--folder", folder, "setup",
            "--skip-system-exclusions"]
    for name in ("alpha", "beta"):
        argv += ["--repo", repos[name]]
    proc = subprocess.run(argv, cwd=tmp, env=kit_env(),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=120)
    if proc.returncode != 0:
        raise AssertionError("holdout setup failed:\n%s%s"
                             % (proc.stdout, proc.stderr))
    folder = os.path.realpath(folder)

    excl_path = os.path.join(folder, "kit", "b3-exclusions.json")
    excl = _load(excl_path)
    excl["commit_sha256"] = sorted(set(excl["commit_sha256"])
                                   | {_sha(THROWAWAY_B3_REV.encode())})
    _write_json(excl_path, excl)

    sealed = os.path.join(folder, "sealed")
    scratch = os.path.join(tmp, "fixture-scratch")
    ids = {}
    for slot, (rname, category) in VALID_LAYOUT.items():
        repo = repos[rname]
        catch = category is not None
        base_rev = _head(repo)
        write(repo, module_name(slot),
              _module_text(slot, "new", "unsafe" if catch else "safe"))
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "change %s" % slot.lower())
        feature_rev = _head(repo)

        cid = _new_id(set(ids.values()))
        ids[slot] = cid
        cdir = os.path.join(sealed, "cases", cid)
        kdir = os.path.join(sealed, "keys", cid)
        os.makedirs(os.path.join(kdir, "proof"))
        os.makedirs(cdir)

        base_dir = os.path.join(scratch, slot, "base")
        changed_dir = os.path.join(scratch, slot, "changed")
        tar_bytes = _export_rev(repo, base_rev, base_dir)
        _export_rev(repo, feature_rev, changed_dir)
        with open(os.path.join(cdir, "base.tar"), "wb") as fh:
            fh.write(tar_bytes)
        diff = subprocess.run(["git", "diff", base_rev, feature_rev],
                              cwd=repo, env=helper_env(),
                              stdout=subprocess.PIPE, timeout=120,
                              check=True).stdout
        with open(os.path.join(cdir, "change.diff"), "wb") as fh:
            fh.write(diff)
        _write_json(os.path.join(cdir, "case.json"),
                    {"id": cid, "base": "base.tar", "diff": "change.diff",
                     "apply_with": "git apply"})

        if catch:
            key = {"slot": slot, "class": "catch",
                   "defect": "fixture defect text %s" % slot,
                   "location": {"file": module_name(slot), "line_start": 3,
                                "line_end": 8},
                   "causal_failure": "fixture causal text %s" % slot,
                   "causal_failure_category": category}
        else:
            key = {"slot": slot, "class": "quiet",
                   "expected_quiet_rationale": "fixture rationale %s" % slot,
                   "supported_behavior": "fixture behavior %s" % slot,
                   "exposure_check": "fixture exposure %s" % slot}
        _write_json(os.path.join(kdir, "key.json"), key)

        rejections = [{"ordinal": n, "rev": "%040x" % (n + 7 * len(ids)),
                       "reason": "fixture rejection %d" % n}
                      for n in (1, 2)]
        _write_json(os.path.join(kdir, "provenance.json"), {
            "slot": slot, "kind": "organic", "source_repo": repo,
            "repo_name": rname, "repo_in_b3": False,
            "base_rev": base_rev, "feature_rev": feature_rev,
            "search": {"budget": 25,
                       "order_rule": "git log --no-merges newest-first",
                       "screened": 3, "rejections": rejections},
            "selected_using_reviewer_output": False,
            "found_at": "2026-01-01T00:00:00Z"})

        run = os.path.join(kdir, "proof", "run")
        with open(run, "w", encoding="utf-8") as fh:
            fh.write(PROOF_TEMPLATE % module_name(slot))
        os.chmod(run, 0o755)
        base_exit, base_out = _run_proof_script(run, base_dir)
        changed_exit, changed_out = _run_proof_script(run, changed_dir)
        if base_exit != 0 or (changed_exit != 0) != catch:
            raise AssertionError("fixture premise failed for %s: base %d, "
                                 "changed %d" % (slot, base_exit,
                                                 changed_exit))
        _write_json(os.path.join(kdir, "proof-results.json"), {
            "runnable": True,
            "base": {"exit": base_exit, "output_sha256": _sha(base_out),
                     "ran_at": "2026-01-01T00:00:00Z"},
            "changed": {"exit": changed_exit,
                        "output_sha256": _sha(changed_out),
                        "ran_at": "2026-01-01T00:00:00Z"}})
    shutil.rmtree(scratch)
    return folder, ids

