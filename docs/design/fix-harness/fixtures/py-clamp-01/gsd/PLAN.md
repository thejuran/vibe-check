---
phase: 52-harness-case
plan: 01
type: execute
---

# Plan: clamp helper

<objective>
Add `clamp(value, lo, hi)` that bounds a number to the closed range [lo, hi],
plus small range-description helpers.
</objective>

<tasks>
- Implement `clamp`, `width` and `describe_range` in `src/clamp.py`.
- Cover them with unit tests in `tests/test_clamp.py`.
</tasks>
