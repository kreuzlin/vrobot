# 0013: Stay on Python 3.14 until the Django LTS supports 3.15

- Status: accepted
- Date: 2026-11-21

## Context

Dependabot proposed `python:3.14-slim` → `python:3.15-slim` (#39). The
project is bound to the Django 5.2 LTS (CLAUDE.md, ADR 0002).

Checked on 2026-11-21 (PyPI trove classifiers, latest releases):

| Package | Version | Python 3.15 declared |
|---|---|---|
| Django | 5.2.19 (latest 5.2.x) | **no** (3.10–3.14); only Django 6.1 declares 3.15 |
| gunicorn | 27.0.1 | no (up to 3.13; runs fine on 3.14) |
| whitenoise | 6.12.0 | no (up to 3.14) |
| django-environ | 0.14.0 | no (up to 3.14) |
| Pillow, psycopg, Markdown | 13.0.0, 3.3.9, 3.11.3 | yes |
| nh3 | 0.3.8 | no classifiers (version-independent wheels) |

In a locally built 3.15 image, `manage.py check` and all tests passed. But
Django does not test 5.2 against 3.15, so fixes for 3.15 problems are not
guaranteed.

Python 3.14 gets bugfix releases until about October 2027 and security
fixes until October 2030 (PEP 745), so there is no pressure to move.

## Decision

- Production stays on **Python 3.14** (`python:3.14-slim`).
- We switch to 3.15 when the Django LTS we use officially supports it:
  either a Django 5.2.x release adds 3.15, or we move to the next LTS
  (Django 6.2, expected April 2027; that move needs its own ADR). At the
  latest we decide before 3.14 leaves bugfix support (autumn 2027).
- Before switching, the other dependencies are checked again (gunicorn,
  whitenoise, django-environ) and the tests run in a 3.15 image. Steps:
  issue #42.
- Dependabot ignores Python minor and major updates of the base image
  (`.github/dependabot.yml`). The ignore rule is removed together with the
  switch.

## Consequences

- No Python upgrade PRs until we lift the ignore rule; checking the
  condition above is a manual task (#42).
- Python 3.14 patch releases and Debian security updates still arrive: the
  floating tag `3.14-slim` is pulled on every image build, including the
  weekly scheduled rebuild (#32), and deployed automatically (ADR 0012).
  Dependabot would not report them anyway, because the tag has no patch
  version.
- Dependabot security updates cover Python packages (uv), not the base
  image; base image fixes rely on the weekly rebuild.
