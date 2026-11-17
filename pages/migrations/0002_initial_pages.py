"""Create the fixed pages with placeholder content.

The texts are placeholders and are meant to be replaced in the admin.
"""

from django.db import migrations

PAGES = [
    {
        "slug": "ueber-uns",
        "title": "Über uns",
        "meta_description": (
            "Wer wir sind: Der Verein Robotik Talente (VRoboT) fördert Kinder "
            "und Jugendliche in Robotik und Programmieren."
        ),
        "body": (
            "*Platzhalter – bitte im Admin unter «Seiten» ersetzen.*\n\n"
            "## Wer wir sind\n\n"
            "Der Verein Robotik Talente (VRoboT) fördert Kinder und Jugendliche, "
            "die sich für Robotik und Programmieren begeistern.\n\n"
            "## Vorstand\n\n"
            "- Präsidium: …\n"
            "- Finanzen: …\n"
        ),
    },
    {
        "slug": "mitmachen",
        "title": "Mitmachen",
        "meta_description": (
            "So kannst du beim Verein Robotik Talente mitmachen: als Teilnehmerin, "
            "Teilnehmer, Coach oder Mitglied."
        ),
        "body": (
            "*Platzhalter – bitte im Admin unter «Seiten» ersetzen.*\n\n"
            "## Für Kinder und Jugendliche\n\n"
            "…\n\n"
            "## Als Coach oder Helfer/in\n\n"
            "…\n\n"
            "## Mitglied werden\n\n"
            "…\n"
        ),
    },
    {
        "slug": "kontakt",
        "title": "Kontakt",
        "meta_description": "So erreichst du den Verein Robotik Talente.",
        "body": (
            "*Platzhalter – bitte im Admin unter «Seiten» ersetzen.*\n\n"
            "Hast du Fragen? Schreib uns über das Formular.\n"
        ),
    },
]


def create_pages(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    for data in PAGES:
        Page.objects.get_or_create(slug=data["slug"], defaults=data)


def remove_pages(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    Page.objects.filter(slug__in=[p["slug"] for p in PAGES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_pages, remove_pages),
    ]
