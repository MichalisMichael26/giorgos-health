from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MedicationEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="Ημερομηνία")),
                ("time", models.TimeField(verbose_name="Ώρα")),
                ("name", models.CharField(max_length=160, verbose_name="Φάρμακο / συμπλήρωμα")),
                ("dose", models.DecimalField(decimal_places=2, max_digits=8, verbose_name="Ποσότητα")),
                ("unit", models.CharField(
                    choices=[
                        ("ml", "ml"),
                        ("mg", "mg"),
                        ("g", "g"),
                        ("drops", "Σταγόνες"),
                        ("scoops", "Κουταλάκια"),
                        ("dose", "Δόση"),
                        ("other", "Άλλο"),
                    ],
                    default="ml",
                    max_length=20,
                    verbose_name="Μονάδα",
                )),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="medication_entries",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"ordering": ["-date", "-time"]},
        ),
        migrations.CreateModel(
            name="MedicalAppointment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="Ημερομηνία")),
                ("time", models.TimeField(verbose_name="Ώρα")),
                ("doctor", models.CharField(blank=True, max_length=160, verbose_name="Ιατρός")),
                ("clinic", models.CharField(blank=True, max_length=180, verbose_name="Κλινική / νοσοκομείο")),
                ("purpose", models.CharField(max_length=220, verbose_name="Λόγος / επανέλεγχος")),
                ("reminder_days_before", models.PositiveSmallIntegerField(default=1, verbose_name="Υπενθύμιση (ημέρες πριν)")),
                ("status", models.CharField(
                    choices=[
                        ("scheduled", "Προγραμματισμένο"),
                        ("completed", "Ολοκληρώθηκε"),
                        ("cancelled", "Ακυρώθηκε"),
                    ],
                    default="scheduled",
                    max_length=20,
                    verbose_name="Κατάσταση",
                )),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["date", "time"]},
        ),
    ]
