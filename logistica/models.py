from django.db import models
from core.usuarios.models import Usuario


class Sucursal(models.Model):
    nombre     = models.CharField(max_length=100)
    codigo     = models.CharField(max_length=100)
    tipo       = models.CharField(max_length=50, blank=True)
    activo     = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nombre} ({self.codigo})'


class Linea(models.Model):
    TIPOS_LINEA = [
        ("PROPIA",   "Propia"),
        ("EXTERNA",  "Externa"),
    ]
    nombre     = models.CharField(max_length=200)
    clave      = models.CharField(max_length=20, unique=True)
    tipo_linea = models.CharField(max_length=10, choices=TIPOS_LINEA)
    activo     = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.clave} — {self.nombre}'


class Unidad(models.Model):
    TIPO_CHOICES = [
        ("TRACTOR",  "Tractor"),
        ("REMOLQUE", "Remolque"),
    ]
    numero_economico = models.CharField("Número económico", max_length=50, unique=True)
    vin              = models.CharField("VIN", max_length=20, unique=True)
    linea            = models.ForeignKey(Linea, on_delete=models.PROTECT, null=True)
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
        ("INSPECCION",     "Inspección"),
    ]
    unidades              = models.ManyToManyField(Unidad, through="UnidadMovimiento")
    tipo                  = models.CharField(max_length=30, choices=TIPO_CHOICES)
    sucursal              = models.ForeignKey(Sucursal,    on_delete=models.PROTECT)
    manifiesto            = models.ForeignKey(
        "Manifiesto", null=True, blank=True, on_delete=models.SET_NULL, related_name="movimientos"
    )
    fecha_hora_evento     = models.DateTimeField()
    fecha_hora_registro   = models.DateTimeField(auto_now_add=True)
    usuario               = models.ForeignKey(Usuario,    on_delete=models.PROTECT)
    ESTATUS_CAJA_CHOICES = [
        ("CARGA", "Cargada"),
        ("VACIA", "Vacía"),
    ]
    estatus_caja          = models.CharField("Estatus de caja", max_length=5, choices=ESTATUS_CAJA_CHOICES, blank=True)
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


class Manifiesto(models.Model):
    ESTADO_CHOICES = [
        ("BORRADOR",    "Borrador"),
        ("CONFIRMADO",  "Confirmado"),
        ("EN_TRANSITO", "En tránsito"),
        ("COMPLETADO",  "Completado"),
        ("CANCELADO",   "Cancelado"),
    ]
    folio_hoja_viajera = models.CharField("Folio hoja viajera", max_length=50, unique=True, null=True, blank=True)
    unidades           = models.ManyToManyField(Unidad, through="UnidadManifiesto")
    sucursal_origen    = models.ForeignKey(
        Sucursal, on_delete=models.PROTECT, related_name="manifiestos_origen"
    )
    sucursal_destino  = models.ForeignKey(
        Sucursal, on_delete=models.PROTECT, related_name="manifiestos_destino"
    )
    estado            = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="BORRADOR")
    fecha_salida      = models.DateTimeField()
    fecha_llegada_est = models.DateTimeField(null=True, blank=True)
    usuario           = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    numero_fianza     = models.CharField("Número de fianza", max_length=30, blank=True)
    observaciones     = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Hoja Viajera: {self.folio_hoja_viajera} - Manifiesto #{self.pk} — {self.sucursal_origen} → {self.sucursal_destino}'


class UnidadManifiesto(models.Model):
    manifiesto = models.ForeignKey(Manifiesto, on_delete=models.CASCADE, related_name="unidad_manifiestos")
    unidad     = models.ForeignKey(Unidad,     on_delete=models.PROTECT,  related_name="manifiestos")

    class Meta:
        unique_together = [("manifiesto", "unidad")]


TIPO_SUB_INSPECCION = [
    ("GENERAL",           "Inspección general"),
    ("CAJA",              "Inspección de caja"),
    ("CAJA_VACIA",        "Inspección de caja vacía"),
    ("LLANTAS",           "Inspección de llantas"),
    ("CINCO_PUNTOS",      "Inspección 5 puntos VVTTB"),
    ("DIECINUEVE_PUNTOS", "Inspección 19 puntos de seguridad"),
    ("CANINA",            "Inspección canina"),
    ("MEDIDAS_REMOLQUE",  "Inspección de medidas de remolques vacíos"),
]


