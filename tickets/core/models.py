from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from tickets.core.exceptions import SeatAlreadyTakenError

User = get_user_model()


def default_reserved_until():
    return timezone.now() + timedelta(minutes=15)


class TicketQuerySet(models.QuerySet):
    def annotate_is_expired(self):
        return self.annotate(
            is_expired=models.Case(
                models.When(reserved_until__lt=timezone.now(), then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField(),
            )
        )

    def taken_seats(self, trip_id: int) -> list[int]:
        return list(
            self.filter(trip_id=trip_id, is_expired=False)
            .values_list("seat_number", flat=True)
            .order_by("seat_number")
        )

    def is_seat_taken(self, trip_id: int, seat_number: int) -> bool:
        return self.filter(
            trip_id=trip_id, seat_number=seat_number, is_expired=False
        ).exists()

    def currently_active(self) -> QuerySet:
        return self.filter(status__in=["paid", "reserved"])

    def of_trip(self, trip_id: int) -> QuerySet:
        return self.filter(trip_id=trip_id)

    def active_for_trip(self, trip_id) -> QuerySet:
        return self.currently_active().of_trip(trip_id)

    def group_by_status(self):
        paid_tickets = self.filter(status="paid", can_cancel=True)
        reserved_tickets = self.filter(status="reserved", can_cancel=True)
        failed_tickets = self.filter(can_cancel=False)

        return paid_tickets, reserved_tickets, failed_tickets

    def paid(self) -> QuerySet:
        return self.filter(status=Ticket.Status.PAID)

    def within_date_range(self, start_date=None, end_date=None) -> QuerySet:
        queryset = self

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset


class TicketManager(models.Manager):
    def get_queryset(self):
        return TicketQuerySet(self.model, using=self._db).annotate_is_expired()

    def taken_seats(self, trip_id: int) -> set[int]:
        return self.get_queryset().taken_seats(trip_id)

    def is_seat_taken(self, trip_id: int, seat_number: int) -> list[int]:
        return self.get_queryset().is_seat_taken(trip_id, seat_number)

    def invoice_exists(self, invoice_id: str) -> bool:
        return self.filter(invoice_id=invoice_id).exists()

    def sales_count(self, start_date=None, end_date=None):
        return (
            self.get_queryset().paid().within_date_range(start_date, end_date).count()
        )

    def paid(self):
        return self.get_queryset().paid()

    def currently_active(self) -> TicketQuerySet:
        return self.get_queryset().currently_active()

    def of_trip(self, trip_id: int) -> TicketQuerySet:
        return self.get_queryset().of_trip(trip_id)

    def active_for_trip(self, trip_id) -> TicketQuerySet:
        return self.get_queryset().active_for_trip(trip_id)

    def create_ticket(self, **data):
        trip_id = data["trip_id"]
        seat_number = data["seat_number"]

        if self.model.objects.is_seat_taken(trip_id, seat_number):
            raise SeatAlreadyTakenError("Seat already taken.")

        ticket = self.model(**data)
        ticket.status = ticket.Status.RESERVED
        ticket.reserved_until = timezone.now() + timedelta(minutes=15)
        ticket.save()

        from tickets.core.tasks import expire_ticket, send_ticket_payment

        expire_ticket.apply_async((ticket.id,), eta=ticket.reserved_until)
        send_ticket_payment.delay(ticket.id)

        return ticket

    def cancel_for_trip(self, trip_id):
        tickets = self.active_for_trip(trip_id)

        if not tickets.exists():
            return {"cancelled": [], "failed": []}

        paid_queryset, reserved_queryset, failed_queryset = tickets.group_by_status()

        with transaction.atomic():
            cancelled_queryset = paid_queryset | reserved_queryset
            cancelled_queryset.update(status=Ticket.Status.CANCELLED)

        refund_ids = list(paid_queryset.values_list("id", flat=True))
        cancelled_ids = list(cancelled_queryset.values_list("id", flat=True))

        if cancelled_ids:
            from tickets.core.tasks import (
                refund_cancelled_tickets,
                send_trip_cancellation_emails,
            )

            refund_cancelled_tickets.delay(refund_ids)
            send_trip_cancellation_emails.delay(cancelled_ids)

        return {
            "cancelled": list(cancelled_queryset.values("id", "status")),
            "failed": list(failed_queryset.values("id", "status")),
        }


class Ticket(models.Model):
    objects = TicketManager()
    is_expired: bool  # annotated from manager

    class Status(models.TextChoices):
        RESERVED = "reserved", _("Reserved")
        PAID = "paid", _("Paid")
        CANCELLED = "cancelled", _("Cancelled")
        EXPIRED = "expired", _("Expired")
        USED = "used", _("Used")

    price = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    trip_id = models.IntegerField(null=True)
    origin = models.CharField(
        max_length=200,
        validators=[
            MinLengthValidator(3),
        ],
        null=True,
        blank=True,
    )
    destination = models.CharField(
        max_length=200,
        validators=[
            MinLengthValidator(3),
        ],
        null=True,
        blank=True,
    )
    seat_number = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    status = models.CharField(
        max_length=10,
        choices=Status,
        default=Status.RESERVED,
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tickets", null=True, blank=True
    )
    invoice_id = models.CharField(null=True, blank=True, unique=True, max_length=100)
    refund_id = models.CharField(null=True, blank=True, unique=True, max_length=100)
    reserved_until = models.DateTimeField(
        default=default_reserved_until, null=True, blank=True
    )
    file = models.FileField(upload_to="tickets/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    can_cancel = models.GeneratedField(
        expression=models.ExpressionWrapper(
            models.Q(status__in=["reserved", "paid"]),
            output_field=models.BooleanField(),
        ),
        db_persist=True,
        output_field=models.BooleanField(),
    )
    can_confirm = models.GeneratedField(
        expression=models.ExpressionWrapper(
            models.Q(status__in=["reserved"]),
            output_field=models.BooleanField(),
        ),
        db_persist=True,
        output_field=models.BooleanField(),
    )

    @property
    def description(self):
        return f"Ticket from {self.origin} to {self.destination}"

    def __str__(self):
        return self.description

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def cancel(self):
        if not self.can_cancel:
            raise ValidationError(
                f"Cannot cancel a ticket with status '{self.status}'."
            )

        if self.status == self.Status.PAID:
            from tickets.core.tasks import refund_ticket

            refund_ticket.delay(self.id)

        self.status = self.Status.CANCELLED
        self.save()

    def confirm(self, invoice_id: str):
        if not self.can_confirm:
            raise ValidationError(
                f"Cannot confirm a ticket with status '{self.status}'."
            )

        self.status = self.Status.PAID
        self.invoice_id = invoice_id
        self.save()

        from tickets.core.tasks import generate_ticket_pdf, send_ticket_email

        generate_ticket_pdf.delay(self.id)
        send_ticket_email.delay(self.id)
