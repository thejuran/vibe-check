# Phase 37: Close - Context

**Gathered:** 2026-07-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Ship v2.9. Bump `plugins/vibe-check/.claude-plugin/plugin.json` 2.8.0 → 2.9.0, create the
annotated tag `v2.9`, publish per the standing directive (merge/ff `main`, push main + tag +
branch), and run the milestone audit. The v2.8 evidence debt needs no separate retroactive
audit — it became v2.9 Phase-35 requirements, so the v2.9 audit covers it. (CLOSE-01; boundary
fixed by ROADMAP.md.)

</domain>

<decisions>
## Implementation Decisions

### Publish surface & privacy (owner decision 2026-07-05)
- **D-01:** Publish AS-IS. The committed B3 ground-truth kit (`docs/design/b3-ground-truth/` —
  reversed-fix patches, provenance sidecars naming triggarr/seedsyncarr/roonseek, BUGGY.py,
  18 captured run states) goes public intact with the push. NO history rewrite, NO scrub, NO
  relocation — the pre-registration evidence chain (ANSWER_KEY_COMMIT ancestry through every
  runs/ commit) MUST survive publish byte-identical; rewriting history would destroy the proof
  behind the measured numbers. All underlying bugs are already fixed in the source repos.
  (Owner explicitly chose plain publish-as-is over the publish-plus-privacy-backlog variant.)

### Release notes
- **D-02:** Add a SMALL honest README pointer (3–6 lines): v2.9 ships the first measured
  catch-rate / false-positive-rate — exact fractions (catch 8/9, FP 6/9), the small-N caveat,
  and a link to `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md`. Honesty-first framing; no
  marketing language; do NOT create a CHANGELOG file (no such convention in this repo).

### Worktree hygiene
- **D-03:** The ~38 stale deleted-but-uncommitted `.planning` files (shipped-milestone residue,
  phases 14–33) stay UNTOUCHED this phase — no housekeeping commit; they cannot affect the
  publish (uncommitted changes never merge). GSD's own cleanup owns them later.

### Carried-forward publish ritual (standing, not re-decided)
- **D-04:** Publish per the standing directive: merge/ff `main`, push main + tag + branch;
  annotated tag `v2.9`; after push, EXACT-HASH verify local == remote for main, the tag, and
  the branch (the v2.7 gate that caught a real partial-publish).
- **D-05:** Pre-publish gates: `pytest -q` green in `plugins/vibe-check/scripts` (baseline
  356 passed + 221 subtests); after the bump, installed-cache vs repo `plugin.json` parity
  noted (a resync needs a process relaunch — flag it, don't silently skip); version bump is
  exactly 2.8.0 → 2.9.0.
- **D-06:** The milestone audit (CLOSE-01 criterion 3) runs via `/gsd:audit-milestone` and must
  be clean before `complete-milestone`; the wrapper orchestrator drives audit + archive at
  milestone-end — this phase's execution delivers bump + README pointer + tag + publish.

### Claude's Discretion
- Exact README wording and placement of the pointer (keep it in the efficacy/README claims
  neighborhood if one exists; otherwise a short "Measured efficacy" note near the top).
- Whether bump and README pointer land as one commit or two (atomic-per-concern preferred).
- Tag message content — mirror the v2.8 annotated-tag style.

</decisions>

<specifics>
## Specific Ideas

- Owner is a PM; the README pointer must read as honest measurement, not marketing: exact
  fractions ("8/9", "6/9"), the small-N caveat stated plainly, link to the full report.
- The publish is the FIRST push of `feat/v2.9` (55 commits, local-only until now) — the
  moment of publication for everything the milestone committed.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & ritual
- `.planning/ROADMAP.md` §Phase 37 — goal + CLOSE-01 success criteria (versioned / tagged+published / audited)
- `.planning/REQUIREMENTS.md` §Close — CLOSE-01 exact wording
- `plugins/vibe-check/.claude-plugin/plugin.json` — the version field to bump (currently 2.8.0)

### What the README pointer cites
- `plugins/vibe-check/docs/efficacy/RESULTS-v2.9.md` — the B3 section (headline fractions, limitations, D-11 verdict)

### Must-survive-publish invariants
- `docs/design/b3-ground-truth/PREREGISTRATION.md` — the evidence-chain manifest; publish must never rewrite the history it pins (D-01)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The v2.8 close ritual is the template: bump commit → real merge to main (`f19be14` precedent) →
  annotated tag → push main+tag+branch → hash-verify. v2.7's exact-hash publish gate is the
  verification pattern.

### Established Patterns
- One results doc per milestone (RESULTS-v2.9.md already carries P35 proofs + the B3 report —
  nothing new is written there this phase).
- `.planning` is gitignored with force-tracked exceptions; any new phase artifacts need
  `git add -f`.

### Integration Points
- The Claude Code marketplace pins `ref:main` — pushing main IS the release. The installed
  cache updates on the user's next plugin update + process relaunch (chronic staleness gotcha).

</code_context>

<deferred>
## Deferred Ideas

- **Future ground-truth kits' privacy location** — considered at the publish decision; owner
  chose plain publish-as-is and declined a standing backlog item. Revisit only if a future kit
  sources from repos the owner wants kept private.
- Post-v2.9 items already on record in STATE.md: security.md critique pass, B3-gated scorer
  design challenges (D-11 says PROCEED on H-CORE/H-LANE/B-SEV/B-REWEIGHT at next-milestone
  scoping), CATEGORY_DOMAIN twin proposals, config.py symlink-follow hardening (CWE-61).

</deferred>

---

*Phase: 37-close*
*Context gathered: 2026-07-05*
