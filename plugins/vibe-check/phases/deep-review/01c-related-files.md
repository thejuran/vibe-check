# Phase 1c — Related files (for impact agent)

> **Lazy-loaded.** Read from `commands/deep-review.md` when Phase 1c is entered (every deep review, after Phase 1.5 and before Phase 2, in its own turn).
> Announce on entry, after this Read: `✓ Phase 1c — Related files`.

After Phase 1.5, before Phase 2, for impact agent only:

For each diff file:
- `git grep -l "from.*<basename>"` → importers
- Parse diff's import statements → importees
- Find test files: `<basename>.test.*`, `test_<basename>.*`, `__tests__/<basename>.*`

Assemble `<related-files>`:

```
<related-files>
  <file path="src/users.ts">
    <imported-by>src/api/handlers.ts, src/admin/routes.ts</imported-by>
    <imports>src/db/client.ts, src/lib/email.ts</imports>
    <test-file>src/users.test.ts</test-file>
  </file>
</related-files>
```

Inject into impact agent's prompt only.
