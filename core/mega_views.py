import base64
import io
import os
import re
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

import qrcode
import requests
from PIL import Image, ImageOps
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .access import user_role
from .feeding_timing import (
    FIXED_FEED_TIMES,
    meal_finished_datetime,
)
from .advanced_views import _matching_safety_rules, feeding_stats, get_profile
from .restriction_checks import baseline_restriction_checks
from .mega_forms import (
    CreateAccessUserForm,
    DoctorQuestionAnswerForm,
    DoctorQuestionForm,
    EditAccessUserForm,
    EmergencyShareForm,
    HealthReminderForm,
    LabResultForm,
    ScannedProductForm,
)
from .models import (
    BackupRun,
    ChildProfile,
    DiaperEntry,
    DoctorQuestion,
    GlucoseReading,
    GrowthMeasurement,
    HealthReminder,
    LabResult,
    MealEntry,
    MedicalAppointment,
    MedicalDocument,
    MedicationEntry,
    MedicationPlan,
    ProductSafetyRecord,
    SymptomEntry,
    UserAccessLog,
    UserAccessProfile,
    VaccineEntry,
)


def _photo_response(data, mime, filename, *, optimize=False):
    if not data:
        raise Http404("Δεν υπάρχει φωτογραφία.")

    payload = bytes(data)
    content_type = mime or "image/jpeg"
    safe_name = Path(filename or "photo.jpg").name

    if optimize:
        try:
            with Image.open(io.BytesIO(payload)) as source:
                image = ImageOps.exif_transpose(source)
                image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                if image.mode not in {"RGB", "L"}:
                    image = image.convert("RGB")
                elif image.mode == "L":
                    image = image.convert("RGB")

                output = io.BytesIO()
                image.save(
                    output,
                    format="JPEG",
                    quality=82,
                    optimize=True,
                    progressive=True,
                )
                optimized = output.getvalue()

            if optimized and len(optimized) < len(payload):
                payload = optimized
                content_type = "image/jpeg"
                safe_name = f"{Path(safe_name).stem or 'photo'}.jpg"
        except Exception:
            pass

    response = HttpResponse(payload, content_type=content_type)
    response["Content-Disposition"] = f'inline; filename="{safe_name}"'
    response["Cache-Control"] = "private, max-age=86400"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
def symptom_photo(request, pk):
    item = get_object_or_404(
        SymptomEntry.objects.only("photo_data", "photo_mime", "photo_name"),
        pk=pk,
    )
    return _photo_response(item.photo_data, item.photo_mime, item.photo_name)


@login_required
def diaper_photo(request, pk):
    # Pull only the photo columns from PostgreSQL. The normal detail image is
    # optimized for mobile; ?full=1 keeps access to the stored original.
    item = get_object_or_404(
        DiaperEntry.objects.only("photo_data", "photo_mime", "photo_name"),
        pk=pk,
    )
    return _photo_response(
        item.photo_data,
        item.photo_mime,
        item.photo_name,
        optimize=request.GET.get("full") != "1",
    )


@login_required
def product_label_photo(request, pk):
    item = get_object_or_404(ProductSafetyRecord, pk=pk)
    return _photo_response(item.label_photo_data, item.label_photo_mime, item.label_photo_name)


def _analysis_payload(kind, name, ingredients):
    ingredients = (ingredients or "").strip()
    restriction_checks = baseline_restriction_checks(ingredients)

    if not ingredients:
        return {
            "level": "needs_ingredients",
            "title": "Χρειάζονται συστατικά για έλεγχο",
            "decision": "caution",
            "matches": [],
            "restriction_checks": restriction_checks,
        }

    matches = _matching_safety_rules(kind, ingredients)
    avoid = [r for r in matches if r.guidance == "avoid"]
    caution = [r for r in matches if r.guidance == "caution"]

    if avoid:
        level = "avoid"
        title = "Περιέχει καταχωρημένο περιορισμό"
        decision = "avoid"
    elif caution:
        level = "caution"
        title = "Χρειάζεται έλεγχος"
        decision = "caution"
    else:
        level = "clear"
        title = "Δεν εντοπίστηκε λακτόζη, ζάχαρη ή φρουκτόζη"
        decision = "checked"

    return {
        "level": level,
        "title": title,
        "decision": decision,
        "restriction_checks": restriction_checks,
        "matches": [
            {"term": r.term, "guidance": r.guidance, "label": r.get_guidance_display(), "note": r.note}
            for r in matches
        ],
    }


@login_required
def scanner_check(request):
    kind = (request.GET.get("kind") or "food").strip()
    name = (request.GET.get("name") or "").strip()
    ingredients = (request.GET.get("ingredients") or "").strip()
    return JsonResponse(_analysis_payload(kind, name, ingredients))


