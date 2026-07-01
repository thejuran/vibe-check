"""Alert processing with machine grouping, priority escalation, and deduplication."""

import logging
import threading
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from app.models.health_state import HealthState
from app.models.machine import Machine
from app.models.notification_settings import NotificationSettings
from app.models.service import Service
from app.services.crypto import decrypt_value
from app.services.pushover_client import PushoverNotifier

logger = logging.getLogger(__name__)

# DR2-01: in-memory cooldown for machine-level agent_offline / agent_recovered
# Pushover dispatch. Without this a flapping agent (dies every 180-300s just
# past the 3-strike hysteresis) pages priority-1 on every cycle, overriding
# operator DND. 5-minute cooldown keyed on (machine_id, kind) matches the
# per-event HealthState.last_notified_state sentinel used at the service level.
# Cooldown state is process-lifetime (resets on restart — acceptable; the next
# flap edge fires once and then suppresses normally).
#
# DR3w-01: the check-and-set must be serialized. `_dispatch_machine_events` is
# invoked from two background threadpool threads (`health_check_loop` +
# `ingest_probe_results_loop`). Individual dict ops are GIL-atomic, but the
# `get` and the `[key] = now` are separate bytecodes with a GIL-release window
# between them — two threads dispatching the same (machine_id, kind) in the
# same tick can both read None and both send Pushover, defeating the cooldown.
# The Pushover HTTP call stays OUTSIDE the lock so a slow notifier.send_* does
# not serialize every dispatch.
_MACHINE_ALERT_COOLDOWN_SECONDS = 300  # 5 minutes
_machine_alert_last_sent: dict[tuple[int, str], float] = {}
_machine_alert_lock = threading.Lock()


def _reset_machine_alert_cooldown() -> None:
    """Test hook — clear the DR2-01 machine-alert cooldown dict."""
    with _machine_alert_lock:
        _machine_alert_last_sent.clear()


def should_send_alert(health: HealthState, session: Session) -> bool:
    """
    Determine whether a notification should be sent for this health state.

    Prevents duplicate notifications by comparing current state to last notified state.
    Phase 42 adds a machine-level grace-window gate (G-02..G-05).

    Gates (in order):
    1. Dedup: same state as last_notified_state -> False.
    2. First check passing (no prior notification, not down) -> False.
    3. Machine grace window (G-02): if the service's machine has
       alerts_suppressed_until > now, return False. Blanket suppression per
       G-03 -- blocks BOTH service_down and service_recovered events for the
       first 60s after agent recovery to prevent the v1.0 thundering-herd
       pattern. Applies only to service-level events; machine-level events
       (agent_offline/agent_recovered) bypass this function per G-05.
    4. DOWN always alerts.
    5. Recovery from non-healthy alerts.
    6. Other transitions suppressed.
    """
    # Prevent duplicates: same state already notified
    if health.state == health.last_notified_state:
        return False

    # Don't alert for first check passing (new service that's healthy)
    if health.last_notified_state is None and health.state != "down":
        return False

    # G-02 / G-03 (Phase 42): machine-grace window — blanket suppression for
    # the service's machine when alerts_suppressed_until is in the future.
    # Applies to SERVICE-level events only; machine-level events
    # (agent_offline/agent_recovered) are routed separately and bypass here.
    service = session.get(Service, health.service_id)
    if service is not None and service.machine_id is not None:
        machine = session.get(Machine, service.machine_id)
        if machine is not None and machine.alerts_suppressed_until is not None:
            suppressed_until = machine.alerts_suppressed_until
            if suppressed_until.tzinfo is None:
                suppressed_until = suppressed_until.replace(tzinfo=UTC)
            if suppressed_until > datetime.now(UTC):
                return False

    # Always alert on DOWN
    if health.state == "down":
        return True

    # Alert on recovery (any non-healthy -> HEALTHY)
    if health.state == "healthy" and health.last_notified_state not in (
        None,
        "healthy",
    ):
        return True

    # All other transitions (UNKNOWN->DEGRADED, etc.)
    return False


