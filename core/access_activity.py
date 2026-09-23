from django.db import OperationalError, ProgrammingError
from django.utils import timezone

from .models import UserAccessLog, UserAccessProfile


SESSION_LOG_ID = "_gh_access_log_id"
SESSION_LAST_WRITE = "_gh_access_last_seen_write"
WRITE_INTERVAL_SECONDS = 5 * 60


def _user_agent(request):
    return (request.META.get("HTTP_USER_AGENT") or "")[:500]


def _safe_path(request):
    return (getattr(request, "path", "") or "")[:240]


class AccessActivityMiddleware:
    """
    Lightweight access tracking.

    - A real login is created by the Django user_logged_in signal.
    - If a user already had a persistent session when this feature was deployed,
      the first observed authenticated request creates an "existing_session"
      access-log row.
    - last_seen is written at most once every 5 minutes to avoid unnecessary
      database writes on every page request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self._touch(request)
        return self.get_response(request)

    def _touch(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return

        path = _safe_path(request)

        # Service worker / push background traffic should not make a user appear
        # active in the app.
        if path == "/service-worker.js" or path.startswith("/push/"):
            return

        now = timezone.now()
        now_ts = int(now.timestamp())

        try:
            previous_ts = int(request.session.get(SESSION_LAST_WRITE, 0) or 0)
        except (TypeError, ValueError):
            previous_ts = 0

        if previous_ts and now_ts - previous_ts < WRITE_INTERVAL_SECONDS:
            return

        try:
            profile, _ = UserAccessProfile.objects.get_or_create(user=user)
            UserAccessProfile.objects.filter(pk=profile.pk).update(
                last_seen_at=now,
                last_seen_path=path,
                last_seen_user_agent=_user_agent(request),
            )

            log_id = request.session.get(SESSION_LOG_ID)
            log = None
            if log_id:
                log = UserAccessLog.objects.filter(
                    pk=log_id,
                    user=user,
                    logout_at__isnull=True,
                ).first()

            if log is None:
                log = UserAccessLog.objects.create(
                    user=user,
                    login_at=now,
                    last_seen_at=now,
                    entry_source="existing_session",
                    user_agent=_user_agent(request),
                    first_path=path,
                    last_path=path,
                )
                request.session[SESSION_LOG_ID] = log.pk
            else:
                UserAccessLog.objects.filter(pk=log.pk).update(
                    last_seen_at=now,
                    last_path=path,
                )

            request.session[SESSION_LAST_WRITE] = now_ts
        except (OperationalError, ProgrammingError):
            # During deploy/migrations the new tracking tables/columns may not
            # exist for a brief moment. Access to the app must still work.
            return
