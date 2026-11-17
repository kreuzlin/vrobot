"""Quick links and hints on the admin start page."""

from django import template
from django.urls import reverse

from contact.models import ContactMessage

register = template.Library()

QUICK_LINKS = [
    ("Neuer Beitrag", "admin:posts_post_add", "posts.add_post"),
    ("Neuer Termin", "admin:events_event_add", "events.add_event"),
    ("Neues Dokument", "admin:documents_document_add", "documents.add_document"),
]


@register.inclusion_tag("core/admin/dashboard.html", takes_context=True)
def admin_dashboard(context):
    user = context["request"].user
    links = [
        {"label": label, "url": reverse(url_name)}
        for label, url_name, perm in QUICK_LINKS
        if user.has_perm(perm)
    ]
    unsent = 0
    if user.has_perm("contact.view_contactmessage"):
        unsent = ContactMessage.objects.filter(email_sent=False).count()
    return {
        "links": links,
        "unsent_count": unsent,
        "unsent_url": reverse("admin:contact_contactmessage_changelist")
        + "?email_sent__exact=0",
    }
