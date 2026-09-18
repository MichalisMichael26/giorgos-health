import csv
import io
import json
import zipfile
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote
import unicodedata

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .advanced_forms import (
    DiaperEntryForm,
    EmergencyProfileForm,
    MedicalDocumentForm,
    MedicalDocumentMetadataForm,
    SymptomEntryForm,
    VaccineEntryForm,
    ProductCheckerForm,
    SafetyRuleForm,
    ProductSafetyRecordForm,
)
from .models import (
    AuditLog,
    ChildProfile,
    DiaperEntry,
    GlucoseReading,
    GrowthMeasurement,
    MealEntry,
    MedicalAppointment,
    MedicalDocument,
    MedicationEntry,
    SymptomEntry,
    VaccineEntry,
    SafetyRule,
    ProductSafetyRecord,
)
from .who_growth import (
    HEAD_BOYS,
    LENGTH_HEIGHT_BOYS,
    WEIGHT_BOYS,
    age_months_float,
    chart_payload,
    percentile_band,
)


def get_profile():
    return ChildProfile.objects.first()


def feeding_stats(start_date, end_date):
    meals = list(MealEntry.objects.filter(date__range=(start_date, end_date)).order_by("date", "scheduled_time"))
    count = len(meals)
    consumed_values = [m.consumed_ml for m in meals if m.consumed_ml is not None]
    offered_sum = sum(m.offered_ml or 0 for m in meals)
    consumed_sum = sum(m.consumed_ml or 0 for m in meals)
    avg_consumed = round(sum(consumed_values) / len(consumed_values), 1) if consumed_values else None
    intake_ratio = round(consumed_sum / offered_sum * 100, 1) if offered_sum else None
    completed = sum(1 for m in meals if m.status == "completed")
    partial = sum(1 for m in meals if m.status == "partial")
    missed = sum(1 for m in meals if m.status == "missed")
    return {
        "count": count,
        "offered_sum": offered_sum,
        "consumed_sum": consumed_sum,
        "avg_consumed": avg_consumed,
        "intake_ratio": intake_ratio,
        "completed": completed,
        "partial": partial,
        "missed": missed,
    }


def daily_snapshot(day):
    meals = MealEntry.objects.filter(date=day)
    glucose = GlucoseReading.objects.filter(date=day)
    consumed = sum(item.consumed_ml or 0 for item in meals)
    values = [float(item.value) for item in glucose]
    return {
        "date": day,
        "meal_count": meals.count(),
        "consumed_ml": consumed,
        "glucose_count": len(values),
        "glucose_avg": round(sum(values) / len(values), 1) if values else None,
    }


def dashboard_extras(today):
    yesterday = today - timedelta(days=1)
    today_data = daily_snapshot(today)
    yesterday_data = daily_snapshot(yesterday)

    seven_start = today - timedelta(days=6)
    seven_meals = MealEntry.objects.filter(date__range=(seven_start, today))
    seven_glucose = list(GlucoseReading.objects.filter(date__range=(seven_start, today)))
    seven_meals = list(seven_meals)
    seven_total_ml = sum(item.consumed_ml or 0 for item in seven_meals)
    seven_recorded_days = len({item.date for item in seven_meals}) or 1
    seven_values = [float(item.value) for item in seven_glucose]

    comparison = {
        "today": today_data,
        "yesterday": yesterday_data,
        "ml_delta": today_data["consumed_ml"] - yesterday_data["consumed_ml"],
        "meal_delta": today_data["meal_count"] - yesterday_data["meal_count"],
        "glucose_count_delta": today_data["glucose_count"] - yesterday_data["glucose_count"],
        "seven_day_avg_ml": round(seven_total_ml / seven_recorded_days, 1),
        "seven_day_glucose_avg": round(sum(seven_values) / len(seven_values), 1) if seven_values else None,
    }

    vaccine_reminders = []
    for vaccine in VaccineEntry.objects.filter(next_date__isnull=False).order_by("next_date")[:50]:
        days_until = (vaccine.next_date - today).days
        if days_until <= vaccine.reminder_days_before:
            if days_until < 0:
                overdue = abs(days_until)
                label = f"Εκκρεμεί {overdue} ημέρα/ες"
            elif days_until == 0:
                label = "Σήμερα"
            elif days_until == 1:
                label = "Αύριο"
            else:
                label = f"Σε {days_until} ημέρες"
            vaccine_reminders.append({"object": vaccine, "label": label, "days_until": days_until})

    return {
        "day_comparison": comparison,
        "vaccine_reminders": vaccine_reminders[:5],
        "feeding_today": feeding_stats(today, today),
    }


