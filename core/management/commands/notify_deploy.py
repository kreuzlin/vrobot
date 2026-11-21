"""Mail a deploy notification (failed deploy, rollback) to the maintainer.

Called by scripts/deploy.sh on the server; uses the regular email settings
(Hostpoint SMTP, ADR 0010). Recipients: DEPLOY_ALERT_RECIPIENTS in `.env`.

Usage: printf 'body' | python manage.py notify_deploy "Subject"
"""

import sys

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError

SUBJECT_PREFIX = "[vrobot.ch] "


class Command(BaseCommand):
    help = "Mail a deploy notification to DEPLOY_ALERT_RECIPIENTS (body on stdin)."

    def add_arguments(self, parser):
        parser.add_argument("subject")

    def handle(self, subject, **options):
        recipients = settings.DEPLOY_ALERT_RECIPIENTS
        if not recipients:
            raise CommandError("DEPLOY_ALERT_RECIPIENTS is empty, no mail sent.")
        body = sys.stdin.read()
        send_mail(SUBJECT_PREFIX + subject, body, None, recipients)
        self.stdout.write(f"Sent to {len(recipients)} recipient(s).")
