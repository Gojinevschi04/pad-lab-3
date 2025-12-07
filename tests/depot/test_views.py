from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status

from tickets.core.models import Ticket


@pytest.mark.django_db
class TestTripViewSet:
    @pytest.fixture
    def mock_backend(self):
        with patch("tickets.depot.views.get_depot_backend") as mock_fn:
            backend = MagicMock()
            mock_fn.return_value = backend
            yield backend

    @pytest.fixture
    def mock_seats(self, raw_trip):
        return {"trip_info": raw_trip, "seats": {"1": "available", "2": "reserved"}}

    @pytest.fixture
    def mock_seats_serialized(self, trip):
        return {"trip_info": trip, "seats": {"1": "available", "2": "reserved"}}

    @pytest.mark.django_db
    def test_list_url_and_view(self, client, mock_backend, trip, raw_trip):
        url = reverse("tickets-depot:trip-list")
        mock_backend.list_trips.return_value = [raw_trip]

        response = client.get(url, {"origin": "Ialoveni", "destination": "Hincesti"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [trip]
        mock_backend.list_trips.assert_called_once_with("Ialoveni", "Hincesti")

    @pytest.mark.django_db
    def test_retrieve_success(self, client, mock_backend, raw_trip, trip):
        url = reverse("tickets-depot:trip-detail", kwargs={"pk": 1})
        mock_backend.get_trip.return_value = raw_trip

        response = client.get(url, {"origin": "Ialoveni", "destination": "Hincesti"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == trip
        mock_backend.get_trip.assert_called_once_with(1, "Ialoveni", "Hincesti")

    @pytest.mark.django_db
    def test_retrieve_not_found(self, client, mock_backend):
        url = reverse("tickets-depot:trip-detail", kwargs={"pk": 999})
        mock_backend.get_trip.return_value = None

        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Trip not found."

    @pytest.mark.django_db
    def test_seats_success(
        self, client, mock_backend, mock_seats, mock_seats_serialized, raw_trip, trip
    ):
        url = reverse("tickets-depot:trip-seats", kwargs={"pk": 1})
        mock_backend.get_seat_info.return_value = mock_seats

        response = client.get(url, {"origin": "Ialoveni", "destination": "Hincesti"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_seats_serialized
        mock_backend.get_seat_info.assert_called_once_with(1, "Ialoveni", "Hincesti")

    @pytest.mark.django_db
    def test_seats_not_found(self, client, mock_backend):
        url = reverse("tickets-depot:trip-seats", kwargs={"pk": 999})
        mock_backend.get_seat_info.return_value = None

        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Trip not found."

    @pytest.mark.django_db
    def test_cancel_tickets(self, client, paid_ticket):
        url = reverse(
            "tickets-depot:trip-cancel-tickets", kwargs={"pk": paid_ticket.id}
        )

        with patch.object(
            Ticket.objects,
            "cancel_for_trip",
            return_value={"cancelled": [1], "failed": []},
        ) as mock_cancel:
            response = client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"cancelled": [1], "failed": []}
        mock_cancel.assert_called_once_with(str(paid_ticket.id))
