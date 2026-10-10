from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0045_moodentry"),
    ]

    operations = [
        migrations.AlterField(
            model_name="moodentry",
            name="mood",
            field=models.CharField(
                "Διάθεση",
                max_length=16,
                choices=[
                    ("happy", "😄 Χαρούμενος"),
                    ("calm", "😌 Ήρεμος"),
                    ("restless", "😟 Ανήσυχος"),
                    ("fussy", "😣 Γκρινιάρης"),
                    ("sad", "😢 Λυπημένος"),
                    ("scared", "😨 Φοβισμένος"),
                    ("sleepy", "😴 Νυσταγμένος"),
                    ("crying", "😭 Κλαίει"),
                    ("uncomfortable", "😖 Δείχνει δυσφορία"),
                    ("playful", "🥰 Παιχνιδιάρης"),
                    ("very_playful", "🤩 Πολύ παιχνιδιάρης"),
                ],
            ),
        ),
    ]
