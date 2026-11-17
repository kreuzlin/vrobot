from django.urls import path

from contact.views import ContactView

from .views import JoinView, PageView

app_name = "pages"

urlpatterns = [
    path("ueber-uns/", PageView.as_view(page_slug="ueber-uns"), name="about"),
    path("mitmachen/", JoinView.as_view(), name="join"),
    # Page content plus the contact form (contact app).
    path("kontakt/", ContactView.as_view(), name="contact"),
]
