from rest_framework import viewsets, filters
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import IsAdminUser, IsRegularUser, UserPermission
from accounts.serializers import UserSerializer

# Create your views here.


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [UserPermission]
    filter_backends = [filters.SearchFilter]

    search_fields = ["username", "email", "first_name", "last_name"]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return User.objects.all()

        elif user.role == "user":
            return User.objects.filter(
                Q(id=user.id) | Q(created_by=user)  # themselves  # their friends
            )

        # Friends can only see themselves
        else:
            return User.objects.filter(id=user.id)

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def analytics(self, request):
        """Custom endpoint for analytics, only accessible by admin"""
        total_users = User.objects.count()
        total_friends = User.objects.filter(role="friend").count()

        return Response(
            {
                "total_users": total_users,
                "total_friends": total_friends,
            }
        )

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
        if friend.created_by != request.user or not request.user.has_perm(
            "accounts.can_manage_own_friends"
        ):
            return Response(
                {"detail": "You do not have permission to manage this friend"},
                status=403,
            )
        # Add friend management logic here
        return Response({"status": "friend settings updated"})

    def perform_create(self, serializer):
        # Set created_by field when creating friend accounts
        role = serializer.validated_data.get("role", "user")
        if role == "friend":
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
