from django.contrib.auth import logout
from django.db import OperationalError, ProgrammingError
from django.shortcuts import redirect
from django.utils import timezone

from .access import is_readonly_doctor
from .models import DoctorPageViewLog, UserAccessLog, UserAccessProfile


SESSION_LOG_ID = "_gh_access_log_id"
SESSION_LAST_WRITE = "_gh_access_last_seen_write"
SESSION_DOCTOR_STARTED_AT = "_gh_doctor_started_at"
WRITE_INTERVAL_SECONDS = 5 * 60
DOCTOR_SESSION_SECONDS = 5 * 60


def _user_agent(request):
    return (request.META.get("HTTP_USER_AGENT") or "")[:500]


def _safe_path(request):
    return (getattr(request, "path", "") or "")[:240]


def _is_background_path(path):
    return (
        path == "/service-worker.js"
        or path.startswith("/push/")
        or path.startswith("/static/")
        or path.startswith("/native/")
    )


class AccessActivityMiddleware:
    """
    Doctor-only access tracking + hard session control.

    - Every doctor login creates a UserAccessLog row.
    - Doctor accounts have a hard 5-minute session limit on desktop, mobile,
      and tablet. After that they must authenticate again.
    - Each real page opened by a doctor is recorded in DoctorPageViewLog with
      timestamp, URL path and Django view name.
    - Background/service-worker/push requests are intentionally excluded.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timeout_response = self._enforce_doctor_session_limit(request)
        if timeout_response is not None:
            return timeout_response

        self._touch(request)
        response = self.get_response(request)
        self._record_page_view(request, response)
        return response

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

        request.doctor_session_remaining_seconds = remaining

        if elapsed >= DOCTOR_SESSION_SECONDS:
            logout(request)
            return redirect("login")

        return None

    def _get_or_create_access_log(self, request, now, path):
        user = request.user
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

        return log

    def _touch(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not is_readonly_doctor(user):
            return

        path = _safe_path(request)
        if _is_background_path(path):
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

            log = self._get_or_create_access_log(request, now, path)
            UserAccessLog.objects.filter(pk=log.pk).update(
                last_seen_at=now,
                last_path=path,
            )
            request.session[SESSION_LAST_WRITE] = now_ts
        except (OperationalError, ProgrammingError):
            return

    def _record_page_view(self, request, response):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not is_readonly_doctor(user):
            return

        if request.method != "GET":
            return

        path = _safe_path(request)
        if _is_background_path(path):
            return

        status_code = getattr(response, "status_code", 500)
        if status_code >= 400:
            return

        try:
            now = timezone.now()
            log = self._get_or_create_access_log(request, now, path)
            match = getattr(request, "resolver_match", None)
            view_name = ((match.url_name if match else "") or "")[:120]

            DoctorPageViewLog.objects.create(
                access_log=log,
                user=user,
                path=path,
                view_name=view_name,
            )

            UserAccessLog.objects.filter(pk=log.pk).update(
                last_seen_at=now,
                last_path=path,
            )

            profile, _ = UserAccessProfile.objects.get_or_create(user=user)
            UserAccessProfile.objects.filter(pk=profile.pk).update(
                last_seen_at=now,
                last_seen_path=path,
                last_seen_user_agent=_user_agent(request),
            )
        except (OperationalError, ProgrammingError):
            # During the deploy that introduces the page-view table, requests
            # must continue to work before/while migrations finish.
            return
