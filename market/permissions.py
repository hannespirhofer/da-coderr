from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed

from market.models import MarketUser

class isOwnerOr405(BasePermission):
    """
    Checking if the request user is the owner
    """
    def has_object_permission(self, request, view, obj):
        if obj.user != request.user:
            raise AuthenticationFailed()
        return True

class IsBusiness(BasePermission):
    """
    Allows access only to business accounts.
    """
    message = "Restricted to Business Users"

    def has_permission(self, request, view):
        user = request.user
        try:
            marketuser = MarketUser.objects.get(user=user)
        except MarketUser.DoesNotExist:
            self.message = "No Marketuser connected to this user"
            return False
        return bool(marketuser and marketuser.type == 'business')

class isOfferOwner(BasePermission):
    """
    Allows only offer owner
    """

    def has_object_permission(self, request, view, obj):
        try:
            marketuser = MarketUser.objects.get(user=request.user)
        except MarketUser.DoesNotExist:
            return False
        return obj.user == marketuser
