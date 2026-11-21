# 0012: Automatic deployment on the server

- Status: accepted
- Date: 2026-11-21

## Context

Until now every merge needed a manual `scripts/deploy.sh` on the server, and
security fixes in the container images (Python base image, `caddy:2.10`,
`postgres:18`) only arrived when someone remembered to deploy (#32). The
association has one maintainer; manual routines get forgotten.

Options:

1. **Push from GitHub Actions** via SSH after the image build. Needs an SSH
   key with Docker access (root-equivalent) stored as a GitHub secret.
2. **Watchtower** or a similar container with the Docker socket. Updates
   containers but knows nothing about migrations or the git checkout.
3. **Polling on the server**: a cron job pulls the images and runs the
   normal `scripts/deploy.sh` when one changed.

## Decision

Option 3. `scripts/auto-update.sh` runs from the `deploy` user's crontab:

- every 5 minutes for `web` (GHCR, no pull rate limit): a merge is live
  within minutes after CI pushed its image;
- daily for all services, so Caddy patch releases and PostgreSQL 18.x minor
  updates follow (Docker Hub's anonymous pull limit rules out polling those
  every few minutes).

CI rebuilds `main` weekly with a fresh base image (#32), so base image fixes
reach the server through the same path. The host itself reboots
automatically after kernel updates (`unattended-upgrades`, 05:00).

## Consequences

- No credentials for the server outside the server; GitHub cannot reach it.
- Every merge to `main` goes live without a manual step, including
  docs-only merges (`web` restarts for a few seconds). `main` must always be
  deployable; this is already enforced by the required CI checks.
- A failing deploy (e.g. a migration error) leaves the previous containers
  running and is retried every 5 minutes. Output goes to syslog
  (`journalctl -t vrobot-update`); there is no alert yet – uptime monitoring
  is tracked in #33.
- Pinning `IMAGE_TAG=sha-<commit>` in `.env` (rollback) stops automatic app
  updates until it is set back to `latest`.
- New minor or major versions (Caddy 2.11, PostgreSQL 19, Python 3.15) are
  still deliberate changes via pull request.
