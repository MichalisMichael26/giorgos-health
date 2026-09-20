import logging
import os
import threading
import time

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "giorgos_health.settings")
application = get_wsgi_application()

logger = logging.getLogger("giorgos_health.push_scheduler")
_scheduler_started = False


def _push_scheduler_loop():
    from django.db import close_old_connections
    from core.push_utils import dispatch_due_reminders

    try:
        interval = int(os.environ.get("PUSH_SCHEDULER_INTERVAL_SECONDS", "30"))
    except ValueError:
        interval = 60

    interval = max(interval, 30)

    # Small startup delay gives migrations/deploy startup a moment to settle.
    time.sleep(8)

    while True:
        try:
            close_old_connections()
            result = dispatch_due_reminders()
            if result.get("initial_successes") or result.get("repeat_successes"):
                logger.info("Push scheduler delivered reminders: %s", result)
        except Exception:
            logger.exception("Push scheduler cycle failed")
        finally:
            close_old_connections()

        time.sleep(interval)


def _start_push_scheduler():
    global _scheduler_started

    enabled = os.environ.get("ENABLE_PUSH_SCHEDULER", "true").lower() in {
        "1", "true", "yes", "on"
    }
    debug = os.environ.get("DEBUG", "False").lower() == "true"

    if _scheduler_started or not enabled or debug:
        return

    _scheduler_started = True
    threading.Thread(
        target=_push_scheduler_loop,
        name="giorgos-health-push-scheduler",
        daemon=True,
    ).start()


_start_push_scheduler()
