from django.contrib import admin
from market import models

# Register your models here.
admin.site.register(models.MarketUser)
admin.site.register(models.Offer)
admin.site.register(models.OfferDetail)