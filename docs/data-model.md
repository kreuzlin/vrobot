# Datenmodell

Entwurf für Version 1. Wird bei jeder Modelländerung nachgeführt.
Alle Modelle haben `created_at`/`updated_at` (automatisch).

## Beitrag – `posts.Post`

| Feld           | Typ                     | Bemerkung                              |
|----------------|-------------------------|----------------------------------------|
| `title`        | CharField               | Pflicht                                |
| `slug`         | SlugField, eindeutig    | für die URL, aus dem Titel vorbefüllt  |
| `body`         | TextField               | Inhalt (Formatierung: siehe offene Punkte) |
| `image`        | ImageField, optional    | inkl. Alt-Text-Feld `image_alt`        |
| `author`       | CharField               | Anzeigename, nicht zwingend ein Admin-User |
| `published_at` | DateTimeField           | Beiträge in der Zukunft sind noch nicht sichtbar |
| `is_published` | BooleanField            | Entwurf vs. veröffentlicht             |
| `meta_description` | CharField, optional | Fallback: Anfang des Textes            |

Sortierung: neueste zuerst.

## Termin – `events.Event`

| Feld          | Typ                    | Bemerkung                         |
|---------------|------------------------|-----------------------------------|
| `title`       | CharField              | Pflicht                           |
| `start`       | DateTimeField          | Pflicht                           |
| `end`         | DateTimeField, optional| muss nach `start` liegen          |
| `location`    | CharField, optional    |                                   |
| `description` | TextField, optional    |                                   |
| `link`        | URLField, optional     | z. B. Anmeldung                   |

Öffentlich sichtbar: Termine, deren Ende (bzw. Start, wenn kein Ende) nicht in
der Vergangenheit liegt. Umgesetzt als QuerySet-Methode `upcoming()`; keine
Löschung, die Termine bleiben im Admin erhalten.

## Dokument – `documents.Document`

| Feld        | Typ                          | Bemerkung                     |
|-------------|------------------------------|-------------------------------|
| `title`     | CharField                    | Pflicht                       |
| `category`  | ForeignKey → `DocumentCategory` | z. B. Statuten, Formulare, Jahresberichte |
| `year`      | PositiveSmallIntegerField    | Pflicht                       |
| `file`      | FileField                    | primär PDF                    |
| `description` | TextField, optional        |                               |

`DocumentCategory`: `name`, `slug`, `order`. Als eigenes Modell, damit der
Vorstand Kategorien selbst ergänzen kann.

Anzeige: nach Kategorie gruppiert, innerhalb nach Jahr absteigend.

## Feste Seite – `pages.Page`

| Feld               | Typ                  | Bemerkung                        |
|--------------------|----------------------|----------------------------------|
| `title`            | CharField            |                                  |
| `slug`             | SlugField, eindeutig | `ueber-uns`, `mitmachen`, `kontakt` |
| `body`             | TextField            |                                  |
| `meta_description` | CharField            |                                  |

Die Seiten werden per Datenmigration angelegt; Struktur und URLs sind fix,
nur der Text ist im Admin editierbar. Die Kontaktseite zeigt zusätzlich das
Formular.

## Kontaktanfrage – `contact.ContactMessage`

| Feld         | Typ           | Bemerkung                    |
|--------------|---------------|------------------------------|
| `name`       | CharField     |                              |
| `email`      | EmailField    |                              |
| `message`    | TextField     |                              |
| `created_at` | DateTimeField |                              |

Wird gespeichert **und** per E-Mail an den Verein weitergeleitet, damit nichts
verloren geht, falls der Mailversand ausfällt. Löschfrist festlegen (Datenschutz).

## Offene Punkte

- Textformatierung in Beiträgen/Seiten: Markdown (einfach, sicher) oder
  Rich-Text-Editor im Admin? → ADR, sobald entschieden.
- Mehrere Bilder pro Beitrag nötig?
