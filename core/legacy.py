"""Redirects from the URLs of the old PHP site (until 2026) to the new pages.

Keeps old links and search results working after the switch of vrobot.ch to
the new site. Internal targets are permanent (301); the GearsBot target is an
external setting and may change, so it is a temporary redirect (302).
"""

from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import path
from django.views.generic import RedirectView

from documents.models import Document
from posts.models import Post

# Old page → URL name of the new page.
PAGES = {
    "index.php": "core:home",
    "about.php": "pages:about",
    "engage.php": "pages:join",
    "agenda.php": "events:list",
    "contact.php": "pages:contact",
}

# Old post IDs (post.php?ID=…) → slug of the imported post (import_old_site).
POSTS = {"1": "die-welt-braucht-arduino"}


def old_post(request):
    slug = POSTS.get(request.GET.get("ID", ""))
    post = Post.objects.published().filter(slug=slug).first() if slug else None
    if post:
        return HttpResponsePermanentRedirect(post.get_absolute_url())
    return redirect("posts:list", permanent=True)


def old_attachment(request, filename):
    """/attachments/<file> → the imported document with the same file name."""
    document = (
        Document.objects.filter(file__endswith=f"/{filename}").order_by("-year").first()
    )
    if document:
        return HttpResponsePermanentRedirect(document.file.url)
    return redirect("documents:list", permanent=True)


def old_gearsbot(request, rest=""):
    """The old site hosted its own GearsBot copy under /python/public/."""
    return HttpResponseRedirect(settings.GEARSBOT_URL)


urlpatterns = [
    *(
        path(old, RedirectView.as_view(pattern_name=name, permanent=True))
        for old, name in PAGES.items()
    ),
    path("post.php", old_post),
    path("attachments/<path:filename>", old_attachment),
    path("python/public/", old_gearsbot),
    path("python/public/<path:rest>", old_gearsbot),
]
