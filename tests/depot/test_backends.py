import json
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.core.exceptions import ImproperlyConfigured

from tickets.depot.backends.base import BaseBackend, get_depot_backend
from tickets.depot.backends.json import JsonDepotBackend
from tickets.depot.backends.service import DepotClient, DepotServiceBackend
from tickets.depot.exceptions import DepotServiceError


def test_base_backend_methods_raise():
    backend = BaseBackend()

    with pytest.raises(NotImplementedError):
        backend.list_trips("A", "B")

    with pytest.raises(NotImplementedError):
        backend.get_trip(1, "A", "B")

    with pytest.raises(NotImplementedError):
        backend.get_seat_info(1, "A", "B")


class TestGetDepotBackend:
    @pytest.mark.django_db
    def test_get_depot_backend_missing_backend(self, settings):
        settings.DEPOT = {}
        with pytest.raises(ImproperlyConfigured):
            get_depot_backend()

    @pytest.mark.django_db
    def test_get_depot_backend_success(self, settings):
        class DummyBackend:
            def __init__(self, client=None, **kwargs):
                self.client = client
                self.kwargs = kwargs

        settings.DEPOT = {
            "backend": "tickets.depot.backends.base.DummyBackend",
            "options": {"base_url": "http://fake", "timeout": 5},
        }

        with (
            patch(
                "tickets.depot.backends.base.import_string", return_value=DummyBackend
            ),
            patch("tickets.depot.backends.client.DepotClient") as mock_client,
        ):
            mock_client.return_value = MagicMock()

            backend = get_depot_backend()

        mock_client.assert_called_once_with(base_url="http://fake", timeout=5)

        assert isinstance(backend, DummyBackend)
        assert backend.client == mock_client.return_value


class TestDepotClientInit:
    def test_initializes_without_api_key(self):
        client = DepotClient(base_url="http://fake")
        assert client.base_url == "http://fake"
        assert client.api_key is None
        assert "Authorization" not in client.headers

    def test_initializes_with_api_key(self):
        client = DepotClient(base_url="http://fake", api_key="secret")
        assert client.api_key == "secret"
        assert client.headers["Authorization"] == "Bearer secret"


