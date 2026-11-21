# Project status

Current state of vrobot.ch and the next steps. **Every PR updates this file**
(at least "Last updated" and whatever the PR changes). Details live in the
linked docs; open work lives in GitHub issues.

_Last updated: 2026-11-21 (PR "Add Dependabot for dependency updates")_

## Live

- **https://vrobot.ch** – live on the new server since **2026-11-18**.
  `www.vrobot.ch` and `www2.vrobot.ch` redirect there (301); URLs of the old
  PHP site redirect to the new pages (`core/legacy.py`).
- Deployed commit: `curl -s https://vrobot.ch/version`, compare with
  `git rev-parse origin/main`. Last manual deploy: `15f67fb` (2026-11-18).
  From this PR on, deploys are automatic (ADR 0012): every merge is live
  within about 5 minutes after CI pushed its image, docs-only merges too.
- Search engines: indexing allowed (`ROBOTS_TAG=all`), HSTS one year.

## Infrastructure

| What | Where |
|---|---|
| Server | UpCloud, Ubuntu 26.04, `212.147.228.149` / `2a04:3542:1000:910:9010:e8ff:fe50:1f67`, time zone Europe/Zurich |
| Access | `ssh deploy@212.147.228.149` (key only, no root login, passwordless sudo) |
| App | `/srv/vrobot` (git checkout), `compose.prod.yaml`: `db` (PostgreSQL 18), `web` (GHCR image, Gunicorn), `caddy` (HTTPS) |
| Secrets | `/srv/vrobot/.env` on the server only |
| Deploy | Automatic: cron `scripts/auto-update.sh` (every 5 min for `web`, daily for all images) runs `scripts/deploy.sh`; log `journalctl -t vrobot-update` |
| Backups | cron 02:00 `scripts/backup-db.sh` (14 days in `backups/`), UpCloud backup daily 02:15 UTC |
| Cron | 02:00 backup, 03:00 `delete_old_contact_messages`, every 5 min / 05:30 `auto-update.sh` |
| Mail | Hostpoint SMTP, sender `mail@vrobot.ch`; contact form recipient set in the server `.env` |
| DNS | Hostpoint (`vrobot.ch`, `www`, `www2` → server; MX and mail records unchanged) |
| Hostpoint web hosting | Kept for other purposes – not used by the website, do not cancel (#25 closed) |
| CI | GitHub Actions: lint + tests, `linux/amd64` image to `ghcr.io/kreuzlin/vrobot` (`latest`, `sha-<commit>`) on `main`; runs on `main` are queued, never cancelled; weekly rebuild Mondays 03:30 UTC with a fresh base image |
| Updates | App image rebuilt weekly by CI and deployed automatically; `caddy:2.10` / `postgres:18` patches pulled daily; host: `unattended-upgrades` with reboot at 05:00 when needed |
| Dependencies | Dependabot: weekly PRs (uv, GitHub Actions, Dockerfile, Compose images); security updates, secret scanning and push protection enabled |

Runbook: [`deployment.md`](deployment.md). Architecture:
[`architecture.md`](architecture.md). Decisions: [`decisions/`](decisions/).

## Done (version 1)

- Django 5.2 site with posts, events (past ones hidden, grouped by month),
  documents, fixed pages (Über uns, Mitmachen, Kontakt), contact form with
  spam protection and email, links to GearsBot and the RoboChallenge.
- Design from the logo (colours, header, mobile menu, footer), images from the
  old site (home photo, page banners, "Mitmachen" topics).
- Admin for non-technical editors: group "Redaktion", Markdown editor with a
  preview like the website, password reset, editor guide
  ([`editor-guide.md`](editor-guide.md), German).
- Content of the old site imported (`manage.py import_old_site`), plus
  annual reports 2023 and 2024.
- Events on the live site: weekly trainings (Fridays 18:00–19:00, Quader
  Schulhaus, Zimmer 203) until 23.06.2028 following the Chur school holiday
  plan; RoboChallenge 2027 (20.03.2027, Trimmis). Post "RoboChallenge 2027 in
  Trimmis – jetzt anmelden" published.

## Open issues

Overview: `gh issue list`. At the time of writing:

| # | Topic | Who |
|---|---|---|
| #27 | Mail deliverability: DKIM, then DMARC | maintainer / Marc (DNS) |
| #28 | Trainings for school year 2028/29 when the holiday plan is out | content |
| #29 | Complete and check content ("Mitglied werden", document years, …) | association |
| #30 | Check usage rights of images taken over from the old site | association |
| #31 | Editor accounts for association members | maintainer |
| #33 | Uptime monitoring, Google Search Console | ops |

## Next steps

1. After merging #32's PR, on the server: deploy once by hand, install the
   new crontab lines and the reboot setting (`deployment.md` sections 1 and
   5), then check that the next merge goes live by itself.
2. Content issues (#29, #30, #31) with the association.
3. #33 (uptime monitoring, Search Console), #27 (DKIM/DMARC).

## Working agreements (summary)

- Conversation with the maintainer in German; docs and code in English; site
  content German (Swiss spelling). See CLAUDE.md.
- Every change via branch + PR; the maintainer merges, or Claude merges with
  `gh pr merge <N> --squash --auto` when explicitly asked, then verifies with
  `gh pr view`. Never pipe `gh` output.
- Content on the live site (posts, events, documents) lives only in the
  production database, not in git; local data is a playground.
