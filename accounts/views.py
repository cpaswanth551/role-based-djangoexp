# views.py

from django.conf import settings
import jwt
from rest_framework import viewsets, filters, status
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate

from accounts.models import User
from accounts.permissions import IsAdminUser, IsRegularUser, UserPermission
from accounts.serializers import (
    LoginSerializer,
    RegisterSerializer,
    TokenRefreshSerializer,
    UserSerializer,
)
from .utils import generate_tokens


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, UserPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "first_name", "last_name"]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return User.objects.all()
        elif user.role == "user":
            return User.objects.filter(Q(id=user.id) | Q(created_by=user))
        else:
            return User.objects.filter(id=user.id)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        """Custom action for user registration"""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "User registered successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create_friend(self, serializer):
        """Helper method to set the creator of a friend"""
        role = serializer.validated_data.get("role", "user")
        serializer.save(created_by=self.request.user if role == "friend" else None)

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def analytics(self, request):
        """Custom endpoint for analytics, accessible only by admins"""
        total_users = User.objects.count()
        total_friends = User.objects.filter(role="friend").count()
        return Response({"total_users": total_users, "total_friends": total_friends})

    @action(
        detail=False, methods=["get"], permission_classes=[IsRegularUser | IsAdminUser]
    )
    def my_friends(self, request):
        """Endpoint to list friends created by the current user"""
        friends = User.objects.filter(created_by=request.user, role="friend")
        serializer = self.get_serializer(friends, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def activate_user(self, request, pk=None):
        """Admin-only endpoint to activate a user"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({"status": "user activated"})

    @action(detail=True, methods=["post"], permission_classes=[IsRegularUser])
    def manage_friend(self, request, pk=None):
        """Endpoint for users to manage their friends' settings"""
        friend = self.get_object()
        if friend.created_by != request.user:
            return Response(
                {"detail": "You do not have permission to manage this friend"},
                status=403,
            )
        # Add friend management logic here
        return Response({"status": "friend settings updated"})


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def token(self, request):
        """Endpoint to obtain JWT tokens"""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        if not user:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        access_token, refresh_token = generate_tokens(user)
        return Response(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
            }
        )

    @action(detail=False, methods=["post"])
    def refresh_token(self, request):
        """Endpoint to refresh JWT tokens"""
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data["refresh_token"]
            print("Received refresh token:", refresh_token)
            payload = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=["HS256"]
            )

            if payload.get("token_type") != "refresh":
                raise jwt.InvalidTokenError("Not a refresh token")

            user = User.objects.get(id=payload["user_id"])
            access_token, new_refresh_token = generate_tokens(user)

            return Response(
                {"access_token": access_token, "refresh_token": new_refresh_token}
            )

        except jwt.ExpiredSignatureError:
            return Response(
                {"error": "Refresh token has expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except jwt.InvalidTokenError as e:
            print("Invalid token error:", str(e))
            return Response(
                {"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User does not exist"}, status=status.HTTP_401_UNAUTHORIZED
            )
