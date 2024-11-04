import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestAuthentication:
    def test_login_admin(self, api_client, admin_user):
        url = reverse("auth-token")

        data = {"username": admin_user.username, "password": "password123"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data
        assert response.data["user"]["role"] == "admin"

    def test_login_regular_user(self, api_client, regular_user):
        url = reverse("auth-token")
        data = {"username": regular_user.username, "password": "password123"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"]["role"] == "user"

    def test_login_invalid_credentials(self, api_client, regular_user):

        url = reverse("auth-token")
        data = {"username": regular_user.username, "password": "wrongpassword"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenRefresh:
    def test_refresh_token(self, api_client, regular_user):

        # First get tokens
        url = reverse("auth-token")
        data = {"username": regular_user.username, "password": "password123"}
        response = api_client.post(url, data)

        refresh_token = response.data["refresh_token"]

        # Then refresh
        refresh_url = reverse("auth-refresh-token")
        response = api_client.post(refresh_url, {"refresh_token": refresh_token})

        print(response)

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data

    def test_refresh_invalid_token(self, api_client):
        url = reverse("auth-refresh-token")
        response = api_client.post(url, {"refresh_token": "invalid-token"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
