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

### `.vibe-check.toml` (repo-level config)

Drop a `.vibe-check.toml` at your repo root to tune reviews per project. **Every key is optional** — a repo with **no** `.vibe-check.toml` runs exactly as before, with no warning and no behavior change. Any invalid key falls back to its default and surfaces a one-line note on the report's **config-health line** (near the top of the review), so a misconfiguration is never silently applied and never breaks the review.

```toml
# .vibe-check.toml  (repo root — all keys optional)

[review]
thresholds = { critical = 95, warning = 80, medium = 70 }  # band-label cutoffs (defaults shown)

[agents]
disabled = []          # agent names to skip dispatching (default: none)
top_model = "opus"     # opus | fable  (default: opus)

[noise]
idiom_floor = "medium"   # cap the `idiom` category at this max band (default: "medium")
                         #   band name (critical|warning|medium|low) to cap, or off|none to disable
#   codex = "auto"       # (Phase 33 — not active yet)
```

| Key | Default | Values | Effect |
|---|---|---|---|
| `[review].thresholds` | `{ critical = 95, warning = 80, medium = 70 }` | three score floors, strictly descending, `medium ≥ 70` | The **band labels** a finding's score maps to (Critical / Warning / Medium). Absent ⇒ the built-in 95 / 80 / 70. |
| `[agents].disabled` | `[]` | list of agent names | Agents to skip dispatching. Disabling a **core** agent (`bugs`/`security`) is honored but **announced** on the config-health line (coverage reduced, never silent). |
| `[agents].top_model` | `opus` | `opus`, `fable` | Top-tier model for the two judgment-gating agents (`bugs` + `architecture`) in `/deep-review` — the toml equivalent of `VIBE_CHECK_TOP_MODEL`. |
| `[noise].idiom_floor` | `"medium"` | a band name (`critical` / `warning` / `medium` / `low`) or `off` / `none` to disable | Caps the **`idiom`** category's band at this max, so idioms never block finalize — **active by default at `medium`** (this is the one knob whose default is an active cap). `off` / `none` disables the cap (idioms may then reach any band). `"low"` caps idioms at the `low` band — a **supported** value, NOT a disable: a low-capped idiom still renders, in the report's **Low / Informational** listing. Applies ONLY to `category == "idiom"` and only ever LOWERS a band (never raises one). |

**Precedence (per knob):** `CLI flag` > `.vibe-check.toml` > built-in default. For `top_model` this reads concretely as **`VIBE_CHECK_TOP_MODEL` (env) > `top_model` (toml) > `opus`** — a shell override still wins over the repo config, coherent with the env-var table above.

**Two layers, don't conflate them.** `thresholds` tunes only the **band labels** — what counts as Critical vs Warning vs Medium. A *separate*, fixed layer decides which banded findings actually surface: `/review` shows findings scoring **≥ 80**, `/deep-review` shows **≥ 70**. This phase does not tune that per-command cutoff. So a band floor set below a command's cutoff (e.g. `critical = 72`) takes effect only under the command with the lower cutoff (`/deep-review`); under `/review` those findings are still banded but filtered out as sub-threshold. That's intended — the config is valid and accepted, not rejected.

#### The `// vibe-ignore` marker

To suppress a specific finding inline, add a **`// vibe-ignore: <reason>`** comment within ±2 lines of it. A `vibe-ignore` **with a reason** suppresses the nearby finding — it joins the existing silenced markers (`eslint-disable`, `# noqa`, `// nolint`, `@SuppressWarnings`, `#[allow(`) and rides the same suppression path.

**The reason is required** — that is what distinguishes `vibe-ignore` from the other markers. A **bare** `// vibe-ignore` (no reason after the colon, or no colon at all) does **NOT** suppress anything; instead it is itself surfaced as a low **suppression-without-reason** finding in the report's **Suppression (audit)** section, so every suppression stays auditable. Write `// vibe-ignore: false positive — validated upstream`, not a bare `// vibe-ignore`.

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
