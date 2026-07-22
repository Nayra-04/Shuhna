from rest_framework.permissions import BasePermission
from .models import User


class IsMerchant(BasePermission):
    message = "هذا الإجراء متاح للتجار فقط"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.MERCHANT
        )


class IsRep(BasePermission):
    message = "هذا الإجراء متاح للمندوبين فقط"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.REP
        )