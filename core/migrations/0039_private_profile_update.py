import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import migrations


def _text(name):
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else None


def _integer(name):
    value = _text(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _decimal(name):
    value = _text(name)
    if value is None:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def apply_private_profile_update(apps, schema_editor):
    ChildProfile = apps.get_model("core", "ChildProfile")
    GrowthMeasurement = apps.get_model("core", "GrowthMeasurement")

    daily_min = _integer("GIORGOS_DAILY_MIN_ML")
    profile_values = {
        "clinician_target_min_ml": daily_min,
        "clinician_target_note": _text("GIORGOS_FEEDING_TARGET_NOTE"),
        "target_with_maxijul_min_ml": daily_min,
        "feeding_target_note": _text("GIORGOS_FEEDING_TARGET_NOTE"),
        "planned_maxijul_scoops_per_feed": _decimal("GIORGOS_MAXIJUL_SCOOPS_PER_FEED"),
        "maxijul_scoop_grams": _decimal("GIORGOS_MAXIJUL_SCOOP_GRAMS"),
        "current_feeding_plan": _text("GIORGOS_FEEDING_PLAN"),
        "emergency_instructions": _text("GIORGOS_EMERGENCY_INSTRUCTIONS"),
    }
    profile_values = {key: value for key, value in profile_values.items() if value is not None}
    if profile_values:
        profile_values["clinician_target_max_ml"] = None
        profile_values["target_with_maxijul_max_ml"] = None
        profile_values["maxijul_plan_active"] = True
        ChildProfile.objects.all().update(**profile_values)

    raw_date = _text("GIORGOS_GROWTH_DATE")
    if not raw_date:
        return
    try:
        measured_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        return

    growth_values = {
        "weight_kg": _decimal("GIORGOS_GROWTH_WEIGHT_KG"),
        "length_cm": _decimal("GIORGOS_GROWTH_LENGTH_CM"),
        "head_cm": _decimal("GIORGOS_GROWTH_HEAD_CM"),
        "measured_by": _text("GIORGOS_GROWTH_MEASURED_BY") or "",
        "notes": _text("GIORGOS_GROWTH_NOTES") or "",
    }
    if not any(growth_values[key] is not None for key in ("weight_kg", "length_cm", "head_cm")):
        return

    item = GrowthMeasurement.objects.filter(date=measured_date).order_by("pk").first()
    if item is None:
        GrowthMeasurement.objects.create(date=measured_date, **growth_values)
    else:
        for field, value in growth_values.items():
            setattr(item, field, value)
        item.save(update_fields=["weight_kg", "length_cm", "head_cm", "measured_by", "notes"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0038_seed_0610_labs"),
    ]

    operations = [
        migrations.RunPython(apply_private_profile_update, migrations.RunPython.noop),
    ]
