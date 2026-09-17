from datetime import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import GlucoseReadingForm, GrowthMeasurementForm, MealEntryForm
from .models import GlucoseReading, GrowthMeasurement, MealEntry


SCHEDULED_TIMES = [
    time(1, 30),
    time(4, 30),
    time(7, 30),
    time(10, 30),
    time(13, 30),
    time(16, 30),
    time(19, 30),
    time(22, 30),
]


def next_scheduled_time(now_local):
    current = now_local.time().replace(second=0, microsecond=0)
    for scheduled in SCHEDULED_TIMES:
        if scheduled >= current:
            return scheduled
    return SCHEDULED_TIMES[0]


@login_required
def dashboard(request):
    today = timezone.localdate()
    meals_today = MealEntry.objects.filter(date=today).order_by("scheduled_time")
    glucose_today = GlucoseReading.objects.filter(date=today).order_by("time")

    context = {
        "today": today,
        "meals_today": meals_today,
        "glucose_today": glucose_today,
        "latest_glucose": GlucoseReading.objects.first(),
        "latest_growth": GrowthMeasurement.objects.first(),
        "consumed_total": sum(item.consumed_ml or 0 for item in meals_today),
        "next_meal_time": next_scheduled_time(timezone.localtime()),
        "schedule": SCHEDULED_TIMES,
    }
    return render(request, "dashboard.html", context)


@login_required
def meal_list(request):
    return render(request, "meals/list.html", {"meals": MealEntry.objects.all()})


@login_required
def meal_create(request):
    form = MealEntryForm(
        request.POST or None,
        initial={
            "date": timezone.localdate(),
            "scheduled_time": next_scheduled_time(timezone.localtime()),
        },
    )
    if form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, "Το γεύμα αποθηκεύτηκε.")
        return redirect("meal_list")
    return render(request, "form.html", {"form": form, "title": "Νέο γεύμα"})


@login_required
def meal_edit(request, pk):
    item = get_object_or_404(MealEntry, pk=pk)
    form = MealEntryForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Το γεύμα ενημερώθηκε.")
        return redirect("meal_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία γεύματος"})


@login_required
def meal_delete(request, pk):
    item = get_object_or_404(MealEntry, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Το γεύμα διαγράφηκε.")
        return redirect("meal_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή γεύματος"})


@login_required
def glucose_list(request):
    readings = GlucoseReading.objects.select_related("related_meal").all()
    return render(request, "glucose/list.html", {"readings": readings})


@login_required
def glucose_create(request):
    form = GlucoseReadingForm(
        request.POST or None,
        initial={
            "date": timezone.localdate(),
            "time": timezone.localtime().strftime("%H:%M"),
            "context": "pre_feed",
        },
    )
    if form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, "Η μέτρηση γλυκόζης αποθηκεύτηκε.")
        return redirect("glucose_list")
    return render(request, "form.html", {"form": form, "title": "Νέα μέτρηση γλυκόζης"})


@login_required
def glucose_edit(request, pk):
    item = get_object_or_404(GlucoseReading, pk=pk)
    form = GlucoseReadingForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Η μέτρηση γλυκόζης ενημερώθηκε.")
        return redirect("glucose_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία γλυκόζης"})


@login_required
def glucose_delete(request, pk):
    item = get_object_or_404(GlucoseReading, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Η μέτρηση γλυκόζης διαγράφηκε.")
        return redirect("glucose_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή μέτρησης γλυκόζης"})


@login_required
def growth_list(request):
    return render(
        request,
        "growth/list.html",
        {"measurements": GrowthMeasurement.objects.all()},
    )


@login_required
def growth_create(request):
    form = GrowthMeasurementForm(
        request.POST or None,
        initial={"date": timezone.localdate()},
    )
    if form.is_valid():
        form.save()
        messages.success(request, "Η μέτρηση ανάπτυξης αποθηκεύτηκε.")
        return redirect("growth_list")
    return render(request, "form.html", {"form": form, "title": "Νέα μέτρηση ανάπτυξης"})


@login_required
def growth_edit(request, pk):
    item = get_object_or_404(GrowthMeasurement, pk=pk)
    form = GrowthMeasurementForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Η μέτρηση ανάπτυξης ενημερώθηκε.")
        return redirect("growth_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία ανάπτυξης"})


@login_required
def growth_delete(request, pk):
    item = get_object_or_404(GrowthMeasurement, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Η μέτρηση ανάπτυξης διαγράφηκε.")
        return redirect("growth_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή μέτρησης ανάπτυξης"})
