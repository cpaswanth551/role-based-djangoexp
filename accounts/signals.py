from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User


@receiver(post_save, sender=User)
def ensure_superuser_admin_role(sender, instance, created, **kwargs):
    if instance.is_superuser:
        if instance.role != "admin":
            instance.role = "admin"
            instance.save(update_fields=["role"])

        admin_group = Group.objects.get(name="Admin")
        if admin_group not in instance.groups.all():
            instance.groups.add(admin_group)


@receiver(post_migrate)
def create_default_groups_permissions(sender, **kwargs):
    try:

        content_type = ContentType.objects.get_for_model(User)

        # Create permissions if they don't exist
        permissions = {
            "can_view_analytics": "Can view analytics",
            "can_create_friends": "Can create friend accounts",
            "can_manage_own_friends": "Can manage own friend accounts",
        }

        created_permissions = []
        for codename, name in permissions.items():
            permission, created = Permission.objects.get_or_create(
                codename=codename, content_type=content_type, defaults={"name": name}
            )
            created_permissions.append(permission)

        # Create groups
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        user_group, _ = Group.objects.get_or_create(name="User")
        friend_group, _ = Group.objects.get_or_create(name="Friend")

        # Assign permissions to groups
        admin_group.permissions.set(created_permissions)
        user_group.permissions.set(
            [
                perm
                for perm in created_permissions
                if perm.codename in ["can_create_friends", "can_manage_own_friends"]
            ]
        )
        friend_group.permissions.clear()

        # Ensure all superusers are in admin group and have admin role
        for superuser in User.objects.filter(is_superuser=True):
            superuser.role = "admin"
            superuser.groups.add(admin_group)
            superuser.save(update_fields=["role"])

        print("Groups and permissions configured successfully!")
        print(f"Created/Updated permissions: {', '.join(permissions.keys())}")
        print(f"Created/Updated groups: Admin, User, Friend")

    except Exception as e:
        print(f"Error setting up permissions and groups: {str(e)}")
