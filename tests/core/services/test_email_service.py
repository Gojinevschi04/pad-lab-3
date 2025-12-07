from unittest.mock import MagicMock, patch

import pytest
from django.core.mail import EmailMessage

from tickets.core.services.email_service import EmailType, TicketEmailService


@pytest.fixture
def service():
    return TicketEmailService()


@patch("tickets.core.services.email_service.render_to_string")
def test_render_email(mock_render, service):
    mock_render.return_value = "<p>Hi!</p>"

    email = service._render_email(
        to_email="test@example.com",
        subject="Test Subject",
        template_name="emails/sample_template.html",
        context={"key": "value"},
    )

    mock_render.assert_called_once_with("emails/sample_template.html", {"key": "value"})
    assert isinstance(email, EmailMessage)
    assert email.subject == "Test Subject"
    assert email.body == "<p>Hi!</p>"
    assert email.to == ["test@example.com"]
    assert email.content_subtype == "html"


@patch("tickets.core.services.email_service.render_to_string")
@patch("tickets.core.services.email_service.TicketPDFService.download_content")
@patch("tickets.core.services.email_service.EmailMessage")
def test_send_ticket_email(
    mock_email_cls, mock_pdf_download, mock_render, service, paid_ticket
):
    mock_render.return_value = "Email body"
    mock_pdf_download.return_value = b"PDF content"

    email_instance = MagicMock()
    mock_email_cls.return_value = email_instance

    paid_ticket.file = MagicMock()
    paid_ticket.file.name = "tickets/ticket_123.pdf"

    service.send_ticket_email(
        to_email="user@example.com",
        ticket=paid_ticket,
        data={
            "subject": "Your Ticket",
            "user_name": "Test User",
            "trip_id": paid_ticket.trip_id,
        },
    )

    mock_email_cls.assert_called_once_with(
        subject="Your Ticket",
        body="Email body",
        to=["user@example.com"],
    )
    mock_pdf_download.assert_called_once_with(paid_ticket)
    email_instance.attach.assert_called_once_with(
        "ticket_123.pdf", b"PDF content", "application/pdf"
    )
    email_instance.send.assert_called_once()


@patch("tickets.core.services.email_service.TicketEmailService._render_email")
def test_send_trip_email_calls_render(mock_render, service):
    mock_email_instance = MagicMock()
    mock_render.return_value = mock_email_instance

    data = {
        "user_name": "User Test",
        "trip_date": "2025-08-01",
        "trip_time": "10:00",
        "trip_from": "City A",
        "trip_to": "City B",
    }

    service.send(
        to_email="test@example.com",
        email_type=EmailType.TRIP_CANCELLATION,
        context=data,
        subject=data.get("subject"),
    )

    mock_render.assert_called_once_with(
        to_email="test@example.com",
        subject="Your trip has been cancelled",
        template_name="emails/trip_cancellation_email.html",
        context=data,
        attachments=None,
    )
    mock_email_instance.send.assert_called_once()


@patch("tickets.core.services.email_service.TicketEmailService._render_email")
def test_send_trip_email_with_reminder(mock_render, service):
    mock_email_instance = MagicMock()
    mock_render.return_value = mock_email_instance

    data = {
        "user_name": "User Test",
        "trip_date": "2025-08-01",
        "trip_time": "10:00",
        "trip_from": "City A",
        "trip_to": "City B",
    }

    service.send(
        to_email="test@example.com", email_type=EmailType.TRIP_REMINDER, context=data
    )

    mock_render.assert_called_once_with(
        to_email="test@example.com",
        subject="Your trip reminder",
        template_name="emails/trip_reminder_email.html",
        context=data,
        attachments=None,
    )
    mock_email_instance.send.assert_called_once()
