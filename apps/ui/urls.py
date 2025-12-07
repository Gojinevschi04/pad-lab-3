from django.urls import path

from . import views

app_name = "ui"

urlpatterns = [
    path("home/", views.HomeView.as_view(), name="home"),
    path("partial/", views.PartialView.as_view(), name="partial"),
]
