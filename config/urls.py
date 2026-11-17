"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "VRoboT – Verwaltung"
admin.site.site_title = "VRoboT Verwaltung"
admin.site.index_title = "Inhalte verwalten"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("agenda/", include("events.urls")),
    path("beitraege/", include("posts.urls")),
    path("dokumente/", include("documents.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    # Development only: in production Caddy serves uploaded files.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
