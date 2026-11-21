#!/bin/sh
# Deploy the latest image on the production server (run from the repo
# checkout, e.g. /srv/vrobot). Optional: IMAGE_TAG=sha-<commit> to pin a build.
set -eu
# The whole script is one block, so sh has read all of it before
# `git pull` in deploy.sh can replace the file.
{
cd "$(dirname "$0")/.."

compose() { docker compose -f compose.prod.yaml "$@"; }

# One deploy at a time: wait for a running one (scripts/auto-update.sh holds
# the lock itself and sets DEPLOY_LOCKED).
if [ -z "${DEPLOY_LOCKED:-}" ]; then
  exec 9>/tmp/vrobot-deploy.lock
  flock 9
fi

git pull --ff-only
# All images: web (app), caddy (patch releases of the pinned minor tag) and
# db (PostgreSQL 18.x minor updates; a major upgrade needs dump/restore).
compose pull
compose up -d db
# Migrations run once, before the new version takes traffic.
compose run --rm web python manage.py migrate --noinput
compose up -d --remove-orphans
docker image prune -f
compose ps
exit
}
