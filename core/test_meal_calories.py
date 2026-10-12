from datetime import date, time, timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import MealEntry
from .nutrition import estimate_meal_energy, summarize_meal_energy


def sample_meal(consumed, formula="6", supplement="1 κουταλιά (5 g)",
                prepared_volume=None, status="completed", ng=False):
    return SimpleNamespace(
        consumed_ml=consumed, formula=formula, supplement=supplement,
        prepared_volume_ml=prepared_volume, status=status,
        nasogastric_tube_used=ng,
    )


class MealEnergyUnitTests(SimpleTestCase):
    def test_standard_current_recipe_full_bottle(self):
        value = estimate_meal_energy(sample_meal(205))
        self.assertEqual(value["kcal"], Decimal("149.7"))
        self.assertEqual(value["carbs_g"], Decimal("19.4"))
        self.assertEqual(value["frisolac_kcal"], Decimal("130.7"))
        self.assertEqual(value["maxijul_kcal"], Decimal("19.0"))
        self.assertEqual(value["prepared_volume_ml"], Decimal("205"))

    def test_consumed_ml_controls_calories(self):
        self.assertEqual(estimate_meal_energy(sample_meal(100))["kcal"], Decimal("73.0"))
        self.assertEqual(estimate_meal_energy(sample_meal(150))["kcal"], Decimal("109.5"))
        self.assertEqual(estimate_meal_energy(sample_meal(0))["kcal"], Decimal("0.0"))

    def test_ng_and_bottle_not_counted_twice(self):
        value = estimate_meal_energy(sample_meal(100, ng=True))
        self.assertEqual(value["kcal"], Decimal("73.0"))

    def test_previous_known_dilution(self):
        self.assertEqual(
            estimate_meal_energy(sample_meal(175, formula="5"))["kcal"],
            Decimal("127.9"),
        )

    def test_custom_prep_requires_volume(self):
        missing = estimate_meal_energy(sample_meal(90, formula="4", supplement="0"))
        self.assertIsNone(missing["kcal"])
        custom = estimate_meal_energy(
            sample_meal(90, formula="4", supplement="0", prepared_volume=180)
        )
        self.assertEqual(custom["kcal"], Decimal("43.6"))

    def test_grams_only_maxijul_does_not_mean_five_scoops(self):
        self.assertEqual(
            estimate_meal_energy(sample_meal(205, supplement="5 g"))["kcal"],
            Decimal("149.7"),
        )

    def test_unrecorded_missed_unknown_are_never_zero(self):
        self.assertIsNone(estimate_meal_energy(sample_meal(None))["kcal"])
        self.assertIsNone(estimate_meal_energy(sample_meal(120, status="missed"))["kcal"])
        self.assertIsNone(estimate_meal_energy(sample_meal(120, formula="unknown"))["kcal"])

    def test_partial_totals_are_explicit(self):
        summary = summarize_meal_energy([
            sample_meal(100),
            sample_meal(80, formula="unknown"),
            sample_meal(50, ng=True),
        ])
        self.assertEqual(summary["kcal"], Decimal("109.5"))
        self.assertEqual(summary["counted_ml"], 150)
        self.assertEqual(summary["missing_ml"], 80)
        self.assertEqual(summary["missing_count"], 1)
        self.assertFalse(summary["complete"])


class MealEnergyDisplayTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("energy-test", password="unit-test-password")
        self.client.force_login(self.user)

    def test_meal_list_shows_calories_for_saved_record(self):
        MealEntry.objects.create(
            date=date(2026, 10, 11),
            scheduled_time=time(11, 0),
            offered_ml=205,
            consumed_ml=100,
            formula="6",
            supplement="1 κουταλιά (5 g)",
            status="partial",
        )
        response = self.client.get(reverse("meal_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "73")
        self.assertContains(response, "kcal")

    def test_optional_prepared_volume_persists(self):
        meal = MealEntry.objects.create(
            date=date(2026, 10, 11), scheduled_time=time(11, 0),
            formula="4", supplement="0", offered_ml=180, consumed_ml=90,
            prepared_volume_ml=180,
        )
        meal.refresh_from_db()
        self.assertEqual(meal.prepared_volume_ml, 180)
        self.assertEqual(meal.energy_estimate["kcal"], Decimal("43.6"))


class MealEnergyChartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("energy-chart-test", password="unit-test-password")
        self.client.force_login(self.user)
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        # A fully documented oral/NG meal: only the combined consumed ml count.
        MealEntry.objects.create(
            date=yesterday, scheduled_time=time(12, 0),
            formula="6", supplement="1 κουταλιά (5 g)",
            consumed_ml=100, offered_ml=205, nasogastric_tube_used=True,
            status="partial",
        )
        # An incomplete preparation on the following date means the entire
        # daily calorie bar must be missing, not a misleading partial total.
        MealEntry.objects.create(
            date=today, scheduled_time=time(9, 0),
            formula="6", supplement="1", consumed_ml=100,
            status="partial",
        )
        MealEntry.objects.create(
            date=today, scheduled_time=time(12, 0),
            formula="unknown", supplement="1", consumed_ml=40,
            status="partial",
        )

    def test_analytics_calories_for_every_supported_period(self):
        for period in ("7", "30", "90", "all"):
            with self.subTest(period=period):
                response = self.client.get(reverse("analytics"), {"period": period})
                self.assertEqual(response.status_code, 200)
                chart = response.context["chart_data"]
                self.assertEqual(chart["daily_kcal"][-2], 73.0)
                self.assertIsNone(chart["daily_kcal"][-1])
                self.assertEqual(chart["daily_kcal_missing_days"], 1)
                self.assertContains(response, "Θερμίδες ανά ημέρα")

    def test_feeding_performance_calories_and_missing_day(self):
        response = self.client.get(reverse("feeding_performance"), {"period": "7"})
        self.assertEqual(response.status_code, 200)
        chart = response.context["chart_data"]
        self.assertEqual(chart["kcal"][-2], 73.0)
        self.assertIsNone(chart["kcal"][-1])
        self.assertEqual(chart["kcal_missing_days"], 1)
        self.assertContains(response, "Ελλιπή στοιχεία")
