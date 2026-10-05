import os

from django.contrib.auth.hashers import make_password
from django.db import migrations


def reset_tsiappa_password_v2(apps, schema_editor):
    User = apps.get_model("auth", "User")

    username = (os.environ.get("DJANGO_TSIAPPA_USERNAME") or "tsiappa").strip()
    password = os.environ.get("DJANGO_TSIAPPA_PASSWORD")
    if not password:
        raise RuntimeError("DJANGO_TSIAPPA_PASSWORD is required.")

    User.objects.filter(username=username).update(password=make_password(password))


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0036_reset_tsiappa_password"),
    ]

    operations = [
        migrations.RunPython(
            reset_tsiappa_password_v2,
            migrations.RunPython.noop,
        ),
    ]
}
