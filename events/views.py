from django.views.generic import ListView

from core.seo import SeoMixin

from .models import Event


class EventListView(SeoMixin, ListView):
    template_name = "events/event_list.html"
    context_object_name = "events"
    page_title = "Agenda"
    meta_description = (
        "Die nächsten Termine des Vereins Robotik Talente: Trainings, Workshops "
        "und Wettbewerbe."
    )

    def get_queryset(self):
        return Event.objects.upcoming()
