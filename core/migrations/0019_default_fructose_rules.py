from django.db import migrations


FRUCTOSE_RULES = [
    {
        "term": "φρουκτόζη",
        "applies_to": "both",
        "guidance": "avoid",
        "note": "Καταχωρημένος περιορισμός: όχι φρουκτόζη.",
        "active": True,
    },
    {
        "term": "fructose",
        "applies_to": "both",
        "guidance": "avoid",
        "note": "Καταχωρημένος περιορισμός: όχι φρουκτόζη.",
        "active": True,
    },
]


def seed_fructose_rules(apps, schema_editor):
    SafetyRule = apps.get_model("core", "SafetyRule")

    for rule in FRUCTOSE_RULES:
        existing = SafetyRule.objects.filter(term__iexact=rule["term"]).first()

        if existing:
            existing.applies_to = rule["applies_to"]
            existing.guidance = rule["guidance"]
            existing.note = rule["note"]
            existing.active = True
            existing.save(
                update_fields=["applies_to", "guidance", "note", "active", "updated_at"]
            )
        else:
            SafetyRule.objects.create(**rule)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_dynamic_feeding_from_finish"),
    ]

    operations = [
        migrations.RunPython(seed_fructose_rules, migrations.RunPython.noop),
    ]
