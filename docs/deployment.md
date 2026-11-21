# Deployment and operations

How the production server runs vrobot.ch. Architecture and rationale:
[`architecture.md`](architecture.md), ADRs 0005–0008.

## Overview

- UpCloud server, Ubuntu 26.04 LTS, Docker Engine with the Compose plugin.
- Repo checkout in `/srv/vrobot` (public repo, no credentials needed). It
  provides `compose.prod.yaml`, `deploy/Caddyfile` and the scripts; the app
  itself comes as an image from GHCR.
- `.env` in `/srv/vrobot` holds all secrets (mode `600`, never committed).
- Containers: `db` (PostgreSQL 18), `web` (Gunicorn), `caddy` (HTTPS).

## 1. Server setup (once)

As root on a fresh server:

```bash
# Updates, automatic security updates (enabled by default once installed)
apt update && apt upgrade -y
apt install -y ufw unattended-upgrades git ca-certificates curl
# reboot if /var/run/reboot-required exists

# Reboot automatically at 05:00 when an update requires it (kernel, libc)
cat > /etc/apt/apt.conf.d/52unattended-upgrades-local <<'EOF'
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "05:00";
EOF

# Swap as a safety net (the server has ~2 GB RAM)
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo "/swapfile none swap sw 0 0" >> /etc/fstab
echo "vm.swappiness=10" > /etc/sysctl.d/99-swappiness.conf && sysctl -p /etc/sysctl.d/99-swappiness.conf

# Firewall
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw allow 443/udp
ufw enable

# Admin user with SSH key login (copies root's authorized_keys).
# No password, so sudo without password – the docker group is
# root-equivalent anyway.
adduser --disabled-password --gecos "" deploy
usermod -aG sudo deploy
echo "deploy ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/deploy && chmod 440 /etc/sudoers.d/deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

Docker publishes ports past `ufw`; only Caddy publishes ports (80/443), so
this is fine – never publish the database or `web`.

SSH hardening: first check that `ssh deploy@<server>` and `sudo -n true`
work in a second session. Then create
`/etc/ssh/sshd_config.d/00-hardening.conf` (the `00-` prefix matters: sshd
uses the first value it reads, and `50-cloud-init.conf` may enable
passwords), run `sshd -t && systemctl reload ssh` and verify with `sshd -T`:

```
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
```

From now on log in as `deploy`. Install Docker Engine from Docker's apt
repository (docs.docker.com, "Install Docker Engine on Ubuntu"), then
`usermod -aG docker deploy` and limit container log size in
`/etc/docker/daemon.json`, then `systemctl restart docker`:

```json
{
  "log-driver": "json-file",
  "log-opts": {"max-size": "10m", "max-file": "5"}
}
```

## 2. DNS

At Hostpoint: an `A` record for `www2.vrobot.ch` pointing to the server
(`212.147.228.149`). Do not change any other records (the old site stays
live). The zone has a wildcard `*` record (A and AAAA) pointing to Hostpoint;
an explicit `www2` record takes precedence over it, so no `AAAA` record must
exist for `www2` (the server has no IPv6 configured). Caddy can only obtain
the certificate once this record resolves. Hostpoint published the change
within minutes.

## 3. First deployment

As `deploy`:

```bash
sudo mkdir -p /srv/vrobot && sudo chown deploy:deploy /srv/vrobot
git clone https://github.com/kreuzlin/vrobot.git /srv/vrobot
cd /srv/vrobot
cp .env.example .env && chmod 600 .env
```

Edit `.env` for production:

| Variable | Value |
|---|---|
| `SECRET_KEY` | new random key (see comment in `.env.example`) |
| `DEBUG` | `false` |
| `ALLOWED_HOSTS` | `www2.vrobot.ch` |
| `CSRF_TRUSTED_ORIGINS` | `https://www2.vrobot.ch` |
| `SITE_ADDRESS` | `www2.vrobot.ch` |
| `ROBOTS_TAG` | `noindex, nofollow` (test phase) |
| `POSTGRES_PASSWORD` | new random password, same in `DATABASE_URL` |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_SSL` | `asmtp.mail.hostpoint.ch`, `465`, `true` |
| `EMAIL_HOST_USER` | the website's own mailbox, e.g. `mail@vrobot.ch` |
| `EMAIL_HOST_PASSWORD` | its password, in single quotes (see below) |
| `DEFAULT_FROM_EMAIL` | `VRoboT <mail@vrobot.ch>` |
| `CONTACT_RECIPIENTS` | addresses for contact form messages |

Secrets are entered on the server by the maintainer, never passed through
chat, tickets or the repo. Put passwords in **single quotes**
(`EMAIL_HOST_PASSWORD='...'`): Docker Compose interpolates `$` in unquoted
values. A password can be written without echoing it, e.g. with
`read -rsp "Passwort: " PW` and a small script that updates `.env`.

**Before DNS points to the server**, test over plain HTTP on the IP: set
`SITE_ADDRESS=:80` and add the IP to `ALLOWED_HOSTS`. Do not set the domain
earlier – Caddy would keep failing the ACME challenge and can hit Let's
Encrypt's rate limit for failed validations. Once the Hostpoint name servers
answer with the new IP (check with `dig +short www2.vrobot.ch A
@ns.hostpoint.ch`, which bypasses local caches), set
`SITE_ADDRESS=www2.vrobot.ch`, remove the IP from `ALLOWED_HOSTS` and
recreate the containers (see "Changing `.env`"). Caddy obtains the
certificate within seconds.

Then:

```bash
scripts/deploy.sh
docker compose -f compose.prod.yaml exec web python manage.py createsuperuser
# Content of the old site (one-time; try --dry-run first)
docker compose -f compose.prod.yaml exec web python manage.py import_old_site
```

Check `https://www2.vrobot.ch/`, log in to `/admin/`, send a test message via
the contact form. Test email sending directly:

