from django.urls import path

from .views import PageView

app_name = "pages"

urlpatterns = [
    path("ueber-uns/", PageView.as_view(page_slug="ueber-uns"), name="about"),
    path("mitmachen/", PageView.as_view(page_slug="mitmachen"), name="join"),
    # The contact form is added to this page by the contact app.
    path("kontakt/", PageView.as_view(page_slug="kontakt"), name="contact"),
]
