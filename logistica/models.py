from django.db import models
from core.usuarios.models import Usuario


class Sucursal(models.Model):
    nombre     = models.CharField(max_length=100)
    ciudad     = models.CharField(max_length=100)
    tipo       = models.CharField(max_length=50, blank=True)
    activo     = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nombre} ({self.ciudad})'


class Unidad(models.Model):
    TIPO_CHOICES = [
        ("TRACTOR",  "Tractor"),
        ("REMOLQUE", "Remolque"),
    ]
    numero_economico = models.CharField("Número económico", max_length=50, unique=True)
    tipo             = models.CharField(max_length=20, choices=TIPO_CHOICES)
    sucursal_actual  = models.ForeignKey(
        Sucursal, null=True, blank=True, on_delete=models.SET_NULL
    )
    activo     = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.numero_economico}'


class Movimiento(models.Model):
    TIPO_CHOICES = [
        ("ENTRADA",        "Entrada"),
        ("SALIDA",         "Salida"),
        ("TALLER_ENTRADA", "Entrada a taller"),
        ("TALLER_SALIDA",  "Salida de taller"),
        ("CORRECCION",     "Corrección"),
    ]
    unidades              = models.ManyToManyField(Unidad, through="UnidadMovimiento")
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


class UnidadMovimiento(models.Model):
    movimiento = models.ForeignKey(Movimiento, on_delete=models.CASCADE, related_name="unidad_movimientos")
    unidad     = models.ForeignKey(Unidad,     on_delete=models.PROTECT,  related_name="movimientos")

    class Meta:
        unique_together = [("movimiento", "unidad")]


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
