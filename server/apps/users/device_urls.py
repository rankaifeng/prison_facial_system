from django.urls import re_path
from .controllers import FaceRecognitionController
from .controllers.handheld_callback_controller import HandheldCallbackController

# 设备上报接口前缀 /api/v1/，和主系统的 /user_manage/ 互不干扰
urlpatterns = [
    re_path(r'^record/face/?$', FaceRecognitionController.as_view(), name='record_face'),
    re_path(r'^handheld-callback/?$', HandheldCallbackController.as_view(), name='handheld_callback'),
]
