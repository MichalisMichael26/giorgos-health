from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_mealentry_remaining_ml"),
    ]

    operations = [
        migrations.AddField(
            model_name="diaperentry",
            name="possible_diarrhea",
            field=models.BooleanField(
                default=False,
                verbose_name="Πιθανή διάρροια",
            ),
        ),
    ]
