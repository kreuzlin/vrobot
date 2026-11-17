from django.views.generic import TemplateView

from events.models import Event

from .seo import SeoMixin


class HomeView(SeoMixin, TemplateView):
    template_name = "core/home.html"
    # No page title: the home page uses the plain site title.

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["upcoming_events"] = Event.objects.upcoming()[:3]
        return context
