# reach-new-2 — expected verdict

**Shape:** demonstrated new exposure (a guard removed)
**Expected verdict:** finding (warning) at the changed binding.

## Keyed defect (answer-key form)

- **Defect:** notification text is rendered as HTML instead of as text.
- **Location:**
  `src/angular/src/app/pages/main/notification-bell.component.html:28` at
  feature_sha (`<span class="bell-notif-text" [innerHTML]="notif.text">`).
- **Causal failure:** notification text is built from server- and
  remote-influenced strings. With `[innerHTML]`, markup in those strings is parsed
  as HTML in every open UI. Angular's sanitizer strips scripts and event handlers
  but keeps links, images and formatting, so injected markup can render
  attacker-controlled links or images in a trusted UI element. Interpolation
  (`{{ notif.text }}`) rendered the same strings as inert text.

## Reachability evidence (at feature_sha 093cd18)

1. **Remote-influenced input:** the controller copies the remote scanner's error
   text into status (`src/python/controller/controller.py:633`,
   `latest_remote_scan_error = remote_scan.error_message`), which is serialized
   to the UI (`src/python/web/serialize/serialize_status.py:37`) and parsed
   (`src/angular/src/app/services/server/server-status.ts:74`).
2. **Into a notification:** `src/angular/src/app/pages/main/header.component.ts:96`
   builds the notification text from it via
   `src/angular/src/app/common/localization.ts:15-16`.
3. **User/server echo input:** server error bodies become notification text
   (`src/angular/src/app/pages/settings/settings-page.component.ts:170,239,257`,
   `text: reaction.errorMessage`). For example, the auto-queue handler echoes the
   submitted pattern in its 409 body
   (`src/python/web/handler/auto_queue.py:32`).
4. **Sink:** `notification-bell.component.html:28` now binds that text with
   `[innerHTML]`.

## Why the exposure is new relative to base_sha

At base_sha a6a0c6d the same line renders `{{ notif.text }}` (escaped text), and
no other template renders notification text through `innerHTML`. The only
`innerHTML` use in the Angular app at base is the confirm-modal service, which
these strings do not reach. The commit is the first change that routes these
strings into an HTML parser.

## Repository follow-up (corroboration, not part of the case)

Reverted the same day by `68bc550`
("fix(62): CR-01 replace innerHTML with text interpolation to prevent XSS").
