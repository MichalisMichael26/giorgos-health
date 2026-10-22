"""Update Giorgos's daily Hemafer plan from 22 October 2026.

Only the active daily plan changes; previously administered doses remain as logged.
"""
from decimal import Decimal

from django.db import migrations


def update_hemafer_plan(apps, schema_editor):
    MedicationPlan = apps.get_model("core", "MedicationPlan")
    for plan in MedicationPlan.objects.filter(active=True, name__iexact="Hemafer"):
        if plan.unit != "ml":
            continue
        if plan.dose == Decimal("3.50"):
            continue
        plan.dose = Decimal("3.50")
        change_note = (
            "Αλλαγή ημερήσιου πλάνου από 22/10/2026: "
            "3,5 ml Hemafer μία φορά την ημέρα, κατόπιν οδηγίας γονέα. "
            "Οι προηγούμενες πραγματικές καταχωρίσεις παραμένουν αμετάβλητες."
        )
        if change_note not in (plan.notes or ""):
            plan.notes = ((plan.notes or "").strip() + "\n" + change_note).strip()
        plan.save(update_fields=["dose", "notes", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0052_backfill_20261021_medications"),
    ]

    operations = [
        migrations.RunPython(update_hemafer_plan, migrations.RunPython.noop),
    ]
