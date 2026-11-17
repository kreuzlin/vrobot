# Architecture

## Overview

```
Browser ──HTTPS──▶ Caddy ──HTTP──▶ web (Django + Gunicorn) ──▶ db (PostgreSQL)
                     │
                     └─ serves /static/ and /media/ directly
```

Everything runs via Docker Compose on an UpCloud server (Ubuntu 26.04 LTS, x86_64).

## Components

| Service | Responsibility                                                       |
|---------|----------------------------------------------------------------------|
| `caddy` | TLS (Let's Encrypt, automatic), reverse proxy, static and media files |
| `web`   | Django app running under Gunicorn                                     |
| `db`    | PostgreSQL, data on a named volume                                    |

Volumes: `postgres_data`, `media`, `static`, `caddy_data` (certificates).

## Django structure (planned)

| App         | Contents                                              |
|-------------|-------------------------------------------------------|
| `config`    | Settings, URLs, WSGI (project package)                |
| `core`      | Base template, home page, SEO helpers (title/meta)    |
| `posts`     | Posts                                                 |
| `events`    | Events calendar                                       |
| `documents` | Documents with category and year                      |
| `pages`     | Static pages (About us, Get involved)                 |
| `contact`   | Contact form with spam protection, email via Hostpoint SMTP |

The GearsBot emulator is not integrated, only linked (`GEARSBOT_URL`).

### `core` in detail

- `base.html`: layout, header with main navigation, footer, SEO tags
- `seo.py`: `SeoMixin` and `build_title()` (`"<page> – VRoboT"`, home page:
  `"VRoboT – Verein Robotik Talente"`)
- `navigation.py`: main navigation entries; `context_processors.site` resolves
  them and marks the current page
- German `404.html`; standalone `500.html` without template logic
- `markdown.py`: `render_markdown()` (Markdown → HTML, sanitised with `nh3`
  allowlist; `# ` headings become `<h2>`), template filter `|markdown`
- `widgets.py`: `MarkdownEditor` admin widget using EasyMDE, vendored under
  `core/static/core/vendor/easymde/` (v2.21.0, MIT) with German text buttons,
  so the admin loads no external resources

### Admin

- Editors: staff users in the group "Redaktion" (`core/editor_group.py`,
  created by migration `core.0001_editor_group`): manage posts, events,
  documents and categories; edit pages; read/delete contact messages; no
  access to users and permissions.
- Start page (`core/templates/admin/index.html`): quick links based on the
  user's permissions, warning for contact messages that were not emailed.
  `core` is listed before `django.contrib.admin` so its template wins.
- Password reset from the login page (Django auth views, emails via SMTP).
- Guide for editors (German): `docs/editor-guide.md`.

### `contact`

`/kontakt/` combines the "Kontakt" page (`pages.views.PageMixin`) with the
contact form. Spam protection: honeypot + signed timing token (ADR 0011).
Messages are saved, then emailed; failures are logged and visible in the
admin (`email_sent`).

### Logging

Logs go to stdout (collected by Docker). `django.request` logs only errors;
access logs come from Caddy.

### Media files

Uploads go to `MEDIA_ROOT` (`media/` locally, a volume in production). In
development Django serves them (`DEBUG` only); in production Caddy does.

## Configuration

- Settings: `config/settings.py`, values read with `django-environ`.
- Python 3.14 (`.python-version`), dependencies in `pyproject.toml` / `uv.lock`.

- All environment-specific values come from environment variables in `.env`
  (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, email credentials …).
- `.env.example` documents every variable.
- A single settings module; dev/prod differences only via environment variables.

## Docker image

- `Dockerfile`: `python:3.14-slim` + uv; dependencies installed with
  `uv sync --locked --no-dev` into `/opt/venv`; static files collected at build
  time; runs as non-root user `app`; default command is Gunicorn on port 8000.
- `compose.yaml` (development): `db` (PostgreSQL 18, volume `postgres_data`)
  and `web` (bind-mounted source, `migrate` + `runserver` on start).

## Build and deployment

1. Merge to `main` → GitHub Actions: Ruff, tests, then build the Docker image
   for `linux/amd64` and push it to the GitHub Container Registry (GHCR).
2. On the server: `docker compose pull && docker compose up -d`, then
   `migrate` (details to follow once deployment is set up).

Locally (Apple Silicon) the image is built natively for `arm64`; the server
image is only built in CI.

## Operations

- **Backups:** UpCloud server backups (scheduled snapshots), plus a nightly
  `pg_dump` to local disk before the snapshot so the database is restorable
  consistently. See ADR 0008. Schedule and retention: to be set when the
  server is provisioned.
- **Test phase:** the new site runs on `www2.vrobot.ch` (A record at
  Hostpoint pointing to the UpCloud server). Caddy sends
  `X-Robots-Tag: noindex` there so it is not indexed; optional Basic Auth.
- **Cutover:** the old Hostpoint site stays live until the new site has been
  accepted on `www2.vrobot.ch`. Then switch DNS, redirect old URLs where
  useful, and let `www2` redirect to the main domain (or remove it).

## Scheduled jobs (production)

- daily: `python manage.py delete_old_contact_messages`
- nightly: `pg_dump` before the UpCloud backup (ADR 0008)

## Open questions

- Production hardening: HSTS and HTTP→HTTPS redirect (Caddy vs. Django),
  to be settled with the production setup
- Basic Auth on `www2` during the test phase: yes or no
- Which content to migrate from the old site
