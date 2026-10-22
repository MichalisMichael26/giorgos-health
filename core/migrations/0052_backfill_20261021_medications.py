"""Backfill parent-reported 21 October doses without inventing administration times."""
from datetime import date
from decimal import Decimal

from django.db import migrations, models


def backfill_21_october_doses(apps, schema_editor):
    ChildProfile = apps.get_model("core", "ChildProfile")
    MedicationEntry = apps.get_model("core", "MedicationEntry")
    MedicationPlan = apps.get_model("core", "MedicationPlan")

    # This is a one-off backfill for this child's record, not default/demo data.
    if not ChildProfile.objects.filter(birth_date=date(2026, 6, 27)).exists():
        return

    vitamin_plans = MedicationPlan.objects.filter(
        name__iexact="Vitamin D", dose=Decimal("400.00"), unit="mg"
    )
    for plan in vitamin_plans:
        plan.unit = "IU"
        plan.unit_confirmation_required = False
        plan.notes = (
            "Μονάδα ημερήσιας δόσης: 400 IU. "
            "Η προηγούμενη καταχώρηση 400 mg ήταν σφάλμα μονάδας και διορθώθηκε στις 22/10/2026."
        )
        plan.save(update_fields=["unit", "unit_confirmation_required", "notes", "updated_at"])

    # Correct only the known 400-unit Vitamin D logging error, preserving the
    # dose/date/time and appending an explicit audit trail in the notes.
    for entry in MedicationEntry.objects.filter(
        name__iexact="Vitamin D", dose=Decimal("400.00"), unit="mg"
    ).iterator():
        entry.unit = "IU"
        audit = "Διόρθωση μονάδας στις 22/10/2026: mg → IU, χωρίς αλλαγή ποσότητας ή ώρας."
        entry.notes = (entry.notes.strip() + "\n" if entry.notes.strip() else "") + audit
        entry.save(update_fields=["unit", "notes", "updated_at"])

    day = date(2026, 10, 21)
    note = (
        "Αναδρομική καταχώρηση 22/10/2026 μετά από αναφορά γονέα "
        "ότι το φάρμακο δόθηκε στις 21/10/2026. "
        "Δεν δηλώθηκε η πραγματική ώρα χορήγησης."
    )
    for name in ("Vitamin D", "Colipro", "Hemafer"):
        plan = MedicationPlan.objects.filter(name__iexact=name, active=True).first()
        if plan is None:
            continue
        if MedicationEntry.objects.filter(date=day, name__iexact=plan.name).exists():
            continue
        MedicationEntry.objects.create(
            date=day,
            time=None,
            name=plan.name,
            dose=plan.dose,
            unit=plan.unit,
            notes=note,
            created_by_id=None,
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0051_meal_route_breakdown")]

    operations = [
        migrations.AlterField(
            model_name="medicationentry",
            name="time",
            field=models.TimeField("Ώρα", blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="medicationentry",
            name="unit",
            field=models.CharField(
                "Μονάδα", max_length=20, default="ml",
                choices=[
                    ("ml", "ml"), ("mg", "mg"), ("IU", "IU"), ("g", "g"),
                    ("drops", "Σταγόνες"), ("scoops", "Κουταλάκια"),
                    ("dose", "Δόση"), ("other", "Άλλο"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="medicationplan",
            name="unit",
            field=models.CharField(
                "Μονάδα", max_length=20, default="ml",
                choices=[
                    ("ml", "ml"), ("mg", "mg"), ("IU", "IU"), ("g", "g"),
                    ("drops", "Σταγόνες"), ("scoops", "Κουταλάκια"),
                    ("dose", "Δόση"), ("other", "Άλλο"),
                ],
            ),
        ),
        migrations.RunPython(backfill_21_october_doses, migrations.RunPython.noop),
    ]
