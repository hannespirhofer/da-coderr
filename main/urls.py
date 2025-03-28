from django.contrib import admin
from django.urls import include, path

from market.views import LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('market.urls'))
]
