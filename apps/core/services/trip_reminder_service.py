from datetime import datetime, timedelta

from django.utils import timezone

from tickets.core.models import Ticket
from tickets.core.services.email_service import TicketEmailService
from tickets.depot.backends.base import get_depot_backend
from tickets.depot.serializers import TripSerializer


class TripReminderService:
    REMINDER_INTERVALS: list[int] = [24, 1]

    def __init__(self, email_service: TicketEmailService | None = None) -> None:
        self.email_service: TicketEmailService = email_service or TicketEmailService()
        self.backend = get_depot_backend()

    def process_reminders(self) -> None:
        now: datetime = timezone.now()

        for hours in self.REMINDER_INTERVALS:
            self._send_reminders_for_interval(now, hours)

    def _send_reminders_for_interval(self, now: datetime, hours: int) -> None:
        reminder_time: datetime = now + timedelta(hours=hours)
        reminder_date = reminder_time.date()
        reminder_hour = reminder_time.time().hour

        tickets = Ticket.objects.filter(
            status=Ticket.Status.PAID,
        ).select_related("user")

        for ticket in tickets:
            raw_trip = self.backend.get_trip(
                ticket.trip_id, ticket.origin, ticket.destination
            )
            serialized_trip = TripSerializer(raw_trip).data

            if not serialized_trip:
                continue

            if (
                serialized_trip["date"] == reminder_date
                and serialized_trip["start_time"].hour == reminder_hour
            ):
                user = ticket.user

                email_data: dict[str, str] = {
                    "user_name": user.get_full_name() or user.username,
                    "trip_date": str(serialized_trip["date"]),
                    "trip_time": str(serialized_trip["start_time"]),
                    "trip_from": ticket.origin,
                    "trip_to": ticket.destination,
                    "subject": f"Reminder: Your trip is in {hours} hour(s)!",
                }

                self.email_service.send_trip_reminder(
                    to_email=user.email,
                    data=email_data,
                )