class PlantillaPunto(models.Model):
    """Catálogo de puntos de revisión por tipo de subinspección."""
    tipo_sub    = models.CharField(max_length=30, choices=TIPO_SUB_INSPECCION)
    descripcion = models.CharField(max_length=200)
    orden       = models.PositiveSmallIntegerField(default=0)
    activo      = models.BooleanField(default=True)

    class Meta:
        ordering = ["tipo_sub", "orden"]

    def __str__(self):
        return f'[{self.get_tipo_sub_display()}] {self.descripcion}'


class Inspeccion(models.Model):
    ESTADO_CHOICES = [
        ("EN_PROCESO", "En proceso"),
        ("COMPLETADA", "Completada"),
        ("RECHAZADA",  "Rechazada"),
    ]
    movimiento    = models.OneToOneField(Movimiento, on_delete=models.PROTECT, related_name="inspeccion")
    estado        = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="EN_PROCESO")
    observaciones = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Inspección #{self.pk} — {self.movimiento}'


class SubInspeccion(models.Model):
    inspeccion         = models.ForeignKey(Inspeccion, on_delete=models.CASCADE, related_name="sub_inspecciones")
    tipo               = models.CharField(max_length=30, choices=TIPO_SUB_INSPECCION)
    comentarios        = models.TextField(blank=True)
    completada          = models.BooleanField(default=False)
    fecha_hora_inicio  = models.DateTimeField(null=True, blank=True)
    fecha_hora_fin     = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("inspeccion", "tipo")]

    def __str__(self):
        return f'{self.get_tipo_display()} — {"completada" if self.fecha_hora_fin else "pendiente"}'


# ─── Choices compartidos en detalles de sub-inspección ───────────────────────

_SINO = [("SI", "Sí"), ("NO", "No")]


# ─── Catálogos ───────────────────────────────────────────────────────────────

class Marca(models.Model):
    nombre            = models.CharField(max_length=100, unique=True)
    aplica_llanta     = models.BooleanField(default=False)
    aplica_remolque   = models.BooleanField(default=False)
    aplica_contenedor = models.BooleanField(default=False)
    activo            = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class PosicionLlanta(models.Model):
    nombre                 = models.CharField(max_length=20, unique=True)
    requerir_en_inspeccion = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class MedidaLlanta(models.Model):
    medida = models.CharField(max_length=30, unique=True)

    class Meta:
        ordering = ["medida"]

    def __str__(self):
        return self.medida


class ConfiguracionInspeccion(models.Model):
    max_fotos = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="Máximo de fotografías por sub-inspección",
    )

    class Meta:
        verbose_name        = "Configuración de inspecciones"
        verbose_name_plural = "Configuración de inspecciones"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Configuración de inspecciones"


# ─── Fotografías (comunes a todas las sub-inspecciones) ───────────────────────

