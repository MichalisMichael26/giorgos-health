from datetime import date

from django.db import migrations


VACCINES = [
    {
        "name": "Hexyon",
        "date": date(2026, 8, 27),
        "dose_label": "1η δόση",
        "next_date": date(2026, 10, 27),
        "reminder_days_before": 7,
        "notes": "Συνδυασμένο εμβόλιο: DTaP + IPV + Hib + Hep B. Καταχώρηση από το βιβλιάριο εμβολιασμών.",
    },
    {
        "name": "Prevenar 20",
        "date": date(2026, 8, 27),
        "dose_label": "1η δόση",
        "next_date": date(2026, 10, 27),
        "reminder_days_before": 7,
        "notes": "Πνευμονιοκοκκικό συζευγμένο εμβόλιο (PCV). Καταχώρηση από το βιβλιάριο εμβολιασμών.",
    },
    {
        "name": "Rotavirus",
        "date": date(2026, 8, 27),
        "dose_label": "1η δόση",
        "next_date": date(2026, 10, 27),
        "reminder_days_before": 7,
        "notes": "Εμβόλιο ροταϊού. Καταχώρηση από το βιβλιάριο εμβολιασμών.",
    },
]


def seed_vaccines(apps, schema_editor):
    VaccineEntry = apps.get_model("core", "VaccineEntry")

    for data in VACCINES:
        VaccineEntry.objects.get_or_create(
            name=data["name"],
            date=data["date"],
            dose_label=data["dose_label"],
            defaults={
                "next_date": data["next_date"],
                "reminder_days_before": data["reminder_days_before"],
                "notes": data["notes"],
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_daily_care_suite"),
    ]

    operations = [
        migrations.RunPython(seed_vaccines, migrations.RunPython.noop),
    ]
