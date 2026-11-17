from django.contrib import admin

from .models import Document, DocumentCategory


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "document_count"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ["name"]}

    @admin.display(description="Anzahl Dokumente")
    def document_count(self, obj):
        return obj.documents.count()


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "year", "file"]
    list_filter = ["category", "year"]
    search_fields = ["title", "description"]
    list_select_related = ["category"]
    fields = ["title", "category", "year", "file", "description"]
