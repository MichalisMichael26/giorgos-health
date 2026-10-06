import os
from decimal import Decimal, InvalidOperation

from django.db import migrations, models


def _text(name):
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else None


def _decimal(name):
    value = _text(name)
    if value is None:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def apply_maxijul_5g_correction(apps, schema_editor):
    ChildProfile = apps.get_model("core", "ChildProfile")
    MealEntry = apps.get_model("core", "MealEntry")

    grams = _decimal("GIORGOS_MAXIJUL_SCOOP_GRAMS") or Decimal("5.00")
    feeding_plan = _text("GIORGOS_FEEDING_PLAN")

    values = {
        "maxijul_scoop_grams": grams,
        "planned_maxijul_scoops_per_feed": Decimal("1.00"),
    }
    if feeding_plan:
        values["current_feeding_plan"] = feeding_plan

    ChildProfile.objects.all().update(**values)

    # Normalize the common historical value without changing the recorded quantity.
    for meal in MealEntry.objects.exclude(supplement="").iterator():
        raw = (meal.supplement or "").strip().replace(",", ".")
        if raw in {"1", "1.0", "1.00", "1 scoop", "1 κουταλιά"}:
            meal.supplement = "1 κουταλιά (5 g)"
            meal.save(update_fields=["supplement"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0040_refresh_private_profile_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mealentry",
            name="supplement",
            field=models.CharField(
                blank=True,
                max_length=120,
                verbose_name="Maxijul (κουταλιές — 1 κουταλιά = 5 g)",
            ),
        ),
        migrations.AlterField(
            model_name="childprofile",
            name="planned_maxijul_scoops_per_feed",
            field=models.DecimalField(
                decimal_places=2,
                default=1,
                max_digits=5,
                verbose_name="Προγραμματισμένες κουταλιές Maxijul / γεύμα",
            ),
        ),
        migrations.AlterField(
            model_name="childprofile",
            name="maxijul_scoop_grams",
            field=models.DecimalField(
                decimal_places=2,
                default=5.0,
                help_text="1 κουταλιά Maxijul = 5 g στο τρέχον πλάνο.",
                max_digits=5,
                verbose_name="Maxijul — γραμμάρια ανά κουταλιά",
            ),
        ),
        migrations.RunPython(apply_maxijul_5g_correction, migrations.RunPython.noop),
    ]
