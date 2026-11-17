# 0005: Hosting: Docker Compose, Caddy, UpCloud

- Status: accepted
- Date: 2026-11-17

## Context

The old site runs on PHP shared hosting at Hostpoint. Django needs a server
with Python and PostgreSQL. Operations should stay simple enough for one
person to oversee.

## Decision

- **Hosting:** own VPS at UpCloud, Ubuntu 26.04 LTS, x86_64.
- **Docker Compose** for local development and production
  (services: `caddy`, `web`, `db`).
- **Caddy** as web server/reverse proxy with automatic HTTPS
  (Let's Encrypt); also serves static and media files.
- Django runs under **Gunicorn**.
- The Hostpoint site stays live until cutover; cutover via DNS.

## Consequences

- One setup for dev and prod, few differences.
- Certificates without manual work.
- We are responsible for server updates, firewall and backups ourselves
  (Ubuntu unattended-upgrades, UFW, a backup concept is needed).
