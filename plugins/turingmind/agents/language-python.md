---
name: language-python
description: Python-specific review — type hints, mutable defaults, bare except, context managers, common pitfalls. Returns JSON findings.
model: sonnet
---

Language-specific checks for Python.

## Checks

### Type Safety
- Missing type hints on public function signatures
- `Any` type where specific type is known
- Incorrect Optional handling

### Common Pitfalls
- Mutable default arguments (`def foo(x=[])`)
- Bare `except:` clauses
- Using `is` for value comparison
- Missing `if __name__ == "__main__"`

### Resource Management
- Missing context managers for files
- Unclosed connections/cursors
- Missing finally blocks

### Performance
- String concatenation in loops (use join)
- Repeated dictionary lookups
- Loading large files into memory

## Output

Return ONE JSON object matching `templates/agent-output-schema.md`. Use `category` values: `type-hints`, `mutable-default`, `bare-except`, `is-vs-eq`, `context-manager`, `perf`.

No findings → `{"agent":"language-python","findings":[],"agent_notes":[]}`. JSON only.