def _openfoodfacts_product(code):
    """
    Lookup a barcode in Open Food Facts.

    Return a normalized dict or None. The ingredient text is preferred, but an
    ingredient-label image can be returned as a fallback for browser OCR.
    """
    url = f"https://world.openfoodfacts.org/api/v2/product/{code}"
    response = requests.get(
        url,
        params={
            "fields": (
                "code,product_name,product_name_el,product_name_en,brands,"
                "ingredients_text,ingredients_text_el,ingredients_text_en,"
                "image_ingredients_url,image_ingredients_small_url"
            )
        },
        headers={
            "User-Agent": "GiorgosHealth/1.1 (private family health tracker)"
        },
        timeout=7,
    )
    response.raise_for_status()
    payload = response.json()
    product = payload.get("product") or {}

    if payload.get("status") != 1 or not product:
        return None

    name = (
        product.get("product_name_el")
        or product.get("product_name")
        or product.get("product_name_en")
        or product.get("brands")
        or f"Barcode {code}"
    )
    ingredients = (
        product.get("ingredients_text_el")
        or product.get("ingredients_text")
        or product.get("ingredients_text_en")
        or ""
    )
    ingredients_image = (
        product.get("image_ingredients_url")
        or product.get("image_ingredients_small_url")
        or ""
    )

    return {
        "name": name,
        "ingredients": ingredients,
        "ingredients_image": ingredients_image,
    }


def _safe_openfoodfacts_image_url(url):
    if not url:
        return None

    try:
        parsed = urlparse(url)
    except Exception:
        return None

    if parsed.scheme != "https":
        return None

    hostname = (parsed.hostname or "").lower()
    allowed_hosts = {
        "images.openfoodfacts.org",
        "world.openfoodfacts.org",
        "static.openfoodfacts.org",
    }
    if hostname not in allowed_hosts:
        return None

    return url


@login_required
def barcode_lookup(request, code):
    code = re.sub(r"[^0-9A-Za-z_-]", "", code or "")[:64]
    if not code:
        return JsonResponse(
            {"found": False, "error": "Μη έγκυρο barcode."},
            status=400,
        )

    local = (
        ProductSafetyRecord.objects.filter(barcode=code)
        .order_by("-reviewed_on", "-updated_at")
        .first()
    )

    # If our local record already has ingredients, use it immediately.
    if local and (local.ingredients or "").strip():
        return JsonResponse({
            "found": True,
            "source": "local",
            "local_review": True,
            "id": local.pk,
            "name": local.name,
            "barcode": local.barcode,
            "kind": local.kind,
            "ingredients": local.ingredients,
            "decision": local.decision,
            "decision_label": local.get_decision_display(),
            "reviewed_on": local.reviewed_on.isoformat() if local.reviewed_on else "",
            "confirmed_by": local.confirmed_by,
            "analysis": _analysis_payload(local.kind, local.name, local.ingredients),
            "ingredients_image_available": False,
        })

    # If the product is local but ingredients were never saved, continue
    # online instead of stopping at the incomplete local record.
    off = None
    try:
        off = _openfoodfacts_product(code)
    except Exception:
        off = None

    if off:
        name = (local.name if local and local.name else "") or off["name"]
        ingredients = off["ingredients"] or (local.ingredients if local else "") or ""
        image_url = _safe_openfoodfacts_image_url(off["ingredients_image"])

        payload = {
            "found": True,
            "source": "local+openfoodfacts" if local else "openfoodfacts",
            "local_review": bool(local),
            "name": name,
            "barcode": code,
            "kind": local.kind if local else "food",
            "ingredients": ingredients,
            "analysis": _analysis_payload(
                local.kind if local else "food",
                name,
                ingredients,
            ),
            "ingredients_image_available": bool(image_url),
            "ingredients_image_proxy": (
                reverse("barcode_ingredients_image", kwargs={"code": code})
                if image_url
                else ""
            ),
        }

        if local:
            payload.update({
                "id": local.pk,
                "decision": local.decision,
                "decision_label": local.get_decision_display(),
                "reviewed_on": local.reviewed_on.isoformat() if local.reviewed_on else "",
                "confirmed_by": local.confirmed_by,
            })

        return JsonResponse(payload)

    # No online product. Still return the local record if it exists, even if
    # incomplete, so the user does not lose previously saved metadata.
    if local:
        return JsonResponse({
            "found": True,
            "source": "local",
            "local_review": True,
            "id": local.pk,
            "name": local.name,
            "barcode": local.barcode,
            "kind": local.kind,
            "ingredients": local.ingredients,
            "decision": local.decision,
            "decision_label": local.get_decision_display(),
            "reviewed_on": local.reviewed_on.isoformat() if local.reviewed_on else "",
            "confirmed_by": local.confirmed_by,
            "analysis": _analysis_payload(local.kind, local.name, local.ingredients),
            "ingredients_image_available": False,
        })

    return JsonResponse({
        "found": False,
        "source": "none",
        "barcode": code,
        "message": (
            "Δεν βρέθηκε το προϊόν online. "
            "Φωτογράφισε την ετικέτα συστατικών για έλεγχο."
        ),
    })


