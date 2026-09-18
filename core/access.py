import os

from django.http import HttpResponseForbidden
from django.shortcuts import redirect


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# GET pages that are themselves mutation forms/actions.
UNSAFE_VIEW_NAMES = {
    "meal_create",
    "meal_edit",
    "meal_delete",
    "glucose_create",
    "glucose_edit",
    "glucose_delete",
    "growth_create",
    "growth_edit",
    "growth_delete",
    "medication_create",
    "medication_edit",
    "medication_delete",
    "appointment_create",
    "appointment_edit",
    "appointment_delete",
    "child_profile_edit",
    "document_create",
    "document_edit",
    "document_delete",
    "vaccine_create",
    "vaccine_edit",
    "vaccine_delete",
    "symptom_create",
    "symptom_edit",
    "symptom_delete",
    "diaper_create",
    "diaper_edit",
    "diaper_delete",
    "emergency_edit",
    "safety_rule_create",
    "safety_rule_edit",
    "safety_rule_delete",
    "product_record_create",
    "product_record_edit",
    "product_record_delete",
    "lab_create",
    "lab_edit",
    "lab_delete",
    "reminder_create",
    "reminder_edit",
    "reminder_done",
    "reminder_delete",
    "doctor_question_create",
    "doctor_question_answer",
    "doctor_question_delete",
    "emergency_share_settings",
    "emergency_share_rotate",
    "user_access_create",
    "user_access_edit",
    "cloud_backup_now",
}


def configured_doctor_username():
    return (os.environ.get("DJANGO_DOCTOR_USERNAME") or "drsavvas").strip().casefold()


def user_role(user):
    if not user or not user.is_authenticated:
        return None

    if user.is_superuser:
        return "parent"

    # Hard safety fallback: the configured Dr Savvas account is ALWAYS read-only,
    # even if its UserAccessProfile was missing or was accidentally changed.
    if (user.username or "").strip().casefold() == configured_doctor_username():
        return "doctor_readonly"

    try:
        return user.access_profile.role
    except Exception:
        return "parent"


def is_readonly_doctor(user):
    return user_role(user) == "doctor_readonly"


class ReadOnlyDoctorMiddleware:
    """
    Enforces doctor read-only access server-side.

    1. Any modifying HTTP request is rejected, except logout.
    2. GET access to create/edit/delete/action forms is redirected to Doctor View.
    """

    ALLOWED_POST_PATHS = {
        "/logout/",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and is_readonly_doctor(request.user)
            and request.method not in SAFE_METHODS
            and request.path not in self.ALLOWED_POST_PATHS
        ):
            return HttpResponseForbidden(
                "Read-only doctor account: this action cannot modify Giorgos Health data."
            )

        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated or not is_readonly_doctor(request.user):
            return None

        match = getattr(request, "resolver_match", None)
        view_name = match.url_name if match else None

        if request.method in SAFE_METHODS and view_name in UNSAFE_VIEW_NAMES:
            return redirect("doctor_view")

        return None
