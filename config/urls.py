"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

admin.site.site_header = "VRoboT – Verwaltung"
admin.site.site_title = "VRoboT Verwaltung"
admin.site.index_title = "Inhalte verwalten"

# Password reset for admin users ("Passwort vergessen?" on the login page).
# The admin app ships the German templates for these views.
password_reset_urls = [
    path(
        "admin/password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "admin/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "admin/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "admin/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]

urlpatterns = [
    *password_reset_urls,
    path("admin/", admin.site.urls),
    path("agenda/", include("events.urls")),
    path("beitraege/", include("posts.urls")),
    path("dokumente/", include("documents.urls")),
    path("", include("pages.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    # Development only: in production Caddy serves uploaded files.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
