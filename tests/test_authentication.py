from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from jwt import ExpiredSignatureError, InvalidTokenError
from rest_framework import exceptions

from tickets.authentication import OpenIDAuthenticationExtension

User = get_user_model()


def test_no_authorization_header_returns_none(auth_instance, api_factory):
    request = api_factory.get("/some-url/")
    result = auth_instance.authenticate(request)
    assert result is None


def test_invalid_header_format_raises_exception(auth_instance, api_factory):
    request = api_factory.get("/some-url/", HTTP_AUTHORIZATION="Bearer")
    with pytest.raises(exceptions.AuthenticationFailed):
        auth_instance.authenticate(request)


def test_non_bearer_header_returns_none(auth_instance, api_factory):
    request = api_factory.get("/some-url/", HTTP_AUTHORIZATION="Token abc.def.ghi")
    result = auth_instance.authenticate(request)
    assert result is None


def test_authenticate_success(
    mocker,
    auth_instance,
    api_factory,
    mock_token,
    mock_payload,
):
    request = api_factory.get("/some-url/", HTTP_AUTHORIZATION=f"Bearer {mock_token}")

    mock_signing_key = mocker.Mock()
    mock_signing_key.key = "fake-key"

    mock_jwks_client = mocker.patch(
        "tickets.authentication.PyJWKClient",
    ).return_value
    mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key

    mocker.patch("tickets.authentication.jwt.decode", return_value=mock_payload)
    mock_user = User(email=mock_payload["email"], username=mock_payload["email"])
    mocker.patch.object(User.objects, "get_or_create", return_value=(mock_user, True))

    user, auth = auth_instance.authenticate(request)
    assert user.email == mock_payload["email"]
    assert auth is None


def test_missing_email_raises_exception(
    mocker,
    auth_instance,
    api_factory,
    mock_token,
):
    request = api_factory.get("/some-url/", HTTP_AUTHORIZATION=f"Bearer {mock_token}")

    mock_signing_key = mocker.Mock()
    mock_signing_key.key = "fake-key"

    mocker.patch(
        "tickets.authentication.PyJWKClient"
    ).return_value.get_signing_key_from_jwt.return_value = mock_signing_key
    mocker.patch("tickets.authentication.jwt.decode", return_value={})

    with pytest.raises(exceptions.AuthenticationFailed, match="Token missing email"):
        auth_instance.authenticate(request)


def test_expired_token_raises_exception(
    mocker,
    auth_instance,
    api_factory,
    mock_token,
):
    request = api_factory.get("/some-url/", HTTP_AUTHORIZATION=f"Bearer {mock_token}")
    mock_signing_key = mocker.Mock()
    mock_signing_key.key = "fake-key"

    mocker.patch(
        "tickets.authentication.PyJWKClient"
    ).return_value.get_signing_key_from_jwt.return_value = mock_signing_key
    mocker.patch(
        "tickets.authentication.jwt.decode",
        side_effect=ExpiredSignatureError("Token expired"),
    )

    with pytest.raises(exceptions.AuthenticationFailed, match="Token expired"):
        auth_instance.authenticate(request)


def test_invalid_token_raises_exception(
    mocker,
    auth_instance,
    api_factory,
    mock_token,
):
    request = api_factory.get("/some-url/", HTTP_AUTHORIZATION=f"Bearer {mock_token}")
    mock_signing_key = mocker.Mock()
    mock_signing_key.key = "fake-key"

    mocker.patch(
        "tickets.authentication.PyJWKClient"
    ).return_value.get_signing_key_from_jwt.return_value = mock_signing_key
    mocker.patch(
        "tickets.authentication.jwt.decode",
        side_effect=InvalidTokenError("Invalid token"),
    )

    with pytest.raises(
        exceptions.AuthenticationFailed, match="Invalid token: Invalid token"
    ):
        auth_instance.authenticate(request)


def test_signing_key_failure_raises_exception(
    mocker,
    auth_instance,
    api_factory,
    mock_token,
):
    request = api_factory.get("/some-url/", HTTP_AUTHORIZATION=f"Bearer {mock_token}")
    mock_jwks = mocker.patch("tickets.authentication.PyJWKClient").return_value
    mock_jwks.get_signing_key_from_jwt.side_effect = Exception("Key error")

    with pytest.raises(
        exceptions.AuthenticationFailed, match="Unable to find signing key"
    ):
        auth_instance.authenticate(request)


@pytest.mark.django_db
def test_get_security_definition(settings):
    settings.OAUTH2_AUTHORIZATION_URL = "https://example.com/oauth/authorize"
    settings.OAUTH2_TOKEN_URL = "https://example.com/oauth/token"

    mock_target = Mock()
    extension = OpenIDAuthenticationExtension(mock_target)
    result = extension.get_security_definition(auto_schema=None)

    expected = {
        "type": "oauth2",
        "flows": {
            "authorizationCode": {
                "authorizationUrl": "https://example.com/oauth/authorize",
                "tokenUrl": "https://example.com/oauth/token",
                "scopes": {
                    "openid": "OpenID Connect scope",
                    "profile": "User profile",
                    "email": "User email",
                },
            },
        },
    }

    assert result == expected
