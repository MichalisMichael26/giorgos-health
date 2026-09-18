from datetime import date, datetime, time
from decimal import Decimal

from django.db import OperationalError, ProgrammingError
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .audit import get_current_user
from .models import AuditLog


def _tracked_sender(sender):
    sensitive_internal_models = {
        "PushConfig",
        "PushSubscription",
        "PushDeliveryLog",
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
