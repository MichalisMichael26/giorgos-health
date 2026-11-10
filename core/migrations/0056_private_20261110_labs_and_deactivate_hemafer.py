"""Import a confidential 2026-11-10 lab batch and deactivate Hemafer in active tracking.

The laboratory observations are loaded from a private Render environment
variable and are not published in the repository. Historical medication
administrations remain unchanged. The change to the active app plan is
made at the parent's request; it is not a prescribing instruction.
"""
import json
import os
from datetime import date, time
from decimal import Decimal, InvalidOperation

from django.db import migrations


PAYLOAD_ENV = "GIORGOS_LABS_IMPORT_20261110_JSON"
EXPECTED_DATE = date(2026, 11, 10)
EXPECTED_COUNT = 36
EXPECTED_TIMES = {time(10, 13), time(10, 14)}


def apply_parent_requested_update(apps, schema_editor):
    raw = os.environ.get(PAYLOAD_ENV, "")
    if not raw.strip():
        raise ValueError("Required private 2026-11-10 lab payload missing; refusing incomplete update")

    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get("date") != EXPECTED_DATE.isoformat():
        raise ValueError("Invalid date for private lab batch")

    observations = payload.get("records")
    if not isinstance(observations, list) or len(observations) != EXPECTED_COUNT:
        raise ValueError("Unexpected number of private laboratory observations")

    lab = payload.get("laboratory", "")
    if not isinstance(lab, str) or not lab or len(lab) > 180:
        raise ValueError("Invalid laboratory identifier")

    # Validate every record before writing any clinical data.
    normalized = []
    keys = set()
    for row in observations:
        if not isinstance(row, dict):
            raise ValueError("Malformed laboratory observation")
        name = row.get("name")
        unit = row.get("unit", "")
        if not isinstance(name, str) or not name.strip() or len(name) > 160:
            raise ValueError("Invalid laboratory test name")
        if not isinstance(unit, str) or len(unit) > 80:
            raise ValueError("Invalid laboratory result unit")
        clock = time.fromisoformat(row["time"])
        if clock not in EXPECTED_TIMES:
            raise ValueError("Unexpected collection time")
        key = (clock, name)
        if key in keys:
            raise ValueError("Duplicate laboratory test/time in batch")
        keys.add(key)
        try:
            val = Decimal(str(row["value"]))
            low = Decimal(str(row["min"])) if row.get("min") is not None else None
            high = Decimal(str(row["max"])) if row.get("max") is not None else None
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("Invalid laboratory numeric value") from exc
        if any(v is not None and not v.is_finite() for v in (val, low, high)):
            raise ValueError("Nonfinite laboratory numeric value")
        if low is not None and high is not None and low > high:
            raise ValueError("Invalid laboratory reference range")
        normalized.append((clock, name, val, unit, low, high))

    LabResult = apps.get_model("core", "LabResult")
    MedicationPlan = apps.get_model("core", "MedicationPlan")
    HealthReminder = apps.get_model("core", "HealthReminder")
    alias = schema_editor.connection.alias
    added = 0
    already_present = 0

    for clock, name, val, unit, low, high in normalized:
        _, created = LabResult.objects.using(alias).get_or_create(
            date=EXPECTED_DATE,
            time=clock,
            test_name=name,
            defaults={
                "value": val,
                "unit": unit,
                "reference_min": low,
                "reference_max": high,
                "laboratory": lab,
                "notes": "Πηγή: επίσημα εργαστηριακά αποτελέσματα 10/11/2026.",
            },
        )
        added += int(created)
        already_present += int(not created)

    modified_plans = 0
    reminders_disabled = 0
    for plan in MedicationPlan.objects.using(alias).filter(name__iexact="Hemafer"):
        plan.active = False
        plan.reminder_enabled = False
        note = (
            "Αφαιρέθηκε από το ενεργό πλάνο της εφαρμογής στις 10/11/2026 "
            "κατόπιν αιτήματος γονέα. Οι παλιές καταχωρίσεις διατηρούνται."
        )
        if note not in (plan.notes or ""):
            plan.notes = ((plan.notes or "").strip() + "\n" + note).strip()
        plan.save(update_fields=["active", "reminder_enabled", "notes", "updated_at"])
        modified_plans += 1

        reminders_disabled += HealthReminder.objects.using(alias).filter(
            auto_generated=True,
            reminder_type="medication",
            source_key__startswith=f"med-plan:{plan.pk}:",
        ).update(active=False)

    print(
        f"Private labs 2026-11-10: added={added}, already_present={already_present}; "
        f"medication_plans_deactivated={modified_plans}; reminders_disabled={reminders_disabled}"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0055_merge_colipro_private_labs"),
    ]
    operations = [
        migrations.RunPython(apply_parent_requested_update, migrations.RunPython.noop),
    ]