@login_required
def barcode_ingredients_image(request, code):
    """
    Same-origin proxy for the ingredient-label photo published by Open Food
    Facts. This lets Tesseract.js OCR the remote label without cross-origin
    browser restrictions.
    """
    code = re.sub(r"[^0-9A-Za-z_-]", "", code or "")[:64]
    if not code:
        raise Http404("Μη έγκυρο barcode.")

    try:
        product = _openfoodfacts_product(code)
    except Exception:
        product = None

    image_url = _safe_openfoodfacts_image_url(
        product.get("ingredients_image") if product else ""
    )
    if not image_url:
        raise Http404("Δεν υπάρχει φωτογραφία συστατικών.")

    try:
        image_response = requests.get(
            image_url,
            headers={
                "User-Agent": "GiorgosHealth/1.1 (private family health tracker)"
            },
            timeout=10,
            stream=True,
        )
        image_response.raise_for_status()

        # Verify the final URL too in case of redirects.
        if not _safe_openfoodfacts_image_url(image_response.url):
            raise Http404("Μη επιτρεπτή πηγή φωτογραφίας.")

        content_type = (
            image_response.headers.get("Content-Type") or "image/jpeg"
        ).split(";")[0].strip().lower()
        if not content_type.startswith("image/"):
            raise Http404("Το αρχείο δεν είναι εικόνα.")

        chunks = []
        total = 0
        max_bytes = 6 * 1024 * 1024
        for chunk in image_response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                raise Http404("Η φωτογραφία είναι πολύ μεγάλη.")
            chunks.append(chunk)

        response = HttpResponse(b"".join(chunks), content_type=content_type)
        response["Cache-Control"] = "private, max-age=3600"
        return response
    except Http404:
        raise
    except Exception:
        raise Http404("Δεν ήταν δυνατή η λήψη φωτογραφίας συστατικών.")


@login_required
def product_scanner(request):
    initial = {
        "kind": request.GET.get("kind", "food"),
        "barcode": request.GET.get("barcode", ""),
        "name": request.GET.get("name", ""),
        "reviewed_on": timezone.localdate(),
    }
    form = ScannedProductForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, "Το προϊόν/φάρμακο αποθηκεύτηκε μαζί με την αξιολόγηση.")
        return redirect("reviewed_products")
    return render(request, "scanner/index.html", {"form": form})


@login_required
def reviewed_products(request):
    tab = request.GET.get("tab", "checked")
    q = (request.GET.get("q") or "").strip()
    qs = ProductSafetyRecord.objects.all().order_by("-reviewed_on", "-updated_at")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(barcode__icontains=q) | Q(ingredients__icontains=q))
    if tab == "avoid":
        qs = qs.filter(decision="avoid")
    elif tab == "caution":
        qs = qs.filter(decision="caution")
    else:
        tab = "checked"
        qs = qs.filter(decision__in=["checked", "confirmed"])
    return render(
        request,
        "scanner/reviewed.html",
        {
            "items": qs,
            "tab": tab,
            "q": q,
            "counts": {
                "checked": ProductSafetyRecord.objects.filter(decision__in=["checked", "confirmed"]).count(),
                "avoid": ProductSafetyRecord.objects.filter(decision="avoid").count(),
                "caution": ProductSafetyRecord.objects.filter(decision="caution").count(),
            },
        },
    )


def _lab_category(test_name):
    name = (test_name or "").casefold()

    if name.startswith("abg ") or name in {"lactate", "abg glucose"}:
        return "Αέρια αίματος"

    if name in {
        "wbc", "neutrophils", "lymphocytes", "monocytes",
        "hemoglobin", "hematocrit", "mcv", "mch", "platelets", "crp"
    }:
        return "Αιματολογικά"

    if name in {
        "alp", "ggt", "alt", "ast", "ldh", "cpk",
        "triglycerides", "uric acid", "ammonia"
    }:
        return "Ήπαρ / μεταβολικά"

    if name in {"urea", "creatinine", "sodium", "potassium", "glucose"}:
        return "Νεφρά / ηλεκτρολύτες / γλυκόζη"

    return "Άλλα"


