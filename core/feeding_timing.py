from datetime import datetime, time, timedelta

from django.db import OperationalError, ProgrammingError
from django.utils import timezone

from .models import ChildProfile, MealEntry


DEFAULT_FEEDING_START_TIME = time(7, 30)
DEFAULT_FEEDING_INTERVAL_MINUTES = 180
DEFAULT_MEAL_NOTIFY_MINUTES_BEFORE = 12


def build_feed_times(start_time=DEFAULT_FEEDING_START_TIME, interval_minutes=DEFAULT_FEEDING_INTERVAL_MINUTES):
    """
    Build a repeating 24-hour fixed-clock schedule.

    The interval must divide 24 hours exactly so that the same clock schedule
    repeats every day without a hidden shorter/longer gap at midnight.
    """
    start_time = start_time or DEFAULT_FEEDING_START_TIME
    try:
        interval_minutes = int(interval_minutes or DEFAULT_FEEDING_INTERVAL_MINUTES)
    except (TypeError, ValueError):
        interval_minutes = DEFAULT_FEEDING_INTERVAL_MINUTES

    if interval_minutes <= 0 or 1440 % interval_minutes != 0:
        interval_minutes = DEFAULT_FEEDING_INTERVAL_MINUTES

    start_minutes = start_time.hour * 60 + start_time.minute
    slots = 1440 // interval_minutes

    values = []
    for index in range(slots):
        minute_of_day = (start_minutes + index * interval_minutes) % 1440
        values.append(time(minute_of_day // 60, minute_of_day % 60))

    # Day views/reminders need chronological clock order, regardless of the
    # configured anchor time.
    return sorted(values)


# Backwards-compatible defaults. Runtime scheduling uses current_feed_times().
FIXED_FEED_TIMES = build_feed_times()
REFERENCE_FEED_TIMES = FIXED_FEED_TIMES


def _profile_or_none(profile=None):
    if profile is not None:
        return profile
    try:
        return ChildProfile.objects.first()
    except (OperationalError, ProgrammingError):
        return None


def feeding_interval_minutes(profile=None):
    profile = _profile_or_none(profile)
    try:
        value = int(getattr(profile, "feeding_interval_minutes", 0) or 0)
    except (TypeError, ValueError):
        value = 0

    if value <= 0 or 1440 % value != 0:
        return DEFAULT_FEEDING_INTERVAL_MINUTES
    return value


def feeding_schedule_start_time(profile=None):
    profile = _profile_or_none(profile)
    value = getattr(profile, "feeding_schedule_start_time", None)
    return value or DEFAULT_FEEDING_START_TIME


def meal_notify_minutes_before(profile=None):
    profile = _profile_or_none(profile)
    try:
        value = int(getattr(profile, "meal_notify_minutes_before", DEFAULT_MEAL_NOTIFY_MINUTES_BEFORE))
    except (TypeError, ValueError):
        value = DEFAULT_MEAL_NOTIFY_MINUTES_BEFORE
    return max(0, min(value, 180))


def current_feed_times(profile=None):
    return build_feed_times(
        feeding_schedule_start_time(profile),
        feeding_interval_minutes(profile),
    )


def schedule_settings(profile=None):
    return {
        "start_time": feeding_schedule_start_time(profile),
        "interval_minutes": feeding_interval_minutes(profile),
        "notify_minutes_before": meal_notify_minutes_before(profile),
        "times": current_feed_times(profile),
    }


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


def next_fixed_meal_due(now=None, profile=None):
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    day = local_now.date()
    feed_times = current_feed_times(profile)

    for feed_time in feed_times:
        candidate = _aware(day, feed_time)
        if candidate >= local_now:
            return candidate

    return _aware(day + timedelta(days=1), feed_times[0])


def suggested_meal_datetime(now=None, profile=None):
    """
    For a new meal form, prefer the most recent configured fixed slot for up to
    90 minutes if it has not been logged yet. Otherwise suggest the next slot.
    """
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    day = local_now.date()
    feed_times = current_feed_times(profile)

    previous_candidate = None
    for feed_time in feed_times:
        candidate = _aware(day, feed_time)
        if candidate <= local_now:
            previous_candidate = candidate
        else:
            break

    if previous_candidate is None:
        previous_candidate = _aware(day - timedelta(days=1), feed_times[-1])

    if local_now - previous_candidate <= timedelta(minutes=90):
        local_candidate = timezone.localtime(previous_candidate)
        already_logged = MealEntry.objects.filter(
            date=local_candidate.date(),
            scheduled_time=local_candidate.time().replace(tzinfo=None, second=0, microsecond=0),
        ).exclude(status="missed").exists()

        if not already_logged:
            return previous_candidate

    return next_fixed_meal_due(now, profile=profile)


def next_meal_due(profile=None, now=None):
    """
    Backwards-compatible signature. The due time is determined by the editable
    fixed-clock schedule, never by the previous meal's finish time.
    """
    now = now or timezone.now()
    due_at = next_fixed_meal_due(now, profile=profile)
    last_meal, last_started_at = latest_started_meal(now)
    return due_at, last_meal, last_started_at


def next_reference_due(now_local=None):
    if now_local is None:
        return next_fixed_meal_due()
    return next_fixed_meal_due(now_local)
