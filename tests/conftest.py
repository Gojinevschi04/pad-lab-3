from datetime import date, time

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory

from tickets.authentication import OpenIDAuthentication
from tickets.core.models import Ticket

User = get_user_model()


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.fixture
def auth_instance():
    return OpenIDAuthentication()


@pytest.fixture
def mock_payload():
    return {
        "email": "test@example.com",
    }


@pytest.fixture
def mock_token():
    return "mock.jwt.token"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def logged_in_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="pass")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="otheruser", password="pass")


@pytest.fixture
def raw_trip():
    return {
        "id": 1,
        "trip_nr": "T123",
        "date": date.today(),
        "status": "scheduled",
        "price": 15.50,
        "departure_time": time(8, 0),
        "arrival_time": time(10, 0),
        "from_station": {
            "city": "City A",
            "address": "Central Station",
            "street": "Main St",
        },
        "to_station": {
            "city": "City B",
            "address": "Bus Terminal",
            "street": "Second St",
        },
        "schedule": {
            "id": 1,
            "day_of_week": "Monday",
            "direction": "forward",
            "start_time": time(8, 0),
            "end_time": time(10, 0),
            "route": {
                "id": 1,
                "name": "City A - City B",
            },
            "bus": {
                "id": 1,
                "model": "Mercedes Sprinter",
                "plate_number": "AB-123-CD",
                "color": "white",
                "capacity": 20,
                "status": "active",
                "fuel": "diesel",
                "driver": {
                    "id": 1,
                    "status": "active",
                    "name": "John Doe",
                    "phone_number": "+37377777777",
                    "employee_id": "EMP001",
                },
            },
        },
    }


@pytest.fixture
def trip(raw_trip):
    from tickets.depot.serializers import TripSerializer

    return TripSerializer().to_representation(raw_trip)


@pytest.fixture
def ticket_factory(user, trip):
    def create_ticket(**kwargs):
        defaults = {
            "price": trip["price"],
            "seat_number": 1,
            "trip_id": trip["id"],
            "user": user,
            "status": Ticket.Status.RESERVED,
            "origin": trip["origin"],
            "destination": trip["destination"],
        }
        defaults.update(kwargs)
        return Ticket.objects.create(**defaults)

    return create_ticket


@pytest.fixture
def reserved_ticket(ticket_factory):
    return ticket_factory()


@pytest.fixture
def other_reserved_ticket(ticket_factory, other_user):
    return ticket_factory(user=other_user, seat_number=2)


@pytest.fixture
def paid_ticket(ticket_factory):
    return ticket_factory(
        seat_number=5, status=Ticket.Status.PAID, invoice_id="INV-EXISTING"
    )


@pytest.fixture
def expired_ticket(ticket_factory):
    return ticket_factory(
        reserved_until=timezone.now().replace(year=timezone.now().year - 1)
    )
