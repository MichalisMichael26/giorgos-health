from django.db import migrations


def clear_stale_fixed_meal_reminders(apps, schema_editor):
    HealthReminder = apps.get_model("core", "HealthReminder")

    # One-time cleanup on deploy. The scheduler immediately recreates the valid
    # current :30 schedule using the current application code.
    HealthReminder.objects.filter(
        auto_generated=True,
        reminder_type="meal",
        source_key__startswith="meal-schedule:",
    ).delete()

    # Legacy finish-based reminder from the older implementation.
    HealthReminder.objects.filter(source_key="meal-next:dynamic").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0026_backfill_access_from_audit_7days"),
    ]

    operations = [
        migrations.RunPython(
            clear_stale_fixed_meal_reminders,
            migrations.RunPython.noop,
        ),
    ]
