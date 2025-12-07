from unittest.mock import MagicMock

import pytest
from rest_framework.exceptions import ValidationError

from tickets.core.models import Ticket
from tickets.core.serializers import TicketConfirmationSerializer, TicketSerializer


@pytest.mark.django_db
class TestTicketSerializer:
    @pytest.fixture
    def context(self, user, raw_trip):
        backend = MagicMock()
        backend.get_trip.return_value = raw_trip
        return {"request": MagicMock(user=user), "backend": backend}

    def test_valid_ticket_reservation(self, context, trip, user, raw_trip):
        data = {
            "trip_id": trip["id"],
            "seat_number": 5,
            "origin": trip["origin"],
            "destination": trip["destination"],
        }

        serializer = TicketSerializer(data=data, context=context)
        assert serializer.is_valid(), serializer.errors

        validated = serializer.validated_data
        assert validated["price"] == trip["price"]
        assert validated["origin"] == trip["origin"]
        assert validated["destination"] == trip["destination"]
        assert validated["status"] == Ticket.Status.RESERVED
        assert validated["user"] == user

    def test_invalid_trip_id(self, context, trip):
        context["backend"].get_trip.return_value = None
        data = {
            "trip_id": 999,
            "seat_number": 1,
            "origin": trip["origin"],
            "destination": trip["destination"],
        }

        serializer = TicketSerializer(data=data, context=context)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        assert "Cannot fetch trip" in str(exc.value)

    def test_seat_out_of_bounds(self, context, raw_trip, trip):
        data = {
            "trip_id": raw_trip["id"],
            "seat_number": 2000,
            "origin": trip["origin"],
            "destination": trip["destination"],
        }

        serializer = TicketSerializer(data=data, context=context)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        assert f"Seat number must be between 1 and {trip['bus_capacity']}." in str(
            exc.value
        )

    def test_seat_already_reserved(self, context, raw_trip, trip, user):
        # Pre-create a ticket with the same seat
        Ticket.objects.create(
            trip_id=raw_trip["id"],
            seat_number=5,
            status=Ticket.Status.RESERVED,
            user=user,
            price=trip["price"],
            origin=trip["origin"],
            destination=trip["destination"],
        )

        data = {
            "trip_id": trip["id"],
            "seat_number": 5,
            "origin": trip["origin"],
            "destination": trip["destination"],
        }

        serializer = TicketSerializer(data=data, context=context)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        assert "Seat is already taken." in str(exc.value)

    def test_create_ticket_success(self, context, trip):
        data = {
            "trip_id": trip["id"],
            "seat_number": 7,
            "origin": trip["origin"],
            "destination": trip["destination"],
        }

        serializer = TicketSerializer(data=data, context=context)
        assert serializer.is_valid(), serializer.errors

        ticket = serializer.save()
        assert isinstance(ticket, Ticket)
        assert ticket.trip_id == trip["id"]
        assert ticket.status == Ticket.Status.RESERVED
        assert ticket.price == trip["price"]


@pytest.mark.django_db
class TestTicketConfirmationSerializer:
    def test_valid_ticket_confirmation(self, user):
        ticket = Ticket.objects.create(
            seat_number=1,
            trip_id=111,
            status=Ticket.Status.RESERVED,
            user=user,
            price=99.99,
            origin="Origin",
            destination="Destination",
        )

        data = {"ticket_id": ticket.id, "invoice_id": "abc123"}
        serializer = TicketConfirmationSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["ticket_id"] == ticket.id

    def test_ticket_confirmation_invalid_ticket_id(self):
        data = {"ticket_id": 999999, "invoice_id": "some_invoice"}
        serializer = TicketConfirmationSerializer(data=data)

        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        assert "Ticket not found." in str(exc.value)
