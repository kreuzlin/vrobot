"""One-time import of the content of the old PHP site (vrobot.ch).

Imports the texts of "Über uns", "Mitmachen" and "Kontakt", the only post and
the downloadable documents (fetched from the old site). Texts are taken over
from the old site with spelling fixes only. The topics of "Mitmachen" with
their images are fixed in the template (pages/topics.py), not imported.

Safe to run more than once:
- pages are only overwritten while they still contain the placeholder text
  from the initial migration (or with --force),
- the post and documents are skipped if they already exist.

Usage: python manage.py import_old_site [--dry-run] [--force]
"""

import datetime
import urllib.request
from zoneinfo import ZoneInfo

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from documents.models import Document, DocumentCategory
from pages.models import Page
from posts.models import Post

OLD_SITE = "https://vrobot.ch"
PLACEHOLDER_MARKER = "Platzhalter"

PAGES = {
    "ueber-uns": {
        "meta_description": (
            "VRoboT fördert seit 2017 Kinder und Jugendliche in Robotik: "
            "konstruieren, programmieren, forschen und präsentieren – im Team."
        ),
        "body": """\
## Motivation

VRoboT wurde von Michel Peder und Marc Thoma im Januar 2017 mit dem Zweck \
gegründet, Kinder und Jugendliche im Bereich Robotik zu fördern. \
Kernkompetenzen wie Konstruieren und Programmieren wie auch Forschen und \
Präsentieren stehen im Mittelpunkt. Es wird vor allem im Team getüftelt und \
trainiert, um zentrale Kooperations- und Kommunikationsfähigkeiten zu fördern. \
Ebenso wird der Kontakt zu Fachleuten und Firmen hergestellt und gepflegt.

Robotik-Wettkämpfe wie zum Beispiel die World Robot Olympiad bieten die \
herausfordernde Möglichkeit, sich mit dem erarbeiteten VRoboT-Know-how in \
sportlichem Umfeld mit anderen Technikbegeisterten zu messen.

## Unsere Regeln

- Während des Trainings lassen wir uns nicht von Videospielen und anderen \
Medien wie z.\u00a0B. «Filmchen» ablenken.
- Wir helfen uns gegenseitig und sabotieren uns nicht.
- Wir gehen mit Werkzeugen und Material sorgsam um.
- Aufräumen ist Ehrensache, Drückeberger dulden wir keine.
- Wir begegnen uns mit Anstand und Respekt.

## Downloads

Statuten, Jahresberichte und das Beitrittsformular findest du unter \
[Dokumente](/dokumente/).
""",
    },
    "mitmachen": {
        "meta_description": (
            "Mindstorms, Arduino, Elektronik, Python, Scratch und Präsentieren: "
            "die Themen bei VRoboT – spielerisch lernen im Team."
        ),
        "body": """\
> «Lehren heisst, ein Feuer entfachen, und nicht, einen leeren Eimer füllen.» \
– Heraklit
>
> «Gebt Lehrern keine Chance. Verblüfft sie durch Wissen!» – unbekannt

## Mitglied werden

Das Beitrittsformular findest du unter [Dokumente](/dokumente/). Fragen \
beantworten wir gerne über das [Kontaktformular](/kontakt/).
""",
    },
    "kontakt": {
        "meta_description": (
            "Fragen zum Verein Robotik Talente (VRoboT)? Schreib uns über das "
            "Kontaktformular."
        ),
        "body": """\
Hast du Fragen? Wir haben Antworten …

Präsident: Marc Thoma
""",
    },
}

