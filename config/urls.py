"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "VRoboT – Verwaltung"
admin.site.site_title = "VRoboT Verwaltung"
admin.site.index_title = "Inhalte verwalten"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]
