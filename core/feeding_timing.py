from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import ChildProfile, MealEntry


REFERENCE_FEED_TIMES = [
    time(1, 30),
    time(4, 30),
    time(7, 30),
    time(10, 30),
    time(13, 30),
    time(16, 30),
    time(19, 30),
    time(22, 30),
]

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

    # If a feed crosses midnight, a finish clock time smaller than its start
    # belongs to the following calendar day.
    if start_time and meal.finished_time < start_time:
        finish_date = finish_date + timedelta(days=1)

    return _aware(finish_date, meal.finished_time)


def feeding_interval_minutes(profile=None):
    if profile is None:
        profile = ChildProfile.objects.first()
    value = getattr(profile, "feeding_interval_minutes", None) if profile else None
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = DEFAULT_FEEDING_INTERVAL_MINUTES
    return max(value, 1)


def recent_meals(limit=80):
    return list(
        MealEntry.objects.exclude(status="missed")
        .order_by("-date", "-scheduled_time", "-pk")[:limit]
    )


def latest_finished_meal(now=None):
    candidates = []
    now = now or timezone.now()
    for meal in recent_meals():
        finished_at = meal_finished_datetime(meal)
        if finished_at is not None and finished_at <= now:
            candidates.append((finished_at, meal))

    if not candidates:
        return None, None

    finished_at, meal = max(candidates, key=lambda pair: pair[0])
    return meal, finished_at


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


def meal_after_datetime(moment, now=None):
    now = now or timezone.now()
    matches = []
    for meal in recent_meals():
        started_at = meal_start_datetime(meal)
        if started_at and moment < started_at <= now + timedelta(minutes=10):
            matches.append((started_at, meal))
    if not matches:
        return None, None
    return min(matches, key=lambda pair: pair[0])[1], min(matches, key=lambda pair: pair[0])[0]


def next_meal_due(profile=None, now=None):
    now = now or timezone.now()
    meal, finished_at = latest_finished_meal(now=now)

    if not meal or not finished_at:
        latest_started, _ = latest_started_meal(now=now)
        if latest_started is not None and meal_finished_datetime(latest_started) is None:
            # A meal is currently/incompletely logged. The next interval cannot
            # start until its finish time is entered.
            return None, latest_started, None
        return None, None, None

    # If another feed has already started after that finish but has not yet
    # been completed/logged, do not keep reminding for the feed already begun.
    newer_meal, newer_started_at = meal_after_datetime(finished_at, now=now)
    if newer_meal is not None:
        newer_finished_at = meal_finished_datetime(newer_meal)
        if newer_finished_at is None:
            return None, newer_meal, None

    interval = feeding_interval_minutes(profile)
    return finished_at + timedelta(minutes=interval), meal, finished_at


def next_reference_due(now_local=None):
    now_local = now_local or timezone.localtime()
    current_time = now_local.time().replace(tzinfo=None, second=0, microsecond=0)
    day = now_local.date()

    for reference_time in REFERENCE_FEED_TIMES:
        if reference_time >= current_time:
            return _aware(day, reference_time)

    return _aware(day + timedelta(days=1), REFERENCE_FEED_TIMES[0])


def format_interval(minutes):
    minutes = int(minutes or 0)
    hours, remainder = divmod(minutes, 60)
    if hours and remainder:
        return f"{hours}ω {remainder}λ"
    if hours:
        return f"{hours} ώρες" if hours != 1 else "1 ώρα"
    return f"{remainder} λεπτά"
