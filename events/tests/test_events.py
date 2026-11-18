"""Tests for the events calendar."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event

ZURICH = ZoneInfo("Europe/Zurich")


def at(year, month, day, hour=0, minute=0):
    """Aware datetime in Swiss local time."""
    return datetime(year, month, day, hour, minute, tzinfo=ZURICH)


class UpcomingTests(TestCase):
    """`Event.objects.upcoming()` hides past events automatically."""

    # Reference time for all tests: Saturday, 21 Nov 2026, 15:00 local time.
    now = at(2026, 11, 21, 15, 0)

    def make(self, title, start, end=None):
        return Event.objects.create(title=title, start=start, end=end)

    def assert_upcoming(self, *titles):
        result = [e.title for e in Event.objects.upcoming(now=self.now)]
        self.assertEqual(result, list(titles))

    def test_future_event_is_shown(self):
        self.make("Workshop", at(2026, 11, 28, 14))
        self.assert_upcoming("Workshop")

    def test_past_event_with_end_is_hidden(self):
        self.make("Vorbei", at(2026, 11, 21, 9), at(2026, 11, 21, 12))
        self.assert_upcoming()

    def test_running_event_is_shown_until_its_end(self):
        self.make("Läuft", at(2026, 11, 21, 14), at(2026, 11, 21, 17))
        self.assert_upcoming("Läuft")

    def test_multi_day_event_is_shown_until_its_end(self):
        self.make("Lager", at(2026, 11, 19, 9), at(2026, 11, 22, 16))
        self.assert_upcoming("Lager")

    def test_event_without_end_is_shown_for_the_whole_start_day(self):
        self.make("Heute früh", at(2026, 11, 21, 8))
        self.assert_upcoming("Heute früh")

    def test_event_without_end_is_hidden_the_next_day(self):
        self.make("Gestern", at(2026, 11, 20, 23, 30))
        self.assert_upcoming()

    def test_day_boundary_uses_swiss_local_time(self):
        # 00:30 local on the 21st is still the 20th in UTC.
        self.make("Kurz nach Mitternacht", at(2026, 11, 21, 0, 30))
        self.assert_upcoming("Kurz nach Mitternacht")

    def test_ordered_by_start(self):
        self.make("Später", at(2026, 12, 5, 10))
        self.make("Früher", at(2026, 11, 25, 10))
        self.assert_upcoming("Früher", "Später")

    def test_is_upcoming_matches_queryset(self):
        events = [
            self.make("a", at(2026, 11, 28, 14)),
            self.make("b", at(2026, 11, 21, 9), at(2026, 11, 21, 12)),
            self.make("c", at(2026, 11, 21, 8)),
            self.make("d", at(2026, 11, 20, 23, 30)),
        ]
        upcoming = set(Event.objects.upcoming(now=self.now))
        for event in events:
            with self.subTest(event=event.title):
                self.assertEqual(event.is_upcoming(now=self.now), event in upcoming)


class ValidationTests(TestCase):
    def test_end_before_start_is_rejected(self):
        event = Event(
            title="Falsch", start=at(2026, 11, 21, 15), end=at(2026, 11, 21, 14)
        )
        with self.assertRaises(ValidationError) as ctx:
            event.full_clean()
        self.assertIn("end", ctx.exception.message_dict)

    def test_end_is_optional(self):
        Event(title="Ohne Ende", start=at(2026, 11, 21, 15)).full_clean()


class EventListViewTests(TestCase):
    def setUp(self):
        now = timezone.now()
        Event.objects.create(
            title="Robotik-Workshop",
            start=now + timedelta(days=7),
            location="Schulhaus Musterwil",
            description="Für Einsteiger.\nBitte Laptop mitnehmen.",
        )
        Event.objects.create(
            title="Altes Training",
            start=now - timedelta(days=7),
            end=now - timedelta(days=7) + timedelta(hours=2),
        )

    def test_shows_only_upcoming_events(self):
        response = self.client.get(reverse("events:list"))
        self.assertContains(response, "Robotik-Workshop")
        self.assertContains(response, "Schulhaus Musterwil")
        self.assertContains(response, "Bitte Laptop mitnehmen.")
        self.assertNotContains(response, "Altes Training")

    def test_title_and_navigation(self):
        response = self.client.get(reverse("events:list"))
        self.assertContains(response, "<title>Agenda – VRoboT</title>", html=True)
        self.assertContains(
            response, f'<a href="{reverse("events:list")}" aria-current="page">'
        )

    def test_empty_state(self):
        Event.objects.all().delete()
        response = self.client.get(reverse("events:list"))
        self.assertContains(response, "Zurzeit sind keine Termine geplant.")

    def test_dates_are_german(self):
        Event.objects.all().delete()
        Event.objects.create(title="Wettbewerb", start=at(2030, 3, 2, 9, 30))
        response = self.client.get(reverse("events:list"))
        self.assertContains(response, "Samstag, 2. März 2030")
        self.assertContains(response, "09:30")


class AgendaByMonthTests(TestCase):
    def test_events_are_grouped_by_month_with_jump_links(self):
        Event.objects.create(title="Training A", start=at(2030, 3, 1, 18))
        Event.objects.create(title="Training B", start=at(2030, 3, 8, 18))
        Event.objects.create(title="Training C", start=at(2030, 4, 5, 18))
        response = self.client.get(reverse("events:list"))
        content = response.content.decode()

        self.assertEqual(
            [len(group["events"]) for group in response.context["months"]], [2, 1]
        )
        self.assertContains(response, 'href="#monat-2030-03"')
        self.assertContains(response, 'id="monat-2030-04"')
        self.assertInHTML(
            '<h2 class="section-title" id="monat-2030-03-titel">März 2030</h2>',
            content,
        )
        self.assertLess(content.index("März 2030</h2>"), content.index("Training A"))
        self.assertLess(content.index("Training B"), content.index("April 2030</h2>"))

    def test_month_uses_swiss_local_time(self):
        # 31 March 23:30 UTC is already 1 April in Switzerland (CEST, UTC+2).
        Event.objects.create(
            title="Mitternacht",
            start=datetime(2030, 3, 31, 23, 30, tzinfo=UTC),
        )
        response = self.client.get(reverse("events:list"))
        self.assertEqual(response.context["months"][0]["month"].month, 4)


class HomePageEventsTests(TestCase):
    def test_home_shows_next_three_events(self):
        now = timezone.now()
        for i in range(1, 5):
            Event.objects.create(title=f"Termin {i}", start=now + timedelta(days=i))
        response = self.client.get(reverse("core:home"))
        for i in range(1, 4):
            self.assertContains(response, f"Termin {i}")
        self.assertNotContains(response, "Termin 4")
        self.assertContains(response, reverse("events:list"))
