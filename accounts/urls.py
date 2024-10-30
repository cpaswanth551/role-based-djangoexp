from django.urls import include, path

from rest_framework.routers import DefaultRouter

from accounts.views import *


router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"auth", AuthViewSet, basename="auth")

urlpatterns = [
    path("", include(router.urls)),
]
