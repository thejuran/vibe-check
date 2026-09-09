#!/usr/bin/env python3
"""Canonical seal-2 append verifier (owned by 38-02; invoked — never re-embedded — by the
checklist gates, 38-04 STEP C, the 38-05 ladder, and the 38-06 phase exit).
Seal-commit derivation is FULL-HISTORY over all branches/tags/remotes (never branch-relative,
never history-simplified away), with the derived pair bound to the scored tree by ancestry asserts.
BYTE-exact: compares raw `git show` bytes, so a CRLF rewrite or any seal-1 byte change
fails; the whitelist suffix is validated with re.fullmatch on bytes (no dollar anchors,
no line splitting). Exit 0 + SEAL2-APPEND-WHITELIST-OK only for a legal pair.
Usage: verify-seal2-append.py [repo-root]   (default: current directory)"""
import re, subprocess, sys
ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
M = 'docs/design/b3-ground-truth/PREREGISTRATION-v2.10.md'
def git(*a):
    return subprocess.check_output(('git', '-C', ROOT) + a)
revs = git('log', '--format=%H', '--full-history', '--simplify-merges', '--topo-order',
           '--reverse', '--branches', '--tags', '--remotes', '--', M).decode().split()
if len(revs) != 2:
    sys.exit('SEAL VERIFIER FAIL: manifest commits != 2 (full-history, all branches/tags/remotes): %r' % revs)
s1c, s2c = revs
for a, b, what in ((s1c, s2c, 'SEAL1 -> SEAL2'), (s1c, 'HEAD', 'SEAL1 -> HEAD'), (s2c, 'HEAD', 'SEAL2 -> HEAD')):
    if subprocess.call(('git', '-C', ROOT, 'merge-base', '--is-ancestor', a, b)) != 0:
        sys.exit('SEAL VERIFIER FAIL: ancestry broken (%s)' % what)
s1 = git('show', revs[0] + ':' + M)
s2 = git('show', revs[1] + ':' + M)
if not s2.startswith(s1):
    sys.exit('SEAL VERIFIER FAIL: SEAL-2 MODIFIED THE SEALED BAR (not a byte-pure append)')
if not s1.endswith(b'\n'):
    sys.exit('SEAL VERIFIER FAIL: seal-1 blob lacks a trailing newline')
WL = re.compile(
    rb'NEW_ANSWER_KEY_COMMIT: [0-9a-f]{40}\n'
    rb'NEW_ANSWER_KEY_SHA256: [0-9a-f]{64}\n'
    rb'DENOM_CATCH_RUNS: [0-9]+\n'
    rb'DENOM_QUIET_RUNS: [0-9]+\n'
    rb'DENOM_TOTAL_RUNS: [0-9]+\n')
suffix = s2[len(s1):]
if not WL.fullmatch(suffix):
    sys.exit('SEAL VERIFIER FAIL: appended bytes violate the ordered whitelist: %r' % suffix)
d = dict(l.split(': ') for l in suffix.decode().strip().split('\n') if l.startswith('DENOM_'))
if int(d['DENOM_TOTAL_RUNS']) != int(d['DENOM_CATCH_RUNS']) + int(d['DENOM_QUIET_RUNS']):
    sys.exit('SEAL VERIFIER FAIL: DENOM_TOTAL_RUNS != CATCH + QUIET')
print('SEAL2-APPEND-WHITELIST-OK')
