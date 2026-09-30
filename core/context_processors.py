from .access import is_readonly_doctor


def access_context(request):
    is_doctor = is_readonly_doctor(getattr(request, "user", None))
    remaining = getattr(
        request,
        "doctor_session_remaining_seconds",
        None,
    )

    return {
        "is_readonly_doctor": is_doctor,
        "doctor_session_remaining_seconds": remaining,
    }
