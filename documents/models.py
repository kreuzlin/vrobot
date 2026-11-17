import os

from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.utils import timezone

ALLOWED_EXTENSIONS = ["pdf", "docx", "xlsx", "odt", "ods"]
MAX_FILE_SIZE_MB = 20


def validate_file_size(file):
    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"Die Datei ist grösser als {MAX_FILE_SIZE_MB} MB.")


def current_year():
    return timezone.localdate().year


def document_file_path(instance, filename):
    return f"documents/{instance.year}/{filename}"


class DocumentCategory(models.Model):
    name = models.CharField("Name", max_length=100, unique=True)
    slug = models.SlugField("Kurzname", max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(
        "Reihenfolge",
        default=0,
        help_text="Kategorien mit kleinerer Zahl erscheinen weiter oben.",
    )

    class Meta:
        verbose_name = "Kategorie"
        verbose_name_plural = "Kategorien"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Document(models.Model):
    title = models.CharField("Titel", max_length=200)
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name="documents",
        verbose_name="Kategorie",
    )
    year = models.PositiveSmallIntegerField(
        "Jahr",
        default=current_year,
        validators=[MinValueValidator(1990), MaxValueValidator(2100)],
        help_text="Jahr, auf das sich das Dokument bezieht, z. B. beim Jahresbericht.",
    )
    file = models.FileField(
        "Datei",
        upload_to=document_file_path,
        validators=[
            FileExtensionValidator(ALLOWED_EXTENSIONS),
            validate_file_size,
        ],
        help_text=f"PDF bevorzugt. Erlaubt: {', '.join(ALLOWED_EXTENSIONS)}; "
        f"max. {MAX_FILE_SIZE_MB} MB.",
    )
    description = models.TextField("Beschreibung", blank=True, help_text="Optional.")
    created_at = models.DateTimeField("Erstellt", auto_now_add=True)
    updated_at = models.DateTimeField("Geändert", auto_now=True)

    class Meta:
        verbose_name = "Dokument"
        verbose_name_plural = "Dokumente"
        ordering = ["category__order", "category__name", "-year", "title"]

    def __str__(self):
        return f"{self.title} ({self.year})"

    @property
    def file_size(self):
        """Size in bytes, or None if the file is missing on disk."""
        try:
            return self.file.size
        except OSError:
            return None

    @property
    def extension(self):
        """File type for display, e.g. "PDF"."""
        return os.path.splitext(self.file.name)[1].lstrip(".").upper()
