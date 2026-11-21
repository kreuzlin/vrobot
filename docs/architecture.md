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

The GearsBot emulator is not integrated, only linked (`GEARSBOT_URL`). The
old site hosted its own copy under `/python/public/`; we link the official
instance instead (maintainer decision), and the old path will redirect there.

The RoboChallenge (robotics competition in Trimmis, co-organised by VRoboT)
has its own website; we link it (`ROBOCHALLENGE_URL`) in the main navigation,
the footer and a red teaser on the home page. The teaser has no dates so it
does not go stale; current dates go into posts and events.

Checkermint (platform for tasks, feedback and points used in the trainings)
is linked the same way (`CHECKERMINT_URL`) in the main navigation and the
footer, without a home page teaser.

### `core` in detail

- `base.html`: layout, header with main navigation, footer, SEO tags
- `seo.py`: `SeoMixin` and `build_title()` (`"<page> – VRoboT"`, home page:
  `"VRoboT – Verein Robotik Talente"`)
- `navigation.py`: main navigation entries; `context_processors.site` resolves
  them and marks the current page
- `/version`: JSON with the git commit of the running image (`APP_COMMIT`,
  set by CI as build arg), used to compare the live site with `main`
- German `404.html`; standalone `500.html` without template logic
- `markdown.py`: `render_markdown()` (Markdown → HTML, sanitised with `nh3`
  allowlist; `# ` headings become `<h2>`), template filter `|markdown`
- `widgets.py`: `MarkdownEditor` admin widget using EasyMDE, vendored under
  `core/static/core/vendor/easymde/` (v2.21.0, MIT) with German text buttons,
  so the admin loads no external resources. Its preview is rendered by the
  server (`POST /admin/markdown-preview/`, staff only, CSRF-protected) with
  the same `render_markdown()` and styled with the shared `prose.css`, so it
  looks like the published page

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

### Design

- Colours from the logo (see `site.css` header and CLAUDE.md), system font
  stack (no web fonts, no external requests).
- Header: logo symbol + "VRoboT / Verein Robotik Talente"; the logo links to
  the home page (no "Start" menu entry). Below 68rem (the width where logo
  and all menu items still fit on one line) the navigation collapses behind a
  "Menü" button (`core/static/core/js/site.js`); without JavaScript it stays
  visible. Below 52rem the logo and brand text get smaller.
- Recurring elements taken from the logo: red slanted tab before section
  titles, grey "circuit line" with red end above the footer.
- Logo: only a raster source exists (`design/vrobot_logo.png`, no SVG).
  `scripts/build_logo_assets.py` derives cropped, transparent, palette-reduced
  PNGs (full logo 480/960 px, symbol for the header) and favicons.
  `design/` and `scripts/` are excluded from the Docker image.

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
- `compose.prod.yaml` (production): `db`, `web` (GHCR image, Gunicorn, not
  published) and `caddy` (ports 80/443, config `deploy/Caddyfile`).
  Volumes: `postgres_data`, `media` (shared read-only with Caddy),
  `caddy_data` (certificates), `caddy_config`.
- Static files: served by Django via **WhiteNoise** (hashed file names,
  pre-compressed, cached for a year), so they ship with the image and need no
  shared volume. Tests use plain storage because the manifest only exists
  after `collectstatic`.
- Media files: served by Caddy directly from the `media` volume (`/media/`).

## Build and deployment

1. GitHub Actions (`.github/workflows/ci.yml`):
   - every pull request and push to `main`: Ruff (lint + format), `manage.py
     check`, `makemigrations --check`, tests against PostgreSQL 18, then a
     `linux/amd64` image build (PRs: build only, to verify the Dockerfile);
   - push to `main` (i.e. after a merge): the image is pushed to GHCR as
     `ghcr.io/kreuzlin/vrobot:sha-<commit>` and `:latest`;
   - weekly schedule (Mondays 03:30 UTC) and manual runs on `main`: same
     pipeline, rebuilt with a freshly pulled base image so base image
     security fixes reach `latest` between merges;
   - concurrency: a new push to a PR cancels its running check; runs on
     `main` are queued instead, so `latest` is pushed in merge order and each
     merge gets its `sha-<commit>` image (except a pending run replaced by a
     newer one when three or more merges happen within minutes).