def process_health_events(events: list[dict[str, Any]], session: Session) -> None:
    """
    Process health check events and send Pushover notifications.

    Groups down events by machine for emergency escalation.
    Sends individual recovery alerts.
    Updates last_notified_state after successful sends.

    Phase 42 DR-01: also handles machine-level agent events:
    {"event": "agent_offline"|"agent_recovered", "machine_id": N}. These
    bypass the per-machine grace window gate (G-05) — the operator
    always wants to know when an agent is down or back.

    Args:
        events: List of event dicts from health checker
               ({"event": "service_down"/"service_recovered", "service_id": N, ...})
               or agent-liveness cascade
               ({"event": "agent_offline"/"agent_recovered", "machine_id": N}).
        session: Database session
    """
    if not events:
        return

    # Load notification settings (singleton row)
    settings = session.exec(select(NotificationSettings)).first()
    if settings is None or not settings.pushover_user_key or not settings.pushover_api_token:
        logger.debug("Pushover not configured - skipping notifications")
        return

    notifier = PushoverNotifier(
        user_key=decrypt_value(settings.pushover_user_key),
        api_token=decrypt_value(settings.pushover_api_token),
    )

    # DR-01: separate machine-level agent events from service-level events.
    # Agent events don't carry service_id and must not be routed through the
    # service_id-keyed dispatch loop below (which would KeyError or silently
    # skip them and drop the Pushover notification).
    _dispatch_machine_events(events, session, settings, notifier)

    # Separate events by type
    down_events: list[dict[str, Any]] = []
    recovered_events: list[dict[str, Any]] = []

    for event in events:
        # Skip machine-level events already handled above.
        if event.get("event") in ("agent_offline", "agent_recovered", "machine_offline", "machine_reconnected"):
            continue
        if "service_id" not in event:
            # Defensive: unexpected event shape — log and skip rather than KeyError.
            logger.warning("Alerting: unexpected event shape (no service_id): %r", event)
            continue
        service_id = event["service_id"]
        health = session.get(HealthState, service_id)
        if health is None:
            continue

        if not should_send_alert(health, session):
            continue

        if event["event"] == "service_down":
            down_events.append(event)
        elif event["event"] == "service_recovered":
            recovered_events.append(event)

    # Group down events by machine for potential emergency escalation
    machine_failures: dict[int | None, list[dict[str, Any]]] = defaultdict(list)
    for event in down_events:
        service = session.get(Service, event["service_id"])
        if service:
            machine_failures[service.machine_id].append(event)

    # Process grouped down events
    for machine_id, machine_events in machine_failures.items():
        machine = session.get(Machine, machine_id) if machine_id else None
        if machine:
            hostname = machine.hostname
        else:
            # Manual services: use service name as hostname identifier in alerts
            svc = session.get(Service, machine_events[0]["service_id"])
            hostname = svc.name if svc else "unknown"

        if len(machine_events) >= settings.emergency_threshold:
            # Emergency: multiple services down on same machine
            service_names = []
            for evt in machine_events:
                svc = session.get(Service, evt["service_id"])
                if svc:
                    service_names.append(svc.name_override or svc.name)

            success = notifier.send_multi_service_alert(
                machine_hostname=hostname,
                failed_services=service_names,
                dashboard_url=settings.dashboard_url,
            )
            if success:
                for evt in machine_events:
                    _mark_notified(session, evt["service_id"], "down")
        else:
            # Individual down alerts
            for evt in machine_events:
                svc = session.get(Service, evt["service_id"])
                if not svc:
                    continue

                success = notifier.send_service_down_alert(
                    service_name=svc.name_override or svc.name,
                    machine_hostname=hostname,
                    failure_reason=evt.get("reason", "Unknown"),
                    dashboard_url=settings.dashboard_url,
                    quiet_hours=(
                        settings.quiet_hours_start,
                        settings.quiet_hours_end,
                    )
                    if settings.quiet_hours_start and settings.quiet_hours_end
                    else None,
                    tz_name=settings.quiet_hours_timezone,
                )
                if success:
                    _mark_notified(session, evt["service_id"], "down")

    # Process recovery events (always individual)
    for event in recovered_events:
        service = session.get(Service, event["service_id"])
        if not service:
            continue

        machine = session.get(Machine, service.machine_id) if service.machine_id else None
        hostname = machine.hostname if machine else (service.name_override or service.name)

        success = notifier.send_service_recovered_alert(
            service_name=service.name_override or service.name,
            machine_hostname=hostname,
            dashboard_url=settings.dashboard_url,
        )
        if success:
            _mark_notified(session, event["service_id"], "healthy")

    session.commit()


