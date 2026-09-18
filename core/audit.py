from threading import local

_state = local()


def get_current_user():
    return getattr(_state, "user", None)


class AuditUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _state.user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        try:
            return self.get_response(request)
        finally:
            _state.user = None
