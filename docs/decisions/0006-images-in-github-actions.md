# 0006: Images in GitHub Actions bauen

- Status: angenommen
- Datum: 2026-11-17

## Kontext

Entwickelt wird auf Apple Silicon (arm64), der Server ist x86_64. Lokal für
amd64 zu bauen (Emulation) ist langsam und fehleranfällig; auf dem Server zu
bauen belastet ihn und braucht dort den Quellcode.

## Entscheidung

GitHub Actions baut das Produktions-Image für `linux/amd64` und pusht es in
die **GitHub Container Registry (ghcr.io)**. Vor dem Build laufen Ruff und die
Tests. Der Server zieht nur fertige Images (`docker compose pull`).

## Konsequenzen

- Reproduzierbare Images, Server braucht keinen Build-Toolchain.
- Images sind mit Commit-SHA getaggt → einfaches Zurückrollen.
- Der Server braucht Lesezugriff auf GHCR (Token oder öffentliches Image).
- Lokal wird weiterhin nativ für arm64 gebaut.
