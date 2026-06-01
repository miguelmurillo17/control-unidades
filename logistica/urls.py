from django.urls import include, path

from .views import (
    LineaListView,
    LineaCreateView,
    LineaUpdateView,
    LineaDeleteView,
    SucursalListView,
    SucursalCreateView,
    SucursalUpdateView,
    SucursalDeleteView,
    UnidadListView,
    UnidadCreateView,
    UnidadUpdateView,
    UnidadDeleteView,
    registrar_movimiento,
    todos_los_registros,
    mis_registros,
    mis_inspecciones,
    manifiestos_list,
    registrar_manifiesto,
    editar_manifiesto,
    manifiesto_movimientos,
    inspeccion_detalle,
    inspeccion_pdf,
    sub_inspeccion_form,
    cerrar_inspeccion,
)

lineas_urls = ([
    path("", LineaListView.as_view(), name="list"),
    path("nueva/", LineaCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", LineaUpdateView.as_view(), name="update"),
    path("<int:pk>/eliminar/", LineaDeleteView.as_view(), name="delete"),
], "lineas")

sucursales_urls = ([
    path("", SucursalListView.as_view(), name="list"),
    path("nueva/", SucursalCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", SucursalUpdateView.as_view(), name="update"),
    path("<int:pk>/eliminar/", SucursalDeleteView.as_view(), name="delete"),
], "sucursales")

unidades_urls = ([
    path("", UnidadListView.as_view(), name="list"),
    path("nueva/", UnidadCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", UnidadUpdateView.as_view(), name="update"),
    path("<int:pk>/eliminar/", UnidadDeleteView.as_view(), name="delete"),
], "unidades")

manifiestos_urls = ([
    path("", manifiestos_list, name="list"),
    path("nuevo/", registrar_manifiesto, name="create"),
    path("<int:pk>/editar/", editar_manifiesto, name="update"),
    path("<int:pk>/movimientos/", manifiesto_movimientos, name="movimientos"),
], "manifiestos")

urlpatterns = [
    path("lineas/", include(lineas_urls)),
    path("sucursales/", include(sucursales_urls)),
    path("unidades/", include(unidades_urls)),
    path("manifiestos/", include(manifiestos_urls)),
    path("movimientos/", todos_los_registros, name="todos_los_registros"),
    path("movimientos/registrar/", registrar_movimiento, name="registrar_movimiento"),
    path("movimientos/mis-registros/", mis_registros, name="mis_registros"),
    path("inspecciones/", mis_inspecciones, name="mis_inspecciones"),
    path("inspecciones/<int:pk>/", inspeccion_detalle, name="inspeccion_detalle"),
    path("inspecciones/<int:pk>/sub/<int:sub_pk>/", sub_inspeccion_form, name="sub_inspeccion_form"),
    path("inspecciones/<int:pk>/pdf/", inspeccion_pdf, name="inspeccion_pdf"),
    path("inspecciones/<int:pk>/cerrar/", cerrar_inspeccion, name="cerrar_inspeccion"),
]
