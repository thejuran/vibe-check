---
name: language-rust
description: Rust-specific review — unsafe usage, error handling, lifetime correctness, common Rust pitfalls. Returns JSON findings.
model: sonnet
---

## Checks

### Safety
- `unsafe` blocks without `// SAFETY:` comment
- `unwrap()` / `expect()` in non-test paths
- `.clone()` cascades where references suffice

### Error handling
- `?` missing where errors should propagate
- Custom errors without `From` impls for upstream errors
- Errors returned as `String` or `Box<dyn Error>` instead of typed enums

### Concurrency
- `Arc<Mutex<T>>` where `RwLock` would allow more parallelism
- Holding locks across `await` points
- `Rc<T>` in async code (should be `Arc<T>`)

### Idioms
- Loop+match where iterator combinators read clearer
- `String` parameters where `&str` works
- Returning `Vec<T>` where `impl Iterator` works

## Output

Return ONE JSON per `templates/agent-output-schema.md`. Use `category` values: `unsafe-usage`, `error-handling`, `concurrency`, `idiom`.

No findings → `{"agent":"language-rust","findings":[],"agent_notes":[]}`. JSON only.
