from collections import defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .access import user_role

from .forms import (
    GlucoseReadingForm,
    GrowthMeasurementForm,
    MealEntryForm,
    MedicationEntryForm,
    MedicalAppointmentForm,
    ChildProfileForm,
    PersistentAuthenticationForm,
)
from .models import (
    GlucoseReading,
    GrowthMeasurement,
    MealEntry,
    MedicationEntry,
    MedicalAppointment,
    ChildProfile,
)


class PersistentLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = PersistentAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        if user_role(self.request.user) == "doctor_readonly":
            return reverse("doctor_view")
        return super().get_success_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.cleaned_data.get("remember_me", True):
            self.request.session.set_expiry(60 * 60 * 24 * 90)
        else:
            self.request.session.set_expiry(0)
        return response


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


def get_child_profile():
    profile = ChildProfile.objects.first()
    if profile:
        return profile
    return ChildProfile.objects.create(
        name="Γιώργος",
        birth_date=ChildProfile.FIXED_BIRTH_DATE,
    )


def child_age_details(birth_date, today):
    if not birth_date or today < birth_date:
        return {"days": 0, "weeks": 0, "months": 0, "display": "—"}

    total_days = (today - birth_date).days
    weeks = total_days // 7

    months = (today.year - birth_date.year) * 12 + today.month - birth_date.month
    if today.day < birth_date.day:
        months -= 1
    months = max(months, 0)

    import calendar
    anchor_year = birth_date.year + (birth_date.month - 1 + months) // 12
    anchor_month = (birth_date.month - 1 + months) % 12 + 1
    anchor_day = min(
        birth_date.day,
        calendar.monthrange(anchor_year, anchor_month)[1],
    )
    anchor_date = datetime(anchor_year, anchor_month, anchor_day).date()
    remaining_days = max((today - anchor_date).days, 0)

    if months < 1:
        display = f"{weeks} εβδομάδων και {total_days % 7} ημερών"
    elif months < 24:
        display = f"{months} μηνών και {remaining_days} ημερών"
    else:
        years = months // 12
        rem_months = months % 12
        display = f"{years} ετών και {rem_months} μηνών"

    return {
        "days": total_days,
        "weeks": weeks,
        "months": months,
        "display": display,
    }


def age_based_milk_guide(age_days):
    # General age-based population guide. Not an individual prescription.
    if age_days <= 14:
        return {"min": 420, "max": 560, "label": "Έως 2 εβδομάδων", "kind": "range", "milk_type": "βρεφικό γάλα"}
    if age_days <= 56:
        return {"min": 450, "max": 735, "label": "2–8 εβδομάδων", "kind": "range", "milk_type": "βρεφικό γάλα"}
    if age_days <= 98:
        return {"min": 525, "max": 1080, "label": "2–3 μηνών", "kind": "range", "milk_type": "βρεφικό γάλα"}
    if age_days <= 175:
        return {"min": 900, "max": 1050, "label": "3–5 μηνών", "kind": "range", "milk_type": "βρεφικό γάλα"}
    if age_days <= 212:
        return {"min": 840, "max": 960, "label": "Περίπου 6 μηνών", "kind": "range", "milk_type": "βρεφικό γάλα"}
    if age_days <= 304:
        return {"min": 600, "max": 600, "label": "7–9 μηνών", "kind": "about", "milk_type": "βρεφικό γάλα"}
    if age_days <= 365:
        return {"min": 400, "max": 400, "label": "10–12 μηνών", "kind": "about", "milk_type": "βρεφικό γάλα"}
    if age_days <= 730:
        return {"min": 350, "max": 400, "label": "1–2 ετών", "kind": "range", "milk_type": "πλήρες αγελαδινό ή άλλο κατάλληλο γάλα"}

    return {"min": None, "max": None, "label": "Άνω των 2 ετών", "kind": "none", "milk_type": ""}


def weight_based_formula_guide(latest_growth, age_days):
    # General guide after the first week until around 6 months: ~150–200 ml/kg/day.
    if (
        not latest_growth
        or latest_growth.weight_kg is None
        or age_days < 7
        or age_days > 183
    ):
        return None

    weight = float(latest_growth.weight_kg)
    return {
        "weight": weight,
        "min": round(weight * 150),
        "max": round(weight * 200),
    }



def _numeric_scoops(value):
    """
    Parse the existing MealEntry.supplement field as Maxijul scoops.
    It accepts values such as "1", "1.0", "1 scoop" or "1 κουταλιά".
    """
    text = str(value or "").strip().replace(",", ".")
    if not text:
        return 0.0

    match = re.search(r"[-+]?\d*\.?\d+", text)
    if not match:
        return 0.0

    try:
        return max(float(match.group(0)), 0.0)
    except (TypeError, ValueError):
        return 0.0


