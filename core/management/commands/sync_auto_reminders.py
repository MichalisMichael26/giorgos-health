from django.core.management.base import BaseCommand

from core.auto_reminders import sync_all_automatic_reminders


class Command(BaseCommand):
    help = "Create/update automatic meal and appointment reminders."

    def handle(self, *args, **options):
        result = sync_all_automatic_reminders()
        self.stdout.write(
            self.style.SUCCESS(
                "Automatic reminders synchronized: "
                f"{result['meal_schedule']} meal schedule rows, "
                f"{result['appointments']} appointments."
            )
        )
