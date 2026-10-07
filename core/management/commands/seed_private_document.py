import base64
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from core.models import MedicalDocument


class Command(BaseCommand):
    help = "Seed one private medical document from Render environment variables."

    def handle(self, *args, **options):
        chunk_keys = sorted(
            key for key in os.environ
            if key.startswith("PRIVATE_MEDICAL_DOCUMENT_B64_")
        )
        chunks = [os.environ.get(key, "") for key in chunk_keys]
        payload = "".join(chunks).strip()

        if not payload:
            self.stdout.write("No private medical document payload configured; skipping.")
            return

        title = (os.environ.get("PRIVATE_MEDICAL_DOCUMENT_TITLE") or "Private medical document").strip()
        raw_date = (os.environ.get("PRIVATE_MEDICAL_DOCUMENT_DATE") or "").strip()
        category = (os.environ.get("PRIVATE_MEDICAL_DOCUMENT_CATEGORY") or "other").strip()
        filename = (os.environ.get("PRIVATE_MEDICAL_DOCUMENT_FILENAME") or "document.pdf").strip()
        content_type = (os.environ.get("PRIVATE_MEDICAL_DOCUMENT_CONTENT_TYPE") or "application/pdf").strip()
        notes = (os.environ.get("PRIVATE_MEDICAL_DOCUMENT_NOTES") or "").strip()

        try:
            document_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            self.stderr.write("PRIVATE_MEDICAL_DOCUMENT_DATE must use YYYY-MM-DD; skipping.")
            return

        try:
            data = base64.b64decode(payload, validate=True)
        except Exception as exc:
            self.stderr.write(f"Invalid base64 private medical document payload: {exc}")
            return

        item = (
            MedicalDocument.objects.filter(
                title=title,
                date=document_date,
                original_filename=filename,
            )
            .order_by("pk")
            .first()
        )

        values = {
            "category": category,
            "content_type": content_type,
            "file_size": len(data),
            "data": data,
            "notes": notes,
        }

        if item is None:
            item = MedicalDocument.objects.create(
                title=title,
                date=document_date,
                original_filename=filename,
                **values,
            )
            action = "created"
        else:
            for field, value in values.items():
                setattr(item, field, value)
            item.save(update_fields=list(values.keys()) + ["updated_at"])
            action = "updated"

        self.stdout.write(
            self.style.SUCCESS(
                f"Private medical document {action}: id={item.pk}, bytes={len(data)}"
            )
        )
