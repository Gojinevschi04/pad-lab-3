import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from tickets.core.exceptions import TicketAlreadyCancelledError, TicketNotFoundError
from tickets.core.models import Ticket
from tickets.depot.backends.base import get_depot_backend
from tickets.depot.exceptions import DepotServiceError
from tickets.depot.serializers import TripDetailSerializer, TripSerializer

logger = logging.getLogger(__name__)


class TripViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    permission_classes = [AllowAny]

    def get_backend(self):
        if not hasattr(self, "_backend"):
            self._backend = get_depot_backend()
        return self._backend

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "origin",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                default="Ialoveni",
                description="Origin city",
            ),
            OpenApiParameter(
                "destination",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                default="Hincesti",
                description="Destination city",
            ),
        ]
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        origin = request.query_params.get("origin")
        destination = request.query_params.get("destination")

        try:
            trips = self.get_backend().list_trips(origin, destination)
        except DepotServiceError as e:
            return Response(
                {"detail": f"Error fetching trips: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "origin",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                default="Ialoveni",
                description="Origin city",
            ),
            OpenApiParameter(
                "destination",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                default="Hincesti",
                description="Destination city",
            ),
        ]
    )
    def retrieve(self, request: Request, pk=None, *args, **kwargs) -> Response:
        origin = request.query_params.get("origin")
        destination = request.query_params.get("destination")

        try:
            trip = self.get_backend().get_trip(int(pk), origin, destination)
        except DepotServiceError as e:
            return Response(
                {"detail": f"Error fetching trip: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if not trip:
            return Response(
                {"detail": "Trip not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TripSerializer(trip)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "origin",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                default="Ialoveni",
                description="Origin city",
            ),
            OpenApiParameter(
                "destination",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                default="Hincesti",
                description="Destination city",
            ),
        ]
    )
    @action(detail=True, methods=["get"])
    def seats(self, request: Request, pk=None) -> Response:
        origin = request.query_params.get("origin")
        destination = request.query_params.get("destination")

        try:
            seat_info = self.get_backend().get_seat_info(int(pk), origin, destination)
        except DepotServiceError as e:
            return Response(
                {"detail": f"Error fetching seat info: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if not seat_info:
            return Response(
                {"detail": "Trip not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TripDetailSerializer(seat_info)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="cancel-tickets")
    def cancel_tickets(self, request, pk=None):
        try:
            result = Ticket.objects.cancel_for_trip(pk)
        except TicketNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except TicketAlreadyCancelledError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except Exception:
            logger.exception("Unexpected error cancelling tickets")
            return Response(
                {"detail": "An unexpected error occurred while cancelling tickets."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "cancelled": result.get("cancelled", []),
                "failed": result.get("failed", []),
            },
            status=status.HTTP_200_OK,
        )
