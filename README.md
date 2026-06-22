<div align="center">

# 🧠 vibe-check

**Catch bugs before they catch you.**

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin for AI-powered code review of your uncommitted changes. Install from the marketplace, review instantly.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)

[Quick Start](#-quick-start) • [Configuration](#%EF%B8%8F-configuration) • [Features](#-features) • [Examples](#-example-output)

</div>

---

## 📦 What is This?

A **Claude Code plugin** that adds two code-review slash commands — a fast pre-commit pass and a deep pre-PR pass. It runs specialized per-domain reviewer agents in parallel, scores and filters their findings, and shows you only what's worth your attention *in your diff* — not pre-existing tech debt.

It is GSD-aware: if your project uses [GSD](https://github.com/open-gsd/gsd-core) phase planning, it reads the phase's intent docs (`PLAN.md` / `SPEC.md` / `RESEARCH.md`) to judge implementation-vs-intent. If you don't use GSD, it falls back to plain git-diff review with zero setup.

> Adapted from the upstream [`turingmindai/turingmind-code-review`](https://github.com/turingmindai/turingmind-code-review) project, with real parallel agent dispatch, model tiering, intent-doc awareness, and a stateful multi-pass review loop.

---

## 🚀 Quick Start

Open Claude Code and run:

```bash
# Step 1: Add the marketplace
/plugin marketplace add thejuran/marketplace
```

```bash
# Step 2: Install the plugin
/plugin install vibe-check@thejuran
```

Then use the commands:

```bash
# Quick review — fast, pre-commit check (Sonnet agents)
/vibe-check:review

# Deep review — thorough pre-PR analysis (adds architecture + impact)
/vibe-check:deep-review
```

### Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and configured
- A git repository with changes to review

---

## ⚙️ Configuration

The plugin works out of the box with no configuration. One optional knob controls the **top model tier** used by the two judgment-gating agents (`bugs` and `architecture`) during `/deep-review`:

| Env var | Default | Values | Effect |
|---|---|---|---|
| `VIBE_CHECK_TOP_MODEL` | `opus` | `opus`, `fable` | Model used for the `bugs` + `architecture` agents in `/deep-review`. |

- **Default (`opus`)** — works on every paid Claude tier with no delay. Leave it unset and you're fine.
- **`fable`** — opt up to the strongest tier *only if your subscription includes Fable*. Set it in your shell or Claude Code env:

  ```bash
  export VIBE_CHECK_TOP_MODEL=fable
  ```

`/review` always uses Sonnet (and downgrades language agents to Haiku on very large diffs) regardless of this setting — it's tuned for cheap iteration.

---

## ✨ Features

### Two Review Modes

| | Quick Review | Deep Review |
|---|---|---|
| **Command** | `/vibe-check:review` | `/vibe-check:deep-review` |
| **Speed** | ⚡ Fast | 🔍 Thorough |
| **Best for** | Pre-commit checks | Before PRs |
| **Top-tier agents** | — | `bugs` + `architecture` (Opus/Fable), `impact` (Opus) |
| **Architecture analysis** | — | ✅ |
| **Impact / blast-radius analysis** | — | ✅ |
| **Intent-doc alignment (GSD)** | — | ✅ |

### What Gets Checked

<table>
<tr>
<td width="50%">

**🐛 Bugs & Logic**
- Null/undefined access
- Off-by-one errors
- Race conditions
- Resource leaks

</td>
<td width="50%">

**🔐 Security (OWASP Top 10)**
- SQL/Command injection
- XSS vulnerabilities
- Hardcoded secrets
- Auth bypass

</td>
</tr>
<tr>
<td>

**📐 Architecture** *(deep only)*
- Pattern consistency
- Abstraction violations
- Circular dependencies

</td>
<td>

**🎯 Project Rules**
- CLAUDE.md / AGENTS.md compliance
- Team conventions

</td>
</tr>
<tr>
<td>

**⚛️ Frameworks (React + FastAPI)**
- React: hook rules, key prop, stale closures
- FastAPI: DI misuse, async/blocking discipline
- FastAPI: Pydantic/validation gaps
- FastAPI: `response_model` data exposure, auth gaps

</td>
<td width="50%"></td>
</tr>
</table>

### Smart Filtering

Findings are confidence-scored and filtered so you don't drown in noise:
- ❌ Pre-existing issues (not introduced by your diff)
- ❌ Linter territory (let ESLint handle it)
- ❌ Pedantic nitpicks
- ❌ Intentional changes near `// review-silenced`-style markers

Filtered findings stay visible in a transparency section — nothing is dropped silently.

---

## 📸 Example Output

### Quick Review

```
## Code Review

**Summary:** Reviewed 3 files, 47 lines changed

### Critical (95-100) 🔴
Must fix before committing:

1. **api/auth.ts:23** - SQL injection vulnerability

   User input directly interpolated into SQL query.

   ```diff
   - const query = `SELECT * FROM users WHERE email = '${email}'`;
   + const query = `SELECT * FROM users WHERE email = $1`;
   + const result = await db.query(query, [email]);
   ```

### Warning (80-94) 🟠
Should fix:

1. **utils/parse.ts:15** - Unchecked null access

   `data.user.name` accessed without null check. Will throw if user is undefined.

   Suggested fix: `data.user?.name ?? 'Unknown'`
```

### Deep Review

Includes everything above, plus:

```
### Architectural Notes 📐
- Pattern consistency: ✅ Follows existing patterns
- Test coverage: ⚠️ No tests for new `validateEmail` function

### Impact Analysis 💥
- **Affected files:** `routes/login.ts`, `middleware/auth.ts`
- **Blast radius:** Auth flow — high business impact
- **Breaking changes:** None detected
```

The deep review then runs an **interactive fix loop**: accept a finding and a dedicated fix agent applies the change semantically and commits it atomically.

---

## 🏗️ Architecture

```text
plugins/vibe-check/
├── commands/           # Review orchestration (/review, /deep-review)
│   ├── review.md
│   └── deep-review.md
├── agents/             # Specialized parallel reviewers
│   ├── triage.md       # Haiku — fast diff classification
│   ├── bugs.md
│   ├── security.md
│   ├── compliance.md
│   ├── architecture.md # deep only
│   ├── impact.md       # deep only
│   ├── fix.md          # applies accepted fixes
│   └── language-*.md / framework-*.md
└── templates/          # Output schema, scoring, false-positive rules
```

The plugin reads from `.planning/` (GSD intent docs) and the repo, but **only writes to `.turingmind/`** — it never touches the `.planning/` namespace. `.turingmind/` is gitignored by default; copy `REVIEW.md` somewhere persistent if you want it tracked.

### Extending

Add a language: copy an existing `agents/language-*.md` and adjust its checklist. Tune detection by editing the relevant agent prompt; tune noise via `templates/false-positive-rules.md`.

---

## ⚠️ Limitations

This is **AI-assisted** code review. It's powerful, but:

- 🔧 **Complements, doesn't replace** SAST tools (Semgrep, CodeQL, Snyk)
- 🔗 Can't trace every complex multi-file data flow
- 🧪 Doesn't run tests or type checking

For security-critical code, layer this with dedicated security scanners.

---

## 📄 License

MIT — adapted from [`turingmindai/turingmind-code-review`](https://github.com/turingmindai/turingmind-code-review) (also MIT). See [LICENSE](LICENSE).

---

<div align="center">

**[⬆ Back to top](#-vibe-check)**

</div>
