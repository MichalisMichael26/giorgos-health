# Generated for the initial Giorgos Health database schema.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GrowthMeasurement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(verbose_name="Ημερομηνία")),
                (
                    "weight_kg",
                    models.DecimalField(
                        blank=True,
                        decimal_places=3,
                        max_digits=5,
                        null=True,
                        verbose_name="Βάρος (kg)",
                    ),
                ),
                (
                    "length_cm",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=5,
                        null=True,
                        verbose_name="Ύψος/Μήκος (cm)",
                    ),
                ),
                (
                    "head_cm",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=5,
                        null=True,
                        verbose_name="Περίμετρος κεφαλής (cm)",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-date"],
            },
        ),
        migrations.CreateModel(
            name="MealEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(verbose_name="Ημερομηνία")),
                (
                    "scheduled_time",
                    models.TimeField(verbose_name="Προγραμματισμένη ώρα"),
                ),
                (
                    "actual_time",
                    models.TimeField(
                        blank=True,
                        null=True,
                        verbose_name="Πραγματική ώρα",
                    ),
                ),
                (
                    "offered_ml",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Προσφέρθηκαν (ml)",
                    ),
                ),
                (
                    "consumed_ml",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Ήπιε (ml)",
                    ),
                ),
                (
                    "formula",
                    models.CharField(
                        blank=True,
                        max_length=120,
                        verbose_name="Formula",
                    ),
                ),
                (
                    "supplement",
                    models.CharField(
                        blank=True,
                        max_length=120,
                        verbose_name="Συμπλήρωμα",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("completed", "Ολοκληρώθηκε"),
                            ("partial", "Μερικό"),
                            ("missed", "Δεν καταχωρήθηκε"),
                        ],
                        default="completed",
                        max_length=20,
                        verbose_name="Κατάσταση",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="meal_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-date", "-scheduled_time"],
            },
        ),
        migrations.CreateModel(
            name="GlucoseReading",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(verbose_name="Ημερομηνία")),
                ("time", models.TimeField(verbose_name="Ώρα")),
                (
                    "value",
                    models.DecimalField(
                        decimal_places=1,
                        max_digits=6,
                        verbose_name="Γλυκόζη (mg/dL)",
                    ),
                ),
                (
                    "context",
                    models.CharField(
                        choices=[
                            ("pre_feed", "Πριν το γεύμα"),
                            ("post_feed", "Μετά το γεύμα"),
                            ("other", "Άλλο"),
                        ],
                        default="pre_feed",
                        max_length=20,
                        verbose_name="Σχέση με γεύμα",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Σημειώσεις")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="glucose_readings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "related_meal",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="glucose_readings",
                        to="core.mealentry",
                        verbose_name="Σχετικό γεύμα",
                    ),
                ),
            ],
            options={
                "ordering": ["-date", "-time"],
            },
        ),
    ]
