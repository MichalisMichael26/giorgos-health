import io
import json
import os
import zipfile
from pathlib import Path

import boto3
from django.utils import timezone

from .advanced_views import _model_row, _records_for_export, build_excel_bytes
from .models import BackupRun, DiaperEntry, MedicalDocument, ProductSafetyRecord, SymptomEntry


def build_backup_bytes():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        all_data = {}
        for title, queryset in _records_for_export():
            all_data[title] = [_model_row(item) for item in queryset]

        archive.writestr(
            "data.json",
            json.dumps(all_data, ensure_ascii=False, indent=2, default=str),
        )
        archive.writestr("giorgos-health-all-data.xlsx", build_excel_bytes())
        archive.writestr(
            "README.txt",
            "Giorgos Health backup\nStructured data + uploaded documents/photos.\n",
        )

        for item in MedicalDocument.objects.all():
            if not item.data:
                continue
            safe_name = Path(item.original_filename).name.replace("/", "_").replace("\\", "_")
            archive.writestr(f"documents/{item.pk}-{safe_name}", bytes(item.data))

        for item in ProductSafetyRecord.objects.exclude(label_photo_data__isnull=True):
            if not item.label_photo_data:
                continue
            safe_name = Path(item.label_photo_name or "label.jpg").name.replace("/", "_").replace("\\", "_")
            archive.writestr(f"product-labels/{item.pk}-{safe_name}", bytes(item.label_photo_data))

        for item in SymptomEntry.objects.exclude(photo_data__isnull=True):
            if item.photo_data:
                safe_name = Path(item.photo_name or "symptom.jpg").name.replace("/", "_").replace("\\", "_")
                archive.writestr(f"symptom-photos/{item.pk}-{safe_name}", bytes(item.photo_data))

        for item in DiaperEntry.objects.exclude(photo_data__isnull=True):
            if item.photo_data:
                safe_name = Path(item.photo_name or "diaper.jpg").name.replace("/", "_").replace("\\", "_")
                archive.writestr(f"diaper-photos/{item.pk}-{safe_name}", bytes(item.photo_data))

    return buffer.getvalue()


def _s3_client():
    endpoint = os.environ.get("BACKUP_S3_ENDPOINT_URL")
    access_key = os.environ.get("BACKUP_S3_ACCESS_KEY_ID")
    secret_key = os.environ.get("BACKUP_S3_SECRET_ACCESS_KEY")
    region = os.environ.get("BACKUP_S3_REGION", "auto")
    bucket = os.environ.get("BACKUP_S3_BUCKET")

    if not all([endpoint, access_key, secret_key, bucket]):
        raise RuntimeError(
            "Δεν έχουν ρυθμιστεί τα BACKUP_S3_ENDPOINT_URL, BACKUP_S3_ACCESS_KEY_ID, "
            "BACKUP_S3_SECRET_ACCESS_KEY και BACKUP_S3_BUCKET."
        )

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    return client, bucket


def upload_backup_to_s3():
    try:
        client, bucket = _s3_client()
        payload = build_backup_bytes()
        now = timezone.localtime()
        key = f"giorgos-health/{now:%Y/%m}/giorgos-health-{now:%Y%m%d-%H%M%S}.zip"
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=payload,
            ContentType="application/zip",
        )
        BackupRun.objects.create(
            status="success",
            destination=f"{bucket}/{key}",
            size_bytes=len(payload),
            notes="Cloud backup μέσω S3-compatible storage.",
        )
        return True, f"Το cloud backup ολοκληρώθηκε: {key}"
    except Exception as exc:
        BackupRun.objects.create(
            status="failed",
            destination=os.environ.get("BACKUP_S3_BUCKET", ""),
            notes=str(exc)[:2000],
        )
        return False, f"Το cloud backup απέτυχε: {exc}"
