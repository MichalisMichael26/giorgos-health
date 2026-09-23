from collections import defaultdict
from datetime import timedelta

from django.db import migrations, models
from django.utils import timezone


def backfill_real_activity_from_audit(apps, schema_editor):
    AuditLog = apps.get_model("core", "AuditLog")
    UserAccessLog = apps.get_model("core", "UserAccessLog")
    UserAccessProfile = apps.get_model("core", "UserAccessProfile")

    cutoff = timezone.now() - timedelta(days=7)

    rows = (
        AuditLog.objects
        .filter(user_id__isnull=False, timestamp__gte=cutoff)
        .order_by("user_id", "timestamp", "pk")
        .values("user_id", "timestamp")
    )

    grouped = defaultdict(list)
    current_tz = timezone.get_current_timezone()

    for row in rows:
        timestamp = row["timestamp"]
        local_day = timezone.localtime(timestamp, current_tz).date()
        grouped[(row["user_id"], local_day)].append(timestamp)

    for (user_id, local_day), timestamps in grouped.items():
        first_activity = min(timestamps)
        last_activity = max(timestamps)

        already_exists = UserAccessLog.objects.filter(
            user_id=user_id,
            entry_source="audit_backfill",
            login_at__date=local_day,
        ).exists()
        if already_exists:
            continue

        UserAccessLog.objects.create(
            user_id=user_id,
            login_at=first_activity,
            last_seen_at=last_activity,
            logout_at=None,
            entry_source="audit_backfill",
            user_agent="",
            first_path="",
            last_path="",
        )

        profile = UserAccessProfile.objects.filter(user_id=user_id).first()
        if profile and (
            profile.last_seen_at is None
            or profile.last_seen_at < last_activity
        ):
            profile.last_seen_at = last_activity
            profile.save(update_fields=["last_seen_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0025_user_access_log"),
    ]

    operations = [
        migrations.AlterField(
            model_name="useraccesslog",
            name="entry_source",
            field=models.CharField(
                choices=[
                    ("login", "Κανονικό login"),
                    ("existing_session", "Ήδη ενεργή συνεδρία"),
                    ("audit_backfill", "Ιστορική δραστηριότητα από Audit Log"),
                ],
                default="login",
                max_length=30,
                verbose_name="Τρόπος εισόδου",
            ),
        ),
        migrations.RunPython(
            backfill_real_activity_from_audit,
            migrations.RunPython.noop,
        ),
    ]
