from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsRegularUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "user"


class IsFriendUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "friend"


class UserPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        if request.method == "POST":
            if request.user.role == "admin":
                return True
            return request.user.has_perm("accounts.can_create_friends")

        return True

    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.role == "admin":
            return True

        # Users can manage their own profile
        if obj == request.user:
            return True

        # Users can manage friends they created if they have permission
        if obj.created_by == request.user and request.user.has_perm(
            "accounts.can_manage_own_friends"
        ):
            return True

        # For safe methods, allow if user has view permission
        if request.method in permissions.SAFE_METHODS:
            return True

        return False
