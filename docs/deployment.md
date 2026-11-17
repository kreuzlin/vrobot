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

At Hostpoint: an `A` record (and `AAAA` if the server has IPv6) for
`www2.vrobot.ch` pointing to the server. Do not change any other records
(the old site stays live). Caddy can only obtain the certificate once this
record resolves.

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
| `EMAIL_*`, `DEFAULT_FROM_EMAIL` | Hostpoint mailbox (ADR 0010) |
| `CONTACT_RECIPIENTS` | addresses for contact form messages |

Then:

```bash
scripts/deploy.sh
docker compose -f compose.prod.yaml exec web python manage.py createsuperuser
# Content of the old site (one-time; try --dry-run first)
docker compose -f compose.prod.yaml exec web python manage.py import_old_site
```

Check `https://www2.vrobot.ch/`, log in to `/admin/`, send a test message via
the contact form.

## 4. Deploying updates

After a PR is merged, CI pushes a new image (`latest` and `sha-<commit>`).
On the server:

```bash
cd /srv/vrobot && scripts/deploy.sh
```

The script pulls the repo and images, runs migrations, restarts the
containers and removes old images.

**Rollback** to an earlier build: set `IMAGE_TAG=sha-<commit>` in `.env` and
run `scripts/deploy.sh` again (set it back to `latest` afterwards). Migrations
are not rolled back automatically.

## 5. Scheduled jobs

`crontab -e` as `deploy`:

```cron
# Delete old contact messages (data protection), daily 03:00
0 3 * * * cd /srv/vrobot && docker compose -f compose.prod.yaml exec -T web python manage.py delete_old_contact_messages
# Database dump before the UpCloud backup, nightly 02:00
0 2 * * * cd /srv/vrobot && scripts/backup-db.sh
```

The server's time zone is `Europe/Zurich` (`timedatectl set-timezone
Europe/Zurich`, then `systemctl restart cron`), so cron times are Swiss time.
The UpCloud backup runs daily at 02:15 UTC (03:15/04:15 Swiss time), i.e.
after the dump (ADR 0008).

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

## 8. Go-live (later)

Planned in step 12: switch `SITE_ADDRESS` to the main domain(s), set
`ROBOTS_TAG=all`, enable HSTS, add redirects for old URLs,
then change DNS at Hostpoint.
