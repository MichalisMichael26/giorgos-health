from datetime import date, time
from decimal import Decimal

from django.db import migrations


LABORATORY = "Μακάρειο Νοσοκομείο"
LAB_DATE = date(2026, 10, 6)
CBC_TIME = time(13, 13)
CHEM_TIME = time(13, 13)


# time, test_name, value, unit, ref_min, ref_max, notes
LABS_0610 = [
    # Κλινική Βιοχημεία — δείγμα 06/10/2026 13:13
    (CHEM_TIME, "Glucose", "81", "mg/dL", "60", "100", "Πηγή: LabTestResults41205599.pdf."),
    (CHEM_TIME, "Uric acid", "4.1", "mg/dL", "3.4", "7.0", "Πηγή: LabTestResults41205599.pdf."),
    (CHEM_TIME, "GGT", "85", "U/L", "10", "71", "Πηγή: LabTestResults41205599.pdf."),
    (CHEM_TIME, "ALT", "30", "U/L", "10", "50", "Πηγή: LabTestResults41205599.pdf."),
    (CHEM_TIME, "AST", "48", "U/L", "10", "50", "Πηγή: LabTestResults41205599.pdf."),

    # Γενική αίματος — δείγμα 06/10/2026 13:13
    (CBC_TIME, "WBC", "14.10", "10^9/L", "5.00", "19.00", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Neutrophils", "15.0", "%", "15.0", "35.0", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Neutrophils #", "2.11", "10^9/L", "0.80", "6.70", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Lymphocytes", "73.8", "%", "42.0", "72.0", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Lymphocytes #", "10.41", "10^9/L", "2.10", "13.70", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Monocytes", "6.5", "%", "0.0", "6.0", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Monocytes #", "0.91", "10^9/L", "0.00", "1.10", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Eosinophils", "4.1", "%", "0.0", "3.0", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Eosinophils #", "0.58", "10^9/L", "0.00", "0.60", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Basophils", "0.4", "%", "0.0", "1.0", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Basophils #", "0.06", "10^9/L", "0.00", "0.20", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "IG %", "0.20", "%", "0.00", "0.90", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "IG #", "0.030", "10^9/L", "0.000", "0.200", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "RBC", "4.27", "10^12/L", "3.80", "5.20", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Hemoglobin", "12.4", "g/dL", "10.7", "17.3", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "Hematocrit", "35.3", "%", "35.0", "49.0", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "MCV", "82.7", "fL", "83.0", "97.0", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "MCH", "29.0", "pg", "27.0", "33.0", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "MCHC", "35.1", "g/dL", "31.0", "35.0", "Πηγή: LabTestResults41204574.pdf."),
    (CBC_TIME, "NRBC %", "0.1", "/100WBC", None, None, "Πηγή: LabTestResults41204574.pdf. Το εύρος αναφοράς δεν καταχωρήθηκε επειδή δεν αποδίδεται καθαρά στο εκτύπωμα."),
    (CBC_TIME, "NRBC #", "0.01", "10^3/uL", None, None, "Πηγή: LabTestResults41204574.pdf. Το εύρος αναφοράς δεν καταχωρήθηκε επειδή δεν αποδίδεται καθαρά στο εκτύπωμα."),
    (CBC_TIME, "Platelets", "629", "10^9/L", "150", "450", "Πηγή: LabTestResults41204574.pdf."),

    # Αέρια αίματος — φωτογραφία εκτυπώματος 06/10/2026.
    # Η ώρα είναι μερικώς κρυμμένη στη φωτογραφία, οπότε δεν αποθηκεύεται εικαστική ώρα.
    (None, "Blood gas pH", "7.347", "", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026. Είδος δείγματος: Not specified. Θερμοκρασία: 37.0 C."),
    (None, "Blood gas pCO2", "40.1", "mmHg", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas pO2", "42.1", "mmHg", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas ctHb", "14.3", "g/dL", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas Hct", "43.8", "%", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas sO2", "74.6", "%", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas FO2Hb", "72.9", "%", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas FCOHb", "1.2", "%", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas FHHb", "24.8", "%", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas FMetHb", "1.1", "%", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas K+", "4.8", "mmol/L", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas Na+", "138", "mmol/L", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas iCa2+", "1.21", "mmol/L", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas Cl-", "106", "mmol/L", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas Glucose", "82", "mg/dL", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas Lactate", "2.9", "mmol/L", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026. Στο εκτύπωμα αναγράφεται: 0210: Calibration error(s) present."),
    (None, "Blood gas pH(T)", "7.347", "", None, None, "Temperature-corrected value. Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas pCO2(T)", "40.1", "mmHg", None, None, "Temperature-corrected value. Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas pO2(T)", "42.1", "mmHg", None, None, "Temperature-corrected value. Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas ctO2", "14.6", "Vol%", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas p50", "28.46", "mmHg", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas Base Excess", "-3.3", "mmol/L", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas HCO3", "21.1", "mmol/L", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
    (None, "Blood gas mOsm", "281.4", "mmol/kg", None, None, "Πηγή: φωτογραφία εκτυπώματος αερίων αίματος 06/10/2026."),
]


def seed_0610_labs(apps, schema_editor):
    LabResult = apps.get_model("core", "LabResult")

    for lab_time, test_name, raw_value, unit, raw_min, raw_max, notes in LABS_0610:
        defaults = {
            "value": Decimal(raw_value),
            "unit": unit,
            "reference_min": Decimal(raw_min) if raw_min is not None else None,
            "reference_max": Decimal(raw_max) if raw_max is not None else None,
            "laboratory": LABORATORY,
            "notes": notes,
        }

        item = LabResult.objects.filter(
            date=LAB_DATE,
            time=lab_time,
            test_name=test_name,
        ).order_by("pk").first()

        if item is None:
            LabResult.objects.create(
                date=LAB_DATE,
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
        ("core", "0037_reset_tsiappa_password_v2"),
    ]

    operations = [
        migrations.RunPython(
            seed_0610_labs,
            migrations.RunPython.noop,
        ),
    ]
