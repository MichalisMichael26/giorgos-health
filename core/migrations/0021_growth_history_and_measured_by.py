from decimal import Decimal
from datetime import date

from django.db import migrations, models


GROWTH_ROWS = [
    {
        "date": date(2026, 8, 27),
        "weight_kg": Decimal("5.320"),
        "length_cm": Decimal("59.00"),
        "head_cm": Decimal("39.20"),
        "measured_by": "ΣΑΒΒΑΣ ΣΑΒΒΑ / SAVVAS SAVVA",
    },
    {
        "date": date(2026, 8, 11),
        "weight_kg": Decimal("4.850"),
        "length_cm": Decimal("58.00"),
        "head_cm": Decimal("38.30"),
        "measured_by": "ΣΑΒΒΑΣ ΣΑΒΒΑ / SAVVAS SAVVA",
    },
    {
        "date": date(2026, 7, 28),
        "weight_kg": Decimal("4.210"),
        "length_cm": Decimal("56.00"),
        "head_cm": Decimal("37.40"),
        "measured_by": "ΣΑΒΒΑΣ ΣΑΒΒΑ / SAVVAS SAVVA",
    },
    {
        "date": date(2026, 7, 22),
        "weight_kg": Decimal("3.830"),
        "length_cm": Decimal("54.00"),
        "head_cm": Decimal("36.80"),
        "measured_by": "ΣΑΒΒΑΣ ΣΑΒΒΑ / SAVVAS SAVVA",
    },
    {
        "date": date(2026, 7, 15),
        "weight_kg": Decimal("3.630"),
        "length_cm": Decimal("52.00"),
        "head_cm": Decimal("36.00"),
        "measured_by": "",
    },
]


def seed_growth_history(apps, schema_editor):
    GrowthMeasurement = apps.get_model("core", "GrowthMeasurement")

    for row in GROWTH_ROWS:
        item = GrowthMeasurement.objects.filter(date=row["date"]).order_by("pk").first()
        if item is None:
            GrowthMeasurement.objects.create(
                date=row["date"],
                weight_kg=row["weight_kg"],
                length_cm=row["length_cm"],
                head_cm=row["head_cm"],
                measured_by=row["measured_by"],
                notes="",
            )
            continue

        item.weight_kg = row["weight_kg"]
        item.length_cm = row["length_cm"]
        item.head_cm = row["head_cm"]
        item.measured_by = row["measured_by"]
        item.save(
            update_fields=[
                "weight_kg",
                "length_cm",
                "head_cm",
                "measured_by",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0020_fixed_three_hour_schedule"),
    ]

    operations = [
        migrations.AddField(
            model_name="growthmeasurement",
            name="measured_by",
            field=models.CharField(
                blank=True,
                max_length=180,
                verbose_name="Μετρήθηκε από",
            ),
        ),
        migrations.RunPython(
            seed_growth_history,
            migrations.RunPython.noop,
        ),
    ]
