# reach-new-1 — expected verdict

**Shape:** demonstrated new exposure
**Expected verdict:** finding (warning, or critical if the reviewer establishes
a reader of the log viewer who is not the operator) at the new token log call or
at the log-buffer path it newly feeds.

## Keyed defect (answer-key form)

- **Defect:** the password-reset token is written to the in-app log viewer.
- **Location:** `triggarr/web/routes.py:1689-1692` at feature_sha
  (`logger.warning("Password reset token minted. ... {token}", token=token)`
  inside `reset_request_post`).
- **Causal failure:** the existing buffer sink copies every WARNING-level message
  into `log_buffer`, and redacts only the secrets collected at startup (the reset
  token is not among them). `GET /partials/log-viewer` and the dashboard render
  that buffer. So any party who can read the log viewer can read a live reset
  token and complete a password reset, contradicting the commit's own contract
  (`routes.py:1641`: "The token NEVER appears in any HTTP response body").

## Reachability evidence (at feature_sha 050c9c9)

1. **Input:** an unauthenticated `POST /reset/request`
   (`triggarr/web/routes.py:1627-1628`). It is exempt from the auth gate:
   `triggarr/web/middleware.py:118` passes `path.startswith("/reset/")` through
   without authentication.
2. **New step:** `routes.py:1679-1680` mints the token and stores it;
   `routes.py:1689-1692` logs it at WARNING.
3. **Existing, unchanged sink:** `triggarr/logging.py:72-84` registers
   `buffer_sink`, which replaces only the startup `secrets` list
   (`logging.py:74-76`) and adds the entry to `log_buffer`.
4. **Existing, unchanged reader:** `routes.py:1079-1094`
   (`partial_log_viewer`) returns `log_buffer.get_recent(30)` as HTML; the
   dashboard does the same at `routes.py:382`.

## Why the exposure is new relative to base_sha

At base_sha 345eaaa there is no reset-request route, no token is ever minted, and
nothing secret is logged on this path; the log viewer exists but carries no
credential that grants account control. The commit adds the first value that is
both a credential and routed into the viewer. Nothing in the logging or viewer
code changes, so the exposure comes entirely from the new caller.

## Repository follow-up (corroboration, not part of the case)

The owner's own deep review later logged this exact issue ("Reset token must not
reach the in-UI log viewer"), and it was fixed in `d5ed064`
("feat(77-04): keep reset token out of the in-app log viewer"). The commit also
received unrelated review fixes (`64dfd4d`, `77e9e4b`: a non-fatal token-file
write and a raw-fd leak); those are legitimate extra findings if raised, not
false alarms.
