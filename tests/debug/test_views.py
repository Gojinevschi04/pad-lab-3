import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTicketEmailViewSet:
    def test_send_ticket_email_success(self, auth_client, user, ticket, mocker):
        ticket.user = user
        ticket.save()

        mock_task = mocker.patch("tickets.core.tasks.send_ticket_email.delay")

        url = reverse(
            "debug:ticket-emails-send-ticket-email-action", kwargs={"pk": ticket.id}
        )
        response = auth_client.post(url)

        assert response.status_code == 200
        assert response.data["detail"] == "Ticket email sent."
        mock_task.assert_called_once_with(ticket.id)

    def test_send_ticket_email_not_found(self, auth_client):
        url = reverse(
            "debug:ticket-emails-send-ticket-email-action", kwargs={"pk": 9999}
        )
        response = auth_client.post(url)

        assert response.status_code == 404

    def test_send_ticket_email_not_owner(self, auth_client, other_user, ticket):
        ticket.user = other_user
        ticket.save()

        url = reverse(
            "debug:ticket-emails-send-ticket-email-action", kwargs={"pk": ticket.id}
        )
        response = auth_client.post(url)

        assert response.status_code == 404

    def test_send_ticket_email_unauthenticated(self, client, ticket):
        url = reverse(
            "debug:ticket-emails-send-ticket-email-action", kwargs={"pk": ticket.id}
        )
        response = client.post(url)

        assert response.status_code in (401, 403)

    def test_send_cancellation_email_success(self, auth_client, user, ticket, mocker):
        ticket.user = user
        ticket.save()

        mock_task = mocker.patch(
            "tickets.core.tasks.send_trip_cancellation_email.delay"
        )

        url = reverse(
            "debug:ticket-emails-send-cancellation-email-action",
            kwargs={"pk": ticket.id},
        )
        response = auth_client.post(url)

        assert response.status_code == 200
        assert response.data["detail"] == "Trip cancellation email sent."
        mock_task.assert_called_once_with(ticket.id)

    def test_send_reminders_success(self, auth_client, mocker):
        mock_service = mocker.patch(
            "tickets.debug.views.TripReminderService.process_reminders"
        )

        url = reverse("debug:ticket-emails-send-reminders-action")
        response = auth_client.post(url)

        assert response.status_code == 200
        assert response.data["detail"] == "Reminder emails sent."
        mock_service.assert_called_once()
