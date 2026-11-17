# vrobot.ch

Neubau der Website des **Vereins Robotik Talente (VRoboT)**.

Die bisherige PHP-Seite auf Hostpoint bleibt live, bis die neue Seite fertig ist
und der DNS-Eintrag umgestellt wird.

## Stack

| Bereich        | Wahl                                              |
|----------------|---------------------------------------------------|
| Framework      | Django 5.2 LTS, Django-Templates (kein SPA)       |
| Sprache        | Python, Abhängigkeiten mit [uv](https://docs.astral.sh/uv/) |
| Lint/Format    | Ruff                                              |
| Datenbank      | PostgreSQL                                        |
| Laufzeit       | Docker Compose (lokal und auf dem Server)         |
| Webserver      | Caddy (Reverse Proxy, automatisches HTTPS)        |
| Hosting        | UpCloud, Ubuntu 26.04 LTS, x86_64                 |
| CI/CD          | GitHub Actions baut `linux/amd64`-Images          |

Begründungen: siehe [`docs/decisions/`](docs/decisions/).

## Inhalte (Version 1)

- Beiträge (Titel, Text, Bild, Autor, Datum)
- Agenda mit Terminen – vergangene Termine werden automatisch ausgeblendet
- Dokumente (Statuten, Formulare, Jahresberichte) mit Kategorie und Jahr
- Feste Seiten: Über uns, Mitmachen, Kontakt (Formular mit Spamschutz)
- Link zum bestehenden GearsBot-Emulator
- Pflege aller Inhalte über das Django-Admin
- Saubere Seitentitel und Meta-Descriptions
- Sprache der Website: Deutsch

## Lokale Entwicklung

> Die folgenden Befehle gelten, sobald das Django-Grundgerüst steht.

```bash
cp .env.example .env          # Werte anpassen, .env nie committen
docker compose up --build     # Web + PostgreSQL starten
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py createsuperuser
```

Website: <http://localhost:8000> · Admin: <http://localhost:8000/admin/>

Qualitätschecks:

```bash
uv run ruff check .
uv run ruff format .
uv run python manage.py test
```

## Dokumentation

- [`CLAUDE.md`](CLAUDE.md) – Arbeitsregeln für Claude Code (und Menschen)
- [`docs/architecture.md`](docs/architecture.md) – Aufbau, Deployment, Betrieb
- [`docs/data-model.md`](docs/data-model.md) – Datenmodell
- [`docs/decisions/`](docs/decisions/) – Architecture Decision Records (ADRs)
