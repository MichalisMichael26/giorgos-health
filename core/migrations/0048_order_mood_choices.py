from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0047_moodentry_additional_moods"),
    ]

    operations = [
        migrations.AlterField(
            model_name="moodentry",
            name="mood",
            field=models.CharField(
                "Διάθεση",
                max_length=16,
                choices=[
                    ("very_playful", "🤩 Πολύ παιχνιδιάρης"),
                    ("playful", "🥰 Παιχνιδιάρης"),
                    ("happy", "😄 Χαρούμενος"),
                    ("calm", "😌 Ήρεμος"),
                    ("sleepy", "😴 Νυσταγμένος"),
                    ("restless", "😟 Ανήσυχος"),
                    ("fussy", "😣 Γκρινιάρης"),
                    ("sad", "😢 Λυπημένος"),
                    ("scared", "😨 Φοβισμένος"),
                    ("crying", "😭 Κλαίει"),
                    ("uncomfortable", "😖 Δείχνει δυσφορία"),
                ],
            ),
        ),
    ]
