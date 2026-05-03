from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    ROLE_CHOICES = [
        ("CASETA", "Caseta"),
        ("TRAFICO", "Tráfico"),
        ("ADMIN", "Administrador"),
    ]
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES)
