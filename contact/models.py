from django.db import models


class ContactMessage(models.Model):
    """A message sent through the contact form.

    Stored in addition to being emailed, so nothing is lost if delivery
    fails. Old messages are removed by `delete_old_contact_messages`.
    """

    name = models.CharField("Name", max_length=100)
    email = models.EmailField("E-Mail")
    message = models.TextField("Nachricht")
    created_at = models.DateTimeField("Eingegangen", auto_now_add=True)
    email_sent = models.BooleanField(
        "Per E-Mail weitergeleitet",
        default=False,
        help_text="Nein = der Versand ist fehlgeschlagen; bitte direkt hier lesen.",
    )

    class Meta:
        verbose_name = "Kontaktanfrage"
        verbose_name_plural = "Kontaktanfragen"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"
