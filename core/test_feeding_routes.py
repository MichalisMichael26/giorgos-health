from datetime import datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .advanced_views import feeding_stats
from .feeding_timing import default_meal_route
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


class RouteDefaultsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("defaults-test", password="defaults-test-pass")
        self.client.force_login(self.user)

    def test_boundary_night_starts_at_2200_and_includes_0730(self):
        for at, expect_tube in (
            (time(21, 59), False),
            (time(22, 0), True),
            (time(23, 59), True),
            (time(0, 0), True),
            (time(7, 29), True),
            (time(7, 30), True),
            (time(7, 31), False),
            (time(12, 0), False),
        ):
            with self.subTest(at=at):
                route = default_meal_route(at, 205)
                self.assertEqual(route["tube_ml"], 205 if expect_tube else 0)
                self.assertEqual(route["oral_ml"], 0 if expect_tube else 205)
                self.assertEqual(route["tube_route"], "ngt" if expect_tube else "")

    def test_initial_values_on_create_and_manual_edit_unaffected(self):
        for at, tube_expected in ((time(7, 30), 205), (time(7, 31), 0)):
            with self.subTest(at=at):
                due = timezone.make_aware(
                    datetime.combine(timezone.localdate(), at),
                    timezone.get_current_timezone(),
                )
                with patch("core.views.next_scheduled_datetime", return_value=due):
                    response = self.client.get(reverse("meal_create"))
                self.assertEqual(response.status_code, 200)
                initial = response.context["form"].initial
                self.assertEqual(initial["tube_ml"], tube_expected)
                self.assertEqual(initial["oral_ml"], 205 - tube_expected)
                self.assertContains(response, 'data-new-meal-route-defaults="true"')

        meal = MealEntry.objects.create(
            date=timezone.localdate(), scheduled_time=time(7, 30),
            consumed_ml=120, oral_ml=100, tube_ml=20, tube_route="ngt",
        )
        response = self.client.get(reverse("meal_edit", args=[meal.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-new-meal-route-defaults="false"')
        self.assertEqual(response.context["form"].instance.oral_ml, 100)
        self.assertEqual(response.context["form"].instance.tube_ml, 20)

    def test_invalid_post_keeps_user_values(self):
        data = meal_data(oral_ml="150", tube_ml="100")
        response = self.client.post(reverse("meal_create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-new-meal-route-defaults="false"')
        self.assertEqual(response.context["form"]["oral_ml"].value(), "150")
