from django.contrib import admin
from .models import Sucursal, Unidad, Movimiento, Inspeccion, DetalleInspeccion


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ciudad", "tipo", "activo", "created_at")
    list_filter = ("activo", "tipo")
    search_fields = ("nombre", "ciudad")


@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ("numero_economico", "tipo",
                    "sucursal_actual", "activo", "created_at")
    list_filter = ("tipo", "activo", "sucursal_actual")
    search_fields = ("numero_economico",)


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = (
        "get_unidades", "tipo", "sucursal", "fecha_hora_evento",
        "usuario", "inconsistente", "cancelado",
    )
    list_filter  = ("tipo", "inconsistente", "cancelado", "sucursal")
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


class DetalleInspeccionInline(admin.TabularInline):
    model = DetalleInspeccion
    extra = 0
    fields = ("punto_revision", "resultado", "comentario")


@admin.register(Inspeccion)
class InspeccionAdmin(admin.ModelAdmin):
    list_display = ("movimiento", "resultado_general", "created_at")
    search_fields = ("movimiento__unidad__numero_economico",)
    inlines = [DetalleInspeccionInline]
