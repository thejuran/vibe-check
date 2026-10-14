# reach-new-1 — expected verdict

**Label:** development evidence — shares a broad category with a B3 case; not
independent evidence.

**Shape:** demonstrated new exposure
**Expected verdict:** finding (warning, or critical if the reviewer establishes
a reader of the log viewer who is not the operator) at the new token log call or
at the log-buffer path it newly feeds.

## Keyed defect (answer-key form)

- **Defect:** the password-reset token is written to the in-app log viewer.
- **Location:** `triggarr/web/routes.py:1689-1692` at feature_sha
  (`logger.warning("Password reset token minted. ... {token}", token=token)`
  inside `reset_request_post`).
- **Causal failure:** the change sends a new credential into an unchanged
  logging path. The unchanged buffer sink copies every message at the configured
  level into `log_buffer`, and redacts only the values in the unchanged startup
  redaction list, which does not contain the reset token. The unchanged log
  viewer and dashboard render that buffer. So any party who can read the log
  viewer can read a live reset token and complete a password reset, contradicting
  the commit's own contract (`routes.py:1641`: "The token NEVER appears in any
  HTTP response body").

## Unchanged behavior the change newly reaches

The commit touches only `triggarr/web/routes.py` (167 insertions, no deletions).
`git diff 345eaaa 050c9c9 -- triggarr/logging.py triggarr/startup.py
triggarr/web/middleware.py` is empty. Each downstream step below is the same code
at both commits; only the line offset in `routes.py` moves by 2.

| Unchanged step | base_sha 345eaaa | feature_sha 050c9c9 |
|---|---|---|
| Buffer sink: redacts `secrets`, then `log_buffer.add` | `triggarr/logging.py:72-84` | `triggarr/logging.py:72-84` |
| Redaction list: `collect_secrets(settings)` (configured API keys + auth secrets; no reset token) passed to `setup_logging` | `triggarr/startup.py:74`, `:195-198` | `triggarr/startup.py:74`, `:195-198` |
| In-app log viewer: `GET /partials/log-viewer` renders `log_buffer.get_recent(30)` | `triggarr/web/routes.py:1077-1092` | `triggarr/web/routes.py:1079-1094` |
| Dashboard reads the same buffer | `triggarr/web/routes.py:380` | `triggarr/web/routes.py:382` |
| Auth gate passes `/reset/` paths through unauthenticated | `triggarr/web/middleware.py:118` | `triggarr/web/middleware.py:118` |

## Reachability evidence (at feature_sha 050c9c9)

1. **Input:** an unauthenticated `POST /reset/request`
   (`triggarr/web/routes.py:1627-1628`, new). It is exempt from the auth gate:
   `triggarr/web/middleware.py:118` (unchanged) passes `path.startswith("/reset/")`
   through without authentication.
2. **New step:** `routes.py:1679-1680` mints the token and stores it;
   `routes.py:1689-1692` logs it at WARNING. The in-code comment at
   `routes.py:1682-1686` states the token is intentionally not added to
   `collect_secrets`.
3. **Unchanged sink, newly reached by a credential:** `triggarr/logging.py:72-84`
   (`buffer_sink`) replaces only the `secrets` list built by
   `triggarr/startup.py:195` and adds the entry to `log_buffer`. The reset token
   passes through unredacted.
4. **Unchanged readers, newly carrying a credential:** `routes.py:1079-1094`
   (`partial_log_viewer`) returns the buffer as HTML; the dashboard reads it at
   `routes.py:382`.

## Why the exposure is new relative to base_sha

At base_sha 345eaaa the sink, the redaction list, the viewer and the dashboard
are the same code (table above), but no route mints a reset token and no caller
logs a credential that the redaction list misses. The viewer therefore carries no
value that grants account control. The commit adds the first caller that routes
such a value into the unchanged sink, so the exposure comes entirely from the new
caller reaching unchanged downstream behavior. A finding that only says "a new
bug appeared" without naming that unchanged sink/viewer path does not exercise
the reachability rule.

## Supporting context (not proof)

The owner's own deep review later logged this exact issue ("Reset token must not
reach the in-UI log viewer"), and it was fixed in `d5ed064`
("feat(77-04): keep reset token out of the in-app log viewer"). The commit also
received unrelated review fixes (`64dfd4d`, `77e9e4b`: a non-fatal token-file
write and a raw-fd leak); those are legitimate extra findings if raised, not
false alarms. The expected verdict rests on the code comparison above, not on
this history.
