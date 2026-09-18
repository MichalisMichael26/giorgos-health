from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import HealthReminder, MealEntry, MedicalAppointment


FIXED_MEAL_TIMES = [
    time(1, 30),
    time(4, 30),
    time(7, 30),
    time(10, 30),
    time(13, 30),
    time(16, 30),
    time(19, 30),
    time(22, 30),
]

LOW_MEAL_THRESHOLD_ML = 50
LOW_MEAL_FOLLOWUP_MINUTES = 60
APPOINTMENT_NOTIFY_MINUTES_BEFORE = 24 * 60
MEAL_NOTIFY_MINUTES_BEFORE = 10


def _aware(local_date, local_time):
    naive = datetime.combine(local_date, local_time)
    return timezone.make_aware(naive, timezone.get_current_timezone())


def _upsert_auto_reminder(source_key, defaults):
    reminder = HealthReminder.objects.filter(source_key=source_key).first()

    if reminder is None:
        return HealthReminder.objects.create(
            source_key=source_key,
            auto_generated=True,
            **defaults,
        )

    timing_changed = (
        reminder.due_at != defaults["due_at"]
        or reminder.notify_minutes_before != defaults.get("notify_minutes_before", 0)
        or reminder.repeat_if_incomplete_minutes != defaults.get("repeat_if_incomplete_minutes", 0)
    )

    for field, value in defaults.items():
        setattr(reminder, field, value)

    reminder.auto_generated = True

    if timing_changed:
        reminder.push_notified_at = None
        reminder.push_repeat_notified_at = None

    reminder.save()
    return reminder


def sync_fixed_meal_reminders(now=None, include_tomorrow=True):
    """
    Ensure reminders exist for the fixed Giorgos feeding schedule.

    The reminder's due_at is the scheduled feeding time and the push is sent
    10 minutes before it.
    """
    now = now or timezone.now()
    local_today = timezone.localtime(now).date()
    days = [local_today]

    if include_tomorrow:
        days.append(local_today + timedelta(days=1))

    created_or_updated = 0

    for day in days:
        for scheduled_time in FIXED_MEAL_TIMES:
            source_key = f"meal-schedule:{day.isoformat()}:{scheduled_time.strftime('%H%M')}"
            already_logged = MealEntry.objects.filter(
                date=day,
                scheduled_time=scheduled_time,
            ).exists()

            _upsert_auto_reminder(
                source_key,
                {
                    "reminder_type": "meal",
                    "title": f"Προγραμματισμένο γεύμα {scheduled_time.strftime('%H:%M')}",
                    "due_at": _aware(day, scheduled_time),
                    "notes": "Αυτόματη υπενθύμιση: 10 λεπτά πριν από την προγραμματισμένη ώρα γεύματος.",
                    "notify_minutes_before": MEAL_NOTIFY_MINUTES_BEFORE,
                    "repeat_if_incomplete_minutes": 0,
                    "active": True,
                    "completed": already_logged,
                },
            )
            created_or_updated += 1

    # Keep the database tidy. Old schedule rows have no further purpose.
    cutoff = local_today - timedelta(days=7)
    HealthReminder.objects.filter(
        auto_generated=True,
        source_key__startswith="meal-schedule:",
        due_at__date__lt=cutoff,
    ).delete()

    return created_or_updated


def sync_low_meal_reminder(meal):
    """
    User-defined rule:
    if consumed amount is 50 ml or less, create a follow-up reminder 1 hour later.
    """
    source_key = f"low-meal:{meal.pk}"

    if meal.consumed_ml is None or meal.consumed_ml > LOW_MEAL_THRESHOLD_ML:
        HealthReminder.objects.filter(source_key=source_key).delete()
        return None

    base_time = meal.actual_time or meal.scheduled_time
    if not base_time:
        return None

    meal_dt = _aware(meal.date, base_time)
    due_at = meal_dt + timedelta(minutes=LOW_MEAL_FOLLOWUP_MINUTES)

    reminder = _upsert_auto_reminder(
        source_key,
        {
            "reminder_type": "meal",
            "title": f"Επανέλεγχος γεύματος — ήπιε {meal.consumed_ml} ml",
            "due_at": due_at,
            "notes": (
                f"Αυτόματη υπενθύμιση βάσει του κανόνα ≤ {LOW_MEAL_THRESHOLD_ML} ml. "
                f"Το καταχωρημένο γεύμα ήταν {meal.consumed_ml} ml. "
                f"Υπενθύμιση {LOW_MEAL_FOLLOWUP_MINUTES} λεπτά μετά."
            ),
            "notify_minutes_before": 0,
            "repeat_if_incomplete_minutes": 0,
            "active": True,
            "completed": False,
        },
    )
    return reminder


def sync_meal_schedule_completion(meal):
    if not meal.scheduled_time:
        return

    source_key = f"meal-schedule:{meal.date.isoformat()}:{meal.scheduled_time.strftime('%H%M')}"
    HealthReminder.objects.filter(source_key=source_key).update(completed=True)


def sync_appointment_reminder(appointment):
    source_key = f"appointment:{appointment.pk}"

    if appointment.status != "scheduled":
        HealthReminder.objects.filter(source_key=source_key).update(
            active=False,
            completed=True,
        )
        return None

    appointment_dt = _aware(appointment.date, appointment.time)
    existing = HealthReminder.objects.filter(source_key=source_key).first()

    return _upsert_auto_reminder(
        source_key,
        {
            "reminder_type": "appointment",
            "title": f"Ραντεβού — {appointment.purpose}",
            "due_at": appointment_dt,
            "notes": (
                "Αυτόματη υπενθύμιση 1 ημέρα πριν από το ραντεβού. "
                f"{appointment.doctor or ''} {appointment.clinic or ''}".strip()
            ),
            "notify_minutes_before": APPOINTMENT_NOTIFY_MINUTES_BEFORE,
            "repeat_if_incomplete_minutes": 0,
            "active": True,
            "completed": existing.completed if existing else False,
        },
    )


def sync_upcoming_appointment_reminders(now=None):
    now = now or timezone.now()
    today = timezone.localtime(now).date()

    appointments = MedicalAppointment.objects.filter(
        status="scheduled",
        date__gte=today,
    )

    count = 0
    for appointment in appointments:
        sync_appointment_reminder(appointment)
        count += 1

    return count


def sync_all_automatic_reminders(now=None):
    now = now or timezone.now()
    return {
        "meal_schedule": sync_fixed_meal_reminders(now=now, include_tomorrow=True),
        "appointments": sync_upcoming_appointment_reminders(now=now),
    }
