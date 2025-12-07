from io import BytesIO

from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from tickets.core.models import Ticket
from tickets.depot.backends.base import get_depot_backend
from tickets.depot.serializers import TripSerializer


def generate_ticket_file(ticket: Ticket, trip_info: dict[str, str]) -> BytesIO:
    if not trip_info:
        raise ValueError(f"No trip info found for ticket {ticket.id}")

    pdf_file: BytesIO = BytesIO()
    c: canvas = canvas.Canvas(pdf_file, pagesize=letter)

    lines = [
        (750, f"Ticket #{ticket.id}"),
        (730, f"Seat Number: {ticket.seat_number}"),
        (680, f"Trip Number: {trip_info.get('trip_nr') or trip_info.get('id')}"),
        (660, f"Route: {trip_info.get('route_name', '')}"),
        (
            640,
            f"From: {ticket.origin} To: {ticket.destination}",
        ),
        (
            620,
            f"Date: {trip_info.get('date', '')} Start: {trip_info.get('start_time', '')} End: {trip_info.get('end_time', '')}",
        ),
        (
            600,
            f"Bus Model: {trip_info.get('bus_model', '')} ({trip_info.get('bus_plate_number', '')})",
        ),
        (
            580,
            f"Driver: {trip_info.get('driver_name', '')} ({trip_info.get('driver_phone', '')})",
        ),
        (560, f"Price: {ticket.price} MDL"),
    ]

    for y, text in lines:
        c.drawString(100, y, text)

    c.save()
    pdf_file.seek(0)
    return pdf_file


class TicketPDFService:
    def __init__(self) -> None:
        self.backend = get_depot_backend()

    def create_and_store_pdf(self, ticket: Ticket, filename: str) -> None:
        raw_trip = self.backend.get_trip(
            ticket.trip_id, ticket.origin, ticket.destination
        )
        serialized_trip = TripSerializer(raw_trip).data
        pdf_buffer: BytesIO = generate_ticket_file(ticket, serialized_trip)
        name = filename or f"ticket_{ticket.id}.pdf"
        ticket.file.save(name, ContentFile(pdf_buffer.getvalue()), save=True)

    def get_download_url(self, ticket: Ticket) -> str:
        if not ticket.file:
            raise ValueError("No PDF available for this ticket.")
        return ticket.file.url

    def download_content(self, ticket: Ticket) -> bytes:
        if not ticket.file:
            raise ValueError(f"No PDF available for ticket {ticket.id}")
        try:
            return ticket.file.read()
        except Exception as e:
            raise RuntimeError(f"Error reading PDF for ticket {ticket.id}: {e}")
