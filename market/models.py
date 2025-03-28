from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from market.constants import CUSTOMER_TYPE

class MarketUser(models.Model):
    #registration fields
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    #autoadded fields
    created_at = models.DateTimeField(auto_now_add=True)
    #patch fields
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    file = models.FileField(upload_to='profile-images/', blank=True, null=True)
    location = models.CharField(max_length=30, blank=True, null=True)
    tel = models.CharField(max_length=30, blank=True, null=True)
    description = models.CharField(max_length=150, blank=True, null=True)
    working_hours = models.CharField(max_length=15, blank=True, null=True)
    type = models.CharField(choices=CUSTOMER_TYPE, max_length=20)

    def __str__(self):
        return (f"ID {self.pk}: {self.user.username} [{self.type}]")