@login_required
def document_list(request):
    return render(request, "documents/list.html", {"documents": MedicalDocument.objects.all()})


@login_required
def document_create(request):
    form = MedicalDocumentForm(request.POST or None, request.FILES or None, initial={"date": timezone.localdate()})
    if form.is_valid():
        upload = form.cleaned_data["upload"]
        suffix = Path(upload.name).suffix.lower()
        safe_content_type = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }.get(suffix, "application/octet-stream")
        MedicalDocument.objects.create(
            date=form.cleaned_data["date"],
            category=form.cleaned_data["category"],
            title=form.cleaned_data["title"],
            original_filename=Path(upload.name).name,
            content_type=safe_content_type,
            file_size=upload.size,
            data=upload.read(),
            notes=form.cleaned_data["notes"],
            created_by=request.user,
        )
        messages.success(request, "Το έγγραφο αποθηκεύτηκε.")
        return redirect("document_list")
    return render(request, "documents/form.html", {"form": form, "title": "Νέο έγγραφο"})


@login_required
def document_edit(request, pk):
    item = get_object_or_404(MedicalDocument, pk=pk)
    form = MedicalDocumentMetadataForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Τα στοιχεία του εγγράφου ενημερώθηκαν.")
        return redirect("document_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία εγγράφου"})


def _document_response(item, inline):
    if not item.data:
        raise Http404("Το αρχείο δεν βρέθηκε.")
    response = HttpResponse(bytes(item.data), content_type=item.content_type or "application/octet-stream")
    disposition = "inline" if inline else "attachment"
    response["Content-Disposition"] = f"{disposition}; filename*=UTF-8''{quote(item.original_filename)}"
    response["Content-Length"] = str(item.file_size or len(item.data))
    return response


@login_required
def document_view(request, pk):
    return _document_response(get_object_or_404(MedicalDocument, pk=pk), True)


@login_required
def document_download(request, pk):
    return _document_response(get_object_or_404(MedicalDocument, pk=pk), False)


@login_required
def document_delete(request, pk):
    item = get_object_or_404(MedicalDocument, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Το έγγραφο διαγράφηκε.")
        return redirect("document_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή εγγράφου"})


@login_required
def vaccine_list(request):
    today = timezone.localdate()
    return render(request, "vaccines/list.html", {"vaccines": VaccineEntry.objects.all(), "today": today})


@login_required
def vaccine_create(request):
    form = VaccineEntryForm(
        request.POST or None,
        initial={"date": timezone.localdate(), "reminder_days_before": 7},
    )
    if form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, "Το εμβόλιο αποθηκεύτηκε.")
        return redirect("vaccine_list")
    return render(request, "form.html", {"form": form, "title": "Νέο εμβόλιο"})


@login_required
def vaccine_edit(request, pk):
    item = get_object_or_404(VaccineEntry, pk=pk)
    form = VaccineEntryForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Το εμβόλιο ενημερώθηκε.")
        return redirect("vaccine_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία εμβολίου"})


@login_required
def vaccine_delete(request, pk):
    item = get_object_or_404(VaccineEntry, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Η καταχώρηση εμβολίου διαγράφηκε.")
        return redirect("vaccine_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή εμβολίου"})


@login_required
def symptom_list(request):
    return render(request, "symptoms/list.html", {"items": SymptomEntry.objects.all()})


@login_required
def symptom_create(request):
    form = SymptomEntryForm(
        request.POST or None,
        initial={"date": timezone.localdate(), "time": timezone.localtime().strftime("%H:%M")},
    )
    if form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, "Το σύμπτωμα/επεισόδιο αποθηκεύτηκε.")
        return redirect("symptom_list")
    return render(request, "form.html", {"form": form, "title": "Νέο σύμπτωμα / επεισόδιο"})


@login_required
def symptom_edit(request, pk):
    item = get_object_or_404(SymptomEntry, pk=pk)
    form = SymptomEntryForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Η καταχώρηση ενημερώθηκε.")
        return redirect("symptom_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία συμπτώματος"})


