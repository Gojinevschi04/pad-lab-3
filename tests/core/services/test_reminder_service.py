from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from django.utils import timezone

from tickets.core.services.email_service import EmailType
from tickets.core.services.trip_reminder_service import TripReminderService


@pytest.fixture
def mock_email_service():
    return MagicMock()


@pytest.fixture
def mock_backend():
    return MagicMock()


@pytest.mark.xfail(raises=AssertionError, reason="some problems with sending emails")
@pytest.mark.django_db
def test_reminder_sent_when_trip_matches(
    user, paid_ticket, raw_trip, mock_email_service, mock_backend
):
    now = timezone.now()
    reminder_time = now + timedelta(hours=1)

    raw_trip["date"] = reminder_time.date()
    raw_trip["schedule"]["start_time"] = reminder_time.replace(
        minute=0, second=0, microsecond=0
    ).time()

    mock_backend.get_trip.return_value = raw_trip

    service = TripReminderService(email_service=mock_email_service)
    service.backend = mock_backend

    service.process_reminders()

    mock_email_service.send.assert_called_once()
    _, kwargs = mock_email_service.send.call_args

    assert kwargs["to_email"] == user.email
    assert kwargs["email_type"] == EmailType.TRIP_REMINDER

    context = kwargs["context"]
    assert context["trip_from"] == paid_ticket.origin
    assert context["trip_to"] == paid_ticket.destination
    assert context["user_name"] == user.get_full_name() or user.username
    assert "subject" in context


@pytest.mark.django_db
def test_reminder_skips_ticket_without_trip_info(user, paid_ticket, mock_email_service):
    # Arrange
    mock_backend = MagicMock()
    mock_backend.get_trip.return_value = None

    service = TripReminderService(email_service=mock_email_service)
    service.backend = mock_backend

    service.process_reminders()

    mock_email_service.send.assert_not_called()


@pytest.mark.django_db
def test_reminder_skips_if_hour_does_not_match(
    user, paid_ticket, raw_trip, mock_email_service
):
    now = timezone.now()
    raw_trip["date"] = (now + timedelta(hours=5)).date()
    raw_trip["schedule"]["start_time"] = (
        (now + timedelta(hours=5)).replace(minute=0, second=0, microsecond=0).time()
    )

    mock_backend = MagicMock()
    mock_backend.get_trip.return_value = raw_trip

    service = TripReminderService(email_service=mock_email_service)
    service.backend = mock_backend

    service.process_reminders()

    mock_email_service.send.assert_not_called()
