from django.core.management.base import BaseCommand, CommandError
from core.backup_utils import upload_backup_to_s3


class Command(BaseCommand):
    help = "Create and upload a Giorgos Health backup to configured S3/R2 storage."

    def handle(self, *args, **options):
        ok, message = upload_backup_to_s3()
        if not ok:
            raise CommandError(message)
        self.stdout.write(self.style.SUCCESS(message))