@login_required
def symptom_delete(request, pk):
    item = get_object_or_404(SymptomEntry, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Η καταχώρηση διαγράφηκε.")
        return redirect("symptom_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή συμπτώματος"})


@login_required
def diaper_list(request):
    return render(request, "diapers/list.html", {"items": DiaperEntry.objects.all()})


@login_required
def diaper_create(request):
    form = DiaperEntryForm(
        request.POST or None,
        initial={"date": timezone.localdate(), "time": timezone.localtime().strftime("%H:%M")},
    )
    if form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, "Η πάνα αποθηκεύτηκε.")
        return redirect("diaper_list")
    return render(request, "form.html", {"form": form, "title": "Νέα πάνα"})


@login_required
def diaper_edit(request, pk):
    item = get_object_or_404(DiaperEntry, pk=pk)
    form = DiaperEntryForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Η καταχώρηση ενημερώθηκε.")
        return redirect("diaper_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία πάνας"})


@login_required
def diaper_delete(request, pk):
    item = get_object_or_404(DiaperEntry, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Η καταχώρηση διαγράφηκε.")
        return redirect("diaper_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή πάνας"})


@login_required
def growth_percentiles(request):
    profile = get_profile()
    measurements = list(GrowthMeasurement.objects.order_by("date"))
    birth_date = profile.birth_date if profile else None

    actual_weight = []
    actual_length = []
    actual_head = []
    latest_bands = None

    for item in measurements:
        age = age_months_float(birth_date, item.date) if birth_date else 0
        if item.weight_kg is not None:
            actual_weight.append({"x": round(age, 2), "y": float(item.weight_kg)})
        if item.length_cm is not None:
            actual_length.append({"x": round(age, 2), "y": float(item.length_cm)})
        if item.head_cm is not None:
            actual_head.append({"x": round(age, 2), "y": float(item.head_cm)})

    latest = GrowthMeasurement.objects.first()
    if latest and birth_date:
        age = age_months_float(birth_date, latest.date)
        latest_bands = {
            "date": latest.date,
            "age_months": round(age, 2),
            "weight": percentile_band(latest.weight_kg, WEIGHT_BOYS, age),
            "length": percentile_band(latest.length_cm, LENGTH_HEIGHT_BOYS, age),
            "head": percentile_band(latest.head_cm, HEAD_BOYS, age),
        }

    payload = {
        "weight": chart_payload(WEIGHT_BOYS),
        "length": chart_payload(LENGTH_HEIGHT_BOYS),
        "head": chart_payload(HEAD_BOYS),
        "actual_weight": actual_weight,
        "actual_length": actual_length,
        "actual_head": actual_head,
    }
    return render(
        request,
        "growth/percentiles.html",
        {"profile": profile, "payload": payload, "latest_bands": latest_bands},
    )


@login_required
def feeding_performance(request):
    raw = request.GET.get("period", "7")
    if raw not in {"7", "30", "90", "all"}:
        raw = "7"
    today = timezone.localdate()
    if raw == "all":
        first = MealEntry.objects.order_by("date").values_list("date", flat=True).first()
        start = first or today
        label = "Πάντα"
    else:
        days = int(raw)
        start = today - timedelta(days=days - 1)
        label = f"{days} ημέρες"
    stats = feeding_stats(start, today)

    day_rows = []
    current = start
    while current <= today:
        day_stats = feeding_stats(current, current)
        day_rows.append({"date": current, **day_stats})
        current += timedelta(days=1)

    chart_data = {
        "labels": [row["date"].strftime("%d/%m") for row in day_rows],
        "consumed": [row["consumed_sum"] for row in day_rows],
        "ratio": [row["intake_ratio"] or 0 for row in day_rows],
    }
    return render(
        request,
        "feeding/performance.html",
        {"period": raw, "period_label": label, "stats": stats, "chart_data": chart_data, "day_rows": reversed(day_rows)},
    )


