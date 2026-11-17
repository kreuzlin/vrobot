# Architektur

## Überblick

```
Browser ──HTTPS──▶ Caddy ──HTTP──▶ web (Django + Gunicorn) ──▶ db (PostgreSQL)
                     │
                     └─ liefert /static/ und /media/ direkt aus
```

Alles läuft per Docker Compose auf einem UpCloud-Server (Ubuntu 26.04 LTS, x86_64).

## Komponenten

| Dienst  | Aufgabe                                                        |
|---------|----------------------------------------------------------------|
| `caddy` | TLS (Let's Encrypt, automatisch), Reverse Proxy, statische Dateien und Medien |
| `web`   | Django-App unter Gunicorn                                      |
| `db`    | PostgreSQL, Daten auf benanntem Volume                         |

Volumes: `postgres_data`, `media`, `static`, `caddy_data` (Zertifikate).

## Django-Struktur (geplant)

| App         | Inhalt                                               |
|-------------|------------------------------------------------------|
| `config`    | Settings, URLs, WSGI (Projektpaket)                  |
| `core`      | Basis-Template, Startseite, SEO-Helfer (Titel/Meta)  |
| `posts`     | Beiträge                                             |
| `events`    | Agenda                                               |
| `documents` | Dokumente mit Kategorie und Jahr                     |
| `pages`     | Feste Seiten (Über uns, Mitmachen)                   |
| `contact`   | Kontaktformular mit Spamschutz, E-Mail-Versand       |

Der GearsBot-Emulator wird nicht integriert, sondern nur verlinkt.

## Konfiguration

- Alle umgebungsabhängigen Werte über Umgebungsvariablen aus `.env`
  (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, E-Mail-Zugang …).
- `.env.example` dokumentiert jede Variable.
- Ein Settings-Modul; Unterschiede Dev/Prod nur über Umgebungsvariablen.

## Build und Deployment

1. Push auf `master` → GitHub Actions: Ruff, Tests, dann Docker-Image für
   `linux/amd64` bauen und in die GitHub Container Registry (GHCR) pushen.
2. Auf dem Server: `docker compose pull && docker compose up -d`, danach
   `migrate` (Details folgen, sobald das Deployment steht).

Lokal (Apple Silicon) wird das Image nativ für `arm64` gebaut; das
Server-Image entsteht nur in CI.

## Betrieb

- **Backups:** regelmässiger `pg_dump` plus Sicherung des Medien-Volumes,
  ausserhalb des Servers abgelegt (Verfahren noch festzulegen).
- **Umstellung:** Die alte Seite auf Hostpoint bleibt live, bis die neue unter
  einer Test-Domain abgenommen ist. Danach DNS umstellen; alte URLs, wo
  sinnvoll, per Redirect weiterleiten.

## Offene Punkte

- Domain/Subdomain für die Testphase
- E-Mail-Versand für das Kontaktformular (SMTP von Hostpoint oder Dienst)
- Backup-Ziel
- Welche Inhalte von der alten Seite übernommen werden
