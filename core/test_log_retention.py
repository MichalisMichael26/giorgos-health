from datetime import datetime, timedelta, timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core.log_retention import prune_expired_doctor_access_logs
from core.models import DoctorPageViewLog, UserAccessLog, UserAccessProfile
from core.signals import _json_value


class AuditDatetimeTests(TestCase):
    def test_same_instant_uses_same_audit_value(self):
        utc_value = datetime(2026, 10, 29, 5, tzinfo=dt_timezone.utc)
        cyprus_value = utc_value.astimezone(dt_timezone(timedelta(hours=2)))
        self.assertEqual(_json_value(utc_value), _json_value(cyprus_value))


class DoctorAccessRetentionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.doctor = User.objects.create_user(username="test_doctor")
        self.parent = User.objects.create_user(username="test_parent")
        UserAccessProfile.objects.create(user=self.doctor, role="doctor_readonly")
        UserAccessProfile.objects.create(user=self.parent, role="parent")

    def _session(self, user, when):
        return UserAccessLog.objects.create(
            user=user, login_at=when, last_seen_at=when,
            entry_source="login",
        )

    def _view(self, user, session, when):
        view = DoctorPageViewLog.objects.create(
            user=user, access_log=session, path="/doctor/",
            view_name="doctor_view",
        )
        DoctorPageViewLog.objects.filter(pk=view.pk).update(viewed_at=when)
        return view

    def test_prunes_only_expired_doctor_activity(self):
        now = timezone.now()
        old = now - timedelta(days=20)
        recent = now - timedelta(days=3)

        old_session = self._session(self.doctor, old)
        old_view = self._view(self.doctor, old_session, old)
        recent_session = self._session(self.doctor, recent)
        recent_view = self._view(self.doctor, recent_session, recent)
        parent_session = self._session(self.parent, old)

        dry_run = prune_expired_doctor_access_logs(now=now, dry_run=True)
        self.assertEqual(dry_run["page_views"], 1)
        self.assertEqual(dry_run["sessions"], 1)
        self.assertTrue(UserAccessLog.objects.filter(pk=old_session.pk).exists())

        result = prune_expired_doctor_access_logs(now=now)
        self.assertEqual(result["page_views"], 1)
        self.assertEqual(result["sessions"], 1)
        self.assertFalse(DoctorPageViewLog.objects.filter(pk=old_view.pk).exists())
        self.assertFalse(UserAccessLog.objects.filter(pk=old_session.pk).exists())
        self.assertTrue(DoctorPageViewLog.objects.filter(pk=recent_view.pk).exists())
        self.assertTrue(UserAccessLog.objects.filter(pk=recent_session.pk).exists())
        self.assertTrue(UserAccessLog.objects.filter(pk=parent_session.pk).exists())

    def test_recent_view_protects_older_session_from_cascade(self):
        now = timezone.now()
        old = now - timedelta(days=20)
        recent = now - timedelta(days=1)
        session = self._session(self.doctor, old)
        view = self._view(self.doctor, session, recent)
        prune_expired_doctor_access_logs(now=now)
        self.assertTrue(UserAccessLog.objects.filter(pk=session.pk).exists())
        self.assertTrue(DoctorPageViewLog.objects.filter(pk=view.pk).exists())
