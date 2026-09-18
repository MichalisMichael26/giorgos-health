from django.http import HttpResponseForbidden


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def user_role(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return "parent"
    try:
        return user.access_profile.role
    except Exception:
        return "parent"


class ReadOnlyDoctorMiddleware:
    """Blocks modifying requests for accounts explicitly configured as doctor/read-only."""

    ALLOWED_POST_PATHS = {
        "/logout/",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and user_role(request.user) == "doctor_readonly"
            and request.method not in SAFE_METHODS
            and request.path not in self.ALLOWED_POST_PATHS
        ):
            return HttpResponseForbidden(
                "Ο λογαριασμός ιατρού είναι μόνο για προβολή και δεν μπορεί να αλλάξει δεδομένα."
            )
        return self.get_response(request)
