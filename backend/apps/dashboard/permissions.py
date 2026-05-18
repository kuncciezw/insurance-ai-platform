from __future__ import annotations

from typing import Any

from rest_framework import permissions
from rest_framework.request import Request


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:  # type: ignore[override]
        profile = getattr(request.user, 'profile', None)
        return (
            bool(request.user and request.user.is_authenticated)
            and profile is not None
            and profile.role == 'SUPER_ADMIN'
        )


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:  # type: ignore[override]
        profile = getattr(request.user, 'profile', None)
        return (
            bool(request.user and request.user.is_authenticated)
            and profile is not None
            and profile.role in ('SUPER_ADMIN', 'ADMIN')
        )


class CanManageUsers(permissions.BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:  # type: ignore[override]
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, 'profile', None)
        if profile is None:
            return False
        return bool(profile.can_manage_users())


class RoleBasedPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:  # type: ignore[override]
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, 'profile', None)
        if profile is None:
            return False

        required_roles = getattr(view, 'required_roles', None)
        if required_roles is None:
            return True

        method_roles: dict[str, list[str]] = getattr(view, 'method_roles', {})
        if request.method in method_roles:
            required_roles = method_roles[request.method]

        return bool(profile.role in required_roles)