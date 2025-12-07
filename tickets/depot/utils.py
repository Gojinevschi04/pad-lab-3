from tickets.core.models import Ticket


def generate_seat_status(trip_id: int, capacity: int) -> dict:
    taken = set(Ticket.objects.taken_seats(trip_id))

    def seat_state(seat: int) -> str:
        return "reserved" if seat in taken else "available"

    return {str(seat): seat_state(seat) for seat in range(1, capacity + 1)}
