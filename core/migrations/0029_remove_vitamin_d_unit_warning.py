from django.db import migrations


def remove_vitamin_d_unit_warning(apps, schema_editor):
    MedicationPlan = apps.get_model("core", "MedicationPlan")
    MedicationPlan.objects.filter(name__iexact="Vitamin D").update(
        unit_confirmation_required=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0028_editable_feeding_schedule"),
    ]

    operations = [
        migrations.RunPython(
            remove_vitamin_d_unit_warning,
            migrations.RunPython.noop,
        ),
    ]
