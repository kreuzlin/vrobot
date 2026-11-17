from django.urls import path

from contact.views import ContactView

from .views import PageView

app_name = "pages"

urlpatterns = [
    path("ueber-uns/", PageView.as_view(page_slug="ueber-uns"), name="about"),
    path("mitmachen/", PageView.as_view(page_slug="mitmachen"), name="join"),
    # Page content plus the contact form (contact app).
    path("kontakt/", ContactView.as_view(), name="contact"),
]
