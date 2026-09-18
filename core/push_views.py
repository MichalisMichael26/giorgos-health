import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .access import is_readonly_doctor
from .models import PushSubscription
from .push_utils import get_or_create_push_config, send_test_push


def service_worker(request):
    javascript = render_to_string("service-worker.js")
    response = HttpResponse(javascript, content_type="application/javascript")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Service-Worker-Allowed"] = "/"
    return response


@login_required
def push_public_config(request):
    if is_readonly_doctor(request.user):
        return JsonResponse({"enabled": False, "publicKey": ""})

    config = get_or_create_push_config()
    return JsonResponse(
        {
            "enabled": True,
            "publicKey": config.public_key_b64,
            "activeDevices": PushSubscription.objects.filter(
                user=request.user,
                active=True,
            ).count(),
        }
    )


@login_required
@require_POST
def push_subscribe(request):
    if is_readonly_doctor(request.user):
        return JsonResponse({"ok": False, "error": "read_only"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        endpoint = payload["endpoint"]
        keys = payload["keys"]
        p256dh = keys["p256dh"]
        auth = keys["auth"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "invalid_subscription"}, status=400)

    subscription, _ = PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "user": request.user,
            "p256dh": p256dh,
            "auth": auth,
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:2000],
            "active": True,
        },
    )

    return JsonResponse(
        {
            "ok": True,
            "subscriptionId": subscription.pk,
            "activeDevices": PushSubscription.objects.filter(
                user=request.user,
                active=True,
            ).count(),
        }
    )


@login_required
@require_POST
def push_unsubscribe(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        endpoint = payload.get("endpoint", "")
    except (ValueError, json.JSONDecodeError):
        endpoint = ""

    if endpoint:
        PushSubscription.objects.filter(
            user=request.user,
            endpoint=endpoint,
        ).update(active=False)

    return JsonResponse(
        {
            "ok": True,
            "activeDevices": PushSubscription.objects.filter(
                user=request.user,
                active=True,
            ).count(),
        }
    )


@login_required
@require_POST
def push_test(request):
    if is_readonly_doctor(request.user):
        return JsonResponse({"ok": False, "error": "read_only"}, status=403)

    successes, failures = send_test_push(request.user)

    if successes:
        return JsonResponse(
            {
                "ok": True,
                "successes": successes,
                "failures": failures,
                "message": "Η δοκιμαστική ειδοποίηση στάλθηκε.",
            }
        )

    return JsonResponse(
        {
            "ok": False,
            "successes": 0,
            "failures": failures,
            "message": "Δεν υπάρχει ενεργή συσκευή ή η αποστολή απέτυχε.",
        },
        status=400,
    )
