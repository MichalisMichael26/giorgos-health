from django.db import migrations, models


def remove_old_fixed_meal_reminders(apps, schema_editor):
    HealthReminder = apps.get_model("core", "HealthReminder")
    HealthReminder.objects.filter(
        auto_generated=True,
        source_key__startswith="meal-schedule:",
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_diaperentry_possible_diarrhea"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mealentry",
            name="actual_time",
            field=models.TimeField(
                blank=True,
                null=True,
                verbose_name="Ώρα έναρξης",
            ),
        ),
        migrations.AddField(
            model_name="mealentry",
            name="finished_time",
            field=models.TimeField(
                blank=True,
                null=True,
                verbose_name="Ώρα ολοκλήρωσης",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="feeding_interval_minutes",
            field=models.PositiveSmallIntegerField(
                default=180,
                help_text="Το επόμενο γεύμα υπολογίζεται από την ώρα ολοκλήρωσης του προηγούμενου.",
                verbose_name="Διάστημα επόμενου γεύματος από το τέλος (λεπτά)",
            ),
        ),
        migrations.RunPython(
            remove_old_fixed_meal_reminders,
            migrations.RunPython.noop,
        ),
    ]
