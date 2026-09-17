from collections import defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
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

    # Prevent accidental extremely large reports.
    max_days = 365
    if (end_date - start_date).days > max_days:
        start_date = end_date - timedelta(days=max_days)

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

    meals_by_date = defaultdict(list)
    glucose_by_date = defaultdict(list)
    growth_by_date = defaultdict(list)

    for item in meals:
        meals_by_date[item.date].append(item)

    for item in glucose:
        glucose_by_date[item.date].append(item)

    for item in growth:
        growth_by_date[item.date].append(item)

    dates = set(meals_by_date) | set(glucose_by_date) | set(growth_by_date)

    days = []
    for day_date in sorted(dates, reverse=True):
        day_meals = meals_by_date.get(day_date, [])
        day_glucose = glucose_by_date.get(day_date, [])
        day_growth = growth_by_date.get(day_date, [])

        total_consumed = sum(item.consumed_ml or 0 for item in day_meals)
        glucose_values = [float(item.value) for item in day_glucose]

        timeline = []

        for item in day_meals:
            display_time = item.actual_time or item.scheduled_time
            timeline.append(
                {
                    "time": display_time,
                    "kind": "meal",
                    "title": "Γεύμα",
                    "text": (
                        f"{item.consumed_ml if item.consumed_ml is not None else '—'} ml"
                        + (
                            f" από {item.offered_ml} ml"
                            if item.offered_ml is not None
                            else ""
                        )
                    ),
                    "extra": item.formula or "",
                }
            )

        for item in day_glucose:
            timeline.append(
                {
                    "time": item.time,
                    "kind": "glucose",
                    "title": "Γλυκόζη",
                    "text": f"{item.value:g} mg/dL",
                    "extra": item.get_context_display(),
                }
            )

        timeline.sort(key=lambda item: item["time"])

        days.append(
            {
                "date": day_date,
                "meals": day_meals,
                "glucose": day_glucose,
                "growth": day_growth,
                "timeline": timeline,
                "total_consumed": total_consumed,
                "glucose_min": min(glucose_values) if glucose_values else None,
                "glucose_max": max(glucose_values) if glucose_values else None,
            }
        )

    return days


@login_required
def dashboard(request):
    today = timezone.localdate()
    meals_today = MealEntry.objects.filter(date=today).order_by("scheduled_time")
    glucose_today = GlucoseReading.objects.filter(date=today).order_by("time")

    previous_days = build_history_days(today - timedelta(days=3), today - timedelta(days=1))

    context = {
        "today": today,
        "meals_today": meals_today,
        "glucose_today": glucose_today,
        "latest_glucose": GlucoseReading.objects.first(),
        "latest_growth": GrowthMeasurement.objects.first(),
        "consumed_total": sum(item.consumed_ml or 0 for item in meals_today),
        "next_meal_time": next_scheduled_time(timezone.localtime()),
        "schedule": SCHEDULED_TIMES,
        "previous_days": previous_days[:3],
    }
    return render(request, "dashboard.html", context)


@login_required
def history(request):
    start_date, end_date = history_range(request)
    days = build_history_days(start_date, end_date)

    return render(
        request,
        "history.html",
        {
            "days": days,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


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


@login_required
def history_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    start_date, end_date = history_range(request)
    days = build_history_days(start_date, end_date)

    response = HttpResponse(content_type="application/pdf")
    filename = f"giorgos-health-{start_date.isoformat()}-{end_date.isoformat()}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    font_name = _register_pdf_font()

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Giorgos Health - Ιστορικό",
        author="Giorgos Health",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleGreek",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#315D9D"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleGreek",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6C7892"),
        spaceAfter=12,
    )
    day_style = ParagraphStyle(
        "DayGreek",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#315D9D"),
        spaceBefore=6,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyGreek",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1F2A44"),
    )
    small_style = ParagraphStyle(
        "SmallGreek",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#596579"),
    )

    story = [
        Paragraph("Giorgos Health", title_style),
        Paragraph(
            f"Ιστορικό από {start_date.strftime('%d/%m/%Y')} έως {end_date.strftime('%d/%m/%Y')}",
            subtitle_style,
        ),
    ]

    if not days:
        story.append(Paragraph("Δεν υπάρχουν καταχωρήσεις για αυτή την περίοδο.", body_style))

    for index, day in enumerate(days):
        story.append(
            Paragraph(
                day["date"].strftime("%d/%m/%Y"),
                day_style,
            )
        )

        summary_parts = [
            f"Γεύματα: {len(day['meals'])}",
            f"Σύνολο: {day['total_consumed']} ml",
            f"Μετρήσεις γλυκόζης: {len(day['glucose'])}",
        ]
        if day["glucose_min"] is not None:
            summary_parts.append(
                f"Εύρος γλυκόζης: {day['glucose_min']:.0f}-{day['glucose_max']:.0f} mg/dL"
            )

        story.append(Paragraph(" · ".join(summary_parts), small_style))
        story.append(Spacer(1, 4 * mm))

        if day["meals"]:
            story.append(Paragraph("Γεύματα", body_style))
            meal_rows = [["Πρόγρ.", "Πραγμ.", "Προσφ.", "Ήπιε", "Formula"]]
            for item in day["meals"]:
                meal_rows.append(
                    [
                        item.scheduled_time.strftime("%H:%M"),
                        item.actual_time.strftime("%H:%M") if item.actual_time else "—",
                        f"{item.offered_ml} ml" if item.offered_ml is not None else "—",
                        f"{item.consumed_ml} ml" if item.consumed_ml is not None else "—",
                        item.formula or "—",
                    ]
                )

            table = Table(
                meal_rows,
                colWidths=[22 * mm, 22 * mm, 26 * mm, 24 * mm, 76 * mm],
                repeatRows=1,
            )
            table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), font_name),
                        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9F4FF")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#315D9D")),
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDE5F0")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 4 * mm))

        if day["glucose"]:
            story.append(Paragraph("Γλυκόζη", body_style))
            glucose_rows = [["Ώρα", "Τιμή", "Σχέση με γεύμα", "Σημειώσεις"]]
            for item in day["glucose"]:
                glucose_rows.append(
                    [
                        item.time.strftime("%H:%M"),
                        f"{item.value:g} mg/dL",
                        item.get_context_display(),
                        Paragraph(item.notes or "—", small_style),
                    ]
                )

            table = Table(
                glucose_rows,
                colWidths=[22 * mm, 30 * mm, 42 * mm, 76 * mm],
                repeatRows=1,
            )
            table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), font_name),
                        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF1E6")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#8A5428")),
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E9E0D7")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 4 * mm))

        if day["growth"]:
            story.append(Paragraph("Ανάπτυξη", body_style))
            for item in day["growth"]:
                growth_text = (
                    f"Βάρος: {item.weight_kg if item.weight_kg is not None else '—'} kg · "
                    f"Μήκος: {item.length_cm if item.length_cm is not None else '—'} cm · "
                    f"Περίμετρος κεφαλής: {item.head_cm if item.head_cm is not None else '—'} cm"
                )
                story.append(Paragraph(growth_text, small_style))
                if item.notes:
                    story.append(Paragraph(f"Σημειώσεις: {item.notes}", small_style))

        if index < len(days) - 1:
            story.append(Spacer(1, 5 * mm))

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
