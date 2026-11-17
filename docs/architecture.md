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

The GearsBot emulator is not integrated, only linked.

## Configuration

- Settings: `config/settings.py`, values read with `django-environ`.
- Python 3.14 (`.python-version`), dependencies in `pyproject.toml` / `uv.lock`.

- All environment-specific values come from environment variables in `.env`
  (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, email credentials …).
- `.env.example` documents every variable.
- A single settings module; dev/prod differences only via environment variables.

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

## Open questions

- Production hardening: HSTS and HTTP→HTTPS redirect (Caddy vs. Django),
  to be settled with the production setup
- Basic Auth on `www2` during the test phase: yes or no
- Which content to migrate from the old site
