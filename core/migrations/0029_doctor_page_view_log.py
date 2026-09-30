from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0028_editable_feeding_schedule"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DoctorPageViewLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("viewed_at", models.DateTimeField(auto_now_add=True, verbose_name="Προβολή στις")),
                ("path", models.CharField(max_length=240, verbose_name="Σελίδα / path")),
                ("view_name", models.CharField(blank=True, max_length=120, verbose_name="View name")),
                (
                    "access_log",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="page_views",
                        to="core.useraccesslog",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="giorgos_doctor_page_views",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["viewed_at"],
            },
        ),
        migrations.AddIndex(
            model_name="doctorpageviewlog",
            index=models.Index(fields=["access_log", "viewed_at"], name="gh_doctor_view_session"),
        ),
        migrations.AddIndex(
            model_name="doctorpageviewlog",
            index=models.Index(fields=["user", "-viewed_at"], name="gh_doctor_view_user"),
        ),
    ]
