from django.db import migrations, models


def backfill_remaining_ml(apps, schema_editor):
    MealEntry = apps.get_model("core", "MealEntry")
    for meal in MealEntry.objects.filter(
        offered_ml__isnull=False,
        consumed_ml__isnull=False,
        remaining_ml__isnull=True,
    ):
        if meal.offered_ml >= meal.consumed_ml:
            meal.remaining_ml = meal.offered_ml - meal.consumed_ml
            meal.save(update_fields=["remaining_ml"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_childprofile_known_allergies"),
    ]

    operations = [
        migrations.AddField(
            model_name="mealentry",
            name="remaining_ml",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Έμεινε (ml)",
            ),
        ),
        migrations.RunPython(
            backfill_remaining_ml,
            migrations.RunPython.noop,
        ),
    ]
