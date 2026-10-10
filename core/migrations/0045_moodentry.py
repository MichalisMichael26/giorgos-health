from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0044_mealentry_nasogastric_tube_checkbox"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MoodEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="Ημερομηνία")),
                ("time", models.TimeField(verbose_name="Ώρα")),
                ("mood", models.CharField(choices=[
                    ("happy", "😄 Χαρούμενος"),
                    ("calm", "😌 Ήρεμος"),
                    ("restless", "😟 Ανήσυχος"),
                    ("fussy", "😣 Γκρινιάρης"),
                    ("sad", "😢 Λυπημένος"),
                ], max_length=16, verbose_name="Διάθεση")),
                ("notes", models.TextField(blank=True, verbose_name="Παρατήρηση (προαιρετική)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="mood_entries", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ["-date", "-time", "-pk"],
                "verbose_name": "Καταγραφή διάθεσης",
                "verbose_name_plural": "Καταγραφές διάθεσης",
            },
        ),
    ]
