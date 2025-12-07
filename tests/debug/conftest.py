from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from tickets.core.models import Ticket

User = get_user_model()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="pass")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="otheruser", password="pass")


@pytest.fixture
def ticket(user, trip):
    return Ticket.objects.create(
        price=trip.get("price"),
        seat_number=3,
        trip_id=trip.get("id"),
        user=user,
        status=Ticket.Status.RESERVED,
        origin=trip.get("origin"),
        destination=trip.get("destination"),
        invoice_id="INV-123",
    )


@pytest.fixture
def trip():
    return {
        "id": 1,
        "trip_id": 1,
        "trip_nr": "T123",
        "price": 33,
        "date": timezone.now().date(),
        "start_time": timezone.now().time(),
        "end_time": (timezone.now() + timedelta(hours=2)).time(),
        "origin": "Ialoveni",
        "destination": "Hincesti",
        "bus_capacity": 52,
    }
