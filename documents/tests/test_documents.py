"""Tests for documents."""

import shutil
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from documents.models import MAX_FILE_SIZE_MB, Document, DocumentCategory

TEMP_MEDIA = tempfile.mkdtemp()


def pdf(name="dokument.pdf", content=b"%PDF-1.4 test"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class DocumentTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def category(self, slug):
        return DocumentCategory.objects.get(slug=slug)

    def make(self, title, category="formulare", year=2026, **kwargs):
        return Document.objects.create(
            title=title,
            category=self.category(category),
            year=year,
            file=pdf(),
            **kwargs,
        )


class InitialCategoriesTests(TestCase):
    def test_default_categories_exist_in_order(self):
        self.assertEqual(
            list(DocumentCategory.objects.values_list("name", flat=True)),
            ["Statuten", "Formulare", "Jahresberichte"],
        )


class ValidationTests(DocumentTestCase):
    def build(self, file, year=2026):
        return Document(
            title="Test", category=self.category("formulare"), year=year, file=file
        )

    def test_pdf_is_accepted(self):
        self.build(pdf()).full_clean()

    def test_disallowed_extension_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self.build(SimpleUploadedFile("virus.exe", b"MZ")).full_clean()
        self.assertIn("file", ctx.exception.message_dict)

    def test_too_large_file_is_rejected(self):
        big = pdf(content=b"0" * (MAX_FILE_SIZE_MB * 1024 * 1024 + 1))
        with self.assertRaises(ValidationError) as ctx:
            self.build(big).full_clean()
        self.assertIn("file", ctx.exception.message_dict)

    def test_implausible_year_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self.build(pdf(), year=1900).full_clean()
        self.assertIn("year", ctx.exception.message_dict)

    def test_category_with_documents_cannot_be_deleted(self):
        from django.db.models import ProtectedError

        self.make("Anmeldeformular")
        with self.assertRaises(ProtectedError):
            self.category("formulare").delete()


class ListViewTests(DocumentTestCase):
    def test_grouped_by_category_and_sorted_by_year_desc(self):
        self.make("Jahresbericht 2024", "jahresberichte", 2024)
        self.make("Jahresbericht 2025", "jahresberichte", 2025)
        self.make("Statuten", "statuten", 2020)

        response = self.client.get(reverse("documents:list"))
        content = response.content.decode()

        # Category order: Statuten before Jahresberichte.
        self.assertLess(
            content.index("<h2>Statuten</h2>"), content.index("<h2>Jahresberichte</h2>")
        )
        # Within a category: newest year first.
        self.assertLess(
            content.index("Jahresbericht 2025"), content.index("Jahresbericht 2024")
        )

    def test_empty_categories_are_hidden(self):
        self.make("Statuten", "statuten", 2020)
        response = self.client.get(reverse("documents:list"))
        self.assertNotContains(response, "<h2>Formulare</h2>", html=True)

    def test_shows_link_type_and_size(self):
        doc = self.make("Anmeldeformular")
        response = self.client.get(reverse("documents:list"))
        self.assertContains(response, f'href="{doc.file.url}"')
        self.assertContains(response, "2026 · PDF")

    def test_missing_file_on_disk_does_not_break_page(self):
        doc = self.make("Verloren")
        doc.file.storage.delete(doc.file.name)
        response = self.client.get(reverse("documents:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verloren")

    def test_empty_state_title_and_navigation(self):
        response = self.client.get(reverse("documents:list"))
        self.assertContains(response, "Zurzeit sind keine Dokumente verfügbar.")
        self.assertContains(response, "<title>Dokumente – VRoboT</title>", html=True)
        self.assertContains(
            response, f'<a href="{reverse("documents:list")}" aria-current="page">'
        )
