"""Retention policy for doctor-only access activity logs.

Keep 14 complete days of session and page-view history. Clinical records,
doctor accounts, access profiles, and the general AuditLog are not changed.
"""

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from .models import DoctorPageViewLog, UserAccessLog


DOCTOR_ACCESS_RETENTION_DAYS = 14


def prune_expired_doctor_access_logs(*, now=None, dry_run=False):
    cutoff = (now or timezone.now()) - timedelta(days=DOCTOR_ACCESS_RETENTION_DAYS)

    expired_views = DoctorPageViewLog.objects.filter(
        user__access_profile__role="doctor_readonly",
        viewed_at__lt=cutoff,
    )

    # A session is eligible only after both its last observed activity and
    # any logged logout are older than the retention cutoff. Do not cascade
    # a recent page view from a stale session.
    expired_sessions = (
        UserAccessLog.objects.filter(
            user__access_profile__role="doctor_readonly",
            login_at__lt=cutoff,
        )
        .filter(Q(last_seen_at__lt=cutoff) | Q(last_seen_at__isnull=True))
        .filter(Q(logout_at__lt=cutoff) | Q(logout_at__isnull=True))
        .exclude(page_views__viewed_at__gte=cutoff)
        .distinct()
    )

    view_count = expired_views.count()
    session_count = expired_sessions.count()

    if not dry_run:
        expired_views.delete()
        expired_sessions.delete()

    return {
        "retention_days": DOCTOR_ACCESS_RETENTION_DAYS,
        "cutoff": cutoff.isoformat(),
        "page_views": view_count,
        "sessions": session_count,
        "dry_run": dry_run,
    }
