from datetime import datetime, timedelta

from django.utils import timezone

from .feeding_timing import (
    feeding_interval_minutes,
    format_interval,
    meal_finished_datetime,
    meal_start_datetime,
    next_meal_due,
)
from .models import ChildProfile, HealthReminder, MedicalAppointment


LOW_MEAL_THRESHOLD_ML = 50
LOW_MEAL_FOLLOWUP_MINUTES = 60
APPOINTMENT_NOTIFY_MINUTES_BEFORE = 24 * 60
MEAL_NOTIFY_MINUTES_BEFORE = 11
DYNAMIC_MEAL_SOURCE_KEY = "meal-next:dynamic"


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


def sync_dynamic_meal_reminder(now=None):
    """
    Keep ONE next-meal reminder based on:
        previous meal finish time + configured feeding interval.

    The old fixed clock schedule is no longer used for automatic meal pushes.
    """
    now = now or timezone.now()
    profile = ChildProfile.objects.first()

    due_at, last_meal, finished_at = next_meal_due(
        profile=profile,
        now=now,
    )

    # If no completed meal has a finish time, or another meal has already
    # started but has not yet finished, an exact next-feed time cannot be
    # calculated safely. Remove any stale dynamic reminder.
    if due_at is None or last_meal is None or finished_at is None:
        HealthReminder.objects.filter(source_key=DYNAMIC_MEAL_SOURCE_KEY).delete()
        return None

    interval = feeding_interval_minutes(profile)

    return _upsert_auto_reminder(
        DYNAMIC_MEAL_SOURCE_KEY,
        {
            "reminder_type": "meal",
            "title": f"Επόμενο γεύμα · {timezone.localtime(due_at):%H:%M}",
            "due_at": due_at,
            "notes": (
                "Αυτόματη υπενθύμιση: "
                f"{format_interval(interval)} μετά την ολοκλήρωση του προηγούμενου γεύματος "
                f"({timezone.localtime(finished_at):%H:%M}). "
                f"Push {MEAL_NOTIFY_MINUTES_BEFORE} λεπτά πριν."
            ),
            "notify_minutes_before": MEAL_NOTIFY_MINUTES_BEFORE,
            "repeat_if_incomplete_minutes": 0,
            "active": True,
            "completed": False,
        },
    )


def sync_low_meal_reminder(meal):
    """
    User-defined rule:
    if consumed amount is 50 ml or less, create a follow-up reminder 1 hour
    after the meal FINISH time. Older entries without a finish time fall back
    to their recorded start/reference time for backwards compatibility.
    """
    source_key = f"low-meal:{meal.pk}"

    if meal.consumed_ml is None or meal.consumed_ml > LOW_MEAL_THRESHOLD_ML:
        HealthReminder.objects.filter(source_key=source_key).delete()
        return None

    base_dt = meal_finished_datetime(meal) or meal_start_datetime(meal)
    if base_dt is None:
        return None

    due_at = base_dt + timedelta(minutes=LOW_MEAL_FOLLOWUP_MINUTES)

    reminder = _upsert_auto_reminder(
        source_key,
        {
            "reminder_type": "meal",
            "title": f"Επανέλεγχος γεύματος — ήπιε {meal.consumed_ml} ml",
            "due_at": due_at,
            "notes": (
                f"Αυτόματη υπενθύμιση βάσει του κανόνα ≤ {LOW_MEAL_THRESHOLD_ML} ml. "
                f"Το καταχωρημένο γεύμα ήταν {meal.consumed_ml} ml. "
                f"Υπενθύμιση {LOW_MEAL_FOLLOWUP_MINUTES} λεπτά μετά "
                "την ολοκλήρωση του γεύματος."
            ),
            "notify_minutes_before": 0,
            "repeat_if_incomplete_minutes": 0,
            "active": True,
            "completed": False,
        },
    )
    return reminder


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

    # Clean up any old fixed-clock meal reminders left by older versions.
    HealthReminder.objects.filter(
        auto_generated=True,
        source_key__startswith="meal-schedule:",
    ).delete()

    meal_reminder = sync_dynamic_meal_reminder(now=now)

    return {
        "meal_schedule": 1 if meal_reminder else 0,
        "dynamic_meal": 1 if meal_reminder else 0,
        "appointments": sync_upcoming_appointment_reminders(now=now),
    }
