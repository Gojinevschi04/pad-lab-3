import logging

from celery import Task, shared_task
from django.contrib.auth import get_user_model
from django.forms import model_to_dict
from django.utils import timezone

from tickets.core.models import Ticket
from tickets.core.services.email_service import EmailType, TicketEmailService
from tickets.core.services.ticket_pdf_service import TicketPDFService
from tickets.core.services.trip_reminder_service import TripReminderService
from tickets.core.services.trip_service import TripService
from tickets.depot.backends.base import get_depot_backend
from tickets.treasury.backends.base import get_treasury_backend

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseTask(Task):
    autoretry_for = (RuntimeError,)
    max_retries = 3
    retry_backoff = True
    retry_jitter = True


@shared_task(base=BaseTask)
def generate_ticket_pdf(ticket_id: int) -> None:
    ticket: Ticket = Ticket.objects.get(id=ticket_id)
    service: TicketPDFService = TicketPDFService()
    filename: str = f"ticket_{ticket.id}.pdf"
    service.create_and_store_pdf(ticket, filename)


@shared_task(base=BaseTask)
def send_ticket_email(ticket_id: int) -> None:
    ticket: Ticket = Ticket.objects.get(id=ticket_id)
    user: User = ticket.user

    email_service: TicketEmailService = TicketEmailService()
    email_service.send_ticket_email(
        to_email=user.email,
        ticket=ticket,
        data={
            "user_name": user.get_full_name() or user.username,
            "trip_id": ticket.trip_id,
        },
    )


@shared_task(base=BaseTask)
def send_trip_cancellation_email(ticket_id: int) -> None:
    ticket: Ticket = Ticket.objects.get(id=ticket_id)
    user: User = ticket.user
    service = TripService(get_depot_backend())

    trip_dict = service.fetch_and_serialize_trip(
        ticket.trip_id, ticket.origin, ticket.destination
    )

    email_service: TicketEmailService = TicketEmailService()
    email_service.send_trip_email(
        to_email=user.email,
        data={
            "user_name": user.get_full_name() or user.username,
            "trip_id": ticket.trip_id,
            "trip_date": trip_dict.get("date"),
            "trip_time": trip_dict.get("start_time"),
            "trip_from": trip_dict.get("origin"),
            "trip_to": trip_dict.get("destination"),
        },
        email_type=EmailType.TRIP_CANCELLATION,
    )


@shared_task
def send_upcoming_trip_reminders():
    service: TripReminderService = TripReminderService()
    service.process_reminders()


@shared_task
def expire_unpaid_tickets() -> None:
    now = timezone.now()
    tickets = Ticket.objects.filter(
        status=Ticket.Status.RESERVED,
        reserved_until__lt=now,
    )
    for ticket in tickets:
        ticket.status = Ticket.Status.EXPIRED
        ticket.save()


@shared_task
def expire_ticket(ticket_id: int) -> None:
    try:
        ticket: Ticket = Ticket.objects.get(pk=ticket_id)
    except Ticket.DoesNotExist:
        return

    if ticket.status != Ticket.Status.RESERVED:
        # Already paid or cancelled
        return

    if ticket.reserved_until and ticket.reserved_until <= timezone.now():
        ticket.status = Ticket.Status.EXPIRED
        ticket.save()


@shared_task(base=BaseTask)
def send_ticket_payment(ticket_id: int) -> None:
    ticket = Ticket.objects.get(id=ticket_id)
    ticket_dict = model_to_dict(ticket)
    user = model_to_dict(ticket.user)

    service = TripService(get_depot_backend())
    trip = service.fetch_and_serialize_trip(
        ticket.trip_id, ticket.origin, ticket.destination
    )

    treasury_backend = get_treasury_backend()
    treasury_backend.pay_ticket(user, ticket_dict, trip)


@shared_task(base=BaseTask)
def refund_ticket(ticket_id: int) -> None:
    ticket = Ticket.objects.get(id=ticket_id)
    ticket_payload = model_to_dict(ticket)
    treasury_backend = get_treasury_backend()
    treasury_backend.refund_ticket(ticket_payload)


@shared_task(base=BaseTask)
def refund_cancelled_tickets(ticket_ids: list[int]) -> None:
    treasury_backend = get_treasury_backend()
    tickets = Ticket.objects.filter(id__in=ticket_ids)

    for ticket in tickets:
        ticket_payload = model_to_dict(ticket)
        treasury_backend.refund_ticket(ticket_payload)


@shared_task(base=BaseTask)
def send_trip_cancellation_emails(ticket_ids: list[int]) -> None:
    service = TripService(get_depot_backend())
    email_service = TicketEmailService()

    tickets = Ticket.objects.filter(id__in=ticket_ids).select_related("user")

    for ticket in tickets:
        trip_dict = service.fetch_and_serialize_trip(
            ticket.trip_id, ticket.origin, ticket.destination
        )

        email_service.send_trip_email(
            to_email=ticket.user.email,
            data={
                "user_name": ticket.user.get_full_name() or ticket.user.username,
                "trip_id": ticket.trip_id,
                "trip_date": trip_dict.get("date"),
                "trip_time": trip_dict.get("start_time"),
                "trip_from": trip_dict.get("origin"),
                "trip_to": trip_dict.get("destination"),
            },
            email_type=EmailType.TRIP_CANCELLATION,
        )
