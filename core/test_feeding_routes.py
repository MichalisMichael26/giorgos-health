from datetime import time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .advanced_views import feeding_stats
from .forms import MealEntryForm
from .models import MealEntry


def meal_data(**updates):
    values = {
        "date": timezone.localdate().isoformat(),
        "scheduled_time": "12:00", "actual_time": "12:00",
        "status": "partial", "offered_ml": "205", "remaining_ml": "5",
        "consumed_ml": "200", "oral_ml": "80", "tube_ml": "120",
        "tube_route": "ngt",
    }
    values.update(updates)
    return values


class RouteFormTests(TestCase):
    def test_split_saved_and_total_preserved(self):
        form = MealEntryForm(data=meal_data())
        self.assertTrue(form.is_valid(), form.errors)
        meal = form.save()
        self.assertEqual((meal.oral_ml, meal.tube_ml, meal.consumed_ml), (80, 120, 200))
        self.assertEqual(meal.tube_route, "ngt")
        self.assertTrue(meal.nasogastric_tube_used)

    def test_gastrostomy_does_not_enable_legacy_ng_checkbox(self):
        form = MealEntryForm(data=meal_data(tube_route="gastrostomy"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.save().nasogastric_tube_used)

    def test_reject_mismatch_and_tube_without_route(self):
        self.assertFalse(MealEntryForm(data=meal_data(oral_ml="70")).is_valid())
        form = MealEntryForm(data=meal_data(tube_route=""))
        self.assertFalse(form.is_valid())
        self.assertIn("tube_route", form.errors)

    def test_new_entry_requires_breakdown(self):
        form = MealEntryForm(data=meal_data(oral_ml="", tube_ml="", tube_route=""))
        self.assertFalse(form.is_valid())
        self.assertIn("oral_ml", form.errors)

    def test_previous_unsplit_meal_can_still_be_edited(self):
        meal = MealEntry.objects.create(
            date=timezone.localdate(), scheduled_time=time(12, 0),
            consumed_ml=200, offered_ml=205, remaining_ml=5,
            nasogastric_tube_used=True,
        )
        form = MealEntryForm(data=meal_data(oral_ml="", tube_ml="", tube_route=""), instance=meal)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        meal.refresh_from_db()
        self.assertIsNone(meal.tube_ml)
        self.assertTrue(meal.nasogastric_tube_used)


class FeedingRouteStatsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("route-test", password="route-test-password")
        self.client.force_login(self.user)
        self.today = timezone.localdate()
        yesterday = self.today - timedelta(days=1)
        MealEntry.objects.create(
            date=yesterday, scheduled_time=time(10, 0), offered_ml=205,
            consumed_ml=150, oral_ml=50, tube_ml=100, tube_route="ngt",
            nasogastric_tube_used=True,
        )
        MealEntry.objects.create(
            date=self.today, scheduled_time=time(10, 0), offered_ml=205,
            consumed_ml=50, oral_ml=50, tube_ml=0,
        )
        MealEntry.objects.create(
            date=self.today, scheduled_time=time(13, 0), offered_ml=205,
            consumed_ml=30, nasogastric_tube_used=True,
        )

    def test_daily_mean_uses_days_with_actual_records(self):
        stats = feeding_stats(self.today - timedelta(days=6), self.today)
        self.assertEqual(stats["recorded_days"], 2)
        self.assertEqual(stats["consumed_sum"], 230)
        self.assertEqual(stats["daily_avg_ml"], 115.0)
        self.assertEqual(stats["tube_known_ml"], 100)
        self.assertEqual(stats["split_unknown_count"], 1)

    def test_page_shows_daily_tube_column_and_average(self):
        response = self.client.get(reverse("feeding_performance"), {"period": "7"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Μ.ό. ml / ημέρα")
        self.assertContains(response, "Μέσω σωλήνα")
        self.assertContains(response, "χωρίς κατανομή")
        self.assertEqual(response.context["stats"]["daily_avg_ml"], 115.0)
