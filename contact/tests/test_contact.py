"""Tests for the contact form, spam protection and email forwarding."""

import time
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from contact.forms import MAX_SECONDS, make_token
from contact.models import ContactMessage
from contact.views import SUCCESS_MESSAGE

URL = reverse("pages:contact")


def form_data(**overrides):
    data = {
        "name": "Erika Muster",
        "email": "erika@example.com",
        "message": "Wann ist das nächste Training?",
        "website": "",
        # Form opened one minute ago.
        "token": make_token(time.time() - 60),
    }
    data.update(overrides)
    return data


@override_settings(
    CONTACT_RECIPIENTS=["vorstand@example.org"],
    DEFAULT_FROM_EMAIL="website@example.org",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class ContactFormTests(TestCase):
    def post(self, **overrides):
        return self.client.post(URL, form_data(**overrides), follow=True)

    def test_page_shows_form_and_page_content(self):
        response = self.client.get(URL)
        self.assertContains(response, "<title>Kontakt – VRoboT</title>", html=True)
        self.assertContains(response, 'name="message"')
        self.assertContains(response, 'name="token"')
        self.assertContains(response, 'class="form-field hp-field"')

    def test_valid_message_is_saved_and_emailed(self):
        response = self.post()

        self.assertContains(response, SUCCESS_MESSAGE)
        msg = ContactMessage.objects.get()
        self.assertEqual(msg.email, "erika@example.com")
        self.assertTrue(msg.email_sent)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["vorstand@example.org"])
        self.assertEqual(email.from_email, "website@example.org")
        self.assertEqual(email.reply_to, ["erika@example.com"])
        self.assertIn("Erika Muster", email.subject)
        self.assertIn("Wann ist das nächste Training?", email.body)

    def test_redirects_after_success(self):
        response = self.client.post(URL, form_data())
        self.assertRedirects(response, URL)

    def test_required_fields_and_invalid_email(self):
        response = self.post(name="", email="kein-email", message="")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dieses Feld ist zwingend erforderlich.")
        self.assertContains(response, "gültige E-Mail-Adresse")
        self.assertFalse(ContactMessage.objects.exists())

    def test_form_after_error_gets_fresh_token(self):
        old_token = form_data()["token"]
        response = self.post(name="", token=old_token)
        new_token = response.context["form"]["token"].value()
        self.assertNotEqual(new_token, old_token)

    # Spam protection

    def test_honeypot_discards_silently(self):
        response = self.post(website="https://spam.example")
        self.assertContains(response, SUCCESS_MESSAGE)
        self.assertFalse(ContactMessage.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_too_fast_submission_discards_silently(self):
        response = self.post(token=make_token(time.time()))
        self.assertContains(response, SUCCESS_MESSAGE)
        self.assertFalse(ContactMessage.objects.exists())

    def test_tampered_token_is_rejected(self):
        response = self.post(token="manipuliert")
        self.assertContains(response, "Das Formular ist ungültig.")
        self.assertFalse(ContactMessage.objects.exists())

    def test_missing_token_is_rejected(self):
        data = form_data()
        del data["token"]
        self.client.post(URL, data)
        self.assertFalse(ContactMessage.objects.exists())

    def test_expired_form_is_rejected(self):
        response = self.post(token=make_token(time.time() - MAX_SECONDS - 10))
        self.assertContains(response, "zu lange geöffnet")
        self.assertFalse(ContactMessage.objects.exists())

    # Delivery problems

    def test_email_failure_keeps_message(self):
        with (
            mock.patch(
                "django.core.mail.EmailMessage.send", side_effect=OSError("SMTP down")
            ),
            self.assertLogs("contact.views", level="ERROR"),
        ):
            response = self.post()
        self.assertContains(response, SUCCESS_MESSAGE)
        msg = ContactMessage.objects.get()
        self.assertFalse(msg.email_sent)

    @override_settings(CONTACT_RECIPIENTS=[])
    def test_missing_recipients_keeps_message(self):
        with self.assertLogs("contact.views", level="ERROR"):
            self.post()
        self.assertFalse(ContactMessage.objects.get().email_sent)
        self.assertEqual(len(mail.outbox), 0)


class ContactAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(
            get_user_model().objects.create_superuser("admin", "a@example.com", "pw")
        )
        self.msg = ContactMessage.objects.create(
            name="Max", email="max@example.com", message="Hallo"
        )

    def test_messages_are_read_only(self):
        response = self.client.get(
            reverse("admin:contact_contactmessage_change", args=[self.msg.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hallo")
        self.assertNotContains(response, 'name="message"')
        self.assertEqual(
            self.client.get(reverse("admin:contact_contactmessage_add")).status_code,
            403,
        )


class RetentionTests(TestCase):
    def test_deletes_only_old_messages(self):
        old = ContactMessage.objects.create(name="Alt", email="a@x.ch", message="x")
        ContactMessage.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(days=400)
        )
        ContactMessage.objects.create(name="Neu", email="n@x.ch", message="x")

        out = StringIO()
        call_command("delete_old_contact_messages", "--days", "365", stdout=out)

        self.assertEqual(
            list(ContactMessage.objects.values_list("name", flat=True)), ["Neu"]
        )
        self.assertIn("Deleted 1", out.getvalue())
