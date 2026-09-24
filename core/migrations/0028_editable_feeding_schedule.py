from datetime import time

from django.db import migrations, models


def configure_current_feeding_schedule(apps, schema_editor):
    ChildProfile = apps.get_model("core", "ChildProfile")
    HealthReminder = apps.get_model("core", "HealthReminder")

    ChildProfile.objects.all().update(
        feeding_schedule_start_time=time(7, 30),
        feeding_interval_minutes=180,
        meal_notify_minutes_before=12,
    )

    # Remove all generated fixed meal reminders from the previous clock schedule.
    # The scheduler / settings page will recreate only the current valid rows.
    HealthReminder.objects.filter(
        auto_generated=True,
        reminder_type="meal",
        source_key__startswith="meal-schedule:",
    ).delete()
    HealthReminder.objects.filter(source_key="meal-next:dynamic").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0027_clear_stale_meal_schedule_reminders"),
    ]

    operations = [
        migrations.AddField(
            model_name="childprofile",
            name="feeding_schedule_start_time",
            field=models.TimeField(
                default=time(7, 30),
                help_text="Η βασική ώρα από την οποία δημιουργείται το σταθερό ημερήσιο πρόγραμμα.",
                verbose_name="Ώρα εκκίνησης προγράμματος γευμάτων",
            ),
        ),
        migrations.AlterField(
            model_name="childprofile",
            name="feeding_interval_minutes",
            field=models.PositiveSmallIntegerField(
                default=180,
                help_text="Χρησιμοποιείται για το σταθερό ωράριο γευμάτων και δεν εξαρτάται από τη διάρκεια του προηγούμενου γεύματος.",
                verbose_name="Διάστημα μεταξύ γευμάτων (λεπτά)",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="meal_notify_minutes_before",
            field=models.PositiveSmallIntegerField(
                default=12,
                help_text="Πόσα λεπτά πριν από κάθε προγραμματισμένο γεύμα θα έρχεται push notification.",
                verbose_name="Ειδοποίηση γεύματος (λεπτά πριν)",
            ),
        ),
        migrations.RunPython(
            configure_current_feeding_schedule,
            migrations.RunPython.noop,
        ),
    ]
