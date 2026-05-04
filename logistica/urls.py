from django.urls import path

from .views import (
    SucursalListView,
    SucursalCreateView,
    SucursalUpdateView,
    SucursalDeleteView,
)

app_name = "sucursales"

urlpatterns = [
    path("", SucursalListView.as_view(), name="list"),
    path("nueva/", SucursalCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", SucursalUpdateView.as_view(), name="update"),
    path("<int:pk>/eliminar/", SucursalDeleteView.as_view(), name="delete"),
]
