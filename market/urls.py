from django.urls import include, path
from rest_framework.routers import DefaultRouter
from market.views import BusinessCompletedOrderCount, BusinessOrderCount, LoginView, OfferDetailView, OrderViewset, RegisterView, ProfileDetailView, CustomerListView, BusinessListView, OfferViewset, ReviewViewset

router = DefaultRouter()
router.register(r'offers', OfferViewset, basename='offers')
router.register(r'orders', OrderViewset, basename='orders')
router.register(r'reviews', ReviewViewset, basename='reviews')


urlpatterns = [

    #Viewsets auto generated urls
    path('', include(router.urls)),

    # Market Auth
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),

    # Profile Marketuser
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),

    # Marketuser List by Type
    path('profile/customer/', CustomerListView.as_view(), name='customer-list'),
    path('profile/business/', BusinessListView.as_view(), name='business-list'),

    # OfferDetail View
    path('offerdetails/<int:pk>/', OfferDetailView.as_view(), name='offerdetail'),

    # Order Custom Views
    path('order-count/<int:pk>/', BusinessOrderCount.as_view(), name='business-order-count'),
    path('completed-order-count/<int:pk>/', BusinessCompletedOrderCount.as_view(), name='business-completed-order-count'),


    # DRF Auth /login /register
    path('api-auth/', include('rest_framework.urls'))
]
