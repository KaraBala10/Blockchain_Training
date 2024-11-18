import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from web3 import Web3

web3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER))


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError("يجب تحديد اسم المستخدم.")
        account = web3.eth.account.create(secrets.token_hex(16))
        extra_fields.setdefault("wallet_address", account.address)
        extra_fields.setdefault("private_key", account.key.hex())
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("المشرف يجب أن يكون لديه is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("المشرف يجب أن يكون لديه is_superuser=True.")
        return self.create_user(username, password, **extra_fields)


class CustomUser(AbstractUser):
    wallet_address = models.CharField(max_length=42, unique=True)
    private_key = models.CharField(max_length=66)

    objects = CustomUserManager()

    def __str__(self):
        return self.username
