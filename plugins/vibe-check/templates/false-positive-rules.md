---
name: False Positive Filtering Rules
---

## False Positive Filtering

Use these rules to filter out issues that should not be reported.

### Always Filter Out

1. **Pre-existing Issues**
   - Issue exists in lines not modified by this diff
   - Use `git blame` to verify if uncertain

2. **Linter/Compiler Territory**
   - Syntax errors
   - Type mismatches (TypeScript will catch)
   - Unused variables
   - Import ordering

3. **Pedantic Nitpicks**
   - Would a senior engineer call this out in code review?
   - Is this actionable, or just "could be better"?

4. **Silenced Issues**
   - `// eslint-disable-next-line`
   - `# noqa`
   - `// nolint`
   - `#[allow(...)]`
   - `@SuppressWarnings`

5. **Intentional Changes**
   - Functionality changes that appear deliberate
   - Style changes matching existing codebase patterns

6. **Style Not in CLAUDE.md**
   - General style preferences not explicitly required
   - Formatting issues (prettier/black will handle)

### Scoring and banding

This file owns only the qualitative filtering above. All scoring — point weights, severity
weights, score-derived bands (Critical / Warning / Medium / Filtered), and per-command
thresholds — is defined in one place: [`scoring.md`](./scoring.md). Consult `scoring.md` as
the single source for any banding or scoring question; do not score or band findings from
this file.

