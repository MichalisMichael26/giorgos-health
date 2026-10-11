from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0049_correct_formula_nutrition_text")]
    operations = [
        migrations.AddField(
            model_name="mealentry",
            name="prepared_volume_ml",
            field=models.PositiveIntegerField(
                blank=True, null=True,
                verbose_name="Τελικός όγκος παρασκευής (ml)",
                help_text="Τελικός όγκος όλου του παρασκευασμένου γάλακτος, όχι μόνο όσα προσφέρθηκαν.",
            ),
        ),
    ]