class TestDepotServiceBackendRequest:
    def test_request_success(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 1}
        mock_response.raise_for_status.return_value = None
        mock_client.request.return_value = mock_response

        backend = DepotServiceBackend(client=mock_client)
        result = backend._request("get", "/trips")

        assert result == {"id": 1}
        mock_client.request.assert_called_once_with("get", "/trips")

    def test_request_failure_raises(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.RequestException("fail")
        mock_client.request.return_value = mock_response

        backend = DepotServiceBackend(client=mock_client)

        with pytest.raises(DepotServiceError) as exc:
            backend._request("get", "/bad")

        assert "GET" in str(exc.value) and "/bad" in str(exc.value)


class TestDepotServiceBackendTrips:
    def test_list_trips_returns_list(self):
        backend = DepotServiceBackend(client=MagicMock())
        backend._request = MagicMock(return_value=[{"id": 1}])

        result = backend.list_trips("A", "B")

        backend._request.assert_called_once_with(
            "get",
            "smart-trip-search",
            params={"origin": "A", "destination": "B"},
        )
        assert result == [{"id": 1}]

    def test_list_trips_non_list_returns_empty(self):
        backend = DepotServiceBackend(client=MagicMock())
        backend._request = MagicMock(return_value={"id": 1})

        result = backend.list_trips("A", "B")
        assert result == []


class TestDepotServiceBackendTripDetails:
    def test_get_trip_calls_request(self):
        backend = DepotServiceBackend(client=MagicMock())
        backend._request = MagicMock(return_value={"trip": 123})

        result = backend.get_trip(5, "A", "B")

        backend._request.assert_called_once_with(
            "get",
            "trips/5/extra-info",
            params={"origin": "A", "destination": "B"},
        )
        assert result == {"trip": 123}

    def test_get_seat_info_returns_none_if_no_trip(self):
        backend = DepotServiceBackend(client=MagicMock())
        backend._request = MagicMock(return_value=None)

        result = backend.get_seat_info(10, "A", "B")
        assert result is None

    def test_get_seat_info_returns_trip_and_seats(self, monkeypatch):
        backend = DepotServiceBackend(client=MagicMock())
        fake_trip = {"schedule": {"bus": {"capacity": 50}}}
        backend._request = MagicMock(return_value=fake_trip)

        monkeypatch.setattr(
            "tickets.depot.backends.service.generate_seat_status",
            lambda trip_id, cap: {"seatmap": f"{trip_id}-{cap}"},
        )

        result = backend.get_seat_info(99, "X", "Y")

        assert result["trip_info"] == fake_trip
        assert result["seats"] == {"seatmap": "99-50"}


class TestJsonDepotBackendInit:
    def test_init_loads_trips_from_file(self, tmp_path, settings):
        trips_data = {"trips": [{"id": 1, "name": "Trip A"}]}
        file = tmp_path / "trips.json"
        file.write_text(json.dumps(trips_data), encoding="utf-8")

        settings.BASE_DIR = tmp_path

        backend = JsonDepotBackend(file_path="trips.json")

        assert backend.trips == [{"id": 1, "name": "Trip A"}]

    def test_init_raises_if_trips_not_list(self, tmp_path, settings):
        invalid_data = {"trips": {"id": 1}}
        file = tmp_path / "trips.json"
        file.write_text(json.dumps(invalid_data), encoding="utf-8")

        settings.BASE_DIR = tmp_path

        with pytest.raises(ValueError, match="Expected 'trips' to be a list"):
            JsonDepotBackend(file_path="trips.json")


class TestJsonDepotBackendLoadJson:
    def test_load_json_invalid_file_raises(self, tmp_path, settings):
        settings.BASE_DIR = tmp_path
        missing_file = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError):
            JsonDepotBackend(file_path="missing.json")

    def test_load_json_invalid_json_raises(self, tmp_path, settings):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json", encoding="utf-8")
        settings.BASE_DIR = tmp_path

        with pytest.raises(ValueError, match="Invalid JSON"):
            JsonDepotBackend(file_path="bad.json")

    def test_load_json_non_dict_root_raises(self, tmp_path, settings):
        bad_file = tmp_path / "list.json"
        bad_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        settings.BASE_DIR = tmp_path

        with pytest.raises(ValueError, match="Expected JSON root to be an object"):
            JsonDepotBackend(file_path="list.json")


class TestJsonDepotBackendMethods:
    @pytest.fixture
    def backend(self, tmp_path, settings, monkeypatch):
        trips_data = {
            "trips": [
                {"id": 1, "schedule": {"bus": {"capacity": 40}}},
                {"id": 2, "schedule": {"bus": {"capacity": 20}}},
            ]
        }
        file = tmp_path / "trips.json"
        file.write_text(json.dumps(trips_data), encoding="utf-8")
        settings.BASE_DIR = tmp_path

        return JsonDepotBackend(file_path="trips.json")

    def test_list_trips_returns_all(self, backend):
        trips = backend.list_trips("A", "B")
        assert len(trips) == 2
        assert trips[0]["id"] == 1

    def test_get_trip_found(self, backend):
        trip = backend.get_trip(1)
        assert trip is not None
        assert trip["id"] == 1

    def test_get_trip_not_found(self, backend):
        assert backend.get_trip(99) is None

    def test_get_seat_info_returns_data(self, backend, monkeypatch):
        monkeypatch.setattr(
            "tickets.depot.backends.json.generate_seat_status",
            lambda trip_id, cap: {"mocked": f"{trip_id}-{cap}"},
        )
        info = backend.get_seat_info(1)
        assert info["trip_info"]["id"] == 1
        assert info["seats"] == {"mocked": "1-40"}

    def test_get_seat_info_returns_none_if_trip_missing(self, backend):
        assert backend.get_seat_info(99) is None
