# 0003: PostgreSQL als Datenbank

- Status: angenommen
- Datum: 2026-11-17

## Kontext

Die Datenmenge ist klein. SQLite wäre technisch ausreichend, aber Betrieb in
Containern, Backups und spätere Erweiterungen sprechen für einen echten
Datenbankserver.

## Entscheidung

PostgreSQL (aktuelle stabile Hauptversion, offizielles Docker-Image),
in Entwicklung **und** Produktion. Kein SQLite, auch nicht für Tests.

## Konsequenzen

- Gleiches Verhalten lokal und auf dem Server.
- Backups per `pg_dump`.
- Ein zusätzlicher Container und ein Volume, das gesichert werden muss.
