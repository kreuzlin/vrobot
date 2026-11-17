# vrobot.ch

[![CI](https://github.com/kreuzlin/vrobot/actions/workflows/ci.yml/badge.svg)](https://github.com/kreuzlin/vrobot/actions/workflows/ci.yml)

Rebuild of the website of the **Verein Robotik Talente (VRoboT)**.

The current PHP site on Hostpoint stays live until the new site is finished
and DNS is switched over.

## Stack

| Area          | Choice                                                   |
|---------------|----------------------------------------------------------|
| Framework     | Django 5.2 LTS, Django templates (no SPA)                |
| Language      | Python 3.14, dependencies managed with [uv](https://docs.astral.sh/uv/) |
| Lint/format   | Ruff                                                     |
| Database      | PostgreSQL                                               |
| Runtime       | Docker Compose (local and on the server)                 |
| Web server    | Caddy (reverse proxy, automatic HTTPS)                   |
| Hosting       | UpCloud, Ubuntu 26.04 LTS, x86_64                        |
| CI/CD         | GitHub Actions builds `linux/amd64` images               |

Rationale: see [`docs/decisions/`](docs/decisions/).

## Scope (version 1)

- Posts (title, text, image, author, date)
- Events calendar – past events are hidden automatically
- Documents (statutes, forms, annual reports) with category and year
- Static pages: About us, Get involved, Contact (form with spam protection)
- Link to the existing GearsBot emulator
- All content maintained through the Django admin
- Proper page titles and meta descriptions
- Website language: German

## Local development

Requirements: Docker (with the buildx plugin) and [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env          # set SECRET_KEY and passwords, never commit .env
docker compose up --build     # start web + PostgreSQL, migrations run automatically
docker compose exec web python manage.py createsuperuser
```

Site: <http://localhost:8000> · Admin: <http://localhost:8000/admin/>

The project directory is mounted into the container, so code changes reload
automatically. After changing dependencies (`uv add …`), rebuild with
`docker compose up --build`.

Common tasks:

```bash
docker compose exec web python manage.py test        # tests (inside Docker)
docker compose exec web python manage.py makemigrations
uv run ruff check . --fix && uv run ruff format .    # lint/format (on the host)
docker compose down                                  # stop (data is kept)
docker compose down -v                               # stop and delete the database
```

Inside the container the virtualenv is on `PATH`, so use `python manage.py …`
directly (not `uv run`).

## Documentation

- [`CLAUDE.md`](CLAUDE.md) – working rules for Claude Code (and humans)
- [`docs/architecture.md`](docs/architecture.md) – structure, deployment, operations
- [`docs/deployment.md`](docs/deployment.md) – server setup, deployments, backups
- [`docs/data-model.md`](docs/data-model.md) – data model
- [`docs/decisions/`](docs/decisions/) – Architecture Decision Records (ADRs)
- [`docs/editor-guide.md`](docs/editor-guide.md) – guide for editors (German)
