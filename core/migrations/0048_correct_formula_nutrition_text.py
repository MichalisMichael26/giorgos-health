"""Correct old display typos while preserving the clinician's feeding amounts."""
import re
from decimal import Decimal

from django.db import migrations


def _normalize(value):
    value = str(value or "")
    value = re.sub(r"\bFrysolac\b", "Frisolac", value, flags=re.IGNORECASE)
    value = re.sub(r"\bδιατροφολόγος\b", "κλινική διαιτολόγος", value, flags=re.IGNORECASE)
    value = re.sub(r"\bδιατροφολόγου\b", "κλινικής διαιτολόγου", value, flags=re.IGNORECASE)
    value = re.sub(r"\bδιατροφολόγο\b", "κλινική διαιτολόγο", value, flags=re.IGNORECASE)
    return value


def update_current_reference_text(apps, schema_editor):
    ChildProfile = apps.get_model("core", "ChildProfile")
    fields = ("current_feeding_plan", "feeding_target_note", "clinician_target_note", "emergency_instructions")
    for profile in ChildProfile.objects.all().iterator():
        updates = {}
        for field in fields:
            before = getattr(profile, field) or ""
            after = _normalize(before)
            if after != before:
                updates[field] = after
        # These are the supplied powder values; keep the recorded clinical
        # formula volumes, prepared meals, and historical documents untouched.
        if profile.maxijul_scoop_grams != Decimal("5"):
            updates["maxijul_scoop_grams"] = Decimal("5")
        if profile.maxijul_kcal_per_100g != Decimal("380"):
            updates["maxijul_kcal_per_100g"] = Decimal("380")
        if profile.maxijul_carbs_per_100g != Decimal("95"):
            updates["maxijul_carbs_per_100g"] = Decimal("95")
        if updates:
            ChildProfile.objects.filter(pk=profile.pk).update(**updates)


class Migration(migrations.Migration):
    dependencies = [("core", "0047_moodentry_additional_moods")]
    operations = [
        migrations.RunPython(update_current_reference_text, migrations.RunPython.noop),
    ]
