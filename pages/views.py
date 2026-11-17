from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from core.seo import SeoMixin

from .models import Page


class PageView(SeoMixin, TemplateView):
    """Renders the fixed page identified by `page_slug`."""

    page_slug = None
    template_name = "pages/page.html"

    def get(self, request, *args, **kwargs):
        self.page = get_object_or_404(Page, slug=self.page_slug)
        return super().get(request, *args, **kwargs)

    def get_page_title(self):
        return self.page.title

    def get_meta_description(self):
        return self.page.meta_description

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = self.page
        return context
