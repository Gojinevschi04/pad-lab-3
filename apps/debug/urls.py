from django.urls import path
from rest_framework.routers import DefaultRouter

from tickets.debug.views import (
    AdminStatsView,
    GenerateTicketPDFView,
    TicketEmailViewSet,
    WhoAmIView,
)

app_name = "debug"

router = DefaultRouter()
router.register(r"tickets/emails", TicketEmailViewSet, basename="ticket-emails")

urlpatterns = [
    path(
        "generate-pdf/<int:ticket_id>/",
        GenerateTicketPDFView.as_view(),
        name="generate-pdf",
    ),
    path("admin/stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("whoami/", WhoAmIView.as_view(), name="whoami"),
] + router.urls
