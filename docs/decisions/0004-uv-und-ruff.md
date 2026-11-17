# 0004: Python-Tooling: uv und Ruff

- Status: angenommen
- Datum: 2026-11-17

## Kontext

Abhängigkeiten sollen reproduzierbar sein, das Tooling schlank und schnell.

## Entscheidung

- **uv** verwaltet Python-Version, virtuelle Umgebung und Abhängigkeiten
  (`pyproject.toml` + `uv.lock`, beides committet). Auch im Docker-Image.
- **Ruff** übernimmt Linting und Formatierung (statt flake8/isort/black),
  konfiguriert in `pyproject.toml`. Läuft in CI und vor jedem Commit.

## Konsequenzen

- Ein Lockfile, identische Versionen lokal, in CI und auf dem Server.
- Kein `requirements.txt`, kein `pip install`.
