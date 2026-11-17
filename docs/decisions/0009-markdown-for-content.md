# 0009: Markdown for rich text content

- Status: accepted
- Date: 2026-11-17

## Context

Posts and static pages need formatted text (headings, paragraphs, lists,
links). Editors are association members without a technical background.
WYSIWYG editors tend to let pasted styles (fonts, colours, sizes from Word or
emails) leak into the site and require HTML sanitising.

## Decision

- Body text is stored as **Markdown** in a `TextField`.
- The admin uses a small Markdown editor with a toolbar and preview
  (e.g. EasyMDE, loaded as a static script, no build step), so editors do not
  need to know Markdown syntax.
- Rendering happens server-side (Python Markdown library) and the resulting
  HTML is sanitised with an allowlist (e.g. `nh3`) before output.
- Version 1 has no inline images; each post has one main image field.

## Consequences

- Consistent layout: only headings, paragraphs, emphasis, lists and links.
- Content stays readable and portable as plain text.
- One small JS dependency in the admin only; the public site is unaffected.
- Inline images or galleries would need a separate feature later.
