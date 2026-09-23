from datetime import time

from django.db import migrations, models


def configure_daily_medication_reminders(apps, schema_editor):
    MedicationPlan = apps.get_model("core", "MedicationPlan")
    HealthReminder = apps.get_model("core", "HealthReminder")

    settings = {
        "Vitamin D": time(8, 0),
        "Colipro": time(8, 0),
        "Hemafer": time(15, 0),
    }

    for name, reminder_time in settings.items():
        item = MedicationPlan.objects.filter(name__iexact=name).order_by("pk").first()
        if not item:
            continue
        item.reminder_enabled = True
        item.reminder_time = reminder_time
        item.save(update_fields=["reminder_enabled", "reminder_time", "updated_at"])

    # Clear any previously generated medication-plan reminders so they can be
    # recreated using the configured schedule after deploy.
    HealthReminder.objects.filter(
        auto_generated=True,
        reminder_type="medication",
        source_key__startswith="med-plan:",
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_current_daily_medications"),
    ]

    operations = [
        migrations.AddField(
            model_name="medicationplan",
            name="reminder_enabled",
            field=models.BooleanField(default=False, verbose_name="Καθημερινή υπενθύμιση"),
        ),
        migrations.AddField(
            model_name="medicationplan",
            name="reminder_time",
            field=models.TimeField(blank=True, null=True, verbose_name="Ώρα υπενθύμισης"),
        ),
        migrations.RunPython(
            configure_daily_medication_reminders,
            migrations.RunPython.noop,
        ),
    ]
