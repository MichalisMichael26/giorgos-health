from datetime import date

from django.db import migrations


FIXED_BIRTH_DATE = date(2026, 6, 27)


def lock_existing_birth_date(apps, schema_editor):
    ChildProfile = apps.get_model("core", "ChildProfile")
    ChildProfile.objects.all().update(birth_date=FIXED_BIRTH_DATE)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_structured_emergency_phones"),
    ]

    operations = [
        migrations.RunPython(lock_existing_birth_date, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="medicalappointment",
            options={"ordering": ["-date", "-time"]},
        ),
    ]
