from django.db import migrations


AUTO_NOTE_PREFIX = "Αυτόματη καταχώρηση από μέτρηση γλυκόζης "


def clear_system_generated_symptom_notes(apps, schema_editor):
    SymptomEntry = apps.get_model("core", "SymptomEntry")
    SymptomEntry.objects.filter(
        auto_generated=True,
        notes__startswith=AUTO_NOTE_PREFIX,
    ).update(notes="")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0031_low_glucose_symptom_tracking"),
    ]

    operations = [
        migrations.RunPython(
            clear_system_generated_symptom_notes,
            migrations.RunPython.noop,
        ),
    ]
