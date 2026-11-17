"""Markdown rendering for editor content (ADR 0009).

Content is written in Markdown in the admin and rendered to HTML on output.
The HTML is sanitised with an allowlist, so raw HTML or scripts typed into
the editor never reach the page.
"""

import markdown as md
import nh3
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

# <h1> is reserved for the page title, so editors get h2–h4.
ALLOWED_TAGS = {
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "a",
    "h2",
    "h3",
    "h4",
    "blockquote",
    "code",
    "pre",
    "hr",
}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}
ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}


def render_markdown(text: str) -> str:
    """Convert Markdown to sanitised HTML (marked safe for templates)."""
    html = md.markdown(text or "", extensions=["sane_lists"], output_format="html")
    # A top-level heading ("# ...") becomes <h2> instead of being dropped.
    html = html.replace("<h1>", "<h2>").replace("</h1>", "</h2>")
    clean = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel="noopener noreferrer",
    )
    # Safe to mark as safe: the HTML has just been sanitised by nh3.
    return mark_safe(clean)


def markdown_to_plain_text(text: str, max_chars: int = 160) -> str:
    """Plain-text excerpt of Markdown content, e.g. for meta descriptions."""
    plain = " ".join(strip_tags(render_markdown(text)).split())
    return Truncator(plain).chars(max_chars)
