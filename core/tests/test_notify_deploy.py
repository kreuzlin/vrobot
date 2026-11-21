import io
from unittest import mock

from django.core import mail
from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, override_settings


@override_settings(DEFAULT_FROM_EMAIL="VRoboT <mail@example.com>")
class NotifyDeployTests(SimpleTestCase):
    def run_command(self, subject, body):
        with mock.patch("sys.stdin", io.StringIO(body)):
            call_command("notify_deploy", subject, stdout=io.StringIO())

    @override_settings(DEPLOY_ALERT_RECIPIENTS=["admin@example.com"])
    def test_sends_subject_and_body(self):
        self.run_command("Deploy fehlgeschlagen", "Rollback auf abc123.\n")
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "[vrobot.ch] Deploy fehlgeschlagen")
        self.assertEqual(message.body, "Rollback auf abc123.\n")
        self.assertEqual(message.to, ["admin@example.com"])
        self.assertEqual(message.from_email, "VRoboT <mail@example.com>")

    @override_settings(DEPLOY_ALERT_RECIPIENTS=[])
    def test_fails_without_recipients(self):
        with self.assertRaises(CommandError):
            self.run_command("Deploy fehlgeschlagen", "x")
        self.assertEqual(mail.outbox, [])
