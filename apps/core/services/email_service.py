from dataclasses import dataclass
from enum import Enum
from typing import Any

from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from tickets.core.models import Ticket
from tickets.core.services.ticket_pdf_service import TicketPDFService


@dataclass(frozen=True)
class EmailMeta:
    template: str
    default_subject: str


class EmailType(Enum):
    TICKET_PDF = EmailMeta(
        template="emails/ticket_pdf_email.html", default_subject="Your Ticket PDF"
    )
    TRIP_REMINDER = EmailMeta(
        template="emails/trip_reminder_email.html", default_subject="Your trip reminder"
    )
    TRIP_CANCELLATION = EmailMeta(
        template="emails/trip_cancellation_email.html",
        default_subject="Your trip has been cancelled",
    )


class TicketEmailService:
    def __init__(self):
        self.pdf_service = TicketPDFService()

    def _render_email(
        self,
        *,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        attachments: dict[str, bytes | str] | None = None,
    ) -> EmailMessage:
        body = render_to_string(template_name, context)
        email = EmailMessage(subject=subject, body=body, to=[to_email])
        email.content_subtype = "html"

        if attachments:
            for filename, content in attachments.items():
                if isinstance(content, bytes):
                    email.attach(filename, content, "application/pdf")
                else:
                    email.attach_file(content)

        return email

    def send(
        self,
        *,
        to_email: str,
        email_type: EmailType,
        context: dict,
        subject: str | None = None,
        attachments: dict[str, bytes | str] | None = None,
    ):
        meta = email_type.value
        final_subject = subject or meta.default_subject
        template = meta.template

        email = self._render_email(
            to_email=to_email,
            subject=final_subject,
            template_name=template,
            context=context,
            attachments=attachments,
        )
        email.send()

    def send_ticket_email(
        self, to_email: str, ticket: Ticket, data: dict[str, Any]
    ) -> None:
        if not ticket.file:
            filename = f"ticket_{ticket.id}.pdf"
            self.pdf_service.create_and_store_pdf(ticket, filename)

        try:
            pdf_bytes = self.pdf_service.download_content(ticket)
        except Exception as e:
            raise RuntimeError(f"Unable to attach PDF for ticket {ticket.id}: {e}")

        pdf_filename = ticket.file.name.split("/")[-1] if ticket.file else "ticket.pdf"

        self.send(
            to_email=to_email,
            email_type=EmailType.TICKET_PDF,
            context=data,
            attachments={pdf_filename: pdf_bytes},
            subject=data.get("subject"),
        )

    def send_trip_email(self, to_email: str, data: dict, email_type: EmailType) -> None:
        if email_type not in [EmailType.TRIP_REMINDER, EmailType.TRIP_CANCELLATION]:
            raise ValueError("Invalid trip email type")

        self.send(
            to_email=to_email,
            email_type=email_type,
            context=data,
            subject=data.get("subject"),
        )
