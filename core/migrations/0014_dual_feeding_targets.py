from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_automatic_health_reminders"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mealentry",
            name="supplement",
            field=models.CharField(
                blank=True,
                max_length=120,
                verbose_name="Maxijul (scoops)",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="target_with_maxijul_min_ml",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Με Maxijul — ελάχιστο ml/24ωρο",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="target_with_maxijul_max_ml",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Με Maxijul — μέγιστο ml/24ωρο",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="target_without_maxijul_min_ml",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Χωρίς Maxijul — ελάχιστο ml/24ωρο",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="target_without_maxijul_max_ml",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Χωρίς Maxijul — μέγιστο ml/24ωρο",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="feeding_target_note",
            field=models.CharField(
                blank=True,
                help_text="Πηγή/ημερομηνία οδηγίας μεταβολικής ομάδας ή παιδιάτρου.",
                max_length=300,
                verbose_name="Σημείωση εξατομικευμένων στόχων",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="maxijul_plan_active",
            field=models.BooleanField(
                default=True,
                help_text="Χρησιμοποιείται μόνο όταν δεν υπάρχουν ακόμη γεύματα για τη σημερινή ημέρα.",
                verbose_name="Τρέχον πλάνο με Maxijul",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="planned_maxijul_scoops_per_feed",
            field=models.DecimalField(
                decimal_places=2,
                default=1,
                max_digits=5,
                verbose_name="Προγραμματισμένα scoops Maxijul / γεύμα",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="maxijul_scoop_grams",
            field=models.DecimalField(
                decimal_places=2,
                default=4.2,
                help_text="Ελέγξτε ότι αντιστοιχεί στο scoop που χρησιμοποιείτε.",
                max_digits=5,
                verbose_name="Maxijul — γραμμάρια ανά scoop",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="maxijul_kcal_per_100g",
            field=models.DecimalField(
                decimal_places=1,
                default=380,
                max_digits=6,
                verbose_name="Maxijul — kcal / 100 g",
            ),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="maxijul_carbs_per_100g",
            field=models.DecimalField(
                decimal_places=1,
                default=95,
                max_digits=6,
                verbose_name="Maxijul — υδατάνθρακες g / 100 g",
            ),
        ),
    ]
