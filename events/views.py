from itertools import groupby

from django.utils import timezone
from django.views.generic import ListView

from core.seo import SeoMixin

from .models import Event


def group_by_month(events):
    """Group events (ordered by start) into months, in Swiss local time.

    Returns a list of {"month": date (first day of the month), "events": [...]}.
    """

    def month_of(event):
        return timezone.localtime(event.start).date().replace(day=1)

    return [
        {"month": month, "events": list(items)}
        for month, items in groupby(events, key=month_of)
    ]


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["months"] = group_by_month(context["events"])
        return context
