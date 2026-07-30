from django.urls import re_path
from .controllers import FaceRecognitionController

# 设备上报接口前缀 /api/v1/，与一体机固件约定一致，和主系统的 /user_manage/ 互不干扰
urlpatterns = [
    re_path(r'^record/face/?$', FaceRecognitionController.as_view(), name='record_face'),
]
