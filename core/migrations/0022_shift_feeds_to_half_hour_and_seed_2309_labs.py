from datetime import date, time
from decimal import Decimal

from django.db import migrations


LABORATORY = "Μακάρειο Νοσοκομείο"


# date, time, test_name, value, unit, ref_min, ref_max, notes
LABS_2309 = [
    # Κλινική Βιοχημεία — δείγμα 23/09/2026 11:52
    (date(2026, 9, 23), time(11, 52), "Glucose", "108", "mg/dL", "60", "100", "Πηγή: LabTestResults40927148.pdf."),
    (date(2026, 9, 23), time(11, 52), "Uric acid", "4.2", "mg/dL", "3.4", "7.0", "Πηγή: LabTestResults40927148.pdf."),
    (date(2026, 9, 23), time(11, 52), "Triglycerides", "114", "mg/dL", None, "150", "Πηγή: LabTestResults40927148.pdf. Όριο αναφοράς: <150."),
    (date(2026, 9, 23), time(11, 52), "Urea", "6.4", "mg/dL", "4.0", "19.0", "Πηγή: LabTestResults40927148.pdf."),
    (date(2026, 9, 23), time(11, 52), "Creatinine", "0.17", "mg/dL", "0.17", "0.42", "Πηγή: LabTestResults40927148.pdf. Ακριβές εργαστηριακό αποτέλεσμα: <0.17 mg/dL."),
    (date(2026, 9, 23), time(11, 52), "Sodium", "137", "mmol/L", "138", "145", "Πηγή: LabTestResults40927148.pdf."),
    (date(2026, 9, 23), time(11, 52), "Potassium", "4.5", "mmol/L", "4.1", "5.3", "Πηγή: LabTestResults40927148.pdf."),
    (date(2026, 9, 23), time(11, 52), "ALP", "422", "U/L", "122", "469", "Πηγή: LabTestResults40927148.pdf."),
    (date(2026, 9, 23), time(11, 52), "GGT", "180", "U/L", "10", "71", "Πηγή: LabTestResults40927148.pdf."),
    (date(2026, 9, 23), time(11, 52), "ALT", "66", "U/L", "10", "50", "Πηγή: LabTestResults40927148.pdf."),
    (date(2026, 9, 23), time(11, 52), "AST", "71", "U/L", "10", "50", "Πηγή: LabTestResults40927148.pdf."),
    (date(2026, 9, 23), time(11, 52), "CPK", "78", "U/L", None, "190", "Πηγή: LabTestResults40927148.pdf. Όριο αναφοράς: <190."),

    # Γενική αίματος — δείγμα 23/09/2026 11:51
    (date(2026, 9, 23), time(11, 51), "WBC", "13.68", "10^9/L", "5.00", "19.00", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Neutrophils", "15.1", "%", "15.0", "35.0", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Neutrophils #", "2.05", "10^9/L", "0.80", "6.70", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Lymphocytes", "72.4", "%", "42.0", "72.0", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Lymphocytes #", "9.91", "10^9/L", "2.10", "13.70", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Monocytes", "7.4", "%", "0.0", "6.0", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Monocytes #", "1.01", "10^9/L", "0.00", "1.10", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Eosinophils", "4.6", "%", "0.0", "3.0", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Eosinophils #", "0.63", "10^9/L", "0.00", "0.60", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Basophils", "0.4", "%", "0.0", "1.0", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Basophils #", "0.06", "10^9/L", "0.00", "0.20", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "IG %", "0.10", "%", "0.00", "0.90", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "IG #", "0.020", "10^9/L", "0.000", "0.200", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "RBC", "3.92", "10^12/L", "3.80", "5.20", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Hemoglobin", "11.5", "g/dL", "10.7", "17.3", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Hematocrit", "34.0", "%", "35.0", "49.0", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "MCV", "86.7", "fL", "83.0", "97.0", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "MCH", "29.3", "pg", "27.0", "33.0", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "MCHC", "33.8", "g/dL", "31.0", "35.0", "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "NRBC %", "0.0", "/100WBC", None, None, "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "NRBC #", "0.00", "10^3/uL", None, None, "Πηγή: LabTestResults40926045.pdf."),
    (date(2026, 9, 23), time(11, 51), "Platelets", "665", "10^9/L", "150", "450", "Πηγή: LabTestResults40926045.pdf."),
]


def apply_schedule_and_labs(apps, schema_editor):
    HealthReminder = apps.get_model("core", "HealthReminder")
    LabResult = apps.get_model("core", "LabResult")

    # Remove only the generated fixed meal reminders from the previous :00
    # schedule. They will be rebuilt automatically at :30 by the scheduler.
    HealthReminder.objects.filter(
        auto_generated=True,
        reminder_type="meal",
        source_key__startswith="meal-schedule:",
    ).delete()

    for lab_date, lab_time, test_name, raw_value, unit, raw_min, raw_max, notes in LABS_2309:
        defaults = {
            "value": Decimal(raw_value),
            "unit": unit,
            "reference_min": Decimal(raw_min) if raw_min is not None else None,
            "reference_max": Decimal(raw_max) if raw_max is not None else None,
            "laboratory": LABORATORY,
            "notes": notes,
        }

        item = LabResult.objects.filter(
            date=lab_date,
            time=lab_time,
            test_name=test_name,
        ).order_by("pk").first()

        if item is None:
            LabResult.objects.create(
                date=lab_date,
                time=lab_time,
                test_name=test_name,
                **defaults,
            )
        else:
            for field, value in defaults.items():
                setattr(item, field, value)
            item.save(
                update_fields=[
                    "value",
                    "unit",
                    "reference_min",
                    "reference_max",
                    "laboratory",
                    "notes",
                    "updated_at",
                ]
            )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0021_growth_history_and_measured_by"),
    ]

    operations = [
        migrations.RunPython(
            apply_schedule_and_labs,
            migrations.RunPython.noop,
        ),
    ]
