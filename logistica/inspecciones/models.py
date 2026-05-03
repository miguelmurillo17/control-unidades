from django.db import models
from logistica.movimientos.models import Movimiento


class Inspeccion(models.Model):
    movimiento        = models.OneToOneField(Movimiento, on_delete=models.CASCADE)
    resultado_general = models.CharField(max_length=50, blank=True)
    observaciones     = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)


class DetalleInspeccion(models.Model):
    inspeccion     = models.ForeignKey(Inspeccion, on_delete=models.CASCADE)
    punto_revision = models.CharField(max_length=100)
    resultado      = models.CharField(max_length=20)  # "SI" | "NO" | "NA"
    comentario     = models.TextField(blank=True)
