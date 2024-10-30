from typing import Any
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager


class CustomUserManager(UserManager):
    def create_superuser(
        self,
        username: str,
        email: str | None,
        password: str | None,
        **extra_fields: Any
    ) -> Any:
        extra_fields.setdefault("role", "admin")
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    ADMIN = "admin"
    USER = "user"
    FRIEND = "friend"

    ROLE_CHOICES = [(ADMIN, "Admin"), (USER, "User"), (FRIEND, "Friend")]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=USER)
    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_friends",
    )

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.ADMIN
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-date_joined"]
        permissions = [
            ("can_view_analytics", "Can view analytics"),
            ("can_create_friends", "Can create friend accounts"),
            ("can_manage_own_friends", "Can manage own friend accounts"),
        ]
