"""Tests for the base layout, navigation and SEO tags."""

import re

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

    def test_logo_links_home_and_marks_current_page(self):
        # The home page has no navigation entry; the logo link is "current".
        self.assertContains(
            self.response,
            f'<a class="brand" href="{reverse("core:home")}" aria-current="page">',
        )

    def test_has_favicon_and_default_og_image(self):
        self.assertContains(self.response, "core/img/favicon.ico")
        self.assertContains(
            self.response,
            'property="og:image" content="http://testserver/static/core/img/logo-full-960.png"',
        )

    def test_loads_shared_prose_styles(self):
        # prose.css is shared with the admin editor preview.
        self.assertContains(self.response, "core/css/prose.css")

    def test_footer_lists_navigation(self):
        footer = self.response.content.decode().split('class="site-footer"')[1]
        for url_name in [
            "posts:list",
            "events:list",
            "documents:list",
            "pages:contact",
        ]:
            self.assertIn(f'href="{reverse(url_name)}"', footer)

    @override_settings(GEARSBOT_URL="https://gearsbot.example/")
    def test_links_to_gearsbot(self):
        response = self.client.get(reverse("core:home"))
        # Navigation, teaser and footer.
        self.assertContains(response, 'href="https://gearsbot.example/"', count=3)

    @override_settings(ROBOCHALLENGE_URL="https://robochallenge.example/")
    def test_links_to_robochallenge(self):
        response = self.client.get(reverse("core:home"))
        # Navigation, home page teaser and footer.
        self.assertContains(response, 'href="https://robochallenge.example/"', count=3)
        other_page = self.client.get(reverse("pages:about"))
        # Navigation and footer on every page.
        self.assertContains(
            other_page, 'href="https://robochallenge.example/"', count=2
        )

    @override_settings(CHECKERMINT_URL="https://checkermint.example/")
    def test_links_to_checkermint(self):
        for url_name in ["core:home", "pages:about"]:
            with self.subTest(url_name):
                response = self.client.get(reverse(url_name))
                # Navigation and footer, both open in a new tab with a hint
                # for screen readers.
                links = re.findall(
                    r'<a [^>]*href="https://checkermint\.example/"[^>]*>(.*?)</a>',
                    response.content.decode(),
                )
                self.assertEqual(len(links), 2)
                for link in links:
                    self.assertIn("Checkermint", link)
                    self.assertIn(
                        '<span class="visually-hidden"> (öffnet in neuem Tab)</span>',
                        link,
                    )
                self.assertContains(
                    response,
                    'href="https://checkermint.example/" rel="noopener" '
                    'target="_blank"',
                    count=2,
                )

    def test_checkermint_url_default(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, 'href="https://checkermint.ch/"', count=2)


class ErrorPageTests(TestCase):
    @override_settings(DEBUG=False)
    def test_404_page_is_german(self):
        response = self.client.get("/gibt-es-nicht/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Seite nicht gefunden", status_code=404)
        self.assertContains(
            response, "<title>Seite nicht gefunden – VRoboT</title>", status_code=404
        )
