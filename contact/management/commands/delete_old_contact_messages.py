from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from contact.models import ContactMessage


class Command(BaseCommand):
    help = (
        "Delete contact messages older than CONTACT_MESSAGE_RETENTION_DAYS "
        "(data protection). Intended to run daily via cron in production."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Override the retention period in days.",
        )

    def handle(self, *args, days=None, **options):
        days = days if days is not None else settings.CONTACT_MESSAGE_RETENTION_DAYS
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = ContactMessage.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(
            f"Deleted {deleted} contact message(s) older than {days} days."
        )
