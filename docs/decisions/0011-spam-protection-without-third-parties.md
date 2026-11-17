# 0011: Spam protection without third-party services

- Status: accepted
- Date: 2026-11-17

## Context

The contact form needs spam protection. CAPTCHA services (reCAPTCHA,
hCaptcha, Turnstile) load third-party scripts, may set cookies, need a
privacy notice and are a hurdle for children and people with disabilities.
The expected spam volume for a small association site is low.

## Decision

Two invisible checks, no external services:

- **Honeypot:** an extra text field hidden from humans with CSS. If it is
  filled in, the submission is spam.
- **Timing token:** the form carries a signed timestamp (`django.core.signing`).
  Submissions faster than 3 seconds are spam; a tampered token or a form open
  longer than 24 hours is rejected with a message asking to submit again.

Spam is discarded silently: the sender sees the normal success message, so
bots get no feedback. Nothing is stored or emailed.

## Consequences

- No cookies, no third-party requests, accessible for everyone.
- Stops simple bots; targeted spam may get through. If that becomes a
  problem, add rate limiting per IP or reconsider a privacy-friendly CAPTCHA
  in a new ADR.
