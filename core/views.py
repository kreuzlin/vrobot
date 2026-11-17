from django.views.generic import TemplateView

from .seo import SeoMixin


class HomeView(SeoMixin, TemplateView):
    template_name = "core/home.html"
    # No page title: the home page uses the plain site title.
