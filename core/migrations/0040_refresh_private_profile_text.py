import os

from django.db import migrations


def _text(name):
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else None


def refresh_private_profile_text(apps, schema_editor):
    ChildProfile = apps.get_model("core", "ChildProfile")

    values = {
        "current_feeding_plan": _text("GIORGOS_FEEDING_PLAN"),
        "emergency_instructions": _text("GIORGOS_EMERGENCY_INSTRUCTIONS"),
        "feeding_target_note": _text("GIORGOS_FEEDING_TARGET_NOTE"),
        "clinician_target_note": _text("GIORGOS_FEEDING_TARGET_NOTE"),
    }
    values = {key: value for key, value in values.items() if value is not None}
    if values:
        ChildProfile.objects.all().update(**values)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0039_private_profile_update"),
    ]

    operations = [
        migrations.RunPython(refresh_private_profile_text, migrations.RunPython.noop),
    ]
