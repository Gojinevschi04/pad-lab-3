from rest_framework import serializers

from tickets.core.models import Ticket
from tickets.core.services.trip_service import TripService


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = [
            "id",
            "price",
            "status",
            "user",
            "invoice_id",
            "refund_id",
            "reserved_until",
            "file",
            "created_at",
            "updated_at",
            "expires_at",
        ]

    def validate(self, attrs: dict) -> dict:
        trip_id = attrs["trip_id"]
        seat_number = attrs["seat_number"]

        backend = self.context.get("backend")

        if not backend:
            raise serializers.ValidationError("Backend not provided for validation.")

        service = TripService(backend=backend)

        try:
            trip = service.fetch_and_serialize_trip(
                trip_id, attrs["origin"], attrs["destination"]
            )
        except RuntimeError as e:
            raise serializers.ValidationError(f"Cannot fetch trip: {str(e)}")

        if attrs["seat_number"] < 1 or attrs["seat_number"] > trip["bus_capacity"]:
            raise serializers.ValidationError(
                f"Seat number must be between 1 and {trip['bus_capacity']}."
            )

        if Ticket.objects.is_seat_taken(trip_id, seat_number):
            raise serializers.ValidationError("Seat is already taken.")

        attrs["status"] = Ticket.Status.RESERVED
        attrs["price"] = trip["price"]
        attrs["origin"] = trip["origin"]
        attrs["destination"] = trip["destination"]
        request = self.context.get("request")

        if not request or not hasattr(request, "user"):
            raise serializers.ValidationError(
                "User information missing in request context."
            )

        attrs["user"] = request.user
        return attrs


class TicketConfirmationSerializer(serializers.Serializer):
    ticket_id = serializers.IntegerField()
    invoice_id = serializers.CharField()

    @classmethod
    def validate_ticket_id(cls, value: str) -> str:
        if not Ticket.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Ticket not found.")
        return value

    def validate(self, attrs: dict) -> dict:
        invoice_id = attrs.get("invoice_id")

        if invoice_id and Ticket.objects.invoice_exists(invoice_id):
            raise serializers.ValidationError(
                {
                    "invoice_id": "This invoice is already associated with another ticket."
                }
            )

        return attrs
