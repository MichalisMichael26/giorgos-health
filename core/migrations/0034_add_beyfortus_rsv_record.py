from django.db import migrations


def add_beyfortus_rsv_record(apps, schema_editor):
    VaccineEntry = apps.get_model("core", "VaccineEntry")

    VaccineEntry.objects.get_or_create(
        date="2026-09-25",
        name="Beyfortus 100 mg (RSV)",
        defaults={
            "dose_label": "1η δόση",
            "next_date": None,
            "reminder_days_before": 7,
            "notes": (
                "Beyfortus 100 mg (nirsevimab) για προφύλαξη έναντι RSV. "
                "Αρ. παρτίδας: AZ250077. Καταχώρηση από το βιβλιάριο."
            ),
            "created_by_id": None,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0033_fix_late_evening_meal_date"),
    ]

    operations = [
        migrations.RunPython(
            add_beyfortus_rsv_record,
            migrations.RunPython.noop,
        ),
    ]
