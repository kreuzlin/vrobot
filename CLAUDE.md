# CLAUDE.md

Guidelines for working on this repository (vrobot.ch, website of the
Verein Robotik Talente). Applies to Claude Code and human contributors.

## Project context

- Rebuild of the association's website. The old PHP site on Hostpoint stays
  live until the new one is finished. Do not touch the old site or DNS.
- Content site with little interactivity. Content is maintained by association
  members through the Django admin – the admin must be understandable for
  non-technical users (German `verbose_name`s, help texts, sensible list views
  and filters).
- Scope of version 1: see README.md. No features beyond that without asking.

## Stack (binding)

- Django 5.2 LTS with Django templates. No React/SPA, no frontend build step
  unless it becomes necessary.
- Python dependencies only via **uv** (`pyproject.toml`, `uv.lock`).
  No `pip install`, no `requirements.txt`.
- **Ruff** for linting and formatting.
- **PostgreSQL** – also locally, no SQLite.
- **Docker Compose** for development and production.
- Production: UpCloud, Ubuntu 26.04 LTS, Caddy (automatic HTTPS).
- GitHub Actions builds images for `linux/amd64` (development happens on
  Apple Silicon, the server is x86).

Rationale lives in `docs/decisions/`. To deviate, write a new ADR first.

## Language

| What                                                        | Language |
|-------------------------------------------------------------|----------|
| Conversation with the maintainer                            | German   |
| Website content, templates (user-facing text), admin labels, form and error messages | German (Swiss spelling: «ss», never «ß») |
| Documentation (README, CLAUDE.md, docs/, ADRs)              | English  |
| Exception: `docs/editor-guide.md` (for association members) | German   |
| Code: identifiers, comments, docstrings, commit messages    | English  |

- `LANGUAGE_CODE = "de-ch"`, `TIME_ZONE = "Europe/Zurich"`, `USE_TZ = True`.

## Workflow

- **Pull requests.** The default branch is `main`. Never commit or push
  directly to `main`.
  - Each step gets its own branch from an up-to-date `main`, named
    `<type>/<short-description>` (e.g. `feat/events`, `fix/contact-form`,
    `docs/…`, `chore/…`).
  - Push the branch and open a PR against `main` with `gh pr create`; the PR
    description (English) explains what changed and how it was tested.
  - The maintainer reviews and merges the PR. Do not merge PRs yourself
    unless explicitly asked.
  - `main` is protected by a ruleset that only allows **squash merges**. The
    PR title becomes the commit message on `main`, so write it as a good
    commit subject (English, imperative, e.g. "Add events calendar").
  - Once CI exists, a PR is only ready when CI is green.
- **Small steps.** Commit after every working step (tests green, Ruff clean).
  Keep PRs small – one step of the plan per PR.
- Before committing: `uv run ruff check . && uv run ruff format --check .` and
  `docker compose exec web python manage.py test`.
- Tests cover the most important behaviour (e.g. events calendar hides past
  events, contact form incl. spam protection, post visibility, page titles and
  meta descriptions).
- Keep docs in sync: model changes → `docs/data-model.md`, architecture or
  operations changes → `docs/architecture.md`, fundamental decisions → new ADR
  in `docs/decisions/`.

## Secrets

- Secrets only in `.env` (never committed). The repo contains only
  `.env.example` with placeholders and comments.
- Every new environment variable is documented in `.env.example` at the same time.
- No passwords, tokens or personal data in code, tests, fixtures or docs.

## Conventions

- Small, topic-focused Django apps (e.g. `posts`, `events`, `documents`,
  `pages`, `contact`).
- Every public page sets `<title>` and `<meta name="description">`: views use
  `core.seo.SeoMixin` (`page_title`, `meta_description`); the base template
  renders title, description, canonical and Open Graph tags, falling back to
  `SITE_TITLE` / `SITE_DESCRIPTION` from settings.
- Templates extend `base.html`. New sections get a main navigation entry in
  `core/navigation.py`.
- Styles live in `core/static/core/css/site.css` (plain CSS, no framework).
- Rich text fields are Markdown: admin widget `core.widgets.MarkdownEditor`,
  output only via the `|markdown` filter. Never render user content with
  `|safe`.
- Images always have an alt text field; it is required when an image is set.
- Editors are staff users in the group "Redaktion" (never superusers). Its
  permissions are defined in `core/editor_group.py`; a new content model needs
  an entry there plus a data migration calling `sync_editor_group`.
- Admin changes that affect editors are reflected in `docs/editor-guide.md`.
- Uploaded files (images, PDFs) live under `MEDIA_ROOT` on a Docker volume;
  static files are collected during the image build.
- Time logic (e.g. "past events") uses `django.utils.timezone.now()`, never
  naive datetimes.

## Useful commands

```bash
docker compose up --build                            # dev environment
docker compose exec web python manage.py <command>   # manage.py inside Docker
docker compose exec web python manage.py test
uv run ruff check . --fix
uv run ruff format .
```

- Inside the container use `python manage.py`, not `uv run` (the venv is
  at `/opt/venv` and on `PATH`; `uv run` would try to sync dev dependencies).
- `compose.yaml` is the development setup; production gets its own Compose
  file with Caddy and the GHCR image.
