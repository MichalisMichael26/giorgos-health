"""Private GSD-Ia emergency and illness discussion draft.

The screen intentionally has no treatment order, approval toggle, public token,
API auto-dose calculation or changes to the established feeding schedule.
It reads the already stored child profile and measurements at each visit.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from .models import GlucoseReading, GrowthMeasurement, NasogastricTubePlan
from .views import get_child_profile


@login_required
def sick_day_plan(request):
    profile = get_child_profile()
    latest_weight = (
        GrowthMeasurement.objects.filter(weight_kg__isnull=False)
        .order_by("-date", "-id")
        .first()
    )
    return render(
        request,
        "health/sick_day_plan.html",
        {
            "profile": profile,
            "latest_weight": latest_weight,
            "latest_glucose": GlucoseReading.objects.order_by("-date", "-time", "-id").first(),
            "ngt_plan": NasogastricTubePlan.objects.filter(child=profile).first(),
            "today": timezone.localdate(),
        },
    )