@login_required
def lab_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = LabResult.objects.all().order_by("-date", "-time", "test_name")

    if q:
        qs = qs.filter(
            Q(test_name__icontains=q)
            | Q(laboratory__icontains=q)
            | Q(notes__icontains=q)
        )

    items = list(qs)
    dates = sorted({item.date for item in items}, reverse=True)

    category_order = [
        "Αιματολογικά",
        "Νεφρά / ηλεκτρολύτες / γλυκόζη",
        "Ήπαρ / μεταβολικά",
        "Αέρια αίματος",
        "Άλλα",
    ]

    grouped = {}
    for item in items:
        category = _lab_category(item.test_name)
        grouped.setdefault(category, {}).setdefault(item.test_name, {}).setdefault(item.date, []).append(item)

    sections = []
    for category in category_order:
        tests = grouped.get(category)
        if not tests:
            continue

        rows = []
        for test_name in sorted(tests, key=lambda value: value.casefold()):
            by_date = tests[test_name]
            cells = []
            units = []

            for lab_date in dates:
                cell_items = by_date.get(lab_date, [])
                cells.append(cell_items)
                for entry in cell_items:
                    if entry.unit and entry.unit not in units:
                        units.append(entry.unit)

            rows.append({
                "test_name": test_name,
                "unit": " / ".join(units),
                "cells": cells,
            })

        sections.append({
            "name": category,
            "slug": (
                category.casefold()
                .replace(" ", "-")
                .replace("/", "-")
                .replace("ά", "α")
                .replace("έ", "ε")
                .replace("ή", "η")
                .replace("ί", "ι")
                .replace("ό", "ο")
                .replace("ύ", "υ")
                .replace("ώ", "ω")
            ),
            "rows": rows,
        })

    return render(
        request,
        "labs/list.html",
        {
            "items": items,
            "q": q,
            "dates": dates,
            "sections": sections,
            "result_count": len(items),
            "date_count": len(dates),
        },
    )


@login_required
def lab_create(request):
    form = LabResultForm(
        request.POST or None,
        initial={"date": timezone.localdate(), "time": timezone.localtime().strftime("%H:%M")},
    )
    if form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, "Η εργαστηριακή τιμή αποθηκεύτηκε.")
        return redirect("lab_list")
    return render(request, "form.html", {"form": form, "title": "Νέα εργαστηριακή τιμή"})


@login_required
def lab_edit(request, pk):
    item = get_object_or_404(LabResult, pk=pk)
    form = LabResultForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Η εργαστηριακή τιμή ενημερώθηκε.")
        return redirect("lab_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία εργαστηριακής τιμής"})


@login_required
def lab_delete(request, pk):
    item = get_object_or_404(LabResult, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Η εργαστηριακή τιμή διαγράφηκε.")
        return redirect("lab_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή εργαστηριακής τιμής"})


@login_required
def lab_chart(request):
    name = (request.GET.get("name") or "").strip()
    names = list(LabResult.objects.order_by("test_name").values_list("test_name", flat=True).distinct())
    if not name and names:
        name = names[0]
    rows = list(LabResult.objects.filter(test_name=name).order_by("date", "time")) if name else []
    chart = {
        "labels": [r.date.strftime("%d/%m/%Y") for r in rows],
        "values": [float(r.value) for r in rows],
        "units": rows[-1].unit if rows else "",
    }
    return render(request, "labs/chart.html", {"name": name, "names": names, "rows": rows, "chart": chart})


@login_required
def reminder_list(request):
    now = timezone.now()
    readonly_doctor = user_role(request.user) == "doctor_readonly"

    # Parent view may safely synchronize automatic reminders on page load.
    # Doctor GET requests remain strictly read-only and never create/update rows.
    if not readonly_doctor:
        from .auto_reminders import sync_all_automatic_reminders
        sync_all_automatic_reminders(now=now)

    # Manual reminders stay in their own list. Automatic reminders are shown
    # separately below as a compact "next notifications" panel.
    items = HealthReminder.objects.filter(auto_generated=False)

    # Show the next automatic notifications separately so the page never gives
    # the false impression that there are "no reminders".
    next_auto_notifications = []
    auto_items = HealthReminder.objects.filter(
        auto_generated=True,
        active=True,
        completed=False,
    )

    for reminder in auto_items:
        notification_at = reminder.due_at - timedelta(
            minutes=reminder.notify_minutes_before or 0
        )

        # Keep future notifications and very recent due notifications visible.
        if notification_at < now - timedelta(minutes=5):
            continue

        next_auto_notifications.append(
            {
                "item": reminder,
                "notification_at": notification_at,
            }
        )

    next_auto_notifications.sort(key=lambda row: row["notification_at"])
    next_auto_notifications = next_auto_notifications[:5]

    push_device_count = 0
    if not readonly_doctor:
        from .models import PushSubscription
        push_device_count = PushSubscription.objects.filter(
            user=request.user,
            active=True,
        ).count()

    return render(
        request,
        "reminders/list.html",
        {
            "items": items,
            "now": now,
            "push_device_count": push_device_count,
            "next_auto_notifications": next_auto_notifications,
            "fixed_meal_times": [value.strftime("%H:%M") for value in FIXED_FEED_TIMES],
            "meal_notify_minutes_before": 12,
            "medication_reminder_plans": MedicationPlan.objects.filter(
                active=True,
                reminder_enabled=True,
                reminder_time__isnull=False,
            ).order_by("reminder_time", "name"),
        },
    )