@login_required
def doctor_view(request):
    profile = get_profile()
    today = timezone.localdate()
    last7 = today - timedelta(days=6)
    latest_growth = GrowthMeasurement.objects.first()
    latest_glucose = GlucoseReading.objects.first()
    glucose_7 = list(GlucoseReading.objects.filter(date__range=(last7, today)))
    glucose_values = [float(item.value) for item in glucose_7]
    growth_bands = None
    if profile and latest_growth:
        age = age_months_float(profile.birth_date, latest_growth.date)
        growth_bands = {
            "weight": percentile_band(latest_growth.weight_kg, WEIGHT_BOYS, age),
            "length": percentile_band(latest_growth.length_cm, LENGTH_HEIGHT_BOYS, age),
            "head": percentile_band(latest_growth.head_cm, HEAD_BOYS, age),
        }
    context = {
        "profile": profile,
        "today": today,
        "today_stats": daily_snapshot(today),
        "feeding_7": feeding_stats(last7, today),
        "latest_growth": latest_growth,
        "growth_bands": growth_bands,
        "latest_glucose": latest_glucose,
        "glucose_avg_7": round(sum(glucose_values) / len(glucose_values), 1) if glucose_values else None,
        "glucose_min_7": min(glucose_values) if glucose_values else None,
        "glucose_max_7": max(glucose_values) if glucose_values else None,
        "medications_today": MedicationEntry.objects.filter(date=today).order_by("time"),
        "symptoms_7": SymptomEntry.objects.filter(date__range=(last7, today)).order_by("-date", "-time")[:12],
        "upcoming_appointments": MedicalAppointment.objects.filter(status="scheduled", date__gte=today).order_by("date", "time")[:5],
        "vaccines": VaccineEntry.objects.order_by("-date")[:8],
    }
    return render(request, "doctor/view.html", context)


@login_required
def emergency_card(request):
    profile = get_profile()
    return render(
        request,
        "emergency/card.html",
        {
            "profile": profile,
            "latest_growth": GrowthMeasurement.objects.first(),
            "latest_glucose": GlucoseReading.objects.first(),
        },
    )


@login_required
def emergency_edit(request):
    profile = get_profile()
    if not profile:
        messages.error(request, "Δεν βρέθηκε προφίλ παιδιού.")
        return redirect("dashboard")
    form = EmergencyProfileForm(request.POST or None, instance=profile)
    if form.is_valid():
        form.save()
        messages.success(request, "Η επείγουσα κάρτα ενημερώθηκε.")
        return redirect("emergency_card")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία επείγουσας κάρτας"})


@login_required
def audit_log(request):
    model_filter = request.GET.get("model", "").strip()
    logs = AuditLog.objects.select_related("user").all()
    if model_filter:
        logs = logs.filter(model_name=model_filter)
    models = list(AuditLog.objects.order_by().values_list("model_name", flat=True).distinct())
    return render(request, "audit/list.html", {"logs": logs[:500], "models": models, "model_filter": model_filter})



def _normalize_checker_text(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(value.casefold().split())


def _matching_safety_rules(kind, text):
    normalized = _normalize_checker_text(text)
    if not normalized:
        return []

    rules = SafetyRule.objects.filter(active=True).order_by("guidance", "term")
    matches = []

    for rule in rules:
        if rule.applies_to not in {"both", kind}:
            continue
        term = _normalize_checker_text(rule.term)
        if term and term in normalized:
            matches.append(rule)

    return matches


@login_required
def safety_checker(request):
    query = (request.GET.get("q") or "").strip()
    known_results = ProductSafetyRecord.objects.none()

    if query:
        known_results = ProductSafetyRecord.objects.filter(name__icontains=query)[:20]
    else:
        known_results = ProductSafetyRecord.objects.all()[:12]

    initial = {}
    if query:
        initial["name"] = query

    form = ProductCheckerForm(request.POST or None, initial=initial)
    analysis = None

    if request.method == "POST" and form.is_valid():
        kind = form.cleaned_data["kind"]
        name = form.cleaned_data["name"].strip()
        ingredients = form.cleaned_data["ingredients"].strip()
        combined = f"{name}\n{ingredients}"
        matches = _matching_safety_rules(kind, combined)

        avoid = [rule for rule in matches if rule.guidance == "avoid"]
        caution = [rule for rule in matches if rule.guidance == "caution"]

        exact_records = ProductSafetyRecord.objects.filter(
            kind=kind,
            name__iexact=name,
        ).order_by("-reviewed_on", "-updated_at")

        if avoid:
            result_level = "avoid"
            result_title = "Περιέχει καταχωρημένο περιορισμό"
            result_text = "Βρέθηκε στα συστατικά ένας ή περισσότεροι ενεργοί όροι που έχουν καταχωρηθεί ως «Να αποφεύγεται»."
        elif caution:
            result_level = "caution"
            result_title = "Χρειάζεται επιβεβαίωση"
            result_text = "Βρέθηκε ένας ή περισσότεροι όροι που έχουν καταχωρηθεί ως «Χρειάζεται έλεγχος»."
        else:
            result_level = "clear"
            result_title = "Δεν εντοπίστηκε λακτόζη ή ζάχαρη"
            result_text = (
                "Στα συστατικά που καταχωρήθηκαν δεν βρέθηκε αντιστοιχία "
                "με τους ενεργούς περιορισμούς του app."
            )

        analysis = {
            "kind": kind,
            "name": name,
            "ingredients": ingredients,
            "matches": matches,
            "avoid": avoid,
            "caution": caution,
            "level": result_level,
            "title": result_title,
            "text": result_text,
            "exact_records": exact_records,
        }

    return render(
        request,
        "checker/index.html",
        {
            "form": form,
            "analysis": analysis,
            "query": query,
            "known_results": known_results,
            "rules_count": SafetyRule.objects.filter(active=True).count(),
        },
    )


@login_required
def safety_rule_list(request):
    return render(
        request,
        "checker/rules.html",
        {"rules": SafetyRule.objects.all()},
    )


@login_required
def safety_rule_create(request):
    form = SafetyRuleForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Ο κανόνας αποθηκεύτηκε.")
        return redirect("safety_rule_list")
    return render(request, "form.html", {"form": form, "title": "Νέος κανόνας ελέγχου"})


@login_required
def safety_rule_edit(request, pk):
    item = get_object_or_404(SafetyRule, pk=pk)
    form = SafetyRuleForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Ο κανόνας ενημερώθηκε.")
        return redirect("safety_rule_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία κανόνα"})


