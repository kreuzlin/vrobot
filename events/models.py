from datetime import datetime, time

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def start_of_today(now=None):
    """Return midnight of the current local day as an aware datetime."""
    now = now or timezone.now()
    today = timezone.localdate(now)
    return timezone.make_aware(datetime.combine(today, time.min))


class EventQuerySet(models.QuerySet):
    def upcoming(self, now=None):
        """Events that are not over yet, ordered by start.

        - With an end: visible until the end has passed.
        - Without an end: visible for the whole day of the start, so an event
          does not disappear from the website the minute it begins.
        """
        now = now or timezone.now()
        return self.filter(
            models.Q(end__gte=now)
            | models.Q(end__isnull=True, start__gte=start_of_today(now))
        ).order_by("start")


class Event(models.Model):
    title = models.CharField("Titel", max_length=200)
    start = models.DateTimeField("Beginn")
    end = models.DateTimeField(
        "Ende",
        null=True,
        blank=True,
        help_text="Optional. Ohne Ende wird der Termin bis zum Ende des Tages angezeigt.",
    )
    location = models.CharField("Ort", max_length=200, blank=True)
    description = models.TextField(
        "Beschreibung",
        blank=True,
        help_text="Optional. Einfacher Text, Zeilenumbrüche werden übernommen.",
    )
    link = models.URLField(
        "Link",
        blank=True,
        help_text="Optional, z. B. zur Anmeldung oder zu weiteren Informationen.",
    )
    created_at = models.DateTimeField("Erstellt", auto_now_add=True)
    updated_at = models.DateTimeField("Geändert", auto_now=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        verbose_name = "Termin"
        verbose_name_plural = "Termine"
        ordering = ["-start"]
        indexes = [models.Index(fields=["start"]), models.Index(fields=["end"])]

    def __str__(self):
        local_start = timezone.localtime(self.start)
        return f"{self.title} ({local_start:%d.%m.%Y})"

    def clean(self):
        if self.start and self.end and self.end < self.start:
            raise ValidationError({"end": "Das Ende muss nach dem Beginn liegen."})

    def is_upcoming(self, now=None):
        """Python counterpart of `EventQuerySet.upcoming()` for one event."""
        now = now or timezone.now()
        if self.end:
            return self.end >= now
        return self.start >= start_of_today(now)

    @property
    def ends_same_day(self):
        if not self.end:
            return True
        return timezone.localdate(self.start) == timezone.localdate(self.end)