def _save_reminder_form(form, request, instance=None):
    previous = None
    if instance and instance.pk:
        previous = HealthReminder.objects.filter(pk=instance.pk).first()

    item = form.save(commit=False)
    due_date = form.cleaned_data["due_date"]
    due_time = form.cleaned_data["due_time"]
    naive = datetime.combine(due_date, due_time)
    item.due_at = timezone.make_aware(naive, timezone.get_current_timezone())

    if not instance:
        item.created_by = request.user

    if previous and (
        previous.due_at != item.due_at
        or previous.notify_minutes_before != item.notify_minutes_before
        or previous.repeat_if_incomplete_minutes != item.repeat_if_incomplete_minutes
    ):
        item.push_notified_at = None
        item.push_repeat_notified_at = None

    item.save()
    return item


@login_required
def reminder_create(request):
    form = HealthReminderForm(
        request.POST or None,
        initial={"due_date": timezone.localdate(), "due_time": timezone.localtime().strftime("%H:%M")},
    )
    if form.is_valid():
        _save_reminder_form(form, request)
        messages.success(request, "Η υπενθύμιση αποθηκεύτηκε.")
        return redirect("reminder_list")
    return render(request, "form.html", {"form": form, "title": "Νέα υπενθύμιση"})


@login_required
def reminder_edit(request, pk):
    item = get_object_or_404(HealthReminder, pk=pk)
    if item.auto_generated:
        messages.info(
            request,
            "Η υπενθύμιση δημιουργείται αυτόματα από το Giorgos Health και δεν χρειάζεται χειροκίνητη επεξεργασία.",
        )
        return redirect("reminder_list")
    form = HealthReminderForm(request.POST or None, instance=item)
    if form.is_valid():
        _save_reminder_form(form, request, item)
        messages.success(request, "Η υπενθύμιση ενημερώθηκε.")
        return redirect("reminder_list")
    return render(request, "form.html", {"form": form, "title": "Επεξεργασία υπενθύμισης"})


@login_required
def reminder_done(request, pk):
    item = get_object_or_404(HealthReminder, pk=pk)
    if request.method == "POST":
        item.completed = True
        item.save(update_fields=["completed", "updated_at"])
    return redirect("reminder_list")


@login_required
def reminder_delete(request, pk):
    item = get_object_or_404(HealthReminder, pk=pk)
    if item.auto_generated:
        messages.info(
            request,
            "Η υπενθύμιση είναι αυτόματη και διαχειρίζεται από το Giorgos Health.",
        )
        return redirect("reminder_list")
    if request.method == "POST":
        item.delete()
        messages.success(request, "Η υπενθύμιση διαγράφηκε.")
        return redirect("reminder_list")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή υπενθύμισης"})


@login_required
def doctor_questions(request):
    tab = request.GET.get("tab", "pending")
    qs = DoctorQuestion.objects.all()
    if tab == "answered":
        qs = qs.filter(status="answered")
    else:
        tab = "pending"
        qs = qs.filter(status="pending")
    return render(request, "questions/list.html", {"items": qs, "tab": tab})


@login_required
def doctor_question_create(request):
    form = DoctorQuestionForm(request.POST or None)
    if form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, "Η ερώτηση αποθηκεύτηκε.")
        return redirect("doctor_questions")
    return render(request, "form.html", {"form": form, "title": "Νέα ερώτηση για τον γιατρό"})


@login_required
def doctor_question_answer(request, pk):
    item = get_object_or_404(DoctorQuestion, pk=pk)
    form = DoctorQuestionAnswerForm(request.POST or None, instance=item)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.status = "answered"
        obj.answered_at = timezone.now()
        obj.save()
        messages.success(request, "Η ερώτηση σημειώθηκε ως απαντημένη.")
        return redirect("doctor_questions")
    return render(request, "form.html", {"form": form, "title": "Απάντηση / οδηγία γιατρού"})


@login_required
def doctor_question_delete(request, pk):
    item = get_object_or_404(DoctorQuestion, pk=pk)
    if request.method == "POST":
        item.delete()
        return redirect("doctor_questions")
    return render(request, "confirm_delete.html", {"title": "Διαγραφή ερώτησης"})


@login_required
def doctor_visit(request):
    today = timezone.localdate()
    start = today - timedelta(days=7)
    return render(
        request,
        "doctor/visit.html",
        {
            "questions": DoctorQuestion.objects.filter(status="pending"),
            "meals": MealEntry.objects.filter(date__range=(start, today)).order_by("-date", "-actual_time")[:20],
            "glucose": GlucoseReading.objects.filter(date__range=(start, today)).order_by("-date", "-time")[:20],
            "labs": LabResult.objects.order_by("-date", "-time")[:15],
            "symptoms": SymptomEntry.objects.filter(date__range=(start, today))[:15],
            "latest_growth": GrowthMeasurement.objects.first(),
            "upcoming": MedicalAppointment.objects.filter(date__gte=today, status="scheduled").order_by("date", "time")[:5],
        },
    )


