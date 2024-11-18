from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class RegistrationForm(UserCreationForm):
    username = forms.CharField(max_length=150, required=True, help_text="اسم المستخدم")
    password1 = forms.CharField(
        widget=forms.PasswordInput, label="كلمة المرور", help_text="كلمة المرور"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        label="تأكيد كلمة المرور",
        help_text="تأكيد كلمة المرور",
    )

    class Meta:
        model = CustomUser
        fields = ("username", "password1", "password2")


class TransferForm(forms.Form):
    to_username = forms.CharField(max_length=150, label="اسم المستخدم للمستلم")
    amount = forms.DecimalField(max_digits=18, decimal_places=8, label="المبلغ")
