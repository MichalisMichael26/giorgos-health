from datetime import date
from django.db import migrations, models


def create_default_profile(apps, schema_editor):
    ChildProfile = apps.get_model("core", "ChildProfile")
    if not ChildProfile.objects.exists():
        ChildProfile.objects.create(
            name="Γιώργος",
            birth_date=date(2026, 6, 27),
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_medications_appointments"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChildProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="Γιώργος", max_length=100, verbose_name="Όνομα παιδιού")),
                ("birth_date", models.DateField(verbose_name="Ημερομηνία γέννησης")),
                ("clinician_target_min_ml", models.PositiveIntegerField(blank=True, null=True, verbose_name="Στόχος ιατρού — ελάχιστο ml/24ωρο")),
                ("clinician_target_max_ml", models.PositiveIntegerField(blank=True, null=True, verbose_name="Στόχος ιατρού — μέγιστο ml/24ωρο")),
                ("clinician_target_note", models.CharField(blank=True, help_text="Π.χ. οδηγία παιδιάτρου / διαιτολόγου και ημερομηνία.", max_length=220, verbose_name="Σημείωση στόχου")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Προφίλ παιδιού",
                "verbose_name_plural": "Προφίλ παιδιού",
            },
        ),
        migrations.RunPython(create_default_profile, migrations.RunPython.noop),
    ]
