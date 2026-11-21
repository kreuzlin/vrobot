#!/bin/sh
# Deploy automatically when a newer image is available (ADR 0012). Run from
# cron on the production server, see docs/deployment.md:
#   scripts/auto-update.sh web   # every 5 minutes: new app image from CI
#   scripts/auto-update.sh       # daily: also caddy and postgres
# Pulls the given services (default: all), then runs scripts/deploy.sh if a
# container is missing or runs an image other than the one its tag points to
# now. Prints nothing when everything is up to date.
set -eu
# The whole script is one block, so sh has read all of it before
# `git pull` in deploy.sh can replace the file.
{
cd "$(dirname "$0")/.."

compose() { docker compose -f compose.prod.yaml "$@"; }

# Skip this run while a deploy is in progress; deploy.sh uses the same lock.
exec 9>/tmp/vrobot-deploy.lock
flock -n 9 || exit 0

# Pull output only on errors, so cron logs stay empty when nothing changed.
if ! out=$(compose pull --quiet "$@" 2>&1); then
  echo "auto-update: pull failed: $out" >&2
  exit 1
fi

reason=""
running=$(compose ps --status running --services)
for service in $(compose config --services); do
  echo "$running" | grep -qx "$service" || reason="$reason $service:not-running"
done
# Compare each container's image with the one its tag points to now. The tag
# comes from the container itself (`compose ps` shows an ID once the tag has
# moved on).
for container in $(compose ps -q); do
  read -r ref current <<EOF
$(docker inspect -f '{{.Config.Image}} {{.Image}}' "$container")
EOF
  [ "$(docker image inspect -f '{{.Id}}' "$ref")" = "$current" ] ||
    reason="$reason $ref:new-image"
done

[ -n "$reason" ] || exit 0

echo "auto-update: deploying ($reason )"
if DEPLOY_LOCKED=1 scripts/deploy.sh; then
  echo "auto-update: done, commit $(compose exec -T web printenv APP_COMMIT)"
else
  echo "auto-update: deploy FAILED" >&2
  exit 1
fi
exit
}
