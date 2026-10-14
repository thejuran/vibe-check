# reach-new-2 — expected verdict

**Shape:** demonstrated new exposure (a guard removed)
**Expected verdict:** finding (warning) at the changed binding.

## Keyed defect (answer-key form)

- **Defect:** notification text is rendered as HTML instead of as text (HTML
  injection).
- **Location:**
  `src/angular/src/app/pages/main/notification-bell.component.html:28` at
  feature_sha (`<span class="bell-notif-text" [innerHTML]="notif.text">`).
- **Causal failure:** the change routes unchanged server- and remote-influenced
  notification strings into an HTML parser. With `[innerHTML]`, markup in those
  strings is parsed as HTML in every open UI. Angular's sanitizer strips scripts
  and event handlers but keeps links, images and formatting, so injected markup
  can render attacker-controlled links or images in a trusted UI element.
  Interpolation (`{{ notif.text }}`) rendered the same strings as inert text.

## Scoring rule for this case

Credit is for the **demonstrated HTML injection**: a row that names this binding
and the causal failure above (influenced notification text now parsed as HTML)
earns the catch. Script execution is **neither required nor claimed**: a row
need not show a script running, and the case does not assert that one can run
past Angular's sanitizer. A row that claims script execution is still credited
for the HTML-injection substance it carries; the over-claim is not the keyed
defect.

## Unchanged sources and sinks the change newly reaches

The commit changes one line of one file (`notification-bell.component.html`,
1 insertion, 1 deletion). Every source below is the same code at the same line at
both commits:

| Unchanged step | base_sha a6a0c6d | feature_sha 093cd18 |
|---|---|---|
| Remote scanner error copied into status (`latest_remote_scan_error = remote_scan.error_message`) | `src/python/controller/controller.py:633` | `src/python/controller/controller.py:633` |
| Serialized to the UI | `src/python/web/serialize/serialize_status.py:37` | `src/python/web/serialize/serialize_status.py:37` |
| Parsed in the UI | `src/angular/src/app/services/server/server-status.ts:74` | `src/angular/src/app/services/server/server-status.ts:74` |
| Notification text built from it | `src/angular/src/app/pages/main/header.component.ts:96` via `src/angular/src/app/common/localization.ts:15-16` | same lines |
| Server error bodies become notification text (`text: reaction.errorMessage`) | `src/angular/src/app/pages/settings/settings-page.component.ts:170,239,257` | same lines |
| Example echo: auto-queue 409 body includes the submitted pattern | `src/python/web/handler/auto_queue.py:32` | `src/python/web/handler/auto_queue.py:32` |
| **Sink: notification text binding** | `notification-bell.component.html:28` = `{{ notif.text }}` (escaped text) | `notification-bell.component.html:28` = `[innerHTML]="notif.text"` (HTML parser) |

## Reachability evidence (at feature_sha 093cd18)

1. **Remote-influenced input:** `controller.py:633` → `serialize_status.py:37` →
   `server-status.ts:74` → `header.component.ts:96` (text via
   `localization.ts:15-16`).
2. **User/server echo input:** `settings-page.component.ts:170,239,257` turn
   server error bodies into notification text; `auto_queue.py:32` echoes the
   submitted pattern in its 409 body.
3. **Sink:** `notification-bell.component.html:28` now binds that text with
   `[innerHTML]`.

## Why the exposure is new relative to base_sha

The sources and the notification text are identical at both commits (table
above); only the sink changed. At base_sha a6a0c6d line 28 renders
`{{ notif.text }}` (escaped text), and no other template renders notification
text through `innerHTML`. The only `innerHTML` use in the Angular app at base is
`src/angular/src/app/services/utils/confirm-modal.service.ts:100`, which these
strings do not reach. The commit is the first change that routes these unchanged
strings into an HTML parser.

## Supporting context (not proof)

Reverted the same day by `68bc550`
("fix(62): CR-01 replace innerHTML with text interpolation to prevent XSS"). The
expected verdict rests on the code comparison above, not on this history.
