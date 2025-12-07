from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def mock_jwt(monkeypatch):
    mock_key = MagicMock()
    mock_key.key = "secret"

    decode_mock = MagicMock()
    get_key_mock = MagicMock(return_value=mock_key)

    monkeypatch.setattr("tickets.authentication.jwt.decode", decode_mock)
    monkeypatch.setattr(
        "tickets.authentication.PyJWKClient.get_signing_key_from_jwt", get_key_mock
    )

    return {"decode": decode_mock, "get_key": get_key_mock}


@pytest.mark.django_db
class TestWhoAmI:
    def test_whoami_returns_user_info(self, auth_client, user):
        response = auth_client.get("/debug/whoami/")
        assert response.status_code == 200
        data = response.data

        assert data["email"] == user.email
        assert data["username"] == user.username
        assert data["id"] == user.id

    def test_whoami_creates_user_if_not_exists(self, client, mock_jwt):
        new_email = "newuser@example.com"

        mock_jwt["decode"].return_value = {"email": new_email}

        response = client.get("/debug/whoami/", HTTP_AUTHORIZATION="Bearer faketoken")
        assert response.status_code == 200

        user = User.objects.get(email=new_email)
        assert user.email == new_email

        data = response.data
        assert data["email"] == new_email
        assert data["id"] == user.id
