from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from django.utils import timezone

from .forms import UsuarioCreacionForm, UsuarioEdicionForm
from .models import Usuario
from logistica.models import Movimiento, Unidad, Sucursal


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.rol == "ADMIN"


@login_required
def dashboard(request):
    context = {}
    if request.user.rol == "ADMIN":
        hoy = timezone.localdate()
        context["total_unidades_activas"] = Unidad.objects.filter(activo=True).count()
        context["total_sucursales"] = Sucursal.objects.filter(activo=True).count()
        context["total_usuarios_activos"] = Usuario.objects.filter(is_active=True).count()
        context["movimientos_hoy"] = Movimiento.objects.filter(
            fecha_hora_registro__date=hoy, cancelado=False
        ).count()
    return render(request, "dashboard.html", context)


class UsuarioListView(AdminRequiredMixin, ListView):
    model = Usuario
    template_name = "usuarios/list.html"
    context_object_name = "usuarios"
    ordering = ["last_name", "first_name"]


class UsuarioCreateView(AdminRequiredMixin, CreateView):
    model = Usuario
    form_class = UsuarioCreacionForm
    template_name = "usuarios/form.html"
    success_url = reverse_lazy("usuarios:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nuevo usuario"
        ctx["accion"] = "Crear"
        return ctx


class UsuarioUpdateView(AdminRequiredMixin, UpdateView):
    model = Usuario
    form_class = UsuarioEdicionForm
    template_name = "usuarios/form.html"
    success_url = reverse_lazy("usuarios:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Editar usuario"
        ctx["accion"] = "Guardar cambios"
        return ctx


class UsuarioDeleteView(AdminRequiredMixin, DeleteView):
    model = Usuario
    template_name = "usuarios/confirm_delete.html"
    success_url = reverse_lazy("usuarios:list")
