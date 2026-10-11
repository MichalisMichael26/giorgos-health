"""Read-only product nutrition references as supplied by the clinical dietitian.

All values refer to 100 g of DRY powder, never to 100 ml of prepared milk.
No treatment, dosing, or daily intake target is calculated here.
"""
from decimal import Decimal, ROUND_HALF_UP
import re

PRODUCTS = (
    {
        "name": "Frisolac AC",
        "kcal_per_100g": Decimal("503"),
        "carbs_per_100g": Decimal("56.2"),
        "scoop_g": Decimal("4.33"),
    },
    {
        "name": "Super Soluble Maxijul",
        "kcal_per_100g": Decimal("380"),
        "carbs_per_100g": Decimal("95"),
        "scoop_g": Decimal("5"),
    },
)


def nutrition_reference_products():
    """Product data plus simple per-scoop arithmetic, not a feeding prescription."""
    result = []
    for product in PRODUCTS:
        item = dict(product)
        item["kcal_per_scoop"] = (
            product["kcal_per_100g"] * product["scoop_g"] / 100
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        item["carbs_per_scoop"] = (
            product["carbs_per_100g"] * product["scoop_g"] / 100
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        result.append(item)
    return result


def normalize_product_labels(value):
    """Fix display typos only; never change quantities or feeding intervals."""
    value = str(value or "")
    value = re.sub(r"\bFrysolac\b", "Frisolac", value, flags=re.IGNORECASE)
    value = re.sub(r"\bδιατροφολόγος\b", "κλινική διαιτολόγος", value, flags=re.IGNORECASE)
    value = re.sub(r"\bδιατροφολόγου\b", "κλινικής διαιτολόγου", value, flags=re.IGNORECASE)
    value = re.sub(r"\bδιατροφολόγο\b", "κλινική διαιτολόγο", value, flags=re.IGNORECASE)
    return value