@login_required
def safety_rule_delete(request, pk):
    item = get_object_or_404(SafetyRule, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Ο κανόνας διαγράφηκε.")
        return redirect("safety_rule_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή κανόνα"})


@login_required
def product_record_create(request):
    initial = {
        "kind": request.GET.get("kind", "food"),
        "name": request.GET.get("name", ""),
        "reviewed_on": timezone.localdate(),
    }
    form = ProductSafetyRecordForm(request.POST or None, initial=initial)
    if form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, "Η αξιολόγηση προϊόντος/φαρμάκου αποθηκεύτηκε.")
        return redirect("safety_checker")
    return render(
        request,
        "form.html",
        {
            "form": form,
            "title": "Νέα επιβεβαιωμένη αξιολόγηση",
        },
    )


@login_required
def product_record_edit(request, pk):
    item = get_object_or_404(ProductSafetyRecord, pk=pk)
    form = ProductSafetyRecordForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Η αξιολόγηση ενημερώθηκε.")
        return redirect("safety_checker")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία αξιολόγησης"})


@login_required
def product_record_delete(request, pk):
    item = get_object_or_404(ProductSafetyRecord, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Η αξιολόγηση διαγράφηκε.")
        return redirect("safety_checker")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή αξιολόγησης"})


def _records_for_export():
    return [
        ("Profile", ChildProfile.objects.all()),
        ("Meals", MealEntry.objects.all()),
        ("Glucose", GlucoseReading.objects.all()),
        ("Growth", GrowthMeasurement.objects.all()),
        ("Medications", MedicationEntry.objects.all()),
        ("Appointments", MedicalAppointment.objects.all()),
        ("Vaccines", VaccineEntry.objects.all()),
        ("Symptoms", SymptomEntry.objects.all()),
        ("Diapers", DiaperEntry.objects.all()),
        ("Documents", MedicalDocument.objects.all()),
        ("SafetyRules", SafetyRule.objects.all()),
        ("ProductChecks", ProductSafetyRecord.objects.all()),
        ("Audit", AuditLog.objects.all()),
    ]


def _model_row(instance):
    row = {}
    for field in instance._meta.concrete_fields:
        if field.name == "data":
            continue
        try:
            value = getattr(instance, field.attname if field.is_relation else field.name)
        except Exception:
            value = None
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        elif value is not None and not isinstance(value, (str, int, float, bool)):
            value = str(value)
        row[field.name] = value
    return row


def build_excel_bytes():
    from openpyxl import Workbook

    wb = Workbook()
    default = wb.active
    wb.remove(default)
    for title, queryset in _records_for_export():
        ws = wb.create_sheet(title=title[:31])
        rows = [_model_row(item) for item in queryset]
        if not rows:
            ws.append(["No data"])
            continue
        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row.get(h) for h in headers])
        ws.freeze_panes = "A2"
        for column in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in column)
            ws.column_dimensions[column[0].column_letter].width = min(max(max_len + 2, 10), 42)
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


