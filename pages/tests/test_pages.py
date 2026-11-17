"""Tests for the fixed pages."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pages.models import Page


class InitialPagesTests(TestCase):
    def test_fixed_pages_exist(self):
        self.assertEqual(
            set(Page.objects.values_list("slug", flat=True)),
            {"ueber-uns", "mitmachen", "kontakt"},
        )

    def test_every_page_has_a_url(self):
        for page in Page.objects.all():
            with self.subTest(page=page.slug):
                self.assertEqual(
                    self.client.get(page.get_absolute_url()).status_code, 200
                )


class PageViewTests(TestCase):
    def test_renders_markdown_title_and_description(self):
        Page.objects.filter(slug="ueber-uns").update(
            title="Über uns",
            body="## Vorstand\n\nWir sind **motiviert**.",
            meta_description="Alles über den Verein",
        )
        response = self.client.get(reverse("pages:about"))
        self.assertContains(response, "<h2>Vorstand</h2>", html=True)
        self.assertContains(response, "<strong>motiviert</strong>", html=True)
        self.assertContains(response, "<title>Über uns – VRoboT</title>", html=True)
        self.assertContains(
            response, '<meta name="description" content="Alles über den Verein">'
        )

    def test_urls_are_german(self):
        self.assertEqual(reverse("pages:about"), "/ueber-uns/")
        self.assertEqual(reverse("pages:join"), "/mitmachen/")
        self.assertEqual(reverse("pages:contact"), "/kontakt/")

    def test_missing_page_returns_404(self):
        Page.objects.filter(slug="mitmachen").delete()
        self.assertEqual(self.client.get(reverse("pages:join")).status_code, 404)

    def test_navigation_and_footer_link_contact(self):
        response = self.client.get(reverse("pages:contact"))
        self.assertContains(
            response, '<a href="/kontakt/" aria-current="page">Kontakt</a>', html=True
        )
        self.assertContains(response, 'href="/kontakt/"', count=2)


class PageAdminTests(TestCase):
    def setUp(self):
        self.client.force_login(
            get_user_model().objects.create_superuser("admin", "a@example.com", "pw")
        )

    def test_pages_can_be_edited(self):
        page = Page.objects.get(slug="mitmachen")
        response = self.client.get(reverse("admin:pages_page_change", args=[page.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="markdown-editor"')
        # Slug is not editable.
        self.assertNotContains(response, 'name="slug"')

    def test_pages_cannot_be_added_or_deleted(self):
        page = Page.objects.get(slug="mitmachen")
        self.assertEqual(
            self.client.get(reverse("admin:pages_page_add")).status_code, 403
        )
        self.assertEqual(
            self.client.get(
                reverse("admin:pages_page_delete", args=[page.pk])
            ).status_code,
            403,
        )
