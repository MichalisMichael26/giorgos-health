from django.contrib.auth import logout
from django.db import OperationalError, ProgrammingError
from django.shortcuts import redirect
from django.utils import timezone

from .access import is_readonly_doctor
from .models import UserAccessLog, UserAccessProfile


SESSION_LOG_ID = "_gh_access_log_id"
SESSION_LAST_WRITE = "_gh_access_last_seen_write"
SESSION_DOCTOR_STARTED_AT = "_gh_doctor_started_at"
WRITE_INTERVAL_SECONDS = 5 * 60
DOCTOR_SESSION_SECONDS = 5 * 60


def _user_agent(request):
    return (request.META.get("HTTP_USER_AGENT") or "")[:500]


def _safe_path(request):
    return (getattr(request, "path", "") or "")[:240]


def _device_type(user_agent):
    ua = (user_agent or "").casefold()
    if not ua:
        return "unknown"
    if "ipad" in ua or "tablet" in ua or ("android" in ua and "mobile" not in ua):
        return "tablet"
    if "iphone" in ua or "ipod" in ua or "mobile" in ua or "android" in ua:
        return "mobile"
    return "desktop"


class AccessActivityMiddleware:
    """
    Access tracking + doctor session control.

    - A real login is created by the Django user_logged_in signal.
    - If a user already had a persistent session when this feature was deployed,
      the first observed authenticated request creates an "existing_session"
      access-log row.
    - last_seen is written at most once every 5 minutes to avoid unnecessary
      database writes on every page request.
    - Every read-only doctor account has a hard 5-minute session limit on
      desktop, mobile and tablet. After that the doctor is logged out and must
      authenticate again, creating a new UserAccessLog login entry.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timeout_response = self._enforce_doctor_session_limit(request)
        if timeout_response is not None:
            return timeout_response

        self._touch(request)
        return self.get_response(request)

    def _enforce_doctor_session_limit(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not is_readonly_doctor(user):
            return None

        now_ts = int(timezone.now().timestamp())

        try:
            started_ts = int(
                request.session.get(SESSION_DOCTOR_STARTED_AT, 0) or 0
            )
        except (TypeError, ValueError):
            started_ts = 0

        if not started_ts:
            started_ts = now_ts
            request.session[SESSION_DOCTOR_STARTED_AT] = started_ts

        elapsed = max(now_ts - started_ts, 0)
        remaining = max(DOCTOR_SESSION_SECONDS - elapsed, 0)

        # Expose the server-calculated remaining time to templates so the
        # browser can automatically submit logout on desktop, mobile or tablet
        # even if the doctor stays on the same page without another request.
        request.doctor_session_remaining_seconds = remaining

        if elapsed >= DOCTOR_SESSION_SECONDS:
            logout(request)
            return redirect("login")

        return None

    def _touch(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not is_readonly_doctor(user):
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
