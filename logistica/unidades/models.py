from django.db import models
from logistica.sucursales.models import Sucursal


class Unidad(models.Model):
    TIPO_CHOICES = [
        ("TRACTOR",  "Tractor"),
        ("REMOLQUE", "Remolque"),
    ]
    numero_economico = models.CharField(max_length=50, unique=True)
    tipo             = models.CharField(max_length=20, choices=TIPO_CHOICES)
    sucursal_actual  = models.ForeignKey(
        Sucursal, null=True, blank=True, on_delete=models.SET_NULL
    )
    activo     = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
