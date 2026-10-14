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

## Before/after comparison (the basis of the quiet verdict)

The commit touches `src/roonseek/web/library.py` and
`src/roonseek/web/_filter_overrides.py` (removes `parse_optional_int`). It splits
one handler registered for POST and PUT into two handlers. `merge_overrides`
(`_filter_overrides.py:63-68`) is the same code at both commits.

### Routes and callers

| | base_sha 754b2f1 | feature_sha 79031dc |
|---|---|---|
| POST `/api/artists/{artist_id}/filter-overrides` | `library.py:698-700`, `require_auth` | `library.py:790-794`, `require_auth` |
| PUT `/api/artists/{artist_id}/filter-overrides` | `library.py:702-706`, `require_auth` (same handler) | `library.py:812-816`, `require_auth` |
| Body dispatch | `library.py:634`: POST → form; otherwise → raw body (`:723` calls the shared parser) | POST → `_overrides_from_form` (`:806`); PUT → `_overrides_from_json_body` (`:831`) |

Same URL, same methods, same auth dependency, same caller set; POST still reads
the form and PUT still reads the raw body.

### Inputs and checks per weakness

| Weakness | base_sha 754b2f1 | feature_sha 79031dc | Same input, same check? |
|---|---|---|---|
| (a) body decode | `library.py:671`: `(await request.body()).decode("utf-8").strip()`; no `UnicodeDecodeError` handler | `library.py:701`: `body.decode("utf-8").strip()` (body read at `:831`); no `UnicodeDecodeError` handler | yes: the same PUT bytes reach the same unguarded decode |
| (b) integer coercion | `library.py:645-648`: `raw = str(form.get(key, "")).strip()`, then `parse_optional_int(raw)` = strip + `int()` (`_filter_overrides.py:76-79`); `ValueError` → 400 at `:649` | `library.py:673-677`: same stripped `raw`, then `int(raw)`; `ValueError` → 400 at `:678` | yes: the input is already stripped, so the removed second strip changes nothing; the same strings are accepted and rejected |
| (b) range bound | `merge_overrides` integer branch, type check only (`_filter_overrides.py:63-67`), called at `library.py:662` | same branch, called via `_validate_filter_overrides_payload` (`library.py:630-641`) | yes: no bound before, no bound after |
| (c) re-fetched row | `library.py:756-757`: `fetchone()`, then `row["filter_overrides"]` with no None check | `library.py:760-761`: `fetchone()`, then `row["filter_overrides"]` with no None check | yes |

## Why the exposure is unchanged

The same authenticated callers send the same bytes to the same URL and method,
and those bytes reach the same decode, the same `int()` coercion and the same
`merge_overrides` call (tables above). No new route, input, or caller was added,
and no guard was removed. The deleted `parse_optional_int` was only a
strip-then-`int()` wrapper around an input that was already stripped.

## Supporting context (not proof)

The owner's own hardening note for these three issues states: "None were
introduced by Phase 29; all predate the Safari activation audit. Low-severity
(authenticated operator surface only)". They were fixed later in `ac56cc9`
("fix: harden filter override inputs"). This history agrees with the verdict but
does not establish it; the before/after comparison above does.
