from django.contrib import admin
from django.urls import path, include
from apps.users.views import LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user_manage/user_login/user_login_web', LoginView.as_view(), name='login'),
]
