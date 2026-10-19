"""Daily feeding-route volumes for charts, without guessing historic splits."""

from collections import defaultdict


ROUTE_KEYS = ("oral", "ngt", "gastrostomy", "unknown")


def daily_route_totals(meals):
    """Return known ml by route, keeping legacy/inconsistent splits unknown.

    A pre-route meal may only record its combined consumed_ml (even when the
    legacy nasogastric checkbox was selected). It would be misleading to label
    all of that milk as oral or via tube. Each meal counts exactly once.
    """
    totals = defaultdict(lambda: {key: 0 for key in ROUTE_KEYS})
    for meal in meals:
        if meal.consumed_ml is None:
            continue
        total = int(meal.consumed_ml)
        daily = totals[meal.date]
        oral, tube = meal.oral_ml, meal.tube_ml
        if oral is None or tube is None or oral + tube != total:
            daily["unknown"] += total
            continue
        daily["oral"] += oral
        if tube:
            route = meal.tube_route if meal.tube_route in ("ngt", "gastrostomy") else "unknown"
            daily[route] += tube
    return totals
