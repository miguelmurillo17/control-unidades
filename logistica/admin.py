from django.contrib import admin
from .models import (
    Sucursal, Unidad, Movimiento,
    PlantillaPunto, Inspeccion, SubInspeccion,
    Marca, PosicionLlanta, MedidaLlanta, ConfiguracionInspeccion,
    FotoSubInspeccion,
    DetalleGeneral, DetalleCaja, DetalleCajaVacia, RegistroLlanta,
    DetalleCincoPuntos, DetalleDiecinuevePuntos, DetalleCanina, DetalleMedidasRemolque,
)


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "ciudad", "tipo", "activo", "created_at")
    list_filter   = ("activo", "tipo")
    search_fields = ("nombre", "ciudad")


@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display  = ("numero_economico", "tipo", "sucursal_actual", "activo", "created_at")
    list_filter   = ("tipo", "activo", "sucursal_actual")
    search_fields = ("numero_economico",)


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = (
        "get_unidades", "tipo", "sucursal", "fecha_hora_evento",
        "usuario", "inconsistente", "cancelado",
    )
    list_filter   = ("tipo", "inconsistente", "cancelado", "sucursal")
    search_fields = ("unidades__numero_economico", "observaciones")
    readonly_fields = (
        "unidades", "tipo", "sucursal", "fecha_hora_evento",
        "fecha_hora_registro", "usuario", "observaciones",
        "inconsistente", "referencia_movimiento",
    )

    def get_unidades(self, obj):
        return ", ".join(u.numero_economico for u in obj.unidades.all())
    get_unidades.short_description = "Unidades"

    def has_delete_permission(self, _request, _obj=None):
        return False


@admin.register(PlantillaPunto)
class PlantillaPuntoAdmin(admin.ModelAdmin):
    list_display  = ("tipo_sub", "descripcion", "orden", "activo")
    list_filter   = ("tipo_sub", "activo")
    search_fields = ("descripcion",)
    ordering      = ("tipo_sub", "orden")


# ─── Catálogos ────────────────────────────────────────────────────────────────

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "aplica_llanta", "aplica_remolque", "aplica_contenedor", "activo")
    list_filter   = ("aplica_llanta", "aplica_remolque", "aplica_contenedor", "activo")
    search_fields = ("nombre",)


@admin.register(PosicionLlanta)
class PosicionLlantaAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "requerir_en_inspeccion")
    list_filter   = ("requerir_en_inspeccion",)


@admin.register(MedidaLlanta)
class MedidaLlantaAdmin(admin.ModelAdmin):
    list_display  = ("medida",)
    search_fields = ("medida",)


@admin.register(ConfiguracionInspeccion)
class ConfiguracionInspeccionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not ConfiguracionInspeccion.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ─── Inspecciones ─────────────────────────────────────────────────────────────

class SubInspeccionInline(admin.TabularInline):
    model  = SubInspeccion
    extra  = 0
    fields = ("tipo", "comentarios", "fecha_hora_inicio", "fecha_hora_fin")
    readonly_fields = ("tipo",)


@admin.register(Inspeccion)
class InspeccionAdmin(admin.ModelAdmin):
    list_display  = ("pk", "movimiento", "estado", "created_at")
    list_filter   = ("estado",)
    search_fields = ("movimiento__manifiesto__folio_hoja_viajera",)
    inlines       = [SubInspeccionInline]


class FotoSubInspeccionInline(admin.TabularInline):
    model  = FotoSubInspeccion
    extra  = 0
    fields = ("imagen", "etiqueta")


class RegistroLlantaInline(admin.TabularInline):
    model  = RegistroLlanta
    extra  = 0
    fields = ("posicion", "cautin", "marca", "medida", "origen")


@admin.register(SubInspeccion)
class SubInspeccionAdmin(admin.ModelAdmin):
    list_display  = ("inspeccion", "tipo", "fecha_hora_inicio", "fecha_hora_fin")
    list_filter   = ("tipo",)
    inlines       = [FotoSubInspeccionInline, RegistroLlantaInline]
