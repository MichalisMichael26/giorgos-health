from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .advanced_views import dashboard_extras
from .models import HealthReminder


class DashboardReminderWindowTests(TestCase):
    def make_reminder(self, title, offset_days, **kwargs):
        return HealthReminder.objects.create(
            title=title,
            reminder_type="other",
            due_at=timezone.now() + timedelta(days=offset_days),
            **kwargs,
        )

    def test_home_only_shows_reminders_within_one_week(self):
        recent_overdue = self.make_reminder("Overdue six days", -6)
        upcoming = self.make_reminder("Due in six days", 6)
        stale = self.make_reminder("Overdue eight days", -8)
        distant = self.make_reminder("Due in eight days", 8)
        completed = self.make_reminder("Completed tomorrow", 1, completed=True)
        inactive = self.make_reminder("Inactive tomorrow", 1, active=False)

        shown = dashboard_extras(timezone.localdate())["custom_reminders"]
        shown_ids = {reminder.pk for reminder in shown}

        self.assertEqual(shown_ids, {recent_overdue.pk, upcoming.pk})
        self.assertNotIn(stale.pk, shown_ids)
        self.assertNotIn(distant.pk, shown_ids)
        self.assertNotIn(completed.pk, shown_ids)
        self.assertNotIn(inactive.pk, shown_ids)

        # Hiding a reminder on the dashboard must never delete its record.
        self.assertEqual(HealthReminder.objects.count(), 6)