```bash
docker compose -f compose.prod.yaml exec -T web python manage.py sendtestemail <address>
```

### Changing `.env`

`docker compose up -d` does not notice changes inside `.env`. Recreate the
affected containers:

```bash
docker compose -f compose.prod.yaml up -d --force-recreate web    # Django settings
docker compose -f compose.prod.yaml up -d --force-recreate caddy  # SITE_ADDRESS, ROBOTS_TAG
```

## 4. Deploying updates

Deploys are **automatic** (ADR 0012): after a merge, CI pushes a new image
(`latest` and `sha-<commit>`), and within a minute the cron job
`scripts/auto-update.sh web` (section 5) notices it and runs
`scripts/deploy.sh`. Check that the site runs the new commit:

```bash
curl -s https://vrobot.ch/version   # {"commit": "<sha>", "short": "<sha7>"}
```

The commit is baked into the image by CI (`GIT_COMMIT` build arg →
`APP_COMMIT`); locally built images report `dev`.

`scripts/deploy.sh` pulls the repo and all images (`web`, `caddy`, `db`),
runs migrations, restarts the containers whose image changed and removes old
images. It can still be run by hand (`cd /srv/vrobot && scripts/deploy.sh`),
e.g. after changing `.env`; a lock makes sure only one deploy runs at a time.

Log of the automatic deploys (silent when nothing changed):

```bash
journalctl -t vrobot-update --since "1 week ago"
```

A failing deploy (e.g. a migration error) leaves the previous containers
running and is retried every minute – check the log if `/version` does not
show the merged commit after 5 minutes.

**Rollback** to an earlier build: set `IMAGE_TAG=sha-<commit>` in `.env` and
run `scripts/deploy.sh` (migrations are not rolled back automatically). While
the tag is pinned, automatic app updates stop; set it back to `latest`
afterwards.

### Keeping images and the host up to date

- **App image** (`python:3.14-slim` base): CI rebuilds `main` every Monday
  03:30 UTC with a freshly pulled base image and pushes `latest` (and
  overwrites `sha-<commit>` of the same commit – same code, newer base); the
  cron job deploys it. The commit at `/version` does not change then. A
  rebuild can also be started by hand: `gh workflow run ci.yml --ref main`.
- **`caddy:2.11`** and **`postgres:18`**: the daily `scripts/auto-update.sh`
  run pulls them, so Caddy 2.11.x patches and PostgreSQL 18.x minor updates
  are applied automatically (PostgreSQL restarts for a few seconds).
- **Host**: `unattended-upgrades` installs security updates and reboots at
  05:00 when an update needs it (section 1). Docker starts the containers
  again (`restart: unless-stopped`).