POST = {
    "slug": "die-welt-braucht-arduino",
    "title": "Die Welt braucht Arduino",
    "author": "Linard",
    "published_at": datetime.datetime(
        2020, 10, 4, 12, 0, tzinfo=ZoneInfo("Europe/Zurich")
    ),
    "meta_description": "Ein Computer zum Anfassen: warum Arduino eine "
    "beliebte Plattform für eigene Projekte rund um das Internet of Things ist.",
    "body": """\
*Ein Computer zum Anfassen …*

## Grundsätzliches zum Arduino

Wir leben in einer Welt, in der Computer nicht nur immer selbstverständlicher, \
sondern auch immer weniger greifbar werden. Viele Computer haben wir durch \
unser Smartphone oder iPad ersetzt. Und die eigentlichen Computer auf unseren \
Schreibtischen sind geschlossene, kompakte Systeme, die wenig Raum für \
Experimente zulassen.

Zum Glück ist da noch das Internet of Things (IoT). Also die vernetzten Dinge, \
welche wir in Zukunft zu Hunderten antreffen werden, die aber erst noch \
erfunden werden müssen.

Arduino ist eine beliebte Entwicklungsplattform für IoT-Projekte. Es gibt dazu \
eine grosse und stetig wachsende Auswahl an Hardware, meist zu erschwinglichen \
Preisen.

## Was brauchen wir dazu?

Wir benötigen einen beliebigen Computer mit installierter Arduino-Software. \
Die Arduino-Software kann man sich auf [www.arduino.cc](https://www.arduino.cc) \
gratis besorgen. Weiter braucht man ein Entwicklungsboard mit einem \
Mikrocontroller, z.\u00a0B. einen Arduino UNO. An den Mikrocontroller kann man dann \
je nach Belieben Sensoren anschliessen und z.\u00a0B. Motoren ansteuern.
""",
}

# (title, category slug, year, file name on the old site under /attachments/)
DOCUMENTS = [
    ("Statuten", "statuten", 2022, "Statuten_VRoboT.pdf"),
    (
        "Beitritts- und Bewerbungsformular",
        "formulare",
        2022,
        "Beitritts-_und_Bewerbungsformular_-_VRoboT_V-12-23.pdf",
    ),
    *(
        (
            f"Jahresbericht des Präsidenten {year}",
            "jahresberichte",
            year,
            f"Jahresbericht_{year % 100}_-_Praesident.pdf",
        )
        for year in (2022, 2021, 2019, 2018, 2017)
    ),
]


def download(url):
    """Fetch a file from the old site. Separate function so tests can mock it."""
    request = urllib.request.Request(url, headers={"User-Agent": "vrobot-import"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


class Command(BaseCommand):
    help = "Importiert die Inhalte der alten Website vrobot.ch (einmalig)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Nur anzeigen, was importiert würde; nichts speichern.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Seitentexte auch überschreiben, wenn sie schon bearbeitet wurden.",
        )

    def handle(self, *args, dry_run=False, force=False, **options):
        self.dry_run = dry_run
        with transaction.atomic():
            self.import_pages(force)
            self.import_post()
            self.import_documents()
            if dry_run:
                transaction.set_rollback(True)
        if dry_run:
            self.stdout.write(self.style.WARNING("Probelauf: nichts gespeichert."))

    def log(self, action, what):
        self.stdout.write(f"{action:<12} {what}")

    def import_pages(self, force):
        for slug, data in PAGES.items():
            try:
                page = Page.objects.get(slug=slug)
            except Page.DoesNotExist as exc:
                raise CommandError(f"Seite «{slug}» fehlt – Migrationen?") from exc
            if PLACEHOLDER_MARKER not in page.body and not force:
                self.log("übersprungen", f"Seite «{page.title}» (schon bearbeitet)")
                continue
            page.body = data["body"]
            page.meta_description = data["meta_description"]
            page.full_clean()
            page.save()
            self.log("importiert", f"Seite «{page.title}»")

    def import_post(self):
        if Post.objects.filter(slug=POST["slug"]).exists():
            self.log("übersprungen", f"Beitrag «{POST['title']}» (existiert)")
            return
        post = Post(**POST, is_published=True)
        post.full_clean()
        post.save()
        self.log("importiert", f"Beitrag «{post.title}»")

    def import_documents(self):
        for title, category_slug, year, filename in DOCUMENTS:
            if Document.objects.filter(title=title).exists():
                self.log("übersprungen", f"Dokument «{title}» (existiert)")
                continue
            category = DocumentCategory.objects.get(slug=category_slug)
            url = f"{OLD_SITE}/attachments/{filename}"
            if self.dry_run:
                # Files are not covered by the transaction rollback.
                self.log("importiert", f"Dokument «{title}» (Probelauf, {url})")
                continue
            try:
                data = download(url)
            except OSError as exc:
                raise CommandError(f"Download fehlgeschlagen: {url} ({exc})") from exc
            document = Document(title=title, category=category, year=year)
            document.file.save(filename, ContentFile(data), save=False)
            document.full_clean()
            document.save()
            self.log("importiert", f"Dokument «{title}» ({len(data) // 1024} KB)")
