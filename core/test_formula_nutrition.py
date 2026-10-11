from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .nutrition import normalize_product_labels, nutrition_reference_products


class FormulaNutritionReferenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="nutrition-test", password="nutrition-test-password")
        self.client.force_login(self.user)

    def test_nutrition_product_reference_values_and_scoops(self):
        frisolac, maxijul = nutrition_reference_products()
        self.assertEqual(frisolac["name"], "Frisolac AC")
        self.assertEqual(frisolac["kcal_per_100g"], Decimal("503"))
        self.assertEqual(frisolac["carbs_per_100g"], Decimal("56.2"))
        self.assertEqual(frisolac["scoop_g"], Decimal("4.33"))
        self.assertEqual(frisolac["kcal_per_scoop"], Decimal("21.78"))
        self.assertEqual(frisolac["carbs_per_scoop"], Decimal("2.43"))
        self.assertEqual(maxijul["name"], "Super Soluble Maxijul")
        self.assertEqual(maxijul["kcal_per_100g"], Decimal("380"))
        self.assertEqual(maxijul["carbs_per_100g"], Decimal("95"))
        self.assertEqual(maxijul["scoop_g"], Decimal("5"))
        self.assertEqual(maxijul["kcal_per_scoop"], Decimal("19.00"))
        self.assertEqual(maxijul["carbs_per_scoop"], Decimal("4.75"))

    def test_readonly_nutrition_reference_has_health_hub_link(self):
        response = self.client.get(reverse("formula_nutrition"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frisolac AC")
        self.assertContains(response, "Super Soluble Maxijul")
        self.assertContains(response, "503")
        self.assertContains(response, "56.2")
        self.assertContains(response, "4.33")
        self.assertContains(response, "Κλινική Παιδιατρική Διαιτολόγος")
        self.assertContains(self.client.get(reverse("health_hub")), reverse("formula_nutrition"))

    def test_normalization_keeps_clinical_quantities_unchanged(self):
        raw = "190 ml + 6 μεζούρες Frysolac AC + 1 κουταλιά Maxijul (5 g) - διατροφολόγου"
        corrected = normalize_product_labels(raw)
        self.assertEqual(
            corrected,
            "190 ml + 6 μεζούρες Frisolac AC + 1 κουταλιά Maxijul (5 g) - κλινικής διαιτολόγου",
        )
