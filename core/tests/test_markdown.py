"""Tests for Markdown rendering and sanitising (ADR 0009)."""

from django.test import SimpleTestCase

from core.markdown import markdown_to_plain_text, render_markdown


class RenderMarkdownTests(SimpleTestCase):
    def test_basic_formatting(self):
        html = render_markdown("**fett** und *kursiv*\n\n- eins\n- zwei")
        self.assertInHTML("<strong>fett</strong>", html)
        self.assertInHTML("<em>kursiv</em>", html)
        self.assertInHTML("<ul><li>eins</li><li>zwei</li></ul>", html)

    def test_links_get_rel_noopener(self):
        html = render_markdown("[VRoboT](https://vrobot.ch)")
        self.assertIn('href="https://vrobot.ch"', html)
        self.assertIn('rel="noopener noreferrer"', html)

    def test_top_level_heading_becomes_h2(self):
        html = render_markdown("# Titel\n\n## Abschnitt")
        self.assertNotIn("<h1>", html)
        self.assertInHTML("<h2>Titel</h2>", html)
        self.assertInHTML("<h2>Abschnitt</h2>", html)

    def test_script_tags_are_removed(self):
        html = render_markdown("Hallo <script>alert('x')</script>")
        self.assertNotIn("<script", html)
        self.assertNotIn("alert", html)

    def test_dangerous_attributes_and_urls_are_removed(self):
        html = render_markdown(
            '<a href="javascript:alert(1)" onclick="x()">klick</a> '
            '<img src="x" onerror="alert(1)">'
        )
        self.assertNotIn("javascript:", html)
        self.assertNotIn("onclick", html)
        self.assertNotIn("<img", html)

    def test_empty_input(self):
        self.assertEqual(render_markdown(""), "")
        self.assertEqual(render_markdown(None), "")


class PlainTextTests(SimpleTestCase):
    def test_strips_formatting(self):
        self.assertEqual(
            markdown_to_plain_text("## Titel\n\n**Fett** und [Link](https://x.ch)"),
            "Titel Fett und Link",
        )

    def test_truncates(self):
        result = markdown_to_plain_text("Wort " * 100, max_chars=20)
        self.assertLessEqual(len(result), 20)
        self.assertTrue(result.endswith("…"))
