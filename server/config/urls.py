from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from apps.users.controllers.video_controller import serve_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user_manage/', include('apps.users.urls')),
    path('prison_manage/', include('apps.users.prison_urls')),
    path('api/v1/', include('apps.users.device_urls')),
    # media 文件服务（自定义视图，兼容 Daphne/Channels）
    re_path(r'^media/(?P<path>.*)$', serve_media, name='serve_media'),
]
