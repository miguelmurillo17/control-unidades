from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import MovimientoForm, ManifiestoForm
from .models import Manifiesto, Movimiento, Sucursal, Unidad, UnidadManifiesto
from .services import detectar_inconsistencias, crear_movimiento


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.rol == "ADMIN"


class SucursalListView(AdminRequiredMixin, ListView):
    model = Sucursal
    template_name = "logistica/sucursales/list.html"
    context_object_name = "sucursales"
    ordering = ["nombre"]


class SucursalCreateView(AdminRequiredMixin, CreateView):
    model = Sucursal
    template_name = "logistica/sucursales/form.html"
    fields = ["nombre", "ciudad", "tipo", "activo"]
    success_url = reverse_lazy("sucursales:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva sucursal"
        ctx["accion"] = "Crear"
        return ctx


class SucursalUpdateView(AdminRequiredMixin, UpdateView):
    model = Sucursal
    template_name = "logistica/sucursales/form.html"
    fields = ["nombre", "ciudad", "tipo", "activo"]
    success_url = reverse_lazy("sucursales:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar sucursal"
        ctx["accion"] = "Guardar cambios"
        return ctx


class SucursalDeleteView(AdminRequiredMixin, DeleteView):
    model = Sucursal
    template_name = "logistica/sucursales/confirm_delete.html"
    success_url = reverse_lazy("sucursales:list")


class UnidadListView(AdminRequiredMixin, ListView):
    model = Unidad
    template_name = "logistica/unidades/list.html"
    context_object_name = "unidades"
    ordering = ["numero_economico"]


class UnidadCreateView(AdminRequiredMixin, CreateView):
    model = Unidad
    template_name = "logistica/unidades/form.html"
    fields = ["numero_economico", "tipo", "sucursal_actual", "activo"]
    success_url = reverse_lazy("unidades:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva unidad"
        ctx["accion"] = "Crear"
        return ctx


class UnidadUpdateView(AdminRequiredMixin, UpdateView):
    model = Unidad
    template_name = "logistica/unidades/form.html"
    fields = ["numero_economico", "tipo", "sucursal_actual", "activo"]
    success_url = reverse_lazy("unidades:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar unidad"
        ctx["accion"] = "Guardar cambios"
        return ctx


class UnidadDeleteView(AdminRequiredMixin, DeleteView):
    model = Unidad
    template_name = "logistica/unidades/confirm_delete.html"
    success_url = reverse_lazy("unidades:list")


@login_required
def mis_registros(request):
    if request.user.rol != "CASETA":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    movimientos = (
        Movimiento.objects
        .filter(usuario=request.user)
        .prefetch_related("unidad_movimientos__unidad", "sucursal")
        .order_by("-fecha_hora_evento")
    )
    return render(request, "logistica/movimientos/mis_registros.html", {
        "movimientos": movimientos,
    })


@login_required
def registrar_movimiento(request):
    if request.user.rol != "CASETA":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    movimiento_guardado = None

    if request.method == "POST":
        form = MovimientoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            confirmar = request.POST.get("confirmar") == "1"

            advertencias = detectar_inconsistencias(data["unidades"], data["tipo"])

            if advertencias and not confirmar:
                return render(request, "logistica/movimientos/form.html", {
                    "form": form,
                    "advertencias": advertencias,
                })

            movimiento_guardado = crear_movimiento(data, request.user)
            form = MovimientoForm()  # Limpiar formulario para el siguiente registro
    else:
        form = MovimientoForm()

    return render(request, "logistica/movimientos/form.html", {
        "form": form,
        "movimiento_guardado": movimiento_guardado,
    })


@login_required
def manifiestos_list(request):
    if request.user.rol != "PLANEACION":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    manifiestos = (
        Manifiesto.objects
        .exclude(estado="CANCELADO")
        .select_related("sucursal_origen", "sucursal_destino", "usuario")
        .prefetch_related("unidad_manifiestos__unidad")
        .order_by("-created_at")
    )
    return render(request, "logistica/manifiestos/list.html", {"manifiestos": manifiestos})


@login_required
def registrar_manifiesto(request):
    if request.user.rol != "PLANEACION":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    manifiesto_guardado = None

    if request.method == "POST":
        form = ManifiestoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            manifiesto = Manifiesto.objects.create(
                sucursal_origen=data["sucursal_origen"],
                sucursal_destino=data["sucursal_destino"],
                fecha_salida=data["fecha_salida"],
                fecha_llegada_est=data.get("fecha_llegada_est"),
                usuario=request.user,
                observaciones=data.get("observaciones", ""),
            )
            for unidad in data["unidades"]:
                UnidadManifiesto.objects.create(manifiesto=manifiesto, unidad=unidad)
            manifiesto_guardado = manifiesto
            form = ManifiestoForm()
    else:
        form = ManifiestoForm()

    return render(request, "logistica/manifiestos/form.html", {
        "form": form,
        "manifiesto_guardado": manifiesto_guardado,
    })
