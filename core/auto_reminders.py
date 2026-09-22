from datetime import datetime, timedelta

from django.utils import timezone

from .feeding_timing import FIXED_FEED_TIMES, meal_finished_datetime, meal_start_datetime
from .models import HealthReminder, MealEntry, MedicalAppointment


LOW_MEAL_THRESHOLD_ML = 50
LOW_MEAL_FOLLOWUP_MINUTES = 60
APPOINTMENT_NOTIFY_MINUTES_BEFORE = 24 * 60
MEAL_NOTIFY_MINUTES_BEFORE = 12


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


def _meal_schedule_source_key(day, feed_time):
    return f"meal-schedule:{day.isoformat()}:{feed_time.strftime('%H%M')}"


def sync_fixed_meal_schedule_reminders(now=None):
    """
    Create fixed meal reminders for today and tomorrow.

    Current pediatrician-directed schedule:
    00:00 / 03:00 / 06:00 / 09:00 / 12:00 / 15:00 / 18:00 / 21:00

    Meal duration and finished_time do not affect the next scheduled feed.
    """
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    today = local_now.date()

    # Remove the old finish-based dynamic reminder if it still exists.
    HealthReminder.objects.filter(source_key="meal-next:dynamic").delete()

    # Keep the reminder table tidy without touching manual reminders.
    HealthReminder.objects.filter(
        auto_generated=True,
        reminder_type="meal",
        source_key__startswith="meal-schedule:",
        due_at__lt=now - timedelta(days=2),
    ).delete()

    created_or_updated = 0

    for day in (today, today + timedelta(days=1)):
        for feed_time in FIXED_FEED_TIMES:
            due_at = _aware(day, feed_time)
            source_key = _meal_schedule_source_key(day, feed_time)

            completed_by_meal = MealEntry.objects.filter(
                date=day,
                scheduled_time=feed_time,
            ).exclude(status="missed").exists()
            existing = HealthReminder.objects.filter(source_key=source_key).first()
            completed = completed_by_meal or bool(existing and existing.completed)

            _upsert_auto_reminder(
                source_key,
                {
                    "reminder_type": "meal",
                    "title": f"Γεύμα · {feed_time.strftime('%H:%M')}",
                    "due_at": due_at,
                    "notes": (
                        "Αυτόματη υπενθύμιση σταθερού 3ώρου. "
                        "Η διάρκεια του προηγούμενου γεύματος δεν αλλάζει την επόμενη ώρα. "
                        f"Push {MEAL_NOTIFY_MINUTES_BEFORE} λεπτά πριν."
                    ),
                    "notify_minutes_before": MEAL_NOTIFY_MINUTES_BEFORE,
                    "repeat_if_incomplete_minutes": 0,
                    "active": True,
                    "completed": completed,
                },
            )
            created_or_updated += 1

    return created_or_updated


def sync_low_meal_reminder(meal):
    """
    User-defined separate follow-up rule:
    if consumed amount is 50 ml or less, create a follow-up reminder 1 hour
    after the meal finish time when available. This does NOT change the fixed
    3-hour feeding schedule.
    """
    source_key = f"low-meal:{meal.pk}"

    if meal.consumed_ml is None or meal.consumed_ml > LOW_MEAL_THRESHOLD_ML:
        HealthReminder.objects.filter(source_key=source_key).delete()
        return None

    base_dt = meal_finished_datetime(meal) or meal_start_datetime(meal)
    if base_dt is None:
        return None

    due_at = base_dt + timedelta(minutes=LOW_MEAL_FOLLOWUP_MINUTES)

    return _upsert_auto_reminder(
        source_key,
        {
            "reminder_type": "meal",
            "title": f"Επανέλεγχος γεύματος — ήπιε {meal.consumed_ml} ml",
            "due_at": due_at,
            "notes": (
                f"Αυτόματη υπενθύμιση βάσει του κανόνα ≤ {LOW_MEAL_THRESHOLD_ML} ml. "
                f"Το καταχωρημένο γεύμα ήταν {meal.consumed_ml} ml. "
                f"Υπενθύμιση {LOW_MEAL_FOLLOWUP_MINUTES} λεπτά μετά την ολοκλήρωση. "
                "Δεν μετακινεί το σταθερό 3ωρο."
            ),
            "notify_minutes_before": 0,
            "repeat_if_incomplete_minutes": 0,
            "active": True,
            "completed": False,
        },
    )


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

    meal_count = sync_fixed_meal_schedule_reminders(now=now)

    return {
        "meal_schedule": meal_count,
        "dynamic_meal": 0,
        "appointments": sync_upcoming_appointment_reminders(now=now),
    }
