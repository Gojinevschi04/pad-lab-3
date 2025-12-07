import logging
from typing import Any

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from jwt import PyJWKClient
from rest_framework import authentication, exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request

logger = logging.getLogger(__name__)

User = get_user_model()


class OpenIDAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> tuple[User, None] | None:
        auth_header = authentication.get_authorization_header(request).split()
        if not auth_header or auth_header[0].lower() != b"bearer":
            return None

        if len(auth_header) != 2:
            raise exceptions.AuthenticationFailed("Invalid Authorization header")

        token = auth_header[1].decode()
        return self._authenticate_token(token)

    def _authenticate_token(self, token: str) -> tuple[User, None]:
        jwks_url = settings.OAUTH2_JWKS_URL
        jwks_client = PyJWKClient(jwks_url)

        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
        except Exception as e:
            raise exceptions.AuthenticationFailed(
                f"Unable to find signing key: {e!s}",
            )

        try:
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=None,
                options={"verify_aud": False},
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token expired")
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f"Invalid token: {e!s}")

        email = payload.get("email") or payload.get("preferred_username")
        if not email:
            raise exceptions.AuthenticationFailed("Token missing email")

        user, _ = User.objects.get_or_create(email=email, defaults={"username": email})

        return (user, None)


class OpenIDAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "tickets.authentication.OpenIDAuthentication"
    name = "oauth"

    def get_security_definition(self, auto_schema: Any) -> dict[str, Any]:
        return {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": settings.OAUTH2_AUTHORIZATION_URL,
                    "tokenUrl": settings.OAUTH2_TOKEN_URL,
                    "scopes": {
                        "openid": "OpenID Connect scope",
                        "profile": "User profile",
                        "email": "User email",
                    },
                },
            },
        }
