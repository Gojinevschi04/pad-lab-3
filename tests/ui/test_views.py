import pytest
from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
def test_home_view_authenticated(logged_in_client):
    url = reverse("ui:home")
    response = logged_in_client.get(url)

    assert response.status_code == 200
    assert "ui/home.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_partial_view_authenticated(logged_in_client):
    url = reverse("ui:partial")
    response = logged_in_client.get(url)

    assert response.status_code == 200
    assert "ui/partial.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_home_view_redirects_when_not_logged_in(client):
    url = reverse("ui:home")
    response = client.get(url)

    assert response.status_code == 302
    assert response.url.startswith(str(settings.LOGIN_URL))


@pytest.mark.django_db
def test_partial_view_redirects_when_not_logged_in(client):
    url = reverse("ui:partial")
    response = client.get(url)

    assert response.status_code == 302
    assert response.url.startswith(str(settings.LOGIN_URL))
