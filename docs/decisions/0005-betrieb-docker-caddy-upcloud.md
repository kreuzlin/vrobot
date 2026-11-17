# 0005: Betrieb: Docker Compose, Caddy, UpCloud

- Status: angenommen
- Datum: 2026-11-17

## Kontext

Die alte Seite läuft als PHP-Shared-Hosting bei Hostpoint. Für Django wird
ein Server mit Python und PostgreSQL gebraucht. Der Betrieb soll einfach
bleiben und von einer Person überblickt werden können.

## Entscheidung

- **Hosting:** eigener VPS bei UpCloud, Ubuntu 26.04 LTS, x86_64.
- **Docker Compose** für lokale Entwicklung und Produktion
  (Dienste: `caddy`, `web`, `db`).
- **Caddy** als Webserver/Reverse Proxy mit automatischem HTTPS
  (Let's Encrypt), liefert auch statische Dateien und Medien aus.
- Django läuft unter **Gunicorn**.
- Die Hostpoint-Seite bleibt bis zur Umstellung live; Umstellung per DNS.

## Konsequenzen

- Ein Setup für Dev und Prod, wenig Unterschiede.
- Zertifikate ohne Handarbeit.
- Wir sind selbst für Server-Updates, Firewall und Backups verantwortlich
  (Ubuntu unattended-upgrades, UFW, Backup-Konzept nötig).
