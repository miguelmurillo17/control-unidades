from django.contrib.auth.forms import UserCreationForm
from django import forms

from .models import Usuario


class UsuarioCreacionForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "rol", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["rol"].required = True


class UsuarioEdicionForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "rol", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["rol"].required = True