class FotoSubInspeccion(models.Model):
    sub_inspeccion = models.ForeignKey(SubInspeccion, on_delete=models.CASCADE, related_name="fotos")
    imagen         = models.ImageField(upload_to="inspecciones/fotos/")
    etiqueta       = models.CharField(max_length=100, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Foto #{self.pk} — {self.sub_inspeccion}'


# ─── Detalles por tipo de sub-inspección ─────────────────────────────────────

class DetalleGeneral(models.Model):
    sub_inspeccion   = models.OneToOneField(SubInspeccion, on_delete=models.CASCADE, related_name="detalle_general")
    placas           = models.CharField(                 max_length=20,  blank=True)
    estado           = models.CharField(                 max_length=100, blank=True)
    chofer           = models.CharField(                 max_length=100, blank=True)
    anio_remolque     = models.PositiveSmallIntegerField("Año remolque",    null=True, blank=True)
    vin_remolque     = models.CharField("VIN remolque",  max_length=50,  blank=True)
    marca_remolque   = models.ForeignKey(
        Marca, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    anio_contenedor   = models.PositiveSmallIntegerField("Año contenedor",  null=True, blank=True)
    vin_contenedor   = models.CharField("VIN contenedor", max_length=50, blank=True)
    marca_contenedor = models.ForeignKey(
        Marca, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    numero_sello     = models.CharField("# Sello", max_length=50, blank=True)

    def __str__(self):
        return f'General — {self.sub_inspeccion}'


class DetalleCaja(models.Model):
    sub_inspeccion    = models.OneToOneField(SubInspeccion, on_delete=models.CASCADE, related_name="detalle_caja")
    remaches_de_carga = models.CharField(max_length=2, choices=_SINO, blank=True)
    manitas           = models.CharField(max_length=2, choices=_SINO, blank=True)
    patines           = models.CharField(max_length=2, choices=_SINO, blank=True)
    soqueteras        = models.CharField(max_length=2, choices=_SINO, blank=True)
    manivelas         = models.CharField(max_length=2, choices=_SINO, blank=True)
    golpes_y_rallones = models.CharField("Golpes y rayones", max_length=2, choices=_SINO, blank=True)
    reflejantes       = models.CharField(max_length=2, choices=_SINO, blank=True)
    molduras          = models.CharField(max_length=2, choices=_SINO, blank=True)
    bisagras          = models.CharField(max_length=2, choices=_SINO, blank=True)
    llantas           = models.CharField("Llantas sin ponchar", max_length=2, choices=_SINO, blank=True)
    receptor_electrico     = models.CharField("Receptor eléctrico", max_length=2, choices=_SINO, blank=True)
    luz_lateral       = models.CharField("Luz lateral (led/normal)", max_length=2, choices=_SINO, blank=True)
    luz_trasera       = models.CharField("Luz trasera (led/normal)", max_length=2, choices=_SINO, blank=True)

    def __str__(self):
        return f'Caja — {self.sub_inspeccion}'


class DetalleCajaVacia(models.Model):
    sub_inspeccion           = models.OneToOneField(SubInspeccion, on_delete=models.CASCADE, related_name="detalle_caja_vacia")
    techo_libre_filtraciones = models.CharField("Techo libre de filtraciones", max_length=2, choices=_SINO, blank=True)
    libre_olores             = models.CharField("Libre de olores",             max_length=2, choices=_SINO, blank=True)
    pisos_integros           = models.CharField("Pisos íntegros",              max_length=2, choices=_SINO, blank=True)
    paredes_integros         = models.CharField("Paredes íntegras",            max_length=2, choices=_SINO, blank=True)
    techos_integros          = models.CharField("Techos íntegros",             max_length=2, choices=_SINO, blank=True)
    bisagras                 = models.CharField(                                max_length=2, choices=_SINO, blank=True)
    mecanismos_de_cierre     = models.CharField("Mecanismos de cierre",        max_length=2, choices=_SINO, blank=True)
    puertas_simetricas       = models.CharField("Puertas simétricas",          max_length=2, choices=_SINO, blank=True)
    parches_y_reparaciones   = models.CharField("Parches y reparaciones",      max_length=2, choices=_SINO, blank=True)
    limpieza                 = models.CharField(                                max_length=2, choices=_SINO, blank=True)
    paredes_de_interior      = models.CharField("Paredes de interior",         max_length=2, choices=_SINO, blank=True)

    def __str__(self):
        return f'Caja vacía — {self.sub_inspeccion}'


class RegistroLlanta(models.Model):
    sub_inspeccion = models.ForeignKey(SubInspeccion, on_delete=models.CASCADE, related_name="llantas")
    posicion       = models.ForeignKey(PosicionLlanta, on_delete=models.PROTECT)
    cautin         = models.CharField("Cautín",  max_length=50,  blank=True)
    marca          = models.ForeignKey(Marca, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    medida         = models.ForeignKey(MedidaLlanta, null=True, blank=True, on_delete=models.SET_NULL)
    origen         = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = [("sub_inspeccion", "posicion")]

    def __str__(self):
        return f'Llanta pos.{self.posicion} — {self.sub_inspeccion}'


class DetalleCincoPuntos(models.Model):
    sub_inspeccion    = models.OneToOneField(SubInspeccion, on_delete=models.CASCADE, related_name="detalle_cinco_puntos")
    ver_sellos        = models.CharField("Vea sellos y mecanismos",      max_length=2, choices=_SINO, blank=True)
    verificar_sello   = models.CharField("Verifique número de sello",    max_length=2, choices=_SINO, blank=True)
    tirar_sello       = models.CharField("Tire del sello",               max_length=2, choices=_SINO, blank=True)
    torcer_sello      = models.CharField("Tuerza y gire el sello",       max_length=2, choices=_SINO, blank=True)
    verificar_bisagra = models.CharField("Verifique bisagras aseguradas", max_length=2, choices=_SINO, blank=True)

    def __str__(self):
        return f'5 puntos VVTTB — {self.sub_inspeccion}'


class DetalleDiecinuevePuntos(models.Model):
    sub_inspeccion          = models.OneToOneField(SubInspeccion, on_delete=models.CASCADE, related_name="detalle_diecinueve_puntos")
    defensa                 = models.CharField(max_length=2, choices=_SINO, blank=True)
    llantas_y_rines         = models.CharField("Llantas y rines",          max_length=2, choices=_SINO, blank=True)
    piso_tractor            = models.CharField("Piso del tractor",         max_length=2, choices=_SINO, blank=True)
    tanque_gasolina         = models.CharField("Tanque de gasolina",       max_length=2, choices=_SINO, blank=True)
    interior_cabina         = models.CharField("Interior de cabina",       max_length=2, choices=_SINO, blank=True)
    tanques_de_aire         = models.CharField("Tanques de aire",          max_length=2, choices=_SINO, blank=True)
    chasis_y_quinta_rueda   = models.CharField("Chasis y quinta rueda",    max_length=2, choices=_SINO, blank=True)
    ejes_de_transmision     = models.CharField("Ejes de transmisión",      max_length=2, choices=_SINO, blank=True)
    tubo_de_escape          = models.CharField("Tubo de escape",           max_length=2, choices=_SINO, blank=True)
    motor                   = models.CharField(                             max_length=2, choices=_SINO, blank=True)
    base_del_remolque       = models.CharField("Base del remolque",        max_length=2, choices=_SINO, blank=True)
    puertas_interiores      = models.CharField("Puertas interiores",       max_length=2, choices=_SINO, blank=True)
    pared_lateral_derecha   = models.CharField("Pared lateral derecha",    max_length=2, choices=_SINO, blank=True)
    techo_interno_y_externo = models.CharField("Techo interno y externo",  max_length=2, choices=_SINO, blank=True)
    pared_frontal           = models.CharField("Pared frontal",            max_length=2, choices=_SINO, blank=True)
    pared_lateral_izquierda = models.CharField("Pared lateral izquierda",  max_length=2, choices=_SINO, blank=True)
    piso_interno            = models.CharField("Piso interno",             max_length=2, choices=_SINO, blank=True)
    eje_palanca_patin       = models.CharField("Eje palanca/patín",        max_length=2, choices=_SINO, blank=True)
    sistema_refrigeracion   = models.CharField("Sistema de refrigeración", max_length=2, choices=_SINO, blank=True)

    def __str__(self):
        return f'19 puntos — {self.sub_inspeccion}'


class DetalleCanina(models.Model):
    sub_inspeccion = models.OneToOneField(SubInspeccion, on_delete=models.CASCADE, related_name="detalle_canina")
    aprobado       = models.CharField(max_length=2, choices=_SINO, blank=True)

    def __str__(self):
        return f'Canina — {self.sub_inspeccion}'


class DetalleMedidasRemolque(models.Model):
    sub_inspeccion = models.OneToOneField(SubInspeccion, on_delete=models.CASCADE, related_name="detalle_medidas_remolque")
    largo          = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="metros")
    ancho          = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="metros")
    alto           = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="metros")

    def __str__(self):
        return f'Medidas remolque — {self.sub_inspeccion}'
