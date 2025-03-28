from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed

class isOwnerOr405(BasePermission):
    """
    Checking if the request user is the owner
    """
    def has_object_permission(self, request, view, obj):
        if obj.user != request.user:
            raise AuthenticationFailed()
        return True