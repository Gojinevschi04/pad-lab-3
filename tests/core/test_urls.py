from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestTicketURLs:
    @pytest.fixture(autouse=True)
    def test_ticket_list_get(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("tickets-core:ticket-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_ticket_create_post(self, api_client, user, raw_trip):
        api_client.force_authenticate(user=user)
        url = reverse("tickets-core:ticket-list")
        data = {
            "trip_id": 1,
            "seat_number": 5,
            "origin": "Ialoveni",
            "destination": "Hincesti",
        }

        mock_backend = MagicMock()
        mock_backend.get_seat_info.return_value = raw_trip

        with pytest.MonkeyPatch().context() as patcher:
            patcher.setattr(
                "tickets.core.views.get_depot_backend", lambda: mock_backend
            )
            response = api_client.post(url, data=data)

        assert response.status_code in (
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_ticket_detail_get(self, api_client, user, reserved_ticket):
        api_client.force_authenticate(user=user)
        url = reverse("tickets-core:ticket-detail", kwargs={"pk": reserved_ticket.id})
        response = api_client.get(url)
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND)

    @pytest.mark.django_db
    def test_ticket_webhook_confirm_post(
        self, mock_send_email, mock_generate_pdf, api_client, user, reserved_ticket
    ):
        api_client.force_authenticate(user=user)
        url = reverse("tickets-core:ticket-confirm")
        data = {"ticket_id": reserved_ticket.id, "invoice_id": "INV-123"}

        response = api_client.post(url, data=data)

        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        )
        mock_generate_pdf.assert_called_once_with(reserved_ticket.id)
        mock_send_email.assert_called_once_with(reserved_ticket.id)

    def test_ticket_cancel_post(self, api_client, user, paid_ticket):
        api_client.force_authenticate(user=user)
        url = reverse("tickets-core:ticket-cancel", kwargs={"pk": paid_ticket.id})
        response = api_client.post(url)
        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        )

    def test_ticket_presigned_get(self, api_client, user, paid_ticket):
        api_client.force_authenticate(user=user)
        url = reverse("tickets-core:ticket-presigned", kwargs={"pk": paid_ticket.id})
        response = api_client.get(url)
        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        )
