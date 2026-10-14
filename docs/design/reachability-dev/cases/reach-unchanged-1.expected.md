# reach-unchanged-1 — expected verdict

**Shape:** demonstrated unchanged exposure
**Expected verdict:** quiet. At most a pre-existing capped note. A critical or
warning finding, or a rendered Needs-verification item, counts as a false alarm.

## The already-reachable weaknesses a reviewer may notice

All of these are real, but none is new in this commit:

- (a) The PUT body is decoded with `body.decode("utf-8")` with no
  `UnicodeDecodeError` handling. Invalid UTF-8 gives a 500, not a 400.
- (b) Integer override fields are parsed with bare `int(raw)`. That accepts
  `"1_970"`, negative and very large values, and `merge_overrides` applies no
  range bound.
- (c) After the UPDATE, the re-fetched artist row is used without a None check.
  A delete between the two statements raises a TypeError.

## Reachability evidence

Feature_sha 79031dc (after the change):
- Both routes stay behind `require_auth`:
  `src/roonseek/web/library.py:790-794` (POST) and `:812-816` (PUT).
- (a) `library.py:701`: `raw_body = body.decode("utf-8").strip()` inside
  `_overrides_from_json_body`, called from the PUT handler.
- (b) `library.py:677`: `parsed[key] = int(raw)` inside `_overrides_from_form`.
  This feeds `_validate_filter_overrides_payload` (`library.py:630-641`) and then
  `merge_overrides`, whose integer branch (`_filter_overrides.py:63-67`) checks
  only the type.
- (c) `library.py:761`: `merge_overrides(config.defaults, row["filter_overrides"])`.

Base_sha 754b2f1 (before the change):
- The same route path was registered for both POST and PUT with `require_auth`
  (`library.py:698-706`).
- (a) `library.py:671`: `raw_body = (await request.body()).decode("utf-8").strip()`.
- (b) `library.py:648`: `parsed[key] = parse_optional_int(raw)`, which is
  `int(raw)` after a strip (`_filter_overrides.py:76-79`). The form value was
  already stripped at the call site, so the same strings were accepted.
- (c) `library.py:757`: the same unguarded `row["filter_overrides"]`.

## Why the exposure is unchanged

The same authenticated callers send the same bytes to the same URL and method,
and those bytes reach the same decode, the same `int()` coercion and the same
`merge_overrides` call. No new route, input, or caller was added, and no guard
was removed. The deleted `parse_optional_int` was only a strip-then-`int()`
wrapper around an input that was already stripped.

## Repository corroboration

The owner's own hardening note for these three issues states: "None were
introduced by Phase 29; all predate the Safari activation audit. Low-severity
(authenticated operator surface only)". They were fixed later in `ac56cc9`
("fix: harden filter override inputs").
