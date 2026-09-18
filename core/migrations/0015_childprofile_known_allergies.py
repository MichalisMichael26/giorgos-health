from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_dual_feeding_targets"),
    ]

    operations = [
        migrations.AddField(
            model_name="childprofile",
            name="known_allergies",
            field=models.TextField(
                blank=True,
                help_text="Καταχώρησε μόνο επιβεβαιωμένες/γνωστές αλλεργίες. Άφησέ το κενό αν δεν υπάρχουν.",
                verbose_name="Γνωστές αλλεργίες",
            ),
        ),
    ]
