from django.urls import include, path
from rest_framework.routers import DefaultRouter
from market.views import *

router = DefaultRouter()
router.register(r'offers', OfferViewset, basename='offers')
router.register(r'orders', OrderViewset, basename='orders')
router.register(r'reviews', ReviewViewset, basename='reviews')


urlpatterns = [

    #Viewsets auto generated urls
    path('', include(router.urls)),

    # Market Auth
    path('login/', LoginView.as_view(), name='login'),
    path('registration/', RegisterView.as_view(), name='register'),

    # Profile Marketuser
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),

    # Marketuser List by Type
    path('profiles/customer/', CustomerListView.as_view(), name='customer-list'),
    path('profiles/business/', BusinessListView.as_view(), name='business-list'),

    # OfferDetail View
    path('offerdetails/<int:pk>/', OfferDetailView.as_view(), name='offerdetail'),

    # Order Custom Views
    path('order-count/<int:pk>/', BusinessOrderCount.as_view(), name='business-order-count'),
    path('completed-order-count/<int:pk>/', BusinessCompletedOrderCount.as_view(), name='business-completed-order-count'),

    # Base Info
    path('base-info/', BaseInfoView.as_view(), name='base-info'),

    # DRF Auth /login /register
    path('api-auth/', include('rest_framework.urls'))
]