def _dispatch_machine_events(
    events: list[dict[str, Any]],
    session: Session,
    settings: NotificationSettings,
    notifier: PushoverNotifier,
) -> None:
    """DR-01: send Pushover alerts for agent_offline / agent_recovered events.

    Machine-level events bypass the service-level grace window (G-05). Mirrors
    the existing send_service_down_alert / send_service_recovered_alert shape
    but uses the dedicated send_agent_*_alert methods so the copy and priority
    match `machine_offline` / `machine_reconnected` precedent.

    DR2-01: per-(machine_id, kind) cooldown prevents a flapping agent from
    spamming priority-1 Pushover pages. Cooldown is 5 minutes keyed on
    time.monotonic() so the check is robust against system-clock drift.
    """
    now = time.monotonic()
    for event in events:
        kind = event.get("event")
        if kind not in ("agent_offline", "agent_recovered"):
            continue
        machine_id = event.get("machine_id")
        if machine_id is None:
            logger.warning("Alerting: agent event without machine_id: %r", event)
            continue
        # DR2-01 cooldown: skip if we sent the same (machine_id, kind)
        # notification within the cooldown window. Separate cooldowns per kind
        # so an immediate offline->recovered edge still fires both alerts.
        # `last is None` means "never sent before" — must fire. Using dict.get()
        # with a 0.0 default is wrong here because time.monotonic() can start
        # at 0.0 on some platforms (and always starts at 0.0 under a test
        # monotonic stub), which would make every first dispatch suppress itself.
        #
        # DR3w-01: lock ONLY the check-and-set. The Pushover HTTP call stays
        # outside the critical section so a slow notifier.send_* does not
        # serialize every dispatch. Two threads racing on the same
        # (machine_id, kind) now resolve deterministically: the winner writes
        # `now` and fires; the loser sees the fresh timestamp and suppresses.
        key = (machine_id, kind)
        with _machine_alert_lock:
            last = _machine_alert_last_sent.get(key)
            if last is not None and now - last < _MACHINE_ALERT_COOLDOWN_SECONDS:
                logger.info(
                    "Alerting: suppressing %s for machine %d (cooldown %.0fs remaining)",
                    kind,
                    machine_id,
                    _MACHINE_ALERT_COOLDOWN_SECONDS - (now - last),
                )
                continue
            _machine_alert_last_sent[key] = now
        # Lock released — Pushover HTTP call stays outside the critical section.
        machine = session.get(Machine, machine_id)
        hostname = machine.hostname if machine else f"machine-{machine_id}"
        if kind == "agent_offline":
            notifier.send_agent_offline_alert(
                machine_hostname=hostname,
                dashboard_url=settings.dashboard_url,
            )
        else:
            notifier.send_agent_recovered_alert(
                machine_hostname=hostname,
                dashboard_url=settings.dashboard_url,
            )


def _mark_notified(session: Session, service_id: int, state: str) -> None:
    """Update health state to record that notification was sent."""
    health = session.get(HealthState, service_id)
    if health:
        health.last_notified_state = state
        health.last_notification_sent = datetime.now(UTC)
        session.add(health)


def verify_pushover_connectivity(session: Session) -> dict:
    """
    Verify Pushover configuration and connectivity.

    Used by settings page test button and startup check.

    Returns:
        Dict with keys: configured (bool), connected (bool), error (str or None)
    """
    settings = session.exec(select(NotificationSettings)).first()
    if settings is None or not settings.pushover_user_key or not settings.pushover_api_token:
        return {
            "configured": False,
            "connected": False,
            "error": "Pushover not configured",
        }

    try:
        notifier = PushoverNotifier(
            user_key=decrypt_value(settings.pushover_user_key),
            api_token=decrypt_value(settings.pushover_api_token),
        )
        success = notifier.test_notification()
        return {
            "configured": True,
            "connected": success,
            "error": None if success else "Test notification failed",
        }
    except Exception as e:
        logger.error("Pushover connectivity check failed: %s", e, exc_info=True)
        return {
            "configured": True,
            "connected": False,
            "error": "Pushover connectivity check failed",
        }
