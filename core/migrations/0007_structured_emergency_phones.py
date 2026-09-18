from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_default_lactose_sugar_rules"),
    ]

    operations = [
        migrations.AddField(
            model_name="childprofile",
            name="father_phone",
            field=models.CharField(blank=True, max_length=40, verbose_name="Τηλέφωνο μπαμπά"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="mother_phone",
            field=models.CharField(blank=True, max_length=40, verbose_name="Τηλέφωνο μαμάς"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="dr_savvas_phone",
            field=models.CharField(blank=True, max_length=40, verbose_name="Τηλέφωνο Δρ Σάββας Σάββα"),
        ),
        migrations.AddField(
            model_name="childprofile",
            name="dr_grafakou_phone",
            field=models.CharField(blank=True, max_length=40, verbose_name="Τηλέφωνο Δρ Όλγα Γραφάκου"),
        ),
        migrations.AlterField(
            model_name="childprofile",
            name="emergency_contacts",
            field=models.TextField(
                blank=True,
                help_text="Προαιρετικά: άλλο τηλέφωνο, κλινική, νοσοκομείο ή επαφή.",
                verbose_name="Άλλο τηλέφωνο / επαφή",
            ),
        ),
    ]
