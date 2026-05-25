---
name: language-go
description: Go-specific review — error handling, goroutine safety, defer/cleanup, common Go pitfalls. Returns JSON findings.
model: sonnet
---

## Checks

### Error handling
- Unchecked error returns
- Errors wrapped without context (use `fmt.Errorf("...: %w", err)`)
- Panic in library code that should return errors

### Concurrency
- Data races on shared state without sync.Mutex/RWMutex/atomic
- Goroutines without bounded lifetime (no context, no done channel)
- Channel sends without select+default
- Closure capture of loop variables in goroutines

### Resource management
- Missing `defer file.Close()` after os.Open
- Missing `defer rows.Close()` after sql.Query
- HTTP response bodies not closed

### Idioms
- Pointer vs value receiver inconsistency
- `interface{}` / `any` where specific type fits
- Naming: exported should be CamelCase

## Output

Return ONE JSON per `templates/agent-output-schema.md`. Use `category` values: `error-handling`, `concurrency`, `resource-leak`, `idiom`.

No findings → `{"agent":"language-go","findings":[],"agent_notes":[]}`. JSON only.