@login_required
def hospital_mode(request):
    today = timezone.localdate()
    recent_meals = list(MealEntry.objects.order_by("-date", "-scheduled_time")[:40])
    last_meal = None
    if recent_meals:
        from .feeding_timing import meal_start_datetime
        last_meal = max(
            recent_meals,
            key=lambda meal: meal_start_datetime(meal) or timezone.make_aware(
                datetime.combine(meal.date, meal.scheduled_time),
                timezone.get_current_timezone(),
            ),
        )

    latest_lab = LabResult.objects.order_by("-date", "-time").first()
    latest_lab_date = latest_lab.date if latest_lab else None
    latest_labs = (
        LabResult.objects.filter(date=latest_lab_date).order_by("test_name", "time")
        if latest_lab_date
        else LabResult.objects.none()
    )

    return render(
        request,
        "hospital/mode.html",
        {
            "latest_glucose": GlucoseReading.objects.first(),
            "last_meal": last_meal,
            "medications": MedicationEntry.objects.filter(date=today).order_by("-time"),
            "latest_lab_date": latest_lab_date,
            "labs": latest_labs,
            "profile": get_profile(),
        },
    )


def _emergency_public_context(profile):
    return {
        "profile": profile,
        "latest_growth": GrowthMeasurement.objects.first(),
        "latest_glucose": GlucoseReading.objects.first(),
    }


def emergency_public(request, token):
    profile = get_object_or_404(ChildProfile, emergency_share_token=token, emergency_share_enabled=True)
    return render(request, "emergency/public.html", _emergency_public_context(profile))


@login_required
def emergency_share_rotate(request):
    profile = get_profile()
    if not profile:
        raise Http404
    if request.method == "POST":
        profile.emergency_share_token = uuid.uuid4()
        profile.save()
        messages.success(request, "Δημιουργήθηκε νέο Emergency QR/link. Το παλιό link δεν ισχύει πλέον.")
    return redirect("emergency_card")


@login_required
def emergency_share_settings(request):
    profile = get_profile()
    if not profile:
        raise Http404
    form = EmergencyShareForm(
        request.POST or None,
        initial={
            "enabled": profile.emergency_share_enabled,
            "show_identity": profile.emergency_share_show_identity,
            "show_instructions": profile.emergency_share_show_instructions,
            "show_feeding": profile.emergency_share_show_feeding,
            "show_doctors": profile.emergency_share_show_doctors,
            "show_phones": profile.emergency_share_show_phones,
            "show_glucose": profile.emergency_share_show_glucose,
        },
    )
    if request.method == "POST" and form.is_valid():
        profile.emergency_share_enabled = bool(form.cleaned_data["enabled"])
        profile.emergency_share_show_identity = bool(form.cleaned_data["show_identity"])
        profile.emergency_share_show_instructions = bool(form.cleaned_data["show_instructions"])
        profile.emergency_share_show_feeding = bool(form.cleaned_data["show_feeding"])
        profile.emergency_share_show_doctors = bool(form.cleaned_data["show_doctors"])
        profile.emergency_share_show_phones = bool(form.cleaned_data["show_phones"])
        profile.emergency_share_show_glucose = bool(form.cleaned_data["show_glucose"])
        profile.save()
        messages.success(request, "Οι ρυθμίσεις Emergency QR ενημερώθηκαν.")
        return redirect("emergency_card")
    return render(request, "form.html", {"form": form, "title": "Emergency QR — Ρυθμίσεις"})


def emergency_qr_data(request, profile):
    if not profile or not profile.emergency_share_enabled:
        return None, None
    url = request.build_absolute_uri(reverse("emergency_public", args=[profile.emergency_share_token]))
    img = qrcode.make(url)
    out = io.BytesIO()
    img.save(out, format="PNG")
    data_uri = "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")
    return data_uri, url


