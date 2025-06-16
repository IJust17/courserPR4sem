from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    - SAFE-методы (GET, HEAD, OPTIONS) доступны всем.
    - Любые изменения могут делать только администраторы (is_staff).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
