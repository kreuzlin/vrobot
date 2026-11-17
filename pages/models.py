from django.db import models
from django.urls import reverse

from core.widgets import MARKDOWN_HELP_TEXT


class Page(models.Model):
    """A fixed page (About us, Get involved, Contact).

    Pages are created by a data migration and have fixed URLs; only their
    content is editable in the admin.
    """

    # slug → URL name; the slug never changes.
    URL_NAMES = {
        "ueber-uns": "pages:about",
        "mitmachen": "pages:join",
        "kontakt": "pages:contact",
    }

    title = models.CharField("Titel", max_length=200)
    slug = models.SlugField("Kurzname", max_length=100, unique=True)
    body = models.TextField("Text", blank=True, help_text=MARKDOWN_HELP_TEXT)
    meta_description = models.CharField(
        "Beschreibung für Suchmaschinen",
        max_length=160,
        help_text="Max. 160 Zeichen. Erscheint z. B. in den Google-Suchergebnissen.",
    )
    updated_at = models.DateTimeField("Geändert", auto_now=True)

    class Meta:
        verbose_name = "Seite"
        verbose_name_plural = "Seiten"
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(self.URL_NAMES[self.slug])
