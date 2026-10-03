from django.db import migrations, models
import django.db.models.deletion


LOW_THRESHOLD = 60


def backfill_low_glucose_symptoms(apps, schema_editor):
    GlucoseReading = apps.get_model("core", "GlucoseReading")
    SymptomEntry = apps.get_model("core", "SymptomEntry")

    relation_map = {
        "pre_feed": "before_feed",
        "post_feed": "after_feed",
        "other": "unknown",
    }

    for reading in GlucoseReading.objects.filter(value__lt=LOW_THRESHOLD).iterator():
        relation = relation_map.get(reading.context, "unknown")
        rounded_value = int(round(float(reading.value)))
        SymptomEntry.objects.get_or_create(
            source_glucose_id=reading.pk,
            defaults={
                "date": reading.date,
                "time": reading.time,
                "symptom": "Χαμηλή γλυκόζη – συμπληρώστε συμπτώματα",
                "severity": "mild",
                "relation_to_feed": relation,
                "notes": (
                    f"Αυτόματη καταχώρηση από μέτρηση γλυκόζης "
                    f"{rounded_value} mg/dL (<60). "
                    "Συμπληρώστε εδώ τα συμπτώματα/παρατηρήσεις που υπήρχαν εκείνη τη στιγμή."
                ),
                "auto_generated": True,
                "details_completed": False,
                "created_by_id": reading.created_by_id,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0030_merge_0029_doctor_views_vitamin_d"),
    ]

    operations = [
        migrations.AddField(
            model_name="symptomentry",
            name="source_glucose",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="symptom_entry",
                to="core.glucosereading",
                verbose_name="Συνδεδεμένη μέτρηση γλυκόζης",
            ),
        ),
        migrations.AddField(
            model_name="symptomentry",
            name="auto_generated",
            field=models.BooleanField(default=False, verbose_name="Αυτόματη καταχώρηση"),
        ),
        migrations.AddField(
            model_name="symptomentry",
            name="details_completed",
            field=models.BooleanField(default=False, verbose_name="Έγινε συμπλήρωση συμπτωμάτων"),
        ),
        migrations.RunPython(backfill_low_glucose_symptoms, migrations.RunPython.noop),
    ]
}
