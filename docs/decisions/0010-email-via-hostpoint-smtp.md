# 0010: Send email via Hostpoint SMTP

- Status: accepted
- Date: 2026-11-17

## Context

The contact form must forward messages to the association by email. The
vrobot.ch domain and its mailboxes are hosted at Hostpoint and stay there.

## Decision

- Django sends email through **Hostpoint's SMTP server** using an existing
  association mailbox (submission port with TLS, e.g. 465 or 587).
- `From` is the association's own address; the sender's address from the form
  is set as `Reply-To` (never as `From`, to avoid spoofing and SPF failures).
- Credentials live only in `.env` (`EMAIL_HOST`, `EMAIL_PORT`,
  `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, …).
- Messages are also stored in the database, so nothing is lost if delivery
  fails (see `docs/data-model.md`).

## Consequences

- No additional provider or account; SPF/DKIM are already handled by Hostpoint
  for the domain.
- Depends on outbound SMTP from the UpCloud server being allowed on the chosen
  port – verify when provisioning.
- Locally, Django's console email backend is used.
