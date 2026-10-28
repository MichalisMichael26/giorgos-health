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
    next_retention_run = 0.0

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

        # Prune access records daily without adding another paid cron service.
        # This never touches clinical records or the general audit table.
        if time.monotonic() >= next_retention_run:
            try:
                close_old_connections()
                from core.log_retention import prune_expired_doctor_access_logs

                summary = prune_expired_doctor_access_logs()
                logger.info("Doctor access retention: %s", summary)
                next_retention_run = time.monotonic() + 24 * 60 * 60
            except Exception:
                logger.exception("Doctor access retention failed")
                next_retention_run = time.monotonic() + 60 * 60
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
