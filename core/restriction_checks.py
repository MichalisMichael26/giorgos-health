import unicodedata


BASELINE_RESTRICTIONS = [
    {
        "key": "lactose",
        "label": "Λακτόζη",
        "terms": ["λακτόζη", "lactose"],
    },
    {
        "key": "sugar",
        "label": "Ζάχαρη",
        "terms": ["ζάχαρη", "sugar"],
    },
    {
        "key": "fructose",
        "label": "Φρουκτόζη",
        "terms": ["φρουκτόζη", "fructose"],
    },
]


def normalize_restriction_text(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.casefold().split())


def baseline_restriction_checks(text):
    """
    Check only the three explicitly configured ingredient restrictions:
    lactose, sugar and fructose.

    This is a literal ingredient-text check. It does not make a broader
    medical-safety conclusion about the product.
    """
    normalized = normalize_restriction_text(text)
    has_ingredients = bool(normalized)
    rows = []

    for restriction in BASELINE_RESTRICTIONS:
        matched_terms = []
        for term in restriction["terms"]:
            normalized_term = normalize_restriction_text(term)
            if normalized_term and normalized_term in normalized:
                matched_terms.append(term)

        rows.append(
            {
                "key": restriction["key"],
                "label": restriction["label"],
                "detected": bool(matched_terms) if has_ingredients else None,
                "matched_terms": matched_terms,
            }
        )

    return rows
