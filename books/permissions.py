from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """
    GET/HEAD/OPTIONS — дозволено всім, включно з анонімними користувачами.
    POST/PUT/PATCH/DELETE — лише для request.user.is_staff.
    """

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
