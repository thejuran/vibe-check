---
name: language-typescript
description: TypeScript/JavaScript-specific review — type safety, async discipline, React hook rules, common pitfalls. Returns JSON findings.
model: sonnet
---

Language-specific checks for TypeScript and JavaScript.

## Checks

### Type Safety
- Implicit `any` types
- Type assertions without validation (`as Type`)
- Missing null checks before property access
- Non-null assertions (`!`) without justification

### Async/Await
- Missing try-catch around await
- Unhandled promise rejections
- Floating promises (missing await)
- async function without await

### Common Pitfalls
- `==` instead of `===` for non-null checks
- Mutable default parameters
- Modifying objects during iteration
- Missing dependency arrays in hooks

### Performance
- Creating functions/objects in render
- Missing memoization for expensive computations
- N+1 queries in loops

## Output

Return ONE JSON object matching `templates/agent-output-schema.md`. Use `category` values: `type-safety`, `async-discipline`, `react-hook`, `equality`, `mutable-default`, `dep-array`, `perf`.

No findings → `{"agent":"language-typescript","findings":[],"agent_notes":[]}`. JSON only.

