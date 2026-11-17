"""Tests for the base layout, navigation and SEO tags."""

from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.views.generic import TemplateView

from core.seo import SeoMixin, build_title


class BuildTitleTests(SimpleTestCase):
    def test_without_page_title_uses_site_title(self):
        self.assertEqual(build_title(), "VRoboT – Verein Robotik Talente")

    def test_with_page_title_appends_short_name(self):
        self.assertEqual(build_title("Agenda"), "Agenda – VRoboT")


class SeoMixinTests(SimpleTestCase):
    def test_puts_title_and_description_into_context(self):
        class View(SeoMixin, TemplateView):
            template_name = "base.html"
            page_title = "Agenda"
            meta_description = "Nächste Termine"

        view = View()
        view.setup(RequestFactory().get("/"))
        context = view.get_context_data()

        self.assertEqual(context["page_title"], "Agenda")
        self.assertEqual(context["meta_description"], "Nächste Termine")


class HomePageTests(TestCase):
    def setUp(self):
        self.response = self.client.get(reverse("core:home"))

    def test_renders(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, "core/home.html")

    def test_title_and_meta_description(self):
        self.assertContains(
            self.response, "<title>VRoboT – Verein Robotik Talente</title>", html=True
        )
        self.assertContains(
            self.response, '<meta name="description" content="Der Verein'
        )
        self.assertContains(self.response, 'property="og:title"')

    def test_language_is_swiss_german(self):
        self.assertContains(self.response, '<html lang="de-ch">')

    def test_navigation_marks_current_page(self):
        self.assertContains(
            self.response, f'<a href="{reverse("core:home")}" aria-current="page">'
        )

    @override_settings(GEARSBOT_URL="https://gearsbot.example/")
    def test_links_to_gearsbot(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, 'href="https://gearsbot.example/"', count=2)


class ErrorPageTests(TestCase):
    @override_settings(DEBUG=False)
    def test_404_page_is_german(self):
        response = self.client.get("/gibt-es-nicht/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Seite nicht gefunden", status_code=404)
        self.assertContains(
            response, "<title>Seite nicht gefunden – VRoboT</title>", status_code=404
        )
