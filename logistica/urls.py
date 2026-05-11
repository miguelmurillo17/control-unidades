from django.urls import include, path

from .views import (
    SucursalListView,
    SucursalCreateView,
    SucursalUpdateView,
    SucursalDeleteView,
    UnidadListView,
    UnidadCreateView,
    UnidadUpdateView,
    UnidadDeleteView,
    registrar_movimiento,
    mis_registros,
    manifiestos_list,
    registrar_manifiesto,
)

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
], "manifiestos")

urlpatterns = [
    path("sucursales/", include(sucursales_urls)),
    path("unidades/", include(unidades_urls)),
    path("manifiestos/", include(manifiestos_urls)),
    path("movimientos/registrar/", registrar_movimiento, name="registrar_movimiento"),
    path("movimientos/mis-registros/", mis_registros, name="mis_registros"),
]
