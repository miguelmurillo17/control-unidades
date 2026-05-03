from django.db import models
from core.usuarios.models import Usuario
from logistica.unidades.models import Unidad
from logistica.sucursales.models import Sucursal


class Movimiento(models.Model):
    TIPO_CHOICES = [
        ("ENTRADA",        "Entrada"),
        ("SALIDA",         "Salida"),
        ("TALLER_ENTRADA", "Entrada a taller"),
        ("TALLER_SALIDA",  "Salida de taller"),
        ("CORRECCION",     "Corrección"),
    ]
    unidad                = models.ForeignKey(Unidad,    on_delete=models.PROTECT)
    tipo                  = models.CharField(max_length=30, choices=TIPO_CHOICES)
    sucursal              = models.ForeignKey(Sucursal,  on_delete=models.PROTECT)
    fecha_hora_evento     = models.DateTimeField()
    fecha_hora_registro   = models.DateTimeField(auto_now_add=True)
    usuario               = models.ForeignKey(Usuario,   on_delete=models.PROTECT)
    observaciones         = models.TextField(blank=True)
    inconsistente         = models.BooleanField(default=False)
    cancelado             = models.BooleanField(default=False)
    referencia_movimiento = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )
