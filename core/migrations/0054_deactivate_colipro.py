"""Remove Colipro from the active app medication plan at parent request.

Keep past medication administrations and reminder history intact.
This changes app tracking only; it is not a clinical instruction.
"""
from django.db import migrations


def deactivate_colipro(apps, schema_editor):
    MedicationPlan = apps.get_model("core", "MedicationPlan")
    HealthReminder = apps.get_model("core", "HealthReminder")

    for plan in MedicationPlan.objects.filter(name__iexact="Colipro"):
        plan.active = False
        plan.reminder_enabled = False
        note = (
            "Αφαιρέθηκε από το ενεργό πλάνο της εφαρμογής στις 02/11/2026 "
            "κατόπιν αιτήματος γονέα. Οι παλιές καταχωρίσεις παραμένουν."
        )
        if note not in (plan.notes or ""):
            plan.notes = ((plan.notes or "").strip() + "\n" + note).strip()
        plan.save(update_fields=["active", "reminder_enabled", "notes", "updated_at"])

        # Existing reminders must no longer be pushed or shown as pending.
        # Keep their records for audit/history; do not touch user-created reminders.
        HealthReminder.objects.filter(
            auto_generated=True,
            reminder_type="medication",
            source_key__startswith=f"med-plan:{plan.pk}:",
        ).update(active=False)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0053_hemafer_35ml_from_20261022"),
    ]

    operations = [
        migrations.RunPython(deactivate_colipro, migrations.RunPython.noop),
    ]
