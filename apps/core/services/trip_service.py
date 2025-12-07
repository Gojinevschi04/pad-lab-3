from tickets.depot.exceptions import DepotServiceError
from tickets.depot.serializers import TripSerializer


class TripService:
    def __init__(self, backend):
        self.backend = backend

    def fetch_and_serialize_trip(
        self, trip_id: int, origin: str, destination: str
    ) -> dict:
        try:
            raw_trip = self.backend.get_trip(trip_id, origin, destination)
        except DepotServiceError as error:
            raise RuntimeError(f"Failed to fetch trip {trip_id}: {error}") from error

        if not raw_trip:
            raise RuntimeError(
                f"Trip {trip_id} not found for {origin} -> {destination}"
            )

        return TripSerializer(raw_trip).data
