# vrobot.ch

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

> These commands apply once the Django skeleton is in place.

```bash
cp .env.example .env          # adjust values, never commit .env
docker compose up --build     # start web + PostgreSQL
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py createsuperuser
```

Site: <http://localhost:8000> · Admin: <http://localhost:8000/admin/>

Without Docker (Django on the host, PostgreSQL still required):

```bash
uv sync                       # create .venv from uv.lock
# set DATABASE_URL in .env to a reachable PostgreSQL, e.g. localhost
uv run python manage.py runserver
```

Quality checks:

```bash
uv run ruff check .
uv run ruff format .
uv run python manage.py test
```

## Documentation

- [`CLAUDE.md`](CLAUDE.md) – working rules for Claude Code (and humans)
- [`docs/architecture.md`](docs/architecture.md) – structure, deployment, operations
- [`docs/data-model.md`](docs/data-model.md) – data model
- [`docs/decisions/`](docs/decisions/) – Architecture Decision Records (ADRs)
