"""Tests for the redirects from the old site's URLs (core/legacy.py)."""

import shutil
import tempfile

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from documents.models import Document, DocumentCategory
from posts.models import Post


class OldPageRedirectTests(TestCase):
    def test_old_pages_redirect_permanently(self):
        for old, url_name in [
            ("/index.php", "core:home"),
            ("/about.php", "pages:about"),
            ("/engage.php", "pages:join"),
            ("/agenda.php", "events:list"),
            ("/contact.php", "pages:contact"),
        ]:
            with self.subTest(old=old):
                response = self.client.get(old)
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response["Location"], reverse(url_name))


class OldPostRedirectTests(TestCase):
    def test_known_post_id_redirects_to_post(self):
        post = Post.objects.create(
            title="Die Welt braucht Arduino",
            slug="die-welt-braucht-arduino",
            body="Text",
            author="Linard",
            is_published=True,
        )
        response = self.client.get("/post.php?ID=1")
        self.assertRedirects(response, post.get_absolute_url(), status_code=301)

    def test_unknown_or_missing_post_redirects_to_post_list(self):
        for url in ["/post.php?ID=99", "/post.php", "/post.php?ID=1"]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response["Location"], reverse("posts:list"))


class OldAttachmentRedirectTests(TestCase):
    def setUp(self):
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media)
        override = override_settings(MEDIA_ROOT=media)
        override.enable()
        self.addCleanup(override.disable)

    def test_attachment_redirects_to_document_file(self):
        document = Document(
            title="Statuten",
            category=DocumentCategory.objects.get(slug="statuten"),
            year=2022,
        )
        document.file.save("Statuten_VRoboT.pdf", ContentFile(b"%PDF"), save=True)
        response = self.client.get("/attachments/Statuten_VRoboT.pdf")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], document.file.url)

    def test_unknown_attachment_redirects_to_documents(self):
        response = self.client.get("/attachments/EZS_VRoboT.jpg")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], reverse("documents:list"))


class OldGearsBotRedirectTests(TestCase):
    @override_settings(GEARSBOT_URL="https://gearsbot.example/")
    def test_gearsbot_copy_redirects_to_official_instance(self):
        for url in ["/python/public/", "/python/public/index.html"]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response["Location"], "https://gearsbot.example/")
