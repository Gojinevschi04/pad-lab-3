from django.urls import resolve, reverse

from tickets.ui import views


def test_home_url_resolves():
    path = reverse("ui:home")
    assert resolve(path).func.view_class == views.HomeView


def test_partial_url_resolves():
    path = reverse("ui:partial")
    assert resolve(path).func.view_class == views.PartialView
