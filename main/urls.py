from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from market.views import LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('market.urls'))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)