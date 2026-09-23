from decimal import Decimal

from django.db import migrations, models


CURRENT_MEDICATIONS = [
    {
        "name": "Vitamin D",
        "dose": Decimal("400.00"),
        "unit": "mg",
        "frequency": "1 φορά/ημέρα",
        "notes": (
            "Μονάδα καταχωρήθηκε όπως δόθηκε από τον γονέα. "
            "Χρειάζεται επιβεβαίωση της μονάδας πριν χρησιμοποιηθεί ως επαληθευμένη ιατρική πληροφορία."
        ),
        "unit_confirmation_required": True,
        "active": True,
    },
    {
        "name": "Colipro",
        "dose": Decimal("5.00"),
        "unit": "drops",
        "frequency": "1 φορά/ημέρα",
        "notes": "",
        "unit_confirmation_required": False,
        "active": True,
    },
    {
        "name": "Hemafer",
        "dose": Decimal("2.50"),
        "unit": "ml",
        "frequency": "1 φορά/ημέρα",
        "notes": "",
        "unit_confirmation_required": False,
        "active": True,
    },
]


def seed_current_medications(apps, schema_editor):
    MedicationPlan = apps.get_model("core", "MedicationPlan")

    for row in CURRENT_MEDICATIONS:
        item = MedicationPlan.objects.filter(name__iexact=row["name"]).order_by("pk").first()
        if item is None:
            MedicationPlan.objects.create(**row)
            continue

        for field, value in row.items():
            setattr(item, field, value)
        item.save(
            update_fields=[
                "name",
                "dose",
                "unit",
                "frequency",
                "notes",
                "unit_confirmation_required",
                "active",
                "updated_at",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_shift_feeds_to_half_hour_and_seed_2309_labs"),
    ]

    operations = [
        migrations.CreateModel(
            name="MedicationPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, verbose_name="Φάρμακο / συμπλήρωμα")),
                ("dose", models.DecimalField(decimal_places=2, max_digits=8, verbose_name="Ποσότητα")),
                (
                    "unit",
                    models.CharField(
                        choices=[
                            ("ml", "ml"),
                            ("mg", "mg"),
                            ("g", "g"),
                            ("drops", "Σταγόνες"),
                            ("scoops", "Κουταλάκια"),
                            ("dose", "Δόση"),
                            ("other", "Άλλο"),
                        ],
                        default="ml",
                        max_length=20,
                        verbose_name="Μονάδα",
                    ),
                ),
                ("frequency", models.CharField(default="1 φορά/ημέρα", max_length=120, verbose_name="Συχνότητα")),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                (
                    "unit_confirmation_required",
                    models.BooleanField(default=False, verbose_name="Χρειάζεται επιβεβαίωση μονάδας"),
                ),
                ("active", models.BooleanField(default=True, verbose_name="Ενεργό")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.RunPython(seed_current_medications, migrations.RunPython.noop),
    ]
