"""Tests for the admin setup: editor role, password reset, dashboard."""

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from contact.models import ContactMessage
from core.editor_group import EDITOR_GROUP_NAME


def make_editor(username="redaktion"):
    user = get_user_model().objects.create_user(
        username, f"{username}@example.com", "geheim-123", is_staff=True
    )
    user.groups.add(Group.objects.get(name=EDITOR_GROUP_NAME))
    return user


class EditorGroupTests(TestCase):
    def setUp(self):
        self.client.force_login(make_editor())

    def get(self, url_name, *args):
        return self.client.get(reverse(url_name, args=args)).status_code

    def test_can_manage_content(self):
        for url_name in [
            "admin:posts_post_add",
            "admin:events_event_add",
            "admin:documents_document_add",
            "admin:documents_documentcategory_add",
            "admin:pages_page_changelist",
            "admin:contact_contactmessage_changelist",
        ]:
            with self.subTest(url_name=url_name):
                self.assertEqual(self.get(url_name), 200)

    def test_cannot_manage_users_or_groups(self):
        for url_name in [
            "admin:auth_user_changelist",
            "admin:auth_user_add",
            "admin:auth_group_changelist",
        ]:
            with self.subTest(url_name=url_name):
                self.assertEqual(self.get(url_name), 403)

    def test_cannot_add_pages(self):
        self.assertEqual(self.get("admin:pages_page_add"), 403)

    def test_cannot_change_contact_messages(self):
        msg = ContactMessage.objects.create(name="A", email="a@x.ch", message="x")
        user = get_user_model().objects.get(username="redaktion")
        self.assertTrue(user.has_perm("contact.view_contactmessage"))
        self.assertTrue(user.has_perm("contact.delete_contactmessage"))
        self.assertFalse(user.has_perm("contact.change_contactmessage"))
        self.assertEqual(self.get("admin:contact_contactmessage_change", msg.pk), 200)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetTests(TestCase):
    def test_login_page_links_to_password_reset(self):
        response = self.client.get(reverse("admin:login"))
        self.assertContains(response, reverse("admin_password_reset"))

    def test_full_reset_flow(self):
        make_editor("erika")
        response = self.client.post(
            reverse("admin_password_reset"), {"email": "erika@example.com"}
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)

        link = re.search(r"http://testserver(/admin/reset/\S+/)", mail.outbox[0].body)
        self.assertIsNotNone(link)
        # The first request redirects to a URL with the token hidden in the session.
        response = self.client.get(link.group(1), follow=True)
        form_url = response.redirect_chain[-1][0]
        response = self.client.post(
            form_url,
            {
                "new_password1": "Neues-Passwort-2026",
                "new_password2": "Neues-Passwort-2026",
            },
        )
        self.assertRedirects(response, reverse("password_reset_complete"))
        self.assertTrue(
            self.client.login(username="erika", password="Neues-Passwort-2026")
        )


class DashboardTests(TestCase):
    def test_editor_sees_quick_links(self):
        self.client.force_login(make_editor())
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "Schnellzugriff")
        self.assertContains(response, reverse("admin:posts_post_add"))
        self.assertContains(response, reverse("admin:events_event_add"))
        self.assertContains(response, reverse("admin:documents_document_add"))
        self.assertContains(response, "Website ansehen")
        # Django's app list is still there.
        self.assertContains(response, "Beiträge")

    def test_warns_about_unsent_contact_messages(self):
        self.client.force_login(make_editor())
        ContactMessage.objects.create(name="A", email="a@x.ch", message="x")
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "1 Kontaktanfrage konnte nicht per E-Mail")

    def test_no_warning_when_all_sent(self):
        self.client.force_login(make_editor())
        ContactMessage.objects.create(
            name="A", email="a@x.ch", message="x", email_sent=True
        )
        response = self.client.get(reverse("admin:index"))
        self.assertNotContains(response, "nicht per E-Mail weitergeleitet")

    def test_staff_without_permissions_sees_no_quick_links(self):
        user = get_user_model().objects.create_user("ohne", password="x", is_staff=True)
        self.client.force_login(user)
        response = self.client.get(reverse("admin:index"))
        self.assertNotContains(response, reverse("admin:posts_post_add"))
