from datetime import date, datetime, time
from decimal import Decimal

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db import OperationalError, ProgrammingError
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .audit import get_current_user
from .models import (
    AuditLog,
    HealthReminder,
    MealEntry,
    MedicationEntry,
    MedicationPlan,
    MedicalAppointment,
    UserAccessLog,
    UserAccessProfile,
)


def _tracked_sender(sender):
    sensitive_internal_models = {
        "PushConfig",
        "PushSubscription",
        "PushDeliveryLog",
        "UserAccessLog",
    }
    return (
        getattr(sender, "_meta", None)
        and sender._meta.app_label == "core"
        and sender is not AuditLog
        and sender.__name__ not in sensitive_internal_models
    )


def _json_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "[binary data]"
    return str(value)


def snapshot(instance):
    data = {}
    for field in instance._meta.concrete_fields:
        if field.name in {"data", "created_at", "updated_at"}:
            continue
        try:
            if field.is_relation:
                value = getattr(instance, field.attname, None)
            else:
                value = getattr(instance, field.name, None)
            data[str(field.verbose_name)] = _json_value(value)
        except Exception:
            continue
    return data


def _write_log(action, instance, changes):
    if not changes:
        return
    try:
        AuditLog.objects.create(
            user=get_current_user(),
            action=action,
            model_name=instance._meta.verbose_name.title(),
            object_id=str(instance.pk or ""),
            object_repr=str(instance)[:255],
            changes=changes,
        )
    except (OperationalError, ProgrammingError):
        # The audit table may not exist yet while migrations are running.
        return


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    if not _tracked_sender(sender):
        return
    if not instance.pk:
        instance._audit_before = {}
        return
    try:
        old = sender.objects.get(pk=instance.pk)
        instance._audit_before = snapshot(old)
    except sender.DoesNotExist:
        instance._audit_before = {}
    except (OperationalError, ProgrammingError):
        instance._audit_before = {}


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    if not _tracked_sender(sender):
        return
    after = snapshot(instance)
    before = getattr(instance, "_audit_before", {})
    if created:
        changes = {key: {"old": None, "new": value} for key, value in after.items()}
        _write_log("create", instance, changes)
        return
    changes = {}
    for key in sorted(set(before) | set(after)):
        old = before.get(key)
        new = after.get(key)
        if old != new:
            changes[key] = {"old": old, "new": new}
    _write_log("update", instance, changes)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if not _tracked_sender(sender):
        return
    before = snapshot(instance)
    changes = {key: {"old": value, "new": None} for key, value in before.items()}
    _write_log("delete", instance, changes)



@receiver(post_save, sender=MealEntry)
def sync_meal_automatic_reminders(sender, instance, **kwargs):
    from .auto_reminders import (
        sync_fixed_meal_schedule_reminders,
        sync_low_meal_reminder,
    )

    sync_low_meal_reminder(instance)
    sync_fixed_meal_schedule_reminders()


@receiver(post_delete, sender=MealEntry)
def remove_meal_automatic_reminders(sender, instance, **kwargs):
    from .auto_reminders import sync_fixed_meal_schedule_reminders

    HealthReminder.objects.filter(source_key=f"low-meal:{instance.pk}").delete()
    sync_fixed_meal_schedule_reminders()


@receiver(post_save, sender=MedicalAppointment)
def sync_appointment_automatic_reminder(sender, instance, **kwargs):
    from .auto_reminders import sync_appointment_reminder

    sync_appointment_reminder(instance)


@receiver(post_delete, sender=MedicalAppointment)
def remove_appointment_automatic_reminder(sender, instance, **kwargs):
    HealthReminder.objects.filter(source_key=f"appointment:{instance.pk}").delete()


@receiver(post_save, sender=MedicationEntry)
def sync_medication_plan_reminder_after_entry(sender, instance, **kwargs):
    from .auto_reminders import sync_medication_plan_reminders

    sync_medication_plan_reminders()


@receiver(post_delete, sender=MedicationEntry)
def sync_medication_plan_reminder_after_delete(sender, instance, **kwargs):
    from .auto_reminders import sync_medication_plan_reminders

    sync_medication_plan_reminders()


@receiver(post_save, sender=MedicationPlan)
def sync_medication_plan_after_plan_change(sender, instance, **kwargs):
    from .auto_reminders import sync_medication_plan_reminders

    sync_medication_plan_reminders()


@receiver(user_logged_in)
def record_user_login(sender, request, user, **kwargs):
    now = timezone.now()
    path = ((getattr(request, "path", "") or "")[:240] if request else "")
    user_agent = (
        ((request.META.get("HTTP_USER_AGENT") or "")[:500])
        if request
        else ""
    )

    try:
        log = UserAccessLog.objects.create(
            user=user,
            login_at=now,
            last_seen_at=now,
            entry_source="login",
            user_agent=user_agent,
            first_path=path,
            last_path=path,
        )

        if request is not None:
            request.session["_gh_access_log_id"] = log.pk
            request.session["_gh_access_last_seen_write"] = int(now.timestamp())

        profile, _ = UserAccessProfile.objects.get_or_create(user=user)
        UserAccessProfile.objects.filter(pk=profile.pk).update(
            last_seen_at=now,
            last_seen_path=path,
            last_seen_user_agent=user_agent,
        )
    except (OperationalError, ProgrammingError):
        return


@receiver(user_logged_out)
def record_user_logout(sender, request, user, **kwargs):
    if user is None:
        return

    now = timezone.now()
    path = ((getattr(request, "path", "") or "")[:240] if request else "")

    try:
        log_id = request.session.get("_gh_access_log_id") if request else None
        updated = 0

        if log_id:
            updated = UserAccessLog.objects.filter(
                pk=log_id,
                user=user,
                logout_at__isnull=True,
            ).update(
                logout_at=now,
                last_seen_at=now,
                last_path=path,
            )

        if not updated:
            latest_open = UserAccessLog.objects.filter(
                user=user,
                logout_at__isnull=True,
            ).order_by("-login_at").first()
            if latest_open:
                UserAccessLog.objects.filter(pk=latest_open.pk).update(
                    logout_at=now,
                    last_seen_at=now,
                    last_path=path,
                )
    except (OperationalError, ProgrammingError):
        return
