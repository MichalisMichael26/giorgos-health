from django.core.management.base import BaseCommand

from core.push_utils import dispatch_due_reminders


class Command(BaseCommand):
    help = "Send due Giorgos Health mobile push reminders."

    def handle(self, *args, **options):
        result = dispatch_due_reminders()
        self.stdout.write(
            self.style.SUCCESS(
                "Push dispatch complete: "
                f"initial {result['initial_successes']}/{result['initial_attempts']}, "
                f"repeat {result['repeat_successes']}/{result['repeat_attempts']}."
            )
        )
