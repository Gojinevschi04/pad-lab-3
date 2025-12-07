import pytest
from django.urls import resolve, reverse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from tickets.core.views import OAuth2RedirectView
from tickets.debug.views import WhoAmIView
from tickets.ui import views as ui_views


@pytest.mark.django_db
def test_admin_url_resolves():
    path = reverse("admin:index")
    resolver = resolve(path)
    assert resolver.namespace == "admin"
    assert resolver.url_name == "index"


def test_ui_urls_resolve():
    path = reverse("ui:home")
    assert resolve(path).func.view_class == ui_views.HomeView


@pytest.mark.django_db
def test_whoami_url_resolves():
    path = reverse("debug:whoami")
    assert resolve(path).func.view_class == WhoAmIView


@pytest.mark.django_db
def test_ticket_list_view_get(client):
    url = reverse("tickets-core:ticket-list")
    response = client.get(url)
    assert response.status_code in [200, 403]


@pytest.mark.django_db
def test_ticket_list_view_post_not_allowed(client):
    url = reverse("tickets-core:ticket-list")
    response = client.post(url, data={})
    assert response.status_code == 403


@pytest.mark.django_db
def test_ticket_detail_view_get(client):
    url = reverse("tickets-core:ticket-detail", kwargs={"pk": 1})
    response = client.get(url)
    assert response.status_code in [200, 403, 404]


@pytest.mark.django_db
def test_ticket_detail_view_post_not_allowed(client):
    url = reverse("tickets-core:ticket-detail", kwargs={"pk": 1})
    response = client.post(url, data={})
    assert response.status_code == 403


def test_openapi_schema_urls():
    path_schema = reverse("schema")
    assert resolve(path_schema).func.view_class == SpectacularAPIView

    path_swagger = reverse("swagger-ui")
    assert resolve(path_swagger).func.view_class == SpectacularSwaggerView

    path_redoc = reverse("redoc")
    assert resolve(path_redoc).func.view_class == SpectacularRedocView

    path_oauth_redirect = reverse("swagger-ui-oauth2-redirect")
    assert resolve(path_oauth_redirect).func.view_class == OAuth2RedirectView


@pytest.mark.django_db
def test_whoami_view_status(client):
    url = reverse("debug:whoami")
    response = client.get(url)
    assert response.status_code in [200, 401, 403]


@pytest.mark.django_db
def test_openapi_schema_response(client):
    url = reverse("schema")
    response = client.get(url)
    assert response.status_code == 200
