from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Read-only archive of contact form messages."""

    list_display = ["name", "email", "created_at", "email_sent"]
    list_filter = ["email_sent"]
    search_fields = ["name", "email", "message"]
    date_hierarchy = "created_at"
    readonly_fields = ["name", "email", "message", "created_at", "email_sent"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Viewing is allowed via the view permission; nothing can be edited.
        return False
