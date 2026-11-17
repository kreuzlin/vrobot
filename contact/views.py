import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views.generic import FormView

from pages.views import PageMixin

from .forms import ContactForm
from .models import ContactMessage

logger = logging.getLogger(__name__)

SUCCESS_MESSAGE = "Vielen Dank für deine Nachricht! Wir melden uns so bald wie möglich."


def forward_by_email(contact_message):
    """Email the message to the association. Returns True on success."""
    recipients = settings.CONTACT_RECIPIENTS
    if not recipients:
        logger.error(
            "CONTACT_RECIPIENTS is not configured; message %s not sent",
            contact_message.pk,
        )
        return False
    email = EmailMessage(
        subject=f"Kontaktformular vrobot.ch: {contact_message.name}",
        body=render_to_string("contact/email.txt", {"msg": contact_message}),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
        # Answering the email goes to the sender; From stays our own address
        # so SPF/DKIM pass (ADR 0010).
        reply_to=[contact_message.email],
    )
    try:
        email.send()
    except Exception:
        logger.exception("Sending contact message %s failed", contact_message.pk)
        return False
    return True


class ContactView(PageMixin, FormView):
    """The "Kontakt" page: page content plus the contact form."""

    page_slug = "kontakt"
    template_name = "contact/contact.html"
    form_class = ContactForm

    def form_valid(self, form):
        if form.is_spam:
            logger.info("Contact form: spam submission discarded")
        else:
            data = form.cleaned_data
            contact_message = ContactMessage.objects.create(
                name=data["name"], email=data["email"], message=data["message"]
            )
            if forward_by_email(contact_message):
                contact_message.email_sent = True
                contact_message.save(update_fields=["email_sent"])
        # Same response for spam and real messages (no feedback for bots).
        messages.success(self.request, SUCCESS_MESSAGE)
        return redirect(self.request.path)
