"""Import a dated lab batch from private Render environment, not from public source.

Payload contains confidential clinical observations, so raw values are NOT
committed to this repository. This migration is idempotent by date/time/name
and never modifies observations already entered in the application.
"""
import json
import os
from datetime import date, time
from decimal import Decimal, InvalidOperation

from django.db import migrations


PAYLOAD_ENV = "GIORGOS_LABS_IMPORT_20261027_JSON"
EXPECTED_DATE = date(2026, 10, 27)
EXPECTED_ROWS = 51


def import_private_lab_batch(apps, schema_editor):
    payload = os.environ.get(PAYLOAD_ENV, "")
    if not payload.strip():
        print("2026-10-27 private lab import payload absent; no clinical data changed")
        return

    batch = json.loads(payload)
    if batch.get("date") != EXPECTED_DATE.isoformat():
        raise ValueError("Private lab batch has unexpected date")
    rows = batch.get("records")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROWS:
        raise ValueError("Private lab batch has unexpected count")

    LabResult = apps.get_model("core", "LabResult")
    laboratory = batch.get("laboratory", "")[:180]
    seen = set()
    created = 0
    untouched = 0

    for r in rows:
        name = r["name"]
        clock = time.fromisoformat(r["time"])
        key = (clock, name)
        if not isinstance(name, str) or len(name) > 160 or key in seen:
            raise ValueError("Private lab batch has invalid or duplicate test name/time")
        seen.add(key)
        if clock not in (time(9, 54), time(9, 55), time(10, 54)):
            raise ValueError("Private lab batch contains unexpected sample time")
        try:
            value = Decimal(r["value"])
            ref_min = Decimal(r["min"]) if r.get("min") is not None else None
            ref_max = Decimal(r["max"]) if r.get("max") is not None else None
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("Private lab batch contains a malformed numeric value") from exc
        if not value.is_finite():
            raise ValueError("Private lab batch contains nonfinite number")

        _, made = LabResult.objects.using(schema_editor.connection.alias).get_or_create(
            date=EXPECTED_DATE,
            time=clock,
            test_name=name,
            defaults={
                "value": value,
                "unit": r.get("unit", "")[:80],
                "reference_min": ref_min,
                "reference_max": ref_max,
                "laboratory": laboratory,
                "notes": r.get("notes", ""),
            },
        )
        if made:
            created += 1
        else:
            untouched += 1

    print(f"2026-10-27 confidential lab records: inserted={created} existing_untouched={untouched}")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0053_hemafer_35ml_from_20261022"),
    ]

    operations = [
        migrations.RunPython(import_private_lab_batch, migrations.RunPython.noop),
    ]