@login_required
def export_center(request):
    return render(
        request,
        "exports/center.html",
        {
            "counts": {
                "meals": MealEntry.objects.count(),
                "glucose": GlucoseReading.objects.count(),
                "growth": GrowthMeasurement.objects.count(),
                "documents": MedicalDocument.objects.count(),
                "safety_rules": SafetyRule.objects.count(),
                "product_checks": ProductSafetyRecord.objects.count(),
                "audit": AuditLog.objects.count(),
            }
        },
    )


@login_required
def export_excel(request):
    response = HttpResponse(
        build_excel_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="giorgos-health-all-data.xlsx"'
    return response


@login_required
def export_zip(request):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        all_data = {}
        for title, queryset in _records_for_export():
            all_data[title] = [_model_row(item) for item in queryset]
        profile = get_profile()
        all_data["Profile"] = _model_row(profile) if profile else {}
        archive.writestr("data.json", json.dumps(all_data, ensure_ascii=False, indent=2, default=str))
        archive.writestr("giorgos-health-all-data.xlsx", build_excel_bytes())
        archive.writestr(
            "README.txt",
            "Giorgos Health backup\nContains structured data in JSON and Excel plus all uploaded documents.\n",
        )
        for item in MedicalDocument.objects.all():
            safe_name = Path(item.original_filename).name.replace("/", "_").replace("\\", "_")
            archive.writestr(f"documents/{item.pk}-{safe_name}", bytes(item.data))
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="giorgos-health-backup.zip"'
    return response


@login_required
def export_pdf(request):
    from xml.sax.saxutils import escape
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from .views import _pdf_styles, _report_logo_path
    from reportlab.platypus import Image

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="giorgos-health-all-data.pdf"'
    font_name, styles = _pdf_styles()
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=12*mm, leftMargin=12*mm, topMargin=12*mm, bottomMargin=12*mm)
    story = []
    logo_path = _report_logo_path()
    if logo_path:
        logo = Image(logo_path, width=20*mm, height=20*mm)
        logo.hAlign = "CENTER"
        story.extend([logo, Spacer(1, 2*mm)])
    profile = get_profile()
    story.append(Paragraph("Giorgos Health — Πλήρης εξαγωγή", styles["title"]))
    if profile:
        story.append(Paragraph(escape(profile.full_name or profile.name), styles["heading"]))
        story.append(Paragraph(f"Ημερομηνία γέννησης: {profile.birth_date.strftime('%d/%m/%Y')}", styles["small"]))
        if profile.current_feeding_plan:
            story.append(Paragraph("Τρέχον πλάνο σίτισης: " + escape(profile.current_feeding_plan), styles["small"]))
        if profile.emergency_instructions:
            story.append(Paragraph("Βασικές ιατρικές οδηγίες: " + escape(profile.emergency_instructions), styles["small"]))
        if profile.treating_doctors:
            story.append(Paragraph("Θεράποντες ιατροί: " + escape(profile.treating_doctors), styles["small"]))
        phone_parts = []
        if profile.father_phone:
            phone_parts.append("Μπαμπάς: " + profile.father_phone)
        if profile.mother_phone:
            phone_parts.append("Μαμά: " + profile.mother_phone)
        if profile.dr_savvas_phone:
            phone_parts.append("Δρ Σάββας Σάββα: " + profile.dr_savvas_phone)
        if profile.dr_grafakou_phone:
            phone_parts.append("Δρ Όλγα Γραφάκου: " + profile.dr_grafakou_phone)
        if profile.emergency_contacts:
            phone_parts.append("Άλλη επαφή: " + profile.emergency_contacts)
        if phone_parts:
            story.append(Paragraph("Τηλέφωνα: " + escape(" | ".join(phone_parts)), styles["small"]))
    story.append(Spacer(1, 4*mm))

    sections = [
        ("Γεύματα", [[m.date.strftime('%d/%m/%Y'), m.scheduled_time.strftime('%H:%M'), str(m.consumed_ml or ''), str(m.offered_ml or ''), m.status] for m in MealEntry.objects.order_by('-date','-scheduled_time')], ["Ημ/νία","Ώρα","Ήπιε","Προσφ.","Κατάσταση"]),
        ("Γλυκόζη", [[g.date.strftime('%d/%m/%Y'), g.time.strftime('%H:%M'), f"{g.value:g}", g.get_context_display()] for g in GlucoseReading.objects.order_by('-date','-time')], ["Ημ/νία","Ώρα","mg/dL","Σχέση"]),
        ("Ανάπτυξη", [[g.date.strftime('%d/%m/%Y'), str(g.weight_kg or ''), str(g.length_cm or ''), str(g.head_cm or '')] for g in GrowthMeasurement.objects.order_by('-date')], ["Ημ/νία","kg","cm","Κεφάλι"]),
        ("Φάρμακα", [[m.date.strftime('%d/%m/%Y'), m.time.strftime('%H:%M'), m.name, f"{m.dose:g} {m.get_unit_display()}"] for m in MedicationEntry.objects.order_by('-date','-time')], ["Ημ/νία","Ώρα","Όνομα","Δόση"]),
        ("Ραντεβού", [[a.date.strftime('%d/%m/%Y'), a.time.strftime('%H:%M'), a.doctor, a.purpose] for a in MedicalAppointment.objects.order_by('-date','-time')], ["Ημ/νία","Ώρα","Ιατρός","Λόγος"]),
        ("Εμβόλια", [[v.date.strftime('%d/%m/%Y'), v.name, v.dose_label, v.next_date.strftime('%d/%m/%Y') if v.next_date else ''] for v in VaccineEntry.objects.order_by('-date')], ["Ημ/νία","Εμβόλιο","Δόση","Επόμενη"]),
        ("Συμπτώματα", [[s.date.strftime('%d/%m/%Y'), s.time.strftime('%H:%M'), s.symptom, s.get_severity_display()] for s in SymptomEntry.objects.order_by('-date','-time')], ["Ημ/νία","Ώρα","Σύμπτωμα","Ένταση"]),
        ("Πάνες", [[d.date.strftime('%d/%m/%Y'), d.time.strftime('%H:%M'), d.get_kind_display(), d.stool_color] for d in DiaperEntry.objects.order_by('-date','-time')], ["Ημ/νία","Ώρα","Τύπος","Χρώμα"]),
        ("Έγγραφα", [[d.date.strftime('%d/%m/%Y'), d.get_category_display(), d.title, d.original_filename] for d in MedicalDocument.objects.order_by('-date')], ["Ημ/νία","Κατηγορία","Τίτλος","Αρχείο"]),
        ("Κανόνες ελέγχου", [[r.term, r.get_applies_to_display(), r.get_guidance_display(), r.note] for r in SafetyRule.objects.order_by('term')], ["Όρος","Ισχύει για","Οδηγία","Σημείωση"]),
        ("Αξιολογήσεις προϊόντων", [[p.get_kind_display(), p.name, p.get_decision_display(), p.confirmed_by] for p in ProductSafetyRecord.objects.order_by('kind','name')], ["Τύπος","Ονομασία","Αξιολόγηση","Επιβεβαιώθηκε από"]),
        ("Audit log", [[a.timestamp.strftime('%d/%m/%Y %H:%M'), a.get_action_display(), a.model_name, a.object_repr] for a in AuditLog.objects.order_by('-timestamp')[:500]], ["Ημ/νία","Ενέργεια","Τύπος","Αντικείμενο"]),
    ]
    for title, rows, headers in sections:
        story.append(Paragraph(title, styles["heading"]))
        if not rows:
            story.append(Paragraph("Δεν υπάρχουν δεδομένα.", styles["small"]))
            continue
        table_data = [headers] + [[Paragraph(escape(str(cell)), styles["small"]) for cell in row] for row in rows]
        col_width = 180*mm / len(headers)
        table = Table(table_data, colWidths=[col_width]*len(headers), repeatRows=1)
        table.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EAF2FF")),
            ("GRID", (0,0), (-1,-1), .25, colors.HexColor("#DDE5F0")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("PADDING", (0,0), (-1,-1), 3),
        ]))
        story.append(table)
        story.append(Spacer(1, 4*mm))
    doc.build(story)
    return response
