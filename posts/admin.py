from django.contrib import admin
from django.db import models

from core.widgets import MarkdownEditor

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # The only TextField is `body`.
    formfield_overrides = {models.TextField: {"widget": MarkdownEditor}}
    list_display = ["title", "author", "published_at", "is_published", "visible"]
    list_filter = ["is_published"]
    search_fields = ["title", "body", "author"]
    date_hierarchy = "published_at"
    prepopulated_fields = {"slug": ["title"]}

    class Media:
        js = ["core/js/image-alt-required.js"]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "image":
            field.widget.attrs["data-alt-field"] = "id_image_alt"
        return field

    fieldsets = [
        (None, {"fields": ["title", "body"]}),
        ("Bild", {"fields": ["image", "image_alt"]}),
        (
            "Veröffentlichung",
            {"fields": ["author", "published_at", "is_published"]},
        ),
        (
            "Erweitert",
            {"fields": ["slug", "meta_description"], "classes": ["collapse"]},
        ),
    ]

    @admin.display(boolean=True, description="Auf der Website sichtbar")
    def visible(self, obj):
        return obj.is_visible()

    def get_changeform_initial_data(self, request):
        # Prefill the author with the logged-in user's name.
        initial = super().get_changeform_initial_data(request)
        initial.setdefault(
            "author", request.user.get_full_name() or request.user.get_username()
        )
        return initial
