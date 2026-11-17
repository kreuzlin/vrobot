"""Contact form with spam protection.

Spam protection without third-party services or cookies:

- Honeypot: a field hidden from humans via CSS. Bots that fill in every field
  are detected.
- Timing: the form carries a signed timestamp. Submissions faster than
  `MIN_SECONDS` are treated as bots; a tampered or very old timestamp is
  rejected with a message asking to submit again.

Bot submissions are not saved, but the view still shows the normal success
message, so bots get no feedback to adapt to.
"""

import time

from django import forms
from django.core import signing

MIN_SECONDS = 3
MAX_SECONDS = 24 * 60 * 60
SIGNING_SALT = "contact.form.timestamp"


def make_token(now=None):
    return signing.dumps(
        int(now if now is not None else time.time()), salt=SIGNING_SALT
    )


class ContactForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)
    email = forms.EmailField(label="E-Mail")
    message = forms.CharField(
        label="Nachricht", max_length=5000, widget=forms.Textarea(attrs={"rows": 8})
    )
    # Honeypot: must stay empty. Hidden via CSS, not type=hidden, so naive bots fill it.
    website = forms.CharField(
        label="Website (bitte leer lassen)",
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
    )
    token = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["token"] = make_token()
        self.is_spam = False

    def clean_token(self):
        try:
            started = signing.loads(self.cleaned_data["token"], salt=SIGNING_SALT)
        except signing.BadSignature:
            raise forms.ValidationError(
                "Das Formular ist ungültig. Bitte lade die Seite neu und sende "
                "die Nachricht erneut."
            ) from None
        age = time.time() - started
        if age > MAX_SECONDS:
            raise forms.ValidationError(
                "Das Formular war zu lange geöffnet. Bitte sende die Nachricht erneut."
            )
        if age < MIN_SECONDS:
            self.is_spam = True
        return self.cleaned_data["token"]

    def clean_website(self):
        if self.cleaned_data["website"]:
            self.is_spam = True
        return ""

    def clean(self):
        cleaned = super().clean()
        # A fresh token for re-rendering the form after errors.
        self.data = self.data.copy()
        self.data["token"] = make_token()
        return cleaned
