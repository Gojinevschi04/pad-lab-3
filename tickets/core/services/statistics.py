from collections import Counter

from tickets.core.models import Ticket


def get_ticket_sales_count(start_date=None, end_date=None) -> int:
    queryset = Ticket.objects.filter(status=Ticket.Status.PAID)
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)
    return queryset.count()


def get_most_active_routes(limit=5) -> list:
    paid_tickets = Ticket.objects.filter(status=Ticket.Status.PAID)

    trip_id_counts = Counter(paid_tickets.values_list("trip_id", flat=True))

    results = []
    # for trip in trip_infos:
    #     count = trip_id_counts.get(trip.trip_id, 0)
    #     results.append({"route_name": trip.route_name, "total_sold": count})

    return sorted(results, key=lambda r: r["total_sold"], reverse=True)[:limit]


def get_seat_occupancy_rates() -> list:
    trips = {}
    stats = []

    for trip in trips:
        total_capacity = trip.bus_capacity
        sold = Ticket.objects.filter(
            trip_id=trip.trip_id,
            status=Ticket.Status.PAID,
        ).count()
        occupancy = sold / total_capacity if total_capacity > 0 else 0
        stats.append(
            {
                "trip_id": trip.trip_id,
                "route_name": trip.route_name,
                "sold": sold,
                "capacity": total_capacity,
                "occupancy_rate": round(occupancy * 100, 2),
            },
        )

    return stats
