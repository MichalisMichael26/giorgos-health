from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0043_nasogastric_tube"),
    ]

    operations = [
        migrations.AddField(
            model_name="mealentry",
            name="nasogastric_tube_used",
            field=models.BooleanField(default=False, verbose_name="Ρινογαστρικός σωλήνας"),
        ),
    ]
