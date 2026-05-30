from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from apps.users.controllers.video_controller import serve_hls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user_manage/', include('apps.users.urls')),
    path('prison_manage/', include('apps.users.prison_urls')),
    # HLS流媒体文件服务
    re_path(r'^media/hls/(?P<path>.*)$', serve_hls, name='hls_stream'),
]

# 开发环境提供 media 文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
