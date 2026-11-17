"""Tests for the one-time import of the old site (import_old_site)."""

import shutil
import tempfile
from io import BytesIO, StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from core.management.commands import import_old_site
from documents.models import Document
from pages.models import Page
from posts.models import Post

FAKE_PDF = b"%PDF-1.4 fake"


def fake_jpeg(width=4032, height=1833):
    out = BytesIO()
    Image.new("RGB", (width, height), "blue").save(out, "JPEG")
    return out.getvalue()


def fake_download(url):
    return fake_jpeg() if url.endswith(".jpg") else FAKE_PDF


class ImportOldSiteTests(TestCase):
    def setUp(self):
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media)
        settings_override = override_settings(MEDIA_ROOT=media)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        patcher = mock.patch.object(
            import_old_site, "download", side_effect=fake_download
        )
        self.download = patcher.start()
        self.addCleanup(patcher.stop)

    def run_import(self, *args):
        out = StringIO()
        call_command("import_old_site", *args, stdout=out)
        return out.getvalue()

    def test_imports_pages_post_and_documents(self):
        self.run_import()

        about = Page.objects.get(slug="ueber-uns")
        self.assertIn("Unsere Regeln", about.body)
        self.assertNotIn("Platzhalter", about.body)
        self.assertIn("Heraklit", Page.objects.get(slug="mitmachen").body)

        post = Post.objects.get(slug="die-welt-braucht-arduino")
        self.assertTrue(post.is_visible())
        self.assertEqual(post.published_at.year, 2020)
        self.assertTrue(post.image_alt)
        with Image.open(post.image) as image:
            # Scaled down from the 4032 px original.
            self.assertEqual(image.width, import_old_site.POST_IMAGE_MAX_WIDTH)

        self.assertEqual(Document.objects.count(), len(import_old_site.DOCUMENTS))
        statuten = Document.objects.get(title="Statuten")
        self.assertEqual(statuten.category.slug, "statuten")
        self.assertEqual(statuten.file.read(), FAKE_PDF)
        self.download.assert_any_call(
            "https://vrobot.ch/attachments/Statuten_VRoboT.pdf"
        )

    def test_running_twice_creates_nothing_new(self):
        self.run_import()
        output = self.run_import()
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Document.objects.count(), len(import_old_site.DOCUMENTS))
        self.assertNotIn("importiert", output)

    def test_does_not_overwrite_edited_pages(self):
        Page.objects.filter(slug="kontakt").update(body="Schon bearbeitet.")
        self.run_import()
        self.assertEqual(Page.objects.get(slug="kontakt").body, "Schon bearbeitet.")

    def test_force_overwrites_edited_pages(self):
        Page.objects.filter(slug="kontakt").update(body="Schon bearbeitet.")
        self.run_import("--force")
        self.assertIn("Marc Thoma", Page.objects.get(slug="kontakt").body)

    def test_dry_run_saves_nothing(self):
        self.run_import("--dry-run")
        self.assertFalse(Post.objects.exists())
        self.assertFalse(Document.objects.exists())
        self.assertIn("Platzhalter", Page.objects.get(slug="ueber-uns").body)
        self.download.assert_not_called()
