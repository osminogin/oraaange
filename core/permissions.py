from rest_framework import permissions


class OnlyOwnerAllowedEdit(permissions.BasePermission):
    """
    Доступ к объeкту только владельцу объекта.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Superuser always allowed
        if request.user.is_superuser:
            return True

        # Instance must have an attribute named `owner`.
        return obj.owner == request.user
