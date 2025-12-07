from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from tickets.core import tasks
from tickets.core.models import Ticket

User = get_user_model()


@pytest.mark.django_db
@patch("tickets.core.tasks.TicketPDFService")
def test_generate_ticket_pdf(mock_pdf_service):
    ticket = Ticket.objects.create(
        user=User.objects.create(username="testuser"), trip_id=1
    )
    mock_service_instance = mock_pdf_service.return_value

    tasks.generate_ticket_pdf(ticket.id)

    mock_pdf_service.assert_called_once()
    mock_service_instance.create_and_store_pdf.assert_called_once_with(
        ticket, f"ticket_{ticket.id}.pdf"
    )


@pytest.mark.django_db
@patch("tickets.core.tasks.TicketEmailService")
def test_send_ticket_email(mock_email_service):
    user = User.objects.create(username="testuser", email="test@example.com")
    ticket = Ticket.objects.create(user=user, trip_id=42)
    mock_service_instance = mock_email_service.return_value

    tasks.send_ticket_email(ticket.id)

    mock_email_service.assert_called_once()
    mock_service_instance.send_ticket_email.assert_called_once_with(
        to_email=user.email,
        ticket=ticket,
        data={
            "user_name": user.get_full_name() or user.username,
            "trip_id": ticket.trip_id,
        },
    )


@patch("tickets.core.tasks.TripReminderService")
def test_send_upcoming_trip_reminders(mock_reminder_service):
    mock_service_instance = mock_reminder_service.return_value

    tasks.send_upcoming_trip_reminders()

    mock_reminder_service.assert_called_once()
    mock_service_instance.process_reminders.assert_called_once()


@pytest.mark.django_db
def test_expire_unpaid_tickets(expired_ticket):
    now = timezone.now()
    user = User.objects.create(username="user1")

    Ticket.objects.create(
        user=user,
        trip_id=11,
        seat_number="2",
        status=Ticket.Status.RESERVED,
        reserved_until=now.replace(year=now.year + 1),
    )

    tasks.expire_unpaid_tickets()

    expired_ticket.refresh_from_db()
    assert expired_ticket.status == Ticket.Status.EXPIRED


@pytest.mark.django_db
def test_expire_ticket_no_ticket():
    tasks.expire_ticket(99999)


@pytest.mark.django_db
def test_expire_ticket_status_not_reserved(paid_ticket):
    tasks.expire_ticket(paid_ticket.id)

    paid_ticket.refresh_from_db()
    assert paid_ticket.status == Ticket.Status.PAID
