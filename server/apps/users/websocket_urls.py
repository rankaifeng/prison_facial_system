from django.urls import re_path
from .consumers import DoorEventConsumer

websocket_urlpatterns = [
    re_path(r'ws/door-events/$', DoorEventConsumer.as_asgi()),
]