@login_required
def global_search(request):
    q = (request.GET.get("q") or "").strip()
    results = {}
    if q:
        date_value = None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                date_value = datetime.strptime(q, fmt).date()
                break
            except ValueError:
                pass
        if date_value is None:
            for fmt in ("%d/%m", "%d-%m"):
                try:
                    parsed = datetime.strptime(q, fmt)
                    date_value = parsed.replace(year=timezone.localdate().year).date()
                    break
                except ValueError:
                    pass

        doc_q = Q(title__icontains=q) | Q(notes__icontains=q) | Q(original_filename__icontains=q)
        lab_q = Q(test_name__icontains=q) | Q(laboratory__icontains=q) | Q(notes__icontains=q)
        med_q = Q(name__icontains=q) | Q(notes__icontains=q)
        appt_q = Q(doctor__icontains=q) | Q(clinic__icontains=q) | Q(purpose__icontains=q) | Q(notes__icontains=q)
        prod_q = Q(name__icontains=q) | Q(barcode__icontains=q) | Q(ingredients__icontains=q) | Q(notes__icontains=q)
        symptom_q = Q(symptom__icontains=q) | Q(notes__icontains=q)
        question_q = Q(question__icontains=q) | Q(answer__icontains=q)

        if date_value:
            doc_q |= Q(date=date_value)
            lab_q |= Q(date=date_value)
            med_q |= Q(date=date_value)
            appt_q |= Q(date=date_value)
            symptom_q |= Q(date=date_value)

        results["documents"] = MedicalDocument.objects.filter(doc_q)[:12]
        results["labs"] = LabResult.objects.filter(lab_q)[:12]
        results["medications"] = MedicationEntry.objects.filter(med_q)[:12]
        results["appointments"] = MedicalAppointment.objects.filter(appt_q)[:12]
        results["products"] = ProductSafetyRecord.objects.filter(prod_q)[:12]
        results["symptoms"] = SymptomEntry.objects.filter(symptom_q)[:12]
        results["questions"] = DoctorQuestion.objects.filter(question_q)[:12]

        if date_value:
            results["meals"] = MealEntry.objects.filter(date=date_value)[:12]
            results["glucose"] = GlucoseReading.objects.filter(date=date_value)[:12]
            results["vaccines"] = VaccineEntry.objects.filter(Q(date=date_value) | Q(next_date=date_value))[:12]

    total = sum(len(value) for value in results.values()) if q else 0
    return render(request, "search/results.html", {"q": q, "results": results, "total": total})


def daily_summary_data(day):
    meals = list(MealEntry.objects.filter(date=day))
    glucose = list(GlucoseReading.objects.filter(date=day))
    meds = list(MedicationEntry.objects.filter(date=day))
    diapers = list(DiaperEntry.objects.filter(date=day))
    symptoms = list(SymptomEntry.objects.filter(date=day))
    consumed = sum(m.consumed_ml or 0 for m in meals)
    avg_meal = round(consumed / len(meals), 1) if meals else None
    glucose_values = [float(g.value) for g in glucose]

    profile = get_profile()
    maxijul = None
    if profile:
        from .views import maxijul_day_summary
        maxijul = maxijul_day_summary(profile, meals)

    return {
        "date": day,
        "meals": meals,
        "meal_count": len(meals),
        "consumed": consumed,
        "avg_meal": avg_meal,
        "maxijul": maxijul,
        "glucose": glucose,
        "glucose_count": len(glucose),
        "glucose_avg": round(sum(glucose_values) / len(glucose_values), 1) if glucose_values else None,
        "medications": meds,
        "diapers": diapers,
        "symptoms": symptoms,
    }


@login_required
def daily_summary(request):
    raw = request.GET.get("date")
    try:
        day = datetime.strptime(raw, "%Y-%m-%d").date() if raw else timezone.localdate()
    except ValueError:
        day = timezone.localdate()
    return render(request, "summary/daily.html", {"summary": daily_summary_data(day)})


