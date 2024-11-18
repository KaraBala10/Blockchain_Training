from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", obtain_auth_token, name="login"),
    path("balance/", views.balance_view, name="balance"),
    path("transfer/", views.transfer_view, name="transfer"),
    path("profile/", views.profile_view, name="profile"),
    path("accounts/", views.list_accounts_view, name="list_accounts"),
    path("custom-login/", views.custom_login_view, name="custom_login"),
]
