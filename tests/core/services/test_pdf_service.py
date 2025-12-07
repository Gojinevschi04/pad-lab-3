from io import BytesIO
from unittest.mock import MagicMock

import pytest

from tickets.core.services.ticket_pdf_service import (
    TicketPDFService,
    generate_ticket_file,
)


@pytest.mark.django_db
class TestTicketPDFService:
    @pytest.fixture(autouse=True)
    def setup_mock_backend(self, mocker):
        self.mock_backend_patch = mocker.patch(
            "tickets.core.services.ticket_pdf_service.get_depot_backend"
        )
        self.mock_backend_instance = MagicMock()
        self.mock_backend_patch.return_value = self.mock_backend_instance

    @pytest.fixture(autouse=True)
    def override_storage(self, settings):
        settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
        settings.MEDIA_ROOT = "/tmp/test_media"

    def test_generate_ticket_file_success(self, paid_ticket, raw_trip):
        buffer = generate_ticket_file(paid_ticket, raw_trip)
        assert isinstance(buffer, BytesIO)
        content = buffer.getvalue()
        assert content.startswith(b"%PDF")

    def test_create_and_store_pdf_with_mocked_trip(self, paid_ticket, raw_trip):
        self.mock_backend_instance.get_trip.return_value = raw_trip

        service = TicketPDFService()
        service.create_and_store_pdf(paid_ticket, "mock_ticket.pdf")

        paid_ticket.refresh_from_db()
        assert paid_ticket.file.name.endswith("mock_ticket.pdf")
        assert paid_ticket.file.read().startswith(b"%PDF")
        self.mock_backend_instance.get_trip.assert_called_once_with(
            paid_ticket.trip_id, paid_ticket.origin, paid_ticket.destination
        )

    def test_get_download_url_success(self, paid_ticket, raw_trip):
        self.mock_backend_instance.get_trip.return_value = raw_trip
        service = TicketPDFService()
        service.create_and_store_pdf(paid_ticket, "download_ticket.pdf")

        url = service.get_download_url(paid_ticket)
        assert isinstance(url, str)
        assert "download_ticket.pdf" in url

    def test_get_download_url_no_pdf(self, paid_ticket):
        service = TicketPDFService()
        with pytest.raises(ValueError, match="No PDF available for this ticket."):
            service.get_download_url(paid_ticket)

    def test_download_content_success(self, paid_ticket, raw_trip):
        self.mock_backend_instance.get_trip.return_value = raw_trip
        service = TicketPDFService()
        service.create_and_store_pdf(paid_ticket, "ticket.pdf")

        content = service.download_content(paid_ticket)
        assert isinstance(content, bytes)
        assert content.startswith(b"%PDF")

    def test_download_content_no_file(self, paid_ticket):
        service = TicketPDFService()
        with pytest.raises(
            ValueError, match=f"No PDF available for ticket {paid_ticket.id}"
        ):
            service.download_content(paid_ticket)

    def test_download_content_file_read_error(self, paid_ticket, raw_trip, mocker):
        self.mock_backend_instance.get_trip.return_value = raw_trip
        service = TicketPDFService()
        service.create_and_store_pdf(paid_ticket, "error_ticket.pdf")

        mock_file = mocker.Mock()
        mock_file.read.side_effect = OSError("Boom")
        paid_ticket.file = mock_file

        with pytest.raises(
            RuntimeError, match=f"Error reading PDF for ticket {paid_ticket.id}: Boom"
        ):
            service.download_content(paid_ticket)
