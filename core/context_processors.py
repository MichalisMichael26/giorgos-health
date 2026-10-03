from .access import is_owner_user, is_readonly_doctor


def access_context(request):
    is_doctor = is_readonly_doctor(getattr(request, "user", None))
    remaining = getattr(
        request,
        "doctor_session_remaining_seconds",
        None,
    )

    user = getattr(request, "user", None)
    can_print_export = is_owner_user(user)

    return {
        "is_readonly_doctor": is_doctor,
        "doctor_session_remaining_seconds": remaining,
        "can_print_export": can_print_export,
        "privacy_restricted": bool(user and user.is_authenticated and not can_print_export),
    }
