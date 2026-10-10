from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0046_alter_moodentry_mood"),
    ]

    operations = [
        migrations.AddField(
            model_name="moodentry",
            name="additional_moods",
            field=models.JSONField(blank=True, default=list, verbose_name="Επιπλέον διαθέσεις"),
        ),
    ]