- **Not automatic**: new minor/major versions (e.g. `caddy:2.12`, the `uv`
  version in the `Dockerfile`) arrive as Dependabot PRs on Mondays and are
  merged by hand. Python minor versions (#42) and PostgreSQL major upgrades
  (19, need a dump and restore, section 6) are excluded from Dependabot and
  done deliberately.
- GitHub disables scheduled workflows after 60 days without repository
  activity; it then shows a notice in the Actions tab and the workflow has to
  be re-enabled there.

## 5. Scheduled jobs

`crontab -e` as `deploy`:

```cron
# Database dump before the UpCloud backup, nightly 02:00
0 2 * * * cd /srv/vrobot && scripts/backup-db.sh
# Delete old contact messages (data protection), daily 03:00
0 3 * * * cd /srv/vrobot && docker compose -f compose.prod.yaml exec -T web python manage.py delete_old_contact_messages
# Automatic deploy of new app images (ADR 0012), every minute
* * * * * cd /srv/vrobot && scripts/auto-update.sh web 2>&1 | logger -t vrobot-update
# All images incl. caddy and postgres, daily 05:30 (after a possible reboot)
30 5 * * * cd /srv/vrobot && scripts/auto-update.sh 2>&1 | logger -t vrobot-update
```

The `web` check runs every minute since 2026-11-21 (#52; ADR 0012 started
with 5 minutes). GHCR has no pull rate limit, a run without a new image takes
about a second and prints nothing, and a lock prevents overlapping runs.

The server's time zone is `Europe/Zurich` (`timedatectl set-timezone
Europe/Zurich`, then `systemctl restart cron`), so cron times are Swiss time.
The UpCloud backup runs daily at 02:15 UTC (03:15/04:15 Swiss time), i.e.
after the dump (ADR 0008) and before the automatic reboot at 05:00.

## 6. Backups and restore

- `scripts/backup-db.sh` writes `backups/vrobot-YYYY-MM-DD.dump`
  (`pg_dump` custom format) and keeps 14 days (`KEEP_DAYS`).
- Uploaded files live in the Docker volume `vrobot_media`; the UpCloud
  backup of the disk covers them.

Restore a dump into the running database:

```bash
docker compose -f compose.prod.yaml exec -T db \
  sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' \
  < backups/vrobot-YYYY-MM-DD.dump
```

## 7. Logs and status

```bash
docker compose -f compose.prod.yaml ps
docker compose -f compose.prod.yaml logs --tail 100 web    # Django/Gunicorn
docker compose -f compose.prod.yaml logs --tail 100 caddy  # access log, TLS
```

## 8. Go-live

Main address `https://vrobot.ch`; `www.vrobot.ch` and `www2.vrobot.ch`
redirect there permanently (Caddy, `REDIRECT_ADDRESSES`). URLs of the old PHP
site redirect to the new pages (`core/legacy.py`). Caddy sends HSTS
(1 year, without subdomains).

1. Merge the go-live PR, wait for the CI image. Do **not** deploy yet:
   `REDIRECT_ADDRESSES` is required by the new Caddyfile.
2. DNS at Hostpoint (TTL is 5 minutes): `vrobot.ch` and `www.vrobot.ch`
   `A` → `212.147.228.149`; delete their `AAAA` records (they point to
   Hostpoint's web server). Do not touch `MX`, `SPF` or other mail records.
   If the domain is attached to the Hostpoint web hosting, detach it there
   first, otherwise Hostpoint may reset the records.
3. Check the authoritative name servers until both names answer with the new
   IP and no AAAA: `dig +short vrobot.ch A @ns.hostpoint.ch` (same for `www`).
4. Update `.env` and deploy:

   ```
   SITE_ADDRESS=vrobot.ch
   REDIRECT_ADDRESSES=www.vrobot.ch, www2.vrobot.ch
   ALLOWED_HOSTS=vrobot.ch
   CSRF_TRUSTED_ORIGINS=https://vrobot.ch
   ROBOTS_TAG=all
   ```

   ```bash
   scripts/deploy.sh   # recreates web and caddy with the new .env
   ```

   Caddy obtains certificates for all three names within seconds.
5. Check: `https://vrobot.ch/` (200, no `X-Robots-Tag: noindex`),
   `https://www.vrobot.ch/agenda/` and `https://www2.vrobot.ch/` → 301 to
   `https://vrobot.ch/…`, `https://vrobot.ch/about.php` → `/ueber-uns/`,
   admin login, contact form.
6. The Hostpoint web hosting stays (still used for other purposes, decided
   2026-11-18); only `vrobot.ch` and `www` no longer point to it. Do not
   cancel it as part of the website.
