"""Import a one-time batch of glucose readings from a private Render environment variable.

No patient measurements are stored in source control. Running this more than once
is idempotent for readings with the same value near the supplied time.
"""
import json
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import GlucoseReading


class Command(BaseCommand):
    help = "Import handwritten glucose observations supplied through private environment."

    def handle(self, *args, **options):
        raw = os.getenv("GIORGOS_GLUCOSE_IMPORT_JSON", "").strip()
        if not raw:
            self.stdout.write("No private glucose import batch provided.")
            return

        try:
            readings = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CommandError("Invalid glucose import JSON.") from exc
        if not isinstance(readings, list) or not (1 <= len(readings) <= 120):
            raise CommandError("Glucose import requires 1 to 120 entries.")

        validated = []
        for index, item in enumerate(readings, start=1):
            if not isinstance(item, dict):
                raise CommandError(f"Row {index}: expected an object.")
            try:
                reading_date = datetime.strptime(item["date"], "%Y-%m-%d").date()
                reading_time = datetime.strptime(item["time"], "%H:%M").time()
                value = Decimal(str(item["value"]))
            except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
                raise CommandError(f"Row {index}: invalid date, time or value.") from exc
            if not value.is_finite() or not (1 <= value <= 1000):
                raise CommandError(f"Row {index}: glucose out of accepted input range.")
            validated.append((reading_date, reading_time, value))

        # Validate the complete batch before making any persistent changes.
        added, existing = 0, 0
        with transaction.atomic():
            for reading_date, reading_time, value in validated:
                minutes = reading_time.hour * 60 + reading_time.minute
                prior_times = GlucoseReading.objects.filter(
                    date=reading_date, value=value
                ).values_list("time", flat=True)
                duplicate = any(
                    abs((t.hour * 60 + t.minute) - minutes) <= 20
                    for t in prior_times
                )
                if duplicate:
                    existing += 1
                    continue
                GlucoseReading.objects.create(
                    date=reading_date,
                    time=reading_time,
                    value=value,
                    context="other",
                    notes=(
                        "Χειρόγραφη μέτρηση από φύλλο καταγραφής γλυκόζης "
                        "ΟΚΥπΥ (28–30/10/2026). "
                        "Η σχέση με τη σίτιση δεν αναγράφεται."
                    ),
                )
                added += 1
        self.stdout.write(
            self.style.SUCCESS(f"Glucose batch complete: added={added}, matched_existing={existing}.")
        )
