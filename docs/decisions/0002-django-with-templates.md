# 0002: Django with server-side templates

- Status: accepted
- Date: 2026-11-17

## Context

vrobot.ch is a content site (posts, events, documents, static pages, contact
form) with little interactivity. Content is maintained by association members
without a technical background. The existing site is PHP.

## Decision

- **Django, current LTS (5.2)**, updating within the LTS line; plan the move
  to the next LTS (6.2, expected April 2027) deliberately.
- **Django templates** for the frontend, no React/SPA.
- **Django admin** as the editing interface, no separate CMS.

## Consequences

- One stack, no frontend build, fast pages, good SEO without extra effort.
- The admin is available immediately but has to be labelled and configured
  carefully so non-technical users can work with it.
- If more interactivity is needed later, try small tools first (e.g. htmx)
  before introducing a JS framework.
