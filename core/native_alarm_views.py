from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from .access import is_readonly_doctor
from .auto_reminders import sync_all_automatic_reminders
from .models import HealthReminder


@login_required
def native_alarm_schedule(request):
    """
    JSON schedule consumed by the Android companion app.

    Authentication is the same Django login session used by the WebView.
    The Dr Savvas/read-only account is intentionally excluded.
    """
    if is_readonly_doctor(request.user):
        return JsonResponse(
            {
                "enabled": False,
                "reason": "doctor_readonly",
                "items": [],
            }
        )

    now = timezone.now()
    sync_all_automatic_reminders(now=now)

    horizon = now + timedelta(days=14)
    rows = HealthReminder.objects.filter(
        active=True,
        completed=False,
        due_at__lte=horizon,
    ).order_by("due_at")

    items = []
    for reminder in rows:
        notify_at = reminder.due_at - timedelta(
            minutes=reminder.notify_minutes_before or 0
        )

        # A short grace window helps a phone that just came back online.
        if notify_at < now - timedelta(minutes=5):
            continue

        source_key = reminder.source_key or f"manual:{reminder.pk}"

        items.append(
            {
                "id": source_key,
                "reminder_id": reminder.pk,
                "type": reminder.reminder_type,
                "title": reminder.title,
                "body": reminder.notes or reminder.get_reminder_type_display(),
                "due_at": reminder.due_at.isoformat(),
                "notify_at": notify_at.isoformat(),
                "notify_at_epoch_ms": int(notify_at.timestamp() * 1000),
                "automatic": reminder.auto_generated,
                "alarm_sound": "agoo",
            }
        )

    return JsonResponse(
        {
            "enabled": True,
            "server_time": now.isoformat(),
            "items": items,
        }
    )
