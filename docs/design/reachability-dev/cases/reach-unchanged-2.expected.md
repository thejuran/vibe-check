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

## Reachability evidence

Feature_sha 43ee518 (after the change):
- Routes are unchanged: `src/python/web/handler/controller.py:66-70` (queue,
  stop and extract by POST; delete_local and delete_remote by DELETE, each with
  a `<file_name>` path segment).
- Shared helper `_dispatch_command` (`controller.py:76`) unquotes first
  (`:92`), runs `_check_path_safe` only when `guard` is true (`:93-94`), and
  echoes the name on success (`:104`, `success_msg.format(file_name)`).
- `guard=True` is passed only by extract, delete_local and delete_remote
  (`:125`, `:134`, `:143`). Queue and stop use the default `guard=False`.
- `_check_path_safe` (`:172`) returns None when the local path is unset (`:180`).

Base_sha b853a18 (before the change):
- Each of the five handlers unquoted first (`controller.py:81,100,119,142,165`).
- Only extract, delete_local and delete_remote called `_check_path_safe`
  (`:121,144,167`). Queue and stop did not.
- Every handler echoed the name on success (`:91,110,133,156,179`).

## Why the exposure is unchanged

For each of the five routes, the same URL input passes through the same unquote,
the same guard decision (guarded for the same three actions, unguarded for the
same two), the same command queue and the same echoing response. The commit
moves the shared scaffold into one helper and keeps unquote-before-guard. It adds
no route, caller or input, and removes no check. The bulk-command path is
untouched.

## Repository corroboration

No later commit touches this file to fix anything this refactor introduced.