def maxijul_day_summary(profile, meals):
    meals = list(meals)
    recorded = [
        meal
        for meal in meals
        if meal.status != "missed" and meal.consumed_ml is not None
    ]

    prepared_scoops = 0.0
    consumed_scoops = 0.0
    with_maxijul = 0
    without_maxijul = 0

    for meal in recorded:
        scoops = _numeric_scoops(meal.supplement)

        if scoops > 0:
            with_maxijul += 1
            prepared_scoops += scoops

            # Maxijul is mixed through the prepared bottle. Estimate actual
            # intake proportionally to consumed/offered volume. If offered
            # volume is unavailable, fall back to the full entered scoop amount.
            if meal.offered_ml and meal.offered_ml > 0:
                ratio = min(max((meal.consumed_ml or 0) / meal.offered_ml, 0), 1)
                consumed_scoops += scoops * ratio
            elif (meal.consumed_ml or 0) > 0:
                consumed_scoops += scoops
        else:
            without_maxijul += 1

    if recorded:
        if with_maxijul and without_maxijul:
            mode = "mixed"
        elif with_maxijul:
            mode = "with_maxijul"
        else:
            mode = "without_maxijul"
    else:
        mode = (
            "planned_with_maxijul"
            if profile.maxijul_plan_active
            else "planned_without_maxijul"
        )

    scoop_grams = float(profile.maxijul_scoop_grams or 0)
    kcal_per_100g = float(profile.maxijul_kcal_per_100g or 0)
    carbs_per_100g = float(profile.maxijul_carbs_per_100g or 0)

    grams = consumed_scoops * scoop_grams
    kcal = grams * kcal_per_100g / 100 if grams and kcal_per_100g else 0
    carbs = grams * carbs_per_100g / 100 if grams and carbs_per_100g else 0

    return {
        "mode": mode,
        "recorded_meals": len(recorded),
        "with_maxijul_meals": with_maxijul,
        "without_maxijul_meals": without_maxijul,
        "prepared_scoops": round(prepared_scoops, 2),
        "total_scoops": round(consumed_scoops, 2),
        "grams": round(grams, 1),
        "kcal": round(kcal, 1),
        "carbs_g": round(carbs, 1),
        "planned_scoops_per_feed": profile.planned_maxijul_scoops_per_feed,
    }


def _normalized_target(minimum, maximum):
    if minimum is None and maximum is None:
        return None, None

    target_min = minimum if minimum is not None else maximum
    target_max = maximum if maximum is not None else minimum
    return target_min, target_max


def daily_milk_guide(profile, latest_growth, today, meals_today):
    meals_today = list(meals_today)
    consumed_today = sum(item.consumed_ml or 0 for item in meals_today)

    age = child_age_details(profile.birth_date, today)
    age_guide = age_based_milk_guide(age["days"])
    weight_guide = weight_based_formula_guide(latest_growth, age["days"])
    maxijul = maxijul_day_summary(profile, meals_today)

    with_min, with_max = _normalized_target(
        profile.target_with_maxijul_min_ml,
        profile.target_with_maxijul_max_ml,
    )
    without_min, without_max = _normalized_target(
        profile.target_without_maxijul_min_ml,
        profile.target_without_maxijul_max_ml,
    )

    mode = maxijul["mode"]
    target_min = None
    target_max = None
    active_source = "reference_only"
    active_label = "Δεν έχει οριστεί εξατομικευμένος στόχος"
    has_active_target = False

    if mode in {"with_maxijul", "planned_with_maxijul"}:
        if with_min is not None or with_max is not None:
            target_min, target_max = with_min, with_max
            active_source = "with_maxijul"
            active_label = "Εξατομικευμένος στόχος · με Maxijul"
            has_active_target = True
        else:
            active_source = "with_maxijul_missing"
            active_label = "Με Maxijul · αναμονή εξατομικευμένου στόχου"

    elif mode in {"without_maxijul", "planned_without_maxijul"}:
        if without_min is not None or without_max is not None:
            target_min, target_max = without_min, without_max
            active_source = "without_maxijul"
            active_label = "Εξατομικευμένος στόχος · χωρίς Maxijul"
            has_active_target = True
        else:
            active_source = "without_maxijul_missing"
            active_label = "Χωρίς Maxijul · αναμονή εξατομικευμένου στόχου"

    elif mode == "mixed":
        active_source = "mixed"
        active_label = "Μικτή ημέρα · δεν εφαρμόζεται αυτόματα ένας στόχος"

    progress = None
    if has_active_target and target_max and target_max > 0:
        progress = min(round((consumed_today / target_max) * 100), 100)

    return {
        "age": age,
        "age_guide": age_guide,
        "weight_guide": weight_guide,
        "maxijul": maxijul,
        "with_maxijul_min": profile.target_with_maxijul_min_ml,
        "with_maxijul_max": profile.target_with_maxijul_max_ml,
        "without_maxijul_min": profile.target_without_maxijul_min_ml,
        "without_maxijul_max": profile.target_without_maxijul_max_ml,
        "feeding_target_note": profile.feeding_target_note,
        "has_with_maxijul_target": (
            profile.target_with_maxijul_min_ml is not None
            or profile.target_with_maxijul_max_ml is not None
        ),
        "has_without_maxijul_target": (
            profile.target_without_maxijul_min_ml is not None
            or profile.target_without_maxijul_max_ml is not None
        ),
        "has_active_target": has_active_target,
        "active_source": active_source,
        "active_label": active_label,
        "target_min": target_min,
        "target_max": target_max,
        "consumed_today": consumed_today,
        "progress": progress,
    }


def meal_timing_context(now_local):
    today = now_local.date()
    current_time = now_local.time().replace(tzinfo=None)

    next_date = today
    next_time = None
    for scheduled in SCHEDULED_TIMES:
        if scheduled > current_time:
            next_time = scheduled
            break
    if next_time is None:
        next_date = today + timedelta(days=1)
        next_time = SCHEDULED_TIMES[0]

    next_naive = datetime.combine(next_date, next_time)
    next_dt = timezone.make_aware(next_naive, timezone.get_current_timezone())

    recent_meals = list(MealEntry.objects.order_by("-date", "-scheduled_time")[:30])
    last_meal = None
    last_naive = None
    for candidate in recent_meals:
        candidate_time = candidate.actual_time or candidate.scheduled_time
        candidate_dt = datetime.combine(candidate.date, candidate_time)
        if last_naive is None or candidate_dt > last_naive:
            last_meal = candidate
            last_naive = candidate_dt

    last_dt = None
    if last_naive is not None:
        last_dt = timezone.make_aware(last_naive, timezone.get_current_timezone())

    return {
        "next_meal_dt": next_dt,
        "next_meal_iso": next_dt.isoformat(),
        "last_meal": last_meal,
        "last_meal_dt": last_dt,
        "last_meal_iso": last_dt.isoformat() if last_dt else "",
    }

def next_scheduled_time(now_local):
    current = now_local.time().replace(second=0, microsecond=0)
    for scheduled in SCHEDULED_TIMES:
        if scheduled >= current:
            return scheduled
    return SCHEDULED_TIMES[0]


def parse_date(value, fallback):
    if not value:
        return fallback
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return fallback


def history_range(request):
    today = timezone.localdate()
    default_start = today - timedelta(days=6)

    end_date = parse_date(request.GET.get("end"), today)
    start_date = parse_date(request.GET.get("start"), default_start)

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    if (end_date - start_date).days > 365:
        start_date = end_date - timedelta(days=365)

    return start_date, end_date


def build_history_days(start_date, end_date):
    meals = list(
        MealEntry.objects.filter(date__range=(start_date, end_date))
        .select_related("created_by")
        .order_by("-date", "scheduled_time")
    )
    glucose = list(
        GlucoseReading.objects.filter(date__range=(start_date, end_date))
        .select_related("related_meal", "created_by")
        .order_by("-date", "time")
    )
    growth = list(
        GrowthMeasurement.objects.filter(date__range=(start_date, end_date))
        .order_by("-date")
    )
    medications = list(
        MedicationEntry.objects.filter(date__range=(start_date, end_date))
        .select_related("created_by")
        .order_by("-date", "time")
    )

    meals_by_date = defaultdict(list)
    glucose_by_date = defaultdict(list)
    growth_by_date = defaultdict(list)
    meds_by_date = defaultdict(list)

    for item in meals:
        meals_by_date[item.date].append(item)
    for item in glucose:
        glucose_by_date[item.date].append(item)
    for item in growth:
        growth_by_date[item.date].append(item)
    for item in medications:
        meds_by_date[item.date].append(item)

    dates = set(meals_by_date) | set(glucose_by_date) | set(growth_by_date) | set(meds_by_date)

    days = []
    for day_date in sorted(dates, reverse=True):
        day_meals = meals_by_date.get(day_date, [])
        day_glucose = glucose_by_date.get(day_date, [])
        day_growth = growth_by_date.get(day_date, [])
        day_meds = meds_by_date.get(day_date, [])

        total_consumed = sum(item.consumed_ml or 0 for item in day_meals)
        glucose_values = [float(item.value) for item in day_glucose]

        timeline = []

        for item in day_meals:
            display_time = item.actual_time or item.scheduled_time
            timeline.append({
                "time": display_time,
                "kind": "meal",
                "icon": "🍼",
                "title": "Γεύμα",
                "text": (
                    f"{item.consumed_ml if item.consumed_ml is not None else '—'} ml"
                    + (f" από {item.offered_ml} ml" if item.offered_ml is not None else "")
                ),
                "extra": f"Formula: {item.formula}" if item.formula else "",
            })

        for item in day_glucose:
            timeline.append({
                "time": item.time,
                "kind": "glucose",
                "icon": "🩸",
                "title": "Γλυκόζη",
                "text": f"{item.value:g} mg/dL",
                "extra": item.get_context_display(),
            })

        for item in day_meds:
            timeline.append({
                "time": item.time,
                "kind": "medication",
                "icon": "💊",
                "title": item.name,
                "text": f"{item.dose:g} {item.get_unit_display()}",
                "extra": item.notes,
            })

        timeline.sort(key=lambda item: item["time"])

        days.append({
            "date": day_date,
            "meals": day_meals,
            "glucose": day_glucose,
            "growth": day_growth,
            "medications": day_meds,
            "timeline": timeline,
            "total_consumed": total_consumed,
            "glucose_min": min(glucose_values) if glucose_values else None,
            "glucose_max": max(glucose_values) if glucose_values else None,
        })

    return days


def appointment_reminder_items(today):
    appointments = MedicalAppointment.objects.filter(
        status="scheduled",
        date__gte=today,
    ).order_by("date", "time")[:20]

    reminders = []
    upcoming = []

    for item in appointments:
        days_until = (item.date - today).days
        if days_until == 0:
            label = "Σήμερα"
        elif days_until == 1:
            label = "Αύριο"
        else:
            label = f"Σε {days_until} ημέρες"

        data = {
            "object": item,
            "days_until": days_until,
            "label": label,
        }
        upcoming.append(data)

        if days_until <= item.reminder_days_before:
            reminders.append(data)

    return reminders[:5], upcoming[:5]


@login_required
def dashboard(request):
    today = timezone.localdate()
    meals_today = MealEntry.objects.filter(date=today).order_by("scheduled_time")
    glucose_today = GlucoseReading.objects.filter(date=today).order_by("time")
    medications_today = MedicationEntry.objects.filter(date=today).order_by("time")
    latest_growth = GrowthMeasurement.objects.first()
    profile = get_child_profile()
    consumed_total = sum(item.consumed_ml or 0 for item in meals_today)
    milk_guide = daily_milk_guide(profile, latest_growth, today, meals_today)

    previous_days = build_history_days(today - timedelta(days=3), today - timedelta(days=1))
    reminder_appointments, upcoming_appointments = appointment_reminder_items(today)
    meal_timing = meal_timing_context(timezone.localtime())

    from .advanced_views import dashboard_extras
    extras = dashboard_extras(today)

    context = {
        "today": today,
        "meals_today": meals_today,
        "glucose_today": glucose_today,
        "medications_today": medications_today,
        "meal_count": meals_today.count(),
        "glucose_count": glucose_today.count(),
        "latest_glucose": GlucoseReading.objects.first(),
        "latest_growth": latest_growth,
        "profile": profile,
        "milk_guide": milk_guide,
        "consumed_total": consumed_total,
        "next_meal_time": next_scheduled_time(timezone.localtime()),
        "schedule": SCHEDULED_TIMES,
        "previous_days": previous_days[:3],
        "reminder_appointments": reminder_appointments,
        "upcoming_appointments": upcoming_appointments,
        **meal_timing,
        **extras,
    }
    return render(request, "dashboard.html", context)


@login_required
def child_profile_edit(request):
    profile = get_child_profile()
    form = ChildProfileForm(request.POST or None, instance=profile)
    if form.is_valid():
        form.save()
        messages.success(request, "Τα στοιχεία και οι στόχοι σίτισης ενημερώθηκαν.")
        return redirect("dashboard")
    return render(
        request,
        "profile/edit.html",
        {"form": form, "profile": profile},
    )


@login_required
def more(request):
    return render(request, "more.html")


@login_required
def analytics(request):
    raw_period = request.GET.get("period", "7")
    allowed_periods = {"7", "30", "90", "all"}
    if raw_period not in allowed_periods:
        raw_period = "7"

    today = timezone.localdate()

    if raw_period == "all":
        earliest_dates = []

        first_meal = MealEntry.objects.order_by("date").values_list("date", flat=True).first()
        first_glucose = GlucoseReading.objects.order_by("date").values_list("date", flat=True).first()
        first_growth = GrowthMeasurement.objects.order_by("date").values_list("date", flat=True).first()

        for value in (first_meal, first_glucose, first_growth):
            if value:
                earliest_dates.append(value)

        start_date = min(earliest_dates) if earliest_dates else today
        period_label = "Πάντα"
    else:
        period_days = int(raw_period)
        start_date = today - timedelta(days=period_days - 1)
        period_label = f"{period_days} ημέρες"

    meals = MealEntry.objects.filter(date__range=(start_date, today))
    glucose = GlucoseReading.objects.filter(
        date__range=(start_date, today)
    ).order_by("date", "time")
    growth = GrowthMeasurement.objects.filter(
        date__range=(start_date, today)
    ).order_by("date")

    ml_by_date = defaultdict(int)
    for item in meals:
        ml_by_date[item.date] += item.consumed_ml or 0

    # For the daily-ml graph, use every calendar date in the requested period.
    date_count = (today - start_date).days + 1
    dates = [start_date + timedelta(days=i) for i in range(date_count)]

    chart_data = {
        "period": raw_period,
        "period_label": period_label,
        "daily_labels": [d.strftime("%d/%m/%y") for d in dates],
        "daily_ml": [ml_by_date.get(d, 0) for d in dates],
        "glucose_labels": [
            f"{item.date.strftime('%d/%m/%y')} {item.time.strftime('%H:%M')}"
            for item in glucose
        ],
        "glucose_values": [float(item.value) for item in glucose],
        "weight_labels": [
            item.date.strftime("%d/%m/%y")
            for item in growth
            if item.weight_kg is not None
        ],
        "weight_values": [
            float(item.weight_kg)
            for item in growth
            if item.weight_kg is not None
        ],
        "length_labels": [
            item.date.strftime("%d/%m/%y")
            for item in growth
            if item.length_cm is not None
        ],
        "length_values": [
            float(item.length_cm)
            for item in growth
            if item.length_cm is not None
        ],
    }

    return render(request, "analytics.html", {
        "period": raw_period,
        "period_label": period_label,
        "chart_data": chart_data,
    })


@login_required
def history(request):
    start_date, end_date = history_range(request)
    days = build_history_days(start_date, end_date)
    return render(request, "history.html", {
        "days": days,
        "start_date": start_date,
        "end_date": end_date,
    })


def _register_pdf_font():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
    ]

    for candidate in candidates:
        if Path(candidate).exists():
            try:
                pdfmetrics.registerFont(TTFont("GiorgosPDF", candidate))
                return "GiorgosPDF"
            except Exception:
                continue
    return "Helvetica"


def _report_logo_path():
    """Find the app logo both locally and after collectstatic."""
    candidates = [
        Path(settings.BASE_DIR) / "static" / "images" / "logo.png",
        Path(settings.BASE_DIR) / "staticfiles" / "images" / "logo.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def _pdf_styles():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    font_name = _register_pdf_font()
    styles = getSampleStyleSheet()

    return font_name, {
        "title": ParagraphStyle(
            "TitleGreek",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#315D9D"),
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleGreek",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=9,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#6C7892"),
            spaceAfter=12,
        ),
        "heading": ParagraphStyle(
            "HeadingGreek",
            parent=styles["Heading2"],
            fontName=font_name,
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#315D9D"),
            spaceBefore=5,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "BodyGreek",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1F2A44"),
        ),
        "small": ParagraphStyle(
            "SmallGreek",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#596579"),
        ),
    }


@login_required
def history_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    start_date, end_date = history_range(request)
    days = build_history_days(start_date, end_date)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="giorgos-health-{start_date.isoformat()}-{end_date.isoformat()}.pdf"'
    )

    font_name, styles = _pdf_styles()
    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Giorgos Panayiotis Michael - Giorgos Health - Ιστορικό",
        author="Giorgos Health",
    )

    story = []
    logo_path = _report_logo_path()
    if logo_path:
        logo = Image(logo_path, width=22*mm, height=22*mm)
        logo.hAlign = "CENTER"
        story.extend([logo, Spacer(1, 2*mm)])

    story.extend([
        Paragraph("Giorgos Health", styles["title"]),
        Paragraph("Giorgos Panayiotis Michael", styles["heading"]),
        Paragraph(
            f"Ιστορικό από {start_date.strftime('%d/%m/%Y')} έως {end_date.strftime('%d/%m/%Y')}",
            styles["subtitle"],
        ),
    ])

    if not days:
        story.append(Paragraph("Δεν υπάρχουν καταχωρήσεις για αυτή την περίοδο.", styles["body"]))

    for day in days:
        story.append(Paragraph(day["date"].strftime("%d/%m/%Y"), styles["heading"]))
        story.append(Paragraph(
            f"Γεύματα: {len(day['meals'])} · Σύνολο: {day['total_consumed']} ml · "
            f"Γλυκόζη: {len(day['glucose'])} μετρήσεις · "
            f"Φάρμακα/συμπληρώματα: {len(day['medications'])}",
            styles["small"],
        ))
        story.append(Spacer(1, 3 * mm))

        if day["meals"]:
            rows = [["Πρόγρ.", "Πραγμ.", "Προσφ.", "Ήπιε", "Formula"]]
            for item in day["meals"]:
                rows.append([
                    item.scheduled_time.strftime("%H:%M"),
                    item.actual_time.strftime("%H:%M") if item.actual_time else "—",
                    f"{item.offered_ml} ml" if item.offered_ml is not None else "—",
                    f"{item.consumed_ml} ml" if item.consumed_ml is not None else "—",
                    item.formula or "—",
                ])
            table = Table(rows, colWidths=[22*mm, 22*mm, 25*mm, 24*mm, 77*mm], repeatRows=1)
            table.setStyle(TableStyle([
                ("FONTNAME", (0,0), (-1,-1), font_name),
                ("FONTSIZE", (0,0), (-1,-1), 7.5),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E9F4FF")),
                ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDE5F0")),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("PADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(table)
            story.append(Spacer(1, 4*mm))

        if day["glucose"]:
            rows = [["Ώρα", "Τιμή", "Σχέση", "Σημειώσεις"]]
            for item in day["glucose"]:
                rows.append([
                    item.time.strftime("%H:%M"),
                    f"{item.value:g} mg/dL",
                    item.get_context_display(),
                    Paragraph(item.notes or "—", styles["small"]),
                ])
            table = Table(rows, colWidths=[22*mm, 30*mm, 42*mm, 76*mm], repeatRows=1)
            table.setStyle(TableStyle([
                ("FONTNAME", (0,0), (-1,-1), font_name),
                ("FONTSIZE", (0,0), (-1,-1), 7.5),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#FFF1E6")),
                ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#E9E0D7")),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("PADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(table)
            story.append(Spacer(1, 4*mm))

        if day["medications"]:
            rows = [["Ώρα", "Φάρμακο / συμπλήρωμα", "Ποσότητα", "Σημειώσεις"]]
            for item in day["medications"]:
                rows.append([
                    item.time.strftime("%H:%M"),
                    item.name,
                    f"{item.dose:g} {item.get_unit_display()}",
                    Paragraph(item.notes or "—", styles["small"]),
                ])
            table = Table(rows, colWidths=[22*mm, 60*mm, 35*mm, 53*mm], repeatRows=1)
            table.setStyle(TableStyle([
                ("FONTNAME", (0,0), (-1,-1), font_name),
                ("FONTSIZE", (0,0), (-1,-1), 7.5),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EBFFF4")),
                ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDE9E3")),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("PADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(table)
            story.append(Spacer(1, 4*mm))

        if day["growth"]:
            story.append(Paragraph("Ανάπτυξη", styles["body"]))
            for item in day["growth"]:
                story.append(Paragraph(
                    f"Βάρος: {item.weight_kg if item.weight_kg is not None else '—'} kg · "
                    f"Μήκος: {item.length_cm if item.length_cm is not None else '—'} cm · "
                    f"Περίμετρος κεφαλής: {item.head_cm if item.head_cm is not None else '—'} cm",
                    styles["small"],
                ))
        story.append(Spacer(1, 5*mm))

    doc.build(story)
    return response


def _aware_event_datetime(date_value, time_value):
    dt = datetime.combine(date_value, time_value)
    return timezone.make_aware(dt, timezone.get_current_timezone())



def _rolling_24h_data():
    end_dt = timezone.localtime()
    start_dt = end_dt - timedelta(hours=24)
    date_start = start_dt.date()
    date_end = end_dt.date()

    meals = []
    for item in MealEntry.objects.filter(
        date__range=(date_start, date_end)
    ).order_by("date", "scheduled_time"):
        event_time = item.actual_time or item.scheduled_time
        if start_dt <= _aware_event_datetime(item.date, event_time) <= end_dt:
            meals.append(item)

    glucose = []
    for item in GlucoseReading.objects.filter(
        date__range=(date_start, date_end)
    ).order_by("date", "time"):
        if start_dt <= _aware_event_datetime(item.date, item.time) <= end_dt:
            glucose.append(item)

    medications = []
    for item in MedicationEntry.objects.filter(
        date__range=(date_start, date_end)
    ).order_by("date", "time"):
        if start_dt <= _aware_event_datetime(item.date, item.time) <= end_dt:
            medications.append(item)

    latest_growth = GrowthMeasurement.objects.first()
    total_ml = sum(item.consumed_ml or 0 for item in meals)

    profile = get_child_profile()
    maxijul_24h = maxijul_day_summary(profile, meals)

    glucose_values = [float(item.value) for item in glucose]
    glucose_min = min(glucose_values) if glucose_values else None
    glucose_max = max(glucose_values) if glucose_values else None

    return {
        "start_dt": start_dt,
        "end_dt": end_dt,
        "meals": meals,
        "glucose": glucose,
        "medications": medications,
        "latest_growth": latest_growth,
        "total_ml": total_ml,
        "maxijul_24h": maxijul_24h,
        "glucose_min": glucose_min,
        "glucose_max": glucose_max,
    }


@login_required
def report_24h_preview(request):
    data = _rolling_24h_data()
    return render(request, "reports/report_24h_preview.html", data)


@login_required
def history_report_preview(request):
    start_date, end_date = history_range(request)
    days = build_history_days(start_date, end_date)

    total_meals = sum(len(day["meals"]) for day in days)
    total_ml = sum(day["total_consumed"] for day in days)
    total_glucose = sum(len(day["glucose"]) for day in days)
    total_medications = sum(len(day["medications"]) for day in days)

    glucose_values = [
        float(item.value)
        for day in days
        for item in day["glucose"]
    ]

    return render(
        request,
        "reports/history_report_preview.html",
        {
            "days": days,
            "start_date": start_date,
            "end_date": end_date,
            "total_meals": total_meals,
            "total_ml": total_ml,
            "total_glucose": total_glucose,
            "total_medications": total_medications,
            "glucose_min": min(glucose_values) if glucose_values else None,
            "glucose_max": max(glucose_values) if glucose_values else None,
        },
    )


@login_required
def report_24h_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    report_data = _rolling_24h_data()
    end_dt = report_data["end_dt"]
    start_dt = report_data["start_dt"]
    meals = report_data["meals"]
    glucose = report_data["glucose"]
    medications = report_data["medications"]
    latest_growth = report_data["latest_growth"]
    total_ml = report_data["total_ml"]
    maxijul_24h = report_data["maxijul_24h"]

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="giorgos-health-last-24h-{end_dt.strftime("%Y%m%d-%H%M")}.pdf"'
    )

    font_name, styles = _pdf_styles()
    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=14*mm,
        leftMargin=14*mm,
        topMargin=14*mm,
        bottomMargin=14*mm,
        title="Giorgos Panayiotis Michael - Giorgos Health - 24ωρη Αναφορά",
        author="Giorgos Health",
    )

    story = []
    logo_path = _report_logo_path()
    if logo_path:
        logo = Image(logo_path, width=22*mm, height=22*mm)
        logo.hAlign = "CENTER"
        story.extend([logo, Spacer(1, 2*mm)])

    story.extend([
        Paragraph("Giorgos Health", styles["title"]),
        Paragraph("Giorgos Panayiotis Michael", styles["heading"]),
        Paragraph("24ωρη Αναφορά", styles["heading"]),
        Paragraph(
            f"Περίοδος: {start_dt.strftime('%d/%m/%Y %H:%M')} – {end_dt.strftime('%d/%m/%Y %H:%M')}",
            styles["subtitle"],
        ),
        Paragraph(
            f"Γεύματα: {len(meals)} · Σύνολο: {total_ml} ml · Μετρήσεις γλυκόζης: {len(glucose)} · "
            f"Φάρμακα/συμπληρώματα: {len(medications)}",
            styles["body"],
        ),
        Paragraph(
            f"Maxijul 24ώρου: {maxijul_24h['total_scoops']:g} scoops · "
            f"≈ {maxijul_24h['grams']:g} g · ≈ {maxijul_24h['kcal']:g} kcal",
            styles["body"],
        ),
        Spacer(1, 4*mm),
    ])

    if latest_growth:
        story.append(Paragraph(
            f"Τελευταία ανάπτυξη ({latest_growth.date.strftime('%d/%m/%Y')}): "
            f"Βάρος {latest_growth.weight_kg if latest_growth.weight_kg is not None else '—'} kg · "
            f"Μήκος {latest_growth.length_cm if latest_growth.length_cm is not None else '—'} cm",
            styles["small"],
        ))
        story.append(Spacer(1, 4*mm))

    if meals:
        story.append(Paragraph("Γεύματα", styles["heading"]))
        rows = [["Ημ/νία", "Ώρα", "Προσφ.", "Ήπιε", "Formula", "Maxijul"]]
        for item in meals:
            event_time = item.actual_time or item.scheduled_time
            rows.append([
                item.date.strftime("%d/%m"),
                event_time.strftime("%H:%M"),
                f"{item.offered_ml} ml" if item.offered_ml is not None else "—",
                f"{item.consumed_ml} ml" if item.consumed_ml is not None else "—",
                item.formula or "—",
                f"{_numeric_scoops(item.supplement):g} scoop" if _numeric_scoops(item.supplement) else "—",
            ])
        table = Table(rows, colWidths=[22*mm, 20*mm, 26*mm, 26*mm, 55*mm, 26*mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("FONTSIZE", (0,0), (-1,-1), 7.5),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E9F4FF")),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDE5F0")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("PADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(table)
        story.append(Spacer(1, 4*mm))

    if glucose:
        story.append(Paragraph("Γλυκόζη", styles["heading"]))
        rows = [["Ημ/νία", "Ώρα", "Τιμή", "Σχέση"]]
        for item in glucose:
            rows.append([
                item.date.strftime("%d/%m"),
                item.time.strftime("%H:%M"),
                f"{item.value:g} mg/dL",
                item.get_context_display(),
            ])
        table = Table(rows, colWidths=[30*mm, 30*mm, 40*mm, 70*mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("FONTSIZE", (0,0), (-1,-1), 7.5),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#FFF1E6")),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#E9E0D7")),
            ("PADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(table)
        story.append(Spacer(1, 4*mm))

    if medications:
        story.append(Paragraph("Φάρμακα / συμπληρώματα", styles["heading"]))
        rows = [["Ημ/νία", "Ώρα", "Όνομα", "Ποσότητα"]]
        for item in medications:
            rows.append([
                item.date.strftime("%d/%m"),
                item.time.strftime("%H:%M"),
                item.name,
                f"{item.dose:g} {item.get_unit_display()}",
            ])
        table = Table(rows, colWidths=[30*mm, 25*mm, 75*mm, 40*mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), font_name),
            ("FONTSIZE", (0,0), (-1,-1), 7.5),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EBFFF4")),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#DDE9E3")),
            ("PADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(table)

    if not meals and not glucose and not medications:
        story.append(Paragraph("Δεν υπάρχουν καταχωρήσεις στο τελευταίο 24ωρο.", styles["body"]))

    doc.build(story)
    return response


@login_required
def meal_list(request):
    return render(request, "meals/list.html", {"meals": MealEntry.objects.all()})


@login_required
def meal_create(request):
    suggested_time = next_scheduled_time(timezone.localtime())
    form = MealEntryForm(
        request.POST or None,
        initial={
            "date": timezone.localdate(),
            "scheduled_time": suggested_time,
            "actual_time": suggested_time,
            "same_as_scheduled": True,
            "offered_ml": 175,
            "consumed_ml": 175,
            "formula": "5",
            "supplement": "1",
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
    return render(request, "growth/list.html", {"measurements": GrowthMeasurement.objects.all()})


@login_required
def growth_create(request):
    form = GrowthMeasurementForm(request.POST or None, initial={"date": timezone.localdate()})
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


@login_required
def medication_list(request):
    return render(request, "medications/list.html", {
        "medications": MedicationEntry.objects.all(),
    })


@login_required
def medication_create(request):
    form = MedicationEntryForm(
        request.POST or None,
        initial={
            "date": timezone.localdate(),
            "time": timezone.localtime().strftime("%H:%M"),
        },
    )
    if form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, "Η καταχώρηση φαρμάκου/συμπληρώματος αποθηκεύτηκε.")
        return redirect("medication_list")
    return render(request, "form.html", {"form": form, "title": "Νέο φάρμακο / συμπλήρωμα"})


@login_required
def medication_edit(request, pk):
    item = get_object_or_404(MedicationEntry, pk=pk)
    form = MedicationEntryForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Η καταχώρηση ενημερώθηκε.")
        return redirect("medication_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία φαρμάκου / συμπληρώματος"})


@login_required
def medication_delete(request, pk):
    item = get_object_or_404(MedicationEntry, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Η καταχώρηση διαγράφηκε.")
        return redirect("medication_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή φαρμάκου / συμπληρώματος"})


@login_required
def appointment_list(request):
    return render(request, "appointments/list.html", {
        "appointments": MedicalAppointment.objects.order_by("-date", "-time"),
        "today": timezone.localdate(),
    })


@login_required
def appointment_create(request):
    form = MedicalAppointmentForm(
        request.POST or None,
        initial={
            "date": timezone.localdate(),
            "time": "09:00",
            "reminder_days_before": 1,
            "status": "scheduled",
        },
    )
    if form.is_valid():
        form.save()
        messages.success(request, "Το ραντεβού αποθηκεύτηκε.")
        return redirect("appointment_list")
    return render(request, "form.html", {"form": form, "title": "Νέο ιατρικό ραντεβού"})


@login_required
def appointment_edit(request, pk):
    item = get_object_or_404(MedicalAppointment, pk=pk)
    form = MedicalAppointmentForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Το ραντεβού ενημερώθηκε.")
        return redirect("appointment_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία ραντεβού"})


@login_required
def appointment_delete(request, pk):
    item = get_object_or_404(MedicalAppointment, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Το ραντεβού διαγράφηκε.")
        return redirect("appointment_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή ραντεβού"})
