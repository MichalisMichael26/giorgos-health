from django.db import migrations


def clear_old_meal_reminders(apps, schema_editor):
    HealthReminder = apps.get_model("core", "HealthReminder")

    HealthReminder.objects.filter(
        auto_generated=True,
        reminder_type="meal",
        source_key="meal-next:dynamic",
    ).delete()

    HealthReminder.objects.filter(
        auto_generated=True,
        reminder_type="meal",
        source_key__startswith="meal-schedule:",
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0019_default_fructose_rules"),
    ]

    operations = [
        migrations.RunPython(
            clear_old_meal_reminders,
            migrations.RunPython.noop,
        ),
    ]
