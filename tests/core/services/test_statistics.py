# from datetime import timedelta
#
# import pytest
# from django.utils import timezone
#
# from tickets.core.models import Ticket
# from tickets.core.services.statistics import (
#     get_most_active_routes,
#     get_seat_occupancy_rates,
#     get_ticket_sales_count,
# )
#
#
# @pytest.fixture
# def trip_a(db):
#     return {
#         "trip_id": 1,
#         "route_name": "Route A",
#         "bus_model": "Model X",
#         "bus_plate_number": "AAA123",
#         "bus_capacity": 50,
#         "driver_name": "Alex",
#         "driver_phone": "123",
#         "price": 30.0,
#         "date": timezone.now().date(),
#         "start_time": timezone.now().time(),
#         "end_time": timezone.now().time(),
#         "from_city": "CityA",
#         "to_city": "CityB",
#         "trip_nr": "TRIP001",
#     }
#
#
# @pytest.fixture
# def trip_b(db):
#     return {
#         "trip_id": 2,
#         "route_name": "Route B",
#         "bus_model": "Model Y",
#         "bus_plate_number": "BBB456",
#         "bus_capacity": 50,
#         "driver_name": "Ben",
#         "driver_phone": "456",
#         "price": 35.0,
#         "date": timezone.now().date(),
#         "start_time": timezone.now().time(),
#         "end_time": timezone.now().time(),
#         "from_city": "CityX",
#         "to_city": "CityY",
#         "trip_nr": "TRIP002",
#     }
#
#
# @pytest.fixture
# def tickets_for_trip_a(user, trip_a):
#     Ticket.objects.create(
#         user=user,
#         trip_id=trip_a.trip_id,
#         seat_number=1,
#         status=Ticket.Status.PAID,
#         price=trip_a.price,
#     )
#     Ticket.objects.create(
#         user=user,
#         trip_id=trip_a.trip_id,
#         seat_number=2,
#         status=Ticket.Status.PAID,
#         price=trip_a.price,
#     )
#
#
# @pytest.fixture
# def ticket_for_trip_b(user, trip_b):
#     Ticket.objects.create(
#         user=user,
#         trip_id=trip_b.trip_id,
#         seat_number=3,
#         status=Ticket.Status.PAID,
#         price=trip_b.price,
#     )
#
#
# @pytest.fixture
# def old_ticket(user):
#     ticket = Ticket.objects.create(
#         user=user,
#         title="Old Ticket",
#         seat_number=1,
#         trip_id=1,
#         status=Ticket.Status.PAID,
#         price=20.0,
#     )
#     ticket.created_at = timezone.now() - timedelta(days=5)
#     ticket.save(update_fields=["created_at"])
#     return ticket
#
#
# @pytest.fixture
# def new_ticket(user):
#     ticket = Ticket.objects.create(
#         user=user,
#         title="New Ticket",
#         seat_number=2,
#         trip_id=1,
#         status=Ticket.Status.PAID,
#         price=20.0,
#     )
#     ticket.created_at = timezone.now()
#     ticket.save(update_fields=["created_at"])
#     return ticket
#
#
# @pytest.mark.django_db
# def test_get_most_active_routes_returns_top_routes(user, trip_a, trip_b, tickets_for_trip_a, ticket_for_trip_b):
#     top_routes = get_most_active_routes()
#
#     assert len(top_routes) == 2
#     assert top_routes[0]["route_name"] == trip_a.route_name
#     assert top_routes[0]["total_sold"] == 2
#
#
# @pytest.mark.django_db
# def test_get_seat_occupancy_rates(user, trip_a, tickets_for_trip_a):
#     results = get_seat_occupancy_rates()
#
#     assert len(results) == 1
#     assert results[0]["trip_id"] == trip_a.trip_id
#     assert results[0]["route_name"] == trip_a.route_name
#     assert results[0]["sold"] == 2
#     assert results[0]["capacity"] == trip_a.bus_capacity
#     assert results[0]["occupancy_rate"] == 100 * 2 / trip_a.bus_capacity
#
#
# @pytest.mark.django_db
# def test_get_ticket_sales_count_filters_by_date(new_ticket, old_ticket):
#     now = timezone.now()
#     count = get_ticket_sales_count(start_date=now - timedelta(days=1))
#     assert count == 1
