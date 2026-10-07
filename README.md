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

## 📊 Measured Efficacy

**v2.11 (this release).** 2.11 was re-measured on the same 12 sealed organic diffs × 3 (36 assistant-driven `/deep-review` runs on build `e6eafbd`) against the unchanged pre-registered bar: **false alarms ≤ 3/18 and catches 15/15**. **Result: false alarms 5/18 (sealed literal 8/21, never deciding), catches 15/15 — a MISS.** Every real defect was still caught; the miss is on the false-alarm side: one known weak spot (a setting that is declared but not read yet, flagged 3/3, predicted before any run) plus two one-off alarms on two other diffs. The one allowed retune was diagnosed but not applied. The owner chose to ship despite the miss; the reason is recorded in RESULTS-v2.11, which quotes the committed decision line (`ship-decision: ship-as-measured (owner, 2026-10-07T12:41:11-0400, verdict of record MISS 5/18 15/15)`). Decision cards on the declined fix-loop path stayed at 2.00 per fix-loop firing, the same as v2.10. Same small-N and three-own-repos caveats as v2.10. Full method: [`docs/efficacy/RESULTS-v2.11.md`](plugins/vibe-check/docs/efficacy/RESULTS-v2.11.md).

**Release not B3-measured.** The B3 result above was measured on build `e6eafbd`. 2.11.0 also contains `11c8afc` (the fix agent's commit helper no longer lets an error while silencing its output, such as a missing stdout, turn an already-published commit into a `refused` exit), made after that measurement and not re-measured, so the release itself is not B3-measured. The owner chose to ship it under a recorded release waiver.

**v2.10 (previous release).** v2.10's numbers come from 45 `/deep-review` runs on the changed plugin: 36 first-pass runs (12 sealed organic diffs × 3) plus 9 retune re-runs (the 3 failed diffs × 3). The runs were assistant-driven via tmux, not owner-typed — one fresh `claude` session per run, a fixed keystroke set, no findings fed back (RESULTS limitation 11 / 43-CONTEXT D-13). They were scored against a pre-registered bar of **≤ 8/18** quiet runs firing **and 15/15** catches. **Untuned first pass: false alarms 6/18 (sealed literal 9/21), catches 13/15 — a MISS** on that bar (the false-alarm arm cleared it, the catch arm did not). Exact fractions, no rounding; the 18-run figure is the corrected cohort (one quiet diff excluded because it contains a real defect), the 21-run literal is printed beside it.

After the one retune the pre-registration allowed (prompts only, re-run on the 3 failed diffs) the **combined result is 3/18 (6/21) · 15/15 — a PASS**, but a weaker one than it sounds. The retune was written after seeing those exact diffs fail and was scored only on them; the other nine diffs were not re-run. The catch arm is self-scored and basis-sensitive: under a stricter reading of one diff's titles the combined arm is 14/15 (a MISS) and the untuned arm 12/15. Phases 40–42 were also designed while looking at this same set of diffs, so neither pass is a held-out test. The untuned first pass is the cleaner estimate of how the tool does on diffs it was not tuned against.

What was measured: a Fable 5.1 session with a 1M-token context window, with the Codex adversarial pass joined on all 45 runs. The default Opus top tier, a 200k context window, and setups without Codex installed were not measured. Small-N (one run moves a diff by 1/3; the catch arm has zero headroom), three repos all the owner's, organic-only — indicative, not a general accuracy claim. Full method, per-diff scoring, and honest limitations: [`docs/efficacy/RESULTS-v2.10.md`](plugins/vibe-check/docs/efficacy/RESULTS-v2.10.md), section "B3 v2.10 — Phase 43 post-change measurement".

**Disclosed post-measurement change (v2.10).** After the v2.10 measurement, commit `214c7df` changed when the Codex wait starts: it is now timed from the moment the Codex launch actually starts, not from the kickoff step a few seconds earlier. This can only turn a would-be timeout into a join, and Codex joined all 45 measured runs, so the v2.10 numbers are unaffected. The plugin that shipped as 2.10.0 differs from the measured snapshots in this one respect.

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
# Quick review — fast, pre-commit check (Sonnet 5 agents, Haiku 4.5 triage)
/vibe-check:review

# Deep review — thorough pre-PR analysis (adds architecture, impact, test-sufficiency, and a Codex adversarial pass when installed)
/vibe-check:deep-review
```

### Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and configured
- A git repository with changes to review

---

## ⚙️ Configuration

The plugin works out of the box with no configuration. One optional knob controls the **top model tier** used by the two judgment-gating agents (`bugs` and `architecture`) during `/deep-review`. The default is Opus (the `opus` alias — Opus 5 as of the 2026-09-08 price check); Fable 5.1 is opt-in:

| Env var | Default | Values | Effect |
|---|---|---|---|
| `VIBE_CHECK_TOP_MODEL` | `opus` | `opus`, `fable` | Model used for the `bugs` + `architecture` agents in `/deep-review`. Only `opus` and `fable` are accepted; anything else falls back to `opus` with a one-line warning. |

- **Default (`opus`)** — Opus 5 (as of 2026-09-08); works on every paid Claude tier with no delay. Leave it unset and you're fine.
- **`fable`** — opt up to Fable 5.1 *only if your subscription includes Fable*. Set it in your shell or Claude Code env:

  ```bash
  export VIBE_CHECK_TOP_MODEL=fable
  ```

`/review` never uses the top tier: every reviewer agent runs on Sonnet 5 with Haiku 4.5 triage, regardless of this setting — it's tuned for cheap iteration. On very large diffs (>2000 changed lines) the language and framework agents are downgraded to Haiku 4.5 in both commands; the core agents keep their model.

**What runs where.** `/review`: Sonnet 5 for every reviewer agent, Haiku 4.5 for triage. `/deep-review`: the top tier (Opus 5 by default, Fable 5.1 opt-in) for `bugs` + `architecture`; `impact` and `test-sufficiency` always on Opus; Sonnet 5 for `security`, `compliance` and the language/framework agents; Haiku 4.5 triage; plus the Codex (GPT-5-codex) adversarial pass when Codex is installed. The interactive fix agent runs on Opus.

**Rough cost (estimates, not measurements).** A typical `/deep-review` pass is ~$2–5 on the default Opus 5 top tier, toward the high end or above with `VIBE_CHECK_TOP_MODEL=fable` (Fable 5.1 costs 2× Opus 5 per token, partly offset by cheaper cache reads). `/review` runs on Sonnet 5 with Haiku 4.5 triage at roughly ~$0.25–$0.60 a pass. `--all` prints its own estimate and asks before dispatching. Actual cost depends on diff size and cache hits.

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
codex = "auto"           # gate the /deep-review Codex adversarial pass (default: "auto")
                         #   off | auto | on   (overridable per run with --codex)
# min_confidence = 30    # optional: drop NEW findings whose agent confidence is below this (int 0–49; unset = no filter)
                         #   values ≥ 50 are refused (they would also hide real criticals); per run: --min-confidence N
                         #   unresolved findings carried from an earlier pass are kept open, never dropped
```

| Key | Default | Values | Effect |
|---|---|---|---|
| `[review].thresholds` | `{ critical = 95, warning = 80, medium = 70 }` | three score floors, strictly descending, `medium ≥ 70` | The **band labels** a finding's score maps to (Critical / Warning / Medium). Absent ⇒ the built-in 95 / 80 / 70. |
| `[agents].disabled` | `[]` | list of agent names | Agents to skip dispatching. Disabling a **core** agent (`bugs`/`security`) is honored but **announced** on the config-health line (coverage reduced, never silent). |
| `[agents].top_model` | `opus` | `opus`, `fable` | Top-tier model for the two judgment-gating agents (`bugs` + `architecture`) in `/deep-review` — the toml equivalent of `VIBE_CHECK_TOP_MODEL`. |
| `[noise].idiom_floor` | `"medium"` | a band name (`critical` / `warning` / `medium` / `low`) or `off` / `none` to disable | Caps the **`idiom`** category's band at this max, so idioms never block finalize — **active by default at `medium`** (this is the one knob whose default is an active cap). `off` / `none` disables the cap (idioms may then reach any band). `"low"` caps idioms at the `low` band — a **supported** value, NOT a disable: a low-capped idiom still renders, in the report's **Low / Informational** listing. Applies ONLY to `category == "idiom"` and only ever LOWERS a band (never raises one). |
| `[noise].codex` | `"auto"` | `off`, `auto`, `on` (also settable per run via `--codex off\|auto\|on`) | Gates the **Codex (GPT-5-codex) adversarial pass** in `/deep-review`. `off` never attempts Codex (short-circuits all Codex plumbing). `auto` (default) runs it when Codex is installed, authenticated, and the diff is representable — behavior unchanged from prior versions. `on` uses the same dispatch decision as `auto` but surfaces any skip reason prominently. `/review` never runs Codex, so this knob only affects `/deep-review`, which prints one Codex outcome line per run (joined / skipped: reason / off via config). Orchestrator-only — never enters the score envelope. |
| `[noise].min_confidence` | unset (no filter) | int `0`–`49` (also per run via `--min-confidence N`) | Drops findings whose agent confidence is below N **before** scoring; dropped findings stay visible in the Filtered section (reason "below min_confidence"). Values ≥ 50 are refused — they would silently hide real criticals — and fall back to no filter with a config-health note. From 2.11 this applies to new findings only: a finding raised on an earlier pass that is still unresolved is never dropped by `min_confidence` or a raised threshold. It stays listed as a kept-open row and still blocks finalize until it is verified fixed or you decide on it. |

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
| **Top-tier agents** | — | `bugs` + `architecture` (Opus 5 default, Fable 5.1 opt-in); `impact` + `test-sufficiency` (Opus, always on) |
| **Models** | Sonnet 5 agents, Haiku 4.5 triage | Top tier above; Sonnet 5 for the rest; Haiku 4.5 triage; Codex adversarial pass when installed |
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

**⚛️ Frameworks (8 agents)**
- React / React Native: hook rules, key prop, stale closures, list virtualization
- Vue, Angular, Express, Electron (security-weighted IPC/preload checks)
- FastAPI: DI misuse, async/blocking discipline, Pydantic gaps, `response_model` exposure
- Claude Agent Skills: SKILL.md quality and plugin wiring

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
├── commands/               # Entry points (/review, /deep-review)
│   ├── review.md
│   └── deep-review.md
├── phases/                 # Orchestration steps shared by both commands (review/, deep-review/, shared/)
├── agents/                 # Specialized parallel reviewers
│   ├── triage.md           # Haiku 4.5 — fast diff classification
│   ├── bugs.md             # Sonnet 5; top tier in /deep-review
│   ├── security.md
│   ├── compliance.md
│   ├── architecture.md     # deep only — top tier
│   ├── impact.md           # deep only — Opus
│   ├── test-sufficiency.md # deep only — Opus
│   ├── codex-adversarial.md # deep only — contract for the Codex (GPT-5-codex) pass
│   ├── fix.md              # applies accepted fixes (Opus)
│   └── language-*.md / framework-*.md
├── scripts/                # stdlib-Python scoring, config, guard and state helpers (pytest-covered)
└── templates/              # Output schema, scoring, false-positive rules
```

The plugin reads from `.planning/` (GSD intent docs) and the repo, but **only writes to `.turingmind/`** — it never touches the `.planning/` namespace. `.turingmind/` is gitignored by default; copy `REVIEW.md` somewhere persistent if you want it tracked.

### Extending

Add a language: copy an existing `agents/language-*.md` and adjust its checklist. Tune detection by editing the relevant agent prompt; tune noise via `templates/false-positive-rules.md`.

---

## ⚠️ Limitations

This is **AI-assisted** code review. It's powerful, but:

- 🔧 **Complements, doesn't replace** SAST tools (Semgrep, CodeQL, Snyk)
- 🔗 Can't trace every complex multi-file data flow
- 🧪 Doesn't run your test suite or type checker as a gate (review agents can run shell commands while investigating — see the next item)
- ✅ **Fixed in 2.11 (known issue in 2.10):** a review agent (`compliance`) was once observed running `git stash pop` in the repo under review. From 2.11, review agents cannot change your repo's git state. A guard refuses any command from a review agent that it cannot prove read-only, across shell, sub-agent, file-edit, notebook and worktree tools. Each review also fingerprints your repo's git state (HEAD, staged changes, stashes, branches/tags, reflog, merge/rebase state) before and after the agents run, and halts the pass without saving anything if it changed. The only agent that commits is the fix agent, and it acts only on fixes you accept. Residual: web-fetch (WebFetch) and MCP-server tools are outside the guard (tracked for a future release). If you also edit the repo in another window during a review, the pass halts, because the fingerprint cannot tell who changed it.
- ⚠️ **Known tradeoff (v2.10):** the retune's second rule treats a security bypass that lives inside an unchanged helper your change only calls as a pre-existing gap. It is counted in the report's Filtered summary but not listed as a finding. If you are changing auth or validation call sites, read the Filtered section.

For security-critical code, layer this with dedicated security scanners.

---

## 📄 License

MIT — adapted from [`turingmindai/turingmind-code-review`](https://github.com/turingmindai/turingmind-code-review) (also MIT). See [LICENSE](LICENSE).

---

<div align="center">

**[⬆ Back to top](#-vibe-check)**

</div>
