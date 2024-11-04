import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from pytest_factoryboy import register
from faker import Faker
import factory
from django.urls import reverse


fake = Faker()

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "password123")
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    is_active = True


class AdminFactory(UserFactory):
    role = "admin"
    is_staff = True
    is_superuser = False


class RegularUserFactory(UserFactory):
    role = "user"


class FriendUserFactory(UserFactory):
    role = "friend"


# Register factories
register(AdminFactory)
register(RegularUserFactory)
register(FriendUserFactory)


# Fixtures
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(admin_factory):
    return admin_factory()


@pytest.fixture
def regular_user(regular_user_factory):
    return regular_user_factory()


@pytest.fixture
def friend_user(friend_user_factory):
    return friend_user_factory()


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """Returns an authenticated client for admin user"""
    url = reverse("auth-token")
    response = api_client.post(
        url, {"username": admin_user.username, "password": "password123"}
    )
    token = response.data["access_token"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def authenticated_user_client(api_client, regular_user):
    """Returns an authenticated client for regular user"""
    url = reverse("auth-token")
    response = api_client.post(
        url, {"username": regular_user.username, "password": "password123"}
    )
    token = response.data["access_token"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def authenticated_friend_client(api_client, friend_user):
    """Returns an authenticated client for friend user"""
    url = reverse("auth-token")
    response = api_client.post(
        url, {"username": friend_user.username, "password": "password123"}
    )
    token = response.data["access_token"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client
