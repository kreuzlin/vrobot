from django.contrib import admin

from .models import Event


class TimeFilter(admin.SimpleListFilter):
    title = "Zeitraum"
    parameter_name = "zeitraum"

    def lookups(self, request, model_admin):
        return [("kommend", "Kommende"), ("vergangen", "Vergangene")]

    def queryset(self, request, queryset):
        upcoming = Event.objects.upcoming().values("pk")
        if self.value() == "kommend":
            return queryset.filter(pk__in=upcoming)
        if self.value() == "vergangen":
            return queryset.exclude(pk__in=upcoming)
        return queryset


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "start", "end", "location", "upcoming"]
    list_filter = [TimeFilter]
    search_fields = ["title", "location", "description"]
    date_hierarchy = "start"
    fieldsets = [
        (None, {"fields": ["title", ("start", "end"), "location"]}),
        ("Details", {"fields": ["description", "link"]}),
    ]

    @admin.display(boolean=True, description="Wird angezeigt")
    def upcoming(self, obj):
        return obj.is_upcoming()
