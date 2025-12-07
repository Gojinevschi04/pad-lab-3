from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from tickets.core.models import Ticket

User = get_user_model()


@pytest.fixture(autouse=True)
def mock_ticket_tasks():
    with (
        patch("tickets.core.tasks.refund_ticket.delay") as mock_refund,
        patch("tickets.core.tasks.generate_ticket_pdf.delay") as mock_pdf,
        patch("tickets.core.tasks.expire_ticket.apply_async") as mock_expire,
        patch("tickets.core.tasks.send_ticket_payment.delay") as mock_payment,
        patch("tickets.core.tasks.send_ticket_email.delay") as mock_email,
    ):
        yield {
            "refund": mock_refund,
            "pdf": mock_pdf,
            "email": mock_email,
            "expire": mock_expire,
            "payment": mock_payment,
        }


@pytest.mark.django_db
class TestTicketViews:
    def test_list_only_returns_user_tickets(
        self, auth_client, reserved_ticket, other_reserved_ticket
    ):
        url = reverse("tickets-core:ticket-list")
        response = auth_client.get(url)

        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 1
        assert results[0]["id"] == reserved_ticket.id

    def test_retrieve_ticket_success(self, auth_client, reserved_ticket):
        url = reverse("tickets-core:ticket-detail", kwargs={"pk": reserved_ticket.id})
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == reserved_ticket.id

    def test_retrieve_ticket_forbidden(self, auth_client, other_reserved_ticket):
        url = reverse(
            "tickets-core:ticket-detail", kwargs={"pk": other_reserved_ticket.id}
        )
        response = auth_client.get(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestTicketCreation:
    @pytest.fixture(autouse=True)
    def patch_backend(self, mocker, raw_trip):
        mock_backend = MagicMock()
        mock_backend.get_trip.return_value = raw_trip
        mocker.patch("tickets.core.views.get_depot_backend", return_value=mock_backend)

    def test_create_ticket_success(self, auth_client, trip, mock_ticket_tasks):
        url = reverse("tickets-core:ticket-list")
        payload = {
            "trip_id": trip["id"],
            "seat_number": 1,
            "origin": trip["origin"],
            "destination": trip["destination"],
        }

        response = auth_client.post(url, data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["trip_id"] == trip["id"]
        assert response.data["seat_number"] == 1
        assert response.data["status"] == "reserved"
        assert "reserved_until" in response.data

        mock_ticket_tasks["payment"].assert_called_once()
        mock_ticket_tasks["expire"].assert_called_once()

    def test_create_ticket_invalid_trip_id_negative(self, auth_client, trip, mocker):
        url = reverse("tickets-core:ticket-list")
        payload = {
            "trip_id": -5000,
            "seat_number": 1,
            "origin": trip["origin"],
            "destination": trip["destination"],
        }

        mock_backend = MagicMock()
        mock_backend.get_trip.return_value = None
        mocker.patch("tickets.core.views.get_depot_backend", return_value=mock_backend)

        response = auth_client.post(url, data=payload)
        assert response.status_code == 400
        assert "trip_id" in response.data or "Cannot fetch trip" in str(response.data)

    def test_create_ticket_invalid_seat_number_out_of_range(self, auth_client, trip):
        url = reverse("tickets-core:ticket-list")
        payload = {
            "trip_id": trip["id"],
            "seat_number": 999,
            "origin": trip["origin"],
            "destination": trip["destination"],
        }

        response = auth_client.post(url, data=payload)

        assert response.status_code == 400
        assert "non_field_errors" in response.data or "seat_number" in response.data

    def test_create_ticket_with_already_taken_seat(self, auth_client, trip, user):
        Ticket.objects.create(
            trip_id=trip["id"],
            seat_number=5,
            user=user,
        )

        url = reverse("tickets-core:ticket-list")
        payload = {
            "trip_id": trip["id"],
            "seat_number": 5,
            "origin": trip["origin"],
            "destination": trip["destination"],
        }

        response = auth_client.post(url, data=payload)

        assert response.status_code == 400
        assert "non_field_errors" in response.data or "seat_number" in response.data
        assert response.data["non_field_errors"][0] == "Seat is already taken."

    def test_create_ticket_trip_id_does_not_exist(self, auth_client, trip, mocker):
        mock_backend = MagicMock()
        mock_backend.get_trip.return_value = None
        mocker.patch("tickets.core.views.get_depot_backend", return_value=mock_backend)

        url = reverse("tickets-core:ticket-list")
        payload = {
            "trip_id": 9999,
            "seat_number": 1,
            "origin": trip["origin"],
            "destination": trip["destination"],
        }

        response = auth_client.post(url, data=payload)

        assert response.status_code == 400
        assert "Cannot fetch trip" in str(response.data)


@pytest.mark.django_db
class TestTicketConfirmation:
    def test_confirm_ticket_success(
        self, auth_client, reserved_ticket, mock_ticket_tasks
    ):
        url = reverse("tickets-core:ticket-confirm")
        payload = {"ticket_id": reserved_ticket.id, "invoice_id": "INV-123"}

        response = auth_client.post(url, data=payload)

        assert response.status_code == 200
        assert response.data["message"] == "Ticket confirmed."

        reserved_ticket.refresh_from_db()
        assert reserved_ticket.status == Ticket.Status.PAID
        assert reserved_ticket.invoice_id == "INV-123"

        mock_ticket_tasks["pdf"].assert_called_once_with(reserved_ticket.id)
        mock_ticket_tasks["email"].assert_called_once_with(reserved_ticket.id)

    def test_confirm_ticket_invalid_ticket_id(self, auth_client):
        url = reverse("tickets-core:ticket-confirm")
        payload = {"ticket_id": 99999, "invoice_id": "INV-123"}

        response = auth_client.post(url, data=payload)

        assert response.status_code == 400
        assert "ticket_id" in response.data
        assert response.data["ticket_id"] == ["Ticket not found."]

    def test_confirm_ticket_duplicate_invoice(
        self, auth_client, reserved_ticket, paid_ticket
    ):
        url = reverse("tickets-core:ticket-confirm")
        payload = {"ticket_id": reserved_ticket.id, "invoice_id": "INV-EXISTING"}

        response = auth_client.post(url, data=payload)

        assert response.status_code == 400
        assert "invoice_id" in response.data
        assert response.data["invoice_id"] == [
            "This invoice is already associated with another ticket."
        ]

    def test_confirm_ticket_cannot_be_confirmed(self, auth_client, reserved_ticket):
        reserved_ticket.status = Ticket.Status.PAID
        reserved_ticket.save()

        url = reverse("tickets-core:ticket-confirm")
        payload = {"ticket_id": reserved_ticket.id, "invoice_id": "INV-NEW"}

        response = auth_client.post(url, data=payload)

        assert response.status_code == 400
        assert "detail" in response.data
        assert "Cannot confirm a ticket" in response.data["detail"]

    def test_confirm_ticket_missing_fields(self, auth_client):
        url = reverse("tickets-core:ticket-confirm")
        response = auth_client.post(url, data={})

        assert response.status_code == 400
        assert "ticket_id" in response.data
        assert "This field is required." in response.data["ticket_id"]


@pytest.mark.django_db
class TestTicketCancellation:
    def test_cancel_reserved_ticket_success(self, auth_client, user, reserved_ticket):
        reserved_ticket.status = Ticket.Status.RESERVED
        reserved_ticket.user = user
        reserved_ticket.save()

        url = reverse("tickets-core:ticket-cancel", kwargs={"pk": reserved_ticket.id})
        response = auth_client.post(url)

        assert response.status_code == 200
        assert response.data["status"] == Ticket.Status.CANCELLED
        assert response.data["message"] == "Ticket cancelled."

        reserved_ticket.refresh_from_db()
        assert reserved_ticket.status == Ticket.Status.CANCELLED

    def test_cancel_paid_ticket_triggers_refund(
        self, auth_client, user, paid_ticket, mocker
    ):
        mock_refund = mocker.patch("tickets.core.tasks.refund_ticket.delay")

        url = reverse("tickets-core:ticket-cancel", kwargs={"pk": paid_ticket.id})
        response = auth_client.post(url)

        assert response.status_code == 200
        assert response.data["status"] == Ticket.Status.CANCELLED
        assert response.data["message"] == "Ticket cancelled."
        mock_refund.assert_called_once_with(paid_ticket.id)

    def test_cancel_invalid_status_ticket(self, auth_client, user, reserved_ticket):
        reserved_ticket.status = Ticket.Status.USED
        reserved_ticket.user = user
        reserved_ticket.save()

        url = reverse("tickets-core:ticket-cancel", kwargs={"pk": reserved_ticket.id})
        response = auth_client.post(url)

        assert response.status_code == 400
        assert "detail" in response.data
        assert (
            f"Cannot cancel a ticket with status '{Ticket.Status.USED}'"
            in response.data["detail"]
        )

    def test_cancel_ticket_not_found(self, auth_client):
        url = reverse("tickets-core:ticket-cancel", kwargs={"pk": 9999})
        response = auth_client.post(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestTicketPresignedURL:
    @pytest.fixture
    def mock_pdf_service(self, monkeypatch):
        class MockPDFService:
            def __init__(self, return_url=None, raise_error=False):
                self.return_url = return_url
                self.raise_error = raise_error

            def get_download_url(self, ticket):
                if self.raise_error:
                    raise ValueError("No PDF available for this ticket.")
                return self.return_url or f"https://example.com/{ticket.id}.pdf"

        service = MockPDFService()
        monkeypatch.setattr(
            "tickets.core.views.pdf_service.get_download_url", service.get_download_url
        )
        return service

    def test_presigned_url_success(self, auth_client, paid_ticket, mock_pdf_service):
        mock_pdf_service.return_url = "https://example.com/presigned.pdf"

        url = reverse("tickets-core:ticket-presigned", kwargs={"pk": paid_ticket.id})
        response = auth_client.get(url)

        assert response.status_code == 200
        assert "presigned_url" in response.data
        assert response.data["presigned_url"] == "https://example.com/presigned.pdf"

    def test_presigned_url_pdf_not_ready(
        self, auth_client, paid_ticket, mock_pdf_service
    ):
        mock_pdf_service.raise_error = True

        url = reverse("tickets-core:ticket-presigned", kwargs={"pk": paid_ticket.id})
        response = auth_client.get(url)

        assert response.status_code == 400
        assert "error" in response.data
        assert "PDF not available yet" in response.data["error"]
