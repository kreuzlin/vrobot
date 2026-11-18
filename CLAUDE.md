# CLAUDE.md

Guidelines for working on this repository (vrobot.ch, website of the
Verein Robotik Talente). Applies to Claude Code and human contributors.

## Session start

Every new session first works out the current state itself – the
conversation history of earlier sessions is not available. Run `/start`
(`.claude/commands/start.md`) or do the same by hand:

1. `git status --short` (uncommitted changes? ask before switching), then
   `git switch main && git pull`.
2. Read `docs/STATUS.md` – current state, infrastructure, open issues, next
   steps.
3. `git log --oneline -15`
4. `gh pr list --state open`
5. `gh issue list --state open`
6. `gh run list --limit 10` (failed or cancelled runs on `main`?)
7. Live version: `curl -s https://vrobot.ch/version` and compare with
   `git rev-parse origin/main`.

Report the result to the maintainer in German before starting new work.

## Project context

- Rebuild of the association's website, **live on https://vrobot.ch since
  2026-11-18** (UpCloud server, see `docs/STATUS.md`). The old PHP site is no
  longer served; the Hostpoint web hosting itself stays (used for other
  purposes – do not touch or cancel it). DNS and mail stay at Hostpoint; DNS
  changes are done by the maintainer.
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
  - `main` is protected by the ruleset "protect main" that only allows
    **squash merges**. The PR title becomes the commit message on `main`, so
    write it as a good commit subject (English, imperative, e.g. "Add events
    calendar").
  - The ruleset also requires the CI checks "Lint and test" and
    "Build image (linux/amd64)" to pass before a PR can be merged. If a job
    is renamed in `.github/workflows/ci.yml`, update the ruleset as well.
  - Repository settings: **auto-merge is allowed** and **head branches are
    deleted automatically** after the merge.
- **Merging (only when asked):**
  - Use `gh pr merge <N> --squash --auto`. With green checks GitHub merges
    right away; otherwise the PR is queued and merges once the checks pass.
  - Then check the result with
    `gh pr view <N> --json state,mergedAt,autoMergeRequest` **before**
    waiting for CI or deploying: `state` is `MERGED`, or `autoMergeRequest`
    is set (queued). Anything else means the merge did not happen – report
    it, do not wait.
  - If the PR is already merged, say so and skip the merge command.
- **Do not pipe `gh` output** through `tail`, `head`, `grep` or similar, and
  do not hide its stderr: errors and hints from `gh` must stay visible.
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
- **Every PR updates `docs/STATUS.md`**: at least "Last updated", plus what
  the PR changes (state, open issues, next steps). Work done directly on the
  server (content, `.env`, deploys) is recorded there too, in the next PR.
- Open work is tracked as GitHub issues (labels `ops`, `content`, `bug`,
  `enhancement`); reference them in PRs (`Fixes #N`).
- After a merge that changes the app, deploy on the server
  (`scripts/deploy.sh`, see `docs/deployment.md`) once CI has pushed the image
  for the merge commit, and check `https://vrobot.ch/version`.

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
  Rich text styles (`.prose`) live in `prose.css`, which the admin editor
  preview loads too – keep it self-contained (no dependency on `site.css`).
  Colours from the logo as CSS variables: black `#1A1A1A` (text), red
  `#E2000A` (accents only), grey `#939CA4` (lines/decoration only – too light
  for text; use `--text-muted` instead). Errors must not rely on red alone.
- Logo assets in `core/static/core/img/` are generated from
  `design/vrobot_logo.png` by `scripts/build_logo_assets.py`; do not edit them
  by hand.
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
- `compose.yaml` is the development setup; `compose.prod.yaml` is production
  (Caddy + GHCR image, see `docs/deployment.md`).