2. On the server: `scripts/auto-update.sh` (cron, every 5 minutes for `web`,
   daily for all images) runs `scripts/deploy.sh` when a newer image is
   available (ADR 0012). `deploy.sh` pulls the repo and all images (`web`,
   `caddy`, `db`), runs `migrate`, then restarts the containers. Rollback:
   `IMAGE_TAG=sha-<commit>`.
   Step by step: [`deployment.md`](deployment.md).

Locally (Apple Silicon) the image is built natively for `arm64`; the server
image is only built in CI.

Dependency updates: Dependabot (`.github/dependabot.yml`) opens weekly PRs
for Python packages (uv, minor/patch grouped; Django stays on 5.2 LTS),
GitHub Actions, the Dockerfile base images and the Compose images (no
PostgreSQL major upgrades). Security updates and secret scanning with push
protection are enabled in the repository settings. The PRs are reviewed and
merged like any other.

## Operations

- **Backups:** UpCloud server backups (scheduled snapshots), plus a nightly
  `pg_dump` to local disk before the snapshot so the database is restorable
  consistently. See ADR 0008. Schedule and retention: to be set when the
  server is provisioned.
- **Test phase:** the new site runs on `www2.vrobot.ch` (A record at
  Hostpoint pointing to the UpCloud server). Caddy sends
  `X-Robots-Tag: noindex` there so it is not indexed. No Basic Auth (decided
  by the maintainer); the snippet mechanism in `deploy/caddy.d/` stays
  available if that changes.
- **Cutover:** main address `https://vrobot.ch`; `www` and `www2` redirect
  there (Caddy). Old PHP URLs (`about.php`, `engage.php`, `agenda.php`,
  `contact.php`, `index.php`, `post.php?ID=…`, `attachments/…`,
  `python/public/…`) redirect to the new pages (`core/legacy.py`). Caddy sends
  HSTS for one year (no `includeSubDomains`, so mail hosts are unaffected).
  Steps: `docs/deployment.md`, "Go-live".

## Scheduled jobs (production)

- daily: `python manage.py delete_old_contact_messages`
- nightly: `scripts/backup-db.sh` (`pg_dump`, custom format, kept 14 days in
  `backups/`) before the UpCloud backup (ADR 0008)
- every 5 minutes / daily: `scripts/auto-update.sh` (automatic deploy,
  ADR 0012); log in syslog (`journalctl -t vrobot-update`)
- host: `unattended-upgrades`, automatic reboot at 05:00 when required

Crontab: see [`deployment.md`](deployment.md).

## Content migration from the old site

`python manage.py import_old_site` (one-time, idempotent) takes over the
content of the old PHP site: texts of "Über uns", "Mitmachen" and "Kontakt"
(spelling fixes only), the single post (2020) and the documents (statutes,
membership form, annual reports), downloaded from `vrobot.ch/attachments/`.
Pages are only overwritten while they still hold the placeholder text
(`--force` overrides); `--dry-run` saves nothing.

The six topics of "Mitmachen" with their images are fixed in the template
(maintainer decision): `pages/topics.py`, images in
`pages/static/pages/img/topics/` (700×400 JPEG, from the old site). The
editable page text is shown above them (`pages.views.JoinView`).

The old site's header photos are fixed design images too:
`core/static/core/img/banners/` – the home page photo (`home-*.jpg`, 3:2) and a
decorative title image per fixed page and the agenda (`<slug>-{800,1600}.jpg`,
16:9, cropped to 3:1 by CSS; `core/_banner.html`). The post "Die Welt braucht
Arduino" gets its old header photo as post image (scaled to 1600 px).

Not migrated (maintainer decisions): the self-hosted GearsBot copy (official
instance is linked), the Twitter link, the outdated orange payment slip
(`EZS_VRoboT.jpg`, invalid since 2022). The old agenda was empty.

## Open questions

None at the moment.
