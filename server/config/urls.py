from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user_manage/', include('apps.users.urls')),
    path('prison_manage/', include('apps.users.prison_urls')),
]
