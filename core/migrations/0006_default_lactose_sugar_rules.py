from django.db import migrations


DEFAULT_RULES = [
    {
        "term": "λακτόζη",
        "applies_to": "both",
        "guidance": "avoid",
        "note": "Καταχωρημένος περιορισμός: όχι λακτόζη.",
        "active": True,
    },
    {
        "term": "lactose",
        "applies_to": "both",
        "guidance": "avoid",
        "note": "Καταχωρημένος περιορισμός: όχι λακτόζη.",
        "active": True,
    },
    {
        "term": "ζάχαρη",
        "applies_to": "both",
        "guidance": "avoid",
        "note": "Καταχωρημένος περιορισμός: όχι ζάχαρη.",
        "active": True,
    },
    {
        "term": "sugar",
        "applies_to": "both",
        "guidance": "avoid",
        "note": "Καταχωρημένος περιορισμός: όχι ζάχαρη.",
        "active": True,
    },
]


def seed_default_rules(apps, schema_editor):
    SafetyRule = apps.get_model("core", "SafetyRule")

    for rule in DEFAULT_RULES:
        existing = SafetyRule.objects.filter(term__iexact=rule["term"]).first()

        if existing:
            # Do not create duplicates. Make the explicitly requested restriction active.
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
        ("core", "0005_safety_checker"),
    ]

    operations = [
        migrations.RunPython(seed_default_rules, migrations.RunPython.noop),
    ]
