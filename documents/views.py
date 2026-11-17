from django.db.models import Prefetch
from django.views.generic import ListView

from core.seo import SeoMixin

from .models import Document, DocumentCategory


class DocumentListView(SeoMixin, ListView):
    """All documents, grouped by category (only categories with documents)."""

    template_name = "documents/document_list.html"
    context_object_name = "categories"
    page_title = "Dokumente"
    meta_description = (
        "Statuten, Formulare und Jahresberichte des Vereins Robotik Talente "
        "zum Herunterladen."
    )

    def get_queryset(self):
        return (
            DocumentCategory.objects.filter(documents__isnull=False)
            .distinct()
            .prefetch_related(
                Prefetch(
                    "documents", queryset=Document.objects.order_by("-year", "title")
                )
            )
        )
