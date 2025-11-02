from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level permission to only allow owners to edit it."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.uploader == request.user


class IsStaffOrReadOnly(permissions.BasePermission):
    """Allow staff users to edit, others can only read."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user and request.user.is_staff


class IsOwnerOrStaff(permissions.BasePermission):
    """Allow owners and staff to access the object."""

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        return hasattr(obj, 'uploader') and obj.uploader == request.user


class HasImportPermission(permissions.BasePermission):
    """Custom permission for import operations."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Staff can do anything
        if request.user.is_staff:
            return True

        # Regular users can create imports
        if view.action in ['create', 'list', 'retrieve']:
            return True

        # Only staff can perform destructive actions
        if view.action in ['destroy', 'update']:
            return False

        return True


class CanRetryFailedImport(permissions.BasePermission):
    """Permission to retry failed imports."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff:
            return True

        # Users can only retry their own failed imports
        return obj.uploader == request.user and obj.status == 'FAILURE'