from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import AuthenticationFailed
from accounts.authentication import JWTAuthentication
from django.http import JsonResponse
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.urls import resolve


class AuthMiddleware(MiddlewareMixin):

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.django_auth_middleware = None

    def process_request(self, request):
        """
        Initial request processing to handle both session and JWT authentication
        """

        if self.django_auth_middleware is None:
            self.django_auth_middleware = AuthenticationMiddleware(self.get_response)

        self.django_auth_middleware.process_request(request)

        if hasattr(request, "user") and request.user.is_authenticated:
            return None

        if not hasattr(request, "user"):
            request.user = None
        if not hasattr(request, "auth"):
            request.auth = None

        return None

    def process_view(self, request, view_func, *view_args, **view_kwargs):
        """Authenticate the request using JWTAuthentication and set request.user."""

        path = request.path_info.rstrip("/")

        skip_auth_paths = [
            "/admin",
            "/api/v1/auth/token",
            "/api/v1/users/register",
            "/api/v1/auth/refresh_token",
        ]

        if any(path.startswith(skip_path) for skip_path in skip_auth_paths):
            return None

        auth = JWTAuthentication()
        try:
            # Only attempt authentication if Authorization header is present
            if "Authorization" in request.headers:
                user_auth_tuple = auth.authenticate(request)
                if user_auth_tuple is not None:
                    request.user, request.auth = user_auth_tuple

            # For protected routes, ensure user is authenticated
            if not any(path.startswith(skip_path) for skip_path in skip_auth_paths):
                if not request.user or not request.user.is_authenticated:
                    return JsonResponse(
                        {"detail": "Authentication required"}, status=401
                    )

        except AuthenticationFailed as e:
            return JsonResponse({"detail": str(e)}, status=401)

        return None
