# Data model

Draft for version 1. Updated with every model change.
All models have `created_at`/`updated_at` (automatic).
Admin labels (`verbose_name`) are German; field names are English.

## Post – `posts.Post`

| Field              | Type                  | Notes                                       |
|--------------------|-----------------------|---------------------------------------------|
| `title`            | CharField             | required                                    |
| `slug`             | SlugField, unique     | for the URL, prefilled from the title       |
| `body`             | TextField             | Markdown, rendered and sanitised (ADR 0009) |
| `image`            | ImageField, optional  | stored under `media/posts/<year>/`          |
| `image_alt`        | CharField             | required when an image is set (also enforced in the browser, so the chosen file is not lost on form errors) |
| `author`           | CharField             | display name; prefilled with the admin user's name |
| `published_at`     | DateTimeField         | posts dated in the future are not visible yet |
| `is_published`     | BooleanField          | draft vs. published                         |
| `meta_description` | CharField, optional   | fallback: beginning of the body             |

Visible on the website: `is_published` and `published_at <= now`
(`Post.objects.published()`, newest first; `Post.is_visible()` per object).
Drafts and scheduled posts return 404.

Shown on `/beitraege/` (10 per page), `/beitraege/<slug>/` and on the home
page (latest three). The detail page sets `og:image` when an image exists.

## Event – `events.Event`

| Field         | Type                    | Notes                  |
|---------------|-------------------------|------------------------|
| `title`       | CharField               | required               |
| `start`       | DateTimeField           | required               |
| `end`         | DateTimeField, optional | must be after `start`  |
| `location`    | CharField, optional     |                        |
| `description` | TextField, optional     | plain text, line breaks kept |
| `link`        | URLField, optional      | e.g. registration      |

Publicly visible ("upcoming"):

- events with an end: until the end has passed;
- events without an end: for the whole local day (Europe/Zurich) of the start.

Implemented as `Event.objects.upcoming()` (ordered by start) with the Python
counterpart `Event.is_upcoming()` used in the admin. Nothing is deleted; past
events remain in the admin (filter "Zeitraum").

Shown on `/agenda/` (all upcoming) and on the home page (next three).

## Document – `documents.Document`

| Field         | Type                            | Notes                                       |
|---------------|---------------------------------|---------------------------------------------|
| `title`       | CharField                       | required                                    |
| `category`    | ForeignKey → `DocumentCategory` | e.g. statutes, forms, annual reports        |
| `year`        | PositiveSmallIntegerField       | default: current year, 1990–2100            |
| `file`        | FileField                       | pdf, docx, xlsx, odt, ods; max. 20 MB; stored under `media/documents/<year>/` |
| `description` | TextField, optional             |                                             |

`DocumentCategory`: `name`, `slug`, `order`. A separate model so the board
can add categories themselves. The initial categories Statuten, Formulare and
Jahresberichte are created by a data migration. A category that still has
documents cannot be deleted (`PROTECT`).

Display on `/dokumente/`: grouped by category (empty categories hidden),
within each category by year descending, with file type and size.

Note: deleting a document or replacing its file does not delete the old file
from disk (Django default). Acceptable for v1; clean up manually if needed.

## Static page – `pages.Page`

| Field              | Type              | Notes                                   |
|--------------------|-------------------|-----------------------------------------|
| `title`            | CharField         |                                         |
| `slug`             | SlugField, unique | `ueber-uns`, `mitmachen`, `kontakt`     |
| `body`             | TextField         | Markdown (ADR 0009)                     |
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

- Multiple images per post needed?
