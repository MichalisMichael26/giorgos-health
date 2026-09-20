import base64
import json
import os
from datetime import timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.utils import timezone
from django.db import connection
from py_vapid import Vapid
from pywebpush import WebPushException, webpush

from .access import is_readonly_doctor
from .models import HealthReminder, PushConfig, PushDeliveryLog, PushSubscription


def get_or_create_push_config():
    config = PushConfig.objects.first()
    if config:
        return config

    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    public_b64 = base64.urlsafe_b64encode(public_bytes).rstrip(b"=").decode("ascii")

    return PushConfig.objects.create(
        private_key_pem=private_pem,
        public_key_b64=public_b64,
    )


def active_parent_subscriptions():
    subscriptions = []
    for sub in PushSubscription.objects.filter(active=True).select_related("user"):
        if not is_readonly_doctor(sub.user):
            subscriptions.append(sub)
    return subscriptions


def reminder_icon(reminder_type):
    return {
        "meal": "🍼",
        "medication": "💊",
        "vaccine": "💉",
        "measurement": "🩸",
        "lab": "🧪",
        "appointment": "📅",
        "other": "🔔",
    }.get(reminder_type, "🔔")


def reminder_payload(reminder, delivery_kind="initial"):
    local_due = timezone.localtime(reminder.due_at)
    icon = reminder_icon(reminder.reminder_type)

    if delivery_kind == "repeat":
        title = f"{icon} Υπενθύμιση που εκκρεμεί"
        body = f"{reminder.title} · προγραμματισμένο {local_due:%H:%M}"
    elif reminder.notify_minutes_before:
        title = f"{icon} {reminder.title}"
        minutes_before = reminder.notify_minutes_before
        if minutes_before >= 1440 and minutes_before % 1440 == 0:
            days = minutes_before // 1440
            when_text = "Σε 1 ημέρα" if days == 1 else f"Σε {days} ημέρες"
        elif minutes_before >= 60 and minutes_before % 60 == 0:
            hours = minutes_before // 60
            when_text = "Σε 1 ώρα" if hours == 1 else f"Σε {hours} ώρες"
        else:
            when_text = f"Σε {minutes_before} λεπτά"
        body = f"{when_text} · {local_due:%H:%M}"
    else:
        title = f"{icon} {reminder.title}"
        body = f"Τώρα · {local_due:%H:%M}"

    return {
        "title": title,
        "body": body,
        "tag": f"giorgos-reminder-{reminder.pk}-{delivery_kind}",
        "url": "/reminders/",
        "icon": "/static/icons/icon-192.png",
        "badge": "/static/icons/icon-192.png",
        "silent": False,
        "vibrate": [220, 100, 220],
        "renotify": True,
        "data": {
            "reminder_id": reminder.pk,
            "delivery_kind": delivery_kind,
            "url": "/reminders/",
        },
    }


def _send_to_subscription(subscription, payload):
    config = get_or_create_push_config()
    info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth,
        },
    }

    subject = os.environ.get(
        "VAPID_SUBJECT",
        "mailto:giorgos-health@example.com",
    )

    try:
        # pywebpush treats ordinary strings as DER/base64 key material or as a
        # filesystem path. Our key is stored in PostgreSQL as PEM text, so parse
        # it explicitly into a Vapid object before sending.
        vapid_key = Vapid.from_pem(config.private_key_pem.encode("utf-8"))

        response = webpush(
            subscription_info=info,
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=vapid_key,
            vapid_claims={"sub": subject},
            ttl=300,
        )
        return True, getattr(response, "status_code", None), ""
    except WebPushException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in {404, 410}:
            subscription.active = False
            subscription.save(update_fields=["active", "last_seen_at"])
        return False, status, str(exc)
    except Exception as exc:
        return False, None, str(exc)


def send_test_push(user):
    payload = {
        "title": "🔔 Giorgos Health",
        "body": "Οι ειδοποιήσεις στο κινητό λειτουργούν.",
        "tag": "giorgos-health-test",
        "url": "/reminders/",
        "icon": "/static/icons/icon-192.png",
        "badge": "/static/icons/icon-192.png",
        "silent": False,
        "vibrate": [220, 100, 220],
        "renotify": True,
        "data": {"url": "/reminders/"},
    }

    subscriptions = list(
        PushSubscription.objects.filter(user=user, active=True)
    )

    successes = 0
    failures = 0
    last_status = None
    last_error = ""

    for sub in subscriptions:
        ok, status, error = _send_to_subscription(sub, payload)
        successes += int(ok)
        failures += int(not ok)

        if not ok:
            last_status = status
            last_error = error or ""

    return {
        "active_devices": len(subscriptions),
        "successes": successes,
        "failures": failures,
        "last_status": last_status,
        "last_error": last_error,
    }


