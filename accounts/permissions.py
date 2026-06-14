from rest_framework.permissions import BasePermission

from accounts.models import UserRole


class IsSeller(BasePermission):
    message = "Only sellers can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.SELLER
        )


class IsBuyer(BasePermission):
    message = "Only buyers can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.BUYER
        )
