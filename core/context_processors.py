from .access import is_readonly_doctor


def access_context(request):
    return {
        "is_readonly_doctor": is_readonly_doctor(getattr(request, "user", None)),
    }
