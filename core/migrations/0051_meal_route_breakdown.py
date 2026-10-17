from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0050_meal_prepared_volume")]

    operations = [
        migrations.AddField(
            model_name="mealentry", name="oral_ml",
            field=models.PositiveIntegerField("Από στόμα (ml)", blank=True, null=True),
        ),
        migrations.AddField(
            model_name="mealentry", name="tube_ml",
            field=models.PositiveIntegerField("Μέσω σωλήνα (ml)", blank=True, null=True),
        ),
        migrations.AddField(
            model_name="mealentry", name="tube_route",
            field=models.CharField(
                "Οδός σίτισης μέσω σωλήνα", max_length=16,
                choices=[("ngt", "Ρινογαστρικός σωλήνας"), ("gastrostomy", "Γαστροστομία")],
                blank=True, default="",
            ),
        ),
    ]
