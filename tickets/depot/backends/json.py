import json
from pathlib import Path

from django.conf import settings

from tickets.depot.backends.base import BaseBackend
from tickets.depot.backends.client import DepotClient
from tickets.depot.utils import generate_seat_status

trips = {
    "trips": [
        {
            "id": 1,
            "schedule": {
                "id": 1,
                "route": {
                    "id": 1,
                    "name": "Chisinau-Hincesti"
                },
                "bus": {
                    "id": 1,
                    "driver": {
                        "id": 1,
                        "status": "sănătos",
                        "name": "Vasiliy Bombilo",
                        "phone_number": "+37377777777",
                        "employee_id": "EMP-EN7JGS"
                    },
                    "fuel": "motorină",
                    "model": "Tesla Model X",
                    "plate_number": "BMW 777",
                    "color": "black",
                    "capacity": 52,
                    "status": "ready"
                },
                "day_of_week": "luni",
                "direction": "dus",
                "start_time": "08:00:00",
                "end_time": "09:00:00"
            },
            "status": "planificat",
            "price": 33.0,
            "from_station": {
                "city": "Ialoveni",
                "address": "Alex Winner, 95"
            },
            "departure_time": None,
            "to_station": {
                "city": "Hincesti",
                "street": "bd. Stefan cel Mare, 25"
            },
            "arrival_time": None,
            "date": "2025-07-21",
            "trip_nr": "C6FMYTIM2LWPLT"
        },
        {
            "id": 2,
            "schedule": {
                "id": 1,
                "route": {
                    "id": 1,
                    "name": "Chisinau-Hincesti"
                },
                "bus": {
                    "id": 1,
                    "driver": {
                        "id": 1,
                        "status": "sănătos",
                        "name": "Vasiliy Bombilo",
                        "phone_number": "+37377777777",
                        "employee_id": "EMP-EN7JGS"
                    },
                    "fuel": "motorină",
                    "model": "Tesla Model X",
                    "plate_number": "BMW 777",
                    "color": "black",
                    "capacity": 52,
                    "status": "ready"
                },
                "day_of_week": "luni",
                "direction": "dus",
                "start_time": "08:00:00",
                "end_time": "09:00:00"
            },
            "status": "planificat",
            "price": 33.0,
            "from_station": {
                "city": "Ialoveni",
                "address": "Alex Winner, 95"
            },
            "departure_time": None,
            "to_station": {
                "city": "Hincesti",
                "street": "bd. Stefan cel Mare, 25"
            },
            "arrival_time": None,
            "date": "2025-07-21",
            "trip_nr": "C6FMYTIM2LWPLT"
        }
    ]
}


class JsonDepotBackend(BaseBackend):
    def __init__(self, client: DepotClient):
        super().__init__()
        self.client = client
        self.data = self._load_json()

        self.trips = self.data.get("trips", [])
        if not isinstance(self.trips, list):
            raise ValueError("Expected 'trips' to be a list")

    def _load_json(self) -> dict:
        return trips

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
