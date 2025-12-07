from types import SimpleNamespace

import pytest
from rest_framework.views import APIView

from tickets.core.permissions import IsTicketOwner


class DummyUser:
    def __init__(self, username):
        self.username = username


@pytest.fixture
def permission():
    return IsTicketOwner()


@pytest.fixture
def dummy_view():
    return APIView()


def test_has_object_permission_owner(permission, dummy_view):
    user = DummyUser("alice")
    obj = SimpleNamespace(user=user)
    request = SimpleNamespace(user=user)
    assert permission.has_object_permission(request, dummy_view, obj) is True


def test_has_object_permission_not_owner(permission, dummy_view):
    user = DummyUser("alice")
    other_user = DummyUser("bob")
    obj = SimpleNamespace(user=other_user)
    request = SimpleNamespace(user=user)
    assert permission.has_object_permission(request, dummy_view, obj) is False
