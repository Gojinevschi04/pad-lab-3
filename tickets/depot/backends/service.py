import requests

from tickets.depot.backends.base import BaseBackend
from tickets.depot.backends.client import DepotClient
from tickets.depot.exceptions import DepotServiceError
from tickets.depot.utils import generate_seat_status


class DepotServiceBackend(BaseBackend):
    def __init__(self, client: DepotClient):
        super().__init__()
        self.client = client

    def _request(self, method: str, path: str, **kwargs) -> dict | None:
        try:
            response = self.client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, requests.JSONDecodeError) as exception:
            raise DepotServiceError(method.upper(), path, exception) from exception

    def list_trips(self, origin: str, destination: str) -> list[dict]:
        data = self._request(
            "get",
            "smart-trip-search",
            params={"origin": origin, "destination": destination},
        )
        return data if isinstance(data, list) else []

    def get_trip(self, trip_id: int, origin: str, destination: str) -> dict | None:
        return self._request(
            "get",
            f"trips/{trip_id}/extra-info",
            params={"origin": origin, "destination": destination},
        )

    def get_seat_info(self, trip_id: int, origin: str, destination: str) -> dict | None:
        trip = self._request(
            "get",
            f"trips/{trip_id}/extra-info",
            params={"origin": origin, "destination": destination},
        )

        if not trip:
            return None

        schedule = trip.get("schedule") or {}
        bus = schedule.get("bus") or {}
        bus_capacity = bus.get("capacity", 0)

        return {
            "trip_info": trip,
            "seats": generate_seat_status(trip_id, bus_capacity),
        }
