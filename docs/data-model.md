# Data model

Draft for version 1. Updated with every model change.
All models have `created_at`/`updated_at` (automatic).
Admin labels (`verbose_name`) are German; field names are English.

## Post – `posts.Post`

| Field              | Type                  | Notes                                       |
|--------------------|-----------------------|---------------------------------------------|
| `title`            | CharField             | required                                    |
| `slug`             | SlugField, unique     | for the URL, prefilled from the title       |
| `body`             | TextField             | content (formatting: see open questions)    |
| `image`            | ImageField, optional  | with alt text field `image_alt`             |
| `author`           | CharField             | display name, not necessarily an admin user |
| `published_at`     | DateTimeField         | posts dated in the future are not visible yet |
| `is_published`     | BooleanField          | draft vs. published                         |
| `meta_description` | CharField, optional   | fallback: beginning of the body             |

Ordering: newest first.

## Event – `events.Event`

| Field         | Type                    | Notes                  |
|---------------|-------------------------|------------------------|
| `title`       | CharField               | required               |
| `start`       | DateTimeField           | required               |
| `end`         | DateTimeField, optional | must be after `start`  |
| `location`    | CharField, optional     |                        |
| `description` | TextField, optional     |                        |
| `link`        | URLField, optional      | e.g. registration      |

Publicly visible: events whose end (or start, if there is no end) is not in
the past. Implemented as a QuerySet method `upcoming()`; nothing is deleted,
past events remain in the admin.

## Document – `documents.Document`

| Field         | Type                            | Notes                                       |
|---------------|---------------------------------|---------------------------------------------|
| `title`       | CharField                       | required                                    |
| `category`    | ForeignKey → `DocumentCategory` | e.g. statutes, forms, annual reports        |
| `year`        | PositiveSmallIntegerField       | required                                    |
| `file`        | FileField                       | mainly PDF                                  |
| `description` | TextField, optional             |                                             |

`DocumentCategory`: `name`, `slug`, `order`. A separate model so the board
can add categories themselves.

Display: grouped by category, within each category by year descending.

## Static page – `pages.Page`

| Field              | Type              | Notes                                   |
|--------------------|-------------------|-----------------------------------------|
| `title`            | CharField         |                                         |
| `slug`             | SlugField, unique | `ueber-uns`, `mitmachen`, `kontakt`     |
| `body`             | TextField         |                                         |
| `meta_description` | CharField         |                                         |

Pages are created by a data migration; structure and URLs are fixed, only the
text is editable in the admin. The contact page additionally shows the form.

## Contact message – `contact.ContactMessage`

| Field        | Type          | Notes |
|--------------|---------------|-------|
| `name`       | CharField     |       |
| `email`      | EmailField    |       |
| `message`    | TextField     |       |
| `created_at` | DateTimeField |       |

Stored **and** forwarded by email to the association, so nothing is lost if
email delivery fails. A retention period needs to be defined (data protection).

## Open questions

- Text formatting in posts/pages: Markdown (simple, safe) or a rich text
  editor in the admin? → ADR once decided.
- Multiple images per post needed?