def send_reminder_push(reminder, delivery_kind="initial"):
    payload = reminder_payload(reminder, delivery_kind)
    subscriptions = active_parent_subscriptions()

    attempted = 0
    successes = 0

    for sub in subscriptions:
        attempted += 1
        ok, status_code, error = _send_to_subscription(sub, payload)
        successes += int(ok)
        PushDeliveryLog.objects.create(
            reminder=reminder,
            subscription=sub,
            delivery_kind=delivery_kind,
            success=ok,
            status_code=status_code,
            error=error[:2000],
        )

    return attempted, successes


PUSH_DISPATCH_LOCK_ID = 824611093


def _try_dispatch_lock():
    if connection.vendor != "postgresql":
        return True

    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [PUSH_DISPATCH_LOCK_ID])
        row = cursor.fetchone()
        return bool(row and row[0])


def _release_dispatch_lock():
    if connection.vendor != "postgresql":
        return

    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_unlock(%s)", [PUSH_DISPATCH_LOCK_ID])


def dispatch_due_reminders(now=None):
    now = now or timezone.now()

    counters = {
        "initial_attempts": 0,
        "initial_successes": 0,
        "repeat_attempts": 0,
        "repeat_successes": 0,
        "reminders_marked": 0,
        "skipped_locked": 0,
    }

    if not _try_dispatch_lock():
        counters["skipped_locked"] = 1
        return counters

    try:
        # Keep system-generated meal/appointment reminders synchronized before
        # deciding which push notifications are due.
        from .auto_reminders import sync_all_automatic_reminders
        sync_all_automatic_reminders(now=now)

        # Repair reminders that older code marked as "notified" merely because
        # an attempt was made, even when every delivery failed. If there is no
        # successful delivery log, make the still-useful reminder eligible for
        # another attempt.
        previously_marked = HealthReminder.objects.filter(
            active=True,
            completed=False,
            push_notified_at__isnull=False,
            due_at__gte=now - timedelta(hours=1),
        )
        for reminder in previously_marked:
            delivered = PushDeliveryLog.objects.filter(
                reminder=reminder,
                delivery_kind="initial",
                success=True,
            ).exists()
            if not delivered:
                reminder.push_notified_at = None
                reminder.save(update_fields=["push_notified_at", "updated_at"])

        qs = HealthReminder.objects.filter(
            active=True,
            completed=False,
        ).order_by("due_at")

        for reminder in qs:
            # Initial notification. Do not send very old stale reminders.
            if reminder.push_notified_at is None:
                trigger = reminder.due_at - timedelta(
                    minutes=reminder.notify_minutes_before or 0
                )
                latest_useful = reminder.due_at + timedelta(hours=1)

                if trigger <= now <= latest_useful:
                    attempted, successes = send_reminder_push(reminder, "initial")
                    counters["initial_attempts"] += attempted
                    counters["initial_successes"] += successes

                    # IMPORTANT: mark as delivered only when at least one push
                    # actually succeeded. Transient failures are retried by the
                    # next scheduler pass instead of being silently lost.
                    if successes:
                        reminder.push_notified_at = now
                        reminder.save(update_fields=["push_notified_at", "updated_at"])
                        counters["reminders_marked"] += 1

            # Optional second alert if still incomplete.
            if (
                reminder.repeat_if_incomplete_minutes
                and reminder.push_notified_at is not None
                and reminder.push_repeat_notified_at is None
            ):
                repeat_trigger = reminder.due_at + timedelta(
                    minutes=reminder.repeat_if_incomplete_minutes
                )
                repeat_latest = reminder.due_at + timedelta(hours=6)

                if repeat_trigger <= now <= repeat_latest:
                    attempted, successes = send_reminder_push(reminder, "repeat")
                    counters["repeat_attempts"] += attempted
                    counters["repeat_successes"] += successes

                    if successes:
                        reminder.push_repeat_notified_at = now
                        reminder.save(
                            update_fields=["push_repeat_notified_at", "updated_at"]
                        )

        return counters
    finally:
        _release_dispatch_lock()
