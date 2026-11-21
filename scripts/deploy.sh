#!/bin/sh
# Deploy the latest image on the production server (run from the repo
# checkout, e.g. /srv/vrobot). Optional: IMAGE_TAG=sha-<commit> to pin a build.
set -eu
cd "$(dirname "$0")/.."

compose() { docker compose -f compose.prod.yaml "$@"; }

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
