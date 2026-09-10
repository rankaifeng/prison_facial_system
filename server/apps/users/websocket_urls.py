from django.urls import re_path
from .consumers import DoorEventConsumer, DeviceConsumer

websocket_urlpatterns = [
    re_path(r'ws/door-events/$', DoorEventConsumer.as_asgi()),
    re_path(r'ws/device/$', DeviceConsumer.as_asgi()),
    re_path(r'.*', DeviceConsumer.as_asgi()),  # 兜底：设备只填 IP:端口（无路径）时走这里
]
