"""Tests for posts."""

import io
import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from posts.models import Post

TEMP_MEDIA = tempfile.mkdtemp()


def make_image(name="bild.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (32, 18), "blue").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def make_post(slug="beitrag", **kwargs):
    defaults = {
        "title": "Ein Beitrag",
        "slug": slug,
        "body": "Text des Beitrags.",
        "author": "Erika Muster",
        "is_published": True,
        "published_at": timezone.now() - timedelta(hours=1),
    }
    defaults.update(kwargs)
    return Post.objects.create(**defaults)


class PublishedTests(TestCase):
    def test_only_published_posts_up_to_now(self):
        now = timezone.now()
        make_post("sichtbar", published_at=now - timedelta(days=1))
        make_post("entwurf", is_published=False)
        make_post("geplant", published_at=now + timedelta(days=1))
        self.assertEqual(
            [p.slug for p in Post.objects.published(now=now)], ["sichtbar"]
        )

    def test_newest_first(self):
        now = timezone.now()
        make_post("alt", published_at=now - timedelta(days=5))
        make_post("neu", published_at=now - timedelta(days=1))
        self.assertEqual(
            [p.slug for p in Post.objects.published(now=now)], ["neu", "alt"]
        )

    def test_is_visible_matches_queryset(self):
        now = timezone.now()
        posts = [
            make_post("a", published_at=now - timedelta(days=1)),
            make_post("b", is_published=False),
            make_post("c", published_at=now + timedelta(days=1)),
        ]
        published = set(Post.objects.published(now=now))
        for post in posts:
            with self.subTest(post=post.slug):
                self.assertEqual(post.is_visible(now=now), post in published)


class MetaDescriptionTests(TestCase):
    def test_uses_explicit_description(self):
        post = make_post(meta_description="Eigene Beschreibung")
        self.assertEqual(post.get_meta_description(), "Eigene Beschreibung")

    def test_falls_back_to_plain_text_of_body(self):
        post = make_post(body="## Rückblick\n\nUnser **Team** war dabei.")
        self.assertEqual(post.get_meta_description(), "Rückblick Unser Team war dabei.")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ImageTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def test_image_requires_alt_text(self):
        post = Post(
            title="Mit Bild",
            slug="mit-bild",
            body="Text",
            author="A",
            image=make_image(),
        )
        with self.assertRaises(ValidationError) as ctx:
            post.full_clean()
        self.assertIn("image_alt", ctx.exception.message_dict)

    def test_detail_shows_image_and_og_image(self):
        post = make_post(image=make_image(), image_alt="Roboter auf dem Tisch")
        response = self.client.get(post.get_absolute_url())
        self.assertContains(response, 'alt="Roboter auf dem Tisch"')
        self.assertContains(response, 'property="og:image" content="http://testserver/')


class ViewTests(TestCase):
    def test_list_shows_published_posts_only(self):
        make_post("sichtbar", title="Sichtbarer Beitrag")
        make_post("entwurf", title="Geheimer Entwurf", is_published=False)
        response = self.client.get(reverse("posts:list"))
        self.assertContains(response, "Sichtbarer Beitrag")
        self.assertNotContains(response, "Geheimer Entwurf")
        self.assertContains(response, "<title>Beiträge – VRoboT</title>", html=True)

    def test_list_is_paginated(self):
        for i in range(12):
            make_post(f"b{i}", title=f"Beitrag {i}")
        response = self.client.get(reverse("posts:list"))
        self.assertEqual(len(response.context["posts"]), 10)
        self.assertContains(response, "Seite 1 von 2")

    def test_detail_renders_markdown_and_seo(self):
        post = make_post(
            title="Wettbewerb in Bern",
            body="Wir haben **gewonnen**!",
            meta_description="Bericht vom Wettbewerb",
        )
        response = self.client.get(post.get_absolute_url())
        self.assertContains(response, "<strong>gewonnen</strong>", html=True)
        self.assertContains(
            response, "<title>Wettbewerb in Bern – VRoboT</title>", html=True
        )
        self.assertContains(
            response, '<meta name="description" content="Bericht vom Wettbewerb">'
        )
        self.assertContains(response, "Erika Muster")

    def test_draft_and_scheduled_posts_return_404(self):
        draft = make_post("entwurf", is_published=False)
        scheduled = make_post(
            "geplant", published_at=timezone.now() + timedelta(days=1)
        )
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(scheduled.get_absolute_url()).status_code, 404)

    def test_home_shows_latest_three_posts(self):
        now = timezone.now()
        for i in range(4):
            make_post(
                f"b{i}", title=f"Beitrag {i}", published_at=now - timedelta(days=i + 1)
            )
        response = self.client.get(reverse("core:home"))
        for i in range(3):
            self.assertContains(response, f"Beitrag {i}")
        self.assertNotContains(response, "Beitrag 3")


class AdminTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_superuser(
            "redaktion", "r@example.com", "pw", first_name="Erika", last_name="Muster"
        )
        self.client.force_login(user)

    def test_add_form_uses_markdown_editor_and_prefills_author(self):
        response = self.client.get(reverse("admin:posts_post_add"))
        self.assertContains(response, 'class="markdown-editor"')
        self.assertContains(response, "core/vendor/easymde/easymde.min.js")
        self.assertContains(response, 'value="Erika Muster"')

    def test_image_input_is_linked_to_alt_text_field(self):
        response = self.client.get(reverse("admin:posts_post_add"))
        self.assertContains(response, 'data-alt-field="id_image_alt"')
        self.assertContains(response, "core/js/image-alt-required.js")
