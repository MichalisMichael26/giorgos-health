import os

from django.db import migrations


DISPLAY_NAME = "Georgia Chappa Clinical Paediatric Dietitian"


def rename_tsiappa_profile(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserAccessProfile = apps.get_model("core", "UserAccessProfile")

    configured = (os.environ.get("DJANGO_TSIAPPA_USERNAME") or "tsiappa").strip()
    usernames = {name.casefold() for name in (configured, "tsiappa", "chiappa") if name}

    for user in User.objects.all().iterator():
        if (user.username or "").strip().casefold() not in usernames:
            continue

        UserAccessProfile.objects.update_or_create(
            user_id=user.id,
            defaults={
                "role": "doctor_readonly",
                "display_name": DISPLAY_NAME,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0041_correct_maxijul_to_5g"),
    ]

    operations = [
        migrations.RunPython(rename_tsiappa_profile, migrations.RunPython.noop),
    ]
