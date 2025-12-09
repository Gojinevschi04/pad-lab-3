import json
from pathlib import Path

from django.conf import settings

from tickets.depot.backends.base import BaseBackend
from tickets.depot.backends.client import DepotClient
from tickets.depot.utils import generate_seat_status


class JsonDepotBackend(BaseBackend):
    def __init__(self, client: DepotClient, file_path: str = "trips.json"):
        super().__init__()
        self.client = client
        self.file_path = Path(settings.BASE_DIR) / file_path
        self.data = self._load_json(self.file_path)

        self.trips = self.data.get("trips", [])
        if not isinstance(self.trips, list):
            raise ValueError("Expected 'trips' to be a list")

    def _load_json(self, path: Path) -> dict:
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {path}: {e}")

        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON root to be an object, got {type(data)}")
        return data

    def list_trips(self, origin: str, destination: str) -> list[dict]:
        return self.trips

    def get_trip(
        self, trip_id: int, origin: str = "", destination: str = ""
    ) -> dict | None:
        trip = next((t for t in self.trips if t.get("id") == trip_id), None)
        return trip if trip else None

    def get_seat_info(self, trip_id: int) -> dict | None:
        trip = self.get_trip(trip_id)

        if not trip:
            return None

        schedule = trip.get("schedule") or {}
        bus = schedule.get("bus") or {}
        bus_capacity = bus.get("capacity", 0)

        return {
            "trip_info": trip,
            "seats": generate_seat_status(trip_id, bus_capacity),
        }
