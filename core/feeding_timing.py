from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import MealEntry


FIXED_FEED_TIMES = [
    time(0, 30),
    time(3, 30),
    time(6, 30),
    time(9, 30),
    time(12, 30),
    time(15, 30),
    time(18, 30),
    time(21, 30),
]

# Backwards-compatible alias used in a few views/templates.
REFERENCE_FEED_TIMES = FIXED_FEED_TIMES

DEFAULT_FEEDING_INTERVAL_MINUTES = 180


def _aware(local_date, local_time):
    naive = datetime.combine(local_date, local_time)
    return timezone.make_aware(naive, timezone.get_current_timezone())


def meal_start_datetime(meal):
    start_time = meal.actual_time or meal.scheduled_time
    if not start_time:
        return None
    return _aware(meal.date, start_time)


def meal_finished_datetime(meal):
    if not meal.finished_time:
        return None

    finish_date = meal.date
    start_time = meal.actual_time or meal.scheduled_time

    if start_time and meal.finished_time < start_time:
        finish_date = finish_date + timedelta(days=1)

    return _aware(finish_date, meal.finished_time)


def feeding_interval_minutes(profile=None):
    # The current pediatrician-directed schedule is fixed every 3 hours.
    # Kept for backwards compatibility with older code/data.
    return DEFAULT_FEEDING_INTERVAL_MINUTES


def format_interval(minutes):
    minutes = int(minutes or 0)
    hours, remainder = divmod(minutes, 60)
    if hours and remainder:
        return f"{hours}ω {remainder}λ"
    if hours:
        return f"{hours} ώρες" if hours != 1 else "1 ώρα"
    return f"{remainder} λεπτά"


def recent_meals(limit=80):
    return list(
        MealEntry.objects.exclude(status="missed")
        .order_by("-date", "-scheduled_time", "-pk")[:limit]
    )


def latest_started_meal(now=None):
    now = now or timezone.now()
    candidates = []
    for meal in recent_meals():
        started_at = meal_start_datetime(meal)
        if started_at and started_at <= now + timedelta(minutes=10):
            candidates.append((started_at, meal))
    if not candidates:
        return None, None
    started_at, meal = max(candidates, key=lambda pair: pair[0])
    return meal, started_at


def latest_finished_meal(now=None):
    now = now or timezone.now()
    candidates = []
    for meal in recent_meals():
        finished_at = meal_finished_datetime(meal)
        if finished_at is not None and finished_at <= now:
            candidates.append((finished_at, meal))
    if not candidates:
        return None, None
    finished_at, meal = max(candidates, key=lambda pair: pair[0])
    return meal, finished_at


def next_fixed_meal_due(now=None):
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    day = local_now.date()

    for feed_time in FIXED_FEED_TIMES:
        candidate = _aware(day, feed_time)
        if candidate >= local_now:
            return candidate

    return _aware(day + timedelta(days=1), FIXED_FEED_TIMES[0])


def suggested_meal_datetime(now=None):
    """
    For a new meal form, prefer the most recent fixed slot for up to 90 minutes
    if it has not been logged yet. Otherwise suggest the next fixed slot.

    Example: at 15:45 an unlogged 15:30 meal opens as 15:30, while the dashboard
    countdown still points to 18:30.
    """
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    day = local_now.date()

    previous_candidate = None
    for feed_time in FIXED_FEED_TIMES:
        candidate = _aware(day, feed_time)
        if candidate <= local_now:
            previous_candidate = candidate
        else:
            break

    if previous_candidate is None:
        previous_candidate = _aware(day - timedelta(days=1), FIXED_FEED_TIMES[-1])

    if local_now - previous_candidate <= timedelta(minutes=90):
        local_candidate = timezone.localtime(previous_candidate)
        already_logged = MealEntry.objects.filter(
            date=local_candidate.date(),
            scheduled_time=local_candidate.time().replace(tzinfo=None, second=0, microsecond=0),
        ).exclude(status="missed").exists()

        if not already_logged:
            return previous_candidate

    return next_fixed_meal_due(now)


def next_meal_due(profile=None, now=None):
    """
    Backwards-compatible signature. The due time is now determined only by the
    fixed clock schedule, never by the previous meal's finish time.
    """
    now = now or timezone.now()
    due_at = next_fixed_meal_due(now)
    last_meal, last_started_at = latest_started_meal(now)
    return due_at, last_meal, last_started_at


def next_reference_due(now_local=None):
    if now_local is None:
        return next_fixed_meal_due()
    return next_fixed_meal_due(now_local)
