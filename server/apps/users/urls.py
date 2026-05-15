from django.urls import path, re_path
from .views import LoginView, AccountListView, AccountDeleteView

urlpatterns = [
    re_path(r'^user_login/user_login_web/?$', LoginView.as_view(), name='login'),
    re_path(r'^account/account_list/?$', AccountListView.as_view(), name='account_list'),
    re_path(r'^account/account_add/?$', AccountListView.as_view(), name='account_add'),
    re_path(r'^account/account_delete/?$', AccountDeleteView.as_view(), name='account_delete'),
]
