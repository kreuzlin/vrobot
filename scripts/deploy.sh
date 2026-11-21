#!/bin/sh
# Deploy the latest images on the production server (run from the repo
# checkout, e.g. /srv/vrobot); see docs/deployment.md, section 4.
#
#   1. Remember the image of every running container
#      (local tag vrobot-previous:<service>, list in .deploy-previous).
#   2. git pull, pull all images, migrate, start the new containers.
#   3. Check the site through Caddy on this server: /version must report the
#      commit of the web image, the home page must answer.
#   4. If step 2 or 3 fails: start the remembered images again (rollback),
#      record the failed images in .deploy-failed (scripts/auto-update.sh
#      does not retry them) and mail DEPLOY_ALERT_RECIPIENTS.
#
# Environment: IMAGE_TAG=sha-<commit> pins a build (rollback by hand);
# DEPLOY_NO_PULL=1 skips pulling images (deliberate rollback test).
set -eu
# The whole script is one block, so sh has read all of it before
# `git pull` can replace the file.
{
cd "$(dirname "$0")/.."

compose() { docker compose -f compose.prod.yaml "$@"; }
log() { echo "deploy: $*"; }

PREVIOUS=.deploy-previous
FAILED=.deploy-failed
ALERTED=.deploy-alert
CHECK_TRIES=12   # x 5 s
CHECK_DELAY=5

# One deploy at a time: wait for a running one (scripts/auto-update.sh holds
# the lock itself and sets DEPLOY_LOCKED).
if [ -z "${DEPLOY_LOCKED:-}" ]; then
  exec 9>/tmp/vrobot-deploy.lock
  flock 9
fi

# "<service> <image reference>" for every service, as compose resolves it now
# (IMAGE_TAG included).
configured_images() {
  compose config --format json | python3 -c '
import json, sys
for name, service in json.load(sys.stdin)["services"].items():
    if "image" in service:
        print(name, service["image"])
'
}

site_address() {
  compose config --format json | python3 -c '
import json, sys
print(json.load(sys.stdin)["services"]["caddy"]["environment"]["SITE_ADDRESS"])
'
}

image_id() { docker image inspect -f '{{.Id}}' "$1" 2>/dev/null || echo none; }
container_image() {
  c=$(compose ps -q "$1" 2>/dev/null || true)
  if [ -n "$c" ]; then docker inspect -f '{{.Image}}' "$c"; else echo none; fi
}

# Commit baked into the web image (APP_COMMIT, set by CI).
expected_commit() {
  web_ref=$(configured_images | awk '$1 == "web" { print $2 }')
  docker image inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$web_ref" |
    sed -n 's/^APP_COMMIT=//p'
}

live_version() {
  site=$(site_address)
  case $site in
    :*) curl -fsS --max-time 5 "http://127.0.0.1$site/version" ;;
    *) curl -fsS --max-time 5 --resolve "$site:443:127.0.0.1" "https://$site/version" ;;
  esac
}

# The site answers through Caddy, /version shows the expected commit and the
# home page returns 2xx/3xx. Retries for up to CHECK_TRIES x CHECK_DELAY s.
check_site() {
  expected=$(expected_commit)
  site=$(site_address)
  case $site in
    :*) base="http://127.0.0.1$site"; set -- ;;
    *) base="https://$site"; set -- --resolve "$site:443:127.0.0.1" ;;
  esac
  i=0
  while [ "$i" -lt "$CHECK_TRIES" ]; do
    if version=$(curl -fsS --max-time 5 "$@" "$base/version" 2>/dev/null) &&
      echo "$version" | grep -q "\"commit\": \"$expected\"" &&
      curl -fsS -o /dev/null --max-time 10 "$@" "$base/" 2>/dev/null; then
      log "site OK, commit $expected"
      return 0
    fi
    i=$((i + 1))
    sleep "$CHECK_DELAY"
  done
  log "site check FAILED (expected commit $expected, got: ${version:-no answer})"
  return 1
}

