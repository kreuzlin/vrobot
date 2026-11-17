from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.markdown import markdown_to_plain_text
from core.widgets import MARKDOWN_HELP_TEXT


class PostQuerySet(models.QuerySet):
    def published(self, now=None):
        """Posts visible on the website, newest first.

        A post is visible when it is marked as published and its publication
        date has been reached (allows scheduling posts in advance).
        """
        now = now or timezone.now()
        return self.filter(is_published=True, published_at__lte=now).order_by(
            "-published_at"
        )


def post_image_path(instance, filename):
    return f"posts/{timezone.now():%Y}/{filename}"


class Post(models.Model):
    title = models.CharField("Titel", max_length=200)
    slug = models.SlugField(
        "Kurzname für die Adresse",
        max_length=200,
        unique=True,
        help_text="Wird aus dem Titel vorgeschlagen und erscheint in der Adresse "
        "des Beitrags. Nach dem Veröffentlichen nicht mehr ändern.",
    )
    body = models.TextField("Text", help_text=MARKDOWN_HELP_TEXT)
    image = models.ImageField(
        "Bild", upload_to=post_image_path, blank=True, help_text="Optional."
    )
    image_alt = models.CharField(
        "Bildbeschreibung",
        max_length=250,
        blank=True,
        help_text="Kurze Beschreibung des Bildinhalts für Screenreader und "
        "Suchmaschinen, z. B. «Drei Kinder programmieren einen Roboter».",
    )
    author = models.CharField("Autor/in", max_length=100)
    published_at = models.DateTimeField(
        "Veröffentlichungsdatum",
        default=timezone.now,
        help_text="Liegt das Datum in der Zukunft, erscheint der Beitrag erst dann.",
    )
    is_published = models.BooleanField(
        "Veröffentlicht",
        default=False,
        help_text="Ohne Häkchen ist der Beitrag ein Entwurf und nicht sichtbar.",
    )
    meta_description = models.CharField(
        "Beschreibung für Suchmaschinen",
        max_length=160,
        blank=True,
        help_text="Optional, max. 160 Zeichen. Leer = Anfang des Textes.",
    )
    created_at = models.DateTimeField("Erstellt", auto_now_add=True)
    updated_at = models.DateTimeField("Geändert", auto_now=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        verbose_name = "Beitrag"
        verbose_name_plural = "Beiträge"
        ordering = ["-published_at"]
        indexes = [models.Index(fields=["is_published", "published_at"])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("posts:detail", kwargs={"slug": self.slug})

    def clean(self):
        if self.image and not self.image_alt:
            raise ValidationError(
                {"image_alt": "Bitte beschreibe kurz, was auf dem Bild zu sehen ist."}
            )

    def get_meta_description(self):
        return self.meta_description or markdown_to_plain_text(self.body)

    def is_visible(self, now=None):
        now = now or timezone.now()
        return self.is_published and self.published_at <= now
