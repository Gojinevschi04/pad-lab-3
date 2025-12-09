import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from tickets.core.models import Ticket
from tickets.core.permissions import IsTicketOwner
from tickets.core.services.ticket_pdf_service import TicketPDFService
from tickets.core.services.trip_reminder_service import TripReminderService

pdf_service = TicketPDFService()

logger = logging.getLogger(__name__)


class GenerateTicketPDFView(APIView):
    permission_classes = [IsAuthenticated, IsTicketOwner]

    def post(self, request, ticket_id):
        try:
            Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"status": "PDF generation task queued", "ticket_id": ticket_id},
        )


class TicketEmailViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="send-ticket-email")
    def send_ticket_email_action(self, request, pk=None):
        ticket = get_object_or_404(self.get_queryset(), pk=pk)
        return Response({"detail": "Ticket email sent."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="send-cancellation-email")
    def send_cancellation_email_action(self, request, pk=None):
        ticket = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(
            {"detail": "Trip cancellation email sent."}, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"], url_path="send-reminders")
    def send_reminders_action(self, request):
        service: TripReminderService = TripReminderService()
        service.process_reminders()
        return Response({"detail": "Reminder emails sent."}, status=status.HTTP_200_OK)


class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # ticket_sales = get_ticket_sales_count()
        # active_routes = get_most_active_routes()
        # occupancy_stats = get_seat_occupancy_rates()

        return Response(
            {
                "ticket_sales_count": 1,
                "most_active_routes": 2,
                "seat_occupancy_rates": 3,
            },
        )


class WhoAmIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        return Response(
            {
                "email": getattr(user, "email", ""),
                "username": getattr(user, "username", ""),
                "id": user.id,
            },
        )
