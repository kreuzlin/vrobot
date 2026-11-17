from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from events.models import Event
from posts.models import Post

from .markdown import render_markdown
from .seo import SeoMixin


class HomeView(SeoMixin, TemplateView):
    template_name = "core/home.html"
    # No page title: the home page uses the plain site title.

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["latest_posts"] = Post.objects.published()[:3]
        context["upcoming_events"] = Event.objects.upcoming()[:3]
        return context


@staff_member_required
@require_POST
def markdown_preview(request):
    """Render Markdown for the admin editor preview.

    Uses the same renderer and sanitiser as the website, so the preview shows
    exactly what visitors will see. Staff only; CSRF-protected via POST.
    """
    html = render_markdown(request.POST.get("text", ""))
    return HttpResponse(html, content_type="text/html; charset=utf-8")
