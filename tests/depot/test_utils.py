from unittest.mock import patch

import pytest

from tickets.core.models import Ticket
from tickets.depot.utils import generate_seat_status


@pytest.mark.django_db
class TestGenerateSeatStatus:
    def test_all_seats_available(self):
        trip_id = 1
        capacity = 5

        with patch.object(Ticket.objects, "taken_seats", return_value=[]):
            seats = generate_seat_status(trip_id, capacity)

        expected = {str(i): "available" for i in range(1, capacity + 1)}
        assert seats == expected

    def test_some_seats_taken(self):
        trip_id = 1
        capacity = 5

        with patch.object(Ticket.objects, "taken_seats", return_value=[2, 4]):
            seats = generate_seat_status(trip_id, capacity)

        expected = {
            "1": "available",
            "2": "reserved",
            "3": "available",
            "4": "reserved",
            "5": "available",
        }
        assert seats == expected

    def test_all_seats_taken(self):
        trip_id = 1
        capacity = 3

        with patch.object(Ticket.objects, "taken_seats", return_value=[1, 2, 3]):
            seats = generate_seat_status(trip_id, capacity)

        expected = {str(i): "reserved" for i in range(1, capacity + 1)}
        assert seats == expected
