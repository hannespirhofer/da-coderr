from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from rest_framework.status import HTTP_403_FORBIDDEN
from market.models import Offer

from market.models import MarketUser

class isOwnerOr405(BasePermission):
    """
    Checking if the request user is the owner
    """
    def has_object_permission(self, request, view, obj):
        request_marketuser = MarketUser.objects.get(user = request.user)
        obj_marketuser = MarketUser.objects.get(pk=obj.user.pk)

        if obj_marketuser != request_marketuser:
            raise PermissionDenied('You are not allowed to patch this profile', code=HTTP_403_FORBIDDEN)
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

class IsCustomer(BasePermission):
    """
    Allows access only to customer accounts.
    """
    message = "Restricted to Customer Users"

    def has_permission(self, request, view):
        user = request.user
        try:
            marketuser = MarketUser.objects.get(user=user)
        except MarketUser.DoesNotExist:
            self.message = "No Marketuser connected to this user"
            return False
        return bool(marketuser and marketuser.type == 'customer')

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