# Mail DEPLOY_ALERT_RECIPIENTS once per distinct event (repeated failures of
# the same kind, e.g. every minute from cron, send no further mail until a
# deploy succeeds). $1: subject; body on stdin.
notify() {
  body=$(cat)
  key=$(printf '%s\n%s' "$1" "$(cat "$FAILED" 2>/dev/null || true)" | sha256sum | cut -c1-16)
  if [ "$(cat "$ALERTED" 2>/dev/null || true)" = "$key" ]; then
    log "mail already sent for this failure: $1"
    return 0
  fi
  text=$(printf '%s\n\nServer: %s\nZeit: %s\nLog: journalctl -t vrobot-update (automatisch) oder Ausgabe von scripts/deploy.sh\nAnleitung: docs/deployment.md, Abschnitt 4\n' \
    "$body" "$(hostname)" "$(date '+%Y-%m-%d %H:%M:%S %Z')")
  # The running web container sends it (after a rollback: the old version);
  # fall back to a one-off container of the configured image.
  if printf '%s\n' "$text" | compose exec -T web python manage.py notify_deploy "$1" ||
    printf '%s\n' "$text" | compose run --rm --no-deps -T web python manage.py notify_deploy "$1"; then
    echo "$key" >"$ALERTED"
    log "mail sent: $1"
  else
    log "could not send mail: $1"
  fi
}

# Start the remembered images again for every service whose image changed,
# then check the site. $1: what failed.
rollback() {
  what=$1
  log "$what - rolling back"
  : >"$FAILED.new"
  services=""
  configured_images >"$PREVIOUS.refs"
  while read -r service old_id; do
    ref=$(awk -v s="$service" '$1 == s { print $2 }' "$PREVIOUS.refs")
    [ -n "$ref" ] || continue
    new_id=$(image_id "$ref")
    [ "$new_id" = "$old_id" ] || echo "$ref $new_id" >>"$FAILED.new"
    if [ "$new_id" != "$old_id" ] || [ "$(container_image "$service")" != "$old_id" ]; then
      docker tag "vrobot-previous:$service" "$ref"
      services="$services $service"
    fi
  done <"$PREVIOUS"
  rm -f "$PREVIOUS.refs"
  mv "$FAILED.new" "$FAILED"

  status=0
  if [ -n "$services" ]; then
    log "restarting previous images:$services"
    # shellcheck disable=SC2086
    compose up -d --no-deps --force-recreate $services || status=1
  fi
  if [ "$status" = 0 ] && check_site; then
    notify "Deploy fehlgeschlagen, alte Version wiederhergestellt" <<EOF
Der automatische Deploy ist fehlgeschlagen: $what.

Die vorherige Version läuft wieder (Rollback), die Website ist erreichbar.
Zurückgesetzt:$services
Live: $(live_version 2>/dev/null || echo "?")

Nicht übernommene Images (werden nicht nochmals versucht, erst ein neues
Image aus der CI wird wieder deployt):
$(cat "$FAILED")

Hinweis: Migrationen werden beim Rollback nicht zurückgenommen.
EOF
  else
    notify "DRINGEND: Deploy fehlgeschlagen, Rollback hat nicht geklappt" <<EOF
Der automatische Deploy ist fehlgeschlagen: $what.

Auch der Rollback auf die vorherige Version hat die Website NICHT wieder
erreichbar gemacht. Bitte sofort auf dem Server prüfen:
  cd /srv/vrobot && docker compose -f compose.prod.yaml ps
  docker compose -f compose.prod.yaml logs --tail 100 web caddy

Betroffene Images:
$(cat "$FAILED")
EOF
  fi
  exit 1
}

# 1. Remember what runs now.
: >"$PREVIOUS"
for service in $(compose ps --services --status running); do
  id=$(container_image "$service")
  [ "$id" != none ] || continue
  docker tag "$id" "vrobot-previous:$service"
  echo "$service $id" >>"$PREVIOUS"
done

# 2. Update. Failing before anything was restarted: nothing to roll back.
if ! git pull --ff-only; then
  notify "Deploy fehlgeschlagen: git pull" <<EOF
scripts/deploy.sh konnte den Repo-Stand auf dem Server nicht aktualisieren
(git pull --ff-only). Es wurde nichts verändert, die bisherige Version läuft
weiter. Vermutlich gibt es lokale Änderungen in /srv/vrobot (git status).
EOF
  exit 1
fi
if [ -z "${DEPLOY_NO_PULL:-}" ]; then
  # All images: web (app), caddy (patch releases of the pinned minor tag) and
  # db (PostgreSQL 18.x minor updates; a major upgrade needs dump/restore).
  # A failed pull changes nothing and is usually temporary: log only.
  compose pull || { log "pull failed, nothing changed"; exit 1; }
fi
compose up -d db || rollback "Start der Datenbank fehlgeschlagen"
# Migrations run once, before the new version takes traffic.
compose run --rm web python manage.py migrate --noinput ||
  rollback "Migration fehlgeschlagen"
compose up -d --remove-orphans || rollback "Start der Container fehlgeschlagen"

# 3. Check the site.
check_site || rollback "Website antwortet nach dem Update nicht korrekt"

rm -f "$FAILED" "$ALERTED"
docker image prune -f
compose ps
exit
}
