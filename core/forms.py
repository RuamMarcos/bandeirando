from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User

from .models import AVATARES


class BootstrapMixin:
    """Aplica as classes do Bootstrap em todos os campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget, (forms.RadioSelect, forms.CheckboxInput)):
                continue
            campo.widget.attrs["class"] = "form-control form-control-lg"


class LoginForm(BootstrapMixin, AuthenticationForm):
    pass


class CadastroForm(BootstrapMixin, UserCreationForm):
    email = forms.EmailField(label="E-mail", required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class SenhaForm(BootstrapMixin, PasswordChangeForm):
    pass


class PerfilForm(BootstrapMixin, forms.Form):
    first_name = forms.CharField(label="Nome", max_length=30, required=False)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=False)
    email = forms.EmailField(label="E-mail", required=False)
    avatar = forms.ChoiceField(label="Avatar", choices=[(a, a) for a in AVATARES], widget=forms.RadioSelect)
