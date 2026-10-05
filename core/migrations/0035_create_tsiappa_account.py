import os

from django.contrib.auth.hashers import make_password
from django.db import migrations


TSIAPPA_DISPLAY_NAME = "Κυρία Τσιάππα"


def create_tsiappa_readonly_account(apps, schema_editor):
    User = apps.get_model("auth", "User")
    UserAccessProfile = apps.get_model("core", "UserAccessProfile")

    username = (os.environ.get("DJANGO_TSIAPPA_USERNAME") or "tsiappa").strip()
    password = os.environ.get("DJANGO_TSIAPPA_PASSWORD")
    if not password:
        raise RuntimeError("DJANGO_TSIAPPA_PASSWORD is required to create the Tsiappa account.")

    user, _ = User.objects.get_or_create(username=username)
    user.password = make_password(password)
    user.is_active = True
    user.is_staff = False
    user.is_superuser = False
    user.save(update_fields=["password", "is_active", "is_staff", "is_superuser"])

    UserAccessProfile.objects.update_or_create(
        user_id=user.id,
        defaults={
            "role": "doctor_readonly",
            "display_name": TSIAPPA_DISPLAY_NAME,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0034_add_beyfortus_rsv_record"),
    ]

    operations = [
        migrations.RunPython(
            create_tsiappa_readonly_account,
            migrations.RunPython.noop,
        ),
    ]
