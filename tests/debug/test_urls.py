import pytest
from django.urls import resolve, reverse

from tickets.debug import views


def test_generate_pdf_url_resolves():
    path = reverse("debug:generate-pdf", kwargs={"ticket_id": 1})
    assert resolve(path).func.view_class == views.GenerateTicketPDFView


def test_admin_stats_url_resolves():
    path = reverse("debug:admin-stats")
    assert resolve(path).func.view_class == views.AdminStatsView


def test_whoami_url_resolves():
    path = reverse("debug:whoami")
    assert resolve(path).func.view_class == views.WhoAmIView


def test_ticket_email_send_ticket_url_resolves():
    path = reverse("debug:ticket-emails-send-ticket-email-action", kwargs={"pk": 1})
    view_class = resolve(path).func.cls
    assert view_class == views.TicketEmailViewSet


def test_ticket_email_send_cancellation_url_resolves():
    path = reverse(
        "debug:ticket-emails-send-cancellation-email-action", kwargs={"pk": 1}
    )
    view_class = resolve(path).func.cls
    assert view_class == views.TicketEmailViewSet


def test_ticket_email_send_reminders_url_resolves():
    path = reverse("debug:ticket-emails-send-reminders-action")
    view_class = resolve(path).func.cls
    assert view_class == views.TicketEmailViewSet


@pytest.mark.django_db
def test_generate_pdf_view(client):
    url = reverse("debug:generate-pdf", kwargs={"ticket_id": 1})
    response = client.get(url)
    assert response.status_code in [200, 403, 404]
