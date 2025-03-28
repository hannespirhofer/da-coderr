from django.urls import include, path
from market.views import LoginView, RegisterView, ProfileDetailView, CustomerListView, BusinessListView

urlpatterns = [

    # Market Auth
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),

    # Profile Marketuser
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),

    # Marketuser List by Type
    path('profile/customer/', CustomerListView.as_view(), name='customer-list'),
    path('profile/business/', BusinessListView.as_view(), name='business-list'),


    # DRF Auth /login /register
    path('api-auth/', include('rest_framework.urls'))
]
