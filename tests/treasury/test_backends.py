from unittest.mock import MagicMock, patch

import pytest
import requests
from django.core.exceptions import ImproperlyConfigured

from tickets.treasury.backends.base import get_treasury_backend
from tickets.treasury.backends.service import TreasuryClient, TreasuryServiceBackend
from tickets.treasury.exceptions import TreasuryServiceError


class TestGetTreasuryBackend:
    @pytest.mark.django_db
    def test_get_treasury_backend_missing_backend(self, settings):
        settings.TREASURY = {}
        with pytest.raises(ImproperlyConfigured):
            get_treasury_backend()

    @pytest.mark.django_db
    def test_get_treasury_backend_success(self, settings):
        class DummyBackend:
            def __init__(self, client=None, **kwargs):
                self.client = client
                self.kwargs = kwargs

        settings.TREASURY = {
            "backend": "tickets.treasury.backends.base.DummyBackend",
            "options": {"base_url": "http://treasury.fake", "timeout": 7},
        }

        with (
            patch(
                "tickets.treasury.backends.base.import_string",
                return_value=DummyBackend,
            ),
            patch("tickets.treasury.backends.client.TreasuryClient") as mock_client,
        ):
            mock_client.return_value = MagicMock()

            backend = get_treasury_backend()

        mock_client.assert_called_once_with(base_url="http://treasury.fake", timeout=7)

        assert isinstance(backend, DummyBackend)
        assert backend.client == mock_client.return_value


class TestTreasuryClientInit:
    def test_initializes_without_api_key(self):
        client = TreasuryClient(base_url="http://fake")
        assert client.base_url == "http://fake"
        assert client.api_key is None
        assert "Authorization" not in client.headers

    def test_initializes_with_api_key(self):
        client = TreasuryClient(base_url="http://fake", api_key="secret")
        assert client.api_key == "secret"
        assert client.headers["Authorization"] == "Bearer secret"


class TestTreasuryClientRequest:
    def test_request_adds_timeout_and_urljoin(self):
        client = TreasuryClient(base_url="http://fake", timeout=20)

        with patch("requests.Session.request", return_value="mocked") as mock_request:
            result = client.request("get", "/invoices")

        mock_request.assert_called_once_with("get", "http://fake/invoices", timeout=20)
        assert result == "mocked"


class TestTreasuryServiceBackendRequest:
    def test_request_success(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status.return_value = None
        mock_client.request.return_value = mock_response

        backend = TreasuryServiceBackend(client=mock_client)
        result = backend._request("get", "/invoices")

        assert result == {"ok": True}
        mock_client.request.assert_called_once_with("get", "/invoices")

    def test_request_failure_raises(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.RequestException("fail")
        mock_client.request.return_value = mock_response

        backend = TreasuryServiceBackend(client=mock_client)

        with pytest.raises(TreasuryServiceError) as exc:
            backend._request("get", "/bad")

        assert "GET" in str(exc.value) and "/bad" in str(exc.value)


class TestTreasuryServiceBackendPayments:
    def test_pay_ticket_calls_formatter_and_request(self, monkeypatch):
        mock_client = MagicMock()
        backend = TreasuryServiceBackend(client=mock_client)

        fake_data = {"payload": "test"}

        monkeypatch.setattr(
            "tickets.treasury.backends.service.TicketFormatterDict",
            lambda u, t, tr: MagicMock(to_dict=lambda: fake_data),
        )

        backend._request = MagicMock(return_value={"invoice": 123})

        result = backend.pay_ticket({"user": 1}, {"ticket": 2}, {"trip": 3})

        backend._request.assert_called_once_with(
            "post",
            "api/invoices",
            json=fake_data,
        )
        assert result == {"invoice": 123}

    def test_refund_ticket_calls_request(self):
        mock_client = MagicMock()
        backend = TreasuryServiceBackend(client=mock_client)

        backend._request = MagicMock(return_value={"refunded": True})
        data = {"invoice_id": "abc123"}

        result = backend.refund_ticket(data)

        backend._request.assert_called_once_with("post", "api/refund", json=data)
        assert result == {"refunded": True}
