from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from tickets.core.views import OAuth2RedirectView, TicketViewSet

router = DefaultRouter()
router.register(r"tickets", TicketViewSet, basename="ticket")

urlpatterns = [
    path("health/", lambda request: HttpResponse(content=b"OK"), name="health"),
    path("admin/", admin.site.urls),
    path("", include("tickets.ui.urls", namespace="ui")),
    path("", include("tickets.core.urls", namespace="tickets-core")),
    path("", include("tickets.depot.urls", namespace="tickets-depot")),
    # OpenAPI schema JSON
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path(
        "api/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Optional: ReDoc UI
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path(
        "api/oauth2-redirect.html",
        OAuth2RedirectView.as_view(),
        name="swagger-ui-oauth2-redirect",
    ),
    path("debug/", include("tickets.debug.urls", namespace="debug")),
]