@login_required
def daily_summary_pdf(request):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from xml.sax.saxutils import escape
    from .views import _pdf_styles

    raw = request.GET.get("date")
    try:
        day = datetime.strptime(raw, "%Y-%m-%d").date() if raw else timezone.localdate()
    except ValueError:
        day = timezone.localdate()

    summary = daily_summary_data(day)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="giorgos-health-summary-{day.isoformat()}.pdf"'
    font_name, styles = _pdf_styles()
    doc = SimpleDocTemplate(response, pagesize=A4, leftMargin=14*mm, rightMargin=14*mm, topMargin=14*mm, bottomMargin=14*mm)
    story = [
        Paragraph("Giorgos Health — Daily Health Summary", styles["title"]),
        Paragraph("Giorgos Panayiotis Michael", styles["heading"]),
        Paragraph(day.strftime("%d/%m/%Y"), styles["subtitle"]),
        Spacer(1, 4*mm),
        Paragraph(f"Γεύματα: {summary['meal_count']} · Σύνολο: {summary['consumed']} ml · Μ.ό.: {summary['avg_meal'] or '—'} ml", styles["body"]),
        Paragraph(
            (
                f"Maxijul: {summary['maxijul']['total_scoops']:g} scoops · "
                f"≈ {summary['maxijul']['grams']:g} g · "
                f"≈ {summary['maxijul']['kcal']:g} kcal"
            )
            if summary.get("maxijul")
            else "Maxijul: —",
            styles["body"],
        ),
        Paragraph(f"Γλυκόζη: {summary['glucose_count']} μετρήσεις · Μ.ό.: {summary['glucose_avg'] if summary['glucose_avg'] is not None else '—'} mg/dL", styles["body"]),
        Paragraph(f"Φάρμακα/συμπληρώματα: {len(summary['medications'])}", styles["body"]),
        Paragraph(f"Πάνες: {len(summary['diapers'])} · Συμπτώματα: {len(summary['symptoms'])}", styles["body"]),
        Spacer(1, 5*mm),
    ]
    rows = [["Έναρξη–Τέλος", "Γεύμα ml", "Γλυκόζη mg/dL"]]
    by_time = {}
    for m in summary["meals"]:
        start_label = (m.actual_time or m.scheduled_time).strftime("%H:%M")
        finish_label = m.finished_time.strftime("%H:%M") if m.finished_time else "—"
        key = f"{start_label}–{finish_label}"
        by_time.setdefault(key, ["", ""])
        by_time[key][0] = str(m.consumed_ml or "")
    for g in summary["glucose"]:
        key = g.time.strftime("%H:%M")
        by_time.setdefault(key, ["", ""])
        by_time[key][1] = str(g.value)
    for key in sorted(by_time):
        rows.append([key, *by_time[key]])
    table = Table(rows, colWidths=[40*mm, 55*mm, 55*mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), font_name),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EAF2FF")),
        ("GRID", (0,0), (-1,-1), .25, colors.HexColor("#DDE5F0")),
        ("PADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(table)
    doc.build(story)
    return response


def _superuser(user):
    return user.is_authenticated and user.is_superuser


@user_passes_test(_superuser)
def user_access_list(request):
    users = User.objects.all().order_by("username")
    rows = []
    for user in users:
        profile, _ = UserAccessProfile.objects.get_or_create(user=user)
        latest_access = (
            UserAccessLog.objects.filter(user=user)
            .order_by("-login_at")
            .first()
        )
        rows.append(
            {
                "user": user,
                "profile": profile,
                "latest_access": latest_access,
            }
        )
    return render(request, "users/list.html", {"rows": rows})


@user_passes_test(_superuser)
def user_access_log(request):
    q = (request.GET.get("q") or "").strip()
    user_id = (request.GET.get("user") or "").strip()

    logs = (
        UserAccessLog.objects
        .select_related("user", "user__access_profile")
        .all()
        .order_by("-login_at")
    )

    if q:
        logs = logs.filter(
            Q(user__username__icontains=q)
            | Q(user__access_profile__display_name__icontains=q)
            | Q(user_agent__icontains=q)
        )

    if user_id.isdigit():
        logs = logs.filter(user_id=int(user_id))

    paginator = Paginator(logs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    users = (
        User.objects.select_related("access_profile")
        .all()
        .order_by("username")
    )

    return render(
        request,
        "users/access_log.html",
        {
            "page_obj": page_obj,
            "logs": page_obj.object_list,
            "users": users,
            "q": q,
            "selected_user": user_id,
        },
    )


@user_passes_test(_superuser)
def user_access_create(request):
    form = CreateAccessUserForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        UserAccessProfile.objects.update_or_create(
            user=user,
            defaults={"role": form.cleaned_data["role"], "display_name": form.cleaned_data["display_name"]},
        )
        messages.success(request, "Ο χρήστης δημιουργήθηκε.")
        return redirect("user_access_list")
    return render(request, "form.html", {"form": form, "title": "Νέος χρήστης"})


@user_passes_test(_superuser)
def user_access_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile, _ = UserAccessProfile.objects.get_or_create(user=user)
    form = EditAccessUserForm(
        request.POST or None,
        initial={"role": profile.role, "display_name": profile.display_name, "is_active": user.is_active},
    )
    if form.is_valid():
        profile.role = form.cleaned_data["role"]
        profile.display_name = form.cleaned_data["display_name"]
        profile.save()
        user.is_active = form.cleaned_data["is_active"]
        user.save(update_fields=["is_active"])
        messages.success(request, "Ο λογαριασμός ενημερώθηκε.")
        return redirect("user_access_list")
    return render(request, "form.html", {"form": form, "title": f"Ρυθμίσεις χρήστη — {user.username}"})


@login_required
def backup_status(request):
    configured = all([
        os.environ.get("BACKUP_S3_ENDPOINT_URL"),
        os.environ.get("BACKUP_S3_ACCESS_KEY_ID"),
        os.environ.get("BACKUP_S3_SECRET_ACCESS_KEY"),
        os.environ.get("BACKUP_S3_BUCKET"),
    ])
    return render(
        request,
        "backup/status.html",
        {
            "configured": configured,
            "last_run": BackupRun.objects.first(),
            "runs": BackupRun.objects.all()[:20],
        },
    )


@user_passes_test(_superuser)
def cloud_backup_now(request):
    if request.method != "POST":
        return redirect("backup_status")
    from .backup_utils import upload_backup_to_s3
    ok, message = upload_backup_to_s3()
    if ok:
        messages.success(request, message)
    else:
        messages.error(request, message)
    return redirect("backup_status")
