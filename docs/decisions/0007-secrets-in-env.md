# 0007: Secrets nur in .env

- Status: angenommen
- Datum: 2026-11-17

## Kontext

Das Repository kann öffentlich werden oder mit weiteren Personen geteilt
werden. Zugangsdaten (Django `SECRET_KEY`, Datenbank, SMTP) dürfen nie darin
landen.

## Entscheidung

- Secrets und umgebungsabhängige Werte ausschliesslich in `.env`
  (in `.gitignore`), eingelesen über Docker Compose und Umgebungsvariablen.
- Im Repo liegt nur `.env.example` mit Platzhaltern und Erklärungen.
- In GitHub Actions werden nötige Werte als Repository-Secrets hinterlegt.

## Konsequenzen

- Jede neue Variable muss in `.env.example` nachgeführt werden.
- Die produktive `.env` existiert nur auf dem Server und muss separat
  gesichert werden (z. B. im Passwortmanager des Vereins).
