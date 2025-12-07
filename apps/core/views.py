import logging

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import (
    TemplateHTMLRenderer,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from ..depot.backends.base import get_depot_backend
from .exceptions import SeatAlreadyTakenError
from .models import Ticket
from .permissions import IsTicketOwner
from .serializers import (
    TicketConfirmationSerializer,
    TicketSerializer,
)
from .services.ticket_pdf_service import TicketPDFService

pdf_service = TicketPDFService()

logger = logging.getLogger(__name__)


class TicketViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsTicketOwner]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["backend"] = get_depot_backend()
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ticket = Ticket.objects.create_ticket(**serializer.validated_data)
        except SeatAlreadyTakenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except Exception:
            logger.exception("Unexpected error while creating ticket")
            return Response(
                {"detail": "An unexpected error occurred while creating ticket."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "id": ticket.id,
                "trip_id": ticket.trip_id,
                "seat_number": ticket.seat_number,
                "status": ticket.status,
                "reserved_until": ticket.reserved_until,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["post"],
        serializer_class=TicketConfirmationSerializer,
        url_path="webhook/confirm",
    )
    def confirm(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket_id = serializer.validated_data["ticket_id"]
        invoice_id = serializer.validated_data["invoice_id"]

        ticket = get_object_or_404(self.get_queryset(), pk=ticket_id)

        try:
            ticket.confirm(invoice_id)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Ticket confirmed."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        ticket = get_object_or_404(self.get_queryset(), pk=pk)

        try:
            ticket.cancel()
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(ticket)
        return Response(
            {"message": "Ticket cancelled.", **serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="presigned")
    def presigned(self, request: Request, pk=None) -> Response:
        ticket = get_object_or_404(self.get_queryset(), pk=pk)

        try:
            presigned_url = pdf_service.get_download_url(ticket)
        except ValueError:
            return Response(
                {"error": "PDF not available yet"},
                status=HTTP_400_BAD_REQUEST,
            )

        return Response({"presigned_url": presigned_url})


class OAuth2RedirectView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "tickets/oauth2-redirect.html"
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response(
            {"message": "Redirecting to OAuth2 provider."},
            template_name=self.template_name,
        )

    def post(self, request: Request) -> Response:
        return Response(
            {"message": "Redirected to OAuth2 provider."},
            template_name=self.template_name,
        )
