from django.contrib import admin
from django.db import models

from core.widgets import MarkdownEditor

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Pages are fixed: they can be edited, but not added or deleted."""

    list_display = ["title", "updated_at"]
    fields = ["title", "body", "meta_description"]
    # The only TextField is `body`.
    formfield_overrides = {models.TextField: {"widget": MarkdownEditor}}

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
