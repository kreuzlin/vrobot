# CLAUDE.md

Leitfaden für die Arbeit an diesem Repository (vrobot.ch, Website des Vereins
Robotik Talente). Gilt für Claude Code und für menschliche Mitwirkende.

## Projektkontext

- Neubau der Vereinswebsite; die alte PHP-Seite auf Hostpoint bleibt live, bis
  die neue fertig ist. Nichts an der alten Seite oder am DNS ändern.
- Inhaltsseite mit wenig Interaktivität. Inhalte werden von Vereinsmitgliedern
  über das Django-Admin gepflegt – das Admin muss für Laien verständlich sein
  (deutsche `verbose_name`, Hilfetexte, sinnvolle Listen und Filter).
- Umfang Version 1: siehe README.md. Keine Features darüber hinaus ohne Rückfrage.

## Stack (verbindlich)

- Django 5.2 LTS mit Django-Templates. Kein React/SPA, kein Build-Schritt für
  Frontend, solange nicht nötig.
- Python-Abhängigkeiten ausschliesslich mit **uv** (`pyproject.toml`, `uv.lock`).
  Kein `pip install`, kein `requirements.txt`.
- **Ruff** für Linting und Formatierung.
- **PostgreSQL** – auch lokal, kein SQLite.
- **Docker Compose** für Entwicklung und Betrieb.
- Produktion: UpCloud, Ubuntu 26.04 LTS, Caddy (automatisches HTTPS).
- Images baut GitHub Actions für `linux/amd64` (Entwicklung auf Apple Silicon,
  Server ist x86).

Begründungen stehen in `docs/decisions/`. Wer davon abweichen will, schreibt
zuerst einen neuen ADR.

## Sprache

- Website-Inhalte, Templates, Admin-Beschriftungen, Doku: **Deutsch** (Schweizer
  Schreibweise, also «ss» statt «ß»).
- Code (Bezeichner, Modell- und Feldnamen), Commit-Messages: Englisch.
- `LANGUAGE_CODE = "de-ch"`, `TIME_ZONE = "Europe/Zurich"`, `USE_TZ = True`.

## Arbeitsweise

- **Kleine Schritte.** Nach jedem funktionierenden Schritt committen
  (Tests grün, Ruff sauber).
- Vor einem Commit: `uv run ruff check . && uv run ruff format --check . && uv run python manage.py test`.
- Für die wichtigsten Funktionen gibt es Tests (z. B. Agenda blendet vergangene
  Termine aus, Kontaktformular inkl. Spamschutz, Sichtbarkeit von Beiträgen,
  Seitentitel/Meta-Descriptions).
- Doku mitführen: Datenmodell-Änderungen → `docs/data-model.md`, Architektur-
  oder Betriebsänderungen → `docs/architecture.md`, grundlegende Entscheidungen
  → neuer ADR in `docs/decisions/`.

## Secrets

- Secrets nur in `.env` (nie committen). Im Repo liegt nur `.env.example` mit
  Platzhaltern und Kommentaren.
- Neue Umgebungsvariablen immer gleichzeitig in `.env.example` dokumentieren.
- Keine Passwörter, Tokens oder Kundendaten in Code, Tests, Fixtures oder Doku.

## Konventionen

- Django-Apps klein und thematisch (z. B. `posts`, `events`, `documents`,
  `pages`, `contact`).
- Jede öffentliche Seite setzt `<title>` und `<meta name="description">` über
  einen gemeinsamen Mechanismus im Basis-Template.
- Hochgeladene Dateien (Bilder, PDFs) liegen unter `MEDIA_ROOT` auf einem
  Docker-Volume; statische Dateien werden beim Image-Build gesammelt.
- Zeitlogik (z. B. «vergangene Termine») über `django.utils.timezone.now()`,
  nie über naive Datetimes.

## Nützliche Befehle

```bash
docker compose up --build
docker compose exec web uv run python manage.py <befehl>
uv run ruff check . --fix
uv run ruff format .
uv run python manage.py test
```
