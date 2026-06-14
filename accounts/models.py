from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    SELLER = "SELLER", "Seller"
    BUYER = "BUYER", "Buyer"


class User(AbstractUser):
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.BUYER,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_seller(self):
        return self.role == UserRole.SELLER

    @property
    def is_buyer(self):
        return self.role == UserRole.BUYER

    def __str__(self):
        return f"{self.username} ({self.role})"
