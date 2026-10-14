# reach-unchanged-2 — expected verdict

**Shape:** demonstrated unchanged exposure
**Expected verdict:** quiet. At most a pre-existing capped note. A critical or
warning finding, or a rendered Needs-verification item, counts as a false alarm.

## The already-reachable weaknesses a reviewer may notice

All of these are real or arguable, but none is new in this commit:

- (a) The queue and stop actions take a URL-supplied file name with no
  path-containment check.
- (b) The containment check silently does nothing when no local path is
  configured, and for remote delete it checks against the local path rather than
  the remote one.
- (c) The success response echoes the URL-decoded file name back in the body.

## Before/after comparison (the basis of the quiet verdict)

The commit touches only `src/python/web/handler/controller.py`. It moves the
shared body of five single-action handlers into one helper.

### Routes and inputs

| | base_sha b853a18 | feature_sha 43ee518 |
|---|---|---|
| Route registration (queue, stop, extract by POST; delete_local, delete_remote by DELETE; each with a `<file_name>` path segment) | `controller.py:66-70` | `controller.py:66-70` (identical lines) |
| Input: URL `<file_name>` unquoted before any check | each handler: `controller.py:81,100,119,142,165` | `_dispatch_command`: `controller.py:92` |

Same routes, same methods, same single URL input per route.

### Checks and outputs per route

| Route | base_sha b853a18 | feature_sha 43ee518 | Same? |
|---|---|---|---|
| queue | unquote `:81`; no `_check_path_safe`; echo `:91` | `_dispatch_command` with default `guard=False` (`:82`); echo `:104` | yes: unguarded before and after |
| stop | unquote `:100`; no `_check_path_safe`; echo `:110` | default `guard=False`; echo `:104` | yes: unguarded before and after |
| extract | unquote `:119`; `_check_path_safe` `:121-123`; echo `:133` | `guard=True` (`:125`) → `_check_path_safe` `:93-96`; echo `:104` | yes: guarded before and after, guard after unquote |
| delete_local | unquote `:142`; `_check_path_safe` `:144-146`; echo `:156` | `guard=True` (`:134`) → `:93-96`; echo `:104` | yes |
| delete_remote | unquote `:165`; `_check_path_safe` `:167-169`; echo `:179` | `guard=True` (`:143`) → `:93-96`; echo `:104` | yes |
| `_check_path_safe` body (no-op when local path unset; checks the local path) | `controller.py:209` | `controller.py:172` (returns None when unset at `:180`) | yes: same function, moved |
| Bulk-command path guard | `controller.py:373-376` | `controller.py:336-339` | yes: untouched, moved |

## Why the exposure is unchanged

For each of the five routes, the same URL input passes through the same unquote,
the same guard decision (guarded for the same three actions, unguarded for the
same two), the same command queue and the same echoing response (tables above).
The commit moves the shared scaffold into one helper and keeps
unquote-before-guard. It adds no route, caller or input, and removes no check.

## Supporting context (not proof)

No later commit touches this file to fix anything this refactor introduced. This
absence agrees with the verdict but does not establish it; the before/after
comparison above does.
