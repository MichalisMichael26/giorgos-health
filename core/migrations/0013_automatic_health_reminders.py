from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_mobile_push_notifications"),
    ]

    operations = [
        migrations.AlterField(
            model_name="healthreminder",
            name="reminder_type",
            field=models.CharField(
                choices=[
                    ("meal", "Γεύμα"),
                    ("medication", "Φάρμακο"),
                    ("vaccine", "Εμβόλιο"),
                    ("measurement", "Μέτρηση"),
                    ("lab", "Εξέταση"),
                    ("appointment", "Ραντεβού"),
                    ("other", "Άλλο"),
                ],
                default="other",
                max_length=20,
                verbose_name="Τύπος",
            ),
        ),
        migrations.AddField(
            model_name="healthreminder",
            name="auto_generated",
            field=models.BooleanField(default=False, verbose_name="Αυτόματη υπενθύμιση"),
        ),
        migrations.AddField(
            model_name="healthreminder",
            name="source_key",
            field=models.CharField(
                blank=True,
                max_length=140,
                null=True,
                unique=True,
                verbose_name="Κλειδί αυτόματης υπενθύμισης",
            ),
        ),
    ]
