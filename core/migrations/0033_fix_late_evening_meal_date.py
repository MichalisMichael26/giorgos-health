from datetime import time, timedelta
from zoneinfo import ZoneInfo

from django.db import migrations


NICOSIA = ZoneInfo("Europe/Nicosia")


def fix_late_evening_meals_shifted_to_next_day(apps, schema_editor):
    MealEntry = apps.get_model("core", "MealEntry")

    for meal in MealEntry.objects.filter(actual_time__isnull=False).iterator():
        if not meal.created_at:
            continue

        created_local = meal.created_at.astimezone(NICOSIA)
        created_date = created_local.date()

        # The old "new meal" defaults could roll the date to tomorrow late at
        # night. Only repair records that match that exact shape.
        if meal.date != created_date + timedelta(days=1):
            continue
        if meal.scheduled_time != meal.actual_time:
            continue
        if created_local.time() < time(20, 0):
            continue

        created_minutes = created_local.hour * 60 + created_local.minute
        actual_minutes = meal.actual_time.hour * 60 + meal.actual_time.minute
        minutes_after_meal_start = created_minutes - actual_minutes

        # A meal entered shortly after it actually started belongs to the local
        # creation day, not tomorrow.
        if 0 <= minutes_after_meal_start <= 180:
            meal.date = created_date
            meal.save(update_fields=["date"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0032_clear_auto_symptom_notes"),
    ]

    operations = [
        migrations.RunPython(
            fix_late_evening_meals_shifted_to_next_day,
            migrations.RunPython.noop,
        ),
    ]
