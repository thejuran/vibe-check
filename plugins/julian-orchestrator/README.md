# julian-orchestrator

Personal Claude Code plugin that sequences existing skills (superpowers:brainstorming, /gsd:*, /codex:adversarial-review, /turingmind-code-review:deep-review, walkthrough) into a single milestone-level command: `/milestone:run`.

## Install

This is a personal, unpublished plugin. Install locally by adding it to your Claude Code plugins config.

```bash
# Adjust the exact mechanism to match how your other local plugins are wired.
# Symlinking or referencing this directory from ~/.claude/plugins/installed_plugins.json
# is one common approach.
```

## Usage

**Cold start (no `.planning/ROADMAP.md`):**
```
/milestone:run "build a thumbnail cache for the photo app"
```
Brainstorms, seeds a new GSD milestone, then drives every phase.

**Warm start (`.planning/ROADMAP.md` exists):**
```
/milestone:run
```
Skips brainstorming and drives remaining phases.

## Configuration

Optional `.orchestrator.json` at the repo root:

```json
{
  "review_tier": "deep",
  "adversarial_max_rewrites": 2,
  "skip_walkthrough": false,
  "deploy_prep_extras": []
}
```

See `commands/milestone.md` for the full key reference.

## Design

See the design spec at `~/turingmind-code-review/docs/superpowers/specs/2026-05-25-milestone-orchestrator-design.md` (the repo where this orchestrator was conceived).
