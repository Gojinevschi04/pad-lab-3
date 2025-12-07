import pytest
from django.urls import resolve, reverse

from tickets.depot.views import TripViewSet


@pytest.mark.django_db
def test_trip_list_url_resolves():
    url = reverse("tickets-depot:trip-list")
    resolver = resolve(url)
    assert resolver.func.cls == TripViewSet


@pytest.mark.django_db
def test_trip_detail_url_resolves():
    url = reverse("tickets-depot:trip-detail", kwargs={"pk": 1})
    resolver = resolve(url)
    assert resolver.func.cls == TripViewSet


@pytest.mark.django_db
def test_trip_seats_url_resolves():
    url = reverse("tickets-depot:trip-seats", kwargs={"pk": 1})
    resolver = resolve(url)
    assert resolver.func.cls == TripViewSet


@pytest.mark.django_db
def test_trip_cancel_tickets_url_resolves():
    url = reverse("tickets-depot:trip-cancel-tickets", kwargs={"pk": 1})
    resolver = resolve(url)
    assert resolver.func.cls == TripViewSet
