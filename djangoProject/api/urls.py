from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.custom_login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("balance/", views.balance_view, name="balance"),
    path("accounts/", views.list_accounts_view, name="list_accounts"),
    path("mint-tokens/", views.mint_tokens_view, name="mint_tokens"),
    path("transfer/", views.transfer_view, name="transfer"),
]
