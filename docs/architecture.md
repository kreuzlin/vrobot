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
| `contact`   | Contact form with spam protection, email delivery     |

The GearsBot emulator is not integrated, only linked.

## Configuration

- All environment-specific values come from environment variables in `.env`
  (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, email credentials …).
- `.env.example` documents every variable.
- A single settings module; dev/prod differences only via environment variables.

## Build and deployment

1. Push to `master` → GitHub Actions: Ruff, tests, then build the Docker image
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
- **Cutover:** the old Hostpoint site stays live until the new site has been
  accepted on a test domain. Then switch DNS and redirect old URLs where
  useful.

## Open questions

- Domain/subdomain for the test phase
- Email delivery for the contact form (Hostpoint SMTP or a service)
- Which content to migrate from the old site
