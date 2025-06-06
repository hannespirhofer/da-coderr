import random
from django.db import models
from django.contrib.auth.models import User
from market.constants import CUSTOMER_TYPE, ORDER_STATUS

class MarketUser(models.Model):
    #registration fields
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
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
    type = models.CharField(choices=CUSTOMER_TYPE, max_length=50)

    def __str__(self):
        return (f"Marketuser PK: {self.pk}; User PK {self.user.pk} - {self.first_name} {self.last_name} ({self.user.username} [{self.type}])")

#Pakete wie Grafikpaket
class Offer(models.Model):
    user = models.ForeignKey(MarketUser, on_delete=models.CASCADE, verbose_name='Market User')
    title = models.CharField(max_length=100)
    image = models.FileField(upload_to='offer-images/', blank=True, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    min_price = models.IntegerField(blank=True, null=True, default=int(random.random()*100))
    min_delivery_time = models.IntegerField(blank=True, null=True, default=int(random.random()*100))

    def __str__(self):
        return f"{self.title} [{self.pk}]"

#DL wie Basic Design
class OfferDetail(models.Model):
    offer = models.ForeignKey(Offer, related_name='details', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    revisions = models.IntegerField()
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.title} [{self.pk}]"

#Orders
class Order(models.Model):
    offerdetail = models.ForeignKey(OfferDetail, on_delete=models.PROTECT, related_name='order')
    #additional
    customer_user = models.ForeignKey(MarketUser, on_delete=models.PROTECT, related_name='order_customer')
    business_user = models.ForeignKey(MarketUser, on_delete=models.PROTECT, related_name='order_business')
    # get title, revisions, delivery_time, price, features and type from offerdetail here too
    status = models.CharField(choices=ORDER_STATUS, default='inprogress' ,max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - Order from: {self.customer_user.first_name}"


class Review(models.Model):
    business_user = models.ForeignKey(MarketUser, on_delete=models.PROTECT, related_name='review_business_user')
    reviewer = models.ForeignKey(MarketUser, on_delete=models.PROTECT, related_name='reviewer')
    rating = models.PositiveIntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.reviewer.first_name} rated {self.business_user.first_name} | Rating: {self.rating}"

