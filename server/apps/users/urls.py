from django.urls import path
from .views import LoginView

urlpatterns = [
    path('user_login_web/', LoginView.as_view(), name='login'),
]
