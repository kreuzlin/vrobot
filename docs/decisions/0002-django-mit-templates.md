# 0002: Django mit Server-Templates

- Status: angenommen
- Datum: 2026-11-17

## Kontext

vrobot.ch ist eine Inhaltsseite (Beiträge, Agenda, Dokumente, feste Seiten,
Kontaktformular) mit wenig Interaktivität. Die Inhalte pflegen
Vereinsmitglieder ohne technischen Hintergrund. Die bestehende Seite ist PHP.

## Entscheidung

- **Django in der aktuellen LTS-Version (5.2)**, Updates innerhalb der LTS-Linie;
  Wechsel auf die nächste LTS (6.2, erwartet April 2027) bewusst planen.
- **Django-Templates** für das Frontend, kein React/SPA.
- **Django-Admin** als Redaktionsoberfläche, kein separates CMS.

## Konsequenzen

- Ein Stack, kein Frontend-Build, schnelle Seiten, gute SEO ohne Zusatzaufwand.
- Das Admin ist sofort verfügbar, muss aber sorgfältig beschriftet und
  konfiguriert werden, damit Laien damit arbeiten können.
- Falls später mehr Interaktivität nötig ist, zuerst kleine Mittel (z. B. htmx)
  prüfen, bevor ein JS-Framework eingeführt wird.
