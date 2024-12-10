from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Изменять или удалять объект может только автор."""
    def has_object_permission(self, request, view, obj):
        if request.method in ['DELETE', 'PUT', 'PATCH']:
            return obj.author == request.user
        return True
