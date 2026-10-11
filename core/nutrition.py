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


# Previous confirmed dilution (5 formula scoops + 5 g Maxijul, about 175 ml)
# and current dilution (6 formula scoops + 5 g Maxijul, about 205 ml).
# Other preparations require their final prepared volume to be recorded.
KNOWN_PREPARATIONS_ML = {
    (Decimal("6"), Decimal("1")): Decimal("205"),
    (Decimal("5"), Decimal("1")): Decimal("175"),
}


def _quantity_in_scoops(value, scoop_size_g, *, empty_is_zero=False):
    """Safely interpret historic meal strings; never guess from unknown text."""
    text = str(value or "").strip().lower().replace(",", ".")
    if not text:
        return Decimal("0") if empty_is_zero else None
    if text in {"0", "0.0", "χωρίς", "none", "no"}:
        return Decimal("0")

    # A grams-only supplement entry (e.g. '5 g') is not five scoops.
    grams_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:g|gr|γραμμάρια)", text)
    if grams_match:
        return Decimal(grams_match.group(1)) / scoop_size_g

    match = re.search(r"(?<!\w)(\d+(?:\.\d+)?)(?!\w)", text)
    if not match:
        return None
    quantity = Decimal(match.group(1))
    return quantity if Decimal("0") <= quantity <= Decimal("30") else None


def estimate_meal_energy(meal):
    """Estimate consumed dry-powder kcal/carbs by volume fraction.

    Includes Frisolac AC and Super Soluble Maxijul, but not other ingredients.
    A reported ml amount must be the combined oral + NG tube volume.
    This intentionally never double-counts the same ml by feeding route.
    """
    missing = {"kcal": None, "carbs_g": None, "frisolac_kcal": None,
               "maxijul_kcal": None, "prepared_volume_ml": None, "reason": "incomplete"}
    if meal.status == "missed" or meal.consumed_ml is None:
        return missing

    formula_scoops = _quantity_in_scoops(getattr(meal, "formula", ""), Decimal("4.33"))
    maxijul_scoops = _quantity_in_scoops(
        getattr(meal, "supplement", ""), Decimal("5"), empty_is_zero=True
    )
    if formula_scoops is None or maxijul_scoops is None or formula_scoops <= 0:
        return missing

    prepared_volume = getattr(meal, "prepared_volume_ml", None)
    if prepared_volume is None:
        prepared_volume = KNOWN_PREPARATIONS_ML.get((formula_scoops, maxijul_scoops))
    if prepared_volume is None:
        return missing
    prepared_volume = Decimal(str(prepared_volume))
    if prepared_volume <= 0:
        return missing

    consumed = Decimal(str(meal.consumed_ml))
    if consumed < 0:
        return missing
    formula_g = formula_scoops * PRODUCTS[0]["scoop_g"]
    maxijul_g = maxijul_scoops * PRODUCTS[1]["scoop_g"]
    frisolac_kcal = formula_g * PRODUCTS[0]["kcal_per_100g"] / Decimal("100")
    maxijul_kcal = maxijul_g * PRODUCTS[1]["kcal_per_100g"] / Decimal("100")
    carbs = (
        formula_g * PRODUCTS[0]["carbs_per_100g"]
        + maxijul_g * PRODUCTS[1]["carbs_per_100g"]
    ) / Decimal("100")
    portion = consumed / prepared_volume
    one_decimal = lambda x: x.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return {
        "kcal": one_decimal((frisolac_kcal + maxijul_kcal) * portion),
        "carbs_g": one_decimal(carbs * portion),
        "frisolac_kcal": one_decimal(frisolac_kcal * portion),
        "maxijul_kcal": one_decimal(maxijul_kcal * portion),
        "prepared_volume_ml": prepared_volume,
        "reason": "estimated",
    }


def summarize_meal_energy(meals):
    """Do not present a partial computed sum as the complete daily intake."""
    total_kcal = Decimal("0")
    total_carbs = Decimal("0")
    counted_ml = 0
    missing_ml = 0
    count = 0
    missing_count = 0
    for meal in meals:
        if meal.status == "missed" or meal.consumed_ml is None:
            continue
        value = estimate_meal_energy(meal)
        if value["kcal"] is None:
            missing_count += 1
            missing_ml += meal.consumed_ml
            continue
        total_kcal += value["kcal"]
        total_carbs += value["carbs_g"]
        counted_ml += meal.consumed_ml
        count += 1
    return {
        "kcal": total_kcal.quantize(Decimal("0.1")),
        "carbs_g": total_carbs.quantize(Decimal("0.1")),
        "counted_ml": counted_ml,
        "missing_ml": missing_ml,
        "count": count,
        "missing_count": missing_count,
        "complete": missing_count == 0 and count > 0,
        "has_data": count > 0,
    }
