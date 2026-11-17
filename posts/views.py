from django.views.generic import DetailView, ListView

from core.seo import SeoMixin

from .models import Post


class PostListView(SeoMixin, ListView):
    template_name = "posts/post_list.html"
    context_object_name = "posts"
    paginate_by = 10
    page_title = "Beiträge"
    meta_description = (
        "Neuigkeiten, Berichte und Rückblicke des Vereins Robotik Talente."
    )

    def get_queryset(self):
        return Post.objects.published()


class PostDetailView(SeoMixin, DetailView):
    template_name = "posts/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        # Drafts and scheduled posts return 404.
        return Post.objects.published()

    def get_page_title(self):
        return self.object.title

    def get_meta_description(self):
        return self.object.get_meta_description()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.image:
            context["og_image"] = self.request.build_absolute_uri(self.object.image.url)
        return context
