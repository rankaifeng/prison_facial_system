from django.urls import re_path
from .consumers import DoorEventConsumer, DeviceConsumer

websocket_urlpatterns = [
    re_path(r'ws/door-events/$', DoorEventConsumer.as_asgi()),
    re_path(r'ws/device/$', DeviceConsumer.as_asgi()),
]
